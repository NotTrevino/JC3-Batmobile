#!/usr/bin/env python
"""jc3sigdiff.py - G2-12: the exact civilian -> signature_preorder diff of the armed Serpente.

The card asks what JC3 changes to turn `v0300_car_kensington_sportsmuscle` into the armed
`signature_preorder` variant. This script diffs the two `.ee` containers six ways:

  container  every inner member by name and sha1 (what was added, removed or replaced)
  graph      the `.epe` object trees, matched by semantic path, with object-id churn removed
  weapon     the component `main_weapon` points at: points, muzzle effects, aim, model, tunes
  parts      the `*_vehicle_parts.vmodc` modules (part rows field by field)
  meshes     every `.rbm` header (block count, AABB, size), pairing base and signature files
  tunes      the embedded `w618_sportsmuscle_missile.wtunec` and `.ftunec`, plus the VFS copy

The entity's `.epe` references objects by 32-bit context id (`XXXXXXXX=YYYYYYYY`), and those ids
are renumbered in every build. A byte-level or id-level diff marks all 450 objects changed; this
tool resolves every object reference through the semantic tree path and ignores `vec_events`
(per-entity event hashes), so the remaining list is the real wiring change. Both counts are printed.

Usage:
  python jc3sigdiff.py --write     # decode, diff and write SIGNATURE_DIFF.json + .md
  python jc3sigdiff.py --check     # re-read the archives, rebuild, compare both files
  python jc3sigdiff.py dump graph  # one section (members, graph, weapon, parts, meshes, tunes, toc)
  python jc3sigdiff.py dump all

Raw XML/ADF stays outside the repo in `E:/Modding/_shared/gamedata/JC3grab/sigdiff/`.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jc3adf  # noqa: E402
import jc3detail  # noqa: E402
import jc3index  # noqa: E402
import jc3wiring  # noqa: E402
from eetoc import read_toc  # noqa: E402
from rbmhdr import hash_jenkins, parse_header  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
CACHE = os.path.join(RAW, "sigdiff")
GAME = os.environ.get("JC3_GAME", jc3index.DEFAULT_GAME)

STATE = "CIVILIAN"
BASE = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
        "v0300_car_kensington_sportsmuscle_civilian_01.ee")
VARIANT = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
           "v0300_car_kensington_sportsmuscle_signature_preorder.ee")
JSON_NAME = "SIGNATURE_DIFF.json"
MD_NAME = "SIGNATURE_DIFF.md"
PARTS_TABLE = os.path.join(OUT, "PARTS_TABLE.jsonl")

OID_RE = re.compile(r"^[0-9A-F]{8}=[0-9A-F]{8}$")
VOLATILE = ("_object_id", "_GUID", "name_hash", "id:D04059E6")
ROOT_CLASSES = jc3wiring.ROOT_CLASSES


# --------------------------------------------------------------------- helpers
def sha1(blob: bytes) -> str:
    return hashlib.sha1(blob).hexdigest()


def read_entry(rows: list[dict], path: str) -> bytes:
    r = jc3detail.pick(rows, path)
    with open(os.path.join(GAME, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        blob = f.read(r["size"])
    if len(blob) != r["size"]:
        raise IOError(f"short read {len(blob)} != {r['size']} for {path}")
    return blob


def kind_of(name: str) -> str:
    n = name.lower()
    if n.endswith(".rbm"):
        return "mesh"
    if n.endswith(".lod"):
        return "lod"
    if n.endswith(".vmodc"):
        return "module"
    if n.endswith(".epe"):
        return "graph"
    if n.endswith((".wtunec", ".ftunec", ".etunec", ".ctunec")):
        return "tune"
    if n.endswith(".effc"):
        return "effect"
    if n.endswith((".ddsc", ".hmddsc")):
        return "texture"
    if n.endswith(".pfxc"):
        return "physics"
    if n.endswith((".stringlookup", ".fmod_guids", ".toc")):
        return "meta"
    return "other"


def short(name: str) -> str:
    return name.rsplit("/", 1)[-1]


def short2(name: str) -> str:
    return "/".join(name.rsplit("/", 2)[-2:])


def fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def read_entity(path: str, rows: list[dict], tag: str) -> dict:
    blob = read_entry(rows, path)
    stream, members = jc3detail.inner_files(blob)
    mem = []
    for name, off, size in members:
        mem.append({
            "name": name,
            "off": off,
            "size": size,
            "sha1": sha1(stream[off:off + size]) if off else None,
            "kind": kind_of(name),
        })
    toc = None
    toc_path = path[:-3] + ".ee.toc"
    if any(r["path"] == toc_path for r in rows):
        toc = [{"name": n, "off": o, "size": s}
               for n, o, s in read_toc(read_entry(rows, toc_path))]
    # the loose .epe next to the container is a different build; record it, do not use it
    loose = None
    loose_path = path[:-3] + ".epe"
    if any(r["path"] == loose_path for r in rows):
        lb = read_entry(rows, loose_path)
        loose = {"size": len(lb), "sha1": sha1(lb)}
    inner = [m for m in mem if m["name"].endswith(".epe")]
    if len(inner) != 1:
        raise ValueError(f"{path}: expected one inner .epe, got {len(inner)}")
    return {
        "path": path,
        "tag": tag,
        "container": {"size": len(blob), "sha1": sha1(blob)},
        "inner_epe": {"name": inner[0]["name"], "size": inner[0]["size"],
                      "sha1": inner[0]["sha1"]},
        "loose_epe": loose,
        "members": mem,
        "toc": toc,
        "stream": stream,
    }


def decode_graph(ent: dict) -> tuple[list, str]:
    """Convert the container's inner .epe and parse it with jc3wiring's full reader."""
    os.makedirs(CACHE, exist_ok=True)
    member = [m for m in ent["members"] if m["name"].endswith(".epe")][0]
    blob = ent["stream"][member["off"]:member["off"] + member["size"]]
    tag = ent["tag"]
    src = os.path.join(CACHE, tag + ".epe")
    dst = os.path.join(CACHE, tag + ".xml")
    with open(src, "wb") as f:
        f.write(blob)
    p = subprocess.run([jc3detail.CONVERT, "--e", src, dst], capture_output=True)
    if p.returncode != 0 or not os.path.exists(dst):
        raise RuntimeError(f"ConvertProperty failed for {ent['path']}: "
                           f"{p.stdout[-300:]!r} {p.stderr[-300:]!r}")
    return jc3wiring.parse_epe(dst), dst


def part_module(ent: dict) -> dict:
    hits = [m for m in ent["members"] if m["name"].endswith("vehicle_parts.vmodc")]
    if len(hits) != 1:
        raise ValueError(f"{ent['path']}: expected one parts module, got {len(hits)}")
    m = hits[0]
    blob = ent["stream"][m["off"]:m["off"] + m["size"]]
    path = os.path.join(CACHE, ent["tag"] + "_parts.vmodc")
    with open(path, "wb") as f:
        f.write(blob)
    return {"path": m["name"], "size": m["size"], "sha1": sha1(blob),
            "parts": jc3adf.parts(jc3adf.Adf(blob))}


# ------------------------------------------------------------------ graph diff
def semantic_tree(root) -> tuple[dict, dict]:
    """oid -> semantic path, and path -> object. Entity names at the root are dropped so the
    variant's CCar subtree keeps the same paths even though the entity is renamed."""
    oidmap: dict[str, str] = {}
    paths: dict[str, object] = {}

    def walk(o, path: str) -> None:
        if o.oid:
            oidmap[o.oid] = path
        paths[path] = o
        counts: collections.Counter = collections.Counter()
        for c in o.children:
            if c.parent is root and c.cls in ROOT_CLASSES:
                key = c.cls
            elif c.name:
                key = f"{c.cls}:{c.name}"
            else:
                n = counts[c.cls]
                counts[c.cls] += 1
                key = f"{c.cls}:#{n}"
            walk(c, path + "/" + key)

    walk(root, "root")
    return oidmap, paths


def child_keys(o) -> list[tuple[str, object]]:
    counts: collections.Counter = collections.Counter()
    out = []
    for c in o.children:
        if c.name:
            key = f"{c.cls}:{c.name}"
        else:
            n = counts[c.cls]
            counts[c.cls] += 1
            key = f"{c.cls}:#{n}"
        out.append((key, c))
    return out


def prop_types(o) -> dict[str, str]:
    return {k: t for k, t, _v in o.values}


def ref_value(v: str | None, oidmap: dict[str, str]) -> str | None:
    if v is None:
        return None
    if OID_RE.match(v):
        return "->" + oidmap.get(v, v)
    return v


def graph_diff(root_a, root_b) -> dict:
    oid_a, _ = semantic_tree(root_a)
    oid_b, _ = semantic_tree(root_b)
    added: list[dict] = []
    removed: list[dict] = []
    changed: list[dict] = []
    skipped = {"vec_events": 0, "volatile": 0, "refs": 0}

    def descendants(o) -> list:
        out = []
        stack = [o]
        while stack:
            cur = stack.pop()
            out.append(cur)
            stack.extend(cur.children)
        return out

    def stable_key(child, at_root: bool) -> str:
        if at_root and child.cls in ROOT_CLASSES:
            return child.cls
        return f"{child.cls}:{child.name}" if child.name else ""

    def add_node(o, path: str, bucket: list[dict]) -> None:
        ds = descendants(o)
        classes = collections.Counter(x.cls for x in ds)
        bucket.append({
            "path": path,
            "class": o.cls,
            "name": o.name,
            "objects": len(ds),
            "classes": dict(sorted(classes.items())),
        })

    def compare(a, b, path: str) -> None:
        ta, tb = prop_types(a), prop_types(b)
        diffs = {}
        for k in sorted(set(a.props) | set(b.props)):
            if k in VOLATILE:
                skipped["volatile"] += 1
                continue
            if ta.get(k) == "vec_events" or tb.get(k) == "vec_events":
                skipped["vec_events"] += 1
                continue
            va, vb = a.props.get(k), b.props.get(k)
            if va == vb:
                continue
            ra, rb = ref_value(va, oid_a), ref_value(vb, oid_b)
            if OID_RE.match(va or "") or OID_RE.match(vb or ""):
                if ra == rb:
                    skipped["refs"] += 1
                    continue
            diffs[k] = {"before": ra, "after": rb, "type": ta.get(k) or tb.get(k)}
        if diffs:
            changed.append({"path": path, "class": a.cls, "name": a.name,
                            "props": diffs})
        cb = dict(child_keys(b))
        paired: list[tuple[str, object, object]] = []
        unmatched_a = []
        for key, child in child_keys(a):
            if key in cb:
                paired.append((key, child, cb[key]))
            else:
                unmatched_a.append((key, child))
        used = {key for key, _, _ in paired}
        unmatched_b = [(k, c) for k, c in child_keys(b) if k not in used]
        # A class-unique fallback is only for identity-less children (or the root entity, whose
        # name is the variant name). A named child with a different name is a real rename.
        allow_rename = path == "root"
        for key, child in list(unmatched_a):
            same_a = [x for x in unmatched_a if x[1].cls == child.cls]
            same_b = [x for x in unmatched_b if x[1].cls == child.cls]
            if len(same_a) == 1 and len(same_b) == 1 and (
                    allow_rename or (not child.name and not same_b[0][1].name)):
                paired.append((key, child, same_b[0][1]))
                unmatched_a.remove((key, child))
                unmatched_b = [x for x in unmatched_b if x is not same_b[0]]
        at_root = path == "root"
        for key, child in unmatched_a:
            add_node(child, path + "/" + (stable_key(child, at_root) or key), removed)
        for key, child in unmatched_b:
            add_node(child, path + "/" + (stable_key(child, at_root) or key), added)
        for key, ca_, cb_ in paired:
            compare(ca_, cb_, path + "/" + (stable_key(ca_, at_root) or key))

    compare(root_a, root_b, "root")
    classes_a = collections.Counter(x.cls for x in descendants(root_a))
    classes_b = collections.Counter(x.cls for x in descendants(root_b))
    deltas = {k: [classes_a.get(k, 0), classes_b.get(k, 0)]
              for k in sorted(set(classes_a) | set(classes_b))
              if classes_a.get(k, 0) != classes_b.get(k, 0)}
    return {
        "objects": [len(descendants(root_a)), len(descendants(root_b))],
        "added": sorted(added, key=lambda x: x["path"]),
        "removed": sorted(removed, key=lambda x: x["path"]),
        "changed": sorted(changed, key=lambda x: x["path"]),
        "class_deltas": deltas,
        "skipped": skipped,
    }


# --------------------------------------------------------------- members/parts
def pair_stem(name: str) -> str:
    base = short(name)
    return base[len("signature_"):] if base.startswith("signature_") else base


def member_diff(a: dict, b: dict) -> dict:
    A = {m["name"]: m for m in a["members"]}
    B = {m["name"]: m for m in b["members"]}
    added = [B[n] for n in sorted(set(B) - set(A))]
    removed = [A[n] for n in sorted(set(A) - set(B))]
    changed = [{"name": n, "before": A[n], "after": B[n]}
               for n in sorted(set(A) & set(B)) if A[n]["sha1"] != B[n]["sha1"]]
    # pair `signature/signature_X` against `X` (same file role, new art path)
    rem_by_stem = collections.defaultdict(list)
    for m in removed:
        rem_by_stem[(pair_stem(m["name"]), m["name"].rsplit(".", 1)[-1])].append(m)
    replaced = []
    for m in added:
        key = (pair_stem(m["name"]), m["name"].rsplit(".", 1)[-1])
        if key in rem_by_stem and rem_by_stem[key]:
            old = rem_by_stem[key].pop(0)
            replaced.append({
                "stem": pair_stem(m["name"]),
                "before": {"name": old["name"], "size": old["size"], "sha1": old["sha1"]},
                "after": {"name": m["name"], "size": m["size"], "sha1": m["sha1"]},
                "delta": m["size"] - old["size"],
            })
    paired_before = {r["before"]["name"] for r in replaced}
    paired_after = {r["after"]["name"] for r in replaced}
    unpaired_added = [m for m in added if m["name"] not in paired_after]
    unpaired_removed = [m for m in removed if m["name"] not in paired_before]

    def by_kind(ms):
        c = collections.Counter(m["kind"] for m in ms)
        return dict(sorted(c.items()))

    return {
        "counts": [len(A), len(B)],
        "added": added,
        "removed": removed,
        "changed": changed,
        "replaced": sorted(replaced, key=lambda r: r["after"]["name"]),
        "unpaired_added": unpaired_added,
        "unpaired_removed": unpaired_removed,
        "added_by_kind": by_kind(added),
        "removed_by_kind": by_kind(removed),
        "unpaired_added_by_kind": by_kind(unpaired_added),
        "unpaired_removed_by_kind": by_kind(unpaired_removed),
    }


def parts_diff(a: dict, b: dict, table_mismatches: dict,
               inst_a: list[int], inst_b: list[int]) -> dict:
    A = {p["part_index"]: p for p in a["parts"]}
    B = {p["part_index"]: p for p in b["parts"]}
    only_a = sorted(set(A) - set(B))
    only_b = sorted(set(B) - set(A))
    changed = []
    field_names = set()
    for i in sorted(set(A) & set(B)):
        fields = {k: {"before": A[i].get(k), "after": B[i].get(k)}
                  for k in A[i] if A[i].get(k) != B[i].get(k)}
        if fields:
            changed.append({"index": i, "name": A[i]["name"], "fields": fields})
            field_names |= set(fields)
    rows = []
    for i in sorted(B):
        p = B[i]
        rows.append({
            "index": p["part_index"], "name": p["name"], "behavior": p["behavior"],
            "damage_type": p["damage_type"], "parent": p["parent_part_index"],
            "model": p["model"], "model_swap": p["model_swap"],
            "children": p["children_part_indices"],
        })
    return {
        "civilian_module": {"path": a["path"], "size": a["size"], "sha1": a["sha1"],
                            "parts": len(a["parts"])},
        "variant_module": {"path": b["path"], "size": b["size"], "sha1": b["sha1"],
                           "parts": len(b["parts"])},
        "only_civilian": only_a,
        "only_variant": only_b,
        "changed": changed,
        "changed_fields": sorted(field_names),
        "variant_rows": rows,
        "civilian_signature_models": [p["name"] for p in a["parts"]
                                       if "/signature/" in (p["model"] or "")],
        "epe_instantiated": {
            "civilian": inst_a,
            "variant": inst_b,
            "civilian_missing": sorted(set(A) - set(inst_a)),
            "variant_missing": sorted(set(B) - set(inst_b)),
        },
        "table_mismatches": table_mismatches,
    }


def table_check(rows: list[dict], a: dict, b: dict) -> dict:
    if not os.path.exists(PARTS_TABLE):
        return {"checked": False, "reason": "no PARTS_TABLE.jsonl"}
    table = {}
    for line in open(PARTS_TABLE, encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("entity") in (BASE, VARIANT):
            table[rec["entity"]] = rec
    out = {"checked": True, "rows": {}, "mismatches": []}
    for ent, mod in ((BASE, a), (VARIANT, b)):
        rec = table.get(ent)
        if not rec:
            out["mismatches"].append({"entity": ent, "why": "no row"})
            continue
        tp = rec.get("parts") or []
        out["rows"][ent] = {"parts": len(tp), "module": rec.get("module")}
        if len(tp) != len(mod["parts"]):
            out["mismatches"].append({"entity": ent, "why": "part count",
                                      "table": len(tp), "decoded": len(mod["parts"])})
        for p, t in zip(mod["parts"], sorted(tp, key=lambda x: x.get("i", -1))):
            if p["part_index"] != t.get("i") or p["name"] != t.get("n") or p["model"] != t.get("m"):
                out["mismatches"].append({"entity": ent, "index": p["part_index"],
                                          "decoded": [p["name"], p["model"]],
                                          "table": [t.get("n"), t.get("m")]})
    out["matches"] = not out["mismatches"]
    return out


# -------------------------------------------------------------------- meshes
def mesh_stats(ent: dict) -> dict[str, dict]:
    out = {}
    for m in ent["members"]:
        if not m["name"].endswith(".rbm"):
            continue
        blob = ent["stream"][m["off"]:m["off"] + m["size"]]
        try:
            h = parse_header(blob[:4096])
            out[m["name"]] = {
                "size": m["size"], "sha1": m["sha1"],
                "blocks": h.get("block_count"), "version": h.get("version"),
                "size_m": h.get("size_m"), "min": h.get("min"), "max": h.get("max"),
            }
        except Exception as e:  # noqa: BLE001 - a bad header is a finding, not a crash
            out[m["name"]] = {"size": m["size"], "sha1": m["sha1"], "error": str(e)}
    return out


def mesh_diff(a: dict, b: dict) -> dict:
    A, B = mesh_stats(a), mesh_stats(b)
    amap = {pair_stem(n): n for n in A}
    pairs, standalone = [], []
    for n in sorted(B):
        st = pair_stem(n)
        if "/signature/" not in n:
            if n not in A:
                standalone.append({"name": n, **{k: B[n].get(k) for k in
                                                  ("size", "blocks", "sha1")}})
            continue
        old = amap.get(st)
        if not old:
            standalone.append({"name": n, **{k: B[n].get(k) for k in
                                              ("size", "blocks", "sha1")}})
            continue
        ha, hb = A[old], B[n]
        pairs.append({
            "stem": st,
            "before": old, "after": n,
            "before_size": ha["size"], "after_size": hb["size"],
            "delta": hb["size"] - ha["size"],
            "blocks": [ha.get("blocks"), hb.get("blocks")],
            "aabb_equal": ha.get("min") == hb.get("min") and ha.get("max") == hb.get("max"),
        })
    return {
        "counts": [len(A), len(B)],
        "pairs": pairs,
        "standalone_added": standalone,
        "removed": sorted(n for n in A if n not in B),
    }


# --------------------------------------------------------------------- tunes
def adf_rows(blob: bytes) -> dict[str, object]:
    return {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(blob))}


def strip_prefix(rows: dict[str, object]) -> dict[str, object]:
    out = {}
    for k, v in rows.items():
        out[k.replace("missile_weapon[0].", "")] = v
    return out


TUNE_KEYS = (
    "tuning.base_tuning.damage",
    "tuning.base_tuning.impulse",
    "tuning.base_tuning.vehicle_damage_factor",
    "tuning.base_tuning.object_damage_factor",
    "tuning.missile_base_tuning.missile_turning_speed",
    "tuning.missile_base_tuning.missile_loose_lock_distance",
    "tuning.missile_base_tuning.gravity",
    "tuning.missile_base_tuning.meters_times_speed_in_front_of_target",
    "ai_tuning.base_tuning.damage",
    "ai_tuning.ai_base_tuning.range[0]",
    "ai_tuning.ai_base_tuning.range[1]",
    "magazine_size",
    "max_range",
    "fire_rate",
    "burst_count",
    "unlimited_ammo",
)


def tune_section(rows: list[dict], ent: dict) -> dict:
    want = ("w618_sportsmuscle_missile.wtunec", "w618_sportsmuscle_missile.ftunec")
    found = {}
    for m in ent["members"]:
        if m["name"].endswith(want):
            blob = ent["stream"][m["off"]:m["off"] + m["size"]]
            found[short(m["name"])] = {"member": m["name"], "size": m["size"],
                                       "sha1": m["sha1"], "rows": strip_prefix(adf_rows(blob))}
    # the VFS copy of the tune (patch mount) is a different build: compare it
    vfs = [r for r in rows if r["path"].endswith("w618_sportsmuscle_missile.wtunec")]
    if vfs:
        blob = read_entry(rows, vfs[0]["path"])
        vfs_rows = strip_prefix(adf_rows(blob))
        emb = found.get("w618_sportsmuscle_missile.wtunec")
        diff = {}
        if emb:
            for k in sorted(set(vfs_rows) | set(emb["rows"])):
                if vfs_rows.get(k) != emb["rows"].get(k):
                    diff[k] = {"vfs": vfs_rows.get(k), "embedded": emb["rows"].get(k)}
        found["vfs_wtunec"] = {"path": vfs[0]["path"], "mount": vfs[0]["mount"],
                               "size": len(blob), "sha1": sha1(blob),
                               "rows": len(vfs_rows), "diff": diff}
    # autoaim tune and the force pulse file path, straight from the entity graph
    graph = [line for line in open(os.path.join(CACHE, ent["tag"] + ".xml"),
                                   encoding="utf-8") if "autoaim_vehicle_no_lockon_missile" in line]
    auto = sorted({re.search(r">([^<]+)<", line).group(1) for line in graph})
    found["autoaim_path"] = auto[0] if auto else None
    return found


# ----------------------------------------------------------------------- toc
def toc_diff(a: dict, b: dict) -> dict:
    if not a.get("toc") or not b.get("toc"):
        return {"available": False}
    A = {r["name"]: r for r in a["toc"]}
    B = {r["name"]: r for r in b["toc"]}
    added = [B[n] for n in sorted(set(B) - set(A))]
    removed = [A[n] for n in sorted(set(A) - set(B))]
    return {
        "available": True,
        "counts": [len(A), len(B)],
        "external": [sum(1 for r in a["toc"] if r["off"] == 0),
                     sum(1 for r in b["toc"] if r["off"] == 0)],
        "added": added,
        "removed": removed,
        "added_by_kind": dict(sorted(collections.Counter(kind_of(r["name"]) for r in added).items())),
        "removed_by_kind": dict(sorted(collections.Counter(kind_of(r["name"]) for r in removed).items())),
    }


# -------------------------------------------------------------------- weapon
def weapon_detail(graph: list, rows: list, members: list) -> dict:
    """The component the root main_weapon points at, with its points and muzzle effects."""
    root = [o for o in graph if o.cls in ROOT_CLASSES][0]
    comp = next((o for o in graph if o.oid == root.get("id:851CAABE")), None)
    if comp is None:
        return {"found": False}
    by_hash = {}
    for r in rows:
        try:
            by_hash[int(r["hash"], 16)] = (r["path"], "vfs")
        except (KeyError, ValueError):
            pass
    for m in members:
        by_hash.setdefault(hash_jenkins(m["name"].encode("ascii")), (m["name"], "container"))

    def position(o: "Obj") -> list[float] | None:
        w = o.get("world")
        if not w:
            return None
        vals = [v.strip() for v in w.split(",")]
        if len(vals) != 16:
            return None
        return [float(v) for v in vals[12:15]]

    def effect_hash(o: "Obj") -> int | None:
        h = o.get("Effect")
        try:
            return int(h) & 0xFFFFFFFF
        except (TypeError, ValueError):
            return None

    points = [{"name": p.name, "type": p.get("type"),
               "fire_effect": p.get("fire_effect"), "position": position(p)}
              for p in comp.children if p.cls == "SWeaponPoint"]
    points.sort(key=lambda x: x["name"])
    muzzles = []
    for se in comp.children:
        if se.cls != "SEffects":
            continue
        for e in se.children:
            if e.cls != "SAttachedEffect":
                continue
            h = effect_hash(e)
            hit = by_hash.get(h) if h is not None else None
            muzzles.append({"name": e.name or "(unnamed)", "effect": h,
                            "effect_path": hit[0] if hit else None,
                            "effect_source": hit[1] if hit else None,
                            "position": position(e)})
    for p in points:
        hit = [m for m in muzzles if m["position"] == p["position"]]
        p["muzzle"] = hit[0]["name"] if len(hit) == 1 else None
    aim = [c for c in comp.children if c.cls == "CAimPOIWeaponComponent"]
    slots = {}
    for k in ("id:851CAABE", "id:00568A74", "mounted_weapon", "id:AC0BC788"):
        v = root.props.get(k)
        slots[k] = v if v and v != "00000000" else None
    return {
        "found": True,
        "slots": slots,
        "class": comp.cls, "name": comp.name, "object_id": comp.oid,
        "weapon_id": comp.get("weapon_id"), "weapon_type": comp.get("weapon_type"),
        "model": comp.get("id:61641926"), "tune": comp.get("id:AA7096C9"),
        "autoaim": comp.get("id:6D4C8277"), "collision": comp.get("id:C253D5FD"),
        "rigid_object_effect_settings": comp.get("id:35B57209"),
        "points": points,
        "muzzles": muzzles,
        "aim": ({"class": aim[0].cls, "name": aim[0].name,
                 "value": aim[0].get("id:2D0B3C09")} if aim else None),
    }


# --------------------------------------------------------------------- write
def build() -> dict:
    rows = jc3index.load_index(OUT)
    os.makedirs(CACHE, exist_ok=True)
    a = read_entity(BASE, rows, "civilian")
    b = read_entity(VARIANT, rows, "variant")
    graph_a, _xml_a = decode_graph(a)
    graph_b, _xml_b = decode_graph(b)
    root_a = [o for o in graph_a if o.parent is None][0]
    root_b = [o for o in graph_b if o.parent is None][0]
    parts_a = part_module(a)
    parts_b = part_module(b)
    inst = lambda g: sorted({int(o.props["part_index"]) for o in g
                             if o.cls == "CPartProp" and "part_index" in o.props})
    table = table_check(rows, parts_a, parts_b)
    out = {
        "entities": {
            "civilian": {k: a[k] for k in ("path", "container", "inner_epe", "loose_epe")},
            "variant": {k: b[k] for k in ("path", "container", "inner_epe", "loose_epe")},
        },
        "members": member_diff(a, b),
        "graph": graph_diff(root_a, root_b),
        "weapon": weapon_detail(graph_b, rows, b["members"]),
        "parts": parts_diff(parts_a, parts_b, table, inst(graph_a), inst(graph_b)),
        "meshes": mesh_diff(a, b),
        "tunes": tune_section(rows, b),
        "toc": toc_diff(a, b),
    }
    # resolve the root's hashed content ids against the containers' own module names
    member_hash = {hash_jenkins(m["name"].encode("ascii")): m["name"]
                   for m in a["members"] + b["members"]}
    for x in out["graph"]["changed"]:
        for v in x["props"].values():
            if v.get("type") != "int":
                continue
            for side in ("before", "after"):
                raw = v.get(side)
                if raw is None:
                    continue
                try:
                    n = int(raw) & 0xFFFFFFFF
                except (TypeError, ValueError):
                    continue
                if abs(int(raw)) >= 1000 and n in member_hash:
                    v[side + "_path"] = member_hash[n]
    out["digest"] = hashlib.sha1(json.dumps(out, sort_keys=True,
                                            separators=(",", ":")).encode()).hexdigest()[:16]
    return out


def md_source_table(d: dict) -> list[str]:
    a, b = d["entities"]["civilian"], d["entities"]["variant"]
    lines = [
        "| | civilian | signature_preorder |",
        "|---|---|---|",
        f"| entity | `{short(a['path'])}` | `{short(b['path'])}` |",
    ]
    for label, k in (("container size", "size"), ("container sha1", "sha1")):
        lines.append(f"| {label} | {a['container'][k]} | {b['container'][k]} |")
    lines.append(f"| inner `.epe` | {a['inner_epe']['size']} B `{a['inner_epe']['sha1']}` | "
                 f"{b['inner_epe']['size']} B `{b['inner_epe']['sha1']}` |")
    la, lb = a.get("loose_epe"), b.get("loose_epe")
    lines.append(f"| loose `.epe` entry | {la['size'] if la else '-'} B `{la['sha1'] if la else '-'}` | "
                 f"{lb['size'] if lb else '-'} B `{lb['sha1'] if lb else '-'}` |")
    return lines


def md_members(d: dict) -> list[str]:
    m = d["members"]
    lines = [
        "## 2. Container diff",
        "",
        f"{m['counts'][0]} members vs {m['counts'][1]}: **{len(m['added'])} added** "
        f"(**{len(m['replaced'])} of them a same-role replacement**, a `signature/` path for the "
        f"base path), **{len(m['removed'])} removed**, **{len(m['changed'])} changed by name**.",
        "",
        "| kind | added | removed |",
        "|---|---|---|",
    ]
    for k in sorted(set(m["added_by_kind"]) | set(m["removed_by_kind"])):
        lines.append(f"| {k} | {m['added_by_kind'].get(k, 0)} | {m['removed_by_kind'].get(k, 0)} |")
    lines += ["", "Same-role replacements (base asset → signature asset):", "",
              "| stem | before | after | Δ bytes |", "|---|---|---|---|"]
    for r in m["replaced"]:
        lines.append(f"| `{r['stem']}` | {r['before']['size']} | {r['after']['size']} | {r['delta']:+d} |")
    un = m["unpaired_added"]
    if un:
        lines += ["", "Added and not a rename (grouped by kind and directory):", ""]
        groups = collections.defaultdict(list)
        for x in un:
            dirs = x["name"].rsplit("/", 1)[0]
            groups[(x["kind"], dirs)].append(x)
        for (kind, dirs), items in sorted(groups.items()):
            names = ", ".join(f"`{short(i['name'])}`" for i in items)
            lines.append(f"- **{kind}** in `{dirs}` ({len(items)}): {names}")
    ur = m["unpaired_removed"]
    if ur:
        lines += ["", "Removed and not replaced 1:1:", ""]
        for x in ur:
            lines.append(f"- **{x['kind']}** `{x['name']}` ({x['size']} B)")
    return lines


def md_graph(d: dict) -> list[str]:
    g = d["graph"]
    lines = [
        "## 3. Entity graph (`epe`)",
        "",
        f"{g['objects'][0]} objects vs {g['objects'][1]}. The raw id diff marks all "
        f"{g['objects'][0]} objects changed; resolving references by semantic path and ignoring "
        f"`vec_events` leaves **{len(g['changed'])} changed objects**, plus "
        f"**{len(g['added'])} added** and **{len(g['removed'])} removed** subtrees "
        f"({g['skipped']['refs']} reference values resolved to the same path, "
        f"{g['skipped']['vec_events']} `vec_events` values and {g['skipped']['volatile']} "
        f"identity fields discarded).",
        "",
        "### Added",
        "",
        "| path | class | name | objects | contents |",
        "|---|---|---|---|---|",
    ]
    for x in g["added"]:
        cls = ", ".join(f"{k}×{v}" for k, v in x["classes"].items())
        lines.append(f"| `{x['path']}` | `{x['class']}` | `{x['name']}` | {x['objects']} | {cls} |")
    lines += ["", "### Removed", "", "| path | class | name | objects |", "|---|---|---|---|"]
    for x in g["removed"]:
        lines.append(f"| `{x['path']}` | `{x['class']}` | `{x['name']}` | {x['objects']} |")
    lines += ["", "### Changed properties", "",
              "Identity-only churn is excluded; a reference is shown by the semantic path it "
              "resolves to. `->` is a link, `00000000` is null.", ""]
    for x in g["changed"]:
        lines.append(f"**`{x['class']}`** `{x['name']}` — `{x['path']}`")
        lines.append("")
        lines.append("| property | type | before | after |")
        lines.append("|---|---|---|---|")
        for k, v in x["props"].items():
            label = f"`{k}`" if not k.startswith("id:") else f"`{k}` (unnamed)"
            cells = []
            for side in ("before", "after"):
                cell = fmt(v[side])
                if v.get(side + "_path"):
                    cell += f" → `{short2(v[side + '_path'])}`"
                cells.append(cell)
            lines.append(f"| {label} | {v['type']} | {cells[0]} | {cells[1]} |")
        lines.append("")
    if g["class_deltas"]:
        lines += ["Class counts that moved:", "", "| class | civilian | variant |", "|---|---|---|"]
        for k, (ca, cb) in g["class_deltas"].items():
            lines.append(f"| `{k}` | {ca} | {cb} |")
    return lines


def md_weapon(d: dict) -> list[str]:
    w = d.get("weapon") or {}
    lines = ["### The added weapon, point by point", ""]
    if not w.get("found"):
        return lines + ["The root `main_weapon` slot resolves to no component.", ""]
    lines += [f"`{w['class']}` `{w['name']}` — object `{w['object_id']}`, `weapon_id` "
              f"{w['weapon_id']}, `weapon_type` {w['weapon_type']}.", "",
              "| property | value |", "|---|---|"]
    for label, key in (("model", "model"), ("tune", "tune"), ("autoaim", "autoaim"),
                       ("collision", "collision"),
                       ("rigid-object effects", "rigid_object_effect_settings")):
        lines.append(f"| {label} | `{w[key]}` |" if w.get(key) else f"| {label} | - |")
    null_slots = [k for k, v in w["slots"].items() if not v]
    lines += ["", f"Slots: `main_weapon` (`id:851CAABE`) → this component; "
              + (", ".join(f"`{k}`" for k in null_slots) + " → null." if null_slots else
                 "no other slot is null.")]
    lines += ["", f"The component carries {len(w['points'])} `SWeaponPoint`s and "
              f"{len(w['muzzles'])} `SAttachedEffect` muzzles under one `SEffects`. Each "
              f"point's position equals its muzzle's position; `--check` asserts the pairing.", "",
              "| point | type | fire_effect | position (x, y, z) | muzzle |",
              "|---|---|---|---|---|"]
    for p in w["points"]:
        pos = ", ".join(f"{v:g}" for v in p["position"]) if p["position"] else "-"
        lines.append(f"| `{p['name']}` | {p['type']} | {p['fire_effect']} | {pos} | "
                     f"`{p['muzzle'] or '-'}` |")
    effects = {m["effect"] for m in w["muzzles"] if m["effect"] is not None}
    if len(effects) == 1:
        e = w["muzzles"][0]
        resolved = f" → `{e['effect_path']}`" if e["effect_path"] else ""
        lines += ["", f"All muzzles share effect hash `{e['effect']}`{resolved}."]
    if w.get("aim"):
        a = w["aim"]
        lines += ["", f"Aim: `{a['class']}` `{a['name']}`, `id:2D0B3C09` = {a['value']}."]
    lines.append("")
    return lines


def md_parts(d: dict) -> list[str]:
    p = d["parts"]
    lines = [
        "## 4. Parts modules",
        "",
        f"| | civilian | signature_preorder |",
        "|---|---|---|",
        f"| module | `{p['civilian_module']['path']}` | `{p['variant_module']['path']}` |",
        f"| size / sha1 | {p['civilian_module']['size']} B `{p['civilian_module']['sha1'][:12]}` | "
        f"{p['variant_module']['size']} B `{p['variant_module']['sha1'][:12]}` |",
        f"| parts defined | {p['civilian_module']['parts']} | {p['variant_module']['parts']} |",
        f"| parts instantiated by the `epe` | {len(p['epe_instantiated']['civilian'])} | "
        f"{len(p['epe_instantiated']['variant'])} |",
        "",
    ]
    if p["only_civilian"] or p["only_variant"]:
        lines += [f"Part indices: {p['only_civilian']} only in the civilian, "
                  f"{p['only_variant']} only in the signature.", ""]
    else:
        lines += [f"The two modules are the same part set: {len(p['variant_rows'])} names at the "
                  f"same indices, no part only in one of them. Changed fields across the shared "
                  f"parts: {', '.join(f'`{x}`' for x in p['changed_fields']) or 'none'}.", ""]
    em = p["epe_instantiated"]
    lines += [
        f"The instantiated tree is the difference, not the definitions. Each `epe` builds only "
        f"the hood branch it needs: the civilian tree holds {len(em['civilian'])} of the "
        f"{p['civilian_module']['parts']} parts and leaves out "
        f"{', '.join(f'`{i}`' for i in em['civilian_missing'])}; the signature tree holds "
        f"{len(em['variant'])} and leaves out "
        f"{', '.join(f'`{i}`' for i in em['variant_missing'])}. Everything else is shared.",
        "",
    ]
    if p["changed"]:
        lines += ["| index | name | field | civilian | variant |", "|---|---|---|---|---|"]
        for c in p["changed"]:
            for k, v in c["fields"].items():
                lines.append(f"| {c['index']} | `{c['name']}` | `{k}` | "
                             f"`{v['before']}` | `{v['after']}` |")
        lines.append("")
    elif p["only_civilian"] or p["only_variant"]:
        lines.append("No shared part changed any field; the difference is the part set only.")
        lines.append("")
    lines += ["The signature module's part rows (this is the definition the `epe` instantiates "
              "from):", "",
              "| i | part | behaviour | damage type | parent | model |", "|---|---|---|---|---|---|"]
    for r in p["variant_rows"]:
        model = "/".join(r["model"].split("/")[-2:]) if "/signature/" in r["model"] else short(r["model"])
        lines.append(f"| {r['index']} | `{r['name']}` | {r['behavior'] or '-'} | {r['damage_type']} | "
                     f"{r['parent']} | `{model}` |")
    lines.append("")
    t = p["table_mismatches"]
    if t.get("matches"):
        lines += [f"`PARTS_TABLE.jsonl` cross-check: both rows match the decoded modules "
                  f"({t['rows'].get(BASE, {}).get('parts')} and "
                  f"{t['rows'].get(VARIANT, {}).get('parts')} parts, same names and models).", ""]
    else:
        lines += [f"**`PARTS_TABLE.jsonl` cross-check failed**: {len(t.get('mismatches', []))} "
                  f"mismatch(es); see the json.", ""]
    return lines


def md_meshes(d: dict) -> list[str]:
    m = d["meshes"]
    pairs = m["pairs"]
    eq = sum(1 for p in pairs if p["blocks"][0] == p["blocks"][1] and p["aabb_equal"])
    lines = [
        "## 5. Meshes",
        "",
        f"{m['counts'][0]} `.rbm` vs {m['counts'][1]}. **{len(pairs)} pairs** share a stem "
        f"(base path → `signature/` path); **{eq}** have the same block count and the same AABB. "
        f"Size deltas: {sorted({p['delta'] for p in pairs})}.",
        "",
        "| stem | blocks | Δ bytes | AABB equal |",
        "|---|---|---|---|",
    ]
    for p in pairs:
        lines.append(f"| `{p['stem']}` | {p['blocks'][0]}→{p['blocks'][1]} | {p['delta']:+d} | "
                     f"{'yes' if p['aabb_equal'] else '**no**'} |")
    if m["standalone_added"]:
        lines += ["", "Added meshes with no base counterpart:", "",
                  "| mesh | size | blocks |", "|---|---|---|"]
        for x in m["standalone_added"]:
            lines.append(f"| `{short(x['name'])}` | {x['size']} | {x['blocks']} |")
    return lines


def md_tunes(d: dict) -> list[str]:
    t = d["tunes"]
    wt = t.get("w618_sportsmuscle_missile.wtunec")
    ft = t.get("w618_sportsmuscle_missile.ftunec")
    vfs = t.get("vfs_wtunec")
    lines = [
        "## 6. The `w618` tune and the blast",
        "",
        f"The weapon component stores its tune under the hashed property `AA7096C9` "
        f"(`tuning_file`): `editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/"
        f"w618_sportsmuscle_missile.wtune`. Autoaim: `{t.get('autoaim_path') or '-'}`.",
        "",
    ]
    if wt:
        lines += ["| tune member | value |", "|---|---|"]
        for k in TUNE_KEYS:
            if k in wt["rows"]:
                lines.append(f"| `{k}` | {fmt(wt['rows'][k])} |")
        lines.append("")
    if vfs:
        lines += [f"The signature container embeds a **{wt['size']} B** copy of the wire tune; "
                  f"the VFS path resolves to the patch entry at **{vfs['size']} B** "
                  f"(`{vfs['mount']}`). Decoded, the patch copy has {vfs['rows']} rows and the "
                  f"embedded copy {len(wt['rows'])}; the diff is "
                  f"**{len(vfs['diff'])} fields**, all absent from the embedded copy:", ""]
        for k, v in vfs["diff"].items():
            lines.append(f"- `{k}`: VFS `{fmt(v['vfs'])}`, embedded {fmt(v['embedded']) if v['embedded'] is not None else 'absent'}")
        lines.append("")
    if ft:
        lines += ["Blast (`w618_sportsmuscle_missile.ftunec`, only embedded, no VFS entry):", "",
                  "| field | value |", "|---|---|"]
        for k in ("PlayerDamage", "PlayerDamageRadius", "PlayerDamageRadiusPercentageMax",
                  "AIDamage", "AIDamageRadius"):
            if k in ft["rows"]:
                lines.append(f"| `{k}` | {fmt(ft['rows'][k])} |")
        lines.append("")
    return lines


def md_toc(d: dict) -> list[str]:
    t = d["toc"]
    if not t.get("available"):
        return ["## 7. `.ee.toc`", "", "No `.toc` entry found.", ""]
    lines = [
        "## 7. `.ee.toc` (the load list)",
        "",
        f"{t['counts'][0]} records vs {t['counts'][1]}, of which "
        f"{t['external'][0]} / {t['external'][1]} are offset-0 (load from the global archives, "
        f"not from this container). Added {len(t['added'])}, removed {len(t['removed'])}.",
        "",
        "| kind | added | removed |",
        "|---|---|---|",
    ]
    for k in sorted(set(t["added_by_kind"]) | set(t["removed_by_kind"])):
        lines.append(f"| {k} | {t['added_by_kind'].get(k, 0)} | {t['removed_by_kind'].get(k, 0)} |")
    return lines


def md_implications(d: dict) -> list[str]:
    parts = d["parts"]
    return [
        "## 8. What B-05/B-06 must carry",
        "",
        "* **Two `CPartProp` nodes, not a new parts module.** The signature `epe` drops the plain "
        "`sportsmuscle_hood` part and adds `sportsmuscle_hood_signature` (index 25) with "
        "`sportsmuscle_missile_base_signature` (index 41) as its child. The parts module already "
        "defines both at every index in both variants; the instantiated tree is what changes.",
        f"* **Part indices are stable**: the modules define the same {len(parts['variant_rows'])} "
        f"parts at the same indices, and the two `epe`s differ only by which hood branch they "
        f"build, so the port keeps every index and adds nothing at the end.",
        "* **The art is a path swap on the parts the kit restyles.** "
        f"{sum(1 for c in parts['changed'] if 'model' in c['fields'])} of the "
        f"{len(parts['variant_rows'])} parts point at `signature/signature_*.lod`; the rest keep "
        "the base model. The paired `.rbm` files have the same block counts and the same AABBs, "
        "i.e. the kit is the same shell recompiled against the signature textures, not new "
        "geometry. A port should copy the part *links* and its own meshes, not assume a new shape.",
        "* **The root's content ids follow the kit.** `vehicle_parts` switches to the signature "
        "module hash (the one decoded in section 4), `decals` to a different hash, and `palette` "
        "is cleared to null in the variant, so the signature look is not a palette swap.",
        "* **The weapon is a four-tube missile pod on the hood.** One `CMissileWeaponBase` "
        "(`w618_sportsmuscle_missile`) with four type-2 `internal.fire_point.N` points, one "
        "`CAimPOIWeaponComponent`, four `SAttachedEffect` muzzle flashes (all "
        "`sportsmuscle_missile_muzzleflash.effc`, one per tube, at the tube positions), one "
        "`CForcePulse` (`...w618...ftune`) and one `CMaterialEffectTable` "
        "(`tank_explosion_effect_table`). The "
        "root `main_weapon` (`851CAABE`) is the only slot it uses; the other three are null.",
        "* **The missile reuses the RPG fire-leach projectile**, not a unique mesh: the component's "
        "model is `w143_rpg_fire_leach_projectile_body.model_xml`, and the signature container "
        "adds that mesh's five LODs and four textures.",
        "* **The tune is unguided and unlimited**: `missile_turning_speed` 0, no lock-on, "
        "`magazine_size` -1, `fire_rate` 0.5 s, `damage` 1500, `max_range` 300 m, blast "
        "1100 player / 500 AI in 8 m. Copy the tune values, not only the wiring.",
        "* **The interaction graph is unchanged.** Only the stunt-hood area name changes "
        "(`front_area` → `front_signature_area`). No seat, entry, exit or trigger is added, so "
        "the port does not need a new seat or action.",
        "* **Two root scalars remain unnamed** (`id:EA011E72` float 0.3→1, `id:FFE31EE1` int 1→0); "
        "no Jenkins candidate in the shipped vocabulary matched either. They are recorded, not "
        "guessed, and neither is a weapon slot.",
        "* **The VFS tune is the authoritative copy.** The container embeds an older 148-row "
        "`wtunec`; the patch path has 155 rows. The seven extras are six zero-valued schema "
        "members plus `fire_rate_level_2` = 0.12; values on the shared rows are identical.",
        "",
    ]


def md_validation(d: dict) -> list[str]:
    p = d["parts"]
    m = d["meshes"]
    eq = sum(1 for x in m["pairs"] if x["blocks"][0] == x["blocks"][1] and x["aabb_equal"])
    return [
        "## 9. Validation and limits",
        "",
        f"`jc3sigdiff.py --check` re-reads both `.ee`s out of the archives, converts the inner "
        f"`.epe`s again, rebuilds every section and compares `{JSON_NAME}` field-for-field and "
        f"`{MD_NAME}` byte-for-byte. It also asserts: the civilian has 0 weapon slots and the "
        f"variant 1; every variant part model the kit restyles points at `signature/` and no "
        f"civilian part does; the changed part fields are only "
        f"{', '.join(p['changed_fields']) or 'none'}; the two `epe`s instantiate "
        f"{len(p['epe_instantiated']['civilian'])} and {len(p['epe_instantiated']['variant'])} "
        f"parts and differ only by the hood branch they build; the weapon has four fire "
        f"points, each paired by position with its own muzzle, all four naming one effect "
        f"path; "
        f"all {len(m['pairs'])} mesh pairs keep their block count and AABB ({eq} of "
        f"{len(m['pairs'])}); the tune path in the graph exists as a VFS entry.",
        "",
        "**Limits.** The mesh comparison is header-level (block count, AABB, size); it does not "
        "decode vertex data, so `aabb_equal` means the same bounds, not the same vertices. "
        "`CMaterialEffectTable` is an opaque 30-byte hash blob (class `CMaterialEffectTable`); its "
        "contents are not decoded. The two unnamed root scalars are reported without a name. The "
        "diff is between these two entity builds only; no other v0300 variant is compared.",
        "",
    ]


def render_md(d: dict) -> str:
    lines = [
        "# The armed Serpente: civilian → signature_preorder",
        "",
        "The exact difference between `v0300_car_kensington_sportsmuscle_civilian_01` and "
        "`..._signature_preorder` (G2-12), read from the two `.ee` containers: every inner member, "
        "the `.epe` object graph and its weapon subtree, the parts modules, the mesh headers and "
        "the `w618` tunes. The "
        "point is to separate the *wiring* (what B-05/B-06 import) from the *art* (what the "
        "signature body kit is).",
        "",
        "## 1. Sources",
        "",
    ]
    lines += md_source_table(d)
    lines += ["", "The container member is the graph the game builds. The loose `.epe` entry next "
                 "to it is a different build (both sizes/hashes above), so it is not used for the "
                 "diff and not quoted as authoritative.", ""]
    lines += md_members(d)
    lines.append("")
    lines += md_graph(d)
    lines.append("")
    lines += md_weapon(d)
    lines.append("")
    lines += md_parts(d)
    lines.append("")
    lines += md_meshes(d)
    lines.append("")
    lines += md_tunes(d)
    lines.append("")
    lines += md_toc(d)
    lines.append("")
    lines += md_implications(d)
    lines.append("")
    lines += md_validation(d)
    return "\n".join(lines).rstrip() + "\n"


def invariant_checks(d: dict) -> list[str]:
    bad = []
    g = d["graph"]
    # civilian has no weapon; variant binds exactly one main_weapon
    slot = [x for x in d["graph"]["changed"]
            if x["class"] in ROOT_CLASSES and "id:851CAABE" in x["props"]]
    if len(slot) != 1:
        bad.append(f"expected one root main_weapon change, got {len(slot)}")
    else:
        v = slot[0]["props"]["id:851CAABE"]
        if v["before"] != "00000000" or not str(v["after"]).startswith("->"):
            bad.append(f"main_weapon change is not null->component: {v}")
    p = d["parts"]
    changed = set(p["changed_fields"])
    if changed - {"model", "model_swap"}:
        bad.append(f"unexpected part fields changed: {sorted(changed - {'model', 'model_swap'})}")
    roots = [x for x in d["graph"]["changed"] if x["class"] in ROOT_CLASSES]
    if len(roots) != 1:
        bad.append(f"expected one changed root, got {len(roots)}")
    else:
        props = roots[0]["props"]
        for key in ("vehicle_parts", "decals"):
            for side in ("before", "after"):
                if not props.get(key, {}).get(side + "_path"):
                    bad.append(f"root {key} {side} does not resolve to a container module")
        if not props.get("palette", {}).get("before_path"):
            bad.append("root palette before value does not resolve")
        if props.get("palette", {}).get("after") is not None:
            bad.append("root palette is not cleared in the variant")
        parts_after = props.get("vehicle_parts", {}).get("after_path", "")
        if "/signature/" not in parts_after:
            bad.append(f"variant vehicle_parts does not resolve to the signature module: {parts_after}")
    em = p["epe_instantiated"]
    if em["civilian_missing"] != [25, 41]:
        bad.append(f"civilian epe does not build exactly the non-signature hood branch: "
                   f"missing {em['civilian_missing']}")
    if em["variant_missing"] != [24]:
        bad.append(f"variant epe does not build exactly the signature hood branch: "
                   f"missing {em['variant_missing']}")
    module_indices = {r["index"] for r in p["variant_rows"]}
    for side, key in (("civilian", "civilian"), ("variant", "variant")):
        extra = set(em[key]) - module_indices
        if extra:
            bad.append(f"{side} epe instantiates part indices the module does not define: {sorted(extra)}")
    if p["civilian_signature_models"]:
        bad.append("civilian parts already point at signature/: "
                   f"{p['civilian_signature_models']}")
    w = d.get("weapon") or {}
    if not w.get("found"):
        bad.append("root main_weapon does not resolve to a weapon component")
    else:
        expect = [f"internal.fire_point.{i}" for i in range(4)]
        if sorted(p["name"] for p in w["points"]) != expect:
            bad.append(f"weapon points are not the four fire points: "
                       f"{[p['name'] for p in w['points']]}")
        if any(p["type"] != "2" for p in w["points"]):
            bad.append(f"a fire point is not type 2: {[p['type'] for p in w['points']]}")
        if len(w["muzzles"]) != len(w["points"]):
            bad.append(f"{len(w['points'])} points but {len(w['muzzles'])} muzzles")
        if any(p["muzzle"] is None for p in w["points"]):
            bad.append(f"a fire point has no muzzle at its position: "
                       f"{[p['name'] for p in w['points'] if not p['muzzle']]}")
        if len({m["effect"] for m in w["muzzles"]}) != 1:
            bad.append(f"muzzles do not share one effect: "
                       f"{sorted({m['effect'] for m in w['muzzles']})}")
        if any(not m["effect_path"] for m in w["muzzles"]):
            bad.append("a muzzle effect hash does not resolve to an indexed path")
        if any(m["effect_source"] != "container" for m in w["muzzles"]):
            bad.append("a muzzle effect is not a member of this .ee")
        if not w["aim"]:
            bad.append("weapon has no CAimPOIWeaponComponent")
        other_slots = {k: v for k, v in w["slots"].items() if k != "id:851CAABE"}
        if any(other_slots.values()):
            bad.append(f"the variant binds more than main_weapon: {other_slots}")
        if not w["slots"].get("id:851CAABE"):
            bad.append("main_weapon slot is null in the variant")
        if not (w["model"] or "").endswith(".model_xml"):
            bad.append(f"weapon model is not a .model_xml: {w['model']}")
    restyled = 0
    for c in p["changed"]:
        for field in ("model", "model_swap"):
            v = c["fields"].get(field)
            if v and "/signature/" not in v["after"]:
                bad.append(f"variant part {c['name']} {field} is not signature/: {v['after']}")
        if "model" in c["fields"]:
            restyled += 1
    if not restyled:
        bad.append("no part model is restyled to signature/, the kit is empty")
    for r in d["meshes"]["pairs"]:
        if r["blocks"][0] != r["blocks"][1] or not r["aabb_equal"]:
            bad.append(f"mesh pair {r['stem']} lost block count/AABB")
    if not d["tunes"].get("w618_sportsmuscle_missile.wtunec"):
        bad.append("w618 wtunec not found in the variant container")
    if not d["tunes"].get("vfs_wtunec"):
        bad.append("w618 wtunec VFS entry not found")
    return bad


def cmd_write() -> int:
    d = build()
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, JSON_NAME), "w", encoding="utf-8", newline="\n") as f:
        json.dump(d, f, indent=1, sort_keys=True, ensure_ascii=False)
        f.write("\n")
    with open(os.path.join(OUT, MD_NAME), "w", encoding="utf-8", newline="\n") as f:
        f.write(render_md(d))
    print(f"{JSON_NAME}: {d['members']['counts'][0]} -> {d['members']['counts'][1]} members, "
          f"graph {d['graph']['objects'][0]} -> {d['graph']['objects'][1]}, "
          f"{len(d['graph']['added'])} added / {len(d['graph']['removed'])} removed")
    print(f"{MD_NAME}: {len(open(os.path.join(OUT, MD_NAME), encoding='utf-8').read().splitlines())} lines")
    return 0


def cmd_check() -> int:
    d = build()
    bad = []
    jp = os.path.join(OUT, JSON_NAME)
    mp = os.path.join(OUT, MD_NAME)
    if not os.path.exists(jp) or not os.path.exists(mp):
        print(f"FAIL: {JSON_NAME}/{MD_NAME} missing")
        return 1
    old = json.load(open(jp, encoding="utf-8"))
    if old != d:
        for k in sorted(set(old) | set(d)):
            if old.get(k) != d.get(k):
                bad.append(f"json section changed: {k}")
                break
    md = render_md(d)
    current = open(mp, encoding="utf-8").read()
    if md != current:
        import difflib
        diff = list(difflib.unified_diff(current.splitlines(), md.splitlines(),
                                         "file", "rebuilt", n=1))
        bad.append("md differs: " + " | ".join(diff[2:8]))
    bad += invariant_checks(d)
    if bad:
        print("FAIL: " + "; ".join(bad))
        return 1
    print(f"PASS: {d['members']['counts'][0]} -> {d['members']['counts'][1]} members, "
          f"graph {d['graph']['objects'][0]} -> {d['graph']['objects'][1]} objects, "
          f"{len(d['graph']['added'])} added / {len(d['graph']['removed'])} removed, "
          f"{len(d['parts']['changed'])} part rows changed, "
          f"{len(d['meshes']['pairs'])} mesh pairs, "
          f"{len(d['graph']['changed'])} graph objects changed")
    return 0


def cmd_dump(what: str) -> int:
    d = build()
    keys = ["members", "graph", "weapon", "parts", "meshes", "tunes", "toc"]
    for k in keys if what == "all" else [what]:
        if k not in d:
            print(f"no section {k}; one of {', '.join(keys)}")
            return 2
        print(json.dumps(d[k], indent=1, sort_keys=True, ensure_ascii=False)[:12000])
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    d = sub.add_parser("dump")
    d.add_argument("what")
    a = p.parse_args()
    if a.cmd == "dump":
        return cmd_dump(a.what)
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

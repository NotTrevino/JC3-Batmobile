"""jc3detail.py - grab the entity graph (`.epe`) and mesh bounds (`.rbm`) of every vehicle (G2-5/G2-6).

`jc3grab.py` decodes the `.vmodc` modules (the *values*). This script reads the two
things that describe *shape and structure*, both of which live inside the same `.ee`:

  `.epe`  RTPC property file: the entity's object graph. `CCar` at the root, a
          `CParts` node with one `CPartProp` per mesh part (`name`, `part_index`),
          plus `SVehicleLight`, `SAttachedEffect`, `CCameraModifier`, interaction
          graph nodes and so on. Decoded with Gibbed's ConvertProperty.
  `.rbm`  RenderBlockModel: the RBMDL header carries the mesh's local AABB, LOD tag
          and block count - enough to compare shapes across the fleet without
          touching payloads (`rbmhdr.parse_header`, which works on bytes because
          these meshes never exist as files).

`.physicsc` is deliberately NOT decoded here: the bytes are a **Havok 2014.1
packfile** (`W\\xe0\\xe0W` + `__classnames__`/`__types__`/`__data__` sections), not an
RTPC file, so it needs a Havok reader rather than ConvertProperty. See G2-8 in
`Research/JC3Grab/README.md`.

Usage:
  python jc3detail.py build --all            # every vehicle .ee (raw JSON outside the repo)
  python jc3detail.py build --entity v0300
  python jc3detail.py report                 # ENTITIES.md + part tables
  python jc3detail.py check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from jc3index import DEFAULT_GAME, DEFAULT_OUT, load_index, MOUNT_RANK  # noqa: E402
from eetoc import unaaf, sarc_dir  # noqa: E402
from rbmhdr import parse_header, RbmError  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
CONVERT = os.path.join(TOOLS, "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
OUT = os.path.join(ROOT, "Research", "JC3Grab")


# ------------------------------------------------------------------ helpers

def vehicle_ees(rows: list[dict], only: str | None) -> list[str]:
    out = set()
    for r in rows:
        p = r["path"]
        if p.startswith("editor/entities/jc_vehicles/") and p.endswith(".ee"):
            if not only or only.lower() in p.lower():
                out.add(p)
    return sorted(out)


def pick(rows: list[dict], path: str) -> dict:
    hits = [r for r in rows if r["path"] == path]
    return sorted(hits, key=lambda r: MOUNT_RANK[r["mount"]])[-1]


# --------------------------------------------------------------- epe graph

def parse_epe(xml_path: str) -> dict:
    root = ET.parse(xml_path).getroot()
    classes: dict[str, int] = {}
    objects: list[dict] = []
    parts: list[dict] = []

    def walk(el: ET.Element, parent: str, depth: int) -> None:
        idx = 0
        for ch in el:
            if ch.tag != "object":
                continue
            oid = ch.get("id") or str(idx)
            idx += 1
            node = f"{parent}/{ch.get('name') or '?'}"
            vals = {}
            cls = None
            for v in ch:
                if v.tag != "value":
                    continue
                nm = v.get("name")
                if not nm:
                    continue
                txt = (v.text or "").strip()
                vals[nm] = txt
                if nm == "_class":
                    cls = txt
            if cls:
                classes[cls] = classes.get(cls, 0) + 1
            rec = {
                "id": oid,
                "node": node,
                "depth": depth,
                "class": cls,
                "name": vals.get("name"),
                "values": {k: v for k, v in vals.items()
                           if k not in ("_class", "tags") and len(v) < 80},
            }
            objects.append(rec)
            if cls == "CPartProp":
                parts.append({
                    "part_index": int(vals.get("part_index", -1) or -1),
                    "name": vals.get("name"),
                    "node": node,
                })
            walk(ch, node, depth + 1)

    walk(root, "", 0)
    parts.sort(key=lambda p: p["part_index"])
    return {"objects": objects, "classes": classes, "parts": parts}


def decode_epe(blob: bytes, work: str, tag: str) -> dict | None:
    src = os.path.join(work, tag + ".epe")
    dst = os.path.join(work, tag + ".xml")
    with open(src, "wb") as f:
        f.write(blob)
    try:
        r = subprocess.run([CONVERT, "--e", src, dst], capture_output=True)
        if r.returncode != 0 or not os.path.exists(dst):
            return None
        return parse_epe(dst)
    finally:
        for p in (src, dst):
            try:
                os.remove(p)
            except OSError:
                pass


# -------------------------------------------------------------- entity pass

def grab(ee_path: str, rows: list[dict], opt) -> dict:
    r = pick(rows, ee_path)
    arc = os.path.join(opt.game, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        raw = f.read(r["size"])
    stream, entries = inner_files(raw)

    work = os.path.join(RAW, "tmp_epe")
    os.makedirs(work, exist_ok=True)
    epe = None
    meshes = []
    physics = []
    for name, off, size in entries:
        blob = stream[off:off + size]
        if name.endswith(".epe") and epe is None:
            epe = decode_epe(blob, work, "ent")
            if epe is not None:
                epe["file"] = name
        elif name.endswith(".rbm"):
            try:
                h = parse_header(blob[:4096])
            except RbmError as e:
                meshes.append({"path": name, "error": str(e)})
                continue
            meshes.append({
                "path": name,
                "size_m": h["size_m"],
                "min": h["min"],
                "max": h["max"],
                "blocks": h["block_count"],
                "version": h["version"],
            })
        elif name.endswith(".physicsc"):
            physics.append({"path": name, "size": size,
                            "magic": blob[:4].hex().upper(),
                            "sections": [s.decode() for s in
                                         (b"__classnames__", b"__types__", b"__data__")
                                         if s in blob[:0x400]]})
    return {
        "entity": ee_path,
        "source": {"archive": r["archive"], "offset": r["offset"], "size": r["size"]},
        "epe": epe,
        "meshes": meshes,
        "physics": physics,
    }


def inner_files(raw: bytes):
    stream = unaaf(raw)
    return stream, sarc_dir(stream)


def slug(ee_path: str) -> str:
    parent = ee_path.rsplit("/", 1)[0].rsplit("/", 1)[-1]
    return f"{parent}__{ee_path.rsplit('/', 1)[-1]}"


def cmd_build(a) -> int:
    rows = load_index(a.index)
    targets = vehicle_ees(rows, a.entity)
    if a.limit:
        targets = targets[:a.limit]
    os.makedirs(os.path.join(RAW, "detail"), exist_ok=True)
    print(f"{len(targets)} entities")
    index = []
    for i, p in enumerate(targets, 1):
        try:
            doc = grab(p, rows, a)
        except Exception as e:  # one bad bundle must not kill a 232-entity sweep
            print(f"[{i}/{len(targets)}] {os.path.basename(p)}: ERROR {e}")
            continue
        path = os.path.join(RAW, "detail", slug(p) + ".json")
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(doc, f, indent=0)
        nparts = len(doc["epe"]["parts"]) if doc["epe"] else 0
        print(f"[{i}/{len(targets)}] {os.path.basename(p)}: "
              f"{len(doc['meshes'])} meshes, "
              f"{len(doc['epe']['objects']) if doc['epe'] else 0} objects, {nparts} parts")
        index.append({"entity": p, "meshes": len(doc["meshes"]), "parts": nparts,
                      "path": os.path.relpath(path, RAW).replace("\\", "/")})
    with open(os.path.join(RAW, "detail_index.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(index, f, indent=1)
        f.write("\n")
    return 0


# ------------------------------------------------------------------ report

def load_detail() -> list[dict]:
    d = os.path.join(RAW, "detail")
    if not os.path.isdir(d):
        raise SystemExit(f"nothing grabbed under {d}")
    return [json.load(open(os.path.join(d, fn), encoding="utf-8"))
            for fn in sorted(os.listdir(d)) if fn.endswith(".json")]


def mesh_class(p: str) -> str:
    base = p.rsplit("/", 1)[-1]
    base = re.sub(r"\.rbm$", "", base, flags=re.I)
    base = re.sub(r"_lod\d+$", "", base, flags=re.I)
    return base


def cmd_report(a) -> int:
    docs = load_detail()
    lines = ["# JC3 vehicle entities — structure and shape", "",
             f"Derived from **{len(docs)}** decoded `.epe` graphs and their `.rbm` headers by",
             "`Tools/scripts/jc3detail.py`. Raw decodes stay outside the repo.", ""]

    cls_all: dict[str, int] = {}
    for d in docs:
        if d["epe"]:
            for k, v in d["epe"]["classes"].items():
                cls_all[k] = cls_all.get(k, 0) + v
    lines += ["## Class inventory (all entities)", "",
              "| class | occurrences |", "|---|---|"]
    for k, v in sorted(cls_all.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{k}` | {v} |")
    lines.append("")

    parts_counts = sorted(len(d["epe"]["parts"]) for d in docs if d["epe"])
    lines += ["## Parts", "",
              f"`CPartProp` per entity: min **{parts_counts[0]}**, median "
              f"**{parts_counts[len(parts_counts) // 2]}**, max **{parts_counts[-1]}** "
              f"(n={len(parts_counts)}).", ""]

    donor = [d for d in docs if a.donor.lower() in d["entity"].lower()]
    if donor and donor[0]["epe"]:
        d = donor[0]
        lines += [f"### Donor parts — `{d['entity'].rsplit('/', 1)[-1]}`", "",
                  "| part_index | name |", "|---|---|"]
        for p in d["epe"]["parts"]:
            lines.append(f"| {p['part_index']} | `{p['name']}` |")
        lines.append("")

    # lights: the fleet's own vocabulary, which is what LGT-1 needed
    light_counts = []
    presets: dict[str, int] = {}
    for d in docs:
        if not d["epe"]:
            continue
        ls = [o for o in d["epe"]["objects"] if o["class"] == "SVehicleLight"]
        light_counts.append(len(ls))
        for o in ls:
            p = o["values"].get("preset_id") or "(none)"
            presets[p] = presets.get(p, 0) + 1
    lines += ["## Lights (`SVehicleLight`)", ""]
    if light_counts:
        light_counts.sort()
        lines += [f"Lights per entity: min **{light_counts[0]}**, median "
                  f"**{light_counts[len(light_counts) // 2]}**, max **{light_counts[-1]}** "
                  f"(n={len(light_counts)}).", ""]
    lines += ["### Preset vocabulary (fleet)", "", "| preset_id | uses |", "|---|---|"]
    for k, v in sorted(presets.items(), key=lambda kv: -kv[1])[:24]:
        lines.append(f"| `{k}` | {v} |")
    lines.append("")
    if donor and donor[0]["epe"]:
        d = donor[0]
        ls = [o for o in d["epe"]["objects"] if o["class"] == "SVehicleLight"]
        if ls:
            lines += [f"### Donor lights — {len(ls)} entries", "",
                      "| name | preset | diffuse | radius | spot | volumetric |",
                      "|---|---|---|---|---|---|"]
            for o in ls:
                v = o["values"]
                lines.append(f"| `{v.get('name', '')}` | `{v.get('preset_id', '')}` | "
                             f"{v.get('diffuse', '')} | {v.get('radius', '')} | "
                             f"{v.get('spot_angle', '')} | {v.get('volumetric_mode', '')} |")
            lines.append("")

    lines += ["## Meshes", "",
              "| item | value |", "|---|---|"]
    mesh_counts = [len(d["meshes"]) for d in docs]
    sizes = [max((m["size_m"]["z"] for m in d["meshes"] if "size_m" in m), default=0) for d in docs]
    lines += [f"| meshes per entity | min {min(mesh_counts)} / median "
              f"{sorted(mesh_counts)[len(mesh_counts) // 2]} / max {max(mesh_counts)} |",
              f"| longest mesh (z) per entity | max {max(sizes):.3f} m |",
              f"| RBM versions | " + ", ".join(sorted({m['version'] for d in docs
                                                     for m in d['meshes'] if 'version' in m})) + " |",
              ""]

    # the biggest mesh per entity is a decent proxy for "the car body"
    biggest = []
    for d in docs:
        body = max((m for m in d["meshes"] if "size_m" in m),
                   key=lambda m: m["size_m"]["x"] * m["size_m"]["y"] * m["size_m"]["z"],
                   default=None)
        if body:
            biggest.append((d["entity"], body))
    biggest.sort(key=lambda t: -t[1]["size_m"]["x"] * t[1]["size_m"]["y"] * t[1]["size_m"]["z"])
    lines += ["### Largest mesh per entity (top 15)", "",
              "| entity | mesh | size x×y×z (m) |", "|---|---|---|"]
    for ent, m in biggest[:15]:
        s = m["size_m"]
        lines.append(f"| `{ent.rsplit('/', 2)[-2]}/{ent.rsplit('/', 1)[-1]}` | "
                     f"`{m['path'].rsplit('/', 1)[-1]}` | {s['x']} × {s['y']} × {s['z']} |")
    lines.append("")

    phys = [(d["entity"], p) for d in docs for p in d["physics"]]
    lines += ["## `.physicsc` (not decoded)", "",
              f"{len(phys)} files across {len({e for e, _ in phys})} entities; every one starts "
              "with the Havok 2014 packfile tag `57E0E057` and carries "
              "`__classnames__` / `__types__` / `__data__` sections. That is a Havok binary "
              "packfile, not an RTPC property file, so `ConvertProperty` cannot read it. "
              "See G2-8.", ""]

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "ENTITIES.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"ENTITIES.md: {len(docs)} entities, {len(cls_all)} classes written")
    return 0


def cmd_check(a) -> int:
    docs = load_detail()
    problems = []
    if len(docs) != 232:
        problems.append(f"entities {len(docs)} != 232")
    no_epe = [d["entity"] for d in docs if not d["epe"]]
    if no_epe:
        problems.append(f"{len(no_epe)} entities without an .epe")
    no_mesh = [d["entity"] for d in docs if not d["meshes"]]
    if no_mesh:
        problems.append(f"{len(no_mesh)} entities without meshes")
    donor = [d for d in docs if "v0300_car_kensington_sportsmuscle_civilian_01" in d["entity"]]
    if not donor:
        problems.append("donor not in the detail set")
    else:
        d = donor[0]
        parts = d["epe"]["parts"]
        body = [p for p in parts if p["name"] == "sportsmuscle_body"]
        print(f"donor: {len(d['meshes'])} meshes, {len(parts)} parts, "
              f"body part_index={body[0]['part_index'] if body else None}, "
              f"{len(d['physics'])} physicsc")
        if not body:
            problems.append("donor .epe has no sportsmuscle_body part")
        if len(d["meshes"]) != 198:
            problems.append(f"donor meshes {len(d['meshes'])} != 198")
    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    print("check ok")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="grab .epe + .rbm headers for vehicles")
    b.add_argument("--entity", help="substring filter")
    b.add_argument("--all", action="store_true")
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)
    r = sub.add_parser("report", help="write ENTITIES.md")
    r.add_argument("--donor", default="v0300_car_kensington_sportsmuscle_civilian_01")
    r.set_defaults(func=cmd_report)
    c = sub.add_parser("check", help="assert the detail grab is complete")
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()

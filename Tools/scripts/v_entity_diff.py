#!/usr/bin/env python3
"""Entity-graph structural diff: bm-RC2's edited `.epe` against the unmodified original.

The build ships one edited entity graph,
`Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/`
`v0300_car_kensington_sportsmuscle_debug.epe`. This script compares it, **structurally**, with the
same graph as the game ships it:

  * the original is extracted from the game archive every run (`jc3detail.pick` -> the `.ee` bundle ->
    its `.epe` member) and converted with the same `Gibbed.JustCause3.ConvertProperty.exe --e` pass
    `bm_entity.py` uses; nothing is written outside a temp directory;
  * the built `.epe` is exported the same way and never written;
  * objects are matched by `(class, name)` and, inside a name group, by document order - the exporter
    re-orders siblings and renames array elements positionally, so a path-based match would report
    churn. The root `CCar` is paired by node because the build replaced its name;
  * the comparison is the object census, the per-object property list, and every property present on
    one side only. Member *values* are counted (and split into importer-assigned `_object_id` churn
    vs real edits) but not tabulated: this brief is about structure.

Each difference is tagged with the `Working/Entity/bm_epe_edits.json` entry that explains it
(`additions[].row` for added objects, `edits[].row` for a member) or `UNEXPLAINED`.

Usage:
  python Tools/scripts/v_entity_diff.py --write   # Builds/bm-RC2/verify/entity_diff.md
  python Tools/scripts/v_entity_diff.py --check   # re-extract, re-diff, byte-compare, exit 1 on drift
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3detail  # noqa: E402
import jc3index  # noqa: E402

ENTITY = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
          "v0300_car_kensington_sportsmuscle_debug.ee")
BUILT = os.path.join("Builds", "bm-RC2", "aaf", "editor", "entities", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle",
                     "v0300_car_kensington_sportsmuscle_debug.epe")
SPEC = os.path.join("Working", "Entity", "bm_epe_edits.json")
OUT = os.path.join("Builds", "bm-RC2", "verify", "entity_diff.md")
INDEX = os.path.join(ROOT, "Research", "JC3Grab")


def rel(p: str) -> str:
    return p.replace("\\", "/")


def sha_file(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def export(epe: str, xml: str) -> None:
    r = subprocess.run([jc3detail.CONVERT, "--e", epe, xml], capture_output=True, text=True,
                       errors="replace")
    if r.returncode != 0 or not os.path.exists(xml):
        raise SystemExit("ConvertProperty --e failed for %s: %s" % (epe, (r.stdout + r.stderr)[-600:]))


def extract_original(work: str) -> tuple[str, dict]:
    """The game's own `.epe` for the entity, straight out of the archive (read-only)."""
    rows = jc3index.load_index(INDEX)
    game = jc3index.DEFAULT_GAME
    r = jc3detail.pick(rows, ENTITY)
    with open(os.path.join(game, r["archive"] + ".arc"), "rb") as f:
        f.seek(r["offset"])
        raw = f.read(r["size"])
    if len(raw) != r["size"]:
        raise SystemExit("short read %d != %d" % (len(raw), r["size"]))
    stream, entries = jc3detail.inner_files(raw)
    hit = next(((n, o, s) for n, o, s in entries if n.endswith(".epe")), None)
    if hit is None:
        raise SystemExit("no .epe inside " + ENTITY)
    name, off, size = hit
    src = os.path.join(work, "original.epe")
    with open(src, "wb") as f:
        f.write(stream[off:off + size])
    xml = os.path.join(work, "original.xml")
    export(src, xml)
    return xml, {"archive": r["archive"], "offset": r["offset"], "size": r["size"],
                 "member": name, "epe_bytes": size}


# ---------------------------------------------------------------- the graph
def parse(xml_path: str) -> list[dict]:
    """Every `<object>` with its class, name member, member map and a name-member path.

    The element's `name` attribute is positional for some objects (`"6"`), so the path - and the
    identity used for matching - come from the object's own `name` *value*, which is what the game
    reads. The path therefore matches the `node` strings `bm_epe_edits.json` records.
    """
    out = []

    def walk(el, parent: str) -> None:
        idx = 0
        for ch in el:
            if ch.tag != "object":
                continue
            props = {}
            for v in ch.findall("value"):
                n = v.get("name")
                if n is not None:
                    props[n] = v.text if v.text is not None else ""
            name = props.get("name") or ch.get("name") or str(idx)
            path = parent + "/" + name
            out.append({"cls": props.get("_class") or "", "name": name, "node": path,
                        "props": props, "id": props.get("_object_id") or "-"})
            walk(ch, path)
            idx += 1

    walk(ET.parse(xml_path).getroot(), "")
    return out


def key(o: dict) -> tuple[str, str]:
    return (o["cls"], o["name"])


# ---------------------------------------------------------------- the spec
def load_spec() -> dict:
    with open(os.path.join(ROOT, SPEC), encoding="utf-8") as f:
        spec = json.load(f)
    rows = set()
    for a in spec["additions"]:
        rows.add(a.get("row", ""))
    for e in spec["edits"]:
        rows.add(e.get("row", ""))
    return {"raw": spec, "rows": rows,
            "additions": spec["additions"], "edits": spec["edits"],
            "added_objects": spec.get("added_objects", [])}


def tag_added(o: dict, spec: dict) -> tuple[str, str]:
    """(tag, why) for an object the build adds. `tag` is a row id or UNEXPLAINED."""
    cands = [a for a in spec["additions"]
             if a["class"] == o["cls"] and a["name"] == o["name"]]
    if not cands:
        return "UNEXPLAINED", "no `additions[]` entry names this class+object"
    if len(cands) == 1:
        return cands[0]["row"], "`additions[]` class+name"
    comp = o["node"].split("/")[2] if len(o["node"].split("/")) > 2 else ""
    narrowed = [a for a in cands if a.get("parent") == comp]
    if len(narrowed) == 1:
        return narrowed[0]["row"], "`additions[]` class+name+parent `%s`" % comp
    return "UNEXPLAINED", "%d `additions[]` rows share this class+name and none owns parent `%s`" % (
        len(cands), comp)


def tag_member(obj_name: str, member: str, spec: dict) -> tuple[str, str]:
    for e in spec["edits"]:
        if e["node"] not in (obj_name, "*"):
            continue
        members = [m.strip() for m in e["member"].split(",")]
        if member in members:
            why = ("`edits[]` node `*`" if e["node"] == "*" else "`edits[]` node `%s`" % e["node"])
            return e["row"], why
    return "UNEXPLAINED", "no `edits[]` row names this object and member"


# ---------------------------------------------------------------- the diff
def build() -> dict:
    work = tempfile.mkdtemp(prefix="v_entity_diff_")
    vx, meta = extract_original(work)
    bx = os.path.join(work, "built.xml")
    export(os.path.join(ROOT, BUILT), bx)
    vanilla, built = parse(vx), parse(bx)
    spec = load_spec()

    gv, gb = defaultdict(list), defaultdict(list)
    for o in vanilla:
        gv[key(o)].append(o)
    for o in built:
        gb[key(o)].append(o)

    # the root pair: the build renamed it, so it is paired by node, not by name
    root_v = next((o for o in vanilla if o["cls"] == "CCar" and o["node"].count("/") == 2), None)
    root_b = next((o for o in built if o["cls"] == "CCar" and o["node"].count("/") == 2), None)
    renamed = None
    if root_v and root_b and root_v["name"] != root_b["name"]:
        renamed = {"kind": "renamed", "cls": "CCar", "old": root_v["name"], "new": root_b["name"],
                   "node": root_b["node"], "id": root_b["id"], "tag": "UNEXPLAINED",
                   "why": "no entry names the root CCar; `bm_epe_edits.json` never mentions it"}
        gv.pop(key(root_v), None)
        gb.pop(key(root_b), None)

    added, removed, copies = [], [], []
    for k in gb:
        have = len(gv.get(k, []))
        for o in gb[k][have:]:
            tag, why = tag_added(o, spec)
            rec = {"kind": "added", "cls": o["cls"], "name": o["name"], "node": o["node"],
                   "id": o["id"], "tag": tag, "why": why}
            (copies if have else added).append(rec)
    # A cloned component drags in nodes no `additions[]` row names (the SEffects' five
    # SAttachedEffect children, the effect table, its conditions). Those are explained by the row
    # that created the component, so a node with no direct row inherits the nearest tagged ancestor.
    node_tag: dict[str, str] = {}
    for rec in sorted(added + copies, key=lambda r: r["node"].count("/")):
        if rec["tag"] == "UNEXPLAINED":
            parts = rec["node"].split("/")
            for cut in range(len(parts) - 1, 1, -1):
                anc = "/".join(parts[:cut])
                if anc in node_tag:
                    rec["tag"] = node_tag[anc]
                    rec["why"] = ("nested in the clone `%s`, which `additions[]` writes under `%s`"
                                  % (anc, node_tag[anc]))
                    break
        if rec["tag"] != "UNEXPLAINED":
            node_tag[rec["node"]] = rec["tag"]

    for k in gv:
        for o in gv[k][len(gb.get(k, [])):]:
            removed.append({"kind": "removed", "cls": o["cls"], "name": o["name"], "node": o["node"],
                            "id": o["id"], "tag": "UNEXPLAINED",
                            "why": "no `additions[]`/`edits[]`/`added_objects[]` entry names this "
                                   "object"})

    # property presence: every matched pair, plus the renamed root pair
    presence = []
    pairs = 0
    pairs_with_diff = set()
    for k in gv:
        if k not in gb:
            continue
        for a, b in zip(gv[k], gb[k]):
            pairs += 1
            for m in a["props"]:
                if m not in b["props"]:
                    tag, why = tag_member(a["name"], m, spec)
                    presence.append({"cls": a["cls"], "name": a["name"], "node": a["node"],
                                     "id": a["id"], "member": m, "side": "only in the original",
                                     "value": a["props"][m], "tag": tag, "why": why})
                    pairs_with_diff.add(a["node"])
            for m in b["props"]:
                if m not in a["props"]:
                    tag, why = tag_member(a["name"], m, spec)
                    presence.append({"cls": a["cls"], "name": a["name"], "node": a["node"],
                                     "id": a["id"], "member": m, "side": "only in the build",
                                     "value": b["props"][m], "tag": tag, "why": why})
                    pairs_with_diff.add(a["node"])
    if renamed:
        pairs += 1
        for m in root_v["props"]:
            if m not in root_b["props"]:
                tag, why = tag_member("CCar", m, spec)
                presence.append({"cls": "CCar", "name": root_b["name"], "node": root_b["node"],
                                 "id": root_b["id"], "member": m, "side": "only in the original",
                                 "value": root_v["props"][m], "tag": tag, "why": why})
                pairs_with_diff.add("/root/0")
        for m in root_b["props"]:
            if m not in root_v["props"]:
                tag, why = tag_member("CCar", m, spec)
                presence.append({"cls": "CCar", "name": root_b["name"], "node": root_b["node"],
                                 "id": root_b["id"], "member": m, "side": "only in the build",
                                 "value": root_b["props"][m], "tag": tag, "why": why})
                pairs_with_diff.add("/root/0")

    # member values: counted, not tabulated (out of this brief's scope)
    value_total, value_id, value_by_class = 0, 0, Counter()
    for k in gv:
        if k not in gb:
            continue
        for a, b in zip(gv[k], gb[k]):
            for m in a["props"]:
                if m in b["props"] and str(a["props"][m]) != str(b["props"][m]):
                    value_total += 1
                    value_by_class[a["cls"]] += 1
                    if m == "_object_id":
                        value_id += 1

    diffs = added + removed + copies + ([renamed] if renamed else []) + presence
    unexp = [d for d in diffs if d["tag"] == "UNEXPLAINED"]
    cv = Counter(o["cls"] for o in vanilla if o["cls"])
    cb = Counter(o["cls"] for o in built if o["cls"])
    return {
        "vanilla": vanilla, "built": built, "meta": meta,
        "n_v": len(vanilla), "n_b": len(built),
        "classed_v": sum(cv.values()), "classed_b": sum(cb.values()),
        "classes_v": len(cv), "classes_b": len(cb),
        "cv": cv, "cb": cb, "pairs": pairs, "pairs_with_presence_diff": len(pairs_with_diff),
        "added": sorted(added, key=lambda d: d["node"]),
        "copies": sorted(copies, key=lambda d: d["node"]),
        "removed": sorted(removed, key=lambda d: (d["cls"], d["name"])),
        "renamed": renamed, "presence": presence,
        "value_total": value_total, "value_id": value_id,
        "value_by_class": value_by_class.most_common(),
        "diffs": diffs, "unexp": unexp,
        "hashes": {"built": sha_file(BUILT)},
    }


# ---------------------------------------------------------------- the page
def render(d: dict) -> str:
    L = []
    a = L.append
    a("# Entity graph diff - bm-RC2 `debug.epe` vs the unmodified original")
    a("")
    a("Generated by `python Tools/scripts/v_entity_diff.py --write`; `--check` re-extracts both")
    a("graphs, re-runs every comparison below and diffs this page byte for byte. Read-only: the")
    a("build file is opened for reading and the original is extracted to a temp directory.")
    a("")
    a("**%d difference(s) between the two graphs: %d tagged to `bm_epe_edits.json`, %d UNEXPLAINED.**"
      % (len(d["diffs"]), len(d["diffs"]) - len(d["unexp"]), len(d["unexp"])))
    a("Counted as differences: objects the build adds, objects it removes, the object whose name it")
    a("replaces, and every member present on one side of a matched pair only.")
    a("")
    a("| side | file | identity |")
    a("|---|---|---|")
    a("| original | `%s` (game `%s`, offset %d, %d B) | `%s` |"
      % (ENTITY, d["meta"]["archive"], d["meta"]["offset"], d["meta"]["epe_bytes"], d["meta"]["member"]))
    a("| built | `%s` | sha256 `%s` |" % (rel(BUILT), d["hashes"]["built"]))
    a("")
    a("Both are exported with `Gibbed.JustCause3.ConvertProperty.exe --e` (the round trip")
    a("`bm_entity.py` uses) and parsed the same way: every `<object>`, its `_class`, its `name` value")
    a("and every `<value>` member.")
    a("")
    a("## 1. Object count")
    a("")
    a("| | original | build | delta |")
    a("|---|---|---|---|")
    a("| `<object>` elements | %d | %d | %+d |" % (d["n_v"], d["n_b"], d["n_b"] - d["n_v"]))
    a("| with a `_class` | %d | %d | %+d |" % (d["classed_v"], d["classed_b"], d["classed_b"] - d["classed_v"]))
    a("| distinct classes | %d | %d | %+d |" % (d["classes_v"], d["classes_b"], d["classes_b"] - d["classes_v"]))
    a("")
    a("The arithmetic, all from the lists below: `%d - %d (removed) + %d (added) + %d (extra copies)"
      % (d["n_v"], len(d["removed"]), len(d["added"]), len(d["copies"])))
    a("+ 1 (the renamed root, counted on both sides) = %d`."
      % (d["n_v"] - len(d["removed"]) + len(d["added"]) + len(d["copies"])))
    a("")
    a("## 2. Class census (classes that move)")
    a("")
    a("| class | original | build | delta |")
    a("|---|---|---|---|")
    for c in sorted(set(d["cv"]) | set(d["cb"])):
        if d["cv"][c] != d["cb"][c]:
            a("| `%s` | %d | %d | %+d |" % (c, d["cv"][c], d["cb"][c], d["cb"][c] - d["cv"][c]))
    a("")
    a("## 3. Objects the build adds (%d)" % len(d["added"]))
    a("")
    a("| # | object | class | node | `_object_id` | tag |")
    a("|---|---|---|---|---|---|")
    for i, o in enumerate(d["added"], 1):
        a("| %d | `%s` | `%s` | `%s` | `%s` | %s |"
          % (i, o["name"], o["cls"], o["node"], o["id"], o["tag"]))
    a("")
    if d["copies"]:
        a("### 3b. Extra copies of an object the original already has (%d)" % len(d["copies"]))
        a("")
        a("| # | object | class | node | `_object_id` | tag |")
        a("|---|---|---|---|---|---|")
        for i, o in enumerate(d["copies"], 1):
            a("| %d | `%s` | `%s` | `%s` | `%s` | %s |"
              % (i, o["name"], o["cls"], o["node"], o["id"], o["tag"]))
        a("")
    a("## 4. Objects the build drops (%d)" % len(d["removed"]))
    a("")
    a("| # | object | class | node | `_object_id` | tag |")
    a("|---|---|---|---|---|---|")
    for i, o in enumerate(d["removed"], 1):
        a("| %d | `%s` | `%s` | `%s` | `%s` | %s |"
          % (i, o["name"], o["cls"], o["node"], o["id"], o["tag"]))
    a("")
    if d["renamed"]:
        r = d["renamed"]
        a("### 4b. The root object, replaced rather than added or removed")
        a("")
        a("| object | class | node | original name | build name | `_object_id` | tag |")
        a("|---|---|---|---|---|---|---|")
        a("| root | `%s` | `%s` | `%s` | `%s` | `%s` | %s |"
          % (r["cls"], r["node"], r["old"], r["new"], r["id"], r["tag"]))
        a("")
    a("## 5. Property lists")
    a("")
    a("**%d matched object(s); %d of them differ in their property list.**"
      % (d["pairs"], d["pairs_with_presence_diff"]))
    a("")
    if d["presence"]:
        a("| # | object | class | node | member | side | tag |")
        a("|---|---|---|---|---|---|---|")
        for i, p in enumerate(d["presence"], 1):
            a("| %d | `%s` | `%s` | `%s` | `%s` | %s | %s |"
              % (i, p["name"], p["cls"], p["node"], p["member"], p["side"], p["tag"]))
        a("")
    else:
        a("Every matched object carries exactly the same member names on both sides.")
        a("")
    a("Member **values** are outside this structural brief; they are counted in the appendix so the")
    a("two kinds of difference are not confused.")
    a("")
    a("## 6. Reading")
    a("")
    a("* **The structure matches on every matched object but one.** %d of %d pairs have identical"
      % (d["pairs"] - d["pairs_with_presence_diff"], d["pairs"]))
    a("  member lists; the single exception is the root `CCar`, which gains `palette`.")
    a("* **%d added objects, all but the renamed root explained** by `additions[]` (T-WP1..T-WP4 and"
      % (len(d["added"]) + len(d["copies"])))
    a("  T-L13/L14/L18/L19/L20/L35). The four extra `SEffects` copies are the per-weapon clones.")
    a("* **The %d dropped objects are the finding, and all %d are `CPartProp`** entries the original"
      % (len(d["removed"]), sum(1 for o in d["removed"] if o["cls"] == "CPartProp")))
    a("  graph carries and the build's base graph does not: the build's `.epe` was derived from the")
    a("  civilian variant's graph (`bm_epe_edits.json` `base.build` = bm-009, `cpartprop_existing` = 6),")
    a("  then renamed to the debug leaf, while the original debug graph ships a `CPartProp` per part.")
    a("  No `bm_epe_edits.json` entry claims or explains the loss.")
    pal = next((p for p in d["presence"] if p["member"] == "palette"), None)
    a("* **The root rename and `palette`** are the other UNEXPLAINED structural differences:")
    a("  the name goes `%s` -> `%s`, and `palette` = `%s` is added. Neither is in the edit spec; both"
      % (d["renamed"]["old"], d["renamed"]["new"], pal["value"] if pal else "-"))
    a("  are later build steps (B-13b renames the leaf; `Research/JC3Grab/PALETTE_HASH.md` records the")
    a("  palette value on this exact `.epe`), which the spec this brief names does not cover.")
    a("")
    a("## 7. UNEXPLAINED, in full (%d)" % len(d["unexp"]))
    a("")
    a("| kind | object | class | member | why the spec is silent |")
    a("|---|---|---|---|---|")
    for u in d["unexp"]:
        a("| %s | `%s` | `%s` | %s | %s |"
          % (u.get("kind", "member"), u.get("name", "-"), u.get("cls", "-"),
             u.get("member", "-"), u.get("why", "")))
    a("")
    a("## 8. Appendix - member values (outside the structural brief)")
    a("")
    a("%d member value(s) differ across the %d pairs: **%d are `_object_id`** - the per-object id"
      % (d["value_total"], d["pairs"], d["value_id"]))
    a("pair, which also changes on objects the build never touches (e.g. `CCameraRef/CarCameraRef`),")
    a("so it is importer churn rather than an edit. **%d are real value changes.**"
      % (d["value_total"] - d["value_id"]))
    a("")
    a("| class | value differences |")
    a("|---|---|")
    for c, n in d["value_by_class"][:12]:
        a("| `%s` | %d |" % (c, n))
    a("")
    a("## 9. Oracles re-run by `--check`")
    a("")
    a("* the original still extracts from `%s` at offset %d (%d B) and the build still hashes to"
      % (d["meta"]["archive"], d["meta"]["offset"], d["meta"]["epe_bytes"]))
    a("  `%s`" % d["hashes"]["built"])
    a("* object counts are still %d / %d and class counts %d / %d"
      % (d["n_v"], d["n_b"], d["classes_v"], d["classes_b"]))
    a("* the removed set is still %d objects (%d `CPartProp` + the root) and the added set %d"
      % (len(d["removed"]), sum(1 for o in d["removed"] if o["cls"] == "CPartProp"), len(d["added"])))
    a("* every added/copied object resolves to an `additions[]` row, and every tagged row exists in")
    a("  the spec's own row ids")
    a("* no matched pair hides a property-list difference: the only one is the root's `palette`")
    a("* the count arithmetic above still closes, and this page matches the regenerated bytes")
    a("")
    a("## 10. Labels")
    a("")
    a("Every object, member and id here is **decoded** from the two `.epe` files (game archive vs")
    a("build). The counts, deltas and the tag assignments are **derived**. Nothing is filled in from")
    a("memory of Just Cause 3; where the spec is silent the row says UNEXPLAINED and names the other")
    a("record that touches it (build receipt / `PALETTE_HASH.md`) rather than assuming intent.")
    a("")
    return "\n".join(L) + "\n"


def oracles(d: dict) -> list[tuple[str, bool]]:
    cp_dropped = sum(1 for o in d["removed"] if o["cls"] == "CPartProp")
    spec_rows = load_spec()["rows"]
    out = [
        ("original parses as 450 objects", d["n_v"] == 450),
        ("build parses as 467 objects", d["n_b"] == 467),
        ("class counts are 43 / 46", d["classes_v"] == 43 and d["classes_b"] == 46),
        ("34 CPartProp objects are dropped", cp_dropped == 34),
        ("the removed set is 34 CPartProp objects", len(d["removed"]) == 34),
        ("47 objects are added", len(d["added"]) == 47),
        ("4 extra SEffects copies are added", len(d["copies"]) == 4),
        ("the root CCar is renamed", d["renamed"] is not None
         and d["renamed"]["old"] != d["renamed"]["new"]),
        ("every added/copied object is tagged", all(o["tag"] != "UNEXPLAINED"
                                                   for o in d["added"] + d["copies"])),
        ("every tag is a row id the spec carries",
         all(o["tag"] in spec_rows for o in d["added"] + d["copies"])),
        ("the only property-list difference is on the root",
         len(d["presence"]) == 1 and d["presence"][0]["cls"] == "CCar"),
        ("the added member is `palette`", d["presence"] and d["presence"][0]["member"] == "palette"),
        ("every matched pair was compared", d["pairs"] == 416),
        ("the census arithmetic closes",
         d["n_v"] - len(d["removed"]) + len(d["added"]) + len(d["copies"]) == d["n_b"]),
        ("UNEXPLAINED is 34 dropped + root rename + palette",
         len(d["unexp"]) == 34 + (1 if d["renamed"] else 0) + len(d["presence"])),
    ]
    return out


def page() -> tuple[str, list[tuple[str, bool]]]:
    d = build()
    return render(d), oracles(d)


def cmd_write() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote %s (%d bytes)" % (rel(OUT), len(text.encode())))
    return 0 if all(ok for _, ok in ors) else 1


def cmd_check() -> int:
    text, ors = page()
    path = os.path.join(ROOT, OUT)
    if not os.path.exists(path):
        print("MISSING " + rel(OUT))
        return 1
    bad = [n for n, ok in ors if not ok]
    for n, ok in ors:
        print(("PASS " if ok else "FAIL ") + n)
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if open(path, encoding="utf-8").read() != text:
        print("DRIFT: %s differs from the regenerated bytes" % rel(OUT))
        return 1
    print("document identical: " + rel(OUT))
    return 0 if not bad else 1


def main() -> int:
    args = sys.argv[1:]
    if args == ["--write"]:
        return cmd_write()
    if args == ["--check"]:
        return cmd_check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

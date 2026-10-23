"""grab_slots.py - mesh LOD -> material slot -> texture table (GRB-10).

Three independent reads of the same mesh are joined, so slot order is never assumed:

  * `umodel`'s props dump of the exported SkeletalMesh (`Materials[19]` in order, plus each LOD's
    `LODMaterialMap`),
  * the mesh's own ActorX export (`MATERIALS` chunk order and a material index per face), which also
    gives the faces drawn per slot, and
  * `Working/Assembled/assembly.json`, which records the block each slot was assembled with.

Textures come from `Research/BatmobileGrab/MATERIALS.md` (instance rows); a slot that is a master
material rather than an instance is reported as such instead of being given invented textures.

Writes:
    Research/BatmobileGrab/SLOTS.json
    Research/BatmobileGrab/SLOTS.md

Usage:
    python Tools/scripts/grab_slots.py --write
    python Tools/scripts/grab_slots.py --check
    python Tools/scripts/grab_slots.py --mesh Batmobile_V2 --lod0 <path.pskx>
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import psk2rbm as P      # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
GRAB = os.path.join(ROOT, "Working", "Appearance", "grab", "Playable_Batmobile_SF", "SkeletalMesh3")
ASSEMBLY = os.path.join(ROOT, "Working", "Assembled", "assembly.json")
MATERIALS = os.path.join(OUT, "MATERIALS.md")


def _cells(line):
    """Split a markdown table row on unescaped pipes."""
    out, cur, i = [], "", 0
    while i < len(line):
        c = line[i]
        if c == "\\" and i + 1 < len(line) and line[i + 1] == "|":
            cur += "|"
            i += 2
            continue
        if c == "|":
            out.append(cur.strip())
            cur = ""
        else:
            cur += c
        i += 1
    out.append(cur.strip())
    return out


def material_instances(path=MATERIALS):
    """instance name -> {package, parent, textures} from MATERIALS.md's instance table."""
    if not os.path.exists(path):
        return {}
    rows, in_table = {}, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## Material instances"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        c = _cells(line)
        if len(c) < 7 or c[1] in ("instance", "---"):
            continue
        tex = {}
        for part in c[6].split(", "):
            if "→" not in part:
                continue
            k, v = part.split("→", 1)
            tex[k.strip()] = v.strip().strip("`")
        rows[c[2]] = {"package": c[1], "parent": c[3].strip("`"), "textures": tex}
    return rows


def material_masters(path=MATERIALS):
    """master name -> {package, textures} from MATERIALS.md's master table (channel -> texture refs)."""
    if not os.path.exists(path):
        return {}
    rows, in_table = {}, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## Master materials"):
            in_table = True
            continue
        if in_table and line.startswith("## "):
            break
        if not in_table or not line.startswith("|"):
            continue
        c = _cells(line)
        if len(c) < 4 or c[1] in ("material", "---"):
            continue
        tex = {}
        for channel, refs in re.findall(r"(\w+)→`[^`]+`\s*(?:\[([^\]]*)\])?", c[3]):
            got = [x.strip().strip("`") for x in refs.split(",") if x.strip() and x.strip() != "—"]
            if got:
                tex[channel] = ", ".join(got)
        rows[c[2]] = {"package": c[1], "textures": tex}
    return rows


def props(path):
    """Materials order and per-LOD material maps from umodel's props dump."""
    text = open(path, encoding="utf-8", errors="replace").read()
    mats = []
    for m in re.finditer(r"Materials\[(\d+)\] = \w+'([^']+)'", text):
        mats.append((int(m.group(1)), m.group(2).split(".")[-1], m.group(2)))
    mats.sort()
    lods = []
    for lm in re.finditer(r"LODInfo\[(\d+)\] =\s*\{(.*?)\n    \}", text, re.S):
        idx, body = int(lm.group(1)), lm.group(2)
        mp = [(int(a), int(b)) for a, b in re.findall(r"LODMaterialMap\[(\d+)\] = (\d+)", body)]
        lods.append({"lod": idx, "material_map": [b for a, b in sorted(mp)],
                     "map_len": len(mp)})
    return mats, lods


def plan_slots(path=ASSEMBLY):
    """mat_index -> material name for every part in the assembly plan (they must agree)."""
    try:
        a = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {}, {}
    by_index, by_material = {}, {}
    for part, slots in (a.get("plan") or {}).items():
        for s in slots:
            by_index.setdefault(s["mat_index"], set()).add(s["material"])
            by_material.setdefault(s["material"], set()).add(part)
    return by_index, by_material


def build(mesh="Batmobile_V2", lod0=None, props_path=None):
    lod0 = lod0 or os.path.join(GRAB, mesh + ".pskx")
    props_path = props_path or os.path.join(GRAB, mesh + ".props.txt")
    mats, lods = props(props_path)
    instances = material_instances()
    masters = material_masters()
    by_index, by_material = plan_slots()
    _, _, faces, chunk_mats = P.read_pskx(lod0)
    counts = collections.Counter(int(m) for m in faces["m"]) if len(faces) else collections.Counter()
    problems = []
    if [n for _, n, _ in mats] != list(chunk_mats):
        problems.append("props Materials order != pskx MATERIALS chunk order")
    if len(mats) != len(chunk_mats):
        problems.append("props has %d slots, pskx has %d" % (len(mats), len(chunk_mats)))
    slots = []
    for i, name, path in mats:
        chunk = chunk_mats[i] if i < len(chunk_mats) else None
        if chunk and chunk != name:
            problems.append("slot %d: props says %s, pskx says %s" % (i, name, chunk))
        inst = instances.get(name)
        master = masters.get(name)
        row = inst or master or {}
        planned = by_index.get(i, set())
        if planned and name not in planned:
            problems.append("slot %d: assembly used %s for that index, mesh says %s"
                            % (i, ", ".join(sorted(planned)), name))
        if not planned:
            problems.append("slot %d (%s): not present in assembly.json" % (i, name))
        if not row:
            problems.append("slot %d (%s): no row in MATERIALS.md" % (i, name))
        slots.append({
            "index": i, "material": name, "object_path": path,
            "kind": "MaterialInstanceConstant" if inst else ("Material/master" if master else "unknown"),
            "package": row.get("package"),
            "parent": row.get("parent"),
            "textures": row.get("textures") or {},
            "lod0_faces": counts.get(i, 0),
            "assembly_parts": sorted(by_material.get(name, set())),
            "assembly_block": None,
        })
    # assembly block per slot (body plan is authoritative for the shared slots)
    try:
        plan = json.load(open(ASSEMBLY, encoding="utf-8"))["plan"]
        for s in slots:
            for part, rows in plan.items():
                hit = next((r for r in rows if r["mat_index"] == s["index"]
                            and r["material"] == s["material"]), None)
                if hit:
                    s["assembly_block"] = hit["block"]
                    break
    except (OSError, ValueError, KeyError):
        pass
    for l in lods:
        l["identity"] = all(v == i for i, v in enumerate(l["material_map"]))
        l["covers_slots"] = len(l["material_map"] or slots)
    drawn = sum(1 for s in slots if s["lod0_faces"])
    summary = {
        "mesh": mesh, "slots": len(slots), "lod0_faces": sum(s["lod0_faces"] for s in slots),
        "slots_with_geometry": drawn, "slots_without_geometry": len(slots) - drawn,
        "instances": sum(1 for s in slots if s["kind"] == "MaterialInstanceConstant"),
        "textures": len({t for s in slots for t in s["textures"].values()}),
        "lods": len(lods),
        "lod_maps_identity": sum(1 for l in lods if l["identity"]),
    }
    return {"schema": 1, "generated_by": "grab_slots.py", "mesh": mesh,
            "sources": {"props": os.path.relpath(props_path, ROOT),
                        "pskx": os.path.relpath(lod0, ROOT),
                        "materials": os.path.relpath(MATERIALS, ROOT),
                        "assembly": os.path.relpath(ASSEMBLY, ROOT)},
            "slots": slots, "lods": lods, "summary": summary, "problems": problems}


def write_md(doc):
    s = doc["summary"]
    L = ["# Batmobile_V2 - LOD -> material slot -> texture (GRB-10)", "",
         "Generated by `Tools/scripts/grab_slots.py`. The slot order is read three ways and must agree: "
         "umodel's `Materials[19]` dump, the mesh's own `MATERIALS` chunk, and `assembly.json`. Textures "
         "are the instance's bindings from `MATERIALS.md`; a master slot has none to report.", "",
         "## Summary", "", "| fact | value |", "|---|---|"]
    for k, v in s.items():
        L.append("| %s | **%s** |" % (k, v))
    L += ["", "Problems: " + ("none" if not doc["problems"] else "")]
    L += ["- " + p for p in doc["problems"]]
    L += ["", "## Slots (LOD0)", "",
          "| # | material | kind | parent | LOD0 faces | textures | block | parts |",
          "|---|---|---|---|---|---|---|---|"]
    for x in doc["slots"]:
        tex = ", ".join("%s=%s" % (k, v) for k, v in sorted(x["textures"].items())) or "—"
        L.append("| %d | `%s` | %s | %s | %s | %s | %s | %s |" % (
            x["index"], x["material"], x["kind"], ("`%s`" % x["parent"]) if x["parent"] else "—",
            x["lod0_faces"], tex, x["assembly_block"] or "—",
            ", ".join(x["assembly_parts"]) or "—"))
    L += ["", "## LOD material maps", "",
          "| LOD | entries | identity |", "|---|---|---|"]
    for l in doc["lods"]:
        L.append("| %d | %d | %s |" % (l["lod"], l["map_len"], "yes" if l["identity"] else "no"))
    L += ["", "LOD1/LOD2 section counts are not measured: umodel's ActorX export writes LOD0 only, so "
          "the face counts above are LOD0's. The LOD maps come from the mesh's own `LODInfo`."]
    open(os.path.join(OUT, "SLOTS.md"), "w", encoding="utf-8").write("\n".join(L))
    return os.path.join(OUT, "SLOTS.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--mesh", default="Batmobile_V2")
    ap.add_argument("--lod0")
    a = ap.parse_args()
    doc = build(a.mesh, a.lod0)
    if a.write:
        os.makedirs(OUT, exist_ok=True)
        json.dump(doc, open(os.path.join(OUT, "SLOTS.json"), "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(os.path.join(OUT, "SLOTS.json"), ROOT), "and",
              os.path.relpath(write_md(doc), ROOT))
    print(json.dumps(doc["summary"], indent=1))
    if a.check:
        fail = []
        s = doc["summary"]
        if s["slots"] != 19:
            fail.append("expected 19 material slots, got %d" % s["slots"])
        if s["lod0_faces"] != 299837:
            fail.append("expected 299837 LOD0 faces, got %d" % s["lod0_faces"])
        if s["lods"] != 3:
            fail.append("expected 3 LODs, got %d" % s["lods"])
        if s["lod_maps_identity"] != 3:
            fail.append("expected identity LOD material maps, got %d" % s["lod_maps_identity"])
        if any(x["assembly_block"] is None for x in doc["slots"]):
            fail.append("a slot has no assembly block")
        if any(x["kind"] == "unknown" for x in doc["slots"]):
            fail.append("a slot resolves to neither a master nor an instance row in MATERIALS.md")
        if fail:
            print("FAIL")
            for f in fail:
                print("  -", f)
            return 1
        print("OK: %d slots, %d faces, %d instances, %d LODs"
              % (s["slots"], s["lod0_faces"], s["instances"], s["lods"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

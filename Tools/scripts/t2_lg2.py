"""t2_lg2.py - is the build's light rig the donor's, row for row? (T-LG2)

T-2 carried an open question: the donor entity's graph holds **22**
`SVehicleLight` objects while the build's lights module holds **21** rows, and
which side was short one was not established.  This re-reads both sides out of
the installed build and out of the vanilla archive:

  * the module: `..._lights.vmodc` sliced through the build's `.toc`, decoded
    with Gibbed, one row per `lights[i]`;
  * the graph: the `.epe` inside the same `.ee`, converted with the same
    `ConvertProperty` `jc3detail.py` uses, counting `SVehicleLight` objects.

Then it does the same for the vanilla donor entity and compares the two preset-id
sets.  The answer, printed rather than assumed: the build carries **exactly the
donor's 21 rows** and **the donor's 22 objects**; the counts differ inside the
vanilla entity itself, because the module addresses presets by hash - 20 resolve
to objects the graph instantiates, 1 is a preset the graph does not instantiate,
and 2 graph objects are not referenced by any row.  No row was dropped by the
build.

Usage:
  python t2_lg2.py [--ee <installed .ee>] [--game <JC3 dir>] [--json out.json]
Exit code is 0 only when the build's rig equals the donor's on both sides.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3detail  # noqa: E402
import jc3index  # noqa: E402
from eetoc import read_toc, sarc_dir, unaaf  # noqa: E402
from t5_apply import decode, paths  # noqa: E402
from t5_measure import DROP  # noqa: E402

DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_civilian_01.ee")
LIGHTS = "_lights.vmodc"


def members(ee_path: str) -> tuple[dict[str, tuple[int, int]], bytes]:
    """name -> (offset, size) through the .toc, and the whole decompressed SARC."""
    sarc = unaaf(open(ee_path, "rb").read())
    toc_path = ee_path + ".toc"
    if os.path.exists(toc_path):
        toc = {n: (o, s) for n, o, s in read_toc(open(toc_path, "rb").read())}
    else:
        toc = {n: (o, s) for n, o, s in sarc_dir(sarc)}
    return toc, sarc


def lights_of(ee_path: str, work: str) -> dict:
    toc, sarc = members(ee_path)
    name = next((n for n in toc if n.lower().endswith(LIGHTS)), None)
    if name is None:
        raise SystemExit(f"no {LIGHTS} in {ee_path}")
    off, size = toc[name]
    vm = os.path.join(work, "lights.vmodc")
    with open(vm, "wb") as f:
        f.write(sarc[off:off + size])
    root = ET.fromstring(decode(vm, os.path.join(work, "lights.xml")))
    table = paths(root.find("instances/instance"))
    idx = sorted({int(m.group(1)) for k in table
                  if (m := re.match(r"lights\[(\d+)\]", k))})
    rows = []
    for i in idx:
        rows.append({k.split(".", 1)[1]: v.text for k, v in table.items()
                     if k.startswith(f"lights[{i}].")})
    epe_name = next((n for n in toc if n.lower().endswith(".epe")), None)
    if epe_name is None:
        raise SystemExit(f"no .epe in {ee_path}")
    eoff, esize = toc[epe_name]
    graph = jc3detail.decode_epe(sarc[eoff:eoff + esize], work, "lg2")
    if graph is None:
        raise SystemExit("ConvertProperty refused the .epe")
    objects = [o for o in graph["objects"] if o["class"] == "SVehicleLight"]
    hashes = {int(o["values"]["name_hash"]) & 0xFFFFFFFF: o["name"] for o in objects}
    return {"rows": rows,
            "presets": [int(r.get("preset_id") or 0) for r in rows],
            "objects": hashes, "epe": epe_name}


def summary(rig: dict) -> dict:
    matched = [p for p in rig["presets"] if p in rig["objects"]]
    return {"rows": len(rig["rows"]),
            "objects": len(rig["objects"]),
            "matched": len(matched),
            "row_presets_not_in_graph": sorted(set(rig["presets"]) - set(rig["objects"])),
            "graph_objects_unused": sorted(n for h, n in rig["objects"].items()
                                           if h not in rig["presets"]),
            "behaviors": sorted({r.get("behavior") for r in rig["rows"]})}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ee", default=DROP)
    ap.add_argument("--game", default=jc3index.DEFAULT_GAME)
    ap.add_argument("--json")
    a = ap.parse_args()

    if not os.path.exists(a.ee):
        raise SystemExit(f"no installed build at {a.ee} - install it or pass --ee")

    rows = jc3index.load_index(jc3index.DEFAULT_OUT)
    donor = jc3detail.pick(rows, DONOR)
    arc = os.path.join(a.game, donor["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(donor["offset"])
        vblob = f.read(donor["size"])

    with tempfile.TemporaryDirectory() as td:
        build = lights_of(a.ee, td)
        van_path = os.path.join(td, "vanilla.ee")
        with open(van_path, "wb") as f:
            f.write(vblob)
        vanilla = lights_of(van_path, td)

    bs, vs = summary(build), summary(vanilla)
    problems = []
    if build["presets"] != vanilla["presets"]:
        problems.append("the build's light rows differ from the donor's preset ids")
    if sorted(build["objects"]) != sorted(vanilla["objects"]):
        problems.append("the build's SVehicleLight objects differ from the donor's")
    print(f"build   rows {bs['rows']} objects {bs['objects']} matched {bs['matched']} "
          f"unused-objects {len(bs['graph_objects_unused'])} "
          f"presets-not-in-graph {len(bs['row_presets_not_in_graph'])}")
    print(f"vanilla rows {vs['rows']} objects {vs['objects']} matched {vs['matched']} "
          f"unused-objects {len(vs['graph_objects_unused'])} "
          f"presets-not-in-graph {len(vs['row_presets_not_in_graph'])}")
    print("  row presets the graph does not instantiate:",
          [hex(p) for p in bs["row_presets_not_in_graph"]])
    print("  graph objects no row references:", bs["graph_objects_unused"])
    if a.json:
        with open(a.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"build": bs, "vanilla": vs, "problems": problems}, f, indent=1)
    if problems:
        print("FAIL")
        for p in problems:
            print(" ", p)
        sys.exit(1)
    print("check ok: the build's rig is the donor's, row for row")


if __name__ == "__main__":
    main()

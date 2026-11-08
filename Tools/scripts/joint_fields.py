#!/usr/bin/env python3
"""What a correct turret/cannon joint looks like, and what the B-04 manifest lacks.

The donor parts modules carry one joint member: `parts[i].constraint_index`, a signed int32
that indexes the ordered constraint-object list of the vehicle's `.physicsc`. The constraint
is a 304-byte `hkpLimitedHingeConstraintData` whose axis is at +0x30, pivot at +0x60 and
min/max angles at +0xFC/+0x100 in **radians**. This script decodes the medium tank (v0201)
and the APC (v0200) as the two worked examples, then states the field-by-field values BmAK
would need for P-01 (yaw 120 deg) and P-02 (pitch 25 deg).

Describe only: no manifest or generator is written.

Usage:
  python Tools/scripts/joint_fields.py --write   # Working/Parts/JOINT_FIELDS.md
  python Tools/scripts/joint_fields.py --check
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
import jc3hkx  # noqa: E402

RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
TANK = os.path.join(RAW, "tmp", "mediumtank_vehicle_parts.vmodc")
APC = os.path.join(RAW, "tmp", "apc_vehicle_parts.vmodc")
TURRET = os.path.join(ROOT, "Research", "JC3Grab", "TURRET.json")
T8 = os.path.join(ROOT, "Working", "Translation", "T8_PARTS.json")
MANIFEST = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
GEN = os.path.join(ROOT, "Tools", "scripts", "bm_parts.py")
PHYS = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                    "v0300_car_kensington_sportsmuscle", "batmobile", "sportsmuscle.physicsc")
OUT = os.path.join(ROOT, "Working", "Parts", "JOINT_FIELDS.md")
DEG = 180.0 / math.pi

CASES = (("mediumtank", TANK, (26, 38)), ("apc", APC, (30, 44)))


def f(x, n=6):
    return f"{x:.{n}f}"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def parts_of(path):
    return {p["part_index"]: p for p in jc3adf.parts(jc3adf.Adf(open(path, "rb").read()))}


def turret_samples():
    d = json.load(open(TURRET, encoding="utf-8"))
    return {s["label"] if "label" in s else s["entity"]: s for s in d["samples"]}


def constraint_objects():
    """Count the built physicsc's constraint objects in file order (jc3turret's ordering)."""
    pf = jc3hkx.Packfile(open(PHYS, "rb").read())
    objs = sorted((o for o in pf.objects if "Constraint" in o.cls), key=lambda o: o.offset)
    return [{"i": i, "class": o.cls, "size": pf.extents[o.offset]} for i, o in enumerate(objs)]


def build_payload():
    samples = turret_samples()
    t8 = {r["id"]: r for r in json.load(open(T8, encoding="utf-8"))["rows"]}
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    mparts = {p["name"]: p for p in manifest["parts"]}
    gen_text = open(GEN, encoding="utf-8").read().splitlines()
    gen_line = next((n for n, s in enumerate(gen_text, 1) if '"constraint_index"' in s), None)

    rows = {}
    for tag, path, ids in CASES:
        P = parts_of(path)
        label = next(k for k in samples if samples[k]["tag"] == tag)
        cons = {c["i"]: c for c in samples[label]["constraints"]}
        rows[tag] = []
        for i in ids:
            p = P[i]
            c = cons.get(p["constraint_index"])
            if c is None:
                raise SystemExit(f"{tag} part {i}: constraint {p['constraint_index']} missing")
            rows[tag].append({
                "part_index": i, "name": p["name"], "behaviour": p["behavior"],
                "parent": p["parent_part_index"], "constraint_index": p["constraint_index"],
                "pso": [p["parent_space_offset"][12 + k] for k in range(3)],
                "kids": p["children_part_indices"],
                "constraint": c,
            })

    # BmAK targets. P-01's joint is measured from the animation; P-02 has no animated rotation
    # (row `joint: null`), so its angular envelope is the carrier hinge it names.
    p1 = t8["P-01"]
    p2 = t8["P-02"]
    targets = {
        "P-01": {"part": mparts[p1["part"]], "axis": p1["joint"]["axis_jc3"],
                 "min_deg": p1["joint"]["min_deg"], "max_deg": p1["joint"]["max_deg"],
                 "pivot": mparts[p1["part"]]["pivot_m"], "source": "P-01 joint (animation)"},
        "P-02": {"part": mparts[p2["part"]], "axis": p2["hinge"]["axis"],
                 "min_deg": p2["hinge"]["min_deg"], "max_deg": p2["hinge"]["max_deg"],
                 "pivot": mparts[p2["part"]]["pivot_m"],
                 "source": "P-02 `hinge` (carrier hinge; row joint is null)"},
    }
    for t in targets.values():
        t["min_rad"] = math.radians(t["min_deg"])
        t["max_rad"] = math.radians(t["max_deg"])
        t["span_deg"] = t["max_deg"] - t["min_deg"]
        t["parent"] = t["part"]["parent"]
        t["part_index"] = t["part"]["part_index"]

    cons = constraint_objects()
    limited = sum(1 for c in cons if c["class"] == "hkpLimitedHingeConstraintData")
    return {
        "schema": 1,
        "sha": {"tank": sha(TANK), "apc": sha(APC), "turret": sha(TURRET), "t8": sha(T8),
                "manifest": sha(MANIFEST)},
        "rows": rows,
        "targets": targets,
        "manifest_keys": sorted(mparts["batmobile_turret"].keys()),
        "has_joint_key": any("joint" in k.lower() or "constraint" in k.lower()
                             for k in mparts["batmobile_turret"]),
        "gen_line": gen_line,
        "built_constraints": {"count": len(cons), "limited": limited,
                              "next_index": len(cons)},
        "lang": {"deg": DEG},
    }


def to_md(p):
    L = []
    a = L.append
    a("# JOINT_FIELDS - what a JC3 turret/cannon hinge needs, and what P-01/P-02 would say")
    a("")
    a("Generated by `python Tools/scripts/joint_fields.py --write`; `--check` re-decodes the")
    a("donor parts modules and `TURRET.json` and compares this page byte for byte. **Describe")
    a("only:** the B-04 manifest and `bm_parts.py` are read, never written.")
    a("")
    a("**Answer.** A moving part has exactly **one** joint member in the parts module:")
    a("`parts[i].constraint_index`, an int32. It is an index into the ordered list of")
    a("constraint objects in the vehicle's `.physicsc`. The object is a 304-byte")
    a("`hkpLimitedHingeConstraintData`; `+0x30` is its axis, `+0x60` its pivot, and `+0xFC` /")
    a("`+0x100` its minimum / maximum angle **in radians**. There is no joint object in the")
    a("parts module and no axis/limit member in `hinged_parts[]` - that array stores only a")
    a("part index (`MOVING_PARTS.md` §3).")
    a("")
    a("`bm_vehicle_parts.json` has **no** joint member (its P-01/P-02 records list")
    a(f"{len(p['manifest_keys'])} keys, none joint/constraint), and `bm_parts.py` writes")
    a("`constraint_index = -1` for every new part, so the built turret and cannon have no")
    a("hinge to point at. The fields below are what would close that gap.")
    a("")
    a("## 1. The member in the donor rows")
    a("")
    a("| vehicle | part | i | behaviour | parent | `constraint_index` | constraint |")
    a("|---|---|---|---|---|---|---|")
    for tag, rows in p["rows"].items():
        for r in rows:
            c = r["constraint"]
            a(f"| {tag} | `{r['name']}` | {r['part_index']} | `{r['behaviour']}` | "
              f"{r['parent']} | **{r['constraint_index']}** | `{c['class']}` ({c['size']} B), "
              f"list index {c['i']} |")
    a("")
    a("The two donor rows in full (axis / pivot / limits from the constraint object):")
    a("")
    a("| part | axis (x, y, z) | pivot (m) | min | max | span | parent_space_offset |")
    a("|---|---|---|---|---|---|---|")
    for tag, rows in p["rows"].items():
        for r in rows:
            c = r["constraint"]
            a(f"| `{r['name']}` | ({c['axis'][0]:.1f}, {c['axis'][1]:.1f}, {c['axis'][2]:.1f}) | "
              f"({c['pivot'][0]:.4f}, {c['pivot'][1]:.4f}, {c['pivot'][2]:.4f}) | "
              f"{c['min_deg']:.3f}° = {c['min_rad']:.6f} rad | "
              f"{c['max_deg']:.3f}° = {c['max_rad']:.6f} rad | "
              f"{c['max_deg'] - c['min_deg']:.3f}° | "
              f"({r['pso'][0]:.4f}, {r['pso'][1]:.4f}, {r['pso'][2]:.4f}) |")
    a("")
    a("Every constrained donor part here has an identity `parent_space_offset`; its position is")
    a("carried by the constraint's own pivot, not by the part transform.")
    a("")
    a("## 2. How the index resolves")
    a("")
    a("`constraint_index` is not a Havok body id and not a `raycast_body_id`; it is the position")
    a("of the constraint object in the `.physicsc` file's constraint-object list, ordered by")
    a("object offset (the ordering `jc3turret.py` uses). The medium tank has three limited")
    a("hinges, so 0 = cannon, 1 = hatch, 2 = turret; the APC has 16, so 14 = weapon mount,")
    a("15 = turret base. A wrong index silently binds the part to another panel's hinge - the")
    a("index must be assigned after the objects are ordered, not guessed from part indices.")
    a("")
    a("The limited-hinge object is decoded from these fields:")
    a("")
    a("| offset | type | meaning | units |")
    a("|---|---|---|---|")
    a("| `+0x30` | `float4` | hinge axis (x, y, z; w unused for the axis reading) | unit vector |")
    a("| `+0x60` | `float4` | hinge pivot (x, y, z) | metres, vehicle frame as stored |")
    a("| `+0xFC` | `float32` | minimum angle | **radians** |")
    a("| `+0x100` | `float32` | maximum angle | **radians** |")
    a("")
    a("`min_deg = min_rad × 180/π` and `max_deg = max_rad × 180/π` is the only unit bridge")
    a("(57.29577951308232). The values are float32; the page prints six decimals.")
    a("")
    a("## 3. What BmAK asks for - P-01 and P-02")
    a("")
    a("| field | P-01 (`batmobile_turret`, part 50) | P-02 (`batmobile_cannon`, part 51) |")
    a("|---|---|---|")
    for k, label in (("part_index", "part_index"), ("parent", "parent"),
                     ("behaviour", "behaviour"), ("constraint_index", "`constraint_index`")):
        if k == "behaviour":
            a(f"| {label} | `Turret` | `Cannon` |")
        elif k == "constraint_index":
            a(f"| {label} | **{p['built_constraints']['next_index']}** (append order; see §4) | "
              f"**{p['built_constraints']['next_index'] + 1}** |")
        else:
            a(f"| {label} | {p['targets']['P-01'][k]} | {p['targets']['P-02'][k]} |")
    for k, label, fmt in (("axis", "axis (unit)", lambda v: "(" + ", ".join(f(x, 1) for x in v) + ")"),
                          ("pivot", "pivot (m, vehicle frame)",
                           lambda v: "(" + ", ".join(f(x, 6) for x in v) + ")"),
                          ("min_deg", "min (deg)", lambda v: f"{v:.1f}"),
                          ("max_deg", "max (deg)", lambda v: f"{v:.1f}"),
                          ("span_deg", "span (deg)", lambda v: f"{v:.1f}"),
                          ("min_rad", "min (rad)", lambda v: f"{v:.6f}"),
                          ("max_rad", "max (rad)", lambda v: f"{v:.6f}")):
        a(f"| {label} | {fmt(p['targets']['P-01'][k])} | {fmt(p['targets']['P-02'][k])} |")
    a("")
    a("Sources: P-01's 120° comes from the measured `Batmobile_V2_Turret_Spin` joint")
    a("(`min -60`, `max +60`, axis `+Y`); P-02's 25° is the carrier hinge span `-5 .. +20`,")
    a("axis `+X` (P-02's own row has `joint: null` because the cannon bones translate; its")
    a("`hinge` block is the medium-tank cannon hinge, and the verify line is \"the barrel stops")
    a("at the carrier's own -5..20 deg\").")
    a("")
    a("**Frame of the pivot.** The donor's hinge pivot and B-04's `pivot_m` are both in vehicle space:")
    a("P-02's `pivot_m` is exactly P-01's `pivot_m` plus P-02's `parent_space_offset`")
    a("(0.876249 + 0.826197 = 1.702446), and `parent_frame_origin_m` of P-02 is P-01's pivot.")
    a("So `constraint_pivot_m` takes the part's **`pivot_m`**; the existing")
    a("`parent_space_offset` stays the parent-relative placement. Do not copy the pso into the")
    a("constraint: doing so would put the trunnion at 0.826 m above the hull floor instead of")
    a("1.702 m, or double-place it if the part pivot were rewritten too.")
    a("")
    a("The quote comes from the built page `Builds/bm-RC2/verify/joint_trace.md` and")
    a("`Builds/bm-RC2/verify/turret_ranges.md` (“stops at the carrier's own -5..20 deg”).")
    a("")
    a("## 4. Field-by-field manifest requirement")
    a("")
    a("Minimum: add a signed integer **`constraint_index`** to each P-01/P-02 record (and to")
    a("every future `Turret`/`Cannon` part). `-1` remains the no-joint value used for static")
    a("parts. Because the built physicsc currently has no Batmobile hinge, the generator also")
    a("needs enough data to create the two objects and then assign their ordered indices:")
    a("")
    a("| proposed manifest field | type | P-01 value | P-02 value | why |")
    a("|---|---|---|---|---|")
    a(f"| `constraint_index` | int | {p['built_constraints']['next_index']} | "
      f"{p['built_constraints']['next_index'] + 1} | index into the ordered constraint list |")
    a("| `constraint_class` | string | `hkpLimitedHingeConstraintData` | same | the only class the fleet uses for turret/cannon |")
    a(f"| `constraint_axis` | float[3] | {p['targets']['P-01']['axis']} | "
      f"{p['targets']['P-02']['axis']} | unit axis, +Y yaw / +X pitch |")
    a(f"| `constraint_pivot_m` | float[3] | {p['targets']['P-01']['pivot']} | "
      f"{p['targets']['P-02']['pivot']} | hinge pivot; state the frame |")
    a(f"| `constraint_min_rad` | float | {p['targets']['P-01']['min_rad']:.6f} | "
      f"{p['targets']['P-02']['min_rad']:.6f} | the stored unit |")
    a(f"| `constraint_max_rad` | float | {p['targets']['P-01']['max_rad']:.6f} | "
      f"{p['targets']['P-02']['max_rad']:.6f} | the stored unit |")
    a(f"| `constraint_min_deg` | float | {p['targets']['P-01']['min_deg']:.1f} | "
      f"{p['targets']['P-02']['min_deg']:.1f} | human/round-trip check only |")
    a(f"| `constraint_max_deg` | float | {p['targets']['P-01']['max_deg']:.1f} | "
      f"{p['targets']['P-02']['max_deg']:.1f} | human/round-trip check only |")
    a("| `constraint_frame` | string | `vehicle` | `vehicle` | the donor's stored frame; not proven as body-local |")
    a("| `constraint_source` | string | P-01 joint | P-02 carrier hinge | provenance for the numbers |")
    a("")
    a(f"The built physicsc currently has **{p['built_constraints']['count']}** constraint")
    a(f"objects ({p['built_constraints']['limited']} limited hinges); appending the two new")
    a(f"objects gives the indices **{p['built_constraints']['next_index']}** and")
    a(f"**{p['built_constraints']['next_index'] + 1}** used above. If the generator reorders or")
    a("replaces donor objects, the indices must be recomputed from the final object order, not")
    a("hardcoded.")
    a("")
    a("What must **not** be used: `hinged_parts[]` (only a part index, no axis or limit) and")
    a("`aim_part_constraints[]` (suspension/steering, zero rows on every turreted sample).")
    a("`raycast_body_id` is also unrelated to a joint.")
    a("")
    a("## 5. Current loss, for context")
    a("")
    a(f"The manifest's P-01/P-02 records have keys `{', '.join(p['manifest_keys'])}` and no")
    a("joint key. `Tools/scripts/bm_parts.py` writes the `constraint_index` flag tuple with a")
    a(f"literal `-1` at line {p['gen_line']} and never opens the physicsc, so the current build")
    a("ships `constraint_index = -1` on parts 50/51. This page does not change either file.")
    a("")
    a("## 6. UNKNOWNs")
    a("")
    a("- **The frame of the constraint pivot/axis.** The donor tank stores values that agree with")
    a("  vehicle space, but the hinge transform's body-A-local vs vehicle-space layout is not")
    a("  proven in `TURRET.md` §6; on wheeled mounts the pitch pivot sits above an adapter part.")
    a("  A port must copy the donor's convention and verify it (Q-1), not assume.")
    a("- **Turn rate / acceleration.** A limited hinge carries an axis and two angles only; the")
    a("  speed is code-side. `max_rate_deg_s` in the animation row is an animation figure, not a")
    a("  hinge field.")
    a("- **Whether a `Turret`/`Cannon` part with `constraint_index = -1` gets a runtime joint")
    a("  anyway.** No decoded engine code in the repo answers this; the donor rows all point at a")
    a("  real constrained object.")
    a("")
    a("## 7. Inputs")
    a("")
    a("| file | sha256 |")
    a("|---|---|")
    for k, label in (("tank", "mediumtank parts module"), ("apc", "apc parts module"),
                     ("turret", "TURRET.json"), ("t8", "T8_PARTS.json"),
                     ("manifest", "bm_vehicle_parts.json")):
        a(f"| {label} | `{p['sha'][k]}` |")
    a("")
    a("```")
    a("python Tools/scripts/joint_fields.py --write")
    a("python Tools/scripts/joint_fields.py --check")
    a("```")
    return "\n".join(L) + "\n"


def main():
    p = build_payload()
    if "--write" in sys.argv[1:]:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="\n").write(to_md(p))
        print("wrote", os.path.relpath(OUT, ROOT).replace("\\", "/"))
        return 0
    if "--check" in sys.argv[1:]:
        problems = []
        if not os.path.exists(OUT):
            problems.append("JOINT_FIELDS.md missing")
        elif open(OUT, encoding="utf-8").read() != to_md(p):
            problems.append("JOINT_FIELDS.md stale")
        want = {("mediumtank", 26): 2, ("mediumtank", 38): 0,
                ("apc", 30): 15, ("apc", 44): 14}
        for tag, rows in p["rows"].items():
            for r in rows:
                if r["constraint_index"] != want[(tag, r["part_index"])]:
                    problems.append(f"{tag} part {r['part_index']} constraint_index")
        if p["has_joint_key"]:
            problems.append("manifest unexpectedly has a joint key")
        if p["gen_line"] is None:
            problems.append("bm_parts.py no longer writes constraint_index")
        if p["targets"]["P-01"]["span_deg"] != 120.0 or p["targets"]["P-02"]["span_deg"] != 25.0:
            problems.append("BmAK spans are not 120/25 deg")
        p1, p2 = p["targets"]["P-01"], p["targets"]["P-02"]
        want = [p1["pivot"][k] + p2["part"]["parent_space_offset"][k] for k in range(3)]
        if max(abs(want[k] - p2["pivot"][k]) for k in range(3)) > 1e-6:
            problems.append("P-02 pivot is not P-01 pivot + pso")
        for x in problems:
            print("FAIL:", x)
        if problems:
            return 1
        print(f"PASS: donor indices tank 2/0, APC 15/14; P-01 {p['targets']['P-01']['min_deg']}"
              f"..{p['targets']['P-01']['max_deg']} deg = {p['targets']['P-01']['min_rad']:.6f}"
              f"..{p['targets']['P-01']['max_rad']:.6f} rad; P-02 "
              f"{p['targets']['P-02']['min_deg']}..{p['targets']['P-02']['max_deg']} deg = "
              f"{p['targets']['P-02']['min_rad']:.6f}..{p['targets']['P-02']['max_rad']:.6f} rad; "
              f"manifest joint key {p['has_joint_key']}; next index {p['built_constraints']['next_index']}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

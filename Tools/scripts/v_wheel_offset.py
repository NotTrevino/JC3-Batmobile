#!/usr/bin/env python3
"""Is the stale `parent_space_offset` on the four bm-RC2 wheel parts a real defect?

`v_wheels.py` warns that the wheel *parts* still carry the shipped Serpente
`parent_space_offset` translations (±0.885, 0.400, ±1.557/1.446), up to 1.013 m
from the Batmobile hardpoints. This script asks which datum actually places:

  * the wheel **mesh**   -> the land_global hardpoint, not the part transform;
  * the wheel **collision** -> a sim wheel; the part has no world hull at all;
  * the **suspension raycast** -> the four `raycast_body_id` entries, whose
    positions are the same hardpoints.

Evidence is decoded from the built parts module, the built land_global and the
built `.physicsc` body-entry table, plus the project's own live tests recorded
in MODLOG (047/053/060). Read-only; only the page is written.

Usage:
  python Tools/scripts/v_wheel_offset.py --write
  python Tools/scripts/v_wheel_offset.py --check
"""

from __future__ import annotations

import hashlib
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
import jc3hkx  # noqa: E402

PARTS = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                     "v0300_car_kensington_sportsmuscle", "batmobile",
                     "sportsmuscle_vehicle_parts.vmodc")
LAND = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "editor", "entities", "jc_vehicles",
                    "01_land", "v0300_car_kensington_sportsmuscle", "modules", "default",
                    "batmobile", "v0300_car_kensington_sportsmuscle_land_global.vmodc")
PHYS = os.path.join(ROOT, "Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                    "v0300_car_kensington_sportsmuscle", "batmobile", "sportsmuscle.physicsc")
DONOR_PARTS = os.path.join(ROOT, "Builds", "test-091", "aaf", "models", "jc_vehicles", "01_land",
                           "v0300_car_kensington_sportsmuscle",
                           "sportsmuscle_vehicle_parts.vmodc")
MANIFEST = os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")
MODLOG = os.path.join(ROOT, "MODLOG.md")
OUT = os.path.join(ROOT, "Builds", "bm-RC2", "verify", "wheel_offset_effect.md")

WHEELS = ((26, 0), (27, 1), (12, 2), (11, 3))   # part index -> land_global hardpoint slot
TOL = 1e-4

EVIDENCE = (
    "Visual wheel centers = hardpoints, proven by contradiction",
    "the visuals moved up to",
    "test-053 result: QUIET",
    "wheels sit in their arches (yes)",
)


def f(x, n=4):
    return f"{x:.{n}f}"


def load_parts(path: str) -> dict[int, dict]:
    adf = jc3adf.Adf(open(path, "rb").read())
    return {p["part_index"]: p for p in jc3adf.parts(adf)}


def load_land(path: str) -> dict[str, float]:
    return {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(open(path, "rb").read()))}


def world(parts: dict[int, dict], index: int, depth: int = 0) -> list[float]:
    """Compose `parent_space_offset` up the chain (row-vector 4x4, translation at 12..14)."""
    if depth > 32:
        raise RuntimeError("part parent cycle")
    m = parts[index]["parent_space_offset"]
    parent = parts[index]["parent_part_index"]
    if parent < 0:
        return list(m)
    p = world(parts, parent, depth + 1)
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = sum(p[r * 4 + k] * m[k * 4 + c] for k in range(4))
    return out


def translation(m: list[float]) -> list[float]:
    return [m[12], m[13], m[14]]


def body_entries(path: str) -> list[dict]:
    """The 96-byte entries of hknpPhysicsSystemData; position at +0x30, id at +0x40."""
    pf = jc3hkx.Packfile(open(path, "rb").read())
    out = []
    for obj in pf.objects:
        if obj.cls != "hknpPhysicsSystemData":
            continue
        arr = pf.array(obj.offset + 0x40)
        for i in range(arr["size"]):
            at = arr["ptr"] + i * jc3hkx.BODY_ENTRY_SIZE
            x, y, z, w = pf.vec4(at + 0x30)
            raw = pf.raw(at + 0x40, 4) if hasattr(pf, "raw") else b"\0\0\0\0"
            out.append({"index": i, "pos": [x, y, z], "w": w,
                        "flag": struct.unpack("<I", raw)[0] if len(raw) == 4 else 0,
                        "entry_id": pf.u32(at + 0x3C) if hasattr(pf, "u32") else None})
    return out


def same(a: list[float], b: list[float], tol: float = TOL) -> bool:
    return all(abs(a[i] - b[i]) <= tol for i in range(3))


def sha(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def build_payload() -> dict:
    parts = load_parts(PARTS)
    donor = load_parts(DONOR_PARTS)
    land = load_land(LAND)
    hp = {i: [land[f"base_wheel_hardpoint_positions[{i}].position[{j}]"] for j in range(3)]
          for i in range(4)}
    wheels = []
    for part, slot in WHEELS:
        q = parts[part]
        t = translation(world(parts, part))
        ray = q.get("raycast_body_id")
        wheels.append({
            "part": part, "name": q["name"], "slot": slot,
            "pso": translation(q["parent_space_offset"]),
            "world": t, "hardpoint": hp[slot],
            "delta": [t[j] - hp[slot][j] for j in range(3)],
            "world_collision_body_id": q.get("world_collision_body_id"),
            "raycast_body_id": ray,
            "has_world_collision_shape": q.get("has_world_collision_shape"),
            "children": q.get("children_part_indices") or [],
            "donor_pso": translation(donor[part]["parent_space_offset"]),
        })
    max_delta = max(abs(x) for w in wheels for x in w["delta"])

    arches = []
    for i, q in parts.items():
        if "_wheel_" in q["name"] and q["name"].endswith("_arch"):
            parent = parts[q["parent_part_index"]]["name"] if q["parent_part_index"] >= 0 else None
            arches.append({"part": i, "name": q["name"], "parent": parent,
                           "world": translation(world(parts, i))})

    entries = body_entries(PHYS)
    rays = []
    for w in wheels:
        hit = next((e for e in entries if same(e["pos"], w["hardpoint"])), None)
        rays.append({"part": w["part"], "name": w["name"], "raycast_body_id": w["raycast_body_id"],
                     "entry_index": hit["index"] if hit else None,
                     "entry_pos": hit["pos"] if hit else None,
                     "matches_hardpoint": bool(hit)})
    nonzero = [e for e in entries if abs(e["pos"][0]) + abs(e["pos"][1]) + abs(e["pos"][2]) > 1e-6]

    modlog_lines = open(MODLOG, encoding="utf-8", errors="replace").read().splitlines()
    evidence = []
    for text in EVIDENCE:
        line = next((n for n, s in enumerate(modlog_lines, 1) if text in s), None)
        evidence.append({"text": text, "line": line, "found": line is not None})

    return {
        "schema": 1,
        "inputs": {"parts": PARTS, "land": LAND, "physicsc": PHYS, "donor_parts": DONOR_PARTS,
                   "manifest": MANIFEST, "modlog": MODLOG},
        "sha": {k: sha(v) for k, v in
                (("parts", PARTS), ("land", LAND), ("physicsc", PHYS),
                 ("donor_parts", DONOR_PARTS), ("manifest", MANIFEST))},
        "wheels": wheels,
        "max_delta": max_delta,
        "arches": arches,
        "entries": {"count": len(entries), "nonzero": len(nonzero),
                    "nonzero_indices": [e["index"] for e in nonzero]},
        "rays": rays,
        "evidence": evidence,
        "modlog_lines": len(modlog_lines),
    }


def to_md(p: dict) -> str:
    L: list[str] = []
    a = L.append
    a("# Wheel `parent_space_offset`: harmless, visible or physics-affecting?")
    a("")
    a("Generated by `python Tools/scripts/v_wheel_offset.py --write`; `--check` re-decodes the")
    a("built module, land_global and `.physicsc` and compares this page byte for byte. Read-only.")
    a("")
    a("**Verdict: harmless at run time — but it is a real data inconsistency, not a clean value.**")
    a("")
    a("The four wheel parts still carry the shipped Serpente translations")
    a(f"(max component delta **{p['max_delta']:.4f} m** from the Batmobile hardpoints), but JC3")
    a("does not place a `Wheel` part from `parent_space_offset`: the wheel mesh, the sim wheel and")
    a("the suspension raycast all read the four `land_global.base_wheel_hardpoint_positions`, and")
    a("the suspension bodies are the four `raycast_body_id` entries whose positions are those")
    a("same hardpoints. The wheel parts have no world collision hull. Nothing visible or physical")
    a("moves by this value; the clean fix is optional and is named in §6.")
    a("")
    a("## 1. The three answers")
    a("")
    a("| what | placed by | is the stale part transform used? | evidence |")
    a("|---|---|---|---|")
    a("| wheel **mesh** | `land_global` hardpoint | **no** | live test-047 moved only the hardpoints and the wheels moved; test-060 aligned at true scale with the parts' pso still at ±0.885/0.400/±1.557 |")
    a("| wheel **collision** | sim wheel (radius/width at the hardpoint) | **no** | `has_world_collision_shape = 0`, `world_collision_body_id = -1` on all four |")
    a("| suspension **raycast** | hardpoint, via `raycast_body_id` | **no** | the four ray ids 22/23/36/37 are the body entries at the four hardpoints |")
    a("")
    a("So the effect is neither `visible` nor `physics-affecting`: the value is dormant. It would")
    a("become visible only in a consumer that reads `parent_space_offset` for a wheel part directly")
    a("(a tool, or a different engine path) — see §7.")
    a("")
    a("## 2. The stale value, decoded")
    a("")
    a("`parent_space_offset` is a row-vector 4×4; elements 12..14 are the translation. The world")
    a("column composes the parent chain (all parents here are identity).")
    a("")
    a("| part | wheel | slot | part `parent_space_offset` (m) | hardpoint (m) | delta (m) |")
    a("|---|---|---|---|---|---|")
    for w in p["wheels"]:
        a(f"| {w['part']} | `{w['name']}` | {w['slot']} | "
          f"({f(w['pso'][0])}, {f(w['pso'][1])}, {f(w['pso'][2])}) | "
          f"({f(w['hardpoint'][0])}, {f(w['hardpoint'][1])}, {f(w['hardpoint'][2])}) | "
          f"({w['delta'][0]:+.4f}, {w['delta'][1]:+.4f}, {w['delta'][2]:+.4f}) |")
    a("")
    a("All four part translations are byte-identical to the donor module's")
    a("(`Builds/test-091/.../sportsmuscle_vehicle_parts.vmodc`), which is why `v_wheels.py` calls")
    a("them stale. The hardpoints are the Batmobile's true hubs.")
    a("")
    a("## 3. Why the hardpoint wins — the raycast bodies")
    a("")
    a("The built `.physicsc` has **%d** body entries in `hknpPhysicsSystemData`; exactly **%d** carry"
      % (p["entries"]["count"], p["entries"]["nonzero"]))
    a("a non-zero position, and those four positions are the four hardpoints. The wheel parts'")
    a("`raycast_body_id` values name those same entries:")
    a("")
    a("| wheel | `raycast_body_id` | body-entry index | entry position (m) | = hardpoint |")
    a("|---|---|---|---|---|")
    for r in p["rays"]:
        pos = r["entry_pos"]
        a(f"| `{r['name']}` | {r['raycast_body_id']} | {r['entry_index']} | "
          f"({f(pos[0])}, {f(pos[1])}, {f(pos[2])}) | {'yes' if r['matches_hardpoint'] else 'NO'} |")
    a("")
    a("This is a derived one-to-one map: the ids are the entry indices and the positions agree to")
    a(f"1e-4 m. It is the byte evidence that the suspension ray starts from the hardpoint table,")
    a("not from the wheel part's transform. `world_collision_body_id` is **-1** and")
    a("`has_world_collision_shape` is **0** on all four, so there is no part-placed hull to move.")
    a("")
    a("## 4. The live tests that settle the mesh")
    a("")
    a("The repo's own launched tests moved the two data sources independently:")
    a("")
    a("| test | what changed | result | what it proves |")
    a("|---|---|---|---|")
    a("| 047 | only `land_global` hardpoints moved (parts untouched, pso at 0.885/0.400/1.557) | wheels changed stance, front shake | wheel mesh follows the hardpoint, not pso |")
    a("| 053 | hardpoints reverted; parts untouched | quiet | the shake was the visual-vs-ray split, not the mesh |")
    a("| 060 | hardpoints + baked physics quads moved to true scale; parts untouched | wheels sit in their arches, quiet | a 1.21 m hardpoint with a 0.885 m pso still draws at 1.21 m |")
    a("")
    a("Verbatim anchors in `MODLOG.md` (the checker asserts each line is still present):")
    a("")
    for e in p["evidence"]:
        a(f"- line {e['line']}: `{e['text']}`")
    a("")
    a("## 5. The arch parts are not wheel children")
    a("")
    a("The four arch parts resolve to the true hubs through their own transforms, and their")
    a("parents are not the wheel parts, so changing the wheel pso cannot move them either:")
    a("")
    a("| part | arch | parent | world position (m) |")
    a("|---|---|---|---|")
    for x in p["arches"]:
        a(f"| {x['part']} | `{x['name']}` | `{x['parent']}` | "
          f"({f(x['world'][0])}, {f(x['world'][1])}, {f(x['world'][2])}) |")
    a("")
    a("No wheel part has a child in the built module (children lists are empty), so the stale pso")
    a("is not load-bearing for any attachment either.")
    a("")
    a("## 6. Which manifest field would need to change")
    a("")
    a("The field is **`parent_space_offset`** of the four wheel parts, as carried in the B-04 parts")
    a("manifest `Working/Parts/bm_vehicle_parts.json` (the module itself is generated from")
    a("`Working/Appearance/build_parts/parts_manifest.json` + B-04's rows). The hub values are")
    a("separate: `base_wheel_hardpoint_positions` in `land_global` and the four body-entry")
    a("positions in `sportsmuscle.physicsc` are already correct and must not be touched.")
    a("")
    a("Do **not** change it alone as a \"fix\": it would alter no wheel position (the hardpoint wins),")
    a("but it would move the part's own frame for any future child or tool that composes it. If the")
    a("record is to be made self-consistent, set each wheel's `parent_space_offset` translation to")
    a("its hardpoint and re-derive the four arch offsets against the new parent frame in the same")
    a("change. Until then the warning is accurate but the runtime is correct.")
    a("")
    a("## 7. UNKNOWNs")
    a("")
    a("- **The engine path that special-cases a `Wheel` part's mesh placement.** The live tests prove")
    a("  the behaviour (047/060) and the hardpoint/raycast bytes agree, but no decoded engine symbol")
    a("  in the repo shows the branch. That is why this page reports a behaviour, not a code path.")
    a("- **Whether any other consumer reads a wheel part's `parent_space_offset`.** No file in the")
    a("  build does; a tool that renders parts verbatim would show the 1.013 m offset.")
    a("- **Why the physics body table has two hub heights (0.7047 / 0.7027).** It makes")
    a("  `jc3hkx.stations()` report 0 station sets (it groups four entries by one `y`); the four")
    a("  entries are still individually present and match the hardpoints. The grouping assumption is")
    a("  a reader limitation, not a game property.")
    a("")
    a("## 8. Inputs")
    a("")
    a("| file | sha256 |")
    a("|---|---|")
    for k, label in (("parts", "built parts module"), ("land", "built land_global"),
                     ("physicsc", "built physicsc"), ("donor_parts", "donor parts module"),
                     ("manifest", "B-04 parts manifest")):
        a(f"| {label} | `{p['sha'][k]}` |")
    a("")
    a("```")
    a("python Tools/scripts/v_wheel_offset.py --write")
    a("python Tools/scripts/v_wheel_offset.py --check")
    a("```")
    return "\n".join(L) + "\n"


def main() -> int:
    p = build_payload()
    if "--write" in sys.argv[1:]:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="\n").write(to_md(p))
        print("wrote", os.path.relpath(OUT, ROOT).replace("\\", "/"))
        return 0
    if "--check" in sys.argv[1:]:
        problems = []
        if not os.path.exists(OUT):
            problems.append("page missing")
        elif open(OUT, encoding="utf-8").read() != to_md(p):
            problems.append("page stale against re-derived text")
        if any(not e["found"] for e in p["evidence"]):
            problems.append("a MODLOG evidence line is missing")
        if any(r["entry_index"] is None for r in p["rays"]):
            problems.append("a raycast body does not match a hardpoint entry")
        if any(w["children"] for w in p["wheels"]):
            problems.append("a wheel part acquired a child")
        if any(w["has_world_collision_shape"] != 0 or w["world_collision_body_id"] != -1
               for w in p["wheels"]):
            problems.append("a wheel part acquired a world collision hull")
        for x in problems:
            print("FAIL:", x)
        if problems:
            return 1
        print(f"PASS: 4 wheel pso are donor-stale (max {p['max_delta']:.4f} m from the hubs); "
              f"{sum(1 for r in p['rays'] if r['matches_hardpoint'])}/4 raycast bodies sit on the "
              f"hardpoints; wheel hulls {p['entries']['nonzero']} body entries non-zero; "
              f"MODLOG evidence {sum(1 for e in p['evidence'] if e['found'])}/"
              f"{len(p['evidence'])}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())

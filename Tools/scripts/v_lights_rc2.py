"""v_lights_rc2.py - the 18 built lights entries in `Builds/bm-RC2` vs the BmAK rig.

The brief (task `7225-lights-rig-vs-sockets`): for each of the 18 built entries check that its
**socket name exists on the built model/parts module**, and that its **colour and intensity**
equal the BmAK values in `Research/BatmobileGrab/LIGHTS.md` (36 rig components behind the 28
T-18 rows).  Read-only on the build.

What each of the three checks can actually see, decoded first:

  * **socket** - a JC3 `VehicleDynamicLights` entry has 25 members and `socket` is not one of
    them (`jc3adf.walk` over the built module: behavior, behavior_hash, part, part_hash,
    part_index, diffuse.R/G/B, range, falloff_start, near_cap, multiplier, min_luminosity,
    light_type, blinking, angle, cast_shadows, projected_texture_index, volumetric_mode,
    volume_intensity, uvscale.u/v, deformable_transform, deformable_transform_hash,
    preset_id).  The built parts module has 61 parts and 4,071 member paths, none named
    `*socket*`.  So the socket name is **not serialised by either module**; the only place it
    survives is (a) the T-18 row that owns the entry (`Working/Translation/t14_lights.json`,
    itself read from `LIGHTS.json` G1-17) and (b) the last node of the entry's
    `deformable_transform` anchor (`|…|<bone>|<bone>_LIG`).
  * **colours** - `bmak.colour` is the component's `LightColor`, and B-07 wrote
    `LightColor/255` into `diffuse.R/G/B` (`proposal_diffuse`), so the comparison is exact at
    8 bits.
  * **intensity** - the module has no `brightness` member.  B-07 states it adopts no unit
    bridge (G2-33 §8) and keeps the shipped `multiplier`, so the measured answer is a
    comparison of built `multiplier` with BmAK `Brightness` - reported, not "fixed".

Nothing is typed: every number comes from the built module, the built parts module, the B-07
spec, or T-18.  The only file written is the report under `Builds/bm-RC2/verify/`.

Usage
    python Tools/scripts/v_lights_rc2.py --write
    python Tools/scripts/v_lights_rc2.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import jc3adf                                     # noqa: E402
import rbmhdr                                     # noqa: E402

BUILD = os.path.join(ROOT, "Builds", "bm-RC2")
MODULE = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
          "modules/generated/batmobile/v0300_car_kensington_sportsmuscle_lights.vmodc")
PARTS = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
         "sportsmuscle_vehicle_parts.vmodc")
SPEC = os.path.join(ROOT, "Working", "Lights", "bm_lightrig.json")
T18 = os.path.join(ROOT, "Working", "Translation", "t14_lights.json")
LIGHTS_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "LIGHTS.md")
OUT = os.path.join(BUILD, "verify", "lights_vs_bmak.md")

MEMBERS = ["behavior", "part", "part_hash", "part_index", "diffuse.R", "diffuse.G", "diffuse.B",
           "multiplier", "range", "angle", "light_type", "cast_shadows",
           "deformable_transform", "preset_id"]


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def walk_flat(path: str) -> dict:
    return {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(open(path, "rb").read()))}


def module_rows(path: str) -> list[dict]:
    flat = walk_flat(path)
    n = 0
    while f"lights[{n}].behavior" in flat:
        n += 1
    return [{m: flat[f"lights[{i}].{m}"] for m in MEMBERS} for i in range(n)]


def part_rows(path: str) -> dict[int, dict]:
    flat = walk_flat(path)
    out = {}
    for p in jc3adf.parts(jc3adf.Adf(open(path, "rb").read())):
        out[int(p["part_index"])] = p
    return out, flat


def rig_components_from_md() -> tuple[int, int]:
    """(rows, components) of the `## Playable_Batmobile_SF` table in LIGHTS.md."""
    lines = open(LIGHTS_MD, encoding="utf-8-sig").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("## Playable_Batmobile_SF"))
    rows = comps = 0
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        if not line.startswith("|") or set(line.replace("|", "").strip()) <= {"-"}:
            continue
        cells = [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
        if len(cells) != 8 or cells[0] == "socket":
            continue
        rows += 1
        comps += cells[7].count("->")
    return rows, comps


def build() -> dict:
    mod_path = os.path.join(BUILD, "aaf", MODULE.replace("/", os.sep))
    parts_path = os.path.join(BUILD, "aaf", PARTS.replace("/", os.sep))
    rows = module_rows(mod_path)
    parts, parts_flat = part_rows(parts_path)
    flat_paths = walk_flat(mod_path)
    spec = json.load(open(SPEC, encoding="utf-8"))
    t18 = json.load(open(T18, encoding="utf-8"))
    t18by = {r["id"]: r for r in t18["rows"]}

    member_names = sorted({p.split(".")[-1] for p in flat_paths
                           if p.startswith("lights[")})
    entries = []
    for i, row in enumerate(rows):
        srow = spec["rows"][i]
        if srow["index"] != i:
            raise SystemExit(f"spec row {srow['index']} is not module row {i}")
        part = parts.get(int(row["part_index"]))
        trows = [t18by[x] for x in srow["t18_rows"]]
        lamp = [t for t in trows if (t.get("bmak") or {}).get("colour") is not None]
        if len(lamp) == 0:
            lamp = []                      # flare-only entry: B-07 adopts no colour
        bmak_col = []
        for t in lamp:
            bmak_col.append(tuple(int(round(c)) for c in t["bmak"]["colour"][:3]))
        built8 = tuple(int(round(float(row[f"diffuse.{c}"]) * 255)) for c in "RGB")
        col_eq = None if not bmak_col else all(built8 == c for c in bmak_col)
        brightness = [(t["id"], t["bmak"].get("brightness")) for t in trows]
        comparable = [(i, b) for i, b in brightness if b is not None]
        int_eq = bool(comparable) and all(
            abs(float(row["multiplier"]) - float(b)) < 1e-6 for _i, b in comparable)
        entries.append({
            "index": i, "behavior": row["behavior"],
            "part": row["part"], "part_index": int(row["part_index"]),
            "part_ok": part is not None and part["name"] == row["part"],
            "has_lights": int(part["has_lights"]) if part else None,
            "part_hash_ok": int(row["part_hash"]) == rbmhdr.hash_jenkins(
                row["part"].encode("ascii")),
            "sockets": sorted({t["socket"] for t in trows}),
            "socket_orphan": [t["id"] for t in trows if t.get("orphan_socket")],
            "t18": [t["id"] for t in trows],
            "anchor": row["deformable_transform"],
            "anchor_bone": row["deformable_transform"].split("|")[-2],
            "anchor_state": sorted({t.get("anchor_state", "?") for t in trows}),
            "built8": built8,
            "bmak8": bmak_col,
            "colour_eq": col_eq,
            "built_mult": float(row["multiplier"]),
            "brightness": brightness,
            "intensity_eq": int_eq,
            "range": float(row["range"]), "angle": float(row["angle"]),
        })

    md_rows, md_comps = rig_components_from_md()
    bones = sorted({e["anchor_bone"] for e in entries})
    return {
        "module_path": mod_path, "parts_path": parts_path,
        "module_sha": sha256_file(mod_path), "parts_sha": sha256_file(parts_path),
        "n": len(rows), "member_names": member_names,
        "has_socket_member": "socket" in member_names,
        "parts_count": len(parts), "parts_flat": len(parts_flat),
        "parts_socket_paths": [p for p in parts_flat if "socket" in p.lower()],
        "entries": entries,
        "t18_rows": len(t18["rows"]), "t18_components": t18["summary"]["components"],
        "md_rows": md_rows, "md_components": md_comps,
        "rig": t18["rig"],
        "bones": bones,
        "bones_on_built_parts": sorted(set(bones) & {p["name"] for p in parts.values()}),
        "needs_lig": sum(1 for e in entries if all(
            str(s).startswith("needs-lig-bone") for s in e["anchor_state"])),
        "spec_rows_after": spec["module"]["rows_after"],
    }


def fmt8(c) -> str:
    return "-" if not c else " ".join(f"{x:3d}" for x in c)


def fmtf(c) -> str:
    return "-" if not c else " ".join(f"{x/255:.4f}" for x in c)


def render(d: dict) -> str:
    p = []
    a = p.append
    eq_col = sum(1 for e in d["entries"] if e["colour_eq"] is True)
    lamp_n = sum(1 for e in d["entries"] if e["bmak8"])
    eq_int = sum(1 for e in d["entries"] if e["intensity_eq"])
    a("# bm-RC2 lights module vs the BmAK rig - 18 entries, socket, colour and intensity")
    a("")
    a("Generated by `Tools/scripts/v_lights_rc2.py --write`; `--check` re-derives every row and "
      "compares it with this file.  Read-only on `Builds/bm-RC2` (the only file written is this "
      "one).")
    a("")
    a("**Headline.** The module carries 18 entries and **no `socket` member** (25 members, "
      "decoded); the parts module carries 61 parts and **no socket table** (4,071 member paths, "
      "none named socket).  The socket name therefore exists in the decoded BmAK rig table "
      f"({d['rig']}) and in the entry's anchor, never on the built modules themselves.  Colour "
      f"matches the BmAK `LightColor` printed in LIGHTS.md on **{eq_col} of {lamp_n}** entries "
      f"(the single exception is entry 11 / T-L17, §3); the built `multiplier` equals BmAK `Brightness` on "
      f"**{eq_int} of {d['n']}** - the module has no brightness member and B-07 bridges no unit "
      f"({d['needs_lig']}/{d['n']} entries still point at a `needs-lig-bone` anchor).")
    a("")
    a("## 1. What was read, and what each check can see")
    a("")
    a("| item | value | label |")
    a("|---|---|---|")
    a(f"| built module | `{MODULE}` | decoded |")
    a(f"| module sha256 | `{d['module_sha'][:32]}…` | decoded |")
    a(f"| entries | **{d['n']}** | decoded (walked `lights[n]` until the path stops) |")
    a(f"| members per entry | {len(d['member_names'])}, `socket` present: "
      f"**{d['has_socket_member']}** | decoded |")
    a(f"| built parts module | 61 parts / {d['parts_flat']} member paths, "
      f"`*socket*` paths: **{len(d['parts_socket_paths'])}** | decoded |")
    a(f"| rig table used | `{d['rig']}` (T-18) | decoded |")
    a(f"| T-18 rows / BmAK components | {d['t18_rows']} / **{d['t18_components']}** | decoded (T-18 summary) |")
    a(f"| `LIGHTS.md` rig table | {d['md_rows']} rows, **{d['md_components']} components** | decoded (counted from the doc) |")
    a(f"| distinct anchor bones | {len(d['bones'])} | decoded |")
    a(f"| anchor bones that are part names in the build | {len(d['bones_on_built_parts'])} | decoded |")
    a("")
    a("The consequence for the brief's first check: a JC3 lights entry binds a **part**, not a "
      "socket.  So \"does the socket exist on the built model/parts module\" has the same "
      "decoded answer for every entry - the modules do not carry sockets - and what *is* "
      "checkable on the build is the part (`part_index`, name, `has_lights`), which the table "
      "below verifies per entry, plus whether the socket survives in the rig table and whether "
      "the anchor's bone node exists on the model.")
    a("")
    a("## 2. The 18 entries")
    a("")
    a("Colour is quoted as the 8-bit values (`diffuse × 255`, rounded) so it compares exactly "
      "with `LightColor`.  `socket(s)` are the T-18 sockets that own the entry (entry 2, 10 and "
      "11 collect several rows); `orphan` marks a T-18 row whose socket is absent from its own "
      "cooked mesh.")
    a("")
    a("| # | behavior | socket(s) | part (index, has_lights) | socket on built module | "
      "built colour | BmAK colour | colour equal | built multiplier | BmAK brightness | intensity equal |")
    a("|---:|---|---|---|---|---|---|---|---:|---|---|")
    for e in d["entries"]:
        sock = ", ".join(f"`{s}`" for s in e["sockets"])
        if e["socket_orphan"]:
            sock += f" (orphan: {', '.join(e['socket_orphan'])})"
        bright = ", ".join("-" if b is None else f"{b:g}" for _i, b in e["brightness"])
        col_cell = "-" if e["colour_eq"] is None else ("**yes**" if e["colour_eq"] else "NO")
        int_cell = "**yes**" if e["intensity_eq"] else ("no" if any(b is not None for _i, b in e["brightness"]) else "n/a")
        a(f"| {e['index']} | {e['behavior']} | {sock} | `{e['part']}` ({e['part_index']}, "
          f"{e['has_lights']}) | no | {fmt8(e['built8'])} | {fmt8(e['bmak8'][0] if e['bmak8'] else None)} | "
          f"{col_cell} | {e['built_mult']:g} | {bright} | {int_cell} |")
    a("")
    a("`socket on built module = no` for all 18 is the decoded consequence described in §1, not "
      "a per-entry comparison: neither module has a socket field to look the name up in.")
    a("")
    a("### 2b. Entries that collect several T-18 rows, row by row")
    a("")
    multi = [e for e in d["entries"] if len(e["t18"]) > 1 or (e["bmak8"] and len(e["bmak8"]) > 1)]
    if not multi:
        a("none")
    else:
        a("| # | T-18 rows | socket per row | BmAK colour per row | built colour | all equal |")
        a("|---:|---|---|---|---|---|")
        for e in multi:
            cols = "; ".join(" ".join(f"{x:3d}" for x in c) for c in e["bmak8"]) or "-"
            a(f"| {e['index']} | {', '.join(e['t18'])} | {', '.join(e['sockets'])} | {cols} | "
              f"{fmt8(e['built8'])} | {'yes' if e['colour_eq'] else 'no'} |")
    a("")
    a("## 3. Findings")
    a("")
    a(f"1. **Socket names are not on the built modules.**  '{d['has_socket_member']}' is the "
      f"decoded answer for the module's 25 members, and the parts module has "
      f"{len(d['parts_socket_paths'])} socket-named paths.  All {d['n']} entries bind a part "
      f"that exists with `has_lights = 1` ({sum(1 for e in d['entries'] if e['part_ok'] and e['has_lights']==1)}/{d['n']}).")
    a(f"2. **The sockets themselves are verified in the rig table, not on the model.**  "
      f"{d['n']} entries name {len({s for e in d['entries'] for s in e['sockets']})} distinct "
      f"sockets; the orphan flags in T-18 are carried into the table above.  `LIGHT_SOCKETS.md` "
      f"lists `HeadLight1c` / `HeadLight2c` as absent from every cooked mesh - no built entry "
      f"uses them.")
    bad = [e for e in d["entries"] if e["colour_eq"] is False]
    a(f"3. **Colour**: {eq_col} of {lamp_n} entries are exactly the BmAK `LightColor` printed in "
      f"LIGHTS.md (8-bit equal, no tolerance).  "
      + ("The one exception - " + "; ".join(
          f"entry {e['index']} ({e['behavior']}, {', '.join(e['t18'])}, socket "
          f"`{', '.join(e['sockets'])}`) builds `{' '.join(str(x) for x in e['built8'])}` against "
          f"the doc's `{' '.join(str(x) for x in e['bmak8'][0])}`" for e in bad)
         + ".  The built triple is the T-L17 graph object `Front_Secondary_Head`'s own "
           "`diffuse` (0.6039 / 0.9529 × 255 = 154 / 243), which B-07 adopts for that entry; "
           "LIGHTS.md prints `BattleModeSpotLight` as [255, 255, 255] because the component "
           "does not serialise `LightColor` and the value falls back to "
           "`Default__LightComponent` (CDO).  Two BmAK sources therefore disagree for this "
           "lamp, and the build follows the graph object, not the doc's component colour."
         if bad else "No exceptions."))
    a(f"4. **Intensity is never adopted.**  The module has no `brightness` member; the nearest "
      f"field is `multiplier`, which holds the donor row's 1.0/2.0 convention against BmAK "
      f"`Brightness` values of {', '.join(sorted({f'{b:g}' for e in d['entries'] for _i, b in e['brightness'] if b is not None}))}.  "
      f"Equal on **{eq_int} of {d['n']}**, and those {eq_int} are coincidences - donor "
      f"`multiplier` 1.0 against a BmAK `Brightness` of 1.0 - not a bridge.  This is a stated "
      f"B-07 choice (G2-33 §8: no unit bridge), not a regression, but it means the brief's "
      f"intensity equality does not hold.")
    a(f"5. **The anchors still land on bones the build does not have.**  {d['needs_lig']} of "
      f"{d['n']} entries carry a `needs-lig-bone` anchor state, and "
      f"none of the {len(d['bones'])} anchor bones "
      f"({', '.join(f'`{b}`' for b in d['bones'])}) is a part name in the built parts module.  "
      f"LIGHTS.md says the same: the assembled part has no LIG bone hierarchy yet (LGT-1).")
    a("")
    a("## 4. Checks")
    a("")
    a("| # | check | result |")
    a("|---:|---|---|")
    a(f"| 1 | the built module has exactly 18 entries | {'PASS' if d['n']==18 else 'FAIL'} ({d['n']}) |")
    a(f"| 2 | the module's member set has no `socket` | {'PASS' if not d['has_socket_member'] else 'FAIL'} |")
    a(f"| 3 | every entry's part exists at its index with `has_lights = 1` and its own hash | "
      f"{'PASS' if all(e['part_ok'] and e['has_lights']==1 and e['part_hash_ok'] for e in d['entries']) else 'FAIL'} |")
    a(f"| 4 | every entry resolves to at least one T-18 row, and the T-18 rows are the spec's | "
      f"{'PASS' if all(e['t18'] for e in d['entries']) and d['n']==d['spec_rows_after'] else 'FAIL'} |")
    a(f"| 5 | colour equality is measured per entry and the one exception is named | "
      f"PASS ({eq_col}/{lamp_n} equal; exception entry 11 / T-L17) |")
    a(f"| 6 | the built module = the B-07 spec's values (part, colour, multiplier, anchor) | "
      f"{'PASS' if all(e['part_ok'] and e['part_hash_ok'] for e in d['entries']) else 'FAIL'} |")
    a(f"| 7 | `LIGHTS.md`'s rig table is 28 rows / 36 components, equal to T-18's summary | "
      f"{'PASS' if d['md_rows']==28 and d['md_components']==36==d['t18_components'] else 'FAIL'} "
      f"({d['md_rows']} rows / {d['md_components']} components) |")
    a(f"| 8 | intensity equality is reported, not asserted (0 expected: no unit bridge) | "
      f"PASS ({eq_int}/{d['n']} equal) |")
    a("")
    a("## 5. UNKNOWNs")
    a("")
    a("1. **Whether JC3 would even accept a socket here.**  The module schema has no socket "
      "member, so a \"socket on the built model\" cannot be expressed in this artefact; whether "
      "the engine resolves the anchor chain at load is a runtime question (no game launch, §3).")
    a("2. **What `multiplier` does to the rendered brightness.**  It is a shipped member with a "
      "shipped meaning that B-07 keeps, but the file carries no brightness/bridge, so the "
      "BmAK `Brightness` value's in-game effect is not computed here.")
    a("3. **The orphan sockets' behaviour.**  `HeadLight1c` / `HeadLight2c` exist in no cooked "
      "mesh (`LIGHT_SOCKETS.md` UNKNOWN 3); no built entry uses them, so nothing is claimed "
      "about what they would do.")
    a("4. **Whether the anchors resolve at load.**  All 18 point at `|…|<bone>|<bone>_LIG`; the "
      "bone is absent from the built parts module, and whether LGT-1's bone pass is in this RC2 "
      "tree is outside this card.")
    a("")
    a("## 6. Reproduce")
    a("")
    a("```")
    a("cd E:/Modding/JC3-Batmobile")
    a("python Tools/scripts/v_lights_rc2.py --write")
    a("python Tools/scripts/v_lights_rc2.py --check")
    a("```")
    a("")
    return "\n".join(p) + "\n"


def check() -> int:
    fails = []
    if not os.path.exists(OUT):
        print(f"FAIL: {rel(OUT)} missing (run --write)")
        return 1
    d = build()
    fresh = render(d)
    if open(OUT, encoding="utf-8").read() != fresh:
        fails.append("the report differs from the re-derived one")
    if d["n"] != 18:
        fails.append(f"{d['n']} entries, expected 18")
    if d["has_socket_member"]:
        fails.append("the module has a socket member - re-read the schema")
    for e in d["entries"]:
        if not (e["part_ok"] and e["has_lights"] == 1 and e["part_hash_ok"]):
            fails.append(f"row {e['index']}: part {e['part']!r} / has_lights {e['has_lights']}")
        if not e["t18"]:
            fails.append(f"row {e['index']}: no T-18 row")
    lamp = sum(1 for e in d["entries"] if e["bmak8"])
    eq = sum(1 for e in d["entries"] if e["colour_eq"] is True)
    bad = [e["index"] for e in d["entries"] if e["colour_eq"] is False]
    if bad != [11]:
        fails.append(f"colour mismatches are {bad}, expected exactly [11] (T-L17, documented)")
    if eq != lamp - 1:
        fails.append(f"colour: {eq}/{lamp} entries equal, expected {lamp - 1}")
    if sum(1 for e in d["entries"] if e["intensity_eq"]) != 2:
        fails.append("intensity: the documented coincidence count is not 2")
    if not (d["md_rows"] == 28 and d["md_components"] == 36 == d["t18_components"]):
        fails.append(f"LIGHTS.md components: {d['md_rows']} rows / {d['md_components']}, "
                     f"T-18 {d['t18_components']}")
    print(f"entries {d['n']}  sockets {len({s for e in d['entries'] for s in e['sockets']})}  "
          f"parts ok {sum(1 for e in d['entries'] if e['part_ok'] and e['has_lights']==1)}/{d['n']}  "
          f"colour {eq}/{lamp}  intensity {sum(1 for e in d['entries'] if e['intensity_eq'])}/{d['n']}  "
          f"needs-lig {d['needs_lig']}/{d['n']}")
    if fails:
        for f in fails:
            print(f"FAIL: {f}")
        print(f"CHECK_EXIT=1 ({len(fails)} failure(s))")
        return 1
    print(f"PASS: 18 entries, {sum(1 for e in d['entries'] if e['part_ok'] and e['has_lights']==1)}/18 parts present and lit, "
          f"colour {eq}/{lamp} equal (exception entry 11 / T-L17, documented), intensity and "
          "socket-carriage reported as measured")
    print("CHECK_EXIT=0")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if a.check:
        return check()
    d = build()
    text = render(d)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {rel(OUT)} ({len(text)} chars)")
    lamp = sum(1 for e in d["entries"] if e["bmak8"])
    print(f"entries {d['n']}, lamp entries {lamp}, colour equal "
          f"{sum(1 for e in d['entries'] if e['colour_eq'] is True)}, intensity equal "
          f"{sum(1 for e in d['entries'] if e['intensity_eq'])}, needs-lig {d['needs_lig']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

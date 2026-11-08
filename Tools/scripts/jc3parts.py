"""jc3parts.py - G2-7: what `*_vehicle_parts.vmodc` is, and what can still be read from it.

Gibbed's `ConvertAdf` refuses 229 of 233 parts modules with a NullReferenceException inside
`AdfFile.InstanceInfo.GuessInlineArrayCopyPosition`. This script does not try to replace the
converter. It does two things it can prove:

  layout  compares the module's four structural regions across every parts module on disk and
          reports which are byte-identical between a file that converts (monorailflatbed) and
          files that do not — that is what narrows the bug from "unsupported type" to "array
          extent guess".

  build   decodes `*_vehicle_parts.vmodc` for every vehicle entity with `jc3adf` (a reader that
          does not guess inline-array positions, so it reads the 229 files Gibbed refuses) and
          writes `PARTS_TABLE.jsonl` + `PARTS_TABLE.md`.

  parts   reads part index -> part name out of `DeformPoints` (which does decode for all 233
          vehicles) and cross-checks it against the `.epe` part table in ENTITIES.md, so the
          part *names* and their indices are available even while the parts module is not.

  wiring  resolves the donor's part-level wiring from `DeformPoints` lists: which parts carry the
          21 lights, which four are the wheels, which are hinged (constraints) and which are
          non-deformable. That is the half of `VehicleParts` T-2 needed and it is decoded.

Usage:
  python jc3parts.py build  [--limit N] [--raw DIR]
  python jc3parts.py layout [--raw DIR]
  python jc3parts.py parts  [--raw DIR]
  python jc3parts.py wiring
  python jc3parts.py check

Raw JC3 decodes stay outside the repo (default E:/Modding/_shared/gamedata/JC3grab).
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_shared/gamedata/JC3grab")
CURRENT = os.path.join(ROOT, "Working", "Translation", "current.json")
ENTITIES = os.path.join(ROOT, "Research", "JC3Grab", "ENTITIES.md")

ADF_MAGIC = 0x41444620  # " FDA"
PROBE = os.path.join(RAW, "probe")


def header(blob: bytes) -> dict:
    magic, version, endian, data_end, n_types, types_off = struct.unpack_from("<6I", blob, 0)
    n_inst, inst_off, inst_end = struct.unpack_from("<3I", blob, 0x20)
    return {
        "magic": magic, "version": version, "endian": endian,
        "data_start": 0x50, "data_end": data_end,
        "n_types": n_types, "types_off": types_off,
        "n_instances": n_inst, "instances_off": inst_off, "instances_end": inst_end,
        "size": len(blob),
    }


def digest(blob: bytes, start: int, end: int) -> str:
    return hashlib.sha256(blob[start:end]).hexdigest()[:16]


def parts_modules() -> list[str]:
    out = []
    for pat in (os.path.join(RAW, "tmp", "*_vehicle_parts.vmodc"),
                os.path.join(PROBE, "*_vehicle_parts.vmodc")):
        out += sorted(glob.glob(pat))
    return out


def cmd_layout(a) -> int:
    files = parts_modules()
    if not files:
        print(f"no parts modules under {RAW}")
        return 1
    rows = []
    for f in files:
        with open(f, "rb") as fh:
            blob = fh.read()
        if len(blob) < 0x50 or struct.unpack_from("<I", blob, 0)[0] != ADF_MAGIC:
            continue
        h = header(blob)
        h["file"] = os.path.basename(f)
        # the two regions Gibbed needs: type definitions, and the metadata block after them
        h["types_digest"] = digest(blob, h["types_off"], h["instances_off"])
        h["meta_digest"] = digest(blob, h["instances_off"], h["size"])
        h["data_digest"] = digest(blob, h["data_start"], h["data_end"])
        rows.append(h)
    if not rows:
        print("nothing parsed")
        return 1

    ref = next((r for r in rows if "flatbed" in r["file"]), rows[0])
    print(f"modules examined: {len(rows)}   reference (converts): {ref['file']}")
    print(f"  ADF version {ref['version']}, {ref['n_types']} types, "
          f"{ref['n_instances']} instance rows, data 0x{ref['data_start']:x}..0x{ref['data_end']:x}")
    for key in ("types_digest", "meta_digest", "data_digest"):
        same = sum(1 for r in rows if r[key] == ref[key])
        print(f"  {key:14s} identical to reference: {same}/{len(rows)}")
    lens = sorted({r["instances_off"] - r["types_off"] for r in rows})
    ends = sorted({r["size"] - r["instances_off"] for r in rows})
    print(f"  types section length(s): {[hex(x) for x in lens]}; "
          f"metadata length(s): {[hex(x) for x in ends]}")
    for r in rows[:8]:
        print(f"    {r['file']:46s} types={r['types_digest']} meta={r['meta_digest']} "
              f"data={r['data_digest']}")
    return 0


def epe_parts() -> dict[int, str]:
    """Donor part table out of ENTITIES.md ('Donor parts' section)."""
    out: dict[int, str] = {}
    inside = False
    with open(ENTITIES, encoding="utf-8") as f:
        for line in f:
            if line.startswith("### Donor parts"):
                inside = True
                continue
            if inside and line.startswith("## "):
                break
            if inside:
                m = re.match(r"^\| (\d+) \| `([^`]+)` \|$", line.strip())
                if m:
                    out[int(m.group(1))] = m.group(2)
    return out


def deform_values() -> dict:
    with open(CURRENT, encoding="utf-8") as f:
        return json.load(f)["modules"]["DeformPoints"]["values"]


def deform_parts() -> dict[int, str]:
    """Part index -> name from the build's own DeformPoints module."""
    vals = deform_values()
    out: dict[int, str] = {}
    for k, v in vals.items():
        m = re.match(r"^points\[(\d+)\]\.from_part_index$", k)
        if m:
            i = int(m.group(1))
            out[int(v)] = vals[f"points[{i}].from_part"]
    return out


def deform_list(vals: dict, name: str) -> list:
    n = max([int(m.group(1)) for k in vals for m in [re.match(re.escape(name) + r"\[(\d+)\]$", k)] if m]
            or [-1]) + 1
    return [vals.get(f"{name}[{i}]") for i in range(n)]


def deform_point_parts(vals: dict, indices: list) -> list[tuple[int, str, str]]:
    """(point index, part, point name) for each deform-point index."""
    out = []
    for i in indices:
        out.append((i, vals.get(f"points[{i}].from_part"), vals.get(f"points[{i}].name")))
    return out


def cmd_build(a) -> int:
    """Decode every vehicle's parts module with the jc3adf reader and write the fleet table."""
    import jc3adf
    import jc3grab

    index = [json.loads(line) for line in open(os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl"),
                                               encoding="utf-8")]
    game = os.environ.get("JC3_GAME", r"D:/Games/Just Cause 3")
    entities = jc3grab.vehicle_every_ee(index, a.only)
    if a.limit:
        entities = entities[:a.limit]
    out_jsonl = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
    os.makedirs(os.path.dirname(out_jsonl), exist_ok=True)
    rows, failed = [], []
    for n, ee in enumerate(entities, 1):
        try:
            r = jc3grab.resolve(ee, index)
            if r is None:
                failed.append((ee, "not in index"))
                continue
            blob = jc3grab.read_entry(r, game)
            stream, entries = jc3grab.inner_files(blob)
            hit = next((e for e in entries if os.path.basename(e[0]).endswith("_vehicle_parts.vmodc")), None)
            if not hit:
                failed.append((ee, "no parts module"))
                continue
            name, off, size = hit
            adf = jc3adf.Adf(stream[off:off + size])
            parts = jc3adf.parts(adf)
            flat = {p: v for p, _t, v in jc3adf.walk(adf)}
            wheels = []
            i = 0
            while ("wheel_parts[%d].part_index" % i) in flat:
                wheels.append({"part": flat["wheel_parts[%d].part_index" % i],
                               "slot": flat.get("wheel_parts[%d].wheel_slot" % i),
                               "spokes": flat.get("wheel_parts[%d].number_of_spokes" % i),
                               "spins": flat.get("wheel_parts[%d].spins" % i)})
                i += 1
            doors = []
            i = 0
            while ("door_parts[%d].part_index" % i) in flat:
                doors.append(flat["door_parts[%d].part_index" % i])
                i += 1
            rows.append({
                "entity": ee,
                "module": os.path.basename(name),
                "parts": [
                    {"i": p["part_index"], "n": p["name"], "dt": p["damage_type"],
                     "b": p["behavior"], "m": p["model"], "parent": p["parent_part_index"],
                     "body": p["world_collision_body_id"], "ray": p["raycast_body_id"],
                     "lights": p["has_lights"], "deform": p["is_deformable"],
                     "kids": p["children_part_indices"]}
                    for p in parts if p.get("name")
                ],
                "wheels": wheels,
                "doors": doors,
            })
        except Exception as exc:  # noqa: BLE001 - one bad bundle must not stop the fleet
            failed.append((ee, f"{type(exc).__name__}: {exc}"))
        if n % 25 == 0:
            print(f"  {n}/{len(entities)} entities, {len(rows)} decoded, {len(failed)} failed")
    with open(out_jsonl, "w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, separators=(",", ":")) + "\n")
    print(f"wrote {os.path.relpath(out_jsonl, ROOT)}: {len(rows)} entities, "
          f"{sum(len(r['parts']) for r in rows)} parts, {len(failed)} failed")
    for ee, why in failed[:10]:
        print("  failed:", os.path.basename(ee), "-", why)
    write_summary(rows)
    return 0 if rows else 1


def write_summary(rows: list[dict]) -> None:
    from collections import Counter
    out = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.md")
    types = Counter(p["dt"] for r in rows for p in r["parts"])
    counts = sorted(len(r["parts"]) for r in rows)
    lines = ["# JC3 parts tables — decoded fleet-wide", "",
             "Generated by `Tools/scripts/jc3parts.py build` with `Tools/scripts/jc3adf.py`.",
             "Do not edit by hand.", "",
             f"* entities decoded: **{len(rows)}**",
             f"* parts: **{sum(len(r['parts']) for r in rows)}** "
             f"(per entity {counts[0]} … {counts[-1]}, median {counts[len(counts) // 2]})",
             f"* damage types used: **{len(types)}**", "",
             "## Damage types across the fleet", "",
             "| type | parts |", "|---|---|"]
    for name, n in types.most_common():
        lines.append(f"| `{name}` | {n} |")
    lines += ["", "## Parts per vehicle (first 25)", "",
              "| entity | parts | types |", "|---|---|---|"]
    for r in rows[:25]:
        kinds = len({p["dt"] for p in r["parts"]})
        lines.append(f"| `{os.path.basename(os.path.dirname(r['entity']))}` | {len(r['parts'])} | {kinds} |")
    lines += ["", "## Donor — `v0300_car_kensington_sportsmuscle`", "",
              "| i | part | damage type | behavior | body | lights | kids |",
              "|---|---|---|---|---|---|---|"]
    donor = next((r for r in rows if "v0300_car_kensington_sportsmuscle" in r["entity"]), None)
    if donor:
        for p in donor["parts"]:
            lines.append(f"| {p['i']} | `{p['n']}` | `{p['dt']}` | `{p['b'] or '—'}` | "
                         f"{p['body']} | {p['lights']} | {len(p['kids'])} |")
    else:
        lines.append("| — | not in the table | | | | | |")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {os.path.relpath(out, ROOT)}")


def cmd_wiring(a) -> int:
    vals = deform_values()
    parts = deform_parts()
    print(f"parts: {len(parts)} (index -> name, from DeformPoints)")
    for name in ("wheel_indices", "light_indices", "constraint_indices",
                 "non_deformable_parts_indices"):
        idx = deform_list(vals, name)
        resolved = deform_point_parts(vals, idx)
        uniq = sorted({p for _, p, _ in resolved if p})
        print(f"\n{name}: {len(idx)} deform points -> {len(uniq)} parts")
        for i, part, point in resolved:
            print(f"  point {i:3d}  {part:34s} {point}")
    return 0


def cmd_parts(a) -> int:
    epe = epe_parts()
    dp = deform_parts()
    print(f"ENTITIES.md donor parts: {len(epe)}   DeformPoints part indices: {len(dp)}")
    both = sorted(set(epe) & set(dp))
    agree = [i for i in both if epe[i] == dp[i]]
    print(f"indices in both: {len(both)}   agree: {len(agree)}")
    only_epe = sorted(set(epe) - set(dp))
    only_dp = sorted(set(dp) - set(epe))
    if only_epe:
        print(f"in .epe but no deform point ({len(only_epe)}): {[epe[i] for i in only_epe]}")
    if only_dp:
        print(f"deform point but not in .epe ({len(only_dp)}): {[dp[i] for i in only_dp]}")
    print("index  name (both sources)")
    for i in both:
        mark = "" if epe[i] == dp[i] else f"   <-- .epe says {epe[i]}"
        print(f"  {i:3d}  {dp[i]}{mark}")
    return 0


def cmd_check(a) -> int:
    epe = epe_parts()
    dp = deform_parts()
    if not epe or not dp:
        print("parts tables empty")
        return 1
    both = set(epe) & set(dp)
    bad = [i for i in both if epe[i] != dp[i]]
    if bad:
        print(f"disagreement at indices {sorted(bad)}: "
              f"{[(epe[i], dp[i]) for i in sorted(bad)]}")
        return 1
    vals = deform_values()
    wheels = deform_point_parts(vals, deform_list(vals, "wheel_indices"))
    lights = deform_point_parts(vals, deform_list(vals, "light_indices"))
    wheel_parts = {p for _, p, _ in wheels}
    if len(wheel_parts) != len(wheels):
        print(f"wheel points do not map 1:1 to parts: {wheels}")
        return 1
    if not lights or any(p is None for _, p, _ in lights):
        print(f"light points do not resolve to parts: {lights}")
        return 1
    print(f"ok: {len(both)} part indices agree between .epe and DeformPoints; "
          f"{len(wheels)} wheel points -> {len(wheel_parts)} wheel parts; "
          f"{len(lights)} light points -> {len({p for _, p, _ in lights})} parts")
    return check_parts_table(deform_parts(),
                             {p for _, p, _ in lights}, wheel_parts)


def check_parts_table(dp: dict, light_parts: set, wheel_parts: set) -> int:
    """Cross-check the decoded parts table (PARTS_TABLE.jsonl) against the other modules."""
    table = os.path.join(ROOT, "Research", "JC3Grab", "PARTS_TABLE.jsonl")
    if not os.path.exists(table):
        print(f"skip: no {os.path.relpath(table, ROOT)} (run `jc3parts.py build`)")
        return 1
    donor = None
    with open(table, encoding="utf-8") as f:
        for line in f:
            row = json.loads(line)
            if "v0300_car_kensington_sportsmuscle_civilian_01" in row["entity"]:
                donor = row
                break
    if donor is None:
        print("donor not in PARTS_TABLE.jsonl")
        return 1
    parts = donor["parts"]
    bad = []
    if len(parts) != len(dp):
        bad.append(f"part count {len(parts)} != DeformPoints {len(dp)}")
    for p in parts:
        if dp.get(p["i"]) != p["n"]:
            bad.append(f"index {p['i']}: table {p['n']} vs DeformPoints {dp.get(p['i'])}")
    lit = {p["n"] for p in parts if p["lights"]}
    if lit != light_parts:
        bad.append(f"light parts {sorted(lit)} != DeformPoints {sorted(light_parts)}")
    wheel_behavior = {p["n"] for p in parts if p["b"] == "Wheel"}
    if wheel_behavior != wheel_parts:
        bad.append(f"parts with behavior Wheel {sorted(wheel_behavior)} != "
                   f"DeformPoints wheels {sorted(wheel_parts)}")
    with open(CURRENT, encoding="utf-8") as f:
        vals = json.load(f)["modules"]["VehicleDamage"]["values"]
    known = {vals[k] for k in vals if re.match(r"^part_damage_types\[\d+\]\.type\.string$", k)}
    unknown = {p["dt"] for p in parts} - known
    idx = {p["i"] for p in parts}
    stray = [k for p in parts for k in p["kids"] if k not in idx]
    if stray:
        bad.append(f"children outside the part list: {stray[:5]}")
    if bad:
        for b in bad:
            print("  ", b)
        return 1
    print(f"ok: donor table has {len(parts)} parts, names {len(parts)}/{len(dp)} with DeformPoints, "
          f"lights {len(lit)} parts match, wheels {len(wheel_behavior)} match, "
          f"damage types {len({p['dt'] for p in parts})} used")
    if unknown:
        print(f"  note: {sorted(unknown)} not in this vehicle's VehicleDamage table "
              f"({len(known)} types) - the part falls back to Default damage")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("layout", "parts", "check", "wiring", "build"):
        sp = sub.add_parser(name)
        sp.add_argument("--raw", default=RAW)
        if name == "build":
            sp.add_argument("--limit", type=int, default=0)
            sp.add_argument("--only", default=None)
    a = p.parse_args()
    globals()["RAW"] = a.raw
    return {"layout": cmd_layout, "parts": cmd_parts, "check": cmd_check,
            "wiring": cmd_wiring, "build": cmd_build}[a.cmd](a)


if __name__ == "__main__":
    raise SystemExit(main())

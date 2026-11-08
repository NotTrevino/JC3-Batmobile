#!/usr/bin/env python3
"""t_st7.py - is 0.5 s a hard JC3 steering floor, or only the lowest shipped value?

T-ST7 is blocked on the claim that BmAK's `SteerSpeed` 220 deg/s needs 0.25 s to reach
its 55 deg lock, while "the JC3 family floor is 0.5 s".  This tool re-derives both
numbers from the shipped bytes instead of quoting them:

  BmAK  the `RVehicleSimBatmobile` archetype in each `Playable_Batmobile*.upk`:
        the FloatProperty at native offset 0x0DC (the BMSDK table names that offset
        `SVehicleSimCar.SteerSpeed`) and the `StandardSteeringSpeedCurve` points,
        both walked with `upk_read.py`.
  JC3   every land entity's `LandSteering` modules, split into the player module and
        its `_ai` twin (`land_steering_ai.vmodc`), and - wherever the module file is
        on disk - the float at the type member's own declared offset.

The split matters: the two module kinds ship different values for the same car, so a
fleet statistic that pools them is measuring two different consumers.

    python t_st7.py --write    # Working/Translation/T_ST7_FLOOR.{md,json}
    python t_st7.py --check    # recompute every number, compare, fail on any oracle
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import statistics as st
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3adf  # noqa: E402
from upk_read import Package, best_walk  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
RAW = os.environ.get("JC3_RAW", r"E:/Modding/_gamedata/JC3grab")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "T_ST7_FLOOR.md")
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "T_ST7_FLOOR.json")

SKIP = ("Cine_", "Death_", "Chases_Gen_")
STEER_OFFSET = 0x0DC          # BMSDK: SVehicleSimCar.SteerSpeed, offset 220
MEMBER = "t_to_full_steer_s"

# Module files that are actually unpacked on disk, tried in this order.
RAW_ROOTS = [os.path.join(RAW, p) for p in
             ("b13b/unpacked", "rc_merge/stage", "rc_merge/verify", "")]
TARGET_REL = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
              "modules/default/batmobile/"
              "v0300_car_kensington_sportsmuscle_land_steering.vmodc")


# ----------------------------------------------------------------- BmAK package bytes

def curve_points(tag: dict) -> list[tuple[float, float]]:
    """(x, y) samples out of a decoded FInterpCurveFloat struct."""
    for p in tag.get("props", []):
        if p.get("type") == "ArrayProperty" and "items" in p:
            pts = []
            for item in p["items"]:
                if not isinstance(item, list):
                    continue
                floats = [t.get("value") for t in item if t.get("type") == "FloatProperty"]
                if len(floats) >= 2:
                    pts.append((floats[0], floats[1]))
            if pts:
                return pts
    return []


def curve_knot(pts: list[tuple[float, float]], x: float = 600.0) -> float | None:
    """The steering angle at the 600 cm/s knot: BmAK's angle at driving speed.

    `StandardSteeringSpeedCurve` starts at 60 deg at 0 cm/s and is 55 deg at 600 cm/s.
    The 55 is not the maximum (60 at standstill) and not always a plateau (the Joker
    curve falls to 50 at 1100), so it is read as the 600 cm/s knot - the value
    T-ST7's 0.25 s uses.
    """
    for px, py in pts:
        if px == x:
            return py
    return None


def bmak_archetypes() -> list[dict]:
    out = []
    for path in sorted(glob.glob(os.path.join(GAME, "Playable_Batmobile*.upk"))):
        base = os.path.splitext(os.path.basename(path))[0]
        if any(base.startswith(s) for s in SKIP):
            continue
        pkg = Package(path)
        for i in range(1, pkg.export_count + 1):
            if pkg.object_class(i) != "RVehicleSimBatmobile":
                continue
            tags, end, why = best_walk(pkg, pkg.data(i))
            speeds = [t for t in tags if t["type"] == "FloatProperty"
                      and t["offset"] == STEER_OFFSET]
            curves = [t for t in tags if t.get("name") == "StandardSteeringSpeedCurve"]
            pts = curve_points(curves[0]) if curves else []
            lock = curve_knot(pts)
            speed = speeds[0]["value"] if len(speeds) == 1 else None
            out.append({
                "package": base,
                "export_index": i,
                "export": pkg.exports[i - 1]["name"],
                "export_bytes": pkg.exports[i - 1]["size"],
                "tags": len(tags),
                "walk_end": end,
                "walk_stop": why,
                "steer_speed": speed,
                "steer_speed_tag_at": speeds[0]["at"] if speeds else None,
                "curve_points": [list(p) for p in pts],
                "standstill_deg": pts[0][1] if pts else None,
                "lock_deg": lock,
                "lock_time_s": round(lock / speed, 6) if lock and speed else None,
            })
    return out


# ----------------------------------------------------------------- JC3 module bytes

def fleet() -> list[dict]:
    rows = []
    for path in glob.glob(os.path.join(RAW, "entities", "*.json")):
        doc = json.load(open(path, encoding="utf-8"))
        ent = doc.get("entity", "")
        if "/01_land/" not in ent:
            continue
        for m in doc.get("modules", []):
            if m.get("type") != "LandSteering":
                continue
            vals = {r["path"]: r["value"] for r in m.get("rows", [])}
            rows.append({
                "entity": ent,
                "kind": "ai" if "/ai/" in m.get("file", "") else "player",
                "file": m.get("file", ""),
                "t_to_full": vals.get(MEMBER),
                "max_speed_t_to_full": vals.get("max_speed_t_to_full_steer_s"),
            })
    return rows


def stats(rows: list[dict], key: str) -> dict:
    vals = [r[key] for r in rows if isinstance(r[key], (int, float))]
    pos = sorted(v for v in vals if v > 0)
    counts: dict[float, int] = {}
    for v in pos:
        counts[round(v, 4)] = counts.get(round(v, 4), 0) + 1
    return {
        "n": len(vals),
        "entities": len({r["entity"] for r in rows}),
        "min": pos[0] if pos else None,
        "at_min": sum(1 for v in pos if v == pos[0]) if pos else 0,
        "median": st.median(pos) if pos else None,
        "below_0_5": [round(v, 6) for v in pos if v < 0.5],
        "distinct_bottom": [[k, counts[k]] for k in sorted(counts)[:6]],
    }


def find_raw(rel: str) -> str | None:
    for root in RAW_ROOTS:
        p = os.path.join(root, rel)
        if os.path.exists(p):
            return p
    return None


def module_facts(path: str) -> dict:
    blob = open(path, "rb").read()
    adf = jc3adf.Adf(blob)
    inst = adf.instances[0]
    typ = adf.types[inst["type"]]
    member = next((m for m in typ["members"] if m["name"] == MEMBER), None)
    if member is None:
        return {"file": path, "member": None}
    pos = inst["offset"] + member["offset"]
    raw = blob[pos:pos + 4]
    return {
        "file": path,
        "type": typ["name"],
        "instance_offset": inst["offset"],
        "member_offset": member["offset"],
        "file_offset": pos,
        "hex": raw.hex(),
        "value": struct.unpack("<f", raw)[0],
    }


def raw_checks(rows: list[dict]) -> list[dict]:
    out = []
    seen = set()
    for r in rows:
        if r["file"] in seen:
            continue
        path = find_raw(r["file"])
        if not path:
            continue
        seen.add(r["file"])
        facts = module_facts(path)
        facts["json_value"] = r["t_to_full"]
        facts["kind"] = r["kind"]
        facts["agrees"] = (facts.get("value") is not None
                           and abs(facts["value"] - float(r["t_to_full"])) < 1e-6)
        out.append(facts)
    return out


# ----------------------------------------------------------------- build

def build() -> dict:
    bmak = bmak_archetypes()
    rows = fleet()
    player = [r for r in rows if r["kind"] == "player"]
    ai = [r for r in rows if r["kind"] == "ai"]

    p_main = stats(player, "t_to_full")
    p_aux = stats(player, "max_speed_t_to_full")
    a_main = stats(ai, "t_to_full")
    a_aux = stats(ai, "max_speed_t_to_full")

    raw = raw_checks(rows)
    target_path = find_raw(TARGET_REL)
    target = module_facts(target_path) if target_path else None
    write_hex = struct.pack("<f", 0.25).hex()

    docs = {
        "bmak": bmak,
        "fleet": {
            "player": {"t_to_full": p_main, "max_speed_t_to_full": p_aux},
            "ai": {"t_to_full": a_main, "max_speed_t_to_full": a_aux},
            "mugello_ai_025": sorted({r["entity"] for r in ai
                                      if r["t_to_full"] == 0.25}),
        },
        "raw_modules": raw,
        "target": target,
        "write_hex": write_hex,
        "verdict": {
            "player_min": p_main["min"],
            "ai_min": a_main["min"],
            "player_below_0_5": p_main["below_0_5"],
            "is_engine_clamp": False,
            "kind": ("lowest shipped player value; the AI twin of four Mugello variants "
                     "ships 0.25, so 0.5 is not a data-wide minimum either"),
        },
    }

    def every(key, pred):
        return all(pred(a.get(key)) for a in bmak)

    docs["oracles"] = {
        "bmak_archetypes": {
            "ok": len(bmak) == 4 and all(a["export"] == "SimulationModel" for a in bmak),
            "detail": [f"{a['package']}#{a['export_index']} {a['export']} {a['export_bytes']}B"
                       for a in bmak],
        },
        "bmak_steer_speed_220": {
            "ok": every("steer_speed", lambda v: v == 220.0),
            "detail": [{"package": a["package"], "offset": hex(STEER_OFFSET),
                        "tag_payload_byte": a["steer_speed_tag_at"],
                        "value": a["steer_speed"]} for a in bmak],
        },
        "bmak_lock_55_at_600": {
            "ok": every("lock_deg", lambda v: v == 55.0)
            and every("curve_points", lambda p: p[0] == [0.0, 60.0]),
            "detail": [{"package": a["package"], "points": a["curve_points"],
                        "standstill": a["standstill_deg"], "knot_600": a["lock_deg"]}
                       for a in bmak],
        },
        "lock_time_025": {
            "ok": every("lock_time_s", lambda v: v == 0.25),
            "detail": [a["lock_time_s"] for a in bmak],
        },
        "fleet_player_min_050": {
            "ok": p_main["min"] == 0.5 and not p_main["below_0_5"] and p_main["n"] == 125,
            "detail": {k: p_main[k] for k in ("n", "entities", "min", "at_min", "median")},
        },
        "fleet_ai_counterexample_025": {
            "ok": a_main["min"] == 0.25 and a_main["at_min"] == 4,
            "detail": {k: a_main[k] for k in ("n", "entities", "min", "at_min", "median")},
        },
        "fleet_aux_min": {
            "ok": p_aux["min"] == 0.5 and not p_aux["below_0_5"]
            and abs((a_aux["min"] or 0) - 0.2) < 1e-6,
            "detail": {"player": p_aux["min"], "ai": a_aux["min"],
                       "player_below_0_5": p_aux["below_0_5"]},
        },
        "raw_member_offset_8": {
            "ok": bool(raw) and all(r.get("member_offset") == 8 for r in raw),
            "detail": [{"file": os.path.basename(r["file"]), "member_offset": r["member_offset"],
                        "file_offset": r["file_offset"], "hex": r["hex"]} for r in raw],
        },
        "raw_decode_agrees": {
            # The module copies on disk are a mix: the player copy under b13b reads
            # 0.8 where the entity decode says 1.2, so it is a project build tree,
            # not a shipped anchor.  At least one unmodified copy must agree, and
            # every parsed copy must share the type member offset.
            "ok": bool(raw) and any(r["agrees"] for r in raw)
            and all(r.get("member_offset") == 8 for r in raw),
            "detail": [{"file": os.path.basename(r["file"]), "bytes": r["value"],
                        "json": r["json_value"], "kind": r["kind"],
                        "agrees": r["agrees"]} for r in raw],
        },
        "target_module": {
            "ok": bool(target) and target.get("value") is not None
            and abs(target["value"] - 0.8) < 1e-6 and target.get("member_offset") == 8
            and target.get("hex") == "cdcc4c3f",
            "detail": target,
        },
        "write_bytes_025": {
            "ok": write_hex == "0000803e",
            "detail": {"float": 0.25, "hex": write_hex},
        },
    }
    return docs


# ----------------------------------------------------------------- render

def fnum(v, digits=4):
    if v is None:
        return "—"
    if isinstance(v, int):
        return str(v)
    return f"{v:.{digits}g}"


def render(doc: dict) -> str:
    b = doc["bmak"]
    p, a = doc["fleet"]["player"], doc["fleet"]["ai"]
    pm, pu = p["t_to_full"], p["max_speed_t_to_full"]
    am, au = a["t_to_full"], a["max_speed_t_to_full"]
    tgt = doc["target"]
    L = [
        "# T-ST7 — is 0.5 s a JC3 steering floor?",
        "",
        "Generated by `Tools/scripts/t_st7.py --write`; `--check` re-reads the Batman packages and",
        "the JC3 entity/module bytes, recomputes every number below and fails on any oracle.",
        "",
        "## 1. Verdict",
        "",
        f"**0.5 s is not an engine clamp.** No decoded input contains one, and the claim that the",
        f"fleet bottoms out at 0.5 s is false once the player module and its AI twin are separated:",
        "",
        f"- **player** `LandSteering.t_to_full_steer_s`: n={pm['n']}, min **{fnum(pm['min'])} s**,",
        f"  {pm['at_min']} vehicles at that value, **no value below 0.5 s**.",
        f"- **AI twin** (`*_land_steering_ai.vmodc`): n={am['n']}, min **{fnum(am['min'])} s**,",
        f"  {am['at_min']} modules at 0.25 s (`{'`, `'.join(x.split('/')[-1] for x in doc['fleet']['mugello_ai_025'])}`).",
        "",
        "So the family minimum over *all shipped LandSteering modules* is 0.25 s, and 0.5 s is only",
        "the lowest value any shipped **player** module uses. Whether the player steering update",
        "honours a value below 0.5 s is **UNKNOWN until measured**: nothing in the decoded files",
        "clamps it, and nothing proves it does not. The AI twin is evidence about the member and the",
        "parser, not about the player path.",
        "",
        "BmAK's number is unchanged and reproducibly 0.25 s: a **55°** plateau in",
        "`StandardSteeringSpeedCurve` at a **220 °/s** `SteerSpeed`.",
        "",
        "## 2. BmAK — 220 °/s and the 55° lock, from package bytes",
        "",
        "| package | export | bytes | FloatProperty @0x0DC (value, tag payload byte) | curve points (cm/s → deg) | 55° knot | 55/220 |",
        "|---|---|---:|---|---|---:|---:|",
    ]
    for x in b:
        pts = "  ".join(f"{fnum(x0)}→{fnum(y)}" for x0, y in x["curve_points"])
        L.append(f"| `{x['package']}` | #{x['export_index']} `{x['export']}` | {x['export_bytes']} | "
                 f"{fnum(x['steer_speed'])} @ {x['steer_speed_tag_at']} | {pts} | "
                 f"{fnum(x['lock_deg'])}° | **{fnum(x['lock_time_s'], 3)} s** |")
    L += [
        "",
        "`0x0DC` is the native class offset the BMSDK table names `SVehicleSimCar.SteerSpeed`; the",
        "value at that offset is read from the archetype's own tag stream, so the **220 is decoded**",
        "and only the *name* of the slot is named-sdk. The 55° is the curve's 600 cm/s knot of",
        "`StandardSteeringSpeedCurve`, whose values are degrees of steer angle; reading that curve as",
        "angle-vs-speed (rather than something else) is the derived step, and it is the same reading",
        "T1 already uses for T-ST1.",
        "",
        "The curve starts at **60° at 0 cm/s**; at a standstill 60/220 would be 0.273 s. T-ST7's",
        "0.25 s is the **55° knot at 600 cm/s**, not a plateau: the Joker curve falls to 50° at",
        "1100 cm/s. Both times are shown above so the standstill case is not silently treated as",
        "0.25 s.",
        "",
        "0.25 s is therefore **derived** as `55° ÷ 220 °/s`, exactly, in all four archetypes.",
        "",
        "## 3. JC3 — the fleet, player module vs AI twin",
        "",
        "| module kind | n | entities | min | count at min | median | values below 0.5 | bottom of the distribution |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for label, s in (("player `t_to_full_steer_s`", pm), ("AI `t_to_full_steer_s`", am),
                     ("player `max_speed_t_to_full_steer_s`", pu),
                     ("AI `max_speed_t_to_full_steer_s`", au)):
        bottom = ", ".join(f"{fnum(k)}×{c}" for k, c in s["distinct_bottom"])
        below = ", ".join(fnum(v) for v in s["below_0_5"]) or "none"
        L.append(f"| {label} | {s['n']} | {s['entities']} | {fnum(s['min'])} | {s['at_min']} | "
                 f"{fnum(s['median'])} | {below} | {bottom} |")
    L += [
        "",
        "**Raw cross-check.** Every module parsed with `jc3adf.py` puts `t_to_full_steer_s` at type",
        "offset **+8**, and the unmodified AI copy reads the same 2.0 s as its entity row. The player",
        "copy under `b13b/unpacked` reads 0.8 s where the entity decode says 1.2 s, so that tree is a",
        "project build copy, not a shipped anchor; it is reported in the oracle table rather than",
        "used as evidence. The fleet numbers above therefore rest on the jc3grab entity decode; the",
        "AI copy is the byte-level confirmation that the decode and the member offset agree.",
        "",
        "125 land entities carry a player `LandSteering` module and the same 125 carry an AI twin;",
        "pooling the two (as a single 250-row scan does) mixes a 0.25 from the AI file with a 1.2",
        "from the player file of the same car. The four 0.25 s AI modules are the Mugello vintage",
        "sports variants, whose player module is 1.2 s — a concrete demonstration that the member",
        "and the parser accept 0.25 s, and that the shipped data is not floored at 0.5 s.",
        "",
        "## 4. Why 0.5 s looked like a floor",
        "",
        "The earlier fleet note measured the player module only (n=125, min 0.5, median 1.8), which",
        "is correct for that module, and turned it into \"the JC3 family floor\". It is a **shipped",
        "minimum**, not a clamp: the engine clamp would have to be shown in code or by a probe, and",
        "no decoded file carries one. T-ST3's `max_speed_t_to_full_steer_s` has the same player",
        "minimum (0.5 s) and an AI minimum of 0.2 s.",
        "",
        "## 5. The exact member and offset",
        "",
        f"Target: `{tgt['file'].replace(os.sep, '/')}`",
        "",
        "| quantity | value |",
        "|---|---|",
        f"| ADF type | `{tgt['type']}` |",
        f"| instance offset in file | {tgt['instance_offset']} (0x{tgt['instance_offset']:x}) |",
        f"| member | `{MEMBER}` at **+{tgt['member_offset']} (0x{tgt['member_offset']:02x})** |",
        f"| file byte of the float | **{tgt['file_offset']} (0x{tgt['file_offset']:x})** |",
        f"| current bytes | `{tgt['hex']}` = **{tgt['value']:.9g} s** |",
        f"| bytes for 0.25 s | `{doc['write_hex']}` |",
        "",
        "To revert, write `cdcc4c3f` back at that offset. On the BmAK side the equivalent single",
        "value is the FloatProperty at **0x0DC** in `RVehicleSimBatmobile` (220.0); 110.0 there",
        "would make BmAK 0.5 s at the same 55° lock, if the intent is to slow BmAK rather than",
        "speed JC3 up.",
        "",
        "## 6. What would settle whether <0.5 s works (UNKNOWN until measured)",
        "",
        "1. **One-variable probe**: write `0000803e` (0.25) at the offset above in a single build",
        "   and measure lock-to-lock at standstill against the same car at 0.5 and 0.8. A measured",
        "   0.25 s means the member is honoured; a measured 0.5 s means something clamps.",
        "2. **Code evidence**: a disassembly search of the steering update for a clamp on the",
        "   `t_to_full_steer_s` value. This repo has no such decode (the JC3 side is ADF data only),",
        "   so it is UNKNOWN here.",
        "",
        "Neither is available in this task: the operator banned installs, game launches and builds.",
        "",
        "## 7. Oracles",
        "",
        "| oracle | ok | detail |",
        "|---|---|---|",
    ]
    for name, o in doc["oracles"].items():
        d = json.dumps(o["detail"], default=str)
        if len(d) > 220:
            d = d[:217] + "..."
        L.append(f"| `{name}` | {o['ok']} | `{d}` |")
    L += [
        "",
        "## 8. Sources",
        "",
        "- Batman packages: `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/Playable_Batmobile*.upk`,",
        "  export `SimulationModel` (class `RVehicleSimBatmobile`), read with `Tools/scripts/upk_read.py`.",
        "- Offset name: `Research/BatmobileGrab/BMSDK_OFFSETS.json` (`SVehicleSimCar.SteerSpeed`, offset 220).",
        "- JC3 entities: `E:/Modding/_gamedata/JC3grab/entities/*.json` (grab decode) and the unpacked",
        "  `*_land_steering.vmodc` module bytes, read with `Tools/scripts/jc3adf.py`.",
        "",
    ]
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    doc = build()
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True)
    bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
    for k, v in doc["oracles"].items():
        print(f"{'ok  ' if v['ok'] else 'FAIL'} {k}")

    if args.write:
        os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js + "\n")
        print(f"wrote {OUT_MD}\nwrote {OUT_JSON}")
    else:
        if not os.path.exists(OUT_MD) or not os.path.exists(OUT_JSON):
            print("missing output; run --write")
            return 1
        if open(OUT_MD, encoding="utf-8").read() != md:
            print("FAIL md differs from a fresh recomputation")
            bad.append("md")
        if open(OUT_JSON, encoding="utf-8").read() != js + "\n":
            print("FAIL json differs from a fresh recomputation")
            bad.append("json")
        print("check ok" if not bad else "check FAILED")
    return 0 if not bad else 1


if __name__ == "__main__":
    raise SystemExit(main())

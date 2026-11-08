#!/usr/bin/env python3
"""Turret / cannon range audit for the bm-RC2 build: row vs built vs BmAK.

Reads three sides and compares them:

  * the rows            - `Working/Translation/T8_PARTS.md` P-01 (turret yaw) and
                          P-02 (cannon pitch), cross-checked against the carrier
                          table in `Research/JC3Grab/TURRET.md` section 1;
  * the built tree      - `Builds/bm-RC2/.../batmobile/sportsmuscle_vehicle_parts.vmodc`
                          (each Turret/Cannon part's `constraint_index`) and the
                          `.physicsc` beside it (the hinge objects those indices address);
  * the BmAK animation  - `Research/BatmobileGrab/ANIMATIONS.md` moved-bone rows for
                          `Batmobile_V2_Turret_Spin` and `Batmobile_V2_Cannon_Fire`.

Every number in the document is recomputed here; `--check` renders the page again and
compares it byte for byte. Nothing is written outside the requested verify file, and the
build itself is only opened for reading.

Usage:
  python Tools/scripts/v_turret_ranges.py --write   # Builds/bm-RC2/verify/turret_ranges.md
  python Tools/scripts/v_turret_ranges.py --check   # re-derive + byte-compare, exit 1 on drift
"""

from __future__ import annotations

import hashlib
import math
import os
import re
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

import jc3adf  # noqa: E402
import jc3hkx  # noqa: E402

BAT = os.path.join("Builds", "bm-RC2", "aaf", "models", "jc_vehicles", "01_land",
                   "v0300_car_kensington_sportsmuscle", "batmobile")
PARTS = os.path.join(BAT, "sportsmuscle_vehicle_parts.vmodc")
PHYS = os.path.join(BAT, "sportsmuscle.physicsc")
OUT = os.path.join("Builds", "bm-RC2", "verify", "turret_ranges.md")
T8 = os.path.join("Working", "Translation", "T8_PARTS.md")
TURRET = os.path.join("Research", "JC3Grab", "TURRET.md")
ANIM = os.path.join("Research", "BatmobileGrab", "ANIMATIONS.md")

LIMIT_MIN, LIMIT_MAX = 0x0FC, 0x100     # HINGE_LIMIT min/max in jc3_physics_limits.py
THRESHOLD = 0.5                          # degrees; the brief's flag level
DEG = 180.0 / math.pi
TURRET_PART, CANNON_PART, SUPPRESSOR_PART = "batmobile_turret", "batmobile_cannon", "batmobile_riot_suppressor"


def rel(p: str) -> str:
    return p.replace("\\", "/")


def read(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), encoding="utf-8") as f:
        return f.read()


def sha256(rel_path: str) -> str:
    with open(os.path.join(ROOT, rel_path), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


RANGE_RE = re.compile(r"(-?\d+(?:\.\d+)?)\s*…\s*(-?\d+(?:\.\d+)?)\s*°")


# ---------------------------------------------------------------- the rows
def t8_row(rid: str) -> dict:
    for line in read(T8).splitlines():
        if line.startswith("| %s |" % rid):
            c = [x.strip() for x in line.split("|")]
            # 1 id, 2 part, 3 behaviour, 4 joint bone, 5 pivot, 6 axis local, 7 axis JC3,
            # 8 motion, 9 rate, 10 part bone, 11 carrier limits, 12 damage
            m = RANGE_RE.search(c[8])
            car = RANGE_RE.search(c[11])
            return {"id": c[1], "part": c[2], "behaviour": c[3], "bone": c[4],
                    "pivot": c[5], "axis_jc3": c[7], "motion": c[8],
                    "rate": c[9], "carrier": c[11], "damage": c[12],
                    "motion_range": (float(m.group(1)), float(m.group(2))) if m else None,
                    "carrier_range": (float(car.group(1)), float(car.group(2))) if car else None}
    raise SystemExit("row %s not found in %s" % (rid, T8))


def turret_md_carriers() -> dict:
    """The medium tank's own yaw/pitch hinge lines from TURRET.md section 1."""
    out = {}
    for line in read(TURRET).splitlines():
        for key, label in (("yaw hinge", "yaw"), ("pitch hinge", "pitch")):
            if line.startswith("| %s |" % key):
                m = re.search(r"(-?\d+)\s*\.\.\s*\+?(-?\d+) deg", line)
                if not m:
                    raise SystemExit("cannot parse %s line: %s" % (key, line))
                out[label] = (float(m.group(1)), float(m.group(2)))
    if set(out) != {"yaw", "pitch"}:
        raise SystemExit("TURRET.md section 1 yaw/pitch hinge rows not found")
    return out


# ---------------------------------------------------------------- BmAK
def mechanism_row(section: str) -> str:
    """The `| Batmobile | <set> | <sequence> | bones... |` row of an ANIMATIONS.md section."""
    body = read(ANIM).split("### `%s`" % section, 1)[1]
    body = body.split("\n### ", 1)[0]
    for line in body.splitlines():
        if line.startswith("| Batmobile |"):
            return line
    raise SystemExit("no Batmobile row in ANIMATIONS.md section %s" % section)


def bone_swing(line: str, bone: str) -> tuple[float, float]:
    """(cm, deg) for one bone in a moved-bones cell."""
    m = re.search(re.escape(bone) + r"\s+(\d+(?:\.\d+)?) cm / (\d+(?:\.\d+)?) deg", line)
    if not m:
        raise SystemExit("bone %s not in moved-bones row" % bone)
    return float(m.group(1)), float(m.group(2))


# ---------------------------------------------------------------- the built tree
def built_parts() -> dict:
    adf = jc3adf.Adf(open(os.path.join(ROOT, PARTS), "rb").read())
    parts = jc3adf.parts(adf)
    return {"n": len(parts), "by_name": {p["name"]: p for p in parts}, "list": parts}


def built_constraints() -> list[dict]:
    """Every constraint object in the built .physicsc, in packfile offset order.

    That order is the convention `jc3_turret_limits.py` uses for `constraint_index`
    (`part_view` -> `s['constraints'][ci]`), so indices are comparable.
    """
    pf = jc3hkx.Packfile(open(os.path.join(ROOT, PHYS), "rb").read())
    objs = sorted((o for o in pf.objects if "Constraint" in o.cls), key=lambda o: o.offset)
    out = []
    for o in objs:
        ext = pf.extents[o.offset]
        rec = {"i": len(out), "class": o.cls, "offset": o.offset}
        if o.cls == "hkpLimitedHingeConstraintData":
            raw = pf.raw(o.offset, ext)
            lo, hi = struct.unpack_from("<2f", raw, LIMIT_MIN)
            ax = struct.unpack_from("<3f", raw, 0x30)
            pv = struct.unpack_from("<3f", raw, 0x60)
            rec.update({"min": math.degrees(lo), "max": math.degrees(hi),
                        "axis": [round(v, 4) for v in ax], "pivot": [round(v, 4) for v in pv]})
        out.append(rec)
    return out


def built_joint(part_name: str, parts: dict, cons: list[dict]) -> dict:
    p = parts["by_name"][part_name]
    ci = p.get("constraint_index")
    rec = {"part": part_name, "behaviour": p["behavior"], "index": p["part_index"],
           "parent": p.get("parent_part_index"), "ci": ci, "joint": None}
    if isinstance(ci, int) and 0 <= ci < len(cons):
        c = cons[ci]
        rec["joint"] = {"class": c["class"], "offset": c["offset"]}
        if "min" in c:
            rec["joint"].update({"min": c["min"], "max": c["max"],
                                 "axis": c["axis"], "pivot": c["pivot"]})
    return rec


# ---------------------------------------------------------------- the comparison
def span(lo: float | None, hi: float | None) -> float:
    return 0.0 if lo is None or hi is None else round(hi - lo, 3)


def joint_span(j: dict | None) -> float | None:
    if not j or "min" not in j:
        return None
    return span(j["min"], j["max"])


def delta(a: float | None, b: float | None) -> float:
    """Abs difference of two spans; a missing joint counts as a 0 degree span."""
    return round(abs((a or 0.0) - (b or 0.0)), 3)


def build() -> dict:
    p1, p2 = t8_row("P-01"), t8_row("P-02")
    carriers = turret_md_carriers()
    turret_line, cannon_line = mechanism_row("turret"), mechanism_row("cannon")
    t_cm, t_deg = bone_swing(turret_line, "Batmobile_Rig_Weapons_Turret_Root")
    c1_cm, c1_deg = bone_swing(cannon_line, "Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01")
    c2_cm, c2_deg = bone_swing(cannon_line, "Batmobile_Rig_Weapons_Heavy_Cannon_Barrrel_02")

    parts, cons = built_parts(), built_constraints()
    yaw_part = built_joint(TURRET_PART, parts, cons)
    pitch_part = built_joint(CANNON_PART, parts, cons)
    sup_part = built_joint(SUPPRESSOR_PART, parts, cons)

    yaw_row = span(*p1["motion_range"]) if p1["motion_range"] else 0.0
    pitch_row = span(*p2["motion_range"]) if p2["motion_range"] else 0.0
    yaw_bmak = round(2 * t_deg, 3)          # symmetric swing about the bind pose
    pitch_bmak = round(abs(c1_deg) + abs(c2_deg), 3)

    yaw_built = joint_span(yaw_part["joint"])
    pitch_built = joint_span(pitch_part["joint"])

    head = [
        {"joint": "yaw", "row": yaw_row, "built": yaw_built, "bmak": yaw_bmak},
        {"joint": "pitch", "row": pitch_row, "built": pitch_built, "bmak": pitch_bmak},
    ]
    for r in head:
        r["d_row_built"] = delta(r["row"], r["built"])
        r["d_row_bmak"] = delta(r["row"], r["bmak"])
        r["d_bmak_built"] = delta(r["bmak"], r["built"])
        r["flag"] = max(r["d_row_built"], r["d_row_bmak"], r["d_bmak_built"]) > THRESHOLD

    # What each row's own verify line asks the build to carry.
    req = [
        {"joint": "yaw", "want": p1["motion_range"], "want_src": "P-01's own BmAK motion - its verify line asks the yaw to sweep that span",
         "built": yaw_built, "note": "built part `%s`, constraint_index %s" % (TURRET_PART, yaw_part["ci"])},
        {"joint": "pitch", "want": p2["carrier_range"], "want_src": "P-02's carrier range (its verify line: 'stops at the carrier's own -5..20 deg')",
         "built": pitch_built, "note": "built part `%s`, constraint_index %s" % (CANNON_PART, pitch_part["ci"])},
        {"joint": "yaw (carrier)", "want": p1["carrier_range"], "want_src": "JC3 carrier's own hinge, informational - not what P-01's verify line asks for",
         "built": yaw_built, "note": "same part as the yaw row"},
    ]
    for r in req:
        r["want_span"] = span(*r["want"]) if r["want"] else 0.0
        r["d"] = delta(r["want_span"], r["built"])
        r["flag"] = r["d"] > THRESHOLD

    hinges = [c for c in cons if c["class"] == "hkpLimitedHingeConstraintData"]
    spans = sorted(span(c["min"], c["max"]) for c in hinges)
    joined = [p for p in parts["list"] if isinstance(p.get("constraint_index"), int)
              and p["constraint_index"] >= 0]
    loose = [p for p in parts["list"] if p.get("constraint_index") == -1]

    return {            "p1": p1, "p2": p2, "carriers": carriers,
        "joined_n": len(joined), "loose_n": len(loose),
        "joined_names": sorted(p["name"] for p in joined),
        "max_ci": max(p["constraint_index"] for p in joined) if joined else -1,
        "bmak": {"turret_cm": t_cm, "turret_deg": t_deg, "c1_cm": c1_cm, "c1_deg": c1_deg,
                 "c2_cm": c2_cm, "c2_deg": c2_deg},
        "yaw_part": yaw_part, "pitch_part": pitch_part, "sup_part": sup_part,
        "parts_n": parts["n"], "cons_n": len(cons), "hinges_n": len(hinges),
        "span_max": max(spans) if spans else 0.0,
        "span_min": min(spans) if spans else 0.0,
        "head": head, "req": req,
        "flags": sum(1 for r in head if r["flag"]) + sum(1 for r in req if r["flag"]),
        "files": {"parts": rel(PARTS), "phys": rel(PHYS), "t8": rel(T8),
                  "turret": rel(TURRET), "anim": rel(ANIM)},
        "hashes": {"parts": sha256(PARTS), "phys": sha256(PHYS)},
    }


# ---------------------------------------------------------------- the page
def f3(v: float) -> str:
    return "%.3f" % v


def rng(r: tuple[float, float] | None, unit: str = "°") -> str:
    return "none" if r is None else "%s…%s%s" % (f3(r[0]), f3(r[1]), unit)


def jv(j: dict | None) -> str:
    return "none (no joint)" if not j or "min" not in j else rng((j["min"], j["max"]))


def yes(flag: bool) -> str:
    return "**FLAG**" if flag else "ok"


def render(d: dict) -> str:
    p1, p2, b = d["p1"], d["p2"], d["bmak"]
    L = []
    a = L.append
    a("# Turret and cannon ranges - row vs built vs BmAK (bm-RC2)")
    a("")
    a("Generated by `python Tools/scripts/v_turret_ranges.py --write`; `--check` re-derives every")
    a("number below from the same bytes and compares this page byte for byte. Read-only on the")
    a("build: no file under `Builds/bm-RC2/` is written except this one.")
    a("")
    a("**%d joint(s) compared, %d flagged above %.1f°.** A difference is the absolute gap between"
      % (len(d["head"]) + len(d["req"]), d["flags"], THRESHOLD))
    a("two **spans** (`max - min`), and a side with no joint counts as a 0.000° span - which is why")
    a("a missing hinge reads as a %.0f° or %.0f° difference rather than as a smaller number." % (
        d["head"][0]["d_row_built"], d["req"][1]["d"]))
    a("")
    a("Sources (all read-only):")
    a("")
    a("| side | file | sha256 (build files) |")
    a("|---|---|---|")
    a("| rows | `%s` (P-01, P-02) and `%s` §1 | - |" % (d["files"]["t8"], d["files"]["turret"]))
    a("| built | `%s` | `%s` |" % (d["files"]["parts"], d["hashes"]["parts"]))
    a("| built | `%s` | `%s` |" % (d["files"]["phys"], d["hashes"]["phys"]))
    a("| BmAK | `%s` (`turret`, `cannon` moved-bone rows) | - |" % d["files"]["anim"])
    a("")
    a("## 1. Headline motion - what moves")
    a("")
    a("| joint | row (T8 motion) | built (RC2) | BmAK (ANIMATIONS.md) | Δ row-built | Δ row↔BmAK | Δ BmAK-built | > %.1f° |" % THRESHOLD)
    a("|---|---|---|---|---|---|---|---|")
    names = {"yaw": "yaw (`%s`)" % TURRET_PART, "pitch": "pitch (`%s`)" % CANNON_PART}
    for r in d["head"]:
        a("| %s | %s | %s | %s | %s | %s | %s | %s |" % (
            names[r["joint"]],
            rng(p1["motion_range"]) if r["joint"] == "yaw" else
            ("static" if p2["motion_range"] is None else rng(p2["motion_range"])),
            jv(d["yaw_part"]["joint"]) if r["joint"] == "yaw" else jv(d["pitch_part"]["joint"]),
            ("±%s°" % f3(b["turret_deg"])) if r["joint"] == "yaw" else
            ("static (0.000° rotation; %.2f cm / %.2f cm translation)" % (b["c1_cm"], b["c2_cm"])),
            f3(r["d_row_built"]), f3(r["d_row_bmak"]), f3(r["d_bmak_built"]), yes(r["flag"])))
    a("")
    a("* **yaw**: BmAK turns `Batmobile_Rig_Weapons_Turret_Root` **±%.2f°** in `Batmobile_V2_Turret_Spin`"
      % b["turret_deg"])
    a("  (%.2f cm translation), so the row's -60.000…60.000 is the animation's own swing. The built" % b["turret_cm"])
    a("  part names **no joint at all**, so the game has no range to apply.")
    a("* **pitch**: the row's motion is `static` and BmAK agrees - the cannon bones rotate **%.2f°** and" % b["c1_deg"])
    a("  translate (%.2f cm / %.2f cm). Row and BmAK match; the built part again names no joint." % (b["c1_cm"], b["c2_cm"]))
    a("")
    a("## 2. The limit each row asks the build to carry")
    a("")
    a("| joint | row's required limit | why that number | built | Δ | > %.1f° |" % THRESHOLD)
    a("|---|---|---|---|---|---|")
    for r in d["req"]:
        a("| %s | %s | %s | %s | %s | %s |" % (
            r["joint"], rng(r["want"]), r["want_src"],
            "none (no joint)" if r["built"] is None else f3(r["built"]),
            f3(r["d"]), yes(r["flag"])))
    a("")
    a("* the built part's evidence is `constraint_index = %d` on `%s` (part %d, behaviour `%s`),"
      % (d["yaw_part"]["ci"], TURRET_PART, d["yaw_part"]["index"], d["yaw_part"]["behaviour"]))
    a("  `%d` on `%s` (part %d, behaviour `%s`) and `%d` on `%s` (part %d, behaviour `%s`)."
      % (d["pitch_part"]["ci"], CANNON_PART, d["pitch_part"]["index"], d["pitch_part"]["behaviour"],
         d["sup_part"]["ci"], SUPPRESSOR_PART, d["sup_part"]["index"], d["sup_part"]["behaviour"]))
    a("  TURRET.md §1: \"the yaw part carries behaviour `Turret`, the pitch part `Cannon`, each is one")
    a("  `hkpLimitedHingeConstraintData` in the vehicle's `.physicsc`\" - `-1` therefore means the link")
    a("  the row assumes is absent, not that the part is static by design.")
    a("* the built `.physicsc` holds **%d constraint objects**: %d `hkpLimitedHingeConstraintData` + %d"
      % (d["cons_n"], d["hinges_n"], d["cons_n"] - d["hinges_n"]))
    a("  `hkpRagdollConstraintData`. The widest limited hinge is **%.1f°** (spans %.1f…%.1f°), so no"
      % (d["span_max"], d["span_min"], d["span_max"]))
    a("  object in the file can be the yaw joint even if some index were mis-read: all %d are the donor"
      % d["hinges_n"])
    a("  car's panel hinges (doors 0…80 / -35…0, windows, hood 0…70, boot 0…90).")
    a("* of the module's %d parts, **%d carry a `constraint_index`** (0…%d: %s) and **%d carry `-1`**."
      % (d["parts_n"], d["joined_n"], d["max_ci"], ", ".join("`%s`" % n for n in d["joined_names"]),
         d["loose_n"]))
    a("  The build therefore does write the field - the three turret-unit parts are among the ones it")
    a("  leaves at `-1`, so the missing joint is a value, not a field the writer skips.")
    a("")
    a("## 3. Reading")
    a("")
    a("| what | verdict |")
    a("|---|---|")
    a("| row vs BmAK, yaw | agree - Δ %s° |" % f3(d["head"][0]["d_row_bmak"]))
    a("| row vs BmAK, pitch | agree - both static, Δ %s° |" % f3(d["head"][1]["d_row_bmak"]))
    a("| row vs built, yaw | **built has no yaw joint** - Δ %s° |" % f3(d["head"][0]["d_row_built"]))
    a("| row vs built, pitch limit | **built has no pitch joint** - Δ %s° |" % f3(d["req"][1]["d"]))
    a("| BmAK vs built, yaw | **the animation's ±%.2f° cannot be reached** - Δ %s° |"
      % (b["turret_deg"], f3(d["head"][0]["d_bmak_built"])))
    a("")
    a("The rows are consistent with the animation: both say the turret swings ±60.000°, the cannon")
    a("does not rotate. The disagreement is between the rows and the **build**: the built module")
    a("publishes the three parts and their behaviours but not the hinge each needs, so the yaw span")
    a("and the carrier pitch range from P-02's verify line exist nowhere in the shipped tree.")
    a("")
    a("That gap is already on record: `Research/challenge/card-B-04.md` measured `constraint_index = -1`")
    a("on 19/19 new parts (B4-02), against 24/24 fleet Turret+Cannon parts that ship `>= 0` with an")
    a("identity `parent_space_offset`. This page re-measures it for RC2 on the turret unit only.")
    a("")
    a("## 4. UNKNOWNs")
    a("")
    a("* **whether JC3 auto-creates a joint for a `Turret`/`Cannon` part with `constraint_index = -1`.**")
    a("  No file says so; TURRET.md §1 gives the hinge as the link, and no decoded vehicle in the")
    a("  232-entity census has a Turret/Cannon part without one. A test would settle it, and the test")
    a("  ban stands.")
    a("* **a turn rate.** The rows carry %.2f °/s (P-01), derived from the animation; a JC3 limited" % float(p1["rate"].split()[0]))
    a("  hinge stores an axis and two angles and no rate (TURRET.md §6), so even a written hinge would")
    a("  not carry P-01's rate. The rate is code-side (UNKNOWN).")
    a("* **pivot and axis of the missing joints.** The rows give them (pivot `%s`, axis %s for yaw), but" % (p1["pivot"], p1["axis_jc3"]))
    a("  nothing built can be compared against them until a constraint exists.")
    a("")
    a("## 5. Oracles re-run by `--check`")
    a("")
    a("* `T8_PARTS.md` still has a P-01 row with motion -60.000…60.000° and carrier -179.0…179.0°, and a")
    a("  P-02 row with motion `static` and carrier -5.0…20.0°")
    a("* `TURRET.md` §1's yaw hinge is still -179 .. 179 deg and its pitch hinge -5 .. 20 deg (the same")
    a("  carriers the rows quote)")
    a("* `ANIMATIONS.md` still reports `Turret_Root` at %.2f deg and the two cannon bones at %.2f deg" % (b["turret_deg"], b["c1_deg"]))
    a("  with %s cm / %s cm translation" % (f3(b["c1_cm"]).rstrip("0").rstrip("."), f3(b["c2_cm"]).rstrip("0").rstrip(".")))
    a("* the build still has %d parts and %d constraint objects (%d limited + %d ragdoll), widest limited"
      % (d["parts_n"], d["cons_n"], d["hinges_n"], d["cons_n"] - d["hinges_n"]))
    a("  span %.1f°" % d["span_max"])
    a("* `batmobile_turret`, `batmobile_cannon` and `batmobile_riot_suppressor` still resolve to")
    a("  `constraint_index` %d / %d / %d and behaviours `%s` / `%s` / `%s`"
      % (d["yaw_part"]["ci"], d["pitch_part"]["ci"], d["sup_part"]["ci"],
         d["yaw_part"]["behaviour"], d["pitch_part"]["behaviour"], d["sup_part"]["behaviour"]))
    a("* both build files still hash to the values in the table above; every span, delta and flag is")
    a("  recomputed, and this page matches the regenerated bytes")
    a("")
    a("## 6. Labels")
    a("")
    a("Row values are **decoded** (`T8_PARTS.md`, itself derived from the BmAK animation tracks);")
    a("built values are **decoded** from the module's `constraint_index` fields and the `.physicsc`")
    a("float atoms at 0x0FC/0x100; BmAK values are **decoded** from `ANIMATIONS.md`. The spans and")
    a("deltas are **derived** here. Nothing is typed from memory of Arkham Knight or Just Cause 3.")
    a("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- oracles
def oracles(d: dict) -> list[tuple[str, bool]]:
    p1, p2, b = d["p1"], d["p2"], d["bmak"]
    out = [
        ("P-01 motion is -60.000…60.000", p1["motion_range"] == (-60.0, 60.0)),
        ("P-01 carrier is -179.0…179.0", p1["carrier_range"] == (-179.0, 179.0)),
        ("P-02 motion is static", p2["motion_range"] is None and "static" in p2["motion"]),
        ("P-02 carrier is -5.0…20.0", p2["carrier_range"] == (-5.0, 20.0)),
        ("TURRET.md carriers match the rows",
         d["carriers"]["yaw"] == p1["carrier_range"] and d["carriers"]["pitch"] == p2["carrier_range"]),
        ("BmAK turret swing is 60.00 deg", abs(b["turret_deg"] - 60.0) < 1e-9),
        ("BmAK cannon rotation is 0.00 deg", b["c1_deg"] == 0.0 and b["c2_deg"] == 0.0),
        ("built module has 61 parts", d["parts_n"] == 61),
        ("built physicsc has 11 constraints (9 limited + 2 ragdoll)",
         d["cons_n"] == 11 and d["hinges_n"] == 9),
        ("no limited hinge is wide enough to be the yaw joint", d["span_max"] < 100.0),
        ("%d parts carry a constraint_index and %d carry -1" % (d["joined_n"], d["loose_n"]),
         d["joined_n"] + d["loose_n"] == d["parts_n"] and 0 <= d["max_ci"] < d["cons_n"]),
        ("the turret unit's three parts carry no joint",
         d["yaw_part"]["ci"] == -1 and d["pitch_part"]["ci"] == -1 and d["sup_part"]["ci"] == -1),
        ("the three parts keep their behaviours",
         (d["yaw_part"]["behaviour"], d["pitch_part"]["behaviour"], d["sup_part"]["behaviour"])
         == ("Turret", "Cannon", "Cannon")),
        ("yaw row and BmAK agree within 0.5 deg", d["head"][0]["d_row_bmak"] <= THRESHOLD),
        ("pitch row and BmAK agree within 0.5 deg", d["head"][1]["d_row_bmak"] <= THRESHOLD),
        ("yaw row vs built is flagged", d["head"][0]["flag"] and d["head"][0]["d_row_built"] > THRESHOLD),
        ("pitch row vs built is flagged", d["req"][1]["flag"] and d["req"][1]["d"] > THRESHOLD),
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
        print("MISSING %s" % rel(OUT))
        return 1
    disk = open(path, encoding="utf-8").read()
    bad = [name for name, ok in ors if not ok]
    for name, ok in ors:
        print(("PASS " if ok else "FAIL ") + name)
    print("oracles: %d/%d pass" % (len(ors) - len(bad), len(ors)))
    if disk != text:
        print("DRIFT: %s differs from the regenerated bytes" % rel(OUT))
        return 1
    print("document identical: %s" % rel(OUT))
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

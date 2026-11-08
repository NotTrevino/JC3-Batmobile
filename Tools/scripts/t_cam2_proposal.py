"""t_cam2_proposal.py - settle the T-CAM2 contradiction and emit the corrected row.

`Working/Translation/MODES_HUD_EVIDENCE.md` flags T6's T-CAM2 for a clause its own
numbers contradict: the row ships `FOV [55,63]` v (= 85 h and 95 h at 16:9) and at the
same time says "68 only if the +10 speed bonus is folded in; **95 boost is a gap**".

This tool reads the cited bytes - `Research/BatmobileGrab/CAMERA.json` (the decoded BmAK
values), `Research/BatmobileGrab/CAMERA.md` (the prose the clause came from), the donor
ADF `car_base.ctunec` and the built `Builds/test-091/.../bat_base.ctunec` (the two floats
the row ships) - recomputes every conversion, and writes
`Working/Translation/T_CAM2_PROPOSAL.md`. It never edits T6.

    python Tools/scripts/t_cam2_proposal.py --write   # emit the proposal
    python Tools/scripts/t_cam2_proposal.py --check   # recompute everything, compare

`--check` re-reads every byte the proposal quotes, recomputes the four conversions, and
requires the emitted file to equal a fresh render; it also fails if T6's T-CAM2 row was
edited (the proposal is the change, not the row).
"""
from __future__ import annotations

import argparse
import math
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

CAM_JSON = os.path.join(ROOT, "Research/BatmobileGrab/CAMERA.json")
CAM_MD = os.path.join(ROOT, "Research/BatmobileGrab/CAMERA.md")
CAM_TUNE = os.path.join(ROOT, "Working/Camera/CAM_TUNE.json")
T6 = os.path.join(ROOT, "Working/Translation/T6_HUD_CAMERA.md")
DONOR = os.path.join(
    ROOT, "Working/Audio/jc3cam/editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec")
BUILT = os.path.join(
    ROOT, "Builds/test-091/aaf/editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec")
OUT = os.path.join(ROOT, "Working/Translation/T_CAM2_PROPOSAL.md")

# T6_HUD_CAMERA.md:127, as it stands (the proposal is a *proposal*: the row is not edited).
ORIGINAL_ROW = (
    "| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 | "
    "`FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9) | "
    "30…55° v | `FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; "
    "**95 boost is a gap** | decoded | wide chase, no fisheye |")

PROPOSED_ROW_TMPL = (
    "| T-CAM2 | `DrivingCamFOV` 85 **h**, `BoostingCamFOV` 95 **h**, `MaxExtraFOV` 10 **h** | "
    "`FOV [30,55]` over `FOVVelocityRange [5,50]` | UE3 horizontal → JC3 vertical (16:9): "
    "85 h → {c85} v, 95 h → {c95} v | 30…55° v | `FOV [55,63]` v = rest 55 (85 h) → top 63 "
    "(95 h); 95 = 85 + 10, so 63 is the boost value **and** the +10 bonus at once — the only "
    "state one JC3 band cannot express is boost **at** speed, 95 + 10 = 105 h = **{c105}** v "
    "(not 68) | derived | wide chase, no fisheye |")


def proposed_row(c: dict) -> str:
    return PROPOSED_ROW_TMPL.format(c85=f"{c['85']:.2f}", c95=f"{c['95']:.2f}",
                                    c105=f"{c['105']:.2f}")

# ADF member offsets, from `bmak_camfile.py` `member_offset()` (recorded in CAM_TUNE.json).
OFF_RANGE0, OFF_RANGE1, OFF_FOV0, OFF_FOV1 = 316, 320, 324, 328


def h2v(h: float, aspect_w: float = 16.0, aspect_h: float = 9.0) -> float:
    """UE3 horizontal FOV -> vertical FOV for an aspect_w:aspect_h screen, in degrees."""
    return 2.0 * math.degrees(math.atan(math.tan(math.radians(h) / 2.0) * aspect_h / aspect_w))


def v2h(v: float, aspect_w: float = 16.0, aspect_h: float = 9.0) -> float:
    return 2.0 * math.degrees(math.atan(math.tan(math.radians(v) / 2.0) * aspect_w / aspect_h))


def blob(path: str) -> bytes:
    with open(path, "rb") as fh:
        return fh.read()


def locate(path: str, needle: str) -> dict:
    """Byte offset and 1-based line of the first occurrence of `needle`."""
    text = blob(path)
    off = text.find(needle.encode("utf-8"))
    if off < 0:
        raise SystemExit(f"{path}: {needle!r} not found")
    return {"path": path, "needle": needle, "offset": off,
            "line": text[:off].count(b"\n") + 1}


def f32(path: str, off: int) -> dict:
    raw = blob(path)[off:off + 4]
    if len(raw) != 4:
        raise SystemExit(f"{path}: short read at {off}")
    return {"path": path, "offset": off, "hex": raw.hex(" "),
            "value": struct.unpack("<f", raw)[0]}


def facts() -> dict:
    cam = blob(CAM_JSON)
    tune = blob(CAM_TUNE)

    values = {}
    for name in ("DrivingCamFOV1", "BoostingCamFOV1", "DrivingCamMaxExtraFOV1"):
        m = locate(CAM_JSON, f'"{name}": ')
        end = cam.index(b",", m["offset"])
        literal = cam[m["offset"]:end].decode()
        values[name] = {
            "literal": literal,
            "offset": m["offset"],
            "line": m["line"],
            "value": float(literal.split(": ")[1]),
        }

    tune_offsets = {
        "FOV[0]": OFF_FOV0, "FOV[1]": OFF_FOV1,
        "FOVVelocityRange[0]": OFF_RANGE0, "FOVVelocityRange[1]": OFF_RANGE1,
    }
    donor = {k: f32(DONOR, v) for k, v in tune_offsets.items()}
    built = {k: f32(BUILT, v) for k, v in tune_offsets.items()}

    edits = {}
    for name in ("FOV[0]", "FOV[1]"):
        m = locate(CAM_TUNE, f'"path": "{name}"')
        edits[name] = {"line": m["line"], "offset": m["offset"]}
    rb = tune.decode("utf-8")
    edits["readback_literal"] = {
        "line": rb[:rb.index('"readback": 55.0')].count("\n") + 1,
        "text": '"readback": 55.0' if '"readback": 55.0' in rb else "",
    }

    prose = {
        "sixty_eight": locate(CAM_MD, "95+10 h → 68.4 v"),
        "convert_85": locate(CAM_MD, "85 h → 54.5 v"),
        "convert_95": locate(CAM_MD, "95 h → 63.1 v"),
        "one_band": locate(CAM_MD, "min/max pair over speed"),
        "h_units": locate(CAM_MD, "The `85`/`95` values are UE3 horizontal FOV"),
    }

    t6 = blob(T6).decode("utf-8")
    row_line = next((i + 1 for i, ln in enumerate(t6.splitlines()) if ln.startswith("| T-CAM2 |")), 0)
    row = t6.splitlines()[row_line - 1] if row_line else ""

    h = {k: v["value"] for k, v in values.items()}
    return {
        "values": values,
        "donor": donor,
        "built": built,
        "edits": edits,
        "prose": prose,
        "t6_line": row_line,
        "t6_row": row,
        "conv": {
            "85": h2v(h["DrivingCamFOV1"]),
            "95": h2v(h["BoostingCamFOV1"]),
            "105": h2v(h["BoostingCamFOV1"] + h["DrivingCamMaxExtraFOV1"]),
            "100": h2v(100.0),
            "95_16x10": h2v(h["BoostingCamFOV1"], 16.0, 10.0),
            "v55_as_h": v2h(55.0),
            "v63_as_h": v2h(63.0),
        },
        "sum": h["DrivingCamFOV1"] + h["DrivingCamMaxExtraFOV1"],
    }


def render(f: dict) -> str:
    v = f["values"]
    c = f["conv"]
    d, b = f["donor"], f["built"]
    p = f["prose"]
    rel = lambda path: os.path.relpath(path, ROOT).replace("\\", "/")  # noqa: E731

    return f"""# T-CAM2 — corrected row, with the bytes behind it

**Verdict: the numbers are right, the clause is wrong.** The row ships `FOV [55,63]` v and
every byte that produces it agrees: 85 h → {c['85']:.2f} v and 95 h → {c['95']:.2f} v, rounded to
55/63, and those two floats sit in the built tune. The two clauses do not survive their own
arithmetic: folding the +10 in gives 95+10 = 105 h = **{c['105']:.2f} v**, not 68, and the
"95 boost is a gap" claim is refuted by the 63 the same cell ships, because 63 *is* 95 h.
The one unrepresented state is boost **at** speed (105 h = 72.49 v), not boost.

This file is a proposal. `T6_HUD_CAMERA.md:{f['t6_line']}` was **not** edited.

## 1. The numbers hold — 85 h and 95 h at 16:9 are exactly 55 and 63

The conversion the row names in its transform column, applied to its own inputs:

| horizontal (BmAK, `CAMERA.json`) | 16:9 vertical | shipped |
|---|---:|---:|
| 85 `DrivingCamFOV1` | {c['85']:.2f} | 55 |
| 95 `BoostingCamFOV1` | {c['95']:.2f} | 63 |
| 105 = 95 + 10 `DrivingCamMaxExtraFOV1` | {c['105']:.2f} | — |
| 100 (for reference) | {c['100']:.2f} | — |

Both shipped values are inside 0.5° of their source: 55 is {55.0 - c['85']:.2f}° above
{c['85']:.2f}, 63 is {c['95'] - 63.0:.2f}° below {c['95']:.2f}; the band is rounded inward by
under half a degree. Back-converted, 55 v = {c['v55_as_h']:.2f} h and 63 v = {c['v63_as_h']:.2f} h,
i.e. the pair is the 85/95 pair and nothing else.

The bytes are in three places and they agree:

* `Research/BatmobileGrab/CAMERA.json` — `{v['DrivingCamFOV1']['literal']}` at byte
  {v['DrivingCamFOV1']['offset']} (line {v['DrivingCamFOV1']['line']}),
  `{v['BoostingCamFOV1']['literal']}` at byte {v['BoostingCamFOV1']['offset']} (line
  {v['BoostingCamFOV1']['line']}), `{v['DrivingCamMaxExtraFOV1']['literal']}` at byte
  {v['DrivingCamMaxExtraFOV1']['offset']} (line {v['DrivingCamMaxExtraFOV1']['line']}). Those are the
  decoded `R3rdPersonCamera` values; `bmak_camera.py --check` re-reads all 33 from `BmGame.upk`.
* `{rel(DONOR)}` (the donor tune the row replaces) — the `FOV` pair is the row's "now"
  column: offset {d['FOV[0]']['offset']} = `{d['FOV[0]']['hex']}` = {d['FOV[0]']['value']:.1f},
  offset {d['FOV[1]']['offset']} = `{d['FOV[1]']['hex']}` = {d['FOV[1]']['value']:.1f}. That is
  "30…55° v", verbatim.
* `{rel(BUILT)}` (test-091, the build the row records) — offset {b['FOV[0]']['offset']} =
  `{b['FOV[0]']['hex']}` = {b['FOV[0]']['value']:.1f}, offset {b['FOV[1]']['offset']} =
  `{b['FOV[1]']['hex']}` = {b['FOV[1]']['value']:.1f}. `{b['FOVVelocityRange[1]']['hex']}` at
  {b['FOVVelocityRange[1]']['offset']} = {b['FOVVelocityRange[1]']['value']:.1f} km/h is the speed
  top T-CAM3 pairs with it. `Working/Camera/CAM_TUNE.json` records both edits (`FOV[0]` at
  line {f['edits']['FOV[0]']['line']}, `FOV[1]` at line {f['edits']['FOV[1]']['line']}, readback
  55.0 / 63.0).

## 2. The clause does not — 68 is not the 16:9 image of any of these values

The clause is inherited from `Research/BatmobileGrab/CAMERA.md`, line
{p['sixty_eight']['line']}: "**85 h → 54.5 v**, **95 h → 63.1 v**, and **95+10 h → 68.4 v**".
Its first two terms are the row's numbers (correct); the third does not follow from its own
formula:

```
95 + 10 = 105 h at 16:9  ->  {c['105']:.2f} v     <- the formula's answer
100 h                    ->  {c['100']:.2f} v     <- 68 is this, at 16:9
 95 h at 16:9            ->  {c['95']:.2f} v      <- the shipped 63
 95 h at 16:10           ->  {c['95_16x10']:.2f} v     <- where 68.4 comes from
```

So "68" is either ~100 h at 16:9 ({c['100']:.2f}) or 95 h on a 16:10 screen
({c['95_16x10']:.2f}) - a stray aspect ratio, not the +10 bonus. A reader who folds the +10 in
on the strength of that note targets 68 and lands **{c['105'] - 68.0:.1f}° narrow**; the 16:9
number is {c['105']:.2f}.

The second half fails differently. "95 boost is a gap" says a state has no JC3 member, yet the
same cell ships its value: 63 is 95 h at 16:9, and 63 is what the built tune carries. The
boost FOV is expressed, so there is no boost gap. `CAMERA.md` line {p['one_band']['line']} gives
the reason a *second* value would be hard - "JC3's `FOV` is a min/max pair over speed, not a
per-state value" - and the ADF agrees: `FOV[0]`/`FOV[1]` at {OFF_FOV0}/{OFF_FOV1} are bounded by
`FOVVelocityRange` at {OFF_RANGE0}/{OFF_RANGE1}. That argument rules out a *fourth* step
(boost at speed), which is the real gap; it cannot also rule out the boost value, because the
row already spends its top of band on it.

## 3. Why 63 is safe under either attribution

`DrivingCamMaxExtraFOV` is added to the driving FOV, and 85 + 10 = {f['sum']:.0f} = the boost FOV.
The two readings of the top of the band therefore coincide *numerically*:

| reading | value | 16:9 vertical |
|---|---:|---:|
| normal drive + the 10° speed bonus | 85 + 10 = 95 h | {c['95']:.2f} |
| boost | 95 h | {c['95']:.2f} |
| boost + the 10° speed bonus | 95 + 10 = 105 h | {c['105']:.2f} |

The shipped 63 is right whichever of the first two the tune was aiming at; only the third is
missing. That is why the row can drop "95 boost is a gap" without moving a single byte - the
build is correct and stays untouched.

## 4. Corrected row (paste-ready, one line, 9 columns)

```
{proposed_row(c)}
```

What changed, cell by cell:

| cell | before | after | why |
|---|---|---|---|
| BmAK source | `MaxExtraFOV` 10 | `MaxExtraFOV` 10 **h** | same unit as the two FOVs it is added to (`CAMERA.md`, line {p['h_units']['line']}) |
| transform | "UE3 horizontal → JC3 vertical (16:9)" | same, plus both conversions | the two numbers are now checkable in the cell |
| proposed | "`FOV [55,63]` v; 68 only if the +10 speed bonus is folded in; **95 boost is a gap**" | "`FOV [55,63]` v = rest 55 (85 h) → top 63 (95 h); 95 = 85 + 10, so 63 is the boost value **and** the +10 bonus at once — the only state one JC3 band cannot express is boost **at** speed, 95 + 10 = 105 h = **72.49** v (not 68)" | drops the refuted 68 and the false boost gap; names the real gap |
| conf | `decoded` | `derived` | the value is a unit conversion plus a 0.5° inward rounding, not a decoded number (`review-CAM-1.md` §5, suggested fix 4). This is the one cell that is not a contradiction fix - drop it if the operator wants only the clause corrected |

Nothing else in the row changes: the JC3 target (`FOV`/`FOVVelocityRange`), the "now" column
(30…55 v, the donor bytes above), the verify cell and T-CAM3's 108 km/h are all untouched.

## 5. What this proposal does not touch

* `T6_HUD_CAMERA.md` — the row still reads exactly as quoted in §6; applying the change is the
  operator's edit.
* `Builds/test-091` and the tune — the FOV bytes are already right; no rebuild.
* `Research/BatmobileGrab/CAMERA.md` — the 68.4 sentence is still there (that file is another
  task's input). If this proposal is accepted, that line should carry the same correction, or
  the row will re-inherit it.
* The A15 camera drive — still pending, and this does not substitute for it: nothing here was
  observed in a game (test ban).

## 6. The row as it stands today

`T6_HUD_CAMERA.md`, line {f['t6_line']}:

```
{f['t6_row']}
```

`--check` asserts that line is unchanged, so a later edit of the row fails this tool instead of
silently rotating the proposal.

## 7. UNKNOWNs

* **Which of the two coincident readings the tune was aiming at.** 85 + 10 = 95 = the boost
  value, and the ADF carries one `FOV` pair with no per-state attribution; the number is the
  same either way, so nothing is guessed here - the row simply stops claiming a distinction
  the file does not make.
* **Whether JC3 recomputes the vertical FOV from the screen aspect at runtime.** The 55/63 are
  correct for 16:9 (`CAMERA.md` §2a's own scope). A 21:9 screen would widen the horizontal
  view; no file read here reports JC3's behaviour, and no game was run (test ban).
* **Whether 105 h should ever be built.** If the boost-at-speed state matters, it needs a
  second carrier (a per-state camera), which no byte here supplies - recorded as a gap, not
  filled.

## 8. Checks

`python Tools/scripts/t_cam2_proposal.py --check` re-reads every byte quoted above and
recomputes every number, including the 16:10 reconstruction of 68.4 and the equality
85 + 10 = 95. It also regenerates this file and requires it to match.
"""


def ok(cond: bool, label: str, detail: str = "") -> bool:
    print(f"{'PASS' if cond else 'FAIL'} {label}" + (f" [{detail}]" if detail and not cond else ""))
    return cond


def check(f: dict) -> int:
    c, v, d, b = f["conv"], f["values"], f["donor"], f["built"]
    good = True

    good &= ok(v["DrivingCamFOV1"]["value"] == 85.0,
               "CAMERA.json DrivingCamFOV1 is 85 h at its byte offset",
               v["DrivingCamFOV1"]["literal"])
    good &= ok(v["BoostingCamFOV1"]["value"] == 95.0,
               "CAMERA.json BoostingCamFOV1 is 95 h at its byte offset",
               v["BoostingCamFOV1"]["literal"])
    good &= ok(v["DrivingCamMaxExtraFOV1"]["value"] == 10.0,
               "CAMERA.json DrivingCamMaxExtraFOV1 is 10 h at its byte offset",
               v["DrivingCamMaxExtraFOV1"]["literal"])
    good &= ok(f["sum"] == 95.0, "85 + 10 = 95: the bonus lands exactly on the boost FOV",
               str(f["sum"]))

    good &= ok(abs(c["85"] - 54.54) < 0.02, f"85 h -> {c['85']:.2f} v, rounds to 55")
    good &= ok(abs(c["95"] - 63.08) < 0.02, f"95 h -> {c['95']:.2f} v, rounds to 63")
    good &= ok(abs(c["105"] - 72.49) < 0.03,
               f"95 + 10 = 105 h -> {c['105']:.2f} v, which is not 68")
    good &= ok(abs(c["100"] - 67.68) < 0.03,
               f"68 v is the 16:9 vertical of ~100 h ({c['100']:.2f}), not of any cited value")
    good &= ok(abs(c["95_16x10"] - 68.60) < 0.03,
               f"95 h at 16:10 -> {c['95_16x10']:.2f} v: where the 68.4 in CAMERA.md came from")
    good &= ok(55.0 > c["85"] and 63.0 < c["95"],
               f"the band is rounded inward ({c['85']:.2f} < 55, 63 < {c['95']:.2f})")
    good &= ok(abs(c["v63_as_h"] - 95.0) < 0.2,
               f"63 v back-converts to {c['v63_as_h']:.2f} h, i.e. the boost FOV")

    good &= ok((d["FOV[0]"]["hex"], d["FOV[0]"]["value"]) == ("00 00 f0 41", 30.0),
               "donor FOV[0] at 324 is float32 30.0 (the row's 'now')",
               d["FOV[0]"]["hex"])
    good &= ok((d["FOV[1]"]["hex"], d["FOV[1]"]["value"]) == ("00 00 5c 42", 55.0),
               "donor FOV[1] at 328 is float32 55.0 (the row's 'now')",
               d["FOV[1]"]["hex"])
    good &= ok((b["FOV[0]"]["hex"], b["FOV[0]"]["value"]) == ("00 00 5c 42", 55.0),
               "test-091 FOV[0] at 324 is float32 55.0",
               b["FOV[0]"]["hex"])
    good &= ok((b["FOV[1]"]["hex"], b["FOV[1]"]["value"]) == ("00 00 7c 42", 63.0),
               "test-091 FOV[1] at 328 is float32 63.0",
               b["FOV[1]"]["hex"])
    good &= ok((b["FOVVelocityRange[1]"]["value"]) == 108.0,
               "test-091 FOVVelocityRange[1] at 320 is 108 km/h (T-CAM3's pair)")

    good &= ok("95+10 h → 68.4 v" in blob(CAM_MD).decode("utf-8"),
               f"CAMERA.md line {f['prose']['sixty_eight']['line']} still carries 95+10 -> 68.4",
               "the clause's source")
    good &= ok("min/max pair over speed" in blob(CAM_MD).decode("utf-8"),
               "CAMERA.md still states JC3's FOV is one min/max pair over speed")

    good &= ok(f["t6_row"] == ORIGINAL_ROW,
               f"T6_HUD_CAMERA.md:{f['t6_line']} still holds the original row (not edited)")
    good &= ok(ORIGINAL_ROW not in blob(T6).decode("utf-8").replace(f["t6_row"], "", 1),
               "the original row appears exactly once in T6")

    expected = render(f)
    on_disk = blob(OUT).decode("utf-8") if os.path.exists(OUT) else ""
    if on_disk == expected:
        good &= ok(True, f"{os.path.relpath(OUT, ROOT)} matches a fresh render (bytes re-checked)")
    else:
        good &= ok(False, f"{os.path.relpath(OUT, ROOT)} differs from a fresh render")
    row = proposed_row(c)
    good &= ok(row in on_disk, "the proposal carries the corrected row verbatim")
    good &= ok("95 boost is a gap" not in row, "the corrected row drops the false gap")
    good &= ok(row.count("68") == 1 and "(not 68)" in row,
               "the row mentions 68 only to refute it")
    good &= ok(f"{c['105']:.2f}" in row and f"{c['85']:.2f}" in row and f"{c['95']:.2f}" in row,
               "the row's three conversions are the recomputed ones")
    return 0 if good else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="emit the proposal")
    g.add_argument("--check", action="store_true", help="recompute all and compare")
    a = ap.parse_args()

    f = facts()
    if a.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(f))
        print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT)} bytes)")
        print(f"85 h -> {f['conv']['85']:.2f} v | 95 h -> {f['conv']['95']:.2f} v | "
              f"105 h -> {f['conv']['105']:.2f} v")
        return 0

    rc = check(f)
    print(f"\n{'check: all assertions passed' if rc == 0 else 'check: FAILED'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

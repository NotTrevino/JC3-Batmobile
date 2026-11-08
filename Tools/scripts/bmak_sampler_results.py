"""bmak_sampler_results.py - G3-02f results: what the two live sampler2 logs show, derived from the logs.

Reads (read-only) Research/BatmobileGrab/runtime/samples2-20261105T073917Z.jsonl and ...T075011Z.jsonl,
extracts every pulse of every RPlayerInput button byte (in0.b768..b799), every change of the vehicle flag word
and BoostingOut, and writes SAMPLER_RESULTS.json + SAMPLER_RESULTS.md. --check re-derives and compares.

    python bmak_sampler_results.py --write
    python bmak_sampler_results.py --check
"""
from __future__ import annotations

import datetime
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RT = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime")
LOGS = ["samples2-20261105T073917Z.jsonl", "samples2-20261105T075011Z.jsonl"]
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_RESULTS.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "SAMPLER_RESULTS.md")
FLAG = "RVehicleBatmobile1.boostflags11D8"


def ts(t):
    return datetime.datetime.fromisoformat(t.rstrip("Z"))


def derive():
    res = {"logs": {}}
    for name in LOGS:
        recs = [json.loads(l) for l in open(os.path.join(RT, name), encoding="utf-8")]
        base = recs[0]["changed"]
        t0 = ts(recs[0]["t"])
        open_at, pulses, flags, boosting_out, booster = {}, [], [], [], []
        for r in recs[1:]:
            t = r["t"][11:23]
            for k, v in r["changed"].items():
                if k.startswith("in0.b") and k[5:].isdigit():
                    b = int(k[5:])
                    if b >= 796:
                        continue          # 796..799 is an analog value, not a button
                    if v and b not in open_at:
                        open_at[b] = r["t"]
                    elif not v and b in open_at:
                        d = (ts(r["t"]) - ts(open_at[b])).total_seconds()
                        pulses.append({"byte": b, "start": open_at[b][11:23], "held_s": round(d, 3)})
                        del open_at[b]
                elif k == FLAG:
                    flags.append({"t": t, "value": v, "hex": hex(v)})
                elif k.endswith("BoostingOut"):
                    boosting_out.append({"t": t, "value": v})
                elif k.endswith("Booster1.boostword"):
                    booster.append({"t": t, "value": v})
        res["logs"][name] = {
            "records": len(recs), "baseline_keys": len(base),
            "axes_at_baseline": {k: v for k, v in base.items() if "Axis" in k},
            "axes_ever_changed": any("Axis" in k for r in recs[1:] for k in r["changed"]),
            "pulses": sorted(pulses, key=lambda p: p["start"]),
            "flag_changes": flags, "boosting_out_changes": boosting_out, "booster_word_changes": booster,
        }
    return res


STATED = """\
## Presses stated by the operator (not derivable from the logs)

The 075011 run was driven from this list, in pursuit mode, with no markers typed:
RT; X (reverse); RT+Y; Y alone; LT + X twice. The eject at 07:56:04 was announced as "just ejected" and later
described as **A double-tapped**. Matching a pulse to a press below is by timing and order only.
"""

MAP = """\
## Mapping (label per row)

| control | RPlayerInput byte | layout name | label |
|---|---:|---|---|
| Y (boost) | 781 | `bVehicleBoostButton` | **decoded + observed** (flips on Y alone and on RT+Y; the booster `bBoosting` bit rose only when RT was held too) |
| RT | 772 + 778 | 778 = `bFireVehicleWeapon`; 772 unnamed here | **observed** (3 RT presses over two runs, pursuit mode; byte 780 `bThrottleButton` never moved) |
| X (reverse) | 783 | unnamed in the sampled region | **probable** (one 3.3 s hold matches the stated X; the earlier 0.6 s pulse and double tap fit too) |
| LT | 773 | `bReadyGadgetButton` | **probable** (11 s hold matches the stated LT; in the first run 773 rose with two 783 taps) |
| A (eject, double-tapped) | 771 | unnamed here | **probable** (only button byte that moved around the eject; two pulses fit the double tap, but the second was held 2.2 s, not a quick tap) |
| (unidentified) | 774 | `bCancelButton` | taps of ~0.1-0.15 s near the start/end of presses; **UNKNOWN** what produces them (possibly a keyboard Enter; not tested) |
"""

UNKNOWN = """\
## UNKNOWN (left for the grab queue; no more in-game testing is planned)

1. The meaning of vehicle flag-word bits `0x100000`, `0x100`, `0x80`, `0x400`, `0x10`, `0x8`, `0x2` that toggled with
   boost, X-reverse and LT (the sampler's bit table names only `0x80000 bCockpitOpen` among them).
2. Why `BoostingOut` (vehicle +5901) pulsed on eject, not on boost.
3. Whether the X-twice barrage press registers on 783 with the barrage meter empty (run 075011: LT held 11 s, no 783
   event in that window; run 073917: two 783 taps 0.3 s apart inside a 773 hold).
4. The RT byte pair: why pursuit RT sets `bFireVehicleWeapon` and not `bThrottleButton`; `aThrottleAxis` and
   `aBrakeAxis` stayed 0.0 for the whole run, so the throttle is not read from those two axes in this input path.
5. No `RPlayerController` instance was found, so `CurrentEjectType`, `LastEjectFromBatmobileTime` and
   `UsedQuickGadget` were never sampled (absence of a change is not evidence here).
6. Byte 783 / 771 / 772 names and `TArray` strides for the missile arrays (SAMPLER_FIELDS2.md UNKNOWN 4).
"""


def write():
    d = derive()
    json.dump(d, open(OUT_JSON, "w", encoding="utf-8"), indent=1)
    L = ["# SAMPLER_RESULTS - what the two live sampler2 logs show (G3-02f follow-up)", "",
         "Generated by `Tools/scripts/bmak_sampler_results.py --write`; `--check` re-derives every table from the",
         "logs in `Research/BatmobileGrab/runtime/`. Read-only observation of `BatmanAK.exe`; nothing was written to the",
         "game. Sampler: `Tools/scripts/bmak_runtime_sampler2.py`.", "", STATED, MAP]
    for name, lg in d["logs"].items():
        L += [f"## Log `{name}` ({lg['records']} records)", "",
              f"Axes at baseline {lg['axes_at_baseline']}; ever changed: **{lg['axes_ever_changed']}**.", "",
              "| button byte | start (UTC) | held (s) |", "|---:|---|---:|"]
        L += [f"| {p['byte']} | {p['start']} | {p['held_s']} |" for p in lg["pulses"]]
        L += ["", "Vehicle flag word changes: " + (", ".join(f"{c['t']}={c['hex']}" for c in lg["flag_changes"]) or "none"),
              "", "BoostingOut changes: " + (", ".join(f"{c['t']}={c['value']}" for c in lg["boosting_out_changes"]) or "none"),
              "", "Booster `boostword` changes: " + (", ".join(f"{c['t']}={c['value']}" for c in lg["booster_word_changes"]) or "none"), ""]
    L += [UNKNOWN, "## Reproduce", "", "```", "python Tools/scripts/bmak_sampler_results.py --write",
          "python Tools/scripts/bmak_sampler_results.py --check", "```", ""]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L))
    print("wrote", OUT_JSON, OUT_MD)


def check():
    d = derive()
    old = json.load(open(OUT_JSON, encoding="utf-8"))
    ok = d == old
    # spot oracles taken from the stated run
    p2 = {(p["byte"], p["start"]) for p in d["logs"][LOGS[1]]["pulses"]}
    need = [(781, "07:50:42.672"), (783, "07:50:32.768"), (773, "07:51:40.489"), (771, "07:56:04.263")]
    missing = [n for n in need if n not in p2]
    print("derive == stored JSON:", ok, "| spot pulses missing:", missing)
    sys.exit(0 if ok and not missing else 1)


if __name__ == "__main__":
    write() if "--write" in sys.argv else check()

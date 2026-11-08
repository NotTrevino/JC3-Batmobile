"""tl17_proposal.py - the proposed correction for T-L17 (built light entry 11).

`Research/BatmobileGrab/LIGHT_ENTRY11.md` decoded BmAK's run-time colour for the
`BattleModeSpotLight` / `VEHLT_BattleModeLight` lamp as the class-default white
`LightColor [255, 255, 255, 0]` (the component carries no colour tag; the chain lands on
`Default__LightComponent`). The build (entry 11) instead carries JC3's own graph-object
colour `0.6039 / 0.6039 / 0.9529` from `Front_Secondary_Head`.

This tool settles what that means for the row: what unit the JC3 field wants, what white
converts to, and whether the intensity moves with it. It writes
`Working/Translation/TL17_PROPOSAL.md` (the proposed row edit as JSON) and never edits the
row, `t14_lights.json` or the build.

    python Tools/scripts/tl17_proposal.py --write
    python Tools/scripts/tl17_proposal.py --check
"""
from __future__ import annotations

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

T14_JSON = os.path.join(ROOT, "Working/Translation/t14_lights.json")
T14_MD = os.path.join(ROOT, "Working/Translation/T14_LIGHTS.md")
LIGHTS_JSON = os.path.join(ROOT, "Research/BatmobileGrab/LIGHTS.json")
LIGHT_SYSTEM = os.path.join(ROOT, "Research/JC3Grab/LIGHT_SYSTEM.md")
RIG_JSON = os.path.join(ROOT, "Working/Lights/bm_lightrig.json")
ENTRY11_MD = os.path.join(ROOT, "Research/BatmobileGrab/LIGHT_ENTRY11.md")
OUT = os.path.join(ROOT, "Working/Translation/TL17_PROPOSAL.md")

OLD_CELL = "diffuse 0.604,0.604,0.953 r 10.0 ang 60.0"
NEW_CELL = "diffuse 1.000,1.000,1.000 r 10.0 ang 60.0"


def text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def line_of(path: str, needle: str) -> int:
    body = text(path)
    off = body.find(needle)
    if off < 0:
        raise SystemExit(f"{path}: {needle!r} not found")
    return body[:off].count("\n") + 1


def census_line(body: str, member: str) -> str:
    """The value-census row for `member`, not the type-table row.

    Both start with `| `member` |`; only the census carries `value x count` tokens.
    """
    for ln in body.splitlines():
        if f"`{member}`" in ln and re.search(r"`[0-9.]+` x\d+", ln):
            return ln
    raise SystemExit(f"LIGHT_SYSTEM.md: no value census found for {member}")


def facts() -> dict:
    t14 = json.load(open(T14_JSON, encoding="utf-8"))
    row = next(r for r in t14["rows"] if r["id"] == "T-L17")
    lights = json.load(open(LIGHTS_JSON, encoding="utf-8"))
    entry = next(e for e in lights["vehicles"][0]["entries"]
                 if e["socket"] == "BattleModeSpotLight")
    rig = json.load(open(RIG_JSON, encoding="utf-8"))
    built = next(r for r in rig["rows"] if r["origin"] == "graph-object (T-L17)")
    comp = entry["components"][0]
    m = built["members"]

    colour = comp["colour"]["value"]
    rgb = colour[:3]

    # The /255 question, answered from the recipe the JC3 grab already emitted:
    # LIGHT_SYSTEM.md converts LightColor [160,180,255] to 0.627451/0.705882/1.0.
    ls = text(LIGHT_SYSTEM)
    mul_line = census_line(ls, "multiplier")
    lum_line = census_line(ls, "min_luminosity")
    mults = [(float(v), int(n)) for v, n in re.findall(r"`([0-9.]+)` x(\d+)", mul_line)]
    lums = [(float(v), int(n)) for v, n in re.findall(r"`([0-9.]+)` x(\d+)", lum_line)]

    t14_row = next(ln for ln in text(T14_MD).splitlines() if ln.startswith("| T-L17 |"))

    return {
        "t14_row": t14_row,
        "t14_line": next(i + 1 for i, ln in enumerate(text(T14_MD).splitlines())
                         if ln.startswith("| T-L17 |")),
        "row": row,
        "entry": entry,
        "component": comp,
        "colour": colour,
        "rgb": rgb,
        "brightness": comp["fields"]["Brightness"],
        "brightness_src": comp["field_sources"]["Brightness"],
        "colour_src": comp["field_sources"]["LightColor"],
        "built": {
            "diffuse": [m["diffuse.R"]["v"], m["diffuse.G"]["v"], m["diffuse.B"]["v"]],
            "multiplier": m["multiplier"]["v"],
            "min_luminosity": m["min_luminosity"]["v"],
            "range": m["range"]["v"],
            "near_cap": m["near_cap"]["v"],
            "index": built["index"],
        },
        "object": row["targets"][0]["object"],
        "proposal_diffuse": row["proposal_diffuse"],
        "conv": [c / 255.0 for c in rgb],
        "recipe": {"r": 0.627451, "g": 0.705882, "b": 1.0, "src": [160, 180, 255]},
        "multipliers": mults,
        "luminosities": lums,
        "mul_total": sum(n for _v, n in mults),
        "ls_lines": {
            "types": line_of(LIGHT_SYSTEM, "| `diffuse.R` | float | 3,217 |"),
            "recipe": line_of(LIGHT_SYSTEM, "| `diffuse.R` | `0.627451` |"),
            "multiplier": line_of(LIGHT_SYSTEM, "| `multiplier` | `1` x2188"),
            "min_luminosity": line_of(LIGHT_SYSTEM, "| `min_luminosity` | `0` x3217 |"),
            "units_unknown": line_of(LIGHT_SYSTEM, "**Range/angle units**"),
        },
        "entry11_line": line_of(ENTRY11_MD, "**Answer: white"),
    }


def edit_object(f: dict) -> dict:
    """The proposed row edit, as data (rendered to JSON in the proposal)."""
    b = f["built"]
    return {
        "row": "T-L17",
        "doc": f"Working/Translation/T14_LIGHTS.md:{f['t14_line']}",
        "ledger": "T_ROWS.jsonl: T-14, '3. The rows', dispo 'next', edits 0",
        "status": "proposed - not applied",
        "cells": {
            "now": {
                "keep": "LightColor 255,255,255,0 B 0.0 cone 5.0/15.0 R 4500.0",
                "why": "decoded and unchanged: LIGHTS.json Playable_Batmobile_SF entry 9 "
                       "(SpotLightComponent)",
            },
            "proposed": {"from": OLD_CELL, "to": NEW_CELL},
        },
        "fields": [
            {"field": "diffuse.R", "built": b["diffuse"][0], "bmak": f"{f['colour']}",
             "bmak_channel": f["colour"][0], "correct": 1.0, "action": "change",
             "transform": "255 / 255", "class": "derived",
             "why": "LightColor is FColor 0..255; JC3 diffuse is a 0..1 float "
                    "(LIGHT_SYSTEM.md field table + the /255 recipe)"},
            {"field": "diffuse.G", "built": b["diffuse"][1], "bmak": f"{f['colour']}",
             "bmak_channel": f["colour"][1], "correct": 1.0, "action": "change",
             "transform": "255 / 255", "class": "derived",
             "why": "same conversion; white is all three channels 255"},
            {"field": "diffuse.B", "built": b["diffuse"][2], "bmak": f"{f['colour']}",
             "bmak_channel": f["colour"][2], "correct": 1.0, "action": "change",
             "transform": "255 / 255", "class": "derived",
             "why": "same conversion; white is all three channels 255"},
            {"field": "multiplier", "built": b["multiplier"], "bmak_brightness": 0.0,
             "correct": b["multiplier"], "action": "keep",
             "class": "UNKNOWN (no decoded bridge)",
             "why": "BmAK Brightness 0.0 is the component's own serialised value on a lamp "
                    "that ships dark until a script raises it; JC3 multiplier is a 0.3..5 "
                    "scale with no zero in 3,217 shipped entries, so 0 would delete the "
                    "lamp. No file maps Brightness -> multiplier (T-18 owns that bridge)."},
            {"field": "min_luminosity", "built": b["min_luminosity"], "bmak_brightness": 0.0,
             "correct": b["min_luminosity"], "action": "keep",
             "class": "derived",
             "why": "all 3,217 shipped entries carry 0, so there is nothing to copy"},
        ],
        "intensity_changes": False,
        "out_of_scope": [
            {"field": "range", "built": b["range"], "bmak": "Radius 4500.0",
             "why": "metres vs UE3 cm - no decoded unit bridge (LIGHT_SYSTEM.md "
                    "'Range/angle units' is UNKNOWN); a fidelity choice, not a conversion"},
            {"field": "angle", "built": 60.0, "bmak": "OuterConeAngle 15.0",
             "why": "same missing bridge; the graph's 60.0 stays until T-18 decides"},
            {"field": "near_cap", "built": b["near_cap"], "bmak": None,
             "why": "graph value, kept"},
        ],
        "reconciles": {
            "t14_lights.json": f"rows[T-L17].proposal_diffuse = {f['proposal_diffuse']}",
            "note": "the JSON row already proposes white; only the .md 'proposed' cell "
                    "still prints the graph colour, so this edit makes the two agree",
        },
        "evidence": [
            f"Research/BatmobileGrab/LIGHTS.json vehicles[0].entries[9].components[0]."
            f"colour = {f['colour']}, source '{f['colour_src']}'",
            f"Research/BatmobileGrab/LIGHT_ENTRY11.md:{f['entry11_line']} - 'Answer: white' "
            f"with the class-default chain",
            f"Research/JC3Grab/LIGHT_SYSTEM.md:{f['ls_lines']['types']} - diffuse.R/G/B are "
            f"float, 3,217 entries (0..1 values)",
            f"Research/JC3Grab/LIGHT_SYSTEM.md:{f['ls_lines']['recipe']} - 160/255 = 0.627451 "
            f"(plain /255, no gamma)",
            f"Working/Lights/bm_lightrig.json rows[{f['built']['index']}] - built diffuse "
            f"{f['built']['diffuse']}, multiplier {f['built']['multiplier']}",
        ],
        "not_edited": ["Working/Translation/T14_LIGHTS.md", "Working/Translation/t14_lights.json",
                       "Working/Lights/bm_lightrig.json", "any Builds/ tree"],
    }


def render(f: dict) -> str:
    e = edit_object(f)
    b = f["built"]
    obj = f["object"]
    payload = json.dumps(e, indent=2, ensure_ascii=False)
    return f"""# T-L17 — proposed row edit (built light entry 11)

**The colour changes; the intensity does not.** BmAK runs this lamp at the
class-default white `LightColor [255, 255, 255, 0]`; JC3's `diffuse.R/G/B` are 0..1 floats
(`LIGHT_SYSTEM.md` field table, and its own recipe divides `LightColor` by 255: 160 → 0.627451
exactly), so white converts to **1.000, 1.000, 1.000**, not to 0.604/0.604/0.953 - that
triple is JC3's graph object `Front_Secondary_Head`'s own colour, which the build copied.
The intensity is a different question with no decoded bridge, so it stays at the shipped
`multiplier 1.0` (see §3): BmAK's `Brightness 0.0` is a serialised "ships dark" value, and
`multiplier` never takes 0 in the 3,217 shipped entries, so copying it would delete the lamp
rather than match it.

Nothing is applied: `T14_LIGHTS.md:{f['t14_line']}`, `t14_lights.json` and
`Working/Lights/bm_lightrig.json` are untouched.

## 1. The proposed edit, as JSON

```json
{payload}
```

## 2. Which field, and why 0..1

`VehicleDynamicLights` carries three colour members per entry - `diffuse.R`, `diffuse.G`,
`diffuse.B` - each typed **float** and present on all 3,217 entries
(`LIGHT_SYSTEM.md:{f['ls_lines']['types']}`). Their census is 0..1 (`1.0`, `0.185, 0.3132, 1.0`
on the police siren, `0, 1, 0` in the `.epe` samples): **no shipped value exceeds 1.0**, so the
field is a normalised 0..1 triple, not 0..255.

The scale factor is proven by `LIGHT_SYSTEM.md:{f['ls_lines']['recipe']}`, which converts a
BmAK colour it already decodes - `LightColor [160, 180, 255]` - to
`0.627451 / 0.705882 / 1.0`:

```
160 / 255 = {160/255:.6f}   <- the emitted 0.627451
180 / 255 = {180/255:.6f}   <- the emitted 0.705882
255 / 255 = {255/255:.1f}          <- the emitted 1.0
```

That is a plain divide by 255 (the recipe's "sRGB -> 0..1" keeps the encoding; it is not a
gamma linearisation - a linearisation of 160 would be ~0.35, not 0.627). White is 255 on all
three channels, so **every channel becomes 1.0** either way, and the row's precision
(`0.604,0.604,0.953`, the graph's) becomes `1.000,1.000,1.000`.

`LightColor`'s fourth byte is 0 in BmAK's `FColor`; it is the unused alpha of a light colour,
not transparency, and JC3's entry has no alpha member, so nothing is carried from it.

## 3. Whether the intensity must change: no

BmAK's `Brightness` here is **0.0**, and it is the component's *own* serialised value
(`field_sources.Brightness = "component"`, not the CDO like the colour). The colour's source
and the brightness's source are different links in the same chain, which is why the colour
moves to the class default while the brightness stays at 0.0. Three reasons it must not be
copied into JC3:

1. **It is a "ships dark" value, not a scale.** A 0.0-brightness spotlight emits nothing until
   a script raises it; the lamp's own radius/cone are authored (4500 / 5..15), so the shape is
   real and only the drive is zero. JC3's `multiplier` is the brightness scale of an entry
   that is meant to light.
2. **0 is outside JC3's observed domain.** The shipped census
   (`LIGHT_SYSTEM.md:{f['ls_lines']['multiplier']}`) is
   `1` ×2188, `2` ×792, `0.5` ×174, `0.7` ×30, `3` ×12, `5` ×12, `0.3` ×6, `0.4` ×3 - **0 of
   {f['mul_total']} entries use 0**. `min_luminosity` is 0 on all
   {sum(n for _v, n in f['luminosities'])} of them. Writing `multiplier = 0.0` would black the
   entry out, not reproduce BmAK.
3. **There is no decoded bridge.** No file states what BmAK `Brightness` corresponds to in
   JC3's `multiplier`/`min_luminosity` pair, and the same rig doesn't even agree with itself:
   `T-L15`/`T-L16` carry `B 1.0` and `R 150.0`, `T-L18`/`T-L19` carry `B 5.0`, this light
   `B 0.0` on `R 4500.0`. A monotone copy of 0.0 would be a guess, so the built
   `multiplier {b['multiplier']}` stays and is relabelled *JC3 graph value, not a BmAK copy*
   rather than "converted". `LIGHT_ENTRY11.md` lists the same gap under its UNKNOWNs.

So the edit touches the three colour channels only. `range` and `angle` are listed in the
JSON's `out_of_scope` for the same reason as the intensity - `LIGHT_SYSTEM.md:{f['ls_lines']['units_unknown']}`
records their units as UNKNOWN - and are **not** part of this proposal.

## 4. What the row and the build say today

| file | field | value | source |
|---|---|---:|---|
| `t14_lights.json` row `T-L17` | `bmak.colour` | `{f['colour']}` | LIGHTS.json entry 9 (class default) |
| `t14_lights.json` row `T-L17` | `bmak.brightness` | {f['brightness']} | component |
| `t14_lights.json` row `T-L17` | `proposal_diffuse` | `{f['proposal_diffuse']}` | **already white** |
| `T14_LIGHTS.md:{f['t14_line']}` | proposed cell | `{OLD_CELL}` | the graph object |
| `bm_lightrig.json` entry {b['index']} | `diffuse.R/G/B` | `{b['diffuse']}` | graph object `{obj['name']}` |
| `bm_lightrig.json` entry {b['index']} | `multiplier` / `min_luminosity` | {b['multiplier']} / {b['min_luminosity']} | graph object / shipped row |

The two T-14 records already disagree with each other: the JSON row's
`proposal_diffuse` is `{f['proposal_diffuse']}`, while the `.md` proposed cell still prints
`{OLD_CELL}`. This edit makes the `.md` cell match the JSON, i.e. it is a copy correction,
not a new decision. The **build** entry {b['index']} is what implements the stale cell
(`{b['diffuse']}` = `154 154 243` at 255), so applying the row alone does not change the
lamp - a rebuild is needed, and that is deliberately out of scope here.

## 5. Labels

* **Decoded:** `LightColor [255,255,255,0]` and its `class default: Default__LightComponent
  (Engine.upk)` source; `Brightness 0.0` and its `component` source; the graph object's
  `diffuse`/`multiplier`; the JSON's `proposal_diffuse`; the `.md` cells; the file census lines.
* **Derived:** 255/255 = 1.0; 160/255 = 0.627451 as the proof of a plain /255; the "0 is outside
  0.3..5" argument; the decision that intensity does not move.
* **UNKNOWN:** whether a script recolours or brightens the component at run time
  (`LIGHT_ENTRY11.md`); the `Brightness` -> `multiplier` bridge; the range/angle units.

## 6. UNKNOWNs

* **Brightness semantics.** 0.0 here vs 1.0/5.0 on other lamps; nothing decoded maps it, so no
  number is written for it. Where it would be found: the native `SetFreeCameraConfig`-style
  decodes have no light equivalent yet; a `BatmanAK.exe` read of the light update path, or a
  Q-1 #7 observation with the battle lamp scripted on.
* **Whether the presets override these members.** `LIGHT_SYSTEM.md` §3 shows presets do not fix
  the numbers across vehicles, but whether a preset *overrides* an entry at run time is UNKNOWN.
  This entry's `preset_id` is the graph's own hash, and no module row references it (T-LG2).
* **What 0.604/0.604/0.953 was for.** If the intent was "match JC3's own look", the built colour
  is a choice, not an error; the row's `now` cell, however, prints BmAK's white, so the row
  cannot claim both. This proposal takes the row at its word (BmAK-faithful).
"""


def ok(cond: bool, label: str, detail: str = "") -> bool:
    print(f"{'PASS' if cond else 'FAIL'} {label}" + (f" [{detail}]" if detail and not cond else ""))
    return cond


def check(f: dict) -> int:
    good = True
    e = edit_object(f)
    b = f["built"]

    good &= ok(f["colour"] == [255, 255, 255, 0],
               "LIGHTS.json entry 9 LightColor is [255, 255, 255, 0]", str(f["colour"]))
    good &= ok("Default__LightComponent" in f["colour_src"],
               "that colour's recorded source is the class default", f["colour_src"])
    good &= ok(f["brightness"] == 0.0 and f["brightness_src"] == "component",
               "Brightness is 0.0 and is the component's own serialised value",
               f"{f['brightness']} / {f['brightness_src']}")
    good &= ok(b["diffuse"] == [0.6039, 0.6039, 0.9529],
               "the build (entry 11) still carries the graph colour 0.6039/0.6039/0.9529",
               str(b["diffuse"]))
    good &= ok(f["proposal_diffuse"] == [1.0, 1.0, 1.0],
               "t14_lights.json already proposes [1.0, 1.0, 1.0]", str(f["proposal_diffuse"]))

    good &= ok([round(c, 6) for c in f["conv"]] == [1.0, 1.0, 1.0],
               "255 / 255 = 1.0 on all three channels")
    good &= ok(abs(160 / 255 - f["recipe"]["r"]) < 1e-6
               and abs(180 / 255 - f["recipe"]["g"]) < 1e-6
               and abs(255 / 255 - f["recipe"]["b"]) < 1e-6,
               "LIGHT_SYSTEM's own recipe is LightColor/255 (160 -> 0.627451)", )
    good &= ok(max(f["rgb"]) / 255 <= 1.0, "no converted channel exceeds 1.0")
    good &= ok(f["built"]["multiplier"] == 1.0 and min(v for v, _n in f["multipliers"]) > 0.0,
               "multiplier stays 1.0: 0 is outside the 0.3..5 shipped census",
               str((f["built"]["multiplier"], sorted(v for v, _n in f["multipliers"])[:3])))
    good &= ok(len(f["multipliers"]) >= 8 and f["mul_total"] == 3217,
               "the multiplier census parsed and covers all 3,217 entries",
               f"{len(f['multipliers'])} values / {f['mul_total']}")
    good &= ok(len(f["luminosities"]) == 1 and all(v == 0.0 for v, _n in f["luminosities"])
               and sum(n for _v, n in f["luminosities"]) == 3217,
               "min_luminosity is 0 on all 3,217 shipped entries",
               str(f["luminosities"]))
    good &= ok(e["intensity_changes"] is False, "the proposal leaves the intensity alone")

    good &= ok(OLD_CELL in f["t14_row"] or NEW_CELL in f["t14_row"],
               f"T14_LIGHTS.md:{f['t14_line']} holds the old cell (or the applied one) - not edited")
    good &= ok("LightColor 255,255,255,0 B 0.0" in f["t14_row"],
               "the row's 'now' cell is unchanged (BmAK white / B 0.0)")
    good &= ok(f["t14_row"].count(OLD_CELL) + f["t14_row"].count(NEW_CELL) == 1,
               "exactly one of the two proposed-cell texts is present")

    expected = render(f)
    disk = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
    good &= ok(disk == expected, f"{os.path.relpath(OUT, ROOT)} matches a fresh render "
                                 "(every value re-read)")
    good &= ok('"correct": 1.0' in disk and '"action": "change"' in disk,
               "the JSON edit carries 1.0 as the corrected channel value")
    good &= ok('"intensity_changes": false' in disk,
               "the JSON edit records that the intensity does not change")
    good &= ok(NEW_CELL in disk and OLD_CELL in disk,
               "the edit shows both the from and the to cell")
    return 0 if good else 1


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()

    f = facts()
    if a.write:
        with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(render(f))
        print(f"wrote {os.path.relpath(OUT, ROOT)} ({os.path.getsize(OUT)} bytes)")
        print(f"colour {f['rgb']} / 255 -> {[round(c, 4) for c in f['conv']]}; "
              f"intensity kept at multiplier {f['built']['multiplier']}")
        return 0

    rc = check(f)
    print(f"\n{'check: all assertions passed' if rc == 0 else 'check: FAILED'}")
    return rc


if __name__ == "__main__":
    sys.exit(main())

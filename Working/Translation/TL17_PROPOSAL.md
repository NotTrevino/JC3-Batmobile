# T-L17 — proposed row edit (built light entry 11)

**The colour changes; the intensity does not.** BmAK runs this lamp at the
class-default white `LightColor [255, 255, 255, 0]`; JC3's `diffuse.R/G/B` are 0..1 floats
(`LIGHT_SYSTEM.md` field table, and its own recipe divides `LightColor` by 255: 160 → 0.627451
exactly), so white converts to **1.000, 1.000, 1.000**, not to 0.604/0.604/0.953 - that
triple is JC3's graph object `Front_Secondary_Head`'s own colour, which the build copied.
The intensity is a different question with no decoded bridge, so it stays at the shipped
`multiplier 1.0` (see §3): BmAK's `Brightness 0.0` is a serialised "ships dark" value, and
`multiplier` never takes 0 in the 3,217 shipped entries, so copying it would delete the lamp
rather than match it.

Nothing is applied: `T14_LIGHTS.md:64`, `t14_lights.json` and
`Working/Lights/bm_lightrig.json` are untouched.

## 1. The proposed edit, as JSON

```json
{
  "row": "T-L17",
  "doc": "Working/Translation/T14_LIGHTS.md:64",
  "ledger": "T_ROWS.jsonl: T-14, '3. The rows', dispo 'next', edits 0",
  "status": "proposed - not applied",
  "cells": {
    "now": {
      "keep": "LightColor 255,255,255,0 B 0.0 cone 5.0/15.0 R 4500.0",
      "why": "decoded and unchanged: LIGHTS.json Playable_Batmobile_SF entry 9 (SpotLightComponent)"
    },
    "proposed": {
      "from": "diffuse 0.604,0.604,0.953 r 10.0 ang 60.0",
      "to": "diffuse 1.000,1.000,1.000 r 10.0 ang 60.0"
    }
  },
  "fields": [
    {
      "field": "diffuse.R",
      "built": 0.6039,
      "bmak": "[255, 255, 255, 0]",
      "bmak_channel": 255,
      "correct": 1.0,
      "action": "change",
      "transform": "255 / 255",
      "class": "derived",
      "why": "LightColor is FColor 0..255; JC3 diffuse is a 0..1 float (LIGHT_SYSTEM.md field table + the /255 recipe)"
    },
    {
      "field": "diffuse.G",
      "built": 0.6039,
      "bmak": "[255, 255, 255, 0]",
      "bmak_channel": 255,
      "correct": 1.0,
      "action": "change",
      "transform": "255 / 255",
      "class": "derived",
      "why": "same conversion; white is all three channels 255"
    },
    {
      "field": "diffuse.B",
      "built": 0.9529,
      "bmak": "[255, 255, 255, 0]",
      "bmak_channel": 255,
      "correct": 1.0,
      "action": "change",
      "transform": "255 / 255",
      "class": "derived",
      "why": "same conversion; white is all three channels 255"
    },
    {
      "field": "multiplier",
      "built": 1.0,
      "bmak_brightness": 0.0,
      "correct": 1.0,
      "action": "keep",
      "class": "UNKNOWN (no decoded bridge)",
      "why": "BmAK Brightness 0.0 is the component's own serialised value on a lamp that ships dark until a script raises it; JC3 multiplier is a 0.3..5 scale with no zero in 3,217 shipped entries, so 0 would delete the lamp. No file maps Brightness -> multiplier (T-18 owns that bridge)."
    },
    {
      "field": "min_luminosity",
      "built": 0.0,
      "bmak_brightness": 0.0,
      "correct": 0.0,
      "action": "keep",
      "class": "derived",
      "why": "all 3,217 shipped entries carry 0, so there is nothing to copy"
    }
  ],
  "intensity_changes": false,
  "out_of_scope": [
    {
      "field": "range",
      "built": 10.0,
      "bmak": "Radius 4500.0",
      "why": "metres vs UE3 cm - no decoded unit bridge (LIGHT_SYSTEM.md 'Range/angle units' is UNKNOWN); a fidelity choice, not a conversion"
    },
    {
      "field": "angle",
      "built": 60.0,
      "bmak": "OuterConeAngle 15.0",
      "why": "same missing bridge; the graph's 60.0 stays until T-18 decides"
    },
    {
      "field": "near_cap",
      "built": 1.25,
      "bmak": null,
      "why": "graph value, kept"
    }
  ],
  "reconciles": {
    "t14_lights.json": "rows[T-L17].proposal_diffuse = [1.0, 1.0, 1.0]",
    "note": "the JSON row already proposes white; only the .md 'proposed' cell still prints the graph colour, so this edit makes the two agree"
  },
  "evidence": [
    "Research/BatmobileGrab/LIGHTS.json vehicles[0].entries[9].components[0].colour = [255, 255, 255, 0], source 'class default: `Default__LightComponent` (Engine.upk)'",
    "Research/BatmobileGrab/LIGHT_ENTRY11.md:3 - 'Answer: white' with the class-default chain",
    "Research/JC3Grab/LIGHT_SYSTEM.md:40 - diffuse.R/G/B are float, 3,217 entries (0..1 values)",
    "Research/JC3Grab/LIGHT_SYSTEM.md:240 - 160/255 = 0.627451 (plain /255, no gamma)",
    "Working/Lights/bm_lightrig.json rows[11] - built diffuse [0.6039, 0.6039, 0.9529], multiplier 1.0"
  ],
  "not_edited": [
    "Working/Translation/T14_LIGHTS.md",
    "Working/Translation/t14_lights.json",
    "Working/Lights/bm_lightrig.json",
    "any Builds/ tree"
  ]
}
```

## 2. Which field, and why 0..1

`VehicleDynamicLights` carries three colour members per entry - `diffuse.R`, `diffuse.G`,
`diffuse.B` - each typed **float** and present on all 3,217 entries
(`LIGHT_SYSTEM.md:40`). Their census is 0..1 (`1.0`, `0.185, 0.3132, 1.0`
on the police siren, `0, 1, 0` in the `.epe` samples): **no shipped value exceeds 1.0**, so the
field is a normalised 0..1 triple, not 0..255.

The scale factor is proven by `LIGHT_SYSTEM.md:240`, which converts a
BmAK colour it already decodes - `LightColor [160, 180, 255]` - to
`0.627451 / 0.705882 / 1.0`:

```
160 / 255 = 0.627451   <- the emitted 0.627451
180 / 255 = 0.705882   <- the emitted 0.705882
255 / 255 = 1.0          <- the emitted 1.0
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
   (`LIGHT_SYSTEM.md:78`) is
   `1` ×2188, `2` ×792, `0.5` ×174, `0.7` ×30, `3` ×12, `5` ×12, `0.3` ×6, `0.4` ×3 - **0 of
   3217 entries use 0**. `min_luminosity` is 0 on all
   3217 of them. Writing `multiplier = 0.0` would black the
   entry out, not reproduce BmAK.
3. **There is no decoded bridge.** No file states what BmAK `Brightness` corresponds to in
   JC3's `multiplier`/`min_luminosity` pair, and the same rig doesn't even agree with itself:
   `T-L15`/`T-L16` carry `B 1.0` and `R 150.0`, `T-L18`/`T-L19` carry `B 5.0`, this light
   `B 0.0` on `R 4500.0`. A monotone copy of 0.0 would be a guess, so the built
   `multiplier 1.0` stays and is relabelled *JC3 graph value, not a BmAK copy*
   rather than "converted". `LIGHT_ENTRY11.md` lists the same gap under its UNKNOWNs.

So the edit touches the three colour channels only. `range` and `angle` are listed in the
JSON's `out_of_scope` for the same reason as the intensity - `LIGHT_SYSTEM.md:289`
records their units as UNKNOWN - and are **not** part of this proposal.

## 4. What the row and the build say today

| file | field | value | source |
|---|---|---:|---|
| `t14_lights.json` row `T-L17` | `bmak.colour` | `[255, 255, 255, 0]` | LIGHTS.json entry 9 (class default) |
| `t14_lights.json` row `T-L17` | `bmak.brightness` | 0.0 | component |
| `t14_lights.json` row `T-L17` | `proposal_diffuse` | `[1.0, 1.0, 1.0]` | **already white** |
| `T14_LIGHTS.md:64` | proposed cell | `diffuse 0.604,0.604,0.953 r 10.0 ang 60.0` | the graph object |
| `bm_lightrig.json` entry 11 | `diffuse.R/G/B` | `[0.6039, 0.6039, 0.9529]` | graph object `Front_Secondary_Head` |
| `bm_lightrig.json` entry 11 | `multiplier` / `min_luminosity` | 1.0 / 0.0 | graph object / shipped row |

The two T-14 records already disagree with each other: the JSON row's
`proposal_diffuse` is `[1.0, 1.0, 1.0]`, while the `.md` proposed cell still prints
`diffuse 0.604,0.604,0.953 r 10.0 ang 60.0`. This edit makes the `.md` cell match the JSON, i.e. it is a copy correction,
not a new decision. The **build** entry 11 is what implements the stale cell
(`[0.6039, 0.6039, 0.9529]` = `154 154 243` at 255), so applying the row alone does not change the
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

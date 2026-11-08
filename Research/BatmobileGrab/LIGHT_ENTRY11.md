# Built light entry 11: which colour does BmAK use?

**Answer: white, `LightColor = [255, 255, 255, 0]` (i.e. 1.0, 1.0, 1.0 in the JC3 0..1
scale). The built entry's `0.6039, 0.6039, 0.9529` is JC3's own graph-object colour, not
the BmAK lamp's, so as a copy of BmAK the built colour is wrong.** The row that carries
it is **`T-L17`** (build entry 11, origin `graph-object (T-L17)`); its correct BmAK colour
is `[255, 255, 255, 0]`. Nothing was edited.

## The precedence rule, from the bytes

A cooked UE3 component serialises only the properties that differ from its archetype, and
a tag carries `(type, struct offset, value)` with no name. `grab_lights.py` therefore
resolves each field down a chain and keeps the **first link that carried it**:

1. the component's own serialised tags,
2. the object's archetype - export record word 6 (`archetype_ref`), following an import
   chain when the word is negative,
3. `Default__<class>` (and its parent CDOs) in `Engine.upk` / `BmGame.upk`,
4. the native default, which is compiled into the executable and is in no file.

`Research/BatmobileGrab/LIGHTS.md` states the same rule in its G1-17 section: values
"come from the component itself, then its archetype, then `Default__<class>` in
`Engine.upk` / `BmGame.upk`", and `grab_lights.py` implements it in `resolve_component`
("Every field keeps the first source that carried it", `field_sources`).

### This light, read live out of the shipped packages

Subject: `Playable_Batmobile_SF.upk`, export **5371** (`Batmobile.SpotLightComponent`), the
single component of the `BattleModeSpotLight` / `VEHLT_BattleModeLight` entry:

| link | bytes read | carries LightColor? |
|---|---|---|
| component 5371 | 12 tags; word 6 (archetype) = **0** | **no** - no tag maps to the LightColor offset |
| archetype | word 6 = 0, so the instance inherits straight from the class default | n/a - no archetype object in between |
| `Default__LightComponent` (Engine.upk) | `LightColor = [255, 255, 255, 0]` (FColor, read B,G,R,A) | **yes** - this is the value the chain lands on |

What the component *does* serialise (the 7 fields around the colour): `InnerConeAngle = 5.0`, `OuterConeAngle = 15.0`, `Radius = 4500.0`, `FalloffExponent = 1.0`, `Brightness = 0.0`, `CastDynamicShadows = False`, `CastShadows = False`.
Its `Brightness` is the component's own `0.0`; its radius/cone are `4500.0` / `5.0`..`15.0`. The chain reports
no gap. `resolve_component` returns LightColor `[255, 255, 255, 0]` from
`class default: `Default__LightComponent` (Engine.upk)`, and the CDO read of `SpotLightComponent`'s parent
(`class default: `Default__LightComponent` (Engine.upk)`) carries the same value.

**So at run time the BmAK light's colour is the class default white.** Alpha 0 in the
`FColor` is the unused fourth byte for a light, not transparency: the three colour
channels are 255, 255, 255. (Derived, not decoded: with `Brightness = 0.0` the lamp
contributes nothing until a script raises it; the colour it then shows is this white.)

## What the build has instead

`Working/Lights/bm_lightrig.json` entry 11 is the T-L17 graph-object entry. Its colour is
the JC3 asset's own authored diffuse, decoded from the entity graph object
`Front_Secondary_Head`:

| member | built value | source recorded in the build |
|---|---:|---|
| `diffuse.R` | 0.6039 | graph object `Front_Secondary_Head`.diffuse[0] (decoded) |
| `diffuse.G` | 0.6039 | graph object `Front_Secondary_Head`.diffuse[1] (decoded) |
| `diffuse.B` | 0.9529 | graph object `Front_Secondary_Head`.diffuse[2] (decoded) |
| `preset_id` | 3189390601 | the graph object's own hash (T-LG2: no module row references it) |

That graph object is a JC3-side preset (`Front_Secondary_Head`, hash 3189390601), so
0.6039/0.6039/0.9529 is a colour JC3 authored for its own light, not a value BmAK holds.
`T-18`'s row T-L17 already prints the BmAK side correctly - `LightColor 255,255,255,0`,
`B 0.0`, `cone 5.0/15.0`, `R 4500.0` - and then proposes the graph values. The build
implements the proposal, which is where the two numbers part.

## The correction (given, not applied)

| field | built now | BmAK (correct) | JC3 0..1 form |
|---|---|---|---|
| colour | 0.6039, 0.6039, 0.9529 | `LightColor [255, 255, 255, 0]` | **1.0, 1.0, 1.0** |
| range | 10.0 | `Radius 4500.0` | 4500.0 (bridge decisions belong to T-18) |
| angle | 60.0 | `OuterConeAngle 15.0` | 15.0 |

Row to change: **`T-L17`** (`dispo: next`, never applied). Its `proposed` cell and the
`bm_lightrig` entry 11 that mirrors it should carry `diffuse 1.000,1.000,1.000` for a
BmAK-faithful lamp. The range/angle columns follow the same authorship difference and are
listed only so the change is not half-made; whether to prefer BmAK's 4500/15 or the
JC3 graph's 10/60 is a fidelity decision, not a byte question.

## UNKNOWNs

* **Whether anything at run time changes the colour**: the entity graph or Kismet could
  set a colour on the component. The shipped default is white; a script override is not
  decodable from these files and no game was launched (test ban).
* **Whether T-L17 should be BmAK-faithful at all**: the row's intent may be "give the
  graph preset a module row that matches JC3's own look". In that reading the built
  colour is a deliberate artist choice, not an error - but it is still not the BmAK value
  the row's `now` cell prints.
* **Brightness semantics**: BmAK's 0.0 does not map 1:1 onto JC3's `multiplier` /
  `min_luminosity`; the bridge is T-18's, not this audit's.

## Oracles re-run by `--check`

* PASS LIGHTS.json holds Playable_Batmobile_SF/BattleModeSpotLight/VEHLT_BattleModeLight
* PASS the light's component is SpotLightComponent export 5371
* PASS the grab records LightColor [255, 255, 255, 0]
* PASS the grab says the colour came from the class default, not the component
* PASS the other 7 fields are serialised on the component (7)
* PASS the archetype chain has no gaps
* PASS the shipped packages are on disk (Playable_Batmobile_SF.upk, Engine.upk)
* PASS export record word 6 (archetype) is 0 - the instance inherits straight from the class default
* PASS the component serialises 12 tags (12)
* PASS no tag on the component maps to LightColor
* PASS the component's serialised fields are the 7 around the colour
* PASS Default__LightComponent's CDO carries LightColor [255, 255, 255, 0]
* PASS resolve_component lands on the CDO colour with that source
* PASS Brightness 0.0 is serialised on the component itself
* PASS resolve_component reports no gap
* PASS LIGHTS.md prints that row with the CDO colour
* PASS LIGHTS.md states the precedence (component -> archetype -> Default__<class>)
* PASS grab_lights.py resolves in that same order (first source that carried the field)
* PASS bm_lightrig entry 11 is the T-L17 graph-object entry
* PASS the built diffuse is [0.6039, 0.6039, 0.9529]
* PASS all three channels cite the JC3 graph object `Front_Secondary_Head`
* PASS the built colour is not the BmAK colour (255/255 = 1.0, 1.0, 1.0)
* PASS T-18's row T-L17 already records the BmAK colour [255, 255, 255, 0]
* PASS the row also records brightness 0.0, radius 4500, outer cone 15
* PASS the ledger row T-L17 prints LightColor 255,255,255,0 in its 'now' cell
* PASS T-L17 is still `next` (the change is not applied)

## Labels

Decoded: the live package reads (archetype word, 12 tags, the 7 serialised fields, the CDO
colour), `LIGHTS.json` / `LIGHTS.md` / `bm_lightrig.json` / `t14_lights.json` / the ledger
cell. Derived: the run-time conclusion (white), the JC3 0..1 form, the change list.
UNKNOWN: the three items above.

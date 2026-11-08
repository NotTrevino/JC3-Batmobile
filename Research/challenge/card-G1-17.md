# Assumption challenge — G1-17 · Light colours, intensities and cones

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or either game install
was written; no game was launched; nothing was committed. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-17 card (§5, line 507) and its `Done` clause, the
§12 row (line 1285), `MODLOG.md` §"G1-17 · Light colours, intensities and cones — done" (line 8458),
the outputs `Research/BatmobileGrab/LIGHTS.md` (317 lines) / `LIGHTS.json` (schema 2, 276 KB), the
generator `Tools/scripts/grab_lights.py` (707 lines), the class dump `BMSDK_OFFSETS.json`, and the
grab `objects.jsonl` the values come from.

## VERDICT

**Every number reproduces, and three of the framing assumptions are materially wrong.** The gate is
green (`OK: 101 entries / 4 rigs …` + `OK: 36 Batmobile-rig components carry colour and intensity`),
the counts re-derive from the JSON, the BGRA reading survives a semantic test, and the class-default
chain is the right one for 74/74 referenced components. What does not hold:

* **19 of the 74 light components ship with `bEnabled` clear.** The card reads two shadow masks out of
  the very same `0x220` bool word and does not read mask 4 — so a third of the "intensity" column
  describes lights the asset has switched off (`ChainGunMuzzle` in all four rigs, `BattleModeSpotLight`
  ×2, `LWheelLight`, `HeadLight2` in three rigs). Whether code turns them on at run time is not in the
  grab; the artefact neither says nor flags it.
* **"colour 129/129, intensity 74/74" is gated on 36 components of one rig.** The check asserts the
  `Playable_Batmobile_SF` rig only (28 entries / 36 components = 28 % of 129); the other three rigs and
  the 129/74 totals are generated but never asserted.
* **"cast-shadow flags" is 2 of the 5 shadow masks in the word.** `CastStaticShadows` (mask 32) is set
  on 28 of 74 components and is not reported.
* **The §12 row's "1,786 truncated records" contradicts the MODLOG's measured "1,778 of 20,128".** One
  of the two numbers is wrong by 8.

| # | assumption | verdict |
|---|---|---|
| A1 | 101 entries over 4 rigs is every light rig the mod ships | **HOLDS** |
| A2 | a light's colour/intensity is `LightColor`/`Brightness`, full stop | **BROKEN** — 19/74 components have `bEnabled` = 0 |
| A3 | `FColor` is stored B,G,R,A (the BGRA reading) | **HOLDS** (brake-lamp role test decisive; alpha byte unexplained) |
| A4 | the two reported flags are "the cast-shadow flags" | **WEAK** — `CastStaticShadows` 28/74 unreported; 5 masks live in the word |
| A5 | 129/129 colour and 74/74 intensity are what `--check` proves | **WEAK** — the gate covers the SF rig only (36/129) |
| A6 | a lens flare's intensity may be "-" without breaking the `Done` | **WEAK** — true of the data, but it meets the clause by exclusion (17/36 in the checked rig) |
| A7 | the class-default fallback is the value the light would run with | **HOLDS** — 74/74 referenced lights have archetype 0; CDO values re-read match |
| A8 | export word 6 is the archetype | **HOLDS** — 0 on all 74 referenced, and 5 negatives resolve to real paths |
| A9 | "the five Xray instances point at `BmScript`" | **WEAK** — 4 of 5; the fifth points at a thug pawn in `BmGame.upk`, which ships |
| A10 | `MinStrength` ships nowhere and no shipped class derives from `LensFlareComponent` | **HOLDS** for the CDO; the subclass half is only consistent with the grab |
| A11 | every field carries its source string | **HOLDS** |
| A12 | "1,786 truncated records re-opened" (tracker) = "1,778 of 20,128" (MODLOG) | **BROKEN** — the two cannot both be right |
| A13 | "the 28 `Batmobile` rig entries" means the plain `Batmobile` rig | **HOLDS** by reading; **silent** (Funhouse and MK2 also have 28) |
| A14 | a type-stripped light's behaviour can be inferred from its socket name | **WEAK** — two components on one socket, both mapped `HeadLight`, colours contradict |
| A15 | radius, cone angle and `Brightness` need no unit | **WEAK** — no unit anywhere in the artefact; 0.15 vs 5.0 are not comparable to JC3's fields |
| A16 | the alpha byte in `[R,G,B,A]` needs no comment | **WEAK** — 255 on 14 lights, 0 on 60, never explained; JC3 `diffuse` is RGB |

Baseline, quoted once:

```
$ python Tools/scripts/grab_lights.py --check
{"entries": 101, "vehicles": 4, "components": 129, "components_with_colour": 129,
 "components_with_intensity": 74, "colour_sources": {"component": 67, "class default": 62}, …}
OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing bones
OK: 36 Batmobile-rig components carry colour and intensity (schema 2)
EXIT=0
```

---

## A1 · "101 entries over 4 rigs is the whole rig" — HOLDS

**Assumption.** The five-sample census in `grab_model.lights()` (`RVehicleBatmobile` objects, tags
named `VehicleLights`) catches every light the mod ships.

**Test.** Counted the owners and the struct tags in `objects.jsonl` across all 15 packages:

```
RVehicleBatmobile objects: {'Playable_BatmobileFunhouse_SF': 1, 'Playable_BatmobileJoker_SF': 1,
                            'Playable_BatmobileMK2_SF': 1, 'Playable_Batmobile_SF': 1}
VehicleLights struct tags: Funhouse 28, Joker 17, MK2 28, SF 28  -> total 101
```

**Result.** **HOLDS.** 101 is every `VehicleLights` struct on the four `RVehicleBatmobile` objects, one
per variant, and no other package (including the 11 `*_Std*` stubs) has an `RVehicleBatmobile`. The
Joker variant really is smaller (17 entries, 21 components).

## A2 · "Colour and intensity describe the light" — BROKEN (R5: name, not behaviour)

**Assumption (silent).** `LightColor` and `Brightness` are the light's colour and intensity, and the
`Done` clause ("every component … has colour and intensity") is therefore meaningful.

**Test.** The same `0x220` bool word the card already reads `CastShadows`/`CastDynamicShadows` from
carries 35 flags (`BMSDK_OFFSETS.json`, `LightComponent`). Decoded the word for all 74 light
components:

```
bEnabled              mask 4      set on 55/74      <- 19 lights shipped OFF
CastShadows           mask 16     set on 0/74
CastStaticShadows     mask 32     set on 28/74
CastDynamicShadows    mask 64     set on 28/74
bCastCompositeShadow  mask 128    set on 74/74
distinct bits values: 0x20200184 (29), 0x202001e4 (17), 0x20200180 (14),
                      0x200001e4 (6), 0x202001e0 (5), 0x20000184 (3)
```

and mapped the 19 off components to their entries:

```
Funhouse  HeadLight2           SpotLightComponent          [160,180,255,0]  0.0   OFF
Funhouse  ChainGunMuzzle       SpotLightComponent          [255,255,255,0]  1.0   OFF
Funhouse  BattleModeSpotLight  SpotLightComponent          [255,255,255,0]  0.0   OFF
Funhouse  LWheelLight          SpotLightComponent          [255,0,0,0]      0.0   OFF
Funhouse  BattleModeSpotLight  RHelicopterSpotLightComponent [195,255,244,0] 0.0  OFF
   … same set in Joker / MK2 / SF (19 of 74 in total)
```

**Result.** **BROKEN.** `LightColor` and `Brightness` are decoded correctly, but 19 of the 74
components are switched off in the shipped archetype, and the artefact does not read, print or flag
`bEnabled` — even though it reads two other masks from the identical word. The consequence for LGT-1
is concrete: the *wheel* light (`LWheelLight`, the LGT-1/LGT-2 target) is off, radius 0, brightness 0,
and its red `[255,0,0]` `BattleModeLight` row is a disabled component (the `BattleModeLight` rows of
`HeadLight1/2` are enabled and carry `[255,0,0]` at brightness 5.0, so the colour alone does not say
which rows are live). Whether BmAK's
code enables these at run time (ChainGunMuzzle on fire, battle lights when battle mode engages) is
**UNKNOWN** from the grab; the record states neither the flag nor that unknown.

## A3 · "`FColor` is B,G,R,A" — HOLDS

**Test 1 — the raw bytes.** Pulled the `LightColor` tag for the brake lamp and the headlights out of
`objects.jsonl` and applied the reader's conversion:

```
PointLightComponent   raw=0026ff00  bytes(B,G,R,A)=['00','26','ff','00']  -> [255, 38, 0, 0]  red
SpotLightComponent    raw=f6c58aff  -> [138, 197, 246, 255]              cool white
SpotLightComponent    raw=0000ff00  -> [255, 0, 0, 0]                    pure red
SpotLightComponent    raw=4b5bdf00  -> [223, 91, 75, 0]                  warm red
```

**Test 2 — the semantic role.** A brake lamp must be red. Under the BGRA reading the brake lamp is
`[255,38,0]`; read as R,G,B it would be `[0,38,255]`, a blue brake light. The forensics scan lights
likewise land on `[255,0,0]` (red) instead of blue.

**Result.** **HOLDS** — the byte order is carried by the engine's documented `FColor` layout (the card
quotes UEViewer `UnCore.h`) and confirmed by the brake/forensics roles. Caveat: the test is decisive
only where the role is colour-coded; for the cool-white rows both readings are visually plausible
(`[138,197,246]` vs `[246,197,138]`), so a per-row sanity check would not catch an error. The raw bytes
are still in `objects.jsonl`, so the conversion stays re-checkable.

## A4 · "`CastShadows` + `CastDynamicShadows` are the cast-shadow flags" — WEAK

**Assumption (stated).** The component table's two shadow columns answer the card's "cast-shadow
flags".

**Test.** Enumerated the shadow-class flags in `BMSDK_OFFSETS.json` at `0x220` and counted each set bit
over the 74 lights (output in A2).

**Result.** **WEAK.** The two reported masks are read correctly (CastShadows 0/74, CastDynamicShadows
28/74, and the md's `False`/`True` pattern matches the bits exactly), but the word holds five
shadow-related flags and one of them — `CastStaticShadows` (mask 32) — is set on **28 of 74**
components and is not in `LIGHT_FIELDS`. `bCastCompositeShadow` (128) is set on all 74. "Cast-shadow
flags" plural is therefore only half answered, and a translator choosing JC3 `cast_shadows` cannot see
that static shadows are requested on the same lights the dynamic flag names.

## A5 · "129/129 and 74/74 are what the gate proves" — WEAK

**Assumption (stated).** MODLOG: "**Result.** … colour on **129/129** … intensity on all **74** light
components … **Verified:** `grab_lights.py --check`".

**Test.** Read the check: it selects `next(v for v in doc["vehicles"] if v["package"] ==
"Playable_Batmobile_SF")`, requires `len(entries) == 28`, then iterates that rig's components into
`checked` and prints `OK: %d Batmobile-rig components` = **36**. The summary's
`components_with_colour`/`components_with_intensity` are computed over all four rigs but never
compared.

```
per rig: Funhouse 28 entries / 36 comps (19 lights, 17 flares), colour 36/36, intensity 19/19
         Joker    17 / 21 (17 lights,  4 flares), colour 21/21, intensity 17/17
         MK2      28 / 36 (19 lights, 17 flares), colour 36/36, intensity 19/19
         SF       28 / 36 (19 lights, 17 flares), colour 36/36, intensity 19/19
totals: 101 / 129 components, colour 129, intensity 74   (recomputed: identical)
```

**Result.** **WEAK.** 36 of 129 components (28 %) are gated; a regression that lost the colour of, say,
every Joker component would leave `--check` green and the summary at 108/129 without a FAIL. The
figures are R11-safe in the sense that they are derived from the data, but the *claim* "129/129 colour"
is a generated count, not a verified one — the MODLOG puts it under "Verified", which over-states what
the command does. The card's own `Done` names only the 28 `Batmobile` rig entries, so the gate matches
the card; the mismatch is in the MODLOG/§12 wording, not the gate.

## A6 · "A lens flare has no intensity, so `-` is fine" — WEAK

**Assumption (stated).** "A lens flare is not a light: it has no `Brightness` … its only strength field
`MinStrength` ships nowhere … so its intensity is a stated gap".

**Test.** Checked the CDO and the artefact:

```
$ class_defaults('LensFlareComponent') -> {'SourceColor': ([1.0,1.0,1.0,1.0], Engine.upk)}
flare rows: 55 | colour: all (1.0, 1.0, 1.0, 1.0) | intensity source:
   'not serialised anywhere in the install (native default)' × 55
SF rig: 36 components = 19 lights + 17 flares -> 17 of the 36 checked components have no intensity
```

**Result.** **WEAK.** The data claim is right (`Default__LensFlareComponent` carries only `SourceColor`,
so `MinStrength` really is native-only), and the md says so per row. But the card's `Done` is "has
colour and intensity **or `class default` with the default stated**": for 17 of the 36 components in
the checked rig no default value is stated, only "not serialised anywhere". The clause is met by
excluding flares from "component … intensity", which is a scope decision the record argues for but
does not label as a reading of the Done. Also note the 55 flare colours are all the CDO
`[1,1,1,1]`: they carry no per-instance information, so "colour 129/129" is materially 74 light
colours (67 decoded + 7 white CDO) + 55 identical defaults.

## A7 · "The class-default fallback is the value the light runs with" — HOLDS

**Assumption (stated).** A field the component does not serialise is resolved `component → archetype →
Default__<class>`, and the CDO value is what the instance inherits.

**Test.** Re-ran the resolver's own CDO step (read-only) for every class in play:

```
LightComponent   -> Brightness 1.0, LightColor [255,255,255,0], CastShadows True,
                    CastDynamicShadows True                      (Engine.upk)
PointLightComponent -> Radius 1024.0, FalloffExponent 2.0, Brightness 1.0, LightColor [255,255,255,0]
SpotLightComponent  -> OuterConeAngle 44.0, Radius 1024.0, FalloffExponent 2.0, Brightness 1.0 …
RHelicopterSpotLightComponent -> same set (Engine.upk)
```

and compared with the 62 "class default" colour cells and 20 intensity cells in the artefact: all say
`CDO Default__<class> (Engine.upk)` with exactly those values (`[255,255,255,0]`, `1.0`, `1024.0`,
`44.0`, `2.0`).

**Result.** **HOLDS.** The chain is right (see A8: every referenced component's archetype is 0, so the
class default *is* the inherited value) and the printed numbers match the CDOs byte for byte. The
`InnerConeAngle`-is-native claim also holds: `SpotLightComponent`'s CDO carries `OuterConeAngle` but
no `InnerConeAngle`, which is why 32 light components have `-` there.

## A8 · "Export word 6 is the archetype" — HOLDS

**Test.** Called the reader's `archetype_ref` / `archetype_target` on the components themselves:

```
referenced light components: 74 | archetype 0: 74 | negative: 0 | local export: 0
unreferenced light-class components: 5
  Playable_BatmobileFunhouse_SF PointLightComponent idx 5111 archetype=-485
     -> ('BmScript', 'Default__RVehicleBatmobile.XrayLightComponent')
  Playable_BatmobileJoker_SF    PointLightComponent idx 2971 -> ('BmScript', 'Default__RVehicleBatmobile.XrayLightComponent')
  Playable_BatmobileJoker_SF    SpotLightComponent  idx 3273 -> ('BmGame',  'Default__RPawnVillainThug.XrayLightComponent')
  Playable_BatmobileMK2_SF      PointLightComponent idx 5072 -> ('BmScript', 'Default__RVehicleBatmobile.XrayLightComponent')
  Playable_Batmobile_SF         PointLightComponent idx 5021 -> ('BmScript', 'Default__RVehicleBatmobile.XrayLightComponent')
```

**Result.** **HOLDS.** The field behaves exactly as an archetype reference: 0 (class default) on all 74
referenced components, and negative import indices on the five leftovers that resolve to coherent
outer-class paths. This is the independent check the chain needed; without it the whole "archetype then
CDO" logic would rest on a reading of a 72-byte record.

## A9 · "The five Xray instances point at `BmScript`" — WEAK

**Assumption (stated).** MODLOG: "the five `XrayLightComponent` instances point at
`BmScript.Default__RVehicleBatmobile.XrayLightComponent`, and **BmScript ships no file** — those are
recorded as chain gaps".

**Test.** The five archetype targets, quoted above.

**Result.** **WEAK.** Four of the five point at `BmScript.Default__RVehicleBatmobile.XrayLightComponent`
(a package with no file — correct); the fifth (`Playable_BatmobileJoker_SF` `SpotLightComponent` 3273)
points at **`BmGame.Default__RPawnVillainThug.XrayLightComponent`**, and `BmGame.upk` *does* ship (the
reader reads its CDOs, A7). So "five … BmScript" is off by one, and the odd one is not even a
Batmobile archetype — it is a thug pawn's x-ray light copied into the Joker package. None of the five
is referenced by a `VehicleLights` entry, so no value in the artefact depends on it; the error is in
the record's account of its own chain. "Recorded as chain gaps" is also not visible in `LIGHTS.json`
(`component_gaps` 0, no `Xray` string in the file) — it exists only in the MODLOG prose.

## A10 · "`MinStrength` ships nowhere; no shipped class derives from `LensFlareComponent`" — HOLDS (first half), UNVERIFIED (second)

**Test.** `class_defaults('LensFlareComponent')` returns only `SourceColor`; `objects.jsonl` contains 55
objects of class `LensFlareComponent` and no other *Flare* class.

**Result.** **HOLDS** for `MinStrength` (nothing in the shipped CDO carries it). The "no shipped class
derives from it" half is only consistent with the grab's class census — the install's full class table
is not something the reader enumerates — but nothing in the artefact depends on it beyond the `-` in the
intensity column, which is already justified by the CDO.

## A11 · "Every field carries its source" — HOLDS

**Test.** Counted `field_sources` coverage over all 129 components:

```
LightColor          present 74  none  0   {component 67, class default 7}
Brightness          present 74  none  0   {component 54, class default 20}
Radius              present 74  none 55   {component 50, class default 24, not serialised 55}
InnerConeAngle      present 42  none 32   {component 42, not serialised 32}
OuterConeAngle      present 65  none  9   {component 57, class default 8, not serialised 9}
FalloffExponent     present 74  none  0   {component 36, class default 38}
CastShadows         present 74  none  0   {component 74}
CastDynamicShadows  present 74  none  0   {component 74}
SourceColor         present 55  none  0   {class default 55}
MinStrength         present  0  none 55   {not serialised 55}
entries with any gap: 0
```

**Result.** **HOLDS.** Every field of every component has a source, and the three source kinds
(component / class default / not serialised) are exactly the ones the prose claims. This is the
strongest part of the record: no value in `LIGHTS.json` is unattributed.

## A12 · "1,786 truncated records" vs "1,778 of 20,128" — BROKEN (number)

**Assumption (stated twice, differently).** §12 row: "the walker's 32-byte GuidProperty fix re-opened
**1,786** truncated records". MODLOG: "**1,778** of 20,128 records".

**Test.** Re-derived the census the numbers hang on, from `objects.jsonl`:

```
objects.jsonl rows: 20128 | with a decoded tag stream: 19203 | without: 925
MODLOG claims: 20,128 exports | 19,203 readable | 925 untagged
```

**Result.** **BROKEN** as a pair: the census re-derives exactly (20,128 / 19,203 / 925), so the MODLOG's
setting is right, but its "1,778" and the tracker's "1,786" describe the same event with an 8-record
difference. Nothing on disk can re-decide which is correct (the fix is already in; the pre-fix count is
gone), so the honest fix is to mark the re-opened count as measured once (1,778, as the MODLOG's own
sentence says) and drop the unsourced 1,786 from §12 — or to state where each number came from. As it
stands the tracker quotes a number the record contradicts.

## A13 · "The 28 `Batmobile` rig entries" — HOLDS by reading, silent ambiguity

**Test.** Entry counts per rig: Funhouse 28, Joker 17, MK2 28, **SF 28**.

**Result.** **HOLDS** for the gate, which selects `Playable_Batmobile_SF` (the plain
`Batmobile_Archetypes.Vehicle`), and that rig has exactly 28 entries / 36 components. But three of the
four rigs have 28 or 17 entries and two also have 28, so "the 28 `Batmobile` rig entries" is ambiguous
between Funhouse/MK2/SF; the record never says which rig it picked. Silent, not wrong.

## A14 · "Type-stripped behaviour may be inferred from the socket name" — WEAK

**Assumption (stated).** For the 12 entries whose `Type` enum the cooker stripped, behaviour comes from
`_socket_behavior(socket)` — `"head"` → `HeadLight`, `"brake"` → `TailLight`, `"wheel"` → `TailLight`,
`"signal"`/`"reverse"` by name.

**Test.** Looked at what sits on those sockets. Each typed `HeadLight1` entry already has a cool-white
spot (`[138,197,246]`, radius 6000/1800); the type-stripped entry on the *same* socket is a second
`SpotLightComponent` with a warm red colour and pure class defaults for everything else:

```
SF  HeadLight1  -  SpotLightComponent  [223, 91, 75, 0]  bright 1.0  radius 1024.0  inner -  outer 44.0
```

**Result.** **WEAK.** The inference is disclosed per row ("inferred from socket name (type stripped by
the cooker)"), but two components on one socket are both mapped to the JC3 `HeadLight` behaviour with
different colours, and the artefact gives no way to tell which one renders — or whether the warm
`[223,91,75]` component is actually a marker/x-ray light (both `bXrayLight` bits are clear on every
component, so the grab does not support that either). This is the R5 shape the rules warn about: a
behaviour taken from the member's (socket's) name where the mechanism is unknown. "UNKNOWN behaviour
for 12 type-stripped entries" would be the R4-safe row.

## A15 · Units and conventions — WEAK

**Assumption (silent).** `radius`, `inner cone`, `outer cone` and "intensity" are usable numbers as
printed.

**Test.** Searched the artefact for any unit statement (`grep -in 'units\|degrees\|cm\|metre' LIGHTS.md`)
— none; and looked at the values: radius 0.1 / 80 / 150 / 400 / 1024 / 1800 / 3072 / 4096 / 4500 /
6000; cones 5 / 10 / 15 / 20 / 35 / 44 / 45 / 50 / 60 / 70; brightness 0.0 / 0.15 / 0.2 / 0.4 / 1.0 /
4.0 / 5.0.

**Result.** **WEAK.** The magnitudes are consistent with Unreal units (cm; the CDO radius 1024 is UE3's
default) and degrees (the CDO outer cone 44), so the numbers are almost certainly cm/degrees — but the
file never says so, and `Brightness` is renamed "intensity" with no unit at all (UE3 brightness is a
unitless multiplier; it is not lumens, and it is not JC3's `multiplier`/`range`). T-18 must supply
units and a mapping, and the artefact gives it neither. At 6000 units the headlight's range is 60 m if
cm; that is an inference, not a decode.

## A16 · The alpha byte — WEAK (silent)

**Test.** Counted the fourth component of every light colour:

```
light colour alpha values: {255: 14, 0: 60} of 74
alpha 255 rows: the two typed HeadLight1 spots (6000/1800 radius) and the forensics lights
```

**Result.** **WEAK.** `FColor` alpha is unused by UE3 lights, and the artefact prints `[R,G,B,A]` without
saying so; a consumer that carries the four numbers into JC3's `diffuse` (three floats in the vanilla
table) would either drop a real channel or carry a meaningless 0. The split (255 exactly where the
cook wrote a full colour constant) suggests it is a cooking artefact, but that is my inference, not the
record's.

---

## What this challenge could not test

* **Whether the 19 disabled lights are switched on at run time.** `bEnabled` is the archetype's state;
  BmAK's scripts/kismet could enable `ChainGunMuzzle` on fire or the battle lights on mode change. No
  decoded script in the grab names a light component, so this is **UNKNOWN**, and the record should say
  so rather than imply the values are live.
* **Which of the two components on `HeadLight1`/`HeadLight2` renders** (A14). Both are plain
  `SpotLightComponent`s in the same package; only the colour and radius differ.
* **The pre-fix truncation count** (A12): the guid fix is already applied, so 1,778 vs 1,786 cannot be
  re-measured, only reconciled against the surviving census.
* **The full class table** (A10's subclass claim): the reader enumerates exports, not the engine's class
  hierarchy.
* Everything above was measured on files on disk with read-only probes of `E:\Games\Batman - Arkham
  Knight\BmGame\CookedPCConsole` (the same packages the generator opens); no game was launched, nothing
  under either game install was written, and nothing was committed.

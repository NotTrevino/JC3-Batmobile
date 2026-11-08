# Review — G1-17 · Light colours, intensities and cones

Reviewer: independent (did not write the card). Date 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5, the G1-17 card (§6, lines 507–517), the §12 row (line 1285),
`MODLOG.md` §"2026-10-25 · G1-17 … done" (lines 8458–8528), `Research/BatmobileGrab/LIGHTS.md`,
`Research/BatmobileGrab/LIGHTS.json`, `Tools/scripts/grab_lights.py`, and the raw inputs the
script reads (`objects.jsonl`, `BMSDK_OFFSETS.json`, `Engine.upk` / `BmGame.upk` via
`upk_read.py`, `Working/Lights/serpente_lights.xml`).
Read-only: no file under `Research/`, `Tools/`, `GRAB_BACKLOG.md`, `MODLOG.md`, `Working/`,
`Builds/` or the game install was written; no game was launched. This report is the only file
written.

## VERDICT

**minor issues** — the card's substance holds: `grab_lights.py --check` passes, both Out paths
exist, `LIGHTS.json` **and** `LIGHTS.md` are byte-identical to a fresh rebuild (no stale doc, no
hand-typed numbers), and every decoded value I traced back to the raw tag was right, including
the BGRA `FColor` reading. What is wrong is the **record and wording around the data**, not the
data: one number in the §12 row contradicts the MODLOG and the data (1,786 vs the measured
1,778), the check's own success line claims intensity on components that have none, the doc makes
two claims the data contradicts (the flare CDO's contents, "every entry is needs-lig-bone"), and
`--check` only gates 36 of the 129 components it is used to vouch for. All fixes are one-line
wording/number corrections plus a wider assertion in `--check`; **no value has to be re-derived
and the card does not need redoing**.

## Check output (verbatim)

Command (from `E:/Modding/JC3-Batmobile`):

```
python Tools/scripts/grab_lights.py --check
```

Output (exit status 0):

```
{
 "entries": 101,
 "vehicles": 4,
 "components": 129,
 "components_with_colour": 129,
 "components_with_intensity": 74,
 "colour_sources": {
  "component": 67,
  "class default": 62
 },
 "intensity_sources": {
  "component": 54,
  "not shipped": 55,
  "class default": 20
 },
 "component_gaps": 0,
 "by_component_class": {
  "SpotLightComponent": 61,
  "LensFlareComponent": 55,
  "PointLightComponent": 9,
  "RHelicopterSpotLightComponent": 4
 },
 "orphan_sockets": 6,
 "missing_bones": 0,
 "by_type": {
  "VEHLT_HeadLight": 46,
  "(stripped)": 12,
  "VEHLT_TailLight": 8,
  "VEHLT_BattleModeLight": 16,
  "VEHLT_ForensicsLight": 12,
  "VEHLT_Interior": 4,
  "VEHLT_BootLight": 3
 },
 "by_behavior": {
  "HeadLight": 70,
  "(none)": 16,
  "TailLight": 15
 },
 "by_disposition": {
  "mapped": 54,
  "no-jc3-equivalent": 16,
  "inferred from socket name (type stripped by the cooker)": 8,
  "approximated": 23
 },
 "by_part": {
  "sportsmuscle_body": 77,
  "sportsmuscle_wheel_f_l": 14,
  "sportsmuscle_wheel_f_r": 10
 }
}
OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing bones
OK: 36 Batmobile-rig components carry colour and intensity (schema 2)
```

Extra freshness test (read-only, nothing written): `grab_lights.build()` compared to
`LIGHTS.json` on disk → **identical**; `write_md()` rendered into memory compared to
`LIGHTS.md` on disk → **identical** (317 lines both). So the check is re-deriving the data that
produced the two Out files, not a newer/older state.

## Issues

### 1. §12 row quotes a number that no command produces, and the MODLOG disagrees with it (wrong number)

- `GRAB_BACKLOG.md:1285`: "the walker's 32-byte GuidProperty fix re-opened **1,786** truncated
  records".
- `MODLOG.md:8463`: "**1,778** of 20,128 records".
- `Tools/scripts/upk_read.py:44` (the fix's own comment): "All **1,778** guid-bearing records in
  objects.jsonl desynced at the guid before this".
- Measured now: `objects.jsonl` holds 20,128 records, of which **exactly 1,778** contain a
  `GuidProperty` tag.

1,786 appears nowhere else in the repo and cannot be derived by any tool; the other two places and
the data all say 1,778. Fix the §12 row to 1,778 (R11: counts are generated, not typed; R14).

### 2. The check's success line claims intensity on 17 components that have none (false statement used as evidence)

`Tools/scripts/grab_lights.py:702` prints

```
OK: 36 Batmobile-rig components carry colour and intensity (schema 2)
```

but the 36 base-rig components are 17 × `LensFlareComponent`, 16 × `SpotLightComponent`,
2 × `PointLightComponent`, 1 × `RHelicopterSpotLightComponent`. All 17 flares have
`intensity.value = null` with source "not serialised anywhere in the install (native default)" —
the check explicitly skips them (`grab_lights.py:684–691`). **Only 19 of the 36 carry an
intensity.** `MODLOG.md:8521–8522` and the §12 row quote this line as the card's evidence, so the
record currently states something 17/36 false. The surrounding MODLOG body is careful
("intensity on all 74 light components", "its intensity is a stated gap") — only this one line
(and its two quotations) overstates. Reword to e.g. "36 components carry colour; 19 carry
intensity; 17 are flares with no intensity field".

### 3. The card's Done criterion is not what `--check` actually verifies (scope gap)

Card (`GRAB_BACKLOG.md:516–517`): "`grab_lights.py --check` passes; every component of the 28
`Batmobile` rig entries has colour and intensity **or `class default` with the default stated**."

- The 28/36 scope is enforced (`grab_lights.py:667`), and colour is enforced for all 36.
- Intensity is **not** required for flare components — a defensible exemption (a flare has no
  `Brightness`), but it is a deviation from the card's literal "every component", documented only
  in a code comment, not in the card. The card should be amended to say "colour on every
  component, intensity on every non-flare component", otherwise the next agent reading the card
  will think the Done was met literally.
- "or `class default` with the default stated" is not tested at all: the check only asserts the
  source string is non-`null`, never that it names a `Default__` object, and never that the md
  renders it (the md's `-` cells are not re-read). Nothing in the check would notice a source
  string being lost from the table while `LIGHTS.json` stayed right.
- The `129/129` colour and `74/74` intensity figures in the §12 row are only **printed** from the
  summary; the assertions run on the base rig only. A colour lost in `Playable_BatmobileJoker_SF`
  (93 of the 129 components are unchecked) would still exit 0. If the row is going to quote
  129/129 and 74/74, `--check` should assert them.

### 4. LIGHTS.md says the flare CDO "carries only PerInstanceRandom" — the data contradicts it, and so does the doc's own table

`LIGHTS.md:179–180` (generated from `grab_lights.py:596–597`): "`Default__LensFlareComponent`
carries only `PerInstanceRandom`, and no shipped class derives from `LensFlareComponent`".

- Walked directly (`Engine.upk`, export 23369): the CDO serialises **8** tags —
  `SourceColor` (0x254), `ReplacementPrimitive`, `TickGroup`, `PerInstanceRandom` (0x16c float),
  and four boolean words at 0x74 / 0x1dc / 0x1e0 / 0x23c.
- The doc's own table takes every flare colour **from that same CDO** ("CDO
  `Default__LensFlareComponent` (Engine.upk)"), so the sentence contradicts the table it
  introduces.
- The load-bearing claim is true and verified: `MinStrength` is at 0x250 in the BmSDK dump and
  **no** `Default__LensFlareComponent` tag and **no** flare component tag carries 0x250, so a flare
  intensity really is unshipped.
- "no shipped class derives from `LensFlareComponent`" is an unsupported negative: the only
  evidence on disk is the 41-class vendored `BMSDK_OFFSETS.json` (which naturally has no such
  subclass in its subset), not a scan of the install's class list. It is harmless here — all 55
  flares are exactly `LensFlareComponent` — but per R4 it should be `UNKNOWN` or cite a scan.

Fix the sentence to what was measured: "`Default__LensFlareComponent` serialises `SourceColor`,
`ReplacementPrimitive`, `TickGroup`, `PerInstanceRandom` and four bool words; `MinStrength` (0x250)
is not serialised by it or by any of the 55 flare components."

### 5. LIGHTS.md:5 says "every entry is `needs-lig-bone`" — 6 are orphans, as the same doc states six lines later

`LIGHTS.md:5`: "…which is why every entry is `needs-lig-bone` (LGT-1)". Measured:
95 entries `needs-lig-bone`, **6** `orphan-socket: no bone, cannot place` (the doc's own
"Problems" list, `LIGHTS.md:28–33`). Cosmetic, but it is a factual claim contradicted by the file.

### 6. The `-` legend conflates "not a field of this class" with "field exists but is not serialised"

`LIGHTS.md:176–177`: "`-` means no shipped object serialises that field: the value is the native
default, which is compiled into the executable and appears in no file."

Two different things print `-`:

- a property that **does** exist but no shipped object serialises — e.g. `SpotLightComponent`
  `Radius`/`InnerConeAngle`, `LensFlareComponent` `MinStrength` (verified: 0x250 never present);
- a property the class **does not have at all** — e.g. `OuterConeAngle`/`InnerConeAngle` on
  `PointLightComponent` (`BrakeLightL`/`BrakeLightR`). Cones are `SpotLightComponent` fields
  (`BMSDK_OFFSETS.json`: 732/736); a point light has no "native default cone angle", the field
  does not exist on it.

No cell is wrong, but the legend is, and a reader is told an inapplicable field is a compiled-in
default. Split the legend into "not serialised (native default)" vs "not a field of this class".

### 7. `CastShadows` / `CastDynamicShadows` are printed side by side without any reading, and the combination needs one

Measured over the 74 light components: `CastShadows` is **True on 0 of 74**, `CastDynamicShadows`
is **True on 28**. The bits come from one word (offset 0x220): ordinary lights carry `0x20200184`
(mask 4 `bEnabled`, 128, 256, 2 097 152, 536 870 912), the 28 carry `0x202001E4` (+64
`CastDynamicShadows`, +32 `CastStaticShadows`). So the master `CastShadows` bit (16) is clear on
every light while the "dynamic shadows" bit is set on 28 of them.

The table puts those two booleans in adjacent columns with no note, which reads as "these 28 lights
cast dynamic shadows". Whether the master bit gates the other two is not established anywhere in
this card, and `CastStaticShadows` — set on the same 28 components — is not extracted at all
(`LIGHT_FIELDS`, `grab_lights.py:60–61`, omits it). Two fixes, both cheap: record the shadow
triple, and mark the reading `UNKNOWN` (or cite a take) instead of leaving the reader to infer a
behaviour from a member name (R5).

### 8. "Gaps in the component chain: none." is true only for the 129 referenced components

`LIGHTS.md:315` prints "none." from `component_gaps = 0`. The grab holds **134** light components;
the 5 additional `XrayLightComponent` instances (e.g. `Playable_Batmobile_SF` 5021,
`Playable_BatmobileJoker_SF` 2971 / 3273, `Playable_BatmobileMK2_SF` 5072,
`Playable_BatmobileFunhouse_SF` 5111) point at
`BmScript.Default__RVehicleBatmobile.XrayLightComponent` and have no file behind that package —
exactly the chain gap the MODLOG says is "recorded". It is not in `LIGHTS.json` at all, because
those instances appear in no `VehicleLights` entry. The number is right; the absolute wording is
not. Add "none among the 129 components the rig references (5 further Xray components in the grab
are unreferenced and carry the BmScript gap)".

### 9. Minor / not blocking

- `LIGHT_FIELDS`/table cover `CastShadows`, `CastDynamicShadows` but not `CastStaticShadows`
  (see §7). The card says "cast-shadow flags", so this is incomplete rather than wrong.
- The 23 `approximated` behaviours (`VEHLT_Interior` → `TailLight`, `VEHLT_BootLight` →
  `TailLight`, `VEHLT_BattleModeLight` → `HeadLight`, `RHelicopterSpotLightComponent` → plain
  spotlight) are labelled as approximations, which is honest, but no behaviour take exists yet —
  they are member-name choices awaiting a test in T-18. That is in-scope for G1-17 as written, but
  T-18 should not treat these as settled (R5).
- `MODLOG.md:8504` says "all 134 light components now walk to `eof`"; 132 stop `eof`, 2 stop
  `end`. Zero unresolved tags on all 134 (checked), so the substance is right; the word "eof" is
  not literal for 2 records.

## Spot-checks

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | `BrakeLightL` colour `[255, 38, 0, 0]` (`LIGHTS.md:172` region) | `objects.jsonl`, `Playable_Batmobile_SF` index **5019**, tag `LightColor` offset 512, `raw: "0026ff00"` → BGRA b=0x00, g=0x26(38), r=0xff, a=0x00 | **match.** Also the case that settles the byte order: read as RGBA the brake lamp would be `[0,38,255]`, i.e. blue. |
| 2 | `HeadLight1` (base) colour `[138, 197, 246, 255]`, intensity `0.15`, radius `6000.0`, inner `20.0`, outer `70.0` | same file, index **5365**: `LightColor raw "f6c58aff"`; float tags 496 = 0.15, 616 = 6000.0, 732 = 20.0, 736 = 70.0; `BMSDK_OFFSETS.json` maps 496 `Brightness`, 616 `Radius`, 732 `InnerConeAngle`, 736 `OuterConeAngle` (`LightComponent`/`PointLightComponent`/`SpotLightComponent`) | **match**, and the offset→name mapping is right, not just the numbers. |
| 3 | `BrakeLightL` intensity `1.0` "CDO `Default__LightComponent` (Engine.upk)" | `Engine.upk` export **11730** (`Default__LightComponent`): float at 496 = **1.0**, `LightColor raw "ffffff00"` (= `[255,255,255,0]` in the same BGRA reading) | **match**; the MODLOG's stated class defaults hold. |
| 4 | Summary: `entries 101`, `components 129`, `colour_sources component 67 / class default 62`, `intensity_sources 54 / 20 / 55` | `Research/BatmobileGrab/LIGHTS.json` `summary`, compared with a fresh `grab_lights.build()` → byte-identical document | **match**; every number in the doc's Summary table and prose is the script's, none typed (R11). |
| 5 | Vanilla `HeadLight` reference: range `2.0`, angle `10.0`, diffuse `[1.0, 1.0, 1.0]` (`LIGHTS.md:46–50`) | `Working/Lights/serpente_lights.xml`, 21 `Structure` blocks (the doc's "21 entries"), `HeadLight` aggregate | **match.** |
| 6 | `-` for `MinStrength` / flare radius: "no shipped object serialises it" | tags of `Default__LensFlareComponent` (Engine.upk 23369) and of all 55 flare components contain no offset 592 (`MinStrength`) and no 588 (`Radius`) | **match** for the flare geometry; only the "carries only `PerInstanceRandom`" wording is wrong (§4). |

Additional checks that came out clean: 129 component references (no duplicate `(package, index)`),
md component table 36 + 36 + 36 + 21 = 129 rows, 0 unresolved tag offsets across all 134 light
components, `BMSDK_OFFSETS.json` = 41 classes, `GRAB_BACKLOG.md` §12 status `done` with the card's
Out paths present.

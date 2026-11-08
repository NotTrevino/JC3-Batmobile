# Keep-audit: lights — 28 BmAK entries vs the 18 built B-07 rows

Scope: ledger rows **T-LG1, T-LG2, T-LG3, T-LG6** (all `keep`). The card's premise is right and
T-LG2 is not the test: `t2_lg2.py` proves the built entity is row-for-row the **donor's**, which is
a statement about JC3's own data, not about BmAK. This report measures the second thing — what
happened to the **28 BmAK light entries**.

Labels: **decoded** = read from bytes/JSON at a stated path; **derived** = arithmetic on decoded
values with the rule shown; **UNKNOWN** = not decoded, with what would settle it.

## 1. Verdict

| question | answer | label |
|---|---|---|
| BmAK entries per rig | **28** (4 rigs, 101 entries) | decoded (`LIGHTS.json` `vehicles[]`) |
| JC3 rows built in B-07 | **18** (21 donor rows − 10 dropped + 7 added) | decoded (`Builds/bm-007` module, re-read) |
| BmAK entries with a lamp that JC3 carries | 18 of 28 | derived |
| entries carried **exactly** (every authored quantity equal) | **0** | derived |
| entries whose **colour alone** is bit-exact | **13** | derived |
| entries carried **approximately** | **5** | derived |
| entries **not carried** | **10** | derived |

The count that matters: **0 of 28 BmAK lights is reproduced.** Thirteen lights have their colour
carried to the last bit and nothing else; five are approximated; ten are absent. The reason is
structural, not sloppy: JC3's light entry has no member for BmAK's `Brightness`, no inner cone, and
its `range`/`angle` units have no bridge (`Research/JC3Grab/LIGHT_SYSTEM.md` §8, quoted below), so
B-07 deliberately **kept the donor's numbers** for `range`, `angle`, `multiplier`, `falloff_start`,
`near_cap`, `min_luminosity`, `blinking`, `cast_shadows`, `volumetric_mode` and `uvscale` and
converted only the colour (`LightColor/255`).

So T-LG6's "30 / 40 on the 5 spots" is not a BmAK result. 30 and 40 are two of the donor's own
values; BmAK's headlight is **radius 6000, cone 20/70**. T-LG6 closed the row on the number being
*inside the fleet band*, which is the exact substitution STAGES.md forbids.

## 2. Evidence and method

| input | what it gives |
|---|---|
| `Research/BatmobileGrab/LIGHTS.json`, `vehicles[3]` = `Playable_Batmobile_SF` | the 28 entries, each with `socket`, `type`, `bone`, `jc3_anchor`, and per-component `InnerConeAngle`, `OuterConeAngle`, `Radius`, `FalloffExponent`, `Brightness`, `LightColor` (decoded; `grab_lights.py`) |
| `Working/Translation/t14_lights.json` | the T-18 mapping, entry *i* ↔ row `T-L(i+8)` |
| `Tools/scripts/bm_lightrig.py` `plan()` + `decode_module()` | the 18 built rows, member by member, re-derived from `Builds/bm-007`'s `.vmodc` (not from a receipt) |
| `Research/JC3Grab/LIGHT_SYSTEM.md` §1/§8 | the 25 entry members, the fleet value domains, the UNKNOWNs (units, `preset_id`, `light_type`) |

The built rows were re-derived twice in this session (`bm_lightrig.plan()` run twice, identical
output) and cross-checked against the module bytes. `bm_lightrig.py --check` was also run: it
reports `rows 18 (base 21, dropped 10, added 7)` and then **fails** on an unrelated file
(`…civilian_01.epe` differs from the base build). That failure is pre-existing in `bm-007` and is
noted here, not repaired: no file under `Builds/` was touched by this audit.

## 3. Per-BmAK-light table

`r`= JC3 `range`, `a`= `angle`, `m`= `multiplier`; `diff` = JC3 `diffuse` triple. BmAK `rad` is the
component `Radius` in UE units (cm — derived from UE3's convention, no file states it); `cone` is
`InnerConeAngle/OuterConeAngle` in degrees (decoded).

| # | row | socket | BmAK class | BmAK colour (R,G,B,A) | bri | cone | rad | fall | built row(s) → r/a/m, diff | verdict |
|---:|---|---|---|---|---:|---|---:|---:|---|---|
| 0 | T-L8 | `HeadLight1` | Spot | 138,197,246,255 | 0.15 | 20/70 | 6000 | 1 | 2 → 30/40/2, .541 .773 .965 · 5 → 2/10/1, same | colour exact |
| 1 | T-L9 | `HeadLight2` | Spot | 160,180,255,0 | 0.00 | 10/35 | 0.1 | 1 | 9 → 2/10/1, .627 .706 1.0 · 10 → 30/40/2 | colour exact |
| 2 | T-L10 | `ChainGunMuzzle` | Spot | 255,255,255,0 | 1.0 | –/50 | 4096 | 1 | **none** | **not carried** |
| 3 | T-L11 | `HeadLight1` | Spot | 223,91,75,0 | 1.0 | –/44 | 1024 | 2 | 4 → 30/40/2, .875 .357 .294 · 7 → 2/10/1 | colour exact |
| 4 | T-L12 | `HeadLight2` | Spot | 223,91,75,0 | 1.0 | –/44 | 1024 | 2 | 3 → 2/10/1 · 6 → 30/40/2 | colour exact |
| 5 | T-L13 | `LWheelLight` | Spot | 160,180,255,0 | 0.00 | –/0 | 0 | 1 | 12 (custom, `preset_id 0`) → 2/10/1 | colour exact |
| 6 | T-L14 | `RWheelLight` | Spot | 160,180,255,0 | 0.00 | –/0 | 0 | 1 | 13 (custom) → 2/10/1 | colour exact |
| 7 | T-L15 | `BrakeLightL` | **Point** | 255,38,0,0 | 1.0 | –/– | 150 | 6 | 8 → 2/10/2, 1.0 .149 0.0 | colour exact |
| 8 | T-L16 | `BrakeLightR` | **Point** | 255,38,0,0 | 1.0 | –/– | 150 | 6 | 1 → 2/10/2 | colour exact |
| 9 | T-L17 | `BattleModeSpotLight` | Spot | 255,255,255,0 | 0.00 | 5/15 | 4500 | 1 | 11 → 10/60/1, **.604 .604 .953** | **approx** (colour from JC3's own object) |
| 10 | T-L18 | `HeadLight1` | Spot | 255,0,0,0 | 5.0 | 10/35 | 1024 | 2 | 14 (custom) → 2/10/1 | colour exact |
| 11 | T-L19 | `HeadLight2` | Spot | 255,0,0,0 | 5.0 | 10/35 | 1024 | 2 | 15 (custom) → 2/10/1 | colour exact |
| 12 | T-L20 | `LWheelLight` | Spot | 255,0,0,0 | 0.00 | 5/15 | 2048 | 2 | 16 (custom) → 2/10/1 | colour exact |
| 13 | T-L21 | `BattleModeSpotLight` | RHelicopterSpot | 195,255,244,0 | 0.00 | –/0 | 0 | 1 | **none** | **not carried** |
| 14 | T-L22 | `HeadLight1` | Spot | 255,0,0,255 | 5.0 | 10/35 | 1024 | 2 | **none** | **not carried** |
| 15 | T-L23 | `HeadLight2` | Spot | 255,0,0,255 | 5.0 | 10/35 | 1024 | 2 | **none** | **not carried** |
| 16 | T-L24 | `Dashboard_Light` | Spot | 172,245,255,0 | 5.0 | 20/45 | 80 | 2 | 0 → 2/10/1, behaviour **HeadLight** | colour exact |
| 17 | T-L25 | `HeadLight1a` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | 2 (rides the lamp) | **approx** (flare unrepresented) |
| 18 | T-L26 | `HeadLight2a` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | 10 (rides) | **approx** |
| 19 | T-L27 | `HeadLight1b` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | 2 (rides) | **approx** |
| 20 | T-L28 | `HeadLight1c` | LensFlare only, **orphan socket** | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 21 | T-L29 | `HeadLight2b` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | 10 (rides) | **approx** |
| 22 | T-L30 | `HeadLight2c` | LensFlare only, **orphan socket** | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 23 | T-L31 | `RWheelLight_top` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 24 | T-L32 | `RWheelLight_bottom` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 25 | T-L33 | `LWheelLight_top` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 26 | T-L34 | `LWheelLight_bottom` | LensFlare only | CDO 1,1,1,1 | – | – | – | – | **none** | **not carried** |
| 27 | T-L35 | `BootLight` | Spot | 152,255,225,0 | 5.0 | 50/60 | 400 | 2 | 17 (custom) → 2/10/1 | colour exact |

### The five approximate entries, with the difference

| entry | difference |
|---|---|
| T-L17 | colour **−0.3961, −0.3961, −0.0471**: the row carries the JC3 graph object `Front_Secondary_Head`'s `diffuse` (.604 .604 .953), not BmAK's (1,1,1). `range` 10 and `angle` 60 are that object's `radius`/`spot_angle`, not BmAK's 4500 and 5/15 (derived from `bm_lightrig.TL17_MEMBERS`). |
| T-L25, T-L26, T-L27, T-L29 | each is a **LensFlareComponent with no light**: BmAK authors a flare, JC3's module has no flare member. The row that "carries" it is the neighbouring lamp's row, so the entry contributes nothing; its `SourceColor` (1,1,1) is not adopted and `MinStrength` ships nowhere (decoded, `LIGHTS.json`). Two rows for one lamp = the entry is double-represented, not carried twice. |

### The ten not carried

| entry | why |
|---|---|
| T-L10 `ChainGunMuzzle` | no T-18 row: the muzzle lamp sits on `Batmobile_Rig_Weapons_Machine_Gun_01`, which has no JC3 part and no emissive face (B-03), so nothing hosts it |
| T-L13…T-L15 (`VEHLT_ForensicsLight` group: T-L21, T-L22, T-L23) | the forensics rig is a **named omission** (T-LG5, `superseded`): no JC3 behaviour, and T-18 wrote no row |
| T-L28, T-L30 `HeadLight1c`/`HeadLight2c` | flare-only **and** orphan sockets — the shipped mesh has no such socket (decoded: `LIGHTS.md` Problems, 6 orphans over 4 rigs) |
| T-L31…T-L34 | four wheel-light flares (`RWheelLight_top/_bottom`, `LWheelLight_top/_bottom`) — flare-only, no row. The lit wheel *arches* they would need are built, and carry `has_lights = 1` with no module entry |

## 4. Channel accounting (the part T-LG2 could not see)

| BmAK quantity | entries authoring it | entries carrying it | built value in place of it | label |
|---|---:|---:|---|---|
| `LightColor` | 15 | **13 exactly**, 1 approximately, 1 not | `diffuse` = RGB/255 | decoded |
| `Brightness` | 15 | **0** | `multiplier` 1 or 2 (donor) | decoded |
| `OuterConeAngle` | 15 | **0** | `angle` 10 or 40 (donor) | decoded |
| `InnerConeAngle` | 8 | **0** | — (no member) | decoded |
| `Radius` | 15 | **0** | `range` 2 or 30 (donor) | decoded |
| `FalloffExponent` | 15 | **0** | `falloff_start` 0 or 0.8 (donor) | decoded |
| flicker | **0** | — | `blinking = 1` on **4 built rows** (3, 5, 7, 9) | decoded |
| socket | 28 | 18 written as `deformable_transform` text | resolution | UNKNOWN |

Two consequences worth naming plainly:

- **`blinking` is a donor artefact that invents behaviour BmAK does not have.** Rows 3, 5, 7 and 9
  (T-L12, T-L8, T-L11, T-L9) blink in JC3 because the donor rows they were cloned from blink
  (`blinking = 1`), while no BmAK entry authors a blink field at all. A steady headlight that
  blinks is a visible lore error introduced by the row-for-row clone T-LG2 signed off.
- **Brightness has a 5× gap where it matters.** Every BattleMode lamp is `Brightness 5.0` and the
  dashboard/boot lamps are `5.0`; they are built with `multiplier 1.0`. The fleet does use
  `multiplier = 5` (12 entries of 3,217, `LIGHT_SYSTEM.md` §3), so the value exists in the domain —
  the build simply never proposed it.

## 5. Ledger rows, re-read against the built bytes

| row | what the ledger says | what the build holds | verdict |
|---|---|---|---|
| **T-LG1** | "28 entries/rig, 4 rigs" → "**21 entries**", `keep 21`, decoded, "count in the built module" | **18** rows (21 − 10 dropped + 7 added) | **STALE** — the cell's own evidence line is "count in the built module", and that count is 18, not 21. The number predates B-07. |
| **T-LG2** | "21 rows / 22 objects, row-for-row the donor's" → `closed` | true of the **donor join**; says nothing about BmAK | **KEEP, but it is not a fidelity test.** 10 donor rows were dropped and 7 added, so the module is no longer row-for-row the donor either; the `closed` verdict survives only because `t2_lg2.py` measures the `.epe`, not `lights[]`. |
| **T-LG3** | "6 headlight-class entries per rig" → "2 primary + 1 secondary spot", "**5 spot rows at `range` 30**" | 6 headlight-class entries per rig is decoded and true; but the module has **4** rows at `range` 30 (2, 4, 6, 10) | **COUNT WRONG** (5 → 4) |
| **T-LG6** | "`range`/`angle` authored per entry" → "30 / 40 on the 5 spots; 2 / 10 on **16**" | **4** rows at 30/40, **1** at 10/60 (T-L17), **13** at 2/10 | **COUNT WRONG** (5 → 4, 16 → 13) and **the values are the donor's**: BmAK's headlight is radius 6000, cone 20/70, brightness 0.15 — none of which appears anywhere in the 18 rows |

So all four rows are `keep` for reasons that do not hold: T-LG1's count is stale, T-LG2 measures the
wrong file, T-LG3/T-LG6 count rows that exist at donor values. None of them is an omission, which is
why the ledger did not catch it: the lamp **is** there, at the wrong cone.

## 6. Closest JC3 system, and the gap for the build (STAGES.md)

"JC3 has no system" is not an answer, so each quantity gets its nearest carrier and the arithmetic
the build must author.

| BmAK quantity | closest JC3 member | what the build must author | error now |
|---|---|---|---|
| `Brightness` 0.15 / 1.0 / 5.0 | `lights[].multiplier` (fleet: 1, 2, 0.5, 0.7, 3, **5**) × `diffuse`, with `min_luminosity` 0 | a linear map brightness → `multiplier` (e.g. 1.0 → 5, 0.15 → 0.75 clipped at the fleet max 5, or scale the whole rig by 1/5); the renderer's own brightness unit is UNKNOWN, so the map needs the Q-1 night probe | BattleMode lamps 5.0 → 1 (5× dark); headlight 0.15 → 2 (**13× bright**) |
| `OuterConeAngle` 70 / 50 / 60 / 44 / 35 / 15 | `lights[].angle` (degrees per `LIGHT_SYSTEM.md` §8 "look like … degrees", UNKNOWN) | `angle = outer` per entry: 70, 50, 60, 44, 35, 15 — not the donor's 40/10 | headlight 70 → 40 (**−30°, 43 % of the cone lost**); boot 60 → 10 (−50°) |
| `InnerConeAngle` 20 / 10 / 5 | **no member** (one `angle` per entry) | nothing can carry a hot core separately; closest composition is a second row on the same part with the narrow `angle` (10 or 5) and a higher `multiplier` — same lamp, two entries | inner cone absent on all 8 entries that author it |
| `Radius` 6000 / 4500 / 4096 / 2048 / 1024 / 400 / 150 / 80 / 0.1 | `lights[].range` (metres, UNKNOWN) | `range = radius_cm / 100` if the unit is cm→m: **60, 45, 40.96, 20.48, 10.24, 4, 1.5, 0.8, 0.001** — the 60 and 45 exceed the fleet max 50 by 20 % and 10 %, so the fleet band itself is not a valid excuse; author 60/45 and accept the outlier, or prove the unit first | headlight 6000 (60 m) → 30 (**half the reach**); brake 150 (1.5 m) → 2 |
| `FalloffExponent` 1 / 2 / 6 | `lights[].falloff_start` (fleet: 0 / 0.8 / 1) | no exponent member; closest is `falloff_start` as a distance where falloff begins — the brake's 6 has no carrier at all (UNKNOWN semantics) | brake falloff 6 → `falloff_start` 0 |
| flicker (none authored) | `lights[].blinking` | set `blinking = 0` on rows 3, 5, 7, 9 | 4 rows blink that should not |
| lens flares (17 entries) | **no member**; closest is an emissive/sprite on the lamp part — the same technique the wheel-arch recipe already uses (`G2-33` §7), via the `CarLight` block or a part with `has_lights = 1` | a flare quad per flare entry (10 flare-only + 7 riding), carried by a part, not by `lights[]` | 0 of 17 carried |
| `VEHLT_ForensicsLight` | no behaviour; closest `HeadLight` with the code-3 red tint | 3 rows on the body/headlight parts, colour `255,0,0`, toggled by mode if a mode switch exists | 3 entries absent |
| `VEHLT_Interior` (dashboard) | no `Interior` behaviour; built as `HeadLight` on the **body** | a row on the cockpit part once the cockpit mesh exists (T-21), behaviour `HeadLight`, range 0.8, angle 45 | behaviour and host both wrong |
| `ChainGunMuzzle` | no vehicle part hosts it | a weapon-side FX light (`.effc`/particle light) rather than a `lights[]` row — outside this module | 1 entry absent |
| 2 point lights (brakes) | `light_type` 0/1 (fleet 0 ×2494, 1 ×723) | the point-vs-spot meaning of `light_type` is UNKNOWN (§8); author 0 and verify in Q-1 | spot semantics applied to a point lamp |
| socket / anchor | `deformable_transform` | the 18 anchors were written from decoded socket chains; every entry is `needs-lig-bone` and the chain's resolution inside a non-rigged part is the §112 probe | UNKNOWN |

## 7. Counts, for the ledger

- BmAK lights: **28** per rig (**101** over 4 rigs).
- Carried exactly (all authored quantities): **0**.
- Colour carried bit-exactly: **13** (T-L8, L9, L11, L12, L13, L14, L15, L16, L18, L19, L20, L24, L35).
- Carried approximately: **5** (T-L17 colour −0.3961/−0.3961/−0.0471; T-L25, L26, L27, L29 flare-only, unrepresented).
- Not carried: **10** (T-L10, L21, L22, L23, L28, L30, L31, L32, L33, L34).
- JC3 rows: **18** built, of which 4 sit at `range` 30 / `angle` 40, 1 at 10 / 60, 13 at 2 / 10.
- Behaviour carried: 15 `HeadLight` + 3 `TailLight` — BmAK has **9 distinct behaviours** over its 28
  entries (`VEHLT_HeadLight`, `TailLight`, `BattleModeLight`, `ForensicsLight`, `Interior`,
  `BootLight`, plus the stripped/graph cases), so 6 of 9 collapse into two JC3 behaviours.

Everything unmarked above is decoded from `LIGHTS.json`, `t14_lights.json`, `bm_lightrig.plan()` or
`LIGHT_SYSTEM.md`; `/255`, `/100` and the fleet percentages are derived arithmetic. The three
UNKNOWNs that block a faithful cone/intensity are: the renderer's `range`/`angle`/`multiplier`
units, `preset_id` override semantics, and which of `lights[]` / `.epe` `SVehicleLight` the renderer
reads — all §8 of `LIGHT_SYSTEM.md`, all three settlable by one Q-1 night drive with a stock car and
a modified one.

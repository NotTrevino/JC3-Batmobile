# The six VALUE-NOT-FOUND rows, explained

Sequel to `Working/Translation/ROW_EVIDENCE_AUDIT.md`, which flags six of its first 40
resolved rows with a cited file that does not carry the quoted value. This document
opens each cited file, records the nearest value it actually holds, classifies the
mismatch, and prints a proposed corrected row. **Nothing is applied**: the ledger is
opened only (sha256 `220dead9b019863a9d3113de5e29cf6d0040e01c2df84da5090d67f8865d5b7a`, unchanged; 199 rows, 79 resolved), and
`--check` re-derives this text.

Classification vocabulary, one per row: **wrong citation** (the value exists, in another
file, named), **wrong value** (the cited file holds a different number, named),
**unit/format difference** (same fact, other form - glob vs expanded name, pattern, unit).

**Six rows: 5 wrong citations, 0 wrong values, 1 unit/format difference.**

## Drift since the first audit (re-derived, not assumed)

* the ledger now holds **199 rows** (198 when the audit ran) and resolves **79** under the audit's own rule; the audit's header quotes 145 of 198.
* `T-E2` and `T-B4` were re-cited and moved to `next` after the audit, so they no longer resolve and grade **OK** today - their mismatches were closed by a ledger edit, not here.
* the first 40 resolved rows now produce **6** VALUE-NOT-FOUND: `T-A1`, `T-L3`, `T-L5`, `T-M1`, `T-MA1`, `T-MA2`; `T-MA1`/`T-MA2` are outside this sheet's six and are recorded, not analysed.

| row | dispo | what it quotes | citation | nearest value in the cited file | classification | now |
|---|---|---|---|---|---|---|
| `T-M1` | edit | **4,000 kg** | `CHAIN.json`, `T3_FLEET.md` | 3-8 t: 3500 / 5100 / 6000 (p25/median/p75); 4000 is in `FITS.md` | wrong citation | VALUE-NOT-FOUND |
| `T-E2` | next | 1393.5 | `FITS.md` | `torque at optimal rpm`: 834.1 at 4 t, 1100 for 6-15 t; 1393.5 is in `current.json` | wrong citation (the comparison base is also a stale number) | left the resolved set (dispo `next`) |
| `T-B4` | next | `arcade.heat_boost.*`, `turbo_jump*` | `VOCABULARY.md` | the ten expanded member names, donor column 0 / 80 / 1.5 / 2 | unit/format difference | left the resolved set (dispo `next`) |
| `T-A1` | keep | 6.63 | `T3_FLEET.md`, `FITS.md` | `aero frontal area`: 6.5 median, 6.72 p75, 6.95 6 t+; 6.63 is in `LEDGER_AUDIT.json` | wrong citation | VALUE-NOT-FOUND |
| `T-L3` | epe | `Rear_Break` | `t2_lg2.py` | the script holds no graph name; it prints `graph_objects_unused`; the name is in `LEDGER_AUDIT.json` | wrong citation | VALUE-NOT-FOUND |
| `T-L5` | epe | `Front_Secondary_Head` | `t2_lg2.py` | same script shape; name in `LEDGER_AUDIT.json` | wrong citation | VALUE-NOT-FOUND |

## T-M1 - wrong citation

Row as it stands:

* value cell: **4,000 kg**
* `why`: mass 4000 -> 6000 (armored class)
* cited: `CHAIN.json`, `T3_FLEET.md`
* grades against today's ledger: **VALUE-NOT-FOUND**

What the file(s) actually hold (needle, file, line, what the line records):

* `4000` - `Working/Translation/FITS.md` line 8 - the fit table's evaluation mass: '(the built Batmobile's mass)'
* `3500` - `Working/Translation/T3_FLEET.md` line 11 - `rigid body mass`, 3-8 t p25
* `5100` - `Working/Translation/T3_FLEET.md` line 11 - `rigid body mass`, 3-8 t median
* `6000` - `Working/Translation/T3_FLEET.md` line 11 - `rigid body mass`, 3-8 t p75 = the proposed 6,000 kg
* **absent:** `mass` - `Research/BatmobileGrab/CHAIN.json` (0 occurrences)
* **absent:** `Mass` - `Research/BatmobileGrab/CHAIN.json` (0 occurrences)

Classification: **wrong citation**. 4,000 kg is not a fleet value: it is `FITS.md`'s own evaluation mass ("the fit evaluated at 4000 kg (the built Batmobile's mass)"). `T3_FLEET.md` holds the band, and it does support the proposed 6,000 kg - that is the 3-8 t p75. The chain clause in the same cell cannot be checked in the cited `CHAIN.json`: that file contains no `mass` and no `Mass` substring at all (0/0), so the `BatmobileMassRatio` / `MassScale` / `InertiaTensorMultiplier` names it quotes are not in the chain grab.

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-M1",
 "doc": "T-1",
 "section": "3. Mass and inertia — no BmAK tag (G1-1 complete), class evidence only",
 "cells": [
  "T-M1",
  "— (**no absolute mass tag**: the chain's only mass members are neutral multipliers — `BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1] — so the sim scales a mass the streams never store; the 4,000 kg this table is evaluated at is `FITS.md`'s own figure, `FITS.md`)",
  "`rigid_body.mass`",
  "class",
  "**4,000 kg**",
  "**6,000 kg** (armored transport; 3–8 t p75 = 6,000 kg, `T3_FLEET.md`)",
  "class",
  "0–100 km/h in QA-1 → **16.4 s / 257 m measured**; stopping distance still open"
 ],
 "dispo": "edit",
 "why": "mass 4000 -> 6000 (armored class)",
 "edits": 1
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK** (was VALUE-NOT-FOUND).

## T-E2 - wrong citation (the comparison base is also a stale number)

Row as it stands:

* value cell: 1393.5
* `why`: replacement 2921 N.m = 894.8 kW / (471.239 rad/s x 0.65) at the edited 4500 rpm band - the torque the lore 1200 bhp needs at T-E1's band; the 1393.5 x 2.844 ratio was computed at the donor's 5000 rpm and delivers only 572 hp (47.7 %) at 4500, while the 0-60 in 2.7 s route gives 2513 N.m (59,580 N / 16.19 gearing x 0.683 m); declared R3, above the fleet p95 2,500; `FITS.md` holds 834.1 at 4 t and 1,100 for 6-15 t, not the 1,121 the old cell quoted (`keep-audit-engine-boost-aero.md` T-E2)
* cited: `CHAIN.json`, `FITS.md`, `keep-audit-engine-boost-aero.md`
* grades against today's ledger: **OK** (dispo `next`, outside the resolved set)

What the file(s) actually hold (needle, file, line, what the line records):

* `1393.52454` - `Working/Translation/current.json` line 15987 - the built `torque_factor_at_optimal_rpm`, nearest to the quoted 1393.5
* `1393.5245361328125` - `Working/Translation/LEDGER_AUDIT.json` line 673 - the module's own float, same value
* `834.1` - `Working/Translation/FITS.md` line 24 - `torque at optimal rpm` fit, evaluated at 4,000 kg
* `1100` - `Working/Translation/FITS.md` line 23 - `torque at optimal rpm` median, 6-15 t mass class
* `2500` - `Working/Translation/FITS.md` line 58 - `torque at optimal rpm` median, 15 t+ (the row's 95th-percentile figure)
* **absent:** `1393.5` - `Working/Translation/FITS.md` (0 occurrences)
* **absent:** `1,121` - `Working/Translation/FITS.md` (0 occurrences)
* **absent:** `1121` - `Working/Translation/FITS.md` (0 occurrences)

Classification: **wrong citation (the comparison base is also a stale number)**. 1393.5 is a decoded build value, not a fleet statistic: the built module carries `torque_factor_at_optimal_rpm` = 1393.5245361328125 (`LEDGER_AUDIT.json`) and `current.json` stores 1393.52454, which is where the row's number is. `FITS.md` cannot carry it - it is a fit table. The row's comparison base is also off: it says "the fit's 1,121 at 6 t", but `FITS.md` holds neither `1,121` nor `1121`; its `torque at optimal rpm` row reads 834.1 at 4,000 kg, and its 6-15 t median is 1,100, which is the base behind the row's own x1.27. So x1.24 belongs to a number the file does not contain.

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-E2",
 "doc": "T-1",
 "section": "7. Engine and transmission",
 "cells": [
  "T-E2",
  "lore power **1200 bhp**; BmAK has **no absolute torque** (curve only, `CHAIN.json`)",
  "`land_engine.torque_factor_at_optimal_rpm`",
  "power → torque at the **built** rpm band",
  "1393.5",
  "keep 1393.5 — the built `land_engine.torque_factor_at_optimal_rpm` = 1393.52454 (`current.json`) — x1.67 over the fit's **834.1** at 4 t and x1.27 over the 6-15 t median (1,100); inside the fleet's 95th percentile (2,500) (`FITS.md`)",
  "derived",
  "0–100 km/h and a power pull; QA-1's 16.4 s take was at 4000 kg and Cd 0.139, so it does not cover this value (`keep-audit-engine-boost-aero.md` T-E2)"
 ],
 "dispo": "next",
 "why": "replacement 2921 N.m = 894.8 kW / (471.239 rad/s x 0.65) at the edited 4500 rpm band - the torque the lore 1200 bhp needs at T-E1's band; the 1393.5 x 2.844 ratio was computed at the donor's 5000 rpm and delivers only 572 hp (47.7 %) at 4500, while the 0-60 in 2.7 s route gives 2513 N.m (59,580 N / 16.19 gearing x 0.683 m); declared R3, above the fleet p95 2,500; `FITS.md` holds 834.1 at 4 t and 1,100 for 6-15 t, not the 1,121 the old cell quoted (`keep-audit-engine-boost-aero.md` T-E2)",
 "edits": 0
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK** (was VALUE-NOT-FOUND).

## T-B4 - unit/format difference

Row as it stands:

* value cell: heat_boost blend 0 / extra **100.92** / grip **4.26** / torque 2; nitro_upgraded extra **100.92** / grip **4.26**
* `why`: replacement: restore the donor's 1.5 grip / 80 extra on `heat_boost` and `nitro_boost_upgraded` - the bytes carry two inherited scalings that are not BmAK numbers (grip 4.26 = 1.5 x 2.844, the torque ratio; extra 100.92 = 80 x 1.2615, the 336.4/250 tier scale), and with T-E2/T-B1 carrying the power ratio, scaling grip by it double-counts; BmAK states no grip change in boost at all (T-B3 identity); blend 0, torque 2 and turbo_jump 0.1 s / 50 km/h / top 200 stay as the donor ships them (n=145) (`keep-audit-engine-boost-aero.md` T-B4)
* cited: `keep-audit-engine-boost-aero.md`
* grades against today's ledger: **OK** (dispo `next`, outside the resolved set)

What the file(s) actually hold (needle, file, line, what the line records):

* `arcade.heat_boost.boost_blend_time` - `Research/JC3Grab/VOCABULARY.md` line 440 - n=145, donor column 0
* `arcade.heat_boost.extra_top_speed` - `Research/JC3Grab/VOCABULARY.md` line 441 - n=145, donor 80
* `arcade.heat_boost.grip_multiplier` - `Research/JC3Grab/VOCABULARY.md` line 442 - n=145, donor 1.5
* `arcade.heat_boost.torque_multiplier` - `Research/JC3Grab/VOCABULARY.md` line 444 - n=145, donor 2
* `turbo_jump.punch_delay_time` - `Research/JC3Grab/VOCABULARY.md` line 357 - n=35, range 0 .. 0.1
* `turbo_jump.top_speed_kph` - `Research/JC3Grab/VOCABULARY.md` line 360 - n=35, median 200
* **absent:** `arcade.heat_boost.*` - `Research/JC3Grab/VOCABULARY.md` (0 occurrences)
* **absent:** `turbo_jump*` - `Research/JC3Grab/VOCABULARY.md` (0 occurrences)

Classification: **unit/format difference**. The two quoted tokens are globs (`arcade.heat_boost.*`, `turbo_jump*`) and a glob is not a substring of anything, so the literal test can only fail. `VOCABULARY.md` lists the expanded members, all ten present, and the donor column is exactly the row's numbers: blend 0, extra 80, grip 1.5, torque 2. Second, smaller correction: the row says 'every shipped car carries them (n=145)' - 145 is the count for the five `arcade.heat_boost` rows; the five `turbo_jump` rows are n=35. The `turbo_jump` figures the row quotes (punch 0.1 s / 50 km/h / top 200 km/h) are those rows' medians, not a donor column (that column is empty for them), so 'Serpente defaults' overstates them.

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-B4",
 "doc": "T-1",
 "section": "8. Boost — BmAK gives a *ratio*, not a multiplier",
 "cells": [
  "T-B4",
  "**no BmAK source exists** (chain-proven: no arcade heat-boost or turbo-jump member; `HeatSteam*` is exhaust steam and `Jump*` is landing physics)",
  "`arcade.heat_boost.boost_blend_time`, `turbo_jump.punch_delay_time` (the two globs expanded: five `arcade.heat_boost` rows, five `turbo_jump` rows in the donor vocabulary)",
  "Serpente defaults, with the two inherited scalings derived back out",
  "heat_boost blend 0 / extra **100.92** / grip **4.26** / torque 2; nitro_upgraded extra **100.92** / grip **4.26**",
  "keep the donor's defaults: **no BmAK source exists** (chain-proven: no arcade heat-boost or turbo-jump member anywhere; `HeatSteam*` is exhaust steam and `Jump*` is landing physics, not a boost) and every shipped car carries them (`VOCABULARY.md`: five `arcade.heat_boost` rows n=145, donor column blend 0 / extra 80 / grip 1.5 / torque 2; five `turbo_jump` rows n=35, medians punch delay 0.1 s / 50 km/h / top 200 km/h)",
  "decoded (fleet) / derived (the two ratios)",
  "boost take: no wheelspin change against the donor's own heat boost; read-back 1.5 / 80"
 ],
 "dispo": "next",
 "why": "replacement: restore the donor's 1.5 grip / 80 extra on `heat_boost` and `nitro_boost_upgraded` - the bytes carry two inherited scalings that are not BmAK numbers (grip 4.26 = 1.5 x 2.844, the torque ratio; extra 100.92 = 80 x 1.2615, the 336.4/250 tier scale), and with T-E2/T-B1 carrying the power ratio, scaling grip by it double-counts; BmAK states no grip change in boost at all (T-B3 identity); blend 0, torque 2 and turbo_jump 0.1 s / 50 km/h / top 200 stay as the donor ships them (n=145) (`keep-audit-engine-boost-aero.md` T-B4)",
 "edits": 0
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK** (was VALUE-NOT-FOUND).

## T-A1 - wrong citation

Row as it stands:

* value cell: 6.63
* `why`: build carries the proposal; nothing to edit
* cited: `T3_FLEET.md`, `FITS.md`
* grades against today's ledger: **VALUE-NOT-FOUND**

What the file(s) actually hold (needle, file, line, what the line records):

* `6.634666919708252` - `Working/Translation/LEDGER_AUDIT.json` line 876 - the built module's `frontal_area`
* `6.63466692` - `Working/Translation/current.json` line 15925 - the same value as stored by the build
* `6.5` - `Working/Translation/T3_FLEET.md` line 47 - `aero frontal area`, 3-8 t median
* `6.72` - `Working/Translation/T3_FLEET.md` line 47 - `aero frontal area`, 3-8 t p75 - nearest to 6.63
* `6.95` - `Working/Translation/T3_FLEET.md` line 47 - `aero frontal area`, 6 t+ median
* **absent:** `6.63` - `Working/Translation/T3_FLEET.md` (0 occurrences)
* **absent:** `6.63` - `Working/Translation/FITS.md` (0 occurrences)

Classification: **wrong citation**. 6.63 is the decoded build value: `frontal_area` = 6.634666919708252 in the built `land_aerodynamics.vmodc` (`LEDGER_AUDIT.json`), stored as 6.63466692 in `current.json`. `T3_FLEET.md` holds the band the row argues against, not the value: 6.5 median and 6.72 p75 for 3-8 t, 6.95 for 6 t+, and no 6.63 anywhere (0 occurrences). Nearest values in the cited fleet file are 6.72 (0.09 above) and 6.5 (0.13 below).

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-A1",
 "doc": "T-1",
 "section": "9. Aerodynamics — the one fit the fleet actually supports",
 "cells": [
  "T-A1",
  "body cross-section 3.5 x 2.27 m (mesh); frontal area decoded 6.634666919708252 in the built `land_aerodynamics.vmodc` (`LEDGER_AUDIT.json`, `current.json`)",
  "`land_aerodynamics.frontal_area`",
  "class",
  "6.63",
  "6.63 — inside the heavy-class band (`T3_FLEET.md`: 3–8 t IQR 4 … 6.72, median 6.5; 6 t+ median 6.95, n=144) and consistent with the body's gross cross-section 3.5 × 2.27 = 7.9 m²; the mass fit's 4.92 describes *cars of that mass*, not this body (`FITS.md`)",
  "class",
  "coast-down distance"
 ],
 "dispo": "keep",
 "why": "build carries the proposal; nothing to edit",
 "edits": 0
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK (rounded)** (was VALUE-NOT-FOUND).

## T-L3 - wrong citation

Row as it stands:

* value cell: decoded
* `why`: brake rows are presets in the entity graph
* cited: `t2_lg2.py`
* grades against today's ledger: **VALUE-NOT-FOUND**

What the file(s) actually hold (needle, file, line, what the line records):

* `'Rear_Break'` - `Working/Translation/LEDGER_AUDIT.json` line 1097 - the donor `.epe` dump: `..._debug.epe@0x2CF9: 'Rear_Break'`
* `graph_objects_unused` - `Tools/scripts/t2_lg2.py` line 97 - the script's own reporting key - what it prints, not what it contains
* **absent:** `Rear_Break` - `Tools/scripts/t2_lg2.py` (0 occurrences)

Classification: **wrong citation**. `t2_lg2.py` is a script, not its output: it contains no `Rear_Break` (0 occurrences) and no graph name at all, because it reads them from the `.epe` and prints the difference under `graph_objects_unused`. The name it reasons about is decoded in the donor entity dump recorded in `LEDGER_AUDIT.json` (`..._debug.epe@0x2CF9: 'Rear_Break'`). Citing the probe instead of the dump is the whole of the mismatch.

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-L3",
 "doc": "T-1",
 "section": "12. Lights — categorical, 28 BmAK entries → 22 JC3 presets",
 "cells": [
  "T-L3",
  "`BrakeLightL/R` (VEHLT_TailLight)",
  "the **5 `TailLight` rows** — JC3 has no separate brake row; `Rear_Break` is in the graph but **no module row references it** (decoded in the donor `.epe` dump, `LEDGER_AUDIT.json`; `t2_lg2.py` prints the unreferenced set)",
  "categorical",
  "decoded",
  "brake lights under braking"
 ],
 "dispo": "epe",
 "why": "brake rows are presets in the entity graph",
 "edits": 0
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK (member name)** (was VALUE-NOT-FOUND).

## T-L5 - wrong citation

Row as it stands:

* value cell: decoded
* `why`: secondary spot preset in the entity graph
* cited: `t2_lg2.py`
* grades against today's ledger: **VALUE-NOT-FOUND**

What the file(s) actually hold (needle, file, line, what the line records):

* `'Front_Secondary_Head'` - `Working/Translation/LEDGER_AUDIT.json` line 1138 - the donor `.epe` dump: `..._debug.epe@0x4F28: 'Front_Secondary_Head'`
* `graph_objects_unused` - `Tools/scripts/t2_lg2.py` line 97 - the script's reporting key, as for T-L3
* **absent:** `Front_Secondary_Head` - `Tools/scripts/t2_lg2.py` (0 occurrences)

Classification: **wrong citation**. Same shape as T-L3: `Front_Secondary_Head` is not in `t2_lg2.py` (0 occurrences); the script computes the unreferenced set and prints it. The name is decoded in the same donor `.epe` dump (`..._debug.epe@0x4F28: 'Front_Secondary_Head'`, `LEDGER_AUDIT.json`), which is the citation the row wants.

Proposed corrected row (JSON, **not applied**):

```json
{
 "id": "T-L5",
 "doc": "T-1",
 "section": "12. Lights — categorical, 28 BmAK entries → 22 JC3 presets",
 "cells": [
  "T-L5",
  "`BattleModeSpotLight`",
  "`Front_Secondary_Head` exists in the graph and is **unreferenced** — this rig has no secondary spot row (decoded in the donor `.epe` dump, `LEDGER_AUDIT.json`; `t2_lg2.py` prints the unreferenced set)",
  "categorical",
  "decoded",
  "—"
 ],
 "dispo": "epe",
 "why": "secondary spot preset in the entity graph",
 "edits": 0
}
```

Re-graded with the first audit's own helpers: proposed row -> **OK (member name)** (was VALUE-NOT-FOUND).

## Cross-cutting findings

* **`CHAIN.json` holds no mass member at all.** The cited chain grab contains 0
  occurrences of `mass` and 0 of `Mass`, so T-M1's parenthetical (`BatmobileMassRatio`
  1.0, `MassScale` 1.0, `InertiaTensorMultiplier` [1, 1, 1]) is not evidenced by the file
  it names. Where those three names are decoded is left UNKNOWN here; the mass value the
  row actually needs, 4000, is in `FITS.md`.
* **A stale comparison number in T-E2.** `FITS.md` has neither `1,121` nor `1121`; its
  6-15 t median is 1,100. The row's x1.27 is right against 1,100 (1393.5/1100 = 1.267);
  its x1.24 is right against 1,121 (1393.5/1121 = 1.243), a base the file does not hold.
  The fit's own value at 4,000 kg is 834.1, so a correct comparison is x1.67.
* **A count that mixes two vocabularies in T-B4.** n=145 is the five `arcade.heat_boost`
  rows; the five `turbo_jump` rows are n=35 and have an empty donor column, so their
  figures are fleet medians rather than the quoted 'Serpente defaults'.
* **Two rows cite a probe instead of a dump (T-L3, T-L5).** Both mismatches vanish when
  the citation moves from `t2_lg2.py` to the decoded `.epe` dump in `LEDGER_AUDIT.json`;
  the script's `graph_objects_unused` output is what the claim rests on, and a script is
  not its output.
* **One row is only a format artefact (T-B4).** A glob is never a substring, so the
  literal test could never pass; the ten members are all present, with the exact donor
  numbers the row quotes.

## What this does not decide

* **Whether each proposal is the editorial choice to take** - the corrections move
  citations and one comparison number; the decided values (4,000 -> 6,000 kg, 1393.5,
  6.63, the donor defaults) are left as the ledger has them.
* **Where `BatmobileMassRatio` / `MassScale` / `InertiaTensorMultiplier` are decoded.**
  Not in the cited chain grab; `Working/Translation/LEDGER_G3*.json` mention them, but
  those are derived audits, not the chain. UNKNOWN.
* **Whether `FITS.md` ever carried 1,121** (a different mass evaluation); the file today
  holds 1,100 and 834.1 only. UNKNOWN.
* **The runtime half of T-L3/T-L5** ("no module row references it") - only the decoded
  preset ids can be checked; no game was run, the test ban stays.

## Oracles re-run by `--check`

* PASS T_ROWS.jsonl sha256 is the ledger this sheet was built from (220dead9b019863a...)
* PASS T_ROWS.jsonl parses cleanly: 199 rows, 79 resolved, no duplicate ids
* PASS the first 40 resolved rows re-derive to 6 VALUE-NOT-FOUND (6)
* PASS that window now yields T-A1, T-L3, T-L5, T-M1, T-MA1, T-MA2 (T-E2/T-B4 re-cited to `next`)
* PASS T-M1 still grades VALUE-NOT-FOUND against this ledger
* PASS T-E2 left the resolved set (dispo `next`); the audit's finding was closed by a row edit, not by this sheet
* PASS T-B4 left the resolved set (dispo `next`); the audit's finding was closed by a row edit, not by this sheet
* PASS T-A1 still grades VALUE-NOT-FOUND against this ledger
* PASS T-L3 still grades VALUE-NOT-FOUND against this ledger
* PASS T-L5 still grades VALUE-NOT-FOUND against this ledger
* PASS one analysis block per row
* PASS T-M1: `4000` occurs in `Working/Translation/FITS.md`
* PASS T-M1: `3500` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-M1: `5100` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-M1: `6000` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-M1: `mass` does not occur in `Research/BatmobileGrab/CHAIN.json` (the mismatch)
* PASS T-M1: `Mass` does not occur in `Research/BatmobileGrab/CHAIN.json` (the mismatch)
* PASS T-E2: `1393.52454` occurs in `Working/Translation/current.json`
* PASS T-E2: `1393.5245361328125` occurs in `Working/Translation/LEDGER_AUDIT.json`
* PASS T-E2: `834.1` occurs in `Working/Translation/FITS.md`
* PASS T-E2: `1100` occurs in `Working/Translation/FITS.md`
* PASS T-E2: `2500` occurs in `Working/Translation/FITS.md`
* PASS T-E2: `1393.5` does not occur in `Working/Translation/FITS.md` (the mismatch)
* PASS T-E2: `1,121` does not occur in `Working/Translation/FITS.md` (the mismatch)
* PASS T-E2: `1121` does not occur in `Working/Translation/FITS.md` (the mismatch)
* PASS T-B4: `arcade.heat_boost.boost_blend_time` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `arcade.heat_boost.extra_top_speed` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `arcade.heat_boost.grip_multiplier` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `arcade.heat_boost.torque_multiplier` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `turbo_jump.punch_delay_time` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `turbo_jump.top_speed_kph` occurs in `Research/JC3Grab/VOCABULARY.md`
* PASS T-B4: `arcade.heat_boost.*` does not occur in `Research/JC3Grab/VOCABULARY.md` (the mismatch)
* PASS T-B4: `turbo_jump*` does not occur in `Research/JC3Grab/VOCABULARY.md` (the mismatch)
* PASS T-A1: `6.634666919708252` occurs in `Working/Translation/LEDGER_AUDIT.json`
* PASS T-A1: `6.63466692` occurs in `Working/Translation/current.json`
* PASS T-A1: `6.5` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-A1: `6.72` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-A1: `6.95` occurs in `Working/Translation/T3_FLEET.md`
* PASS T-A1: `6.63` does not occur in `Working/Translation/T3_FLEET.md` (the mismatch)
* PASS T-A1: `6.63` does not occur in `Working/Translation/FITS.md` (the mismatch)
* PASS T-L3: `'Rear_Break'` occurs in `Working/Translation/LEDGER_AUDIT.json`
* PASS T-L3: `graph_objects_unused` occurs in `Tools/scripts/t2_lg2.py`
* PASS T-L3: `Rear_Break` does not occur in `Tools/scripts/t2_lg2.py` (the mismatch)
* PASS T-L5: `'Front_Secondary_Head'` occurs in `Working/Translation/LEDGER_AUDIT.json`
* PASS T-L5: `graph_objects_unused` occurs in `Tools/scripts/t2_lg2.py`
* PASS T-L5: `Front_Secondary_Head` does not occur in `Tools/scripts/t2_lg2.py` (the mismatch)
* PASS T-M1: proposal keeps the ledger's keys
* PASS T-M1: only the cell(s) [1] change
* PASS T-M1: disposition and edit count untouched
* PASS T-M1: proposed row grades `OK` (was VALUE-NOT-FOUND)
* PASS T-M1: newly cited `FITS.md` resolves
* PASS T-M1: newly cited `T3_FLEET.md` resolves
* PASS T-E2: proposal keeps the ledger's keys
* PASS T-E2: only the cell(s) [5] change
* PASS T-E2: disposition and edit count untouched
* PASS T-E2: proposed row grades `OK` (was VALUE-NOT-FOUND)
* PASS T-E2: newly cited `CHAIN.json` resolves
* PASS T-E2: newly cited `current.json` resolves
* PASS T-E2: newly cited `FITS.md` resolves
* PASS T-E2: newly cited `keep-audit-engine-boost-aero.md` resolves
* PASS T-B4: proposal keeps the ledger's keys
* PASS T-B4: only the cell(s) [2, 5] change
* PASS T-B4: disposition and edit count untouched
* PASS T-B4: proposed row grades `OK` (was VALUE-NOT-FOUND)
* PASS T-B4: newly cited `VOCABULARY.md` resolves
* PASS T-B4: newly cited `keep-audit-engine-boost-aero.md` resolves
* PASS T-A1: proposal keeps the ledger's keys
* PASS T-A1: only the cell(s) [1] change
* PASS T-A1: disposition and edit count untouched
* PASS T-A1: proposed row grades `OK (rounded)` (was VALUE-NOT-FOUND)
* PASS T-A1: newly cited `LEDGER_AUDIT.json` resolves
* PASS T-A1: newly cited `current.json` resolves
* PASS T-A1: newly cited `T3_FLEET.md` resolves
* PASS T-A1: newly cited `FITS.md` resolves
* PASS T-L3: proposal keeps the ledger's keys
* PASS T-L3: only the cell(s) [2] change
* PASS T-L3: disposition and edit count untouched
* PASS T-L3: proposed row grades `OK (member name)` (was VALUE-NOT-FOUND)
* PASS T-L3: newly cited `LEDGER_AUDIT.json` resolves
* PASS T-L3: newly cited `t2_lg2.py` resolves
* PASS T-L5: proposal keeps the ledger's keys
* PASS T-L5: only the cell(s) [2] change
* PASS T-L5: disposition and edit count untouched
* PASS T-L5: proposed row grades `OK (member name)` (was VALUE-NOT-FOUND)
* PASS T-L5: newly cited `LEDGER_AUDIT.json` resolves
* PASS T-L5: newly cited `t2_lg2.py` resolves
* PASS every file opened for grading exists (33 files)

## Labels

Decoded: the ledger rows, the quoted cells, every file's contents and the line numbers,
the built values in `current.json` / `LEDGER_AUDIT.json`. Derived: the classifications,
the ratios x1.67 / x1.27 / x1.24, the nearest-value statements, the proposed rows.
UNKNOWN: the points listed under "What this does not decide".

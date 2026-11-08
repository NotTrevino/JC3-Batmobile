# Tank pivot donor trace

**Source plan:** `tmp/freebuff/reports/tank-pivot-values-for-battle-mode-turn-plan.md` (the brief's
`reports/…` path does not exist; the plan is under `tmp/freebuff/reports/`).
**Index searched:** `Research/JC3Grab/INDEX.jsonl` (81,952 rows).
**Files read:** the unpacked grab under `Research/TankRef/aaf/editor/entities/jc_vehicles/01_land/`,
plus `Research/JC3Grab/TANKTURN.json` / `TANKTURN.md`.
**Date:** 2026-11-08. **Method:** identify the tank the plan takes values from, find that name in the
index, open the grabbed module files and match each quoted value as a little-endian `float32`/`int32`
at a 4-byte-aligned offset. No game run, no build, no edits to game data.

---

## 0. Headline

- **Donor name:** the plan never uses the words "donor tank"; its only "Donor (…)" label is the
  Batmobile's own car (`plan:62-66`). The tank whose values it adopts is the **medium tank**,
  labelled `v0201` in the plan's table (`plan:44`), full id **`v0201_car_capstone_mediumtank`**
  (`TANKTURN.json:247`, `:486`). Its value-identical twin `v0202_car_capstone_bavariumtank`
  (`TANKTURN.json:508-528`) is quoted alongside it in every row that uses tank values (`plan:78-81`).
- **Index hit:** `INDEX.jsonl:37260` holds the donor's entity file
  `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee`
  (archive `archives_win64/game35`, offset 183842816, 5,058,192 B). The index also lists three of its
  default modules (`INDEX.jsonl:37252-37254`), but **not** the steering, transmission or
  custom-land-global modules — those come from the unpacked grab at `Research/TankRef/`.
- **Trace result:** **15 of 15** medium-column tank values appear in the matching `v0201` module
  binary (all byte-present; offsets below). The donor name appears in every file path, and as a string
  inside three of the four files (not inside `land_global.vmodc`).
- **Not donor values:** the plan's write values **22 km/h** and **1.30** do not appear in any donor
  file (both are derived from BmAK, not copied); **30°** appears only as a different field
  (`steer_angle_max_speed_deg`), not as the pivot angle.
- **UNKNOWN:** the other three chassis columns (`v0200`, `v0202`, `v0603`) have **no local grab file**,
  so their quoted values cannot be traced beyond `TANKTURN.json`. The donor `.ee` named by the index is
  also not present locally (only its modules are).

---

## 1. Which name the plan uses

| plan label | full chassis id (source) | role in the plan | local grab? |
|---|---|---|---|
| `v0200` APC | `v0200_car_capstone_apc` (`TANKTURN.json:246`) | comparison column only (APC 25° drift angle) | no |
| **`v0201` medium** | **`v0201_car_capstone_mediumtank`** (`TANKTURN.json:247`, values `:486-506`) | **the values the plan adopts** (45/30/10/100/5, 8.4, 45/10) | **yes — `Research/TankRef/…/v0201_car_capstone_mediumtank/`** |
| `v0202` Bavarium | `v0202_car_capstone_bavariumtank` (`TANKTURN.json:248`, values `:508-528`) | named with the medium tank in rows 3–6; values identical to `v0201` | no |
| `v0603` small | `v0603_car_urga_smalltank` (`TANKTURN.json:249`) | comparison column only | no |

Evidence that the adopted numbers are the medium/Bavarium ones: `plan:78` ("medium/Bavarium/small
tanks" for counter-steer 5), `plan:79` (8.4, "medium/Bavarium tanks"), `plan:80` (drift gate 10),
`plan:81` (drift angle 45, "medium/Bavarium/small tanks; APC 25"), and the write set at `plan:84-86`
(8.4 and 22/30). `TANKTURN.json:486-506` and `:508-528` are identical value-for-value, so the trace
uses the only one with a local grab: `v0201_car_capstone_mediumtank`.

`Research/TankRef/aaf/@files.xml:2` names the same entity build
(`…/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee.fmod_guids`), which
confirms the grab is the donor's own package.

---

## 2. Index search and the grab file

| index line | path | what it is |
|---:|---|---|
| `INDEX.jsonl:37260` | `editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee` | donor entity file (`archives_win64/game35`, offset 183842816, 5,058,192 B) |
| `INDEX.jsonl:37252` | `…/modules/default/ai/v0201_car_capstone_mediumtank_land_global_ai.vmodc` | AI twin, not a player copy |
| `INDEX.jsonl:37253` | `…/modules/default/v0201_car_capstone_mediumtank_land_engine.vmodc` | engine |
| `INDEX.jsonl:37254` | `…/modules/default/v0201_car_capstone_mediumtank_land_global.vmodc` | `LandGlobal` |
| `INDEX.jsonl:56814/56815/56830` | `models/jc_vehicles/…/mediumtank_vehicle_{deform,parts}.vmodc` | art/deform modules, no turn values |
| `INDEX.jsonl:37280` | `…/v0202_car_capstone_bavariumtank_military_01.ee` | Bavarium twin entity (no local grab) |

`INDEX.jsonl` contains **6** `v0201…vmodc` rows and only **three** default-module rows; a search for
`v0201_car_capstone_mediumtank_(land_steering|transmission|custom_land_global).vmodc` returns
**0 rows**. The three turn-value modules that the index omits are present in the unpacked grab:

`Research/TankRef/aaf/editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/modules/default/`
- `v0201_car_capstone_mediumtank_land_steering.vmodc` (1,073 B)
- `v0201_car_capstone_mediumtank_transmission.vmodc` (1,455 B)
- `v0201_car_capstone_mediumtank_custom_land_global.vmodc` (3,399 B)
- `v0201_car_capstone_mediumtank_land_global.vmodc` (1,542 B)

The donor `.ee` itself is **not** in the project (`Research/TankRef/…/v0201…/` holds only
`…_military_01.epe`, `…_military_01.stringlookup`, `…_military_01.ee.fmod_guids` and `modules/`), so
the values are traced in the module binaries, not in the entity container.

**Donor-name presence:** the string `v0201` occurs in the paths of all four files, and inside the bytes
of `land_steering.vmodc`, `transmission.vmodc` and `custom_land_global.vmodc`; it is **absent inside**
`land_global.vmodc` (name-in-path only).

---

## 3. Value trace (medium tank, `v0201`)

Presence = the exact value at a 4-byte-aligned little-endian float (`int32` where the member is an
integer). "Hits" are all matching offsets; the first is the one in the serialized block that matches
`TANKTURN.json`'s ordering. Presence is **byte-level** — the field binding itself is `TANKTURN.json`'s
decode, not re-derived here.

| # | member | plan value | grab file (under `…/modules/default/`) | present? | offsets | donor in path / in file |
|---:|---|---:|---|---|---|---|
| 1 | `LandGlobal.number_of_wheels` | 8 | `…_land_global.vmodc` | **yes** (int32, many) | 80, 176, 320, 432, 576, 652, 708, 792 | yes / no |
| 2 | `LandGlobal.number_of_front_wheels` | 4 | `…_land_global.vmodc` | **yes** (int32, many) | 84, 364, 376, 396, 400, 448, 492, … (24) | yes / no |
| 3 | `LandGlobal.wheels_friction_type` | 2 | `…_land_global.vmodc` | **yes** | int32 92, 384, 1068; float 896 | yes / no |
| 4 | `LandGlobal.ground_clearance` | 0.4 | `…_land_global.vmodc` | **yes** | 100, 568 | yes / no |
| 5 | `LandGlobal.front_wheels.radius` | 0.66 | `…_land_global.vmodc` | **yes** | 104, 136 | yes / no |
| 6 | `LandSteering.steer_angle_min_speed_deg` | 45 | `…_land_steering.vmodc` | **yes** | 104, 424 | yes / yes |
| 7 | `LandSteering.steer_angle_max_speed_deg` | 30 | `…_land_steering.vmodc` | **yes** | 108 | yes / yes |
| 8 | `LandSteering.min_speed_kmph` | 10 | `…_land_steering.vmodc` | **yes** | 96, 360, 456 | yes / yes |
| 9 | `LandSteering.max_speed_kmph` | 100 | `…_land_steering.vmodc` | **yes** | 100, 392 | yes / yes |
| 10 | `LandSteering.countersteer_speed_factor` | 5 | `…_land_steering.vmodc` | **yes** | 116 | yes / yes |
| 11 | `Transmission.final_drive` | 8.4 | `…_transmission.vmodc` | **yes** (`8.39999962`) | 216 | yes / yes |
| 12 | `Transmission.gears` | 5 | `…_transmission.vmodc` | **yes** (int32) | 80, 424, 496 | yes / yes |
| 13 | `Transmission.top_speed` | 105 | `…_transmission.vmodc` | **yes** | 208 | yes / yes |
| 14 | `CustomLandGlobal.drift.max_drift_angle_deg` | 45 | `…_custom_land_global.vmodc` | **yes** | 140, 184, 992, 1344 | yes / yes |
| 15 | `CustomLandGlobal.drift.min_speed_to_drift_kmph` | 10 | `…_custom_land_global.vmodc` | **yes** | 180, 204, 1312 | yes / yes |

**Result: 15/15 values present, donor name present in every path** (in-file for 10 of the 15 rows,
i.e. three of the four files). The steering block at offsets 96–116 reads 10, 100, 45, 30, 5 in
`TANKTURN.json`'s order, and the transmission block reads 105 / 8.4 at 208/216 — corroborating that
these are the serialized field values, not coincidental floats.

---

## 4. Write-set numbers that are not donor values

| plan number | plan source | donor-file presence | verdict |
|---|---:|---|---|
| **22 km/h** (`drift.min_speed_to_drift_kmph`) | BmAK 600 cm/s × 0.036 = 21.6, rounded (`plan:80`) | `22.0` and `21.6` are **absent from all four modules** | **derived — not a donor value** |
| **1.30** (`final_drive` alternative) | 3.91 / 3 (`plan:79`) | `1.3` **absent from all four modules** | **derived — not a donor value** |
| **30°** (`drift.max_drift_angle_deg`) | BmAK `BattleModeStopAndTurnAngleStationary` (`plan:81`) | `30.0` occurs only at `land_steering.vmodc:108`, which is `steer_angle_max_speed_deg`, not a drift angle | **BmAK's own value — not copied from the donor** |
| **8.4** (`final_drive`) | tank value (`plan:79`, `:135`) | present at `transmission.vmodc:216` | **donor value, traced** |
| **2** (`countersteer_speed_factor`, keep) | car donor (`plan:78`) | tank file holds **5** at `land_steering.vmodc:116`; a `2.0` exists in the file but is not this member's value | **car value — not a tank value** |
| **2** (`wheels_friction_type`) | all 12 tanks (`plan:76`) | present (`land_global.vmodc:92/384/1068` as int32) | **donor value, traced** |

The plan's own arithmetic is therefore split: 8.4 and the friction enum are donor numbers that exist
in the donor file; 22, 1.30 and 30 are not, and the 30.0 in the donor file belongs to a different
member. The plan states the 22 conversion (`plan:80`) but labels 30 only "BmAK's own angle" in the
write column; the trace confirms that labelling.

---

## 5. UNKNOWNs

| # | item | why it stays UNKNOWN |
|---:|---|---|
| U1 | `v0202` (Bavarium), `v0200` (APC), `v0603` (small) value traces | no local grab file for those chassis; only `TANKTURN.json` quotes them. `v0202`'s block (`:508-528`) is value-identical to `v0201`'s (`:486-506`), but identity was not verified against a file. |
| U2 | the donor `.ee` container itself | `INDEX.jsonl:37260` names it, but `Research/TankRef/` holds only its `.epe`, `.stringlookup`, `.fmod_guids` and modules — the 5,058,192 B `.ee` is not in the project. |
| U3 | semantic field binding of each offset | this trace proves byte presence, not that offset N is member M; the binding is `TANKTURN.json`'s decode (`:486-506`), not re-derived. |
| U4 | whether the shipped tank actually pivots | `TANKTURN.md:118-122` — native code, not in these files (plan's U2/U3, unchanged). |
| U5 | steering/transmission/custom modules in `INDEX.jsonl` | 0 index rows for those three paths; they exist only in the unpacked `Research/TankRef/` grab, so the index alone cannot locate the files holding those values. |

---

## 6. Change record

1. **Intended change:** add one trace report that names the medium tank as the plan's tank source,
   shows the `INDEX.jsonl` hit and the local grab files, and records presence/absence of each quoted
   pivot value with offsets.
2. **File:** `reports/tank-pivot-donor-trace.md` (mirrored to
   `tmp/freebuff/reports/tank-pivot-donor-trace.md`, the path the task requires).
3. **Revert:** delete both copies. No game file, `Research/` file, build, tune or ledger was modified;
   no game launched.

**Limits.** Static byte scan only; `float32`/`int32` compared with a 1e-5 tolerance; integer members
(8, 4, 5, 2) have many coincidental hits and are therefore weaker evidence than the float matches.

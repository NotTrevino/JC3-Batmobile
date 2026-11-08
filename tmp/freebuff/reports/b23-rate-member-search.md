# B-23: which BmAK fields hold a stiffness, damping or rate value per vehicle state?

Card: 8827-b23-rate-member-search. 2026-11-08.

**Answer in one paragraph.** Reading the 750 row in `suspension-unit-bridge.md` §9 first (it says
`PMWheelSuspensionStiffness 750` / `PMWheelSuspensionBias 20` / `StationaryWheelSuspensionBias 5` have
"no member [that] carries a per-mode spring rate or a stationary bias"), then searching every decode
output under `Research/BatmobileGrab/`, the picture splits in two. **In BmAK the per-mode and
stationary fields do exist**: `PMWheelSuspensionStiffness` = **750**, `PMWheelSuspensionBias` = **20**
are pursuit-mode fields and `StationaryWheelSuspensionBias` = **5** is a rest field
(`MECHANICS_NAMES.md:89-91`). What does not exist is a **JC3** receiver, which is what the B-23 row is
about. The search produces **15 candidates with a stored value** — 5 per-mode, 1 stationary, 9 neither
— plus **5 UNKNOWNs**. The strongest new finding is that the same field carries **two different stored
values**: the shipped `SimulationModel` has `PMWheelSuspensionStiffness` **500** and
`BMWheelSuspensionStiffness` **1000** (`DRIVE_MODES.json:722`, `:560`), while the BMSDK class default
has **750** and **3000** (`MECHANICS_NAMES.md:89`, `:82`). The B-23 row's "750" is the class default;
a build reading the shipped simulation object would see 500.

Output: `Working/Prep/b23_rate_members.json` (the candidate list). `Research/specs/B-23.md` was
**read only, not edited**.

## 1. The 750 row, read first

`suspension-unit-bridge.md` §9, "No member (gap for BUILD)", item 3:

> `PMWheelSuspensionStiffness 750` / `PMWheelSuspensionBias 20` / `StationaryWheelSuspensionBias 5`: no
> member carries a per-mode spring rate or a stationary bias. The mask has to come from a separate
> module (/script) in BUILD.

And §7's row for the pursuit number:

> `PMWheelSuspensionStiffness 750` | strength at the same length | 3.571 | sag = 172% of length |
> UNKNOWN - implies 55.6 kg or a 1.51 m length; no member carries a mode rate

That "no member" is about **JC3's `Suspension` module** (`B-23.md` §2: "one value, no gate"). The
BmAK side is a different question, and it is the one this card searched.

## 2. The candidates

Rules, so the classification is checkable rather than implied:

- **per-mode** — the name carries a mode token for a mode the car enters. `PM` = **Pursuit Mode**
  (corroborated in the same object by `MaxPMSuspensionSpeed`, `PMFrontWheelMaxDroop`,
  `PMRearWheelMaxDroop`); `BattleMode` = **Battle Mode**.
- **stationary** — the name carries `Stationary`.
- **neither** — a base rate with no mode or rest token.
- `BM` is **Batmobile**, not Battle Mode: Battle Mode fields are spelled `BattleMode*`
  (`DRIVE_MODES.json:177`), and the `BM*` fields sit beside them on `RVehicleSimBatmobile`.

| # | member | stored value | where (file:line) | class |
|---|---|---:|---|---|
| 1 | `BMWheelSuspensionStiffness` | 1000.0 | `DRIVE_MODES.json:560` (shipped `SimulationModel`) | **neither** |
| 2 | `BMWheelSuspensionDamping` | 100.0 | `DRIVE_MODES.json:551` | **neither** |
| 3 | `PMWheelSuspensionStiffness` | 500.0 | `DRIVE_MODES.json:722` | **per-mode** (pursuit) |
| 4 | `PMWheelSuspensionDamping` | 50.0 | `DRIVE_MODES.json:713` | **per-mode** (pursuit) |
| 5 | `WheelSuspensionStiffness` | 500.0 | `DRIVE_MODES.json:929` | **neither** |
| 6 | `WheelSuspensionDamping` | 50.0 | `DRIVE_MODES.json:920` | **neither** |
| 7 | `BattleModeSteerBiasRate` | 3.0 | `DRIVE_MODES.json:177` | **per-mode** (battle) — a steering bias *rate*, not a spring rate |
| 8 | `BatmobileOnFireRadiusDecayRate` | 0.1 | `DRIVE_MODES.json:1024` | **neither** — its state is on-fire, not a drive mode |
| 9 | `BMWheelSuspensionStiffness` | 3000 | `MECHANICS_NAMES.md:82` (class default, 4 packages) | **neither** |
| 10 | `BMWheelSuspensionDamping` | 300 | `MECHANICS_NAMES.md:83` | **neither** |
| 11 | `BMWheelSuspensionBias` | 50 | `MECHANICS_NAMES.md:84` | **neither** — a bias, not a rate |
| 12 | `BMFrontWheelSuspensionBias` | 10 | `MECHANICS_NAMES.md:85` | **neither** |
| 13 | `PMWheelSuspensionStiffness` | **750** | `MECHANICS_NAMES.md:89` | **per-mode** (pursuit) |
| 14 | `PMWheelSuspensionBias` | **20** | `MECHANICS_NAMES.md:90` | **per-mode** (pursuit) |
| 15 | `StationaryWheelSuspensionBias` | **5** | `MECHANICS_NAMES.md:91` | **stationary** (rest) |

Counts: **15 candidates — 5 per-mode, 1 stationary, 9 neither.** The three numbers the B-23 row names
appear as rows 13, 14 and 15, and in BmAK all three **do** sit on a mode or rest field. The MECHANICS_NAMES.md
values repeat identically across the four Batmobile packages (lines 89/160/231/302, 90/161/232/303,
91/162/233/304), so the numbers are not package-specific.

## 3. The finding that matters: one field, two stored values

| field | shipped `SimulationModel` (`Startup.upk`) | BMSDK class default (`BmGame.upk`) | ratio |
|---|---:|---:|---|
| `BMWheelSuspensionStiffness` | `1000.0` — `DRIVE_MODES.json:560` | `3000` — `MECHANICS_NAMES.md:82` | 3x |
| `BMWheelSuspensionDamping` | `100.0` — `DRIVE_MODES.json:551` | `300` — `MECHANICS_NAMES.md:83` | 3x |
| `PMWheelSuspensionStiffness` | `500.0` — `DRIVE_MODES.json:722` | `750` — `MECHANICS_NAMES.md:89` | 1.5x |

Both objects are decoded and both are BmAK data; they are different objects
(`Default__RVehicleBatmobile.SimulationModel` vs `Default__RVehicleSimBatmobile`). The suspension bridge
used the **class default** pair (3000 / 300 — `suspension-unit-bridge.md` §1), and therefore the 750 it
reports for pursuit mode is the class-default 750, not the shipped 500. Which object the engine
actually reads for spring rate is **UNKNOWN** in this file set (settle with a paired decode that shows
which of the two is instantiated per vehicle, or a run).

That is not a contradiction of the B-23 row — the row is about the JC3 receiver — but it is a
qualification a build must not skip: "750" is one of two stored values for the same field.

## 4. UNKNOWNs, each with the file that settles it

| # | unknown | settles with |
|---|---|---|
| 1 | `PMWheelSuspensionDamping` class-default value — the field exists (`BMSDK_OFFSETS.json:24443`, offset 816) and ships as `50.0` (`DRIVE_MODES.json:713`), but `MECHANICS_NAMES.md` has **no row** for it | class-default decode of `RVehicleSimBatmobile` (`RVehicleSimBatmobile.g.cs`, the member after `g.cs:1048`) |
| 2 | `PMFrontWheelSuspensionBias` value — declared at offset 824 (`BMSDK_OFFSETS.json:24457`), no value anywhere searched | same class-default decode |
| 3 | `WheelSuspensionStiffness` / `WheelSuspensionDamping` / `WheelSuspensionBias` **class-default** values — only the shipped values (`DRIVE_MODES.json:929`, `:920`) and the member declaration (`BMSDK_OFFSETS.json:26574`) exist | same class-default decode |
| 4 | Whether the mode machine **switches** the `PM*` fields at runtime. `per-mode` here is established from the field names and the mode vocabulary, not from a decoded switch site | the `REVehicleSim` mode-switch body, or `DRIVE_MODES.md`'s mode-switch section |
| 5 | Whether "no JC3 member" is still true after this search — this card searched **BmAK** decode outputs only | `B-23.md` §2 and `suspension-unit-bridge.md` §5/§9 (the JC3 side), neither of which this card re-ran |

## 5. What this changes for B-23

1. **The row's sentence is right about JC3 and would mislead about BmAK.** BmAK has
   `PMWheelSuspensionStiffness`, `PMWheelSuspensionDamping`, `PMWheelSuspensionBias`,
   `PMFrontWheelSuspensionBias` and `StationaryWheelSuspensionBias`; JC3's `Suspension` module has no
   per-mode or stationary member. Say "JC3 has no receiver", not "the numbers have no field".
2. **The number to carry is ambiguous until the object is chosen**: 750 (class default) vs 500
   (shipped SimulationModel). A build that reads `SimulationModel` and is told to write "750" may be
   off by 1.5x.
3. **`PMWheelSuspensionDamping` is the quiet gap**: a per-mode damping field with no class-default
   value in any decoded file. If the pursuit variant is ever authored, this is the value it needs and
   cannot get from the current grab.

## 6. Change record

- **Intended change:** add one candidate list (`Working/Prep/b23_rate_members.json`) and this report.
- **Files written:** those two only. `Research/specs/B-23.md` untouched; `GRAB_BACKLOG.md` untouched;
  no decode output edited.
- **Why those paths:** the card names them.
- **Revert:** delete the JSON and this report.

## 7. Checks run

| check | result |
|---|---|
| 750 row read in `suspension-unit-bridge.md` §9 first | yes — §9 item 3 and §7's pursuit row quoted in §1 |
| B-23 row and card read | `GRAB_BACKLOG.md:1549`, `:1876`; `Research/specs/B-23.md` (read-only) |
| key scan for stiff/damp/rate/spring across `Research/BatmobileGrab/*.json` | 39 files parsed; 5 carry relevant keys (`DRIVE_MODES`, `MECHANICS_NAMES`, `CHAIN`, `BMSDK_OFFSETS`, `COVERAGE`) |
| values traced to a line | 15 of 15 candidates |
| JSON validity | parsed back with `json.load` (see below) |
| classification counts | 5 per-mode / 1 stationary / 9 neither / 5 unknown |
| `Research/specs/B-23.md` edited | **no** |
| game launched / anything built | **no** |

## 8. Limits

- **Static only.** No file here shows the runtime switch between `BM*` and `PM*`; `per-mode` is a
  name-level tie, stated as such in the JSON's `classification_rule`.
- **BmAK side only.** The card's question was "fields that hold a stiffness, damping or rate value per
  vehicle state" in the grab outputs; the JC3 side was not re-searched, so the B-23 row's "no member" is
  neither confirmed nor denied here.
- Bias fields are included but flagged: a bias is a rest position, not a rate, so rows 11, 12, 14, 15
  satisfy "per vehicle state" without being rates.

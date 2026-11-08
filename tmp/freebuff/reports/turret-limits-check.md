STATUS: done — the turret (P-01) and cannon (P-02) rows agree with the BmAK animation to 0.000°, but the bm-RC2 build carries **no joint at all** for either part, so every range the rows ask the build to store is missing (Δ 120.000° yaw, Δ 25.000° pitch): 4 of 5 comparisons flagged.

# Turret / cannon range check, bm-RC2

## What was asked

Pick the turret and cannon rows (P-01, P-02 in `Working/Translation/T8_PARTS.md`, cross-checked
against `Research/JC3Grab/TURRET.md`), compare their yaw and pitch ranges with what the built parts
module in `Builds/bm-RC2` stores and with the BmAK values in `Research/BatmobileGrab/ANIMATIONS.md`
(moved-bone rows), tabulate row / built / BmAK, and flag differences over 0.5°. Output
`Builds/bm-RC2/verify/turret_ranges.md` plus `Tools/scripts/v_turret_ranges.py --check`, read-only on
the build.

## Files written

| file | what |
|---|---|
| `Tools/scripts/v_turret_ranges.py` | new generator; `--write` renders the page, `--check` re-derives every span, delta and flag from the source bytes and byte-compares the page |
| `Builds/bm-RC2/verify/turret_ranges.md` | the tabulation (new file in the build's `verify/` dir; no build payload touched) |
| `MODLOG.md` | one appended section: intended change, why this file, revert path |
| this report | `tmp/freebuff/reports/turret-limits-check.md` |

## The numbers

Rows (`T8_PARTS.md`, columns "BmAK motion", "rate", "carrier limits"):

* **P-01 `batmobile_turret`, behaviour `Turret`** — BmAK motion **-60.000…60.000°**, 174.05 °/s, pivot
  `0.000, 0.876, 0.333`, axis `[-0.000, 1.000, -0.000]` (JC3 space), carrier limit -179.0…179.0°
  (v0201 medium tank).
* **P-02 `batmobile_cannon`, behaviour `Cannon`** — motion **static**, carrier limit **-5.0…20.0°**;
  its verify line asks the barrel to stop at "the carrier's own -5..20 deg".

Built (`Builds/bm-RC2/aaf/models/.../batmobile/`, read with `jc3adf.parts()` — the same walk
`jc3adf.py dump --paths` uses — and `jc3_physics_limits`' hinge atoms at 0x0FC/0x100):

* 61 parts; `batmobile_turret` = 50 (`Turret`), `batmobile_cannon` = 51 (`Cannon`),
  `batmobile_riot_suppressor` = 53 (`Cannon`), parents 0 / 50 / 50.
* **`constraint_index = -1` on all three.** 11 other parts do carry indices 0…10 (both doors, both
  bumpers, grill, engine, hood, hood_signature, both mirrors, trunk), so the field is written — the
  turret unit is left unjointed by value.
* the built `sportsmuscle.physicsc` holds **11 constraint objects: 9 `hkpLimitedHingeConstraintData`
  + 2 `hkpRagdollConstraintData`** — the donor car's panels only (0…80 / -35…0 doors, 0…30, 0…70 hood,
  -15…0 boot, 0…90). Widest limited span **90.0°**, so no object there can be the yaw hinge even if
  an index were mis-read.

BmAK (`ANIMATIONS.md`, `turret` and `cannon` moved-bone rows, identical for Batmobile/MK2/Funhouse/Joker):

* `Batmobile_Rig_Weapons_Turret_Root` **0.00 cm / 60.00 deg** in `Batmobile_V2_Turret_Spin` → ±60.000°
  yaw swing.
* `Heavy_Cannon_Barrel_01` **36.13 cm / 0.00 deg**, `Heavy_Cannon_Barrrel_02` **53.38 cm / 0.00 deg**
  in `Batmobile_V2_Cannon_Fire` → the cannon translates, it does not rotate.

Comparison (difference = absolute gap of two spans; a side with no joint counts as a 0.000° span):

| joint | row | built | BmAK | Δ row-built | Δ row↔BmAK | Δ BmAK-built | > 0.5° |
|---|---|---|---|---|---|---|---|
| yaw | -60.000…60.000° | **none (no joint)** | ±60.000° | **120.000** | 0.000 | **120.000** | FLAG |
| pitch motion | static | none (no joint) | static (0.000°, 36.13/53.38 cm) | 0.000 | 0.000 | 0.000 | ok |
| pitch limit the row asks for | -5.000…20.000° | none (no joint) | — | **25.000** | — | — | FLAG |
| yaw carrier (informational) | -179.000…179.000° | none (no joint) | — | **358.000** | — | — | FLAG |

**Verdict.** The rows and the animation agree exactly (Δ 0.000° on both axes; the 0.5° threshold is
never approached between them). The disagreement is rows vs **build**: RC2 publishes the three parts
and their behaviours but not the hinge each needs, so neither P-01's ±60° sweep nor P-02's carrier
pitch range exists anywhere in the shipped tree. `jc3adf` resolves the link exactly as
`Research/JC3Grab/TURRET.md` §1 describes it (behaviour + one limited hinge addressed by
`constraint_index`), and the same gap is already on record for 19/19 new parts in
`Research/challenge/card-B-04.md` (B4-02, BROKEN).

## Commands and output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && export PYTHONIOENCODING=utf-8 && set -o pipefail && python Tools/scripts/v_turret_ranges.py --write; echo "EXIT write=$?"; python Tools/scripts/v_turret_ranges.py --check; echo "EXIT check=$?"
wrote Builds/bm-RC2/verify/turret_ranges.md (7252 bytes)
EXIT write=0
PASS P-01 motion is -60.000…60.000
PASS P-01 carrier is -179.0…179.0
PASS P-02 motion is static
PASS P-02 carrier is -5.0…20.0
PASS TURRET.md carriers match the rows
PASS BmAK turret swing is 60.00 deg
PASS BmAK cannon rotation is 0.00 deg
PASS built module has 61 parts
PASS built physicsc has 11 constraints (9 limited + 2 ragdoll)
PASS no limited hinge is wide enough to be the yaw joint
PASS 11 parts carry a constraint_index and 50 carry -1
PASS the turret unit's three parts carry no joint
PASS the three parts keep their behaviours
PASS yaw row and BmAK agree within 0.5 deg
PASS pitch row and BmAK agree within 0.5 deg
PASS yaw row vs built is flagged
PASS pitch row vs built is flagged
oracles: 17/17 pass
document identical: Builds/bm-RC2/verify/turret_ranges.md
EXIT check=0
```

Exploration runs that produced the evidence above (all read-only; each printed its own tables):
`jc3adf.parts()` on the built `sportsmuscle_vehicle_parts.vmodc` (61 parts, `constraint_index`
histogram `{-1: 50, 0…10: 11}`), `jc3_physics_limits.scan()` / raw `jc3hkx.Packfile` on the built
`sportsmuscle.physicsc` (11 constraint objects; per-hinge min/max: 0…80, -35…0, 0…80, -35…0, -15…0,
0…30, 0…70, -15…0, 0…90), and the same two scans over `bm-RC1` (identical: 9 hinges, same spans,
`constraint_index = -1` on the turret unit), which is why RC2 is described here as carrying the gap
rather than introducing it.

## UNKNOWNs

* **Does JC3 create a joint on its own for a `Turret`/`Cannon` part with `constraint_index = -1`?**
  Tried: TURRET.md §1/§6 (the hinge is the link), the 232-entity census (no Turret/Cannon part
  without one), `card-B-04.md` (calls it BROKEN). No file states the engine behaviour and the test
  ban stands, so it stays unknown — the page says so rather than calling the missing joint harmless.
* **Turn rate.** P-01's 174.05 °/s has no home: a JC3 limited hinge stores an axis and two angles,
  no rate (TURRET.md §6). Even a correctly written hinge would not carry it.
* **Pivot and axis of the built joint.** Nothing built can be compared against the row's pivot
  `0.000, 0.876, 0.333` / axis `[-0.000, 1.000, -0.000]` until a constraint exists, so this page
  compares spans only.

## COMPROMISES

* The build ships the turret and cannon as parts with **no hinge**: the yaw range (±60°) and the
  carrier pitch range (-5…20°) are absent, and P-01's 174.05 °/s can never be expressed in a JC3
  hinge even once one is written. This is a lore-accuracy gap that the operator must approve or
  schedule as work (the missing joints are the same defect as B4-02, seen from the range side).
* Nothing was installed, launched or attached to; the build was opened for reading only, and the
  single new file inside it is the requested `verify/turret_ranges.md`.

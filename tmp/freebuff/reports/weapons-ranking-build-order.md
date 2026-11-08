# Weapons build order, following the operator's ranking

2026-11-06. Inputs, read-only: `OPERATOR_PRIORITIES.md` (ranking and its two rulings), the build
briefs in `tmp/freebuff/queue/` (`8300` B-01 scaffold, `8304` B-05 entity graph, `8305` B-06 weapons
tunes, `8306` B-07 effects, `8320` B-14 RC4 merge, and the verify wave `8400`-`8406`), and the reports
those briefs consume. **The queue was not edited** — this file is advice about it, not a mutation of
it.

**The ranking** (`OPERATOR_PRIORITIES.md`, verbatim order): 1 tracker + EMP missile ("the EMP missile
does not work without the tracker"), 2 booster mesh, 3 EMP burst, 4 hacker ("not many drones in JC3"),
5 sonar (lowest; mission-dependent in BmAK). Two rulings bound this order: the ranking **orders**
weapon work and **never removes** a weapon (all BmAK weapons are required), and the unranked weapons
(cannon, Vulcan, riot, missile pods) are **not** below sonar by default — the operator has to rank
them first.

---

## 1. The order

| # | stage | what ships | briefs, in order | reports it depends on | gate before the next stage |
|---|---|---|---|---|---|
| 0 | **scaffold** | identity copy of test-091 as `Builds/bm-RC4-base`, receipt naming the batches each later step consumes | `8300` (B-01) | `translation-closeout-t23.md`, `review-translation-wave.md` | `.ee`/`.toc` byte-identical to test-091 |
| 1 | **W1a entity + slots** | the two driver slots on the `CCar` root (`main_weapon`, `id:00568A74`) and the four `CCar` roots for the 8 slot-able objects | `8304` (B-05) **moved ahead of `8302`/`8303`** | `wp13-slots-force.md`, `apply-weapon-slot-rows.md`, `repeated-slot-pointer-evidence.md` | both slot pointers non-null and mapped to a named part |
| 2 | **W1b tracker launcher** | `RBatmobileVehicleTracker` half: the tag geyser on the same button and socket as the missile; the target's yellow/grey marker | `8305` (B-06, **split**: only the tracker tune + the missile in this pass) → a **new** hud brief (none exists, §5) | `immobilizer-vs-emp-missile.md`, `hacker-and-tracker-gadgets.md` (T-WP7/T-WP9 rows), `tracker-lock-hud-plan.md` | tag persists on the target; marker changes state by remove+create, not re-type |
| 3 | **W1c EMP missile** | `w618` clone + Fire Leech guidance + a NEW lock-on `AutoAim`; every fire-block value stays `w618`'s; the trail at `MissileL/R` | `8305` (rest of the missile half) then `8306` (B-07, trail + launch FX) | `wp4-fire-leech.md`, `lock-hold-salvo-closest-system-plan.md`, `missile-pod-salvo-plan.md`, `lock-hold-and-salvo-carrier.md` | missile flies, seeks, and the launcher's own numbers are unchanged from `w618` |
| 4 | **W1d lock hold + reticle** | the 2.0 s held lock, the 8-target salvo, and the reticle's entity → HUD link | **cards `B-24` and `B-25` have no build brief yet** (§5) | `lock-hold-and-salvo-carrier.md`, `lock-on-reticle-hud-link.md`, `Research/specs/B-24.md`, `Research/specs/B-25.md` | 8 targets acquire in the cone; POI type 21 disappears on fire or on leaving the cone |
| 5 | **W2 booster mesh** | the 18-nozzle ring mesh (authored — no JC3 part is a nozzle), the pose-driven deploy, the plume/flame emitters | `8306` (B-07, effects half) + a parts brief for the authored ring | `booster-mesh-and-flame-plan.md`, `weapon-bay-animation-plan.md` | ring opens in 0.600 s and closes in 0.833 s under nitro; plume colour ramp matches |
| 6 | **W3 EMP burst** | entity-level `CForcePulse` with `truck_emp.ftune` + a private copy of the 4-stage burst | `8306` (effects) + the EMP writer work of `Research/specs/B-18` | `emp-visual-and-hit-plan.md`, `immobiliser-and-emp-trigger.md` | burst damages nothing, pushes, and the cooldown reads 2.0 s |
| 7 | **W4 hacker** | beam (35 cm, magenta), success feedback, interaction trigger on a drone/vehicle | `8306` (effects) + `Research/specs/B-19` | `hacker-gadget-visual-plan.md`, `hacker-and-tracker-gadgets.md` | beam spawns from 6 sockets and the target reacts; cooldown 1.0 s |
| 8 | **W5 sonar** | damage-free pulse at BmAK's radius + a **new** ring effect | `8306` (effects) + `Research/specs/B-20` | `sonar-pulse-visual-plan.md`, `sonar-and-scan-pulse.md` | pulse reaches 25 m at 1 s and 37.5 m at 1.5 s |
| 9 | **rest of B-06** | cannon, Vulcan, missiles, riot and the rest — **unranked, do not reorder below sonar** without the operator | `8305` (remainder) | `apply-weapon-slot-rows.md`, `non-lethal-cannon-carrier.md`, `weapon-points-vs-bmak.md` | each tune member written with its BmAK source number |
| 10 | **merge** | all `bm-RC4-*` trees into `Builds/bm-RC4` with the 3-way `.epe` merge, receipt schema 2, `install.ps1` | `8320` (B-14) | the nine `build-d0*` reports | budget (Model 4,915 KB / Texture 7,065 KB), aafdiff vs RC2 |
| 11 | **verify** | gates VX-1…V7 | `8400`-`8406` | `v05_predictions.md`, `v05_driving.md` | all seven gates green |

---

## 2. What moves earlier, and why

| brief | today | proposed | why |
|---|---|---|---|
| `8304` B-05 entity graph | after `8302` lights + `8303` materials | **first after the scaffold** | every ranked item needs the slots and the graph objects: the tracker and missile are *stored in* the two driver slots, and the effects/parts of W2-W5 attach to graph nodes. Building lights and materials first delays rank 1 behind two unranked-looking batches |
| `8305` B-06 weapons tunes | one batch, after `8306` B-07 effects | **split**: tracker + missile tune first, the rest at step 9 | the brief asks for "every weapon the apply-weapon-slot-rows report put on the car" in one pass, which makes the queue's order the anti-ranking. The same file is written either way (each patch is at its decoded offset-in-file, so the file size is unchanged), so splitting it costs one extra `--check` run, not a second build |
| `8306` B-07 effects | one batch | **twice**: the missile trail/launch with W1c, the rest with W2-W5 | the missile is not shippable without its trail (T-FX12/T-FX14), while the booster/EMP/hacker/sonar effects are later ranks |
| new hud brief | **absent** | after W1b | the tracker's yellow/grey marker is a POI in `ui/hud.gfx` (T-19), and no queue brief owns that file. Without it the tracker half of rank 1 cannot ship, which is exactly the half the operator says the missile depends on |

Nothing else moves. `8300` stays first (a new private tree must exist before any patch), `8320` stays
last among the builds, and the verify wave stays after the merge.

---

## 3. Why rank 1 is two halves, and what each half is

`tmp/freebuff/reports/immobilizer-vs-emp-missile.md` settles the operator's own 2026-11-05 question:
**the Immobiliser is the EMP missile** — `RBatmobileEMPMissile` fires the immobilising round and BmAK
puts the "Immobiliser" string on that round's impact sound — while `RBatmobileVehicleTracker` is a
separate launcher on the same button and socket and is the half that **tags** the target. That is why
the ranking couples them: the missile's acquisition needs the tag.

| half | decoded content | JC3 carrier | gap, named |
|---|---|---|---|
| tracker | the tagged target shows a **yellow** or **grey** circle with a distance readout; in `ui/hud.gfx` that is `POI_TYPE_MISSION` (19, arrow `0xFFE717`) and `POI_TYPE_LOCKED` (24, arrow `0x808080`), distance printed from the caller's string into `MCI_distance.TXT_distance` | `CreatePoi(type, use_progress_bar, is_minor, label)` + `ShowPoi`/`HidePoi`; the type is fixed at creation, so the lock changes state by **remove + create** | the world→screen transform is native and stays UNKNOWN: `x`/`y` must be supplied by us |
| missile | a `w618` clone whose own fire-block values are kept, plus the Fire Leech's guidance: `missile_turning_speed` 300, random 60, acceleration 30→65 over 0.2→10 s, accel-random 2→5; a NEW `AutoAim` with the fleet lock-on preset's classes (`CanTargetCharacters` 0), cone 0.12/0.15 and `MaxAimDistance` 120 m | donor `w618_sportsmuscle_missile` + `missile_base_tuning.*` | the 2.0 s lock hold, the 8-target salvo and the reticle link have **no known member** — cards B-24 / B-25; the *disable* half is T-WP15, deliberately `out` (no EMP-named member on any NPC `RVehicle*`; the only route is `w702_emp`, B-18) |

So rank 1 ships in four increments (W1a-W1d) and only W1d needs B-24/B-25 authored first.

## 4. The later ranks, in one line each

| rank | decoded anchor | report | card | why it is not earlier |
|---|---|---|---|---|
| 2 booster | 18 nozzle bones on a ring at z 2.989 m, radius ≈34 cm; plume `MESH_Batmobile_Jet_V01` (114,160 B), flame `Firefly_JetMesh` (5,270 B); deploy pose `Batmobile_V2_Jet_Boost` 0.600 s / 19 keys, close 0.833 s / 26 keys; JC3 `car_cycle_base_nitrous.effc` (8 emitters), `jet_exhaust_base.effc` (11) | `booster-mesh-and-flame-plan.md` | — | the nozzle mesh must be **authored** (0 hits for "nozzle" in the 17 MB index), which is a modelling step the other ranks do not need |
| 3 EMP burst | `RBatmobileEMP`: `WeaponCoolDown` 2.0 s, four stages to `[250, 30, 30]` cm, lifetime 0.2-4.0 s, spawn 0-1500, `MaterialToUpdateWhenPresent` `Batmobile_V3_Wheel_EMP_MAT_INST` at index 0 | `emp-visual-and-hit-plan.md`, `immobiliser-and-emp-trigger.md` | B-18 | needs the entity-level `CForcePulse` writer that B-18 defines; ships after the missile so the two EMP paths are not debugged at once |
| 4 hacker | `DroneHacker_Beam` 35 cm wide, colour `[2.0, 0.0, 1.0]`, 4 s on a drone / 10 s heavy tank, 6 sockets, cooldown 1.0 s; **no world-space target outline exists** | `hacker-gadget-visual-plan.md` | B-19 | the operator's own note ("not many drones in JC3") is a content limit, not a missing member |
| 5 sonar | 7 emitters, axial 2500 cm/s, lifetimes 1/1.5/1.5/1-3 s → 25/37.5/75 m, thickness 0.2×0.2×0.1, **fade not decoded**; JC3 has **0 of 930** `.effc` paths named ring/shockwave/wave/pulse and `CForcePulse` has 8 numeric members, all damage/radius, no speed or lifetime | `sonar-pulse-visual-plan.md`, `sonar-and-scan-pulse.md` | B-20 | it needs a **new** ring effect authored from scratch; cheapest thing to defer |

---

## 5. Gaps this order exposes (nothing invented to close them)

1. **No brief owns `ui/hud.gfx`.** The tracker marker is a POI, and T-19 owns the HUD; the queue has
   no hud build step between B-05 and B-14. W1b cannot ship without one.
2. **B-24 and B-25 have specs but no build brief.** `Research/specs/B-24.md` (2.0 s hold, 8-target
   salvo) and `B-25.md` (reticle entity→HUD link, POI type 21) exist; the queue does not.
3. **The queue's B-06 text is "every weapon" in one pass.** Honouring the ranking needs that brief
   split (step 2/3 vs step 9); nothing else about it changes.
4. **Unranked weapons are unranked, not lowest.** Cannon, Vulcan, riot and missile pods sit at step 9
   by *default order*, not by rank; the operator has said they are not below sonar by default and has
   to rank them before this table can put them anywhere.
5. **The lock-hold and reticle numbers are still missing:** 2.0 s hold, 8 targets and the reticle link
   have no member on either side; B-24/B-25 are the build route, not a decoded value.

---

## 6. Limits

- This file changes **no** queue brief, no ledger row and no build tree; it is a reading of the
  ranking against the briefs as they stand today (`ls tmp/freebuff/queue`).
- The dependency chains in §1 are the ones the briefs' own `AFTER:` headers and the reports' cited
  carriers state; where a brief's `AFTER:` list names a report that does not exist, that is recorded
  in §5 rather than filled in.
- `tmp/freebuff/queue/8767-weapons-ranking-build-order.txt` (the queue copy of this brief) is **not
  on disk**; this report was written from the message text and the surviving briefs.

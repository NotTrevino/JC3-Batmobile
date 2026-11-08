# Research reset — findings (2026-11-02)

User decision after Q re-test 5: **stop building.** The project slid from grab → translate → build → verify
into guess → test. The Batmobile loading was the first moment the translation could be judged as a whole,
and it showed that the failure is further back than the surface bugs (drop menu, crashes) that hid it.
No more builds on guesses. This file records what is known, what was never grabbed, and what was never
translated or was guessed. Every claim names its source; nothing here is a plan to build.

## 1. What was never grabbed

| gap | evidence | blocks |
|---|---|---|
| **The drivable Batmobile's collision.** BmAK's physics asset (`Batmobile_V3_Destroyed_Physics`, 32 `RB_BodySetup` boxes) belongs to the destroyed wreck; it has no chassis body. Where BmAK's driving collision lives (vehicle sim, skeletal-mesh simple collision, another package) was never found. | `Research/BatmobileGrab/PHYSICS.md:75` | every collision card (B-10, B-10b, B-10c) |
| **BmAK's controls / input.** `BmGame/Config/BmInput.ini` (and the Batmobile's input handling) was never read; no grab file mentions bindings. | no hit for input/keybind in `Research/BatmobileGrab/*.md`; file present in the install | D-11 (enter with JC3 controls, all else BmAK) |
| **JC3's control model.** What a JC3 vehicle can remap, and where vehicle input is defined, was never grabbed. | GRAB_BACKLOG D-11 "not yet researched" | D-11 |
| **925 untagged/native BmAK objects (4.6 %)**, including `RB_StayUprightSetup`, `RVisualDamageComponent`, `SkeletalMeshComponent`, `CylinderComponent`, 4 `MaterialInstanceConstant` (eof), and the `BmScript` package (not on disk). | `Research/BatmobileGrab/GAPS.md` | handling, self-righting, damage visuals, part of the material chain |
| **A runtime oracle.** Nothing measures in game what the game actually loaded or computed (which `.physicsc` is read, where collision sits relative to the mesh, which colour reaches the screen). Every verification so far compares files to files. | MODLOG Q-1 entries | knowing, rather than guessing, for every in-game symptom |

## 2. What was not translated at all

**Colour.** The decoded BmAK body colour is linear `[0.0258, 0.0258, 0.030]`, near-black (ledger `T-MA3`,
disposition "keep"). The build did not carry it. A chain of constants replaced it, the last of which
(ALB-2, `PAINT_ALBEDO_GAIN = 4.0`) was chosen from screenshots. The result is 0x837d86, which renders
white-violet in JC3 daylight (MODLOG §107 albedo history; Q re-test 4 screenshot). There is no
decoded bridge between UE3's lit material (with its environment probe) and JC3's `CarPaintMM`. So
"BmAK black" has no known JC3 value: the conversion is unknown, not merely mis-tuned.

**Ledger rows still open.** In `Working/Translation/T_ROWS.jsonl` (198 rows), 13 are `blocked` and 40 are `next`:
- **Blocked:**
  - **Audio:** 90 events in 10 banks absent from the install (T-AU3, T-AU5).
  - **Effects:** the exhaust/afterburner flame (T-FX3).
  - **Handling:** suspension droop and bias (T-S6) and steering rate (T-ST7).
  - **Weapons:** EMP missile and burst (T-WP4, T-WP5), and 11 weapons into 2 driver slots (T-WP13).
  - **Rebel Drop entry:** its name and description strings (T-WLD4, T-WLD6).
  - **Stunt areas** (T-WLD11).
  - **Modes:** the immobilizer (T-MD2) and the battle-mode switch (T-MD14).
- **Named omissions:**
  - **Battle mode, turn-on-spot and transformation** (T-BM1, T-MD13).
  - **Rigs and audio:** the forensics rig and interior audio.
  - **Modes overall:** D-2's "one hybrid car" means no pursuit/battle switch exists at all.
- **The ledger is not reconciled with the builds.** Some `next` rows were built later (for example T-WP1/T-WP2 by B-05/B-06, and the T-L lamp rows by B-05/B-07). So the ledger cannot answer "what is translated" without an audit against the built files.

## 3. What was translated wrongly (found this session, traced to the step)

| step | what it did | what the source says |
|---|---|---|
| T-13 interaction points | anchored all 15 points/triggers 0.05–0.30 m off the shell, invented yaws, unit scale | donor: identity rotation, triggers are scaled volumes, seat inside (fixed as T-13R; **entry confirmed in game**) |
| B-03/B-04 arch lamps | parented under wheel parts (AK skins them to the wheel disc bones) | JC3: no car parents anything under a wheel part (0 of ~170) → crash +0x151410f (fixed, confirmed loads) |
| B-04 behaviours | Turret/Cannon/GatlingGun/AirBrake/EngineRotatingPart on body-less parts | fleet: these always carry a world body (22/68/24/3/3); loads, whether they work is unverified |
| B-10 collision | stretched the Serpente chassis hull per axis; never refit the dynamic AABB trees | no BmAK chassis collision was grabbed (§1) |
| B-10b / B-10c | rebuilt the raycast mesh, then the world hull, from the Batmobile **render** mesh | a derivation, not a grab; user reports collision still off on the sides, front and back, so the cause is unknown (§4) |
| MODLOG §56 | "body_COL follows the render mesh" | wrong: the extern mesh's geometry and BVH are baked into the `.physicsc` |
| ALB-2 colour | ×4 gain picked from screenshots | decoded colour ignored (§2) |

## 4. Collision: what is known and what is not

- **Known (decoded, with oracles in `bm_colmesh.py` and `bm_colhull.py`):**
  - Body 0 (world collision) is one convex polytope, and body 42 (raycast) is an extern mesh.
  - The tree, geometry and polytope formats are decoded, and every donor hull re-encodes byte for byte.
- **Built:** the shipped file's world hull is the exact convex hull of the Batmobile LOD2 (bounds −1.745..1.754 / 0.075..2.358 / −3.428..3.609 m).
- **Observed:** the user reports collision still off on the sides, front and back.
- **Not known:**
  1. Whether the game reads our `.physicsc` at all. It was moved by B-18; no in-game observation has ever distinguished our file from the vanilla one.
  2. Whether the physics frame equals the render frame for this entity.
  3. What the remaining 41 Serpente part bodies contribute. They are live world bodies at Serpente positions: bumpers, fenders, hood, trunk, windows and lamps, plus 2 static compounds of 7 front and 7 rear pieces.
  4. What BmAK's own collision is (§1).
- **None of these may be answered by another build-and-look.** Each needs a measurement first.

## 5. Process failures (why it went wrong)

1. **The donor was the default.** When a BmAK fact was missing, the Serpente's shape, value or behaviour was kept or stretched, and labelled "translation".
2. **Assumed and chosen values were built.** Examples: the ALB-2 gain, T-13's "0.10 m chosen" clearance, B-10's per-axis stretch, and LOD2 standing in for collision.
3. **Files were verified against files, never against the game.** Checks passed while the game showed something else.
4. **The surface hid the core.** Crashes and the drop menu kept attention on loading. Once it loaded, the translation's gaps were all visible at once.
5. **The ledger drifted from the builds**, so "done" stopped meaning translated.

## 6. Research to do before any build (no guesses)

Each item ends in a source file or a measurement, not a build:
- **R-1:** find BmAK's drivable collision: package, class, shape.
- **R-2:** grab `BmInput.ini` and the Batmobile input path; grab JC3's vehicle input model (for D-11).
- **R-3:** build a runtime oracle. Measure in game which resources the drop loaded, and where collision and mesh actually sit, before touching physics again.
- **R-4:** decode both renderers' colour pipelines (UE3 material plus probe versus JC3 `CarPaintMM` plus palette and tint) far enough to state whether an exact conversion exists. If it doesn't, write down what the closest defensible mapping depends on.
- **R-5:** reconcile `T_ROWS.jsonl` against the built files: for every row, translated / not / guessed, with the evidence.
- **R-6:** decode the 925 untagged objects that touch the vehicle (handling, upright, visual damage, materials).

## 7. Backlog made exhaustive (2026-11-02, later)

The research list R-1..R-6 is now the backlog's Phase G3 (`GRAB_BACKLOG.md` §6b, cards G3-01..G3-11,
tracker rows `open`). Mapping: R-1 → G3-01 + G3-10, R-2 → G3-02 + G3-08, R-3 → G3-07, R-4 → G3-04 + G3-09
(+ G3-03), R-5 → G3-11, R-6 → G3-05 + G3-06 + G3-12 (JC3 donor decode depth: 566/566 files named, depth unmeasured).

**New finding while auditing (G3-01):** BmAK's drivable collision was there all along and was missed.
The archetype `Vehicle.Batmobile` has two dedicated collision meshes, `BatmanCollisionMeshPursuitMode0` and
`BatmanCollisionMeshBattleMode0`, plus `CollisionCylinder`, `FrontCollisionCylinder` and
`RearCollisionCylinder`, and an `RB_StayUprightSetup`. All of them are only partly decoded. They are
instances of `Default__RVehicleBatmobile.*` class defaults in `BmGame.upk` (imports 456/457/577/578), and
that package was only value-hunted, never decoded for them. The asset references (which StaticMesh, what
size) live in those defaults.

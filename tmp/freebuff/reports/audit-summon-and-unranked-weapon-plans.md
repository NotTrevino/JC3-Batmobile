# Audit — summon (drive-in) and unranked-weapons plans: does the cited JC3 carrier exist?

**Reports audited (not edited):** `tmp/freebuff/reports/summon-drive-in-closest-system.md` (S-claims) and
`tmp/freebuff/reports/unranked-weapons-closest-system.md` (W-claims).
**Question per claim:** does the cited carrier/member **and** the cited file exist in `Research/JC3Grab`,
`Research/BatmobileGrab` or `Working/Translation`, and does the file actually say that?
**Method:** each citation was opened at the named file/line; "found" means the path resolves as written.
Verdicts: **VERIFIED** = file says it; **OVERSTATED** = the evidence exists but does not support the
strength of the claim; **UNSUPPORTED** = the cited file/line does not contain it (or the claim is
contradicted by the cited file).

---

## Claim table

| # | claim | cited path (as written) | found? | what the file actually says | verdict |
|---|---|---|---|---|---|
| S1 | the donor ships **five `_ai.vmodc` modules**, all graded FULL, sizes 1345 / 523 / 445 / 1494 / 1073 B | `Research/JC3Grab/DECODE_DEPTH.md:539-543` | yes (rows 539–543 are at file lines **609–613**) | five rows: `…_ai.vmodc` 1345, `…_brakes_ai.vmodc` 523, `…_land_aerodynamics_ai.vmodc` 445, `…_land_global_ai.vmodc` 1494, `…_land_steering_ai.vmodc` 1073 — every one `embedded / FULL` | **VERIFIED** (the numbers are table row ids, not line numbers — cite 609–613) |
| S2 | `global/global.blo` carries 31 traffic-rule names, 41 tag selectors, Driver seats, 10 `ai/bts/…` paths | `Research/JC3Grab/TRAFFIC.md` §3 | yes | `TRAFFIC.md:105`: "**31 traffic-rule names**, **41 tag selectors** … and **10 AI behaviour-tree paths**", with the rule→`Driver`+`ai/bts/…` mechanism spelled out | **VERIFIED** |
| S3 | the donor's tags satisfy exactly one selector, `ambient,ground,car,liberated,-highend`, whose rule is `03_CivilianCarLiberatedProvince` | `Research/JC3Grab/TRAFFIC.md` §3 | yes | `TRAFFIC.md:111` — that selector row, that rule name, matched = yes; `:119` lists the rule among the 31 | **VERIFIED** |
| S4 | that rule pairs the car with `ai/bts/civilian/civilian_std.bts` | `Research/JC3Grab/TRAFFIC.md` §3 | partly | `TRAFFIC.md:105` states the *mechanism* (selector + `Driver` + `ai/bts/…`) and gives a tank example, but the string `civilian_std` **does not appear anywhere in TRAFFIC.md**; it appears once, in `tmp/freebuff/probe/global.blo` (the report's own probe) | **OVERSTATED** — true of the probe file, not of the cited file; cite `tmp/freebuff/probe/global.blo` |
| S5 | the index has **0 `.bts` entries**, so the tree's members cannot be read | `Research/JC3Grab/INDEX.jsonl` (`grep -c '\.bts"'`) | yes | `grep -c '\.bts"' INDEX.jsonl` → **0** | **VERIFIED** |
| S6 | `Limit_Speed.y_max` 35 on the donor and a fleet ordering 22 (bus) / 30 (monster truck) / 35 / 35 / 35 / 40 (tank); `y_min` 2 / 5 / 8 | `E:/Modding/JustCause3/_grab/entities/v0300_….ee.json` (outside the repo) | not in repo | the only in-repo decode is `Research/JC3Grab/VOCABULARY.md:259-260`: `Limit_Speed.y_max` **30 .. 40 (med 35, n=19)** and `y_min` **5 .. 7 (n=19)**; `x_min` 0 .. 0.07, `x_max` 1. The 22 and 30 ceilings and the 2 and 8 floors fall **outside** that decoded band | **UNSUPPORTED in repo** — the low values are unverified against any project file; donor 35/0.1 is inside the band |
| S7 | `CVehicleRule` holds `chance`, `heat_level`, `spawn_event`, `health`, `invulnerable`, all 0 — spawn-rule metadata only | `Research/JC3Grab/DAMAGE_MECHANISMS.md:46-47` | yes | "`CVehicleRule.health / invulnerable` (59 objects, 8 entities) is **spawn-rule metadata** (`chance`, `heat_level`, `spawn_event`); all values are 0 and it does not damage anything" | **VERIFIED** |
| S8 | Rebel Drop has no position/destination field; the car appears at the drop marker's transform; "(menu, pricing, delivery animation) is code" | `Research/JC3Grab/REBELDROP.md:359`, §2 | yes | `REBELDROP.md:359-360`: "how the game consumes an item (**menu, pricing, delivery animation) is code**" — quoted accurately. The "no position field" half rests on §2's 26-member `Item` table, not re-read here | **VERIFIED** (quote verbatim; the structural half is §2's) |
| S9 | BmAK-side citations `CONTROLS.md:135-142`, `COLLISION_SELECTOR.md:79`, `NATIVE.md:119,134`, `CONTROLS_NATIVE2.md:34`, `PACKAGES_G305.md:565`, `GADGET_PARAMS.md` | bare filenames | yes, but not at that path | all six exist under **`Research/BatmobileGrab/`**, none under `Research/JC3Grab/`; written bare in the plan they do not resolve | **UNSUPPORTED as written** — prefix is missing, not the evidence |
| S10 | `vehicle_delivery.gsc` 35,799 B; `msub_vehicle_controller.gsc` 67,143 B; seven ADF v4 graphs | `Research/JC3Grab/INDEX.jsonl` | yes | INDEX rows: `graphs/random_encounters/vehicle_delivery.gsc` size **35799**; `graphs/mission/modules/msub_vehicle_controller.gsc` size **67143** (extracted copies in `tmp/freebuff/probe/gsc/`) | **VERIFIED** (sizes); node/data counts are the report's probe output, not re-derived |
| S11 | `SVehicle.MaxSpeed` 4000.0, `SelfDriveAllowBoost` True, `SelfDriveCanJumpDown` True | `Research/BatmobileGrab/CLASS_DEFAULTS.md:163,179,152` | yes | line 163 `MaxSpeed` (SVehicle) **4000.0**; line 179 `SelfDriveAllowBoost=True`; line 152 `SelfDriveCanJumpDown=True` | **VERIFIED** |
| W1 | cannon donor `w602_mediumtank_canon` (fire_rate 1.75, velocity 500); Vulcan donor `w603_mediumtank_mgun` (0.1, 750); missile donors w614/w618; `w618` fire_rate 0.5, velocity 360 | `Research/JC3Grab/WEAPONS.md` §1–§6 | yes | `:30-31` the two presets with their tune types; `:60-61` fire_rate 1.75 / 0.1, velocity 500 / 750; `:72` w614 0.25, burst 6, cd 5; `:76` w618 0.5, velocity 360 | **VERIFIED** |
| W2 | carrier `v0201_car_capstone_mediumtank_debug.ee`, slot `main_weapon` = `w602_mediumtank_canon`, `secondary (id:00568A74)` = `w603_mediumtank_mgun` | `Research/JC3Grab/WEAPON_WIRING.md:305` | yes | `:305`: "slots on `CCar` …: main_weapon `w602_mediumtank_canon` · secondary (id:00568A74) `w603_mediumtank_mgun`" | **VERIFIED** |
| W3 | cannon fire point `fire_position_0` = (0.247, 0.485, −2.018), parent part `mediumtank_cannon` | `Research/JC3Grab/WEAPON_WIRING.md:314` | yes (line exists) | `:314` is the table **header**; `:315` gives **`w603_mediumtank_mgun`** = (0.247, 0.485, −2.018); `:316` gives **`w602_mediumtank_canon`** = (0, 0.3739, **−5.8174**). The numbers quoted are the machine gun's, not the cannon's | **OVERSTATED / wrong value** — the cannon's own point is (0, 0.3739, −5.8174) |
| W4 | cannon part behaviour `Cannon` (index 38) parented to `Turret` (index 26) | `Research/JC3Grab/WEAPON_WIRING.md:52` | line exists | `:52` is an entity/chassis row ("`v0201_car_capstone_mediumtank_debug.ee` … 2 weapons"); no "Cannon index 38 / Turret index 26" statement appears in the file (grep for `index 38` = 0) | **UNSUPPORTED** |
| W5 | Vulcan fire point (−0.407, 1.552, −0.167) | `Research/JC3Grab/WEAPON_WIRING.md:314` | line exists | the tank's mgun point in that table is (0.247, 0.485, −2.018); (−0.407, 1.552, −0.167) is not in the file — it is the built Batmobile point (`weapon-points-vs-bmak.md`) | **UNSUPPORTED as cited** |
| W6 | `w619_buggy_mgun` on `v0604_car_urga_buggy` is "the only **CCar** whose entity carries a `GatlingGun` part (`weapon_rpm`)" | `Research/JC3Grab/MOVING_PARTS.md:127` | line exists | `:127`: `GatlingGun \| rotating, weapon_rpm \| 24 \| 12 \| 3 \| CBoat, CHelicopter \| **unproven-on-CCar**`; `:170` lists `GatlingGun` among "**Unproven on a car (30)**"; `:61` is a zero-count `GatlingGun` row | **OVERSTATED** — contradicted by the cited line and by the plan's own V-2 ("0 of 24 cars") |
| W7 | `weapon_rpm`'s unit is UNKNOWN | `Research/JC3Grab/MOVING_PARTS.md:71` | line exists | `:71` is about **`rotoscope_rpm_per_cycle`** (20.0 / 50.0) and says its meaning is UNKNOWN; `weapon_rpm` appears at `:61` and `:127` | **UNSUPPORTED line** (conclusion is still right; cite `:61`/`:127`) |
| W8 | `gen_explosion_5m_nodamage.ftune` is the only shipped 0-damage tune (0 player / 0 AI, 5 m, push only) | `Research/JC3Grab/FORCEPULSE.md` §3 | yes | `:108` and `:131`: the tune is listed as a `ForcePulse` source on 2 vehicles, row "`0 / 5`" columns; `:168` uses it as the low end of the spread | **VERIFIED** (existence and role); "only 0-damage tune" is the plan's reading, not re-derived |
| W9 | missile pods: **no** private tune — manifest row `T-WP3` has `"private": null` | `Working/Weapons/manifest.json` | yes | `weapons[]` row: `missile \| T-WP3 \| editor/entities/jc_weapons/06_vehicle/w618_batmobile_missile/w618_batmobile_missile.wtunec` — a private clone **is** assigned (not on disk in `bm-RC2`, only the manifest row) | **MISMATCH (stale)** — "two of four have a carrier" is now three |
| W10 | riot mode: **no** private tune ("none") | `Working/Weapons/manifest.json`; `Research/specs/B-15.md` | yes | manifest row: `riot \| B-15 \| …/riot_batmobile_suppressor/riot_batmobile_suppressor.wtunec` — a clone is registered; `B-15.md` exists | **MISMATCH (stale)** |
| W11 | the fleet has **2** driver slots and no third; no next/prev action | `Research/JC3Grab/WEAPON_WIRING.md` §2b | yes | `:305` lists exactly `main_weapon` + `secondary (id:00568A74)` and `-` for mounted slots; "no third slot" is an inference from that listing | **VERIFIED** (two slots); the "cannot exist" half is derived |
| W12 | the four weapons map to `RBatmobileHeavyCannon` (§11), `RBatmobileCannon` incl. riot group (§8), `RBatmobileMissileLauncher` (§12) | `Research/BatmobileGrab/WEAPONS.md` | yes | section headers at `:647` (§8 Cannon), `:872` (§11 HeavyCannon), `:1011` (§12 MissileLauncher), `:1059` (§13 Joker launcher) | **VERIFIED** |
| W13 | `AutoAim` has no duration, no heat member, bullet damage 1…3000 / impulse 0…100 | `Research/JC3Grab/WEAPONS.md` §3, §9, §10 | yes | `:296` §9 Lock-on/`AutoAim`; `:424` §10 "What the card asked for" incl. the absences; `:84` §3 damage/impulse table | **VERIFIED** |

---

## Claims the next review must downgrade

**From `summon-drive-in-closest-system.md`**

1. **S6 — the `Limit_Speed` fleet table.** Present 22 / 30 / 2 / 8 as *probe readings from the entity
   grab*, not as fleet fact: `VOCABULARY.md:259-260` decodes `y_max` 30..40 and `y_min` 5..7 (n=19), so
   the bus 22, the truck 30 and the `y_min` 2/8 rows sit outside every in-repo observation. The donor's
   35 and 40 are inside it.
2. **S4 — the `civilian_std.bts` pairing.** TRAFFIC.md gives the mechanism and the rule name, not this
   tree; the binding is a probe finding. Cite `tmp/freebuff/probe/global.blo` and say so.
3. **S9 — six bare BmAK citations.** Prefix `Research/BatmobileGrab/` (`CONTROLS.md`,
   `COLLISION_SELECTOR.md`, `NATIVE.md`, `CONTROLS_NATIVE2.md`, `PACKAGES_G305.md`, `GADGET_PARAMS.md`);
   as written they point at `Research/JC3Grab/`, where none exists.
4. **S1 — the `:539-543` line numbers.** Those are table row ids; the rows are at `DECODE_DEPTH.md:609-613`.

**From `unranked-weapons-closest-system.md`**

5. **W3 — the cannon's fire point is wrong.** The plan puts (0.247, 0.485, −2.018) on the cannon; that
   row belongs to `w603_mediumtank_mgun`. The cannon's own `fire_position_0` is **(0, 0.3739, −5.8174)**
   (`WEAPON_WIRING.md:316`). The muzzle geometry in §1.2 is therefore the Vulcan's, and any claim that the
   cannon muzzle "matches BmAK at 0.000 cm" needs re-deriving against the right row.
6. **W4 — `Cannon` index 38 / `Turret` index 26.** No such statement is in `WEAPON_WIRING.md`; either
   find the table that carries the part-behaviour indices or drop the parent/child claim.
7. **W6 — `GatlingGun` on a `CCar`.** `MOVING_PARTS.md:127` marks it `unproven-on-CCar`; `:170` lists it
   under "Unproven on a car (30)". §2.2's "the only CCar whose entity carries a GatlingGun part" must
   become "a candidate donor, unproven on a car", which is what §2.4 already says.
8. **W9 / W10 — the build-state section is stale.** `Working/Weapons/manifest.json` carries private tunes
   for the missile (`w618_batmobile_missile.wtunec`, T-WP3) and the riot mode
   (`riot_batmobile_suppressor.wtunec`, B-15). §0.1's "two of four have a carrier, two have none" should
   read "three recipes are registered in the manifest; only cannon and Vulcan are on disk in `bm-RC2`".
9. **W5 / W7 — two citations point at the wrong line.** The Vulcan point is not in `WEAPON_WIRING.md`
   (cite the build report); `weapon_rpm` is at `MOVING_PARTS.md:61`/`:127`, not `:71`.

---

## Limits

* Static reads only; no build run, no game. The 232-module / entity-grab values that live outside the
  repo (`E:/Modding/JustCause3/_grab/…`) were not opened and are marked accordingly.
* The probe artefacts (`tmp/freebuff/probe/global.blo`, `probe/gsc/*.gsc`) exist and were checked for the
  `civilian_std` string only; their decoded node/hash counts were not re-derived.
* Neither report was modified. This audit touches only this file. **Revert:** delete this file.

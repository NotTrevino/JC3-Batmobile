# G2-35 — the carriers sections 8 and 9 name, scored against the four required properties

Read for this note: sections 8 and 9 of `tmp/freebuff/reports/carrier-ram-and-dodge.md`
(§8 rows at `:237-253`, the §9 capability statement at `:249-260`), the card
`Research/specs/G2-35.md`, the tracker row `GRAB_BACKLOG.md:1857`, and the three grab files those
sections cite: `Research/JC3Grab/VOCABULARY.md`, `Research/JC3Grab/FORCEPULSE.md`,
`Research/JC3Grab/DRIVE_CARRIERS.md`. Nothing was installed, built or launched; the card and the
backlog were read only.

`decoded` = a member and value read at the file and line named; `derived` = a rule over decoded
inputs; `UNKNOWN` = the cited files do not settle it, with the file that would.

## 0. Count

| verdict | count |
|---|---:|
| candidates listed in §8/§9 | **5** |
| satisfy all four properties (trigger, non-damaging, target selection, duration) | **0** |
| best partial | **1** — `CForcePulse` (3 of 4) |
| properties no candidate supplies at all | **duration** (0 of 5) |

## 1. Every carrier §8/§9 names, with its file and line

| # | carrier | file:line | what that line says |
|---|---|---|---|
| 1 | `drift.max_drift_torque` | `Research/JC3Grab/VOCABULARY.md:479` | `float | 0 .. 35000 (med 12000, n=145) | 5000` |
| 2 | `drift.counter_steer_torque` | `Research/JC3Grab/VOCABULARY.md:469` | `float | 0 .. 60000 (med 10000, n=145) | 3000` |
| 3 | `arcade.nitro_boost.push_force` | `Research/JC3Grab/VOCABULARY.md:448` | `float | 15000 .. 15000 (med 15000, n=145) | 15000` |
| 4 | `CForcePulse` impulse members | `Research/JC3Grab/FORCEPULSE.md:31` and `:46` | `id:24872388` 25..1000 (6 distinct, 307 pulses); `id:9865E7F2` 25..250 (5 distinct, 307) |
| 5 | `arcade.turbo_jump.*` | `Research/JC3Grab/VOCABULARY.md:455-460` | `f_multiplier` 12..15, `punch_delay_time` 0.1, `punch_speed_kph` 50, `r_multiplier` 12, `top_speed_jump_multiplier` 2, `top_speed_kph` 200 (n=145) |

The carrier report's own mapping lines, for the join back to BmAK: `:237` and `:240` (road-assist max
torque and `PMDodgeTorque` → `drift.max_drift_torque`), `:238` (angle strength →
`drift.counter_steer_torque`), `:241` (`PMDodgeForce` → `nitro_boost.push_force`), `:244`
(`BattleDodgeImpulse` → `CForcePulse`), `:245` (`VehicleShovingTorque` → `drift.max_drift_torque`),
`:249-253` (`turbo_jump`, "the closest thing to `BattleDodgeImpulse` **in shape** … no target
selection").

## 2. The four properties, per candidate

Machine-readable copy: `Working/Prep/g2_35_candidates.csv` (columns `carrier, file, line, trigger,
damaging, target_select, duration, verdict`; 5 data rows, every field quoted).

| carrier | trigger | damaging | target selection | duration | score |
|---|---|---|---|---|---|
| `drift.max_drift_torque` | **no** — a continuous state, not an event (`DRIVE_CARRIERS.md:118` "yaw torque / slide shaping"; §8 `:237` "wrong trigger") | no — a yaw torque on the own car, no damage member named | no — own car only | no — no duration member | 1/4 |
| `drift.counter_steer_torque` | **no** — same, a continuous counter-steer assist (§8 `:238` "wrong trigger") | no | no | no | 1/4 |
| `arcade.nitro_boost.push_force` | **UNKNOWN** — "What fires `arcade.nitro_boost`" is §7 UNKNOWN item 2 (`DRIVE_CARRIERS.md:364`); no keymap action exists | no — a forward force, no damage member | no — forward force on the own car | no — `boost_blend_time` 0.2 (`DRIVE_CARRIERS.md:297`) is a ramp, not a duration | 1/4 |
| `CForcePulse` | **yes, but explosion only** — `FORCEPULSE.md:3` "Trigger: explosion, and the owner says which explosion"; `:181` "collision 0 of 23 tune paths mention collision; no pulse owner is a collision object" | **partial** — `gen_explosion_5m_nodamage.ftune` carries `0 / 5` damage (`FORCEPULSE.md:131`, listed `:108`) on 2 pulses; the other 21 tunes do damage | **partial** — the blast radius in the tune (e.g. `500 / 5` on `car_explosion_medium.ftune`, `FORCEPULSE.md:139`) selects by position, not by actor type | **UNKNOWN** — `id:57F1B4E1` is `0.1 .. 0.25` on all 307 (`FORCEPULSE.md:34`) and no member is *named* duration; the names are "in no shipped name table" (`FORCEPULSE.md:19-20`) | 3/4 |
| `arcade.turbo_jump.*` | **yes, but jump action only** — `DRIVE_CARRIERS.md:33` "fixed-direction impulse block, 6 members"; §8 `:253` "it fires on the jump action, not on a dodge" | no — an impulse block, no damage member | no — `DRIVE_CARRIERS.md:350` "Neither block takes a direction"; §8 `:253` "no target selection" | no — `punch_delay_time` 0.1 s (`VOCABULARY.md:456`) is a delay before the punch and `turbo_jump_cooldown` 5 s (`VOCABULARY.md:1567`) is a cooldown; neither is a duration | 2/4 |

No candidate above was scored on a property the cited files leave open: each cell is either a member
read at the line shown or an explicit UNKNOWN with the file that would settle it.

## 3. Best partial, and the single build step that would close the remaining gap

**Best partial: `CForcePulse`** — 3 of 4. It is the only candidate with an event trigger, a
non-damaging tune already in the fleet, and a positional selection; what it lacks is a *vehicle-fired*
trigger and a named duration.

**The single step:** bind one of the **14 owner-less `CForcePulse` objects** under a
`CShapeTrigger`/`CEventTrigger` in the vehicle's `.epe` graph, so the pulse fires from a car event
instead of an explosion. That step is the card's own instruction, in order:
`Research/specs/G2-35.md:61-62` — "the 14 `CForcePulse` objects with UNKNOWN owners (bind one to a
`CShapeTrigger`/`CEventTrigger`, which today fire no pulse)". The 14 are recorded as UNKNOWN owners in
`FORCEPULSE.md:10-13`, not explained, so the step is a graph edit in a private copy and not a value
translation.

**What that step does not close:** duration stays UNKNOWN after the bind. It is settled by resolving
the pulse's hashed member names — `FORCEPULSE.md:33-34` (`id:57F1B4E1` 0.1..0.25 is the only
duration-shaped member) — or by an in-game probe, which the test ban forbids. Target selection would
be positional (inside the trigger volume), not the actor-type selection the card asks for.

The alternative best-partial reading is `arcade.turbo_jump.*` at 2/4, and it is the one §8 `:249-253`
calls closest *in shape*. It is not chosen because the jump action is the only trigger, the impulse is
fixed to the car's own axes (`DRIVE_CARRIERS.md:350`), and it has neither a target nor a duration —
two hard failures against `CForcePulse`'s one.

## 4. UNKNOWN, and what would settle each

| # | UNKNOWN | would be settled by |
|---|---|---|
| 1 | What fires `arcade.nitro_boost` (so whether `push_force` is even event-triggered) | the native action table / a keymap carrying a boost action — `DRIVE_CARRIERS.md:364`, §7 UNKNOWN 2 |
| 2 | The name and unit of `CForcePulse`'s hashed impulse members `id:24872388` / `id:9865E7F2` | a BmSDK/`.g.cs` binding for `CForcePulse`, or `FORCEPULSE.md` §1's name search extended (`FORCEPULSE.md:355`, UNKNOWN 5) |
| 3 | Whether `id:57F1B4E1` (0.1..0.25, 307 pulses) is the pulse duration | the same name resolution as (2), or an in-game probe |
| 4 | Whether `turbo_jump_cooldown` (`VOCABULARY.md:1567`, n=233) gates an impulse we could re-point, i.e. whether a dodge could share the jump's action | `arcade.turbo_jump`'s consumer in the engine; no decoded file names it (`DRIVE_CARRIERS.md:352-356`) |
| 5 | Whether the 14 owner-less pulses can be fired by a `CShapeTrigger` that today fires nothing | a private-copy graph edit plus a launch — forbidden by the test ban (`Research/specs/G2-35.md:35`) |

`COMPROMISES`: none. No value was tuned, no ledger row and no card was edited, and the card's
prediction in §3 is untouched.

## 5. Files, and revert

**Written:** `Working/Prep/g2_35_candidates.csv` (the table in §2, 5 rows) and this note.
**Untouched:** `Research/specs/G2-35.md`, `GRAB_BACKLOG.md`, `Working/Translation/T_ROWS.jsonl`, and
every file read above.

**Revert:** delete `Working/Prep/g2_35_candidates.csv` and
`tmp/freebuff/reports/g2-35-impulse-candidates.md`. Nothing else changed.

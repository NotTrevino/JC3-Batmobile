# Interaction translation (T-13)

Every interaction object in the Serpente donor `.epe` placed on the **Batmobile** body, by
role, with a transform (position, forward, up, yaw) and a measured distance to the hull.
Rebuilt by `python Tools/scripts/t9_interaction.py --check` from
`Research/JC3Grab/INTERACTION.json` (digest `da864a28edcbcbff`) and the body mesh
`Working/TrueScale/body_lod1.rbm` (20000 triangles, 28940 vertices).

## 1. Decision applied

`D-9` is **resolved 2026-10-28 (user): no**: hijack objects (*pull.out*, *pulled.out*) dropped.
They keep a transform for completeness but are not part of the port.

## 2. Method

Frame (JC3, the same one as COCKPIT.md): x lateral (left = -x), y vertical (ground 0.020),
z longitudinal, nose at -z. Each object's role picks an anchor on the body shell, found by a
ray cast against the body mesh; the transform sits `clearance` metres outward along the
anchor normal.

| anchor | surface point (m) | normal | target clearance |
|---|---|---|---|
| `hood` - front deck - topmost body surface at z -2.14 | [0.0005, 1.3606, -2.14] | [0.0, 1.0, 0.0] | 0.06 m - decoded (donor stunt-area gap 0.048 m, band floor applied) |
| `roof` - roof - topmost body surface at z -0.5 (canopy over the driver) | [0.0005, 2.0811, -0.5] | [0.0, 1.0, 0.0] | 0.1474 m - decoded (donor stunt-area gap 0.1474 m, band floor applied) |
| `left` - cockpit left side ray, y 1.15, z -0.95 | [-1.471, 1.15, -0.95] | [-1.0, 0.0, 0.0] | 0.1 m - chosen (band midpoint; donor side clearance not decoded - UNKNOWN) |
| `right` - cockpit right side ray, y 1.15, z -0.95 | [1.462, 1.15, -0.95] | [1.0, 0.0, 0.0] | 0.1 m - chosen (band midpoint; donor side clearance not decoded - UNKNOWN) |

The `Driver` socket is the seat transform: [-0.0025, 0.8647, -1.0654] m, forward (0, 0, -1) (COCKPIT.md §2).

## 3. Counts

| item | count |
|---|---|
| objects | 85 |
| placed | 77 |
| dropped_D9 | 6 |
| socket | 1 |
| unknown | 1 |
| in_band | 77 |

| role | objects |
|---|---|
| `driver` | 29 |
| `hood` | 9 |
| `passenger` | 25 |
| `seat.driver` | 1 |
| `seat.passenger1` | 1 |
| `seat.stunt` | 1 |
| `stunt` | 19 |

## 4. Every object

| object | role | disposition | anchor | pos (m) | clearance (m) | nearest (m) | inside | verdict |
|---|---|---|---|---|---|---|---|---|
| `interaction.seat.driver` | seat.driver | socket | socket | -0.0025, 0.8647, -1.0654 | 0 | 0.0279 | no | inside by design (the seat is in the cockpit) |
| `entry.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `point.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.default` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.ai.driver.default` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.driver.to.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `exit.driver.roll.out` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.moving.parachute` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.ai.driver.default90R` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.pushed.out` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.ai.driver.default90L` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.to.fall` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.ai.driver.default180` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.to.swim` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `exit.ai.driver.default0` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.driver.pulled.out` | driver | dropped (D-9) | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.passenger1.exit` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.driver.upside.down` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `point.passenger1.onground` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `transition.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `transition.passenger1.side` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.ai.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.jump_to_stunt_vehicle_to_vehicle` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.driver.pull.out.onground.no.door` | driver | dropped (D-9) | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `point.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `exit.from.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `point.passenger1.side` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `transition.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `transition.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.pull.up.to.stunt.hood.close` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `entry.stunt.to.driver.side.enter.vehicle2` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.stunt.to.driver.side.enter.vehicle3` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.passenger1.no.door` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.reel.to.stunt.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `entry.reel.to.stunt.main` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.passenger1.pull.out.onground` | passenger | dropped (D-9) | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.pull.up.to.stunt.hood.far` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `entry.passenger1.side.fast` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.step.over.low.stunt.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `entry.pull.up.to.stunt.close` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.jump_to_stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.driver.locked.onground` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `point.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.passenger1.default` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.passenger1.roll.out` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.passenger1.default90L` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.passenger1.default180` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.passenger1.default` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `transition.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `exit.passenger1.upside.down` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.passenger1.default0` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.passenger1.pulled.out` | passenger | dropped (D-9) | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `exit.ai.passenger1.to.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `exit.ai.passenger1.default90R` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.passenger1.pull.out.onground.no.door` | passenger | dropped (D-9) | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.step.over.high.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `point.stunt.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `exit.from.stunt.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `point.driver.onground` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.driver.side` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `entry.driver.pull.out.onground` | driver | dropped (D-9) | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `entry.stunt.to.driver.side.enter.vehicle` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.step.over.low.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.passenger1.locked.onground` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `entry.step.over.high.stunt.hood` | hood | placed | hood | 0.0005, 1.5265, -2.14 | 0.1659 | 0.0573 | no | in band |
| `entry.ai.driver.left` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `entry.pull.up.to.stunt.far` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.driver.side.fast` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `point.driver.side` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `transition.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `entry.driver.no.door` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `trigger.driver` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `trigger.step.to.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `trigger.driver.fast` | driver | placed | left | -1.571, 1.15, -0.95 | 0.1 | 0.0969 | no | in band |
| `interaction.seat.stunt` | seat.stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `trigger.passenger1` | passenger | placed | right | 1.5744, 1.15, -0.95 | 0.1124 | 0.1001 | no | in band |
| `trigger.stunt.vehicle.to.vehicle` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `interaction.seat.passenger1` | seat.passenger1 | unknown | - | - | - | - | - | UNKNOWN - the Batmobile cockpit has one seat (COCKPIT.md §1); no analogous location for a passenger seat |
| `trigger.stationary.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |
| `trigger.stunt` | stunt | placed | roof | 0.0005, 2.2467, -0.5 | 0.1656 | 0.1453 | no | in band |

## 5. The Done rule

`--check` asserts, for every **placed** object: nearest hull triangle >= 0.05 m and
<= 0.3 m, and the point is not inside the hull. The `Driver` socket is the one
documented exception - a seat is inside the cockpit by definition - and
`interaction.seat.passenger1` has no transform because the Batmobile cockpit has one seat.

## 6. UNKNOWNs and limits

* **Donor clearance for entries, exits, transitions, points and triggers is not in any
  decoded file.** G2-18 recorded the donor gap only for the three stunt areas (0.048 m hood,
  0.1474 m roof); the side anchors therefore use a chosen 0.10 m inside the card's band and
  the choice is labelled, not presented as a game value.
* **No passenger seat exists** on the Batmobile (COCKPIT.md §1: one cockpit tub, one seat),
  so `interaction.seat.passenger1` is UNKNOWN rather than placed.
* Side anchors are one station per side (y 1.15, z -0.95); the card does not ask for a
  per-object lateral spread, and the donor's world positions are mostly inherited container
  origins (70 of 85), so there is nothing finer to copy.
* Yaw is `atan2(forward.x, -forward.z)` in degrees, the project's JC3 convention (forward =
  -z at 0); it is derived from the anchor normal, not decoded from the donor.

## 7. Reproduce

```
python Tools/scripts/t9_interaction.py --write
python Tools/scripts/t9_interaction.py --check
```

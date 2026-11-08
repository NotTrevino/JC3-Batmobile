STATUS: done

The stale wheel-part `parent_space_offset` is **harmless at run time**, not visible and not
physics-affecting. JC3 does not place a `Wheel` part from that transform:

* **Wheel mesh** — placed at the `land_global.base_wheel_hardpoint_positions` hardpoint. Live
  test-047 (MODLOG §58) moved *only* the four hardpoints, with the parts module unchanged
  (`parent_space_offset` still ±0.885, 0.400, ±1.557/1.446 at test-047/053), and the wheels moved;
  test-053 reverted them and was quiet. Test-060 aligned at true scale with the same stale pso.
* **Wheel collision** — sim-only: the four wheel parts have `has_world_collision_shape = 0` and
  `world_collision_body_id = -1`, so no part-placed hull exists to move.
* **Suspension raycast** — the four `raycast_body_id` values 22/23/36/37 are exactly the four
  non-zero body entries of the built `.physicsc`'s `hknpPhysicsSystemData`, and those entries carry
  the Batmobile hardpoints (-1.208/0.7047/-2.57, 1.208/0.7047/-2.5699,
  1.2845/0.7027/2.4589, -1.2845/0.7027/2.4589). Decoded byte evidence, not a guess.

The maximum component delta is 1.0130 m (front z / rear z); the pso remains byte-identical to the
donor Serpente's. It is a real data inconsistency, but dormant. No wheel part has children in the
built module, and the four arch parts resolve to the true hubs through their own transforms with
non-wheel parents, so the stale pso is not load-bearing for an attachment either.

**Manifest field that would need to change:** `parent_space_offset` of the four wheel parts, as
carried in the B-04 parts manifest `Working/Parts/bm_vehicle_parts.json` (the module is generated
from `Working/Appearance/build_parts/parts_manifest.json` plus B-04's rows). Do not touch the hub
data: `base_wheel_hardpoint_positions` and the `.physicsc` body-entry positions are already
correct. Changing the pso alone would not move a wheel at run time; if the record is to be made
self-consistent, set each wheel pso to its hardpoint and re-derive the four arch offsets in the
same change. No edits were made.

## Files written

* `Tools/scripts/v_wheel_offset.py` (new, `--write` / `--check`)
* `Builds/bm-RC2/verify/wheel_offset_effect.md` (new, generated)
* `tmp/freebuff/reports/wheel-offset-effect.md` (this report)

Read-only inputs: the built parts module, built `land_global`, built `sportsmuscle.physicsc`, the
donor parts module (`Builds/test-091`), `Working/Parts/bm_vehicle_parts.json` and `MODLOG.md`.
Nothing under `Builds/` other than the new verify page was written; no manifest, build or game file
was edited.

## Commands and output (verbatim)

```
$ python Tools/scripts/v_wheel_offset.py --write
wrote Builds/bm-RC2/verify/wheel_offset_effect.md
$ python Tools/scripts/v_wheel_offset.py --check
PASS: 4 wheel pso are donor-stale (max 1.0130 m from the hubs); 4/4 raycast bodies sit on the hardpoints; wheel hulls 4 body entries non-zero; MODLOG evidence 4/4
exit=0
```

Key decoded values (also in the page):

| wheel | part pso (m) | hardpoint (m) | delta (m) | raycast id → entry |
|---|---|---|---|---|
| `sportsmuscle_wheel_f_l` (26) | (-0.8850, 0.4000, -1.5570) | (-1.2080, 0.7047, -2.5700) | (+0.3230, -0.3047, +1.0130) | 22 → (-1.2080, 0.7047, -2.5700) |
| `sportsmuscle_wheel_f_r` (27) | (0.8850, 0.4000, -1.5570) | (1.2080, 0.7047, -2.5699) | (-0.3230, -0.3047, +1.0129) | 23 → (1.2080, 0.7047, -2.5699) |
| `sportsmuscle_wheel_r_r` (12) | (0.8850, 0.4000, 1.4460) | (1.2845, 0.7027, 2.4589) | (-0.3995, -0.3027, -1.0129) | 37 → (1.2845, 0.7027, 2.4589) |
| `sportsmuscle_wheel_r_l` (11) | (-0.8850, 0.4000, 1.4460) | (-1.2845, 0.7027, 2.4589) | (+0.3995, -0.3027, -1.0129) | 36 → (-1.2845, 0.7027, 2.4589) |

The built `.physicsc` has 62 `hknpPhysicsSystemData` body entries; exactly 4 carry a non-zero
position, and those 4 are the hardpoints above. `jc3hkx.stations()` prints 0 sets because it groups
four entries by a single `y` and the car has two hub heights (0.7047 front / 0.7027 rear) — a reader
limitation, not a missing table.

## UNKNOWNs

* **The engine branch that special-cases a `Wheel` part's mesh placement.** The live 047/053/060
  tests prove the behaviour and the hardpoint/raycast bytes agree, but no decoded engine symbol in
  the repo shows the branch; the page therefore records behaviour, not a code path.
* **Any other consumer of a wheel part's `parent_space_offset`.** None exists in the build; a tool
  that renders parts verbatim would show the 1.013 m offset. That is the only way this value could
  become visible.
* **Why the body-entry table has two hub heights.** The four entries are individually correct and
  match the hardpoints; only the four-in-one-`y` grouping in `jc3hkx.stations()` fails on this
  vehicle.

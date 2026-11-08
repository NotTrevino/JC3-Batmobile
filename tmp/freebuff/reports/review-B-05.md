# Independent review — B-05 · Entity graph (`.epe`)

**Scope.** Read-only review of `GRAB_BACKLOG.md` §0.5/§8/§12, `MODLOG.md` §"B-05 · Entity graph (`.epe`) — done",
`tmp/freebuff/reports/B-05.md`, `Working/Entity/bm_epe_edits.json`, `Tools/scripts/bm_entity.py` and the built
`Builds/bm-005/.../v0300_car_kensington_sportsmuscle_civilian_01.epe`. The only file written is this report.
The card's command was re-run; the built `.epe` was exported with `ConvertProperty --e` into OS temp dirs and
`Builds/bm-009` was exported the same way for comparison. No game launch, no git, no install.

## VERDICT: **needs rework**

The three Done criteria pass mechanically and the big numbers (bytes, sha, 9 points, 28 lights, 4 components,
19 parts, 51 additions) reproduce. But two of the graph's own Done-2 claims are false against the built file —
one `SWeaponPoint` member still references a donor part that does not exist in the Batmobile module, and the
check is written so it cannot see it — two of the four weapon components are unreferenced by any root slot
(so the missiles cannot fire), and both `w618` components carry `weapon_type` 1 while the measured donor
carries 2. Those are data/provenance defects, not presentation nits, so the build has to be regenerated.
Everything else below is documentation accuracy.

## Check output (verbatim)

```
$ python Tools/scripts/bm_entity.py --check
PASS: 4 weapon component(s), 9 weapon point(s), 28 light(s) (6 T-18 custom), 19 part name(s) resolve, 0 dangling | objects 416 + 51 = 467 | round trip identical
EXIT=0
```

Both Out paths exist: `Working/Entity/bm_epe_edits.json` (33,082 B) and the `.epe` in `Builds/bm-005`
(124,520 B, sha256 `d118c0aa29167a5e6b695321a3e964b5b61e1bdfa7f5b5656277977c6c395c3d`). The card's Done line
("ConvertProperty round-trips …; every weapon point, light and part name resolves (script check); `.epe`
object count = base + planned additions") does map onto the three arms of `check()`, but two of those arms
verify less than the sentence says (issues 1 and 6).

## Issues

### 1. `attach.vehicle` still binds a donor part that is not a Batmobile part — "0 dangling" is false
**Where:** built `.epe`, all four `attach.vehicle` objects, value `id="A90F5E74"` = `weapon_anchor`;
`Tools/scripts/bm_entity.py:632` and `:664`; `tmp/freebuff/reports/B-05.md` Done-2 section and `MODLOG.md:18215`.
**Why:** each `attach.vehicle` object carries **three** part-name strings, not two. The build rewrites the
first two (`id:5C19E7E0` → `batmobile_cannon` / `batmobile_machine_gun` / `batmobile_missile_pod_r`;
`id:80201E4D` → `batmobile_turret` / `batmobile_missile_pod_l`) and leaves the third inherited from the APC:
`weapon_anchor`. `weapon_anchor` is not in `Working/Parts/bm_vehicle_parts.json` (19 names) and the string is
absent from `sportsmuscle_vehicle_parts.vmodc`. So the built graph has a dangling part reference, the claim
"all four `attach.vehicle` points bind only B-04 part names" is false, and so is the PASS text "0 dangling"
(which is a literal string in the f-string, not a computed count).
The check cannot catch it by construction: line 632 only inspects string props that `startswith("batmobile_")`,
so any inherited non-`batmobile_` name is invisible; line 635's "every part name" loop compares the parts list
to itself (see issue 6).

### 2. Both missile components are dead weight — no root slot references them, and this is not in the limits
**Where:** built `.epe`; `CCar` slots `851CAABE` → `DF009C2C=FFFF8002` (w602) and `00568A74` → `DD9B64C0=FFFF8005`
(w603), `AC0BC788` = `00000000`, `mounted_weapon` = `00000000`. `w618_sportsmuscle_missile` (`8AE3029C=FFFF8008`)
and `w618_sportsmuscle_missile_emp` (`AAE79E16=FFFF800C`) each occur exactly once in the exported XML — at their
own `_object_id`. `MODLOG.md:18152-18159` and `tmp/freebuff/reports/B-05.md` step 2.
**Why:** the card serves WPN; a component with no root pointer is called "dead weight" by the project's own
`Research/JC3Grab/WEAPON_WIRING.md:31`, and `Working/Translation/T7_WEAPONS.md:68` had already concluded that
WPN-3's missiles are left without a slot (it also lists T-WP4 as **blocked** at line 10). Neither the MODLOG
step-2 bullet nor the report's four "limits" says that the two w618 components cannot fire. Presenting "4
components" and 3 missile points as done, while the actual carrier count for the missiles is zero, is an R5
problem: the members exist, the behaviour does not.

### 3. `weapon_type` 1 on both w618 components contradicts the measured donor value (2), with no provenance
**Where:** `Tools/scripts/bm_entity.py:89-110` (`"weapon_type": 1` in the T-WP3 and T-WP4 entries); built
`.epe` `weapon_type` = 1 for `w618_sportsmuscle_missile` and `…_emp`.
**Why:** the shipped donor is `CMissileWeaponBase w618_sportsmuscle_missile …, weapon_id 618, weapon_type 2`
(`Research/JC3Grab/SIGNATURE_DIFF.md:252`; same in `SIGNATURE_DIFF.json`), and `WEAPON_WIRING.md:31` states
"its `weapon_type` is `2` for every weapon". The `src` string on those two rows cites T-11's row/socket, not a
type; w602/w603 use 2, so the 1 is a typed constant that no input in the repo supports and one measured file
contradicts. R4 (no value without provenance) and R11 (no typed values) both apply. Whether JC3 ignores the
field is UNKNOWN — but that is exactly why it should be copied, not changed.

### 4. The six T-18 custom lights are all placed at the front-left lamp's transform
**Where:** built `.epe`, `sportsmuscle_wheel_f_l_arch_light`, `…_f_r_arch_light`, `…_arch_battle_light`,
`headlight_battle_left_light`, `headlight_battle_right_light`, `boot_light_light`: `id:A04C3B1E` is identical to
base `Front_Left_Point` (`0.7198463,-0.6040228,-0.3420202,0, …`) and `preset_id` is `Front_Left_Point`.
`MODLOG.md:18166-18168`; `bm_entity.py` step 3 writes only `diffuse` for customs.
**Why:** the T-18 custom rows carry per-light `deformable_transform`, `part`/`part_hash`, socket and a measured
`parent_space_offset`; none of that is written, so all six new lamps inherit the front-left lamp's position and
part binding. The MODLOG does say the 11 positional slots are "inherited from that sibling", but neither the
MODLOG nor the report states the consequence (all six sit at one lamp), and the report's Limits section omits it
entirely while the report's opening says the graph "carries … the T-18 lights". It does carry their names and
diffuse colours; it does not carry their placement.

### 5. "467 objects / 47 classes" counts a classless root and a `None` class
**Where:** `GRAB_BACKLOG.md:1338`, `MODLOG.md:18139`, `GRAB_BACKLOG.md:18222` ("467 = 416 + 51").
**Why:** the exported graph has **466** objects carrying `_class` and **46** distinct classes; the 467th
`<object>` is the classless top-level `root` wrapper, and `jc3wiring.parse_epe` yields `cls=None` for it, which
the script counts as a 47th "class". The base is 416 object elements / **415** classed / **43** real classes,
not "416 / 44". The addition count 51 is unaffected (all 51 are classed), but the class figure in the tracker is
wrong by one in both directions. Not a check failure — the same convention is used on both sides — but a
reader of §12 is told the graph has 47 classes when it has 46.

### 6. `--check`'s "part name resolves" arm is a tautology; the module-bytes proof is not in the command
**Where:** `Tools/scripts/bm_entity.py:635-637`:
`for name in parts: if name not in {p["name"] for p in json.load(...)["parts"]}: …`
**Why:** the loop compares the parts dict to the same JSON reloaded, so it can never fail, and the PASS figure
`19 part name(s) resolve` is just `len(parts)` (`:664`), i.e. the length of `Working/Parts/bm_vehicle_parts.json`,
not a number of names resolved in the built module. The real evidence the report prints —
`module bytes 39278 | names in spec 19 | absent from module bytes 0 []` — is true (I reproduced it) but comes
from an unnamed one-off snippet, not from the card's `--check`, so R11's "re-derivable by a command" is not met
for that claim. This is why issue 1's `weapon_anchor` and any future module-name drift pass silently.

### 7. Skip and edit accounting in the report does not match the spec JSON
**Where:** `tmp/freebuff/reports/B-05.md` Limits #3 ("15 of 84 … The other 60 are skipped"); `MODLOG.md:18168`
("13 shipped lights … 19 edits"); `Working/Entity/bm_epe_edits.json`.
**Why:** `skipped[]` has **69** rows — 60 "no named `world` member" **plus 9** `CInteractionGraphTransition` rows
skipped because class+name matches 3 objects. The report names only the 60 and never the 9, so 15 + 60 ≠ 84;
the MODLOG does describe the 9 at `:18175`, so this is a report defect, not a data one. Separately, the light
edits are **12** distinct shipped lights over **16** edit rows (T-L8/T-L25/T-L27 all target
`Sport_Muscle_Headlight_Volume_Left`, same values), and the 19 total edits include the 2 `CCar` slot pointers and
1 `*` interaction row. "13 shipped lights … 19 edits" is not a number the JSON supports.

### 8. Done 3's equality is definitionally true
**Where:** `bm_entity.py` `check()` Done-3 block and `build()` (`expected_objects = BASE_OBJECTS + len(added)`,
`added` = built node paths not in base).
**Why:** `got == 416 + len(added)` holds for any built graph that lost no base object, so the count arm cannot
detect an unplanned addition or a dropped planned one on its own; the 27-row plan is never compared to 51. The
real guard is the semantic plan-vs-built comparison above it (which is why the tamper test works), and the
report's wording ("the plan's own effect, not a constant") overstates what Done 3 proves. Minor, but the claim
"not a number typed into the script" is only true of the 51, not of the 416 (a typed constant, deliberately).

## Spot-checks

| value checked | where verified | result |
|---|---|---|
| `.epe` 124,520 B, sha256 `d118c0aa29167a5e…` | `wc -c` + `sha256sum` on `Builds/bm-005/.../_civilian_01.epe` | match |
| 502,357 B round-tripped XML | `ConvertProperty --e` on the built `.epe` (temp dir) | match |
| 4 components / 9 points / 28 lights = 41 named weapon+light objects, 0 `name_hash` mismatches | re-parsed the exported XML, recomputed `rbmhdr.hash_jenkins(name)` per object | 41, 0 mismatches |
| 32 `w206`-path strings, 4 `50calImpact`, 4 `sound_turret_rotation_yaw` | plain string counts in the exported XML | exactly 32 / 4 / 4 |
| parts module 39,278 B, all 19 B-04 names present | `Builds/bm-009/.../sportsmuscle_vehicle_parts.vmodc` byte search | 39,278 B, 0 absent |

## What was not re-verified

- `--write` determinism (`d118c0aa…` before/after the `addition_rows` dedupe): re-running `--write` rewrites
  `Builds/bm-005`, `Working/Entity` and `receipt.json`, which this read-only review must not do. `--check`
  re-derives and compares in memory and passed, which is consistent with the claim but does not re-prove the
  byte-for-byte determinism.
- In-game behaviour of a loose `.epe` (the report already records this as UNKNOWN) — unchanged by this review.

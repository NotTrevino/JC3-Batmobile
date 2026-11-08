# Independent review - G2-16 (The EMP truck)

Reviewer: independent (did not author the card). Mode: read-only - nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/` or any game path was modified; this file is
the only one written. No game launched, nothing committed.

Card: `GRAB_BACKLOG.md` §2.3 "G2-16 · The EMP truck · S · deps: P0-2 · serves: WPN-4/5".
Row: `GRAB_BACKLOG.md:1299` (status `done`).
MODLOG: intended change `MODLOG.md:9857`, done block `MODLOG.md:9881`.

## VERDICT

**minor issues.** The card is answered and its artfacts are real: both output paths exist, the
`--check` command passes, and the three things the Done line asks for are present - a yes/no
answer (with the weapon-slot half proved by data: 0 `CEMPWeapon` in 88 fleet components), a copy
list, and the evidence behind both. Every number I spot-checked is correct. What keeps it off
"sound" is (a) a validation record in MODLOG that claims an invariant the script does not have,
(b) a handful of true-but-unrecorded claims that `--check` therefore cannot protect - including
one mission claim that is asserted rather than marked UNKNOWN, and (c) `emp_active.effc` in the
copy list although no build that carries it can fire the pulse.

## Check output (verbatim)

```
$ python Tools/scripts/jc3emp.py --check
PASS: 2 builds, 9 variants, 3 device parts, 2 EMP weapons, fleet CEMPWeapon 0
exit=0
```

Out paths named in the row all exist:

```
-rw-r--r-- 1 User 197121 16497 Oct 26 23:51 Research/JC3Grab/EMP.json
-rw-r--r-- 1 User 197121 11107 Oct 26 23:51 Research/JC3Grab/EMP.md
-rwxr-xr-x 1 User 197121 34274 Oct 26 23:49 Tools/scripts/jc3emp.py
```

`Research/JC3Grab/README.md` has the section and Files row the intended-change entry promised
(lines 414, 931).

Done line: "a yes/no answer 'can the EMP effect be fired by a driver of a different vehicle',
with evidence; the list of files that would have to be copied."

* Answer present, `EMP.md:3-9`: "**Answer: yes for the effect, no as a weapon-slot copy.**" - a
  split answer, but each half is tied to evidence rather than left ambiguous.
* Copy list present, `EMP.md:179-197` (§7).
* Evidence: pulse, tune, trigger, variants and the fleet weapon census are all in `EMP.json` and
  asserted by `invariants()`.

## Issues

### 1. MODLOG claims an invariant the script does not implement

`MODLOG.md:9935` (Validation): "Invariants: **both containers 794/454**; ...". `invariants()` in
`Tools/scripts/jc3emp.py:502-579` never reads `trucks[*]["members"]` or `["objects"]` - the strings
794/454 occur in that file only inside the doc prose at `jc3emp.py:262`. So a container losing a
member would be caught by the JSON comparison (build vs stale json) but not by any assertion, and
the record overstates what the checks cover. Small, but the record is the audit trail.

### 2. `794`/`454` are typed into the doc (R11)

`EMP.md:12` "`rebel_emp_01` is a 794-member container with 454 objects" comes from a literal at
`Tools/scripts/jc3emp.py:262`, while §8 of the same doc prints the same numbers from
`emp['members']`/`emp['objects']` (`jc3emp.py:476`). Two renderings of one fact, one derived and
one typed. Values are correct today (json: 794 / 454 for both builds), but the typed copy is the
one a reader meets first.

### 3. True claims that no artifact records, so `--check` cannot protect them

I verified each of these against the raw decode (see Spot-checks), and every one is correct -
but none is stored in `EMP.json`, so nothing would catch them going stale:

| claim | where | what backs it |
|---|---|---|
| "`trigger.use_item` is a 2x-scaled box" | `EMP.md:85` (`jc3emp.py:342`) | the trigger's `world` matrix is `2,0,0,0, 0,2,0,0, 0,0,2,0, 0,1.350708,2.395996,1`; `EMP.json` stores only `xyz`, so the 2x is not in the machine file |
| "**No EMP sound**: the container's attached effects are the ordinary vehicle set (engine, horn, gear change, damage fires, exhaust) ... there is no `SAttachedEffect` naming emp" | `EMP.md:112-115` (`jc3emp.py:364-368`) | 25 `SAttachedEffect` objects on both builds, names `engine_running_sound`, `horn`, `GearChange`, `damage_fire_left/right`, `exhaust`, ... none with `emp` - the negative is right, and `build()` never enumerates truck `SAttachedEffect`s (`effects` is collected for weapons only, `jc3emp.py:206`) |
| "Both use the stock `fow_weapon` tune ... the tune carries damage, range, recoil and magazine" | `EMP.md:170-173` (`jc3emp.py:439-440`) | each `.wtunec` decodes to 146 rows under `fow_weapon[0].tuning.base_tuning.*`, including `recoil.recoil_yaw[0..1]`, `recoil_pitch[0..1]`, `recoil_first_shot_multiplier`; `EMP.json` keeps only `damage`, `max_range`, `magazine_size`, `fire_rate`, `velocity`, so "recoil" is in no file the reviewer or `--check` can see |

For a card whose whole question is "can another vehicle fire this", the `SAttachedEffect` negative
and the trigger scale are load-bearing, so they belong in the json and in `invariants()`.

### 4. Mission context asserted rather than marked as inference (R4)

* `EMP.md:135-136` (`jc3emp.py:404-406`): "which is the mission prop (`mm250` is the escort
  mission's EMP truck). **The blast in that mission is the script's.**"
* `EMP.md:7-8` states the same split a second time.

Nothing in the files read here names a mission, an escort, or a script. The data fact is that
`mm250` carries no `CForcePulse` at all (json: `pulses` for mm250 excludes `EMP`, tune absent) -
so "the blast comes from elsewhere" is a fair inference, but "the script's", and the whole
mission framing, is outside knowledge presented as fact. The card's own rules want UNKNOWN with a
reason for anything the files do not give.

### 5. Copy list includes an asset from the build that cannot fire

`EMP.md:188` (§7 copy list): `effects/props/emp_active.effc`. That effect is embedded only in
`mm250` (`EMP.md:106`, json `mm.files`), the build that has **no pulse and no tune** - §5 says so
explicitly ("the mm250 build drops the pulse and its tune and adds the charging prop"). A copy
list for a working device therefore mixes two builds: everything else in the list comes from
`emp_01`. Either `emp_active.effc` should be dropped or labelled "only if you also want the
mission build's charging prop".

### 6. Smaller assertion gaps

* `EMP.md:222-224` (Limits): "the 88 vehicle weapon components in `WEAPON_WIRING`" - json
  `fleet.components` is 88, but `invariants()` asserts only `fleet.cemp == 0`, so the 88 would go
  stale silently.
* `EMP.md:28-30`: "100/25/1/1 for players and AI" - the raw tune does have
  `AIDamageRadiusPercentageMax`/`Min` = 1.0, but `invariants()` checks only `AIDamage` and
  `AIDamageRadius` for AI (`jc3emp.py:519-521`).
* `EMP.md:59`: "only 5 of them differ" is derived (`diff_keys`) and correct, but the table mixes
  two kinds of difference - three flags, one material table ref, and one EMP-only ref whose plain
  side is `-`. The MODLOG states it more precisely ("three flags ... plus the `emp_flatbed_table`",
  `MODLOG.md:9898-9900`) than the doc does.

## Spot-checks

| # | value in the doc | verified against | result |
|---|---|---|---|
| 1 | `truck_emp.ftunec` is "8 numbers and nothing else", 100/25/1/1 player+AI (`EMP.md:35-52`) | raw decode of the embedded `.ftunec`: exactly 8 rows - `PlayerDamage 100`, `PlayerDamageRadius 25.0`, `...PercentageMax 1.0`, `...Min 1.0`, `AIDamage 100`, `AIDamageRadius 25.0`, `...PercentageMax 1.0`, `...Min 1.0` | match |
| 2 | both builds are 794-member containers, 454 objects, 78 parts (`EMP.md:14`, `:124-127`) | raw container listing = 794 members for `emp_01`; `EMP.json` trucks[].members/objects/parts_total = (794, 454, 78) and (794, 454, 78) | match |
| 3 | EMP pulse at (0, 2.0356, 0.6992) on `truck_emp.ftune`; plain blast 500 in 5 m (`EMP.md:21-25`, `:41-48`) | `EMP.json` `trucks[0].pulses` and `tunes["car_explosion_medium.ftunec"]` | match |
| 4 | core is part 46, `Rotor`, 6 blades, axis (0,0,1), `rpm_multiplier` 1 | `EMP.json` `trucks[0].emp_parts` + `rotor[0]` | match |
| 5 | trigger at (0, 1.3507, 2.396), state `S_STUNT_USE_ITEM_VEHICLE`, prompt `ui_activate_emp` | `EMP.json` `trucks[0].use_item` | match |
| 6 | "only 5 of them differ" | `EMP.json` pulse props vs plain props diff = `id:06A05F33`, `id:4912FC04`, `id:AE6F7EFF`, `id:CF4F7880`, `id:D3DDD766` | match |
| 7 | 9 oldtruck variants, 3 device parts in every module, `CPartProp`s + pulse on 2 (`EMP.md:124-152`) | `EMP.json` `variants[]` (9 rows, all `emp_parts` length 3, 2 with props/pulse) | match |
| 8 | `w702` id 702/type 6, `FirePosition` (0, 0.13, -0.69); `w503` id 503/type 2, `CTurretWeaponComponent`; damage/range 500/50 m and 500/750 m | `EMP.json` `weapons[]` (`component`, `points`, `components`, `tune.values`) | match |
| 9 | fleet `CEMPWeapon` 0 among 88 vehicle weapon components | `EMP.json` `fleet` {cemp: 0, components: 88} | match |
| 10 | "2x-scaled box", "no `SAttachedEffect` naming emp", `fow_weapon` tune with recoil | raw decode: trigger world diag (2,2,2); 25 `SAttachedEffect` names, none `emp`; 146 `fow_weapon[0].tuning.*` rows incl. recoil | match (but not recorded in `EMP.json`, Issue 3) |

## What holds up

* The card's real question is answered with a distinction that the data supports: the device is
  entity objects (parts, `CPartProp`, `CForcePulse`, tune, material table, effect, use-item
  trigger) and the fleet census proves no vehicle carries `CEMPWeapon` - so "copyable as objects,
  not as a weapon slot" is the honest reading, and the Limits section says plainly which parts
  cannot be decided from data (duration, disable set, flag meaning, engine acceptance of
  `CEMPWeapon` in a vehicle slot, the missing trigger->pulse pointer).
* R5 is handled well: `entry.use_item` / `trigger.use_item` are described as an action and a
  prompt (`S_STUNT_USE_ITEM_VEHICLE`, `ui_activate_emp`), and the doc is explicit that the files
  prove the action and its label, not that the pulse fires.
* Empty `tune.emp_keys`, the dangling `5FED74E7=FFFF7F53`, and the mm250 build's disabled
  emitter (`enabled` 0) are surfaced rather than smoothed over - the negatives are the card's
  substance, and they are in the json and asserted.
* Copy-list rows are derived from `emp_parts`, `files`, pulse refs, the pulse and the trigger,
  so the list is not hand-invented (models/textures paths are the only typed part).

## Limits of this review

* Read-only, so I did not re-run a tamper test. `MODLOG.md:9939-9941` records
  `PlayerDamage` 100 -> 101 producing `FAIL: EMP.json stale` and a rebuild returning PASS, which
  is consistent with `cmd_check()` as I read it (`jc3emp.py:596-620`).
* I took `WEAPON_WIRING.jsonl` as given (88 components, 0 `CEMPWeapon`) instead of re-deriving it;
  that file is G2-11's, not this card's.
* `CForcePulse` / `CEMPWeapon` semantics in code (what the three flags do, whether the class
  fires the pulse) are outside any file here and are correctly left as UNKNOWN by the card.

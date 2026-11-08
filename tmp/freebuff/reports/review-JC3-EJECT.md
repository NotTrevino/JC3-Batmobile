# Review of `Research/JC3Grab/EJECT.md` (G2-20): does JC3 have an eject?

**VERDICT: PARTLY CONTRADICTED.**

The reviewed report's **data conclusion survives and re-derives exactly**: no exit in any shipped
interaction graph carries a launch/velocity member, and no vehicle module carries a driver impulse.
But its **headline is wrong**: JC3's engine carries an eject action
(`ACT_EJECT_FROM_VEHICLE`, `ACT_EJECT_FROM_VEHICLE_MG`), two eject states
(`S_EJECT_FROM_VEHICLE_ALIVE` / `S_EJECT_FROM_VEHICLE_DEAD`), a `VehicleBailExplosion` heat-tuning
name, a vehicle member `is_rico_bail_vulnerable_timer_active`, a Rico animation clip
`PPparachute_vehicle_eject`, four `bark_rico_parachute_ejecting_*` voice lines and a
`cb.bail.out.announce` challenge event. What is missing is not the concept but the **data-side
trigger**: none of the 165 state machines, 344 interaction graphs, 600 scripts or 61 animation sets
references any of those names. So "JC3 has no eject" must become **"no vehicle graph authors an
eject"**.

A second, smaller correction: the report's 9-key exit census is **incomplete**. The donor `.epe`
carries **17 further hash-named members** on every exit that `detail/*.ee.json` drops. They are all
`int` / `vec_events` / `mat` typed (0 float or vector members), so the no-launch finding holds — but
it holds **by type**, not by the key count the report gives.

Third: the reviewed script's own `--check` **fails** on this install (stale raw-data path in the
prose only; every number and the JSON digest match).

---

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3eject2.py` | the review script, `--write` / `--check`, digest `53d406793d11f6a0` |
| `Research/JC3Grab/EJECT_REVIEW.md` | 191-line generated review |
| `Research/JC3Grab/EJECT_REVIEW.json` | every number above, re-derivable |
| `tmp/freebuff/reports/review-JC3-EJECT.md` | this report |

No other task's file was edited. Scratch went to `tmp/freebuff/scratch/` and
`tmp/freebuff/scratch/eject_review/`.

---

## Commands and outputs

### 1. The reviewed report's own `--check` (as shipped)

```
$ cd E:/Modding/JC3-Batmobile && uv run --with lxml python Tools/scripts/jc3eject.py --check
FAIL EJECT.md stale: --- disk | +++ derived | @@ -5 +5 @@ | -232 vehicle `.epe` graphs in `E:/Modding/_JC3grab\detail`. | +232 vehicle `.epe` graphs in `E:/Modding/_gamedata/JC3grab\detail`. | @@ -323,2 +323,2 @@ | -`E:/Modding/_JC3grab\detail/*.ee.json` �232, | -`E:/Modding/_JC3grab\entities/*.ee.json` �232 (module rows), | +`E:/Modding/_gamedata/JC3grab\detail/*.ee.json` �232, | +`E:/Modding/_gamedata/JC3grab\entities/*.ee.json` �232 (module rows),
1 problem(s)
EXIT=1
```

The old raw path no longer exists:

```
$ ls -d /e/Modding/_JC3grab /e/Modding/_gamedata/JC3grab
ls: cannot access '/e/Modding/_JC3grab': No such file or directory
/e/Modding/_gamedata/JC3grab
$ ls /e/Modding/_JC3grab/detail | wc -l
0
$ ls /e/Modding/_gamedata/JC3grab/detail | wc -l
232
$ JC3_RAW=E:/Modding/_JC3grab uv run --with lxml python Tools/scripts/jc3eject.py --check
FileNotFoundError: [WinError 3] The system cannot find the path specified: 'E:/Modding/_JC3grab\\detail'
EXIT=1
```

Path-agnostic reproduction of the numbers (the script's own `build()` vs the on-disk JSON):

```
orig_check: derived_digest=8dca980204969198  disk_digest=8dca980204969198
            json_equal=True  md_equal=False  md_changed_lines=6 (all path strings)
```

That is the whole of the "failure": 6 path lines, 0 numeric lines, digest identical.

### 2. Fleet interaction graphs (232 roster + the 12 the roster leaves out)

```
From the 232 detail/*.ee.json graphs: 4832 exits, 61 distinct names, 9 member keys,
  no key outside the 9, 0 velocity/impulse/launch/force/speed members, state absent on 23.
Graph vocabulary: 104 classes; Veloc/Impulse/Launch/Eject/Force: CForcePulse,
  CInteractionGraphParentVelocityCondition.
344 .epe files ship; 234 contain CInteractionGraphExit; 12 are not roster vehicles.
Off-roster graphs decoded with Gibbed.JustCause3.ConvertProperty.exe: 57 exits,
  0 launch-capable members, named keys outside the known set: none.
```

(The earlier regex-only probe printed 7 exits for those 12 graphs; the regex was truncating nested
`<object>` bodies. The ElementTree parse used by the final script reads 57 — that is the number in
`EJECT_REVIEW.json`, and all 57 are listed there.)

Census at file level:

```
CInteractionGraphExit appears in 234 of 344 .epe files.
CInteractionGraph* classes across all 344 .epe + 963 .ee: 27, none with Eject/Launch/Catapult/Impulse.
```

### 3. The exe's strings (never read by the reviewed report)

```
$ JustCause3.exe  bytes 51,083,264
ACT_EJECT_FROM_VEHICLE                   2 @ 0x23d4528
ACT_EJECT_FROM_VEHICLE_MG                1 @ 0x23d4540
S_EJECT_FROM_VEHICLE_ALIVE               1 @ 0x23d25b8
S_EJECT_FROM_VEHICLE_DEAD                1 @ 0x23d2598
VehicleBailExplosion                     1 @ 0x241f113
is_rico_bail_vulnerable_timer_active     1 @ 0x24e9888
ACT_PANIC_EXIT_VEHICLE                   1 @ 0x23d4390   (control, expected unused)
ACT_EXIT_VEHICLE                         7 @ 0x23d4230   (control, known used)
```

Neighbouring names in the same printable runs (why these are an action/state table, not noise):

```
ACT_EJECT_FROM_VEHICLE:      ... ACT_FIRE | ACT_RELOAD | ACT_KEEP_HANGING |
                             ACT_EJECT_FROM_VEHICLE | ACT_EJECT_FROM_VEHICLE_MG |
                             ACT_IDLED_FOR_A_LONG_LONG_TIME | ACT_ABORT_CUSTOM_ANIMATION ...
S_EJECT_FROM_VEHICLE_ALIVE:  ... S_LIFT_MC_START | S_LIFT_MC_FINISH |
                             S_EJECT_FROM_VEHICLE_DEAD | S_EJECT_FROM_VEHICLE_ALIVE |
                             S_SIDE_JUMP_PART1 | S_SIDE_JUMP_PART2 ...
VehicleBailExplosion:        ... HeatTriggerDistance | ChaosTriggerDistance |
                             VehicleBailExplosion | [HeatLevelTuningBase] ...
is_rico_bail_vulnerable_timer_active: ... height_above_ground_or_sea_level |
                             is_rico_bail_vulnerable_timer_active | steering_signal_horn ...
```

Because "in the exe" is weak on its own, the review ran controls:

```
$ grep -aE "^(ACT_|S_|PACT_).*(LAUNCH|CATAPULT|BAIL|IMPULSE)" jc3exe_strings.txt   -> (none)
$ grep -ai launch jc3exe_strings.txt -> CO_E_LAUNCH_PERMSSION_DENIED, weapon,grenadelauncher
```

i.e. there is **no** `ACT_LAUNCH*` / `ACT_CATAPULT*` / `S_*BAIL*` action or state; the eject names
are the only eject-ish engine vocabulary, and no launch action exists at all.

### 4. Who references those names (the reachability test)

Scope: 165 `.afsmb` + 344 `.epe` + 300 `.gsc` + 300 `.gdc` + 61 `.asb` = **1170 files**, plaintext plus
(Gibbed Jenkins lookup3 over the upper-case name) for `.afsmb`.

```
ACT_EJECT_FROM_VEHICLE                hash 12ED2105   .afsmb 0   distinct files 0
ACT_EJECT_FROM_VEHICLE_MG             hash 011534FA   .afsmb 0   distinct files 0
S_EJECT_FROM_VEHICLE_ALIVE            hash 45EA7222   .afsmb 0   distinct files 0
S_EJECT_FROM_VEHICLE_DEAD             hash 0C815149   .afsmb 0   distinct files 0
VehicleBailExplosion                  hash 711E1C78   .afsmb 0   distinct files 0
is_rico_bail_vulnerable_timer_active  hash 4F59AA62   .afsmb 0   distinct files 0
ACT_EXIT_VEHICLE (control)            hash 7B3C34AB   .afsmb 3   distinct files 3
ACT_STUNT_VEHICLE_EXIT (control)      hash FEAB98DF   .afsmb 1   distinct files 1
S_EXIT_VEHICLE_PARA (control)         hash 2F8BACC7   .afsmb 1   distinct files 223
ACT_PANIC_EXIT_VEHICLE (control)      hash 1102CD69   .afsmb 0   distinct files 0
```

Controls: `ACT_EXIT_VEHICLE` is present both plaintext and as its uppercase Jenkins hash
(`7B3C34AB`) in `rico_base.afsmb`, `civ_male_base.afsmb`, `soldier_gen_base.afsmb`, which proves the
hash scheme; `ACT_PANIC_EXIT_VEHICLE` is in the exe and in no data file, which proves the exe table is
a **superset** and that absence from data is meaningful.

### 5. Animation, audio, script evidence

```
rico_base.asb:
  PPparachute_vehicle_eject                      1 @ 0x2d272
  rico_vehi_car_low_driver_to_parachute.ban      1 @ 0xb079e
  PPparachute* family: PPparachute_flip, PPparachute_from_reel_long,
    PPparachute_from_wingsuit, PPparachute_opened, PPparachute_vehicle_eject
rico_base.afsmb:
  S_EXIT_VEHICLE_PARA present; any EJECT name: []
index:
  bark_rico_parachute_ejecting_01..04  x (.ban + .wavc)  = 8 paths
  mission_dlc2_mm110_dial_obj13_eject_*                  = 50 files / 10 languages
scripts:
  crash_bomb_main.gdc  @ 0x490  cb.bail.out.announce
  mm340_main.gdc       @ 0x4e70 mm340_play_sheldon_bail_dialog
```

Broad binary sweep (2207 files: `.afsmb`, `.asb`, `.epe`, `.ee`, `.gsc`, `.gdc`, `.pfxc`, `.effc`,
3,979,054,821 bytes, 186 s) for `eject|catapult|bail`: the only vehicle-graph hit is
`ShellEjection` / `ejection_port` in **weapon** `.epe` files (shell-casing components — unrelated),
the only animation hit is `PPparachute_vehicle_eject`, and the only `.ee` "hits" are float bytes
that happen to spell `baIl` inside printable runs (e.g. the donor's own `.ee`) — discarded as noise
by the printable-run parse in the final script.

### 6. The 9-key census is incomplete

`detail/*.ee.json` stores only **named** values. `Research/Epe/serpente_civilian.xml` (the reviewed
report's own input) keeps the hashes too:

```
CInteractionGraphExit, 26 donor exits:
  named: _class, _object_id, disable_event, enable_event, enabled, interaction, modifier,
         name, name_hash, state, tags            (11)
  hash-named: 17 per exit
  types across 26 exits: int x312, mat x26, vec_events x104
  float/vector members: 0
  id:D04059E6 = jenkins hash of the object's class name on 43/43 classes in the file
                (1505987802 == hash("CInteractionGraphExit"))
  dictionary attack (15,150 snake_case exe tokens, jenkins + FNV, lower/upper) on the 17 ids: 0 hits
```

Off-roster exits show the same shape (57 exits: int x684, mat x57, vec_events x228, float/vector 0).

So the report's "exactly 9 keys / 0 keys outside them" is **wrong as written**, but its conclusion
survives because an impulse must be a float or a vector and no exit member is either.

### 7. Module sweep, checked as written and then widened

```
reviewed regex (eject|launch|catapult|impulse|parachute|wingsuit):        1  TrainGlobal.crashing_impulse x12
+ bail (the term the reviewed regex omitted):                             1  TrainGlobal.crashing_impulse x12
+ bail and veloc:                                                        33 (RigidBody.max_linear_velocity,
   tyre slip velocities, Buoyancy.up_velocity_cap, drift rotation, ...)
```

The 33 wide-lens hits are vehicle-body physics members; none acts on a seated driver and none is a
launch. Adding `bail` changes nothing.

### 8. Final checks

```
$ uv run --with lxml python Tools/scripts/jc3eject2.py --write
wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\EJECT_REVIEW.md (191 lines) + EJECT_REVIEW.json
OK: PARTLY CONTRADICTED | roster 4832 exits / 0 launch | off-roster 57 exits / 0 launch |
    engine eject names 6/6, data refs 0 | control ACT_EXIT_VEHICLE 3 | asb clip 1 | barks 8 |
    orig json_equal True md_equal False

$ uv run --with lxml python Tools/scripts/jc3eject2.py --check
PASS: PARTLY CONTRADICTED | ... (same summary)
EXIT=0
```

---

## What contradicts "no eject"

1. **Exe action/state names** — `ACT_EJECT_FROM_VEHICLE`, `ACT_EJECT_FROM_VEHICLE_MG`,
   `S_EJECT_FROM_VEHICLE_ALIVE`, `S_EJECT_FROM_VEHICLE_DEAD` at `0x23d4528`, `0x23d4540`,
   `0x23d25b8`, `0x23d2598`, inside the contiguous `ACT_*` / `S_*` tables.
2. **Bail in vehicle/heat systems** — `VehicleBailExplosion` in the heat-tuning name block
   (`0x241f113`), `is_rico_bail_vulnerable_timer_active` in the vehicle-state member block
   (`0x24e9888`).
3. **Animation** — `PPparachute_vehicle_eject` in `rico_base.asb` (`0x2d272`), plus a car
   driver-to-parachute clip `rico_vehi_car_low_driver_to_parachute.ban` (`0xb079e`).
4. **Dialogue** — 8 index paths for `bark_rico_parachute_ejecting_01..04`; 50 DLC eject dialogue files.
5. **Script** — `cb.bail.out.announce` in `crash_bomb_main.gdc`, `mm340_play_sheldon_bail_dialog`
   in `mm340_main.gdc`.

## What still supports the report

1. 0 launch-named members in **4,839** exits (4,832 roster + 57 off-roster).
2. 17 hash-named members per exit, but **0 float/vector** typed members — no place to store an impulse.
3. 0 references to any eject/bail name in 1,170 data files, with two working controls.
4. 0 `ACT_LAUNCH*` / `ACT_CATAPULT*` actions anywhere in the exe.
5. Module sweep unchanged when `bail` is added.

---

## UNKNOWNs

1. **Whether the engine eject is reachable at all.** Names exist; no data names them. The trigger is
   native code or a code default not stored in any `.epe` / `.afsmb` / script. Closing this needs a
   Q-1 probe (input or debug command); read-only review cannot.
2. **Whether the eject / `PPparachute_vehicle_eject` applies a vertical impulse.** Clip bodies are
   not decoded; Q1-EJ-A remains the only test.
3. **What `ACT_EJECT_FROM_VEHICLE_MG` selects.** The two mount graphs exit through
   `S_EXIT_MOUNTED_WEAPON` and never name it.
4. **Whether the four `parachute_ejecting` barks fire.** No script or decoded bark table names them
   as a triggered event.
5. **The 17 hash-named exit members' names.** Types are known (no float/vector), one is the
   class-hash field; a 15,150-token dictionary found no other name. Needs the epe property-name list,
   which is not in the grab.

## Recommended edits to `EJECT.md` (not applied — another task's file)

* Replace "**JC3 has no eject**" with "**no vehicle graph authors an eject**" and add the engine
  evidence above.
* Replace "members from a set of 9 keys / 0 keys outside the set" with "9 named keys in the detail
  JSON; the donor `.epe` also carries 17 hash-named members, none float/vector".
* Regenerate the report so its own `--check` passes (the raw path moved).

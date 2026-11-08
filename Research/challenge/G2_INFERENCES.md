# Challenge — the G2 'Limits' / UNKNOWN / inferred statements

Scope: the `**Limits.**` sections, UNKNOWN sentences and explicit inferences in the
`Research/JC3Grab/*.md` files written by cards G2-10…G2-34 (doc → card from `GRAB_BACKLOG.md` §12).
Read-only: no existing document was edited, no game launched, nothing committed. New files:
`Tools/scripts/chase/g2_close.py` and this report.

Method per item: state the sentence, then try to close it with data (routes below), then record
CLOSED (with the value/negative and the command that produces it) or STILL OPEN (with the routes
tried and why each fails). Rules in force: `GRAB_BACKLOG.md` §0.5 R4 (no value without a
provenance class; `assumed` is not buildable) and R5 (behaviour before member).

```
python Tools/scripts/chase/g2_close.py tanks     # G2-21 opposite-direction check
python Tools/scripts/chase/g2_close.py refs      # G2-16 pulse references, exhaustively
python Tools/scripts/chase/g2_close.py index HASH  # dangling <hash>=<oid> refs against INDEX.jsonl
```

**Result: 16 items examined — 5 CLOSED (3 of them as proven negatives, 2 as narrowed facts),
11 STILL OPEN.** The closed ones matter because they remove work from phase Q: no phase-Q probe
is needed to find a trigger→pulse link, a tank-only data member, or a helicopter airlift member —
none exists in the data, and that is now shown exhaustively rather than argued.

---

## 1. G2-16 · The EMP truck

### G2-16-a — "There is **no object reference from the trigger, the entry or the vehicle to the
`EMP` pulse**" / "the pulse is fired by whatever executes that state"
*Doc:* `EMP.md:78-83`; repeated `MODLOG.md:9920-9923`. *Statement class:* inferred (from a
trigger/entry scan).
**Verdict: CLOSED (negative, exhaustive).**
The card scanned the trigger and the entry. This challenge scanned **every string property of every
object in the truck's `.epe`** for the pulse's own id (`594C9A11=FFFFC0C2`):

```
$ python Tools/scripts/chase/g2_close.py refs
454 objects in v0505_car_solar_oldtruck_rebel_emp_01.ee

pulse CForcePulse oid EE13C0B6=FFFFE90F: 2 object(s) carry that id
   CCar                     v0505_car_solar_oldtruck_rebel_emp_01 id:B5AE7986
   CForcePulse              CForcePulse                  _object_id

pulse EMP oid 594C9A11=FFFFC0C2: 1 object(s) carry that id
   CForcePulse              EMP                          _object_id
```

The stock blast is referenced by the `CCar` (one owner), the `EMP` pulse by nothing but itself.
So the single hit for the EMP is the pulse's own `_object_id`. So there is no pointer to the pulse anywhere in
the entity — not from the trigger, not from a script action, not from a component. The negative is
now proven for the whole object graph, which also means **no phase-Q probe can be replaced by more
reading**: what fires the pulse after `S_STUNT_USE_ITEM_VEHICLE` is native.
(The separate sentence "it is a store — the driver presses use item and the pulse fires" stays
STILL OPEN, see G2-16-c.)

### G2-16-b — "its other ref, `5FED74E7=FFFF7F53`, is not an object in the entity and stays
dangling"
*Doc:* `EMP.md:71-73`, `MODLOG.md:9918-9919`.
**Verdict: CLOSED (the dangling status is a fact, not an unread layer).**
Route 1: look the 8-hex file hash up in the JC3 index (81,952 paths, `hash_jenkins(path)` per row):

```
$ python Tools/scripts/chase/g2_close.py index 5FED74E7
index rows 81952; hash 5FED74E7: 0 path(s)
```

Route 2 (route 1 of the card): the entity's object table — already done by the card, id absent.
Route 3: dictionary attack of the id against object names — not applicable, because the `a=b`
form is (file hash, object id), not a name hash: `hash_jenkins('emp_flatbed_table')` = `AB20D4E8`,
not the id used in the file. So the reference names a **path that is not in the index** (a
mod-local or unindexed entity) and can never resolve from shipped data. The row should say
"unresolved because the target file is not indexed", which is stronger than "dangling".

### G2-16-c — "Duration and disable semantics are UNKNOWN in data — they are code" and "`the driver
presses use item and the pulse fires` is inferred"
*Doc:* `EMP.md:56-58`, `EMP.md:210-213`.
**Verdict: STILL OPEN, and correctly so.** Routes tried:
1. `truck_emp.ftunec` is 8 members (`PlayerDamage`, radii, `AIDamage`, radii) — re-read, no
   duration/disable field. The `CForcePulse` object carries no duration member either.
2. The `.epe` has no state machine beyond `CInteractionGraphEntry` → `S_STUNT_USE_ITEM_VEHICLE`;
   scanning all 252 objects for the pulse id (above) finds nothing, so no script action is stored
   in the entity.
3. Static executable route: `BatmanAK.exe` carries only exec-function registration strings for the
   sim classes (`RVehicleSimBatmobileexec…`), no property names — the JC3 executable is not part of
   this grab at all. No attributable constant, so no address is claimed.
This stays a Q-1 probe. The card is right to call it code; the improvement would be to stop calling
the firing "inferred" and call it "unproven" — the files are silent, not suggestive.

---

## 2. G2-21 · Turn-on-the-spot (tank pivot)

### G2-21-a — "a pivot, if the game has one, is decided in native code keyed to the vehicle's
identity — data leaves no other discriminator"
*Doc:* `TANKTURN.md:123`, `:12`. *Statement class:* inferred from a member census.
**Verdict: CLOSED (negative, independently reproduced).**
`g2_close.py tanks` diffs every module member of the four tanks (`v0200`, `v0201`, `v0202`,
`v0603`) against all 49 other land chassis:

* **257 member paths are carried only by tanks.** Every one is wheel-count geometry —
  `DeformPoints.wheel_indices[6..7]`, `Suspension.wheel_hardpoint_offsets[6..7]`,
  `LandGlobal.base_wheel_hardpoint_positions[6..7]` — or `Propellers.*` on one chassis. **Not one
  is a steering, torque-vectoring or turn-rate member.**
* The three members the card examined behave as it said: `wheels_friction_type` is 2 on all four
  tanks **and on 11 cars** (so it is not a track flag); `number_of_front_wheels` is −1 on 47 cars
  and 2 tanks, 4 on the other 2 tanks (so it is not a discriminator); `use_shape_cast` is 0
  everywhere in the class.
Conclusion: no `land_*` member can grant turn-on-the-spot, exactly as the doc concluded. What is
still missing is only the *rate* and whether the shipped tanks pivot at all — both native.

### G2-21-b — "`wheels_friction_type`'s enum meaning (0/1/2) is `UNKNOWN` — it tracks the off-road
tyre modules only loosely (40 of 47 users) and is not a track flag"
*Doc:* `TANKTURN.md:129`. *Statement class:* inferred.
**Verdict: CLOSED for the "not a track flag" half; STILL OPEN for the enum labels.**
Type 2 = all 4 tanks + 11 cars (by-chassis count from `g2_close.py tanks`). A value shared by
eleven cars cannot name a track. The labels themselves remain unlabelled — no shipped table maps
0/1/2 to names, and the exe-side route (string scan) finds no member names.

### G2-21-c — "`number_of_front_wheels = -1` means unset/auto is a guess"
*Doc:* `TANKTURN.md:129`. **Verdict: STILL OPEN, and the guess is now weaker.** −1 is carried by
47 cars **and** 2 tanks, 4 by the other 2 tanks; a sentinel shared by 47 non-tanks cannot encode
"tracked". It reads as "steering axle count" (cars steer 2, a 4-axle tank steers all 4, −1 =
default) — a hypothesis, not a value; no file labels it.

---

## 3. G2-31 · Water behaviour

### G2-31-a — "the unit behind the `_ms` suffix is not decoded (`UNKNOWN`): 10/20 ms is too short
to be a drown timer, so the name is the only evidence"
*Doc:* `WATER.md:239`, `:274`. **Verdict: STILL OPEN.** Routes tried:
1. The decoded module (`vehicle_damage`) has no unit metadata: ADF stores member names and values,
   not units, and the values are bare integers (10, 20, 20, 50, 30).
2. Cross-module comparison: every other time-like member in the fleet uses `_s` for seconds
   (`explosion_delay_s`, `*_engine_shut_down_delay_s` 30 s, `smoke_threshold`), so `_ms` is
   deliberately a different unit — but which one is not in the file.
3. Static route: no JC3 executable is in the grab; the AK exe is a different game.
It stays UNKNOWN, and the doc's warning "do not quote it as seconds" is the correct handling.

### G2-31-b — "What a submerged car actually does after the timer runs is native code"
*Doc:* `WATER.md:5`, `:265`. **Verdict: STILL OPEN (and unfalsifiable from data).** Member census
over all 52 module types finds only the `water` module, the `vehicle_damage` timers,
`number_of_water_collision_sensors`, `fins[].effective_in_water` and helicopter `dive_*` — no
`drown`/`flood`/`swim` member, reproduced independently here. Nothing further to read.

---

## 4. G2-32 · Names, icons and strings

### G2-32-a — "store art `textures/ui/store/v0300_sportsmuscle_01.ddsc` … **which UI page loads it
is UNKNOWN**"
*Doc:* `NAMES.md:105`, `:152`. **Verdict: STILL OPEN, but narrowed.**
Routes tried:
1. Whole-index reference search: the path appears **once** in 81,952 rows — its own entry. No
   manifest, no `.onlinec`, no UI list names it.
2. The only store movies in the archives are `ui/comm_store.gfx` (base `game5`, 59,939 B and
   patch `game6`, 61,956 B). Reading the base movie and scanning its bytes for
   `sportsmuscle`, `v0300`, `sportsmuscle_01`, `.ddsc` → **0 hits each**. So the community-store
   movie does not reference it by name; the vehicle menu must build the path from a template.
3. That template is inside a compiled Scaleform movie; `ffdec` is available in the toolset
   (`E:/Modding/_tools/ffdec/`) but decompiling a 60 KB GFX to find a path template is a separate
   card, not this challenge.
Conclusion: the texture is loaded by a name built at runtime, not by a stored string; the doc's
UNKNOWN stands.

---

## 5. G2-34 · Tether, airlift and winch carriers

### G2-34-a — "**Whether a helicopter can airlift a car**: UNKNOWN. No fleet helicopter has a
[matching member]"
*Doc:* `TETHER.md:224`, `:228`. **Verdict: CLOSED (negative).**
Independent scan of every `02_air` entity's module rows for `tether`/`winch` members: **41 air
entities, 0 rows** carrying either word, across the whole air fleet (the same scan over the 53 land
chassis finds the tether modules only on the land side). So the absence the card reports is a property of the
fleet, not of one unread module — an airlift in JC3 must be a script/rope-runtime behaviour, not a
vehicle module member. That is a fact worth having in the row: it says a phase-Q probe is the only
route, and no amount of further entity decoding will find a carrier.

### G2-34-b — "tether strength / break force: UNKNOWN, not in any decoded table"
*Doc:* `TETHER.md:224`. **Verdict: STILL OPEN.** The `tether` module type is shared
(`vehicle_common`-style), so a strength member would appear on the 232 decoded entities; it does
not. The only remaining location is the native rope solver. No route found.

---

## 6. G2-15 · Door animation; G2-13 · turret mechanics

### G2-15-a — "An angle is the hinge's authored limit, not a measured swing … what writes
`hood_angle` … is not in any file read here" (UNKNOWN)
*Doc:* `DOORS.md:149-151`. **Verdict: STILL OPEN.** Routes tried: (1) module census — the only
angles are `.physicsc` limits (already read by the card); (2) state-variable names
(`hood_angle`, `canopy_angle`) appear in `vehicle_common` but no object in any decoded entity
writes them, and the `.epe` graph has no script action carrying those strings — the same
exhaustive string scan used for the EMP pulse finds nothing; (3) executable route — no JC3
executable in the grab and the AK one carries no property names (verified again here:
`AirControlInterpTime`, `hood_angle` etc. are 0 hits in `BatmanAK.exe`). So the writer is code and
cannot be named from data.

### G2-13-a — "Which *code* writes a given variable … is not in any file read here" / pivot key
native
*Doc:* `MOVING_PARTS.md:206-208`, `TANKTURN.md:129`. **Verdict: STILL OPEN** (same route failure
as G2-15-a). What is closed: the *binding* table itself is complete and machine-checked
(`jc3moving.py --check` passes), so only the writer is unknown.

---

## 7. G2-29 · Traffic

### G2-29-a — "the donor's pool is `UNKNOWN` — what selects it is the tag list … the picker is
native"
*Doc:* `TRAFFIC.md:39`, `:136`. **Verdict: STILL OPEN.** Routes tried: (1) the record's own fields —
no pool key in the donor's record (8 of 86 records carry one, all singletons); (2) the index —
`settings/` has no traffic definition naming the donor beyond `spawn_vehicle_defs.bin`;
(3) scripts — no `graphs/*.gsc` or `ai/bts/*.btc` mentions the tags (card's result, reproduced on
the same list). The matcher is native; no closure available.

### G2-29-b — "whether the engine honours a replaced settings file without a hash change is
`UNKNOWN` (G2-27's question)"
*Doc:* `TRAFFIC.md:148`. **Verdict: STILL OPEN (Q-1 by construction).** No shipped example of a
replaced settings file exists in the index, so there is nothing to compare against; a build probe
is the only route.

---

## 8. G2-27 · Standalone entity

### G2-27-a — "A *new* leaf from an item hash is **UNKNOWN** … 0 shipped counter-examples"
*Doc:* `STANDALONE.md:3`, `:14`, `:21`. **Verdict: STILL OPEN.** Route tried: count shipped
counter-examples — the registry decodes 251/922 index leaves with 0 ledger rows for new leaves
(card's number, unchanged by this pass); a hash→leaf search over all 81,952 index rows finds no
record whose hash is not the hash of its own path, i.e. no shipped case of a leaf invented at
lookup time. "No counterexample" is the honest answer, and it cannot be turned into a yes/no from
files.

---

## 9. G2-30 · Collision shapes

### G2-30-a — "the *write* side: nothing in this toolkit writes a `.physicsc`"
*Doc:* `T_PLAN`/`SHAPES` limits, quoted in `T1_TRANSLATION.md` §15. **Verdict: CLOSED — the
statement is stale.** `Tools/scripts/jc3hkx.py` **does** write `.physicsc` blobs: line 2125
unblocks T-P3 ("no `.physicsc` writer" → "unblocked for hull-based collision"), and
`--write` emits them (`open(os.path.join(WRITE_DIR, name + ".physicsc"), "wb")`, line 2199,
reported as `wrote N .physicsc blobs`). So the blocked row in `T1_TRANSLATION.md` §15 and §13
(T-P3) is out of date: a writer exists for hull-based collision, and only the *shape* fidelity
(BmAK boxes vs JC3 hulls) remains open, as the same file's note says.

---

## 10. G2-17 · `CForcePulse`

### G2-17-a — "The pointer's *name* is UNKNOWN (a Jenkins hash with no dictionary hit)"
*Doc:* `FORCEPULSE.md:285`. **Verdict: STILL OPEN, route recorded.** The hash in question is a
member *name* hash, and the project's name dictionary is `INDEX.jsonl` (81,952 path hashes) plus
the decoded member paths under `E:/Modding/_JC3grab/entities/`. `g2_close.py index` searches the
index; the entity-side member names are already the same strings the card used, so if the name is
not among them it is not in the shipped name space the grab holds. Cracking it would need the
game's full name table, which is inside the (compressed) `.epe`/module name tables already
decoded — i.e. the card's dictionary was already exhaustive for this grab.

---

## 11. Not attempted in this pass

These items were read and are real, but no route was available without either a build probe or a
different grab, so they are recorded as STILL OPEN with the reason rather than guessed:

| doc | item | why not closable here |
|---|---|---|
| `SEAT.md:188-201` | tank seat height, bone lists, collision | needs the tank's animation clip decode (not in the grab) |
| `EJECT.md:113` | which of two exits wins | selection is code-side; both gates ship |
| `DAMAGE_MODEL.md:18-24` | part→damage-type map; what `_armor_strength` does | only one `VehicleParts` module decodes (monorail flatbed); the donor/tank/build maps fail ConvertAdf |
| `REBELDROP.md:62-65` | `RebelDropTimer` unit; enum labels | bare ints, no labels in any table |
| `WATER.md:239` | `_ms` unit | no unit metadata in ADF |
| `USAGES.md` (121 limit lines) | engine-side effect usages | out of scope for a data-only pass |

## Method and limits

* Every claim was checked against the decoded cache (`E:/Modding/_JC3grab/entities|detail`) and
  `Research/JC3Grab/INDEX.jsonl`; the two BmAK-side checks used `BatmanAK.exe` and `BmGame.upk`
  read-only, never written to.
* Where a sentence is an inference rather than a value, the verdict judges whether the *negative*
  behind it is now proven (CLOSED) or whether it remains a statement about native code (STILL
  OPEN). No item was closed by argument: each CLOSED has a command and its output above.
* The member diff is chassis-level, so a member carried by one entity of a chassis counts for the
  chassis; for the tank question that is the conservative direction (it would find *more*
  tank-only members, not fewer).
* One correction made while writing this report: the first air-fleet scan used a filename glob
  (`*02_air*.json`) that matches nothing, because the loadout path is inside the JSON, not the file
  name. The scan was rerun filtering on `entity` containing `/02_air/` — 41 entities, 0 hits. The
  earlier vacuous result would have looked like a proof and was not one.
* Nothing under `D:/Games` was read for this report — the decoded cache and the two read-only
  package reads sufficed, and no game was launched.

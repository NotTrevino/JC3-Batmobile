# Independent review — backlog card B-09 (private health module and damage types)

Card: `GRAB_BACKLOG.md` §8, `#### B-09 · Private health module and damage types (old DMG-2/DMG-3)
S · deps: B-04, T-14 · serves: ARM-1…6` (line 1065). §12 row: line 1339.
Outputs reviewed: `Working/Damage/bm_health.json`, `Builds/bm-009/` (`receipt.json`, `aaf` tree,
`.ee`, `.toc`), `Tools/scripts/bm_health.py`, `Tools/scripts/damage_audit.py`,
`Tools/scripts/damage_predict.py`, `Working/Translation/T10_DAMAGE.md`,
`Working/Translation/damage_switches.json`, `Working/Translation/t10_damage_edits.json`, and
MODLOG §"B-09 · private health module — done" (line 17291).

Read-only: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`, `Tools/`, `Working/`,
`Builds/` or the game was edited; this report is the only file written. No game launch, no commit,
no game data copied.

## VERDICT

**Minor issues.** The build is real and its central claims reproduce: a 3,741 B private
`batmobile_health_medium.vmodc` with `max_health` 36,000, the two wheel rows at 400, the `.epe`
`damage` hash repointed by one 4-byte write at 474, the shared module unchanged since bm-002, all
five receipt hashes matching on disk, and both Done commands green with the exact tables the journal
quotes. What is wrong is at the edges: **one count is typed and wrong** (77 vehicles share
`lave_health_medium` → the data says 81 entities / 29 vehicle folders), **one generated sentence
contradicts the script's own check** ("every part's type resolves" vs "4 without a row"), **one
attribution is wrong** (`Boat_Antenna` is the donor's part, not one of B-04's), and two statements
are narrower than they read (R7's "byte-identical" is against bm-002, whose copy is already edited;
"incoming collision damage" is a name-based reading). None of these changes a byte of the build.

## Check output (verbatim)

The card's own Done command, re-run on the current tree:

```
$ python Tools/scripts/bm_health.py --check
1. .toc record  batmobile_health_medium.vmodc: offset=23222112 size=3741 (PASS)
2. health values  max_health=36000, deform_scale=0, impact_damage_factor=0
3. wheel rows  front_wheels_damage.skew_health=400, rear_wheels_damage.skew_health=400
4. .epe damage  1928726201 (Jenkins of batmobile_health_medium.vmodc) x1, shared hash x0
5. R7 shared   lave_health_medium.vmodc sha256 AF5C33E6306DEBA7… (unchanged)
6. part types  59 parts use 19 distinct damage types; 24 PartDamageType rows in the private module; 4 without a row ['Boat_Antenna', 'Boat_Generic', 'Plane_Control_Surface', 'Train_Generic']
PASS: Builds/bm-009 re-read (9042218243A21278…, 605 .toc records, 6 edit row(s), 0 problem(s))
EXIT=0
```

The two commands the **card** actually names as Done, re-run:

```
$ python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf
max_health                           36000    500..4000        700  switch
melee_armor                           5000      0..0             0  switch
melee_armor_strength                   100      0..0             0  switch
npc_explosion_threshold               4000    500..4000        700  inside
smoke_threshold                       1050    200..1050        200  inside
vulnerable_duration_s                    5      5..5             5  inside
vulnerable_explosion_threshold         100     10..100          35  inside
weapon_deform_threshold                  0      0..0             0  inside

29 members, 6 outside the shipped range, 6 declared switches
check ok
EXIT=0

$ python Tools/scripts/damage_predict.py --root Builds/bm-009 table
build under test: Builds/bm-009 (build_bm-009, max_health 36000)
arm            channel       damage     H0    H1    H2
pistol         bullet         30.00   1200 120000 never
assault_rifle  bullet         32.00   1125 112500 never
machine_gun    bullet         28.00   1286 128572 never
shotgun        bullet        144.00    250 25000   285
rpg            explosion    1500.00     24    48    25
grenade        unknown      1012.50     36    36    36
tank_cannon    explosion    1500.00     24    48    25
heli_missile   unknown      1500.00     24    24    24
heli_mg        bullet         25.00   1440 144000 never
hits-to-kill against the root pool; H0 armour ignored / H1 percentage gate / H2 threshold+pool
EXIT=0
```

Both are identical to the journal's quoted output, line for line.

## Issues

**1 · "shared by 77 vehicles" is not the number the data gives — typed, not derived (R11).**
`Working/Damage/bm_health.json` → `private_copy.reason`, and the same string in
`Builds/bm-009/receipt.json` → `edits.private_copy.reason`: "R7: `lave_health_medium.vmodc` is
shared by **77** vehicles". It is a literal in the generator, `Tools/scripts/bm_health.py:194`.
Counting the decoded fleet (`E:/Modding/_JC3grab/entities/*.ee.json`, `VehicleDamage` module path):

```
entities sharing: 81  distinct vehicle folders: 29
```

81 entities (29 vehicles × their variants) reference that module; 77 matches neither count. Why it
matters: this sentence is the *reason* R7 exists and it is printed into both generated artefacts, so
a wrong figure propagates to every future reader — and the count is trivially derivable from the
same decode the project already keeps.

**2 · The generated spec says every part's type resolves; the same script's check prints the
opposite.**
`Working/Damage/bm_health.json` → `part_damage_types.why`: "the health module's 24 `PartDamageType`
rows are the donor's, and this build **asserts every part's type resolves to one of them**". Check
6 of the very same `--check` run prints "4 without a row". Measured from the built parts module:
59 parts, 19 distinct damage types, 24 rows in the private module, and 8 parts resolve through
`Default`:

```
i= 33 sportsmuscle_c_mirror        Boat_Antenna
i= 52 batmobile_machine_gun        Boat_Generic
i= 54 batmobile_missile_pod_l      Train_Generic
i= 55 batmobile_missile_pod_r      Train_Generic
i= 56 batmobile_aero_flap_l_f      Plane_Control_Surface
i= 57 batmobile_aero_flap_r_f      Plane_Control_Surface
i= 58 batmobile_aero_flap_l_b      Plane_Control_Surface
i= 59 batmobile_aero_flap_r_b      Plane_Control_Surface
```

Why it matters: the MODLOG's open item states the truth ("so they resolve through the module's
`Default` row"), so the *journal* is right and the *spec* is wrong — but the spec is the artefact a
later agent loads first. A `why` that says "asserts every type resolves" is exactly the sentence
that stops someone checking (R4: this is a claim the data cannot support).

**3 · The open item attributes `Boat_Antenna` to B-04's parts — it is the donor's part.**
MODLOG line 17382: "Four damage types used by **B-04's parts** (`Boat_Antenna`, `Boat_Generic`,
`Plane_Control_Surface`, `Train_Generic`) have no `PartDamageType` row". B-04's 19 parts use
`Land_Light`/`Land_Generic`/`Boat_Generic`/`Train_Generic`/`Plane_Control_Surface`; `Boat_Antenna`
belongs to `sportsmuscle_c_mirror` (index 33), one of the 40 surviving donor parts. The accurate
split is **3 types / 7 parts from B-04 + 1 type / 1 donor part**. Minor, but it puts a donor
inheritance into a B-04/T-12 action item, which is where a later session would look for it.

**4 · R7's "byte-identical" has no baseline, and the baseline is already edited.**
§12 row: "the shared `lave_health_medium.vmodc` stays byte-identical (R7, sha256 `AF5C33E6…`)";
MODLOG: "The shared `lave_health_medium.vmodc` is byte-identical (R7)." Verified true **against
bm-002** (identical bytes, same sha as the receipt). But the archived module that 81 entities
reference decodes as:

```
max_health = 700    deform_scale = 1    impact_damage_factor = 1    explosion_threshold = 700
```

while the tree's shared copy holds `2000 / 0 / 0` — earlier builds (test-085/091, `t5_applied_085.json`
lists the file, and `Research/JC3Grab/DAMAGE_MODEL.md`'s own "build" column records `2000` and
`0/0`) already changed it. So the sha in the row protects those 81 entities against *further* edits
only; it does not mean "the game's shared module is untouched". Why it matters: R7 is the rule that
stops one build from retuning 81 vehicles, and the sentence as written would let a reader conclude
the file matches the archive when it does not.

**5 · The card is missing its `In:`/`Out:`/`Stop:` lines (§0.4).**
The card body is `Do:` + `Done:` only. Consequences: the private module's path, `bm_health.json`
and the receipt appear only in §12, and the card's Done line names neither `bm_health.py --check`
nor the private module's name — the two things that make the result checkable. It is the reason the
§12 row is doing the card's job.

**6 · The card's Done criterion does not test the values it asserts.**
`damage_audit.py --build` is green because every out-of-domain value is **declared** in
`damage_switches.json`; five of the six declarations (`impact_damage_factor`, `deform_scale`,
`impact_armor`, `melee_armor`, `melee_armor_strength`) are inherited from the pre-B-09 block and
were not written by this card; two of them (`deform_scale` @152, `impact_damage_factor` @148) were
already 0 in the base tree, so "T-DM6/T-DM8: from 0 → 0, no write" is correctly recorded and the
only bytes this card touches are `max_health` (2 B) and the two wheel rows (4 B). `damage_predict` prints a table from
a model whose 7-step chain carries 7 UNKNOWNs (its own output says so). Only
`bm_health.py --check` ties built bytes to spec — and the card does not ask for it. Not a defect in
the result; a defect in what "done" was defined as.

**7 · "Incoming collision damage off" is a name-based reading presented as fact (R5 risk).**
`bm_health.json` T-DM8 `why`: "incoming collision damage off (BmAK: ramming does not scratch it)".
The chain behind it is `damage_switches.json` ("multiplied into **incoming** collision damage") →
`POSTMORTEM_DAMAGE.md` §8 → `T10_DAMAGE.md:162` ("G2-28 found no outgoing ram-damage member; the
only impact member is incoming"). That is an inference from a member name plus the *absence* of an
outgoing counterpart, not a measured behaviour. The switch file is explicit that it is a declared
deviation; the generated json's one-liner is not. Nothing in the build changes if the inference is
wrong, but the sentence should read "read as incoming (name + no outgoing member; behaviour
UNKNOWN)".

**8 · "245 members re-read" is 245 primitives, not 245 of 245 members.**
The module has 246 leaves (independent `jc3adf` read: 246 rows, identical path set to the decoded
JSON). `bm_health.py`'s collector in `members()` only records nodes with `offset-in-file`; the one
left out is the `part_damage_types` **array node** itself, which has no offset — its 24 × 8 children
are among the 245. So there is no coverage hole, but the printed number invites the reader to think
one member was skipped. Say "245 primitive members".

**9 · The row states 36,000 as a number, the pending condition lives elsewhere.**
§12: "`max_health` 2000 -> 36000 (T-DM1, a switch declared for `bm-009` only)" and then "-> 36,000
HP and tank cannon 24 / 48 / 25 hits = T-14's table". The doc and the switch file both say the value
is **pending Q1-DM-A** (H1 would need 18,000, and 48 hits is what H1 currently predicts).
`t10_damage.py --check` even prints "Done clause 2 PARTIAL". A reader of §12 alone gets a settled
number; the row should carry "pending Q1-DM-A".

**10 · One stale clause in the doc.** `Working/Translation/T10_DAMAGE.md:27`: "6 declarations,
1 pending (`max_health` 36000) **until a build carries it**" — bm-009 now carries it (the switch
declares `"build": "bm-009"` and the module holds 36000). Everything else in that doc matches its
generator (`t10_damage.py --check`: `md match True, json match True, switch file clean True`,
`check ok`).

## Spot-checks

Each value below was read from the artefact, not from the journal.

| # | Value in the doc / json | Where verified | Result |
|---|---|---|---|
| 1 | `max_health` 2000 → **36000**, "3,741 B in, 3,741 B out" | `build.../batmobile_health_medium.vmodc` bytes: `int32 @80` = 36000; the shared source `@80` = 2000; whole-file byte diff = **2 bytes** (0x07D0 → 0x8CA0); both files 3741 B | ✓ |
| 2 | `.epe` `damage` hash 670,155,287 → **1,928,726,201** "at 474" | `hash_jenkins("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile_health_medium.vmodc")` = 1928726201; `uint32 @474` = 1928726201; bm-002's `@474` = 670155287; `0x4f489f01` property present | ✓ |
| 3 | "59 parts use 19 distinct damage types; 24 `PartDamageType` rows; 4 without a row" | built parts module (`jc3adf`): 59 parts, 19 distinct types; private module: 24 rows, set difference = the 4 named types; **8 parts** affected (the check does not print that number) | ✓ (counts), +1 new figure |
| 4 | `front/rear_wheels_damage.skew_health` 200 → **400** | land_global `int32 @108` and `@120` = 400 (bm-002: 200); exactly **4 bytes** differ in the 3,399 B file | ✓ |
| 5 | tank cannon **24 / 48 / 25** hits at 36,000 HP | `damage_predict.py --root Builds/bm-009 table` re-run — identical table; 36000/1500 = 24 (H0), 36000/750 = 48 (H1) | ✓ |
| 6 | "24 heavy-cannon hits" is a decoded BmAK ratio, not a chosen number | `Research/JC3Grab/DAMAGE_MODEL.json` `arm_targets.bmak_ratio` = `health 1200`, `heavy_cannon_damage 50.0`, `heavy_cannon_hits 24`, `source: DAMAGE_RULES.json (G1-14)`; 1200/50 = 24 | ✓ |
| 7 | "`aafdiff` vs bm-002 exactly 4 files" | sha256 of every file in both `aaf` trees: 1 added (the private module) + 3 changed (`@files.xml`, `custom_land_global.vmodc`, `.epe`) = **4** | ✓ |
| 8 | "605 `.toc` records (1 appended)", module internal at **23,222,112** | receipt + `--check` step 1: offset 23222112, size 3741, non-zero; bm-002 had 604 records | ✓ |
| 9 | All five artefact hashes | `.ee` `90422182…`, `.toc` `501F6A8D…`, module `D325308B…`, land_global `6F7F2629…`, `.epe` `1778816D…` — recomputed on disk, **5/5 match** the receipt | ✓ |
| 10 | R7 "unchanged" | staged shared module is byte-identical to bm-002's (`sha256 AF5C33E6306DEBA7…`); the tamper baseline `tmp/b09/tamper/before.sha` lists five files and its spec hash `0a35df46…` still equals `Working/Damage/bm_health.json` today | ✓ against bm-002 — see issue 4 for the baseline |

## What I could not verify (and did not pretend to)

* **No game launch, so nothing about runtime behaviour is tested.** Whether the engine accepts an
  internally packed, privately named `VehicleDamage` module, whether the `.epe` hash repoint is what
  gives the car 36,000 HP, and whether the `Default` fallback for 8 parts behaves as the fleet's own
  fallback does are all phase-Q questions. The card says so; this review agrees.
* **The 4 tamper tests were not re-run** — they write into `Builds/bm-009` and the shared module,
  which this review is forbidden to touch. Their evidence is on disk (`tmp/b09/tamper/`: 5 `.bak`
  files and `before.sha`, whose hashes match the current tree for the spec and — via the receipt —
  for the `.ee`).
* **The `.toc`'s mtime (01:09) is later than the build (00:54).** That is the tamper-4 restore
  rewriting the same bytes; the content hash equals the receipt (`501F6A8D…`), so there is no drift.
  Noted so a future reader does not read the mtime as a post-build edit.

## Summary for the tracker

The card's shape is right and its one risky decision is the *right* kind of risk: 36,000 is derived
from a decoded BmAK ratio (1200 HP / 50 per heavy-cannon hit), written only into a private module
(R7), declared as an out-of-domain switch with a named probe (Q1-DM-A) and an explicit alternative
(18,000), and left *pending* rather than presented as fact. The fixes needed are documentation and
provenance, not rebuilds: correct 77 → 81 entities (29 vehicle folders) in the generator, delete or
correct the "every part's type resolves" sentence, move `Boat_Antenna` out of the B-04 sentence,
name R7's baseline ("unchanged since bm-002; the tree copy already carries test-085/091's values"),
add the card's missing `Out:` line, and carry "pending Q1-DM-A" into §12.

## Commands run (all read-only apart from the check's own temp XML under `tmp/b09/`)

```
python Tools/scripts/bm_health.py --check
python Tools/scripts/damage_audit.py --build Builds/bm-009/aaf
python Tools/scripts/damage_predict.py --root Builds/bm-009 table
python Tools/scripts/damage_predict.py --check
python Tools/scripts/t10_damage.py --check
sha256sum Working/Damage/bm_health.json
python - (sha256 of .ee/.toc/module/land_global/.epe vs receipt; struct @80/@108/@120/@474;
          hash_jenkins recompute; byte diffs; aaf tree hash diff)
python - (jc3adf over the built parts module and the private module: 59 parts, 19 types, 24 rows)
python - (E:/Modding/_JC3grab/entities/*.ee.json: 81 entities / 29 folders share lave_health_medium;
          archived VehicleDamage values 700 / 1 / 1)
```

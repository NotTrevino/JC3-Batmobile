# Assumption challenge — card B-06 · Weapon entities (private copies)

**Scope.** `GRAB_BACKLOG.md` §0.5 (R1–R14), §8 card `B-06`, the §12 `B-06` row, MODLOG
§"B-06 · Weapon entities (private copies) — done", and the card's outputs:
`Tools/scripts/bm_weapons.py`, `Tools/scripts/jc3weapons.py`, `Working/Weapons/manifest.json`,
`Builds/bm-006/receipt.json`, `Builds/bm-006/aaf/…`.

**Method.** Every claim was re-derived from disk: the generator's own `--check`, SHA-1/SHA-256 of
the shipped and private files, `ConvertAdf -e` / `ConvertProperty --e` exports to OS temp, byte-level
float reads at the edited offsets, the project hash `rbmhdr.hash_jenkins`, the 295 cached fleet
graphs in `E:/Modding/_JC3grab/wiring/epe`, `Research/JC3Grab/{INDEX.jsonl,WEAPONS.jsonl,WEAPON_WIRING.md,
CHAIN.json}`, and `Research/BatmobileGrab/CHAIN.json`.

Read-only: no backlog, MODLOG, `Research/`, `Tools/` or game file was edited; the only file written is
this report. The card's `--check` was run as instructed; it rewrites its own scratch
`tmp/b06/built.xml`. No game launch, no write under `D:/Games` or `E:/Games`, no git, no secrets.

**Alphabetical note on provenance.** `AA7096C9` and `6D4C8277` are *hash-decoded* names (verified
below), so using them is not a guess. The card's real risks are elsewhere: the build predates its
own dependency, one guard is a tautology, and two behaviour members were left pointing at the APC.

---

## VERDICT SUMMARY

| # | Assumption | Verdict |
|---|---|---|
| A1 | `bm-006` was built from the `bm-005` bytes it records | **BROKEN** — base is now `f4abe91d…`; the build used `d118c0aa…` |
| A2 | `bm_weapons.py --check` re-derives the delivered build | **BROKEN** — 6 objects differ; exit 1 |
| A3 | The "base build changed" guard would detect a moved dependency | **BROKEN** — it compares the base file to itself |
| A4 | `id:AA7096C9` = `tuning_file`, `id:6D4C8277` = `autoaim_tuning_file` | **HOLDS** — both hash-decode |
| A5 | The medium tank's own graph carries the exact w602/w603 tune + autoaim values written | **HOLDS** |
| A6 | The Serpente's own graph carries the w618 tune + no-lock-on autoaim written | **HOLDS** |
| A7 | `fire_rate` is seconds between shots, 1:1 with BmAK `FiringInterval` (2.0 / 0.138) | **HOLDS** |
| A8 | `velocity` 500 → 400 is a decoded value | **WEAK** — `derived` via `/100` with an unstated JC3 unit |
| A9 | offsets `0xA0` / `0x9C` identify those members and in-place patching is byte-safe | **HOLDS** |
| A10 | Writing float32 `0.138` satisfies a re-read of `0.138` | **HOLDS** — relative 1e-6 tolerance |
| A11 | `w602`/`w603` ship no `.ee`, so a tune-only copy is the whole entity | **HOLDS** as a file claim; loading is untested |
| A12 | The graph names `.wtune` while the shipped file is `.wtunec` (engine convention) | **HOLDS** — 320 `.wtune` / 0 `.wtunec` in graphs; 0 `.wtune` / 103 `.wtunec` in INDEX |
| A13 | "all 34 shipped tunes are named `<basename>.wtune`" (why the copy keeps its inner name) | **BROKEN** as a universal — counter-example on disk |
| A14 | Done 1: "every weapon path the `.epe` names **exists in the build**" | **BROKEN** literally — 2 of 9 exist there |
| A15 | B-06 needed only to repoint tune + autoaim; the other APC leftovers are out of scope | **BROKEN** for `impact_usage`; `sound_*` hidden |
| A16 | The two `w618` components need no private copy (no T-11 numeric edit) | **WEAK** — true for numbers, narrower than the Do |
| A17 | `@files.xml` registration is required and the edit preserves the file's EOL | **HOLDS** (one pre-existing CRLF, not B-06's) |
| A18 | No shipped module was edited in place (R7) | **HOLDS** — source SHA-1s match the receipt |
| A19 | `467 → 467` objects and `aafdiff` 687/2/2 | **HOLDS** |
| A20 | The installer deploys everything the build needs | **HOLDS** at file-list level (loose-file loading unproven) |

**6 BROKEN, 3 WEAK, 11 HOLDS.** The tune engineering (A4–A12, A18, A19) is solid and reproducible. The
problems are (a) a stale dependency that makes the card's own gate fail, (b) a guard that cannot see
it, and (c) a behaviour repoint the card inherited and did not finish.

---

## A1 — The build's base is the `bm-005` bytes the card records

**Assumption (silent).** `Working/Weapons/manifest.json` `base` names `Builds/bm-005` with
`epe_sha256 d118c0aa…`, 124,520 B, 47 classes; the delivered graph is that base plus 8 member
repoints.

**Test.**

```
$ sha256sum Builds/bm-005/…/v0300_…_civilian_01.epe
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf
$ ls -l Builds/bm-006/…/v0300_…_civilian_01.epe
124776  b89fea2df67ccceba98c2779baaa73512cbcd8dc9b6a595f64631dab3aa4d043
```

The manifest's recorded base (`d118c0aa…`, 124,520 B) is B-05's **pre-rework** file; `bm-005` on disk
is the reworked `f4abe91d…` (124,488 B). B-06 was written 04:49, B-05's rework 06:16.

**Consequence measured in the delivered graph** (export to temp, parse):
```
w602_mediumtank_canon          weapon_type 2
w603_mediumtank_mgun           weapon_type 2
w618_sportsmuscle_missile      weapon_type 1   ← pre-rework (reworked B-05 writes 2)
w618_sportsmuscle_missile_emp  weapon_type 1
4 × attach.vehicle still carry  id:A90F5E74 = weapon_anchor   ← B-05 rework omits it
```

**Verdict: BROKEN.** B-06 did not edit its dependency, but it rebuilt on a base that later moved, and
it now ships members its dependency deliberately removed (`weapon_anchor` names no B-04 part).

---

## A2 — `bm_weapons.py --check` re-derives the delivered build

**Test (the card's own command).**

```
$ python Tools/scripts/bm_weapons.py --check
FAIL: the built .epe differs from the re-derived plan: 6 object(s) missing, 6 unexpected, …
  … ('id:A90F5E74', 'weapon_anchor') …  (unexpected side)
CHECK_EXIT=1 (1 failure(s))
EXIT=1
```

The 6 objects are exactly the 4 `attach.vehicle` points carrying the extra `weapon_anchor` ref and
the 2 `w618` components whose `weapon_type` is still 1.

**Verdict: BROKEN.** The card's §12 row presents this command as passing. It does not. The second
command still passes (below), so the failure is scoped to the graph, not the tunes:

```
$ python Tools/scripts/jc3weapons.py --check --root Builds/bm-006
check ok: 3/3 edit(s) re-read from the built tunes, 2/2 tune file(s) decode
EXIT=0
```

---

## A3 — The base-integrity guard would catch a moved dependency

**Assumption (silent, from the code's own message).** `bm_weapons.py` prints
`"the base build's .epe changed - a card may not edit its dependency"` if the base moves.

**Test.** `build()` line 253 stores `"epe_sha256": sha256(open(BASE_EPE).read())` into the freshly
derived `doc`; `check()` line 556 compares `sha256(open(BASE_EPE).read())` with that same value.
Both operands are produced in the same run, so the comparison is a tautology. The recorded base sha
in the manifest is never consulted; `receipt.json` stores only `"base": "Builds/bm-005"` (no sha).

**Verdict: BROKEN.** This is why A1 surfaced as a 6-object graph diff instead of a one-line
dependency error. The guard is structurally incapable of failing.

---

## A4 — `AA7096C9` = `tuning_file`, `6D4C8277` = `autoaim_tuning_file`

**Assumption.** The card calls these members by name and repoints them; a wrong name would mean the
wrong slot.

**Test.**
```
tuning_file           AA7096C9
autoaim_tuning_file   6D4C8277
```
Both match the ids exactly. `Research/JC3Grab/WEAPON_WIRING.md:16` independently records
`tuning_file = AA7096C9`, `autoaim_tuning_file = 6D4C8277`.

**Verdict: HOLDS (decoded).** The manifest's shorter label "autoaim" is a wording nit, not a value
problem.

---

## A5 — The medium tank's own graph carries the exact w602/w603 values written

**Assumption.** The two private paths and `autoaim_vehicle_mgun.wtune` are what the weapon's own
carrier graph names.

**Test** (`E:/Modding/_JC3grab/wiring/epe/v0201_car_capstone_mediumtank_debug.ee.xml`):
```
CBulletWeaponBase w603_mediumtank_mgun  type 2
   id:AA7096C9 = editor/entities/jc_weapons/06_vehicle/w603_mediumtank_mgun/w603_mediumtank_mgun.wtune
   id:6D4C8277 = editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune
CBulletWeaponBase w602_mediumtank_canon type 2
   id:AA7096C9 = editor/entities/jc_weapons/06_vehicle/w602_mediumtank_canon/w602_mediumtank_canon.wtune
   id:6D4C8277 = editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_mgun.wtune
```
The built graph carries exactly these, with the leaf renamed to `w6xx_batmobile_<name>`.

**Verdict: HOLDS.**

---

## A6 — The Serpente's own graph carries the w618 pair written

**Test** (the armed signature variant, same vehicle):
```
CMissileWeaponBase w618_sportsmuscle_missile type 2
   id:AA7096C9 = editor/entities/jc_weapons/06_vehicle/w618_sportsmuscle_missile/w618_sportsmuscle_missile.wtune
   id:6D4C8277 = editor/entities/jc_weapons/00_shared/autoaim_tuning/autoaim_vehicle_no_lockon_missile.wtune
```
The built `w618_sportsmuscle_missile` and `…_emp` carry both values.

**Verdict: HOLDS for the path values.** (The carrier class is a different story — see A16.)

---

## A7 — `fire_rate` is seconds between shots and BmAK's 2.0 / 0.138 are the values

**Assumption.** The semantic bridge is 1:1, not merely two fields whose names match (R5).

**Test 1 — the BmAK side.** `Research/BatmobileGrab/CHAIN.json`:
```
RVehicleWeapon.FiringInterval   2.0                    ×3
RVehicleWeapon.FiringInterval   0.1379999965429306     ×4
RBatmobileCannon.ComboFiringInterval 0.1379999965429306 ×4
```
**Test 2 — the JC3 side.** `Research/JC3Grab/WEAPONS.md:82`: "`fire_rate` is the seconds between
shots (0.1 on the buggy MG is 10 shots/s)"; `T7_WEAPONS.md:24,103,142` record the 1:1 bridge.
**Test 3 — the written bytes.** `struct.unpack('<f', 0xA0)` = `2.0` and `0.1379999965`.

**Verdict: HOLDS.** This is a genuine decoded behaviour bridge, not a name match.

---

## A8 — `velocity` 500 → 400 is a decoded value

**Assumption.** Writing 400 changes the projectile speed by the intended ratio.

**Test.** `T7_WEAPONS.md:25,105` classify this as **`derived`**: BmAK `Projectile.Speed`
40000 UU/s (1 UU = 1 cm) = 400 m/s; JC3 `velocity` is 500 and "the member's unit is not stated in any
decoded file"; the mapping is `/100`. The BmAK value exists (`CHAIN.json`: `Projectile.Speed 40000.0`),
and the manifest's class is `derived`, not `decoded`.

**Verdict: WEAK.** The unit bridge (JC3 `velocity` unit unknown) is an assumption; it is correctly
labelled `derived` in the manifest and T7, so R4 is not violated, but the §12 row's flat
"`velocity` 500 -> 400" reads stronger than the evidence. It only becomes `decoded` at Q-3 #3.

---

## A9 — The offsets identify those members, and in-place patching is byte-safe

**Test.** Source bytes at the reported offsets: w602 `0xA0 = 1.75`, `0x9C = 500.0`,
w603 `0xA0 = 0.1`; copies: `2.0`, `400.0`, `0.138`. Sizes unchanged (14,224 / 14,223), and
`jc3weapons --check --root` decodes the copies and finds exactly one float row whose leaf name is
`fire_rate` / `velocity` per tune, then compares it.

**Verdict: HOLDS.** The member is identified by the decoder after the write, not only by the offset.

---

## A10 — float32 `0.138` re-reads as `0.138`

**Test.** `jc3weapons.py` compares `abs(got - want) <= 1e-6 * max(1, abs(want))`. The stored float is
`0.1379999965`; the difference is ~3.5e-9, well inside the tolerance, and the printed value is
`0.138`.

**Verdict: HOLDS.** (A strict equality check would have failed; the tolerance is deliberate and stated
in the code.)

---

## A11 — `w602`/`w603` ship no `.ee`, so a tune-only copy is the whole entity

**Test** (`Research/JC3Grab/WEAPONS.jsonl`):
```
w602_mediumtank_canon    dir_files [{…w602_mediumtank_canon.wtunec, mount patch, size 14224}]
w603_mediumtank_mgun     dir_files [{…w603_mediumtank_mgun.wtunec,  mount patch, size 14223}]
w618_sportsmuscle_missile dir_files [{….ee base}, {….ee.toc}, {….epe}, {….wtunec}]
```

**Verdict: HOLDS as a file claim.** Only one patch file exists per weapon, so a tune copy is all there
is to copy. Whether a loose `.wtunec` in dropzone actually overrides the packed base is a load
question the card does not claim to have answered (the loose-install limit is carried).

---

## A12 — The `.wtune`/`.wtunec` pairing is the engine's convention

**Assumption.** The graph may name `….wtune` while the shipped file is `….wtunec`, so Done 1's
substitution is legitimate.

**Test.** Across the 295 cached fleet graphs: **320** mentions of `.wtune`, **0** of `.wtunec`.
In `INDEX.jsonl` under `editor/entities/jc_weapons/`: **0** `.wtune`, **103** `.wtunec`
(e.g. the autoaim presets are indexed as `…autoaim_vehicle_mgun.wtunec`).

**Verdict: HOLDS.** The two names are the reference form and the packed form, consistently.

---

## A13 — "all 34 shipped tunes are named `<basename>.wtune`"

**Assumption.** The private copies' inner ADF instance names are left as the shipped basenames because
that is the universal shipped pattern; only a non-byte-identical re-encode could change them.

**Test 1 — the universal.** `_JC3grab/weapons` holds 20 `.wtunec` files; `WEAPONS.jsonl` `dir_files`
lists 25 (not 34). A raw-byte search for `<basename>.wtune` inside each file finds it in 12 of 20,
absent in 8. Converting one absent case:
```
$ ConvertAdf -e w611_fighterbomber_missile.wtunec x.xml
<instance name="w611_fighterbomber.wtune" … type-name="WeaponTuning">
```
The instance name is **not** the file basename (`w611_fighterbomber` vs
`w611_fighterbomber_missile`). **Test 2 — the re-encode claim.** `ConvertAdf -e` then `-i` on the
private w602 copy: `14224 → 14208`, `not identical`. That half is right.

**Verdict: BROKEN as a universal.** The two copies do follow the pattern (their inner names are
`w602_mediumtank_canon.wtune` / `w603_mediumtank_mgun.wtune`), and whether the name is load-bearing
is correctly UNKNOWN. But the justification ("all 34 …") is false on disk: 25 tune rows exist, 8 of
20 local files carry a different source name, and the "34" has no source found. Keeping the name may
still be the right call; the sentence supporting it is not evidence.

---

## A14 — Done 1: "every weapon path the `.epe` names exists in the build"

**Assumption.** The card's Done criterion is the command that was run.

**Test.** `done_paths()` in `bm_weapons.py`:
```
private: 2   (the two new .wtunec files, present under Builds/bm-006/aaf)
shared : 7   (resolved against INDEX + the APC graph + SIGNATURE_DIFF, NOT against the build)
dangling: 0
```
The 7 are the rigid-object `.etune`, two autoaim `.wtune`s, the M2 grip point, the `w618` tune, and
two M2 model paths. Spot-check: `w206_mounted_capstone_m2hm_body.model_xml` has **0** hits in
`INDEX.jsonl` and resolves only because it is a string inside the APC's shipped graph.

**Verdict: BROKEN literally.** Seven of the nine paths do not exist in the build; the gate checks a
weaker, defensible property ("resolves in the shipped game") and the PASS line says "0 dangling".
The §12 row repeats the Done wording, so a reader believes nine files are in `bm-006`.

---

## A15 — B-06 only had to repoint tune + autoaim; the other APC leftovers were out of scope

**Assumption.** B-05's stated handoff — "32 `w206`-path strings, 4 `50calImpact`, 4
`sound_turret_rotation_yaw` … for B-06 to repoint" — is satisfied by the two tune members and the
autoaim member.

**Test 1 — what B-06 repointed.** 8 members = 2 (`AA7096C9`, `6D4C8277`) × 4 components. Built
graph still carries:
```
w602_mediumtank_canon          id:D075017A = 50CalBulletImpact
w603_mediumtank_mgun           id:D075017A = 50CalBulletImpact
w618_sportsmuscle_missile      id:D075017A = 50CalBulletImpact
w618_sportsmuscle_missile_emp  id:D075017A = 50CalBulletImpact
sound_turret_rotation_yaw    ×4
sound_turret_rotation_pitch  ×4
```
**Test 2 — what the donor says.** The medium tank's own components:
```
w602_mediumtank_canon  id:D075017A = AAGunImpact
w603_mediumtank_mgun   id:D075017A = 50CalBulletImpact
```
So `w602`'s impact is known and differs (`AAGunImpact`), yet the clone keeps the APC's M2 impact.
`sound_turret_rotation_*` is not enumerated in the manifest's `unchanged_members` at all (those four
entries are the rigid-object `.etune`, the M2 body collision, the M2 grip point and the M2 body
model). `done_paths()` cannot see any of these because none is a path string.

**Verdict: BROKEN (R5).** The component *named* `w602_mediumtank_canon` still *behaves* with the APC's
M2 impact and turret sounds. The card's §12/MODLOG never state this; B-05's row explicitly handed the
`50calImpact` and `sound_turret_rotation_*` leftovers to B-06. This is the same name-vs-behaviour
failure R5 exists to prevent, and the Done gate is blind to it by construction.

---

## A16 — The two `w618` components need no private copy

**Assumption.** T-11 has no numeric edit for the missiles, so the shared shipped tune is correct and
R7 forbids touching it.

**Test.** `t7_weapons_edits.json` has 3 edits on 2 rows (T-WP1 twice, T-WP2 once); zero for
T-WP3/T-WP4 — true. But the Do says "for each cloned JC3 weapon: copy its `.ee`/tunes to a new private
path"; 2 of 4 components get no copy, and both `w618` objects remain `CBulletWeaponBase` clones of
the APC (the same vehicle's armed graph has `CMissileWeaponBase`). B-06 does not repeat B-05's
carrier-class caveat.

**Verdict: WEAK.** Declared as a limit (BL-4, R7) and safe (nothing shared is edited), but the row's
"2 private tune copies … 0 dangling" can read as full WPN coverage. The `w618` tune path is written
onto a bullet-weapon object, so its behaviour cannot be predicted from the path alone.

---

## A17 — `@files.xml` registration is required, and the edit preserves the file's EOL

**Test.** `deploy.py:14,106` states the rule and `add_to_manifest` inserts CRLF unconditionally;
`@files.xml` is 707 lines, 706 bare LF, exactly one CRLF (line 704,
`batmobile_health_medium.vmodc`, a pre-existing line), and the two B-06 lines end in LF:
```
ends CR? False  b'…w602_batmobile_cannon.wtunec</file>'
ends CR? False  b'…w603_batmobile_vulcan.wtunec</file>'
```
Both lines are present (lines 706–707).

**Verdict: HOLDS.** The "this file is LF" sentence is a slight simplification (one pre-existing CRLF
line), but B-06's two insertions match the dominant EOL, which is the property that matters.

---

## A18 — No shipped module was edited in place (R7)

**Test.** SHA-1 of the three shipped tunes against the receipt:
```
w602_mediumtank_canon    1a8c072ab67e…  match
w603_mediumtank_mgun     d9f58989839c…  match
w618_sportsmuscle_missile f93f9c40eb0d… match
```
`bm_weapons --check` also re-asserts each source SHA-1 every run. Only `Builds/bm-006` files differ
from `bm-005` (2 new tunes, `@files.xml`, `.epe`).

**Verdict: HOLDS.**

---

## A19 — `467 → 467` objects and `aafdiff` 687 identical / 2 new / 2 changed

**Test.** Parsed built graph: 467 objects, 46 classes (excluding the classless root). Tree diff vs the
current `bm-005`: 689 vs 691 files, 2 only in bm-006, 0 only in bm-005, 2 changed (`@files.xml`,
`.epe`) → 687 identical.

**Verdict: HOLDS.** (The manifest's `47` classes is the old counting convention; the file count and
object count are right.)

---

## A20 — The installer deploys what the build adds

**Test.** `Builds/bm-006/install.ps1` lists three files: the `.epe` and both private `.wtunec` files,
and `Verify` hashes each. It is generated, never run.

**Verdict: HOLDS at file-list level.** The deeper question — whether dropzone loose files (`.epe`,
`.wtunec`) override the packed base — remains UNKNOWN and is correctly carried as B-05's limit.

---

## What the card gets right (do not lose this in a rework)

* The private-copy approach genuinely respects R7; the shipped tunes are byte-identical.
* All three numeric edits are decoded, offset-verified and re-read by an independent decoder.
* The autoaim and tune repoints are sourced from the weapons' own carrier graphs, not chosen.
* `AA7096C9`/`6D4C8277` are hash-decoded names; the card is not guessing members from labels.
* The UNKNOWNs it declares (inner ADF name, loose-file install) are real and properly left open.

## The smallest correct repair

1. Re-run `bm_weapons.py --write` from the current `bm-005` (`f4abe91d…`): this removes the
   `weapon_anchor` refs and writes `weapon_type 2` for the `w618` pair; re-run both checks.
2. Make the base check compare `BASE_EPE` with the **recorded** base sha, and store that sha in
   `receipt.json`.
3. Repoint `id:D075017A` on `w602` to `AAGunImpact` (the donor value is on disk), and either repoint
   or explicitly declare the 8 `sound_turret_rotation_*` strings in `unchanged_members`.
4. Reword Done 1 or the §12 line so "exists in the build" means the 2 private files, with the 7
   shipped references named as shipped.
5. Fix the "all 34 … `<basename>.wtune`" sentence to the measured statement (the copy keeps the
   source's instance name, which is usually but not always the basename).

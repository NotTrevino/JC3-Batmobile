# Independent review — G1-10 · Animation sequences: names, bones, lengths, notifies

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only: no file under
`Research/`, `Tools/`, `GRAB_BACKLOG.md`, `MODLOG.md` or the game install was modified; this
report is the only file written. No game was launched, nothing was committed.

Card under review: `GRAB_BACKLOG.md` L416–437 (§G1-10), tracker row L1278, rules §0.5 L71–91.
Journal entry: `MODLOG.md` L8000–8038 (intent + done).
Outputs: `Research/BatmobileGrab/ANIMATIONS.md`, `Research/BatmobileGrab/ANIMATIONS.json`,
`Tools/scripts/grab_anims.py`, keyframes under `E:\Modding\_BmAKgrab\anims\keys\`.

## VERDICT: minor issues

The card is substantively delivered and its numbers reproduce. `grab_anims.py --check` exits 0
from a full re-derivation of the packages and PSAs, both committed records are byte-identical to
the re-derivation, every `Out` path exists, and every number I spot-checked matched the raw data.
The reasons it is not "sound":

* one real classification defect: 8 of the 253 sequences (`Batmobile_V2_Cannon_Reload_Left/Right`
  in each of the four packages) are classed `transformation` because the string `Shell` in the
  cannon **ammunition** bones (`Batmobile_L_Shell_*`, `Batmobile_R_Shell_*`) is taken as the
  transformation shell;
* the doc's taxonomy prose does not match the code in one rule (wheel-arch arms), and several
  counts in the generated `.md` are literals in the generator rather than derived values (R11);
* a few statements overstate what the files prove (`--write` "exports one PSA ... with umodel";
  the door AnimTree "has no sequence"; the `51` row label).

None of these invalidates the record: it is a bone/PSA record with per-row evidence, and the
mislabels are visible and re-derivable. Fix list at the end.

## Check output (verbatim)

Command, run from the project root `E:\Modding\JC3-Batmobile`:

```
python Tools/scripts/grab_anims.py --check
```

Output:

```
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\ANIMATIONS.json
ok E:\Modding\JC3-Batmobile\Research\BatmobileGrab\ANIMATIONS.md
PASS: 253 sequences, 13 sets, 3 trees, 253 PSA sequences, 3147888 keys, 309 notifies (204 sound, 35 script); 253/253 named, 253 bone lists, 253 mechanisms; 13/13 keyframe files present
```

Exit status: `0` (captured with `echo "EXIT=$?"`; the two `ok` lines and the `PASS` line are the
complete stdout, no stderr).

## Out-path audit

| Out (card L436–437) | status |
|---|---|
| `Research/BatmobileGrab/ANIMATIONS.md` | present, 384,784 B, 1,387 lines |
| `Research/BatmobileGrab/ANIMATIONS.json` | present, 2,358,421 B (valid JSON, keys `schema/generator/verdict/inputs/counts/mechanism_counts/notify_class_counts/sets/trees/sequences/duplicate_names/psa_name_differences/psa_missing`) |
| key-frame JSON outside the repo | present: 13 files in `E:\Modding\_BmAKgrab\anims\keys\`, 88 MiB total, one per AnimSet, plus the 13 PSA/`.config`/`.props.txt` triples in `E:\Modding\_BmAKgrab\anims\<package>\AnimSet\` |
| `Tools/scripts/grab_anims.py` (`--check` entry point named by the Done line) | present, 1,310 lines |

Card `In:` says "253 `AnimSequence`, 2 `AnimSet`, 1 `AnimTree`"; `objects.jsonl` actually holds
13 `AnimSet` + 3 `AnimTree` (2+2+2+7 sets, 1+1+1 trees across the four packages) and 253
sequences (37+37+37+142). The MODLOG entry states this correction explicitly — the card's `In:`
line is the wrong one, not the record.

## Done criterion vs what `--check` verifies

Card Done: "253/253 sequences named; each has a bone list and a mechanism class (or `other` with
the bones listed); `grab_anims.py --check` passes."

What `--check` does (`grab_anims.py` L1273–1290): re-runs `collect()` (reads `objects.jsonl`, the
four `.upk`s through `upk_read`, and the 13 PSAs), re-renders the JSON and the MD, compares both
texts byte-for-byte (`ok`/`FAIL`), then prints the counts and returns 0. So the counts on the
`PASS` line **are** re-derived, and 253/253 named + 253 bone lists + 253 mechanisms are reported.
Two gaps:

* the counts are printed, never asserted — `check()` returns 0 even if `named < sequences` or
  `with_bone_lists < sequences`; only a changed file makes it fail (and after `--write` it would
  pass again). "Done" is therefore gated by the operator reading the line, not by the exit code;
* keyframe presence is only a `WARN` (L1288) and still returns 0, so the third `Out` path is not
  gated by `--check` at all. The MD states this honestly (L1368: "`--check` ... reports whether
  the 13 files are present, but does not re-serialize the keyframes"), and the MODLOG records a
  separate read-back of all 13 files.

`psa_sequences` counts `psa_index is not None`, which would also count the `"remaining"` fallback
that assigns an arbitrary unused PSA row (L283–285). There are 0 such cases here (249
`exact+frames`, 4 `prefix+frames`), so the count is clean today, but the metric does not
distinguish "matched" from "assigned the leftovers".

## Issues

### 1. Eight sequences are `transformation` only because cannon ammunition is named `*Shell*` (substantive)

* Files: `Tools/scripts/grab_anims.py` L75 (`TRANSFORM_BONES`), L83
  (`TRANSFORM_SIGNATURE = ("Shell",)`), L169 (`is_transform_signature`); data in
  `Research/BatmobileGrab/ANIMATIONS.json`; rendered rows `ANIMATIONS.md` L119, L120, L156, L157,
  L193, L194, L331, L332; evidence L718, L719.
* `Batmobile_V2_Cannon_Reload_Right/_Left` are classed `transformation`. The only tracks that
  clear the 5 cm / 5° bar are the ammo casings:
  `Batmobile_L_Shell_Tween_001 14.65 cm / 77.50 deg`, `Batmobile_L_Shell_008 8.10 cm / 40.00 deg`,
  …, while the cannon's own bones show `cannon ... moved_bones 0` and `Vulcan ... moved 0` in the
  same JSON record. Nothing in these two sequences reconfigures the car.
* The rule itself is wrong here, not merely the result: `ANIMATIONS.md` L59 files `Heavy_Shells`
  under `cannon`, and L64 then claims `transformation` for `*Shell*`. Ammunition shells match,
  transformation shells were evidently not what the author meant. This is the R5 shape — a name
  that sounds like the behaviour — applied to a bone taxonomy rather than to a JC3 member.
* Impact: `mechanism_counts.transformation = 32` includes 8 false positives; any later step that
  reads "... is a transformation sequence" from this class (G1-12 deps on G1-10, ANI-2…8) inherits
  them. A suffix/whitelist rule (`Shell` excluding `_Shell_`, or an explicit list of the real shell
  bones) would fix it without touching anything else.

### 2. The doc's `suspension` rule is not the code's rule (wheel-arch arms)

* `ANIMATIONS.md` L63: "`suspension` - `SUSP*`, `Damper*`, `Wheel_Parent*`, wheel-arch arms."
* `grab_anims.py` L157–159 tests `"WHEEL_ARCH_Arm" in bone`, which matches
  `Batmobile_Chassis_REAR_WHEEL_ARCH_Arm_LB/_RB` but **not** the two parent arch bones
  `Batmobile_Chassis_{L,R}_REAR_WHEEL_ARCH`. Those record as `other`
  (`ANIMATIONS.json`, `Batmobile_V2_Bat_Tracker`: `other` max_dpos 60.462 cm / 28.372°, and the
  top evidence rows `..._R_REAR_WHEEL_ARCH 60.46 cm / 28.35 deg`).
* The MD line is prose in `render_md`, so it can never be caught by `--check`: it is a claim about
  the taxonomy that the tables beside it contradict.

### 3. Counts typed into the generated MD that `--check` cannot validate (R11)

All of these are string literals in `render_md`, so `--check` regenerates them identically even if
they are wrong:

| value | where | verified? |
|---|---|---|
| `37` ("the same 37 sequence names exist in the base / MK2 / Funhouse / Joker car sets") | `ANIMATIONS.md` L1277; script L1134 | correct — 37 names are in all four packages — but derived nowhere |
| `301-frame` / `284-frame` for the two `Disarm_Switch_Player` rows | L1333; script L1149 | correct (see spot-check 4) |
| `2007-frame` for the two `...Finale` rows | L1333; script L1152 | correct |
| `63`-character truncation, "three long `Phase2_JK_FACE` names" | L1333; script L1151–1152 | correct, but typed |
| "All 13 AnimSets" | L1372; script L1189 | correct (`counts.sets`), typed |

The script header also states "No value is hand-typed" (L25) and the MD says "nothing here is
hand-listed" (L3). That is true of the table cells and false of these sentences; the honest
statement is "every table value is derived; the prose contains a few constants read off the
record".

### 4. `names repeated across packages | 51` over-counts what the label says

* `ANIMATIONS.md` L22; same wording in `MODLOG.md` ("51 sequence names repeat across packages").
* 51 is `counts.duplicate_names` and is right, but 14 of those names repeat only **inside**
  `Playable_BatmobileJoker_SF` (e.g. `2Face_Finale`, `BM_Seperate_Out`, `BatMobile_Stand_Out`), not
  across packages. Label it "names occurring more than once" (the §8 sentence at L1277 already
  says that correctly).

### 5. The "bone" column is a generic `NameProperty` for non-sound notifies (R4 label)

* `ANIMATIONS.md` L962 header `... | class | bone | target / payload |`; 5 rows hold a Kismet event
  name, e.g. L1117 `AnimNotify_Kismet | JokerExitBmobStart`.
* `notify_record` (script L452–460) fills `rec["bone"]` from *any* `NameProperty` for classes other
  than `AnimNotify_Sound`/`RAnimNotify_Script`. For `AnimNotify_Kismet` the value is the Kismet
  event, not a bone. Rename the field (or only set it for classes where a bone is expected) — as
  written the record asserts a bone the payload does not establish.

### 6. `--write` does not export PSAs, and the umodel step is recorded nowhere

* `ANIMATIONS.md` L1344: "`--write` exports one PSA per AnimSet with umodel and writes a compact
  JSON per set to: ..."
* `grab_anims.py` never invokes umodel: no `subprocess` import, no umodel call (only the strings at
  L9, L25, L974, L1163, L1215). `--write` reads whatever `.psa` already exists and, if one is
  absent, records it in `psa_missing`, writes fewer keyframe files and exits 0. The
  `E:\Modding\_BmAKgrab\anims\` tree (13 PSAs, their `.config` with the hand-editable
  `[RemoveTracks]` sections, `.props.txt`) is an unreproducible prerequisite: neither the umodel
  command that produced it nor the origin of the removal choices appears in `MODLOG.md` or the
  scripts.
* I did test whether the config is trustworthy as provenance: it agrees with the PSAs. For the
  base `Batmobile_V2_Pose_States` set I checked all 5,536 (sequence, track) pairs; 5,522 have
  exactly the absence of position/rotation components that the config declares, and the only 14
  exceptions are `Batmobile_Bone_Chair_Rot_001` sitting at identity rotation without a config
  entry. So "null = the config says that component was not exported" is literally true and the
  config is not a guess — but it is still an input file whose author is undocumented.

### 7. The AnimTree bullet contradicts itself and asserts an absence as a fact

* `ANIMATIONS.md` L1372: "The three AnimTrees are recorded but do not own sequences:
  `Batmobile_Skel_Ctrl_Door` has no sequence on its `AnimNodeSequence`, and
  `Batwing_Vehicle_AnimTree` points at `Batwing_Rescue_01`." The second clause contradicts the
  first.
* On the door tree, what the files show is that export 158 (`AnimNodeSequence`) carries only three
  tags (`IntProperty` @144, `FloatProperty` @152, `ParentNodes` @156) and **no** `AnimSeqName`
  `NameProperty` @280, while the Batwing node (export 275) does carry it (`Batwing_Rescue_01`).
  "No tag" is not "no sequence" — cooked packages strip defaults. The claim should be "the record
  carries no `AnimSeqName` property" (or `UNKNOWN`), not "has no sequence".
* The MD's §2 table also prints only `children: Child` and drops the `sequence` field the JSON
  does have, which is why the Batwing binding is invisible in the table.

### 8. Unsupported method claim: "PSA `ANIMINFO` is sorted by name"

* `ANIMATIONS.md` L1333. Nothing in `grab_anims.py` or `ANIMATIONS.json` records the PSA
  `ANIMINFO` order or compares it to sorted order; the claim is inferred from the two names that
  truncate to the same 63 characters. The matching outcome (249 exact + 4 prefix, unique indices,
  0 frame mismatch) supports the mapping, not the sort claim. It is very likely true of umodel's
  exporter, but it is stated as a fact with no evidence attached.

### 9. "Every notify time is within its sequence length" is true but not checked

* `ANIMATIONS.md` L944 and L1376; nothing in `check()` computes it. I verified independently: 0 of
  309 notify times exceed their `sequence_length`. The statement is correct; it should be an
  assertion inside `check()` (or be phrased as the author's verification, not a property of the
  record).

### 10. Minor: `other` example list names a category its rows never use

* `ANIMATIONS.md` L65 lists "tracker" among the `other` motions, but the only tracker sequence
  (`Batmobile_V2_Bat_Tracker`) is `transformation` (L108, by the ≥3-mechanism rule: canopy 35.3 cm,
  cannon 57.2 cm, missile bays 10.9 cm/15.0°, transformation 57.5 cm, suspension 34.4 cm). The
  classification is defensible under the printed rule; the example list is not.

## Spot-checks

All performed against the data the script reads (the 13 PSA files) and against
`ANIMATIONS.json`, independently of `grab_anims.py` (own struct parser; no import of the script).

| spot-check | where in the doc / JSON | verified against | result |
|---|---|---|---|
| 1. PSA keys read = `3,147,888` | `ANIMATIONS.md` L16, verdict L5, check line | sum over the 13 `ANIMINFO` arrays of `NumRawFrames × bone count` parsed directly from the PSA headers | 3,147,888 exactly (per set: 26,271 ×3 Chassis, 236,664 ×4 Pose_States, 25,363 Camera, 1,197,471 Phase2_JK, 787,501 Phase2_JK_FACE, 70,488 Phase2_TG, 15,325 Batwing_Rescue) |
| 2. `Batmobile_V2_Bat_Tracker` (base package) evidence `Weapons_Trans 57.51 cm`, `Heavy_Shells 57.18 cm`, `R_REAR_WHEEL_ARCH 60.46 cm / 28.35 deg` | `ANIMATIONS.md` L717; JSON `dpos_cm` 57.5063 / 57.182 / 60.462 | max distance from frame 0 read from `Playable_Batmobile_SF/AnimSet/Batmobile_V2_Pose_States.psa` keys | 57.5063 cm / 57.182 cm / 60.462 cm, rot 28.347° — match |
| 3. `Batmobile_V2_Cannon_Fire` = 22 frames, 0.700 s, `Heavy_Cannon_Barrrel_02 53.38 cm` | `ANIMATIONS.md` L95, L677; JSON `num_frames` 22, `sequence_length` 0.7, `dpos_cm` 53.376 | PSA `ANIMINFO` (raw frames 22, track 22.0, rate 31.429 → 0.700 s) and keys | 22 / 0.7 / 53.376 cm — match |
| 4. `Disarm_Switch_Player` = 301 frames ↔ PSA `Disarm_Switch_Player_180`; 284 frames ↔ PSA `Disarm_Switch_Player`; the two `...Finale` rows are both 2007 frames | `ANIMATIONS.md` L205, L259, L284, L286, L1333 | JSON `num_frames`/`psa_frames`/`psa_match` | 301→301 (`prefix+frames`), 284→284 (`exact+frames`), both Finale rows 2007 and both PSA names truncate to `..._2Face_Fin` — match |
| 5. 309 notifies, 204 `AnimNotify_Sound`, 35 `RAnimNotify_Script` | `ANIMATIONS.md` L19, L20, L948–L960 | sum over the 253 JSON sequences' `notifies` | 309 / 204 / 35 — match; 1 sound notify without an `AkEvent` (documented at L1375) |

Extra checks done while reviewing (no doc numbers involved):

* `TrackBoneNames` order equals PSA `BONENAMES` order for all 13 sets (the MODLOG claim), compared
  through each `.props.txt` and the PSA header.
* The 13 keyframe files total 88 MiB, matching the MODLOG's "92 MB / 88 MiB".
* `inputs.objects_sha256` in `ANIMATIONS.json` equals the sha256 of the current
  `Research/BatmobileGrab/objects.jsonl`.
* `percent (frames − 1) / sequence_length == rate_scale` for all 253 sequences (0 exceptions),
  which independently supports the offset-156/160/168 tag mapping the doc depends on.
* Mechanism counts sum to 253; every sequence has a non-empty `active_bones` list; `psa_index` is
  unique within every set.

## Fix list (smallest first)

1. `grab_anims.py` L83/L169: stop treating `Batmobile_*_Shell_*` ammunition as the transformation
   shell (e.g. require `Shell` not preceded by `_L_`/`_R_`, or an explicit shell-bone list); re-run
   `--write`, which will move the 8 `Cannon_Reload_*` rows out of `transformation` and update the
   evidence rows. Card Done is unaffected (still 253 named / 253 bone lists / 253 mechanisms).
2. `ANIMATIONS.md` L63 (script L162): make the printed rule match `bone_category`, or extend the
   code to catch the two `_REAR_WHEEL_ARCH` bones.
3. Replace the typed prose counts (L1134, L1149, L1152, L1189) with values from `doc["counts"]` /
   `doc["duplicate_names"]` / `doc["psa_name_differences"]`, so `--check` actually validates them.
4. Relabel L22 (and the MODLOG sentence) to "names occurring more than once", and rename the JSON
   `bone` field for notify classes where it is not a bone (L1117 is the visible case).
5. Correct L1344: `--write` consumes existing PSAs; record the umodel command that produced
   `E:\Modding\_BmAKgrab\anims\` (and the origin of the `RemoveTracks` config) in `MODLOG.md`.
6. Reword L1372 (door `AnimNodeSequence`: no `AnimSeqName` property rather than "no sequence";
   drop the "do not own sequences" clause or exclude the Batwing tree from it), and either assert
   the notify-length property in `check()` or attribute it to the author's verification. Add the
   `psa_name_differences` sortedness check, or drop the sort claim at L1333.

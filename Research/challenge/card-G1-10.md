# Assumption challenge — G1-10 · Animation sequences: names, bones, lengths, notifies

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written; no game launched, nothing installed into `D:\Games`, nothing committed. This report
is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 71–91), the G1-10 card (lines 416–437), the
§12 row (line 1278: `| G1-10 | done | Research/BatmobileGrab/ANIMATIONS.md + MODLOG §"G1-10 ·
Animation sequences — done" |`), `MODLOG.md` §"G1-10 · Animation sequences — intent" (line 8000)
and §"G1-10 · Animation sequences — done" (line 8020), the outputs
`Research/BatmobileGrab/ANIMATIONS.{json,md}`, the script `Tools/scripts/grab_anims.py`, the
13 PSA/`.config` triples and the 13 keyframe files under `E:\Modding\ArkhamKnight\_grab\anims\`, and the
cooked packages under `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole` (read only, through
`upk_read.py`).

## VERDICT

**The record is reproducible and its numbers match the data it reads, but four of its stated
methods are false and its universe is not the Batmobile's animation universe.** 17 assumptions
tested: **6 HOLD, 7 WEAK, 4 BROKEN.**

What holds: every one of the 253 sequences names/bone-list/mechanism counts out; the PSA mapping
is unique (249 `exact+frames` + 4 `prefix+frames`, 0 fallbacks, no duplicate `psa_index` in any
set); the 3,147,888-key total reproduces as `Σ(frames × bones)` over the 13 PSAs; PSA bone order
equals `TrackBoneNames` for 13/13 sets; the cm/quaternion/hierarchy convention survives an
independent rebuild against `BONES.json`; 203/204 sound notifies resolve to a same-package
`AkEvent` and all 39 distinct event names exist in `AUDIO_MAP.json`; no PSA carries scale keys,
so nothing is silently dropped.

What breaks:

* **`PSA ANIMINFO is sorted by name` is false** — 12 of 13 PSAs are not sorted; the rows follow
  the AnimSet's `Sequences` array. Consequently the two 2007-frame `Phase2_JK_FACE` rows are
  **swapped** in the record, and those two animations differ in 74,389 of 287,001 keys.
* **`*Shell*` is not the transformation shell** — 8 `Cannon_Reload_*` sequences are classed
  `transformation` because cannon *ammunition* bones are named `Batmobile_L_Shell_*`; the same
  sequences show `cannon ... moved_bones 0`. `transformation = 32` is really 24.
* **253 is not the Batmobile's AnimSequence count** — six other Batmobile packages carry 25 more
  `AnimSequence` objects, six of them vehicle-mechanism sequences on the same skeleton, and
  `Batmobile_V2_Tank_Spread_Open_Showcase` is 72 frames / 2.367 s against the playable 61 / 2.000.
* **`frame_times_s` is not a time base** — it is `i / PSA rate`, and the PSA rate is
  `frames / duration`, not `RateScale`; a 2-frame sequence gets a 0.0167 s step instead of
  0.0333 s (2×), a 138-frame one 4.5336 s instead of 4.5667 s. `grab_poses.py` (G1-12) and
  `t12_parts.py` (T-12) both consume it; T-12 divides frame deltas by it to report deg/s.

```
$ python Tools/scripts/grab_anims.py --check
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\ANIMATIONS.json
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\ANIMATIONS.md
PASS: 253 sequences, 13 sets, 3 trees, 253 PSA sequences, 3147888 keys, 309 notifies (204 sound, 35 script); 253/253 named, 253 bone lists, 253 mechanisms; 13/13 keyframe files present
EXIT=0
```

The card's Done line — "253/253 sequences named; each has a bone list and a mechanism class (or
`other` with the bones listed); `grab_anims.py --check` passes" — is met *for the four packages
it selected*, and each of its three clauses is printed by `--check`. What `--check` cannot do is
fail: it returns 0 unless a committed file differs (A7), and it never asserts the counts it
prints.

---

## A1 — The four Playable packages are the Batmobile animation universe (253 = all)

**Test.** Count `AnimSequence` / `AnimSet` / `AnimTree` exports in every Batmobile-named package
in the cooked folder, not only the four the card names (the §0.6/README package list is the four
Playable packages plus their `_Std_*` variants).

```
Playable_Batmobile_Std_1_SF.upk               exports=    4 animclasses=-
Playable_Batmobile_Std_6_SF.upk               exports=   92 animclasses=-
Playable_BatmobileMK2_Std_SF.upk              exports=    4 animclasses=-
Playable_BatmobileJoker_Std_SF.upk            exports=    4 animclasses=-
Playable_BatmobileFunhouse_Std_SF.upk         exports=    4 animclasses=-
Showcase_Batmobiles_Standard.upk              exports= 1055 animclasses={'AnimSet': 1, 'AnimSequence': 3, 'AnimNotify_Sound': 29, 'AnimTree': 1, 'AnimNodeSequence': 1, ...}
Showcase_Batmobiles_MK2.upk                   exports=  945 animclasses={'AnimSet': 1, 'AnimSequence': 3, 'AnimNotify_Sound': 29, 'AnimTree': 1, ...}
Showcase_Batmobiles_Jokerfied.upk             exports= 1136 animclasses={'AnimSet': 1, 'AnimSequence': 3, 'RAnimNotify_Clip': 1, ...}
CityZ_08_Cine_Ch1c_Batmobile_Intro.upk        exports= 1297 animclasses={'AnimSet': 5, 'AnimSequence': 8, 'AnimNotify_Sound': 2, ...}
Death_Joker_BatMobile.upk                     exports=  223 animclasses={'AnimSet': 2, 'AnimSequence': 4, ...}
Death_Thug_BatMobile.upk                      exports=  209 animclasses={'AnimSet': 2, 'AnimSequence': 4, ...}
Batmobile_Generator_1_SF.upk                  exports=  180 animclasses=-
Gad_RBatmobileRemoteBm_SF.upk                 exports=    5 animclasses=-
```

The six vehicle-mechanism sequences on the same skeleton:

```
Showcase_Batmobiles_Standard Batmobile_V2_Tank_Spread_Close_Showcase   frames=61  len=2.0
Showcase_Batmobiles_Standard Batmobile_V2_Tank_Spread_Open_Showcase    frames=72  len=2.366666555404663
Showcase_Batmobiles_Standard Showcase_Spin_And_Fire                    frames=150 len=4.9666666984558105
Showcase_Batmobiles_MK2      Batmobile_V2_Tank_Spread_Close_Showcase   frames=61  len=2.0
Showcase_Batmobiles_MK2      Batmobile_V2_Tank_Spread_Open_Showcase    frames=72  len=2.366666555404663
Showcase_Batmobiles_MK2      Showcase_Spin                             frames=130 len=4.300000190734863
Showcase_Batmobiles_Jokerfied Showcase_Jokerfied_BattleMode_Close      frames=61  len=2.0
Showcase_Batmobiles_Jokerfied Showcase_Jokerfied_BattleMode_Open       frames=73  len=2.4000000953674316
Showcase_Batmobiles_Jokerfied Showcase_Jokerfied_Spin_And_Fire         frames=151 len=5.0
```

The Showcase AnimSet is the same rig — `TrackBoneNames` count 172, `Cockpit_Mesh` and
`Weapons_Turret_Root` present — so these are not a different skeleton's data. The cine package
also carries a baked `Batmobile_V2_Pose_States` with `Batmobile_V2_Cockpit_Close/_Open/_Boost_Noise`.

**Verdict: BROKEN** for "253 is the Batmobile's animation universe"; the doc's own sentence
("Every `AnimSequence` in the four Batmobile packages") is honest, but the card's `In:`/`Done:`
and the G1X gate read 253/253 as complete. Six battle-mode/transform sequences, one of them a
different length from the playable version G1-12 uses for APP-6/MOD-2, were never opened. The
impact on G1-12 is limited (it names `Tank_Spread_Open_Game` explicitly) but the omission is
undisclosed.

## A2 — Offset 84 is `SequenceName`; 156/160/168 are `SequenceLength` / `NumFrames` / `RateScale`

**Test.** The cooked property stream carries no property names for these tags, so the labels are
positional. Print every tag at those offsets for all 253 sequences:

```
(84,  'NameProperty',  None) 253
(156, 'FloatProperty', None) 253
(160, 'IntProperty',   None) 253
(168, 'FloatProperty', None) 253
sequences with no NameProperty at offset 84: 0
```

Three checks support the mapping without a name:

```
identity (frames-1)/length == rate_scale violations: 0  (253/253)
psa_frames vs num_frames mismatches: 0
psa_length vs length mismatches: 0
export_name values: Counter({'AnimSequence': 253})
```

`psa_frames` and `psa_length` come from a third-party decoder (umodel's PSA header), so 160 =
frames and 156 = length are cross-checked against code that did not read this record. 168 agrees
with `(frames-1)/length` on all 253.

**Verdict: WEAK.** The values are right to the limit of the evidence; the *provenance label* is
not "decoded". No tag carries `SequenceName` / `SequenceLength` / `NumFrames` / `RateScale` —
the names in the doc and in `inputs.name_rule` are an inference from offset + arithmetic + PSA
agreement, which under R4 is `derived`, not `decoded`. The `(frames-1)/rate == length` identity
is a consistency check, not an independent one (satisfying it is how UE3 serialises these three
fields); the genuine cross-check is the PSA comparison.

## A3 — "PSA `ANIMINFO` is sorted by name", and duplicate rows are assigned in name order

**Test 1 — is ANIMINFO sorted?**

```
Playable_Batmobile_SF/BM_Batmobile_Chassis.psa        rows=5   sorted_exact=False sorted_lower=False
Playable_Batmobile_SF/Batmobile_V2_Pose_States.psa    rows=32  sorted_exact=False sorted_lower=False
Playable_BatmobileJoker_SF/Camera.psa                 rows=70  sorted_exact=False sorted_lower=False
Playable_BatmobileJoker_SF/Phase2_JK.psa              rows=14  sorted_exact=False sorted_lower=False
Playable_BatmobileJoker_SF/Phase2_JK_FACE.psa         rows=3   sorted_exact=True  sorted_lower=True
```

12 of 13 PSAs are not sorted, and not merely case-insensitively unsorted.

**Test 2 — what order are they in?** Compare each PSA's row order with the AnimSet's decoded
`Sequences` array (an `ArrayProperty` of `ObjectNCRProperty` refs), with names truncated to 63
characters:

```
Playable_Batmobile_SF        BM_Batmobile_Chassis     seqs=5   psa=5   order(animset)==psa: True
Playable_Batmobile_SF        Batmobile_V2_Pose_States seqs=32 psa=32  order(animset)==psa: True
Playable_BatmobileMK2_SF     Batmobile_V2_Pose_States seqs=32 psa=32  order(animset)==psa: True
Playable_BatmobileJoker_SF   Phase2_JK                seqs=14  psa=14  order(animset)==psa: True
Playable_BatmobileJoker_SF   Phase2_TG                seqs=14  psa=14  order(animset)==psa: True
Playable_BatmobileJoker_SF   Batwing_Rescue           seqs=4   psa=4   order(animset)==psa: True
Playable_BatmobileJoker_SF   Camera                   seqs=70  psa=70  order(animset)==psa: False
     row 43 animset=Disarm_Switch_Player              psa=Disarm_Switch_Player_180
Playable_BatmobileJoker_SF   Phase2_JK_FACE           seqs=3   psa=3   order(animset)==psa: False
     row 1/2 both truncate to ..._2Face_Fin
```

The Camera "difference" is only umodel appending `_180` to the 301-frame row; it sits at the
AnimSet's row 43 in both (`animset row 43 export 346 ('Disarm_Switch_Player', 301)`). So the rule
is: **PSA row order = the AnimSet's `Sequences` order**, in 12 sets, with zero sets contradicting
it.

**Test 3 — what does that do to the two 2007-frame rows?** The AnimSet refs are
`[426 Intro 1493, 425 Finale_Ver01 2007, 427 Finale 2007]`; PSA rows are `[Intro 1493, 2007,
2007]`, so row 1 = `Finale_Ver01` and row 2 = `Finale`. The record assigns the opposite
(`Finale` → `psa_index` 1, `Finale_Ver01` → 2), and the two rows are different animations:

```
row1 len 9184032 row2 len 9184032 identical: False
differing 32-byte keys between the two 2007-frame rows: 74389 of 287001
first differing bone: FcFX_Jaw frame 0
```

**Verdict: BROKEN.** The stated method is false and the swap it hides is real. Blast radius is
confined to two Joker face animations (not vehicle mechanisms, not used by G1-12 or T-12), and
the `Disarm_Switch_Player` pair is safe (301 vs 284 frames disambiguates it), but the record
mis-maps two sequences' keyframes.

## A4 — `*Shell*` marks the transformation shell

**Test.** List every `transformation` sequence whose evidence is a `_Shell_` bone, and look at
the cannon bones in the same sequences:

```
transformation via *_Shell_* bones: 8 ['Batmobile_V2_Cannon_Reload_Left', 'Batmobile_V2_Cannon_Reload_Right']
transformation via >=3 mechanisms: 24
```

```
Batmobile_V2_Cannon_Reload_Left   mech=transformation frames=15 len=0.466667 active=56 moved=14
    Batmobile_L_Shell_Tween_001    transformation  14.651 cm  77.500 deg
    Batmobile_L_Shell_008          transformation   8.102 cm  40.002 deg
    Batmobile_L_Shell_Chamber      transformation   8.618 cm   0.000 deg
    mechanisms: [('transformation', 14)]
Batmobile_V2_Cannon_Reload_Right  mech=transformation frames=15 len=0.466667 active=57 moved=14
    Batmobile_R_Shell_Tween_001    transformation  14.652 cm  79.750 deg
    mechanisms: [('transformation', 14)]
```

`Batmobile_Rig_Weapons_Heavy_Cannon_*` and `Heavy_Shells` are in the same sequences and show
0 moved bones; the record itself files `Heavy_Shells` under `cannon` (`ANIMATIONS.md` §3) while
`_Shell_` is the transformation signature.

**Verdict: BROKEN.** This is the R5 shape applied to bones — a name that sounds like the
behaviour. `mechanism_counts.transformation = 32` contains 8 false positives; the real count is
24. The card's Done line still passes (253 mechanisms), so nothing flagged it.

## A5 — The mechanism class is behaviour, so `transformation` means pursuit↔battle

**Test.** Inspect the non-shell `transformation` rows and the class's printed rule.

```
Batmobile_V2_Bat_Tracker  mech=transformation frames=37 len=1.2 active=58 moved=57
    Batmobile_Chassis_R_REAR_WHEEL_ARCH   other  60.462 cm 28.347 deg
    Batmobile_Rig_Weapons_Trans           transformation  57.506 cm
    Batmobile_Rig_Weapons_Heavy_Shells    cannon 57.182 cm
    mechanisms: [('canopy', 4), ('cannon', 1), ('missile bays', 6), ('transformation', 4), ('wheels/strafe', 4), ('suspension', 12), ('other', 26)]
Batmobile_V2_Fans_Spin    mech=wheels/strafe  active=5 moved=4   Wheel_*_Fan 180.0 deg
```

`ANIMATIONS.md` §3 lists "tracker" as an example of `other`, yet `Bat_Tracker` is
`transformation` (the ≥3-mechanism rule fires: canopy + cannon + missile bays). `Fans_Spin` is
classed `wheels/strafe` from `Wheel_*_Fan` bones, i.e. wheel-hub fans are read as wheels.

**Verdict: WEAK.** The rule as printed does produce these classes, and "transformation" is
defined in the doc as "three or more strong weapon/body mechanisms", not as "the battle-mode
reconfiguration the game plays". A consumer reading APP-6/MOD-2 off this class would be misled:
`Bat_Tracker` deploys a tracker device, it does not reconfigure the car. The doc's own example
list contradicts the row, which is the visible symptom.

## A6 — `--check` passing proves the card's Done criteria

**Test.** Read `check()` (`grab_anims.py` 1273–1290):

```
bad = 0
for path, text in ((OUT_JSON, json_text(doc)), (OUT_MD, render_md(doc))):
    ... if old == text: print("ok %s"); continue
    bad += 1
...
if bad: print("FAIL: animation record is stale"); return 1
present = 0 ... print("PASS: ... %d/%d named ...")
if present != len(doc["sets"]): print("WARN: keyframe files are missing")
return 0
```

The counts on the PASS line are printed from the fresh derivation, never compared to 253 or
asserted. The 13 keyframe files are checked for existence only; a corrupted keyframe passes.

**Verdict: WEAK.** The check is a staleness check (strong: byte-for-byte against a full
re-derivation from the four `.upk`s and 13 PSAs), not a Done-criteria check. "0 hand-typed
values" and "253/253" survive only because an operator reads the line. This matters because
`--check` is the card's only gate and G1-12 consumes the keyframe files it does not validate.

## A7 — The PSAs are a complete, faithful export, and `RemoveTracks` removed only constant tracks

**Test 1 — does the script make the PSAs?** The doc says "`--write` exports one PSA per AnimSet
with umodel" (`ANIMATIONS.md` §9). The script has no `subprocess` import and never invokes
umodel:

```
$ grep -n "subprocess" Tools/scripts/grab_anims.py
(no output)
```

**Test 2 — can the removal filter be cross-checked?** The same sequences are exported in four
packages with four independent configs; if the removals were hand-picked they would drift:

```
Playable_Batmobile_SF vs Playable_BatmobileMK2_SF      Batmobile_V2_Pose_States  sequences 32/32, differing 0
Playable_Batmobile_SF vs Playable_BatmobileFunhouse_SF Batmobile_V2_Pose_States  sequences 32/32, differing 0
Playable_Batmobile_SF vs Playable_BatmobileJoker_SF    Batmobile_V2_Pose_States  sequences 32/32, differing 0
Playable_Batmobile_SF vs Playable_BatmobileMK2_SF      BM_Batmobile_Chassis      sequences 5/5,   differing 0
```

**Test 3 — does a filter ever drop the mechanism it is supposed to show?** Two sets animate the
same mechanism with different configs and agree on what moves:

```
Cockpit_Open (14 frames, 23 active, 2 moved) vs Batmobile_V2_Cockpit_Open (10 frames, 3 active, 2 moved)
  A mechanisms: [('canopy', 2, 2), ('wheels/strafe', 13, 0), ('suspension', 5, 0), ('other', 3, 0)]
  B mechanisms: [('canopy', 2, 2), ('other', 1, 0)]
```

**Verdict: WEAK.** The input is unreproducible from the repo: neither the umodel command nor the
origin of the `[RemoveTracks]` choices is recorded in `MODLOG.md` or the scripts (the MODLOG's
revert note points at "the two README rows", and `grep -c ANIMATIONS
Research/BatmobileGrab/README.md` returns `0`). The evidence available says the filter behaves:
identical across four exports, and the canopy, turret, cannon, Vulcan, missile-bay and flap
sequences all retain their expected movers. But "a removed track is constant" is an assumption
about an unaudited input, not a checked fact.

## A8 — PSA is centimetres and `(x,y,z,w)` local transforms in the PSK hierarchy

**Test.** Compose PSA frame 0 of `Batmobile_V2_Idle` (its only animated bone is
`Batmobile_Bone_Chair_Rot_001`) through the skeleton from `BONES.json` using the PSK convention
(`q_world = q_child * q_parent`, parent's inverse rotation on the local offset), then compare the
world pivots and the overall extent:

```
Batmobile_V2_Idle     pos_tracks= 1 rot_tracks= 1 | bone world vs bind: max 12.06 cm mean 0.27
Batmobile_V2_Tank_Idle pos_tracks=45 rot_tracks=49 | bone world vs bind: max 141.39 cm mean 49.88 | PSA bbox cm x=645.4 y=435.3 z=258.1
BONES bind pivot bbox cm: [630.  323.3 192.2]
```

The single translated bone lands at `[-159.3, 0.0, 104.3] cm` against a bind local of
`[-157.46, 0.0, 112.03] cm` — the same pose to a few centimetres, which is only possible if the
PSA number is centimetres and local. `Tank_Idle` (battle-mode idle) differs by up to 141 cm and
grows the extent to 645 × 435 × 258 cm, i.e. the composed pose is a coherent taller/wider car,
not a 100× or 1/100 scaled one. Independently, G1-12 skins the same keyframes and gets a pursuit
bbox of `3.495 × 2.341 × 7.026 m` (`POSES.json`), which is the DIM-1 car.

**Verdict: HOLDS.** Units, quaternion component order and hierarchy convention survive a
from-scratch rebuild against a different record (G1-11) and a different consumer (G1-12).

## A9 — `frame_times_s = i / PSA rate` is the animation's time base

**Test.** Compare the PSA rate with the sequence's own `RateScale` and its length:

```
rate_scale values: Counter({30.0: 247, 29.999998: 6})
psa_rate values: min 30.015 max 60.000
identity (frames-1)/length == rate_scale violations: 0
Batmobile_V2_Spin: frames 138, length 4.566667, rate_scale 30.0, psa_rate 30.218979
```

The PSA rate is `frames / duration` (138/4.566667 = 30.219), i.e. umodel's derived value, not the
cooked rate. For `Batmobile_V2_Spin` the last frame is written at `137 / 30.218979 = 4.5336 s`
while the sequence is 4.566667 s long and the frame step is `1/30`. For the 2-frame idles the PSA
rate is 60, so:

```
Batmobile_V2_Idle: frames 2, length 0.033333, psa_rate 60.0
  recorded frame_times_s: [0.0, 0.016667]      true frame times: [0.0, 0.033333]
```

Two consumers use the field:

```
$ grep -rn "frame_times_s" Tools/scripts
Tools/scripts/grab_poses.py:316:  time_s = seq["frame_times_s"][frame]
Tools/scripts/t12_parts.py:272:    times = seq.get("frame_times_s") or []
```

`t12_parts.py` reports `rate max |delta angle| / delta time between adjacent key frames, deg/s`,
so every deg/s it publishes is scaled by `rate/frames` — 0.7 % for a 138-frame sequence, 50 % for
a 61-frame one (30.5 vs 30), 100 % for a 2-frame one.

**Verdict: BROKEN** as a time base. The field is honest about its formula but the formula is not
`i / RateScale`; the error is bounded for long sequences (≤0.7 %) and doubles for the short idles,
and it propagates into G1-12's `time_s` labels and T-12's deg/s numbers.

## A10 — `AnimNotify_Sound → AkEvent` is a usable sound binding

**Test.** Count resolution and cross-check the event names against the audio record.

```
sound notifies: 204 local refs: 203
sound target classes: {'AkEvent'}
sound without event name: 0
unique sound events: 39
notify AkEvent names resolving into AUDIO_MAP (outer,name): 39 / 39
unresolved: []
```

**Verdict: HOLDS.** 203/204 point at an `AkEvent` object in the same package; the 39 distinct
names all exist in `AUDIO_MAP.json` as `Ww_BML_Batmobile.<event>`, so G1-15 can join on them.
The one unresolved notify is documented in the record and in §10.

## A11 — 309 notifies in 95 sequences, every time inside its sequence

**Test.** Recompute from `ANIMATIONS.json`:

```
notifies: 309   sequences with notifies 95
notify times beyond length: 0
notify with time_s None: 0
notify with class None: 0
notify classes: {'AnimNotify_Sound': 204, 'RAnimNotify_Script': 35, 'RAnimNotify_Footstep': 16, ... 'AnimNotify_ClothingMaxDistanceScale': 1}
script notifies: 35 without script name: 0
```

`best_walk` reaches the end of every sequence export rather than stopping early, so the counts
are not a parse truncation:

```
best_walk stop reasons for 253 AnimSequence: {'end': 253}
min/mean/max fraction of export consumed: 0.000 / 0.161 / 0.928
```

**Verdict: HOLDS.** The counts, the class split and the in-range property reproduce. Nothing in
`check()` asserts the range property, so the statement is the author's verification rather than a
gated invariant (A6), but it is true.

## A12 — The `bone` column of a notify row is a bone

**Test.** Rows of classes other than `AnimNotify_Sound` / `RAnimNotify_Script`:

```
other-class notifies: 70 Counter({'RAnimNotify_Footstep': 16, 'RAnimNotify_DialogueTrigger': 15, 'RAnimNotify_Clip': 11, 'RAnimNotify_ChangeCape': 6, 'RAnimNotify_MeetingPoint': 6, 'AnimNotify_Kismet': 5, ...})
other-class rows with a 'bone' field: 5 [('AnimNotify_Kismet', 'JokerExitBmobStart'), ('AnimNotify_Kismet', 'JokerExitBmob'), ('AnimNotify_Kismet', 'JokerExitBmob'), ('AnimNotify_Kismet', 'JokerExitBmobRoofStart'), ('AnimNotify_Kismet', 'JokerExitBmob')]
```

`notify_record` fills `bone` from *any* `NameProperty` for non-sound classes, so five Kismet
events are printed in a column headed `bone`.

**Verdict: WEAK** (label). The payload is not lost — the Kismet event name is useful — but the
field asserts a bone the payload does not establish (R4).

## A13 — "The three AnimTrees … do not own sequences; `Batmobile_Skel_Ctrl_Door` has no sequence"

**Test.** Read the door tree and its node, and the Batwing tree's node:

```
tree export 244 AnimTree Batmobile_V2_Mesh.Batmobile_Skel_Ctrl_Door
tags: [('BoolProperty',...), ('ArrayProperty','SkelControlLists',3), ('ArrayProperty','AnimTickArray',2), ('ArrayProperty','Children',1), ('FloatProperty',...)]
refs on AnimTickArray [(244, 'Batmobile_V2_Mesh.Batmobile_Skel_Ctrl_Door', 'AnimTree'), (158, 'Batmobile_Skel_Ctrl_Door.AnimNodeSequence', 'AnimNodeSequence')]
items on Children [[{... NameProperty 'Child' ...}, {... ref 'Batmobile_Skel_Ctrl_Door.AnimNodeSequence' ...}, {...FloatProperty...}]]

export 158 AnimNodeSequence ... size 46   stop: eof end 44 of 46
    {'type': 'IntProperty', 'offset': 144, 'value': 1}
    {'type': 'FloatProperty', 'offset': 152, 'value': 1.0}
    {'type': 'ArrayProperty', 'offset': 156, 'name': 'ParentNodes', 'count': 1, ...}
Batwing node 275 AnimNodeSequence Batwing_Vehicle_AnimTree.AnimNodeSequence
    {'type': 'NameProperty', 'offset': 280, 'value': 'Batwing_Rescue_01'}
```

The door node carries no `AnimSeqName` tag at offset 280, but the export is a 46-byte stripped
default, and cooked packages drop default-valued properties, so "no tag" is not "no sequence".
The sentence also contradicts itself (the same bullet says the Batwing tree points at a sequence).

**Verdict: WEAK.** The honest statement is "the record carries no `AnimSeqName` property on the
door `AnimNodeSequence`". `Batmobile_Skel_Ctrl_Door` is the door *skeletal controller* tree the
card's MOD-4/ANI-8 path depends on, so the difference between "no sequence" and "no tag" matters
to a later reader.

## A14 — Every number in the generated MD is derived (R11)

**Test.** Locate the literals in `render_md` and check them against the data.

| printed value | where | recomputed |
|---|---|---|
| `37` "the same 37 sequence names exist in the base / MK2 / Funhouse / Joker car sets" | `ANIMATIONS.md` §8, script L1134 | correct: `names present in all four packages: 37` |
| `301-frame` / `284-frame` | L1333, script L1149 | correct: `SEQ 346 … frames 301`, `SEQ 400 … frames 284` |
| `2007-frame` | L1333, script L1152 | correct: `animset row 41 export 403 ('2Face_Finale', 2007)` |
| `63`-character truncation | L1333, script L1151 | correct (PSA names are 63 chars) |
| `names repeated across packages | 51` | L22, script L994 | **wrong label**: `dup names: 51 spanning >1 package: 37 confined to one package: 14` |

All of them are string literals in `render_md`, so `--check` regenerates them identically even if
they are wrong — which is how the 51 label survived.

**Verdict: WEAK.** Every table cell is derived; the prose is not, and one prose label
over-counts what it says (14 of the 51 are duplicate names *inside* `Playable_BatmobileJoker_SF`,
mostly `Camera`/`Phase2_JK` pairs). The script header's "No value is hand-typed" and the MD's
"nothing here is hand-listed" are stronger than the truth.

## A15 — No bone-scale animation is silently ignored

**Test.** `parse_psa` skips `SCALEKEYS`; check whether any exist with content.

```
Playable_Batmobile_SF/Batmobile_V2_Pose_States.psa  {'ANIMHEAD': (0,0), 'BONENAMES': (120,173), 'ANIMINFO': (168,32), 'ANIMKEYS': (32,236664), 'SCALEKEYS': (16,0)}
... all 13 PSAs: 'SCALEKEYS': (16, 0)
```

Every PSA carries the chunk with `count = 0`, and the key total reproduces
(`sum(num_raw_frames x bones) over 13 sets = 3147888`, equal to `psa_keys`).

**Verdict: HOLDS.** There is no scale curve in any of the 13 exports to lose.

## A16 — The four-package component is complete: no AnimSequence was skipped inside them

**Test.** Every `AnimSequence` row is owned by an `AnimSet`, every set's `Sequences` array was
read, and the per-set totals sum to the package total:

```
AnimSequence rows in four pkgs: 253
AnimSequence rows elsewhere: []          (objects.jsonl covers 15 packages)
counts: sets 13, sequences 253, named 253, with_bone_lists 253, with_mechanism 253
rows with class None: 7  (RHidePoint_Batmobile ×3, RBatmobileMissileLauncherJoker, RJokerMissileTarget, RPawnVillainThugJokerWarehouse, RSeqEvent_JokerBossEvent)
sets whose PSA bone order != TrackBoneNames: 0
sets with duplicate psa_index: []
```

**Verdict: HOLDS** within the four packages: 37+37+37+142 = 253, no sequence has a non-AnimSet
outer, none of the seven unresolved-class exports is an animation, and the bone-index join from
config index to `TrackBoneNames` is exact for 13/13 sets (which is what makes the `RemoveTracks`
lookup safe). This does not rescue A1: completeness is true *of the chosen universe*, and the
universe is narrow.

## A17 — Names are unique keys for a sequence

**Test.** Count instances per name:

```
total instances: 253 distinct names: 128
names with >1 instance: 51
names repeated within one package+set: 1 [(('Playable_BatmobileJoker_SF','Camera','Disarm_Switch_Player'), 2)]
```

**Verdict: HOLDS as a warning, in the record's favour.** The record keeps every instance and
publishes a duplicate table, so nothing is collapsed, but 253 sequences carry 128 names and a
consumer that keys on `name` alone will silently pick one of up to four. G1-12 and T-12 key on
`(package, set, name)`, which is what the record's own ordering supports.

---

## What this changes for the project

Nothing in the card needs a rebuild of the record to be *useful*: the per-bone tables and the
mechanism lists for canopy, turret, cannon, Vulcan, missile bays, flaps and transformation are
sound, and G1-12/T-12 consume them. The items worth fixing, smallest first:

1. `TRANSFORM_SIGNATURE` (`grab_anims.py` L83/L169): stop matching `Batmobile_L_Shell_*` /
   `Batmobile_R_Shell_*` ammunition as the transformation shell (8 rows, A4).
2. `ANIMATIONS.md` §8 + the FACE tie-break: replace "ANIMINFO is sorted by name" with "ANIMINFO
   follows the AnimSet `Sequences` order", and re-map the two 2007-frame rows (A3). The
   `grab_anims.py` group re-ordering at L295–313 should then be driven by the AnimSet refs, not
   by sorted names.
3. `frame_times_s`: use `i / RateScale` (or `i * (N-1) / (length * N)`); re-run `--write` and
   T-12's rates (A9).
4. Scope note in `ANIMATIONS.md` and the §12 row: the four Playable packages are not the
   Batmobile's only animation carrier (`Showcase_Batmobiles_*` 3+3+3, cine 8), and the showcase
   `Tank_Spread_Open_Showcase` is a 72-frame variant of the 61-frame playable transform (A1).
5. `check()`: assert `named == with_bone_lists == with_mechanism == sequences` and fail on a
   missing keyframe file instead of `WARN` (A6).
6. Labels: `bone` → `payload_name` for non-sound notifies (A12); "names repeated across packages"
   → "names occurring more than once" (A14); "the door node has no sequence" → "carries no
   `AnimSeqName` tag" (A13); `--write` does not export PSAs (A7).

No game file, save, dropzone or build was touched; the only write was this report.

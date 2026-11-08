# Assumption challenge — backlog card G1-23 (footage and file answers)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-23 card (§5, line 560),
its §12 row (line 1291), the MODLOG `G1-23 · Footage gaps closed — done` / `G1-23 · Footage and file
answers — revised` / `G1-23 rework — intended change` / `G1-23 rework — done` sections, the artifacts
`Research/BatmobileGrab/FOOTAGE.md` + `FOOTAGE.json`, the generator `Tools/scripts/grab_footage_gaps.py`,
and the data it reads (`WEAPONS.json`, `OFFSETS.json`, `MODES.json`, `objects.jsonl`, `DAMAGE_RULES.md`)
plus the five source clips at the path the card records. Nothing was launched, nothing under `D:/Games`
was touched, no capture was copied in, nothing was committed, and the only file written is this one.

Method: run the card's own gate; then attack each claim with the data on disk — in-memory
monkeypatches of the generator's own inputs (never `--write`, never a file edit), `ffprobe`/`ffmpeg`
reads of the clips piped to stdout (no frames extracted to disk), and direct reads of the JSON.
Where a claim could only be settled by looking at frames, that is stated as a limit instead of
being guessed.

Gate, as the card records it:

```
$ python Tools/scripts/grab_footage_gaps.py --check
OK: 72 rows, 2 file-resolved, 1 measured (3 samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1,
'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53, 'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1};
27/27 checks; md byte-identical                              EXIT=0
```

## VERDICT

**Two BROKEN, nine WEAK, six HOLDS.** The file-side half of the card is in good shape: the three
`InaccuracyVsTime` points are decoded (including the interpolation mode), the four
`HeatUpPerSecond` tags really do ship `0.0`, the 72-row arithmetic reproduces exactly, and the
"no tank objects / no footage in the workspace" claims are true *of the set that was searched*.

What does not hold is the one thing the card advertises as measured. The airborne window is not
read from the footage by the tool — the two boundaries per clip are **typed constants** in
`SOURCES`, snapped to the nearest presentation timestamp. Nothing in the gate can tell them from
invented numbers: rewriting all three windows to boundaries 1.9 s apart still yields **27/27** and
renders "1.898 s mean (1.901 / 1.882 / 1.911 s)". The MODLOG says the boundaries came from
contact sheets read at 15 fps, and those sheets are gone, so the numbers may well be right — but
the record cannot show it, and the checks that are supposed to prove it are tautologies.

Second: the "*across the cannon objects*" heat check verifies one field path, not four objects.
Mutating three of the four objects to `0.9` in memory leaves the gate green and the row printing
`0.0`.

| # | assumption | verdict |
|---|---|---|
| A1 | the five clips in `C:\Users\User\Videos\Captures` are Arkham Knight captures | **HOLDS** — the container `title` tag says so on all five |
| A2 | the clips show the Batmobile jumping, and the names describe the content | **WEAK** — game identity is machine-evidenced, content is filename-only; no frame is inspected anywhere in the record |
| A3 | the three air samples (1.251 / 1.183 / 1.200 s) are measurements of the footage | **BROKEN as verification** — boundaries are typed constants; fabricated windows pass 27/27 |
| A4 | "airborne window" is the observable for `AirControlTimeInAir` (R5) | **WEAK** — the gap was restated to a measurable the field does not name |
| A5 | the clips are VFR and the window holds "37–38 unique frames at a ~31 fps cadence" | **WEAK** — PTS method holds; the stated cadence is 28.5–30.2 fps and the "16.7/33 ms alternation" is not in the files |
| A6 | presentation timestamps are real time (no capture-time compression) | **HOLDS** — video and audio stream durations agree to ≤0.06 s on all five |
| A7 | `HeatUpPerSecond` = 0.0 "in 1 of 1 cannon objects" | **WEAK** — 4 objects carry it (all 0.0) and a 5th cannon archetype carries none; the count is a field-path count |
| A8 | the gate's heat check covers the fleet | **BROKEN as check** — one path, `sum(...) >= 1`; three mutated objects stay green |
| A9 | the `InaccuracyVsTime` points are decoded, not inferred, and the curve is linear | **HOLDS** — 4 float pairs + `CIM_Linear` per point, identical in all four archetypes |
| A10 | the curve's in-axis is seconds and its values add to `InaccuracyAngle` 0.1 | **WEAK** — both are inferences; only the numbers are decoded |
| A11 | no per-second heat is configured, the overheat path is still "wired" | **HOLDS as hedged** — the only heat members are the bar pair, the rate, the threshold and two resolvable AkEvents |
| A12 | `(LifeSpan|Lifetime)` matching 0 fields means no projectile carries a lifetime | **WEAK** — that is an absence of *overrides*; a CDO default would not be serialised |
| A13 | "0 tank weapon/shell objects in the grab" ⇒ the shells-to-kill number is out of reach | **WEAK** — true of 15 grabbed packages; the install holds 3,287, including the tank vehicle packages |
| A14 | `Health` = 1200 is the Batmobile's health | **WEAK** — 3 of 4 archetypes carry the tag; `JokersBatmobile` carries none at offset 1144 |
| A15 | no Arkham Knight footage inside the workspace | **HOLDS** — 1,818 `.mp4` (all 3ds Max tooltips) + 1 `.mkv`; no other video extension exists in the tree |
| A16 | the auxiliary checks prove what their names say (R4 duplicates, "md byte-identical", natives, "1 measured on five captures") | **WEAK** — substring heuristic, text-mode compare, and 3 of 5 clips, respectively |
| A17 | the counts and arithmetic in the row (72 = 5+61+1+5, reasons, 20/17, 1.212 mean, 0.068 spread) | **HOLDS** — every one reproduces |

Counts: 6 HOLDS, 9 WEAK, 2 BROKEN (one of them a check, one the headline number's provenance).

---

## A1 — the five clips are Arkham Knight footage. **HOLDS**

The whole card is worthless if the clips are something else (the first attempt at this card did
scan 1,818 3ds Max tooltip clips by mistake). The record's only check is "present at the recorded
path + 1920×1080 + nominal 60 fps", which says nothing about *which game*.

The container carries the answer:

```
$ ffprobe -show_entries stream=width,height,r_frame_rate:format=duration:format_tags … <each .mp4>
Batman™_ Arkham Knight Air steer down 2-5s.mp4      1920x1080 r=60/1       avg=28.469 frames=202 dur=7.153
   tags: creation_time 2026-10-26T08:55:57Z  title 'Batman™: Arkham Knight'
Batman™_ Arkham Knight Air steer right 3-6s.mp4     1920x1080 r=60/1       avg=30.250 frames=267 dur=8.882
   tags: title 'Batman™: Arkham Knight'
Batman™_ Arkham Knight Air steer up 2-5s.mp4        1920x1080 r=60000/1001 avg=29.862 frames=189 dur=6.388
   tags: title 'Batman™: Arkham Knight'
Batman™_ Arkham Knight Battlemode entry… .mp4       1920x1080 r=60/1       avg=27.410 frames=1096
Batman™_ Arkham Knight VulcanFire_10s-15s.mp4       1920x1080 r=60000/1001 avg=27.498 frames=1352
Just Cause 3 test-086.mp4                           1280x720  r=60000/1001 avg=30.094  title 'Just Cause 3'
Just Cause 3 test-087.mp4                           1280x720  r=60/1       avg=30.386  title 'Just Cause 3'
```

`title = Batman™: Arkham Knight` on all five is machine evidence the recorder wrote, and the
folder's two JC3 takes carry `title = Just Cause 3`, so the tag discriminates. This is stronger
evidence than the card itself cites, and it is not in the card — it should be.

## A2 — the clips show the Batmobile jumping, and the names describe the content. **WEAK**

A game title is not a subject. The record's evidence that a clip shows a ramp jump, a landing or
a steering input is the **filename** (`Air steer up 2-5s`), plus the roles in `SOURCES`
(`ramp jump, pitch up`). Under R5 a name is not a behaviour.

Test — does anything in the record or the tooling inspect a frame? `air_samples()` reads only
`s["air"]` (the tuple). `probe_frames()` reads only `pts_time`. `probe_stream()` reads geometry,
rate and duration. There is no frame decode, no contact sheet, no saved still: the MODLOG's
"contact sheets with burned-in PTS (`drawtext`)" are not on disk and `FOOTAGE.json` holds no
image reference.

A cheap independent probe (per-frame luma, read via stdout, nothing written) also finds no visual
event at either recorded boundary of the first clip:

```
$ ffmpeg -i <clip> -vf signalstats,metadata=print:file=- -f null -
 pts    YAVG   dYAVG
 3.172    59.7    +0.5
 3.204    60.5    +0.8      <- recorded "first air"
 3.242    61.6    +1.1
 …
 4.423    46.9    +0.3
 4.455    46.3    -0.6      <- recorded "first contact"
 4.492    46.1    -0.2
 4.526    48.3    +2.3
```

That is inconclusive by nature (leaving a ramp and landing need not change mean luma), so it does
not falsify the boundaries — it only shows that nothing on disk corroborates them. Verdict:
**WEAK**; the identification rests on the filename, which is exactly what R5 forbids as sole
evidence.

## A3 — the three air samples are measurements of the footage. **BROKEN as verification**

This is the card's single measured number, and §12 and G1X both quote it
("1.251/1.183/1.200 s … PTS-based because the clips are VFR"). The generator does this:

```python
SOURCES = [ {"file": "…Air steer up…", "kind": "air", "air": (3.200, 4.467)}, … ]
def air_samples():
    for s in SOURCES:
        pts = probe_frames(path)          # only timestamps
        t0, t1 = s["air"]                  # <-- the boundaries are typed
        i0 = nearest(pts, t0); i1 = nearest(pts, t1)
        air_time = pts[i1] - pts[i0]
```

So the "measurement" is two hand-typed timestamps per clip, snapped to the nearest frame. The
snapping is real arithmetic and reproducible (`4.4553 − 3.2039 = 1.2514`; mean `1.21153 → 1.212`;
spread `1.2514 − 1.1832 = 0.0682`) — but the boundaries themselves are inputs, not observations.

Test 1 — replace the three typed windows with invented ones (in memory only; `SOURCES` monkeypatched,
`build()` called normally):

```
DEMO B (invented boundaries 1.9 s apart):
   2.0031 3.9044 1.9013 snap 0.004
   0.5244 2.4066 1.8823 snap 0.024
   4.0007 5.9117 1.9110 snap 0.012

fabricated-boundary build: 27/27 pass; failures: []
fabricated row text: **measured: 1.898 s mean** across three ramp jumps (1.901 / 1.882 / 1.911 s),
                     56-59 unique frames each …
```

Test 2 — the check that is supposed to guard the boundaries is tautological. `SNAP_S = 0.05` while
the clips' frame spacing is 26–50 ms, so *any* typed time snaps inside tolerance:

```
every air sample snapped to a frame within 0.05 s | PASS | 0.004, 0.024, 0.012
```

The same holds for the other three air checks: "agreeing within 0.1 s" and "over a second" are
properties of whatever numbers were typed, and "three ramp jumps are measured" only counts three
entries in `SOURCES`. Every one of them passed on the fabricated build.

**Verdict: BROKEN as a verification** — the number is an unexplained constant dressed as a
measurement, the rework's F-6 fix (format the row *from* the samples) improved the rendering but
left the provenance untouched, and the card's `Done` criterion ("a measured value … frame count at
known fps") is not what `--check` verifies. It is not proven *wrong*: the MODLOG says the
boundaries came from contact sheets at 15 fps, which would be a legitimate manual measurement — but
that artifact is gone and no check can distinguish it from invention. A one-line fix exists and is
not taken: store the two frames' **image evidence** (e.g. a per-frame luma/edge signature around
each boundary, or an `ffmpeg` scene score) so the gate recomputes the boundary instead of trusting
it.

## A4 — the airborne window is the observable for `AirControlTimeInAir`. **WEAK (R5)**

The gap the row closes is F-6, and G1-21's gap is a *field value*: `AirControlTimeInAir`, plus
`AirControlInterpTime` and six torque factors, all "declared, not serialised". The row's gap text
was rewritten to "time airborne on a ramp/ledge jump (the observable for the air-control window)",
and it is marked **MEASURED**.

What 1.212 s actually is: the wall-clock duration between leaving a ramp and touching ground. What
`AirControlTimeInAir` names: the time air control is *active* (it could be 0.2 s of a 1.2 s
flight, or the whole flight, or a cap). Nothing decoded connects the two — the field has no value
anywhere in the grab, so its relation to air time is a guess from its name. That is the R5 pattern
the card itself warns about, one line after correctly refusing to do it for
`bUsedAirControlDuringJump`:

```
It does **not** measure steering authority … `bUsedAirControlDuringJump` is a member name,
not an observation (R5).
```

Credit where due: the doc *does* hedge the steering half, and the F-7/56–62 rows stay
`VALUE-NATIVE`. But the MEASURED row still converts an unanswered field into a closed row, and
§12 plus G1X read it as "the air-control window is the one measured observable (1.212 s mean)".
**WEAK**: a hedge in the body, an over-claim in the summary line.

## A5 — VFR, "unique frames", "~31 fps cadence". **WEAK**

The method (use PTS, not frame counts) is right, and the reason is real: `r_frame_rate` says 60 but
the average is 27–30 fps.

```
$ ffprobe -show_entries frame=pts_time …            (delta histogram, top entries)
Air steer down  202 frames span 7.079 mean_delta 0.0351   {0.033:78, 0.034:21, 0.027:11, 0.035:8, 0.031:8, 0.032:7, 0.017:6}
Air steer right 267 frames span 8.810 mean_delta 0.0331   {0.033:86, 0.034:31, 0.032:23, 0.035:19, 0.031:14, 0.036:11}
Air steer up    189 frames span 6.312 mean_delta 0.0335   {0.033:56, 0.035:15, 0.034:13, 0.031:12, 0.036:11, 0.032:10}
```

Two things follow:

1. The cadence is **28.5–30.2 fps** (means 0.0331–0.0351 s), not "~31 fps". Close enough not to
   matter, but it is a typed figure in the prose, not a computed one.
2. The MODLOG's stated VFR premise — *"the PTS deltas alternate ~16.7 ms and ~33 ms, and 37-38
   unique frames cover 1.2 s (a ~31 fps cadence)"* — is not what the files show: deltas cluster at
   33 ms with jitter, and 0.0167 s appears as a minority tail (6 of 201 in one clip). The clips
   look like a ~30 fps capture labelled 60, not 60 fps with half the frames duplicated.

"Unique frames" is defensible: no two consecutive frames have identical luma/chroma statistics in
any of the three air clips (`dup_pairs = 0`), and the window holds 37 distinct signatures for the
first clip. Verdict **WEAK**: right method, one wrong supporting detail, one typed rate.

## A6 — PTS is real time. **HOLDS**

If the recorder dropped frames and rewrote timestamps, PTS differences would not be seconds of
playback and every sample would be scaled wrong. Audio is an independent clock:

```
Air steer down   video 7.0955 s / audio 7.039979 s
Air steer right  video 8.8266 s / audio 8.831979 s
Air steer up     video 6.3291 s / audio 6.335979 s
Battlemode       video 39.9859 s / audio 39.978646 s
VulcanFire       video 49.1665 s / audio 49.151979 s
```

Agreement within 0.06 s on all five — no evidence of time compression or systematic dropouts.
(Note this is a different uncertainty from A3: it says the *clock* is sound, not that the
boundaries are.)

## A7 — `HeatUpPerSecond` = 0.0 "in 1 of 1 cannon objects". **WEAK**

The value is genuinely decoded — a `FloatProperty` tag carrying `0.0`, not a missing tag — and it
is the same in every object that has one:

```
objects carrying HeatUpPerSecond: 4
   Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2 [0.0]
   Playable_BatmobileJoker_SF.Batmobile_Cannon_V2   [0.0]
   Playable_BatmobileMK2_SF.Batmobile_Cannon_V2     [0.0]
   Playable_Batmobile_SF.Batmobile_Cannon_V2        [0.0]
cannon-class objects total: 5
cannon objects WITHOUT HeatUpPerSecond: ['Playable_BatmobileJoker_SF.Batmobile_JokerCannon_V2']
```

Two defects in the sentence, none in the value:

- **The count is a path count, not an object count.** The row prints `in %d of %d cannon objects`
  from `len(heat_zero), len(heat_paths)`, where `heat_paths` is the set of **bare field paths** —
  so it renders "1 of 1" while four objects carry the tag. The 10-26 MODLOG ("in all four cannon
  objects") was the more accurate sentence; the rework made it worse.
- **The fifth cannon archetype has no tag at all.** `Batmobile_JokerCannon_V2` carries no heat or
  inaccuracy member. Under G1-21's own rule (*"a missing tag is a CDO default, UNKNOWN — never 0"*,
  quoted in the §12 row for G1-21) its per-second heat is **UNKNOWN**, not 0.0. The doc's claim
  "no per-second heat is configured" therefore covers 4 of 5 cannon archetypes, and the record
  never says which.

## A8 — the gate's heat check guards the fleet. **BROKEN as a check**

```
heat == 0.0 and sum(1 for k, v in values.items()
                    if isinstance(k, str) and k.endswith("HeatUpPerSecond") and v == 0.0) >= 1
```

`values` maps a bare path to the **first** object's value (`out.setdefault(f["path"], …)`), so the
left side is one object, and `>= 1` is satisfied by that same bare key. Test: mutate three of the
four objects to `0.9` in memory, rebuild the helper and re-evaluate the predicate:

```
mutated 3 of 4 objects to 0.9: helper still reports heat = 0.0 | gate predicate passes: True
```

The check named "HeatUpPerSecond still ships 0.0 **across the cannon objects**" cannot see a
divergent value in three of them. Same shape as the review issue the rework fixed for the answered
table ("each quantity takes its first matched field") — the same bug survives in the heat path, the
`InaccuracyAngle` read (`values.get("RBatmobileCannon.InaccuracyAngle")`, one object) and the curve
read (`curves.get("Playable_Batmobile_SF.Batmobile_Cannon_V2")`, hard-coded to one key).

## A9 — the `InaccuracyVsTime` points are decoded and the curve is linear. **HOLDS**

This is the one place the doc inherited a genuine decode, and it is solid. Raw array items:

```
InaccuracyVsTime.Points | count 4 | stride 62 | decoded True
   item 0 [FloatProperty 0.0, FloatProperty 0.0, FloatProperty 0.0, FloatProperty 0.0, ByteProperty 'CIM_Linear']
   item 1 [FloatProperty 0.5, FloatProperty 0.0, …                 ByteProperty 'CIM_Linear']
   item 2 [FloatProperty 1.5, FloatProperty 1.5, …                 ByteProperty 'CIM_Linear']
   item 3 [FloatProperty 2.5, FloatProperty 3.0, …                 ByteProperty 'CIM_Linear']
```

Identical in all four cannon archetypes (Funhouse, Joker, MK2, base). The upgraded variant is
`0/1/3/5 s → 0/0/1.5/3.0`, also `CIM_Linear`. So "linear" is a decoded member, not an inference —
and the doc does not cite the `CIM_Linear` byte it rests on, which is a small lost opportunity
rather than an error. The pair extraction (`first two FloatProperty` per item) is correct for this
struct layout: the third and fourth floats are the arrive/leave tangents and are 0.0.

## A10 — the curve's in-axis is seconds and it adds to `InaccuracyAngle` 0.1. **WEAK**

Nothing in the cooked data labels the in-axis: the items are four bare floats plus an enum; the
struct is `FInterpCurveFloat`, which carries no unit. "s" comes from the member name
(`InaccuracyVsTime`) — reasonable, and consistent with `InaccuracyAngle` 0.1 sitting next to it —
but it is inferred.

"**on top of** `InaccuracyAngle` **0.1**" is a second inference: no field, comment or reference in
the grab says the curve is added to the base rather than replacing or scaling it. The MODLOG/FOOTAGE
prose states the combination as fact. Both should read "x-axis understood as seconds; combination
with the base angle inferred". Neither affects the values, which are decoded.

## A11 — no per-second heat is configured and the overheat path is "wired". **HOLDS as hedged**

Every heat-ish member in the 62 objects, by name search over 231 distinct paths:

```
-- heat (5)
   HeatBarSize                            objects 4  [0.125, 0.03]
   HeatBarStart                           objects 4  [0.79, 0.68]
   RBatmobileCannon.ChainGunOverheatSound objects 4  -> Engine.Play_Minigun_Overheat   (AkEvent)
   RBatmobileCannon.HeatUpPerSecond       objects 4  0.0
   RBatmobileCannon.OverheatOffValue      objects 4  0.25
-- cool (2)
   RBatmobileCannon.ChainGunCooledSound   objects 4  -> Engine.Play_Minigun_Cooled     (AkEvent)
```

There is no per-shot heat member, and the sound/threshold pair genuinely resolves (not a dangling
import), so "a path is wired" is fair. The doc's conclusion — *whether a per-shot add exists in
native code is not excluded*, mechanism UNKNOWN — is the correct reading, and it is the one claim
in the heat section that survives a strict R5 test because it refuses to name a behaviour from a
member.

## A12 — "no projectile carries a lifetime" from 0 pattern matches. **WEAK**

```
-- life (0 hits over 231 paths)      -- span (0 hits)
field_index: projectile lifetime  (LifeSpan|Lifetime)  matches 0
```

The absence is real *as an absence of tags*. But a cooked archetype only serialises values that
differ from its class default, so "no tag" means "not overridden here", not "no such value". The
card's own source is careful — `WEAPONS.md` §4 says *"no projectile carries `LifeSpan`/`Lifetime`.
Class defaults are not claimed."* — while FOOTAGE.md's row compresses it to "no projectile carries
a lifetime", which a reader takes as a value of zero/absent at runtime. The status (`UNKNOWN`,
`NOT-IN-CLIP`) is right either way, so this is wording, not a wrong conclusion.

## A13 — "0 tank weapon/shell objects in the grab" ⇒ the number is not obtainable. **WEAK**

The predicate reproduces exactly:

```
tank filter -> 0 []                      # 'tank' in name AND class Proj/Weapon or name has Shell/Cannon
loose (name has shell|tank) -> 51        # all AkEvents, Package refs, particles, ChainGunShells0
```

But the search space is 15 packages, not the game:

```
grab.json: "game": "E:\\Games\\Batman - Arkham Knight\\BmGame\\CookedPCConsole",
           "packages": 15 × Playable_Batmobile*
objects.jsonl: distinct packages: 15, objects 20128
$ ls "E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole" | wc -l
3287
$ ls … | grep -i tank
Showcase_Vehicles_LightTank.upk / _HeavyTank / _CommanderTank / _LightTankArmour / _LightTankMissile …
```

One of those packages, read with the project's own reader (`upk_read.Package`, names only, nothing
extracted): `Showcase_Vehicles_LightTank.upk` — 570 exports, **277** whose path names tank/cannon/
projectile/turret (`GCPD_Tank_HeavyMissileMuzzleFlash_P`, `Baked_TANK_Lite_Tank_GUN_V3_Anims`, …).
So tank *material* is in the install and outside the grab. The row's own sentence is correctly
scoped ("the grab holds 0 … the incoming damage lives in the enemy packages"), and F-5 stays
`NOT-IN-CLIP`, so the conclusion is intact — but the claim "a number these files do not carry" is
true only because "these files" is a 15-file whitelist. That is the "no carrier exists that only
searched some places" pattern, and it should say so explicitly: *the shells-to-kill number is not
in the Batmobile packages; nobody has opened the faction vehicle packages yet.*

## A14 — `Health` = 1200 is the Batmobile's health. **WEAK**

```
RVehicleBatmobile Health IntProperty count 3 [1200, 1200, 1200]
```

and at offset 1144 in the archetype objects:

```
Playable_BatmobileFunhouse_SF  BatmobileFunhouse  -> [(None,'IntProperty',1200)]
Playable_BatmobileJoker_SF     JokersBatmobile    -> []
Playable_BatmobileMK2_SF       Batmobile_MK2      -> [(None,'IntProperty',1200)]
Playable_Batmobile_SF          Batmobile          -> [(None,'IntProperty',1200)]
```

Three of four Batmobiles override the tag; the Joker one does not, so its health is the unshipped
`BsmScript` CDO default (UNKNOWN by the project's own rule, not 1200). The row text is honest
("3 packages"), but the gate's name — "Health still reads 1200 in **every** OFFSETS.json package" —
is not, and F-5's arithmetic (1200 / shell damage) silently assumes the played vehicle is a base or
MK2 variant. Also worth noting for provenance: the tag is **unnamed** in the cooked data; "Health"
is the SDK dump's name for offset 1144 (the same name-by-offset evidence class the G1-21 challenge
checked and found sound), not a decoded name.

## A15 — no Arkham Knight footage inside the workspace. **HOLDS**

Independent walk of the whole tree (the gate's own scan, re-derived):

```
{'.gif': 895, '.mp4': 1818, '.mkv': 1}     # other video extensions (.mpg/.mpeg/.wmv/.flv/.ts/.m2ts/.bik): 0
outside the scan's extension list: 895 .gif  (all under "Autodesk 3ds Max")
```

1,818 `.mp4` + 1 `.mkv` = the 1,819 files the check accounts for (1,818 tooltip clips + the
frame-verified JC3 camera take); 0 candidates. The scope limit is the extension list (`.mp4 .webm
.mkv .avi .m4v .mov`), which misses `.gif`/`.bik`; no such gameplay recording exists here, so the
claim stands as written. This also confirms R10's "captures stay outside the repo" half.

## A16 — the auxiliary checks prove what their names say. **WEAK**

Three small ones, all low-stakes, all fixable in a line:

1. **"no footage-measured row duplicates a quantity the files answer (R4)"** is a substring test
   between the row's gap text and 20 short quantity names:

   ```
   gap as shipped: time airborne on a ramp/ledge jump (…)   -> duplicate detected: False
   "inaccuracy-vs-heat"                     -> False
   "spread growth as the Vulcan heats"      -> False     (duplicates F-2; not flagged)
   "damage"                                 -> True
   ```

   It catches literal word reuse only. `inaccuracy-vs-heat` is not even in the answered set (it has
   0 matches), so the obvious duplicate would slip through.

2. **"md byte-identical"** is a text-mode comparison:

   ```
   md == disk (text mode, as --check does): True
   disk CRLF count: 288        # the render is LF-only
   ```

   True in substance, not byte-for-byte; a line-ending change would not be caught. (The JSON
   comparison is a real equality test, so tampering with `FOOTAGE.json` is caught — the rework's
   tamper test was right about that half.)

3. **§12's "1 measured on five captures"** and §1's "All five are variable-framerate" read as if
   five clips were measured; three are, and the Vulcan and Battlemode clips contribute no sample
   (correctly so — one is used only as corroboration, the other not at all).

The natives check is the exception and does hold: `DAMAGE_RULES.md` has exactly 5 `**native**`
table rows (`ShouldRadialDamageHit`, `CanBatmobileDoImpactDamage`, `SetDamageLevel`,
`SetArmouredMode`, `GetDamageMod`); F-4 names one, `NATIVE_UNTRACED` the other four, and the gate's
regex picks exactly those five (it does not pick up the `E_native_parm_refs_own_properties` check
row, which lacks the bold).

## A17 — the counts and arithmetic. **HOLDS**

Everything numeric in the §12 row reproduces from the artifacts:

```
rows 72 = 5 card quantities + 61 MODES fields + 1 measured + 5 undocumented units
reasons: FILE-VALUE 2, MEASURED 1, NOT-IN-CLIP 2, VALUE-NATIVE 53, UNDOCUMENTED 5,
         WRONG-SCOPE 8, NATIVE 1                                   (sum 72)
answered: 20 (17 decoded, 3 field-present with contents this walker does not decode)
air: 1.2514 / 1.1832 / 1.2000  -> mean 1.21153 (printed 1.212), spread 0.0682
snap errors 0.0117 / 0.0151 / 0.0056  (all < 0.05)
```

`WEAPONS.json` carries 62 objects, 4 of them `RBatmobileCannon` V2 archetypes plus the Joker cannon;
`MODES.json` reports 61 not-serialised fields and 5 undocumented units; `DAMAGE_RULES.md` has 5
natives. The self-consistency of the record is not the problem — the provenance of one input is.

---

## What would close the two BROKEN items (smallest version)

1. **A3** — make the boundary recomputable instead of typed: store the frame indices *and* one
   per-frame signal the gate can re-derive without a human (e.g. the `signalstats` luma/edge trace
   around the boundary, or `select=gt(scene,…)` scores) and check that the recorded boundary is the
   onset of that signal; or accept the measurement as `assumed` under R4 and mark the row
   `UNKNOWN / measured-not-reproducible` instead of `MEASURED`.
2. **A8 / A7** — read heat, angle and curve values **per object** (4 archetypes + the Joker
   archetype with no tag → `UNKNOWN`), require all objects present, and print the object count, not
   the path count.

Neither change touches a value that is currently correct; both change what the record is entitled
to claim.

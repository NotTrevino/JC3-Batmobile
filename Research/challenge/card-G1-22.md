# Assumption challenge — G1-22 · Native remainder check for feature relevance

**Scope.** Finished card `GRAB_BACKLOG.md:552-557` (S, deps G1-08), its §12 row
(`GRAB_BACKLOG.md:1290`), MODLOG §"G1-22 · Native remainder relevance — done" (line 8814) and
§"G1-22 rework — done" (line 15987), and the outputs those name:
`Research/BatmobileGrab/NATIVE_RELEVANCE.md`, `NATIVE_RELEVANCE.json`,
`Tools/scripts/grab_native_relevance.py`. Rules read first: `GRAB_BACKLOG.md` §0.5 R1–R14.

**Method.** Every assumption below was attacked with the data on disk only. Commands were run
with `python -` reading from stdin (no helper scripts written). The BmAK install at
`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole` was **read** (the card's own generator
reads it; §0.6/R10 put game data outside the repo). No game was launched, nothing was written
into `D:\Games`, nothing was committed, no shared module was edited.

**Change record (AGENTS.md).** The only file written is this one,
`Research/challenge/card-G1-22.md`. It is the correct file because the task names it and it is
the project's existing home for challenge reports (`Research/challenge/card-G1-1x.md`).
Revert: delete this file; nothing else is touched.

**The card's own check, re-run (read-only):**

```
$ python Tools/scripts/grab_native_relevance.py --check
OK: 140/140 classified (96 irrelevant, 44 relevant); 13/13 checks; md: PASS
EXIT=0
```

So the arithmetic machinery is intact. Everything below is about **what the numbers are taken to
mean**, not about whether the generator reproduces them.

---

## VERDICT

| # | assumption | verdict |
|---|---|---|
| A1 | 925 untagged / 140 over 8 B is the right population | **HOLDS** |
| A2 | every number is script-derived and the `--check` comparison is real | **HOLDS** |
| A3 | the rows still describe the shipped packages (no stale grab) | **HOLDS** |
| A4 | `*Property` is irrelevant *because the value lives on the archetype* | **BROKEN** |
| A5 | `FaceFXAnimSet` is "counted by the audio cards" | **BROKEN** |
| A6 | the 20 `Function` exports are undecoded bytecode, "not decoded by … any G1 card" | **BROKEN** |
| A7 | the 7 parent classes are name-inferred, not decoded | **HOLDS** (understated — they are corroborated structurally) |
| A8 | the 7 class payloads are "empty list + parent class" and fully explained | **WEAK** — 1,460 B of structured tail is unexplained |
| A9 | component tails are "a header, not a value" | **WEAK** — true of the 8-byte FName only; 7 floats sit after it |
| A10 | the 17 component tails are the object's own name | **HOLDS** |
| A11 | 96 "native references across 29 rows … not values" | **WEAK** — 3 of the 96 are name indices |
| A12 | the relevant classes' values live on `Default__*` rows the grab decodes | **BROKEN** |
| A13 | the families G1-08/14/21 list are "already in `OFFSETS.json` / `CHAIN.json`" | **WEAK** — unenumerated; 4 of 5 class families absent |
| A14 | "none of the names appears in `WEAPONS.md`" | **HOLDS** literally, **WEAK** as evidence |
| A15 | byte sizes / the >8 B cut / the 0.01–10⁴ float window are safe conventions | **HOLDS** |
| A16 | six-byte rows are outside the rule, and "anything no rule covers is UNCLASSIFIED" | **WEAK** — 8 six-byte rows of a *relevant* class are never classified |
| A17 | the 2 `State` rows are "script state header … not a value" | **WEAK** — name-based; 59/71 B payloads, no decode attempted |

**One-line summary.** The counts are honest and reproducible, and the two "nothing here was
hidden" statements are correctly hedged. What does not hold is the *semantic* half: the card
declares one third of its relevant set (20 `Function` exports, 5,562 B) undecodable while a
sibling G1 tool (`Tools/scripts/bmak_damage.py`, G1-14) decodes exactly that structure and reads
literals out of five of them on the spot; it dismisses 96 property declarations with a reason
("the value lives on the archetype") that is true for 2 of 10 class-level cases and false by
construction for 71 of 81; it credits the audio cards with a coverage they do not have; and it
counts three name indices as object references.

---

## A1 · "925 untagged; 140 larger than 8 B" — the population

**Card / doc.** Card: "`objects.jsonl` (925 untagged; 140 larger than 8 B)". Doc: "untagged
exports in the grab - objects with no property tag, not objects the reader failed on".

**Assumption (silent).** `tag_count == 0` in `objects.jsonl` is a fact about the object, and the
925/140 boundary is where tag streams stop.

**Test.** Re-derived the population from `objects.jsonl` and checked every one of the 140 against
the live packages (name, size, class, payload length):

```
rows 20128
untagged 925
untagged sizes>8 140
140 rows checked against live upk: mismatches = 0
class mismatches: 0
```

All 140 stop at `end` with `parsed = 0`, i.e. the tag walker reads a zero 16-bit type-id at byte
0 of every one. That is a real byte fact for all 140, not a timeout.

**Where it is weaker than the doc's parenthetical.** The *complement* is not "decoded objects".
14 tagged rows have a failed or truncated walk:

```
tagged rows with a bad/abnormal stop: 14
  ('PawnToMove','ObjectProperty','unknown_type_-217',34,30)
  ('AllSeqEvents','ArrayProperty','unknown_type_2239',34,18)
  ('GameSeq','ObjectProperty','unknown_type_2239',34,18)
  ('IsHeavyWeaponValid','Function','overrun',45,38)
  ('Batmobile_Jokerfied_Skin','SkeletalMesh','truncated_walk(end)',20385512,4867)
```

So "tagged" is where the walker happened to emit 1–2 junk tags, not where an object stops having
data. That does not invalidate the 140 (their zero type-ids are genuine), but it does mean the
card never looked at the rows the reader half-failed, and the doc's contrast ("not objects the
reader failed on") is not demonstrated — it is asserted.

**Verdict: HOLDS** for the 140 (verified byte-for-byte against the packages), with the boundary
caveat recorded.

---

## A2 · "every number is script-derived" and `--check` really compares

**Test.** Inspected `write_markdown()`: every figure is an f-string over `doc`/`summary`
(96/44, 67,298/7,524, 64,558, 5,562, 17/7, 29/96, 768/17). The only literal is the number of
census entries to print. Re-ran the check (above: 13/13, `md: PASS`) and independently summed the
JSON:

```
objects: 140 irrelevant 96 67298 relevant 44 7524
all bytes: 74822
facefx bytes: 64558
checks passing: 13 / 13
```

64,558 / 67,298 = 95.9 %, matching the doc's "the byte mass is FaceFX".

Two checks are weaker than the prose they are quoted for: `script-class tails decode a parent
class` asserts `7 rows, 5 distinct values` but never tests that the parent *matches the export
name* (the doc's "all 5 parents match the export names" is hand-checked prose); and `GAPS.md
still publishes 925 untagged` is `"**925**" in gaps`, which would pass on any occurrence of that
string. Neither makes a number wrong.

**Verdict: HOLDS** (R11 satisfied; two checks are weaker than their labels).

---

## A3 · the rows still describe the shipped packages

**Assumption (silent).** The `.upk`s on disk today are the ones the grab read, so `size` and
`index` are valid for the second pass.

**Test.** For all 140: `exports[i-1]['name'] == row['name']`, `['size'] == row['size']`,
`len(pkg.data(i)) == row['size']`, and `pkg.object_class(i) == row['class']`. Result: 0
mismatches of 140 (quoted in A1). Every one of the 44 relevant rows printed `len=? True`.

**Verdict: HOLDS.**

---

## A4 · `*Property` is irrelevant "because the value lives on the archetype"

**Doc.** Rule table: "`*Property` | irrelevant | property declaration - names a slot in a script
struct or function; **the value itself lives on the archetype**". 81 declarations, 2,708 B.

**Assumption.** A declaration never carries a number, and the number is elsewhere and decoded.

**Test 1 — where each declaration actually lives**, by the class of its *own outer export*
(export table, not name lookup):

```
81 property declarations, by the class of their ACTUAL outer export:
   Function                                      60
   ArrayProperty                                 11
   class-level (outer = the script class)        10
```

60 of 81 are function parameters/locals/returns (outer is a `Function`), 11 are array element
declarations (outer is the `ArrayProperty`). For those 71 the stated reason cannot apply at all:
a parameter has no archetype default; its value is whatever the bytecode passes. The doc's single
reason is correct for at most the 10 class-level rows.

**Test 2 — do the 10 class-level defaults appear on the decoded `Default__*` row?**

```
NewHydraPFX          ComponentProperty Default__RBatmobileMissileLauncherJoker  distinct tags=1  present=False
LastHitTime          FloatProperty     Default__RPawnVillainThugJokerWarehouse  distinct tags=3  present=False
DistToCannon         FloatProperty     Default__RPawnVillainThugJokerWarehouse  distinct tags=3  present=False
CannonRagdollRange   FloatProperty     Default__RPawnVillainThugJokerWarehouse  distinct tags=3  present=False
bRagdollWithCannon   BoolProperty      Default__RPawnVillainThugJokerWarehouse  distinct tags=3  present=False
(… ThugDeathAnims / ThugDeathIdleAnims: present=True)
```

2 of 10 present. The three floats that a damage/sim card would most want —
`CannonRagdollRange`, `DistToCannon`, `LastHitTime` — are declared, are **not** on the decoded
archetype, and are not anywhere else in the 140. So "the value lives on the archetype, which the
grab decodes" is exactly backwards for them: the card's own evidence is that the archetype decode
holds 3 names, none of them this.

**Verdict: BROKEN.** The reason is false for 71/81 by the outer chain and unverified for 8/10 of
the rest. The *verdict* ("irrelevant") is defensible for parameters, but the card's justification
for it does not survive, and three class-level floats are neither decoded nor flagged as a gap.

---

## A5 · `FaceFXAnimSet` = "audio/vis data, **counted by the audio cards**"

**Doc.** "FaceFX facial-animation asset for a dialogue line - audio/vis data, **counted by the
audio cards**", and "64,558 of the 67,298 irrelevant bytes" — i.e. 96 % of the dismissed byte mass
is dismissed on this sentence.

**Test.** Searched every audio output for the class:

```
$ grep -rn "FaceFX" Research/BatmobileGrab/*.md Research/BatmobileGrab/*.json | grep -v NATIVE_RELEVANCE
Research/BatmobileGrab/ASSETS.md:124:| FaceFXAnimSet | 13 |
Research/BatmobileGrab/ASSETS.md:407:- **FaceFXAnimSet** (7): FaceFXAnimSet, Main_Ch10_S05_Joker_A1_Warehouse_Intro_Conversation_06b, …
Research/BatmobileGrab/GAPS.md:37:| FaceFXAnimSet | end | 13 |
Research/BatmobileGrab/grab.json:121:  "FaceFXAnimSet": 13,
$ grep -n -i "dialogue\|facefx\|lip" Research/BatmobileGrab/AUDIO_FEATURES.md
(no output)
$ grep -rln "FaceFX" Tools/scripts/
Tools/scripts/grab_native_relevance.py
```

No audio card mentions FaceFX: not `AUDIO_FEATURES.md`, not `bmak_audio_features.py`. The 13
sets are counted by `ASSETS.md` — the generic asset census — and by `GAPS.md`, which is the very
gap table the card exists to close. "Counted by the audio cards" is a false attribution, and the
64,558 B are dismissed without a decode, on the class name alone (R5).

**Verdict: BROKEN** for the coverage claim. (The claim "facial animation is not a
weapon/sim/damage number" is probably right, but nothing on disk proves it and the card's stated
proof does not exist.)

---

## A6 · the 20 `Function` exports are "live bytecode, not an empty list", "not decoded by … any G1 card"

**Doc.** Rule: "`Function` | relevant | script bytecode - **not decoded**". Bullet: "The other 20
are `Function` payloads - live bytecode, not an empty list - and stay undecoded". Gaps: "20
`Function` exports (5,562 B) are **undecoded bytecode**. A numeric literal could be in the
instruction stream; **nothing here reads it**". `classify()` in the script: "not decoded by this
pass **or by any G1 card**".

**Test 1 — the bytes.** All 20 begin with a zero 16-bit word, so the walker stops at byte 0 for
all 44 relevant rows, exactly as it does for the 24:

```
StartFiring    Joker 559B head=00 00 00 00 00 00 69 fd ff ff 30 00 00 00 36 03  first4zero=True
MovePawnTo     V2    193B head=00 00 00 00 00 00 3c fe ff ff 03 00 00 00 00 01  first4zero=True
GetObjClassVersion Joker 54B head=00 00 00 00 00 00 84 fe ff ff 70 00 00 00 19 00 first4zero=True
BeginState     Joker  50B head=00 00 00 00 00 00 66 fd ff ff 14 00 00 00 15 00  first4zero=True
FireAtTarget   Joker 793B head=00 00 31 00 00 00 35 fe ff ff 3a 00 00 00 94 04  first4zero=False
```

20/20 have `00 00` at byte 0; 6/20 have four zero bytes. The doc's distinction ("the 24 have an
empty list, the other 20 do not") is therefore not a byte distinction the walker made — it is a
class-name distinction applied to identical first bytes.

**Test 2 — is the layout known?** `Research/BatmobileGrab/DAMAGE_RULES.json` (G1-14,
`bmak_damage.py`) publishes `function_export_layout`:

```
{"prefix_u16":0,"next":2,"super":6,"children":10,"line":14,
 "script_size_field":18,"script":22,"script_size":"len - 38", …}
```

Applied to the 20: `next`, `super`, `children`, `line` parse as coherent object refs and line
numbers, `super` equals the export table's own `super_index` (e.g. FireAtTarget -459,
PlayHitReaction -486, MovePawnTo -452), `script_size` at +18 is `len-37` for **20/20**, and the
`name_index` at `len-8` is the export's own name for **20/20**. So the payload is 22 B header +
script + 16 B trailer, not an opaque blob.

**Test 3 — run the sibling decoder on them** (`bmak_damage.Bm.walk`, unchanged):

```
FireWeapon       payload=548B script=510B tokens=113 refs=63 consts=4 unexplained=129
    consts: [{'at':126,'kind':'int','value':-1},{'at':158,'kind':'float','value':65536.0},
             {'at':211,'kind':'int','value':-1},{'at':338,'kind':'float','value':0.1}]
FireAtTarget     payload=793B script=755B tokens=159 refs=100 consts=3
    consts: [{'kind':'float','value':0.7},{'kind':'float','value':1.3}]
StartFiring      payload=559B script=521B tokens=108 refs=71  consts=2
    consts: [{'kind':'int','value':0},{'kind':'float','value':9999.0}]
DamagedBy        payload=218B script=180B tokens=33  refs=19  consts=1
    consts: [{'at':29,'kind':'float','value':0.2}]
ShouldGoRagdoll  payload=152B script=114B tokens=35  refs=12  consts=0
    refs: ['ShouldGoRagdoll.dmgType','Core.RDmgType_BatmobileCannon',
           'RPawnVillainThugJokerWarehouse.bRagdollWithCannon']
```

Five of the twenty decode immediately, with literals in the instruction stream (0.1, 0.2, 0.7,
1.3, 9999.0) and refs that name the very properties the card called irrelevant
(`bRagdollWithCannon`). The claim "not decoded by this pass or by any G1 card" is false:
G1-14's `bmak_damage.py` decodes 14 functions of the same class, publishes the layout, and works
on these without modification. The card's "5,562 B of undecoded bytecode" also overstates the
undecoded mass: 20 × 38 B = 760 B is header/trailer, leaving 4,802 B of script.

**Verdict: BROKEN.** Not a small wording issue: the card's Gaps section, its rule table, its
"what this settles" paragraph and the tracker row all rest on "these 20 are undecoded, so a
literal inside them is UNKNOWN". They are decodable today with the project's own tool, and five
of them yield numbers. (The doc's hedge — "explained: not decoded, never a value" — is honest
about its own limits, but the limit was not real.)

---

## A7 · the 7 parent classes are "inferred from the name correspondence, not a decoded `UClass.SuperField`"

**Assumption (stated, as a modesty claim).** The parent identification is a name guess.

**Test.** Compared the payload int32 at +4 with the export table's own `super_index`:

```
name                            pkg   idx  size | export.super_index -> path        | payload int32@4
RPawnVillainThugJokerWarehouse  Joker 110   332 | -127 Core.RPawnVillainThug        | -127 Core.RPawnVillainThug
RHidePoint_Batmobile            V2      5   224 | -126 Core.RHidePoint              | -126 Core.RHidePoint
RBatmobileMissileLauncherJoker  Joker  72   212 | -105 Core.RBatmobileMissileLauncher| -105 Core.RBatmobileMissileLauncher
RJokerMissileTarget             Joker  74   128 | -118 Core.RDummyTarget_Spawnable  | -118 Core.RDummyTarget_Spawnable
RSeqEvent_JokerBossEvent        Joker 114   116 | -270 Core.SequenceEvent           | -270 Core.SequenceEvent
```

7/7 exact. The same export records give `class_index = 0` and `outer = BmScript` for all seven:

```
RPawnVillainThugJokerWarehouse  Joker    class_idx=0  super=-127  outer=BmScript
RHidePoint_Batmobile            Funhouse class_idx=0  super=-109  outer=BmScript
```

So the parent class is readable from the export table independently of the payload, and the two
agree in every row. The doc's "inferred, not decoded" is over-cautious rather than wrong — but
the consequence is that the `--check` guard (`7 rows, 5 distinct parents`) is testing the weaker
thing: it would pass on any 7 negative int32s resolving to 5 distinct paths, even if the payload
and export table disagreed.

**Verdict: HOLDS** (the identification survives; the doc's modesty label understates the evidence
and the check does not enforce the correspondence the prose claims).

---

## A8 · "declaring no properties of its own" — are the 7 class payloads explained?

**Doc.** "which is what an `(unresolved)` class export is: a script class compiled into the
package, outer `BmScript`, **declaring no properties of its own**". Gaps lists only the 17
component tails, not these.

**Test.** Dumped the 7 payloads. They are 116–332 B each (1,460 B total) and are not "empty list +
super":

```
=== RHidePoint_Batmobile (Funhouse) 224B
   +0   00 00 00 00 93 ff ff ff 04 00 00 00 00 00 00 00
   +16  00 00 00 00 49 01 00 00 ff ff 02 00 01 00 00 00
   +32  a6 07 00 00 00 00 00 00 04 00 00 00 12 02 a0 80
   +48  86 ff ff ff d3 07 00 00 00 00 00 00 09 00 00 00
   …
   +88  00 00 00 00 00 00 00 00 75 00 00 00 00 00 00 00
```

`+20 = 329` is the export index of `BatmobileFunhouse.LensFlareComponent`; `+60 = 9` is
`Batmobile_EMPMissile_Projectile.RocketTrail`; `+88/+112/+124/+136 = 117/118/119/120` are the four
`AkEvent` imports. In `RPawnVillainThugJokerWarehouse` the pattern is a name index next to an
object ref (`+132 = 3195` → `Default__…Mesh`, `+136 = 1084` → `names[1084] = "CollisionCylinder"`,
`+160 = 3084` → `names[3084] = "ThreatComp"`). So each class payload carries a list of its default
sub-objects/components by name and reference — 34–300 B per row that the document neither decodes
nor lists as a gap.

A brute walk from every start offset 0–79 finds candidate tag parses at 8, 26, 40, 60, 65, 77 in
these payloads, so I am not claiming a tag stream is there — only that 1,460 B is described as
"no properties of its own" while it demonstrably holds a component list.

**Verdict: WEAK.** The classification ("relevant, defaults elsewhere") is right; the explanation is
incomplete for 1,460 B and the Gaps section omits it (it names only the component tails). The
sentence "declaring no properties of its own" is an inference from an empty tag list, not a
finding about the class.

---

## A9 · component tails: "a header, not a value"

**Doc.** "17 component rows stop at their own name: the tail is `NameIndex + Number` … so it is a
header, not a value", then "**7 of those 17 payloads carry a float-like value**".

**Test 1 — structure.** The 8-byte FName is real (A10), but it is not the whole tail:

```
CollisionCylinder  Joker 46B 00 00 00 00 3c 04 00 00 00 00 00 00 05 00 3c 01 91 0a 00 00
                              00 00 00 00 04 00 00 00 00 00 00 00 00 00 00 00 04 00 6c 01
                              37 5b 1b 3f 00 00
NewHydraPFX1       Joker 62B … 04 00 6c 01 dd 5d 6e 3f 03 00 dc 01 00 40 00 50 00 00
```

After the FName (offset 12) there are 34–50 further bytes with a repeating shape
(`04 00 | 6c 01 | <float32> | 00 00`) and a second record in `NewHydraPFX1`. The doc's wording
"the tail is NameIndex + Number" describes offsets 4–11 only; the "header, not a value" conclusion
is then applied to bytes the document itself says carry 7 floats.

**Test 2 — is the float window hiding values?** Rescanned every component tail at every byte
offset with window 1e-6 … 1e6, negatives included:

```
CollisionCylinder   46B script=[(40,0.60686)]      extra=[(37,7.71e-06)]
NewHydraPFX1        62B script=[(48,0.93112)]      extra=[(19,0.00781),(54,2.00011)]
GadgetMesh          58B script=[(40,0.77383)]      extra=[(39,9827.00098)]
CriticalPfxCompBase 46B script=[(40,0.23984)]      extra=[(40,0.23984)]   ← same value, unrounded
```

Every "extra" is the same byte run read at an unaligned offset. No in-range value is being
dropped, and the count 7 of 17 is right. The values themselves are all in (0.24, 0.93) — a spread
that looks like real float data, not bit noise — which is why "UNKNOWN" is the correct label and
"header, not a value" is not.

**Verdict: WEAK.** The count and the UNKNOWN label hold; the sentence that the tail is a header
rather than a value over-reaches past the 8-byte name.

---

## A10 · the 17 tails are the object's own name

**Test.** For all 17, `pkg.names[int32@+4] == row['name']` — true 17/17 — and the same int read as
an object index resolves elsewhere:

```
XCS              +4 idx 3367  names[3367]=XCS       as object: jongee_test.Batmobile_V3_TEXTURES_Wheel_V2_R
ThreatComp       +4 idx 3084  names[3084]=ThreatComp as object: PhysicsAssetInstance.RB_BodyInstance
XrayLightComponent +4 idx 3378 names[3378]=XrayLightComponent as object: Textures.Lens_Dirt
```

**Verdict: HOLDS.** This is the card's cleanest decode.

---

## A11 · "96 native references across 29 rows … a reference is a pointer to another object, not a value"

**Test 1 — arithmetic:** 29 rows, 96 refs (recounted from `objects.jsonl`), matching
`summary.native_refs`. **Test 2 — what the words are.** The grab's finder
(`batmobile_grab.py:119`) keeps every aligned word whose value resolves to an export of an
"interesting" class. Ran it against the name table:

```
XCS                +4  idx 3367  names[3367]=XCS
ThreatComp         +4  idx 3084  names[3084]=ThreatComp
XrayLightComponent +4  idx 3378  names[3378]=XrayLightComponent
```

Those three of the 96 *are* the own-name words A10 proves are headers — the document contradicts
itself between "a header, not a value" (17/17 verified) and "references, not values" (96 counted).
Sixteen more refs are a single repeated constant at +88 in every FaceFX/dialogue row
(`idx 256`), which is at least as consistent with a fixed FName field as with a pointer.

**Verdict: WEAK** (3 of 96 provably mislabelled; the remaining 93 are unverified guesses by the
same heuristic, and some — e.g. `RHidePoint_Batmobile` `+88..+136` → four consecutive `AkEvent`
imports — look genuine).

---

## A12 · "the values the relevant classes do have live on their `Default__*` objects"

**Doc.** "The values the relevant classes do have live on their `Default__*` objects, which the
grab decodes as ordinary tagged rows (`Default__RBatmobileMissileLauncherJoker` and friends)."

**Test.** Looked up `Default__<class>` for the 5 script classes and the 7 component classes:

```
Default__RBatmobileMissileLauncherJoker   Joker   size=132 tags=9    stop=eof
Default__RHidePoint_Batmobile             ×3      size=310 tags=15   stop=eof
Default__RPawnVillainThugJokerWarehouse   Joker   size=334 tags=18   stop=eof
Default__RSeqEvent_JokerBossEvent         Joker   size=497 tags=3    stop=eof
Default__RDummyTarget_Spawnable           MISSING
Default__AkDialogueComponent              MISSING
Default__CylinderComponent                MISSING
Default__ParticleSystemComponent          MISSING
Default__RInteractionComponent            MISSING
Default__RVehicleThreatComponent          MISSING
Default__SkeletalMeshComponent            MISSING
Default__SpotLightComponent               MISSING
```

8 of 12 have no `Default__` row in the grab at all (the classes are `Core` imports, so their
defaults are not in these packages and were never read). And the four that exist are thin:
`Default__RPawnVillainThugJokerWarehouse` carries 18 tags but only **3 distinct names**
(`Components`, `ThugDeathAnims`, `ThugDeathIdleAnims`); `Default__RBatmobileMissileLauncherJoker`
carries one (`MaxTargetsPerLevel`). So "the values … live on the `Default__*` objects" is
unsupported for the missile-target class specifically (`RJokerMissileTarget`, the one row in the
set whose name says "weapon target"), and the archetype rows it does point at hold almost nothing.

**Verdict: BROKEN** as a fleet-wide statement. It is the sentence the card uses to justify calling
each relevant row harmless.

---

## A13 · "the families G1-08 / G1-14 / G1-21 list are all in `OFFSETS.json` / `CHAIN.json` already"

**Test.** Counted the relevant-class families in both files:

```
OFFSETS.json  Joker 46  MissileLauncher 98  RHidePoint 0  SequenceEvent 0  RPawnVillainThug 0  DummyTarget 0
CHAIN.json    Joker 36  MissileLauncher 76  RHidePoint 0  SequenceEvent 0  RPawnVillainThug 0  DummyTarget 0
CannonRagdollRange 0  DistToCannon 0   (both files)
```

Four of the five class families in the card's own relevant set appear zero times; the `Joker`
hits are unrelated strings (`BatmobileJoker…` material/texture names). The sentence is about
"the families those cards list", which it never enumerates, so it cannot be checked against the
set it is used to excuse — and for the values that *would* be in scope (the three
`Default__RPawnVillainThugJokerWarehouse` floats) it is false: they are in neither file.

**Verdict: WEAK** (unenumerated, and the one testable reading fails).

---

## A14 · "none of the names appears in `WEAPONS.md`, and `DAMAGE_RULES.md` carries only the unrelated substring …"

**Test.** Grepped all 18 distinct function names across `Research/BatmobileGrab/*.md|*.json`:

```
BeginState    -> ASSETS.md DAMAGE_RULES.json
FireWeapon    -> ASSETS.md BMSDK_OFFSETS.json DAMAGE_RULES.json
ReadyToFire   -> ASSETS.md DAMAGE_RULES.json
DamagedBy     -> ASSETS.md DAMAGE_RULES.md BMSDK_OFFSETS.json DAMAGE_RULES.json
…
$ grep -c "ReadyToFire\|FireWeapon" Research/BatmobileGrab/DAMAGE_RULES.md
0
```

The literal claim holds: 0 hits in `WEAPONS.md`; `DAMAGE_RULES.md` has only
`bDamagedByCloudburstTank` (line 108). But the sibling JSON it sits next to names the same
functions:

```
"DAMAGE_RULES.json" field_references:
  "Firing.BeginState", "Primed.ReadyToFire", "RBatmobileMissileLauncher.ReadyToFire",
  "RBatmobileAllegianceSwitcher.FireWeapon", …
```

`ReadyToFire` / `FireWeapon` / `BeginState` are exactly the states of
`RBatmobileMissileLauncherJoker`, the class in this card's relevant set. The sentence is being
used to support "adds no new number"; as evidence of that it is misleading, even though the
sentence as written is true.

**Verdict: HOLDS literally, WEAK as evidence.** (The real problem with this row is A6, not the
grep.)

---

## A15 · units and conventions: byte sizes, the >8 B cut, the float window

**Assumptions.** (i) `size` is the export payload in bytes; (ii) the card's ">8 B" is applied as
`size > 8`; (iii) a "float-like" value is a finite float in [0.01, 10⁴].

**Test.** (i) `len(pkg.data(i)) == row['size']` for 140/140 (§A3). (ii) The small census is
`{2: 768, 6: 17}` — only two sizes, no 8-byte row, `768 + 17 = 785 = 925 − 140`; the generator's
own check re-derives it and passes. (iii) A 6-decade-wider rescan with negatives found no new
values (§A9). The window does silently drop 0.0 and negatives — but there are none in these 17
payloads, so the published count is not a floor.

**Verdict: HOLDS.** (No coordinate/transform convention is involved in this card, so R2 does not
apply.)

---

## A16 · "Anything no rule covers would be reported as `UNCLASSIFIED`; there are none" / the six-byte rows

**Test.** `small_by_size_class`:

```
"6": {"AkVehicleSound":4, "PointLightComponent":1, "RInteractionComponent":8, "RVisualDamageComponent":4}
```

`RInteractionComponent` is in the script's `COMPONENTS` set, i.e. the rule's verdict for it is
**relevant** — yet its 8 six-byte rows are never classified. The doc names only the three classes
"not in the rule above" and says nothing about the 8 rows that *are* in the rule but below the
cut. `GAPS.md` corroborates the count (`RInteractionComponent | end | 15` = 7 + 8), so the rows
are real and known. Since each 14-B sibling is provably just an FName + 2 bytes (A10), a 6-B one
cannot hold a value, so the *outcome* is safe; the *statement* ("anything no rule covers …
none") is true only inside the 140, and the doc's six-byte paragraph describes the census
incompletely.

**Verdict: WEAK** (outcome safe, framing inaccurate).

---

## A17 · the 2 `State` rows = "script state header (state machine label, not a value)"

**Test.** Dumped both payloads (59 B `Holstered`, 71 B `Firing`, outer
`BmScript.RBatmobileMissileLauncherJoker`). They share the function-shaped 14-byte header
(`00 00 | next | super | children | line`), but the field at +18 is `1`, not `len-37`:

```
Firing     71B script_size_field=1 len-37=34 script=33B tokens=3 refs=3 consts=0
Holstered  59B script_size_field=1 len-37=22 script=21B tokens=2 refs=2 consts=0
```

So the G1-14 function layout does **not** transfer, and the generic walker's "tokens" here are
likely coincidence. What is certain is that the payload is not a bare state label: it carries a
ref table and 21/33 B past the header. The card did not decode it; it classified by class name.
130 B total, so the risk is small — but the reason given is a guess (R5).

**Verdict: WEAK** (name-based reason, no decode; no value found either).

---

## What I could not test

- **The bytecode literals are not mine to interpret.** `bmak_damage.Bm.walk` is the project's own
  heuristic token scan (its docstring: "aligned but not a decoder"). It proves the payloads are
  structured and readable and that literals exist; it does not prove what `0.1`, `0.7` or `9999.0`
  *mean*. A6 is therefore "the card's reason is false", not "the card missed a specific value".
- **Whether `FaceFXAnimSet` carries only visemes.** I did not decode a FaceFX payload. The verdict
  on A5 is about the claimed coverage, which is checkably absent.
- **The 93 other "native refs".** I proved 3 are name indices; I did not classify the rest, so I
  did not raise or lower the 96.
- **The 785 small objects** were not individually re-read; only their size census and the 17
  six-byte rows (A16).

## Suggested corrections (for the card's owner, not applied here)

1. Replace "not decoded by this pass or by any G1 card" with the G1-14 layout and run
   `bmak_damage`'s `script()` + `walk()` over the 20 rows; publish the literals as UNKNOWN-meaning
   but *decoded* values, and correct 5,562 B → 4,802 B of script + 760 B of header/trailer.
2. Replace the `*Property` reason with the outer-chain split (60 function members / 11 array
   elements / 10 class-level) and list the 3 floats with no decoded default as a gap.
3. Drop "counted by the audio cards" (it is `ASSETS.md`), or add the FaceFX sets to the audio
   card's scope.
4. Qualify "the values live on `Default__*`" with the 8 of 12 classes that have no such row.
5. Exclude the 3 own-name words from `native_refs`, or say the 96 are "candidate" references.
6. Note the 8 six-byte `RInteractionComponent` rows and the 1,460 B of class-payload tails.

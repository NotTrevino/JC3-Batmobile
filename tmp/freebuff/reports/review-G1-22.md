# Independent review — G1-22 · Native remainder check for feature relevance

Reviewer: Buffy (Freebuff), 2026-10-29. Card: `GRAB_BACKLOG.md` L552-557; tracker row L1290.
Outputs reviewed: `Research/BatmobileGrab/NATIVE_RELEVANCE.md` (144 lines),
`NATIVE_RELEVANCE.json` (416 objects' worth of record + `summary` + 9 checks),
`Tools/scripts/grab_native_relevance.py` (419 lines), MODLOG §"G1-22 · Native remainder
relevance — done" (L8811-8856).

## VERDICT: **needs rework**

The population work (925/140, 116+24, face-validity of the 140 classification, the
index-based second pass) is careful and reproducible, and every headline count reproduces
exactly. But the card's *deliverable* is a relevance judgement, and two of its four
irrelevant rules rest on claims the data does not support:

* the 20 `Function` exports (5,562 B) are called irrelevant because their "behaviour is
  already decoded through G1-08, G1-14, REGISTRATION.md". Those functions' bodies were
  never read by any card, and the named documents contain none of them except one
  substring hit. Script bytecode holds numeric literals — this is the one class of the 140
  that most plausibly could carry a damage/impulse number, and it was never handed to a
  decode pass.
* the 17 component instances are called "header-only" with "no room for a value field",
  which the payload bytes contradict: 7 of the 17 end in a distinct non-zero float at
  byte +40 (0.60686 / 0.23984 / 0.84841 / 0.82546 / 0.77383 / 0.49544 / 0.93112).

Because of those two, the bold conclusion "**No weapon, sim or damage value hides in the
native remainder**" (L107) is not supported by the evidence in the document, and the
tracker row's "17 header-only components" propagates the same claim. These are R4 failures
(a guess presented as fact instead of UNKNOWN) and an R5 failure (a member's name — and the
name of a neighbouring card — used in place of its behaviour).

The classification mechanics, provenance of every count, and the `--check` gate (other than
one gap listed below) are sound; this is a rework of the reasoning and two rule texts, not of
the population.

## Check output (verbatim)

```
$ python Tools/scripts/grab_native_relevance.py --check
OK: 140/140 classified (116 irrelevant, 24 relevant); 9/9 checks
EXIT=0
```

All 9 checks pass:

```
PASS population: 925 untagged | 925
PASS population: 140 over the 8 B threshold | 140 over, 785 at or below
PASS 140/140 classified | 116 irrelevant, 24 relevant, 0 unclassified
PASS every relevant object got a second pass | 24/24
PASS every second pass records a stop reason | end
PASS script-class tails decode a parent class | 7 rows, 5 distinct parents
PASS component tails are the object's own name | 17/17 components
PASS no second pass read a property tag | 0 tags over 24 objects
PASS GAPS.md still publishes 925 untagged | text search
```

Out paths: `NATIVE_RELEVANCE.md` exists (144 lines) and `NATIVE_RELEVANCE.json` exists. The
card names only the `.md`; the `.json` is a superset, fine.

Done criterion vs what `--check` verifies:

| card Done | verified by `--check`? |
|---|---|
| 140/140 classified | yes — `len(objects)==140` and `unclassified==0`, both recomputed from `objects.jsonl` |
| relevant ones **decoded or explained** | only structurally: "every relevant object got a second pass" asserts a `pass` dict exists, "every second pass records a stop reason" asserts `stop` is non-empty, "no second pass read a property tag" asserts `tag_count==0`. Nothing checks that the `detail` text is *true*, and nothing at all constrains the 116 irrelevant rows. The Done criterion is therefore stronger than the gate. |

The gate also never compares the `.md` with a fresh render (issue 8).

## Issues

### 1. `Function` = irrelevant rests on a false provenance claim — CONFIRMED, R4 + R5, blocking

`Research/BatmobileGrab/NATIVE_RELEVANCE.md` L24 (rule table) and L37 (irrelevant table),
identical text in `grab_native_relevance.py` L52-53 (`IRRELEVANT["function"]`):

> script bytecode - the behaviour behind these names is already decoded through the
> reference passes (G1-08, G1-14, REGISTRATION.md)

Evidence against it:

* `grep -l FireWeapon StartFiring FinishedFiring PlayHitReaction Research/BatmobileGrab/*.md`
  → only `ASSETS.md`, whose L410 is a plain name list
  (`**Function** (18): \`BeginState\`, \`CheckForDeadThugs\`, \`DamagedBy\`, …`). That is a
  listing of exports, not a decode of behaviour.
* `WEAPONS.md` (G1-08) contains **none** of the 20 names. `DAMAGE_RULES.md` (G1-14) contains
  the substring `DamagedBy` only inside `bDamagedByCloudburstTank` (L108), an unrelated flag.
* The 20 `Function` payloads are not header-only. `upk_read.export_summary` stops at the
  empty property list at byte 0, but the tail is live bytecode:

  ```
  FireWeapon   idx 30, 548 B, tail 544 B, 362 non-zero bytes
              00 00 5a fd ff ff 1d 00 00 00 fb 02 00 00 ff 01 00 00 07 ef 02 ...
  FireAtTarget idx 59, 793 B, tail 789 B, 552 non-zero bytes
  DamagedBy    idx 93, 218 B, tail 214 B, 149 non-zero bytes (float 0.2 at tail +48)
  ```

* The names are exactly the behaviour of the Joker missile launcher and the thug pawn
  (`FireWeapon`, `StartFiring`, `FireAtTarget`, `ReadyToFire`, `ShouldGoRagdoll`,
  `CheckForDeadThugs`, `MovePawnTo`). Classifying them irrelevant is a judgement made from
  the *class name* and the *function names*; no byte was decoded. That is R5.

Consequence: the card's Done criterion ("relevant ones decoded or explained") is not met for
the largest non-FaceFX block of the remainder, and the 5,562 B it covers is precisely where a
literal damage/impulse/velocity number would live.

**Required fix (generator, not the `.md`)**: either run the decode pass on the 20 `Function`
exports (record the bytecode layout, list any float/int literals found and mark their meaning
`UNKNOWN`), or reclassify them `relevant` with the reason "script bytecode — not decoded;
numeric literals possible", and drop the "already decoded" sentence and the "no value hides"
conclusion. Nothing may claim G1-08/G1-14 decoded these.

### 2. `Function` reclassification is also inconsistent with the counts in the same doc

The doc's own rule table lists 4 irrelevant classes; `Function` is 5,562 B of the 72,860 B
irrelevant total, i.e. it is 7.6 % of the mass the "no value" claim covers. Whichever way
issue 1 is resolved, the `92,860`-style arithmetic and the tracker row must be re-derived.

### 3. "header-only" / "no room for a value field" is contradicted by the payloads — CONFIRMED, R4, blocking

`NATIVE_RELEVANCE.md` L99-101:

> **17 component rows stop at their own name** … At 14-62 bytes there is no room for a
> value field in any case.

and L107-110:

> 17 component instances whose payloads are header-only

The 4 B empty tag list + 8 B FName header account for 12 B. Beyond that the larger payloads
carry structure and a per-object float at offset +40 (verified by decoding the export at the
JSON's own index, Joker package):

| object | size | float at +40 |
|---|---|---|
| `CollisionCylinder` (`CylinderComponent`, idx 502) | 46 B | 0.60686 |
| `CriticalPfxCompBase` (`ParticleSystemComponent`, idx 2963) | 46 B | 0.23984 |
| `GenericHeadParticleSystem` (`ParticleSystemComponent`, idx 2964) | 46 B | 0.84841 |
| `XCS` (`ParticleSystemComponent`, idx 2965) | 46 B | 0.82546 |
| `GadgetMesh` (`SkeletalMeshComponent`, idx 120) | 58 B | 0.77383 |
| `Mesh` (`SkeletalMeshComponent`, idx 3195) | 58 B | 0.49544 |
| `NewHydraPFX1` (`ParticleSystemComponent`, idx 117) | 62 B | 0.93112 (+ a 2.00011 at +54) |

Example, `Mesh` idx 3195 in full:

```
00 00 00 00  4e 08 00 00 00 00 00 00  05 00 3c 01 91 0a 00 00 00 00 00 00
04 00 00 00 00 00 00 00 00 00 00 00  04 00 6c 01 fb a9 fd 3e  00 00 ...
^ empty list ^ FName 2126 = "Mesh", number 0                                  ^=0.49544
```

"62 bytes is no room for a value field" is false on its face (62 B holds 15 floats), and the
+40 field is a number the document never mentions. Its *meaning* is genuinely `UNKNOWN`
(scale? bounds? sort priority? — this walker does not model the tail, as L120-124 admits),
but the honest record is "7 of 17 carry an unlabelled float at +40; semantics UNKNOWN", not
"header-only, no value". Note the internal contradiction too: the Gaps section (L120-124)
correctly says the tail "hold[s] an FName header and, for the larger ones, native bytes this
walker does not decode", which cannot coexist with "no room for a value field in any case"
(L101).

### 4. "No weapon, sim or damage value hides in the native remainder" is an overclaim — CONFIRMED, R4, blocking

L107. The evidence covers 24 of 140 objects. The remaining 116 irrelevant objects include
5,562 B of unread bytecode (issue 1). The 785 objects at or below the threshold are not part
of the 140, but the sentence says "the native remainder" without that scope, and that set is
not just stubs (issue 6). The supportable statement is narrower: "of the 24 objects this card
calls relevant, none yielded a property tag; their parent classes and owning archetypes are
known" — plus an explicit `UNKNOWN` for the bytecode and the unmodelled tails.

### 5. "The relevant half is 5 script class declarations and 17 component instances" — CONFIRMED, arithmetic error

L107-108. `5 + 17 = 22`, but `relevant` is 24. The 7 rows are 5 *distinct classes* (L86 says
this correctly). Should read "7 script-class rows (5 distinct classes) and 17 component
instances".

### 6. "768 of them are 2-byte `Package` stubs" is wrong, and hides 17 components — CONFIRMED, R11 + R4

L124-125:

> The 785 untagged objects at or below 8 B are not individually classified - the card sets
> the threshold at >8 B, and 768 of them are 2-byte `Package` stubs.

768 is the number of 2-byte objects, not of `Package` objects. Recomputed from
`objects.jsonl`: 785 ≤ 8 B = 768 two-byte + 17 six-byte;

* two-byte, by class: `Package` **696**, `RAkAudible` 30, `RAnimNotify_Clip` 9,
  `MaterialInstanceConstant` 4, `RB_BodyInstance` 4, `RB_ConstraintInstance` 4,
  `RB_StayUprightSetup` 4, `RAddContentBatmobileMesh` 4, `RAnimNotify_CollisionOptions` 4,
  `RAnimNotify_CanCancelAfterHere` 3, `RAnimNotify_Footstep` 2, and one each of
  `RJokerMissileTarget`, `AnimNotify_Sound`, `ForceFeedbackWaveform`,
  `RAnimNotify_FloorHeight`;
* six-byte: `RInteractionComponent` **8**, `RVisualDamageComponent` **4**,
  `AkVehicleSound` 4, `PointLightComponent` 1.

So the sentence is off by 72 objects, and the 17 six-byte rows are component instances whose
classes the doc's own rule calls *relevant* — including `RVisualDamageComponent`, a
damage-named class sitting inside the untagged remainder. "Not in scope" is a legitimate
answer (the card's threshold is >8 B), but the document should say what the 17 are, not fold
them into "Package stubs". The count is also a typed literal in the renderer
(`grab_native_relevance.py` write_markdown, the `"%d of them are 2-byte ..."` line), i.e. an
R11 violation independent of the wrong value.

Related, same table: L16 prints
`| at or below 8 B (not in scope; Package 696, RAkAudible 30, RAnimNotify_Clip 9) | 785 |`
— a `[:3]` slice of `small_by_class` (six classes), presented as if it were the census. The
sentence "not in scope; Package 696, …" reads as an exhaustive description of the 785.

### 7. Header says the 925 "could not decode" — CONFIRMED, minor R4

L3-4: "the 925 untagged exports the grab could not decode". Untagged is not undecoded: 17 of
the 925 carry `parsed > 0` and 0 tags (e.g. `Interactions` idx 3135, 4 of 14 B parsed) — the
walker decoded the (empty) property list and found nothing. The 140 under review are the
0-tag set; "untagged" is the right word, "could not decode" overstates failure.

### 8. `--check` does not verify the Markdown — CONFIRMED, gate gap

`main()` compares `NATIVE_RELEVANCE.json` with a fresh `build()` but only tests that
`NATIVE_RELEVANCE.md` *exists*. A hand-edited `.md` — e.g. changing "116" to "110" — still
passes. Today the file is genuine: I re-rendered `write_markdown(build())` and it is
byte-identical to the shipped file (11,326 chars, no diff). So this is a hole in the gate,
not a defect in the current output; still worth closing (compare `write_markdown(doc)` with
the on-disk text, as the project's other `--check`s do).

### 9. Parent-class reading stated as fact, corroborated only by name — CONFIRMED, minor R4

L87-91 ("decode their parent class … which is what an `(unresolved)` class export is") and
the MODLOG's "each exactly the base class the export's name implies". The pass establishes:
the first int32 after the empty tag list is negative, i.e. an import index, and its path is
`Core.RHidePoint` / `Core.RBatmobileMissileLauncher` / `Core.RDummyTarget_Spawnable` /
`Core.RPawnVillainThug` / `Core.SequenceEvent`. That those imports are the *super class
field* is an inference corroborated 5/5 by the export names (`RHidePoint_Batmobile` →
`Core.RHidePoint`), which is good evidence but not a decoded UE3 `UClass.SuperField`. The
name check in the script (`len({names}) == 5 and len(parents) == 7`) tests the names, not the
semantics. One sentence marking it "inferred from the name correspondence" would close this.

### 10. Tracker row and MODLOG repeat the two blocking claims — CONFIRMED

`GRAB_BACKLOG.md` L1290: "24 relevant = 7 script-class exports whose parent class the second
pass decodes + 17 **header-only** components". MODLOG L8811-8856 repeats "the behaviour the
reference passes already decoded: `FireWeapon`, `StartFiring`, `DamagedBy`,
`PlayHitReaction` …" and "no weapon, sim or damage value hides in the native remainder".
Both need the same correction as issues 1-4 when the card is reworked.

## Spot-checks

All numbers recomputed from the sources the script reads (`objects.jsonl`, 993-file grab) or,
for the component payloads, from the shipped `.upk` at the JSON's recorded export index.

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | 140 relevant-to-review out of 925 untagged; 785 ≤ 8 B | `objects.jsonl`: `len([r for r in rows if not r["tag_count"]])` = 925; `size > 8` = **140**; `<= 8` = **785** (768×2 B + 17×6 B) | matches |
| 2 | `FaceFXAnimSet` 13 objects, 64,558 B, and 64,558 of the 72,860 irrelevant bytes | sum over the 13 big `FaceFXAnimSet` rows = **64,558**; irrelevant total (116 rows) = **72,860** | matches |
| 3 | "96 native references across 29 of the 140 rows" | `sum(len(native_refs))` over the 140 = **96**; rows with any = **29** | matches |
| 4 | `Function` 20 objects, 5,562 B | count = 20, byte sum = **5,562** (FireAtTarget 793 … FindContactName 45) | matches — but the verdict on them does not (issue 1) |
| 5 | 17 own-name tails / 7 parent-class rows / 5 distinct parents | `JSON.summary.outcomes` = `{"own-name": 17, "parent-class": 7}`; `parents` has 5 entries; panel re-walked at each index reproduces the same `detail` | matches |
| 6 | "component payloads are header-only" | decoded 7 of the 17 payloads at their own index: float at +40 = 0.60686 / 0.23984 / 0.84841 / 0.82546 / 0.77383 / 0.49544 / 0.93112 | **does not match** (issue 3) |
| 7 | 128 of the 140 in `Playable_BatmobileJoker_SF` (MODLOG) | Counter over the 140 = Joker **128**, Funhouse 4, MK2 4, V2 4 | matches |
| 8 | `Default__RBatmobileMissileLauncherJoker` is "decoded as an ordinary tagged row" (L109-111) | `objects.jsonl`: `size 132`, `tag_count 9` | matches |

## What would flip this to "sound"

1. `Function` handled honestly (decoded, or `relevant` + `UNKNOWN`), with the "already
   decoded through G1-08/G1-14" sentence removed (issue 1).
2. Component section rewritten around the +40 float and the unmodelled tail; "header-only"
   and "no room for a value field" deleted (issue 3).
3. The "no value hides" headline scoped to what was actually walked, with the bytecode and
   the 785 ≤ 8 B rows named as `UNKNOWN` (issue 4).
4. The two typed/incorrect numbers fixed in the generator: 5-vs-7 rows (issue 5), the
   "768 … Package stubs" sentence and the `[:3]` class list (issue 6).
5. `--check` comparing the rendered `.md` with disk (issue 8).

Everything else — the 925/140 population, the index-based second pass, the FaceFX byte-mass
argument, the `native_refs`-are-pointers explanation, the revert path in MODLOG, and the
"never wrote into the game install" claim (the pass only reads the `.upk`s) — is sound and
reproducible.

No game was launched, no file outside this report was written, nothing was committed.

# Assumption challenge — backlog card **B-02 · Split the body into movable parts** (done 2026-10-24)

Read-only pass over the finished card. What was read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76),
the B-02 card and its `Done` clause (§8, lines 994–1011), its §12 row (line 1333), the two MODLOG
blocks that make up its record — `## B-02 · Split-face review — done` (line 8178) and
`## B-02 · Part split — done` (line 8215) — and every artifact they name:
`Working/Appearance/build_parts/` (80 RBMs + `parts_manifest.json` + `assembly.json`),
`Working/Translation/T8_PARTS.json`/`.md`, `Research/BatmobileGrab/SPLIT_FACES.{json,md}`,
`BONES.json`, `TYRES.md`, `Tools/scripts/bat_assemble.py` (the `--parts` cut), `silhouette_check.py`,
`spec_check.py`, `deploy.py`'s budget metric, and `Builds/test-091`'s entity folder for comparison.

No game was launched (R6), nothing was written to `D:/Games`, nothing was committed, no secret was
read, and **no repository file was modified except this document**. Three of the card's own checks
were re-run read-only and all exited 0: `silhouette_check.py --manifest …`,
`spec_check.py Working/Appearance/build_parts <body_lod1 template>`, and two scratch recomputations
(face accounting from `BONES.json`, byte totals and SHA-256 of the 80 RBMs). Nothing else was
touched; the proxies were `python -c` one-liners plus `/tmp` scripts.

---

## VERDICT summary

**The card's four headline numbers reproduce exactly.** 80 RBMs (16 entries × 5), 299,837 LOD0
faces, silhouette coverage **0.9997**, interior tears **0.065 %**, budget **4,790.9 / 4,915 KB**,
`spec_check` **295 blocks / 0 mismatches**, ties **31 → 26/4/1**. Where the card is weak is not in its
arithmetic but in **what its sentences cover**: "every part at its pivot" excludes the wheels, "the
faces owned by its bones" is not the rule used for the wheels, "pivots are bone bind" is false for
those same four wheels, "5 LODs" includes 22 files that are byte-identical copies, and the budget's
124 KB headroom is smaller than the 186 KB of duplicate LODs the card created.

| # | assumption (stated or silent) | verdict |
|---|---|---|
| A1 | "0 lost faces": body 171,391 + parts 44,502 = 215,893 is the full non-wheel LOD0 body | **HOLDS** — `all_faces_accounted` compares the manifest's 299,837 with the source face array, and the same total matches `BONES.json`; one of the three checks is a typed constant (R11 nit) |
| A2 | every part's faces are "the faces owned by its bones" (Do step 1) | **WEAK** — true for the 11 parts (±1,476 split faces), false for the 4 wheels: 28,528 owned vs 83,944 built (the hub-radius classification, not bone ownership) |
| A3 | pivots are "bone bind through the one transform" | **WEAK** — 12/16 match `BONES.json` to ≤ 1.4e-5 m; the 4 wheels are 2.0–3.2 mm off and wheel_f_l carries wheel_f_r's z |
| A4 | "reassembling **every** part at its pivot reproduces the body silhouette" | **WEAK** — the check reassembles 12 of 16 parts; all four wheels (83,944 LOD0 faces, 28 % of the mesh) are excluded from `silhouette_parts` |
| A5 | "5 LODs per part" | **BROKEN in substance** — 80 files exist, but 22 of them are byte-identical duplicates of a lower LOD (185.8 KB), more than the 124.1 KB the card has left under the cap |
| A6 | budget "4791 KB of 4915 KB" is the vehicle's Model footprint | **WEAK** — it is the *model block set* (80 files). The same entity folder holds 197 RBMs / 8,528.1 KB; the number is the house metric (`deploy.py`), but nothing in the card says so |
| A7 | "the same decimation settings as the body" | **WEAK** — the body's LOD targets are absolute tri counts (`43000,6000,3000,1500,800`), the parts' are ratios; "same settings" is not what happened and cannot be |
| A8 | `split.cross_part` 209 describes the review's 230 cross-part faces | **WEAK** — two counts for the same words, 21 apart, and neither document reconciles them |
| A9 | the 31 three-bone ties are resolved by the documented 2:1/3:0 fallback, all to weapons | **HOLDS** — 15 `weapons` + 16 `body|weapons` = 31, assigned 26 pod_r / 4 pod_l / 1 riot, and a tied vote aborts the build rather than being recorded |
| A10 | the body keeps every unowned face | **HOLDS** — body 171,391 = 299,837 − 83,944 (wheels) − 44,502 (parts); its own RBM bbox is the manifest's body bbox |
| A11 | children keep their parent (cannon / machine gun / riot → turret, everything else → body) | **HOLDS** — matches the bone hierarchy under `Batmobile_Rig_Weapons_Turret_Root` |
| A12 | the done block's supporting numbers (295 blocks, 0 mismatches, +27 KB over the pre-split 4,764) | **HOLDS** for 295 blocks and the +27 KB; the two inherited BUD-1 numbers are `read`, not re-runnable |

Net: **4 hold (A1 total, A9, A10, A11), 7 weak, 1 broken in substance (A5).** None of the findings
moves a face to a different part; they move what the card is entitled to *claim*. The dispositions
are unaffected; the next build (B-03, B-04) is affected twice — the wheels are the one group whose
pivots and face assignment deviate from the card's stated rules, and the LOD duplication eats more
than the remaining budget headroom.

---

## A1 · "0 lost faces", and what actually proves it

**Claim.** Card `Done`: *"0 lost faces vs before the split"*. MODLOG: *"Body 171,391 faces + parts
44,502 = 215,893, the full non-wheel LOD0 body (0 lost)"*; manifest `checks:
{"all_faces_accounted": true, "body_plus_parts_215893": true, "no_lost_body_faces": true}`.

**Test 1 — the total, against an artifact the cut did not write.** Sum every entry's LOD0 faces:

```
body 171,391
wheels  20,254 + 21,234 + 21,228 + 21,228 = 83,944
parts   16,923 + 754 + 5,346 + 5,035 + 4,326 + 4,298 + 346 + 346 + 428 + 428 + 6,272 = 44,502
sum                                                          = 299,837
BONES.json counts.faces_by_lod[0]                            = 299,837   (G1-11, same pskx)
```

That is the real evidence, and it holds exactly.

**Test 2 — read the three checks, not the label.** `bat_assemble.py:920-922`:

```python
"all_faces_accounted":    sum(e["faces_lod0"] for e in entries) == len(F),
"body_plus_parts_215893": body_plus == body_source_faces,
"no_lost_body_faces":     body_plus == 215_893,
```

`all_faces_accounted` is the strong one: the manifest's 16 entries must sum to the source PSKX's
own face array length — a lost face between the mesh and the manifest fails it. The other two
compare the same in-memory pair, one against a live count and one against a **hard-coded 215,893**.
The literal is a typed count in a generated record (R11), and it is a regression guard (a changed
split base fails it), but it measures nothing new: `body_plus_parts` is by construction the non-wheel
total.

**Test 3 — what catches a loss between counting and writing?** The silhouette check, and only for
12 parts (§A4).

**Verdict: HOLDS.** The 299,837 total is separately confirmed by `BONES.json` (an artifact the cut
did not write), and `all_faces_accounted` ties the manifest to the source array. Nit: `215_893` is a
typed constant — the card's own R11 rule.

---

## A2 · "for each part, take the faces owned by its bones"

**Claim.** Card `Do` step 1: *"for each part, take the faces owned by its bones, keep materials,
express vertices relative to the part pivot"*. MODLOG repeats it for the cut.

**Test — reconcile the manifest against bone ownership, computed independently.** For each part I
took its root bone from the manifest's `pivot_bone`, walked `BONES.json`'s parent/children tree,
subtracted nested part subtrees (turret contains cannon, machine gun, riot suppressor), and summed
each bone's `owned_faces["0"]`:

```
part                       bones owned LOD0  manifest  delta
batmobile_turret              44      16860     16923     63
batmobile_cannon               2        744       754     10
batmobile_machine_gun          3       5344      5346      2
batmobile_riot_suppressor      4       5013      5035     22
batmobile_missile_pod_l        6       3862      4326    464
batmobile_missile_pod_r        6       3808      4298    490
batmobile_aero_flap_l_f        2        317       346     29
batmobile_aero_flap_r_f        2        317       346     29
batmobile_aero_flap_l_b        2        409       428     19
batmobile_aero_flap_r_b        2        409       428     19
batmobile_jet                 22       5943      6272    329
parts sum owned 43026, assigned 1476
```

Every delta is positive and concentrated where the seam tables say the seams are (missile barrel/mid
809 faces, jet 329) — i.e. the parts = owned bones **+ the split faces the seam rule gave them**.
That is what the card claims, and it is consistent to the face.

**But the wheels are a different rule.** Their entry faces have nothing to do with bone ownership:

```
wheel_f_l  own bone Wheel_Front_Left_Vis owned 6,700   manifest 20,254
wheel_f_r  own bone Wheel_Front_Right_Vis owned 6,700  manifest 21,234
wheel_r_l  own bone Wheel_Rear_Left_Vis owned 7,564    manifest 21,228
wheel_r_r  own bone Wheel_Rear_Right_Vis owned 7,564   manifest 21,228
wheels: 28,528 owned -> 83,944 built  (+55,416 absorbed)
```

The build assigns a wheel every face inside the tyre circle (`Batmobile_V3_WheelArchs` /
hub-radius classification, MODLOG:5704), which takes the disc, strut, damper and fan faces with it —
`TYRES.md` §"The wheel bones" lists exactly those owners (Disc 8,198, `SUSP2_Wheel_Front_Left`
4,938, Damper 776, Fan 32, … ≈ 20.8 k per corner, matching the manifest's 20.3–21.2 k). It is a
defensible rule — it is simply **not** "the faces owned by its bones", and it is why the four wheels
hold 83,944 faces = 28 % of the car, 1.9× the 11 parts that the card is about.

**Verdict: WEAK.** The card's step is the implemented rule for 11 of 15 non-body entries; for the
four largest separate parts it is a different rule that the card does not mention, and the difference
is 55,416 faces.

---

## A3 · "Pivots are bone bind through the one transform"

**Claim.** MODLOG: *"Pivots are bone bind through the one transform"*; manifest entries carry
`pivot_bone` and `pivot_m`.

**Test.** Compare each `pivot_m` with `BONES.json`'s `pivot_jc3_m` for the named bone:

```
batmobile_turret        manifest [1.3e-05, 0.876249, 0.333226]  BONES [1.2e-05, 0.876249, 0.333240]   ok (1.4e-5)
batmobile_cannon        manifest [0.000358, 1.702446, 0.017586] BONES [0.000358, 1.702446, 0.017600]   ok
batmobile_machine_gun   manifest [-0.09166, 1.413141, 0.809727] BONES [-0.091661, 1.413141, 0.809740]   ok
batmobile_riot_supp.    manifest [0.388086, 1.563236, 0.559873] BONES [0.388085, 1.563236, 0.559886]   ok
batmobile_missile_pod_l manifest [-0.615528, 1.504646, -0.464823] BONES [...same..., -0.464810]          ok
batmobile_missile_pod_r manifest [0.615489, 1.504643, -0.464872] BONES [...same..., -0.464858]           ok
batmobile_aero_flap_*   manifest ... all match to <= 1.4e-5                                         ok (4/4)
batmobile_jet           manifest [4.9e-05, 0.542762, 1.342593]  BONES [4.8e-05, 0.542762, 1.342607]   ok
wheel_f_l               manifest [-1.208, 0.7047, -2.5699]      BONES [-1.21116, 0.70268, -2.569927] 3.2 mm / 2.0 mm
wheel_f_r               manifest [ 1.208, 0.7047, -2.5699]      BONES [ 1.210557, 0.702623, -2.570035] 2.6 mm / 2.1 mm
wheel_r_l               manifest [-1.2845, 0.7027, 2.4589]      BONES [-1.284737, 0.702692, 2.459111] ok
wheel_r_r               manifest [ 1.2845, 0.7027, 2.4589]      BONES [ 1.284904, 0.702651, 2.458708] ok
```

The 12 parts are the bone bind through `T(p)`, as claimed. The **four wheels are the station table**,
not the bone bind: `stations.json` `hub_true` is `[-1.208, 0.7047, -2.57]` / `[1.208, 0.7047,
-2.5699]` / `[-1.2845, …]` / `[1.2845, …]`, and the manifest's f_l takes f_r's `z` (`-2.5699`, not
`-2.57`) — a 0.1 mm mirror of the kind `TYRES.md` warns about for `tyre_width`.

**Verdict: WEAK.** Right result for the purpose (a wheel should spin about the station hub), wrong
sentence, and the same four entries are the ones §A2 and §A4 already flag.

---

## A4 · "reassembling **every** part at its pivot reproduces the body silhouette at ≥ 99.9 %"

**Claim.** Card `Done`. MODLOG: *"`silhouette_check.py --manifest ...` reassembles all 12 body/part
LOD1 meshes at their pivots: **coverage 0.9997** …"*. §12: *"silhouette 99.97 %"*.

**Test 1 — re-run it.** Exit 0:

```
applied the manifest offset [4.77e-07, 0.022231445, 0.154284012] to the source
reassembled 12 body/part LOD1 meshes; 215,893 source faces
frame 2400x864  source 215,893 tris  ours 40,248 tris
silhouette   source 1,131,963 px   ours 1,131,599 px   coverage 0.9997
holes        3,494 px = 0.309% of the source silhouette
of which interior tears (>=3 px inside the outline)  740 px = 0.065%
```

The number is real and reproducible.

**Test 2 — "every part".** The manifest's own `silhouette_parts` list is:

```json
["body", "batmobile_turret", "batmobile_cannon", "batmobile_machine_gun",
 "batmobile_riot_suppressor", "batmobile_missile_pod_l", "batmobile_missile_pod_r",
 "batmobile_aero_flap_l_f", "batmobile_aero_flap_r_f", "batmobile_aero_flap_l_b",
 "batmobile_aero_flap_r_b", "batmobile_jet"]
```

— 12 of the manifest's **16** entries. The four wheels are not reassembled, and they are not a minor
omission: 83,944 LOD0 faces (28 % of the car) and 4 of the 16 RBMs. A wheel placed 10 cm wrong, or a
wheel whose vertices were not made pivot-relative, would not move this 0.9997 by a pixel. The check
therefore certifies the *cut*, not the *assembly* — which is fair for the card's purpose, but the
sentence says "every part".

**Test 3 — is the LOD0 claim covered at all?** The source is the 215,893-face LOD0 split and "ours"
is 40,248 LOD1 triangles, i.e. the 0.9997 mixes decimation loss with split loss. There is no LOD0 RBM
to compare against (the build ships `body_lod1…lod5`, matching the donor's `lod1…lod5` convention),
so the geometric numerator of "0 lost faces" is never measured at LOD0.

**Verdict: WEAK.** 0.9997 HOLDS for what it measures (12 parts, LOD1); the claim as written
("every part") over-covers by the four largest separate parts.

---

## A5 · "5 LODs per part"

**Claim.** `Do` step 3 and `Done`; manifest `checks: {"five_lods_each": true, "lod_files_exist":
true}`; MODLOG *"80 RBMs: body + 4 wheels + 11 parts, **5 LODs each**"*.

**Test 1 — count.** 80 `*.rbm` files, 16 entries × 5, per-entry `lod_files` all present. HOLDS.

**Test 2 — are the five LODs five *levels*?** SHA-256 each entry's five files against each other:

```
batmobile_turret            5 LODs, 1 duplicate; sizes [211025, 43849, 26799, 25119, 25119]
batmobile_cannon            5 LODs, 3 duplicates; sizes [10290, 4578, 4578, 4578, 4578]
batmobile_machine_gun       5 LODs, 2 duplicates; sizes [62486, 17066, 11414, 11414, 11414]
batmobile_riot_suppressor   5 LODs, 1 duplicate;  sizes [60095, 13491, 9159, 7215, 7215]
batmobile_missile_pod_l     5 LODs, 1 duplicate;  sizes [54363, 18015, 14481, 12657, 12657]
batmobile_missile_pod_r     5 LODs, 1 duplicate;  sizes [54555, 18159, 14697, 12873, 12873]
batmobile_aero_flap_l_f     5 LODs, 3 duplicates; sizes [8236, 7312, 7312, 7312, 7312]
batmobile_aero_flap_r_f     5 LODs, 3 duplicates; sizes [8236, 7240, 7240, 7240, 7240]
batmobile_aero_flap_l_b     5 LODs, 3 duplicates; sizes [9334, 7642, 7642, 7642, 7642]
batmobile_aero_flap_r_b     5 LODs, 3 duplicates; sizes [9406, 7636, 7636, 7636, 7636]
batmobile_jet               5 LODs, 1 duplicate;  sizes [60439, 17089, 9799, 6367, 6367]
```

22 of the 80 files are byte-identical to another LOD of the same part — **185.8 KB of the 4,790.9 KB
budget**. The body and the four wheels do have five distinct levels; every *part* except none has at
least one duplicate, and the small parts are four copies of one mesh.

**Test 3 — what the check actually asserts.** `bat_assemble.py:927`:

```python
"five_lods_each": all(len(e["faces_per_lod"]) == 5 for e in entries),
```

It counts the length of a list in the manifest it is about to write, and `lod_files_exist` only asks
whether the named files exist. Neither can see that two of them are the same bytes, so the check is
true for four copies of one mesh exactly as for five levels.

**Test 4 — why it matters.** The remaining headroom under R9 is **124.1 KB** (4,915 − 4,790.9).
The duplicate copies alone are **185.8 KB** — 1.5× the headroom. B-03's own record already had to
borrow against this margin ("net 4,899.6 KB of 4,915 KB", MODLOG:14271), so the deduplication lever
the card never mentions is bigger than everything left on the table. The decimator is
boundary-limited on these parts (the same floor MODLOG:5688 describes for the body: "the plan's
other lever, 'trim LOD4/5', turned out not to exist"), so a duplicate is the honest output of a
decimator asked for fewer than its floor — but then "5 LODs each" is a file count, not a LOD count,
and the check should say so.

**Verdict: BROKEN in substance.** The files exist as claimed; the levels do not. This is the one
finding that costs budget rather than words.

---

## A6 · "budget 4791 KB of 4915 KB" is the Model footprint

**Claim.** MODLOG: *"`model footprint 4791 KB of 4915 KB` (green)"*; §12: *"4791/4915 KB"*; manifest
`budget: {"model_kb": 4790.9, "cap_kb": 4915.0, "hard_kb": 4915}`.

**Test 1 — does the number equal the metric?** `deploy.py:325` is
`sum(getsize(rbm_path(p,i)) for p in blocks for i in 1..5) / 1024`. Summing the 80 files:

```
body   2,405.7 KB
wheels 1,358.4 KB
parts  1,026.8 KB
total  4,790.9 KB   == manifest budget.model_kb 4790.9      (cap 4,915 -> 124.1 KB free)
```

HOLDS to the tenth of a KB, and it is the same metric the pre-split build reported (4,764 KB,
MODLOG:5704): body 3,405.0 KB → 2,405.7 KB, +1,026.8 KB of parts = **+27.5 KB**, so the split
itself costs ~27 KB (the file/block headers of 11 new parts) — worth stating, and not stated.

**Test 2 — what the number does not count.** The same entity folder in `Builds/test-091` holds
**197 RBMs totalling 8,528.1 KB** (the 42 donor part models still referenced by the parts module).
The 4,790.9 counts the *model block set* the assembly writes (16 part files), not "every model file
the vehicle ships". That is the house convention — `deploy.py` is the guard and it uses `blocks` —
so the number is defensible; but a reader of §12 ("4791/4915") will think it is the vehicle's total,
and the vehicle's folder is 78 % larger than the cap. Nothing in the card says which set is counted.

**Verdict: WEAK.** Right number, right metric, unstated scope. (The 8,528 figure also means the 4,791
cannot be checked against the game's own Model HARD by inspection — only against the project's
metric.)

---

## A7 · "the same decimation settings as the body"

**Claim.** Card `Do` step 3: *"Emit 5 LODs per part with the same decimation settings as the body."*

**Test.** The body's settings are absolute triangle targets — MODLOG:5704 records
`--body-tris 43000,6000,3000,1500,800` — while the parts' LOD counts are ratios of their own size
(a 346-face flap becomes 61/39/39/39/39; a 16,923-face turret becomes 3,142/446/215/199/199). The
realised ratios for the first two steps agree closely (turret 0.186 / 0.142 vs body 0.187 / 0.141),
which is presumably what "same settings" means — a share of the target, not the target. Then they
diverge exactly where the decimator's floor is reached (turret LOD4/LOD3 = 0.93, body 0.60).

So the sentence is true in the loose sense (same schedule shape, same floor behaviour) and false in
the literal one (the body's five targets would give a 346-face flap a 43,000-triangle LOD1). The card
does not say which.

**Verdict: WEAK** (documentation). It matters because B-04/B-05 will read "same settings" and may
re-run the pipeline with the body's absolute numbers.

---

## A8 · `split.cross_part` 209 vs the review's 230

**Claim.** Manifest `split`: `{"split_faces_total": 1701, "split_faces_body": 1683, "part_unique":
1176, "weight_resolved": 193, "ties": 31, "cross_part": 209, "body_only": 283, "unresolved": 0}`.
The review the card consumes (`SPLIT_FACES.md`): *"1,701 LOD0 split faces … **230 cross-part seams**"*,
with the breakdown `body|weapons 111`, `aero_flaps|body 96`, `body|wheel_r_r 12`, `body|wheel_r_l 11`
(= 230, verified in `by_part_pair`).

**Test 1 — do the sub-counts reconcile?**

```
1176 + 193 + 31 + 283 = 1683 = split_faces_body
1701 - 1683            =   18  faces whose bones belong to no body bone at all
 230 - 209            =   21  faces counted as cross-part by the review, not by the cut
```

**Test 2 — why the 21.** `bat_assemble.py` increments `cross_part` only for faces whose
`face_owner` set spans ≥2 *parts* **and** which are still `body_ids` at that point in the cut. The
wheel faces were already re-assigned by the hub-radius classification before this loop (A2), so a
cross-part face that the wheel rule already took is never counted. 12 (`body|wheel_r_r`) + 11
(`body|wheel_r_l`) = 23 wheel-adjacent seams; 21 of them are pre-assigned, 2 remain — which lands on
209. The arithmetic is consistent with that reading, but **neither document says it**: the manifest
reports 209 for the same words the review reports 230 for, and the card quotes neither.

**Verdict: WEAK.** Not an error, an unreconciled pair of counts (21 faces, all at the wheels) in two
artifacts a reader will compare side by side.

---

## A9 · the 31 three-bone ties

**Claim.** `Do` step 2 + review input: *"the 31 three-bone ties are 1.0/1.0/1.0 and need the
documented 2:1 or 3:0 part-level vertex fallback (all resolve to weapons)"*. MODLOG: *"26 ->
`batmobile_missile_pod_r` (16 body+pod, 10 all-pod), 4 -> `batmobile_missile_pod_l`, 1 ->
`batmobile_riot_suppressor`; 0 unresolved"*.

**Test.**

```
SPLIT_FACES.md by_part_pair ties: weapons 15, body|weapons 16, every other pair 0   -> 31
manifest split.ties 31; ties_by_part {pod_r: 26, pod_l: 4, riot_suppressor: 1}      -> 31
manifest checks all_ties_weapon true, unresolved_0 true
bat_assemble.py: the bone-weight winner is tried first (len(win)==1 -> dest), and a still-tied
part-level vote raises SystemExit("part-level vertex vote is tied") instead of recording a guess
```

The '26 = 16 + 10' split the MODLOG gives is exactly the two tie groups (16 `body|weapons`, 15
`weapons` → 10 of those 15 to pod_r, 4 to pod_l, 1 to riot). Consistent, and the failure mode is
loud, not silent.

**Verdict: HOLDS.** (One wording point: the card's `Do` step 2 says ties are closed "by assigning each
split face to the part with the larger weight" — for these 31 there is no larger weight; the
review-input paragraph supplies the real rule, so the card has both sentences and only the second is
operable.)

---

## A10 · "the body keeps every unowned face"

**Claim.** `Do` step 1. MODLOG: body 171,391 faces.

**Test.**

```
body 171,391 = 299,837 (all LOD0) - 83,944 (wheels) - 44,502 (11 parts)
body RBM local bbox (pivot [0,0,0]) min [-1.751, 0.087, -3.422] max [1.746, 2.363, 3.605]
manifest body_bbox_m                 min [-1.748, 0.091, -3.420] max [1.747, 2.362, 3.605]
```

The body's own RBM bbox equals the manifest's body bbox to ≤ 4 mm (LOD1 decimation), so the body
really does span the whole car minus the wheels and parts — it did not lose a region.

**Verdict: HOLDS.**

---

## A11 · parent links

**Claim.** MODLOG: *"children keep their parent (cannon/machine gun/riot -> turret, everything else ->
body)"*.

**Test.** Manifest: `batmobile_cannon`, `batmobile_machine_gun`, `batmobile_riot_suppressor` have
`parent: batmobile_turret`; the other 8 parts and the 4 wheels have `parent: body`; body has
`parent: null`. Independent check: `BONES.json`'s tree puts `Batmobile_Rig_Weapons_Heavy_Cannon_Barrel_01`,
`…_Machine_Gun_Root` and `…_Riot_Suppressor_Root` under `Batmobile_Rig_Weapons_Turret_Root`, and the
missile/aero/jet roots under the chassis — the same nesting the manifest records, and the same one my
subtree subtraction in A2 had to respect.

**Verdict: HOLDS.**

---

## A12 · the done block's supporting numbers

**Test.**

```
spec_check.py Working/Appearance/build_parts <sportsmuscle_body_lod1.rbm>
  -> "checked 295 blocks; spec mismatches 0; template values silently inherited 0"   exit 0
manifest blocks_per_lod summed over 16 entries = 16 + 4*5 + 23 = 59 per LOD; 59 * 5 = 295
pre-split model 4,764 KB (MODLOG:5704) -> 4,790.9 KB  = +26.9 / +27.5 KB (rounding in the source)
```

Both reproduce. Not re-runnable here: the two BUD-1 one-off runs the card inherits (the 4,764 KB
baseline and the "old two-block body chain failed spec_check at 2 vs 16" merge failure) are not
inputs on disk — only their numbers are in the MODLOG, so they are `read`, not verified, in this
pass.

**Verdict: HOLDS** for what is on disk, with the inherited numbers marked as unverified.

---

## Impact on the next cards, and the smallest honest fixes

**B-03/B-04 consume this manifest directly.** Three of its fields are narrower than they read:

1. `silhouette_parts` (12 names) is the list B-03's lamp pivot work and B-04's part placement will
   treat as "the parts" — while `entries` has 16. The wheels' pivots (A3) are the ones that were
   never silhouette-checked (A4).
2. `five_lods_each: true` is a file count. A build step that later needs KB will find 185.8 KB of
   byte-identical LOD copies and 124.1 KB of headroom; the cheapest fix is to point LOD3–5 block
   entries at the LOD2 file where the bytes are equal (or record `distinct_lods` per part so the
   check stops implying five levels).
3. `split.cross_part: 209` and the review's 230 describe the same seams 21 faces apart (A8); a
   one-line derivation in the manifest would stop the next reader re-deriving it.

**Smallest set of changes that would make the card honest** (no re-cut, no new geometry):
1. Say "the model block set (80 files)" beside 4,791 KB, and note the entity folder's 8,528 KB.
2. Add `distinct_lods` to `entries` and make `five_lods_each` count distinct levels.
3. Record the wheels' pivot source as the station table, with the 3 mm delta and the f_l/f_r `z`
   swap, or switch them to the bone bind and re-emit four RBMs.
4. Either add the wheels to `silhouette_parts` or change the sentence from "every part" to "the 12
   body/weapon/aero parts".
5. State the wheel rule ("every face inside the tyre circle", +55,416 faces over bone ownership) in
   `Do` step 1, since that is what the build does.

No game was launched; no build, save, dropzone or git state was touched. `silhouette_check.py`,
`spec_check.py` and the two scratch recomputations were run read-only and all exited 0.

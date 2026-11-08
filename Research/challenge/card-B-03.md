# Assumption challenge — backlog card B-03 (emissive `CarLight` blocks and light parts)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the B-03 card (§8), its §12 row, and the B-03 outputs and
journal sections: `Tools/scripts/bm_lights.py`, `Tools/scripts/spec_check.py` (`--lights` arm),
`Working/Appearance/build_lights/` (24 RBMs + `lights_manifest.json`),
MODLOG §"B-03 · Emissive `CarLight` blocks and light parts — done" and §"B-03 rework — done".

Read-only: no file was written except this report; no game, no `D:/Games`, no commit.
The card's own Done commands were re-run on the current tree:

```
$ python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights
CarLight: checked 24 blocks over 8 lamp parts; spec mismatches 0
EXIT=0
$ python Tools/scripts/bm_lights.py --check --fast
PASS: 8 lamp parts / 24 RBMs, 4576 Emissive faces cut, 16 lamp sockets (6 with a T-18 LightColor), 21 T-18 rows (19 mapped, 2 unmapped), 3 rig lamps with no faces; pivot-relative per parent part (6 lamps bbox-checked); model 288.6 KB lights, sum 5079.5 KB, net 4899.6 KB of 4915 KB (fast: files decoded, not re-decimated)
EXIT=0
```

Both are green. The question is what the green rests on.

## VERDICT summary

| # | Assumption | Verdict |
|---|---|---|
| B1 | PSKX material 5 is `Batmobile_V3_Emissive` (SLOTS slot 5) | **HOLDS** — the name and the 4,576 face count both agree |
| B2 | "4,576 Emissive faces **leave** the body" | **WEAK** — the cut is a plan: the body RBMs on disk still carry an emissive block, and its per-LOD count is 295/40/20/20/20 tris, not 4,576 |
| B3 | Net model **4,899.6 KB of 4,915 (green, 15 KB spare)** | **BROKEN** — the 184,158 B credit is computed from the *lamp* geometry; the body only gives back **24,474 B**, so the true net is **5,055.6 KB — 140.6 KB over the R9 hard wall** |
| B4 | Header + 16 B mid-static + texture table cloned "the only safe way"; block params undecoded | **BROKEN for the mid-static** — the donor has **39 distinct** 16 B mid-static values over its 44 light blocks (varying per family and per LOD); all 24 built blocks carry one lamp's LOD1 value |
| B5 | The texture table is the template's, so the look is unknown | **HOLDS** as a disclosed UNKNOWN (limit 3); noted: BmAK's own emissive/normal maps are never used |
| B6 | The card's Do ("write the `CarLight` block with values from T-18") is met, so `done` | **BROKEN** — the manifest itself says `t18_values_in_block: 0`, `UNKNOWN`; the Done check asserts equality with the clone and cannot see a wrong value |
| B7 | "3 rig lamps have no Emissive faces" (a rig census) | **WEAK** — the list is authored; the rig has 18 light sockets, and `BattleModeSpotLight` (T-L17/T-L21, role `light`) has no emissive faces and is not in the list |
| B8 | "3 LODs = the donor's own ladder" | **WEAK** — the generator takes the *minimum* over 13 families (8 ship 3, 5 ship 4); the donor's tail lights have a LOD4 the build omits |
| B9 | "pivot-relative per parent part (6 lamps bbox-checked)" | **WEAK** — 4 of the 6 checked lamps have pivot `[0,0,0]` (the check is an identity), and the 2 rear arches with a real pivot are skipped because their LOD1 is decimated |
| B10 | The authored parent/pivot is the frame the geometry lives in (R5) | **WEAK** — 3 of 8 lamps hang somewhere their dominant bone does not: front-left arch 594/612 faces on `Damper_Left_Front_02` but parented to the wheel; both tail strips weighted to `SUSP2_Wheel_Rear_*` but parented to the body |
| B11 | "16 sockets, 6 with a T-18 `LightColor`, 21 T-18 rows (19 mapped, 2 unmapped)" | **HOLDS** as counts; **WEAK** as an association — socket→lamp is X-sign only, nearest lamp face 0.63–1.19 m |
| B12 | "16/16 script checks" | **WEAK** — at least 9 of the 16 are construction-true or vacuous |
| B13 | Unit / coordinate convention (metres, `to_jc3_rot`, scale 0.01, offset) | **HOLDS** — manifest transform equals `stations.json` to 0.0, front −Z / rear +Z confirmed by the bboxes |
| B14 | "One CarLight block per LOD", 8 parts × 3 LODs = 24 RBMs | **HOLDS** — 24 files, one `CarLight` block each |

Overall: the **geometry** side of B-03 is sound — the material cut is real and exact (4,576 faces
partitioned 8 ways, none twice), the ONE transform is imported and reproduces the wheel-subtraction
frame, the file count and per-file block structure are as claimed, and the donor census (44 blocks,
38 with `Window`, 1,085 B header) reproduces down to the sha. What does **not** hold is the card's
economic claim and the block's content claim: the build is **over the hard model budget** once the
credit is computed from the geometry that is actually removed (B3), and the "undecoded, therefore
cloned" argument is contradicted by the donor's own 39 distinct mid-static values (B4). The card is
`done` on a Done check that only proves the clone (B6).

---

## B1 · PSKX material index 5 = SLOTS slot 5 = `Batmobile_V3_Emissive`

**The assumption (stated in the docstring).** "`SLOTS.json` slot 5 is `Batmobile_V3_Emissive`
(4,576 LOD0 faces); the PSKX `MATT0000` list is `material_0..18`, so PSKX material index 5 is that
slot." The whole cut depends on this index identity.

**Test — read the PSKX material table and count faces per material; compare with `SLOTS.json`.**

```
$ python -c "P.read_pskx(...); print(mats[:8]); print(faces per material)"
materials from PSKX: ['BatmobileV3_Wheel_V2_MIC', 'Batmobile_V3_Glass_INST',
 'Batmobile_V3_Mainbody_NEW_MIC', 'Batmobile_V3_WheelArchs_NEW_MIC',
 'Batmobile_V3_Undercarriage_NEW_MIC', 'Batmobile_V3_Emissive',
 'Batmobile_V3_Undercarriage', 'Batmobile_V3_Turret_NEW_MIC'] ... n= 19
faces per material: {0: 62668, 1: 3532, 2: 37819, 3: 42999, 4: 26150, 5: 4576, 6: 684, ...}
SLOTS slot 5: {"index": 5, "material": "Batmobile_V3_Emissive", ..., "lod0_faces": 4576,
               "assembly_block": "CarPaintMM"}
```

Both the name and the count agree, from two independently produced files (the PSKX material table
and `SLOTS.json`), and `bmak_coverage`/`spec_check` do not participate. A wrong index would have to
be wrong in two files at once with a matching face count.

**Verdict: HOLDS.**

---

## B2 · "All 4,576 Emissive faces leave the body/wheels for 8 lamp parts"

**The assumption (stated).** MODLOG: "All **4,576** `Batmobile_V3_Emissive` LOD0 faces … leave the
body/wheels for **8 lamp parts** … 4,576 / 4,576 faces accounted, none twice. The cut is recorded as
the source face-index list + sha256 … so B-04/B-05 re-emit the body/wheels without those faces."

**Test 1 — the partition itself.** The manifest's per-lamp counts sum exactly, and the generator
aborts unless every material-5 face index is used once
(`checks.every_face_once`, `lamp_faces_sum_equals_cut`, both True):

```
sportsmuscle_headlight_f_l   378   sportsmuscle_headlight_f_r   378
sportsmuscle_wheel_f_l_arch  612   sportsmuscle_wheel_f_r_arch  612
sportsmuscle_wheel_r_l_arch 1146   sportsmuscle_wheel_r_r_arch 1146
sportsmuscle_tailstrip_r_l   152   sportsmuscle_tailstrip_r_r   152
sum = 4576; clusters 6+6+11+11+14+14+14+14 = 90
```

**Test 2 — did they leave the body?** Decode B-02's body RBMs and look for the emissive material
(the block whose textures name `wheel_lights`):

```
$ python - (body_lod{1..5}.rbm, block 5)
  lod1 tris=  295 verts=  348 emissive_tex=True
  lod2 tris=   40 verts=   89 emissive_tex=True
  lod3 tris=   20 verts=   59 emissive_tex=True
  lod4 tris=   20 verts=   59 emissive_tex=True
  lod5 tris=   20 verts=   59 emissive_tex=True
body emissive total verts 614 tris 395
lamp LOD totals verts [2959, 1913, 1076] tris [3747, 2154, 1000]
```

The body on disk still has the emissive block at all five LODs; B-03 only records the face list B-04
will use. And the two sides are not the same size: the body's highest LOD carries **295** emissive
tris, while the lamp parts carry **3,747** at their LOD1. The card's own limit 7 admits the net "is an
accounting figure, not a build measurement", but not that the face counts on the two sides differ by
12.7× — which is the root of B3.

**Verdict: WEAK.** "4,576 faces accounted for, none twice" is true of the lamp files. "Leave the
body" is a plan, and the body's per-LOD representation of those faces is far smaller than the lamp
parts' (see B3).

---

## B3 · The R9 budget: "net 4,899.6 KB of 4,915 KB (green, 15 KB spare)"

**The assumption (stated).** The card's §12 evidence: "288.6 KB lights / net 4,899.6 of 4,915 KB".
The generator:

```python
lights_kb = sum(len(b) for b in files.values()) / 1024.0                 # the new lamp files
paint_bytes = sum(e["vertices_per_lod"][i] * 24 + e["faces_per_lod"][i] * 3 * 2
                  for e in entries for i in range(lods))                 # ... over the LAMPS
net_kb = b02["model_kb"] + (sum(len(b) for b in files.values()) - paint_bytes) / 1024.0
```

The credit is computed from the **lamp** entries — i.e. it assumes the body gives back exactly as
many vertices and faces as the lamps take. The bytes that actually leave the body are the body
block's own counts, which are much smaller because B-02 decimated that material's block to 295/40/
20/20/20 tris.

**Test — recompute both numbers from the files.**

```
$ python - (sizes, body emissive block per LOD, CarPaintMM strides)
CarPaintMM vb0 12 x 1179  vb1 24 x 1179  index_count 2895      # 36 B/vertex, 2 B/index
lamp verts 5948 faces 6901 lights bytes 295518                 # 288.6 KB
body emissive total verts 614 tris 395
actual freed bytes (36 B/v + 6 B/tri): 24474
  manifest 24B/v over lamp counts   credit=184158 -> net 4899.6 KB  GREEN
  actual body counts 36B/v          credit= 24474 -> net 5055.6 KB  OVER
```

4,790.9 (B-02) + (295,518 − 24,474)/1024 = **5,055.6 KB**, i.e. **140.6 KB over the 4,915 KB cap**
(R9: "Over budget = the whole entity vanishes"). Two independent errors both point the same way:

1. the credit's **geometry** is the lamp's, not the body's (184,158 B vs 24,474 B — 159,684 B of
   phantom credit);
2. the credit's **stride** is 24 B/vertex, but a `CarPaintMM` vertex is `vb0` 12 B + `vb1` 24 B =
   36 B (the 24 B is only the second stream) — that error is *in the safe direction* and would lower
   the net by another 69.7 KB, burying the first one.

The card does report the un-credited sum (5,079.5 KB), but calls the net "the operative figure". It
is operative only if the body can be charged the same face budgets the lamps were given, which
B-02's own output contradicts.

**Verdict: BROKEN.** This is a hard-wall rule (R9), the number is in §12, and the `net_model_budget_green`
check passes because it evaluates the same formula. The nearest correct figure I can derive from the
files on disk is 5,055.6 KB — over by 2.9 %, not 15 KB under.

---

## B4 · "Header, 16 B mid-static and texture table cloned — the only safe way"

**The assumption (stated).** The docstring: "Every one of the 44 vanilla `CarLight` blocks in our own
donor tree has a byte-identical 1,085 B pre-static header, so a block is authored the only safe way:
header, 16 B mid-static and the 6-name texture table are copied from a vanilla light part". MODLOG:
"the 1,085 B pre-static header, the 16 B mid-static and the 6-name texture table are **byte-identical
to the template** (that is what `spec_check --lights` proves)".

**Test 1 — the 1,085 B header over every donor light block.**

```
families 13 files 44
pre_static (len,sha16) distribution: Counter({(1085, '0f87705c32878e24'): 44})
```

All 44 identical. That half of the sentence is true.

**Test 2 — the 16 B mid-static over the same 44 blocks.**

```
mid_static sha variants: 39 distinct values over 44 files
  sportsmuscle_headlight_f_l_01_lod1  mid=(1.662, 65536.0, 65536.0, 0.0)
  sportsmuscle_headlight_f_l_01_lod2  mid=(1.652, 65536.0, 65536.0, 0.0)
  sportsmuscle_headlight_f_l_01_lod3  mid=(1.577, 65536.0, 65536.0, 0.0)
  sportsmuscle_taillight_r_l_lod1     mid=(1.318, 65536.0, 65536.0, 0.0)
  sportsmuscle_taillight_r_l_lod2     mid=(1.267, 65536.0, 65536.0, 0.0)
  sportsmuscle_taillight_r_l_lod3     mid=(1.234, 65536.0, 65536.0, 0.0)
  sportsmuscle_taillight_r_rmshswap_lod3 mid=(0.480, 65536.0, 65536.0, 0.0)
built: 24 files, distinct mid_static 1, value (1.6621, 65536.0, 65536.0, 0.0)
```

The mid-static is **not** a constant: its first float varies per family *and per LOD*, decreasing with
LOD inside each family — exactly what an intensity/fade parameter looks like. B-03 copies the head
lamp's LOD1 value (1.6621) into **all 24 blocks**, including both tail strips at all three LODs,
where the donor's own values are 1.318/1.267/1.234 (25–35 % lower) and the rear-left mshswap is 0.48.
So "cloned, therefore safe" is an assertion about a field the donor itself tabulates 39 ways, and the
card's own limit 1 ("the block's emissive colour/intensity is whatever the template's is") is true but
understates it: the four floats could be *read per family per LOD from the donor* without decoding
their semantics, and were not.

**Test 3 — the texture table.**

```
distinct texture tables over the 44 donor files: 1
  ('.../car_lights_kensington_modern_dif.ddsc', '..._nrm.ddsc', '..._mpm.ddsc',
   'a00_dummy_grey_dif_detail.ddsc', 'a00_dummy_flat_nrm.ddsc',
   '...car_lights_kensington_modern_emissive_alpha_mpm.ddsc')
```

One table for all 44 — so that part is genuinely constant. (The consequence is B5.)

**Verdict: BROKEN for the mid-static sentence.** The 16 B field is per-lamp and per-LOD data, the
clone fixes it to one donor lamp's LOD1, and `carllight_header_from_template` asserts that identity,
so nothing can catch it. `pre_static` and the texture table do hold.

---

## B5 · The texture table is the template's, so the look is unknown

**The assumption (stated).** Limit 3: "The texture table is the template's (shared
`car_lights_kensington_modern_*`). Our UVs are BmAK UVs, so the mapping from UV to that atlas is not
proven — a night look in phase Q decides it."

**Test — what the source material actually owns.**

```
SLOTS slot 5 (Batmobile_V3_Emissive) textures:
  "Emissive_Map": "Engine.Batmobile_V3_Wheel_E",
  "Normal_Map": "Textures.Batmobile_V3_Wheel_Lights_N",
  "Material_Separation_Mask": "Textures.Batmobile_V3_Wheel_Lights_M", ...
manifest.material: {"index": 5, "name": "Batmobile_V3_Emissive", "faces_lod0": 4576}
manifest.template.textures: the six Kensington car_lights paths
```

The built blocks sample the **donor Serpente's** light atlas, not `Batmobile_V3_Wheel_E`; the
manifest's `material` block names the material whose faces were cut, not the material the lamp is
rendered with. The UNKNOWN is disclosed, and the UV mismatch is disclosed, so this is a known-unknown
rather than a hidden one — but the name `Batmobile_V3_Emissive` next to the block is a reading of the
encoder's intent, not the file's content (R5: a member read by its name).

**Verdict: HOLDS** as a disclosure (the limit is explicit), **WEAK** in the manifest's naming, which a
later card could read as "the lamp uses Batmobile_V3_Emissive".

---

## B6 · The card's Do step is met, so `done`

**The assumption (silent).** §12: `| B-03 | done | … 24/24 CarLight blocks byte-identical to the
cloned header …`. The card's Do says: "for each lamp … **write the `CarLight` block with values from
T-18**", and the Done says: "`spec_check.py` passes on every new block; a `GEOMETRY.md`-style decode of
the written block round-trips."

**Test 1 — what the manifest says about T-18 values.**

```
manifest.block_values = {"t18_values_in_block": 0, "status": "UNKNOWN",
  "why": "… the header/mid-static/texture table are cloned byte-exact from the template and no T-18
          number is written into the block; the card's Do step 'write the CarLight block with values
          from T-18' is therefore NOT met and stays UNKNOWN rather than guessed"}
```

**Test 2 — are the T-18 colours even available to be written?** Yes, for 6 of 16 sockets, and they are
recorded but nowhere used:

```
HeadLight1   colour=[138,197,246,255]  rows=[T-L8,T-L11,T-L18,T-L22]  nearest face 0.0077 m
HeadLight2   colour=[160,180,255,0]    rows=[T-L9,T-L12,T-L19,T-L23]  nearest face 0.003  m
LWheelLight  colour=[160,180,255,0]    nearest face 0.7924 m
RWheelLight  colour=[160,180,255,0]    nearest face 0.7522 m
BrakeLightL  colour=[255,38,0,0]       nearest face 0.6303 m
BrakeLightR  colour=[255,38,0,0]       nearest face 0.6281 m
sockets 16, with colour 6
```

**Test 3 — can the Done check see a wrong value?** `check_lights()` compares `blk.pre_static`,
`blk.mid_static` and `blk.textures` **to the template** (the same file the generator cloned). Its
spec is the clone; a lamp with the wrong colour passes by construction. It is a valid byte-level
round-trip and a valid directory-completeness check (the rework's addition), not a light-value check.

**Verdict: BROKEN** for "the card's Do is met". The card is `done` because its Done criterion is
satisfiable by cloning a block whose parameters the card explicitly did not write. The UNKNOWN is
recorded honestly, which keeps the output R4-compliant in spirit, but §12's evidence line leads with
"24/24 CarLight blocks byte-identical to the cloned header" — a measurement of the substitution, not
of the requirement.

---

## B7 · "Three rig lamps have no Emissive faces"

**The assumption (stated).** The docstring: "Light components the rig carries that the Emissive
material gives NO faces. Each row is measured (distance to the nearest lamp face) rather than
assumed." MODLOG: "**Three rig lamps have no Emissive faces at all** (measured, not assumed):
`Dashboard_Light` 1.5565 m …, `BootLight` 1.5827 m …, `Headlight_Centre` 0.3909 m".

**Test — enumerate the rig's light sockets from `SOCKETS_JC3.json` and subtract what B-03 covers.**

```
SOCKETS_JC3 light/role=light sockets (18):
 BattleModeSpotLight, BootLight, BrakeLightL, BrakeLightR, Dashboard_Light,
 HeadLight1, HeadLight1a, HeadLight1b, HeadLight2, HeadLight2a, HeadLight2b,
 Headlight_Centre, LWheelLight, LWheelLight_bottom, LWheelLight_top,
 RWheelLight, RWheelLight_bottom, RWheelLight_top
hosted by B-03 (14 of those 18) + BrakeTrailL/BrakeTrailR (not lamps) = 16 sockets
NO_FACE = Dashboard_Light, BootLight, Headlight_Centre
unaccounted: BattleModeSpotLight
  {"socket": "BattleModeSpotLight", "bone": "Batmobile_Rig_Weapons_Drone_Decoder",
   "role": "light", ...}
  t14 rows for BattleModeSpotLight: T-L17 (battle-spot, graph object Front_Secondary_Head),
                                    T-L21 (forensics)
```

`BattleModeSpotLight` is a light socket, it has no material-5 faces (its light is a graph object on
the drone-decoder bone), and it appears in neither the hosted list nor `NO_FACE`. The card serves
APP-4/LGT-1, so leaving LGT-2's battle spotlight for another card is defensible — but the comment and
the MODLOG sentence present the three as the rig's complete no-face set, and they are not.

Also, the `no_face_lamps_measured` check only asserts `nearest_lamp_face_m > 0`, which any socket
passes because the socket point is not a lamp vertex — it cannot detect a lamp whose faces are 1 mm
away. The distances are real measurements; the *check* does not test the claim.

**Verdict: WEAK.** 3 is a hand-authored subset of a rig with at least one more light-shaped socket
without faces; the measurement wording ("no Emissive face lies within this distance") is honest, the
census wording ("Light components the rig carries that … gives NO faces") is not complete.

---

## B8 · "3 LODs per lamp — the donor's own ladder"

**The assumption (stated).** MODLOG: "The LOD ladder is the donor's own: the three LODs every donor
lamp mesh reaches (head lamps ship lod1..lod3)"; manifest `lod_ladder.what`: "the fewest LODs any donor
light family ships … only the levels every family shares are kept".

**Test — census the donor light families' LODs.**

```
families 13 files 44
lods distribution Counter({3: 8, 4: 5})
headlight_*  families: [1,2,3]   taillight_* families: [1,2,3,4]
max tris per lod: {1: 244, 2: 108, 3: 50, 4: 28}
manifest: {"lods": 3, "triangles_per_lens": [244, 108, 50], "census": {"family_lods": {"3": 8, "4": 5}}}
```

The rule is `keep = min(family_lods) = 3`, so "the donor's own ladder" is really the donor's
*floor*: 5 of 13 families ship a fourth LOD (28 tris) that the build omits. Combined with B2 (the body
has 5 LODs and will lose the emissive faces at LOD4/5 when B-04 runs), the tail lamps will have no
geometry at the two furthest LODs while their donor counterparts do. That consequence is nowhere
stated.

Also `checks.lod_budget_within_vanilla_ladder` is true by construction — the budgets *are*
`min(len(faces), cap × elements)`.

**Verdict: WEAK.** The floor is measured and disclosed in the census; the phrase "the donor's own
ladder" overstates it, and the LOD4/5 consequence is unstated.

---

## B9 · "pivot-relative per parent part (6 lamps bbox-checked)"

**The assumption (stated).** §12: "vertices pivot-relative per parent part (`pivot_m` + `part_index`
42/43 recorded for B-04)". Summary: "pivot-relative per parent part (6 lamps bbox-checked)".

**Test — which lamps the check actually covers.**

```
pivot_check: {'lamps_checked': 6, 'why': "… compares LOD1's absolute bbox (vertices + pivot) with the
source faces' bbox for the lamps whose LOD1 kept every face; a lamp whose LOD1 is decimated is not counted"}
headlight_f_l   pivot [0,0,0]              faces [378,324,150]  -> checked
headlight_f_r   pivot [0,0,0]              faces [378,324,150]  -> checked
wheel_f_l_arch  pivot [-1.208,0.7047,-2.5699] faces [612,323,150] -> checked
wheel_f_r_arch  pivot [ 1.208,0.7047,-2.5699] faces [612,323,150] -> checked
wheel_r_l_arch  pivot [-1.2845,0.7027,2.4589] faces [731,324,150] -> NOT checked (731 < 1146)
wheel_r_r_arch  pivot [ 1.2845,0.7027,2.4589] faces [732,324,150] -> NOT checked (732 < 1146)
tailstrip_r_l   pivot [0,0,0]              faces [152,106,50]  -> checked
tailstrip_r_r   pivot [0,0,0]              faces [152,106,50]  -> checked
```

4 of the 6 "checked" lamps have pivot `[0,0,0]`, where the check reduces to "the bbox equals itself";
the 2 lamps with a non-zero pivot that are skipped are exactly the rear arches, whose LOD1 is
decimated below the source face count. So the check certifies **2** of the 4 wheel-parented lamps and
none of the 2 whose pivot is largest.

**Verdict: WEAK.** The pivot arithmetic is right (the manifest's `bbox_body_m` equals the source bbox
for the front arches, `pivot + vertices`), but "6 lamps bbox-checked" is 4 identities + 2 real checks.

---

## B10 · The authored parent is the frame the geometry lives in (R5)

**The assumption (silent).** The `LAMPS` table's `parent` (donor part index → B-02 part → pivot) is
authored; the docstring admits it ("The lamp table itself … is an authored input"), and the only
verification is `pivot_applied_exactly` (arithmetic) and `socket_side_matches_lamp` (X sign).

**Test — compare each lamp's authored parent with the bones its faces are weighted to** (both are in
the manifest).

```
headlight_f_l    parent body       bones Batmobile_Nose_Mesh 378                     (agree: nose is body)
headlight_f_r    parent body       bones Batmobile_Nose_Mesh 378                     (agree)
wheel_f_l_arch   parent wheel_f_l  bones Damper_Left_Front_02 594, Wheel_Frnt_Left_Disc 18   (594/612 body-side)
wheel_f_r_arch   parent wheel_f_r  bones Wheel_Frnt_Right_Disc 612                   (agree)
wheel_r_l_arch   parent wheel_r_l  bones Wheel_Rear_Left_Disc 1146                   (agree)
wheel_r_r_arch   parent wheel_r_r  bones Wheel_Rear_Right_Disc 1146                  (agree)
tailstrip_r_l    parent body       bones SUSP2_Wheel_Rear_Left 152                   (suspension, not body)
tailstrip_r_r    parent body       bones SUSP2_Wheel_Rear_Right 152                  (suspension, not body)
```

The two front arches are the same geometry mirrored (bboxes −1.271…−1.145 vs +1.145…+1.271), yet
their weights are not: the left is 97 % on a **damper** bone, the right 100 % on the **wheel disc**.
B-03 parents both to the wheel, so either the left lamp will spin with the wheel although BmAK
weighted it to the suspension, or the right side's weights are the odd ones. The tail strips are
weighted to rear suspension bones and parented to the body, which is the opposite choice. Which is
right depends on what those BmAK bones do — not decidable from the files on disk, so the honest
answer is UNKNOWN, but the manifest carries both facts side by side and does not flag the
disagreement.

**Verdict: WEAK.** The parent table is disclosed as authored and the bones are recorded, so nothing is
hidden; what is missing is the R5 step — choosing the parent from the weights rather than from the lamp
name/geometry position, or recording the three disagreements as UNKNOWN.

---

## B11 · "16 sockets, 6 with a T-18 LightColor; 21 T-18 rows (19 mapped, 2 unmapped)"

**The assumption (stated).** §12 and the summary.

**Test — count from the manifest; measure the socket→lamp distance.**

```
sockets 16, with colour 6
t18_hosting: rows_hosted_count 21; rows_hosted_mapped 19; rows_hosted_unmapped [T-L22, T-L23];
             rows_in_t18_map_not_hosted [T-L17, T-L24, T-L35]
nearest_lamp_face_m: HeadLight1 0.0077, HeadLight2 0.0030, LWheelLight 0.7924,
                     RWheelLight 0.7522, BrakeLightL 0.6303, BrakeTrailL 1.1871
```

The counts are exact and the "19 mapped / 2 unmapped" split is honest about T-L22/T-L23 being
outside T-18's own part map. The association, though, is X-sign only — the rework says so ("the four
brake/trail sockets sit 0.63–1.19 m inboard of the corner strips, so the new check tests the side
sign"). A lamp "hosting" a light 1.19 m away is a claim about the intended wiring, not a measured
coincidence.

**Verdict: HOLDS as counts, WEAK as an association** (disclosed in the rework).

---

## B12 · "16/16 script checks"

**The assumption (stated).** MODLOG: "Its own 12 checks are all PASS" (now 16 after the rework).

**Test — classify each check by what it can fail on.**

```
checks 16
faces_total_4576                 compares PSKX material-5 face count to SLOTS lod0_faces   independent
lod_budget_within_vanilla_ladder budgets are defined as min(faces, cap*elements)           construction-true
every_face_once                  assign() already aborts unless this holds                 construction-true
lamp_faces_sum_equals_cut        same partition                                            construction-true
lods_each_3                      the loop writes 3 files                                    construction-true
lod_files_unique                 dict keyed by file name                                    construction-true
carllight_header_from_template   the clone is the spec                                      construction-true
roundtrip_byte_identical         same writer and reader                                     self-consistency
pivot_applied_exactly            real, but 4 of 6 are pivot [0,0,0] (B9)                    weak
socket_side_matches_lamp         X sign only, 0.63–1.19 m gaps (B11)                        weak
t18_rows_exist                   referential                                                independent
t18_sockets_exist_in_jc3         referential                                                independent
net_model_budget_green           evaluates the formula in B3                                encodes the error
sum_equals_parts                 same array, summed twice                                   construction-true
no_face_lamps_measured           only `nearest > 0`, which any socket passes                 vacuous
no_face_lamps_not_hosted         real                                                       independent
```

Four checks are independent of the generator's own inputs (`faces_total_4576`, the two referential
ones, `no_face_lamps_not_hosted`); the rest are construction-true, self-referential, weak, or — in
`net_model_budget_green` — the carrier of the B3 error.

**Verdict: WEAK.** "16/16" is a true count of true statements; the rework removed four tautologies and
several of the same class remain.

---

## B13 · Unit and coordinate convention

**The assumption (silent).** Positions are metres in the JC3 frame, produced by the ONE transform
`to_jc3_rot(p) × 0.01 + offset` (R2), expressed in the parent part's pivot frame.

**Test.**

```
stations.json: scale 0.01 offset [-4.76837158203125e-07, 0.02223144531250008, 0.15429743957519537]
manifest:      scale 0.01 offset [-4.77e-07, 0.022231445, 0.15429744]
offset difference: [-0.0, -0.0, 0.0]
head lamp bbox  [-0.478, 0.503, -3.050] .. [-0.356, 0.721, -2.965]
tail strip bbox [-1.487, 0.670, +3.255] .. [-1.103, 0.783, +3.340]
body length 7.026 m (DIM-1); wheel stations front z -2.570, rear z +2.459
```

Front is −Z (head lamps at −3.05, tail strips at +3.34), X is lateral with left = −X (matching the
wheel pivots −1.208 / +1.208), Y is up (0.50–1.26 m, head height), and the offset matches
`stations.json` exactly. `bm_lights.py` imports `bat_assemble` and calls `BA.to_jc3_rot`; it does not
use `psk2rbm.to_jc3` (the older reflection) for vertices.

**Verdict: HOLDS.** R2 satisfied and the frame convention is consistent with DIM-1 and BONES.

---

## B14 · "8 lamp parts × 3 LODs = 24 RBMs, one `CarLight` block each"

**Test.** `Working/Appearance/build_lights/` holds 24 `*.rbm` plus the manifest; every file decodes to
exactly one block named `CarLight`; `spec_check --lights` reports "checked 24 blocks over 8 lamp
parts"; the directory holds exactly the manifest's file set (rework check).

**Verdict: HOLDS.**

---

## What would change the verdicts

1. Recompute the credit from the body block that actually loses the faces (per LOD: 295/40/20/20/20
   tris, 614 verts over 5 LODs) and at 36 B/vertex — the build is ~5,055.6 KB and over R9; either
   reduce the lamp LOD budgets / `lamp_elements`, or make B-02's body decimation consistent with the
   lamp budgets (B3).
2. Clone the 16 B mid-static per family and per LOD from the matching donor light block, or record it
   as a per-lamp UNKNOWN instead of a single clone (B4).
3. Copy the T-18 colour block per socket when the parameters are eventually decoded; until then, stop
   citing "24/24 byte-identical" as the completion evidence (B6).
4. Add `BattleModeSpotLight` (and any other light-role socket with no faces) to `NO_FACE`, and derive
   the list from `SOCKETS_JC3.json` instead of typing it (B7).
5. Take the parent from the face weights (or record the 3 mismatches as UNKNOWN) before B-04 wires
   `parent_space_offset` (B10).

Every quoted output came from the current tree on 2026-10-30. No game was launched, no file outside
this report was written, nothing was committed.

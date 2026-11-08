# Assumption challenge — backlog card B-07 (lights module rewrite)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14), the B-07 card (§8, lines 1055–1059), its §12 row
(line 1342), and the card's result and outputs: `Tools/scripts/bm_lightrig.py`,
`Working/Lights/bm_lightrig.json`, `Builds/bm-007/` (aaf, `.ee`, `.toc`, `receipt.json`,
`install.ps1`), MODLOG §"B-07 start" (18253) and §"B-07 — done" (18448).

Read-only review. Nothing was modified except this file. No game was launched, nothing was
written to `D:/Games` or `E:/Games`, no archive was internalised, no commit, no secret read.
The card's own `--check` and tamper tests were **not** re-run because they write into
`tmp/b07/`; the Done line was instead re-derived in memory from the packed artefact with the
card's own decoders (`eetoc.unaaf` → `sarc_dir` → `bm_lightrig.decode_module_bytes` →
`decode_parts`), and the inputs were re-read from disk.

---

## VERDICT summary

| # | Assumption | Verdict |
|---|---|---|
| A1 | The Done line "18/18 entries name a part that exists with `has_lights = 1`" | **HOLDS** — 18 rows, 7 parts, every index/name/flag matches, read back from the `.ee` |
| A2 | A row that names a lamp part also puts the light at that lamp (behaviour, not member, R5) | **BROKEN** — 10 head rows share one bone 0.713 m from either lens; tail rows 2.731 m from their strips |
| A3 | The 18 rows place 18 distinct lamps | **BROKEN** — 7 distinct anchors, 10 rows on `Winch_DOOR_Mesh_LIG`, 2 on `Batmobile_Chassis_LIG` |
| A4 | The headlamp left/right assignment (`HeadLight1→f_l`, `HeadLight2→f_r`) | **BROKEN** — BmAK `HeadLight1` computes to JC3 x `+0.452` (right lens), `HeadLight2` to `−0.386` (left); all 10 head rows are mirrored |
| A5 | The `_LIG` anchor chain resolves and carries the socket offset | **WEAK** — disclosed as UNKNOWN, but no `_LIG` node exists in BONES/parts (0 of 180), and no offset is stored; only the bone origin is buildable |
| A6 | The installable `.ee` carries B-05's graph and the 6 custom `SVehicleLight` objects | **BROKEN** — the packed `.epe` is bm-009's 105,430 B graph; B-05's is 124,520 B; the custom objects exist only in the loose aaf `.epe`, which `install.ps1` never copies |
| A7 | The 10 dropped behaviours are gone from the car | **WEAK** — gone from the module; the packed graph still carries `Front_Left_Turn`, `Rear_Left_Reverse`, `Rear_Brake`, `Front_Primary_Head`, … and which list renders is UNKNOWN |
| A8 | `has_lights = 1` proves the binding is honoured | **WEAK** — G2-33 §4: the flag is artist-set, not loader-enforced (6 fleet entries on flag-0 parts, 13 lit parts with no entry) |
| A9 | The only lit parts without an entry are the 2 rear arches | **BROKEN** — the built parts module has **13** such parts; the 11 donor lamp parts the rows used to name are still live, lit and inside the `.ee` |
| A10 | Leaving the rear arches unmanaged is a vanilla pattern (13 of 2,073) | **WEAK** — the count reproduces, but G2-33 calls those exceptions; the rear arches are themselves carriers (1,146 emissive faces each) |
| A11 | "The BmAK rig has no indicator, reverse lamp or central high beam" | **HOLDS** for the rig census (4 packages, 0 signal/reverse sockets), but it is a socket census, not a lamp census |
| A12 | `Front_Primary_Head` has no possible host (nearest face 0.3909 m) | **BROKEN as evidence** — 0.3909 m is the measured nearest distance (a post-hoc threshold), and the card hosts three rows on the body; the decision is defensible for another reason |
| A13 | Keeping the dashboard donor row's `HeadLight` behaviour is correct | **BROKEN** — T-18 maps `Dashboard_Light`/`VEHLT_Interior` to `TailLight`; the built row is `HeadLight`, so the dash is on the headlight circuit |
| A14 | The 6 custom rows can safely reuse the `lights[2]` (`Dash_Light`) recipe | **BROKEN** — 84 cells labelled `decoded`; the battle head gets range 2 / angle 10 / type 0 where the same module's head rows use 30 / 40 / 1, and BmAK's battle head is radius 1024 cm, cone 10/35 |
| A15 | The 450-cell provenance counts (`360 decoded … 0 assumed`) are accurate | **WEAK** — counts reproduce, but 187 `decoded` cells are "kept from the shipped row" (a single-instance `read`), and 84 more are the borrowed recipe (`class`, not `decoded`) |
| A16 | Range/angle/multiplier need no conversion (disclosed UNKNOWN) | **WEAK** — values unchanged; but a 30 range / 40° head row against BmAK's 6000 cm / 70° and a 2 / 10 battle row are unbridged consequences |
| A17 | `aafdiff` vs bm-005 is exactly 1 file, shared modules byte-identical | **BROKEN on the current tree** — it is 2 files: the module and the `.epe` (124,488 → 124,520); bm-005 was regenerated at 06:16, after bm-007 was built at 04:33 |
| A18 | The packed `.ee` differs from bm-009 in exactly 1 inner file | **HOLDS** — 685 unpacked files, 1 changed (the lights module); sha/toc record match |
| A19 | 21 shipped rows → 11 kept + 10 dropped + 7 added; kept members are unchanged | **HOLDS** — base is 21 rows, every kept row's non-part/anchor/colour member is byte-equal |
| A20 | `preset_id = 0` self-describes; a non-zero preset does not override the row | **WEAK** — preset-0 self-description holds (G2-33 §6.3); the 12 non-zero rows rest on preset semantics that the card itself lists as UNKNOWN |

**Overall.** The literal Done line is true and reproducible: 18 rows, 7 lamp parts, every
`part`/`part_index`/`has_lights` resolves in the packed artefact. But the result is a
**part-binding** result, not a light-rig result. The module places 10 of its 18 entries on
one bone (`Winch_DOOR_Mesh_LIG`) that is 0.713 m from either head-lamp lens, anchors the two
brake rows 2.731 m forward of their strips, and mirrors every headlamp left/right. The
installable `.ee` carries bm-009's graph, not B-05's, so the 6 custom rows have no
`SVehicleLight` object in the delivered build. And the "only two unmanaged lit parts" claim
is false: there are 13, including the 11 donor lamp parts whose rows B-07 thought it had
moved off. The card should not be `done` on the present Done line; the line needs at least
"the anchor resolves in the named part's rig and the lamp pair is not collapsed".

---

## A1 · The Done line: 18/18 entries name a part that exists with `has_lights = 1`

**The assumption (stated, §8 and §12).** "every entry names a part that exists with
`has_lights = 1`."

**Test — decode the module from the aaf and the part table, in memory.**

```
$ python - <<'PY'   # bm_lightrig.decode_module_bytes / decode_parts
module bytes 5745 rows 18
parts 59
0 HeadLight sportsmuscle_body 0 -> sportsmuscle_body has_lights 1
1 TailLight sportsmuscle_tailstrip_r_r 49 -> sportsmuscle_tailstrip_r_r has_lights 1
2 HeadLight sportsmuscle_headlight_f_l 44 -> sportsmuscle_headlight_f_l has_lights 1
…
17 TailLight sportsmuscle_body 0 -> sportsmuscle_body has_lights 1
```

The same read against the **packed** `.ee` (not the aaf copy) gives the same 18 rows; the
module inside the `.ee` is byte-identical to the aaf's, the `.toc` record is
`(16499616, 5745)` and the SARC entry agrees:

```
module bytes 5745 rows 18
parts 59
ee size 11180088 sha B953E20CD76E3C936F398851D4C0225798C1A5BE02606D536FD2C3D5E5C836B4
toc records 605 module rec (16499616, 5745)
sarc files 703 module sarc (16499616, 5745)
```

Distinct parts used: 7 (`body`, `headlight_f_l`, `headlight_f_r`, `tailstrip_r_l`,
`tailstrip_r_r`, `wheel_f_l_arch`, `wheel_f_r_arch`). All 7 exist at the stated indices and
all carry `has_lights = 1`.

**Verdict: HOLDS**, as the literal Done line. It proves the row→part binding, not the
light's behaviour; see A2/A3.

---

## A2 · A row that names a lamp part puts the light at that lamp

**The assumption (silent, and required by R5 "behaviour before member").** Because the
entry's `part` is `sportsmuscle_headlight_f_l`, the headlamp behaviour is carried by that
part. The card checks the `part` field only.

**Test — compare the anchor bone's JC3 position with the lamp part's measured bbox.** The
module carries no offset member (22 fields: `behavior … preset_id`, `Research/JC3Grab/
LIGHT_SYSTEM.md` §1 and the built type definition), so `deformable_transform` is the only
position carrier. For each row, take the anchor's bone pivots from `BONES.json`
(`pivot_jc3_m`, already through `to_jc3_rot`) and the lamp bbox from B-03's manifest
(part-frame, so add `pivot_m`):

```
sportsmuscle_headlight_f_l      part_centre [-0.417 0.612 -3.007] bone [-0.000 1.137 -2.764] dist 0.713 m
sportsmuscle_headlight_f_r      part_centre [ 0.417 0.612 -3.007] bone [-0.000 1.137 -2.764] dist 0.713 m
sportsmuscle_tailstrip_r_l      part_centre [-1.295 0.726  3.298] bone [-0.885 1.227  0.645] dist 2.731 m
sportsmuscle_tailstrip_r_r      part_centre [ 1.294 0.726  3.298] bone [ 0.885 1.227  0.645] dist 2.731 m
sportsmuscle_wheel_f_l_arch     part_centre [-1.208 1.003 -2.974] bone [-1.211 0.703 -2.570] dist 0.503 m
sportsmuscle_wheel_f_r_arch     part_centre [ 1.208 1.003 -2.974] bone [ 1.211 0.703 -2.570] dist 0.503 m
```

The two brake rows are anchored to `SUSP2_Wheel_Rear_*`, whose `pivot_jc3_m` is
`(±0.885, 1.227, 0.645)`; the tail strips sit at z `3.298`. That is the BmAK brake socket's
own offset: `LIGHTS.json` `BrakeLightL.socket_location = [-273.69, -40.90, -15.19]` cm — the
socket is 2.7 m from the bone, and the module cannot express that offset. The same is true,
smaller, for the head sockets (`[21.29, 45.19, -44.25]` cm).

The card's limit 1 acknowledges "whether that chain resolves inside a light part is the §112
probe", but not that the chain is a **bone**, not the socket, and that the bone is 0.5–2.7 m
from the lens.

**Verdict: BROKEN.** Naming the part does not place the light; the row's only position
carrier is 0.713 m (head) / 2.731 m (brake) from the lamp it names, or 0.503 m (arch).

---

## A3 · The 18 rows place 18 lamps (distinct anchors)

**The assumption (silent).** "18 rows" is treated as 18 lamp behaviours, including four
left and four right head rows and two battle heads.

**Test — count distinct `deformable_transform` values in the built module.**

```
distinct anchors: 7
2 |sportsmuscle_LOD1|body|Batmobile_Chassis|Batmobile_Chassis_LIG
1 |sportsmuscle_LOD1|body|SUSP2_Wheel_Rear_Right|SUSP2_Wheel_Rear_Right_LIG
10 |sportsmuscle_LOD1|body|Winch_DOOR_Mesh|Winch_DOOR_Mesh_LIG
1 |sportsmuscle_LOD1|body|SUSP2_Wheel_Rear_Left|SUSP2_Wheel_Rear_Left_LIG
1 |sportsmuscle_LOD1|body|Batmobile_Rig_Weapons_Drone_Decoder|Batmobile_Rig_Weapons_Drone_Decoder_LIG
2 |sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|Wheel_Frnt_Left_Disc_LIG
1 |sportsmuscle_LOD1|wheel_f_r|Wheel_Frnt_Right_Disc|Wheel_Frnt_Right_Disc_LIG
```

Ten rows — every L/R head lamp (T-L8, T-L9, T-L11, T-L12) plus both battle heads (T-L18,
T-L19) — share one node. The BmAK sockets on that bone are not coincident:

```
HeadLight1 HeadLight2    85.72 cm; same bone? True
HeadLight1a HeadLight2a  87.23 cm; same bone? True
HeadLight1b HeadLight2b  80.47 cm; same bone? True
```

T-18's own challenge already found this (`card-T-18.md` A7: "12 entries share one anchor
node"). B-07 inherits it and increases the concentration: 10 of 18 rows on one point.

**Verdict: BROKEN.** "One beam per side on the road" (T-18's verify cell for these rows)
cannot be produced by a single node, and no L/R separation exists in the built row set.

---

## A4 · The headlamp left/right assignment

**The assumption (silent).** T-18/B-07 map socket `HeadLight1` (T-L8/T-L11/T-L18) to
`sportsmuscle_headlight_f_l` and `HeadLight2` (T-L9/T-L12/T-L19) to `…_f_r`.

**Test 1 — the BmAK material type, an independently decoded field.**

```
HeadLight1  mat=VEHLTMAT_HeadLightRight  bone=Winch_DOOR_Mesh  loc=[21.286633, 45.192657, -44.25]
HeadLight2  mat=VEHLTMAT_HeadLightLeft   bone=Winch_DOOR_Mesh  loc=[28.216906, -38.593201, -61.0]
BrakeLightL mat=VEHLTMAT_TailLightLeft
BrakeLightR mat=VEHLTMAT_TailLightRight
```

For the brakes, the material side and the socket side agree; for the headlights, the
material says `HeadLight1` is the Right lamp.

**Test 2 — put the socket offsets through the project's one transform (R2).** The bone's
bind transform from `BONES.json`:
`world_position_cm = [291.847751, 0.0244, 111.431369]`,
`world_rotation_quat ≈ [0, 0, 0, −1]` (180° about Z). Rotate the local socket, then apply
`to_jc3_rot = (−y, z, −x) × 0.01`:

```
HeadLight1 world cm [270.56, -45.16, 67.18] jc3 m [ 0.4516, 0.6718, -2.7056]
HeadLight2 world cm [263.63,  38.62, 50.43] jc3 m [-0.3862, 0.5043, -2.6363]
left lamp bbox  x [-0.4781, -0.3559]  y [0.503, 0.7212]
right lamp bbox x [ 0.3559,  0.4781]  y [0.503, 0.7212]
```

`HeadLight1` lands inside the **right** lens bbox (x +0.452); `HeadLight2` inside the
**left** (x −0.386). B-07 has them the other way round on all ten head rows (rows 2,3,4,5,
6,7,9,10,14,15). B-03's hosting note (`card-B-03.md` B11) already says the socket→lamp
association is X-sign only; this is the same inference, and it is inverted.

**Verdict: BROKEN.** Two independent decoded signals (material type and the R2 transform)
agree that `HeadLight1` is the right lamp; the build puts it on `f_l`.

---

## A5 · The `_LIG` anchor chain resolves

**The assumption (disclosed as limit 1 / spec `unknowns[0]`).** "the anchor chain
(`deformable_transform`) resolving inside a non-rigged part is the §112 probe — B-07 writes
T-18's decoded socket chain unchanged."

**Test — does any built rig contain the node?**

```
$ python - (BONES.json)
bones 180 _LIG 0
parts_manifest _LIG count 0, Winch 0, Nose 0
```

`Research/JC3Grab/LIGHT_SYSTEM.md` §6 already states the node is "not in the RBM, not in the
parts `bones` array and not in the deform table". So the chain names a node that the build
does not author. If the game synthesises it at the bone, A2/A3's distances apply; if it does
not, the entries have no position at all. Either way the module carries no per-socket
offset, and the BmAK socket offset (2.73 m for the brakes) has no home.

**Verdict: WEAK** — honestly disclosed, but the disclosure says "resolving inside a
non-rigged part"; it does not say "the only resolvable point is 0.5–2.7 m from the lens, and
ten rows share it". The card's Done line cannot see this.

---

## A6 · The installable `.ee` carries the B-05 graph the card depends on

**The assumption (stated as the pack choice, limit 4).** B-07's dependency is B-05; the
build is "aaf copied from bm-005, the rebuilt loose `.epe`", and "packed `.ee`/`.toc`".

**Test — compare the `.epe` inside bm-007's `.ee` with B-05's and with the aaf.**

```
bm-009 packed epe 105430 1778816d26ce5505
bm-007 packed epe 105430 1778816d26ce5505
bm-005 aaf epe  124488 f4abe91da0bc3ce3
bm-007 aaf epe  124520 d118c0aa29167a5e
```

The packed graph is bm-009's (base `bm-002` per its receipt), not B-05's. The six custom
`SVehicleLight` objects B-05 added exist only in the loose aaf `.epe`:

```
aaf .epe strings include: headlight_battle_left_light, headlight_battle_right_light,
  sportsmuscle_wheel_f_l_arch_light, …_f_r_arch_light, …_f_l_arch_battle_light,
  boot_light_light
packed .epe strings include: none of those
```

And `install.ps1` copies only the `.ee` and `.toc`:

```powershell
Copy-Item ... 'v0300_..._civilian_01.ee'      -Destination $EeT       -Force
Copy-Item ... 'v0300_..._civilian_01.ee.toc'  -Destination ($EeT+'.toc') -Force
```

So the delivered build has six module rows (`preset_id = 0`) with no matching graph object,
and none of B-05's other graph work. If the renderer reads the graph, those six rows do
nothing. Limit 4 says this, but the §12 row and the Done line still treat the build as the
B-05 state.

**Verdict: BROKEN** for the delivered artefact (disclosed, but the result rests on it).

---

## A7 · The 10 dropped behaviours are gone from the car

**The assumption (stated).** "10 shipped rows dropped with measured reasons (2 tail points,
1 orphan `Rear_Brake` preset, 4 indicators + 2 reverse …, `Front_Primary_Head` …)."

**Test — read the presets' names out of the packed graph.** The `.epe` inside bm-007's
`.ee` still contains:

```
Front_Left_Turn, Front_Right_Turn, Rear_Left_Turn, Rear_Right_Turn,
Rear_Left_Reverse, Rear_Right_Reverse, Rear_Brake, Front_Primary_Head
```

These are the donor `SVehicleLight` objects. `LIGHT_SYSTEM.md` §8 says which list the
renderer reads — module entries vs `.epe` objects — is `UNKNOWN`, and "the counts differ and
no file joins them". The module has 18 rows; the packed graph still carries the donor's
`SVehicleLight` objects, including the presets behind the ten B-07 "dropped" rows.

**Verdict: WEAK.** "Dropped" is true of one of the two candidate lists. The card does not
reconcile the other, so the car may still show indicators/reverse/tail points — which would
also explain why B-07 could drop them without touching the graph.

---

## A8 · `has_lights = 1` proves the binding

**The assumption (stated, the whole Done line).** A part with the flag can host a light
entry.

**Test — the fleet evidence the card itself cites (G2-33 §4, `LIGHT_SYSTEM.json`).**

```
"parts_with_lights": 2073, "lit_parts_without_a_light": 13,
"on_unlit_part": 6, "index_missing": 3, "name_mismatch": 27
```

The doc's own conclusion: "`has_lights` is a **flag the artist sets, not a gate the loader
enforces**: entries exist on parts with it clear (6 of them), and 13 of the 2,073 lit parts
carry no entry at all." So the flag is necessary for a new light part, not sufficient for
the entry to render. The card uses it as the Done criterion.

**Verdict: WEAK.** The 18/18 check is real but tests an authoring convention, not the
binding. The data half of A1 still holds.

---

## A9 · Only the 2 rear arch parts are lit with no entry

**The assumption (stated).** `bm_lightrig.json` `lit_parts_without_entry.parts = [wheel_r_l_arch,
wheel_r_r_arch]`, "the two rear arch parts carry `has_lights = 1` and no module entry".

**Test — full 59-part scan, not just B-03's 8 lamps.**

```
$ python - (decode_parts on the built parts module)
parts 59 lit 20
lit with no entry:
 (8, sportsmuscle_taillight_r_l)   (9, sportsmuscle_taillight_r_r)
 (29, sportsmuscle_signal_r_l)     (30, sportsmuscle_signal_r_r)
 (31, sportsmuscle_taillight_r_c)  (34, sportsmuscle_headlight_f_l_01)
 (35, sportsmuscle_headlight_f_l_02) (36, sportsmuscle_signal_f_l)
 (37, sportsmuscle_headlight_f_r_01) (38, sportsmuscle_headlight_f_r_02)
 (39, sportsmuscle_signal_f_r)      (46, sportsmuscle_wheel_r_l_arch)
 (47, sportsmuscle_wheel_r_r_arch)
```

**13**, not 2. The 11 donor lamp parts are the parts the 11 kept rows used to name; B-07
re-pointed the rows to the new B-03 parts but left the donor parts in the parts module with
`has_lights = 1`, `starts_deleted = 0`, `should_break = 1`, and geometry. They are live and
inside the installable `.ee`:

```
sportsmuscle_taillight_r_l.lod            True (15960508, 495)
sportsmuscle_taillight_r_l_lod1.rbm       True (15429196, 10132)
sportsmuscle_headlight_f_l_01_lod1.rbm    True (14988916, 12182)
sportsmuscle_signal_r_l_lod1.rbm          True (15686972, 5772)
```

and they carry `CarLight` blocks:

```
sportsmuscle_taillight_r_l_lod1.rbm   0.422 x 0.215 x 0.301  first block 0xDB948BF1 (CarLight)
sportsmuscle_tailstrip_r_l_lod1.rbm   0.384 x 0.113 x 0.085  first block 0xDB948BF1 (CarLight)
```

The card's `--check` whitelists them out (`lamp_names` excludes indices 0 and 42–49), and
`lit_parts_without_entry` never looks past B-03's eight lamps. This is the "no carrier"
claim that searched only one place.

**Verdict: BROKEN.** The delivered car has 13 lit parts with no entry, 11 of them donor
lamps with their own geometry.

---

## A10 · Leaving the rear arches unmanaged is a vanilla pattern

**The assumption (stated).** "the same pattern as 13 of the fleet's 2,073 lit parts (G2-33
§4)."

**Test — reproduce the count and read its meaning.** The counts reproduce exactly
(`parts_with_lights 2073`, `lit_parts_without_a_light 13`). But §4 calls them "the
exceptions, so nobody re-derives them", and the listed examples are broken bindings
(`part_index not in the module`, module has another part, `has_lights = 0`), not an
intentional class of permanently-lit, unmanaged lamps.

**Test 2 — are the rear arches carriers?** B-03 cut 1,146 emissive faces into each rear
arch part; their bbox is at z ≈ 2.46 m (rear). So the car has two large unmanaged emitters
whose state is whatever the `CarLight` block does, with no module row to turn them on/off.
"No socket" is true; "no carrier" is false.

**Verdict: WEAK.** The count is real; the inference ("vanilla pattern, so benign") is not
supported by the exceptions it cites, and the geometry is a carrier.

---

## A11 · The BmAK rig has no indicator, reverse lamp or central high beam

**The assumption (stated as the drop reason).** "the BmAK rig has no indicator (G1-17: 28
entries, 9 behaviours, none Left/RightSignal) … no reverse lamp … no central high beam".

**Test — every BmAK package in `LIGHTS.json`, not just `Playable_Batmobile_SF`.**

```
Playable_BatmobileFunhouse_SF 28 signal-ish sockets: [] types: BattleModeLight, BootLight, ForensicsLight, HeadLight, Interior, TailLight
Playable_BatmobileJoker_SF     17 signal-ish sockets: [] types: BattleModeLight, ForensicsLight, HeadLight, Interior, TailLight
Playable_BatmobileMK2_SF       28 signal-ish sockets: [] types: BattleModeLight, BootLight, ForensicsLight, HeadLight, Interior, TailLight
Playable_Batmobile_SF          28 signal-ish sockets: [] types: BattleModeLight, BootLight, ForensicsLight, HeadLight, Interior, TailLight
```

No `Turn`, `Signal`, `Reverse` or `Indicator` socket in any rig; no central socket beyond
`HeadLight1/2`. The claim holds — as a **socket** census. It does not cover the possibility
of a lamp driven without a `VEHLT` socket, and it does not explain the rear arch emitters
(1,146 faces each) that B-03 cut.

**Verdict: HOLDS**, with the scope stated: no indicator/reverse/central socket exists in the
four BmAK rigs, so dropping those donor rows is BmAK-faithful (R1). The "no lamp exists"
reading is not established.

---

## A12 · `Front_Primary_Head` has no possible host

**The assumption (stated).** Dropped because "B-03 measured no Emissive face within
0.3909 m of the BmAK central socket `Headlight_Centre`, so no Batmobile light part can host
it".

**Test — inspect the number.** 0.3909 m is exactly `lamps_without_faces.Headlight_Centre.
nearest_lamp_face_m`: the claim "no face within this distance" is true by construction — it
is the measured minimum. The left/right lamp bboxes are x ±0.356…0.478, z −3.05…−2.965;
the central socket is at (0, 0.655, −3.160), so 0.39 m is the nose lens itself. The
manifest's own `not_claimed` says "absence of lens geometry … other material slots were not
examined".

**Test 2 — "no part can host it".** The Done line accepts the body: rows 0, 11 and 17 hang
on `sportsmuscle_body` with `has_lights = 1`. So a body-hosted `Front_Primary_Head` row
would have passed the card's own gate. The real reason to drop it is that BmAK has no
central high beam (A11), which holds.

**Verdict: BROKEN as stated evidence** (tautological radius + a claim the card's own
body-hosted rows contradict); the drop decision itself is defensible on BmAK grounds.

---

## A13 · The dashboard row's `HeadLight` behaviour is correct

**The assumption (silent).** Row 0 keeps donor row 2's `behavior` (`HeadLight`) and maps
`Dashboard_Light` onto it.

**Test — T-18's own row for that socket.**

```
T-L24  socket Dashboard_Light  bmak_type VEHLT_Interior  bmak_behavior TailLight
       target donor row 2: behavior HeadLight, preset Dash_Light (2763198432)
```

T-18 maps `VEHLT_Interior → TailLight`, but the kept module row is `HeadLight`; B-07's
report counts the dashboard among the 15 `HeadLight` rows. T-18's challenge already flagged
this (`card-T-18.md` A15). The built row:

```
0 HeadLight sportsmuscle_body 0  diffuse 0.6745 0.9608 1.0  range 2.0 angle 10.0 preset 2763198432
```

The dashboard lamp will therefore be driven by the headlight circuit, not the tail/interior
one — the opposite of the socket's decoded behaviour.

**Verdict: BROKEN.** This is precisely R5: the row carries the behaviour of the donor member
whose name matched, not the behaviour of the BmAK socket.

---

## A14 · The 6 custom rows can reuse the `lights[2]` (`Dash_Light`) recipe

**The assumption (stated in the spec source strings).** For the six no-preset rows, "range,
falloff, near_cap, multiplier, min_luminosity, light_type, blinking, angle, …" are "copied
from the donor's shipped steady HeadLight point lamp (module lights[2])", class `decoded`.

**Test — read the values written and the BmAK values they replace.**

```
12 HeadLight wheel_f_l_arch  range 2.0 angle 10.0 type 0 preset 0
13 HeadLight wheel_f_r_arch  range 2.0 angle 10.0 type 0 preset 0
14 HeadLight headlight_f_l   range 2.0 angle 10.0 type 0 preset 0   (battle left)
15 HeadLight headlight_f_r   range 2.0 angle 10.0 type 0 preset 0   (battle right)
16 HeadLight wheel_f_l_arch  range 2.0 angle 10.0 type 0 preset 0   (battle arch)
17 TailLight body            range 2.0 angle 10.0 type 0 preset 0   (boot)
```

Compare with the same module's normal head rows (`range 30 / angle 40 / type 1`) and with
the BmAK battle-head values (T-L18: `radius_ue 1024` = 10.24 m, `cone_inner 10.0`,
`cone_outer 35.0`, `brightness 5.0`). A battle headlight gets a 2-unit, 10° point lamp —
the dashboard's recipe — while the normal head gets 30/40. T-18's A11/A12 called the
template `Dash_Light`; B-07 writes it into the module and labels the 84 cells `decoded`.

**Verdict: BROKEN** for "behaviour-neutral". The row is internally inconsistent with the
card's own head rows, and the source is a dashboard lamp, not this lamp.

---

## A15 · The 450-cell provenance counts are accurate

**The assumption (stated, §12).** "450 member cells 360 decoded / 6 decoded (mapped) /
68 derived / 16 derived (verified), 0 assumed".

**Test — recompute from `bm_lightrig.json` and inspect the `src` of each class.**

```
cells 450 Counter({'decoded': 360, 'derived': 68, 'derived (verified)': 16, 'decoded (mapped)': 6})
decoded with src "kept from the shipped row ... (read from the module)": 187
decoded with src "G2-33 §7a recipe, copied from ... lights[2]": 84
```

The counts are exact and there are 0 `assumed` cells. But R4 lists `read` as its own class;
187 `decoded` cells are a single-instance read of one donor row, and 84 more are a borrowed
recipe (`class`, per R4's "no value without provenance" grading), not a decoded semantic for
this lamp. 271 of 450 cells therefore carry a stronger class than the evidence.

**Verdict: WEAK.** No fiction, but the headline "360 decoded, 0 assumed" overstates what was
decoded; it counts reads and a template as decoded.

---

## A16 · Range/angle/multiplier need no conversion

**The assumption (stated).** "No unit is converted: `range`/`angle`/`multiplier` are the
shipped numbers (G2-33 §8)"; spec `unknowns[2]`: units have no bridge.

**Test — the values are unchanged (true), but what do they mean?**

```
built row 2  range 30.0 angle 40.0 type 1   (normal head volume)
built row 5  range  2.0 angle 10.0 type 0   (normal head point)
BmAK T-L8    radius_ue 6000.0 (60 m) cone 20/70
built row 1  range 2.0 angle 10.0 type 0    (brake)
BmAK T-L15   radius_ue 150.0 (1.5 m), no cone (PointLight)
```

The card says it cannot bridge cm↔module units, so it keeps donor numbers. That is honest,
but the result then rests on "a 30-unit range and 40° cone reproduce a 60 m / 70° headlamp",
which no file supports. The Done line does not test it, and Q-1 #7 is left to discover it.

**Verdict: WEAK.** The no-conversion decision is declared; the consequence is not measured.

---

## A17 · `aafdiff` vs bm-005 is exactly 1 file

**The assumption (stated, §12 and MODLOG).** "aafdiff vs bm-005 exactly 1 file, shared
modules and `@files.xml` byte-identical (R7)".

**Test — re-run the card's own command on the current tree.**

```
$ python Tools/scripts/aafdiff.py Builds/bm-005/aaf Builds/bm-007/aaf --hash
identical=687 changed=2 onlyA=0 onlyB=0

| Bytes A | Bytes B | Delta | Path |
| 6337 | 5745 | -592 | editor/.../modules/generated/v0300_..._lights.vmodc |
| 124488 | 124520 | +32 | editor/.../v0300_..._civilian_01.epe |
```

It is **2** files. The `.epe` is bm-005's pre-rework graph: bm-005 was regenerated at 06:16
by the B-05 rework (`f4abe91d…`, 124,488 B), while bm-007's aaf carries `d118c0aa…`
(124,520 B). bm-007 was built at 04:33; bm-005's `.epe` mtime is 06:16.

```
bm-005 aaf epe 124488 f4abe91d…
bm-007 aaf epe 124520 d118c0aa…
bm-007 weapon_anchor occurrences: 1   bm-005: 0
```

So the delivered aaf still carries the `weapon_anchor` ref the B-05 rework removed. The
`687` identical files and the `@files.xml` claim still hold; the "1 file" claim does not.
(Note: the `.ee` that `install.ps1` copies does not include this `.epe`, so the stale graph
is in the aaf tree, not the installed graph.)

**Verdict: BROKEN on the current tree.** The card built against a superseded B-05 state,
and the §12 R7 sentence is not reproducible.

---

## A18 · The packed `.ee` differs from bm-009 in exactly 1 inner file

**The assumption (stated).** "packed diff 1 inner file(s) vs bm-009".

**Test — unpack both `.ee` trees and hash every file, without trusting the tool's table.**

```
$ python - (SmallUnpack verify trees)
files 685 685 only009 0 only007 0
changed 1
editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc 6337 5745
```

`.ee` sha/size and `.toc` record reproduce exactly (A1). Caveat, inherited from bm-009 and
not caused by B-07: the SARC has 703 records, 19 with offset 0, and SmallUnpack materialises
685 files in both builds. That is a pre-existing packaging hole, not a B-07 change.

**Verdict: HOLDS** for "one inner file changed".

---

## A19 · 21 shipped rows → 11 kept + 10 dropped + 7 added; kept members unchanged

**Test — decode the base module and diff every kept row against the built row, excluding
part/anchor/colour.**

```
base rows 21 bytes 6337
Counter({'HeadLight': 10, 'TailLight': 5, 'LeftSignal': 2, 'RightSignal': 2, 'Reverse': 2})
0 donor 2  fields changed besides part/anchor/colour: []
1 donor 7  ...
…
10 donor 20 fields changed besides part/anchor/colour: []
```

All 11 kept rows reproduce their donor's 17 other members exactly. The dropped indices
(0,1,3,4,5,6,9,10,15,16) all exist in the base with the presets B-07 names. Arithmetic
21 − 10 + 7 = 18.

**Verdict: HOLDS.**

---

## A20 · `preset_id = 0` self-describes; a non-zero preset does not override the row

**The assumption (stated in spec `unknowns[1]` and used by 12 rows).** "whether a preset
overrides the entry's members is UNKNOWN (G2-33 §8); every entry carries its own numbers".

**Test — G2-33 §6.3.** "a light with `preset_id = 0` is fully described by its row — that is
what the 17 shipped zero-preset entries do." That supports A20 for the 6 custom rows. For the
12 rows with a non-zero preset, the graph object's members differ from the module row's on
every row checked in T-18's challenge (e.g. T-L15: module range 2 / angle 10 vs object
radius 1.5 / spot 60). If the preset wins, the colours/values B-07 wrote are ignored; if the
row wins, the preset is decorative. No file decides it.

**Verdict: WEAK.** The custom rows are safe by design; the other 12 rest on a declared
UNKNOWN, and the build's photometry depends on which branch is true.

---

## What this review did not test

- `bm_lightrig.py --check` and the 2 tamper tests were not re-run: they write into
  `tmp/b07/`. The Done line was reproduced directly from the packed module instead (A1).
- No game launch, no install, no `D:/Games` read: the "no in-game evidence" limit stands.
- The B-03/B-04/B-05 upstream claims (emissive cut, part pivots, `_LIG` semantics) were used
  only where the card cites them; their own challenges are `card-B-03.md`, `card-B-04.md`,
  `card-B-05.md` and `card-T-18.md`.

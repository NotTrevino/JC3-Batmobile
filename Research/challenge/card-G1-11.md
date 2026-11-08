# Assumption challenge — G1-11 · Skeleton and vertex-to-bone ownership

Challenger: Freebuff (did not write this card). Date: 2026-10-30. Read-only: nothing under
`GRAB_BACKLOG.md`, `MODLOG.md`, `Tools/`, `Working/`, the rest of `Research/` or the game install
was written, and the card's `--check` was deliberately **not** run (see A10: it writes the 181
external `.npy` files). No game was launched. This report is the only file written.

Inputs read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-11 card (§5, line 435), the §12 row
(line 1279), `MODLOG.md` §"G1-11 · Bone ownership — intent" (8054) and §"… — done" (8078), the
outputs `Research/BatmobileGrab/BONES.md` (§0–§9) and `BONES.json`, the generator
`Tools/scripts/grab_bones.py`, and the corroborating records `MESHES.md`/`MESHES.json` (G1-4/5),
`SLOTS.json`, `Working/TrueScale/stations.json`, `Tools/scripts/bat_assemble.py`,
`Tools/scripts/pskx_parts.py`, plus `BMSDK_OFFSETS.json` is not needed here (no class names).

## VERDICT

**The arithmetic in this record is the most defensible part of it: every count, every parent
relation and every pivot re-derives, and the skeleton convention is verifiable to 0.000002 cm.
The defect is in the *claims around* the arithmetic — one check is circular by construction, one
`.npy` validation cannot fail, and the record never says that a third of its bones own no
geometry at all, including every bone a movable part in APP-5 needs.**

Reproduced independently (all quoted below): 180 bones / 1 root; 299,837 / 144,857 / 21,720 faces
exactly equal to the cooked `MESHES.md`; 298,136 / 143,315 / 21,243 owned + 1,701 / 1,542 / 477
split = total; 3,720 split rows; 470,166 per-bone rows; per-bone and per-slot tables sum to the
LOD totals; the 19/15/15 section tables equal `MESHES.json`'s cooked per-material tables
position-by-position; and the parent-chain rule `q_world = q_child × q_parent` with the parent's
inverse rotation applied to the child offset reproduces all 180 stored world positions to
**2e-6 cm** while the three other candidate orders are **148.8 cm** out.

What does not survive:

- **BROKEN (A10): `--check` is not read-only and its `.npy` validation is vacuous.**
  `collect()` creates `E:\Modding\_BmAKgrab\bones` and `np.save`s all 180 face files plus
  `_split.npy` (grab_bones.py 638–656) *before* `main()` branches to `check()`, which then calls
  `check_files()` on the files the same run just wrote. The MODLOG's "validating all 180 `.npy`
  files and `_split.npy`" cannot detect a damaged or hand-edited face file.
- **WEAK, and it defeats the card's purpose (A11): the bones a movable part needs own nothing.**
  No bone name contains `canop`, `steer` or `yoke`; `Batmobile_Rig_Jet_Thruster` (the turbine)
  owns **0** LOD0 faces (266 at LOD1); `Winch_DOOR_Mesh` owns **0** at all three LODs while six
  `HeadLight*` sockets ride it in G1-13; the 11 `Batmobile_Bone_Chair_*` bones own **0** while the
  seat's 12,470 slot-11 faces belong to `Batmobile_Chassis`. 41 of 180 bones own no LOD0 face.
  The card's Done check ("every face owned or split") passes without noticing.
- **WEAK (A6): the transform check is tested against its own derivation.** The "hub delta
  0.000093707 m" compares bone pivots (REFSKELT) to tyre-bbox hubs from the same PSKX, and that
  same bbox fit produces the recomputed offset that is then compared with `stations.json`
  (tolerance 5e-5 m, actual 1.35e-5 m). It is a genuine bone-vs-geometry alignment check, but not
  evidence that the transform is the right one.
- **WEAK (A7): "the skeleton's own lateral pivot offset" is half wrong.** The 3.751 mm maximum
  decomposes into −3.16 mm X **and −2.01 mm Y** on the front-left tyre (front-right +2.57/−2.07
  mm), while both rear wheels are 0.29/0.45 mm. Two millimetres of that is *radial*, so a wheel
  spun about its bone pivot runs out ~2 mm; and the offset is front-only, not a uniform rule.

## A1 — "Ownership" (one bone per face) is a definition, not an engine fact

**Test.** Read the rule and check what it guarantees. `face_ownership()` marks a point with no
weight ≥ 0.5 or with a tied maximum as ownerless, then a face is *owned* only if its three points
carry the same unique owner. Recomputed from `BONES.json`:

```
LOD0 sum points_ge_0_5=201338 sum points_dominant=201338 points_total=201338
LOD1 sum points_ge_0_5=104812 sum points_dominant=104812 points_total=104812
LOD2 sum points_ge_0_5=21842  sum points_dominant=21842  points_total=21842
```

so exactly one influence ≥ 0.5 per point (no overlaps), and the partition is well defined.

**Verdict: HOLDS as a stated rule — WEAK as a description of the engine.** UE3 has no "owner":
a vertex with 0.6/0.4 influences *deforms* between two bones, and the record never reports how
many points carry a secondary influence. The record stores only aggregates, so a reader cannot
tell a rigid vertex from a 60/40 blended one, and "faces owned by bone X" does not mean "faces
that move rigidly with X". For B-02's cut decision that is the difference between a clean part and
a torn seam. The `.md` §4 definition is honest; the missing number is not disclosed anywhere.

## A2 — 180 bones, one root, parent-before-child

**Test.** Cross-check against the cooked record and re-derive from the JSON.

```
MESHES.md:  | Batmobile_V2 | Playable_Batmobile_SF | 201338 | 299837 | 144857 | 21720 | 180 | 19 | ...
BONES.json: bones=180, unique_names=True, roots=['Batmobile_Chassis'],
            parent_before_child=True, flags all 0
```

**Verdict: HOLDS.** Inverse bind matrices would need the same count; the glTF cross-check found
180 joints, and `grab_bones` guards that `pskx_parts`'s REFSKELT list and its own agree.

## A3 — The hierarchy convention (`q_world = q_child * q_parent`, inverse parent rotation)

**Test.** `BONES.json` stores each bone's local *and* world bind transform, so the rule can be
falsified from the record alone. Re-deriving all 180 world positions under each candidate:

```
order child*parent   inv=False max world-position error = 148.807268 cm
order child*parent   inv=True  max world-position error =   0.000002 cm   <-- stated rule
order parent*child   inv=False max world-position error = 148.807977 cm
order parent*child   inv=True  max world-position error = 148.800789 cm
```

**Verdict: HOLDS.** This is the strongest verification in the record and it is better than the
one the record cites (A14): the rule is exact to 2e-6 cm, not 0.027 cm.

## A4 — "Pivots are produced by importing `bat_assemble`, not copied" (Done criterion)

**Test.** Import the tool and recompute every pivot:

```
$ python -c "import bat_assemble as ba; ..."
pivots recomputed via bat_assemble.pivot_point: n=180 mean_err=5.032e-07 m max_err=7.869e-07 m
bones with error > 1e-6 m: []
```

`pivot_jc3_m` is stored to 6 decimals, so 0.79 µm is the rounding floor. `transform.offset_used`
equals `Working/TrueScale/stations.json`'s `offset` element for element
(`[-4.76837158203125e-07, 0.02223144531250008, 0.15429743957519537]`).

**Verdict: HOLDS.** The Done criterion is literally met: `pivot_point(world_cm, 0.01, offset)`,
imported, reproduces the stored values.

## A5 — The transform's *policy constants* are imported, not re-typed

**Test.** `bat_assemble` gets `scale/ground/center_z` from argparse; `grab_bones` hard-codes them:

```
grab_bones.py:  SCALE = 0.01   GROUND = 0.02   CENTER_Z = -0.0555   WHEELS = 4   MOVE_WEIGHT = 0.5
bat_assemble.py: --scale default 0.01  --ground default 0.02  --center-z default -0.0555
```

**Verdict: WEAK (latent, not present).** The numbers agree today, so every recorded value is
right; but R2 says "import it; never re-implement it", and the three constants that decide
`T(p) = to_jc3_rot(p)*scale + offset` are re-typed here. Change a `bat_assemble` default and
`grab_bones` will not follow — it will instead fail or, worse, pass if the difference stays under
its 5e-5 m tolerance.

## A6 — "The offset is recomputed and must agree with `stations.json`" validates the transform

**Test.** Where do the two sides of the comparison come from?

```
compute_frame():  hubs[c] = (pts.min(0) + pts.max(0)) / 2   over  Vw[unique(tris[fb == tyre_bone])]
                  offset = [-mean_x, GROUND - ground, CENTER_Z - zc]
transform_check(): used = stations["offset"]; delta = |computed - used| (fails above 5e-5)
                  hub  = hubs[c]["centre"] + used   vs  stations["corners"][c]["hub_true"]
$ measured: offset_delta 1.3462e-05 m, hub_delta 9.3707e-05 m
```

Both sides are the same LOD0 tyre vertices through the same `to_jc3_rot`. The `stations.json`
offset was itself produced by `bat_assemble` from those vertices. So:

- **bone pivot vs tyre geometry (0.09 mm)** is a real, useful check: two independent data sources
  (REFSKELT accumulation vs mesh vertices) land on the same place, which is what R3 needs.
- **offset refit vs `stations.json` offset (1.3e-5 m)** is circular: the same fit is compared with
  the earlier run of the same fit.

**Verdict: WEAK.** The record presents both numbers as one "transform" verification; only the
first is evidence. It also cannot detect a *wrong* transform (a uniformly scaled or shifted
placement would reproduce identically), which is by design — R2 fixes the transform by policy.

## A7 — "wheel-bone/hub offset 0.003751 m is the skeleton's own lateral offset, not drift"

**Test.** Decompose the vector per corner from `BONES.json`:

```
f_l Wheel_Front_Left_Vis   d(x,y,z)=[-3.157e-03 -2.013e-03 -2.0e-05] |d|=0.003744
f_r Wheel_Front_Right_Vis  d(x,y,z)=[ 2.570e-03 -2.070e-03 -1.3e-04] |d|=0.003302
r_l Wheel_Rear_Left_Vis    d(x,y,z)=[-2.28e-04   1.60e-05  1.78e-04] |d|=0.000290
r_r Wheel_Rear_Right_Vis   d(x,y,z)=[ 3.84e-04  -2.50e-05 -2.25e-04] |d|=0.000446
```

**Verdict: WEAK.** Three quarters of the figure is X (lateral, harmless for a spin about X), but
**2.0 mm of it is Y (radial) on both front wheels**, and the rear wheels are two orders of
magnitude closer. "Lateral pivot offset" does not describe a front-only 2 mm radial offset, and
"not transform drift" is asserted rather than tested — a 2 mm vertical eccentricity *is* what a
wheel built from these bones would show (4 mm tread runout). If B-02 cuts the wheels by bone and
spins them at the pivot, this is the number to compensate.

## A8 — LOD1/LOD2 are complete and their sections are mapped to the right materials

**Test.** The mapping rule is an *ordered equality* check, not a best-match:

```
slot_map_for_lod(): counts = bincount(PSK face section); cooked_counts = [s["faces"] for s in sections]
                    if [int(x) for x in counts] != cooked_counts: raise
                    out.append(s["material"])  for every cooked section
LOD0 19 sections, LOD1 15, LOD2 15  -> all accepted
non-zero face counts unique per LOD (no permutation ambiguity): duplicates = {}
```

and the resulting per-slot table equals the cooked per-material table in `MESHES.json`, which was
generated by G1-4/G1-5 **before** these LOD exports existed:

```
LOD0 BONES faces_by_slot == MESHES.json cooked faces_by_material: True
LOD1 True   [25436, 922, 24415, 26163, 9961, 4072, 289, 21877, 58, 15872, 5867, 2920, 53, 672, 0, 0, 0, 6280, 0]
LOD2 True   [3404, 230, 4208, 4265, 2366, 350, 104, 2650, 40, 2382, 978, 301, 12, 160, 0, 0, 0, 270, 0]
```

**Verdict: HOLDS.** This is the record's best independent corroboration: the material identity of
every LOD orphan section is confirmed by a record that predates the export.

## A9 — Face totals per LOD equal `MESHES.md` (Done criterion)

**Test.** PSK face counts vs the cooked `MESHES.json` and the LOD0 vertex count:

```
LOD 0  points 201338  faces 299837  expected 299837
LOD 1  points 104812  faces 144857  expected 144857
LOD 2  points  21842  faces  21720  expected  21720
MESHES.json PSKX block: vertices 201338, faces 299837, bones 180, materials 19
```

**Verdict: HOLDS.** The PSK face count is the sum over the parseable `FACE` chunk; the expected
number comes from the cooked object. An incomplete LOD export cannot pass this.

## A10 — "`--check` validates the 180 `.npy` files; `--write` writes them"

**Test.** Read the entry point, then where the files are written:

```
main():  doc = collect()          <-- always
         if a.check: return check(doc)
         write(doc)

collect(), lines 638-656:
    BONE_ROOT.mkdir(parents=True, exist_ok=True)
    for b in range(sk["count"]):
        ... np.save(path, arr, allow_pickle=False)      # all 180
    np.save(BONE_ROOT / "_split.npy", split_arr, allow_pickle=False)

check(): bad += check_files(doc)   # np.load()s and compares with doc["bones"]
```

**Verdict: BROKEN.** (1) `--check` is not read-only: it rewrites every `.npy` before validating
it, which is why this challenge did not run it. (2) Consequently `check_files()` can only fail on
an `np.save` error or a JSON/disk mismatch that the same run created — the MODLOG's "comparing
both records byte-for-byte and validating all 180 `.npy` files and `_split.npy`" overstates what
was proven. The 180-row counts in `check_files` (`k0 != sum(b["owned_faces"])`) are tautologies
under `--check`. A user who edits a face file can never see `--check` complain.

## A11 — "Every face is owned or split" is what APP-5/B-02 needs

**Test.** Which of the parts §1.1 lists have their own bone, and does that bone own geometry?

```
bones with 0 owned faces at LOD0: 41
  Wheel_Parent_F_L/R, Wheel_Parent_B_L/R, Wheel_Rear_Right, Wheel_Front_Right, Wheel_Rear_Left,
  Batmobile_L/R_(F|B)_Wheel_Armour*, Batmobile_Rig_Jet_Root, Batmobile_Rig_Jet_Thruster,
  Winch_DOOR_Mesh, Rear_Door_BOTTOM, Rear_Door_BOTTOM_Ref,
  Batmobile_Bone_Chair_* (11 bones), Batmobile_Rig_Weapons_Root,
  Batmobile_Rig_Weapons_Drone_Decoder_Root, Batmobile_Rig_Weapons_Sides_01,
  Batmobile_Rig_Weapons_R/L_Power_Cell, Batmobile_Rig_Weapons_Turret_Root,
  Batmobile_Rig_Weapons_Trans, Batmobile_R_Shell_Tween_005/006,
  Batmobile_Rig_Weapons_Riot_Sup_Ammo, Batmobile_Rig_Weapons_Heavy_Shells

bone names containing canopy/steer/yoke: NONE
Batmobile_Rig_Jet_Thruster owned L0/L1/L2 = 0 / 266 / 72      (turbine fan bone)
Winch_DOOR_Mesh                 owned = 0 / 0 / 0              (6 HeadLight sockets ride it, G1-13)
Batmobile_Bone_Chair_* (11)     owned = 0 / 0 / 0              (seat bones)
CockPit_Mesh LOD0 owned by slot = {1 glass: 1716, 2: 2724, 6: 48, 7: 4428, 10: 14136, 11: 544, 18: 524}
Batmobile_Chassis slot 11 (BatmobileV3_Cockpit_Seat) = 12470 of the 13014 faces
```

So: the canopy is inside `CockPit_Mesh` (with the glass spread over slot 1), the steering yoke is
inside `CockPit_Mesh` slot 10, the seat is bound to the root `Batmobile_Chassis`, the turbine's
own bone is empty at LOD0, and the door bone is empty everywhere. For MOD-4 (canopy), ANI-7
(yoke), ANI-9 (seat pose) and ANI-4 (turbine) this record offers **no face set at all**, and the
Done check cannot see it because it only asks whether the partition covers every face.

**Verdict: WEAK for the purpose, HOLDS for the letter.** The card exists to make "movable parts
are separate meshes" (APP-5) buildable; the record proves the partition, not the nine parts. It
should say, per part, whether a bone with geometry exists.

## A12 — Split faces are a small seam remainder that B-02 can handle

**Test.**

```
LOD0 split 1701 by slot {2:58, 3:103, 4:349, 5:36, 7:856, 17:299}   = 1701
LOD1 split 1542 by slot {0:99, 2:163, 3:164, 7:1048, 8:4, 17:64}   = 1542
LOD2 split  477 by slot {0:54, 2:76, 3:47, 7:280, 17:20}           = 477
split with no >=0.5 owner: 0 / 0 / 0 ; _split.npy rows 3720 = 1701+1542+477
turret touching: Batmobile_Rig_Weapons_Turret_Top 63, ..._Turret_Top_Slide 57, missile tubes 86-93 each
```

**Verdict: HOLDS.** 0.57 % of LOD0, and it is concentrated exactly where parts meet (slot 7 =
turret armour and weapons, slot 17 = upgrades). The record correctly calls these *touching*, not
owned, and does not pretend the partition has no holes. Anyone cutting a turret by bone will get a
1,701-face ring of missing geometry across all LODs; that is disclosed.

## A13 — "0 ties, 0 under threshold" and the per-point facts are in the record

**Test.** What can be re-derived from `BONES.json` alone:

```
per-bone points_ge_0_5 sum == points_total per LOD  (shown in A1)
per-bone owned_faces_by_slot sums == owned_faces    True
split_touching_by_slot sums == split_touching       True
face_rows total 470166 == counts.face_rows_total
```

but there is no per-point weight vector in the JSON — only per-bone maxima and counts.

**Verdict: WEAK (auditability).** The claims are internally consistent, but `points_tie = 0` and
`points_no_ge_0_5 = 0` can only be re-run by re-reading the PSKX outside the repository, and the
blended-point population (A1) is absent from the record entirely. Two scalars — "points whose
dominant weight < 1.0" and "sum of secondary weights per bone" — would close both gaps.

## A14 — The glTF cross-check ("0.0266 cm max") is the independent confirmation

**Test.** Compare it with the record's own data. The glTF inverse-bind matrices come from umodel's
export of the same package; the PSK side is the REFSKELT accumulation. My re-derivation from the
stored locals is 2e-6 cm (A3), i.e. **13,000× tighter** than the glTF figure, so the 0.0267 cm
residual is on the glTF/umodel side, not in the accumulation. At 700 cm from the origin, float32
resolution is ~1e-4 cm, so 0.027 cm is ~300× float32 noise and remains unexplained in the record.

**Verdict: HOLDS as a discriminator, WEAK as a statement of agreement.** The check does rule out
the wrong multiply order (which would be 148 cm, A3) and it is not a pivot source, as the `.md`
says. But "reproduces umodel's own glTF inverse-bind pivots to 0.0266 cm" invites the reading that
the two agree to rounding; they do not, and the record's own JSON is a far better witness.

## A15 — The external files the record points at are the ones it measured

**Test.** `BONES.json` carries `sha256` for `Batmobile_V2.pskx`
(`c80752e2…bae844`), `Batmobile_V2_Lod1.pskx` (`32edb21f…a7669e`), `Batmobile_V2_Lod2.psk`
(`759ddf74…e447a3`), the glTF (`37f20e81…`) and its `.bin`, and `stations.json`
(`deb01833…`). All of them live outside the repository (R10), and the 181 `.npy` files on
`E:\Modding\_BmAKgrab\bones` are not in the repo either.

**Verdict: WEAK as evidence, HOLDS as disclosure.** The hashes are recorded and the `.md` says the
files are external; but a challenger working from the repository cannot verify any of them, and
the only in-repo validator for the `.npy` set rewrites it (A10). The in-repo numbers that *can* be
checked — face counts and per-slot tables against `MESHES.json`, pivots against `bat_assemble` —
all pass, which is why the verdict above is not harsher.

## A16 — One face-to-bone rule is used throughout the tool

**Test.** Two functions assign faces to bones:

```
pskx_parts.face_bones()   "dominant bone per face: sum of the bone weights of its three points"
                          -> acc[face_points].sum(1).argmax(1)          (no threshold, no unanimity)
grab_bones.face_ownership()  a face is owned only if all three points share the same unique
                          >= 0.5 owner; otherwise split
```

`compute_frame()` uses the first to find the tyre bones; the hub, the recomputed offset and hence
the transform check all depend on that classification. The record documents only the second.

**Verdict: WEAK (silent, no measured effect).** The hub is a bounding-box centre, so a slightly
different tyre face set moves it by far less than the 0.09 mm agreement; no recorded value is
threatened. But "faces of the tyre bone" means two different sets in two files of the same grab,
and a reader comparing them would be surprised.

## A17 — The record's own totals are mutually consistent

**Test.** Re-sum everything in `BONES.json` instead of trusting `counts`:

```
recomputed owned sum LOD0/1/2 = 298136 / 143315 / 21243
recomputed split-touching     = 3433 / 3085 / 954  (= 7472)
sum face_rows = 470166
owned_by_slot sums == owned (all bones, all LODs): True
bone slot totals == faces_by_slot - split_by_slot (all LODs): True
```

**Verdict: HOLDS.** No arithmetic defect found anywhere in the record.

---

## Spot-checks

| value in the record | where verified | result |
|---|---|---|
| **180** bones, 1 root, names unique, parent-first order | `BONES.json` recount + `MESHES.md` bones column | agree |
| **299,837 / 144,857 / 21,720** faces | PSK record vs `MESHES.json` cooked | agree |
| **298,136 / 143,315 / 21,243** owned, **1,701 / 1,542 / 477** split | per-bone sums | agree |
| **327,992** points, 0 ties, 0 under threshold | per-bone `points_ge_0_5` sums | agree (A13) |
| hierarchy `q_world = q_child * q_parent` + inverse parent rotation | 4-order falsification test | **agree, to 2e-6 cm** (better than the record's own glTF check) |
| pivots via `bat_assemble.pivot_point` | imported the module and recomputed | agree to 7.9e-7 m |
| **0.000093707 m** max hub delta | reproduced from `transform.hubs` | agree, but circular (A6) |
| **0.003751 m** wheel-bone/hub | per-axis decomposition | agrees in magnitude, **wrong description** (A7) |
| **0.0266 cm** glTF max | vs my 2e-6 cm re-derivation | discriminates the order, overstates agreement (A14) |
| "`--check` validates the `.npy` files" | `main()` + `collect()` source | **disagree: check writes them first** (A10) |
| per-slot tables equal the cooked sections | `MESHES.json` (pre-existing) | agree, all 3 LODs |

## What would move this from "sound" to "tight"

1. Split `collect()` into a read-only derivation and a writer. `--check` must load the `.npy`
   files and compare them with the derivation *without* saving first, otherwise the claim is
   untestable. (One function boundary; it also makes `--check` safe for read-only auditing.)
2. Publish the per-part verdict the card exists for: for each APP-5 part, the bone that owns its
   faces or "no bone — manual cut". Canopy, yoke, seat, turbine and the winch door currently have
   none, and `Winch_DOOR_Mesh` carrying six light sockets while owning no geometry is a live trap
   for G1-13 (a door animation would move the lights without the metal).
3. Record the blend population (points whose dominant weight < 1.0, and the secondary-weight mass
   per bone) so "owned" can be read as "rigid" where it is rigid and "60/40" where it is not.
4. Correct "lateral pivot offset": state the front-wheel radial component (−2.01 / −2.07 mm in Y)
   and that the rear wheels are within 0.45 mm, or compensate it in B-02's wheel cut.
5. Import `SCALE`/`GROUND`/`CENTER_Z` from `bat_assemble` (or pass them) instead of re-typing
   them, per R2; and note that Umodel's glTF residual (0.027 cm) is unexplained while the
   REFSKELT-to-stored-world check closes to 0.000002 cm.
6. Card conformance detail: the card's `In:` list names `psk_geom.py`; `grab_bones.py` does not
   import it (`grep -c psk_geom` = 0) — no consequence, but the record should say which reader was
   used for what.

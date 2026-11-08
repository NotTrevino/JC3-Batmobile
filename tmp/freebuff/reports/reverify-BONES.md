STATUS: done — VERDICT: **the cooked mesh agrees with `BONES.md` on every bone name, every parent index, the bone count and all three LOD triangle counts.** The PSKX export is faithful for those quantities. It is *not* evidence about the PSKX vertex/wedge/weight data, which this export does not contain in a form decoded here.

Task file: `tmp/freebuff/running/L1__3117-reverify-bones.txt`
DONE path: `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/reverify-BONES.md`

## 1. Answer in one table

`Research/BatmobileGrab/BONES.md` / `.json` (G1-11, `grab_bones.py`) claim: **180 bones, 1 root, 3 LODs at 299,837 / 144,857 / 21,720 faces**, built from umodel's `.pskx`/`.psk` exports plus the cooked package's section tables.

Read out of `Playable_Batmobile_SF.upk`, export **5284** (`Batmobile_V2_Mesh.Batmobile_V2`, `SkeletalMesh`, 20,151,210 bytes of object data):

| quantity | cooked package (this task) | `BONES.md` / `.json` | same? |
|---|---|---|---|
| bones | **180** records, stride 44 | 180 | **yes** |
| bone names, in record order | 180/180 equal to the card's row order | 180 names | **yes** |
| parent index | **180/180 equal** | 180 values | **yes** |
| roots (`parent == own index`) | exactly **1**, record 0 `Batmobile_Chassis` | "1 root" | **yes** |
| LODs | **3** (`int32` before LOD0 = 3, and 3 models follow) | 3 | **yes** |
| LOD0 faces | **299,837** (19 sections) | 299,837 | **yes** |
| LOD1 faces | **144,857** (15 sections) | 144,857 | **yes** |
| LOD2 faces | **21,720** (15 sections) | 21,720 | **yes** |
| `BONES.md` §3 table, parsed as text | 180 rows, index 0…179, names and parent *names* all match | — | **yes** |
| index counts | 899,511 / 434,571 / 65,160 = exactly `3 × faces` | — | **yes** |

**So: no mismatch.** Nothing here contradicts a later card built on the PSKX *as far as the skeleton and face counts go* — see §7 for the boundary of that statement.

## 2. What was decoded, byte for byte

`upk_read.Package` gives the export's object data. In it:

* The reference skeleton is **180 records of 44 bytes** at **offset 8395**, ending at 16315:
  `quat (16 B, f32×4) | position_cm (12 B, f32×3) | FName (8 B: u32 index, u32 number=0) | int32 parent index | 0xFFFFFFFF`.
  Record 0 = `Batmobile_Chassis`, parent 0 (self = root). Record 179 = `Batmobile_Rig_Aero_Flap_R_B_Piston_Top_001`, parent 178.
* LOD0's `Sections` array starts at **16323**, i.e. 8 bytes after the last bone record — so the count of 180 cannot be padded or truncated: no 181st record fits before the next structure.
* Each `FStaticLODModel3` section entry is **13 bytes** (`int16 MaterialIndex, int16 ChunkIndex, int32 FirstIndex, int32 NumTriangles, byte`), and `FirstIndex` is the running `3 × NumTriangles`. The three real models sit at offsets 16323, 12730612 and 18968553, and each is followed 6–13 bytes later by an index count equal to `3 × faces`.

## 3. The oracles (why this is not a pattern match)

| oracle | result |
|---|---|
| the 44-byte record shape is found by its own contents, not by a bone name (`+40 == 0xFFFFFFFF`, unit quat at `+0`, resolvable FName with number 0 at `+28`) | the longest such run is 180 records; outside the skeleton's own span **no run exists at all** (next-longest 0) |
| exactly one root | one: record 0 |
| every parent index ≤ the child's index (topological order) | true for 180/180 |
| parent field forms one connected tree over all records | true (no cycle, every bone reaches record 0) |
| bone names distinct | 180 distinct / 180 |
| all record quaternions unit length | max ‖1−|q|‖ = 5.64e-07 |
| **field order inside the record**: `quat | position` must reproduce the PSKX bind pose | **180/180 bones**, max `1−|dot|` 5.64e-07, max position error **0.00001 cm**, once the PSK convention of negating Y is applied (the same convention `grab_collision_frame.py` reports). With no negation, only 131/180 quats and 60/180 positions match — so the slots are not interchangeable |
| LOD section tables | 11 section arrays in the export have a self-consistent `FirstIndex` chain; only **3** are followed by an index count of `3 × faces`. The other 8 are single-section 65,536-face lookalikes inside vertex data and are rejected by that second test |

The bind-pose test is the one that pins the field *order*; the name/parent values themselves are located by structure (item 1) and only then compared with the card, so the comparison is not circular.

## 4. Files written

* `Tools/scripts/reverify_bones.py` — new tool, `--write` / `--check`. The check re-decodes the package and fails on any disagreement with `BONES.md`/`BONES.json`, with the stored JSON, or with its own oracles.
* `Research/BatmobileGrab/REVERIFY_BONES.json` — the decode (all 180 names, parents, per-LOD section tables) and the comparisons.
* `Research/BatmobileGrab/REVERIFY_BONES.md` — the readable page.
* this report.

Nothing else was edited: `BONES.md`, `BONES.json`, `grab_bones.py` and the game install are read-only inputs here. Revert = delete the three new files above and this report.

## 5. The check has teeth

A `--check` that cannot fail is worthless, so it was tested against deliberate tampering (scratch only, the stored files were not modified):

```
tampered stored copy fails --check: True
tampered LOD face fails --check: True
untouched stored copy passes --check: True
```

## 6. Commands and output (verbatim)

Probe 1 — locate the bone-name run and print raw records:

```
$ timeout 400 python tmp/freebuff/scratch/rv_bones_1.py 2>&1 | tail -40
BONES.json bones: 180 first: ['Batmobile_Chassis', 'Batmobile_Chassis_Mesh', 'SUSP1_Wheel_Front_Left', 'SUSP2_Wheel_Front_Left']
export 5284: Batmobile_V2_Mesh.Batmobile_V2 SkeletalMesh 20151210
name indices resolved: 180 / 180
stride 44 origin 8423 matches 180/180
best: (180, 44, 8423)
bone 0 @8423 Batmobile_Chassis                  c80000000000000000000000ffffffff5900f42c000001abefc6102effff7fbf000000000000008000000000
   words: [200, 0, 0, -1, 754188377, -1425997824, 772851439, -1082130433, 0, -2147483648, 0]
bone 1 @8467 Batmobile_Chassis_Mesh             ca0000000000000000000000ffffffff5b229a3389b02bb6495a58b9ffff7fbf55b804438bf4f1c2d3949542
   words: [202, 0, 0, -1, 865739355, -1238650743, -1185392055, -1082130433, 1124382805, -1024330613, 1117099219]
bone 2 @8511 SUSP1_Wheel_Front_Left             ae0a00000000000001000000ffffffffdebfc93523702f3607f46c39ffff7fbffeff39bb00005cbb000022bb
   words: [2734, 0, 1, -1, 902414302, 909078563, 963441671, -1082130433, -1153826818, -1151598592, -1155399680]
bone 3 @8555 SUSP2_Wheel_Front_Left             b40a00000000000002000000ffffffff35cb1cb3d3cb02b4ed04353ff80435bfc4b50b430098f3bd72cdd7c0
   words: [2740, 0, 2, -1, -1289958603, -1274885165, 1060439277, -1087044360, 1124840900, -1108109312, -1059598990]
bone 4 @8599 Wheel_Parent_F_L                   e00b00000000000003000000ffffffff99e5a2b358ab45b4fe404034ffff7fbffaffbf37f6ffffb700000037
   words: [3040, 0, 3, -1, -1281170023, -1270502568, 876626174, -1082130433, 935329786, -1207959562, 922746880]
bone 5 @8643 Wheel_Front_Left_Vis               d90b00000000000004000000ffffffff34ef5a33aafd75b3b9414034ffff7fbff8ff7f37f6ffffb700000037
   words: [3033, 0, 4, -1, 861597492, -1284112982, 876626361, -1082130433, 931135480, -1207959562, 922746880]
...
bone 179 @16299 3301000000000000b2000000ffffffff0000000003000000130000000000000000000000ccf4000000010001
```

Probe 4 — which field is the parent, and the coordinate relation to the PSKX pose:

```
$ timeout 300 python tmp/freebuff/scratch/rv_bones_4.py 2>&1 | head -40
identity  quat ok 131/180 max 1-|dot| 0.804 | pos ok  60/180 max dist 257.03220 cm
y         quat ok 180/180 max 1-|dot| 1.78e-07 | pos ok 180/180 max dist 0.00000 cm
y,w       quat ok 117/180 max 1-|dot| 1 | pos ok 180/180 max dist 0.00000 cm
all       quat ok 131/180 max 1-|dot| 1 | pos ok 180/180 max dist 0.00000 cm
z         quat ok 119/180 max 1-|dot| 1 | pos ok  28/180 max dist 444.79446 cm
x         quat ok 117/180 max 1-|dot| 1 | pos ok  30/180 max dist 612.15759 cm

parent index from +8 vs BONES.json parent_index, and names:
parent mismatches: 0 []
name mismatches:   0 []
flags word distinct: [-1]
roots (parent == self index): [0]
all parents < index: True
    0 Batmobile_Chassis                        parent   0
    1 Batmobile_Chassis_Mesh                   parent   0
    2 SUSP1_Wheel_Front_Left                   parent   1
  179 Batmobile_Rig_Aero_Flap_R_B_Piston_Top_001 parent 178
```

Probe 5 — LOD section arrays:

```
$ timeout 400 python tmp/freebuff/scratch/rv_lod_1.py 2>&1 | tail -20
export size 20151210
bone array count int at 8375: 0
self-consistent section arrays: 12
  at    16323 n=19 end    16574 faces  299837 idx_at 16583 array_len 3
  at  3615671 n= 1 end  3615688 faces   65536 idx_at None array_len 0
  at  3615769 n= 1 end  3615786 faces   65536 idx_at None array_len 0
  at  3615885 n= 1 end  3615902 faces   65536 idx_at None array_len 0
  at 12730612 n=15 end 12730811 faces  144857 idx_at 12730820 array_len 0
  at 14469750 n= 1 end 14469767 faces   65536 idx_at None array_len 4128768
  at 14470072 n= 1 end 14470089 faces   65536 idx_at None array_len 0
  at 14470102 n= 1 end 14470119 faces   65536 idx_at None array_len 0
  at 18968553 n=15 end 18968752 faces   21720 idx_at 18968761 array_len 0
  at 19099665 n= 1 end 19099682 faces   65536 idx_at None array_len 4128768
  at 19099933 n= 1 end 19099950 faces   65536 idx_at None array_len 0
  at 19099963 n= 1 end 19099980 faces   65536 idx_at None array_len 0
```

(The tool's scan adds one bound this probe did not have - `0 <= ChunkIndex < 512` on each 13-byte entry - which drops one of the twelve, so its page reports 11 arrays seen, of which 3 are followed by an index buffer. Its own listing of those 11: 3 real models plus 8 single-section 65,536-face lookalikes.)

The committed tool:

```
$ timeout 500 python Tools/scripts/reverify_bones.py --write 2>&1 | tail -6
export 5284 Batmobile_V2_Mesh.Batmobile_V2, 20151210 bytes
bones: 180 records at 8395, stride 44; roots [0]; connected True
names vs BONES.json: 180/180 equal; parents: 180/180 equal
LODs: 299837 faces (19 sections) / 144857 faces (15 sections) / 21720 faces (15 sections)
AGREES: the cooked SkeletalMesh carries 180 bones with the same names and the same parent index on every bone as BONES.md/.json, and its own section tables give 299837 / 144857 / 21720 faces at LOD0/1/2 (19/15/15 sections) - identical to the card. The PSKX-based cards rest on a faithful export for the skeleton and the triangle counts.
```

```
$ timeout 500 python Tools/scripts/reverify_bones.py --check
export 5284 Batmobile_V2_Mesh.Batmobile_V2, 20151210 bytes
bones: 180 records at 8395, stride 44; roots [0]; connected True
names vs BONES.json: 180/180 equal; parents: 180/180 equal
LODs: 299837 faces (19 sections) / 144857 faces (15 sections) / 21720 faces (15 sections)
AGREES: the cooked SkeletalMesh carries 180 bones with the same names and the same parent index on every bone as BONES.md/.json, and its own section tables give 299837 / 144857 / 21720 faces at LOD0/1/2 (19/15/15 sections) - identical to the card. The PSKX-based cards rest on a faithful export for the skeleton and the triangle counts.
checks: cooked bones == BONES.md/.json names+parents, one connected root, LOD faces == card (json and verdict line), index counts == 3*faces, stored json == fresh decode - all ok
exit=0
```

Tamper test:

```
$ timeout 500 python - <<'EOF'
import json, sys
sys.path.insert(0,"Tools/scripts")
import reverify_bones as R
doc = json.load(open(R.OUT_JSON, encoding="utf-8"))
bad = json.loads(json.dumps(doc))
bad["skeleton"]["parents"][7] = 0
print("tampered stored copy fails --check:", bool(R.check(bad)))
bad2 = json.loads(json.dumps(doc)); bad2["lods"][1]["faces"] += 1
print("tampered LOD face fails --check:", bool(R.check(bad2)))
print("untouched stored copy passes --check:", not R.check(doc))
EOF
tampered stored copy fails --check: True
tampered LOD face fails --check: True
untouched stored copy passes --check: True
```

Layout knowledge check (why the field *names* below are UNKNOWN):

```
$ python - <<'EOF'
import json
d=json.load(open("Research/BatmobileGrab/BMSDK_OFFSETS.json",encoding="utf-8"))
cls=d.get("classes",{})
print("classes:", len(cls))
print("SkeletalMesh in classes:", "SkeletalMesh" in cls)
print("structs with Bone:", [k for k in d.get("structs",{}) if "Bone" in k or "Skel" in k][:10])
print("struct count:", len(d.get("structs",{})))
EOF
classes: 41
SkeletalMesh in classes: False
structs with Bone: []
struct count: 0
```

(That last `0` is itself accurate: `BMSDK_OFFSETS.json` has keys `classes`/`generated_by`/`schema`/`source` only — it carries no struct table at all, so there is no `FMeshBone` layout to cite.)

## 7. What this does and does not let later cards trust

* **Can be trusted (now proven against the game's bytes, not against umodel's output):** the bone count (180), every bone name and its index, every parent index, the single root, and the face count at each of the three LODs (299,837 / 144,857 / 21,720), plus the LOD section counts (19/15/15).
* **Not covered here:** the PSKX-only payload — vertex positions, wedges, `RAWWEIGHTS`, per-point influences, per-face ownership, the 1,701 / 1,542 / 477 split-face counts, and the glTF joint check. The cooked export's skeleton is a *reference* skeleton (quat + position per bone, no weights), so this task cannot speak to them. The one bridge that does exist: the bind pose stored in the package reproduces the PSKX bind pose on all 180 bones to 1e-5 cm, which is what a faithful geometry export would give.
* Note that `BONES.md`'s own intro says the face counts came from the cooked section tables; the part that was only ever checked through the PSKX is the skeleton, and that is the part verified here.

## 8. UNKNOWNs

1. **The member names of the four fields inside a record.** The layout is decoded (`quat@+0`, `position@+16` in cm, `FName@+28`, `parent@+36`, `0xFFFFFFFF@+40`) and each role is proven by an oracle, but no local layout names them: `BMSDK_OFFSETS.json` has 41 classes and **no `SkeletalMesh` class and no struct table**, and `E:/Modding/_tools/BmSDK-AK` would need an `FMeshBone`/`FReferenceSkeleton` dump that this repo does not carry. Would be resolved by G3-06's native-layout dump. Names are not needed for the verification.
2. **What the `0xFFFFFFFF` word at +40 is.** Constant on all 180 records (a sentinel, or `NumChildren` written as −1); no witness anywhere in the decoded data distinguishes those readings.
3. **Why the packaged pose is the Y-negated form of the PSKX bind pose.** Measured exactly (180/180, 1e-7 on quats, 1e-5 cm on positions) but the *reason* is an ActorX/umodel convention, not a fact in either file. It does not affect the name/parent/triangle comparison.
4. **The 8 bytes between the last bone record (ends 16315) and LOD0's section array (starts 16323).** Left undecoded; they are not needed to fix the bone count, since no fifth-of-44 record fits there.
5. **Whether other meshes' ref skeletons decode the same way.** Only export 5284 was read. `Batmobile_MK2_Skin`, `Batmobile_Jokerfied_Skin`, `Batmobile_V3_Destroyed`, `Batwing_Carrier` and `Batmobile_V2_Fire` were not touched, so the 44-byte shape is proven for this export, not for the class.

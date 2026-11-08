STATUS: done

# What the float at `[Pawn.Mesh + 0xd8]` is, and what state it measures

**Answer.** `[Pawn.Mesh + 0xd8]` is the third vector float of `PrimitiveComponent.LocalToWorld.ZPlane`
(`0xd8 = 0xb0 + 40 = ZPlane(+32) + 8`) - the world-Z component of the mesh component's own up (+Z)
axis. It measures the Batmobile mesh's **orientation relative to world up**, i.e. `cos` of the angle
between the mesh's local +Z and world +Z: `+1` upright, `0` on its side (90 deg), `-1` on its roof
(180 deg). It is a pose, not a speed/ throttle/ mode flag.

The decoded gate in `BatmanAK.exe` `0x140063e90` rejects the mode change when that value is `< -0.707`
(more than 135 deg from upright) and, unless `BatmobileStuckTimeFlip >= BatmobileStuckTime`, also when
it is `< +0.707` (more than 45 deg from upright).

**Files written**
- `Tools/scripts/grab_pawnmesh_d8.py` - new script, `--write` / `--check` (check recomputes every
  number from the exe bytes and the layout, and re-renders the note).
- `Research/BatmobileGrab/PAWNMESH_D8.md`, `Research/BatmobileGrab/PAWNMESH_D8.json` - generated note
  and its data.
- this report: `tmp/freebuff/reports/CONTROLS-0xd8.md`.

Read-only inputs only (`E:/Games/Batman - Arkham Knight/Binaries/Win64/BatmanAK.exe`,
`E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated`, `Research/BatmobileGrab/BMSDK_OFFSETS.json`,
`Research/BatmobileGrab/runtime/*.jsonl`). The game was never run or attached to.

## Labels

| item | value | label |
|---|---|---|
| `[this+0x38c]` | `Pawn.Mesh` (`ComponentProperty`), at 908 = 0x38c, declared type `SkeletalMeshComponent`; unique at that offset on the `RVehicleBatmobileBase` chain | **decoded** (`BMSDK_OFFSETS.json` Pawn.Mesh, offset 908; CLASS_DEFAULTS.json line 5055) |
| mesh component class | `SkeletalMeshComponent` : `MeshComponent` : `PrimitiveComponent` : `ActorComponent` : `Component` : `GameObject` | **decoded** (`.g.cs` class clauses, BmSDK-AK) |
| member at 0xd8 | no property *starts* at 0xd8 in that chain; 0xd8 lies inside `PrimitiveComponent.LocalToWorld` (0xb0, `FMatrix`, width 64) at +40 | **decoded** (`Engine/PrimitiveComponent.g.cs:2063`, getter `AsRef<FMatrix>(Ptr + 176)`) |
| 0xd8 inside the matrix | `0xd8-0xb0 = 40 = ZPlane(+32) + 8`; `FMatrix` = 64 bytes with XPlane/YPlane/ZPlane/WPlane at 0/16/32/48 | **decoded** (`Core/GameObject.g.cs`, `FMatrix` `Size = 64`) |
| the plane member at +8 | `FPlane` is `Size = 16` and declares only `W` at +12, so +8 is the third vector component; the name `Z` is inferred from that size and the W offset, not declared | **derived** |
| the compare | `0x140063efc: movss xmm1,[rax+0xd8]`; `0x140063f04: comiss xmm1,[0x141bf1cdc]` = -0.707; `0x140063f22: comiss xmm1,[0x141bce8f8]` = +0.707, each followed by `jb 0x140063fbe` (return 0) | **decoded** (bytes + disassembly) |
| meaning | cos of the tilt of the mesh up axis against world up; `-0.707`/`+0.707` = cos 135 deg / cos 45 deg | **derived** (unit basis row's Z component is that cosine; the branch rejects *below* each constant) |
| which state | the vehicle's uprightness / inversion (its world orientation), not throttle, speed or mode | **derived** from the above |
| sampler evidence for this float | none: no mesh/matrix key is sampled, no sampled float near +-0.707 | **decoded** (see below) |

## Evidence, source by source

1. **Layout (dump).** `RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle -> Pawn ->
   Actor`; `Pawn.Mesh` at 0x38c, type `SkeletalMeshComponent`, and it is the only property at 0x38c on
   that chain. The dump `BMSDK_OFFSETS.json` does not itself carry `SkeletalMeshComponent` (41 classes,
   none of them the mesh classes), so the mesh chain is taken from BmSDK-AK's generated sources.
2. **Layout (BmSDK-AK `.g.cs`).** `Engine/SkeletalMeshComponent.g.cs:11` : `MeshComponent`;
   `Engine/MeshComponent.g.cs:11` : `PrimitiveComponent`; `Engine/PrimitiveComponent.g.cs:11` :
   `ActorComponent`; `Core/Component.g.cs:11` : `GameObject`. In `PrimitiveComponent`, `LocalToWorld`
   (`StructProperty`, `Ptr + 176`, FMatrix 64 B) is the only span containing 216, and 176+64 = 240 is the
   next property (`CachedParentToWorld`), so the span is bounded and not a guess.
3. **The comparing function.** `mov rax,[rbx+0x38c]` then `movss xmm1,[rax+0xd8]`, then two `comiss`
   against -0.707 and +0.707 with `jb` to the `xor eax,eax` epilogue at `0x140063fbe`. The second compare
   is guarded by `BatmobileStuckTimeFlip (0x1d20) < BatmobileStuckTime (0x1d18)`.
4. **The rest of `.text` (oracle against a rival reading).** 21/20/24/11 functions read the full triples
   `[mesh+0xb0,0xb4,0xb8]`, `[+0xc0,0xc4,0xc8]`, `[+0xd0,0xd4,0xd8]`, `[+0xe0,0xe4,0xe8]` - i.e. four
   rows of a 4x4 float matrix at 0xb0, not three unrelated scalar fields. 41 reads touch `+0xd8` after a
   `[x+0x38c]` load; the constants compared against that element elsewhere are `-0.5`, `0.7`, `0.85` -
   inside `[-1,1]`, as a cosine is and a distance or a degree value would not be.
5. **Sampler logs.** 7 files, 1122 records, 63 distinct keys under `Research/BatmobileGrab/runtime/`:
   no key names a mesh/matrix/LocalToWorld/up-axis/tilt, and no sampled float is within 2e-3 of +-0.707,
   so **nothing sampled lines up with this float**. The sampler does watch part of the same gate
   (`veh*.flags_11D8` bit 0x2 = `ArmouredMode`, tested at `0x140063f45`, and
   `veh*.PreventModeSwitchDuration` = 0x1990, compared to 0 at `0x140063f7e`).

## Commands and their output (verbatim)

```
$ cd "E:/Modding/JustCause3/JC3-Batmobile/Research/BatmobileGrab" && python -c "
import json
d=json.load(open('BMSDK_OFFSETS.json',encoding='utf-8'))
v=d['classes'].get('RVehicleBatmobileBase')
print('super',v.get('super'),'size',v.get('size'),'file',v.get('file'))
...
print(chain('RVehicleBatmobileBase'))
for cl in chain('RVehicleBatmobileBase'):
    for p in d['classes'][cl].get('properties',[]):
        if p.get('offset') in (908,0x1d18,0x1d20,0x1990,0x112c,0x11dc,0x11d8,0x38c):
            print(' ',cl,hex(p['offset']),p['name'],p['kind'],p.get('mask'),p.get('type'))
"
super RVehicle size 8352 file RVehicleBatmobileBase.g.cs
['RVehicleBatmobileBase', 'RVehicle', 'AkVehicle', 'SVehicle', 'Vehicle', 'Pawn', 'Actor']
  RVehicleBatmobileBase 0x1990 PreventModeSwitchDuration FloatProperty None float
  RVehicleBatmobileBase 0x1d18 BatmobileStuckTime FloatProperty None float
  RVehicleBatmobileBase 0x1d20 BatmobileStuckTimeFlip FloatProperty None float
  RVehicle 0x112c MatineeControlRefCount IntProperty None int
  Pawn 0x38c Mesh ComponentProperty None SkeletalMeshComponent
```

```
$ cd "E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated" && sed -n '2040,2100p' Engine/PrimitiveComponent.g.cs
    /// <summary>
    /// StructProperty: LocalToWorld
    /// </summary>
    public unsafe ref BmSDK.GameObject.FMatrix LocalToWorld
        => ref BmSDK.Framework.MarshalUtil.AsRef<BmSDK.GameObject.FMatrix>(Ptr + 176);

    /// <summary>
    /// StructProperty: CachedParentToWorld
    /// </summary>
    public unsafe ref BmSDK.GameObject.FMatrix CachedParentToWorld
        => ref BmSDK.Framework.MarshalUtil.AsRef<BmSDK.GameObject.FMatrix>(Ptr + 240);
```

```
$ cd "E:/Modding/_shared/tools/BmSDK-AK/src/BmSDK/Generated" && grep -n "record struct FMatrix" -A 40 Core/GameObject.g.cs
4708:    public partial record struct FMatrix          (Size = 64)
      XPlane @0   YPlane @16   ZPlane @32   WPlane @48
5402:    public partial record struct FPlane           (Size = 16)
      W @12   (X/Y/Z not declared)
```

```
$ uv run --with pefile --with capstone --with numpy python -c "... disassemble 0x140063e90 ..."
func 0x140063e90 0x140063fcb
0x140063ed7: cmp qword ptr [rbx + 0x1494], 0
0x140063ee5: mov qword ptr [rsp + 0x30], 0x240
0x140063eee: cmp rdx, qword ptr [rsp + 0x30]
0x140063ef3: jne 0x140063f2f
0x140063ef5: mov rax, qword ptr [rbx + 0x38c]
0x140063efc: movss xmm1, dword ptr [rax + 0xd8]
0x140063f04: comiss xmm1, dword ptr [rip + 0x1b8ddd1]
0x140063f0b: jb 0x140063fbe
0x140063f11: movss xmm0, dword ptr [rbx + 0x1d20]
0x140063f19: comiss xmm0, dword ptr [rbx + 0x1d18]
0x140063f20: jae 0x140063f2f
0x140063f22: comiss xmm1, dword ptr [rip + 0x1b6a9cf]
0x140063f29: jb 0x140063fbe
0x140063f2f: cmp dword ptr [rbx + 0x112c], 0
...
0x140063fbe: xor eax, eax
```

```
$ uv run ... python -c "... constant of each compare site ..."
== func 0x140019390
    0x1400193e9: movss xmm0, dword ptr [rip + 0x1bb56cf]   -> 0x141bceac0 0.8500000238418579
    0x1400193f1: comiss xmm0, dword ptr [r8 + 0xd8]
== func 0x1400659c0
    0x140065a5e: movss xmm0, dword ptr [rax + 0xd8]
    0x140065a66: comiss xmm0, dword ptr [rip + 0x1d4a7cb]  -> 0x141db0238 0.8999999761581421
== func 0x1400659c0
    0x1400663f0: movss xmm0, dword ptr [rcx + 0xd8]
    0x1400663f8: comiss xmm0, dword ptr [rip + 0x1d4c7a5]  -> 0x141db2ba4 0.800000011920929
== func 0x14006ae00
    0x14006bd27: movss xmm0, dword ptr [rip + 0x1b7c939]   -> 0x141be8668 -0.5
    0x14006bd2f: comiss xmm0, dword ptr [rcx + 0xd8]
```

```
$ uv run ... python -c "... every function that loads [x+0x38c] and then reads the mesh matrix ..."
0x140057e80 | 0x140058047: mov rax, qword ptr [rbx + 0x38c]
             | 0x14005804e: movss xmm11, dword ptr [rax + 0xd8] ;
               0x140058057: movss xmm12, dword ptr [rax + 0xd4] ;
               0x140058060: movss xmm13, dword ptr [rax + 0xd0]
0x14005b040 | 0x14005b54a: mov rax, qword ptr [rdi + 0x38c]
             | 0x14005b551: movss xmm3, dword ptr [rax + 0xd8] ;
               0x14005b559: movss xmm2, dword ptr [rax + 0xd4] ;
               0x14005b561: movss xmm1, dword ptr [rax + 0xd0]
0x140063e90 | 0x140063ef5: mov rax, qword ptr [rbx + 0x38c]
             | 0x140063efc: movss xmm1, dword ptr [rax + 0xd8] ;
               0x140063f04: comiss xmm1, dword ptr [rip + 0x1b8ddd1] ;
               0x140063f0b: jb 0x140063fbe
(the full 0x38c listing is long; the script regenerates and stores the complete set in
 PAWNMESH_D8.json - "text_sites"; nothing is hand-copied)
```

```
$ cd "E:/Modding/JustCause3/JC3-Batmobile/Research/BatmobileGrab/runtime" && wc -l *.jsonl && head -c 120 samples-20261103T120003Z.jsonl
    17 samples-20261103T084831Z.jsonl
    17 samples-20261103T085330Z.jsonl
    26 samples-20261103T085631Z.jsonl
     1 samples-20261103T113755Z.jsonl
    18 samples-20261103T114350Z.jsonl
   314 samples-20261103T115320Z.jsonl
   729 samples-20261103T120003Z.jsonl
  1122 total
{"t": "2026-11-03T12:00:03.220Z", "changed": {"veh0.flags_11D8": 4194304, ...
```

```
$ uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_pawnmesh_d8.py --write
wrote PAWNMESH_D8.md and PAWNMESH_D8.json
member: PrimitiveComponent.LocalToWorld.ZPlane(+8)
compares: [('0x140063f04', -0.707), ('0x140063f22', 0.707)]
d8 read sites: 41 row triples: {'row1': 20, 'row2': 24, 'row0': 21, 'row3': 11}
oracles: {'pawn_mesh_is_the_slot': True, 'no_property_starts_at_0xd8_in_the_mesh_chain': True,
 '0xd8_is_the_third_float_of_the_local_to_world_z_plane': True, 'compare_constants_are_pm_0_707': True,
 'branch_reject_semantics_are_decoded': True, 'mesh_matrix_is_read_as_rows_elsewhere': True,
 'd8_compare_constants_stay_inside_unit_range': True, 'sampler_has_no_mesh_field': True}

$ uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_pawnmesh_d8.py --check
OK: PrimitiveComponent.LocalToWorld.ZPlane(+8) ; 2 compare(s) ; 41 d8 read site(s) ; oracles all true
check_exit=0
```

The `--check` re-derives the whole document from the exe bytes + the layout and fails if the stored
JSON/MD differ or any oracle is false. It passes (exit 0).

## Oracles (all re-run by `--check`)

| oracle | ok | what would fail it |
|---|---|---|
| `pawn_mesh_is_the_slot` | True | 0x38c not `Pawn.Mesh`, or a second property there on the chain |
| `no_property_starts_at_0xd8_in_the_mesh_chain` | True | any property starting at 216 in the 6-class chain |
| `0xd8_is_the_third_float_of_the_local_to_world_z_plane` | True | LocalToWorld not at 0xb0/64 wide, FMatrix planes not at 0/16/32/48, FPlane not 16 with W at +12 |
| `compare_constants_are_pm_0_707` | True | constants at other addresses or not +-0.707 |
| `branch_reject_semantics_are_decoded` | True | a branch other than `jb` to the reject epilogue |
| `mesh_matrix_is_read_as_rows_elsewhere` | True | no other function reading the 0xb0/0xc0/0xd0 triples |
| `d8_compare_constants_stay_inside_unit_range` | True | a constant outside [-1,1] against this element |
| `sampler_has_no_mesh_field` | True | a mesh/matrix key or a sampled value near +-0.707 |

## Two candidates: how each would be told apart (and what stays UNKNOWN)

The layout yields **one** span at 0xd8, so the answer is not split. Two readings of that span cannot be
separated from the bytes, and each is marked UNKNOWN below with the test that would settle it:

1. **Non-unit Z scale in `LocalToWorld`.** If the Batmobile mesh's matrix carries `DrawScale3D` in its
   Z row, the value is `scaleZ * cos(tilt)` and the 0.707 thresholds would be scale-relative. Told apart
   by reading the lengths of the three rows on a live mesh (sampling `LocalToWorld` is not in the sampler's
   field list today).
2. **Row-versus-column reading of the element.** The dump declares `FMatrix` as four `FPlane`s, so
   element 10 is `ZPlane`'s float 3 either way; for an orthonormal basis the two readings give the same
   scalar, so only the axis naming (local Z in world vs world Z in local) differs. Told apart by naming
   the axes against a live rotation.

Other UNKNOWNs:
- which part of the angle the test "means" (pitch alone vs pitch+roll combined): `ZPlane.Z` is the total
  tilt of the up axis; splitting pitch from roll needs the other elements (and is not needed for the gate).
- why the `-0.707` branch exists (`BatmobileStuckTimeFlip >= BatmobileStuckTime` exemption): the two timer
  fields are decoded by name, but their writers and tick logic are not decoded here.
- `FPlane`'s X/Y/Z members are not named by the dump (only `W` at +12); the `Z` name for +8 is derived
  from the struct size and the `W` offset, cross-checked by the .text row reads (0xd0/0xd4/0xd8).

## Notes on method / repairs

The project rule from `AGENTS.md` was followed: the change is a **new** file
`Tools/scripts/grab_pawnmesh_d8.py`, the generated `PAWNMESH_D8.md`/`.json`, and this report; nothing
existing was edited, so reverting is deleting those files. No game file was written, no process was
started. During development the `.g.cs` parser first mis-read nested `Struct` declarations and
`paramsPtr` offsets as class properties (which put a bogus span at 52) and later compared JSON-round-tripped
string keys against int keys; both are fixed in the committed script and the `--check` now passes on the
final files.

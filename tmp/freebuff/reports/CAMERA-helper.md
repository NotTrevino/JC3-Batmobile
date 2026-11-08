# Camera tracking helper: the three floats are `Vehicle.ExitOffset`

STATUS: done

## Summary

**Build provenance first.** `Research/BatmobileGrab/CAMERA.md` does **not** record a digest of the
`BatmanAK.exe` it disassembled: 0 64-hex strings appear in the file, and none matches the installed
binary. So *which* build produced the `0x14004CD00` address is **UNKNOWN** — the artefact says
"`BatmanAK.exe`" and nothing more. What can be checked is that the installed GOG binary is
*consistent* with it: CAMERA.md's section 2b addresses still land on function bodies.

| item | value |
|---|---|
| installed exe | `E:/Games/Batman - Arkham Knight/Binaries/Win64/BatmanAK.exe` |
| size | 55,101,440 B |
| sha256 | `4b81c4cd410e016223894985c3beecaf7c64d26a8ce805ce340b1c0b7101490a` |
| image base | `0x140000000` |
| PE TimeDateStamp | `0x6508B1CE` |
| GOG `version.txt` | 1.999 |

CAMERA.md §2b natives in this exe: `SetFreeCameraConfig 0x140113480` (`48895c2408574883`),
`UpdateDrivingCamSettings 0x14010AD00` (`488bc45553574156`), `UpdateCameraPosition 0x140111660`
(`488bc4f30f115820`) — all real prologues, so the address space agrees. That is consistency, not
identity.

**The helper, disassembled statically in the installed exe** (`0x14004CD00`, file offset `0x4C100`):

```text
0x14004cd00  mov eax, dword ptr [rcx + 0x5f0]
0x14004cd06  mov dword ptr [rdx], eax
0x14004cd08  mov eax, dword ptr [rcx + 0x5f4]
0x14004cd0e  mov dword ptr [rdx + 4], eax
0x14004cd11  mov eax, dword ptr [rcx + 0x5f8]
0x14004cd17  mov dword ptr [rdx + 8], eax
0x14004cd1a  mov rax, rdx
0x14004cd1d  ret
```

So the three floats are **an object field**: a contiguous `Vector3` at `+0x5F0` of the object in
`rcx`, copied verbatim into the out-vector in `rdx` (also returned in `rax`). There is **no
rip-relative operand**, so it is not a fixed constant; there is **no arithmetic**, so it is not a
computation.

**Which field.** `BMSDK_OFFSETS.json` binds offset 1520 (`0x5F0`) in class `Vehicle` to
**`ExitOffset`** (`StructProperty`, `Vector3`), and `Vehicle` is on the Batmobile chain:
`RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle -> Pawn -> Actor -> ...`.
The helper therefore copies **`Vehicle.ExitOffset`** — the vehicle's exit point, not a
camera-specific value and not a distance.

**Callers.** Exactly two `call` sites reach the helper:

| call site | enclosing function | instructions | behaviour |
|---|---|---|---|
| `0x140122C74` | `0x140122Bxx` | 208 | consumes the triple, multiplies it by a matrix at `[rax+0xB0..0xC0]` |
| `0x1404BE29C` | `0x1404BE2xx` | 11 | copies `[rax]`, `[rax+4]`, `[rax+8]` straight out |

The short one is the "call the helper, copy three floats" wrapper CAMERA.md describes; its shape
matches, but the **"18 instructions" count cannot be reproduced** here (11 by this tool's boundary
heuristic, 208 for the other caller), so that number is not comparable across builds.

## Files written

- `Tools/scripts/bmak_camera_helper.py` (new, `--write` / `--check`; `uv run --with pefile --with capstone`)
- `Research/BatmobileGrab/CAMERA_HELPER.md` (5,372 B)
- `Research/BatmobileGrab/CAMERA_HELPER.json` (23,917 B)
- this report

The binary was read statically only — no process was started, attached to or injected into.

## Commands and output

### `--write`

```
$ PYTHONIOENCODING=utf-8 uv run --with pefile --with capstone python Tools/scripts/bmak_camera_helper.py --write
PASS  the installed exe's identity is recorded (size, sha256, PE timestamp)
      55101440 B, sha256 4b81c4cd410e0162..., TimeDateStamp 0x6508B1CE
PASS  the helper is the 8-instruction copy of [rcx+0x5F0..0x5F8] into [rdx..]
      8 instructions, reads ['5f0', '5f4', '5f8']
PASS  the three floats are one object field, not a constant or a computation
      reads ['5f0', '5f4', '5f8']; rip-relative operands 0
PASS  offset 1520 binds to Vehicle.ExitOffset and Vehicle is on the Batmobile chain
      hits [{'class': 'Vehicle', 'member': 'ExitOffset', 'kind': 'StructProperty', 'type': 'Vector3', 'offset': 1520}]; chain RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle -> Pawn -> Actor -> StateObject -> GameObject -> IGameObject
PASS  the helper has exactly two call sites, one of them a short copy-out wrapper
      xrefs ['0x140122c74', '0x1404be29c']; caller instruction counts [208, 11]
PASS  CAMERA.md's section 2b addresses still decode to function bodies here
      SetFreeCameraConfig 0x140113480 48895c2408574883; UpdateDrivingCamSettings 0x14010ad00 488bc45553574156; UpdateCameraPosition 0x140111660 488bc4f30f115820
PASS  CAMERA.md records no digest matching this exe, so its build is UNKNOWN
      0 digests in CAMERA.md, none equal to 4b81c4cd410e0162...

7/7 oracles pass
wrote Research\BatmobileGrab\CAMERA_HELPER.md (5372 B)
wrote Research\BatmobileGrab\CAMERA_HELPER.json (23917 B)
```

Exit status 0.

### `--check`

```
$ PYTHONIOENCODING=utf-8 uv run --with pefile --with capstone python Tools/scripts/bmak_camera_helper.py --check
... 7/7 oracles pass ...
CHECK OK: the stored .md/.json are byte-identical to a fresh recompute
```

Exit status 0.

## Oracles

| # | check | result |
|---:|---|---|
| O1 | installed exe identity recorded (size, sha256, PE timestamp) | PASS |
| O2 | helper is exactly the 8-instruction copy of `[rcx+0x5F0..0x5F8]` → `[rdx..]` | PASS |
| O3 | those three floats are one object field (no rip-relative constant, no arithmetic) | PASS |
| O4 | offset 1520 → `Vehicle.ExitOffset` (Vector3) and `Vehicle` is on the chain | PASS |
| O5 | exactly two call sites, one a short copy-out wrapper | PASS |
| O6 | CAMERA.md §2b addresses decode to function bodies in this exe | PASS |
| O7 | CAMERA.md records no digest matching this exe → its build is UNKNOWN | PASS |

## Defects found while building this

1. **"9 instructions"** in my first write-up of the helper: it is **8** (six `mov`, `mov rax, rdx`,
   `ret`). Corrected in the tool and the generated card.
2. **Caller instruction counts are heuristic.** The enclosing function start is found by scanning
   back to a byte after an `int3`/`ret`, which lands differently on different builds. The counts
   (208 / 11) are reported as measurements of *this* exe only, not as a correction of CAMERA.md's 18.

## UNKNOWNs

1. **The build CAMERA.md disassembled.** No digest is recorded, so it cannot be compared to the
   installed `4b81c4cd…` file. The 2b address matches and the helper shape matches, which is
   consistent evidence but not proof of identity.
2. **Whether `ExitOffset` is semantically the tracking point.** The helper copies it and one caller
   forwards it unchanged; the other transforms it by a matrix at `[rax+0xB0..0xC0]`. Which
   consumer is `GetCameraTrackingOffset`'s out-vector is not claimed here.
3. **The 18-instruction count** is not reproducible in this build with a heuristic boundary.

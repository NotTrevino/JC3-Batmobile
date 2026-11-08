# G3-01b — box rotations, the 0x4C tag, and every byte of the box record

**STATUS: done**

Card: `GRAB_BACKLOG.md` §6b `#### G3-01b` open items — *"box rotations, the 0x4C tag, extents
convention"* (`RB_BodySetup` 169750 `Batmobile_Chassis`, 169751 `Batmobile_Rig_Weapons_Trans`,
`BmGame.upk`).

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_collision_boxes.py` | the tool (`--write` / `--check`), 1,278 lines |
| `Research/BatmobileGrab/COLLISION_BOXES.md` | the record (20,182 B, generated) |
| `Research/BatmobileGrab/COLLISION_BOXES.json` | the same as data (138,630 B: every box, every byte-map record, every oracle number) |
| `tmp/freebuff/reports/G3-01b-boxes.md` | this report |

Nothing else was written. `GRAB_BACKLOG.md`, `MODLOG.md`, `STATUS.md`,
`grab_collision_geom.py`, `grab_physics.py`, `grab_collision_convex.py` and their outputs are
unchanged (the tool only *reads* `COLLISION_CONVEX.json` for the hull oracle and imports
`parse_element` from G3-01c). Read-only on the game install; no game launched or read; nothing
written under `E:/Games` or `D:/Games`; no git operations.

## What the bytes say (decoded)

The AggGeom payload is `u32 sphere_count`, `u32 box_count`, then per box:

| bytes | content | evidence |
|---:|---|---|
| 20 | StructProperty tag: `type=10`, `offset=0`, `name_index`, `number=0`, `size=64`, `array_index=0` | name index 78655 resolves to **`TM`** in `BmGame.upk`; 2846 resolves to `TM` in `Playable_Batmobile_SF.upk`; `size=64` is exactly the 64 bytes that follow |
| 64 | `TM`: 16 floats — 3x3 from floats `4i+1..4i+3`, translation from floats 13..15 | 3x3 is orthonormal with det +1 on **131/131** boxes; the floats at `4i` are `0,0,0,1` on every box |
| 8 | FloatProperty `0x40` = Extent X | decoded tag |
| 8 | FloatProperty `0x44` = Extent Y | decoded tag |
| 8 | FloatProperty `0x48` = Extent Z | decoded tag |
| 8 | BoolProperty `0x4C`, 4-byte **packed bool word** | decoded tag |
| 2 | `type 0` end-of-tag-list | decoded |

Element struct = `0x50` = 80 B (TM 0x00-0x3F, extents 0x40-0x4B, bool word 0x4C-0x4F).

The three BmGame boxes (previously only extents + centre were known):

| export | bone | box | TM 3x3 | translation (cm) | extents X/Y/Z (cm) | 0x4C word |
|---|---|---:|---|---|---|---|
| 169750 | `Batmobile_Chassis` | 0 | identity | (9.0, 0.0, 106.75) | 690.305 / 374.536 / 207.5 | `0x40` (bit 6) |
| 169750 | `Batmobile_Chassis` | 1 | identity | (0.0, 0.0, 79.0) | 679.585 / 345.688 / 103.5 | `0x00` |
| 169751 | `Batmobile_Rig_Weapons_Trans` | 0 | (0.998,0,−0.070; 0,1,0; 0.070,0,0.998) | (−30.5, 0.0, 93.25) | 166.177 / 189.365 / 39.8 | `0x00` |

The weapons box's 3x3 is a rotation about the Y axis of **4.00°** (cos = 0.997564 = cos 4.0°,
sin = 0.0697565 = sin 4.0°), axis vector (0, −1, 0). The translation is byte-identical to the
"12 bytes before the tag stream" that `grab_physics.py`/`grab_collision_geom.py` read as the
centre — those values are confirmed, not replaced.

What follows the boxes, and why the payload closes: 169750 = boxes to byte 244, `u32 0`,
`u32 convex_count = 1`, one convex element in G3-01c's proven layout (1,498 B, `ElemBox ==
vertex bounds` holds), 9-byte zero footer → **1759/1759 bytes mapped**. 169751 = boxes to byte
126, `u32 0`, `u32 0`, 9-byte zero footer → **143/143 bytes mapped**.

## Oracles actually run

| oracle | result |
|---|---|
| reading A (`rows = floats[4i+1..4i+3]`) orthonormal + det +1 | **131 / 131** boxes (worst row-norm error 2.7e−08, worst `|row·row|` 3.5e−21, dets {1.0, 1.0000001}) |
| reading B (`rows = floats[4i..4i+2]`) | **0 / 131** — singular on the 128 identity boxes → REJECTED |
| 128 wreck boxes (4 packages × 32) | all identity 3x3, det 1.0, TM tag named `TM`, `0x4C` word `0x00`, layouts byte-identical across packages |
| translation == the earlier "12 bytes before the tags" rule | agrees on 3/3 boxes |
| byte accounting to the payload end | exact on both bodies, zero footer, byte-map offsets strictly increasing from 0 |
| convex element after the boxes | `ElemBox == vertex bounds` holds (169750's single element) |
| **extents: full or half lengths** | **FULL lengths** — see below |
| wreck-union size test | **does not decide** — recorded, not used (see UNKNOWN/limitations) |

Extents oracle, the decisive numbers (hull = union of the drivable collision hull's decoded
element boxes from `COLLISION_CONVEX.json`, where `ElemBox == vertex bounds` on 56/56):

- against the tight hull (169749, pursuit mesh, spans 671.0 / 318.3 / 224.1 cm) the chassis
  box's full-length spans (690.3 / 374.5 / 207.5 cm) deviate **0.150** (worst axis ratio
  0.85–1.08); the half-length reading deviates **0.575** — **3.8× worse**.
- containment: at full lengths every box sits inside that hull to within **28.11 cm** (4.2 % of
  the hull's largest span; chassis box 0 Z = 3.0..210.5 cm inside hull Z = 0..224.1 cm); at
  half lengths the worst overhang is **359.70 cm** (53.6 %).
- half lengths would make the car **13.806 × 7.491 × 4.150 m**; full lengths **6.903 × 3.745 ×
  2.075 m**.
- finding (recorded, not explained): the battle-mode hull (169748, spans 695.4 / 492.9 /
  294.5 cm) is 32 % wider and 42 % taller than chassis box 0; the box is inside it (overhang
  0.0 cm). The pursuit hull is the closer match.

## Commands and outputs (verbatim)

```
uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --write
```
```
wrote COLLISION_BOXES.json and COLLISION_BOXES.md (131 boxes: 3 BmGame + 128 wreck); extents: FULL lengths
```
exit status **0**

```
uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_boxes.py --check
```
```
OK: 131 boxes (3 BmGame + 128 wreck), 2 byte-mapped payloads, rotations 3/131, extents FULL lengths, 14/14 checks, md byte-identical
```
exit status **0**. `--check` re-reads both packages, re-decodes all 131 boxes, re-runs every
oracle and fails if `COLLISION_BOXES.md` or `.json` differs by one byte.

Strict JSON validation (no NaN/Infinity tokens):

```
uv run python -c "import json;raw=open('Research/BatmobileGrab/COLLISION_BOXES.json',encoding='utf-8').read();d=json.loads(raw, parse_constant=...);print(...)"
```
```
JSON strict-parse ok, keys: 10 | bytes: 138630
boxes: 131 | extents: FULL lengths
```
exit status **0**

Independent spot-check (re-reads the raw bytes and recomputes, does not use the tool's code):

```
169750 box 0 tag 10 0x0 TM 0 64 0 | payload bytes 1759 | extents [690.305, 374.5361, 207.5] | word 64
    translation from raw [9.0, 0.0, 106.75]
    det 1.0 row norms [1.0, 1.0, 1.0]
169750 box 1 tag 10 0x0 TM 0 64 0 | payload bytes 1759 | extents [679.5852, 345.6876, 103.5] | word 0
    translation from raw [0.0, 0.0, 79.0]
    det 1.0 row norms [1.0, 1.0, 1.0]
169751 box 0 tag 10 0x0 TM 0 64 0 | payload bytes 143 | extents [166.1769, 189.3649, 39.8001] | word 0
    translation from raw [-30.5, -0.0, 93.25]
    det 1.0000001 row norms [1.0, 1.0, 1.0]
```
exit status **0**

```
python -m py_compile Tools/scripts/grab_collision_boxes.py
```
```
COMPILE_OK
```
exit status **0**

## UNKNOWNs and why

| # | unknown | what was tried | why it stays UNKNOWN / where it would be found |
|---|---|---|---|
| U-1 | the **name and meaning of the 0x4C bool** | decoded the tag (type 3, offset 0x4C, 4-byte packed word) for all 131 boxes: bit 6 is set only on `Batmobile_Chassis` box 0 (`0x40`), word is 0 on chassis box 1, the weapons box and all 128 wreck boxes. Searched `BMSDK_OFFSETS.json`: only 41 classes (Actor, RVehicle*, SVehicle* …), **no `FKBoxElem`/aggregate struct**, so no local layout names the member or the bit | BmSDK-AK's struct dump for the box element (G3-06 native layouts), or a body where another bit of the same word differs and its effect is observable. Not guessed |
| U-2 | which element type the **zero count before the convex count** belongs to (the old "sphyl" word) | decoded: `u32 0` at byte 244 (169750) / 126 (169751), then `u32 convex_count` = 1 / 0 whose elements consume the payload to the footer. No sphere or sphyl element exists in any body decoded here, so the type order cannot be tested | a body that contains a sphere or sphyl element, or the engine's aggregate serialiser definition |
| U-3 | whether the decoded 3x3 is the transform's **rows or columns** (hence the sign of the 4.00° Y tilt) | tested both readings of the 16 floats (B fails orthonormality); R and Rᵀ are both proper 4.00°-about-Y rotations, and no second known transform for the same bone is available in this record | a known bone-local matrix for `Batmobile_Rig_Weapons_Trans`, or this build's `FMatrix` convention (G3-06). The angle and axis are decoded; only the sign is conditional |
| U-4 | the **StaticMesh `Bounds`** as a second extents oracle | G3-01c already walked 175973/175974: 4 unnamed tags, no `Bounds` struct; `BMSDK_OFFSETS.json` has no `StaticMesh` class. Re-checked the first/last 96 B of both exports and scanned for FBoxSphereBounds-shaped float runs (0 candidates) | G3-06, then re-run this tool's comparison with the mesh box as a second hull |
| U-5 | the **wreck-union size test** as a confirming oracle | computed the wreck boxes' union under both conventions: 453.2 / 197.1 / 156.0 cm (full) vs 717.9 / 394.2 / 247.9 cm (half) against the intact hull 671.0 / 318.3 / 224.1 cm. The half reading matches the intact car, the opposite of the chassis-box test | it stays out of the verdict because the wreck boxes are per-bone envelopes of an exploded rig — the largest is 317.9 cm on one axis while all translations span only 312.3 / 79.3 / 80.6 cm — so "these boxes tile the intact car" is an unproven assumption. Reported with its numbers instead of being used |

## What this changes for the card

- **Box rotations: decoded** (they were "UNKNOWN: the chassis TM is not decoded"). Both chassis
  boxes are identity; the weapons box is a 4.00° Y rotation; translations confirmed.
- **The 0x4C tag: decoded as data** — a packed bool word at logical offset 0x4C (element struct
  80 B). Its *name/meaning* remains UNKNOWN with the reason (no local struct layout).
- **Every byte of both box records is accounted for**, and both AggGeom payloads close to the
  last byte (1759/1759, 143/143) including a convex element in 169750 that the earlier decode
  did not report.
- **Extents: FULL lengths**, by two independent mechanical tests with numbers (span match 0.150
  vs 0.575; containment 28.1 cm vs 359.7 cm). The old "derived/conditional" label on that value
  can now be upgraded to a decoded-structure + oracle result; the *frame* link (bone space →
  JC3 space) is still UNKNOWN, so the boxes' positions are still not expressed in JC3 space here.

## Limitations

- The extents verdict rests on `COLLISION_CONVEX.json` (G3-01c) and assumes the hull's union
  boxes and the physics boxes share one axis frame; the spans are compared sorted to stay
  frame-agnostic, the containment test does not (it compares intervals axis by axis).
- `0x4C` bit 6 is reported as a bit, not as a named flag; no behaviour is inferred from it.
- The wreck asset is used only as a fleet invariant for the *struct* (identity 3x3, TM tag name,
  `0x4C` word 0, identical layouts) and its size arithmetic is reported without a claim.

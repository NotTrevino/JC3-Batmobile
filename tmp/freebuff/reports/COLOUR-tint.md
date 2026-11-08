# COLOUR-tint · Who writes the CarPaintMM dynamic float4s — card report

**STATUS: partial** — the constant-buffer update and the field offsets are decoded from the
image; the last hop (which code picks the tint per vehicle) is not a direct call anywhere in
the image, so by the brief's rule this card stops at that boundary and reports it UNKNOWN
rather than inventing a writer. Everything below is static: the game was not run, nothing was
attached to, nothing was built, no other task's file was edited, no git command was run.

The decoded chain, in one paragraph: the shader's own reflection header gives the cbuffer
layout (`m_TintColorR/G/B` at 0/16/32, `_unused` at 48, three override floats at 64/68/72,
76 B total). The engine-side type is `CSyncedShaderConstantData<SCarPaintDynamicMaterialParams>`;
its RTTI resolves to vtable `0x14234e5f0`, whose slot 0 is **`0x140259f00`** — the constant-buffer
update. It selects one of two 76-byte CPU copies by a parity bit (`imul rax, rax, 0x4c`,
`lea r8, [rax + rcx + 0x18]`), pairs it with the GPU handle at `+0xb0` and tail-jumps to
`0x1400b1960`. The CPU-side fill is **`0x140289a80`**, which copies the 76 bytes from a source
struct in exactly the cbuffer's member order (`+0x00→+0x18`, `+0x10→+0x28`, `+0x20→+0x38`,
`+0x30→+0x48`, `+0x40→+0x58`, `+0x48→+0x60`). Its **only** caller is `0x1402dd36f`, inside the
CarPaint render-block class constructor `0x1402dd1a0`, passing the block object's own field
`+0x168` as the source and the synced constant data at `+0x98` as the destination. So the
per-vehicle tint float4s are read from **block object `+0x168`, `+0x178`, `+0x188`**.

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_tint_write.py` | new; `--write` builds `Research/JC3Grab/TINT_WRITE.md`, `--check` re-derives every number and oracle from the PE bytes and the reflection header and compares the file byte for byte |
| `Research/JC3Grab/TINT_WRITE.md` | the deliverable: result, 8 oracles, cbuffer layout, the RTTI chain, the update and writer disassembly, the caller, the field table at every layer, UNKNOWNs |
| `tmp/freebuff/scratch/strs.py`, `strs2.py`, `xref.py`, `rtti.py`, `rtti2.py`, `sites.py`, `sites2.py`, `tint1.py`…`tint7.py` | scratch exploration (nothing depends on them) |
| `tmp/freebuff/reports/COLOUR-tint.md` | this report |

Not touched: `D:/Games`, `E:/Games`, `E:/Modding/_shared/gamedata`, `Research/JC3Grab/COLOUR*.md`,
`Research/JC3Grab/RUNTIME_LAYOUT.*`, `Tools/scripts/jc3_colour*.py`, `Builds/`, git.

## Every command run for the result, and its output

### 1. Strings in the image

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/strs.py
CarPaintMM       16 hits
   off 0x2331358 VA 0x142332158 .rdata  b'CarPaintMM_Skinned'
   ... b'CarPaintMM_Deform', b'CarPaintMM', b'CarPaintMMPreZVelocity_*', b'CarPaintMMShadow_*'
TintColor        0 hits
CarPaintStatic   0 hits
CarPaintDynamic  3 hits
   off 0x2d44242 VA 0x142d45642 .data  b'CarPaintDynamicObjectParams@@@NGraphicsEngine@@'
   off 0x2d442b2 VA 0x142d456b2 .data  b'CarPaintDynamicMaterialParams@@@NGraphicsEngine@@'
```

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/strs2.py
0x142d45620  .?AV?$CSyncedShaderConstantData@USCarPaintDynamicObjectParams@@@NGraphicsEngine@@
0x142d45690  .?AV?$CSyncedShaderConstantData@USCarPaintDynamicMaterialParams@@@NGraphicsEngine@@
MaterialParams 2, DynamicObjectParams 1, Tint 4, tint 10, Paint 26, ColorR 1
```

No `m_TintColorR` string exists in the image, so the field names can only come from the
reflection header (read below); the engine names its type, not its members.

### 2. RTTI route (first attempt failed, recorded)

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/rtti.py
CarPaint type names: [...]
control type names: [...]
(no COL lines)
```
Discarded: I passed the *name string* address where the *type_info* address belongs
(type_info = name − 0x10) and required an exact 4-byte signature.

### 3. RTTI route, corrected

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/rtti2.py
.?AV?$CSyncedShaderConstantData@USCarPaintDynamicMaterialParams@@@NGra
  type_info 0x142d45680 (vfptr 0x1428260d8) cols ['0x14286e928']
   vtable(s): ['0x14234e5f0']
     lea refs: ['0x140259ddc', '0x140259ebb', '0x1402dd475', '0x1405ef242', '0x1405f45a0']
.?AV?$CSyncedShaderConstantData@USCarPaintDynamicObjectParams@@@NGraph
  type_info 0x142d45610 (vfptr 0x1428260d8) cols ['0x14286e8a8']
   vtable(s): ['0x14234e580']
     lea refs: ['0x140259cfc', '0x140259d5b', '0x1402dd1e6', '0x1402dd4b5']
```

### 4. Vtable slots and the constructor

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/sites.py
=== vtable MaterialParams 0x14234e5f0
   slot 0 -> 0x140259f00
=== vtable ObjectParams 0x14234e580
   slot 0 -> 0x140259da0
```

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/sites2.py
=== MaterialParams vtable[0] 0x140259f00 (29 insns)
   0x140259f00  8b8248040000 mov eax, dword ptr [rdx + 0x448]
   0x140259f06  83e001       and eax, 1
   0x140259f0b  486bc04c     imul rax, rax, 0x4c
   0x140259f0f  4c8d440818   lea r8, [rax + rcx + 0x18]
   0x140259f14  4881c1b0000000 add rcx, 0xb0
   0x140259f1b  e9407ae5ff   jmp 0x1400b1960
=== ObjectParams vtable[0] 0x140259da0 (8 insns)
   0x140259da0  8b8248040000 mov eax, dword ptr [rdx + 0x448]
   0x140259dab  4c8d0480     lea r8, [rax + rax*4]
   0x140259daf  4e8d448118   lea r8, [rcx + r8*4 + 0x18]
   0x140259db8  e9a37be5ff   jmp 0x1400b1960
--- call sites of ctor MaterialParams 0x140259dc0: 2 ['0x1402dd22b', '0x140607536']
--- call sites of dtor MaterialParams 0x140259ea0: 0 []
```

### 5. The cbuffer writer and its single caller

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/tint5.py
=== 0x140289a80 (36 insns, pdata 0x140289a80..0x140289b16)
   0x140289a95  ba4c000000   mov edx, 0x4c
   0x140289a9a  4881c1b0000000 add rcx, 0xb0
   0x140289aa1  e8ba8fe3ff   call 0x1400c2a60
   0x140289abd  8b05e90bab02 mov eax, dword ptr [rip + 0x2ab0be9]
   0x140289ac3  8b4f48       mov ecx, dword ptr [rdi + 0x48]
   0x140289ac6  0f100f       movups xmm1, xmmword ptr [rdi]
   0x140289ac9  0f105710     movups xmm2, xmmword ptr [rdi + 0x10]
   0x140289acd  0f105f20     movups xmm3, xmmword ptr [rdi + 0x20]
   0x140289ad4  486bc04c     imul rax, rax, 0x4c
   0x140289ae1  0f114c3018   movups xmmword ptr [rax + rsi + 0x18], xmm1
   0x140289ae6  0f11543028   movups xmmword ptr [rax + rsi + 0x28], xmm2
   0x140289aeb  0f115c3038   movups xmmword ptr [rax + rsi + 0x38], xmm3
   0x140289af0  0f11643048   movups xmmword ptr [rax + rsi + 0x48], xmm4
   0x140289af5  f20f11443058 movsd qword ptr [rax + rsi + 0x58], xmm0
   0x140289afb  894c3060     mov dword ptr [rax + rsi + 0x60], ecx
=== 0x140289b20 (48 insns) static params, 0xf0-byte block
```

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/tint7.py
=== callers of SetDynamicMaterialParams 0x140289a80: 1 ['0x1402dd36f']
  in fn 0x1402dd1a0 (110 insns)
      0x1402dd361  498d9668010000 lea rdx, [r14 + 0x168]
      0x1402dd368  498d8e98000000 lea rcx, [r14 + 0x98]
   >> 0x1402dd36f  e80cc7faff   call 0x140289a80
      0x1402dd374  498d96d0070000 lea rdx, [r14 + 0x7d0]
      0x1402dd37e  e89dc7faff   call 0x140289b20
```

### 6. The block-class constructor (source field and default)

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/tint4.py
=== 0x1402dd1a0 (110 insns)
   0x1402dd1e6  488d0593130702 lea rax, [rip + 0x2071393]     -> 0x14234e580 (ObjectParams vtable)
   0x1402dd224  498d8e98000000 lea rcx, [r14 + 0x98]
   0x1402dd22b  e890cbf7ff     call 0x140259dc0            (MaterialParams ctor)
   0x1402dd231  49c786680100000000803f mov qword ptr [r14 + 0x168], 0x3f800000
   0x1402dd243  49c786740100000000803f mov qword ptr [r14 + 0x174], 0x3f800000
   0x1402dd24e  49c7867c0100000000803f mov qword ptr [r14 + 0x17c], 0x3f800000
   0x1402dd259  49c786840100000000803f mov qword ptr [r14 + 0x184], 0x3f800000
   0x1402dd26b  41c786900100000000803f mov dword ptr [r14 + 0x190], 0x3f800000
   0x1402dd276  41c786940100000000803f mov dword ptr [r14 + 0x194], 0x3f800000
   0x1402dd361  498d9668010000 lea rdx, [r14 + 0x168]
```

### 7. Runs that were discarded (honesty)

```
$ ... python tmp/freebuff/scratch/tint2.py
Command timed out after 600 seconds
```
Discarded: disassembling all 188,670 `.pdata` functions was the wrong shape.

```
$ ... python tmp/freebuff/scratch/tint3.py
byte-pattern store hits: 1340
candidate functions: 664
functions storing a full triple: 40
```
Discarded as evidence: a store triple at `+0x18/+0x28/+0x38` is common to many 0x168-byte
structures; the list of 40 functions is not specific to CarPaint.

```
$ ... python tmp/freebuff/scratch/tint6.py
disp32 xmm hits at +0x168/+0x178/+0x188: 363
```
Discarded for the same reason (the displacement alone does not identify the object).

### 8. Build and verify the deliverable

```
$ uv run --with pefile --with capstone python Tools/scripts/jc3_tint_write.py --write
wrote Research/JC3Grab/TINT_WRITE.md
  cbuffer Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt: 7 members, 76 B
  material vtable 0x14234e5f0, upload 0x140259f00
  writer 0x140289a80, callers ['0x1402dd36f']
  oracles 8/8
```

```
$ uv run --with pefile --with capstone python Tools/scripts/jc3_tint_write.py --check
OK 8/8 oracles, 76 B struct, upload 0x140259f00, writer 0x140289a80, md byte-identical
exit=0
```

## The values, labelled

### decoded (instruction/field + address, quoted in `TINT_WRITE.md`)

- cbuffer `CarPaintDynamicMaterialParams`, `Tools/JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt`:
  `m_TintColorR` @0, `m_TintColorG` @16, `m_TintColorB` @32, `_unused` @48,
  `m_SpecularGlossOverride` @64, `m_MetallicOverride` @68, `m_ClearCoatOverride` @72; 76 B.
- `0x142d45680` type_info, `0x14286e928` COL, `0x14234e5f0` vtable for
  `CSyncedShaderConstantData<SCarPaintDynamicMaterialParams>`; the object-params twin is
  `0x142d45610 / 0x14286e8a8 / 0x14234e580`.
- `0x140259f00` (vtable slot 0) is the constant-buffer update:
  `mov eax, [rdx + 0x448]`, `and eax, 1`, `imul rax, rax, 0x4c`, `lea r8, [rax + rcx + 0x18]`,
  `add rcx, 0xb0`, `jmp 0x1400b1960`.
- `0x140289a80` is the 76-byte CPU fill: source `[rdi]`, `[rdi+0x10]`, `[rdi+0x20]`,
  `[rdi+0x30]`, `[rdi+0x40]` (movsd), `[rdi+0x48]` (dword) → destination
  `[rax+rsi+0x18]`, `+0x28`, `+0x38`, `+0x48`, `+0x58`, `+0x60`, with
  `mov edx, 0x4c` creating the GPU buffer at `+0xb0`.
- `0x1402dd36f` is its only caller, with `lea rdx, [r14 + 0x168]` and `lea rcx, [r14 + 0x98]`.
- `0x1402dd1a0` seeds the identity basis: `0x3f800000` at `+0x168`, `+0x174`, `+0x17c`,
  `+0x184`, `+0x190`, `+0x194` with zeroed dwords between.

### derived (rule + inputs)

- Because the writer copies in the cbuffer's member order, block `+0x168 → +0x178 → +0x188`
  maps to source `+0x00 → +0x10 → +0x20`, which maps to `m_TintColorR → G → B`.
- The 4th float4 at source `+0x30`/cbuffer `+0x30` is `_unused`, so the three override floats
  are source `+0x40..+0x48` → cbuffer `+0x40..+0x48` (offsets 64/68/72) — consistent with the
  ctor zeroing `+0x1a8/+0x1b0`.
- Parity: 76-byte copies at `+0x18` (parity 0) and `+0x64` (parity 1), selected by
  `[rdx+0x448] & 1` in the update and by `[0x142d3a6ac] & 1` in the writer.

### UNKNOWN

- **Who writes block `+0x168`.** The writer has one caller, the block constructor; no other
  direct call in the image passes a 76-byte struct into that field. Tried: all callers of
  `0x140289a80` and `0x140289b20` (1 each), xrefs to the block constructor, an immediate
  search for the CarPaintMM block hash `0x483304D6` (0 hits in `.text` — the block type is
  selected by a vtable, not by a hash compare), a disp8 triple-store sweep (1,340 hits) and a
  disp32 sweep at `+0x168/+0x178/+0x188` (363 hits) — neither is specific enough to be
  evidence. Where it would be found: the CarPaint block object is handed to the render/material
  system and updated through its own interface; the next step is a virtual-call-aware walk from
  the block vtable, which this card does not have an oracle for.
- **Shader-side meaning of the three float4s.** They are uploaded as `m_TintColorR/G/B` but
  carry a 3×3-looking basis (`0.14, 0.19, 0.25, 1`, etc.); the shader body is not on disk
  (`COLOUR.md` §6.1).
- **Palette → tint.** `COLOUR.md` §4 already showed no asset names the palette; this card does
  not reach the palette record either.
- **On-screen colour.** Out of scope by the brief and not attempted.

## Notes on the brief's escape clause

The trail does reach a virtual dispatch: the upload itself is vtable slot 0 of
`CSyncedShaderConstantData<SCarPaintDynamicMaterialParams>` (called through the block object's
member), and the block object is updated through its class interface rather than by any direct
call visible in the image. Per the brief, the card stops there and says so instead of naming a
tint writer it cannot prove.

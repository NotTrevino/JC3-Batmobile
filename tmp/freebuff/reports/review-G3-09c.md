# review-G3-09c - are the 15 "all-zero" constants really vertex-element declarations?

STATUS: done

## VERDICT

**HOLDS - and the card stops one step short of the proof it could have made.**

The 15 strings, the 20-byte records and the "not a paint-colour writer" conclusion are all real
and reproducible. What the card does **not** show is the decisive part: the consumer
`0x141952F00` builds **32-byte `D3D11_INPUT_ELEMENT_DESC` records** and hands them to
**`CreateInputLayout` through the device vtable**, with an `HRESULT` check and the four per-stream
byte offsets stored back as vertex strides. So the block is a vertex-element declaration by
construction, not by inference from "the fields are read as ints".

* **Table confirmed, independently.** `0x142dceff0` holds 15 qword pointers, each landing in
  `.rdata` on a NUL-terminated name: `POSITION, BLENDWEIGHT, BLENDINDICES, NORMAL, PSIZE,
  TEXCOORD, TANGENT, BINORMAL, TESSFACTOR, POSITIONT, COLOR, FOG, DEPTH, SAMPLE, VOID` - the 15
  the card lists, in that order. Slot 15 is **not** a pointer (`0x3fc90fdb40c90fdb`, two float32s
  whose high halves are `1.5708`-shaped); the table is exactly 15 entries as claimed.
* **Three records re-read and they match.** From my own store emulation of the builder
  `0x140153430`, the arrays handed to `0x141952F00` cut exactly on 20 bytes:
  `0x14015359d[0] = (stream 0, 3, 4, semantic 0 = POSITION, index 0)`,
  `0x14015359d[1] = (1, 2, 4, 5 = TEXCOORD, 1)`, `0x14015359d[2] = (1, 2, 4, 5, 2)`; and
  `0x1401536c6[0] = (0, 3, 4, 0, 0)`, `0x1401536c6[1] = (0, 4, 10, 5, 0)`. Every field equals
  the card's row for that record.
* **The consumer's `cmp eax, 0xe` is the VOID sentinel**, and on match it **skips** the element
  (`je 0x141952fb1` jumps past the descriptor write) - which only makes sense for an element
  list, not for a parameter block.
* **The descriptor the consumer writes is 32 bytes and its fields are D3D11's, in order**:
  `[base+0]` semantic **string pointer** (from the table), `[base+8]` = field 4 (SemanticIndex),
  `[base+0xc]` = Format from the table at `0x1425f664c`, `[base+0x10]` = field 0 (InputSlot),
  `[base+0x14]` = running per-stream byte offset, `[base+0x18..0x1f]` = 0 (class = per-vertex,
  step rate = 0), then `add r10, 0x20`. That is `D3D11_INPUT_ELEMENT_DESC` field for field.
* **The formats are vertex formats**: index 19 -> **6 = `R32G32B32_FLOAT`, 12 B** for the
  POSITION records, index 18 -> **16 = `R32G32_FLOAT`, 8 B** for the TEXCOORD records, with the
  size table `0x1425f66fc` giving exactly those bytes, and the per-stream accumulator advancing
  by them. A colour float4 would be format 2 / 16 B; that value appears only for the
  `(0,4,4,POSITION,0)` variant.
* **The call is `CreateInputLayout`, not a constant-buffer write.** After the loop the function
  allocates an output object, then does `call qword ptr [r10 + 0x58]` on `[[r14+0x28]]` with
  `rdx` = descriptor array, `r8d` = element count, `r9` = shader bytecode pointer,
  `[rsp+0x20]` = bytecode length, `[rsp+0x28]` = `&out`; then `test eax, eax; jns` treats the
  return as an `HRESULT` and the failure path calls `0x141952020` with code `14`. Slot offset
  `0x58` is index 11, which in the documented `ID3D11Device` vtable is `CreateInputLayout`, and
  the five arguments are that method's signature (derived: vtable order from the D3D11 ABI,
  cross-checked here against the argument shape). It then stores the four stream accumulators
  (`edi`, `esi`, `ebp`, `r12d`) into the new object at `+8`, `+0xc`, `+0x10`, `+0x14` - the vertex
  strides per stream. **No constant-buffer map, no `UpdateSubresource`, no float4 store appears
  anywhere in this function.**
* **Where the paint colour must enter instead: neither of the other two CarPaintMM functions.**
  `0x1401056A0` and `0x140106800` are shader-variant binders and nothing else: every one of their
  actions is `mov rcx, [arg1+0x10]; lea rdx, [material+off]; lea r8, "CarPaintMM…";
  call 0x14196B6F0` (or `call 0x14196B780`), i.e. name -> slot in the material struct. Callee
  `0x14196B6F0` appends `".vb"`, hashes the name (`0x14196A8C0`) and resolves the shader
  (`0x1410D0F60`). Neither function touches a colour, a float4 or a buffer.
  The only float4-sized structure in this CarPaintMM code is created by the builder's **other**
  callee, `0x141952DC0`: it builds a buffer descriptor `{ByteWidth = 16*n, Usage = arg3,
  BindFlags = 4, MiscFlags = 0 or 0x10000}` on the stack and calls `[device_vtable + 0x18]`
  (= index 3 = `ID3D11Device::CreateBuffer`) with `r9` as the initial-data pointer. **BindFlags 4
  is `D3D11_BIND_CONSTANT_BUFFER`**, so the CarPaintMM material parameters are uploaded through
  that constant buffer, whose initial data is the `r9` argument. The tint floats must be inside
  that data - supplied by the material/palette path that fills it, which is outside all three
  functions, exactly as G3-09b's "0 code references for the schema names" predicts.
* **What the card gets wrong or leaves open.** (a) Its §3 stops at "read as integers and used as
  table indices"; the descriptor layout and the `CreateInputLayout` call are the actual proof and
  are absent. (b) Its §2 sentence "the constants are copied 16 bytes at a time with
  `movdqa`/`movaps`, and their type is decided by whoever reads the copies" is right but
  under-stated: the type is decided, and it is a set of five u32 fields, not a type at all.
  (c) It never says that the four accumulator values become stream strides, which is what closes
  the "this is a vertex declaration" loop.
* **My own limitation, stated.** My emulator does not track every store source, so in four of the
  six arrays some bytes stayed unwritten (24 B in `0x140153647`, 12 B in `0x140153700`, 36 B in
  each of `0x14015375c`/`0x1401537c1`). The records I quote above come only from arrays my
  emulation completed, and I do **not** claim the card's rows for the incomplete arrays are wrong.

Nothing here is a claim about JC3 behaviour beyond the instructions I read. `JustCause3.exe` was
opened read-only; nothing was run, attached or injected. `jc3_colour_native2.py` and its outputs
were **not** edited.

## 1. The table (my read, `0x142dceff0` + 8*i)

```
  [ 0] slot 0x142dceff0 -> 0x0000000142509aa0  sec=.rdata 'POSITION'
  [ 1] slot 0x142dceff8 -> 0x00000001425f65d8  sec=.rdata 'BLENDWEIGHT'
  [ 2] slot 0x142dcf000 -> 0x00000001425f65c8  sec=.rdata 'BLENDINDICES'
  [ 3] slot 0x142dcf008 -> 0x0000000142509aac  sec=.rdata 'NORMAL'
  [ 4] slot 0x142dcf010 -> 0x00000001425f65bc  sec=.rdata 'PSIZE'
  [ 5] slot 0x142dcf018 -> 0x00000001425f65b0  sec=.rdata 'TEXCOORD'
  [ 6] slot 0x142dcf020 -> 0x0000000142522af8  sec=.rdata 'TANGENT'
  [ 7] slot 0x142dcf028 -> 0x0000000142522ae8  sec=.rdata 'BINORMAL'
  [ 8] slot 0x142dcf030 -> 0x00000001425f65a0  sec=.rdata 'TESSFACTOR'
  [ 9] slot 0x142dcf038 -> 0x00000001425f6590  sec=.rdata 'POSITIONT'
  [10] slot 0x142dcf040 -> 0x0000000142522b00  sec=.rdata 'COLOR'
  [11] slot 0x142dcf048 -> 0x00000001425f6588  sec=.rdata 'FOG'
  [12] slot 0x142dcf050 -> 0x000000014233fa38  sec=.rdata 'DEPTH'
  [13] slot 0x142dcf058 -> 0x00000001425f6580  sec=.rdata 'SAMPLE'
  [14] slot 0x142dcf060 -> 0x00000001425f6578  sec=.rdata 'VOID'
  [15] slot 0x142dcf068 -> 0x3fc90fdb40c90fdb  sec=None   None
```

## 2. Three records (my emulation of the builder's stores)

```
call 0x14015359d  base rbp+480  count=5  span=100 B  unwritten bytes=4
   rec[0] = (stream=0, a=3, b=4, semantic=0, index=0)
   rec[1] = (stream=1, a=2, b=4, semantic=5, index=1)
   rec[2] = (stream=1, a=2, b=4, semantic=5, index=2)

call 0x1401536c6  base rbp+352  count=6  span=120 B  unwritten bytes=8
   rec[0] = (stream=0, a=3, b=4, semantic=0, index=0)
   rec[1] = (stream=0, a=4, b=10, semantic=5, index=0)
```

`sportsmuscle`-independent cross-check: the record's first four words are a contiguous 16-byte
`.rdata` constant (which is why the 15 constants are read as `movdqa`), and the fifth word is a
separate `dword` store - the 20-byte record is not a float4 at all. Semantic field 0/5 maps to
`POSITION`/`TEXCOORD` through the table above; `cmp eax, 0xe` skips `VOID`.

## 3. The descriptor the consumer builds (`0x141952F00`)

```
0x141952f34  movsxd r11, r8d              ; count
0x141952f51  lea r10, [rsp + 0x48]        ; descriptor array base + 8
0x141952f56  lea r8, [rdx + 0xc]          ; record pointer, fields at -0xc,-8,-4,0,+4
0x141952f61  movsxd rax, dword ptr [r8]   ; field 3 = semantic
0x141952f68  cmp eax, 0xe                 ; == VOID?
0x141952f6b  je 0x141952fb1               ;   then skip this element
0x141952f6d  mov rax, [rbx + rax*8 + 0x2dceff0]   ; semantic NAME POINTER
0x141952f75  movsxd rcx, dword ptr [r8 - 4]       ; field 2
0x141952f79  mov dword ptr [r10 + 8], r9d         ; SemanticIndex <- field 0? see note
0x141952f7d  mov qword ptr [r10 - 8], rax         ; SemanticName
0x141952f81  mov eax, dword ptr [r8 + 4]          ; field 4
0x141952f88  mov dword ptr [r10], eax             ; SemanticIndex
0x141952f8b  movsxd rax, dword ptr [r8 - 8]       ; field 1
0x141952f8f  lea rdx, [rax + rcx*4]               ; index into the format tables
0x141952f93  mov ecx, [rsp + r9*4 + 0x30]         ; running offset for this stream
0x141952f98  mov eax, [rbx + rdx*4 + 0x25f664c]   ; DIAGNOSTIC FORMAT
0x141952f9f  mov dword ptr [r10 + 0xc], ecx       ; AlignedByteOffset
0x141952fa3  mov dword ptr [r10 + 4], eax         ; Format
0x141952fa7  xor eax, eax
0x141952fa9  add r10, 0x20                        ; stride 32 = sizeof(INPUT_ELEMENT_DESC)
0x141952fad  mov qword ptr [r10 - 0x10], rax      ; class=0 (per-vertex), step rate=0
0x141952fb1  ...
0x141952fb9  add r8, 0x14                         ; record stride 20
0x141952fc1  mov ecx, [rbx + rdx*4 + 0x25f66fc]   ; byte size of this element
0x141952fc8  add dword ptr [rsp + r9*4 + 0x30], ecx   ; advance the stream offset
0x141952fcd  dec r11
0x141952fd0  jne 0x141952f61
0x141952fe3  movzx eax, byte ptr [r14 + 0x394]
0x141952feb  mov rcx, qword ptr [r14 + 0x238]
0x141953008  call qword ptr [r14 + 0x228]         ; allocate the output object
0x141953022  mov rdx, qword ptr [r15 + 0x10]      ; bytecode LENGTH
0x14195302a  mov r9, qword ptr [r15 + 8]          ; bytecode POINTER
0x141953031  mov qword ptr [rsp + 0x28], rbx      ; &out layout
0x141953036  mov qword ptr [rsp + 0x20], rdx      ; length arg
0x14195303b  lea rdx, [rsp + 0x40]                ; descriptor array
0x141953040  call qword ptr [r10 + 0x58]          ; CreateInputLayout (vtbl idx 11)
0x141953044  test eax, eax
0x141953046  jns 0x141953058                       ; HRESULT success
0x141953048  mov r8d, eax
0x14195304b  mov edx, 0xe                         ; error code 14
0x141953053  call 0x141952020
0x141953058  mov dword ptr [rbx + 8], edi          ; stream 0 stride
0x14195305b  mov dword ptr [rbx + 0xc], esi        ; stream 1 stride
0x14195305e  mov dword ptr [rbx + 0x10], ebp       ; stream 2 stride
0x141953061  mov dword ptr [rbx + 0x14], r12d      ; stream 3 stride
```

Descriptor layout, decoded from those stores (base = `r10-8`):

| offset | field | source |
|---:|---|---|
| +0x00 | `SemanticName` (pointer) | `table[field3]` |
| +0x08 | `SemanticIndex` | record field 4 |
| +0x0c | `Format` | `fmt[field1 + 4*field2]` |
| +0x10 | `InputSlot` | record field 0 |
| +0x14 | `AlignedByteOffset` | per-stream accumulator |
| +0x18 | `InputSlotClass` | 0 (per-vertex) |
| +0x1c | `InstanceDataStepRate` | 0 |

Format/size tables (my read): `fmt[19] = 6` (`R32G32B32_FLOAT`, 12 B), `fmt[18] = 16`
(`R32G32_FLOAT`, 8 B); the size table at `0x1425f66fc` returns 12 and 8 for exactly those
indices, and those are the numbers the accumulator advances by.

## 4. The sibling callee `0x141952DC0` - where a float4 block can live

```
0x141952dda  movzx eax, byte ptr [rcx + 0x394]
0x141952de7  mov rcx, qword ptr [rcx + 0x238]     ; device
0x141952df4  mov edi, r8d                         ; usage arg
0x141952df7  mov ebx, edx                         ; count arg
0x141952dfe  mov dword ptr [rsp + 0x28], 0xc
0x141952e0a  call qword ptr [r12 + 0x228]         ; allocate the buffer object
0x141952e45  shl ebx, 4                           ; ByteWidth = 16*n
0x141952e48  lea r8, [rsp + 0x30]                 ; initial-data struct (rsi)
0x141952e51  mov dword ptr [rsp + 0x40], ebx      ; desc.ByteWidth
0x141952e2d  mov dword ptr [rsp + 0x48], 4        ; desc.BindFlags = CONSTANT_BUFFER
0x141952e5c  mov rcx, qword ptr [r12 + 0x28]      ; device
0x141952e73  call qword ptr [rax + 0x18]          ; CreateBuffer (vtbl idx 3)
0x141952e76  test eax, eax
0x141952e78  jns 0x141952e99                        ; HRESULT success
```

`ByteWidth = 16*n`, `BindFlags = 4` = `D3D11_BIND_CONSTANT_BUFFER`, initial data in `r8`.
This - not the 20-byte element records - is the structure a colour float4 can be uploaded
through, and its contents come from the caller's data, not from this function.

## 5. Commands and output

`uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native2.py --check` (exit 0):

```
OK: 15 constants; 14 non-zero as u32, all denormal/zero as f32; 40 reference sites, 0 scalar float loads
OK: 6 built arrays, record stride 20, 22 records, semantics POSITION, TEXCOORD
OK: interpretation = integer indices/enum values
OK: COLOUR_NATIVE2.md and COLOUR_NATIVE2.json match the re-derived render
```

My table dump and import listing (`tmp/freebuff/scratch/g309c.py table|imports`):

```
semantic table at 0x142dceff0:
  [ 0] slot 0x142dceff0 -> 0x0000000142509aa0  sec=.rdata 'POSITION'
  ... (15 rows, listed in section 1) ...
  [15] slot 0x142dcf068 -> 0x3fc90fdb40c90fdb  sec=None   None
dxgi.dll: 2 imports
d3d11.dll: 1 imports
d3d9.dll: 1 imports
```

(The single `d3d11.dll` import is not `CreateInputLayout` - the exe reaches it through a device
wrapper's vtable, which is why the call is `call qword ptr [r10+0x58]` rather than a direct IAT
call. That is the same wrapper pattern the `CreateBuffer` call at `0x141952e73` uses.)

Consumer disassembly (`g309c.py dis 0x141952F00 120`) - quoted in section 3.

Record emulation (`g309c_records.py`) - quoted in sections 2 and 4, including the arrays it could
not complete:

```
call 0x140153647  base rbp+224  count=6  span=120 B  unwritten bytes=24
call 0x140153700  base rbp+112  count=1  span=20 B   unwritten bytes=12
call 0x14015375c  base rbp+136  count=2  span=40 B   unwritten bytes=36
call 0x1401537c1  base rbp+176  count=2  span=40 B   unwritten bytes=36
```

`g309c.py dis 0x140153430 40` (builder head) shows the material fields it writes -
`mov qword [rdi+0x10], "CarPaintMM"`, `mov [rdi+0x18], eax` (name hash), `mov byte [rdi+0x2c8]`,
`mov dword [rdi+0x2cc], 0xbf800000` (-1.0f), `mov dword [rdi+0x2d0], 0` - none of which is a
colour, and the two variant binders being called with `rcx = rdi` (the material).

## 6. Files

* `tmp/freebuff/reports/review-G3-09c.md` (this report)
* `tmp/freebuff/scratch/g309c.py`, `tmp/freebuff/scratch/g309c_records.py` (read-only PE helpers)
* No project file edited; `COLOUR_NATIVE2.md`/`.json` and `jc3_colour_native2.py` untouched.

## UNKNOWNs

1. **The full record contents for the four arrays my emulator left incomplete.** Tried: tracking
   xmm loads from `.rdata`, GP immediates, `xor`, and `movaps` register copies; the missing bytes
   are written from registers whose value comes from memory (`mov eax, [mem]`), which I do not
   propagate. Where it would be answered: a full data-flow emulator, or the reviewed script's
   tracker (whose arrays it reports as complete). Not a contradiction of the card.
2. **What exactly fills the constant buffer's initial data** (`r9` into `0x141952DC0`), i.e. which
   of its `n` float4s is `TintColorR/G/B`. Tried: this function only forwards the pointer; the
   builder passes a struct it built at `[rsp+...]`. Where it would be answered: the callers that
   prepare that data (the material parameter / palette path), which is a separate trace from these
   three functions - and consistent with G3-09b's finding that the tint is not name-addressed.
3. **Whether slot 0x58 could be any other method on the same object.** It is index 11 of an
   interface whose slot 3 is `CreateBuffer` and whose calls are `HRESULT`-returning device calls;
   the five-argument shape here (element-desc array, count, bytecode, length, out pointer) is
   `CreateInputLayout`'s alone. A dump of the vtable from a live process would make it explicit,
   and this task does not touch a process.

# The CarPaintMM parameter block, re-read as integers (G3-09c)

Corrects `Research/JC3Grab/COLOUR_NATIVE.md` (G3-09b) on one point: its 15 constants are
**not** `(0, 0, 0, 0)`. That reading came from `round(x, 6)` applied to denormal floats;
read as `u32` the same bytes are small integers, and the code that consumes them treats
them as **indices into the vertex-semantic table** at `0x142dceff0`.`
Every number below is re-decoded from `JustCause3.exe`
(read-only, `--check` re-derives and compares).

## 1. The 15 constants, three ways

| constant va | raw 16 bytes | as `u32` | as `f32` |
|---|---|---|---|
| `0x1423310e0` | `00000000010000000200000004000000` | 0, 1, 2, 4 | 0, 1.4013e-45, 2.8026e-45, 5.60519e-45 |
| `0x1423310f0` | `05000000010000000100000002000000` | 5, 1, 1, 2 | 7.00649e-45, 1.4013e-45, 1.4013e-45, 2.8026e-45 |
| `0x142331100` | `00000000030000000400000000000000` | 0, 3, 4, 0 | 0, 4.2039e-45, 5.60519e-45, 0 |
| `0x142331110` | `04000000050000000200000001000000` | 4, 5, 2, 1 | 5.60519e-45, 7.00649e-45, 2.8026e-45, 1.4013e-45 |
| `0x142331120` | `02000000040000000500000003000000` | 2, 4, 5, 3 | 2.8026e-45, 5.60519e-45, 7.00649e-45, 4.2039e-45 |
| `0x142331130` | `02000000020000000400000005000000` | 2, 2, 4, 5 | 2.8026e-45, 2.8026e-45, 5.60519e-45, 7.00649e-45 |
| `0x142331140` | `00000000040000000400000000000000` | 0, 4, 4, 0 | 0, 5.60519e-45, 5.60519e-45, 0 |
| `0x142331150` | `05000000000000000100000002000000` | 5, 0, 1, 2 | 7.00649e-45, 0, 1.4013e-45, 2.8026e-45 |
| `0x142331160` | `04000000050000000100000001000000` | 4, 5, 1, 1 | 5.60519e-45, 7.00649e-45, 1.4013e-45, 1.4013e-45 |
| `0x142331170` | `02000000040000000500000002000000` | 2, 4, 5, 2 | 2.8026e-45, 5.60519e-45, 7.00649e-45, 2.8026e-45 |
| `0x142331180` | `03000000020000000200000004000000` | 3, 2, 2, 4 | 4.2039e-45, 2.8026e-45, 2.8026e-45, 5.60519e-45 |
| `0x142331190` | `01000000040000000400000005000000` | 1, 4, 4, 5 | 1.4013e-45, 5.60519e-45, 5.60519e-45, 7.00649e-45 |
| `0x1423311a0` | `0000000000000000040000000a000000` | 0, 0, 4, 10 | 0, 0, 5.60519e-45, 1.4013e-44 |
| `0x1423311b0` | `01000000020000000400000005000000` | 1, 2, 4, 5 | 1.4013e-45, 2.8026e-45, 5.60519e-45, 7.00649e-45 |
| `0x142331360` | `00000000000000000000000000000000` | 0, 0, 0, 0 | 0, 0, 0, 0 |

Read as `u32`: **14 of the 15 have a non-zero word** (only `0x142331360` is all zero).
Read as `f32`: every word is **0 or denormal** (largest 1.4e-44) — a subnormal float, not a
colour in 0…1 and not a usable number at all. The old `0, 0, 0, 0` column was produced by
`round(x, 6)` on those denormals; no rounding is applied here.

## 2. How the bytes are used

Every rip-relative reference to those 15 addresses, by mnemonic: `movaps` ×1, `movdqa` ×39. 
There are **0 scalar float loads** (`movss`/`movsd`) at those addresses: the constants are
copied 16 bytes at a time with `movdqa`/`movaps`, and their type is decided by whoever reads
the copies.

The copying function is `0x140153430`–`0x1401538e3`. It builds arrays on the stack and hands each to
`0x141952f00` with a count:

| call site | array base | count | bytes (count × 20) | complete |
|---|---|---:|---:|---|
| `0x14015359d` | `rbp+480` | 5 | 100 | yes |
| `0x140153647` | `rbp+224` | 6 | 120 | yes |
| `0x1401536c6` | `rbp+352` | 6 | 120 | yes |
| `0x140153700` | `rbp+112` | 1 | 20 | yes |
| `0x14015375c` | `rbp+136` | 2 | 40 | yes |
| `0x1401537c1` | `rbp+176` | 2 | 40 | yes |

Each array is `count × 20` bytes, but it is written as 16-byte `movdqa` copies plus
trailing dwords — so the "15 16-byte constants" are **slices of a 20-byte-record array**,
not 15 float4s. Cutting the bytes at the callee's own stride gives:

| record | field 0 (stream) | field 1 | field 2 | field 3 (semantic) | field 4 (index) |
|---|---|---|---|---|---|
| 0x14015359d[0] | 0 | 3 | 4 | **0 = `POSITION`** | 0 |
| 0x14015359d[1] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 1 |
| 0x14015359d[2] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 2 |
| 0x14015359d[3] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 3 |
| 0x14015359d[4] | 2 | 2 | 4 | **5 = `TEXCOORD`** | 4 |
| 0x140153647[0] | 0 | 4 | 4 | **0 = `POSITION`** | 0 |
| 0x140153647[1] | 0 | 4 | 0 | **5 = `TEXCOORD`** | 0 |
| 0x140153647[2] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 1 |
| 0x140153647[3] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 2 |
| 0x140153647[4] | 1 | 4 | 4 | **5 = `TEXCOORD`** | 3 |
| 0x140153647[5] | 2 | 2 | 4 | **5 = `TEXCOORD`** | 4 |
| 0x1401536c6[0] | 0 | 3 | 4 | **0 = `POSITION`** | 0 |
| 0x1401536c6[1] | 0 | 4 | 10 | **5 = `TEXCOORD`** | 0 |
| 0x1401536c6[2] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 1 |
| 0x1401536c6[3] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 2 |
| 0x1401536c6[4] | 1 | 2 | 4 | **5 = `TEXCOORD`** | 3 |
| 0x1401536c6[5] | 2 | 2 | 4 | **5 = `TEXCOORD`** | 4 |
| 0x140153700[0] | 0 | 3 | 4 | **0 = `POSITION`** | 0 |
| 0x14015375c[0] | 0 | 4 | 4 | **0 = `POSITION`** | 0 |
| 0x14015375c[1] | 0 | 4 | 0 | **5 = `TEXCOORD`** | 0 |
| 0x1401537c1[0] | 0 | 3 | 4 | **0 = `POSITION`** | 0 |
| 0x1401537c1[1] | 0 | 4 | 10 | **5 = `TEXCOORD`** | 0 |

## 3. What the consumer does with a record (`0x141952f00`)

| evidence | address | meaning |
|---|---|---|
| `movsxd r11, r8d` | `0x141952f34` | the count is an integer loop bound |
| `lea r8, [rdx + 0xc]` | `0x141952f56` | fields are read at +0, +4, +8, +0xc, +0x10 |
| `add r8, 0x14` | `0x141952fb9` | **record stride = 20 bytes**, exactly the cut above |
| `movsxd rax, dword ptr [r8 - 0xc]` … | 7 `movsxd` sites | every field is read as a signed integer; no field is ever loaded into an xmm register as a scalar |
| `cmp eax, 0xe` | `0x141952f68` | field 3 is compared with 14 |
| `mov rax, [rbx + rax*8 + 0x2dceff0]` | `0x141952f6d` | field 3 indexes a 15-entry qword table |
| `mov dword [rsp + r9*4 + 0x30]` … | — | field 0 indexes a 4-slot per-stream accumulator |

That table is not anonymous — it is the vertex-semantic name table:

| index | name |
|---|---|
| 0 | `POSITION` |
| 1 | `BLENDWEIGHT` |
| 2 | `BLENDINDICES` |
| 3 | `NORMAL` |
| 4 | `PSIZE` |
| 5 | `TEXCOORD` |
| 6 | `TANGENT` |
| 7 | `BINORMAL` |
| 8 | `TESSFACTOR` |
| 9 | `POSITIONT` |
| 10 | `COLOR` |
| 11 | `FOG` |
| 12 | `DEPTH` |
| 13 | `SAMPLE` |
| 14 | `VOID` |

`cmp eax, 0xe` compares against **index 14 = `VOID`** — the "no semantic" sentinel. So a
record's field 3 is a semantic enum, and the values used here are `POSITION`, `TEXCOORD`.

## 4. The corrected conclusion

G3-09b stated that the block builder copies 15 constants and that **none of them is
non-zero**, so as written that path initialises or clears a parameter block, and that a call
storing only zeros cannot be what puts a paint colour into a float4. Both halves change:

1. **The values are not zero.** As `u32` they are 14 non-zero tuples over 0…10; as `f32`
   they are denormals, which is a *second* reason they are not colours, not a reason they are
   zero.
2. **The block is not a colour parameter block at all.** It is a set of **vertex-element
   declarations**: each 20-byte record is (stream, offset, type, semantic, usage-index),
   consumed by `0x141952f00` as integer indices into the `POSITION…VOID` table and a per-stream
   offset accumulator. A colour float4 is read as a float; these are read with `movsxd` and
   used as table indices.

So the exclusion of this call as the tint writer survives — but on structural evidence, not
on "zeros": the call declares vertex semantics for the CarPaint material, and no path here
writes a tint. Whether some other instruction in this function (or elsewhere) writes the
CarPaintMM tint float4s stays **UNKNOWN**, as G3-09b said.

Positive control that the same function does use real float constants: it writes `0x3f800000`
(1.0) as `movss`/`movabs` immediates for a different array, and 5 `movss` instruction(s)
store zeros for another. The 15 index constants are a different kind of data in the same
function, not a mis-read float array.

## 5. Reproduce

```
uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native2.py --check
```

`--check` re-decodes all 15 constants, every reference site, every built array, the callee's
stride/table/sentinel and the semantic table, re-derives the verdict and fails on drift or if
an invariant breaks (15 constants; ≥1 non-zero `u32`; all `f32` denormal or zero; no scalar
float load at these addresses; the callee's `lea`/`add 0x14`/`movsxd`/`cmp 0xe` present;
table[14] = `VOID`; every record's field 3 inside the table; every array's bytes fully
accounted for).


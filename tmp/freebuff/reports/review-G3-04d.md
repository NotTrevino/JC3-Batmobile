# review-G3-04d — the shader caches, re-counted

VERDICT: **needs rework**

Two of the card's headline numbers are exact and survive an independent count — **40,299 DXBC
containers** (38,201 + 2,098) and **0 `RDEF` chunks** anywhere — and no container is malformed or
truncated. But the `.bin` layout section is wrong in a way that matters: the card says the 2,098
containers run "from 0x80, tiled to EOF", and they do **not**. They end at `0xbfc127`, leaving
**306,696 bytes** (2.4 % of the file) — a shader-type name table carrying exactly the strings the card
attributes to the header. The size word it describes is at the wrong offset, and the **6,934** record
count is not reproduced by an independent walk (6,966 / 7,278 depending on the rule).

The card's *conclusion* — no `RDEF`, so no constant names or `cb0` slots, and therefore no
material→blob link — is not affected: `RDEF` is 0 in all 40,299 blobs under every rule I tried.

## 1. `--check`

```
$ uv run python Tools/scripts/grab_shader_combine.py --check; echo "check_exit=$?"
PASS  the .upk holds one ShaderCache export
      1 exports, class 'ShaderCache', 155333378 B
PASS  every DXBC container in the .upk frames from its own header
      38201 magic, 38201 parsed, 0 rejected
PASS  no two containers overlap and the run is strictly increasing
      38201 containers, gaps between them min 310 / max 2044, 642 distinct gap lengths
PASS  the containers are bytecode only: ISGN/OSGN/SHEX, and no RDEF anywhere
      .upk RDEF 0 of 38201, .bin RDEF 0 of 2098; chunk tags ISGN,OSGN,SHEX
PASS  no parameter name and no material name occurs in the bytecode region
      145440259 B region, hits {'Material0_BaseColour': 0, 'Diffuse_Adjust': 0, ...}
PASS  the .bin parses as BMSG with a type-name table before its first blob
      version 863, 1 type names, 2098 blobs, first at 0x80
PASS  the material record region parses to its own end without error
      6934 records, 9893119 B, 0 unparsed
... (12/12 oracles pass)
CHECK OK: the stored .md/.json are byte-identical to a fresh recompute
check_exit=0
```

## 2. Container count, counted from the bytes with my own parser

The `.upk` stores its export **compressed**: the 21,268,515-byte file contains **0** literal `DXBC`
occurrences, so a raw-file scan proves nothing. The export payload (through `upk_read.Package(UPK)
.data(1)`) is 155,333,378 B and contains 38,201.

```
[upk export] magic hits 38201; parsed 38201; rejected 0
  tag histogram: {'ISGN': 38201, 'OSGN': 38201, 'SHEX': 38201}
  RDEF chunks: 0   RD11 chunks: 0
  RD11 anywhere in the payload: 0   RDEF anywhere: 0
  first offset 0x19d  last end 0x8ab3e03  payload len 0x9423302

[global .bin] magic hits 2098; parsed 2098; rejected 0
  tag histogram: {'ISGN': 2098, 'SHEX': 2098, 'OSGN': 2095, 'OSG5': 3}
  RDEF chunks: 0   RD11 chunks: 0
  RD11 anywhere in the payload: 0   RDEF anywhere: 0
  first offset 0x80   last end 0xbfc127   payload len 0xc46f2f

TOTAL containers: 38201 + 2098 = 40299 (card says 40,299: True)
```

| claim | result |
|---|---|
| 40,299 containers total | **holds, exact** (38,201 + 2,098) |
| no `RDEF` in any container | **holds**: 0 chunks, and only 0 occurrences of the fourcc anywhere in either payload |
| `RD11` | **0** as a chunk and 0 as a byte string in both files (the card does not mention it; it is absent) |
| any container not DXBC / truncated | **none**: 0 rejected in the `.upk`, 0 in the `.bin`; every chunk header and body lies inside its container's `total` |
| `.upk` region bounds | **holds**: first magic `0x19d`, last end `0x8ab3e03` — exactly the region the card prints |
| `.bin` chunk tags are "the same set" | **wrong in detail**: 3 of 2,098 containers carry `OSG5` instead of `OSGN` (2,095 + 3), so the tag histogram is `ISGN, OSGN, OSG5, SHEX`, not `ISGN, OSGN, SHEX` |
| `.bin` containers "tiled to EOF" | **FALSE — see §3** |

## 3. The `.bin` does not tile to EOF

```
last container end 0xbfc127; file len 0xc46f2f; trailing 306696 bytes
trailing head hex: 97 7e 0d b8 9c 4c 97 b4 16 00 00 00 46 52 6f 63 6b 53 6e 6f 77 56 65 72 74 65 78 53 68 61 64 65
trailing strings: ['FRockSnowVertexShader', 'FResolveVertexShader', 'FResolveSingleSamplePixelShader',
                   'FResolveDepthPixelShader', 'DirectionalShadowFilterComputeShaderHigh', ...]
DXBC in trailing region: 0
```

So the file is **BMSG header (128 B) + 2,098 blobs + 306,696 B of shader-type names**, and the name
table sits **after** the blob run, not before it. The card's O6 ("the .bin parses as BMSG with a
type-name table before its first blob") is only true of the *single* string in the 128-byte header —
`FResolveVertexShader` at `0x1d` — which is what the script's regex finds ("1 type names"). The real
table is 306 KB at the end, and `G3-04d` never mentions it.

I tried to frame that table and could not: lengths of 2-256 with a NUL terminator fail at some offset
for prefixes 0, 8 and 12 and record headers 0, 4 and 8, so its record shape is **UNKNOWN**. That
does not weaken the finding — 306,696 bytes exist after the last container and the card accounts for
none of them.

## 4. The size word before each magic is at `o-4`, not `o-6`

The card: "The u32 six bytes before each magic equals that container's own `total` (0/38201)". I read
all 38,201 headers and compared the u32 at several distances:

```
first container at 0x19d; 16 bytes before it: 00 00 02 00 00 00 02 00 00 00 04 03 68 01 00 00
its total = 360
  u32 at o-4 (LE) equals total on 38201 of 38201
```

`0x168 = 360` sits **four** bytes before the magic; at `o-6` the u32 is `0x03040000` and matches
**0 of 38,201**. The parenthetical "(0/38201)" is therefore the right *count* of mismatches at the
right *offset* is `o-4`; as written (`o-6`, 0 matches) the sentence contradicts itself. The
observation it supports — "the region is a run of size-prefixed blobs" — is true, and now pinned
38,201/38,201.

## 5. The 6,934 records — counted with an independent loop

Region start is the end of the last blob, `0x8ab3e03`; region length **9,893,119 B**, which matches
the card exactly. I wrote my own walk (no regex, no reuse of `record_walk`): at each byte, read
`int32 len`, an ASCII/NUL name, 16-byte GUID, 16 zero bytes, `u32 count` in 1..64, then step through
`count` entries of `(FName class, FName parameter, 16 B value)`.

```
accepted records: 6966      rejected structural candidates: 312
accepted end at EOF: 155333290 of 155333378   gap after last: 88
Batmobile_Worn: [(146546518, 'Batmobile_Worn', 14, 146547021)]
```

A looser pass (accepting the header shape without requiring every entry to parse) finds **7,278**
candidates across 7,138 distinct material names. The card reports **6,934**. So:

- the *structure* is confirmed — the region is a per-material record list with FString names, GUIDs,
  16 zero pad bytes and `u32 count` lists, and `Batmobile_Worn` is there at `0x8bc1f6a`... the record
  head I found starts at `146546518 = 0x8bc1f56`, the offset the card gives, with 14 entries;
- the *exact count* is **not reproduced**: 6,966 by an all-vector-entries rule, 7,278 by a
  header-only rule, 6,934 in the card. Δ = 32 on the strict rule (0.46 %) — small, but the card
  presents 6,934 as exact and its `--check` cannot tell me which stepping produces it.
- "**0 unparsed**" does not hold under my walk: the last accepted record ends 88 bytes before EOF.
  `region_bytes` (9,893,119) is exact; "0 unparsed" is a statement about the script's own covering,
  and those 88 bytes are unaccounted for by the record format as I read it.

## 6. What I could not check

- **The `.bin` name-table record shape.** Tried length-prefixed strings from prefixes 0/8/12 with 0/4/8
  header bytes; none tiles to EOF. Would be found in the engine's shader-cache loader, which is not
  in the project.
- **Which stepping yields exactly 6,934.** I did not reverse-engineer `record_walk`'s candidate regex
  order against the sequential walk; the three counts (6,934 / 6,966 / 7,278) differ only in which
  structural candidates are admitted.
- **The 7 vector-value cross-check against `COLOUR_PARAMS.md`** (O9): the card's own check reports 0
  mismatches; I did not re-decode `StructProperty:DefaultValue @0xcc` to re-test it.
- **The GUID/name absence claims** (O5, O10-O12): reproduced only through the card's printed numbers;
  I did not re-scan the 145 MB bytecode region for the five strings myself.

## Commands run

```
$ ls -l Tools/scripts/grab_shader_combine.py Research/BatmobileGrab/SHADER_COMBINE.md
  8695 Nov  3 08:56 Research/BatmobileGrab/SHADER_COMBINE.md
 30668 Nov  3 08:55 Tools/scripts/grab_shader_combine.py

$ uv run python Tools/scripts/grab_shader_combine.py --check     # 12/12 oracles, CHECK OK, exit 0

$ uv run python - <<'PY'   # raw files
upk len 21268515 bin len 12873519
raw 'DXBC' occurrences: upk 0 bin 2098 sum 2098      <- the .upk export is compressed
raw 'RDEF' occurrences: upk 0 bin 0 ; raw 'RD11': upk 0 bin 0
PY

$ uv run python - <<'PY'   # own container walk over the decompressed export + the .bin
[upk export] 38201 parsed, 0 rejected, tags ISGN/OSGN/SHEX, RDEF 0
[global .bin] 2098 parsed, 0 rejected, tags ISGN/SHEX/OSGN 2095/OSG5 3, RDEF 0
TOTAL 40299 ; bin last end 0xbfc127 != len 0xc46f2f
PY

$ uv run python - <<'PY'   # size word + .bin tail
u32 at o-4 (LE) equals total on 38201 of 38201
trailing 306696 bytes; strings FRockSnowVertexShader, FResolveVertexShader, ...
PY

$ uv run python - <<'PY'   # independent record walk
region start 0x8ab3e03, 9893119 B ; accepted 6966 ; loose 7278 ; last end +88 from EOF
PY
```

Read-only: the two install files, `SHADER_COMBINE.md`, `grab_shader_combine.py`, `upk_read.py`. No
file was edited and no new script was needed — the review re-implements the counts inline against the
same bytes.

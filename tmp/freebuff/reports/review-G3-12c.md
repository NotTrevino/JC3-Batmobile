# review-G3-12c — the `.ddsc` decode, re-run and hand-checked

VERDICT: **minor issues**

The decode itself holds: `--check` passes, 116/116 files close, the format counts are exact, and the
three format-87 files reconcile from their own bytes. **One claim is false**: the report calls
format 87's 64 B/block "the one place this pass adds a *new* fact … which neither earlier pass
reported". Both earlier cards report it — `DECODE_DEPTH2.md:54,:104` and `DECODE_DEPTH6.md:81,:194`
each carry `87 -> [64] B` with the same file count. The "two earlier passes" summary is otherwise
accurate. Everything this review could not check is listed at the end.

## 1. Re-run of the script

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/decode_depth5.py --check; echo "check_exit=$?"
PASS  the archive holds exactly the 116 .ddsc paths G3-12 graded PARTIAL
      116 in the archive, 116 in G3-12, 116 shared, 0 only-archive, 0 only-G3-12
PASS  every .ddsc names AVTX and closes as header_size + payload == file length
      116/116 close; header {'128': 116}; dimension-1 {'2': 116}; depth {'1': 116}
PASS  exactly one block size per file closes the stored mip chain
      single-candidate files 116/116; candidates seen [(8,), (16,), (64,)]
PASS  the format id -> block size map is a function across the fleet
      71 -> [8] B; 77 -> [16] B; 83 -> [16] B; 87 -> [64] B
PASS  the stored mip ranges tile [header_size, len) with zero residue
      116/116 files; 1013 mips stored
PASS  the omitted-mip table decodes: k records, prefix-sum offsets, level prices, tag 16
      116/116 files; 78 records; tags [16777232]; total 30408704 B; pad zero on 116/116
PASS  full-chain identity: levels 0..full-1 cost payload + table total
      116/116 files; 104034368 B of texel chain over 73625664 B stored + 30408704 B omitted
PASS  round trip: header rebuilt from decoded fields + payload == the file, byte for byte
      116/116 files
PASS  negation: +-4 texels or +-1 mip breaks the identity on every file
      0 files with a blind spot; 116 files where +-1 texel is absorbed by block rounding
PASS  the earlier pass agrees per file (block size, mip counts, FULL grade)
      0 mismatches vs DECODE_DEPTH6.json
PASS  G3-12's 121 PARTIAL split by extension as re-counted here
      121 PARTIAL: .ddsc 116, .pfxc 0, .rbm 3, .physicsc 1, .epe 1; plus 4 NAMED-ONLY: .pfxc 4
PASS  every non-.ddsc PARTIAL / NAMED-ONLY file is listed with its block type
      .pfxc 4, .rbm 3, .physicsc 1, .epe 1

12/12 oracles pass
CHECK OK: the stored .md/.json are byte-identical to a fresh recompute
check_exit=0
```

Artifact sizes on disk match the report: `DECODE_DEPTH5.md` 10,061 B, `DECODE_DEPTH5.json` 240,708 B,
`decode_depth5.py` 35,159 B.

## 2. Format-id counts, re-read from the archive (not the artifact)

Re-enumerated the bundle myself (`decode_depth5.bundle()` + `.inner()`, 116 `.ddsc` entries) and read
the four header fields straight out of each blob:

```
ddsc files on disk (archive re-enumeration): 116
format counts from bytes: {71: 46, 77: 66, 83: 1, 87: 3} sum: 116
12c quoting 77 x66, 71 x46, 87 x3, 83 x1: True
```

**decoded** — the report's four counts and their sum are exact. `k` distribution also re-derived:
`{0: 71, 1: 21, 2: 16, 3: 7, 4: 1}` = 116, matching `DECODE_DEPTH6.md` and 12c's table.

## 3. Format 87, all three files, by hand

Every number below is read at its offset in the file (0x08 format, 0x0C/0x0E w/h, 0x14/0x15 mip
counts, 0x20 header size, 0x24 payload) and then closed arithmetically:

| file | w x h | mips full/stored | header | payload | w·h·4 | file length | header+chain | closes |
|---|---|---|---:|---:|---:|---:|---:|---|
| `effects/textures/erosion/erosion_smallcurve_soft.ddsc` | 256 x 16 | 1 / 1 | 128 | 16,384 | 16,384 | 16,512 | 16,512 | **yes** |
| `effects/textures/t_flare_headlight_ramp.ddsc` | 256 x 256 | 1 / 1 | 128 | 262,144 | 262,144 | 262,272 | 262,272 | **yes** |
| `effects/textures/t_spherical_ramp.ddsc` | 256 x 256 | 1 / 1 | 128 | 262,144 | 262,144 | 262,272 | 262,272 | **yes** |

Per-mip bytes with 64 B per 4x4 block: `[16384]`, `[262144]`, `[262144]`; full chain = stored chain
in all three (omitted = 0), so `payload + omitted == full` trivially. **decoded**: 12c's
"256x256x4 = 262,144 = payload; 256x16x4 = 16,384" is exact, and 4 B/texel is the only candidate
that closes — `ceil(256/4)²·blk = 4096·blk` equals 262,144 only at `blk = 64` (8 → 32,768; 16 →
65,536; 32 → 131,072).

One property the card does not state and should: **all three format-87 files are single-mip**
(`mip_full = mip_stored = 1`). The 64 B/block value therefore rests on one level per file, not on a
chain — sound, but it is a weaker fit than the 16-mip files give format 77.

## 4. The negation test (O9), re-run independently

I perturbed each file myself instead of trusting the oracle's boolean:

```
O9 survivors (full identity, as defined in the card): 0
stored-chain-only +-4 blind spots: 45
their k values: [1, 2, 3, 4]
```

**Holds** for the identity the card defines (`closes()` = stored chain *and* table records *and*
full-chain sum): no file survives ±4 texels or ±1 mip, so the field is pinned.

But the 45 files are exactly the `k > 0` set, and the *stored chain alone* absorbs a ±4 texel shift
in every one of them — the table is what catches it. So the sentence "a wrong width, height or mip
count has no candidate that closes" is true only because the table half is part of the check; the
report should say that O9's strength on 45 of 116 files comes entirely from the omitted-mip records.
This is a precision issue, not a wrong number: the printed `0 blind spots` reproduces.

## 5. The "two earlier passes" statement — partly right, one claim false

| 12c says | the earlier card says | verdict |
|---|---|---|
| `decode_depth2.py` (G3-12b) "fitted the AVTX header and left 45 files on an unread 84-byte tail" | `DECODE_DEPTH2.md`: `.ddsc` **71 FULL / 45 PARTIAL**; tail `0x2C..0x80` = 84 B, "zero on the FULL files, non-zero on the PARTIAL ones (UNKNOWN)" | **true** |
| `decode_depth6.py` (G3-12d) "decoded that tail as the omitted-mip table and closed 116/116 `.ddsc` plus 4/4 `.pfxc`" | `DECODE_DEPTH6.md`: `.ddsc` **116 FULL / 0**; `.pfxc` **4 FULL / 0**; §1.1 tail = `k` records of `(offset, size, tag 0x01000010)` | **true** |
| G3-12's own census still carries the older 116 PARTIAL grades | `DECODE_DEPTH2.md` opens with "G3-12's census had `.ddsc` 0 FULL / 116 PARTIAL" | **true** |
| "the one place this pass adds a *new* fact is the format map (**format 87 is 64 bytes per 4x4 block, 4 B/texel, which neither earlier pass reported**)" | `DECODE_DEPTH2.md:54` — `\| 87 \| 3 \| 541056 \| **[64]** \| …`; `:104` — "`87 -> [64] B`". `DECODE_DEPTH6.md:81` — `\| 87 \| 3 \| 541056 \| **[64]** \| …`; `:194` — "`87 -> [64] B`" | **FALSE** |

Both earlier cards print the 64 B/block value for format 87 in their per-format tables **and** in
their fleet-map check lines. What is genuinely new in 12c is the *interpretation* (4 B/texel, an
uncompressed 4-channel shape, `w·h·4 == payload`) and the worked hand reconciliation of the three
files — not the block size. `--check`'s own cross-check line ("0 mismatches vs
`DECODE_DEPTH6.json`", which compares `block_bytes`) is the machine proof that G3-12d already had
the value.

Also accurate, checked because it is cited as precedent: `Tools/scripts/tex2ddsc.py` does carry
`FMT = {"colour": 71, "mask": 71, "normal": 83, "glass": 77}` with `71 BC1`, `83 BC5`,
`77 BC3/DXT5` (lines 34-36; the docstring at 9-13 names 71/83). 12c cites "lines 5-7, 20-22" — the
content is there but the line numbers are off; harmless, the map is right.

## 6. What I could not check

- **Texel contents / codec identity for format 87.** No decoder in the project turns a block into
  pixels and no reference export exists here; 12c labels this UNKNOWN and that is correct. Testing
  it needs `ConvertTexture.exe` on one of the three files.
- **The 74,172,750-byte PARTIAL total and the 99.3 % share.** I re-derived the file *counts*
  (116/3/1/1 + 4 NAMED-ONLY) but not the byte totals against `DECODE_DEPTH.json`.
- **`decode_depth2.py` / `decode_depth6.py` scripts' internals.** I verified what their *cards*
  state and that neither script contains a `perturb`/`negation`/`blind` path, so "a negation test the
  earlier passes did not have" is supported at the grep level, but I did not re-run those two
  scripts.
- **Whether the `0x06` / `0x12` / `0x28` header meanings are recoverable.** 12c leaves them UNKNOWN
  with the values decoded; nothing in the project maps them, and I found no additional evidence.

## Commands run

```
$ ls -l Tools/scripts/decode_depth5.py Research/JC3Grab/DECODE_DEPTH5.md Research/JC3Grab/DECODE_DEPTH5.json
-rw-r--r-- 240708 Nov  3 08:47 Research/JC3Grab/DECODE_DEPTH5.json
-rw-r--r--  10061 Nov  3 08:47 Research/JC3Grab/DECODE_DEPTH5.md
-rw-r--r--  35159 Nov  3 08:47 Tools/scripts/decode_depth5.py

$ uv run python Tools/scripts/decode_depth5.py --check   # 12/12 oracles, CHECK OK, exit 0

$ uv run python - <<'PY'   # byte-level re-read of the archive
format counts from bytes: {71: 46, 77: 66, 83: 1, 87: 3} sum: 116
... format 87 w/h/mips/payload/len table as in §3 ...
O9 survivors (full identity): 0 ; stored-chain-only +-4 blind spots: 45 (k = 1..4)
PY

$ grep -n "perturb\|negation\|blind" Tools/scripts/decode_depth2.py Tools/scripts/decode_depth6.py
(no matches)

$ grep -n "87" Research/JC3Grab/DECODE_DEPTH2.md Research/JC3Grab/DECODE_DEPTH6.md
DECODE_DEPTH2.md:54:| 87 | 3 | 541056 | [64] | 3 | 3 | 0 |
DECODE_DEPTH2.md:104:... 87 -> [64] B; 83 -> [16] B
DECODE_DEPTH6.md:81:| 87 | 3 | 541056 | [64] | 3 | 0 | 0 | 3 |
DECODE_DEPTH6.md:194:... 83 -> [16] B; 87 -> [64] B
```

Read-only throughout: `DECODE_DEPTH5.*`, `DECODE_DEPTH2.md`, `DECODE_DEPTH6.md`, the donor bundle and
the two earlier scripts. No file was edited; no new script was needed, since the review re-uses
`decode_depth5.py`'s own entry points against the bytes.

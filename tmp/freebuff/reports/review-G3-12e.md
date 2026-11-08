# review-G3-12e — the Serpente `.epe` round trip, re-measured

VERDICT: **holds.** I re-extracted the member fresh, ran the tool's `--e`/`--i` myself, and
recomputed the float differences with numpy on the raw bytes. The two headline numbers are exact:
**2,189 bytes** are padding-only canonicalisation (`0x50` → `0x00`, every one of them outside any
referenced span) and **75 float words** change, with a maximum distance of **7 ULP** (proper
sign-magnitude ULP, not just an int32 subtraction). The 2,293 differing bytes close exactly as
2,189 + 104 with **0 unexplained**. The 75 words are **not one field**: 63 belong to the matrix
property `0x6ca6d4b9` (`world`) across eight of its sixteen components and 12 to the unnamed matrix
`0xa04c3b1e` across six, in 35 payloads. On the reader question, the bytes settle size and hash
unambiguously and leave only value comparison to the engine (UNKNOWN, as the card already says).

## 1. What I ran and what it produced

### 1.1 The card's own check

```
$ uv run python Tools/scripts/decode_depth7.py --check
PASS O1 the archive member is the file G3-12 graded PARTIAL
      109526 B, sha256 f67bc17ebb16b70f...
PASS O2 export and import both succeed and keep the length
      109526 -> 109526 -> 109526 B; xml 444927 B
PASS O3 the byte map labels every byte exactly once
      107337 role bytes + 2189 pad bytes = 109526
PASS O4 the padding map is the same in both files
      750 runs, len [(1, 240), (2, 212), (3, 185), (4, 26), (8, 43), (10, 3), (12, 41)], every run ends on a 4- or 16-byte boundary
PASS O5 pad bytes: vanilla 0x50, tool 0x00
      vanilla values ['0x50'] over 2189 B; tool values ['0x0'] over 2189 B
PASS O6 layout is unchanged, so nothing was re-ordered
      450 node records and 6521 property records byte-identical; payload offsets identical: True
PASS O7 every differing byte is padding or a mat float
      2293 = 2189 pad + 104 mat-float + 0 unexplained
PASS O8 the changed words are the 7-digit decimal round trip, and only 7
      6 digits -> 149 words; 7 digits -> 75 words MATCH; 8 digits -> 1 words; 9 digits -> 0 words; 10 digits -> 0 words
PASS O9 the tool is a fixed point after one pass
      b == b2 == b3; xml1 == xml2: True
PASS O10 the Batmobile .epe built through the tool round-trips identically
      105430 B, sha256 1778816d26ce5505..., 2131 pad bytes all ['0x0']
PASS O11 the export's name for the changed mat property re-hashes to it
      hash_jenkins("world") = 0x6ca6d4b9, binary property hash 0x6ca6d4b9, 138 distinct names in the export

11/11 oracles pass
PASS the stored .json is identical to a fresh recompute
PASS the stored .md is identical to a fresh recompute
RESULT: PASS
CHECK_EXIT=0
```

### 1.2 Fresh round trip and numpy diff (my own, not the card's probes)

Extraction uses the same archive loader (`bm_rc`/`eetoc`) but a fresh call; the export/import goes
to a new scratch directory. The structure parser is imported from the card's module (to attribute
offsets to nodes/properties); **all diff and float arithmetic below is numpy on the bytes**.

```
$ PYTHONIOENCODING=utf-8 uv run --with numpy python tmp/freebuff/scratch/g3_12e_review/probe2.py
A 109526 B 109526 shaA f67bc17ebb16b70f
shaB f5a11052b5fc8f3a xml 444927
diff 2293 = 2189 pad + 104 other; pad all role 'pad': True; other roles {'fixed8': 104}

changed words 75 in 35 distinct payloads
proper ULP distance: max 7, histogram {1: 35, 2: 30, 3: 5, 4: 4, 7: 1}
naive int32 distance max 7
negative values among changed words: 27
differing bytes accounted: 104 (should be 104)
max |rel| 4.307e-07  max |abs| 3.815e-06
value range on changed words: -1.621 .. 23.41

by hash {'0x6ca6d4b9': 63, '0xa04c3b1e': 12}
  0x6ca6d4b9 fields {0: 3, 1: 2, 4: 2, 5: 3, 10: 2, 12: 10, 13: 25, 14: 16}
  0xa04c3b1e fields {2: 2, 4: 2, 5: 2, 8: 2, 9: 2, 10: 2}

first 6:
   node 18 0x6ca6d4b9 f13 3fde8000->3fde7ffe  1.73828125 -> 1.73828101  ulp 2 bytes 2
   node 27 0x6ca6d4b9 f 0 406c2fff->406c2ffd  3.69042945 -> 3.69042897  ulp 2 bytes 1
   node 27 0x6ca6d4b9 f 5 3fe35c00->3fe35bff  1.77624512 -> 1.776245  ulp 1 bytes 2
   node 27 0x6ca6d4b9 f12 bfcf7000->bfcf6ffc  -1.62060547 -> -1.62060499  ulp 4 bytes 2
   node 27 0x6ca6d4b9 f13 be248000->be247ffe  -0.160644531 -> -0.160644501  ulp 2 bytes 2
   node 31 0x6ca6d4b9 f 0 4198f575->4198f574  19.1198521 -> 19.1198502  ulp 1 bytes 1

0x6ca6d4b9 sample values: [1.738281, 3.690429, 1.776245, -1.620605, -0.160645, 19.119852, 14.109852, 23.409853]
EXIT=0
```

The proper ULP metric matters here because **27 of the 75 changed words are negative**; for
sign-magnitude floats an `int32` view is not monotonic. It happens that both metrics give the same
answer for this file (max 7, same histogram), so the card's int32 statement is not wrong — but the
check now rests on the correct distance.

### 1.3 Idempotence and payload shape (from bytes)

```
$ ... --e rt2.epe rt3.xml && --i rt3.xml rt3.epe && sha256sum ...
f5a11052b5fc8f3a6492926e5fa2f3c3552f7392937e7e67d4e7c6806370e413 *rt2.epe
f5a11052b5fc8f3a6492926e5fa2f3c3552f7392937e7e67d4e7c6806370e413 *rt3.epe
f5a11052b5fc8f3a6492926e5fa2f3c3552f7392937e7e67d4e7c6806370e413 *tmp/freebuff/scratch/g3_12e/b_noproj.epe
SECOND PASS IDENTICAL
header b'RTPC\x01\x00\x00\x00' mat props 148 role fixed8 bytes 9472 == 64*props: True
mat payload offsets on 4B grid: True any payload overlaps a pad byte: False
file len 109526 no length field in header: True
```

### 1.4 The digit sweep, recomputed over all 3,136 float words

```
float words 3136 actual changed 75
digits 5 predicted 150 same multiset as actual: False
digits 6 predicted 149 same multiset as actual: False
digits 7 predicted 75 same multiset as actual: True
digits 8 predicted 1 same multiset as actual: False
digits 9 predicted 0 same multiset as actual: False
digits 10 predicted 0 same multiset as actual: False
```

Only `%.7g` reproduces the changed set, and it reproduces it as an exact multiset (not merely the
same count). That is the strongest form of the card's mechanism claim and it survives.

## 2. Are the 75 changed floats "the same field"?

**No.** They are the *same kind of record* (a `Matrix4x4`, type 8) but not one field or one property:

| property hash | name | words | components (0–15) |
|---|---|---:|---|
| `0x6ca6d4b9` | `world` (Jenkins of the name, card O11) | 63 | 0, 1, 4, 5, 10, 12, 13, 14 |
| `0xa04c3b1e` | no name in the fork's list | 12 | 2, 4, 5, 8, 9, 10 |

They sit in 35 distinct 64-byte payloads. Within `world` the hits are concentrated in the
translation row (components 12–14: 51 of 63) but also in the upper 3×3 (0, 1, 4, 5, 10); the
unnamed matrix is spread over six components. So the correct statement is "the whole matrix text is
re-emitted at 7 significant digits and every component whose value that rounds differently moves",
not "one field changes everywhere". The card's wording ("float32 inside a Matrix4x4 payload") is
accurate; anyone reading it as a single field should be corrected by this table.

## 3. Could 7 ULP change a hash, a comparison or the file size for the reader?

Answered from the bytes, not from engine knowledge:

- **File size: no.** Both files are 109,526 B. The changed values live in type-8 payloads whose size
  is fixed by the type — the byte map assigns exactly `9472 = 148 × 64` bytes to type 8, and the
  header is only `RTPC` + version (8 B, identical). No length prefix sits in front of a matrix, and
  no counted array (`type 9/10/11/14`) byte differs. A 1–7 ULP change cannot move a byte count.
- **Stored hash: no.** Every differing byte is either pad (`2,189`, all role `pad`, unreferenced) or
  inside a matrix payload (`104`, all role `fixed8`). The 8-byte header, all 450 node records, all
  6,521 property records and every string/array span are byte-identical. Property hashes in the
  file are Jenkins hashes of *names*; the name strings are in unchanged string spans, so the hash
  table cannot move. There is no digest field over the payloads anywhere in the file.
- **Comparison: only if the reader compares values, and nothing in the file records a comparison.**
  The text round trip is a pure function of the value, so any two values that were bit-equal before
  remain bit-equal after (identical input → identical decimal text → identical result); equality of
  duplicated matrices is preserved. Only a comparison between *distinct* values that were within
  7 ULP of each other could flip, and the file stores no comparison result, ordering key or
  dedup flag that would make that visible in the bytes.
- **What is still UNKNOWN:** anything the engine computes at load time (a runtime hash for caching,
  a tolerance/equality test against another asset). No byte in this file encodes such a result, so
  it cannot be settled statically; the card's UNKNOWN 1 says the same.

## 4. Claims re-read, one line each

| claim | result |
|---|---|
| vanilla member 109,526 B, sha256 `f67bc17e…` | **confirmed** (fresh extraction, same hash) |
| tool output 109,526 B, sha256 `f5a11052…` | **confirmed** (same hash; my second pass equals the card's `b_noproj.epe`) |
| 2,293 differing bytes, first at `0x765` | **confirmed** |
| 2,189 bytes are padding, vanilla `0x50` → tool `0x00` | **confirmed**; all 2,189 labelled `pad`, none inside a payload |
| 104 bytes / 75 words / 35 payloads are matrix floats | **confirmed** (35 distinct payloads, 104 bytes accounted) |
| at most 7 ULP | **confirmed** with proper sign-magnitude ULP; histogram `{1:35, 2:30, 3:5, 4:4, 7:1}` |
| the 7-digit decimal round trip, and only 7 | **confirmed**; 7 is the only digit count whose predicted set equals the actual multiset |
| fixed point after one pass | **confirmed** independently (`rt2 == rt3`, equal to the card's `b`) |
| "no structure refers to the padding" | **confirmed**: every pad byte is role `pad`, and no property payload offset falls in one |
| Batmobile `.epe` (105,430 B) round-trips identically | not re-run here; the card's sha is in the scratch dir and O10 passes |

## 5. What I could not check

- **Engine acceptance** of the 75 re-rounded values — no run, no attach, by rule. The static bound is
  `max |rel| 4.31e-07`, `max |abs| 3.82e-06` (largest value on a changed word: 23.409853).
- **The per-value XML line mapping** in `DECODE_DEPTH7.md` §4a. I verified the binary side (node,
  payload, component, word) but did not re-match each of the 75 rows to a line of the 444,927-byte
  export.
- **The bm-009 `.epe` round trip** (card O10). It was not re-run in this review; its scratch copy and
  hash are present, and the card's own `--check` re-runs it.
- **Runtime hashing/comparison** by the engine, as in §3.

## 6. Files

Scratch only: `tmp/freebuff/scratch/g3_12e_review/probe.py` (first attempt, wrong float view,
superseded), `probe2.py` (the numbers above), plus `vanilla.epe`, `rt.xml`, `rt2.epe`, `rt3.xml`,
`rt3.epe`. No project file was edited; the archive and the Gibbed tool were only read.

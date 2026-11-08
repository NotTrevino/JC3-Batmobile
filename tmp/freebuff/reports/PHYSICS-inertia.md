# PHYSICS-inertia — is the mass-properties payload an inertia tensor?

STATUS: done

The brief's oracle was run on all 56 decoded mass values and the body-entry array, and it
**fails**: the best of seven byte layouts and of all ten int16 diagonal placements passes on
**27 of 54** bodies at the stated 25 % per-moment tolerance (median normalised error 0.252,
40/54 at 50 %, 50/54 at 100 %). Per the brief, the tensor semantics is therefore **UNKNOWN**.

Two findings that stand on their own:

1. **The bytes after the mass cannot be the tensor.** `hknpShapeMassProperties` is 48 bytes:
   16 zero bytes, a 24-byte payload at `+0x10..+0x27`, the mass `f32` at `+0x28`, and one
   `f32` at `+0x2C..+0x2F`. Four bytes is too few for a symmetric tensor (24 bytes for six
   values, 36 for nine), and the tail is a single scalar that is exactly zero in 38 of 56
   blocks. *(decoded)*
2. **The tensor-sized payload is the 24 bytes before the mass, and it still misses the
   oracle.** It is three int16x4 groups. A mirror test that assumes no layout — it finds
   mirrored parts from hull geometry alone and asks which int16 lanes change sign — decodes
   exactly three x-odd lanes, `0`, `9`, `10`: one vector component and two scalars. That is the
   shape of a compressed mass-properties record (centre of mass / diagonal / two products), and
   the placement search agrees: lanes 4,5,6 (`+0x18,+0x1a,+0x1c`) is the best diagonal of all
   ten windows on every metric (pd 56/56, triangle 56/56, box 27/54). It is not good enough to
   call it decoded. *(decoded bytes and mirror mask; derived grouping; UNKNOWN semantics)*

## Files written

- `Tools/scripts/jc3_inertia.py` — new script, `--write` / `--check`, donor read once with
  `jc3hkx.py` (read-only). `--check` re-derives everything from the source bytes, compares the
  stored JSON, re-renders the note and re-runs the five structural oracles plus a verdict/
  oracle consistency guard.
- `Research/JC3Grab/INERTIA.md` — generated note (176 lines).
- `Research/JC3Grab/INERTIA.json` — generated data (all 56 blocks, all 54 per-body rows, the
  10-window scan, the mirror pair, the oracles).
- `tmp/freebuff/reports/PHYSICS-inertia.md` — this report.

No file belonging to another task was edited; `jc3hkx.py`, `jc3_physics_roles2.py`, the donor
and the game install were read only.

## Values, labelled

| value | label |
|---|---|
| block 48 bytes, `+0x00..+0x0f` zero | decoded (56/56) |
| payload 24 bytes at `+0x10..+0x27` | decoded (bytes) |
| mass `f32` at `+0x28` (800.0, 275.0, 40.0, 25.0, 5.0, 1.0, 0.018 … 0.002) | decoded |
| tail `f32` at `+0x2C`: 0 in 38 blocks, 0.001947..0.16509 in 18 | decoded |
| 54 polytope→mass links, 54 blocks with a hull, 40 with a body id | decoded |
| mirror pair blocks `0x5db0` (body 1) / `0x67f0` (body 4), mass 40.0; negated lanes 0, 9, 10 | decoded |
| 3 x int16x4 grouping (groups at `+0x10`, `+0x18`, `+0x20`) | derived from the mirror mask |
| diagonal at lanes 4,5,6 = `+0x18,+0x1a,+0x1c` | derived (best of 10 windows) |
| positive-definite 56/56, triangle inequality 56/56 | derived (scale-free) |
| box agreement ≤25 %: 27/54; ≤50 %: 40/54; ≤100 %: 50/54; median 0.252174 | derived |
| oracle pass 27/54 → tensor semantics | **UNKNOWN** |
| scale of the quantised lanes; group 3 = products or axis; meaning of the `+0x2C` f32; handedness | **UNKNOWN** |

## Commands run (verbatim)

1. Checking the helper names I relied on exist in the reader:

```
$ cd "E:/Modding/JC3-Batmobile" && grep -n "BODY_ENTRY_SIZE\|^BODY\|def array\|def decode_polytope\|self.extents\|self._starts" Tools/scripts/jc3hkx.py | head -30
94:BODY_ENTRY_SIZE = 96         # hknpPhysicsSystemData 4th array; hardpoint at +0x30
159:        self._starts = {o.offset: o.cls for o in self.objects}
160:        self._order = sorted(self._starts)
161:        self.extents = {}
164:            self.extents[off] = nxt - off
237:    def array(self, slot: int) -> dict:
282:        (0x40, "body_entries", "array", BODY_ENTRY_SIZE),
364:def decode_polytope(pf: Packfile, off: int) -> dict:
624:            at = arr["ptr"] + i * BODY_ENTRY_SIZE + 0x30
```

2. First `--write` (crash: median over an empty list)

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy python Tools/scripts/jc3_inertia.py --write
Traceback (most recent call last):
  File "E:\Modding\JC3-Batmobile\Tools\scripts\jc3_inertia.py", line 689, in <module>
    raise SystemExit(main())
  File "E:\Modding\JC3-Batmobile\Tools\scripts\jc3_inertia.py", line 635, in main
    doc = build()
  File "E:\Modding\JC3-Batmobile\Tools\scripts\jc3_inertia.py", line 340, in build
    results = [run_layout(n, f, blocks) for n, _d, f in LAYOUTS]
  File "E:\Modding\JC3-Batmobile\Tools\scripts\jc3_inertia.py", line 329, in run_layout
    "box_error_median": (round(sorted(r["box_error"] for r in tested
  IndexError: list index out of range
```

   fixed; two more crashes followed in the same session (`KeyError: 'oracles'` because the new
   `build()` return dict dropped the key, and `KeyError: 'box_moments'` because the row is on
   `rec`, not `test`). Both fixed before any output was accepted.

3. Debug dump of the block structure (extents, zero fields, tail values, masses, mirror pairs):

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy python - <<'PY'
import sys, json, struct, collections
sys.path.insert(0, "Tools/scripts")
import jc3_inertia as J
c = J.collect()
b = c["blocks"]
print("extents:", collections.Counter(x["extent"] for x in b))
print("header_zero:", sum(x["header_zero"] for x in b), "tail_zero:", sum(x["tail_zero"] for x in b))
print("tails:", collections.Counter(x["tail"] for x in b))
print("masses:", [round(x["mass"],3) for x in b])
print("linked hulls:", sum(1 for x in b if x["hull_extents"]))
mir = J.mirror_pairs(c)
print("pairs:", len(mir["pairs"]))
for p in mir["pairs"]:
    print("  ", hex(p["a"]), hex(p["b"]), p["mass"], "flip", p["flip_lanes"], "other", p["other_lanes"])
for x in b[:6]:
    print(hex(x["at"]), x["payload"], x["ei"], x["hull_extents"], x["mass"])
PY
extents: Counter({48: 56})
header_zero: 56 tail_zero: 38
tails: Counter({'00000000': 38, 'a975333b': 1, '2026ff3a': 1, 'e862bf3b': 1, '7ed0173c': 1, '3e27ff3a': 1, '4666bf3b': 1, '45db173c': 1, '700d293e': 1, '6e0d293e': 1, 'bb68a93b': 1, '4c0d3f3c': 1, '2a52923b': 1, '4e66a93b': 1, '6c0c3f3c': 1, '832f913c': 1, '0623923b': 1, '740d293e': 1, '720d293e': 1})
masses: [800.0, 40.0, 5.0, 1.0, 40.0, 5.0, 1.0, 275.0, 30.0, 1.0, 1.0, 1.0, 30.0, 1.0, 1.0, 1.0, 25.0, 0.003, 0.002, 0.006, 0.009, 0.002, 0.006, 0.009, 1.0, 25.0, 40.0, 40.0, ... , 5.0, 5.0, 5.0]
linked hulls: 40
pairs: 8
   0x8140 0x8ed0 1.0 flip [0] other [5, 6, 8, 9, 10, 11]
   0xb8c0 0xbc00 25.0 flip [] other [0, 1, 2]
   ...
0x5970 8fff9759d8560030d93c8546cd188035d77d0580e87f2af5 [-113, 22935, 22232, 12288, 15577, 18053, 6349, 13696, 32215, -32763, 32744, -2774] [2.085002, 1.212002, 3.678848] 800.0
0x5db0 558dac5bf9f80030994b6a3a2c150032617a2e81b37480f4 [-29355, 23468, -1799, 12288, 19353, 14954, 5420, 12800, 31329, -32466, 29875, -2944] [0.387052, 1.04506, 1.414985] 40.0
0x5fc0 bcd08c4d80068030154c8446e00500305676d281ab6acff2 [-12100, 19852, 1664, 12416, 19477, 18052, 1504, 12288, 30294, -32302, 27307, -3377] [0.153537, 0.349132, 1.267498] 5.0
0x63b0 b9c4d9458be38030b02d6f739a7f802c7c65019ed26637eb [-15175, 17881, -7285, 12416, 11696, 29551, 32666, 11392, 25980, -25087, 26322, -5321] [0.20745, 0.153172, 0.133814] 1.0
0x67f0 ab72ac5bf9f80030994b6a3a2c150032617ad17e4c8b80f4 [29355, 23468, -1799, 12288, 19353, 14954, 5420, 12800, 31329, 32465, -29876, -2944] [0.38777, 1.047652, 1.415004] 40.0
0x6a00 442f8c4d80068030154c8546df0500305576277e4995d1f2 [12100, 19852, 1664, 12416, 19477, 18053, 1503, 12288, 30293, 32295, -27319, -3375] [0.14684, 0.349132, 1.267499] 5.0
```

   (the mass list is truncated in this report for width; it is complete in `INERTIA.json`)

4. Diagonal placement search over all ten int16 windows, before fixing the render:

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy python - <<'PY'
... window scan, 10 windows, signed and abs ...
PY
win sgn pd tri e25 e50 median_err
  0 signed   0   0   0   0 0
  0 abs     17   6   0   4 0.8447
  1 signed   1   1   0   0 0.6472
  1 abs     40  15   3  15 0.5738
  2 signed   1   1   0   0 0.6993
  2 abs     40  26   6  21 0.4826
  3 signed  40  27  11  20 0.532
  4 signed  40  40  17  28 0.3043
  5 signed  40  22  10  22 0.4226
  6 signed   6   1   0   2 0.5694
  7 signed   0   0   0   0 0
  8 signed   0   0   0   0 0
  9 signed   0   0   0   0 0
```

5. Mirror-pair debug after the geometry fix (this is the pair the note uses):

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy python - <<'PY'
... J.mirror_pairs(c) ...
PY
pairs: 1 masks: {'0': 1} rejected: 3
   0x5db0 [1] 0x67f0 [4] m 40.0 flip [0] other [9, 10]
0x5db0 [1] [-1.0309, 0.3452, -0.7614] [-0.6439, 1.3903, 0.6536]
0x67f0 [4] [0.6432, 0.3452, -0.7614] [1.0309, 1.3929, 0.6536]
```

   lanes 9 and 10 differ by one unit, i.e. they *are* negated but not exactly — the test now
   allows one quantisation unit, and the mask becomes `0|9|10`.

6. Final write and check:

```
$ cd "E:/Modding/JC3-Batmobile" && uv run --with numpy python Tools/scripts/jc3_inertia.py --write; echo "write_exit=$?"; uv run --with numpy python Tools/scripts/jc3_inertia.py --check; echo "check_exit=$?"
wrote INERTIA.md / INERTIA.json
blocks: 56  polytope links: 54  with hull: 54  with body id: 40
mirror pairs: 1 masks: {'0|9|10': 1}
  i16_grouped_diag   pass 27/54  pd 56 tri 56 box25 27 box50 40 sym n/a
  after_mass_4B      pass  0/54  pd  0 tri  0 box25  0 box50  0 sym n/a
  f32x6_at_10        pass  0/54  pd  0 tri  0 box25  0 box50  0 sym 53/53
  f16x6_at_10        pass  0/54  pd  0 tri  0 box25  0 box50  0 sym 45/45
  i16x6_at_10        pass  0/54  pd  0 tri  0 box25  0 box50  0 sym 56/56
  i16x9_at_10        pass  0/54  pd  0 tri  0 box25  0 box50  0 sym 56/56
  i16_grouped        pass  0/54  pd  0 tri  0 box25  0 box50  0 sym 56/56
verdict: UNKNOWN - the payload fails the four-part oracle: best layout i16_grouped_diag passes 27 of 54 bodies at 25% per-moment tolerance (median normalised error 0.252174, 40 pass at 50%)
oracles: {'block_is_48_bytes_with_16_zero_leading': True, 'bytes_after_the_mass_are_one_scalar': True, 'mass_link_to_hulls': True, 'mirror_mask_is_three_x_odd_lanes': True, 'best_int16_window_is_the_grouped_diagonal': True, 'box_agreement_at_25pct_is_met': False}
write_exit=0
OK: best i16_grouped_diag 27/54 ; verdict UNKNOWN ; structural oracles true
check_exit=0
```

## Result detail

Per-body pass/fail is in `INERTIA.md` §4 (one row per block) and `INERTIA.json`
(`layouts[].rows[]`, with `box_error_by_moment`). Totals for the best layout
`i16_grouped_diag`: pd 56/56, triangle 56/56, box ≤25 % 27/54, box ≤50 % 40/54, oracle pass
27/54.

First failing byte layout, in the order the brief asks:

1. `+0x2C..+0x2F` — "the bytes after the mass". Four bytes, single `f32`, zero in 38/56. Fails
   on size in 56/56 blocks. This is the literal reading and it is the first to fail.
2. `+0x10..+0x27` as `f32` x6: 0/56 positive-definite (the lanes are not IEEE floats).
3. `+0x10..+0x1B` as IEEE half x6: 0/56.
4. `+0x10..+0x21` as int16 x9, and int16 x6 at `+0x10`: 0/56 (the products placed at `+0x22`,
   `+0x24`, `+0x20` are saturated, so the matrix is indefinite).
5. Best int16 diagonal `+0x18,+0x1A,+0x1C`: first failing body `0x5db0` (body 1, the left door,
   mass 40.0, hull 0.387 x 1.045 x 1.415 m) — its third moment sits at `+0x1C` and is 30.2 %
   off the box value; the payload is `558dac5bf9f80030994b6a3a2c150032617a2e81b37480f4`.

## UNKNOWNs

1. **The scale from quantised lanes to SI moments.** No project decoder reads it, so only the
   shape of the moments is testable (all four oracle parts were chosen to be scale-free). What I
   tried: the fourth lane of each group (`+0x16` = 12288..13312, `+0x1E` = 11392..13696) stays
   in a narrow band in all 56 blocks and looks like an exponent/scale marker, but no file in
   this tree documents the field. Where it would be found: a documented
   `hknpShapeMassProperties` layout (the tree has none) or a runtime read of one block.
2. **Whether group 3 (`+0x20..+0x27`) is three products or a principal axis.** Its triple norm
   is 1.3638..1.7321 in Q15: neither 1.0 (an axis) nor ~0 (products near a principal frame).
   Two of its lanes are x-odd, which both readings allow, so the mirror mask does not separate
   them.
3. **The `f32` at `+0x2C`.** Zero in 38/56, 0.001947..0.16509 in the rest, no monotone relation
   to mass checked here. Volume, density and an unused slot all remain possible.
4. **Handedness of the x-odd lanes** (row vs column, right- vs left-handed). The mirror mask
   fixes which lanes are x-odd, not the convention.
5. **Why box agreement fails.** The hull is not a box (a 1.4 m door with 0.39 m thickness, thin
   panels), so the reference tensor is itself a model. This is the most likely explanation and
   the next experiment: build the tensor from a tetrahedral decomposition of the polytope's
   vertices and re-run the same scale-free comparison — that separates an encoding error from a
   reference-model error.

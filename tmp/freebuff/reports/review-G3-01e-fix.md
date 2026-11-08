# review-G3-01e-fix - the `DriverLeft` guard-reference settlement, checked against the bytes

STATUS: done

## VERDICT

**The settlement's conclusion is right and its corrections are wrong.**

All four names are in `RVehicleBatmobile.DriverLeft` (`Startup.upk` export 7400). None is absent.
But the three offset corrections it draws - "BatmobileWinch is @286 not @277", "@253 is
FakeRoadCollisionStatic not ArmouredMode", "WinchPullType / IsVehicleAsleep not found" - are wrong,
and they are wrong for one reason: **the two reports are using different coordinate frames.**

* The fix reports **script-frame offsets of the one-byte prefix** that precedes a property token.
* The adjudication reports **payload-frame offsets of the int32 index field**.
* `payload = script + 22`, and the index field is at `token + 1`.

Its four cited numbers are exactly that: 277 = 255 + 22, 341 = 319 + 22, 286 = 264 + 22,
253 = 231 + 22. Every one is a real index field of a real reference. So the "corrections" compare
a script offset of one reference with a payload offset of another reference, 23 bytes apart.

Per name:

| name | present | reference tokens (script) | index field (script) | index field (payload) | import | class |
|---|---|---|---:|---|---:|---|
| `Core.ArmouredMode` | **yes, twice** | **254, 318** | 255, 319 | **277, 341** | 1366 | `BoolProperty` |
| `Core.BatmobileWinch` | **yes, twice** | **263, 278** | 264, 279 | **286, 301** | 5673 | `ObjectProperty` |
| `Core.WinchPullType` | **yes, twice** | **284, 290** | 285, 291 | 307, 313 | 1515 | `ByteProperty` |
| `Core.IsVehicleAsleep` | **yes, twice** | **223, 328** | 224, 329 | 246, 351 | 1498 | `BoolProperty` |

What that does to each disputed sentence:

1. **"BatmobileWinch is @286 not @277"** - both are real. `@263` is an instance reference whose
   index field is payload 286; `@277` is a `0x19 Context` whose object operand is
   `Core.BatmobileWinch` (token 278, index field payload 301). The fix found the second and missed
   the first; the adjudication found the first and missed the second. Neither offset refutes the
   other.
2. **"@253 is FakeRoadCollisionStatic not ArmouredMode"** - the fix's 253 is the `0x2D` byte
   immediately before the `Core.ArmouredMode` token at **script 254**; its index field is payload
   277. `Core.FakeRoadCollisionStatic` is a **separate** reference: token 230, index field 231 =
   payload **253**. So the adjudication's 253 is right *and* the fix's 253 label is right; they are
   two different references 22 bytes apart, read in two different frames.
3. **"WinchPullType / IsVehicleAsleep not found at the claimed offsets"** - both are present, twice
   each, one byte after the offsets the fix published (283/289 and 222/327 are the prefix bytes; the
   property tokens are 284/290 and 223/328). `Core.WinchPullType` is a `ByteProperty` (index 1515),
   `Core.IsVehicleAsleep` a `BoolProperty` (index 1498).
4. **"PRESENCE confirmed (review wrong)"** - right, and for the right reason: properties are
   referenced through the package object table (negative import indices), not through FName
   indices. The earlier `review-G3-01e` negative was a false negative.

The fix is also internally inconsistent: its docstring gives the **prefix** offsets for
`Core.ArmouredMode` (`@253/@317`) but the **token** offsets for the other three (`@223/@327
IsVehicleAsleep, @278 BatmobileWinch, @284/@290 WinchPullType`), while its rendered table and its
`guard_names` JSON use the prefix offsets for all four (222/327, 277, 283/289). Neither the prose
nor the table uses one frame throughout.

What the fix *does* get wrong, beyond the frame: its pattern scan sees 22 of the script's **28**
property references. It misses `Core.Driver` @54, `Core.InteriorLightsSwitchedOn` @61,
`Core.ReturnValue` @100 and @179, `Core.BatmobileWinch` @263 and
`Core.WheelspinSmokeMomentum` @351 - because the byte before each is `0x0F`, `0x8C`, `0x2C`,
`0x20`, `0x77` or `0x0F`, none of which is one of its four prefixes.

## How this was decoded

`Tools/scripts/review_g3_01e_bc.py` (new): a **sequential** walk of the 368 ScriptText bytes, from
0 to the terminal `0x04 Return` at 367. Nothing is pattern-scanned - a token is consumed only at the
position the walk has reached, so an operand byte cannot be mistaken for a reference.

* The reference form is `<0x01|0x00> <int32 object index>`, resolved through the package import
  table. `0x01` is always that form. `0x00` is that form only when the int32 behind it resolves;
  otherwise it is a one-byte prefix. The choice is forced, not guessed: forcing the one-byte reading
  at five of the seven `0x00` sites desyncs the walk (`local_form_forced_desyncs`).
* The one remaining ambiguity - `00 1D FC FF FF` at 100 and 179, which also parses as `0x00` +
  `0x1D IntConst` - is decided by a byte fact: the two flag blocks at 67-111 and 146-190 are
  identical **except for one byte** (0x2C at 99 vs 0x20 at 178). Identical bytes follow that
  difference in both blocks, so those bytes are one-byte tokens in the same slot and the tail is
  decoded identically - as a reference (`Core.ReturnValue`), not as a 16,777,212 constant. The
  alternative parse changes none of the four names and none of the offsets above, and is listed
  under UNKNOWN.
* The walk consumes all 368 bytes with **0 unexplained**, 135 tokens, 28 references, and lands on
  `Return`. Export anchors: payload 406 B, `size field @18 = 369 = script + 1`, trailer name index
  19530 = `DriverLeft`, script sha1 `70471c04b9526a2616e27c3c3830155112765efb` (recomputed at
  run time, printed in the generated JSON).

## Every property reference, in script-frame order

`form` is the byte that carries the reference; the int32 index follows at `token + 1`.

| # | token at | form | index | resolves to | class | index field (script / payload) |
|---:|---:|---|---:|---|---|---|
| 1 | 5 | `0x01` | -1382 | `Core.bWasRemoteDriving` | BoolProperty | 6 / 28 |
| 2 | 21 | `0x01` | -5746 | `Core.Driver` | ObjectProperty | 22 / 44 |
| 3 | 43 | `0x01` | -5746 | `Core.Driver` | ObjectProperty | 44 / 66 |
| 4 | 54 | `0x01` | -5746 | `Core.Driver` | ObjectProperty | 55 / 77 |
| 5 | 61 | `0x01` | -1581 | `Core.InteriorLightsSwitchedOn` | ByteProperty | 62 / 84 |
| 6 | 70 | `0x01` | -5702 | `Core.WorldInfo` | ObjectProperty | 71 / 93 |
| 7 | 76 | `0x00` | -5749 | `Core.GRI` | ObjectProperty | 77 / 99 |
| 8 | 82 | `0x01` | -5749 | `Core.GRI` | ObjectProperty | 83 / 105 |
| 9 | 88 | `0x00` | -5377 | `Core.FlagManager` | ObjectProperty | 89 / 111 |
| 10 | 94 | `0x01` | -5377 | `Core.FlagManager` | ObjectProperty | 95 / 117 |
| 11 | 100 | `0x00` | -995 | `Core.ReturnValue` | BoolProperty | 101 / 123 |
| 12 | 149 | `0x01` | -5702 | `Core.WorldInfo` | ObjectProperty | 150 / 172 |
| 13 | 155 | `0x00` | -5749 | `Core.GRI` | ObjectProperty | 156 / 178 |
| 14 | 161 | `0x01` | -5749 | `Core.GRI` | ObjectProperty | 162 / 184 |
| 15 | 167 | `0x00` | -5377 | `Core.FlagManager` | ObjectProperty | 168 / 190 |
| 16 | 173 | `0x01` | -5377 | `Core.FlagManager` | ObjectProperty | 174 / 196 |
| 17 | 179 | `0x00` | -995 | `Core.ReturnValue` | BoolProperty | 180 / 202 |
| 18 | 223 | `0x01` | -1498 | `Core.IsVehicleAsleep` | BoolProperty | 224 / **246** |
| 19 | 230 | `0x01` | -1361 | `Core.FakeRoadCollisionStatic` | BoolProperty | 231 / **253** |
| 20 | 254 | `0x01` | -1366 | `Core.ArmouredMode` | BoolProperty | 255 / **277** |
| 21 | 263 | `0x01` | -5673 | `Core.BatmobileWinch` | ObjectProperty | 264 / **286** |
| 22 | 278 | `0x01` | -5673 | `Core.BatmobileWinch` | ObjectProperty | 279 / **301** |
| 23 | 284 | `0x00` | -1515 | `Core.WinchPullType` | ByteProperty | 285 / **307** |
| 24 | 290 | `0x01` | -1515 | `Core.WinchPullType` | ByteProperty | 291 / **313** |
| 25 | 318 | `0x01` | -1366 | `Core.ArmouredMode` | BoolProperty | 319 / **341** |
| 26 | 328 | `0x01` | -1498 | `Core.IsVehicleAsleep` | BoolProperty | 329 / **351** |
| 27 | 344 | `0x01` | -1494 | `Core.bForceWheelspin` | BoolProperty | 345 / 367 |
| 28 | 351 | `0x01` | -3046 | `Core.WheelspinSmokeMomentum` | FloatProperty | 352 / 374 |

References 4, 5, 11, 17, 21 and 28 are the six the fix's scan cannot see. Reference 28 is the
`0x0F <ref> <0x1E float 0.0> ... 0x1C DriverLeft` assignment at the tail.

The two selector calls are where the fix says: `0x1B VirtualFunction
SetBatmanVsBatmobileCollisionMode` at **301** with `0x24 2`, and at **334** with `0x24 1`. The
value->mesh table is untouched by this review and was not re-derived.

## What this does to the two artifacts

* `Research/BatmobileGrab/COLLISION_SELECTOR2.md` section 2 should either shift the "at" column by
  one to the reference token, or rename it "prefix byte". Its `guard_windows` conclusion is
  unaffected: Winch refs (263, 278) sit before the value-2 call at 301 and the
  ArmouredMode/IsVehicleAsleep refs (318, 328) sit between 301 and 334 in either frame.
  The table should gain the six missing references; the completeness claim ("The script's 6-byte
  member refs") is currently a partial list.
* The MODLOG adjudication (the "MY ADJUDICATION" entry) should be corrected on its three offset
  corrections and its two UNCONFIRMED verdicts. Its presence conclusion stands.
* Nothing in `Builds/` and no game file was touched.

## Files written

- `Tools/scripts/review_g3_01e_bc.py` - new. `--write` / `--check`; the check re-reads
  `Startup.upk`, re-walks every token, re-resolves every index, re-runs all 11 oracles and compares
  the two generated files byte for byte.
- `Research/BatmobileGrab/DRIVERLEFT_7400.md` - generated: export facts, frames, the four names,
  all 28 references, the fix reconciliation, oracles.
- `Research/BatmobileGrab/DRIVERLEFT_7400.json` - generated: the same, with the full token list.
- `tmp/freebuff/reports/review-G3-01e-fix.md` - this report.
- Scratch (not an output): `tmp/freebuff/scratch/dl7400_dump.py`, `tmp/freebuff/scratch/dl7400_walk.py`.

## Commands run, verbatim

The deliverable, final run (passing):

```
$ python Tools/scripts/review_g3_01e_bc.py --write
wrote Research\BatmobileGrab\DRIVERLEFT_7400.md and Research\BatmobileGrab\DRIVERLEFT_7400.json
script 368 B, 135 tokens, 28 refs, closed=True
Core.ArmouredMode      [254, 318]
Core.BatmobileWinch    [263, 278]
Core.WinchPullType     [284, 290]
Core.IsVehicleAsleep   [223, 328]
oracles: 11/11 ok
write exit=0
-----
$ python Tools/scripts/review_g3_01e_bc.py --check
OK 135 tokens, 28 refs, walk closes on 368 B; md+json byte-identical
four names: {'Core.ArmouredMode': [254, 318], 'Core.BatmobileWinch': [263, 278], 'Core.WinchPullType': [284, 290], 'Core.IsVehicleAsleep': [223, 328]}
oracles: {"adjudication_payload_frame": true, "all_refs_resolve": true, "export_identity": true, "fix_misses_six": true, "fix_offsets_are_prefixes": true, "flag_blocks_differ_only_at_99_178": true, "four_names_offsets": true, "local_form_forced_desyncs": true, "script_anchors": true, "selector_calls": true, "walk_closes": true}
check exit=0
```

The first run of the same command **failed 2 of 11 oracles**, and that is worth recording because it
is what pinned the last two facts:

```
oracles: 9/11 ok FAILED: adjudication_payload_frame, local_form_forced_desyncs
  - oracle adjudication_payload_frame failed: {"Core.ArmouredMode": {"payload_idx_offsets": [277, 341], "adjudication": [277, 341]}, "Core.BatmobileWinch": {"payload_idx_offsets": [286, 301], "adjudication": [286]}, "Core.FakeRoadCollisionStatic": {"payload_idx_offsets": [253], "adjudication": [253]}}
  - oracle local_form_forced_desyncs failed: {"76": {"closed": false, "consumed": 77}, "88": {"closed": false, "consumed": 89}, "100": {"closed": true, "consumed": 368}, "155": {"closed": false, "consumed": 156}, "167": {"closed": false, "consumed": 168}, "179": {"closed": true, "consumed": 368}, "284": {"closed": false, "consumed": 285}}
```

Both were my oracles being too strict, not the decode being wrong: `BatmobileWinch` has two
references (the adjudication cites one, so the test is a subset test), and the `0x00` form is
decided by closure at five sites but by the block oracle at 100/179. After correcting those two
oracles the run is 11/11.

Scratch commands used to reach the tables above (outputs reproduced in the generated `.md`/`.json`;
the 23-line hexdump and the 133-line walk listing are omitted here only for length):

```
$ python tmp/freebuff/scratch/dl7400_dump.py
path RVehicleBatmobile.DriverLeft class Function
payload bytes 406 size field@18 369
script bytes 368 trailer 0b000000020002004a4c000000000000
last8 name idx 19530 = DriverLeft
...
  5 tok=01 idx=-1382 Core.bWasRemoteDriving  cls=BoolProperty
223 tok=01 idx=-1498 Core.IsVehicleAsleep    cls=BoolProperty
230 tok=01 idx=-1361 Core.FakeRoadCollisionStatic cls=BoolProperty
254 tok=01 idx=-1366 Core.ArmouredMode        cls=BoolProperty
263 tok=01 idx=-5673 Core.BatmobileWinch      cls=ObjectProperty
278 tok=01 idx=-5673 Core.BatmobileWinch      cls=ObjectProperty
284 tok=00 idx=-1515 Core.WinchPullType       cls=ByteProperty
290 tok=01 idx=-1515 Core.WinchPullType       cls=ByteProperty
318 tok=01 idx=-1366 Core.ArmouredMode        cls=BoolProperty
328 tok=01 idx=-1498 Core.IsVehicleAsleep     cls=BoolProperty

$ python tmp/freebuff/scratch/dl7400_walk.py
len 368 tokens 133 unexplained 15 [...]
```

The 15 "unexplained" bytes in the first scratch walk were the `0x00`-as-prefix tokens and the
`0x0F`/`0x09` prefixes; the deliverable walk resolves them and reaches 0.

## UNKNOWNs

1. **The names of the one-byte tokens.** `0x03, 0x09, 0x0F, 0x14, 0x20, 0x2A, 0x2C, 0x2D, 0x38,
   0x3A, 0x4A, 0x77, 0x81, 0x82, 0x8C, 0x9B, 0xF8` are consumed as one-byte tokens because the
   walk then closes on 368 bytes; their semantics are not decoded and are not guessed here. What
   would settle it: a shipped `.g.cs`/token table for this build's bytecode, or a function whose
   disassembly is independently known.
2. **`00 1D FC FF FF` at 100 and 179.** Two parses close: a `0x00` reference to `Core.ReturnValue`,
   or `0x00` + `0x1D IntConst 16777212`. The block oracle makes the reference reading the coherent
   one (identical tails, single-byte token difference), but this is a two-parse ambiguity, not a
   proof, and it changes no offset in dispute. Tried: forcing each site to one byte - still closes
   at 100/179 (`consumed 368`), which is why the block oracle exists.
3. **Branch words.** The `0x06/0x07` words (49, 81, 352, 436, 474) are still not offsets in any
   encoding tried (G3-01e's corpus test, unchanged here). Which side of a branch each guard selects
   therefore remains UNKNOWN; the fix's positional association stays `derived`.
4. **Whether the four names are globals or members.** The import path is `Core.<name>`; expanding
   that needs the layout of the importing package, which is not in this read.
5. **Whether the `0x19 Context` tokens carry a skip operand** in this cooked stream. Here they are
   one byte each (closure forces it), but that is an extent, not a meaning.

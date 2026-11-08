# review-G3-10c — constraint partner side, 96-byte body-entry fields, inertia

VERDICT: **minor issues.** The three load-bearing claims survive re-reading: the mass link is a
stored pointer chain and reproduces on every body I tried (including two bodies the card does not
count), the "no partner body" negative is about the whole 24-byte `hknpConstraintCinfo` record and
does **not** contradict G3-10h, and inertia is correctly left UNKNOWN. But four statements in the
card are wrong against the bytes: the body-entry census (`38`/`24` and the 22/23/36/37 exclusion),
"+0x3C = 0x3F800000 in every entry", "read as f32 they are sub-1e-6 noise", and the `54 of 54`
framing that hides that the two mass blocks it leaves out also resolve. The generator's checks
still pass because none of them covers those sentences (§3 below).

Everything here is static and read-only: the donor
`Builds/test-091/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc`
(340368 B) through the existing `jc3hkx.Packfile` loader, plus the two cards' own `--check` modes.
No game process, no install write, no build, no git.

## 1. Mass link, re-derived from the body entry (four bodies, plus a fifth)

Claim: `polytope + 0x20` → `hkRefCountedProperties` → `+0x10` → `hknpShapeMassProperties`, mass at
`+0x28`; 54 of 54 polytopes resolve. I walked it myself, not through the card's code:

| body | body entry | `+0x00` fixup | `+0x20` fixup | `+0x10` fixup | mass @+0x28 |
|---|---|---|---|---|---|
| 0 | 0x2DC0 | 0x5250 `hknpConvexPolytopeShape` | 0x5940 `hkRefCountedProperties` | 0x5970 `hknpShapeMassProperties` | **800.0** (`44480000`) |
| 1 | 0x2E20 | 0x59C0 `hknpConvexPolytopeShape` | 0x5D80 `hkRefCountedProperties` | 0x5DB0 `hknpShapeMassProperties` | **40.0** (`42200000`) |
| 2 | 0x2E80 | 0x5E00 `hknpConvexPolytopeShape` | 0x5F90 `hkRefCountedProperties` | 0x5FC0 `hknpShapeMassProperties` | **5.0** (`40a00000`) |
| 16 | 0x33C0 | 0x8F20 `hknpStaticCompoundShape` | 0x9370 `hkRefCountedProperties` | 0x93A0 `hknpShapeMassProperties` | **25.0** (`41c80000`) |
| (26) | 0x3780 | 0xC570 `hknpStaticCompoundShape` | 0xC9C0 `hkRefCountedProperties` | 0xC9F0 `hknpShapeMassProperties` | **25.0** (`41c80000`) |

These are the **packfile's own fixups**, not offsets I computed: the reverse pointer map says the
record that points at node 0x5940 sits at 21104 = `0x5270` = shape `0x5250` + 0x20, and the record
that points at block 0x5970 sits at 22864 = `0x5950` = node `0x5940` + 0x10. The clue for the first
body is printed below, with the same arithmetic for the other three. So the chain is *stored in the
file*; the mass number is not reached by a guess.

Oracles I ran on it (any of these would fail if the link were wrong):

- 54 polytopes, **54 distinct blocks**, **none shared** by two polytopes → the mapping is 1:1.
- 56 mass blocks in the donor; the only two not reachable from a polytope are **0x93A0 = body 16,
  25.0** and **0xC9F0 = body 26, 25.0**, i.e. the two static compounds — and the same
  `+0x20 → +0x10` path reaches them too (rows above). So the link is **56 of 56 blocks**, not 54.
- Sum check: the 54 polytope-linked masses total **1577.097155**; all 56 total **1627.097155**;
  the difference is exactly **50.0 = 25 + 25**, the two compound blocks.

### Comparison with the 56 masses G3-10b lists

`Research/JC3Grab/PHYSICS_ROLES2.json` → 56 items, sum 1627.097155. The multiset of those values is
**identical** to a fresh scan of the 56 `hknpShapeMassProperties` objects in the donor
(`sorted(...) == sorted(...)` → True). The four bodies' values sit in that multiset as:

| mass | occurrences among the 56 |
|---|---|
| 800.0 | 1 |
| 40.0 | 4 |
| 5.0 | 6 |
| 25.0 | 10 |

So the value alone identifies only body 0 (800.0 is unique); for the others the *pointer* is what
identifies the block, and the value match is a consistency check, not an identity test. That is
worth stating in the card, because "compare the mass with the 56" is weak wherever a value repeats
17 times (1.0) or 10 times (25.0).

## 2. Scope of "no partner body" — record or sub-struct? And G3-10h

**It is the whole 24-byte record, not a sub-struct.** The cinfo *is* `hknpConstraintCinfo`, the
record stored in `hknpPhysicsSystemData+0x50` with a measured 24-byte stride; there is no larger
constraint record wrapped around it. The constraint *objects* (`hkpLimitedHingeConstraintData` etc.,
at 0x4DA80…) are a separate table, and the cinfo's first word is the fixup to one of them.

G3-10h's registry says `hknpConstraintCinfo` has objectSize **0x18** and members
`constraintData +0x00`, `bodyA +0x08`, `bodyB +0x0c`, `flags +0x10`; `bodyB` is `0x7fffffff` in
494/494 shipped records, and a decoded engine block writes `0x7fffffff` into a `+0xc` body field to
detach a body. That is **word 3 of G3-10c's six words** — the `0x7FFFFFFF` column the card dumps.
The two reports therefore agree on the bytes and on the negative ("no second body is stored"), and
they do **not** contradict: G3-10h adds the field's name and the engine's meaning of the value.

The card should still be reworded in two places, because its phrasing invites the contradiction a
reader will look for:

1. "**no second body id exists** in it" → a `bodyB` field exists and holds the invalid marker. The
   defensible sentence is "the record has a second body field, and it is invalid in 100% of the
   donor's 11 records". The card's §1 table header already says "second body? **none**", which is
   the right claim.
2. "+0x0C is the same sentinel the body table uses for **bodies without a part id**" — that gloss
   is not the engine's meaning. G3-10h decoded the sentinel as "no body here" (detach), which is
   strictly better evidence. The *fact* that body entries +0x08 carry the same constant is decoded
   (G3-10b: 2936/2936); the *interpretation* should be replaced.

G3-10c's own UNKNOWN 1 ("partner not stored per-cinfo; next: body table's +0x20 graph or the
entity's constraint list") remains valid, and G3-10h did not close it either.

## 3. What else I re-read, and what is wrong

### 3.1 Body-entry rules (donor, all 62 entries)

Re-read with the same 96-byte stride at `hknpPhysicsSystemData+0x40`:

- **+0x0C**: 42 entries (bodies **0..41**, all of them) hold their own index; **20** entries
  (bodies 42..61) hold `0x7FFFFFFF`; no third value. The rule the code checks — `+0x0C ∈ {i,
  0x7FFFFFFF}` — holds. **But the card's census is wrong**: it says "*the 38 part bodies (0..41
  minus 22/23/36/37); 0x7FFFFFFF for the other 24*". Bodies 22/23/36/37 read
  `+0x0C = 0x16 / 0x17 / 0x24 / 0x25` — their own ids — and the sentinel count is 20, not 24. The
  wheel exclusion belongs to G3-10b's part map (world body −1), not to this field.
- **+0x10**: 62/62 satisfy `(id << 16) | flag` with `flag ∈ {0xFF, 0x01}`; `0x01` exactly at
  bodies **11, 15, 27**, `0xFF` elsewhere. Holds.
- **+0x3C**: **42** entries are `0x3F800000`; **20** entries (42..61) are `0x00000000`. The card's
  "*0x3F800000 in every entry*" is false. Only +0x4C has the "every entry" property.
- **+0x4C**: `{0x3f7fffff, 0x3f800000}`, the latter in the last two — holds.

Why the card passes anyway: `body_id_rule`'s pass/fail uses the code rule (which is correct), and
its *detail* only prints bodies 0,1,2,60,61. The prose counts are not checked by any oracle, and
`quaternion_w` only inspects +0x4C.

### 3.2 The 24 bytes at mass+0x10..+0x27

The words are exactly the card's table (e.g. block 0x5970 = `5997ff8f 300056d8 46853cd9 358018cd
80057dd7 f52a7fe8`), so the *dump* is right. The **description is wrong**: read as f32 these are not
"sub-1e-6 noise". Block 0x5970 reads `5.35e15, 4.67e-10, 1.71e4, 9.54e-7, -5.04e-40, -2.16e32`
(|f32| spans 5.0e-40 … 2.2e32); the other four blocks I dumped span similarly. The conclusion still
stands — the six words are not an IEEE tensor — but it stands on the *rebased/biased* form of the
values (the two's-complement-looking trailing words, the sign pattern), not on "all values are
tiny". As written, the sentence would be refuted by one `struct.unpack`.

Also inconsistent: the module docstring says word +0x1C "scales with mass (ratio ~2^-31)", while
the md says `/2^31/mass` has relative spread 2.65 (i.e. not a constant scale). The md is the
measured one; the docstring reads like a decode.

### 3.3 Fleet and checks

- `jc3_physics_roles3.py --check` → **OK**, 7/7 oracles, md+json byte-identical.
- `jc3_constraint_code.py --check` (G3-10h) → **17/17**, "MATCH" both files.
- Scope note: G3-10c's fleet is 41 raw files / 40 decoded in `_gamedata/JC3grab/hkx/all`; G3-10h's
  494 records come from **50** files. Different file sets, so the two record counts are not
  comparable; neither card claims they are.

## 4. Commands run (verbatim)

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/g10c_review.py
donor bytes=340368 objects=430 bodies=62 polytopes=54 mass_blocks=56 cinfos=11
block masses: [800.0, 40.0, 5.0, 1.0, 40.0, 5.0, 1.0, 275.0, 29.999998, 1.0, 1.0, 1.0, 29.999998, 1.0, 1.0, 1.0, 25.0, 0.002738, 0.001947, 0.005841, 0.009266, 0.001947, 0.005841, 0.009269, 1.0, 25.0, 40.0, 40.0, 25.0, 25.0, 25.0, 25.0, 25.0, 25.0, 0.00517, 0.011661, 0.004465, 0.00517, 0.011661, 0.017723, 0.00446, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 5.0, 35.0, 25.0, 25.0, 1.0, 5.0, 5.0, 5.0]
G3-10b count=56 sum=1627.097155 equal_to_scan=True
multiset of the 56: {0.001947: 2, 0.002738: 1, 0.00446: 1, 0.004465: 1, 0.00517: 2, 0.005841: 2, 0.009266: 1, 0.009269: 1, 0.011661: 2, 0.017723: 1, 1.0: 17, 5.0: 6, 25.0: 10, 29.999998: 2, 35.0: 1, 40.0: 4, 275.0: 1, 800.0: 1}
distinct blocks reachable from polytopes: 54 polytopes with a block: 54 blocks not reached: ['0x93a0', '0xc9f0'] blocks shared by >1 polytope: []

--- body 0: entry 0x2DC0 ---
  +0x00 fixup -> 0x5250 hknpConvexPolytopeShape (entry words ['00000000', '00000000', '7fffffff', '00000000', '000000ff', '00000000'])
  +0x20 fixup -> 0x5940 hkRefCountedProperties ; +0x10 fixup -> 0x5970 hknpShapeMassProperties
  mass @ block+0x28 = 800.0  (raw 44480000)
  occurrences of that value in the 56: 1
  words at block +0x10..+0x27: ['5997ff8f', '300056d8', '46853cd9', '358018cd', '80057dd7', 'f52a7fe8']
  fixup records that point AT 0x5250: [('0x2dc0', '0x2DC0'), ('0x4990', '0x4990'), ('0x4f38', '0x4F38'), ('0x4aa40', '0x4AA40')]
  fixup records that point AT node 0x5940: [21104]
  fixup records that point AT block 0x5970: [22864]

--- body 1: entry 0x2E20 ---
  +0x00 fixup -> 0x59C0 hknpConvexPolytopeShape (entry words ['00000000', '00000000', '7fffffff', '00000001', '000100ff', '00000000'])
  +0x20 fixup -> 0x5D80 hkRefCountedProperties ; +0x10 fixup -> 0x5DB0 hknpShapeMassProperties
  mass @ block+0x28 = 40.0  (raw 42200000)
  occurrences of that value in the 56: 4
  words at block +0x10..+0x27: ['5bac8d55', '3000f8f9', '3a6a4b99', '3200152c', '812e7a61', 'f48074b3']
  fixup records that point AT 0x59C0: [('0x2e20', '0x2E20'), ('0x4998', '0x4998'), ('0x4f48', '0x4F48'), ('0x4b210', '0x4B210')]
  fixup records that point AT node 0x5D80: [23008]
  fixup records that point AT block 0x5DB0: [23952]

--- body 2: entry 0x2E80 ---
  +0x00 fixup -> 0x5E00 hknpConvexPolytopeShape (entry words ['00000000', '00000000', '7fffffff', '00000002', '000200ff', '00000000'])
  +0x20 fixup -> 0x5F90 hkRefCountedProperties ; +0x10 fixup -> 0x5FC0 hknpShapeMassProperties
  mass @ block+0x28 = 5.0  (raw 40a00000)
  occurrences of that value in the 56: 6
  words at block +0x10..+0x27: ['4d8cd0bc', '30800680', '46844c15', '300005e0', '81d27656', 'f2cf6aab']
  fixup records that point AT 0x5E00: [('0x2e80', '0x2E80'), ('0x49a0', '0x49A0'), ('0x4f58', '0x4F58'), ('0x4b290', '0x4B290')]
  fixup records that point AT node 0x5F90: [24096]
  fixup records that point AT block 0x5FC0: [24480]

--- body 16: entry 0x33C0 ---
  +0x00 fixup -> 0x8F20 hknpStaticCompoundShape (entry words ['00000000', '00000000', '7fffffff', '00000010', '001000ff', '00000000'])
  +0x20 fixup -> 0x9370 hkRefCountedProperties ; +0x10 fixup -> 0x93A0 hknpShapeMassProperties
  mass @ block+0x28 = 25.0  (raw 41c80000)
  occurrences of that value in the 56: 10
  words at block +0x10..+0x27: ['0b31fffe', '3100b540', '66dc071e', '32006251', '800187b6', 'f4ee7fff']
  fixup records that point AT 0x8F20: [('0x33c0', '0x33C0'), ('0x4a10', '0x4A10'), ('0x5078', '0x5078'), ('0x4c6e0', '0x4C6E0')]
  fixup records that point AT node 0x9370: [36672]
  fixup records that point AT block 0x93A0: [37760]

reachable masses: n=54 sum=1577.097155
masses with no polytope owner: [25.0, 25.0] -> [('0x93a0', 25.0), ('0xc9f0', 25.0)]
EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python tmp/freebuff/scratch/g10c_review2.py
bodies=62 bodies_with_mass_block=42 distinct_blocks=42 total_blocks=56 bodies_without=[(42, 68480, 'hknpExternMeshShape'), (43, 145392, 'hknpExternMeshShape'), (44, 157008, 'hknpExternMeshShape'), (45, 158816, 'hknpExternMeshShape'), (46, 170432, 'hknpExternMeshShape'), (47, 172240, 'hknpExternMeshShape'), (48, 212816, 'hknpExternMeshShape'), (49, 221664, 'hknpExternMeshShape'), (50, 230512, 'hknpExternMeshShape'), (51, 235760, 'hknpExternMeshShape'), (52, 239088, 'hknpExternMeshShape'), (53, 251296, 'hknpExternMeshShape'), (54, 263504, 'hknpExternMeshShape'), (55, 273792, 'hknpExternMeshShape'), (56, 284864, 'hknpExternMeshShape'), (57, 287184, 'hknpExternMeshShape'), (58, 289504, 'hknpExternMeshShape'), (59, 290768, 'hknpExternMeshShape'), (60, 292032, 'hknpDynamicCompoundShape'), (61, 305440, 'hknpDynamicCompoundShape')]
blocks no body entry reaches: ['0x95a0', '0x9780', '0x9a00', '0x9c20', '0x9e00', '0xa030', '0xa250', '0xcc90', '0xcf50', '0xd170', '0xd3f0', '0xd6b0', '0xd980', '0xdba0']
blocks shared by >1 body: []

shape classes over body entries: {'hknpConvexPolytopeShape': 40, 'hknpDynamicCompoundShape': 2, 'hknpExternMeshShape': 18, 'hknpStaticCompoundShape': 2}

--- spot rows ---
body  0 words[3,4]=00000000 000000ff  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body  1 words[3,4]=00000001 000100ff  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body  2 words[3,4]=00000002 000200ff  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 11 words[3,4]=0000000b 000b0001  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 15 words[3,4]=0000000f 000f0001  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 16 words[3,4]=00000010 001000ff  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 26 words[3,4]=0000001a 001a00ff  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 27 words[3,4]=0000001b 001b0001  w15(+0x3c)=3f800000  w19(+0x4c)=3f7fffff
body 60 words[3,4]=7fffffff 000000ff  w15(+0x3c)=00000000  w19(+0x4c)=3f800000
body 61 words[3,4]=7fffffff 000000ff  w15(+0x3c)=00000000  w19(+0x4c)=3f800000

+0x0c == own index: 42 bodies [0..41]
+0x0c == 0x7fffffff: 20 bodies [42..61]
+0x0c neither: []
(id<<16)|0xFF-or-0x01 rule violations: []
flag=0x01 bodies: [11, 15, 27]
+0x3c values: ['00000000', '3f800000']
+0x4c values: ['3f7fffff', '3f800000']
EXIT2=0
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/jc3_physics_roles3.py --check
OK cinfos 11 / constraints 11 / mass links 54; fleet 40 files; md+json byte-identical
oracles: {"body_id_rule": true, "cinfo_no_second_body": true, "constraint_type_tags": true, "fleet_invariants": true, "mass_link": true, "mass_word_correlation": true, "quaternion_w": true}
CHECK3_EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_constraint_code.py --check
PASS  the hknpConstraintCinfo registry record resolves by name
PASS  its objectSize is the file record stride (0x18 = 24)
PASS  its member table is constraintData, bodyA, bodyB, flags
PASS  bodyA sits at +0x08 and bodyB at +0x0c, both inside the record
PASS  the four member offsets tile the object: 0x00, 0x08, 0x0c, 0x10
PASS  hknpConstraint has bodyIdA/bodyIdB members and is 0x38 bytes
PASS  all 50 fleet files scan and yield 494 records
PASS  every record's reference field is resolved by the packfile fixup map
PASS  its high half at +0x04 is zero in every record - a pointer half, not a body id
PASS  +0x08 (bodyA) is a real body index in every record
PASS  +0x0c (bodyB) is 0x7fffffff in every record, never a body index
PASS  bodyA at +0x08 reproduces the prior card's 'recorded body' field
PASS  the failing +0x04 reading is gone: no record has a body id there
PASS  the cinfo->constraint instantiation is reported, not assumed
PASS  the engine tests a +0xc body field against 0x7fffffff at a reproducible site count
      4 sites: ['0x14028169f', '0x140281887', '0x1415e5d72', '0x141943278']
PASS  a decoded block writes the sentinel to detach a body, so it means 'no body'
PASS  no 24-byte walk reads both body offsets, so no creation site is claimed
17/17 checks pass
MATCH Research\JC3Grab\CONSTRAINT_CODE.md
MATCH Research\JC3Grab\CONSTRAINT_CODE.json
CHECK10H_EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python - <<'PY'
for mb in (0x5970, 0x5DB0, 0x5FC0, 0x93A0, 0xC9F0):
    ws=[struct.unpack_from("<I",blob,b+mb+0x10+4*k)[0] for k in range(6)]
    fs=[struct.unpack_from("<f",blob,b+mb+0x10+4*k)[0] for k in range(6)]
    print("block 0x%X mass=%r" % (mb, struct.unpack_from("<f",blob,b+mb+0x28)[0]))
    print("  words:", ["%08x"%w for w in ws])
    print("  f32  :", ["%.6g"%f for f in fs])
    print("  |f32| min=%.3g max=%.3g  all<1e-6=%s" % (
        min(abs(f) for f in fs), max(abs(f) for f in fs),
        all(abs(f)<1e-6 for f in fs)))
PY
echo "EXIT=$?"
```

Output:

```
block 0x5970 mass=800.0
  words: ['5997ff8f', '300056d8', '46853cd9', '358018cd', '80057dd7', 'f52a7fe8']
  f32  : ['5.34796e+15', '4.66895e-10', '17054.4', '9.54396e-07', '-5.0432e-40', '-2.16134e+32']
  |f32| min=5.04e-40 max=2.16e+32  all<1e-6=False
block 0x5DB0 mass=40.0
  words: ['5bac8d55', '3000f8f9', '3a6a4b99', '3200152c', '812e7a61', 'f48074b3']
  f32  : ['9.71382e+16', '4.69199e-10', '0.000893766', '7.45539e-09', '-3.20466e-38', '-8.14186e+31']
  |f32| min=3.2e-38 max=8.14e+31  all<1e-6=False
block 0x5FC0 mass=5.0
  words: ['4d8cd0bc', '30800680', '46844c15', '300005e0', '81d27656', 'f2cf6aab']
  f32  : ['2.95311e+08', '9.31507e-10', '16934', '4.65745e-10', '-7.73116e-38', '-8.21662e+30']
  |f32| min=7.73e-38 max=8.22e+30  all<1e-6=False
block 0x93A0 mass=25.0
  words: ['0b31fffe', '3100b540', '66dc071e', '32006251', '800187b6', 'f4ee7fff']
  f32  : ['3.42815e-32', '1.87295e-09', '5.19526e+23', '7.47294e-09', '-1.40519e-40', '-1.51167e+32']
  |f32| min=1.41e-40 max=1.51e+32  all<1e-6=False
block 0xC9F0 mass=25.0
  words: ['10dcffe5', '31004943', '75980cad', '32006f08', '80026e0a', 'f3cd7fff']
  f32  : ['8.7169e-29', '1.86681e-09', '3.85491e+32', '7.47583e-09', '-2.23146e-40', '-3.25628e+31']
  |f32| min=2.23e-40 max=3.85e+32  all<1e-6=False
EXIT=0
```

```
cd /e/Modding/JC3-Batmobile && PYTHONIOENCODING=utf-8 uv run python - <<'PY'
+0x3c != 1.0: [(42, '00000000', 'hknpExternMeshShape'), (43, '00000000', 'hknpExternMeshShape'), (44, '00000000', 'hknpExternMeshShape'), (45, '00000000', 'hknpExternMeshShape'), (46, '00000000', 'hknpExternMeshShape'), (47, '00000000', 'hknpExternMeshShape'), (48, '00000000', 'hknpExternMeshShape'), (49, '00000000', 'hknpExternMeshShape'), (50, '00000000', 'hknpExternMeshShape'), (51, '00000000', 'hknpExternMeshShape'), (52, '00000000', 'hknpExternMeshShape'), (53, '00000000', 'hknpExternMeshShape'), (54, '00000000', 'hknpExternMeshShape'), (55, '00000000', 'hknpExternMeshShape'), (56, '00000000', 'hknpExternMeshShape'), (57, '00000000', 'hknpExternMeshShape'), (58, '00000000', 'hknpExternMeshShape'), (59, '00000000', 'hknpExternMeshShape'), (60, '00000000', 'hknpDynamicCompoundShape'), (61, '00000000', 'hknpDynamicCompoundShape')]
body 22: +0x0c=00000016 +0x10=001600ff shape=hknpConvexPolytopeShape
body 23: +0x0c=00000017 +0x10=001700ff shape=hknpConvexPolytopeShape
body 36: +0x0c=00000024 +0x10=002400ff shape=hknpConvexPolytopeShape
body 37: +0x0c=00000025 +0x10=002500ff shape=hknpConvexPolytopeShape
count w15==0: 20
body 26 shape=0xC570 hknpStaticCompoundShape node=0xC9C0 block=0xC9F0 mass=25.0
EXIT=0
```

Scratch probes (read-only): `tmp/freebuff/scratch/g10c_review.py`, `g10c_review2.py`, and the two
inline heredocs above. No project file was edited; `PHYSICS_ROLES3.*` was only read.

## 5. What I could not check

- **Inertia format.** Re-read the bytes, not the encoding. Whether the six words are a biased
  triple with separate exponents is still open, and my dump gives no new handle beyond the card's
  (the "sub-1e-6" framing must be dropped before anyone builds on it).
- **The other 56-mass files.** The multiset comparison is donor-only; I did not re-run the 40-file
  fleet for mass values (out of scope for this review).
- **The 14 blocks no body entry reaches** (0x95a0 … 0xdba0) — consistent with the seven instances
  inside each static compound, but I did not decode that ownership.
- **What fills `bodyB` at simulation time** — unchanged UNKNOWN from G3-10h; I did not re-walk the
  image this time.
- **The `0x01` flag at bodies 11/15/27** — still unexplained; my census only confirms the set.

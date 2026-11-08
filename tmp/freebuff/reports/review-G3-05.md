# Independent review — G3-05 (BmAK packages the grab never read)

**VERDICT: minor issues.** The decoded numbers I re-read are correct and the byte accounting is
honest, but two of the card's UNKNOWNs are mis-scoped (the values they call unknown sit in a
decodable export the card already lists), and one table presents a 40-item list as "every
export". Nothing invented; no value is fabricated; no rework of the census is needed.

Artifact under review: `Research/BatmobileGrab/PACKAGES_G305.md` (970 lines),
`Research/BatmobileGrab/PACKAGES_G305.json` (922,055 B), `Tools/scripts/grab_packages_g305.py`.
I did not write this card and changed nothing outside this report.

## 1. `--check` output (verbatim)

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_packages_g305.py --check; echo "CHECK_EXIT=$?"
OK: 20 packages, 320,415 exports, 3,099 relevant, 646 undecoded; 22/22 checks; md byte-identical
CHECK_EXIT=0
```

Reproduces the record byte for byte. Its internal arithmetic also holds: the per-package export
column sums to 320,415 (5+6+1136+945+1055+6×5+174890+142232+6×4+92), the relevant column to
3,099, and undecoded 646 = 489 (Startup) + 157 (StartupPatch).

## 2. Spot-checks — five values re-read from the raw source by me

Method: file sizes by `os.stat`; the two big packages' headers and export tables parsed by my own
`struct` reads off `Startup.upk`/`StartupPatch.upk` (chunk-by-chunk `zlib`/`lzo1x`, stopping at the
export table — not the tool's `PartialPackage`); small packages through `upk_read.Package(path)`.

| # | value in the record | my source | match |
|---|---|---|---|
| 1 | `Startup.upk` 434,869,146 B, 174,890 exports, 67,407 names, 7,419 imports | my header parse of the raw header at offset 12 (`version` 863, `licensee` 32995 also match) | **yes** |
| 2 | `StartupPatch.upk` 248,812,096 B, 142,232 exports | my header parse of the raw header | **yes** |
| 3 | `Gad_RBatmobileRemoteBm_SF` 113,443 B, 5 exports, classes `Package×2, ObjectReferencer×1, SwfMovie×1, Texture2D×1`, no vehicle class | `upk_read.Package` export table + `object_class` census | **yes** |
| 4 | `Playable_Batmobile_Std_SF` 4 exports / **1** with ≥1 tag; 3 empty; 0 undecoded (matches `GAPS.md` line 27, `4 | 1`) | my own `walk_tags` per export: `ObjectReferencer` 30 B → 1 tag, walk ends 28 (`closed_terminator`); the other three payloads are exactly `0000`, 2 B | **yes** |
| 5 | `Showcase_Batmobiles_Standard` 1,055 exports; exactly one `SkeletalMesh`, named `Batmobile_V2` | `upk_read.Package` census; mesh list = `[(98, 'Batmobile_V2')]`, count 1 | **yes** |
| 6 (extra) | the two name indices quoted in §4: `0x64E3 = FrontCollisionCylinder`, `0xDB8E = RearCollisionCylinder` | my Startup export-table read: export 82147 `name_index=0x64E3` → `'FrontCollisionCylinder'`; 82148 `0xDB8E` → `'RearCollisionCylinder'` | **yes** |

Limitation stated plainly: for check 6 I verified the name-index side from the export table. The
other half of that claim — that each payload's `int32` at +4 equals it — I did **not** re-read,
because that payload sits at offset 416,463,177 and would cost ~416 MB of chunk decompression; it
rests on the tool's own check over 21 payloads.

## 3. Issues

### I-1 (must fix, scope): U-1 and U-2 call "unknown" a value that is in a decoded stream

- **Where:** `PACKAGES_G305.md` §4 ("Two payload shapes hide behind \"untagged\"") and §7 `U-1`,
  `U-2`; `PACKAGES_G305.json` `decode` / `owners`.
- **Claim:** *"the values of the `BmScript.RVehicleBatmobile` class-default properties (97
  objects)"* and *"the values of the `BmScript.RBatmobileRemoteBm` gadget parameters (48 objects)"*
  are UNKNOWN, *"where it would be found: the untagged-object format, G3-06"*.
- **Why it is unsupported:** those 97 + 48 exports are the classes' **property descriptors**
  (`UProperty` objects), and a descriptor payload cannot hold a value: every one is 30 bytes, the
  same size and shape as `Engine.upk`'s `CylinderComponent` members (`FloatProperty` exports of 30
  bytes whose `int32` at +2 is the next-member index — decoded in `COLLISION_CYLINDERS.md` this
  session). The property **values** are serialised in the class default object, **`Startup.upk`
  export 7530 `Default__RVehicleBatmobile`, 978 bytes**, which is *not* described as an
  undecodable object anywhere in the card. I walked it from byte 0:

  ```
  93 tags, end 976/978 (eof)
  by type: {'ObjectNCRProperty': 63, 'IntProperty': 2, 'BoolProperty': 5, 'FloatProperty': 15,
            'ArrayProperty': 6, 'NameProperty': 2}
  offset span: 92 .. 8624
  FloatProperty tags: [(8588, 5.0), (8592, 25.0), (8604, 100.0), (6032, 1300.0), (6752, 2000.0),
                       (6756, 5000.0), (6760, 2500.0), (6848, 2500.0), (7864, 50.0), (1688, 210.0),
                       (1808, 4000.0), (1860, 0.5), (1864, 0.5), (1556, 1.0), (1072, 6000.0)]
  BoolProperty tags: [(8564, True), (4576, True), (2180, True), (2184, True), (1496, True)]
  ```

  So the values are present, serialised, and cheaply readable — 15 floats and 5 bools with bytes
  attached. **Fix:** say the 30-byte objects are descriptors (no values by construction), and point
  U-1/U-2 at export 7530 instead of at G3-06's untagged format. Note honestly in the card that
  only 15 floats are present, i.e. only the non-default ones; naming each one needs the class
  layout (the same "which slot" problem G3-01b solved for the cylinders), which the card does not
  claim and this review did not do.

### I-2 (must fix, a printed number): the asset tables are capped at 40 and captioned "every export"

- **Where:** `PACKAGES_G305.md` §2, the three `The assets it owns (every export of these classes, by
  name)` tables — `SkeletalMeshSocket | 40 | SkeletalMeshSocket (×40)` in all three levels.
- **Why:** the cap is in the tool, `grab_packages_g305.py:438` — `rec["assets"] = {k: v[:40] for k, v
  in assets.items()}``. The real counts, from my own census, are **63** (Jokerfied), **55** (MK2),
  **65** (Standard), all owned by the level's single mesh (`Mesh.Batmobile_Jokerfied_Skin` 63,
  `Mesh.Batmobile_MK2_Skin` 55, `Batmobile_V2_Mesh.Batmobile_V2` 65). The same cap silently truncates
  every class above 40 (`MaterialExpressionScalarParameter` 194/143/140, `Texture2D` 72/65/62 …).
  The class-census numbers are right; only the name lists are truncated, but the caption says they
  are complete. **Fix:** either raise the cap or caption them "first 40 names of N".

### I-3 (should fix): U-3 frames the cylinders' dimensions as this package's, and 0x16C is not one

- **Where:** §7 `U-3`, and §4's sentence *"which class slot each offset is - and therefore what the
  cylinder dimensions are - is G3-01's question"*.
- **Why:** the two Startup templates carry tags only at `0x13C` (316, `ReplacementPrimitive`) and
  `0x16C` (364). `0x16C` is `PerInstanceRandom` — the two templates differ there (0.9998 vs 0.6012),
  which is exactly what a per-instance random looks like — so a reader of U-3 can be led to read a
  random number as a radius/height. The dimensions are at **540/544** and are not serialised in
  either Startup object at all; they live in `BmGame.upk` base templates 142597/142598 (78.0 and
  175.0) and are now named `CollisionHeight`/`CollisionRadius` by `COLLISION_CYLINDERS.md`
  (`AABBScale` = 548, 1.0). **Fix:** state that the Startup templates carry no dimension and say
  where they do live.

### I-4 (should fix): U-7's six "not-read" payloads include two that are already decoded

- **Where:** §7 `U-7` ("6 relevant `Startup` payloads that end past the 512 MiB decode budget").
- **Why:** the six are `BatmanCollisionMeshBattleMode0`, `BatmanCollisionMeshPursuitMode0`,
  `WheelFL`, `WheelFR`, `WheelRL`, `WheelRR`. The first two (Startup exports **171103 / 171104**)
  are decoded in `Research/BatmobileGrab/COLLISION.md` / `.json` (tags, `HiddenGame`,
  `BlockActors`, `CollideActors`, and the `StaticMesh` references 175973/175974 with their
  `RB_BodySetup`s). So 2 of the 6 are not open questions; only the four `SVehicleWheel` payloads
  are budget-blocked. **Fix:** split U-7 into "resolved elsewhere (2)" and "budget-blocked (4)".

### I-5 (wording only): §1's "4 token hits" mixes a count with a class breakdown

- **Where:** §1 — *"The 4 token hits in the package are its own name appearing in owner paths and in
  its `Package` exports: Package×2, SwfMovie×1, Texture2D×1."*
- **Why:** the package has 5 exports and the record says 4 hits; the breakdown `Package×2` is
  presented as part of the hits while the sentence also says the hits are in "its `Package`
  exports". The metric (what counts as a hit — export name, owner path, or class) is defined
  nowhere in the md, so 4 vs 5 cannot be reconciled from the record. The underlying census is
  right (5 exports, those classes, no vehicle class), so this is a definition/wording defect, not a
  wrong number.

## 4. UNKNOWNs that the bytes can resolve

| unknown | how, and where the value is |
|---|---|
| **U-1** vehicle class-default property values | Walk `Startup.upk` export **7530** from byte 0 — done above: 93 tags, 976/978 bytes, 15 floats + 5 bools with values. Naming each float needs the class layout: the 97 descriptor exports give the member list; `BMSDK_OFFSETS.json` (used by the card for the 97 names) or the tag offsets give the slots. Not attempted here beyond confirming the stream. |
| **U-2** remote-gadget parameter values | Same mechanism: the gadget's CDO is a separate export — `Startup.upk` **export 536 `Default__RBatmobileRemoteBm`, outer `BmScript`, 364 bytes**, offset 16,866,662 (my export-table read; the card lists its single child `SkeletalMeshComponent` but never walks the CDO itself). Walk export 536 from byte 0 the same way as 7530. |
| **U-3** cylinder radius/height | Already resolved outside this card: `COLLISION_CYLINDERS.md` — 540 = `CollisionHeight` = 78.0, 544 = `CollisionRadius` = 175.0, 548 = `AABBScale` = 1.0, values from `BmGame.upk` 142597/142598. `0x16C` = 364 = `PerInstanceRandom`, not a dimension. |
| **U-4** does `StartupPatch` override a `Startup` value | For the vehicle class: no — the card's own check "StartupPatch carries no RVehicleBatmobile class defaults" passes, and my export-table read confirms `StartupPatch.upk` has 142,232 exports with the `RVehicleBatmobile` owner absent from its `BmScript` rows. What remains of U-4 is the gadget's parameter values, i.e. U-2. |
| **U-7** (2 of 6) | `BatmanCollisionMeshBattleMode0` / `PursuitMode0` are decoded in `COLLISION.md` (Startup 171103/171104). Only the four `SVehicleWheel` payloads stay blocked, and they are 14-byte objects — a raised budget or a chunk index would settle them. |
| **U-5 / U-6** | Not resolvable from bytes: U-5 is influence, U-6 is what the game binds at runtime. Both correctly deferred (G3-07). |

## 5. What holds up

- **Byte accounting over opinion:** the status vocabulary (`empty` / `untagged` / `closed_prefix` /
  `closed` / `closed_payload` / `closed_terminator` / `partial`) is used consistently and the
  statuses sum to the export counts (Startup: 19 + 2 + 7 + 6 + 489 = 523 ✓).
- **The GAPS.md baseline is quoted correctly** and independently reproduced: `GAPS.md` lines 21–27
  hold `4/1, 4/2 … 92/80` and line 20 `5490`; my own walk of `Playable_Batmobile_Std_SF` returns
  exactly 4 exports / 1 with a tag, and the three zero-tag payloads are literally `0000`.
- **The §5 argument (25–50 % is a counting artifact) is sound** and is the card's best finding: the
  metric counts objects with ≥1 tag, so zero-property class stubs read as undecoded. That claim is
  verified by the byte statuses, not asserted.
- **No over-claiming of the untagged/native objects:** the card records them, does not invent
  layouts, and defers the format to G3-06 — the correct call, with the one scope error in I-1.
- **The "what each package adds" censuses** I could recompute (Gad 4 pairs, Showcase_Batmobiles 6,
  Std_* 3/3/3/3/3/3 and 10) are consistent with the package tables.

Scope of this review: read-only. I ran `--check`, re-read six values from the raw packages with my
own parsing, and walked one extra object (Startup 7530). I did not re-read every row, did not
re-derive the 117,106 / 102,359 "adds over base" pair counts, and did not touch any file except
this report.

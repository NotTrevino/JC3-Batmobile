STATUS: done. Two corrections to the D1 premise, both decoded:

1. **BmAK's clean state is not "all mud scalars zero".** The shipped *mainbody* material instance
   carries `Mud_Opacity = 50`, `Mud2_Opacity = 2`, `Mud_Edges_Opacity = 100`; the values are
   multipliers against a mask, and the mask/chapter state is what changes, not the scalars. Only
   `Mud_WetStreaks` is **absent** from the mainbody instance (it is authored on the tyre, wheel and
   disc-break instances as 1 / 1 / 1.2).
2. **There is no `DirtColor` parameter in BmAK at all.** The colour parameters that exist are
   `Mud_Colour`, `Mud2_Colour` and `Damage_Dirt_Colour`. `DirtColor` as named in the brief is
   **UNKNOWN/absent** — searching all 206 systems' parameter names returns no such FName.

On the JC3 side the dirt path is real and explicit: `SupportDirt` (`cb2[19].y`), `m_DirtParams`
(`cb2[5]`), `m_DirtBlend` (`cb2[6]`), `m_DirtColor` (`cb2[7]`), a shared `vehicle_dirt_msk.ddsc`
dirt mask at sampler `s6`, and a per-block dirt flag. Corpus scan: 399 `CarPaintMM` blocks in 160
`.rbm` files, `SupportDirt` **1.0 on 76 blocks (61 files), 0.0 on 323**. The donor body the build
uses (`sportsmuscle_body_lod1.rbm`) ships `SupportDirt = 0` on every block, so the Batmobile is
clean **by absence of the flag**, not by an authored value — exactly what D1 says must stop.

## Files written

| file | what |
|---|---|
| `tmp/freebuff/reports/app-mud-and-dirt-default.md` | this report |

Read-only: no `.rbm`, build tree or ledger row was modified; every command below only decodes.
Revert = delete this one file.

## 1. BmAK clean-state numbers (decoded)

Sources: `Research/BatmobileGrab/MATERIALS.md` (instance parameter blocks), `SKINS.md` (per-material
parameter lists), `COLOUR_PARAMS.md` (the master material's own `FloatProperty` defaults).

| parameter | mainbody instance (`Batmobile_V3_Mainbody_NEW_MIC`, master `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC`) | wheel-arch instance (`Batmobile_V3_WheelArchs_NEW_MIC`) | tyre | wheel | disc-break | master default |
|---|---:|---:|---:|---:|---:|---:|
| `Mud_Opacity` | **50.0** | 2.0 | 30.0 | 1.0 | 0.0 | 100.0 |
| `Mud2_Opacity` | **2.0** | 0.65 | 1.5 | 2.0 | 1.0 | 0.65 |
| `Mud_Edges_Opacity` | **100.0** | 4.0 | 1.2 | 0.5 | 0.2 | 0.3 |
| `Mud_WetStreaks` | **absent** (not authored on the body) | absent | 1.0 | 1.0 | 1.2 | 1.0 |
| `Mud_Density` | absent | 0.11 | absent | absent | absent | — |
| `Mud_Roughness` | absent | absent | 0.2 | absent | absent | — |

Colour parameters (vector, linear RGBA), decoded from the same instances:

| parameter | value | where |
|---|---|---|
| `Mud_Colour` | `[0.2652, 0.1433, 0.06887, 1]` | `SKINS.md:208` (and 217, 230, 256, 376, …) |
| `Mud2_Colour` | `[0.1492, 0.05605, 0.01548, 1]` | `SKINS.md:208` |
| `Damage_Dirt_Colour` | `[0.41573, 0.389493, 0.33165, 1]` | `SKINS.md:208`, `COLOUR_PARAMS.md:67,152` |
| `DirtColor` | **does not exist** (0 hits over the 206 systems' parameter names) | — |

`Mud_Opacity = 50` with `Mud_Edges_Opacity = 100` on the body is the reason a zero-everything
"clean" reading is wrong: those are multipliers into the mud mask/edge mask, and the *mask strength*
is what the chapter script drives. The material default (`Mud_Opacity = 100`,
`Mud_Edges_Opacity = 0.3`, `Mud2_Opacity = 0.65`, `Mud_WetStreaks = 1.0`) is a different number set
again, so "the BmAK default" must be quoted per instance, never as one figure.

## 2. How JC3 dirt works (decoded)

Member names and offsets are from `Research/JC3Grab/CB0_SLOTS.md` §3 (12/12 shader reflection headers
agree; `.rbm` `CarPaintMM` block is the cbuffer payload, `rbm_geom` re-encodes it byte-identically):

| member | slot | block offset | type | carriers |
|---|---|---:|---|---|
| `m_DirtParams` | `cb2[5]` | 80 | float4 | `static_params` float4[5] @ payload `+0x59` |
| `m_DirtBlend` | `cb2[6]` | 96 | float4 | `static_params` float4[6] @ payload `+0x69` |
| `m_DirtColor` | `cb2[7]` | 112 | float4 | `static_params` float4[7] @ payload `+0x79` |
| `SupportDirt` | `cb2[19].y` | 308 | float | `static_support` float[5] @ payload `+0x13d` |
| dirt mask | sampler `s6` `DirtMap` | — | `.ddsc` | shared `vehicle_dirt_msk.ddsc` (`COLOUR.md` §2) |
| dirt flag | block `flags` | payload `+0x1` | u32 | `0x101F` blocks carry the dirt bit (`COLOUR.md` §1) |

So JC3 dirt is **per material block, not per vehicle entity**: each block declares whether it
supports dirt (`SupportDirt`), how strong (`m_DirtParams`, `m_DirtBlend`), and what colour
(`m_DirtColor`), and sample it through one shared mask texture. The engine then paints dirt on that
block as the car drives — the vehicle-level side is only which blocks carry the flag.

## 3. Corpus scan of the JC3 dirt members (decoded this session)

All `.rbm` under `E:/Modding/_gamedata/JC3grab/b13b/unpacked` (277 files), decoded with
`rbm_geom.decode`, `CarPaintMM` blocks only:

| fact | value |
|---|---:|
| `CarPaintMM` blocks | **399** in **160** files |
| `SupportDirt = 1.0` | **76** blocks (61 files) |
| `SupportDirt = 0.0` | 323 blocks |
| blocks with nonzero `m_DirtParams` or `m_DirtBlend` | **94** |
| most common `m_DirtParams` / `m_DirtBlend` pair | `(0, 0, 1.5, 0)` / `(1, 1, 0, 0)` |
| `m_DirtColor` distinct values | `(0,0,0,1)` ×200 · `(0.2652, 0.1433, 0.0689, 1)` ×105 · `(0.35, 0.3, 0.235, 1)` ×94 |

The `(0.2652, 0.1433, 0.0689)` dirt colour is the **same colour as BmAK's `Mud_Colour`**
`[0.2652, 0.1433, 0.06887]` to 4 decimals — i.e. JC3's paint dirt colour and BmAK's mud colour are
already the same authoring value. That is a match, not a coincidence to be tuned.

**Donor body as shipped** (`sportsmuscle_body_lod1.rbm`, 2,311,365 B, 17 blocks, 16 `CarPaintMM`):

| block | `m_DirtParams` | `m_DirtBlend` | `m_DirtColor` | `SupportDirt` |
|---|---|---|---|---|
| 0, 5, 6, 8–16 | `(0,0,0,0)` | `(0,0,0,0)` | `(0,0,0,1)` | 0.0 |
| 2, 3, 4, 7 | `(0,0,0,0)` | `(0,0,0,0)` | `(0.2652, 0.1433, 0.0689, 1)` | 0.0 |

**Discrepancy, recorded as UNKNOWN:** `COLOUR.md` §1 reports the same-named file as **9** blocks
with flags `0x1004`/`0x101F`, while this session's decode of the `b13b` copy returns **17** blocks
and reads `flags = 0x0000/0x0200` for the paint blocks. Both came from `rbm_geom`; one of the two
files is a different build. Which block set the RC donor actually ships must be settled by
re-running the decode on the exact file the build copies, before any per-block dirt value is written.

## 4. What the build must set explicitly (the answer to D1)

The clean, lore-accurate default is **dirt off by authored value, not by omission**:

| member | clean value to write | why |
|---|---|---|
| `SupportDirt` (`cb2[19].y`) | **`0.0`** | turns the dirt path off for that block; today it is 0 only because the donor never set it |
| `m_DirtParams` (`cb2[5]`) | **`(0, 0, 0, 0)`** | zero strength, so a later script or tool that raises `SupportDirt` still paints nothing |
| `m_DirtBlend` (`cb2[6]`) | **`(0, 0, 0, 0)`** | no blend weight into the dirt layer |
| `m_DirtColor` (`cb2[7]`) | **`(0.2652, 0.1433, 0.0689, 1)`** | keep the authored colour inert; it equals BmAK `Mud_Colour`, so if dirt is ever enabled the tint is already correct |

Mechanism: edit the private copy of the donor `.rbm` (`Builds/bm-RC*/…/sportsmuscle_body_lod1.rbm`),
then read the four members back through `rbm_geom.decode` and confirm `rbm_geom.encode` reproduces
the block byte-for-byte (the same oracle `CB0_SLOTS.md` uses). That is an offline build step; the
test ban is untouched.

## 5. Closest system and the gap (STAGES.md rule)

| BmAK feature | closest JC3 system | carrying members | gap |
|---|---|---|---|
| mud layer, chapter-scripted strength | paint dirt path | `SupportDirt`, `m_DirtParams`, `m_DirtBlend`, `m_DirtColor`, shared `s6 vehicle_dirt_msk.ddsc` | **no per-chapter material parameter animation** in JC3 content: the block is static, the only runtime writer is the engine. Build closes it by publishing two states (clean = zeros; dirty = BmAK's 50/2/100) rather than a script |
| separate `Mud_*` vs `Damage_Dirt_*` layers | one dirt path + one damage path | `m_Dirt*` vs `m_Damage`/`m_DamageBlend`/`m_DamageColor` (`cb2[15..17]`) | BmAK layers mud over dirt; JC3 has two independent block paths, so the build must decide per block which one carries mud |
| `Mud_WetStreaks`, `Mud_Roughness`, `Mud_Density`, `Mud_Reflectivity` | none named in the paint block | — | **no member**. Closest is packing them into the `s6` dirt mask channels + `cb2[5]` unused components, which changes the mask texture, not a scalar. This is the capability the build has to author (a new mask), not tune |
| `DirtColor` | `m_DirtColor` (`cb2[7]`) | exact name mismatch only; the value is carried | none for colour |

## Commands and output, verbatim

```text
$ python - <<'PY'   # corpus scan, rbm_geom.decode over every .rbm
...
CarPaintMM blocks: 399 files: 160
SupportDirt (cb2[19].y) distribution: {1.0: 76, 0.0: 323}
blocks with nonzero DirtParams or DirtBlend: 94
   debris_vehicle_debri01_lod1.rbm 0 flags=0x0004 (0.0, 0.0, 1.5, 0.0) (1.0, 1.0, 0.0, 0.0)
   sportsmuscle_c_mirror_lod1.rbm 0 flags=0x001F (0.0, 0.0, 1.1, 0.0) (1.0, 1.0, 0.0, 0.0)
DirtColor distinct: 3
   200 (0.0, 0.0, 0.0, 1.0)
   105 (0.2652, 0.1433, 0.0689, 1.0)
    94 (0.35, 0.3, 0.235, 1.0)
files with SupportDirt!=0: 61
```

```text
$ python - <<'PY'   # donor body, per block
size 2311365 blocks 17
   0 CarPaint flags=0x0000 static=288 support=(0.0, ...) dirtP=(0.0, 0.0, 0.0, 0.0) dirtC=(0.0, 0.0, 0.0, 1.0) ntex=12
   2 CarPaint flags=0x0000 static=288 support=(0.0, ...) dirtP=(0.0, 0.0, 0.0, 0.0) dirtC=(0.2652, 0.1433, 0.0689, 1.0) ntex=12
   ...
  13 CarPaint flags=0x0100 static=288 support=(0.0, ...) dirtP=(0.0, 0.0, 0.0, 0.0) dirtC=(0.0, 0.0, 0.0, 1.0) ntex=12
```

```text
$ grep -n "Batmobile_V3_Mainbody_NEW_MIC" Research/BatmobileGrab/MATERIALS.md
1064:| Playable_Batmobile_SF | Batmobile_V3_Mainbody_NEW_MIC | `Material_Worn.Batmobile_V3_WheelArchs_NEW_MIC` | Material0_Reflectivity=0.2000, ... Mud2_Opacity=2.0000, Mud_Edges_Opacity=100.0000, Mud_Opacity=50.0000, Vector_Displacement_Multiplier=1.0000 | ...
```

## UNKNOWNs

1. **`DirtColor` in BmAK.** Tried: parameter-name extraction over all 206 systems
   (`objects.jsonl`) — `DirtColor` 0 hits; the real names are `Mud_Colour`, `Mud2_Colour`,
   `Damage_Dirt_Colour`. Would be found in: nothing; the brief's name is a paraphrase.
2. **Which block set the RC donor actually ships** (9 blocks with `0x101F` per `COLOUR.md` vs 17
   blocks per this decode of the b13b copy). Would be settled by decoding the exact `.rbm` the build
   copies, before writing `SupportDirt`.
3. **What `m_DirtParams.zw` and `m_DirtBlend` components mean.** Decoded values exist
   (`(0,0,1.5,0)`, `(1,1,0,0)`, `(0,0,1.1,0)`), semantics are in the SHEX, not on disk. Same for the
   per-block dirt flag bit (flags `0x101F` blocks carry dirt per `COLOUR.md`; the bit index is not
   isolated).
4. **Whether JC3's engine writes the dirt members at runtime** (as BmAK's chapter script does) or
   only reads the static block. The write site is in the executable; no project decode reads it.

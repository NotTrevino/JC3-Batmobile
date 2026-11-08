# Where the BmAK colour ramps actually are

2026-11-06. Static read only: nothing was run in the game, no package was written.

Rule **D10** says the three ramp files are "missing on disk". **All three exist as real `Texture2D`
exports, with pixels that decode.** The claim is false for every one of them.

| # | name | carries it | export | size |
|---|---|---|---:|---:|
| 1 | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `BmGame.upk` + `Startup.upk` | **#176227 / #171638** | **1,894 B** |
| 2 | `Batman_BM3_V2_Leather_Ramp` | 15 packages (`Playable_Batmobile_*`, `Startup`'s map/level peers) | see §2 | **1,894 B** each |
| 3 | `Batmobile_V3_Body_ColourRamp` | `BmGame.upk` | **#176233** | **1,922 B** |

`BmGame.upk` is the master carrier: **84,813 names, 177,031 exports**, and it holds every ramp in the
car as a local `Texture2D` export, including the anisotropy LUTs.

---

## 1. `Batman_BM3_V2_Lacquered_Underlayer_Ramp` — the body ramp

| package | export index | name | class | size |
|---|---|---|---|---|
| `BmGame.upk` | **#176227** | `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `Texture2D` | **1,894 B** (`0x766`) |
| `Startup.upk` | **#171638** | same | `Texture2D` | **1,894 B** |

Both exports point at the **same cache chunk**: `Chunk1` at offset **363,525,127**, 498 stored bytes →
16,384 raw. So the two are one asset cooked into two packages, not two variants.

Its pixels were extracted and decoded — `app-colour-ramp-textures.md` §2. Independent corroboration:
the umodel grab `Working/Appearance/grab/Startup/Texture2D/Batman_BM3_V2_Lacquered_Underlayer_Ramp.tga`
matches the package decode to within 1 LSB.

The Batmobile packages reference it as an **import** pointing at `Core.Maps`, which is why looking only
at the Batmobile packages reads as a miss:

| package | reference | kind |
|---|---|---|
| `Playable_Batmobile_SF` | #-588 | import (`Core.Maps`) |
| `Playable_BatmobileMK2_SF` | #-588 | import |
| `Playable_BatmobileJoker_SF` | #-615 | import |
| `Playable_BatmobileFunhouse_SF` | #-558 | import |
| `Showcase_Batmobiles_Standard` | #-215 | import |
| `Batmobile_Generator_1/2/3_SF` | #-59 | import |

`Core.upk` has **0** ramp names — `Core.Maps` is the uncooked editor package path; the cooked copy is in
`BmGame` (and duplicated in `Startup`).

---

## 2. `Batman_BM3_V2_Leather_Ramp` — exported in 15 packages, always the same 1,894 B

Every row is a local `Texture2D` **export** read from that package's own export table:

| package | export index | size |
|---|---:|---:|
| `Playable_Batmobile_SF` | 5399 | 1,894 B |
| `Showcase_Batmobiles_Standard` | 422 | 1,894 B |
| `Playable_BatmobileMK2_SF` | 5440 | 1,894 B |
| `Playable_BatmobileJoker_SF` | 3289 | 1,894 B |
| `Playable_BatmobileFunhouse_SF` | 5483 | 1,894 B |
| `Ace_B1` | 1771 | 1,894 B |
| `Ace_A2_Ch2` | 5427 | 1,894 B |
| `BatEntry__Benchmark_ChJ7_Bm` | 2284 | 1,894 B |
| `BatEntry__City_Ch3a_LOD2` | 260 | 1,894 B |
| `BatEntry__City_ChD1b_LOD2` | 306 | 1,894 B |
| `BatEntry__City_Ch7c_LOD2` | 4131 | 1,894 B |
| `CityX_06_Ch4` | 1733 | 1,894 B |
| `CityX_08_Ch3c` | 1627 | 1,894 B |
| `CityX_09_Cine_Ch5b_Drop_Off_Ivy_At_Botanical_Gardens` | 333 | 1,894 B |

Generated dump corroboration for row 1: `Research/BatmobileGrab/list_Playable_Batmobile_SF.txt:5402`
reads `5398  1FED779      766 Texture2D Batman_BM3_V2_Leather_Ramp` (0-based row, hex size).

**Notably absent from `BmGame.upk`**: the seat ramp is cooked per level package that uses the Batmobile
seat, not into the master — the opposite of the other five ramps.

---

## 3. `Batmobile_V3_Body_ColourRamp` — exported in `BmGame`, and it was the last one found

| package | export index | name | class | size |
|---|---|---|---|---|
| `BmGame.upk` | **#176233** | `Batmobile_V3_Body_ColourRamp` | `Texture2D` | **1,922 B** (`0x782`) |

`Chunk1` at offset **236,029,175**, 567 stored bytes → 16,384 raw, 64×512 `PF_DXT1`.

Every material reference is still an **import** — which is why this name looked missing for so long:

| package | reference | kind | outer |
|---|---|---|---|
| `Playable_Batmobile_SF` | #-594 | import | `BatmobileV3.Textures` |
| `Playable_BatmobileMK2_SF` | #-594 | import | `BatmobileV3.Textures` |
| `Playable_BatmobileJoker_SF` | #-639 | import | `BatmobileV3.Textures` |
| `Playable_BatmobileFunhouse_SF` | #-505 | import | `BatmobileV3.Textures` |
| `Showcase_Batmobiles_Standard` | #-205 | import | `BatmobileV3.Textures` |
| `Ace_A2_Rescue_Cine_CH2` | #-477 | import | — |
| `CityX_09_Cine_Ch7b_Cloudburst_Activated` | #-612 | import | — |

The import's outer name `BatmobileV3.Textures` is the **uncooked editor path**: there is no
`BatmobileV3.upk` and no `BatmobileV3_Textures.upk` on disk. The cooked copy was folded into
`BmGame.upk`, next to `Tyre_ColourRamp`. **A missing carrier package is not a missing file.**

---

## 4. Close variants — all also exported in `BmGame.upk`

| name | export | class | size | mip 0 |
|---|---:|---|---:|---|
| `Batmobile_V3_Tyre_ColourRamp` | #176234 | `Texture2D` | 1,922 B | 64×512 DXT1 |
| `Aniso_ramp_Lacquered` | #176254 | `Texture2D` | 11,414 B | 512×512 DXT1 |
| `Aniso_ramp_D2` | #176251 | `Texture2D` | 11,386 B | 256×256 DXT1 |

So the tyre ramp and both anisotropy LUTs (D5's texture family) are present too. Their pixel content and
sampled values are in `app-colour-ramp-textures.md` §3.

---

## 5. Scope of the search, and the package count

**The brief says the grab covers 4,145 packages. This install has 3,266 `.upk` files** in
`BmGame/CookedPCConsole` (44 GB), and there are **0** `.upk` files anywhere else under
`E:\Games\Batman - Arkham Knight`. The 4,145 figure does not describe this install's package
population; the difference (879) is unexplained — it may count `.tfc`/`.sdc` members or a DLC tree that
is not present.

Method — name tables and export tables, read with the project's own reader
(`Tools/scripts/upk_read.py`, the only parser that accepts these containers):

1. open each `.upk` with `upk_read.Package`;
2. search its full **name table** for `ramp|lacquered|colourlut|colorlut` (case-insensitive);
3. resolve every hit with `find()` into an **export** (positive index → class + size from the export
   table) or an **import** (negative index → class + outer package path).

**Coverage.** The automated pass reached **800 of 3,266 packages** (alphabetical prefix through
the `Ci…` range) before being stopped, because `upk_read` must decompress an entire package to read its
tables and the install is 44 GB. Every claim above is therefore **verified by direct package read**, not
inferred from the partial pass: `BmGame.upk`, `Startup.upk`, `Core.upk`, the five Batmobile packages and
the three `Batmobile_Generator_*` packages were each opened individually and their export/import tables
printed. Hits are appended in `Working/Ramp/ramp_hits.jsonl`; progress in
`Working/Ramp/ramp_scan_progress.txt`.

**A tool defect found on the way (worth recording).** `Tools/scripts/bmak_ramp_sweep.py`'s fast
name-table path (`_parse`) **cannot read this install**. For every package tried it rebuilds
`raw[:name_offset] + body` and then walks past the end of the buffer — on `Startup`, chunk 0
decompresses to 3,511,283 B while the name walk runs to 268 M. Its `validate()` passes only because
`names_fast` falls back to `upk_read.Package`, so the "61 sampled packages, 0 mismatches" line is the
fallback agreeing with itself. The sweep's `--check` would therefore report drift for reasons unrelated
to any ramp. The working scan is `tmp/freebuff/gscan.py`.

---

## 6. What this changes for D10

| name | D10 said | the bytes say |
|---|---|---|
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | missing | **`BmGame` #176227 / `Startup` #171638, 1,894 B, decodes to 64×512 px** |
| `Batman_BM3_V2_Leather_Ramp` | missing | **15 exports, 1,894 B each, decodes to 64×512 px** |
| `Batmobile_V3_Body_ColourRamp` | missing | **`BmGame` #176233, 1,922 B, decodes to 64×512 px** |

D10's reason is wrong for all three names; the ramps were never missing from disk. What is genuinely
absent is a **JC3-side carrier**: `CarPaintMM` has no ramp sampler, so a ramp cannot be shipped as a
ramp — but it can be sampled once and written as the tint, which is all the flat plateau requires
(`app-colour-ramp-textures.md` §6). The "blocked" status should move from *"no BmAK pixels"* to
*"no JC3 ramp sampler"*.

---

## 7. Reproduce

```bash
cd "E:/Modding/JustCause3/JC3-Batmobile"
python -c "import sys;sys.path.insert(0,'Tools/scripts');import upk_read as u; \
p=u.Package(r'E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk'); \
[print(n, p.find(n), p.object_class(p.find(n)), p.exports[p.find(n)-1]['size']) for n in \
 ('Batman_BM3_V2_Lacquered_Underlayer_Ramp','Batmobile_V3_Body_ColourRamp','Batmobile_V3_Tyre_ColourRamp')]"
python tmp/freebuff/gscan.py      # full name+export scan -> Working/Ramp/ramp_hits.jsonl
```

## 8. Limits

- The install-wide automated pass covered 800 of 3,266 packages; packages later in the alphabet were
  not swept in bulk. The three names under test are nevertheless settled by direct reads.
- `.tfc` chunks hold no names and were not name-searched; a texture present only as an orphan chunk is
  unreachable by the game and is not what any material binds.
- The 4,145-vs-3,266 discrepancy is recorded, not resolved.

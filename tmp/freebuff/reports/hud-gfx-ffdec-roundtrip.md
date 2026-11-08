# HUD `ui/hud.gfx` — FFDec round trip, and the P3 payload we can now ship

STATUS: **done**. JPEXS FFDec 26.4.0 re-saves JC3's `ui/hud.gfx` without touching the container, the tag
order or the single AVM2 `DoABC`; the only drift is 137 `DefineShape*`/`DefineSprite` tag lengths and 131
same-length shape/sprite body re-encodes, and all **839** exported shapes are SVG-identical, so the re-encode is
lossless. Two real losses were found and are recorded, not hidden: FFDec **drops 631 undeclared trailing bytes**
that the original carries, and the movie's 375 `tag1008` / 9 `tag1009` GFx tags have no name in the tag table.
The P3 probe payload is built (one text tag, styling preserved), receipted, and **not installed**; no game was
started or attached.

## Files written

| file | what it is |
|---|---|
| `Tools/scripts/hud_gfx_roundtrip.py` | new `--write` / `--check` script: parses the CFX container and the tag stream itself and recomputes every number below |
| `Working/HUD_GFX_ROUNDTRIP.json` | generated: container fields, tag census, orig↔rt↔p3 comparisons |
| `Builds/probe-L0/P3-hud-gfx/payload/ui/hud.gfx` | the P3 payload, 387,528 B, sha256 `b798c0491bec3f8051add6ab3cabdf524f54c374777f8d6846bccb73cc6fa667` |
| `Builds/probe-L0/P3-hud-gfx/PROBE.md` | rewritten: the change, the expected observation, pass/fail, undo (this file replaces the earlier UNKNOWN version, sha256 `c37f6469…`) |
| `Builds/probe-L0/P3-hud-gfx/receipt.json` | rewritten to match the shipped payload (schema 1, same keys as P1/P2 plus `source_sha256`, `tool`, `install_path`, `checks`) |
| this report | — |

Scratch (outside the repo, disposable): `E:/Modding/_JC3grab/hud_roundtrip/` — `orig.gfx`, `rt.gfx`,
`p3_candidate.gfx`, `orig.xml`, `*_tags.txt`, `txt*/`, `sv_orig/`, `sv_rt/`.

## 1. The input, and why it is the right movie

`Research/JC3grab/INDEX.jsonl` names two copies (verbatim):

```
{"path":"ui/hud.gfx","hash":"DDD7F9D7","archive":"archives_win64/game2","mount":"base","offset":105447424,"size":296631,"source":"gibbed-filelist"}
{"path":"ui/hud.gfx","hash":"DDD7F9D7","archive":"patch_win64/game6","mount":"patch","offset":288028672,"size":386281,"source":"gibbed-filelist"}
```

The extracted copy already on disk, `E:/Modding/_gamedata/JC3grab/hud/hud.gfx`, is **386,281 B** — the patch
movie — and sha256 `c88af343186af1e150d89f7c77e48018185ded6e523c7e2cd37ba5d01e258ecd`. It was used read-only;
no re-extraction was needed. Container: `CFX` (compressed GFx), version 15, ZLIB, `gfx=true`,
display rect `[0,0,25600,14400]` = 1280×720 twips-scaled, frameRate 24 (`0x1800`), 1 frame, **2,405 tags**.

## 2. Step 2 — round trip with no edit: every difference

`-swf2xml` then `-xml2swf` on the same file. Header survives: `CFX`, version 15, ZLIB, `gfx=true`. The
`-header -set gfx true` step turns out to be **unnecessary** for this movie — the header dump of the round-trip
copy reports `gfx=true` without it.

| # | measured difference | original | round trip |
|---|---|---|---|
| 1 | sha256 | `c88af343…258ecd` | `7fe781c8…8c0787` |
| 2 | size on disk | 386,281 B | 387,420 B (**+1,139**) |
| 3 | declared length (`CFX` header field) | 974,225 | 973,538 |
| 4 | decompressed body | 974,848 B | 973,530 B (**−1,318**) |
| 5 | tag count / tag-id sequence | 2,405 | 2,405, **identical sequence** (no tag added, dropped or reordered) |
| 6 | tags whose **length** changed | — | **137**: `DefineShape2` 108, `DefineShape3` 12, `DefineShape4` 11, `DefineSprite` 6, all **shorter** in the copy, deltas −1…−18 B |
| 7 | tags whose **body** changed at equal length | — | **131**: `DefineShape2` 90, `DefineShape4` 24, `DefineSprite` 12, `DefineShape3` 5 |
| 8 | undeclared trailing bytes after `End` | **631** | **0** — dropped |
| 9 | exported shape art (`-export shape`, 839 files each side) | — | **839 identical, 0 different, 0 missing** |

What did **not** change, tag for tag, byte for byte: the single `DoABC` (the entire HUD's AS3), all **223**
`DefineEditText`, the fonts (`DefineFont*`, 0 in this movie — text is `fontClass`-driven), `SymbolClass`,
`ImportAssets2` ×2, `CSMTextSettings` ×83, `DefineMorphShape` ×15 / `DefineMorphShape2` ×13,
`DefineSceneAndFrameLabelData`, `FileAttributes`, `SetBackgroundColor`, `GFx ExporterInfo`.
So: the drift is confined to shape/sprite *layout records*, which GFx bit-packs; item 9 proves the drift is a
re-serialisation, not a change of content.

Reading of item 6: the copy is *smaller in the tag stream* but *larger on disk* — the shorter shape records remove
1,318 B of decompressed data while a slightly less compressible stream costs 1,139 B compressed. Both files are
valid; nothing in the numbers suggests truncation (item 5).

## 3. Step 3 — the one visible text edit

**Route chosen:** `-replace` on a single `DefineEditText`, importing the **whole `initialText` HTML** with one word
swapped, so the label keeps its font size, colour and alignment.

**Which label, and why not the first candidate.** The brief asks for a static label. The first candidate,
chid **401** `TXT_name` = `WREAK HAVOC`, is *reachable* from the main timeline but its chain is
`401 → 403 (TXT_name) → 406 (MCI_text_group) → 409 (MCI_sub_task_00) → 422 (MCI_task_group_00) → 2285 (MCI_settlement_list)`,
i.e. it draws with the settlement/task list — a panel, not a permanent element. Rejected for that reason.
The shipped target is **chid 2241**:

| | |
|---|---|
| chain | `2241 --TXT_label--> 2242 --MCI_life_bar_with_text--> 2277`, and **2277 is one of the 10 sprites placed directly on the main timeline** |
| tag | `DefineEditText` chid 2241, tag index 2,330, **149 B → 150 B** |
| before | `<p align="center"><font size="14" color="#000000" letterSpacing="0.000000" kerning="1">VEHICLE</font></p>` |
| after | `<p align="center"><font size="14" color="#000000" letterSpacing="0.000000" kerning="1">BM PROBE</font></p>` |

Verification of the edit: re-parsing the payload shows 2,405 tags in the original order, and **exactly one tag body
differs from the original** — index 2,330, tagId 37 — while the other 2,404 tags (including `DoABC` and the 222
other text tags) are byte-identical. `-export text` on the payload reads back `BM PROBE` for 2241 and still reads
`WREAK HAVOC` for 401. Header `CFX` / v15 / ZLIB / `gfx=true` / rect unchanged. The payload is therefore a
*strictly smaller edit* than the no-edit round trip: it keeps FFDec's shape re-encoding but has no unrelated
text change.

Payload: 387,528 B, sha256 `b798c0491bec3f8051add6ab3cabdf524f54c374777f8d6846bccb73cc6fa667`, installs at
`drop/ui/hud.gfx`. Expected observation, pass/fail and undo are in `Builds/probe-L0/P3-hud-gfx/PROBE.md`; the
machine-readable version is `receipt.json`.

## 4. Step 4 — what FFDec warns about (the U6 concern)

`reports/hud-cluster-closest-system-plan.md` §8 states **U6** as *"AVM2 GFx v0f → JC3 loader compatibility"*, settled
by *"`ffdec -dumpSWF` tag compare of `HudModuleBatmobile.Image` vs `ui/hud.gfx`"*.

Tag census of `ui/hud.gfx` (decoded, `Working/HUD_GFX_ROUNDTRIP.json` `tag_census`):

| tag | count | | tag | count |
|---|---|---|---|---|
| `DefineSprite` | 828 | | `DefineMorphShape2` | 13 |
| `DefineShape` | 499 | | `PlaceObject2` | 10 |
| `tag1008` | **375** | | `tag1009` | **9** |
| `DefineEditText` | 223 | | `ImportAssets2` | 2 |
| `DefineShape2` | 198 | | `DoABC` | **1** |
| `DefineShape4` | 105 | | `SymbolClass`, `End`, `FileAttributes`, `GFx ExporterInfo`, `SetBackgroundColor`, `ShowFrame`, `DefineSceneAndFrameLabelData` | 1 each |
| `CSMTextSettings` | 83 | | `DefineShape3` | 37 |

- **Compression**: `CFX` = ZLIB, and both FFDec writes keep it. Not a risk.
- **Unknown GFx tags**: `1008` (375) and `1009` (9) are outside the SWF/GFx tag table FFDec names — it carries them
  opaquely. They survive the round trip with **identical bodies and lengths** (they are in neither drift list),
  which is the behaviour we need. What they *are* is **UNKNOWN**; a settler is one Scaleform SDK header or the
  `GFx` reference source, neither in this repo.
- **U6, the part this experiment settles (JC3 side)**: a re-saved movie keeps its AVM2 block intact — the single
  `DoABC` is byte-identical, so FFDec did not decompile/recompile the scripts, and the tag order is unchanged.
  **The part it does not settle**: whether JC3's loader accepts the re-save at all, and whether
  `HudModuleBatmobile.Image` (BmAK side) has a compatible tag set. The first needs the P3 session; the second
  needs the BmAK movie extracted (not done here).
- **The one warning worth carrying into the probe**: the 631 trailing bytes. They are *not* zeros — the tail is
  `"_reticle\0…hud_fla.reticle_displ…deat_reinforcement…"` (string data; the only printable run longer than 3
  chars also recognised by the XML is `_reticle`, and it appears in no `name="…"` attribute). FFDec declares the
  file length without them and drops them. Whether JC3's loader reads past the declared length is **UNKNOWN**;
  if the probe fails with a blank HUD, re-append those 631 bytes and retry — they are preserved verbatim in the
  scratch copy `orig.gfx` (bytes `974217 …` of the decompressed body, before re-compression).

## 5. UNKNOWNs

| # | UNKNOWN | what was tried | what settles it |
|---|---|---|---|
| 1 | does JC3 load a private `ui/hud.gfx` from the dropzone | no evidence in the repo or the community writers check; cannot be tested under the test ban | the P3 session (`Builds/probe-L0/P3-hud-gfx/PROBE.md`) |
| 2 | what `tag1008` (375) / `tag1009` (9) are | tag table + FFDec naming; bodies survive unchanged | Scaleform SDK / GFx source header, or a GFx reader that names them |
| 3 | is the 631-byte tail required by the loader | tail extracted and inspected; the only printable run is `_reticle` | the P3 session, or a JC3-side GFx loader dump |
| 4 | does the BmAK `HudModuleBatmobile.Image` tag set match (U6, BmAK side) | not attempted in this task | that movie's own `-dumpSWF`, compared against this census |
| 5 | is `MCI_life_bar_with_text` drawn when *not* in a vehicle | chain proven to the main timeline, draw condition not decoded | an AS3 read of that sprite, or the probe session on foot vs driving |
| 6 | which of the two archived copies (`base` 296,631 B vs `patch` 386,281 B) the loader picks | both are indexed with the same hash `DDD7F9D7`; no loader rule decoded | the loader's patch-override rule, or a live check |

## 6. Commands run (verbatim, key ones)

```
java -jar E:/Modding/_tools/ffdec/ffdec.jar -swf2xml orig.gfx orig.xml
java -jar E:/Modding/_tools/ffdec/ffdec.jar -xml2swf orig.xml rt.gfx
java -jar E:/Modding/_tools/ffdec/ffdec.jar -header orig.gfx          # CFX v15 ZLIB gfx=true 974225
java -jar E:/Modding/_tools/ffdec/ffdec.jar -header rt.gfx            # CFX v15 ZLIB gfx=true 973538
java -jar E:/Modding/_tools/ffdec/ffdec.jar -dumpSWF orig.gfx > orig_tags.txt
java -jar E:/Modding/_tools/ffdec/ffdec.jar -dumpSWF p3_candidate.gfx > p3_tags.txt
java -jar E:/Modding/_tools/ffdec/ffdec.jar -export text txt orig.gfx          # 401 -> "WREAK HAVOC"
java -jar E:/Modding/_tools/ffdec/ffdec.jar -export shape sv_orig orig.gfx     # 839 files
java -jar E:/Modding/_tools/ffdec/ffdec.jar -export shape sv_rt rt.gfx         # 839 files, 0 differ
java -jar E:/Modding/_tools/ffdec/ffdec.jar -replace orig.gfx p3_candidate.gfx 2241 t2241.txt
python Tools/scripts/hud_gfx_roundtrip.py --write
python Tools/scripts/hud_gfx_roundtrip.py --check
```

Output of the last two: `sizes {orig 386281, rt 387420, p3 387528}`, `tags {orig 2405, rt 2405, p3 2405}`,
`rt_ids_same true`, `rt_len_diffs 137`, `rt_len_deltas [-18 … -1]`, `rt_body_diffs 131`, `edit_diffs 1`,
`edit_only_text true`, `unknown_tag_ids [1008, 1009]`, `WARN original carries 631 undeclared trailing bytes that
FFDec drops`, then **`CHECK OK`, exit 0**.

The check enforces: the same tag count and tag-id sequence, no drift outside `DefineShape*`/`DefineSprite`, at
least some drift reported (so a broken parser cannot pass silently), the payload differing from the original in
exactly one text tag, and the original being `CFX`. It does not gate on the 631-byte drop, because that drop is a
property of the tool, not a failure of our edit — it is printed as a WARN and carried in `container` in the JSON.

## 7. COMPROMISES

None. No value, parameter or behaviour was accepted as a limit; the payload is one label swap, and every loss the
tool introduces is named above with its settler. No build tree `Builds/bm-*` was edited, nothing was installed in a
dropzone, and no game process was started or attached.

## 8. Revert

Delete `Tools/scripts/hud_gfx_roundtrip.py`, `Working/HUD_GFX_ROUNDTRIP.json`,
`Builds/probe-L0/P3-hud-gfx/payload/`, and this report; restore `Builds/probe-L0/P3-hud-gfx/PROBE.md` and
`receipt.json` with `git checkout -- Builds/probe-L0/P3-hud-gfx/PROBE.md Builds/probe-L0/P3-hud-gfx/receipt.json`
(prior PROBE.md sha256 `c37f64694af81429790b67b75a951946915a5d89538b33b2855b951815044c7a`). Nothing outside
`E:/Modding/_JC3grab/hud_roundtrip/` (disposable scratch) and the repo was touched.

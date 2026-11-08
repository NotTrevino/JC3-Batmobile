# RC5 — the six G3 asset paths (DONE)

**Six in, three out.** Three of the six are gate normalisation errors, one is a reference the
stock entity makes identically, and two are real gaps the merge must fill. On unchanged
`Builds/bm-RC4` the normalised gate reports **G3 dangling 3** where the RC4 gate reports 6, and
its total dangling rows fall **7 → 4** (the four `F30CCB1C` owner links are untouched and still
dangle; they are the other half of the V-03 work).

| | |
|---|---|
| source (read only) | `Builds/bm-RC4/.../v0300_car_kensington_sportsmuscle_debug.epe`, 134,072 B, sha256 `a8d5d11f…` |
| gate copy | `Tools/scripts/v03_wiring_rc5.py` (RC4 original untouched), writes `tmp/freebuff/rc5-verify/wiring.json` |
| classifier | `Tools/scripts/rc5_asset_refs.py` (`--write`, `--check`), writes `Builds/bm-RC5-entity/asset_refs.json` |
| RC4 gate, unchanged file | `FAIL G3: 32 asset paths (ctune 17/17, etune 2/3, ftune 1/3, model_xml 0/1, pfx 0/1, wtune 6/7) … dangling 6` |
| RC5 gate, same file | `FAIL G3: 32 asset paths (ctune 17/17, etune 2/3, ftune 1/3, model_xml 1/1, pfx 1/1, wtune 7/7) … dangling 3` |

`rc5_asset_refs.py --check` exits **0** (`6 -> 3 dangling on unchanged RC4, 1 stock + 2 real gaps,
document matches`); two `--write` runs are byte-identical (`cmp` clean); `git status --porcelain
Builds` is empty and `Builds/bm-RC4/verify/wiring.json` does not exist.

## 1. The six, with every lookup the brief asks for

Carriers are read from the `.epe` with an indent-authoritative walk; `member` is the `.epe` member
that holds the string, `occurrences` the number of members naming it. Hashes are Jenkins
one-at-a-time over the ASCII path (`rbmhdr.name_hash`, pinned against `HashName.exe`), and the
convention is validated on a known row (`accomplishments/accomplishments.bin` → `3A8DC752`, the
index's own value).

| # | path exactly as the `.epe` stores it | `.epe` byte | carrier (member, occurrences) | jenkins source / compiled | index hits (path, +c, lower, back-slash, hash) | verdict |
|---:|---|---:|---|---|---|---|
| 1 | `editor/entities/jc_environments/shared/rigid_object_effect_settings_default.etune` | `0xecf4` | `CBulletWeaponBase` ×4 (`w602_mediumtank_canon`, `w603_mediumtank_mgun`, `w618_sportsmuscle_missile`, `w618_sportsmuscle_missile_emp`), member `35B57209`, 4 | `A4B4D90E` / `6A501CCF` | 0 / 0 / 0 / 0 / 0 | **stock_donor_identical** |
| 2 | `editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftune` | `0x2974` | `CForcePulse` `CForcePulse_Sonar` (`AC7A15C1=FFFF801D`), member `SettingsFile`, 1 | `878028AA` / `B225A2C4` | 0 / 0 / 0 / 0 / 0 | **real_gap** |
| 3 | `editor/entities/jc_explosions/vehicles/truck_emp.ftune` | `0x13a0` | `CForcePulse` `CForcePulse_EMP` (`EAEFF7B1=FFFF801C`), member `SettingsFile`, 1 | `BEA29B98` / `39B3B4FE` | 0 / 0 / 0 / 0 / 0 | **real_gap** |
| 4 | `editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_grip_point.wtune` | `0xee50` | four weapons, member `9E74F03F`, 4 | `BCC66E6C` / `CA22A669` | resolves as `…/w206_mounted_capstone_m2hm.ee` | **gate_normalisation_error** |
| 5 | `models/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_body.model_xml` | `0xef88` | four weapons, member `F9DCF6AB`, 4 | `15D6B347` / `C271F3B5` | resolves as `…/w206_mounted_capstone_m2hm.ee` | **gate_normalisation_error** |
| 6 | `models/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm_body_col.pfx` | `0xedf0` | four weapons, member `98BBA63E`, 4 | `1EDE97E8` / `0881C190` | resolves as `…/w206_mounted_capstone_m2hm.ee` | **gate_normalisation_error** |

No case, slash, `+c` or hash variant of any of the six exists in the index, and none is present in
`Builds/bm-RC4/aaf` (the tool records both per variant). The index is therefore not a *missing-file*
problem for any of them: the six names genuinely are not archive entries.

### How complete the index is (why absence had to be read carefully)

`Research/JC3Grab/INDEX.json` records `tab_entries 81953`, `named_rows 81952`,
`unnamed_entries 1` (that one is `patch_win64/game4`, `unnamed_magic E04A0100` — not a tune).
`INDEX.jsonl` carries 81,952 rows, so the index names every tab entry but one; a name absent from
it is very probably absent from the shipped archives. `INDEX.json` is a *summary* and holds no
paths, so every lookup here ran against `INDEX.jsonl`; the summary's `by_extension` block is also
inconsistent for these families (`.wtunec 105`, `.pfxc 39`, but `.etunec 0` and `.ftunec 0` while
the jsonl holds two `.ftunec` paths), so no verdict rests on it.

## 2. The three normalisation errors

The RC4 gate searches only the built `.ee`'s inner records (`build = set(inner)`) plus the archive
name index, and only the exact name or its `+c` leaf. That cannot see a record compiled **inside**
an `.ee`/`.wtunec` container. All three w206 names live in the container
`editor/entities/jc_weapons/04_mounted/w206_mounted_capstone_m2hm/w206_mounted_capstone_m2hm.ee`,
whose own leaf **is** in the index (1,699,840 B, `archives_win64/game36`), next to
`w206_mounted_capstone_m2hm.wtunec` (14,228 B, `patch_win64/game1`). The directory in the
`models/…` reference is a different tree from the container's `editor/entities/…` directory, which
is why a same-directory rule alone still dangled two of the three.

Corroboration that these are stock sub-assets, not ours: the stock APC graph — the entity the four
weapons were cloned from — names all three identically, and it also names
`rigid_object_effect_settings_default.etune`. Nothing in the clone invented them.

## 3. The one stock reference

`rigid_object_effect_settings_default.etune` is carried by all four weapons (member `35B57209`) and
is present verbatim in the stock APC graph, so the clone copied it unchanged. It is **not** an
archive entry in any variant, and the indexed siblings are the `_light` / `_medium_light` variants.
Whether the stock APC resolves it from inside its own `.ee` is UNKNOWN here (that `.ee` is not in
the repo and reading it is outside this task); what is proven is that the reference is stock, so it
is not a defect the clone introduced and no clone of ours should invent a different name for it.

## 4. The two real gaps, and the clone each needs

Both are tunes our own objects name, and neither is shipped, indexed, nor inside a container in its
own directory. Precedent in the build itself: the RC already ships one extracted explosion tune
loose, `Builds/bm-RC4/aaf/editor/entities/jc_explosions/vehicles/car_explosion_medium.ftunec`, and
`Tools/scripts/jc3emp.py` reads tunes as **inner records of an `.ee`**
(`jc3detail.inner_files(jc3grab.read_entry(...))`), not as archive paths — which is exactly why the
gate cannot find them by name.

| path | carrier | clone the merge must add | why |
|---|---|---|---|
| `editor/entities/jc_explosions/vehicles/truck_emp.ftune` | `CForcePulse_EMP` (`SettingsFile`) | `editor/entities/jc_explosions/vehicles/truck_emp.ftunec` | the EMP burst's own 8-number tune (MODLOG §“G2-16”: `EMP` on `truck_emp.ftune`, 100 player/AI damage in 25 m); the later EMP burst build keeps the pulse and keeps `truck_emp.ftunec` |
| `editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftune` | `CForcePulse_Sonar` (`SettingsFile`) | `editor/entities/jc_explosions/gen_explosion_5m_nodamage.ftunec` | the Sonar pulse's 0-damage tune; GRAB_BACKLOG plans it as “a `.ftunec` copied from `gen_explosion_5m_nodamage.ftune`” |

Neither clone exists today (`present_in_build False`, `present_in_index False`). Extraction must be
from the stock `.ee` that carries the record (the EMP truck for `truck_emp.ftunec`), into the paths
above, plus the `aaf/@files.xml` registration the build already uses for loose tune files.

## 5. What was changed in the gate copy (and what was not)

`Tools/scripts/v03_wiring_rc5.py` is `v03_wiring_rc4.py` verbatim except for three G3 changes, each
documented in the file header:

1. **the build is more than the `.ee`'s inner records** — the loose `aaf/` tree is searched too,
   because extracted stock records are shipped there;
2. **compiled-container rule (b)** — a name resolves when a container in its own directory exists
   (`<dir>/<dir>.ee`, `.wtunec`, `.etunec`, `.ftunec`, `.pfxc`, `.effc`, `.vmodc`);
3. **compiled-container rule (c)** — a name resolves when an indexed container's stem prefixes the
   record's own file name (`…_body.model_xml` → `w206_mounted_capstone_m2hm.ee`), longest stem
   wins, stems shorter than 8 characters ignored so the rule cannot match everything.

Nothing was excused by name, no path was whitelisted, and G1/G2/G4/G5 are byte-for-byte the RC4
logic: G2 still reports its four `F30CCB1C` values, G4/G5 still pass, and the gate still exits 1
because real gaps remain. The classifier and the gate share `resolve_path`, so they cannot drift.

## 6. Files written, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/v03_wiring_rc5.py` | new RC5 gate copy (G3 normalisation) | delete the file |
| `Tools/scripts/rc5_asset_refs.py` | new classifier, `--write`/`--check` | delete the file |
| `Builds/bm-RC5-entity/asset_refs.json` | generated: 6 rows, 3 normalised, 1 stock, 2 gaps | delete the file |
| `tmp/freebuff/rc5-verify/wiring.json`, `wiring.md` | RC5 gate run record | delete |
| `tmp/freebuff/reports/rc5-six-dangling-asset-paths.md` | this report | delete |

No build tree, `.ee`, `.toc`, card or game file was modified.

## 7. Limits and UNKNOWNs

* **Whether the stock APC resolves `rigid_object_effect_settings_default.etune` inside its own
  `.ee` is UNKNOWN** — that container is not in the repo and was not read.
* **The two clones' bytes are not in the repo**: the tool names the path and the stock owner, but
  extracting `truck_emp.ftunec` / `gen_explosion_5m_nodamage.ftunec` needs the stock `.ee`, which
  the RC5 merge step must do.
* **`INDEX.json`'s `by_extension` is unreliable for `.etunec`/`.ftunec`** (says 0 while the jsonl
  holds paths of both); the verdicts use the jsonl path and hash lookups instead.
* **Rule (c) is a naming heuristic**, not a decode: it proves the container leaf exists, not that
  the record is inside it. Eight-character floor and longest-stem preference keep it from matching
  `shared`, `vehicles` or `jc_explosions`.
* **G3's other tallies are unchanged**: ctune 17/17 and the rest still resolve; the six paths here
  are the whole of the G3 delta.

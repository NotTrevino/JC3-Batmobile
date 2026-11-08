# The last unnamed archive entry — named: `ara/mission_mm320_dial_gameplay_sams01.wavc`

**Result: NAMED.** `patch_win64/game4` hash **`016DE9D1`** (+618,637,312, 84,720 B) is
`sound/dialogue/ara/mission_mm320_dial_gameplay_sams01.wavc`. The proof is the archive's own
write order plus `hash_jenkins(path) == 016DE9D1`; both neighbours re-hash to their own records,
so the bracket rule is verified in place, not assumed.

**Provenance / reversibility.** New file,
`tmp/freebuff/reports/unnamed-wavc-016de9d1.md`
= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/unnamed-wavc-016de9d1.md`. Intended change: record
the last bounded naming attempt on the one archive entry `INDEX.json` could not name. It is the
correct file because it is the requested output path and the only job artefact besides the name
itself. **Revert:** delete this file, `Tools/names/derived_016de9d1.json`,
`Tools/names/jc3_mm320_sams01.filelist` and `Tools/scripts/g2_last_entry.py`, then re-run
`python Tools/scripts/jc3index.py build`.

---

## 1. The take's own bytes

Read from `D:/Games/Just Cause 3/patch_win64/game4.arc` at the tab record's offset.

| field | value | note |
|---|---|---|
| tab record | hash `016DE9D1` → `(618637312, 84720)` | `patch_win64/game4.tab`, 4,453 records |
| prefix | `u32 84704` = size − 16, then 12 zero bytes | the same 16-byte `.wavc` prefix every take has |
| magic | `FSB5` at +16 | after the prefix |
| FSB5 header | version **1**, `numSamples` **1**, `sampleHeaderSize` **60**, `nameTableSize` **40** | one-sample bank |
| sample header | **11,025 Hz**, **1 channel**, **243,648 samples**, mode **15** | **22.100 s**; data 84,544 B (84,720 − 16 − 60 − 60 − 40) |
| name table @136 | `u32 offset 4` then `"1606523576\0"` | the token, exactly as `Tools/names/README.md` recorded |
| other ASCII in the payload | only 4–6 byte compressed-audio runs | no path, no basename, no string lookup inside the take |

So the container is a **normal** Arabic dialogue take: 11.025 kHz mono, FSB5 v1 mode 15, 22.1 s.
Nothing in the payload names it — which is the whole problem the token route was meant to solve.

## 2. Its neighbours in the same archive

Physical order in `patch_win64/game4`, ascending offset (the `.arc` lays payloads down in ascending
VFS-path order):

| offset | size | hash | token | format | path |
|---:|---:|---|---|---|---|
| 618,434,560 | 31,472 | `8FEF9C80` | 257240667 | 11,025 Hz / 1 ch / 7.291 s | `…/ara/mission_mm320_dial_csa_050.wavc` |
| 618,467,328 | 82,640 | `4D4A1E63` | 179323138 | 11,025 Hz / 1 ch / 23.313 s | `…/ara/mission_mm320_dial_csa_060.wavc` |
| 618,551,296 | 40,752 | `E6EAC7BA` | 876847260 | 11,025 Hz / 1 ch / 11.238 s | `…/ara/mission_mm320_dial_csa_080.wavc` |
| 618,592,256 | 44,368 | `5567C6E5` | 1468515345 | 11,025 Hz / 1 ch / 12.660 s | `…/ara/mission_mm320_dial_gameplay_090.wavc` |
| **618,637,312** | **84,720** | **`016DE9D1`** | **1606523576** | **11,025 Hz / 1 ch / 22.100 s** | **`…/ara/mission_mm320_dial_gameplay_sams01.wavc`** ← named here |
| 618,723,328 | 141,040 | `CB7DBEA9` | a3000117 | 11,025 Hz / 1 ch / 33.379 s | `…/ara/mission_mm320_dial_gameplay_start05.wavc` |
| 618,864,640 | 22,224 | `6DDA516B` | a955204688 | 11,025 Hz / 1 ch / 6.889 s | `…/ara/mission_mm340_dial_csd_010.wavc` |

Two things this table settles that prose could not:

1. **Format:** every neighbour is 11,025 Hz mono — the take belongs to this Arabic set by its audio
   shape as well as by its offset. It is not a mis-filed English or music payload.
2. **Bracket:** the predecessor is `mission_mm320_dial_gameplay_090` and the successor is
   `mission_mm320_dial_gameplay_start05`, so the basename must sort strictly inside
   `"mission_mm320_dial_gameplay_090" < X < "mission_mm320_dial_gameplay_start05"`. Both neighbours
   re-hash to their own tab records (`5567C6E5`, `CB7DBEA9`), so the ordering premise is verified,
   not borrowed from the earlier pass.

## 3. The language-invariant token route — why it could not work here

The route that named the Polish take is: the FSB5 name-table token is **language-invariant**, so a
take with copies in several languages shares one token, and the unnamed copy borrows the named
copy's basename.

| test | result |
|---|---|
| named `.wavc` scanned (payload header + name table) | **31,001** |
| distinct tokens among them | **14,849** (1:1 with basenames) |
| tokens shared by more than one named file | **1,902** — the language copies |
| does any named `.wavc` carry token `1606523576`? | **NO** |
| `mm320` basenames with ≥2 language copies, tokens compared | **6 agree, 0 disagree** |

The invariance still holds (6/6), and that is exactly what dooms the route: **this take has no
sibling copy anywhere**, so there is no named file to borrow a basename from. It is a unique orphan.

**Why it has no sibling — the census explains it.** The Arabic directory carries only **5** `mm320`
takes (`csa_050`, `csa_060`, `csa_080`, `gameplay_090`, `gameplay_start05`); English carries **86**.
English ships `mission_mm320_dial_gameplay_sams02.wavc` and `…_sams03.wavc` and **no `sams01`**. So the
take is an Arabic-only recording of a line whose numbering skips 01 in every other language — a
perfectly ordinary localisation artefact, and precisely the shape that produces a unique-orphan token.

`mm320_main.stringlookup` (the only in-archive name source that lists this mission's takes) was
re-read for this pass: it names `gameplay_080/240/250/choppers01/02/05…` and **omits `_090` and every
`sams` take**, so it could not have named the record either. Eight `.stringlookup`/`.fl` files
mention `mm320`; none contains a take name inside the bracket.

## 4. Every candidate space tried in this pass

| # | sweep | paths | hits |
|---|---|---:|---:|
| 1 | numeric takes `0…9999`, widths 1–4, under the Arabic bracket | 37,153 | 0 |
| 2 | numeric takes, same space, across all 11 dialogue language dirs | 142,407 | 0 |
| 3 | 3-digit take + letter `a…z`, plus `start0..20`, `start0N`, `start_05`, `start5` | 783 | 0 |
| 4 | all **153** English `mm320` basenames × 11 language dirs | 1,683 | 0 |
| 5 | **take-suffix and word vocabulary** (11,591 distinct take suffixes + 796 word tokens from all 31,001 named dialogue takes, each also with `01…09`, `1…9`, `alt`, `_alt`) under the Arabic bracket | **514,994** | **1** |
| | **total this pass** | **697,020** | **1** |
| | previous pass (`MODLOG` G3g/G3h) | 243,341 | 0 |

Sweeps 1–4 are the numeric and known-basename spaces the earlier pass had already covered; they are
re-run here so the record is self-contained. **Sweep 5 is the space that was missing**: the Arabic
bracket is full of *word* takes, and a numeric/letter sweep cannot reach a word. The single hit:

```
sound/dialogue/ara/mission_mm320_dial_gameplay_sams01.wavc  ->  016DE9D1
```

It also passes the bracket test the hit had to pass anyway: `…_090` < `…_sams01` < `…_start05`
(`'a' < 't'` after the shared `…_gameplay_s`), and it lands at exactly the record's physical slot
between those two payloads.

## 5. What was written, and how it is checked

| artefact | content |
|---|---|
| `Tools/names/jc3_mm320_sams01.filelist` | the path plus the bracket and token evidence as comments — this is what `jc3index.py` consumes |
| `Tools/names/derived_016de9d1.json` | the evidence record: entry, container/FSB5 fields, bracket, token census, sweeps, verification |
| `Tools/scripts/g2_last_entry.py` | `--write` (regenerates the json/filelist) and `--check` (re-derives everything from the install) |

`python Tools/scripts/g2_last_entry.py --check` — **all 13 checks pass**:

```
PASS tab record  patch_win64/game4 016DE9D1 -> (618637312, 84720)
PASS 16-byte prefix  u32=84704
PASS FSB5 token  1606523576
PASS FSB5 sample header  11025 Hz / 1 ch / 243648 samples = 22.100 s
PASS hash_jenkins(candidate) == record  ...gameplay_sams01.wavc -> 016DE9D1
PASS predecessor  5567C6E5 @618592256
PASS successor  CB7DBEA9 @618723328
PASS candidate sorts inside the bracket
PASS neighbours hash to their own records
PASS index row present / offset+size / source derived-names
PASS evidence json
ALL CHECKS PASS
```

Sequencing note: the first `--write` run reported `FAIL index row present` **by design** — the index
had not been rebuilt yet. Order is: write the name list, `jc3index.py build`, then `--check`.

## 6. The G2 coverage figure, after the change

`python Tools/scripts/jc3index.py build` then `status_audit.py --write` (STATUS.md is generated, never
hand-edited):

| | before | after |
|---|---:|---:|
| archive entries named | 81,952 / 81,953 | **81,953 / 81,953** |
| coverage | 99.999 % | **100.000 %** |
| unnamed tab entries | 1 | **0** |
| derived-names rows | 90 | **91** |
| index check | `check ok`, 1 unnamed | `check ok: 81953 rows, 78908 paths, 0 unnamed entries, DLC 20682/20682 named` |

`STATUS.md:13` now reads `archive entries named | 81,953 / 81,953 | 100.000%`. Source mix:
`gibbed-filelist` 55,811, `jcmr-dictionary` 26,051, **`derived-names` 91**.

**G2 JC3 grab: 81,953 / 81,953 archive entries named = 100.000 %.** That is the whole archive, not a
sample: every tab record in 88 archives now resolves to a path, and every derived path is accepted by
`hash_jenkins(path) == tab hash`.

## 7. Limits

* This names the take's **file**, which is what G2 measures. It does not give the line's spoken
  content or speaker: no string table names `sams01`, and the token is FMOD's opaque source name, so
  the semantic title stays UNKNOWN (`mm320_main.stringlookup` omits the take entirely).
* `derived-names` provenance is weaker than a shipped filelist by construction; `INDEX.json` marks
  the row `"source": "derived-names"` and `jc3index.check` re-hashes it on every build.
* Read-only against the game install; no payload was written, patched or moved. `INDEX.json(l)`,
  `STATUS.md` and `Tools/names/README.md` are regenerated/updated by the normal pipeline.
* `GRAB_BACKLOG.md` and `Research/JC3Grab/README.md` still describe the 81,952 state (they are not
  regenerated by `status_audit.py`); the authoritative figure is `STATUS.md` / `INDEX.json`.

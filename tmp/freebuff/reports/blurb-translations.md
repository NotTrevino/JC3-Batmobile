# Rebel Drop blurb - proposed translations for the 10 non-English languages

STATUS: done. The English blurb is 111 characters under key `F34BA8E8`; the built store carries
that same English string in **11/11** lanes, which `Builds/bm-RC2/verify/strings_languages.md`
shows is abnormal (all 83 vanilla vehicle blurbs are translated in all 10 non-English lanes).
Ten machine-written proposals are written to `Working/Translation/BLURB_TRANSLATIONS.{md,json}`,
each labelled **"machine-written proposal, needs native review"**. Every proposal sits under the
**unchanged** key `F34BA8E8` and fits the **per-language vanilla maximum** character count. The
build was not touched: `Builds/bm-RC2/drop/profile/online.stringlookup` still hashes
`6dcdf0ce1af304b6a77ebcb319e53a59fcaafed6bf329ca2e9821483d3c60bc4` (the pin in `strings.md`) and
its mtime is 02:42, before this session.

## 1. The English source

> Arkham Knight's armoured Batmobile: pursuit speed, a battle-mode turret, and armour that shrugs off small arms.

- 111 chars, key `F34BA8E8` = `hash_jenkins("v0300_car_kensington_sportsmuscle_debug_desc")`
  (recomputed in the script); name key `60A5E7A4` = `hash_jenkins("v0300_car_kensington_sportsmuscle_debug")`.
- read from the built store, lane 0, `TextOffset` 1436124; the same text sits at 11 lane offsets
  (1436124, 1436236, ... 1437244, stride 112 = 111 chars + NUL).

## 2. Vanilla register (three blurbs, all 11 languages)

Quoted in full in `BLURB_TRANSLATIONS.md` §2, decoded from
`E:/Modding/_gamedata/JC3grab/strings_rt/online.stringlookup`:

| sample | leaf | key | en chars |
|---|---|---|---|
| sports car | `v0300_car_kensington_sportsmuscle_civilian_01` | `7B942DF2` | 156 |
| light assault tank | `v0603_car_urga_smalltank_rebel_01` | `C24EF295` | 143 |
| assault helicopter | `v2200_helicopter_capstone_assault_rebel_01` | `A0A08F3C` | 156 |

Each key is `hash_jenkins(<leaf> + "_desc")` recomputed by the script and printed in the
sample headings of the generated file.

Register, as observed in those 33 strings: one or two declarative third-person sentences, no
exclamation, make/model named first, capability listed with a colon or "and", and a concrete spec
at the end (76 mm turret, 64 Volcanus / 99 Vindicator missiles, 250 km/h). Non-English runs longer
in most languages (fr 210 vs en 156, de 189, it 206, ru 205, pl 185, ar 195); Japanese is far
shorter (82) and Spanish is level (165). The proposals follow that shape.

## 3. Proposals (all machine-written, needs native review)

| lang | max vanilla chars | proposal chars | proposal |
|---|---|---|---|
| `fr` | 237 | 133 | La Batmobile blindée d'Arkham Knight : vitesse de poursuite, une tourelle en mode combat et un blindage qui ignore les armes légères. |
| `de` | 228 | 152 | Das gepanzerte Batmobile von Arkham Knight: Verfolgungsgeschwindigkeit, ein Turm für den Kampfmodus und eine Panzerung, die Kleinwaffen abprallen lässt. |
| `it` | 217 | 149 | La Batmobile corazzata di Arkham Knight: velocità di inseguimento, una torretta in modalità combattimento e una corazza che respinge le armi leggere. |
| `es` | 194 | 138 | El Batmobile blindado de Arkham Knight: velocidad de persecución, una torreta en modo combate y un blindaje que resiste las armas ligeras. |
| `ru` | 221 | 134 | Бронированный Batmobile от Arkham Knight: скорость погони, турель в боевом режиме и броня, выдерживающая попадания стрелкового оружия. |
| `pl` | 242 | 111 | Opancerzony Batmobile Arkham Knight: prędkość pościgu, wieża w trybie bojowym i pancerz odporny na broń krótką. |
| `ja` | 92 | 60 | Arkham Knightの装甲Batmobile。追跡速度、バトルモードのターレット、小火器を寄せ付けない装甲を備える |
| `pt` | 197 | 142 | O Batmobile blindado de Arkham Knight: velocidade de perseguição, uma torreta em modo de combate e uma blindagem que resiste a armas ligeiras. |
| `es-MX` | 194 | 138 | El Batmobile blindado de Arkham Knight: velocidad de persecución, una torreta en modo combate y un blindaje que aguanta las armas ligeras. |
| `ar` | 223 | 112 | تتميز Batmobile المدرعة الخاصة بـArkham Knight بسرعة المطاردة، وبرج في وضع القتال، وتدريع يقاوم الأسلحة الخفيفة. |

`en` is repeated unchanged in the file so the row set covers all 11 lanes.

## 4. Key and length checks (recomputed by `--check`)

- **Key unchanged.** The store's `Hash` is `hash_jenkins(<leaf> + "_desc")`, a property of the
  leaf, not of the text; the text is bytes at a `TextOffset`. The script recomputes
  `F34BA8E8` and `60A5E7A4` from the leaf and asserts the blurb key is present in all 11 lanes of
  the built store, so a text swap cannot move a key. Vanilla does the same: one hash, 11 lane
  offsets.
- **Length.** Budget = the longest vanilla vehicle blurb **in that language**, over the 83 blurbs
  present in all 11 lanes: en 195, fr 237, de 228, it 217, es 194, ru 221, pl 242, ja 92, pt 197,
  es-MX 194, ar 223. Every proposal is under its budget (largest margin: ja 60/92; tightest:
  de 152/228).
- **Format.** No proposal contains a NUL (which would truncate the store's NUL-separated text
  blob); all are valid UTF-8.

## 5. Files written

- `Tools/scripts/blurb_translations.py` - `--write` / `--check`; the check re-reads both stores,
  recomputes the hashes, the budgets and the lengths, and rebuilds both documents byte for byte.
- `Working/Translation/BLURB_TRANSLATIONS.md` - the proposals, the three vanilla samples in all 11
  languages, the key/length tables, and the limits.
- `Working/Translation/BLURB_TRANSLATIONS.json` - the same as data, every row carrying
  `"label": "machine-written proposal, needs native review"`.
- this report.

Nothing under `Builds/` was written. Revert = delete the four files above.

## 6. Commands and output (verbatim, final run)

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/blurb_translations.py --write; echo "WRITE_EXIT=$?"
wrote Working\Translation\BLURB_TRANSLATIONS.md and BLURB_TRANSLATIONS.json
11 rows, 11/11 lanes still carrying the English string
WRITE_EXIT=0

$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/blurb_translations.py --check; echo "CHECK_EXIT=$?"
PASS English blurb read from the built store (111 chars)
PASS all 11 lanes still carry the same English string (the thing being fixed)
PASS blurb key = hash_jenkins(leaf_desc) = F34BA8E8
PASS name key = hash_jenkins(leaf) = 60A5E7A4
PASS the blurb key is present in all 11 lanes of the built store
PASS 83 vanilla blurbs set the budget
PASS the three vanilla samples resolve in all 11 languages
PASS one proposal per language lane
PASS every proposal sits under the unchanged key F34BA8E8
PASS every proposal fits the per-language vanilla maximum
PASS no proposal contains a NUL (would truncate the store's text blob)
PASS the en row is the shipped English string, unchanged
PASS every row carries the machine-written label
PASS Working\Translation\BLURB_TRANSLATIONS.md re-derives byte for byte
PASS BLURB_TRANSLATIONS.json re-derives byte for byte
PASS: blurb translations 0 failure(s)
CHECK_EXIT=0
```

A first `--check` run failed one assertion because the English string is 111 characters, not the
112 I had assumed from the 112-byte lane stride (111 chars + NUL); the assertion was corrected to
the measured value and the run above is the repaired one. No build, game or install script was run.

## 7. UNKNOWNs

1. **Whether these read naturally to a native speaker.** No file can answer that; the proposals
   match the decoded vanilla register and length only. This is why every row is labelled.
2. **Whether `Batmobile` / `Arkham Knight` should be transliterated.** Vanilla prose keeps
   `Kerner`, `Capstone`, `Urga` in Latin script, so the proposals do too; the name pair is
   `BATMOBILE` in all 11 lanes, so no file records a localisation decision for the proper noun.
3. **Grammatical gender of "Batmobile"** (`La Batmobile`, `Das Batmobile`) - no vanilla string
   names a Batmobile, so there is no in-file oracle; common usage was followed.
4. **Whether "battle mode" is a term the localisation team would keep in English.** The BmAK
   source calls it `BattleMode` (`HUD_SPEC.json` `mode_strings`), but no JC3 string carries the
   term, so the proposals translate it descriptively.
5. **Whether the engine enforces any length limit.** None is decoded; the budget used here is the
   vanilla maximum, not an engine cap. The store's text blob is offset-based, so a longer string
   would still fit the format.

STATUS: done

The vanilla vehicle blurbs in `profile/online.stringlookup` are genuinely translated, not English
in every language. Of the **83** vehicle blurb keys (`hash_jenkins(<leaf> + "_desc")`) that exist
in all 11 languages, **83/83** differ from the English text in **each** of the 10 non-English
languages; **0** are English-only. Item descriptions behave the same: **105/105** different in
every non-English language, 0 English-only. English-in-every-language is **not** normal for prose
in this store: of the 185 English-only keys in the 11-language intersection, **0** are
sentence-like and **0** are item descriptions; all 185 are proper names (182 examples include
vehicle/weapon names such as `STRIA CARERA G`).

The build's new blurb `F34BA8E8` is indeed the same English sentence in all 11 languages, so it
does **not** match the vanilla pattern: it is a compromise, not normal. The new name `60A5E7A4`
("BATMOBILE") is also English in all 11, which *is* normal for a proper name.

Per-language counts (different from English, over keys present in all 11 languages):

| language | vehicle blurbs | vehicle names | item descriptions | all 11-language pairs |
|---|---:|---:|---:|---:|
| fr | 83/83 | 26/133 | 105/105 | 1041/1275 |
| de | 83/83 | 22/133 | 105/105 | 1057/1275 |
| it | 83/83 | 24/133 | 105/105 | 1065/1275 |
| es | 83/83 | 26/133 | 105/105 | 1056/1275 |
| ru | 83/83 | 22/133 | 105/105 | 1067/1275 |
| pl | 83/83 | 27/133 | 105/105 | 1050/1275 |
| ja | 83/83 | 7/133 | 105/105 | 1038/1275 |
| pt | 83/83 | 25/133 | 105/105 | 1059/1275 |
| es-MX | 83/83 | 26/133 | 105/105 | 1056/1275 |
| ar | 83/83 | 22/133 | 105/105 | 1066/1275 |

Newly added items: the index lists 51 vehicle leaves whose `.ee` rows live only on the `dlc`
mount; **none** of them has a `<leaf>_desc` pair in `profile/online.stringlookup` in any language,
so this store carries no DLC vehicle blurbs and cannot show how those were localized (see
UNKNOWNs).

## Files written

* `Tools/scripts/v_strings_languages.py` (new; `--write` / `--check`)
* `Builds/bm-RC2/verify/strings_languages.md` (new, generated)
* `tmp/freebuff/reports/strings-languages.md` (this report)

No other file was modified. Read-only inputs: the vanilla store, the built store, `item.onlinec`
and `Research/JC3Grab/INDEX.jsonl`.

## Commands and output (verbatim)

```
$ python Tools/scripts/v_strings_languages.py --write
wrote Builds/bm-RC2/verify/strings_languages.md
$ python Tools/scripts/v_strings_languages.py --check
PASS: vehicle blurbs 83/83 translated in every language (english-only 0), item descriptions 105/105, all-pair english-only 185/1275 (0 prose), new blurb english-in-11 True, DLC blurbs present 0/51
exit=0
```

Exploratory reads (same numbers; the generator recomputes them from the source bytes):

```
lanes 11 [1385, 1307, 1301, 1310, 1318, 1370, 1329, 1385, 1307, 1320, 1380]
keys in all 11: 1275
fr diff 1041 same 234
de diff 1057 same 218
it diff 1065 same 210
es diff 1056 same 219
ru diff 1067 same 208
pl diff 1050 same 225
ja diff 1038 same 237
pt diff 1059 same 216
es-MX diff 1056 same 219
ar diff 1066 same 209
english-only keys: 185
v leaves: 284
blurb keys all11: 83 name keys all11: 133
== blurb
fr 83; de 83; it 83; es 83; ru 83; pl 83; ja 83; pt 83; es-MX 83; ar 83;
english-only 0
== name
fr 26; de 22; it 24; es 26; ru 22; pl 27; ja 7; pt 25; es-MX 26; ar 22;
english-only 102
...
mounts of v .ee rows Counter({'base': 232, 'dlc': 77, 'patch': 1})
('base',) leaves 232 blurbs 83 english-only 0
('dlc',) leaves 51 blurbs 0 english-only 0
('patch',) leaves 1 blurbs 0 english-only 0
english-only total 185
english-only sentence-like 0
items 197 desc hashes 111 in all11 105
fr 105; de 105; it 105; es 105; ru 105; pl 105; ja 105; pt 105; es-MX 105; ar 105;
english-only intersect item descs 0 names 125
en dlc blurbs present 0 of 51
```

## How the counts were made

* `profile/online.stringlookup` decodes as `Languages[N].SortedPairs[].{Hash,TextOffset}` into one
  NUL-separated `Text` blob (the same decode as `Research/JC3Grab/NAMES.md`). 11 lanes; lane 0 is
  English; lanes 1-10 are `fr, de, it, es, ru, pl, ja, pt, es-MX, ar` (inferred from text, as
  NAMES.md records).
* Vehicle leaves are all `v*` `.ee` leaves under `editor/entities/jc_vehicles/` in
  `Research/JC3Grab/INDEX.jsonl` (284). Blurb key = `hash_jenkins(leaf + "_desc")`; name key =
  `hash_jenkins(leaf)`. This rule is proven on the Serpente donor in `NAMES.md`
  (`D2B46B49` / `7B942DF2`).
* Only keys present in all 11 lanes are counted; text is compared as the exact decoded string.
* Item descriptions are the low 32 bits of `Items[].UIDescription` in
  `Builds/bm-RC2/drop/profile/item.onlinec` (111 distinct hashes, 105 present in all 11).

## UNKNOWNs

* **Where DLC vehicle blurbs live.** 51 DLC-only vehicle leaves have no `_desc` pair in
  `profile/online.stringlookup` in any language. I did not decode a DLC-side `.stringlookup` or
  another store, so how those blurbs were localized is UNKNOWN.
* **Whether any genuinely added item ever shipped English-only.** The only added items in this
  store are the build's two pairs; no vanilla 11-language blurb or item description is
  English-only, so there is no vanilla example to compare against. DLC-side stores would have to
  be decoded to settle it.
* **Language identity field.** The store carries no language-name enum; the order is inferred from
  the text (English first), not decoded from a field.

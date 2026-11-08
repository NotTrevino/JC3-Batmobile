# Independent review — G1-15 · Audio by feature, decoded to WAV

Reviewer: Buffy (did not write this card). Date: 2026-10-29. Read-only: the only file written is
this report. No game launch, no commit, no edit to `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file. (`write_md()` was called with its output path redirected to the OS temp
dir, to test whether the shipped `.md` still matches the `.json`; nothing under `Research/` changed.)

**Change record (AGENTS.md).** Intended change: create this one review file. File:
`tmp/freebuff/reports/review-G1-15.md`. Why this file: the review was asked to land exactly here.
Revert: delete `tmp/freebuff/reports/review-G1-15.md`.

**Scope reviewed:** `GRAB_BACKLOG.md` §0.5 (R1–R14), the G1-15 card (`GRAB_BACKLOG.md:485-495`), the
G1-15 §12 row (`GRAB_BACKLOG.md:1283`); `MODLOG.md:8310-8386` (intended + done); the outputs
`Research/BatmobileGrab/AUDIO_FEATURES.md` (776 lines, 90,994 B),
`Research/BatmobileGrab/AUDIO_FEATURES.json` (2,081,094 B),
`Tools/scripts/bmak_audio_features.py` (815 lines); the inputs it reads
(`Research/BatmobileGrab/AUDIO_MAP.json`, the `AkBank` exports, `Working/Audio/`) and the 423 WAVs it
wrote outside the repo under `E:\Modding\_BmAKgrab\audio\wav\`.

---

## VERDICT: **minor issues**

The card's substance holds up. Every sampled value re-derives: a WAV's LUFS/peak/duration recompute
to the printed digits, the RTPC curves in the doc match the JSON, the 361/118/447/90/27 counts match
the declared input `AUDIO_MAP.json`, the shipped `.md` rebuilds **byte-identically** from the `.json`
in memory (`identical: True`), and both `Out` paths exist with the 423 WAVs on disk at 48 kHz.

What is wrong is (a) prose that contradicts the very table below it, (b) a `--check` that validates
the *shape* of the stored JSON rather than re-deriving it, and (c) two reporting losses (silent
5-point curve truncation, a double-counted WEM column). None of these requires the card to be redone;
all are generator fixes.

The single false statement that matters downstream is the MODLOG's "the 24 streamed rows are all
voice lines" — 8 of the 24 are engine media, and T-16 already depends on this file for its engine
sources.

## Check output (verbatim)

Command, from `E:/Modding/JC3-Batmobile`, exit status `0`:

```
$ python Tools/scripts/bmak_audio_features.py --check
{
 "rows": 361,
 "unique_event_ids": 118,
 "groups_used": 14,
 "media": 447,
 "decoded": 423,
 "decode_errors": 24,
 "missing_rows": 90,
 "banks": 27,
 "rtpc_objects": 261,
 "rtpc_entries": 506,
 "rtpc_params_distinct": 41,
 "rtpc_params_named": 22,
 "duration_total_s": 971.4
}
OK: 361 rows / 118 ids -> 14 groups, 423/447 WEMs decoded (24 errors), 90 missing rows, 27 banks, 506 RTPC entries over 261 objects (22 named params)
```

The `OK` line is exactly what `MODLOG.md:8331-8333` quotes; the MODLOG omits the JSON block the
command prints first, which is cosmetic.

## Out paths and Done criterion

| path (card `Out` / §12) | exists | size / state |
|---|---|---|
| `Research/BatmobileGrab/AUDIO_FEATURES.md` | yes | 90,994 B, 776 lines |
| `Research/BatmobileGrab/AUDIO_FEATURES.json` | yes | 2,081,094 B |
| WAVs outside the repo (`E:\Modding\_BmAKgrab\audio\wav\`) | yes | 423 `.wav`, all 48 kHz (`--check` asserts rate + existence) |
| `Tools/scripts/bmak_audio_features.py` | yes | 815 lines (extra; §12 names it implicitly through `--check`) |

Card `Done` (`GRAB_BACKLOG.md:495`): *"every one of the 361 events is in exactly one feature group (or
`other`); 447/447 WEMs decoded or listed with the decode error; the 90 `missing-bank` rows stay
explicit."*

What `--check` actually verifies (`bmak_audio_features.py:729-775`): `rows == 361`,
`unique_event_ids == 118`, `media == 447`, `decoded + decode_errors == 447`, `missing_rows == 90`,
`banks == 27`, every `group` is one of the 17 rule-list names, no `(package, name)` row appears
twice, `rtpc_entries != 0`, at least two RTPC parameters resolve to a name, every media WAV exists and
is 48 kHz, every decode error carries a message.

That is a fair reading of the three `Done` clauses, with two caveats:

* "in exactly one feature group" is only checked as *membership in the allowed list* — there is one
  `group` field per row, so "exactly one" is structural, and a **wrong** group still passes;
* "447/447 decoded or listed" is checked as an arithmetic identity on the summary
  (`decoded + errors == 447`), not as "each of the 447 row WEMs is in exactly one of the two lists".

Both caveats are exercised in issue 1 below.

---

## Issues

### 1. Moderate — `--check` cannot see a wrong value; it validates the JSON's shape (R11 evidence quality)

`check(doc)` (`bmak_audio_features.py:729`) is handed the **stored** JSON; nothing is re-decoded and
the MD is never compared. Six in-memory tampers against a loaded copy of the shipped JSON (no file
touched):

| tamper | rc | what `--check` said |
|---|---|---|
| a media row's `lufs` → −99.0 | **0** | `OK: … 423/447 WEMs decoded …` |
| a row regrouped to `sonar` | **0** | `OK: …` |
| a row's `wems` emptied | **0** | `OK: …` |
| `decoded` 424 / `decode_errors` 23 (sum still 447) | **0** | `OK: … 424/447 WEMs decoded (23 errors) …` |
| `rtpc_entries` 1 | **0** | `OK: … 1 RTPC entries …` |
| a media `wav` path that does not exist | 1 | `FAIL - WAV missing on disk: …` |

So a re-measured loudness, a mis-grouped row, a row that lost all its media, or a 500-fold RTPC
regression are all green — the `506` and `261` in the `OK` line are **printed from the summary**, not
asserted. The script's own usage line is honest about it (`--check # Done-when gate (reads the
JSON)`, line 32), but the card's Done reads as a re-derivation and the MODLOG calls the files
"re-derived by the new script". Fix: assert what is cheap and real — `{media wems} ∪ {error wems} ==
{row wems}` with no overlap (it already holds 423 + 24 = 447), `rtpc_entries == Σ per-row bindings`,
and `open(MD).read() == write_md(doc)` (the file is generated, so this is free).

### 2. Moderate — the generated header states the opposite of the table below it (R4, R11)

`Research/BatmobileGrab/AUDIO_FEATURES.md:5-7`:

```
rows lands in exactly one feature group; every one of the 447 media ids is decoded to a
48 kHz WAV under `E:\Modding\_BmAKgrab\audio\wav` (outside the repo) and measured.
```

Its own summary says `decoded 423`, `decode_errors 24`, and the file lists the 24 undecoded ids at
`:694-718`. The sentence is typed in `write_md` (`bmak_audio_features.py:638-643`) with the literal
`447` (and `361` on the previous line), so `--check` re-renders it unchanged and can never catch it —
exactly the R11 failure mode. Fix: build the sentence from `s["rows"]`, `s["media"]`, `s["decoded"]`,
`s["decode_errors"]` ("423 of 447 … the other 24 listed with their error").

### 3. Moderate — "the 24 streamed rows are all voice lines" is false; 8 are engine media

`MODLOG.md:8348-8352`: *"the 24 streamed rows are all voice lines whose banks ship `HIRC`+`STID`
only"*. The file's own `decode_errors`:

```
error banks: {'DLG_MAIN_CH10_S05_JOKER_A1_WAREHOUSE_TWO_FACE_GORDON_OUTRO': 5, 'BML_Engine': 4,
 'VEH_Batmobile_MK2_Engine': 4, 'DLG_MAIN_CH10_S08_GOTHAM_ALF_PLEAD': 3,
 'DLG_MAIN_CH10_S05_JOKER_A1_WAREHOUSE_INTRO_CONVERSATION': 3,
 'DLG_MAIN_CH10_S05_JOKER_A1_WAREHOUSE_TWO_FACE_STAND': 1,
 'DLG_MAIN_CH03_S24_CITYX_PT3_CALLCAR': 1, 'DLG_CHAR_BATMAN_MISC_COBRA_BARRAGE_ENERGY': 1,
 'DLG_CHAR_BATMAN_MISC_COBRA_BARRAGE': 1, 'DLG_CHAR_BATMAN_MISC_COBRA_BARRAGE_ENERGY_B': 1}
```

16 voice + **8 engine**. The engine ids belong to `Play_Batmobile_Positional` (2),
`Play_Batmobile_Engine_Transition_In/Out` (2), `Play_Batmobile_Reverse` (2) in `BML_Engine`, and
`Play_Batmobile_MK2_Engine_Transition_In/Out` + `MK2_Positional` (4) in `VEH_Batmobile_MK2_Engine`.
The doc's error table is correct (it prints the `BML_Engine` rows); only the MODLOG's sentence is
wrong, and it is the sentence a later card would trust. This is not academic: T-16's A-01 row lists
`Play_Batmobile_Engine_Transition_In (53 WEMs)` while only 51 have media, because 2 of the 53 are
these undecoded ones. Fix: restate as "16 voice + 8 engine layers; the engine ones are the only part
of the engine bed with no bytes on disk", and carry that into the doc's Gaps.

### 4. Minor — RTPC curves are silently cut to five points

`write_md` prints `es[0]["points"][:5]` (`bmak_audio_features.py:684-686`). Measured distribution of
bindings by point count: `{2: 1118, 3: 1228, 4: 603, 5: 248, 6: 127, 7: 4}` — **131 bindings have six
or seven points** and are shown as five, with no ellipsis or count. Example: `AUDIO_FEATURES.md:227`
shows `BML_Steering: -1->0 -0.2->0 -0.02->-1 0.02->-1 0.2->-0.006289` for
`Play_Batmobile_Steering_Bed`, whose curve actually has a seventh point `1.0 -> 0.0`. Fix: print all
points or append `(+N)`.

### 5. Minor — typed numbers in generated prose (R11)

Three places, all reproducible but none derived:

* `AUDIO_FEATURES.md:5-7` — `361`, `447` (see issue 2);
* `AUDIO_FEATURES.md:775` — "90 rows sit in the 10 banks that are not shipped on disk"; the JSON has
  `missing_rows 90` and `len(missing) == 10`, so both are derivable (`bmak_audio_features.py:718`);
* the decode-error message itself types "no DIDX entry in any of the **14** bank files searched"
  (`:713`), which nothing counts.

### 6. Minor — the group table's WEM column double counts

The `## Feature groups` table (`AUDIO_FEATURES.md:53-70`) sums to **481** WEMs against
`summary.media = 447`. That is correct data, not an arithmetic error: 34 media carry two groups
(`groups per media: {1: 389, 2: 34}`), because one WEM is reached by events in two feature groups. The
table does not say so, so a reader who adds the column gets 481 ≠ 447. Fix: a footnote ("a WEM
reached by two features appears in both rows; 34 do") and ideally a distinct-WEM column.

### 7. Minor — a `Stop_` row names itself as its own loop counterpart

`AUDIO_FEATURES.md:57-60`: `Play_BML_Sonar_Rumble_Lp` → `Stop_BML_Sonar_Rumble_Lp (Lp)` (useful), and
`Stop_BML_Sonar_Rumble_Lp` → `Stop_BML_Sonar_Rumble_Lp (Lp)` (self-referential, carries no
information). `write_md` prints `r0["loop"].get("stop_event")` for every row regardless of whether
the row *is* that stop event. Fix: blank the cell when `r0["name"] == stop_event`, or print
`is the stop`.

### 8. Minor — the `bytes` column is the WEM's size, not the WAV's

`AUDIO_FEATURES.md:270`: `0F897F3B.wav | … | 90341 | 23.483 | …`, but the file on disk is
**4,508,852 B** (`os.path.getsize`). `bytes` is the compressed media size from `AUDIO_MAP.json`
(correct provenance, wrong-looking header next to a WAV filename). Fix: rename the column
(`WEM bytes`) or add the WAV size.

### Not an issue (checked, sound)

* **R5 / member-name vs behaviour.** Grouping is by event name (`RULES`, `bmak_audio_features.py:75-93`)
  and the card asks exactly that, but the doc never upgrades a name into a claim: loop evidence is
  the `Stop_` counterpart, the name tokens and vgmstream's own loop lines, explicitly "recorded,
  never inferred" (`:767-770`); curve `y` values are printed raw with no interpretation; "horn stays
  empty" is stated as *no event ships*, not as *the car has no horn*.
* **R4.** The three deliberate absences (`winch`, `emp`, `horn` = 0 rows) carry notes with the reason;
  the 90 `missing-bank` rows stay explicit per bank; the unnamed RTPC ids keep `param: null` and the
  Gaps say why.
* **Derivation.** Summary, group table, per-event tables and the media table are all rendered from the
  JSON, and the shipped MD rebuilds byte-identically (`identical: True`, 776 lines).
* **Card wording.** The card's Done says "361 events"; the data is 361 `(package, event)` **rows**
  over 118 unique event ids, and both the doc (`:12-13`) and `--check` report both numbers, so the
  card's loose word does not hide anything.

---

## Spot-checks

Each checked against the JSON and then against the raw data the script reads, not against the doc.

| # | doc value | verified where | result |
|---|---|---|---|
| 1 | `0F897F3B.wav`: 23.483 s, peak −3.71 dBFS, **LUFS −12.59**, 48 kHz, 2 ch (`AUDIO_FEATURES.md:270`) | re-read the WAV with `scipy.io.wavfile` (1,127,202 frames @ 48 kHz = 23.483 s) and re-ran `bmak_audio_features.integrated_lufs` / peak formula → **−12.59**, **−3.71** | match |
| 2 | `BML_Steering: -1->200 0->-200 1->200` on `Play_Batmobile_CornerSqueal` (`AUDIO_FEATURES.md`, burnout section; quoted in `MODLOG.md:8345`) | JSON row `Play_Batmobile_CornerSqueal` → `rtpc[param=BML_Steering].points = [[-1.0, 200.0, 4], [0.0, -200.0, 4], [1.0, 200.0, 4]]`, `curve_id 0x044E2CE9` | match (and `Drift 0->0, 50000->-1` likewise, 6 rows) |
| 3 | 361 rows / 118 unique ids / 447 media / 90 missing rows / 27 banks | `AUDIO_MAP.json` `summary`: `rows 361, unique_event_ids 118, media 447, missing_rows 90, banks 27, media_entries 508, streamed_rows 24` | match |
| 4 | 423 WAVs, all 48 kHz, on disk | `os.listdir(E:\Modding\_BmAKgrab\audio\wav)` → 423 `.wav`; JSON `media` 423 rows, 423 distinct WEMs, all `sample_rate 48000`, all `source: embedded` | match |
| 5 | the 24 decode errors are listed with their error | `AUDIO_FEATURES.md:694-718` 24 rows, each `RuntimeError: streamed media: no DIDX entry …`; JSON `decode_errors` 24, all with a message | match on the listing — **but not "all voice"** (issue 3) |
| 6 | `duration_total_s 971.4` | Σ `media[].duration_s` = 971.43 | match |
| 7 | shipped MD == generator output | `write_md()` re-run with `MD_OUT` redirected to the temp dir → 776 lines, `identical: True` | match |

## What would clear it

1. Issue 1: add the three cheap real assertions (`media ∪ errors == row WEMs`, no overlap;
   `rtpc_entries == Σ row bindings`; `MD == write_md(JSON)`), so the gate can fail on a wrong value.
2. Issue 2 and 5: format the header sentence and the Gaps line from `summary`/`missing`, no literals.
3. Issue 3: correct the MODLOG sentence and add the "16 voice + 8 engine" split to the doc's Gaps —
   the engine half is the part T-16 cannot measure.
4. Issues 4, 6, 7, 8: render all curve points, note the WEM double count, drop the self-referential
   `Stop_` cell, rename the `bytes` column.

## Limits of this review

- Read-only: I did **not** run `--write` (it rewrites `Research/` and re-decodes 447 WEMs), so the
  decode path itself is reviewed by reading, not by re-running. The measurement path was exercised
  by re-measuring a shipped WAV with the same functions.
- I did not re-parse the `.pck`/`.bnk` exports to re-derive the 506 RTPC bindings; spot-check 2 checks
  the values that came out of that parse, not the parse.
- No game launched, so nothing here says whether any event is audible in game.
- The in-memory tamper table calls `check()` directly; it does not modify the shipped JSON (verified:
  the file's mtime/size are unchanged and `--check` still returns 0 afterwards).

## Files touched by this review

`tmp/freebuff/reports/review-G1-15.md` (this file) and one throw-away `g115_rebuild.md` written to the
OS temp directory by the redirected `write_md()` call. Nothing else.

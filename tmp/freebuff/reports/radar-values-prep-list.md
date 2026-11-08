# Radar values prep list — completion note

Card: 8826-radar-values-prep-list. 2026-11-08.

**What was asked.** Read `tmp/freebuff/reports/hud-radar-bmak-values.md`, collect every numeric radar
value it lists, create `Working/Prep` if absent, write `Working/Prep/radar-values.md` with one row per
value (name, value, unit, source line), mark any value with no stated unit UNKNOWN, write nothing
outside `Working/Prep` and `reports/`, and leave this completion note.

## Result

| item | outcome |
|---|---|
| source read | `tmp/freebuff/reports/hud-radar-bmak-values.md`, 130 lines, all 31 numbered lines inspected |
| folder `Working/Prep` | **already existed** — it held `count_eject_steps.py` (2,342 B). Nothing was created, nothing in it was touched except the new page. |
| output written | **`Working/Prep/radar-values.md`** — 31 rows |
| rows with value + unit | **15** |
| rows marked UNKNOWN | **5** (range/radius, blip size, fade time, pulse period, refresh rate) |
| census-count rows | **11** |
| excluded as provenance | 6 groups (byte sizes, SHA, AS3/`hud.as` line numbers, RECT words, tag bytes, doc bookkeeping), each with a reason |
| files outside `Working/Prep` + `reports/` | **none written** |
| this note | `tmp/freebuff/reports/radar-values-prep-list.md` |

## What the collection shows

- **The two values most likely to be wanted do not exist in the source.** *Range* is UNKNOWN because
  no metre/radius constant is in the AS3 or in `HUD.json`/`RADAR.json` (`:17`, `:31`, `:109-110`);
  *fade time* is UNKNOWN because the word "fade" appears **0** times in the file — a verified
  absence, not an assumed one (`grep -ic fade` → 0).
- **Blip size is also UNKNOWN**, and for a stated reason: 113 `DefineSprite` carriers exist but none is
  measured (`:33`, `:114`).
- **What does exist is a scale and a clock**: 80 px per distance unit (`:30`), the ×57.3 rad→deg
  factor (`:83`), a 1024×720 @ 30 fps stage (`:16`, `:34`), 40 frames (`:104`), and a debug divisor of
  400 (`:32`).
- **Every value carries a line citation.** The single row without a line (fade) records the command
  that proves the absence, so a reader can re-run it.

## Change record and revert

1. **Intended change:** add one prep page of radar values and this completion note.
2. **Files:** `Working/Prep/radar-values.md` (new) and this note. `Working/Prep` was not created — it
   already existed.
3. **Why those paths:** the card names `Working/Prep/radar-values.md` and `reports/…`; the two-write
   scope is exactly what the card permits.
4. **Revert:** delete `Working/Prep/radar-values.md` and this note. Nothing else changed; no source
   document was edited, and no game, build or archive file was read or written.

## Checks run

| check | result |
|---|---|
| source opened and all numbered lines read | yes — 130 lines, `grep -nE "[0-9]"` |
| `Working/Prep` existence tested before writing | yes — present, listing confirmed |
| "fade" absence verified | `grep -ic "fade"` → **0** |
| range/radius absence verified | source states it 4 times (`:17`, `:31`, `:86`, `:109-110`); quoted, not inferred |
| every row has a source line | 30 of 31; the 31st is the verified absence (no line exists) |
| files written outside the two permitted areas | **0** |
| game launched / anything built | **no** — file reads and two writes only |

## Limits

- The page reports what `hud-radar-bmak-values.md` says, not what the radar movie contains. Where that
  file says UNKNOWN, this page says UNKNOWN rather than re-deriving the value from the AS3.
- The exclusion list in §4 is a judgement about what counts as a "radar value". It is written down
  with reasons so it can be overturned without re-reading the source.


## smart_search — deferred (chase_candidates not done) (2026-10-29)

**Not started.** This card's prerequisite is `tmp/freebuff/reports/chase-candidates.md` existing with
`STATUS: done`. It does not exist (`ls` says so, `ls tmp/freebuff/reports/ | grep -i chase` is empty,
and no MODLOG line names it), so the single-member mode, `smart_search.py`, the calibration set and the
scores were **not** attempted. `Tools/scripts/chase/chase_candidates.py` (443 lines) and
`chase_judge.py` (100 lines) are on disk and `E:\Modding\_BmAKgrab\chase\` holds the earlier chase
outputs, so the missing piece is the chase-candidates report, not the code.

**What was written instead:** `tmp/freebuff/reports/smart-search.md` with
`STATUS: deferred (chase_candidates not done)`, the evidence above, and the input table that shows
everything else the card needs is present.

**Not touched:** `chase_candidates.py`, `chase_judge.py`, `FOOTAGE.md`, the chase files,
`GRAB_BACKLOG.md`, `D:/Games`, `E:/Games`; nothing launched, nothing committed, no secret read.

**Revert:** delete this section and the deferred report; no other change was made.

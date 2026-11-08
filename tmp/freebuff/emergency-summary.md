# Emergency summary 2026-11-05/06
Lanes ran 3 x 60 min waves at 03:00Z, 04:02-04:05Z (daily hours 14 -> 11 -> 8 -> 5 -> 2 -> 0 expected). See skills/freebuff/EMERGENCY_MODE_REPORT.md for hiccups, fixes and the next-run checklist.
Key findings (details in GRAB_BACKLOG.md section 12): bm-RC2 has no turret/cannon joints (cause: B-04 manifest + generator; fixed in the new private tree Builds/bm-RC3-parts BUT the two
constraint objects must still be appended to the physicsc); Rollback091 in Builds/bm-RC2/install.ps1 deletes files on a dropzone that already holds the build (install_v3 fixes it, operator
decision to adopt); T-L17 light colour wrong; 4 translation rows need an operator decision (Working/Translation/DECISIONS_NEEDED.md); new car blurb is English-only (proposals in BLURB_TRANSLATIONS).

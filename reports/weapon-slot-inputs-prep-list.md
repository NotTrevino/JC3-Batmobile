# Weapon slot build — input list: completion note

**Status:** done. 2026-11-08.

**Deliverable:** `Working/Prep/weapon-slot-inputs.md` (created; `Working/Prep/` already existed with
`count_eject_steps.py`, left untouched).

**Sources read only:**
- `tmp/freebuff/reports/four-weapon-slot-build-plan.md`
- `tmp/freebuff/reports/ammo-types-and-reload-plan.md`

Both plans are unchanged: neither was opened for writing, no tool call targeted their paths. Their
mtimes still read 2026-11-07 18:52 and 2026-11-06 09:34 respectively.

**What the list contains:** 62 input rows in four groups — slot/entity (20), weapon identity/carrier/
HUD (17), ammunition/reload/fire-rate/damage/heat (25), plus 4 non-input carrier gaps. Every supplied
value carries the file and line it was re-read from; 7 rows are UNKNOWN, each naming the file or probe
that would settle it. Examples of the core inputs: slot count 4 (`T-WP13b.md:32-37`), usable fire
paths 2 (`INPUT.json:481-496`), ammo capacity absent on the donor and `magazine_size -1` on the JC3
side (`Research/BatmobileGrab/WEAPONS.md:553-574`, `Research/JC3Grab/WEAPONS.md:764`), reload time is
UNKNOWN because only `reload_time_scale` exists (`Research/JC3Grab/WEAPONS.md:880`), and the weapon
names are `Batmobile_Heavy_Cannon_Primary` / `Batmobile_Cannon_V2` / `Batmobile_Missile_Launcher` /
`Batmobile_EMP_Burst` with tunes `w602` / `w603` / `w618`.

**Method / limits:** values were re-read in the cited files; the plans were used only to enumerate
what the build needs. No decode, no build, no game launch. No value was inferred from the plans
themselves where the underlying file could be opened. Line numbers are current to this tree.

**Files written:**
- `Working/Prep/weapon-slot-inputs.md` — the list (revert: delete).
- `reports/weapon-slot-inputs-prep-list.md` — this note (revert: delete).
- `tmp/freebuff/reports/weapon-slot-inputs-prep-list.md` — required mirror of this note.

**Checks run:** both written files exist and are non-empty; 10 sampled `file:line` citations were
re-opened and matched (slot table, spares, fire actions, HUD clip count, magazine/reload ranges,
tune rows, heat and reload fields). No source plan was modified.

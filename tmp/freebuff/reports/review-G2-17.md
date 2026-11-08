# Independent review — G2-17 · `CForcePulse`

Reviewer: independent read-only pass (did not write the card). Date 2026-10-28.
Card: `GRAB_BACKLOG.md:663` (`G2-17 · CForcePulse`, S, deps P0-2, serves WPN-5/8, MOD-1).
Tracker row: `GRAB_BACKLOG.md:1300` (`G2-17 | done`). Journal: `MODLOG.md:9987` (intended
change), `MODLOG.md:10143` (`done`).
Outputs reviewed: `Research/JC3Grab/FORCEPULSE.md` (293 lines), `Research/JC3Grab/FORCEPULSE.json`
(761,684 B), `Tools/scripts/jc3forcepulse.py` (797 lines).

## VERDICT: minor issues

The card is genuinely done: members, fleet ranges and a stated trigger (with the residual parts
recorded as UNKNOWN) are all present, every number is produced by the script, the Done check
passes, and the two refutations (horn, collision) are measurement-backed. What is wrong is
narrative arithmetic in §4.2 and one mislabelled row in §2 — the doc's own owner table contradicts
two of its sentences. No output path is missing and no claim I spot-checked against the data is
false.

## Check output (verbatim)

Command: `python Tools/scripts/jc3forcepulse.py --check`

```
PASS: 307 pulses / 232 entities / 79 chassis, 31 members, 23 tunes, owners {'(none)': 14, 'CAirPlane': 18, 'CBoat': 35, 'CBulletWeaponBase': 29, 'CCar': 126, 'CHelicopter': 23, 'CMissileWeaponBase': 25, 'CMotorBike': 19, 'CRPGFireLeachWeapon': 6, 'CTrain': 12}, unowned 14, horn tunes 0, collision tunes 0
```

Exit code 0. Both Out paths exist (`FORCEPULSE.md` 19,097 B, `FORCEPULSE.json` 761,684 B, both
written 2026-10-27 22:43; script 22:27).

Done-criterion match: the card asks "members + fleet ranges + a stated trigger or `UNKNOWN`". The
members and ranges are asserted in `invariants()` (`jc3forcepulse.py:1-60`), the trigger is §4 and
the unowned pulses are §4.3 + the limits paragraph, and `--check` compares both files byte for
byte (`cmd_check`, md rebuilt through `render_md`). So the Done check does coincide with the card.

## Issues

1. **`FORCEPULSE.md:207` — "54 pulses are owned by a weapon component" is wrong; the classes it
   names give 60.** `CBulletWeaponBase` 29 + `CMissileWeaponBase` 25 + `CRPGFireLeachWeapon` 6 =
   **60**, and the doc's own table at `FORCEPULSE.md:186-199` lists all three. Cause is in
   `jc3forcepulse.py:369-370`: `weapon_pulses = sum(... if k in ("CBulletWeaponBase",
   "CMissileWeaponBase"))` — the sum skips the leech class, while line 547 prints the class list
   with `if "Weapon" in k`, which includes it. Consequence: the two bullets at
   `FORCEPULSE.md:202/207` account for 214 + 54 + 14 = 282 of 307 pulses; with the correct 60 they
   still only reach 288.

2. **The missing 19 are the bikes, and §2 labels them unknown.** `FORCEPULSE.md:91` reads
   "By root class: `(none)` 19, …" — that 19 is not an unresolved class. `root_class` is
   computed at `jc3forcepulse.py:243` as `next((o.cls for o in objs if o.cls in ROOT_CLASSES), None)`
   with `ROOT_CLASSES = ("CCar", "CAirPlane", "CBoat", "CHelicopter", "CTrain")` (`line 72`); I
   checked the json: the 19 `root_class: null` entities are exactly the `v3xxx` bikes
   (`v3000_bike_autostraad_trials_civilian_01.ee`, …) whose root object class is `CMotorBike`, a
   class the constant omits. So the class is *known* and the row reads as a decode failure. The
   same omission drops `CMotorBike`'s **19** pulses from the §4.2 bullet that enumerates "the
   vehicle root class" — they sit in the table above it with no sentence. Correct bookkeeping is
   214 root + 60 weapon + 19 bike + 14 unowned = 307.

3. **`FORCEPULSE.md:262` — the `w603` "`00000000`" value cannot be read out of the json.**
   The pulse/component rows store the pointer as `None` both when the member is absent and when it
   is `00000000`, so `FORCEPULSE.json` cannot distinguish the two and nothing in `--check` guards
   the sentence. I verified it in the raw graph instead:
   `E:/Modding/_JC3grab/tmp/epe_cache/v0201_car_capstone_mediumtank_military_01.ee.xml` contains
   `<value id="B5AE7986" type="objectid">00000000</value>` on the `w603_mediumtank_mgun`
   component, and `7EE245DC=FFFFB14B` on the `w602` cannon — so the claim is **true**, but its
   provenance is the cache, not the deliverable (R11/R4: mark it or keep the raw value in the json).

4. **`FORCEPULSE.md:91` mixes units with §4.2 without saying so.** `CCar` is 125 there and 126 in
   the owner table (`FORCEPULSE.md:191`); the first counts *entities*, the second *pulses* (one
   build carries the car blast plus its barrel pulses). A one-word column label would remove the
   apparent contradiction.

None of 1-3 are invented data: each is a rendering/aggregation defect inside the card's own files,
and each is fixable without re-decoding anything.

## Spot-checks

| value in the doc | where verified |
|---|---|
| `car_explosion_medium` 500 player damage / 5 m radius (`FORCEPULSE.md:139`) | `FORCEPULSE.json` `tunes[... car_explosion_medium.ftune].values` = `PlayerDamage 500`, `PlayerDamageRadius 5.0`, `AIDamage 500`, `AIDamageRadius 5.0` — matches; same values re-asserted in `invariants()` |
| owner census `CCar` 126 summing to 307 (`FORCEPULSE.md:191`) | `FORCEPULSE.json` `owners` sums to 307 with `CCar: 126`; recomputed per pulse from `entities[].pulses[].owners` — agrees |
| 31 members = 5 named + 26 hashed, `world` on all 307 (`FORCEPULSE.md:16-19`) | `FORCEPULSE.json` `members`: 31 rows, `kind == "named"` on 5, `world.present == 307`; `id:593FCDBF`, `id:71446B1A`, `id:879640EA`, `id:9BD6FA33` present 0 |
| 41 entities with more than one pulse (`FORCEPULSE.md:86`) | `sum(1 for e in json.entities if len(e["pulses"]) > 1)` = 41 |
| medium-tank coax `id:B5AE7986 == 00000000` (`FORCEPULSE.md:262`) | raw cached `.epe` XML (see issue 3) — true, but not derivable from the json |

## Rules

R4 (no guesses as fact): honoured where it matters — the pointer's *name*, the firing moment, the
EMP trigger and the mm340 bytecode are all UNKNOWN/Q-1, and the MODLOG repeats them. The one
unmarked provenance is the `00000000` sentence (issue 3).
R5 (name ≠ behaviour): the doc is careful — it says the pointer proves the *owner* and the tune, not
the moment; horn and collision are refuted by counts (178 `horn` effects, 0 matching tune paths,
0 matching pulse names).
R11 (no typed numbers): every table cell is rendered from `build()`; the only hand-typed number is
the 54 via a mis-scoped sum, i.e. a script bug rather than an edit.

## Limits of this review

Read-only: I re-ran `--check` and the json/XML reads only; I did not edit `GRAB_BACKLOG.md`,
`MODLOG.md`, `Research/` or `Tools/`. I did not re-run the three tamper tests recorded in
`MODLOG.md:10201` — `--check` currently passes and compares both artefacts byte for byte. I did not
audit §5's per-vehicle narratives beyond the two spot-checks above (corvette: 8 `boat_explosion_large`
+ 27 `boat_explosion_medium` = 35 boat pulses, consistent with `CBoat 35`).

DONE - AUDIT-T: lore-accuracy compromise audit of the translation

## What was asked

Every place the translation chose less than BmAK lore **without** a recorded operator approval,
one line each, UNAPPROVED first and ranked by visibility in play, approval only where a file quotes
a user/operator decision for that loss.

## What was produced

| file | what it is |
|---|---|
| `Working/Translation/COMPROMISES_T.md` | the audit: answer, counts, 69 UNAPPROVED rows ranked controls > weapons > sounds > look > handling > collision, 3 APPROVED rows with file:line, the reopened "JC3 cannot" closures, the failed citation |
| `Working/Translation/COMPROMISES_T.json` | the same data, field-by-field, for the next pass |
| `Tools/scripts/audit_compromises_t.py` | generator; `--write` / `--check` / `--dump list|cites` |

Not edited: `T_ROWS.jsonl`, `GRAB_BACKLOG.md`, `T_PLAN.md`, any T-xx document, any build.

## Answer

**72 of the project's 198 translation rows compromise the lore goal; 3 carry a recorded operator
approval; 69 are UNAPPROVED.** By disposition the 72 are `out` 34, `keep` 11, `edit` 10,
`blocked` 9, `next` 6, `superseded` 2. By visibility: controls 3, weapons 9, sounds 4, look 20,
handling 26, collision 10 - and every look/handling/collision row is unapproved.

The three approved rows are T-WP6 (winch -> d-pad right, tether), T-WP10 and T-WP14 (riot
suppressor stays an omission, D-3 "accept JC3 lethality, no toggle", `GRAB_BACKLOG.md:1507`).

Ranked top of the unapproved list, most visible first:

1. **T-WP13** - 2 of 11 weapons fire; a third `SelectVehicleWeapon` index has no member; the
   T-WP13 proposal itself records 3 addressable and 8 lost. UNAPPROVED (D-7 asks for all 11).
2. **T-MD8 / T-BM1** - battle-mode turn-on-the-spot dropped to a named omission.
3. **T-WP4 / T-WP5** - the EMP missile and EMP burst: no disable path and no trigger.
4. **T-WP3** - the Missile Barrage is an unguided `w618` clone; lock-on UNKNOWN.
5. **T-WP7 / T-WP8 / T-WP9** - Drone Virus, sonar, tracker: absent, closed on a fleet census.
6. **T-AU3 / T-AU5 / T-MD14 / T-AU4** - 90 BmAK events in 10 banks silent; no transformation sting.
7. **T-ST7** - 0.6-0.8 s to full steer against BmAK's 0.25 s (2.4-3.2x slower).
8. Then the mode-scalar cluster (T-MD5/MD6/MD7/MD13), the suspension/brake bridges
   (T-S1/S2/S6, T-K1..K4), the paint/licence/casing losses (T-MA4, T-MA7, T-FX12/13/16) and the
   collision set (T-DM1/2/6/7, T-AC1, T-RA1, T-SR1, T-WLD11/15/17).

## Findings worth the operator's attention

- **The colour approval is not where the instruction says it is.** `CONTROLS_MENU_SCREENS.md`
  (52 lines) records the controls, the winch and the AR/Mission Select drops; it has no colour or
  lighting statement (0 hits for `colour|color|lighting`). So no colour loss is counted as
  approved. The good news: the colour itself is not compromised - T-MA3 keeps the authored
  `[0.02579, 0.02579, 0.03]` exactly through the linear->sRGB gain. Only T-MA4 (gloss 0.6 -> 0.45)
  loses something, and it is UNAPPROVED.
- **Six "JC3 cannot" closures are reopened by the 2026-11-05 leads**: the 11-weapon slots, the
  0.25 s steering, the real BmAK sounds, heat-seeking/lock-on, hackable drones and stunt areas.
  Each is marked UNAPPROVED with the lead's evidence beside it; none is counted as approved, and
  reopening a closure does not approve what it left behind.
- **Of the 8 weapons the first T-WP13 pass declared lost**, one is approved (riot suppressor, D-3),
  one has an approved route (winch -> tether), and six remain UNAPPROVED: EMP missile, EMP burst,
  hacker, sonar, tracker, booster mesh.
- **Two rows were held out of the ranked list as non-compromises**, with reasons recorded:
  T-WLD4/T-WLD6 are blocked on a missing `.stringlookup` *writer*, not on a design choice - the
  BmAK name and blurb are the intended output and nothing was dropped by decision.
  Seven more rows are excluded as no-loss (BmAK ships no such system, or the row was superseded by
  a fix that carries it); all nine are listed with reasons in the document, so the filter is visible.

## Verification

```
python Tools/scripts/audit_compromises_t.py --write
python Tools/scripts/audit_compromises_t.py --check
```

`--check` re-derives both files byte-for-byte, asserts every audited id exists in
`T_ROWS.jsonl`, re-opens each approval file and asserts the quoted decision still sits at the
cited line, and asserts approved + unapproved = audited. Result: exit 0,
`72 audited: 72 total -> 3 approved, 69 unapproved`.

## Limits

This is a reading of the ledger, not a re-decode: it does not re-prove any absence, and it does not
speak for the build - phase Q does. `blocked` rows that are not permanent (T-WP4/T-WP5/T-WP13) are
counted as compromises because they ship the omission today. Approval was not inferred anywhere: a
loss that merely follows from an approved decision (D-2's hybrid car) is still listed UNAPPROVED.

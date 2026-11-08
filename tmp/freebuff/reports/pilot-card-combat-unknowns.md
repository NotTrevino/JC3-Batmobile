# Pilot-card combat/gadget UNKNOWNs — what the grab decides, and what it does not

Source: `tmp/freebuff/reports/pilot-card-combat-and-gadgets.md` (read only, unchanged).
Output: `Working/Prep/pilot_card_combat_unknowns.csv` (24 rows, columns `marker_line`, `topic`,
`found_in`, `found_line`, `value`, `still_unknown`).

**SUMMARY: 24 combat/gadget markers, 4 tied to a value (still_unknown=no), 20 still open.**
The report holds 52 `UNKNOWN` occurrences on 48 lines; 24 of those lines name a weapon, gadget or
combat value and are registered here. The rest are driving/state markers, result-schema cells, check
output and meta prose — the exclusion list in §3 gives the line and the reason for each.

## 1. The four the grab settles

| marker | quantity | value found | file:line |
|---:|---|---|---|
| 59 | Vulcan time-to-overheat | `HeatUpPerSecond` **0** with `OverheatOffValue` 0.25 → no finite overheat time, by design; JC3 has **0** heat params, so neither side can overheat | `Working/Translation/T7_WEAPONS.md:147` |
| 60 | shots to kill, cannon (2–3 band) | `tank_cannon` 250 @ 50 → **H0/H2 = 2 hits, H1 = 3** against `max_health` 2000 | `Research/JC3Grab/DAMAGE_MODEL.md:139` |
| 61 | hull HP / damage readout | medium tank `max_health` **2000**; BmAK `Pawn.Health` **1200** → 1200 / 50 = **24 shell hits** | `Research/JC3Grab/DAMAGE_MODEL.md:39`, same file `:177` |
| 256 | riot damage half | BmAK has **no riot damage member**; the riot round is `base_tuning.damage` **0** and JC3 lethality was accepted (D-3) | `Working/Translation/T7_WEAPONS.md:510` |

Markers 60/61/256 are settled **as values**, not as observations: the card still cannot *count* hits or
read target health in a take (§2's instrument gaps are unchanged). What changed is that the card no
longer has to treat the number as unknown — it has a decoded band and a decoded health pool to test
against.

## 2. The twenty that stay open

| marker | topic | nearest row | why the value does not close it |
|---:|---|---|---|
| 38 | lock duration 2.0 s | `T7:215` | BmAK's `MissileLockOnDuration` 2.0 s is decoded; JC3 has **0** lock-duration members and every capture sample is ≤ 1 s |
| 149 | Vulcan shots to kill | `T7:144` | `ChainGunDamage` 40 (upgraded 50) exists, but "no target health behind it" — no target pool to ratio against |
| 167 | barrage fire input | `T7:78` | T-WP3 gives the carrier and 4 fire points, no JC3 action; `CONTROLS.md` rows 12–14/17 are `UNKNOWN` |
| 179 | lock onset time | `T7:57` | "no lock duration and no lock range" in `AutoAim` |
| 185 | reticle appears | `T7:196` | "the AutoAim -> POI link is unwritten; 0 lock members" |
| 194 | RESULT `UNKNOWN` — no reticle | `T7:196` | same evidence as 185 |
| 207 | EMP input | `T_WP5B:65` | BmAK's binding **is** decoded (`Tap {PAD_B}` Lv1 / `Hold` Lv2, keyboard `Tap [3]`); JC3 has no action to carry it |
| 228 | what fires the pulse | `T7:254` | T-WP5: "no slot: the pulse is an entity object"; 293 of 307 pulses are owned by an explosion pointer, 14 unowned |
| 239 | riot toggle input | `T7:86` | toggle is a second weapon entity and the slot count is `T-WP13` (**blocked**) |
| 251 | knock-back impulse unit | `T7:28` | join table records the bridge as **none** (units differ) |
| 253 | which member is the 7.5° cone | `T7:400` | `RiotSuppressorLockOnAngle` 7.5 is decoded; the AutoAim side has three angle members and no role statement |
| 286 | afterburner input | `T7:87` | `arcade.nitro_boost` on 145/232 vehicles, "nitro is a button, not a slot"; no JC3 action name |
| 303 | sonar input | `T7:84` | no slot, pulse is an entity object, fired by an authored vehicle action |
| 313 | sonar reveal / markers | `T7:84` | "the reveal has no probe until the marker exists"; 0 decoded script creates a scan POI |
| 322 | winch input | `T7:82` | no winch class or member on either side; the anchor is an object to add |
| 337 | hacker input | `T7:83` | no allegiance class, no beam effect, no hack interaction; slot count T-WP13 |
| 346 | did the hack flip hold | `T7:83` | 0 allegiance members in 295 `.ee` dumps |
| 355 | tracker input | `T7:85` | `BattleModeSpotLight` socket and 30° offset decoded; no slot |
| 366 | which member homes | `T7:85` | homing flag and homing delay have no member on either side |
| 446 | lock duration (instrument gap) | `T7:215` | same as 38 |

### Which file would settle each

| marker(s) | file that would settle it | in the repo? |
|---|---|---|
| 38, 179, 446 | a live read of the lock field on the weapon instance, recorded in a Q-3 take (`Working/Q/RESULTS.md`); K-11's evidence is `Working/Q/PREDICTIONS_COMBAT.md` | takes: no (test ban); K-11: yes |
| 149 | a BmAK target-health decode for the classes the Vulcan shoots — `Research/BatmobileGrab/DAMAGE_RULES.md` would have to carry it | yes (file), no (value) |
| 167, 207, 286, 303, 322, 337, 355 | `Working/Q/PILOT/CONTROLS.md` rows 12–20 plus `Research/JC3Grab/INPUT_D11.md` (0 of 134 vehicle modules reference a keymap action) | yes — both are the files, and both already say "no action" |
| 185, 194 | `Research/JC3Grab/JC3_HUD_WEAPONS.md` §1.5 (the AutoAim → POI link) | yes; it records the link as unwritten |
| 228 | `Research/JC3Grab/FORCEPULSE.md` §4.3 plus the B-18 probe | yes (doc), no (probe) |
| 239, 337 | `Working/Translation/T7_WEAPONS.md` T-WP13 — blocked on a slot mechanism | yes, and it is the block |
| 251 | `Research/JC3Grab/WEAPONS.md` §3 (impulse bands 0–100) | yes; it gives a band, not a unit bridge |
| 253 | `Research/JC3Grab/WEAPONS.md` §9 (AutoAim, 22 members, 6 contexts) | yes; membership role unstated |
| 313 | a POI census dump (entity/POI) — **does not exist** in the repo | no |
| 346 | the B-19 probe, recorded in `Working/Q/RESULTS.md` | no (test ban) |
| 366 | `Research/JC3Grab/WEAPONS.md` §5 (missile homing members) | yes; the members are absent for this projectile |

## 3. Excluded markers, with the reason

| line | marker | why excluded |
|---:|---|---|
| 8, 9, 29, 64, 399, 418, 426 | `UNKNOWN` used in the file's own prose about controls rows / aspect counts / discovery rules | no weapon, gadget or combat value named |
| 73 | P4 build id | neither combat nor a value |
| 265, 277, 278 | C6 mode switch input and threshold | driving/state, covered by the `T-MD*` rows elsewhere |
| 376–384 | `PASS / UNKNOWN / BLOCKED` verdict grammars per card | result schema, not a claim |
| 396 | example RESULT row | example of the schema; its lock-duration content is registered at 38/446 |
| 437, 449 | the instrument-gap section heading and its closing line | container, not a marker |
| 455, 456, 459 | check-table output (`46 UNKNOWN` aspects, key audit) | meta counts |

## 4. Checks

- `Working/Prep/pilot_card_combat_unknowns.csv` parses as 25 lines (header + 24), 6 columns on every
  row, `marker_line` ascending, 24 unique lines.
- Every `found_in` file exists, every `found_line` is inside it, and the first token of each `value`
  occurs on the cited line (scripted check, run at write time).
- Each `yes` row names its settling file in §2; three of those files do not exist in the repo (POI
  census, the Q-3 takes, the B-19 probe), and the report says so rather than inventing a value.
- The source report was not modified; no game install, build or tracker row was touched.

## 5. Revert

Delete `Working/Prep/pilot_card_combat_unknowns.csv` and this report.

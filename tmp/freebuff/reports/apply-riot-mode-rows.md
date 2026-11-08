# Applying the riot-mode rows (T-WP10 / T-WP14) under the 2026-11-06 rule

**STATUS: done.** The report `tmp/freebuff/reports/non-lethal-cannon-carrier.md` found **no**
non-lethal carrier in JC3, so this is the **second** of the brief's two cases: the rows take the
**closest system** (a zero-damage, high-impulse round) and the remaining gap is a **build card**
(`Research/specs/B-15.md`). The 2026-10-28 "accept JC3 lethality" decision is **superseded**, and
both rows moved `out` → `next`. No build tree, install or game was touched.

## 1. Which case applies, and why

| the brief asks | finding | case |
|---|---|---|
| did the report find a non-lethal carrier? | **no.** 0 hits for `stun`, `taser`, `shock`, `tranq*`, `bean-bag`, `ragdoll`, `water cannon`, `non-lethal`, `incapacit*` in `WEAPONS.md`, `WEAPON_WIRING.md`, `DAMAGE_MECHANISMS.md`; `electricity` is a vehicle-armour channel with no weapon→channel map; damage is typed on the **part**, not the weapon | — |
| nearest incapacitating / reduced-damage mechanism | `base_tuning.damage = 0` + `base_tuning.impulse` (+ `vehicle_impulse_factor` / `object_impulse_factor`); the only shipped 0-damage tune is the pulse `gen_explosion_5m_nodamage.ftune` (0/0, 5 m, push only) | **closest system** |
| can a tune store "non-lethal"? | **no.** `damage` numbers only; a bullet at 0 damage is unproven (only the pulse ships 0) | **gap → B-15** |
| mode toggle | no member; needs a second weapon entity/slot (T-WP13 is blocked on slots) | **gap → B-15** |

So the row text now says, in the cell itself, "**closest system, not a found non-lethal carrier**".

## 2. Files changed, and how to revert

| file | change | revert |
|---|---|---|
| `Tools/scripts/t7_weapons.py` | new `row_riot()` builds T-WP10 (was `omission(...)`); `row_d3()` rewritten: dispo `out`→`next`, title/carrier/"answer" aspects, `now`/`proposed`/`verify`/`why` | delete `row_riot()`, restore the `omission(B, J, "WPN-10", …)` call and the old `row_d3` text; re-run `--write` |
| `Working/Translation/T7_WEAPONS.md` | **regenerated** (`t7_weapons.py --write`), rows 85 and 89 | re-run `--write` after the revert |
| `Tools/scripts/t_rows.py` | `DISPO["T-WP10"]`/`["T-WP14"]`: `out` → `next` with the new why | restore the two lines |
| `Working/Translation/T_ROWS.jsonl` | **regenerated** (`t_rows.py build`), not hand-edited | `t_rows.py build` after the revert |
| `Tools/scripts/audit_compromises_t.py` | T-WP10/T-WP14 lose the `D-3` approval (both are `next` now); §3.1 prose says the approval is superseded | restore the two tuples and the sentence; `--write` |
| `Working/Translation/COMPROMISES_T.{md,json}` | **regenerated**: 72 audited, 1 approved (was 3), 71 unapproved | `--write` after the revert |
| `STATUS.md` | **regenerated** (`status_audit.py --write`): queued 46 | `--write` after the revert |
| `Research/specs/B-15.md` | **new** build card for the gap | delete the file |

## 3. The rows as they now read

`Working/Translation/T_ROWS.jsonl`:

- `T-WP10` — `dispo: next`; carrier cell: "**closest system, not a found non-lethal carrier**: a
  private bullet-tune copy with `base_tuning.damage` = 0, `base_tuning.impulse` kept high and
  `vehicle_impulse_factor` / `object_impulse_factor`; the only shipped 0-damage tune is the pulse
  `gen_explosion_5m_nodamage.ftune` (0/0, 5 m, push only)"; `now`: "nothing carries a non-lethal
  mode"; `proposed`: the tune copy + a second weapon entity for the toggle; `why`: the 2026-11-06
  rule supersedes D-3 and moves the gap to B-15.
- `T-WP14` — `dispo: next`; "**no non-lethal property in the vocabulary** … the closest system is a
  0-damage bullet tune + impulse (T-WP10)"; `proposed`: `damage` 0 + `impulse` + a second entity;
  `verify`: Q-1 with the 0-damage copy at a pedestrian and a car.

## 4. The private tune plan (what B-15 writes, in a private copy)

Target: `Working/Weapons/riot/<leaf>.wtunec` — a **copy** of B-06's built cannon tune, never the
lethal file. Members (all from `Research/JC3Grab/WEAPONS.md:84-112, 425-450`):

| member path | value | source on the BmAK side | class |
|---|---:|---|---|
| `base_tuning.damage` | **0** | riot mode has no damage of its own; the cannon's `ChainGunDamage` 40 is lethal-only | derived |
| `base_tuning.impulse` | tune maximum (100 player / 40 AI) | `RiotSuppressorVillainImpulse` 6000, `ImpactMomentum` 60000 | derived |
| `vehicle_impulse_factor` | 1.0 | same | derived |
| `object_impulse_factor` | 1.0 | same | derived |
| `fire_rate` | 0.75 | `RiotSuppressorFiringInterval` 0.75 s | decoded → direct |
| `AngleThresholdNewTarget` | 7.5 | `RiotSuppressorLockOnAngle` 7.5° | derived (which of the three is the cone is UNKNOWN) |
| `AngleThresholdCurrentTarget` | 7.5 | same | derived |
| `StickyAimStartAngle` | 7.5 | same | derived |

Entity side (not tune members): the gel impact `Riot_Suppressor.Anti_firearm_gel_Miss`, the tracer
`Particles.Batmobile_RiotSuppressor_Tracer` and the casing `Particles.RiotSuppressor_BulletCasing`
attach as `.effc`/particle references on the riot weapon entity. Both riot **sounds** are
`missing-object` in the grab, so the audio half is not carried.

Toggle: a **second weapon entity** that clones the cannon node; the lethal copy stays untouched.
It is bindable only if T-WP13's slot blocker is resolved (2 driver slots, no third index), so B-15
puts the entity in the tree and records the binding as UNKNOWN.

Order of work: copy → set the 8 members → read every member back out of the private copy → author
the second entity + effects → receipt (`sha256` of the lethal tune unchanged) → Q-1 prediction
written before any test.

## 5. Checks actually run

```
$ python Tools/scripts/t7_weapons.py --write
T7_WEAPONS.md + t7_weapons_edits.json: 14 rows (12 WPN + 2 decisions), 141 aspects (49 UNKNOWN),
3 edits, 507 md lines                                              exit=0
$ python Tools/scripts/t_rows.py build
Working\Translation\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows   exit=0
$ python Tools/scripts/t7_weapons.py --check
PASS: 14 rows = 12 WPN codes + 2 decision rows (7 with a JC3 carrier, 4 named omissions,
3 blocked) | 141 aspects classified, 49 UNKNOWN | ... | json match True, md match True   exit=0
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 46 keep 60 epe 26 re-read 0 blocked 9 out 34 superseded 7 |
edits 35 over 16 rows
check ok                                                           exit=0
$ python Tools/scripts/audit_compromises_t.py --write
72 audited, 1 approved, 71 unapproved                              exit=0
$ python Tools/scripts/audit_compromises_t.py --check
72 audited: 1 approved, 71 unapproved; by dispo {... 'next': 11 ...}
OK: every approval quote re-read at its cited line; document re-derived identically   exit=0
$ python Tools/scripts/status_audit.py --write && python Tools/scripts/status_audit.py --check
STATUS.md is current                                               exit=0
```

For the T-S6 bridge (the earlier request) the same round also passed:
`python Tools/scripts/t_s6_bridge.py --check` → `PASS: 14 checks, 3 artefacts`, exit=0. The T-7
hacker/tracker artefacts: `python Tools/scripts/t7_hacker_tracker.py --check` →
`PASS: 20/20 checks, 3 artefacts`, exit=0.

## 6. What is still not carried (stated, not accepted)

1. **A guarantee of non-lethality.** `damage = 0` is a number, not a property; whether the engine
   still kills, or still applies impulse and hit reactions, at 0 damage is UNKNOWN (only the pulse
   ships 0). Q-1 settles it; if it kills, B-15 goes BROKEN and the row returns to `blocked`, not
   `out`.
2. **The toggle.** No tune member switches modes; it is entity identity, and a bind needs a slot
   (T-WP13).
3. **The 7.5° cone mapping.** Three autoaim members are written; which one the engine treats as the
   cone is UNKNOWN.
4. **The two riot sounds** are missing objects in the grab.
5. **Stun/incapacitation on the NPC side** is outside the decoded damage model, so even a
   zero-damage round's target reaction is not decodable here.

Nothing above is recorded as an accepted compromise: rows T-WP10/T-WP14 are `next`, and
`COMPROMISES_T.md` now lists them as unapproved, with the gap owned by `Research/specs/B-15.md`.

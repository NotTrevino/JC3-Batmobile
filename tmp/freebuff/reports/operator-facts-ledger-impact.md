STATUS: done — report only, **no ledger edits** (`Working/Translation/T_ROWS.jsonl`, `GRAB_BACKLOG.md`, cards and queue briefs are untouched; the 903x apply chain keeps ownership of `T_ROWS.jsonl`). Every fact below is traced to the row/card/brief that currently states the opposite, with the exact proposed wording for review brief **9033** to apply.

# Operator gameplay facts (2026-11-08) — ledger and card impact

Source of the facts: `ROADMAP.md` §7 ("Facts from the operator that change tasks"). Evidence greps:
`Working/Translation/T_ROWS.jsonl` (248 KB, 198+ rows), `GRAB_BACKLOG.md` §1 (lines 118–256) and §11
(1788–1810), `Working/Q/PILOT/*.md`, `tmp/freebuff/queue/91*.txt`, `Working/Roadmap/*.md`.

Rule applied throughout: where a **decoded** value disagrees with a **player fact**, both are kept and
flagged `CONFLICT — reconcile`, never resolved here.

---

## F1. Pursuit mode fires only the EMP missile; tracking and boost are not weapons

**What it says now**
- `T_ROWS.jsonl` → **T-WP13**: "11 weapon classes + 1 HUD code; D-7 says **every weapon in both modes**".
- `T_ROWS.jsonl` → **T-MD9**: "D-7 resolved that every weapon is available in both modes … carried: all weapons on the one car, no mode gate".
- `T_ROWS.jsonl` → **T-BM1**: `BattleMode*`/`ArmourModeDamageReduction` rows routed to T-15 "per D-2".
- `GRAB_BACKLOG.md` §11 → **D-7**: "**resolved 2026-10-28 (user): every BmAK weapon in both battle and pursuit modes** — no per-mode split".
- `Working/Q/PILOT/CONTROLS.md` rows 10–17 list every weapon as "battle", with row 12 "tracker + EMP missile" and row 8 afterburner — no statement that pursuit has one fire slot.
- Briefs: `9104` (EMP missile, rank 1), `9105` (lock/salvo), `9110` (cannon + Vulcan + riot pods), `9130` (mode pair), `9199` (campaign review) — all built on "every weapon every mode".

**Implication.** D-7 as written is **contradicted by lore**. Per-mode weapon sets are correct, pursuit
carries **one** fire slot (EMP missile), and tracker/boost are pursuit-exclusive *systems*, not weapons.
T-WP13's slot-pressure argument collapses from N slots to 1 in pursuit.

**Proposed change (9033)**
- `T-WP13`: replace "D-7 says every weapon in both modes" with "**operator 2026-11-08: pursuit = EMP missile only; tracker/boost are pursuit-exclusive systems, not weapons**; battle = the rest. Slot pressure: pursuit 1 fire slot, battle 2." Keep the 53-entity / max-2-driver-slot decode as the JC3 limit.
- `T-MD9`: "carried: all weapons on the one car, no mode gate" → "carried: battle set on the one car; **a pursuit set of 1 (EMP) must be gated per mode** (NEW-WPN-9/34)".
- `T-BM1`: unchanged decode, add "D-2 re-opened by operator fact (per-mode weapon sets), not by new evidence".
- `GRAB_BACKLOG.md` §11 D-7: append "**REOPENED 2026-11-08 (operator, played BmAK): pursuit fires only the EMP missile; tracking/boost are pursuit-only and are not weapons. Per-mode weapon sets are lore. T-WP13/T-MD9 revised accordingly.**" (Do not delete the 2026-10-28 resolution — show the reversal with its date.)
- `CONTROLS.md`: add a "mode" column value `pursuit` to row 12 and `battle` to rows 10, 11, 13–17, and a note "pursuit has one fire slot".

## F2. Armour is identical in both modes

**What it says now**
- `T_ROWS.jsonl` → **T-MD10**: "`ArmourModeDamageReduction` = **0** (int, undocumented scale), identical on Funhouse/MK2/V2 … carried: the shipped value is 0, so there is no reduction to carry".
- `T_ROWS.jsonl` → **T-DM3**: "no per-channel armour exists … `ArmourModeDamageReduction` 0".
- `GRAB_BACKLOG.md` §1 → **MOD-2**: battle mode includes "armour reduction (`ArmourModeDamageReduction`)" as a *battle* property.
- `Working/Roadmap/damage_world.md` G1-14 line lists "(0)" without a mode statement.

**Implication.** The decode (value 0, three packages) and the player fact (**identical armour, both
modes**) agree in *effect* but the backlog labels it a battle-mode property, which is now wrong as a
statement of design. No value changes.

**Proposed change.** `MOD-2`: delete "armour reduction (`ArmourModeDamageReduction`)" from the battle
row and add a note "armour identical in both modes (operator 2026-11-08)". `T-MD10` gains
"mode-invariant (operator); the 0 is not a battle scalar". **CONFLICT flag:** if any later decode shows
a non-zero `ArmourModeDamageReduction` on another package, keep both and reconcile — do not pick.

## F3. Health regenerates out of combat, full on re-summon / after death

**What it says now**
- `GRAB_BACKLOG.md` §1 → **ARM-5**: "Armour regeneration out of combat, **if** BmAK has a regen value (G1-14 decides)" — conditional.
- `Working/Roadmap/damage_world.md` **ARM-5**: "regeneration: JC3 has no member … BmAK rate value UNKNOWN" → status **blocked**; **NEW-ARM-01** also blocked (needs running BmAK CDO).
- Brief `9171` sets max_health and the explosion but carries **no regen** requirement.

**Implication.** ARM-5 is no longer "maybe absent": regeneration is **required lore**. Per the closest-system
rule a carrier is mandatory (regen timer → RB-9), and "full on re-summon" is a *spawn* property, separate
from the regen rate.

**Proposed change.** `ARM-5` reword: "out-of-combat regeneration and **full health on re-summon** are
lore (operator 2026-11-08); the rate value stays UNKNOWN (NEW-ARM-01) but the mechanism is not optional".
`Working/Roadmap/damage_world.md` ARM-5 status `blocked` → `todo` with the carrier named (RB-9), keeping
NEW-ARM-01 blocked for the *value* only. `9171` must add two acceptance lines (below).

## F4. Eject: hold A to charge, tap A goes higher, double-tap gives the lowest eject

**What it says now**
- `GRAB_BACKLOG.md` §1 → **MOD-3**: "Ejection: **hold-to-eject** launches the driver into the air (Batman glides)".
- `T_ROWS.jsonl` → **T-CT2**: "**operator rule 4**: eject = **double press of A** … no double-press field anywhere … **blocked**".
- `Working/Q/PILOT/CONTROLS.md` row 19: `Eject into glide` → BmAK `A A`, JC3 `UNKNOWN`.
- `Working/Roadmap/modes_controls_anim.md` **NEW-MOD-2** ("confirm eject input … double-press A vs older hold A") and **NEW-MOD-5** ("double-press window for A; needs runtime").

**Implication.** All three records are partial: the mechanic is **three-level** (charged hold, tap = higher,
double-tap = lowest). NEW-MOD-2 is answered and can close. T-CT2's "no double-press field" stays true
*for data*; the level selection is runtime logic, not a keymap field.

**Proposed change.** `MOD-3`: "Ejection: **three levels** — hold A to charge (height by charge), **tap A**
= higher eject, **double-tap A** = lowest eject (operator 2026-11-08)". `T-CT2`: add "three-level eject;
the keymap only carries the binding — level logic is code (9170), not data". `CONTROLS.md` row 19:
`A A` → `A (tap = high, hold = charged, double-tap = low)`. `NEW-MOD-2` → `done` (answered by operator),
`NEW-MOD-5` stays todo (window length still unknown).

## F5. The car explodes instantly at 0 HP

**What it says now**
- `T_ROWS.jsonl` → **T-FX22**: "**keep: the 3-variant burn family** (engine fire)". **T-FX23**: "**keep: engine smoke, then `dmg_post_burn`**".
- `Working/Roadmap/hud_cam_lights_fx.md` line 169: "T-FX22/23 … **CONFLICT** with operator fact 'no visible damage stages'"; line 244/256 keep the conflict open.
- Brief `9171` already says "the health bar falls to zero, then the car explodes violently" — **aligned**.

**Implication.** The rows' disposition ("keep") contradicts the fact; the brief is right. T-FX22/23
should move from "keep" to "**not carried** — donor stage effects dropped", and 9171 must not add them.

**Proposed change.** `T-FX22`/`T-FX23` disposition → "**dropped** (operator 2026-11-08: instant explosion at
0 HP, no fire/smoke stages); the `.effc` stays decoded for reference only". `hud_cam_lights_fx.md` line
169 becomes "resolved: no stages", and its question 9 closes. **CONFLICT kept on record:** the donor
`.ee` *does* list `dmg_fire_engine`/`dmg_post_burn` (T-FX22/23 decode) — that is the donor's chain, not
lore; flag for reconciliation rather than deleting the evidence.

## F6. Paint: dark gunmetal satin, carbon-weave insets, white chevron decals

**What it says now**
- `GRAB_BACKLOG.md` §1 → **APP-2**: "Paint reads as the Arkham Knight **matte/satin** armour in noon and night light".
- `Working/Roadmap/appearance.md` line 178 asks the operator "pure black, charcoal, gunmetal blue? … matte or satin?" — now answered; line 192 calls colour "no ground truth path".
- Brief `9143`: "Write the body paint … four channels' colour, F0 and wetness members, with the decoded values of `COLOUR_PARAMS.md`" — no colour target stated.

**Implication.** APP-2's criterion is too weak ("matte/satin") and the open question is answered:
**dark gunmetal satin**, specular edges, **carbon-weave insets**, **white chevrons**. The RC white-violet
result was both too light and wrong in hue. Whether the carbon/chevron slots exist is still a check
(APP question 10).

**Proposed change.** `APP-2`: criterion → "dark **gunmetal satin** body, specular edge response, carbon-weave
insets, white chevron decals; white-violet RC rejected on lightness **and** hue (operator 2026-11-08)".
`appearance.md` question 1 marked answered; keep question 10 (do the chevron/carbon slots exist).
`9143` gains the target colour as an acceptance line, still sourced from `COLOUR_PARAMS.md` channels.

## F7. Barrage auto-fires at full lock; 1/4/7/10 targets by upgrade level

**What it says now**
- Brief `9105`: "covers the held lock of 2.0 s with the **8-target salvo**: BmAK carries `MissileLockOnDuration` and `MaxTargets`".
- `GRAB_BACKLOG.md` §1 → **WPN-3**: "missile barrage with target lock — multi-target lock-on salvo".
- `Working/Roadmap/weapons.md` rows referenced by 9105 (`B-24` spec) carry the 8-target figure.

**Implication.** Two things change: (a) the salvo **auto-fires at full lock** (no separate fire press),
(b) target count is **1/4/7/10 by upgrade level**, not a flat 8.

**Proposed change.** `9105` must be rewritten before it runs. `WPN-3` row: add "auto-fires at full lock;
targets 1/4/7/10 by level; build at **10** for a fully upgraded car unless told otherwise (ROADMAP §7)".
**CONFLICT — reconcile:** decoded `MaxTargets` = 8 vs lore max 10; keep both (8 is the data value found
in BmAK's classes, 10 is the player-visible max level) and do not overwrite the decoded number.

## F8. RT fires the cannon, RB the Vulcan

**What it says now**
- `Working/Q/PILOT/CONTROLS.md` rows 10–11: cannon → JC3 `LMB`/`RSHOULDER`, "BmAK `RT`"; Vulcan → `RMB`/`LSHOULDER`, "BmAK `RB`" — **already correct** in the BmAK column.
- `T_ROWS.jsonl` **T-WP13** has no bind statement; brief `9110` builds both weapons without a bind statement.
- `GRAB_BACKLOG.md` §11 **D-11** ("only ENTER uses JC3's control") already implies this.

**Implication.** Confirmation, not a change — but it fixes the JC3 side: cannon onto the primary fire
action (RT→`RSHOULDER` or `LMB`), Vulcan onto secondary (`RB`→`LSHOULDER`/`RMB`), and the mode split from
F1 decides when each is live.

**Proposed change.** `9110` gains "binds: RT = cannon, RB = Vulcan (operator 2026-11-08)" and the mapping
row; `CONTROLS.md` rows 10–11 keep the values and drop the "menu: …" hedge. No ledger value change.

## F9. Transform takes ~2 s and causes a near-instant slowdown

**What it says now**
- `T_ROWS.jsonl` **T-BM1** → transform pose routed to T-12; no duration.
- Brief `9130`: "Rebuild the pair on the RC5 base with the **pursuit** …" (mode pair + swap), no timing/speed statement.
- `ROADMAP.md` §7: "B-12/9130: a momentum loss on swap is lore, so the second-entity route's 'arrives at rest' problem shrinks (the state carried is health/ammo, not speed)".

**Implication.** The swap has a **duration (~2 s)** and a **near-instant speed loss**; a second-entity swap
does not need to transfer velocity, and the HUD/animation must cover the 2 s window.

**Proposed change.** `9130` must be rewritten with (a) the 2 s transform window as an acceptance line,
(b) "speed drops on swap" as lore, (c) the carried state = health/ammo only. `T-BM1` gains
"transform ≈ 2 s, near-instant slowdown (operator)". Add a row (T-MD or T-CT) for the swap slowdown if
9033 wants it tracked; do not silently extend T-12.

---

## Queue briefs that must be rewritten before they run

| brief | why | rewrite needed |
|---|---|---|
| **9105** lock/salvo | F7: auto-fire at full lock, 1/4/7/10 targets | **yes — blocking** |
| **9110** cannon/Vulcan/riot | F1 (mode gating: cannon/Vulcan are battle-only), F8 (binds) | **yes — blocking** |
| **9130** mode pair + swap | F1 per-mode sets, F2 identical armour, F9 2 s + slowdown | **yes — blocking** |
| **9143** paint channels | F6 gunmetal satin + carbon + chevrons target | **yes — blocking** |
| **9170** controls/entry/exit/eject | F4 three-level eject | **yes — blocking** |
| **9171** health/explosion | F3 regen + full on re-summon; F5 drop burn stages | **yes — blocking** |
| **9194** pilot-card refresh | must encode F1/F4/F6/F7/F8 into cards and `CONTROLS.md` | **yes — after the six above** |
| 9104 EMP missile | consistent with F1 (pursuit weapon) | no |
| 9107 EMP burst | ROADMAP's disable fact, not one of the nine | no |
| 9199 campaign review | read-only review | no |

Ordering consequence for 9033: 9130 depends on 9105/9110's per-mode decision, and 9194 must run last.

## Reconciliation register (both values kept)

| item | decoded / recorded | player fact | action |
|---|---|---|---|
| armour per mode | `ArmourModeDamageReduction` 0 (3 packages) | identical in both modes | both kept; row text says mode-invariant |
| max lock targets | `MaxTargets` = 8 (BmAK classes / B-24 spec) | 1/4/7/10 by level | both kept, flagged in 9105 |
| 0 HP behaviour | donor `.ee` lists `dmg_fire_engine` + `dmg_post_burn` | instant explosion | effects dropped from the build, decode kept as evidence |
| eject input | backlog "hold A" / menu "double-press" | three-level | three-level recorded; old wordings kept in history only |
| top speed | 336.4 km/h `assumed` (T-E5) | not part of these nine facts | untouched |

## What this report did not do
No file other than itself was written. No ledger row, backlog row, card or brief was edited, so the 903x
apply chain remains the only writer of `T_ROWS.jsonl`. No fact was allowed to overwrite a decoded value.

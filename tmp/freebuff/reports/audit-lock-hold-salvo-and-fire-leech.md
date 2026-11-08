# Audit — lock-hold / 8-target salvo plan against its two named sources

**Plan audited (not edited):** `tmp/freebuff/reports/lock-hold-salvo-closest-system-plan.md`.
**Sources checked:** `tmp/freebuff/reports/wp4-fire-leech.md` (wp4) and
`Working/Translation/T_WP3B_LOCKON.md` (T-WP3b), plus the plan's own carrier report
`tmp/freebuff/reports/lock-hold-and-salvo-carrier.md` where a claim is sourced only there.
**Focus:** the 2.0 s lock hold, the 8-target salvo, every tune-member offset the plan names, and the
statement that `missile_per_shot` is 1.
Verdicts: **VERIFIED** = the named source says it; **OVERSTATED** = the fact exists but does not support
the claim as written; **UNSUPPORTED** = not in the named source, or contradicted by it.

---

## Claim table

| # | claim in the plan | source and line | what the source says | verdict |
|---|---|---|---|---|
| L1 | BmAK lock hold = `RBatmobileEMPMissile.MissileLockOnDuration` **2.0 s** @0x0A00 (civilian 1.0 @0x0A04) | `T_WP3B_LOCKON.md` §4.1, §6; `wp4-fire-leech.md` §3.4 | T-WP3b §6: "`MissileLockOnDuration` \| 2.0 at `0x0A00`", civilian "1.0 at `0x0A04`"; wp4 §3.4: "lock hold `MissileLockOnDuration` **2.0 s** (civilian 1.0)" | **VERIFIED** (the BmAK value and offsets) |
| L2 | the hold is carried on `WeaponTuning.aim_timer_override` @108 set to **2.0** — "the only root-level timer" | `T_WP3B_LOCKON.md` §4.1; `wp4-fire-leech.md` §2.2, §4 | T-WP3b §4.1: lock hold "**none**: `AutoAimSettings` is 22 members, none a duration … `UNKNOWN` — *where:* the native aim manager"; wp4 §4: "a lock that is *held* for a duration — **no**". wp4 §2.2 lists `aim_timer_override` **4.0** as a fire-block value. The plan's own carrier report §4.1 says "`aim_timer_override` … an RPG-class aim timer, **not 2.0 and not lock-gated**" | **UNSUPPORTED / contradicted** — both named sources say no member carries the hold; the carrier report explicitly denies this member is one |
| L3 | `aim_timer_override` is at **offset 108**, 4 B float; 4.0 on the RPG class; distribution 8 at 4.0 / 1 at 0.001 / 65 at −1 | `wp4-fire-leech.md` (no offset), `T_WP3B_LOCKON.md` (no such member) | neither audit source names offset 108 or the distribution; `lock-hold-and-salvo-carrier.md:114-118` does: "offset **108**, 4 B float … 8 file(s) at 4, 1 file(s) at 0.001, 65 file(s) at -1" | **VERIFIED against the carrier report**, **UNSOURCED in the two audit files** |
| L4 | a 2.0 s `STimerComponent` on the launcher, repurposed from `w501` (decoded timers 1 / 2 / 6 / 0.6 / 0.01 / 20 s) is the gate | `wp4-fire-leech.md`, `T_WP3B_LOCKON.md` | neither mentions `STimerComponent` or its values; `lock-hold-and-salvo-carrier.md` §8 (`w501_turret_sam_v2.epe`) gives `STimerComponent=1`, `STimerComponent1=2`, `delay=2`, `destroy_tower=6`, `CTimeTrigger=0.01`, `blink_on_hit=0.6`, `fade_all_CTimeTrigger=20` | **VERIFIED against the carrier report**, **UNSOURCED in the two audit files** |
| L5 | BmAK 8-target salvo = `RBatmobileMissileLauncher.MaxTargets` **8** @0x095C | `wp4-fire-leech.md` §3.4; `T_WP3B_LOCKON.md` §8.5 | wp4 §3.4: "`MaxTargets` **8** / `MissileNumberParameter` … `missile_per_shot` 1 … nothing names a target count"; T-WP3b §8.5: "BmAK's `MaxTargets` 8 has no JC3 counterpart in the data" | **VERIFIED** (value 8); the 0x095C offset is not in either source |
| L6 | the salvo is carried by `MissileWeaponTuningBase.missile_per_shot` @44 = **8**, one trigger firing 8 | `T_WP3B_LOCKON.md` §1, §5, §8.5; `wp4-fire-leech.md` §4, §6.4 | T-WP3b §1: "`missile_per_shot` is 1 on every vehicle missile, and nothing in `WeaponTuning` counts *targets*: a burst is several missiles at one aim point, not a salvo split across several targets"; §5: "A salvo split across 8 targets needs a code bridge … or the BmAK behaviour reduced to a burst at one"; wp4 §4: "a salvo split across 8 targets — **no**" | **OVERSTATED / UNSUPPORTED** — the member exists, but the sources distinguish it from a target count and say the 8-target behaviour needs a code bridge. The plan's D1 calls this a "1:1" mapping |
| L7 | `missile_per_shot` is **1** on every vehicle missile and **6** on `w123` | `T_WP3B_LOCKON.md` §1; `wp4-fire-leech.md` §2.1, §3.1 | T-WP3b §1 table: `w123` per shot **6**, all 14 vehicle missiles **1**; wp4 §2.1 and §3.1 both give `w143`/`w618` `missile_per_shot` **1** | **VERIFIED** — but the plan then writes 8, which its two sources say is a different quantity |
| L8 | `missile_per_shot` is at **offset 44**, **u8** | `T_WP3B_LOCKON.md` §2 | "| 44 | 1 | `missile_per_shot` | missiles per trigger pull |" | **VERIFIED** |
| L9 | 6-muzzle `SWeaponFirePattern` cloned from `w501_turret_sam_v2`; 8 = 6 + 2 repeat | `wp4-fire-leech.md`, `T_WP3B_LOCKON.md` | neither names `SWeaponFirePattern` counts or w501's muzzle count; `lock-hold-and-salvo-carrier.md` §8/§15: "`w501_turret_sam_v2` is a `CMissileWeaponBase` with **6 muzzles** … `missile_per_shot` 1, turning 35" | **VERIFIED against the carrier report**, **UNSOURCED in the two audit files**; "8 from 6 muzzles is legal" is the plan's inference (T-WP3b supports >1 per muzzle via w123's 6) |
| L10 | the Fire Leech leg carries guided flight with `missile_turning_speed` @24 = **150** | `wp4-fire-leech.md` §0, §2.1, §3.3; `T_WP3B_LOCKON.md` §2.1 | wp4: the Fire Leech's turning speed is **300 / 300**, and §3.3 says "copy 5 values from `w143` … `missile_turning_speed` **300**, random 60, accel 30→65 …"; T-WP3b §2.1: `w143` 300, `w609` 150 | **OVERSTATED** — 150 is `w609`'s number, not the Fire Leech's; the leg is mislabelled (offset 24 itself is **VERIFIED** in T-WP3b §2) |
| L11 | `missile_no_turning_time` @32 = 0.0 and `missile_loose_lock_distance` @48 = 0 (w609 values) | `T_WP3B_LOCKON.md` §2, §2.1 | offsets 32 and 48 with size 4; §2.1 values 0 for `w609` | **VERIFIED** |
| L12 | `MaxAimDistance` @60, 750 on `w609`, −1 in both shared presets; build carries −1 | `T_WP3B_LOCKON.md` §3.1, §4.1 | §3.1: `MaxAimDistance` \| 60 \| 750 (`w609`) \| 750 (`w612`) \| −1 (`w613`); §4.1: "−1 *unlimited* in both shared presets, 750 in `w609`'s own preset" | **VERIFIED** |
| L13 | the missile's AutoAim is a private copy of the Fire Leech profile: 0.12 / 0.15 / Cutoff 100 / `MaxAim` −1 / `MinAim` 15 / `CanTargetVehicles` 1, "all 6 contexts identical" | `wp4-fire-leech.md` §2.3, §3.4 | wp4 §2.3 confirms every value and "6 × 88 B … repeated identically for all six shooter contexts"; **but** it also records `CanTargetCharacters` **1** (unique), `CanTargetRigidObjects` **0**, and §3.4 recommends a *new* tune with characters **0**, vehicles 1, rigid 1 because "copying the tune wholesale would let the Batmobile lock pedestrians, which BmAK does not" | **VERIFIED** values; **OVERSTATED** as a wholesale copy — the source prescribes an edited profile |
| L14 | lock cone 40° has a member but the unit is UNKNOWN (D10) | `T_WP3B_LOCKON.md` §4.1, §4.2; `wp4-fire-leech.md` §2.3 | §4.1: "no member carries degrees"; §4.2: "The `StickyAimAngle*` family (5 / 10 / 15) cannot be turns … The reading stays `UNKNOWN`" | **VERIFIED** |
| L15 | reticle: `POI_TYPE_LOCK_ON_TARGET` 21, 1.5 s per turn, **0** `CreatePoi` calls, entity→HUD native | `T_WP3B_LOCKON.md` §4; `wp4-fire-leech.md` §1 | §4: "`POI_TYPE_LOCK_ON_TARGET`, one turn per 1.5 s … 0 `CreatePoi(POI_TYPE_LOCK_ON_TARGET, …)` calls"; "the entity→HUD call is native (`UNKNOWN`)" | **VERIFIED** |
| L16 | `burst_count` / `burst_cooldown` at offsets **@88 / @92** | `T_WP3B_LOCKON.md` §2 | the 15-member `MissileWeaponTuningBase` table ends at offset **68**; no 88/92 anywhere in T-WP3b, none in wp4 | **UNSOURCED** |
| L17 | `MaxTargetsPerLevel` @0x0A20 (array, 1 item), `MissileSockets` @0x0A30 (10 items), `MissileNumberParameter` @0x09CC | `wp4-fire-leech.md`, `T_WP3B_LOCKON.md` | no offset or array length for any of the three appears in either file (`Research/BatmobileGrab/WEAPONS.md` §13 is the plan's actual citation) | **UNSOURCED in the two named files** |
| L18 | `FireInterval` 0.5 s at **0x098C** | `wp4-fire-leech.md` §3.1 | wp4 gives `fire_rate` **0.5** for `w618` but no 0x098C; T-WP3b §1 gives no offset for burst/cadence | **UNSOURCED offset**, value VERIFIED |
| L19 | the missile must move from `CBulletWeaponBase` to `CMissileWeaponBase` to home | `wp4-fire-leech.md` §3.3, §3.4 | "guidance is a **tune** member, not a component or a class … **change no class and add no component** — w618's build keeps its own weapon class and only gains a lock-on `AutoAim` tune" | **UNSUPPORTED / contradicted** |
| L20 | `w618` turning speed is **0**, so today's missile does not home | `wp4-fire-leech.md` §3.1; `T_WP3B_LOCKON.md` §2.1 | wp4 §3.1: `w618` 0/0; T-WP3b §2.1: 0/0 and lists `w618` among the seven zero-turning vehicle missiles | **VERIFIED** |
| L21 | `w501` has 6 muzzles, turning 35, `missile_per_shot` 1, `STargetPoint.min_aim_distance` 5 | `wp4-fire-leech.md`, `T_WP3B_LOCKON.md` | `w501_sam_missile` turning **35 / 50** and per shot **1** in T-WP3b §1; muzzle count and `min_aim_distance` 5 only in the carrier report §8 | **PARTLY VERIFIED** (turning / per-shot), muzzle + aim distance from the carrier report |
| L22 | 8 markers require 8 simultaneously held targets (U3 flags it UNKNOWN) | `T_WP3B_LOCKON.md` §8.5 | "Whether a missile can hold several targets … `missile_per_shot` 1 everywhere and no target-count member" | **VERIFIED as UNKNOWN** — the plan is honest here |

---

## Claims the plan owner must correct

1. **The 2.0 s hold is not a carry (L2).** Both named sources say JC3 has **no** lock-duration member
   (`AutoAimSettings` 22 members, none a duration; native aim manager), and the plan's own carrier report
   calls `aim_timer_override` "an RPG-class aim timer, **not 2.0 and not lock-gated**". Re-file P1 as an
   **invented gate** (script/entity timer) with `aim_timer_override` as an optional secondary write, and
   stop describing it as "the only root-level timer" carry. The plan's own U1 already half-admits this.
2. **The salvo is not 8 targets (L6).** `MaxTargets` counts *targets*; `missile_per_shot` counts
   *projectiles per trigger pull*, and both sources say a target-count member does not exist and that
   splitting a salvo across 8 targets "needs a code bridge". Either rename the leg to "8 missiles at one
   aim point" (which the data supports) or move the target-split to the UNKNOWN/code-bridge column.
   D1's "derived, 1:1" mislabels the transform.
3. **Drop the weapon-class change (L19).** wp4 §3.3 is explicit: guidance is a tune member and the build
   should "change no class and add no component". Moving the component to `CMissileWeaponBase` is
   unsupported by the cited sources and would risk the existing `w618` wiring.
4. **The Fire Leech leg uses the wrong donor number (L10).** 150 is `w609`'s turning speed; the Fire
   Leech is **300** (wp4 §2.1, §3.3). Rename the leg to "w609-guided flight" or write 300.
5. **Do not copy the Fire Leech AutoAim wholesale (L13).** It is the only tune with
   `CanTargetCharacters` 1 and it drops rigid objects; wp4 §3.4 prescribes characters 0 / vehicles 1 /
   rigid 1 with w143's 0.12 / 0.15 cone.
6. **Fix or attribute the offsets (L16–L18).** @88/@92, 0x095C, 0x0A20, 0x0A30, 0x09CC and 0x098C are
   not in either named source. Either cite `Research/BatmobileGrab/WEAPONS.md` §12–§13 and the carrier
   report explicitly, or drop the offset and keep the value.
7. **Separate carrier-report facts from wp4/T-WP3b facts (L3, L4, L9, L21).** Offset 108, the timer
   distribution, the 6 muzzles and `min_aim_distance` 5 are real but come from
   `lock-hold-and-salvo-carrier.md`, not from the two files the plan lists as its evidence.

---

## Limits

* Static reads only: no archive, tune or entity decoded in this audit; every quote is from the markdown
  named in the row.
* The carrier report's own decode of `aim_timer_override` offset 108 and w501's timers was not re-run
  against the archive; it is treated as the plan's source, which is how the plan cites it.
* The plan was not edited. This audit touches only this file. **Revert:** delete this file.

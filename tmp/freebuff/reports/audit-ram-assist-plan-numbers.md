# Audit — ram-assist plan numbers against their cited sources

**Plans audited (not edited):** `tmp/freebuff/reports/ram-assist-closest-system-plan.md` (§1, §2.2–2.5, §5.3–5.4) and
`tmp/freebuff/reports/carrier-ram-and-dodge.md` (§0, §1, §2, §8).
**Method:** every claim below was located in the plan, then read in the file it names. Verdicts are
about the *number and its source*, not about the composition.
Labels: **MATCH** = cited source says the claimed value; **MISMATCH** = source says something else;
**UNSOURCED** = no cited line says it, or the cited file does not exist.

---

## Claim table

| # | claim in the plan | cited source with line | what the source says | verdict |
|---|---|---|---|---|
| 1 | `rotor_collision.damage_to_other_per_second` **100000/s** on **232 module sets**, donor included (`carrier` §0, §2; `ram` §2.2) | `Research/JC3Grab/VOCABULARY.md:1415` | "`rotor_collision.damage_to_other_per_second` \| float \| 100000 .. 100000 (med 100000, **n=232**) \| 100000" — min = max = 100000, donor 100000 | **MATCH** |
| 2 | "the module is in the set of **all 232 vehicles**" (not 233) (`carrier` §0; `ram` §2.2) | `Research/JC3Grab/DAMAGE_MECHANISMS.md:28` (the plan's own 233 figure) | "**233 roots in 232 entities** (one train entity carries two)" — so 232 vehicles/entities is the correct denominator, 233 is entity *roots* | **MATCH** (the 233/232 pair is reconciled by that line; no contradiction) |
| 3 | sibling members `min_rpm` 30, `light_object_mass_ratio` 0.02, `mass_ratio_when_no_mass` 0.1 (`ram` §2.1) | `VOCABULARY.md:1416-1418` | 0.02 (n=232), 0.1 (n=232), 30 (n=232), min = max in each | **MATCH** |
| 4 | band floor **20** and ceiling **150** are the *archetype* (shipped) values (`ram` §1) | `Research/BatmobileGrab/DAMAGE_RULES.md:151-152`; per-instance rows `:584-585`, `:637-638`, `:664-665` | `ImpactMaxDamageSpeed` 150 (`:151`), `ImpactMinDamageSpeed` 20 (`:152`); `…ImpactMaxDamageSpeed` 150 / `…ImpactMinDamageSpeed` 20 for `Playable_Batmobile_SF`, MK2 (`:664-665`, `:637-638`) | **MATCH** (citation imprecise — see C2) |
| 5 | class defaults are **60 / 200** and are the losing column (`ram` §1) | `Research/BatmobileGrab/CLASS_DEFAULTS.md:256-257` | 200.0 (`0x04e0`, 6860), 60.0 (`0x04e8`, 6864) | **MATCH** |
| 6 | `ImpactStrafeMod` **2.25** archetype / **1.5** class (`ram` §1, §2.4) | `DAMAGE_RULES.md:153`, `:593`, `:646`, `:673`; `CLASS_DEFAULTS.md:258` | 2.25 (`:153`, and all four Batmobile archetype rows); class 1.5 at `0x04f0` | **MATCH** |
| 7 | `ImpactBoostMod` **2.0** archetype / **1.5** class (`ram` §1) | `DAMAGE_RULES.md:147`, `:583`, `:636`, `:663`; `CLASS_DEFAULTS.md:260` | 2 (`:147`, and `:583`/`:636`/`:663` archetype rows); class 1.5 at `0x0500` | **MATCH**, but the carrier's `BOOST_COVERAGE.md:120` citation is **UNSOURCED** — no file of that name exists in the repo (glob `**/*BOOST_COVERAGE*` = 0 files) |
| 8 | `KillFlipTorque` is **−2,000,000** (`ram` §0, §1, §5.4; `carrier` §1) | `CLASS_DEFAULTS.md:270` (`ram` §1 cites only the file, no line) | "`KillFlipTorque` (RVehicleBatmobileBase) \| FloatProperty \| **-2000000.0** \| decoded \| BmGame\RVehicleBatmobileBase.g.cs:7946 (off 7192)" — i.e. the **class default** at `0x0588`/7192 | **MISMATCH** as the *shipped* value: `DAMAGE_RULES.md:594`, `:618`, `:647`, `:674` give the archetype `KillFlipTorque` = **−200** (Batmobile, MK2), **−400** (Joker). The CDO line does exist, so the number is traced to a line — but to the wrong value set. |
| 9 | `KillFlipTorqueDuration` **1.5 s** (`ram` §1, §5.4) | `CLASS_DEFAULTS.md:271` | 1.5 (`0x0590`, 7196) | **MISMATCH** as shipped: archetype duration is **0.5 s** (`DAMAGE_RULES.md:595`, `:648`, `:675`), Joker 0.75 (`:619`). |
| 10 | "the drift torque ceiling is 35000, **57× short**" (`ram` §0, §5.4) | `VOCABULARY.md:479`; arithmetic over `CLASS_DEFAULTS.md:270` | "`drift.max_drift_torque` \| float \| **0 .. 35000** (med 12000, n=145) \| 5000" | **MATCH** arithmetic only: 2 000 000 / 35 000 = 57.1. On the archetype value (−200) the ceiling is **175× larger** than the torque, i.e. the "impossible" verdict flips (see C4). |
| 11 | the pulse impulse slot is "2000× the fleet max (1000)" (`ram` §5.4) | `Research/JC3Grab/FORCEPULSE.md:31` | "`id:24872388` \| hashed \| 307 \| 6 \| **25 .. 1000**" | **MATCH** (2 000 000 / 1000 = 2000) |
| 12 | `rotor_collision` offsets 0x130/0x134/0x138/0x13C in `vehicle_common.vmodc` (`ram` §2.1, §8) | in-plan re-read printed in `ram` §8 | the `struct.unpack_from` output in the plan prints 30.0 / 0.1 / 100000.0 / 0.02 at those offsets | **MATCH** (self-contained read-back; not re-run here) |
| 13 | `ImpactRoadAssistMaxTorque` 15000 / 30000 already carried as `counter_steer_torque_brake` 15000 / `counter_steer_torque_handbrake` 30000 (`ram` §0, §5.1) | `CLASS_DEFAULTS.md:229` (15000) and `DAMAGE_RULES.md` archetype (30000), plus the drift block in `Builds/bm-RC2` | class 40000 factor / 15000 torque at `0x02ce`; archetype table in `carrier` §1 quotes 30000 | **MATCH** on the two quoted numbers (the 30000 line itself is not pinned in either plan — see C5) |

---

## Corrections for the plan owner

**C1 — Kill-flip magnitude is a class default, not the shipped value (highest priority).**
`ram-assist-closest-system-plan.md` §1 uses the archetype column for every impact value (20/150/2.25/2.0,
and 10000 for `VehicleShovingTorque`) but takes `KillFlipTorque` −2 000 000 from `CLASS_DEFAULTS.md:270`.
The same file's archetype rows (`DAMAGE_RULES.md:594, 618, 647, 674`) ship **−200** (Batmobile, MK2) and
**−400** (Joker); duration **0.5 s**, not 1.5. Either state the row as "class default −2 000 000 /
archetype −200" the way §1 does for every other member, or retarget the leg at −200. As written, the plan's
headline "57× short of the torque ceiling" and "2000× out of domain" describe a value the game does not ship.

**C2 — Cite the decoded lines, not the prose summary.**
`carrier-ram-and-dodge.md` §1 cites `DAMAGE_RULES.md:153` for the strafe mod (correct) but the band itself
is attributed to `DAMAGE_RULES.md:274`, which is the report's own prose row ("speed band 20→150 …"), not a
decoded tag. The decoded lines are `DAMAGE_RULES.md:151-152` (table) and `:584-585` / `:637-638` / `:664-665`
(per-archetype sdk-layout). Use those.

**C3 — `BOOST_COVERAGE.md:120` does not exist.**
`carrier` §1 line for `ImpactBoostMod` names it; the repo has no `BOOST_COVERAGE.md` (glob returned 0).
Replace with `DAMAGE_RULES.md:147` (value 2) and `:583` (archetype tag), plus `CLASS_DEFAULTS.md:260` for
the 1.5 class default.

**C4 — Re-derive the kill-flip verdict on the archetype value.**
With −200 the drift torque ceiling (35000, `VOCABULARY.md:479`) is no longer "57× short": the value fits
inside a real torque member, so `drift.max_drift_torque` deserves a fresh look before the leg is declared
impossible and pushed into a pulse impulse 2000× outside the decoded 25..1000 range
(`FORCEPULSE.md:31`). The "cannot go into any torque member" sentence in §0 is false for the shipped −200.

**C5 — Two numbers are quoted without a pinned line.**
`ram` §5.1's `ImpactRoadAssistMaxTorque` 30000 (archetype) and `carrier` §1's `VehicleShovingTorque` 10000
(archetype) come from `DAMAGE_RULES.md` but no line is given; `CLASS_DEFAULTS.md:229` / `:286` give the
class 15000 / 20000. Add the archetype line numbers so the "already carried, exact" claim can be checked.

**C6 — Scope of claim 1 holds, and should be stated as such.**
"232 module sets" is exactly what `VOCABULARY.md:1415` reports; the 233 in `DAMAGE_MECHANISMS.md:15` counts
entity *roots* (one train entity carries two, `:28`). No edit needed — recorded so the two numbers are not
"fixed" into a contradiction later.

---

## Limits

* Static reads only; no build, no game, no re-decode of the 232 module sets. The 232/100000 population is
  taken from `VOCABULARY.md:1415` as the plans cite it; an independent recount (408 `*_vmodc` type-dictionary
  scan in `carrier` §2) did not reproduce the member's offsets and was not re-run here.
* Offsets in row 12 are the plan's own printed `struct.unpack_from` output; not re-executed.
* No plan was modified. This audit touches only this file. **Revert:** delete this file.

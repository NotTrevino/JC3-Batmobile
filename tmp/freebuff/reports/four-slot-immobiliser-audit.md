# Audit - the four-slot and Immobiliser plans against their source reports

**Plans audited (not edited):** `tmp/freebuff/reports/four-weapon-slot-build-plan.md` (plan A) and
`tmp/freebuff/reports/immobiliser-launch-payload-build-plan.md` (plan B).
**Named sources:** `tmp/freebuff/reports/T-WP13b.md` (plan A) and `tmp/freebuff/reports/T-WP4d.md` (plan B).
**Independent checks:** `Working/Translation/T_WP13B.md`, `Research/JC3Grab/WEAPON_WIRING.md`,
`Research/JC3Grab/INPUT.md`, `Research/BatmobileGrab/DRIVINGMODE.md`, the shipped
`BmGame/Config/DefaultInput.ini`, and a read-only re-read of the four cooked Batmobile packages with
`Tools/scripts/upk_read.py` (no package or plan was written).

Grades are about the figure and its stated provenance:

- **VERIFIED** - the named source says it, and the package/ini agrees.
- **OVERSTATED** - the figure is right (or partly right) but the named source does not say it, or says
  something weaker/different.
- **UNSUPPORTED** - neither the named source nor the package carries it.

---

## A. Plan A - four weapon slots

Plan A's own line numbers are given in the first column; "source" is `T-WP13b.md` unless stated.

| # | figure as planned | what the source says | independent check | grade |
|---|---|---|---|---|
| A1 | four button indices `1,2,3,4` (plan:47, 55-60) | "BmAK addresses **four** indices, one button each: 1, 2, 3, 4" (`T-WP13b.md:16-17`); `SelectVehicleWeapon(1/2/3)` bodies at `DRIVINGMODE.md:197,205,213` | `DefaultInput.ini:259` carries the literal `SelectVehicleWeapon 4`; the state bodies carry 1-3 | **VERIFIED** |
| A2 | index 1 = `XboxTypeS_B` (plan:130) | `T-WP13b.md:16` prints `XboxTypeB` (no `S_`) | `DefaultInput.ini:268` defines `XboxTypeS_B`, whose command list includes `QuickGadgetB`; `DRIVINGMODE.md:203-207` shows `QuickGadgetB` -> `SelectVehicleWeapon(1)`. `Working/Translation/T_WP13B.md:31,238` also prints `XboxTypeS_B` | **VERIFIED** (plan correct; named source's literal is truncated - see C2) |
| A3 | index 2 = `XboxTypeS_X` (plan:131) | `T-WP13b.md:16` prints `XboxTypeX` | `DefaultInput.ini:269` `XboxTypeS_X` includes `QuickGadgetX`; `DRIVINGMODE.md:193-197` `QuickGadgetX` -> `SelectVehicleWeapon(2)` | **VERIFIED** (same source defect) |
| A4 | index 3 = `XboxTypeS_Y` (plan:132) | `T-WP13b.md:17` prints `XboxTypeY` | `DefaultInput.ini:270` `XboxTypeS_Y` includes `QuickGadgetY`; `DRIVINGMODE.md:209-213` `QuickGadgetY` -> `SelectVehicleWeapon(3)` | **VERIFIED** (same source defect) |
| A5 | index 4 = `XboxTypeS_DPad_Up` (plan:133) | `T-WP13b.md:17` "4 -> `XboxTypeS_DPad_Up` (binding literal `SelectVehicleWeapon 4`)" | `DefaultInput.ini:259` - `XboxTypeS_DPad_Up` command list contains `SelectVehicleWeapon 4` / `ReleaseVehicleWeapon 4` | **VERIFIED** |
| A6 | slot property `main_weapon` (`id:851CAABE`, driver) (plan:8, 57, 70) | `T-WP13b.md:33-37` names the four properties but gives **no id for `main_weapon`** | `WEAPON_WIRING.md:11` "1st driver `id:851CAABE` = `main_weapon`"; `Working/Translation/T_WP13B.md:136` same | **VERIFIED** value / **OVERSTATED** provenance (the plan cites `T_WP13B.md §1, O2`, where the id does not appear) |
| A7 | second driver (`id:00568A74`) (plan:9, 58, 71) | `T-WP13b.md:35` "`secondary (id:00568A74)` | driver | 54 | 24" | `WEAPON_WIRING.md:12` "2nd driver `id:00568A74`, **no name found**" | **VERIFIED** |
| A8 | `mounted_weapon` (gunner) (plan:9, 72) | `T-WP13b.md:36` "`mounted_weapon` | gunner | 54 | 14" | `WEAPON_WIRING.md` slot tables (`:188`, `:305`) show it bound on gunners | **VERIFIED** |
| A9 | `mounted_weapon_2` (`id:AC0BC788`, gunner) (plan:10, 73) | `T-WP13b.md:37` names it, no id | `WEAPON_WIRING.md:14` "2nd gunner `id:AC0BC788` = `mounted_weapon_2`" | **VERIFIED** value / **OVERSTATED** provenance (id not in the named source) |
| A10 | spare pointer `id:8580BA42`, non-null on 0 (plan:11, 44, 83) | `T-WP13b.md:45-48` "`id:8580BA42` and `id:CA86AA17` ... present on all 54 roots, **non-null on none**" | `WEAPON_WIRING.md:18` "null on all 53 armed entities"; `objects` slot tables show no value behind it | **VERIFIED** |
| A11 | spare pointer `id:CA86AA17` (plan:11, 44, 84) | same lines `T-WP13b.md:45-48` | same | **VERIFIED** |
| A12 | "all four on 54/54 roots" (plan:10, 40) | `T-WP13b.md:33-37` roots carrying 54 each; `:88` oracle "four slots on 54/54 roots" | `Working/Translation/T_WP13B.md:19,232` same | **VERIFIED** |
| A13 | driver-slot histogram `0:15, 1:14, 2:24` (plan:43, cited "same, O4") | `T-WP13b.md` says only "max 2 driver slots" in its oracle list (`:88`); it prints **no histogram** and has no `O4` label | `Working/Translation/T_WP13B.md:56` "Driver slots per armed graph: {0: 15, 1: 14, 2: 24}" and `:234` oracle `O4` prints the same | **VERIFIED** value / **OVERSTATED** provenance (the histogram is in the generated doc, not the named report) |
| A14 | "max 3 weapon components, 7 graphs with an unbound one" (plan:46) | `T-WP13b.md:50-53` "max 3 weapon components ... 7 graphs with a component no slot points at" | `WEAPON_WIRING.md` §2c entities listed in plan §8 | **VERIFIED** |
| A15 | every index labelled "(battle)" (plan:57-60) | `T-WP13b.md:55-60` says B carries EMP in battle and Tracker in pursuit; it does **not** scope indices 1-4 to battle | no package evidence for a per-index mode gate | **OVERSTATED** (an inference presented as the index's state) |

Plan A's related prose claim "2 land-vehicle actions; the only selector actions (`NEXT_WEAPON`,
`PREV_WEAPON`) are keyboard-only and **on-foot**" (plan:45) is **OVERSTATED**: `INPUT.md:155,168`
labels both on-foot, but `INPUT.md:287` says explicitly "whether NEXT_WEAPON / PREV_WEAPON reach a
vehicle ... no file says which mode consumes them". The plan cites `T-WP13b §4b`, which does not
exist in the named report at all.

## B. Plan B - Immobiliser launch and payload

| # | figure as planned | what `T-WP4d.md` says | independent package re-read | grade |
|---|---|---|---|---|
| B1 | launcher offset **2428** -> `Batmobile_EMPMissile_Projectile_ForCars` (plan:4-6, 21, 55, 174) | `:13-14` both payload pointers at 2492 and 2428 resolve to `_ForCars` (export 5116); `:79-80`, `:135`, `:241-242` same | `Playable_Batmobile_SF` launcher 5114: `@2428 -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars` (`ObjectNCRProperty`); same in MK2 (5165) and Funhouse (5204) | **VERIFIED** |
| B2 | launcher offset **2492** -> same (plan:4-6, 22, 55, 175) | same `T-WP4d.md:13-14, 79` | same three packages: `@2492 -> Projectiles.Batmobile_EMPMissile_Projectile_ForCars` | **VERIFIED** |
| B3 | **export 5116** = `Batmobile_EMPMissile_Projectile_ForCars` (plan:5, 20, 41, 55) | `:14` "export 5116"; `:168` "5116 Batmobile_EMPMissile_Projectile_ForCars" | base package: launcher 5114, fired 5116, orphan 16 - exactly as quoted | **VERIFIED** |
| B4 | the **unused projectile archetype** = `Batmobile_EMPMissile_Projectile`, export 16, 0 incoming refs (plan:6, 51, 57, 180) | `:16` "export 16, which **no export in any of the four packages references**"; `:84` table column; reverse scan quoted as 0 | reverse walk of all 5,490 base exports: refs to `_ForCars` = **2**, refs to `Batmobile_EMPMissile_Projectile` = **0** | **VERIFIED** |
| B5 | "both already resolve ... in all three Batmobile packages (measured today, 6/6 PASS)" (plan:4-5, 55) | `:13-14` covers the pointers; the package table `:41` lists three packages; the probe `:129-136` shows Batmobile only, with MK2/Funhouse "identical verdicts" `:172` | probe: Batmobile, MK2 and Funhouse each PASS both pointers; **Joker (`Playable_BatmobileJoker_SF`, 3,388 exports) has no `Batmobile_EMP_Missile_Launcher` at all** (`find` = None) | **VERIFIED** for the three that have it; see C8 for the wording |
| B6 | damage / damage type / Immobiliser sound sit on **export 16** (plan:5-6, 65-70) | `:18-21` C2/C3: `Projectile.Damage 60.0` and `ExlposionSound` sit on export 16, which no export references; `:84-95` table, fired archetype 10 tags / 0 scalars / 0 AkEvents | fired 5116: tags=10, size=83, `@728` absent, `@968` absent; same in MK2/Funhouse | **VERIFIED** |
| B7 | `Projectile.MyDamageType` @712 is **`ClassProperty` (ObjectNCR)** (plan:70) | `:84-95` only says `@712` = `Core.RDmgType_BatmobileCannon`; it never names the property type | the tag is **`ObjectNCRProperty`** (type id 16) whose reference target is a Class; `ClassProperty` is type 8 and appears nowhere at 712 | **OVERSTATED** (wrong type name; the value and offset are right) |
| B8 | splice grows the fired export **83 -> 115 bytes (+32)** and **10 -> 14 tags** (plan:95-96, 107-111) | `T-WP4d.md:84-95` gives only the baseline (10 tags, size 83). It contains no splice, no 115, no +32 | baseline re-confirmed (tags=10, size=83); the post-splice numbers are not in the named source and were not re-run here | **UNSUPPORTED by the named source** (self-measured in the plan's own scratch run) |

## C. Corrections the plans need (plans not edited)

1. **Plan A - citations do not resolve.** `T-WP13b.md` has no numbered sections (`§1`, `§4a`, `§4b`)
   and no `O2`/`O4`/`O5` labels in its prose; the `O*` names exist only in
   `Working/Translation/T_WP13B.md:232-238`. Replace every "`T_WP13B.md` §n / On" with the generated
   doc's oracle lines or the underlying `WEAPON_WIRING.md` / `INPUT.md` lines.
2. **Plan A - button literals.** `T-WP13b.md:16-17` prints `XboxTypeB/X/Y` (no `S_`), while the plan
   prints `XboxTypeS_B/X/Y`. The plan is **right**: `DefaultInput.ini:268-270` defines
   `XboxTypeS_B/X/Y` and their command lists carry `QuickGadgetB/X/Y`, which
   `DRIVINGMODE.md:193-213` maps to `SelectVehicleWeapon(2/1/3)`. Cite the ini and DRIVINGMODE, and
   flag the report's truncated literal rather than inheriting it.
3. **Plan A - two slot ids are not in the named source.** `id:851CAABE` (`main_weapon`) and
   `id:AC0BC788` (`mounted_weapon_2`) come from `WEAPON_WIRING.md:11,14` (also
   `Working/Translation/T_WP13B.md:136`), not from `T-WP13b.md`. Add those citations to the §1 and §3
   tables.
4. **Plan A - histogram provenance.** `0:15, 1:14, 2:24` is in
   `Working/Translation/T_WP13B.md:56,234`; `T-WP13b.md` only says "max 2". Cite the generated doc or
   drop the histogram to a parenthetical.
5. **Plan A - the 54/53 denominator.** The plan's "non-null on 0 of 54" matches
   `T-WP13b.md:47` (54 roots, none non-null), but `WEAPON_WIRING.md:18` counts "all 53 armed entities".
   State both once: 54 roots, 53 armed, 0 pointing at a weapon behind either spare.
6. **Plan A - drop the per-index "(battle)" qualifier.** The source decodes one button per index; the
   battle/pursuit reuse it does decode is for B only (EMP vs Tracker, `T-WP13b.md:55-60`). X, Y and
   d-pad-up have no decoded mode scope.
7. **Plan A - the selector sentence.** Replace "keyboard-only and on-foot" (settled) with what
   `INPUT.md` says: both actions are labelled on-foot (`:155,168`) and **whether either reaches a
   vehicle is UNKNOWN** (`:287`). The plan currently cites a non-existent `§4b`.
8. **Plan B - "all three Batmobile packages".** Say "the three packages that carry
   `Batmobile_EMP_Missile_Launcher` (Batmobile, MK2, Funhouse); `Playable_BatmobileJoker_SF` has no
   launcher and 0 refs to either projectile". Otherwise a reader takes "three" as the size of the
   Batmobile set, while `T-WP4d.md:41` and the reverse scan both walk four packages.
9. **Plan B - the damage-type tag's type.** `@712` is `ObjectNCRProperty` (type 16) holding a Class
   reference, not `ClassProperty` (type 8). Fix the §2 table cell; the value
   `Core.RDmgType_BatmobileCannon` and the offset are correct.
10. **Plan B - label the splice as its own measurement.** `83 -> 115` bytes and `10 -> 14` tags are
    the plan's in-memory experiment (plan:95-96), not a `T-WP4d.md` figure; `T-WP4d.md` stops at the
    10-tag / 83-byte baseline. Keep the numbers, change the evidence label from "decoded" to
    "measured in this plan's scratch run", and re-run the splice on MK2/Funhouse as the plan's own
    step 5 already asks.

## D. Net result

- **Plan A:** 12 of 15 figures verified outright; 2 more (A6, A9) are right in value but cite the
  wrong file for an id, and A13's histogram is right but credited to a report that does not print it;
  the one genuine overstatement is the per-index "(battle)" qualifier (A15). No figure is wrong in
  value, and the `XboxTypeS_*` literals are more correct than the source report's.
- **Plan B:** all four required figures (2428, 2492, 5116, export 16) verified against both
  `T-WP4d.md` and the packages; the two defects are a mislabelled property type and a splice result
  presented without its provenance, plus the "three packages" scope wording.
- No plan was edited. This file is the only artefact. **Revert:** delete this file.

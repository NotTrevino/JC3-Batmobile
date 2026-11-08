# What `ArmourModeDamageReduction` actually does

**STATUS: done (report only).** No build tree, entity, parts file, ledger row or queue brief was written or
edited; nothing was launched.

**Provenance / revert.** New file `tmp/freebuff/reports/armour-mode-reduction-meaning.md`
(= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/armour-mode-reduction-meaning.md`), the output path the
brief names. **Revert = delete this file.**

Labels: **decoded** (file:line / offset), **derived** (rule + inputs), **UNKNOWN** (tried, where it would be).

---

## 0. Verdict

> **CONSISTENT with the operator fact**, and stronger than "consistent": on the shipped car the member is
> **authored to 0**, so armoured/battle mode applies **no reduction at all** — pursuit and battle take
> identical damage. The class default is **20**, and the archetype overrides it to **0**: the developers
> zeroed it on purpose. One caveat survives, kept as a second fact (see below): the **Joker** Batmobile has
> **no tag**, so its running value is the class default (20) or whatever the CDO holds — **UNKNOWN**, not 0.

| question | answer |
|---|---|
| what does the member do | `IntProperty` @ **6424** (`0x1918`), class default **20**; **1** script reader in the whole package — `RVehicleBatmobileBase.TakeDamage`, reference #14 in that body — where armoured mode multiplies the incoming direct hit |
| does any serialised package set a non-default value | **no.** `0` in the three that carry the tag (`Playable_Batmobile_SF`, `Playable_BatmobileMK2_SF`, `Playable_BatmobileFunhouse_SF`); the Joker archetype omits the tag |
| is it applied to the car's health | **yes** — `TakeDamage` on `RVehicleBatmobileBase`, i.e. the car's own `Pawn.Health` pool (1200 on 3 archetypes) |
| could it mean passengers / turret / a story upgrade | passengers **no** (separate Pawns, different `TakeDamage`); turret/weapons **no** (no per-part health; the weapon generator is a *separate* pool drained in the same body); a story-only armour upgrade **possible in principle but not decoded** — no writer exists among the 14 traced entry points, and the shipped value is 0, so if a story script raised it at runtime that write is **UNKNOWN** |
| reach, even if it were set | **direct hits only**: `TakeRadiusDamageFromWeapon` (explosions) and `TakesDamageFromRam` (being rammed) never read it |

---

## 1. The member, decoded

| fact | evidence |
|---|---|
| declaration | `IntProperty`, offset **6424** (`0x1918`), member of `RVehicleBatmobileBase` — `CLASS_DEFAULTS.md:242`, `:549`; `MODES.md:153`; `CONTROLS.md:165` (row 9734) |
| class default | **20** — `CLASS_DEFAULTS.md:242` (`BmGame\RVehicleBatmobileBase.g.cs:7290 (off 6424)`) |
| unit | **none stated** — `MODES.md:153` prints it as "int, undocumented scale"; `chase-09.md` F-70 records the unit as **STILL UNKNOWN** |
| shipped value | **0** in `Playable_Batmobile_SF.Batmobile`, `Playable_BatmobileMK2_SF.Batmobile_MK2`, `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` — `DAMAGE_RULES.md:578, 631, 658`; `CHAIN.json` shows three `RVehicleBatmobileBase.ArmourModeDamageReduction` rows, value `0` |
| Joker | **no archetype tag** — `MODES.md` §Gaps: "`ArmourModeDamageReduction` (Joker)" among the 5 serialised fields missing from at least one archetype; the running value is the class default/CDO, **UNKNOWN** (never 0 unless proven) |
| serialisation check | `MODES.md:304` `T-BM1: ArmourModeDamageReduction | PASS | serialized=True` |

Why "authored to 0" is the right reading and not "undeclared switch": a cooked UE3 archetype **omits** a
property that equals its class default (`MODES.md` §Gaps says this explicitly). The tag is **present** with
the value 0 on three assets, so 0 is not the default leaking through — it is a deliberate authored value that
differs from the class's 20.

---

## 2. Its readers: one function, one reference

`Research/BatmobileGrab/DAMAGE_RULES.json` → `functions` has the 14 traced entry points
(`TakeDamage`, `TakeRadiusDamageFromWeapon`, `TakesDamageFromRam`, `ShouldRadialDamageHit`,
`CanBatmobileDoImpactDamage`, `CalculateAndStoreImpactDamage`, `SetDamageLevel`, `SetArmouredMode`,
`DrainWeaponGeneratorForDamage`, `ExperienceAwarded`, `LoadHealth`, `GiveMaxEnergy`, `OnModifyHealth`,
`RVehicleCombatManager.GetDamageMod`).

A scan for the member name over that record returns **4** strings:

| path | meaning |
|---|---|
| `/functions/RVehicleBatmobileBase.TakeDamage/refs[14]/ref = RVehicleBatmobileBase.ArmourModeDamageReduction` | **the only reader** — a token-aligned reference in the 2,028-byte `TakeDamage` body |
| `/damage_values[151]`, `[204]`, `[231]` | the three archetype values (0, 0, 0) — value rows, not readers |

`DAMAGE_RULES.md` §3.1 states the same in prose: "**1** script function in the whole package reads that
field, and this body is it", and §3.6 puts it in the direct-hit row:
`GetDamageMod` (native) × `ArmourModeDamageReduction` (ships 0), "armoured/battle mode is the only mode gate".

### 2.1 Where the mode bit comes from

| member | verdict | evidence |
|---|---|---|
| `RVehicleBatmobileBase.SetArmouredMode` | **native**, 43 B export / **5 B** body / **1** parameter descriptor / 2 `exec<>` strings | `DAMAGE_RULES.md` §2 table |
| `ArmouredMode` (the bool the reader gates on) | a stored bool, read inside `TakeDamage` | `DAMAGE_RULES.md` §3.1 step 2 |

So the chain is: some native/script code calls `SetArmouredMode(true)` when battle mode engages → the bool
`ArmouredMode` is set → `TakeDamage` reads it and applies `ArmourModeDamageReduction`. **The multiplier is
only as real as the integer**, and the integer is 0.

---

## 3. What it is *not*: the other four candidates, tested

| candidate | what the files say | verdict |
|---|---|---|
| **passengers (Batman)** | the member lives on `RVehicleBatmobileBase` (the car). Batman is a `Pawn`; `Pawn.Health`/`Pawn.TakeDamage` is a different class, and the only Batmobile member that touches the player's bar is `OnModifyHealth` (116 B), which "takes an `Action`, casts the PC and calls `InstantUpdateHealth` — that is the **Batsuit** bar" (`DAMAGE_RULES.md` §4) | **no** |
| **the turret / weapons** | there is no per-part health on the class (`T-DM5`: "no per-part health table"); the weapons' survivability is the **weapon generator**, a separate pool: `DrainWeaponGeneratorForDamage` reads `WeaponGeneratorPower`, `bWeaponGeneratorShielding`, `WeaponUnavailableReason` (`DAMAGE_RULES.md` §3.1 step 7, §4) | **no** |
| **the car's health** | `TakeDamage` is the car's own incoming-damage entry; `Pawn.Health` = **1200** on all three Batmobile archetypes | **yes** |
| **a story-only armour upgrade** | no writer for the int among the 14 traced entry points (only the one reader). `SeqAct_ModifyHealth` exists, but it is a health seqact, and `RestoreArmour` / `RestoreArmourProportional` are health-restore names, not this field. A write from an untraced script or a console `Set` would not show up in this record | **possible, not decoded** — UNKNOWN (§7 U2) |

### 3.1 Reach: which damage paths it can even touch

| damage path | reader of `ArmourModeDamageReduction`? | consequence |
|---|---|---|
| direct hit (bullet, shell, melee) → `TakeDamage` | **yes** | the only path the mode can scale |
| radial / explosive → `TakeRadiusDamageFromWeapon` | **no** | explosions hit the same in both modes, even if the value were >0 |
| being rammed → `TakesDamageFromRam` | **no** (body begins `return true`) | ramming the Batmobile cannot be reduced by this field at all |
| outgoing ram → `CalculateAndStoreImpactDamage` | **no** (it reads only outgoing `Impact*`/`BattleModeImpact*` multipliers) | — |

So even the "armoured mode" label overstates it: the field is a **direct-hit-only** reduction, and it ships
disabled.

---

## 4. Against the operator fact

| operator statement | files | result |
|---|---|---|
| "battle (armour) mode and pursuit mode take identical damage" | shipped reduction = **0** on the playable car → the multiplier is neutral | **consistent**, and *by authoring* (class default 20 was overridden to 0) |
| the same claim for the **Joker** Batmobile | no tag → class default/CDO value, unknown | **UNKNOWN** — not a contradiction, an absence of evidence |
| "armour mode" as a damage *concept* | `SetArmouredMode` is native; `ArmouredMode` gates `TakeDamage` | the **gate** exists, the **reduction** does not run |

**Both facts are kept:** (1) the mechanism exists and is wired into `TakeDamage`; (2) the shipped value is 0
on the three packages that carry it, so in play the two modes are identical. Neither fact cancels the other —
a value row that is 0 is not the same statement as "no such rule", and the design intent (class default 20)
is not the shipped behaviour.

---

## 5. Ledger rows affected

| row | current wording | effect of this report |
|---|---|---|
| **`T-MD10`** (MOD-2 armour reduction, `dispo: keep`) | "`ArmourModeDamageReduction` = **0** (int, undocumented scale), identical on the three packages that serialise it (Funhouse, MK2, V2)" | **confirmed**; sharpen with: *read by exactly one function (`TakeDamage`, ref #14); direct hits only — radial and ram never read it; class default is 20, so 0 is an authored override, not a default; Joker has no tag (UNKNOWN).* Still `keep`. |
| **`T-DM3`** (no per-channel armour, `dispo: next`) | "one `TakeDamage` path, `ArmourModeDamageReduction` 0, a weapon-generator shield" | **confirmed**; the "0" can now be cited as an authored override with a single reader, which is what makes "one path, no per-channel armour" airtight |
| **`T-DM9`** (small arms do not move the bar) | silent on the mode field | unaffected; no edit needed |
| **`T-DM1`** (`Health` 1200) | — | unaffected; the field does not change the pool size |
| **`T-MD15`** (the hybrid itself) | — | unaffected, but worth knowing that "armour mode" in BmAK is a **gate with a zeroed multiplier**, not a health switch — relevant when the build decides what battle mode changes |

No `T-MD*` or `T-DM*` row needs a disposition change. The only text edit is `T-MD10`'s evidence column
(and optionally `T-DM3`'s parenthetical).

---

## 6. Consequences for the JC3 card

JC3 has no mode-gated incoming-damage multiplier of this kind, and the BmAK value is 0, so **nothing needs to
be carried**: the build's battle mode should leave `VehicleDamage` channels untouched for incoming damage,
which is what the operator sees. If a later card wants a *real* armour mode (a lore change, not a
translation), the BmAK number to start from is the **class default 20** — labelled as a default, never as the
shipped behaviour, and with the direct-hit-only reach stated.

**COMPROMISES: none.** The player fact and the files agree; nothing has to be accepted or approximated.

---

## 7. UNKNOWNs

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | the **unit/scale** of the int (is 20 = 20%?) | `MODES.md:153` prints "undocumented scale"; `chase-09.md` F-70 keeps it UNKNOWN; no arithmetic in `TakeDamage` is decoded (token-aligned trace, no expression tree) | one disassembly of `TakeDamage` around ref #14, or a probe that sets it to 20 and measures a hit |
| U2 | whether a **story/seqact** ever writes the field | 0 writers among the 14 traced entry points; `SeqAct_ModifyHealth` is health, not this | a full-package scan for writes to offset 6424 / the property ref, over every function (the trace covered 14) |
| U3 | the **Joker** running value (no tag) | archetype tag absent; class default 20 is declared, CDO not in the grab | the running game's `Default__RVehicleBatmobileBase` (a CDO read, probe), same gap class as `HealthRecoverRate` |
| U4 | whether `SetArmouredMode` also clamps the value | body is 5 B (1 parameter descriptor) = native stub, nothing readable | the exe's `execSetArmouredMode` |

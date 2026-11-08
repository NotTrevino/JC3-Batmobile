# `ExperienceAwarded`: the function that reads `HealthRecoverRate`

**STATUS: done (report only).** No build tree, entity, parts file, ledger row or queue brief was written or
edited; nothing was launched.

**Provenance / revert.** New file `tmp/freebuff/reports/regen-reader-function.md`
(= `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/reports/regen-reader-function.md`). **Revert = delete this file.**

Labels: **decoded** (file:line / offset / byte), **derived** (rule + inputs), **UNKNOWN** (tried, where it
would be).

---

## 0. Answer in six lines

| question | answer |
|---|---|
| which function reads `HealthRecoverRate` | **`RVehicleBatmobileBase.ExperienceAwarded`** — export **10862**, **218 B** export / **180 B** script, sha1 `5246ad97…`, `verdict: script`, 0 parm descriptors, 0 `exec<>` strings (so it is ours to read, not native) |
| what triggers recovery | **an XP award**, not a clock. The body reads `HealthRecoverRate`, `RGameInfo.GetDifficulty`, two int locals (`XpAwarded`, `TeethXpAwarded`), a float local (`HealthRecovery`), an int local (`HealthToRecover`), then `Core.Health` twice and adds. There is **no `WorldInfo.TimeSeconds`, no `SetTimer`, no `TimeSince` field** in the body. |
| any delay constant | **none.** The body has exactly **one** literal: **`2.0f` at script `+137`**. No seconds value, no threshold. |
| class-default value | **reachable and decoded: `HealthRecoverRate` = `ArrayProperty`, count **3**, `float [8.0, 4.0, 2.0]`** at `0x0ad4` (8220) — `CLASS_DEFAULTS.md:330`, `:637`; declared `TArray<float>` in `Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs:8872-8874` |
| does that match the operator's "regenerates out of combat"? | **partly.** A recovery *mechanism* exists and is difficulty-indexed (8 / 4 / 2 per award). An **out-of-combat timer is not in this body**; the package's name table does carry `UpdateReplenishingHealth` and `bReplenishHealth` (and `CMod_Pos_ReplenishingHealth`), so a separate out-of-combat path may exist elsewhere — **UNKNOWN** (§6 U2). Both facts are kept. |
| what 7976 must fetch live | the running `HealthRecoverRate` values (the class default may be overridden in a CDO), the difficulty index mapping, whether `UpdateReplenishingHealth` is a timer, and the units of the rate |

---

## 1. The record

From `Research/BatmobileGrab/DAMAGE_RULES.json → functions["RVehicleBatmobileBase.ExperienceAwarded"]`:

| field | value |
|---|---|
| `path` | `RVehicleBatmobileBase.ExperienceAwarded` |
| `index` | 10862 |
| `size` / `script_bytes` | 218 / **180** |
| `script_sha1` | `5246ad973ccd5c9eb82b7f71af91da1f3cb3230c` |
| `script_raw` | `Working/vendor/BmAKgrab/scripts/RVehicleBatmobileBase_ExperienceAwarded.hex` |
| `native_parm_descriptors` / `native_parm_bytes` | 0 / 0 → **script**, not a native thunk |
| `exec_strings_in_exe` | **0** (no `execExperienceAwarded` registration — consistent with a script body) |
| `verdict` | `script` |
| `constants` | **1**: `{"at": 137, "kind": "float", "value": 2.0}` |
| `walk` | `accepted_tokens` **43**, `bare_tokens` **17**, `unexplained_bytes` **33**, `unaligned_ref_candidates` 1, `unparsed_tail_bytes` 0 |
| `refs` | **25** (listed in §3) |

The 33 unexplained bytes are the operators (see §4): `Tools/scripts/bmak_damage.py`'s `TOKENS` table
(lines 70-81) names 43 of them but not the arithmetic/compare opcodes, which is why the expression tree is
not recoverable with the repo's tools as they stand.

---

## 2. The body, verbatim (180 bytes, offsets in decimal)

```
  0: 07 34 00 97 00 6c 2a 00 00 00 6d 2a 00 00 16 1c
 16: 3c fa ff ff 16 0f 00 6d 2a 00 00 00 6c 2a 00 00
 32: 0f 00 6a 2a 00 00 10 19 19 01 59 f5 ff ff 09 00
 48: c0 f4 ff ff 00 01 c0 f4 ff ff 0a 00 53 41 00 00
 64: 00 1c 54 41 00 00 16 01 5d 25 00 00 a2 00 6d 2a
 80: 00 00 00 6c 2a 00 00 16 0f 00 6b 2a 00 00 fa 38
 96: 44 ab 38 3f 00 6d 2a 00 00 00 6a 2a 00 00 16 25
112: 16 a1 00 6b 2a 00 00 fa 38 44 ab ab 38 3f 00 6c
128: 2a 00 00 00 6a 2a 00 00 16 1e 00 00 00 40 16 25
144: 16 16 0f 01 c2 f5 ff ff f9 92 01 c2 f5 ff ff 00
160: 6b 2a 00 00 16 1b 97 98 00 00 16 16 1b bc a4 00
176: 00 4a 16 04
```

Local-variable indices resolved by the tool: `0x2a6c` = **10860 `TeethXpAwarded` (int)**, `0x2a6d` =
**10861 `XpAwarded` (int)**, `0x2a6a` = **10858 `HealthRecovery` (float)**, `0x2a6b` = **10859
`HealthToRecover` (int)**; `0xf5c2` (= −2622) = **`Core.Health` (int)**, `0xf559` (= −2727) =
**`Core.WorldInfo`**, `0xf4c0` (= −2880) = **`Core.Game`**, `0x4153` = **`GetDifficulty.ReturnValue`**,
`0x4154` = **`RGameInfo.GetDifficulty`**, `0x255d` = **`HealthRecoverRate` (ArrayProperty)**,
`0x9897` = **`IsAlreadyDoingJob.ReturnValue`**, `0xa4bc` = **`NotifyFinished.FinishedAction`**.

---

## 3. The token trace the tool accepted (25 references, in byte order)

| # | at | token | target | kind |
|---:|---:|---|---|---|
| 0 | 4 | `EX_LocalVariable` | `ExperienceAwarded.TeethXpAwarded` (10860) | IntProperty |
| 1 | 9 | `EX_LocalVariable` | `ExperienceAwarded.XpAwarded` (10861) | IntProperty |
| 2 | 15 | `EX_FinalFunction` | `Core.ScriptTrace` (−1476) | Function |
| 3 | 22 | `EX_LocalVariable` | `ExperienceAwarded.XpAwarded` | IntProperty |
| 4 | 27 | `EX_LocalVariable` | `ExperienceAwarded.TeethXpAwarded` | IntProperty |
| 5 | 33 | `EX_LocalVariable` | `ExperienceAwarded.HealthRecovery` (10858) | **FloatProperty** |
| 6 | 41 | `EX_InstanceVariable` | `Core.WorldInfo` (−2727) | ObjectProperty |
| 7 | 47 | `EX_LocalVariable` | `Core.Game` (−2880) | (misaligned: a negative index on a local token) |
| 8 | 53 | `EX_InstanceVariable` | `Core.Game` | ObjectProperty |
| 9 | 59 | `EX_LocalVariable` | `GetDifficulty.ReturnValue` (16723) | IntProperty |
| 10 | 65 | `EX_FinalFunction` | `RGameInfo.GetDifficulty` (16724) | Function |
| 11 | 71 | `EX_InstanceVariable` | **`RVehicleBatmobileBase.HealthRecoverRate`** (9565) | **ArrayProperty** |
| 12 | 77 | `EX_LocalVariable` | `ExperienceAwarded.XpAwarded` | IntProperty |
| 13 | 82 | `EX_LocalVariable` | `ExperienceAwarded.TeethXpAwarded` | IntProperty |
| 14 | 89 | `EX_LocalVariable` | `ExperienceAwarded.HealthToRecover` (10859) | IntProperty |
| 15 | 100 | `EX_LocalVariable` | `ExperienceAwarded.XpAwarded` | IntProperty |
| 16 | 105 | `EX_LocalVariable` | `ExperienceAwarded.HealthRecovery` | FloatProperty |
| 17 | 114 | `EX_LocalVariable` | `ExperienceAwarded.HealthToRecover` | IntProperty |
| 18 | 126 | `EX_LocalVariable` | `ExperienceAwarded.TeethXpAwarded` | IntProperty |
| 19 | 131 | `EX_LocalVariable` | `ExperienceAwarded.HealthRecovery` | FloatProperty |
| 20 | 147 | `EX_InstanceVariable` | `Core.Health` (−2622) | **IntProperty** (write side) |
| 21 | 154 | `EX_InstanceVariable` | `Core.Health` | IntProperty (read side) |
| 22 | 159 | `EX_LocalVariable` | `ExperienceAwarded.HealthToRecover` | IntProperty |
| 23 | 165 | `EX_VirtualFunction` | `IsAlreadyDoingJob.ReturnValue` (39063) | BoolProperty |
| 24 | 172 | `EX_VirtualFunction` | `NotifyFinished.FinishedAction` (42172) | ObjectProperty |

**The literal:** `EX_FloatConst` at **+137**, value **`2.0`** (`1e 00 00 00 40`).

---

## 4. The statement reading (derived from the byte order; operators unnamed)

UE3 statement shape is `EX_Let (0x0F) <lhs> <rhs> EX_EndFunctionParms (0x16)`. Three `0x0F` tokens anchor
the body: **+21**, **+32**, **+88**, and a fourth at **+146**. Reading them with the reference table:

| statement | bytes | reading |
|---|---|---|
| 1 | `+21 0f` + `+22 00 6d2a0000` (XpAwarded) + `+27 00 6c2a0000` (TeethXpAwarded) | **`XpAwarded = TeethXpAwarded`** (a local alias; the two int locals are the function's XP inputs) |
| 2 | `+32 0f` + `+33 00 6a2a0000` (**HealthRecovery**) + `+38 10` … `+41 WorldInfo` … `+53 Game` … `+65 RGameInfo.GetDifficulty` … `+71 HealthRecoverRate` … `+77 XpAwarded` … `+82 TeethXpAwarded` | **`HealthRecovery = HealthRecoverRate[GetDifficulty()] … (XpAwarded, TeethXpAwarded)`** — the difficulty index comes from `RGameInfo.GetDifficulty`, the array is indexed at `+76`, and the XP locals are operands |
| 3 | `+88 0f` + `+89 00 6b2a0000` (**HealthToRecover**, int) + `+94` … `+100 XpAwarded` `+105 HealthRecovery` | **`HealthToRecover = f(HealthRecovery, XpAwarded)`** — a float `HealthRecovery` converted into the int pool increment |
| 4 | `+114 HealthToRecover` … `+119` … `+126 TeethXpAwarded` `+131 HealthRecovery` `+136 16` `+137 1e 00000040` (**2.0f**) `+143 25` (EX_IntZero) | a second expression on the same operands, clamped/compared against **2.0** and **0** |
| 5 | `+146 0f` + `+147 01 c2f5ffff` (**Core.Health**) + `+152 f9` `+153 92` + `+154 01 c2f5ffff` (**Core.Health**) + `+159 00 6b2a0000` (HealthToRecover) `+164 16` | **`Health = Health <op@+153> HealthToRecover`** — the only write to the health pool in the body |
| tail | `+165 1b 97980000` (`IsAlreadyDoingJob`) `+172 1b bca40000` (`NotifyFinished`) `+177 4a` `+179 04` | two virtual calls and `EX_Return` — the UI/health-bar notification path |

**What is NOT decodable with the repo's tools:** the operators themselves — `0x97` (+3, the `EX_JumpIfNot`
condition), `0x10` (+38), `0xA2` (+76, the array element/index), `0xA1` (+113), `0xFA` (+94, +119),
`0xF9` (+152), `0x92` (+153) — are **not in `bmak_damage.py`'s `TOKENS` table** (lines 70-81 cover
`0x00-0x48` only), so the arithmetic tree, the cast direction and the clamp are **UNKNOWN**. The 33
`unexplained_bytes` are exactly these. The operand *set* is decoded; the *formula* is not.

---

## 5. The trigger: an XP award, not a clock

Evidence that this body is not a timer, all from the same 180 bytes:

| a timer would need | present? |
|---|---|
| `WorldInfo.TimeSeconds` | **no** — the only `WorldInfo` use is the Context chain at `+41` that reaches `Game`/`GetDifficulty` (the same idiom `EjectFromVehicle` uses to reach `WorldInfo.TimeSeconds`, here reaching `GetDifficulty` instead) |
| `SetTimer` / `ClearTimer` | **no** — neither ref appears among the 25 |
| a `TimeSince…` / `LastDamageTime` field | **no** — the only stored time field on the class in the grab is `LastEjectFromBatmobileTime`, and it is not referenced here |
| a seconds constant | **no** — one literal, `2.0` |

So the decoded mechanism is: **XP is awarded → `ExperienceAwarded(TeethXpAwarded)` → difficulty-indexed
rate × XP → `HealthToRecover` → `Health += HealthToRecover`**. The class default rate ladder
**[8.0, 4.0, 2.0]** is the number of health units per XP at difficulty index 0 / 1 / 2 — *descending with
difficulty* (**derived**: array order read as the difficulty index the body feeds it, and the body feeds
`GetDifficulty()` as that index; the unit "health per XP point" is itself **UNKNOWN**, only the ladder is
decoded).

### 5.1 Where an "out of combat" timer could live

The name table (same package, `DAMAGE_RULES.md` §5) carries four names that are not this function:
`UpdateReplenishingHealth`, `bReplenishHealth`, `CMod_Pos_ReplenishingHealth`, `CanReplenishHealth`. None
was traced; `HealthRecoverRate` has **exactly one** reader (this function, §3 ref 11). So:

* the **award-driven** path is decoded and complete;
* a **time-driven** path is a *named but untraced* candidate — **UNKNOWN**, §6 U2.

This is the one place the operator fact and the files do not yet meet: "regenerates out of combat" needs a
timer, and the timer I can prove does not exist in this body. Both facts stand: an award-driven heal is
decoded; an out-of-combat heal is named in the package but not located.

---

## 6. What brief 7976 must fetch at runtime

| # | fetch | why the files cannot answer |
|---|---|---|
| F1 | the live `HealthRecoverRate` array (3 floats) | the class default is `[8.0, 4.0, 2.0]`, but a CDO or a gameplay `Set` can override it; `CHAIN.json` and `OFFSETS.json` carry **0** rows for it, so no archetype tag pins it |
| F2 | the difficulty→index mapping actually used | `RGameInfo.GetDifficulty` is a `FinalFunction`; its return value's domain (0..2? 0..3?) is not in the body |
| F3 | whether `UpdateReplenishingHealth` runs on a timer and with what period | named in the package, not traced; no `TimeSeconds` in the reader body |
| F4 | the unit of the ladder (health per XP point? per award?) | the body's operators are unnamed (§4), so the multiplication is inferred from operand order only |
| F5 | the value of `HealthRecovery`/`HealthToRecover` for a real award | they are **locals**, not fields; only a live read or a deeper trace shows the numbers |
| F6 | the "full on re-summon" half | `LoadHealth` (319 B) reads `BatmobileHealth`/`BatmobileEnergy`/`PersistentOptions`, and `GiveMaxHealth`/`GiveMaxEnergy` exist; which one a summon runs is not decoded here |

---

## 7. UNKNOWNs

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | the exact arithmetic (rate × XP? / 2? clamp at 2.0?) | 180-byte body dumped; operators `0x97/0x10/0xA2/0xA1/0xFA/0xF9/0x92` are outside `bmak_damage.py`'s `TOKENS` | extend the token table to the `0x80-0xFF` operator range (a new version of the script, per the project rule), then re-walk |
| U2 | the out-of-combat timer | not in this body; named only as `UpdateReplenishingHealth` / `bReplenishHealth` / `CMod_Pos_ReplenishingHealth` | a package-wide trace of those names, or the live probe (7976) |
| U3 | the difficulty index domain | `GetDifficulty` is `FinalFunction`, body not read here | its export body, or the live probe |
| U4 | the rate's live value | class default decoded `[8,4,2]`; no archetype tag, no CDO in the grab | 7976 |
| U5 | the "full on re-summon" carrier | `LoadHealth`/`GiveMaxHealth` both exist; neither traced | 7976, or a trace of the summon path |

---

## 8. Ledger / cards touched

| record | effect |
|---|---|
| `ARM-5` (the regen question) | **mechanism = yes** and now *named*: `ExperienceAwarded`, difficulty-indexed `[8,4,2]`; **timer = UNKNOWN** (named, untraced) |
| `T-DM1` (`Health` 1200) | unaffected in value; the recovery ladder is a separate axis |
| `T-DM4` (destruction thresholds) | unaffected |
| a new card for out-of-combat regen (does not exist yet) | this report is its input: the award path is decoded, the timer path is a named candidate for 7976 |

**COMPROMISES: none.** The award-driven recovery is fully carried by decoded evidence; the out-of-combat
half is a *missing capability* to be carded (per the operator rule: report the carrier or write the exact
missing capability as a new card), not a number to approximate.

---

## 9. Commands run this pass (verbatim, trimmed)

```
python (read RESEARCH/BatmobileGrab/DAMAGE_RULES.json functions.ExperienceAwarded)
  keys ['path','index','size','script_bytes','script_sha1','script_raw','fields',
        'native_parm_descriptors','native_parm_bytes','refs','constants','walk','verdict','exec_strings_in_exe']
  index 10862  size 218  script_bytes 180  verdict script
  refs len 25   constants len 1  -> {'at': 137, 'kind': 'float', 'value': 2.0}
  walk: accepted_tokens 43  bare_tokens 17  unexplained_bytes 33  unaligned_ref_candidates 1

python (dump Working/vendor/BmAKgrab/scripts/RVehicleBatmobileBase_ExperienceAwarded.hex)
  bytes 180   (hex shown in §2)

grep -rn "HealthRecoverRate" Research/BatmobileGrab/CLASS_DEFAULTS.* Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs
  CLASS_DEFAULTS.md:330  | 152 | 0x0ad4 | 8220 | HealthRecoverRate (RVehicleBatmobileBase) | ArrayProperty |
                          count=3 float [8.0, 4.0, 2.0] | decoded | BmGame\RVehicleBatmobileBase.g.cs:8872 (off 8220)
  CLASS_DEFAULTS.md:637  | 8220 | HealthRecoverRate | count=3 float [8.0, 4.0, 2.0] |
  RVehicleBatmobileBase.g.cs:8874  public unsafe BmSDK.TArray<float> HealthRecoverRate

sed -n '70,81p' Tools/scripts/bmak_damage.py   (TOKENS table: 0x00-0x48 only; no 0x80+ operators)
```

**Not done:** no script was modified (the missing operators would need a new `bmak_damage2.py`); nothing was
installed or launched. **Revert = delete this file.**

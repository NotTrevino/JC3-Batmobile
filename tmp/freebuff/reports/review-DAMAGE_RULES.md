# Review: the `Function` export layout recovery in `Research/BatmobileGrab/DAMAGE_RULES.md` §1

VERDICT: **PASS WITH ONE ERROR — the layout recovery holds field for field, but the body is one byte shorter than the note says, so its body sizes, its `ScriptSize == len + 1` rule, its 1-byte `0x04` script anchor and its `TakesDamageFromRam` tail all inherit that single byte error. Every literal the note quotes for the three decoded damage functions re-decodes exactly, and both traced damage rules trace to exact bytecode.**

Subject: `Research/BatmobileGrab/DAMAGE_RULES.md` (678 lines), §1 layout, §2 body sizes, §3.1 / §3.4 rules, and the constants quoted for `TakeDamage`, `TakeRadiusDamageFromWeapon`, `DrainWeaponGeneratorForDamage` (plus `TakesDamageFromRam`, which §3.4 decodes too).

## 1. Method

A new tool, `Tools/scripts/bmak_damage_layout_audit.py`, re-parses `BmGame.upk` with **its own reader** — signature, chunk container, name/import/export tables, no import of `upk_read.py` or `bmak_damage.py` — and re-derives every claim from the raw bytes. Each head field is tested against an **oracle over all 29,620 `Function` exports**, not just the traced functions. The body length is tested by a **token scan**: a body of the right length is consumed exactly by a token walk, a body cut short leaves a partial final token.

A second, independent reader (`upk_read.Package`, pre-existing) was used to re-locate the same exports, so the audit's offsets do not rest on one implementation (`tmp/freebuff/scratch/x_final.py`, output in §6).

Package: **214,757,637** bytes, version 863, licensee 32995, 84,813 names, 3,268 imports, 177,031 exports, **29,620** of them `Function`.

## 2. The three functions, re-parsed from the raw bytes

Bytecode boundary = offset 22 + `ScriptSize` @18. The note's boundary = `len(export) - 38`.

| function | export | file offset | size | ScriptSize | body (audit) | body (note) | body sha1 (audit) |
|---|---:|---:|---:|---:|---:|---:|---|
| `TakeDamage` | 10436 | 16,877,887 | 2,066 | 2029 | **2029** | 2028 | `f5b3fde67e9228623d598daca8b0a1f27d354837` |
| `TakeRadiusDamageFromWeapon` | 10416 | 16,876,770 | 326 | 289 | **289** | 288 | `d311fcfe1186448fed2743e803960558dadca5d5` |
| `DrainWeaponGeneratorForDamage` | 10231 | 16,861,640 | 360 | 323 | **323** | 322 | `e953a6f723d0893b878ddb046e819f9a6cb33cac` |
| `TakesDamageFromRam` (§3.4) | 10595 | 16,894,143 | 45 | 8 | **8** | 7 | `f3a2180b2691eb6a13645b7c48a0e70a26e1511e` |

Both readers agree on export index, file offset, size and body sha1; the two sha1s differ only between the audit's length and the note's. Head fields resolved to objects — the independent check on offsets 2/6/10/14:

| function | Next @2 | SuperField @6 | Children @10 | Line @14 |
|---|---|---|---|---|
| `TakeDamage` | `RVehicleBatmobileBase.InGodMode` | `Core.TakeDamage` | `…TakeDamage.DamageAmount` | 3041 |
| `TakeRadiusDamageFromWeapon` | `RVehicleBatmobileBase.EquipSecondaryWeapon` | `Core.TakeRadiusDamageFromWeapon` | `…TakeRadiusDamageFromWeapon.InstigatedBy` | 425 |
| `DrainWeaponGeneratorForDamage` | `…TriggerWeaponGeneratorScarecrowBonus` | `None` | `…DrainWeaponGeneratorForDamage.HitNumber` | 467 |
| `TakesDamageFromRam` | `RVehicleBatmobileBase.GetCurrentSideSwipeTarget` | `None` | `…TakesDamageFromRam.Target` | 12 |

Every field name, order and width in the note's §1 table is confirmed. The trailer is 15 bytes (`17` on 145 exports) and always ends in the export's own `FName` + a zero number — the note's `name FName @size-8` / `number @size-4` rows are exact (29,620/29,620 each).

## 3. The one error: the body is one byte longer than the note says

`ScriptSize` is a **byte count**. `ScriptSize − (len(export) − 38)` is `+1` in **29,475** exports and `−1` in **145**: the note's slice cuts the last body byte in 99.5% of the package.

| body length used | token scan ends exactly on the last byte | of | % |
|---|---:|---:|---:|
| `ScriptSize` (= @18) | **26,039** | 29,620 | **87.9** |
| `ScriptSize − 1` (= `len(export) − 38`, the note) | 14,456 | 29,620 | 48.8 |
| `ScriptSize + 1` | 1,531 | 29,620 | 5.2 |

The cut byte is not padding: **17,345** bodies end in `04 0b` (`return;`) and **8,451** in `04 3a <4-byte ref>` (`return <ref>`); under the note's slice they end on a bare `04` or a 3-byte operand. `TakeRadiusDamageFromWeapon` is one of the second group: its body ends `04 3a a6 28 00 00`, the note's ends `04 3a a6 28`.

Consequences inside the note, all reproduced: §2's body column is one short on every row (2,028 / 288 / 322 / 7 → 2029 / 289 / 323 / 8); anchor `B_script_size_is_len_plus_one` is false; anchor `C_thinnest_script_is_return` is false in both frames (the one-byte bodies are `0b`/`EX_Nothing`, 1,544 of them, and `04` alone is never a body); §3.4's "4 trailing bytes that do not form a complete descriptor… the tail is UNKNOWN" is an artefact of the missing byte — the 4 bytes `3a 60 29 00 00` do complete, and the reference resolves to export 10592 `RVehicleBatmobileBase.TakesDamageFromRam.ReturnValue`, so the reading the note **withdrew** in §3.4 was correct.

Two smaller §1 errors: `trailing i32 @size-16 is a flags word` — `@size-16` is the body's last byte in 29,475 exports (of 2,066 total size, `size-16` = 2,050 = `22 + 2029 − 1`); and `pre-name word … always 0x0002xxxx` — the high half takes `0x0002`, `0x0082`, `0x0042`, `0x00c2`, `0xffff`, `0x0012`, `0x0004`, `0x0008`, so it holds only as a bit test (bit 17) and not for the 145 exports with a 17-byte trailer.

## 4. Constants: no error found

A float literal is a `0x1e` byte whose next four bytes decode to a plausible source float. Every one is listed, so a constant the note missed would appear.

| function | `0x1e` bytes | distinct values | note's claim |
|---|---:|---|---|
| `TakeDamage` | 9 | 0.5, 1.0, 2.0, 2.5, 5.0, 1000.0 | "9 found, distinct 0.5, 1.0, 2.0, 2.5, 5.0, 1000.0" — **match** |
| `TakeRadiusDamageFromWeapon` | 9 | 0.0, 0.1, 0.5, 1.0, 1500.0 | "0.0, 0.1, 0.5, 1.0, 1500.0" — **match** |
| `DrainWeaponGeneratorForDamage` | 8 | 0.0, 0.05, 0.5, 1.0 | "8 found, distinct 0.0, 0.05, 0.5, 1.0" — **match** |
| `TakesDamageFromRam` | 0 | — | "not a literal (constants: 0)" — **match** |

Offsets (the note quotes none): `TakeDamage` `1000.0`@486, `2.5`@516, `2.0`@606, `1.0`@636, `2.0`@1395, `0.5`@1773, `0.5`@1778, `5.0`@1783, `1.0`@1791 · `TakeRadiusDamageFromWeapon` `1.0`@3, `0.5`@112, `0.0`@119, `0.0`@134, `1500.0`@159, `0.5`@174, `0.1`@192, `1.0`@205, `1.0`@226 · `DrainWeaponGeneratorForDamage` `0.0`@148, `1.0`@159, `0.05`@178, `0.5`@218, `0.5`@236, `0.0`@251, `1.0`@271, `1.0`@290. No `0x1e` byte in those bodies failed the plausibility test, so nothing is unaccounted for.

Also checked for the same three functions: the note's `exec<>` column in `BatmanAK.exe` — `3 / 0 / 0` reproduces as a substring count, but one of the three is `execTakeDamageFromChainGun`, so the registrations of the exact name are **2**. The note's conclusion (the count does not decide native-vs-script; the body does) is unaffected. The `parm descs` column (0 / 0 / 0) is confirmed, and the note's anchor `E_native_parm_refs_own_properties` holds over the whole package: **3,407/3,407** `29 <ref>` descriptors in **1,825** stubs name a property of the function they sit in.

## 5. Two rules traced to bytecode

### 5.1 §3.1 `ArmouredMode` → `ArmourModeDamageReduction`

Gate at body 108: `07 cf 00` = `JumpIfNot`, operand 207, condition at 111 `2d 01 ff 26 00 00` — the instance variable `RVehicleBatmobileBase.ArmouredMode` (object index 9983, a `BoolProperty`). Statement at 117..143:

```
0f 00 c3 28 00 00  91 90 00 c3 28 00 00  93 2c 64  01 06 26 00 00  16 16  2c 64  16
```

Decoded with each operator's parm list closed by `0x16` (the nesting balances exactly and the statement ends on the next `0x0f` `Let`):

```
RVehicleBatmobileBase.TakeDamage.DamageAmount
  = 0x91( 0x90( DamageAmount, 0x93( 100, ArmourModeDamageReduction ) ), 100 )
```

`ArmourModeDamageReduction` sits at body 134; `100` occurs exactly twice (`2c 64`, a one-byte `IntConstByte`); the field is read by exactly **1** script function in the package, and that is `TakeDamage`; every archetype ships it as `IntProperty = 0` (`Playable_BatmobileFunhouse_SF.BatmobileFunhouse`, `Playable_BatmobileMK2_SF.Batmobile_MK2`, `Playable_Batmobile_SF.Batmobile`). Read as a percentage cut — `(DamageAmount * (100 − reduction)) / 100` — the factor at the shipped value is exactly 1, so the rule **holds**: armoured mode reduces incoming damage by nothing as shipped. Which of `0x90`/`0x91` is multiply and which is divide is not established here (§7), and the conclusion survives either assignment because the reduction is 0. The one thing this trace cannot pin is `0x07`'s offset base: the two plausible bases give targets 207 and 318, neither a statement start — but both are past the statement's last byte 142, so "not `ArmouredMode` → skip the reduction" holds under either.

### 5.2 §3.4 `TakesDamageFromRam` returns true unconditionally

Body, **8** bytes, in full: `04 27 04 3a 60 29 00 00`.

- `04 27` = `EX_Return` `EX_True` → `return true`, first statement, no condition, no field read.
- `04 3a 60 29 00 00` = a second `EX_Return` whose operand `60 29 00 00` (= 10592) resolves to `RVehicleBatmobileBase.TakesDamageFromRam.ReturnValue`, a `BoolProperty` of this very function.

The note's 7-byte body hashes `1aa78f331a90f55e8fb9f173dcc80128458f4030`; `--check` reproduces that hash from the 7-byte slice, so the note's numbers are internally consistent — the slice is simply one byte short. The rule (`return true`, no gate, no archetype value can switch it off from here) **holds**; the "tail is UNKNOWN" sentence is the cost of the one-byte error, and the note's withdrawal of the `ReturnValue` reading is wrong.

## 6. Commands and outputs

`uv run python Tools/scripts/bmak_damage_layout_audit.py --write` (final run, abridged to the claim list):

```
wrote Research\BatmobileGrab\DAMAGE_LAYOUT_AUDIT.json
wrote Research\BatmobileGrab\DAMAGE_LAYOUT_AUDIT.md
verdict: STRUCTURE HOLDS; BODY LENGTH IS ONE BYTE SHORT
  L1   PASS  u16 prefix at 0 is constant 0 on every Function export
  L2   PASS  Next @2 is the UField sibling link
  L3   PASS  Children @10 is the first child property (the first parameter)
  L4   FAIL  ScriptSize @18 == len(script) + 1
  L5   FAIL  Script @22 is len(export) - 38 bytes
  L6   FAIL  trailing i32 @size-16 is a flags word
  L7   FAIL  pre-name word @size-12 is always 0x0002xxxx
  L8   PASS  name FName @size-8 is the function's own name; number @size-4 is 0
  L9   FAIL  anchor C: the thinnest script in the package is one byte and it is 0x04
  L10  PASS  anchor F: a 0x1c token is followed by a Function export in 99%+ of hits
  L11  PASS  UEViewer stops after Children for GAME_Batman4
  L12  PASS  UEViewer reads ScriptSize bytes of script
  L13  FAIL  body B column: TakeDamage 2,028 / TakeRadius 288 / Drain 322
  L14  PASS  TakeDamage body literals: 9 found, distinct 0.5/1.0/2.0/2.5/5.0/1000.0
  L15  PASS  TakeRadiusDamageFromWeapon body literals: 0.0/0.1/0.5/1.0/1500.0
  L16  PASS  DrainWeaponGeneratorForDamage body literals: 8 found, distinct 0.0/0.05/0.5/1.0
  L17  FAIL  TakesDamageFromRam body is 7 bytes (sha1 1aa78f33...); its 4 trailing bytes
  L18  PASS  ArmourModeDamageReduction is read by exactly 1 script function
  L19  PASS  LowHealthWarningLevel has exactly 1 reader
  L20  PASS  HealthRecoverRate is read by exactly 1 script function (ExperienceAwarded)
  L24  PASS  `exec<>` count in the exe: TakeDamage 3, TakeRadius 0, Drain 0
  L21  PASS  anchor A_super: SuperField of TakeDamage resolves to an inherited TakeDamage
  L22  PASS  anchor A_children: Children of TakeDamage is TakeDamage.DamageAmount
  L23  PASS  anchor E_native_parm_refs_own_properties
```

`uv run python Tools/scripts/bmak_damage_layout_audit.py --check`:

```
json: PASS
md: PASS
check: PASS
exit=0
```

Independent reader (`uv run python tmp/freebuff/scratch/x_final.py`, abridged — all four blocks follow this shape):

```
reader: Package
raw bytes: 214757637 image bytes: 356085334 exports: 177031
RVehicleBatmobileBase.TakeDamage -> 10436

TakeDamage  export 10436  file 16,877,887  size 2066
  u16@0=0 Next=10419 Super=-2500 Children=10435 Line=3041 ScriptSize=2029
  body(ScriptSize) 2029 bytes sha1 f5b3fde67e9228623d598daca8b0a1f27d354837
  body(note)       2028 bytes sha1 b00acfae06bd5bcf95606c6273f73fc70bc199d5
  trailer 15 bytes: 00 00 00 02 48 02 00 00 29 01 00 00 00 00 00
  last 6 body bytes: 16 06 40 0b 04 0b
RVehicleBatmobileBase.TakeRadiusDamageFromWeapon -> 10416

TakeRadiusDamageFromWeapon  export 10416  file 16,876,770  size 326
  u16@0=0 Next=10400 Super=-1635 Children=10415 Line=425 ScriptSize=289
  body(ScriptSize) 289 bytes sha1 d311fcfe1186448fed2743e803960558dadca5d5
  body(note)       288 bytes sha1 b05295b1a5371efaa0b93a9770f45a542427cd78
  trailer 15 bytes: 00 00 00 02 48 82 00 81 29 01 00 00 00 00 00
  last 6 body bytes: 04 3a a6 28 00 00
```

Corpus oracle for the body length (`uv run python - <<'PY'` on the audit package class, counts over all 29,620 `Function` exports):

```
0x06/0x07 tokens 74844 absolute-target-is-Let 2060 relative-target-is-Let 350
TakeDamage body[207] = 0x00 body[318] = 0xff
```

Descriptor anchor E (`uv run python - <<'PY'` over every `29 <ref>` stub):

```
descriptor stubs (29 refs + 0b): 1825 | refs whose outer is that function: 3407 | not: 0
TakeDamage 0x29 descs: 0
TakeRadiusDamageFromWeapon 0x29 descs: 0
DrainWeaponGeneratorForDamage 0x29 descs: 0
```

`exec<>` counts in `BatmanAK.exe` (55,101,440 bytes), by string:

```
TakeDamage occurrences: 2 | bare substring: 3
TakeRadiusDamageFromWeapon occurrences: 0 | bare substring: 0
DrainWeaponGeneratorForDamage occurrences: 0 | bare substring: 0
TakesDamageFromRam occurrences: 0 | bare substring: 0
GetDamageMod occurrences: 1 | bare substring: 1
31448519 execTakeDamageFromChainGun
38072304 execTakeDamage
38075592 execTakeDamage
```

Claim tally from `DAMAGE_LAYOUT_AUDIT.json`:

```
24 Counter({'PASS': 17, 'FAIL': 7})
['L4', 'L5', 'L6', 'L7', 'L9', 'L13', 'L17']
```

## 7. Files written

- `Tools/scripts/bmak_damage_layout_audit.py` — new; `--write` regenerates both artifacts, `--check` re-derives every number from `BmGame.upk` / `BatmanAK.exe` / `UnTypeinfo.h`, diffs both and exits 1 on drift.
- `Research/BatmobileGrab/DAMAGE_LAYOUT_AUDIT.json` — machine-readable record (package stats, head-oracle counters, body-length test, trailer histogram, per-function head + body + every `0x1e` byte, both rule traces, the exe counts, 24 claims).
- `Research/BatmobileGrab/DAMAGE_LAYOUT_AUDIT.md` — the same, rendered.
- `tmp/freebuff/scratch/x_final.py` — the independent cross-check through `upk_read.Package`.

`DAMAGE_RULES.md` and its `DAMAGE_RULES.json` were **not** edited (they belong to another task). The correction this review implies for it: `Script` is `ScriptSize` bytes at offset 22, the export ends in a 15-byte trailer (17 on 145), and §2's body column, anchor B, anchor C, and the §3.4 tail sentence need the +1.

## 8. UNKNOWNs

- **Opcode semantics above `0x7f`.** `0x90`, `0x91`, `0x93`, `0xb1` are decoded only as parm-list operators (each operand list closed by `0x16`, nesting balances exactly). Which of `0x90`/`0x91` is multiply and which is divide is not established: the note's token table stops at `0x2e`, no local file documents the rest, and a runnable oracle (the game's VM) is outside the read-only inputs. The §3.1 conclusion does not depend on it because the reduction ships as 0.
- **`0x07`'s jump-offset base.** Neither "absolute script offset" (207) nor "relative to the end of the instruction" (318) lands on a statement start in `TakeDamage`; a corpus test is meaningless without a full statement parser, and this audit did not build one. The gate relation holds under both bases (both targets are past the guarded statement), but the base itself is UNKNOWN.
- **The trailer's own fields** (the 7 bytes before the `FName`): length, constant tail and effect on the body boundary are decoded, the field meanings are not. The 145 exports with a 17-byte trailer are counted, not explained.
- **`Next` / `SuperField`** are checked for resolution and class (0 or a `UField`-subclass export; negative = import), not by walking the `UField` chain in order.
- **The third `execTakeDamage` hit** is a prefix match inside `execTakeDamageFromChainGun`; whether that string is a registration of a different function or a duplicate table entry was not resolved, and it does not affect the native-vs-script verdict.

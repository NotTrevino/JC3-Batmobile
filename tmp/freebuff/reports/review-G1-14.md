# Independent review — G1-14 · Damage rules, health, armour, regeneration

Reviewer: not the author. Read-only pass: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified. Only this file was written. No game launched, no commit.

Card: `GRAB_BACKLOG.md:470-479` (deps G1-08, serves ARM-1…6). Tracker row: `GRAB_BACKLOG.md:1282`.
MODLOG section: `MODLOG.md:8246` (§"G1-14 · Damage rules — done (2026-10-25)").
Outputs: `Research/BatmobileGrab/DAMAGE_RULES.md` (290 lines),
`Research/BatmobileGrab/DAMAGE_RULES.json` (6,730 lines, machine source),
`Tools/scripts/bmak_damage.py` (462 lines).

**Machine source read for this review:** `DAMAGE_RULES.json` (`functions` 14 entries, `missing: []`,
`damage_values` 251 rows, `field_references` 5 fields, `regeneration`, `anchors`),
`Working/vendor/BmAKgrab/scripts/*.hex` (14 bodies, gitignored — `Working/` is ignored at
`.gitignore:103`, so R10 is not broken), `Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs`, and the
tool's own `Package` reader re-run for the package-level counts.

## VERDICT: needs rework (narrow)

The structural work is real and independently reproducible: the `Function` export layout holds up
under all seven booleans `--check` prints, the native/script split is body-derived and recorded per
function (`functions.*.verdict`), the armoured-mode reduction (0), the health (1,200), the impact
numbers and the reader counts all match the JSON exactly, and the `TakesDamageFromRam` correction to
`POSTMORTEM_DAMAGE.md` is a genuine finding. Two of the three functions the card asked for are
closed correctly.

But the document is not the script's output — it is hand-written prose beside a JSON, and
`--check` never reads the `.md` — so the wrong numbers below survived. Four of them are in tables
that T-11/T-14/G2-28 will copy (missile damage, a literal list per function, a field claimed read
that is not referenced). None of the faults is deep: they are all fixable by deriving the prose
tables from `DAMAGE_RULES.json` instead of from an ad-hoc scan.

## Check output (verbatim)

```
$ python Tools/scripts/bmak_damage.py --check
anchors: {'A_super_is_parent_take_damage': True, 'A_children_is_first_param': True, 'B_script_size_is_len_plus_one': True, 'C_thinnest_script_is_return': True, 'D_name_word_is_own_name': True, 'E_native_parm_refs_own_properties': True, 'F_final_function_token_is_call': True}
check: PASS
EXIT=0
```

Note for the record: `--check` returns 0 on `json.dumps(old, sort_keys=True) == json.dumps(doc,
sort_keys=True)` (`bmak_damage.py:453-457`) — it proves the JSON is reproducible, and prints the
anchors without asserting them separately (an anchor that had always been `False` would also
"PASS", since the stored file would agree with itself).

## Out paths and Done criterion

Out paths exist: `DAMAGE_RULES.md` ✓, `DAMAGE_RULES.json` ✓ (`--write` produces the JSON and the 14
raw bodies; the `.md` is written by hand). Card Done = "every damage-related field listed with value
and source; each script function either decompiled into the file or marked `native` with proof;
regeneration answered yes/no/unknown with evidence."

`--check` verifies **none** of those three clauses:

- it does not read the `.md` at all (contrast `jc3rebeldrop.py`, which rebuilds its `.md` byte for
  byte and diffs it), so doc↔JSON drift is structurally undetectable — exactly the failure mode in
  issues 1–5 below;
- "decompiled into the file" is not what the note does: it records an ordered symbol trace, and
  `DAMAGE_RULES.md:266-269` says control flow is not resolved. The card's wording and the
  deliverable diverge, and the note's own §7 is honest about it — the tracker row's "14 entry
  points: 5 native, 9 script" is the part that is machine-recorded (`functions.*.verdict`; 5
  `native` / 9 `script` confirmed);
- "every damage-related field listed" is only true of the JSON (251 rows with
  class/archetype/name/type/value/`named_by`); the `.md` tables list a selection.

## Issues

### 1. (data, R4) The missile damage row is wrong — `DAMAGE_RULES.md:188-189`

Doc:

```
| `Batmobile_Missile_*` | `Projectile.Damage` | 60 |
| `Batmobile_Missile_*` (Joker) | `Projectile.Damage` | 250 |
```

`DAMAGE_RULES.json → damage_values`:

- `RBatmobileMissile | Playable_Batmobile_SF.Batmobile_Missile_Projectile | Projectile.Damage = 250.0`
  (same 250 in `Playable_BatmobileMK2_SF` and `Playable_BatmobileFunhouse_SF`);
- `RBatmobileMissile | Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile | Projectile.Damage = 60.0`;
- `RBatmobileMissile | Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile | Projectile.Damage = 250.0`.

So 250 is the **ordinary** missile, 60 is the **EMP** missile, and the "(Joker)" split is a fiction —
the non-Joker missile is 250 as well. This is the one number a reader would take to G2-28's
hits-to-kill table, and it is off by 4×.

### 2. (data) "Each projectile also carries `Projectile.MyDamageType`" — `DAMAGE_RULES.md:191`

14 of the 26 projectile archetypes in `damage_values` carry `Projectile.MyDamageType`; **12 do not**:
`Batmobile_Heavy_Cannon_BodyShot_Projectile`, `..._HeadShot_Projectile`,
`..._Fully_Upgraded_Projectile`, `..._EMPMissile_Projectile_ForCars` — each in the SF, MK2 and
Funhouse packages. "Each" is an over-claim; the per-type multiplier is also therefore absent for
those four.

### 3. (data, R5-flavoured) `DAMAGE_RULES.md:203` conflates two members

```
| weapons fired | projectile archetypes | `Projectile.Damage` 50/75/110/250, radius 350 | per weapon |
```

110 is `RBasicProjectile.TurretShotDamage`, not `Projectile.Damage`; the EMP missile's 60 is missing
from the list. A summary row that names one field and quotes another field's values is the same
class of mistake the postmortem's R5 warning is about (member name standing in for behaviour/field).

### 4. (R11) Three literal lists in the prose are not in the JSON — and do not match it

| doc | claim | `DAMAGE_RULES.json → functions.*.constants` |
|---|---|---|
| `:116` §3.2 | "literals **1500.0, 0.5, 0.1, 1.0, 0.0**" (`TakeRadiusDamageFromWeapon`) | `1.0@3, 0.0@119, 1500.0@159, 0.1@192` — **no 0.5** |
| `:218` §4 | "literals **0.05, 0.5, 1.0**" (`DrainWeaponGeneratorForDamage`) | `0.05@178` only |
| `:214` §4 | "Literals `9999999` … and `0.0`" (`LoadHealth`) | `9999999@182` only |

I scanned the raw bodies for `0x1E` + float and **do** find a 0.5 in both of the first two
(`TakeRadiusDamageFromWeapon.hex` at bytes 112 and 174; `DrainWeaponGeneratorForDamage.hex` at 218
and 236), and a 0.0 in `LoadHealth.hex` at 302. That means the prose lists were produced by an ad-hoc
byte scan while the JSON's `constants` comes from a token-aware walk — the two disagree, and the doc
quotes the one that is not in the artifact. Either the extractor drops tokens it should keep, or the
prose adds values the tool cannot reproduce; both break R11 ("numbers are generated, never typed")
and neither is detectable by `--check`. Pick one source and regenerate the sentence from it.

### 5. (R4) `ImpactMaxDamage` is claimed "read", but nothing references it — `DAMAGE_RULES.md:133`

```
| `ImpactMaxDamage` | read (cap) | — |
```

`functions."RVehicleBatmobileBase.CalculateAndStoreImpactDamage".refs` (186 entries) contains
`RVehicleBatmobileBase.ImpactMaxDamageSpeed`, `.BattleModeImpactMaxDamageSpeed` and
`.BattleModeImpactMaxDamagePow` — but no `RVehicleBatmobileBase.ImpactMaxDamage`. The row looks like
a substring match on `ImpactMaxDamage*`. Every other "read" row in that table checks out (§
Spot-checks), so this one is the outlier.

### 6. (R4) The regen negation is broader than the artifact supports — `DAMAGE_RULES.md:248`

"No `*Regen*` field exists on `RVehicle*`, `Pawn` or `AkVehicle` (the SDK scan in
`DAMAGE_RULES.json → regeneration` is the full list)". The artifact is
`regeneration.bm_sdk_symbols` — a `Counter` over **all** `Working/vendor/BmSDK/*.cs` with class
ownership dropped — plus `regeneration.bmgame_names`, the flat name table. The name table contains
`bRegenerateChildren`, so a reader checking the "full list" finds a `*Regen*` name in it and cannot
tell which class owns it. The per-class negation needs per-class evidence (owner recorded per
symbol), not a global counter.

### 7. (method) The reference traces carry noise with no confidence marker

`functions."RVehicleBatmobileBase.TakeRadiusDamageFromWeapon".refs` contains
`RemovePropSkeletal.PawnDied` ×4, `GFxMovieHudMenu.SetupResolution` ×3 and
`RAEC_Casualty_Sub_Tyger.AssignCasualty`; `CalculateAndStoreImpactDamage.refs` contains
`RemovePropSkeletal.PawnDied` ×6 and `GFxMovieHudMenu.SetupResolution` ×2. A distance-falloff
function does not call `PawnDied`, and an impact calculation does not call a GFx resolution setter.
The prose silently leaves them out and `:266-269` still calls the trace "ordered and complete".
Related: `field_references` (`bmak_damage.py:369-375`) decides "read_by" by raw 4-byte containment of
the export index anywhere in the body region, not at token boundaries — so the 25/1/1 reader counts
that carry §4 and §5 are "the index appears in the body", not "a token references it". Both need a
stated caveat (or a token-aligned re-scan) before T-14 leans on "exactly one reader".

### 8. (R11, cosmetic) "6/6 anchors" is not what the tool prints — `DAMAGE_RULES.md:11,286`

The doc (and `MODLOG.md:8255`, `:8301`) says "6/6 anchors" / "prints **6/6 anchors** and `PASS`".
The tool prints a seven-key dict (`A` is split into `A_super_is_parent_take_damage` and
`A_children_is_first_param`) and never prints "6/6". Six is the count of *lettered* anchors A–F in
the doc's own table; quoting it as the command's output is a typed count.

### 9. (needs stating or UNKNOWN) `TakesDamageFromRam`'s seven bytes — `DAMAGE_RULES.md:167-171`

The body is `04 27 04 3a 60 29 00` (from `functions.*.script_raw` / the `.hex`). `04 27` plausibly
consumes as "return true"; the trailing `04 3a 60 29 00` is **not** explained by the doc, and
`functions."RVehicleBatmobileBase.TakesDamageFromRam".refs` is `[]` and `.constants` is `[]` — so the
inline comment "then a read of the function's own ReturnValue slot" corresponds to no `refs` entry
and to a `0x29` byte that is short of a five-byte descriptor. I cannot decode the tail from the
files available here, and I am not asserting the "return true" reading is wrong — only that the
sentence is stronger than the trace behind it. Per R4, the tail's meaning should be stated as
UNKNOWN (or the descriptor re-checked) rather than glossed in a comment; §3.4 and §6.2 both rest on
it.

### 10. (minor, completeness) Selection presented as a listing

Done asks for "every damage-related field listed"; the `.md` shows ~30 of 251 rows and the JSON holds
the rest. That is defensible if the note says so, but §3.5 reads as the weapons list while omitting
`TurretShotDamage` 75 on `Batmobile_Heavy_Cannon_Primary_Projectile` (present in the JSON) and the
EMP missile entirely (see issue 1).

## Spot-checks (value → where verified)

| value in doc | doc line | verified at |
|---|---|---|
| `Pawn.Health` = 1200 on every Batmobile archetype | `:209` | `DAMAGE_RULES.json → damage_values`: 1200 for `RVehicleBatmobile` in `Playable_Batmobile_SF.Batmobile`, `Playable_BatmobileMK2_SF.Batmobile_MK2`, `Playable_BatmobileFunhouse_SF.BatmobileFunhouse` |
| `ArmourModeDamageReduction` = 0, single reader = `TakeDamage` | `:84`, `:214`, `:242` | `damage_values` = 0 (all three archetypes); `field_references."…ArmourModeDamageReduction"` → `"read_by": ["RVehicleBatmobileBase.TakeDamage"]` |
| `ImpactMin/MaxDamageSpeed` 20/150, battle 120/540, `ImpactStrafeMod` 2.25, `ImpactBoostMod` 2.0, `BattleModeImpactMaxDamagePow` 0.5; Joker 40/180, 0.8, 0.666 | `:121-126` | `damage_values` for `Playable_Batmobile_SF.Batmobile` and `Playable_BatmobileJoker_SF.JokersBatmobile` — all eight values match exactly |
| `WeaponGeneratorPower` "read by **25** script functions"; `HealthRecoverRate` "exactly **one** … `ExperienceAwarded`" | `:216`, `:244-246` | `field_references`: `…WeaponGeneratorPower` `read_by` length 25; `…HealthRecoverRate` `read_by` = `["RVehicleBatmobileBase.ExperienceAwarded"]` |
| `ImpactCivilianVehicleMod`, `RVehicle.CivilianVehicle`, `HeavyArmouredVehicle`, `bHasAPCStyleWeakSpot` → `RemoveWeakSpot`, `CurrentStrafeCooldown`/`StafeImpactImpulse`, `bBoosting`, `IsChallengeMode`, `DamageNumbers` all "read" | `:121-137` | all present in `CalculateAndStoreImpactDamage.refs` (only `ImpactMaxDamage` is absent — issue 5) |
| `HealthRecoverRate` is `TArray<float>` at +8220 | `:225` | `Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs:8872-8877` (`ArrayProperty: HealthRecoverRate`, `Ptr + 8220`) |
| package 214,757,637 B; 84,813 names; 177,031 exports of which 29,620 `Function`; 1,724 one-byte `04` bodies | `:3-5`, `:35` | re-ran the tool's own `Package` reader: `exports 177031`, `funcs 29620`, `names 84813`, one-byte-`EX_Return` bodies `1724`, `os.path.getsize(UPK) == 214757637` |
| `HealthRecoverRate` absent from the 423-field `OFFSETS.json` binding and from `CHAIN.json` | `:227-229` | `len(OFFSETS.json["fields"]) == 423`; `"HealthRecoverRate"` occurs in neither file |

## Limits of this review

I did not resolve bytecode control flow either, so I can neither confirm nor refute the ordered
semantics in §3.1–§3.3; I checked that the symbols, literal tokens and archetype values each claim
cites exist in the record, and reported the ones that do not. `GetDamageMod`'s scaling and
`HealthRecoverRate[difficulty]` genuinely need the running game — those two UNKNOWNs are correctly
filed under §7 and G1-22/G2-28, and I did not test them.

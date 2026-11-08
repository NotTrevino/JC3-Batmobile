# review-T-WP4c — independent re-derivation of three numeric claims

**VERDICT: minor issues.**

The three claims I was asked to re-derive all survive: `2468` is the base's size and the tracker really
adds no member; `[5461,0,0]` really is 30.0 degrees of pitch, and the generated MD does state the rule
(`/65536*360`); `Play_Batmobile_Immobiliser_Impact` really is the only *Immobiliser* string in the four
vehicle packages. But two labels/attributions in the DONE report are wrong and must be corrected before
it is treated as settled:

1. the tracker's `bInstantFire = true (class default)` is **not** carried by any decoded record — that
   `true` belongs to the EMP missile's row, so the tracker's value is **UNKNOWN**;
2. the Immobiliser impact sound and the EMP missile's `Projectile.Damage 60.0` are quoted from
   `Batmobile_EMPMissile_Projectile`, the archetype **no launcher points at**; the projectile the
   launcher actually fires (`_ForCars`) serializes **no** AkEvent and **no** damage at all. The report's
   "sitting on this missile's impact" and its "EMP missile numbers" paragraph read as one object's values.

Neither defect changes the row table or any JC3 route, which is why this is "minor issues" and not
"needs rework". Both are one-line corrections in `Tools/scripts/t_wp4c.py` plus a `--write`.

## The command I ran, and its output

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/t_wp4c.py --check; echo "EXIT=$?"
OK Working/Translation/T_WP4C_TRACKER_EMP.md (21373 chars)
OK Working/Translation/T_WP4C_TRACKER_EMP.json (36266 chars)
CHECK PASS
EXIT=0
```

The check passes and the two sizes it prints match the DONE report's `21,373` / `36,266`. That only says
the generated files agree with the script — it is not evidence for the numbers inside them, which is why
everything below was re-derived from the grab records and the SDK layout.

## Method (and one disclosure)

I did not read `Tools/scripts/t_wp4c.py` before deriving. One broad `code_search` for the sound string
returned, as incidental hits, two source lines of that script (407 and 587) containing the same
*Immobiliser* sentence; they carried none of the numbers I re-derived (no size, no rotator value, no
offset) and I did not open the file after that either. Sources used: `Working/vendor/BmSDK/*.g.cs` (the
BmSDK layout), `Research/BatmobileGrab/WEAPONS.json` + `WEAPONS.md` (the cooked property records of the
four vehicle packages, generated and `--check`ed by `grab_weapons.py`), `AUDIO_MAP.json`, and the
generated `Working/Translation/T_WP4C_TRACKER_EMP.md`. All read-only; no game launched or attached.

---

## Claim 1 — "`RBatmobileVehicleTracker` size 2468 = the base's, so **0 own fields**"

Report (DONE, Tracker paragraph): *"size 2468 = the base's, so **0 own fields**"*.

My derivation, two independent sources:

- BmSDK layout, class headers: `RBatmobileVehicleTracker` `(size = 2468)`,
  `RPursuitModeMissileLauncher` `(size = 2468)`, `RVehicleWeapon` `(size = 2396)`,
  `RBatmobileEMPMissile` `(size = 2672)`, `RBatmobileBooster` `(size = 2400)`.
  ```
  $ grep -n "size = " Working/vendor/BmSDK/RPursuitModeMissileLauncher.g.cs \
        Working/vendor/BmSDK/RBatmobileVehicleTracker.g.cs Working/vendor/BmSDK/RBatmobileEMPMissile.g.cs \
        Working/vendor/BmSDK/RVehicleWeapon.g.cs Working/vendor/BmSDK/RBatmobileBooster.g.cs
  RPursuitModeMissileLauncher.g.cs:8:/// (size = 2468)
  RBatmobileVehicleTracker.g.cs:8:/// (size = 2468)
  RBatmobileEMPMissile.g.cs:8:/// (size = 2672)
  RVehicleWeapon.g.cs:8:/// (size = 2396)
  RBatmobileBooster.g.cs:8:/// (size = 2400)
  ```
- The tracker's `g.cs` declares **no property accessor at all** — only three function wrappers
  (`ReadyToFire`, `CheckAutoTarget`, `ProjectileHitActor`). Every `Ptr + n` in that file is a *parameter
  buffer* offset (`paramsPtr`), not a member. So nothing is added above 2468.
- The cooked records agree: all three `Vehicle_Tracker` instances serialize exactly the base's 7 fields,
  every offset below 2468 — `Actor.Tag` 360, `RInventoryGadget.Mesh` 792, `FireStartEvent` 2176,
  `IndividualFireEvent` 2200, `ProjectileArchetype` 2428, `LaunchSocketName` 2436,
  `LaunchRotationOffset` 2452.

Oracle: a class that had an own field would show `size > 2468` and at least one accessor at `Ptr >= 2468`
— exactly what `RBatmobileEMPMissile` does (2672, 204 bytes of own fields). The tracker shows neither.

**Label check: correct.** The size is *decoded* (SDK header); "0 own fields" is a *derived* rule
(same size + no member above the base) and the report presents it that way ("2468 = the base's, so").

**But the same sentence mislabels `bInstantFire`.** The report lists `bInstantFire` true ("class
default") among the tracker's inherited launcher fields. It is not in any tracker record:

```
Playable_BatmobileFunhouse_SF Vehicle_Tracker fields=  7 bInstantFire=False Damage=False
Playable_BatmobileMK2_SF   Vehicle_Tracker fields=  7 bInstantFire=False Damage=False
Playable_Batmobile_SF      Vehicle_Tracker fields=  7 bInstantFire=False Damage=False
Playable_BatmobileFunhouse_SF Batmobile_EMP_Missile_Launcher fields= 21 bInstantFire=True  Damage=False
```

No `bInstantFire` appears anywhere in `CLASS_DEFAULTS.json`/`.md` either (grep: 0 hits), so the class
default is not decoded. The `True` in the report is the **EMP missile's** row, borrowed. The Limitations
section then states *"only `bInstantFire` is carried by a decoded row (true)"* — false for the tracker.
Correct label: **UNKNOWN** (not serialized on the tracker; class default not in any decoded file). This
is a wrong label, the one hard error I found.

---

## Claim 2 — "`LaunchRotationOffset` [5461,0,0] = **+30°** pitch"

Report (DONE): *"`LaunchRotationOffset` [5461,0,0] = **+30°** pitch"*, labelled decoded with the tracker.

My derivation:

- Value and offset, from the cooked record (`Playable_Batmobile_SF.Vehicle_Tracker`):
  `RPursuitModeMissileLauncher.LaunchRotationOffset`, offset **2452**, type `RotatorProperty`,
  `named_by: "sdk-layout"`, value **[5461, 0, 0]** (identical in Batmobile, MK2, Funhouse — the variant
  map reports 0 differences).
- Layout, from the SDK: `LaunchRotationOffset` is `Ptr + 2452` as `BmSDK.Rotator`, and the next member
  `bInstantFire` is at `Ptr + 2464`. 2452 + 12 = 2464, i.e. the rotator is exactly the three int32s
  2452..2463 — **the recorded offset 2452 and the SDK offset 2452 agree**, which is the oracle that the
  three values in the record are the three rotator components, in order (Pitch, Yaw, Roll).
- Unit and rule. A UE3 `Rotator` is 16-bit angle units, 65,536 per full turn (the project's own framing:
  `T7_WEAPONS.md` §"rotator | `LaunchRotationOffset`, UE rotator units (65536 = 360 deg)"; `WEAPONS.md`
  §0 says the same). So:
  ```
  $ python -c "n=5461; print(n*360/65536, round(n*360/65536,1)); print(65536/12)"
  29.9981689453125
  30.0
  5461.333333333333
  ```
  5461 units = **29.9981689…°**, i.e. 30.0° to one decimal, and 65,536/12 = 5,461.33 — a twelfth of a
  turn, consistent with a hand-set 30°.

**Is "+30 degrees" derived by a stated rule?** **Yes, in the generated MD** — line 51 of
`T_WP4C_TRACKER_EMP.md`:

> `| launch point and pitch | `LaunchSocketName` = "BattleModeSpotLight", `LaunchRotationOffset` = [5461, 0, 0] (UE rotator; /65536*360 = 30.0 deg of pitch) | decoded / derived |`

So the unit is stated (UE rotator units, 65,536 = 360°) and the arithmetic is shown, and the row is
labelled `decoded / derived` — correct, since the value is decoded and the degrees are derived.

Two nits, not errors:

- 5461 units is 29.998°, not exactly 30.0; the MD writes `= 30.0` without showing the unrounded value or
  saying "rounded to 1 dp". A one-word fix.
- The DONE report drops the rule entirely (`= **+30°** pitch` with no unit), and neither document says
  whether +30° pitches the socket **up** or **down** — the sign convention is not decoded anywhere in the
  files, so "up" must not be asserted. The same applies to the EMP missile's `-20°`: the MD keeps the raw
  `[-3640, 0, 0]` (decoded) and `-3640*360/65536 = -19.9951… → -20.0` checks out, but the DONE report
  prints `−20°` as a bare number.

**Label check: correct**, with a rounding note missing.

---

## Claim 3 — the Immobiliser sound string

Report (DONE): *"the only Immobiliser string in the weapon data — `RBatmobileMissile.ExlposionSound` =
`Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` — sitting on this missile's impact"*.

My derivation:

- The field→target pairing is decoded: archetype `Batmobile_EMPMissile_Projectile`, class
  `RBatmobileMissile`: `RBatmobileMissile.ExlposionSound` → `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`
  (AkEvent, resolved), identical in Batmobile/MK2/Funhouse. `AUDIO_MAP.json` carries the same event name.
- "Only *Immobiliser* string in the weapon data" holds for the four vehicle packages: the sole distinct
  match is `Play_Batmobile_Immobiliser_Impact` (15 instance occurrences, one name; no
  `Immobiliser_Fire`/`_Loop`/etc.).
- Note the field's own spelling, `ExlposionSound` (sic) — the report reproduces the game's typo, correct.

**Label check: the string is decoded, the attribution is wrong.** The Immobiliser missile's two payload
pointers — `RBatmobileEMPMissile.ProjectileForCarsArchetype` (offset 2492) and inherited
`RPursuitModeMissileLauncher.ProjectileArchetype` (offset 2428) — both carry export 5116, which resolves
to **`Batmobile_EMPMissile_Projectile_ForCars`**, not to `Batmobile_EMPMissile_Projectile`. And the fired
one has no sound at all:

```
### Batmobile_EMPMissile_Projectile            (20 fields, NOT referenced by any launcher)
    RBatmobileMissile.ExplosionTemplate = 4976      (Particles.Rocket.Batmobil_Rocket_Explosion)
    RBatmobileMissile.ExlposionSound = 123          (Play_Batmobile_Immobiliser_Impact)
    Projectile.MyDamageType = -121                  (Core.RDmgType_BatmobileCannon)
    Projectile.Damage = 60.0
### Batmobile_EMPMissile_Projectile_ForCars    (10 fields, the one both pointers resolve to)
    RBatmobileMissile.ExplosionTemplate = 4977      (Particles.Rocket.Batmobil_Rocket_Explosion_Small)
    (no ExlposionSound, no Projectile.Damage, no MyDamageType)
```

So "sitting on this missile's impact" is a *derived* claim at best, and the derivation is not shown: the
sound sits on the sibling archetype that no launcher points at. The class identification (lead (a)) still
stands on its strongest legs — the class/archetype pair and both payload pointers being on the
`RBatmobileEMPMissile` gadget — but the sound leg is a name-adjacency hint, not proof of the impact.
Correct label: **decoded** for the field→event pairing; **derived/UNKNOWN** for "this is the fired
missile's impact sound".

### The same defect, one paragraph later (extra finding)

The DONE report's "**EMP missile numbers.**" paragraph reads: *"`Projectile.Damage` 60.0 with
`RDmgType_BatmobileCannon`, `DamageRadius` 0, explosion `Rocket.Batmobil_Rocket_Explosion_Small`"*, then
*"The anti-car payload serializes no scalar at all (10 reference tags)."* Those two sentences describe
**two different objects** and the paragraph merges them: 60.0 / `RDmgType_BatmobileCannon` /
`DamageRadius 0` belong to the unfired `Batmobile_EMPMissile_Projectile`; `Explosion_Small` belongs to
the fired `_ForCars`. Read literally, the report credits the fired EMP missile with 60 damage — the one
number that most affects a translation. The correct statement is: the fired archetype is
reference-only (10 fields, no damage, no damage type, no AkEvent) and any damage on it can only come from
`RBatmobileMissile`/`RProjectile` class defaults, which are **not** decoded here (grep of
`CLASS_DEFAULTS.json`/`.md`: no hit). This must be split into two rows before the report is used.

---

## Label table for the reviewed claims

| claim | report label | my verdict | note |
|---|---|---|---|
| tracker size 2468 = base → 0 own fields | decoded (size) + derived (0 fields) | **correct** | corroborated by 7/7/7-field records and absence of accessors |
| tracker `bInstantFire` true (class default) | decoded row | **wrong → UNKNOWN** | `true` is the EMP missile's row; no tracker instance serializes it |
| `[5461,0,0]` = +30.0° pitch | decoded / derived | **correct** | rule stated in MD line 51; 29.9982° rounded to 30.0, rounding not stated |
| pitch sign (up/down) | not stated | **correctly absent** | no decoded convention in the files |
| `ExlposionSound` = `Play_Batmobile_Immobiliser_Impact` | decoded | **correct as a pairing** | — |
| "sitting on this missile's impact" | decoded | **overstated → derived/UNKNOWN** | sits on `Batmobile_EMPMissile_Projectile`, which no launcher references |
| "the only Immobiliser string in the weapon data" | decoded | **correct** | 1 distinct name, 15 instance hits, four vehicle packages |
| EMP missile `Damage 60.0` + `Explosion_Small` together | decoded | **wrong grouping** | damage ∈ unfired archetype; `Explosion_Small` ∈ fired `_ForCars` |

## What I could not check

- **The raw export bytes of `Playable_Batmobile_SF.upk`.** There is no `objects.jsonl` under
  `E:/Modding/_shared/gamedata` and `WEAPONS.json` records the property offset but not the export's absolute file
  offset, so I could not myself walk the package header and read the 12 bytes at export+2452. I therefore
  confirmed `[5461,0,0]` and `[-3640,0,0]` as *recorded-at-offset-2452* values whose offsets agree with an
  independent layout, not by opening the .upk. A byte-level confirmation needs a package walk (or the
  schema-6 `objects.jsonl` regenerated); it would be a 5-minute job and would settle it completely.
- **Class defaults for `bInstantFire`, `AutoTargetAngle`, `Range`, `Projectile.Damage` on
  `Batmobile_EMPMissile_Projectile_ForCars`.** No decoded default record carries them
  (`CLASS_DEFAULTS.json`/`.md`: 0 hits for `InstantFire`), so these stay UNKNOWN rather than zero — which
  is also what the report says for `AutoTargetAngle`/`Range`, and I confirmed that part is right.
- **Anything runtime.** Test ban respected: no game launch, no injection, read-only on the install. The
  native bodies of `CheckAutoTarget` / `ProjectileHitActor` / `FireMissile` are not in the bytes, so the
  disable's duration stays open exactly as the report says; I did not try to re-derive it.

No compromise with lore accuracy is proposed or implied by this review; the two corrections above are
accuracy *restorations*, and I approve none of the report's C1–C3 compromises — that stays the operator's
call through Claude.

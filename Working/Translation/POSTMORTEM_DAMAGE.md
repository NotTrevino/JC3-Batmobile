# Test-087: the damage regression, and where the architecture broke

**Verdict: the test failed because the row it came from translated the Batmobile's ram *offence*
into JC3 *defence*, and because the behaviour the mod already had was a hand-hack that the ledger
could not see.** The grab is not innocent, but it is not the first failure: the BmAK values and even
the direction of the fields were captured. The translation stage is where the inversion happened,
and the record is what let it pass every gate.

Written 2026-10-23, after test-087 was installed and driven. It is live in the dropzone right now:
`10B14A60…` (test-087) vs test-085's `D9C4AAD3…`.

---

## 1. The mechanism, exactly

test-087 = test-085 + 9 values. Three of them are the damage block:

| module.member | test-085 | test-087 | what the member does |
|---|---|---|---|
| `vehicledamage.impact_damage_factor` | **0** | **1.0** | multiplies damage taken from a collision. 0 is an off switch; 1 is the shipped value for every land vehicle |
| `vehicledamage.impact_armor` | **5000** | **5.0** | per-hit impact armour pool |
| `vehicledamage.deform_scale` | **0** | **1.0** | panel crumple on impact |

The first line is the whole regression. Every other value in the block stayed at the game's
maximum. With the factor at 1 the car takes collision damage at a 6 t-armour level, so ramming
traffic and walls now dents, burns and eventually kills it — the opposite of the one behaviour the
Batmobile has to have.

## 2. Where `0 → 1` came from: a direction error

T-DM7's BmAK side is `ImpactMinDamageSpeed` 20, `ImpactMaxDamageSpeed` 150, `ImpactStrafeMod` 2.25,
`ImpactBoostMod` 2.0, `BattleModeImpact*` (`Research/BatmobileGrab/OFFSETS.md` rows at `0x1ACC`,
`0x1AD0`, `0x1AD4`, `0x1ADC`, `0x1AE4`). Those fields are **outgoing**. The class API says so in
three function signatures, all of which take the *other* actor
(`Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs`):

| function | argument | direction |
|---|---|---|
| `TakesDamageFromRam(Target, RamSpeed)` | the vehicle being rammed | Batmobile → other |
| `CanBatmobileDoImpactDamage(OtherVehicle)` | the vehicle being rammed | Batmobile → other |
| `CalculateAndStoreImpactDamage(OtherVehicle, pos, Speed)` | the vehicle being rammed | Batmobile → other |

There is no incoming-impact entry point on the class. That is consistent with the health bar
(`UC_SetHealth`, grabbed in `HUD.md`): the bar exists, and ramming does not move it. So BmAK's
impact block is the **ram attack** — the thing that turns a 3-tonne car into a wreck when you hit
it at 150 km/h — and it says nothing about what the Batmobile takes.

T-DM7 mapped it onto `impact_damage_factor` / `impact_armor` because both sides say "impact". Its
own transform cell admitted there was "no bridge to JC3's damage model". Under the old rule that
was not a blocker: `conf: class` was allowed to stand in for the missing bridge, and the class rule
then chose 1 because 156/156 land vehicles ship 1. So the translation did not merely guess — it
replaced a known behaviour with a fleet statistic, which is the definition of manual tuning wearing
an evidence label.

There is a second, worse consequence. JC3 gives a player car no way to damage what it rams, so the
*outgoing* half of that BmAK block has no JC3 expression at all. T-DM7 should have been `out` on the
offence and a separate **behaviour** row on the defence. It was neither.

## 3. The immunity that was destroyed was not a translation either

The pre-087 block is a saturation island. Against the shipped ranges in
`Research/JC3Grab/VOCABULARY.md` (`VehicleDamage`, n=233, donor column):

| member | build (test-085/087) | shipped range | verdict |
|---|---:|---|---|
| `impact_damage_factor` | **0** | 1 … 12 | **outside** — off switch |
| `impact_armor` | **5000** | 0 … 5 | **outside** — 1,000× the maximum |
| `impact_armor_strength` | 100 | 0 … 100 | at the maximum |
| `bullet_armor` | 5000 | 0 … 5000 | at the maximum |
| `bullet_armor_strength` | **100** | 0 … 99 | **outside** — one above the maximum |
| `melee_armor` / `_strength` | **5000 / 100** | 0 … 0 / 0 … 0 | **outside** — no shipped vehicle uses melee armour |
| `deform_scale` | **0** | 1 … 2 | **outside** — deformation off |
| `explosion_armor` / `_threshold` | 250 / 4000 | 0 … 250 / 500 … 4000 | at the maximum |
| `smoke_threshold` / `burn_threshold` | 1050 / 250 | 200 … 1050 / 50 … 250 | at the maximum |
| `max_health` | 2000 | 500 … 4000 | inside (6 t+ p75) |

Six of these are outside every value the game ships. That is not a translation, it is an
invulnerability switch someone built by hand earlier and never recorded as one. The ledger then
treated them as ordinary `keep` values because it records **provenance**, and "it is in the build"
counts as provenance.

So both statements are true, and this is the actual architecture failure:

- the immunity was real and load-bearing, and
- it had no row, no unit, no explanation and no domain check, so the first tidy-up pass was
  guaranteed to delete it.

## 4. Why every gate stayed green

| gate | what it proves | why it missed |
|---|---|---|
| `t_rows check` | every row has a disposition and a reason | the reason said "156/156 ship 1" |
| `t1_apply` / `t5_apply` / `t5_build` / `verify_install` | the bytes were written and read back | bytes ≠ behaviour |
| `STATUS.md` | 97/112 rows evidenced | **0/112 behaviour-verified**; the metric never touched the car |
| T-DM7's own verify cell | — | it said "ram a wall at 40 km/h: **damage taken**, no instant destruction" — the pass criterion encoded the opposite of the source behaviour |

The project did know. T-DM7's `now` cell literally says *"0 disables impact damage, so the
Batmobile is currently indestructible by collision"*, and `T1_TRANSLATION.md` says the same in
prose. The row queued the change anyway because the class rule outranked the behaviour. A written
fact that lives in a confidence column loses to a number in a build column every time.

Scale of the pattern: **28 of the 96 in-scope T-1/T-2b/T-3 rows are `class`** — a value chosen
because the JC3 fleet does it, not because BmAK says it or a unit bridge carries it. T-DM7 was the
one that happened to sit on the car's defining behaviour.

## 5. What actually failed in the grab

Two gaps, both on the JC3 side:

1. **G2 decoded JC3's damage members but not JC3's damage model.** The fleet table gives ranges and
   the donor column gives a value; nothing says how `*_armor`, `*_armor_strength`,
   `*_damage_factor`, `*_threshold` and `max_health` compose. Without that, every damage row is a
   number with a story attached. It is the same gap the camera had until §2b of `CAMERA.md` was
   disassembled — and it is closed the same way.
2. **Nobody looked for a damage-immune state — now they have.** The entity graph carries one:
   every vehicle root (`CCar`, `CBoat`, `CHelicopter`, `CMotorBike`, `CAirPlane`, `CTrain`) has an
   int32 `invulnerable` alongside `health`, and all 233 shipped roots leave it at 0. The value is
   live — 10 `CDamageController` objects ship `1` — and the field is addressable in the `.epe`
   (`type 0x0e · hash af4406fb · value` at `+1162/+1163/+1167`, 4 bytes). That is the route T-DM9
   needs; the module never had it. Details and caveats: `Research/JC3Grab/DAMAGE_MECHANISMS.md`.

On the BmAK side the missing piece is narrower: `TakeDamage`, `ShouldRadialDamageHit` and the
`TakesDamageFromRam` body are script functions in `BmGame.upk`. The project already decompiles that
package (`ffdec`, used for the HUD movie and `R3rdPersonCamera`), so the immunity rule is readable
rather than guessable. That is the next grab task, and it is cheap.

## 6. Bullets: the same root, one step further

The car sat at the shipped maximum in **every** armour channel — bullet 5000/100, explosion
250/4000, smoke 1050, burn 250 — and bullets still destroy it. Two readings are possible and both
have the same consequence:

- armour is a reduction with a cap, not an immunity, or
- the `*_armor` field only counts when its paired condition holds (the pairs are
  `*_armor` + `*_armor_strength`), and we have only ever moved one side of each pair.

Either way, "small arms do not hurt it" **cannot be expressed by tuning `VehicleDamage`**. It is not
a value row. It is a mechanism, and the mechanism turned out to be one field away: the entity root's
`invulnerable` int32 (`DAMAGE_MECHANISMS.md`). It stays `blocked` until the 4-byte write is built and
the take passes — but the route is no longer a hypothesis. This is the part of the report the old
table would have answered with another number, which is exactly how test-087 happened.

## 7. test-086 (camera): derived, not tuned — and derived wrong

The suspicion is reasonable but the provenance is real. Every one of the eight values in test-086
came from a named BmAK field (`Working/Camera/CAM_TUNE.json`):

| value written | source |
|---|---|
| `FOV` min 55 | `DrivingCamFOV1` 85 **h** → 54.5 **v** (16:9 conversion) |
| `FOV` max **85** | `BoostingCamFOV1` 95 **h**, **copied as vertical** — the bug |
| `FOVVelocityRange` max 108 | `DrivingCamFOVInterpMaxSpeed` 3000 cm/s |
| `CameraPosition` 7.0 / 2.4 | body-length ratio at the time; now decoded as 400 cm boom + 300 cm sit = **700 cm**, height **130 cm** |
| `LookAtPoint` 1.7 | body-height ratio; decoded pivot = **155 cm** |
| `RollWithVehicleAmount` 0.38 | `DrivingCameraLeanFactor` 7.5 / `RollLimit` 20 |
| `CollisionStartPoint` 1.6 | 2.271 m body vs 1.41 m donor |

So: not hand-tuned, but two of the eight were arithmetic errors (horizontal-as-vertical FOV, and
ratio geometry), which is why the drive read "less zoomed in". Since then the native composition is
decoded and checked (`bmak_camdecode.py --check`, 18/18), so the corrected camera needs no taste
calls at all: **FOV 55…63, `CameraPosition` [0, 1.30, 7.00], `LookAtPoint` [0, 1.55, 0],
`CollisionStartPoint` [0, 1.6, 0]**. The camera is the one subsystem where the answer is "translate
again with the decoded numbers", not "back to the drawing board".

## 8. The rules that replace the doctrine

R1. **Behaviour rows are first class.** Every requirement (the car does X in BmAK) gets a row whose
    source is the behaviour, whose target is the JC3 *mechanism* (not a member that sounds similar),
    and whose verify cell is a take that can fail. Value rows may support it; they may not replace it.

R2. **No bridge → `blocked`.** `class` is not a bridge. A fleet median is legal only when BmAK has
    no value **and** the row carries no behavioural requirement. It is never legal to out-vote a
    behaviour with a majority of JC3 vehicles.

R3. **Domains are evidence.** Any build value outside the shipped fleet range is a **switch**, must
    be declared with its reason and row in `Working/Translation/damage_switches.json`, and
    `Tools/scripts/damage_audit.py` fails if it is not. Undeclared out-of-domain values are defects,
    not translations.

R4. **S4 is not done.** A batch value is not "translated" until the take that can fail has passed.
    Until then the row stays `next`, not `resolved`. `STATUS.md` already separates S4 from S5; the
    batch list must too.

R5. **Every `keep` names its origin.** "It is in the build" is not provenance. A keep is either the
    donor's value, BmAK's value, or a declared switch — and the cell says which.

## 9. State after this note

- **test-087 is withdrawn.** The live dropzone must go back to test-085
  (`Builds/test-087/install.ps1 -Action Rollback085`), which carries the immunity block.
- **T-DM7 → `out`** (BmAK impact block is outgoing ram damage; JC3 has no equivalent).
- **T-DM8 → `keep`** (behaviour: no incoming collision damage; JC3 mechanism
  `impact_damage_factor 0`, declared as a switch). This is the row that was missing.
- **T-DM9 → `blocked`, route found** (behaviour: small arms do not move the health bar; the module
  has no member, the entity root has `CCar.invulnerable` at `epe+1167` — a 4-byte write, probe
  build not yet run).
- **T-DM6 → `keep`** (`deform_scale 0`, declared cosmetic switch: no crumple).
- **Batch B loses its three damage values.** The six handling values stay staged but unbuilt until
  R1 is applied to them: each needs a behaviour and a failing take, not only a class median.

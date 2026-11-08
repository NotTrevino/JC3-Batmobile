# Review — G1-09 · Projectiles and explosions

Independent, read-only pass. Nothing under `Research/`, `Tools/`, `Working/` or either game folder
was edited; the only file written is this report. Card: `GRAB_BACKLOG.md` §0.5 / §1 WPN / §12 line
1277 (card at lines 402-409). Outputs: `WEAPONS.md` §4, `WEAPONS.json` (`projectiles`,
`projectile_coverage`), `Tools/scripts/grab_weapons.py`, MODLOG
`## G1-09 · Projectiles and explosions — done (2026-10-24)`.

## VERDICT: sound

The Done criterion is computed, not asserted: `projectile_coverage.orphan_refs` is
`set(fired_by) - set(rows)` and is empty, so every launcher-referenced projectile has a row; the one
projectile that is not launcher-referenced is kept and marked. The check reproduces the MODLOG
verbatim, including the file sizes. Every value I re-derived matches the record — the heavy-cannon
primary's 40000/48000/-1000 z/50/0/66666.671875 sit at offsets 668/672/856/728/732/736 in
`objects.jsonl` with those exact bytes, and `CHAIN.json` binds those offsets to
`Projectile.Speed`, `Projectile.MaxSpeed`, `RBasicProjectile.InitialAcceleration`,
`Projectile.Damage`, `Projectile.DamageRadius` and `Projectile.MomentumTransfer`. The G1-08
resolver correction is real: `…Primary_Projectile.ImpulseComponent0` resolves to export **index 14**
of `Playable_Batmobile_SF`, whose raw row is that name/class/outer.

Two hygiene points, no wrong value: the "15,000 impulse" is a name given in prose to an unnamed
field, and the Done is visible in the data rather than failing the check.

## Check output (verbatim)

```
$ python Tools/scripts/grab_weapons.py --check
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.json
ok E:\Modding\JustCause3\JC3-Batmobile\Research\BatmobileGrab\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences, 10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows
EXIT=0
```

## Out paths and Done criterion

- `WEAPONS.md` §4 "Projectiles" — exists; ten `###` subsections, one per projectile
  (`Batmobile_EMPMissile_Projectile` … `Batmobile_Tracker_Projectile`), plus the launcher-coverage
  table (`projectile | class | instances | fired by`) and the FX/audio rows.
- `WEAPONS.json` — `projectiles` (10 rows, each with `instances`, `fired_by`, per-quantity
  `status`/`field`/`searched`, `impulse`, `effects`, `audio`), `projectile_coverage`
  (`launcher_targets` 9, `unfired` 1, `orphan_refs` 0).
- Done ("every projectile referenced by a launcher in G1-08 has a row"): **computed** —
  `grab_weapons.py:592` builds `orphan_refs` as `set(fired_by) - set(groups)`, and it is `[]`;
  all 9 `launcher_targets` are row names, and the 10th (`Batmobile_EMPMissile_Projectile`) is in
  `unfired` and still has a row. The card's Do list is covered or explicitly absent: speed / max /
  accel / homing / damage / radius / momentum(=`MomentumTransfer`) / impulse component / trail and
  impact particle systems / flight and explosion AkEvents; `LifeSpan`/`Lifetime` is absent from all
  ten and recorded as `absent`, not filled.

## Issues

### 1. "the 15,000 impulse" is prose naming an unnamed field (small R4/R5 note)

The record keeps the impulse component's fields honestly — for the heavy-cannon primary the value is
`{"path": "offset 0x0220", "offset": 544, "type": "FloatProperty", "named_by": null, "value":
15000.0}` inside the referenced `RB_RadialImpulseComponent`, and for the EMP missile it is the same
offset with `1000.0`. The MODLOG's G1-08-correction sentence calls it "the 15,000 impulse", i.e. it
gives the unnamed field a name from the class it lives in. The `.md` §4 table does not repeat that
label (it prints the field path), so nothing in the deliverable claims the member name; the prose
does. A reader following only the MODLOG would think the field is named.

### 2. The Done is data-visible but does not fail `--check`

`--check` byte-compares the two files against a re-derivation, so it catches drift but not a hole: if
a future edit dropped a projectile row, `orphan_refs` would become non-empty and `--write` would print
it (`grab_weapons.py:900-902`) — but `--check` would still pass, because the regenerated file equals
the regenerated file. `if coverage["orphan_refs"]: return 1` inside `check()` would make the card's
Done a gate instead of a number someone has to read. Today it is `[]`, so nothing is wrong.

### 3. Minor: the per-quantity table has no per-package column

§4's tables collapse the 3-4 instances per projectile into one value column, on the strength of
G1-08's variant map (0 differing over 1,065 comparisons). The `.md` says so explicitly ("a per-package
column appears only where a value actually differs"), and I confirmed the claim holds for the shared
objects, so this is a stated design choice rather than a gap — but it means a Joker-only retune of
one projectile value would show as a single column with no warning. The variant map is what protects
it, not the projectile table.

### 4. What is genuinely absent is recorded, not guessed

`Batmobile_EMPMissile_Projectile_ForCars` has no scalar values at all; EMP and Tracker have no
`Projectile.Damage`; no projectile has `LifeSpan`/`Lifetime`; `ExplosionTemplate` is a
`ParticleSystem`, not an explosion actor, and the packages carry no explosion damage/radius actor
values. All four are stated as absences in the `.md` and in the MODLOG limits, with `status: absent`
and the `searched` path per quantity in the JSON. That is the card's Stop rule handled correctly.

## Spot-checks

| value in the doc | where verified |
|---|---|
| heavy cannon primary: speed 40000, max 48000, accel `[0, 0, -1000]`, damage 50 (turret 75), radius 0, momentum 66666.671875 | raw tags in `objects.jsonl` for `Playable_Batmobile_SF.Batmobile_Heavy_Cannon_Primary_Projectile`: offset **668** `FloatProperty 40000.0`, **672** `48000.0`, **856** `VectorProperty [0,0,-1000]`, **728** `50.0`, **732** `0.0`, **736** `66666.671875`, **944** `IntProperty 75`; `CHAIN.json` names those offsets `Projectile.Speed`, `Projectile.MaxSpeed`, `RBasicProjectile.InitialAcceleration`, `Projectile.Damage`, `Projectile.DamageRadius`, `Projectile.MomentumTransfer`, `RBasicProjectile.TurretShotDamage` |
| EMP missile: max 7500, accel 40000, damage 60, radius 0, no momentum; impulse 1000 | JSON `projectiles[0].values` (`max_speed` 7500.0, `acceleration` 40000.0, `damage` 60.0, `damage_radius` 0.0, `momentum_transfer` absent); `impulse.fields[0]` = offset 544, 1000.0 |
| 10 rows / 9 launcher targets / 1 unfired / 0 orphans | `projectile_coverage`: 9 names, `unfired = [Batmobile_EMPMissile_Projectile]`, `orphan_refs = []`; every target present in the 10 row names; the `.md` §4 has 10 `###` subsections |
| particle counts: `Batmobile_CanonTrail` 2 emitters; the two `Batmobile_HeavyCannon_Impact` exports 8 and 5 | `PARTICLES.json`: `Playable_Batmobile_SF` index 4978 `Batmobile_CanonTrail` = 2 emitters (ribbon + sprite); `Batmobile_HeavyCannon_Impact` exports 4942 (8 emitters) and 4943 (5 emitters), mirrored in Funhouse 5033/5034 |
| G1-08 resolver correction: `…Primary_Projectile.ImpulseComponent0` by export index | reference `resolved_to` = `{package: Playable_Batmobile_SF, index: 14, name: ImpulseComponent0, class: RB_RadialImpulseComponent, outer: Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile}`; the raw export at index 14 has exactly those fields |

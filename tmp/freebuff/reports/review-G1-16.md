# Independent review — G1-16 · Particles by feature

Reviewer: Freebuff (did not write this card). Date: 2026-10-29.
Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14) + card G1-16 + tracker row §12; `MODLOG.md` §"G1-16 · Particles by feature — done";
`Research/BatmobileGrab/PARTICLES_FEATURES.md` + `.json`; `Tools/scripts/bmak_particle_features.py`.
Read-only: no project file was modified. This report is the only file written.

## VERDICT: **minor issues**

The deliverable itself is sound and reproducible: all 206 rows, the 63 names, the 17 used groups, the
emitter/level/colour totals and the 49-name coverage set re-derive exactly from the inputs, the `.md`
is byte-for-byte the script's output (so no typed numbers, R11 holds for content), and every Out path
exists. What is weak is the **gate**, not the data: `--check` never re-reads the inputs, so it proves
internal consistency rather than the card's Done-when; plus one mislabelled count, one provenance
overreach (heat-steam, R4), and per-package presentation that the doc does not explain. No number is
wrong, so this is not a rework — but the check must re-derive and the three labels must be fixed.

Out paths (both exist):
`Research/BatmobileGrab/PARTICLES_FEATURES.json` 447,582 B (2026-10-25 05:33),
`Research/BatmobileGrab/PARTICLES_FEATURES.md` 28,391 B (2026-10-25 05:33).
Script named in the MODLOG Revert: `Tools/scripts/bmak_particle_features.py` (584 lines, 05:32).

## Check output (verbatim)

Command: `python Tools/scripts/bmak_particle_features.py --check` → exit 0.

```
{
 "systems": 206,
 "distinct_names": 63,
 "emitters": 1433,
 "levels": 1107,
 "groups_used": 17,
 "systems_with_colours": 183,
 "systems_with_material": 206,
 "systems_with_lifetime": 203,
 "systems_with_spawn": 206,
 "systems_with_size": 174,
 "external_refs": 5,
 "colour_boxes": 1290
}
OK: 206 systems (63 names) in 17 groups; facts: lifetime 203, spawn 206, size 174, materials 206, colours 183 (1290 boxes); coverage 49 referenced names (44 in-grab + 5 external), 8 MECHANICS wheel refs all found in objects.jsonl
```

(The JSON block above is the script echoing the *stored* `summary` block of the JSON, not a measurement —
see issue 1. The `OK:` line matches MODLOG:8448.)

## Issues

### 1. `--check` does not re-derive from the inputs — the card's Done-when is only checked against itself
`Tools/scripts/bmak_particle_features.py:503-552` (`check(doc)`) receives the already-loaded
`PARTICLES_FEATURES.json` (`:571-575`) and only tests that file against itself: `s["systems"] != 206`
(`:508`) compares a stored integer to 206; the coverage sums (`:519`) and the group-row sum (`:527`)
were computed by `build()` with the same expressions. `PARTICLES.json`, `WEAPONS.json` and
`objects.jsonl` are never opened in `--check` mode.
Why it matters: the card's Done is "every system referenced by G1-08/G1-09 or a wheel/vehicle object has
a feature group". The 49-name reference set and the 206/1433 totals are frozen in the JSON; a stale
build, a hand edit, or a new particle reference added to `WEAPONS.json` tomorrow leaves the gate green
while that Done-when becomes false. `GRAB_BACKLOG.md` §0.2 step 5 requires `--check` to "re-derive and
compare". The fix is cheap: a full `build()` takes **2.4 s** on this machine (measured). Today the data
is right — I ran `bmak_particle_features.build()` and compared with the stored file: `summary` equal,
`coverage` equal, same 206 `(package,index)` keys, **0 differing rows**.

### 2. A count labelled "systems" is a count of names
`Research/BatmobileGrab/PARTICLES_FEATURES.md:243` — `| systems nothing references | 19 |`.
19 is `len(coverage.unreferenced_systems)`, and that list (`script:340`, printed in the JSON) holds 19
**names**, e.g. `Batmobile_canonMuzzleflash_NV`, `Batwing_Exhaust_P`, `EMP_Burst_Stage_01`.
The number of system *rows* nothing references is **54 of 206** (checked against the actual
`(package,index)` reference set, see spot-check 4). A reader takes 19 as "19 of 206 systems are
unreferenced"; the true figure is 54.

### 3. Unsupported claim presented as fact (R4) in the heat-steam note, and an unproven either/or in wall-scrape
`PARTICLES_FEATURES.md:50` (same string in `PARTICLES_FEATURES.json` → `groups[].note`, `EMPTY_NOTES`):
"no system of that name ships in the 206; **heat/steam is the HUD + audio side (G1-14 recorded the weapon
generator heat, not a particle)**".
The data supports the first clause only. The project's own G1-14 record —
`Research/BatmobileGrab/DAMAGE_RULES.md:219` — says the weapon-generator drain path *"ends in
`IncSteamEffect` + `RBatmobileCannon.OverHeat`"*, i.e. a steam **effect** tied to the weapon generator,
not "the HUD + audio side". Nothing in this card's four inputs says which side owns it, or what
`IncSteamEffect` spawns. Under R4/§0.1 the second clause should be `UNKNOWN` (e.g. "no ParticleSystem
named heat/steam in the 206; `IncSteamEffect` (G1-14 §4) implies a steam effect on overheat, its
ParticleSystem is UNKNOWN").
Same class, lower severity: `PARTICLES_FEATURES.md:52` — "wall-scrape sparks are **either** a
material-side effect **or** live outside the Batmobile packages". Neither branch is evidenced; only
"no system in the 206 has scrape/spark in its name" is. Also `:35`: "both sonar systems are referenced by
`RBatmobileSonar` (G1-08)" — `RBatmobileSonar` is an `objects.jsonl` source, not a G1-08/`WEAPONS.json`
one (the row's own "referenced by" cell says so).

### 4. Per-name rows show one package's facts while the `rows` column counts up to six
`script:448-462` (`write_md`) groups rows by name and prints **only `r0`** for emitters, lifetime, spawn,
size, colours and materials, while the `rows` column prints `len(rs)`. Consequences in the doc:
- `PARTICLES_FEATURES.md:114` `Batmobile_Muzzleflash_NoTracer` shows "9 (light×1, mesh×3, sprite×3) emitters",
  but the 4 rows of that name sum to more; the per-name emitters column of the whole `tracer` group sums to
  **28** while the group's own line (`:40`) says **112**. Same for every group: displayed per-name sums are
  roughly 1/4 of the group totals (e.g. cannon-impact 63 shown vs 204; explosion 37 vs 139).
- The facts are not always package-invariant: `Batmobile_HeavyCannon_Impact` (`:141`) has 6 rows in two
  distinct variants (5 emitters / 4 materials / 5 colour boxes vs 8 / 6 / 9). The doc prints the 8-emitter
  variant without naming the package; the other variant is invisible.
- The "206 systems" is really 59 + 59 + 59 + 29 rows of 63 names (one row per package that exports the
  name). The doc never states that rows are per-package duplicates, so "muzzle-flash: 21 systems"
  (`:42`) reads as 21 distinct effects when it is 6 names across 4 packages.
None of the numbers is wrong; the labelling is. A footnote ("emitters/lifetime/etc. are the first row of
that name; group columns are totals over all rows") would close it.

### 5. Name-substring grouping puts the "no tracer" systems in the `tracer` group (R5-adjacent)
`RULES` (`script:66-87`) assigns `tracer` by `re.search("tracer", name)`. `Batmobile_Muzzleflash_NoTracer`
and `_NoTracer_Nv` therefore land in `tracer` — **8 of that group's 16 rows** (`:114`, `:115`), i.e. half
the group is explicitly the *no-tracer* variant. Downstream this is already load-bearing: `T_ROWS.jsonl`
T-FX12 cites "G1-16 tracer: 16 systems / 4 names" as the tracer carrier evidence, and half of that is the
negation. The doc does disclose the rule ("first name rule wins"), but the group carries no note that the
behaviour behind `NoTracer` is the opposite of the group's name, so the grouping is a name fact, not a
behaviour fact. R5 asks for the behaviour; at minimum the note should say the group is name-derived and
that `NoTracer` is present.

### 6. `systems_with_spawn 206` counts 77 systems whose only spawn data is `0..0`/absent
`PARTICLES_FEATURES.md:15` and MODLOG:8435 ("spawn 206/206"). Defined at `script:351` as "has a
`spawn_rate` **or** `required_spawn`", where a stored `0..0` counts as present. Measured: **77 of 206**
rows have no non-zero continuous rate (e.g. `Batmobile_HeavyCannon_Impact`, `Missile_LineMarker`,
`Batmobile_RiotSuppressor_Tracer`); real continuous rates exist for **129**. The Method (`:26`) does
explain that `0..0` means burst/`SpawnPerUnit` "not extracted", but the summary row and the group column
(`:38` hack-fx "0", `:40` tracer "0") present that 0 as a value. "spawn 206/206" should read
"spawn 129/206 continuous, 77 only 0..0 (burst/SPU not extracted)".

### 7. Method text describes a call the code does not make
`PARTICLES_FEATURES.md:28` and `script:375`: materials are "resolved with `Walker.path`". `level_extra`
(`script:170-176`) reads the tag's own `ref` string and never calls `Walker.path`. The values happen to be
right (the ref is already the dotted path; I audited all 1,107 `ParticleModuleRequired` modules and the
`cand[0]` fallback at `:174` was used **0 times**, every candidate carrying `ref_class = Material`), so
this is a documentation error only — but it is the sentence a re-implementer would follow.

### 8. MODLOG accuracy (R14) and evidence cell
- MODLOG:8452 "**Record:** README gained two rows". `Research/BatmobileGrab/README.md` has **no**
  `PARTICLES_FEATURES` row (`grep` over the file returns nothing; the file table lists G1-17…G1-23 but
  skips G1-16). The revert instruction ("delete … the two README rows") therefore points at rows that do
  not exist, and the grab index is missing this card's two files.
- MODLOG:8445 "49 referenced names — **44 from `WEAPONS.json` (G1-08/G1-09)** plus 5 external refs".
  44 is the *in-grab* count from both sources. `WEAPONS.json` contributes 30 names (29 in-grab + 1
  external, `Batmobile_rocketExplosion_TEMP`); the other in-grab names come from `objects.jsonl`.
- Tracker row `GRAB_BACKLOG.md:1284` cites only the `.md` + MODLOG. The card's Out also lists the
  `.json`, and the MODLOG Revert names `Tools/scripts/bmak_particle_features.py`; neither appears in the
  evidence cell, unlike G1-21/22/23 which cite their scripts.

### 9. `referenced by` is stamped per name, not per package
`script:315-317` attaches `referenced_by` to every row with that name. So the three non-`SF` copies of
e.g. `Batmobil_Rocket_Explosion` are all marked "WEAPONS.json (G1-08/G1-09)", although `WEAPONS.json`
resolved that reference to `Playable_Batmobile_SF` index 4976 only (`resolved_to.package/index`).
Measured: **152 rows stamped referenced vs 158 `(package,index)` rows actually referenced**. The group
"referenced" column (e.g. target-markers 20, `:37`) is therefore a name-level count. Low impact, but the
column's provenance is the name, not the object.

## Spot-checks

| value in the doc | where verified |
|---|---|
| `emitters 1433`, `systems 206`, `distinct_names 63` (`PARTICLES_FEATURES.md:9-13`) | `PARTICLES.json`: `sum(len(s["emitters"]))` = 1433, 206 systems, 63 distinct names; same total in the features JSON. |
| `HydraMissile_P` lifetime `0.15..3.2 s`, 5 emitters `(light×2, mesh×1, sprite×2)` (`:181`) | raw `PARTICLES.json` system `Playable_BatmobileJoker_SF` export 2913: lifetimes constant 0.15, uniform 0.5..2.0, 1.6..3.2, 0.8..1.5, constant 1.0 → min 0.15 / max 3.2; 5 emitters with those kinds. |
| `HydraMissile_P` first colour box `Start [2.0, 0.5, 0.1]..[2.0, 0.5, 0.1]` (`:181`) | raw tags: `ParticleModuleColor.StartColor` stored vectors `[[2.0,0.5,0.1],[2.0,0.5,0.1]]` via `grab_particles.vec_pair` on export 2913's levels. |
| `colour_boxes 1290`, `systems_with_colours 183` (`:15-16`) | `sum(len(r["colours"]))` over the 206 rows = 1290; 23 rows without colours; 0 error entries. |
| Coverage `49 referenced names / 44 in-grab / 5 external`, `264 particle ref rows` (`:236-242`) | independent walk of `WEAPONS.json` (30 names, 118 ref dicts) + `objects.jsonl` vehicle-class refs (41 names, 264 rows) → union 49, ∩206 = 44, external = `Batmobile_Burnout`, `Batmobile_rocketExplosion_TEMP`, `Tire_Track_Pulse_P`, `Water_Splash`, `tyreMarks_ribbonTest` — exactly the doc's table. |
| every number in the `.md` is the script's (`R11`) | re-rendered `write_md(doc)` into memory with `open` stubbed out: output **byte-identical** to `PARTICLES_FEATURES.md`. |
| 8 MECHANICS wheel refs (check line) | `coverage.mechanics_wheel` = 8 and all 8 appear in `mechanics_in_objects_refs`; `load_references` enforces `mech - found` empty (`script:522-525`). |

Not verified: anything requiring the game or a package re-read beyond the script's own parser
(`grab_particles.Walker`) — no game was launched, no UPK was written.

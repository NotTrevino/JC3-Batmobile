# Independent review — B-04 · Parts module (`vehicle_parts.vmodc`)

Reviewer: Buffy (did not write this card). Date: 2026-10-31. Read-only pass: nothing outside this
file was written. No game launched, nothing committed, no `GRAB_BACKLOG.md` / `MODLOG.md` /
`Research/` / `Tools/` / game file touched.

Card (`GRAB_BACKLOG.md` §8, lines 1024-1030):

```
#### B-04 · Parts module (`vehicle_parts.vmodc`)   M · deps: B-02, B-03, T-12, T-14, T-18 · serves: APP-5, ANI, ARM-4, LGT-1
Do: 1. Remove `door_f_l`/`door_f_r` and their `door_parts` entries (old PRT-1; keep the index
map documented). 2. Add every new part (`parts[]`: name, model `.lod`, parent, `parent_space_offset`
= pivot, damage type, `has_lights`, `is_deformable` 0, collision ids). 3. Add behaviour entries
(`hinged_parts`, `rotating_parts`, `door_parts`, `aim_part_constraints`) per T-12/TURRET.md.
4. Pack with `eetoc --internal` (R8).
Out: `Working/Parts/bm_vehicle_parts.json` (edit spec) + the module in the build.
Done: `jc3parts.py check` and `jc3adf.py` re-read the built module; every part's model resolves
to a file in the build; `.toc` record for the module has a non-zero offset.
```

Inputs read: §0.5 (R1-R14), the card, the B-04 row in §12 (line 1337); `MODLOG.md` §"B-04 start",
§"B-04 · Parts module — done" (line 16858) and §"B-04 — re-verified"; `Tools/scripts/bm_parts.py`
(1,135 lines); `Working/Parts/bm_vehicle_parts.json`; `Builds/bm-002/{receipt.json, install.ps1,
.ee, .ee.toc}`; the built module and its `tmp/b04/build/bm_vehicle_parts.xml`; `Tools/scripts/
jc3parts.py`, `jc3adf.py`, `aafdiff.py`; and the deps the spec claims (`parts_manifest.json`,
`lights_manifest.json`, `T8_PARTS.json`, `t16_collision.json`, `PRT1_PARTMAP.md`, `PARTS_TABLE.jsonl`).

---

## VERDICT: **minor issues**

The build is sound and the delivered module is what the record says it is: 59 parts, indices
`0…60` with 1/2 gone, the `.toc` record internal at offset 16,400,188 / 39,278 B, the packed bytes
byte-identical to the staged module, all 59 part models and their 222 `.rbm` present and packed,
the 40 surviving parts field-identical, and the 19 new rows matching T-12's behaviour and damage-type
values exactly. The card's Do steps are met and no value is invented.

The issues are about **what the evidence proves**, not what was built:

* the card's first Done clause names `jc3parts.py check` as a check of the *built* module, and that
  command never reads the build (it reads the donor table, the test-091 `DeformPoints` dump and the
  fleet table) — so the Done as written is carried by different commands;
* `bm_parts.py --check` compares spec↔build and never re-runs the plan, so it cannot catch a changed
  input or an edited spec (the R11 "`--check` re-derives" claim is stronger than the code);
* `aafdiff`'s "exactly 100 files" reproduces only on the `aaf` subtrees, not on the build roots the
  log names, and the whole-tree diff hides one file that exists only in bm-001;
* R9's two budgets are reported only inside `receipt.json` (with R9 declared **open**), not in the
  check output or the §12 row;
* three reporting gaps: the hinge rows can carry only `part_index` (schema), so T-12's flap angles
  are not written anywhere and the spec does not say so; 7 new parts use damage types that fall back
  to `Default`; `receipt.checks` is empty.

None of these changes the bytes in `Builds/bm-002`. All of them change what the card is entitled to
claim.

---

## Check output (verbatim)

The card's `--check` command, re-run in `E:/Modding/JustCause3/JC3-Batmobile` (`--check` writes nothing: the
spec's mtime stayed 00:44):

```
$ python Tools/scripts/bm_parts.py --check
1. .toc record  sportsmuscle_vehicle_parts.vmodc: offset=16400188 size=39278 (PASS)
2. jc3adf re-read sportsmuscle_vehicle_parts.vmodc: 39278 B, 59 parts, 3915 rows
3. models resolve 59/59 parts; 0 missing .rbm, 0 not packed
4. surviving parts 40 re-read identical: 0 field(s) moved, 4 re-parented (['sportsmuscle_door_f_l_window', 'sportsmuscle_l_mirror', 'sportsmuscle_door_f_r_window', 'sportsmuscle_r_mirror'])
5. model bytes (distinct .rbm the module references): 8271315 B = 8077.5 KB (222 files); bm-001 7032.4 KB (151 files), delta +1045.1 KB
PASS: Builds/bm-002 re-read (18E55FE4AF78E8E9�, 604 .toc records, 59 parts, 0 problem(s))
EXIT=0
```

The card's other named command, re-run:

```
$ python Tools/scripts/jc3parts.py check
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls back to Default damage
EXIT=0
```

The `jc3adf` re-read of the built module (the card's third named tool):

```
$ python Tools/scripts/jc3adf.py info Builds/bm-002/aaf/…/sportsmuscle_vehicle_parts.vmodc
sportsmuscle_vehicle_parts.vmodc: 39278 B, 31 types, 106 names
  instance VehicleParts type VehicleParts at 0x50 size 0x81cc
  …
  HingedPart                 code=1 size=   1 members=1
  RotatingPart               code=1 size=  44 members=8
EXIT=0
$ python Tools/scripts/jc3adf.py dump Builds/bm-002/aaf/…/sportsmuscle_vehicle_parts.vmodc --paths | wc -l
59
```

### Output paths

Both `Out:` paths exist and are non-empty: `Working/Parts/bm_vehicle_parts.json` (50,173 B, schema
with `parts`/`behaviour`/`omissions`/`unknowns`/`module`/`build`) and the module inside the build
(`Builds/bm-002/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/
sportsmuscle_vehicle_parts.vmodc`, 39,278 B `4FA283FC…`), plus `Builds/bm-002/receipt.json`,
`install.ps1` and the `.ee`/`.toc` pair the card's Done names.

---

## Issues

### 1. `jc3parts.py check` does not read the built module — the card's first Done clause is carried by other commands (Done wording)

`Tools/scripts/jc3parts.py:117` (`epe_parts()`) reads `Research/JC3Grab/ENTITIES.md` §"Donor parts";
`deform_values()` reads `Working/Translation/current.json`, whose own `build` field is
`E:\Modding\JustCause3\JC3-Batmobile\Builds\test-091`; `check_parts_table()` reads
`Research/JC3Grab/PARTS_TABLE.jsonl`. Nothing in the command touches `Builds/bm-002`. Its output says
so out loud: **"donor table has 42 parts"** while the build the card made has 59.

Consequences:

* The first Done clause ("`jc3parts.py check` … re-read the built module") is not what that command
  does. What does re-read the build is `bm_parts.py --check` step 2 (jc3adf on the `.toc`-sliced
  bytes) and the separate `jc3adf.py info/dump <built module>` — both real, both re-run above. So the
  requirement is met; the record pairs a donor-side gate with a build-side claim.
* The gate is structurally blind to the build's most likely inconsistency: the spec's own `unknowns`
  says `sportsmuscle_vehicle_deform.vmodc` still names parts **1 and 2** as deform targets, and
  `jc3parts.py check` cross-checks the *live* `DeformPoints` (test-091), not bm-002's, so it cannot
  see whether the build's 59-part module and its deform module still agree.

### 2. `--check` does not re-derive the plan (`spec` ↔ build, not inputs ↔ spec) — R11 is weaker than claimed

`main()` calls `build_plan()` only under `--write` (`bm_parts.py:1123`); `check()` (line 927) loads
`Working/Parts/bm_vehicle_parts.json` and compares it to the built module. Every check that matters —
the 19 rows' name/model/parent/damage type/behaviour/`has_lights`/`is_deformable`/collision ids, the
pivots, the behaviour arrays — is *spec vs build*. Not one is *manifest vs spec*. So:

* a hand-edited spec whose module was built from the edit would pass;
* a changed `parts_manifest.json` / `lights_manifest.json` / `T8_PARTS.json` (the deps) would leave
  `--check` green with a stale spec and stale module.

`GRAB_BACKLOG.md` §0.2 step 5 asks that "every value must be re-derivable by a command (`--check`
mode re-derives and compares)". For B-04 the re-derivation is `--write` only; `--check` cannot prove
the spec was not typed. (Determinism is asserted in the MODLOG — two `--write` runs, identical `.ee`
hash — but a read-only review cannot re-run `--write` into `Builds/bm-002`, so that claim is taken on
trust.)

### 3. R9's budgets are reported only inside `receipt.json`, and the one number the check prints reads as a breach

`receipt.budgets` is honest and explicit:

```
"model_kb": 8077.456, "model_cap_kb": 4915.0, "model_files": 222,
"base_model_kb": 7032.369, "delta_kb": 1045.087, "textures_added": 0,
"note": "model bytes = every distinct .rbm reachable from the built module's part models. This is NOT
 the R9 appearance figure: it also counts the 40 shipped Serpente part meshes the module still
 references … bm-002 does not re-emit body/wheels, so R9 is reported as the delta against bm-001 and
 stays open until that re-emit lands. No .ddsc is added, so the texture budget is unchanged."
```

That is the right handling of a metric that is not R9's (B-02 measured the appearance set at
4,790.9 KB, B-03's net 4,899.6 of 4,915 KB — both match their rows). Two gaps remain:

* `--check` prints `8271315 B = 8077.5 KB` with **no cap and no note**, in the same output whose
  other lines quote PASS. A reader of the check alone sees a model number 3,162 KB above R9's 4,915
  wall and no statement that it is not the R9 figure.
* §12's B-04 row carries **no budget line at all**, so the tracker (which is what the next session
  reads) never states R9's status. R9 says "every build reports both"; here only the receipt does,
  and it says "open".

### 4. `aafdiff`'s "exactly 100 files" is right for the `aaf` trees and wrong for the paths the log names — and the whole-tree diff hides one file

Re-run:

```
$ python Tools/scripts/aafdiff.py Builds/bm-001/aaf Builds/bm-002/aaf
identical=588 changed=2 onlyA=0 onlyB=98      # 2 changed (@files.xml, module) + 98 new = 100 ✓

$ python Tools/scripts/aafdiff.py Builds/bm-001 Builds/bm-002
identical=1172 changed=8 onlyA=1 onlyB=196
```

The second form is what the MODLOG's sentence ("`aafdiff` vs bm-001 is exactly 100 files") suggests
when read literally, and it produces a different answer because `Builds/bm-002/verify/` duplicates
every changed/new file. It also surfaces `applied.json`, present only in bm-001
(`{"source": null, "base": "Builds/bm-001/aaf", "applied": []}` — B-01's empty record). Harmless, but
"no collateral" should be scoped to the `aaf` tree and the dropped file named.

### 5. The hinge rows can only carry `part_index`, so T-12's flap extents are written nowhere — and the record does not say so

`jc3adf info` on the built module: `HingedPart code=1 size=1 members=1`, and the XML confirms the one
member is `part_index` (int8). So the 4 `hinged_parts` rows `[56, 57, 58, 59]` are **schema-complete**
— there is no angle/axis member to fill. But T-12 decoded flap extents (20/30° blade, 54.8° piston),
and neither the spec's `unknowns` nor its `omissions` says that those numbers have no carrier in this
module. "Behaviour rows … per T-12" therefore invites the reader to believe the extents ship. The same
kind of silence would be wrong for `RotatingPart`, and there the spec does it right (it labels
`rpm_multiplier` 1.0 / `min|max_rpm_visible` −1 / `rpm_opacity_transition` −1 as "the module's own
type definitions (defaults)").

### 6. 7 of the 19 new parts use damage types with no `PartDamageType` row in the vehicle's table

From the spec: `batmobile_machine_gun` 52 → `Boat_Generic`; `batmobile_missile_pod_l/r` 54/55 →
`Train_Generic`; the four `batmobile_aero_flap_*` 56–59 → `Plane_Control_Surface`. B-09's row records
that `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic` (+ `Boat_Antenna`) have no
`PartDamageType` row in the 24-row private health module, so those parts resolve through `Default`.
The values themselves are T-12's (correct provenance), but B-04 is where the parts are created and its
`unknowns` says nothing about the runtime fallback; only B-09's row does. A reader of B-04 alone
would think each part got a real damage row.

### 7. Minor — the "0,0,0 centroid" source sentence is a rounding, not the file's value

The spec's provenance table says the centroid/`deformation_centroid_offset` are 0 because "this
module's own four non-deformable wheels carry 0,0,0". Decoded from bm-001 (and bm-002), the four
wheels' `centroid` is `[0, ±1.907e-08, 0, 0]` — float noise, not exactly zero. The new parts write
exactly 0.0. Trivial, but the cited value is not what the file holds.

### 8. Minor — `receipt.checks` is empty

`Builds/bm-002/receipt.json` has `"checks": []` while the MODLOG documents five checks and a PASS
line. A consumer of the receipt alone cannot see any Done result; the only check-shaped content in it
is the `budgets` block. (The `.ee`/`.toc`/module sha256 in the receipt are correct — I verified the
module hash against the staged file.)

### 9. Minor — the spec points at scratch XML that `--check` does not regenerate

`module.xml` = `tmp/b04/build/bm_vehicle_parts.xml` (569,814 B today). `tmp/` is scratch, the file is
produced by `--write` only, and nothing in `--check` touches it. The durable record (staged module +
receipt sha256) is fine; the pointer can dangle on a cleaned tree.

### R5 check (behaviour vs member name)

B-04 does **not** invent a name→behaviour mapping: every new row's `behaviour` and `damage_type` are
copied from T-12 and carry `T-12 P-xx` as their source. I verified them against `T8_PARTS.json`:

| part | T-12 row | behaviour / damage type (T-12) | built module |
|---|---|---|---|
| `batmobile_turret` 50 | P-01 | `Turret` / `Land_Generic` | same |
| `batmobile_cannon` 51 | P-02 | `Cannon` / `Land_Generic` | same |
| `batmobile_machine_gun` 52 | P-03 | `GatlingGun` / `Boat_Generic` | same |
| `batmobile_riot_suppressor` 53 | P-04 | `Cannon` / `Land_Generic` | same |
| `batmobile_jet` 60 | P-05 | `EngineRotatingPart` / `Land_Generic` | same |
| `batmobile_aero_flap_*` 56–59 | P-09…P-12 | `AirBrake` / `Plane_Control_Surface` | same |
| `batmobile_missile_pod_l/r` 54/55 | P-14/P-15 | `None` / `Train_Generic` | same |

What the behaviour field cannot promise is behaviour: `aim_part_constraints` is correctly **empty**
(TURRET.md measures 0 rows on the six turreted vehicles), so the turret's aiming is not carried by
this module and the row says so. Any doubt about whether `Turret`/`Cannon`/`GatlingGun` are the right
behaviours belongs to T-12, which owns that mapping; B-04 transmits it faithfully.

---

## Spot-checks (value, where verified)

| # | value in the record | where verified | result |
|---|---|---|---|
| 1 | "59 parts", indices `0…60`, doors 1/2 gone | `jc3adf.parts()` on the staged module | 59 parts, max index 60, no part with index 1/2; no part parents to 1/2 and no `children_part_indices` array still names them ✓ |
| 2 | ".toc record offset=16400188 size=39278", and the packed bytes are the staged module | `eetoc.read_toc` + `unaaf` on `Builds/bm-002/….ee` | record `(16400188, 39278)`; sliced sha256 `4FA283FC…` == staged module sha256 `4FA283FC…` ✓ |
| 3 | "model bytes … 8271315 B = 8077.5 KB (222 files); delta +1045.1 KB" | recomputed from the 59 parts' `.lod` files and the `.rbm` they name | 222 distinct `.rbm`, 8,271,315 B (8,077.5 KB) ✓ |
| 4 | "599/11,643 fleet parts" with collision ids −1/−1 (provenance for the new parts' `-1/-1`) | `Research/JC3Grab/PARTS_TABLE.jsonl` (`body` −1 = 761, `ray` −1 = 599, both = 599 of 11,643) | 599 exactly ✓ |
| 5 | "the body's `kids` count fell from 15 to 13"; "604 records (506 + 98 appended)" | decoded both modules; `read_toc` on bm-001/bm-002 `.toc` | body kids 15 → 13; 506 → 604 records ✓ |
| 6 | 19 new parts' `parent_space_offset` = pivot − parent origin | spec vs `jc3adf.parts()` vs B-02/B-03 manifests (`batmobile_turret` pivot `[1.3e-05, 0.876249, 0.333226]`) | module offsets `[0.0, 0.8762, 0.3332]` etc. match the spec and the pivot ✓ (B-02's manifest key is not `pivot_m` for these rows, so the parent-origin chain itself could only be spot-checked, and it agrees) |
| 7 | byte diff vs bm-001 | `aafdiff` on the `aaf` trees | 2 changed + 98 new = 100 files, exactly 1 module + 79 `.rbm` + 19 `.lod` + `@files.xml` ✓ (see issue 4 for the whole-tree form) |

Cross-cutting:

* **R11 (counts generated):** the spec is produced by `bm_parts.py --write`; every table value in it
  carries a `source`/`provenance` string. The one structural weakness is issue 2 (check does not
  re-derive).
* **R4 (provenance):** each written field names a source, and the sources are real files. Nothing is
  labelled `assumed`; the jet's missing rotation axis, the canopy/bay/yoke rows with no part, and the
  removed doors are recorded as omissions/removals with reasons, not filled. The three `unknowns`
  (centroid semantics, the deform module still naming 1/2, body/wheels not yet re-emitted) are the
  right ones to carry forward.
* **R7/R8:** no shared module is edited — the module is the entity's own member, packed with
  `eetoc --internal` (offset 16,400,188 proves the internal record); the base bm-001 module and the
  game files are read-only inputs.
* **R9:** see issue 3 — reported in the receipt with R9 declared open, omitted from the check output
  and the §12 row.

## What is needed for this card to be citable as evidence downstream

1. Re-word the Done clause (or the §12 row) so it names what actually re-reads the build:
   `bm_parts.py --check` (which imports `jc3adf`) and `jc3adf.py info/dump <built module>`; keep
   `jc3parts.py check` as the *donor-side* gate it is, and say so.
2. Add a `--check` path that re-derives the spec from B-02/B-03/T-12 in memory and diffs it against
   the file on disk (the pattern the other B cards use), so a stale spec fails.
3. Put R9's status in §12 / the check output, not only the receipt: either the appearance figures
   (4,899.6 of 4,915 KB per B-02/B-03) with the "not re-emitted yet" caveat, or the receipt's
   "open" wording.
4. One line in `unknowns` for (a) the flap extents having no member to carry them, (b) the three
   damage types resolving through `Default`, and (c) scope the `aafdiff` "100 files / no collateral"
   claim to the `aaf` tree, naming the dropped `applied.json`.

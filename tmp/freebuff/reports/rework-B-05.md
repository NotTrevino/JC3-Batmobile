# B-05 rework — response to the independent review

**STATUS: DONE.** Every issue in `tmp/freebuff/reports/review-B-05.md` (8 of 8) was re-verified against
the built `.epe`, the spec JSON and the generator; all were **CONFIRMED** and fixed in
`Tools/scripts/bm_entity.py`, then the build was regenerated with `--write`. **0 REJECTED.** The card's
`--check` passes with the corrected census; the tamper test fails and restores as required.

No game launch, no write under `D:/Games` or `E:/Games`, no shared module, no git, no secrets.

## Per-issue disposition

### 1. `attach.vehicle` carried the donor's `weapon_anchor` — CONFIRMED
**Evidence (before):** exported `Builds/bm-005/…/_civilian_01.epe` had four `attach.vehicle` objects,
each with three part refs:
`[('5C19E7E0','batmobile_cannon'), ('80201E4D','batmobile_turret'), ('A90F5E74','weapon_anchor')]`.
`weapon_anchor` is not in `Working/Parts/bm_vehicle_parts.json` (19 names) and `b"weapon_anchor"` is
absent from `sportsmuscle_vehicle_parts.vmodc` (39,278 B). The check's part arm filtered on
`startswith("batmobile_")` and its PASS printed a literal `0 dangling`.
**Fix:** the generator omits the third ref when cloning the APC point (no invented part name) and
records it in `declared[]` (one entry per weapon row). The check now tests the point refs by their
measured member ids (`5C19E7E0`, `80201E4D`, `A90F5E74`) and counts `dangling` instead of printing a
literal. After `--write` each point has exactly the two T-11 refs; a tamper to `weapon_anchor` is
caught by both the plan comparison and the new arm.

### 2. Both `w618` components are unbound and the limit was not stated — CONFIRMED
**Evidence (before):** root slots `851CAABE` → `DF009C2C=FFFF8002` (w602), `00568A74` →
`DD9B64C0=FFFF8005` (w603), `AC0BC788` = `00000000`, `mounted_weapon` = `00000000`;
`8AE3029C=FFFF8008` (w618 missile) and `AAE79E16=FFFF800C` (w618 emp) each occurred **once** — their
own `_object_id`. `Research/JC3Grab/WEAPON_WIRING.md:31` calls such a component dead weight and
`Working/Translation/T7_WEAPONS.md:68` already says WPN-3's missiles have no slot.
**Fix:** `unbound[]` is now computed from the built graph's text and written to the spec and receipt
(`counts.unbound_weapons = 2`); the check prints `2 unbound (declared)`. The limit is in the card
report and the §12 line: no free root slot exists, T-11 has no WPN-3 carrier and T-WP4 is blocked, so
the missiles are present but cannot fire. No slot was invented.

### 3. `weapon_type` 1 on both `w618` components contradicted the measured donor — CONFIRMED
**Evidence (before):** built components read `weapon_type` **1**; `Research/JC3Grab/SIGNATURE_DIFF.md:252`
measures the donor `CMissileWeaponBase w618_sportsmuscle_missile` at **2**, and
`WEAPON_WIRING.md:31` says every weapon component carries 2. The `src` strings cited rows/sockets, not
a type.
**Fix:** the typed `weapon_type` constant was removed from `WEAPONS`. Every component copies the
measured APC template value, and the two w618 clones are cross-checked against
`SIGNATURE_DIFF.json`'s `weapon.weapon_type`; a mismatch aborts the run. The built graph now reads 2
for all four components.

### 4. The six custom lights all inherit `Front_Left_Point`'s transform — CONFIRMED
**Evidence (before):** each of the six had `id:A04C3B1E` identical to base `Front_Left_Point`
(`0.7198463,-0.6040228,-0.3420202,0, …`) and `preset_id` = `Front_Left_Point`; step 3 wrote only
`diffuse`.
**Fix:** no matrix is invented — T-18's custom rows carry none. `declared[]` now records that the 11
positional slots (including the matrix and `preset_id`) are inherited, so all six sit at that lamp
until B-07's module anchor binds them. The card report and §12 carry the same limit.

### 5. "467 objects / 47 classes" counted the classless root and a `None` class — CONFIRMED
**Evidence (before):** the exported graph had 467 `<object>` elements, **466 with `_class`**, and
**46 distinct classes**; the base was 416 / 415 classed / **43** classes. `jc3wiring.parse_epe` returns
`cls=""` for the classless root, and the census counted that empty string as a class.
**Fix:** class counts filter `if o.cls`; `BASE_CLASSES` is 43; the build reports
`classed_objects` separately and the PASS line prints `466 classed + 1 classless root, 46 classes`.
The object count (467) is unchanged.

### 6. The "part name resolves" arm was a tautology and the module proof was ad hoc — CONFIRMED
**Evidence (before):** lines 635–637 compared the parts list to the same JSON reloaded; the PASS
figure was `len(parts)`. The 39,278 B / 0-absent evidence existed only as an unnamed one-off.
**Fix:** `check()` now reads `Builds/bm-005/aaf/models/…/sportsmuscle_vehicle_parts.vmodc` and
verifies every B-04 name against its bytes, failing on any absence; PASS prints `19/19 part name(s)
in the module`. The point refs are verified by member id, so a non-`batmobile_` name can no longer
hide.

### 7. The report's skip/edit accounting did not match the spec JSON — CONFIRMED
**Evidence (before):** `skipped[]` = **69** (60 `no named world member` + 9
`3 object(s) with that class+name`); the report said "the other 60". The spec had **12** distinct
light edit nodes over **16** edit rows; the 19 edits include 2 `CCar` slot pointers and 1 `*`
interaction row, not 13 lights / 19 light edits.
**Fix (prose, not generated output):** `tmp/freebuff/reports/B-05.md` now says 69 = 60 + 9 and 12
distinct lights / 16 rows / 19 total edits; the §12 line records 69 and 12/16/19. The MODLOG's
historical "done" section is left as written (R14 append-only); the `B-05 rework — done` section
states the corrections.

### 8. Done 3's equality is definitional — CONFIRMED
**Evidence (before):** `expected_objects = BASE_OBJECTS + len(added)` where `added` is the built graph
minus base, so `got == 416 + 51` holds unless a base object vanishes; the 27 planned rows were never
compared to 51.
**Fix:** the check still keeps the equality (it does catch a lost base object), but the PASS text now
says `count definitional; plan equality enforced above`, and the card report explains that the
object-for-object plan comparison is the real guard. No functional change was needed.

## Files changed

| file | change |
|---|---|
| `Tools/scripts/bm_entity.py` | generator fix for issues 1–6 and 8: derive `weapon_type`, omit the donor-only attach ref, `declared[]`/`unbound[]`, class census without the empty `cls`, module-bytes part check, part refs by member id, corrected PASS text/docstring |
| `Working/Entity/bm_epe_edits.json` | regenerated by `--write` (adds `declared`, `unbound`, `counts.unbound_weapons`, `base_classes` 43, `built.classed_objects`) |
| `Builds/bm-005/…/v0300_car_kensington_sportsmuscle_civilian_01.epe` | regenerated: **124,488 B**, sha256 `f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf` (was 124,520 B `d118c0aa…`) |
| `Builds/bm-005/receipt.json`, `install.ps1` | regenerated by `--write` (receipt now carries `declared`/`unbound`; bytes 124,488) |
| `tmp/freebuff/reports/B-05.md` | prose corrections (bytes/sha, 502,109 B XML, counts, 69 skipped, 12/16/19, new limits) |
| `GRAB_BACKLOG.md` §12 | only the `B-05` line, updated to the reworked evidence |
| `MODLOG.md` | `B-05 rework — intended change` + `B-05 rework — done` (appended) |
| `tmp/freebuff/reports/rework-B-05.md` | this report |

The `.epe` and the spec JSON were produced only by `--write`; no generated output was hand-edited.
A pre-rework copy of the generator is at `tmp/b05_entity.pre-rework.py` (revert instructions are in
the MODLOG section).

## `--check` output (verbatim, final)

```
$ python Tools/scripts/bm_entity.py --check
PASS: 4 weapon component(s), 2 unbound (declared), 9 weapon point(s), 28 light(s) (6 T-18 custom), 19/19 part name(s) in the module, 0 dangling | objects 416 + 51 = 467 (466 classed + 1 classless root, 46 classes) | round trip identical (count definitional; plan equality enforced above)
CHECK_EXIT=0
```

Round trip, run by hand on the regenerated file:

```
$ ./Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe --e <built .epe> a.xml
$ ./Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe -i a.xml b.epe
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf *<built .epe>
f4abe91da0bc3ce371edb1da135e0eb34357555741a409cb377b0785cb4e9fdf *b.epe
$ ./Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe --e b.epe b.xml
$ cmp a.xml b.xml && echo "XML IDENTICAL ($(wc -c < a.xml) B)"
XML IDENTICAL (502109 B)
```

Determinism: a second `--write` produced the same `f4abe91d…` sha (124,488 B).

## Tamper test (must fail)

One `attach.vehicle` part ref (`id:5C19E7E0` on `w602`) set back to the old `weapon_anchor` and
re-imported into the built `.epe`:

```
FAIL: the built .epe differs from the re-derived plan: 1 object(s) missing, 1 unexpected, e.g. missing ["('SWeaponPoint', 'attach.vehicle', (('_object_id', 'EC9CC816=FFFF8003'), ('fire_effect', (0.0,)), ('id:5C19E7E0', 'batmobile_cannon'), …
FAIL: Done 2: point 'attach.vehicle' binds 'weapon_anchor' via id:5C19E7E0, not a B-04 part
TAMPER_EXIT=1
```

Restored from `tmp/b05rework/orig.epe`; sha `f4abe91d…`; `--check` PASS again. `t_rows.py check` →
`check ok`; `status_audit.py --check` → `STATUS.md is current`.

## Residual observation (not one of the eight issues, not fixed here)

The two `w618` components are still clones of the **APC's `CBulletWeaponBase`**, while the donor
`w618` is a `CMissileWeaponBase` (`SIGNATURE_DIFF.md:252`). The review did not raise it and this
rework does not change it: fixing it needs a measured missile-component template and a re-plan of
the cloned members, which is a T-11/B-05 scope decision, not a value that can be derived from the
files read here. It is carried in the §12 line's "APC clones … for B-06" limit.

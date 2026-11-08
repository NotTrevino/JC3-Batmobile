**STATUS: DONE — all five V-01 file gates GREEN on `Builds/bm-RC2`.** `.ee` sha256 `886a7919e205fc3b…`, 607 `.toc` records, 5 edited `.vmodc` modules; Model 4,791.3 KB of 4,915, Texture 5,855.8 KB of 7,065. `v01_rc2.py --check` re-derives `verify/files.{md,json}` byte-identically.

# V-01 file gates on `Builds/bm-RC2`

## Files written

| file | what |
|---|---|
| `Tools/scripts/v01_rc2.py` | the gate runner (`--write` / `--check`); reads the packed `.ee` through its `.toc`, never edits the build |
| `Builds/bm-RC2/verify/files.md` | per-gate page with the tools' verbatim output |
| `Builds/bm-RC2/verify/files.json` | the same numbers plus the per-module rows |
| `tmp/freebuff/reports/v01-file-gates-rc2.md` | this report |

`Builds/bm-RC2` was not modified except for the two `verify/files.*` files this card asks for. No install, no dropzone, no game.

## Gate results

```
GREEN spec      spec_check exit 0: CarLight: checked 24 blocks over 8 lamp parts; spec mismatches 0; light RBMs hash-equal 24/24
GREEN parts     jc3parts check exit 0: ... built module (via .toc) decodes 61 parts, B-04R 61, Working/Parts manifest 59 (stale: pre-B-04R)
GREEN budget    Model non-vanilla 4,791.3 KB of 4,915 (reachable 7,166.1 KB, 189 .rbm) | Texture resident 5,855.8 KB of 7,065
GREEN adf       jc3adf.py info on 5 edited .vmodc: 5 re-read, toc slice equal 5/5, bad 0
GREEN readback  values/slices proven 12, failed 0
ALL GREEN
```

## 1. `spec_check.py`

```
python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights
CarLight: checked 24 blocks over 8 lamp parts; spec mismatches 0
```

Ran directly (exit 0), and every one of the 24 light RBMs named by `lights_manifest.json` hashes equal in the RC's aaf (24/24).

## 2. `jc3parts.py check`

```
python Tools/scripts/jc3parts.py check
ok: 40 part indices agree between .epe and DeformPoints; 4 wheel points -> 4 wheel parts; 21 light points -> 12 parts
ok: donor table has 42 parts, names 42/42 with DeformPoints, lights 12 parts match, wheels 4 match, damage types 17 used
  note: ['Boat_Antenna'] not in this vehicle's VehicleDamage table (24 types) - the part falls back to Default damage
```

Exit 0. The built parts module — read through the `.toc`, not from `receipt.json` — decodes **61 parts**, which is B-04R's own step (`'parts': 61`). `Working/Parts/bm_vehicle_parts.json` still says **59** (`parts_after`), i.e. the manifest predates B-04R; that divergence is named in the page rather than hidden.

## 3. `bm_budget.py` (Model ≤ 4,915 KB, Texture ≤ 7,065 KB)

```
Model non-vanilla 4,791.3 KB of 4,915.0  (reachable 7,166.1 KB, 189 .rbm)
Texture resident 5,855.8 KB of 7,065.0
```

`bm_budget.measure()` keys its module read on `bm_parts.MODULE`, the pre-B-18 path; in this tree the module lives at `…/sportsmuscle/batmobile/sportsmuscle_vehicle_parts.vmodc`, so the gate runs **the same rule** (`reachable .rbm minus vanilla-identical bytes`) against this tree's path. Both caps have headroom: 123.7 KB under Model, 1,209.2 KB under Texture.

## 4. `jc3adf.py` re-read of every edited module

`jc3adf.py info` on each of the 5 edited `.vmodc` (exit 0 each), and each module's `.toc` slice equals the aaf file byte for byte:

| module | exit | nodes | toc slice == aaf |
|---|---|---|---|
| `lave_health_medium.vmodc` | 0 | 246 | yes |
| `batmobile_health_medium.vmodc` | 0 | 246 | yes |
| `v0300_..._custom_land_global.vmodc` | 0 | 61 | yes |
| `v0300_..._lights.vmodc` | 0 | 451 | yes |
| `sportsmuscle_vehicle_parts.vmodc` | 0 | 4,071 | yes |

## 5. Read back every edited value through the built `.toc`

12 values/slices proven, 0 failed:

- 5× each edited module's `.toc` slice == the shipped aaf bytes;
- the B-09 health rows' target values re-read from the `.toc` slice via `jc3adf.walk` (module member paths, exact/1e-3 match);
- B-10: the physicsc `.toc` slice equals the aaf file and re-reads clean under `jc3hkx.py check --file` — `902,384 B`, `check ok`. (It is **not** `Working/Collision/batmobile.physicsc`, 340,368 B: B-10b/B-10c re-boxed and re-encoded it after the B-10 install, so the source file is the wrong oracle here and was not used as one.)

## UNKNOWNs / limits

- **Runtime acceptance** of the packed `.ee` (load, spawn, render) — phase Q; no game was launched.
- **The 59-vs-61 parts manifest.** Which value downstream tooling should read is not settled by this pass: B-04R's step and the built module agree on 61, the Working manifest says 59. Left as recorded.
- **`spec_check.py` covers the light blocks only** (the CarPaint arm needs an assembly dir + template the RC does not ship); no paint-spec assertion is claimed here.
- **`bm_budget.measure()` path assumption** noted above; the rule is reused, not changed, and `bm_budget.py` itself was not edited.

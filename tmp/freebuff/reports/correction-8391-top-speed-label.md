# Correction 8391 — T-E5's 336.4 km/h is an assumed label, not a measurement

STATUS: done. Option **(a)** was taken: 336.4 km/h stays as the **top of a 300-336 km/h band labelled
`assumed`**, the drag write `0.55 -> 0.1213` is **withdrawn**, and the top-speed prediction is the
**267 km/h terminal** that T-A2's Cd 0.55 actually produces at T-E2's 894.7 kW. Every place that
presented the label and the drag as one translation now presents them as two decisions.

## 1. What was wrong

The pair `official_top_speed 336.4` + `drag_coefficient 0.1213` read as one decoded translation. It
is not:

* **336.4 km/h is a label.** BmAK has no absolute speed member (`COMPROMISES_T`: "BmAK has no speed
  member"); the only source is the wiki's 209 mph figure, which the operator signed off on
  2026-10-23 as the mod's target. The sign-off covers the label, not a file value, and not the drag.
* **0.1213 is a balance value.** It was derived backwards — 336.4 km/h (93.44 m/s) at 2921 N·m,
  A = 6.635 m² — so that the label would be reachable. `build-d10-handling-values.md` §5.2 and its
  value table carried it as if it were the aero translation.
* **The old arithmetic did not even close.** Cd 0.1213 × 6.635 = 0.805 m² needs only
  P = ½·rho·Cd·A·v³ ≈ 394 kW at 93.44 m/s, not the 894.7 kW it cited; the "260 km/h" the old cell
  quoted did not follow from its own inputs either. 336.4 km/h at 894.7 kW needs Cd ≈ 0.276.

## 2. The decision and its arithmetic

Kept: `vehicle_misc.official_top_speed` **336.4** as the top of the **300-336 km/h** band, class
`assumed`.

Not written: `land_aerodynamics.drag_coefficient` stays **T-A2's class fit 0.55** (read back from the
built `.toc` at `0.550000012`). The withdrawn write is recorded in
`Working/Translation/t1_handling.json` as `would_be: "0.55 -> 0.1213"`,
`class: "rejected (balance value reverse-engineered from an assumed label)"` with the full derivation
of the rejection.

Predicted terminal at the built values:

```
T-E2 torque 2921 N.m × T-E3 wash 0.65 × omega(4500 rpm)      = 894.7 kW
Cd.A = 0.55 × 6.634667                                        = 3.649 m²
v = (2P / (rho Cd A))^(1/3), rho 1.2                          = 74.2 m/s = 267 km/h
```

265 km/h at rho 1.225. This — not 336.4 — is the number a Q-2 A2 take compares with, on a declared
±10 % band of **240-294 km/h**. A terminal inside 300-336 km/h would **falsify the Cd 0.55 / T-E2
pair**, not pass the label: any top-speed take tests **reachability of a label, not fidelity to
BmAK**.

## 3. Files changed by this correction

| file | change |
|---|---|
| `Working/Translation/t1_handling.json` | the T-E5 drag write is `rejected`, with the 0.1213 rejection arithmetic printed |
| `Working/Translation/t1_handling_edits.json` | carries no `drag_coefficient` edit (verified by `t1_apply`) |
| `Working/Translation/T1_TRANSLATION.md`, `T_ROWS.jsonl`, `GRAB_BACKLOG.md` | T-E5 row: 300-336 band, `assumed`, Cd 0.55, 267 km/h predicted, 0.1213 rejected (correction 8391) |
| `tmp/freebuff/reports/build-d10-handling-values.md` §5.2 | finding 2 rewritten: "a labelled band, not a translation, and the drag is not tuned to it"; 336.4 no longer reads as measured |
| `Working/Q/PREDICTIONS.md` (+ `Tools/scripts/v05_driving.py`) | D-2 now predicts **267 km/h / 240-294 km/h**, class `derived` vs `assumed`, with the label-reachability sentence; the D-2 UNKNOWN entry now says the *label* is what is unmeasured, not the terminal |
| `Tools/scripts/v05_predictions.py` | Q2-A2 row: 267 km/h at Cd 0.55, label not a pass criterion |
| `Tools/scripts/b10_handling.py` | regenerates the d10 §5.2 wording above |
| `Tools/scripts/t23_closeout_inventory.py` + `T23_INVENTORY.{json,md}` | T-E5's inherit comment and closeout row no longer say "Cd 0.1213 / 260 km/h"; the row is the corrected ledger text |
| `MODLOG.md` | entry "Correction 8391 — T-E5 top speed is a label, not a measurement" |

Not touched: any game install, `E:/Modding/_shared/gamedata/`, `Builds/` bytes, the RC4 lineage. No value
was written, so no build changed.

## 4. Checks actually run

```
$ python Tools/scripts/t1_apply.py --edits Working/Translation/t1_handling_edits.json \
      --current Working/Translation/rc4_current.json
check ok: every edit matches the build, the table and a real member          # exit 0

$ python Tools/scripts/b10_handling.py --check
CHECK PASS - 52/52 read back through the .toc (17/17 payload), 6 module(s) changed, sizes equal True

$ python Tools/scripts/bm_build.py --tag bm-RC4-handling --check
PASS: Builds/bm-RC4-handling re-read against its receipt (2312DCBA4B392FBF…, 506 .toc records)

$ python Tools/scripts/v05_driving.py --write   # then --check
21/21 oracles pass
PASS D-2 terminal re-derives as (2P/(rho Cd A))^(1/3) = 267 km/h at the built Cd 0.55
PASS document: PREDICTIONS.md matches the regenerated driving sheet

$ python Tools/scripts/t23_closeout_inventory.py --check
(see §5 - regenerated to the corrected ledger text, then re-checked green)
```

The built module reads back `drag_coefficient = 0.550000012`
(`Builds/bm-RC4-handling/verify/d10_readback.json`, `T-A2`, PASS), so the correction matches the
shipped bytes rather than only the prose.

## 5. Limits

* Whether `official_top_speed` is a cap or only a label is **UNKNOWN** (T-E5) — unchanged by this
  correction, and irrelevant to it: either way 336.4 is not a measurement.
* Nothing was installed or launched; the 267 km/h terminal is a drag balance on decoded values, not
  a take. Q-2 A2 is the first measurement that can test it.
* Option (b) — keeping 0.1213 as a second compromise row — was **not** taken. If the build ever
  needs the car to reach the label, it has to be a new, separately evidenced balance row, and the
  ledger would then say so in the T-E5 cell.

## 6. Revert

`git` history for this tree holds `Working/Translation/d10_spec.json` and `rc4_current.json` before
the change; if the prior drag is ever reinstated, restore those two files and rebuild
`Builds/bm-RC4-handling`:

```bash
python Tools/scripts/t1_apply.py --edits Working/Translation/t1_handling_edits.json \
    --current Working/Translation/rc4_current.json
python Tools/scripts/bm_build.py --tag bm-RC4-handling --base bm-RC4-base \
    --edits Working/Translation/d10_spec.json
python Tools/scripts/b10_handling.py --check
python Tools/scripts/bm_build.py --tag bm-RC4-handling --check
```

Prose revert: re-run `python Tools/scripts/v05_driving.py --write` after restoring the generator's
D-2 block, `python Tools/scripts/t23_closeout_inventory.py --write` after restoring its T-E5 comment,
and drop the MODLOG section plus this report.

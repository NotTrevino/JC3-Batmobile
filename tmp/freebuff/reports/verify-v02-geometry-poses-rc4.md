# V-02 — geometry and pose verdict on `Builds/bm-RC4`, combined for verify-v05

Date: 2026-11-07. Build: `Builds/bm-RC4`. This file adds no measurements. Every figure below is copied
verbatim from the two finished V-02 reports and carries the section it came from:

- **A** = `tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md`
- **B** = `tmp/freebuff/reports/verify-v02b-pose-renders-lights.md`

The machine-readable form of this verdict — the file verify-v05 reads — is
**`Builds/bm-RC4/verify/geometry.md`**, written in the same pass with the same figures.

## Gate lines, in the order the card fixes

**1. Silhouette against the 99.9 % limit — PASS.** Side **99.9004 %** (+0.0004 pp over the limit),
front **100.0691 %** (+0.1691 pp), top **99.9247 %** (+0.0247 pp), from **A §1**
(`python Tools/scripts/v02a_rc4.py --gate silhouette`). What moved it: **nothing** — RC2's side margin
is carried over unchanged (`side_px_delta = 0`), the body is byte-identical (`10cbbf40…`, 2,311,365 B),
and the source offset `[0.0, 0.022231, 0.154284]` m and the 215,893-face split are identical. Front and
top are new in A and have more room than the side.

**2. Parts census against 59 parts and 19 types — PASS.** **59 parts, 19 distinct damage types**, 59/59
part models resolve, indices 1 and 2 absent; from **A §2** (`--gate census`). It returned **59, not
61**, so there were no two extra parts to find; the 59-part table is the post-B-04 one, and 19 types is
RC2's 20 minus `Land_Door`.

**3. Interaction points, 5 cm outside the hull and within 30 cm — PASS.** **77/77** placed points in
band, distance range **0.0577–0.1461 m**, 0 placed inside the hull, worst excursion outside the
envelope **0.0000 m** against the 0.02 m allowance; from **A §3** (`--gate interaction`). 85 donor
objects = 77 placed + 6 dropped by D-9 + 1 socket + 1 UNKNOWN (the passenger seat, one-seat cockpit).

**4. Collision against the 5 cm placement gate — PASS for the shipped bytes.** Shape against BmAK
chassis box 0 **0.000000 m** (exact); placement **[0.0005, 0.0000, 0.0025] m = 0.25 cm**, under the
5 cm gate; **5 hulls written** (body 0 + wheels 11/12/26/27) over the donor's **62 bodies**; **0 of 54**
hull slots free; **2 of 3** BmAK boxes have no shape instance; the 1 constraint is a named omission.
From **A §4–§5** (`.ee` member `sportsmuscle.physicsc`, 340,368 B, sha
`fda78f4d8056a4ee47bd8316b6c738fac6f16d227e3bd4769853a43613b41095`).

The line is PASS only because report A *did* measure the placement within 5 cm (2.5 mm). The brief's
6.1 cm vector `[0.0005, 0.061, 0.0025]` belongs to payload `0164936b928f821c…9399323`, which is **not
in the RC4 tree**; on that payload the gate is **NOT MET** and A says so. If verify-v05's acceptance
basis is that payload rather than the one that ships, this line reads **FAIL** — it is not
reinterpreted as a pass.

**5. Pose renders at each moving part's two limits — PASS for 18, UNKNOWN for 6.** **18/18** renderable
rows rendered (9 parts x 2 limits), 21 PNGs in `Builds/bm-RC4/verify/v02b/` (18 poses + 3 rest views),
from **B §1** (`python Tools/scripts/v02b_pose_renders.py`, exit 0). Turret ±60.000° (1170 mm max
vertex travel), machine gun −179.493°/+177.861° (3617/3635 mm), riot suppressor −89.999°/−0.000°,
four air-brake flaps −48.9°…+7.5°, both missile pods +0.019°/+15.007°. **UNKNOWN: P-02 cannon pitch,
P-05 jet, P-06 canopy, P-07 and P-08 hatches, P-13 yoke** — the first two because the bones translate
(53.376 cm, 40.163 cm) and a hinge cannot reproduce translation, the rest because no joint or bone
exists in `T8_PARTS.json`. Rerun: `python Tools/scripts/v02b_pose_renders.py`. Two rows rendered but are
degenerate limits, quoted as such and not as travel: P-04 max at −0.000° (0 mm) and P-14/P-15 min at
+0.019° (1 mm).

**5b. Battle pose — not in this tree.** `battle pose: not in this tree`, from **B §1**. Never PASS:
`tmp/freebuff/reports/build-d12-variants-modes.md` line 126 records T-MD13 blocked by
`ConvertAdf --e sportsmuscle_vehicle_parts.vmodc` throwing `NullReferenceException` in
`InstanceMemberInfo.PrepareForWritting` → `InstanceInfo.GuessInlineArrayCopyPosition`, and `bm_build`
has no `.epe` applier, so the pose is declared and not written.

**6. Lights — PASS for the row count and the `CarLight` census, with the out-of-domain note
carried.** **24 rows**, **7,105 B**, sha
`01405084aefe1ddff24d9a66a4f2be30363dfec0849025d2418ffc559c583f4c`, from **B §2**
(`python Tools/scripts/v02b_lights_check.py`, exit 0). Each headlight carries **two 70° entries**, at
18 m and 60 m (`reaches [18.0, 18.0, 60.0, 60.0]`). **6 rows are out-of-domain: angle 70 and range 60
exceed the shipped maximum of 50 and 50** (`build-d03` U-1) — the four 70° headlight rows plus two 60°
`body` rows, recorded as **render risk**, not shipped behaviour. **24 `CarLight` blocks over 8 lamp
parts**, 3 per part (one per LOD), no lamp part missing a block.

## Status at a glance

| gate | figure | source | verdict |
|---|---|---|---|
| silhouette | side 99.9004 %, front 100.0691 %, top 99.9247 % | A §1 | PASS |
| parts census | 59 parts / 19 types / 59 models | A §2 | PASS |
| interaction | 77/77 in band, worst outside 0.0000 m | A §3 | PASS |
| collision | shape 0.000000 m, placement 0.25 cm on `fda78f4d…` | A §4–§5 | PASS (shipped bytes; FAIL on `0164936b…`) |
| pose renders | 18/18 renderable, 6 UNKNOWN | B §1 | PASS / UNKNOWN |
| battle pose | not in this tree | B §1, `build-d12` | UNKNOWN |
| lights | 24 rows, 70°/60 m out of domain, 24 blocks / 8 parts | B §2 | PASS + risk noted |

## What verify-v05 takes from `Builds/bm-RC4/verify/geometry.md`

verify-v05 must take the six gate figures and verdicts in that file as its predicted values — with
collision read as 0.25 cm on payload `fda78f4d…` and never as 6.1 cm, battle pose read as absent
rather than passed, and the lights 70° angle / 60 m range read as out-of-domain render risk — and
compare them against the shipped artifact without re-measuring any of them.

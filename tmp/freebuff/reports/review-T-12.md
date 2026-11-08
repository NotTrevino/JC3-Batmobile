# Independent review — T-12 · Moving-parts translation

Reviewer role: independent, read-only. Nothing under `Tools/`, `Research/`, `Working/`,
`GRAB_BACKLOG.md` or `MODLOG.md` was modified; the only file written is this report. Date 2026-10-29.

Read: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–79), §7 card T-12 (line 878–886), §12 row
`| T-12 | done |` (line 1321); `MODLOG.md` §"T-12 · Moving-parts translation — done" (12647–12732);
outputs `Working/Translation/T8_PARTS.md` (268 lines), `Working/Translation/T8_PARTS.json`
(schema 2), `Tools/scripts/t12_parts.py`; inputs `Research/BatmobileGrab/{ANIMATIONS,BONES,POSES,
MOVING_PARTS,TURRET}.json`, `Research/JC3Grab/PARTS_TABLE.jsonl`, `Working/Appearance/build_parts/
parts_manifest.json`, key frames `E:/Modding/ArkhamKnight/_grab/anims/keys/`, `Tools/scripts/bat_assemble.py`.

## VERDICT: needs rework (narrow)

The measurement work is real: 15 rows, every pivot re-derived through `bat_assemble.pivot_point`
(verified below), limits/rates measured from the exported key frames, damage types read from
`PARTS_TABLE.jsonl`, the shipped hinges read from `TURRET.json`, and `--check` is green. The rows
are a good basis for B-02/B-05.

It cannot be accepted as finished because:
1. **T-12 broke the consumer of its own output.** `T8_PARTS.json` is now `schema 2`;
   `bat_assemble.load_part_spec()` refuses anything but schema 1, so
   `bat_assemble.py --parts Working/Translation/T8_PARTS.json` **aborts** — while `T8_PARTS.md:267`
   and `MODLOG.md:12651` both say the file is still a valid spec.
2. **Two rows give a static reason the data contradicts.** P-02 and P-05 say "no sequence in the
   base package moves a bone of this part", yet the same JSON records 53.376 cm / 36.129 cm of
   cannon recoil and 40.163 cm of jet travel.
3. **The Vulcan's limits are a wrap artifact**, and the MODLOG/§12 call 357.4° "per spin" when the
   clip rotates 2160° (six turns).

The rest are label/clarity issues (issues 5–8). None of the 15 rows needs re-measuring; the fix pass
is a schema decision, a renderer line, and a handful of sentences.

## Check output (verbatim)

```
$ python Tools/scripts/t12_parts.py --check
PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge) | 25 BmAK sequences | fastest joint 1229.51 deg/s | pivots re-derived through bat_assemble (max delta 1.3918e-05 m) | damage types ['Boat_Generic', 'Land_Generic', 'Land_Hood', 'Plane_Control_Surface', 'Train_Generic'] | internal rows ['P-02', 'P-05', 'P-13'] | json match True, md match True
exit 0
```

The two standing gates the done section records:

```
$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
exit 0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit 0
```

And the compatibility check the doc claims, run against the delivered file:

```
$ python -c "import sys; sys.path.insert(0,'Tools/scripts'); import bat_assemble; bat_assemble.load_part_spec('Working/Translation/T8_PARTS.json')"
REFUSED: part spec Working/Translation/T8_PARTS.json: schema 2, expected 1
```

## Out paths and Done criterion

| card requirement | state |
|---|---|
| `Out:` `Working/Translation/T8_PARTS.md` + rows (doc `T-8`) | exists, 268 lines, 15 rows; the rows are `P-*` part rows, not `T-*` ledger values, and the done section says so |
| §12 row's `T8_PARTS.json` | exists, schema 2, `parts` 11 (unchanged), behaviour rows beside them |
| §12 row's `t12_parts.py --check` | exists, exit 0 |

| card `Done:` clause | verified by | result |
|---|---|---|
| each part has a pivot | `invariants()` `t12_parts.py:636-642` (exists + within BONES' offset delta) | met |
| … an axis | nothing asserts `joint.axis_index` / `axis_local` exist | **not verified** |
| … a limit | only `span_deg > 0` (`:643-644`); min/max sanity and the part-vs-child choice (issue 7) are not checked | partly |
| … a rate | `max_rate_deg_s > 0` (`:643-644`) | met |
| … a behaviour | `behaviour is None and joint and not moves_with` → fail (`:646-647`) | met |
| … or a reason it stays static | no per-row reason is stored or asserted; only `verify` non-empty (`:648-649`) | **not verified**, and false for P-02/P-05 (issue 2) |

## Issues

**1. The delivered JSON is no longer a `bat_assemble.py --parts` spec, and two files say it is
(`T8_PARTS.md:267`, `MODLOG.md:12650-12651`, `bat_assemble.py:60-65`, `T8_PARTS.json` `schema` 2).**
`load_part_spec()` is explicit: `if doc.get("schema") != 1: raise SystemExit(...)`. I called it on the
delivered file and it exits with "schema 2, expected 1", so the B-02 assembly step would abort if it
is re-run from this spec. The doc's closing line — "`T8_PARTS.json` stays a valid `bat_assemble.py
--parts` spec: `parts` is unchanged, the behaviour rows are added beside it" — is false, and so is
the MODLOG sentence "so `bat_assemble.py --parts` still reads it". The card did not ask for a schema
bump; the T-12 session's own intended-change table claims it kept the interface. Two ways out:
teach `load_part_spec` to accept 2 (schema 1 plus the new keys), or keep the behaviour rows in a
second file / leave `schema` at 1. Until one is done, R2's "import it, never fork it" is only half
honoured — T-12 imports `pivot_point` but has invalidated the sibling entry point.

**2. P-02 and P-05 say no sequence moves their bones; the same JSON records that it does
(`T8_PARTS.md:77`, `:114`; `t12_parts.py:576-579`, `:584-586`; `T8_PARTS.json` `translation`).**
P-02: `translation = {Barrrel_02: 53.376 cm in Batmobile_V2_Cannon_Fire, Barrel_01: 36.129 cm}`.
P-05: `{JetSMove: 40.163 cm in Batmobile_V2_Bat_Tracker}`. Both rows have `joint: null` (no *rotation*
is animated), so the renderer's else-branch prints "no sequence in the base package moves a bone of
this part" and never prints the translation line (that line is emitted only inside the
joint branch). Net effect: the doc drops data it has, and the card's "reason it stays static" is
false for these two rows — "stays static" is true only for rotation. The MODLOG's own row
(`MODLOG.md:12657-12658`) has the correct statement ("P-02 — no rotation animation exists, only
recoil"), so the doc's template is the defect.

**3. The Vulcan's "limits" are a wrap artifact, and "357.4° per spin" is not the motion
(`T8_PARTS.md:44`, `:88`, `MODLOG.md:12669`, `GRAB_BACKLOG.md:1321`; `t12_parts.py:149-167`).** I
recomputed the base-package track `Batmobile_Rig_Weapons_Machine_Gun_02` in
`Playable_Batmobile_SF__Batmobile_V2_Pose_States.json`: the X Euler channel runs 0 → 161.3 →
−179.1 → −157.6 … and returns to 0 at the end; the wrapped travel is **2160.0° over 3.900 s**, i.e.
six full revolutions, while min/max of the raw channel are −179.493 / 177.861 and the "span" is
357.354°. `euler_extents()` measures max−min of a ±180-wrapped channel, so for a continuous spin it
reports one wrap, not the travel, and the row presents that as the part's "BmAK limits". The rate
(1229.51 °/s) is correct as a peak and reproduces exactly. A builder reading
"−179.493…177.861°" could author a ±179 hinge for a barrel that must spin. The doc should either
report "six turns, 360°/rev, peak 1229.5°/s" or mark the range as "sampled channel extent, not a
limit"; the MODLOG/§12 "357.4° per spin" wording should be corrected either way.

**4. The Done clause's axis and static-reason halves are not checked
(`t12_parts.py:628-661`).** `--check` never looks at `axis_index`/`axis_local`/`axis_jc3`, never
checks that a static row carries a reason (there is no `static_reason` field; the reason exists only
as rendered prose), and only requires `span_deg > 0` for limits. The MODLOG's description of the gate
(`MODLOG.md:12690-12694`) is accurate as far as it goes but omits the axis and the static reason,
while the card's `Done:` names both. Combined with issue 2, two rows fail the only alternative the
Done allows.

**5. "25 BmAK sequences" is 25 row-sequence pairs, not 25 clips (`T8_PARTS.md:16`,
`MODLOG.md:12687`, check output).** `summary.sequences_scanned = sum(r["animation_sequence_count"])`
(`t12_parts.py:470`), and the same clip is counted once per row: `Batmobile_V2_Missles_Up` appears in
P-07, P-08, P-14 and P-15. The distinct set is **15** clips. The number is derived, but the label
overstates what was scanned.

**6. The behaviour table's `axis` column is bone-local while the neighbouring `carrier limits` column
is JC3-space (`T8_PARTS.md:40-56`; e.g. `:42` P-01, `:47` P-06).** P-01 reads `+Z` beside
"−179.0…179.0°", whose hinge axis is `+Y`; P-06 reads `+Y` beside a donor hinge of `+X` and the
detail says "agrees" (`_same_axis`, `t12_parts.py:190-199`, is collinear-only, so +X and −X count as
agreeing). Both are correct in their own space, but the table gives the reader no way to see that;
the detail lines ("local +Z ([−0.0, 1.0, −0.0] in JC3 space)") are the only place the JC3-space axis
appears. Given R2/R3, a column in JC3 space (or both) is the safer presentation.

**7. For six rows the headline joint is a child bone, so the table's limits/rate are not the part's
(`T8_PARTS.md:44,45,50-53`; `t12_parts.py` joint choice = largest span).** P-03's joint is the barrel
child (`is_pivot_bone: false`), P-04's is `Riot_Sup_Ammo`, and P-09…P-12's is the `Piston_Top`. The
flap part itself moves −0.003…20.007° at 37.20 °/s (P-09), while the row's headline says
−18.352…7.465° at 48.70 °/s — the piston's numbers. The doc does disclose it ("note the joint bone is
not the part pivot") and the §12 row distinguishes "20/30° blade + 54.8° piston", but a builder
reading only the table would drive the part from the wrong bone. The card asked for "the part's"
axis/limits; a `part bone` column, or the part bone's numbers in the headline, would close this.

**8. Journal nits (R14).** `MODLOG.md:12649` says the doc is "262 lines"; it is 268 (`wc -l`), and the
file has not changed since the session (mtime 05:52, same as the script). `MODLOG.md:12679` lists the
yoke's damage types as "`Land_Selector`/`Land_Generic`"; `PARTS_TABLE.jsonl` has no `Land_Selector` —
the behaviour's fleet values are `Boat_Steering_Wheel`, `Land_Generic`, `Land_Steering_Wheel`, which
is what the doc prints. Neither affects a row.

**Read positively (not issues):** the canopy's 72.481 cm / 12.494° and the "0.71 m / 11.2°" quoted in
P-06's verify and §UNKNOWN 3 are two different statistics of the same five clips — the per-sequence
spans are 11.23°, 11.23°, 12.49°, 12.44° and the row takes the union. They are not contradictory, but
the doc never says which clip/statistic each is, so a reader cannot reconcile them; worth one phrase.

## Spot-checks (value → where verified)

| value in `T8_PARTS.md` | verified at |
|---|---|
| P-01 pivot `0.000, 0.876, 0.333` and "max pivot disagreement 0.000013918 m" | independent `bat_assemble.pivot_point(bind.world_position_cm, scale 0.01, offset)` on `BONES.json`'s `Batmobile_Rig_Weapons_Turret_Root` → `(1.3e-05, 0.876249, 0.333226)`, delta 1.3678e-05 m; tolerance `pivot_tolerance_m` 1.4462e-05 = BONES `offset_delta_m` 1.3462e-05 + 1e-6 ✓ |
| P-03 "1229.51 °/s", "−179.493…177.861°" | recomputed from `E:/Modding/ArkhamKnight/_grab/anims/keys/Playable_Batmobile_SF__Batmobile_V2_Pose_States.json` → `Batmobile_V2_ChainGun_Spin`: min −179.493, max 177.861, peak rate 1229.51 °/s — exact; total travel 2160.0° (issue 3) |
| damage types per row (`Land_Generic`, `Land_Hood`, `Train_Generic`, `Plane_Control_Surface`, `Boat_Generic`) | `part_table_dt()` over `Research/JC3Grab/PARTS_TABLE.jsonl`: Turret `Land_Generic`, Cannon `Land_Generic`, GatlingGun `Boat_Generic` (no land carrier), Hood `Land_Hood`, MissileHatch `Train_Generic`, AirBrake `Plane_Control_Surface`, SteeringWheel `Land_Generic` (fleet `Boat_Steering_Wheel`, `Land_Generic`, `Land_Steering_Wheel`) — all match, including "no land vehicle carries GatlingGun" |
| shipped hinges P-01/P-02/P-04/P-06 (`mediumtank_turret` +Y ±179 pivot 0,2.2812,1.1382; `mediumtank_cannon` +X −5…20 pivot 0,2.5347,0; `sportsmuscle_hood_signature` +X 0…70 pivot 0,1.0572,−0.8478) | `Research/JC3Grab/TURRET.json` `samples` — the four rows are byte-equal to the doc's quotes, damage types included |
| P-09's part bone moves 20.007° at 37.20 °/s while the row's headline is 25.817° at 48.70 °/s | `T8_PARTS.json` P-09 `joint.candidates` / "other bones" line, recomputed from the same key file (issue 7) |

## Limits of this review

- Read-only: no card file, script, ledger, research file or game file was modified; no game launched;
  nothing committed. The three tamper tests in the MODLOG were not re-run by editing files (that needs
  write access), but `cmd_check()` compares the rebuilt doc and JSON byte-for-byte against the disk
  copies, so those failure modes are structural.
- I re-derived the Vulcan track and the turret pivot independently and spot-checked the damage/hinge
  tables; I did not recompute all 25 row-sequence extents.
- Key frames live outside the repo (`E:/Modding/ArkhamKnight/_grab/anims/keys`, R10); reading them is what the
  script does and no file was written there.

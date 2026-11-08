STATUS: done. The five effect rows that were `out` on a keyword search are now ledgers with a
carrier or an authoring plan: **T-FX9** heat haze -> `effects/jc_vehicles/exhaust/car_speedrom_heater.effc`
at the `Afterburner` socket; **T-FX12** tracers -> the cloned `WeaponTuning` (8 members) plus a
private copy of `effects/jc_weapons/missile/missile_trail_car.effc`; **T-FX13** casings -> the shipped
`SAttachedEffect ShellEjection` (Effect 600259254, Usage 4131019937 = `Fire`) over
`effects/jc_weapons/minigun/bullet_eject_minigun.effc`; **T-FX16** round trail -> the same private copy
as T-FX12, sprite emitter; **T-FX20** brake trail -> an authoring plan (private copy of
`car_cycle_base_dual_nitrous.effc` on the `t_velocity_streak_alpha_dif.dds.1_1b.trim` strip, plus an
authored brake trigger). Every plan names the members a private copy changes and whether the file
grows. `Working/Translation/T13_FX.md` is **17 rows, 17 chosen carriers, 0 named omissions**, and
`t_rows.py check`, `t17_fx.py check` and all nine standing gates pass. One new card, **B-17 · Effect
writer (private `.effc` copies)**, is in `GRAB_BACKLOG.md` §8 with its §12 tracker row. Nothing was
installed, launched or written into a game folder; no archive was written.

## What the five rows now say (and where the evidence is)

| row | carrier chosen | authoring plan: copy / members / growth | evidence |
|---|---|---|---|
| **T-FX9** heat haze | `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` (12 vehicles, 14,703 B, 5 emitters, blocks `3012430835`×8 + `2199516487`×2), attached at `Afterburner` | attach first (no byte change); a private copy only to tune `Instantiators[i].RenderBlockData[0]` of the 4 sprite instantiators (`3125323646, 436538540, 869501834, 124404425`), the `RenderBlockData[]` floats and `EmitterTemplates[i].MaxParticles` (10/60/3/7/100). **In place.** | `fx9-heat-haze-source.md` §4/§5/§8; `Research/JC3Grab/FX9_HAZE.json` |
| **T-FX12** tracers | linear half is the clone's tune; art half `effects/jc_weapons/missile/missile_trail_car.effc` (11,199 B, 1,412 rows, 179 arrays) | tune in place: `tracer_fire_width` 0.5 @0x188 (already the 50 uu ribbon), `tracer_time_to_live` 0.0 @0x190 -> 1.25 s, `tracer_fire_length` 30 @0x184, `tracer_fire_velocity` 900 @0x180, `smoke_trail_tile_size` 5.0, `tracer_per_smoke_trail` 1, `tracer_texture_type` 1; effect: +1 ribbon (0.50 m / 1.25 s / 8 per s) and +1 sprite (0.035-0.05 s / 1 per s / -0.50 m). **Growth.** | `fx12-16-tracer-and-trail.md` §3/§4/§7/§8/§9/§10 |
| **T-FX13** casings | `SAttachedEffect ShellEjection` (Effect 600259254 = `hash_jenkins(effects/jc_weapons/minigun/bullet_eject_minigun.effc)`, Usage 4131019937, `name_hash` 3811014039, no `world`) under the mounted-MG entity, + `bullet_eject_minigun.effc` (6,703 B, cap 30, gravity `Params[12]` -9.82) | `.effc` in place: `MaxParticles`, `Params[12]`, `Params[9]/[10]` cone angles; `.epe`: one added `SAttachedEffect` object. **No `.effc` growth.** | `fx13-shell-casings.md` §3/§4/§7 (14 graphs / 5 dirs decoded; 21 vehicle containers carry the capstone variant) |
| **T-FX16** cannon round trail | the same private copy as T-FX12 (`missile_trail_car.effc`) | sprite emitter gives the round its trail (0.035-0.05 s, 1 per s, -0.50 m); the ribbon is the shared streak; the round's tune carries `tracer_time_to_live` 0.0 -> 1.25 s. **Growth.** | `fx12-16-tracer-and-trail.md` §7/§8/§10; `FX16_TERM.md` (the old `0 of 955` named no term = UNKNOWN, not a negative) |
| **T-FX20** brake trail | no brake-named effect exists; the look is an authored `.effc` built on `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` (donor boost glow, 20,671 B in its `.ee`) | `RenderBlockData[]` floats (one slot per probe), `MaxParticles`, `StartTime`/`EmitterLifetimeIndex`; the trim binding is not a member (`TrimIndex` is the corpus-wide 14). **In place for the restyle; the trigger is authored** (no `Brake` behaviour). | `fx20-brake-trail.md` §3/§4/§6/§8; `LIGHT_SYSTEM.md` §1 |

`T13_FX.md` §4 keeps, for each row, what it used to say and why the keyword test could not see the
carrier (a `.effc` stores no strings: 0 in 955/955; T-FX13's paths are `bullet_eject_*`; T-FX16 named
no search term at all). §5 is the authoring-plan section, one block per row.

## Files changed

| file | change | revert |
|---|---|---|
| `Tools/scripts/t17_fx.py` | the 5 `RULES` blocks (carrier + `authoring` plan), `FORMER` table, `authoring` carried into the record, doc §4 rewritten and §5 added | restore the 5 rule blocks, drop `FORMER`, restore the old §4 block |
| `Tools/scripts/t_rows.py` | 5 `DISPO` entries `out` -> `next` with the carrier/plan reason | restore the 5 strings |
| `Tools/scripts/audit_compromises_t.py` | 2 `EXCLUDED` reasons (T-FX9, T-FX20 said "absent on both sides") | restore the 2 strings |
| `GRAB_BACKLOG.md` | T-17 Do text; new card **B-17** in §8; tracker rows T-17, T-FX12-16, **B-17** | delete B-17 and its tracker row, restore the three texts |
| `Working/Translation/T13_FX.md`, `t17_fx.json`, `T_ROWS.jsonl` | regenerated (pinned) | `t17_fx.py --write`, `t_rows.py build` after reverting the tools |
| `STATUS.md` | regenerated (5 rows left `out`) | `status_audit.py --write` |
| `Working/Translation/COMPROMISES_T.{json,md}` | regenerated after the two `EXCLUDED` reasons changed | `audit_compromises_t.py --write` |

`MODLOG.md` was **not** touched: the session rules (`tmp/freebuff/rules.txt`) forbid editing it, so this
report is the journal entry. No other task's file was edited.

## Commands and output, verbatim

```text
$ python Tools/scripts/t17_fx.py --write
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\t17_fx.json: 17 rows (17 chosen, 0 named omissions), FX codes 4/4
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\T13_FX.md: 189 lines

$ python Tools/scripts/t_rows.py build
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows

$ python Tools/scripts/status_audit.py --write
UnicodeEncodeError: 'charmap' codec can't encode character '\u2192' in position 3630   # cp1252 console, after the file was written
$ PYTHONIOENCODING=utf-8 python Tools/scripts/status_audit.py --write
status_write=0
```

The first `status_audit.py --write` wrote `STATUS.md` and then failed printing a `->` to the cp1252
console; the re-run under `PYTHONIOENCODING=utf-8` exits 0. That is a console-encoding defect in the
tool, not a stale file (the `--check` below passes).

```text
$ python Tools/scripts/t17_fx.py --check
PASS: 17 rows (17 chosen, 0 named omissions) | FX codes 4/4 | donor effects 85 | fleet .effc 955 | sockets 8 | ledger 17/17

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 58 keep 60 epe 26 re-read 0 blocked 9 out 22 superseded 7 | edits 35 over 16 rows
check ok

$ python Tools/scripts/audit_compromises_t.py --check          # first run, before --write
72 audited: 1 approved, 71 unapproved; ...
FAIL: json drifted
FAIL: markdown drifted
$ python Tools/scripts/audit_compromises_t.py --write && python Tools/scripts/audit_compromises_t.py --check
OK: every approval quote re-read at its cited line; document re-derived identically
```

Standing gates (§0.7), each run after the last edit:

```text
$ python Tools/scripts/grab_model.py check
OK: grab output matches schema 6 and its own summary.                        g1_inventory=0
$ python Tools/scripts/bmak_chain.py --check
PASS: chain record current (105 objects, 9225 named bindings, 336 cross-checked, 0 conflicts, 0 bool words left unnamed)
                                                                            bmak_chain=0
$ python Tools/scripts/bmak_coverage.py --check
  weapons      62 rows -> 10 T rows, 0 unassigned
check ok                                                                    bmak_coverage=0
$ python Tools/scripts/jc3index.py check
check ok: 81952 rows, 78907 paths, 1 unnamed entries, DLC 20682/20682 named, sources
{'gibbed-filelist': 55811, 'jcmr-dictionary': 26051, 'derived-names': 90}   jc3index=0
$ python Tools/scripts/jc3hkx.py check --all
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 |
geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions
exact) | station sets 17 (land_global agree 17, disagree 0)
check ok                                                                    jc3hkx=0
$ python Tools/scripts/jc3fx.py check
checked 57187 files | problems 0                                            jc3fx=0
$ python Tools/scripts/t3_fleet.py --check
E:\Modding\JustCause3\JC3-Batmobile\Working\Translation\T3_FLEET.md: 41 members over 156 vehicles
check ok                                                                    t3_fleet=0
$ python Tools/scripts/status_audit.py --check
STATUS.md is current                                                        status_check=0
$ python Tools/scripts/t_rows.py check
check ok                                                                    t_rows_check=0
```

The three archive-scanning gates (`jc3index`, `jc3hkx`, `jc3fx`) were run as background jobs and
polled to their `=0` status lines: running all three in one shell window exceeded a 600 s call, not
their own budgets.

## The B-17 card

Added to `GRAB_BACKLOG.md` §8 after B-14 and tracked in §12:

> **B-17 · Effect writer (private `.effc` copies)** S · deps: B-05, T-17 · serves: FX-1…4 —
> copy the T-17 carriers to private paths; patch at decoded offsets
> (`MaxParticles`, `RenderBlockData[]` one slot per probe, `Params[]`, `StartTime`);
> T-FX13's attachment is the `SAttachedEffect ShellEjection` object `bm_fx.py` already places;
> growth (the two-emitter T-FX12/T-FX16 copy) last. Done: `effc_writer.py check` passes and every
> built effect re-reads through the built `.toc` with each patched member equal to its row's number.

The card is written because `effc-format-writable.md` proves the writer: `effc_writer.py check`
PASS, 95/95 sampled effects re-encoded byte-identically (91.49% of their bytes from decoded fields,
0 unexplained bytes), and one edited copy (`EmitterTemplates[0].MaxParticles` 60 -> 317) re-reads
with exactly 2 bytes changed and reverts to the shipped bytes.

## Downstream consumer check (one FAIL, pre-existing and unrelated)

`Tools/scripts/bm_fx.py` (B-08) reads `t17_fx.json`, so I re-ran its `--check` after the change:

```text
$ python Tools/scripts/bm_fx.py --check
FAIL: the built .epe differs from the re-derived plan: 6 object(s) missing, 6 unexpected, e.g.
missing [("SWeaponPoint", "attach.vehicle", ... no 'id:A90F5E74') ...] /
unexpected [... ('id:A90F5E74', 'weapon_anchor') ...]
CHECK_EXIT=1 (1 failure(s))
```

It is the **B-16** base drift, not this brief: `Builds/bm-008` was built on the pre-rework `bm-005`,
whose `.epe` still carries the four `id:A90F5E74` = `weapon_anchor` refs that the reworked B-05
removed (tracker row B-16: "RC merge per-branch base fix (bm-007/008 on the pre-rework bm-005)").
No failure mentions a T-17 row: the criterion my change could move - every chosen path resolving in
the fleet `.effc` vocabulary - is silent, so all 17 chosen paths (including the five new ones)
resolve. Rebuilding `bm-008` is not this brief's work and would edit an existing `Builds/bm-*` tree.

## UNKNOWNs

1. **Growth acceptance.** Adding emitters (T-FX12/T-FX16) re-lays out the `A[..]` (offset, count)
   pairs and `total_size`. The format expresses it, but no re-laid-out file was built or re-read,
   and engine acceptance is untestable under the test ban. It is B-17's last step.
2. **`RenderBlockData[]` slot semantics** (T-FX9, T-FX20). The floats are writable; which slot is
   size, rate, scroll or texture is named by no member. One slot per probe.
3. **Blend mode and per-emitter texture.** No `.effc` carries a string (0 in 955/955); only 8
   `RenderBlockTypeHash` values exist game-wide and the single-use `2813794826` is the only unnamed
   lead. Whether `car_speedrom_heater` actually refracts is UNKNOWN.
4. **The casing cone's local axis** (T-FX13). The attachment has no `world` and the effect stores no
   named axis; Q-3 #4 is the probe.
5. **BmAK brake-trail numbers** (T-FX20). `BrakeTrail0/1` serialise no `ParticleSystem` template, so
   width/length/colour are not in the grabbed packages; the float at @364 has no SDK name.
6. **Tracer colour and material identity** (T-FX12). Colour is not a `WeaponTuning` member and
   `tracer_texture_type` = 1 is an enum whose `.ddsc` is unnamed.
7. **No in-game observation.** Every `verify` cell is a Q probe; none ran (test ban).

## COMPROMISES

None. No lore value was dropped or substituted: each row carries either a shipped carrier or an
authoring plan that reproduces the BmAK emitter set, and each remaining part is a named gap with an
owner (B-17) rather than an accepted JC3 limitation.

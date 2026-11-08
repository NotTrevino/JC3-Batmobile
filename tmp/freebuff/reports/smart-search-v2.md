# smart_search v2 — filters

**STATUS: done, with one honest adverse result.** The search now refuses every hit that made v1's
22 false positives, and the judge's prompt states the five "never a default" cases. On the same rows
440 candidates (today's plan, unfiltered) → **1**; the judge was shown that one and said false. The
calibration is complete for the first time (38/38) and its recall fell **0.700 → 0.000** — because
v1's recall was being produced by the calibration's own answer file inside the scan root. Evidence
in §5; the number is reported, not hidden, and the next real step is named in §7.

Files changed: `Tools/scripts/chase/chase_candidates.py`, `chase_judge.py`, `chase_calibrate.py`.
MODLOG: `## smart_search v2 — filters — done (2026-10-29)`.

## 1. What the search now refuses, and where

**Text route** (`chase_candidates.text_files`, `json_shaped`, `text_candidates`)

- Corpus is **game-derived text only**, 298 → **132 files**: the install's `BmGame/Config/**`
  (recursive, so `Config/PC/PCGame.ini` and friends are now in — they were not before),
  `BmGame/Localization/**`, `Binaries/Win64`, and the non-chase `.txt`/`.config` dumps under
  `E:\Modding\_BmAKgrab`.
- Excluded by rule: every `.json`/`.jsonl`/`.md`/`.csv`/`.log` (all project-written records) and
  every path under `_BmAKgrab/chase` (candidates, verdicts, cache, calib runs, selftest). Ten of the
  22 old false positives lived there.
- A JSON-shaped hit line (`{`, `[`, `"name": value`) is dropped as bookkeeping, so no count
  (`"BattleModeHeight": 1`) or offset map (`"AirControlYawTorqueFactorMin": 1200` with
  `1200 = 0x4b0`) can reach the model even if such a file reappears in the corpus.
- A hit must be `<member>=` on its own line, optionally prefixed `+. - !` (UE3 config syntax). v1's
  22 `StrafeRight` candidates were `Bindings=(Name="StrafeRight",...)` — an input binding, not a
  default.

**Exe route** (`chase_candidates.store_verdict`, `traced_literal`), applied per store site:

| rule | what it rejects |
|---|---|
| `stack-base-rsp` / `stack-base-rbp` | `[rsp+disp]`, `[rbp+disp]` — a frame local, never `this` |
| `stack-frame-reg` | base register loaded from rsp/rbp (`lea rbx,[rsp+0x…]`, `mov rbx,rbp`) |
| `read-modify-write` | the window reads the same displacement before the store (`+=`, `-=`, delta, field copy) |
| `computed-value` | the stored register was produced by arithmetic (`addss`/`subss`/`mulss`/`divss`/`cvtsi2ss`/`cvtdq2ps`…) |
| `no-literal-in-window` | the source is memory or untraceable — no constant visible in the snippet |
| `immediate-is-offset` | the literal equals the field offset or is within `0x40` of it (1200 = 0x4b0) |
| `window-misses-store` | the VA is in a section but is not an instruction start |

`traced_literal` follows the source register back through `movss xmm,xmm` chains, accepts an
immediate, a `pxor`/`xorps` zero, or a float from a RIP-relative constant (the same constant the
snippet annotates inline), and gives up as `computed` / `memory` / `opaque` otherwise. A site is
kept only when a literal is visible next to the store — the judge no longer has to guess which
number in the window was the value.

**Judge** (`chase_judge.PROMPT`): a value equal to the offset, a count, a value from a register or
memory, a stack-frame store, a per-frame update, and a JSON/analysis record are each stated to be
*never* a default; `found=true` requires the literal on the store's own line or its loader (the
`; [0x…] = float X` annotation counts). `PROMPT_VERSION` moved **aabe0532 → 51c8dd3c**, so the
verdict cache could not hand a v1 answer to a v2 question.

## 2. Filters, with counts dropped

43 rows chased, 37 with an offset; 181 raw exe hits and 22 raw text hits.

| rule | dropped |
|---|---:|
| `stack-base-rbp` | 63 |
| `read-modify-write` | 60 |
| `no-literal-in-window` | 23 |
| `text-not-an-assignment` | 22 |
| `computed-value` | 19 |
| `stack-frame-reg` | 7 |
| `stack-base-rsp` | 4 |
| `window-misses-store` | 4 |
| **total** | **202** |

`candidates.jsonl`: **440 → 1** on today's plan (the stored v1 file was 235 over 30 rows — stale, the
plan has since grown to 43 chased / 25 excluded / 1 no-member). The survivor is
`F-62 AirControlTurnTorque 0x17c`, `exe 0x141218c03` — a `pxor`-zeroed store inside a run of
consecutive field inits (`[rcx+0x160 … 0x194]`), which is exactly the shape the search *should*
surface. Judged **false** (`verdicts_v2.jsonl`: 1 judged, 0 found, 0 unparsable); the reason given
("loads from r12d") is weak, the site is worth a human look — no provenance is claimed for it.

## 3. The old 22, one by one

Each row is the old `found=true` source re-run through the v2 stage that now sees it.

| old hit | member @ offset | old source | v2 outcome |
|---|---|---|---|
| F-18#0014 | StrafeForce 0x11f8 | `_BmAKgrab/chase/selftest.jsonl:1` | filtered — our own fixture, `chase/` not in corpus |
| F-23#0004 | TransformationAnimNode 0x1494 | `chase/sim_cdo_07.json:494` | filtered — our own offset map |
| F-33#0002 | BattleModeHeight 0x199c | `chase/namescan_b.json:26` | filtered — our own package count |
| F-38#0002 | BattleModeSpeedDelta 0x1eb4 | `chase/namescan_b.json:28` | filtered — our own package count |
| F-57#0008 | AirControlYawTorqueFactorMin 0x4b0 | `chase/value_cdo_08.json:632` | filtered — our own offset map (1200 = 0x4b0) |
| F-60#0006 | AirControlTimeInAir 0x4bc | `chase/value_cdo_08.json:631` | filtered — our own offset map (1212 = 0x4bc) |
| F-61#0004 | BattleModeSlopeFactor 0x4c0 | `chase/value_cdo_08.json:633` | filtered — our own offset map (1216 = 0x4c0) |
| F-62#0035 | AirControlTurnTorque 0x17c | `chase/value_cdo_08.json:636` | filtered — our own offset map (380 = 0x17c) |
| F-63#0002 | StayUprightRollResistAngle 0x6d4 | `chase/value_cdo_08.json:640` | filtered — our own offset map (1748 = 0x6d4) |
| F-64#0002 | StayUprightPitchResistAngle 0x6d8 | `chase/value_cdo_08.json:639` | filtered — our own offset map (1752 = 0x6d8) |
| F-39#0002 | TurnOnSpotSteeringSpeedCurve 0x268 | `exe 0x140034dc3` | filtered — `read-modify-write` (`+= 100`, heading wrapped at ±180) |
| F-39#0003 | " | `exe 0x14014698f` | filtered — `stack-base-rbp` |
| F-39#0012 | " | `exe 0x140788c7c` | filtered — `stack-base-rbp` |
| F-39#0016 | " | `exe 0x140dfbadb` | filtered — `computed-value` |
| F-40#0018 | BattleModeMoving 0x294 | `exe 0x1417492e9` | filtered — `stack-base-rbp` |
| F-44#0004 | BattleModeFrontThrottle 0x2e4 | `exe 0x14016b9e0` | filtered — `stack-base-rbp` (the local `Vector3`) |
| F-44#0008 | " | `exe 0x14024f094` | filtered — `no-literal-in-window` (field copy) |
| F-45#0007 | BattleModeRearThrottle 0x2e8 | `exe 0x14016b9e8` | filtered — `stack-base-rbp` |
| F-62#0007 | AirControlTurnTorque 0x17c | `exe 0x140775b71` | filtered — `stack-base-rbp` |
| F-62#0009 | " | `exe 0x14077ce98` | filtered — `stack-base-rbp` |
| F-62#0014 | " | `exe 0x140815ba2` | filtered — `computed-value` (×0.001953125 on a live value) |
| F-62#0032 | " | `exe 0x1416faefa` | filtered — `window-misses-store` (mid-instruction VA) |

**22/22 filtered or judged false: 22 filtered, 0 needed a verdict.** The split by rule
(`stack-base-rbp` 6, text corpus 10, `computed-value` 3, `read-modify-write` 1,
`no-literal-in-window` 1, `window-misses-store` 1) matches the failure family chase-verify assigned
to each hit, which is the check that the filters encode the finding rather than a coincidence.

## 4. Precision / recall, v1 vs v2

| | v1 (`aabe0532`) | v2 (`51c8dd3c`) |
|---|---|---|
| calibration cases run | 10/38 | **38/38** |
| reachable (known value in some candidate) | 6/10 | **0/28** |
| recall | 0.700 (0.500 on reachable) | **0.000** |
| precision | 0.778 (14/18 found values) | **no claims** (0 `found=true`, so 0 false positives) |
| unparsable | 0.010 | 0.000 |
| s/candidate | 10.10 | n/a (nothing to judge) |
| row run: candidates | 235 (30 rows) | 1 (43 rows) |
| row run: found=true | 22 | 0 |
| row run: confirmed | 0 (0 %) | 0 claims |

v2 "precision 0.000" in the tool's one-line summary is `0 right / 0 found`; it means **no claims**,
not 100 % wrong. The meaningful pair is: v1 made 22 claims and every one was false; v2 makes none.

## 5. Why recall fell, and why that is the honest number

**v1's recall was the answer key.** Every one of v1's 14 correct values came from `calib.jsonl` —
the case file itself, which is inside v1's scan root and carries every case's member name *and* its
`known` value:

```
$ sed -n '4p' E:/Modding/_BmAKgrab/chase/calib.jsonl
{"family": "a", "id": "P04", "kind": "positive", "known": "600", "member": "TurningModeMaxSpeed", ...}
```

and v1's P04 verdict was `E:/Modding/_BmAKgrab/chase/calib.jsonl:4 -> 600`. The same holds for
P05:5, P06:6, P07:7, P08:8, P09:9, P10:10 — each "found" hit cites the line of the case that asks
the question. So v1's recall measured "the corpus contains the answer". Its four wrong values were
exe hits, i.e. the nearest float in the window: `0.5` for a known `0.8` (P01), `0.0` for `2` (P03),
and `50.0` / `-1.0` for `0.333333` (P07) — the same behaviour that produced the 22.

**What the exe actually has at those offsets.** Re-derived per site for the v2 corpus:

| case | offset | exe hits | filters |
|---|---:|---:|---|
| P01 TurnOnSpotFrontTorqueFactor | 0x1c8 | 37 | 31 `stack-base-rbp`, 5 RMW, 1 no-literal |
| P03 TurnOnSpotModeEngineBrakingFactor | 0x1d0 | 40 | 25 rbp, 8 RMW, 5 no-literal, 1 computed, 1 window-miss |
| P04 TurningModeMaxSpeed | 0x2c4 | 16 | 10 rbp, 4 RMW, 1 computed, 1 rsp |
| P07 BattleModeTurnOnSpotTorqueFactor | 0x2e0 | 22 | 7 rbp, 6 RMW, 5 no-literal, 2 computed, 1 rsp, 1 window-miss |
| P08 BattleModeThrottleSpeed | 0x2ec | 16 | 9 RMW, 6 rbp, 1 rsp |
| P10 BattleModeStopAndTurnAngleStationary | 0x2f8 | 18 | 10 rbp, 3 RMW, 2 computed, 2 no-literal, 1 window-miss |
| F11 BattleModeCamFOV | 0x4fd0 | **0** | — |
| F31 BattleModeWidth | 0x1994 | **0** | — |

Every one of the 20 family-(a) positives is a value decoded from the **packages** by the G1 readers
(`MODES.json`: serialised, identical on all four). A serialised property default is data, not code:
it need not appear in `BatmanAK.exe` at all, and at these offsets it does not. `reach 0/28` says the
failure is a **search** miss, not a judge miss — the calibration harness's own distinction, now
reporting the truth. Recovering recall needs a package route (below), not a weaker filter; loosening
a filter to raise this number would re-create the 22.

## 6. Checks (verbatim)

```
$ python Tools/scripts/chase/chase_candidates.py --check
rows chased 43 | excluded 25 | no member 1 | candidates 1 | text files 132 | exe 55101440 B
...
| filter | dropped |
|---|---:|
| computed-value | 19 |
| no-literal-in-window | 23 |
| read-modify-write | 60 |
| stack-base-rbp | 63 |
| stack-base-rsp | 4 |
| stack-frame-reg | 7 |
| text-not-an-assignment | 22 |
| window-misses-store | 4 |
| **total** | **202** |
check ok: 1 candidates, 1 unique ids, 4783 B, byte-identical
exit=0
```

```
$ python Tools/scripts/chase/chase_calibrate.py --check
check ok: 1 prompt run(s); latest 51c8dd3c recall 0.000 precision 0.000 unparsable 0.000 0.00 s/candidate; 38 cases, provenance re-verified, report block matches
exit=0
```

Both re-run after the last edit. `chase_calibrate.py --check` was red before this work for three
reasons, all fixed: `N01`'s provenance was mis-parsed (a FOOTAGE row whose parenthetical names
`MODES.json` was read as a MODES field), the report had no generated block, and 28 cases had no run.
Two further check fixes: only the **latest** prompt directory must be complete (an old directory is
history), and only 8-hex prompt directories are scored — a concurrent hand-made
`calib_runs/51c8dd3c_v1search` (2 files, 38 `rc=2` lines, no run JSON) appeared in the tree during
this session and made the check red; it is not a prompt version and is now ignored.

## 7. Limits and the next step

- The exe route now answers only "is there a literal store at this displacement" — for these
  classes the answer is no, so **the tool currently finds nothing on the chase ledger**. It is a
  precision-first search with an honest floor of zero, not a working oracle.
- `immediate-is-offset` uses ±0x40; a genuine default that happens to equal a nearby offset would be
  dropped (none of the 22 differed from the offset, so this is a hypothesis, not a measured loss).
- `stack-base-rbp` assumes rbp is a frame pointer, which holds for every rbp site the verify audit
  opened (7/7) and for all 63 dropped here by construction of the pattern; a build that keeps `this`
  in rbp would lose recall to this rule.
- The next recall step is a **package route**: decode the game's own `.upk` property values (what
  `MODES.json` already summarises) into candidate snippets, then judge them with this prompt. That
  is where 20 of the 28 calibration positives actually live. Until it exists, the calibration's
  `reach 0/28` is the correct score and the report's table says so.

## 8. Safety

`BatmanAK.exe` and the game text were opened `rb` only; nothing written under `E:\Games` or
`D:\Games`; no game launched or patched; the llama-server was neither started nor stopped
(`/health` answered `{"status":"ok"}` before the first call and stayed up); `FOOTAGE.md`,
`Research/BatmobileGrab/chase/**`, `GRAB_BACKLOG.md` and `chase09_native.py` untouched (MODLOG
appended only); no commit, no push, no secret read.

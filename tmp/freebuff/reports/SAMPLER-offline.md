# SAMPLER-offline - can the existing sampler logs resolve G3-02f's three action UNKNOWNs?

STATUS: **done** - and the answer is **no: all three stay UNKNOWN**, for reasons that are counted, not
asserted. `Tools/scripts/sampler_unknowns.py` (--write/--check) reads only the seven
`Research/BatmobileGrab/runtime/samples-*.jsonl` logs and `Research/BatmobileGrab/SAMPLER_FIELDS2.md`,
recomputes every number, and `--check` exits 0 on a byte-identical rebuild. No game was run, attached to,
injected into or read; nothing under `E:/Games`, `D:/Games` or `E:/Modding/_gamedata` was touched.

The brief's central premise is **wrong in a way that decides the task**: the logs do not carry the user's
presses for X, Y or A. They carry exactly **five** input bytes (LT, B, LB, RT, THR). So the exact counts
asked for are **0 presses of X and 0 presses of Y** - and **0 of A** - not "too few to analyse" but zero,
because `bVehicleBoostButton` (+781) and the X byte were never read (the X byte does not exist in the
layout at all) and `bBatmobileEjectModifier` (+786) was never read either.

Second finding, which is why no field is promoted even where presses exist: the rate test the brief
specifies has **no discriminating power on this corpus**. Run on a binding that is known (LT -> battle
mode, D-11 CONFIRMED live), it promotes **0 of 5** fields, and a 2.0 s sensitivity window does not rescue
it (49/175 presses vs 294/402 press-free instants). A test that cannot find a real link cannot find an
unknown one, so "no candidate" here is honest rather than evidence of absence.

## What the three UNKNOWNs resolve to (each value labelled)

| # | G3-02f UNKNOWN | sampled field that changes when the action occurs | rate_in vs rate_out | presses | verdict |
|---|---|---|---|---|---|
| 1 | X (missile barrage) input byte | **none identifiable** - 0 X presses, and no missile-launcher field is sampled | not computable | 0 | **UNKNOWN** |
| 2 | A (eject) input byte | LB (exit/enter) moves `veh1.Driver`, `veh1.BatmanVsBatmobileCollisionMode`, `veh1.bits11D8` on 1-2 of 4 presses | 0.716 s^-1 vs 0.039 / 0.028 / 0.551 s^-1 | 0 (A) / 4 (LB) | **UNKNOWN** |
| 3 | boost duration / boost time field | **none** - `bBoosting`/`bWarming`/`BoostingOut`/`LastBoostPickupTime` never sampled; the two boost bits in the sampled word never set | 0.000 vs 0.000 | 0 | **UNKNOWN** |

Labels: the 44 observables and every offset are `decoded` (BmSDK `.g.cs` file:line, re-parsed from
`SAMPLER_FIELDS2.md` §1-§4); the log-key offsets and bit names are `decoded` (the sampler's own
`PI`/`VEH`/`GADGETS`/`BITS_11D8` tables, line numbers recomputed by the script); the press counts,
bracket rates, baselines and the 4-of-44 coverage are `derived` (rule stated in the report §4, inputs
named); X, A and boost stay `UNKNOWN`.

## Files written

| file | bytes | what |
|---|---:|---|
| `Tools/scripts/sampler_unknowns.py` | 38,886 | the analysis, `--write` / `--check` (check rebuilds every number and byte-compares) |
| `Research/BatmobileGrab/SAMPLER_UNKNOWNS.md` | 17,416 (17,402 characters - the script's own print counts characters, not UTF-8 bytes) | the card: corpus, press census, 4-of-44 coverage, method, per-UNKNOWN tables, LT control, 10 oracles |
| `tmp/freebuff/reports/SAMPLER-offline.md` | this file | DONE report |

Read-only inputs: the seven logs, `SAMPLER_FIELDS2.md`, and `bmak_runtime_sampler.py` (only to name the
log keys). No other file was read or written.

## Commands and output (verbatim; the exploratory commands are marked as excerpts)

Corpus and field census (excerpt - the command printed all 63 fields and all 1,122 record keys):

```
cd "E:/Modding/JC3-Batmobile" && python -c "..."
top keys Counter({'t': 1122, 'changed': 1122})
field count 63
357 in0.aLeftTrigger
274 veh1.flags_11D8
...
```

Press extraction over every log (excerpt - the command printed every `in0.*` transition, ~700 lines):

```
cd Research/BatmobileGrab/runtime && python - <<'EOF' ... EOF
========== samples-20261103T084831Z.jsonl records 17 inputs sampled: ['in0.aLeftShoulder', 'in0.aLeftTrigger', 'in0.aRightTrigger', 'in0.aThrottleAxis', 'in0.bCancelButton']
    3 08:49:17.715 in0.aLeftTrigger       0.0 -> 1.0
...
========== samples-20261103T120003Z.jsonl records 729 inputs sampled: [...same five...]
```

That is the finding that decides UNKNOWNs 1 and 3: **five** input keys exist, no `bVehicleBoostButton`,
no X byte, no eject byte.

Control diagnostic (the LT binding, to test whether the method has any power):

```
cd "E:/Modding/JC3-Batmobile" && python - <<'EOF' ... EOF
LT presses 175 with a following flags/weapon change: 173
lag median 13.936  p25 1.599  p75 33.152  max 106.380
lag buckets Counter({'>5': 106, '<=0.5': 22, '<=5': 18, '<=2': 15, '<=1': 12})
hit within 2s 49/175  within 5s 67/175
baseline hit within 2s (random records): 158/300
```

Final build and check (the values in the report are these numbers):

```
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/sampler_unknowns.py --write; echo "WRITE_EXIT=$?"; echo "=== CHECK ==="; PYTHONIOENCODING=utf-8 python Tools/scripts/sampler_unknowns.py --check; echo "CHECK_EXIT=$?"
```

```
wrote Research\BatmobileGrab\SAMPLER_UNKNOWNS.md (17,402 B)
logs: 7; records: 1122; observables parsed: 44
WRITE_EXIT=0
=== CHECK ===
OK rebuilt byte-identical from 7 logs and 44 observables
CHECK_EXIT=0
```

Final `--check` after this report was written (no input or output changed between the two runs):

```
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/sampler_unknowns.py --check; echo "CHECK_EXIT=$?"
```

```
OK rebuilt byte-identical from 7 logs and 44 observables
CHECK_EXIT=0
```

## The numbers the brief asked for

**Corpus.** 7 logs, 1,122 records, 124,237 B, span 2026-11-03T08:48:31.767Z to 2026-11-04T02:05:16.159Z.
Sampling intervals <= 5 s total 399.1 s; 73 longer gaps (max 46,273.1 s) excluded from every rate.
38 records carry a `null` (teardown) and are never counted as a change. 63 distinct sampled fields.

**Presses.** LT 175, B 62, LB 4, RT 70, THR 73. **X 0, Y 0, A 0.**

**Coverage.** Of G3-02f's 44 observables, **4** appear in the logs, matched by class+offset:
`RPlayerInput.aThrottleAxis` (840), `RVehicleWeapon.bFiring` (2084, on the EMP-missile/tracker objects),
`RVehicleBatmobileBase.bBoostLocked` and `InfiniteBoost` (bits of the sampled word at 0x11D8 = 4568).
`bBoostLocked` never sets in 284 word reads; `InfiniteBoost` sets once, in a teardown record. The other
**40** - every missile-launcher, every eject and all five boost-object fields - are absent.

**Rate test (the brief's rule).** One sampling interval around the press (union of brackets, so
overlap is counted once), press-free baseline = intervals no bracket touches. Candidate only if the
field changed inside >= 3 distinct brackets **and** rate_in >= 3 x rate_out **and**
rate_in - rate_out >= 0.5 s^-1.

**Result - X:** 0 presses, no field. No table can exist. UNKNOWN.

**Result - A:** 0 A presses. Nearest action = LB (exit/enter), 4 presses, 1.397 bracket-seconds,
179.6 press-free seconds. Only `veh1.Driver`, `veh1.BatmanVsBatmobileCollisionMode`, `veh1.bits11D8`
and `veh1.flags_11D8`/`flags_11DC` move inside any LB bracket, each on 1-2 presses. **0 fields pass**
the >= 3-press floor; the press's own key is excluded as a construction artifact. UNKNOWN.

**Result - boost:** 0 Y presses; no boost field sampled; the two bits never move; and a duration could
only be measured from `bBoosting` rise/fall, which was never read. UNKNOWN.

**Control (the reason the negative results mean nothing either way):** LT, a confirmed binding, gives
`veh1.flags_11D8` 12/175 presses at 0.095 s^-1 in-bracket vs 1.136 s^-1 press-free (ratio 0.08) -
**0 of 5 fields pass**, and the 2.0 s sensitivity check is 49/175 (28%) for presses vs 294/402 (73%)
for press-free instants. The logs' flags word churns several times a second regardless of input, so
this corpus cannot attribute a state change to a press by timing.

## Two scope notes (recorded, not silently resolved)

1. The brief says G3-02f "left 3 UNKNOWNs"; `SAMPLER_FIELDS2.md` §6 actually lists **four**. Three are
   actions (X byte, A byte, boost duration) and are the ones tested here; the fourth - TArray element
   stride for `CurrentTargets`/`FiredProjectiles` - is not an action and the brief's scope excludes it.
2. The brief says "the logs carry the user's presses per G3-02d". They carry five input bytes, and of the
   G3-02d scripted actions only LT, B and LB (plus RT/THR driving). A and both queried buttons are absent.

## UNKNOWNs

1. **X barrage input byte** - no X press in any log (0), no X-named field in `RPlayerInput`, no
   launcher field sampled. Where it would be answered: `BmInput.ini` / the bind table (decode), or a new
   capture that reads `PI` +773/+774/+784 and the launcher's target count.
2. **A eject input byte** - 0 A presses; `bBatmobileEjectModifier` (+786) never read; the LB-correlated
   vehicle fields are consequence markers, and they clear only 1-2 of 4 presses. Same two routes.
3. **Boost duration / time** - 0 Y presses; `bBoosting` (+2396) never read; no timer field exists in the
   layout. Needs a capture that reads +2396, then a rise/fall measurement - not a field read.
4. **Whether any input->state link is recoverable from these logs at all** - the LT control fails
   (0/5 fields, 28% vs 73% at 2 s). Closing that needs denser sampling around a single isolated press,
   which is a new capture, not an analysis of this corpus.

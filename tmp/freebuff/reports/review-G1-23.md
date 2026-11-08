# Independent review — G1-23 · Footage capture for behaviours the files cannot give

Reviewer: not the author. Read-only pass: nothing in `GRAB_BACKLOG.md`, `MODLOG.md`, `Research/`,
`Tools/` or any game file was modified. Only this file was written. No game launched, no commit, no
secrets.

Card: `GRAB_BACKLOG.md:560-572` (deps G1-08…G1-21, serves WPN/MOD). Tracker row:
`GRAB_BACKLOG.md:1291`. MODLOG sections: `MODLOG.md:8881` (first done, 2026-10-25) and
`MODLOG.md:8944` (§"G1-23 · Footage and file answers — revised", 2026-10-26 — the one the tracker
cites).

Outputs: `Research/BatmobileGrab/FOOTAGE.md` (259 lines), `Research/BatmobileGrab/FOOTAGE.json`
(1,324 lines, schema 2), `Tools/scripts/grab_footage_gaps.py` (691 lines).

**Sources read for this review:** the stored record, a read-only re-run of `build()` and
`write_markdown()`, `WEAPONS.json`, `MODES.json`, `OFFSETS.json`, `objects.jsonl`,
`DAMAGE_RULES.md`, and `ffprobe` on the five captures the script reads (timing only, nothing
written).

## VERDICT: needs rework (narrow)

The measurement is real and reproduces exactly: the three air samples (1.251 / 1.183 / 1.200 s)
land on the frames and presentation timestamps the record prints, the two file-value rows are
correctly closed by `HeatUpPerSecond` 0.0 and the decoded `InaccuracyVsTime` curve, and the 72-row
reason split matches the note row for row. `--check` exits 0 and the JSON equals a fresh build.

What is not done:

1. **R11 in the generated note.** The generated F-6 row carries a hand-typed sample list
   ("1.251 / 1.183 / 1.200 s", "37-38 unique frames") that no check ties to the samples it sits
   next to. I changed the samples in memory by +0.6 s and `--check` still printed **23/23** while
   the row read "**1.812 s mean** … (1.251 / 1.183 / 1.200 s)". The same typed pattern is in the
   §2 curve table (typed tuple, though that one *is* pinned by a check) and in the HeatBar values.
2. **The gate never reads `FOOTAGE.md`.** `main()` tests `os.path.isfile(md_path)` and diffs only
   the JSON (`grab_footage_gaps.py:670-676`), so a hand edit to the note passes — exactly the hole
   the G1-14 rework closed in `DAMAGE_RULES.md`. Today the note equals `write_markdown(build())`
   byte for byte (verified), so nothing is wrong yet, only uncatchable.
3. **Two of the 23 checks cannot fail**, so "23/23" overstates the evidence: `bool(VULCAN_OUT_OF_FRAME)`
   (`:450`, non-empty constant) and `"UNREACHABLE" not in REASONS` (`:384-385`, a module constant).
   A third, the R4 check at `:436-439`, tests two hardcoded gap strings rather than the invariant
   its name claims.
4. **Two claims go past the evidence** (R4/R5): "the car is controllable in the air" is asserted
   from air *time* alone (`FOOTAGE.md:86`, `:142`), which shows the airborne window, not steering
   authority; and "firing adds no heat, so the bar cannot reach a stop" (`FOOTAGE.md:130`) turns
   one per-second field into a statement about all heat input, while `OverheatOffValue` 0.25 and
   `ChainGunOverheatSound` show the overheat path exists in the object.

None of these makes a printed number wrong today, which is why the verdict is narrow rather than a
rebuild: the data side is sound. But rules R11 and R4 are explicit, and the card's cited evidence
(`--check`, 23/23) is weaker than it reads.

## Check output (verbatim)

```
$ python Tools/scripts/grab_footage_gaps.py --check
OK: 72 rows, 2 file-resolved, 1 measured (3 samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1, 'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53, 'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 23/23 checks
EXIT=0
```

Record freshness, read-only re-run:

```
$ python - <<'EOF'
import sys, json
sys.path.insert(0,'Tools/scripts'); import grab_footage_gaps as G
d=G.build(); disk=json.load(open('Research/BatmobileGrab/FOOTAGE.json',encoding='utf-8'))
print('json equal:', d==disk)
print('md equal to fresh render:', open('Research/BatmobileGrab/FOOTAGE.md',encoding='utf-8').read()==G.write_markdown(d))
EOF
json equal: True
md equal to fresh render: True
```

## Issues

### 1. (R11, blocking) F-6 carries typed sample numbers that `--check` cannot see

`Tools/scripts/grab_footage_gaps.py:388-394` builds the F-6 row with a literal list
`"(1.251 / 1.183 / 1.200 s)"` and `"37-38 unique frames"` beside a computed mean, while the
per-sample table in §3 is rendered from `doc["rows"]`. The two therefore cannot be compared by any
check — and the check only asserts sample count, snap error, spread ≤ 0.1 s and ≥ 1.0 s.

Demonstration (in memory, no file written): I wrapped `air_samples()` to add 0.6 s to each
`air_time_s` and rebuilt.

```
$ python - <<'EOF'
import sys; sys.path.insert(0,'Tools/scripts'); import grab_footage_gaps as G
real=G.air_samples
def fake():
    s=real()
    for x in s: x["air_time_s"]=round(x["air_time_s"]+0.6,4)
    return s
G.air_samples=fake
d=G.build(); md=G.write_markdown(d)
print([l for l in md.splitlines() if l.startswith("| F-6 ")][0])
print("checks pass:", sum(1 for c in d["checks"] if c["pass"]), "/", len(d["checks"]))
EOF
| F-6 | ... | **measured: 1.812 s mean** across three ramp jumps (1.251 / 1.183 / 1.200 s), 37-38 unique frames each at the captures' ~31 fps cadence. ... | **MEASURED** | `MEASURED` |
checks pass: 23 / 23
```

The mean moved, the sample list did not, and every check still passed. Fix inside the generator:
format the list from the samples (`" / ".join("%.3f" % s["air_time_s"] for s in good)` and the
`frames_airborne` range), and add a check that the row text contains the formatted samples. The
same treatment applies to `FOOTAGE.md:71` (curve tuple, typed at `:544`) and the HeatBar values at
`:553-555` — the curve is at least pinned by `check("the InaccuracyVsTime curve is decoded …")`,
the HeatBar pair is not.

### 2. (gate) `--check` never verifies `FOOTAGE.md`

`grab_footage_gaps.py:670-676`:

```
    if not os.path.isfile(json_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    ... if json.load(fh) != doc: print("STALE …")
```

The note is only tested for existence; nothing re-renders `write_markdown(doc)` and diffs it. So
the file that says "Generated by `Tools/scripts/grab_footage_gaps.py`" (`FOOTAGE.md:3`) can be
hand-edited while the tracker's `--check` stays green. Today it is identical to a fresh render, so
this is a coverage hole, not drift. Fix: render and compare, printing `md: PASS|FAIL`, as
`bmak_damage.py --check` now does after the G1-14 rework.

### 3. (evidence quality) two checks are tautologies and inflate the 23/23 count

- `grab_footage_gaps.py:449-450`: `check("the Vulcan capture is recorded as out-of-frame for fire
  intervals", bool(VULCAN_OUT_OF_FRAME), "recorded")` — `VULCAN_OUT_OF_FRAME` is a non-empty string
  constant (`:95-97`), so this is always `True`.
- `:384-385`: `check("air rows no longer claim UNREACHABLE …", "UNREACHABLE" not in REASONS, …)` —
  `REASONS` is a dict literal without that key (`:57-71`), so this is always `True`.
- `:436-439`: the "no row measured by footage also has a file value (R4)" check looks only at two
  hardcoded gap labels and would not catch a new MEASURED row that duplicates a file answer.

The tracker cites `(23/23)` as the card's proof. Two of those 23 prove nothing, and one proves far
less than its name. Fix: derive the Vulcan statement from `doc["vulcan_note"]` being non-empty in
the record, drop or make real the `UNREACHABLE` premise check (e.g. assert no row has that reason
code), and make the R4 check walk every MEASURED row's subject against the file-side sources.

### 4. (R4/R5) "the car is controllable in the air" is not what the footage measures

`FOOTAGE.md:86` and `FOOTAGE.md:142` (F-6):

> "The car is controllable in the air for over a second on every jump - which is the observable
> the `AirControl*` fields govern." … "the car is controllable in the air for over a second per
> jump, and the value that runs is a native default"

What was measured is the airborne interval between "first frame clear of the ramp" and "first frame
with ground contact" (§3, `:76-80`): 1.251 / 1.183 / 1.200 s. Air time says the car is *airborne*;
it says nothing about whether pitch/yaw input changes the attitude, which is what `AirControl*`
governs. The clips' names ("Air steer up / down / right") are the only evidence for steering, and
the record does not say so. `bUsedAirControlDuringJump` is a *member name*, not an observation
(R5). Reword to: airborne window measured; that the player steered in it rests on the capture
names, not on the measurement; steering authority itself remains UNKNOWN from the files. If the
steering is to be a measured claim, the sample needs an attitude/displacement observable.

### 5. (R4) the heat mechanism claim is stronger than the field supports

`FOOTAGE.md:130` (F-3) and the correction box at `:11-14`:

> "`HeatUpPerSecond` = **0.0** … firing adds no heat, so the bar cannot reach a stop and the weapon
> fires indefinitely … the behaviour … is the field's own value, not a missing number"

`HeatUpPerSecond` is the *per-second* heat term; 0.0 removes that input. It does not establish that
no other heat input exists — the same object carries `OverheatOffValue` 0.25 (printed in the note)
and `RBatmobileCannon.ChainGunOverheatSound`, i.e. an overheat path is wired. A per-shot heat add in
native code is not excluded by this grab. The *outcome* (it never overheats in play) is supported by
the user's 2026-10-26 observation, which the record names; the *mechanism* sentence is inferred and
should be stated as "no per-second heat is configured; the observed no-overheat behaviour is the
user's note, the causal path is not in the files".

### 6. (R11, minor) five "answered, not gaps" rows display no value

`FOOTAGE.md:92-115` is headed "What the files already answer (not gaps)" and the summary counts
`quantities the files *do* answer (not gaps) | 20` (`:27`). Five of the twenty show
`array (points not decoded)` in the value column (`:108-115`): charge, salvo / targets, launch
sockets, screen shakes, bones to hide.

```
$ python - <<'EOF'   # FOOTAGE.json, answered[]
...print(len([q for q in f['answered'] if q['example_value'] is None and not q['array_points']]))
5
```

`grab_footage_gaps.py:293-296` takes `q["fields"][0]` as the example, which is the first matched
path — for charge that is `ChargingScreenShake` (value `None`) although `RBatmobileHeavyCannon.
ChargeUpTime` = 2.5 is in the same match set; for salvo it is `MaxTargetsPerLevel` (array
`decoded: false`) although `RBatmobileMissileLauncher.MaxTargets` = 8 / 16 is present. So two rows
understate their evidence and three (launch sockets, screen shakes, bones) genuinely have no decoded
contents — their array headers do carry counts (10 and 2) that could be shown. Either pick the first
matched field with a decoded value, or split the section: "answered" (decoded) vs "field exists,
contents not decoded (not a footage gap)". As written, the sentence "The card's own examples that
`WEAPONS.json` carries a value for" (`:94`) is false for those rows.

### 7. (minor, check wording) "each with >= 3 samples of itself" is not what was done

`grab_footage_gaps.py:374-376` names the check
`"three ramp jumps are measured, each with >= 3 samples of itself"`, detail `"3 measured"`. There
is **one** sample per clip, three clips — three samples for one gap, not three per jump. The card
asks for "repeat count (≥ 3 samples)" per gap, which three independent jumps satisfy; only the
check's name is wrong. It is the line a later reader will quote.

### 8. (minor, evidence) the Health check verifies only the first package

`grab_footage_gaps.py:339-341` asserts `health_val[0] == 1200` while the note prints all three
values (`FOOTAGE.md:131`: `[1200, 1200, 1200]`, `IntProperty, 3 packages`). All three are 1200
today (verified), but the check would pass with the other two different. Assert the whole list.

### 9. (coverage) the gap list is not demonstrably complete for G1-14's natives

The card's In is "list of `UNKNOWN`/`native` values from G1-08, G1-14, G1-21". `DAMAGE_RULES.md:
72-82` records **five** native entry points (`ShouldRadialDamageHit`,
`CanBatmobileDoImpactDamage`, `SetDamageLevel`, `SetArmouredMode`, `GetDamageMod`); FOOTAGE has one
`NATIVE` row (F-4, `ShouldRadialDamageHit`). Two of the other four are setters and one is a gate, so
they need not each be a gap — but `GetDamageMod` is the encounter multiplier behind ARM-2's
hits-to-kill, which the tank-shell row (F-5) explicitly depends on, and the record never says why it
is not a row. Add a line in §5 stating which natives are out of scope and why, or a row. There is
also no check that ties the 72 rows back to the three source records, so "every gap" in the Done
line is asserted, not verified.

## Spot-checks (value → where verified)

| value in doc | doc line | verified at |
|---|---|---|
| air steer up: air 1.251 s, frames 97→133 | `:82` | `ffprobe` PTS frame 97 = 3.203933 s, frame 133 = 4.455300 s → 1.251367 s |
| air steer right: first air 149 / 5.006 s, first contact 186 / 6.205 s, 1.200 s | `:84` | PTS frame 149 = 5.005567 s, frame 186 = 6.205533 s → 1.199966 s |
| air steer down: 96 / 3.285 s → 133 / 4.468 s, 1.183 s | `:83` | PTS frame 96 = 3.284900 s, frame 133 = 4.468133 s → 1.183233 s |
| clip frame counts 189 / 202 / 267, durations 6.39 / 7.15 / 8.88 s | `:42-44` | `ffprobe -count_frames`: 189 @ 6.388 s, 202 @ 7.1532 s, 267 @ 8.882134 s |
| `Health` = [1200, 1200, 1200], IntProperty, 3 packages | `:132` | `OFFSETS.json` `RVehicleBatmobile` offset 1144, `count: 3`, `values: [1200, 1200, 1200]` |
| 0 tank weapon/shell objects in the grab | `:132` | scan of `objects.jsonl` (20,128 objects) with the script's filter: 0 (42 names contain "tank", none a weapon/projectile class) |
| `HeatUpPerSecond` 0.0 in 4 of 4 cannon objects | `:57` | `WEAPONS.json`: 0.0 for Funhouse, Joker, MK2, SF `Batmobile_Cannon_V2` |
| `InaccuracyVsTime` 4 points 0→0, 0.5→0, 1.5→1.5, 2.5→3.0 | `:61-66` | `WEAPONS.json` `InaccuracyVsTime.Points`, same four pairs in all four packages (`InaccuracyVsTimeUpgrade` is the separate 0/1/3/5 → 0/0/1.5/3.0 curve, correctly not used here) |
| `InaccuracyAngle` 0.1 | `:68` | `WEAPONS.json` value 0.10000000149011612 |
| 61 not-serialised mode fields, 5 undocumented units | `:136`, `:27-35` | `MODES.json`: 61 `serialized == False`, 5 `unit_basis == "none"` |
| 72 rows, split 2 / 1 / 53 / 8 / 5 / 2 / 1, 20 answered | `:23-35` | `FOOTAGE.json` `summary`; sums to 72 |
| `AirControl` declared on `Pawn` at 0x448, float, not serialised | `:143` (F-7) | `MODES.json` field entry: `Pawn 0x448 float serialized False unit_basis none` |

Every number I checked reproduces. The record is not stale and the note is currently a true render
of the JSON.

## Limits of this review

I did not re-derive the four screenshots' visual boundaries (first-air / first-contact frames) —
those are documented visual calls, and what I verified is that the recorded frame indices and PTS
values exist and give the printed intervals. I did not watch the clips, so I cannot say whether the
car is steered in them (issue 4) or whether the Vulcan really fires indefinitely (issue 5); both
rest on the user's notes, which the record names. I did not re-run G1-08/G1-14/G1-21; I checked that
the counts the note takes from `MODES.json` and `WEAPONS.json` are those files' current values.

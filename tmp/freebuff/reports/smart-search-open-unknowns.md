# Smart search on the open UNKNOWNs — judge choice, 25 members, and what survived R4

**Task:** run `Tools/scripts/chase/smart_search.py` over members the project still lists as UNKNOWN /
not-found, with the judge `tmp/freebuff/reports/jeb-vs-qwen-calibration.md` recommends, and re-verify
every `found=true` against its source address or offset before reporting (R4).

**Answer in one line:** the recommended judge is **Qwen3.5-4B** (Qwen, no threshold; Jeb is rejected
by the calibration at every threshold), all **25** members were run, **80** candidates were judged,
**4** came back `found=true`, and **2 of those 4 fail R4** — one is the wrong field at the right
offset, one is the right offset on the wrong class. **Two values survive** and are listed in §5 for an
apply brief:

> `BattleModeHeight` = **250.0** (F-33, 0x199c, `Default__RVehicleBatmobileBase`)
> `ImpactShakeAbandonedVehicleFactor` = **3.0** (F-35, 0x1ccc, `Default__RVehicleBatmobileBase`)

Nothing was entered into `FOOTAGE.md`, `MODES.json` or the tracker. Revert = delete this file.

Labels: **verified** = the literal was re-read at the record the judge named *and* the record's own
offset/class agree with the declared member; **rejected** = it does not; **UNKNOWN** = no candidate.

---

## 0. Judge choice, from the calibration report

`jeb-vs-qwen-calibration.md` verdict: *"keep the Qwen3.5-4B judge as the default for smart search, and
do not switch to Jeb at any threshold."* Jeb's stored P(true) never reaches 0.5 on any of the 190
verdicts (max 0.472, on a *found* case), so at its only zero-false-positive threshold it returns
nothing; below it, negatives fire and positives still do not. Qwen is the only judge that gets the one
disagreement right (F35 = 3.0).

| | judge | threshold | server |
|---|---|---|---|
| used | **qwen** (`--judge qwen`) | n/a — the prompt is a yes/no verdict, no P(true) | `127.0.0.1:8080`, model `qwen3.5-4b` |

No `P(true)` is reported for any row because Qwen does not produce one; the calibration's `--judge jeb`
path is the only one with a probability, and it is not used.

### 0.1 The judge had to be brought up, and how

The project's Qwen launcher is `E:\AI\agent_qwen3.5-4b-q6-32k.bat` (llama-server, `-c 32768`, port
8080). Started as shipped, it **crashed during model load**:

```
load_model: loading model 'E:\AI\models\Qwen3.5-4B-Q6_K.gguf'
ggml.c:1644: GGML_ASSERT(ctx->mem_buffer != NULL) failed
```

`/health` then answered `503 Loading model` indefinitely. The machine reports 16.7 GB RAM; the 3.5 GB
Q6 model plus a 32k f16 KV cache did not fit in the free block at start. Recovery: the same model, same
alias, same port, **`-c 8192`** instead of 32768 —

```
E:/AI/llama/llama-server.exe -m E:/AI/models/Qwen3.5-4B-Q6_K.gguf -t 4 -np 1 -c 8192 \
  --host 127.0.0.1 --port 8080 --jinja --alias qwen3.5-4b
```

`/health` → `{"status":"ok"}`. The judge saw the same prompt (`chase_judge.PROMPT`, version
`51c8dd3c`); only the server's context window differs from the launcher, and every snippet here is
≤ 12 KB, so 8k is not a constraint. **This deviation is recorded because it is not the shipped
launcher.**

**Every one of the 80 verdicts came from the verdict cache** (`cache 80`, `judge 0.00 s/candidate` —
`smart_search.py` keys the cache on model + prompt). They are therefore the **stored Qwen verdicts
from the calibration run** (prompt `51c8dd3c`, same candidates), not fresh model output. That is
reproducible and cost no model call; it also means the result is exactly what the calibration run
already decided, which is consistent with its 1/28 recall.

---

## 1. The search half is the real bottleneck — 0/25 on the current search

Before judging, every member was run with `--url http://127.0.0.1:9` (judge unreachable) so only the
search half ran:

```
python Tools/scripts/chase/smart_search.py --member <M> --owner <O> --offset <OFF> --type <T> \
  --judge qwen --max 6 --quiet --url http://127.0.0.1:9 --search current
```

**Result: `0 candidates` for all 25 members.** The calibration report predicted this in its last
paragraph — *"the live search half currently returns 0 candidates for these members… the search filter
(`store_verdict` in `chase_candidates.py`) is the first thing to fix, before any judge choice
matters."*

Re-running the same 25 against the frozen search half (`--search v1`) gives **80 candidates across 21
of 25** members. `v1` is labelled calibration-only in the tool; it is used here **because it is the
only half that produces evidence**, and every hit is still verified by hand (R4), so nothing enters a
record on the strength of a candidate list. All judged rows below are `v1`.

This is the finding to act on first: **no judge can be measured on a search half that returns nothing.**

---

## 2. The 25 members and what each returned

`cands` is `current / v1`; `judged` counts only v1 verdicts actually sent (all cache hits).

| # | member (FOOTAGE id) | owner | offset | cands c/v1 | judged | found | verified |
|---:|---|---|---|---:|---:|---:|---|
| 1 | `AirControl` (F-7) | `Pawn` | 0x448 | 0 / 6 | 6 | 0 | — |
| 2 | `StrafeCooldown` (F-16) | `RVehicleBatmobileBase` | 0x11e4 | 0 / 5 | 5 | 0 | — |
| 3 | `StrafeForce` (F-18) | `RVehicleBatmobileBase` | 0x11f8 | 0 / 6 | 6 | 0 | — |
| 4 | `StrafeTorque` (F-19) | `RVehicleBatmobileBase` | 0x11fc | 0 / 4 | 4 | 0 | — |
| 5 | `StrafeDuration` (F-20) | `RVehicleBatmobileBase` | 0x1200 | 0 / 4 | 4 | 0 | — |
| 6 | `StrafeTime` (F-21) | `RVehicleBatmobileBase` | 0x1204 | 0 / 3 | 3 | 0 | — |
| 7 | `StrafeFwdCorrectionForce` (F-22) | `RVehicleBatmobileBase` | 0x1208 | 0 / 4 | 4 | 0 | — |
| 8 | `StrafeRight` (F-17) | `RVehicleBatmobileBase` | 0x11ec | 0 / 6 | 6 | 0 | — |
| 9 | `ImpactRoadAssistTimer` (F-25) | `RVehicleBatmobileBase` | 0x1758 | 0 / 2 | 2 | 0 | — |
| 10 | `ImpactRoadAssistMaxAngle` (F-26) | `RVehicleBatmobileBase` | 0x176c | 0 / **0** | 0 | 0 | no evidence |
| 11 | `ImpactRoadAssistAngVelocityTime` (F-27) | `RVehicleBatmobileBase` | 0x1770 | 0 / **0** | 0 | 0 | no evidence |
| 12 | `ImpactRoadAssistSteeringFactor` (F-28) | `RVehicleBatmobileBase` | 0x1774 | 0 / **0** | 0 | 0 | no evidence |
| 13 | `ImpactRoadAssistLookAheadTime` (F-29) | `RVehicleBatmobileBase` | 0x1778 | 0 / **0** | 0 | 0 | no evidence |
| 14 | `BattleModeWidth` (F-31) | `RVehicleBatmobileBase` | 0x1994 | 0 / 3 | 3 | 0 | — |
| 15 | `BattleModeLength` (F-32) | `RVehicleBatmobileBase` | 0x1998 | 0 / 3 | 3 | **1** | **rejected** (§4.1) |
| 16 | `BattleModeHeight` (F-33) | `RVehicleBatmobileBase` | 0x199c | 0 / 4 | 4 | **1** | **verified 250.0** |
| 17 | `JumpRampUpwardForce` (F-34) | `RVehicleBatmobileBase` | 0x1a60 | 0 / 5 | 5 | 0 | — |
| 18 | `ImpactShakeAbandonedVehicleFactor` (F-35) | `RVehicleBatmobileBase` | 0x1ccc | 0 / 4 | 4 | **1** | **verified 3.0** |
| 19 | `ImpactShakeDestructiblesFactor` (F-36) | `RVehicleBatmobileBase` | 0x1cd0 | 0 / 4 | 4 | 0 | — |
| 20 | `ImpactShakeCoolDown` (F-37) | `RVehicleBatmobileBase` | 0x1cd4 | 0 / 6 | 6 | **1** | **rejected** (§4.2) |
| 21 | `BattleModeSpeedDelta` (F-38) | `RVehicleBatmobileBase` | 0x1eb4 | 0 / 4 | 4 | 0 | — |
| 22 | `BattleModeCamFOV` (F-11) | `R3rdPersonCamera` | 0x4fd0 | 0 / 3 | 3 | 0 | — |
| 23 | `BattleModeWinchCamFOV` (F-12) | `R3rdPersonCamera` | 0x4fd4 | 0 / 2 | 2 | 0 | — |
| 24 | `BattleModeHeadOffset` (F-13) | `R3rdPersonCamera` | 0x4fdc | 0 / 1 | 1 | 0 | — |
| 25 | `BattleModeTransformationAnimName` (F-30) | `RVehicleBatmobileBase` | 0x193c | 0 / 1 | 1 | 0 | — |
| | **totals** | | | **0 / 80** | **80** | **4** | **2 verified** |

Precision on this set: **2/4 = 0.500** after R4, which is lower than the calibration's 1.000 on 38
cases — the difference is that these members' snippets had never been checked against their offsets
before. `unparsable 0 (0.0 %)` on all 80 verdicts.

---

## 3. What the judge said, verbatim, for each hit

| member | value | source the judge named | its reason |
|---|---|---|---|
| `BattleModeLength` | `'265.0'` | `chase2_defaults.json:107` | "explicitly assigns the literal value 265.0 to the field BattleModeLength … for RVehicleBatmobileBase" |
| `BattleModeHeight` | `'250.0'` | `chase2_defaults.json:129` | "explicitly assigns the literal value 250.0 to the field BattleModeHeight in an object default record" |
| `ImpactShakeAbandonedVehicleFactor` | `'3.0'` | `chase2_defaults.json:151` | "explicitly assigns the literal value 3.0 to the field … in a default object definition" |
| `ImpactShakeCoolDown` | `'20.0'` | `chase2_defaults.json:316` | "explicitly assigns the literal value 20.0 … on the RVehicleBatmobileBase object" |

All four are **text-route** hits in the same derived dump
(`E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json`), not the `.upk`. That dump is the CDO/tag
scan's own extraction, so a hit there is evidence *about that dump*; it becomes evidence about the
game only when the record's offset and class agree with the declared member. That is what §4 checks.

---

## 4. R4 — the literal checked at the source record

The record shape is: `class`, `export`, `field`, `object`, `offset`, `owner_expected`, `type`, `value`.

### 4.1 `BattleModeLength` — **REJECTED** (wrong field at the right-looking offset)

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "control BattleModeLength",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 6548, "owner_expected": "RVehicleBatmobileBase",
  "type": "FloatProperty", "value": 265.0 }
```

`offset 6548 = 0x1994`. The declared layout is `BattleModeWidth` **0x1994** (F-31) and
`BattleModeLength` **0x1998** (F-32). The record's own `field` string is `control BattleModeLength`
— not `F-32 BattleModeLength` — and its value **265.0 is the known `BattleModeWidth` default** (the
calibration's F31). The neighbouring record at `0x199c` is labelled `F-33 BattleModeHeight` and holds
250.0, so the F-31/F-32/F-33 offsets do run 0x1994 / 0x1998 / 0x199c. **The judge attached the Width
value to the Length member.** No value for F-32 enters.

**Independent confirmation:** `Research/BatmobileGrab/MODES.json` `fields[36]` declares
`BattleModeLength` at **offset 6552 = 0x1998**; the record the judge cited is at **6548 = 0x1994**.
The rejection does not depend on the judge's reasoning at all.

### 4.2 `BattleModeHeight` — **VERIFIED**

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "F-33 BattleModeHeight",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 6556, "owner_expected": "RVehicleBatmobileBase",
  "type": "FloatProperty", "value": 250.0 }
```

`6556 = 0x199c` — exactly the declared F-33 offset; class and object are the Batmobile base CDO; type
`FloatProperty`; the id prefix `F-33` matches the FOOTAGE row. **Value 250.0.**

### 4.3 `ImpactShakeAbandonedVehicleFactor` — **VERIFIED**

```json
{ "class": "RVehicleBatmobileBase", "export": 10923,
  "field": "F-35 ImpactShakeAbandonedVehicleFactor",
  "object": "Default__RVehicleBatmobileBase",
  "offset": 7372, "owner_expected": "RVehicleBatmobileBase",
  "type": "FloatProperty", "value": 3.0 }
```

`7372 = 0x1ccc` — the declared F-35 offset; class correct (`MODES.json` `fields[51]`: offset 7372,
`declaring_class` `RVehicleBatmobileBase`). **Value 3.0.** This is also the one value
the calibration independently records as Qwen being right about (F35 `chase2_defaults.json:151` = 3.0),
so two separate runs agree.

### 4.4 `ImpactShakeCoolDown` — **REJECTED** (right offset, wrong class)

```json
{ "class": "RVehicleNPC", "export": 12268,
  "field": "F-37 ImpactShakeCoolDown",
  "object": "Default__RVehicleNPC",
  "offset": 7380, "owner_expected": "RVehicleBatmobileBase",
  "type": "FloatProperty", "value": 20.0 }
```

`7380 = 0x1cd4` matches F-37 exactly and the id prefix matches (`MODES.json` `fields[53]`: offset
7380, `declaring_class` `RVehicleBatmobileBase`), **but the record is `Default__RVehicleNPC`, not
`Default__RVehicleBatmobileBase`**, and `RVehicleBatmobileBase` derives
from `RVehicle` (`Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs:11`), not from `RVehicleNPC`. The
judge's own reason asserts the Batmobile-base object, which the record contradicts
(`owner_expected` is the query's expectation, not the record's class). A 20.0 at the same offset on a
sibling class is a coincidence until the Batmobile-base record is produced. **Not entered.**

---

## 5. Verified values, ready for an apply brief

| member | value | id | owner | offset | source record | check |
|---|---:|---|---|---|---|---|
| `BattleModeHeight` | **250.0** | F-33 | `RVehicleBatmobileBase` | 0x199c | `E:/Modding/_shared/gamedata/BmAKgrab/chase/chase2_defaults.json:129` | offset, class, object, type and id prefix all agree; text-route literal re-read |
| `ImpactShakeAbandonedVehicleFactor` | **3.0** | F-35 | `RVehicleBatmobileBase` | 0x1ccc | `.../chase2_defaults.json:151` | as above, plus the calibration's independent F35 hit |

Both are `FloatProperty` defaults on the class CDO `Default__RVehicleBatmobileBase` (export 10923).

**How to enter them (not done here):** an apply brief sets `MODES.json`/`FOOTAGE.md` F-33 and F-35 from
`UNKNOWN` to `FILE-VALUE` with the value and this record as the source, then `MODES.md`/`FOOTAGE.md`
are re-rendered by their own generators (`--check` must stay green). Note F-33 is *not* in the row
ledger's T- rows; F-35 is a camera/impact-shake scalar with no build row, so entering them changes the
record's completeness, not a build.

**Rejected, do not enter:** F-32 `BattleModeLength` (265.0 is Width's value at 0x1994) and F-37
`ImpactShakeCoolDown` (20.0 sits on `Default__RVehicleNPC`).

---

## 6. Everything searched, and what is still UNKNOWN

| outcome | members | meaning |
|---|---|---|
| verified | F-33, F-35 | value + offset + class all agree |
| rejected | F-32, F-37 | a literal exists but not for this member |
| judged false with evidence in front of the judge | 17 members (80 candidates) | Qwen refused every candidate; the value is not in that snippet |
| **no evidence at all** | F-26, F-27, F-28, F-29 (`ImpactRoadAssistMaxAngle`, `AngVelocityTime`, `SteeringFactor`, `LookAheadTime`) | 0 candidates on **both** search halves |
| search half returns nothing | all 25 on `current` | the blocker, §1 |

Still UNKNOWN after this pass, with where the value would come from:

- **F-26…F-29** (road-assist angle/velocity/steering/look-ahead): no candidate in the exe scan or the
  text dump. They are declared on `RVehicleBatmobileBase` and not serialised, so the only sources are
  the native CDO (a live read) or a disassembly of the `ImpactRoadAssist` consumer in
  `BatmanAK.exe`. **Not a judge problem — a corpus gap.**
- **F-7 `AirControl`** and the eleven `Strafe*` fields: 2–6 candidates each, all refused. If a value
  exists it is in a native default, not in the tagged stream (`MODES.md`: 61 fields not serialised).
- **F-11…F-15 (camera)** and **F-23/F-30** (`AnimNodeSequence` / `FName`): typed objects, not scalars;
  a "value" is a config graph or a name index, so `found=true` on a float would have been wrong anyway.

---

## 7. Commands (re-runnable)

```
# judge: same model, smaller context (the 32k launcher crashes on this machine)
E:/AI/llama/llama-server.exe -m E:/AI/models/Qwen3.5-4B-Q6_K.gguf -t 4 -np 1 -c 8192 \
  --host 127.0.0.1 --port 8080 --jinja --alias qwen3.5-4b

# search half only (judge bypassed): 0 candidates for all 25 on `current`
python Tools/scripts/chase/smart_search.py --member AirControl --owner Pawn --offset 0x448 \
  --type float --judge qwen --max 6 --quiet --url http://127.0.0.1:9 --search current

# the judged pass (v1 is the only half that returns evidence)
python Tools/scripts/chase/smart_search.py --member BattleModeHeight \
  --owner RVehicleBatmobileBase --offset 0x199c --type float \
  --judge qwen --max 6 --quiet --search v1 \
  --json-out tmp/freebuff/smartsearch/v1_BattleModeHeight.json
```

Per-member JSON is in `tmp/freebuff/smartsearch/v1_<member>.json` (25 files) plus `counts.txt` (the
`current`/`v1` candidate counts for all 25) and `judge.sh`/`run.sh` (the loops).

**Not done, deliberately:** `FOOTAGE.md`, `MODES.json`, `MODES.md`, `T_ROWS.jsonl` and the tracker are
untouched; no `T-` row was edited; no cache entry was written by hand (all 80 were read from the
cache).

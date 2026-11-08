# T-MD14 battle audio — the BmAK events, the JC3 state events, and what the missing mode flag costs

**Row:** T-MD14 (battle audio), blocked by T-16's **W-08**: *the donor has no mode-switch event.*
This note reads the BmAK side (`AUDIO_MAP.json`, `AUDIO_BANKS.md`) and the JC3 side
(`Working/Audio/bm_bank_manifest.json`, the usage vocabulary in `Research/JC3Grab/USAGES.md` /
`README.md` §"usages") and says what the absence costs, which is the row's actual content.

Labels: **decoded** = a name, id or byte count read at the file named; **derived** = arithmetic over
decoded inputs; **UNKNOWN** = searched and absent, with what would settle it.

---

## 0. Answer

BmAK's battle mode is **32 named engine events plus a battle steering bed**, all keyed to *gear index*
and *engagement*, living in two banks: `BML_Batmobile` (53 HIRC events — `Play_BattleMode_In_A…F`,
`_InRev_*`, `_Out_A…H`, `_OutRev_*`, `Play_BattlemodeEngine`, `Play_BML_EngineCoolTicks`,
`Play_BML_Persistent_idles`) and `BML_Battlemode` (7 HIRC events, 44 sounds, 24 media), of which the map
resolves exactly one by name: **`Play_Batmobile_Steering_Bed`, event id `3532435377` /
`0xD28CAFB1`, outer `Ww_BML_Battlemode`, attenuation 100**.

JC3's vehicle audio is **usage-keyed, not mode-keyed**: a `.epe` object carries a `Usage` name/hash and
the graph plays whatever sound/effect that usage binds. The vocabulary is **12 names** —
`EngineRunning` 69, `OnPartExplode` 33, `EngineSmoking` 23, `Explosion` 23, **`EngineNitro` 18**, and
seven more — with **no mode, stance, battle or transform usage anywhere**. That is W-08, confirmed from
the other side.

So the closest JC3 system is the **`EngineNitro` usage**: a state name that already switches the
vehicle's sound and effect set (18 vehicles, 307 objects, 202 of 232 `.epe` files carry the usage
space). The build's gap is **a `BattleMode` usage and a second event set**, plus the flag that sets it
— and the mode-switch research (`mode-switch-carriers.md`) shows JC3 has **no runtime mode flag at
all**, so the audio cannot be switched by anything the vehicle owns.

---

## 1. BmAK battle-mode audio, decoded

### 1.1 The banks

| bank | package | export | bytes | sha1 | BKHD | HIRC events | actions | sounds | ranseq | media |
|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| `BML_Battlemode` | `Engine` | 37005 | 830,548 | `83dc20e9be47a388` | 112 | **7** | 10 | 44 | 4 | 24 |
| `BML_Batmobile` | `Engine` | 37004 | 2,268,588 | `118a5687851f5c21` | 112 | 53 | — | — | — | — |

(`AUDIO_BANKS.md` rows; `AUDIO_MAP.json` `banks[]`.)

### 1.2 The named events and what each is keyed to

All names below are `AUDIO_MAP.json` `events[]` rows whose `bank` is `BML_Batmobile`; each is
`Play_*` on `Ww_BML_Batmobile`. The naming is systematic, which is what identifies the trigger:

| event family | count | key it encodes |
|---|---:|---|
| `Play_BattleMode_In_A` … `_In_F` | 6 | forward gear **1–6**, clutch **in** (engaged) |
| `Play_BattleMode_In_Rev` | 1 | reverse, engaged |
| `Play_BattleMode_InRev_A` … `_F` | 6 | reverse, **in** — the six-step reverse ramp |
| `Play_BattleMode_Out_A` … `_Out_H` | **8** | forward gears **1–8**, clutch **out** (shift) |
| `Play_BattleMode_Out_Rev` | 1 | reverse, out |
| `Play_BattleMode_OutRev_A` … `_G` | 7 | reverse, out, seven-step ramp |
| `Play_BattlemodeEngine` | 1 | mode-level engine layer (the battle engine bed itself) |
| `Play_BML_EngineCoolTicks` | 1 | cooling ticks (heat/cooldown bed) |
| `Play_BML_Persistent_idles` | 1 | persistent idle layer |
| **total named** | **32** | |

**Derived:** `Out_A…H` having **8** members while `In_A…F` has **6** is the signature of a gear-indexed
set: the battle gearbox exposes 8 forward ratios when disengaged (the shift path) and 6 when engaged
(the drive path). The `Rev`/`InRev`/`OutRev` triple is the same for reverse. The `In`/`Out` pair is a
clutch state, not a mode state — the mode is which **bank** plays.

### 1.3 The one event `BML_Battlemode` resolves, and the other six

`AUDIO_MAP.json`, resolved row (identical in all four Batmobile packages):

```json
{"package":"Playable_Batmobile_SF","name":"Play_Batmobile_Steering_Bed",
 "outer":"Ww_BML_Battlemode","event_id":3532435377,"event_id_hex":"0xD28CAFB1",
 "bank_ref":"Engine.BML_Battlemode","attenuation_radius":100.0,
 "status":"resolved","bank":"BML_Battlemode","targets":[625240879],"media":[{"wem":73608235,...}]}
```

That is the **battle steering bed**: a 100-unit-radius loop that follows steering, i.e. the sound that
tells the player the handling has changed. It is the single most important asset for T-MD14 because it
is the *audible carrier of the mode's handling*, not an engine sample.

The bank reports **7** HIRC events; the map names **1**. The other six are **UNKNOWN by name** — they
are in the bank but no `AkEvent` row in the 361-row map names them
(`AUDIO_MAP.json` `summary`: 361 rows, 118 unique ids, 239 resolved rows, 90 missing rows across 26
missing ids). They would be settled by walking the bank's HIRC table with the event ids and matching
`event_id` to `AkEvent` objects in `BmGame.upk` (the same `grab_audio_banks.py` path that produced
§1.1).

### 1.4 What triggers each event (derived from the names + the mode model)

| trigger | events | evidence level |
|---|---|---|
| mode entry (pursuit → battle) | `Play_BattleMode_In_*` set + `Play_BattlemodeEngine` | name, systematic; the mode switch itself is BmAK's `ArmouredMode`/battle toggle (`MODES.md`: `ArmouredModeDamageReduction`, `BattleMode*` family) |
| mode exit (battle → pursuit) | `Play_BattleMode_Out_*` set | name |
| gear change, engaged | `In_A…F` | name (`In` = clutch in) |
| gear change, disengaged | `Out_A…H` | name (`Out` = clutch out) |
| reverse select | `In_Rev`, `InRev_*`, `Out_Rev`, `OutRev_*` | name |
| steering in battle mode | `Play_Batmobile_Steering_Bed` | decoded row (outer switch `Ww_BML_Battlemode`) |
| heat / cooldown | `Play_BML_EngineCoolTicks` | name |
| idle | `Play_BML_Persistent_idles` | name |

No event in the map carries a numeric trigger threshold; the **gear index and the mode are the only
two state keys**, and both are supplied by script/native code, not by the bank.

---

## 2. The JC3 side: usage-keyed state, not mode-keyed

### 2.1 The usage vocabulary (12 names)

`USAGES.md` / `README.md` §usages, decoded from 232 `.epe` graphs and 885 effect links:

| usage | vehicles | what state it carries |
|---|---:|---|
| `EngineRunning` | 69 | engine on |
| `OnPartExplode` | 33 | a part exploded |
| `EngineSmoking` | 23 | engine damaged |
| `Explosion` | 23 | explosion |
| **`EngineNitro`** | **18** | **boost on** — the fleet's only "performance state" usage |
| (+ 7 more names in the 12-name table) | — | part/damage/impact states |

`EngineNitro` = hash **4197885156**, binds to the effects `dynamic_nitrous` (14 vehicles) and
`EngineNitro` (4 planes), and the `Usage` int sits on **307 objects in 202 of the 232 `.epe`** files.
The nitro sound chain is decoded end-to-end: sound GUID `f74ea43b-…` on 202 objects / 172 vehicles,
`vehicles.bank` `EVTS` 249, three FSB5 samples chosen by name (56 / 150 / 355 — the test-060 swap,
`bm_bank_manifest.json` card **B-11**, generator `Tools/scripts/bm_audio.py`).

### 2.2 What JC3 reacts to, and what it does not

| state | JC3 carrier | does it switch audio? |
|---|---|---|
| boost / nitro | `EngineNitro` usage (18 vehicles, 307 objects) + `arcade.nitro_boost` values | **yes** — the only performance-state usage |
| engine on/off | `EngineRunning` (69) | yes |
| engine damaged / smoking | `EngineSmoking` (23) | yes |
| part damaged / exploded | `OnPartExplode` (33), `EffectAttachments.on_part_reached_damaged_state` | yes |
| RPM (continuous) | `LandAudio.min_rpm` / `max_rpm`, `LandEngine` rpm curve | **continuous parameter**, not a state event |
| gear change | **none** — no gear usage, no gear event; `Transmission.gears` is a value, not an event | **no** |
| handbrake | `Brakes.rear.handbrake` + `tire_effects` (skid particles) | **no audio event** (§8 U3) |
| gear/landing gear change | `LandingGear ← landing_gears_T` (7 chassis) | affects a **part transform**, not audio |
| **mode / stance / battle** | **none** | **no** |

**Derived:** JC3's audio model is *(usage name → sound/effect)* plus *(RPM → continuous parameter)*.
It has no gear-indexed event set (BmAK's `In_A…F` / `Out_A…H` pattern) and no mode usage.

---

## 3. Is there a mode flag? — no, and here is the cost

`tmp/freebuff/reports/mode-switch-carriers.md` establishes: no JC3 module, entity graph or `.physicsc`
has a mode selector; the only runtime handling change is the **boost state** (`nitro_boost*`), the only
visual state is a **hinged part driven by a `*_T` variable**, and the only "second configuration" is a
**separate entity variant**. `ExtendedExposedVariables` — the module that could drive a flag from an
expression — carries **2 expressions in the whole fleet**, both for a speed-ramp effect.

**What that absence costs T-MD14, item by item:**

| BmAK feature | without a mode flag | cost |
|---|---|---|
| 32 gear-indexed battle engine events (`In_*`/`Out_*`, 6/8 ratios) | no gear event exists in JC3, and no second bank is selected | **the battle engine cannot be a separate set**; one RPM-driven engine loop must serve both modes |
| `Play_BattlemodeEngine` (mode-level bed) | no usage to play it on entry | **no entry/exit transition** — the mode change is silent |
| `Play_Batmobile_Steering_Bed` (the handling tell) | no state to start/stop the loop | **the player cannot hear the handling change** — the single largest loss, because it is the audio that represents T-MD5…T-MD8 |
| `Play_BML_EngineCoolTicks` | heat/cooldown states exist (`EngineSmoking`), but no battle-heat state | **partial**: could ride `EngineSmoking`, but that means "damaged", not "battle" |
| `Play_BML_Persistent_idles` | idle exists (`EngineRunning`) | **survivable**: the idle layer can play on `EngineRunning` |
| mode entry/exit timing | no flag → no timestamp | no A/B to measure, so T-MD14 cannot be verified as a *switch* at all |

**In one sentence:** without a mode flag the audio can carry *one* engine voice and a boost layer, but
it cannot carry a *second* engine voice, an entry/exit transition, or the battle steering bed — i.e.
every part of T-MD14 that makes the mode audible.

---

## 4. The closest system, and the gap the build must fill

> **Closest JC3 system:** the **`EngineNitro` usage** — a named state on the entity graph that already
> starts and stops a sound set and its effects, bound to a real fmod event in `vehicles.bank`
> (sound GUID `f74ea43b-…`, 202 objects / 172 vehicles, `EVTS` 249). It is the only vehicle usage that
> represents a *performance* state rather than an on/off or damage state, and it is the exact shape a
> `BattleMode` usage would take.
>
> **Gap:** (a) a `BattleMode` usage name + hash the graph dispatches on, (b) a battle event set to bind
> it to — the 24 media / 7 events of `BML_Battlemode` are the samples, (c) the flag that sets the usage,
> which no JC3 vehicle owns.

### Build composition (three legs, each independently revertible)

| leg | file | change | evidence |
|---|---|---|---|
| **A. flag** | the entity graph, one object | a `Usage` int set to a new `BattleMode` hash on the mode's state object, plus whatever sets it | **speculative**: the consumer must recognise the hash (U1) |
| **B. event set** | `vehicles.bank` (private copy) + the donor's graph | import the `BML_Battlemode` media (24 samples) / the `BML_Batmobile` battle events' samples into the bank's `EVTS`, bound to the new usage | decoded ids/media; sample-import route precedent = `bm_bank_manifest.json` card B-11, test-060 |
| **C. steering bed** | same bank + graph | the `Play_Batmobile_Steering_Bed` loop (event `3532435377`, 100-radius) as a vehicle loop under the usage | decoded row; loop start/stop semantics UNKNOWN (U2) |

**What the build can ship today, without the flag:** leg B's samples can be placed in the bank and the
`EngineNitro` usage can be duplicated to a second usage (`EngineNitro` → donor's 51-value usage map has
room; `USAGES.md`: 155-value `.epe` usage space, 12576 objects). That gives a *second* state the graph
can play, triggered by the **boost input** — the only performance state JC3 has. **Compromise:** the
battle engine would be heard while boosting, not while in a mode.

**What it cannot ship:** the entry/exit (`In_/Out_`) sets and the mode-level bed, because they need a
mode transition, not a held input.

---

## 5. The in-game check (once a flag exists or the boost proxy is used)

**Card sentence:**

> **Q-AU-MD14** — With the car at idle, enter the state (mode, or the boost proxy): the battle engine
> bed and the steering bed must both start within **0.20 s** and the pursuit engine loop must fall to
> **0 residual** in the same window; on exit the reverse must complete within **0.20 s**; three
> entries and three exits, all six inside the window.

0.20 s is the car's own `nitro_boost.boost_blend_time` (0.2, decoded), used as the only shipped blend
time for a state change; BmAK's transition time is not in any read file (U4).

**Control:** the same run with the usage value left at `EngineRunning` — the battle bed must not play,
proving the sound is bound to the usage and not to the mode code path.

**What a failure means:** no change → the usage hash is not recognised (A is dead, revert to the boost
proxy); a change but no steering bed → the loop's start/stop is on a different object (C is wrong);
residual pursuit engine → the two beds are additive and the pursuit one needs a stop action.

---

## 6. What T-16's W-08 says, re-tested

W-08: *the donor has no mode-switch event.* Re-tested from three angles:

1. **usage vocabulary** — 12 names, no mode/battle/stance/transform name (`USAGES.md`). **W-08 holds.**
2. **event list** — the donor's 51-value usage map and the 155-value `.epe` `Usage` space name only
   state/part/damage usages (`README.md` §usages). **W-08 holds.**
3. **module vocabulary** — `LandAudio` has **2 members** (`min_rpm`, `max_rpm`), both continuous; no
   event, no mode. **W-08 holds.**

So T-MD14 stays blocked on the flag, and the row's honest wording is: *battle audio needs a mode
usage, a second event set and a flag; JC3 has the usage mechanism (`EngineNitro`) and the samples
(`BML_Battlemode`, 24 media) but not the flag.*

---

## 7. Where the samples are, for a future build

| asset | count / id | source |
|---|---|---|
| `BML_Battlemode` media | 24 WEMs in 830,548 B, BKHD 112, export 37005 | `Engine.upk` |
| `BML_Battlemode` events | 7 HIRC (1 named: `Play_Batmobile_Steering_Bed`, `0xD28CAFB1`, wem 73608235) | `AUDIO_MAP.json` |
| `BML_Batmobile` battle events | 32 named (`In_*`, `Out_*`, `Rev` sets, engine bed, cool ticks, idles) | `AUDIO_MAP.json` |
| target bank | `vehicles.bank`, `EVTS` 249, GUID `f74ea43b-…`, 202 objects / 172 vehicles | `bm_bank_manifest.json` (B-11), `USAGES.md` |
| usage to clone | `EngineNitro` hash 4197885156, 18 vehicles, 307 objects | `README.md` §usages |

---

## 8. UNKNOWNs

| # | unknown | settler |
|---|---|---|
| U1 | does anything dispatch on a *new* `Usage` hash, or only on the 12 known names? | the `Usage` consumer in `JustCause3.exe` (not decoded); a one-variable probe |
| U2 | is `Play_Batmobile_Steering_Bed` a start/stop loop or a one-shot with a continuous parameter? | the event's HIRC action list (10 actions, 4 ranseq in the bank) — walk it with `grab_audio_banks.py`'s HIRC reader |
| U3 | does JC3 have a handbrake audio event at all? | `USAGES.md` 12 names: none; the `Tire`/`Brakes` modules carry no sound member; exe-side |
| U4 | BmAK's battle-mode transition time (In/Out blend) | no value in `AUDIO_MAP.json` or `MODES.md`; the In/Out events' own crossfade, readable from the bank's actions |
| U5 | the 6 unnamed events in `BML_Battlemode` | HIRC event ids → `AkEvent` objects in `BmGame.upk` |
| U6 | whether the mode flag can exist at all | `mode-switch-carriers.md` §5 (entity variant or boost proxy), §7 U1 |

---

## 9. Sources

- `Research/BatmobileGrab/AUDIO_MAP.json` — 361 rows, 118 unique event ids, 239 resolved, the
  `BML_Battlemode` bank row (7 events / 10 actions / 44 sounds / 4 ranseq / 24 media) and the
  `Play_Batmobile_Steering_Bed` row (id `3532435377`, outer `Ww_BML_Battlemode`, radius 100).
- `Research/BatmobileGrab/AUDIO_BANKS.md` — `BML_Battlemode` export 37005, 830,548 B,
  sha1 `83dc20e9be47a388`, BKHD 112, **7 HIRC**; `BML_Batmobile` export 37004, 53 HIRC.
- `Research/JC3Grab/USAGES.md`, `Research/JC3Grab/README.md` §usages — 12 usage names and counts,
  `EngineNitro` hash 4197885156 / 18 vehicles / 307 objects, the sound GUID `f74ea43b-…`,
  `vehicles.bank` `EVTS` 249, the empty `ExtendedEffectUsages` stub.
- `Research/JC3Grab/VOCABULARY.md` — `LandAudio` (2 members), `LandEngine` rpm curve, `Transmission`.
- `Working/Audio/bm_bank_manifest.json` — B-11 / `Tools/scripts/bm_audio.py`, vehicles bank sha256,
  route a+c, test-060 precedent.
- `tmp/freebuff/reports/mode-switch-carriers.md` — no mode flag; boost state / hinged part / entity
  variant as the only runtime switches.
- `Working/Translation/T_ROWS.jsonl` (T-MD14) and T-16's W-08 claim.

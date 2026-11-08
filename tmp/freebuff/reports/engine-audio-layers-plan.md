# BmAK engine layers → JC3 vehicle audio parameters

**STATUS: done (plan, read-only).** The BmAK engine bed decodes to **11 RPM-driven layers on the
MK1 car** and **9 on the MK2**, carried as per-HIRC-object `REV_RPM` curves, plus 5 non-RPM layers
(idle, distant rev, clutch, cool ticks, gearshift). JC3's car audio entity exposes the parameters
`rpm`, `rpm_norm`, `load`, `engine_load`, `engine_load_norm`, `engine_real_load`, `throttle`,
`gear`, `heat`, `Speed`, `distance_filter`, `doppler`, `engine_timeline`; its stock supercar
(`v0401_car_mugello_racingsupercar`) declares an audio RPM window of **500 … 6000 rpm**. **Six**
BmAK layer families have no existing `vehicles.bank` sample slot and still need a new bank entry;
**seven** can reuse a shipped slot.

Two limits are stated before any table, because they decide how the table may be read:

1. **Layer names are not stored.** A Wwise blend container's track names do not exist in the data
   this grab decodes. Each "layer" below is one HIRC object (id decoded) that carries an `REV_RPM`
   curve under an engine event; the name attached to it (`POS-mid-fall`, `ENG-Clutch`, …) is a
   functional label this report assigns from the curve's shape, not a Wwise name.
2. **The RTPC property (volume vs pitch) is not stored by the reader.** The curve points are
   decoded exactly; which property the y value drives is not. Two y-domains appear and are used as
   the discriminator: `−1 … +0.292` (dB-shaped → read as volume) and `±200` / `−1000 … −590`
   (cent-shaped → read as pitch). That assignment is **derived**, and is labelled as such.

Everything else is decoded from bytes and cited in §9.

---

## 1. Evidence base

| side | fact | source |
|---|---|---|
| BmAK | `engine` group = **44 rows / 18 distinct events / 130 WEMs**, 18/18 resolved | `Research/BatmobileGrab/AUDIO_FEATURES.md` §engine, §Feature groups |
| BmAK | **782 raw RTPC entries** = 106 distinct event × parameter pairs; 5 unresolved parameter hashes (`0x55C2A93B`, `0x7D530EF5`, `0xE5E768E2`, `0x7CF1B505`, `0x1DCD6409`) | `Research/BatmobileGrab/ENGINE_AUDIO_PAIRS.md` §3, §6 |
| BmAK | `REV_RPM` = `0x4624084A`, **37 objects / 62 entries**, the only RPM parameter in the engine group | `Research/BatmobileGrab/AUDIO_FEATURES.json` `rtpc_params` |
| BmAK | each entry carries the HIRC object it sits on, its `interpolation`, `curve_id` and points (x, y, curve_type) | `AUDIO_FEATURES.md` §Method and anchors; `Tools/scripts/bmak_audio_features.py` `rtpc_chain` |
| JC3 | car audio entity module `LandAudio` carries **exactly 2 members**, `min_rpm` and `max_rpm` | `Research/JC3Grab/JC3_AUDIO.md` §4; `JC3_AUDIO_EVENTS.json` `land_audio.members` |
| JC3 | `vehicles` bank names **49** parameters, incl. `rpm`, `rpm_norm`, `load`, `engine_load`, `engine_load_norm`, `engine_real_load`, `throttle`, `gear`, `heat`, `Speed`, `distance_filter`, `doppler`, `engine_timeline` | `JC3_AUDIO_EVENTS.json` `banks.vehicles.param_names` (read in this session) |
| JC3 | **0 decoded event → parameter edges**; the `PMLS` lists exist but the edge is not resolved | `JC3_AUDIO.md` §4 |
| JC3 | engine-role event `engine_running_sound`, GUID `905be2e5-2544-8045-a10b-6034fd27ff11`, `vehicles/146`, tune `vehicles/5` | `JC3_AUDIO.md` §3 |
| JC3 | gear-role event `GearChange`, GUID `3e448c6d-61c1-5844-867d-06d741b7dd24`, `vehicles/66`, tune `vehicles/87` | `JC3_AUDIO.md` §3 |
| JC3 | **tune → wave is not stored** (0 / 649 wave GUIDs in any tune or instance), so which sample a layer would swap is name-only | `JC3_AUDIO.md` §5 |

### 1.1 The stock supercar, decoded for this report

`v0401_car_mugello_racingsupercar` is JC3's racing supercar. Its two audio-relevant modules were
decoded here with the project's own ADF reader (`Tools/Gibbed/Gibbed.JustCause3.ConvertAdf.exe`):

| module | member | value |
|---|---|---:|
| `v0401_..._land_audio.vmodc` | `min_rpm` | **500.0** |
| `v0401_..._land_audio.vmodc` | `max_rpm` | **6000.0** |
| `v0401_..._land_engine.vmodc` | `min_rpm` / `optimal_rpm` / `max_rpm` | **1000 / 5500 / 8250** |

So on the stock supercar the audio RPM window (500–6000) is **narrower than and offset from** the
mechanical band (1000–8250): audio `0.0` sits 500 rpm below idle, and audio `1.0` is 2250 rpm below
the mechanical limiter. That is the window every "rpm" number in §3 must be read against.

For comparison, the other two windows this project already carries:

| car | `land_audio.min_rpm` | `land_audio.max_rpm` | source |
|---|---:|---:|---|
| stock supercar `v0401` | 500 | 6000 | decoded this report |
| donor sports-muscle `v0300` | 1000 | 10000 | `JC3_AUDIO.md` §4 |
| **built Batmobile** (`bm-RC3`) | 1000 | 4500 | decoded this report (`.../batmobile/..._land_audio.vmodc`) |

The built car's `land_engine` band is 800 / 2800 / 4500 (also decoded in `bm-RC3`), so its audio
window's top (4500) coincides with its mechanical limiter — unlike the supercar.

---

## 2. RPM conversion rule (derived)

`REV_RPM` is normalised `0 … 1` on every BmAK bind (x range 0..1 on all 37 objects). The JC3
`LandAudio` window is linear in the same way, so the bridge used below is

```
rpm = min_rpm + x · (max_rpm − min_rpm)
```

with `min/max` taken from the car's own `land_audio` module. The table gives both the built car
(1000–4500) and the stock supercar (500–6000):

| `REV_RPM` x | built Batmobile rpm | stock supercar rpm | appears in |
|---:|---:|---:|---|
| 0.000 | 1000 | 500 | every layer |
| 0.010 | 1035 | 555 | mid-fall, rev-ramp |
| 0.01874 | 1066 | 603 | cool ticks |
| 0.050 | 1175 | 775 | rev-ramp, MK2 fade-in |
| 0.102146 | 1358 | 1062 | sub-idle band |
| 0.150 | 1525 | 1325 | low-rise band |
| 0.200 | 1700 | 1600 | sub-idle top |
| 0.30128 | 2055 | 2157 | cool ticks off |
| 0.420 | 2470 | 2810 | mid-fall saturation |
| 0.500 | 2750 | 3250 | low-mid pitch peak |
| 0.50134 | 2755 | 3257 | low-mid band off |
| 1.000 | 4500 | 6000 | every full-band layer |

This mapping is a **derivation**: no file states that JC3's `rpm`/`rpm_norm` parameter is the
same quantity BmAK's `REV_RPM` carries (`ENGINE_AUDIO_PAIRS.md` §6). It is the only bridge the
two decoded windows support, and it is applied identically everywhere below.

---

## 3. The layer table

### 3.1 MK1 RPM-driven bed — `Play_Batmobile_Positional` (55 WEMs, 2 packages)

Each row is one HIRC object with its own `REV_RPM` curve. "Band" is the x-range in which the
volume curve has left its flat tail (derived by linear interpolation of the decoded points).

| layer (label) | HIRC object | RPM band (x) | built rpm | supercar rpm | pitch curve | volume curve |
|---|---|---|---:|---:|---|---|
| `POS-low-rise` | `0x0CD78D96` | 0 … 0.150 | 1000–1525 | 500–1325 | `0 → −200 c`, `0.15 → +200 c`, `1 → 0 c` | `0 → 0 dB`, `0.15 → −1 dB` |
| `POS-subidle` | `0x07EB1DD5` | 0 … 0.200 | 1000–1700 | 500–1600 | none decoded | `0 → 0 dB`, `0.102 → 0 dB`, `0.2 → −1 dB` |
| `POS-lowmid-rise` | `0x3A0D204A` | 0 … 0.501 | 1000–2755 | 500–3257 | `0 → −200 c`, `0.5 → +200 c`, `1 → 0 c` | `0 → 0 dB`, `0.501 → −1 dB` |
| `POS-mid-fall-a` | `0x0957744B` | 0 … 0.420 | 1000–2470 | 500–2810 | `0 → −1000 c`, `0.42 → −590 c`, flat | `0 → −1 dB`, `0.01 → −0.292 dB`, `0.42 → 0 dB` |
| `POS-mid-fall-b` | `0x3AF68860` | 0 … 0.420 | 1000–2470 | 500–2810 | `0 → −1000 c`, `0.42 → −590 c`, flat | `0 → −1 dB`, `0.01 → −0.292 dB`, `0.42 → 0 dB` |
| `POS-rev-ramp` | `0x1B1B61BA` | 0 … 0.050 | 1000–1175 | 500–775 | none decoded | `0 → −0.499 dB`, `0.05 → 0 dB` |
| `POS-full-a` | `0x0F6D0436` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `POS-full-b` | `0x24BBEB6A` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `POS-full-c` | `0x283947BD` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `POS-full-d` | `0x28EA34AB` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.121 dB` |
| `POS-full-e` | `0x2A40610D` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.109 dB` |

Reading: the bed is **3 band-limited layers + 1 ramp + 2 pitch-fall mid layers + 5 full-range
gain layers**. Only two of the eleven carry a cent-domain curve, and both of those pitch *down*
(`−1000 c` → `−590 c` = −10 to −5.9 semitones) once rpm passes ≈2810 (supercar). The three
band-limited layers hand over at ≈1325, ≈1600 and ≈2810 rpm (supercar), i.e. the crossfade
structure sits in the bottom half of the window.

### 3.2 MK2 RPM-driven bed — `Play_Batmobile_MK2_Positional` (43 WEMs)

Same five curve shapes at different object ids; the MK2 bed has **no** separate `POS-rev-ramp`,
`POS-full-a` or `POS-full-c` object, and folds the ramp and the +0.292 gain onto one id:

| layer (label) | HIRC object | RPM band (x) | built rpm | supercar rpm | pitch curve | volume curve |
|---|---|---|---:|---:|---|---|
| `MK2-low-rise` | `0x32D306A0` | 0 … 0.150 | 1000–1525 | 500–1325 | `0 → −200 c`, `0.15 → +200 c`, `1 → 0 c` | `0 → 0 dB`, `0.15 → −1 dB` |
| `MK2-subidle` | `0x369B46A5` | 0 … 0.200 | 1000–1700 | 500–1600 | none decoded | `0 → 0 dB`, `0.102 → 0 dB`, `0.2 → −1 dB` |
| `MK2-lowmid-rise` | `0x14C20D80` | 0 … 0.501 | 1000–2755 | 500–3257 | `0 → −200 c`, `0.5 → +200 c`, `1 → 0 c` | `0 → 0 dB`, `0.501 → −1 dB` |
| `MK2-ramp-full` | `0x0EC0B41B` | full 0 … 1 | 1000–4500 | 500–6000 | none decoded | `0 → −0.499 dB`, `0.05 → 0 dB` (second curve on the same id: `0 → +0.292 dB`) |
| `MK2-full-a` | `0x08DE0810` | full | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `MK2-full-b` | `0x1AAB2C90` | full | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `MK2-full-c` | `0x24118758` | full | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `MK2-full-d` | `0x2E783608` | full | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.292 dB` |
| `MK2-full-e` | `0x22838733` | full | 1000–4500 | 500–6000 | none decoded | `0 → 0 dB`, `1 → +0.121 dB` |

### 3.3 Reverse overlay — `Play_Batmobile_Reverse` (72 WEMs) / `MK2_Reverse` (21 WEMs)

| layer (label) | HIRC object | RPM band (x) | supercar rpm | pitch curve | volume curve |
|---|---|---|---:|---|---|
| `REV-bed` | `0x07EB1DD5`, `0x0957744B`, `0x0CD78D96`, `0x0F6D0436`, `0x24BBEB6A`, `0x283947BD`, `0x28EA34AB`, `0x2A40610D`, `0x3A0D204A`, `0x3AF68860` | full | 500–6000 | as §3.1 per object | as §3.1 per object |
| `REV-ramp` | `0x1B1B61BA` | 0 … 0.05 | 500–775 | none | `0 → −0.499 dB`, `0.05 → 0 dB` |
| `REV-MK2` | `0x0957744B`, `0x3AF68860` | 0 … 0.42 | 500–2810 | `0 → −1000 c`, `0.42 → −590 c` | `0 → −1 dB`, `0.01 → −0.292 dB`, `0.42 → 0 dB` |

The reverse bed is the positional bed plus a 0–775 rpm entry ramp; there is **no reverse-specific
sample slot in JC3** (§6.3).

### 3.4 Non-RPM layers

| layer (label) | event | bank | RPM range | pitch curve | volume / other curve |
|---|---|---|---|---|---|
| `IDLE` | `Play_Batmobile_Idle` (5 WEMs) | `BML_Engine` | no `REV_RPM` bind → full, effectively idle | none | none (event has 0 RTPC) |
| `MK2-IDLE` | `Play_Batmobile_MK2_Idle` (5 WEMs) | `Vw_VEH_Batmobile_MK2_Engine` | full | none | none |
| `PERSIST-IDLE` | `Play_BML_Persistent_idles` (2 WEMs) | `BML_Batmobile` | full | none | `Startup: 0 → 0`, `1 → −1` |
| `CLUTCH` | `Play_Batmobile_Clutch` (5 WEMs) | `BML_Engine` | full (`0 → +0.292 dB` with rpm) | none | `REV_RPM 0 → 0`, `1 → +0.292 dB`; `Occlusion 0 → 0`, `0.5 → 0`, `1 → +15`; `0x7D530EF5 0 → 1`, `0.5 → 0` |
| `MK2-CLUTCH` | `Play_Batmobile_MK2_Clutch` (5 WEMs) | MK2 bank | full | none | same `REV_RPM` / `Occlusion` shape |
| `COOLTICKS` | `Play_BML_EngineCoolTicks` (22 WEMs) | `BML_Batmobile` | **0 … 0.301** (1000–2055 built / 500–2157 supercar) | none | `REV_RPM 0 → 0`, `0.01874 → +0.0228`, `0.30128 → −1` |
| `ROTATION` | `Play_Batmobile_Rotation` (22 WEMs) | `BML_Engine` | 0 … 0.301 | none | same as `COOLTICKS` |
| `DISTANT-REV` | `Play_Batmobile_DistantRev` (5 WEMs) / `MK2` (5) | `BML_Engine` / MK2 | full (no `REV_RPM`) | none | `Occlusion 0 → 0`, `1 → +30`; `0xE5E768E2 0 → −1`, `30 → −1`, `50 → 0`, `1000 → 0` |
| `GEARSHIFT` | `Play_Batmobile_GearShift_Up` (5 WEMs) | `BML_Batmobile` | one-shot, no rpm bind | none | `0x7D530EF5 0 → 1`, `0.5 → 0` |
| `TRANSITION-IN` | `Play_Batmobile_Engine_Transition_In` (53 WEMs) | `BML_Engine` | full; `REV_RPM` 10 variants, `Startup` gates | as §3.1 | `Startup 0 → −1`, `1 → 0`; `Speed 0 → 0`, `3.52 → 0`, `5.17 → −0.215`, `7.0 → −1` |
| `TRANSITION-OUT` | `Play_Batmobile_Engine_Transition_Out` (53 WEMs) | `BML_Engine` | as in | as §3.1 | as in, plus `Occlusion 0 → 0`, `0.25 → +0.645`, `1 → +0.749` |

| layer (label) | event | RPM value domain | pitch curve | volume curve |
|---|---|---|---|---|
| `BATTLE-ENGINE` | `Play_BattlemodeEngine` (3 WEMs) | `RPM_BattleMode_Shepherd: 500 → −500`, `2000 → +500`, `4000 → +500` (absolute rpm, not normalised) | none decoded | `Speed: 0 → −0.292`, `3 → 0`, `20 → 0`, `30 → −0.499`, `100 → −1` |

`BATTLE-ENGINE` is the **only** layer in the group whose RPM curve is in absolute rpm (500–4000),
which is why it is listed separately: it cannot be converted with the §2 rule.

---

## 4. Matching each layer to the JC3 parameters a car exposes

The donor side decodes **parameter names**, not edges. JC3's per-event parameter bindings are
UNKNOWN (`JC3_AUDIO.md` §4), so the column "JC3 parameter" is a *match by name and role*, never a
proven bind. The class vocabulary is the one `ENGINE_AUDIO_PAIRS.md` already uses
(`same-role` / `plausible-by-name only` / `no counterpart`).

| BmAK layer family | JC3 parameter that would drive it | class | stock supercar value beside it |
|---|---|---|---|
| `POS-*`, `MK2-*` rpm bands | `rpm`, `rpm_norm` | **plausible-by-name only** (`REV_RPM` / `rpm`) | audio window **500 … 6000 rpm**; band edges at **1325 / 1600 / 2810 / 3250 rpm** |
| `POS-full-a … e` gain ramps | `load`, `engine_load`, `engine_load_norm`, `engine_real_load` | **plausible-by-name only** (no decoded load curve on the BmAK side — the gain ramps are `REV_RPM`-driven) | no load member on `LandAudio`; load exists only as a bank parameter name (49-name list) |
| `CLUTCH`, `MK2-CLUTCH`, `TRANSITION-*` ramp | `throttle` | **plausible-by-name only** (`REV_Throttle` / `throttle`) | `REV_Throttle` is `0 … 1` on the BmAK side; supercar has no throttle member in `LandAudio` |
| `GEARSHIFT` | `gear` | **plausible-by-name only** (BmAK event `GearShift_Up`, donor event `GearChange`) | supercar gearshift samples: 4 slots, §6.3 |
| `COOLTICKS`, `ROTATION` | `heat` | **plausible-by-name only** (`EngineHeat` / `heat`) | `EngineHeat 0 → −1`, `0.349 → −0.0008`, `1 → −0.529` on the BmAK side |
| `TRANSITION-IN/OUT`, `REV-bed` | `Speed` | **same-role** (verbatim name in the `vehicles` bank) | `Speed 0 → 0`, `3.52 → 0`, `5.17 → −0.215`, `7.0 → −1`, `100 → −1` (m/s domain on BmAK) |
| `DISTANT-REV` | `distance_filter`, `doppler`, `Distance` | **plausible-by-name only** | `Occlusion 0 → 0`, `1 → +30`; no distance/occlusion member in `LandAudio` |
| `IDLE`, `PERSIST-IDLE`, `TRANSITION-*` startup gate | `engine_timeline`, `timeline` | **plausible-by-name only** (`Startup` gate) | `Startup 0 → 0/−1`, `1 → −1/0` per event |
| `BATTLE-ENGINE` | `rpm` (absolute 500–4000) | **no counterpart** (JC3 has no battle-mode event: AUD-4 deferred with D-2) | — |
| `REV-bed` reverse | `rpm` + direction (no JC3 parameter name for direction) | **no counterpart** for direction | no reverse engine slot in `vehicles.bank`; only `jc3_veh_reverse_warning*` (beeps) and `jc3_veh_transmission_whine_reverse_03` |

**10 of 18 engine events carry `Speed`** (the 10 `same-role` binds counted in
`ENGINE_AUDIO_PAIRS.md`), so `Speed` is the only parameter this project can call same-role. Every
rpm/load/throttle match is name-only; that is the honest ceiling of the current evidence.

---

## 5. The layer table as one line per JC3 driver

For a build, the 20 rpm-driven layers collapse onto the parameters JC3 actually exposes:

| JC3 driver | layers it must carry | rpm span (supercar window) |
|---|---|---|
| `rpm` / `rpm_norm` | `POS-low-rise`, `POS-subidle`, `POS-lowmid-rise`, `POS-mid-fall-a/b`, `POS-full-a…e` (MK1) / the 9 MK2 ids | 500 → 6000, with handovers at 1325 / 1600 / 2810 / 3250 |
| `throttle` | `CLUTCH`, `MK2-CLUTCH`, `TRANSITION-IN/OUT` ramp | full |
| `load` | the five full-range gain layers (they are the only "more rpm → more level" curves) | 500 → 6000 |
| `heat` | `COOLTICKS`, `ROTATION` | 500 → 2157 then off |
| `gear` | `GEARSHIFT` | one-shot |
| `Speed` | `TRANSITION-IN/OUT`, `REV-bed` | — |
| `distance_filter` | `DISTANT-REV` | full |
| `engine_timeline` | `IDLE`, `PERSIST-IDLE`, `TRANSITION-*` startup gate | — |

---

## 6. Which BmAK layers still need a new sound bank entry

Ground rules decoded from `JC3_AUDIO.md`:

* the bank is FMod **Designer/Ex FEV v56**; the event graph **cannot be authored** (route b: no) —
  the only proven write is an **in-place FSB5 payload swap** (route a, test-060);
* `vehicles.bank` holds **649 samples**; adding a *new* sample slot means rebuilding the FSB5
  container. **No FSB5 authoring tool exists under `Tools/scripts/`** (the `fsb5` imports in
  `bm_audio.py`, `_apply_audio.py`, `v04_audio.py` are read/decode paths, not writers). So a "new
  bank entry" is **blocked** today and named as such.

### 6.1 Existing `vehicles.bank` slots that can already receive a layer

Decoded sample list (`JC3_AUDIO_EVENTS.json` `samples.list`), all 48 kHz mono PCM:

| slot index | sample name | frames | would carry |
|---:|---|---:|---|
| 127 | `aston_martin_vantage_engine_rpm_idle_high` | 113,272 | `IDLE` (high-idle variant) |
| 619 | `aston_martin_vantage_engine_rpm_idle2` | 119,392 | `IDLE` |
| 601 | `aston_martin_vantage_engine_rpm_low2` | 111,710 | `POS-subidle` |
| 390 | `aston_martin_vantage_engine_rpm_medium_low` | 98,882 | `POS-low-rise` |
| 636 | `aston_martin_vantage_engine_rpm_medium_high2` | 98,694 | `POS-lowmid-rise` |
| 236 | `aston_martin_vantage_engine_rpm_high` | 94,376 | `POS-full-*` top |
| 177 / 181 / 208 / 490 / 503 / 564 / 597 / 637 | `aston_martin_vantage_exhaust_rpm_{very_high, high, medium_low, idle2, low2, medium_high2, idle_high, very_high}` | 93,638–119,392 | the exhaust doubles of the same bands |
| 295 / 150 | `aston_martin_vantage_engine_start` / `_shutdown` | 221,761 / 125,001 | `TRANSITION-IN` / `TRANSITION-OUT` |
| 498 | `jc3_veh_ferrari_275_engine_whir_loop` | 102,994 | `PERSIST-IDLE` |
| 546 | `olds_3000rpm_full_intake_lp` | 305,152 | `PERSIST-IDLE` (long bed) |
| 229 / 514 / 560 / 588 | `jc3_veh_generic_gear_shift_supercar_01…04` | 5,161–8,138 | `GEARSHIFT` |

These nine families mean **no new bank entry is needed** for: IDLE, PERSIST-IDLE, the three
band-limited RPM layers, the five full-range gain layers (they ride the same six engine slots),
TRANSITION-IN/OUT, GEARSHIFT.

### 6.2 Layers that still need a new bank entry

| layer | why no shipped slot covers it | verdict |
|---|---|---|
| `POS-mid-fall-a`, `POS-mid-fall-b` (**and MK2 twins** `0x0957744B`/`0x3AF68860`) | the only cent-domain curves in the bed (pitch −1000 → −590 c). JC3 ships **no sample with a pitch-fall authored over rpm**, and the baked sample can only be swapped, not re-pitched by the bank | **NEEDS NEW ENTRY** (or an engine-side pitch curve, which is not decoded) |
| `POS-low-rise`, `POS-lowmid-rise` pitch halves | their `−200 → +200 c` curves have no counterpart slot: a swapped static sample cannot carry the bend | **NEEDS NEW ENTRY** for the bend; the gain half can reuse 390/636 |
| `REV-bed` + `REV-ramp` | no reverse engine loop exists in `vehicles.bank` — only beeps and a gearbox whine | **NEEDS NEW ENTRY** |
| `CLUTCH`, `MK2-CLUTCH` | no clutch/engage sample anywhere in the 649 (nearest names are gear-shift one-shots) | **NEEDS NEW ENTRY** |
| `COOLTICKS`, `ROTATION` | no tick/creak loop with a 0–2157 rpm gate; `jc3_veh_lave_chassis_spin_creaks_loop_fast` (279) is a chassis loop, already used for A-05 | **NEEDS NEW ENTRY** |
| `DISTANT-REV` | `distance_filter` exists as a parameter but there is no distant-rev sample to filter | **NEEDS NEW ENTRY** (unless `distance_filter` is proven to gate a shipped slot — edge UNKNOWN) |
| `BATTLE-ENGINE` | JC3 has no battle-mode event at all (AUD-4 deferred) | **NEEDS NEW ENTRY** (deferred with D-2) |

Count: **6 mandatory new entries** (`mid-fall` ×2 voices counted once per family, `low/lowmid`
pitch bends, `REV`, `CLUTCH`, `COOLTICKS`/`ROTATION`, `BATTLE-ENGINE`) **+ 1 conditional**
(`DISTANT-REV`). The two pitch families share one requirement — a *pitched* layer — so a build
that authors one pitch-capable entry satisfies both.

### 6.3 Where the new entries would have to go, and why they are blocked

| route | possible? | evidence |
|---|---|---|
| swap a payload in place (proven) | yes, size- and frame-locked | `MODLOG` §71, `Tools/scripts/_apply_audio.py`; V-04's five slots all ship as `mono/48 kHz/PCM16` |
| add a sample to the FSB5 (new entry) | **blocked: no writer** | no FSB5 authoring code under `Tools/scripts/`; `v04_audio.py` / `bm_audio.py` decode only |
| new event in the FEV graph | **no** | `JC3_AUDIO.md` §10 route b: events/tunes live in the FEV graph, no `.fev` project ships |
| new `.bnk` listed in `master.banklist` | loader can be told about another file (26-line text list, 434 B), but nothing here can author its contents | `JC3_AUDIO.md` §10 |

So the six mandatory layers are **plan-only**: they need either an FSB5 rebuild tool (none in the
repo) or a re-authored FEV graph (no project file). Until one exists, a build can only cover them
by reusing a shipped slot and accepting that the pitch bend, the reverse bed, the clutch, the ticks
and the battle mode will be wrong or silent.

---

## 7. Stock supercar reference beside the Batmobile plan

| what | stock supercar `v0401` | built Batmobile `bm-RC3` | consequence for the layer table |
|---|---|---|---|
| audio `min_rpm` | 500 | 1000 | same `REV_RPM` x lands 500 rpm higher on the Batmobile |
| audio `max_rpm` | 6000 | 4500 | the whole 500–6000 window compresses into 1000–4500 |
| band-edge `POS-subidle` (x 0.20) | 1600 rpm | 1700 rpm | crossfade moves +100 rpm |
| band-edge `POS-mid-fall` (x 0.42) | 2810 rpm | 2470 rpm | pitch-fall saturates 340 rpm earlier |
| band-edge `POS-lowmid-rise` (x 0.501) | 3257 rpm | 2755 rpm | top handover 502 rpm earlier |
| engine mechanical band | 1000 / 5500 / 8250 | 800 / 2800 / 4500 | audio top = limiter on the Batmobile, 2250 rpm below it on the supercar |

The stock supercar's audio window therefore sits **lower and wider relative to its engine** than
the built car's: its six Vantage engine slots (idle → high) cover 500–6000, while the Batmobile's
audio only spans 1000–4500. If the layers are matched by rpm value (not by fraction), the
`POS-mid-fall` pitch drop should land at 2810 rpm, i.e. x = 0.5168 of the built window — not 0.42.

---

## 8. What this plan does not claim

* No layer name, pitch value or volume value is presented as a Wwise-authored number. The names
  are labels; the curves are decoded points; the property split (volume vs pitch) is by y-domain.
* No JC3 event reads a parameter in this document. The parameter column is a name/role match
  against the 49-name `vehicles` bank namespace.
* No sample-to-event edge is claimed: `JC3_AUDIO.md` §5 proves tune → wave is not stored, so the
  §6.1 slots are "the samples whose names fit", not "the samples `engine_running_sound` plays".
* No new bank entry is written or proposed as authored bytes: §6.3 shows the write path does not
  exist in this repo.

## 9. Checks run

| check | result |
|---|---|
| engine group row/event/WEM counts re-read from `AUDIO_FEATURES.json` | 44 / 18 / 130 — matches `AUDIO_FEATURES.md` |
| every `REV_RPM` pair carries an object id; every curve's x within 0…1 | PASS (106 pairs; 37 objects) |
| no engine event without a donor part in `ENGINE_AUDIO_PAIRS.md` | PASS (18/18 paired) |
| supercar `land_audio` decoded with the project ADF reader | `min_rpm` 500, `max_rpm` 6000 |
| supercar `land_engine` decoded | 1000 / 5500 / 8250 |
| built `bm-RC3` `land_audio` / `land_engine` decoded | 1000 / 4500 and 800 / 2800 / 4500 |
| §2 rpm arithmetic reproduced | `rpm = min + x·(max−min)` at 11 x-values, both windows |
| sample slots quoted from the bank record | 20 Vantage/gearshift names + frames, read from `JC3_AUDIO_EVENTS.json` |
| new-entry count | 6 mandatory + 1 conditional, each traced to a missing slot in §6.1 |

## 10. Change record (per `AGENTS.md`)

1. **Intended change:** add one new report that tabulates the BmAK engine layers and matches them
   to JC3's car-audio parameters and the stock supercar's values.
2. **File:** `tmp/freebuff/reports/engine-audio-layers-plan.md` (this file). It is the correct
   file because every other audio report in this repo lives under `tmp/freebuff/reports/` and
   this card asks for exactly that path; no generated `Research/` artefact is touched.
3. **Why no other file was edited:** the layer data already exists in
   `AUDIO_FEATURES.json` / `ENGINE_AUDIO_PAIRS.md`; regenerating them would change checked
   byte-for-byte files for no new decode.
4. **Revert:** delete this file. Nothing else changed; no bank, build, manifest, module, ledger or
   install was written.

## 11. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | which RTPC property each BmAK curve drives (volume vs pitch vs LPF) | decode the parent HIRC object's AkPropID list / the blend track's property field; `bmak_audio_features.py` records the points only |
| U-2 | the authored blend-track order and per-track pitch of the engine container | the HIRC `CAkBlendContainer` track bodies, not decoded by this toolkit |
| U-3 | whether JC3's `rpm`/`rpm_norm` is the same quantity as `REV_RPM`, and its scale | `PMLS`/`MPGS` event→parameter edges — `JC3_AUDIO.md` §4 says the reader cannot resolve them |
| U-4 | which sample each `engine_running_sound` tune plays | tune → wave is not stored (`JC3_AUDIO.md` §5); needs audition or a Wwise/FMOD re-export |
| U-5 | whether `distance_filter` gates any shipped slot (decides the `DISTANT-REV` verdict) | the same `PMLS` edge, or an in-game probe |
| U-6 | whether a pitched sample can be realised at all without an FEV rebuild | an FSB5 writer (none in `Tools/scripts/`) or a re-exported `vehicles.bank` |
| U-7 | the meaning of the 5 unresolved BmAK hashes (`0x55C2A93B`, `0x7D530EF5`, `0xE5E768E2`, `0x7CF1B505`, `0x1DCD6409`) | the BmAK RTPC definition table, not these banks |
| U-8 | whether `0x7D530EF5` (0 → 1, 0.5 → 0) is the "engine running" gate that would carry `IDLE` | U-7 |

No game process was started; no install, dropzone, bank, build or ledger was written. All values
above are static decodes or derivations with their arithmetic shown.

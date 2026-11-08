# Horn and siren — BmAK has no horn; the alert is a weapon-warning AkEvent, and JC3's horn is one attached-effect GUID with 25 decoded samples

**STATUS: done (plan, read-only probe).** The headline finding is a negative one, and it is proven three
ways: **BmAK's Batmobile has no horn sound and no horn input.** `AUDIO_MAP.json` holds 361 event rows and the
string `horn` does not occur in it once; `AUDIO_FEATURES.md` ships a `horn` feature group with **0 rows /
0 events / 0 WEMs**; and `BINDINGS_KEYBOARD.json` has **no key whose name contains `horn`**. `JC3_AUDIO.md`
§8/§9 had already reached the same conclusion from the other side (AUD-7: *"BmAK has no horn event at all …
AUD-7 says remove it"*). What BmAK *does* have is a **per-attacker weapon-warning sound** carried as an
`AkEvent` inside `FBatmobileWeaponWarningContainer`, plus the banked one-shot `Play_HUD_fail`
(`0xDEAD7680`), plus pursuit/battle-mode transformation stingers. The JC3 side carries the horn as an
**`SAttachedEffect` named `horn`** — donor GUID `fd69c63c-84e6-fa43-b067-7eae99a59ce1`, bank `vehicles`,
EVTS ordinal 255, tune `vehicles/122` — with **178 objects in 178 of 232 vehicles, 19 distinct GUIDs**, and
**25 named horn/siren samples** whose loop points are decoded below to the frame, because loop timing was asked
for and the samples are the only place it exists.

Where a value is not in the files this says **UNKNOWN**. Nothing below is invented, and no audio file, bank,
module or build was written.

---

## 1. BmAK: the horn does not exist (three independent proofs)

| probe | command / file | result |
|---|---|---|
| event-name search | `grep -niE "horn\|siren\|klaxon" Research/BatmobileGrab/AUDIO_MAP.json` | **0 matches** in 361 rows |
| feature census | `Research/BatmobileGrab/AUDIO_FEATURES.md` §Feature groups | group `horn`: rows **0**, events **0**, WEMs **0**, RTPC `-`, containers `-` — and its table header is the only content |
| input binding | `grep -oiE "\"[^\"]*horn[^\"]*\"" Research/BatmobileGrab/BINDINGS_KEYBOARD.json` | **0 matches** |
| prior verdict | `Research/JC3Grab/JC3_AUDIO.md:205-212` (§8), `:228` (AUD-7) | *"BmAK has no horn event at all"*; AUD-7 = remove the JC3 horn |

`AUDIO_FEATURES.md` also lists `winch` and `emp` as empty groups, so the zero is a real group with no rows, not
a missing bucket. The 361 rows are partitioned into 14 groups and `horn` is one of them; it stays empty.

**Consequence for "loop timing":** there is no BmAK horn loop to time. This is UNKNOWN **by absence**, not by a
failed decode — a press-and-hold horn has no duration, no fade and no loop point in the files because there is
no event at all. Any figure quoted for a BmAK horn loop would be fabricated.

---

## 2. BmAK: the alert sound that *does* exist

### 2.1 The weapon-warning event

`Working/vendor/BmSDK/RVehicleBatmobileBase.g.cs`:

| member | offset / line | meaning |
|---|---|---|
| `FBatmobileWeaponWarningContainer` | struct size **32 B**, `:4186-4240` | one warning per attacking actor |
| `…AttackingActor` | +0 | who is shooting |
| `…StillRelevant` | bit +8.0 | warning still live |
| `…WeaponWarning` | `TArray<FBatmobileWeaponWarning>` +12 | the per-weapon entries |
| `…VisibleInPursuitMode` | bit +28.0 | show in pursuit mode |
| `…bOnlyShowIfCloseToBatmobile` | bit +28.1 | distance gate |
| **`FBatmobileWeaponWarning.AudioEvent`** | **+8** (`:3908-3918`) | **the alert sound, a `BmSDK.Engine.AkEvent`** |
| `AddWeaponWarning(out …NewWarning, bool ProhibitPursuitModeWarnings)` | `:3124-3139` | creates a warning |
| `TickWeaponWarnings(float DeltaTime)` | `:3105-3109` | per-frame refresh — where the event is fired |

So the Batmobile's "alert" is **not a siren**: it is an `AkEvent` attached to each weapon-warning record,
played from a warning tick when a new attacker appears. `FBatmobileWeaponWarning` is 56 B (`:4238-4241`) and
carries `AttackType` (`EWeaponWarningAttackType : byte`, `:4273-4319`), so the sound can vary per attack type —
but which event each type binds is a CDO value and is **UNKNOWN**.

### 2.2 The banked one-shot

| field | value |
|---|---|
| event | `Play_HUD_fail` |
| id | **`0xDEAD7680`** (3735910016) |
| bank ref | `Engine.CHR_BatmanAlerts`, outer `Ww_CHR_BatmanAlerts` |
| rows | 3 (BatmobileFunhouse / MK2 / base SF packages) |
| bank present? | **yes** — `AkBank` export 131401 in `BmGame` and 7457 in `StartupPatch`, **97,708 B**, **6 events** (`AUDIO_BANKS.md`) |
| status in `AUDIO_MAP.json` | `missing-bank` — but that flag came from scanning only 3 packages; `AUDIO_BANKS.md` §"The 10 missing banks, re-tested" resolves it as **FOUND** |

### 2.3 Mode-change stingers (audible alerts, one-shot)

| member | offset | line |
|---|---:|---|
| `RVehicleBatmobileBase.TransformationReverseDirectionIntoPursuitModeSound` | 4828 | `:5516-5518` |
| `…TransformationReverseDirectionIntoBattleModeSound` | 4836 | `:5525-5527` |
| `…Transform_In_Bed` | 4844 | `:5534` |
| `RVehicle.StartElectricalOverloadEvent` / `…2` | 2228 / 2236 | `:3865-3876` |

None has a loop or a period; each is a single `AkEvent` fired on a state change.

---

## 3. BmAK: the lights (state, not timing)

### 3.1 The two enums

`RVehicle.g.cs:2962-2990`:

| `VehicleLightMaterialType` (`:byte`) | # | `VehicleLightType` (`:byte`) | # |
|---|---:|---|---:|
| `VEHLTMAT_None` | 0 | `VEHLT_Other` | 0 |
| `VEHLTMAT_HeadLightLeft` | 1 | `VEHLT_Hacked` | 1 |
| `VEHLTMAT_Interior` | 2 | `VEHLT_NotHacked` | 2 |
| `VEHLTMAT_HeadLightRight` | 3 | `VEHLT_HeadLight` | 3 |
| `VEHLTMAT_TailLightLeft` | 4 | `VEHLT_TailLight` | 4 |
| `VEHLTMAT_TailLightRight` | 5 | `VEHLT_Interior` | 5 |
| `VEHLTMAT_Special1` | 6 | **`VEHLT_BattleModeLight`** | 6 |
| `VEHLTMAT_Special2` | 7 | `VEHLT_ForensicsLight` | 7 |
| `VEHLTMAT_Special3` | 8 | `VEHLT_RoofLight` | 8 |
| `VEHLTMAT_MAX` | 9 | `VEHLT_BootLight` | 9 |
| | | `VEHLT_CustomLightCommanderTankWeakPoint` | 10 |
| | | `VEHLT_LightTankDamaged` | 11 |
| | | `VEHLT_MAX` | 12 |

Two lights are the Batmobile's signature: `VEHLTMAT_HeadLightLeft/Right` (1/3) for the front, and
`VEHLT_BattleModeLight` (6) for the mode-switch state.

### 3.2 The members

| member | class / offset | line |
|---|---|---|
| `HeadlightsOn()` / `HeadlightsOff()` | `RVehicle` functions | `RVehicle.g.cs:1297-1312` |
| `…HeadlightsOff()` override | `RVehicleBatmobile` | `RVehicleBatmobile.g.cs:620-624` |
| `HeadlightsSwitchedOn` | `RVehicle` bool 3665 | `:3665-3667` |
| `ForceHeadlightsSwitchedOn` | `RVehicleBatmobileBase` bool 4608 | `:4608-4610` |
| `bHasDamagedLightState` | `RVehicle` bool 3710 | `:3710-3712` |
| `BrakeLightsLensFlare` | `RVehicleBatmobileBase` 6274 | `:6274-6276` |
| `TailLightsLensFlare` | `RVehicleBatmobileBase` 6283 | `:6283-6285` |
| `BrakeLightTrailSystemL` / `…R` | `ParticleSystemComponent` 5325 / 5334 | `:5325-5336` |
| `SelfDriveBrakeLights` | `RVehicle` float 4122 | `:4122-4124` |

**Loop timing: none.** Lights are continuous emissive state (`HeadlightsSwitchedOn` is a bool, the flares are
objects) — there is no on/off period, no blink rate and no fade duration member on the car. The only *timed*
light element is the brake-light trail particle plus the flare, and their fade times are not in the decoded CDO
table → **UNKNOWN**. `Play_HUD_fail` and the weapon warning are one-shots, so **BmAK contributes no loop
timing at all to this feature.**

---

## 4. JC3: the horn is an attached effect, not an event name

`Research/JC3Grab/JC3_AUDIO.md` §8 and `JC3_AUDIO_EVENTS.json`:

| probe | result |
|---|---|
| donor `horn` role | **`fd69c63c-84e6-fa43-b067-7eae99a59ce1`**, class `SAttachedEffect`, `.epe` role name `horn` |
| bank | **`vehicles`** (only) |
| EVTS ordinal | **255**, body **127 B** |
| tune | **`vehicles/122`**, tune GUID **`7b1ad2990a5dd14eaabc29fb6419eba2`** |
| `horn` objects in the fleet | **178**, in **178 of 232** vehicles |
| distinct horn GUIDs | **19** (the donor is #19 — full list below) |
| `radio` objects in the fleet | **0** |
| `Sound`-carrying objects / entities | 6659 / 232 (176 distinct roles) |
| how it is triggered | **UNKNOWN** — no input name, no member; it is code |

### 4.1 The 19 horn GUIDs

| # | GUID | | # | GUID |
|---:|---|---|---:|---|
| 1 | `2129add4-8691-6747-828d-e173c35edbfb` | | 11 | `750e0b22-894c-8b41-821c-970529dd4dbc` |
| 2 | `2852644b-cb5a-954c-8359-667ae92246c0` | | 12 | `86a4d164-abf9-674e-8180-c26020649070` |
| 3 | `31bb5bcd-5701-2a40-9b67-f5d176b59615` | | 13 | `8ad9a86a-dab0-7f4c-94e1-3d8a8e25d995` |
| 4 | `42b8e3d9-311a-5845-a9e9-59ded2456e36` | | 14 | `968868dc-c5e8-064e-9fe0-ee17d3040613` |
| 5 | `4716d42d-bb4d-df48-a374-cb63a7bd3014` | | 15 | `a08c6df5-03a4-854b-99e4-0710ab8b9546` |
| 6 | `5e2b69dd-e25c-8f40-a81d-dd7b12d1a79d` | | 16 | `c74d158d-623d-9c4c-bb1c-a34374c5e55a` |
| 7 | `5ed8305d-0803-b849-9211-b5a26941cd65` | | 17 | `e8d35a1e-f1a3-c743-8f33-1f1df3b63939` |
| 8 | `62d61dca-e641-0f48-b7a6-39708a4e47a6` | | 18 | `fa7514ec-971d-2044-aca6-b78f9a65b8db` |
| 9 | `70f23207-7e77-ce46-8126-56d940ac4e9b` | | **19** | **`fd69c63c-84e6-fa43-b067-7eae99a59ce1`** ← **donor** |
| 10 | `74ad95c1-e261-124b-a92f-2db963e3143d` | | | |

Because the horn is a **per-model attached effect**, "removing the horn" is deleting one `SAttachedEffect`
object, not muting an event — which is exactly what AUD-7 asks for.

---

## 5. The decoded loop timing — 25 horn and siren samples

`vehicles.bank` census (vgmstream, sha256-checked copy): **649 samples**, all **16-bit PCM / 48 kHz**, channels
1–2, **22 looped**. Every horn sample is a *loop* sample with explicit `loop_start`/`loop_end`; the two sirens
and the two `_tail`/`Car_Horn` entries are **not** looped.

| # | sample | index | frames | total | loop in..out | **loop length** |
|---|---:|---:|---:|---:|---|---:|
| 1 | `jc3_vehicle_horn_car_01_loop` | 289 | 28,801 | 0.600 s | 8,179..26,729 | **0.3865 s** |
| 2 | `jc3_vehicle_horn_car_02_loop` | 596 | 39,580 | 0.825 s | 15,828..39,578 | **0.4948 s** |
| 3 | `jc3_vehicle_horn_car_03_loop` | 149 | 88,235 | 1.838 s | 15,941..86,167 | **1.4630 s** |
| 4 | `jc3_vehicle_horn_car_04_loop` | 531 | 38,016 | 0.792 s | 5,053..35,947 | **0.6436 s** |
| 5 | `jc3_vehicle_horn_car_05_loop` | 419 | 71,978 | 1.500 s | 34,934..71,975 | **0.7717 s** |
| 6 | `jc3_vehicle_horn_car_06_loop` | 192 | 60,152 | 1.253 s | 11,325..60,150 | **1.0172 s** |
| 7 | `jc3_vehicle_horn_car_07_loop` | 439 | 22,963 | 0.478 s | 8,459..22,961 | **0.3021 s** |
| 8 | `jc3_vehicle_horn_car_08_loop` | 78 | 53,519 | 1.115 s | 10,303..53,517 | **0.9003 s** |
| 9 | `jc3_vehicle_horn_car_09_loop` | 521 | 45,695 | 0.952 s | 5,564..45,693 | **0.8360 s** |
| 10 | `jc3_vehicle_horn_car_10_loop` | 648 | 57,456 | 1.197 s | 9,381..57,453 | **1.0015 s** |
| 11 | `jc3_vehicle_horn_car_11_loop` | 94 | 51,308 | 1.069 s | 27,517..51,306 | **0.4956 s** |
| 12 | `jc3_vehicle_horn_car_11_tail` | 285 | 52,599 | 1.096 s | — | **one-shot** |
| 13 | `jc3_vehicle_horn_motorbike_01_loop` | 589 | 46,642 | 0.972 s | 8,315..46,640 | **0.7984 s** |
| 14 | `jc3_vehicle_horn_motorbike_02_loop` | 213 | 33,384 | 0.696 s | 12,858..33,382 | **0.4276 s** |
| 15 | `jc3_vehicle_horn_motorbike_03_loop` | 283 | 27,428 | 0.571 s | 3,911..27,426 | **0.4899 s** |
| 16 | `jc3_vehicle_horn_truck_01_loop` | 464 | 51,507 | 1.073 s | 22,777..51,504 | **0.5985 s** |
| 17 | `jc3_vehicle_horn_truck_02_loop` | 470 | 42,585 | 0.887 s | 20,811..42,582 | **0.4536 s** |
| 18 | `jc3_vehicle_horn_truck_03_loop` | 617 | 66,418 | 1.384 s | 38,958..66,415 | **0.5720 s** |
| 19 | `jc3_vehicle_horn_truck_04_loop` | 371 | 56,827 | 1.184 s | 35,142..56,825 | **0.4517 s** |
| 20 | `jc3_vehicle_horn_truck_05_loop` | 630 | 36,663 | 0.764 s | 22,798..36,661 | **0.2888 s** |
| 21 | `jc3_vehicle_horn_truck_06_loop` | 10 | 50,140 | 1.045 s | 17,341..50,137 | **0.6833 s** |
| 22 | `jc3_vehicle_horn_truck_07_loop` | 602 | 73,876 | 1.539 s | 49,589..73,873 | **0.5059 s** |
| 23 | `Car_Horn_01_L` | 277 | 65,016 | 1.355 s | — | **one-shot** |
| 24 | **`jc3_veh_siren_police2_close`** | 387 | **241,607** | **5.033 s** | — | **one-shot** |
| 25 | **`jc3_veh_siren_police2_distant`** | 581 | **241,607** | **5.033 s** | — | **one-shot** |

Read across: a car horn's **sustain loop is 0.30–1.46 s**, most under 1 s; the press-and-hold behaviour is the
sample's own loop point, not a game timer. The **sirens are 5.033 s one-shots** (`close` and `distant` are the
same length — a distance variant, not a loop), so a looping police siren cannot be had from the bank entry as
shipped.

---

## 6. What we reference, what we change, what cannot be created

### 6.1 The decision that is already made: no horn

| BmAK | JC3 | action |
|---|---|---|
| 0 horn events, 0 horn rows, no horn input | `horn` = `SAttachedEffect` `fd69c63c-…`, 178 objects | **remove the object** on the Batmobile (AUD-7). No bank edit, no event id, no timing |
| 0 radio objects implied by no radio key | `radio_objects` **0** on the donor too | nothing to suppress |

This is the recommended route and it needs **no sound-bank work at all**: delete one attached effect.

### 6.2 If a horn is wanted anyway — reference, do not create

| question | answer | evidence |
|---|---|---|
| can we **create** a new horn event id? | **no** | `JC3_AUDIO.md` §10 route **b**: banks are FMOD *Designer/Ex* FEV v56 build 50, no `.fev` project ships, the GUID is authored in the FEV graph; `master.banklist` is a 26-line list so a file can be *registered*, but nothing here can author its contents |
| can we **reference** the existing one? | **yes** | event `fd69c63c-84e6-fa43-b067-7eae99a59ce1`, bank `vehicles`, EVTS 255, tune `vehicles/122` |
| can we change *what it sounds like*? | **yes, by sample payload swap** | route **a** — proven in test-060 / `MODLOG.md` §71: in-place FSB5 PCM swap, same byte size, metadata untouched, bank still parses |
| what must a replacement sample satisfy? | **PCM16, 48 kHz, identical frame count** | census: every donor sample is 16-bit PCM at 48 kHz |

**Recommended takeover target:** `jc3_vehicle_horn_car_08_loop` — **53,519 frames** (1.115 s), loop
**10,303..53,517** = **0.9003 s**. A replacement must be exactly 53,519 frames at 48 kHz mono/stereo as the
original, with its loop points left at 10,303/53,517, or the loop seam moves.

### 6.3 The alert side

| BmAK alert | JC3 nearest | what to set |
|---|---|---|
| `FBatmobileWeaponWarning.AudioEvent` (+8) fired from `TickWeaponWarnings` | no per-warning event exists on the donor; JC3 warning audio is HUD/graph side | **no value** — named omission, as AUD-6/T-AU3 already do for impacts |
| `Play_HUD_fail` `0xDEAD7680` | JC3 has its own UI fail sound in `gui.bank` | keep JC3's; do not port |
| `TransformationReverseDirection…PursuitModeSound` (4828) / `…BattleModeSound` (4836) | no donor mode-switch event (`JC3_AUDIO.md` AUD-4: *"no mode-switch event in the donor"*) | **no value** — deferred with D-2 |
| siren (none in BmAK) | `jc3_veh_siren_police2_close` / `_distant`, 5.033 s one-shots | **do not use** — BmAK has no siren and no alert loop; a police siren on the Batmobile is out of scope for a translation |

### 6.4 The light side

| BmAK | JC3 carrier | value |
|---|---|---|
| `HeadlightsOn/Off`, `HeadlightsSwitchedOn`, `ForceHeadlightsSwitchedOn`, `VEHLTMAT_HeadLightLeft/Right` | donor `dynamic_break_light_on` / `dynamic_break_light_off` effects (`effects` bank, GUID `77009170-…`, `JC3_AUDIO.md` §3 #34) | **reference only** — those are break sounds, not the switch; the switch itself has no event on the donor |
| `VEHLT_BattleModeLight` (6) | no battle-mode light type on a JC3 vehicle | no value; carried by the battle-mode art, not audio |
| `BrakeLightsLensFlare` / `TailLightsLensFlare` / `BrakeLightTrailSystemL/R` | `dynamic_break_taillight` (GUID `fd665c9f-…`, #31) | reference only: JC3 has a tail-light *break* sound, not a brake-light one |
| loop timing of any light | — | **none on either side**; no blink rate or fade member exists, so nothing to set |

---

## 7. Build recipe (only if 6.2 is chosen)

1. Keep `vehicles.bank` as the loaded copy (`sound/fmod_banks/vehicles.bank`, no `.toc`, `MODLOG.md` §71).
2. Pick the horn sample by name from §5 — `jc3_vehicle_horn_car_08_loop` by default.
3. Produce a **PCM16 / 48 kHz / 53,519-frame** replacement; do not touch the FSB5 header.
4. Swap the payload in place; re-run `python Tools/scripts/jc3audio.py --check` (it re-reads the bank and the
   649-sample census and compares byte for byte).
5. Leave the `horn` `SAttachedEffect` and its GUID untouched — the event, tune and bank entry are not edited.
6. Revert: restore `vehicles.bank` from the archive copy whose sha256 is recorded in
   `JC3_AUDIO_EVENTS.json` → `bank_copy.archive_sha256`
   (`6161104d8909b7b0b7dd1d1201dbaa993e141877348457a6c7b5c84da1ccd983`).

If 6.1 is chosen instead — the default — the recipe is "delete the `horn` object", and there is no audio build.

---

## 8. Checks run

| check | result |
|---|---|
| `horn` in `AUDIO_MAP.json` | **0** matches over 361 rows |
| `horn` group in `AUDIO_FEATURES.md` | rows **0**, events **0**, WEMs **0** |
| `horn` in `BINDINGS_KEYBOARD.json` | **0** matches |
| `horn`/`siren` in `Working/Audio/car_base.xml` | **0** matches |
| `horn`/`siren` in `AUDIO_REVIEW_G314.md` | **0** matches |
| donor horn event | bank `vehicles`, ordinal **255**, 127 B, tune **vehicles/122**, tune GUID `7b1ad299…` |
| horn GUIDs | **19**, donor present as **#19**, verified `donor_horn.replace('-','')` ∈ `horn_guids` |
| horn objects / vehicles | **178 / 232**; radio **0** |
| sample loop table | 25 rows, all frames/loop points read from the census; loop lengths recomputed at 48 kHz |
| siren length | both variants **241,607 frames = 5.033 s**, `loop_start`/`loop_end` **null** |
| light enums | `VehicleLightMaterialType` 9 values, `VehicleLightType` 12 values, re-read from `RVehicle.g.cs:2962-2990` |
| warning struct | `FBatmobileWeaponWarningContainer` size 32, `AudioEvent` at FBatmobileWeaponWarning +8 |

---

## 9. Change record (per `AGENTS.md`)

1. **Intended change:** add one report stating that BmAK has no horn or siren, naming its alert members and
   light members, and giving the JC3 horn GUID, bank entry, sample loop timings and the reference/create limits.
2. **File:** `tmp/freebuff/reports/horn-and-siren-plan.md` (this file). Correct file because the brief names it
   and every comparable plan lives in `tmp/freebuff/reports/`; nothing in `Working/`, `Research/`, `Builds/` or
   the game install is modified.
3. **Revert:** delete this file. Nothing else changed.

---

## 10. UNKNOWNs

| # | UNKNOWN | what settles it |
|---|---|---|
| U-1 | which `AkEvent` each `FBatmobileWeaponWarning.AttackType` binds | a CDO dump of `RVehicleBatmobileBase`'s `WeaponWarning` array (the decoded table has no such row) |
| U-2 | BmAK brake-light flare / trail fade durations | same CDO dump; no duration member is decoded |
| U-3 | how JC3 triggers the `horn` object | native code — no input name, no member, no graph edge in the decoded `.epe` |
| U-4 | tune → wave for the horn | `JC3_AUDIO.md` §5: not stored (0 / 649 tunes carry a wave GUID), so the sample must be chosen by name and audition |
| U-5 | whether `jc3_veh_siren_police2_*` has a loop point outside the census | the census reads the FSB5 header; both entries report `loop_start`/`loop_end` null, so a looping siren needs authoring, not a setting |
| U-6 | the semantics of the FEV `TRNS` transitions for a horn (cut/loop points at runtime) | `JC3_AUDIO.md` §11 UNKNOWN (4): marker names readable, semantics are code |

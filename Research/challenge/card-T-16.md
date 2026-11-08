# T-16 · Audio translation — assumption challenge

**Read-only challenge.** Nothing was built, launched, installed or committed; the only file written is
this one. Card: `GRAB_BACKLOG.md` §7 `#### T-16 · Audio translation   M · deps: G1-15, G2-24 · serves: AUD-1…7`,
§12 row 1325, `MODLOG.md` §"T-16 · Audio translation — intended change", §"T-16 · Audio translation — done",
§"T-16 rework — intended change", §"T-16 rework — done". Outputs examined:
`Working/Translation/T12_AUDIO.md` (339 lines), `Working/Translation/t12_audio_map.json`,
`Tools/scripts/t12_audio.py` (1259 lines), `Tools/scripts/_apply_audio.py`.

The card's own gate, re-run today (exit 0):

```
> python Tools/scripts/t12_audio.py --check
PASS: 53 rows = 45/45 donor events + 8 weapon/mode rows | dispositions {'blocked': 29, 'kept vanilla': 7, 'mapped': 5, 'named omission': 11, 'remove': 1} | 5 mapped with 5 chosen slot(s) | 34 slot candidates (22 gain-matched on the written payload, max |delivered-slot| 16.78 LU, 5 over 1 LU - chosen 0; 12 kept stock) | tunes 24/45 | 2 rpm curves | features 7/7 | json match True, md match True
```

So the gate and the doc agree with each other. The question here is whether the *claims inside* that
gate survive, and three of them do not.

## VERDICT

| # | assumption the result rests on | verdict |
|---|---|---|
| A1 | `LandAudio.min_rpm`/`max_rpm` (1000/10000) are "the JC3 rpm window", so the two `REV_RPM` curves can be re-based onto it | **BROKEN** — its own source file (G2-24) says that edge is UNKNOWN; the RTPC x is not proven normalised |
| A2 | 21 of 45 donor rows' tune GUIDs are UNKNOWN because those banks are "not decoded" | **BROKEN** — 21/21 resolve from `character.bank` + `effects.bank`, which are on disk; all 45 are already in the card's `In` JSON |
| A3 | Every *chosen* slot is inside the ±1 LU gate (the summary's `chosen 0`) | **BROKEN** — the one stereo chosen slot measures **+2.44 LU** when the payload is written as the slot's 2 channels, and its byte-size route cannot hold for 2 channels at all |
| A4 | "the only `chassis_spin` sample in vehicles.bank" (A-05's slot method) | **BROKEN** — the bank has 3; the choice between them is unexplained and the count was typed, not derived (R11) |
| A5 | `Play_Batmobile_Rotation` is the "body-spin bed … i.e. yaw rate" (R5: member name read as behaviour) | **WEAK** — engine group, 22 WEMs, RTPC list element-for-element identical to `Play_BML_EngineCoolTicks`, which is an engine tick layer; JC3 has no yaw parameter to drive it |
| A6 | "no `.epe` object names" the 22 pinned GUIDs (a no-carrier claim) | **HOLDS** — 0/22 appear in any object field of all three donor `.ee` decodes (450/450/464 objects) |
| A7 | Gain is matched to "the vanilla event's loudness ± 1 LU" | **WEAK** — what is matched is the slot *sample's* LUFS, not the event's; the event/tune gain is not recovered, so the card's wording is only met by substitution |
| A8 | A-02's three nitro slots are a `proven` swap | **WEAK** — the index↔name convention is proven (two tools agree) and the write was proven once, but the prover cannot be re-run today (`fsb5` missing), the proof is decode-only, and two of the three spans are labelled "tail" while the code takes the head |
| A9 | "0 with an FSB5 loop field" is a measurement of the file, not a limit of the tool | **HOLDS** — the same CLI reports `loop start`/`loop end` on BmAK's FSB5 `.wem`s (14 of 423 media) |
| A10 | The card's Done clause ("every donor event … mapped or explicitly kept vanilla") is met by 29 `blocked` rows | **WEAK** — by the file's own wording `blocked` is not "kept vanilla" ("keeping them exactly as shipped is the default, not a decision"), so 22 donor events are neither |
| A11 | `w602`/`w603` "carry no audio of their own" (a no-carrier claim) | **HOLDS** — `ee: null`, `fmod_guids.present: false`, `tune_members` 171 / `tune_audio_members` 0 on both |
| A12 | The 45→tune edge, the 257/257 counts and "0 of 649 sample GUIDs in `TLNS`" | **HOLDS** — re-derived with an independent RIFF walk, not through `jc3audio` |
| A13 | The jump-bank omission: "movement: Jump_Land/PreJump/PreLand/Wind, 0 WEMs" | **HOLDS** — all four events are `missing-bank` with `wems: []`; the group's 5 WEMs belong to `Play_Batmobile_Dodge` |

Three BROKEN claims (A1–A4), five WEAK (A5, A7, A8, A10 and, narrowly, A9's consequence), five HOLDS.
The card is not failed by any of them: nothing here says a wrong sample was chosen, and every broken
claim is a *statement about the evidence*, not a build value. But A2 is free to fix, A3 changes one
gain, and A1 and A4 must stop being written as measurements.

---

## A1 — "JC3 rpm window (`LandAudio`) 1000.0 … 10000.0" is a decoded value

**The claim.** `T12_AUDIO.md` summary: `| JC3 rpm window (`LandAudio`) | 1000.0 … 10000.0 |`; the section
"RPM curve fits (BmAK `REV_RPM` → JC3 rpm)" re-bases the points onto those two numbers; `rpm_curve()`'s docstring says
"Re-base a BmAK `REV_RPM` curve (x is normalised 0..1) onto the JC3 rpm window", and two rows carry
`curve_rpm` built from it (A-01 and A-05, both `1000→+0.000, 1169→+0.023, 3712→-1.000, 10000→-1.000`).
The summary table's other rows are all `read`/`derived`; this one sits among them.

**Why it matters.** R4: a value is `decoded` only when the file says so. If `LandAudio` is not the
event's parameter range, the curve's `rpm` column is a re-based fiction and B-11 would apply a pitch
curve over a range nothing measured.

**Test 1 — the source that produced the numbers contradicts the use.**

```
> sed -n '98,110p' Research/JC3Grab/JC3_AUDIO.md
| `LandAudio` (`v0300_car_kensington_sportsmuscle_land_audio.vmodc`) | `max_rpm` | 10000.0 |
| `LandAudio` (`v0300_car_kensington_sportsmuscle_land_audio.vmodc`) | `min_rpm` | 1000.0 |

`LandAudio` carries **2 members**, the only vehicle-side
audio parameters the donor modules expose. Whether they are the RPM window a particular
engine event is driven over is **UNKNOWN**: the next paragraph shows the event-to-parameter
edge is not decoded, so the names (`min_rpm` / `max_rpm`) are the only evidence.
```

The G2-24 rework entry in `MODLOG.md` records the same correction from the other side: "`LandAudio`'s
two members are not called 'the RPM window' (event-to-parameter is UNKNOWN)". T-16's summary calls them
exactly that, and the G2-24 rework entry even flags this file: "`Working/Translation/T12_AUDIO.md` still
repeats the old claim and needs its own rework". The T-16 rework (§11 issues) did not touch it.

**Test 2 — is the RTPC x unit even a fraction?** Measured from `AUDIO_FEATURES.json`, the same
parameter names carry different x domains:

```
REV_RPM ((0.0, -1200.0), (0.0429, 0.0), (1.0, 0.0))        -> 12 events
REV_RPM ((0.0, 0.0), (0.0187, 0.0228), (0.3013, -1.0), (1.0, -1.0)) -> 8 events
Speed   ((0.0, -500.0), (30.0, 200.0), (100.0, 200.0))     -> 4 events
Speed   ((0.0, -1.0), (10.0, -1.0), (20.0, 0.0), (100.0, -1.0)) -> 3 events
BML_WheelSpeed ((0.0, -220.0), (65.0, 220.0), (700.0, 220.0)) -> 8 events
```

`Speed` spans 0…100 and `BML_WheelSpeed` 0…700, so the x axis is in parameter units, not globally
normalised. `REV_RPM`'s 0…1 is consistent with *some* arbitrary normalisation, but nothing in the
recovered data names the maximum it was normalised against, and nothing says the JC3 `LandAudio`
members bound the same parameter. That is the same reading the file itself gives for the y axis
("which FMOD target … is not in the recovered RTPC data") — applied one axis earlier.

**Verdict: BROKEN.** The two numbers are `read`; "the JC3 rpm window" is `assumed`, and R4 says
`assumed` is not buildable. The fix is already the file's own convention elsewhere: rename the row
(`LandAudio.min_rpm`/`max_rpm` = 1000/10000, **not** labelled a window) and mark the two `curve_rpm`
rows `blocked` on the parameter edge, as G2-24 already does.

---

## A2 — "21 rows: UNKNOWN — banks this card does not decode"

**The claim.** `T12_AUDIO.md` summary: `| rows whose event→tune edge resolved | 24 (of 45 donor rows;
21 UNKNOWN - banks this card does not decode) |`; §"Event → tune": "`24 donor rows resolve their tune
here (vehicles.bank); 21 sit in banks this card does not decode (UNKNOWN)`"; §12: "tunes 24/45". The
check prints `tunes 24/45`.

**Why it matters.** This is the card's own object ("BmAK event(s) → **JC3 event GUID**"); the tune GUID
is the only hop between them that the bank does store (the doc's own §"Event → tune"). If 21 rows are
missing a hop the files already contain, the map is 21 hops short of what its own input proves.

**Test 1 — the input file already has all 45.**

```
> python -c "... j['donor']['events'] ..."
donor events 45 with tune 45
Counter({'vehicles': 24, 'effects': 19, 'character': 2})
```

`Research/JC3Grab/JC3_AUDIO_EVENTS.json` is listed in the card's `In` and in the doc's header as one of
the two sources. Every one of the 45 rows carries `tune: {bank, index, tune_guid}` there.

**Test 2 — are the other two banks actually on disk and readable?**

```
> ls Working/Audio/jc3bank/sound/fmod_banks/
character.bank
effects.bank
vehicles.bank
```

**Test 3 — re-read the edge from those two banks** (same reader, `jc3audio.fev_tunes`):

```
character tunes 193 donor rows in this bank 2 re-read match 2
effects tunes 579 donor rows in this bank 19 re-read match 19
```

i.e. 21/21, with the GUIDs equal to the JSON's (`d87e18de json 99924923 bank 99924923`,
`844fb573 json 6eb0d5e1 bank 6eb0d5e1`, …). The only reason `bank_tunes()` returns 24 is that it is
called once, with its default argument: `bank_tunes(bank: str = "vehicles")`.

**Verdict: BROKEN.** The claim "banks this card does not decode" is false for the edge the row is
about: the two banks are present and the reader resolves all 21 in one call, and the 45 values were
already sitting in the card's own `In` file. This is the exact failure mode §0.5 R4 exists for — a
`blocked`/UNKNOWN label over data that is on disk.

---

## A3 — "chosen slots outside the gate: 0"

**The claim.** Summary: `| chosen slots outside the gate | 0 |` and "22 gain-matched on the written
payload". The doc's table: `| weapons | 408 | jc3_wpn_minigun_fire_close_loop_04 | 48000 | 2 | 160337 |
one-shot | -5.30 | -0.10 | Play_Batmobile_MShot | 1.13 | -5.87 | -0.57 | 3.53 | 2.0011 |` — channel
count **2**, Δ −0.57 LU, chosen for W-03.

**Why it matters.** The card's gate is ±1 LU on the swap. If the payload model is wrong for stereo
slots, the one stereo chosen slot ships ~2.4 LU hot, and B-11's "same byte size" route does not exist
for it.

**Test 1 — what the slot is.**

```
> Tools/vgmstream-win64/vgmstream-cli.exe -s 408 ... weapons.bank
channels: 2
stream total samples: 160337 (0:03.340 seconds)
encoding: 16-bit Little Endian PCM
stream name: jc3_wpn_minigun_fire_close_loop_04
```

2 ch × 160,337 × 2 B = **641,348 B** of payload space; the generator's payload is a *mono* downmix of
160,337 frames = **320,674 B**. `build_payload()` writes `q[:, None]`, and `_apply_audio.py`'s own size
check pins the same assumption for the mono nitro slots: `hlen = payload_len - ns * 2` /
`assert 0 <= hlen < 4096` — for a stereo slot that expression is ~320 kB and the assert fires. So the
doc's "the payload keeps the byte size (route a)" cannot hold here.

**Test 2 — measure the payload the way the slot is shaped.**

```
slot 408 shape (160337, 2) lufs 2ch -5.30 mean-mono -8.51
src mono frames 80124 lufs -6.43
delivered mono -5.87
delivered 2ch-dup -2.86
delta vs slot 2ch 2.44
```

The mono figures reproduce the doc exactly (−5.30 slot, −6.43 source, −5.87 delivered, Δ −0.57). Write
the same payload as the two channels the slot has and it measures **−2.86 LUFS**, i.e. **+2.44 LU**
above the slot — outside the ±1 LU gate. (Duplicating a mono signal into two channels is the only
shape that keeps the frame count; the alternative, writing mono into a 2-channel slot, halves the bytes
and changes the slot's channel count without touching the FSB5 header.)

**Verdict: BROKEN** for the claim that all chosen slots are inside the gate. The comparison is a
mono-monitor measurement against a 2-channel slot, so `delivered − slot` is not one quantity for
`channels: 2` slots. One chosen slot is affected (W-03); the two non-chosen 2-channel candidates
(`#469 endclick`, and the missile slots) change by the same +3 dB if they are ever chosen. Fix: measure
the payload at the slot's channel count, or restrict chosen slots to `channels == 1` until B-11 states
what it writes.

---

## A4 — "the only `chassis_spin` sample in vehicles.bank"

**The claim.** A-05's `slot_method`: "name match: the only `chassis_spin` sample in vehicles.bank",
`confidence: candidate`, `chosen: jc3_veh_lave_chassis_spin_creaks_loop_fast`. The method string is
typed in `SPECS` (`Tools/scripts/t12_audio.py`), i.e. it is not one of the derived columns.

**Test — read the bank's own name table** (`jc3audio.fsb(...)["names"]`, 649 names):

```
> ... names containing 'chassis_spin'
['jc3_veh_lave_chassis_spin_whoosh_cycle_2hz',
 'jc3_veh_lave_chassis_spin_creaks_loop_fast',
 'jc3_veh_lave_chassis_spin_creaks_loop_slow']
```

Three, not one. (`door_tank_open` likewise has `_01/_02/_03`; `premium_nitro` has four names including
`jet_flame_loop`; `gear_shift` has 17 across five families, of which the doc picks
`performance_*` while a `supercar_*` family also exists.)

**Why it matters.** R11 ("counts are generated, never typed") and R4 (a selection is fine, but it has to
be labelled a selection). "The only X" reads as a derived fact and closes the question of why
`creaks_loop_fast` rather than `whoosh_cycle_2hz` or `creaks_loop_slow`. The generator's own summary
shows the narrowing was editorial: A-05 has exactly one `slots` entry, hard-coded, so the "only" is
true of *the candidate list the script was given*, not of the bank.

**Verdict: BROKEN.** The sentence is false about the bank and the count is typed. Fix: derive the
family (`[n for n in names if 'chassis_spin' in n]`) and say "chosen from three `chassis_spin` samples;
`whoosh_cycle_2hz` and `creaks_loop_slow` are the alternates".

---

## A5 — `Play_Batmobile_Rotation` read by its name as the body-spin bed (R5)

**The claim.** A-05's `match`: "role-name: the body-spin bed <-> `Play_Batmobile_Rotation` (its RTPC
list binds `BML_Steering_Rotation` + `BML_WheelSpeed`, i.e. yaw rate)".

**Why it matters.** This is the failure mode R5 was written for. "Rotation" is a word in an event name;
"its RTPC list proves yaw" is a claim about behaviour that can be tested against the other events in
the same group.

**Test — compare the RTPC signature with a control event that is definitely not a spin bed.**

```
Play_BML_EngineCoolTicks  Playable_BatmobileFunhouse_SF  group engine  wems 22
  rtpc [('Speed', 3), (None, 3), ('BML_Steering_Rotation', 5), ('BML_WheelSpeed', 3), ('Speed', 3),
        ('BML_WheelSpeed', 3), (None, 3), ('REV_RPM', 4), (None, 3), ('Startup', 2), ('Startup', 2),
        ('EngineHeat', 3), ('EngineHeat', 2), ('EngineHeat', 2)]
Play_Batmobile_Rotation    Playable_BatmobileFunhouse_SF  group engine  wems 22
  rtpc [('Speed', 3), (None, 3), ('BML_Steering_Rotation', 5), ('BML_WheelSpeed', 3), ('Speed', 3),
        ('BML_WheelSpeed', 3), (None, 3), ('REV_RPM', 4), ('None', 3), ('Startup', 2), ('Startup', 2),
        ('EngineHeat', 3), ('EngineHeat', 2), ('EngineHeat', 2)]
```

The two lists are element-for-element the same set of bindings. `Play_BML_EngineCoolTicks` is an engine
idle-tick layer and nobody would call it a chassis spin; therefore "binds `BML_Steering_Rotation` +
`BML_WheelSpeed`" does not separate a spin bed from an engine layer, and the parenthetical "i.e. yaw
rate" does not follow from the list. Both events are also in the `engine` group with 22 WEMs each, and
the doc's own A-01 text describes `Play_BML_EngineCoolTicks` as one of the engine bed's two layers — so
the same event family is claimed to be both the engine bed and the body-spin bed.

Two consequences the row does not state: (a) JC3 exposes no yaw/wheel-speed parameter (the doc's own
UNKNOWN #4), so the 2 rpm curves fitted for A-05 have no input to drive them; (b) the `burnout` group
holds `Play_Batmobile_WheelSpin`, `Play_Batmobile_Drift` and `Play_Batmobile_Skid_*`, which the row
never considers as the spin source.

**Verdict: WEAK.** The event exists, is pinned, has media, and the slot is a real `chassis_spin` sample,
so the row still names a real candidate — but the *reason* given is a name, the RTPC evidence is
non-discriminating (identical to a control), and the row's own curve has no consumer. It should say
`candidate — name match; the RTPC signature is shared with the engine-tick layer, audition decides`,
and `Play_Batmobile_WheelSpin` should be listed as the alternate source.

---

## A6 — "no `.epe` object names these 22 GUIDs" (the no-carrier claim)

**The claim.** 22 rows `D-01…D-22` are `blocked` with "pinned by the entity but no `.epe` object names
this GUID and no BmAK behaviour maps to it (G2-24 §3)"; the summary counts `| pinned donor GUIDs no
`.epe` object names | 22 |`.

**Why it matters.** It is a negative claim, and a negative is only as good as the search. The doc's own
history shows this exact class of claim being wrong before (the G2-24 rework: "`TLNT` occurs 0 times" /
"0/257 event bodies hold a tune GUID" — both later refuted).

**Test — search every object field of every donor `.ee` decode, not just the roles list.** For each of
the 22 GUIDs, convert to the `.epe` byte-list form (`247,154,52,176,…`) and look for it in any
`values` string of any object:

```
unnamed 22 named 23
249a34b0 249a34b0-7997-424c-9f26-7b7eb0725e9c -> None
30d9ab54 30d9ab54-baf7-5e44-ad67-22a72de44ad3 -> None
... (22 lines, all None)
unnamed GUIDs actually present in some object: 0 / 22

v0300_..._civilian_01.ee.json objects 450 unnamed GUIDs named here: 0
v0300_..._debug.ee.json        objects 450 unnamed GUIDs named here: 0
v0300_..._signature_preorder.ee.json objects 464 unnamed GUIDs named here: 0
```

All three donor variants, every object class (`SAttachedEffect`, `SDynamicAttachedEffect`,
`SAttachedEffectTable`, particle/material objects), not only the sound classes. 51 distinct 16-byte
GUID-valued fields exist in the graph, and none of them is one of the 22.

**Verdict: HOLDS.** The negative claim survives a search wider than the one that produced it. (The
descriptor "the vehicle bank's shared set" is not tested here — that would need every fleet entity's
`.fmod_guids` re-read; it is descriptive, not load-bearing for any row.)

---

## A7 — "gain matched to the vanilla event's loudness ± 1 LU"

**The claim.** The card: "gain matched to the vanilla event's loudness ± 1 LU". The doc: `| slots with a
measured gain match | 22 … |` and "`delivered` is the integrated loudness **measured on the payload the
swap writes** … and `Δ LU` is `delivered − slot`, the card's ±1 LU test". The rework states the rule:
"loudest variant is now loudest **as the payload reads it** (mono), not the shipped multi-channel LUFS".

**Why it matters.** "The event's loudness" and "the sample's loudness" are different objects: what the
player hears is the sample after the event's and the tune's gain/VCA, which is not recovered. The file
is explicit that tune→sample is UNKNOWN; it is silent on tune→gain.

**Test — what the comparator actually is.** For each slot the doc's `slot.lufs` is vgmstream's decode of
that one FSB5 subsound (`vgm_measure` → `integrated_lufs`), and `delivered` is a synthesised mono
payload. Both are the *sample's* integrated loudness. There is no field anywhere in the map that
carries an event or tune loudness (checked: `rows[].sources[].source` carries `lufs`, `peak_dbfs`,
`frames`, `channels` — all WEM-level). And the doc's own UNKNOWN #1 concedes the tuning graph is not
decoded.

So the ±1 LU test is well defined and reproducible (I re-measured three of its numbers and got −5.30 /
−6.43 / −5.87 exactly), but it tests sample-to-sample loudness. An event that ships its sample at −10
LUFS with a −6 dB event gain is 4 LU louder in game than the same sample at unity, and nothing here
measures that.

**Verdict: WEAK.** Not a wrong number — a renamed test. The doc should say "matched to the slot
**sample's** loudness; the event/tune gain is UNKNOWN", which is one clause and keeps the card honest.
(Combined with A3, the same substitution also changes the value for 2-channel slots.)

---

## A8 — A-02's `proven` confidence

**The claim.** `slot_method: proven swap: test-060 replaced FSB5 indices 56/150/355 (0-based) with these
names' payloads and the bank still parsed + decoded (MODLOG §71, `_apply_audio.py`); the per-slot source
and span are that script's JOBS table`; `slot_confidence: proven`. The summary classifies it as
"`proven` only where test-060 swapped that index".

**What is actually proven, tested three ways.**

1. **The index convention** (name-table order == vgmstream 1-based == `_apply_audio.py` 0-based). Two
   independent tools agree:
   ```
   > ... names[56] names[150] names[355]
   names[56]  jc3_veh_land_premium_nitro_start
   names[150] jc3_veh_land_premium_nitro_loop
   names[355] jc3_veh_land_premium_nitro_stop
   > vgmstream-cli -s 57 vehicles.bank
   channels: 1 / stream total samples: 35737 (0:00.745 seconds)
   stream name: jc3_veh_land_premium_nitro_start
   ```
   The doc's `#57` row (35737 frames, mono, 48 kHz) is the same sample. **Holds.**
2. **That the write happened.** `Working/Audio/verify_56.wav`, `verify_150.wav`, `verify_355.wav` exist.
3. **That it can be re-run.** It cannot: `_apply_audio.py` imports `from fsb5 import FSB5`, and
   `python -c "import fsb5"` → `ModuleNotFoundError: No module named 'fsb5'`. The proof lives only in the
   journal and in three wav artefacts.

**What is not proven.** The script's own verification is `returncode == 0 and os.path.exists(...)` after
`-s idx+1` — decode success. That is proof that the three slots accept a payload of that size, *not*
that `exhaust_upgrade_nitrous`'s tune plays those slots; and the doc's own UNKNOWN #1 says tune→sample
is not stored, so it cannot be. `proven` therefore reads as "proven routable" when it means "proven
writable".

**A further mismatch, found while checking the spans.** The JOBS table takes `mono[:need]` for a
positive span and `mono[-need:]` for a negative one:

```
JOBS = [
    (56,  ... "jc3_batmobile_start.wav", 0.7445, 30),
    (150, ... "EC2FD42B.wav",           3.2254, 0),
    (355, ... "EC2FD42B.wav",          -0.756, 100),
]
```

The map records `source_span_s` **0.7445** and **3.2254** (both positive, i.e. head) but the renderer
labels every `slot_src` span "tail":

```
f" ({x['source_span_s']} s{' tail' if x.get('source_rule') == 'slot_src' else ''})"
```

so `T12_AUDIO.md` prints `jc3_batmobile_start.wav (0.7445 s tail)` and `EC2FD42B.wav (3.2254 s tail)`
for two spans that the code takes from the **front** of the file, while `(0.756 s tail)` is the only one
that really is a tail. B-11 implementing from the doc would take the wrong 0.744 s of the start sample.

**Verdict: WEAK.** The numbers and the index convention hold; the confidence word overstates what was
shown; the proof tool is not runnable today; and the head/tail label is wrong on two of three rows.
Fixes: `slot_confidence: candidate (writable slot proven)`, `head`/`tail` rendered from the sign of the
span, and a note that `_apply_audio.py` needs `fsb5` installed to reproduce.

---

## A9 — "0 with an FSB5 loop field"

**The claim.** Summary: `| slot candidates measured | **34** (0 with an FSB5 loop field) |`; the section:
"No candidate carries an FSB5 loop field … Their names say loop and the files' loop fields are empty.
Whether the looping is then produced by the event/tune graph, or this bank build simply ships no loop
metadata, was **not measured** — UNKNOWN."

**Why it matters.** The first half is a measurement claim. If vgmstream simply cannot report loops for
this container, "0 of 34" is an artefact of the tool and every loop-named slot's transform is
unconstrained rather than known-unlooped.

**Test 1 — can the same CLI report loops for FSB5-family files?** Yes:

```
> vgmstream-cli -m E:/Modding/ArkhamKnight/_grab/audio/wem/0267FF16.wem
loop start: 8456 samples (0:00.176 seconds)
loop end: 178312 samples (0:03.715 seconds)
stream total samples: 181362 (0:03.778 seconds)
encoding: Custom Vorbis
```

A `.wem` is an FSB5; `AUDIO_FEATURES.json` records `loop_lines` for **14 of 423** BmAK media on the same
code path. So the field exists and this toolkit reads it; its absence in all 34 JC3 candidates is a
property of those files.

**Test 2 — the counts.** `vgm_measure` reads `loop start:`/`loop end:` from the CLI text; every slot row
in the JSON has `loop_start: null, loop_end: null`, and my own CLI runs on `#57`, `#151`, `#279`, `#7`,
`#408`, `#469`, `#559` printed no loop line. Consistent.

**Verdict: HOLDS** for the measurement. The *consequence* the doc draws is already demoted to UNKNOWN
and should stay there: the tune bodies are 42–181 B (26 distinct lengths, measured below) and only the
first 32 B are decoded, so "the bank ships no loop metadata" is not the same as "no loop is defined
anywhere in the bank".

```
> ... TLNB body sizes: [(42, 40), (66, 49), (68, 53), (92, 28), (98, 1), (100, 1), (116, 3), ...]
    ... 26 distinct
```

---

## A10 — the card's Done clause, met by counting `blocked` rows

**The claim.** The card's `Done`: "every donor event and every chosen weapon event mapped or explicitly
kept vanilla". §12 and the MODLOG call T-16 done on 53 rows with `mapped 5, kept vanilla 7, named
omission 11, remove 1, blocked 29`.

**Test — read the file's own definitions.**

```
| D-01 | UNASSIGNED | `249a34b0` · vehicles/43 · `unnamed` | — | `blocked` | — | — | blocked: Q-1 - keeping it exactly as shipped is the default, not a decision; an audition has to say whether this shared bank event is audible on the car before the row can be called kept vanilla |
```

and the rework's own rule (issue 5): "the 22 rows the fallback path auto-labelled `kept vanilla` become
`blocked` with a named probe (R4: no semantic bridge is `blocked`, never a class); `kept vanilla` must
come from a `SPECS` decision."

So the file itself says a `blocked` row is **not** kept vanilla. Counting: 22 unnamed GUIDs are donor
events and are `blocked`; 11 rows are `named omission` (not "mapped"); 1 is `remove`. Under the clause's
literal wording, **22 donor events are neither mapped nor kept vanilla**, and 12 more are named
omissions/remove.

**Verdict: WEAK.** This may be the right call — R4 forbids a `class` without a bridge, so `blocked` is
the honest disposition and the card's Done clause is simply stricter than the rules allow. But the card
is flipped to `done` while its own clause is unmet by its own definitions, and that should be written
down (the MODLOG does defend the dispositions, but never says the Done clause is being read as
"mapped, kept vanilla, or recorded as blocked per R4"). Either the row stays `blocked: 22 pinned GUIDs
need an audition` or §12 records the re-reading.

---

## A11 — "`w602`/`w603` carry no audio of their own"

**Test — the weapons block of the G2-24 JSON:**

```
"w602": {"banks_holding": [], "components": [], "ee": null, "fmod_guids": {"present": false},
         "guids": [], "label": "60 mm tank cannon", "sound_roles": [],
         "tune": ".../w602_mediumtank_canon.wtunec", "tune_audio_members": [], "tune_members": 171}
"w603": { … same shape …, "label": "tank machine gun", "tune_members": 171, "tune_audio_members": []}
```

No `.ee`, no `.fmod_guids`, no sound role, 171 tune members and 0 audio members. There is also no
`w602*` file in `E:/Modding/JustCause3/_grab/entities/` or `detail/`.

**Verdict: HOLDS.** (The doc spells the entity `w602_mediumtank_cannon` once; the module is
`w602_mediumtank_canon`. Cosmetic, but it is the string B-11 will grep for.)

---

## A12 — the 257/257 event→tune edges and "0 of 649 sample GUIDs in `TLNS`"

**Why test it.** This is the one claim the whole T-16 rework hangs on, and it was produced by the same
parser that had just been corrected. A second parse is the only way to know whether the reader or the
file is doing the work.

**Test — an independent RIFF walk** (`struct` only, no `jc3audio`), straight over
`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank`:

```
sections 26 has TLNS/EVTS/WAVS True
events 257 unique guids 257
tunes 257
tune body 16:32 is an EVTS event GUID: 257 / 257
owner event body 32:48 == tune GUID: 257 / 257
distinct tune GUIDs 257 distinct owners 257
wave entries 649 distinct 649
distinct wave GUIDs found in TLNS bytes: 0
```

**Verdict: HOLDS.** "Stored on both sides, 257/257, one-to-one, and no wave GUID anywhere in `TLNS`" is
true of the bytes, not only of the reader. The consequence ("tune → sample is not stored") therefore
also holds for this bank, and it is what makes every slot a *selection* rather than a decode.

---

## A13 — the jump-bank omission

**The claim.** A-12 `named omission`: "BmAK jump one-shots are `missing-bank` (G1-15 movement:
Jump_Land/PreJump/PreLand/Wind, 0 WEMs), so there is nothing to swap in". The obvious trap is that the
group row says `{'name': 'movement', 'rows': 20, 'events': 5, 'wems': 5}` — five WEMs, i.e. not zero.

**Test — per event:**

```
Play_Batmobile_Dodge           status resolved      wems ['0x0AECBCAC','0x00D81BE5','0x31C97920','0x1E17F4B7','0x0F88874C']
Play_Batmobile_Jump_Land       status missing-bank  wems []
Play_Batmobile_Jump_PreJump    status missing-bank  wems []
Play_Batmobile_Jump_PreLand    status missing-bank  wems []
Play_Batmobile_Jump_Wind       status missing-bank  wems []
```

The group's five belong to `Dodge`, which AUD-6 does not claim.

**Verdict: HOLDS.** The doc cited the four jump events, not the group total, so the count it wrote is the
count that matters. (Same for A-09's `impacts` 16 rows / 5 events / 0 WEMs and A-14/A-15's `death`
1 event / 0 WEMs — both confirmed against the group table.)

---

## What this challenge did not test

* **Which sample the donor's engine tune plays** (A-01). By design unknowable here: tune→sample is not
  stored (A12) and the donor is fictional. A-01 is `blocked` and names all six `aston_martin_vantage`
  layers, which I confirmed is the largest `_engine_rpm_` stack (aston 6, ducati 5, train 5) out of 34
  `engine` names in 649.
* **Whether the in-game loudness follows the sample's LUFS.** Needs phase Q (and a launch, which this
  task forbids).
* **The `proven` write itself.** `fsb5` is not installed, so `_apply_audio.py` cannot be re-run; only
  its three `verify_*.wav` artefacts and the journal attest to it.
* **Whether the 22 unnamed GUIDs are shared by the rest of the fleet.** Would need every fleet entity's
  `.fmod_guids` re-read; no row depends on it.

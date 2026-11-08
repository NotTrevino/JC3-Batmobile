# Assumption challenge — backlog card G2-24 (JC3 vehicle audio system)

Read-only pass over the finished card: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-24 card (§6, line 720),
its §12 row (line 1307), the MODLOG `G2-24 · JC3 vehicle audio system — done` section (line 11613) and
the `G2-24 rework — done` section (line 15321), and the outputs `Research/JC3Grab/JC3_AUDIO.md` +
`JC3_AUDIO_EVENTS.json` + the generator `Tools/scripts/jc3audio.py`, plus what it reads:
`sound/fmod_banks/{vehicles,character,effects,weapons,weapons_preorder}.bank`,
`master.banklist`, `Research/JC3Grab/INDEX.jsonl` (81,952 entries),
`E:/Modding/JustCause3/_grab/{entities,detail}` (232 + 232 decoded `.ee`), `MODLOG.md` §70/§71 and
`Tools/scripts/_apply_audio.py`.

Constraints honoured: no game launched, nothing written into `D:/Games`, no archive written, no `--write`
(the only write is this file), nothing committed, no secrets, no shared game module touched.

Gate re-run first (`--check`, exit 0, verbatim):

```
$ python Tools/scripts/jc3audio.py --check
PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 45/45 donor tunes, 257/257 tunes
with an event GUID, 0/0 wave GUIDs in tunes/instances, 649 samples (22 looped, 1 rate), wave refs 0,
LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True                       EXIT=0
```

## VERDICT

**Three BROKEN, seven WEAK, nine HOLDS, three mixed.** The card's central negative result is wrong, and I can show it
with the same file it measured. `JC3_AUDIO.md` §5 concludes *"tune → wave is not stored … the build picks
a sample by name and audition"* from the probe `wave GUIDs inside any sound instance: 0 of 649`. That probe
reads the wrong 16 bytes: `fev_waves()` parses a `WAV ` entry as `u8 index + 16-byte GUID`, so it takes
`body[1:17]` as the GUID. The entry is `GUID at body[0:16]`, and the bytes it calls "index" are the first
byte of that GUID. With `body[0:16]`:

```
instance body[28:44] set == WAV body[0:16] set:   649/649 (vehicles)   976/976 (character)   1524/1524 (effects)
WAV body[22:24] as u16 == slot position:          649/649              976/976               1524/1524
corrected "wave GUID found outside WAVS":         649/649              976/976               1524/1524   (the doc says 0/649)
```

So **event → tune → sound instance → wave slot → FSB5 sample** is stored, and 12 of the donor's 45 events
resolve to named samples from the file alone — including `horn → slot 418 jc3_vehicle_horn_car_05_loop`,
`engine_running_sound → 99/522 aston_martin_max_remix_start/shutdown`, and
`exhaust_upgrade_nitrous → 56/150/165/355 premium_nitro_{start,loop,jet_flame_loop,stop}`, where **56,
150 and 355 are exactly the three slots `_apply_audio.py` swapped in test-060**. Two independent checks
(a semantic name match and the project's own historical swap) agree with the corrected parse, so this is
not a hypothesis: the off-by-one is the artefact.

Everything else in the card is sound where it is measured, and loose where it generalises: the "fleet"
is 232 of 233 vehicle `.ee` (not a thin sample), horn 178/178 and radio 0 re-derive exactly, `LandAudio`
really does carry exactly 2 members on all 145 vehicles that have it, and no `.fev` ships (0 of 81,952
index entries). What does not hold is the shipping-route story around it: "proven by test-060" is a
file-level proof with an unverified loader (the project's own later entry says the in-game result was
never checked), the swap rule omits the channel count that 143 of 649 samples need, and `vehicles.bank`
ships twice with different FSB data.

| # | assumption | verdict |
|---|---|---|
| A1 | the two GUIDs in `TLNB`/`EVTB` are distinct identities (tune at tune-body 0, owner event at 16; tune at event-body 32), not a self-reference | **HOLDS** — 0/257 self-references, 0 tune GUIDs are event GUIDs, 257/257 unique both ways |
| A2 | "45/45 resolved to a tune index" is evidence | **WEAK** — entailed by the 257/257 bijection: every event in the bank resolves, so 45/45 says nothing beyond "45/45 are in a bank" |
| A3 | tune → wave is not stored (0/649 in tunes and instances) | **BROKEN** — one-byte offset in `fev_waves()`; with `body[0:16]` the instances reference 649/649 wave slots |
| A4 | therefore the sample must be picked by name and audition | **BROKEN** — 12/45 donor events resolve by file; the resolved nitro slots are exactly test-060's 56/150/355 |
| A5 | `WAVS` = "a u8 index + 16-byte GUID per sample slot" | **BROKEN** — the "u8 index" is the GUID's first byte (monotone 1…255, 235 distinct); the slot index is `body[22:24]` == position |
| A6 | the chain stops at the tune (stated universally: "no event path", "the chain stops") | **WEAK** — 103/257 tunes reference an instance id, 154 reference nothing recoverable; universal negative, partial truth |
| A7 | "the 45 events the donor pins" is the event set for the build that ships | **WEAK** — the armed template `…_signature_preorder.ee` pins **55** GUIDs over **4** banks (936 B); the 10 extra are the weapon bank's |
| A8 | `LandAudio` = 2 members, "the whole vehicle-side audio parameter set" | **HOLDS** for the module (145/145 have exactly 2), **WEAK** for "whole" (Boat/Air/Train audio carry RPM curves) and for the values as a schema (donor 1000/10000 vs fleet mode 500/5000) |
| A9 | horn = 178 objects in 178 vehicles, 19 GUIDs | **HOLDS** — re-derived exactly; R5 caveat: the object's *name* is the evidence, its input binding is not decoded (the doc says so) |
| A10 | radio: 0 objects in all 232 decoded vehicles | **HOLDS** as scoped — 0 for "radio" anywhere in the 232 detail JSONs; the scope is 232 of 233 vehicle `.ee` |
| A11 | "the fleet" = the 232 decoded builds | **HOLDS** — index holds 233 vehicle `.ee`; the single miss is an air vehicle (`v2602…_custom_mm230`) |
| A12 | route b impossible: no `.fev` project ships, nothing can author the graph | **HOLDS** on the file search (0 `.fev`/`.fsb` of 81,952), **WEAK** on the two inference clauses it hangs on |
| A13 | route a "possible, proven by test-060" | **WEAK** — the payload swap + redecode is proven; the loose-override loader claim is unverified, and the repo says so elsewhere |
| A14 | "every donor sample is PCM16/48 kHz, so a replacement must be PCM16/48 kHz + the original frame count" | **WEAK** — channel count (143/649 stereo) is a missing third constraint; "donor sample" mislabels a whole-bank census; 32,848 B of the data section is unexplained |
| A15 | 23 of 45 GUIDs named by the `.epe`, 22 unnamed | **HOLDS** — 23/45 present anywhere in the donor `.epe` text, 0 present outside a `Sound` field |
| A16 | "the census asserts the Working copy sha256 equals the archive entry" | **WEAK** — `vehicles.bank` exists twice (`archives_win64/game1` 210,803,872 B, `patch_win64/game5` 210,781,376 B) with different FSB data; the identity is to one of two shipped files |
| A17 | sample numbering (the `#` column, the swap indices, the "slot" index) | **WEAK** — the doc's `#` is 1-based vgmstream, the WAV slot `u16` and `_apply_audio.py` JOBS are 0-based; never stated, and the two differ by one |
| A18 | route c: `weapons.bank` holds 1,228 named samples, so the same swap applies | **HOLDS** on the count (1,228/1,228 measured), **WEAK** on method — it is typed into the generator and §7 says the weapon banks "were not probed" |
| A19 | `w602`/`w603` have no `.ee` and no `.fmod_guids`, only a `.wtunec` | **HOLDS** — 1 path each in the index, both `.wtunec` |
| A20 | `w618`/`w619` bind `Sound` to the first GUID of their own `.fmod_guids` | **HOLDS** — `fire` = `guids[0]` in `weapons_preorder`, `fire_sound_combi` = `guids[0]` in `weapons_preorder` |
| A21 | no event name or path is stored; 0 of the role names occur in `EVTS` | **HOLDS** — 2,333 runs ≥3 chars / 1,654 ≥4, none a role name; 0 sample names in the PROJ region either |
| A22 | the container census (257 events/tunes, 1,674 instances, 969 params / 49 names, 649 samples, 22 looped, 1 rate) | **HOLDS** — every number re-derived |

Counts: 9 HOLDS, 7 WEAK, 3 BROKEN, plus 3 mixed verdicts (A8, A12, A18 — a module-level or number-level
HOLDS that turns WEAK as soon as it is stated fleet-wide).

---

## A3 — "tune → wave is not stored (0/649)". **BROKEN**

`JC3_AUDIO.md` §5:

> | wave GUIDs inside any sound instance (`WAIT`) body | **0** of 649 |
> …
> The chain stops one hop later: **tune -> wave is not stored** — no tune chunk and no sound-instance
> body contains a `WAVS` GUID (0 / 649).

The reading code (`Tools/scripts/jc3audio.py:188`):

```python
def fev_waves(d, f):
    """`WAVS` -> bare `WAV ` chunks: u8 slot index + 16-byte GUID."""
    ...
    out.append({"index": body[0], "guid": body[1:17].hex()})
```

A `WAV ` entry is 26 bytes. Dumped (`WAVS` section, first three entries):

```
WAVS children: 650   sizes: [4, 26]   tags: {b'WAV ', b'LCNT'}
  016417c1225ad3419bcd5c85026b6a7f08000000000000000000   ← 32 hex = 16 B | 08 000000 | 00000000 | 0000
  02c9332d6dfcea499e3c0a0e9a7ed455080000000001000000
  02ca25a7cd452e4ea4632a3284c9f473080000000002000000
```

Read as the reader reads it, the "GUID" is `6417c1225ad3419bcd5c85026b6a7f08` — whose **last byte is
`0x08` for all 649 entries**, and which is preceded by a byte that runs `01, 02, 02, 03, 03, 03, 04, 04, …,
255` (`235` distinct values over 649 slots): a monotone staircase cannot be a slot index. Read as
`body[0:16]`, three facts line up at once, in all three banks:

```
instance body[8:24] (instance id)  distinct: 1674        (one per instance)
instance body[28:44]               distinct: 649         ← equals the sample count
GUID2 == WAV[0:16] set:            649/649 (veh)  976/976 (character)  1524/1524 (effects)
GUID2 == WAV[1:17] set:            0/649          0/976               0/1524
WAV[22:24] u16 == position:        649/649        976/976             1524/1524
```

So the `WAIB` body is `GUID(16) + 4 pad + GUID(16)` = 36 B, where the second GUID is the **wave slot** the
instance plays, and the `WAV ` entry is `GUID(16) + u32 0x08 + u16 0 + u16 slot + u16 0` where
`slot` is the 0-based FSB5 sample index (0…648). The doc's probe asked whether a `WAVS` GUID appears in the
instance bodies and answered 0 because it was searching for a byte-shifted string:

```
reader's wave GUIDs in instance bodies [raw]:      0/649
reader's wave GUIDs in instance bodies [guid_le]:  0/649   (byte-order alternatives also 0)
reader's wave GUIDs in instance bodies [rev]:      0/649
corrected wave GUIDs outside WAVS (PROJ only):     649/649
```

Note the tune-side half of the claim survives (tunes reference instance ids, not wave ids: 0 wave GUIDs in
tune chunks even with the corrected bytes) — the error is the instance half plus the sentence drawn from it.
`invariants()` now *asserts* the broken value (`if vb["wave_guids_in_instances"] != 0: bad.append(...)`), so
the gate will reject the corrected number rather than surface it.

This was missed twice: `--check` re-derives it, and `tmp/freebuff/reports/review-G2-24.md:134` re-derived
"0 of 649 wave GUIDs appear in tunes or sound-instance bodies" independently with the same parser.

## A4 — "the sample inside a tune is picked by name/audition". **BROKEN**

The card's `Done:` clause asks for "every donor event and every chosen weapon's events listed with GUID
**and samples**"; the work answers `samples: UNKNOWN` for all 45 (`"donor rows with samples null: 45 / 45"`),
and the recommendation `a + c` carries the limit sentence. Closing the one-byte gap resolves 12 of 45
donor events with no other change, because the tune body already names its instances and the instance
already names its wave:

```
ev3  vehicles tune 122  slot [418]            jc3_vehicle_horn_car_05_loop
ev9  vehicles tune 30   slot [56,150,165,355] jc3_veh_land_premium_nitro_start / _loop / _jet_flame_loop / _stop
ev12 vehicles tune 0    slot [182,483,576]    JC3_wind_speed_chassi_rumble_eq / rough_terrain_suspension_rumble / gravel_skidding
ev13 vehicles tune 151  slot [31]             jc3_veh_land_start_fail_default
ev18 vehicles tune 90   slot [172]            jc3_veh_lave_chassis_spin_whoosh_cycle_2hz
ev19 vehicles tune 5    slot [99,522]         aston_martin_max_remix_start / _shutdown
ev29/31/34/36/41 (effects bank) slot [862]    jc3_phy_fire_car_small_debris_loop_01
ev32 effects tune 113   slot [1451]           jc3_vehicle_engine_smoking_hiss_loop
```

The evidence that this is the *right* mapping is not the parser but the semantics:

* the role `horn` resolves to a sample literally named `jc3_vehicle_horn_car_05_loop`;
* `chassis_spinning_sound` → `jc3_veh_lave_chassis_spin_whoosh_cycle_2hz`; `ground_roughness_sound_attached`
  → wind-rumble + rough-terrain + gravel skid; `engine_running_sound` → an engine start/shutdown pair;
* `exhaust_upgrade_nitrous` → slots **56, 150, 355** (+165), and `Tools/scripts/_apply_audio.py:13` is
  `JOBS = [(56, …start…), (150, …loop…), (355, …stop…)]` — the three slots test-060 swapped by audition and
  spectral ranking in MODLOG §71. The independent method lands on the same three.

Consequences that follow mechanically (not tested here, listed so they are not lost): `T-16`'s slot method
("`chosen` stays UNKNOWN for the audition to settle"), `Working/Translation/T12_AUDIO.md:27,268` which cite
"G2-24 §5", `USAGES.md` §7's UNKNOWN (2) "event → sample index", the §12 row's `samples` wording, and the
MODLOG entries at 11640-11648 and 12214-12230.

## A5 — the `WAVS` format row. **BROKEN**

`JC3_AUDIO.md` §1:

> | waves | `WAVS` -> `WAV `: a u8 index + 16-byte GUID per sample slot |

Everything in that cell is off: 650 children (one `LCNT` + 649 `WAV `), the first field is not an index but a
GUID byte, the layout is `GUID | 0x08 | 0 | u16 slot | 0`, and the sample slot index sits at `[22:24]` where
nobody looked. The same misparse is what makes the §5 probe return 0 (A3) and what the format table's
"waves" row has taught every downstream reader. It also means the `index` field in
`JC3_AUDIO_EVENTS.json → banks.*.waves` is meaningless (it is `GUID[0]`), and `fev_waves()` returns only 649
of the 650 children without saying that it skipped one.

## A6 — "the chain stops at the tune". **WEAK**

`§5` states the stop universally ("So the chain stops at the event GUID + ordinal"). It is true for most
tunes and false for a resolvable minority:

```
tunes referencing an instance id (16-B windows at 4-byte alignment, offset >= 20): 103 / 257
tunes referencing nothing recognisable:                                            154 / 257
tune body sizes with no reference: 68 B ×53, 66 B ×49, 42 B ×40, 92 B ×5, 121 B ×2, 116 B ×2, …
```

The 42/66/68-byte bodies carry the two GUIDs and a short child block that this reader does not parse
(`tune 87`, 68 B: `5c95f02b… | 3e448c6d… | 03001800 f485e62371cebd44af23f7fc0fcbc1b9 00000000 ba0a0000 …`).
So the honest statement is "stored for 103 of 257 tunes (12 of the donor's 45), unresolved for the rest",
not "not stored". The card's phrasing makes a parser limit sound like a property of the file, which is the
R4 failure mode (`decoded` vs `inferred`) in the opposite direction: an inference stated as an absence.

## A7 — the 45-event frame. **WEAK**

The donor card reads "`sound/fmod_banks/vehicles.bank`, donor `.ee.fmod_guids`" and the doc says "the donor
pins 45 events". Measured across every `v0300` build in the index:

```
v0300_…_civilian_01.ee              count 45  bytes 758  banks ['vehicles','character','effects']
v0300_…_debug.ee                    count 45  bytes 758  banks ['vehicles','character','effects']
v0300_…_signature_preorder.ee       count 55  bytes 936  banks ['weapons_preorder','vehicles','character','effects']
```

The civilian build is the right donor for the *car*, so the 45 is faithfully measured. But the ship template
for the weapon work is the armed sibling (§2.1 of the backlog: the signature car is the one with
`CMissileWeaponBase`, and `G2-12` diffs exactly that build), and it pins **10 more** GUIDs in
`weapons_preorder` — i.e. the weapon-fire carriers that `AUD-5` and route c need are outside the "every
donor event" frame. `w618`'s own `fire` GUID (`84232d53…`) is one of them, and it is in `weapons_preorder`,
not in `effects`/`vehicles`.

## A8 — `LandAudio` = 2 members, "the whole vehicle-side audio parameter set". **HOLDS / WEAK**

Re-derived over the 232 decoded entity modules:

```
audio-ish modules: {'LandAudio': 145, 'BoatAudio': 35, 'AirAudio': 41, 'TrainAudio': 12}
LandAudio member-count distribution: {2: 145}
member paths seen in any LandAudio: ['max_rpm', 'min_rpm']
donor LandAudio rows: [('min_rpm', 1000), ('max_rpm', 10000)]
```

So "2 members" is exact for `LandAudio` on every entity that has one, and the donor's two values are 1000.0 /
10000.0 as printed. Two generalisations around it do not hold:

* **"the whole vehicle-side audio parameter set"** (MODLOG done entry) is wrong: the other three vehicle
  audio modules carry `rpm_mix`, `velocity_to_rpm` (35 boats), `rpm_ramp_up_speed` / `shutdown_rpm` (41 air),
  `rpm_smoothing`, and full `min_rpm_vs_speed` / `max_rpm_vs_speed` control-point curves (12 trains). A car
  that needs a speed→RPM curve has fleet precedent the card does not mention.
* **the values are per-vehicle tuned, not a schema constant**: `min_rpm` mode is **500** (122 of the fleet),
  `max_rpm` mode is **5000** (88); the donor's 1000/10000 is near the top of the land range. That is
  consistent with a high-revving sports car and argues *for* the RPM-window reading, but it also means the
  pair cannot be copied onto the Batmobile as "the" audio range without a decision. The doc's own
  "their runtime role UNKNOWN" is the correct hedge.

## A9 — horn. **HOLDS**

```
sound objects per entity whose name has 'horn': {0: 54, 1: 178}
horn object classes: {'SAttachedEffect': 178}   usages: {'-962520269': 178}
```

Exactly one per vehicle on the 178 that have one, one class, one `Usage` hash — i.e. a per-model attached
effect, as the md says, and 19 distinct `Sound` GUIDs (the doc's number; my count agrees on objects and
entities). The R5 caveat is the one the md already writes down: the evidence is the object's **name** and its
`Sound` value, not a behaviour. All 178 share a single `Usage` hash, so the object is *a* per-model effect;
that the player's horn input fires it is code, which §11 (5) states as a Q-1 probe. No overreach there.

## A10 — radio = 0. **HOLDS (scoped)**

I searched the raw text of all 232 `detail/*.ee.json`, case-insensitive, anywhere in the file — not only
`Sound`-carrying objects:

```
Sound objects named radio: 0
any 'radio' substring anywhere in the 232 detail JSONs: 0
```

The negative is real and stronger than the md claims (it says "0 `radio` objects"; it is 0 *anywhere*). The
scope is the `.epe` graphs; the entity modules (`land_audio` etc.), the UI, and the `music_*`/`diegetic*`
banks are not scanned — which is why the md's "where the radio lives is UNKNOWN" is the right sentence and
should be kept if the number is ever quoted as "JC3 has no radio".

## A11 — "the fleet" = 232 decoded builds. **HOLDS**

```
vehicle .ee in index: 233    cached: 232    missing: 1
  MISSING editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/…_custom_mm230.ee
```

232/233 is not a sample; the one gap is an air vehicle, so no land-vehicle claim is affected. (This is the
opposite of G2-21's fleet frame, where 232 of 314 left a real gap. Here the word "fleet" is earned.) Minor
wording: `.epe` files number 232, `.ee` 233, `.vmodc` 207 — the card should keep saying "232 decoded graphs",
which it does.

## A12 — route b impossible. **HOLDS on the search, WEAK on the reasoning**

```
fev/fsb/fdp/fspro/bank/banklist paths in index: 56   (0 .fev, 0 .fsb; 54 .bank + 2 master.banklist entries)
master.banklist 434 B: master.bank, master_strings, vehicles.bank, gui.bank, vehicles_train, … weapons_preorder, weapons.bank, …
```

`no .fev ships` is measured and true. The two clauses that carry the *impossibility* are not file facts:
"nothing here can author its contents" is a statement about tooling (a negative this project cannot prove
from the index), and "`master.banklist` is a plain 26-line text list, so the loader can be told about another
file" is a loader inference in the *optimistic* direction placed in the *pessimistic* route — the same
unverified-loader question as A13, used here to argue route b is only almost-possible. The recommendation
(`a + c`) is not affected, because it does not need b.

## A13 — route a "possible, proven by test-060". **WEAK**

Two different claims share the word "proven":

* **File level — holds.** `_apply_audio.py` replaces `fsb.samples[idx].data` in place with a same-length
  payload, re-parses (`len(fsb2.samples) == 649`) and re-decodes each swapped stream through vgmstream
  (`verify #%d`). §71 records "Bank byte-size identical (210,781,376), vgmstream re-decodes all three".
* **Loader level — unverified.** "the bank is loaded as a loose override at `sound/fmod_banks/vehicles.bank`
  with no `.toc` (MODLOG §71)" is a parenthetical in §71 written in the same session, and §71's own next
  line is the *unrun* oracle: "ORACLE: hit nitro -> Batmobile afterburner whine instead of stock; if
  silent/crash, bank falls back to archive". test-060's result line reads "LOADS, ALIGNED, **QUIET**", and the
  user's quoted answer is only about wheels. The project says so itself, later and plainly
  (`MODLOG.md:11846`, T-11): *"no game was launched (R6), so the in-game result of the test-060 swap is
  unverified."*

So route a is "possible" as a file operation and "unproven" as a shipping route. The md should carry that
split, because the whole AUD plan rests on it.

## A14 — the PCM/swap rule. **WEAK**

`§10` route a: "every donor sample is 16-bit PCM at 48 kHz (census), so a replacement must be PCM16/48 kHz
and exactly the original frame count". Re-derived from the stored census and the FSB header:

```
samples 649  encodings {'16-bit Little Endian PCM': 649}  rates {48000: 649}
channels {1: 506, 2: 143}       looped 22
sum(frames*channels*2) = 153,406,896   data_bytes = 153,439,744   equal: False  (32,848 B unexplained)
```

Three problems, one material:

1. **Channel count is a required third constraint** and it is missing. 143 of 649 slots are stereo; a
   replacement padded to the right *frame* count with the wrong channel count changes the byte length (or
   plays at the wrong speed), and `_apply_audio.py` hard-codes mono (`hlen = payload_len - ns * 2`). None of
   the 12 slots A4 resolves is stereo, so the live nitro/horn work is safe — but the rule as written will
   break on the first stereo slot anyone targets.
2. **"every donor sample"** is a category error: at the time of writing the donor's samples were `UNKNOWN`
   (45/45 null), so what the census describes is every sample *in the bank*. The premise the rule needs is
   "every slot is PCM16/48 kHz", which is what was measured.
3. The 32,848 B gap means the payload arithmetic does not close; it is consistent with per-sample alignment
   padding, but "same frame count" is the only rule the measurement actually supports.

## A15 — 23 named / 22 unnamed. **HOLDS**

I searched the decoded donor `.epe` JSON text for all 45 GUIDs in both hex spellings, not just `Sound`
fields:

```
GUIDs present anywhere in the decoded donor .epe JSON: 23 /45
present but NOT in a Sound field: 0 []
GUIDs present in the entity module rows: 0
```

So the 23/22 split is right and the 22 really are absent from the graph (their consumer is code or a
preload path — note `sound/preload.fmod_guids` exists as a separate global block in the DLC tree, which is
the shape of the missing consumer). The md's "Whether that is a second, native consumer is UNKNOWN" stands.

## A16 — "the Working copy equals the archive entry". **WEAK**

```
entries for vehicles.bank: [('archives_win64/game1', 210803872), ('patch_win64/game5', 210781376)]
  archives_win64/game1: FEV 56/50  samples 649  data 153,463,072
  patch_win64/game5:    FEV 56/50  samples 649  data 153,439,744
```

The census, the 649-sample table and every byte offset a swap would use describe the **patch** copy
(210,781,376 = the card's number). The check reads like an archive-vs-working integrity assertion, but it
is an identity to one of two shipped files that differ by 22,496 B and 23,328 B of FSB data. If the engine
picks the `archives_win64/game1` copy (or a loose file overrides neither, or both), the sample indices a swap
targets are from the wrong file. Nothing in this card tests which copy wins — that is the same open loader
question as A13, and it should be named, not implied by the word "archive".

## A17 — numbering conventions. **WEAK**

Nothing in the md states a base. Measured:

* `JC3_AUDIO_EVENTS.json → samples.list` is **1-based** (`index` of the first row is 1, name
  `jc3_veh_bmw_m5_start`); the md's §6 `#` column uses that numbering.
* the `WAV ` slot field (`body[22:24]`) is **0-based** (0…648), and `_apply_audio.py`'s `JOBS` and
  `fsb.samples[idx]` are 0-based, verified by its own `-s str(idx + 1)` decode call.
* so "slot 56" (0-based) is row `#57` of §6. test-060's "#56/#150/#355" are 0-based slots, i.e. rows
  #57/#151/#356.

Everything agrees once the convention is written; without it, any human or model copying a resolved slot
number into the md's table or into `_apply_audio.py` is off by one, and the adjacent samples are unrelated:

```
row #57  = slot 56   ch 1  35,737 frames  loop -       jc3_veh_land_premium_nitro_start
row #56  = slot 55   ch 1  23,756 frames  loop -       jc3_veh_generic_undercrrg_impact_light_01
row #419 = slot 418  ch 1  71,978 frames  loop 34934  jc3_vehicle_horn_car_05_loop
row #418 = slot 417  ch 1  24,901 frames  loop -       jc3_veh_gen_truck_chassis_clunk_13
```

A one-off therefore swaps the wrong sample *and* gets its loop state wrong, which decides whether the
same-frame-count rule is even applicable. This is exactly the "unit or coordinate convention" class of
silent assumption.

## A18 — route c's 1,228 named samples. **HOLDS the number, WEAK the method**

```
weapons.bank 177,586,080 B: samples 1228 names 1228   ('jc3_w153_shotgun_automat_reload_clip_in_02', …)
weapons_preorder.bank 6,445,152 B: samples 29 names 29
weapons.bank: FEV 56/50  WAV 1228  idx==pos 1228/1228  instances 5460  wave-match 1228/1228
```

1,228 is correct, and the same corrected wave/instance layout holds in the weapon banks, so "the same payload
swap applies there" is supported. But in the generator the number is a **literal inside an evidence string**
(`jc3audio.py` route c: `"weapons.bank holds 1228 named samples …"`) that no probe backs, while §7 says "the
weapon banks were not probed for this card" — a typed count and a stated non-measurement in the same
document (R11: counts are generated, never typed). It happened to be right; the gate cannot tell.

## A19 / A20 / A21 / A22 — the remaining claims. **HOLDS**

* **A19** `w602`/`w603`: one index path each, `.wtunec` only (14,224 / 14,223 B) — no `.ee`, no
  `.fmod_guids`, and 171 tune members with 0 audio members (`AUDIO_MEMBER` regex over the decoded tune).
* **A20** `w618`: 10 GUIDs over `['weapons_preorder','effects']`, `Sound` of `fire`/`fire2..4` =
  `84232d53-cea8-2d44-86a1-b92ff2402743` = `guids[0]`, and that event is found in **`weapons_preorder`**
  (event ordinal 2 there). `w619`: `fire_sound_combi` = `53e8d43a…` = `guids[0]`, also in `weapons_preorder`
  (ordinal 1).
  The `Sound`-is-first-GUID rule re-derives for both.
* **A21** no event name: 257/257 `EVTS` children are `(EVTB, LIST)` with no name string; printable runs 2,333
  (≥3) / 1,654 (≥4), matching the rework's corrected numbers; 0 of the role names occur; and 0 of the 649
  FSB sample names occur anywhere in the PROJ region either, so the reverse lookup is not stored as text.
* **A22** container census: 257 events / 257 tunes, bijection true, 1,674 instances (1,674 distinct instance
  ids), 969 params / 49 distinct names, 649 samples / 649 FSB names, 22 looped, one rate (48 kHz), 0 `TLNT`.

## A1 / A2 — the two identity claims. **HOLDS / WEAK**

**A1 holds, and it had to be tested** because the "stored twice" claim would be circular if the tune chunk
merely repeated the event's own GUID. It does not:

```
tune_guid == event_guid (same 16 B in both fields):       0 / 257
tune.tune_guid equals the owning event's own GUID:        0 / 257
event body[32:48] == own guid:                            0 / 257
offset of tune guid in event body: {32: 257}, unique-in-body: 257
tune guids that are also an event guid: 0 of 257; distinct tune guids: 257
```

and by hand for the horn: `event 255` body = `fd69c63c…` (its own GUID) + zeros + `7b1ad299…` at 32;
`tune 122` body = `7b1ad299…` + `fd69c63c…` at 16. Two distinct identities, correct labels, both directions.
The MODLOG's rework claim "stronger than the review" is justified.

**A2 is weak as evidence.** "45/45 resolved to a tune index" is entailed by the bijection: `TLNS` holds one
tune per event, `tune_event_bijection` is true, so *any* event found in a bank resolves — 45/45 is another
way of saying "45/45 are in a bank" (`in_a_bank == 45`). It is a consistency check dressed as a finding; the
§12 row leads with it. It costs nothing and it is true, but a reader will over-value it.

---

## What would close the gap cheaply

1. **Fix `fev_waves()`**: `guid = body[0:16]`, `slot = u16 at body[22:24]`; then rebuild §1's waves row,
   §5's two instance probes (`0/649` → `649/649`), the §3 `samples` column, §10's limit sentence, and the
   `invariants()` assertion that currently enforces the wrong zero.
2. **Publish the resolved samples for the donor** (12/45 now: horn 418, nitro 56/150/165/355, engine
   99/522, …) and mark the other 33 as "tune does not reference a sound instance in this reader" rather than
   "not stored"; then re-point T-16/`T12_AUDIO.md`/`USAGES.md` §7 at the resolved slots instead of "audition".
3. **State the numbering convention** (md `#` = 1-based vgmstream; WAV slot and `_apply_audio.py` JOBS =
   0-based) in §6 and in the route-a rule, and add the channel count to that rule ("PCM16, 48 kHz, same
   channel count, same frame count").
4. **Say which file wins**: name the patch copy in the census assertion (A16) and split route a into
   "payload swap proven" vs "loose override unverified, per MODLOG:11846".
5. **Add the armed build to the event frame**: `…_signature_preorder.ee` pins 55 GUIDs / 4 banks, and the 10
   extra are the `weapons_preorder` fire carriers AUD-5 and route c depend on.

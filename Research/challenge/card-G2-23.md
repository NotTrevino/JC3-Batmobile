# Assumption challenge — backlog card G2-23 (nitro FX and audio carriers)

Read-only pass over the finished card. What I read: `GRAB_BACKLOG.md` §0.5 (R1–R14), the G2-23 card
(§7, line 714), its §12 row (line 1306), the MODLOG `G2-23 · Nitro FX and audio carriers — intended
change` (line 11713) and `— done` (line 11803) sections, the outputs `Research/JC3Grab/USAGES.md` §6
("The nitro chain: input -> effect -> sound event -> sample") + `USAGES.json` `nitro` block, the
generator `Tools/scripts/jc3usage.py` (nitro pass + `assertions()`), and the evidence the card relied
on: `E:/Modding/JustCause3/_grab/entities/*.ee.json` (232), `E:/Modding/JustCause3/_grab/detail/*.json` (232 `.epe`
graphs), `Research/JC3Grab/FX_TABLE.jsonl`, `INDEX.jsonl`, `JC3_AUDIO_EVENTS.json`, the audio reader
`Tools/scripts/jc3audio.py`, test-060's `Tools/scripts/_apply_audio.py`, and the local bank copy
`Working/Audio/jc3bank/sound/fmod_banks/{vehicles,character,effects}.bank`.

Constraints honoured: no game launched, nothing written into `D:/Games` (the bank was read from the
project's own `Working/Audio/jc3bank/` copy, not the install), nothing committed, no secret read, no
`--write`, no file touched except this one.

The card's Done check re-run today (exit status captured without a pipe):

```
$ python Tools/scripts/jc3usage.py --check
PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named usages (346 rows,
885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro -> EngineNitro/
dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX rows 57187
exit=0
```

So the card's numbers reproduce. This report is about what those numbers *mean*.

---

## VERDICT

**Two BROKEN, six WEAK, seven HOLDS.** The chain is **stronger than the card says at its effect edge
and weaker than the card says at its input edge.** The one hard error is that `USAGES.md` §7 declares
the object `Effect` hash → `.effc` edge UNKNOWN, and calls the hash function UNKNOWN; both are false
with files already in this repo. `Effect` = 3518298851 is the Jenkins hash of the full path
`effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc`, and **all 181 distinct** object
`Effect` values in the fleet (6,958 object instances) resolve that way — and that exact `.effc` is
embedded in the donor's own container. The card then says "the 9 `*nitrous*.effc` files are a
name-only candidate"; there is no candidate left: the donor's nitro effect has a name and a path.

The other break is the middle of the chain that the card presents as decoded for the donor: the
donor's `EffectAttachments` module binds exactly one usage, `HeadLights`. The
`EngineNitro -> dynamic_nitrous` binding the card leans on exists on **14 vehicles, none of them a
car** (2 armoured trucks, 4 bike families, 1 helicopter family). It is a fleet inference from a class
the donor does not belong to, and the md's §7 UNKNOWN list never says so.

What holds is the part a build actually uses: the donor's own `arcade.nitro_boost` values, the usage
value on the donor's two nitrous exhaust objects (`EngineNitro`'s hash, recomputable), the sound GUID
(a real, unique `vehicles.bank` `EVTS` event at ordinal 249, 195 B), the sample family (the only
nitro-named set in any of the three banks) and the "no `.ee`/`.epe`/`.fmod_guids` edit needed"
conclusion. Seven of the card's ten nitro assertions are regression pins of its own measurements, not
independent checks, so `--check` proves reproducibility, not truth.

| # | assumption | verdict |
|---|---|---|
| A1 | the donor's `arcade.nitro_boost` values are the donor's own, not fleet-inferred | **HOLDS** — read straight out of the donor's `CustomLandGlobal` (61 rows) |
| A2 | `nitro_boost` is *the* nitro because of its name and "what it does to the car" (R5) | **WEAK** — its twin `heat_boost` is on the same 145 builds with a *larger* `extra_top_speed`; nothing in the data links either block to `EngineNitro` |
| A3 | `push_force` is newtons, `extra_top_speed` is km/h, `boost_blend_time` is seconds | **WEAK** — all three inferred; the schema writes `_kph` when it means km/h (`punch_speed_kph`, `nitro_refill_min_speed_kph`) and this member has no suffix |
| A4 | "the 5 `arcade.*` blocks on 145 of 232 vehicles" is the fleet's nitro input | **WEAK** — 220 of 232 builds carry a nitro block, in three different schemas (land 145 / air 41 / sea 35); 145 is the land third |
| A5 | the module binds the donor's `EngineNitro` usage to `dynamic_nitrous` | **BROKEN** — the donor's module binds only `HeadLights`; the binding exists on 14 builds, 0 of them cars |
| A6 | the object `Effect` 3518298851 is unnamed and its `.effc` edge is UNKNOWN | **BROKEN** — it is `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc`; 181/181 object `Effect` values resolve by path hash |
| A7 | "absent from every module `all_effects[]`" is evidence about this hash | **WEAK** — 0 of 6,958 object `Effect` values appear there; the two fields are different hash spaces (path vs name), so the absence is vacuous |
| A8 | the object's `Sound` GUID is the nitro sound event | **HOLDS** — 202 objects / 172 vehicles, 10 names, all `*nitrous*`; GUID unique in `vehicles.bank` |
| A9 | `vehicles.bank` `EVTS` ordinal 249 is decoded, not positional | **HOLDS** — ordinal matched by 16 raw GUID bytes, unique across all three banks; tune 30 repeats the event GUID at offset 16 |
| A10 | the three samples are 56 / 150 / 355, 0-based, chosen by name | **HOLDS** — the only nitro-named samples in any bank; name table verified 0-based and contiguous |
| A11 | "the same set test-060's `_apply_audio.py` swaps" corroborates the pick | **WEAK** — circular: test-060 chose the same three *by name* (MODLOG §71), and the assertion is a hardcoded pin |
| A12 | one event carries the whole start/loop/stop set | **WEAK** — nothing stored links event 249 to any sample; the tune body carries none of 56/150/355 |
| A13 | no `.ee` / `.epe` / `.fmod_guids` edit is needed | **HOLDS** — event, usage and both objects are already on the donor (and the `.effc` is in its container) |
| A14 | which control fires nitro is UNKNOWN | **HOLDS as UNKNOWN**, reason WEAK — `settings/keymap_gamepad.bin` and `scripts/modules/input.xvmc` exist in the index and were not decoded |
| A15 | the Done check proves the chain | **WEAK** — 10 of 30 assertions are G2-23 pins of measured values; one pins a historical script's indices |

Counts: 7 HOLDS, 6 WEAK, 2 BROKEN.

---

## A1 — the donor's `arcade.nitro_boost` block is the donor's own. **HOLDS**

The values in `USAGES.md` §6 (`torque_multiplier` 2, `grip_multiplier` 2, `push_force` 15000,
`boost_blend_time` 0.2, `extra_top_speed` 40; upgraded 20000 / 80) are stated with the file they came
from, so the first test is that they are on *this* entity and not a fleet default:

```
$ python -c "... donor modules['CustomLandGlobal'].rows ..."
rows 61
arcade.nitro_boost.torque_multiplier = 2
arcade.nitro_boost.grip_multiplier = 2
arcade.nitro_boost.push_force = 15000
arcade.nitro_boost.boost_blend_time = 0.200000003
arcade.nitro_boost.extra_top_speed = 40
arcade.heat_boost.torque_multiplier = 2
arcade.heat_boost.grip_multiplier = 1.5
arcade.heat_boost.push_force = 0
arcade.heat_boost.boost_blend_time = 0
arcade.heat_boost.extra_top_speed = 80
arcade.nitro_boost_upgraded.torque_multiplier = 2
arcade.nitro_boost_upgraded.grip_multiplier = 1.5
arcade.nitro_boost_upgraded.push_force = 20000
arcade.nitro_boost_upgraded.boost_blend_time = 0.200000003
arcade.nitro_boost_upgraded.extra_top_speed = 80
```

The block sits in the donor's own module
`…/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc`; the donor is one of
the 145. No inference in this step. One detail the card elides and a build would want: the `_upgraded`
twin is *not* uniformly stronger — `grip_multiplier` goes 2 → 1.5. The card lists only the push and
the top speed and says "twin", which reads as "more of everything".

## A2 — `nitro_boost` is the nitro, by name and behaviour (R5). **WEAK**

`USAGES.md` §6:

> `nitro_boost` is the nitro one by name and by what it does to the car: torque x2, grip x2, a
> 15,000 N push, 0.2 s blend, +40 km/h top speed

`heat_boost` sits in the same module with the same five member names, and on the member that would
separate them it is *larger*:

```
heat_boost:     torque 2  grip 1.5  push 0      blend 0    extra_top_speed 80
nitro_boost:    torque 2  grip 2    push 15000  blend 0.2  extra_top_speed 40
```

and the two blocks have exactly the same carrier set, so neither values nor presence can separate
them:

```
heat 145  nitro 145  upgraded 145  identical sets: True
```

Nothing in the decoded data connects `arcade.nitro_boost` to the FX or audio side. A fleet scan for
every module member whose name matches `nitro|nitrous|boost|afterburn|turbo` finds 64 distinct paths,
and the land block is never referenced from any of the others:

```
233 VehicleMisc full_nitro_refill_time
233 VehicleMisc nitro_refill_min_speed_kph
233 VehicleMisc full_nitro_use_time
233 VehicleMisc full_nitro_use_time_upgraded
145 CustomLandGlobal arcade.nitro_boost.*   (5 members)
145 Transmission nitrous_gears
41  AirGlobal nitro_boost.push_acceleration / extra_top_speed / boost_blend_time
35  BoatGlobal nitro_boost.prop_rpm_multiplier / prop_torque_multiplier / extra_top_speed
```

The nitro *tank* is on every decoded build and the card never mentions it:

```
full_nitro_use_time           4      (232 entities, 233 rows)
full_nitro_use_time_upgraded  8      (232 entities)
full_nitro_refill_time        2      (232 entities)
nitro_refill_min_speed_kph    20 (230×) / 15 (3×)
donor: use 4 / upgraded 8 / refill 2 / min speed 20    nitrous_gears 0
```

So "what it does to the car" is true of `heat_boost` too, and the discriminator is the *word*. Under
R5 that is exactly the failure mode the rule was written for (test-087: ram attack → defence): the
requirement "the car has a boost" is being mapped onto the member whose name sounds closest. The
values are still the right ones to copy (they are the donor's), but the *explanation* "this is nitro"
and the build rows that inherit it (`T-B2`/`T-B3`: `extra_top_speed` 40 → 43.2 km/h) rest on a name.
A 4-second tank plus a separate `heat_boost`/`nitrous_gears` set on the same 145 builds is at least as
consistent with `heat_boost` being the sustained boost and `nitro_boost` a one-shot.

## A3 — newtons, km/h, seconds. **WEAK**

The card writes "15,000 N push", "+40 km/h", "0.2 s blend". None of the three units is in the file.

- `push_force`: the donor's `RigidBody.mass` is 975 kg, so 15,000 N ⇒ ≈15 m/s² (≈1.6 g) — plausible,
  and 15,000 is *constant on all 145 builds*, so the census offers no variance to test the unit
  against. Fleet mass ranges from ~500 kg (bikes) to the tank class, so the same 15,000 gives 30 m/s²
  on a moped and 1.5 m/s² on a tank; both readings survive.
- `extra_top_speed`: fleet values 30 / 40 / 60 (145 builds). As km/h those are sensible boost
  magnitudes; as m/s, +40 m/s = +144 km/h on an old tractor. Magnitude favours km/h. But the schema
  *does* write the unit when it means it — `arcade.turbo_jump.punch_speed_kph`,
  `arcade.turbo_jump.top_speed_kph`, `VehicleMisc.nitro_refill_min_speed_kph` — and
  `extra_top_speed` has no suffix. The file's own convention is therefore *contrary* evidence that
  this member is km/h, which the md does not record.
- `boost_blend_time`: 0.2 on all 145 (0 in `heat_boost`), `turbo_jump.punch_delay_time` 0.1. Seconds is
  the only reading that makes 0.1–0.2 meaningful; nothing names it.

Same fleet, one calibration point that the `torque_multiplier` name *is* behaviourally a multiplier:
the values scale inversely with base power, which is what a multiplier would do —

```
v0506_car_solar_oldtractor  torque 40  grip 1.2  push 15000  top 60
v3500_bike_solar_oldmoped   torque 4   grip 2    push 15000  top 40
v0005_car_autostraad_minetruck torque 5 grip 1.2 push 15000  top 40
donor sportsmuscle          torque 2   grip 2    push 15000  top 40
```

**WEAK**: magnitudes are plausible, the units are inferred, and the one convention in the schema that
could settle it points the other way. A one-line "unit by magnitude, `_kph` convention absent —
confirm in Q-2" would have been honest; the md states the units as if read.

## A4 — "145 of 232" is presented as the fleet's nitro input. **WEAK**

`USAGES.md` §6:

> **The input half is module data, not code.** `CustomLandGlobal` carries five `arcade.*` blocks …
> on **145 of the 232 decoded vehicles**.

The count is right (145, reproduced), and the donor is land, so nothing downstream breaks. But it is
the *land* third of the fleet's nitro data, not "the input half":

```
land (arcade.nitro_boost.push_force)      145
air  (AirGlobal.nitro_boost.push_acceleration)   41
sea  (BoatGlobal.nitro_boost.prop_rpm_multiplier) 35
union                                     220 of 232   (overlap land∩air = 1)
no block at all                            12  — all v5601/v5602/v5603 monorail trains
```

and the three schemas do not agree on the members (`push_force`+`grip_multiplier` on land,
`push_acceleration` on air, `prop_rpm_multiplier`+`prop_torque_multiplier` on sea). So "the input half
is module data" is true and interesting; "on 145 of 232" is the land-only slice, and quoting it as the
fleet figure invites the same error G2-17/G2-21 hit. Related framing: the same population that made
the earlier "sound-only 33" oddity is exactly the sea family — every one of the 172 sound carriers has
some nitro block, i.e. the two halves do line up once all three families are counted.

The denominator is also a sample: the census reads the 232 base-mount entity builds.

```
index vehicle .ee            314  = 232 base mount + 81 dlc + 1 patch
entity cache                 232   (the base-mount set)
not decoded                     82  = 81 DLC builds + the patch override
                                   v2602_helicopter_urga_lightassault_military_01_custom_mm230.ee
```

`FX_TABLE.jsonl` (which G2-22/23 also use) *does* include DLC containers, so within one card the FX
census and the entity census cover different fleets. "232 decoded vehicles" is accurate; "the fleet"
is not.

## A5 — the donor's module binds `EngineNitro` → `dynamic_nitrous`. **BROKEN**

`USAGES.md` §6:

> … the module space names 397752766 `dynamic_nitrous` as the effect the `EngineNitro` usage selects
> (and `EngineNitro` itself on 4 planes). So the module picks `dynamic_nitrous`, the object carries a
> second, unnamed effect hash …

Read as a fleet sentence, true. Read as the donor's chain — which is what the section is titled — it is
false. The donor's `EffectAttachments` module has one usage row:

```
usage_effects
usage_effects[0].usage.string   HeadLights
usage_effects[0].usage.hash     3551535361
usage_effects[0].effect_indices A[int32]
(697 rows total in the module; no other usage_effects[i])
```

Fleet-wide the row exists on 18 builds, and its effect list is two effects:

```
EngineNitro  ->  EngineNitro     (4 builds: v4600/v4800 planes)
             ->  dynamic_nitrous (14 builds: v0001 armouredtruck ×2, v3000 trials bike ×3,
                                  v3401 mugello bike ×2, v3502/v3503 solar bikes ×4,
                                  v2200 capstone helicopter ×3)
```

**Zero cars, zero of the donor's family.** So for the donor the effect-selection edge is *not decoded*:
what is decoded is the `.epe` object's own `Effect` field (A6) and a fleet naming from a class the
donor is not in. The card's §7 UNKNOWN list does not include this, and the done check encodes the
fleet claim as a pass condition (`("EngineNitro` links effect `dynamic_nitrous`", True, True)`), so the
gap is invisible to `--check`. G2-22's own row is more careful than G2-23 here ("donor module lists
only `HeadLights` but its `.epe` attaches `exhaust_upgrade_nitrous*` under `EngineNitro`").

## A6 — `Effect` 3518298851 is unnamed and its `.effc` edge is UNKNOWN. **BROKEN**

`USAGES.md` §7:

> **effect name -> `.effc` path.** … no decoded file maps one to the other: of 849,942 string values
> in the 232 `.epe` graphs, exactly **0** name an `.effc` / `.ctunec` / `.trim`. UNKNOWN - it is a
> lookup the engine holds, not data in these files.
>
> **hash function.** UNKNOWN; hashes are read from the files where the string sits next to them,
> never recomputed, so no identification is needed.

Both sentences are wrong, and the repo already had the tools to show it. `Tools/scripts/rbmhdr.py`
(dates 2026-10-22, six days before this card) ports `StringHelpers.HashJenkins`; `jc3index.py` relies
on it to name all 81,952 archive rows — *"the game finds a file by hashing its VFS path (Gibbed's
Jenkins lookup3 over the ASCII path with FORWARD slashes)"*, and the index accepts a name only when
`hash_jenkins(path)` is an exact tab hash. That is the same "space" the object field is in:

```
$ hash_jenkins(b'effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc')
3518298851            # == the donor objects' Effect (-776668445, 0xD1B4FAE3)
```

And it is not one lucky hash. Every distinct object `Effect` value in the 232 graphs resolves to a
path in `FX_TABLE.jsonl` (57,187 rows, 1,533 distinct paths):

```
object Effect values 181   resolved to an FX path 181   (6,958 object instances)
  e.g. 369 2308137782 effects/jc_vehicles/damage/dmg_fire_engine.effc
       341   55563211 effects/trails/car_explode_trail_01.effc
       264 1681124184 effects/jc_vehicles/collision/break_impact_sm.effc
```

The other direction is what the card mistook for a puzzle — module `all_effects` hashes are *name*
hashes, not path hashes:

```
module effect name-hashes              78 distinct
  of which resolve to an FX path        0
name→hash pairs (all_effects)          78 ; hash_jenkins(name) == hash : 77 (the 78th is ''→0xDEADBEEF)
object name→name_hash pairs            69,020 ; Jenkins match 69,020
hash_jenkins('dynamic_nitrous') = 397752766      (the module effect)
hash_jenkins('EngineNitro')    = 4197885156      (the usage)
```

So the two hash spaces are (a) effect **names** and (b) `.effc` **paths**, and the card's `Effect` hash
is in (b). It names `car_cycle_base_dual_nitrous.effc` — the *dual* exhaust, which matches the donor's
two objects (`exhaust_upgrade_nitrous`, `exhaust_upgrade_nitrous2`), and that file is embedded in the
donor's own container, which the card never checked:

```
$ ... FX_TABLE rows where container contains v0300_car_kensington_sportsmuscle ...
donor FX rows 470, distinct paths 168
donor nitrous rows:
  effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc  <- civilian_01
  effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc  <- debug
  effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc  <- signature_preorder
(17 containers carry that .effc fleet-wide; 9 distinct *nitrous*.effc paths exist, as the card says)
```

T-17's build row (`t17_fx.py`, `match=["exhaust/car_cycle_base_dual_nitrous"]`, `trigger="EngineNitro"`)
guessed the same file from the other end; with this hash the two ends join, and the card's UNKNOWN #3
in MODLOG ("object `Effect` hash -> `.effc`") can be closed. The name→path direction for *named*
module effects (`dynamic_nitrous` → a path) remains open — nothing here maps the 78 name hashes to
paths — so the card's UNKNOWN is only half closed, but the half it named for the donor is.

## A7 — "absent from every `all_effects[]`" is evidence. **WEAK**

Recomputed exactly: over 232 caches, 9,230 `all_effects[].effect.hash` rows, 78 distinct values; the
target is absent. True — and meaningless as a discriminator, because *no* object `Effect` value is in
that set:

```
object Effect instances 6,958   in a module all_effects[]: 0   absent: 6,958
```

The card treats the absence as a finding ("…and that hash appears in **no** `all_effects[]` … so the
object hash -> `.effc` edge stays UNKNOWN"), i.e. it read a space difference as a missing link. The
honest sentence is the one A6 proves: module `all_effects` hashes are effect names, `.epe` object
`Effect` fields are `.effc` path hashes, and the two never intersect by construction. Combined with
A5, the section's "two hash spaces, and only one is named" is actually *three* spaces (usage names,
effect names, effect paths).

## A8 — the `Sound` GUID is the nitro event. **HOLDS**

The link is decoded (the object's `Sound` field on an object whose `Usage` is `EngineNitro`), and the
fleet agrees: 202 objects / 172 vehicles, every one a nitrous-named exhaust, no counter-example.

```
sound objects 202  vehicles 172
names: exhaust_upgrade_nitrous 154, dynamic_exhaust_upgrade_nitrous 14, exhaust_upgrade_nitrous_r 13,
       exhaust_left_upgrade_nitrous 5, exhaust_right_upgrade_nitrous 5, exhaust_upgrade_nitrous_b 3,
       exhaust_upgrade_nitrous2 2, exhaust_upgrade_nitrous_left 2, exhaust_upgrade_nitrous_right 2,
       exhaust_upgrade_nitrous_l 2
```

The card's §6 lists six of these ten (summing to 194) under a "202 objects" headline; the missing 8 are
the `_l`/`_left`/`_right` variants plus 2 `…nitrous2` objects. Minor, but the card elsewhere says
`exhaust_upgrade_nitrous2` has "no `Sound`" — true *for the donor's object*, false fleet-wide (2 have
it). The classification is by object name, which is name-based; it is nevertheless a whole-fleet
consistency check with zero exceptions, and it is corroborated on the audio side by an RTPC named
`nitrous_active` in `vehicles.bank` (61 `PRMS` instances), so **HOLDS**.

## A9 — `EVTS` ordinal 249 is decoded, not positional. **HOLDS**

The card's number could have come from matching the GUID list order in the `.ee.fmod_guids` to the
bank's event order, which would be an inference. It did not; `jc3audio.fev_events` reads the 16 GUID
bytes out of each `EVTB` body and `nitro_chain` matches the object's GUID to them:

```
$ ... per bank: events, hits of f74ea43ba8ac4548ad27b92fd40a516d ...
vehicles events 257 hits [(249, 195, 'f74ea43ba8ac4548ad27b92fd40a516d')]
  tune: [{'index': 30, 'tune_guid': '20bf6f754f551d44a092042a3b30a8a5', 'event_guid': 'f74ea43ba8ac4548ad27b92fd40a516d', 'bytes': 181}]
character events 193 hits []
effects events 579 hits []
```

Unique across all three donor banks, 195 B body, and the tune body repeats the event GUID at offset 16
(`20bf…a5` then `f74e…6d` in the raw hex), which is the independent 1:1 confirmation G2-24 documented.
This is the card's strongest step.

## A10 — samples 56 / 150 / 355, 0-based, by name. **HOLDS (the pick is forced)**

The name table was parsed from the local bank, not trusted:

```
samples 649 names 649 shdr 22100 namelen 23792 datasize 153439744
0   jc3_veh_bmw_m5_start
56  jc3_veh_land_premium_nitro_start
149 aston_martin_vantage_engine_shutdown
150 jc3_veh_land_premium_nitro_loop
355 jc3_veh_land_premium_nitro_stop
648 jc3_veh_land_doors_bus_modern_open_01
name offsets contiguous in order: True   offsets[0] = 2596 (= 4 × 649)
```

0-based is proven (the offset array starts at 2596 = 4×649, so string 0 begins immediately after it),
the names are not alphabetical, and the 1-based reading would land on `…undercrrg_impact_light_01` /
`aston…shutdown` / `f1_backfire_4` — i.e. an off-by-one would have been visible. The pick is also
*forced*: the family is unique and exists in only one of the three donor banks.

```
vehicles  FSB5 ×1  samples 649  nitro-named 4: 56, 150, 165 (jet_flame_loop), 355
character FSB5 ×1  samples 976  nitro-named 0
effects   FSB5 ×1  samples 1524 nitro-named 0
```

So within `vehicles.bank` there is exactly one nitro start/loop/stop set. Caveat the card should carry
and does not: the naming tier is `land_premium`, and the fleet's four `*_premium_01` entity variants
are a modern saloon, a racing supercar, a buggy and a spy boat — the donor is
`v0300_…_civilian_01`, and no donor module names a "premium" audio set (4 builds in 232 contain the
string "premium", all as entity-leaf suffixes). The samples are the only nitro clips the bank holds,
so the *choice* is safe; the *attribution* ("JC3 named these for this event") is a name reading. Also
unexplained: `shdr` = 22,100 B for 649 samples is 34.05 B/sample, so per-sample headers are not a
uniform 64/34-byte stride; the card's "649 samples" is the FSB field and matches the 649 names, but the
payload lengths its recipe needs come from the absent `fsb5` package (A15).

## A11 — "the same set test-060 swaps (asserted, not by hand)" is corroboration. **WEAK**

`USAGES.md` §6 and the MODLOG both offer the test-060 match as the independent check on the name pick.
It is the same reasoning twice:

- MODLOG §71 (test-060): *"`_apply_audio.py` swaps FSB PCM payloads in place … premium_nitro_start/
  loop/stop (#56/#150/#355, PCM16 mono 48k)"* — chosen by name, written down by name.
- `_apply_audio.py` JOBS are typed literals: `(56, …jc3_batmobile_start.wav)`,
  `(150, …EC2FD42B.wav)`, `(355, …EC2FD42B.wav)`.
- `jc3usage.assertions()` then pins `[56, 150, 355]` and `test060_matches_names: True`.

So the assertion proves the *script history* equals the *name set*, which is a tautology once both
came from the same three names. The independent evidence is A10's uniqueness argument, not this.
(Two smaller points: the stop slot reuses the loop WAV's tail, `-0.756` — a build detail, not data;
and `_apply_audio.py` cannot be re-run today because `import fsb5` fails:
`ModuleNotFoundError: No module named 'fsb5'` — so route (a) as documented is not currently
reproducible from the repo's environment, only from its history.)

## A12 — one event carries start + loop + stop. **WEAK**

The chain's last edge is "event → the three samples". The card itself says the banks store no
event→sample link, and my probe agrees:

```
tune 30 body (181 B) small u32 values: [55, 207, 235]     contains 56/150/355? False False False
```

There is no index, GUID or pointer to those three waves in the tune. So the claim "these three samples
are this event's start/loop/stop" is a *naming convention* claim, not a decoded one, and the card's
singular "sound event" hides that an event may hold three one-shots or that start/loop/stop might be
three events. Two facts from the project's own later work bracket it:

- the loop is not in the wave (`T-12`'s audit: *"No candidate slot has an FSB5 loop chunk … 0 of 33.
  The loop lives in the event/tune graph"*), so the loop semantics live in the graph nobody decoded;
- `vehicles.bank` has 61 `nitrous_active` RTPC instances in `PRMS` and 257 events, i.e. the audio
  design has a whole nitrous family, not one event.

**WEAK**: the samples are the right *slots* to fill for a Batmobile afterburner (they are the only
nitro clips), but "the event plays exactly these three, as start/loop/stop" is unverified and should be
a Q-2 audition item, not a decoded step.

## A13 — no `.ee` / `.epe` / `.fmod_guids` edit is needed. **HOLDS**

Checked from the donor side, not the bank side:

- the GUID is in the donor's `.ee.fmod_guids` (`in_fmod_guids: true`, `count: 45`, banks
  `[vehicles, character, effects]`) — the file the card names;
- both nitrous objects are in the donor's `.epe` (2 objects, `Usage` = -97082140 = `EngineNitro`,
  `Effect` = -776668445, `Sound` = `F7,4E,A4,3B,…` on the first, absent on the second);
- the effect the objects point at (A6) is embedded in the donor's container
  (`car_cycle_base_dual_nitrous.effc`).

So the donor already carries usage, effect and event, and a sample swap needs no entity edit. This is
the card's most useful conclusion, and A6 makes it stronger than the card could claim: the effect is
not merely "a candidate" — it is the donor's own embedded `.effc`.

## A14 — which control fires nitro is UNKNOWN. **HOLDS as UNKNOWN, reason WEAK**

The card's UNKNOWN is properly scoped ("the button lives in code / controls data this census does not
carry"), and nothing decoded on disk carries a binding. But the sentence implies the search covered
the plausible places, and it did not: the index contains the two files a binding would live in, both
undecoded.

```
$ ... INDEX.jsonl rows matching input|control|keybind|gamepad, excluding animations/ ...
scripts/modules/input.xvmc
settings/keymap_gamepad.bin        (×2 rows)
```

So "in code" is unproven; there is *controls data*, indexed and named, that no card has read. The
UNKNOWN verdict stands; the reason should say "not in the decoded modules; `settings/keymap_gamepad.bin`
and `scripts/modules/input.xvmc` are candidates nobody has opened". It also means the Q-1 probe the
card implies (find the button) may be cheaper than an in-game probe.

## A15 — the Done check proves the chain. **WEAK**

`assertions()` returns 30 rows; the last 10 are G2-23's, and every one is a hardcoded expectation of a
value the same function just measured, including a historical artifact:

```
("nitro sound -> `vehicles.bank` `EVTS` ordinal", …["ordinal"], 249),
("objects carrying the nitro sound GUID", …, 202),
("nitro object `Effect` hash named in a module `all_effects[]`", …, False),
("nitro sample indices by name", …, [56, 150, 355]),
("test-060 swap indices == the three named samples", …, True),
("vehicles with an `arcade.nitro_boost` block", …, 145),
```

That is the card format's requirement (counts generated, tamper-testable, R11) and it does catch
edits — but `PASS` here means "the same numbers came out again", and two of the ten
(`named_in_module_space: False`, `test060_matches_names: True`) freeze the *misreadings* A7 and A11
describe, so the gate actively certifies them. A challenge on this card can pass `--check` and still be
right, which is exactly what happened above.

---

## What this changes (for the card owner, not done here)

1. **`USAGES.md` §6/§7, effect step — close the edge.** Replace "the object carries a second, unnamed
   effect hash … the 9 `*nitrous*.effc` files are a candidate family matched by name only" with:
   `Effect` 3518298851 = `hash_jenkins("effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc")`,
   the donor's own embedded `.effc`; 181/181 object `Effect` values resolve this way (A6). Delete
   §7's "hash function UNKNOWN" bullet — `rbmhdr.hash_jenkins` predates the card and is what
   `jc3index.py` uses to name every archive row.
2. **`USAGES.md` §6, effect (module) row + §7 — mark the fleet inference.** The donor's module binds
   only `HeadLights`; `EngineNitro → dynamic_nitrous` is on 14 builds, 0 cars (A5). Either say
   "fleet binding, donor has no row" or move it to UNKNOWN. Do not leave the assertion
   `EngineNitro links effect dynamic_nitrous` reading as a donor fact.
3. **`USAGES.md` §6, input step — widen the frame.** Land 145 / air 41 / sea 35 = 220 of 232; add
   `VehicleMisc` `full_nitro_use_time` 4 (8 upgraded) / `full_nitro_refill_time` 2 /
   `nitro_refill_min_speed_kph` 20 and `Transmission.nitrous_gears`, and mark the units
   (`N`, `km/h`, `s`) as by-magnitude, noting the schema's `_kph` convention is absent here (A2–A4).
4. **`USAGES.md` §8 / the tracker row — stop calling the test-060 match corroboration**, and say the
   fleet denominator is 232 of 314 vehicle `.ee` (81 DLC + 1 patch undecoded).

## What still holds

The donor's `arcade.nitro_boost` values; the donor's two `EngineNitro` objects; the sound GUID as a
real, unique `vehicles.bank` `EVTS` event (ordinal 249, 195 B, tune 30); 202 objects / 172 vehicles /
10 nitrous names; the sample family 56 / 150 / 355 as the bank's only nitro set with a verified
0-based name table; and the "no entity edit needed" recipe. With A6, the donor's chain on disk is now
complete from input block to a named `.effc` and a named bank event.

## Appendix — commands used (all read-only)

```
python Tools/scripts/jc3usage.py --check                      # PASS, exit 0
python - <<PY  # donor module rows        (E:/Modding/JustCause3/_grab/entities/v0300_…_civilian_01.ee.json)
python - <<PY  # donor .epe objects       (E:/Modding/JustCause3/_grab/detail/v0300_…_civilian_01.ee.json)
python - <<PY  # fleet arcade / air / boat / tank / nitrous_gears census over 232 caches
python - <<PY  # object Effect → FX path: rbmhdr.hash_jenkins vs FX_TABLE paths (181/181)
python - <<PY  # module all_effects name hashes (78) → 0 paths; name_hash 69,020/69,020 Jenkins
python - <<PY  # jc3audio.fev/fev_events/fev_tunes on the three Working/Audio bank copies
python - <<PY  # FSB5 name table of vehicles.bank (649 names, 0-based, contiguous)
python - <<PY  # INDEX.jsonl vehicle .ee census (314 = 232 base + 81 dlc + 1 patch)
python - <<PY  # FX_TABLE rows for the donor container (car_cycle_base_dual_nitrous.effc)
```

Nothing was written outside `Research/challenge/card-G2-23.md`; no game process was started; the
`D:/Games` install was not opened (the bank reads used the project's `Working/Audio/jc3bank/` copy,
whose size 210,781,376 B matches the card's figure).

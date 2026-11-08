# Assumption challenge — G2-22 · Effect usage vocabulary

Card: `GRAB_BACKLOG.md` §G2-22 (l. 707), tracker row §12 (l. 1305), MODLOG
`## G2-22 · Effect usage vocabulary — done` (l. 10550). Outputs under test:
`Research/JC3Grab/USAGES.md` (660 lines), `Research/JC3Grab/USAGES.json` (693,322 B),
`Tools/scripts/jc3usage.py` (59,074 B).

Mode: read-only. Nothing under `D:/Games` was written or read by me; no game launch; no commit.
Every number below was re-derived from `E:/Modding/JustCause3/_grab/` (decoded caches, `.epe` XML,
`entities/*.ee.json`) plus `Research/JC3Grab/{INDEX,FX_TABLE}.jsonl` and
`Tools/scripts/rbmhdr.py`. I did **not** run `python Tools/scripts/jc3usage.py --check`: its
`redecode()` calls `jc3grab.read_entry(..., GAME)` with `GAME = jc3index.DEFAULT_GAME`
= `D:/Games/Just Cause 3` (`jc3index.py` l. 56), so that check opens the live archives (read-only,
but unnecessary here — every count it prints was reproduced independently, below).

---

## VERDICT summary

| # | assumption | class | verdict |
|---|---|---|---|
| 1 | the hash function is UNKNOWN and no hash may be recomputed | decoded-value inference | **BROKEN** |
| 2 | 85 `.epe` `Usage` values "have no name in any decoded file" | decoded-value inference | **BROKEN** (30 of 85 named on disk) |
| 3 | no usage anywhere is named flame / fire / boost / afterburner | "no carrier exists" claim, narrow search | **BROKEN** as stated (`Fire`, `Fire2`…`Fire6`, `Flame` are `.epe` usage values) |
| 4 | `EngineNitro` = the flame-during-nitro carrier | behaviour read from a name (R5) | **WEAK** — candidate is real, "flame" is not in any decoded data |
| 5 | "fleet" = the 232 decoded caches | fleet-wide claim on a sample | **WEAK/BROKEN** — 314 shipped vehicle `.ee`, 288 vehicle graphs, 232 decoded |
| 6 | the 8 module-less vehicles "carry no usage at all" | fleet-wide claim / silent scope | **BROKEN** — they carry 3–41 `.epe` usage objects each |
| 7 | 12 usage names | counting a sentinel as decoded data | **WEAK** — 11 real names + an unset slot (`0xDEADBEEF`) |
| 8 | effect name → `.effc` file is UNKNOWN ("a lookup the engine holds") | "no carrier exists" claim, narrow search | **BROKEN** — all 8,714 `.epe` `Effect` ints decode to an `.effc` path |
| 9 | 0 cache/re-decode mismatches proves the decode is right | unit/independence convention | **WEAK** — same decoder both sides; and the run does open `D:/Games` |
| 10 | `+40 km/h`, `0.2 s` on the nitro block | unit convention | **WEAK** — no unit suffix on `extra_top_speed` |
| 11 | hashes are "int32" / uint32 interchange | sign/width convention | **HOLDS** (mask required, mask present) |
| 12 | 307 objects / 202 graphs carry the nitro usage | fleet-wide claim on a sample | **HOLDS as scoped**, **WEAK** as fleet claim (378 / 253 on disk) |
| 13 | 346 rows, 885 links, 225 modules, 224 vehicles, 12 names, 9 nitrous `.effc`, 275 containers, 57,187 FX rows | counts | **HOLDS** (all reproduced) |
| 14 | the donor lists only `HeadLights` at module level but attaches its nitrous exhaust | donor identity / sample-of-one | **HOLDS** |

What survives: the measured counts, the 12-row vocabulary table, the null
`ExtendedEffectUsages`, and the donor false-negative finding. What does not survive: the
`UNKNOWN` wall around the hash function and the effect→file edge (both are decodable with
`rbmhdr.hash_jenkins`, which this project already uses as a standing gate), the claim that the
sample is the fleet, and the "no flame/fire usage" sentence.

Downstream impact: `USAGES.md` §3 (85 UNKNOWN), §5 ("no usage … named … flame or fire"), §6
("object hash -> `.effc` edge is UNKNOWN"), §7 (three UNKNOWN entries) and the tracker row's
"9 `*nitrous*.effc` paths … matched by name only" all need correcting before T-17/FX-1 use them.

---

## 1. "The hash function is UNKNOWN; hashes are never recomputed"

**Where.** `USAGES.md` §7 line *"hash function. UNKNOWN; hashes are read from the files where the
string sits next to them, never recomputed, so no identification is needed."* Same claim in the
`jc3usage.py` docstring ("No hash is ever recomputed") and in the `--check` gate line
`6,045 modules / 232 caches`.

**Test.** Recompute every hash the document prints, with the project's own
`Tools/scripts/rbmhdr.hash_jenkins` (the "byte-for-byte port of StringHelpers.HashJenkins", pinned
in `GROUND_TRUTH` against `HashName.exe` on this machine, and already used by the standing gate
`jc3index.py` to verify 81,952 paths).

```
python -c "from rbmhdr import hash_jenkins; ..."   # 11 named usages + 8 value-driven names
   102641159 'EngineSmoking'              jenkins==True
  1674772341 'Siren'                      jenkins==True
  2287746320 'OnPartReachedDamageState'   jenkins==True
  2819629913 'EngineRunning'              jenkins==True
  3321438471 'OnPartBrokeOn'              jenkins==True
  3551535361 'HeadLights'                 jenkins==True
  3587098424 'OnExploded'                 jenkins==True
  3600488098 'Explosion'                  jenkins==True
  3735928559 ''                           jenkins==False
  3760597014 'OnPartExplode'              jenkins==True
  3877802965 'EngineTurboJump'            jenkins==True
  4197885156 'EngineNitro'                jenkins==True
match 11 mismatch 1
--- value-driven
  2476254024 BavariumShieldOn       jenkins==True      ... 8/8 True
```
and `dynamic_nitrous` → 397752766, `HeadLights` → 3551535361, `EngineNitro` → 4197885156
(0xfa36a4e4) all reproduce exactly.

**Result.** The hash function is not UNKNOWN: it is `hash_jenkins`, it reproduces 11/11 named
usage hashes, 8/8 value-driven names and every effect name tried. The single mismatch is the
empty string, which is itself evidence (see §7).

**Verdict: BROKEN.** This is the load-bearing assumption of the whole document: once hashes can
be recomputed, "UNKNOWN" collapses wherever a candidate string exists on disk (§2, §3, §8).

---

## 2. "85 of the 155 `.epe` `Usage` values have no name in any decoded file"

**Where.** `USAGES.md` §3 provenance table (`UNKNOWN 85`), §7, and the tracker/MODLOG
"85 UNKNOWN — recorded as UNKNOWN, never guessed".

**Test.** Build a string corpus from data already decoded on disk — every module `row` string in
`entities/*.ee.json`, every `type="string"` value in all 295 `.epe` XMLs, every `FX_TABLE` path +
basename + stem, every `INDEX` path + basename + stem (198,934 distinct strings) — hash each, and
look up the 85 values the document calls UNKNOWN.

```
corpus 198934
doc UNKNOWN 85; resolved by hashing corpus: 30
    5822793 ['TireDestroyed']
    74260773 ['Fire2']
    475644043 ['wing_loose']
    768006784 ['GearChange']
   1348371367 ['AssaultRifleImpact']
   1771942139 ['LandingGearDeployingStart']
   2303147823 ['Sliding']
   2329189637 ['DoorOpeningEnd']
   2963579072 ['Impact']
   3156189656 ['50CalBulletImpact']
   4059596067 ['DoorOpeningStart']
   4131019937 ['Fire']
   4253434231 ['ReloadStart']   ... 30 total
```

The same for the donor's "29 values that cannot be named from any table" (`USAGES.md` §5):

```
donor unnamed values 29 resolvable by hashing decoded strings 6
    5822793 TireDestroyed · 768006784 GearChange · 2303147823 Sliding
    2551142798 DoorClosingEnd · 2963579072 Impact · 4059596067 DoorOpeningStart
```

**Result.** Those names are in decoded files; they are simply not stored *adjacent* to the hash.
The document's provenance rule ("a hash is only named when the same decode produced the string")
is a reasonable anti-guessing rule but the sentence it produces — "no name in any decoded file" —
is false for at least 30 of 85 (and 6 of 29 for the donor).

**Verdict: BROKEN** (label), and the honest resting state is "adjacent-name UNKNOWN", not
"unknowable". Collision risk is negligible: 198,934 strings over 2³² ≈ 5·10⁻⁵ per value.

---

## 3. "No usage anywhere is named afterburner, boost, flame or fire"

**Where.** `USAGES.md` §5: *"Flame words in usage names: **none** - no usage anywhere in the
fleet vocabulary is named afterburner, boost, flame or fire. The flame is carried by effect
names."* Tracker row: "**0 usage names** match afterburner/boost/flame"; assertion
`usage names matching afterburner/boost/flame | 0`.

**Test.** The assertion only greps the 12 *module* names (`jc3usage.FLAME_NAME`), which is a
narrow place to look for a "no carrier exists" claim, and `.epe` names were never hashed. Hash the
obvious candidates and compare with the `.epe` value table:

```
Flame               456657646     <- doc §3: 456657646 UNKNOWN, objects "flame" x121
flame              3276669149
Fire               4131019937     <- doc §3: 4131019937 UNKNOWN, objects Fire/fire/ShellEjection
Fire2                74260773     <- doc §3: UNKNOWN, objects Fire2 x31
Fire3              2355437128     <- UNKNOWN
Fire4              2506518161     <- UNKNOWN
Fire5              2396082319     <- UNKNOWN
Fire6              2427790152     <- UNKNOWN
afterburner         694867993     (absent)
boost               282818547     (absent)
```

and across all 295 graphs, values whose name from that corpus contains a flame word:

```
 3877802965 EngineTurboJump     94496804 dynamic_exhaust
 4197885156 EngineNitro         397752766 dynamic_nitrous
 4131019937 Fire                74260773 Fire2 / Fire3 / Fire4 / Fire5 / Fire6
```

**Result.** The *module* vocabulary genuinely has no flame word. The `.epe` usage key space —
which the same document treats as the fleet's trigger vocabulary in §3 and §5 — contains `Fire`
(172 objects over all graphs), `Fire2`…`Fire6`, and `Flame` (121 objects). The sentence is true
only for the 12-name list, which is a different set from "the fleet vocabulary".

**Verdict: BROKEN** as written. Reword to "no *module-level* usage name", and list `Flame` /
`Fire*` as flame-named `.epe` usages.

---

## 4. `EngineNitro` is the "flame during nitro" carrier

**Where.** `USAGES.md` §5 "Named candidate … `exhaust_upgrade_nitrous*`"; tracker
"flame-during-nitro candidate = `EngineNitro` (4197885156) -> `dynamic_nitrous` (14 vehicles)";
MODLOG "the flame is carried by *effect* names and by 9 `*nitrous*.effc` paths".

**Test (a) — what the module row binds.** The `usage_effects[]` → `effect_indices[]` →
`all_effects[]` chain is data and reproduces: `EngineNitro` (18 modules) selects effect
`dynamic_nitrous` (397752766) on 14 vehicles and `EngineNitro` on 4 planes. **HOLDS.**

**Test (b) — what the value means in an `.epe` graph.** `4197885156` is simultaneously the hash
of the *usage* `EngineNitro` and of the *effect* `EngineNitro`:

```
  4197885156 EngineNitro  also an effect hash in module data: True  effect names: ['EngineNitro']
effect EngineNitro occurrences: 60 hashes: {4197885156}
```
The other five "module usage name" values (`EngineSmoking`, `Siren`, `EngineRunning`,
`Explosion`, `EngineTurboJump`) are *not* effect hashes, so `EngineNitro` is the one case where
the `.epe` `Usage` field cannot be distinguished between "the usage named EngineNitro" and "the
effect named EngineNitro" — and it is exactly the card's central value.

**Test (c) — is a flame in the data?** The object chain resolves, by hash, to one effect file:

```
donor v0300_car_kensington_sportsmuscle_civilian_01.ee.xml
  usage=EngineNitro  cls=SAttachedEffect  Effect=3518298851 -> effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc
  usage=EngineNitro  cls=SAttachedEffect  Effect=3518298851 -> effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc
```
(from the XML: `<value name="name" type="string">exhaust_upgrade_nitrous</value>`,
`<value name="Effect" type="int">-776668445</value>`, `<value name="Usage" type="int">-97082140</value>`).
There is no decoded `.effc` body anywhere on disk except `E:/Modding/JustCause3/_grab/tmp/sample.effc`
(`find … -iname '*.effc*'`), so the emitter/particle content of
`car_cycle_base_dual_nitrous.effc` cannot be inspected: "flame" rests on three names
(`EngineNitro`, `dynamic_nitrous`, `…_nitrous.effc`) plus one sound event.

**Verdict: WEAK.** The candidate is correctly identified and now has a *file* (resolved by hash,
not by name), which is stronger than the document claims. But (i) calling it "the flame" is a
name inference with no decoded emitter data (R5), and (ii) the `.epe` attribution of 307 objects
is ambiguous between the usage and the same-named effect. Keep the Q-1 probe; drop any wording
that treats the flame as established.

---

## 5. "Fleet" = the 232 decoded caches

**Where.** Scope table ("entity caches `entities/*.ee.json` **232**"), every count through the
document, the tracker's "across the fleet", MODLOG "**on 224 vehicles** - one plane carries two;
**8 vehicles carry none**".

**Test.** Count the vehicle entities the game ships (`INDEX.jsonl`, which the document itself
lists as 81,952 rows) against what was decoded:

```
vehicle .ee rows in INDEX: 314 {'dlc': 81, 'base': 232, 'patch': 1}
distinct vehicle .ee paths: 314     mount dlc 81 / base 232 / patch 1
caches 232 · base stems missing from cache: []          # the decode is exactly the base mount
dlc-only stems: 81  ('v0805_car_na_mech_*', 'v0201_..._blackhand_01', 'v4603_..._blackhand_01', ...)
```

And the `.epe` side, which the document says it read 232 of:

```
epe xml files 295 · distinct stems in epe dir 295
base covered 232 of 232 · dlc covered 55 of 55 · patch covered 1
not a vehicle stem: ['w011_pistol_u_pozhar_98', 'w111_assault_rifle_up_39', 'w501_turret_sam_v2',
                     'w503_turret_emp', 'w618_sportsmuscle_missile', 'w619_buggy_mgun', 'w702_emp']
all graphs: usage objects 15537 distinct 189       # doc: 12,576 / 155
non-base usage objects 2961 distinct 169
values only outside the 232 doc graphs: 34
 of those named by jenkins from existing strings: 20  (MechTransform, MechPunchSFX, GravityGun_*,
    MechJump, MechPowerDown, ZoomIn/ZoomOut, DrawWeapon, HolsterWeapon, OutOfAmmoFire, Pickup, ...)
```

**Result.** 82 shipped vehicle `.ee` files (81 DLC + 1 patch: `v0805_car_na_mech_*`,
`*_blackhand_01` variants, `v2602_..._custom_mm230`) were never decoded into module caches, and
56 vehicle `.epe` graphs that *are* on disk were outside the 232-graph corpus. The 34 extra usage
values include vehicle-relevant triggers (`MechTransform`, `MechPunchSFX`, `MechJump`,
`bavarium_effect_trail_burn`) — not only weapon-graph noise.

**Verdict: WEAK/BROKEN** for the word "fleet". Every count is a base-mount count. It should read
"232 of 314 shipped vehicle entities (base mount); 232 of 288 vehicle graphs on disk". The 12-name
vocabulary may or may not be complete for DLC (the DLC modules are not decoded, so this is
UNKNOWN, not "8 vehicles carry none").

---

## 6. "The 8 vehicles with no `EffectAttachments` module carry no usage at all"

**Where.** `USAGES.md` §1: *"The 8 vehicles with no `EffectAttachments` module (they carry no usage
at all)"*. Tracker: "8 vehicles carry none".

**Test.** Open the `.epe` graph of each of those 8 and count objects carrying a `Usage` int.

```
v0866_car_na_ladbil_civilian_01                                 usage_objects=34
v0866_car_na_ladbil_debug                                       usage_objects=34
v3001_bike_autostraad_snowmobile_debug                          usage_objects=41
v5602_train_urga_monorailflatbed_military_catwalk                usage_objects=3
v5602_train_urga_monorailflatbed_military_containers             usage_objects=3
v5602_train_urga_monorailflatbed_military_containers_rigidobject usage_objects=33
v5602_train_urga_monorailflatbed_military_empty                  usage_objects=3
v5603_train_urga_monorailmissilecar_military_01                  usage_objects=7
```

**Result.** All 8 do carry usage attachments in the graph (e.g. the ladbil: usage 1181737112
`engine_fire_drips`, 5822793 `TireDestroyed`, 1784764557 `rear_left_wheel`). "No module" is true;
"no usage at all" is false, and it matters because the document itself argues (correctly) that the
module row is not the whole vocabulary.

**Verdict: BROKEN** (one word: "module-level").

---

## 7. "12 usage names" (and the `0xDEADBEEF` row)

**Where.** `USAGES.md` §2 (12-row table, one row `(empty string) | 3735928559 | 14`), `--check`
line "12 named usages", tracker "**12 usage names** … + one empty-string usage with hash
`0xDEADBEEF` (14)".

**Test (a) — where the row sits.** Every one of the 14 is `usage_effects[0]`, and the modules
carrying it also carry real rows:

```
v2602_helicopter_urga_lightassault_debug: usage rows 5
    usage_effects[0].usage.string = ''   .hash = 3735928559   effect_indices 28,29
    usage_effects[1] EngineRunning (1,6,7,8) · [2] EngineSmoking (3,4) · [3] Explosion (5)
    usage_effects[4] OnPartReachedDamageState (38)
    all_effects[28] deform_point 'weapon_anchor_l' effect.string '' hash 3735928559
    all_effects[29] deform_point 'weapon_anchor_r' effect.string '' hash 3735928559
v4500_plane_solar_smallfloatprop_civilian_01: usage rows 1 — the only row is the empty one
```

**Test (b) — is `0xDEADBEEF` a name hash?** `hash_jenkins` is initialised
`a = b = c = (0xDEADBEEF + length + seed)` (`rbmhdr.py` l. 63), and no decoded string reaches it:

```
'' 834184464 · 'none' 480320411 · 'default' 3787346786 · …
0xDEADBEEF reachable from 198,934 decoded strings? False
```

**Result.** `''` + `3735928559` on both the usage and the effect side, pointing at
`weapon_anchor_l/r`, is an unset slot (the accumulator's seed value), not a usage. The document's
local statement is right ("the two sides agree, so nothing is being dropped"), but the row is then
counted as a 12th "name" in §2, in `--check` ("12 named usages") and in the tracker.

**Verdict: WEAK.** The count of *real* module usage names is 11. Nothing is lost in decoding;
what is lost is the distinction between "a usage" and "a null slot", and `v4500_..._civilian_01`
and `_debug` end up counted as carrying a usage when their single row binds nothing but
`weapon_anchor` placeholders.

---

## 8. "Effect name → `.effc` path is UNKNOWN; it is a lookup the engine holds"

**Where.** `USAGES.md` §7 first bullet (*"of 849,942 string values in the 232 `.epe` graphs,
exactly **0** name an `.effc` / `.ctunec` / `.trim`. UNKNOWN — it is a lookup the engine holds,
not data in these files"*); §6 (*"the object hash -> `.effc` edge is UNKNOWN"*; *"9 `*nitrous*.effc`
files are a candidate family matched by **name only**"*). The `.effc`-reference count is also a
`--check` assertion.

**Test.** The 849,942/0 measurement is correct but measures strings, not references. `.epe`
objects carry an `Effect` **int**; take it, hash every `FX_TABLE.jsonl` path with `hash_jenkins`,
and look it up:

```
probe_g2_22b.py:  detail files 232 · string values 849942 · ext hits 0        (reproduced)
distinct effc/etc paths 1533 · hashes 1533
objects with Effect field: 8714
  SDynamicAttachedEffect  objects=5484  resolved_to_FX_path=5484  unresolved=0
  SAttachedEffect         objects=3230  resolved_to_FX_path=3230  unresolved=0
  sample (2606884939, 'exhaust_upgrade_nitrous', 'effects/jc_vehicles/exhaust/car_cycle_base_nitrous_v0602.effc')
  sample (937459386,  'dynamic_break_wing',      'effects/jc_vehicles/damage/dmg_break_cargo_wing_base.effc')
nitro object Effect 3518298851 == jenkins('effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc')
   3518298851 effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc
   1989271107 effects/jc_vehicles/exhaust/car_cycle_base_nitrous.effc
    147918646 effects/jc_vehicles/exhaust/car_tjump_trail.effc
```

**Result.** 8,714 of 8,714 `Effect` ints in the `.epe` graphs resolve to an `.effc` path in
`FX_TABLE`. The nitro object's "unnamed hash 0xD1B4FAE3" is the path hash of
`car_cycle_base_dual_nitrous.effc` — i.e. the exact file the document lists as "matched by name
only". Nothing about this edge is native or UNKNOWN; the reference is simply stored hashed, and
the same object carries the human-readable name (`exhaust_upgrade_nitrous`) next to it.

**Verdict: BROKEN.** This is a false "no carrier exists" conclusion produced by searching string
values only, while the carrier was an int on the same object. It is also the single most useful
correction for FX-1/T-17: the effect→file edge is available for every `.epe` effect in the fleet
(and for DLC: `dlc/sky_fortress/.../dlc_angry_exhaust_grunt_drone.effc` resolves too).

---

## 9. "0 mismatches" between cache and re-decode proves the decode

**Where.** MODLOG: *"The check re-decodes every `_effect_attachments.vmodc` … (no archive is
opened; `D:\Games` is never read)"*; tracker "0 mismatches"; `--check` line
`cache/re-decode mismatches | 0`.

**Test.** Follow the code paths. `jc3usage.redecode()` (l. 150-190) reads each container with
`jc3grab.read_entry(jc3detail.pick(index_rows, entity), GAME)`; `jc3grab.read_entry` is

```
arc = os.path.join(game, r["archive"] + ".arc"); open(arc, "rb") …
```
and `GAME = jc3index.DEFAULT_GAME = os.environ.get("JC3_GAME", r"D:/Games/Just Cause 3")`
(`jc3index.py` l. 56). The cache side (`entities/*.ee.json`, built by `jc3grab.py`) and the
re-decode side both walk the same bytes with the same `jc3adf` decoder.

**Result.** Two separate problems: (a) the journal statement "no archive is opened; `D:\Games` is
never read" is factually wrong — the check opens the `.arc` files read-only (no write, so R6 is
not breached, but the MODLOG text would mislead the next session); (b) cache == re-decode is
determinism plus the `entity|module_index` keying fix, not independent verification of the decode.

**Verdict: WEAK.** The keying fix (225 modules / 224 vehicles) is real and I reproduced it
(§13). The "0 mismatches" claim should be labelled "same-decoder reproducibility", and the
`D:\Games` sentence corrected in the log.

---

## 10. Unit conventions: `+40 km/h`, `0.2 s`, "15000 N"

**Where.** `USAGES.md` §6 nitro chain: *"`arcade.nitro_boost`: torque x2, grip x2, `push_force`
15000, `boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h"*.

**Test.** Print the donor's `CustomLandGlobal` rows:

```
arcade.nitro_boost.torque_multiplier   = 2
arcade.nitro_boost.grip_multiplier     = 2
arcade.nitro_boost.push_force          = 15000
arcade.nitro_boost.boost_blend_time    = 0.200000003
arcade.nitro_boost.extra_top_speed     = 40
arcade.turbo_jump.punch_speed_kph      = 50
arcade.turbo_jump.top_speed_kph        = 200
```

**Result.** The file labels *some* speeds with a unit (`*_kph` in `turbo_jump`) and leaves
`extra_top_speed` bare. Nothing in the module says km/h; "40" is equally consistent with m/s
(144 km/h) as a raw number. `0.2 s` is a plausible read of `boost_blend_time` but is also unlabelled
(the value is a float32 `0.200000003`), and `15000 N` adds a unit the module does not carry.

**Verdict: WEAK.** Keep the numbers; move "km/h", "s" and "N" to `derived (assumed unit)` — R4
forbids shipping them as `decoded`/`read`.

---

## 11. Sign and width conventions for the hashes

**Where.** `USAGES.md` §3 header: "12,576 objects … carry a `Usage` **int32**", while every table
lists uint32 values (4197885156, 3735928559, …).

**Test.** Read the raw XML values:

```
<value name="Usage" type="int">-97082140</value>       = 4197885156 (& 0xFFFFFFFF)
<value name="Effect" type="int">-776668445</value>     = 3518298851
```

and the cache row for the null slot: `usage_effects[0].usage.hash = 3735928559` (already
normalised by the cache builder).

**Result.** The file stores two's-complement int32; every reader here masks with `& 0xFFFFFFFF`
(`jc3usage.redecode`, the `.epe` scan). A reader that forgot the mask would silently drop
`EngineNitro` (negative in the file) — i.e. the card's entire answer depends on this convention
being applied consistently on both sides. It is applied, and the conversion is lossless.

**Verdict: HOLDS** (convention correctly applied; worth one sentence in the doc since "int32" and
the printed uint32 values currently read as a contradiction).

---

## 12. "307 objects in 202 of 232 graphs" for the nitro usage

**Where.** `USAGES.md` §5 (307, 281 `SAttachedEffect` / 26 `SDynamicAttachedEffect`), §12 row,
MODLOG "307 objects in 202/232 `.epe` graphs".

**Test.** Re-count `Usage == 4197885156` in the 232 base graphs and in the 63 remaining vehicle
graphs on disk:

```
4197885156 objects base/nonbase: {'base': 307, 'nonbase': 71} graphs base 202 nonbase 51
all graphs: usage objects 15537 distinct 189
```

**Result.** 307 / 202 reproduces **exactly** on the 232 graphs — the arithmetic is sound. But the
same value sits on 71 more objects in 51 more vehicle graphs that are on disk (DLC mech, blackhand,
sky-fortress props) and were not counted, so as a fleet statement it is 378 / 253.

**Verdict: HOLDS as scoped** ("in the 232 decoded graphs"), **WEAK as a fleet number** — the doc's
own header says "202 of 232", which is honest; the tracker/MODLOG wording ("307 objects in 202/232
`.epe` graphs") is where the sample becomes a fleet.

---

## 13. The plain counts (independent reproduction)

**Test.** Re-derive without `jc3usage.build()`, from the caches and JSONL files only
(`tmp/freebuff/probe_g2_22.py`, `probe_g2_22b.py`, plus direct FX/INDEX line counts):

```
cache files 232 · modules 6045
EA per entity {1: 223, 0: 8, 2: 1} · entities with >=1 EA 224
EEU per entity {1: 232} · EEU module files {default_extended_effect_usages.vmodc: 232}
usage rows 346 · nested indices 885 · distinct usage names 12
  'HeadLights' 145 · 'EngineRunning' 69 · 'OnPartExplode' 33 · 'EngineSmoking' 23 · 'Explosion' 23
  'EngineNitro' 18 · '' 14 · 'EngineTurboJump' 11 · 'OnPartReachedDamageState' 3 · 'Siren' 3
  'OnExploded' 2 · 'OnPartBrokeOn' 2
detail files 232 · string values 849942 · ext hits 0
fx rows 57187 · nitrous rows 275 · distinct 9 · containers 275
INDEX.jsonl 81952 lines · FX_TABLE.jsonl 57187 lines
```

**Result.** Every headline number in `USAGES.md` §2 and §12 is reproducible, including the
"one plane carries two modules" fix (`{1: 223, 2: 1, 0: 8}`), the 9 nitrous `.effc` paths and the
275 containers. The `ExtendedEffectUsages` claim is also correct *within its scope* (one shared
627 B file, referenced by all 232).

**Verdict: HOLDS.** Counts are not the problem with this card; the interpretation and the scope are.

---

## 14. The donor reading (module row vs `.epe`)

**Where.** `USAGES.md` §5 "The donor's own attachments"; MODLOG "Reading only the module row would
have been a **false negative for the donor**".

**Test.** (a) Module side: query `USAGES.json` for the donor across all 12 usages;
(b) graph side: read the donor's two `EngineNitro` objects and their `Effect`;
(c) the file each `Effect` resolves to (§8).

```
donor in usage ['HeadLights'] 3551535361
   effect dynamic_headlight vehicles 145 donor here: True
donor in module-map count: 1
donor graphs ['v0300_car_kensington_sportsmuscle_civilian_01.ee.xml']
  usage=EngineNitro cls=SAttachedEffect Effect=3518298851 -> car_cycle_base_dual_nitrous.effc  (x2)
```

**Result.** The false-negative finding is real and, with the hash resolved, stronger than the
document says: the donor's `.epe` attaches two `exhaust_upgrade_nitrous*` objects under
`EngineNitro`, and their `Effect` hash is exactly `car_cycle_base_dual_nitrous.effc` — an `.effc`
the donor also embeds (`USAGES.md` §5 lists it among the donor's four exhaust files).

**Verdict: HOLDS** (and should be upgraded from "name only" to "file resolved by hash").

---

## Residual UNKNOWNs (after this challenge)

- Whether the `.epe` `Usage` field is a *trigger* id or a *selector* into something else: still
  UNKNOWN — and now demonstrably ambiguous for `4197885156`, a value that is both a usage hash and
  an effect hash (§4).
- Whether `EngineNitro` produces a visible flame: still needs Q-1. What is established is the
  effect **file** (`car_cycle_base_dual_nitrous.effc`), the object, and the sound event — not the
  rendered result.
- The 81 DLC + 1 patch vehicle `.ee` modules: not decoded, so DLC usage names/effects are UNKNOWN,
  not "absent".
- 69 of 189 `.epe` usage values (all graphs; 120 resolve from that corpus) still have no candidate
  string in the corpus used here; on the base 232 graphs the document's 85 falls to ~55. That is a
  real residue, but smaller than the document implies.

## What a follow-up should change (not done here — read-only)

1. `USAGES.md` §7: delete the "hash function UNKNOWN" bullet; cite `rbmhdr.hash_jenkins`
   (already a standing gate) and recompute the usage/value-driven names in `jc3usage.py` as a
   cross-check.
2. `USAGES.md` §3: relabel `UNKNOWN 85` → "no *adjacent* string" and print the 30 that hash to
   known strings.
3. `USAGES.md` §5/§6/§7: replace "matched by name only" and "object hash -> `.effc` edge is
   UNKNOWN" with the `Effect` int → `FX_TABLE` path resolution (8,714/8,714).
4. §1/§2: "no usage **at all**" → "no `EffectAttachments` **module**"; count 11 real module usage
   names + 1 null slot; scope every "fleet" number to the base mount and name the 314 / 288 totals.
5. `MODLOG.md` G2-22: correct "no archive is opened; `D:\Games` is never read" (the `--check`
   re-decode opens the `.arc` files read-only).

# Assumption challenge — backlog card B-09 (private health module and damage types)

Scope: `GRAB_BACKLOG.md` §0.5 (R1–R14, lines 59–76), the **B-09** card (§8, line 1065), its **§12**
row (line 1339), MODLOG §"B-09 · private health module — done" (line 17291–17390), and the card's
outputs: `Tools/scripts/bm_health.py`, `Working/Damage/bm_health.json`, `Builds/bm-009/` (`aaf`
tree, `.ee`, `.ee.toc`, `receipt.json`, `verify/`, `install.ps1`), `Working/Translation/
damage_switches.json`, `Working/Damage/jc3_damage_band.md`, `Research/specs/B-09.md`. Where a value
is inherited (T-14, G2-28, B-04), the challenge follows it to that file, because that is where the
assumption really lives.

**Read-only:** no source, generated artefact, build or game file was modified. Nothing was written
under `D:/Games`, no game was launched, nothing was committed, no secrets read. The only file
written is this one. All commands below are read-only Python/reader calls over files already in the
tree.

**Not re-run, and why.** B-09's two Done checks (`damage_audit.py --build`, `damage_predict.py
--root`) shell `Tools/Gibbed-patched/…ConvertAdf.exe` through `t1_current.dump()`, which writes an
XML cache under `E:/Modding/JustCause3/_grab/tmp_t1` — outside the repo, and outside this session's
read-only mandate. `Research/specs/B-09.md` skipped them for the same reason. Their recorded MODLOG
output is quoted where it matters and labelled **[recorded]**; every other number below is fresh.

---

## VERDICT summary

**The card's mechanical result is clean — the bytes, the `.toc` record, the `.epe` hash and the
no-re-encode claim all re-derive exactly. What does not survive is the provenance of the file it
copies and three of the four "shipped" values inside it.** `Builds/bm-002`'s
`lave_health_medium.vmodc` is **not** the game's `lave_health_medium.vmodc`: the game's file is 700
HP with `deform_scale` 1.0 and `impact_damage_factor` 1.0 (three independent witnesses below).
B-09 clones the already-drifted copy, so the module it ships differs from the game's own shared
module in **23 members / 46 bytes**, not the "4 values" the card reports — and that module is packed
*internally* into the `.ee` at a path **77 cars reference**. Separately, "no `PartDamageType` row
exists" is true only of the 24-name `Land_*` table B-09 copied: the fleet has six per-family tables,
and `Train_Generic`/`Boat_Generic`/`Plane_Control_Surface` rows do exist in the train/boat/plane
modules.

Of 16 assumptions tested: **4 HOLD, 4 WEAK, 8 BROKEN** — and the split is systematic: every
*mechanical* claim (bytes, `.toc`, `.epe`, sizes, diff) holds, every *provenance, coverage or
behaviour* claim except one breaks.

| # | Assumption (stated or silent) | Verdict |
|---|---|---|
| B9-01 | the copy source `bm-002/…/lave_health_medium.vmodc` is the file the game ships | **BROKEN** — shipped = `6F9C8FAB…` 700 HP / 1.0 / 1.0; bm-002 = `AF5C33E6…` 2000 / 0 / 0. B-09's module differs from the game's file in **23 members**, not 4 |
| B9-02 | `deform_scale` 0 and `impact_damage_factor` 0 are shipped values ("asserted, not written") | **BROKEN** — the shipped module has 1.0 / 1.0; the project's own `damage_switches.json` calls both "declared deviation(s), not a translated value" |
| B9-03 | "the shared `lave_health_medium.vmodc` stays byte-identical (R7, `AF5C33E6…`)" | **BROKEN as a shipped-file claim** (HOLDS only as a diff vs bm-002) — the `.ee` carries an *internal* record for that path and the packed bytes are the drifted `AF5C33E6`, which 77 `CCar` roots reference |
| B9-04 | `max_health` is the pool incoming damage subtracts from (R5: member by name) | **WEAK** — the value is decoded, the composition is not (`DAMAGE_MODEL.md` step 6 UNKNOWN); no probe has run, and the card family's own armour experiments changed nothing |
| B9-05 | 36,000 = 24 BmAK heavy-cannon hits × 1500 JC3 shell damage | **BROKEN** — 24 is `1200/50` where 50 is the Batmobile's **outgoing** cannon; 1500 is JC3's **`PlayerDamage`** (a player blast, `AIDamage` 550 six-metre twin exists). Two games' numbers multiplied, no unit bridge |
| B9-06 | the predicted table "meets ARM-2's BmAK ratio" | **WEAK** — 24 is H0 only; the same table prints 48 (H1) and 25 (H2), i.e. +100 % under the model the fleet's own tank config suggests |
| B9-07 | `explosion_threshold` 4000 is "independent of the health pool: 36000 does not move it" | **BROKEN** — every shipped vehicle except the medium tank runs `threshold == max_health` (MODLOG 4857); 36000/4000 = 9× is a pair no module in the game has |
| B9-08 | the 4 uncovered part types have no `PartDamageType` row anywhere ("the fleet's own fallback") | **BROKEN** — the fleet has 6 per-family tables (32 `Boat_*`, 18 `Plane_*`, 12 `Train_*` modules); `Train_Generic` is a row in the train table. The claim is true only of the 24-name `Land_*` table, and the fallback precedent covers 1 of the 4 types |
| B9-09 | "part damage types per T-14" is satisfied by asserting the parts module | **BROKEN** — 8 of 59 parts (13.6 %) resolve to `Default` 50/30/20 instead of `Land_Generic` 200/0/50, and `bm_health.py`'s check **prints** that without failing |
| B9-10 | the private module's 24-row part table is "the donor's" | **BROKEN** (one cell) — `Land_Wheel.instantly_damaged_by_bullets` is 1 in the shipped file and 0 here (offset 0x14C), inherited from the live-build edits |
| B9-11 | `skew_health` 200→400 is "at the shipped ceiling 200..400" | **HOLDS** the range (`VOCABULARY.md`, n=145) — **WEAK** on semantics (name only) and on the sample (145 of 233 modules carry the member) |
| B9-12 | the `.epe` repoint is one 4-byte write keyed by `Jenkins(full vfs path)` | **HOLDS** — `Jenkins("damage")` = `0x4F489F01`, `Jenkins(shared path)` = 670155287 at byte 474, `Jenkins(private path)` = 1928726201, exactly one occurrence each, type `0x0E` |
| B9-13 | no re-encode, no file grows, 245 members re-read identical | **HOLDS** — the private module differs from bm-002's copy in **2 bytes** (`a0 8c 00 00` = 36000); land_global in 4 bytes (200→400 ×2); sizes 3,741 / 3,399 unchanged |
| B9-14 | `aafdiff` = exactly 4 files, 605 `.toc` records, private module internal | **HOLDS** — my own tree diff: 1 added + 3 changed; 605 records; record (23,222,112, 3,741); slice == staged copy |
| B9-15 | `damage_predict.py --root Builds/bm-009` reads *the entity's* module | **WEAK** — the current source takes the **first** `VehicleDamage` module in `os.walk` order and never consults the `.epe`; that order visits the shared 2000-HP module first. The recorded 36000 output is not reproducible from today's code |
| B9-16 | 36,000 is a value the engine will honour | **WEAK/UNKNOWN** — 9× the fleet maximum, serialized `int32`; no decoded runtime width, clamp or probe; exceeds `int16` |

---

## 1. B9-01 — the copy source is the file the game ships

**Why the card rests on it.** The card's Do line is *"copy `lave_health_medium.vmodc` to a private
path, apply `t10_damage_edits.json`"* (`GRAB_BACKLOG.md:1066`). §12 and MODLOG describe the result
as *"a private `batmobile_health_medium.vmodc` (3,741 B) with `max_health` 2000 -> 36000 (T-DM1), …
`deform_scale` 0 (T-DM6) and `impact_damage_factor` 0 (T-DM8) **asserted**; the shared
`lave_health_medium.vmodc` stays byte-identical (R7, sha256 `AF5C33E6…`)"* (`:1339`, `:17295`).

**Test.** Hash and read the same member offsets in every copy of that path in the tree, and compare
with the pristine extraction the repo carries (`SerpenteR-EE/`, listed in `Research/INVENTORY.md`
line 135 with the same 3,741 bytes):

```
$ python  # struct.unpack at 0x50/0x94/0x98/0xA8 for Builds/*/aaf/…/00_shared/modules/health/lave_health_medium.vmodc
_shelved-061maxrpm size=3741 max_health=700  impact_factor=1.0 deform=1.0 explosion_thr=700  sha=6f9c8fab7c9d
        bm-001      size=3741 max_health=2000 impact_factor=0.0 deform=0.0 explosion_thr=4000 sha=af5c33e6306d
        bm-002      size=3741 max_health=2000 impact_factor=0.0 deform=0.0 explosion_thr=4000 sha=af5c33e6306d
        bm-009      size=3741 max_health=2000 impact_factor=0.0 deform=0.0 explosion_thr=4000 sha=af5c33e6306d
      test-003 … test-066   (54 trees)   max_health=700 impact_factor=1.0 deform=1.0 sha=6f9c8fab7c9d
      test-067 … test-091    (14 trees, incl. test-091)                                       af5c33e6306d (+5 intermediate hashes)

$ python  # the repo's pristine extraction
SerpenteR-EE/editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc
exists True 3741
sha256 6f9c8fab7c9d3df7 max_health 700 impact 1.0 deform 1.0 expl_thr 700
```

Three independent witnesses agree on the shipped file: the `SerpenteR-EE` extraction, 54 build
trees (including `_shelved-061maxrpm`, so `test-003 … test-066` among them), and
`Research/JC3Grab/DAMAGE_MODEL.json`, whose **donor** row is
`"file": "…/00_shared/modules/health/lave_health_medium.vmodc", "max_health": 700`. The drift
sequence is visible: `6f9c8fab → 643f97d7 (067-069) → 5fc2e230 (070) → 58240465 (071) → f891c1b2
(072) → d9d617d6 (073) → 301fcfdb (074-075) → af5c33e6 (076, 085-086, 088-091, every `bm-*` tree)
/ 382fd9d7 (077-084) / 960fe226 (087)`. Even **`bm-001`**, the
tree the backlog calls the identity build, carries the drifted file.

**What that does to B-09's module.** Diffing the game's file against B-09's private module:

```
$ python  # Builds/test-003/…/lave_health_medium.vmodc  vs  Builds/bm-009/…/batmobile_health_medium.vmodc
shipped 700-file bytes 3741 bm-009 private bytes 3741
differing bytes: 46
differing 4-byte slots: 23 [80, 84, 88, 92, 96, 100, 104, 108, 112, 124, 128, 132, 136, 140, 144, 148, 152, 156, 160, 168, 172, 176, 332]
  0x0050 max_health              shipped=700   bm009=36000
  0x0054 bullet_armor            shipped=0     bm009=5000
  0x0058 bullet_armor_strength   shipped=0.0   bm009=99.0
  0x005c bullet_heavy_armor      shipped=0     bm009=5
  0x0060 bullet_heavy_armor_…    shipped=0.0   bm009=20.0
  0x0064 explosion_armor         shipped=0     bm009=250
  0x0068 explosion_armor_…       shipped=0.0   bm009=50.0
  0x006c impact_armor            shipped=0     bm009=5000
  0x0070 impact_armor_strength   shipped=0.0   bm009=100.0
  0x007c melee_armor             shipped=0     bm009=5000
  0x0080 melee_armor_strength    shipped=0.0   bm009=100.0
  0x0084 electricity_armor       shipped=0     bm009=-1
  0x0088 electricity_armor_…     shipped=0.0   bm009=100.0
  0x008c grapple_pull_armor      shipped=0     bm009=-1
  0x0090 grapple_pull_armor_…    shipped=0.0   bm009=100.0
  0x0094 impact_damage_factor    shipped=1.0   bm009=0.0
  0x0098 deform_scale            shipped=1.0   bm009=0.0
  0x009c smoke_threshold         shipped=200   bm009=1050
  0x00a0 explosion_delay_s       shipped=8     bm009=10
  0x00a8 explosion_threshold     shipped=700   bm009=4000
  0x00ac npc_explosion_threshold shipped=700   bm009=4000
  0x00b0 vulnerable_explosion_…  shipped=35    bm009=100
  0x014c instantly_damaged_by_bullets (Land_Wheel)  shipped=1  bm009=0
```

**Result.** The card's arithmetic ("4 values") is right about B-09's *diff*; it is wrong about the
*file*. `bm_health.py` compares the copy against the source file **in the same tree**
(`moved = [k for k in src_members …]`, `bm_health.py` `write_build`), so anything inherited from
`bm-002` is invisible by construction. The audit then passes because it checks each value against
the *fleet range*, not against the source module (see B9-15/B9-16).

**Verdict: BROKEN.** Not a byte-level defect in B-09's write; a provenance defect in the file it
writes into. The card claims to copy the game's shared module and instead carries 22 other member
edits into the Batmobile's private module.

---

## 2. B9-02 — `deform_scale` 0 and `impact_damage_factor` 0 are shipped values

**Why the card rests on it.** `bm_health.py`'s edit table says
`"why": "no panel crumple (APP-7); already 0 in the shipped module, declared switch"` and
`"incoming collision damage off (BmAK: ramming does not scratch it); declared switch"`, and the
`.epe`/build chain was supposed to *assert* them rather than write them (`MODLOG:17299`).

**Test.** Read the project's own declaration file, which exists precisely to mark values that are
*not* shipped:

```
$ python -c "json.load(open('Working/Translation/damage_switches.json'))"
"impact_damage_factor": {"value": 0, "row": "T-DM8",
  "why": "… Shipped range is 1..12, so it is a switch, not a value. Do not 'correct' it toward the
          fleet median: that is exactly test-087."}
"deform_scale": {"value": 0, "row": "T-DM6",
  "why": "cosmetic switch: no panel crumple … Shipped range is 1..2, so this is a declared
          deviation, not a translated value."}
"impact_armor": {"value": 5000, "row": "T-DM8", "why": "… the shipped range is 0..5 …"}
"melee_armor": {"value": 5000, "row": "T-DM9", "why": "no shipped vehicle uses melee armour (fleet 0..0) …"}
"melee_armor_strength": {"value": 100, "row": "T-DM9", "why": "… fleet range is 0..0 …"}
```

`Research/JC3Grab/VOCABULARY.md:1463,1476` gives the same fleet ranges (`deform_scale` 1..2,
`impact_damage_factor` 1..12, n=233), and `Working/Damage/jc3_damage_band.md`'s "stock medium" column
is 1 / 1 while "ours now (076)" is 0 / 0.

**Result.** "Already 0 in the shipped module" is false. 0 is a deviation the project declared
against the *fleet*, and B-09's private copy inherits it from `test-076`. The claim is also
self-contradictory with §12's own audit line, which reports these as **"6 outside the shipped
range, 6 declared switches"** — i.e. the audit says 0 is outside the shipped range.

**Verdict: BROKEN.**

---

## 3. B9-03 — "the shared module stays byte-identical" keeps R7

**Why the card rests on it.** R7 (`GRAB_BACKLOG.md:73`): *"Never edit shared game modules in place
(`vehicle_common`, `lave_health_medium`, …). Make a private copy with a new path and repoint the
hash."* §12 offers a sha256 as the proof.

**Test 1 — diff vs bm-002 (what the check does).**

```
$ python  # sha256 of Builds/bm-002/aaf/… and Builds/bm-009/aaf/… 00_shared/…/lave_health_medium.vmodc
bm-002 copy sha256 af5c33e6306deba7
bm-009 copy sha256 af5c33e6306deba7   → identical (HOLDS)
```

**Test 2 — what the `.ee` actually ships.**

```
$ python  # read the bm-009 .toc + .ee directory
toc record for the SHARED module: 16538000 3741 internal
packed bytes sha256: af5c33e6306deba7
game/early-build copy    sha256 6f9c8fab7c9d3df7  equal_to_packed=False
bm-002 copy              sha256 af5c33e6306deba7  equal_to_packed=True
```

```
$ python -c "json.load(open('Research/JC3Grab/DAMAGE_MECHANISMS.json'))"   # CCar.damage values, n=126
{"-1154247498": 4, "-310686002": 22, "-564675643": 10, "-964818999": 4, "2496887": 9, "670155287": 77}
```

`670155287` is `Jenkins("editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc")`
(computed, §5), and **77 cars reference it**. The `.toc` record for that path has a **non-zero
(internal) offset**, so the game loads the packed copy, not the archive's — exactly the mechanism
R8 describes.

**Result.** B-09 changes no byte of the shared module *relative to bm-002*; but the artefact B-09
ships does carry a shared-module override, and the override is the drifted `AF5C33E6` file (2000 HP,
5000/99 bullet armour, 5000/100 impact, 5000/100 melee, 250/50 explosion, thresholds 4000). Install
bm-009 and every one of the 77 cars that use `lave_health_medium.vmodc` gets that profile — a
fleet-wide gameplay change the card's §12 row never mentions. The `AF5C33E6` sha256 is offered as
evidence of R7 compliance; it is evidence that the baseline is already non-shipped.

**Verdict: BROKEN as a shipped-file/R7 claim; HOLDS only as "B-09's own diff did not touch it".**

---

## 4. B9-04 — `max_health` is the pool damage subtracts from (R5)

**Why the card rests on it.** R5 (`:70`): *"A requirement is carried by a behaviour row with a take
that can fail, not by the JC3 member whose name sounds closest."* The whole card is one member:
`max_health` 2000 → 36000.

**Test.** Look for a file that states the composition, and for an experiment that measured it.

```
$ sed -n '/| 6 | the vehicle.s health pool/,+0p' Research/JC3Grab/DAMAGE_MODEL.md
| 6 | … | `VehicleDamage.max_health` (500..4000) x the entity root's `health` float32 (100.0 on all
  233 roots) + the root's `invulnerable` int32 | … | decoded (values) | how the root `health` float
  composes with `max_health` (percent? multiplier? a separate pool?) … Every shipped root is 100.0,
  so no file shows a second value to compare against |
```

`DAMAGE_MODEL.md` §8 repeats it under "UNKNOWNs, stated": *"the composition rule itself (step 4/6) —
see the three models; no file states it."* The only behavioural evidence in the tree points the
other way: `MODLOG:6229-6233` records that `explosion_threshold` 4,000, `smoke_threshold` 1,050,
`burn_threshold` 250 and `bullet_armor_strength` 100 were already at the fleet ceiling, *"That is
why 'a couple of mags' does not kill it through thresholds — the remaining lever is `max_health`"*,
while `Working/Damage/part_damage_routing.md` records *"The header armour values (5000 @ 100) are
not on this path at all, which is why raising them in 074/077 changed nothing."* In other words the
same file family has already shown that raising a header member did not produce the modelled effect.

**Result.** The *value* 36,000 is decoded into the right slot; the *behaviour* it is supposed to
buy (24 shells to kill) has never been observed, and the model that converts it is one of three the
project carries precisely because the rule is unknown. The card's Done line ("`damage_predict.py
--root <build>` prints the T-14 table") is satisfied by printing a model, not by a take that can
fail.

**Verdict: WEAK.** (This is the inherited core of T-14; `Research/challenge/card-T-14.md` §10
reaches the same verdict on the 36000.)

---

## 5. B9-05 — 36,000 = 24 BmAK hits × 1500 JC3 damage (unit convention)

**Why the card rests on it.** `damage_switches.json`:
`"why": "ARM-2 at the BmAK ratio: 24 heavy-cannon hits x 1500.0 shell damage = 36000"`. The row is
the only justification for the value.

**Test.** Follow both factors to their source.

- **24** — `DAMAGE_MODEL.md` §5: *"`Pawn.Health` **1200**, the heavy cannon projectile `Damage`
  **50** … so the BmAK ratio is 1200 / 50 = 24 heavy-cannon hits"*. `DAMAGE_RULES` is titled
  *"Outgoing weapon damage"*; `Research/challenge/card-T-14.md` §3 shows 50 is the **Batmobile's own
  outgoing cannon**, and no enemy-tank projectile damage exists in the record.
- **1500** — `DAMAGE_MODEL.md` §3: the tank cannon's `bullet_weapon … damage` is **1.0**; the 1500
  is the blast's **`PlayerDamage`** (`w602_mediumtank_canon`, radius 8 m,
  `PlayerDamageRadiusPercentageMax` 0.15 — full damage only inside 1.2 m). The same
  `ForcePulseSettings` carries `AIDamage` 550 in 6 m (`Research/challenge/card-G2-28.md` §9, which
  calls the `PlayerDamage`-only reading **BROKEN under R5**).
- **No unit bridge.** BmAK `Pawn.Health` is a BmAK number in BmAK's damage units; JC3
  `max_health` is a `VehicleDamage` int32 with an undocumented relationship to the root `health`
  float (B9-04). The product mixes the two.

**Result.** `24 × 1500` multiplies a hit count from one engine by a damage figure from another, and
one of the two factors (`PlayerDamage`) is chosen by its name. If the AI figure is the one that
applies, 24 × 550 = 13,200; if the blast falls off before the hull, every hit is worth less than
1500.

**Verdict: BROKEN** (inherited from T-14 §3/§17; B-09 is where it becomes a shipped number).

---

## 6. B9-06 — the predicted table "meets ARM-2's BmAK ratio"

**Why the card rests on it.** `MODLOG:17363`: *"tank cannon 24 / 48 / 25 hits at `max_health` 36000,
ARM-2's BmAK ratio met under H0 and H2, +100 % under H1."* §12 repeats "36,000 HP and tank cannon
24 / 48 / 25 hits H0/H1/H2 = T-14's table".

**Test.** The table is in the record:

```
[recorded] build under test: Builds/bm-009 (build_bm-009, max_health 36000)
rpg            explosion    1500.00     24    48    25
tank_cannon    explosion    1500.00     24    48    25
```

and `Working/Translation/t10_damage_edits.json` `decision.max_health_for_ratio` =
`{"H0": 36000, "H1": 18000, "H2": 35750}`.

**Result.** The number is the H0 answer only. Under H1 (the percentage gate — the reading the
project originally took from MODLOG §97) the same 36,000 gives **twice** the BmAK ratio, and the
decision file itself says H1 needs 18000. Under H2 it is 25, not 24. So "the ratio is met" is a
2-of-3 statement, and the card's own table is the evidence against the unqualified sentence.

**Verdict: WEAK** (the table is honest; the summary sentence is not).

---

## 7. B9-07 — `explosion_threshold` is independent of the health pool

**Why the card rests on it.** `bm_health.py` T-DM4: *"per-hit damage threshold, independent of the
health pool: 36000 does not move it"*, `from: 4000, to: 4000` — carried as a "keep", so the audit
never looks at it again. `t10_damage_edits.json` T-DM4 says the same and calls the source
`VOCABULARY.md`.

**Test.** The fleet's joint behaviour of the two members:

```
$ sed -n 4853,4862p MODLOG.md
- `max_health` 1800 -> **2000** and `explosion_threshold` 1800 -> **4000**: the
  tank's own working pair (tank runs 2000/4000; every other vehicle in the game
  runs threshold == max_health, so the tank is the deliberate 2x hardening).
```

That equality is why test-076 copied 2000/4000 as a *pair*; it is also why the pair is meaningful.
B-09 then moves one half only:

```
bm-009 module: max_health 36000, explosion_threshold 4000, npc_explosion_threshold 4000,
               smoke_threshold 1050, burn_threshold 250
ratio max_health / explosion_threshold = 9.0      (fleet: 1.0, or 2.0 for the medium tank)
```

`DAMAGE_MODEL.md` step 7 explicitly leaves the semantics open: *"whether `explosion_threshold` is a
per-hit blast damage that destroys the vehicle outright or a health threshold; the fleet's 500..4000
range overlaps max_health 500..4000, so both readings fit the data."* Under the health-threshold
reading (the one the equality supports), the Batmobile now smokes at 2.9 % of its pool and explodes
at 11 % — numbers no shipped vehicle exhibits.

**Result.** "Independent of the health pool" is an assertion contradicted by the fleet's own pairing
and by the project's own decision to copy the pair together at 076. This is the single largest
untested interaction the card creates, and the audit cannot see it because 4000 is inside the
fleet's `explosion_threshold` range.

**Verdict: BROKEN.**

---

## 8. B9-08 — "no `PartDamageType` row exists" for four types

**Why the card rests on it.** `MODLOG:17383`: *"Four damage types used by B-04's parts
(`Boat_Antenna`, `Boat_Generic`, `Plane_Control_Surface`, `Train_Generic`) have no `PartDamageType`
row in the 24-row table, so they resolve through the module's `Default` row (**the fleet's own
fallback: the donor's `Boat_Antenna` part does the same**)."*

**Test 1 — where the search stopped.** The check hashes/reads **one** module: the private copy of
`lave_health_medium.vmodc`. The fleet's part-type tables are per family:

```
$ sed -n 210,224p Research/challenge/card-G2-28.md
distinct part-name sets: 6
  145 x 24 names, first: Default | second: Land_Generic
   32 x 17 names, first: Default | second: Boat_Generic
   23 x 14 names, first: Default | second: Heli_Generic
   18 x 15 names, first: Default | second: Plane_Generic
   12 x 13 names, first: Default | second: Train_Generic
    3 x 16 names, first: Default | second: Boat_Generic   (a second boat set)
```

`Research/JC3Grab/PARTS_TABLE.md:19` counts **371 fleet parts** with `Train_Generic`, and
`Research/challenge/card-T-12.md:291` names its carrier entity
(`01_land/v5603_train_urga_monorailmissilecar`). So `Train_Generic` is a *row* in the train's table,
`Boat_Generic` a row in the boat's, and `Plane_Control_Surface` almost certainly in the plane's
(15 names, `Plane_Generic` first). The claim "no row exists" is true only of the 24-name `Land_*`
table the Batmobile must use.

**Test 2 — how much falls through.** Count the parts the build actually gives those types:

```
$ python -c "json.load(open('Working/Parts/bm_vehicle_parts.json'))"
before: {"parts": 42, "bytes": 29886, "door_parts": [1,2,25]}
removals: sportsmuscle_door_f_l, sportsmuscle_door_f_r
new parts 19 {'Land_Light': 8, 'Boat_Generic': 1, 'Plane_Control_Surface': 4, 'Land_Generic': 4, 'Train_Generic': 2}
→ 42 - 2 + 19 = 59 parts  (matches the check's "59 parts use 19 distinct damage types")
```

Add the donor's one `Boat_Antenna` part (`sportsmuscle_c_mirror`,
`Working/Damage/part_damage_routing.md` row 33): **8 of 59 parts** (13.6 %) — 4 flaps, 2 missile
pods, 1 machine-gun mount, 1 mirror — resolve to `Default` `50/30/20` instead of `Land_Generic`
`200/0/50`. The fallback *precedent* the card cites covers exactly one of the four types
(`Boat_Antenna`), on the donor, in the same 24-name table.

**Result.** The rationale generalizes a one-type precedent (donor `Boat_Antenna`) to three types
whose rows exist in other family modules, and states a fleet-level absence from a single-module
search. The decision not to invent values is defensible (R4); the *reason given* is not.

**Verdict: BROKEN** (claim), **defensible** (choice).

---

## 9. B9-09 — "part damage types per T-14" is satisfied by assertion

**Why the card rests on it.** Card Do line: *"part damage types per T-14"*; `bm_health.py`'s
`part_damage_types` block says *"edit: none — the parts module already carries T-14's per-part
damage types (B-04), and this build asserts every part's type resolves to one of them"*. §12's
open item says the four missing types "fall back to `Default` — no row invented".

**Test.** Read the check's coverage block:

```
print(f"6. part types  {len(parts)} parts use … {len(names)} PartDamageType rows … "
      f"{len(missing)} without a row {missing if missing else ''}")
```

There is no `fails.append` anywhere in that block: the check **prints** the gap and still returns
`PASS … 0 problem(s)`. Compare every other numbered sub-check (`.toc record`, `health values`,
`wheel rows`, `.epe damage`, `R7 shared`), each of which appends to `fails`.

**Result.** The one card requirement that is not a number ("part damage types per T-14") is the one
the check cannot fail on. Combined with B9-08's 8/59 parts and B-04's own challenge (7 of 19 new
parts land on `Default`), "Done" here means "recorded", not "satisfied".

**Verdict: BROKEN** (as a "Done" claim; the choice not to invent values is still the right one).

---

## 10. B9-10 — the private module's 24-row part table is the donor's

**Why the card rests on it.** `bm_health.json` `part_damage_types.edit = "none"`, and `MODLOG:17299`
says *"no part damage type is changed here"*.

**Test.** The same 4-byte-slot diff as B9-01 shows slot `0x14C` — which the layout dump identifies
as row 3 (`Land_Wheel`), offset +28 (`instantly_damaged_by_bullets`):

```
$ grep -n "0000014C" Working/Damage/_dump_health_full.txt
  @0000014C   instantly_damaged_by_bullets   int8   0        # row 3 = Land_Wheel
$ python  # shipped file vs bm-009 private module at 0x14C
 0x014c instantly_damaged_by_bullets  shipped=1  bm009=0
```

`DAMAGE_MODEL.md` §2 names this as *"the build's part table is the donor's with exactly 1 change:
`Land_Wheel.instantly_damaged_by_bullets` 1 -> 0"*.

**Result.** "No part damage type is changed here" is true of B-09's write and false of the module it
ships: one part-row cell is changed relative to the donor, inherited from the live-build edits.
Minor in effect, but it is another inherited value presented as donor data.

**Verdict: BROKEN** (one cell), **low impact.**

---

## 11. B9-11 — `skew_health` 200→400 is the shipped ceiling

**Why the card rests on it.** `bm_health.py`: *"wheel health at the shipped ceiling 200..400; JC3
has no unbreakable-wheel member"*.

**Test.**

```
$ grep -n skew_health Research/JC3Grab/VOCABULARY.md
| `front_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) |
| `rear_wheels_damage.skew_health` | int32 | 200 .. 400 (med 200, n=145) |

$ python  # bm-002 vs bm-009 land_global
sizes 3399 3399
diff bytes 4 [108, 109, 120, 121]
offset 108 from 200 to 400 raw 90010000
offset 120 from 200 to 400 raw 90010000
```

**Result.** 400 is the fleet maximum and the write is exactly where the card says. Two caveats: the
range is a **145-module** sample, not 233 (the other 88 vehicles have no `wheels_damage` block), and
`skew_health` is a name-only bridge — `Research/challenge/card-T-14.md` §14 rates it **WEAK**,
because the part table's `Land_Wheel.initial_health` 1020 is the other candidate for "wheel health".
The row is also inert if the wheel's `damage_type` never resolves to a wheel row (it does:
`Land_Wheel` is in the 24-name table).

**Verdict: HOLDS** for the ceiling, **WEAK** for the semantics.

---

## 12. B9-12 — the `.epe` repoint is one 4-byte Jenkins-path write

**Why the card rests on it.** §12: *"the `.epe` root `damage` hash 670,155,287 -> 1,928,726,201 =
`hash_jenkins` of the private path (one 4-byte write under name hash `4f489f01`, type 0x0e)"*. The
whole repoint, and therefore the private module being used at all, depends on this reading.

**Test.**

```
$ python  # Tools/scripts/rbmhdr.hash_jenkins
'damage'                     1330159361  0x4f489f01
'editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc'  670155287  0x27f1c217
'editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile_health_medium.vmodc'  1928726201  0x72f606b9

$ python  # .epe bytes 469..478, both builds
bm-002 bytes 469..478: 0e019f484f17c2f127  type_at_469=0xe namehash=0x4f489f01 value=670155287
   occurrences of shared 670155287 [474]
   occurrences of private 1928726201 []
bm-009 bytes 469..478: 0e019f484fb906f672  type_at_469=0xe namehash=0x4f489f01 value=1928726201
   occurrences of shared 670155287 []
   occurrences of private 1928726201 [474]
```

**Result.** Every element reproduces: the name hash is `Jenkins("damage")`, the old and new values
are `Jenkins` of the two vfs paths, the type byte is `0x0E`, the write is 4 bytes at 474, and each
hash occurs exactly once. `DAMAGE_MECHANISMS.md` §1 calls the property an "object id", but a 32-bit
match to a specific path (1-in-4·10⁹) plus 6 distinct values over 126 cars (`670155287` × 77,
`2496887` × 9, …) is consistent with the path-hash reading and with nothing else on disk.

**Verdict: HOLDS.**

---

## 13. B9-13 — no re-encode, no growth, members identical

**Why the card rests on it.** §12: *"values written at their decoded `offset-in-file` so no file
grows, 245 health members and 61 land_global members re-read identical"*; `bm_health.py`'s docstring
promises the module is *"not re-encoded (no size change, no +544 B placement padding — MODLOG
§101b)"*.

**Test.** Compare bytes directly instead of trusting the decoder's re-read:

```
$ python  # bm-002 shared vs bm-009 private
sizes 3741 3741
differing byte positions 2 [80, 81]
max_health 80 base 2000 priv 36000 raw a08c0000
deform_scale 152 base 0 priv 0 raw 00000000
impact_damage_factor 148 base 0 priv 0 raw 00000000
explosion_threshold 168 base 4000 priv 4000 raw a00f0000

$ python  # land_global bm-002 vs bm-009
sizes 3399 3399  diff bytes 4 [108,109,120,121]

$ python  # independent count of the module's member rows
member rows in the layout dump (unique offsets): 245
```

**Result.** Exactly the two bytes of 36000 differ (2000 = `d0 07`, 36000 = `a0 8c` — only the low
two bytes move), the land_global edit is the two int32s, sizes are unchanged, and 245 is the real
member count. This is the strongest part of the card: the write is surgical and the claim is
literally true.

**Verdict: HOLDS.** (Caveat on the *method*, not the result: the generator's own "moved members"
test compares decoded strings, not bytes, so it would miss a same-printing float change. My byte
diff does not.)

---

## 14. B9-14 — four files changed, 605 `.toc` records, module internal

**Why the card rests on it.** §12: *"packed, 605 `.toc` records, private module internal at offset
23,222,112; `aafdiff` vs bm-002 exactly 4 files"*.

**Test.** `python Tools/scripts/aafdiff.py` over these trees exceeded my 60 s budget, so I diffed the
unpacked `verify/` trees myself (size + sha256 per file):

```
files 684 685
added   1 ['editor/entities/…/batmobile_health_medium.vmodc']
removed 0 []
changed 3
   @files.xml
   editor/entities/…/v0300_car_kensington_sportsmuscle_civilian_01.epe
   editor/entities/…/modules/default/v0300_car_kensington_sportsmuscle_custom_land_global.vmodc
```

```
$ python  # eetoc read of Builds/bm-009/<ee>.toc + .ee
records 605, ee-dir entries 703
toc record  batmobile_health_medium.vmodc (23222112, 3741) internal
packed bytes sha256 == staged copy: True
```

**Result.** Four files, 605 records, internal, slice equals the staged module. The one thing this
check does *not* bound is the `.ee`'s other internal records (B9-03): 604 of the 605 records came
from bm-002 and one of them is the shared health module.

**Verdict: HOLDS** (for the claim as written).

---

## 15. B9-15 — `damage_predict.py --root Builds/bm-009` reads the entity's module

**Why the card rests on it.** Done check 2 is the card's second Done criterion. It printed
`[recorded] build under test: Builds/bm-009 (build_bm-009, max_health 36000)`.

**Test 1 — what the code selects.**

```
$ sed -n 130,150p Tools/scripts/damage_predict.py
def health_from_build(build: str) -> dict:
    from t1_current import dump
    doc = dump(build)
    for tag, mod in doc["modules"].items():
        if mod.get("instance") == "VehicleDamage" or "health" in tag:
            …
            if "max_health" not in scalars:
                continue
            return {…}
```

There is no `.epe` lookup here (`find_epe` is used only for the root `health`/`invulnerable`
fields), and `t1_current.dump()` inserts modules in `os.walk` order.

**Test 2 — the walk order in this tree.**

```
$ python  # os.walk(Builds/bm-009), health/land_global .vmodc files in visit order
Builds/bm-009\aaf\editor\entities\jc_vehicles\00_shared\modules\health\lave_health_medium.vmodc
Builds/bm-009\aaf\editor\entities\jc_vehicles\01_land\…\batmobile_health_medium.vmodc
Builds/bm-009\aaf\editor\entities\jc_vehicles\01_land\…\modules\default\…_custom_land_global.vmodc
…
Builds/bm-009\verify\editor\entities\jc_vehicles\00_shared\modules\health\lave_health_medium.vmodc
```

The **shared 2000-HP module is visited first**. `health_from_build` therefore returns it (its tag
`lave_health_medium` contains "health" and its scalars contain `max_health`), and the table would be
computed at 2000 → `2 / 3 / 2`, not `24 / 48 / 25`.

**Why the recorded output says 36000 anyway.** `damage_predict.py`'s mtime is **00:59**, the build
and receipt are **00:54**, `bm_health.json` **00:54**, `damage_audit.py` **01:04** — the recorded
Done check 2 was produced before the current source existed. Either the earlier version resolved the
`.epe`, or the shared module failed to decode in that run; nothing on disk says which. (I did not run
it: `t1_current.dump` shells `ConvertAdf` and writes `E:/Modding/JustCause3/_grab/tmp_t1`, outside the
repo.)

**Result.** The number Done check 2 prints is an artefact of directory enumeration order, not of the
`.epe`. A copy of the tree whose `01_land` enumerates first would silently print 2000 with a full,
plausible table and still "pass" the Done line. `damage_audit.py` was fixed for exactly this failure
mode (`epe_damage_module`, "The audit used to read whichever `VehicleDamage` module the decode
produced first"); `damage_predict.py` was not.

**Verdict: WEAK** — the run is unreproducible from current code; the risk is silent wrong numbers,
not a crash. (Cannot be upgraded to BROKEN without executing the decoder.)

---

## 16. B9-16 — 36,000 is a value the engine will honour

**Why the card rests on it.** `max_health` 36,000 is 9× the fleet maximum (`500..4000`,
`VOCABULARY.md:1478`, n=233) and is shipped as a declared switch. A switch still has to be a value
the receiving code accepts.

**Test.** What the files say about the field's storage and about any consumer range:

```
Working/Damage/_dump_health_full.txt
  @00000050   max_health   int32   1800          # serialized int32, 4 bytes, LE
bm-009: a0 8c 00 00 → 36000
```

No file in the repo states a runtime width, a clamp, or a consumer that scales `max_health`; the
only decoded consumers are the three models in `DAMAGE_MODEL.md`, all of which are the project's own
formulas. 36,000 fits the serialized `int32` but not an `int16`/`uint16` consumer, and no shipped
vehicle has ever exceeded 4,000 — the fleet gives no positive evidence either way.

**Result.** This is an UNKNOWN the card treats as buildable. R4 says `assumed` is not buildable; the
value is declared as a switch (which R4 permits for an off-switch or saturation cap), but 36,000 is
neither — it is a translation target from a broken ratio (B9-05). The card should carry it as
"pending Q1-DM-A", which `damage_switches.json` does, and §12 does not.

**Verdict: WEAK/UNKNOWN.**

---

## 17. What the challenge did **not** find

- The **write mechanics** are sound: the offsets are the decoder's own, the file does not grow, the
  `.toc` record is internal and matches the `.ee` directory, the slice equals the staged file, and
  the `.epe` hash is exactly the Jenkins of the private path. B-09's four tamper tests are a real
  regression net for those.
- The **build is not installed** (`receipt.json` `"installed": false`, `install.ps1` never run per
  §12); nothing was written to `D:/Games` by this card.
- The **R7 diff** (bm-009 vs bm-002) is genuinely zero; the defect is the baseline, not the delta.

## 18. What the card should say instead

1. The private module is a **clone of the build's drifted copy**, not of the game's
   `lave_health_medium.vmodc`: 23 members differ from the shipped file (B9-01/B9-02/B9-10), and the
   copy should be sourced from the pristine file and re-declared, or the drift should be recorded
   on the row.
2. The `.ee` **ships the shared health module internally** and 77 cars reference that path (B9-03);
   either internalise nothing for that path or add the fleet-wide effect to §12.
3. `explosion_threshold`/`npc_explosion_threshold` must move with `max_health` or the pair must be
   declared as the first non-`threshold == 2 × max_health` module in the fleet (B9-07).
4. "No row exists" must become "no row in the 24-name `Land_*` table; rows exist in the `Train_*` /
   `Boat_*` / `Plane_*` tables and are not transferable without a value nobody measured" (B9-08),
   and the 8/59 part fallback should be a check that can fail (B9-09).
5. Done check 2 must resolve the module through the `.epe`, as `damage_audit.py` already does
   (B9-15).

---

*Read-only pass; only this file was written. No game launch, nothing under `D:/Games`, no commit,
no secrets. Commands quoted are from this session except where marked `[recorded]`, which is MODLOG
§"B-09 · private health module — done" (line 17291–17390).*

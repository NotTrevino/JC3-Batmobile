# Review — T-20 · World translation

**VERDICT: minor issues.** The card is structurally sound: both Out paths exist, `--check` passes and
actually gates the Done line against the eight-code list, the document is generated rather than
hand-written, and every substantive value I checked is in the input file or recomputes. The problems
are in the *evidence wording* and in a handful of typed constants: one row describes a measurement of
the new leaf that the scan never made, four counts that the inputs already carry are hard-coded in the
generator, and the "the fleet agrees" claim in `T-WLD3` is printed without a gate. None changes a
disposition; two would survive a change in the inputs that they claim to track.

Reviewed read-only. Nothing outside this report was written; no game launched; no commit; no secret read.

## Check output (verbatim)

```
> python Tools/scripts/t15_world.py --check
PASS: 19 rows | WLD codes 8/8 | dispositions next 5, keep 6, epe 3, blocked 3, out 2 | ledger 19/19
EXIT=0
```

Identical to the line recorded in `MODLOG.md` §"T-20 · World translation — done". I did not re-run the
four tamper tests: they require editing the output files, which this review must not do. Their
mechanism is visible in `cmd_check()` — it re-derives the payload and the md text, compares both to
disk, and diffs the first differing character / unified diff line.

Standing gates re-run (read-only), both green:

```
> python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

(The ledger is 198 rows now because later cards ran; the MODLOG's "164 → 183" was true at the time.)

## Card, outputs and Done line

| item | state |
|---|---|
| card `Done:` (GRAB_BACKLOG.md:952-957) | every WLD code has rows |
| `Out:` doc | `Working/Translation/T15_WORLD.md` — exists, 158 lines, generated |
| `Out:` rows | `Working/Translation/T_ROWS.jsonl` — 19 `T-WLD*` rows, `doc` = `T-20`, 5 `next` / 6 `keep` / 3 `epe` / 3 `blocked` / 2 `out` |
| json named in §12 | `Working/Translation/t15_world.json` — exists, 42,663 B |
| script | `Tools/scripts/t15_world.py` — 973 lines, `--write` / `--check` / `show` |
| §12 row (GRAB_BACKLOG.md:1329) | evidence set and counts agree with the doc and the json |

**Done ↔ check.** `build_payload()` ends with

```python
for code in CODES:                      # CODES = WLD-1 … WLD-8, the §1.9 list
    if not counts["rows_per_code"].get(code):
        problems.append(f"{code} has no row")
```

so "every WLD code has rows" is genuinely gated against a canonical list, not against the rows
themselves. The `PASS` line's `covered` is `len(set(codes_covered) & set(CODES))`. This is the
strongest part of the card. The doc's own "All 8/8 codes have at least one row, which is the card's
`Done` line" is therefore backed.

## Issues

### 1. `T-WLD18` describes a measurement of the new leaf that was never made

`Working/Translation/T15_WORLD.md:118`, `Tools/scripts/t15_world.py:541-548`.

The cell reads: *"the new leaf `v0300_car_kensington_sportsmuscle_batmobile` has 0 records there
(G2-29's 11,751-file scan found 17 name-sites, none of them this leaf)"*. The scan's needle is the
**donor** (`TRAFFIC.json scan.needle = "v0300_car_kensington_sportsmuscle_civilian_01"`), and its 17
hits are files containing the donor's name, so "none of them this leaf" is true by construction and
establishes nothing about the new leaf. `--check` asserts only `selectors == 41` and the donor
record's `ambient`/`liberated` tags; nothing reads the new leaf against `spawn_vehicle_defs.bin`. The
input cannot even separate the two leaves in its per-table summaries — both start `v0300`, and
`spawn.tables.settings/spawn_vehicle_defs.bin.v0300` holds exactly one entry, the donor's.

The conclusion (keep, add nothing, no AI selection) is sound, but it follows from **D-6 = standalone**
plus "a leaf that was never added cannot be selected", not from a scan of the new leaf. As written it
is a claim the data cannot support. Fix: drop the parenthetical measurement, or reword to "the donor's
name is in the table; the new leaf cannot be there because the build never writes it".

### 2. R11 — four numbers the inputs already carry are typed into the generator

Each is correct today (I verified all four); none is re-derived, so `--check` cannot catch it going
stale.

| value in the doc | where | the input that already has it |
|---|---|---|
| "18,688 B for every vanilla vehicle" | `t15_world.py:371` (literal in the T-WLD5 source string) | `INDEX.jsonl`: 113/113 `textures/ui/vehicle_icons/*.ddsc` are 18,688 B |
| "the donor's surfaces scale 0.374-0.596 m" | `t15_world.py:432` (T-WLD10 source) | `INTERACTION.json stunt_areas.areas[*].bat_max_clearance_m` = 0.374, 0.374, 0.5955 — which the same row's carrier cell already computes as `0.5955` |
| ratio denominators `40000 / 100000 / 15000`, and "cargo plane 25,000/40,000, transport boat 100,000, monorail flatbed 15,000" | `t15_world.py:298-299` and `:521` | `TETHER.json carriers.models` (`v4603_plane_urga_cargotransport` **[25000, 40000]**, `v1602_boat_urga_transport` [100000], `v5602_train_urga_monorailflatbed` [15000]) |
| "11,751-file scan found 17 name-sites" | `t15_world.py:545-546` | `TRAFFIC.json scan.files = 11751`, `scan.hits` has 17 entries |

Note the third one is the sharpest: the *derived-looking* percentages `15.0 % / 6.0 % / 40.0 %` are
computed from hard-coded capacities, not from `F["tether"]["models"]`, so a changed carrier mass would
produce a stale percentage that `--check` still passes. R11 says "counts are generated, never typed";
these four are the doc's only typed measurements.

### 3. `T-WLD3`'s "the fleet agrees" cell has no gate

`Tools/scripts/t15_world.py:339-343`:

```python
f"{r['vanilla_vehicle_items']}/{r['vanilla_vehicle_items']} vanilla vehicle drops: "
f"Type {vp['Type'][0]}, UIType {vp['UIType'][0]}, Rewardable {vp['Rewardable'][0]}, …"
```

The fraction is the same variable twice (`n/n` is always true) and each value is `[0]`, the first
element of the set gathered in `gather()` — no assertion checks that those sets are singletons.
Today the claim is true: across the 45 vehicle drops the sets are `Type [1]`, `UIType [3]`,
`Rewardable [1]`, and `[0]` for `Purchasable`, `Collectable`, `Consumable`, `DlcId`, `Region`,
`MaxInventory`; the multi-valued fields (`UIFlag`, `UIDisplayOrder`, `RebelDropTimer`) are correctly
printed as lists. So the sentence is right by luck of the data, and would read identically on a mixed
fleet. Contrast the `BaseName` rule, which *is* asserted (`:600`) — that one deserves the confidence it
gets. Fix: assert the nine sets are singletons (or print the set), then print `{n}/{n}` honestly.

### 4. `--check` does not verify the ledger's `doc` tag

`Tools/scripts/t15_world.py:889-935` checks each row's presence, `dispo`, a non-empty `why` and the
`cells`. T-18's checker also compared the document tag (`if ledger[id]["doc"] != "T-14"`). Here the
tag is `T-20` while the document file is `T15_WORLD.md` — by design (`t_rows.py:45` registers
`("T-20", T15_WORLD.md)`), so nothing is wrong today; but a row filed under the wrong document would
pass this card's gate. One line restores parity with T-18.

### 5. Minor / cosmetic

- `T15_WORLD.md:9` — "One row per world requirement, grouped under the eight `WLD` codes" while the
  header prints `len(s['codes'])`/8 (`t15_world.py:722`). With the `CODES` gate this cannot go wrong in
  practice; an out-of-namespace code would print e.g. `9/8` rather than failing.
- §3's `UIPar0…4` are labelled "decoded (the donor's, a UI scale parameter)" and `DlcId 0` "class
  (0 = base game)". The values are decoded (copied from the donor) — correct — but "UI scale
  parameter" and "base game" are interpretations, and §6 lists the timer unit, the enum meanings and
  the mass unit as UNKNOWN without listing these two. One sentence in §6 would cover it.
- §2 and §4 both tabulate rows per code (the §4 table is generated from `rows_per_code`; §1's is too).
  Duplication only.

## Spot-checks

| # | value in the doc | where verified | result |
|---|---|---|---|
| 1 | leaf hash `443190071` = `1A6A8B37`; `BaseName 276735921` | `rbmhdr.hash_jenkins("v0300_car_kensington_sportsmuscle_batmobile")`, `…("v0300")` | exact; and `BaseName == hash(<imagepath prefix>)` on **45/45** vehicle drops, recomputed independently |
| 2 | name/blurb pairs: donor `D2B46B49` → "KERNER SERPENTE R" in 11/11, new hash 0/11; `2432797658` "SPORTS CAR", `1383769868` "SPORTS CARS" | live `profile/online.stringlookup` via `jc3strings.decode_stringlookup` + `resolve` (same path the tool uses) | store has **11** languages; `443190071` → 0; `3535039305` (= 0xD2B46B49) → "KERNER SERPENTE R" in 11; `2073308658` → "Kerner's top sports model…" in 11; both caption hashes in 11 |
| 3 | icons: 113 files, 18,688 B each, new leaf absent, placeholder present | `Research/JC3Grab/INDEX.jsonl` `textures/ui/vehicle_icons/` | 113 files, **all** 18,688 B; `v0300_…_batmobile.ddsc` absent; `placeholder.ddsc` and the donor icon 18,688 |
| 4 | mass 975 → **6000** = 6.154× donor, 3.0× car median; carrier shares 15.0/6.0/40.0 % | `TETHER.json mass` (`donor.mass 975`, `batmobile_target 6000`, `families.car.median 2000`, `models` masses 40000/100000/15000) | 6000/975 = 6.1538 → 6.154; 6000/2000 = 3.0; 15.0 / 6.0 / 40.0 exactly |
| 5 | stunt areas: 3 active in 32 slots, 64 weld rows of which 8 real (0-1 ×6, 0-2 ×1, 1-2 ×1), 0 vertices on the shell, worst 0.5955 m, gaps 0.1035/0.1035/0.0197 | `INTERACTION.json stunt_areas` | all match; clearances 0.374 / 0.374 / 0.5955 |
| 6 | traffic: 27,513 B, 86 records, 8 keyed, donor record at offset 23240 with 13 tags, 1 of 41 selectors → `03_CivilianCarLiberatedProvince` | `TRAFFIC.json spawn.main`, `spawn.donor_record`, `rules` | all match; selector string `ambient,ground,car,liberated,-highend` |
| 7 | water: `will_sink` 1, buoyancy 2.0 / drag 100.0 / radius 0.55 / side_area 1.85 / bottom_area 3 / cap 20 / 1 hull element; constants 10, 20, 20, 50, 30 | `WATER.json build.modules`, `constants.rows` | all match; `build_check.identical` True; census 189 sink / 35 boat / 8 float = 232 |
| 8 | entry/exit/stunt placement: 77 of 85 in the 0.05-0.3 m band, left x −1.471 / right x 1.462 at y 1.15, z −0.95; roof 2.0811 at z −0.5; deck 1.3606 at z −2.14 | `Working/Translation/t9_interaction.json counts/band_m/anchors` | all eight numbers match exactly; 6 hijack objects dropped |

§3's 26-field table also equals `REBELDROP.json recipe.fields` value for value (including
`Feats: ''`, `UIFlag 5`, `UIDisplayOrder 3`, `RebelDropTimer 1800`, `UIPar0…4`), and the recipe has
26 fields against a 26-member `Item` schema — the `26/26` cell in `T-WLD1` is real.

## What is sound

- **Done line gated for real** (issue-free): the `CODES` loop is a genuine coverage test, not a count
  of whatever the rows happen to say.
- **Derivation**: apart from the four constants in issue 2, every number in the doc is an f-string
  over `gather()` (or a count of the same); `--check` re-derives both files, byte-compares them, and
  cross-checks the ledger's cells and dispositions.
- **R4**: no `assumed` class; the `blocked` rows name the missing write side (`.stringlookup` writer,
  the deform-point list) and the `out` rows the absent carrier (no vehicle tether member, no
  helicopter cargo bay); the mass unit, the timer unit and the three enum meanings are UNKNOWN rather
  than converted — including the deliberate refusal to turn 6,000 into kilograms.
- **R5** (behaviour before member): `T-WLD12` is the model — the behaviour is "shoves cars, flattens
  fences", the member is only `rigid_body.mass`, the contact response is handed to T-22's hull, and
  the probe (ram at 40/80 km/h) can fail. `T-WLD13`/`T-WLD14` likewise separate `will_sink` /
  `vehicle_common` constants from the observable behaviour.
- **Blocked ≠ dropped**: §5 lists each `out`/`blocked` row with what is missing and what carries it
  instead, which is what makes the dispositions auditable.

## Recommended

1. Reword `T-WLD18`'s carrier (issue 1) so it does not claim a measurement of the new leaf.
2. Interpolate the four typed values (issue 2) from `INDEX.jsonl`, `INTERACTION.json`,
   `TETHER.json models` and `TRAFFIC.json scan` — the last one also fixes the ratios' denominators.
3. Assert the nine `vehicle_item_profile` sets are singletons before printing `[0]` and `n/n`
   (issue 3).
4. Add the `doc` tag comparison to the ledger loop (issue 4) — one line, parity with T-18.

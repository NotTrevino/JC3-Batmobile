# T-FX16: which search term gives "0 of 955"?

**Verdict: the term is `canon_trail` plus `shell_trail` - the `match` list of the T-FX16
rule in `Tools/scripts/t17_fx.py` line 154 - and each needle, and their union, returns exactly 0 of 955.**
The row and `T13_FX.md` publish the result without the term, so the claim was not
checkable from the document alone; the term was never lost, only left in the generator.

**But the 0 is term-specific.** The word `trail` alone returns 84 of 955 (46 vehicle-carried): JC3 has plenty of
trail effects, none of them spelled `canon_trail` or `shell_trail`. A reader who
reconstructed the search as `trail` would get a very different number, so the proof line
has to name its needles to be worth anything.

## Method

* Pool: the 955 distinct `.effc` paths in `Research/JC3Grab/FX_TABLE.jsonl`,
  re-derived with `t17_fx.py`'s own rule; 589 of them are vehicle-carried (a
  container path contains `/jc_vehicles/`). Both counts agree with `t17_fx.json`'s
  `summary.fleet_effc` / `fleet_vehicle_effc`.
* Test: case-insensitive substring on the full effect path - exactly what the generator
  does (`any(m in p for m in rule['match'])`).
* The omission's pool is `no_paths`, i.e. all 955, not the 589 subset (`no_vehicle_paths`
  is what T-FX13 uses).

## Counts per candidate

| candidate | where the candidate comes from | matches / 955 | vehicle-carried / 589 | first hit |
|---|---|---:|---:|---|
| `canon_trail` | decoded: the T-FX16 `match` list in `t17_fx.py` **reproduces** | 0 | 0 | - |
| `shell_trail` | decoded: the same `match` list **reproduces** | 0 | 0 | - |
| `cannon` | row text: the feature is `cannon round trail` - zero too | 0 | 0 | - |
| `trail` | the shared word of the feature, the row and the BmAK group `projectile-trail` | 84 | 46 | `bavarium_trail_01.effc` |
| `bullet` | row text: JC3 draws the round as a `tracer` on the bullet (T-FX12) | 23 | 16 | `bullet_eject_capstone.effc` |
| `projectile` | the BmAK group name `projectile-trail` | 1 | 0 | `dlc_powercore_projectile.effc` |
| `round` | row text: `the round is represented by the tracer texture` | 11 | 10 | `dlc_exp_grunt_ground_drone.effc` |
| `rocket` | BmAK name `Batmobile_JokersRocket_Trail` | 5 | 5 | `dlc_dmg_burn_engine_rocketboat_01.effc` |
| `mud` | BmAK name `Batmobile_Mud_Trail` | 1 | 0 | `rico_foot_step_mud.effc` |
| `canon` | the one-n spelling that does occur (control, shows the spelling trap) | 1 | 1 | `tank_canon_muzzleflash.effc` |
| `tracer` | the T-FX12 cross-reference in the row's `propose` (control) - zero too | 0 | 0 | - |
| `spark_trail` | T-FX19's term, a different row (control) | 8 | 3 | `dlc3_spark_trail_01.effc` |
| `exhaust` | T-FX7/T-FX8's family, a different row (control) | 39 | 37 | `rocketboat_jet_exhaust.effc` |
| `smoke` | control: the fleet's smoke vocabulary | 29 | 20 | `dlc_dmg_smoke_engine_rocketboat_01.effc` |
| `missile` | control: T-FX14's family | 30 | 25 | `rocket_boat_missile_trail.effc` |

Candidates returning 0 of 955: `canon_trail`, `shell_trail`, `cannon`, `tracer`.

## Reading the table

* **The decoded pair is the only one that is also the row's own search.** `canon_trail`
  and `shell_trail` are what `t17_fx.py` feeds to the absence test for T-FX16, so the
  published "0 of 955" is their union's count, reproduced here: 0 paths.
* **Zero alone does not identify a term.** `cannon`, `canon_trail`, `shell_trail` and the
  T-FX12 control `tracer` all return 0, for unrelated reasons. A bare "0 of 955" is
  therefore not evidence of anything until the needle is printed beside it.
* **The spelling trap is real.** `cannon` (two n) returns 0 while `canon` (one n) returns 1
  - `effects/jc_weapons/muzzle_flash/tank_canon_muzzleflash.effc`. The generator chose
  the one-n spelling, which is why its muzzle term finds the fleet's tank flash; a search
  for `cannon` would report an absence where a file exists.
* **What is actually absent is narrow**: no effect path calls itself a cannon or shell
  trail. Trails exist (84), missile trails exist (30, T-FX14 keeps one), bullet effects
  exist (23), and the bare word `projectile` names one DLC effect. Whether any of those
  *is* a cannon-round trail is a different question from what the path is called.
* **The row's conclusion is unchanged** by naming the term: with `canon_trail` +
  `shell_trail` the count is still 0, so the named omission still holds on its own terms.
  What changes is that the claim can now be re-run by a reader.

## The row as it stands, and the one-line repair

`t17_fx.json` records the T-FX16 omission as:

```json
{
 "candidates": [],
 "matches": 0,
 "test": "no_paths"
}
```

`T13_FX.md` §4 prints it as "0 of 955 match over all distinct `.effc` paths" with no
needle. A proof line that names its term would read, without any other change:

> 0 of 955 match `canon_trail` or `shell_trail` over all distinct `.effc` paths
  (`t17_fx.py` T-FX16 `match`)

That is proposed here as text only. **No row, ledger, document or JSON file was edited** -
`T13_FX.md`, `t17_fx.json` and `T_ROWS.jsonl` are opened read-only.

## What this does not settle

* **Whether a JC3 cannon-round trail exists under another name.** The paths carry no
  such name, but the 84 `trail` effects, 30 `missile` effects and 23 `bullet` effects were
  not opened one by one here; deciding that one of them *is* the cannon round trail is
  UNKNOWN, and belongs to a content read, not a name search.
* **Whether the BmAK side needs the trail at all**: the row's answer (the round shows as
  a tracer texture, T-FX12) rests on `WEAPONS.md` §6 and is not re-tested here.
* **Runtime**: nothing was launched; the test ban stays.

## Oracles re-run by `--check`

* PASS FX_TABLE.jsonl holds 955 distinct .effc paths (955)
* PASS 589 of them are vehicle-carried (589)
* PASS t17_fx.json's own summary agrees (fleet_effc 955, fleet_vehicle_effc 589)
* PASS T-FX16's `match` list in t17_fx.py is ['canon_trail', 'shell_trail']
* PASS the rule is at t17_fx.py line 154
* PASS t17_fx.json records the omission as no_paths with 0 matches and no candidates
* PASS the T-FX16 row/doc does not name `canon_trail` (the defect)
* PASS the T-FX16 row/doc does not name `shell_trail` (the defect)
* PASS T13_FX.md carries the unqualified proof string for T-FX16
* PASS `canon_trail` matches 0 of 955 (0 vehicle-carried)
* PASS `shell_trail` matches 0 of 955 (0 vehicle-carried)
* PASS `cannon` matches 0 of 955 (0 vehicle-carried)
* PASS `trail` matches 84 of 955 (46 vehicle-carried)
* PASS `bullet` matches 23 of 955 (16 vehicle-carried)
* PASS `projectile` matches 1 of 955 (0 vehicle-carried)
* PASS `round` matches 11 of 955 (10 vehicle-carried)
* PASS `rocket` matches 5 of 955 (5 vehicle-carried)
* PASS `mud` matches 1 of 955 (0 vehicle-carried)
* PASS `canon` matches 1 of 955 (1 vehicle-carried)
* PASS `tracer` matches 0 of 955 (0 vehicle-carried)
* PASS `spark_trail` matches 8 of 955 (3 vehicle-carried)
* PASS `exhaust` matches 39 of 955 (37 vehicle-carried)
* PASS `smoke` matches 29 of 955 (20 vehicle-carried)
* PASS `missile` matches 30 of 955 (25 vehicle-carried)
* PASS the union of the decoded needles is 0 of 955 - the row's count reproduces
* PASS every decoded needle is in the zero set ['canon_trail', 'shell_trail', 'cannon', 'tracer']
* PASS the broad word `trail` does not reproduce 0 (84 hits)

## Labels

Decoded: the 955/589 pools and every count, the T-FX16 `match` list and its line number,
the row's `absence` record, the `T13_FX.md` proof string. Derived: the reconstruction of
which candidate the row means, the reading of the zero set, the proposed proof line.
UNKNOWN: everything under "What this does not settle".

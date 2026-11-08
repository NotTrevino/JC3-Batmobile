# Independent review — G2-10 · Vehicle weapon catalogue (old WPN-1)

Reviewer: Buffy (did not write this card). Read-only: no file under `GRAB_BACKLOG.md`, `MODLOG.md`,
`Research/`, `Tools/` or any game file was modified; no game launched; nothing committed.

Files read: `GRAB_BACKLOG.md` §0.5 (R1–R14) + card G2-10 (l. 584–597) + §12 row (l. 1293);
`MODLOG.md` §"G2-10 · … — intended change" (l. 9140) and §"… — done" (l. 9174);
`Research/JC3Grab/WEAPONS.md` (1,223 lines), `WEAPONS.jsonl` (25 rows), `WEAPONS_SHARED.json`
(24 tunes), `Tools/scripts/jc3weapons.py` (1,011 lines), `Research/JC3Grab/FEATURE_CENSUS.json`,
`Research/JC3Grab/INDEX.jsonl`, `Research/JC3Grab/WEAPON_WIRING.jsonl` (cross-card check only).

## VERDICT

**minor issues.**

The decode is sound and the check is real: `--check` re-reads every container out of the archives,
re-derives `WEAPONS.jsonl` and `WEAPONS.md` from scratch, compares both byte-for-byte and re-hashes
all 197 extracted copies; the 25-id set is not self-defined but taken from `FEATURE_CENSUS.json`
(P0-2), so "25/25" is anchored outside the tool. Every table value I spot-checked matches the json.

What is not sound is a small set: one **wrong typed count inside the generated doc** (12 helicopters
where the data says 11), several other **typed count literals** in the doc generator that `--check`
therefore cannot guard (R11), **29 stale files in the extraction tree** that the recorded 197 no
longer describes, two **units/labels presented as fact without provenance** (R4/R5), one
**overreaching `JC3 … no heat model at all`** conclusion, and three **misattributed numbers in the
MODLOG done record**. None of this requires re-decoding; none of it changes a weapon value.

## Check output (verbatim)

```
$ python Tools/scripts/jc3weapons.py --check
PASS: 25 ids, 197 extracted files, 24 shared tunes, md 1223 lines
EXIT=0
```

(`EXIT=$?` echoed 0.)

## Done criterion vs what `--check` actually verifies

Card Done: *"25/25 ids (count the `+_impact` variants separately) have a row with every decoded
member; `--check` re-reads the archives and compares."*

Matches, with two limits worth recording:

* The id list comes from `FEATURE_CENSUS.json` (`collect()`, script l. 194–198), not from the tool's
  own scan — so 25/25 is a real cross-check, and the `+_impact` split is counted separately in the
  doc's opening table and in the §1 table rows.
* "every decoded member" is satisfied in the **jsonl row** (each source carries a full
  `decode.instances[].rows` block, 155 leaf rows per `WeaponTuning`, 132 per `AutoAim`, 8 per
  blast) and in the doc by §12 (every member path, indices collapsed) and §13 (shared tunes
  verbatim). §2–§8 of the doc are *selections* of that data, which the card allows.
* Hole: `--check` compares rows and file hashes, so a census id that lost its tune would still
  produce 25 rows with `tunes: []` and still PASS (`--write` prints `WARNING: no tune for …`;
  `--check` does not test it). Not triggered today — all 25 rows carry a tune — but the criterion
  is weaker than it reads.
* Consequence that produced Issue 1: `--check` regenerates the md from the *same* generator, so any
  fact typed into the generator prose is verified only against itself, never against the decode.

## Issues

### 1. Wrong count in the generated doc — `WEAPONS.md:25` (blocking for the "no typed values" test)

> `w604_helicopter_mgun_impact` on 3 `v2601` + 9 `v2602`/`v2604` helicopters per the census

That is 12 helicopters. The data says **11**: `WEAPONS.jsonl` row `w604_helicopter_mgun_impact`
lists 11 carriers — 3 × `v2601_…heavyassault`, 3 × `v2602_…lightassault`, 5 ×
`v2604_…advancedassault` — and `FEATURE_CENSUS.json` → `weapon_ids` gives `"entities": 11`, which
the same doc's own §1 table prints on l. 33. The "9" is simply a miscount of 3 + 5. Cause: the
sentence is a literal in `Tools/scripts/jc3weapons.py:546`, i.e. a typed value (R11) that
`--check` cannot catch because it regenerates the same literal. The card's whole premise is
"counts are generated", so this is the one finding that should be fixed in the generator.

### 2. Other typed count literals in the doc generator (R11, currently benign)

`Tools/scripts/jc3weapons.py:542` "exactly two standalone `.ftunec` archive entries",
`:685` "the census's 25 ids, 26 spellings", `:691` "Only three ids ship their own preset".
I verified all three independently — `INDEX.jsonl` has exactly 2 `.ftunec` entries
(`gen_explosion_0.5m_nodamage`, `structures/barrel_explosion`); the census has 25 ids / 26 spellings;
`WEAPONS.jsonl` has 3 rows with an `AutoAim` tune — so none is wrong today. They are the same defect
class as Issue 1 (a number in a generated doc that no command derives), which is why Issue 1 was
possible.

### 3. Extraction tree no longer matches the recorded 197 files — `WEAPONS.md:458`

`--write` extracted **197 files** (21,487,435 B)`, "**197 files**" and the byte total are correct for
the record (`WEAPONS.jsonl` `extracted` = 197 entries, 197 unique paths, all present, all sha1-match).
But `E:/Modding/JustCause3/_grab/weapons` holds **226 files**: 29 extra ones left behind by the 17:04 run
(mtime `2026-10-26 17:04`; the recorded set is 17:31/17:32). They are re-attributed copies of the
same bytes under the wrong id, e.g.

```
weapons/w604_helicopter_mgun/v2601_helicopter_urga_heavyassault_debug__w604_helicopter_mgun_impact.ftunec
weapons/w610_fighterjet_mgun_impact/v4202_plane_capstone_fighterjet_debug__w610_fighterjet_mgun.wtunec
```

`--check` iterates only the recorded paths, so stale or junk files in the tree are invisible to it,
and the doc's sentence describes what the last `--write` wrote rather than what is on disk. Either
say "the record lists 197 files" or clean the tree in `--write`; as written, a reader who counts the
directory gets 226 and a mismatch.

### 4. `fire_rate` unit asserted, not derived (R4/R5) — `WEAPONS.md:57`, `:82`, `:428`

Header "`fire_rate (s)`", body "`fire_rate` is the seconds between shots (0.1 on the buggy MG is 10
shots/s)", §10 "| fire rate | `fire_rate` | seconds per shot |". No decoded member states a unit;
the reading is inferred from magnitude (0.1 on the MGs vs 1.75 on the tank canon), which is very
likely right but is still a behaviour claim from a member name. It matters because the value is
already consumed downstream (`Tools/scripts/damage_predict.py` builds DPS from
`WEAPONS.jsonl` `fire_rate`). The same doc handles the harder case correctly — `SnapAimTarget` is
explicitly `UNKNOWN` because "its unit is not proven" (§10) — so the standard is applied unevenly.
Same for `reload_time_scale` 0 → "no reload step is scaled in" (`:82`), another name-based reading.

### 5. Overreach on the heat question — `WEAPONS.md:449` (and MODLOG §"G2-10 … done", "The two absences")

> JC3 weapons therefore have no heat model at all: a JC3 Vulcan fires until its ammo runs out

The file answer is narrower and is correct: no member of the decoded tune classes (22
`WeaponTuning` + 3 `AutoAim` + 9 `ForcePulseSettings` + 24 shared tunes) matches
`heat|cool\b|cooldown|temperature` except `burst_cooldown` (`HEAT_RE`, script l. 74; verified by
re-running the decode). "No heat field in any weapon tune" is evidence. "No heat model at all in
JC3" is an absence-of-evidence → absence claim about the engine/HUD, which this card never looked
at; that half should be `UNKNOWN` with the scope stated. The card asked "ammo/clip/reload **or**
overheat", so answering "no overheat member in the tune, engine-side heat not established" satisfies
it fully.

### 6. Numbers misattributed in the MODLOG done record (not in the doc)

* `MODLOG.md:9235` — "Only 4 of the **14** missile ids home at all". `WEAPONS.jsonl` has
  **11** `kind: missile` rows (11 missile + 11 bullet + 3 impact = 25); the four that home are
  `w608` 75, `w609` 150, `w612` 300, `w614` 200, all correct. Should read "4 of the 11".
* `MODLOG.md:9191` — "`WeaponTuning` | 22 | 4,054 over both sides". 4,054 is the **grand total of
  leaf rows across all three classes** (3,586 `WeaponTuning` + 396 `AutoAim` + 72
  `ForcePulseSettings` = 4,054, recomputed from the jsonl). `WeaponTuning` alone is **3,586**, which
  is also what the tool itself prints on `--write` ("… 3586 weapon rows").
* `MODLOG.md:9193` — "`ForcePulseSettings` | 9 + 3 impact ids | 12". The three `+_impact` ids are
  **inside** the 9 (doc §8 table has 9 rows; tracker row says "9 ids"), so "9 + 3" reads as 12 ids;
  and a decoded blast has **8** members, not 12 (doc §13 says "members 8"; 8 keys in every
  `summary.blast`). Both cells overstate.

Everything else in the done record that I could re-derive is right: 161 sources, 67 containers
(14 + 53), 24 shared tunes, 197 files / 21,487,435 B, 26 spellings, 1 alias
(`w613_bomb` → `w613_fighterbomber_missile_ground_lockon`, the only 2-spelling row and the census's
only alias entry), and the "tank canon 1 direct / 1500 blast" reading.

### 7. Nits

* `WEAPONS.md:300` "Only three ids ship their own preset; **the rest bind a shared one**" — the
  binding is wiring, which this doc itself hands to G2-11; the card records which presets sit in a
  bundle, not which weapon binds which. It is true per `WEAPON_WIRING.jsonl`
  (`autoaim_vehicle_mgun` 76 refs, `autoaim_vehicle_no_lockon_missile` 40,
  `autoaim_assault_rifle` 38, `autoaim_w613_bombs` 6, `autoaim_vehicle_lockon_missile` 4), but it is
  not evidenced here.
* `WEAPONS.md:422` stray apostrophe: "… are the player weapons')."; the claim itself is name-derived
  (those presets are indeed absent from the wiring data, so "unused by an armed vehicle" holds for
  the 67 containers examined).
* §5/§6 use `?` with no legend. It means "member not present in this block type" (e.g. every bullet
  row's missile columns), not `UNKNOWN`. Given R4's insistence on distinguishing absent from
  unknown, one sentence would remove the ambiguity.

## Spot-checks

| # | doc value | where verified | result |
|---|---|---|---|
| 1 | §1: 61 rows under `jc_weapons/06_vehicle`, 22 ids with a directory, 14 of those with an `.ee`, 67 containers (14 + 53) | recomputed from `WEAPONS.jsonl` `dir_files` (61, 22, 14) and `FEATURE_CENSUS.json` (`armed_entities` = 53) vs `INDEX.jsonl` (81,952 rows, 61 unique paths under the prefix) | matches |
| 2 | §3 `w602_mediumtank_canon`: 1 / 1 / 1 / 0 / **20** / 10 / 0 / 0 (player dmg, veh x, obj x, impulse, AI dmg, AI veh x, AI obj x, AI impulse) | `WEAPONS.jsonl` → `summary`: `bullet.player.damage` 1.0, `player.vehicle_damage_factor` 1.0, `player.impulse` 0.0, `ai.damage` 20.0, `ai.vehicle_damage_factor` 10.0 | matches |
| 3 | §8 `w604_helicopter_mgun_impact`: 25 / 0 / 1.5 / 0 / 1 / 0.9 | `summary.blast` = PlayerDamage 25, AIDamage 0, PlayerDamageRadius 1.5, PercentageMax 1.0, Min 0.9 | matches |
| 4 | §2 + §5 `w613_…_ground_lockon`: fire_rate 0.2, burst 6, burst_cd 4, mag 6; turning_speed 0, accel [20, 0], accel_time [0.05, 0] | `summary`: 0.2 / 6 / 4.0 / 6, `missile.missile.turning_speed` 0.0, `acceleration` [20.0, 0.0], `acceleration_time` [0.05, 0.0] | matches |
| 5 | §6 + §7 `w620_racingboat_mgun`: tracer 900 / 15 / 0.55 / 0.1 / 1; AI 20 / [10, 100] / 10 / 1 / 3 / 3 / 3 / 3 / 1; §9 `w613` `SnapAimTarget` 0.2 in all six contexts | `summary.bullet.*`, `summary.bullet.ai.*`, `summary.autoaim` (`{OnFoot,Stunting,MotorCycle,ReelingIn,ReeledIn,Parachute}.SnapAimTarget` all 0.2) | matches |
| 6 | Issue 1's counter-evidence: `w604_…_impact` carriers = 3 v2601 + 3 v2602 + 5 v2604 | `WEAPONS.jsonl` row `carriers` (11 entries) and `FEATURE_CENSUS.json` `weapon_ids` → `entities: 11` | doc l. 25 says 12; table l. 33 says 11 |

## Limits of this review

* Read-only, so I did not tamper with `WEAPONS.md`/`WEAPONS.jsonl` to prove `--check` has teeth. By
  inspection it would catch an edited md (byte compare), an edited row (field compare) and an
  edited/deleted extracted file (size + sha1); it would **not** catch a typed prose count
  (Issue 1) or an extra file in the tree (Issue 3). Unlike G2-11, no tamper test is recorded in the
  G2-10 MODLOG entry.
* I did not re-open the game archives by hand; the raw bytes are covered by `--check`'s re-decode
  and by the extracted-file hashes, and my spot-checks went through `WEAPONS.jsonl`.
* No judgement is made here on whether `fire_rate` is really seconds per shot (Issue 4) — that is a
  Q-1-style probe question, and this review only records that the doc states it as fact.

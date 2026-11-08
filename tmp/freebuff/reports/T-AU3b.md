STATUS: done - T-AU3/T-AU5's claim is **proven for the JC3 install**: all **27** distinct BmAK banks the Batmobile references are ABSENT from JC3 by name (index path, FSB5 name table, dropzone file name) and by Jenkins hash (bank name and `sound/fmod_banks/<bank>.bank`), across 81,952 index rows / 78,907 named paths / all 88 archives incl. DLC mounts. The banks do exist in the BmAK install (27 exports), so the rows' `why` is right about JC3 and wrong if read as "never grabbed". 40 derived JC3 candidates are listed for the 10 banks where a decoded sample name matches; the other 17 keep no candidate.

# T-AU3b - are the BmAK audio banks absent from the JC3 install?

## 1. What was tested

Rows `T-AU3` and `T-AU5` (`Working/Translation/COMPROMISES_T.md:45-46`) say the BmAK Batmobile's
audio banks are absent from the install. The banks were taken from
`Research/BatmobileGrab/AUDIO_MAP.json` (the Batmobile's own bank map, 27 exports / 27 distinct
names / 361 events), cross-checked against `AUDIO_BANKS.md` (27-name table plus the 117 exports it
read) and `AUDIO_BANKS2.md`. Every bank was then searched in the **JC3** install by four methods:

| method | what was searched |
|---|---|
| N1 | every named path in `Research/JC3Grab/INDEX.jsonl` - 81,952 rows, 78,907 named paths, 88 archives (base, patch, dlc mounts) |
| N2 | the JC3 banks' decoded FSB5 sample-name tables - 649 names |
| N3 | the live `D:/Games/Just Cause 3/dropzone` tree, bank/pck/fsb file names |
| H1 | Jenkins(bank) and Jenkins(`sound/fmod_banks/<bank>.bank`) against every hash the index carries (named and anonymous entries) |

## 2. Result per bank

All 27 are **ABSENT**: 0 hits on N1, N2, N3 and H1 for every bank. The per-bank table, the exact
hashes searched and the per-bank N1/N2/N3/H1 counts are in `Working/Translation/T_AU3B.md` section 3.
The 7 car/weapon banks are `BML_Batmobile`, `BML_Battlemode`, `BML_Burnout`, `BML_Engine`,
`BML_Tyres`, `VEH_Batmobile_MK2_Engine`, `AUX_InBatmobile`, `WPN_BulletImpacts_Concrete`,
`WPN_BulletImpacts_Ricochet`; the other 18 are dialogue, sequence, prop and ambience banks the
Batmobile's 361 events also name.

The banks DO exist as BmAK assets (27 exports read out of the BmAK packages by `AUDIO_BANKS.md`),
so the claim is only true when "the install" means JC3. The real loss is not a failed search: it is
that BmAK's FEV graph cannot be authored into JC3's bank format (`JC3_AUDIO.md` section 10, route b
= **no**).

## 3. Closest JC3 carriers (candidates only, all `derived`)

40 candidates for 10 of the 27 absent banks, each from a named token rule on the decoded JC3 sample
names (`AUDIO_BANKS`-independent, `JC3_AUDIO_EVENTS.json`), preferring the `jc3_veh*` family:
engine/chassis -> `jc3_veh_land_chassis_rattle_nycab_fast`, `jc3_vehicle_engine_smoking_hiss_os_03`;
burnout -> `jc3_veh_land_premium_nitro_start/_loop/_stop`; tyres -> the `jc3_veh_*skid*` family;
weapons -> `jc3_wpn_*minigun/cannon*`; impacts -> the `jc3_veh_*impact*` family. The remaining 17
banks (all `DLG_*`, `SEQ_*`, `OBJ_*`, `VFX_*`, `WEA_*`, `BML_Battlemode`, `CHR_*`) keep **no**
candidate: `JC3_AUDIO_EVENTS.json` decodes name tables only for the banks it read, so a name miss
there is a coverage limit, not a claim that JC3 has no such sound. No candidate was auditioned.

## 4. Files written

- `Tools/scripts/t_au3b_banks.py` - new, `--write` / `--check`.
- `Working/Translation/T_AU3B.json` - the search record (per-bank methods, counts, hashes, candidates).
- `Working/Translation/T_AU3B.md` - 206 lines, generated.
- This report. Nothing under `Builds/`, no game file, no install, no launch.

## 5. Commands and output (verbatim)

```
$ uv run python Tools/scripts/t_au3b_banks.py --write; echo "write exit=$?"
wrote Working/Translation/T_AU3B.json and Working/Translation/T_AU3B.md (206 lines)
banks 27, ABSENT 27, FOUND 0, index rows 81952, fsb names 649
write exit=0
=== CHECK ===
$ uv run python Tools/scripts/t_au3b_banks.py --check; echo "check exit=$?"
PASS Working/Translation/T_AU3B.md re-derives byte for byte from the sources
PASS Working/Translation/T_AU3B.json re-derives byte for byte from the sources
PASS 27 distinct BmAK banks examined
PASS no JC3 index path carries any BmAK bank name (N1)
PASS no JC3 FSB5 sample table carries a BmAK bank name (N2)
PASS no dropzone file carries a BmAK bank name (N3)
PASS no index entry hashes to a BmAK bank name (H1)
PASS every bank is ABSENT in JC3 (27/27)
PASS every absent bank lists candidates or a recorded reason for none (17 of 27 have none)
PASS every candidate is labelled derived
PASS search coverage: 81952 index rows, 649 FSB5 names
PASS: T-AU3b 0 failure(s), 27 banks, 27 ABSENT, 40 derived candidates
check exit=0
```

## 6. UNKNOWNs

- **Whether any candidate sounds like the BmAK asset.** All candidates are name-level matches; only
  an audition (a Q step, currently banned) could rank them.
- **Whether JC3 carries these sounds under a third name or hash space.** H1 tests Jenkins of the
  bank name and of the FSB path JC3 would use; an unrelated hashing scheme would not be found, and
  no other scheme is documented in this project.
- **Sample-name coverage of JC3's non-vehicle banks.** `JC3_AUDIO_EVENTS.json` decodes 649 names
  (vehicles/weapons only), so N2 cannot speak for `character.bank`, `effects.bank` etc. The N2 miss
  is therefore a coverage limit, not proof.
- **Whether a BmAK event id could live in a JC3 bank.** `AUDIO_BANKS2.md` searched one id
  (`0x6BB2C66E`) across 117 exports with no hit; a full id sweep is a different card.

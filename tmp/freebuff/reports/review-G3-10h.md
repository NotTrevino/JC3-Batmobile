# review-G3-10h — the 494 constraint records, re-counted from the bytes

VERDICT: **minor issues**

Scope re-read here: `E:/Modding/_gamedata/JC3grab/**/*.physicsc` — **51 paths on disk, 48 distinct contents, 50 parsed**. The report under review (`tmp/freebuff/reports/G3-10h.md`) counts **494** records over **50** files. Re-counting every path independently gives **494** records over those 50 paths and **461** over the 48 distinct contents.

| claim in G3-10h | re-counted | verdict |
|---|---|---|
| 494 constraint records | 494 over paths, 461 over distinct files | **differs** |
| `bodyB` (+0x0c) = `0x7fffffff` in 494/494 | 494/494 | **holds** |
| `bodyA` (+0x08) always a real body index | 494/494 in range; 0 at the sentinel | **holds** |
| each record names exactly one body | 0 bodyA == bodyB; 0 bodyB in range | **holds** |
| 50 files = the whole population | 51 paths scanned, 50 parsed, 1 failed | **subset** |
| the field called `bodyB` is G3-10c's field | `+0x0C`, the same sentinel column | **holds** |

### What is not clean

- the 494 is a **per-path** count: 494 records over 50 parsed paths, but only **461** over the 48 distinct file contents - the difference is 33 records re-read from identical copies
- 1 path(s) carry no `hknpPhysicsSystemData` object at all (town_01_ai_junction.physicsc), so they cannot contribute a constraint record and their exclusion costs nothing

## C1 — the record count, and whether 494 is the population

Every `.physicsc` under `E:/Modding/_gamedata/JC3grab` was parsed; nothing was filtered by result. Records are read from the `hknpPhysicsSystemData` object's array at `+0x50` (`ptr`, `size`, `capacity`), at a **24-byte** stride, taking `+0x08` and `+0x0c` of each record.

- paths on disk: **51**; parsed: **50**; no `hknpPhysicsSystemData` at all: **1**; parse errors: **0**; parsed but zero records: **0**.
  - `town_01_ai_junction.physicsc`: no hknpPhysicsSystemData object - it holds no `hknpPhysicsSystemData` object and **no class whose name contains `Constraint`**, so it cannot contribute a cinfo record; its absence from the 494 costs nothing.
- records over all paths: **494**. Records over distinct file contents: **461**.
- **the same content appears under several paths**, so a per-path sum can double count:

| sha256 | paths | records |
|---|---|---:|
| `1b90daefdc9660b4` | E:/Modding/_gamedata/JC3grab\b13b\unpacked\models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\sportsmuscle.physicsc<br>E:/Modding/_gamedata/JC3grab\hkx\write\roundtrip_donor.physicsc | 11 |
| `62163ea4496feb57` | E:/Modding/_gamedata/JC3grab\hkx\sportsmuscle.physicsc<br>E:/Modding/_gamedata/JC3grab\probe\sportsmuscle.physicsc | 11 |
| `eda17906c1f81c7b` | E:/Modding/_gamedata/JC3grab\rc_merge\stage\models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\batmobile\sportsmuscle.physicsc<br>E:/Modding/_gamedata/JC3grab\rc_merge\verify\models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\batmobile\sportsmuscle.physicsc | 11 |

Per file:

| file | n_bodies | cinfos | ConstraintData objects | error |
|---|---:|---:|---:|---|
| `sportsmuscle.physicsc` | 62 | 11 | 11 |  |
| `apc.physicsc` | 83 | 16 | 16 |  |
| `armoredjeep.physicsc` | 106 | 19 | 19 |  |
| `armoredtransport.physicsc` | 113 | 16 | 16 |  |
| `articulatedtruck.physicsc` | 64 | 6 | 6 |  |
| `atv.physicsc` | 78 | 6 | 6 |  |
| `bavariumtank.physicsc` | 57 | 3 | 3 |  |
| `buggy.physicsc` | 101 | 12 | 12 |  |
| `cargotransport.physicsc` | 156 | 57 | 57 |  |
| `combatdirt.physicsc` | 40 | 1 | 1 |  |
| `fighterjet.physicsc` | 63 | 16 | 16 |  |
| `heavypatrol.physicsc` | 88 | 7 | 7 |  |
| `heavytroop.physicsc` | 86 | 8 | 8 |  |
| `lightpatrol.physicsc` | 37 | 4 | 4 |  |
| `mediumoldfishing.physicsc` | 115 | 38 | 38 |  |
| `modernbus.physicsc` | 118 | 31 | 31 |  |
| `modernmini.physicsc` | 82 | 6 | 6 |  |
| `modernmoped.physicsc` | 37 | 1 | 1 |  |
| `modernroad.physicsc` | 34 | 1 | 1 |  |
| `modernroadster.physicsc` | 67 | 8 | 8 |  |
| `modernsaloon.physicsc` | 74 | 10 | 10 |  |
| `modernsport.physicsc` | 33 | 1 | 1 |  |
| `modernsportssaloon.physicsc` | 77 | 8 | 8 |  |
| `modernsuper.physicsc` | 30 | 1 | 1 |  |
| `modernsuv.physicsc` | 77 | 4 | 4 |  |
| `monstertruck.physicsc` | 104 | 8 | 8 |  |
| `motoryacht.physicsc` | 85 | 4 | 4 |  |
| `oldbus.physicsc` | 130 | 8 | 8 |  |
| `oldjeep.physicsc` | 106 | 17 | 17 |  |
| `oldmini.physicsc` | 54 | 8 | 8 |  |
| `oldmoped.physicsc` | 31 | 1 | 1 |  |
| `oldroad.physicsc` | 45 | 1 | 1 |  |
| `oldtractor.physicsc` | 54 | 4 | 4 |  |
| `racingboat.physicsc` | 45 | 2 | 2 |  |
| `racinghothatch.physicsc` | 85 | 7 | 7 |  |
| `racingsupercar.physicsc` | 66 | 9 | 9 |  |
| `smalloldfishing.physicsc` | 53 | 1 | 1 |  |
| `technicaljeep.physicsc` | 90 | 13 | 13 |  |
| `town_01_ai_junction.physicsc` | - | - | - | no hknpPhysicsSystemData object |
| `transport.physicsc` | 53 | 12 | 12 |  |
| `trials.physicsc` | 29 | 1 | 1 |  |
| `vintagesports.physicsc` | 90 | 8 | 8 |  |
| `sportsmuscle.physicsc` | 62 | 11 | 11 |  |
| `replace_hull.physicsc` | 62 | 11 | 11 |  |
| `roundtrip_assembled.physicsc` | 62 | 11 | 11 |  |
| `roundtrip_donor.physicsc` | 62 | 11 | 11 |  |
| `scale_wheel.physicsc` | 62 | 11 | 11 |  |
| `shift16.physicsc` | 62 | 11 | 11 |  |
| `sportsmuscle.physicsc` | 62 | 11 | 11 |  |
| `sportsmuscle.physicsc` | 62 | 11 | 11 |  |
| `sportsmuscle.physicsc` | 62 | 11 | 11 |  |

The cinfo count equals the number of `*ConstraintData` objects in **50 of 50** files with records, so the array is the constraint list itself and not a filtered view of it.

## C2 — the sentinel in the second field

- `+0x0c` values seen across all records: [2147483647].
- `+0x0c` == `0x7fffffff`: **494 of 494**; in range of the body count: **0**.
- `bodyA` (+0x08): distinct **97**, min **0**, max **104**; in range **494/494**; at the sentinel **0**.
- `flags` (+0x10): [0]; tail dword (+0x14) zero in 494/494; the reference's high half (+0x04) is zero in 494/494.

So the report's numbers re-derive exactly — with the caveat in the verdict: the count is a **per-path** count of the same bytes, not a count of distinct assets.

## C3 — bodyA against the body count

No record has a `bodyA` outside its file's body count, and every file's `bodyA` values are inside `0..n_bodies-1`. Maximum `bodyA` is **104**; the file with that record has at least that many bodies (see the per-file table).

Records with `bodyA == bodyB`: **0** (impossible here, since `bodyB` is always the sentinel and `bodyA` never is — both facts measured, not assumed).

## C5 — is `bodyB` the field G3-10c names?

`PHYSICS_ROLES3.md` (G3-10c) dumps the same 24-byte record as six words and puts the `0x7FFFFFFF` in the fourth word, i.e. **+0x0C**, with a column headed "+0x0C" and a "second body?" verdict of "none"; its probe stored that word as `field_0c`.

  > | # | record | words +0x00..+0x14 | constraint class | body id | +0x0C | second body? |
  > fleet file; +0x0C is the same sentinel the body table uses for bodies without a part id.
  > | +0x0C | body id | equals the entry index for the 38 part bodies (0..41 minus 22/23/36/37); 0x7FFFFFFF for the other 24 |
  > | id | +0x0C | +0x10 | +0x4C |
  > 3. body-entry words other than +0x0C, +0x10, +0x3C, +0x4C keep their G3-10b domains

The report's `bodyB` is that same `+0x0c` dword, and its `bodyA` at `+0x08` is where G3-10c reads the one body id. **The offsets agree.** One readability trap, not a contradiction: G3-10c's section 2 uses `+0x0C` again as the **body-entry** body id (`{id, (id<<16)|flag}` table, 0x90-byte entries) — a different structure, the same offset number.

## What I could not check

- **The semantic claim** that `0x7fffffff` means "no body" rests on the disassembly in G3-10h (four `cmp ... 0x7fffffff` sites and the detach block). I did not re-disassemble `JustCause3.exe`; this review re-counts the data, not the code. The data is consistent with the reading — the field is never a body index — but consistency is not the code proof.
- **Whether the runtime substitutes body 0.** Not decodable from these files; the report already marks it UNKNOWN.
- **G3-10g's 494 agreement.** The card claims `prior_card_agreement: 494`; I did not re-derive G3-10g's partner scores, so that cross-check is taken on trust (it does not affect any claim reviewed here).
- **The donor-vs-fleet split.** G3-10c read 11 records from one donor file; that file is one of the duplicates here, so its records are inside the 494 either way.

## Commands run

```
$ uv run python - <<'PY'   # print CONSTRAINT_CODE.json census/offsets/rows[0]; glob every .physicsc
census: {"bodyA_distinct": 97, "bodyA_is_sentinel": 0, "bodyA_max": 104, "bodyA_min": 0, "bodyA_valid_body": 494, "bodyB_distinct": 1, "bodyB_is_sentinel": 494, "bodyB_valid_body": 0, "flags_values": [0], "records": 494, "ref_high_zero": 494, ...}
offsets: {"bodyA": 8, "bodyB": 12, "flags": 16, "object_size": 24, ...}
rows[0]: {"bodyA": 1, "bodyB": 2147483647, "class": "hkpLimitedHingeConstraintData", "file": "sportsmuscle.physicsc", "k": 0, "n_bodies": 62, ...}
disk glob: 51
[... five paths end in sportsmuscle.physicsc: the donor tree, hkx/all, hkx/out, hkx/write, and one more]
```

```
$ uv run python Tools/scripts/review_g310h.py --write
paths 51 | distinct 48 | parsed 50 | failed 1 | zero-cinfo 0
records over paths 494 | over distinct contents 461
bodyB==0x7fffffff 494/494 | bodyA in range 494/494 | bodyA==bodyB 0 | out of range 0
verdict: minor issues
```

## Files written by this review

- `Tools/scripts/review_g310h.py` — `--write` / `--check`; reads only `jc3hkx.py` and the `.physicsc` files, plus `CONSTRAINT_CODE.json` and `PHYSICS_ROLES3.md` for comparison.
- `tmp/freebuff/reports/review-G3-10h.md` (this report) and `review-G3-10h.json`.
- Nothing else was written; `CONSTRAINT_CODE.md/.json` and every other card are untouched.

## Oracles (`--check` re-runs every count)

| oracle | ok |
|---|---|
| `every_physicsc_on_disk_scanned` | PASS |
| `record_count_matches_the_card` | PASS |
| `path_minus_distinct_equals_duplicate_copies` | PASS |
| `no_unexplained_parse_errors` | PASS |
| `no_record_out_of_range` | PASS |
| `no_record_with_equal_bodies` | PASS |
| `cinfo_count_equals_constraint_data_objects` | PASS |
| `g10c_names_the_same_offset` | PASS |

8/8 pass.

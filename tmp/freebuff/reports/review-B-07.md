# Independent review — B-07 · Lights module rewrite

Reviewer: Buffy (not the author). Date 2026-10-31. Read-only: no file edited except this report; no
game launched; no git.

Card: `GRAB_BACKLOG.md` §8 `#### B-07 · Lights module rewrite (old LGT-1 build half)   S · deps: B-05 ·
serves: LGT-1/2`
Done line: *"every entry names a part that exists with `has_lights` = 1."*

## VERDICT: **minor issues**

The Done line passes on the packed artefact, every documented Out path exists, the check is stronger
than the card (it re-encodes the module, compares it with the `.ee`'s copy and the `.toc` record, and
verifies `part_index` ↔ `part` ↔ `has_lights` on the packed bytes), and the numbers I re-derived all
match. The issues below are reporting/provenance gaps and one disclosure omission (the `.ee`/`.toc`
pair is not a complete directory, inherited from the live build). No rework of the module is required.

## Check output (verbatim)

```
$ python Tools/scripts/bm_lightrig.py --check
rows   18 (base 21, dropped 10, added 7)  behaviours {'HeadLight': 15, 'TailLight': 3}
parts  7 distinct, every one in the built parts module with has_lights = 1: ['sportsmuscle_body', 'sportsmuscle_headlight_f_l', 'sportsmuscle_headlight_f_r', 'sportsmuscle_tailstrip_r_l', 'sportsmuscle_tailstrip_r_r', 'sportsmuscle_wheel_f_l_arch', 'sportsmuscle_wheel_f_r_arch']
module 5745 B D4E6610B0EA33A77<0xEF 0xBF 0xBD>, .toc record 16499616/5745, .ee 11180088 B
R7     shared/other files changed besides the lights module: 0
PASS: every entry names a part that exists with has_lights = 1, no donor lamp part, the built module is the re-derived plan
CHECK_EXIT=0
```

(The sha is truncated by the tool and the console prints its last bytes as U+FFFD; the full digest is
`D4E6610B0EA33A77C0B7A6FA6740779EAB4A3E2901AE98A06E6627BFF478A34E`. The run is read-only with
respect to `Builds/bm-007`; its scratch dir is `tmp/b07/`.)

## Issues

### 1. The provenance tally is a hand sum, not a generated count (R11)

`MODLOG.md:18475` — *"Provenance over the 18 × 25 = **450 member cells**: `decoded` 360,
`decoded (mapped)` 6, `derived` 68, `derived (verified)` 16 — **0 `assumed`, 0 UNKNOWN-valued
cells**."*

`Working/Lights/bm_lightrig.json` stores one `class` per member (I re-summed: **450 cells, 360 / 6 /
68 / 16, 0 assumed** — correct), but the file has **no `counts` block** for them and
`Tools/scripts/bm_lightrig.py --check` never aggregates them (no `Counter`, no "member" tally in
`check()`). The tool cannot re-derive the number the doc quotes, which is what R11 asks for. Fix:
add a `counts.members` block in `--write` and print/assert it in `--check`.

### 2. Receipt's `budgets` is null and its note carries typed numbers (R9)

`Builds/bm-007/receipt.json`:

```
"budgets": {"model_kb": null, "texture_kb": null,
            "note": "… R9's Model/Texture budgets are unchanged from B-03's 4,899.6 / 7,065 KB figures."}
```

R9 says "Every build reports both". The build indeed adds no mesh/texture bytes, but the report is
two nulls plus a prose figure copied from B-03; `bm-002`, `bm-007` and `bm-009` receipts differ in
shape here (`bm-002`/`bm-009` carry numbers). Fix: carry the inherited numbers as fields (with a
"source: bm-003" note) or make the check assert they equal the dependency's receipt.

### 3. The `.ee`/`.toc` pair is not a complete directory — inherited, but undisclosed

`MODLOG.md:18456` quotes `.toc 60,917 B / 605 records` and the record for this module, which is
correct. But `python Tools/scripts/eetoc.py compare <ee> <ee.toc>` on the card's own artefact says:

```
DIFFERS  ee=703 toc=605  only_in_ee=98 only_in_toc=0  offset/size_mismatch=7
   editor/entities/jc_cameras/vehicle_cameras/car_base.ctunec: ee (16511464, 5968) toc (0, 5968)
   … 6 more
```

The same shape exists in `Builds/bm-009` (`703/605, 98, 7`) and the live `Builds/test-091`
(`604/506, 98, 8`), so B-07 **did not introduce** it — but the card ships a new `.ee`/`.toc` pair and
its limits list does not mention that 98 inner files have no record and 7 records are zero-offset.
V-01's "`.toc` records for every file … non-zero offset" gate will hit exactly this. Fix: record it
as an inherited limit (or fix it in the pack step).

### 4. Anchor chains are never tested for resolution, and 18/18 rows carry one

Every row's `deformable_transform` is T-18's `jc3_anchor` verbatim (verified against
`Working/Translation/t14_lights.json` for all 18). Five distinct chains are reused:

| chain | rows | nature |
|---|---:|---|
| `|sportsmuscle_LOD1|body|Winch_DOOR_Mesh|Winch_DOOR_Mesh_LIG` | 10 | donor mesh bone name |
| `|sportsmuscle_LOD1|body|Batmobile_Chassis|Batmobile_Chassis_LIG` | 2 | BmAK bone |
| `|sportsmuscle_LOD1|body|SUSP2_Wheel_Rear_{Left,Right}|…` | 2 | donor suspension bone |
| `|sportsmuscle_LOD1|wheel_f_{l,r}|Wheel_Frnt_{Left,Right}_Disc|…` | 3 | BmAK wheel bone |
| `|sportsmuscle_LOD1|body|Batmobile_Rig_Weapons_Drone_Decoder|…` | 1 | BmAK rig bone |

`--check` verifies the part, the part index, the `has_lights` flag and the hashes, but never that the
anchor chain resolves in the built body. `MODLOG.md:18493` (limit 1) calls this UNKNOWN for "the
chain", and that is honest, but the issue covers **all 18 rows** (10 of them on a donor mesh name),
not an edge case. This is the LGT-1 §112 / Q-1 #7 probe; the review records it so the probe's scope
is known.

### 5. `Builds/bm-007/verify/` is an undocumented output; the receipt has no Done record

`ls Builds/bm-007` shows `verify/` (an unpacked copy) in addition to the four documented artefacts.
`check()` reads it (`bm_lightrig.py:782`) and compares it with the packed module, so it is load-bearing
for the gate — if it goes stale the check fails — but the card's file list does not name it.
Separately, `receipt.json` has `"checks": []`; the Done evidence lives only in `MODLOG` prose.

### 6. "Brake is carried by the kept rows" rests on T-18, not on the module

The base module's 21 rows are 10 `HeadLight`, 5 `TailLight`, 2 `LeftSignal`, 2 `RightSignal`,
2 `Reverse` — there is **no** brake/signal behaviour name in the module. The only row whose
`preset_id` is the `Rear_Brake` preset (`3358775008`, base row 3) was dropped, and the three kept
`TailLight` rows (built rows 1, 8, 17) carry presets `4016595472` and T-L35's custom values.
`MODLOG.md:18464` says "the brake/tail behaviour is carried by the two kept rows": that is **T-18's
mapping** (T-L15/T-L16), not something the module proves. Whether `TailLight` fires on braking is
UNKNOWN (same class of unknown as `preset_id` semantics, already listed in limit 2). The card's Done
does not require it, so this is a provenance note, not a Done failure.

## Spot-checks (value, where verified)

| # | value in the doc | where checked | result |
|---|---|---|---|
| 1 | 18 rows, `15 HeadLight + 3 TailLight` | decode the built module (`Builds/bm-007/aaf/.../…_lights.vmodc`) with the card's decoder | **18 rows; HeadLight 15, TailLight 3** |
| 2 | parts: body 0, arch 42/43, head 44/45, tailstrip 48/49, all `has_lights = 1` | `decode_parts` of the 59-part module in the same aaf | **exact** — 44 `sportsmuscle_headlight_f_l` 1, 45 `…_f_r` 1, 48 `…_tailstrip_r_l` 1, 49 `…_r_r` 1, 42/43 arches 1, body 1 |
| 3 | module `5,745 B`, sha `D4E6610B…A34E`, `.toc` record `16499616 / 5745` | `sha256sum` of the loose module; raw `.toc` parse | **5,745 B, `d4e6610b…34e`, record `(16499616, 5745)`, 605 records** |
| 4 | 450 member cells: 360 `decoded` / 6 `decoded (mapped)` / 68 `derived` / 16 `derived (verified)`, 0 assumed | sum of `rows[].members[].class` in `bm_lightrig.json` | **450; 360 / 6 / 68 / 16; 0 assumed** |
| 5 | base 21 rows, 10 dropped, 7 added | decode `Builds/bm-005/.../…_lights.vmodc` | **21 rows** (10 HeadLight, 5 TailLight, 2 LeftSignal, 2 RightSignal, 2 Reverse); 21 − 10 + 7 = 18 |
| 6 | "one file changed" vs `bm-005` | `python Tools/scripts/aafdiff.py Builds/bm-005/aaf Builds/bm-007/aaf --hash` | **1 changed `.vmodc`, 6,337 → 5,745 B (−592)**, 0 only-in |
| 7 | `.ee` 11,180,088 B / `.toc` 60,917 B | `sha256sum` + `ls` | **match**; shas `b953e20c…` / `46eb90b6…` as in the receipt |

## Audit questions

| question | answer |
|---|---|
| Every Out path exists? | **Yes** — `Tools/scripts/bm_lightrig.py`, `Working/Lights/bm_lightrig.json`, `Builds/bm-007/{aaf,.ee,.ee.toc,receipt.json,install.ps1}`, `tmp/freebuff/reports/B-07.md`; plus the undocumented `verify/` (Issue 5) |
| Done criterion matches `--check`? | **Yes, and stronger** — the check validates the packed module's `part_index`/`part`/`has_lights`, the re-encoded bytes and the `.toc` record |
| Numbers script-derived (R11)? | **Mostly** — module size/sha/records, rows, behaviours, parts and `has_lights` are computed; the 450-cell provenance tally is a hand sum (Issue 1) |
| Values lacking provenance / guess as fact (R4)? | Anchor resolution is labelled UNKNOWN; `preset_id` semantics and the brake mapping are UNKNOWN-adjacent (Issue 6). No invented value found in the 18 rows — every member carries a class and a `src` |
| Member name confused with behaviour (R5)? | **No** in the delivered rows: behaviour comes from the shipped row's own `behavior` member, the part from B-03/B-04 measurement, and the check verifies `behavior_hash = hash_jenkins(behavior)`. The brake claim is T-18's mapping, flagged in Issue 6 |
| Claims the data cannot support? | Issue 3 (605 records described without the 98/7 gap) and Issue 6 |

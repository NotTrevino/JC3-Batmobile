STATUS: done - the RC1 build carries **9 UNAPPROVED lore compromises** (ranked by visibility in play), **2 APPROVED** ones with a quoted operator decision, and **1 repair** that is not a compromise. Every number is re-derived from the source bytes by `Tools/scripts/audit_compromises_b.py --check` (exit 0). Nothing under `Builds/` was written.

# AUDIT-B - lore-accuracy compromise audit of the BUILD

## 1. What was audited

`Builds/bm-RC1/receipt.json` (205,174 B, sha256 `4bfe337ccab65c3e...`) and
`Working/RC/bm_rc_manifest.json` (10,947 B, sha256 `dfbac0c773042150...`), read against
`MODLOG.md` (sections B-01..B-16, "Q re-test", "RC merge fix", "shelved"), `GRAB_BACKLOG.md`
section 12 rows B-01..B-16 and V-01/V-03/V-06, `Tools/scripts/bm_budget.py`,
`Tools/scripts/bm_rc.py`, `Research/BatmobileGrab/CONTROLS_MENU_SCREENS.md`,
`Research/BatmobileGrab/COLLISION_GEOM.json`, `LIGHTS.md`, `Working/Lights/bm_lightrig.json`,
`Working/Damage/bm_health.json`, `Working/Parts/bm_vehicle_parts.json`.

Approval rule applied: APPROVED only where a source line contains the operator's own words, with
file + line printed. `done`, `skipped`, card tags, fleet conventions and research conclusions were
never treated as approval.

## 2. UNAPPROVED, ranked by visibility in play

| # | id | card | compromise | BmAK | build ships | loss | scripts |
|---:|---|---|---|---|---|---|---|
| 1 | C-01 | B-10/B-10c | collision hull from the render bbox, not the chassis box | chassis box 690.305 x 374.536 x 207.5 cm | hull target 3.495 x 2.271 x 7.025 m, written 3.499 x 2.283 x 7.037 m | 0.250 m narrow, +0.196 m tall, +0.122 m long - walls 25 cm inside the flanks, 20 cm of empty collision above the roof | `bm_collision.py`, `bm_colhull.py`, `bm_colmesh.py` |
| 2 | C-02 | B-18/B-15 | 8 mesh files are vanilla Serpente bytes | all 5 body LODs are Batmobile_V2 (APP-1) | body lod3+lod4 and 6 wheel LODs reverted to vanilla | the donor shell fades in at mid/far range | `bm_paths.py` |
| 3 | C-03 | B-15/B-17 | approved unbind not done; B-17 hide SKIPPED | no Serpente part at all | 12 panels bound (2,104.5 KB), `B-17: SKIPPED (BM_NO_B17=1)` | donor panels/cabin can draw through the shell | `bm_budget.py`, `bm_hide.py` |
| 4 | C-04 | B-07 | lamp rig 21 shipped rows -> 18 entries | 101 BmAK entries / 129 components incl. high beams | 11 rewritten, 1 new, 6 custom, 10 dropped incl. `Front_Primary_Head` | no primary/high-beam lamp; indicators + reverse lost (not lore losses) | `bm_lightrig.py` |
| 5 | C-05 | B-11 | audio route a+c on JC3's banks | BML_Engine / VEH_Batmobile_MK2_Engine banks, RPM RTPC | private copies of the JC3 banks (210,781,376 B / 177,586,080 B), 5 swapped payloads | engine/tyres/weapons stay JC3 samples; no interior layer, no per-weapon BmAK events | `bm_audio.py` |
| 6 | C-06 | B-04 | 9 behaviour parts have no collision body | turret yaw, cannon pitch, barrel spin, fan, air-brake fins | turret, cannon, suppressor, MG, 4 flaps, jet at ids -1 | may be static decoration; untested | `bm_parts.py` |
| 7 | C-07 | B-09 | health/damage are declared switches | `RVehicleBatmobile.Health` 1,200; 24 cannon hits | 2000 -> 36,000, deform 0, impact 0, wheel skew 200 -> 400 | the pool is 24 x 1,500, outside the shipped domain, 18,000 alternative recorded | `bm_health.py` |
| 8 | C-08 | T-13R/B-05 | entry/exit geometry is the donor's | Batmobile sockets and sides (WLD-3/4) | 15 of 84 transforms = donor 3x3 x box map; 69 rows skipped | points are donor-derived, most transforms never built | `bm_entity.py`, `bm_rc.py` |
| 9 | C-09 | B-13c | spawn record clones the donor's drop-box vectors | the car's own footprint | donor vec fields kept | drop box sized for a 3.72 m Serpente, not a 7.03 m Batmobile | `bm_rebel.py` |

Count by script (13 involvements over 9 items, every script present in `Tools/scripts/`):
`bm_audio.py` 1, `bm_budget.py` 1, `bm_colhull.py` 1, `bm_collision.py` 1, `bm_colmesh.py` 1,
`bm_entity.py` 1, `bm_health.py` 1, `bm_hide.py` 1, `bm_lightrig.py` 1, `bm_parts.py` 1,
`bm_paths.py` 1, `bm_rc.py` 1, `bm_rebel.py` 1.

## 3. APPROVED (quoted operator decision)

- **A-01 B-15 model budget cuts** - 5,972.9 -> 4,791.3 KB of the 4,915.0 KB cap, 16 `.lod`
  trimmed: `MODLOG.md:19109` quotes the user - `User choice: "unbind panels + trim LODs"`.
- **A-02 D-2 one hybrid car** (B-12 `skipped: D-2`) - `GRAB_BACKLOG.md:1506` quotes
  `**resolved 2026-10-28 (user): (b) one hybrid car**`; 13 of 15 T-15 rows that differ between
  pursuit and battle ship as one car.
- **Operator decisions 2026-11-05** (5 quotes found in `CONTROLS_MENU_SCREENS.md:46,47,48,50,52`):
  BmAK controls replace all JC3 controls except pause/commlink; enter Y / exit LB; eject A A;
  winch on d-pad right replacing Mission Select; AR Challenges and Mission Select dropped. None is
  a step that ships in `bm-RC1` yet (the controls/winch work is unbuilt), so there was nothing to
  audit against them.
- **Paint colour - approved in the brief, not in the file.** The brief records "the BmAK colour is
  used exactly, lighting differences accepted" and names `CONTROLS_MENU_SCREENS.md` as the record.
  That file contains **0** occurrences of "colou?r". The build ships `PAINT_ALBEDO_GAIN = 4.0`
  (`MODLOG.md:5488`, chosen from a test-080 luma measurement) plus hand-written sRGB constants, and
  the hull reads pale violet-white in noon sun (`MODLOG.md:19882`); G3-20d relabels the effective
  paint colour "assumed" and G3-11c records the combine operator as UNKNOWN. Status is APPROVED per
  the operator's instruction for this audit, with the file-level citation missing - the one item
  that cannot be granted from disk.

## 4. Checked and NOT a compromise

**B-16: 12 APC mounted-M2 body members removed, 4 `F30CCB1C` owner links nulled.** The removed
members name files that ship only inside the APC's `.ee` (`w206_mounted_capstone_m2hm`), and the
link pointed at the APC's own CCar root. The medium tank (whose `w602`/`w603` names these clones
carry) and the preorder Serpente have the link null and none of the three members. Removing them
restores the donor convention and loses no BmAK content: a repair, not a lore compromise.

The **"shelved"** section the brief named has exactly one entry in `MODLOG.md` (line 4283): a
test-061 max-rpm diagnostic moved aside, with nothing lore-relevant in the build.

## 5. Files written

- `Tools/scripts/audit_compromises_b.py` - new, `--write` / `--check`.
- `Working/RC/COMPROMISES_B.md` - 294 lines, generated.
- This report. No `Builds/bm-*` tree, no `E:/Games` path, no install script and no game file was
  touched (`git status` shows no `Builds/` change).

## 6. Commands and output (verbatim)

```
$ uv run python Tools/scripts/audit_compromises_b.py --write; echo "write exit=$?"
wrote Working/RC/COMPROMISES_B.md (294 lines)
items 9, UNAPPROVED 9, APPROVED 2
by script: bm_audio.py 1, bm_budget.py 1, bm_colhull.py 1, bm_collision.py 1, bm_colmesh.py 1, bm_entity.py 1, bm_health.py 1, bm_hide.py 1, bm_lightrig.py 1, bm_parts.py 1, bm_paths.py 1, bm_rc.py 1, bm_rebel.py 1
write exit=0
=== CHECK ===
$ uv run python Tools/scripts/audit_compromises_b.py --check; echo "check exit=$?"
PASS: Working/RC/COMPROMISES_B.md re-derives byte for byte from the sources
PASS 9 UNAPPROVED items (found 9)
PASS 2 APPROVED items with a quoted decision (found 2)
PASS every script named in the table exists (13 involvements)
PASS every APPROVED item prints a quote found in its file at its line
PASS no UNAPPROVED item carries a quote that approves what it ships
PASS B-15: 5972.9 -> 4791.3 KB, 16 .lod (manifest 16, cap 4915.0)
PASS B-18 reverted 8 .rbm of 10 files to vanilla bytes
PASS B-07: 21 shipped rows -> 18 entries, 10 dropped
PASS B-10 hull vs chassis box delta [-0.25, 0.196, 0.122] m (render bbox target)
PASS: AUDIT-B 0 failure(s), 9 items, 9 UNAPPROVED, 2 APPROVED
check exit=0
```

## 7. UNKNOWNs

- **Chassis-box frame/rotation.** `COLLISION_GEOM.json` records the box transform as not decoded;
  if it carries a rotation, C-01's deltas change. Would be settled by the `FKBoxElem` layout.
- **Whether B-10d's corrected chassis-box hull was meant to ship.** `Working/Collision2/` holds a
  10/10-oracle build; no receipt, card row or operator sentence adopts or rejects it.
- **Whether the 9 body-less behaviour parts move.** Fleet convention says they must carry a body;
  probe 7 only proved they load without one. Needs a Q test.
- **The Batmobile's own drop-box vectors.** No decoded BmAK footprint reaches `bm_rebel.py`.
- **Where the brief's colour decision is recorded.** Not in `CONTROLS_MENU_SCREENS.md` (0 hits) and
  no file searched contains "colour is used exactly" or "lighting differences".
- **Why `Tools/scripts/factors.py` does not contain `PAINT_ALBEDO_GAIN`** although
  `MODLOG.md:20720` cites `factors.py:178` - the constant's current home is UNKNOWN; the audit
  cites the log line, not the script.

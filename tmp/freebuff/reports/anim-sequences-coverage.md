# anim-sequences-coverage - T-8's moving parts against ANIMATIONS.md and BONES.md

## STATUS

**done - 15 T-8 rows cite 15 distinct clip names (60 sequence exports of 253); 12 rows are fully
covered (sequence found with package/export, joint bone in that sequence's `moved_bones` with a
non-zero range, bone in `BONES.json`'s 180). 3 rows have no sequence (P-02 cannon, P-05 jet,
P-13 steering wheel), and 193 sequences are cited by no T-8 row. No row cites a sequence missing
from ANIMATIONS.md, and every non-static row's joint bone is in BONES.json. `--check` PASS
(6/6).**

Files written:

- `Working/Translation/PARTS_ANIM_COVERAGE.md` (19,167 chars - the row table, the two gap lists)
- `Working/Translation/PARTS_ANIM_COVERAGE.json` (same rows as data, plus the flat 193-sequence list)
- `Tools/scripts/parts_anim_coverage.py` (`--write` / `--check`; read-only everywhere else)
- `tmp/freebuff/reports/anim-sequences-coverage.md` (this card)

Untouched: `Research/BatmobileGrab/ANIMATIONS.*`, `BONES.*`, `Working/Translation/T8_PARTS.*`.
No game launched or attached (INSTRUCTIONS §3).

---

## 1. Coverage per row (decoded)

| row | part | joint bone | sequence (package/export) | joint range in ANIMATIONS | bone in BONES |
|---|---|---|---|---|---|
| P-01 | `batmobile_turret` | `Batmobile_Rig_Weapons_Turret_Root` | `Batmobile_V2_Turret_Spin` (`Playable_Batmobile_SF`/223) | 60.001° | #100 |
| P-02 | `batmobile_cannon` | — | **none** | — | — |
| P-03 | `batmobile_machine_gun` | `..._Machine_Gun_02` | `Batmobile_V2_ChainGun_Spin` (`Playable_Batmobile_SF`/218) | 179.496° (one ±180° wrap of a 2160° spin) | #152 |
| P-04 | `batmobile_riot_suppressor` | `..._Riot_Sup_Ammo` | `Batmobile_V2_Cannon_Fire` (/216), `Batmobile_V2_Riot_Suppressor` (/217) | 89.999° | #149 |
| P-05 | `batmobile_jet` | — | **none** | — | — |
| P-06 | — (canopy) | `CockPit_Mesh` | `Batmobile_V2_Cockpit_Close` (/211), `_Open` (/212), `Cockpit_Close` (/207), `Cockpit_Open` (/209), `Cockpit_Open_Idle` (/208) | 12.493° / 72.481 cm | #62 |
| P-07 | — (left hatch) | `..._Missiles_L_T` | `Batmobile_V2_Missles_Down` (/239), `_Up` (/237) | 14.988° | #161 |
| P-08 | — (right hatch) | `..._Missiles_R_T` | same two clips | 14.988° | #154 |
| P-09 | `batmobile_aero_flap_l_f` | `..._Aero_Flap_L_F_Piston_Top` | `Batmobile_V2_Aero_Flap_L_Down` (/232), `_Up` (/233) | 25.763° | #169 |
| P-10 | `batmobile_aero_flap_r_f` | `..._Aero_Flap_R_F_Piston_Top` | `Batmobile_V2_Aero_Flap_R_Down` (/230), `_Up` (/231) | 25.763° | #171 |
| P-11 | `batmobile_aero_flap_l_b` | `..._Aero_Flap_L_B_Piston_Top_001` | `..._Aero_Flap_L_Down/Up` | 54.787° | #174 |
| P-12 | `batmobile_aero_flap_r_b` | `..._Aero_Flap_R_B_Piston_Top_001` | `..._Aero_Flap_R_Down/Up` | 54.799° | #179 |
| P-13 | — (steering wheel) | — | **none** | — | — |
| P-14 | `batmobile_missile_pod_l` | `..._Missiles_L_T` | `Batmobile_V2_Missles_Down/Up` | 14.988° | #161 |
| P-15 | `batmobile_missile_pod_r` | `..._Missiles_R_T` | same two clips | 14.988° | #154 |

All sequence exports are `AnimSequence` under set `Batmobile_V2_Pose_States` or
`BM_Batmobile_Chassis`; the cited clips also exist in the MK2/Funhouse/Joker packages (the
duplicate carriers are in the JSON, the table cites the Playable_Batmobile_SF copy).

## 2. Parts with a row but no sequence

| row | part | why (from T-8's own recorded reason) |
|---|---|---|
| P-02 | `batmobile_cannon` | no rotation animated; the bones translate (53.376 cm in `Batmobile_V2_Cannon_Fire`) and a hinge cannot reproduce translation |
| P-05 | `batmobile_jet` | no rotation animated; `JetSMove` translates 40.163 cm in `Batmobile_V2_Bat_Tracker`; the spin is `engine_rpm` (code) |
| P-13 | — (steering wheel) | no bone carries the part, so nothing can be animated |

These are the three static rows; P-14/P-15 are static shells that ride P-07/P-08's clips and are
therefore counted as sequenced.

## 3. Sequences with no T-8 row - 193 of 253

| mechanism | sequences | examples (package/export) |
|---|---:|---|
| `other` | 112 | `Batmobile_V2_Back_Door_Open` (SF/215), `Batmobile_V2_Boost_Noise` (/219), `Batmobile_V2_Tank_Idle` (/221), `Batmobile_V2_Idle` (/224) |
| `transformation` | 32 | `Drive_To_Combat` (SF/205), `Batmobile_V2_Tank_Spread_Open` (/222), `Batmobile_V2_Bat_Tracker` (/229) |
| `driver/Batman` | 29 | `BatMobile_Stand_Out` (Joker/411), `Vent_Takedown` (/416) |
| `wheels/strafe` | 16 | `BatMobile_Drift_In_01` (SF/206), `Batmobile_V2_Spin` (/210), `Batmobile_V2_Tank_Strafe` (/213) |
| `fins/air-brakes` | 4 | `Batmobile_V2_Jet_Boost` (SF/214, MK2/213, Funhouse/211, Joker/446) |

The complete named list (193 entries with package and export index) is in
`PARTS_ANIM_COVERAGE.json` under `unrowed`. The `other`/`driver` masses are HUD/character and
body-pose clips; the `fins/air-brakes` 4 are the same `Jet_Boost` clip in four packages, which
T-8's P-05 row declines because the jet's motion is translation plus code-driven spin.

## 4. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && python Tools/scripts/parts_anim_coverage.py --write; echo "write_exit=$?"; python Tools/scripts/parts_anim_coverage.py --check; echo "check_exit=$?"
wrote Working/Translation/PARTS_ANIM_COVERAGE.md (19167 chars) and Working/Translation/PARTS_ANIM_COVERAGE.json
rows 15 | cited 60 | unrowed 193 | covered 12 | no-sequence ['P-02', 'P-05', 'P-13']
write_exit=0
rows 15 | cited seqs 60/253 | unrowed 193 | covered 12 | no-sequence 3 (P-02, P-05, P-13) | bones 180
PASS: every cited sequence, joint bone and range is recorded; parts-without-sequence and sequences-without-row are both enumerated
CHECK_EXIT=0
check_exit=0
```

An earlier run counted 15 cited *names* against 253 *exports* and could not balance; the counts
now separate the two (15 names = 60 exports), so the six checks are: cited names all exist; every
cited sequence resolves to package + export index; every non-static joint bone is in BONES.json;
each sequenced row has a non-zero joint range (12/12); rows partition as 12 covered + 3 no-sequence;
exports partition as 60 + 193 = 253.

## 5. UNKNOWNs (with what was tried)

1. **Whether a static row is animatable at all.** P-02/P-05 translate, P-13 has no bone; no
   sequence is claimed for them by design (B-02 decision), recorded rather than resolved.
2. **Whether duplicate clip copies differ.** `ANIMATIONS.md` records 51 names repeated across
   packages; the table cites the first carrier and the JSON lists the others, without comparing
   their keyframes.
3. **The JC3-side rate.** T-8 already records that `all_hinged_part_properties` has no rate
   member; the ranges here are BmAK animation facts, not JC3 values.
4. **The 193 unrowed sequences' relevance.** No claim is made that they should have rows; the list
   is exhaustive so a reviewer can check the mechanisms that matter (`transformation`,
   `fins/air-brakes`) without re-reading 253 rows.

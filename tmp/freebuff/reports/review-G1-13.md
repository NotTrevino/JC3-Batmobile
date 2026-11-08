# Independent review — G1-13 · Sockets in JC3 space

Reviewer: independent read-only pass (did not write this card). Date 2026-10-29.
Card: `GRAB_BACKLOG.md:457` (`G1-13 · Sockets in JC3 space`, S, deps G1-11, serves WPN/LGT/FX/
ANI-9/WLD-3). Tracker row: `GRAB_BACKLOG.md:1281`. Journal: `MODLOG.md:8147` ("G1-13 · Sockets —
done").
Outputs reviewed: `Research/BatmobileGrab/SOCKETS_JC3.md` (181 lines, 16,314 B),
`SOCKETS_JC3.json` (69,890 B), `Tools/scripts/grab_sockets.py` (593 lines).

## VERDICT: minor issues

The card's plumbing is sound. Every `Out` path exists, `--check` is a real re-derivation + byte
comparison (it does not write), the Done paragraph is exactly what the checks assert, and every
number in the markdown is rendered from the JSON. I re-derived the 65 socket records from
`grab_model.sockets`, re-computed a sample of world positions from `BONES.json` + the raw
`VectorProperty` tags, and re-counted the GRB-8 orphans from `LIGHTS.json`; they match.

The problems are small and local: the `up`/`right` **axis names are swapped** in the JSON and the
convention sentence (UE/PSK is X forward, Y width, **Z up**, but the record calls local +Y "up"), the
four rope-anchor outliers are explained as "helicopter rope anchors … by design" on the strength of
the socket **name** alone (R4/R5), some prose counts are typed (`--check` cannot see them, R11), the
same quaternion is applied in opposite senses for positions and for direction vectors without any
note, and the MODLOG says the markdown table carries columns it does not.

## Check output (verbatim)

Command (project root `E:/Modding/JustCause3/JC3-Batmobile`):

```
python Tools/scripts/grab_sockets.py --check
```

stdout, exact:

```
PASS: 65/65 Batmobile_V2 sockets placed; 61/65 inside the body box +0.5 m. The four HangFromRope anchors are 2.446 m above the box by design. GRB-8 has 6 orphan light references (2 in Batmobile); 6 HeadLight* sockets ride Winch_DOOR_Mesh. Required anchors 13/13.
  socket_count_65                            PASS
  all_sockets_placed                         PASS
  all_socket_bones_in_bones_json             PASS
  all_socket_parents_resolved                PASS
  required_anchors_present                   PASS
  headlight_family_present                   PASS
  brakelight_family_present                  PASS
  wheellight_family_6                        PASS
  forward_vectors_unit                       PASS
  muzzle_forward                             PASS
  missile_forward_up                        PASS
  tail_forward                               PASS
  body_box_outliers_are_hang_ropes           PASS
  grb8_orphan_refs_total_6                   PASS
  grb8_orphan_refs_this_package_2            PASS
  door_bound_headlights_6                    PASS
```

Exit status `0`. The check is read-only: both output files still carry their
`2026-10-25 07:39:55` mtime after the run.

## Issues

### 1. `up` and `right` are the wrong two axes (JSON + convention sentence)

`Research/BatmobileGrab/SOCKETS_JC3.md:11` — "`forward` is the socket's local +X (UE forward), and
`up` is local +Y." The project's own frame statement is `bat_assemble.py:231`: **"PSK (X length
prow+, Y width, Z up)"** — so local **+Z** is up and local **+Y** is the width/right axis. The JSON
confirms the labels are swapped: for a chassis socket with a null rotator
(`Driver`, `up_jc3` = `[-1.0, 0, 0]`, `right_jc3` = `[0, 1.0, 0]`) the field named `up` is sideways
and the field named `right` is world-up. Same for `HeadLight1`, `CannonMuzzle`, `LWheelLight`.

Positions and `forward` are unaffected, and the markdown table prints only `forward`, so the Done
line still holds — but every downstream card that uses `up_jc3`/`right_jc3` (LGT, WPN, FX) would
place a sideways "up". Nothing in `checks` tests `up` or `right`, so `--check` cannot see it.

Fix: compute `up = local +Z` and `right = local +Y` (fields and the convention sentence), and add an
orthogonality/handedness check (e.g. `fwd × up = -right`, and `up` ≈ `+Y` for the six
`Winch_DOOR_Mesh`/chassis sockets). The rest of the record is unchanged.

### 2. "helicopter rope anchors … by design" is a name-based inference (R4/R5)

`SOCKETS_JC3.md:5` and `:41` — "The four HangFromRope anchors are 2.446 m above the box **by
design**"; "These four are the **helicopter rope anchors**. They are placed correctly and are not a
transform error". What the files support is narrower:

- the socket records are named `HangFromRope_*` and carry a bone-local `z` of **460.5 cm**
  (`objects.jsonl` records for `Playable_Batmobile_SF`, e.g. `HangFromRope_Rear_Right`
  `[-31.115643, -18.333076, 460.5]`; also `MECHANICS.md:900-904`);
- therefore the world y is 5.308 m and the point is 2.446 m above the **expanded** box. That is
  asset data, not transform drift — true and worth stating.

What is **not** in the data: that a helicopter/rope behaviour consumes these sockets. No decoded
`RSimpleRopeComponent` reference, no `.epe` usage and no `MECHANICS.md` behaviour row ties
`HangFromRope_*` to a rope or winch. `ASSETS.md:144` only counts `RSimpleRopeComponent` (6) somewhere
in the packages; it does not link it to these sockets. So "helicopter rope anchors" and "by design"
are plausible-sounding implementation detail of exactly the kind R4/R5 forbids. The measured
sentence should be: "the four `HangFromRope_*` sockets sit 4.605 m above their wheel pivots in the
shipped socket data (2.446 m above the expanded box); which behaviour reads them — if any — is
UNKNOWN". If a rope behaviour is meant, cite the decoded record, not the socket name.

### 3. Typed prose counts (R11)

The tables/verdict are computed, but three sentences are literals that `--check` re-renders without
re-deriving:

- `SOCKETS_JC3.md:54` — "in **three** packages, so **six** references exist";
- `SOCKETS_JC3.md:58` — "These **six** are real sockets";
- `SOCKETS_JC3.md:41` — "These **four** are …" (the four is derived at :5, the sentence is literal).

They currently agree with the data (3 packages, 6 orphans, 4 outliers, 6 door-bound), so this is a
hygiene issue, not a wrong number. Related: `counts.bones_found` and `counts.placed` are simply
`len(rows)` (`grab_sockets.py:459-460`) — they are not measurements; the real work is in
`all_socket_bones_in_bones_json` and `all_sockets_placed`. Either derive the words from the counts or
mark those keys as aliases.

### 4. Positions and directions use opposite quaternion senses, with no note and no check for the cases where it matters

`grab_sockets.py:315` places the socket with
`wp = bwp + qrot(bwq, loc, inverse=True)`, while `:317-319` builds `fwd/up/right` with
`qrot(wq, [1,0,0])` etc. — **no** inverse. For 24 of the 65 sockets the two senses give different
vectors (up to 180° apart): `Mine1…8`, `MissileL/R`, `SideExhaustL/R`, `Dashboard_Light`,
`Cockpit_Hologram`, `BatterySocket`, `BrakeLight*`/`BrakeTrail*`, `PassengerNoiseOrigin` and the
four `HangFromRope_*`. The checks only pin `forward`, and the missile check
(`missile_forward_up`, `grab_sockets.py:531`) asserts the doc's own sense — it cannot distinguish the
two.

The doc's sense is probably the right one: only under it do `SideExhaustL`/`R` come out
mirror-symmetric (`[0.757, 0.157, 0.635]` vs `[-0.764, 0.080, 0.641]`); the inverse sense gives both
pointing left (`[-0.756, …]` / `[-0.745, …]`), which a symmetric pair of exhausts should not. But
that argument is nowhere in the doc, and a reader has no way to know why the inverse applies to
positions only. One sentence in the Convention section (PSK bone offsets are left-handed, so the
inverse maps them; socket rotations compose the other way) plus a check on a rotated-bone socket
would close this. Without it the `up`/`right` columns (issue 1) are doubly unverifiable.

### 5. The MODLOG overstates what the markdown table carries

`MODLOG.md:8151-8152` — "the table carries bone, parent bone, part hint, relative location/rotation,
world position, forward/up/right axes and the body-box result". `SOCKETS_JC3.md:71` has only
`socket | bone | parent | part | role | pos x/y/z | fwd x/y/z | inside`; relative location/rotation,
up and right live in the JSON only. That is fine as a record, but the journal sentence should say
"the record" or the table should gain the columns.

### 6. Wording: "2.446 m above the box" means the expanded box

`sockets.md:5` / the card. The body bbox is `y 0.091 … 2.362` (`stations.json`); the test box is that
+0.5 m (`2.862`), and 5.3077 − 2.862 = 2.446. Above the **body** box the same point is 2.946 m. The
number is right; say "above the expanded (+0.5 m) box" so it cannot be read two ways.

## Spot-checks

| value in the doc | where verified | result |
|---|---|---|
| `HangFromRope_Front_Left` y **5.308**, outlier 2.446 m | `objects.jsonl` `VectorProperty` `[36.692184, -2.405115, 460.5]`; `BONES.json` `Wheel_Front_Left` pivot_jc3 y `0.702679`; 0.702679 + 4.605 = **5.307679** | match (0.03 mm) |
| `Driver` at `-0.003, 0.865, -1.065` | raw socket `[121.965767, 0.25, 84.249992]` on `Batmobile_Chassis` (pivot 0), `to_jc3_rot = (-y, z, -x)·0.01 + offset` → `(-0.0025, 0.8647, -1.0654)` | match |
| **6** GRB-8 orphans, **2** in `Playable_Batmobile_SF`; none is a socket | `LIGHTS.json`: 6 entries with `orphan_socket: true` (`HeadLight1c`/`2c` in Batmobile, MK2, Funhouse); the 65 socket names contain no `HeadLight1c`/`2c`; `objects.jsonl` has 65 `SkeletalMeshSocket` records, all `outer = Batmobile_V2_Mesh.Batmobile_V2` | match |
| `MissileLaunchSockets` = "two undecoded entries (shape only)" | `WEAPONS.md:841` — `ArrayProperty`, "array, **2 items**, 8 B each - payload not decoded"; `CHAIN.json` value `null` | match |
| 65/65 inside bones; 24 sockets on `Batmobile_Chassis` | JSON `sockets` all bones in `BONES.json`; bone histogram `Batmobile_Chassis` = 24 | match |

Checks that are genuinely independent: `socket_count_65` (source count, `grab_sockets.py:299`),
`all_socket_parents_resolved`, `body_box_outliers_are_hang_ropes`,
`grb8_orphan_refs_total_6/this_package_2`, `door_bound_headlights_6`. The weakest are
`forward_vectors_unit` (asserts the doc's own vectors) and `missile_forward_up` (asserts the doc's own
convention) — they cannot catch issue 4.

## Rules notes

- **R4**: positions are decoded/derived and carry inputs + sha256 of every source in the JSON; the
  rope-anchor behaviour is the one value with no provenance (issue 2).
- **R5**: `role` is a name-derived label and is presented as a label, not behaviour; the muzzle checks
  are the behaviour test. The rope text is the exception.
- **R11**: counts in the tables/verdict are derived; the prose words (issue 3) and the `bones_found`
  alias are not.
- **R14**: the MODLOG entry exists, carries the exact `--check` line and a revert path.

## Limits of this review

Read-only: I ran `--check`, read `BONES.json`, `LIGHTS.json`, `grab_model.sockets` output,
`objects.jsonl`, `MECHANICS.md`, `WEAPONS.md` and `stations.json`, and recomputed individual
positions independently (not through `grab_sockets.py`). I did not re-derive all 65 positions, did
not open the `.psk`, did not test the socket transforms in game, and did not verify the `.epe` side
of the door-bound headlights beyond `LIGHTS.json`. No game launched, no archive/dropzone write, no
commit.

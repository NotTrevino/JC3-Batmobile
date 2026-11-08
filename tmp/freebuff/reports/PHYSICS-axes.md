# PHYSICS-axes — DONE

**STATUS: done.** The card's three oracles were run over all 419 hinges; none of the six candidate
rows passes, so the constraint axis stays **UNKNOWN** on the fleet, with the donor's five Serpente
panels as the only measured pointer at a field (`A0`, `derived`, 5/5).

## Deliverables

| what | path |
|---|---|
| report | `Research/JC3Grab/CONSTRAINT_AXES.md` (10,898 bytes, `--check` OK) |
| script | `Tools/scripts/jc3_constraint_axes.py` (`--write` / `--check`) |
| this report | `tmp/freebuff/reports/PHYSICS-axes.md` |

Read-only everywhere else: the donor `sportsmuscle.physicsc`, the 51 fleet `.physicsc` files and
`jc3hkx.py` were opened read-only; no other file was written.

## What was decoded / derived / UNKNOWN

| claim | label | evidence |
|---|---|---|
| Hinge objects hold one frame atom at +0x020 (type 2, 144 B): two `hkTransform`s, rows at +0x30/+0x40/+0x50 and +0x70/+0x80/+0x90, translations at +0x60 and +0xA0 | decoded | re-read from the donor, matches `PHYSICS_LIMITS` atom table |
| Fleet = 51 `.physicsc`, 419 `hkpLimitedHingeConstraintData` | decoded | `glob E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc` = 51 files, 419 objects — the same 419 PHYSICS_LIMITS counts |
| Two atom frames byte-identical in 410/419 hinges; pivots coincide in 407/419 | decoded | per-hinge comparison, 1e-6 |
| O1 (unit length): **419/419 for all six candidates** | decoded | `norm(row) == 1 ± 1e-3` |
| O2 (perpendicular to pivot-to-pivot): input exists in only **12/419**; best `A1`/`B1` 9/12, `A0`/`B0` 0/12 | decoded | `pivotB − pivotA`, zero in 407 → oracle vacuous |
| O3 ("agreement" with the hull-extent direction): parallel best `A1` 101/402, perpendicular best `A0` 151/402 | decoded + derived | host = largest non-compound body whose world AABB holds the pivot; control host (first body entry, 245 hinges) gives `A0` 112/245, `A1` 18/245, `A2` 42/245 — same ordering |
| No candidate passes the three oracles over 419 → **UNKNOWN** | UNKNOWN | card's own rule |
| Donor doors/hood/trunk: `A0` is exactly `[0,-1,0]` / `[0,1,0]` (doors, sign = side), `[1,0,0]` (hood, hood_signature), `[-1,0,0]` (trunk); door hinge axes are **vertical in the car frame** | decoded | donor panel table in §4 |
| Swing test (rotate hull centre about each candidate by the decoded max angle: outward ≥0.10 m for doors, rise ≥0.10 m for hood/trunk) → `A0` 5/5, `A1` 1/5, `A2` 1/5 | derived | §4 table; agrees with `PHYSICS_LIMITS_REVIEW` §5 |
| `A0` is the axis for all 419 hinges | UNKNOWN | frames identical, pivots coincident, cinfo holds one body id, frames car-axis-aligned in most hinges |

## Commands run (with output)

### 1. Where the Serpente donor is, and the fleet size

```
$ find E:/Modding/_shared/gamedata/JC3grab -iname "*serpente*"        # nothing
$ grep -o '"[^"]*serpente[^"]*"' Research/JC3Grab/DOOR_ANGLES.json | sort | uniq -c
      1 "serpente_vanilla_limits"
      1 "vanilla_serpente"
$ grep -n -i "serpente" Research/JC3Grab/DOOR_ANGLES.md
19: Worked example - the vanilla Serpente's left door. `sportsmuscle_vehicle_parts.vmodc` ...
484:## 5. The vanilla Serpente (sportsmuscle)
$ find E:/Modding/_shared/gamedata/JC3grab -name "*.physicsc" | sed 's#.*/##' | sort | tr '\n' ' '
apc ... sportsmuscle.physicsc (x5) ... vintagesports.physicsc      (51 files)
```

So the "Serpente donor" is `sportsmuscle` (`v0300_car_kensington_sportsmuscle`) — documented in
`DOOR_ANGLES.md` §5, not guessed.

### 2. Donor probe: cinfos, the five panel frames, body AABBs

```
bodies 62 cinfos 11
0 0x4da80 hkpLimitedHingeConstraintData body 1 f0c 0x7fffffff ...
...
10 0x4e740 hkpLimitedHingeConstraintData body 35 f0c 0x7fffffff ...
0x4da80 ext 304   A [[0.0,-1.0,0.0],[0.0,0.0,1.0],[-1.0,-0.0,0.0]]  A_t [-1.0185,0.6223,-0.7714]
                  B [[-0.0,-1.0,0.0], ...]                          B_t [-1.0185,0.6223,-0.7714]
0x4e3b0 ext 304   A [[1.0,0.0,0.0],[0.0,0.0,-1.0],[-0.0,1.0,0.0]]  A_t [0.0,1.0572,-0.8478]
0x4e740 ext 304   A [[-1.0,0.0,0.0],[0.0,-0.4296,0.903],[0.0,0.903,0.4296]] A_t [0.0035,1.44,1.0209]
1 hknpConvexPolytopeShape box ([-1.031,0.345,-0.761],[-0.644,1.39,0.654])   # door_f_l
19 ... box ([-0.791,0.757,-2.37],[0.781,1.085,-0.88])                        # hood
```

Both atoms carry the same frame, so the axis is not handed over by a second frame.

### 3. Fleet probe: the six candidates against the three oracles

```
files 51, hinges 419
A==B rows 410/419, pivot pair zero 407, nonzero 12 (max 8.87 - the project test copies)
body entries 38199, with nonzero position 4082   -> world transforms must be applied
A0 unit 419/419 | o2 0/12  | o3(perp<=0.10) 110/409 | o4 309/409 | mean|cos| 0.380
A1 unit 419/419 | o2 9/12  | o3(perp<=0.10)  63/409 | o4 350/409 | mean|cos| 0.563
A2 unit 419/419 | o2 1/12  | o3(perp<=0.10)  73/409 | o4 109/409 | mean|cos| 0.458
```
(the first pass resolved the partner as the largest containing body *including* compounds; the
donor's body 60 is the whole car, so that rule is wrong — replaced, see 4)

### 4. Donor probe with world AABBs and the geometric host rule

```
{"off":"0x4da80","body":1,"name":"sportsmuscle_door_f_l","partner":60, ...}
```
Body 60 (a `hknpDynamicCompoundShape`) encloses every part, so the host rule was narrowed to
non-compound bodies; the donor panels then resolve to body 42 (the chassis mesh) and the fleet
counts become the ones in report §2.

### 5. A failed command, kept for the record

```
$ python - <<'PYEOF' ... psd=[o for o in pf.objects if o.cls=="hknpPhysicsSystemData"][0]
IndexError: list index out of range
```
One fleet file carries no `hknpPhysicsSystemData`; the script counts it (`no_psd`) instead of
crashing.

### 6. Write and check

```
$ PYTHONIOENCODING=utf-8 python Tools/scripts/jc3_constraint_axes.py --write
wrote E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\CONSTRAINT_AXES.md 10898 bytes
hinges 419 passing [] donor_pass {'A0': 5, 'A1': 1, 'A2': 1, 'B0': 5, 'B1': 1, 'B2': 1}
A0 unit 419 o2 0/12 o3 perp 151/402 par 33/402
A1 unit 419 o2 9/12 o3 perp  42/402 par 101/402
A2 unit 419 o2 1/12 o3 perp  68/402 par 54/402
B0 unit 419 o2 0/12 o3 perp 149/402 par 33/402
B1 unit 419 o2 9/12 o3 perp  42/402 par 101/402
B2 unit 419 o2 1/12 o3 perp  68/402 par 47/402

$ PYTHONIOENCODING=utf-8 python Tools/scripts/jc3_constraint_axes.py --check
check OK 10898 vs 10898      (exit 0)
```

## Limits of this pass

- O2 cannot be run on 407/419 hinges (coincident pivots — a property of how Havok places a hinge
  frame), so it cannot carry a layout even in principle.
- O3's host body is geometric, not a field: the cinfo stores one body id, and `PHYSICS_ROLES2`
  already recorded that the partner is not in the record. The control run shows the choice does not
  flip the ordering.
- The swing test that does separate the rows exists only on the donor (5 panels), because it needs
  each panel's identity, which comes from the parts module, not from the `.physicsc`.

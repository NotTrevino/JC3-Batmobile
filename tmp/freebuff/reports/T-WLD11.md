# T-WLD11 — the three stunt areas: re-index, move, or UNKNOWN

STATUS: done (both repairs decided by oracle: **re-index not supported**, **move UNKNOWN**;
the area geometry is decoded to be a bit-exact cache of the `DeformPoints` list, and neither
frame lands all three areas inside the donor's own tolerance band)

## Summary

`T-WLD11` in `Working/Translation/T15_WORLD.md` was `blocked` on "the 3 stunt areas bind donor
`deform_points` indices and sit 0.10-0.60 m off the Batmobile shell". This pass measured the
question instead of repeating it, and two decoded facts change what the repair can be:

1. **The surface *is* the point list.** For all 22 area vertices,
   `stunt_areas[i].vertices3D_local[j]` equals
   `DeformPoints.points[deform_points[j]].start_transform[12..14]` **bit-exactly** (max delta
   `0.0 m`). `vertices3D_local` is a cache, not an independent surface, so "moving the area"
   is "moving the deform points", and whether the runtime recomputes the cache is the open
   question, not the geometry.
2. **The donor's own areas float above the donor shell.** Measured against the donor's own
   geometry (`geom` sidecar, 70 302 vertices / 75 508 triangles), the donor's 22 bound points
   sit **0.0388 – 0.1578 m** above the donor skin (median 0.1056), on faces whose up-cosine is
   ≥ 0.7529. That is the authoring tolerance the Batmobile must be judged against — the areas
   were never meant to be *on* the shell, and the earlier "0.10-0.60 m off" figure is the gap
   between donor-authored points and Batmobile-sized skin, not a per-vertex error.

Judged against that band, on the Batmobile body mesh
(`Working/Appearance/build_parts/body_lod1.rbm`, 38 443 vertices / 32 124 triangles):

| frame | vertices inside the donor band on a standing face | inside the shell | hit rate |
|---|---:|---:|---:|
| stored entity coordinates | 0 | 11 | 0/22 |
| G2-18 normalised map | 4 | 0 | 4/22 |

- **O-1 re-index → not supported.** Only **15 of 135** donor points pass (outside the shell,
  inside the band, on an up-facing face) anywhere on the Batmobile, and **0 of 3** areas can be
  rebuilt from them within one edge length (≤ 0.30 m) of each vertex. The decisive reason is
  geometric, not statistical: the highest donor point is y **1.5242 m** while the Batmobile roof
  surface reads y **2.0811 m** (deck y 1.3612 m), so no existing point can lift `main_area`
  onto the roof it is supposed to cover.
- **O-2 move → UNKNOWN.** The move itself is encodable (the 22 targets are ray-castable, the
  part bindings resolve — B-04 keeps indices 0/24/25 — and 6 positions are shared by two
  areas, so both copies must move together), but which field the runtime trusts — the stored
  `vertices3D_local` or a recomputation from `DeformPoints` — is **not decoded anywhere in the
  entity, the geom sidecar or the build's modules**. Writing a value blind would be a guess.

So the row stays **UNKNOWN**, but now for one named, testable reason instead of an unexplained
"blocked": a probe that re-reads the module after an edit tells us which field wins.

The earlier task in this session, **G3-10k**, is also finished and passing
(`Tools/scripts/jc3_inertia2.py --check` → `CHECK PASS`, report at
`tmp/freebuff/reports/G3-10k.md`).

## Files written

- `Tools/scripts/t_wld11.py` — new tool, `--write` / `--check` / `dump areas|points|candidates`.
  Reads the donor entity (`StuntAreas`, `DeformPoints`), the donor geometry sidecar, the
  Batmobile body mesh, `stations.json` and the B-04 part table; computes the donor tolerance,
  the per-vertex measurement in both frames (stored and G2-18's map), the full 135-point table,
  and both oracles. `--check` re-derives the JSON and the note, compares both byte-for-byte,
  re-runs the oracles and fails if the verdict moved.
- `Working/Translation/T_WLD11_AREAS.md` — generated note: verdict, the two decoded facts,
  the donor tolerance, per-area/per-vertex tables with both frames and the nearest-vertex
  distance, all 135 `deform_points` with names/parts/positions, the oracles, UNKNOWNs.
- `Working/Translation/t_wld11_areas.json` — the same measurements as data (22 vertices,
  135 points, both oracles, input hashes).
- `tmp/freebuff/reports/T-WLD11.md` — this report.

Not touched: `Working/Entity/bm_epe_edits.json`, `Working/Translation/T_ROWS.jsonl` (and its
`.bak-b13`), `T15_WORLD.md`/`t15_world.json`, any `Builds/` file, any game install.

## Values, labelled

| value | label |
|---|---|
| 135 `DeformPoints`, 3 active `StuntAreas` in 32 slots, 64 weld rows | decoded (donor `.ee.json`, module rows) |
| the build ships `sportsmuscle_stunt_areas.vmodc` + `sportsmuscle_vehicle_deform.vmodc` | decoded (`Builds/bm-009/aaf/models/...`, both present) |
| `vertices3D_local[j] == points[deform_points[j]].start_transform[12..14]`, delta 0.0 m over 22 vertices | decoded (bit-exact comparison) |
| areas bind indices 76/87/110/28/11/65, 89/70/58/42/108/25, 53/99/81/132/116/35/10/63/48/32; 22/22 exist | decoded |
| donor tolerance band 0.0388–0.1578 m (median 0.1056), min up-cosine 0.7529 | derived (22 bound points → donor shell, exact point-triangle distance) |
| Batmobile body y: roof 2.0811 m (z −0.5), deck 1.3612 m (z −2.14) | derived (ray cast down on `body_lod1.rbm`) |
| stored frame: 0/22 in band on a standing face, 11/22 inside the shell, gaps 0.0002–0.0813 m | derived |
| mapped frame: 4/22 in band, 0/22 inside, gaps 0.1236–0.5880 m | derived |
| pool of donor points that pass on the Batmobile: 15/135; 0/3 areas re-buildable | derived (O-1) |
| 6 positions shared by two areas; part indices 0/24/25 in B-04's kept range | decoded |
| runtime precedence between `vertices3D_local` and `DeformPoints` | **UNKNOWN** |

## Commands run (verbatim)

1. Reading the brief's material and the toolchain:

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && ls -la Working/Translation/ ... Working/Appearance/build_parts
(... 80 .rbm parts incl. body_lod1.rbm, assembly.json, T15_WORLD.md 18256 B, t15_world.json 42666 B)

$ ls /e/Modding/_shared/gamedata/JC3grab/
audio b13 ... entities ... geom ... hkx ... phys ...
```

2. The donor entity's shape — deform points carry stunt names and part bindings:

```
$ uv run --with numpy python tmp/freebuff/scratch/wld11_probe1.py
deform points: 135 index range 0 134
sample: [(0, {'name': 'grill'}, [-6.31228177e-05, 0.611966372, -2.48016548]), ...]
slots 32 declared 3
0 front_area 24 6 4 [76, 87, 110, 28, 11, 65]
1 front_signature_area 25 6 4 [89, 70, 58, 42, 108, 25]
2 main_area 0 10 8 [53, 99, 81, 132, 116, 35, 10, 63, 48, 32]
front_area vertices (16, 3) ... |V - P| per vertex: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
main_area ... |V - P| per vertex: [0.0, 0.0, ... 0.0]
```

   (the areas' `vertices3D_local` are the bound deform points, exactly — the fact that decides
   what a repair can be)

3. Donor tolerance and both frames:

```
$ uv run --with numpy python tmp/freebuff/scratch/wld11_probe2.py
deform points 135 fields ['from_part', 'from_part_hash', 'from_part_index', 'has_custom_end',
 'name', 'name_hash', 'shape_key', 'skinned_to_part', 'skinned_to_part_hash', 'skinned_to_part_index']
areas [('front_area', 0, 'sportsmuscle_hood', 6, [76, 87, 110, 28, 11, 65]), ...]
donor shell verts 70302 tris 75508 bbox [-1.062, -0.429, -2.57] [1.061, 1.511, 2.564]
bat verts 38443 tris 32124 bbox [-1.751, 0.087, -3.422] [1.746, 2.363, 3.605]
-- donor area clearance (donor deform point -> donor shell)
front_area tri [0.1056, 0.1056, 0.1578, 0.1219, 0.1219, 0.1568]
main_area tri [0.1056, 0.0885, 0.0999, 0.0733, 0.0389, 0.0388, 0.0716, 0.0901, 0.0742, 0.1056]
donor gap: min 0.0388 med 0.1056 p95 0.1578 max 0.1578
-- batmobile clearance, G2-18 normalised map
front_area tri [0.3593, 0.3581, 0.1237, 0.1597, 0.1586, 0.1236]
main_area tri [0.3593, 0.5873, 0.4481, 0.2301, 0.477, 0.4761, 0.2371, 0.4509, 0.5874, 0.3581]
all 135 mapped: min 0.0007 med 0.2359 max 0.5874  count<=0.03: 15 count<=0.05: 22
```

4. Signed side and the build's module inventory:

```
$ uv run --with numpy python tmp/freebuff/scratch/wld11_probe3.py
front_area  batraw d [0.0566, 0.056, 0.0219, 0.0347, 0.0348, 0.0219] inside [True, True, False, False, False, False]
main_area   batraw d [0.0566, 0.0807, 0.0002, 0.0393, 0.051, 0.0508, 0.0395, 0.0003, 0.0813, 0.056] inside [True, True, False, False, True, True, False, True, True, True]
raw: min 0.0002 max 0.4498  outside 80 inside 55  <=0.158 outside 64
map: min 0.0007 max 0.5874  outside 119 inside 16  <=0.158 outside 31

$ find Builds/bm-009 -iname '*stunt*' -o -iname '*deform*'
Builds/bm-009/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_stunt_areas.vmodc
Builds/bm-009/aaf/models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_deform.vmodc
```

5. The shipped tool, write and check:

```
$ cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy python Tools/scripts/t_wld11.py --write
areas 3  vertices 22  indices exist 22/22
stored pass 0  mapped pass 4  inside stored 11  inside mapped 0
O-1 FAIL  pool 15
verdict UNKNOWN  digest 9b05cd103890ce6b

$ uv run --with numpy python Tools/scripts/t_wld11.py --check
json identical True  md identical True
areas 3  vertices 22  O-1 pass False  O-2 pass False
CHECK PASS
```

6. Per-area hit counts and the O-2 invariants, read back from the shipped JSON:

```
$ uv run python -c "..."
O2 {"cache_vs_list_m": 0.0, "part_binding_resolves": true, "pass": false,
    "positions_shared_by_two_areas": 6}
counts {"area_vertices": 22, "indices_exist": 22, "mapped_inside": 0, "mapped_pass": 4,
        "points_ok_on_batmobile": 15, "stored_inside": 11, "stored_pass": 0}
mapped range 0.1236 0.588
stored range 0.0002 0.0813
per-area [('front_area', 0, 2, 0.0, 6, 1.8431), ('front_signature_area', 0, 2, 0.0, 6, 1.8431),
          ('main_area', 0, 0, 0.0, 10, 1.9038)]
o1 areas [('front_area', 0, 6, False), ('front_signature_area', 0, 6, False), ('main_area', 0, 10, False)]
```

## Answer to the brief, point by point

- **Distance from each bound point to the nearest Batmobile body vertex** — per-vertex column
  in `T_WLD11_AREAS.md` §3 (exact point-triangle distance is the same table's `stored gap`;
  the nearest-vertex figure is reported alongside because the brief asked for it).
- **Which donor `deform_points` indices exist and where** — §4 lists all 135 with name, part
  binding and position; all 22 bound indices exist.
- **Oracle from the donor's own tolerance** — §2: band 0.0388–0.1578 m above the donor skin,
  standing face (cos ≥ 0.7071). Applied to the Batmobile: 0/22 stored, 4/22 mapped.
- **Re-index vs move** — re-index **not supported** (O-1: 0/3 areas, 15/135 usable points,
  highest point below the roof); move **UNKNOWN** (O-2: cache/list precedence not decoded).
- **Outputs** — `Working/Translation/T_WLD11_AREAS.md`, `Tools/scripts/t_wld11.py`
  (`--write`/`--check`), both regenerated and checked above.

## UNKNOWNs

1. **Runtime precedence between `vertices3D_local` and `DeformPoints`.** Tried: the donor
   entity rows (both fields agree bit-exactly), the entity `.bin`, the geom sidecar, the build's
   `sportsmuscle_stunt_areas.vmodc` and `sportsmuscle_vehicle_deform.vmodc`, and the whole
   `Builds/bm-009` tree for any statement of precedence (none). It would be settled by an
   in-game probe: edit one point's `start_transform`, re-read the surface (Q-1 #3).
2. **Whether `DeformPoints` also drives deformation/skinning.** The points carry
   `from_part`/`skinned_to_part` and `shape_key`/`has_custom_end`; nothing in the tree says
   whether moving one deforms geometry. It would be settled by the same probe, watching the
   mesh as well as the standing surface.
3. **Whether the areas are validated at runtime** against the list (a stale cache is exactly
   the state a move would create). Not decoded; same probe.
4. **The band's edges are a 22-point sample** of authoring intent, not a per-vertex guarantee.
   The band is the tightest measured evidence available and is used as such (the tool prints
   the min/median/max, so a wider sample would move it, not the verdict's structure).

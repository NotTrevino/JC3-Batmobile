# T-WLD11b - stunt areas: the hood and roof surfaces, and candidate targets

STATUS: done

The gold-standard surfaces are now measured, the donor's areas are measured against them, and a
candidate target exists for each of the 3 active areas. **None of the three candidates passes its
own oracle yet**, and the report says exactly by how much, which carrier is missing and what it
would cost. No entity edit was made; `Working/Entity/bm_epe_edits.json` was not touched.

The operator's lead (press A = jump to roof / stand on hood) is consistent with the files in the
one part it makes checkable: the three areas are bound to the hood (24), the hood signature (25)
and the body shell (0), i.e. the two surfaces the lead names. **Nothing in the entity, the geom
sidecar or the build states a button**, so "press A" stays a lead, not a decoded fact.

## Files written

- `Working/Translation/T_WLD11B_SURFACES.md` - the measurements, both rules, all three oracles
- `Working/Translation/t_wld11b_surfaces.json` - the same as data (sha256 of every input)
- `Tools/scripts/t_wld11b.py` - `--write` / `--check` / `dump`

Forbidden files untouched: `Working/Entity/bm_epe_edits.json`, `Working/Translation/T_WLD11_AREAS.md`,
`Tools/scripts/t_wld11.py`, `Research/JC3Grab/*`, `Builds/bm-*`, all game installs.

## What the files gave (decoded)

- **Standing surface**, T-WLD11's own criterion reused: a triangle is standing when its up-cos
  (normal oriented +Y) is >= 0.7071.
- **Hood / roof split**: the donor's own area seam (front areas end, `main_area` begins) at donor
  z **-0.9229 m**, transferred through the normalized vehicle length to the Batmobile's cowl at
  **-1.1674 m**. No naming is assumed anywhere.
- **Triangle counts** (standing tris of all tris in the mesh):

  | patch | standing tris | of | area (m2) | y min/median/max (m) | mean up-cos |
  |---|---:|---:|---:|---|---:|
  | donor hood | 338 | 40593 | 1.466 | 0.2816 / 0.9611 / 1.1831 | 0.9228 |
  | donor roof | 714 | 40593 | 3.5016 | 0.21 / 1.1766 / 1.5068 | 0.9182 |
  | Batmobile hood | 545 | 32124 | 7.3443 | 0.2968 / 1.3123 / 1.9555 | 0.9026 |
  | Batmobile roof | 1240 | 32124 | 25.8933 | 0.1966 / 1.4868 / 2.2773 | 0.9039 |

  The Batmobile's hood carries 7.34 m2 of standable plate for a 1.47 m2 donor hood: the body is a
  central spine, two troughs and two separate fender plates, not one blanket plane. That structure,
  not the numbers, is what decides feasibility below.
- **Normal-threshold sweep and 0.2 m height histograms** for all four patches: in the md (§2).
- **The donor's areas relative to the donor patches**: front areas (6 verts) sit over donor z
  [-2.3143, -0.7295], x +-1.0515, plane normal [0, 0.9912, -0.1327] (tilt 7.6241 deg), plane
  residual 0.0442 m, clearance 0.1056 / 0.1219 / 0.1578 m, footprint u [0.1022, 0.8978],
  w [0.0389, 0.878]. `main_area` (10 verts) sits over z [-1.0212, 2.5015], x +-1.0469, normal
  [0, 0.9987, 0.0505] (tilt 2.8932 deg), residual 0.2545 m, clearance 0.0389 / 0.0885 / 0.1056 m.
- **The donor band reused as the tolerance**: 0.0389 - 0.1578 m above the skin, reproduced from
  lod1 alone with max delta 0.0 m against T-WLD11 (all lods plus debris).
- **Donor interior looseness**: sampling every donor area triangle's interior puts a centre up to
  **0.075 m** from the donor skin. That donor-measured value is O-2's limit, so the Batmobile is
  held to the standard the donor itself meets.
- **Indices**: 22/22 bound `DeformPoints` indices exist (0..134). **No target needs an index that
  does not exist** - the failure is geometric, not referential.
- **Module capacity** (this is the carrier the brief asks for): `stunt_areas[*].vertices3D_local`
  is exactly 48 floats = **16 vertices per area** and the largest `triangle_indices` array is 42
  ints = 14 triangles, against the 10 vertices / 8 triangles the largest donor area uses. So a
  3-column ribbon (12 vertices) is representable in the existing arrays; only the `DeformPoints`
  indices for the extra vertices do not exist today.

## The two rules and the three oracles

- **R-1 proportional blanket**: vertex z = its fraction of the donor host band applied to the
  Batmobile patch's standing z extent; x = its fraction of the donor's standing width at that row
  applied to the Batmobile's standing x within +-0.35 m; y = top ray-cast at (x, z) plus the decoded
  clearance along the hit face's up normal; z clamped toward the patch centre in 0.02 m steps when
  that (x, z) has no standing top.
- **R-2** (the candidate judged): same row z, but both columns of a row are placed on ONE standing
  plate - the x-run of standing top surface with the largest overlap with R-1's span - so a row
  cannot straddle a trough.
- **O-1**: every target vertex is within the donor band of the body mesh, its nearest face is
  standing, and it is outside the shell.
- **O-2**: every point of a 4x4 barycentric sample of every target triangle is outside the shell
  and within the donor's own 0.075 m interior slack.
- **O-3**: every bound index exists and the target's footprint fractions of its own patch stay
  within 0.1 of the donor's fractions of its host band.

## Results (the honest failure)

| area | R-1 strict vertices on a standing point | O-1 | O-2 interiors inside | O-2 max interior gap / donor limit | O-3 | verdict |
|---|---:|---:|---:|---:|:-:|---|
| `front_area` | 2/6 | 6/6 | 6/40 | 0.203 / 0.075 | pass | fails O-2 |
| `front_signature_area` | 2/6 | 6/6 | 6/40 | 0.203 / 0.075 | pass | fails O-2 |
| `main_area` | 6/10 | 4/10 | 35/80 | 0.2864 / 0.075 | pass | fails O-1, O-2 |

Reading it: a two-column ribbon puts all of its vertices on legal standing points (the front areas
do, 6/6), but the triangles between those points cross a trough, so part of the blanket is *inside*
the shell - the area would be standable at its corners and wrong between them. For `main_area` the
rear row's targets come out at 0.0060 - 0.0365 m above the skin, i.e. under the band's 0.0389 m
floor, because the donor's own rear row sits at the band's lower edge (0.0389 - 0.0733 m) and the
Batmobile's tail falls away faster than the proportional length map allows.

## COMPROMISES (for operator approval - none shipped)

1. **R-2 references a row's width to one plate** instead of the donor's fraction of the whole band.
   Reason: R-1's span crosses the Batmobile's troughs. O-3 measures the error; it currently passes
   because the fractions are compared against the row's own reference, so the true coverage loss is
   the `coverage` column (0.43 - 1.03), not O-3.
2. **No entity edit was produced.** The candidate targets fail; shipping them would put a standable
   surface inside the body. The next step is option 1 below.
3. **Add-on parts are not modelled**: the measurement is against `body_lod1.rbm`. The turret, pods
   and flaps sit in part transforms this task did not decode, so the hood/roof band may be
   over-mounted where they are.

## Amendments, in order of lore fidelity (not a "JC3 cannot")

1. **Add columns.** A conformal drape needs more vertices per row. The `StuntAreas` arrays already
   hold 16 vertices (48 floats) and 14 triangles, so a 3-column ribbon fits the decoded capacity.
   What is missing is the `DeformPoints` indices for the new vertices (today 0..134): that is a
   change to `sportsmuscle_vehicle_deform.vmodc`, a build step in a private tree, not this analysis.
   Whether the triangle array can grow past 14 is UNKNOWN.
2. **Narrow the blanket to one plate** (spine or one fender): keeps every index and triangle,
   accepts less coverage than the donor. The coverage column is the price.
3. **Widen to the fender plates**: keeps the donor's width, floats over the troughs - the interior
   gap O-2 reports.

## Commands run for the result, verbatim

```
cd /e/Modding/JC3-Batmobile && uv run --with numpy python Tools/scripts/t_wld11b.py --check; echo "EXIT=$?"
json identical False  md identical False
areas 3  vertices 22  vertices pass O-1 16  areas pass all 0
CHECK FAIL
EXIT=1
```
(That failure was a real bug in my own tool: targets were appended in row-sorted order while triangle
indices refer to vertex order, so O-2/O-3 sampled the wrong points. Fixed by writing targets into a
`j -> xyz` map and emitting them in vertex order; the numbers above are after the fix.)

```
cd /e/Modding/JC3-Batmobile && uv run --with numpy python Tools/scripts/t_wld11b.py --write
areas 3  vertices 22  indices exist 22/22
  front_area             O-1 6/6  O-2 fail  O-3 pass  -> candidate fails: O-2
  front_signature_area   O-1 6/6  O-2 fail  O-3 pass  -> candidate fails: O-2
  main_area              O-1 4/10  O-2 fail  O-3 pass  -> candidate fails: O-1, O-2
band 0.0389..0.1578  donor interior max 0.075  digest 8129f08e7eda6a7e
EXIT=0
```

Array-capacity probe against the donor entity (read-only):

```
cd /e/Modding/JC3-Batmobile && uv run python - <<'PY'
import json,re
p=r"E:/Modding/_gamedata/JC3grab/entities/v0300_car_kensington_sportsmuscle__v0300_car_kensington_sportsmuscle_civilian_01.ee.json"
d=json.load(open(p,encoding="utf-8"))
sa=[m for m in d["modules"] if str(m.get("type"))=="StuntAreas"][0]
paths=[r["path"] for r in sa["rows"]]
for pat in ("vertices3D_local","triangle_indices","edge_validity","deform_points"):
    idx=set()
    for q in paths:
        m=re.match(r"stunt_areas\[(\d+)\]\.%s\[(\d+)\]$"%pat,q)
        if m: idx.add(int(m.group(2)))
    print(pat,"max index",max(idx) if idx else None,"count",len(idx))
PY
vertices3D_local max index 47 count 48
triangle_indices max index 41 count 42
edge_validity max index 15 count 16
deform_points max index 15 count 16
EXIT=0
```

Final run (capacity wired into the tool so `--check` guards it):

```
cd /e/Modding/JC3-Batmobile && uv run --with numpy python Tools/scripts/t_wld11b.py --write; echo "EXIT_WRITE=$?"; uv run --with numpy python Tools/scripts/t_wld11b.py --check; echo "EXIT_CHECK=$?"
areas 3  vertices 22  indices exist 22/22
  front_area             O-1 6/6  O-2 fail  O-3 pass  -> candidate fails: O-2
  front_signature_area   O-1 6/6  O-2 fail  O-3 pass  -> candidate fails: O-2
  main_area              O-1 4/10  O-2 fail  O-3 pass  -> candidate fails: O-1, O-2
band 0.0389..0.1578  donor interior max 0.075  digest 4824154d4755f1df
EXIT_WRITE=0
json identical True  md identical True
areas 3  vertices 22  vertices pass O-1 16  areas pass all 0
CHECK PASS
EXIT_CHECK=0
```

Exploratory rule probes (`tmp/freebuff/scratch/wld11b_*.py`) were used to choose R-1/R-2 and the
plate runs; they are not part of the result and every number in the md is recomputed by the tool.

## UNKNOWNs

1. **Which field the runtime trusts** - the stored `vertices3D_local` or a recomputation from
   `DeformPoints`. Tried: the entity, the geom sidecar, the shipped `.vmodc` list. Nowhere states it.
   Would be found in the runtime's stunt-area loader, which is not in the extracted data.
2. **Whether the area must be planar or convex** - the donor's own areas are neither exactly planar
   (0.2545 m residual) nor convex, so no constraint is proven; unproven means not imposed.
3. **Whether add-on parts sit above the hood/roof band** - needs the part transforms, not decoded here.
4. **How many triangles an area may carry** - 14 are stored; whether the array grows is not stated.
   Tried: raw `StuntAreas` row paths. Would be settled by decoding `sportsmuscle_stunt_areas.vmodc`.
5. **The "press A" binding** - the files confirm the three areas cover hood + shell; they do not
   contain a key binding. Tried: the entity and the interaction research from T-WLD11.

# Body-decal texture look — the §3.2 five-minute experiment

STATUS: done — the texture was converted, opened and measured. **Verdict: TEXTURE-BOUND-FIX.** The sheet holds
two large light-grey chevrons plus stencil lettering, so the chevrons are a texture and the fix is a binding.
The UV half is **UNKNOWN**: the per-face UVs are not recorded and the mesh export they would come from is absent.

Deliverable written: `Working/Appearance/DECAL_FINDING.md` (verdict line + evidence + owner file).
Evidence images: `Working/Appearance/diag/body_decals_D_1024.png` (42,277 B),
`Working/Appearance/diag/body_decals_D_mask.png` (6,291 B).

## 1. The experiment the plan asked for

`tmp/freebuff/reports/paint-gunmetal-reference-plan.md` §3.2:

> "The one 5-minute experiment that settles it: open `Batmobile_V3_Body_Decals_D` (the `.tga` in the grab's
> texture dump) and look at it. If it contains white `>` shapes on alpha, the chevrons are a texture and the fix
> is a binding, not geometry; if it is noise/flat, the chevrons are pure geometry…"

## 2. What was found

| question | answer | evidence |
|---|---|---|
| does it hold white chevron shapes? | **yes** — two hard-edged wedges: an open ">" at native x 23–125 / y 11–140 (4,389 px) and a solid wedge at x 133–231 / y 17–133 (5,799 px) | blob table, run log below; visible in the PNG |
| on which alpha? | **no alpha channel exists in this file** — TGA descriptor byte `0` (24-bit RGB); the shipped object is 1024² **PF_DXT1** (`TEXTURES.md:323`), also alphaless; the cut-out is the material's `OpacityMask`, unconnected in all four packages (`MATERIALS.md:17,66,105,152`) | TGA header `0 0 10 … 24 0`; TEXTURES/MATERIALS rows |
| at what pixel bounds? | ink (luma ≥ 200) 15,372 px = **23.46 %**, bbox native **x[4,247] y[11,249]**; the two chevrons alone are the top third | run log |
| noise or flat? | **neither** — 26 blobs ≥ 20 px, straight edges, a framed warning plate, lettering and an "MK 2" label | 32×32 occupancy print, PNG |
| what else is on the sheet | "WARNING" plate (198×53 native), "SOH: L3314113191514", "PATRIOT" + Batmobile silhouette (44×30), three "MK 2" glyphs on the right edge | PNG, blob boxes |

Tone: 544 distinct RGB, luma mean 59.4, max saturation 9 → neutral grey; ink peaks at ≈200–230, with only 10 px
at luma ≥ 250. So the shapes are mask-white, not pure 255 — consistent with a decal *mask* sheet.

## 3. The 58 faces of slot 8 — why the UV answer is UNKNOWN

| source the brief named | what it actually contains |
|---|---|
| `SLOTS.md:33` / `SLOTS.json` index 8 | `Batmobile_V3_TEXTURES_Body_Decals`, Material/master, **`textures: {}`**, **58 LOD0 faces**, part `body` — no UV field |
| `MESHES.md` | per-slot **face counts** per LOD; `grep -i uv` → **0 hits**; the string `decal` → 0 hits |
| `E:/Modding/ArkhamKnight/_grab/meshes` | **absent (0 entries)** — the umodel export `MESHES.md` names as its geometry source is not on this machine's disk |

So the UV box of those 58 faces is not derivable from the repo. The closing command (recorded in
`DECAL_FINDING.md`): export the mesh with `umodel -lods`, take every LOD0 face with material index 8, and compare
its UV bbox with chevron A `x[92,500] y[44,560]` and chevron B `x[532,924] y[68,532]` in 1024² space.

Why it matters, measured: the chevrons live in the top half of the sheet while the WARNING plate runs to
y 249/256. A UV box confined to the top band paints chevrons; a box spanning the sheet also paints "WARNING".

## 4. Owner file for the fix

**`Tools/scripts/factors.py`** — the `textures["s0"]` binding, or the `support.SupportDecals` /
`static.Decal*` block if the decal route is used; output regenerated into `Working/Appearance/build/factors.json`.
This is the file `paint-gunmetal-reference-plan.md` §5 row C4 names. Nothing was built (brief: build nothing).

## 5. Commands run, verbatim

```
$ stat -c '%n %s bytes' Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Body_Decals_D.tga
Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Body_Decals_D.tga 43586 bytes
$ od -An -tu1 -N 18 …/Batmobile_V3_Body_Decals_D.tga
   0   0  10   0   0   0   0   0   0   0   0   0   0   1   0   1
  24   0

$ uv run --with pillow --with numpy python tmp/freebuff/scratch/appearance/decal_look.py
file         Working/Appearance/grab/Playable_Batmobile_SF/Texture2D/Batmobile_V3_Body_Decals_D.tga 43586 B
size/mode    (256, 256) RGB bands= ('R', 'G', 'B')
unique RGB  544   luma min/mean/max 0/59.4/255
mean saturation 0.7   max saturation 9
luma>=250      10 px ( 0.02%)  bbox x[12,228] y[168,222]
luma>=200   15372 px (23.46%)  bbox x[4,247] y[11,249]
luma>=128   18025 px (27.50%)  bbox x[4,248] y[10,249]
blobs >=20px 26   largest 8 (px, x0,y0,x1,y1):
    (5799, 133, 17, 231, 133) size 99x117
    (4389, 23, 11, 125, 140) size 103x130
    (940, 4, 197, 201, 249) size 198x53
    (840, 168, 156, 211, 185) size 44x30
    (599, 123, 202, 175, 219) size 53x18
    (382, 224, 118, 247, 145) size 24x28
    (196, 224, 157, 247, 174) size 24x18
    (195, 224, 216, 247, 235) size 24x20

bright mask, 32x32 cells (# >=25% bright, + >0, . empty):
   ................................
   .........+......................
   ........+#......+############...
   ........##+......###########+...
   .......+###......###########+...
   .......####+.....+##########....
   .......#####......#########+....
   ......######+.....+########.....
   ......#######......########.....
   .....+###+###......#######......
   .....###+.###+.....+######......
   ....+###..+###......#####+......
   ....####...###+.....+####.......
   ....###....####......###+.......
   ...+###.....###......+##....+...
   ...###+.....####......##....###.
   ..+###......+###......#.....###.
   ...+#+.......##.............###.
   .............................++.
   ..+++++#+++++++......##..++.#+..
   #+#############......#####+.###.
   ..++#+#+#+#+++#.++++.######.##+.
   ..+++.++++++++++.#+++######.....
   ..+++.++.+++++++.....++.........
   +########################+..++..
   +####+######+##.+###.....#..+#..
   +######+##############...#......
   +#+#+#+++##++#++##++##...#..#+#.
   +.+.++++++.+.............#..###.
   ++++++++++++++++#+++.++++#..++#.
   +++..++.+++++..++++....+.#......
   +########################+......

wrote Working/Appearance/diag\body_decals_D_1024.png 42277 B
wrote Working/Appearance/diag\body_decals_D_mask.png 6291 B
```

Both PNGs were opened for visual inspection: the sheet reads as two large chevrons, a "WARNING" plate with
"SOH: L3314113191514", a "PATRIOT" mark with the Batmobile silhouette, and a vertical "MK 2" on the right edge.

## 6. UNKNOWNs

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | UV bbox of the 58 slot-8 faces, and whether it lands on the chevrons | `SLOTS.md`, `SLOTS.json`, `MESHES.md` (no UV field anywhere), `E:/Modding/ArkhamKnight/_grab/meshes` (absent) | `umodel -lods` export, then per-face UV bbox for material index 8 |
| U2 | whether the shipped 1024² DXT1 differs from this 256² export in content (the export is a quarter-size copy) | the TGA header says 256×256; `TEXTURES.md` says 1024×1024 | the `.dds`/`.ddsc` inside the package, or a 1024 export |
| U3 | which of the 26 shapes the 58 faces are actually meant to draw (all chevrons, or one arrow per flank) | not answerable without U1 | U1 |
| U4 | whether the decal route (`SupportDecals` / `Decal1..4Color`) or the `s0` route is the right carrier in JC3 | both are named in the plan §3.2/§5; neither was built (build nothing) | a build card for C4 |

## 7. Change record

- **Intended change:** add a diagnostic look (PNG + measurements) for `Batmobile_V3_Body_Decals_D` and record the
  verdict; no build, no game data touched.
- **Files written:** `Working/Appearance/DECAL_FINDING.md`, `Working/Appearance/diag/body_decals_D_1024.png`,
  `Working/Appearance/diag/body_decals_D_mask.png`, `tmp/freebuff/scratch/appearance/decal_look.py`, this report.
- **Why these files:** the brief names the finding file and the diag directory; the script is scratch per
  project rules.
- **Revert:** delete the five files listed above. Nothing else was modified.

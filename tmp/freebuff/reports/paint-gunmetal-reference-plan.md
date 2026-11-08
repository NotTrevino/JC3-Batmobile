# APP-2 against the operator's screenshot — what the reference shows, what RC4 carries, and the five acceptance checks

**STATUS: report only.** Nothing was built, no texture written, no game launched, and neither `factors.py` nor any
`Builds/` file was modified. The operator's screenshot is described in words in the brief; **no pixel values from it
were supplied**, so every threshold below is *relative* (a comparison inside the frame), not an absolute RGB target.

Read for this report: `Research/BatmobileGrab/SLOTS.md` (LOD0 slot table), `MATERIALS.md` (expression slots per
master), `Working/Appearance/progress.md`, the RC4-appearance factor record `Working/Appearance/build/coverage.md`
(the body section at line 420, the decal section at 510) and `Working/Appearance/build/factors.json`,
`Tools/scripts/factors.py`, `Research/JC3Grab/TINT_WRITE.md`, `RESET_FINDINGS.md` §2.

---

## 1. The reference, resolved into five claims

| # | the operator sees | what that is, in material terms |
|---|---|---|
| R1 | dark gunmetal grey, not pure black | a low-luma **neutral**: all three channels within a few levels of each other |
| R2 | satin/metallic sheen with bright specular **streaks along panel edges** | a clearcoat lobe catching the panel's edge normal, over a mid gloss base |
| R3 | darker carbon-fibre-weave **inset panels** | a second material channel: lower luma **and** a tiling high-frequency pattern |
| R4 | white **chevron (">") decals** on the body | a decal layer with its own texture and opacity, not the paint colour |
| R5 | **blue-glowing cockpit screens**, visible through the canopy | emissive interior block + a canopy whose alpha still passes light |

R2 and R3 are the two that the current block cannot express at all, for reasons in the bytes (§3). R1 is a
channel-balance error that is fully explained by arithmetic (§2). R5 is one value away. R4 is the only one that needs a
new texture binding.

Rain beading is in the reference too, but it is not one of the five checks: every rain/wetness factor is disposed
`engine-global` to JC3's weather system (`Mud_*`/`Rain_*` → `SupportDirt 0`, `DirtColor` recorded; `progress.md`
"mud and dirt default (D1)"). Judging beading in a look session grades JC3's weather, not this transfer.

---

## 2. Why the body reads violet, in one chain of numbers

`Working/Appearance/build/coverage.md:501` (body block, `s0`):

```
s0  solid [0.5137254901960784, 0.49019607843137253, 0.5254901960784314]   -> 0x83 0x7d 0x86  (131,125,134)
    source: generated from bmak:Material0_BaseColour (x4.0 -> sRGB, ALB-2)
```

Reproducing that byte triple from the BmAK parameters named in the same section shows where the blue comes from:

| step | R | G | B | factors.py |
|---|---|---|---|---|
| `Material0_BaseColour` (linear, master) | 0.025787 | 0.025787 | **0.030000** | `cl()` |
| × `Diffuse_Adjust` `[2.2, 2.0, 2.0]` | 0.056731 | 0.051573 | 0.060000 | `cl()` |
| × `ALBEDO_GAIN` 4.0 | 0.226924 | 0.206292 | 0.240000 | `s0` solid |
| `srgb8()` → 8-bit | 131 | 125 | 134 | `srgb8()` |

So the violet is **not** an encoding bug: blue is genuinely 16 % above green in linear terms (0.240 vs 0.206), because
the authored colour has `B = 0.03` against `R = G = 0.0258`, and `Diffuse_Adjust` then multiplies R by 2.2 but B by
only 2.0 — the two imbalances add instead of cancelling. HSV on (131,125,134) is hue ≈ 280°, saturation ≈ 6.7 %: a
desaturated violet, which is exactly the "white-violet" in `RESET_FINDINGS.md` §2.

**Consequence for the plan:** channel *neutrality* is arithmetic and can be fixed without solving the bridge that
`RESET_FINDINGS.md` §2 says is unsolved. Getting grey needs the three linear channels equalised **before** the gain
(uniform `Diffuse_Adjust`, `B` set to the `R`/`G` value); the gain then only sets lightness, and picking its value is
still the open judgement, not a computation.

---

## 3. Does RC4 carry the carbon-weave inset and the chevron decal?

### 3.1 The carbon weave — no texture in the body chain, a colour parameter on the *wrong* master

| candidate | where it exists | is it in the body block RC4 builds? |
|---|---|---|
| `Batmobile_Microdetail`, `Batmobile_Micropattern_A/B/C`, `*_A_Normal`, `neutral_normal` | `SLOTS.md` slot 3 and 5 texture rows; `TEXTURES.md` | **No.** Every one is disposed `no-jc3-equivalent` — "tiling micro-detail (no CarPaintMM detail slot; could be baked into s1)" — plan `bake (P1)` in `progress.md`. `coverage.md:420–445` lists all four as `no-jc3-equivalent`. |
| `Carbon_Colour` (vector), `EdgeMask_Colour_Carbon` (scalar) | `objects.jsonl` / `SKINS.md:543,547` — expression parameters of **`Batmobile_MK2_WheelArch_MAT`** and **`Batmobile_Jokerfied_V2_MAT`** | **No.** The body's chain is MIC → `Batmobile_V3_WheelArchs_NEW_MIC` → `Batmobile_Worn` (`coverage.md:421`); those two masters are the MK2 and Joker skins, not this one. `Carbon_Colour` does not appear anywhere in `Working/Appearance/build/factors.json`. |
| a carbon-weave **texture** | searched `Research/BatmobileGrab` for `carbon`/`weave`: the only hits are the parameter names above plus `Carbon_Colour` values in `SKINS.json` | **No such texture exists in the grab.** |

So there is no carbon-weave *image* to bind, and the dark-inset *colour* the MK2/Joker masters use is not on the V3
body chain. What the body does carry is the micro-detail textures at two tiling scales — `MicroDetail_size 15.0` and
`MicroDetail_Material3_Size 250.0` on the `WheelArchs` MIC (`coverage.md:436,437`) — which is the right kind of
signal for a weave and is currently thrown away.

### 3.2 The chevron decal — the material is built, the texture is not bound, decals are switched off

| fact | evidence |
|---|---|
| Slot 8 of LOD0 is `Batmobile_V3_TEXTURES_Body_Decals`, a **Material/master**, 58 faces, and its `textures` cell is **`—`** (no texture parameters on the material as instanced) | `Research/BatmobileGrab/SLOTS.md:33` |
| Its expression inputs `DiffuseColor` and `OpacityMask` are **unconnected** in all four packages | `MATERIALS.md:17,66,105,152` and the per-input table at 248–249 |
| A texture with exactly that name exists: `Batmobile_V3_Body_Decals_D`, 1024×1024, `PF_DXT1` | `TEXTURES.md:41,144,231,323` |
| RC4 includes the material, but its block has **no `JC3 slot` table at all** — nothing reached `s0`–`s3`; `SupportDecals 0.0`, `DecalCount/DecalWidth/Decal1..4Color/DecalBlend` all `0.0` | `Working/Appearance/build/coverage.md:510–549` |
| The switch that would draw it is off by policy, with a written reason | `factors.py` `put("support.SupportDecals", 0.0, "no livery decals")`, and every `static.Decal*` row: "BmAK has no livery-decal system; its decals are geometry" |

Reading those together: the chevrons in BmAK are **geometry** (58 faces carrying the decal material), not a livery
decal painted into the paint mask — which is why `factors.py` made the disposition it did. The build nevertheless
*has* the material and drops its texture, so even the 58 faces draw with no `s0`.

**The one 5-minute experiment that settles it:** open `Batmobile_V3_Body_Decals_D` (the `.tga` in the grab's texture
dump) and look at it. If it contains white ">" shapes on alpha, the chevrons are a texture and the fix is a binding,
not geometry; if it is noise/flat, the chevrons are pure geometry and need a mesh swap or a paint mask. Do this before
any RC5 pigment work — it decides whether R4 is one row or one build.

---

## 4. The five acceptance checks for the first look session

Frame each check the same way so the session is comparable: **noon, clear weather, camera 3–4 m from the flank, sun
behind the camera at ~30°**, plus one night frame for C5. Sample the same three body panels in every frame (front
wing, door skin, rear haunch) and exclude pixels inside a specular highlight.

| # | check | pass rule (measurable in the frame) | the CarPaintMM parameter that moves it | where it is set | value RC4 ships |
|---|---|---|---|---|---|
| **C1** | **hue reads grey, not violet** | on 3 panels × ≥200 px outside highlights: `(max−min)/max ≤ 0.04` **and** `B ≤ R`. Today's block is `0.067` with `B>R>G`, so it fails by construction | `s0`'s solid colour, i.e. the product `Material0_BaseColour × Diffuse_Adjust × ALBEDO_GAIN` through `srgb8()`; the tint fallback is `dynamic.TintColorR/G/B` | `factors.py` `cl()` / `srgb8()` / the `s0` solid branch; constants from `VALUES.json` (`paint.albedo_gain`, `paint.gloss_cap`) | `s0` = `[0.5137, 0.4902, 0.5255]` (131,125,134) |
| **C2** | **specular shows on the panel edges** | a continuous line along ≥60 % of one panel edge whose peak luma ≥ 1.6× the adjacent panel's diffuse luma, and a highlight that is *narrow* (falls to half within ≈1/8 of the panel width). A uniform brightening over the whole panel fails | `static.ClearCoat` (cb2[2]) first, then `static.SpecularGloss` (cb2[0].x, capped by `GLOSS_CAP`) and `static.Metallic` (cb2[1]) | `factors.py`: ClearCoat is set from the presence of `Normal_Map_Lacquer` only; gloss from `1 − roughness` capped at 0.45 | ClearCoat `[0,0,0,0]`, gloss `[0.45 ×4]`, metallic `[0,0,1,0]` |
| **C3** | **the insets are darker than the panels** | inset region luma ≤ 75 % of the adjacent panel, and a repeating pattern resolvable at ≤0.5 m (weave pitch visible, not a smooth gradient) | the channel split: `s2` PropertyMap selects channel N, then `static.SpecularGloss[N]`, `static.Metallic[N]`, `static.ClearCoat[N]`; the inset's colour arrives as `dynamic.TintColorG` or `TintColorB` (channels 1–3) | `factors.py` material-channel loop + the `s2`/`s3` fallback; tints from `Material1..3_BaseColour` × `Diffuse_Adjust` | `s2`/`s3` = `a00_dummy_black_mpm.ddsc` ("channels 1-3 are parameterised but the mask is the master's default → channel 0 everywhere"), so **every face is channel 0** and the near-black `Material1_Basecolour` `[0.01,0.01,0.01]` never appears |
| **C4** | **the chevrons are visible** | ≥1 white ">" on each flank, edges resolved at 1080p, orientation pointing rearward-up as in the reference; a chevron that only shows under specular fails | `support.SupportDecals` (cb2[19]) **and** `static.DecalCount`, `static.DecalWidth`, `static.Decal1Color..Decal4Color`, `static.DecalBlend` (cb2[8]–cb2[14]); alternatively a dedicated block whose `s0` is `Batmobile_V3_Body_Decals_D` | `factors.py` the `SUPPORT` loop and the `static.Decal*` block; texture binding is the `textures["s0"]` branch | `SupportDecals 0.0`; all `Decal*` `0.0`; `s0` unbound (§3.2) |
| **C5** | **the screens glow through the canopy** | night frame, camera outside: screen pixels ≥1.4× the surrounding interior luma **and** `B ≥ R+20`; the glow must be visible *through* the glass, not only with the canopy off | `static.Emissive` (cb2[3]) on the interior block, and the `Window` block's `t0` alpha × `Glass_Opacity` | `factors.py` `put("static.Emissive", [emis]*4, ...)`; glass alpha in the `Window` branch (`alpha_multiplier`) | seat block Emissive `[15.0 ×4]`; screen slot 12 (`Cockpit_Master_Flip_Data`, 100 faces) carries **no parameters**; canopy alpha multiplier 1.2 |

**Two of the five cannot pass as shipped**, and the report says so plainly rather than blaming the look: C1 fails on
the channel maths (§2), C3 fails because channel 0 is forced everywhere (§4 row C3), and C4 fails because the decal
layer is switched off and unbound (§3.2). C2 and C5 are single-value changes on blocks that already exist.

---

## 5. What each failing check needs, and the file that owns it

| check | change | owner file |
|---|---|---|
| C1 | equalise the three linear channels before the gain (`Diffuse_Adjust` uniform; `B` = `R`/`G` base), and re-derive the gain from the *reference's* panel luma instead of keeping 4.0 as a screenshot constant | `Tools/scripts/factors.py` (`cl`, `srgb8`, `s0` branch); values in `Research/BatmobileGrab/VALUES.json` via `grab_values.py` |
| C2 | set `ClearCoat` from *either* lacquer normal **or** a lacquered ramp (`Aniso_ramp_Lacquered` is in this chain and is currently ignored), and stop capping the clearcoat channel at the paint gloss — the cap was a MAT-1 fix for the base gloss | `Tools/scripts/factors.py` (ClearCoat `put`, `GLOSS_CAP` use) |
| C3 | recover a usable separation mask or synthesise one from the parameter set (the master's mask is the unnamed default), so channels 1–3 can be plastered; bake the weave into `s1` (`bake P1`) so the inset has a pattern, not just a darker luma | `Tools/scripts/factors.py` (`s2`/`s3` fallback), `Tools/scripts/appearance_bake.py` (`microdetail_bake`) |
| C4 | decide texture-vs-geometry with the §3.2 experiment, then either bind `Batmobile_V3_Body_Decals_D` as a decal/`s0` or accept the geometry and colour it | `Tools/scripts/factors.py` (`textures["s0"]`, `SupportDecals`), `Working/Appearance/build/factors.json` (regenerated) |
| C5 | give the screen slot an emissive instead of leaving slot 12 parameterless, and keep the canopy alpha above the point where m_Emissive is clipped | `Tools/scripts/factors.py` (`static.Emissive`, Window `alpha_multiplier`) |

The palette (`Research/JC3Grab/TINT_WRITE.md`) is **not** the lever for any of the five: it writes
`Palette.tints[i].tint_r` (four float32 at `Tint+20`, stride 80) and no build has ever written a value — every build
ships the donor's `White` record `0.05` and relies on the `.epe` `CCar.palette` hash. Its one relevant note: a tint
edit is layout-stable (4 bytes at `0x74`, re-import identical), so if C1 ends up wanting a *tint* rather than an
albedo edit, that is the cheapest carrier to try — but the `.epe` pointer and the shader's `cb6` binding are still
UNKNOWN (`TINT_WRITE.md` §5).

---

## 6. UNKNOWNs

1. **Whether `Batmobile_V3_Body_Decals_D` contains the chevrons.** The name matches the slot, the slot binds no
   texture, and the material's inputs are unconnected — three facts that fit either answer. The TXA look in §3.2
   settles it.
2. **Whether the 58 faces at slot 8 are the chevrons or a separate decal quad.** 58 faces is small for a full-body
   livery and plausible for a few arrows; the mesh split is in `MESHES.md`, not re-derived here.
3. **Which block the blue cockpit screens actually are.** Candidates: slot 11 `BatmobileV3_Cockpit_Seat`
   (`Emissive=Int_Cockpit_E`, `EmissiveMultiply 15.0`), slot 5 `Batmobile_V3_Emissive`
   (`Emissive_Map=Wheel_E`, separation mask `Wheel_Lights_M`), and slot 12 `Cockpit_Master_Flip_Data` (100 faces,
   no parameters). No grab file says which one a player sees lit.
4. **Whether the reference's grey is reachable without the bridge.** Equalising the channels removes the violet; the
   *lightness* still depends on a gain chosen against a screenshot, which `RESET_FINDINGS.md` §2 calls unknown. C1 is
   therefore a "not violet" check, not a "matches the reference exactly" check.
5. **The reference's own numbers.** The brief describes the screenshot; no file path or pixel sample was given, so no
   absolute RGB or luma target can be quoted — every threshold above is intra-frame and relative. A measured sample
   from the screenshot would turn C1/C2/C3 from relative to absolute.
6. **Whether rain beading can be judged at all** in a session where JC3 controls the weather (D8), and whether the
   operator's mud backdrop corresponds to a JC3 surface state.

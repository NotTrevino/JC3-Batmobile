"""appearance_plan.py - T-21: every appearance component that is not fully transferred gets a plan.

The card (`GRAB_BACKLOG.md` §7, `#### T-21`) asks for one thing above all:

    Done: 0 unclassified components.

`appearance_progress.py` reports 339 components over four classes (geometry, materials, textures,
factors): 167 transferred, 36 partial, 136 excluded, 0 missing. The 172 that are not fully
transferred are the card's subject. This tool gives each one exactly one of three actions and
fails if any component, or any rule, is left over:

  bake    the value can be carried by baking a BmAK source texture into a JC3 sampler that the
          block already has (s0 albedo / s1 normal) - this is POL-2, the micro-detail group
  route   the value is carriable, but by another carrier the build already writes: a `Window`
          block instead of `CarPaintMM`, an emissive value on `static.Emissive`, or the `CarLight`
          block / lights module that T-18 and B-03 own
  drop    no carrier exists on the JC3 side; the value is dropped and the reason is stated (an
          engine-global system owns it, the source file is absent, it is an editor helper, the
          feature does not exist in JC3)

Inputs, all of them already on disk (nothing is hand-typed, every number below is re-derived):

  `Working/Appearance/progress.json`          the 339 components with status + reason (T-21 `In:`)
  `Research/BatmobileGrab/SLOTS.json`         the 19 material slots, their faces (T-21 `In:`)
  `Research/BatmobileGrab/VARIANTS.md`        the skin material deltas, D-5 (T-21 `In:`)
  `Working/Appearance/build_bud1/factors.json`  the block type + bound slots per material, i.e. the
                                              file the progress numbers were measured from

The reason text of each gap comes from `factors.py`'s disposition table (the tool that produced
`factors.json`), so a rule here is a decision about a disposition, not a re-reading of the BmAK
material. A change to either side breaks the pairing on purpose: an unmapped reason string makes
the component `unclassified` and `--check` fails.

Outputs:

  `Working/Appearance/APPEARANCE_PLAN.md`   the plan, generated
  `Working/Appearance/appearance_plan.json` the same rows as a machine record

Usage:
  python Tools/scripts/appearance_plan.py --write
  python Tools/scripts/appearance_plan.py --check
  python Tools/scripts/appearance_plan.py --show Batmobile_V3_Int_Cockpit_S
"""
import argparse
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROGRESS = os.path.join(ROOT, "Working", "Appearance", "progress.json")
SLOTS = os.path.join(ROOT, "Research", "BatmobileGrab", "SLOTS.json")
VARIANTS = os.path.join(ROOT, "Research", "BatmobileGrab", "VARIANTS.md")
BUILD = os.path.join(ROOT, "Working", "Appearance", "build_bud1")
FACTORS = os.path.join(BUILD, "factors.json")
MD = os.path.join(ROOT, "Working", "Appearance", "APPEARANCE_PLAN.md")
JS = os.path.join(ROOT, "Working", "Appearance", "appearance_plan.json")

# POL-1 (MODDING_PLAN.md phase 6, item 6: "Interior, cockpit, seat, power cell") — the materials
# that make up the visible interior. The names are the ones `SLOTS.json` carries as slots 10, 11,
# 12, 14, 15, 16; G1-19 (`COCKPIT.md`) fixes seat = slot 11 and dashboard = slot 10. The choice of
# *which* slots are interior is the plan's, so it is written here once and validated against the
# slot file at run time (a name that is not a slot fails the run).
INTERIOR = [
    "Batmobile_V3_Cockpit_MIC",      # slot 10 - cockpit / dashboard shell (G1-19: dash)
    "BatmobileV3_Cockpit_Seat",      # slot 11 - seat                            (G1-19: seat)
    "Cockpit_Master_Flip_Data",      # slot 12 - cockpit flip/overlay data
    "Stagg_Battery_01_MAT",          # slot 14 - power-cell battery body
    "Stagg_Battery_Energy_01_MAT",   # slot 15 - power-cell energy strip
    "Nimbus_Power_Cell_Mat",         # slot 16 - power-cell window
]

# The five surface reviews folded into the plan (T-21 closing pass). One entry per report: the
# verdict is the report's own count, the numbers and carrier paths are from its decoded tables.
# `render` prints one section per entry and `appearance_progress.py` prints the same entry under
# `## surfaces`, so the plan and the progress table cannot drift apart.
CROSS = [
    dict(key="cockpit", title="Interior and cockpit (POL-1)",
         report="tmp/freebuff/reports/app-cockpit-interior-materials.md",
         verdict="11 of 15 interior components have no faithful carrier",
         numbers="Metalicity 0.9000; EmissiveMultiply 15.0 x a 1024x1024 mask; seat "
                 "Reflectivity_Multiplier 1.2; ClearCoat [1,1,1,1]; Int_Cockpit_D/N/M and "
                 "Int_Cockpit_S 4096x4096 DXT1 (S has a dead R channel); two Colour_Ramp_Map "
                 "lookups (64x512, the lacquered one missing on disk); Aniso_ramp_Lacquered; "
                 "cockpit 27,334 faces, seat 13,014, screen 100 (0.3188 x 0.1512 m); yoke absent",
         carriers="`s0` DiffuseMap, `s1` NormalMap, `s3` TintMap (the separation mask), "
                  "`m_Metallic` `cb2[1]`, `m_ClearCoat` `cb2[2]`, `m_Emissive` `cb2[3]`, "
                  "`m_SpecularGloss` `cb2[0].x`, `SupportSoftTint` `cb2[19].z`, the `Window` "
                  "block for the canopy, `VehicleParts.damage_type = Land_Steering_Wheel`",
         rows=[
             ("`Batmobile_V3_Cockpit_MIC` Metalicity", "0.9000",
              "`m_Metallic` (`cb2[1]`)", "carried"),
             ("`Material_Separation_Mask` = `Int_Cockpit_M`", "4096x4096 DXT1",
              "`s3` TintMap (`t3`)", "carried"),
             ("seat albedo + normal (`Int_Cockpit_D` / `_N`)", "4096x4096 DXT1",
              "`s0` DiffuseMap / `s1` NormalMap", "carried"),
             ("`ClearCoat`", "[1,1,1,1]", "`m_ClearCoat` (`cb2[2]`)", "carried"),
             ("seat `Reflectivity_Multiplier`", "1.2",
              "`m_Metallic` only when no Metalicity and value > 0.5 (D2)",
              "partial - JC3`s F0 is fixed"),
             ("`EmissiveMultiply` x `Int_Cockpit_E`", "15.0 x 1024x1024 mask",
              "`m_Emissive` (`cb2[3]`) + `SupportSoftTint` (`cb2[19].z`)",
              "mask baked into `s0`; no emissive-mask channel decoded"),
             ("`Int_Cockpit_S`", "4096x4096 DXT1, R channel dead",
              "`m_SpecularGloss` (`cb2[0].x`) as the mean, then `s2`",
              "per-pixel lost until the `s2` channel probe"),
             ("`Colour_Ramp_Map` = `Batman_BM3_V2_Lacquered_Underlayer_Ramp`, "
              "`Batman_BM3_V2_Leather_Ramp`", "64x512 lookup",
              "none - bake into `s0` with `cb6[0..2]` at 1,1,1",
              "no ramp sampler; one ramp file is missing on disk (D10)"),
             ("`Aniso_ramp_Lacquered`", "texture",
              "none - bake into `s1` as a directional smear",
              "no anisotropy member in any of the 961 headers (D4)"),
             ("centre screen `Cockpit_Master_Flip_Data`", "100 faces, no texture in BmAK",
              "`m_Emissive` or a `CarLight` block",
              "author a 0.3188 x 0.1512 m emissive texture"),
             ("yoke / steering control", "absent (4 faces in the hand box, |x|<0.17)",
              "`VehicleParts.parts[].damage_type = Land_Steering_Wheel`",
              "author geometry; grip pose from the `Driver` socket"),
         ]),
    dict(key="glass", title="Glass and canopy",
         report="tmp/freebuff/reports/app-glass-layers.md",
         verdict="9 of 13 glass rows are not faithful and the master carries nothing",
         numbers="`Batmobile_Glass` 8/8 inputs unconnected in all four packages; tint "
                 "[0.02579, 0.02579, 0.03]; Glass_Opacity 1.2; Glass_Reflectivity 0.8; "
                 "Glass_Roughness 1.1; glass_smudges 0.2; V3_Glass_A/N 4096x4096 DXT1; frame "
                 "mask V2_GLASS_MASK 1024x512; canopy one slot, 3,532 faces, open by 72.481 cm",
         carriers="`t0` RGB x `TintPower`, `t0` alpha (`Alpha` / `MinAlpha`), `SpecGloss` and "
                  "`SpecFresnel` `cb1[0]`, `DiffuseRougness` `cb1[8]`, `t3` property channels, "
                  "JC3`s `t4`/`t5` crack maps + `WindowContactPoints[32]`",
         rows=[
             ("master inputs (`DiffuseColor` .. `MetalMask`)", "8/8 unconnected",
              "nothing to carry - the MIC and three textures are the look", "decoded"),
             ("tint", "[0.02579, 0.02579, 0.03]", "`t0` RGB x `TintPower`",
              "no tint vector; bake into the diffuse"),
             ("`Glass_Opacity`", "1.2", "`Alpha` / `MinAlpha` / `t0` alpha",
              "no per-block write; repack `V3_Glass_A` into `t0` alpha"),
             ("`Glass_Reflectivity`", "0.8", "`SpecGloss`, `SpecFresnel` (`cb1[0]`)",
              "one-to-two split, UNKNOWN"),
             ("`Glass_Roughness`", "1.1", "`DiffuseRougness` (`cb1[8]`)",
              "value bridge underived"),
             ("`V3_Glass_S` R/G", "per-pixel", "`t3` property channels",
              "channel map undecoded - needs the 4-block probe"),
             ("`V3_Glass_A`", "4096x4096 DXT1", "`t0` alpha", "same data, other slot; repack"),
             ("`glass_smudges`", "0.2",
              "none for glass; nearest `t40` RainOccluderTexture",
              "not equal - bake as a dirt layer"),
             ("frame mask `V2_GLASS_MASK`", "1024x512 DXT1, unbound", "none",
              "unidentified; bake as an opaque border if it is the frame"),
             ("cracking", "absent in BmAK",
              "`t4`/`t5` crack maps + `WindowContactPoints[32]` + `DamageMaskWeight` / "
              "`DamageRampWeight`", "JC3 has more - nothing to carry"),
             ("canopy open + closed", "one MIC, one slot", "two `Window` blocks (or a `Hood` part)",
              "JC3 canopy is a material/part switch"),
         ]),
    dict(key="wheels", title="Wheels and tyres",
         report="tmp/freebuff/reports/app-wheels-and-tyres.md",
         verdict="7 of 14 wheel components carry a value no JC3 member reproduces",
         numbers="tyre 1.3652-1.3657 m OD, 0.7314-0.7325 m wide; rim (`Fan`) 1.0254 m; "
                 "Wheel_V2_R / Tyre_V2_R / BRAKE_DISC_R per-pixel; scalars 0.6088 + 0.3561 "
                 "(rim), 0.052 (tyre), 0.9586 + 0.431 (disc); tyre EMP 0.0 / 350; tread "
                 "6,700 front vs 7,564 rear faces; 10 mud/rain scalars",
         carriers="`land_global.*_wheels.radius` / `.width` / `.rim_radius`, `s0`/`s1` on each "
                  "`CarPaintMM` wheel block, `m_SpecularGloss`, `m_Metallic`, `m_Emissive`, the "
                  "lights `vmodc` + `CarLight` rows, `mshswap` for a bare rim",
         rows=[
             ("tyre OD / width", "1.3652-1.3657 m / 0.7314-0.7325 m",
              "`land_global.*_wheels.radius` 0.68275 / 0.68265, `.width` 0.73195 / 0.73165",
              "none - <= 0.55 mm per corner, spin axis +x"),
             ("rim diameter (`Fan`)", "1.0254 m", "`..._wheels.rim_radius` 0.539",
              "26 mm quantity mismatch - decision, not derivation"),
             ("`Wheel_V2_R`, `Tyre_V2_R`, `BRAKE_DISC_R`", "3 per-pixel maps",
              "`m_SpecularGloss` 0.6088 / 0.052 / 0.9586, `m_Metallic` 0.3561 / 0.431",
              "per-pixel lost - none of the three `_R` is shipped"),
             ("`Discbreak_front` / `Discbreak_back`", "2 emissive scalars",
              "`m_Emissive`, one per block", "needs a block split (D3)"),
             ("hub lamps + 4 split flares", "6 light rows",
              "lights `vmodc` + `CarLight` block (T-L13, T-L20, T-L31..34)",
              "4 flare rows contradictory: manifest mapped, COMPROMISES_T out"),
             ("tyre EMP glow", "`EMP` 0.0, `EMP_Emissive_Multiplier` 350", "none",
              "dropped (D14) - story effect"),
             ("mud / wet on tyre and rim", "10 scalars", "none - JC3 dirt is dynamic",
              "dropped (D1/D8); the dirt path is now written explicitly, see section 10"),
             ("wheel-lights material (`Wheel_E`, `Wheel_Lights_M/N`)", "3 textures",
              "`s1`, `s2`, `s3` + `m_Emissive`", "partial - emissive mask channel undecoded"),
         ]),
    dict(key="mud", title="Mud and dirt default (D1)",
         report="tmp/freebuff/reports/app-mud-and-dirt-default.md",
         verdict="the clean state is a written value, not an omission; 4 mud scalars have no "
                 "member",
         numbers="Mud_Opacity 50.0 body / 2.0 arch / 30 tyre / 1 wheel / 0 disc (master 100.0); "
                 "Mud2_Opacity 2.0 / 0.65 / 1.5 / 2.0 / 1.0; Mud_Edges_Opacity 100.0 / 4.0 / "
                 "1.2 / 0.5 / 0.2; Mud_WetStreaks absent on the body, 1.0 / 1.0 / 1.2 on "
                 "tyre/wheel/disc; Mud_Density 0.11; Mud_Colour [0.2652, 0.1433, 0.06887]",
         carriers="`m_DirtParams` (`cb2[5]`, +80), `m_DirtBlend` (`cb2[6]`, +96), "
                  "`m_DirtColor` (`cb2[7]`, +112), `SupportDirt` (`cb2[19].y`, +308), the "
                  "shared `s6` `vehicle_dirt_msk.ddsc`, the block dirt flag",
         rows=[
             ("`Mud_Opacity`, `Mud2_Opacity`, `Mud_Edges_Opacity` (body / arch / tyre / wheel "
              "/ disc)", "50 / 2 / 100; 2.0 / 0.65 / 4.0; 30 / 1.5 / 1.2; 1 / 2 / 0.5; "
              "0 / 1 / 0.2",
              "`m_DirtParams` (`cb2[5]`) + `m_DirtBlend` (`cb2[6]`) + `SupportDirt` "
              "(`cb2[19].y`)",
              "no per-chapter animation - publish clean and dirty states"),
             ("`Mud_Colour`", "[0.2652, 0.1433, 0.06887, 1]",
              "`m_DirtColor` (`cb2[7]`)",
              "equals JC3`s own (0.2652, 0.1433, 0.0689) - carried, not tuned"),
             ("`Mud2_Colour`", "[0.1492, 0.05605, 0.01548, 1]",
              "`m_DirtColor`, one per block", "the second layer has no member"),
             ("`Mud_WetStreaks`, `Mud_Roughness`, `Mud_Density`, `Mud_Reflectivity`",
              "1.0 / 1.0 / 1.2; 0.2; 0.11; -",
              "none - at best channels of `s6 vehicle_dirt_msk`",
              "no member; needs an authored mask, not a tune"),
             ("`DirtColor`", "does not exist in BmAK (0 hits over 206 systems)",
              "`m_DirtColor` exists in JC3",
              "UNKNOWN/absent - the brief`s parameter name was wrong"),
             ("`Damage_Dirt_Colour`", "[0.41573, 0.389493, 0.33165, 1]",
              "`m_DamageColor` / `cb2[15..17]`", "separate JC3 path - decide per block"),
             ("clean default", "SupportDirt 1.0 on 76 and 0.0 on 323 of 399 blocks; the donor "
              "`sportsmuscle_body_lod1` has 0.0 on all 16 `CarPaintMM` blocks",
              "write `SupportDirt` 0.0, `m_DirtParams` (0,0,0,0), `m_DirtBlend` (0,0,0,0), "
              "`m_DirtColor` (0.2652, 0.1433, 0.0689, 1)",
              "clean by authored value, not by omission (D1)"),
         ]),
    dict(key="skins", title="Skins and variants (D-5)",
         report="tmp/freebuff/reports/app-skins-and-variants.md",
         verdict="7 of 11 looks have no carrier today - 4 need a drop entry, 3 a mesh/part swap",
         numbers="four full vehicles plus 3 damage states and 4 upgrade visuals = 11 looks; "
                 "V2 -> Joker 61 materials, 54 textures, 40 bones; Joker 26 materials / 31 "
                 "textures on a 78 / 92 baseline; Runhouse 13 / 7; SimulationModel 2,328 B, "
                 "37 tags, 0 differing; R9 texture wall 7,065 KB per entity",
         carriers="one Rebel Drop entry per skin (same `.rbm` + block rules re-run), `mshswap` "
                  "for the damage states, the `Burnout` material path for fire, a texture swap "
                  "on slots 16 / 17 for the upgrade visuals",
         rows=[
             ("V2 (reference)", "1 of 11 looks", "the RC2 single tree", "carried"),
             ("V2 -> Joker", "61 materials, 54 textures, 40 bones differ",
              "a second drop entry and block set - no palette tint exists",
              "cannot become a tint"),
             ("MK2", "replaces the body and wheel materials",
              "a second Rebel Drop entry, the same rules re-run", "not built"),
             ("upgrade visuals", "`Missile_Upgrade_D/N`, `Power_Cell_INT_D`, "
              "`Nimbus_Power_Cell_N`, `Stagg_Battery_01_D/N`",
              "`s0` / `s1` on slots 16 and 17",
              "half-carried - every `_S` dropped by D3, no `_GLOW` shipped"),
             ("damaged story states (`Batmobile_V3_Destroyed`, `Batmobile_V2_Fire`)",
              "separate meshes", "`mshswap`, the mechanism the wheels already use",
              "no material route exists"),
             ("`SimulationModel` + shared weapons",
              "0 differing tags, 0 differing weapon fields",
              "no new physics or weapon tunes per skin",
              "a skin costs meshes, materials and textures only"),
             ("budget", "R9 7,065 KB per entity", "per-skin measurement",
              "UNMEASURED - a skin may not fit"),
         ]),
]

# Default actions, per reason a component is not fully transferred. `why` is matched exactly
# against the reason `appearance_progress.py` recorded, which is `factors.py`'s disposition target.
RULES = [
    # ---------------------------------------------------------------- micro-detail: POL-2 bake
    dict(id="P1", cls="textures", status="excluded",
         why="tiling micro-detail (no CarPaintMM detail slot; could be baked into s1)",
         action="bake", pol="POL-2", target="s1 Normal (and s0 where the pattern is albedo detail)",
         owner="appearance_pipeline.py -> bat_assemble.py texture convert",
         note="micro-detail has no CarPaintMM sampler of its own; baking it into the channel "
              "normal keeps the tiled pattern at no extra block or texture slot"),
    dict(id="P2", cls="factors", status="excluded", why="micro-detail tiling size",
         action="bake", pol="POL-2", target="s1 Normal UV scale at bake time",
         owner="appearance_pipeline.py -> bat_assemble.py texture convert",
         note="the tiling size is the UV multiplier the bake needs; it has no block input, so it "
              "is consumed by the bake rather than written"),
    dict(id="P3", cls="factors", status="excluded", why="micro-detail -> roughness modulation",
         action="bake", pol="POL-2", target="gloss vector modulated by the baked detail",
         owner="appearance_pipeline.py -> bat_assemble.py texture convert",
         note="per-pixel roughness modulation cannot be stored, but its mean and its pattern can "
              "be folded into the baked normal's effect on the gloss vector"),
    # ---------------------------------------------------------------- routed carriers
    dict(id="R1", cls="factors", status="excluded",
         why="JC3 lights module (CarLight blocks + lights.vmodc)",
         action="route", pol="", target="CarLight RBM block + `*_lights.vmodc` entry",
         owner="T-18 (values) -> B-03 (block) + B-07 (module)",
         note="the light colour/group live in the light carrier, not in the paint block; T-18 "
              "already decodes these sockets"),
    dict(id="R2", cls="textures", status="partial",
         why="emissive mask -> material-level m_Emissive (JC3 emissive mask channel not decoded)",
         action="route", pol="", target="static.Emissive intensity + CarLight emitter",
         owner="T-18 (values) -> B-03 (block)",
         note="the mask itself is not sampled (channel undecoded, MODLOG §102d); the emitter is "
              "carried by the CarLight block, which is where APP-4 wants it"),
    dict(id="R3", cls="factors", status="partial",
         why="glass response -> Window block (params not decoded: vanilla glass)",
         action="route", pol="", target="Window block (BC3 dif, ALPHABLENDING)",
         owner="appearance pipeline (factors.py already writes the block)",
         note="the block type is the carrier and is already written; its numeric parameters are "
              "UNKNOWN (§102d) so the vanilla glass response is kept"),
    dict(id="R4", cls="textures", status="partial",
         why="glass layer mask: no per-layer Window slots; carried as the material-level tint only",
         action="route", pol="", target="Window dif alpha (tint x Glass_Opacity)",
         owner="appearance pipeline (factors.py already writes the dif alpha)",
         note="one Window layer only: the mask's per-layer split is lost, its tint survives"),
    # ---------------------------------------------------------------- dropped
    dict(id="D1", cls="factors", status="excluded",
         why="JC3 dirt (dynamic per object); BmAK mud is chapter-scripted: SupportDirt 0, "
             "DirtColor recorded",
         action="drop", pol="", target="JC3 runtime dirt (engine-global)",
         owner="none - JC3 owns dirt per object",
         note="BmAK's mud is chapter-scripted; the value has no material input. DirtColor is "
              "already written by factors.py, dirt is off (SupportDirt 0)"),
    dict(id="D2", cls="factors", status="partial",
         why="dielectric reflectance: JC3 uses a fixed F0; kept only as metallic when no "
             "Metalicity is given and value > 0.5",
         action="route", pol="",
         target="`CarPaintMM` `m_Metallic` (`cb2[1]`) + `m_ClearCoat` (`cb2[2]`) per channel, "
                "F0 residual recorded per value",
         owner="T-21 (values) -> factors.py REFL batch (`tmp/freebuff/reports/"
               "app-reflectance-f0.md`)",
         note="the paint block has no F0 member (0 of 13 `carpaintmm*` headers; "
              "`ModelSpecularColor` is `[unused]`), so the reachable band is "
              "[min(a, F0_d), max(a, F0_d)] = F0_d x [0.65 .. 1.0] on a 0.026 albedo. Of the 20 "
              "decoded values 6 land exactly and 14 miss by 0.0058..0.1551 (rel. 17..330 %), "
              "F0_d = 0.04 assumed; `R > 1` rides `m_ClearCoat` (the exact route is a "
              "`GeneralMkIII` `Reflectivity_1` write, whose payload layout is undecoded)"),
    dict(id="D3", cls="textures", status="partial",
         why="per-pixel reflectivity/roughness -> material-level gloss (JC3 varies properties "
             "only by channel)",
         action="route", pol="",
         target="`CarPaintMM` `s2` four-band selector x `m_SpecularGloss`/`m_Metallic` float4; "
                "`GeneralMkIII` `Gloss1Map`/`Metallic1Map` for the continuous parts",
         owner="T-21 (bake) -> appearance_pipeline.py banded `s2` (`tmp/freebuff/reports/"
               "app-per-pixel-reflectivity.md` section 5.1)",
         note="'only by channel' is false: `s2` is sampled per texel and selects one of four "
              "material channels, so the map carries four discrete gloss/metallic levels "
              "(bins 0.15/0.40/0.70, `GLOSS_CAP` 0.45 per band); `GeneralMkIII` adds separate "
              "per-pixel Gloss/Metallic maps for a block swap. Channel order (R/G/B = "
              "rough/reflect/metal) is UNKNOWN - test T3"),
    dict(id="D4", cls="factors", status="excluded", why="anisotropic highlights",
         action="route", pol="",
         target="s1 normal + tint/gloss bake: the two coloured lobes folded into the baked "
                "`s1`/`s2` (no shader input exists)",
         owner="T-21 (bake) -> appearance_pipeline.py texture convert (`tmp/freebuff/reports/"
               "app-anisotropic-highlights.md` section 7)",
         note="0 of 961 reflection headers declares an anisotropy parameter, a lobe colour, a "
              "tangent-orientation vector or an aniso ramp sampler ('aniso' appears only as "
              "texture-filter names); the decoded effect is two coloured lobes - thin "
              "[0.1957, 0.2, 0.33] / broad [0.462, 0.7335, 0.9723] on WheelArchs, "
              "brightness 0.5/0.1 - and it is a UV-space fake, so a bake reproduces its "
              "colour and streak, not its view response"),
    dict(id="D5", cls="textures", status="excluded", why="anisotropic highlight ramp",
         action="route", pol="",
         target="the D4 `s1`/`s2` bake (the ramp has no sampler; its lookup is what the lobe "
                "bake approximates)",
         owner="T-21 (bake) -> appearance_pipeline.py texture convert",
         note="`Engine.Aniso_ramp_Lacquered` has no sampler in any JC3 block (0 of 961 headers "
              "declare one), so the ramp is consumed at bake time by the same texture that "
              "carries D4's two lobe colours"),
    dict(id="D6", cls="factors", status="excluded",
         why="JC3 dirt colour (recorded in DirtColor, dirt disabled)",
         action="drop", pol="", target="static.DirtColor (already written)",
         owner="none - record only",
         note="the colour is kept in the block as a record; the dirt system that would use it is "
              "off, so nothing else is needed"),
    dict(id="D7", cls="factors", status="excluded", why="JC3 weather",
         action="drop", pol="", target="JC3 weather system (engine-global)",
         owner="none - JC3 owns weather",
         note="rain direction / rain size are scene inputs in JC3, not material inputs"),
    dict(id="D8", cls="factors", status="excluded", why="JC3 weather/wetness system",
         action="route", pol="",
         target="`Window` `s9 RainOccluderSampler` (`t40`) + `GeneralMkIII` "
                "`WetnessNoiseTexture` (`t41`); the paint keeps the scene factor",
         owner="T-21 (textures) -> appearance_pipeline.py; scene value is not ours to write "
               "(`tmp/freebuff/reports/app-wetness-and-rain.md`)",
         note="the paint block has no wetness member and no rain sampler (0 of 13 "
              "`carpaintmm*` headers), so `Wetness_Refl_Fresnel` 0.6, "
              "`Wetness_Reflectivity_Multiplier` 0.6, `RainReflectivityMul` 1.6 and "
              "`RainRoughnessMul` 0.75 ride the scene `TEST_WETNESS_FACTOR` (value UNKNOWN); "
              "the per-material lever exists only on `Window` (4 of 4 headers, s9/t40) and "
              "`GeneralMkIII` (55 of 156 general headers, t41), which is where the mask goes"),
    dict(id="D9", cls="textures", status="excluded",
         why="story-chapter damage reveal (JC3 damage is hit-driven: SupportDmgBlend 0)",
         action="drop", pol="", target="-",
         owner="none - APP-7 wants scorch/smoke only",
         note="BmAK reveals damage by story chapter; JC3 damage is hit-driven and R1 forbids "
              "deformation, so the mask would have nothing to drive"),
    dict(id="D10", cls="textures", status="excluded",
         why="colour ramp lookup (and the ramp files are missing-on-disk)",
         action="drop", pol="", target="-", owner="none - source absent",
         note="the ramp texture is referenced by the material dump but is not in the export, so "
              "it can be neither converted nor baked. Still open: the two ramp reports that "
              "would name a carrier (`app-colour-ramp-textures.md`, "
              "`ramp-names-quick-search.md`) do not exist on disk, so no ramp name, lookup "
              "member or replacement was decoded and this row is unchanged"),
    dict(id="D11", cls="factors", status="excluded",
         why="editor/fake helper or smudge overlay",
         action="drop", pol="", target="-", owner="none - authoring helper",
         note="UE editor scaffolding, not a rendered input"),
    dict(id="D12", cls="factors", status="excluded", why="editor helper",
         action="drop", pol="", target="-", owner="none - authoring helper",
         note="UE editor scaffolding, not a rendered input"),
    dict(id="D13", cls="factors", status="excluded", why="tessellated displacement",
         action="drop", pol="", target="-", owner="none - no tessellation on the JC3 side",
         note="BmAK displaces a tessellated mesh; the JC3 body is a fixed LOD mesh (R1: no "
              "deformation), so displacement has no carrier"),
    dict(id="D14", cls="factors", status="excluded", why="story EMP effect",
         action="drop", pol="", target="entity effect graph (T-17) if ever needed",
         owner="none in the material",
         note="the EMP look is an effect, not a material input; T-17 owns the effects"),
]


def _rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def _load():
    progress = json.load(open(PROGRESS, encoding="utf-8"))
    slots = json.load(open(SLOTS, encoding="utf-8"))
    factors = json.load(open(FACTORS, encoding="utf-8"))["materials"]
    return progress, slots, factors


def _texture_materials(factors):
    """texture name -> materials that bind it (from the `factors.json` dispositions)."""
    out = {}
    for mat, spec in factors.items():
        for d in spec["dispositions"]:
            if not d["factor"].startswith("tex:") or d["value"] in (None, "None"):
                continue
            out.setdefault(d["value"], [])
            if mat not in out[d["value"]]:
                out[d["value"]].append(mat)
    return out


def _rule_for(cls, status, why):
    for r in RULES:
        if r["cls"] == cls and r["status"] == status and r["why"] == why:
            return r
    return None


def _slots_by_material(slots):
    return {s["material"]: s for s in slots["slots"]}


def build_rows():
    progress, slots, factors = _load()
    tex_mats = _texture_materials(factors)
    slot_of = _slots_by_material(slots)
    for name in INTERIOR:
        if name not in slot_of:
            raise SystemExit(f"interior material {name} is not a slot in SLOTS.json")

    rows, unclassified = [], []
    for cls, block in progress["classes"].items():
        for comp in block["components"]:
            if comp["status"] == "transferred":
                continue
            if comp["status"] == "missing":
                unclassified.append(comp["component"] + " (status missing: nothing to plan)")
                continue
            rule = _rule_for(cls, comp["status"], comp["why"])
            if rule is None:
                unclassified.append(f"{comp['component']} [{cls}/{comp['status']}] {comp['why']}")
                continue
            if cls == "factors":
                mats = [comp["component"].split(":")[0]]
            else:
                mats = list(tex_mats.get(comp["component"], []))
            pol = [rule["pol"]] if rule["pol"] else []
            if any(m in INTERIOR for m in mats) and "POL-1" not in pol:
                pol.append("POL-1")
            rows.append({
                "component": comp["component"], "class": cls, "status": comp["status"],
                "rule": rule["id"], "action": rule["action"], "pol": pol,
                "target": rule["target"], "owner": rule["owner"], "note": rule["note"],
                "materials": mats,
                "in_slot": any(m in slot_of for m in mats),
            })

    interior_rows = []
    for name in INTERIOR:
        slot = slot_of[name]
        spec = factors.get(name, {})
        total = sum(1 for r in rows if name in r["materials"])
        interior_rows.append({
            "slot": slot["index"], "material": name, "lod0_faces": slot["lod0_faces"],
            "block": spec.get("block"), "slots_bound": sorted(spec.get("textures", {})),
            "planned": total,
            "planned_rows": [r["component"] for r in rows if name in r["materials"]],
        })

    skins = parse_skins()
    payload = {
        "card": "T-21",
        "schema": 1,
        "sources": {
            "progress": _rel(PROGRESS),
            "progress_build": progress.get("build", "").replace("\\", "/"),
            "slots": _rel(SLOTS), "variants": _rel(VARIANTS), "factors": _rel(FACTORS),
        },
        "totals": totals(progress, rows, unclassified),
        "rules": [{k: r[k] for k in ("id", "cls", "status", "why", "action", "pol", "target",
                                     "owner", "note")} for r in RULES],
        "interior": interior_rows,
        "skins": skins,
        "components": rows,
        "unclassified": unclassified,
    }
    return payload


def totals(progress, rows, unclassified):
    counts = {a: sum(1 for r in rows if r["action"] == a) for a in ("bake", "route", "drop")}
    t = progress["overall"]
    return {
        "components": t["total"], "transferred": t["transferred"], "partial": t["partial"],
        "excluded": t["excluded"], "missing": t["missing"],
        "planned": len(rows), "bake": counts["bake"], "route": counts["route"],
        "drop": counts["drop"], "unclassified": len(unclassified),
        "pol1": sum(1 for r in rows if "POL-1" in r["pol"]),
        "pol2": sum(1 for r in rows if "POL-2" in r["pol"]),
    }


def parse_skins():
    """Per-skin material delta straight out of VARIANTS.md §3 (G1-20's table)."""
    text = open(VARIANTS, encoding="utf-8").read()
    if "## 3. Materials" not in text:
        raise SystemExit("VARIANTS.md has no '## 3. Materials' section")
    sec = text.split("## 3. Materials", 1)[1].split("\n## ", 1)[0]
    rows = []
    # the count cell is a bare integer today (`| V2 | 78 |`); the older table bolded it and listed
    # material names, so both spellings parse and the extra/missing cells are carried as written
    for m in re.finditer(r"^\|\s*(V2|MK2|Joker|Funhouse)\s*\|\s*\*{0,2}(\d+)\*{0,2}\s*\|(.*)$", sec, re.M):
        cells = [c.strip() for c in m.group(3).split("|")]
        rows.append({
            "variant": m.group(1), "materials": int(m.group(2)),
            "extra": cells[0] if len(cells) > 0 else "",
            "missing": cells[1] if len(cells) > 1 else "",
        })
    if len(rows) != 4:
        raise SystemExit(f"VARIANTS.md §3: expected 4 variant rows, parsed {len(rows)}")
    return rows


def render(payload):
    t = payload["totals"]
    skin_rows = payload["skins"]
    uses = {}
    for r in payload["components"]:
        uses.setdefault(r["rule"], []).append(r["component"])

    L = []
    A = L.append
    A("# Appearance plan (T-21)")
    A("")
    A("What is still missing from the appearance transfer, one row per component that is not fully")
    A("transferred, and exactly one action for each: **bake** (POL-2), **route** (another JC3")
    A("carrier) or **drop** (no carrier, reason stated). Generated by")
    A("`Tools/scripts/appearance_plan.py --write` from:")
    A("")
    A(f"- `{payload['sources']['progress']}` (the run this plan classifies; its timestamp and"
      " per-class table are in that file and in `progress.md`)")
    A(f"- `{payload['sources']['slots']}` - the 19 material slots")
    A(f"- `{payload['sources']['factors']}` - block type and bound sampler per material")
    A(f"- `{payload['sources']['variants']}` - the skin deltas (D-5)")
    A("")
    A("**Done criterion:** 0 unclassified components.")
    A("")
    A("```")
    A(f"components {t['components']} = transferred {t['transferred']} + partial {t['partial']}"
      f" + excluded {t['excluded']} + missing {t['missing']}")
    A(f"planned {t['planned']}: bake {t['bake']} | route {t['route']} | drop {t['drop']}"
      f" | unclassified {t['unclassified']}")
    A(f"POL-1 (interior) {t['pol1']} rows | POL-2 (micro-detail bake) {t['pol2']} rows"
      " (a row can carry both)")
    A("```")
    A("")
    carried = t["transferred"] + t["bake"] + t["route"]
    route_partial = sum(1 for r in payload["components"]
                        if r["action"] == "route" and r["status"] == "partial")
    A("## 0. T-21 completion note")
    A("")
    A(f"`appearance_progress.py` counts **{t['components']}** components: {t['transferred']}"
      f" transferred, {t['partial']} partial, {t['excluded']} excluded, {t['missing']} missing."
      f" The plan classifies the {t['planned']} that are not fully transferred - {t['bake']}"
      f" bake, {t['route']} route, {t['drop']} drop - with **{t['unclassified']} unclassified**,"
      " so the card's Done criterion is met.")
    A("")
    A(f"**Faithfully carried by plan: {carried} of {t['components']}"
      f" ({100.0 * carried / t['components']:.1f}%)** = the {t['transferred']} already in the"
      f" build + {t['bake']} baked into a sampler the block already has + {t['route']} routed to a"
      f" named carrier. **{t['drop']} stay unresolved"
      f" ({100.0 * t['drop'] / t['components']:.1f}%)**, each with the reason it cannot be carried:")
    A("")
    for rule in payload["rules"]:
        if rule["action"] != "drop":
            continue
        n = sum(1 for r in payload["components"]
                if r["action"] == "drop" and r["rule"] == rule["id"])
        if not n:
            continue
        A(f"- **{rule['id']}** - {n} - {rule['note']}")
    A("")
    A(f"Of the {t['route']} routed rows, {route_partial} are `partial`: the carrier is named but a"
      " per-pixel part of the value is lost, so they narrow a gap rather than close it."
      f" Counting only what is closed today ({t['transferred']} transferred + {t['bake']} bake,"
      " which still needs the pipeline run):"
      f" {t['transferred'] + t['bake']} of {t['components']}"
      f" ({100.0 * (t['transferred'] + t['bake']) / t['components']:.1f}%).")
    A("")
    A(f"The five carrier reviews (sections 7-{6 + len(CROSS)}) leave these residual gaps:")
    A("")
    for s in CROSS:
        A(f"- **{s['title']}** - {s['verdict']} (`{s['report']}`).")
    A("")
    A("## 1. The actions")
    A("")
    A("| action | rows | what happens |")
    A("|---|---|---|")
    A(f"| bake | {t['bake']} | the BmAK source texture is baked into a sampler the block already "
      "has (s1 normal / s0 albedo); POL-2 |")
    A(f"| route | {t['route']} | the value is carried by another carrier the build writes: "
      "`Window` block, `static.Emissive`, `CarLight` block / lights module, the `s2` gloss "
      "bands / `GeneralMkIII` maps, the rain occluder, or the `s1` bake |")
    A(f"| drop | {t['drop']} | no JC3 carrier exists; the value is dropped and the reason is "
      "stated per rule |")
    A("")
    A("## 2. POL-2 - the micro-detail bake")
    A("")
    A("Micro-detail is the largest single group (textures + tiling sizes + the roughness")
    A("modulation). `CarPaintMM` has no detail sampler of its own - the decoded interface is 18")
    A("static float4 + 7 support floats + the 4 tint components (`factors.py` header) - so the")
    A("pattern reaches the car by baking, which is what POL-2 asks for. The bake changes no block")
    A("count and no texture count, so it does not touch the R9 texture budget.")
    A("")
    A("| rule | component | class | status | where the baked result goes | owner |")
    A("|---|---|---|---|---|---|")
    for r in payload["components"]:
        if r["action"] != "bake":
            continue
        A(f"| {r['rule']} | `{r['component']}` | {r['class']} | {r['status']} | "
          f"{r['target']} | {r['owner']} |")
    A("")
    A("## 3. Routed carriers")
    A("")
    A("| rule | component | class | status | carrier | owner | note |")
    A("|---|---|---|---|---|---|---|")
    for r in payload["components"]:
        if r["action"] != "route":
            continue
        A(f"| {r['rule']} | `{r['component']}` | {r['class']} | {r['status']} | {r['target']} | "
          f"{r['owner']} | {r['note']} |")
    A("")
    A("## 4. Dropped, with the reason")
    A("")
    A("| rule | rows | reason recorded by `appearance_progress.py` | why it cannot be carried |")
    A("|---|---|---|---|")
    for rule in payload["rules"]:
        if rule["action"] != "drop":
            continue
        n = len(uses.get(rule["id"], []))
        if not n:
            continue
        A(f"| {rule['id']} | {n} | {rule['why']} | {rule['note']} |")
    A("")
    A("<details><summary>every dropped component</summary>")
    A("")
    A("| rule | component | class | status |")
    A("|---|---|---|---|")
    for r in payload["components"]:
        if r["action"] != "drop":
            continue
        A(f"| {r['rule']} | `{r['component']}` | {r['class']} | {r['status']} |")
    A("")
    A("</details>")
    A("")
    A("## 5. POL-1 - interior materials")
    A("")
    A("The interior is six of the 19 slots (G1-19 fixes seat = slot 11 and dashboard = slot 10;")
    A("MODDING_PLAN.md phase 6 item 6 names interior, cockpit, seat and power cell).")
    full = all({"s0", "s1", "s2", "s3"} <= set(i["slots_bound"]) for i in payload["interior"])
    if full:
        A("All six already have their four samplers bound (`s0` diffuse, `s1` normal, `s2` property")
        A("map, `s3` tint map), so POL-1's \"no untextured surface\" holds for the interior before")
        A("any of the rows below are worked: what remains is detail, not colour.")
    else:
        A("**At least one interior material does not have all four samplers bound** - a colour")
        A("gap, not a detail gap (POL-1). See the table.")
    pol1 = [r for r in payload["components"] if "POL-1" in r["pol"]]
    acts = {a: sum(1 for r in pol1 if r["action"] == a) for a in ("bake", "route", "drop")}
    A("")
    A(f"Verdict: {len(pol1)} interior components remain - bake {acts['bake']}, route "
      f"{acts['route']}, drop {acts['drop']}; none of them is a missing colour or a missing")
    A("normal map, so POL-1 needs no new interior texture, only the routed emissive and the")
    A("micro-detail bake that POL-2 covers for every material.")
    A("")
    A("| slot | material | LOD0 faces | block | samplers bound | components touching it |")
    A("|---|---|---|---|---|---|")
    for i in payload["interior"]:
        A(f"| {i['slot']} | `{i['material']}` | {i['lod0_faces']} | {i['block']} | "
          f"{', '.join(i['slots_bound'])} | {i['planned']} |")
    A("")
    A("A component shared by two interior materials (a texture bound by the cockpit and the seat)")
    A("appears in both rows, which is why the column sums to more than the "
      f"{len(pol1)} unique interior")
    A("components listed next.")
    A("")
    A("Interior components in this plan (POL-1 tag):")
    A("")
    A("| component | class | status | action | rule | target |")
    A("|---|---|---|---|---|---|")
    for r in payload["components"]:
        if "POL-1" not in r["pol"]:
            continue
        A(f"| `{r['component']}` | {r['class']} | {r['status']} | {r['action']} | {r['rule']} | "
          f"{r['target']} |")
    A("")
    A("## 6. Skins (D-5)")
    A("")
    A("**D-5 resolved 2026-10-28 (user): skins as extra Rebel Drop entries.** Each skin is its own")
    A("drop entry, so each one carries its own body RBM, its own material blocks and its own bake:")
    A("this plan is written for the reference `Batmobile_V2` set and re-applies to a skin's material")
    A("set unchanged, because the actions are per factor name, not per material. The per-variant")
    A("material deltas from G1-20 (`VARIANTS.md` §3):")
    A("")
    A("| variant | materials | extra vs V2 | missing vs V2 |")
    A("|---|---|---|---|")
    for s in skin_rows:
        A(f"| {s['variant']} | {s['materials']} | {s['extra']} | {s['missing']} |")
    A("")
    A("Consequences for the build, from those deltas:")
    A("")
    A("- **MK2** replaces the main body and wheel materials, so its bake is a re-run of the same")
    A("  rules over `Batmobile_MK2_Body_MIC` / `Batmobile_MK2_Wheel_INST` - no new rule.")
    A("- **Joker / Funhouse** swap in the Jokerfied material set and drop the V2 FX materials; the")
    A("  Jokerfied materials are new names, so they need their own `factors.json` run before a row")
    A(f"  count exists (UNKNOWN, §{6 + len(CROSS) + 2}).")
    A("- The skins cost texture budget: each entry ships its own `.ddsc` set, and the R9 wall")
    A("  (Texture 7,065 KB) is per entity - the per-skin totals are not measured yet (UNKNOWN).")
    A("")
    for n, s in enumerate(CROSS, 7):
        A(f"## {n}. {s['title']}")
        A("")
        A(f"Source: `{s['report']}`. **{s['verdict']}.** Decoded numbers against the JC3 member")
        A("that carries each:")
        A("")
        A("| BmAK input | value | JC3 member | gap |")
        A("|---|---|---|---|")
        for bmak, value, member, gap in s["rows"]:
            A(f"| {bmak} | {value} | {member} | {gap} |")
        A("")
    A(f"## {6 + len(CROSS) + 1}. Every planned component")
    A("")
    A("| # | component | class | status | action | rule | POL | materials |")
    A("|---|---|---|---|---|---|---|---|")
    for n, r in enumerate(payload["components"], 1):
        A(f"| {n} | `{r['component']}` | {r['class']} | {r['status']} | {r['action']} | "
          f"{r['rule']} | {', '.join(r['pol']) or '-'} | {', '.join(r['materials']) or '-'} |")
    A("")
    A(f"## {6 + len(CROSS) + 2}. UNKNOWNs and limits")
    A("")
    A("- **The `Window` block's numeric parameters are not decoded** (MODLOG §102d), so the three")
    A("  glass rows route to the block but their values stay vanilla. No number is invented.")
    A("- **The micro-detail bake does not exist yet.** `appearance_pipeline.py` converts textures")
    A("  as they are; a bake step (UV scale from the tiling sizes, pattern folded into s1) is the")
    A("  POL-2 work, owned by that tool. Until it runs, the 23 bake rows stay `partial`/`excluded`.")
    A("- **Per-skin component counts are UNKNOWN**: only the reference build has a `factors.json`,")
    A("  so the MK2/Joker/Funhouse material sets have no measured component rows yet.")
    A("- **Per-skin texture budget is UNKNOWN**: R9's 7,065 KB is per entity and no skin build has")
    A("  been measured.")
    A("- The 27 reflectance rows are routed, not dropped: 6 of the 20 decoded values land in")
    A("  `CarPaintMM`'s metallic band exactly and 14 miss by 0.0058..0.1551 (`app-reflectance-f0.md`")
    A("  section 4.1, `F0_d` = 0.04 assumed). The 4 per-pixel roughness textures are routed to the")
    A("  four-band `s2` (`app-per-pixel-reflectivity.md` section 5.1). What stays dropped by")
    A("  decision is the gloss cap itself (`GRB-6`, `VALUES.json`) - not re-opened here.")
    A("- **Colour ramps (D10) stay dropped and open**: `app-colour-ramp-textures.md` and")
    A("  `ramp-names-quick-search.md` do not exist on disk, so the ramp rows have no decoded")
    A("  replacement yet.")
    A("")
    A(f"## {6 + len(CROSS) + 3}. Reproduce and revert")
    A("")
    A("```")
    A("python Tools/scripts/appearance_plan.py --check    # re-derives this file and the json")
    A("python Tools/scripts/appearance_progress.py --plan  # the same 172 rows, annotated")
    A("```")
    A("")
    A("Revert: delete this file, `appearance_plan.json` and `Tools/scripts/appearance_plan.py`;")
    A("`appearance_progress.py`'s `--plan` block is independent and optional.")
    A("")
    return "\n".join(L)


def write():
    payload = build_rows()
    md = render(payload)
    with open(JS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    summary(payload)
    print("md ->", _rel(MD))
    print("json ->", _rel(JS))
    return 0 if payload["totals"]["unclassified"] == 0 else 1


def summary(payload):
    t = payload["totals"]
    print(f"components {t['components']} | transferred {t['transferred']} | partial "
          f"{t['partial']} | excluded {t['excluded']} | missing {t['missing']}")
    print(f"planned {t['planned']}: bake {t['bake']} route {t['route']} drop {t['drop']} | "
          f"POL-1 {t['pol1']} POL-2 {t['pol2']} | unclassified {t['unclassified']}")


def check():
    payload = build_rows()
    problems = []
    got_md = render(payload)
    if not os.path.exists(MD):
        problems.append(f"{_rel(MD)} missing")
    elif open(MD, encoding="utf-8").read().replace("\r\n", "\n") != got_md:
        problems.append(f"FAIL {_rel(MD)} stale: the regenerated text differs")
    if not os.path.exists(JS):
        problems.append(f"{_rel(JS)} missing")
    else:
        disk = json.load(open(JS, encoding="utf-8"))
        if disk != json.loads(json.dumps(payload)):
            problems.append(f"FAIL {_rel(JS)} stale: the payload differs")

    t = payload["totals"]
    if t["components"] != 339 or t["transferred"] != 167:
        problems.append(f"FAIL progress.json changed shape: {t['components']} components, "
                        f"{t['transferred']} transferred (the card's input is 339 / 167)")
    if t["missing"]:
        problems.append(f"FAIL {t['missing']} component(s) missing: a missing file is not a plan")
    if t["planned"] != t["partial"] + t["excluded"]:
        problems.append(f"FAIL planned {t['planned']} != partial+excluded "
                        f"{t['partial'] + t['excluded']}")
    if t["unclassified"]:
        problems.append(f"FAIL unclassified {t['unclassified']}: the card's Done is 0")
        for u in payload["unclassified"][:10]:
            problems.append("   " + u)
    used = {r["rule"] for r in payload["components"]}
    for rule in payload["rules"]:
        if rule["id"] not in used:
            problems.append(f"FAIL rule {rule['id']} matches no component (dead plan row)")
    for r in payload["components"]:
        if r["action"] not in ("bake", "route", "drop"):
            problems.append(f"FAIL {r['component']}: action {r['action']}")
        if not r["target"]:
            problems.append(f"FAIL {r['component']}: no target")
    if t["pol2"] != t["bake"]:
        problems.append(f"FAIL POL-2 {t['pol2']} != bake {t['bake']}: every bake is POL-2")
    if len(payload["skins"]) != 4:
        problems.append(f"FAIL {len(payload['skins'])} skin rows parsed from VARIANTS.md, expected 4")

    summary(payload)
    print(f"md match {not any('stale' in p and 'APPEARANCE_PLAN.md' in p for p in problems)}, "
          f"json match {not any('stale' in p and '.json' in p for p in problems)}")
    if problems:
        for p in problems:
            print(p)
        print(f"{len(problems)} problem(s)")
        return 1
    print("check ok")
    return 0


def show(name):
    payload = build_rows()
    for r in payload["components"]:
        if r["component"] == name:
            print(json.dumps(r, indent=1, ensure_ascii=False))
            return 0
    lower = name.lower()
    for r in payload["components"]:
        if lower in r["component"].lower():
            print(json.dumps(r, indent=1, ensure_ascii=False))
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--show", metavar="COMPONENT")
    a = ap.parse_args()
    if a.write:
        sys.exit(write())
    if a.check:
        sys.exit(check())
    sys.exit(show(a.show))


if __name__ == "__main__":
    main()

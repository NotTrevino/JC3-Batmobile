# Landmark map: APPEARANCE (body, scale, paint, materials/textures, glass/interior, emissive, wheels, part split, battle silhouette, skins, no-deform)

Read-only mapping, 2026-11-08. All paths are relative to `E:\Modding\JC3-Batmobile` unless absolute. Labels: **decoded/derived** = a file says so; **UNKNOWN** = no file says so. I did not launch anything and edited nothing but this file. Where I could not verify a status I say "unverified".

Key state in one paragraph: the geometry side of APPEARANCE is essentially built and offline-verified (RC4: 25 RBMs, silhouette 99.9004 % vs 99.9 limit, 59 parts, 19 material slots, Model 4,791.3 / 4,915 KB). The colour/material side is built but unfaithful and **never seen in game since the research reset**: RC4 receipt `complete:false` says "12 of 23 texture rows are unfaithful" (4 chapter masks + 8 missing pixel sets). The "BmAK black" problem has **no known JC3 value** (RESET_FINDINGS §2): decoded linear [0.0258,0.0258,0.030] (x Diffuse_Adjust [2.2,2,2] = [0.0567,0.0516,0.06]) was replaced by screenshot-chosen constants (ALB-2 gain 4 -> 0x837d86 = white-violet in JC3 daylight). The game-ready fix (RC5 paint, brief 9143) is queued and gated, and nothing has been installed or launched since: `tmp/freebuff/APPROVED_Q.txt` is absent (test ban). Skins (MK2/Jokerfied/Funhouse), battle-mode silhouette (B-12) and the chapter-mask/ramp/aniso/micropattern classes are not built.

---

## Task table

Legend for stage: GRAB / TRANSLATE / BUILD / VERIFY (offline) / PILOT / TEST (in game) / RELEASE. Size: S <=1 session, M 1-3, L 1-2 wk.

### A. Requirements (the definition of done)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| APP-1 | Body = Batmobile_V2, true scale, 5 LODs, 19 slots, no tears; seen right in game | TEST | partial (built/verified offline, no in-game look since reset) | APPROVED_Q, Q-PILOT proof | R-1 | S | `GRAB_BACKLOG.md:129`; `Builds/bm-RC4/verify/geometry.md`; `tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md` |
| APP-2 | Paint reads as BmAK matte/satin armour in noon + night | TEST | blocked (colour conversion unknown) | NEW-APP-1, 9143, G3-07 | R-1 | L | `GRAB_BACKLOG.md:130`; `RESET_FINDINGS.md` §2 |
| APP-3 | Canopy tinted glass, interior visible through it | TEST | partial (Window block carried, params guessed) | T-MA5 probe, NEW-APP-12 | R-1 | M | `GRAB_BACKLOG.md:131`; `tmp/freebuff/reports/windscreen-and-glass-plan.md` |
| APP-4 | Emissive parts glow (lamps, tail strip, arch lights, dash) | TEST | partial (lamps built B-03/B-07; dash/Wheel_E not) | NEW-APP-14, NEW-APP-15, B-25 | R-1 | M | `GRAB_BACKLOG.md:132`; B-03 row `GRAB_BACKLOG.md:1949` |
| APP-5 | Movable parts are separate meshes (turret, cannon, Vulcan, fins, hatches, fan, canopy, yoke) | TEST | partial (split built; joints/animation unbuilt) | 9172, JOINTS-v2 | R-1 | M | `GRAB_BACKLOG.md:133`; B-02/B-04 rows |
| APP-6 | Battle-mode silhouette reachable (pose or second variant) | TEST | todo | B-12, D-2 swap U1 | R-1 | L | `GRAB_BACKLOG.md:134`; `Research/BatmobileGrab/POSES.md` |
| APP-7 | Car never deforms; no damage visuals (reconcile with operator fact: no visible damage stages, no scratches) | TEST | partial (switch off; wording stale) | NEW-APP-27 | R-1 | S | `GRAB_BACKLOG.md:135`; memory `bmak-gameplay-facts.md` |
| APP-8 | MK2 / Jokerfied (and Funhouse) skins as extra Rebel Drop entries (D-5) | BUILD+TEST | todo | NEW-APP-18..24 | R-1 | L | `GRAB_BACKLOG.md:136,1799`; `tmp/freebuff/reports/app-skins-and-variants.md` |

### B. GRAB (BmAK + JC3 facts)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| G1-11 | Skeleton / vertex-bone ownership | GRAB | done | - | B-02 | - | `Research/BatmobileGrab/BONES.md` |
| G1-12 | Pursuit/battle pose deltas | GRAB | done | - | NEW-APP-25 | - | `Research/BatmobileGrab/POSES.md` |
| G1-19 | Cockpit/driver placement | GRAB | done | - | - | - | `Research/BatmobileGrab/COCKPIT.md` |
| G1-20 | Skins/variants inventory (V2/MK2/Joker/Funhouse diff) | GRAB | done | - | NEW-APP-18 | - | `Research/BatmobileGrab/VARIANTS.md` |
| G3-05b | Skins decode (4 pkgs, 248 sockets, 84 slots) | GRAB | done | - | NEW-APP-18 | - | `Research/BatmobileGrab/SKINS.md` |
| G3-03 | BmAK ini set (tonemap/exposure/post-process keys) | GRAB | unverified (G3-04 lists it as dep; tracker row not read) | - | G3-04 | S | `GRAB_BACKLOG.md:938` |
| G3-04 | BmAK colour pipeline: on-screen colour as function of named terms | GRAB | partial (chain + Diffuse_Adjust decoded; combine rule UNKNOWN) | stripped material graphs | APP-2 | M | `Research/BatmobileGrab/COLOUR.md` |
| G3-04b | Material function bodies (colour logic) | GRAB | blocked: dead end on disk (FunctionExpressions zero) | needs runtime (BmSDK, NEW-APP-3) | G3-04 | - | `Research/BatmobileGrab/COLOUR_FUNCTIONS.md` |
| G3-04c | Body-slot MIC params by owner | GRAB | done | - | 9143 | - | `Research/BatmobileGrab/COLOUR_PARAMS.md` |
| G3-04d/d2/e | JC3 shader cbuffer slots (cb2/cb6/cb7), uniform records | GRAB | partial (names of slots done; name->offset map UNKNOWN) | no RDEF in caches | G3-09 | - | `Research/JC3Grab/CB0_SLOTS.md`, `UNIFORM_RECORDS.md` |
| G3-09 | JC3 on-screen colour function, calibrated on >=3 vanilla paints | GRAB | partial (palette decoded; tint semantics + tonemap need runtime) | G3-07 oracle | APP-2 | M | `Research/JC3Grab/COLOUR.md` |
| G3-09b | JC3 exe: how tint is chosen/written to CarPaintMM dynamic | GRAB | queued (task 2017) | - | G3-09 | M | `GRAB_BACKLOG.md:1043,1903` |
| G3-09c | Native colour constants | GRAB | done | - | - | - | `COLOUR_NATIVE2.md` |
| G3-09d / d2 | Palette tint parameter located; write path = palette .vmodc float, CCar.palette int32 hash | GRAB | done (located) / partial (what writes palette->cb6 UNKNOWN) | G3-07 | NEW-APP-5 | - | `Research/JC3Grab/TINT.md`, `TINT_WRITE.md` |
| G3-07 | JC3 runtime oracle (colour on screen, loaded resources, body transforms) | GRAB | open (root blocker for any measured claim) | none (read-only memory reader, but needs game run) | G3-09, G3-09b, APP-2 | L | `GRAB_BACKLOG.md:988`; `RESET_FINDINGS.md` §1 |
| G3-07a/b | Runtime layout for the sampler (static) | GRAB | a done / b queued (task 2030) | - | G3-07 | M | `Research/JC3Grab/RUNTIME_LAYOUT.md` |
| G3-06 / G3-06h | Untagged remainder; parts/light/particle components (6: PointLight, ParticleSystem, SkeletalMesh) | GRAB | G3-06 done; **G3-06h todo** | T-12, T-18 | APP-5 | S | `GRAB_BACKLOG.md:1912` |
| G3-12 | JC3 donor decode depth (441 FULL/121 PARTIAL/4 NAMED-ONLY; 116 .ddsc FULL not proven) | GRAB | done w/ caveat; G3-12b (.pfxc + .ddsc proof) todo | - | texture build confidence | M | `Research/JC3Grab/DECODE_DEPTH.md` |
| G3-05c / 9054 | Locate 8 missing pixel sets in all cooked packages | GRAB | partial: script + `PIXEL_LOCATE.md` exist (0 found, 5 import-only, 3 absent; 1247 of 3266 packages unreadable); queue brief 9054 still queued, report missing | 1247 unreadable packages | NEW-APP-9 | S | `Working/Appearance/PIXEL_LOCATE.md`; `tmp/freebuff/queue/9054-*` |
| NEW-APP-1 | Define acceptance for "BmAK black": operator-approved criterion (exact decoded colour vs on-screen luminance band) since the combine rule is UNKNOWN. Brief 9143 already assumes "exact decoded colour; JC3 lighting brighter is accepted"; that is an operator rule in a brief, not in OPERATOR_PRIORITIES.md | TRANSLATE | todo (decision) | operator | APP-2, Q1-2 band | S | `tmp/freebuff/queue/9143-*`; `Working/Q/PREDICTIONS_LOOKS.md` Q1-2 |
| NEW-APP-2 | Capture BmAK reference frames of the body (noon / dusk / night / rain) from the operator's installed BmAK for a luminance reference (FOOTAGE.md exists; check coverage vs G3-04 step 3) | GRAB | todo | operator (plays BmAK) | NEW-APP-1, APP-2 | S | `Research/BatmobileGrab/FOOTAGE.md` |
| NEW-APP-3 | BmSDK live scrape of BmAK Batmobile material values + rendered colour (settles the stripped-graph combine rule). Briefs 7992-7994 (BmSDK on GOG copy) | GRAB | queued/low priority; hook offset invalid on repack exe | 7993/7994, Steam copy question | G3-04b | M | `tmp/freebuff/QUEUE_MAP.md` (2026-11-07 notes); `OPERATOR_PRIORITIES.md` Steam section |

### C. TRANSLATE (ledger rows, plans)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| T-21 | Appearance plan: 339 components, 172 classified (23 bake, 61 route, 88 drop, 0 unclassified); only 251/339 (74.0 %) faithful by plan | TRANSLATE | done (but "88 drop" conflicts with STAGES.md "never omit": 9140/9143 re-open them) | - | B-D04 | - | `Working/Appearance/APPEARANCE_PLAN.md` |
| T-MA1, T-MA2, T-MA6 | 19 slots/210 blocks; body albedo = solid colour (BODY_D texture not in grab); 24 TGAs bound -> 21 .ddsc | TRANSLATE | keep/done | - | - | - | `Working/Translation/T_ROWS.jsonl` |
| T-MA3 | Body albedo = base x Diffuse_Adjust, gain 1.0 (0x43/0x41/0x45); v2 corrects green byte to 0x40 | TRANSLATE | partial (`next`; v2 value queued) | 9032/9143 | APP-2 | S | `tmp/freebuff/reports/paint-plans-v2.md` M3 |
| T-MA4 | Gloss 0.60 body (v2: ch1 gloss 0.75, ch3 reflectivity 0.15, F0 0.0060) | TRANSLATE | partial (`next`; v2 queued) | 9032/9143 | APP-2 | S | `paint-plans-v2.md` §1, §2 |
| T-MA5 | Glass: SpecFresnel 0.45 / SpecGloss 0.92 derived; member assignment UNKNOWN | TRANSLATE | partial | one-variable probe (in game) | APP-3 | S | `windscreen-and-glass-plan.md` §0/§7 |
| T-MA7 | 10-tint palette menu all = BmAK colour, gloss 0.600 | TRANSLATE | partial (`next`) | NEW-APP-5 | APP-2 | S | `T_ROWS.jsonl` T-MA7 |
| 8131-8133 etc. (app-wetness-and-rain, app-per-pixel-reflectivity, app-reflectance-f0, app-anisotropic-highlights, app-emissive-mask-channel, app-glass-layers, app-wheels-and-tyres, app-cockpit-interior-materials, app-colour-ramp-*, app-damage-chapter-masks, app-microdetail-bake-plan, app-mud-and-dirt-default) | Closest-system reports for every dropped appearance class (D1-D14) | TRANSLATE | done (reports only, not in ledger beyond 8211) | - | 9140, 9143 | - | `GRAB_BACKLOG.md:1986`; `tmp/freebuff/reports/app-*.md` |
| 9032 | Third serial pass on T_ROWS: paint v2 numbers + new rows for the 12 texture refusals with a build action | TRANSLATE | queued | 9031 (driving/world rows), paint-plans-v2 (done), collision plans | 9033, 9140, 9143 | M | `tmp/freebuff/queue/9032-*` |
| NEW-APP-4 | Reconcile STAGES.md ("0 rows out/omitted") with T-21's 88 "drop" classes: each of D1 mud(41), D6, D7, D9, D10, D11, D12, D13, D14 needs a closest-system + gap + build action row or an operator-signed "no visual effect" (D11/D12 editor scaffolding is arguably not a feature) | TRANSLATE | todo (partly in 9143 list) | 9032 | 9140/9143, RC5 `complete` flag | M | `APPEARANCE_PLAN.md` §0; `STAGES.md` |
| NEW-APP-5 | Palette write: set all 10 palette tints to the T-MA3 colour and gloss 0.6 in the private palette .vmodc; confirm the `CCar.palette` hash pointer; read back; resolve "does tint override the baked s0 colour?" (palette tints REPLACE the authored body colour per T-MA7 why) | BUILD | todo (route found, write path not exercised in RC4: `tint-palette-impact.md` says no tint byte written anywhere) | NEW-APP-1 | APP-2 | M | `Research/JC3Grab/TINT_WRITE.md`; `tmp/freebuff/reports/tint-palette-impact.md`; `paint-slots-palette-verify.md` (4/32 slots match) |
| NEW-APP-6 | Verify the 15 "no source" paint slots (cb2/cb6/cb8/s0 half) once G3-09d2 gives the offsets; rewrite the apply plan so every slot has a source or an explicit UNKNOWN | TRANSLATE | todo | 9143, G3-07 | APP-2 | M | `tmp/freebuff/reports/paint-slots-palette-verify.md` |
| NEW-APP-7 | Texture/model budget ledger across all RC5 branches: model margin is only 123.7 KB (4,791.3 of 4,915) yet RC5 adds booster mesh (9106), tracker launcher (9103), flares, arch lamps, skins; each needs a KB allowance or a LOD trim plan | TRANSLATE | todo | 9106, 9103, 9142 | 9190 merge | S | `Builds/bm-RC4/receipt.json` step R9; `tmp/freebuff/queue/9106-*` |
| NEW-APP-8 | Reconcile texture-budget figures: `budget.json` says tree 33 tex = 5,380.9 KB and bound 5,380.9 "OVER" allocator cap 4,648; `build-d04...md` says bound 32 tex = 4,015.5 KB (86.4 %); V-01-RC2 says 5,855.8 of 7,065. The 4,648 KB is a self-imposed 90 % cap (MODLOG §76), the hard wall is 7,065 | VERIFY | todo | - | 9140 (cites 5,380.9), 9190 | S | `Builds/bm-RC4-appearance/budget.json`; `MODLOG.md:4100-4118`; `reports/build-d04-materials-textures.md` |

### D. BUILD (appearance trees)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| B-01 | Build scaffold, byte-identical control | BUILD | done | - | - | - | `Builds/bm-001/receipt.json` |
| B-02 | Split body into 11 movable parts + lamps; silhouette 99.97 % net (RC4 re-measure 99.9004 %) | BUILD | done | - | B-04 | - | `Working/Appearance/build_parts/parts_manifest.json` |
| B-03 | Emissive CarLight blocks + 8 lamp parts (24 RBMs, 4,576 faces) | BUILD | done | - | B-07 | - | `Working/Appearance/build_lights/lights_manifest.json` |
| B-04 | Parts module 42 -> 59 parts | BUILD | done (joints dropped: root cause TURRET-joint) | - | 9172 | - | `Working/Parts/bm_vehicle_parts.json`; `Builds/bm-RC2/verify/joint_trace.md` |
| B-07 | Light rig module (18 entries) | BUILD | done | - | - | - | `Working/Lights/bm_lightrig.json` |
| B-15 | Budget gate + 16 far-LOD trims | BUILD | done | - | - | - | `Tools/scripts/bm_budget.py` |
| B-D04 / bm-RC4-appearance | Appearance pipeline run: 25 RBMs, 33 .ddsc, P1 micro-detail bake (4 normals), D3 4 masks, R2 emissive atlas (UNBOUND), R4 glass | BUILD | done but unfaithful (12/23 rows) | - | RC5 | - | `Builds/bm-RC4-appearance/progress.md`; `texture_ledger.md` |
| B-14 / bm-RC4 | Release candidate, `complete:false` | BUILD | done-incomplete | - | RC5 | - | `Builds/bm-RC4/receipt.json` not_done |
| 9140 | RC5 textures: bake located pixel sets, state closest mechanism for chapter masks + Leather ramp, write cards for gaps; unfaithful 12/23 must fall | BUILD | queued | rc5 scaffold (9100), 9054, paint-plans-v2 | 9179 review, 9190 | L | `tmp/freebuff/queue/9140-*` |
| 9143 | RC5 paint: 4 channels (colour, F0, wetness), values read back from container | BUILD | queued | 9100, paint-plans-v2 | 9179, 9190 | M | `tmp/freebuff/queue/9143-*` |
| 9172 | RC5 moving parts (wheels, doors, canopy, trunk, aero, bays, recoil, jet): drivers on 59 parts | BUILD | queued | 9101 (entity roots), boost-selector plans | 9179, 9190 | L | `tmp/freebuff/queue/9172-*` |
| 9142 | RC5 lights, flares, beams (T-24/B-25) | BUILD | queued | 9100 | 9179, 9190 | M | `tmp/freebuff/queue/9142-*` |
| 9130 | RC5 mode pair + swap (B-12): battle silhouette carrier | BUILD | queued | 9122, 9121, 9050 exe swap consumer | 9190, APP-6 | L | `tmp/freebuff/queue/9130-*`; `GRAB_BACKLOG.md:1397` |
| 9050 | Entity-swap consumer in exe (is there a runtime swap?) | GRAB | queued | - | 9130 | M | `tmp/freebuff/queue/9050-*` |
| 9106 | Booster mesh (appearance-visible new geometry) | BUILD | queued | 9100 | model budget, silhouette | M | `tmp/freebuff/queue/9106-*` |
| NEW-APP-9 | Author/derive substitutes for the 8 absent pixel sets: Micropattern A/A_N/B/C (detail normal, derive from Batmobile_Microdetail or accept as invisible), Wheel_E (author arch-strip emissive from the 4 arch lamp geometry), Body_ColourRamp, Underlayer_Ramp, Aniso_ramp (import-only; closest = baked normal/spec or none) | BUILD | todo | 9054, 9140 | unfaithful count 12 -> 0 | M | `Working/Appearance/PIXEL_LOCATE.md`; `Builds/bm-RC4-appearance/texture_ledger.md` refused rows |
| NEW-APP-10 | Four D9 chapter masks: decide a static state (which chapter state is shown by default in BmAK Playable_Batmobile?) and route via `SupportDmgBlend`, a second material slot or vertex data; ask the operator what damage/dirt a player sees (answer so far: none) | BUILD | todo | NEW-APP-27 (operator fact), 9140 | texture ledger | M | `reports/app-damage-chapter-masks.md`; `texture_ledger.md` D9 |
| NEW-APP-11 | Colour ramps (D10, 3 rows) and Leather ramp (pixels present, 64x512, sampler absent in all 961 shader headers): bake the ramp into the seat/body diffuse offline; blocked on the lookup rule living in stripped material functions | BUILD | blocked | G3-04b dead end / NEW-APP-3 | cockpit leather, body look | M | `texture_ledger.md`; `reports/colour-ramp-in-material-members.md` |
| NEW-APP-12 | Window block probe: decode cb1 members (SpecGloss/SpecFresnel/DiffuseRougness/PropertyMap t3), settle which BmAK glass scalar goes where, per-layer mask (Glass_S R/G) and frame mask (`Batmobile_V2_GLASS_MASK` unbound) | BUILD | todo (UNKNOWN assignment) | oracle or one-variable in-game probe | APP-3 | M | `reports/app-glass-layers.md`; `windscreen-and-glass-plan.md` |
| NEW-APP-13 | Per-pixel reflectivity/roughness (D3 partial for brake disc, cockpit S, missile S, Nimbus S): cockpit S "R channel dead, packing unknown" -> decode packing; 4-level banded substitute shipped | BUILD | partial | `Int_Cockpit_S` packing | interior/wheel gloss | S | `coverage.md:60`; `reports/app-per-pixel-reflectivity.md` |
| NEW-APP-14 | Bind cockpit emissive (`Int_Cockpit_E` atlas built UNBOUND: 0 CarLight blocks use it) so dashboard screens glow; decide m_Emissive 15 on seat vs atlas | BUILD | todo | emissive mask channel UNKNOWN (`m_Emissive` mask not decoded) | APP-4 | M | `texture_ledger.md` R2; `reports/app-emissive-mask-channel.md` |
| NEW-APP-15 | Lens flares / light units (T-24, T-25, B-25: 17 flare entries; 8 flare rows glow-only today); light range 60/45 above fleet band 50 (Q1-7b out-of-domain) | BUILD | todo | 9142 | APP-4 | M | `GRAB_BACKLOG.md:1244,1587`; `Working/Q/PREDICTIONS_LOOKS.md` Q1-7b |
| NEW-APP-16 | Wheel/tyre look: front wheel lod2/4/5 "unlisted" in the wheel .lod; rim_radius 0.539 vs mesh (26 mm gap); tyre UV layout UNKNOWN (TYRES.md has none); brake disc glow; 4 wheel lod4/5 once unpacked (B-14) | BUILD | partial | - | APP-1 close-up | S | `reports/app-wheels-and-tyres.md`; `GRAB_BACKLOG.md:1956` |
| NEW-APP-17 | Residual Serpente geometry: B-15 left "Serpente panels not unbound (vanilla-identical)"; confirm no donor panel (bumper/fender/hood/window/lamp bodies, 41 part bodies) draws inside or through the Batmobile shell; V-02 only checks silhouette | VERIFY | todo | - | APP-1 | S | `GRAB_BACKLOG.md:1957`; `RESET_FINDINGS.md` §4 |
| NEW-APP-18 | Skin set decision + scope: D-5 resolved "extra Rebel Drop entries"; the user message adds Funhouse; confirm list (MK2, Jokerfied, Funhouse; damaged/Destroyed/Fire/Upgrade looks = 7 of 11 no carrier) | TRANSLATE | todo | operator | NEW-APP-19..24 | S | `reports/app-skins-and-variants.md` verdict |
| NEW-APP-19 | Skin body RBM sets: per skin 5 LODs x body + 4 wheels + parts via `bat_assemble.py`/`appearance_pipeline`; bone differences (40 bones Joker), socket differences (65/55/64/63), different light rigs (28/28/17) | BUILD | todo | NEW-APP-18, base car final | 20-24 | L | `Research/BatmobileGrab/VARIANTS.md`, `SKINS.md` |
| NEW-APP-20 | Skin materials + textures (MK2 replaces body+wheel materials; Joker 61 materials / 54 textures differ), same paint conversion as base | BUILD | todo | NEW-APP-19, base paint final | 21 | L | `app-skins-and-variants.md` §1-2 |
| NEW-APP-21 | Skin entity clone: per-skin leaf `.ee`/`.epe`/parts/lights/handling copies, budget per entity (is the 4,915 KB model / 7,065 KB texture cap per spawned vehicle or global resident? UNKNOWN) | BUILD | todo | G2-27 standalone hash UNKNOWN, 8793 | 22 | L | `Research/JC3Grab/STANDALONE.md` |
| NEW-APP-22 | Skin Rebel Drop entries: item/task rows, names/blurbs, icons, spawn table (B-13 pattern); T-WLD4/T-WLD6 name+desc strings were `blocked` | BUILD | todo | NEW-APP-21 | 23 | M | `Builds/bm-013/`; `RESET_FINDINGS.md` §2 |
| NEW-APP-23 | Skin icons (`textures/ui/vehicle_icons/<leaf>.ddsc`) rendered from each skin | BUILD | todo | NEW-APP-19 | 22 | S | `Research/JC3Grab/NAMES.md` |
| NEW-APP-24 | Skin verification: V-01/V-02/V-03 gates per skin + install dry run + in-game spawn of each | VERIFY/TEST | todo | 19-23, APPROVED_Q | R-1 | M | gate scripts `Tools/scripts/v0*_rc*.py` |
| NEW-APP-25 | Battle-mode silhouette definition: per-bone pursuit vs battle deltas (turret raise, body lift, wheel yaw/strafe stance, fin angles, bbox each) turned into either part angles on one entity or the second variant's visual set; T-MD13 transformation stance, T-MD8 turn-on-spot | TRANSLATE/BUILD | todo (POSES.md done; no build carries any) | D-2 re-resolved (a), U1 runtime swap UNKNOWN | APP-6, B-12 | L | `Research/BatmobileGrab/POSES.md`; `Working/Translation/T11_MODES.md`; `reports/battle-mode-transform-plan.md` |
| NEW-APP-26 | Transformation animation visuals (pursuit <-> battle) at BmAK key times, authored substitute where JC3 animation is short | BUILD | todo | 9172, NEW-APP-25 | APP-6 | M | `reports/mode-swap-trigger-closest-system-plan.md` |
| NEW-APP-27 | Reconcile APP-7 with operator facts (no visible damage stages, no scratches, explosion on zero health): disable JC3 damage visuals that could still show (dirt/damage blend, smoke at low health, part detach, tyre burst visuals); record which JC3 member each is | TRANSLATE/BUILD | todo | 9171 (health/explosion no-crash) | APP-7 | S | memory `bmak-gameplay-facts.md`; `GRAB_BACKLOG.md:135`; `Research/JC3Grab/DAMAGE_MODEL.md` |
| NEW-APP-28 | Rain/wet look: `Wetness_Refl_Fresnel` 0.6 not written (no formula); closest JC3 wetness system (D8) and RAIN pilot card | BUILD | partial (rule: not written) | JC3 wetness member semantics | RAIN card | M | `paint-plans-v2.md` M5; `reports/app-wetness-and-rain.md` |
| NEW-APP-29 | Silhouette margin: RC4 passes the 99.9 % gate by 0.0004 pp; every RC5 geometry add (booster mesh, tracker launcher, arch lamps, skin variants) must re-run `v02a_rc4.py` and recover margin (e.g. LOD1-3 hole closing) | VERIFY | todo | 9106 and others | V-02 on RC5 | S | `tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md` |
| NEW-APP-30 | LOD behaviour: 5 LOD distances / pop check, shadow LOD, and the Texture "resident" limit when LODs change (MODLOG §76 vehicle-vanish mode) | VERIFY | todo | - | APP-1 | S | `MODLOG.md:4100` |
| NEW-APP-31 | Dedicated hole/seam repair: BUD-1 gross holes 0.309 % / 0.2968 % (RC4) at part seams; 31 three-bone-tie faces; check visible gaps at canopy, turret, hatches | BUILD | partial | - | APP-5 | S | `Working/Appearance/build_parts/parts_manifest.json`; `Builds/bm-RC2/verify/geometry.md` |

### E. VERIFY (offline gates on RC5)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| V-01 | File + budget gates (Model <= 4,915, Texture <= 7,065) on RC5 | VERIFY | RC4 done GREEN, RC5 todo | 9190 merge | 9193 | S | `Builds/bm-RC4/verify/files.md`; brief 9191 |
| V-02 | Geometry/pose gates incl. pose renders and lights | VERIFY | RC4 done (8401a), 8401b (pose renders/lights) queued | 8401 split | 9192 | M | `Builds/bm-RC4/verify/geometry.md`; `tmp/freebuff/queue/9192-*` |
| V-05-looks | Predictions: 35 lines, 25 predicted, 9 UNKNOWN, 1 out-of-domain | VERIFY | done on RC4, must be regenerated for RC5 after 9140/9143 land | 9190 | Q-1 | S | `Working/Q/PREDICTIONS_LOOKS.md` |
| V-06 / V-07 | Install dry run + gate VX/approval request | VERIFY | RC4 done; RC5 queued (9192, 9193) | 9190 | APPROVED_Q | S | `Working/Q/APPROVAL_REQUEST.md` |
| 9179 | Review of RC5 body/world branches (textures, paint, parts, lights, modes) | VERIFY | queued | all 91xx branches | 9190 | M | `tmp/freebuff/queue/9179-*` |
| 9190 | Merge all branches into `Builds/bm-RC5` (22 checks) | BUILD | queued | 9179 + weapon review 9119 | 9191-9194 | L | `tmp/freebuff/queue/9190-*` |

### F. PILOT / TEST (needs the human operator)

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| Q-PILOT | Narrow cards so a small model can drive the game incl. looks cards (LOOK_STATIC, LOOK_CLOSEUPS, NIGHT, RAIN, HUD_CHECK) | PILOT | partial (cards written, not run) | APPROVED_Q | Q-1 | M | `tmp/freebuff/reports/pilot-card-looks-and-audio.md`; `Working/Q/PILOT/` |
| 8600 | Q-0: prove pilot cards on a simple car | PILOT | queued | APPROVED_Q | 8601 | M | `tmp/freebuff/queue/8600-*` |
| APPROVED_Q | `tmp/freebuff/APPROVED_Q.txt` (operator-only) | gate | absent | operator, V-07 on RC5 | every TEST row | S | `tmp/freebuff/queue/8601-*` header |
| Q-1 | Session 1: noon/dusk/night shots, canopy, parts at standstill, lamps (45 min est; 8 items) | TEST | todo | APPROVED_Q, 8600, RC5 verify | Q-4 | M | `GRAB_BACKLOG.md:1705`; `Working/Q/APPROVAL_REQUEST.md` |
| NEW-APP-32 | Paint calibration take (within Q-1 or a Q-1a): measure the body on-screen under fixed lighting against the NEW-APP-1 criterion; use G3-07 oracle or screenshot luminance; no retune by feel, produce a fix card | TEST | todo | NEW-APP-1, NEW-APP-2, G3-07 or screenshot path | APP-2 | M | `GRAB_BACKLOG.md:997` Done line; Q-4 rules |
| NEW-APP-33 | Glass/canopy probe take (Window cb1 one-variable build -> look) | TEST | todo | NEW-APP-12 | APP-3 | M | `windscreen-and-glass-plan.md` §7 |
| NEW-APP-34 | Close-ups: wheel/tyre, panel gloss, interior through canopy, no donor panels (NEW-APP-17) | TEST | todo | Q-PILOT LOOK_CLOSEUPS | APP-1/3 | S | pilot card report |
| NEW-APP-35 | Night + rain look: lamps, arches, beams, dashboard, wet reflection | TEST | todo | NEW-APP-14/15/28 | APP-4 | S | NIGHT.md / RAIN.md |
| NEW-APP-36 | Moving-part visual pass at standstill (turret, cannon pitch, Vulcan spin, hatches, canopy open/close, yoke, fan): no floating parts, pivots right | TEST | todo | 9172, TURRET-joint fix | APP-5 | S | `Working/Q/PREDICTIONS_LOOKS.md` ANI rows (4 UNKNOWN) |
| NEW-APP-37 | Battle-silhouette take (after B-12): both poses, transformation, swap trigger | TEST | todo | 9130, NEW-APP-25/26 | APP-6 | M | `GRAB_BACKLOG.md:134` |
| NEW-APP-38 | No-deform take: crash into wall/ram, shoot, RPG: body never deforms and shows no marks | TEST | todo | NEW-APP-27 | APP-7 | S | `GRAB_BACKLOG.md:1720` Q-1 item 6 / Q-3 |
| NEW-APP-39 | Skin takes: each skin appears in Rebel Drop with its icon/name and renders correctly | TEST | todo | NEW-APP-24 | APP-8 | M | `Builds/bm-013/` pattern |
| Q-4 | Fix loop (look failures become one-variable offline fixes, one extra session per session max) | TEST | ongoing | Q-1 results | Q-1 re-run | L | `GRAB_BACKLOG.md:1755` |
| Q-5 | Showcase recording | TEST | optional | QX | - | S | `GRAB_BACKLOG.md:1763` |

### G. RELEASE

| id | task | stage | status | blocked by | blocks | size | evidence |
|---|---|---|---|---|---|---|---|
| R-1 | Release = pipeline + edit specs only (BmAK meshes/textures cannot be redistributed); write RELEASE.md, `um publish check` | RELEASE | todo | QX | R-2 | S | `GRAB_BACKLOG.md:1773` |
| NEW-APP-40 | Make the appearance pipeline rebuildable from the user's own BmAK + JC3: remove hard-coded `E:\Modding\_BmAKgrab`, `E:\Games\Batman - Arkham Knight\...`, `OPENBLAS_NUM_THREADS=1` assumptions in `appearance_bake.py`, `grab_*`, `bat_assemble.py`; one-command grab->convert->build; document the 4 gate scripts | RELEASE | todo | final RC | R-1 | M | `reports/build-d04-materials-textures.md`; `Tools/scripts/appearance_bake.py` |
| NEW-APP-41 | Release checks for appearance outputs: confirm no BmAK asset (RBM, .ddsc, TGA) is inside the repo release folder; skins add 3 more asset sets to exclude | RELEASE | todo | - | R-1 | S | `GRAB_BACKLOG.md:1773-1779` |
| R-2 | KB field note (paint/texture-budget lessons: linear vs sRGB, 4,648 cap, glass BC3, no BC1 punch-through, no append geometry) | RELEASE | todo | QX | - | S | `GRAB_BACKLOG.md:1781`; `tmp/freebuff/QUEUE_MAP.md` "Do not" list |

---

## (a) What is done (brief)

- **Geometry**: Body mesh at true scale 7.026 x 3.495 x 2.271 m (T-G1), wheel Ø1.366 m, 5 LODs x 25 RBMs, 19 material slots, 210 blocks (185 CarPaintMM + 25 Window). `Working/Appearance/progress.md`: geometry 25/25, materials 19/19. `Builds/bm-RC4-appearance/progress.md`.
- **Part split** (B-02): 11 cut parts + 8 lamp parts; 59 parts in the parts module; silhouette 99.9004 % (limit 99.9) in RC4; 59/59 census; 77/77 interaction points in band. `Builds/bm-RC4/verify/geometry.md`, `tmp/freebuff/reports/verify-v02a-silhouette-census-collision.md`.
- **Lights/emissive** (B-03/B-07): 8 lamp parts, 24 CarLight blocks, 18-entry rig. `Working/Appearance/build_lights/lights_manifest.json`.
- **Paint research**: BmAK body colour decoded (`COLOUR_PARAMS.md`); JC3 palette, tint parameter, cb2/cb6 slot names, write path (palette .vmodc float) located (`TINT_WRITE.md`); v2 paint table with audited numbers (`paint-plans-v2.md`); closest-system reports for all dropped classes.
- **Budgets**: Model 4,791.3 / 4,915 KB (R9 gate, 16 far LODs trimmed); textures 33 .ddsc 5,380.9 KB vs 7,065 hard (see NEW-APP-8 for the inconsistent figures). MODLOG §76 explains the 4,648 KB fitted cap and the vanished-vehicle failure.
- **Skins research**: 11 BmAK looks inventoried; D-5 resolved (extra Rebel Drop entries); zero skin builds (`app-skins-and-variants.md`).
- **In-game history** (older builds, not RC4): car visible and textured in test-065; user compared vs BmAK: white racing stripes, tan mud, glossy sheen (MODLOG §76-77, later fixed by switches); white-violet 0x837d86 in daylight with ALB-2 (RESET_FINDINGS §2). Entry/exit of the Batmobile was confirmed in game (T-13R, RESET_FINDINGS §3).

## (b) BLOCKERS (root first)

1. **ROOT-1: Test ban / APPROVED_Q.txt absent.** Everything labelled TEST is blocked by `tmp/freebuff/APPROVED_Q.txt`, which only the operator writes, plus the Q-0 proof of pilot cards (8600) and V-07 on RC5 (9193). Nothing about RC4 or RC5 has been seen in game since the research reset (`STATUS.md`: 0 rows verified in game).
2. **ROOT-2: No decoded BmAK -> JC3 colour conversion** (RESET_FINDINGS §2, R-4). Blocked by: (i) stripped material-function graphs (G3-04b dead end on disk), (ii) UNKNOWN what writes palette -> cb6 and no RDEF names (G3-04d/e, G3-09d), (iii) no runtime oracle (G3-07 open, 07a done, 07b queued), (iv) no BmAK reference frames (FOOTAGE.md coverage unchecked). Operator fallback rule (in brief 9143): ship the exact decoded colour and accept the brighter JC3 look; that must be confirmed as the acceptance criterion (NEW-APP-1) or APP-2 stays blocked.
3. **ROOT-3: Serial apply chain** (9031 -> 9032 -> 9033) edits `T_ROWS.jsonl` and pins; 9140/9143/9172 wait on the rc5 scaffold (9100) and on paint/pixel-set reports (9054 queued with its report missing). 9179 -> 9190 -> 9191/9192/9193 -> approval is the single-file path to a testable RC5.
4. **ROOT-4: Pixel sets that do not exist on disk.** 8 rows: 0 found in 2019 readable packages; 1247 packages unreadable; 5 are import-only (names referenced, no Texture2D), 3 have no name-table entry. These can only be derived/authored (NEW-APP-9) or settled by BmSDK/runtime (NEW-APP-3).
5. **ROOT-5: JC3 shader capability gaps** (no chapter selector, no ramp sampler, no per-layer Window slots, no aniso/emissive-mask channel decoded): 0/961 reflection headers mention these. They are closest-system+gap items, not valid "no system" answers (STAGES.md); each needs an authored substitute (2nd slot, per-vertex, bake).
6. **ROOT-6: Entity-swap trigger UNKNOWN (U1)** blocks the battle silhouette (APP-6), and the per-entity budget question blocks skins (APP-8). 9050/9130 own these.
7. **Downstream chains**: APP-2 <- NEW-APP-1,2,5,6, 9143, G3-07; APP-3 <- NEW-APP-12; APP-4 <- NEW-APP-14,15, 9142; APP-5 <- 9172 + JOINTS-v2 (needs 2 appended hinge constraints in batmobile.physicsc, Parts/Collision landmarks); APP-8 <- all of APP-1..6 final (skins clone the final car); R-1/R-2 <- QX (all Q passed or accepted omissions).
8. **Cross-landmark**: booster mesh (9106), tracker/EMP visuals, collision boxes (9141, 2 of 3 boxes missing), flares (9142) all consume the model budget (123.7 KB spare) and the silhouette margin (0.0004 pp).

## (c) Open questions for the operator (player knowledge)

1. In BmAK (not JC3), what colour does the Batmobile body read as in noon sun, shade, and night: pure black, charcoal, gunmetal blue? Is it matte or satin; is there visible reflection of the sky/city (wet streets) on the body? (the pre-reset JC3 user comparison said "monochrome matte black/gunmetal").
2. Do you accept "exact decoded BmAK colour, brighter under JC3 lighting" as the pass criterion for APP-2, or do you want it to look as dark as BmAK in JC3 (which means a non-decoded gain, i.e. a compromise)? (This is currently only a rule in brief 9143.)
3. Does the BmAK body show any dirt, mud, rain beading or damage-chapter stages in normal play (D1/D7/D9 classes)? Operator fact so far: no damage stages. Is there ever mud on tyres/arches (story chapters)?
4. Canopy: is the interior (seat, dashboard, screens glowing, steering yoke, Batman or Rico visible) clearly visible through the glass from the third-person camera? Is the glass tinted, reflective, or clear from outside; does it fog/rain-bead?
5. Cockpit: do the dashboard screens glow visibly from outside at night? Is there interior light?
6. Wheels: do the rim/brake discs glow? Are there wheel-arch lights always on, only in battle mode, or only at night? Do the wheels visibly turn sideways in battle mode?
7. Battle mode: what exactly changes visually: turret raise, body lowering/raising, wheel yaw, side armour plates, fins? Is the transformation animated and how long?
8. Skins: which exact skins do you want as Rebel Drop entries (Standard, MK2, Jokerfied, Funhouse, any DLC Tumbler/Arkham Origins variants)? Are Destroyed/Fire/upgrade-level looks (Missile_Upgrade, Nimbus Power Cell, Stagg Battery) wanted as visual variants or ignored?
9. Rain: in BmAK does the Batmobile look wet and bead water on the body/glass in rain; is that a must-have?
10. Any badge/decal on the car (bat emblem on hood/roof, tail design)? (BmAK decals are geometry per `MATERIALS`; confirm none are missing.)
11. Is it acceptable that the car's headlight/tail lamp flares are glow-only until T-24/B-25 lands?

## (d) Risks / unknowns that can add time

- **Colour has no ground truth path.** If the operator rejects the "exact decoded" rule, the work reverts to calibration by measurement (G3-07 oracle + G3-09 vanilla paints), which could take many in-game iterations plus a runtime tool that is still `open`.
- **Texture/model budgets**: model spare 123.7 KB; vehicle vanishes when budgets are blown (MODLOG §76: whole entity + collision never appear). RC5 adds meshes and textures; failure mode is catastrophic and only visible in game.
- **Silhouette gate margin 0.0004 pp**: any added geometry could flip V-02 to red and force LOD retuning.
- **Per-entity vs global budget unknown** decides whether three skins fit; may force skins to spawn only one at a time, or share textures.
- **Entity-swap runtime (U1)** may have no data-driven solution; battle pose then rests on part angles of one entity (partial fidelity, which the lore-accuracy rule says to amend, not accept).
- **Unreadable packages (1247 of 3266)** could hide the missing pixel sets; BmSDK port (GOG exe offset invalid) uncertain.
- **JC3 shader members** (Window cb1 assignment, m_DiffuseWrap role, emissive mask channel) may need several one-variable in-game probes; each costs an operator session.
- **Serial ledger chain** and **similarity-guard stripping** of briefs (QUEUE_MAP 2026-11-08) have repeatedly starved the queue; every brief needs unique text.
- **Operator availability**: Q-1 is 45 min, but fix loop allows only one extra session per session; look fixes that need a rebuild + reinstall (383 MiB drop, 9 files) cost much calendar time.
- **Release scope**: R-1 allows only a pipeline release; pipeline reproducibility on other machines (hard-coded E:\ paths, OpenBLAS env, GOG vs Steam) is untested.
- **Doc drift**: `STATUS.md` says 145/216 rows evidenced, `complete:false`; ledger counts have drifted before (RESET_FINDINGS §5). Tracker rows I could not verify: G3-03, G3-05c, G3-09b exact state.

## (e) Estimate of remaining effort

Assumptions: ~100 small-model briefs/day, each brief about 1 agent-session (7-15 min, EST 45-60); human-gated TEST steps limited by operator hours.

| bucket | agent-sessions (briefs) | notes |
|---|---:|---|
| Finish RC5 appearance branches (9032, 9054 re-run, 9140, 9143, 9172, 9142, 9106 visual part) incl. fix/review briefs | ~35-45 | most are L-sized single briefs that tend to need split/rework (cf. 8401, 8134) |
| New offline tasks NEW-APP-1,4-9,13-17,27-31 | ~25-35 | mostly S; NEW-APP-9/10/11/12/14 M |
| Battle silhouette (9050, 9130, NEW-APP-25/26) | ~10-15 | gated on U1 |
| Skins (NEW-APP-18..24, 3 skins) | ~25-40 | cloned pipeline x3; the bulk after base car is final |
| Merge + verify (9179, 9190-9194, V-01..V-07 repeat after each fix) | ~12-20 | RC5 plus at least 2 rebuilds after Q fixes |
| Release prep (NEW-APP-40/41, R-1, R-2) | ~8-12 | |
| **Total offline** | **~115-170 briefs** | about **1.5-2 days of pure throughput**, realistically **5-8 calendar days** because of serial chains, 15-min-per-brief latency, reviews that rewrite later briefs, and rework |
| In-game (operator + pilot agent) | Q-0 + Q-1 + 2 fix sessions + skin take + battle take + night/rain = ~6-8 sessions of 30-60 min | needs APPROVED_Q and reinstalls; ~4-6 operator-days if parallel to offline work, each cycle (rebuild -> install -> look -> fix card) about 1 calendar day |
| **Total to a released appearance** | | **~12-18 calendar days** if the colour acceptance (NEW-APP-1) is answered "exact decoded"; **+7-14 days** (30+ days total) if it requires measured calibration with G3-07 oracle and BmSDK, or if the entity-swap (U1) has no solution and battle/skins need exe-level work. APPEARANCE has no hard dependency on collision/handling but shares the build merge (9190) and the Q-1 session with every other landmark. |

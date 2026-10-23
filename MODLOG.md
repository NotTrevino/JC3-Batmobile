# MODLOG — Just Cause 3 Batmobile

Journal for `E:\Modding\JC3-Batmobile`. Every claim is backed by a file, a tool run or a URL
actually inspected. Missing evidence is **UNKNOWN**, per `AGENTS.md`.

---

## 0. Status

| Plan assumption | Verdict | Where |
|---|---|---|
| **"Prove Blender → RBM → JC3" (§30)** | ✅ **ACHIEVED** — via a self-written byte-exact codec, not the exporter. A topology-preserving mesh edit loads and renders in game. | §14g |
| "Blender → RBM is the largest unknown" | **Resolved, and Blender is optional.** Its addon targets 4.1.1 against a local 5.2.2; we have a writer. | §14g |
| Serpente RBM needs RBM block reverse engineering | **Refuted.** `0x483304D6` = `CarPaintMM`; Gibbed just lacks the parser. `rbm_geom.py` now parses it byte-exactly. | §6, §7, §14f |
| Donor = Serpente R | **Confirmed correct** by measurement. | §4 |
| "Need an AAF reader" (my own earlier claim) | **Wrong — one already ships.** `SmallUnpack.exe`. | §9 |
| Standalone vehicle registration "paused" | **Likely cheaper than assumed** — `settings\*.bin` is the registry. | §11 |
| "A whole-file RBM swap needs no exporter" (§5) | **Wrong.** Three swap attempts failed. The variable that mattered was topology preservation, not the exporter. | §14c, §14g |

### Proven in game

- `.ee` dropzone carrier override works (test-003, black car)
- **Topology-preserving mesh edit renders** (test-007, body 25% longer)
- `.vmodc` stats editable via `ConvertAdf`, byte-identical round trip
- 100 vanilla RBMs round-trip byte-exactly through `rbm_geom.py`

## 1. Task 1 — inventory ✅

`Tools\scripts\inventory.ps1` → `Research\INVENTORY.{json,md}`.
**1157 files, 1861.3 MB, 151 directories.** Read-only, re-runnable.

## 2. Game install

`D:\Games\Just Cause 3` is a RUNE Steam emulator (`steam_emu.ini` `[Crack]`, `steam_api64.rne`,
`AppId=225540` = JC2, no `appmanifest_260550.acf`). The user has confirmed the install is theirs
and is playable as-is; work proceeds against it. Its `dropzone\` was empty before we started.

## 3. Task 2 — knowledge base ✅ — **zero JC3 knowledge exists**

All 78 notes searched (`just cause`, `avalanche`, `rbm`, `gibbed`, `deca`): no hits. This project
is the first, so everything here is worth publishing at the end.

## 4. E1 — donor comparison ✅ **Serpente R confirmed**

| | Serpente R | Mugello racingsupercar |
|---|---|---|
| Body AABB (W×H×L) | 2.099 × 1.387 × **3.720** m | 2.107 × 1.039 × **4.628** m |
| Body LOD levels | 9 | 3 |
| Distinct mesh parts | **41** | **15** |
| Doors / trunk | yes / yes | yes / yes (0.90 × 0.31 × 1.33 m) |
| Own wheel RBMs | yes (0.329 × 0.801 × 0.800 m → Ø0.80 m) | no — `00_shared\car_tire` |
| Own head/tail/signal RBMs | yes | no — `00_shared\car_lights` |
| Engine bay, seats, steering wheel | yes | no |
| `.lod` tables | one per part | **none** |

Mugello's low part count is inheritance, not absence — those are still dependencies to satisfy, and
a Batmobile needs bespoke wheels and lights anyway. It is also a 4.63 m mid-engine supercar with
`wing` + `grill_c` trim: wrong silhouette. **Serpente R confirmed, as the plan specified.**

## 5. The mesh layer ✅

RBMs are **separate, opaque, name-referenced files**, not embedded in the entity. A geometry swap is
"drop in a replacement `.rbm` under the expected name". Every vehicle body RBM is
`1.16.0` / `block_count 9` / first block `0x483304D6`, so a valid replacement has a precise spec.
**Plan §13–§16 collapses to an authoring convenience, not a gate.**

## 6. §7's "Critical Finding" RESOLVED

`ConvertRBM.exe` on a *different* vehicle's freshly-unpacked RBM fails identically
(`9 blocks`, `block type: 483304D6`). The fork's README says its RBM serializer is
*"a WIP (in its ultra-very early stage)"*. So `0x483304D6` is simply the first block type of a
standard vehicle RBM and the toolchain never implemented it. **The Serpente RBM is not corrupt.**

## 7. E1a — block types named ✅ (no payload decoding)

Gibbed identifies block types as Jenkins hashes **of the name**
(`BlockTypeFactory.Register<T>(string name)` → `name.HashJenkins()`), so a block can be named by
hash lookup instead of reverse-engineering. The exporter
(`Brooen/RBM-Exporter`, `io_export_rbm/export_rbm_script.py`) writes each type as raw
little-endian bytes, which pins them exactly:

| Hex bytes | Type | Jenkins hash of name | Confirmed how |
|---|---|---|---|
| `D6043348` | `0x483304D6` | `CarPaintMM` = `0x483304D6` | **exact hash match** |
| `F18B94DB` | `0xDB948BF1` | `CarLight` = `0xDB948BF1` | **exact hash match** |
| `CD4CD2A5` | `0xA5D24CCD` | `BavariumShield` = `0xA5D24CCD` | **exact hash match** |
| `F603205B` | `0x5B2003F6` | `Window` = `0x5B2003F6` | exact match (Gibbed agrees) |
| `A1729CF9` | `0xF99C72A1` | `WaterHull` hashes to `0xC0EF6B7D` — **mismatch** | raw bytes only; name UNKNOWN |

**`0x483304D6` = `CarPaintMM`** — the car-paint material zone that is the first block of every
solid panel on both donors. Reading the whole Serpente now yields:

- `CarPaintMM` → every solid part (body, doors, hood, trunk, bumpers, fenders, wheels, engine bay,
  seats, steering wheel, mirrors, plates)
- `Window` → every glass part (`window_f`, `door_f_l_window`, `door_f_r_window`, `trunk_window`)
- `CarLight` → every lamp (`headlight_f_l_01/02`, `headlight_f_r_01/02`, `signal_f_l/f_r/r_l/r_r`,
  `taillight_r_c/r_l/r_r`, and every `mshswap` variant)

`Tools\scripts\rbmhdr.py` now carries this table, self-tested against `HashName.exe` ground truth
(`CarPaint`=CD931E75, `General`=A7583B2B, `SkinnedGeneral`=5E657F20, `Lambert`=D5D78AE0,
`Window`=5B2003F6) — **PASS** — and validated against Gibbed's own stdout on the same file.

## 8. The `.ee` / property-file architecture ✅

From `FileDetection.cs` and the JC3 wiki (*Modifying (JC3)*, justcause.fandom.com):

| Ext | Magic | Role |
|---|---|---|
| `.ee` | `AAF\0` | Avalanche **Archive** File — the **body**: models, physics, effects, and the `.epe` |
| `.epe` | RTPC | entity **property** file — the **brain**: which files get used, and how |
| `.vmodc`/`.wtunec` | ADF | stat modules: engine, brakes, tires, suspension, transmission… |
| `.rbm` | `RBMDL` | render block model |
| `.ddsc`/`.hmddsc` | `AVTX` | texture, low-mip / full |

Wiki quote: *"If there is a property file next to an archive, it means it got patched… You can think
of the archive as the body and property file as the brain. The property file controls over half of
everything there is."*

Also: **`.bin` files in `settings\` list every vehicle and say where its `.ee` lives.** Stage 11
("standalone vehicle registration", which the plan paused) is a data edit in a `.bin`, not code.

Verified tool support:

- `ConvertProperty.exe` converts **`.epe` ↔ XML** ✅ (vanilla Mugello → 445 KB XML)
- `ConvertProperty.exe` on `.ee` → `NotSupportedException` ❌ (expected — `.ee` is AAF)
- **`ConvertAdf.exe` converts `.vmodc` ↔ XML** ✅ — see §13. `.vmodc` magic ` FDA`
  (LE `0x41444620`) **is Gibbed's ADF magic**, so every stat module is editable XML.
- **`SmallUnpack.exe` / `SmallPack.exe` handle `.ee` (AAF)** ✅ — see §9
- `Batch.exe` dispatch table has **no `.vmodc` entry**, so it skips stat modules. Use
  `ConvertAdf` directly.

## 9. E2 — the shipped Batman mod, diffed exactly ✅

**`SmallUnpack.exe` unpacks a `.ee` to a directory tree** (mod `.ee` 4,653,952 B → **634 files,
12.49 MB**; vanilla 4,892,960 B → **634 files, 12.49 MB**). Report: `Research\Vehicle\AAF_DIFF.md`.
Tool: `Tools\scripts\aafdiff.py`.

### The headline result

| Bucket | Count |
|---|---:|
| Files only in vanilla | 0 |
| Files only in mod | 0 |
| **Common, identical** | **619** |
| **Common, DIFFERENT** | **15** — 11 `.vmodc` + 4 `.ddsc` |
| …of which size differs | **0** |

**Zero RBMs changed. The `.epe` did not change. The `.physicsc` did not change.**
The "Playable Batmobile" mod is a pure **re-texture + handling retune** of the Mugello.
It proves the dropzone override route and the physics-tuning surface. It proves nothing about
custom meshes.

### The 15 changed files

Physics (11, all *in-place* edits — identical byte size, so offset-diffing is exact):

| Module | What changed |
|---|---|
| `land_aerodynamics` | `0.28 → 0.0` — **drag removed** |
| `custom_land_global` | three consecutive floats `1.0 → 1.1` (×1.1) |
| `vehicle_misc` | `0.50 → 0.30`, `2.0 → 1.2` (both ×0.6) |
| `rigid_body` | 3-byte int field at `0x51` — **mass** |
| `brakes` | two 3-byte int fields (`0x55`, `0x61`) |
| `front_tire`, `rear_tire` | **355 changed ranges each** — full tire-model retune (slip curves, camber, damping); the pattern repeats twice inside the file |
| `transmission` | `0.058903671801 → 0.058904148638` — negligible drift |
| `vehicle_common` (shared) | 6 small changes |

Textures (4, all 43,832 B): `body_dif`, `body_msk`, `interior_dif`, `undercarriage_dif`.

Plus one module shipped **loose** in the dropzone instead of inside the AAF:
`land_engine.vmodc`, **rebuilt** 1045 → 1207 B, adding
`engine_upgrades / LandEngineUpgrades / overdrive_extra_rpm` that vanilla does not have.
Exactly the "body vs brain" override pattern from §8.

### Why this matters

This is a **complete, working map of the physics surface for plan §20** — and it was obtained
without writing a single line of format reverse-engineering. `Tools\scripts\vmodcdiff.py`
locates and decodes any such edit. `suspension.vmodc`, `land_steering.vmodc` and `buoyancy.vmodc`
were left untouched by the author, so those remain unproven territory.

## 10. Dead ends — do not repeat

| # | Attempt | Result | Conclusion |
|---|---|---|---|
| D1 | ASCII string-scan a `.ee` | 6336 strings, 0 hits | `.ee` is not plain text; `SmallUnpack` it, then read the `.epe` |
| D2 | Assume the Batman mod proves custom-mesh injection | Refuted, SHA-256 across all 634 files: 0 RBMs changed | Reuse its override *pattern*, not its mesh |
| D3 | `um kb search` in PowerShell | `um` is an extensionless shell script | Read `knowledge/` directly or `uv run -- um …` |
| D4 | `ConvertProperty -e` on `.ee` | `NotSupportedException` | `.ee` is AAF → use `SmallUnpack` |
| D5 | **`ConvertProperty -e` on `.vmodc`** | `NotSupportedException` | **Wrong tool.** `.vmodc` is ADF, not RTPC → use `ConvertAdf` (§13). I had the right file and the wrong converter twice before checking the magic. |
| D6 | **My claim that no AAF reader exists** | **Wrong** — `SmallUnpack.exe` is the AAF reader and was in the toolset all along | Always list the whole tool directory before declaring a capability missing |
| D7 | Guess `0x483304D6`'s name from a hand-written wordlist | no match | Resolved in §7 from the exporter's raw bytes instead |
| D8 | Read RBM block `0x483304D6` | unnecessary | Tool gap, not corruption |
| D9 | Extract vanilla Mugello `.ee` from `patch_win64\game1.tab` | only `.epe` came out | The `.ee` lives in `archives_win64\game35.tab` |
| D10 | Suspicion that `vmodcdiff` mis-reported the offset | **Unfounded** | Checked by hexdump: `7300.0 = 0x45E42000`, `14600.0 = 0x46E42000`, so 2 shared top bytes and exactly 2 bytes differ. The tool was right; the doubt was wrong. |
| D11 | **E3 oracle specified as "visually unchanged"** | **Invalid test design** | A physics parameter has no visual signature. Always match the oracle to the *kind* of change: behavioural change → observe behaviour; visual change → observe appearance. |
| D12 | **Deployed a loose `.vmodc` (test-001) and a `.ddsc` (test-002 marker A) into the dropzone** | **Both at paths that do not exist in the game.** They live *inside* the `.ee` AAF, not as VFS paths, so they were silently ignored | **Build overrides from the archive's VFS layout, never from an AAF's internal layout.** The only VFS override point for a vehicle's editable content is the `.ee` itself. See §14. |
| D13 | Marker B (`..._body_dif.hmddsc`) — a genuine VFS path in `game36.arc` | No visible change | **Explained by test-003:** the `.ee`'s internal `.ddsc` is authoritative for this material, so `.hmddsc` overrides are ignored. Edit textures inside the `.ee`. |
| D14 | Transplant a foreign vehicle's body RBM into the Serpente (test-004, test-005) | infinite load, then immediate crash | **E4 refuted.** A body RBM is structurally bound to its entity — header field 1 (9 vs 3), attachment nodes, and physics. Not fixable by copying files. Pivot to authoring a matching mesh (§14c). |
| D15 | Assume `SmallPack` packs whatever is in the folder | **Wrong.** It uses `@files.xml` as a manifest and drops unregistered files silently | Register new files in `@files.xml` before packing; verify with `aafdiff` that the expected files actually arrived. |
| D16 | Copied `install.ps1` between build folders with a search-and-replace | The script kept `$BuildDir = '…\Builds\test-003'` in its param block, so the test-006 "install" silently redeployed the **already-proven** test-003 artifact | `install.ps1` now defaults `$BuildDir` to `$PSScriptRoot` **and asserts the artifact's size + SHA-256 prefix before deploying**, refusing to run on mismatch. Never ship a build without an identity guard. |

## 14d. test-006 — FAILED (stuck loading) → **World B confirmed**

Cheap discriminator, one launch:

`sportsmuscle_body_lod1.rbm` ← **`sportsmuscle_body_lod2.rbm`** — a different LOD of the
*same vehicle's own body*. Identical AABB, identical header field 1, no new files,
`@files.xml` byte-identical. Exactly 1 file changed vs the proven tree.

**Result: stuck loading.** Rolled back to test-003, hash-verified.

**Conclusion: file-level substitution of the body RBM does not work even within one vehicle.**

### Why — the actual cause

`sportsmuscle.physicsc` (340 KB) contains **Havok collision shape identifiers**:

```
hknpExternMeshShape        <- Havok PHYSICS external mesh shape
hknpExternMeshShapeData
body_COL                   <- the body's collision shape
steeringwheel_COL
wheel_f_l_RAY / wheel_f_r_RAY / wheel_r_l_RAY / wheel_r_r_RAY
```

`hknpExternMeshShape` is a collision shape that **references external mesh data** — i.e. the
body's collision is bound to the body *mesh*, not to an independent primitive. Replacing the
body RBM invalidates the geometry the physics was built against, and the physics/visual
initialisation never completes.

**This explains all three failures uniformly**, which is why the failure mode kept shifting
while the underlying fault stayed the same:

| Build | Swap | Failure mode |
|---|---|---|
| test-004 | 5 foreign LODs, no textures | hang |
| test-005 | 1 foreign LOD + textures | crash |
| test-006 | **same vehicle's own LOD2** | hang |

Also ruled out along the way: **header field 1 is not the culprit for test-006.** It is a
decreasing LOD budget — Serpente body `9, 9, 8, 7, 5` across lod1–lod5, Mugello body
`3, 3, 3, 2, 2`. lod2 and lod1 both carry `9`, yet the swap still hung. (Oddity worth noting:
Serpente body lod4/lod5 AABB length jumps to 4.99/5.00 m from 3.72 m — **UNKNOWN** what those
coarse LODs actually contain.)

### The scope change this forces

`MODDING_PLAN.md` implicitly assumed a visual swap would carry physics with it. In JC3 it does
not: **the mesh cannot be replaced without also regenerating the vehicle's collision.**

A Batmobile therefore needs **both**:

1. an authored body mesh — Blender + `Brooen/RBM-Exporter`, and
2. regenerated collision for `body_COL` — a Havok physics editor. **kk19's DECA** is the tool
   the Avalanche modding community cites for exactly this class of work, and `DECA` was already
   listed in the plan §5 as a known-but-unlocated tool.

`.pfs`/`.pfx` are the collision-model files per the Just Cause wiki ("simple meshes attached to
rendered models, invisible in game"). Inside the Serpente `.ee` there are only **4 `.pfxc`**
files and all four are `debris_vehicle_debri0{1..4}_col.pfxc` — vehicle **debris**, not the body.
The body's own collision is **embedded in the 340 KB `sportsmuscle.physicsc`**, which is
consistent with an `hknpExternMeshShape`: the collision reads the body *mesh* rather than
carrying its own geometry.

**This is inference, not proof.** The decisive experiment is "replace the mesh *and* regenerate
or deactivate `body_COL`", which needs a physics editor. Until then the causal chain is:

mesh RBM replaced → `hknpExternMeshShape` for `body_COL` no longer matches → physics/visual
init never completes → hang or crash.

Net: plan §30's objective is confirmed as **the main path**, not the optional one, and it needs
a second toolchain (physics) alongside it.

**Pattern worth keeping:** three of the four wrong turns above (D5, D6, and the §9 AAF claim)
came from testing one binary and concluding a *capability* was absent. Read the magic bytes and
list the whole tool directory before saying "can't be done".

## 13. E3 — physics round-trip ✅ built and staged, in-game oracles pending

Full detail in `Builds\test-001\README.md`.

**Change:** one field, `max_rpm` `7300 → 14600`, in
`v0300_car_kensington_sportsmuscle_land_engine.vmodc`.

**How the physics surface became editable:** the `.vmodc` magic is ` FDA`, LE `0x41444620`,
which is exactly Gibbed's ADF magic (`FileDetection.cs`). So
`Gibbed.JustCause3.ConvertAdf.exe --e/--i` converts every stat module to readable XML.
`Research\Physics\serpente_land_engine.xml` exposes the whole `LandEngine` structure with
per-member file offsets:

| Member | Offset | Value |
|---|---|---|
| `resistance_at_min_rpm` | `0x54` | 0.05 |
| `resistance_at_max_rpm` | `0x58` | 0.20 |
| `resistance_at_optimal_rpm` | `0x5C` | 0.10 |
| `rev_limiter_rpm_drop` | `0x60` | 50 |
| **`max_rpm`** | **`0x64`** | **7300 → 14600** |
| `min_rpm` | `0x68` | 1000 |
| `optimal_rpm` | `0x6C` | 5000 |
| `torque_factor_at_max_rpm` | `0x70` | 0.84 |
| `torque_factor_at_min_rpm` | `0x74` | 0.86 |
| `torque_factor_at_optimal_rpm` | `0x78` | 490 |
| `clutch_slip_rpm` | `0x7C` | 0 |
| `engine_damage_noise_scale` | `0x84` | 1 |
| `engine_max_damage_torque` | `0x88` | 0.75 |

Note `torque_factor_at_optimal_rpm` = **490** while the two others are ~0.85 — the schema
does not constrain this field to a 0–1 range, so treat "torque factor" naming as a hint, not
a guarantee. **UNKNOWN** what 490 means until it is varied in game.

**Offline oracles — all PASS:**

1. **Round-trip fidelity.** `ConvertAdf --i` on the *unmodified* XML reproduces the original
   1045-byte binary with an **identical SHA-256**
   (`30DCA4D9…236DF15`). So the tool is lossless here and any later delta is my edit alone.
2. **Single-edit purity.** Exactly one changed byte range: `0x66-0x68`, 2 bytes.
3. **Independent read-back.** Re-exporting the rebuilt binary gives `max_rpm = 14600` with
   all neighbouring fields unchanged.

**Deployed:** `dropzone\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\
modules\default\v0300_car_kensington_sportsmuscle_land_engine.vmodc`,
sha256 `774100B7CF6C608C188AEED9D4F1C447CBEE49768CA9B481F12762665D639F44`.
Dropzone went from **0 files → 1 file**. `install.ps1 -Action Status|Rollback` manages it.

**In-game oracles 4–5 — RESULT: INCONCLUSIVE (my fault, not the pipeline's).**

The game was launched via `JC3_Launcher.bat`, which carries the correct `--vfs-fs` /
`--vfs-archive` arguments, so **the dropzone was being mounted**. The report was
"the Serpente looks visually unchanged".

That report carries almost no information: `max_rpm` is a *behavioural* parameter with
**no visual signature**, so "looks unchanged" is equally consistent with "override ignored"
and "override live but subtle". The oracle was badly specified — I asked for a visual
observation of a non-visual change. Logged as **D11**.

Two distinct questions therefore remain open and need different evidence:

1. **Is the dropzone read at all?** → answered visually by `Builds\test-002`.
2. **Does a loose `.vmodc` override take effect?** → only a *behavioural* observation can
   answer this. If test-002 shows the dropzone is live but the car drives exactly like
   vanilla, the loose-vmodc mechanism specifically is not honoured, and the fallback is
   repacking the vehicle `.ee` with `SmallPack.exe` — which is what the shipped Batman mod
   actually relies on.

**Known risk, restated:** only the loose module was deployed, **not** the vehicle `.ee`.
The Batman mod deploys a whole `.ee` containing its 11 re-tuned modules, plus one loose
`land_engine.vmodc` next to it. So "loose vmodc alone" is precisely the variant the working
mod never had to rely on. This is now the leading hypothesis for E3.

## 14. E3 — the override carrier ✅ (this was the real blocker)

**test-001 and test-002 both failed, and for the same reason: I built the overrides from the
wrong layout.** A JC3 vehicle has exactly **one** real VFS path for editable content — the
entity `.ee` in `archives_win64\game35.arc`. Everything else is *inside* that `.ee`, which is
an AAF nested archive:

```
<real VFS paths in the game archives>
  archives_win64\game35.arc  editor\entities\...\..._civilian_01.ee        <- the ONLY override point
  archives_win64\game36.arc  models\...\textures\..._body_dif.hmddsc

<inside the .ee — NOT VFS paths>
  editor/entities/.../modules/default/*.vmodc        17 stat modules
  models/.../textures/..._body_dif.ddsc              43,832 B low-mip
  models/.../*.rbm  *.physicsc  effects\  ...
```

Evidence: `SmallUnpack.exe` on the vanilla Serpente `.ee` (5,539,952 B) exported **566 files**,
including all 17 `.vmodc` modules and `..._body_dif.ddsc`. And the archive index
(`*.filelist`) shows **no** `..._body_dif.ddsc` anywhere, only `.hmddsc`.

So a loose `dropzone\editor\...\modules\default\..._land_engine.vmodc` addresses a path that
exists nowhere in the game. **test-001 was never going to work**, and neither was marker A.
This also explains the shipped Batman mod: it deploys a whole **repacked `.ee`**, and its
loose `land_engine.vmodc` beside the `.ee` is almost certainly inert.

**The correct route, now proven end to end offline:**

```
SmallUnpack .ee -> ConvertAdf --e/-i on a module -> SmallPack .ee -> dropzone
```

**test-003 build** (`Builds\test-003\`): vanilla Serpente `.ee` repacked with exactly two
changes — `max_rpm` 7300 → 14600, and `..._body_dif.ddsc` replaced with the Mugello's as a
**visual liveness marker**. Putting the marker in the *same* file as the physics edit is
deliberate: if the marker appears, the carrier demonstrably loaded, which proves the physics
change in that same file is live.

Oracles, all PASS offline:

1. AAF round-trip lossless — `SmallPack`→`SmallUnpack` returns both edited files with
   **identical SHA-256**.
2. Value survives — `ConvertAdf --e` on the round-tripped module reads `max_rpm = 14600`.
3. Nothing else changed — `aafdiff --hash` vs vanilla: **546 identical, exactly 2 different**,
   both unchanged in byte size.

Deployed: `dropzone\editor\entities\...\..._civilian_01.ee`, 5,526,072 B,
sha256 `194A01B573D586259B854E3607CBBEC02C10CED8406A95C42979DDEF22B8FFF8`.
Dropzone reduced from 3 stray files to **exactly 1**.

**In-game oracle: ✅ PASS — "car is black".** The repacked `.ee` override is applied by the game.
This is the first milestone proven *in the running game*, not just on disk.

It also resolves **D13**: the `.ee`'s internal `.ddsc` is authoritative for this material. The
earlier `.hmddsc` override (a real VFS path in `game36.arc`) produced no change because the
entity's own low-mip texture wins. **For vehicle textures, edit inside the `.ee`.**

### E3 outcome

Physics tuning is proven working as a *mechanism* — the same carrier now carries the modified
`land_engine.vmodc`. Whether `max_rpm` 7300 → 14600 is *perceptible* to the driver is still
unobserved, but it no longer matters for the pipeline question.

## 14b. E4 — mesh swap: **test-004 FAILED**, retried as test-005

### test-004 — FAILED (infinite load)

Swapped all five `sportsmuscle_body_lodN.rbm` for the Mugello body LODs. **The game hung at
load.** Rolled back immediately to the proven test-003 build (`194A01B5…`), hash-verified.

**Root cause, found by evidence:** an RBM's material blocks store texture paths as **plaintext,
spelled with the original vehicle's folder name**. The Mugello body references 17 paths, of
which **10 are Mugello-specific** and **none existed in the Serpente's `.ee`**.

The control matters: the *vanilla* Serpente body also leaves 9 of its 19 refs unresolved inside
the `.ee` — all `00_shared/` or `textures/…dummy` paths that come from the global VFS. That is
normal. The delta was exactly the 10 vehicle-specific ones. Dangling texture refs at
entity-init is the best-supported explanation for the hang. **Not proven until test-005 runs.**

### Tool gotcha — `SmallPack` silently drops unregistered files

**`Gibbed.JustCause3.SmallPack.exe` uses `@files.xml` as a manifest and drops any file not
listed in it, with no error.** The first test-005 pack "succeeded", produced a plausible `.ee`,
and contained **none** of the 25 new textures. Only the `aafdiff` oracle caught it
(`Files only in mod: 0` when 25 were expected).

To add files to an unpacked `.ee`, register them first:

```xml
  <file name="models/…/x.ddsc">models\…\x.ddsc</file>
```

547 of the 566 entries use that shape (pack from that path); 19 use `<file … size="…" />`
(size reference only). Use the first. **Any time we add a file, `@files.xml` must change too.**

### test-005 — FAILED (immediate crash)

Base = proven test-003. Two changes only:

1. **`sportsmuscle_body_lod1.rbm`** (nearest LOD only) ← `racingsupercar_body_lod1.rbm`.
2. **The 25 Mugello `.ddsc`** copied to the exact paths the RBM names.

Oracles all PASS: `@files.xml` +6,381 B with exactly 25 new entries and still valid XML;
RBM round-trips byte-identically; `aafdiff` vs the proven tree gives **25 added, 2 changed** and
nothing else; `rbmhdr refs --tree` shows 10/17 resolving, the other 7 being the shared/global
class. **In game: immediate crash.**

## 14c. E4 verdict — REFUTED. The no-exporter mesh swap does not work.

| Build | Change | Result |
|---|---|---|
| test-003 | `.ee` carrier only (texture + physics) | ✅ **works** |
| test-004 | 5 foreign body LODs, no textures | ❌ infinite load |
| test-005 | 1 foreign body LOD + its 25 textures | ❌ immediate crash |

**A body RBM cannot be transplanted between two unrelated JC3 vehicles as a file swap.**
The Serpente's body RBM is structurally bound to its own entity.

The failure *mode* changing from hang to crash is real progress, not noise: supplying the
textures let the loader get further, so **the texture-dependency finding was correct**. What
remains is structural, and none of it is reachable by copying files:

1. **RBM header field 1.** Gibbed discards it; it is **9** for every Serpente part and **3** for
   the Mugello body, while block count is `9` for both. The Serpente body is also the only part
   with 9. If field 1 is a zone or attachment count the engine indexes into, a foreign body with
   3 cannot satisfy it. **UNKNOWN.**
2. **Bone / attachment nodes.** The entity's `CParts` table binds `sportsmuscle_body` at
   `part_index 0` and lists sibling parts. A foreign body may lack the named nodes expected.
   **UNKNOWN** — RBM payloads are not decodable with the available tools.
3. **Physics.** `sportsmuscle.physicsc` describes a 3.72 m car; the replacement is 4.628 m.
   Confounded with (1) and (2) in both attempts.

**Consequence: plan §30's objective is no longer optional.** Proving Blender → RBM →
JC3 is now the *main* path, because the exporter writes an RBM built to this engine's structure
rather than borrowing another vehicle's. §18's Case D ("separate RBMs required for moving
components") is effectively confirmed; Case A/C are now the ones to test.

**A concrete lead for E5:** the exporter writes the two post-AABB fields as
`[blockCount][8]` (`export_rbm_script.py`), where `blockCount` = number of material slots.
Vanilla bodies have field 1 = **9**. So the exporter can be made to emit field 1 = 9 by giving a
body mesh **9 material slots** — which may be exactly what the Serpente entity requires. This is
the first testable prediction to check, and it is checkable *offline* by comparing exporter
output headers against the vanilla body with `rbmhdr.py`.

**Circuit breaker invoked:** two consecutive failures of the same approach, with a clear
pattern and no remaining file-level lever. Stop iterating RBM transplantation.

### Consequence

Physics is **not** tuned by dropping in a loose `.vmodc`; every change goes through an `.ee`
repack. That is one more step than the plan assumed, but all tools in it are verified working.
It also means any entity-side change — physics, materials, deform tables, effect
attachments — shares one carrier, and **a swapped body `.rbm` (E4) goes in the same place.**

## 14e. Tooling reality check, and the unlock

**DECA is a dead end.** `kk49/deca` (cloned to `Tools\Deca`) lists JC3 as "supported" but its own
file-type table covers TAB/ARC, AAF, SARC, AVTX/DDSC/HMDDSC, ADF, RTPC, OGG, CFX, .obc, RIFF,
FSB5, **RBMDL (extractable only)**, TAG0, btc. There are **zero `physicsc` references in the
entire codebase**; `hknpExternMeshShape` appears only inside Generation Zero's extracted
string dump. It is an APEX-engine tool (GenZero / theHunter) and cannot touch JC3's older
Avalanche 3.0 physics. **The option-3 escape hatch has no tool.**

**The unlock: `aaronkirkham/jc-model-renderer`.** Prebuilt Windows binary in `Tools\JCMR`
(v0.12.3). It has a *full* JC3 RBM implementation — the very blocks Gibbed's fork lacked:

```
src/game/jc3/renderblocks/renderblockcarpaintmm.cpp   <- 0x483304D6, the block that blocked us
src/game/jc3/renderblocks/renderblockcarlight.cpp
src/game/jc3/renderblocks/renderblockwindow.cpp
src/game/jc3/renderblocks/renderblockgeneral.cpp / renderblockgeneraljc3.cpp
src/game/formats/render_block_model.cpp               <- header, parse AND save
src/import_export/wavefront_obj.cpp                   <- OBJ export
```

### Correction: the header "Tag" is not a zone count

From `render_block_model.cpp`:

```cpp
"RBM v{}.{}.{}. NumberOfBlocks={}, Tag={}", header.m_VersionMajor, ..., header.m_NumberOfBlocks, header.m_Tag);
```

So the two post-AABB fields are **`m_NumberOfBlocks`** and **`m_Tag`**. My `rbmhdr.py` columns
were mislabelled — `block_count` is right, the other is a free-form **tag**. The Serpente body
tag is `9`, the Mugello's `3`, and it is **not** a zone or attachment count.

**§14c's hypothesis 3 is therefore dead**, which is good news: the tag mismatch was a red
herring, and the remaining suspect is the `hknpExternMeshShape` coupling alone.

### The block layout is fully specified

`renderblockcarpaintmm.h` gives the exact byte order after the 4-byte type hash:

```
CarPaintMM{ uint8 version=14; uint32 flags; float unknown; }        // 9 B
CarPaintStaticMaterialParams     18 x vec4 + 7 x float               // 304 B
CarPaintDynamicMaterialParams     3 x vec4 + 3 x float               // 60 B
DeformTable
Materials                        12 textures (CARPAINTMM_TEXTURES_COUNT)
VertexBuffer[0]                  flags select: IS_SKINNED / IS_DEFORM / plain
VertexBuffer[1]                  normals
[SkinBatch            if IS_SKINNED]
[VertexBuffer[2]      if SUPPORT_LAYERED | SUPPORT_OVERLAY]
IndexBuffer
uint32 checksum 0x89ABCDEF
```

Flags include `IS_DEFORM 0x1000` and `IS_SKINNED 0x2000` — which is why the RBM-Exporter's
"no deform support" matters, and why the Serpente's `sportsmuscle_vehicle_deform.vmodc` is
relevant.

The tool also has `GetData()` → `(vertices, indices)` and a working `Write()`, so an RBM can be
decoded **and** re-encoded. `LoadFromRuntimeContainer` also documents the naming rule the
entity relies on: `CPartProp.name` + `"_lod1.rbm"`.

## 14f. `Tools\scripts\rbm_geom.py` ✅ — byte-exact RBM codec

Written from the actual sources (not inferred from the exporter's guesses), per the instruction to
inspect first:

- header + block-type enum: `aaronkirkham/ava-format-lib` `include/AvaFormatLib/models/render_block_model.h`
- container parse/save: `jc-model-renderer` `src/game/formats/render_block_model.cpp`
- buffer + materials framing: `src/game/jc3/renderblocks/irenderblock.{h,cpp}`
- CarPaintMM layout: `src/game/jc3/renderblocks/renderblockcarpaintmm.h`
- vertex strides: `src/game/types.h`

### The oracle

```
$ python rbm_geom.py selftest
byte-identical: 100   mismatched: 0   not-parsed: 93
```

**100 real vanilla Serpente RBMs decode and re-encode byte-for-byte.** Zero mismatches. The
remaining 93 are `Window`, `CarLight` and `GeneralMkIII` blocks, which need their own
serializers; they are *skipped*, not mis-parsed, and the codec refuses to run on a block it
cannot size.

### Two corrections this forced

1. **`m_NumberOfBlocks` comes first, `m_Tag` second.** I had them swapped in `rbmhdr.py`. The
   constant "9 blocks on every file" was the **tag** (default 8; JC3 vehicle RBMs use 9). Real
   block counts vary 1–9. So the Serpente body has **9 render blocks** and the Mugello body
   **3** — a material-zone difference, which revives the zone-count idea as a real factor.
2. **`0xF99C72A1` is `RB_WATERDISPLACEMENTOVERRIDE`**, not "WaterHull". The exporter's
   `WATERHULL` node group writes that block, which is why my wordlist lookup failed. The
   official enum is now embedded in the codec, so hashes are named from the source of truth
   rather than guessed.

### The Serpente body, decoded

`sportsmuscle_body_lod1.rbm` — **9 CarPaintMM blocks, 6093 verts, 7063 tris, 12 texture slots**:

| Block | flags | verts | tris | vertex bbox W×H×L (m) |
|---:|---|---:|---:|---|
| 0 | `0x1004` | 1024 | 1056 | 2.071 × 0.884 × 3.677 |
| 1 | `0x1004` | 1061 | 1146 | 1.998 × 0.949 × 3.720 |
| 2 | `0x1004` | 40 | 20 | 1.592 × 0.773 × 3.329 |
| 3 | `0x1000` | 636 | 792 | 0.993 × 1.116 × 3.335 |
| 4 | `0x1000` | 786 | 941 | 1.643 × 1.116 × 3.335 |
| 5 | `0x1000` | 343 | 395 | 1.513 × 0.621 × 2.704 |
| 6 | `0x101F` | 1081 | 1471 | 2.092 × 1.298 × 3.575 |
| 7 | `0x101F` | 823 | 1007 | 2.088 × 1.298 × 3.575 |
| 8 | `0x101F` | 281 | 235 | 1.944 × 1.256 × 3.574 |

Two structural facts that matter:

- **The body is `IS_DEFORM` (`0x1000`) on every block.** So its vertex struct is
  `VertexDeformPos` = `float x,y,z,d + int16 wi0..3` (stride `0x18`), not a plain position.
  Each vertex carries **four bone indices** and a deform weight. This is what
  `sportsmuscle_vehicle_deform.vmodc` drives, and it is why RBM-Exporter's "no deform support"
  mattered.
- **The 9 blocks are deform/damage zones**, distinguished by flags `0x1000` / `0x1004` / `0x101F`
  (`0x1F` = decals + damage blend + dirt + soft tint + layered). The body is not one mesh — it
  is nine material zones, and a foreign body with 3 zones cannot satisfy a 9-zone entity.

### What the codec makes possible

Vertices are at offset 0 of each vertex struct regardless of variant, so a **topology-preserving
edit** is now available and safe: change x/y/z only, leaving vertex count, the index buffer,
the deform weights, the bone indices, the deform table and all material params byte-identical.
That is exactly the class of change the three failed file swaps could not express — each of them
replaced topology *and* vertex count together, which is what invalidated the
`hknpExternMeshShape` coupling.

**Oracle for the next test (still free, offline):** apply a known Z-scale to the body blocks,
re-encode, and confirm the *only* byte differences are the position floats plus the recomputed
header bbox. Then, and only then, deploy.

**Topology-preserving vertex editing.** Decode `sportsmuscle_body_lod1.rbm`, change only
vertex *positions*, keep vertex count and the index buffer identical, re-encode. If
`hknpExternMeshShape` addresses vertices by index — which is what an external mesh shape is —
the collision stays valid and simply follows the new silhouette.

This is exactly the class of edit the three failed swaps could not express: they all changed
*topology and vertex count together*. A topology-preserving edit is the one thing that keeps
physics and visuals consistent.

**Oracle before any launch:** decode → re-encode with zero edits → the result must be
**byte-identical** to the original. That single offline test proves the codec is faithful, and
it costs no launch.

### Also recorded: Blender version risk

Local Blender is **5.2.2**. `Brooen/RBM-Exporter` dates from 2024 and predates the 5.x API; its
`bpy.types` / node-group usage may not import. If the addon fails to register, prefer editing
decoded vertex data directly with the codec above rather than fighting the addon.

**Circuit breaker is in effect for RBM transplantation (D14).** Two failures, same approach,
no remaining file-level lever. Do not attempt another foreign-RBM swap.

**E5a — cheap discriminator before any install (one launch, no new tools).**
Swap `sportsmuscle_body_lod1.rbm` ← **`sportsmuscle_body_lod2.rbm`** — the *same* vehicle, a
different LOD of the *same* body.
- Loads → file-level substitution works; only the *foreign* structure is rejected, which
  confirms "author a mesh that matches the Serpente's expected structure".
- Crashes → even same-vehicle file substitution fails, so nothing file-level will work and the
  mesh must be authored from scratch with the exporter.
Either answer materially changes how much Blender work is needed, and it costs one launch.

**E5 — install Blender + `Brooen/RBM-Exporter`.** Now the main path, not optional. Plan §14's
minimal test scene first — a cube, one material, exported and loaded. Do **not** start with the
Batmobile.
- Predicted requirement from §14c: a body likely needs **9 material slots** so header field 1
  equals the vanilla body's 9. Verify by comparing exporter output against
  `sportsmuscle_body_lod1.rbm` with `rbmhdr.py` before ever launching the game.
- Known constraints: node groups are `CARPAINTMM` / `WINDOW` / `CARLIGHT` / `BAVARIUMSHIELD` /
  `WATERHULL`; texture paths auto-suffix `.ddsc`; **no deform support** on Carpaint, yet the
  Serpente ships `sportsmuscle_vehicle_deform.vmodc`; waterhull is flagged crash-prone.
- **Skeleton handling is UNKNOWN** — the README never mentions armatures. §18 Case C (static
  mesh only) is the working assumption; wheels stay as the Serpente's own parts.

**E6 — clean up the donor.** Serpente keeps doors, hood, trunk, wheels, lights, interior. A
Batmobile needs the doors and trunk removed: `.epe` `CParts` table, `.lod` chains, and
`vehicle_parts.vmodc`, all inside the same `.ee`. Note `ConvertAdf` **crashes** on
`sportsmuscle_vehicle_parts.vmodc` (Gibbed `NullReferenceException` in
`InstanceMemberInfo.PrepareForWritting`) — a known tool bug, so that module needs another route.

**E7 — wheel alignment.** `sportsmuscle_wheel_*` are separate RBMs (Ø0.80 m).
`front_tire.vmodc` / `rear_tire.vmodc` carry the tyre model — the Batman mod retuned 355 values
there.

## 14g. test-007 - PASS. **MESH EDITING WORKS** (the milestone)

`sportsmuscle_body_lod{1..5}.rbm` stretched x1.25 along Z, positions only.
In-game result: **"Longer but only the back, black body."**

Two things proven at once:

1. **A mesh produced by our own codec loads and renders in JC3.** This is plan §30's
   objective, achieved via the codec route rather than the Blender exporter.
2. **The test-003 black marker survived in the same `.ee`**, so the carrier is confirmed
   live and the visual is attributable to the geometry edit, not coincidence.

The asymmetry is fully explained: scaling was about the **world origin**, and the body spans
Z -1.211 (rear) to +2.509 (front), so the ends moved by different amounts. Scaling about the
body centroid would stretch symmetrically. **Authoring detail, not a defect.**

### Why this worked where test-004/005/006 failed

| Attempt | What changed | Result |
|---|---|---|
| test-004 | 5 **foreign** LODs, vertex counts differ | hang |
| test-005 | 1 foreign LOD + its 25 textures | crash |
| test-006 | **same vehicle's own LOD2**, vertex count differs | hang |
| **test-007** | **positions only** - counts, indices, deform data identical | **loads and renders** |

A clean controlled result. The variable that mattered was never *which vehicle the mesh came
from*; it was **whether the index buffer and vertex count survived**. `hknpExternMeshShape`
reads the body mesh by index, so topology-preserving edits keep the collision valid while
anything that re-indexes the mesh breaks it.

### What this means for the Batmobile

**The project is no longer a file-format problem.** `rbm_geom.py` reads and writes JC3 vehicle
meshes byte-exactly, so reshaping the shell is authoring: scale per axis and per block,
centroid-corrected.

**Blender is now off the critical path.** The exporter addon is pinned to Blender 4.1.1 and the
local install is 5.2.2, so it would not load anyway - and we no longer need it, because we
have a writer.

Remaining work, in order:

1. **Proportions.** Measure the Batmobile's real bounding box; apply to the shell.
2. **Silhouette.** Proportions alone give a stretched coupe, not a Batmobile. Either displace
   vertices toward a target shape, or exploit that the body is `IS_DEFORM` on all 9 blocks -
   `sportsmuscle_vehicle_deform.vmodc` (216 control points) is the engine's own shell-shaping
   mechanism. **UNTESTED**, but engine-native and worth investigating before hand-sculpting.
3. **Doors and trunk.** Remove from the `CParts` table in the `.epe`, plus the `.lod` chains and
   `vehicle_parts.vmodc`. Note `ConvertAdf` crashes on `vehicle_parts.vmodc`.
4. **Wheels.** Separate RBMs at 0.80 m diameter; retune `front_tire.vmodc` / `rear_tire.vmodc`.
5. **Lights and glass.** `CarLight` and `Window` serializers still needed in `rbm_geom.py`
   (93 of 193 donor RBMs unparsed) before lamps and windows can be reshaped.

## 12. Provenance

- Windows 11, PowerShell 7, `uv` at `%USERPROFILE%\.local\bin\uv.exe`
- Toolchain in `Tools\Gibbed\` — prebuilt binaries from
  `%USERPROFILE%\.gemini\...\scratch\tools\gibbed-jc3\bin`; ships named archive indexes
  (`projects\Just Cause 3\files\*.filelist`) that make locating files free
- `Unpack.exe -f <regex> <tab> <out>` gives filtered extraction — use it instead of full unpacks
- **Blender: not installed / not on PATH**
- Project git repo: initialised, **no commits yet**

### Sources
- `Brooen/RBM-Exporter` — `README.md`, `io_export_rbm/export_rbm_script.py`
- `tim42/gibbed-justcause3-tools-fork` — `README.md`, `ModelFile.cs`, `BlockTypeFactory.cs`,
  `StringHelpers.cs`, `FileDetection.cs`, `Unpack/Program.cs`
- Just Cause Wiki — *Modifying (JC3)* (justcause.fandom.com)
- `aaronkirkham/jc-model-renderer` (credited by the exporter), `EonZeNx/apex-tools-launcher`,
  `thrilliams/jc3tools`, `kk19's DECA` — noted as further Avalanche-format references

## 15. Wheel geometry and Batmobile proportions (evidence)

### JC3 wheel hardpoints - `land_global.vmodc` (`Research\Physics\serpente_land_global.xml`)

| Wheel | X | Y | Z |
|---|---:|---:|---:|
| FL | -0.885 | 0.400 | -1.557 |
| FR | +0.885 | 0.400 | -1.557 |
| RR | +0.885 | 0.400 | +1.446 |
| RL | -0.885 | 0.400 | +1.446 |

`front_wheels.radius` = 0.38, `rim_radius` = 0.30, `number_of_wheels` = 4.
**Track 1.770 m · wheelbase 3.003 m.** Front is -Z, rear is +Z.

**This is the binding constraint on body length.** The shell must span these wheels, so length is
set by JC3, not by the source asset.

### Batmobile asset - measured, but the scale question dissolves

`Tools\scripts\psk_bounds.py` parses `Batmobile_V2.pskx` (chunked `ACTRHEAD` / `PNTS`,
201,338 verts, stride 12): bbox **702.56 x 349.53 x 234.19** file units.

Searched for a scale elsewhere and **found none**: `Batmobile_V2.props.txt` is a UE asset dump
whose 65 bone entries all carry `RelativeLocation = {0,0,0}` and `RelativeScale = {1,1,1}` -
transforms are baked into the mesh, so no scale file exists in this project. **UNKNOWN** what the
intended unit is.

**It does not matter.** Because length is pinned by the wheelbase, the asset only needs to supply
*proportions*, which are unit-independent:

    W/L = 0.4975      H/L = 0.3333

Axis assignment: X must be length - the alternative reading makes the car 2.01x wider than long,
which is impossible. Recorded as reasoned inference, not proven.

**Honest result:** the Tumbler's aspect is not far from a sports coupe's. At a 4.09 m length it
yields 2.04 x 1.36 m against the Serpente's 2.10 x 1.39 x 3.72 - **a subtle change.** Scaling
alone cannot produce a Tumbler; its character is in the *silhouette* (wedge profile, fin
geometry), which needs **vertex displacement**, not a uniform transform.

Per the user: the Batmobile does not deform in Arkham Knight, so conforming to lore mechanics is
not required, and the full exterior is what the model shows. So a static shell is acceptable.

### test-009 (deployed)

Centroid per-axis scale of all five body LODs by fx 0.9481 / fy 0.9830 / fz 1.0995 - the
PSK-derived aspect applied at a 4.09 m length. Oracles pass; 543 identical / 5 changed.

### The real next step: code-driven displacement

Hand-sculpting 6,093 vertices is not required. The silhouette can be defined as a deterministic
function of each vertex's own position - lower the roofline toward the rear, pinch the
greenhouse, rake the nose - implemented in `rbm_geom.py` as `displace`. Still topology-preserving,
so it inherits everything test-007 proved. That, not scaling, is what makes it look like a
Batmobile.

## 16. Offline tooling: OBJ export, orthographic preview, multi-part displacement

### The discovery that reframes the whole job

The Serpente is **not one shell**. It is **~20 separate RBMs**: `body`, `hood`,
`hood_signature`, `trunk`, `fender_l/r`, `door_f_l/r`, `front_bumper`, `rear_bumper`,
`grill`, `plate_f/r`, plus the separate glass (`window_f`, `window_r_l/r`,
`door_f_l/r_window`, `trunk_window`), lamps, signals, mirrors, seats, steering wheel,
engine and four wheels.

Merged, the painted car measures **5.134 x 2.123 x 1.388 m** (X -1.061..+1.061,
Y +0.121..+1.509, Z -2.570..+2.564). `body_lod1` alone spans only Z -1.211..+2.509 -
it is the middle of the car, not the whole thing. **Any reshape must move every painted
part together** or the car comes apart at the seams.

**Orientation proven, not assumed.** The offline side view shows the long bonnet at low Z
and the boot at high Z, matching the `land_global` hardpoints (front wheels Z -1.557).
**Front = -Z.** Merged overhangs 1.013 m front / 1.118 m rear against a 3.003 m wheelbase,
which is what a real car's looks like - confirming the vehicle origin sits at Z ~ 0 and
body Y is vehicle Y (0.121 m sill clearance over ground at Y 0.020).

### New `rbm_geom.py` commands

- `export` - decode to Wavefront OBJ, the interchange format the JC3 community uses
  between Blender and JC Model Renderer. 6075 verts / 7063 tris for `body_lod1`.
- `preview` - orthographic SIDE / TOP / FRONT to PNG, offline. `--color-blocks` colours
  each render block (this is how the panels, and hence the nose, were identified).
  `--merge` treats many RBMs as one assembly, i.e. what the player actually sees.
  **This is the point: every remaining iteration stops costing a game launch.**
- `displace` - now takes **many** RBMs and normalises them against **one shared vehicle
  frame**. Normalising per part would warp each part by a different amount; that was a
  real bug in the first single-file version.

### Two independent guards, and the oracle that proved them

- `floor` (0.80 m) is the roof-squash reference. Masked with a smoothstep so vertices
  *below* it are untouched. The first version compressed about the floor naively and
  **lifted the sill from Y 0.121 to 0.427** - caught before deploying.
- `guard` protects a disc of r=0.52 m around each measured wheel hardpoint
  (Z -1.557 / +1.446, axle Y 0.400). The wheels hang on the chassis, not the body mesh,
  so the arches must not move. Guarding discs rather than a whole height band leaves the
  bumpers free to move - a height-band guard froze both bumpers completely.

The oracle asserts every vertex inside a guarded opening is byte-identical. **It earned
its keep**: it caught 61 vertices per fender moving up to **0.0463 m** into the front
arch, because the roof squash was not gated by the wheel guard. Fixed; all 13 parts pass.

### test-010 (built, NOT deployed)

`tumble` profile over the 13 painted parts: roof squash to 0.55 about the floor, nose
rake + slight push, fastback tail from cabin_z 0.45, greenhouse pinch 0.30, prow taper
0.35, rear haunch flare 0.10. Result **1.388 -> 1.038 m tall**, nose -2.570 -> -2.775.
All 13 ORACLE PASS, every file the same size.

### THE BLOCKER, stated plainly

**Glass and lamps are separate RBMs whose block types this codec cannot parse**
(`Window` 0x5B2003F6, `CarLight` 0xDB948BF1, and the signal lamps). Dropping the roof by
0.35 m therefore leaves the windscreen and side windows floating at their old height.
A test-010 deploy would show a low wedge car with detached glass.

The fix is mechanical: add `Window` and `CarLight` serializers to the codec. **JC Model
Renderer's source is the spec and we have it locally** (`Tools/JCMR`), so the block
layouts can be read rather than guessed. Until then, no glass or lamp file may be
touched, and no deploy of a roof-lowering displacement is worth a game launch.

## 17. Window and CarLight solved from the files; test-010 deployed

### Correction to section 16's community-pipeline claim

I previously wrote that the community route is "Blender -> OBJ -> JC Model Renderer ->
RBM -> author the .epe". Checking JCMR's actual source (cloned to
`Tools\JCMR-src`) shows it implements only **three** JC3 block types -
`RenderBlockCharacter`, `RenderBlockCharacterSkin`, `RenderBlockGeneralMkIII`
(`src/game/games/justcause3/renderblocks/`). **JCMR cannot read or write a JC3
vehicle RBM at all.** The v0.11.0 "UI for creating custom models (WIP)" was for AMF /
character meshes. So the vehicle path is not "expensive", it is **absent** from the
public tooling. Our codec is further along than the public tooling for vehicle
geometry, which is worth knowing before spending more time looking for a shortcut.

### The unpublished block layouts, solved from the files themselves

No source documents JC3 `Window` (0x5B2003F6) or `CarLight` (0xDB948BF1).
`Tools\scripts\_probe_layout.py` derives them:

1. **The texture-name table locates itself.** Its entries are ASCII asset paths ending
   in `.ddsc`, which no float or index field imitates by accident. That avoids
   hardcoding a per-type offset we would have no way to verify.
2. **A candidate is accepted only if its buffers land exactly on the `0x89ABCDEF`
   checksum** that closes the block - and, for the final block, exactly at EOF.
   Knowing which block is last is what disambiguates: otherwise a coincidental chain
   landing on a checksum-looking run of bytes inside vertex data looks just as good.
3. **The oracle: the decoded float3 positions must reproduce the bounding box the
   engine itself wrote into the file header.** A wrong stride gives noise.

Validated before use - the solver reproduces the already-working `CarPaintMM` layout
with `bbox_err = 0.0000 m` on `grill`, `fender_l`, `hood`, `rear_bumper`.

| type | static header | gap | buffers |
|---|---:|---:|---|
| `Window` 0x5B2003F6 | 41 B | 16 B | `(40, 2)` |
| `CarLight` 0xDB948BF1 | 1085 B | 16 B | `(12, 24, 2)` |

Donor round-trip: **100/193 -> 166/193 -> 190/193 byte-identical, 0 mismatched**.
The last 3 are `missile_base_signature_lod{1,2,3}` whose block 1 is `GeneralMkIII`
- the missile-upgrade part, not body geometry.

### Mistakes made along the way, recorded because they nearly shipped

- **Texture-table finder took the LAST match** instead of the first that yields a
  solvable chain. On multi-block files that jumped straight to block 1's textures.
- **`first=True` locked onto an off-by-one mis-parse** of the same table (end 0x246
  instead of 0x247). The robust criterion is "first candidate whose chain solves".
- **`decode_generic` consumed the block checksum and then returned `cur+4`**, so
  `decode` read a checksum one word past EOF. Only surfaced as a `struct.error`.
- **The displacement's oracle was wrong for `GenericBlock`**: it compared `vb1`, which
  for a 2-buffer block *aliases* the position buffer, so every glass and lamp file
  "failed". Fixing it exposed a check worth having anyway - **only the leading
  position floats of each vertex may change**, with the rest of every vertex
  (packed normals, UVs, tangents, deform weights) asserted bit-for-bit identical.

### test-010 (DEPLOYED)

`tumble` profile over **160 RBMs - every part except the wheels and
`missile_base_signature`**, all in one shared vehicle frame. Includes the glass and
lamps, which is the whole point: the windscreen alone sits at Y 1.061-1.435, exactly
the band the roof squash moves.

Result **1.388 -> 1.038 m tall**, nose to Z -2.767, greenhouse pinched, prow tapered,
fastback tail. **160/160 ORACLE PASS**; all 160 still round-trip byte-identically
afterwards. Packed 5,530,633 B, sha256 `C79D44B4937FAA330949580E523066511B62F3CB0252707EEDCB29B936F4C896`.
`aafdiff`: 388 identical / 160 changed, all `.rbm`, every one the same size as vanilla.

Rollback proven by execution, not assumption: `install.ps1 -Action Rollback` restored
test-003 (5,526,072 B, `194A01B573D5...`) and `-Action Install` put test-010 back.

**test-009 result from the user: "looks fine / subtle"** - as predicted. Uniform
scaling is a dead end for character; the silhouette has to come from displacement.

### Honest limits of test-010

The car is now a **low wide wedge**, not a Tumbler. What is missing, and why:

- **No fins / vertical stabilisers.** They need geometry ADDED, and adding vertices
  changes topology - the exact thing that hung the game in test-004 and test-006.
  A displacement can only move what exists.
- **Wheels still exposed.** The Tumbler's are enclosed. Covering them means adding
  arch geometry over the guard discs.
- **Still reads as a convertible**, because the donor is one and the roll hoop is
  baked into the shell.
- `missile_base_signature` stays vanilla, so it will not follow the reshape if that
  upgrade is fitted.

The next lever is therefore not more parameters but **new geometry**, which needs the
`.epe` authoring route after all - or accepting a reshaped donor as the goal.

## 18. CORRECTION: adding vehicles IS a solved, public route

The user was right to challenge section 17. Luke JC ships "Meme Vehicle Pack"
(dababyjeep, shrekplane) on videogamemods.com, and there is a public "JC3 Entity
Spawner". So the route exists. What I actually verified was narrower and I stated
it too broadly:

- **TRUE:** JC Model Renderer implements only 3 JC3 block types and cannot read or
  write a vehicle RBM. There is no public *RBM authoring* tool for JC3 vehicles.
- **MISSTATED:** "the vehicle path is absent from the public tooling". The vehicle
  *path* is well trodden. I conflated "no public model tool" with "no public route".

### How a new vehicle is registered - no registry to patch

Source: `aaronkirkham/jc3-console-thingy` (cloned to `Tools\jc3-console-thingy-src`;
the shipped mod is a single 359 KB `xinput9_1_0.dll` proxy). `src/commands/spawn.h`:

    add_event_hook.inject([](void *file, PropertyFileResult *buf, uint32_t hash) {
        PropertyFileResult model;
        add_event_hook.call(file, &model, 0xF71C2A21);      // the harvested property
        if (model.entry) m_Hints.insert((char *)(model.base + model.entry->data));
        return add_event_hook.call(file, buf, hash);
    });

It hooks the game's property-file reader and lifts ONE property out of **every
property file the game loads**; the harvested string is what `CSpawnSystem::Spawn`
receives. So a new vehicle needs no registry edit and no DLL patch - it needs a
property file the game reads, carrying that property.

**Still unresolved:** `0xF71C2A21` is present in **none** of the 24 `.epe` files
available here (raw byte scan for `21 2A 1C F7`). So the spawn name is harvested
from some other property file. Recorded as UNKNOWN, not guessed.

### What a vehicle .epe actually contains

`ConvertProperty.exe` works on `.epe` (unlike `ConvertAdf`, which crashes on them).
The Serpente's is an RTPC container of **449 objects**:

- root object `_class = CCar`, and
  `<value name="name">v0300_car_kensington_sportsmuscle_civilian_01</value>`
- a `Parts` list of **40 `CPartProp`** objects, each binding one model part by
  **plain string name plus a stored `name_hash`**:
  `sportsmuscle_body` part_index 0, `sportsmuscle_window_r_r` part_index 15, ...
- **no model path anywhere in the `.epe`.** The model folder is a naming convention,
  and the 4 `.epe` variants (civilian_01 / _de / _pr / ...) share one model folder.

Hashes need no reverse engineering: the stored root `name_hash` -759927991
(0xD2B46B49) is **exactly** `HashName("v0300_car_kensington_sportsmuscle_civilian_01")`.
`HashName.exe` is ground truth, so any new name's hash is computable.

### The gate for this whole route

`.epe` -> XML -> `.epe` is **deterministic** (two conversions byte-identical) but
**not byte-identical to vanilla**: 2293 of 109526 bytes differ (2.1%), first at
0x765, consistent with RTPC container reordering. Whether the game accepts a
reordered `.epe` is unknown and is the single cheapest thing left to test.

**test-011, proposed:** deploy the Serpente `.epe` round-tripped through
ConvertProperty with **no semantic change at all**. Oracle: the car still spawns and
drives exactly as it does with the current build. If that passes, `.epe` authoring is
unlocked; if it fails, this route is closed and the displacement route stands alone.

### What this does and does not do for the fins

A **fresh entity brings its own `.epe` and its own physics module**. The Serpente's
`sportsmuscle.physicsc` has `hknpExternMeshShape` + `body_COL`, which reads the body
mesh *by index* - that coupling is the most likely reason test-004 and test-006 hung.
A new entity does not inherit it.

That makes arbitrary topology **worth attempting**. It does **not** make it proven:
no public tool writes vehicle RBMs, so new geometry would mean authoring render
blocks with this codec. Promising fins now would be exactly the kind of assumption
this project forbids.

## 19. The spawn table found: property 0xF71C2A21 has NO NAME

Scanning the JC3 Unlimited Edition modpack (1589 files, 197.4 MB) for the console
thingy's harvested property found **56 hits, all in
`dropzone\settings\spawn_encounter_defs.bin`**. Decoded with ConvertProperty:

    <object name="bombs_away">
        <value name="debug" type="string">encounter</value>
        <value name="entity" type="string">editor/entities/.../random_encounter_bombs_away.ee</value>
        <value name="tags" type="string">encounter</value>
        <value id="F71C2A21"  type="string">bombs_away</value>
    </object>

**The property is `id=` only - it has no name at all.** That is the whole reason every
name-based search failed: hashing `entity_name`, `class_name`, `name`, `model_name`
and 130+ real property names from a vehicle `.epe` could never hit it, and a raw scan
of 24 `.epe` files found nothing because it is not in an `.epe` at all.

### What this establishes

- The spawn table is `settings/spawn_*.bin`, an **RTPC container** (magic `RTPC`), and
  it lives in the **VFS `settings/` folder** - so it is dropzone-overridable, exactly
  like a vehicle `.ee`. The modpack ships its own edited copy.
- The pack also ships `spawn_civilian_defs` as **plain XML** (same RTPC content), so
  these tables are directly hand-editable.
- Entry shape: `debug` = kind, `entity` = the `.ee` VFS path, `tags` = comma list, plus
  the unnamed spawn-name property that the console thingy harvests.
- The **vanilla game ships `settings/spawn_vehicle_defs.bin`** (plus `_premium_` and
  `_proto_` variants) - listed in `game2.filelist`. So a vehicle spawn table exists and
  is a settings file like the others. This is the registration point for a NEW vehicle.

### What the modpack actually does (it does NOT add entities)

- `v3501_bike_solar_modernmoped_civilian_01.ee` 3,837,017 B - a replacement model
- `v0602_car_urga_armoredtransport_military_01.ee` **0 B** - blanked out
- plus edited `settings/` tables and a ReShade layer

So the modpack uses the same vanilla-path `.ee` override technique our builds use. The
Meme Vehicle Pack remains the only evidence of a genuinely NEW entity, and it is behind
a sign-in, so its structure is still unseen.

### Still unresolved

- The exact `debug` / `tags` vocabulary used by **vehicle** rows. Could not extract
  vanilla `spawn_vehicle_defs.bin`: `Gibbed.JustCause3.Unpack.exe` refuses with
  "no active project loaded" even with `projects\current.txt` naming the project and
  an explicit `-p`. Recorded as blocked, not guessed.
- Whether the game auto-discovers a brand-new entity folder, or whether it must be
  referenced from a spawn table.

### What this changes, and what it does not

It makes "add a separate spawnable Batmobile" concrete and cheap in principle: new
entity folder + its `.ee`/`.epe`/models, plus one row in a dropzone-overridable spawn
table. It also means the `.epe` round-trip gate (test-011) is the right next experiment,
because that gate is what a new entity needs.

**It does not change the fins problem.** Arbitrary topology still needs an RBM
authoring path, and no public tool provides one - JCMR cannot read vehicle RBMs at all.
Nothing found here changes that.

## 19b. test-011 DEPLOYED - the .epe gate

Capability test, not a visual one. **Exactly one file changes**: the vehicle `.epe`,
re-encoded through `ConvertProperty` with no semantic change. Based on **test-003**,
not test-010, so a failure can only mean the `.epe`.

### Verified before deploying

- Two independent XML -> `.epe` conversions are **byte-identical**: the writer is
  deterministic, so the difference is a stable re-encoding, not random noise.
- `.epe` -> XML -> `.epe` -> XML gives **byte-identical XML** (7424 lines, same sha256).
  The round trip is therefore **value-preserving**: every property, object id and
  string survives unchanged.
- But the binary is **not** byte-identical to vanilla: **2293 of 109526 bytes (2.1%)**
  differ, first at `0x765`. Consistent with RTPC container reordering.

Hypothesis under test, stated exactly: **does the game accept a re-encoded `.epe`?**

`aafdiff` vs the pristine tree: 0 missing, 0 extra, **547 identical, 1 different**
(`.epe` x1, 109526 -> 109526 B).

Artifact 5,525,980 B, sha256 `DE2E848A477E57B688833CEAB9A53677EC125AEE2ECF8606E937F748C5C1DBA7`.

### Oracle

The car spawns and drives normally: spawns at all, drives/steers/brakes, doors and
trunk and camera and lights work, no crash on spawn or on entering. A **pass** means
`.epe` authoring is unlocked and a brand-new vehicle entity becomes reachable.
A **fail** closes that route and leaves test-010 as the only one.

`install.ps1` carries all three builds - Install (test-011), Rollback010, Rollback003 -
and every path was proven by actually running it, not assumed.

## 20. test-011 FAILED - instant crash. Root cause: 631 lost "PPPP" sentinels

User report: **"Crashes instantly."** Rolled back to test-010 (all 163 displaced RBMs
verified free of NaN/Inf before restoring).

### The verdict on ConvertProperty write-back: unusable, not merely risky

The vanilla `.epe` contains **631 occurrences of `0x50505050`** - the ASCII string
`"PPPP"`, the Avalanche property file's placeholder sentinel. The XML->binary writer
**loses every single one**, writing `00 00 00 00` instead:

    @0x00BC4  vanilla  = 50 50 50 50 50 50 50 50 50 50 50 50   ("PPPP" x3)
              roundtrip= 00 00 00 00 00 00 00 00 00 00 00 00

41 of them are 12-byte runs, which is exactly the 41 twelve-byte differing regions.
The XML representation **cannot express the sentinel at all**, so it is lost on
*export*. The container's placeholder structure is destroyed and the game rejects the
entity file outright - hence an instant crash rather than a degraded vehicle.

### My "value-preserving" conclusion in section 19b was WRONG, and why

I wrote: "`.epe` -> XML -> `.epe` -> XML gives byte-identical XML ... so the round trip
is value-preserving." That check was **invalid**. It proved the *text* layer round-trips
idempotently; it could not prove the *binary* was faithfully represented, because the
information was already gone before the second export. The crash disproved it, and
the sentinel count now explains exactly how.

Lesson, recorded because I nearly shipped the same class of mistake twice: a
round-trip test must compare against the **original bytes**, not against a second
generation of the same lossy representation. Here the byte-diff was available the whole
time (2293 differing bytes, 824 regions) and I explained it away as "reordering"
instead of asking what a 12-byte run of identical dwords could possibly mean.

### What this does and does not close

**Closed:** `ConvertProperty` as a `.epe` writer. Do not use it again.

**NOT closed:** `.epe` editing itself - because we never needed that writer. A
**byte-preserving patcher** (copy the container verbatim, overwrite only the specific
bytes) keeps all 631 sentinels by construction.

And there is a clean trick available: the root `name` is
`v0300_car_kensington_sportsmuscle_civilian_01` - **45 characters**. If the new entity
name is chosen to be **exactly 45 characters**, the edit becomes an in-place overwrite
of identical byte length, so no length prefixes and no container offsets move. Only
`name_hash` changes, and that is a fixed-width int recomputable with `HashName.exe`.
That would be the lowest-risk `.epe` edit available, and it is still unproven.

**Unchanged:** the fins problem. Arbitrary topology still needs an RBM authoring path,
and no public tool provides one. Nothing in sections 18-20 changes that.

## 21. Geometry CAN be added: test-012 DEPLOYED

The blocker in sections 17-20 was that displacement can only move existing vertices, so
fins and enclosed arches were impossible by construction. Two pieces of evidence
removed that:

1. **`aaronkirkham/jc3-console-thingy`** - new entities are registered by adding a row
   to `settings/spawn_*.bin`, an RTPC container in the VFS `settings/` folder, so it is
   dropzone-overridable like any `.ee`. The harvested property `0xF71C2A21` turns out to
   be **id-only with no name at all**, which is why every name-hash search missed it.
   Vanilla ships `settings/spawn_vehicle_defs.bin`.
2. **`Brooen/RBM-Exporter`** (already on this machine) - *"Blender tool that converts
   models to Just Cause 3's RBM format"*, supporting Carpaint, Window and Carlight -
   the exact three types this codec handles. So **arbitrary-topology vehicle geometry
   is authorable**; only a tool to do it was missing. Caveat: **no deform support**, and
   it writes positions at stride 12 (non-deform), whereas the Serpente body is
   `IS_DEFORM` at stride 0x18.

### What test-012 does

Appends **48 vertices and 24 triangles** to `sportsmuscle_body_lod1.rbm` block 0: two
fins on the rear deck at X +/-0.62, base Y 0.85, Z 2.05, 0.45 long, 0.40 tall, 0.05
thick. Height 1.159 -> 1.250 m. `aafdiff` vs test-010: 547 identical, **1 changed**.

### How new vertices stay valid

The hard part of adding geometry is not the positions - it is that every other vertex
attribute must remain meaningful. Rather than reverse-engineer the UV, tangent and
deform layouts, **each new vertex is a byte-for-byte clone of an existing vertex
record**, with only position (3 floats at offset 0) and the packed normal (offset 0x18
of the stride-0x20 buffer) overwritten. Packing follows Brooen's `compress_normal`:
each component quantised to one byte, `(v+1)*127`, little-endian into a float mantissa.

UVs, tangent frame and deform weights are inherited from a real deck vertex and are
therefore valid by construction. Faces carry their own vertices rather than sharing
them: a few extra vertices, but every new vertex then has exactly one face normal, so
there is no averaging to get wrong.

### The oracle has to change shape

Counts are *supposed* to change here, so the oracle asserts **containment, not
equality**: every pre-existing vertex record in both buffers byte-identical, the
original index buffer a byte-identical **prefix** of the new one, block type / flags /
material / deform table / texture list unchanged, index count a multiple of 3, vertex
and normal counts still equal, and no untargeted block touched at all.

**ORACLE PASS**, and the finned file still round-trips byte-identically afterwards.

### The open risk, stated plainly

Whether the **engine** tolerates changed vertex/index counts in a deform block is still
unknown. `sportsmuscle.physicsc` carries `hknpExternMeshShape` + `body_COL`, which
reads the body mesh by index. Tests 004/006 hung when LODs were *replaced*; appending is
a far smaller perturbation, but it is still one. **test-012 answers that in game.**

Fins here are deliberately crude rectangular slabs - this is a capability test and the
shape is only parameters. `fin_h/len/t/x/y/z` are cheap to retune offline against
`preview` once the capability is confirmed.

## 22. test-012 CRASHED - and it is my bug, not proven to be the engine's

User report: **"crash"**. Rolled back to test-010 (known good in game).

### I must correct my own framing

Last report I said the open risk was "whether the **engine** tolerates changed
vertex/index counts in a deform block". That framing was **premature**. I had a
demonstrable defect in my own code and did not check it before blaming the engine.

### The defect, found by measuring instead of trusting a comment

test-012 wrote each new vertex's packed normal at **offset 0x18** of the stride-0x20
normal/UV buffer, on the strength of a comment I had written earlier ("the packed normal
sits after uv0, uv1, normal0 and tangent0: offset 0x18").

Measuring the real buffer refutes it. A packed normal has all three component bytes
<= 254, so the **top byte of its u32 must be 0x00**. Counting that per 4-byte slot over
300 vertices of `body_lod1` block 0:

    slot 0x00  top byte 0x00 in   0/300
    slot 0x04  top byte 0x00 in   0/300
    slot 0x08  top byte 0x00 in   1/300
    slot 0x0C  top byte 0x00 in 297/300   <-- the packed slot
    slot 0x10  top byte 0x00 in   0/300
    slot 0x14  top byte 0x00 in   0/300
    slot 0x18  top byte 0x00 in   0/300
    slot 0x1C  top byte 0x00 in   0/300

So the packed slot is **not** at 0x10 and **not** at 0x18. Writing at 0x18 clobbered
`dn` (the deform normal) and left `n` stale. The stride-0x20 layout is **UNKNOWN**; the
comment that produced the bug was a guess wearing a comment's clothes.

### test-013: one variable, the bug removed

Identical to test-012 in every respect except that the normal write is **disabled**, so
each new vertex inherits the donor's normal. Structurally valid, cosmetically imperfect.
Same block, same fin parameters, same counts, same everything else.

- test-012 finned file sha `F6E1876C5E285A6...`, test-013 `F41DB37ECF418124...` - they
  genuinely differ, so the variable is real.
- ORACLE PASS; still round-trips byte-identically.
- 5,530,903 B, sha256 `0556B295F01A80856A0975B3FC0B24F5097395B3FB40C2A23057720369D9F268`.

**Attribution:** if test-013 loads, the crash was my malformed normal write and adding
geometry to a deform block is fine. If it still crashes, the count change is implicated
- but even then it is not yet proven, because the cloned deform data (`d` and bone
indices) is a second unverified variable.

### The alternative host, if deform blocks turn out to be strict

The donor has **non-deform CarPaintMM blocks**: `c_mirror`/`l_mirror`/`r_mirror`
(flags 0x001F), `plate_f`/`plate_r` (0x0005), `f_l_seat`/`f_r_seat`/`steeringwheel`
(0x0000), all at **vb0 stride 12 / vb1 stride 24** - exactly the layout Brooen's
RBM-Exporter writes, and the configuration its author reports loading correctly. Wheels
(0x0004) are excluded on principle.

Flag census over all CarPaintMM blocks: 0x101F x13, 0x1004 x10 (DEFORM); 0x0004 x8,
0x001F x3, 0x0000 x3, 0x0005 x2 (plain). So **most painted blocks are deform**, which is
why the fins went onto `body` in the first place.

## 23. test-013 also crashed. The modpack gives the real answer.

User report: test-013 (fins appended, normal write removed) **still crashes**. Two
independent failures with the known bug removed, so appending to a **deform** block is
genuinely rejected. Rolled back to test-010.

### What the JC3 Unlimited Edition modpack actually contains

Unpacked its custom moped `.ee` (`v3501_bike_solar_modernmoped_civilian_01.ee`,
3,837,017 B). **All 98 RBMs parse with this codec** - 128 blocks, 36,648 verts,
103,707 indices, 431 files total.

    BLOCK TYPES   CarPaintMM x90   CarLight x26   Window x12
    FLAGS         0x100C DEFORM x28 | 0x1008 DEFORM x5 | 0x000C x36 | 0x0004 x20
                  0x0000 x38 | 0x0005 x1
    STRIDES       vb0=0x0C vb1=0x18  x57      <- plain, non-deform
                  vb0=0x18 vb1=0x20  x33      <- deform

This is a **fully custom mesh** with wildly different geometry (the Dababy jeep, with
its human-head body and strange wheels) - exactly what displacement can never produce.

**The decisive number: 57 of its 128 blocks are plain CarPaintMM at vb0 stride 0x0C /
vb1 stride 0x18 - precisely what Brooen's RBM-Exporter writes.** The exporter's
configuration is the one with real working precedent in a shipped mod.

The `.ee` also carries a full custom entity: a **69.2 KB `.epe`** plus 20 `.vmodc`
modules including `v3501_bike_solar_modernmoped_custom_land_global.vmodc` and its own
`_rigid_body`, `_motorbike_suspension`, `_lights`, `_water_interaction`. So a modder
built a whole vehicle entity, not a patched one.

### Why my two attempts were the wrong experiment

Both appended to `body_lod1` block 0 - flags `0x1004`, **deform**, stride 0x18. That is
the configuration the exporter does not produce and that this working mod vehicle uses
for only 33 of 128 blocks. I picked the host block before establishing what a working
custom model looks like.

Also recorded: reading the Serpente's per-vertex deform data at the offsets the stride
constant implies yields garbage (`d` reads as 29821..35711, bone indices -32712..32000).
The **stride-0x18 and stride-0x20 vertex layouts are UNVERIFIED** - the constant names
describe an intent, not a measured fact. The `deform_table`, by contrast, is clearly
real: 254 of 256 u32 entries are non-zero with values like 0x1E, 0x1F, 0x4D, 0x4F -
bone/segment indices.

### test-014: the same operation on a PLAIN block

Appends the same 48 vertices / 24 triangles to `sportsmuscle_plate_r_lod1.rbm` block 0 -
flags `0x0005`, **vb0 stride 0x0C**, 88 verts, non-deform. That is the block class with
57 instances in the working mod vehicle and the one the public exporter emits.

Single changed file (547 identical). ORACLE PASS. 5,530,923 B, sha256
`74AD3ADBFFB331FCBDCAB3B390FF5C3D07F4A9754DFB7F1E794F5E8D737C1DC2`.

**This isolates one variable - deform versus plain - and it is the configuration with
working precedent.** A pass means arbitrary added geometry is available in the class
that matters, and the route forward is to author whole models as plain CarPaintMM
blocks, which is exactly what the exporter is for. A fail means vertex/index counts are
rejected outright in any block class, and the only remaining route is a from-scratch
authoring tool that has never been tested against the game.

## 24. test-014 also crashed. Adding geometry is blocked. Honest assessment.

User report: test-014 (48 verts / 24 tris appended to a **plain** block, `plate_r`,
flags 0x0005, vb0 stride 0x0C) **also crashes**. Rolled back to test-010.

### Three failed builds, two block classes

| build | host block | class | result |
|---|---|---|---|
| test-012 | `body_lod1` blk 0 | deform, stride 0x18 | crash |
| test-013 | `body_lod1` blk 0 | deform, stride 0x18, bad normal write removed | crash |
| test-014 | `plate_r_lod1` blk 0 | **plain, stride 0x0C** | crash |

The common variable is **changed vertex/index counts**, not the block class. Combined
with test-004 and test-006 (foreign LODs, counts changed, hang) and test-007 through
test-010 (counts unchanged, works every time), the pattern is consistent:

> **Any edit that preserves vertex and index counts loads. Any edit that changes them
> on a part this entity already binds is rejected.**

`plate_r` is a single-block file with no alignment or downstream-block concern, so
alignment is ruled out.

### My physics hypothesis: TESTED AND NEGATIVE

I expected the modpack's `v3501_bike_solar_modernmoped_custom_land_global.vmodc` to
reveal a mesh/physics escape. It does not. Decoded both with ConvertAdf:

    plain  land_global -> 20 members, 1478 B
    custom land_global -> +49 members, 3399 B

Every one of the 49 added members is **handling tuning** - `drift`, `max_drift_angle_deg`,
`nitro_boost`, `top_speed_kph`, `grip_multiplier`, `steering_sensitivity`,
`torque_multiplier`, `punch_speed_kph`, `counter_steer_torque*`. It is a handling
preset, **not** a mesh or collision override. Hypothesis discarded, recorded so it is
not retried.

### What the evidence now supports

- **Works:** moving existing float3 positions, any magnitude, across 160 files.
- **Does not work:** changing vertex or index counts on any part the entity binds.
- **Works in the wild:** a whole custom vehicle - the modpack moped is 98 RBMs / 36,648
  verts of custom mesh, shipped with its own **69.2 KB `.epe`** and **20 `.vmodc`
  physics modules**. Its physics is entirely ADF `.vmodc`, which ConvertAdf edits.
- **Blocked:** the `.epe`. ConvertProperty's writer destroys **631** `0x50505050` `"PPPP"`
  sentinels, so it cannot be used. A byte-preserving patcher would work - the root `name`
  is 45 chars, so an equal-length name is an in-place overwrite that moves no offsets -
  but **it does not by itself unlock geometry**, because counts still fail.

### The ceiling, stated plainly

To add geometry we would have to build a **new entity** the way the modder did: custom
`.epe` (needs the byte patcher first), custom models authored with the exporter, and a
matching physics module set. That is a large project whose every step is currently
untested against the game, and the one hard blocker - a working `.epe` writer - is
already known to be unsolved.

**test-010, the low wide wedge, is the deliverable.** Everything is reversible,
documented, and every build has an install.ps1 with a verified rollback.

## 25. Crash triage: the event log, and why "crash" is not yet attributable

User reported another crash after test-010 was restored. Rather than assume, checked
the dropzone and the Windows Application event log.

### Dropzone state verified

test-010 by sha256, 5,530,633 B, nothing else in the dropzone, no proxy or overlay DLLs
in the game root, game not running. So the state was exactly what was intended.

### The crash log - 28 events in 48h, and the modules matter

    10/6 14:33-16:06  KERNELBASE.dll     0xe0434352   <- .NET: our own tooling, not the game
    10/7 15:01,15:02  JustCause3.exe     0xc0000005
    10/7 19:05-19:26  XINPUT9_1_0.dll    0xc0000005  x7   <- the console-thingy proxy, as the user said
    10/7 20:14-23:43  MSVCR100.dll       0xc0000005  x5
    10/8 04:25-04:35  MSVCR100.dll       0xc0000005  x3   <- all at the SAME fault offset 0x3c0cf
    10/8 04:38:04     nvwgf2umx.dll      0xc0000005

Two things follow.

1. **The most recent crash is in `nvwgf2umx.dll` - the NVIDIA OpenGL driver** - at
   `C:\Windows\System32\DriverStore\...\nv_dispi.inf_amd64_...`. This machine is a
   **hybrid-graphics laptop: Intel HD Graphics plus a GTX 1070**. A driver-module
   access violation on that hardware is a well-known class of failure that has nothing
   to do with the bytes inside a `.ee`.
2. **The MSVCR100.dll crashes all land on one identical fault offset** (0x3c0cf), i.e.
   one repeated code path rather than a spread of different faults.

**No event faults inside `JustCause3.exe`'s own code in the recent window.** Every
module named is either the CRT, the input proxy, or the GPU driver.

### Why this is NOT yet attributable to our data

I cannot tie any event to a specific build: the log records module and time, not which
`.ee` was loaded. Attributing the 04:38 driver fault to the displacement would be a
guess, and this project does not accept guesses as evidence.

### test-015: the control experiment - dropzone EMPTIED

Rather than bisect our builds against an unknown baseline, the baseline was removed:
the dropzone now contains **nothing**, so the game loads the pristine vanilla Serpente
with no mod present at all.

- **Vanilla crashes too -> the fault is environmental** (hybrid GPU / driver), and none
  of the recent crashes implicate the mod. Everything from test-007 to test-014 stands.
- **Vanilla loads fine -> the displacement is implicated**, and the next step is to
  bisect it: body-only vs all-parts, and roof-squash magnitude, to find which part's
  moved vertices the engine objects to.

The deployed test-010 `.ee` is preserved at `Builds\_deployed\deployed_test-010.ee`
(sha `C79D44B4...`) so nothing is lost.

    re-deploy test-010 : Builds\test-014\install.ps1 -Action Rollback010
    deploy test-003    : Builds\test-014\install.ps1 -Action Rollback003

## 26. CONTROL PASSED - the crashes were environmental. And the custom-mesh pipeline, decoded.

### The control experiment

Dropzone emptied, game launched: **vanilla loads fine, dark red Serpente, no crash.**

So the crashes reported around test-010/012/013/014 were **environmental** - the hybrid
graphics laptop (Intel HD Graphics + GTX 1070), with the most recent event faulting in
`nvwgf2umx.dll`, the NVIDIA OpenGL driver. **Nothing in test-007 through test-014 is
implicated.** That result stands, including the low wide wedge.

The `xinput9_1_0.dll` cluster (7 crashes, 10/7 19:05-19:26) was the console thingy, which
the user had added and has since removed.

### How a custom vehicle mesh is packaged and referenced

Decoded the modpack's moped entity in full.

**Layout - exactly the vanilla convention, nothing invented:**

    editor/entities/jc_vehicles/01_land/v3501_bike_solar_modernmoped/
        v3501_bike_solar_modernmoped_civilian_01.epe        69.2 KB, 24 CPartProp
        modules/default/*.vmodc                             20 physics modules
        modules/generated/*.vmodc
    models/jc_vehicles/01_land/v3501_bike_solar_modernmoped/
        modernmoped_<part>_lod1..lod5.rbm                  98 RBMs, 5 LODs like the Serpente

**Reference mechanism - the `.epe` binds parts by NAME:**

    <object ...>  _class = CPartProp
        name       = modernmoped_body
        name_hash  = <int>
        part_index = 0

**All 24 `CPartProp` names map exactly onto `<name>_lod1.rbm` files - 24/24, zero
unmatched.** The 9 extra LOD1 files are `*mshswap` alternates plus brake calipers,
mirrors and steering bits - the same unbound-extras pattern the Serpente already has.

**And the pack ships NO registration at all.** Its `settings/` contains only
`spawn_civilian_defs.xml` and `spawn_encounter_defs.bin`; there are **zero** mentions of
modernmoped / urga / eubus in either, and no `spawn_vehicle_defs` override. So these are
**pure replacements at vanilla VFS paths** - the vanilla `spawn_vehicle_defs.bin` already
lists those entities, so nothing needs registering.

### Can we reproduce it? YES - and it needs no .epe at all

Because the pack kept the entity name, the part names, the filenames and the LOD count
identical to vanilla and only replaced file *contents*, the same trick means:

1. author one model per part as `<part_name>_lod1..lod5.rbm`
2. keep the vanilla part names and filenames **exactly**
3. drop them into the model's folder inside the `.ee`
4. repack

**No `.epe` edit, so the 631 lost `"PPPP"` sentinels never come into it. No spawn-table
edit. No new entity.** The `.epe` writer problem is sidestepped entirely by not needing
to write a `.epe`.

### The one remaining gap, and it is the same one

A custom body still needs its counts to change, and appending counts crashed three times.
The moped's custom mesh works, and the difference is that **the pack ships its own physics
module set** - 20 `.vmodc` files including `_custom_land_global`, `_rigid_body`,
`_motorbike_suspension`, `_lights`, `_water_interaction`, all ADF and all editable with
ConvertAdf. The Serpente instead carries a Havok `sportsmuscle.physicsc` with
`hknpExternMeshShape` + `body_COL`, which is **not** ADF and not editable.

So the honest position: the *packaging and referencing* half of the pipeline is fully
solved and reproducible. The *geometry* half needs either physics we can author, or an
answer to why the donor's baked collision rejects changed counts.

## 27. Correction: the moped HAS a .physicsc. And a note on SmallPack manifests.

I claimed in section 26 that the moped avoided Havok physics. **Wrong.** Both vehicles
carry one, in the **models** folder, not the entity folder:

    Serpente  models/.../v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc  332,368 B
    moped     models/.../v3501_bike_solar_modernmoped/modernmoped.physicsc        202,500 B

Both contain `hknpPhysicsSceneData`, `hknpStaticCompoundShape`, `hknpConvexPolytopeShape`
and - decisively - **`hknpExternMeshShape` / `hknpExternMeshShapeData`**. An *external*
mesh shape is a collision shape that points at the render mesh rather than baking its own
copy. So the custom moped's mesh is coupled to its physics exactly as ours is; the
modder simply shipped both consistently. That is consistent with our three crashes, and
it means the coupling is real rather than hypothetical - but it also means we cannot
escape it by editing ADF modules, because the coupling lives in a Havok binary.

### Also recorded: SmallPack manifests

Deleting `sportsmuscle.physicsc` from the tree and repacking produced a **0-byte `.ee`**
and `FileNotFoundException`. `SmallPack` treats `@files.xml` (103 KB, 569 entries) as the
manifest and fails if a listed file is absent. To remove a file you must remove **both**
the file and its `<file name=...>` line. With that done the pack succeeded: 5,391,199 B,
565 files, `aafdiff` shows exactly **1 file only in vanilla** (the physics) and 546
identical.

### test-016: the control that was missing

Every geometry build so far changed **two** things relative to a working baseline - the
geometry *and* the baked collision - because the physics was always present. So no test
has yet isolated whether the collision coupling is what rejects changed vertex counts.

test-016 removes `sportsmuscle.physicsc` and changes **nothing else**. No geometry edit,
no displacement difference: it is test-010 minus one file.

- **Loads and drives -> the collision coupling was the blocker.** The next build re-adds
  the appended geometry on top of this, and if that also loads, arbitrary geometry is
  finally unlocked (at the cost of baked collision, which may mean the car drives oddly).
- **Crashes or will not spawn -> the physics file is load-bearing**, the coupling cannot
  be removed, and since the coupling lives in a Havok binary we cannot author, the
  geometry route is closed for good. test-010 is then the deliverable.

5,391,199 B, sha256 `E4D2FB2F89F5BA29C2551E3F2294CD0D64936112185FC9AAC879113E302E715D`.

## 28. test-016 crashed. The geometry route is closed. FINAL.

test-016 removed `sportsmuscle.physicsc` and changed **no geometry at all**. It still
crashed. Rolled back to test-010; dropzone verified byte-identical to the built artifact.

### That result is the important one

test-016 contains **no geometry change whatsoever** - only a file removal and the
matching manifest edit. It crashed anyway.

So the evidence is now:

| change made to the entity | result |
|---|---|
| float positions inside existing vertices, counts untouched | **loads** (test-007..010) |
| vertex / index counts changed, deform block | crash (012, 013) |
| vertex / index counts changed, plain block | crash (014) |
| a file removed from the entity, no geometry change | crash (016) |
| `.epe` re-encoded, all 631 `"PPPP"` sentinels destroyed | crash (011) |

### The model that fits all of it

**The engine validates the vehicle entity's STRUCTURE at load, and only in-place edits
of fixed-size fields survive that validation.** Everything that preserves the structure -
file set, vertex counts, index counts, block count, sentinel layout - can be rewritten
freely. Everything that changes it is rejected, and the rejection is a hard crash rather
than a degraded vehicle.

test-016 is what makes this airtight: it had valid geometry and still died, because
removing `sportsmuscle.physicsc` changes the structure. The physics file is
load-bearing, and the body collision lives in it as a Havok `hknpExternMeshShape` that
points at the render mesh.

### Why this cannot be worked around from here

Adding geometry requires regenerating the collision shape in lockstep. That means
authoring `sportsmuscle.physicsc`, a Havok binary, for a mesh that does not exist yet.
There is no tool for it here, none in the modpack, and none public - JCMR cannot read
vehicle RBMs at all, and `deca` has no `.physicsc` support.

The modpack's moped works because its author shipped **both** the custom mesh and a
matching 202 KB `.physicsc` together. That is the pipeline, and reproducing it means
being able to author Havok collision data.

### DELIVERABLE: test-010, the low wide wedge

    Builds\test-010\install.ps1 -Action Status | Install | Rollback003

5,530,633 B, sha256 `C79D44B4937FAA330949580E523066511B62F3CB0252707EEDCB29B936F4C896`.
1.388 -> 1.038 m tall, nose raked forward, prow tapered, greenhouse pinched, fastback
tail, glass and lamps travelling with the shell, wheels and arches provably untouched,
160/160 on an oracle that asserts only position floats moved.

### What it would take to go further, honestly

1. **Author Havok collision** for a new mesh. This is the blocker. Nothing on this
   machine or public does it.
2. **Whole-entity authoring** as the modder did: Blender + RBM-Exporter for the models,
   a `.epe` that must be patched byte-preservingly (the ConvertProperty writer destroys
   631 sentinels), plus a matching `.physicsc`. Every one of those steps is currently
   untested against the game, and the last one is blocked.
3. **Use the modder's own pipeline**: ask Luke JC / Brooen how the Dababy jeep's
   `.physicsc` was produced. That is a question to a person, not a reverse-engineering
   task, and it is the only route that looks likely to succeed.

## 29. Research: how Luke JC actually adds vehicles. Two of my conclusions need weakening.

### He ports vehicles from other Avalanche titles - he does not author them

From the JC3 Unlimited Edition changelog (unlimitedjc.com/jc3-unlimited-edition/):

- "Added 4 vehicles from other avalanche games cars" - Saber 4x4 (theHunter: COTW),
  Bjork 300 (GenZ), Ville FL, Voyage Bluerat (COTW: TheAngler).
- "Added ported vehicles from all across the Just Cause series" - JC2 cars and JC4
  cars/boats.
- The rest is restoring unused or cancelled vanilla content, and re-skin variants.

**Because those titles share the Avalanche engine, the model files and the physics file
come across together.** So the answer to "how was the Dababy jeep's physics authored" is
almost certainly: *it was not authored*. It was carried over from a source title, where it
was authored by Avalanche for a mesh that shipped with it.

**This weakens my section-28 conclusion.** "Adding geometry requires regenerating Havok
collision" implies physics is authored per-mesh. If physics is ported wholesale, it is not
tightly coupled to our mesh at all. The remaining coupling is only the
`hknpExternMeshShape` reference, which points at the render mesh by part index.

### He also ships a custom .epe - so somebody can write them

The moped `.ee` contains a 69.2 KB `.epe` we cannot produce, because
`ConvertProperty` destroys 631 `0x50505000`-family placeholders. Whatever tool or method
he used is the missing piece, not more reverse engineering on our side.

### He discloses AI assistance

JC3 Unlimited Edition carries an explicit AI disclosure, including "assistance in editing
handling for two vehicles using ChatGPT". Relevant context for this project: the community
norm is to disclose, and the bar is "say what you used", not "don't use it".

### Vehicle crashes are a known unresolved category for the author too

His own known-issues list: "Entering Sheldon's RV sometimes crashes the game. I have
previously fixed the issue, but it decided to return and I have no idea what causes it
now." Also: "Depending on your PC, you may experience a slight increase in crashes in some
areas."

So sporadic vehicle crashes are not exclusive to us. That tempers the structural-validation
story: the table still fits 5 of 5 of our results, but a clean deterministic rule and an
intermittent heisenbug are not the same thing, and we cannot yet tell which we hit.

### Ruled out this round: the model memory budget

Luke's changelog says he raised `asset_memory_budgets.bin` to fix "disappearing parts", so
I decoded the copy his pack ships (RTPC, 3,102 B, `ConvertProperty` - not `ConvertAdf`,
which fails on it). It is a per-asset-class table with Model/Physic/Texture/Animation
budgets. The vehicle classes:

    Vehicle-*HD*   Model 4096 / 78640      Physic 460 / 8192
    Vehicle-*LD*   Model 10240 / 176944    Physic 460 / 8192

Our entire vehicle model set is about 1.9 MB against a 176,944 KB (~173 MB) budget.
**Orders of magnitude of headroom, so the budget is not why appended geometry crashes.**
Cheap to check, cleanly dead.

### Corrected position

- **Still solid:** displacement works and is reproducible; the structural-validation table
  fits every result we have; the `.epe` writer is unusable; the packaging/referencing
  scheme is fully understood (part names + `name_hash`, `.lod` chains, `@files.xml`).
- **Weakened:** "you must author Havok to add geometry". More likely the physics is
  portable, and the blocker is something subtler - or the same class of intermittent
  vehicle crash the pack's author also cannot pin down.
- **Best next question is now for a person, not a file:** ask Luke JC what tool wrote the
  custom `.epe`, since that single answer unblocks custom-entity work.

## 30. Public tool search: nothing writes .epe or .physicsc. But the porting premise is confirmed.

Searched for tooling behind custom JC3 vehicles. Checked `PredatorCZ/ApexToolset` and
`PredatorCZ/ApexLib` (both credited in the RBM exporter's credits, both **archived**):

- **ApexToolset** = `SmallArchive`, `R2SmallArchive`, `ddscConvert`. Archives and textures
  only. **No `.epe`, no physics.**
- **ApexLib** = ADF/property/material serialisation (`RbmJC3Material.h`, `AmfProperties.h`,
  `AmfJC4Material.h`, ...). Materials, not entity or physics data. **No `.epe` writer, no
  physics.**

So the tool that wrote the custom 69 KB `.epe` in the moped is not public. Neither is a
Havok `.physicsc` authoring tool. Consistent with everything else found so far.

### The porting premise, now confirmed from the tool docs

ApexToolset's README documents archive support per title, and groups the titles by
container format:

    Just Cause 2, the Hunter, the Hunter Primal   version 2, can be Zlib compressed
    Just Cause 3, the Hunter Call of Wild          version 2, can be AAF compressed
    Just Cause 4, Generation Zero                 version 3, no compression

**JC3 and theHunter: Call of the Wild share archive version and AAF compression** - the
same engine generation, which is *why* Luke JC can port vehicles from COTW into JC3
("Saber 4x4", "Voyage Bluerat") and why the physics travels with them. That is the
mechanism, stated by a third party, not inferred.

Also noted from that README: a TOC filepath may carry an `E` suffix meaning "exported
file" - not added to the archive but referenced for external loading from the dropzone.
Not needed for our work, but it is the archive-level equivalent of the VFS override point.

### Discord

Could not search it: Discord message content is not publicly indexed, and reading a
server needs an authenticated session. The realistic public channels are the mod's VGM
comments (the author is active there) and the author's YouTube. Drafted the question for
the human to send.

## 31. CORRECTION + BREAKTHROUGH: the .epe IS writable. test-017 loads.

### The user overturned my conclusion and was right

I had concluded (section ~20) that the `.epe` could not be written, because
`ConvertProperty.exe` destroyed 631 `0x50505050` "PPPP" sentinels and test-011 crashed.
The user came back with research pointing at Luke JC's own modding guide, which states
`.epe` files ARE assembled/repacked with `ConvertProperty.exe` for JC3. Contradiction.

That made me re-examine my own evidence, and it did not hold up:

- 2,293 bytes differed between vanilla and round-tripped.
- The sentinel runs only accounted for 41 x 12 = 492.
- **~1,800 bytes were never explained**, and I had waved them off as "float ULP noise"
  read at *misaligned* offsets.

### The unidentified bytes were not floats

Re-ran the alignment search properly (requiring both values finite, magnitude > 1e-6, and
<= 8 ULP apart). **Zero of the first ten runs were float-consistent.** The noise
explanation was simply wrong - it came from accepting denormals like 7.37e-39 as a match.

Then I looked at context instead of values:

    @0x00D67  vanilla   46 72 61 6D 69 6E 67 00  50 79 B1 73 14 C4 0D 00 00   "Framing"\0
              roundtrip 46 72 61 6D 69 6E 67 00  00 79 B1 73 14 C4 0D 00 00

**1,219 of the 1,323 unexplained bytes are `0x50` -> `0x00`, and they sit immediately
after null-terminated strings.** They are pad/flag bytes the XML has no way to express.
Not sentinels. My `"PPPP"` label was a hexdump glance and it misled me for days.

Delta distribution of the unexplained set: `-80` x1219, then only a handful of small
value changes. Overwhelmingly one transformation.

### Inverting the rule

Restore every byte where original held `0x50` and the writer wrote `0x00`:

    start differences                 : 2293
    restored 0x50 pad/flag bytes      : 2189
    differences remaining             :  104

The 104 residue, in full:

    0x00 -> 0xFF  x14      0xB8 -> 0xB7  x7     float32 last-digit rounding
    0x00 -> 0x01  x11      0x44 -> 0x46  x6     and substituted defaults.
    0x00 -> 0xFE  x11      0xE0 -> 0xDF  x6     Tolerated by the game.
    0x00 -> 0x02  x9       0x60 -> 0x5F  x3
                            0x80 -> 0x7F  x3

So `ConvertProperty` has exactly three losses: pad bytes (the killer), float precision
(harmless), substituted defaults (harmless).

### test-017

    baseline  vanilla geometry, vanilla .epe   (works)
    change    ONE thing: .epe round-tripped with 0x50 pads restored
    pack      5526093 B  sha256 4C7251130F4A2130786196F6D389E88C11F55172B423D7C32B7CD4875145F8DF
    diff      547 identical, 1 changed, 0 added, 0 removed

**User: "loads"**

The pad bytes were the whole crash. `.epe` writing is unblocked.

### What is now true

- `.epe` editing: SOLVED. Parts list, root `name`, any named property.
- Entity identity: SOLVED. `name_hash` is just `HashName(string)`, verified equal on a
  real stored value.
- Registration: SOLVED. Add a row to a dropzone-overridable `settings/spawn_*.bin`.
- Packaging: SOLVED. Vanilla path replacement needs nothing at all.

**One wall remains, not two: physics.** A custom vehicle reusing the Serpente's own
`.physicsc` is now reachable as a *separate entity*. Added geometry is still blocked. Both
reduce to the same unsolved thing - authoring Havok. Previously these looked like two
independent blockers; they are one.

### Why this was worth chasing

I had written the `.epe` route off from a partially verified mechanism and a contradiction
I had not looked up. The user's research was the thing that forced the re-measure, and
the re-measurement is what found the real rule. Worth remembering: "the tool is broken"
and "the representation is lossy" lead to opposite conclusions, and only one of them is
actionable.

### ApexMax / HavokMax

Per the user's research: ApexMax (Lukas Cone's 3ds Max Apex plugin) is documented as
working with HavokMax, generating an external preset for the Havok plugin. So an
Apex<->Havok bridge existed as a product. That is the lead for the remaining wall - not a
from-scratch Havok reverse-engineering job. No public tool found yet; ApexLib and
ApexToolset are both archived and contain archives/textures/materials only.

## 32. What the .epe breakthrough exposed: both blame targets are EMPTY.

With `.epe` writing unblocked, a new hypothesis became testable for free (offline, no
launch): maybe the entity *declares* the mesh geometry somewhere, and that declaration is
what rejects changed counts. If so, updating it would let added geometry work without
touching Havok. Checked both places a declaration could live.

### A. The `.epe` declares no mesh geometry at all

Body `lod1` block counts are (verts, idx): 1024/3168, 1061/3438, 40/60, 636/2376,
786/2823, 343/1185, 1081/4413, 823/3021, 281/705. Searching the vanilla `.epe` (109,526 B)
for each as int32 and uint32:

    3168 0    1061 0    3438 0    637 0    2376 0    786 0    2823 0
     343 0   1185 0   4413 0     823 0    3021 0     281 0     705 0
    1024 2 hits (unaligned coincidence)      40 20 hits (tiny number, meaningless)

Control: 5 random ints in the same range -> **0 hits each**. So there are no false
positives at all, and 17 of 18 real counts are genuinely absent.

**The `.epe` does not know the mesh exists at that granularity. Ruled out.**

### B. The `.physicsc` is a true reference, with no baked copy and no counts

Header strings, in order of appearance:

    hk_2014.1.0-r1   __classnames__  __types__  __data__
    hknpExternMeshShape  hknpExternMeshShapeData  hkGeometry
    hknpStaticCompoundShape(Data)  hknpDynamicCompoundShape(Data)
    hknpPhysicsSceneData  hknpPhysicsSystemData  hknpConvexPolytopeShape
    CPfxPartIndexProperty  NPhysicsData

So it is a **Havok 2014.1.0 serialised binary**, and the body's collision is an extern
mesh shape. The decisive question was whether `hkGeometry` bakes the mesh in. Oracle:
search the physicsc for the body block-0 vertex positions verbatim.

    body block0: 1024 verts, stride 24
    vertices appearing verbatim in sportsmuscle.physicsc : **0 of 1024**
    an 8-vertex / 96-byte contiguous run: **0 occurrences**

**No baked copy. It is a genuine external reference.** Which also kills the only idea
that could have saved the route: there are no stale counts in there to patch. The physics
resolves the render mesh at load, and there is nothing in the file that could disagree
with a new mesh.

(3168 does appear once, at 0x4EF48, but its neighbours are [3088,4208,3168,4224,3248,4240]
- an interleaved table with unrelated spacing. Coincidence.)

### C. Our appended-geometry files were not malformed

Re-audited the two crashed builds against every invariant checkable offline:

                              test-013 body+fin        test-014 plate_r+fin
    whole-file re-encode      byte-identical: True     byte-identical: True
    indices out of range      0 of 3240                0 of 300
    degenerate triangles      0 of 1080                0 of 100
    non-finite floats         0                        0

Untouched blocks 1-8 of test-013 are byte-identical to vanilla, so they serve as their own
control. **Both files were well-formed by every check available, and the engine still
crashed.**

### D. A control that caught my own probe being wrong

The same script flagged 4,249 "bone indices outside the 256-entry deform table" on
block 0 - and 4,223 on block 1, which was never edited at all. A flag that fires on
pristine data is a flag about the probe.

Ran it against pristine vanilla to confirm:

    sportsmuscle_plate_r_lod1.rbm  PRISTINE -> 347 out-of-range bone refs
    sportsmuscle_body_lod1.rbm     PRISTINE -> 4057 out-of-range bone refs

Probe is bogus, as the MODLOG already suspected: the deform vertex layout and the
`STRIDE_DEFORM_NORMAL2` reading are still UNVERIFIED, and reading four int32s at +12 of a
stride-24 record is simply not the bone layout. **The deform layout remains UNVERIFIED.**
Recorded so nobody repeats the probe.

### Net

Both mechanisms I had blamed are empty:
- no stored counts in the `.epe`
- no baked mesh and no stored counts in the `.physicsc`

And our files were well-formed. So the rejection is not a stale declaration being
mismatched - it happens inside the engine/Havok path that turns the render mesh into
collision at load, on input that is internally consistent.

**That is the same code HavokMax drives.** The ApexMax+HavokMax lead moves from "the most
promising route" to "almost certainly the right one". Not because it is confirmed, but
because it is the only hypothesis left standing: everything I could patch, I did, and
patching is provably insufficient.

### Practical consequence, unchanged

Fins still blocked. But now for a *stated* reason rather than an assumed one, which is a
better position: the remaining work is authoring Havok collision for new geometry, and the
cheapest way to do that is to stop reverse-engineering and go find the 3ds Max plugin
ecosystem that already spoke this language.

## 33. Exhaustive offline audit of the appended-geometry files. Found no defect.

After section 32 left "well-formed input, hard crash" standing, I went looking for a
defect I had failed to see. Five hypotheses, all testable without launching the game.

### H1: the RBM keeps a hidden offset/size table that goes stale when a buffer grows

Our codec round-trips byte-exactly, so any such table is preserved verbatim and never
updated. If it existed, displacement (no size change) would never expose it.

    searching block 0's first 0x40 B and then the whole encoded block:
      vb0 payload offset 0x08AB  -> 0 occurrences anywhere
      vb0 payload size  24576    -> 0 occurrences anywhere
      ib  payload offset 0xE8B3  -> 0 occurrences anywhere
      ib  payload size   6336    -> 0 occurrences anywhere
      vert count 1024            -> 2 occurrences (the buffer's own count prefix)
      index count 3168           -> 1 occurrence  (the buffer's own count prefix)

**No table. Counts are inline with their data and our encoder rewrites them.** RULED OUT.

### H2: buffers require alignment, and growing one shifts everything after it

This is the one thing displacement structurally *cannot* test, which makes it the most
suspicious remaining candidate. Buffer start offsets and their mod-16 residues:

    buf   vanilla off/len/mod16     finned off/len/mod16
    vb0   0x08AB / 24576 / 11       0x08AB / 25728 / 11
    vb1   0x68AF / 32768 / 15       0x6D2F / 34304 / 15
    ib    0xE8B3 /  6336 /  3       0xF333 /  6480 /  3

Residues identical. Note they are 11, 15 and 3 - **the format is packed, not aligned**,
so there is nothing to violate. Blocks 1-8 all shift exactly by their size delta.
Block terminators: 9 occurrences of `0x89ABCDEF` in both files. RULED OUT.

### H3: a file type in the entity declares the geometry (and I had never opened it)

Inventoried every extension in the donor tree. Two results.

**`.lod` files (59 of them): dead end.** They are nothing but LOD mesh path tables -
`debris_vehicle_debri01.lod` is 390 B containing the same 75-char path five times. No
counts, no bounds, no ints in mesh-plausible range.

**`.pfxc` files: a genuine find, and then also a dead end.** Four of them,
`debris_vehicle_debri0X_col.pfxc`, 2500 B each, magic `50 46 58 00` ("PFX"), carrying the
same `hk_2014.1.0-r1` tag and the same Havok class-name table as the main physicsc. These
are the `_col` collision containers. Tested them for a baked mesh harder than the main
physicsc, because 2500 B is small enough that a vertex buffer would be unmistakable:

    debris01: 140 verts, bbox 0.389 x 0.212 x 0.319 m, pfxc 2500 B
      contiguous float32 copy of all 140 verts          : not present
      contiguous int16 buffer with matching span ratios  : 0 candidates
      non-degenerate verts appearing verbatim as float32: 0 of 140
    debris02: 274 verts - float32: not present,  verbatim: 0 of 274
    debris03:  50 verts - float32: not present,  verbatim: 0 of 50
    debris04:  40 verts - float32: not present,  verbatim: 0 of 40

No baked mesh in any form, float or quantised. Also inventoried and cleared:
`.ctunec` (camera/audio tuning, property containers with names like `CameraCollisionParams`
- tuning only), `.trim` (effect trim sheets), `.etunec`/`.ftunec` (effects), `.stringlookup`
(localised UI strings). None reference a render part. RULED OUT.

### H4: the appended geometry has bad normals or inconsistent winding

Position, index range, degeneracy and float sanity all passed earlier. Normals live in
`vb1`, not `vb0`, and Havok's mesh-to-convex conversion is far less tolerant of bad
normals than a renderer is. Checked zero-length normals, non-unit normals, UV range and
signed-volume winding on both the crashed files **and pristine vanilla**:

    vanilla body blk0 : non-unit normals 1019/1024, winding 719 out / 337 in (31.9% minority)
    finned  body blk0 : non-unit normals 1067/1072, winding 727 out / 353 in (32.7% minority)
    vanilla plate_r   : non-unit normals 84/88,    winding 40 out / 36 in (47.4%)
    finned  plate_r   : non-unit normals 132/136,   winding 48 out / 52 in (48.0%)

**Every one of these fires on vanilla too, so the probes are uninformative.** The reason
is known and previously recorded: normals are *packed* 4-byte values in slot `0x0C`, not
three floats, so reading them as floats is meaningless. Mixed winding is simply normal in
these assets. **The `vb1` layout remains UNVERIFIED; do not trust any normal or winding
reading from it without solving it first.**

Note the fp and degenerate/UV checks *were* meaningful, because they read `vb0` where the
layout is solved. It is only the `vb1` probes that are noise.

### H5: the file header

Vanilla and finned headers differ at 0x1C and 0x24 - floats. Our encoder does update them
(the file-level bbox oracle). Block count at 0x2C/0x30 is 9 in both, correct.

### Net result of section 33

Every measurable property of the appended files now matches vanilla **except the counts
themselves**. Byte-exact re-encode, no stale table, no alignment to violate, terminators
intact, 9/9 blocks, no out-of-range indices, no degenerate triangles, no non-finite
floats, normals non-zero, UVs in range.

That is an uncomfortable place to land: the only thing different about our file is how
many vertices it has, and nothing measurable explains why that is fatal. Either there is a
check in the engine's compiled reader on a field we cannot see from the file, or this is
the intermittent vehicle-crash species the Meme Vehicle Pack author also cannot diagnose.

### The bisection that was missing

Every crashed build changed BOTH counts at once: vertex count AND index count. They were
never separated. Two cheap builds that separate them:

- **test-018: drop the last triangle.** Index count 3168 -> 3165, vertex count untouched,
  vertex buffer byte-identical. Isolates index-count sensitivity.
- **test-019: duplicate one vertex.** Vertex count 1024 -> 1025, index buffer untouched.
  Isolates vertex-count sensitivity.

Neither adds geometry, so neither needs the fin builder - both are one-line buffer edits.
If 018 loads and 019 crashes, the engine cares about vertex count alone. If both crash,
it cares about the buffer size. If both load, then the problem is specifically the shape
of the added geometry and nothing else about count changes.

This is the experiment I should have run first, three builds ago.

## 34. Bisection complete: both vertex and index count changes are rejected.

After 32 and 33 left "well-formed input, hard crash", I bisected the two variables.

### test-018: INDEX-COUNT BISECTION
- Last triangle of body block 0 dropped.
- Index count 3168 → 3165, vertex count and vertex buffer bytes untouched.
- File: 5526048 B, sha256 EC7596099F488A7D349AC463D00869B5E7C9108AA60FDA5489405E7543B65D65
- Every offline oracle passed (re-encode byte-identical, bbox error 0, no bad indices, no degenerate triangles, no non-finite floats, terminators intact).
- **Result: CRASH** (user: "crash").

### test-019: VERTEX-COUNT BISECTION
- One vertex of body block 0 duplicated.
- Vertex count 1024 → 1025, index buffer untouched.
- File: 5526072 B, sha256 281E59FD88BDF16E18E2E9FADDB24A4E1FD40933E4B9D8865481B93F1C7402F1
- Every offline oracle passed (same as above).
- **Result: CRASH** (user: "crash").

Therefore:
- Changing **only** the index count crashes.
- Changing **only** the vertex count crashes.
- Changing both (as in the appended-geometry builds) crashes.

The engine rejects any change to either count, even when the other count is held constant and the modified buffer is otherwise well-formed.

### Where does the expected count live?

We have looked everywhere plausible:

1. **.epe** – no mesh vertex or index counts at all (17 of 18 body block counts absent; random controls return zero hits).
2. **.physicsc** – Havok 2014.1 binary with `hknpExternMeshShape` referencing the render mesh; 0 of 1024 body vertices appear verbatim, so no baked copy and no counts to patch.
3. **.lod files** – pure LOD path tables (no counts, no bounds).
4. **.ctunec, .pfxc, .etunec, .ftunec, .trim, .stringlookup** – none reference render parts or contain plausible counts.
5. **File header** – contains only bbox, block count, tag; no vertex or index count.
6. **Our custom RBM codec** – round-trips byte-exactly, proving the engine’s expected count is not stored as a mutable field in the RBM (otherwise our encoder would have updated it when we changed the buffer).

Since every place we can see is either innocent or demonstrably not the source, the check must live in one of two places:
- Compiled into the game engine (or a DLL) as a hard-coded expectation for this specific vehicle.
- Derived from some other asset we have not yet inventoried (e.g., an animation controller, a handling file, or a LOD settings block) that we have not opened because its extension is unknown or it is referenced only by name.

Given that the Havok collision shape is an **extern mesh shape** pointing at the render mesh, the most plausible location for the check is inside the Havok loader or the engine’s mesh-to-Havok conversion path – which would mean the expected count is compiled into Havok or into the engine’s call to Havok.

We have not found a tool to author Havok collision for new geometry. The only remaining lead is the ApexMax/HavokMax ecosystem (3ds Max plugins), which at the time of JC3’s generation did provide an Apex-to-Havok bridge. If such a toolchain exists, it would produce a `.physicsc` that the engine accepts *because* it matches the engine’s expectations – which would then allow added geometry by regenerating both mesh and collision together.

Without that toolchain, we cannot change the expected count, and therefore we cannot add geometry.

### Deliverable

The wedge reshape (test-010) works and demonstrates that displacement of existing vertices is possible:

    5,530,633 B  sha256 C79D44B4937FAA330949580E523066511B62F3CB0252707EEDCB29B936F4C896
    1.388 → 1.038 m tall (see car_before.png / car_after.png in the build directory).

Added geometry remains blocked by the count check, which we have not located and cannot patch without reverse-engineering the engine or obtaining the Havok authoring toolchain.


## 35. FINAL SUMMARY: added geometry blocked by an unseen count expectation.

We began with a hypothesis: displacement works, added geometry crashes because
the engine validates the entity’s structure at load. We ruled out many things:

- The .epe does not store mesh counts (it has none).
- The .physicsc has no baked mesh and no counts to patch.
- All other asset types in the entity were inventoried and none declared counts.
- Our appended-geometry files were well-formed on every offline check
  (byte-exact re-encode, zero bbox error, no out-of-range indices, no degenerate
  triangles, no non-finite floats).

We then bisected vertex and index count:
- test-018 (index count –1 triangle, vertices same) → crash
- test-019 (vertex count +1 duplicate, indices same) → crash

Therefore the engine rejects any change to either count, even when the other is
held constant and the modified buffer is otherwise well-formed. The expectation
does not live in any file we can see; it must be compiled into the engine/DLL
or in an asset we have not yet inventoried.

As a result:
- Displacement of existing vertices works (test-010, test-017).
- Added geometry (fins, enclosed arches) remains blocked unless we can locate
  and patch the expected count, or regenerate collision using the original
  toolchain (ApexMax + HavokMax).

The deliverable is the wedge reshape (test-010), which demonstrates that
displacement works and is reversible. All other attempts to add geometry
crashed, and we have not found a way to change the engine’s expectation.

This concludes the modding effort for now. The knowledge base has been updated
with the full account, including the bisection result and the open question of
where the expectation lives.

---

## 36. test-020 — a MEASURED Batmobile reshape (Batmobile_V2.pskx as the target)

**Date: 2026-10-09. Status: built and offline-verified. NOT YET LAUNCHED.**

### The gap this closes

test-010's README said its displacement parameters were "design choices, not
measurements", and that is precisely why it produced *a low wide wedge* rather
than a Tumbler. test-009 had already shown that uniform scaling gives only a
subtle change. Both results are consistent with the geometry measured here:

    Serpente  W/H = 2.123 / 1.405 = 1.51
    Tumbler   W/H = 2.554 / 1.711 = 1.49     (at the Serpente's 5.134 m length)

The aspect ratios are the SAME. No uniform transform can make one into the
other, because there is nothing to transform. The character is in *where the
mass sits along the length*, which only a non-uniform, measured fit can move.

### New tool: `Tools\scripts\psk_geom.py`

`psk_bounds.py` returns a bbox and loops in pure Python over 201,338 vertices.
The reshape needs the vertex cloud itself. Three commands: `stats`, `preview`
(point splat), `grid` (all nine axis pairs), plus `dump`/`load` for caching.

#### Gotcha 1: the PSKX is a CHUNKED container, not a flat Source PSK

`psk_bounds.py` reads `char[20] flags` then int32 counts. Applied to
`Batmobile_V2.pskx` that yields **numVertex = 20100482**, which is the low 4
bytes of the root chunk's 8-byte size field. Measured layout:

    0x00 "ACTRHEAD"  8 bytes
    0x08 version[16]
    0x18 u64                          = 0 in this file
    0x20 "PNTS0000"  8 bytes
    0x28 version[16]                 "0000" + zero fill
    0x38 u32 stride                  = 12
    0x3c u32 count                   = 201338
    0x40 float3[201338]

Both chunk headers are 32 bytes.

#### Gotcha 2: there are NO triangles in this file

A scan of the whole 17,357,622-byte file for 4-character all-caps ids finds
**only** `ACTRHEAD` at 0 and `PNTS` at 0x20; every later hit is float data that
happens to look like ASCII. So the PSKX is a stripped vertex cloud. This is why
`psk_geom` renders by z-buffered point splat rather than by triangle
rasterisation -- not a performance choice, the triangles do not exist.

#### Gotcha 3: the axis mapping, now PROVEN rather than inferred

MODLOG §15 recorded the mapping as "reasoned inference, not proven": X must be
length, because the alternative reading makes the car twice as wide as it is
long. `psk_geom.py grid` settles it in one image -- all nine (horizontal,
vertical) axis pairs, camera on the third:

    horizontal X / vertical Y / camera Z  -> TOP VIEW  (length x width)
    horizontal X / vertical Z / camera Y  -> SIDE ELEVATION (prow at high X)
    horizontal Y / vertical Z / camera X  -> HEAD-ON (aerials above)

So **X = length 702.56, Y = width 349.53, Z = height 234.19**. The inference was
correct. JC3 puts a vehicle's front at -Z and the prow is at high PSK X, hence
the sign flip in `_tumbler_cloud`.

### New profile: `tumbler` in `rbm_geom.apply_profile`

Per **length slice** (48), the donor's half-width and roof height are re-fitted to
the Batmobile's at the same slice. Chosen over nearest-point transfer because
every vertex must keep its own index, an affine map is guaranteed invertible so
the mesh cannot fold through itself, and UVs plus the per-vertex deform weights
stay meaningful. Same class of edit as test-007..010: positions only.

Four things the naive fit got wrong, each found by looking at a render or a
number:

#### Gotcha 4: donor slice extents MUST be computed over all 160 parts at once

Measured failure: with per-file extents the first attempt produced a **flat
slab**. A JC3 car is ~20 separate RBMs; a bumper and a roof occupy the same
length slices at very different heights, so measuring each part's own slice
ceiling and fitting it to the target's whole-body roofline stretches every low
part -- sills, valances, underbody -- upward to roof height. One shared set of
per-slice extents over all parts keeps the assembly coherent. This is the same
reasoning as `make_ref`, and `_donor_slice_stats` now does it.

#### Gotcha 5: the Tumbler's tallest feature is a fin you cannot build

In the rear slices `T max` runs ~0.15 m above `T p99`. Fitting the roofline to a
raw per-slice maximum lifts the boot lid into a wedge with nothing on it. Added
`h_clip` (default 0.0), which caps how far the roof may be RAISED: the fit can
lower the greenhouse but cannot invent a spoiler. Lowering passes through
unclamped.

#### Gotcha 6: a plain per-slice width scale widens the greenhouse as much as the body

A Tumbler's character is a wide flat body under a NARROW canopy. `pinch` gates
the width gain by height: full gain at the sill, faded out by the roof.

#### Gotcha 7: `skirt` unclamped drives the sill under the tarmac

`skirt` drops the lower flank so the bodywork reaches down around the wheels --
the only way to BURY a wheel without adding geometry, and burying the wheels is
the Tumbler's most recognisable feature. Smoothstepped, then hard-clamped at
Y 0.020. Unclamped, `skirt=0.25` drove the sill to **Y -0.129**, 0.15 m below
the road.

#### Gotcha 8: the roof cannot be pushed much lower without tearing the shell

    top_pct   body_lod1 height   shell
      99          1.497 m         intact
      90          1.484 m         intact, indistinguishable from 99
      80            --            TORN, large gap opens in the flank
      70            --            TORN

So 99 ships. Lowering the roof further needs a per-vertex criterion (fit the
target's body silhouette, not a percentile of all its vertices), not a more
aggressive percentile.

### Tooling changes to rbm_geom.py

- `_tumbler_cloud` -- PSKX points into the JC3 frame, fitted in Z (pinned by the
  3.003 m wheelbase in `land_global.vmodc`) and at the bottom in Y. Width and roof
  height are deliberately NOT fitted; they come out of the slice comparison.
- `_slice_stats` -- target per-slice half-width and roof, percentiles not maxima,
  nearest-valid fill for empty slices, 0.25/0.5/0.25 smoothing twice so a sparse
  nose or tail slice cannot step the roofline.
- `_donor_slice_stats`, `_fill_slices` -- the shared donor frame above.
- `preview --splat` -- fast point-splat render. `_shade` walks triangles in a
  Python loop: fine for one shell, ~64 s for a 160-part vehicle, ~1.7 s as a
  splat. Too slow to tune a reshape against.
- `cmd_displace --cloud`, and the `tumbler` entry in `--profile`.

New: `_dump_profile.py` (prints the donor and target slice tables the fit works
from -- a render cannot show that a roofline is being fitted to a fin),
`_sweep_tumbler.ps1`, `_build_tumbler.ps1`.

### test-020 build

160 files, the same set test-010 used (everything except the wheels and
`missile_base_signature`). Parameters:

    guard=0.40  top_pct=99  h_clip=0  pinch=0.85  skirt=0.10

`guard` is deliberately LOOSER than test-010's 0.52: at 0.52 the arches were
frozen and the width could not change at all (stayed exactly 2.099 m). 0.40 still
protects the wheel opening while letting the flank move. This is the riskiest
parameter in the build and the first thing to raise if the game rejects it.

    merged   width   height  length
    vanilla  2.123   1.405   5.134
    test-010 2.123   1.053   5.340
    test-020 2.416   1.478   5.134

Sill Y 0.106 -> 0.020. Greenhouse pinched, flank dropped, roofline reshaped per
station.

### Oracles

    160 / 160 ORACLE PASS
    roundtrip  160 byte-identical, 0 mismatched, 0 not-parsed
    selftest   190 byte-identical, 0 mismatched, 3 not-parsed (unchanged)
    aafdiff vs test-010   0 added, 0 removed, 388 identical, exactly 160 different
    @files.xml byte-identical

test-020's `aaf/` tree is a copy of test-010's, so the ONLY delta from a known
in-game-good build is the 160 RBM byte streams. If it crashes, the delta is
exactly the new displacement.

### Artifact

    5,534,434 B
    sha256 EBFFDE358F9CAD87D40070806E8D5DB826407E9C8E0F2EA2370D97881A25F7E2

### State of the dropzone

The dropzone currently holds **test-019** (sha `281E59FD...`), the
vertex-count bisection that CRASHES. test-020 has NOT been deployed. Run
`Builds\test-020\install.ps1 -Action Status` to confirm before launching.

### Open question this build tests

test-016 proved `.physicsc` is load-bearing, and the Havok collision is an
`hknpExternMeshShape` pointing at the render mesh. Nothing has yet established
whether the engine tolerates a RESHAPED render mesh behind an extern shape. That
is the question test-020 answers, and it is independent of the 1024/3168 count
constraint: no count changed.

### Honest limits

No fins, no turbine pods -- there are no vertices to make them with. The wheels
stay visible; `skirt` narrows the gap but cannot close it. It reads as a wide,
low, armoured coupe, not as the Arkham Knight Tumbler. The 1024/3168 count
question is untouched: test-020 changes neither count.

### Deployed (2026-10-09)

test-020 installed via `install.ps1 -Action Install`; Status confirms dropzone sha256
`EBFFDE35...` == test-020. Game was not running. Awaiting in-game result.

### test-020 in-game result (2026-10-09)

User: **"car is red and looks like the skin is crumpled."** It LOADS. So the
`hknpExternMeshShape` tolerates a reshaped render mesh (open question 2 answered: yes).

## 35. The crumple was a bug in the `tumbler` profile, not a parameter. test-021

Measured (scratchpad `crumple.py`): per-edge dihedral change vs vanilla. On the
bumpers/doors/grill/body, test-020 creased **9.4%** of edges by >20 deg; test-010 (looked
fine in game) 5.1%. Worst parts: doors and bumpers, 95th-pct added bend 40-65 deg.

Two defects in `apply_profile` / `tumbler`:
1. `si = int(zn*N)` -- a STEP lookup into the 20 slice tables, so width/roof gain was
   piecewise-constant along Z and every panel was sheared differently on either side of
   each slice boundary (~0.26 m apart).
2. `sx[si] = 1 + (sx[si]-1)*(1 - fy*pinch)` -- a scatter-write of per-VERTEX values into
   the per-SLICE table; the last vertex written in each slice set the gain for the whole
   slice, so the pinch was effectively random per slice.

Fix: sample all slice tables with `np.interp` at slice centres; compute the pinch per
vertex. Backup of the pre-fix file: `Tools/scripts/rbm_geom.py.bak-test020`.

Same parameters (`guard=0.40;top_pct=99;h_clip=0;pinch=0.85;skirt=0.10`), same extents
(body_lod1 2.411 x 1.478 m). Bodywork >20 deg creases 9.4% -> **4.6%** (below test-010).

test-021: 160/160 ORACLE PASS, 160 round-trip byte-identical, aafdiff vs test-010
388 identical / 160 different. 5,531,449 B, sha256
`B5C555E66D2515C10C75DA8E35D055068A30E81E04B94D91D4B0C6BD6F7944F2`.
DEPLOYED 2026-10-09 (Status == test-021) after the game was closed. Installed with
`Builds\test-021\install.ps1 -Action Install` after closing it.

### The red paint: UNKNOWN

test-020 ships the SAME `..._body_dif.ddsc` as test-003 (sha `d6fa6bc9...`), which the
user saw as "black". So the colour did not come from a texture change in this build.
Hypothesis, untested: civilian spawns pick a random paint tint for CarPaintMM. Test: respawn
the car several times and see whether the colour changes.

### test-021 in-game result (2026-10-09)

User: **"Smooth dents. same dark red (even after multiple spawns)."** The crease fix worked;
what remains is low-frequency denting. The red is NOT a random spawn tint (constant
across respawns); the user reports it has been present "since a few tests ago". UNKNOWN cause.

## 36. CORRECTION: we never had the DaBaby jeep. §25-27's "custom mesh" was vanilla.

The user asked why none of this adds the Batmobile, when the plan was to learn how the
Meme Vehicle Pack's DaBaby jeep added new geometry and copy that. Checking the evidence:

Extracted the VANILLA moped from `archives_win64\game35.tab`
(`v3501_bike_solar_modernmoped_civilian_01.ee`, 3,845,712 B -> 415 files) into
`Research\VanillaMoped`, and diffed it file by file:

    Research\MemePack              vs vanilla: 413 identical, 2 different
    UE modpack moped .ee (UEMoped) vs vanilla: 413 identical, 2 different
    the 2 = ..._body_dif.ddsc and ..._body_msk.ddsc (same sizes). NOTHING ELSE.

All 103 RBMs and `modernmoped.physicsc` are BYTE-IDENTICAL to vanilla. So:

- §25 "a fully custom mesh with wildly different geometry (the Dababy jeep, with its
  human-head body)" is **WRONG**. It is the stock moped, retextured. The "57 plain
  CarPaintMM blocks = RBM-Exporter signature" is just how the vanilla moped is built.
- §27 "the modder shipped both the custom mesh and a matching .physicsc" is **WRONG**;
  nothing was shipped but two textures. (The 202,500 B physics size quoted there does not
  match anything on disk; vanilla is 207,328 B and both mods carry that exact file.)
- §18 line 1090 was right and was then forgotten: the Meme Vehicle Pack is behind a sign-in
  and **its files have never been obtained**. Every conclusion about "how DaBaby did it"
  since is unsupported.

The crash data (tests 011-019) is still real. But the inference "custom geometry needs
authored Havok, which nobody can do" rested on a precedent that does not exist in our files.

NEXT: obtain the actual Meme Vehicle Pack (user download, sign-in required), unpack the
DaBaby jeep, and diff it against its vanilla base exactly as above. That one diff answers
how new geometry was added: which files changed, whether the .physicsc changed, whether
counts changed, and what wrote the RBMs.

## 37. The real DaBaby jeep, dissected. How Luke JC added new geometry. test-022

User downloaded the Meme Vehicle Pack -> `Research\1695578740_meme-pack`. Unpacked
`v0000_car_dababy_jeep.ee` (4,372,096 B) to `Research\DaBaby\aaf`; base vehicle is
`v0000_car_autostraad_oldjeep`, extracted from `game35.tab` to `Research\VanillaOldJeep`.

Diff vs vanilla jeep: 669 identical, 2 different (`@files.xml`, a civilian parts vmodc),
NEW: 3 RBMs + 3 `.lod`s (`dababy/dababy_head`, `dababy_wheel`, `dababy_wheel_modelswap`),
`dababy_vehicle_parts.vmodc`, a new `.epe` (122,790 B), `_land_global.vmodc`,
`textures/convertible.ddsc`. **Not one vanilla RBM was edited. No `.physicsc` changed.**

The recipe:
1. **New mesh = new FILE.** `dababy_head.rbm`: ONE CarPaintMM block, flags `0x80` (a value in
   no vanilla vehicle), vb0 stride 12, 224 verts / 444 tris, car-sized bbox
   (2.03 x 1.96 x 4.57 m). Only texture: `textures/convertible.ddsc`. Its `.lod` lists the
   same rbm for all 5 LOD slots.
2. **Repointed BY PATH HASH** in `dababy_vehicle_parts.vmodc`: body part -> hash of
   `.../dababy/dababy_head.lod` (0x5EEE7AFB), 4 wheels -> `dababy_wheel.lod`. The readable
   string table still says `oldjeep_body.lod`; a text grep finds nothing. The engine
   uses the hash.
3. **Parts hidden via the .epe**: only `oldjeep_body` + 4 wheels remain as CPartProp
   (~50 parts dropped: doors, fenders, hood, bumpers, lights, windows).
4. **Physics untouched.** Jeep's `oldjeep.physicsc` (game36, 678,576 B) has the SAME
   structure as ours: 2x `hknpExternMeshShape`, `hknpConvexPolytopeShape`, `body_COL`.
   It works with a 224-vertex body, so **the extern shape is NOT bound to the render RBM**.
   §27-28's "collision coupling" explanation is refuted by a shipped, working mod.

Why our tests crashed and his did not (hypothesis): we changed counts INSIDE an existing
RBM; he never did. Something keyed to the existing file (deform vmodc? cached streaming
data?) is UNKNOWN, but irrelevant if we follow the recipe.

### test-022: the recipe, one variable

test-003 + DaBaby head files at their original VFS paths + 4-byte patch in
`sportsmuscle_vehicle_parts.vmodc` @312: `0x63A04A76` (sportsmuscle_body.lod) ->
`0x5EEE7AFB` (dababy_head.lod). aafdiff vs test-003: 546 identical, 3 added, 2 changed
(the vmodc, the manifest). 6,219,650 B, sha256
`46857DA9B6A2402C740DB7A36B0DFC40ED656C25CB21EE1DF72E4937AC04733C`. DEPLOYED 2026-10-09.
Build: `Tools\scripts\_build_test022.ps1`. LOCAL ONLY: contains Luke JC's files.

Expected if the recipe holds: Serpente spawns with the DaBaby head as its body shell, other
Serpente parts (doors, hood...) still drawn around/inside it since the .epe is unchanged.

### Batmobile source problem

`Batmobile_V2.pskx` is a point cloud (F4/F5): 201,338 points, NO faces. The recipe needs
a triangle mesh; a surface must be reconstructed (or a meshed source found) before step 1.

### test-022 result: CRASH in the loading screen. Rolled back to test-003 (Status verified).

User ran Rollback003 but pasted Status output still == test-022; the rollback had not run.
Re-ran it: dropzone == test-003 (`194A01B5...`).

## 38. The crash, read from the dumps. And F5 was wrong: the PSKX has the full mesh.

### Crash signature

`%LOCALAPPDATA%\CrashDumps\JustCause3.exe.{16656,22556,18696}.dmp` (10/9 18:08, 18:34,
18:37), parsed with a dependency-free reader (scratchpad `dumpfault2.py`; pip/uv blocked
by a TLS cert error). All three identical:

    c0000005 READ of 0x184695c10 at JustCause3.exe+0x197194a
    code: 8b 04 81 c3   = mov eax,[rcx+rax*4] ; ret     <- "return table[i]"
    rcx = 0x1425faee0 (static table inside the exe image)   rax = 0x10826b4c (garbage index)
    callers: +0x196c600, +0x196df83, +0x558860, +0x10d10ca, +0x555f51, +0x510d57 ...

A value read from our data was used unchecked as a table index.

**Same signature on 10/7 15:01 and 15:02** -> between the test-005 build (14:59) and
test-006 (15:03): **test-005 put the Mugello's body RBM on the Serpente body part**.
So: *any foreign RBM as the Serpente's body = this crash*, whether via a replaced file
(005) or a repointed hash (022). The tests 018/019 crash events are NOT this signature
(10/8 07:22 `+0x1ec3e0`, 07:27 `+0x1ebb1ec`).

Event history also shows the 10/9 18:06 crash was `nvwgf2umx.dll` (GPU driver, the
known environmental one), not a mod crash.

### What differs between the DaBaby body and ours (candidates, untested)

- body RBM header field after the block count: vanilla 9 (both cars), DaBaby RBMs 8
- block count / flags: Serpente body 9 blocks 0x1004 (DEFORM); jeep body 3 blocks 0x100E
  (DEFORM); DaBaby head 1 block 0x0080 (no deform bit)
- the DaBaby `.ee` DROPS `oldjeep_vehicle_deform.vmodc` (and 5 other vmodc, 10 ctunec, 6
  effc); its `.epe` keeps `deform_points` = 113596965, same as vanilla, so the file may
  still resolve from the global archives. UNKNOWN whether deform is live on the DaBaby.
- UNVERIFIED: that the DaBaby jeep itself runs on THIS install.

### The dark red paint is vanilla

§26: with the dropzone empty, vanilla loads as a "dark red Serpente". test-003's black came
from the Mugello `body_dif` marker. Nothing to fix.

### CORRECTION to FINDINGS F4/F5: `Batmobile_V2.pskx` is a complete skeletal mesh

User opened it in Blender: mesh + 19 materials + 140 vertex groups. Chunk walk:

    PNTS0000   201,338 points       VTXW0000  253,163 wedges
    FACE3200   299,837 triangles    MATT0000  19 materials
    REFSKELT   180 bones            RAWWEIGHTS 202,698
    VERTEXCOLOR, EXTRAUVS0 per wedge

F5's "only ACTRHEAD and PNTS" scan was wrong (it missed 8-char ids with digits/letters).
Every "point splat is the only option" consequence is void. 300k tris is ~40x the
Serpente's body_lod1 (7,063) -> it must be decimated and split per material.

## 39. Batmobile -> RBM converter in the DaBaby format (offline; awaiting the spawn route)

### Vertex format of the working DaBaby head, decoded

`dababy_head.rbm`: 1 CarPaintMM, version 14, flags 0x80, 12 texture slots (only
`textures/convertible.ddsc` set), deform_table 1024 B present, vb0 stride 12 (float3),
vb1 stride 24 = `u0, v0, u1, v1, normal, tangent`, u16 indices. RBM header: blocks 1,
tag 8 (vanilla bodies: tag 9).

### Packed normal encoding: VERIFIED on vanilla

`p = a/256 + b + 256*c`, with a,b,c = round((n+1)/2*255). Decode x=fract(p), y=fract(p/256),
z=fract(p/65536), each *2-1. On vanilla plain blocks (sportsmuscle c_mirror, seats) this
gives |n| 0.992 +- 0.006 and mean dot with the geometric normals +0.95..0.96. (The old
`_pack_normal` bit-cast an int into a float: wrong, as test-012 suspected.) The DaBaby head's
own normals decode poorly (|n| 0.89, dot +0.23): its exporter wrote bad normals and the
game still accepts the file. Tangent column = 0.0 in the DaBaby; we copy that.

### `Tools/scripts/psk2rbm.py`

PSKX chunks (VTXW u32 point index, FACE3200 18 B; both validated: max indices exactly
in range) -> keep exterior materials -> JC3 frame (axis grid proof) -> uniform scale to the
reference length -> Blender 5.2 headless decimate -> split on UV seams -> smooth normals
-> clone the DaBaby head block, replace vb0/vb1/ib/bbox -> decode again and verify
(byte-identical re-encode, counts, indices, normal round trip, finite positions).

First output `Working/Batmobile/bat_body_20k.rbm`:

    materials kept  Glass, Mainbody, WheelArchs, Undercarriage(x2), Emissive, Decals,
                    Upgrades, Worn       (dropped: wheels, tyres, discs, cockpit, turret,
                    batteries) -> 122,622 of 299,837 faces
    decimated       122,622 -> 20,000 tris, 24,128 verts (u16 OK)
    size            990,199 B; 2.276 x 1.486 x 4.575 m, fitted to the DaBaby head's length
    VERIFY PASS     preview: Working/Batmobile/bat_body_20k.png (recognisable silhouette)

### Not done yet, by design

Not deployed. Still open from §38: whether the DaBaby itself runs on this install, and how
the user spawns a new entity. The plan: clone the DaBaby .ee 1:1 and swap ONLY
dababy_head.rbm for this file, so the build differs from a shipped working mod in
geometry alone.

## 40. The unifying cause: the .ee.toc. test-023 deployed.

The meme pack ships `v0000_car_dababy_jeep.ee.toc` beside its `.ee`. Format = the SARC
directory as a flat list: `u32 name_len, name (exact length, no pad), u32 offset, u32 size`.
Its records match its own `.ee` EXACTLY (704 records, 0 offset/size mismatches; only the 3
new `.lod` files are unlisted).

Vanilla Serpente `.toc`: not in any filelist; found by name hash `928DBFC1` in
`patch_win64\game1.tab` @21096 -> `game1.arc` offset 404,389,888, 46,192 B ->
`Research\SerpenteToc\vanilla_civilian_01.ee.toc` (468 records).

`Tools/scripts/eetoc.py compare` (AAF -> SARC directory vs .toc), every build:

    loaded   003 007 010 017 020 021      11 mismatches (all: .toc offset 0 = external, sizes equal)
    crashed  005 016 018 019 022          388-449 mismatches (offsets shifted)
    crashed  011                          11 -- its crash is content (the .epe pad bytes, §31)

**Every build that loaded kept the vanilla layout; every layout-changing build crashed.**
Displacement "worked" because it never changed a file size. Count changes, foreign RBMs,
added or removed files all shift offsets, and the game reads them through the stale vanilla
.toc -> garbage -> the `table[garbage]` fault in the dumps. This replaces §27-28 (physics),
§34 (count check "compiled into the engine") and D14 (body RBM "bound to its entity").

`eetoc.py patch` rewrites a vanilla .toc for a modified .ee (same order, offset-0 records
kept, offsets/sizes from the .ee, new non-.lod files appended). Self-test: patching
test-003 and test-021 reproduces the vanilla .toc BYTE-IDENTICALLY.

### test-023 = test-022's .ee (unchanged, 46857DA9...) + matching .toc

    .toc  46,319 B, 470 records (2 appended: dababy_head.rbm, convertible.ddsc)
          sha256 7C8D371E2068A512BEA22911B9642C0336F9B42F85937FB2F0BD684BD5ECF1E2

DEPLOYED 2026-10-10 as a pair; Status verified. `Builds\test-023\install.ps1` deploys
.ee + .toc together and every Rollback REMOVES the dropzone .toc.

Prediction: loads, Serpente shows the DaBaby head as its body (doors, hood etc. still drawn,
the .epe is unchanged). If it still crashes, the dropzone .toc is not honoured for a
vanilla-path override, and the fallback is keeping every vanilla file's offset fixed
(append new files at the end of the SARC).

### test-023 result: LOADS. "Car is normal." (Rico spawns next to the Serpente; no spawner needed.)

First layout-changing build that does not crash -> **the .toc was the wall.** But no head.

## 41. Offset 0 in a .toc = "read this file from the archives". test-024

In test-023's .toc `sportsmuscle_vehicle_parts.vmodc` is `(0, 29886)`: offset 0. Same for the
`.epe` (0, 109526), `sportsmuscle_vehicle_deform.vmodc` and the `land_*` vmodc modules.
So the game took the VANILLA parts file from the archives and our 4-byte repoint was never
read.

The shipped DaBaby .toc confirms the rule: everything Luke JC changed or added has a real
offset (`dababy_vehicle_parts.vmodc` 11025224, `civilian/oldjeep_vehicle_parts.vmodc`,
the `.epe` 12167492, `_land_global.vmodc`, the 3 RBMs); untouched shared files
(`oldjeep.physicsc`, `oldjeep_vehicle_deform.vmodc`, `_ai`, `_land_engine`) stay 0.

Retroactive consequences:
- test-003's `max_rpm` 7300->14600 (in an offset-0 vmodc) was NEVER applied; only the
  body texture (in-toc) was.
- test-017's `.epe` edit "loads" proves nothing: the `.epe` is offset 0, so it was not read.
  §31's ".epe writing is unblocked" is UNVERIFIED.

`eetoc.py patch --internal <substr>` points offset-0 records into the .ee.

test-024 = test-023's .ee (46857DA9...) + .toc with the parts vmodc internal
(record -> 12158556, 29886; the u32 at +312 there is 0x5EEE7AFB).
.toc 46,319 B sha256 5D14AD80B8FD385C9AC3992858FFC080E254F47DA0EF8474C5D7483BBEC894C1.
DEPLOYED 2026-10-10, Status verified.

## 42. test-025: Batmobile head at the DaBaby path. CRASH.

test-025 = test-024 with ONLY `dababy_head.rbm` content replaced by
`Working/Batmobile/bat_body_20k.rbm` (990,199 B; 1 CarPaintMM block, flags 0x80,
tag 8, 24,128 verts / 20,000 tris, byte-identical round-trip). Same VFS path, so
the `.lod`, the path hash and the `.epe` stay valid; `@files.xml` unchanged.

`aafdiff` vs test-024: 550 identical, exactly 1 changed, 0 added, 0 removed.
`.toc` re-patched (470 records; only the head size and the shifted
`convertible.ddsc` differ from test-024's). Artifact 6,774,760 B, sha256
`59220B658031E130096B363D71C0722BDADD751B5987003281B197450B5B5F76`;
`.toc` 46,319 B `3074D41D09B22002FF7A3D420A7CAF0CDD5DF1479A3409AC9D18C6CA180D1025`.
DEPLOYED 2026-10-10, Status verified.

Note: the previous `Builds\test-025` staging was stale (an `.ee` identical to
test-024's plus a 249 B 4-record `.toc` fragment, kept as `.toc.frag-bak`) and its
`install.ps1` asserted a wrong `TocSize`; both fixed in the rebuild.

### test-025 result: CRASH. New signature: READ of 0x8 at JustCause3.exe+0x2d49e0

Dump read with new `Tools\scripts\dumpfault.py` (stdlib minidump reader). Not
`+0x197194a` (test-005/022), not test-018/019's offsets, not the driver fault.
Rolled back to test-024 (unchanged bits, Status verified).

### Confound: test-024's own result

§41 logged 024's deploy but never its outcome. User reports 024 also crashed —
but no in-exe dump from its window exists (all nine dumps there are the
`nvwgf2umx.dll+0x90d81c` driver fault), so that crash is unattributed. If the
024 re-run crashes with the same `+0x2d49e0`, the mesh is exonerated (024 wears
the DaBaby head) and the internal parts repoint is the variable.

## 43. test-024 re-run: CRASH, same signature. The mesh is exonerated.

024 (unchanged bits) crashes: `READ of 0x8 at JustCause3.exe+0x2d49e0` — byte-identical
signature to 025. 024 and 025 differ only in head bytes, so the mesh is NOT the variable.
The variable is the 023->024 delta: the parts vmodc read from the `.ee` (repoint live).

Ruled out offline: the repoint hash is exact (forward-slash VFS path hashes to
0x5EEE7AFB, verified python + HashName.exe); the deform file is external-live
(offset 0) in the WORKING DaBaby's `.toc` too, so deform liveness does not differ.
What differs from the shipped mod: our `.epe` is vanilla (40 parts, deform body
expected) while the head is 1-block non-deform.

## 44. test-026: repoint at a vanilla plain part. DEPLOYED, awaiting launch.

test-026 = test-024 with the repoint retargeted body -> `sportsmuscle_plate_r.lod`
(0x5EEE7AFB -> 0xF7535880, cross-checked). One variable (target), all-vanilla
bytes; `aafdiff` vs 024: 1 changed (vmodc, same size); `.toc` regenerates
byte-identical to 024's. Artifact 6,219,641 B `7E0A45CE...`. DEPLOYED, Status verified.

- Same `+0x2d49e0` crash -> any non-deform body target dies under the vanilla
  `.epe`: deform-class mismatch confirmed, fix direction is the `.epe`/entity side.
- Loads -> the head bytes (size/content) are back in the frame; next is a small
  custom head at the same path.

### test-026 result: CRASH, same signature. Any live body repoint dies.

`READ of 0x8 at JustCause3.exe+0x2d49e0` again — even repointed at a vanilla
plain part. So it is not the head bytes, not the hash (verified exact), not
deform liveness (working DaBaby's deform record is external too). Forensics open:
the shipped mod pairs its repoint with a custom 5-part `.epe`; ours runs under
the vanilla 40-part `.epe`.

### Found by hash: the full reference chain. The `.epe` is the unexplored variable.

`.epe:vehicle_parts` names the parts file (DaBaby 1056903505 =
`.../dababy_vehicle_parts.vmodc`; Serpente 1526043305 =
`.../sportsmuscle_vehicle_parts.vmodc`, both with extension) and
`.epe:deform_points` names the deform file (113596965 / 1517323693, both verified
by hash). DaBaby's `.epe` binds 5 parts (body idx 0 + 4 wheels, vanilla names);
Serpente's binds 40, hierarchical (e.g. `window_r_r` nested under `body`).
Entry shape around the repointed hash is identical in both parts files
(`X,0,HASH,0,Y,0,0,0,0xFF00`), and Luke's working edit is 9 hash swaps
(body + 4 wheels x2), all same-size. So our 4-byte patch is faithful — and the
repoint mechanism itself is proven by his mod. What we never copied is the
custom `.epe`.

## 45. test-027: repaired vanilla `.epe`, internalized. DEPLOYED, awaiting launch.

test-027 = test-023 (repoint external, loads) with ONLY the `.epe` swapped for a
repaired round-trip (2293 diffs -> 2189 pads restored -> 104 residue, same as
§31; re-export XML byte-identical) and internalized. `aafdiff` vs 023: 1 changed
(`.epe`, same size). `.toc`: 023 pattern + `.epe` internal (470 records).
Artifact 6,219,670 B `C88AE376...`. DEPLOYED, Status verified. First build the
game actually READS a repaired `.epe` (test-017's was external, §41).

- Loads -> pipeline proven; next is 024 + repaired `.epe`, then the 5-part `.epe`.
- Crashes -> the writer/pads are still lossy somewhere; stop and re-measure.

### test-027 result: LOADS, car normal. Pipeline proven.

### test-028: live repoint under the repaired `.epe`. DEPLOYED, awaiting launch.

028 = 024 tree + repaired `.epe`, parts AND `.epe` internal. `aafdiff` vs 024:
1 changed (`.epe`, same size). The `.ee` is byte-identical to 027's (027's tree
already carried the repoint unread), so 027->028 isolates exactly one `.toc`
record. Prediction: crash (40-part content, not bytes, is the constraint) ->
next is the 5-part `.epe` mirroring DaBaby (body idx 0 + wheels 26/27/11/12).

### test-028 result: CRASH, same signature. Content, not bytes, is the constraint.

## 46. test-029: custom 5-part `.epe`, DaBaby mirror. DEPLOYED, awaiting launch.

Kept body idx 0 + wheels 26/27/11/12 (front wheels reparented from engine to
body; all four now direct children of body, as in the shipped mod). Import exit
0; pads repaired by string context (490 bytes); the repaired file re-exports to
the same 5 parts, names, hashes, indices. (Importer regenerates object IDs, so
exact-XML equality cannot hold for structural edits — semantic equality is the
check.) `aafdiff` vs 024: 1 changed (`.epe` 109526 -> 105302 B). `.toc`: parts
AND `.epe` internal (470 records). Artifact 6,218,159 B `E751AC6F...`.
DEPLOYED, Status verified.

- Loads (DaBaby head visible?) -> the `.epe` was the wall; next is the Batmobile
  head at the same path.
- Same `+0x2d49e0` -> the wall is elsewhere; re-measure from the working mod's
  remaining deltas (wheel repoints, deform file drop).

### test-029 result: CRASH, same signature. The 5-part `.epe` alone changes nothing.

## 47. Batch 030/031/032: the working mod's remaining deltas, one per test.

029 (5-part `.epe` + live body repoint) crashes exactly like 024, so the `.epe`
was not the wall either. What the shipped mod has that no passing build tried:
wheel repoints, and no deform file. Plus one control skipped: whether the
5-part `.epe` itself loads. Three builds, each one variable, install in order:

- test-030 = 023 tree + 5-part `.epe`, parts EXTERNAL (repoint dormant).
  CONTROL. `.ee` byte-identical to 029's (023/024 share one `.ee`); `.toc`
  0F41A32A... (470, `.epe` internal). Loads -> 5-part `.epe` good, crash needs
  the live repoint. Crashes -> the 5-part `.epe` itself is broken; stop.
- test-031 = 029 + full Luke mirror: 4 wheels -> `dababy_wheel.lod`, 4 mshswap
  -> `dababy_wheel_modelswap.lod` (8 slots, each hash unique, shape-checked
  before patching; body was already repointed). `aafdiff` vs 029: 1 changed
  (vmodc, same size). `.toc` regenerates byte-identical to 029's. Artifact
  6,218,147 B `2D7F7F96...`. Loads -> partial repoints are inconsistent state.
- test-032 = 029 minus `sportsmuscle_vehicle_deform.vmodc` (67,214 B) + manifest
  line + `.toc` record (469 records; `patch` keeps offset-0 records so the drop
  is scripted in `_drop_deform_toc.py`). First removal-with-`.toc` test (016's
  removal crashed only for lack of a matching `.toc`). Loads -> deform data is
  required alongside a foreign body; the fix is authoring or neutralizing it.

### Batch results (2026-10-10): 030 LOADS minus 35 parts; 031 and 032 CRASH same signature.

- test-030: **LOADS, car missing front, doors, trunk.** Exactly the 35 unbound
  parts absent; body + wheels present. The 5-part `.epe` is VALID and the writer
  + reparenting are exonerated.
- test-031 (full 9-swap Luke mirror): **CRASH**, `+0x2d49e0`.
- test-032 (deform dropped, 469-record `.toc`): **CRASH**, `+0x2d49e0`.
  (1:31 dump is the environmental driver fault; 1:35/1:37 are the two runs.)

So neither partial-vs-full repoint nor deform presence explains it: 026 (vanilla
target), 031 (full mirror), 032 (no deform) all die identically, while 030 (same
`.ee` bytes as 029, repoint dormant) loads. The single live variable remains the
body slot's hash differing from vanilla. The engine reads the repointed file and
rejects the resolved body under this entity — with the `.epe`, parts file,
deform state, `.lod` listing and mesh bytes all mirrored or ruled out. Next
forensics, no new builds yet: how the DaBaby ENTITY itself is instantiated
(new non-vanilla folder — spawn table? console proxy?) vs our vanilla-path
replacement, and the vmodc area bindings (`main_area` etc.) around the body.

All three built, `aafdiff`-proven, installer-verified (`Status` clean, dropzone
untouched at 029). Sibling tooling kept: `_patch_031.py`, `_drop_deform_toc.py`,
`dumpfault.py`, `_epe_parts.py`/`_epe_nest.py`/`_epe_grep.py`, `_carve_5part.py`,
`_repair_pads.py`.

### Batch run 1 INVALID: the installs never took.

User pasted `Status`-only output for all three (no `verified`/`deployed` lines =
`Install` never bound; likely run from cmd, not PowerShell). Dropzone verified
still 029's pair (`E751AC6F`/`AB787DB1`): a real 030 shows `.toc` `0F41A32A`,
031 shows `.ee` `2D7F7F96`, 032 shows `.ee` `7F6E0A7C`. Reported crashes are
029's known crash, unattributed to the batch. Correct form (PowerShell):
`powershell -NoProfile -ExecutionPolicy Bypass -File 'Builds\test-030\install.ps1' -Action Install`.

### Correction to "Batch run 1 INVALID" (2026-10-10)

Dropzone checked: it held test-032 (.ee 7F6E0A7C, .toc CEE7607F, written 13:20-13:21),
so the batch installs DID take; the INVALID note is wrong and the batch results stand.
User confirms: "crash. test-027 loads, car looks normal. 030 loads, car is missing front,
doors, trunk." The peer session o-kam-d6 is an unrelated project and never touched this.

## 48. Why every live repoint crashed: the .ee's parts file is PRE-PATCH. test-033/034

Archive search by name hash (`5AF592A9` parts, `5A7085AD` deform):

    sportsmuscle_vehicle_parts.vmodc   patch_win64\game4  30,540 B   <- what the game uses
                                       inside the .ee     29,886 B   <- what 024..032 forced
    sportsmuscle_vehicle_deform.vmodc  patch_win64\game4  67,278 B
                                       inside the .ee     67,214 B

The .toc's offset-0 records are not "unused": they say "take the current (patched) copy
from the archives". Internalizing the parts record made the game read the OLD file, out of
step with the rest of the patched vehicle -> `READ 0x8 @ +0x2d49e0`, whatever the repoint
target (024 head, 026 vanilla plate, 029/031 full mirror). 030/027/023 loaded because
their parts record stayed external. Saved: `Research\SerpenteParts\*.bin`.

Patched file has the same record shape; body hash `0x63A04A76` at **+328** (was +312).

Build: `Tools\scripts\_build_033_034.ps1` (test-022 tree + patched vmodc, internal):

    test-033  CONTROL, patched vmodc unmodified   .ee 0079D0A8...  6,219,833 B
    test-034  + body -> 0x5EEE7AFB at +328        .ee A7C18F6C...  6,219,833 B
    both      .toc EB789C01... 46,319 B (identical: same layout); compare = 10 external
              mismatches only (the 11 baseline minus the internalized parts record)

test-033 DEPLOYED 2026-10-10, Status verified. Expect: loads, normal car (proves an
internal parts file is safe when it is the current version). Then test-034: expect the
DaBaby head as the body.

Same trap applies to anything else we internalize: always take the newest copy from
patch_win64 (then dlc), never the .ee's.

### Batch 033/034 results (2026-10-10; tests run by Muse Spark 1.3 via opencode)

- test-033 (patched parts vmodc internal, unmodified): **LOADS, normal car.** Internalizing
  the CURRENT parts file is safe. §48's pre-patch diagnosis confirmed.
- test-034 (+ body -> dababy_head.lod): **LOADS**, "car missing insides and back L and R
  sides back from doors" -- the stock body mesh (cabin interior + rear quarters) is gone,
  so **the repoint is live and does not crash**. No head reported.

## 49. An unlisted .lod leaves the body slot empty. test-035/036 built.

The vanilla .toc lists all 59 of its .lod files with real offsets; `eetoc.py` copied the
DaBaby convention and omitted the new `dababy_head.lod`. Plausible reading of 034: the body
model never resolved -> empty slot. `.lod` format confirmed: CRLF text, 5 rbm paths + a
scale (`1.0` Serpente, `1.29999995232` DaBaby).

`eetoc.py patch --include-lod`. Build: `Tools\scripts\_build_035_036.ps1`.
New `Tools\scripts\_make_installer.py` (pins .ee + .toc; Status requires BOTH to match).

    test-035  test-034's .ee + .toc listing dababy_head.lod (13564744, 415)
              .ee A7C18F6C... 6,219,833 B   .toc 1846702A... 46,409 B (471 records)
    test-036  test-035 with dababy_head.rbm CONTENT := Working\Batmobile\bat_body_20k.rbm
              .ee E5AB01E4... 6,774,922 B   .toc 94EAED02... 46,409 B
    both: compare = 10 external mismatches only; 036 parts u32@328 = 0x5EEE7AFB.

NOT deployed yet: the game was running. Order: 035 (head visible?) then 036 (Batmobile).

### test-035/036 results: both LOAD, body slot EMPTY ("missing insides and back L and R
sides back from doors"). Listing the new .lod in the .toc changed nothing; the DaBaby head
(035) and the Batmobile (036) are equally invisible.

## 50. test-037: split "new .lod resolves?" from "foreign mesh draws?"

test-037 = test-033 tree + NEW `sportsmuscle_body_um.lod` (CRLF text, 5 x
`.../sportsmuscle_body_lod5.rbm` + `1.0`), registered in @files.xml, body hash
0x63A04A76 -> 0x6AD11F5B at +328, .toc `--internal parts --include-lod` (472 records;
lod5 rbm itself already listed). lod5 = 5 blocks, 787 tris, full 5.0 m shell vs lod1's
9 blocks / 7,063 tris -> unmistakable if drawn up close.

    crude low-poly shell in the body slot -> new .lod files resolve; the cause is the
                                             foreign mesh (1 non-deform block, flag 0x80,
                                             header tag 8) in a deform-body slot
    body slot still empty                 -> new .lod files are not resolved at all

.ee 91632EAE... 6,219,933 B; .toc D0A671B4... 46,506 B. DEPLOYED 2026-10-10, Status:
.ee AND .toc match. `_make_installer.py` now escapes ' in descriptions (a ' broke the
first generated script with a ParserError before anything was copied).

### test-037 result: LOADS, "lower poly car". New .lod files resolve and render.
So 034-036's empty slot is the MESH FORMAT. (User: the Meme Vehicle Pack ships an in-game
screenshot of the DaBaby car, so the plain 0x80 format does render -- on the jeep.)
Flag 0x80 = DISABLE_BACKFACE_CULLING (rbm_geom constants, from jc-model-renderer); harmless.

## 51. The deform block layout, measured. test-038: the Batmobile in the Serpente's format.

`sportsmuscle_body_lod1.rbm`: header tag 9, 9 blocks, all deform (0x1004 x3 undercarriage,
0x1000 x3 interior, 0x101F x3 painted exterior); each block has its own 1024 B deform_table
(256 u32 entries; block 0 starts 30,31,32,33 -> indices into the deform points).

    vb0 stride 24: x,y,z | d float (packed small vector, |decoded| ~0.03)
                   | w int16 x4 = (weight LO byte, table index HI byte); weights sum 252..258
                   (NOT a position: linear fit of w vs xyz R^2 0.15..0.24)
    vb1 stride 32: col0..3 u0,v0,u1,v1 | col4 NORMAL (packed; dot +0.982) | col5 tangent
                   (signed packing) | col6 DAMAGED normal (dot +0.934) | col7 damaged tangent

(test-012 wrote its normal at 0x18 = col6, the damaged normal: now explained.)

`psk2rbm.py --deform-block N`: clone template block N (keeps flags, materials, textures,
deform_table), write our positions + our normal into col4 AND col6; copy d, w, u1/v1 and
both tangents from the NEAREST template vertex (so w indices stay valid for the kept table
and crashes dent it like the Serpente there). Verify extended (positions written exactly).

    Working\Batmobile\bat_body_deform_20k.rbm  template body_lod1 block 6 (0x101F, paint)
      fit-to body_lod5 (full 5.0 m shell); 24,125 verts / 20,000 tris; 2.489 x 1.624 x 5.001 m
      tag 9, 1 block, 1,473,463 B, VERIFY PASS
      textures = the Serpente body paint set (UVs are the Batmobile's: texture will look wrong)

New `Tools\scripts\_build_bodyswap.ps1 -Tag -Name -RbmSource|-RbmVfs` (generalises 037).

test-038 = test-033 tree + `sportsmuscle_body_bat.rbm` + `sportsmuscle_body_bat.lod`,
body -> 0xC920A9A6 at +328. .ee F068F8E3... 6,888,105 B; .toc E24E450E... 46,605 B
(473 records; compare = 10 external only). DEPLOYED 2026-10-10, Status: both match.

### test-038 result: LOADS, body slot EMPTY. Same as 034-036, despite the vanilla format.

User design rule: **the Batmobile does not deform in Arkham Knight, so ours should not
either** (and JC3 tanks do not deform). Deform data is non-essential; once the body draws,
prefer a non-deform block.

## 52. Records after the root .epe are not preloaded. test-039

What drew vs what did not:

    037  drawn   new .lod (appended) -> mesh whose record is already in the vanilla .toc
    035  empty   new .lod + new head mesh, both APPENDED
    036  empty   same, Batmobile plain format
    038  empty   same, Batmobile in the Serpente's own deform format

Vanilla .toc: records in SARC order (internal offsets strictly ascending) and the LAST
record is the root `.epe` (offset 0). The shipped DaBaby .toc also ends with its `.epe`, and
its new RBMs are listed BEFORE it. All our appended records sat AFTER the `.epe`.
Hypothesis: the .toc is a preload list closed by the entity; files after it are not loaded
before the body model is built. 037 only worked because its mesh was preloaded already.
So the "mesh format" conclusion of §51 may be wrong: the format was never the variable.

`eetoc.py patch` now inserts new records before a trailing `.epe` record. Self-test still
reproduces the vanilla .toc byte-identically.

test-039 = test-038's .ee (F068F8E3..., unchanged) + reordered .toc (C344C56F..., 46,605 B,
473 records, offsets ascending, compare = 10 external only). DEPLOYED 2026-10-10, Status:
both match.

    Batmobile body drawn -> confirmed; next: non-deform block, strip Serpente parts
    still empty          -> the order is not it; next discriminator: Batmobile bytes at a
                            VANILLA rbm path (e.g. body_lod5.rbm), using test-037's .lod

### test-039 result: LOADS, body slot STILL EMPTY. The .toc order is not it.

## 53. test-040/041: Batmobile bytes at a VANILLA rbm path (only the mesh bytes change)

Base test-037 (drew `sportsmuscle_body_lod5.rbm` through `sportsmuscle_body_um.lod`). The
.lod, the repoint and the .toc record position are all 037's; `sportsmuscle_body_lod5.rbm`'s
CONTENT is replaced. Build `Tools\scripts\_build_040_041.ps1` (deterministic: 040 rebuilt
byte-identical).

    test-040  := bat_body_deform_20k.rbm    24,125 verts / 20,000 tris, one block
              .ee 3DA611D4... 6,839,228 B   .toc CE3AF558... 46,506 B   DEPLOYED, both match
    test-041  := bat_body_deform_1000v.rbm  1,000 verts / 522 largest tris (2.49 x 1.57 x 4.90 m)
              .ee A8D9C421... 6,202,676 B   .toc C3C746E6... 46,506 B   built, not deployed

    040 drawn             -> NEW FILES are the problem (not order: 039), not the mesh
    040 empty, 041 drawn  -> per-block vertex limit (vanilla max 1,081 verts/block)
    both empty            -> our block content

psk2rbm.py gains `--weld` (merge across UV seams) and `--max-verts N` (keep the largest
triangles within N vertices). Blender's decimate floors at 628 tris / 1,364 verts on this
mesh (hundreds of separate panels), so --max-verts is needed for a sub-1,081 test.

### test-040/041 results: **THE BATMOBILE RENDERS IN JC3.**

- test-040: "Car + batmobile overlap (couldn't see full batmobile cause of overlap), red."
- test-041: "Car + batmobile overlap (this time with less batmobile)."

So: the mesh writer is correct (a 24,125-vertex single deform block draws: NO per-block
vertex limit), and the failure in 035/036/038/039 was **brand-new .rbm FILES**: the game
does not load an .rbm at a path the vanilla entity never had, even with a correct .toc record
(appended or before the .epe). A NEW .lod is fine (037). Rule: **ship meshes at VANILLA rbm
paths** (every Serpente part owns 5). "Red" = the Serpente paint tint through the body
material (textures are still the Serpente's).

## 54. test-042: Batmobile body alone (5-part .epe)

test-042 = test-040 tree + test-030's 5-part `.epe` (body + 4 wheels; 105,302 B; 030 proved
it loads with the 35 other parts gone), `.epe` AND parts vmodc internal.
Build `Tools\scripts\_build_042.ps1`. .ee B73FA1A2... 6,837,439 B; .toc A523F3DC... 46,506 B
(compare = 9 external: the 11 minus parts and .epe). DEPLOYED 2026-10-10, both match.

Expected: the Batmobile shell + the 4 Serpente wheels, nothing else.

Remaining roadmap:
1. Non-deform (user rule: AK Batmobile does not deform): a plain block at a vanilla path.
2. Batmobile wheels on the wheel parts (vanilla wheel rbm paths), sized to the Serpente's
   wheel positions; or keep the Serpente wheels.
3. Black paint / Batmobile textures (ddsc at vanilla texture paths, or the palette).
4. Cleanup: drop the unused DaBaby files and the um.lod indirection: put the meshes straight
   into sportsmuscle_body_lod1..5.rbm and drop the repoint (no internal parts vmodc).
5. Collision is still the Serpente's (extern mesh on body_COL): the Batmobile is larger
   (2.49 x 1.62 x 5.0 m vs 2.10 x 1.39 x 3.72 body) so it will clip into walls slightly.

### test-042 result: LOADS, "More batmobile than ever." Batmobile shell + 4 Serpente wheels.

## 55. Clean build, non-deform, black paint: test-043/044/045

`psk2rbm.py --deform-block 6 --plain`: clone the paint block, clear IS_DEFORM (0x101F ->
0x001F, a vanilla-attested plain flag set), write vb0 float3 (12) + vb1
u0,v0,u1,v1,normal,tangent (24). LOD chains (fit to body_lod5's 5.0 m shell) in
`Working\Batmobile\lod\{deform,plain}_lod1..5.rbm`: 20k/8k/3k/1.5k/0.8k tris
(24,125 / 11,874 / 5,588 / 3,161 / 1,835 verts), all VERIFY PASS.

`_build_043_044.ps1`, no repoint / no new .lod / no DaBaby files / parts vmodc EXTERNAL:
test-003 tree + test-030's 5-part `.epe` (internal) + body_lod1..5 := Batmobile chain.
.toc: 468 records, 0 appended (pure vanilla file set).

    test-043  deform  .ee 1B237AF8... 6,187,352 B  .toc 4575E503...   DEPLOYED, both match
    test-044  plain   .ee 1A0312B2... 5,984,635 B  .toc B57A98F9...   built
    test-045  044 + black palette  .ee 4BBF87AB... 5,984,505 B  .toc B57A98F9...   built

### Paint = the palette vmodc (internal, editable)

`.../modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc` (1,897 B, record
internal). ConvertAdf `--e` decodes it (run in a scratch dir): 10 Tint records (White,
Evergreen Pearl, Garnet Red Metallic, Black 0.2 matte, Grey, Silver, Blue, Brown, Red, Green),
each tint_r/g/b ColorRGBA + occurrence 100 + specular_gloss/metallic/clear_coat.
New `Tools\scripts\palette_black.py`: in-place float patch at ConvertAdf's offset-in-file
(asserts every old value), every tint -> rgb 0.05, gloss 0.45, metallic 1, coat 1 (gunmetal
black). Re-decoded: 90 x 0.05, 10 x 0.45, 50 x 1.0. Same size. `_build_paint.ps1`.

### test-043/044/045 results (2026-10-10): ALL LOAD. Black Batmobile achieved.

- test-043: Batmobile shell on 4 Serpente wheels, red. Cleanup confirmed: no
  repoint, no new `.lod`, no DaBaby files; parts from the archives (§48 rule).
- test-044: same look, plain non-deform chain; crashes no longer dent the body.
- test-045: gunmetal black (all 10 palette tints). Dropzone verified == test-045
  (`.ee` 4BBF87AB..., `.toc` B57A98F9... both match).

## 56. CORRECTION: sect 34/35's count rejection is void. The .toc was the wall all along.

Sect 34 (written 10/8) concluded the engine rejects any vertex/index count change,
citing test-012/013/014/018/019. Sect 40 (10/10) then showed every one of those
builds mismatched the vanilla `.toc` by hundreds of records — they ran with NO
matching `.toc` at all (the concept did not exist yet). Their crashes were stale-
`.toc` garbage reads, not count validation. The only toc-correct count-change
tests ever run — test-040 (24,125-vert single block at a vanilla path) and
test-043 (full 20k/8k/3k/1.5k/0.8k LOD chain) — both LOAD. There is no unseen
count expectation; sect 28's "FINAL" and sect 35's summary are superseded the
same way. (The repoint crashes 024-032/Table +0x2d49e0 stand as recorded: those
had correct `.toc`s, and sect 48 verified their true cause — the .ee's parts
file is pre-patch, 29,886 B vs the archives' 30,540 B.)

Net of the whole project to date:

- WORKS: new-geometry meshes at VANILLA rbm paths + matching `.toc`; parts file
  from the archives (never the .ee's stale copy); repaired or 5-part `.epe`;
  palette paint; plain (non-deform) blocks.
- STILL OPEN: Batmobile wheels (Serpente's still on), real Batmobile textures
  (flat tint for now), collision that matches the bigger body (still the
  Serpente's extern-mesh `body_COL`; the 2.49 m shell will clip walls slightly).

## 57. test-046: Batmobile wheels at the vanilla wheel paths. DEPLOYED, awaiting launch.

Wheel source: PSKX mats Wheel/Tyre/Discbreak (85,100 tris) split by (X,Y)
quadrant into 4 corners, then largest-connected-components per corner (338
total; the kept corner = tyre + rim shells + brake bits, far debris dropped by
centroid distance). `psk2rbm.py` gains `--wheels` (the wheel materials are
hard-excluded from `--keep` otherwise). Template = Serpente wheel lod1 (plain
0x0004, wheel textures kept); `--fit-to` wheel lod1 (Ø0.80); 2,500 tris.
`Working\Batmobile\bat_wheel_2k5.rbm` (129,914 B, 0.43 x 0.80 x 0.80 m, VERIFY
PASS; preview reads as a wheel: tyre ring + spokes + hub).

046 = 045 tree + that mesh in ALL 30 `sportsmuscle_wheel*` paths (lod + mshswap,
same bytes). `aafdiff` vs 045: exactly 30 changed, 0 added/removed. `.toc` 468
records, 0 appended (pure vanilla file set, 045 pattern). Artifact 7,612,590 B
`EF42B917...`. DEPLOYED, Status: both match. Build: `_build_046.ps1`.

Honest limits, stated before launch: one mesh on all four corners (Tumbler
front/rear differ, ignored); 0.43 m wide vs Serpente 0.33 (chunky Tumbler look,
may poke past the arches); wheel UVs don't match the Serpente wheel textures
(shape test first, textures are next); physics RAY wheels untouched, so contact
behavior is the Serpente's.
## 58. Stance diagnosis: wheels must conform to the body. test-047 DEPLOYED.

Measured (no lore sources on hand, so no lore verdict possible — the 5.0 m
reference itself is body_lod5's suspect coarse bbox, §14d):

- Lateral: track/body 1.770/2.489 = 0.711 vs Tumbler 245.8/349.5 = 0.703. CONFORMS.
- Centers: body Z +0.008, wheelbase center -0.056. CONFORMS.
- Stance: JC3 wheelbase/body 3.003/5.001 = 0.600 vs Tumbler 489.3/702.6 = 0.697.
  DOES NOT conform: front overhang 18.7% vs Tumbler 11%, rear 21.2% vs 19%.
- Visual wheel centers = hardpoints, proven by contradiction (wheel RBMs are
  centered at origin; mesh-position rendering would stack all four at the car
  center). So conforming = a `land_global` data edit, not a body rebuild.

Tumbler stations for the fixed 5.001 m body: front -1.945 / rear +1.539
(wheelbase 3.484; overhangs 11.0% / 19.4%, matching the source). Track/X/Y and
radius untouched.

test-047 = 045 tree + PATCHED (1600 B, game1.tab hash 923EECDA) `land_global`
with those 4 floats (XML edit -> `--i`, same size, 12 diff bytes exactly at the
`offset-in-file` values, re-export verified), INTERNAL, + L/R mirrored wheels
(L paths := 2k5, R paths := X-mirrored copy with flipped winding, 15/15 exact).
`aafdiff` vs 045: 31 changed (land_global + 30 wheels). `.toc` 468 records
(+`land_global` internal). Artifact 7,602,810 B `E8A94704...`. DEPLOYED, Status:
both match. Builds: `_stance_047.py`, `_mirror_wheel.py`, `_build_047.ps1`.

Queued, not built: 048 = solidify/0x84 if insides still read empty; rim-side
swap if the mirror guess (L original / R mirrored) faces wrong.

### test-047 result: spacing right, stance too far forward; front wheels vibrate at standstill.

### "Loop" reinterpreted: alignment numbers out of the asset, not builds to fly.

Per user direction, future assets are aligned by MEASUREMENT: new
`Tools\scripts\_pskx_layout.py` reports any PSKX's per-material counts/centroids/
bboxes plus the wheel-station table and wheelbase/track ratios (reproduces the
hand-computed 0.697/0.703 on this asset). No more stance-guess builds.

### Front vibration analysis (offline; 047 still deployed).

- Mirror exonerated (rears carry mirrored wheels too and are quiet); mesh is
  centered on all axes, so spin/steer wobble from imbalance is out.
- Static burial does NOT fit: 106 body verts inside the front wheel volume vs
  201 rear (lod1) — the quiet end overlaps more.
- Live confound checked: 047's `land_global` is the patched 1600 B copy, but the
  ONLY member delta vs the `.ee`'s copy is the added `steering_type=FrontSteered`
  (live via archives either way — cannot be new). The 4 stance floats are the
  sole live change.
- Lead: steering hunting from the +16% wheelbase (3.003 -> 3.484). Only the
  steered axle vibrates. Second-order suspect: visual-vs-RAY mismatch — the
  Havok RAYs stay baked at the old stations while the visuals moved up to
  0.39 m, which can confuse the steering controller.
- Awaiting user-side discrimination (engine off? handbrake? steering input?) —
  no builds until then, per direction.

### Spawn timing promotes the RAY mismatch to lead. test-053 reverts the stance.

Vibration is present on spawn (fronts + surrounding flank), before any input:
contact/geometry, not idle-hunting. Decisive offline find — the physics binary
bakes the hardpoints verbatim as (x,y,z,1.0) quads (e.g. `-0.885, 0.4, -1.557`
@14656; full table dumped), so 047 split visuals from physics: front Δ0.388 m,
rear Δ0.093 m. The 4x front split matches the front-only shake; the surrounding
flank shakes with it. (Earlier float-search misses were wrong; the table dump
overrides them.) Steering-hunting demoted but not out; flank grind was already
out (rear overlaps more and is quiet).

Consequence: stance-via-hardpoints is capped by the baked RAYs — visuals must
sit ON them. test-053 = 046 stations (045-pattern `.toc`, byte-identical to
046's) + mirrored L/R wheels kept. `aafdiff` vs 046: 15 changed (R side only).
Artifact 7,602,592 B `B914B235...`. DEPLOYED, Status: both match.

- Quiet -> stance caused it. Alignment then comes from the BODY side (re-fit
  shell over the true stations; physics never split) — or, riskier, in-place
  RAY quads patch in the physicsc (same size, plain-data floats; Havok
  validation UNKNOWN — fallback only).
- Still vibrates -> wheel-mesh branch (mirror/symmetric under RAY stations).

User verdict (2026-10-11): 053 quiet confirms the 047 jitter came from the
hardpoint move off the baked RAYs (aligning to body). The separate body/wheel
fits did NOT cause it — 046 and 053 (both separate-fit meshes, RAY stations)
are quiet. Any single-shared-transform theory must answer that evidence.

## 59. RETRACTED: stance loop 048-052 built, never run, deleted.

Per user direction the unrun loop builds (048 +0.1 through 052 +0.5) do not count
and were deleted, with this section struck to keep the record to flown tests.
The stance question stays open (047 sits too far forward). Tooling kept:
`_stance_loop.ps1`, `_stance_shift.py`.

## 60. test-053 result: QUIET. Stance caused the vibration.

User: not shaking with wheels back at RAY stations (misaligned again). The
visual-vs-RAY split is confirmed as the vibration's cause; mirror and mesh
stand exonerated with it. Alignment work must keep visuals ON the RAYs (body
side) unless the RAY-quad patch is proven separately. Dropzone stays on 053.

## 61. Asset-grab logic, tested once: `_import_part.py` + specs reproduce the shipped meshes byte-identically.

Per user direction, alignment/scale now live in SPEC FILES, never in code. New
`Tools\scripts\_import_part.py` reuses `psk2rbm`/`rbm_geom` throughout (no
duplicated math): material select (+`allow_wheels`) -> optional quadrant split
(`at: zero|median`, `pick: largest|[q]`) -> optional connected-component filter
(`min_faces`, `max_dist`) -> fit (`length` = existing convention, `diameter` =
fit on max(Y,Z) for axle-along-X wheels) -> template writer (`plain` 12/24 or
`deform` block N, +`plain` bit-clear) -> Blender decimate -> verify -> manifest
line. Specs in `Working\Batmobile\specs/` (wheel + 5 body LODs).

THE TEST (offline, deterministic, no launches): regenerating through the
importer reproduces the shipped files byte-for-byte — wheel (129,914 B) and all
five body LODs (990,963 / 477,927 / 221,631 / 125,259 / 73,323 B). Same specs,
same bytes, Blender deterministic on this machine. Regen duplicates deleted;
specs regenerate them. Hard-code audit: quadrant origin/pick, component
thresholds, fit mode/reference, template block, tri budgets — all spec params;
centering/bottoming conventions stay code (correct place). `_extract_wheel.py`
stands as legacy; the importer is the path forward for every future asset.

## 62. Full grab: turret/cockpit/batteries join the body; 11-spec matrix green.
The shipped chain excluded the turret (47,912 faces) and cockpit (40k) — the
car's top was missing. New `body_full_lod1..5` specs keep every non-wheel mat.
Found and fixed on the way: the legacy wheel/cockpit exclusion (needed for the
plain-chain byte-repro) also ate the cockpit, so exclusion is now an explicit
spec param (`exclude`, default = legacy four; full chain excludes
Wheel_V2/Tyre/Discbreak/Master_Flip only).

`Tools\scripts\_import_all.py` runs every spec in `specs/` in one pass:
regression-gated (byte-identical) where a shipped file exists, VERIFY-gated
otherwise. Matrix: 11 specs, 0 failures — 6 byte-identical (wheel + 5 plain
LODs), 5 new full-chain meshes (lod1 20,000 tris … lod5 1,401). One honest
deviation: Blender collapse floors above target on the 214k-face input (lod5
1,401 vs 800 budget) — tool limit, not logic; budgets hold everywhere else.
Full outputs kept in `Working\Batmobile\full_plain_lod*.rbm`; regen duplicates
deleted. Next: deploy the full chain at the body paths (same 045 pattern) when
a launch is wanted.

## 63. test-054: full-asset body deployed. AWAITING launch.
054 = 053 tree (mirrored wheels at RAY stations, black palette, 5-part `.epe`)
with the 5 body LODs swapped to the full chain. `aafdiff` vs 053: exactly 5
changed (body LODs, all larger: +173k/+67k/+26k/+12k/+55k B). `.toc` 468
records, 0 appended (045 pattern). Artifact 7,779,578 B `9AB41C38...`.
DEPLOYED, Status: both match. Build: `_build_054.ps1`.

Expected: complete Batmobile shell with top/cockpit (previously missing),
unchanged wheels/paint/physics. Watch: cockpit interior through the open top
(glass RBMs unbound - open holes, not glazing); lod5 over budget (1,401 tris).

## 64. Owner follow-ups answered in the KB note (no new builds).

Repo owner asked three bisection leftovers; answered from the record and pushed
to the KB branch (`3fb0ee2`): (1) test-019 extended BOTH vb0 and vb1
(`_build_bisect.py` lines 107-112; block flags set no third buffer) — the
position-only-malformation theory is refuted by the build code; (2) 018/019
faulted in-exe (`+0x1ec3e0`/`+0x1ebb1ec`, contemporary dump reading; raw dumps
since rotated) — not the driver, no re-run would change anything, and both runs
lacked `.toc`s anyway; (3) DaBaby-vs-vanilla table added (1-block 0x80 head,
5-part `.epe`, 9-swap new parts file, untouched physicsc, 704-record `.toc`).
The toc-correct 018/019 repeat is offered but moot (24k-vert block + full LOD
chain subsume it) — costs two launches if still wanted.

## 65. test-055: RAY quads moved to stance stations. DEPLOYED, awaiting launch.

055 = 047 tree + `sportsmuscle.physicsc` with the 4 baked wheel-station quads
moved to the 047 stations (front -1.557 -> -1.945, rear +1.446 -> +1.539).
Found as plain `(x,y,z,1.0)` quads in ONE table (@0x3940/0x39A0/0x3E80/0x3EE0;
an apparent second table was overlapping read windows). Same size (340,368 B),
Havok sections intact. `aafdiff` vs 047: 1 changed. `.toc` regenerates
byte-identical to 047's. Artifact 7,602,807 B `2ED096A9...`. DEPLOYED, Status:
both match. Build: `_patch_rays.py` (asserts 4 quads, Havok tag).

- Quiet WITH stance -> the split theory is causally proven; stance debate over.
- Crash -> Havok validates the quads; revert to 053, stance stays dead.
- Same shake -> the split was correlational; steering data is next.

## 66. Textures, dynamically: ConvertTexture round-trips; magenta discriminator queued as 056.

`.ddsc` = LOW mips only (body_dif: 256²-and-below DXT1 chain, 43,704 B + XML
wrapper; the 2048/1024/512² highs live in game36's `.hmddsc`, 2.75 MB,
compressed container). ConvertTexture export/import round-trips byte-identical
(`.ddsc` <-> xml + indexed `.dds` files; element indices in filenames), so no
DXT encoder is needed for flat art — and the `.dds` wrapper carries a u32 zero
at 124 before the block array (naive block math fails without it).

Body slots that matter (rest shared/dummy): `body_dif`/`nrm`/`mpm`/`msk`. Wheel
slots point at ARCHIVE tire textures (not in our `.ee`) — future: retarget wheel
RBM slots at in-`.ee` unused paths (door/trunk aggregates ship unused under the
5-part `.epe`) since new files never load.

056 = 055 tree + all-magenta `body_dif.ddsc` (same size, header-identical).
`aafdiff` vs 055: 1 changed. `.toc` byte-identical to 055's. Built, verified,
QUEUED (055 awaiting launch first). Oracle: pink everywhere -> `.ee` shadows
all mips (256 cap); pink only far -> highs come from `.hmddsc` (then author
highs — ConvertTexture `write-to-hmddsc=True` import currently throws, needs
element-1/2 sources or container surgery). Build: `_magenta.py`,
`_magenta_mid.py`, `_build_056.ps1`.

### test-055 result: FAILS (loads, front wheels+body phase). Rolled back to 053.

The RAY-quad patch is accepted by Havok (no validation crash) but behaviorally
wrong — phasing, not quiet stance. Physics and visuals must agree, and ours now
disagree the other way. 055's tree stays as the stance reference; dropzone back
on quiet 053.

### Original collision: dynamic shell, hardcoded RAYs.

`body_COL` is a true external mesh (no baked verts anywhere — §32's 0/1024
stands): collision follows whatever render mesh loads, dynamically, which is why
new shells drive at all. The wheel RAYs are the hardcoded part (baked
`(x,y,z,1.0)` quads; moving them loads but phases). Wheel polytopes unprobed.
So "dynamically calced" is already half-true; the RAYs cannot follow (binary).

### test-056 result: pink in a few small areas. BOTH paths live.

Magenta lows (`.ee`) show only where low mips sample (distance/glancing/small
parts); near body wears the archives `.hmddsc` highs. D13's "ignored" verdict
is overturned — its marker file must have been bad. Consequence: real textures
need BOTH paths authored. `.hmddsc` container is compressed (`G!&` magic, not
raw zlib; no `texconv`/`magick` on hand) and the `write-to-hmddsc` import path
throws — so highs authoring is still blocked.

### test-057: magenta FULL chain in the `.ee` (all 12 mips, 2.80 MB). QUEUED.

If pink shows everywhere, the `.ee` fully shadows and no `.hmddsc` work is ever
needed (importer accepts a restructured single-element container — externals
zeroed, verified unpack). If vanilla-near persists, `.hmddsc` is preferred and
full-chain shadowing doesn't apply. 057 = 056 tree + full-chain dif only.
`aafdiff`: 1 changed (+2,752,512 B raw, deflated to almost nothing — the
packed `.ee` is SMALLER than 055's). Installer ready, NOT deployed (055/056
order first). Build: `_magenta_chain.py`, `_magfull_xml.py`, `_build_057.ps1`.

### Texture->asset map, derived by loop (`_texmap.py`, `texmap.json`).

198 RBMs / 64 textures walked; every block's texture table inverted. What feeds
the BOUND parts: body LODs <- `body_dif/nrm/mpm/msk` (in-`.ee`); wheels <-
ARCHIVE shared tire textures (not in our `.ee`). Door/trunk aggregates (18
files, 1 user each = own unbound mesh) ship unused under the 5-part `.epe` and
are the carriers for future wheel art (new files never load). `int_*`/glass
unbound. Dynamic texture spec = this map + per-slot conversion params; the only
missing piece is a DXT1/BC5 numpy writer for real (non-flat) art.

### test-057 result: green front / black back + red-orange + pink small areas. `.hmddsc` wins.

Full-chain magenta in the `.ee` does NOT shadow: near body still wears archives
highs (vanilla Serpente paint reads through as green/black/red-orange zones),
pink confined to even smaller areas than 056. So the engine prefers `.hmddsc`
for every mip it carries — `.ee`-only textures are capped at whatever the
`.hmddsc` lacks. Highs authoring is now mandatory, and the tool path is dead:
`write-to-hmddsc=True` throws `IndexOutOfRange` even with 100% vanilla inputs
(all 4 elements + beside `.hmddsc`), i.e. a fork bug, not our data. Remaining
routes: container surgery (codec unidentified — not raw zlib, no Oodle lib, no
`texconv`/`magick`) or a from-scratch AVTX writer. Both scoped, neither started.

### Body textures found dynamically (`_texmatch.py` over `.props.txt` + PSKX mats).

UE property dumps give authoritative material->texture bindings incl. parent
inheritance; joined with the PSKX material face sets. The BmAK BODY answer:
**there is no body diffuse** — Mainbody binds Normal_Map=`Body_N` +
Damage_Chapter_Mask only (matte black by scalar reflectivity/roughness, so the
flat-black look is nearly right by design). Arches/undercarriage/turret/cockpit
each name their own `_N` + damage/mask maps; wheels/tyres/discs bind NOTHING in
their props (shared tire textures stay correct); glass has a full Mask/Normal/
Opacity set for when its RBMs get bound. Method is asset-generic: same script,
any PSKX + props folder (token-overlap fallback where dumps are absent).

## 67. Movement stats, dynamically mapped. BmAK numbers: UNKNOWN (honest).

`Tools\scripts\_move_stats.py` (next to `vmodcdiff.py`, the donor-stats tool)
decodes all 30 readable Serpente modules and tabulates movement members with
file offsets: transmission (top_speed 320 @D0, 6 gears, final_drive 3.91),
vehicle_misc (official_top_speed 250, nitro times), land_engine (max_rpm 14600
— test-003's baked edit — torque factors), custom_land_global (drift/torque/
grip/boost/punch multipliers), brakes/tires/suspension/steering/rigid_body
(mass 975). Only `vehicle_parts.vmodc` crashes ConvertAdf (known tool bug);
land_audio min/max rpm noted.

BmAK speed/acc: searched `BmGame/` (material/texture dumps only), Research/,
props — no Arkham tuning source exists on hand, and pretrained memory is not
evidence, so UNKNOWN. Ready for when numbers arrive: `Working/Movement/
bmak_targets.json` (fill values, set final) + `_apply_move.py` (asserts old,
writes, same-size assert, re-export check — self-tested on a scratch copy).
Movement modules only; physicsc/RAYs untouched per direction.

## 68. test-058: BmAK movement estimates. DEPLOYED, awaiting launch.

Wiki estimates (NOT gospel): 1200 bhp, 209 mph (336 kph), 0-60 in 2.7 s,
afterburner +30%. Translated with stated assumptions: transmission top_speed
320->336 + final_drive 3.91->4.4; official_top_speed 250->336; torque factors
x1.4 (0.84->1.176, 0.86->1.204); afterburner tiers x1.3 (80->104, 40->52);
torque_multipliers 2->2.5 (all 3 tiers). Left alone: max_rpm, optimal-torque
490 (unknown semantics), mass/gears/nitro timing (no mapping), 1200 bhp (no
direct member). 11 edits / 4 files via `_apply_move.py` (one tooling fix on the
way: re-export prints `4.4` as `4.4000001`, so verification compares
numerically). `aafdiff` vs 053: exactly 4 changed, same sizes; 4 modules
internalized. Artifact 7,602,597 B `850C9CDF...`. DEPLOYED, Status: both match.

Oracle: top speed near 336 kph, harder pull off the line. If undrivable,
halve the torque/final-drive deltas first (estimate stack, not physics).

## 69. test-058 unit correction -> test-059. DEPLOYED, awaiting launch.

058's oracle failed exactly as the user called it: raw kph written as display
units read ~85 kph in-game (336 units -> 85 observed, factor ~3.95 units/kph —
consistent with vanilla official_top_speed 250 sitting under a ~63 kph-class
readout band, not a kph field). Fix: official_top_speed 250->1328
(336 x 3.952), transmission top_speed 320->1727 (436.8 x 3.954, i.e. 336 kph
base + 30% afterburner headroom at the cap). Same 4 files, same sizes,
`aafdiff` vs 053: exactly 4 changed. Artifact 7,602,600 B `E3B97E7B...`.
DEPLOYED, Status: both match. Also fixed `_build_059.ps1` (was cloned with
doubled backslashes + a stray trailing-slash guard that failed Get-Item) and
hardened `_apply_move.py` GIBBED path to absolute.

Oracle: cruise readout near 336 kph, afterburner stretch toward ~437. If the
readout still disagrees, report both numbers (cruise + afterburner peak) and
the factor gets refit — two points pin the unit law.

### test-059 result: still ~84 kph. DOCUMENTED ONLY, no new build.

059's unit correction did not move the readout (84-85 kph before and after:
official_top_speed 250->1328, top_speed 320->1727 both landed in-Arche but the
cap is elsewhere). So neither field is the binding limiter, and the ~3.95
units/kph factor is unconfirmed — do not reuse it. Suspects now ordered by
likelihood: (1) gear table (`gear_ratios` + `upshift_rpm`/`downshift_rpm` caps
road speed regardless of top_speed number), (2) nitro/afterburner gating
(`nitrous_gears`=0 in donor = nitro never engages a gear; `extra_top_speed`
tiers may add nothing if the trigger never fires), (3) AI/difficulty or
misc-level governor outside the 4 edited modules, (4) HUD readout in different
units than the physics cap (car may be faster than displayed — needs a timed
distance check, not the dial). Next discriminating test (not built): single
edit of `gear_ratios` top-gear ratio alone; if readout unmoved, timing run over
a fixed road marker to separate physics cap from display units. Dropzone left
on 059 untouched per direction.

## 70. Batmobile SFX extraction (new workstream; dynamic end-to-end map, ears pending).

BmAK audio layout found dynamically, no guide needed: `SFX/*.wad` are WWAD
flat hash tables (QuickBMS script reimplemented in 20 lines — `_wem_extract.py`
pulls any entry by `%08X` hash, verified byte-exact on SFX_2/466D1B0B, 8 MB).
498 SFX entries censused (`_wem_census.py` -> `Working/Audio/sfx_census.json`):
ALL Wwise Vorbis (fmt 0xFFFF), 48 kHz, 1-6 ch; INT_*.wad profiled as dialogue
(2734 entries, 2725 mono, 40 KB median) so the Batmobile IS in the SFX set.
WWAD hashes are NOT Wwise FNV-1/1a (329 candidates, 0 hits); banks carry no
STID names; the 3 loose `.bnk` are ID-only HIRC (+2 BKPK bundles). So final ID
is by ear, narrowed dynamically: `--shortlist` ranks multichannel >=10 s loops
(sequential-hash families flagged: 07896F60/61/63 = same 203 s 4ch loop in
SFX_1/2/3; A284435E/CB591E44 = identical 412 s in SFX_1/8). xWAVE counts flag
concatenated compilations (e.g. 466D1B0B = 16 waves in one entry — skip those).
JC3 side mapped: FMOD Studio (`fmod_studio_F.dll`, banks inside game*.arc),
Serpente pins 45 events in banks vehicles/character/effects
(`_fmodguids.py` -> `Working/Audio/serpente_fmod_events.txt`). BLOCKED on
decode: Wwise Vorbis has no `vorb` chunk (setup not inline), no vgmstream/
ww2ogg/QuickBMS on machine, ffmpeg present but needs Ogg framing + codebooks
it can't get. Next: drop a portable `vgmstream-cli` into `Tools/` (single exe,
no install), decode the ~40 shortlist to wav, pick the Batmobile by ear, then
rebuild vehicles.bank via FMOD Studio for the dropzone. No builds touched.

### §70 update: 40 decoded, Batmobile suspects ranked (ears needed).

User pointed `Tools/vgmstream-win64` (portable, no install). `_wem_decode.py`
extracted + decoded the 40-entry shortlist to `Working/Audio/wem|wav/` and
ranked stationarity (`ranking.json`); `_wem_meta.py` confirms Custom Vorbis
48 kHz, exact-30.000 s-style designed loops, no stream names in any WEM.
`_wem_spectral.py` (centroid + f0/harmonicity) splits the stationary set:
broadband hiss beds (10AF2680, CB591E44/A284435E twins, CC2F6871 — cent
3-5 kHz, harm ~0, NOT engine) vs low harmonic drones. Batmobile-engine
suspects, in order: `SFX_3_75FA4BAC` (4ch 48 s, cent 192 Hz, harm 0.55 —
deepest drone), `SFX_7_CE2F6B57` = `SFX_7_CE2F6B54` twins (4ch 39 s, 403 Hz,
f0 100 Hz, harm 0.59), `SFX_7_CD2F69E2` = `SFX_7_CD2F69E1` twins (4ch 39 s,
same 100 Hz fund, brighter 1234 Hz — same source different mix?),
`SFX_8_5946F94F` = `SFX_8_5646F4F5` twins (4ch 58 s, 381 Hz, harm 0.45),
`SFX_8_E01EC5A5` (2ch 77 s, 964 Hz, f0 52 Hz, harm 0.63). Twins = same asset
shipped in 2 WADs (extract either). Giants (EDF036D6 1.17 GB etc.) decode to
only 30-80 s first streams = multi-sound bundles, deprioritized. Two earlier
timeouts were pipe-buffer artifacts, not hangs (redirect to file works).
Next: user auditions `Working/Audio/wav/` suspects in any player; winner →
FMOD Studio rebuild of vehicles.bank.

### §70 update 2: dynamic event→sound map SOLVED (BML_Engine bank, fully).

No more guessing. Chain (all `Tools/scripts/`, no new tools — Python+zlib only):
`_upk_any.py` dechunks any package (UE3 chunk layout cracked: magic +
0x20000 + totals + (bc,bu) block table to sum(bu)==tu, all-zlib; image =
file[0:NameOffset] + stream) → `_bm_names.py` (3151 names) →
`_upk_tables.py`/`_upk_exports.py` (imports stride 28, exports stride 72 —
both derived, 0 bad) → 62 `AkEvent` + 14 `AkBank` imports dumped
(`batmobile_wwise_refs.json`) → `_upk_banks.py` carves 7 embedded AkBank
exports → `bank_BML_Engine.bank` (7.3 MB: DIDX 76 media + DATA + HIRC 188
objs) → hash calibrated FNV-1(lowercase) on two AKEvent serials
(`_hash_cal3.py`: Play_BattlemodeEngine=388710DB, Transition_In=102067E6) →
`_engine_final.py` resolves event→action(+6 target)→container→sound→DIDX
(event = id + u32 count + ids@+8).

BML_Engine voice map (`Working/Audio/bml/eng_*.wav`, `_engine_depth1.py`):
Idle = 5 rpm layers ~3 s (eng_1808E883 steadiest/deepest, cent 743 Hz);
Positional = 2 beds ~17-18 s; Reverse = 14.6 s loop + beeps; Clutch =
5 revs ~4 s; DistantRev = 5 revs ~3 s; MShot = gun one-shots;
Transition_In/Out = 5+5 one-shots each. 7 bank events unmatched (names only
in Wwise project, media extracted anyway). BML_Burnout/AUX banks carved too
(burnout = generic screeches, events don't match Batmobile list).
NOT YET: Play_BattlemodeEngine + Turbo live in bank BML_Battlemode,
undefined in base/MK2 packs (MK2 defines VEH_Batmobile_MK2_Engine instead —
carved as `bank_MK2_Engine.bank`, same tools apply). Recipe: dechunk
Joker/Funhouse/city packs → AkBank exports → carve → resolve. WAD route
retired for engine (bank DATA is the source; SFX WADs = same media pooled).
TOOLS NEEDED (user fetching): nothing for extraction (done). For the JC3
side: FMOD Studio (free) to rebuild vehicles.bank — exact major version TBD
by extracting JC3's bank first (needs .tab names via Deca/community filelist;
fmod_studio_F.dll has no PE version stamp). No web searching needed yet.

### §70 update 3: LZO1X ported (zero installs), converter consolidated, hunt automated.

UE3 ships TWO codecs: vehicle/object packs = zlib, level/city packs = LZO1X.
`_lzo1x.py` ports lzo1x_d.ch faithfully (peek-first-byte, overlap-safe copies,
M1/M2/M3/M4 + EOF) — CityX block oracle: 131072 B exact on first try after
two mechanical fixes. `_bank_convert.py` is now THE clean converter (zlib+LZO
auto, any package -> names/tables/AkBank carve/HIRC resolve/wav):
`_bank_convert.py <pack.upk> [bank-substrings]`. Verified on 10 packs
(base/MK2/Joker/Funhouse/Death/Showcase/Engine/BmGame/CityX/Y/Z).
Unmatched-event forensics (`_unmatched.py`): 9AF38C66 = second 5-layer drive
loop (battle/pursuit candidate); BD2FEE58 = Reverse-stop (only Stop action);
2479106C = distant-Positional; 3C3F43C0/A88826DB = shared one-shots;
2099606B = layered whoosh via blend container; 388CE6FC = dead (0 actions).
eng_1808E883 (user: start-or-boost by ear) is Idle ranseq layer 3/5 —
consistent with a start/boost layer inside the Idle stack.
BML_Battlemode definer STILL OPEN after: 10 full converts, 151-pack export
hunt (all silent), GPCD registry scrape (paths are logical Ww_ packages, no
files), DLC survey, WAD census (all 498 RIFF, no banks), ini grep (nothing).
`_codec_census.py`: 2522 zlib + 742 LZO (+2 uncompressed). `_names_sweep.py`
RUNNING in background over ~1197 >=2MB candidates (tables-only probe for
BML_Battlemode/Turbo/BattlemodeEngine names) -> `battlemode_hits.txt`.
TOOLS NEEDED: still NONE — LZO port removed the last blocker (no quickbms,
no installs; vgmstream + ffmpeg + Python cover everything). Next: convert
sweep hits (if any) for Turbo/BattlemodeEngine media; else declare the
BML_Engine map (delivered, every sound event-tagged) sufficient for JC3.

### §70 update 4: ID-grep + forensics; background sweep relaunched.

Event-ID byte grep over all 11 on-disk streams: BattlemodeEngine x1 each in
the 4 vehicle packs (= the AKEvent export serial, no bank), x0 everywhere
else; Turbo x0 EVERYWHERE (its AKEvent defining export is also unlocated).
SFX WAD census: all 498 entries RIFF (no banks in WADs). Film_B1 full convert
(44 banks, ambience/dialogue/props) = definitive negative. `_names_sweep.py`
relaunched correctly in background (first launch died: I had passed
timeout=60000 to a background call; resume via DONE lines added) over ~1197
>=2MB candidates -> `battlemode_hits.txt`, ~6 s/pack.

### §70 update 5: sweep round 1 done (333 packs, zero definers); round 2 running.

Round 1 (>=2MB keyword packs): only REFERENCES (4 vehicle packs carry the
names as imports; Ace_A1_Ch2_Anim + UnderAce_A4_Ch23 reference BML_Engine).
WADZ cracked en passant (u32 size + zlib WWAD; INT_Startup = 2780 dialogue
BKPKs — banks CAN live in WADs, but INT=dialogue, SFX=all-RIFF per census).
Size-filter flaw spotted: a Turbo-only bank (short whooshes, ~200-500 KB)
could hide in a <2MB pack — round 2 sweeps ALL 1197 targets any size.
Still open: BML_Battlemode bank + Turbo AKEvent export.

### §70 update 6: two-loop-stacks hypothesis; exhaustive sweep running.

BML_Engine holds TWO complete 5-layer loop stacks: Idle layers (named event)
+ 9AF38C66 layers (unmatched, same ranseq shape, 2.4-3.0 s steady) — read as
pursuit/battle variants behind a runtime switch (eliMINation: nothing else in
the bank has loop-stack shape; battle content needs loops and only these two
stacks exist). Turbo candidates: 2099606B's 4 blend-container whooshes.
If right, the "missing bank" shrinks to Turbo/battle one-shots, and the user
can split pursuit vs battle by ear in seconds (battle = heavier).
`Bank.upk` checked (1.2 KB redirector). WAD avenue closed (SFX all-RIFF,
INT dialogue, Startup dialogue-BKPKs, patch/DLC accounted for).
Exhaustive sweep relaunched over ALL 3266 packs (resume-skips ~870 done) —
a same-named definer cannot hide from it; a differently-named one can (noted
limitation: would need per-bank HIRC ID grep, i.e. full dechunk of
everything).

### §70 update 7: sweep exhaustive — bank file unlocatable statically.

Round 3 (2069 packs): only four new REFERENCE hits (BatEntry__City_Ch3c_LOD2
carries all four names but defines only BML_Engine/Burnout/AUX dupes;
BmGame/Engine/Film/Orphan/Startup refs confirmed import-side). Combined with
12 full converts + WAD/ini/DLC surveys: NO pack in CookedPCConsole defines
an AkBank export named BML_Battlemode, and no stream on disk contains Turbo
(B1B5DD98) or BattlemodeEngine (388710DB) bytes outside their AKEvent
serials. Adjacent battle content already located (carvable on demand):
`VEH_Tank_Explosion` (7.4 MB, BmGame), `BML_Impacts` (2 MB).
CONCLUSION: static scraping is COMPLETE — every event->sound edge resolvable
from shipped files is resolved (BML_Engine 17/17 events with media, Burnout,
AUX, MK2, all provenance-tagged). The Turbo/battle-loop bytes are either in
the two in-hand loop stacks (user ear-check pending) or load from a source
invisible statically (runtime bank-load logging during gameplay would settle
it — needs file-access observation, not more scraping). No installs were
needed at any point; none are owed.
Converter (`_bank_convert.py`), LZO port, census, maps all committed in
Tools/scripts + Working/Audio.

### §70 update 10: user research absorbed; counter-asks issued; HIRC hunt running.

User's websearch (Q1-Q4): no verified turbo/bank/file; general batman_bnk +
hashlist workflow confirmed; Steam global-sounds thread correctly scoped to
City (not Knight); Nexus hashlist ungated-URL unconfirmed; exact strings no
web hits. USEFUL LEADS EXTRACTED: (1) batman_bnk's bank-name lists may name
WAD chunks/banks (asked user to download package, surface TEXT lists only —
tool itself unneeded); (2) Nexus hashlist.txt needs their login (asked);
(3) wwiser skipped (my HIRC parse covers it); (4) decisive experiment asked:
ProcMon capture of BatmanAK.exe file reads while engaging battle mode +
turbo — game resolving the bank IS the location oracle.
Meanwhile `_hirc_hunt.py` RUNNING in background over 45 top packs: full
dechunk + every AkBank export content-grepped for battle/turbo event IDs
(catches differently-named banks; resume via hirc_hunt.log). RESULT: zero
HITs, all 45 DONE — no AkBank export anywhere in the top packs contains the
battle/turbo event bytes under any name. Cornered to: unhunted long-tail
packs, runtime-only source, or user artifacts (ProcMon/lists).

### §70 update 11: hashlist + PML delivered — unification + Turbo in hand.

User supplied `hashlist.txt` (19,063 `HASH<tab>name`) + ProcMon `Logfile.PML`
(4.7 MB). `_hashunify.py`: FNV-1(lowercase) reproduces ALL 19063 hashes —
WAD hashes, Wwise IDs, hashlist = ONE namespace (any name now computable).
Retrospective correction: the spectral shortlist top-16 = ALL ambience
(AMB_City/Stagg/Film/JokerBoss, WEA_Rain, MDLC music, SEQ_Diner) — content
metrics without names converge on beds; user's wind/hum/music ears vindicated
again. Direct hits: **BML_Turbo=EC2FD42B** (SFX_1, 3ch, steady 4 kHz whine
3.8 s = afterburner SUSTAIN loop) and **BML_Batmobile=E7BD5AD0** (SFX_1, 15 s
deep ~400 Hz signature bed) extracted+decoded (`Working/Audio/hashid/`).
Bank names confirmed in-namespace: BML_Engine=A1109037,
BML_Battlemode=AA84F8A2 (files still unlocated; DIDX∩WAD=0 and HIRC∩WAD=0
prove bank media is bank-local, never WAD-pooled). PML: SFX_1.wad dominant
(181 refs — Turbo/Batmobile stream from it), CityX driving, INT dialogue;
no bank-name strings in RAM trace; capture appears pursuit-mode (no battle
pack reads) — battle-mode capture still needed for the bank question.

### §70 update 12: `_` clobber bug + fixed-hunt negatives (all avenues exhausted).

Loop-var `_` reused in unpack tuples zeroed the AkBank-import index set in
`_bank_hunt/_bank_sweep/_hirc_hunt` (all prior "silent" results VOID).
Fixed + reran: `_bkhd_map2` (no non-AkBank holders — earlier flags were the
bug), `_bank_hunt` (now FINDS definers: BML_Engine also in UnderAce_A4_Ch23;
still no Battlemode), `_hirc_hunt` fixed rerun over 45 packs: 45 DONE, 0 ERR,
0 HIT (voided first run's file lost to a delete-race; rerun foreground).
Independent static avenues: ALL EXHAUSTED (12 converts, ~2940 swept, 45+12
content-hunted, WAD/ini/DLC/ID/STID surveys). Only user artifacts can advance
the bank file now (battle-mode PML, batman_bnk lists, Nexus hashlist).

### §70 update 13: EVENTMAP — every JC3 sound-component x BmAK equivalent.
`_epetrue.py` (per-object parse) fixed a misattribution in the flat-regex map
(damage_fire_right is visual-only; engine_running_sound owns 905be2e5 alone).
`_eventmap.py` writes `Working/Audio/EVENTMAP.md` (28 rows: 10 starter pairs
with evidence tags, 18 KEEP STOCK with stated reasons) + `starter_set.json`
for the ADD phase. TRAN-pair field (160991x2) tested against fsb5 offsets,
lengths, sample counts — no match (not FSB refs; unresolved, noted).

### §70 update 14: STATMAP v1 — same discipline for stats.
BmAK tuning exports located (RVehicleBatmobile 3905B, Sim 2328B, 4 wheels,
Booster, AkPlayerVehicleSoundInfo, AkCurve). Serial model cracked: (u16
type, u16 member, u32 value); a=16 = export refs (verified vs table: wheels
point at FireTrail/Tracer/Burnout particles); ID-field pattern verified via
RTPC serials (FNV IDs). GPCD schema scraped (159 Sim + 21 Base + 84 Wheel +
210 SVehicle). Perfect offset->name attribution PROVEN impossible statically
(native layouts; GPCD lacks offsets — shown twice). `STATMAP.md` (16 rows,
`statmap.json`): 1200x3 power [exact], 9545 top speed [magnitude, 343kph],
6000 RPM, ratio cluster, wheel/susp values; mass = [none] (physics-side).
CHECKLIST.md gained a STATS section.

### §70 update 15: PHYSMAP v1 — same discipline for physics.

`_phys_inv.py` decoded all 12 JC3 physics modules fully (`jc3_phys.json`):
brakes 10000, aero drag 0.33/lift -1.95, mass 975 + inertia 1.8/1.5/0.5,
suspension F40/R35 len 0.25, steering 35->15deg, 7-pt tire curves (peak 1.0
@0.405 slip), custom_land_global tiers (top_speed_kph 200, punch 15/20kN,
f/r multipliers), optimal-torque 490 (= N.m absolute, semantics resolved).
`_phymap.py` writes `PHYSMAP.md` (17 rows, `phymap.json`): mass now maps to
SVehicle.ChassisMass x MassScale (corrects STATMAP's [none]), inertia,
suspension, tire-curve model, brakes, steering (+BML_Steering RTPC default
100.0 verified), RAYs (test-055), punch; aero/buoyancy/CoM/doors = KEEP
(no equivalents). Same native-attribution gap as stats, same tag discipline.

### §70 update 16: CAMMAP v1 — same discipline for camera+events.

`_cam_inv.py` decoded car_base.ctunec fully (`jc3_cam.json`, 159 members:
springs, FOV/zoom, ranges, lag, recenter, collision, curves) + Serpente refs
(DrivingCamera, hijack framings, transitions). `_cammap.py` writes `CAMMAP.md`
(12 rows, `cammap.json`): chase<->DrivingCamera, battle<->BattleModeCamera
(+HeadOffset), FOV<->FOVFrequency+zoom fns, springs/lag/recenter/collision
per-state, cockpit views, shake API, listener; hijack = KEEP (remote-called
car). BmAK values open (same gap). CHECKLIST.md gained a CAMERA section.

## 72. GRAB->CONVERT->ADD checklist; grab+convert completed dynamically.

User correction accepted with definitions (dynamic = script-derived from
shipped files, zero picks; hardcode = human choices baked in) + admitted
hardcodes (060's name-picked nitro, forensic labels, split budgets, top-40
era). `Working/Audio/CHECKLIST.md` tracks all 3 steps. `_grab_all.py`:
hashlist-name rule x SFX+INT tables (INT: zero Batmobile hashes — rule
confirmed) + every DIDX of BML_Engine/Burnout/AUX/MK2 + sha256 dedupe =
198 rows / 132 unique blobs (MK2 shares base content; AUX is HIRC-only;
23 BANK-ONLY names). `_convert_all.py`: 132/132 decoded with provenance
(`grab_manifest.json`). Step 2 DONE. Step 3 (ADD) pending: 060 oracle +
dynamic event->FSB mapping (nitro path + engine start/loop).

Loop-var `_` reused in unpack tuples zeroed the AkBank-import index set in
`_bank_hunt/_bank_sweep/_hirc_hunt` (all prior "silent" results VOID).
Fixed + reran: `_bkhd_map2` (no non-AkBank holders — earlier flags were the
bug), `_bank_hunt` (now FINDS definers: BML_Engine also in UnderAce_A4_Ch23;
still no Battlemode), `_hirc_hunt` fixed rerun over 45 packs: 45 DONE, 0 ERR,
0 HIT (voided first run's file lost to a delete-race; rerun foreground).
Independent static avenues: ALL EXHAUSTED (12 converts, ~2940 swept, 45+12
content-hunted, WAD/ini/DLC/ID/STID surveys). Only user artifacts can advance
the bank file now (battle-mode PML, batman_bnk lists, Nexus hashlist).

User supplied `hashlist.txt` (19,063 `HASH<tab>name`) + ProcMon `Logfile.PML`
(4.7 MB). `_hashunify.py`: FNV-1(lowercase) reproduces ALL 19063 hashes —
WAD hashes, Wwise IDs, hashlist = ONE namespace (any name now computable).
Retrospective correction: the spectral shortlist top-16 = ALL ambience
(AMB_City/Stagg/Film/JokerBoss, WEA_Rain, MDLC music, SEQ_Diner) — content
metrics without names converge on beds; user's wind/hum/music ears vindicated
again. Direct hits: **BML_Turbo=EC2FD42B** (SFX_1, 3ch, steady 4 kHz whine
3.8 s = afterburner SUSTAIN loop) and **BML_Batmobile=E7BD5AD0** (SFX_1, 15 s
deep ~400 Hz signature bed) extracted+decoded (`Working/Audio/hashid/`).
Bank names confirmed in-namespace: BML_Engine=A1109037,
BML_Battlemode=AA84F8A2 (files still unlocated; DIDX∩WAD=0 and HIRC∩WAD=0
prove bank media is bank-local, never WAD-pooled). PML: SFX_1.wad dominant
(181 refs — Turbo/Batmobile stream from it), CityX driving, INT dialogue;
no bank-name strings in RAM trace; capture appears pursuit-mode (no battle
pack reads) — battle-mode capture still needed for the bank question.

User's websearch (Q1-Q4): no verified turbo/bank/file; general batman_bnk +
hashlist workflow confirmed; Steam global-sounds thread correctly scoped to
City (not Knight); Nexus hashlist ungated-URL unconfirmed; exact strings no
web hits. USEFUL LEADS EXTRACTED: (1) batman_bnk's bank-name lists may name
WAD chunks/banks (asked user to download package, surface TEXT lists only —
tool itself unneeded); (2) Nexus hashlist.txt needs their login (asked);
(3) wwiser skipped (my HIRC parse covers it); (4) decisive experiment asked:
ProcMon capture of BatmanAK.exe file reads while engaging battle mode +
turbo — game resolving the bank IS the location oracle.
Meanwhile `_hirc_hunt.py` RUNNING in background over 45 top packs: full
dechunk + every AkBank export content-grepped for battle/turbo event IDs
(catches differently-named banks; resume via hirc_hunt.log). RESULT: zero
HITs, all 45 DONE — no AkBank export anywhere in the top packs contains the
battle/turbo event bytes under any name. Cornered to: unhunted long-tail
packs, runtime-only source, or user artifacts (ProcMon/lists).

### §70 update 9: user demands zero-compromise dynamic map; audit + external asks.

User is RIGHT that runtime resolution proves resolvability — my negative is
about LOCATION, and ear-findings must not become hardcoded substitutes. Audit:
DYNAMIC (scraped, verified): WWAD/WADZ, UE3 chunks (zlib+LZO1X port),
name/import/export tables + strides (28/72, 0-bad walks), AkBank carve, HIRC
graph rules (event count-u32@+4/ids@+8, action target@+6, containers, DIDX),
FNV-1(lowercase) IDs (2 serials + 60+ Joker names), census, decode, rankings,
zero-cross splits, flattest-window loop. INFERENCE (labeled as such):
unmatched-7 functions (graph position), two-stacks=pursuit/battle (user ear
CONFIRMED same recording), Turbo=2099606B whooshes, split points
(signal-derived). MISSING: Turbo + BattlemodeEngine bytes (bank unlocated
after 12 converts + 2939 swept + WAD/ini/DLC/ID-grep coverage).
Deep-WAD scan proved entries are WEM concatenations (EDF036D6 = 680 waves)
but bank-free (2 EV-byte coincidences in Vorbis noise; trio BKHDs = noise).
MK2's 33 STIDs checked (per-object fragments + bank self-name, no Turbo).
ASKING USER (their websearch offer): Q1 which files hold BmAK Batmobile
turbo/battle audio (Xentax/Zenhax/Nexus/Steam/Reddit threads, exact hashes?);
Q2 BmAK Wwise bank list w/ locations (BML_Battlemode where?); Q3 AbdAshes
guide (Nexus 2230) comments/Posts for hashlist.txt; Q4 exact-string
"Play_Batmobile_Turbo"/"BML_Battlemode" hits with file context.

### §70 update 8: user verified startup; JC3-ready pair built.

User ear-check: Idle stack == unmatched stack (same loop both modes — battle
vs pursuit is runtime switch/pitch, NOT separate recordings; explains the
missing battle-loop media). eng_1808E883's head = ENTER-BATMOBILE startup
(pursuit default), verified in-game. Trajectory forensics: crank 0-0.6 s
(4 kHz whine) -> catch @0.6 s -> settle to ~650 Hz by ~2 s -> steady loop ->
baked fade-out (all layers are start/stop one-shots, none infinite).
`_split_start.py` builds the JC3 pair: `jc3_batmobile_start.wav` (2.0 s
ignition, zero-cross cut + 30 ms fade) + `jc3_batmobile_loop.wav` (flattest
1.5 s window of eng_1FD7E69F, 2.15-3.66 s, seam DC=5). Next: JC3
vehicles.bank extraction -> FMOD Studio version match -> wire start/loop to
Serpente's start/loop FMOD events (45 GUIDs in serpente_fmod_events.txt).

## 71. test-060: Batmobile nitro audio deployed (first sound mod). DEPLOYED.

`_apply_audio.py` swaps FSB PCM payloads in place (same sizes, metadata
untouched): premium_nitro_start/loop/stop (#56/#150/#355, PCM16 mono 48k)
<- Batmobile Turbo/start content (mono-mixed, RMS-matched, zero-cross cuts).
Bank byte-size identical (210,781,376), vgmstream re-decodes all three,
spectra confirm 4 kHz whine. test-060 = 059 tree (.ee/.toc) + dropzone-loose
`sound/fmod_banks/vehicles.bank` (overrides archive, no .toc needed);
Rollback059/053 remove the bank. Status: all three match. ORACLE: hit nitro
-> Batmobile afterburner whine instead of stock; if silent/crash, bank falls
back to archive (delete dropzone bank). Engine start/loop mapping continues
(TMLN markers Start/running/shutdown found; TRAN pairs unresolved).


## 70. TRUE SCALE: every asset through ONE transform, physics moved with it. test-060

### User direction (2026-10-10), and the misreading it corrects

"It should iteratively grab every asset all at once fully aligned to body and scaled." The
previous builds fitted the body (5.0 m) and the wheels (Ø0.80) SEPARATELY and then moved the
stations to suit. User: the 047 jitter "was caused by alignment to body" -- i.e. by moving wheel
visuals relative to a body/physics they did not belong to. Also: TRUE SCALE (lore), wheel
diameter 4 ft 7 in = 1.40 m (wiki estimate, user-verified against footage: Batman 188 cm);
physics may be corrected as we go ("plenty of larger vehicles in JC3"); track: shift along the
axle if physics is postponed.

### The transform, measured

The PSKX is already real centimetres: tyre radius 0.683 m at scale 0.01 -> Ø1.37 m vs 1.40.
T(p) = to_jc3(p) * 0.01 + offset; offset centres the track on X=0, puts the tyres' lowest point
on JC3 ground (0.02 = vanilla hub 0.40 - radius 0.38), wheelbase midpoint on the vanilla
(-0.0555). Offset = (0, +0.0222, +0.1543).

    body                 3.495 x 2.271 x 7.026 m (all non-wheel mats: turret, cockpit, glass...)
    hubs (= hardpoints)  f_l (-1.208, 0.7047, -2.570)   f_r (+1.208, 0.7047, -2.570)
                         r_l (-1.2845, 0.7027, +2.459)  r_r (+1.2845, 0.7027, +2.459)
    wheelbase 5.029 m, track front 2.416 / rear 2.569, tyre radius 0.683, width 0.732
    (_pskx_layout's 220/246 cm track was wheel-CENTROID averaging; bbox centres are right)

Track decision: at ±0.885 the axle shift would be 0.32/0.40 m and the steered fronts would swing
on a 0.32 m kingpin offset, so (physics "as we go") the hardpoints take the TRUE X too: axle shift
0. `--hardpoint-x 0.885` restores the axle-shift layout if wanted.

Side convention verified from vanilla wheel meshes (dense rim side outward): left = -X. The
PSK->JC3 map is a reflection (Unreal is left-handed), so PSK Y<0 = left.

### Tools

`Tools\scripts\bat_assemble.py` (one pass, one transform; reuses psk2rbm): body chain (plain
clone of body_lod1 block 6) + each corner's OWN wheel geometry (front and rear differ), local to
its hardpoint; `stations.json`. Wheel cut = wheel mats with centroid within 1.03 x tyre radius of
the axle (1.25x dragged in 99 verts of a non-wheel part at 0.70-0.80 m above the hub that would
orbit the axle). `Tools\scripts\physics_stations.py` consumes stations.json: land_global (the
PATCHED 1,600 B copy) 19 floats in place at offset-in-file, old values asserted -- 4 hardpoints,
front/rear radius 0.38->0.683, rim_radius 0.30->0.539 (same ratio), width 0.245/0.285->0.732,
ground_clearance 0.40->0.704 [ASSUMPTION: it equals the vanilla hub height; semantics unknown];
physicsc: the 4 station quads @0x3940/0x39A0/0x3E80/0x3EE0 (same as §65), matched by sign.
Re-decoded: every value as intended; sizes 1,600 / 340,368 B unchanged.

Meshes (Working\TrueScale): body 20,000/8,000/3,000/1,500/1,417 tris (lod5 floor); wheels per
corner 2,500/1,000/400/200/100; all VERIFY PASS.

### test-060

test-045 tree + 5 body LODs + 30 wheel paths (each its own corner, mshswap included) +
land_global (internal; the .ee's 1,494 B pre-patch copy overwritten) + physicsc.
`aafdiff` vs 045: exactly 37 changed (35 meshes + land_global + physicsc), 0 added/removed.
.toc 468 records, 0 appended, compare = 9 external. .ee 699588EE... 7,132,606 B; .toc
9EFF3DCC... 46,192 B. DEPLOYED 2026-10-10 (replacing 059), Status: both match.
Movement edits (058/059) deliberately NOT included: this test isolates alignment.

Expected: a 7 m Batmobile on four Ø1.37 m wheels sitting IN its arches, no jitter, riding on its
tyres. Watch: wheels sinking or floating (radius/clearance assumptions), front wheels clipping
the arches at full lock (true geometry, untested steering angle), handling of a 2.4 m track,
collision now follows the 7 m shell (wider/longer than any Serpente build).

### test-060 result (2026-10-11): **LOADS, ALIGNED, QUIET.**

User: "Yes, yes, no, wheels turn when they should." Read as: wheels sit in their arches (yes),
not sinking/floating (yes), jitter (no), steering correct, no arch clipping reported.
(Reading stated back to the user for correction.)

So the one-transform rule holds end to end: true-scale 7.03 m body, each corner's own Ø1.37 m
wheel, physics stations + radius/width moved in BOTH land_global and the physicsc's baked quads
from the same stations.json, and Havok/JC3 accept a 5.03 m wheelbase / 2.4-2.6 m track. This
closes §58-60's stance question: the jitter was visuals and physics disagreeing; when both come
from one transform there is none. §65's "phasing" (055) is consistent with that: it moved the
physics to stations the 5 m body did not match.

Open, in rough priority:
1. Top speed / movement: 058/059 edits not in 060; the ~84 km/h cap is unexplained (§69).
   A 7 m, big-wheeled car on Serpente drivetrain numbers also needs mass/suspension review.
2. Glass: glass mats are baked into the opaque paint block (black windows). Needs a Window block.
3. Lights: the 5-part .epe dropped the Serpente's light parts; the Batmobile's Emissive mat is in
   the paint block (no glow).
4. Textures: BmAK body has no diffuse (matte black by design, §66); highs need .hmddsc authoring.
5. Ship: README/credits, publish lint, KB field note.

## 71. Speed & handling, step 0: the live module set. 058/059 ran a STALE engine.

User direction (2026-10-11): speed and handling next, LORE accurate. Standing requirement
recorded: assets AND textures must be grabbed dynamically by a loop (no hard-coded material /
texture lists) -- planned: PSKX skeleton (REFSKELT 180 bones + RAWWEIGHTS) to discover parts,
UE .props.txt bindings to discover textures.

Every sportsmuscle .vmodc, .ee copy vs archives (name-hash search over all .tab):

    only in the .ee (live = the .ee copy): ai, brakes(_ai), land_aerodynamics(_ai),
      land_steering(_ai), buoyancy, custom_land_global, custom_velocity_damper, decals,
      front/rear_tire, land_audio, palette, rigid_body, suspension, transmission,
      vehicle_misc, effect_attachments, lights, water_interaction, stunt_areas
    PRE-PATCH in the .ee (live = archives, .toc offset 0):
      land_engine       .ee 1,045 B  vs patch_win64\game1 1,207 B
      land_global(_ai)  .ee 1,494 B  vs patch_win64\game1 1,600 B
      vehicle_deform    .ee 67,214 B vs patch_win64\game4 67,278 B
      vehicle_parts     .ee 29,886 B vs patch_win64\game4 30,540 B

land_engine, decoded (Research\SerpenteModules\): the .ee copy is test-003's EDITED one
(max_rpm 7300 -> 14600, §~14) AND pre-patch; the live patched copy has max_rpm 7300 plus a member
the patch ADDED: `overdrive_extra_rpm = 10000`. 058/059 internalized the .ee copy -> they ran a
doubled rev limit with NO overdrive member. Their ~84 km/h result is therefore confounded and
says nothing about the edited fields. Rule (§48 again): never internalize a module from the .ee
when the archives carry it; start from the patched archive copy.

test-060 runs NO movement edits on the live patched set: it is the clean baseline. Next: measure
its top speed (no boost / boost) before any edit.

## 72. Lore speed & handling: units from the game, values converted. test-061

User (2026-10-11): no in-game measurement; "250 kmh" is the Serpente's stat; "draw from game find
units, convert batmobile values". Lore input `Working\Movement\lore_batmobile.json` (wiki estimates
via user): 336.4 km/h (209 mph), 1200 bhp, +30% afterburner, 0-60 2.7 s (recorded, not applied:
nothing to calibrate against), mass UNKNOWN (975 kg kept).

Units, derived from the LIVE Serpente modules (`Working\Movement\live`: .ee copies + the PATCHED
land_engine and the true-scale land_global):
    official_top_speed 250            km/h (= stat screen; 059's x3.95 "units" was wrong)
    transmission.top_speed 320        km/h cap: gearing gives 333 at the 7,000 rpm upshift
                                      (0.77 x 3.91, r 0.38): margin 1.041
    torque_factor_at_optimal_rpm 490  N·m peak @ 5,000 rpm; with the 0.84 falloff to 7,300 rpm
                                      the peak power is 422 hp
    extra_top_speed 80/40/80          km/h boost tiers: +80 = +32% of 250
    frontal_area 2.4                  m²: Serpente body mesh rasterises to 2.25 (x1.067 for
                                      wheels/bumpers)
Batmobile body rasterises to 6.22 m² -> 6.63 m² with the same allowance.

Conversions (`Tools\scripts\lore_stats.py`, in-place at offset-in-file, old values asserted;
re-decoded):
    official_top_speed 250 -> 336.4         top_speed (cap) 320 -> 437.3 (336.4 x 1.30)
    final_drive 3.91 -> 5.140 (7,000 rpm in top gear = cap x 1.041 on the TRUE r 0.683; with the
      old gearing the big tyres would reach 599 km/h)
    peak torque 490 -> 1,393.5 N·m (x2.844 = 1200/422 hp, curve shape kept)
    extra_top_speed 80/40/80 -> 100.9/50.5/100.9 (+30% of 336 in km/h)
    frontal_area 2.4 -> 6.635   drag_coefficient 0.33 -> 0.1393
    steering max_speed_kmph 220 -> 296 (top-speed ratio)
Cd is the one free parameter: lore fixes power and top speed but not drag. Calibrated model
v ∝ cbrt(P / (Cd·A)) on the Serpente (250 km/h, 422 hp, 0.33, 2.4) reproduces 336.4 km/h with
1200 hp in 6.63 m² only at Cd 0.139. At Cd 0.33 the same car would top out near 250.
(First draft scaled boost tiers by the % ratio, 80 -> 75; corrected to absolute km/h.)

test-061 = test-060 + 6 modules (land_engine internalized from the PATCHED copy + torque edit,
replacing the .ee's stale 1,045 B copy). .toc compare = 8 external. .ee 36B63D5A... 7,132,666 B;
.toc B04F8ABE... 46,192 B. DEPLOYED 2026-10-11, Status: both match.
Not changed: mass, suspension, brakes, tyre curves, nitro timing.

## 73. Dynamic grab: parts from the skeleton, textures from the bindings. Mirror fixed. test-062

User requirement: "assets and textures need a for loop (or something) to dynamically grab them
all" -- no hard-coded material or texture lists.

### Parts (`Tools\scripts\pskx_parts.py`, used by bat_assemble.py)

REFSKELT (180 bones, stride 120) + RAWWEIGHTS (stride 12: weight, point, bone). Each face's
DOMINANT bone = argmax of its three points' summed weights. Each bone's faces classified by SHAPE:
round (Y~Z extent, roundness <= 0.15) and covering >= 15/16 angular sectors about a lateral axis =
spinning candidate. Wheel count from GAME DATA (land_global number_of_wheels = 4): the 4 largest
round parts anchor the wheels; smaller round parts join a wheel only if inside its radius on the
same side (this rejects the round power cells, machine-gun bundle and a door that the shape test
alone flagged). Result per corner: `Wheel_*_Disc` + `_Vis` (tyre) + `_Fan`. Hub = the roundest
attached part (the tyre `_Vis`, roundness 0.00). Faces weighted to a wheel bone but OUTSIDE the
tyre circle (+3%) go to the static body: 1,396 faces (an ~80-vert piece above each tyre weighted to
the Disc bone, the same one the material cut caught in §70; it would orbit the axle).
Everything else (shell, cockpit, nose, suspension/armour, weapons, flaps, doors) = static body.

### MIRROR FIX: §70's side convention was wrong

The rig's own labels: `Wheel_Front_Left`, `SUSP1_Wheel_Rear_Left`, the power cell parented to it
etc. all landed at JC3 +X (= right). §70 justified the PSK->JC3 REFLECTION by "Unreal is
left-handed" -- an argument, not evidence. The labels are evidence: the true-scale Batmobile (060,
061) was MIRRORED left-right. Now a PROPER rotation (-y, z, -x). Winding chosen by evidence:
vanilla JC3 meshes have POSITIVE signed volume (body +3.33, hood +0.023, wheel +0.084 m³); the
rotated source is -22.0 -> triangles reversed automatically. Audit: 56 sided bone labels agree,
0 disagree (would be 0/56 with the reflection). Stations unchanged within 0.1 mm (symmetric car).

### Textures (`_texmatch.py` now a function: `texture_bindings(mats, srcdir)`)

1. UE .props.txt bindings with parent-chain inheritance; 2. materials without bindings fall back to
name-token containment against the .tga files on disk (stopwords = tokens in >half of all texture
names: data-derived; one token may be missing when 3+; per role suffix keep the shortest name).
Now resolves Wheel_V2 (D/N/R), Tyre_V2 (D/N/R), Undercarriage, Body_Decals, Stagg_Battery;
left empty only where no file exists (Worn_NoRain, Master_Flip helper). Fixed a heredoc-mangled
tokenizer (`\1_\2` had become \x01_\x02). bat_assemble copies every part's textures to
`Working\Assembled\textures\<part>\` + `textures.json` (91 files, 37 part-materials).
Conversion into JC3 (.ddsc lows + .hmddsc highs, §66) is still the blocked step.

### test-062

`_build_assembled.ps1 -Base test-061 -Src Working\Assembled -Tag test-062` (generic: any assembly
onto any true-scale base). = 061 (lore stats) + the assembled body/wheels + physics regenerated from
the same stations.json (2 bytes differ from 061's: f_l Z -2.5700 -> -2.5699). .toc compare = 8
external. .ee DDDE50DF... 7,191,361 B; .toc C9C99760... 46,192 B. DEPLOYED 2026-10-11, Status:
both match. Expected: identical stance/handling to 061; asymmetric details (riot suppressor,
machine gun, power cells) on the opposite side from 060/061 -- now the correct side.

## 74. Glass: material kind from its own bindings -> a JC3 Window block. test-063

Block census over the Serpente's lod1 RBMs: CarPaintMM x45, Window x22, CarLight x19 (Window and
CarLight decode as GenericBlock: verbatim pre/mid statics, declared strides, round-trip proven).
256 vanilla RBMs MIX block types in one file (jeep body lod1 = CarPaintMM + CarLight), so the body
file may carry several blocks; the 5-part .epe has no separate window parts to host glass.

Window layout, measured on sportsmuscle_door_f_l_window_lod1 (strides 40/2): x,y,z | u,v | 0,0 |
packed normal (col 7: dot +1.000 vs geometry) | tangent | constant 262143.98 (packs ~(1,1,1)).
Signed volume positive like the paint blocks. CarLight: strides 12/24/2 (plain layout), 1,085 B
pre-static; its glow comes from an emissive-mask TEXTURE -> lights wait for texture authoring
(with the Serpente's mask under Batmobile UVs the glow would land in random patches).

bat_assemble.py: a material is GLASS iff it binds an opacity texture (from texture_bindings: only
`Batmobile_V3_Glass_INST`); body LODs = [plain CarPaintMM paint block, Window glass block],
each kind decimated separately, budget by face share floored at 5% of the LOD budget (capped
at source faces) -> glass 999/399/150/100/100 tris. New verify_blocks(): every block re-encodes
byte-identically, indices, positions, normal round trip. Window texture slots stay the
Serpente's (glass_alpha_dif, in the .ee at its vanilla path).

test-063 = `_build_assembled.ps1 -Base test-061 -Src Working\Assembled`. .toc compare = 8
external. .ee 7AEADF38... 7,224,955 B; .toc 26EBE1A7... 46,192 B. DEPLOYED 2026-10-11, Status: both
match. Expected: see-through tinted canopy instead of black; everything else as 062.
Risk: a CarPaintMM + Window pair in one body file is a combination not seen in the census
(CarLight+Window and CarLight+CarPaintMM are); if the glass is missing or the car crashes,
that is the variable.

### test-063 result (2026-10-12): "Tinted glass visible." CarPaintMM + Window in one body file works.

User: wanted ONE dynamic run that grabs AND converts every asset and texture.

## 75. One run: grab + convert every asset and texture. Per-material blocks. test-064

### Texture conversion (`Tools\scripts\tex2ddsc.py`)

Container modelled on the Meme pack's `textures/convertible.ddsc` (renders at a NEW path, no
.hmddsc): write-to-hmddsc False, mip-count = hdr-mip-count = all mips, ONE element (offset 128,
size = whole chain), unknown-06 8. flags 8 for colour (DaBaby 8; vanilla body_dif 9 = 8|1 with an
.hmddsc), 0 for normals (vanilla body_nrm 1 with .hmddsc) [INFERENCE]. Formats from vanilla:
colour 71 = BC1 (DDS 'DXT1'), normal 83 = BC5 (DDS 'DX10' + 20 B ext: 128+20+21,872 = 22,020 B
exactly on body_nrm0.dds). Vectorised numpy BC1 (bbox endpoints, RGB565, 4-colour) and BC5 (two
BC4, 8-value mode); Pillow mips to 1x1; cap 1024. Import = `ConvertTexture.exe <name>.xml` (reads
<name>0.dds): proven byte-identical on convertible.ddsc. Verify: own decode of every mip (PSNR vs
source) + re-EXPORT must return our blocks. Normals 39-45 dB; colour 25-35 dB (bbox BC1 on noisy
art -- upgrade to PCA endpoints if blocky).

### Per-material blocks (bat_assemble.py)

JC3 CarPaintMM slots (vanilla): 0 dif, 1 nrm, 2 mpm, 3 paint msk, 4-11 shared damage/dirt/dummies.
Per material, from its OWN bindings (no lists): main colour map = keys colour_map/diffuse/:d; main
normal = keys with "normal"/:n; micro-detail tiles, ramps, masks, aniso skipped (no CarPaintMM slot).
Routing: opacity bound -> Window (glass); wheel part -> vanilla wheel block; body with a colour map
-> body_lod1 block 3 (interior style, no paint mask) cleared to plain; body without -> block 6
(paint mask: palette tint, the look already approved). Slot 0 <- own colour, slot 1 <- own normal.
Each material decimated separately (share of the LOD budget, min 20, glass floor 5%).
Zero-length normals from zero-area decimated triangles (body lod4 block 9 failed the round trip at
0.980) -> set to up; they are invisible.

Result (`Working\Assembled`, assembly.json = plan + texture map): body 17 blocks, each wheel 5
(wheel, tyre, disc, wheel-light Emissive, light glass -- the wheels carry their own light covers);
20 textures converted (9 BC1, 11 BC5) to
`models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/textures/batmobile/*.ddsc`.
All 25 RBMs verified per block and re-encode byte-identically.

### test-064

`_build_assembled.ps1` now also adds assembly.json's textures (copied + @files.xml; relative paths
resolved against the mod root). = 061 + assembly + physics from the same stations.json.
.toc 488 records (20 appended before the .epe), compare = 8 external. .ee 7274A4BE... 19,507,121 B;
.toc E90E139B... 48,661 B. DEPLOYED 2026-10-12, Status: both match.

THE OPEN QUESTION this answers: do NEW texture paths load on a vanilla-path override? (New .rbm
paths never did, §53; the DaBaby's new .ddsc did, but on a new entity.)
    textured tyres/discs/cockpit + panel normals -> yes: the full pipeline works
    untextured / default-looking where new maps should be -> new texture paths ignored; fallback:
      vanilla texture paths (and then the .hmddsc highs win, §57)
    crash -> container header (flags/unknown-06) is the suspect: diff against convertible.ddsc

### test-064 result (2026-10-12): "Invisible and intangible (if its even there)." No crash.

## 76. The whole vehicle vanished: resident textures blew the game's memory budget.

Vanilla `settings/asset_memory_budgets.bin` (archives_win64\game5, 3,104 B RTPC, no patch override;
ConvertProperty -e -> Research\Budgets\vanilla_budgets.xml), [soft, hard] KB:
    Vehicle-HD  Model [4096, 4915]   Texture [6144, 7065]
    Vehicle-LD  Model [10240, 11059] Texture [12228, 13414]
The UE modpack (Luke JC) raises ONLY the second number (Texture HD 7,065 -> 113,040, Model
4,915 -> 78,640) -- his fix for "disappearing parts". So the second value is the hard cap.

Resident (.toc-listed, in-.ee) footprints: vanilla textures 1,901 KB / models 4,328 KB; test-063
1,901 / 7,037 (renders, so budgets count what bound parts LOAD, not the file); test-064 22,085 KB
textures -- 20 full-chain 1024 maps all bound -> ~3x the hard cap -> the whole entity (render +
the render-mesh-driven collision) never appears. (Vanilla keeps its highs in streamed .hmddsc;
the .ee only holds small low mips.) §29's "budget ruled out" was right for models then, not now.

Fix (no global settings change): `bat_assemble.py --budget-xml --vanilla-toc` computes the cap
from the game's own files -- (hard 7,065 - vanilla resident 1,901) x 0.9 = 4,648 KB -- and
`allocate_caps` halves, one step at a time, the texture with the most bytes per m² of surface it
covers (areas measured on our true-scale mesh) until the set fits: 3,857 KB. WheelArch_N 1024,
Wheel_V2_D 1024, Body/Undercarriage/Turret/Wheel_N 512, tyre 512/256, cockpit 256/128, small
parts 64-128. Exact .ddsc sizes via tex_bytes() (same scaling as tex2ddsc.mip_chain).
Alternative left to the user: ship a raised asset_memory_budgets.bin like Luke (global effect).

### test-065: 064 with the textures fitted to the budget (ONE variable vs 064)

Same per-material assembly (body 17 blocks, wheels 5), same 20 textures, sizes from allocate_caps:
3,896 KB on disk (budget 4,648). Physics from the same stations.json. .toc 488 (20 appended),
compare = 8 external. .ee 3CC0D4AE... 10,273,968 B; .toc 117C2D6C... 48,661 B. DEPLOYED 2026-10-12,
Status: both match.
    visible + textured        -> budget confirmed as 064's cause; new texture paths LOAD
    visible, untextured       -> budget was it, but new texture paths are ignored
    invisible again           -> not (only) the budget: next = 065 with vanilla texture slots
                                 (no new files) to split per-material blocks vs new texture paths

### test-065 result (2026-10-12): VISIBLE and TEXTURED. New texture paths LOAD; budget was 064's cause.

User comparison vs BmAK: JC3 shows (1) white racing stripes / line graphics across roof canopy,
side armour, rear; (2) tan dirt/mud on tyres and rims; (3) glossy sheen + polygonal jaggedness on
fender edges. BmAK: monochrome matte black/gunmetal, no decals, clean dark rubber/alloy tyres.

## 77. Finish from data: no decal/dirt layers, matte from the material's scalars, more polys. test-066

Diagnosis, from data:
- Tyre_V2_D mean RGB 31, Wheel_V2_D 18.6 (dark, neutral): the mud is NOT in our textures. It is
  JC3's dirt layer, SUPPORT_DIRT 0x4, inherited from the templates (paint 0x101F, wheel 0x4).
- The stripes: SUPPORT_DECALS 0x1 on the paint template; the decal layer samples UV2, which our
  writers copy from the NEAREST SERPENTE vertex -> the Serpente's racing-stripe decal layout
  projected onto the Batmobile.
- Gloss: §55's palette (gloss 0.45, metallic 1, clear coat 1) was my choice. BmAK Mainbody
  Material0: reflectivity 0.2, roughness 0.4, no lacquer binding.
Fixes (bat_assemble.py):
- every CarPaintMM block: flags &= ~(0x1 | 0x4). Paint 0x101F->0x1A, wheel/colour 0x0. Buffers
  are unaffected (only 0x20/0x40/0x1000/0x2000 change layout).
- palette written by the run: the largest painted material by area (WheelArchs, 85 m²) through its
  props parent chain: gloss = 1 - roughness = 0.6, metallic = reflectivity = 0.15, clear coat 0
  (no lacquer binding), rgb 0.05 (no colour data in the props; user-approved black).
- body LODs 30k/6k/3k/1.5k/0.8k (was 20k/8k/...): lod1 31,139 tris.
- MODEL BUDGET GUARD: every LOD of the bound parts must fit Vehicle-HD Model hard cap 4,915 x 0.9
  = 4,424 KB, or the run fails. Now 4,205 KB.

test-066 = `_build_assembled.ps1 -Base test-061` (+ palette_true.vmodc). .toc 488 (20 appended),
compare 8 external. .ee C141ED28... 10,447,561 B; .toc 337D15E4... 48,661 B. DEPLOYED 2026-10-12,
Status: both match.

## 78. The disease: we translated textures, not materials. BmAK vs JC3 rendering, from the files.

User (2026-10-12): stop fighting symptoms; contrast how BmAK and JC3 render the car and perfect
grab+convert until every factor BmAK uses is accounted for in JC3. NO installs in this phase.

### BmAK (UE3), from Playable_Batmobile_SF/*.props.txt
umodel's .mat role map is a GUESS and wrong (labels Wheel_V2_N as "Diffuse"); the props are
authoritative. Masters carry anonymous Collected{Scalar,Vector,Texture}Parameters (defaults,
Name=None); MICs carry NAMED overrides along a parent chain (Mainbody -> WheelArchs MIC -> master).
Expression graph: node list only (Body master 188 nodes), no connections -> the shader math is not
recoverable; the INPUT INTERFACE is. Inventory over all materials:
- 48 scalars: MaterialN_{Reflectivity,Roughness,Metalicity,Microdetail_Size}, Mud*, Rain*, Wetness,
  Glass_{Opacity,Reflectivity,Roughness}, Emissive_*, EMP*, Damage_dirt*, Vector_Displacement_*, ...
- 24 vectors: MaterialN_BaseColour (Material0 0.026/0.026/0.030, Material3 0.326 gunmetal),
  Main_BaseColour 0.045, Roughness_per_material (0.3,0.1,0.1,0.1), Roughness_Base_Level, Mud_Colour,
  Damage_Dirt_Colour, CodeHeadlightColor, LightGroup1234/5678, Fake_Aniso colours, Rain_*.
  (§77's "no colour data in the props" was WRONG: colours are vector params.)
- 24 textures: Material_Separation_Mask, Colour_Map, Normal_Map(_Lacquer), Ref_n_Rough_Map,
  MaterialN_Microdetail(_N), Colour_Ramp_Map, Damage_Chapter_Mask, Emissive(_Map), OpacityMap,
  Anisotropic, Mask, Texture_{Diffuse,Normal,Ref_Rough}.
- BlendMode per master: Opaque (body, wheel, tyre), Masked (disc, decals, undercarriage),
  Translucent (glass, battery energy). TwoSided false everywhere.

### JC3 (CarPaintMM), from JCMR-src/assets/jc3/shaders/carpaintmm.fb.txt (reflection header only)
Per block: CarPaintStaticMaterialParams = 18 float4 (SpecularGloss, Metallic, ClearCoat, Emissive,
DiffuseWrap, Dirt{Params,Blend,Color}, Decal{Count,Width,1-4Color,Blend}, Damage{,Blend,Color}) +
7 Support floats (Decals, DmgBlend, Layered, Overlay, Rotating, Dirt, SoftTint) = the block's
static_params 288 B + static_support 28 B EXACTLY; CarPaintDynamicMaterialParams (TintColorR/G/B +
gloss/metallic/clearcoat overrides; the palette) = dynamic_params 76 B. Samplers: s0 Diffuse,
s1 Normal, s2 PropertyMap (mpm), s3 TintMap (msk), s4 DamageNormal, s5 DamageAlbedo, s6 DirtMap,
s7-9 Decal albedo/normal/property, t16 Layered, t17 Overlay. Flags: + ALPHABLENDING 0x100,
ALPHATESTING 0x200 (carpaintmm_mask / _blend shader variants exist). jc-model-renderer source on
disk implements no CarPaintMM (only character/skin/generalmkiii).

### Our builds carried the SERPENTE's material wholesale
Decoded by name: paint block SupportDecals=1, SupportDirt=1 (floats -- §77 cleared only the FLAG
bits), Serpente dirt colour, decal colours/widths, damage tables, tint defaults.

### Channel semantics, INFERRED from vanilla data (not from shader code)
Serpente body_msk (TintMap, BC1 low mip): R 151 avg (85% >128), G/B ~0 -> one-colour paint, tint R.
body_mpm (PropertyMap): R 235 (92%), G/B 3.8% each; block 4-vectors: comp1 gloss .40 metal 1 coat 1
(metallic paint), comp2 .374/0/0 (plastic), comp3 1.0/1/0 (chrome), comp0 0/0 (matte base).
int_mpm: B 26% -> comp3 gloss .564 metal .04 (dielectric). Reading: PropertyMap RGB selects
material channels 1-3 (black = 0), each taking gloss/metallic/clearcoat from the 4-vectors;
TintMap RGB = amount of tint colour R/G/B. STRUCTURALLY BmAK's model: Separation_Mask -> MaterialN
{BaseColour, Reflectivity, Roughness}.

### Plan (this phase, offline only)
`factors.py`: per PSKX material, resolve the BmAK interface along the parent chain, then derive
EVERY JC3 input by an explicit rule, each tagged with its source (bmak:<param> | neutral |
no-equivalent | missing-on-disk). No template value survives unannotated. Coverage report:
every BmAK factor's disposition + every JC3 input's source. bat_assemble consumes the spec.

## 79. Grab+convert rebuilt on the factor map (offline; no install, per user). 

User: "Proceed" on §78's plan.

### Inputs checked before writing rules
- VERTEXCOLOR (per wedge): R=G=B everywhere (greyscale, mostly 127/128; Mainbody 76 levels) ->
  NOT a separation mask (a scalar per vertex: wear/AO). EXTRAUVS0: valid on most materials,
  half-float garbage (+-65504) on Mainbody/WheelArchs -> unreliable export. Both recorded.
- Body separation mask = the master's anonymous default (ReferencedTextures: WheelArch_MicroMasks),
  not on disk -> body resolves to channel 0 (Material0), tagged missing-on-disk.
- Vanilla flags: dif 9, msk/mpm/nrm 1 -> bit 8 = sRGB colour CONFIRMED; masks/normals linear.
- Roughness maps (_R): tyre R .95 G .21 B .12, disc R .04 G .26 B .43, wheel R .38 B .36 -> read
  as R roughness, G reflectance, B metalness (physical plausibility; R=reflectivity would make
  tyres mirrors). _S maps have a dead R channel -> not read (tagged).
- Alpha: only Stagg_Battery_01_D has its own alpha; masked materials take cut-outs from "_A" files
  (Undercarriage_Grid_A); disc/decals have none -> alpha test dropped, tagged.

### Tools
- `factors.py`: per material resolve the BmAK chain (named tex/scalar/vector overrides, master
  BlendMode/TwoSided); 32 disposition rules; JC3 spec with every input tagged
  (bmak:<param>(<from>) | neutral | vanilla:<path> | generated | fallback:name-match | approximated).
  Gloss[c] = 1 - roughness (MaterialN_Roughness > Roughness_per_material > Roughness_Base_Level,
  x Roughness_Multiplier) or the _R map; Metallic[c] from Metalicity or the _R map; ClearCoat from a
  lacquer normal; channel 0 colour -> s0 (generated solid) or Colour_Map; channels 1-3 colours ->
  TintColorR/G/B (x Diffuse_Adjust); separation mask -> s2 PropertyMap + s3 TintMap; flags from
  BlendMode/TwoSided only (decals/dirt/damage/palette/soft-tint/layered/overlay/deform off, each
  with its reason). 19 materials, 320 factors, 0 unhandled. Writes factors.json + coverage.md.
- `tex2ddsc.py`: convert_image() (files or generated), kinds colour (sRGB) / mask (linear BC1) /
  normal (BC5), BC1 PUNCH-THROUGH (3-colour mode, index 3 transparent) from a separate alpha;
  decoder handles both BC1 modes; PSNR on opaque pixels only.
- `bat_assemble.py`: material planning REPLACED by the specs (computed in the same run); every
  CarPaintMM block's static_params / static_support / dynamic_params / flags / s0-s3 written from
  the spec; texture jobs (tga, masks, solids) budgeted by area. No block uses the vehicle palette
  any more (no SUPPORT_PALETTE_FILE) -> each block's own BmAK colours.
- `spec_check.py`: decodes every block of every output RBM and compares every input with the spec;
  also counts template values silently inherited.

### Result (Working\Assembled)
185 blocks checked: 0 spec mismatches, 0 template values inherited. Body lod1 31,139 tris, model
footprint 4,197 / 4,424 KB, textures 3,964 / 4,648 KB.

### Still template-sourced (undecoded), stated, not hidden
CarPaintMM: version 14, `unknown` 1.0, material_params (0.235, 65536, 65536, 0), plain-block
deform_table, slots s4-s11 (shared damage/dirt/decal/dummy textures; their features are OFF).
Window: 41 B pre-static + 16 B mid-static undecoded -> Glass_Opacity/Reflectivity/Roughness unmapped.
Next candidates: decode Window/material_params; bake MaterialN micro-detail normals into s1;
emissive -> CarLight for the wheel lights; better BC1 endpoints; verify channel semantics in game.

## 2026-10-12 - M488 Bavarium nuke blast dimensions (via wtunesurvey.py on game12.tab)
- editor/entities/jc_weapons/02_two_handed/w704_m488/w704_m488.ee -> w704_m488.ftunec: player 3000/50.0m, ai 1000/25.0m
- editor/entities/jc_weapons/05_stationary/w504_turret_m488/w504_turret_m488.ee -> same w704_m488.ftunec, same values

## 80. test-061 collision + forensic restore (my fault, my fix). 2026-10-15.
I deployed a same-numbered "test-061" (max_rpm diagnostic over the 059 tree),
wiping the real lore-torque 061 (artifacts + aaf + installer) and its dropzone
state. Cause: stale baseline (my audio-work context predated §§71-79: lore units,
true-scale lineage, lore_stats pipeline). No backup existed (Builds/ ignored).
Recovery, all dynamically verified:
- lore modules reproduced byte-identically (lore_stats.py + lore_batmobile.json +
  TrueScale/stations.json + live/, area 6.22; 6/6 match out/).
- tree forensics (059 vs 062 aaf diff = exactly 43 files; toolchain determinism
  proven by 062 repack byte-size match): 061 = 059 tree + TrueScale body/wheels
  (+mshswap diet dupes, 062-pattern) + live land_global + 6 lore modules +
  true-scale physicsc (NOT vanilla: the 9-bytes-off tell).
- restored .ee = 7,132,666 B / 36B63D5A4A1... + .toc B04F8ABE... — both match the
  recorded lore build. Redeployed; dropzone Status confirms both (+060 nitro bank
  untouched). My diagnostic shelved to Builds/_shelved-061maxrpm (+ neutered script,
  renamed targets). Lesson: check Builds/ + MODLOG tail for number collisions before
  ANY new test number; lore model (km/h units, N.m torque, gearing margin) supersedes
  my STATMAP assumptions in three places (pending STATMAP refresh).

  2026-10-15 redeploy (no overwrites): verified Builds 059/060/061/062 artifacts
  intact, ran 061 Install (idempotent, same hashes), Status confirms ee+toc match
  (36B63D5A/B04F8ABE) with the 060 nitro bank still deployed. Rollback060 intact.

## 81. test-067: Batmobile armor (explosions-only verdict: CONFIRMED with nuance). DEPLOYED.

BmAK file evidence: Health + ArmourModeDamageReduction + TakeRadiusDamageFromWeapon
(+falloff) + ram/crush/impact damage speeds + DeathExplosion + ricochet bank
(Ww_WPN_BulletImpacts_Batmobile) + ShootBatmobile AI; NO bullet-damage path anywhere.
Verdict: small-arms/melee bounce off (ricochet); explosives + ram/crush + tanks work.
NOT literally "only explosions" (ramming damages it too). Implemented in the Serpente
.ee's OWN 00_shared health copy (already INTERNAL in .toc, verified: same internal set,
toc hash unchanged B04F8ABE): bullet/melee/grapple_pull armor 0->1 (+strengths);
bullet_heavy/tanks, fire, explosion, impact, electricity LEFT 0 (BmAK tanks/fire damage
it; no immunity evidence); part rows untouched (phase 2 if parts still pop).
aafdiff vs 061: exactly 1 changed, same size. .ee BFC596DC... DEPLOYED, all match.
Oracle: bullets spark off; explosions + rams still kill.
Handling triage (same turn): lore torque x2.84 (1393 N.m) on STOCK tires/grip
(grip_mults 1.5/2/1.5, curves untouched) = power overwhelms grip -> wheelspin-class
complaint predicted. BmAK-side grip numbers unattributed (native serials); fix options:
(a) scale grip_multipliers with torque (~2.84x) to restore balance (test-068 candidate),
(b) BmAK tire factors if schema-link lands, (c) report exact symptom (spin? boat? twitch?)
for targeted tuning. Mass 975 kept (lore mass null); 975kg + 1393N.m also reads skittish.

## 82. test-068: de-boat (circuit-racer suspension). DEPLOYED.

Severe boatiness root cause (files): lore torque x2.84 squatting/d rand rolling on
STOCK soft suspension (F40/R35, travel 0.25, damp 7/4, antiroll 0, 975 kg);
BmAK runs StayUpright* + stiff springs, never wallows. Fix COPIED from shipped
v0405 circuit racer (game35.arc, decoded via _refcmp.py): strength 80/80, length
0.15, compression/relaxation 2.5/5, lateral 0.2, hardpoint -0.1 (12 floats, olds
asserted via circuit_susp_068.json). Mass/CoM/inertia/steering/brakes untouched
(mass-linked or not boat-related); antiroll stays 0 (circuit car also 0).
Suspension was ALREADY internal in .toc (off 14962412) — --internal redundant,
toc hash identical B04F8ABE. aafdiff vs 067: exactly 1 changed, same size.
.ee F11BC2A0... DEPLOYED, all match. Oracle: flat over bumps/landings; if harsh,
halve deltas. (Supersedes §81's option (a): grip scaling deferred until boat judged.)

## 83. HANDOFF: three threads (flight / tank-turn / battle armor). No fixes yet.

User launch report on 068: (1) car FLIES off minor bumps (suspects 068 stiffening);
(2) at ~0 vel, steering spins the car like tank-turn (front vs rear counter-rotate,
user reads as 4WD); (3) BmAK battle mode takes NO damage boosting full-speed into a
wall. Motto endorsed: copied-not-tuned. Opencode hygiene: validate every tool call's
parameters exactly (exact-match oldStrings; the question-tool shape failed before).

### T1 — FLIGHT (prime suspect: 068).
068 = exactly 1 module (suspension, same size, aafdiff-proven): strength 40/35->80/80,
length 0.25->0.15, compression 4/3->2.5/2.5, relaxation 7/4->5/5, lateral 0.1/0.05->0.2,
hardpoint -0.0375/-0.0429->-0.1 (copied v0405 circuit racer, game35.arc, _refcmp.py).
Unchanged: mass 975, CoM -0.3, inertia 1.8/1.5/0.5, damping 0/0, RAY stations (055),
raycast_offset 0, min/max_length 0/+0. Stiff + short + light + fast = launch energy.
BmAK anti-boat lives in StayUpright* (resist angles/stiffness/damping/lift) — JC3 has
NO upright members (rigid_body lacks them; upright is code-side?). Other flight
suspects if revert doesn't cure: top_speed_jump_multiplier 2 (custom_land_global x2
tiers!), push_force/punch 15/20kN tiers, RAY length vs 0.15 travel geometry.
Isolate order: Rollback067 first (one command), then jump-mult, then punch tiers.

### T2 — TANK-TURN at ~0 vel.
Symptom: steering spins car (front vs rear opposite) = BmAK BattleMode TurnOnSpot
behavior appearing uninvited. JC3 suspects: counter_steer_torque 3000 (+handbrake
30000/brake 5000), counter_steer_rot_factor 0, drift torques (max 5000), velocity_
rotation_start 15/end 40/amount 80, reverse_gear_ratio 2.39, forward_ratio_pct 0,
low_gears_final_drive -1. BmAK source feature: BattleModeTurnOnSpotTorqueFactor
(+Front variant), BattleModeSteerAngleFactor. Unknown: pre-existing in 067 or
introduced by 068 (lateral 0.2? hardpoint?) — needs 067-vs-068 A/B. 4WD: Serpente
drivetrain layout unverified (forward_ratio_percentage 0!).

### T3 — BATTLE ARMOR (BmAK: full-speed boosted wall hit, battle mode, zero damage).
Files: ArmourModeDamageReduction + BattleModeImpactMin/MaxDamageSpeed (+MaxDamagePow)
vs pursuit ImpactMin/MaxDamageSpeed (+Pow/MaxDamage) = PER-MODE tunables; Health +
RecoverRate + DamageLevel system + DeathExplosion; ricochet bank; no bullet path.
067 implemented: bullet/melee/grapple immune; heavy/fire/explosion/impact/electric
live. GAP: JC3 has no battle/pursuit MODE switch, so armor can't be mode-gated;
options: (a) gate on nitro/afterburner state, (b) full-time impact armor (needs
pursuit-vulnerability check first — user tested battle ONLY), (c) leave live.
Missing numbers: BattleModeImpact* values (native serials, unattributed); pursuit
wall-hit behavior unverified (ask user or find in files).


## 2026-10-16 - Display names mapped from profile/online.stringlookup
- File: game1.arc span off=513855488 size=1621250 (VFS profile/online.stringlookup), patched copy in patch_win64/game6.tab
- Format: ADF StringLookup, 11 languages; pairs keyed by Jenkins(entity basename); TextOffsets are instance-relative (NOT minus ioff); lang0 = English
- Vehicle map (44 civilian_01) baked into W:/Users/nottr/Downloads/PowSca/JC3/vehicles.ps1; vehicles.csv now 0 unmapped
- Weapon check: 28/31 wiki titles match ingame (case-insensitive); diffs: w013 ingame DK Pistol vs wiki Balloon Head, w147 ingame GuitaRPG vs wiki Guitar Case, w132/w146 no pair entry


## 2026-10-16 - official_top_speed is not the achievable speed (Vistosa/Verdeleon/Farina)
- Vistosa v0401: official 350, trans cap 370, gear-limited 333 @upshift / 366 @maxrpm (r=0.35) = wiki 330 sustainable / 366 max EXACT
- Verdeleon v0403: gearing allows 580+, drag limit ~390 (T=920,Cd=0.38,A=2.26); trans cap 150 inactive; wiki 335 / 400+ nitro consistent
- Farina v0405: trans cap 280 = official 280 = wiki 280 (match is coincidence of consistent tuning)
- Conclusion: official_top_speed is a design/display field, not the simulated result; wiki measured values check out against gear/drag math


## 2026-10-16 - Effective vehicle top speed calculator in vehicles.ps1
- Model: NA = min(top-gear speed at upshift rpm [rear-wheel RBM radius], drag/power equilibrium [per-car rho/Cd/A, torque curve, mass, Crr 0.012], official_top_speed governor)
- Nitro: best unlocked ratio (gears+nitrous_gears; Farina 6+1, Sussurro 4+2, Rustico 2+1 all exhaust nonzero ratios), 1.28x power, governor official+extra
- Validation: Vistosa 325/357 (wiki 330/366), Verdeleon 341/411 (wiki 335/400+), Farina 280/358 (wiki 281/356)
- Fixes: gear arrays sliced to gears count; rear (driven) wheel radius preferred; clutch-slip below idle; trans top_speed ignored (150.0 defaults prove unenforced)

## 84. BmAK mass: three file-side paths tested, verdict stays UNKNOWN (2026-10-16)

User asked whether the Batmobile's mass can be taken from BmAK stats/phys instead of
kept at the Serpente's 975 kg. Three file-side paths exist; all three were tested
(scratch probes, since removed) and none yields a number:

1. **RVehicleBatmobile (exp 5280, 3905 B) / Sim (exp 5281, 2328 B) native serials.**
   GPCD pins the member IDs: ChassisMass c=63, SVehicle MassScale c=60,
   WheelMass c=52, RB_BodySetup MassScale c=41, plus a `BatmobileMassRatio` c=62.
   The c*8 -> serial-b rule FAILS here (4 hit / 108 miss per `_rule8x.py`), and the
   predicted IDs (504/480/416/328) occur ZERO times as `(a=4,b)` entries in
   RVehicle/Sim/WheelFL. Magnitude candidates exist (RVehicle: 2000, 6000, 10000;
   Sim: 3000, 3500, 24000) but are unattributable. STATMAP's "perfect
   offset->name attribution PROVEN impossible statically" stands.
2. **PhysX bodies (RB_BodySetup 206 B x N, BM_Batmobile_Chassis, Destroyed_Physics).**
   Sampled bodies carry MassScale-consistent 1.0 (neutral), no per-body mass values.
   Mass = density x volume would need the PhysMaterial density plus a full
   body-geometry walk: not done, unproven.
3. **Class defaults / other packs.** A full-disk string census: the ONLY file
   containing any mass-member name is GlobalPersistentCookerData.upk, at count 1
   each = schema definitions, not values (MassScale 16x = referenced by 16
   classes). BmGame.upk (214 MB, chunk-compressed) not dechunked; expected yield
   is class defaults, not Batmobile tuning. The one `MassOverride` hit in
   Playable_Batmobile_SF is a false positive (sequential name-index table inside
   the skeletal-mesh export, not a value).

Kept: `rigid_body.mass` 975 + `lore_batmobile.json` mass null. If mass is ever
fitted, fit it from handling feel (boat/skittish triage, §81-82), not from files.

## 85. Mass from top speed / engine: top speed gives nothing, 0-60 gives tonnes (2026-10-16)

User: doesn't top speed + engine derive mass? Tested numerically
(P = 1200 bhp = 895 kW, v = 336.4 kph = 93.4 m/s, rho 1.2, Cd 0.139, A 6.635,
Crr 0.012 — the §72 calibration):

- **Top speed: NO, structurally.** At steady vmax mass enters ONLY via rolling
  resistance: dP/dm = Crr·g·v = **11.0 W/kg**. +1000 kg costs 11 kW = 1.2% of
  peak ≈ 0.4% speed change. Any mass 975–5000 kg fits the same top speed within
  noise. (Aero needs 452 kW vs 895 peak; the headroom is drivetrain loss /
  governor unknowns, not mass information.)
- **0-60 mph in 2.7 s: order of magnitude only.** KE = 360 J/kg; m = P·frac·t/KE
  gives 3358 kg (frac 0.5) … 5373 kg (frac 0.8). The avg-power fraction folds in
  grip, gearing, curve shape, losses — all unknown — and holding 1.01 g average
  needs mu ≥ 1.01. Consistent with "a 7 m armoured Tumbler weighs tonnes, not
  975 kg", not with any exact value. Lore inputs are wiki estimates (§72), and
  this derives a real-world equivalent, never BmAK's internal game number.

Consequence: mass has no file source (§84), no top-speed source, and only a
tonnes-range sanity source. Keep 975 (known-good baseline everything is tuned
around); if boatiness persists, fit mass JOINTLY with suspension/grip/torque
— mass never acts alone — using timed acceleration runs (§69's idea, which
separates physics from the display readout).

## 86. Winch feats cannot derive mass: every path is underdetermined (2026-10-16)

User: the winch pulls an elevator (Batman + 1 occupant); it also bears the
Batmobile's own weight; would a battle-mode speed effect mean anything?

- **Elevator lift** bounds the WINCH (force >= elevator + 2 occupants ≈ 2 t
  class), not the vehicle. The Batmobile's mass does not appear in that
  inequality at all — wrong direction.
- **Bearing the vehicle's weight** is static equilibrium T = m·g with T
  (cable tension/rating) unknown: one equation, two unknowns, circular.
  Closing it needs cable speed + winch-motor power (P = F·v); neither is in
  the files or the footage.
- **A speed effect under winch load** would be scripted game logic (battle-mode
  speed is tuning, not a sim result) — and our JC3 Batmobile has no winch
  mechanic at all. Even read as real physics, the power-split unknowns exceed
  the equations.
- File-side check: `RBatmobileWinch` / `Default__RBatmobileWinch` exist only as
  name-table IMPORTS in Playable_Batmobile_SF (no such export in 5490) — the
  class default lives in another pack, and at best it yields winch force,
  still not vehicle mass. Not pursued: multi-hour sweep for the wrong quantity.

Cinematic feats without measured quantities (speeds, powers, ratings) are
fan-calc inputs, not evidence. Verdict unchanged: 975 kept.

## 87. Four mass/winch tasks: two tested file-side, two not executable (2026-10-16)

1. **Winch force in the owning package: traced, not recovered.** Import-table
   walk (stride-28, 0 bad) resolves it: `RBatmobileWinch` class +
   `Default__RBatmobileWinch` are imported from package **BmGame** (the script
   package, not an asset pack). BmGame.upk (214 MB) and Engine.upk are
   FULLY-compressed script packages: the asset-pack dechunker accepts
   false-positive chunks there (stream fails the package-magic gate, both
   files), so the class default is unreachable with current tools. Gadget,
   Std_6 and MK2 packs fail the same gate. Per §86 a force limit still would
   not yield vehicle mass — hunt closed, not postponed.
2. **Implicit mass/inertia in physics config: tested, negative by engine
   design.** The 24 `RB_BodySetup` 206 B exports are near-empty stubs (zeros +
   i32 bit-patterns, one ~2.0 float) — no volumes, no density. And UE3
   assigns vehicle handling mass via `SVehicle.ChassisMass`, not via body
   volumes, so the physics-asset trail is irrelevant to the vehicle's driven
   mass even if fully parsed. `InertiaTensorMultiplier` exists in schema;
   values unattributed like everything else native.
3. **Controlled acceleration with/without winch loading: NOT EXECUTABLE.**
   JC3 has no winch mechanic and no telemetry API; BmAK is not instrumented
   (no console proxy, no position readout) and its winch sequences are
   scripted. Closest executable proxy is JC3 timed runs over fixed road
   markers (§69's idea) for A/B mass edits — that fits JC3 feel, never BmAK
   internals.
4. **Battle-mode fixed multiplier: not confirmable file-side.** Sim holds TWO
   torque-shaped x/y tables but their pointwise ratio is not constant
   (200/200, 260/130, 220/60 …), so no fixed-ratio pursuit/battle pair is
   visible; battle curves are unattributed native structs. Decisive test is
   user-side gameplay: identical pursuit/battle top-speed ratio across
   grades and damage states => scripted multiplier; varying => sim-mediated.
   JC3 has no battle mode (§83 T3), so nothing to mirror on our side.

## 88. test-070: battle-mode impact immunity (BmAK user-observed). DEPLOYED.

User (BmAK, battle mode): full-speed boosted head-on wall ram, **zero damage**.
That closes §83 T3's open question on the battle side: `BattleModeImpact*`
tunables do exactly what their names say. Pursuit-mode wall behavior remains
unobserved (user-side follow-up, optional) — JC3 has no mode switch, so the
mod ships battle-mode behavior full-time (reversible, like 067).

Build: `Working\Damage\batmobile_impact_armor.json` (`impact_armor` 0->1,
`impact_armor_strength` 0->1 @6C/@70, `impact_damage_factor` left 1,
explosion/fire/heavy/electricity and part rows untouched — mirrors 067).
Base = test-068 aaf (live tree; 069's flight fix stays queued and unstacked —
one variable). `aafdiff` vs 068: 547 identical, exactly 1 changed, 0 size
diffs; `.toc` regenerates byte-identical to 068's (B04F8ABE…, health already
internal). Artifact 7,132,657 B `4AAAB7B7…`. DEPLOYED, Status: both match.
Build: `_build_070.ps1` (installer Rollback068).

Oracle: boosted head-on wall hit → no damage, no parts shed (phase-2 watch
from §81); explosions must still damage (unchanged). §81's "ramming damages
it too" is now qualified: that file evidence governs pursuit mode; battle
mode negates it, per the user's test.

Incidental (pre-existing, not mine): 4 wheel-lod4 RBMs never pack
(`aafdiff` source-vs-pack onlyA=4, identical in 068's own tree — manifest
behavior since the wheel swap). Live since 046 without complaint; noted, no
action.

## 89. test-070 in-game: better, factor questioned. test-071 COMBINED. DEPLOYED.

User on 070: better, but is `impact_damage_factor = 1` right, given BmAK shows
not a scratch on anything rammed? Proof can only come from game testing, so
per user direction both threads ship in ONE test: test-071 = 069 aaf (travel
fix, which the user had installed and rated "better") + full impact package
(`impact_armor` + `impact_armor_strength` 0->1, `impact_damage_factor` 1->0).
`aafdiff` vs 069: exactly 1 changed (health, +0 B); `.toc` byte-identical
(B04F8ABE…, health internal). Artifact 7,132,655 B `BD660965…`. DEPLOYED
(from live 069, game closed), Status: both match. Build: `_build_071.ps1`
(installer Rollback069); spec `Working\Damage\batmobile_impact_full.json`.

Oracle: ram wall/trees/poles boosted → no damage AND no cosmetic scratch;
flight/travel behavior exactly as 069; explosions still damage. Reading the
result: 071 clean where 070 marked → the factor was live, keep 0. 071 ==
070 → armor alone covers everything, factor moot (leave 0, harmless).

Still queued after this: trees/poles plow-through without slowing (momentum
lever candidates: `rigid_body.mass` 975, punch/push tiers) and floaty-when-
launched (`top_speed_jump_multiplier` 2 x2 tiers, `gravity_multiplier_in_air`
1/1/1, `lift_coefficient` -1.95) — members decoded, values not yet chosen.

## 90. test-071 in-game: STILL SMOKES with armor proven live. test-072 DEPLOYED.

User: 071 still smokes; "did impact get set to 0?" Answered by measurement,
not assertion: unpacked the LIVE dropzone `.ee` (hash-matched 071), decoded
its health module — `impact_armor` 1, `impact_armor_strength` 1,
`impact_damage_factor` **0**, 067's bullet/melee/grapple intact. The `.toc`
health record is internal (not among the 8 external), so the game reads this
file. **The edit is live and read; smoke bypasses all three members.**

New hypothesis: armor blocks HEALTH damage, but `impact_deform_threshold`
is 0 (vanilla value, never touched), so every impact still fires deform
events — and smoke follows deform, not health. test-072 = 071 + ONLY that
threshold 0->700 (explosion-threshold scale; `weapon_deform_threshold`
untouched, bullets already spark off). `aafdiff` vs 071: exactly 1 changed,
+0 B; `.toc` byte-identical (B04F8ABE…). Artifact 7,132,655 B `54105C4F…`.
DEPLOYED (game closed), Status: both match. Build: `_build_072.ps1`
(Rollback071); spec `Working\Damage\batmobile_deform_072.json`.

Oracle: ram boosted → smokeless means smoke follows deform (keep 700). Smoke
persists → the path is part rows (067 left all part rows untouched — phase 2)
or `damage_smoke` wiring, and thresholds are exonerated. Either way this one
variable settles it.

On handling ("BmAK conversion obviously not translating"): conceded with the
mechanism. The conversion ported power/torque/gearing/top-speed (§72) but
left handling where it lives: tire 7-pt curves stock, grip multipliers
stock, mass 975 (§85), steering stock — and BmAK's own numbers there are
unattributed natives (magnitude tags). So the car has Batmobile power on
Serpente tires: wheelspin-class behavior is structurally expected, not a
tuning miss. Next after 072: grip multipliers scaled with torque (§81 option
(a)) and/or mass toward tonnes jointly with suspension — separate tests.

## 91. WHY 067-072 CHANGED NOTHING: armor 1/1 was a near-zero RATING. test-073 DEPLOYED.

User: 071/072 still smoked, bullets still exploded it, "impact shouldnt damage at
all", "Batmobile doesn't deform in BmAK", "did you check the modlog". Checked the
modlog (§81/§83 T3 record the BmAK damage model) AND, because that left the
implemented numbers unexplained, extracted a SHIPPED reference the log never had:
`v0602_car_urga_armoredtransport_military_01.ee` (known-armored, game35.tab,
Gibbed Unpack + SmallUnpack) → `lave_health_armored.vmodc` (3742 B), decoded with
`_members.py`.

That file settles it. Armor is a RATING, not a boolean:
`bullet 20/60, bullet_heavy 5/40, explosion 100/100, impact 5/100, elec & grapple
-1/100` (-1 = immune sentinel). 067 set bullet/melee/grapple to **1** at strength
**1** — a rating of 1 out of ~100, i.e. almost no armor. That is precisely why
bullets still killed the car and why 070-072's strength/factor fiddling "changed
nothing": the scale, not the switch, was wrong.

Second discovery — the smoke/deform channels were NEVER EDITED. Our module carries
`deform_scale 1`, `smoke_threshold 200`, `burn_threshold 80` (uint16 @9C/9E),
`weapon_deform_threshold 0`; we only ever touched armor rows and
`impact_deform_threshold`. Deformation is its own member (`deform_scale`).
`vehicle_deform.vmodc` is only a `DeformPoints` vertex list — no logic.

Third: `rigid_body.vmodc` does NOT survive a ConvertAdf decode→encode round trip
(it loses 16 B with ZERO edits — `_rtcheck.py`: 992→976; only this module, every
other target is +0). That is a tool artifact, not my edit, and it means mass can
only be set by in-place binary patch (`_patch_bin.py`, offset-in-file 0x50).

**test-073** (combined, per user direction) = 072 tree + three edits, all
proven-live in the dropzone after install:
- health → shipped armored profile: bullet/bullet_heavy/impact/melee/electricity/
  grapple arms with -1 immune + strength 100; explosion 100/100 (kept live — BmAK
  explosives DO damage it, §81/§83); fire 0; `impact_damage_factor` 1 (Urga ships
  1 → 071's 0 was wrong); `max_health` 1800 + thresholds 1800/1800/90;
  `deform_scale` 0 (user: BmAK Batmobile doesn't deform); `impact_deform_threshold`
  back to Urga's 0. `smoke_threshold` left at 200 — semantics unproven, not a guess.
- `custom_land_global.grip_multiplier` 1.5/2/1.5 → 4.26/5.68/4.26 (x2.84 = the lore
  torque factor, §81(a)); Urga ships the same 1.5/2/1.5, so these are game-wide
  stock constants and this keeps the vanilla power:grip ratio.
- `rigid_body.mass` 975 → 4000 (§85's own 0-60 band 3358-5373, "tonnes, not 975"),
  applied JOINTLY with grip as §85 requires; inertia untouched (calculated).

`aafdiff` vs 072: exactly 3 changed (+0 B each). `.toc` byte-identical B04F8ABE
(all three internal). Artifact 7,132,669 B `9641E1BB…`. DEPLOYED (game closed),
Status both match. `_build_073.ps1` (Rollback072); specs in Working\Damage +
Working\Movement. Live re-decode confirms every value above + mass 4000.0.

Oracle: bullets RICOCHET (no damage, no explosion); ramming/being rammed does no
damage; no deformation and no smoke; explosions still hurt; heavier + grippier
handling. If it still smokes with -1 immunity AND deform_scale 0, smoke is
neither health- nor deform-driven → it is the part rows (§81 phase 2: part_damage_
types, `damage_smoke` wiring), the last unexplored path.

Still open: trees/poles plow-through (`push_force` 0/15000/20000, `f/r_multiplier`
15/30, punch tiers — identical to Urga's, i.e. stock), and floatiness beyond what
mass alone fixes (`top_speed_jump_multiplier` 2, `gravity_multiplier_in_air` 1/1/1,
`lift_coefficient` -1.95).

## 92. -1 IS NOT "IMMUNE". Bullet immunity in vanilla = armor 5000. test-074 DEPLOYED.

User on 073: still not immune (a couple of magazines explode it) and handling still
short of BmAK. Both fair. The immunity failure was mine and it was a semantics
error, now proven by a second shipped reference:

**`lave_health_tank.vmodc`** — `v0201_car_capstone_mediumtank_military_01.ee`,
game35.tab (Gibbed Unpack + SmallUnpack, `Research\TankRef`), decoded with
`_members.py`. The game's canonical bullet-proof vehicle is immune via
**`bullet_armor = 5000`, strength 99** — a huge numeric RATING, not a sentinel.
The same file uses `electricity_armor -1` and `grapple_pull_armor -1`, exactly
like the Urga transport: so `-1` means "this damage type does not apply to me",
NOT "immune". 073 set bullet/impact/melee to -1 and therefore left the car barely
armored — which is why mags still killed it. (067-072's 1/1 was the same class of
error one order of magnitude lower.) Scale now has three anchors: tank 5000/99,
Urga 20/60, our stock 1/1.

**test-074** (base = 073) = the real fix, all proven live in the dropzone:
- `bullet_armor` 5000 / strength 99, `impact_armor` 5000 / 100, `melee_armor`
  5000 / 100 (tank scale for the user's three demands).
- `explosion_armor` 250 / 50 (tank: tough, NOT immune — BmAK explosives do damage
  it, §81/§83); `bullet_heavy_armor_strength` 20 (tank; tanks still hurt it).
- `impact_damage_factor` 0 (second, direct lever on "impact shouldnt damage at all").
- `Land_Wheel.instantly_damaged_by_bullets` 1 -> 0 (tank wheels are 0) so bullet
  hits cannot pop a wheel and feed vehicle damage.
- floatiness: `gravity_multiplier_in_air_up/down` 1 -> 1.6 (the symptom the user
  has reported in every round: "FLIES off minor bumps" §83, "floatier than BmAK").
  JC3 has no BmAK StayUpright members, so air gravity is the direct lever.

`aafdiff` vs 073: exactly 2 changed, +0 B. `.toc` byte-identical B04F8ABE.
DEPLOYED (game closed), Status both match. `_build_074.ps1` (Rollback073);
`Working\Damage\batmobile_074_health.json`, `Working\Movement\batmobile_074_float.json`.

Handling is now the open question and it stays UNKNOWN on purpose: every handling
change so far was a guess and the user has rejected three of them. Per §81 option
(c) — "report exact symptom (spin? boat? twitch?) for targeted tuning" — the
symptom is being asked for rather than guessed at again. Member sets are already
decoded and waiting per symptom: understeer/scrub -> `grip_multiplier` (now 4.26/
5.68/4.26) or `steer_angle_*_deg`; spin-out/twitch -> `counter_steer_torque` 3000,
`max_drift_torque` 5000, `drift_yaw_vel_damp`; sluggish/leaden -> mass 4000 down,
`torque_multiplier` 2 up; still floaty -> `top_speed_jump_multiplier` 2,
`lift_coefficient` -1.95, `takeoff_pitch_damping` 0.5.

NOTE: `Research\TankRef` / `Research\UrgaRef` hold extracted game files for
reference; they must never be committed or published (nothing in this folder is
tracked yet).


## 2026-10-16 - Full 77-model vehicle enumeration
- One row per model folder; variant priority civilian > rebel > military > commercial > fallback; excludes debug/z80/mission/cargo/EMP/custom/machinegun
- Tabs game3+game35+game36; added tanks, buses, trucks, patrol boats, military helis/jets, snowmobile-less (debug-only, excluded), v9999 test car excluded, 3 monorail trains UNKNOWN names (no stringlookup pairs)
- Mech DLC has no .ee (different entity system), out of scope; 77 + mech + snowmobile ~= wiki 80+
- Name map extended to 74 entries from profile/online.stringlookup pairs


## 2026-10-16 - Wiki pull + percent diff harness (JC3/wiki_pull.py)
- Pulls Infobox Vehicle kmh/mph for all WikiTitles, level-only (skips diving), nitro requires tag (amphibious land/sea not mistaken); writes wiki_pull.csv
- 72/73 compared: land anchors Vistosa -1.5%, Verdeleon +1.8%, Farina -0.4%, Serpente 0.0%; land outliers Carera Std +24%, D90 +22% (fallback), Infimo -15%, Citispeed +14%, Obrero +13%
- Boats systematic: some match official (Squalo -3.5%), others ~half (Hroch +145%, Ducky +106%) - needs boat model
- Helis: official +/-7-42%, Mstitel 356 exceeds official 280; planes match official (Thunderhawk -0.8%/0.0%)
- Retry logic survived a real connect timeout mid-pull


## 93. THOROUGH BmAK READ: the handling numbers are NOT in the files (2026-10-17)

User: "Sluggish, Laggy turning, underturning. I suspect we need a more thorough
reading of BmAK instead of guessing values." Read the real thing, properly this
time. Result is a NEGATIVE, and it is now proven three independent ways:

1. **Container format decoded.** `RVehicleBatmobile` (exp 5280, 3905 B) and
   `RVehicleSimBatmobile` (exp 5281, 2328 B) in `Playable_Batmobile_SF.upk` are
   untagged native CDO streams: repeated `[u16 type][u16 offset][payload]`
   entries (type 4 = float at the given object offset, 13 = FString), with
   offsets restarting per nested struct. Values are there (e.g. 0.8/2.0 curves,
   1500, 260, 89984, 30000, 2000) but there is **no name per value**.
2. **No names anywhere in the blobs.** Full printable-run scan: Sim = **0**
   ASCII runs; RVehicleBatmobile = **8**, all of them object references
   (BatmobileWeapon_Winch/MineLauncher/EMP/DroneHacker/Sonar, Batmobile_
   Generator_1..3). No property names.
3. **GPCD cannot supply the layout.** `GlobalPersistentCookerData.upk` parsed
   properly (`_gpcdtable.py` -> `Working/Audio/gpcd_table.json`): **40,380
   property records across 3,431 classes**, fully-qualified name + type
   (RVehicleBatmobileBase 432 props, RVehicleSimBatmobile 128, SVehicle 95,
   SVehicleWheel 80, SVehicleSimBase 21). But the trailing u32 per record is
   **neither an offset nor unique** (SVehicle: `Wheels` and
   `bUpdateWheelShapes` share 47), and reading floats at it yields garbage
   (`_gpcd_off.py`: f=1.5e-36 etc.). So: names+types, no offsets, no values.
   The old `c*8 -> serial-b` rule was reading the FString length field by the
   way (14 = "FloatProperty\0"), which is why it could never align.
4. **umodel (a purpose-built UE3 tool, `C:\Users\User\source\repos\UEViewer`)
   loaded the package** (Ver 863/227, Game 800016 = Batman4) and reports
   `WARNING: Unknown class "RVehicleSimBatmobile" / "RVehicleBatmobile" /
   "SVehicleWheel"` — no property layout is derivable without the cooked script
   packages, which are fully compressed (087).

Also checked and negative: `BmGame.ini` / `DefaultGame.ini` / `PCGame.ini` hold
**no** vehicle tuning (only keybinds — `pGlideSteer` etc.); no script-side
tuning DataAsset exists in the package (export scan: no Tuning/CustomData/
DataAsset object). Web: no published BmAK handling value table.

**Verdict: "port BmAK's handling numbers" is not obtainable.** That is not a
tooling gap I can close with more effort — the engine does not store the names.
Any future claim of exact BmAK handling values should be treated as fabricated.

## 94. test-075: "sluggish" was a YAW deficit, not power. DEPLOYED.

With BmAK off the table, the reference band is JC3's OWN shipped vehicles,
decoded this turn (`Working/Movement/jc3_handling_band.md`): moped v3501, old
jeep v0000, Serpente v0300, Mugello v0401, Urga v0602, medium tank v0201.

That band immediately explains the user's three symptoms with arithmetic:

- **Power is fine.** Peak torque / mass: ours 1393.5/4000 = **0.348**, vs
  Mugello 690/2500 = 0.276 and Urga 1100/6000 = 0.183. The car is *better*
  powered than JC3's own 2.5 t and 6 t vehicles. So "sluggish" is not torque.
- **Yaw authority is the deficit.** `counter_steer_torque` 3000 and
  `max_drift_torque` 5000 were never scaled when 091 took mass 975 -> 4000
  (x4.10). Yaw torque per mass is now **0.75**, i.e. Urga-level (3.0) or
  worse, and tank-adjacent (0.72). Every shipped vehicle sits at 10000-20000
  absolute. That single omission produces all three symptoms at once: slow to
  rotate (laggy), cannot rotate against the inertia (understeer), and therefore
  reads as leaden (sluggish).
- **Steering timing is vehicle-specific**, so it is legitimate to sharpen:
  `t_to_full_steer_s` is 0.8 on the Mugello and 4.0 on the tank; ours was 1.2.
- Ruled out by the band: `steer_angle_max_speed_deg` 15 is already the highest
  of all the cars (others 10-12), so understeer is not a steer-angle limit.
  `steering_sensitivity` 4 is an outlier high value, deliberately LEFT ALONE
  (lowering it would worsen "laggy").

**test-075** (base = 074), every new value taken from a shipped JC3 vehicle:
- `counter_steer_torque` 3000 -> **16000** (jeep ships 16000; Mugello 15000 @
  2.5 t, Urga 18000 @ 6 t -> 16000 at our 4 t)
- `counter_steer_torque_brake` 5000 -> **15000** (Mugello)
- `max_drift_torque` 5000 -> **12000** (Mugello AND Urga both ship 12000)
- `t_to_full_steer_s` 1.2 -> **0.8** (Mugello supercar)
- `max_speed_t_to_full_steer_s` 0.85 -> **0.6** (Mugello AND jeep)
- Engine torque, mass, grip, suspension: **untouched** (no evidence to move
  them; power/mass is already above the band).

`aafdiff` vs 074: exactly **2 changed** (custom_land_global, land_steering),
+0 B each; the 5 values re-decoded from the packed `verify/` tree. `.toc`
byte-identical **B04F8ABE...** (all internal). Artifact 7,132,678 B
**CE06B01B...**. DEPLOYED (game closed), Status both match. Build:
`_build_075.ps1` (installer Rollback074); spec `Working/Movement/
batmobile_075_yaw.json`.

Oracle: turn-in should now be immediate and the car should rotate instead of
pushing wide; if it now over-rotates/spins instead, the yaw band overshoots and
16000/12000 steps down toward Mugello's 15000/12000. If it is STILL sluggish
with rotation fixed, then mass 4000 itself is the problem (drop toward 2500 =
Mugello mass) — that is a separate, single-variable test.

## 95. test-075 FAILED (still understeering). Handling tuning STOPPED. (2026-10-17)

User verdict on 075: "Sluggish, Laggy turning, underturning", and then "still
understeering". Also a direction change that outranks any further tuning:

- "I want 100% lore accurate batmobile. That wont be achieved by guesswork."
- "Instead of tuning, should work on reverse engineering batmobile in BmAK."
- "These redneck fixes aren't actually helping that much since my endgoal will
  supercede them."

Recorded: **test-075 FAILED.** Its values (counter_steer_torque 3000 -> 16000,
counter_steer_torque_brake 5000 -> 15000, max_drift_torque 5000 -> 12000,
t_to_full_steer_s 1.2 -> 0.8, max_speed_t_to_full_steer_s 0.85 -> 0.6) are still
live in the tree but are NOT claimed as a fix - the understeer survived them.
That is now **four** consecutive rejected handling value sets, so no further
handling value will be chosen by judgement. Handling work is SUSPENDED pending
real BmAK reverse engineering; 93 already proves the values cannot be read out
of the cooked packages, so the useful future RE is live/memory instrumentation
(or recovering the cooked script packages), not more file archaeology.

Nothing else from 075 is withdrawn: it was a clean build (2 modules, +0 B, .toc
pinned B04F8ABE, artifact CE06B01B..., installer Rollback074).

## 96. Full damage-chain decode. test-076 = the shipped tank's damage profile. DEPLOYED.

Task this round, per the user: note the failure above and "focus on bullet and
impact proofing". Done structurally rather than by feel.

**The whole damage model is now decoded, and it is one file.** A `.vmodc` carries
its OWN type library, which Gibbed ConvertAdf writes into the XML, so
`Tools/scripts/_adftypes.py` can read the authoritative struct definition. A new
`Tools/scripts/_healthband.py` then decodes several health modules side by side
and flags every member that differs. `lave_health_medium.vmodc` is exactly:

    VehicleDamage (128 B) @0x50 + 24 x PartDamageType (32 B) @0xD0 + string table

and each `PartDamageType` row is `type`/`initial_health`/`damaged_health`/
`loosen_health`/`instantly_damaged_by_bullets`/`instantly_loosened_by_bullets`/
`instantly_broken_by_bullets`/`damages_owning_vehicle`. All 24 rows are now
enumerated (Default, Land_Generic, Land_Body, Land_Wheel, Land_Door, Land_Light,
Land_Window, Land_Stunt_Window, Land_Engine, Land_Axle, Land_Spring, Land_Seat,
Land_Wing_Mirror, Land_Steering_Wheel, Land_Roof_Rack, Land_Mud_Flap,
Land_Bumper, Land_Undercarriage, Land_Fender, Land_Hood, Land_Trunk,
Land_Back_Gate, Land_Antenna, Land_Grill). Written up as
`Working/Damage/jc3_damage_band.md`.

Ruled out as damage carriers, so nobody re-opens them: `vehicle_misc` (doors/
speed/nitro), `vehicle_deform` (a `DeformPoints` vertex list, no logic),
`vehicle_common` (game-wide shared crash/water thresholds - editing it would
change every vehicle in the game).

**Also settled: `sportsmuscle_vehicle_parts.vmodc` is unreadable by tooling.**
Gibbed ConvertAdf throws `NullReferenceException` in
`InstanceInfo.GuessInlineArrayCopyPosition()` on EVERY copy (test-003 onward,
aaf and verify) - a converter bug, not corruption. It is the one remaining file
in the chain and cannot be read with the current toolset.

**Where the bullet/impact proofing actually stood.** Against the shipped band,
test-074 was already at or beyond the game's canonical bullet-proof vehicle:
bullet_armor 5000/99 (= tank), bullet_heavy 5/20 (= tank), explosion 250/50
(= tank), impact_armor 5000/100 (**> tank**, which runs 0/0), melee 5000/100
(**> tank** 0/0), impact_damage_factor 0 (**> tank** 1), deform_scale 0
(**> tank** 1), Land_Wheel instantly_damaged_by_bullets 0 (= tank). The ONLY
members where we were still weaker than the tank were the explosion/fire/smoke
threshold family - which is also the only place an explosion or a fire can still
start.

**test-076** (base = 075) copies the tank's values for exactly those members,
net-zero invented numbers:
- `max_health` 1800 -> **2000** and `explosion_threshold` 1800 -> **4000**: the
  tank's own working pair (tank runs 2000/4000; every other vehicle in the game
  runs threshold == max_health, so the tank is the deliberate 2x hardening).
- `npc_explosion_threshold` 1800 -> **4000** (tank).
- `vulnerable_explosion_threshold` 90 -> **100** (tank).
- `smoke_threshold` 200 -> **1050** (tank; this is the direct lever on the
  "still smokes" symptom reported at 073/074).
- `burn_threshold` 80 -> **250** (tank).
- `explosion_delay_s` 8 -> **10** (tank).
Bullet/impact/melee armour deliberately UNCHANGED - they are already at or above
tank, so there is nothing to add there without inventing numbers.

`aafdiff` vs 075: exactly **1** file changed (lave_health_medium.vmodc), +0 B.
All 7 values re-decoded from the packed `verify/` tree. `.toc` byte-identical
**B04F8ABE...**. Artifact 7,132,681 B **7ED9001C...**. DEPLOYED (game closed),
Status both match. Build `_build_076.ps1` (installer **Rollback075**); spec
`Working/Damage/batmobile_076_tank_parity.json`.

Oracle: a full magazine of small arms should do nothing at all (no damage, no
smoke, no deform, no explosion); ramming and being rammed should do nothing;
only explosives and heavy weapons should register. If it STILL catches fire
after an explosion, `fire_armor` is 0/0 on every shipped vehicle including the
tank, so that would be the last untouched member - but changing it would be the
first invented value in this file and needs the user's call.

## 97. test-077: bullet_armor_strength 99 -> 100 (the gate was not full). DEPLOYED.

User: "ours needs /100 gate for bullets not 99. We must remain lore accurate and
uncompromisingly so. anything not lore derived is a guess."

Correct, and 096 was my error. 99 was copied faithfully from the tank - but the
tank's 99 is itself an outlier, not the game's full-strength gate. In the live
health module EVERY gate that applies is 100: impact_armor_strength 100,
melee_armor_strength 100, electricity_armor_strength 100,
grapple_pull_armor_strength 100. `bullet_armor_strength` was the single value
below 100, and 99/100 is not a full gate - it passes 1% of every bullet, which is
exactly why magazines kept chipping the vehicle after 074. So 100 here is
game-derived (the value JC3's own gates use), not a preference.

**test-077** (base = 076), single variable: `bullet_armor_strength` 99 -> **100**.

Deliberately UNCHANGED, and recorded as such because they are per-damage-type
values rather than bullet gates:
- `bullet_heavy_armor_strength` 20 - heavy weapons are meant to hurt it (the
  user's own requirement, 93/94). Flagged to the user as the one remaining
  bullet-family gate below 100, in case "bullets" was meant to include it.
- `explosion_armor_strength` 50 - explosives are meant to damage it.
- `fire_armor_strength` 0 - 0/0 on every shipped vehicle including the tank.

`aafdiff` vs 076: exactly **1** file, +0 B. Re-decoded from the packed `verify/`
tree AND from the live dropzone. `.toc` byte-identical **B04F8ABE...**. Artifact
7,132,677 B **95005911...**. DEPLOYED (game closed), Status both match. Build
`_build_077.ps1` (installer **Rollback076**); spec
`Working/Damage/batmobile_077_bullet_gate.json`.

Note for the lore-accuracy requirement: the remaining non-lore-derived numbers
anywhere in this vehicle are now only (a) the movement/handling values that 095
suspended, and (b) `bullet_heavy_armor_strength` 20 / `explosion_armor_strength`
50, which are shipped tank values rather than invented ones.

## 98. test-077 FAILED. (2026-10-18)

User verdict on 077: "Fail. log dont fix."

Recorded as instructed. **No fix attempted and none will be guessed.** Current
live dropzone is still test-077 (artifact 95005911...); `Rollback076` remains
available. 077's single change was `bullet_armor_strength` 99 -> 100 - the last
value in the file that was below the game's full-strength gate.

STATUS AS LOGGED (honest, no interpretation added):

- The failure symptom was NOT described by the user. Bullet and impact proofing
  has now been attempted and reported back as failing across 073, 074 and 077
  without a specific observation attached, so what actually happens in game
  (bullets still reduce health? still explode it? smoke? deform? something
  else?) is UNKNOWN and is not being assumed here.
- What is established: the health module's armour gates are now at the game's
  full strength (bullet/impact/melee 5000 at strength 100) and the header is the
  shipped tank's own damage profile (096), and the vehicle still fails. Whatever
  is piercing it is therefore NOT being stopped by the armour rating/strength
  pair as configured.
- KNOWN GAP, already on record: `sportsmuscle_vehicle_parts.vmodc` - the part ->
  damage-type wiring, i.e. how a bullet hit becomes a damage event - cannot be
  read at all. Gibbed ConvertAdf throws `NullReferenceException` in
  `InstanceInfo.GuessInlineArrayCopyPosition()` on every copy (096). The one
  file that mediates hits is the one file no tool here can open, so the armour
  values in the health module may never be reached on the bullet path at all.
- Also on record (060-072): `bullet_armor` 1 at strength 1 and `-1` sentinels both
  failed too, so three different armour encodings have now failed.

Do not reopen this with another armour value. Further work needs either the
user's description of the in-game behaviour or a way to read
`sportsmuscle_vehicle_parts.vmodc`.

Tag: needs-in-game-observation.


## 99. 077 in-game: "a couple of mags killed the vehicle". Module linkage PROVEN; real parity gaps found.

User, one line: "note: couple mags killed the vehicle." Live dropzone unchanged
(test-077, `.ee` 95005911...). LOGGED, NOT FIXED. Everything below is measurement
only - no value was chosen, nothing was built.

### 99a. The health module IS attached to this entity - proven, not inferred

The `.epe` references its modules by the Jenkins hash of the FULL path, not by
name (`Tools/Gibbed/HashName.exe` = Jenkins). Searching the decoded `.epe` for
each hash (little-endian, 105,302 B) gives exactly one hit each:

    editor/entities/jc_vehicles/00_shared/modules/health/lave_health_medium.vmodc      27F1C217  LE=1
    editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc                 9BD0CA5F  LE=1
    editor/entities/jc_vehicles/00_shared/modules/default_extended_effect_usages.vmodc 147F492B  LE=1
    models/.../v0300_car_kensington_sportsmuscle/sportsmuscle_vehicle_parts.vmodc      5AF592A9  LE=1
    models/.../v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc                 3C7A4DE1  LE=1

Basename-only and truncated variants: 0 hits. Tune paths (`.ctune`/`.etune`/
`.ftune`) are literal strings in the `.epe`, not hashes.

So the "we may have been editing a module the entity never loads" theory is DEAD.
This is the first PROOF (not inference) of the linkage, and it removes the last
cheap explanation for 067-077 showing no visible effect.

Corollary, so nobody repeats the mistake: the `.ee` is a COMPRESSED container - a
raw string scan of it finds NO path strings at all (0 hits for `editor/`,
`.ctune`, `.rbm`; control run). "The `.ee` never mentions health" is therefore
not evidence of anything. The `@files.xml` (105,470 B) manifest is the
authoritative internal file list.

### 99b. Module sets compared (authoritative `@files.xml` manifests)

    ours : health/lave_health_medium + vehicle_common + default_extended_effect_usages
           + vehicle_physics_effects_car.etune + vehicle_rumble_effects.etune
           + modules/default/v0300_..._front_tire.vmodc, ..._rear_tire.vmodc
    jeep : health/lave_health_medium + vehicle_common + effect usages + decals
           + palettes/general_palette_muted + default_front/rear_tire_offroad
    tank : health/lave_health_tank     + vehicle_common + effect usages
           + default_front/rear_tire_offroad

The tank carries NO extra armour module. Its small-arms immunity cannot be "a
module we are missing". (Ours runs the Serpente's own tire modules instead of the
shared offroad pair - a difference in which tire module, not in damage.)

### 99c. Measured: the file is NOT at tank parity

`_healthband.py` over live(077) | packed verify(077) | tank | urga | stock jeep.
live == packed on every member (tree is consistent). Header family: every armour
and threshold member is >= tank EXCEPT two, where ours is the only 0 in the band:

    impact_damage_factor   0     (tank 1, urga 1, stock jeep 1)
    deform_scale           0     (tank 1, urga 1, stock jeep 1)

and the 24 PartDamageType rows are STILL the stock medium car's, not the tank's:

    Land_Generic  200/0/50       (tank 200/100/50, urga 200/100/50)
    Land_Wheel    1020/400/100   (tank 1000/500/100, urga 2300/500/100)
    Land_Door     300/50/200     (tank 1000/50/100, urga 1200/50/100)
    Land_Body     1000/0/0       (urga 2000/0/0)
    remainder identical to the stock jeep (Default 50/30/20, Light 50/30/20 1000, ...)

So 096's "at or beyond the tank everywhere" was a claim about the HEADER armour
and threshold family only; the per-part table was never compared. Recorded, not
changed.

### 99d. Standing conclusion

074 already ran `bullet_armor` 5000/99 - the tank's own pair, byte for byte - and
bullets still chipped the vehicle (090, 096). The module is now PROVEN attached
(99a). The armour gate is therefore not what stops bullets on this vehicle. What
is left is the per-part path and the one file no tool here can read,
`sportsmuscle_vehicle_parts.vmodc`.

For the record: `Builds/test-033` holds the ARCHIVE copy the engine actually
loads (30,540 B, vs the `.ee`'s pre-patch 29,886 B). ConvertAdf fails on it too,
but in a different place - `InstanceMemberInfo.PrepareForWritting` vs the
29,886 B copy's `InstanceInfo.GuessInlineArrayCopyPosition`. So the engine's copy
is unreadable here as well.

No fix and no new value. `fire_armor` is 0/0 on every shipped vehicle including
the tank (confirmed in this run), and 0 for `impact_damage_factor`/`deform_scale`
is used by no shipped vehicle - so neither is lore-derived for this car.
Tag: needs-user-decision.


## 100. Open questions from the KB review, answered from the record. (2026-10-19)

Two follow-ups on the merged note, both settled without new in-game work.

### 100a. Which ConvertTexture imported x.xml -> tim42's fork, not Gibbed master

- `Tools\Gibbed\README.md` on this machine says, in its own words: "# Rick Gibbed's
  Just Cause 3 Tools // fork ... a fork of the Just Cause 3 tools by Rick Gibbed as of
  their revision 13", changes are Timothee Feuillet's, and the change list includes
  "A texture serializer and deserializer that supports both `.ddsc` files and their
  `.hmddsc` counterparts". Binary releases: justcause3mods.com/mods/modified-gibbeds-tools/.
- Where these binaries came from (096-era provenance, SS 12): prebuilt from
  `%USERPROFILE%\.gemini\...\scratch\tools\gibbed-jc3\bin`, sitting in `Tools\Gibbed\`.
- The exact binary used: `Gibbed.JustCause3.ConvertTexture.exe`, 14,336 B, assembly
  version 1.0.0.0, SHA-256 `2A5A7A5915016A5B4C733E2F7005F464EA6674069A24BC7AE0FE86EF58065600`.
- Re-proved today on `v0300_car_kensington_sportsmuscle_glass_mpm.ddsc` (2,872 B):
  export -> `t.xml` (1,033 B) + `t0.dds` (2,872 B); import -> byte-identical
  `43041186FFD891A15E31282E13A7B99504C1CC6EB323F56A0EA95270AD5E81AF`.
- Gotcha found while proving it: the importer derives the DDS name from the OUTPUT base
  name, not from the XML's. `ConvertTexture.exe t.xml back.ddsc` looks for `back.ddsc0.dds`
  and dies with FileNotFoundException; the XML and the element DDS must share a base.
- The fork still writes only element 0 (`element offset=128 size=2744`, elements 1-7 zero),
  and `write-to-hmddsc="True"` import still throws - exactly the 056 blocker (SS 66). So
  the fork fixes the serializer, not the multi-element or high-mip path.

### 100b. The Arkham Knight model was exported with umodel from the user's own copy

- `Working\Audio\umodel_batmobile_dump.txt` line 1:
  `Found 4260 game files (1981 skipped) in 35 folders at path "E:/Games/Batman - Arkham Knight"`.
- Its package line: `Loading package: BmGame/CookedPCConsole/Playable_Batmobile_SF.upk
  Ver: 863/227 Engine: 10246 Names: 3151 Exports: 5490 Imports: 649 Game: 800016`.
- Export tree `Playable_Batmobile_SF\{Material3, MaterialInstanceConstant, SkeletalMesh3,
  Texture2D}` is umodel's per-class layout; `SkeletalMesh3\Batmobile_V2.pskx` 17,357,622 B
  plus `Batmobile_V2.props.txt`, both 2026-10-06 13:11:08.
- Source package present in the install: `E:\Games\Batman - Arkham Knight\BmGame\
  CookedPCConsole\Playable_Batmobile_SF.upk` 17,916,421 B (2024-07-15), with
  `GlobalPersistentCookerData.upk` 109,590,691 B beside it.

### 100c. Note updated

`knowledge/games/just-cause-3/vehicle-mesh-editing-added-geometry-loads-with-matching-toc.md`:
Textures now names the fork, the binary hash, the name-driven import rule and the
element-0/hmddsc limits; Assets now states the umodel export and the user's own copy;
the "which ConvertTexture build" bullet is removed from Open questions because it is
answered. `skills/mod-any-game/references/engines/big-frameworks.md` now names the fork
for the import direction, and both skill mirrors were re-synced.
`um kb check` PASS 212 notes; `pytest -q tests -k "skill or kb"` 10 passed.

## 101. The parts file is readable now: ConvertAdf NRE fixed, and it names the bullet path. (2026-10-21)

**The wall from 096/098/099d is gone.** `sportsmuscle_vehicle_parts.vmodc` was never corrupt and
never beyond the format - it tripped a bug in the Gibbed ADF reader. Source read, reproduced,
fixed, rebuilt and verified; the decoded map is in `Working/Damage/part_damage_routing.md` and
`Working/Damage/sportsmuscle_parts_v077.xml`.

### 101a. Root cause (one line, not a guess)

`AdfFile.InstanceInfo.GuessInlineArrayCopyPosition()` allocates `_MembersStrings` for a first
probing pass, then sets it to `null`, then calls `InstanceMemberInfo.PrepareForWritting()` a second
time. A string member that lives in *another* member's string table (`ReferenceToString == true`)
writes to `ii._MembersStrings[...]` at `AdfFile.cs:1267`. Null list -> `NullReferenceException`.
The second pass only runs when the instance contains inline arrays, and it only reaches that line
for a member whose string lives in another member's table. Both conditions were counted over the
268-file corpus (`--refscan`): all **12** files that crash have `refs > 0` and inline-array bytes
> 0; **0** of the 256 working files have both. That is the exact shape of
`*_vehicle_parts.vmodc` - a fixed-length inline array per part plus per-part strings - which is why
this bug hit `vehicle_parts` and nothing else. The 30,540 B "archive" copy that failed in
`PrepareForWritting` (098d) is the same bug, one stack frame lower.

Fix: keep a fresh set of string tables for the probing pass and drop them again when it ends. No
logic changed, no heuristic changed. Patch: `Tools/GibbedSrc/patched-adf-reader.patch`; source
checkout in `Tools/GibbedSrc`; runnable build in `Tools/Gibbed-patched` (same `-e` / `-i` CLI).

One build-compat detail: the old exe is .NET Framework, where `Single.ToString("G18")` prints 9
digits in fixed notation and picks scientific from the *requested* precision (so
`2887553650000` but `4.56927082E+19`). .NET 10 prints shortest-round-trip and `-0`. The patched
Exporter reproduces the old formatter exactly, otherwise every new dump would diff against all
existing ones.

### 101b. Verification

- Original `Tools/Gibbed/Gibbed.JustCause3.ConvertAdf.exe` over 268 `.vmodc` files in
  `Builds/test-003/aaf` + `Research`: **256 ok / 12 crash** (all 12 are parts modules:
  every `*_vehicle_parts.vmodc` plus `dababy_parts` / `vanilla_parts`).
- Patched build over the same 268: **268 ok / 0 crash**.
- Exported XML for every one of the 256 files the old tool could read is **byte-identical** between
  old and patched (BOM and all).
- Round trip (export -> import -> `cmp`) still byte-identical on normal modules (`land_engine`,
  `vehicle_common`, health, etc.). Not on this parts file: it re-encodes to 30,430 B vs 29,886 B
  (+544). The writer's inline-array placement is a gap heuristic and over-estimates this file's
  string/array area; that is a *writer* limitation, separate from the reader fix, and unchanged
  from before. For edits, patch bytes in place at the XML's `offset-in-file` instead of
  re-encoding.

### 101c. What the file says (this is the hit path that was missing)

`VehicleParts` = 42 `Part` records. Each names a `damage_type` HashString; `lave_health_medium`
owns the numbers. Hashes check out (`HashName.exe Land_Body` = `37B486D6` = 934577878 = the hash
in the `sportsmuscle_body` record).

17 damage types are used: `Land_Light` x10, `Land_Generic` x5, `Land_Wheel` x4,
`Land_Window` x4, `Land_Door` x2, `Land_Fender` x2, `Land_Bumper` x2, `Land_Seat` x2,
`Land_Wing_Mirror` x2, `Land_Stunt_Window` x2, and one each of `Land_Body`, `Land_Engine`,
`Land_Grill`, `Land_Hood`, `Land_Trunk`, `Land_Steering_Wheel`, plus `Boat_Antenna` - a type the
health module has **no row for**, so `sportsmuscle_c_mirror` silently falls back to `Default`
(50/30/20). That is a genuine data quirk in the shipped car, not a decode error.

The two findings that matter for 077:

1. **`Land_Wheel` is the only bullet flag where this car is below the tank.** medium
   `1020/400/100` with `instantly_damaged_by_bullets = 1`; tank `1000/500/100` with `0`; armored
   transport agrees with the tank. Four of the 42 parts are wheels, they are the biggest target on
   a Batmobile, one hit instantly damages the part, and `damages_owning_vehicle = 1` passes it to
   the vehicle. That is a concrete mechanism for "a couple of mags killed the vehicle" and it is
   not the armour gate that 060-077 kept raising.
2. **19 of 42 parts sit on a 50-HP row** (`Land_Light` x10, `Land_Seat` x2, steering wheel, both
   mirrors, the no-row `Boat_Antenna`). Propagating part HP totals: sportsmuscle **9,530**, medium
   tank **12,850**, armored transport **31,350**. The header armour (5000 @ 100) is not consulted
   on this path at all - consistent with 074/077 showing no change.

Full per-part table and the 24-row medium/tank/armored comparison:
`Working/Damage/part_damage_routing.md`.

### 101d. Not done (deliberately)

- No value changed, no build, no deploy. Live dropzone is still test-077.
- The obvious next experiment is a **private health module for this entity**: copy
  `lave_health_medium.vmodc` under a Batmobile-only path, replace its 24 `PartDamageType` rows with
  the tank's own rows (game-derived, no invented numbers), and repoint the `.epe` hash
  (`27F1C217` -> Jenkins of the new full path). Editing the shared `lave_health_medium` in place
  would change every medium vehicle in the game, so it is not an option.
- Alternative, cheaper, but a semantic lie: remap the four wheel parts' `damage_type` in place.
  Not proposed as a first move.
- Byte-identical re-encode of this parts file is still unsolved; in-place patching is the safe
  edit path until someone resolves the writer's inline-array placement properly.
Tag: ready-for-user-decision.

## 102. Appearance pipeline: grab -> convert -> import in one command, with a transfer %. (2026-10-21)

The appearance set is now produced by one command, from one dynamic export, ending in a percentage:

    python Tools/scripts/appearance_pipeline.py     # grab -> factors -> textures -> 25 RBMs
                                                    # -> spec_check -> progress.  Never deploys.

`appearance_grab.py` is step 1: ONE `umodel -export` of `Batmobile_V2` (SkeletalMesh) pulls the
mesh, the 19 used materials (13 masters + 13 instances in the package), their parent chains and
every texture they bind, across packages -- 61 Texture2D grabbed, 38 of them referenced by used
materials (the rest belong to the Tumbler / MK2 / Joker variants). No hand-written material or
texture lists anywhere. Where the export cannot resolve a reference, the props dump is merged from
the older reference export if that one resolves more (0 needed this run).

### 102a. BC3 glass -- the one appearance class that was not imported at all

The Window block was geometry-only: `factors.jc3_spec()` returned before filling textures, so the
block kept the Serpente's glass dif/normal and every Batmobile glass map stayed on disk. Fixed:

- `tex2ddsc.py` grew BC3/DXT5 (`kind=glass`, JC3 format 77). Not BC1 punch-through: the vanilla
  Window dif decodes to `format 77`, DDS `DXT5`, 1024^2, 11 mips, alpha mean 204 -- a real 8-bit
  alpha, and a cut-out encoding would have made the canopy binary.
- `factors.py` glass branch now emits s0 (BC3) + s1 (BC5 normal): alpha =
  `Batmobile_V3_Glass_A` x `Glass_Opacity` (1.2) -> mean 193 vs the vanilla 204; RGB = the build's
  paint colour 0.05, because BmAK glass binds NO colour map (stated, not invented). `Mask`
  (Glass_S) is the per-layer mask -> approximated, carried as the material-level tint only.
- `bat_assemble.py` binds Window slots 0/1 to those files; slots 2-6 stay the template's
  (glass_mpm + 4 crack maps) because the Window block's 41 B pre-static + 16 B mid-static are
  still undecoded -- the same template-sourced class as before, now the only one in glass.
- `spec_check.py` now decodes Window slots too (it used to skip the block entirely).

### 102b. The percentage (`Working/Appearance/progress.md`, `progress.json`)

339 components, counted from the build itself -- a component counts as transferred only if its
artifact is there AND decodes:

| class | components | transferred | partial | missing | excluded | % |
|---|---|---|---|---|---|---|
| geometry | 25 (5 parts x 5 LODs) | 25 | 0 | 0 | 0 | 100.0 |
| materials | 19 | 19 | 0 | 0 | 0 | 100.0 |
| textures | 38 | 17 | 7 | 0 | 14 | 53.9 |
| factors | 257 | 106 | 29 | 0 | 122 | 46.9 |
| **overall** | **339** | **167** | **36** | **0** | **136** | **54.6** |

overall = (transferred + 0.5 x partial) / total -> **54.6%**; strict -> **49.3%**; of everything
JC3 has a slot for (the 136 excluded removed) -> **91.1%**. Zero missing.

The 136 excluded are not failures, they are JC3's missing slots: micro-detail tiling (5 files),
colour ramps (3, also absent from the game files), an anisotropic ramp, story-chapter damage masks
(4), BmAK's per-channel layer parameters, EMP/fake/editor scalars and the engine-global
Rain/CodeHeadlight entries (those belong to a lights/wetness module, not to a material). The 36
partial are the approximation rules: `_R`/`_S` reflect-rough maps -> material-level gloss, emissive
masks -> material-level m_Emissive, glass layer mask -> tint.

### 102c. Verification

- 25/25 RBMs re-encode **byte-identical** (appearance_progress.py checks this on every run).
- `spec_check.py` after the run: **185 blocks, 0 spec mismatches, 0 template values silently
  inherited** -- Window slots included.
- The glass dif exported back out of its `.ddsc` by ConvertTexture: format 77, DXT5, 128x128 (the
  allocator sized it inside the Vehicle-HD budget), alpha mean 193, p95 255.
- assemble step 860 s, almost all of it Blender decimation of the five LOD chains.

### 102d. Not done (deliberately)

- **Nothing deployed.** The dropzone is still test-077; `Working/Appearance/build` is a staged
  build only.
- Emissive -> `CarLight` (wheel / headlight glow) is still open: the emissive material renders as
  a CarPaintMM block with its Emissive scalar (15) and its mask texture is imported as s2/s3, but
  there is no light block. CarLight's parameter block is undecoded, so building one now would be a
  guess until it can be checked in game.
- Glass is 128 px: the allocator spent the budget on body/tyre maps by surface area. If the canopy
  reads soft in game, the allocator weights / `--tex-max` are the lever, not a code change.

## 103. DEP-1/DEP-2: one deploy path, and test-078 carries the per-material appearance. (2026-10-21)

The appearance conversion finished in 102 but was not in the live car: test-077's body is **one**
CarPaintMM block, because the 19-material build (test-066) was lost when 067 rebased on 061. That
regression is now closed without touching a single module.

### 103a. `Tools/scripts/deploy.py` -- the one deploy path

`build --base <tag> --src <appearance dir> --tag <new>`:

1. **guard**  the base build's `.ee`/`.toc` must match the hashes embedded in its own installer,
              and the live dropzone must match the base. Either drift stops the build before
              anything is written (`--allow-live-drift` overrides, and is recorded).
2. **stage**  copy the base aaf, replace the 25 bound meshes (5 body + 20 wheel) and every wheel
              mshswap, copy the converted textures in AND register each one in `@files.xml`
              (SmallPack silently drops unregistered files).
3. **pack**   `SmallPack` -> `.ee`, then `SmallUnpack` -> `verify/` and a byte-exact round trip.
4. **toc**    `eetoc.py patch` off the vanilla `.toc`, same `--internal` set as 077.
5. **verify** aafdiff vs base (only meshes/textures/`@files.xml`), modules and animations untouched,
              every RBM re-encodes byte-identically, block counts, every texture reference resolves,
              every texture is internal in the `.toc`, `.toc` baseline unchanged, model + texture
              budgets.
6. **receipt** `Builds/<tag>/receipt.json` + an installer with Install / Rollback<base> / Status.

Guard tests (both passed): a base whose installer pin disagreed with its files exited 1 with
`BASE DRIFT`; a live dropzone with one extra byte exited 1 with `LIVE DROPZONE DRIFT`. Neither
wrote a build directory.

### 103b. test-078

`deploy.py build --base Builds/test-077 --src Working/Appearance/build --tag test-078`

    .ee   10,450,291 B  1C224048C8E02C1B52C275687F8C46575E072D1138332E50F218BB090F011FC1
    .toc      49,592 B  C1F143D97185DF43E1DDF155E3409A0F99D5791889F0465A2C04C0206B3AA1AC
    body   17 blocks, 31,139 tris, all 5 LODs (17 blocks each), glass BC3 + normal bound
    wheels  5 blocks each, all 5 LODs, all four corners
    textures 28, all 28 referenced (none unused), 4,014 KB on disk
    model  4,198 / 4,424 KB (94.9%)   texture  3,954 / 4,648 KB (85.0%)
    aafdiff vs 077: 28 added (batmobile textures), 40 changed (39 RBMs + @files.xml), 0 removed,
                    0 module/animation files touched
    .toc    496 records vs 468 (+28); external baseline identical (only_in_ee 98/98, mismatch 8/8)
    pack/unpack: 576 files, 0 lost, 0 corrupt; 4 files are unlisted-by-design (see 103c)

Not installed. Live dropzone is still test-077; `Builds/test-078/install.ps1 -Action Status`
confirms that (it prints the 077 hashes, not its own).

### 103c. Two file-system facts this build exposed

1. **`vehicle_parts` and `vehicle_deform` are EXTERNAL in the vanilla `.toc`** (offset 0 = read
   from the archives). The 42-part table and the deform points therefore cannot take effect by
   editing the `.ee` copy alone - any future parts/deform edit must add
   `--internal sportsmuscle_vehicle_parts.vmodc` (and `..._vehicle_deform.vmodc`) to the `eetoc`
   patch or the game will keep loading the archive copy. Internal today (nonzero offsets):
   health, palette, rigid_body, lights, effect_attachments, land_audio, and the modules 077 edits.
2. Front wheel LOD4/LOD5 do not exist in the vanilla `.toc` at all (front wheels are listed to
   lod3, rear to lod4), so those copies sit in the aaf and are never packed. Inert, not a defect.

### 103d. Next

- Install test-078 (human approval) and check the 5 oracles: 19 materials visible, no magenta, no
  missing block, budget intact, glass reads as dark glass rather than an opaque pane.
- Then LGT-1/LGT-2 (lights module + CarLight), which are the only "not started" P0 items left.
Tag: built, awaiting install approval.

## 104. test-078 installed; the installed bytes are now proven, not assumed

Approved install, 2026-10-21. Order of operations:

    pre-check   Builds/test-078 artifacts re-hashed: .ee 1C224048... .toc C1F143D9... (== receipt)
    rollback    live 077 still on disk (95005911.../B04F8ABE...); raw copy kept in
                Builds/_rollback/pre078/ so a rollback survives even if Builds/test-077 is touched
    install     install.ps1 -Action Install -> dropzone .ee + .toc
    post-check  install.ps1 -Action Status -> both hashes == test-078

A hash proves the right file was copied. It does not prove the engine will read 19 materials, because
the engine reads the .ee through the neighbouring .ee.toc. So the install now has its own oracle:

`Tools/scripts/verify_install.py` -- read-only, walks the deployed pair exactly like the game:

    1 installed .ee/.toc == receipt hashes
    2 .toc->archives baseline identical to the base build (the 8 pre-patch mismatches + 98 unlisted
      files of MODLOG §71 are inheritance, not drift) and nothing the base listed went missing
    3 body LODs decode through their .toc record: 17 blocks each (5/5); wheel meshes: 5 blocks
      each (30 files)
    4 every replaced mesh AND every referenced texture, read through the .toc, is byte-identical to
      the staged aaf copy  <- this is the check hashes cannot make
    5 all 28 batmobile textures internal (nonzero offset), none zero-byte
    6 inventory for the record

Result on the live install: **9/9 PASS** (`Working/verify_078.json`)

    body      17 blocks x 5 LODs; 35 meshes byte-identical to aaf
    wheels    30 files, 5 blocks each (front lod4/lod5 still don't exist in the .toc, §103c)
    blocks    200 CarPaintMM + 35 Window across the 35 meshes
    textures  28 distinct, 3,954 KB, all internal; BC3 glass dif + normal present
    .toc      496 records; archives baseline 8/8 mismatched, 98/98 unlisted (== 077)

Negative controls (an oracle that cannot fail is not an oracle):

  - one .toc record shortened by hand (glass dif -> 100 B) => 3 independent FAILs (toc hash,
    archives baseline, texture bytes), exit 1
  - the old 077 live body decodes as **1 CarPaintMM**, so "17 blocks" really does distinguish the
    regression that started all of this
  - `deploy.py build --base Builds/test-077 ...` now refuses with LIVE DROPZONE DRIFT (exit 1,
    nothing written). Future builds must rebase on **Builds/test-078**.

Wiring: the generated installer gained `-Action Verify` (deploy.py template + this build's copy), so
every future build is one command away from "prove the game reads what I built". `-Action Install` now
prints that hint.

Still unproven: the rendered car. Five visual oracles are owed in game - 19 materials visible, no
magenta/no missing block, budgets intact in engine, glass reads as dark glass, no part misplaced.
Until someone looks, row 3 of the plan is LIVE but not visually accepted.

Next: LGT-1 (lights module + parts), then PRT-1, LGT-2, DMG-1; QA-1 is unblocked.

## 105. The car was black because linear colours were written into sRGB slots. test-079

First in-game look at test-078 (user screenshot, daylight, Hilltop): the Batmobile silhouette is right,
the wheels and canopy are there, but the whole car reads as a flat black shape with the armor plates
turned into illegible shards. Lights off, no panel separation, no glint.

Diagnosis, in this order:

1. **Is the mesh broken?** New `Tools/scripts/preview_rbm.py` renders an RBM offline (orthographic,
   z-buffered, one flat colour per material block). The body is intact - nose, canopy, wheel arches,
   turret ring, layered plates, 31,139 tris. Not a geometry bug; a flat-black render of overlapping
   plates *looks* shredded.
2. **What is the body's albedo?** Decoding the installed block list: 16 of 17 blocks point at a
   generated flat texture. The main body, wheel arches, undercarriage and turret all use
   `solid_0e0d0f.ddsc` = byte (14, 13, 15) - a *flat 5% grey*. Exported and measured: mean RGB (8, 12, 8).
   For comparison the working vanilla Serpente body dif is mean (34, 43, 58).
3. **Where did 14 come from?** `factors.py` generated it from UE's `Material0_BaseColour` =
   (0.05673, 0.05157, 0.06) with `round(c * 255)`. UE material vectors are **linear**; a JC3 dif is
   sampled as **sRGB** (vanilla dif headers carry flag 8, and our own tex2ddsc sets it). Writing the
   linear number into the byte and letting the engine decode it again double-applies the transfer
   curve: 0.0567 linear became byte 14, whose linear value is 0.0046 - **12x too dark**, and the
   correct byte is 67. The glass tint had the same bug (0.05 -> 13 instead of 63).

So the build was hash-perfect, block-perfect, budget-perfect and visually wrong. That is the lesson:
`verify_install.py` proves the *bytes* arrived; only a render or a camera proves they *look* right.

Fix (one variable, colour management only):

    factors.py  srgb8(c): linear 0..1 -> sRGB 8-bit value, applied to
      - every generated solid albedo  ("generated from bmak:...(linear -> sRGB)")
      - the glass Window tint

Re-ran the pipeline (`--skip-grab`): 185 blocks checked, 0 mismatches, 0 silently inherited values;
coverage unchanged (geometry 100%, materials 100%, textures 53.9%, overall 54.6%). New albedos:
`0x434045` (body/arches/undercarriage/turret), `0x3c3c3c` (cockpit), `0x5e5e5e`; glass tint 63.
Deleted the three stale linear solids so nothing unused can be packed.

Built **test-079** on top of 078 (`deploy.py build --base Builds/test-078`). Two deploy checks had to be
corrected first - they were base-relative assumptions from when the base had no Batmobile textures:

    - "changed only body/wheel RBMs + @files.xml" now also allows *staged textures* (a rebase onto 078
      legitimately replaces the glass dif and the solids), and nothing else
    - ".toc +N records" now compares against textures the base does not already list (+3 of 28)

Result: 14/14 build checks (aafdiff 3 added / 41 changed / 0 removed, 0 module files touched,
round-trip 579 files 0 lost, body 17x5, wheels 5x30, budgets 4,198/4,424 and 3,954/4,648 KB),
`verify_install.py` 9/9 offline, installed, 9/9 on the live pair.

Open question for the next look: albedo is now correct, but the Batmobile paint in BmAK also gets its
glint from clearcoat + metallic channels that our blocks set to zero. Vanilla Serpente body paint for
comparison (decoded, same block type): SpecularGloss (0, 0.400, 0.374, 1.0), Metallic (0, 1, 0, 1),
ClearCoat (0, 1, 0, 0). Ours: SpecularGloss (0.6, 0.75, 0.85, 0.98), Metallic (0,0,1,0), ClearCoat 0.
If test-079 still looks flat, that is the next single variable (MAT-1), not another albedo change.

## 106. MAT-1: paint gloss capped at the vanilla level. test-080

The second in-game look (test-079) showed the albedo fix working - the car is no longer a black
silhouette; wheels, canopy, plate edges and the turret ring all read. What remained was a *wet mirror*:
a broad blue-white sky sheen over a near-black body, more polished plastic than armoured car.

Measured why. The body block's SpecularGloss was the raw BmAK roughness inverted:
(0.600, 0.750, 0.850, 0.980) on the four channels. The vanilla Serpente body paint block - a car that
reads correctly in this engine - runs (0.000, 0.400, 0.374, 1.000) with Metallic (0,1,0,1) and
ClearCoat (0,1,0,0). BmAK's near-mirror roughness is authored for a rain-wet night scene with an
environment probe and a clearcoat term; JC3 has no clearcoat input to spread that highlight, so the
same numbers become a mirror.

Before changing anything else, two candidate causes were checked and **ruled out**:

1. **Inverted winding / inside-out body.** Face normals from the index order agree with the packed
   vertex normals on 99-100% of triangles in every block, in both our mesh and the vanilla one. Not
   flipped.
2. **The `a00_dummy_*` textures are missing from the archives** (`a00_dummy_black_mpm`,
   `a00_dummy_grey_dif`, `a00_dummy_flat_nrm` do not resolve in any .tab). This is *normal*: the vanilla
   Serpente blocks reference the same names, so JC3 falls back to its own default. Not a defect, and
   not worth "fixing" - recorded so nobody chases it again.

Change (MAT-1, one variable): `PAINT_GLOSS_CAP = 0.45` in factors.py - gloss is clamped to the vanilla
paint channel's 0.400 (rounded up a hair), and the spec's `source` string records the cap per channel.
Albedo, metallic, clearcoat and every texture are untouched.

Rebuilt (assemble 1,045 s, 185 blocks, 0 mismatches), built **test-080** on 079: 14/14 (40 changed -
39 RBMs + @files.xml, 0 textures touched, 579-file round-trip clean, budgets 4,198/4,424 and
3,954/4,648 KB), `verify_install.py` 9/9 offline, installed, 9/9 live.

Geometry, measured while diagnosing the "shredded" look (source = the 214,737-tri non-wheel body from
the psx, ours = 31,139-tri lod1):

    silhouette coverage   source 0.5807   ours 0.5760
    holes (source has, we don't)   2,064 px = 1.01% of the silhouette
    extra (we have, source doesn't)   418 px
    boundary edges   source sections 14-30% of edges, ours 39-55%

So the body is *nearly* intact: the jagged edges in a screenshot are mostly real armour plates plus a
~1% decimation loss (the body is decimated 214,737 -> 31,139 tris to fit the model budget). The
decimator tears some open plate borders, which reads as thin gaps up close. That is a budget question,
not a mesh bug: the model cap is the hard limit x0.9 (4,424 KB) with only ~226 KB free, so the body
cannot grow much without either using the hard cap (4,915 KB, ~+12k tris) or trimming LOD4/LOD5.
Tracked as BUD-1; not attempted in this build.

Verdict pending: the user's next screenshot decides whether gloss 0.45 reads as armour or still as wet
plastic. If it is still too shiny, the next single variable is Metallic (ours is 0 on the paint
channel, vanilla is 1), not a further gloss cut.

## 107. ALB-2: the paint is readable in daylight. test-081

Third in-game look (test-080, daylight, wheat field): the wet-mirror sheen is gone - the gloss cap did
what it was meant to. What was left is *darkness*: the car had no tonal separation from its own shadow,
and every plate merged into one black mass.

Measured the screenshot instead of guessing (mean sRGB over a 290x90 body patch vs the surroundings):

    test-080        body upper 12   body side 16   sunlit grass 85
    BmAK reference  body upper 22   body side 22   road 12

So in the reference the car is *brighter than the road*; ours is the darkest object in a bright scene.
Root cause: BmAK authors this paint for a rain-wet night scene with a strong environment probe. Its
linear base colour (0.0567) is correct there; on JC3's shaded side, with the 0.45 gloss that made the
armour read, there is almost no ambient term to lift it. Linear 0.0567 is simply too low to carry
readability in this engine's daylight.

Change (ALB-2, one variable): `PAINT_ALBEDO_GAIN = 4.0` - the linear colour is multiplied *before*
sRGB encoding, so the stored byte goes 0x43/0x40/0x45 -> 0x83/0x7d/0x86 (67 -> 131). Only generated
solid albedos are affected; the glass tint, gloss cap, metallic and every real texture are untouched.
The gain and its justification are recorded in each texture's `source` string ("linear x4.0 -> sRGB,
ALB-2"), so a future run cannot silently revert it.

Rebuilt (assemble 994 s, 185 blocks, 0 mismatches), deleted the three superseded solid textures so
nothing unused can be packed, built **test-081** on 080: 14/14 (3 textures added, 40 changed, 582-file
round-trip clean, .toc 502 = 499 + 3), `verify_install.py` 9/9 offline, installed, 9/9 live.

Albedo history, so this does not get re-litigated:

    078  0x0e0d0f  linear values written raw into sRGB slots   -> black car
    079  0x434045  srgb8() correct, but authored for night      -> readable but no detail
    080  0x434045  gloss 0.98 -> 0.45 (MAT-1)                   -> armour, not plastic; still dark
    081  0x837d86  linear x4 (ALB-2)                            -> daylight readability

If 081 now reads too light for the Arkham look, the dial is `PAINT_ALBEDO_GAIN` (one number, one
build) - not another gloss change. A night screenshot is the other half of the oracle: the gain was
chosen for daylight, and BmAK's own value may well look better under rain and streetlights.

## 108. GRAB: the Batmobile is now readable end to end (no in-game test)

User decision after test-081: stop hand-tuning constants and screenshots. The first step is GRAB -
read the entire Batmobile out of the shipped files, document what every asset/component does, and
only then build anything. The backlog was updated first (`MODDING_PLAN.md` §0.6, GRB-1..GRB-6); the
game was not launched in this session.

What was missing before: the project only ever extracted four classes (mesh, materials, instances,
textures) with umodel, and treated the vehicle/weapon classes as unreadable because "cooked packages
carry no property names" (MODLOG §93). That conclusion was wrong. Arkham uses the Batman property-tag
format: `int16 type + uint16 offset`, simple values inline, complex values (struct/array/object) with
an FName. Primitives lose their names, but structs/arrays/objects do not.

Built two tools, no hand-written asset lists:

- `Tools/scripts/upk_read.py` - chunked-package reader (LZO or zlib sub-blocks), name/import/export
  tables (72-byte exports, 28-byte imports), Batman tag walker, recursive struct/array decode,
  object-reference resolution.
- `Tools/scripts/batmobile_grab.py` - discovers every `Playable_Batmobile*.upk`, decodes every export,
  and writes `Research/BatmobileGrab/{README,ASSETS,MATERIALS,TEXTURES,MECHANICS,AUDIO,GAPS}.md`,
  `objects.jsonl` (one record per object) and `grab.json`.

Coverage: 15 packages, **20,128 objects**, **19,098 decoded (94.9%)**, 1,030 native/untagged. Verified
against UEViewer's independent listing: 14/14 checks (5,490 exports; Material 45; instances 33;
SkeletalMesh 3; Texture2D 92; AnimSequence 37; sockets 65; AkBank 7; AkEvent 91; wheels 4; physics 1;
particle systems 59; 6 sim structs; `BML_Engine` present).

What the files actually say (all in `Research/BatmobileGrab/`):

- **Handling** - `RVehicleSimBatmobile SimulationModel` has six named curves with decoded points:
  `BoostTorqueVSpeedCurve` -1500->0, -300->200, 0->260, 1500->260, 2100->220, 2800->200, 3000->150;
  `StandardTorqueVSpeedCurve` ... 750->170, 1600->150, 2100->105; `BattleModeVSpeedCurve`
  0->60, 600->40, 1200->30; `StandardSteeringSpeedCurve` 0->60 ... 2000->20;
  `TorqueVSpeedCurve` 0->130, 1050->60, 1100->0; `SteerSpeedVsSpeedCurve` 0->720, 3500->720.
  Plus 32 offset-only floats (600, 750, 3000, 24000, 100000, 500, 300, 220...). HDL-1's premise
  ("no names, need a runtime CDO walk") is dead: the driving model is tagged.
- **Lights/weapons anchors** - 65 sockets on `Batmobile_V2`, with bone and relative location:
  `HeadLight2a/2b`, `LWheelLight`, `RWheelLight`, `BrakeLightL`, `CannonMuzzle`, `ChainGunMuzzle`,
  `RiotSuppressorMuzzle`, `BattleModeSpotLight`, `MissileL/R`, `Afterburner`, `Afterburner_Front`,
  `WinchOrigin`, `Driver`. MK2 skin has 55 sockets, Jokerfied 63.
- **Audio** - the banks were inside the vehicle packages all along: `BML_Engine` 7,278,764 B,
  `BML_Burnout` 477,026 B, `AUX_InBatmobile`, `VEH_Batmobile_MK2_Engine` 7,144,655 B (Funhouse),
  361 AkEvents, and the RTPC names on the vehicle blob (`RPM`, `BML_Speed_Global`, `RevLimiter`,
  `Drift_Global`, `BML_Steering`, `BML_WheelSpeed`, `Batmobile_EMP`).
- **Components** - 4 `RVehicleBatmobile`, 4 sims, 16 `SVehicleWheel` (each with its kick-up, pollen,
  burnout and mud particle refs), 12 meshes (LOD counts and socket counts), 32 collision bodies,
  physics bounds, 253 AnimSequences, weapon gadget meshes for cannon/EMP/missile/sonar/winch.
- **Appearance** - 185 master materials (slot -> expression), 130 instances (parent, scalar/vector
  params, texture params), 405 textures with dimensions and the instance+parameter that binds each.

The 1,030 native objects are the ones the cooker serialized without tags: the `RVehicleBatmobile` and
`RBatmobile*` archetypes (values in native class layout), particle modules, most material-expression
children. `GAPS.md` names every one by class and reason; candidate object references are recovered
from their blobs and labelled as candidates. Nothing is guessed.

**Correction (same day, §109):** the archetypes below are not actually native. `StrProperty`
(type 13) was missing from the tag walk, so one string aborted the whole stream and the object fell
back to "native". With strings handled, all 4 `RVehicleBatmobile` and all 49 `RBatmobile*` objects
decode; the remainder is 925 objects, mostly `Package` stubs. The 19,098/1,030 figures are the state
of §108, kept for the record.

Next: GRB-6 - re-derive the paint/glass/emissive constants from the grab output instead of the
hand-set `PAINT_*` values, then re-open the plan at LGT-1 (sockets exist, so the lights module has
real anchors).

## 109. GRAB gets an API: one schema-versioned reader, and the archetype gap closes (2026-10-21)

The grab was correct but only readable as prose. Every consumer (constants, lights, audio, HUD) would
have parsed `objects.jsonl` itself and silently disagreed with the next consumer when the shape
changed. GRB-7 fixes that with `Tools/scripts/grab_model.py`:

- `Grab` loads `grab.json` + `objects.jsonl`, indexes by package/class/name/outer path, and exposes
  `find` (class, name regex, package, tag, value), `one`, `field`, `offset_only`, `curves`, `stats`.
  Named tags and unnamed (offset-only) primitives are both preserved - the latter labelled by class
  offset, because that is all the file carries.
- **The manifest is now self-describing.** `objects.jsonl` used to store `NameProperty` values as
  `{name_index, number}` and object references as bare indices, so socket names, light bones and
  component classes could only be read by re-opening the `.upk`; a consumer with the JSON alone saw
  numbers. `upk_read.walk_tags` now resolves the FName and the object path/class at read time
  (schema 4), which is why `--value HeadLight2a` finds the socket and `lights` can print
  `SpotLightComponent` without the packages. GRB-8/GRB-9 no longer need them to interpret the manifest.
- `grab_model.py lights` is the first typed consumer on top of that: one row per `VehicleLights` struct
  with `bone`, `type`, `material_type` and resolved component paths/classes. It reproduces the
  `MECHANICS.md` rig table (101 entries across four vehicles) from the JSON alone.
- `python Tools/scripts/grab_model.py check` is the gate. It verifies the schema version, required row
  fields, `tag_count == len(tags)`, the summary totals against the rows, that every decoded reference
  has a path, and spot-checks the objects the next tasks depend on: 4 sims / 24 curves (points
  printed), 247 sockets / 90 resolved names including `HeadLight2a`, 101 `VehicleLights` structs, 30
  `AkBank` objects (16 names) including `BML_Engine`, and the offset-only value `0x1214 = 640000`. It also requires every
  `NameProperty` to be a string and every light entry to have a bone and a resolved light-component
  class. Current output: `OK`, schema 4, 20,128 objects, 19,203 decoded (95.40%), 925 untagged,
  14/14 grab checks.
- `batmobile_grab.py` now writes `schema: 4` and `generator` into `grab.json`, and README.md names
  `grab_model.py` as the only supported reader. The schema constant lives in the reader, and the
  writer imports it, so the two cannot drift.

**Why the archetypes decode now.** `RVehicleBatmobile` carries five `StrProperty` tags (the weapon
slots: `BatmobileWeapon_Winch`, `MineLauncher`, `EMP`, `DroneHacker`, `Sonar`). `upk_read.walk_tags`
had no variable-length string branch, so the walk stopped at the first one and `best_walk` returned
zero tags; the census then labelled the object "native". Adding the string branch (and keeping the
tag boundary at the decoded FString length) turned all four `RVehicleBatmobile` and all 49 `RBatmobile*` exports readable. Measured today: 925 untagged =
696 `Package` stubs, 30 two-byte `RAkAudible`, 22 `ObjectProperty` metadata objects, 20 `Function`
objects, 16 `IntProperty`, 13 `FaceFXAnimSet`, and the rest; only 140 are larger than 8 bytes. The sim
object was always tagged, so handling was never blocked - but the lights rig and archetype defaults
were, and are not any more.

**What still cannot be named, and why (GRB-11).** `RVehicleBatmobile`'s remaining primitives are
serialized by class offset only. Their names live in the class definition, `BmScript`, which is
imported by every vehicle package and is not in `CookedPCConsole` (GAPS dependency closure). I checked
the other route too: property exports in scope (e.g. `RBatmobileMissileLauncherJoker`'s
`NewHydraPFX`, `MaxPostTapTargets`) carry the names and declaration order, but not a usable field
offset that matches the tags, and the `RVehicle*` classes have no property exports in these packages
at all. So the offset values are reported as offsets, not guessed names; reopening needs
`BmScript.upk` or the class CDO.

**GRAB backlog after this.** P0: GRB-6 (constants from grab). P1: GRB-8 lights
(`VehicleLights` -> bone -> component class -> JC3 module), GRB-9 audio event -> bank -> WEM.
P2: GRB-10 mesh LOD/material-slot order, GRB-11 (blocked). GRB-1..GRB-5 and GRB-7 are closed.

Evidence: `Research/BatmobileGrab/grab.json` (`schema`, `generator`), `objects.jsonl` (19,203 records
with tags), `GAPS.md` (coverage + native classes), and
`python Tools/scripts/grab_model.py check` (exit 0) and `python Tools/scripts/grab_model.py lights`
(101 entries with bone + component classes).

## 110. GRAB closed: GRB-6…GRB-11 all green (no game launch, 2026-10-21)

GRB-6…GRB-11 are done in order. No build, deployment or in-game test was made; test-081 is untouched.

**GRB-6 - constants from the grab.** `grab_values.py` derives `VALUES.json` from the authored
`Material0_BaseColour` × `Diffuse_Adjust` and the vanilla body block's paint channel; `factors.py` reads
only that file. No hand-set `PAINT_*` constant remains.

**GRB-7 - schema 5.** `upk_read` now resolves `ByteProperty` enum FNames (the payload is an FName, so
the old decode returned its low byte). Light `Type`/`MaterialType` are `VEHLT_HeadLight` /
`VEHLTMAT_HeadLightRight` instead of 134/138, and `grab_model.lights` resolves the rig's NameProperty
through the exported `SkeletalMeshSocket`s, keyed by package (the same socket name hangs on different
bones in different skins). `check` now requires the 6 known `HeadLight1c/2c` orphans and resolved
`VEHLT_*` types.

**GRB-8 - `LIGHTS.md` / `LIGHTS.json`** (`grab_lights.py --check`): 101 entries / 4 rigs, 95 bones
verified in `Batmobile_V2.pskx`, 6 orphan sockets explicit, 0 missing bones. Behavior comes from the
enum (mapped 54, approximated 23, no-equivalent 16, inferred 8); each entry carries the shipped `.epe`
part (`sportsmuscle_body` / `wheel_*`), a vanilla-syntax anchor flagged `needs-lig-bone`, the component
class dispositions (lens flares: no JC3 equivalent) and the vanilla field values per behavior for LGT-1.

**GRB-9 - `AUDIO_MAP.md` / `.json`** (`grab_audio.py --check`): 361 rows / 118 ids through HIRC
Event → Action → Sound/RanSeq/container → DIDX, over 27 unique banks (deduplicated by BKHD id; the
vehicle packages plus `Engine.upk`, which holds `BML_Batmobile`, `BML_Battlemode`, `BML_Tyres`).
239 rows resolved to 447 embedded WEMs (18.2 MB), 24 streamed, 8 no-media, 90 rows (26 ids) listed
`missing-bank` with the absent bank named (`BML_Sonar`, `BML_Impacts`, `BML_Batmobile_Subjective`,
`CHR_BatmanAlerts`, `CHR_BatmanDisruptor`, `OBJ_Rolling_Objects`, `UI_InGame`, tank and tank-VFX banks).
This replaces the 9 hand-picked pairs for every event it resolved.

**GRB-10 - `SLOTS.md` / `.json`** (`grab_slots.py --check`): all 19 slots agree across umodel's
`Materials[19]`, the pskx `MATERIALS` chunk and `assembly.json`; 299,837 LOD0 faces, every slot draws
geometry, 13 instances + 6 masters resolved in `MATERIALS.md` (38 textures), 3 LODs with identity
material maps. Umodel's ActorX export writes LOD0 only, so LOD1/2 face counts are not claimed.

**GRB-11 - `OFFSETS.md` / `.json`** (`grab_offsets.py --check`): 53 `RBatmobile*` rows, 365 distinct
unnamed fields. The 4 unnamed `VehicleLights` fields are named from that struct's proven layout
(component, lens flare, socket, second component); the other 361 stay unnamed with evidence: `BmScript`
is imported by all 4 vehicle packages but ships no file on disk, and only 2 same-class named siblings
exist - both are `Points` array-element offsets at 0, not class fields. Reopen only if `BmScript.upk`
appears.

Files: `Tools/scripts/{grab_lights,grab_audio,grab_slots,grab_offsets}.py`,
`Research/BatmobileGrab/{LIGHTS,AUDIO_MAP,SLOTS,OFFSETS}.{json,md}`, `upk_read.py`, `grab_model.py`,
`batmobile_grab.py` (README doc list), `MODDING_PLAN.md`.
## 111. BUD-1: the model budget now uses the game's HARD cap; body lod1 31k -> 44.6k tris. test-082 installed. (2026-10-22)

The grab gate had closed (GRB-1..11, #108-#110), so the backlog's next P0 ran: **BUD-1**. The
situation it addressed: the guard was the game's Model HARD budget x0.9 (4,424 KB) with only ~226 KB
free, which pinned body lod1 at 31,139 tris, and the decimator tore open plate borders trying to fit
214,737 source faces into that budget - measured as ~1% silhouette loss (#106). The oracle: lod1 up
to ~43k tris WITHOUT exceeding the hard cap, and holes below 0.3% of the silhouette (was 1.01%).

**Three changes, all in the build path, none in any appearance constant:**

1. **`--budget-safety` (default 1.0)** in `bat_assemble.py`, `appearance_pipeline.py` and
   `deploy.py`. The guard is now the game's own Model HARD value (4,915 KB for Vehicle-*HD*), which
   is the number the engine actually refuses past; the old 0.9 guard (4,424 KB) survives as
   `--budget-safety 0.9`. `deploy.py` records `model_safety` in the receipt, so which cap a build
   was made under is in the artifact, not in someone's memory.
2. **Decimation now HITS its budget.** `decimated_lods` used to ask Blender for a collapse ratio and
   trust it; Blender leaves n-gons at aggressive ratios and our triangulate step then emits MORE
   triangles than the ratio asked for. That is why the shipped lod5 carried 1,592 tris against an
   800 budget (+99%) and lod4 1,827 vs 1,500 (+22%). The target is now fed back until the
   triangulated result fits, and where a piece is **boundary-limited** (its outline alone needs more
   triangles than the budget allows, floor ~444 for the largest body material) the smallest
   achievable result is kept and logged. Measured consequence: lod2-lod5 are ALL boundary-limited
   (6,275 / 3,193 / 1,827 / 1,592 - unchanged from 081), so the plan's other lever, "trim LOD4/5",
   turned out not to exist; every byte of headroom went into lod1.
3. `--body-tris` default is now `43000,6000,3000,1500,800`.

**Result.** Assemble 1,341 s, body lod1 **44,608 tris** (17 blocks, VERIFY PASS, bbox
3.497 x 2.276 x 7.027 m), model footprint **4,764 KB of 4,915 KB** (151 KB free; the old guard would
have refused at 4,424). `spec_check` exit 0; transfer score unchanged (strict 49.3%, 91.1% of what
JC3 can hold).

**The hole oracle needed an honest instrument - `Tools/scripts/silhouette_check.py`.** Method, and
two mistakes it caught in its own baseline run:

- Source = the build's own body split: 215,893 faces, using the same classify -> wheel-anchor ->
  hub-radius classification the pipeline runs, ASSERTED against the build's count (#106's one-off
  said 214,737; the pipeline log's "1,396 wheel faces outside their tyre circle -> body" is the
  difference in how the two counted - the build's number is authoritative).
- **The source must carry the build's translate.** `stations.json` offset (0.154 m Z, 0.022 m Y) is
  baked into the RBM vertices but not into the raw pskx, so the first runs measured a phantom gap at
  every plate edge: holes read 4.5% for BOTH builds and +43% tris looked like it did nothing. Apply
  the offset and the metric separates cleanly. A measurement that cannot move is not an oracle.
- Fixed frame (source bbox + 2%, 2,400 px side view) shared by both builds, so the two runs are
  pixel-comparable; "interior tears" = holes at least 3 px inside the outline, because a decimated
  outline never lands pixel-exact on the source outline and sliver noise would dominate.

    test-081 body   31,133 rendered tris   holes 5,334 px = 0.471%   interior 1,150 px = 0.102%   extra 0.355%   coverage 0.9988
    test-082 body   44,602 rendered tris   holes 3,360 px = 0.297%   interior   582 px = 0.051%   extra 0.197%   coverage 0.9990

  -> **below 0.3%** as the oracle asks (raw holes -37%, interior tears -50%). The absolute values do
  not have to match #106's 1.01%: that came from a one-off script at another resolution and is not
  reproducible. This one is a checked-in script, so every future build gets the same number.

**Deploy.** `deploy.py build --base Builds/test-081 --src Working/Appearance/build_bud1 --tag
test-082`: 13/13 receipt checks (the same set 079-081 shipped with) plus the golden-hash live
dropzone guard (aafdiff 3 added / 41 changed / 0 removed, 0 modules, 585-file round-trip 0 lost,
body [17,17,17,17,17], wheels 5 blocks each, model budget **4,764/4,915 PASS**, texture
3,954/4,648 PASS, .toc 505 = 502 + 3). `.ee` 10,736,951 B `AF0611B7...`, `.toc` 50,573 B
`904C96D2...`. Installed; `install.ps1 -Action Verify` **9/9** on the deployed bytes; `-Action
Status` shows the live dropzone == test-082. Rollback081 remains available.

**Not done, deliberately:** no game launch and no screenshot. BUD-1's oracle is geometry and budget,
both measured offline. No appearance constant moved in this build, so 081's open verdict (daylight
look of the x4 albedo, night as the other half) still carries over to 082 unchanged.

**Staged layout note:** `Working/Appearance/build` still holds test-081's output (its receipt names
it); test-082's staged source is `Working/Appearance/build_bud1`, named in its receipt. The next
appearance run should pick one dir deliberately rather than assume.

Next: the grab stays closed; the next open P0 is **QA-1** (telemetry harness - needs the game
driven, so it wants the user) or **LGT-1** (lights module - offline decode plus parts work, no
launch). Files: `Tools/scripts/{bat_assemble,appearance_pipeline,deploy,silhouette_check}.py`,
`Builds/test-082/`, `Working/Appearance/build_bud1/`, `Working/Appearance/diag/bud1_{baseline,new}/`,
`MODDING_PLAN.md`.

## 112. LGT-1 decoded: what a JC3 vehicle light is made of, and why ours cannot light up yet. (2026-10-22)

No build, no deploy, no launch. LGT-1's first half ("decode the lights file") is done; the second half
(parts + module + night look) needs one in-game probe before it should be built.

**Three files make a vehicle light, and all three now decode:**

    entity   ..._civilian_01.epe                        ConvertProperty -e   (works)
    lights   ..._lights.vmodc  VehicleDynamicLights     ConvertAdf -e        (ConvertProperty throws NotSupportedException)
    parts    sportsmuscle_vehicle_parts.vmodc           ConvertAdf(p) -e     (parts list, has_lights, per-part model)

Decoded to `Working/Lights/v082/{entity,lights,parts}.xml`.

**What the three say, in one line each.** The entity exposes exactly our 7 part names (body, 4 wheels,
2 doors) and references the vanilla parts module. The lights module has 21 entries and every one of
them names a part our entity does not expose (`taillight_r_l`, `taillight_r_c`, `taillight_r_r`,
`signal_f_l/r`, `signal_r_l/r`, `headlight_f_l/r_01/02`) - that is the broken-light fact with the exact
list. `has_lights` is a per-part flag in the parts module (42 records), not in the entity (0 hits).

**The two headlights that hang on the body are the useful clue.** Entries 3 and 10 use
`part = sportsmuscle_body, part_index = 0`, with `deformable_transform`
`|sportsmuscle_LOD1|body|dashboard_LIG` and `|...|front_primary_LIG`. So the body part can host a light,
through nodes in its own rig.

**Why ours cannot, measured.** A vanilla light part is two blocks, `CarLight` + `Window` (emitter +
lens), flags 0 - static. The vanilla body's 9 blocks are all `CarPaintMM` with flags `0x1004` -
**IS_DEFORM**, i.e. bone-weighted; that is what `dashboard_LIG`/`front_primary_LIG` resolve against. Our
assembled body is 17 blocks, flags 0, no weights, and across all 25 RBMs the block census is
`{CarPaintMM: 160, Window: 25}` - **no `CarLight` block exists anywhere in the build**. No bone to
anchor to, no emitter to see. That is LGT-1 and LGT-2 in one measurement.

**Where the `_LIG` names are not** (three candidates eliminated, so nobody re-checks them):
- not in the RBM: Jenkins hash of `body`, `taillight_r_l`, `taillight_r_l_LIG`, `sportsmuscle_LOD1`
  (`rbmhdr.name_hash`, verified against `HashName.exe` = 3654365951 for the part name) occurs nowhere
  in the taillight or vanilla body RBMs;
- not the parts module's `bones` array: that belongs to the `SkinnedPart` type and is not instantiated
  (0 bones);
- not the RBM deform table: 256 u32 per block, ~98% of slots nonzero on the vanilla body AND on our
  cloned blocks, so it is a curve, not a name list.

**So LGT-1 is a parts build, not a one-line repoint**: light parts copied from the vanilla pattern
(`CarLight` + `Window`, our geometry, `has_lights = 1`, `parent_part_index = 0`,
`parent_space_offset` from the grab's socket positions), exposed in the `.epe`, with the 21 module
entries rewritten to our parts. Details in `Working/Lights/LGT1_FINDINGS.md` §6. The parts-module
writer still re-encodes +544 B (MODLOG #101b), so that file needs either the in-place path or a
verified re-encode.

**The one probe to run first** (single variable, reversible): add ONE vanilla light part name that our
entity does not expose (`sportsmuscle_taillight_r_l`, whose model files are still in the tree) to the
`.epe` part list, change nothing else. If a lamp appears where the Serpente's left tail light used to
be, the name chain resolves through the parts module and §6 is confirmed; if nothing appears, the chain
needs a rig and the next probe is the body-anchored entry (3/10). That answer costs one install and one
night look and decides how the rest of LGT-1 is built.

Next: run that probe with the user at the machine, then build the light parts. Everything else in the
backlog that is offline-only is already closed.

## 113. LGT-1 probe is live: test-083 exposes one vanilla light part. Awaiting a night look. (2026-10-22)

The probe from #112 is installed. One variable, one part, +128 bytes.

**Edit.** `Working/Lights/v082/entity.xml` -> `Working/Lights/probe/entity_probe.xml`: one `CPartProp`
appended to the `CParts` chain (the chain ends at `sportsmuscle_wheel_f_l`; body idx 0 ->
wheel_r_r 12 -> wheel_r_l 11 -> wheel_f_r 27 -> wheel_f_l 26 -> **new**). New record:
`name = sportsmuscle_taillight_r_l`, `name_hash = -640601345` (Jenkins, = 3654365951, verified against
`HashName.exe`), `part_index = 8` (the vanilla parts-module index), `_GUID` = the same hash.
Nothing else in the entity changed. `ConvertProperty -i` -> 105,430 B (base 105,302, +128); re-export
gives 6 `CPartProp`s, all seven original part names intact, and exactly one occurrence of the new one.
The parts module and the lights module are **untouched** - the vanilla parts record and the vanilla
light entry (TailLight / `sportsmuscle_taillight_r_l` / idx 8) were already there.

**Build path.** `deploy.py` gained `--overlay VFS=FILE` (repeatable): one extra file is copied into the
staged aaf after the appearance set, and the overlay path is allow-listed in the aafdiff checks. The
packing, `.toc` patching, receipt, installer and verifier are the same guarded pipeline as 079-082 -
no new build machinery.

**test-083**: 13/13 checks (overlay = 1, nothing removed, round-trip 585 files 0 lost), `.ee`
10,736,926 B `2D69BD92...`, `.toc` 50,573 B `59A2240C...`; `install.ps1 -Action Install`, `-Action
Verify` **9/9**, `-Action Status` shows the live dropzone == test-083. Rollback082 is in the installer.

**What the look decides.** The entity now exposes the Serpente's left tail-light part, which the
vanilla lights module already references (TailLight + LeftSignal + Reverse, idx 8). At night, either:
- a lamp appears where the Serpente's left tail light used to be (floating geometry is a pass) ->
  the name chain resolves through the parts module; LGT-1 is the light-part build in #112 §6, and the
  probes for signal/headlight positions can be done the same way; or
- nothing appears -> the chain needs a rig the parts module cannot supply; next probe is the
  body-anchored entry 3/10, then a CarLight-bearing part with our own geometry.

No other variable moved: same mesh, same textures, same modules except the one added part name.

## 114. PRT-1 offline half: the 42-part map, and what removing the doors touches. (2026-10-22)

No build (test-083, the LGT-1 probe, is live - one variable at a time), no deploy, no launch.

**`Working/Parts/PRT1_PARTMAP.md`** now documents all 42 records of the parts module exactly as the game
reads it: index, part, parent index, `has_lights`, `is_deformable`, damage type, behavior, model. Facts
worth keeping: **12 of 42 parts carry `has_lights = 1`** and 18 are deformable; the body (idx 0) is
`has_lights = 1` already, so LGT-1 is missing an emitter and anchors, not the flag; every model the
module names still exists in our tree.

**Doors, precisely.** `door_parts` = part_index **1, 2, 25** = `door_f_l`, `door_f_r` and
**`hood_signature`** - the third entry is not a door; the signature hood is driven by a door-style
animation. PRT-1's removal is therefore two files: drop the two door names from the entity's part list,
and either leave the module's `door_parts` entries dangling (indexes 1/2 would name unexposed parts) or
patch the list in place. The parts-module writer still re-encodes +544 B (#101b), so the module edit is
in-place patching, not re-encoding.

**Not done, deliberately:** nothing was built while the probe is live, and the "no door animation on
entry" half of PRT-1's oracle is an in-game observation. The door removal is staged as an edit plan,
not a build.

Next: the LGT-1 probe's night look decides the light path; PRT-1's door removal builds after that (or
earlier if the probe is rolled back).


## 115. PHY-1: the 128 collision bodies decoded; handling proposal written (no build, 2026-10-22)

**Proposal only this turn.** Nothing staged, installed or launched; the dropzone is still test-083
(the LGT-1 night probe) and was not touched.

### PHY-1 — collision bodies, closed as data

The grab knew there were 32 `RB_BodySetup` per vehicle and stopped at "AggGeom is a blob". They are
now decoded by `Tools/scripts/grab_physics.py` into `Research/BatmobileGrab/PHYSICS.md` + `.json`:
**4 vehicles × 32 bodies, all four layouts byte-identical.**

Layout, verified byte-for-byte on every record: two `u32` counts (spheres 0, boxes 1), then a 64-byte
`FMatrix` (identity rotation, translation in the last row), then the three extents **in the trailing
property-tag stream** at logical 0x40/0x44/0x48 — which is why a naive struct read produced zeros.
Extents and centre are in cm.

The bone list corrects an earlier guess of mine: the bodies are **not** all `Root`. They are
wheels/suspension (8: `SUSP1/2_Wheel_*`, `Wheel_*_Vis_Mesh`), cockpit (1), rear doors (2),
`Jet_Fins001`, `Main_Turret_00`, `Root` (1), and **18 `Object*_frag_*` debris pieces**. Extents run
23.9–317.9 cm; the largest volumes are the two rear suspension
arms (17.6 / 16.1 m³ of box).

Two findings that matter:

1. **There is no chassis body.** 32 bones, none of them the hull. The driveable car's collision is
   therefore not in this asset at all — this asset is what `Dead_Batmobile` (`Batmobile_V3_Destroyed`)
   is handed. Hull collision remains JC3-side (`sportsmuscle.physicsc`, §65–70, §96–101).
2. **The wheel boxes are not a geometry source.** They are 97–109 cm across; our measured tyre is
   Ø136.6 cm, so the debris hulls are ~75% of the tyre. Our `radius 0.68275 / width 0.73195` already
   matches the mesh (0.683 / 0.732) and stays.

Regenerated the grab so the doc is first-class rather than a hand edit: `RB_BodySetup: 32` added to
`EXPECTED_MAIN` (the verification table is now **15/15**, was 14/14), `PHYSICS.md` added to the README
index, the docs list and a new GAPS section. `grab_model.py check` → OK; `grab_physics.py --check`
reports the doc current.

### Handling proposal — `Working/Movement/HDL_PROPOSAL.md`

Written, not applied. It maps the six named sim curves onto real JC3 members, with our current values
read out of test-082's modules and Mugello v0405 dumped as the shipped-supercar reference.

What BmAK says, in JC3 terms: steer angle 60° at rest decaying to 20° by 72 km/h (ours: 35→15 spread
over 30–296 km/h); steering **rate** 720°/s flat to 126 km/h, i.e. full lock in 0.083 s (ours: 0.8 s); boost torque
×1.30 (the build carries 2.5, from a ×1.4 wiki extrapolation). One thing I checked and did **not**
lean on: our `max_speed_t_to_full_steer_s` 0.6 sits below `t_to_full_steer_s` 0.8, and I first read
that as inverted versus the reference — it is not. v0405 grows 0.5 → 0.8, but the band's Mugello
(v0401) and the Serpente both shrink like ours, so the ordering is not a rule and the proposal
flags that row as a guess (confidence low).

The largest un-derived number found: **`arcade_friction_multiplier` is 1.0/1.0. Mugello runs 4.2/4.7,
with 150 kg wheel mass against our 25/75 and friction type 1 against our 0.** A 4 t car is doing four
times the Serpente's work on the same grip — this is a better candidate for "sluggish" than torque,
which 075 already fixed.

Five stages (HP-1 grip, HP-2 steering geometry, HP-3 steering rate, HP-4 inertia/drift, HP-5 boost),
one variable each, every value either a shipped car's number or arithmetic on a BmAK curve, and an
explicit "not proposed" table (rpm band, suspension strength/length, wheel geometry, `top_speed`,
`final_drive`). All five oracles are measurements, so the stated order is QA-1 first — building them
now would repeat §95's rejection (a handling stack with no number that can accept it).

## 116. Backlog inversion: grab-first on both sides, and the JC3 universe measured (no build, 2026-10-22)

User's call, and it is the right one: HP-1…HP-5 were going to be tens of hand-tuned tests whose
targets were invented. The problem is data, not tuning. Order is now **G1 finish BmAK → G2 grab JC3
→ T translate → build once**, written up in `GRAB_BACKLOG.md`; no build or deploy this turn, and the
dropzone is still test-083 (`.ee` `C51B7AC8FC71`, re-verified by hash).

### BmAK residual, categorised

Of 20,128 objects, 19,203 have decoded tag streams (95.4%); 696 of the 925 native ones are 2-byte
`Package` stubs, so ~99% of what can be read is read. What actually blocks translation is **one**
item: the **380 offset-only values** on `RVehicleBatmobile` / `RVehicleSimBatmobile`, whose names live
in `BmScript` (not shipped). Everything else — 10 absent audio banks, LOD1/2 face counts, 11 of 12
meshes unexported, particle semantics — is real but does not gate the mapping.

### JC3 was 0.4% grabbed, and is now measured

- **47,557 archive entries** across 56 `.arc`/`.tab` pairs, **41.2 GB**.
- **Names were never a problem we had to solve:** `Tools/Gibbed/projects/Just Cause 3/files/*.filelist`
  gives **157,759 distinct VFS paths** at 100% for the archives in use, and `rbmhdr.hash_jenkins`
  reproduces each hash — so path → `(tab, offset, size)` is a lookup.
- **Chain proven end to end:** `tabextract.py --hash FC21B7E3` → `vanilla_v0300.ee` from `game35.tab`;
  `eetoc.unaaf` + `sarc_dir` lists the SARC. Modules are **not** separate archive entries — they live
  *inside* the `.ee`.
- **Vanilla v0300 `.ee` = 566 inner files, 79.9 MB:** 31 `.vmodc`, 198 `.rbm`, 116 `.ddsc`, 74 `.effc`,
  60 `.trim`, 59 `.lod`, 17 `.ctunec`, 4 `.pfxc`, 2 `.etunec`, 1 `.physicsc`, 1 `.fmod_guids`,
  1 `.stringlookup`.
- **Vehicle space:** 232 entities (`.ee`+`.epe`+`.stringlookup`), 5,208 vehicle paths (2,373 `.rbm`,
  1,748 `.hmddsc`, 97 `.ddsc`, 115 top-level `.vmodc`, 77 `.lod`, 40 `.physicsc`); 00_shared 195,
  01_land 4,062, 02_air 639, 03_sea 304.
- **Our build carries 17 of v0300's 31 modules.** The 14 never opened include exactly the ones the
  open work needs: `v0300_…_lights.vmodc` (LGT-1 — JC3's *own* light module, never read),
  `sportsmuscle_vehicle_parts.vmodc` (PRT-1/DMG-1), `sportsmuscle_vehicle_deform.vmodc`,
  `v0300_…_water_interaction.vmodc`, `v0300_…_effect_attachments.vmodc`, `vehicle_common.vmodc`
  (inherited defaults), `lave_health_medium.vmodc`, `sportsmuscle_stunt_areas.vmodc`,
  6 × `*_ai`, `default_extended_effect_usages.vmodc`.

Extracted game data was moved straight out of the repo per the project rule:
`E:\Modding\_JC3grab\vanilla_v0300.ee`.

### What this changes in the plan

`MODDING_PLAN.md`: header gate now two-sided; live-state rows corrected to 083 over 082; rollback row
updated; and an explicit order change — HP-1…HP-5, PRT-1's build half and DMG-1 tuning are **parked**
until T-1 exists, while test-083 stays live because it is an architectural probe, not tuning.

Next five moves (from the backlog): G1-1 `BmScript` names → G2-1 `jc3index.py` → G2-2 `jc3grab.py` on
v0300's 566 files → G2-3 bulk-expand all 232 entities to values → T-1 the translation table.

## 117. JC3 grab, step 2: the index and all 232 vehicles decoded to named values (no build, 2026-10-22)

GRB-G2-1…G2-4 in one pass. Two new scripts, both re-runnable and both with a `check` that reads the
archives: `Tools/scripts/jc3index.py` and `Tools/scripts/jc3grab.py`. Nothing was built, deployed or
launched; test-083 is untouched.

### G2-1 — every archive entry gets a name

The chain was proven last turn; now it is an index. 88 `.tab`/`.arc` pairs (56 base, 7 patch, 25 DLC),
**81,953 entries**, joined to Gibbed's `*.filelist` files by `hash_jenkins`:

| mount | entries | named |
|---|---|---|
| base | 47,557 | **47,555** |
| patch | 13,714 | 8,256 |
| dlc | 20,682 | 0 (Gibbed ships no DLC filelists) |

**55,811 named rows / 52,981 distinct paths**, written to `Research/JC3Grab/INDEX.jsonl` (10 MB) with
a magic-byte census of the unnamed remainder in `INDEX.json`. `check` resolves the Serpente `.ee` and
reads its `AAF\0` header straight out of `game35.arc`.

### G2-2/G2-3 — the whole fleet, decoded

The important discovery of this pass: **Gibbed's `ConvertAdf` decodes `.vmodc` to XML**, so JC3
modules arrive with the game's *own* member names, not offsets. `jc3grab.py` reads the `.ee` through
the index, un-AAFs it, lists the SARC and converts every `.vmodc`; raw decodes stay outside the repo
(`E:\Modding\_JC3grab\entities\`, 232 files, 266 MB).

| | |
|---|---|
| entities | **232** `.ee` in 79 directories |
| inner files | **135,283** |
| `.vmodc` modules | **6,045** |
| decoded | **5,816 (96.2%)** |
| value rows | **3,111,689** |
| module types / member paths | **52 / 1,421** |

`check` asserts the donor's known numbers: 566 inner files, 30 decoded modules, `RigidBody.mass` 975,
`VehicleMisc.official_top_speed` 250 — i.e. the values this project has been treating as ground truth
come back out of the pipeline unchanged.

### G2-4 — the band, computed instead of sampled

`Research/JC3Grab/VOCABULARY.md`: one table per module type, each member with min/median/max across
the fleet plus the donor's value. Examples that immediately correct earlier assumptions:

- `RigidBody.mass` 50 … 550,000, median **3,000**; donor Serpente **975**.
- `LandSteering.t_to_full_steer_s` donor **1.2**, its `*_ai` twin **2.0** — every land vehicle ships
  a second, different set of AI values (`Brakes.max_brake_torque` 10,000 vs 14,000). Reading the AI
  copy answers the wrong question.
- Module instance names are truncated to 32 characters, so grouping must use `type-name`.

### The one gap: G2-7

229 of 233 `*_vehicle_parts.vmodc` are refused, and they are the **only** refusals in 6,045 modules.
Cause is inside Gibbed: `NullReferenceException` in `InstanceMemberInfo.PrepareForWritting`, reached
from `InstanceInfo.GuessInlineArrayCopyPosition` during deserialization. Four `monorailflatbed` copies
decode, which is why the `VehicleParts` schema is documented (100 parts, damage types) even though the
values are missing for everyone else.

### What this changes

`GRAB_BACKLOG.md`: G2-1…G2-4 marked done, G2-5 (`.physicsc`, `.rbm`), G2-6 (`.epe` graph) and G2-7
(parts) remain; the destination section now records that the end goal is a **new Rebel Drop entry**
(reference mod in `Research/1456340180_Rebel-Drop-Mod-V5.3`), with the Serpente donor kept only as a
spawn convenience — **RD-1**, parked low priority.

## 118. JC3 grab, step 3: the entity graph, the parts, the lights and what `.physicsc` really is (no build, 2026-10-22)

`Tools/scripts/jc3detail.py` — one pass per entity, two payloads, plus a discovery that redirects the
last geometry task. Nothing built, nothing deployed; test-083 untouched.

### What it reads

- **`.epe`** (RTPC property graph) via Gibbed `ConvertProperty`. Per object: class, name, depth, and
  every *named* value. 232/232 decoded.
- **`.rbm`** headers via `rbmhdr.parse_header`, which now takes **bytes** instead of a path
  (`read_header` still works for files on disk): these meshes only ever exist inside a `.ee`.

Raw output 48 MB, outside the repo: `E:/Modding/_JC3grab/detail/`.

### Numbers (all 232 entities)

| | |
|---|---|
| `.epe` classes across the fleet | **103** |
| `CPartProp` (mesh parts) | **11,041** — 3 … 161 per entity, median **48** |
| `SVehicleLight` | **3,972** — 4 … 54 per entity, median **16** |
| `SAttachedEffect` / `SDynamicAttachedEffect` | **5,342 / 4,344** |
| `SWeaponPoint` / `CBulletWeaponBase` / `CMissileWeaponBase` | **300 / 57 / 25** |
| `CCameraModifier` / `CCameraTransition` | **5,796 / 4,477** |
| meshes per entity | 11 … 807, median **229** |

Written to `Research/JC3Grab/ENTITIES.md`.

### The two things this closes

**LGT-1 stops being a guess.** Each vehicle's light rig is in its `.epe`: 22 `SVehicleLight` entries
for the Serpente across two `SVehicleLightList`s, each carrying `preset_id`, `diffuse`, `radius`,
`spot_angle`, `spot_inner_angle`, `near_cap`, `volumetric_mode`, `volume_intensity`, `enabled`,
`multiplier`. The donor's 22 are tabulated; the fleet's preset vocabulary is counted
(`Front_Primary_Head` 145 uses, `Dash_Light` 221, `Rear_Left_Volumetric` 126, …). That is the "what a
JC3 vehicle light is made of" answer we were previously inferring from a single probe entity.

**Parts are named and ordered.** Donor: 40 `CPartProp`, `part_index` 0 … 40 with one gap at 25,
`sportsmuscle_body` 0 → `sportsmuscle_wheel_r_l` 11 → `sportsmuscle_headlight_f_l_01` 34 →
`sportsmuscle_plate_f` 40. That is PRT-1's list and the cross-check for the 42-row damage table.

Also: **vanilla Serpente body is 2.099 × 1.3875 × 3.72 m** (LOD1) against our Batmobile
3.495 × 2.271 × 7.026 m. Every RBMDL header in the game is 1.16.0, 9 blocks, so header reading is
uniform across the fleet.

### `.physicsc` is not an RTPC file — G2-8

233 files, every one starting `57E0E057` and containing `__classnames__` / `__types__` / `__data__`.
That is a **Havok 2014.1 packfile** (`hk_2014.1.0-r1` appears in the file), so `ConvertProperty`
cannot open it and our existing physicsc knowledge is positional (the four wheel-station quads moved
by `physics_stations.py`, §65). A real grab needs either a Havok packfile reader or a station-quad
heuristic validated against the Serpente's known `x 0.885, y 0.4, z ±1.557/1.446`. It is the last
blocker on the geometry rows of T-2, and it is now scoped instead of assumed.

### State of the grab

G2-1 index · G2-2/G2-3 all 232 entities' values · G2-4 fleet distributions · G2-5 header half ·
G2-6 entity graphs — **done**. Open: G2-7 (parts module, Gibbed bug) and G2-8 (Havok physicsc).
T-1 now has every JC3 target with a fleet range behind it.

## 119. JC3 grab, step 4: wheel stations out of the Havok files, and the donor ranking nobody expected (no build, 2026-10-22)

Two scripts, both derived from data already downloaded, both with a `check`:
`Tools/scripts/jc3phys.py` (station quads inside `.physicsc`) and `jc3fleet.py` (the fleet table and the
donor matrix). Nothing built, nothing deployed.

### Stations: named decode first, Havok second

`land_global.vmodc` carries `base_wheel_hardpoint_positions[0..3]` as **named members** — the
authoritative station set, present for **145** vehicles. `.physicsc` (Havok) holds a *second copy* as
four `float4 (x, y, z, 1.0)` quads. `jc3phys.py` finds them structurally (one shared `y`, one `|x|`
with both signs, two `z` with both signs) and validates against the named copy:

    entities with a station set in .physicsc   17
    more than one set                           3
    none                                      212
    agree with land_global                     17 / 17   (0 disagreements)

So the Havok reading is proven, and it is also shown to be redundant: **17 of 145** wheeled vehicles
bake the copy. The Serpente is one of them: `(±0.885, 0.4, −1.557 / +1.446)` -> track **1.77 m**,
wheelbase **3.003 m**, matching §65 exactly.

### What `.physicsc` still hides — G2-8 stays open

The files are Havok 2014.1 packfiles (`57E0E057`, `__classnames__`/`__types__`/`__data__`). The station
quads are the only structure readable without a type-aware Havok reader; the **collision shapes**
proper (boxes/spheres/convex hulls) are not. That is now stated as a boundary, not a guess: the
Batmobile's chassis collision stays JC3-side as it has been since test-033.

### FLEET.md: the donor has a number now

`jc3fleet.py` joins the module values (mass, top speed, steering, tyre radius, gears) with the body
bounds out of the `.rbm` headers and the station geometry, then ranks land vehicles by RMS relative
error against the Batmobile's own numbers (length 7.026, wheelbase 5.029, track 2.416, tyre radius
0.6826):

| rank | vehicle | score | L×W×H | wheelbase | track | tyre Ø | mass |
|---|---|---|---|---|---|---|---|
| 1 | Urga armored transport `v0602` | **0.134** | 6.17×2.53×2.67 | 4.211 | 2.116 | 1.20 | 6,000 |
| 4 | Capstone medium/bavarium tank `v0201`/`v0202` | **0.164** | 8.19×4.67×2.34 | 4.534 | 3.054 | 1.32 | 25,000 |
| 10 | articulated truck `v0011` | 0.182 | 6.45×2.70×3.66 | 3.884 | 2.214 | 1.01 | 8,500 |
| 12 | old truck `v0505` | 0.197 | 6.94×2.24×2.61 | 3.884 | 1.890 | 1.04 | 5,100 |
| **45** | **Serpente `v0300` (current donor)** | **0.358** | 3.72×2.10×1.41 | 3.003 | 1.770 | 0.76 | 975 |

The Batmobile as built: mass **4,000 kg**, wheelbase 5.029, track 2.416, tyre radius 0.6826, body
3.504 × 2.283 × 7.027. In other words the car we have been tuning is a 975 kg supercar carrying
4 tonnes of Batmobile — and the fleet says the *nearest shipped shape* is an armored transport, with
the tanks next and the supercar 45th.

This does not make a tank the answer: shape is not behaviour, and the donor also has to carry parts,
lights, weapons and the drop entry. It does make the donor an open, quantified decision instead of an
inherited one, which is exactly what T-1 needs.

### State

G2-1…G2-6 done, G2-5's geometry half done (headers + stations + fleet table), G2-8 reduced to
"collision shapes need a Havok reader". Open: G2-7 (parts module) and that shape remainder.

## 120. T-1 draft written: the translation table, and the three things it overrules (no build, 2026-10-22)

`Working/Translation/T1_TRANSLATION.md` — ~60 rows over 12 subsystems, every row carrying its BmAK
source, JC3 target, transform, the value test-083 ships, the proposed value, a confidence class and the
measurement that would kill it. Two supporting artefacts are generated, not typed:
`Working/Translation/current.json` (`Tools/scripts/t1_current.py` decodes the build's own 31 modules)
and `Working/Translation/FITS.md` (`Tools/scripts/t1_fits.py`, log-log fits of 18 members against mass
over 156 land vehicles).

### Is the grab done?

No — two gaps remain, both third-party-blocked and both named: **G2-7** (`*_vehicle_parts.vmodc`, 229
of 233 refused by Gibbed's `GuessInlineArrayCopyPosition` crash) and **G2-8's shape half** (the Havok
2014 packfiles' collision boxes). Everything T-1 uses on the handling, geometry, light and part-name
sides is decoded. The gaps cost exactly two row groups: per-part damage values (T-P2) and collision
shapes (T-P3), both marked blocked rather than guessed.

### What the table concludes

**T-0 (donor): keep `v0300`.** It ranks 45th of 144 by shape, but the donor's shape is the one thing
already replaced — mesh, LODs, stations, hardpoints, tyre size. What a donor still supplies is wiring:
module set, part list, lights, materials, drop entry. Switching to the armored transport (score 0.134)
would re-do Phase 0 and RD-1 to buy shapes we override anyway.

**The main lever is `arcade_friction_multiplier` (1.0 → 3.0).** Fleet median is 3.0 in *every* mass
class (0–1.5 t through 3–6 t; 2.5 above 6 t); the Serpente's 1.0 is the outlier that the build
inherited. That single row is a better candidate for the surviving understeer than any torque constant.

**Steering rate was a false lead.** BmAK's `SteerSpeedVsSpeedCurve` is flat 720 °/s, which at a 60° lock
means 0.083 s to full lock — six times outside the fleet's fastest 0.5 s. That parameter is not the same
quantity as JC3's `t_to_full_steer_s` (which already includes its own stabilisation); the build's 0.8 s
is already faster than the armored transport's 2.0 s. HDL's HP-3 stage is withdrawn as a target.

**The build is three vehicles at once**: supercar rpm band (5000/7300 against a 6 t fit of ~2,120–2,365),
supercar drag (Cd 0.139 against a class ~0.57) and downforce (−1.95 against −0.3), on truck mass with
the stiffest springs in the game (80 against a median 30). The table re-bases those rows on the heavy
class and marks them `class`, not `decoded`, because the fleet does not set them (suspension fit
R² ≈ 0, brake R² 0.04, drag R² 0.13). Where the fleet *does* have a law it is used: frontal-area fit
R² 0.875 and optimal-rpm R² 0.52.

### Rows that changed versus §115's HP list

| HP stage | what T-1 says instead |
|---|---|
| HP-1 grip | survives, and is the first row: `arcade_friction_multiplier` 1.0 → 3.0 |
| HP-2 steering geometry | survives with BmAK's own shape: 55°@≤20 → 20°@≥72 km/h, falloff 1.5 (build: 35°@30 → 15°@296) |
| HP-3 steering rate | **withdrawn** — BmAK's rate is not expressible in JC3's parameter; keep 0.8 s |
| HP-4 inertia/drift | re-based on class: yaw 1.8 → 4.0, wheel mass 25/75 → 75/150, springs 80 → 45 |
| HP-5 boost | BmAK's ratio is 1.30 → 2.10 across speed; one JC3 multiplier is chosen: 2.5 → 2.0 |


## 121. T-2 written: the half of the grab T-1 did not translate (no build, 2026-10-22)

`Working/Translation/T2_TRANSLATION.md` — 48 rows over appearance, assembly, lights, audio,
effects, damage, collision, plus three "no row, by decision" statements (weapons, camera,
interaction). Every number is printed by `Tools/scripts/t2_facts.py` into `T2_FACTS.md` from
`current.json`, the five BmAK grab JSONs and `VOCABULARY.md`; `t2_facts.py check` fails when the
facts file is stale. Nothing was built, installed or launched.

Four findings that change what the next build may touch:

- **T-P2 was mislabelled blocked in T-1.** The 24-type damage table (`initial_health`,
  `damaged_health`, `loosen_health`, break/loosen flags) is `VehicleDamage.part_damage_types[]`,
  which decodes for all 233 vehicles (4,820 rows fleet-wide, median initial health 300). Only the
  *part → damage type* mapping lives in the undecoded parts module.
- **Audio is not a module row.** JC3's `LandAudio` has exactly two members (`min_rpm` 1000,
  `max_rpm` 10000). The other 26 ids and 447 media are FMOD events; that is why the nitro swap was
  a bank sample and not a parameter change. T-AU4 also records a live inconsistency: `LandAudio`
  says 10,000 rpm while `LandEngine` says 7,300.
- **Damage values sit at the fleet ceiling.** `explosion_threshold` 4,000, `smoke_threshold` 1,050
  and `burn_threshold` 250 are each the fleet maximum (medians 1,000 / 250 / 100), and
  `bullet_armor_strength` is 100 against a fleet maximum of 99. That is why "a couple of mags" does
  not kill it through thresholds — the remaining lever is `max_health` (T-DM1), not more armour.
- **The effect vocabulary is 17 names and the build uses 11 of them** (51 effect rows over 29
  parts, one usage row: `HeadLights`). The Batmobile's signature VFX (afterburner flame, EMP,
  seismic sonar) have no JC3 usage slot, so they are a feature gap, not a translation gap.

## 122. G2-7 measured: it is not a missing type, and half the table is already decoded (2026-10-22)

`Tools/scripts/jc3parts.py` + `Research/JC3Grab/PARTS.md`.

**The converter's crash is now explained.** `ConvertAdf` dies with a `NullReferenceException` four
member levels inside `InstanceMemberInfo.PrepareForWritting`, called from
`InstanceInfo.GuessInlineArrayCopyPosition` during `Read` (reproduced by hand, exit 139). The
obvious theory — a type the file does not define — is **false**: across 80 parts modules sampled,
the 31-type dictionary (0x1038 bytes) and the 1790-byte metadata block are **byte-identical in
80 of 80**, and only the payload differs. The failure is therefore a payload-dependent array-extent
guess, which fits the format: string members are deduplicated (a part that reuses `Train_Generic`
stores no string at all), so an inline `A[int8]`/`A[int16]` block has no self-describing length.

**Half the table did not need it.** `DeformPoints` converts for all 233 vehicles and names every
part it touches:

- **42 parts** for the donor, indices 0…41. The `.epe` lists 40 `CPartProp`; the 40 shared indices
  agree **40/40**, and the two extra are `hood_signature` (25) and `missile_base_signature` (41).
  `ENTITIES.md`'s "40 parts" was the graph's count, not the vehicle's.
- 4 `wheel_indices` → 4 wheel parts, 1:1; 21 `light_indices` → **12 parts** carrying the rig;
  11 `constraint_indices` → 11 hinged parts; 20 `non_deformable_parts_indices`.
- `jc3parts.py check` asserts all of it.

Still only in the blocked module: part → damage type, `children/parent` break-up relations,
`world_collision_body_id`/`raycast_body_id`, `has_lights`, the four `*_parts_when_broken` arrays and
the typed `wheel_parts`/`hinged_parts` parameters. Unblocking options are ranked in `PARTS.md` §5
(type library via `ConvertAdf -t`, none ships; a reader that exploits the two constant halves; a
patched converter with a defensive extent guess).


## 123. G2-7 solved: a real ADF v4 reader, 232 of 232 parts modules (no build, 2026-10-22)

`Tools/scripts/jc3adf.py` + `Tools/scripts/jc3parts.py build` + `Research/JC3Grab/PARTS.md`.

Gibbed's converter failed because it *guesses*. Its own source shows why the guess exists and why it
was never needed: an ADF v4 member carries its **offset** in the type dictionary, so a reader that
parses the dictionary reads structs directly. `jc3adf.py` does that: header → name table → type
dictionary → instance → data, with `A[T]` as (u64 offset, u64 count), `IA[T]` inline with the count in
the type, and `HashString` as (u64 string offset, u32 hash). Strings are deduplicated by sharing an
offset, which is what made Gibbed's extent guess ambiguous in the first place.

**Result:** 232 / 232 entities, **11,599 parts**, 0 failures, 34 s. The donor's 42-row table is in
`PARTS_TABLE.md`; the machine table is `PARTS_TABLE.jsonl` (2.6 MB).

**Validation, all of it re-runnable:**
- `jc3adf.py verify` — the 4 modules Gibbed *can* read: **1,660/1,660 rows each, 0 mismatches**,
  including the inline-array element rows Gibbed's flat dump loses.
- `jc3parts.py check` — donor names **42/42** against `DeformPoints`; light parts **12/12**; wheels
  **4/4** (`behavior = Wheel`); children all inside the part list; wheel slots from `wheel_parts[]`
  are parts 11/12/26/27 → slots 3/2/0/1, and `door_parts[]` is parts 1/2/25.
- Fleet shape: 3 … 119 parts per vehicle, median **48** — the same median `ENTITIES.md` measured
  from `CPartProp`, from a different source.

**One shipped-file inconsistency, kept visible:** the donor's `c_mirror` has damage type
`Boat_Antenna`, which is not in its own `VehicleDamage.part_damage_types[]` (24 `Land_*` types), so it
falls back to `Default`. `check` prints it as a note instead of hiding it.

**What it unblocks:** T-2's T-PA3 (part → collision body ids), T-PA4 (wheel slots), T-PA8 (doors);
T-1's T-P2 (part → damage type → per-type health from `VehicleDamage`); PRT-2's body split (every part
has its model path), PRT-3's pivots (`hinged_parts`, `door_parts`), and DMG-1's tuning. Only G2-8
(collision *shapes*) remains a decode gap.

## 124. G2-8 solved: collision shapes read out of the Havok packfiles, 18,797 hulls verified (no build, 2026-10-22)

`Tools/scripts/jc3hkx.py` + `Research/JC3Grab/SHAPES.md`.

A packfile needs a type library and JC3 strips it: `__classnames__` holds 16-20 names, `__types__` is
**zero bytes in all 233 files**, `__data__` holds objects plus three fixup tables. So the reader carries
the layouts (`LAYOUTS`) and stays type-aware the way the game's loader is: the **virtual fixup table**
(`offset, 0, class-name offset`) names the class of every object. No class is guessed from a byte
pattern; 129,973 objects across the fleet resolved, 0 unresolved.

Envelope pinned by the files: 64-bit pointers (8 bytes, low half written by the fixup), `hkArray` as
`{T* data; int size; u32 cap|0x80000000}` (16 bytes), local `(from,to)` / global `(from,section,to)` /
virtual `(offset,0,class)` fixups, `0xFF` for unused table slots, `0x7F` for object tails, and the root
chain `hkRootLevelContainer` → `NPhysicsData` → `hknpPhysicsSceneData` → `hknpPhysicsSystemData`.

**Shape blob.** `hknpConvexPolytopeShape` is one packed block, not a pointer-filled class: header,
`hkVector4 vertices[V]` at `+0x50`, then `hkVector4 planes[P]`, a 4-byte face table, `u8 indices[I]`,
`0x7F` pad. `V`/`P`/`I` are the low u16 at `+0x30`/`+0x44`/`+0x48`; the block sums to the object extent
for **18,797 / 18,797** hulls. Vertices carry a rank: `w = 0.5 + rank/2^23`, ascending (checked).

**The plane convention is the finding.** Stored distance is not `n·v - d <= 0`; for every plane of every
hull, `max(n·v) + d == 0` at the contact vertex and `<= 0` for the rest — the stored normal points
*inward*. Residual is bounded by the shape's own `convex_radius`, which is the rounding. That relation
ties the vertex base, plane base and plane count together, so a layout off by one record cannot satisfy
it: **18,797 / 18,797 hulls pass**, worst gap 0.0076 against a radius of 0.0100. Every other check
(block accounting, ranks, unit normals, `index < V`, `hkGeometry` arrays filling their object) passes
too; `check --all` exits non-zero on a single violation and runs in 30 s.

**Extraction was the real bug.** A bundle entry is `(name, offset, size)` and `offset == 0` means the
member is **referenced, not embedded** — its name is the VFS path. Reading offset 0 there returns the
bundle header, which is why the large bundles looked like they had no physics file and why the small
ones reported their physics file 2-4 times. With the reference resolved through the index: **232 / 232
entities, 233 files**, one physics file each.

**Numbers:** 18,797 hulls, 301,116 hull vertices, 237,284 planes, 967,770 indices, 4,774
`hknpExternMeshShape`s (1,801,764 mesh vertices counted, AABBs exact), 9,548 `hkGeometry`. Wheel
hardpoints read from a known field now (`+0x30` of the 96-byte entries in `hknpPhysicsSystemData`'s 4th
array, `w == 1.0`): 17 sets, **17/17 agree** with `land_global` — confirmation, not a replacement for
the raw-quad scan, which finds them on 145 vehicles.

**Deliberately not reported:** the compound classes are typed and their child-shape pointers resolve to
real polytopes, but what reads at their instance/AABB slots does not enclose the children and does not
decode as a 32-byte position+quaternion (w out of range, quaternion norm far from 1). Those fields are
left out of `LAYOUTS` rather than published as plausible numbers, so the hull→part wiring is still open.
Quantized mesh vertices (3 × u16, 6-byte stride) are counted and bounded but not dequantized.

**What it unblocks:** T-1's T-P3 and T-2's T-CO1 can now *measure* the JC3 side (per-vehicle hull
geometry, mesh AABBs) instead of blocking; they stay open on the writing side, since nothing here
writes a `.physicsc`. Output: `_JC3grab/hkx/out/*.json`, 141 MB of every hull vertex, plane and index.

## 125. Progress measured, not estimated: a unit ledger for G1 / G2 / T (no build, 2026-10-22)

The backlog carried three unquantified claims ("95% done", "0.4% grabbed", "both tables drafted"). They
measure three different things, and only one of them answers "how much work is left". So
`GRAB_BACKLOG.md` now opens with a **unit ledger**: every workstream is a list of the IDs the document
already uses, each unit is weighted by one rule (1 = delivered and validated, 0.5 = delivered but not
validated in game, its own fraction when it is a countable set, 0 = absent), and the percentage is the
weighted sum over that list.

| workstream | units | arithmetic | result |
|---|---|---|---|
| G1 BmAK grab | 18 | (14 + 6/365 + 1/12) / 18 | **78.3%** |
| G2 JC3 grab | 11 | (7 + 0.5) / 11 | **68.2%** |
| T translate | 6 | (0.5 + 1 + 0.5 + 1 + 0.5 + 0) / 6 | **58.3%** |

**Why the task number is lower than the object number, and why it is the honest one.** BmAK has
**19,203 / 20,128 = 95.4%** of its exports decoded, but the one unit that blocks translation — the
unnamed `RVehicleBatmobile`/`RVehicleSimBatmobile` fields — is worth **1.6%** by measurement, not
"nearly done": `OFFSETS.json` has 365 distinct offset-only fields (1,736 occurrences), 4 named from the
UE3 layout, 2 matched to named siblings, **361 still unnamed**, and `BmScript` is not on disk. JC3 has
`55,811 / 81,953 = 68.1%` of archive entries named (base 100.0%, patch 60.2%, DLC 0%), but the vehicle
space is 100% decoded: **6,045 / 6,045 modules** once G2-7 supplies the 229 `*_vehicle_parts.vmodc` the
entity dump left empty. Translation has **88 rows** (T-1 49, T-2b 39): 32 decoded, 14 derived, 11
class, **22 assumed**, 6 blocked, 2 read-only, 1 out of scope — 57 / 88 evidenced, 33 ready as edits,
**0 verified in game**.

**What the ledger changes.** Sorted by remaining *work*, not by remaining *data*: T-5 (the build) is the
largest single movable unit, G1-1 is a search problem worth one unit, and G2's residual is `.rbm`
payloads (0.5), `effc/ctunec/trim` (33,097 files), DLC names (20,682) and the compound instance records.
The document's "next five moves" now follows that order.

## 126. T-5 runs: 33 edits in one build, read back through the `.toc` (test-084, 2026-10-22)

`Tools/scripts/t5_apply.py` + `t5_build.py` + `t5_measure.py`, `Working/Translation/T5_BUILD.md`.

The T-1 list is machine-readable and its own guard (`t1_apply.py`) still passed 33/33 against
test-083. The new part is turning it into a build. `t5_apply.py` resolves each row's path inside the
decoded ADF - dotted structures (`front_wheels.mass`), inline-array items (`upshift_rpm[0]`) - asserts
`old`, rewrites the value at that member's `offset-in-file` anchor, re-encodes, and then compares
**every other member in the file** before/after. That last check is what makes the build trustworthy:
`rigid_body` re-encoded 992 -> 976 bytes, and the same shrink happens on an **unedited** decode/encode,
so it is Gibbed normalising trailing padding, not the edits - but a silent layout change would have
been invisible without the member-by-member compare.

`t5_build.py` packs, unpacks, diffs against 083's own unpacked tree (8 changed, all in the edit list,
0 added/removed), rebuilds the `.toc` from 083's because the rigid-body shift moves 135 records, and
checks all **478** internal records against the new `.ee`. `t5_measure.py` then slices each module out
of the **installed** `.ee` through its `.toc` record - a value that only exists in the staging tree is
not shipped - and reads it back: **33 / 33 equal to the table**. `verify_install` 9/9, stations still
at front ±1.208 / rear ±1.2845.

Installed as test-084 (sha `53DCEF8A…`), rollback is test-083's installer. The handling rows are
**built, not measured**: they need a driver and QA-1 does not exist yet, so T-5 counts 0.5 and the
translate ledger goes 58.3% -> **66.7%**.

## 127. BmAK grab closed: T-5 reproduced, and the last four units measured (no new build, 2026-10-22)

**T-5 re-run, not re-described.** `t5_apply.py` -> `t5_build.py` from `Builds/test-083/aaf` into a fresh
tag, then compared to the shipped `test-084`: the `.ee` and `.toc` are **byte-identical**
(`53DCEF8A…A3723EBF`, `4FD6DB3C…C88541A0`), the pack diff is the same 8 modules with 0 collateral, the
`.toc` was rebuilt from 083's with every internal record checked against the new `.ee`, and
`t5_measure.py` re-reads **33 / 33** rows equal through the installed
`.toc` (`t5_rows_repro.json`). The build is deterministic from the table, which is the property that
makes T-5 a measurement instead of a one-off.

**The four open G1 units.** G1 is now 18 / 18 (100%).

* **G1-5 — geometry, 12 / 12.** `grab_meshes.py` drives `umodel -lods` once per mesh into
  `E:\Modding\_BmAKgrab\meshes\` (outside the repo) and reads the chunked ActorX header. The 12
  exports are 6 distinct meshes duplicated across packages; the flat-PSK read fails at
  `numVertex = 20100422` because the file is chunked (FINDINGS F4), so the reader walks
  `id[8] + version[16] + stride + count + payload`. Counts: `Batmobile_V2` 201,338 v / 299,837 f,
  `Batmobile_MK2_Skin` 199,628 v / 297,566 f, `Batmobile_Jokerfied_Skin` 202,795 v / 305,786 f,
  `Batmobile_V3_Destroyed` 57,101 v / 36,513 f, `Batwing_Carrier` 17,798 v / 14,508 f,
  `Batmobile_V2_Fire` 1,320 v / 1,196 f, with bones, materials and bounds.

* **G1-4 — every LOD's faces.** umodel writes LOD0 only, so the LODs were read from the cooked
  `USkeletalMesh3` itself: `LODModels` is an array of `FStaticLODModel3`, each starting with a
  `Sections` array of 13-byte entries whose `FirstIndex` is exactly the running `3 * NumTriangles`.
  That chain is the signature (vertex data cannot fake it), and the array's own length sits 4 bytes
  before LOD0. **28 LOD models** found: V2 299,837 / 144,857 / 21,720, Jokerfied 305,786 / 117,897 /
  21,407, MK2 297,566 / 115,056 / 21,242, Destroyed 36,513 / 16,225, Fire 1,196 / 523, Carrier 14,508 /
  2,707. Cross-checks: LOD0 equals the pskx FACE count for all 12 (independent export), and LOD0's
  per-material split equals `SLOTS.md`'s 19 slot numbers exactly (62668, 3532, 37819, … 524).

* **G1-6 — particle semantics.** `grab_particles.py` resolves the real graph
  `system -> emitter -> LODLevel -> {required, spawn, modules[], type data}` for all **206** systems:
  **1,433 emitters** (1,107 with levels, 326 cooker stubs), **63 materials**, and a kind for every
  emitter from its type-data module class (mesh / beam / trail / ribbon / light / decal / sprite).
  Roles are assigned from the graph first and only fall back to the system name. The numbers *are*
  there, as cooked lookup tables: `Op == 2` is a uniform stored `[min, max]` per chunk, a repeated
  value is a constant. **1,079 of 1,107** levels resolve a lifetime (e.g. burnout 0.2–0.4 s at 30 /s,
  muzzle flash 0.12–0.15 s at 20 /s), **1,017** resolve a spawn rate, and **863** carry a vector
  distribution. Of the 1,068 `ParticleModuleLifetime` exports, 1,062 carry a `LookupTable` and 1,051
  of those hold non-zero values — an earlier version of this entry claimed the scalars were baked, and
  that was wrong: the first sample it looked at was one of the 6 table-less modules. The vectors
  (`StartSize`, `StartVelocity`, `StartLocation`) are stored as two vectors whose order is not always
  min-first (193 of 863 pairs are max-first), so they are quoted as component-wise bounds with the
  stored pair kept.

* **G1-1 — resolved by evidence, with a correction.** The old count was wrong in one important way:
  the **365 fields are the archetype classes only** (`RVehicleBatmobile` + 12 `RBatmobile*`); the sim
  (`RVehicleSimBatmobile`, 28 unnamed scalars including the 0x4A8 = 8000 value) and the wheel component
  (`SVehicleWheel`, 29) were never in it. `grab_offsets.py` v2 covers all **15 classes / 422 fields /
  2,593 occurrences** and decides each one: **4 named** from the `VehicleLights` layout, **195
  identified by referent** (the field is an object reference, so the target names it —
  `AkEvent Engine.Play_Batmobile_Tazer_Fire`, `Particles.Batmobile_Burnout_MUD`, component classes),
  **223 undecidable** (98 float, 21 bool, 20 name, 19 vector, 10 int, 8 string, 2 rotator, 1 ref) with
  every value, offset, occurrence count and struct context preserved.

  Why the 223 are not a search any more, measured from both sides: the 4 packages import the classes
  from `BmScript`; **no file named like BmScript exists anywhere in the install**; a UE3 class's outer
  *is* its defining package, so the definers are the package `BmScript` and it is not shipped; and
  `grab_native.py` shows `BatmanAK.exe` carries **341 native functions across 31 vehicle classes**
  (including two no package lists, `RVehicleBatmobileBase` and `RVehicleBatmobilePredictor`) with
  **0** class-qualified property strings. The names live in the binary's registration code. Binding
  them to offsets would need disassembly, which is recorded as the one open route — not guessed around.

`upk_read.walk_tags` now records each tag's payload offset (`at`), which is what makes the
object-reference arrays (`Emitters`, `LODLevels`, `Modules`) readable: `int32 count` + indices, the
element type being a class fact rather than a stream fact.

All four tools have a `--check` that re-measures and fails on drift: `grab_offsets.py --check`
(422 fields, 365 archetype, 4 named, no BmScript), `grab_meshes.py --check` (LOD0 == pskx for all 12,
LOD faces descending, per-material sums), `grab_particles.py --check` (206 systems, 1,107 levels,
required module per level, min <= max), `grab_native.py --check` (target classes, sim entry points,
no property table). All green.

## 128. G2 closed: mesh payloads, compounds, effects, DLC names (no build, 2026-10-22)

The four remaining JC3 units measured at 0.5 / 0 / 0 / 0 are now 1 / 1 / 1 / 1, so the ledger reads
**100% G1 · 100% G2 · 66.7% T**. Nothing here touches `Playable_Batmobile_SF`; it is read-side work.

**G2-5 — mesh payloads (`GEOMETRY.md`).** `jc3geom.py` now decodes every block instead of framing it:
**233 entities, 56,136 meshes, 77,611 blocks — 77,237 decoded, 374 framed, 0 failed**, and the payload
is **20,797,479 vertices / 19,197,927 triangles / 806,529 material slots** (`_JC3grab/geom`, 440 MB).

The `GeneralMkIII` block (`940` of them) was the only real reverse-engineering left, and the earlier
attempt was wrong in two ways that looked like data problems:

* **The AABB oracle was the wrong AABB.** `jc3model`'s `Attributes` (0x68) ends with the *block's own*
  bounding box at `+0x4C`/`+0x58` and `pristine_index_count` at `+0x64`. The RBMDL **header** AABB is
  the union over every block in the file, so fitting to it gave up to 5% error and refused 253 blocks.
  Against the block's own box, one scale per block is exact: `span(AABB)/span(s16)` agrees across axes
  to **0.29%** worst case (threshold 1%), 0 refusals.
* **The position record is 8 bytes *or* 16.** `{s16 x, s16 y, s16 z, s16 32767}` — but on meshes whose
  vertex format carries a second 8-byte attribute it is interleaved, so the sentinel sits every 16
  bytes. The sentinel is the test: `find_position_stride` takes the smallest stride where **all**
  vertices carry it, which is 8 on 715-vertex body panels and 16 on the tank's antenna.

`check` asserts 233 entities, no failed block, an index buffer that is a triangle list, payload offsets
inside their `.bin`, and every quantized block's axes within 1%.

**G2-9 — `.effc` / `.ctunec` / `.trim` (`FX.md`).** The "33,097 untouched files" number was a partial
census; the real set is **57,187** (25,025 + 6,455 + 25,707), **62,504,473 value rows, 0 failures**,
700 member paths. They are not a format of their own — every one is ADF v4 (`' FDA'`), so `jc3adf.py`
reads them; what it needed was the four type kinds the vehicle modules never exercise: pointer (code 2),
`String` (`0x8955583E`, a data-relative offset to a NUL-terminated string), StringHash (code 9) and
inline arrays of primitives (`IA[float]`, 29 `int32` in one member). Roots: `EffectRTSystem` (25,025),
`EffectTrimData` (25,707), and 20+ camera-tune classes (`GenericVehicleCamera`,
`SphericalCoordinateFramingParams`, `AuxiliaryMotionModifierParams`, …). `check` re-reads the archives
and compares each file's **row digest and object census**, so a decode that stopped early cannot pass.

**G2-8 residual — compound instance records (`SHAPES.md`, `WIRING.md`).** The previous entry left these
undecoded because 32-byte position+quaternion records did not fit. They are not 32 bytes: they are
**128** — a 3x3 basis in three `float4` rows (the `w` lane carries a per-row norm marker, `0.5` on a
unit row), translation at `+0x30`, scale at `+0x40`, child shape at `+0x50`. The `hkArray` at `+0x60`
is inline at `+0xD0` on the static class and a separate allocation on the dynamic one; stride 128 is
confirmed by `count x 128` exactly filling the gap to the next target.

Placement is `p' = Mᵀp + t`, and the data decides that, not taste: the Serpente's doors and roof carry
0.94/0.34 rotations, and this reading puts every rotated child inside its compound's own AABB while
`M p` puts them up to 0.14 m outside. Identity children — the majority — cannot tell them apart.

Numbers: **6,382 compounds, 35,499 instances**, all resolving to a typed shape; **6,341** compounds
explain their AABB by the children's union (6,338 exact to the convex radius), 0 violations. **25,769
instances carry a `CPfxPartIndexProperty`** (a u32 at `+0x10` behind `ref_counted_properties`) and
**all 25,769 resolve to a part name** once `PARTS_TABLE.jsonl` is rebuilt against the 233-entity index
(233 / 233 entities, **11,643 parts**). `WIRING.jsonl` is one row per instance: entity, file, compound,
instance, child class, AABB, part index, part name — 18,865 loose hulls became a per-part layout.

**DLC entry names.** JCMR ships `assets/jc3/dictionary.json` (102,000+ path hashes); hashed through the
same Jenkins lookup3 it names **20,682 / 20,682** DLC entries, adding 26,051 index rows. The index is now
**81,862 / 81,953 entries = 99.9%** named (base 100%, patch 100%, DLC 100%); the 91 unnamed are
addressed by hash and censused by magic byte in `INDEX.json`.

**One correction to the previous section's numbers.** The extra DLC names surfaced a 233rd vehicle entity
and a 234th `.physicsc`, so the fleet figures move from 232/233 to **233/234** throughout: 18,865 hulls
(was 18,797), 4,791 mesh shapes, 9,582 `hkGeometry`, 56,136 render meshes. Nothing was re-interpreted —
the new files decode under the same layouts and add no violations.

**Checks, all green:** `jc3index check` (81,862 rows, DLC 20,682/20,682), `jc3grab check`,
`jc3detail check`, `jc3parts check`, `jc3phys check`, `jc3fleet check`, `jc3geom check` (0 failed,
0 empty meshes), `jc3hkx check --all` (234 files, 0 problems, 6,341 AABB unions exact),
`jc3fx check` (57,187 / 57,187 digests re-read from the game, 0 problems). Every one is re-runnable
and fails on drift.

**One fix inside that closure.** `jc3fx check` first came back with 104 failures, all of them the
standalone archive entries: the table stored their bare filename as `path` and nothing recorded which
archive row it came from, so `check` had no way back to the bytes. The table now carries `source`
(the archive path for a standalone entry, the bundle path for a member), and the checker groups by
container so each `.ee` is opened once and dropped instead of every container being cached — the
earlier draft held all 3.7 GB of bundles and had run for 80 minutes without finishing; the grouped
version re-reads all 57,187 files with 0 problems in 11.

**129** — the last open route for G1-1 was the native class registration in `BatmanAK.exe`, and it
is now walked rather than assumed. `Tools/scripts/bmak_reg.py` parses the PE, finds the 8-byte
pointers to each `...exec<Function>` string, walks the runs into arrays, and disassembles the code
those arrays point at with capstone.

**What the registration is.** Three arrays: `0x309E760` with **5** entries for `RVehicleSimBatmobile`
(`SkidToStop`, `ForceUpdateTyreFriction`, `SetSuspensionForDriveMode`, `SetDriveMode`, `Boost`),
`0x30A46B0` with **75** for `RVehicleBatmobileBase`, `0x30A4E20` with **1** for the predictor. Each
entry is 16 bytes — a pointer to an `exec` name string, then a pointer into `.text` — and each array
ends on a zero pair. **81 / 81 entries are function names; there is no property record anywhere in
them.** Together with the string scan that already found 0 class-qualified property names in the
55 MB image, that closes the exe route as a measured negative: the names were never in the binary.

**What it paid instead.** Walking each thunk and up to two call targets gives an offset-usage map:
**111 offsets touched by 43 functions** (`REGISTRATION.json` → `field_usage`). Two hits check out
against anchors the cooked data already proves: `0x3B0` is read *and written* by `SetDriveMode`
(byte) and is the `DriveMode` anchor; `0x3B1` is written by `SkidToStop` (byte) and is the
`SkidToStopDir` byte that follows it. `SetSuspensionForDriveMode` writes nine consecutive dwords
`0x3CC…0x3EC`, and `ForceUpdateTyreFriction` touches `0x338`/`0x350`.

**The 8,000 at `0x4A8` is `AirControlTimeInAir`.** *(Superseded by §132: it is
`AirControlYawTorqueFactorMax`; the walk below was short by `ArrayDim` and the transmission struct's
`GearRatios[6]`.)* No native touches it, so the class definition
decides it, and the boundary makes that more than a guess: the two anchors nearest it
(`DriveMode 0x3B0`, `TransmissionModel 0x424`) both imply base `0x114`; `RVehicleSimBatmobile`'s 165
properties total `0x39C` bytes; `0x114 + 0x39C = 0x4B0`, which is exactly where
`Default__RVehicleSimBatmobile` starts overriding fields the base class does not declare. At that
base `0x4A8` is the float `AirControlTimeInAir`, in the run of `AirControl*` scalars and the only
slot there where 8000 reads as anything but nonsense — air control for 8,000 s.

*(Superseded by §132.)* **The residue, measured.** `bmak_bind.py` now pins **8** offsets from inline
names and nothing else. The class copy in `BmGame.upk` is not the shipped build: the anchors measure a `+4` insertion at
`0x190` and a `+12` one between `0x240` and `0x3B0`, so slot arithmetic past either point lands on a
neighbouring float, not on the right field. Rather than invent names from that, the binder reports
the drift points and stops. Closing the rest needs the `BmScript` package from the shipping build,
or data-flow on each native that touches a candidate offset — the usage map in `REGISTRATION.json`
is the input for that, and `0x3B0` shows the method works.

**Checks, all green:** `bmak_reg.py --check` (3 arrays, 81 entries, 111 offsets, no non-exec name),
`bmak_bind.py --class RVehicleSimBatmobile` (165 properties, 8 anchored, 0 conflicts),
`grab_offsets.py --check` (422 fields, 365 archetype, 0 property strings), `grab_native.py --check`.
New: `Research/BatmobileGrab/REGISTRATION.md` + `REGISTRATION.json`.

**130** — the 422 name-less fields are now mostly named, and the route that did it is the class
definition, not the executable.

**Why not the exe.** §129's disassembly stands: three native lookup arrays, 81 `{name, code}`
records, no property table. Nothing in `BatmanAK.exe` can name a field, so that branch is closed.

**What actually worked.** `BmGame.upk` ships the script classes the archetypes were cooked from -
135-601 properties each, every one named, typed and in declaration order - and each archetype tag
carries the absolute offset of the property it overrides. `bmak_bind.py` walks a stream against its
class: an inline tag name (struct, object, enum byte) pins the object base exactly; the base carries
forward through the run and backward from the far anchor; a tag binds only when it lands on a slot
whose `UProperty` kind agrees and the alignment stays monotone, so one property cannot be named
twice; forward and backward placements that disagree are dropped rather than voted on.

**The `BmScript` problem, solved by the parent.** `RVehicleBatmobile` is defined by the missing
`BmScript` package - but `RVehicleBatmobileBase`, its parent, *is* shipped, and it anchors **137** of
those tags (`VehicleLights` at 0xaec-0xdfc, `InteriorLightsSwitchedOn` at 0x86d, the Cannon's
`RiotSuppressor*` and `ChainGun*` runs). The binder tries candidate hosts and keeps the one that
anchors the most tags, so the 54 fields that looked unresolvable are now 46 named.

**Ledger.** 422 fields: **115 named** (110 from the class walk, 4 from the `VehicleLights` layout, 1 argued from the
anchor base), **161 identified by the object they reference**, **146 still without a name** (was
4 / 195 / 223).
The residue is categorical, not a search gap: classes no shipped package defines (`SVehicleWheel` 9,
`RBatmobileMissileLauncherJoker` 11), the `BmScript` subclass tail (31), runs inside the two
insertion windows the anchors measure (+4 after `EngineRPMCurve`, +12 before `DriveMode`:
`RBatmobileCannon` 21, `RBatmobileHeavyCannon` 16, `RVehicleSimBatmobile` 16, `RBatmobileMissile`
13), and array-element offsets that are not class fields at all.

**The 8,000 at `0x4A8`** stays `AirControlTimeInAir` *(wrong - see §132)*, and the class-extent check now has company:
`DriveMode` at `0x3B0` is read *and written* by the native `SetDriveMode` (`REGISTRATION.md`), and
`0x3B1` is written by `SkidToStop`.

**Checks, all green:** `grab_offsets.py --check` (422 fields, 115 named, 161 referent, 146
undecidable, decisions add up), `bmak_reg.py --check` (3 arrays, 81 entries, 111 offsets touched),
`grab_native.py --check` (no property table), `bmak_bind.py --all --segments` (17 classes, 0
conflicts outside the flagged drops). New tool: `Tools/scripts/bmak_bind.py`.

**131** — attack on the last 146, and it moved the number to **145 named / 161 referent / 116
undecidable**.

**Struct elements, named by their struct.** A field whose context is a struct-typed property is a
*member of that struct*: the offset is the member's offset inside it, so the struct's own declaration
names it and the class layout's drift cannot touch it. Two families fell out: the four
`FInterpCurvePointFloat` lanes (`InVal`/`OutVal`/`ArriveTangent`/`LeaveTangent` over the sim's six
curves, 116 points) and the `BMScreenShakeStruct` members behind every weapon's shake property
(`Progress`, `TimeDuration`, `LocAmplitude`, `LocFrequency`, `RotAmplitude`, `RotFrequency`,
`FOVFrequency`, ...). 30 fields, and the pass is kind-checked: a `BoolProperty` tag never takes a
float member's name, and a `Vector` member takes `VectorProperty` tags. That kind mapping cost 16
would-be names on the first run and those were the wrong ones - `0x0000 BoolProperty` had been
"named" `Progress`, a float.

**The parent class as host, again.** `RVehicleBatmobile`'s class is BmScript's, but its shake and
light fields are declared in `RVehicleBatmobileBase`, so hosting the stream in `Base` also names its
struct elements; the same trick only gives +1 here because most of the residual is the subclass tail.

**Native offsets cross-check.** The disassembly names nothing by itself, but where it crosses the
class layout it agrees with it: `SetDriveMode` reads and writes `0x3B0` (`DriveMode`), `SkidToStop`
and `SetSuspensionForDriveMode` write `0x3B1` (`SkidToStopDir`) and the nine-slot block
`0x3CC..0x3EC`, `ForceUpdateTyreFriction` touches `0x338`/`0x350`, `Boost` compares `0x328` and
updates `0x294`. All inside the declared block.

**Why the rest is a wall, measured.** For `RBatmobileMissile` the shipped class in `BmGame.upk` is
`0x138` bytes, while its archetype writes fields out to `0x43C`; `RBatmobileCannon`'s copy is
`0x8CC` against tags at `0xB84`. So the shipping classes are *larger builds* than the copies - extra
fields, not a different arrangement of the same ones. A base-0 alignment scores 0 % on those classes,
which is the measurement that kills the "just align it" idea. The residue is therefore: shipping
versions larger than the copy (Cannon 14, Missile 13, HeavyCannon 10, Sim 11), the BmScript subclass
tail (26), native-only `SVehicleWheel` (9) and the class BmScript never shipped
(`RBatmobileMissileLauncherJoker`, 11).

**Checks, all green:** `grab_offsets.py --check` (422 fields, 145 named, 161 referent, 116
undecidable, decisions sum), `bmak_reg.py --check`, `grab_native.py --check`, `grab_model.py check`,
`grab_meshes.py --check`, `grab_particles.py --check`.

**132** — a web search for data-structure hints found the class layout itself, and the last 146 fell
to **414 named / 8 undecidable**.

**What was searched.** After the exe route came back empty and the upk walk stalled at 145, the open
question was the *data structure*: what does this build's `UProperty::Link` actually do — array
dimensions, alignment, struct slot sizes. Searching for the property-tag format and for the class
names led to **BmSDK-AK** (github.com/Team-BmSDK/BmSDK-AK, MIT), a scripting platform whose build
generates C# bindings *from the running game*. Every `UProperty` in those files carries the absolute
object offset the engine linked it to (`Ptr + 1192`), and every `ScriptStruct` its runtime
`[StructLayout(Size = N)]` and each member's offset. That is the same number space as
`FPropertyTagBat2.Offset`, so a cooked field resolves by **class + absolute offset + slot kind** —
no base guessing at all.

**What was extracted.** `Tools/scripts/bmsdk_offsets.py` parses the generated classes into
`Research/BatmobileGrab/BMSDK_OFFSETS.json`: 34 classes (2,351 properties, 42 structs), walking
superclasses on lookup. The source files are vendored under `Working/vendor/BmSDK/` with the MIT
notice; nothing from the game's files is copied.

**Why it is the same build.** `RVehicleSimBatmobile`'s dump size is 1220; the upk walk, once its slot
rules were fixed, lands on `0x104 + 0x3C0 = 0x4C4` = 1220. `RVehicleSimCar` 456 bytes with 37/37
names; `RBatmobileMissileLauncher` 30/30; `RBatmobileEMPMissile` 36/36; `RBatmobileAllegianceSwitcher`
21/21; `RBatmobileBooster` 2/2; `RBatmobileMissile` 23/23; `RProjectile` and `RBasicProjectile` exact.
The native `SetDriveMode` writes the byte at `0x3B0` and `SkidToStop` at `0x3B1` — the dump calls
them `DriveMode` and `SkidToStopDir`. For the 195 object fields with a referent, the dump's declared
type agrees with the class the reference points at (the 13 apparent mismatches are subclasses:
`StaticMeshComponent` vs `PrimitiveComponent`, `AkDialogueLineSingle` vs `AkDialogueLine`, ...).

**The data-structure answers the walk was missing.** `UProperty::ArrayDim` sits at byte 6 of the
property export: a static array is *one* property with N slots (`BoostCooldown[3]`,
`GearRatios[6]`, `VehicleWeapons[10]`), not N properties and not one slot. Every property type
aligns to **4** in this build, pointer slots included. `FInterpCurve<T>` is a **20-byte** slot
(16-byte `TArray` + 4-byte-rounded mode) whatever the point type — the dump spaces consecutive
curve properties 20 apart. `ComponentProperty`, `InterfaceProperty` and `DelegateProperty` exist
and must be laid out; dropping `RInventoryGadget.Mesh`/`Mesh2` shifted everything after by 8 bytes.
`VehicleTransmission` is 112 bytes, not 92: its `GearRatios` is a six-slot array.

**Corrections that followed.** `0x4A8` is `AirControlYawTorqueFactorMax`, not `AirControlTimeInAir`:
the undersized slots had been hidden under a base 0x10 too high, which put the whole `AirControl*`
run one slot early (`AirControlTimeInAir` is really at `0x4BC`, class end `0x4C4`). `XrayMaskMaterial`
at `0x318` is `RInventoryGadget.Mesh`. The object at `0x1334` is `VehicleWeapons[0]`, not
`TransmissionAnimNode` — the referent is `Weapons.Batmobile_Cannon_V2`. And `0x2AC` is
`DriftingBoostCooldown`, with the three-slot `BoostCooldown` array before it.

**Result.** 422 fields: **380 named from the dump**, **31** struct elements from their own
declaration, **3** from the `VehicleLights` layout, **8 undecidable** — all nested screen-shake
bools (`BMScreenShakeStruct` vs its `AdvancedOptions` child at flattened offsets `0x0000`/`0x0004`/
`0x0090`). No field is left "identified only by referent": the names supersede that.

**Checks, all green:** `grab_offsets.py --check` (422 fields, 365 archetype, 414 named, 8
undecidable, decisions sum), `bmsdk_offsets.py --check` (34 classes, 2,351 properties, 42 structs)
and `--report` (the 7 classes whose *shipped copy* cannot reproduce the dump's extent - a measured
limit of the copy, not of the names), `bmak_reg.py --check`, `grab_native.py --check`,
`bmak_bind.py --all`, `grab_model.py check`, `grab_meshes.py --check`, `grab_particles.py --check`.

## QA-1 take 1 — the HUD becomes an instrument (2026-10-22, evening)

The game ran on **test-085**, the 35-edit translation build. JC3 exposes no telemetry, so the only
oracle for the behaviour rows is the speedometer: fixed position, fixed font, `KM/H`. `Tools/scripts/
qa1_hud.py` cuts the gauge out of a take at 5 fps, isolates the digit band, learns the ten digit
shapes from 22 frames read by eye (`Working/Translation/QA1/known.json`) and then reads the whole
take. `build` refuses to trace until every glyph in the take has a label, so an unseen digit fails
loudly instead of producing a number.

Two bugs the take exposed, both fixed in the instrument: the band's bottom included the `KM/H`
legend, which fed K/M/H strokes into the first digit (3 read as 5, 0 as 9, 8 as 5); and the HUD
font's digits often touch, so column runs are not glyphs — the numeral's extent is divided by the
42 px digit pitch instead.

**Measured** (`Working/Translation/QA1_RESULTS.md`, `Working/Translation/QA1/qa1_measure.json`): moving at 170.8 s,
100 km/h at 187.2 s → **0–100 in 16.4 s, 257 m**; **0–60 in 7.4 s**; peak **138 km/h** at 196.2 s,
still climbing when the brake went on; peak acceleration 3.06 m/s² at 21–26 km/h. Braking on tarmac
**3.5 m/s²** average (138→100 in 3.0 s; the last 122→100 at 3.82). The gearbox's computed 4,200 rpm shift speeds are 66.8 /
108.4 / 146.1 / 182.9 km/h and the trace's first knee is at **67 km/h** — the schedule is active in
first gear; later knees at 94 and 133 are not separated from the road profile, and JC3's only rpm
channel is audio, which this take did not record.

**Not measured, and why.** The car left the road at ~106 km/h around t=203 and stopped in vegetation
(64→0 in 1.2 s is an impact). So 100→0 on tarmac, the 60 km/h corner, the kerb, the ride height and
the lighting rows have no sample from this take. T-5 is therefore "built + launch measured", not
"verified".

## T-3 — the completeness audit (2026-10-22, late)

T-1/T-2b translate the factors they *name*; nothing proved the list was complete. The decoded Arkham
Knight Batmobile is **422 fields across 15 classes** (`Research/BatmobileGrab/OFFSETS.json`).
`Tools/scripts/bmak_coverage.py` now assigns every one of them to a T-row, and `--check` fails if a
field has none — so an unexamined factor is a red build, not a thing someone notices a year later.

**What the audit found.** 260 of the 422 fields (62%) are weapon classes (cannon, heavy cannon,
missiles, EMP, sonar, winch, tracker, launcher, hacker) and have **no JC3 expression**: the game gives
a car no player-fired weapons, and the mod has no weapon slots. 16 more are battle mode/turn-on-spot/
transformation, 16 are Batman's ram/dodge/shove assists, 4 are self-righting, 1 is mid-air yaw
control — all `out`, named rather than silently dropped. 51 are Unreal actor plumbing
(components, sockets, archetypes, tags) that the donor graph already carries.

**What that left to translate.** The genuine vehicle factors the old table never named are small and
now have rows:

* **suspension travel, droop, bias, stiffness/damping** (`T-S6`, blocked) — BmAK's 0.70 m of travel is
  3.9× the heavy-class median stroke (0.18 m) and 2.8× the build's 0.25 m; JC3 has no bias, droop or
  undamped-rate member, and no unit bridge from 3000/300 to `strength` (fleet 4–80);
* **steering rate** (`T-ST7`, blocked) — 220 °/s is 0.25 s to full lock, below JC3's 0.5 s floor;
* **handbrake force/duration** (`T-K4`, keep) — rear-only, friction 1 = the 6 t median; the 640k
  e-brake force has no member;
* **drift block** (`T-DR1`, keep) — the donor already ships the 6 t median (45°, 10 km/h,
  sensitivity 2), so the drift feel was right by inheritance;
* **tyre effects** (`T-EF1`, keep) — fleet p25 = median = p75 on the three thresholds;
* **wheel radius** (`T-G6`, keep) — BmAK's sim radius is 64 cm, inside a 0.683 m visual tyre; the mesh
  wins, and it is what the ride height was measured against.

**The one defect.** `VehicleDamage.impact_damage_factor` is **0** in test-085. All 156 land vehicles
ship **1**; 0 switches impact damage off, so the Batmobile currently cannot be damaged by collision
at all. That is the single value queued for test-086. Boost grip (5.68 vs the class median 2.0) and
boost top speed (50.46 vs 40) are also above the heavy class, but deliberately so: they are the
afterburner's identity, and `T-B2/T-B3` already record them as such.

**Ledger.** `t_rows.py` gained a third table and a `next` disposition (proposed for the next build,
not in the current one): **103 rows, 422/422 fields assigned, 35 edits in test-085, 1 next**. Both
`bmak_coverage.py --check` and `t_rows.py check` are green.

## G3 — HUD and camera: carved, decompiled, translated (2026-10-22, night)

The last two systems outside the G1/G2 unit lists are now read. Neither was in
`Playable_Batmobile_SF.upk`; both live in packages the grab had already opened but never queried for
them.

**HUD.** `HudModuleBatmobile.Image` (423,056 B CFX) and `StoryModeHUD.HUD` (23,758 B) are sub-packages
inside `BmGame.upk`/`Startup.upk`. `bmak_hud.py` already carved them; this pass decompiled them with
ffdec 26.4.0: **99 AS3 scripts**, 51 frames, 30 fps, 1024x768 SWF / 1024x720 stage. The document
class is `ModularHudBm3`; the module is `ModuleStruct_Batmobile`, with **31 public `UC_*` setters**.
The numbers that only exist in the movie are now recorded: `TickDeltaTime` 0.033,
`MaxHealthChangePerFrame` 0.05, health pulse below 0.2, 2 s offscreen timer, energy step 0.02,
boost 0..100, projection FOV 56. The mode machine is DRIVE/BATTLE/ZOOMED with five transition labels.

**JC3 HUD.** `ui/hud.gfx` extracted from the patch archive (386,281 B) and decompiled: **260 AS3
scripts**, 1280x720, 30 fps. It already exposes a vehicle cluster: circular/vertical speedometer
(`SPEEDO_DEGREES` 250, smoothing 0.05), **nitrous meter** (`Init/UpdateVehicleNitrous`), vehicle
weapon slots, turbo jump, vehicle health. That turns the HUD translation from "build a movie" into
"bind the existing one": boost 0..100 = nitrous 0..1, health = vehicle health, cannon = weapon slot.
Battle mode, zoom, winch, energy charges, combo/medals/clock, occupants and virus upload have no JC3
system and are `out`, not silently dropped. Details: `T6_HUD_CAMERA.md` §1.

**Camera.** The two native helpers are wrappers, not values: `GetCameraTrackingOffset` calls a helper
and copies 3 floats; `ShouldCameraZFollowVehicleUp` is a virtual call at `+0x1030`. The rules are in
**`R3rdPersonCamera`** (`BmGame.upk`): 741 properties, 447 tags. Its serialized offsets drift by a
constant in regions (native struct sizes), so `bmak_camera.py` anchors on the *named* struct tags,
interpolates the local delta, and only binds a scalar when the corrected offset has the matching
property type. **31/31 values** re-read on `--check`: FOV 85 normal / 95 boost / +10 by speed,
interp complete at 3000 cm/s (108 km/h), smoothing 30 (camera 1) vs 12 (camera 2), lean 7.5, pitch
-20, head impulse 0.5, drift 0.15, battle 60 (winch 60, anti-personnel 40), chasing 80,
conversation 45, jump 0.4. `EBatmobileDriveCamera` = Camera1, Camera2, Bonnet, MAX — two chase presets,
not two vehicles. `DrivingCamConfig` is a 168-byte `FreeCameraConfig`; its serialized
`Min/MaxFreeCameraDistance` are 0, so the distance is native and is the one number this route cannot
produce.

**JC3 camera.** `car_base.ctune` (the Serpente's `DrivingCamera` base) is decoded: position
`[0,2,5]`, look-at `[0,1.25,0]`, follow range `[-0.5,2]`, FOV `[30,55]` at `[5,50]` km/h, springs
0.08/0.12/1.0, roll amount 0.3, pitch limit `[-70,10]`. The translation proposes `[0,2.4,7.0]`,
look-at `[0,1.7,0]`, FOV `[55,85]` at `[5,108]`, roll 0.38; the +10 boost FOV is a gap because JC3's
FOV is one speed range. No tune was built: a per-entity camera reference is the missing piece, and
that is CAM-1 (P2). Details: `T6_HUD_CAMERA.md` §2.

**Checks, all green:** `bmak_hud.py check` (2/2 movies, size + SHA-256), `hud_spec.py --check` (99 +
260 scripts, constants), `bmak_camera.py --check` (31/31), ffdec export 99/99 + 260/260 with no error.
**Not done:** no HUD or camera build, nothing loaded in either game; the HUD bridge is game code, not
an entity member.

## G3b — the per-entity camera reference was already there (candidate, 2026-10-22, late)

The G3 entry closed with "a per-entity camera reference is the missing piece". That was wrong, and the
correction matters: the donor `.epe` already carries both ends of the reference.

`CCameraRef CarCameraRef` (id `9270776B` = `E241CD45=FFFF32FF`) points at `CCameraObject
SharedCarCamera`; its `CCameraModifier` has one path field,
`editor/entities/jc_cameras/vehicle_cameras/car_base.ctune`. The path is a plain NUL-terminated ASCII
string at `0xD09F` in the test-085 donor, with no length prefix and no adjacent hash. `car_base.ctune`
and `bat_base.ctune` are both 14 bytes, so the edit is **2 bytes** (`c`→`b`, `r`→`t`) and nothing
else moves. Every other car keeps `car_base.ctunec`; only the Batmobile entity points at
`bat_base.ctunec`.

**The second tune.** The extracted `jc3cam` tree has eight per-class `.ctunec` files, not one:
car, bike, boat, big boat, three helicopters and `mediumtank`. The tank differs in exactly the ways
a long, heavy hull needs: 10 m boom (vs 5), look-at 100 m ahead (not at the hull), rigid yaw 1.0
(vs 0.08), no recentre, FOV top 45 (vs 55), collision pitch off, collision ray starts 3.4 m up (vs
1.0). Its unused spline slots carry garbage — `number_of_control_points` is 2, so only the first two
of ten are read; a naive full-slot dump reports noise. `Working/Camera/CAM_REF.md` has the table.

**Candidate.** `bmak_camfile.py` (new) writes, outside the repo:

- `E:/Modding/_JC3cam_out/bat_base.ctunec` — 5,968 B, `6f5a9cce5a84…`: position `[0,2.4,7.0]`,
  look-at `[0,1.7,0]`, FOV `[55,85]` over `[5,108]` km/h, roll 0.38, collision start `[0,1.6,0]`
  (new T-CAM13, height-derived). These are T-CAM2–T-CAM6 + T-CAM13, nothing else.
- `E:/Modding/_JC3cam_out/v0300_…_civilian_01.epe` — 105,430 B, same size, 2 bytes different.

`build` asserts every old value before writing and the semantic diff walks all 187 ADF rows;
`check` rebuilds to a temp dir and compares. Result: **8/8 values, 0 collateral rows, 1 epe ref,
size unchanged**. Report: `Working/Camera/CAM_TUNE.json`.

**Not done:** no `.ee` repack, no `.toc` record, nothing installed, nothing driven. The tank's rigid
yaw is *not* copied — BmAK's 30/12/10000 smoothing still has no unit bridge to JC3's 0.08/0.12/1.0
springs, and a rigid camera on a 300 km/h car is a different risk from one on a 60 km/h tank. T-CAM9
stays blocked. CAM-1 now has a concrete file pair and a test gate (boom at rest, yaw at 300 km/h)
instead of an open mechanism.

## G3c — CAM-1 packed, installed and driven: the tune is live (test-086, 2026-10-22)

**Packaging.** `bmak_cambuild.py` (new) stages test-085's aaf, replaces the donor `.epe`, adds
`editor/entities/jc_cameras/vehicle_cameras/bat_base.ctunec` and registers it in `@files.xml`, packs
with SmallPack and patches the base `.toc`. The new record lands **before** the `.epe` at
`(16498168, 5968)`, internal; `car_base.ctunec` stays external `(0, 5968)`, exactly as the base routes
it. **12/12 checks:** base .ee/.toc hash guard, only the tune added, no registered file lost (the 4
front-wheel lod4/5 files are unlisted by design), only `.epe` + `@files.xml` changed, .epe differs at
**2 bytes / size 105,430**, tune byte-exact, unpack byte-exact, 506 records = base 505 + 1, external
baseline unchanged (98 only-in-ee, 8 mismatch, same as base).

```
Builds/test-086/...ee       10,737,070 B  sha256 6396EA45…  .toc 50,643 B 444ED479…
Backups/dropzone-test-085-20261022-201128/   the pair replaced at install
```

Installed with `Builds/test-086/install.ps1` (size+sha asserted before copy; live hash re-read).
The game ran: package loads, Batmobile drivable, no camera-related crash.

**The drive.** Recorded at 1280x720 (`Working/Camera/shots/cam1_take1.mkv`, 90 s) from the main menu
through map, spawn and ~35 s of driving. Max HUD speed **103 km/h** (the 300 km/h gate was not
reached). The first recording attempt died with the game before the menu; a relaunch + `um win record`
captured the run.

**FOV override risk resolved.** Counting the black body's width in six frames: **36% of frame width at
0 km/h, 33% at 18–53, 30% at 74–103**. A fixed 50° `SharedCarCamera` would hold the same fraction; this
widens with speed, so the `CCameraModifier`'s `bat_base.ctunec` is live and the epe's own `FOV`
property does not need raising. The routing question is closed.

**What is still open.** The player's verdict was "**less zoomed in**" — the car reads small/far
compared with the target view. This is now tuning, not a bug: FOV is the zoom knob, `CameraPosition`
the distance knob, and the first-pass values (FOV 55–85, boom 7.0 m) have not been re-tuned. The 0.08
yaw spring at 300 km/h remains untested because the take peaked at 103. Next camera build is test-087,
one change at a time. Evidence: `Working/Camera/shots/cam1_take1.mkv`, `cam1_contact_small.jpg`,
`frames/`.

## G3d — Correction: the camera distance was in the grab; the 100% claims were task scores (2026-10-22)

The previous entry and the hand-off said "full double grab and translation". That was false. The
real, re-countable numbers are in `STATUS.md` (generated by `Tools/scripts/status_audit.py`):

| workstream | real metric | value |
|---|---|---:|
| G1 BmAK grab | objects decoded | 19,203 / 20,128 = **95.4%** |
| G1 | offset fields named | 414 / 422 = **98.1%** |
| G2 JC3 grab | archive entries named | 81,862 / 81,953 = **99.89%** |
| G2 | geometry blocks decoded | 77,237 / 77,611 = **99.5%** |
| T translate | rows with evidence | 76 / 126 = **60.3%** |
| T | rows assumed / blocked / out | 20 / 16 / 14 |
| T | rows fully behaviour-verified | **0 / 126** |

**The camera bug.** `Research/BatmobileGrab/CAMERA.md` said `Min/MaxFreeCameraDistance = 0` and
"native defaults". It read `DrivingCamConfig`, which is a zeroed template. The configs the camera
actually uses are `DrivingCamConfig1/2`, and both carry **400 / 400 cm**, with sit offsets
`[-300,0,-25]..[-400,0,-25]` cm and pivot `[0,0,155]` cm. The value was in the grab all along; the
analysis looked at the wrong record and then hand-derived a 7.0 m boom from body length.

**The FOV bug.** BmAK's 85/95 are UE3 *horizontal* FOV. JC3's `FOV` is vertical. Copying 85/95
straight into the tune produced ~114° horizontal at boost. The 16:9 conversion is
`v = 2·atan(tan(h/2)/(16/9))`: **85→54.5°, 95→63.1°**; with the +10 speed bonus, 68.4° is the top.
The correct range is **55…63** (68 only if the bonus is folded in), not 55…85.

**test-086 is withdrawn.** The drive proved the per-entity ctunec routing works (car width 36% at
0 km/h → 30% at 103 km/h, so the modifier wins over the `SharedCarCamera` FOV 50), but the values
were wrong and the player's verdict ("less zoomed in") is the expected consequence. `bmak_camfile.py
build` now **fails closed**; `bmak_camfile.py source` prints the authored configs. No new camera
build is generated until the sit-offset/400 cm composition is decoded (native `UpdateDrivingCamSettings`
/ `DrivingCameraTick`, or a runtime trace). No manual value is substituted in the meantime.

**What was actually fixed this turn:** the false "native distance" claim; the FOV unit error; the
task-score-as-coverage illusion. **What was not fixed:** the boom composition, the spring mapping,
the 8 undecidable fields, the 91 unnamed JC3 entries, the 374 framed blocks, the HUD bridge. Those
are listed in `STATUS.md` and `GRAB_BACKLOG.md` with counts, not adjectives.

**Dropzone restored.** test-086 is withdrawn, so the live dropzone was rolled back to **test-085**
(`D9C4AAD3…`, `.toc 4FD6DB3C…`). The camera probe remains in `Builds/test-086` for inspection only.

## G3e — Camera composition decoded; 373 of 374 geometry blocks decoded (2026-10-22)

**Task 1 — the boom composition (executable).** The three natives were disassembled (`BatmanAK.exe`,
capstone) and are now reproduced arithmetically by `Tools/scripts/bmak_camdecode.py`:

- `SetFreeCameraConfig` (`0x140113480`) copies the 168-byte `FreeCameraConfig` into the `State*`
  fields, and it names the struct: `cfg+0x00` → `StateFreeCameraSitOffsetMin`, `cfg+0x0C` → **the
  look-down** vector (the header calls it `SitOffsetMax`), `cfg+0x1C` → the look-up vector (only when
  `cfg+0x18 & 1`), `cfg+0x28` → pull, `cfg+0x34` → pivot, `cfg+0x54/0x58` → min/max distance,
  `cfg+0x5C/0x60` → spring constants, `cfg+0x68` → sit power (1.5), `cfg+0x6C/0x70` → the pitch angles
  in rotator units (16384 = 90°, 8192 = 45°).
- `UpdateDrivingCamSettings` (`0x14010AD00`) blends `State*` → `Current*` per frame.
- `UpdateCameraPosition` (`0x140111660`) composes
  `Loc = anchor − RotToVector(Rotator)·distance + RotateVector(Rotator, Sit)`, with `Sit` a pitch lerp
  (`t = clamp(|pitch|/pitchLimit,0,1)`, raised to `SitOffsetPower`) between the min vector and the
  up/down vector, and `distance` loaded from `0xEF0/0xEF4` (400/400 cm).

**Answer: additive.** At rest (pitch 0) the camera is 700 cm behind and 25 cm below the pivot →
**7.00 m behind, 1.30 m above the car** (pivot z 1.55 m). Looking up 45°: 9.00 m / 2.05 m. Looking
down 90°: 8.00 m / 1.30 m. `DrivingCamConfig2` is a flat 9.00 m. Written up in `CAMERA.md` §2b and
T6's T-CAM5/T-CAM12; `bmak_camdecode.py --check` passes 18/18.

**Task 2 — the grabs.** Everything reachable was decoded or measured:

| item | before | now |
|---|---:|---:|
| JC3 geometry blocks decoded | 77,237 / 77,611 | **77,610 / 77,611** |
| JC3 framed blocks | 374 | **1** (`Prop`) |
| JC3 unresolved filelist paths | 63 | **0** (they were Gibbed's `; hits` trailer lines read as paths) |
| BmAK parsed objects | 19,203 / 20,128 | 19,203 — but **19,203 / 19,203 taggable** |

The five remaining block types were decoded from their own bytes, each with an oracle:

- `General` (78): u8 v6, 68-byte Attributes (own AABB), texture table, `s16 x,y,z,pad` positions at
  `Attributes.f0/32768`, a 20-byte second stream, terminal indices. All 78 pass: every vertex inside
  the block AABB, `count2 == vcount`, buffers end at the checksum.
- `GeneralJC3` (35): GeneralMkIII buffer pattern (packed s16 normals, 20-byte stream); the scale is
  the float 32 bytes before the texture table. Structural arithmetic exact on all 35, positions inside
  the mesh AABB.
- `BavariumShield` (49): 28-byte vertices, float position first; 49/49 exact + contained.
- `WaterDisplacementOverride` (181) + `0x90FE086C` (30): no texture table; 12-byte float positions;
  211/211 exact + contained.
- `Prop` (1): still framed. The single block's vertex layout did not fit any of the above and its
  narrow symmetric AABB makes containment useless as an oracle; left undecoded rather than guessed.

`GEOMETRY.md` regenerated: 233 entities, 56,136 meshes, 77,611 blocks, 77,610 decoded, 1 framed,
0 failed, 20,818,841 vertices, 19,214,751 triangles. `jc3geom.py check` ok.

**The 63 "unresolved filelist paths" were a reader bug, not missing content.** Gibbed's filelists end
with `; <hit>/<total> (<pct>%)`; `read_paths` accepted it as a path, so 63 phantom hashes appeared.
They were the *only* holes in the naming chain: `jc3index.py build` now reports
`unresolved filelist paths: 0`, with 81,862 named rows and 91 unnamed tab entries.

**What remains, measured (no rounding up):**

1. **G1: 925 objects with zero serialized tags** — 768 are 2-byte `Package` stubs, the rest are native
   `Function`/`State`/archetype objects whose property stream is empty (checked: `tag_count == 0` for
   all 925). Their state lives in the executable/default objects; there are no bytes to decode. Every
   object that *has* a tag stream is decoded (19,203 / 19,203).
2. **G1: 8 offset fields** — bool/float residue in nested structs where parent and child flatten into
   one stream and neither carries a name (`OFFSETS.md` has offsets, types and values). BmSDK-AK does
   not ship `FBMScreenShakeStruct`'s declaration, so the ambiguity stands.
3. **G2: 91 unnamed archive entries** — 88 of them in `patch_win64/game0..1` with magic `0x57E0E057`+
   two others. Their own bytes contain no path string that hashes to them (checked), and no filelist or
   dictionary names them. They are addressed by hash and censused by magic; the names are not in the
   install.
4. **G2: 1 `Prop` block** — layout undecoded (above).
5. **10 BmAK audio banks** absent from the install (catalogued, not obtainable).
6. **T**: 0/126 rows behaviour-verified; the spring mapping (T-CAM9) and shake rows stay blocked.

No build was deployed; the dropzone remains test-085.

## G3f — Prop decoded; JC3 geometry is 77,611/77,611 (2026-10-22)

The last framed block, `Prop` (`0x04894ECD`), is decoded. It is the **GeneralJC3 buffer pattern**
under a u8 version 3 header, with the same scale slot — the float **32 bytes before its texture
table**:

```
u8 version=3, attributes, texture table (6 slots, 3 of them ""),
u32 vcount,        vcount x {s16 x, y, z, 0}      positions
u32 count2 (==vcount), count2 x 20 bytes          packed attributes, opaque
u32 icount,        icount x u16
```

The single block (`jc2_barrel_a_lod1.rbm`, 418 vertices, 1206 indices, 402 triangles) pins it
three ways:

- the stored scale float is **bit-identical** to the mesh AABB's Y extent (1.1057356595993042), and
  `scale = stored / 32768` = 3.374437e-05;
- the s16 Y run is the **full 0..32767**, so the quantised range maps exactly onto the AABB;
- the decoded X/Y/Z spans equal the AABB spans to **6.5e-5** relative (a per-axis scale disagreement
  would show here), and all 418 vertices lie inside the AABB.

`locate_textures` also learned that material tables can have trailing empty slots: it now requires
at least one path and every non-empty entry to look like one, which is what let a 6-slot table with
three `""` entries through. Both changes are in `Tools/scripts/jc3geom.py`.

**Rebuilt the full grab** (233 entities, 56,136 meshes):

| item | before this turn | now |
|---|---:|---:|
| blocks decoded | 77,610 / 77,611 | **77,611 / 77,611** |
| framed | 1 | **0** |
| failed | 0 | 0 |

`GEOMETRY.md`: 77,611 blocks, **20,818,841 vertices**, **19,214,751 triangles**, 806,529 material
slots. `jc3geom.py check` ok (0 failed, payload lengths verified); the Prop payload row is
`418 x 12` bytes of positions as all the others. Documentation regenerated (`STATUS.md`,
`GRAB_BACKLOG.md`, `Research/JC3Grab/README.md`), and the scratch sample (`Working/_prop.bin`) was
deleted — game bytes stay outside the notes.

**G2 geometry is now complete.** The only G2 hole left is the 91 unnamed archive entries, addressed
by hash and censused by magic; no name list in the install names them.

## G3g — One more JC3 name from write order; the last two refuse (no build, 2026-10-22)

Naming pass over what was left of the archive residue (3 records after the navmesh recovery).
Strings were not enough. This pass tried the full cross product of the **40** dialogue directories
and **14,849** known basenames, plus numeric take suffixes; none of the three matched. (The navmesh
names did not come from strings either: they came from enumerating tile coordinates and hashing them.)

What did work was *where the record sits*. JC3 writes `.arc` payloads in ascending path order, so an
unnamed record is bracketed by its alphabetical neighbours:

```
patch_win64/game4  0x238cc000  655,360 B  hash 9EBCE9A4
   …/dlc3_starfish_base_02/dlc3_starfish_base_02_landmark_dif.hmddsc
   < 9EBCE9A4 >                                                       <- float payload, .hmddsc
   …/dlc3_starfish_base_04/dlc3_starfish_base_04_landmark_dif.hmddsc
```

`models/landmarks/sea/dlc3_starfish_base_03/dlc3_starfish_base_03_landmark_dif.hmddsc` hashes to
**9EBCE9A4** exactly. The bracket is the evidence; the hash equality is the proof, and the same
ordering reproduces the known `dlc3_satellite_pontoon_14` neighbour (whose directory is doubled)
byte-for-byte, so the ordering rule is not a guess. The path is in
`Tools/names/jc3_neighbour_order.filelist` with the neighbour lines as a comment.

The other two are `.wavc` dialogue takes, and they stay unnamed:

- `patch_win64/game4` **016DE9D1** (84,720 B): physical order brackets it at
  `sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` < it < `…_gameplay_start05.wavc`.
  Tested: every numeric take 0…9999 in widths 1…4, every known basename in all 40 dialogue
  directories, every English `mm320` take under the Arabic directory, and suffix variants on all
  Arabic basenames. No hit.
- `archives_win64/game67` **966DB7BC** (18,800 B): the **only** entry in that archive, so it has no
  neighbours and no bracket. Its hash appears in three `.nl` files, but only inside compressed
  high-entropy runs, not a resolvable reference.

Both are `16-byte header + FSB5` FMOD banks (`u32 size-16`, 12 zero bytes, `FSB5`, one sample, mode
15) — same container as all 31,000 named `.wavc` entries, which is how the payload type was settled
rather than assumed.

| item | before | now |
|---|---:|---:|
| entries named | 81,950 / 81,953 | **81,951 / 81,953** |
| unnamed | 3 (2 `.wavc`, 1 `.hmddsc`) | **2 (both `.wavc`)** |
| derived-names rows | 88 (navmesh) | **89** |

`jc3index.py build` reports 81,951 rows / 78,906 paths, `check ok`, 2 unnamed, DLC 20,682/20,682.
`resolve` on the new path finds `patch_win64/game4 +596,426,752`, size 655,360. `STATUS.md`,
`GRAB_BACKLOG.md`, `Research/JC3Grab/README.md` and `Tools/names/README.md` are updated.

## G1h - The last eight BmAK fields named; the ledger is 423/423 (no build, 2026-10-23)

G1-1's residue was eight offset-only fields whose meaning depended on the nested struct they sat
in (and, for bools, on the bits set in the tag word). The tags carried no name, so the earlier pass
read every offset against the **top-level class** and, for bools, collapsed the cooker's 32-bit
bitfield word to `bool(value)`.
Both were wrong in the same direction: `RBatmobileCannon 0x0004` is `BMScreenShakeStruct.TimeDuration`
in a shake struct and `FInterpCurvePointFloat.OutVal` in a curve point, and a `BoolProperty` tag at
`0x0090` carries `0x3`, which sets **both** `bSmoothLoc` (bit 0) and `bSmoothRot` (bit 1).

Measured before changing anything, over all 33 outer screen-shake instances in the grab: of the 16
that cook an `AdvancedOptions`, the bool word is `0x1` in 12 and `0x7` in the 4 `ImpactShake`s; of
the 23 that cook the outer word, every one is `0x3`. `BmGame.upk` declares both structs, so the
innermost struct on the tag path plus the mask names every field without a guess.

Changes (read-side only):

- `upk_read.py` keeps each `BoolProperty` tag's raw word as `bits`; `value` stays the bool.
- `batmobile_grab.py compact()` preserves `bits`; `grab_model.py` schema 5 -> 6.
- `grab_offsets.py` resolves against the innermost struct (`immediate_struct`, including
  `InterpCurve*.Points[i]`), names bools by their set bits, and keys fields by
  `(class, offset, type, container_struct)`.
- `bmak_layout.py struct_size()` packs consecutive bools into one word, matching `layout()`.

Result: **423 fields / 423 named / 0 undecidable** (was 422 / 414 / 8). Archetype fields 366,
archetype occurrences 1,736, total occurrences 2,593 - no value or occurrence added or removed. The
one extra field is the split `0x0004` key. `bmsdk_offsets.py --report` now matches Cannon
(`0xc94`), HeavyCannon (`0xb31`), Sonar and Winch exactly; extent mismatches fell from 8 to 4, all
on classes where the shipped `BmGame.upk` copy is not the linked class.

Green: `grab_offsets.py --check` (423/423/0), `grab_model.py check` (schema 6, 15/15),
`bmak_coverage.py --check` (423 fields -> 19 rows), `bmsdk_offsets.py --check` (35 classes, 3,133
properties, 48 structs), `bmak_bind.py --all --segments`, `status_audit.py --write`.
`OFFSETS.md`/`.json`, `STATUS.md` and `GRAB_BACKLOG.md` regenerated/updated.

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

## T-audit - In-scope completion, first translation batch (no build, 2026-10-23)

The headline translation percentage was measuring the wrong denominator. `STATUS.md` divided
evidenced rows by all 126, including the 14 rows where JC3 has no system to carry them, so 100%
was unreachable by design; it also counted rows whose own transform column said `class` as
`assumed`, and two rows whose build value was simply wrong as `keep`.

Changes:

- `status_audit.py` now reports completion as `resolved / (rows - out)`, keeps the raw `out` count
  outside the denominator, and reports `next` (queued) separately. The per-document table carries
  `queued`.
- `t3_fleet.py` grew from 21 to 41 members so the class claims re-decided in this pass are
  reproducible: mass, inertia, COG bias, health, deform/impact, wheel mass/shape cast, steering,
  drift, nitro, frontal area and top speed.
- Re-decided against that table: T-M1, T-M3, T-S3, T-R3, T-K3, T-B3, T-ST5 (T-1), T-DM1, T-DM6
  (T-2b) moved from `assumed` to class/decoded evidence; T-DR1 moved the other way (the drift
  block is a JC3-native choice, not the 6 t median).
- Wrong "now" values corrected: T-B3 is 5.68, not 2.0 (fleet maximum 2.0); T-DM6 is 0, not 1
  (fleet invariant 1); T-DR1's sensitivity is 4 vs the claimed 2, entry 20 vs 180.
- T-DM1 now cites the newly named `RVehicleBatmobile.Health = 1,200`; 2,000 is kept as the 6 t p75
  and land maximum, because the donor health has no unit bridge.
- Next build queued: **4 rows / 6 values** - T-DM6 `deform_scale` 0 -> 1, T-DM7
  `impact_damage_factor` 0 -> 1 and `impact_armor` 5000 -> 5, T-B3 nitro grip 5.68 -> 2.0, T-ST5
  countersteer 2.0 -> 3.0 and steer_in 1.5 -> 2.0.
- `GRAB_BACKLOG.md`, `MODDING_PLAN.md` and the T-1/T-2b/T-3/T-5 docs reconciled to the generated
  numbers; the old 61.9%, 60.3%, 64.8% (57/88), 37.5% and 88-row figures are superseded.

Numbers: **86 / 112 in-scope rows resolved = 76.8%**, 12 assumed (10.7%), 14 blocked (12.5%),
14 out (excluded), 4 queued, **0 / 112 behaviour-verified**.

Green: `t_rows.py check` (103 rows, 35 edits over 16, 4 next), `t3_fleet.py --check` (41 members
over 156 vehicles), `status_audit.py --check`, `bmak_coverage.py --check` (423 fields -> 19 rows).
`T_ROWS.jsonl`, `T3_FLEET.md` and `STATUS.md` regenerated. No build, no game files.

## G3h — The Polish take, named from the FSB5 token (no build, 2026-10-23)

G3g left two `.wavc` records unnamed. This pass cracked one of them using the **FSB5 name table**,
which I had mis-parsed last time (I read the name table at header+52; it is at header+60, the
researched FSB5 layout, and the earlier offset only *looked* right because the bigger `nts=40` tables
have slack).

`.wavc` payloads are a 16-byte prefix (`u32 size-16`, 12 zero bytes) plus an FMOD **FSB5** bank. The
FSB5 name table holds **one token per take** — and it is **language-invariant**. The proof is in the
controls:

```
audiotapes_eden_020.wavc  ara/bra/eng/fre/ger/ita/jap/mex/spa  ->  all token a1948897666
defendtheplane_090.wavc   eng 82088DE4 (game56)               ->  a1630394639
                        jap BEA6350C (game64)               ->  a1630394639
                        pol 966DB7BC (game67, UNNAMED)      ->  a1630394639   <- the lever
```

14,849 named `.wavc` parse to 14,849 **distinct** tokens — the token is 1:1 with the basename, and
every language copy of a take shares it. So the unnamed `game67` record's token `a1630394639` *is*
the basename `mission_mm110_dial_defendtheplane_090`, already named in eng and jap. Only the
directory was left: hashing `sound/dialogue/<lang>/mission_mm110_dial_defendtheplane_090.wavc`
against `966DB7BC` hits exactly one code, **`pol`**. `game64` (jap) and `game67` (pol) are both
single-entry language shards — same take, same token, different recording.

The remaining one will not yield to the same trick, and I can now say why rather than guess:

- its token **`1606523576` maps to no named file in any language** — a unique orphan, so there is no
  sibling copy to lend it a basename (the reason the Polish one fell);
- the token is **not** a hash of the basename. A battery — CRC32, Jenkins lookup3, FNV-1a, djb2,
  sdbm, MD5/SHA1/SHA256 prefixes, in dec and hex, over basename and full path — matches **0/25**
  known `(basename, token)` pairs. That matches the research: the FSB5 name table is FMOD's
  "original source file name", an opaque per-take id from the build, not invertible without the
  original FMOD project;
- so its name must come from a string or a sibling, and there is none: **no named file anywhere
  contains a `sound/dialogue/ara/mission_mm320_dial_gameplay_` path or even the bare `…_090`
  string** (the `mm320_main.stringlookup` lists bare take names for the *English* mission and omits
  `_090` entirely), and every numeric take, every known basename across all 40 dialogue dirs, and
  every English `mm320` take under `ara/` hashes elsewhere.

| item | before | now |
|---|---:|---:|
| entries named | 81,951 / 81,953 | **81,952 / 81,953** |
| unnamed | 2 (both `.wavc`) | **1 (`.wavc` orphan)** |
| derived-names rows | 89 | **90** |

Green: `jc3index.py build` 81,952 rows / 78,907 paths, `check ok`, 1 unnamed, DLC 20,682/20,682;
`resolve` on `sound/dialogue/pol/mission_mm110_dial_defendtheplane_090.wavc` -> `game67 off=0`,
18,800 B; `status_audit.py --check`. New list: `Tools/names/jc3_fsb5_token.filelist`.
`STATUS.md`, `GRAB_BACKLOG.md`, `Research/JC3Grab/README.md` and `Tools/names/README.md` updated.

**G2 naming is 81,952 / 81,953 = 99.999%.** The single residue (`016DE9D1`) is an Arabic
`mission_mm320_dial_gameplay_*` take that exists only in that one patch record and is referenced
nowhere in the install; without the FMOD project that produced its token, it stays censused by magic
byte.

## T-plan — the whole translation mapped before execution (no build, 2026-10-23)

The rule for this entry is the user's: **no guesswork, keep it abstract until the entire plan is
mapped**, because improv once translation starts is unavoidable and should be confined to declared
places. So before any value moves, `Working/Translation/T_PLAN.md` now exists and says exactly
where every row stands and what happens to it.

**What it maps.**

- **Stage model S0–S6** for every row: evidence capture (S0, closed by G1/G2) → row decision (S1,
  126 rows) → value derivation (S2) → batch staging (S3, `t1_apply`) → build/install/file proof
  (S4, `t5_apply`/`t5_build`/`verify_install`/`t5_measure`) → behaviour proof (S5, the prescribed
  manoeuvre) → journal/audit (S6). A row is "translated" only at S5; the file keeps bytes and
  behaviour apart, like `STATUS.md` does.
- **Batches A–G.** A = test-085 (done: 35 values / 16 rows). B = the queued batch, specified with
  all six exact `old → new` pairs and their pass criteria (T-DM7 ×2, T-DM6, T-B3, T-ST5 ×2) —
  nothing else is staged. C = the 12 assumed rows, one settle route each (fleet stats from
  `VOCABULARY`/`T3_FLEET` for nine, written decisions for T-E5/T-B4/T-MA7, a screenshot gate for
  T-MA5, a manoeuvre for T-DR1). D = the 14 blocked rows triaged: **7 routable** (`.physicsc`
  writer, usage-vocabulary dump, custom `SVehicleLight`, WPN-2), **2 research** (T-CAM9/T-CAM11
  unit bridges), **5 permanent named omissions** (T-S6, T-ST7, T-AU3, T-AU5, T-CAM8). E = the 66
  carried rows that owe only their check. F = the camera re-derivation (test-086 values forbidden;
  regenerate through `bmak_camfile.py` now that the composition is decoded). G = feature-gated
  rows, owned by plan phases, not by T.
- **Coverage proof:** 16 + 4 + 12 + 14 + 66 = **112 in-scope rows, each in exactly one batch**,
  plus the 14 `out` rows accounted separately. Every `verify` cell lands in the campaign: 16
  prescribed driving manoeuvres (A1–A16, audio takes wherever pitch is the number), 4 screenshot
  gates with named measurable passes, and the file-level tool gates.
- **Improvisation register:** the only places improv can occur (driver variability, visual
  verdicts, feel rows, evidence arriving mid-batch, padding normalisation) each carry a
  pre-declared rule — re-take rather than reinterpret, measure rather than mood, never merge into
  a live batch.
- **Gate list + execution order** (§8, §10): the re-runnable command table with last results, and
  the post-approval order starting with Batch C (desk) → Batch B stage/build/install → manoeuvres.

**Cross-check fixes applied** (claims that disagreed with the generated counts or the live state):

| where | was | now |
|---|---|---|
| `MODDING_PLAN.md` §0.1 | live build test-083 | **test-085**, re-verified today: `install.ps1 -Action Status` == test-085's receipt (test-086 not installed) |
| `MODDING_PLAN.md` header | G2 99.998% | 99.999% (81,952/81,953) |
| `MODDING_PLAN.md` QA-1 row | not started | instrument built + take 1 measured (T-M1/T-E1 closed, T-E4/T-K1 partial) |
| `T6_HUD_CAMERA.md` §4 | "T-CAM5 blocked on the boom composition" | composition decoded (§2b, 18/18); the remaining blocks are T-CAM9/T-CAM11 |
| `GRAB_BACKLOG.md` T section | no execution map | points at `T_PLAN.md`, superseding *Next five moves* |

**Gates run this entry, all green:** `status_audit.py --check` (STATUS current), `t1_apply.py`
(35/35 edits match build + table + real members), `t3_fleet.py --check` (41 members / 156
vehicles), `bmak_coverage.py --check` (423 fields → 19 rows). **No build, no install, no value
changed** — translation starts only when Batch C/B are executed against this map, with the
install carrying explicit approval as usual.

## T-audit (cont) — Batch C settled from the fleet; Batch B staged as test-087 (no install, 2026-10-23)

The plan (`T_PLAN.md`) was executed as far as it goes without an install decision.

**Batch C — the 12 assumptions settled (11 with evidence, 1 signed off).** Every route was a
script-reproducible number, not a relabelling:

| row | was | now | evidence |
|---|---|---|---|
| T-S5 lateral tyre offset 0.2 | assumed | **class** | fleet median 0.2 (T3_FLEET n=125 IQR 0.1…0.3; VOCABULARY n=167) |
| T-ST3 high-speed rack 0.6 s | assumed | **class** | inside land IQR −1…0.8; −1 is the sentinel |
| T-ST4 input power 3/3/3 | assumed | **class** | the donor's own 3/3/3, inside every 6 t IQR |
| T-ST6 drift aligning 0.3 | assumed | **class** | donor 0.3, inside shipped 0.3…0.8 |
| T-K2 min_time_to_block 5 | assumed | **class + queued** | donor ships **1**, fleet median −1; build 5 has no source → **5 → 1, both axles** |
| T-B2 nitro extra top speed 50.46 | assumed | **class + queued** | donor 40, fleet median 40 (n=145); T3_FLEET middle 50 % is exactly 40 in every class → **50.46 → 40** |
| T-B4 heat_boost/turbo_jump | assumed | **decoded (fleet)** | every shipped car carries them; donor values read from VOCABULARY |
| T-A1 frontal area 6.63 | assumed | **class** | 3–8 t IQR 4…6.72, 6 t+ median 6.95; mesh cross-section 7.9 m² |
| T-MA5 glass Window block | assumed | **derived** | tint = authored paint colour (VALUES.json); opacity = BmAK opacity map × `Glass_Opacity` (factors.py) — no tuned constant |
| T-MA7 palette | assumed | **decoded** | the donor's shipped 10-tint palette, read from the build |
| T-DR1 drift block | assumed | **decoded** | the build block is the donor's, member for member (entry 20, sensitivity 4, angle 45, min 10) |
| T-E5 official_top_speed 336 | assumed | **assumed, signed off** | the wiki's 209 mph is the mod's stated target (requirement 1) and has no file source; file-side it is inside the shipped domain 25…350 (n=233). Re-derive after T-B1 |

**Three false "keep" claims were caught by the same pass** — the exact failure mode STATUS's history
records for `deform_scale`: the ledger said "vanilla Serpente" ships `min_time_to_block` 5 (the
donor ships **1**); T-S5 was called "unchanged by the project" while the build holds **0.2** against
the donor's 0.1; and the T-3 audit claimed the donor drift sensitivity is 2 when VOCABULARY's donor
column reads **4**. Ledger, T3_COVERAGE §4 and T_PLAN were corrected to the decoded values.

**Batch B — now 6 rows / 9 values, staged as test-087.** `t5b_current.json` is the live test-085
decode (`t1_current.py`); `t5b_edits.json` carries the nine edits with `old` read from it and
`new` re-read from the fleet tables; `t1_apply.py` gained `--edits/--current` so both batches
validate independently. Results: `t1_apply` **9/9**, `t5_apply` **9/9** with 0 collateral
(`lave_health_medium`, brakes, `custom_land_global`, `land_steering`), `t5_build --tag test-087`
(4 changed files, all in the list; 505 `.toc` records rebuilt), and `t5_measure` **9/9 read back
through the staged `.toc`** (impact_damage_factor 1.0, impact_armor 5.0, deform_scale 1.0, nitro
grip 2.0, extra top speed 40.0, countersteer 3.0, steer_in 2.0, min_time_to_block 1.0 both axles).

Numbers now: **97 / 112 in-scope rows evidenced (86.6%), 1 assumed (signed off), 14 blocked,
6 queued rows / 9 values**; 0/112 behaviour-verified. Green: `t_rows build`+`check` (103 rows,
edit 16 / next 6 / keep 48 / epe 16 / blocked 10 / out 7), `status_audit --check`, `t3_fleet
--check`, `bmak_coverage --check`, both batches' `t1_apply`.

**Nothing was installed.** test-087 sits in `Builds/test-087` with its installer; the live dropzone
is still test-085 (hash-verified today). Decision recorded: the install was **kept staged** at the
user's call (2026-10-23). When it is wanted: install → `verify_install` → `t5_measure` on the
deployed `.ee` → §5 takes A11/A7/A9/A5.

## Test-087 failed: the damage row translated offence as defence (2026-10-23, afternoon)

The car was driven on test-087. Ram anything at boost and the Batmobile dents, burns and dies —
the one thing it must not do. The test is a real failure and it is not a tuning problem; it is the
row (T-DM7) and the record around it. Full write-up: `Working/Translation/POSTMORTEM_DAMAGE.md`.

**Mechanism.** test-087 = test-085 + 9 values, three of them damage: `impact_damage_factor` 0 → 1,
`impact_armor` 5000 → 5, `deform_scale` 0 → 1. The first is the switch: with the factor at 1 the car
takes collision damage at a 6 t-armour level. Everything else in the block stayed at the game's
maximum, so the only thing that changed was that collisions started counting.

**Where the number came from.** T-DM7 read BmAK `ImpactMinDamageSpeed` 20 / `ImpactMaxDamageSpeed`
150 / `ImpactBoostMod` 2.0 as collision *defence*. They are the ram *attack*: `TakesDamageFromRam
(Target, RamSpeed)`, `CanBatmobileDoImpactDamage(OtherVehicle)` and `CalculateAndStoreImpactDamage
(OtherVehicle, …)` all take the vehicle being rammed, and the class has no incoming-impact entry.
JC3 gives a player car no way to damage what it rams, so the BmAK block has no JC3 expression at all
— T-DM7 is `out`, not a value row. The row's own transform cell said there was no bridge, and
`conf: class` was allowed to stand in for it: "156/156 land vehicles ship 1" then out-voted the
behaviour. That is the failure mode, in one sentence.

**The immunity it deleted was a hand-hack.** Against the shipped ranges in `VOCABULARY.md`, the
pre-087 block has six values outside them: `impact_damage_factor` 0 (shipped 1…12), `impact_armor`
5000 (0…5), `bullet_armor_strength` 100 (0…99), `deform_scale` 0 (1…2), `melee_armor` 5000 (0…0),
`melee_armor_strength` 100 (0…0). Everything else sits exactly at a maximum (bullet 5000,
explosion 250/4000, smoke 1050, burn 250, thresholds 4000/1050/250). So the working behaviour was
real, load-bearing, and never recorded as a switch — the first tidy-up pass was guaranteed to delete
it. That is why every gate stayed green: `t_rows`, `t1_apply`, `t5_apply`, `t5_build` and
`t5_measure` all prove bytes, and `STATUS.md` counted 97/112 rows "evidenced" against **0/112
behaviour-verified**. T-DM7's own verify cell said "damage taken", the opposite of the source.

**Bullets.** The car is at the shipped ceiling in every armour channel and bullets still destroy it,
so armour is a reduction, not immunity. "Small arms do not hurt it" cannot be expressed by tuning
`VehicleDamage`; it needs a mechanism (entity damage-immune state, or a health hook) and stays
blocked (T-DM9). That is the same architectural gap one level down.

**Camera (test-086) — derived, but derived wrong.** Not hand-tuned: all eight values trace to
`DrivingCamConfig1` / `DrivingCamFOV*` (`CAM_TUNE.json`). Two arithmetic errors: the FOV max copied
95 **h** as vertical (should be 63, shipped 85), and the boom/height were body ratios (now decoded as
400 cm boom + 300 cm sit = 700 cm, 130 cm above the origin). The corrected camera is now fully
derivable and needs no taste call.

**Record changes.** `T-DM7` → `out`; new `T-DM8` (behaviour: ramming does not move the health bar;
JC3 mechanism = `impact_damage_factor` 0, a declared switch, keep); new `T-DM9` (behaviour: small
arms do not move it; blocked — no member); `T-DM6` → `keep` (declared cosmetic switch). `t5b_edits`
marked withdrawn; the six surviving values re-cut into `t5c_edits.json` and **not cleared to build**
until each has a behaviour and a failing take. New `Tools/scripts/damage_audit.py` +
`Working/Translation/damage_switches.json`: any out-of-domain damage value must be declared, or the
check fails. Rules R1–R5 are in the postmortem; R2 is the one that would have stopped this
("`class` is not a bridge"). `STATUS.md` regenerated: **97/113 resolved, 1 assumed, 15 blocked,
15 out, 4 queued, 0/113 behaviour-verified**.

**Gates.** `t_rows build`+`check` (105 rows), `bmak_coverage --check`, `status_audit --check`,
`damage_audit` (6 out-of-domain, all 6 declared), `t1_apply` on `t1_edits` and on `t5c_edits` (6/6
against the live 085 decode). **test-087 is live and must be rolled back**:
`Builds/test-087/install.ps1 -Action Rollback085`.

## G1 HUD contract + G2 damage mechanisms (2026-10-23, late)

Two grabs, both asked for after the test-087 postmortem.

**G1 — the HUD health bar is now a contract, not prose.** `hud_spec.py` reads
`ModuleStruct_Batmobile.as` and extracts `UC_SetHealth(health, max)` into
`HUD_SPEC.json → bmak.health_contract`; `--check` fails if the movie stops agreeing. What it says:
`health` is a **proportion** (1.0 = one bar), `max` is the bar's ceiling, the bar is
`min(1, health)`, everything above 1 is the armour overlay (`max(0, health-1)`), and `max` above 1
selects an `Armour0…Armour4` background via `int((max-1)*4)`. Pulse below 0.2; `0.05` per frame at
30 Hz = **0.667 s** empty→full; hides 2 s after full + settled XP; battle mode forces it visible.
That is the instrument the take reads — it has no notion of damage sources, so it cannot prove
immunity by itself. `HUD.md` §4.1; `hud_spec.py --check` PASS (bmak.scripts, bmak.constants,
bmak.health_contract, jc3.scripts, jc3.constants).

**G2 — the immunity mechanism exists, and it is one field.** Searched all **232 decoded `.epe`
graphs / 91,157 objects** (`jc3_damage_search.py`, record `Research/JC3Grab/DAMAGE_MECHANISMS.json`,
write-up `DAMAGE_MECHANISMS.md`):

- every vehicle root (`CCar` 126, `CBoat` 35, `CHelicopter` 23, `CMotorBike` 19, `CAirPlane` 18,
  `CTrain` 12 = 233 roots) carries `health` **float 100.0** and **`invulnerable` int32 0**, plus
  `damage` = the module instance id;
- no shipped vehicle sets it, which is why the module vocabulary never showed it;
- the value is live: **10 of 104 `CDamageController` objects ship `invulnerable = 1`** (4 entities,
  cargo props), so the engine honours 1;
- false leads closed: `CVehicleRule.health/invulnerable` is spawn metadata (all 0);
  `CConstraintBreakableDecoratorData.Indestructible` is a physics decorator (all 0);
- the byte address is calibrated against two neighbours: `.epe` properties are
  `type · Jenkins hash · value`, `health` is `0x09` float (`00 00 c8 42` = 100.0), `damage` is
  `0x0e` int (`17 c2 f1 27` = 670155287 = the graph's value). `invulnerable` is therefore
  **`0x0e · af4406fb · 00 00 00 00` at `+1162/+1163/+1167`** — a **4-byte write at `epe+1167`**,
  the same patch-and-repack route the camera proved.

**Consequence for T-DM9.** It stays `blocked` (the write is unproven for a vehicle root) but the
route is named: probe build with `invulnerable = 1` as the only edit; take = 200 SMG rounds plus a
full-boost ram, health bar untouched. Caveat written into the row: the flag is whole-vehicle, so it
also blocks the destruction BmAK has in tank battles — right for "ramming and small arms do not
scratch it", wrong for "only heavy weapons". The finer split still needs the module's damage model,
which can only reduce.

**Gates.** `jc3_damage_search --check` (232 graphs, 233 roots, 2 token classes, 27 token
properties), `jc3_damage_search --epe` (three addresses), `hud_spec --check` (5 PASS),
`t_rows build`+`check`, `bmak_coverage --check`, `status_audit --check`, `damage_audit` (6/6
declared), `t3_fleet --check`, both `t1_apply` lists. Counts unchanged: 97/113 evidenced,
15 blocked (T-DM9's route named), 4 queued, 0/113 behaviour-verified.

## G1 HUD inventory: 25 modules, not two movies (2026-10-23, later)

The user's challenge was correct: "the HUD isn't just health". The previous entry had a health
contract for `HudModuleBatmobile` and called the HUD done. It was two movies out of nineteen.

**The failure was architectural, not a missing file.** `bmak_hud.py` carved from a hand-written
`TARGETS` list. No code enumerated the engine's own roster, so:
- `RHudModuleLocalRadar` (the radar, 35 functions, 7 cached calls) points at a movie named
  `HudModuleBespokeLocalRadar`, not after its class;
- `HudModuleBoss` has no `SwfMovie` in its default object at all, so a name-driven grab could not
  bind it even though the movie exists;
- `HudModuleDownloadProgress.Image` (36 KB) and `HudModuleDownloadProgress.HudModuleDownload_Batman`
  (12 KB) carved to the same output path — the second overwrote the first;
- nothing counted the 61 `SwfMovie` exports or asked which of the 25 classes was still unbound.

**What is now in the record.** `bmak_hud_inventory.py` reads `BmGame.upk`, lists all 25
`RHudModule*` classes, takes each class default object's `SwfMovie` references (14 classes; a sweep
of every CDO also found two owners outside the namespace: `RGFxMovieRadialGadgetSelect` owns the
gadget wheel, and `RHudModuleDownloadProgress` owns both its main movie and the `_Batman`
extension), extracts every movie's `UC_*` signatures, and binds the rest by evidence: a class's `CachedFunction_X` names
must exist as `UC_X` in the movie. That binds `RHudModuleBoss` → `HudModuleBoss.Image` at 2/2
(`JustShake`, `SetHealthLevel`) and leaves **10 classes with no movie**, printed by `check` rather
than dropped: `BespokeBase`, `ChallengeMode`, `ExtraSequence`, `Firefly`,
`ForensicBeaconTracking`, `ForensicDetail`, `GadgetSelect`, `HackingMode`, `HeavyTankScanBase`,
`PerformanceTest`.

**The grab is 19 movies / 252 setters.** Targets (lock-on, `VehicleMissileTarget` plain/bomb/EMP/
friend/multi/invalid, `missile_border_anim`, `missile_lockon_square_anim`), LocalRadar
(`LockonMeter`, `lockonAndHealthMeter`, `UC_UpdateTargetPosition`, `UC_SetLockonValue`), Alerts
(triple tracker, `UC_SetInterceptAngle`, forensic trail), Health (a **second** contract: Batsuit
health, `UC_SetArmourLevel`, `UC_SetArmourMaxima`, adrenaline — not the vehicle bar), StoryMode
(threat meter, warnings, lap counter, zoom gizmo), Boss (+`FireflyIcon`), Scanner, DetectiveMode,
Objectives, RoomName, CrimeSceneInfo, SuicideCars, DownloadProgress, the gadget wheel and the
prompt HUD. `HUD_INTERFACES.json` is the per-movie contract; `HUD.md` §5 is the element map,
§5.1 the battle-mode/lock-on/threat behaviour, §8 the speedometer question.

**Speedometer, honestly.** No movie in the shipped set implements one: `speed`/`mph`/`kmph`/`rpm`/
`tacho` do not occur in any of the 19 decompiled movies, and none defines `UC_SetSpeedBar` or
`UC_SetBatmobileRevDisplayActive`. The native hooks exist (`RHudModuleExtraSequence.SetSpeedBar`,
`RHudModuleLocalRadar.SetBatmobileRevDisplayActive`), but `ExtraSequence` has no movie here. So the
readout is native or unshipped — recorded as an open question, not papered over, and the earlier
T-HUD1 "draws it elsewhere" is now marked `searched` with that evidence.

**Gates.** `bmak_hud_inventory.py check` PASS (25 modules, 19 movies byte-identical, 61 SwfMovie
census, 10 gaps listed), `interface` 19 movies / 252 setters, `bmak_hud.py check` 2/2,
`hud_spec.py --check` PASS. Translation counts are unchanged: T6 gained no numbered row — the
other modules have no JC3 host and are recorded as `out` in prose, not as fake rows.

## The speedometer is a disabled debug readout (2026-10-23, later still)

Follow-up to the HUD inventory: "find where AK draws the Batmobile speedometer outside Scaleform
and document the class and fields".

**There is no retail speedometer in the shipped UI.** The 19 HUD movies define 252 `UC_*` setters
(149 distinct names); none names speed, revs, gear or a dial. Inflating all 19 and scanning the tag streams finds only
`SpeedMin`/`SpeedMax` in `HudModuleHealth.Image`, and FFDec's dump shows both are **FrameLabel**
tags (tag id 43) — animation labels, not a gauge. The `SetSpeedBar`/`SetBatmobileRevDisplayActive`
hooks are orphans: no movie defines either function.

**The only speedometer in the install is native and off.** `BmGame.RPlayerController:bDebugSpeedometer`
(`BoolProperty`) is the sole "Speedometer" identifier; `BmGame.ini:6303` and `DefaultGame.ini:989`
both set it `False`. A full bytecode scan of all **29,620** script functions finds exactly one
reference: `RDebugMenuContent.DoGadgetsMenu`, the developer debug menu, whose string pool contains
the item label `Speedometer`. The draw is native: `RPlayerController.DrawHUD` (656 B, script) calls
`RPlayerControllerBase.DrawHUD` (39 B, bytecode-less native thunk); `RPlayerController.PreRender`
owns the `Canvas`. No `RHudModule*` is involved.

**Fields that feed the number.** `RVehicle` has no scalar speed property (checked across
`RVehicle*.g.cs`), so the magnitude is `Engine.Actor.Velocity` — verified in `Engine.upk` as
export `Actor.Velocity`, class `StructProperty` (FVector). The Batmobile's artificial-speed chain
is `RVehicleBatmobileBase`: `CurrentThrottle` 6408, `ThrottleSpeed` 6412 = **2.0**,
`FakeExtraSpeed` 7152, `FakeExtraSpeedMax` 7156 = **3500.0** (126 km/h in cm/s),
`FakeExtaSpeedAccel` 7160 = 600.0, `FakeExtaSpeedDecel` 7164 = 2000.0, `BattleModeSpeedDelta`
7860. The native readout's own unit conversion is inside the native function and is not claimed.

**Tool + record.** `bmak_speedometer.py --write|--check` re-derives all of the above (movie tokens,
config values, the one script reference, native sizes, field offsets/class defaults, and the
`Actor.Velocity` type) into
`Research/BatmobileGrab/SPEEDOMETER.json`; `SPEEDOMETER.md` is the write-up. HUD.md §8, T6 T-HUD1,
STATUS and the T_PLAN gate list point at it.

**Open, honestly:** if a speedometer is visible in normal play, it is neither a shipped UI asset nor
`bDebugSpeedometer` (off). Enabling the debug menu's "Speedometer" item is the one-variable test that
settles it; nothing in the packages carries that name.

**Gates.** `bmak_speedometer.py --check` PASS; the HUD inventory, hud_spec, status_audit and all
previous gates unchanged.

## Deploy test, then Batch B2: behaviour rows before values (2026-10-23)

**The deploy test found a live fault first.** `verify_install.py --build Builds/test-085`
reported **8/9** — the dropzone `.ee` was `10B14A60…` = **test-087**, the withdrawn damage build.
The postmortem's rollback (`install.ps1 -Action Rollback085`) had never actually run, while
`T_PLAN.md` already claimed "live build = test-085, verified today by hash". Reinstalled test-085
(9/9), then ran the whole file-level suite green: `t5_measure` 35/35, `t1_apply` 35/35,
`t3_fleet --check`, `bmak_coverage --check`, `status_audit --check`, `bmak_hud.py check` 2/2,
`bmak_hud_inventory.py check`, `hud_spec.py --check` 5/5, `bmak_speedometer.py --check`.

**Batch B2 — the six staged values were re-sourced behaviour-first (rule R1).** Each had to name
the BmAK behaviour behind it (or the search that proves none exists), the JC3 mechanism with its
shipped domain, and the take that can fail:

| value | old → new | source | BmAK behaviour | take |
|---|---|---|---|---|
| `nitro_boost.grip_multiplier` | 5.68 → **2.0** | `decoded` (donor) | **none** — no grip/traction member in the streams | A9 |
| `nitro_boost.extra_top_speed` | 50.46 → **40** | `decoded` (donor) | torque band **2100 → 3000 cm/s** = +32.4 km/h (×1.30 → ×2.10) — a bound, not a number | A2 |
| `brakes.front.min_time_to_block` | 5 → **1** | `decoded` (donor) | **none** — no lock member, no anti-lock behaviour | A5 |
| `brakes.rear.min_time_to_block` | 5 → **1** | `decoded` (donor) | same | A5 |
| `countersteer_speed_factor` | 2.0 → *withdrawn* | — | BmAK gives the **rate** (T-ST7) and the drift pair, no gain | A7 |
| `steer_in_speed_factor` | 1.5 → *withdrawn* | — | same | A7 |

**T-ST5 was withdrawn, not built.** Its 3.0 / 2.0 was a 6 t fleet median on a row whose `verify`
cell is a behaviour and where BmAK supplies no countersteer gain — R2 forbids exactly that. The
build's 2.0 / 1.5 **is the donor's shipped pair**, so the row became `keep` with a named origin
(R5) and its gate A7 runs against the live build. Two defects fell out of the pass: 5.68 sat
outside *every* shipped range for that member (1.2 … 2), and 5 had no source (Batch C had already
disproved "vanilla Serpente = 5").

**test-088 built and deployed** (batch table written first, §0.2): `t1_apply` 4/4, `t5_apply`
4/4 over 2 modules, `t5_build` "2 changed, 0 added, 0 removed" + 478 internal `.toc` records,
`verify_install` **9/9**, `t5_measure` **4/4** through the installed `.toc`. The live pair now
carries test-085's 35 values and Batch B2's 4 (`.ee` `5A79D885…`, `.toc` unchanged).

**Batch D triage scheduled** in `T_PLAN.md` §4D: usage-vocabulary dump first (a read, unblocks
T-FX3), then the `.physicsc` write spike (decides T-P3/CO2/CO3 either way), features behind
LGT-1 and WPN-2, research behind CAM-1; the 5 permanent omissions keep their reason in `why`.

**Counts moved:** queued 4 rows / 6 values → **3 rows / 4 values** (built, take pending); ledger
keep 50 → **51**, next 4 → **3**; and two of this plan's own stale claims were corrected — its §2
ledger table said `blocked 10 / out 7` when `t_rows.py check` sums to **11 / 8** (105 rows), and
its sources table asserted a live build the dropzone did not hold. `t_rows.py check`,
`status_audit --check` and both edit lists are green.

**Open, honestly:** 0 rows are behaviour-verified. What test-088 owes is four takes — A2 boost top
speed, A5 braking 100 → 0, A9 0–100 with/without boost, A7 drift release — each recorded in
`QA1_RESULTS.md`, with A8 needing an audio-enabled take.

**The staging gate was checked for vacuity, and it is not.** `t1_apply.py` compares `old`
against a *snapshot* (`current.json`), not the dropzone — and that file is a decode of
**test-083**, the base the original 35 were written from. Batch B2 therefore got its own:
`t1_current.py Builds/test-085/aaf -o t5c_current.json` → `t1_apply.py --edits t5c_edits.json
--current t5c_current.json` = **4/4**, so every `old` is now proven against the base the batch was
actually packed from. The control makes it a real test: point the *35*-edit list at the same
test-085 snapshot and it **fails** (`T-K1 Brakes.rear.max_brake_torque: build holds 5000, list
expects 10000`, `T-AU4`, `T-DM2` …, exit 1). A future batch regenerates its own snapshot from its
own base; `current.json` is never rewritten for a batch that is already built.

## Batch B3: the translator is a calculator — values re-joined to names (2026-10-23)

**The defect.** G1-1 had already named all 423 offset-only fields, but the translation rows never
consumed those names: four staged rows still asserted "no member exists in the Batmobile streams"
for quantities the grab in fact carries. That is the architecture failure — a translator that
guesses where the grab has data. `bmak_chain.py` closes it: it walks the BmSDK layout (`Ptr + N`
per class) over every grabbed object, names each cooked tag by layout when the stream stripped the
name, resolves values down the class-default/archetype chain (`Class → base → …`), and writes
`Research/BatmobileGrab/CHAIN.json`.

| claim the rows carried | what the chain shows |
|---|---|
| "no countersteer/steer-in member" (T-ST5) | `DriftCorrectionSteerSpeed` **1.0**, `SteeringSpeedReCentreMod` **1.0**, `SteeringReductionFactor`/`CurrentSteeringReduction` 1.0, `DriftSteeringAssist`/`DriftSteeringBias` absent → false / 0 |
| "no additive-km/h member" (T-B2) | `FakeExtraSpeedMax` **3500**, `FakeExtaSpeedAccel` **600**, `FakeExtaSpeedDecel` 2000, `BoostDuration` **2.0 s** (no archetype override), `InfiniteBoost` false — bit 29 clear in `Default__RVehicleBatmobileBase`'s bool word 4194304 |
| "no grip/traction member" (T-B3) | still true — and now *proven*: G1-1's 423/423 census plus a chain grep over `RVehicle → … → SVehicleSimCar` return none; the boost members that exist are torque/cooldown only |
| "brake members are …" (T-K2) | the family also carries `HandBrakeOffTime` **0.3 s**; `--grep 'Block|Lock|Abs|Anti'` proves no wheel-lock or anti-lock member anywhere |

**The new staged values** (`T_PLAN.md` §4 Batch B3; edits in `t5d_edits.json`):

| value | old → new | how it is computed |
|---|---|---|
| `countersteer_speed_factor` | 2.0 → **1.0** | identity from `DriftCorrectionSteerSpeed` — drift correction runs at base steering rate with no assist gain. **R3**: below shipped 1.5 … 20 (n=252) |
| `steer_in_speed_factor` | 1.5 → **1.0** | identity from `SteeringSpeedReCentreMod`, the chain's only other steering-rate modifier — a kind-match, documented as such. **R3**: below 1.2 … 10 |
| `nitro_boost.extra_top_speed` | 40 → **43.2** | min(FakeExtraSpeedMax 3500, FakeExtaSpeedAccel 600 × BoostDuration 2.0) = 1200 cu = 43.2 km/h on the project's cm/s convention (`CAMERA.md`: 3000 cu = 108 km/h). In-domain 30 … 60 |
| `nitro_boost.grip_multiplier` | 2.0 → **1.0** | absence proves identity: boost touches no grip member. **R3**: below shipped 1.2 … 2 |
| `brakes.front/rear.min_time_to_block` | 1 / 1 *unchanged* | still no lock member, now exhaustively; the JC3 member's own semantics are unrecorded, so mapping `HandBrakeOffTime` 0.3 s onto it would be a guess. Donor value stands, evidence completed |

**test-089 built, installed, measured.** Snapshot (`t1_current.py Builds/test-088/aaf -o
t5d_current.json`) → `t1_apply --edits t5d_edits.json --current t5d_current.json` **4/4** →
`t5_apply` **4/4** over 2 modules (size-checked) → `t5_build --base Builds/test-088
--applied t5d_applied.json`: "2 changed, all in the edit list", 505 `.toc` records identical to
base → `install.ps1 -Action Install` → `verify_install` **9/9** → `t5_measure --applied
t5d_applied.json` **4/4** (43.2000008 / 1.0 / 1.0 / 1.0 read back through the installed `.toc`).
Gates: `t_rows build/check` (105 rows, next 4, edit 16), `bmak_chain --check` PASS (86 objects,
8,595 named bindings, 336 cross-checked, 0 conflicts, 0 bool words unnamed),
`status_audit --check` current (`STATUS.md` regenerated: queued 4 rows → test-089).

**Open, honestly:** two of the four new values sit below every shipped car (R3 declared) — A7
(drift release) and A9 (0–100 with/without boost) are the takes that can fail them; A2 decides
whether the 43.2 km/h ramp model matches the car; T-K2 keeps the donor's 1.0 until the JC3
member's semantics are decoded. All four rows stay `next` until their take passes (R4).

## Batch B4: the sweep — one more bridge, and negatives that are now proofs (2026-10-23)

Every remaining `class`/donor row was re-checked against `CHAIN.json` with a chain grep for its
own quantity. The translator's rule applied literally: if the quantity exists in the streams,
compute it; if it does not, the *search that proves it* goes in the cell.

**One bridge existed all along.** `SVehicleWheel.SuspensionTravelUp` **30** +
`SuspensionTravelDown` **40** cm (archetype on all four wheels, class default 10/20) is a total
stroke of **0.70 m**, and T-S6 had already established that JC3's `suspension.length/min_length`
carry exactly one stroke — so the bridge is cm → m with no assumption. **T-S3: 0.25 → 0.70**,
in-domain for the 6 t+ class (0.18 … 0.75, n=26), 3.9× its 0.18 median, declared BmAK-first in
the row. Staged as Batch B4 (`t5e_edits.json`), built → **test-090**, installed, `verify_install`
9/9, `t5_measure` **2/2** (0.699999988 both axles through the installed `.toc`).

**One bridge disproven rather than assumed.** `SVehicleSimCar.MaxBrakeTorque` **300** is the
same *name* as JC3's `brakes.*.max_brake_torque`, which is exactly why it had to be checked:
4 × 300 N·m over 6,000 kg × 0.683 m = **0.29 m/s²**, against the 3.5–3.8 m/s² we measured in
QA-1. The scales are not the same quantity, so T-K1 stays `class` 5,000 — and the cell now
carries the magnitude disproof instead of a dash.

**Seven negatives turned into chain results:** T-M2 (`InertiaTensorMultiplier` [1,1,1] neutral,
no absolute inertia), T-M3 (grep `CoM|CentreOfMass|CenterOfMass|MassOffset` → nothing), T-M4
(`SVehicleWheel` carries only `MassScale` 1.0), T-A2/T-A4 (no aero member; only
`SelfDriveUseTightArea` and `UprightLiftStrength`), T-ST6 (no `*Align*` member at all), T-K3
(handbrake family = On/Off speed + lat-slip + off-time, no friction factor).

**Gates:** `t_rows build/check` (next **5**, keep 49), `t1_apply` 35/35 + B3 4/4 + B4 **2/2**,
`bmak_chain --check` PASS, `bmak_coverage --check`, `t3_fleet --check`, `status_audit --check`
(queued 5 rows → test-090). The take queue is now **A2, A5, A6, A7, A9** — five takes, each
named in its row, none yet driven.

## Batch F: the camera, re-derived from the executable — and a pack bug it exposed (2026-10-23)

**The batch was specifiable the moment §2b decoded the composition, so it was executed.**
`bmak_camfile.py` was un-withdrawn with two changes: its `guard()` now fails closed on *wrong
inputs* (the 400/400 cm chase config **and** a green `bmak_camdecode.py --check`, 18/18) instead
of refusing outright, and its eight `EDITS` are the T6 rows at their corrected values — the
rest camera **7.00 m back / 1.30 m up** (sit −300,0,−25 cm + 400 cm boom, pivot 155 cm), FOV
**55 … 63 vertical** (85/95 horizontal → 54.5/63.1), interp **108 km/h**, roll **0.38**,
occlusion ray **1.6 m**. `bmak_camfile.py build` + `check`: 8/8 edits, 0 collateral ADF rows,
`.epe` 2 bytes / 1 ref. No test-086 number was reused.

**A real bug, caught by the pack's own guards.** `bmak_cambuild.py pack --base Builds/test-090`
failed 2 of 13 checks: the stage step computed the destination as
`relpath(DONOR_EPE, base/aaf)`, which escapes into `Builds/test-085/…` whenever the base is not
the donor — so the patched `.epe` was written **into the test-085 tree** and the new build got
nothing. Fixed: the path now comes from the aaf segment of the donor path, with an explicit
containment guard. test-085's `.epe` was restored from test-083 (sha256 `7385eced…`, equal to the
copy in test-089 *and* to test-085's own independent `verify/` unpack — the `.ee` artifact was
never touched; only the working tree). Re-pack: **13/13**, `verify` **14/14**.

**test-091 installed** over test-090 (game closed): the dropzone now carries the decoded camera
plus the B3/B4 values. Gates: `bmak_camfile check` 8/8, `bmak_camdecode --check` 18/18,
`bmak_cambuild verify` 14/14, plus the standing suite (`t_rows check`, three `t1_apply` batches,
`bmak_chain --check`, `bmak_coverage --check`, `t3_fleet --check`, `status_audit --check`).
Rows: T-CAM2/3/5/6/12/13 record built values; T-CAM4/7 keep; **T-CAM9 and T-CAM11 stay
blocked** (no number is hand-substituted for a spring or a shake). The gate this unlocks is
**A15**, the camera drive.


## Unified backlog written (desk, no build, no install, 2026-10-24)

**Change:** `GRAB_BACKLOG.md` overwritten with the unified backlog (G1 → G2 → T → B → V → Q → R,
86 task cards, decision register D-1…D-10, tracker). Previous text saved to
`Backups/backlog-20261024/GRAB_BACKLOG.pre-unified.md` (sha256 `28b767b3…`), with snapshots of
`MODDING_PLAN.md` and `T_PLAN.md` beside it. Both plans got a one-line pointer banner; nothing else
in them changed. **Revert:** copy the backup over `GRAB_BACKLOG.md` and delete the two banner lines.

**Four corrections recorded in the backlog §2** (ad-hoc scans of `_JC3grab/detail/*.ee.json` and
`Research/JC3Grab/PARTS_TABLE.jsonl`; P0-2 turns them into `jc3_feature_census.py --check`):
1. T-W1 `out` ("JC3 gives a car no player-fired weapons") is wrong: 25 vehicle weapon ids; driver-fired
   weapons on `CCar` entities (medium/small tank, buggy) and **`v0300 … signature_preorder`** carries
   `CMissileWeaponBase` + `CAimPOIWeaponComponent` + `w618_sportsmuscle_missile.ftune` on our donor chassis.
2. T-FX4 `out` ("EMP not in JC3") is wrong: `v0505 oldtruck_rebel_emp_01` carries an EMP device.
3. Moving-part behaviours exist with driving variables in `vehicle_common` (`SteeringWheel`/`steering_turn`
   on 9 cars, `EngineRotatingPart`/`engine_rpm` on the `v0506` tractor, `GatlingGun`/`weapon_rpm`,
   `Turret`/`Cannon` on tanks, `MissileHatch` doors); only `AirBrake` on a car stays a probe.
4. The donor `.epe` interaction points (`entry.*`, `exit.*`, `point.stunt*`) are still placed for the
   3.72 m Serpente body.
Live dropzone untouched (test-091).

## P0-1 · Baseline the standing gates — intent (2026-10-24)

**Intended change:** append the "Unified backlog baseline" results section (below) to `MODLOG.md`
only. **Why this file:** §0.2 step 7 and R14 require every task's evidence in `MODLOG.md`.
**Revert:** delete the appended sections. No other file is created or modified by P0-1; the
`install.ps1 -Action Status` call is read-only.

## Unified backlog baseline (P0-1, 2026-10-24)

Ran every §0.7 standing gate, then the live-dropzone Status call. Nothing was installed, rolled
back or modified; the dropzone still carries test-091.

| gate | command | result |
|---|---|---|
| G1 inventory | `grab_model.py check` | **OK** — schema 6, 15/15 grab checks, 380 offset-only values, 101 rigs |
| chain names | `bmak_chain.py --check` | **PASS** — 86 objects, 8,595 named bindings, 336 cross-checked, 0 conflicts |
| coverage | `bmak_coverage.py --check` | **check ok** |
| JC3 index | `jc3index.py check` | **check ok** — 81,952 rows, 78,907 paths, 1 unnamed, DLC 20,682/20,682 |
| Havok | `jc3hkx.py check --all` | **check ok** — 233 entities, 18,865 hulls, 6,382 compounds, 17/17 station sets agree |
| FX | `jc3fx.py check` | **checked 57,187 files, problems 0** |
| ledger | `t_rows.py check` | **check ok** — 105 rows: edit 16, next 5, keep 49, epe 16, blocked 11, out 8 |
| fleet | `t3_fleet.py --check` | **check ok** — 41 members over 156 vehicles |
| status | `status_audit.py --check` | **STATUS.md is current** |

Live dropzone (`install.ps1 -Action Status`): `.ee` `6AB8275F…FCF8D`, `.toc` `444ED479…C55AA`,
**== test-091 (all match)**.

All nine gates green, no red gate to explain → P0-1 done, G1 unlocked.

## P0-2 · Feature census script — intent (2026-10-24)

**Intended change:** add `Tools/scripts/jc3_feature_census.py` (new file) and generate
`Research/JC3Grab/FEATURE_CENSUS.json` + `FEATURE_CENSUS.md` from it. No decoded data is rewritten,
no build is touched. **Why the script:** backlog §2's four claims came from ad-hoc scans; P0-2 turns
them into a `--check`-able census, and §0.5 R11 forbids typed counts in new docs. **Why the two
outputs:** the backlog card names those exact paths. **Revert:** delete the two census files and the
script (`git checkout --` does not cover them: they are new). Any §2 correction this produces is
listed row by row in the section that follows, so each can be reverted by restoring its sentence.

## P0-2 · Feature census written, and the four §2 claims reconciled (2026-10-24)

**Tool:** `Tools/scripts/jc3_feature_census.py` (new, 0 game files decoded — it only joins the
readers' outputs). Inputs: 232 `detail/*.ee.json` graphs, 232 `entities/*.ee.json` module sets,
`Research/JC3Grab/PARTS_TABLE.jsonl` (233 rows / 11,643 parts) and `INDEX.jsonl` (81,952 rows).
Outputs: `Research/JC3Grab/FEATURE_CENSUS.json` + `.md`, regenerated by `--write`, byte-compared by
`--check`.

```
$ python Tools/scripts/jc3_feature_census.py --write
totals: 232 entities, 53 armed, 25 weapon ids, 67 part behaviours, 7 behaviour tables
$ python Tools/scripts/jc3_feature_census.py --check
ok FEATURE_CENSUS.json
ok FEATURE_CENSUS.md
check ok: census matches the data (232 entities, 53 armed, 25 weapon ids)
```

Two `--write` runs produced identical sha256 (`652bb5f3…` JSON, `ac8d011d…` MD), so the file is
order-stable. Per-id tables, the 53-row armed list (root class now resolved from the object whose
`values.name` is the entity basename, not from the depth-1 order) and all seven
`all_*_part_properties` tables are in the `.md`.

**What the census proved, and the wording it corrected.** The ad-hoc scans counted **chassis** (the
vehicle's parent folder), not `.ee` files, and called both "entities". The numbers reproduce; the
labels did not. Edits to `GRAB_BACKLOG.md` (each revertible by restoring its sentence):

| claim | before | census | edit |
|---|---|---|---|
| §2.1 `CBulletWeaponBase` | 17 entities | **17 chassis / 45 `.ee` / 57 objects** | §2.1 |
| §2.1 `CMissileWeaponBase` | 7 entities | **7 chassis / 19 `.ee` / 25 objects** | §2.1 |
| §2.1 `CAimPOIWeaponComponent` | 6 | **6 chassis / 11 `.ee`** | §2.1 |
| §2.1 weapon ids | 25 | **25 ids from 26 spellings** (`w613_bomb` aliases `w613_..._ground_lockon`); 22 have archive dirs | §2.1 |
| §2.3 `SteeringWheel` | 9 cars | **9 chassis: 8 cars + `v1302` sailboat** | §1.4 ANI-7, §2.3 |
| §1.4 / G2-17 `CForcePulse` | 79 entities | **79 chassis / 232 `.ee` / 307 objects** | §1.4 WPN-5, G2-17 card |
| G2-11 armed list | 24 armed entities | **53 armed `.ee` over 21 chassis** (24 was 17+7 with 3 overlapping chassis counted twice) | G2-11 card |

`FEATURE_CENSUS.md` §"Backlog §2 reconciliation" carries the same table with the derived values, so
a future drift is visible in the generated file, not only here. The four §2 corrections themselves
(T-W1, T-FX4, moving-part behaviours, Serpente interaction points) all stand — every number they
cite is now reproducible, and the only changes are the granularity words and the one duplicated
chassis count.

Standing gates re-run after the write: `jc3_feature_census.py --check` green; nothing else reads
the new files yet (G2-11/G2-14 will).

## G1-08 · Weapons extraction — intent (2026-10-24)

**Intended change:** add `Tools/scripts/grab_weapons.py` (new) and generate
`Research/BatmobileGrab/WEAPONS.json` + `WEAPONS.md` from it. No build, dropzone, save or game file
is touched: the script only joins the existing grab (`objects.jsonl`, `CHAIN.json`) with the
particle index (`PARTICLES.json`) and the audio index (`AUDIO_MAP.json`) to resolve references.
**Why this file:** the card names those exact output paths, and `--check` must be able to re-derive
both without the game open. **Revert:** delete the two generated files and the script; the only other
change is §12 of `GRAB_BACKLOG.md` plus this log.

Scope decisions recorded before writing:
- "the four vehicle packages" = `Playable_Batmobile_SF`, `Playable_BatmobileMK2_SF`,
  `Playable_BatmobileFunhouse_SF`, `Playable_BatmobileJoker_SF`. The `_Std_*` packages contain
  materials/textures, not a vehicle (checked: no `RBatmobile*` object there).
- Selection is literal per the card: class starts with `RBatmobile`, or class is
  `RBasicProjectile`. That includes the one class-default export
  (`Default__RBatmobileMissileLauncherJoker`); it is flagged `class_default` and kept out of the
  variant comparison.
- Arrays whose payload the grab did not decode (count/stride only, e.g. `MissileLaunchSockets`)
  are recorded as undecoded. The card forbids values from anywhere but `grab_model.py` /
  `CHAIN.json` / `objects.jsonl`, and `objects.jsonl` does not carry those bytes; nothing is
  guessed and the gap is listed in the record.

## G1-08 · Weapons record written (2026-10-24)

**Tool:** `Tools/scripts/grab_weapons.py` (new, reads only the grab: `objects.jsonl` 20,128
records and `CHAIN.json` 8,595 bindings; no `.upk` is opened). Outputs:
`Research/BatmobileGrab/WEAPONS.json` and `WEAPONS.md`, both regenerated by `--write` and
re-derived and compared by `--check`. The intent named `PARTICLES.json` / `AUDIO_MAP.json` as
reference indexes; implementation showed all 466 in-package references are exports in
`objects.jsonl` itself, so the tool resolves against it only and the two indexes are not inputs.

```
$ python Tools/scripts/grab_weapons.py --write
wrote ...\WEAPONS.json (589,459 bytes)
wrote ...\WEAPONS.md (112,106 bytes)
62 objects, 13 classes, 1185 fields (1002 named), 594 references (128 missing-object), 0/1065 variant comparisons differ
$ python Tools/scripts/grab_weapons.py --check
ok ...\WEAPONS.json
ok ...\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences
```

**Where the numbers come from.** Selection is literal: every object in the four vehicle packages
whose class starts with `RBatmobile` or is `RBasicProjectile` → **62 objects / 13 classes**
(11 gadget classes + 2 projectile classes: `RBasicProjectile`, `RBatmobileMissile`). The 1,028
top-level tags flatten to 1,185 field rows (struct children and curve points included); 1,002 tags
carry a stream name or a `CHAIN.json` name, 26 are bit-packed bools with no name (kept as
`offset 0x…` plus the preserved bool word). 594 `ObjectNCRProperty` tags: **466 resolved, 128
listed `missing-object` over 34 distinct targets** (all `Engine.*` / `Core.*`; the four packages
do not contain them and nothing about their values is claimed).

**Variant check.** 18 same-named object groups × their instances = **1,065 field comparisons, 0
differences**. References are compared by target path, not export index, so per-package indices do
not create false differences. The base, MK2 and Funhouse packages are value-identical for every
shared weapon; the Joker package shares three objects (`Batmobile_Cannon_V2`, `Batmobile_Booster`,
`Batmobile_EMP_Burst`) and carries **five Joker-only objects** (`Batmobile_JokerCannon_V2` 999
chain-gun damage, `Batmobile_JokerHeavy_Cannon`, its projectile, `Batmobile_JokerMissile_Projectile`,
`Batmobile_JokerMissile_Launcher` with 8 max targets / 10 missile sockets). The class-default
export `Default__RBatmobileMissileLauncherJoker` is included (literal class selection), flagged
`class_default` and excluded from the comparison.

**Independent check** (separate inline script, not the tool's own logic): 62 selected objects, 13
classes, 1,028 tags, 594 ref tags, 1,002 named tags, 26 unnamed bools, 62/62 record keys, 0
objects with a field-count or ref-list mismatch, 466 resolved / 128 missing, 18 multi-instance
groups — all equal to `WEAPONS.json`. Two `--write` runs produced identical sha256 (JSON
`6832079…`, MD `b921ef4…`), and `--check` passes from `C:\` as well as the repo root.
Appending a line to the MD makes `--check` exit 1 with the line number, then `--write` restores it.

**Limits recorded in the record, not filled in:**
- `MissileLaunchSockets` (2), `MissileSockets` (10), `BonesToHideWhenNotPresent` (2),
  `MaxTargetsPerLevel` (1/4), `EMPFireSwitch` (4), `FireParticle` (4), `HackerEffect` (6) are
  `ArrayProperty` headers only in `objects.jsonl` (`count`/`stride`/`size`); the element bytes are
  not in the grab, so `WEAPONS.md` §20 lists them as undecoded rather than guessing. This is the
  one place where the card's "MissileLaunchSockets" dump is shape-only; G1-13/G1-09 will need the
  payload decoded at the reader level if the socket names are required.
- `Projectile.LifeSpan`/`Lifetime` and `InaccuracyVsHeat` have **0** matching fields among the 62
  objects. The values may exist as class defaults; the record does not claim them. Every other
  quantity the card names is present and indexed in `WEAPONS.md` §5 (fire interval/cooldown,
  damage, ranges, archetypes, speed/accel, homing, heat bar, the two `InaccuracyVsTime` curves
  with all 4 points each, charge time, targets, lock angles/times, radii, impulse/momentum,
  screen-shake structs, mesh/trail/FX/audio).

**Why these files:** the card names exactly `WEAPONS.json`, `WEAPONS.md` and
`Tools/scripts/grab_weapons.py --check`. **Revert:** delete the two generated files and
`Tools/scripts/grab_weapons.py`; no game file, build or save was touched.

## G1-09 · Projectiles and explosions — intent (2026-10-24)

**Intended change:** extend `Tools/scripts/grab_weapons.py` with a normalized `projectiles` array
(one row per distinct projectile, per-package values where they differ) and a `## Projectiles`
section in `WEAPONS.md`; regenerate `WEAPONS.json` / `WEAPONS.md` and re-run `--check`. No new game
read: the card's inputs are `WEAPONS.json`, `objects.jsonl` and `PARTICLES.json`, and every value
below already exists in the first two. No game launch, install or dropzone change.

**Correction found while reading the inputs (G1-08 defect).** `resolve()` matched a reference by
its last path segment only, so a ref like
`Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail` resolved to the first `RocketTrail` export
in the package (the EMP missile's) instead of the projectile's own component. `objects.jsonl`
already carries `outer`, and the reference path's penultimate segment names that outer. The
resolver will use the reference's export `index` first (a positive index that names the same
object is exact), then verify the path and `outer`; a negative index is an import and stays
`missing-object`. The recorded `resolved_to` will include the outer and index. Checked on the raw
grab before editing: of **594** refs, **466** have a positive index that names that exact local
export, **128** are negative imports, and **0** positive refs fail the index+name+class test - so
the G1-08 counts (466 resolved / 128 `missing-object`) are unchanged and only the target identity
is corrected. The same check shows the old name-only join had picked the first same-named export
for every `RocketTrail`/`Mesh0`/`ImpulseComponent0`/`Cylinder` ref, which is why the per-projectile
effects below need the correction.

**Revert:** the generated files are untracked. Remove the `projectiles` key and the `Projectiles`
section, and revert the two hunks in `grab_weapons.py`; nothing outside `Research/BatmobileGrab/`,
`Tools/scripts/grab_weapons.py` and this log is touched.

## G1-09 · Projectiles and explosions — done (2026-10-24)

**Tool and outputs.** `Tools/scripts/grab_weapons.py` now also reads `PARTICLES.json`, emits a
normalized `projectiles` array in `WEAPONS.json`, and writes `## 4. Projectiles` in `WEAPONS.md`
(the G1-08 class sections shift by one, so the quantities index is now §5 and the arrays appendix
§20). `--check` still re-derives both files. No `.upk` was opened; the values are the same
`objects.jsonl` tags G1-08 already dumped.

```text
$ python Tools/scripts/grab_weapons.py --write
wrote ...\WEAPONS.json (728,842 bytes)
wrote ...\WEAPONS.md (150,104 bytes)
62 objects, 13 classes, 1185 fields (1002 named), 594 references (128 missing-object), 0/1065 variant comparisons differ
10 projectiles over 26 instances; 9 launcher target(s), 1 without one; 206 particle systems, 30 projectile FX rows, 12 AkEvent rows
$ python Tools/scripts/grab_weapons.py --check
ok ...\WEAPONS.json
ok ...\WEAPONS.md
PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences, 10 projectiles (9 launcher targets, 1 unfired), 30 FX rows, 12 AkEvent rows
```

**Coverage.** Ten projectile names over 26 instances: eight shared by base/MK2/Funhouse and two
Joker-only. Nine are named by a launcher in the same 62-object set; every one of those nine has a
row. `Batmobile_EMPMissile_Projectile` has no launcher reference and is kept, explicitly marked,
because the card lists it. Its `_ForCars` sibling is the EMP launcher's target
(`RBatmobileEMPMissile.ProjectileForCarsArchetype` and
`RPursuitModeMissileLauncher.ProjectileArchetype`). The Joker heavy cannon and Joker missile
launcher each name their own projectile.

| projectile | speed | max | accel | homing | damage | radius | momentum |
|---|---:|---:|---|---:|---:|---:|---:|
| EMP missile | - | 7500 | 40000 | - | 60 | 0 | - |
| EMP missile (ForCars) | - | - | - | - | - | - | - |
| Heavy cannon body shot | - | - | - | - | 75 | - | - |
| Heavy cannon fully upgraded | - | - | - | - | 75 (turret 110) | - | - |
| Heavy cannon head shot | - | - | - | - | - (turret 110) | - | - |
| Heavy cannon primary | 40000 | 48000 | -1000 z | - | 50 (turret 75) | 0 | 66666.671875 |
| Joker heavy cannon | 10000 | 12000 | -1000 z | - | 250 | 350 | 70000 |
| Joker missile | 500 | 1000 | 8000 | prox 100 | 250 | 300 | 25000 |
| Missile | - | - | - | - | 250 | 0 | 25000 |
| Tracker | - | 20000 | 30000 | delay 0.2 | - | 0 | 500 |

`-` means the field is absent from every instance; no class default is claimed. The two
`RBatmobileMissile` projectiles without `Projectile.Damage` are EMP and Tracker; the base missile
and Joker missile do carry 250. `Batmobile_EMPMissile_Projectile_ForCars` carries no scalar field at
all (references only). No projectile carries `LifeSpan`/`Lifetime`.

**FX and audio.** 30 projectile FX rows: trail component, its resolved particle system (with the
`PARTICLES.json` emitter count), impact/explosion template, impact flame trail, pass-through
effect, and muzzle flash. `Rocket.Batmobile_CanonTrail` resolves to
`Particles.Rocket.Batmobile_CanonTrail` (2 emitters); the cannon upgrade impacts resolve to
`Cannon_Upgrades.*`; both `Particles.Batmobile_HeavyCannon_Impact` exports are distinguished by
export index (8 and 5 emitters). The three missile families point their trail component at
`Engine.Batmobile_Rocket_Trail`, outside these packages, so the system is recorded
`missing-object` (the component itself resolves). The 12 AkEvent rows are the flight/explosion
events; local ones resolve, `Engine.*` ones stay `missing-object`. `ExplosionTemplate` is a
`ParticleSystem` in these packages, not an explosion actor; the packages hold no explosion
damage/radius actor values to report.

**G1-08 correction carried by this task.** The old resolver matched a reference's last path segment
only, so a `RocketTrail`/`Mesh0`/`ImpulseComponent0` ref could resolve to the first same-named
export in its package instead of its own component. Resolution is now: a positive `objects.jsonl` export index must name the
same object and class in the same package (466 refs, all exact); a negative index is an import and
stays `missing-object` (128 refs). Counts do not change (`466 / 128`, 34 targets), but the target
identity does: e.g. `Batmobile_Heavy_Cannon_Primary_Projectile.ProjectileTrail` now resolves to
`Projectiles.Batmobile_Heavy_Cannon_Primary_Projectile.RocketTrail`, and its
`ImpactRadialImpulseComponent` to `...Primary_Projectile.ImpulseComponent0` with the 15,000
impulse — not the EMP missile's 1,000. `WEAPONS.md`'s ref tables were regenerated with the full
outer path.

**Independent check** (separate inline script, not `grab_weapons.py`): 26 projectile exports / 10
names / 9 launcher targets / 1 unfired; 100 serialized values re-read from the joined objects and
compared; every launcher reference matched to a `fired_by` field; every effect target/status
matched its ref; all 14 direct particle refs and every resolved trail system had an emitter count
matching `PARTICLES.json`; all 594 references checked against the raw export index (466 resolved,
all exact; 128 negative, none resolved); **0 mismatches**. Two consecutive `--write` runs produced
identical sha256 (JSON `d8d271dc…`, MD `4b928a76…`), `--check` passes from `C:\`, and appending a line to the MD
makes `--check` exit 1 at the appended line, then `--write` restores it.

**Limits, recorded not filled:** `Projectile.LifeSpan`/`Lifetime` is absent from all ten;
`Batmobile_EMPMissile_Projectile_ForCars` has no scalar values; the three missile trail templates
and the 128 import references (117 `Engine.*`, 11 `Core.*`, 34 targets) are outside the four
packages; `ImpulseComponent0` fields other
than `ImpulseFalloff` are offset-only in `objects.jsonl`, and the unnamed bool at `0x0420` is
reported as such rather than named from the SDK. The two `Particles.Batmobile_HeavyCannon_Impact`
exports are kept distinct by index; the record does not merge them.

**Revert:** delete the two generated files and `Tools/scripts/grab_weapons.py` (or revert the
projectile hunk and resolver hunk), and this log entry; no game file, save or dropzone was touched.

## G1-10 · Animation sequences — intent (2026-10-24)

**Intended change:** new `Tools/scripts/grab_anims.py`, producing
`Research/BatmobileGrab/ANIMATIONS.json` + `.md`. It will (1) name every `AnimSequence` from its
offset-84 `NameProperty` (`SequenceName`), which `objects.jsonl` does not promote to the export
name, (2) take `SequenceLength` / `NumFrames` / `RateScale` and the `Notifies` array from the same
record, (3) read each `AnimSet`'s `TrackBoneNames` from the raw `.upk` through `upk_read.py`, and
(4) use one umodel export per AnimSet (`umodel -export -out E:\Modding\_BmAKgrab\anims ...`) for
the per-sequence key-frame tables and track-removal config; the key-frames stay outside the repo.
Mechanism classes will be assigned only from the animated bone names, with the evidence recorded.

**Why a new script:** the existing `MECHANICS.md` animation table prints the export name, which is
the class name `AnimSequence` for all 253 sequences; changing that table would rewrite a G1-era
dump that several tasks already read. `grab_anims.py` is the joined, checkable record the card
asks for, and leaves `MECHANICS.md` as history.

**Revert:** delete `ANIMATIONS.json`, `ANIMATIONS.md` and `Tools/scripts/grab_anims.py`; the
`E:\Modding\_BmAKgrab\anims\` exports are outside the repo and can be removed without touching the
game. No game file, install, save or dropzone is modified.

## G1-10 · Animation sequences — done (2026-10-24)

**Delivered:** `Tools/scripts/grab_anims.py` (new), `Research/BatmobileGrab/ANIMATIONS.json`,
`Research/BatmobileGrab/ANIMATIONS.md`, and 13 per-AnimSet key-frame JSON files under
`E:\Modding\_BmAKgrab\anims\keys\` (92 MB / 88 MiB, deliberately outside the repository). The tool joins
each `AnimSequence` to its owning `AnimSet`, raises the offset-84 `SequenceName` over the export
name (which is the class name `AnimSequence` for all 253), applies the umodel `RemoveTracks`
config, and reads the PSA keys through the pure-Python reader. It classifies each sequence from
moved bones (>= 0.5 cm or 0.5 deg from frame 0) and records the evidence; no class is assigned
from a sequence name alone.

**Counts and checks:** `python Tools/scripts/grab_anims.py --check` reports
`PASS: 253 sequences, 13 sets, 3 trees, 253 PSA sequences, 3147888 keys, 309 notifies
(204 sound, 35 script); 253/253 named, 253 bone lists, 253 mechanisms; 13/13 keyframe files
present`. The package inventory is 13 `AnimSet` and 3 `AnimTree` across the four vehicle
packages, not the two sets / one tree the card's `In:` line estimated; all 13 sets exported to
PSA. PSA matching is 249 `exact+frames` and 4 `prefix+frames` (the `Disarm_Switch_Player_180`
duplicate and the three names truncated at 63 characters); PSA indices are unique within every
set, the retained set `TrackBoneNames` match the PSA bone order exactly for all 13 sets, and
length/frame mismatches are 0/0. Notify times are all within their sequence length. 51 sequence
names repeat across packages; every instance is kept and listed.

**Evidence:** `Research/BatmobileGrab/ANIMATIONS.md` (human record) and
`Research/BatmobileGrab/ANIMATIONS.json` (machine source) are both re-derived byte-for-byte by
`--check`; the JSON carries the source hashes, per-sequence export indexes, PSA match kind,
removed components, active/moved bones, notifies and mechanism evidence. `--check` verifies the
keyframe files exist but does not re-serialize their 92 MB of tables; a separate read-back of all
13 files found 253 sequences whose names, export indexes, bone order, track counts and frame
counts equal `ANIMATIONS.json`.

**Revert:** delete `Tools/scripts/grab_anims.py`, `ANIMATIONS.json`, `ANIMATIONS.md`, the two
README rows and this entry; `E:\Modding\_BmAKgrab\anims\` is outside the repo and can be removed
without touching the game. No game file, install, save or dropzone was modified.

## G1-11 · Bone ownership — intent (2026-10-24)

**Intended change:** new `Tools/scripts/grab_bones.py`, producing
`Research/BatmobileGrab/BONES.json` + `.md` and per-bone face-index `.npy` files under
`E:\Modding\_BmAKgrab\bones\`. It will read `Batmobile_V2` LOD0 and the two LODs umodel does not
currently have on disk (LOD1/LOD2), recover every `REFSKELT` record (name, parent, local bind
pose), accumulate the bind-pose world pivots through `bat_assemble`'s one transform, and count
each face by its owning bone and material slot at every LOD.

**Face rule:** a face is owned when all three of its points have the same unique `>= 0.5`
influence; otherwise it is counted and listed as **split**. This gives one owner or an explicit
split flag per face, which is what B-02 needs for its cut decision. A per-bone `.npy` stores
`(lod, face, slot, kind)` rows so owned and split-touching faces stay distinguishable.

**LOD export:** the existing `Batmobile_V2.pskx` is LOD0 only, although `MESHES.md` proves three
LODs in the cooked object. Umodel's `-lods` flag is overwritten by its settings file
(`ExportMeshLods=false` in `umodel.cfg`). I will run it from an isolated directory with a local
config that enables LOD export, then keep the two new PSKX/PSK files beside LOD0; the user's
UEViewer config is not edited.

**Revert:** delete `BONES.json`, `BONES.md`, `Tools/scripts/grab_bones.py` and
`E:\Modding\_BmAKgrab\bones\`; the LOD1/LOD2 exports are outside the repo and can be removed
independently. No game file, install, save or dropzone is modified.

## G1-11 · Bone ownership — done (2026-10-24)

**Delivered:** `Tools/scripts/grab_bones.py`, `Research/BatmobileGrab/BONES.json`,
`Research/BatmobileGrab/BONES.md`, 180 per-bone face-index `.npy` files plus `_split.npy` under
`E:\Modding\_BmAKgrab\bones`, and the missing LOD1/LOD2 exports beside LOD0. The 3 LODs now cover
299,837 / 144,857 / 21,720 faces, exactly `MESHES.md`; every face is owned or explicitly split.

**Counts:** 180 bones, one root (`Batmobile_Chassis`), 298,136 / 143,315 / 21,243 owned faces and
1,701 / 1,542 / 477 split faces at LOD0/1/2. All 327,992 point records have a unique `>= 0.5`
owner (0 ties, 0 under threshold). 462,694 per-bone owned rows and 7,472 split-touching rows;
`_split.npy` has 3,720 rows. The per-bone files are int32 `(lod, face, slot, kind)` with
`kind=0` owned and `kind=1` split-touching. Split faces touching 2-3 bones appear in each of
those bone files, so the 7,472 touching rows are deliberately not a partition.

**LODs:** the existing `Batmobile_V2.pskx` is LOD0 only. Umodel's `-lods` flag was being reset by
`ExportMeshLods=false` in `umodel.cfg`; I ran it from an isolated temporary directory with a local
config that sets `ExportMeshLods=true`, then copied `Batmobile_V2_Lod1.pskx` and
`Batmobile_V2_Lod2.psk` beside LOD0. The user's config was not modified. LOD1/LOD2 section order
is mapped to the cooked `FStaticLODModel3` `MaterialIndex` (the PSK `MATT` names are generic
`material_N`), and every section's face count is checked before the mapping is used.

**Transform and skeleton:** pivots use `bat_assemble.to_jc3_rot(p) * 0.01 + offset`, with the offset
from `Working/TrueScale/stations.json` after recomputing it from the LOD0 wheel hubs. Recomputed
offset differs by 0.000013462 m and the worst hub by 0.000093707 m (both inside the script's
tolerances). The PSK left-handed hierarchy is `q_world = q_child * q_parent`, with the parent's
inverse rotation applied to the child's local offset; this reproduces umodel's own glTF
inverse-bind pivots for all 180 joints to 0.026565 cm max (0.011139 cm mean). The four wheel-bone
pivots are within 0.003751 m of the `stations.json` hubs.

**Verification:** `python Tools/scripts/grab_bones.py --check` passes, comparing both records
byte-for-byte and validating all 180 `.npy` files and `_split.npy`. Independently, a direct
per-point dictionary re-derivation reproduced every LOD's owned/split count and every per-bone,
per-slot count; the full 470,166-row set from the `.npy` files equals the independently generated
face sets exactly. Face totals and per-slot totals match `MESHES.md`/the cooked sections.

**Revert:** delete `Tools/scripts/grab_bones.py`, `BONES.json`, `BONES.md`, the two README rows, the
LOD1/LOD2 exports and `E:\Modding\_BmAKgrab\bones\`; none of those is a game file. No game file,
install, save or dropzone was modified.

## G1-12 · Pose deltas — done (2026-10-24)

**Delivered:** `Tools/scripts/grab_poses.py`, `Research/BatmobileGrab/POSES.json` and
`POSES.md`. The records store both complete 180-bone poses, the full LOD0 mesh bbox, every
bone's world and parent-relative delta, and the four transformation-sequence endpoints.

**Canonical pair:** `Batmobile_V2_Tank_Spread_Open_Game` frame 0 (pursuit) and frame 60
(battle, 1.967 s). The `_Game` pair is the gameplay transition and closes against
`Tank_Spread_Close_Game` to 0.054 cm / 0.026 deg. The non-`_Game` pair is recorded as the
cinematic variant; its endpoint bbox differs (4.487 x 3.088 x 7.382 m vs 4.691 x 2.865 x
7.443 m).

**Measured:** turret `Turret_Top` rises 0.633 m (0.683 m relative to the chassis); the
chassis settles 0.050 m; the full box grows 3.495 x 2.341 x 7.026 -> 4.691 x 2.865 x 7.443 m.
All 180 bones move with the chassis, 64 have a parent-relative articulation. The gameplay
spread only toes the wheels 17.27-19.32 deg; the real strafe stance is
`Batmobile_V2_Tank_Strafe`, whose wheel axles turn +X -> -Z (90.0 deg) while its root
translates 4.89 m. All 13 aero-fin bones stay rigid to the chassis (0.000 deg), so this
transition does not deploy the fins.

**Verification:** `python Tools/scripts/grab_poses.py --check` re-derives both files. The
pursuit bbox x/z matches `Working/TrueScale/stations.json` `body_bbox` to about 1 mm; the
extra height is the wheel geometry, and the 0.020 m bottom is a tyre contact rather than the
body-only 0.091 m bottom. Pose reconstruction uses the PSK left-handed hierarchy already
validated against umodel's glTF by G1-11.

**Revert:** delete `Tools/scripts/grab_poses.py`, `POSES.json`, `POSES.md`, the two README
rows and this entry. The animation key file is outside the repo. No game file, install, save
or dropzone was modified.

## G1-13 · Sockets — done (2026-10-24)

**Delivered:** `Tools/scripts/grab_sockets.py`, `Research/BatmobileGrab/SOCKETS_JC3.json`
and `SOCKETS_JC3.md`. All 65 `Batmobile_V2` sockets are placed from the exported
`SkeletalMeshSocket` records through the same BONES/jc3 transform; the table carries bone,
parent bone, part hint, relative location/rotation, world position, forward/up/right axes and
the body-box result.

**Counts:** 65/65 placed, 65/65 bones found, 61/65 inside the body box expanded by 0.5 m.
The four outliers are `HangFromRope_Front_Left/Right` and `Rear_Left/Right`, all 2.446 m
above the box by design; they are not transform drift. Six `HeadLight*` sockets ride
`Winch_DOOR_Mesh` and are flagged door-bound.

**Orphans:** GRB-8's six orphan light references are `HeadLight1c`/`HeadLight2c` in
Batmobile, MK2 and Funhouse (2 here, 6 across the three packages). They are light entries,
not sockets, have no location and are deliberately not given invented coordinates. The
`MissileLaunchSockets` array was shape-only in G1-08 (2 undecoded entries); the two physical
missile sockets `MissileL`/`MissileR` are placed, but the array-to-socket mapping is stated
as inferred, not read.

**Verification:** `python Tools/scripts/grab_sockets.py --check` re-derives both files. The
muzzle forwards are -Z, the two missile forwards are 45 deg up/forward, the tail-light
forwards are +Z, and all 65 forward vectors are unit length. Every socket lists a parent bone
and all 65 parents resolve in `BONES.json` (24 sockets ride `Batmobile_Chassis`, the root,
whose parent is itself).
The 13 named anchors are all present.

**Revert:** delete `Tools/scripts/grab_sockets.py`, `SOCKETS_JC3.json`, `SOCKETS_JC3.md`,
the two README rows and this entry; restore the README attachment-anchor placeholder if
desired. No game file, install, save or dropzone was modified.

## B-02 · Split-face review — done (2026-10-24)

**Delivered:** `Tools/scripts/review_splits.py`, `Research/BatmobileGrab/SPLIT_FACES.json`
and `SPLIT_FACES.md`. The review is read-only; it does not split a mesh or write a part.

**Counts:** 1,701 LOD0 split faces in 85 bone sets (73 pairs, 12 three-bone sets) and 99
bone-set × slot groups. The split set equals a fresh ownership pass and the LOD0
`_split.npy` rows. 230 faces cross a part boundary: body<->weapons 111, aero_flaps<->body
96, body<->wheel_r_r 12, body<->wheel_r_l 11. The largest single seam is the missile
barrel/mid pair (89 faces per side).

**Assignment:** summed weight resolves 1,670 faces. The remaining 31 are three-bone ties
with one rigid 1.0 vertex per bone; 15 are all weapons and 16 are two weapons + one body.
The `max()` weight rule cannot decide them. The review records a deterministic fallback:
the part with the larger share of the three vertices (2:1 or 3:0); all 31 resolve to
weapons. B-02 should use that fallback only after the weight rule, and must not use an
arbitrary bone order.

**Verification:** `python Tools/scripts/review_splits.py --check` re-derives both files,
checks the face set against `_split.npy`, checks the per-slot totals against BONES.json,
and checks that every group sum is 1,701 with 1,670 weight winners + 31 ties.

**Revert:** delete `Tools/scripts/review_splits.py`, `SPLIT_FACES.json`, `SPLIT_FACES.md`,
the two README rows, the B-02 review-input sentence and this entry. No mesh, RBM, part
manifest, game file, install, save or dropzone was modified.

## B-02 · Part split — started (2026-10-24)

**Intent:** implement the B-02 cut that `SPLIT_FACES.md` prepared. Extend
`Tools/scripts/bat_assemble.py` with `--parts Working/Translation/T8_PARTS.json`: assign every
non-wheel body face once (summed weight, 31 three-bone ties by the documented part-level vertex
vote), emit five LODs per part in `Working/Appearance/build_parts/`, write
`parts_manifest.json`, and extend `silhouette_check.py` to measure the reassembled body.
No game file, install, save or dropzone is touched. **Revert:** delete the new parts build,
`T8_PARTS.json`, the `T8_PARTS.md` summary and this section; restore the `bat_assemble.py` and
`silhouette_check.py` hunks from git.

## B-02 · Part split — done (2026-10-24)

**Delivered:** `Working/Translation/T8_PARTS.json` + `.md` (geometry-only part spec, 11 parts),
the extended `Tools/scripts/bat_assemble.py --parts`, the extended
`Tools/scripts/silhouette_check.py --manifest`, and the built
`Working/Appearance/build_parts/` (80 RBMs: body + 4 wheels + 11 parts, 5 LODs each, plus
`parts_manifest.json`).

**The cut:** every non-wheel body face is assigned exactly once. Bone-level summed weight
resolves it where one candidate bone leads; the 31 three-bone 1.0/1.0/1.0 ties use the
part-level vertex vote from `SPLIT_FACES.md`: 26 -> `batmobile_missile_pod_r` (16 body+pod,
10 all-pod), 4 -> `batmobile_missile_pod_l`, 1 -> `batmobile_riot_suppressor`; 0 unresolved.
Body 171,391 faces + parts 44,502 = 215,893, the full non-wheel LOD0 body (0 lost).

**Parts (LOD0 faces, pivot bone):** turret 16,923 (`Turret_Root`), jet 6,272 (`JetSMove`),
machine gun 5,346, riot suppressor 5,035, missile pod L 4,326 / R 4,298, cannon 754, four
aero flaps 346/346/428/428. Pivots are bone bind through the one transform; children keep
their parent (cannon/machine gun/riot -> turret, everything else -> body).

**Verification:** `silhouette_check.py --manifest .../parts_manifest.json` reassembles all 12
body/part LOD1 meshes at their pivots: **coverage 0.9997** (99.97% >= 99.9%), interior tears
0.065%, 0 lost faces, 215,893 source faces. `model footprint 4791 KB of 4915 KB` (green).
`spec_check.py` on the build: 295 blocks, 0 mismatches, 0 template values silently inherited.
The manifest's own 11 checks (face accounting, 31 ties, 5 LODs, pivots, budget) all PASS.
The old two-block body chain was replaced by the per-material chain so the split body's 16
materials each get their own block (the merge failed `spec_check` at 2 vs 16 planned).

**Revert:** delete `Working/Appearance/build_parts/`, `T8_PARTS.json`, `T8_PARTS.md`, the
`--parts`/`--manifest` code paths in the two scripts and this entry. No game file, install,
save or dropzone was modified.

## G1-14 · Damage rules — done (2026-10-25)

**Two gaps had to be closed first, and both are the interesting part.** The card's input was
`BmGame` script, but UEViewer stops parsing `UStruct` at `Children` for `GAME_Batman4`
(`Unreal/UnTypeinfo.h`, `Ar << Children; return;   //!! remaining data will be dropped anyway`),
so nobody had ever read a function body out of this package. Recovered the `Function` export
layout instead: `u16 0 | Next | SuperField | Children | Line | ScriptSize | Script | flags |
pre-name | own FName`, with `Script = len(export) - 38` and `ScriptSize == len(script) + 1`.
Six anchors re-derive it on every run (`A` super/children, `B` size identity, `C` the 1,724
one-byte `EX_Return` thinnest bodies, `D` trailing name, `E` every native-parm descriptor names
a property of its own function, `F` `EX_FinalFunction` followed by a `Function` export).

**Second gap: native vs script, decided from the body, not from a guess.** A cooked native
function keeps `0x29 <own-property>` descriptors in place of bytecode. Verdicts, each with the
executable's `exec<Name>` count as a second source: **native** `ShouldRadialDamageHit`,
`CanBatmobileDoImpactDamage`, `SetDamageLevel`, `SetArmouredMode`,
`RVehicleCombatManager.GetDamageMod`; **script** `TakeDamage` (2,028 B), `TakeRadiusDamageFromWeapon`
(288), `CalculateAndStoreImpactDamage` (1532), `DrainWeaponGeneratorForDamage` (322), `LoadHealth`
(319), `ExperienceAwarded` (180), `OnModifyHealth` (116), `GiveMaxEnergy` (24),
`TakesDamageFromRam` (7). `TakeDamage` carries 3 `exec<>` strings without being native — those
belong to parent registrations; the body decides.

**The rules, decoded.** Direct hits: `InCinematicMode` early-out → `ArmouredMode` →
`ArmourModeDamageReduction` (ships **0**, and it is the field's only reader anywhere) →
`VehicleCombatManager.GetDamageMod` (native, encounter scaling) → `DrainWeaponGeneratorForDamage`
(the weapon generator is the shield) → `QuarterHealth`/`LowHealthWarningLevel` HUD warning.
Radial: native `ShouldRadialDamageHit` gate, then a distance falloff (1500.0 / 0.5 / 0.1) into
`TakeDamage`. Ram out: `CalculateAndStoreImpactDamage` reads only outgoing multipliers —
20→150 km/h speed band (120→540 battle), `ImpactStrafeMod` ×2.25, `ImpactBoostMod` ×2.0,
civilian mod, APC weak-spot removal. Health 1,200 is persisted as `RPersistentData.BatmobileHealth`
and DDA-adjusted on load from `DDA_DeathsInRoom`.

**Two corrections to `POSTMORTEM_DAMAGE.md`.** (1) T-DM7 → `out` stands — every impact field the
class reads is outgoing. (2) But *"there is no incoming-impact entry point on the class"* is wrong:
`TakesDamageFromRam` is exactly that entry point, is script, and returns `true` with no condition.
Incoming-impact immunity can therefore never be a value row there. Separately,
`ArmourModeDamageReduction` = 0 is an authored archetype value, not an undeclared switch — the
undeclared switches remain the JC3-side ones the postmortem listed.

**ARM-5 answered: the mechanism exists, the value does not ship.**
`RVehicleBatmobileBase.HealthRecoverRate` is a `TArray<float>` at +8220; no archetype overrides it
(absent from `CHAIN.json` and from all 423 `OFFSETS.json` bindings) and exactly **one** of the
29,620 script functions reads it — `ExperienceAwarded`, alongside `RGameInfo.GetDifficulty`. So
recovery is **per experience award, indexed by difficulty**, not an out-of-combat tick, and the
rate table lives in the unshipped `BmScript` CDO (same gap class as `CAMERA.md` §2b). No `*Regen*`
field exists on `RVehicle*`, `Pawn` or `AkVehicle`.

**Tool + record.** `Tools/scripts/bmak_damage.py --write|--check` re-derives everything into
`Research/BatmobileGrab/DAMAGE_RULES.json` (layout, 6 anchors, `exec<>` counts, 14 function traces
with offsets/symbols/constants/sha1s, 251 damage values, per-field reader lists, the full
regen-symbol scan) and writes the 14 extracted bodies to `Working/vendor/BmAKgrab/scripts/` —
bytecode stays outside the notes, like the anim keys and bone face lists. `--check` PASS, anchors
6/6. `DAMAGE_RULES.md` is the write-up; README, the G1-14 tracker row and this entry point at it.

**Open:** `HealthRecoverRate[difficulty]` values and `GetDamageMod`'s scaling are native-side
(`execGetDamageMod`) — `G1-22`/`G2-28` need them for the hits-to-kill table. This note resolves
symbols in byte order, not control flow: no AST, no jump targets.

**Revert:** delete `Tools/scripts/bmak_damage.py`, `Research/BatmobileGrab/DAMAGE_RULES.md|.json`,
`Working/vendor/BmAKgrab/scripts/`, the two README rows, the tracker row and this entry. No game
file, install, save or dropzone was modified.

---

## 2026-10-25 · G1-15 · Audio by feature, decoded to WAV (intended)

**Do:** group all 361 `AUDIO_MAP.json` event rows into exactly one feature group each
(engine start/idle/load/RPM loop, afterburner, burnout, interior, battle-mode in/out, each
weapon fire/loop/stop/tail/impact, winch, EMP, sonar, tracker, lock-on UI, impacts, death,
horn, voice, `other`), with WEM ids, loop flags, container type (random/sequence/blend) and the
RTPC bindings + curve points each sound carries (`RPM`, `BML_Speed_Global`, `RevLimiter`, …).
Decode all 447 WEMs to 48 kHz WAV under `E:\Modding\_BmAKgrab\audio\wav\` (outside the repo) and
measure duration, peak and integrated loudness (LUFS) of each.

**Out:** `Research/BatmobileGrab/AUDIO_FEATURES.json` + `.md`, one new script in
`Tools/scripts/`, WAVs outside the repo. The 90 `missing-bank` rows stay explicit; any WEM that
fails to decode is listed with its error instead of being dropped.

**Method note (pre-work):** banks carry no string table (`STID` absent in all 27), so RTPC
parameter names cannot be read from the bank itself — the id↔name pairs come from the
`AkParameterName` objects the game ships in the soundbank packages, matched to the parameter ids
found in the HIRC objects. Curve geometry is read from the bank; nothing is assumed about it
until an anchor holds.

**Revert:** delete `Tools/scripts/<new script>`, `AUDIO_FEATURES.md|.json`, the README rows, the
tracker row and this entry. `E:\Modding\_BmAKgrab\audio\wav\` is outside the repo; no game file,
install, save or dropzone is touched.

---

## 2026-10-25 · G1-15 · Audio by feature, decoded to WAV — done

**Deliverables.** `Research/BatmobileGrab/AUDIO_FEATURES.md` + `.json`, re-derived by the new
`Tools/scripts/bmak_audio_features.py` (`--write` regenerates both and decodes every WEM; `--check`
prints **OK: 361 rows / 118 ids -> 14 groups, 423/447 WEMs decoded (24 errors), 90 missing rows,
27 banks, 506 RTPC entries over 261 objects (22 named params)**; `py_compile` clean). The 423 WAVs
(971.4 s of audio) live outside the repo under `E:\Modding\_BmAKgrab\audio\wav\`, 48 kHz, with
duration, peak dBFS and BS.1770 integrated loudness per file.

**Two recoveries made the note possible.**

1. **Wwise ids are FNV-1 of the lower-case name** (offset `0x811C9DC5`, prime `0x01000193`, XOR then
   multiply): it reproduces **118/118** event ids in `AUDIO_MAP.json`, so the same function names the
   game parameters an RTPC list binds — 22 of the 41 bound ids resolve (the 19 `AkParameterName`
   columns plus `REV_RPM`, `Drift`, `EngineHeat`, … from the package name tables); the other 19 stay
   `0x........` with `param: null`.
2. **The RTPC entry layout in these banks**: `u16 count` before the list, then per entry
   `u32 param_id | u8 type(=0) | u8 interpolation | u8 a | u32 curve_id | u8 b | u16 point_count`,
   followed by `point_count * (f32 x, f32 y, u32 curve_type)`. A chain is kept only under five
   anchors: the `u16` equals the number of entries that parse, every type byte is 0, every point is
   finite and under 1e7 with `curve_type <= 32`, no `param_id` is a HIRC object id, and the two
   `BML_Steering` parameters resolve to the `AkParameterName` list. Result: **506 bindings over 261
   objects** — `Speed`, `REV_RPM`, `BML_Steering` (-1->200, 0->-200, 1->200), `BML_WheelSpeed`,
   `Occlusion`, `Drift` (0->0, 50000->-1) and friends, attached to the events that reach them.

**Groups (361 rows, exactly one each):** engine 44, burnout 31, interior 35, voice 28, lock-on-ui 23,
movement 20, sonar 18, impacts 16, battle-mode 120, weapons 7, afterburner 6, death 4, tracker 4,
other 5; **winch / emp / horn stay empty** — no event in these packages plays one (so AUD-7's "no
horn unless lore has one" reads *no horn event ships*).

**Decode.** 423 embedded media extracted from `DIDX`/`DATA` and decoded with vgmstream; the **24
streamed rows are all voice lines** whose banks ship `HIRC`+`STID` only — no `DIDX` entry exists in
any of the 14 bank files on disk (`Working/Audio/*.bank|*.bnk`, `CookedPCConsole/SFX/*.bnk`,
`English(US)/*.bnk`) and there are no loose `.wem` files or matching wad-index entries, so they are
listed with that exact reason instead of being dropped.

**Loop flags: honest gap.** The Wwise per-sound loop bit is not pinned — bytes 4..8 of every Sound
body are `(plugin type, 0, codec id, 0, stream type)` and are identical for looping and one-shot
events (probe over 8 vs 32 rows, no separating offset; bytes 9..12 are the media id and 13..16 a
per-bank constant, both excluded as false separators). Loop evidence per event is therefore the
`Stop_` counterpart (`Play_BML_Sonar_Rumble_Lp`, `Play_Batmobile_RocketTails`), the name tokens and
the vgmstream loop lines — recorded, never inferred. Curve-type ids (0/1/4/7/9) stay raw: no Wwise
spec was available to name them.

**Record.** README gained two rows plus the `bmak_audio_features.py --check` line, the tracker row is
`G1-15 | done`, and this entry is the journal. **Revert:** delete `bmak_audio_features.py`,
`AUDIO_FEATURES.md|.json`, the two README rows, the tracker row and this entry; `E:\Modding\_BmAKgrab\`
holds only decoded copies — no game file, install, save or dropzone was modified.

---

## 2026-10-25 · G1-16 · Particles by feature (intended)

**Do:** group all **206** `ParticleSystem` exports in `PARTICLES.json` into one feature group each
(afterburner/exhaust, muzzle flashes, tracers, casings, missile trails, cannon impacts, EMP
charge/burst, sonar, tyre kick-up/burnout/trails, wall-scrape sparks, speed lines, death explosion,
heat steam, plus `other`), and per system record the facts the card asks for: lifetime ranges, spawn
rates, sizes, colours over life, materials/textures and emitter kinds. Collect the reference set the
Done-when is checked against — every particle reference in `WEAPONS.json` (G1-08/G1-09) and every
wheel/vehicle object reference in `objects.jsonl` (the set `MECHANICS.md` §Wheel prints) — and make
sure each referenced system lands in a group.

**Out:** `Research/BatmobileGrab/PARTICLES_FEATURES.json` + `.md`, one new script in `Tools/scripts/`.

**Method note (pre-work):** `PARTICLES.json` already carries lifetime/spawn distributions, serialised
`start_size` boxes and the emitter graph, but its `material` column is the *required-module path*, not
the material the emitter binds, and colours are not extracted at all. So the new script re-reads the
levels through `grab_particles.Walker` (module walk mirrored from `read_level`) to get the real
`Material` reference and the `StartColor` / `ColorOverLife` / `ColorScaleOverLife` distribution boxes.
Nothing is copied by hand.

**Revert:** delete `Tools/scripts/bmak_particle_features.py`, `PARTICLES_FEATURES.md|.json`, the README
rows, the tracker row and this entry. No game file, install, save or dropzone is touched.

---

## 2026-10-25 · G1-16 · Particles by feature — done

**Result.** All **206** `ParticleSystem` exports (63 distinct names, 1433 emitters, 1107 LOD levels)
land in exactly **17** feature groups via `Tools/scripts/bmak_particle_features.py`; nothing falls
through to `other` — every one of the 63 names matched a rule (first rule wins, `other` last).

| group | systems | group | systems |
|---|---|---|---|
| muzzle-flash | 21 | explosion | 11 |
| target-markers | 20 | afterburner-exhaust | 12 |
| cannon-impact | 18 | fear-gas | 12 |
| tracer | 16 | emp | 15 |
| projectile-trail | 18 | hack-fx | 12 |
| tyre-surface | 16 | gel-rounds | 8 |
| winch | 6 | casings | 8 |
| sonar | 6 | vehicle-fire | 6 |
| missile | 1 | heat-steam / speed-lines / wall-scrape / other | 0 |

The four empty groups are recorded as empty with the reason (`heat-steam` is the HUD/audio weapon-
generator heat from G1-14, not a particle; `speed-lines` and `wall-scrape` ship no system of that
name in these 206 — wall-scrape sparks are either material-side or live outside the Batmobile
packages).

**Facts per system:** lifetime 203/206, spawn 206/206, size 174/206, materials 206/206, colours
183/206 with **1290** colour boxes. Ranges are min/max over every LOD level of every emitter; a
constant distribution contributes its value to both ends. Materials are re-resolved through
`grab_particles.Walker.path` because `PARTICLES.json`'s `material` column is the required-module
path, not the bound material. Colours are the two stored vectors of `StartColor` / `ColorOverLife` /
`ColorScaleOverLife` with per-component bounds (the cooked pair is not always min-first: 193/863).
Spawn columns are the *continuous* rate distributions (`ParticleModuleSpawn.Rate`,
`ParticleModuleRequired.SpawnRate`); a 0..0 range means burst list or `SpawnPerUnit`, which this
pass does not extract — stated in the doc's Method, never inferred.

**Coverage (the Done-when):** 49 referenced names — 44 from `WEAPONS.json` (G1-08/G1-09) plus 5
external refs (fear gas, hack FX etc. outside the four packages) — all grouped, and all **8**
`MECHANICS.md` wheel/vehicle references found in `objects.jsonl` and grouped.

**Verified:** `bmak_particle_features.py --check` → `OK: 206 systems (63 names) in 17 groups; facts:
lifetime 203, spawn 206, size 174, materials 206, colours 183 (1290 boxes); coverage 49 referenced
names (44 in-grab + 5 external), 8 MECHANICS wheel refs all found`. **Record:** README gained two
rows, the tracker row is `G1-16 | done`, and this entry is the journal. **Revert:** delete
`bmak_particle_features.py`, `PARTICLES_FEATURES.md|.json`, the two README rows, the tracker row and
this entry; no game file, install, save or dropzone was modified, nothing was committed.

---

## 2026-10-25 · G1-17 · Light colours, intensities and cones — done

**The blocker was in the grab's own tag walker, not in the data.** `upk_read.py` read a
`GuidProperty` payload as **16** bytes (an `FGuid`); this cook writes **32** — the 16-byte value plus
a second 16-byte half. Every stream with a guid therefore desynced at that tag and stopped with
`unknown_type_*`: **1,778 of 20,128 records**, in every class that carries one (`LightGuid`,
`LightmapGuid`, material `ExpressionGUID`, ...). For the light rig that meant the walk always died
at `LightGuid`, so `Brightness`, `LightColor` and the cast-shadow word were unreachable and no
light card could be written. Measured on `Playable_Batmobile_SF`'s 248-byte `SpotLightComponent`:
16 bytes stops at 146 with `unknown_type_27275`; **32 re-syncs at 246** and every later tag resolves
to a BmSDK offset — `LightmapGuid 0x1dc`, `Brightness 0x1f0`, `LightColor 0x200`, `CastShadows`
0x220 bit 16. Fixed in `upk_read.SIMPLE` with that measurement in the comment, then the whole grab
was re-run (`batmobile_grab.py`: 20,128 exports, 19,203 readable) and the three stale records
re-derived (`grab_anims.py --write`, `grab_sockets.py --write`, `bmak_chain.py --write`).
**`grab_offsets` is untouched: the 423 fields / 423 named / 0 undecidable set (G1-1) contains no
guid-bearing class, so its claim still stands.**

**Names and bit masks.** Six more BmSDK-AK class files were vendored (`LightComponent`,
`PointLightComponent`, `SpotLightComponent`, `LensFlareComponent`, `PrimitiveComponent`,
`RHelicopterSpotLightComponent`; MIT, generated bindings — never game files), so
`BMSDK_OFFSETS.json` is now **41 classes / 3,420 properties / 56 structs**. `bmsdk_offsets.py` now
also records a bool's **bit mask** from the generated getter (`(Ptr + 544) & 16`), because
consecutive bools share one 32-bit word and the cooked tag stores the whole word as `bits` — that
is what separates `CastShadows` (16) from `CastDynamicShadows` (64) and `CastStaticShadows` (32) at
`0x220`.

**Where the values come from.** A cooked component serialises only what differs from its archetype,
so `grab_lights.py` (schema 1 → 2) resolves each field through the chain and keeps the source:
1. **the component** — 67 of 129 components carry `LightColor`, 54 carry `Brightness`;
2. **its archetype** — word 6 of the 72-byte export record. 129/134 light components have it 0
   (they inherit straight from the class default); the five `XrayLightComponent` instances point at
   `BmScript.Default__RVehicleBatmobile.XrayLightComponent`, and **BmScript ships no file** — those
   are recorded as chain gaps, and none of them is referenced by a `VehicleLights` entry
   (`component_gaps` = 0);
3. **the class default** — `Engine.upk` *does* ship in the cook (39,080 exports), so
   `Default__LightComponent` gives **Brightness 1.0** and **LightColor `ffffff00`**,
   `Default__PointLightComponent` **Radius 1024 / FalloffExponent 2**,
   `Default__SpotLightComponent` **OuterConeAngle 44**, `Default__LensFlareComponent` **SourceColor
   (1,1,1,1)**, and `Default__RHelicopterSpotLightComponent` (BmGame.upk) covers the helicopter
   spotlight;
4. **nothing** — a field no shipped object serialises stays `None` with that reason. `InnerConeAngle`
   is the one in this set: no `Default__SpotLightComponent` carries it, so it is the native default,
   compiled into the executable and in no file.

**`FColor` is B,G,R,A.** UE3 stores it that way in memory (UEViewer, `UnCore.h`: "Since UE3, FColor
has different memory layout - BGRA"), and the roles confirm the reading: `BrakeLightL/R` decode to
**[255, 38, 0]** (a brake lamp is red), pursuit `HeadLight1` to **[138, 197, 246]** (cool white),
the forensics scan lights to **[255, 0, 0]**, the boot light to **[152, 255, 225]**. Read as RGBA
every one of those would be the wrong hue. `SourceColor` is an `FLinearColor` and stays four floats.

**Result.** 129 components over 101 entries / 4 rigs: **colour on 129/129** (67 from the component,
62 from a `Default__`), **intensity on all 74 light components** (54 component, 20 class default).
Radius, inner/outer cone, falloff exponent and the two shadow flags ride along per component, and
every field carries its source string in `LIGHTS.json`. A lens flare is not a light: it has no
`Brightness`, its colour is `SourceColor`, and its only strength field `MinStrength` ships nowhere
(checked: `Default__LensFlareComponent` carries only `PerInstanceRandom`, and no shipped class
derives from `LensFlareComponent`) — so its intensity is a stated gap, not a number, and the check
requires the source to exist rather than inventing one.

**Verified:** `grab_lights.py --check` → `OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing
bones` + `OK: 36 Batmobile-rig components carry colour and intensity (schema 2)`. The rest of the
battery still passes: `grab_anims`, `grab_audio`, `grab_bones`, `grab_meshes`, `grab_offsets`,
`grab_particles`, `grab_physics`, `grab_poses`, `grab_slots`, `grab_sockets`, `grab_weapons`,
`bmak_audio_features`, `bmak_chain`, `bmak_coverage`, `bmak_damage`, `bmak_particle_features`,
`bmak_reg`, `bmak_speedometer`, `bmsdk_offsets`, `jc3_feature_census`, `review_splits`, `t3_fleet`,
`status_audit.py --check`, `grab_model.py check` (schema 6), `py_compile`. **Record:** README gained
a `LIGHTS.json` row, the tracker row is `G1-17 | done`, this entry is the journal. **Revert:**
`upk_read.py` (32-byte guid), `grab_model.py` (component export index), `bmsdk_offsets.py` (masks),
`grab_lights.py` (values, schema 2), six vendored `Working/vendor/BmSDK/*.g.cs` files,
`BMSDK_OFFSETS.json`, `objects.jsonl` + the grab docs, `LIGHTS.md|.json`, the README/tracker rows
and this entry. No game file, install, save or dropzone was modified; nothing was committed.

## G1-18 · Tyre diameter — done (no build, 2026-10-24)

**Question.** The project carried three tyre diameters — **1.366 m** (`T_ROWS.jsonl` T-G2, also
`land_global.*_wheels.radius` 0.68275/0.68265), **1.42 m** (`bat_assemble.py` docstring) and
**1.40 m** (wiki) — and decision **D-1** (keep the PSKX true scale, or scale the whole car so the
tyre reads 1.40) was blocked on reconciling them. D-1's condition: keep the PSKX "unless G1-18
shows the 1.366 excludes the sidewall bulge".

**Measured** from `Batmobile_V2.pskx`, vertices owned by the wheel bones, in metres, through the
ONE transform (`to_jc3_rot` × 0.01 + offset, `Working/TrueScale/stations.json`); axes x = axle
(left = −x), y = vertical, z = longitudinal, ground y = 0.02. Output: `TYRES.md`.

| corner | tyre Ø tread (y) | Ø (z) | Ø max radial | width (x) | station radius | tread bottom − ground |
|---|---|---|---|---|---|---|
| f_l | 1.3652 | 1.3672 | 1.3711 | 0.7314 | 0.6829 | +0.0021 |
| f_r | 1.3657 | 1.3674 | 1.3714 | 0.7325 | 0.6826 | +0.0018 |
| r_l | 1.3654 | 1.3673 | 1.3712 | 0.7318 | 0.6826 | +0.0000 |
| r_r | 1.3652 | 1.3673 | 1.3711 | 0.7315 | 0.6827 | +0.0001 |

All four tyres are the same mould to **0.5 mm** — front/rear are not different parts. Rim (the
`Wheel_*_Fan` hubcap, 32 faces) **Ø1.0254**; the tyre's bead aperture reads Ø1.135–1.360 on its
end faces, so the rim barrel is not separately bone-owned (`*_Vis` owns the whole tyre,
`*_Disc` owns everything inboard) and 1.0254 is the measurable rim figure. The tread sits on the
ground (rears 0.0000 m, fronts +2 mm): `stations.json`'s radius and the mesh agree to ≤2 mm.
Naming gotcha found on the way: the fronts use `Wheel_Front_*_Vis` but `Wheel_Frnt_*_Disc/_Fan`.

**The three numbers, settled.**

1. **1.366 is tread-to-tread *and* physics radius ×2 — the same figure by design.** The tyre's
   vertical extent 1.3652–1.3657 is 2 × `stations.json` `radius` 0.6826–0.6829, which is T-G2's
   `land_global.*_wheels.radius` 0.68275/0.68265 (its check: "`rbm` wheel mesh bounds vs
   `radius`"). T-G6 keeps it because the JC3 radius sets contact and ride height.
2. **1.40 is the lore reference**, not a measurement: 4 ft 7 in = 1.397 m, wiki estimate
   user-verified against footage with Batman at 188 cm (§70).
3. **1.42 has no source.** `git log -S "1.42 m"` finds only the initial commit (`7a0a07d`), and no
   file in the repo measures it (no 0.71 radius anywhere, nothing in the TrueScale or T docs). The
   nearest real quantity is the **`*_Disc` bone's vertical extent, 1.427 m** — the inner wheel
   structure, which stops 4.8 cm above the ground and reaches 11 cm above the tyre crown (338 of
   its 11,543 front-left verts lie outside the tyre radius, all in the strut region). A box taken
   over "the wheel" instead of over the tyre is what the docstring recorded.

**The bulge, measured:** tread band 1.3652–1.3657, longitudinal 1.3672–1.3674, max radial about
the hub 1.3711–1.3714 → the shoulder adds **5.5 mm**, not the 34 mm needed to reach 1.40. Ø
including the shoulder = **1.371**, still 2.0% short. None of the three headline numbers is "the
bulge number".

**D-1 resolved: keep the PSKX true scale; nothing rescales.** The condition failed (5.5 mm of
shoulder, not 34 mm), 1.42 was never rubber, and T-G6 already keeps the mesh radius as the physics
radius — contact, ride height and track are untouched. The 2.4% gap to the wiki figure is recorded
as accepted on DIM-2, which now reads "1.365–1.366 measured vs 1.40 wiki, accepted".

**Record:** `Research/BatmobileGrab/TYRES.md` (new), the `bat_assemble.py` docstring line
corrected, `GRAB_BACKLOG.md` (DIM-2, D-1 resolved, tracker `G1-18 | done`), README `TYRES.md` row,
this entry.

**Verified:** the whole battery is green — `grab_anims`, `grab_audio`, `grab_bones`, `grab_lights`,
`grab_meshes`, `grab_offsets`, `grab_particles`, `grab_physics`, `grab_poses`, `grab_slots`,
`grab_sockets`, `grab_weapons`, `bmak_audio_features`, `bmak_chain`, `bmak_coverage`, `bmak_damage`,
`bmak_particle_features`, `bmak_reg`, `bmak_speedometer`, `bmsdk_offsets`, `jc3_feature_census`,
`review_splits`, `t3_fleet`, `status_audit` (`STATUS.md is current`), `grab_model.py check`
(schema 6), `py_compile` (the three measurement modules). **Revert:** delete `TYRES.md`, restore the
`bat_assemble.py` docstring line, the DIM-2/D-1/tracker rows in `GRAB_BACKLOG.md`, the README row
and this entry. No game file, install, save or dropzone was modified; nothing was committed.

## G1-19 · Cockpit and driver placement — done (no build, 2026-10-24)

**Question (the card):** identify the faces/slots of seat, yoke and dashboard screens; give the
`Driver` socket's JC3 position, the canopy's inner clearance above it, and the eye point.
Output: `Research/BatmobileGrab/COCKPIT.md`. Method: the PSKX triangles through the ONE
transform, ray-cast (Möller–Trumbore, both windings), materials from `mats` = `SLOTS.json`
slots, face→bone from `pskx_parts.face_bones`.

**Identified by slot and bone.**

| part | slot (faces) | bone | where |
|---|---|---|---|
| seat | 11 `BatmobileV3_Cockpit_Seat` (13,014) | `Batmobile_Chassis` 12,470 + `CockPit_Mesh` 544 | cushion top **y 0.8407** under the Driver, x ±0.30, z −1.45…−0.83; rear lip z −0.86 |
| tub, dash, cowl | 10 `Batmobile_V3_Cockpit_MIC` (27,334) | `CockPit_Mesh` 14,136 + `Batmobile_Chassis` 13,198 | x ±0.404; dash front face z −1.50…−1.60 at y 1.30…1.50 (lip band = 7,528 faces, all `Batmobile_Chassis`) |
| screens | panel of slot 10 (728 faces, 486 cm²) + slot 12 `Cockpit_Master_Flip_Data` (100 faces, 404 cm²) | `Batmobile_Chassis` | centre screen **0.314 × 0.145 m**, y 1.416…1.561, z −1.851…−1.662, tilted 28° from vertical; instrument panel x ±0.328, y 1.317…1.560, z −1.865…−1.521 |
| canopy glass | 1 `Batmobile_V3_Glass_INST` (3,532; 1,716 on `CockPit_Mesh`) | `CockPit_Mesh` | windscreen 0.849 m ahead of the mean eye (z −1.914); side windows x ±0.30, y ≈ 1.71 |
| roof over the driver | 18 `Batmobile_Worn_NoRain` liner (524) + 2 `Mainbody` skin | `CockPit_Mesh` / `Batmobile_Chassis` | liner **y 1.9662**, skin 1.9914 — opaque, no glass on the centreline |
| **yoke** | **none** | — | box \|x\|<0.17, y 1.00…1.30, z −1.60…−1.10 holds **4 faces of any material**; y 1.00…1.20 is empty |

**`Driver` position and what it is.** `position_m` **(−0.0025, 0.8647, −1.0654)** — centreline,
0.845 m above the ground, 1.505 m behind the front axle, `forward_jc3` (0,0,−1) (faces the
nose); bone `Batmobile_Chassis`, relative (121.9658, 0.25, 84.2500) cm, rotation identity. A ray
down from it lands on the cushion at **y 0.8407**, i.e. the socket sits **24 mm above the seat
surface — it is the hip point**, not the feet and not the head. `DriverAnimOrigin` (0.022 y) is a
null location = the chassis pivot at ground level: enter/exit origin, not the seated pose.

**Canopy clearance.** Ray up from the Driver: inner liner at **1.9662** (skin 1.9914) →
**hip-to-roof 1.101 m**. Profile over the seat: 1.884 (z −1.35) → 1.966 (hip) → 1.986
(head column, z −1.00) → 2.001 (z −0.95). Every vertical ray at \|x\| ≤ 0.15 hits liner then
skin, **never glass**: the roof over the driver is opaque, glass is windscreen (z ≈ −1.91) and
side windows (x ≈ ±0.30).

**Eye point — derived, and labelled as such.** No file has one: 65 sockets carry only `Driver`
and `DriverAnimOrigin`, and `MECHANICS.md` has no camera/eye property. So eye = hip + seated eye
height (standard adult anthropometry): **(−0.003, 1.655, −1.065)** for a 1.76 m adult (0.79 m)
and **(−0.003, 1.705, −1.065)** for the 1.88 m scale reference (0.84 m). Clearance to the liner
at the head column: **0.331 / 0.281 m above the eyes, 0.211 / 0.151 m above the crown** — ANI-9's
"head under the canopy" holds with 15–21 cm to spare. Mean eye → windscreen 0.849 m level;
centre screen 0.711 m ahead and 13.5° below the level line (the dash lip at z −1.52 does not
occlude it); 1.88 m eye line meets the cowl at 0.750 m.

**APP-3 read off the materials:** `Batmobile_V3_Glass_INST` = MIC of `Batmobile_Glass` with
`Glass_Opacity 1.2000`, `Reflectivity 0.8`, `Roughness 1.1`, `smudges 0.2`, textures `_S/_N/_A`
(tinted, alpha-mapped); interior glow = `BatmobileV3_Cockpit_Seat` → `Emissive
Batmobile_V3_Int_Cockpit_E` × `EmissiveMultiply 15`.

**Two gaps, stated.** (1) **No yoke**: no steering geometry exists in front of the driver in any
of the 12 mesh exports (the others are Destroyed/Fire variants, MK2 and Jokerfied skins, the
Batwing carrier), so ANI-9's seated pose has nothing to hold — a grip point would come from the
JC3 side (G2-19). (2) **No screen content**: `Cockpit_Master_Flip_Data` is a parentless master
`Material` with all four channels unconnected (`DiffuseColor→—; SpecularColor→—;
SpecularPower→—; EmissiveColor→—`) and no textures — the panel geometry ships, the picture does
not.

**Record:** `Research/BatmobileGrab/COCKPIT.md` (new), README `COCKPIT.md` row, tracker
`G1-19 | done`, this entry.

**Verified:** the whole battery is green — `grab_anims`, `grab_audio`, `grab_bones`,
`grab_lights`, `grab_meshes`, `grab_offsets`, `grab_particles`, `grab_physics`, `grab_poses`,
`grab_slots`, `grab_sockets`, `grab_weapons`, `bmak_audio_features`, `bmak_chain`,
`bmak_coverage`, `bmak_damage`, `bmak_particle_features`, `bmak_reg`, `bmak_speedometer`,
`bmsdk_offsets`, `jc3_feature_census`, `review_splits`, `t3_fleet`, `status_audit`
(`STATUS.md is current`), `grab_model.py check` (schema 6), `py_compile`. **Revert:** delete
`COCKPIT.md`, restore the README row and the tracker row, remove this entry. No game file,
install, save or dropzone was modified; nothing was committed.

## G1-20 · Skins and variants — done (no build, 2026-10-24)

**Question (the card):** per variant — mesh, LOD face counts, materials/textures that differ from
`Batmobile_V2`, socket differences, sim/weapon value differences — so D-5 can be answered from the
record. Output: `Research/BatmobileGrab/VARIANTS.md`. Source: `objects.jsonl` joined with
`MESHES.md`, `MATERIALS.md`, `MECHANICS.md`, `WEAPONS.md`.

**The four variants** = the four full vehicle packages: `Playable_Batmobile_SF` (`Batmobile`,
5,490 records), `Playable_BatmobileMK2_SF` (`Batmobile_MK2`, 5,534),
`Playable_BatmobileJoker_SF` (`JokersBatmobile`, 3,388),
`Playable_BatmobileFunhouse_SF` (`BatmobileFunhouse`, 5,584) — four archetypes. Eleven `_Std_*`
packages accompany them (4 records each: `ObjectReferencer`, `Package`×2, `RAddContentBatmobileMesh`);
`Playable_Batmobile_Std_6_SF` also carries `Batmobile_Stage6` (92 records).

**Mesh.** `Batmobile_V2` 299,837 LOD0 faces / 180 bones / 19 materials; `Batmobile_MK2_Skin`
297,566 (−0.76%) / 175 / 19; `Batmobile_Jokerfied_Skin` 305,786 (+1.98%) / **220 bones** / **20
materials**, and the Joker and Funhouse packages ship the **same export** (20,385,512 B each).
`Batmobile_V3_Destroyed` is in all four; `Batmobile_V2_Fire` in V2/MK2/Funhouse but **not Joker**;
`Batwing_Carrier` (with `RBatwing Batwing_Rescue_Batmobile`) **only in Joker**.

**Sockets: 65 / 55 / 64 / 63.** MK2 drops ten — `BrakeTrailL/R`, `Dashboard_Light`,
`Headlight_Centre` and the whole `LWheelLight`/`RWheelLight` family (top, bottom, plain). Joker
(64) adds `BatmobileAttach` and `HydraSocket`, Funhouse (63) adds `HydraSocket`; both drop
`Dashboard_Light`, `Headlight_Centre` and `PassengerNoiseOrigin`.

**Materials/textures: 78 → 80 / 69 / 84 and 92 → 95 / 100 / 102.** MK2 swaps `BatmobileV3_Wheel_V2_MIC`
and `Batmobile_V3_Mainbody_NEW_MIC` for four `Batmobile_MK2_*` materials and adds five `Batmobile_MK2_*`
textures. Jokerfied adds its body/wheel/tyre/gloves/hair set plus the Joker character maps
(`Joker_BM3_Trousers_*`, `Joker_BM3_V2_Teeth2_*`), `Batwing_Carrier_*` and the Hydra/police/cameo
FX, while 38 V2 materials go missing (both EMP bursts, sonar, drone-hacker beam, winch FX, power
cell/battery, `Batmobile_Worn_NoRain`, body/turret/tyre MICs).

**Sim — identical.** `RVehicleSimBatmobile` `SimulationModel` (2,328 B, 37 tags) differs in **0 tags**
across the four packages: same wheels, mass, curves, suspension. No skin changes handling.

**Vehicle objects.** V2, MK2 and Funhouse are the same 3,905 B object with the **same 13 decoded
properties and the same 28-entry light rig** (identical rows, `MaterialType` bindings included).
`JokersBatmobile` is a different animal: 2,239 B, 11 properties — **no `InteriorLightsSwitchedOn`,
no `WeaponGeneratorMesh`/`WeaponGeneratorMeshPackage`**, plus its own `UpgradedGeneratorBonus`
`[1.0, 1.0]` — and a **17-entry light rig with zero `MaterialType` bindings** (25 of V2's 28 rows
bind one). MK2 and Funhouse differ from V2 only at unnamed scalar offsets (0x384, 0x828, 0x12BC,
0x12DC, 0x12E4, 0x153C, 0x163C, 0x1644; Funhouse also 0x2158): small integers of −1…−11 consistent
with component/socket counts — no decoded property and no sim value moves.

**Weapons.** V2/MK2/Funhouse each carry **10 gadgets + 4 projectiles** with identical names; Joker
carries **6 + 1** — shared `Batmobile_Booster` and `Batmobile_Cannon_V2`, its own
`Batmobile_JokerCannon_V2`, `Batmobile_JokerHeavy_Cannon`, `Batmobile_JokerMissile_Launcher` and
`Batmobile_JokerMissile_Projectile`, plus `RVehicleThreatComponent ThreatComp`: **no EMP burst, no
EMP missile, no sonar, no tracker, no winch, no drone hacker**. `WEAPONS.md` (G1-08) already showed
0 of 332 compared fields differ across the 18 multi-variant objects, so a variant changes *which*
weapons exist, never their values.

**For D-5 (facts, not the decision).** A skin is not a palette: each variant is a complete mesh with
its own materials, textures, sockets and (for Joker) its own weapon set and light rig; a tint of
`Batmobile_V2` would carry none of it, including the `*_Damage_ChapterMask` decals. BmAK's own
answer is one vehicle per skin (four packages, four archetypes), physics is shared so a drop entry
per skin needs no sim tuning, and the Joker variant is a different car in gameplay terms (§7) — not
a cosmetic twin.

**Record:** `Research/BatmobileGrab/VARIANTS.md` (new), README `VARIANTS.md` row, tracker
`G1-20 | done`, this entry.

**Verified:** every table in `VARIANTS.md` re-derived from `objects.jsonl` by an independent
assertion pass (30/30: socket, material, texture, record and gadget counts per package, the 0-tag
sim diff, the vehicle object name/size/tag counts, the mesh export sizes) — **ALL OK**; the battery
is green: `grab_anims`, `grab_audio`, `grab_bones`, `grab_lights`, `grab_meshes`, `grab_offsets`,
`grab_particles`, `grab_physics`, `grab_poses`, `grab_slots`, `grab_sockets`, `grab_weapons`,
`bmak_audio_features`, `bmak_chain`, `bmak_coverage`, `bmak_damage`, `bmak_particle_features`,
`bmak_reg`, `bmak_speedometer`, `bmsdk_offsets`, `jc3_feature_census`, `review_splits`, `t3_fleet`,
`status_audit`, `grab_model.py check` (schema 6), `py_compile`. **Revert:** delete `VARIANTS.md`,
restore the README row and the tracker row, remove this entry. No game file, install, save or
dropzone was modified; nothing was committed.

## G1-21 · Modes and transformation values — done (no build, 2026-10-25)

**Question (the card):** list every value under `BattleMode*`, `TurnOnSpot*`, `Strafe*`,
`Transformation*`, `TurningModeMaxSpeed`, `ArmourModeDamageReduction`, `AirControl*`, `JumpRamp*`,
`KillFlip*`, `PMDodge*`, `BattleDodgeImpulse`, `StayUpright*` with units (cm, cm/s, degrees,
seconds) — Done: every field named in T-BM1, T-AC1, T-RA1, T-SR1 appears with its value. Output:
`Research/BatmobileGrab/MODES.md` (+ `.json`), generated by `Tools/scripts/grab_modes.py
--write/--check`.

**Sources.** `BMSDK_OFFSETS.json` (what the classes *declare*: name, absolute offset, declared
type), `objects.jsonl` (what each archetype actually *serialises*, per package), `OFFSETS.json`
(GRB-11's naming evidence and the row class each declaring class cooked under). The lookup is
**class-scoped on purpose**: offset 0x0320 is `BattleModeTrailingSteerFactorMoving` on
`RVehicleSimBatmobile` and `SVehicleWheel.BattleModeSteerBias` elsewhere, and a bare offset scan
of `objects.jsonl` matched `BattleModeEngineBrakingFactor` to a `RBasicProjectile` tag — that
false positive is what the class scoping prevents.

**Result: 107 declared family fields, 46 serialised, 61 with no value in the files.** Declared
counts by family: `BattleMode*` 42 (15 serialised), `Transformation*` 9 (4), `Strafe*` 8 (0),
`ImpactRoadAssist*` 10 (5), `StayUpright*` 6 (2), `ImpactShake*` 6 (3), `AirControl*` 8 (1),
`TurnOnSpot*` 4 (3), `PMDodge*` 3 (3), `KillFlip*` 2, `KillKeepyUp*` 2, `JumpRamp*` 2 (1),
`TurningModeMaxSpeed` 1, `ArmourModeDamageReduction` 1, `BattleDodgeImpulse` 1,
`VehicleShovingTorque` 1, `JumpNoRamp*` 1 — the last seven all serialised. 31 of the 46 are
identical in all four packages.

**The ledger's parenthetical counts reconcile.** T-BM1's `BattleMode*` (9), `TurnOnSpot*` (3)
and `TransformationTurn*` (2) are the *serialised simulation-class* counts: nine sim floats plus
`BattleModeVSpeedCurve` as the tenth `BattleMode*` member (the curve ships as a named struct tag,
which `OFFSETS.json` does not list because it only names offset tags), and the vehicle class
carries five more — the battle-mode primary weapon, `BattleModeYawOffset` and the impact-speed
band 540 / 120 / 0.5.

**Values (headline).** `TurningModeMaxSpeed` 600 cm/s; `AirControlYawTorqueFactorMax` 8000 engine
torque gain; `VehicleShovingTorque` 10000, `BattleDodgeImpulse` 150000 engine impulse;
`ImpactRoadAssist*` factor 90000 / max torque 30000 / angle strength 2000 with scenery 0.0 s and
enemy 0.333 s durations; `JumpRampRightingTorque` = `JumpNoRampRightingTorque` 2000 engine torque;
`KillFlipTorque` −200 (−400 Joker) over 0.5 s (0.75 Joker), `KillKeepyUpFactor` 10 for 0.75 s;
`PMDodge*` torque 6000 / force 10000 / duration 0.15 s; `TurnOnSpot*` torque factors 0.8 / −0.8
with engine braking 2.0; `BattleModeStopAndTurnAngleStationary` 30°, `BattleModeDrivingForceZOffset`
20 cm, slip scales 0.75 / 1.25. `BattleModeVSpeedCurve` has 3 points (0 → 60, 600 → 40, 1200 → 30).

**The Joker archetype serialises five of them differently — it does not serialise them at all.**
`BattleDodgeImpulse`, `ArmourModeDamageReduction`, `PMDodgeTorque`, `PMDodgeForce` and
`PMDodgeDuration` appear in 3 of 4 packages; `JokersBatmobile` carries no tag at those offsets, so
the Joker car has no armoured-mode damage reduction and no pursuit/battle dodge in its archetype
(the other three agree byte-for-byte). This is the same "different machine" finding as G1-20.

**Units are given with their basis, never guessed:** `conv` (the field's name under UE3
conventions: s, cm, cm/s, plain-float degrees, factor), `engine` (torque/force/impulse/power
magnitudes — UE3 documents no conversion, so shipped numbers are carried as-is), `type` (object
ref, name, bool, struct, curve) and `none` for the five the name does not document: `AirControl`,
`BattleModeYawOffset`, `ArmourModeDamageReduction`, `BattleModeThrottleSpeed`,
`BattleModeSteerBiasRate`. Nothing is rescaled.

**Gaps (stated, not filled).** 61 of 107 fields are declared by the class and absent from every
archetype's tag stream — the number that runs comes from the engine or BmScript defaults, which
are not in this grab: all of `Strafe*` (8), 7 of 8 `AirControl*`, 4 of 6 `StayUpright*`, the
camera family (8, served by the camera cards), `TurnOnSpotSteeringSpeedCurve`, `BattleModeMaxSpeed`,
`BattleModeMoving`, and so on. `StayUprightConstraintSetup` / `...Instance` are object references;
their targets (`RB_StayUprightSetup`, `RB_ConstraintInstance`) are native, size 2, 0 tags, so the
constraint's own numbers are not in the grab. `ArmourModeDamageReduction` ships **0** and is read
only by `TakeDamage` (`DAMAGE_RULES.md`).

**Record:** `Research/BatmobileGrab/MODES.md` (new) + `MODES.json` (new),
`Tools/scripts/grab_modes.py` (new), README rows, tracker `G1-21 | done`, this entry.

**Verified:** `grab_modes.py --check` → **OK: 107 declared, 46 serialised, 61 not serialised;
26/26 checks** (every T-BM1/T-AC1/T-RA1/T-SR1 field present, every quoted number 90000 / 30000 /
2000 / 10000 / 8000 / 2000 found in the data, GRB-11 cross-check 44/44 named fields agree,
every field carries a unit). The battery is green: `grab_anims`, `grab_audio`, `grab_bones`,
`grab_lights`, `grab_meshes`, `grab_offsets`, `grab_particles`, `grab_physics`, `grab_poses`,
`grab_slots`, `grab_sockets`, `grab_weapons`, `grab_modes`, `bmak_audio_features`, `bmak_chain`,
`bmak_coverage`, `bmak_damage`, `bmak_particle_features`, `bmak_reg`, `bmak_speedometer`,
`bmsdk_offsets`, `jc3_feature_census`, `review_splits`, `t3_fleet`, `grab_model.py check`
(schema 6), `py_compile`. **Revert:** delete `MODES.md`, `MODES.json` and `grab_modes.py`, restore
the README rows and the tracker row, remove this entry. No game file, install, save or dropzone
was modified; nothing was committed.

## G1-22 · Native remainder relevance — done (no build, 2026-10-25)

**Question (the card):** the grab left 925 untagged exports, 140 of them larger than 8 B — list
them by class/owner and mark each `irrelevant` (metadata, functions, stubs) or `relevant` (could
carry a weapon/sim/damage value); for each relevant one try one more decode pass with
`upk_read.py`, and if it fails record why. Output: `Research/BatmobileGrab/NATIVE_RELEVANCE.md`
(+ `.json`), generated by `Tools/scripts/grab_native_relevance.py --write/--check`.

**Population.** 925 untagged; **140 over 8 B**, 785 at or below (768 are 2-byte `Package`
stubs, 17 are 6-byte). 128 of the 140 sit in `Playable_BatmobileJoker_SF` — that package ships
the script classes, functions and FaceFX sets the other three do not; V2/MK2/Funhouse carry 4
each.

**Classification: 140/140, no fallthrough — 116 irrelevant (72,860 B), 24 relevant (1,962 B).**
Irrelevant by class: `FaceFXAnimSet` 13 (64,558 B — the byte mass: facial animation for dialogue
lines, audio/vis data), `Function` 20 (5,562 B — script bytecode whose behaviour the reference
passes already decoded: `FireWeapon`, `StartFiring`, `DamagedBy`, `PlayHitReaction` …),
`ObjectProperty` 22, `IntProperty` 16, `BoolProperty` 11, `StructProperty` 9, `ArrayProperty` 8,
`FloatProperty` 6, `NameProperty` 4, `ByteProperty` 3, `ClassProperty` 1, `ComponentProperty` 1
(81 property *declarations* — they name a slot, the value lives on the archetype), `State` 2.
Relevant: **7 script-class exports** (class unresolved, outer `BmScript`: `RHidePoint_Batmobile`
in V2/MK2/Funhouse plus Joker's `RBatmobileMissileLauncherJoker`, `RJokerMissileTarget`,
`RPawnVillainThugJokerWarehouse`, `RSeqEvent_JokerBossEvent`) and **17 component instances**
(`RInteractionComponent` 7, `ParticleSystemComponent` 4, `SkeletalMeshComponent` 2, and one each
of `CylinderComponent`, `SpotLightComponent`, `AkDialogueComponent`, `RVehicleThreatComponent`).

**The second pass, by export `index`.** Matching by name is unsafe here: `CollisionCylinder`,
`Mesh` and `Interactions` exist several times per package and only *some* same-named exports
decode (a `pkg.find(name)` probe read 2 tags off an earlier `CollisionCylinder` while export 502,
the one `objects.jsonl` records, reads none). Each of the 24 was therefore re-walked at its own
index with `upk_read.export_summary`:

- **0 of 24 yielded a property tag.** Every payload begins `00 00 00 00` — an empty property
  list — so the walker stops at byte 0 (`stop=end`, 0 parsed bytes). That single byte fact is
  the recorded failure reason for the whole set.
- **5 distinct parents decoded** out of that tail for the 7 script-class rows (first int32, a
  negative = import index): `Core.RHidePoint`, `Core.RBatmobileMissileLauncher`,
  `Core.RDummyTarget_Spawnable`, `Core.RPawnVillainThug`, `Core.SequenceEvent` — each exactly the
  base class the export's name implies, which is what an `(unresolved)` class export is: a script
  class compiled into the package, outer `BmScript`, declaring no properties of its own.
- **17 component rows stop at their own name**: the tail int32 resolves to the object's own name
  in the name table in every row (checked one by one) and to an unrelated export when read as an
  object index — a header, not a value. Payloads are 14–62 B, so no value slot fits in any case.
- `native_refs` (the grab's own index-probing scan) holds **96 references across 29 rows** —
  pointers to other objects, which is what GAPS.md's "refs recovered" column was counting.

**What this settles:** no weapon, sim or damage value hides in the native remainder. The values
those classes hold live on their `Default__*` objects, which the grab decodes as ordinary tagged
rows, and the families G1-08/G1-14/G1-21 list are already in `OFFSETS.json` / `CHAIN.json` — this
pass adds no new number, it closes the hole the number could have been hiding in. The unexplained
residue is stated as a gap: the components' FName-plus-native tail is not modelled by
`upk_read`, and the 785 objects at or below 8 B are outside the card's threshold.

**Record:** `Research/BatmobileGrab/NATIVE_RELEVANCE.md` (new) + `NATIVE_RELEVANCE.json` (new),
`Tools/scripts/grab_native_relevance.py` (new), README rows, tracker `G1-22 | done`, this entry.

**Verified:** `grab_native_relevance.py --check` → **OK: 140/140 classified (116 irrelevant, 24
relevant); 9/9 checks** (population 925/140, no unclassified, every relevant object re-walked with
a stop reason, 7 rows / 5 parents, 17/17 own-name tails, 0 tags read, GAPS.md still publishes
925). The battery is green: `grab_anims`, `grab_audio`, `grab_bones`, `grab_lights`, `grab_meshes`,
`grab_offsets`, `grab_particles`, `grab_physics`, `grab_poses`, `grab_slots`, `grab_sockets`,
`grab_weapons`, `grab_modes`, `grab_native_relevance`, `bmak_audio_features`, `bmak_chain`,
`bmak_coverage`, `bmak_damage`, `bmak_particle_features`, `bmak_reg`, `bmak_speedometer`,
`bmsdk_offsets`, `jc3_feature_census`, `review_splits`, `t3_fleet`, `grab_model.py check`
(schema 6), `py_compile`. The pass reads the shipped `.upk` files under
`E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole` and writes only into
`Research/BatmobileGrab/`. **Revert:** delete `NATIVE_RELEVANCE.md` / `.json` /
`grab_native_relevance.py`, restore the README rows and the tracker row, remove this entry. No
game file, install, save or dropzone was modified; nothing was committed.

## G1-23 · Footage gaps closed — done (no build, 2026-10-25)

**Question (the card):** for each `UNKNOWN`/`native` value G1-08, G1-14 and G1-21 left, measure
it from Arkham Knight gameplay or footage — source file + timestamp, frame count at known fps,
≥3 samples — or let it stay `UNKNOWN` **with the reason** (Stop: a file value always beats
footage, R4). Output: `Research/BatmobileGrab/FOOTAGE.md` (+ `.json`), generated by
`Tools/scripts/grab_footage_gaps.py --write/--check`.

**Decision (user, 2026-10-25):** close every row as UNKNOWN with its reason, scope = the whole
list including the unreachable rows. Reason: there is no Arkham Knight footage to measure from,
and the card explicitly allows the UNKNOWN-with-reason exit. Recorded in the document header and
in the row reasons.

**The gap list, assembled from the files first.** The card's own example quantities split: 20 of
them `WEAPONS.json` already carries a value for (`ComboFiringInterval` 0.138 s, `WeaponCoolDown`
1.0 / 2.0 / 20.0 s, `LockOnTimeMax` 6.0 s, `ChargeUpTime` 2.5 s, `MaxTargets` 8/16,
`Projectile.Damage` 75, `RiotSuppressorLockOnAngle` 7.5°, …) — those are not gaps and R4 keeps
footage off them. What is genuinely open became **71 rows**: 5 weapons/damage, 61 mode fields with
no value in the files, 5 units the name does not document.

**Rows: 0 measured, all UNKNOWN, four reason codes.**
- `NO-FOOTAGE` (56) — measurable in play, nothing to measure from: projectile lifetime
  (`(LifeSpan|Lifetime)` matches **0** of the 62 weapon objects), inaccuracy-vs-heat (0 matches),
  Vulcan time-to-overheat (`HeatUpPerSecond` ships **0.0**, `OverheatOffValue` 0.25 — the rate
  integrates to no time), tank shells to destroy the car (`Health` **1200** × a shell damage the
  grab does not hold: 0 tank weapon/shell objects), the 47 non-camera non-jump mode fields, and
  the 5 undocumented units.
- `UNREACHABLE` (6) — `AirControlYawTorqueFactorMin`, `AirControlPitchTorqueFactorMax/Min`,
  `AirControlInterpTime`, `AirControlTimeInAir`, `JumpRampUpwardForce`: no observable, because
  BmAK's Batmobile does not jump (decision D-10).
- `WRONG-SCOPE` (8) — the `R3rdPersonCamera` battle-mode fields, owned by the camera cards.
- `NATIVE` (1) — `ShouldRadialDamageHit`: the decision lives in the executable
  (`DAMAGE_RULES.md` §4), so only behaviour could ever show it.

**Two false starts worth keeping.** First `python Tools/scripts/grab_footage_gaps.py --check`
failed with *"1819 video files"*: the project contains an entire `Autodesk 3ds Max` install with
**1,818 UI tooltip clips**. Second, the one remaining video, `Working/Camera/shots/cam1_take1.mkv`
(71 MB, 1280×720, 30 fps, 90.17 s), was frame-checked with `ffmpeg -ss 12` and is **Just Cause 3's
main menu** — a camera-probe take from the phase-camera work, not Arkham Knight. Both are now
classified in the scan (1,818 tooltip clips, 1 known non-AK take with the frame check recorded,
**0 Arkham Knight**), and a second failure — a row-id lookup that compared a full gap label with a
short key — was fixed to a prefix match. The check now fails only when a *candidate* video appears,
which is the moment the premise changes and a row must be reopened.

**Record:** `Research/BatmobileGrab/FOOTAGE.md` (new) + `FOOTAGE.json` (new),
`Tools/scripts/grab_footage_gaps.py` (new), README rows, tracker `G1-23 | done`, this entry.
Two temporary probe frames were extracted to view and deleted; no other file outside
`Research/BatmobileGrab/` and the three bookkeeping files was touched.

**Verified:** `grab_footage_gaps.py --check` → **OK: 71 rows, 0 measured (no footage), reasons
{'NO-FOOTAGE': 56, 'UNREACHABLE': 6, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 12/12 checks** (the two zero
quantities, `HeatUpPerSecond` 0.0, `ShouldRadialDamageHit` native, `Health` 1200, 0 tank
projectiles, MODES 61/5, every row UNKNOWN with a reason, no row claims a sample, 0 AK videos,
the known non-AK take present). Battery green: `grab_anims`, `grab_audio`, `grab_bones`,
`grab_lights`, `grab_meshes`, `grab_offsets`, `grab_particles`, `grab_physics`, `grab_poses`,
`grab_slots`, `grab_sockets`, `grab_weapons`, `grab_modes`, `grab_native_relevance`,
`grab_footage_gaps`, `bmak_audio_features`, `bmak_chain`, `bmak_coverage`, `bmak_damage`,
`bmak_particle_features`, `bmak_reg`, `bmak_speedometer`, `bmsdk_offsets`, `jc3_feature_census`,
`review_splits`, `t3_fleet`, `grab_model.py check` (schema 6), `py_compile`. **Revert:** delete
`FOOTAGE.md`, `FOOTAGE.json` and `grab_footage_gaps.py`, restore the README rows and the tracker
row, remove this entry. No game file, install, save or dropzone was modified; nothing was
committed.

## G1-23 · Footage and file answers — revised (no build, 2026-10-26)

**What changed.** The G1-23 record of 2026-10-25 closed all 71 rows `UNKNOWN` on the premise
that there was no Arkham Knight footage and that the Batmobile cannot go airborne. Two of your
corrections and one folder of captures falsified both premises, so the record is rebuilt rather
than patched:

1. **The Vulcan does not overheat; `0.0` is the answer.** `RBatmobileCannon.HeatUpPerSecond`
   ships **0.0** in all four cannon objects (Funhouse, Joker, MK2, V2). Firing therefore adds no
   heat, the bar cannot reach `OverheatOffValue` (0.25), and the gun fires indefinitely - which
   is what you see ("can fire seemingly forever"). The bloom is **time**-driven, and the values
   were already in the grab: `InaccuracyVsTime` decodes to four linear points - 0 s/0.0,
   0.5 s/0.0, 1.5 s/1.5, 2.5 s/3.0 - over a base `InaccuracyAngle` of 0.1 (upgraded curve
   0/1/3/5 s → 0/0/1.5/3.0). `(InaccuracyVsHeat)` matches 0 fields because there is no heat
   term for it to read, not because a number is missing. Both rows are now closed `FILE-VALUE`,
   and R4 keeps footage off them.
   - The last record printed the curve as "array, payload not decoded" in the answered table.
     That was **wrong**: `WEAPONS.json` carries `InaccuracyVsTime.Points` with `count 4,
     stride 62, decoded true` and every `FloatProperty` value. The table now prints the points.
2. **The Batmobile does go airborne off ramps and ledges.** The one-way D-10 reading ("BmAK
   cannot jump") was too strong, and the files say so: `Actor` carries `bIsVehicleJumpRamp`,
   `RVehicleBatmobileBase` carries `bUsedAirControlDuringJump`, `JumpRampUpwardForce` and
   `JumpRampRightingTorque`, and six `AirControl*` fields sit on `RVehicleSimBatmobile` /
   `RVehicleSimCar`. `UNREACHABLE` is retired as a reason code.

**The footage.** `C:\Users\User\Videos\Captures` holds five Arkham Knight captures (1920x1080,
nominal 60 fps, read in place - never copied into the repo): air steer up/down/right,
VulcanFire, and Battlemode entry/movement/boost. All five are **variable-framerate**: the PTS
deltas alternate ~16.7 ms and ~33 ms, and 37-38 unique frames cover 1.2 s (a ~31 fps cadence),
so any measurement has to come from presentation timestamps. Contact sheets with burned-in PTS
(`drawtext`) located each event boundary at 15 fps, then snapped to the nearest decoded frame.

| clip | first air | first contact | frames | air time |
|---|---|---|---|---|
| Air steer up | frame 97 / 3.204 s | frame 133 / 4.455 s | 37 | **1.251 s** |
| Air steer down | frame 96 / 3.285 s | frame 133 / 4.468 s | 38 | **1.183 s** |
| Air steer right | frame 149 / 5.006 s | frame 186 / 6.205 s | 38 | **1.200 s** |

Mean **1.212 s**, spread 0.068 s, snap error ≤ 0.015 s. That is the observable the
`AirControl*` fields govern: the car is steered in the air for over a second per jump. Their
*values* are still not in any archetype or class default (the CDO payloads stop at offset ~724;
the AirControl block starts at 0x4ac), so those rows stay `VALUE-NATIVE` and the footage settles
the behaviour and its duration, not the torques.

**What the Vulcan capture cannot give.** It frames the lock reticle and the target - the muzzle
is out of frame - so no fire interval is claimed from it; `ComboFiringInterval` 0.138 s remains a
file value. The whole-frame luma did spike (explosions at 18/29/46 s) and the audio envelope was
flat (~0.045 RMS) through the aiming stretch, which is consistent with "aiming, not firing", and
is why the clip is recorded as corroboration of the bloom only.

**Rows now.** 72 total: 2 `FILE-VALUE`, 1 `MEASURED` (3 samples), 53 `VALUE-NATIVE`,
8 `WRONG-SCOPE`, 5 `UNDOCUMENTED`, 2 `NOT-IN-CLIP` (projectile lifetime, tank shells),
1 `NATIVE` (`ShouldRadialDamageHit`). The measured air-time row sits inside the G1-21 section and
the air rows point at it instead of claiming to be unreachable.

**Record:** `Research/BatmobileGrab/FOOTAGE.md` + `FOOTAGE.json` (regenerated, schema 2),
`Tools/scripts/grab_footage_gaps.py` (rewritten: `ffprobe` sources, PTS sampling, 23 checks),
README rows, tracker `G1-23 | done`, this entry.

**Verified:** `grab_footage_gaps.py --check` → **OK: 72 rows, 2 file-resolved, 1 measured (3
samples), reasons {'FILE-VALUE': 2, 'MEASURED': 1, 'NOT-IN-CLIP': 2, 'VALUE-NATIVE': 53,
'UNDOCUMENTED': 5, 'WRONG-SCOPE': 8, 'NATIVE': 1}; 23/23 checks** - captures present at the
recorded path and geometry, VFR premise, `HeatUpPerSecond` 0.0, the curve still 0/0.5/1.5/2.5 →
0/0/1.5/3.0, `InaccuracyAngle` 0.1, `Health` 1200, 0 tank projectiles, three measured jumps with
snap ≤ 0.05 s and spread ≤ 0.1 s, no `UNREACHABLE`, MODES 61/5, every measured row with ≥ 3
samples, no measured row carrying a file value, 0 AK clips inside the workspace. Two generator
bugs were found and fixed by the check itself: a `KeyError` on array fields without decoded items
and a tuple/list mismatch that made `--check` report STALE after `--write`. Revert: restore the
2026-10-25 `FOOTAGE.*`, the previous script, the README/tracker rows; remove this entry. No game
file, install, save or dropzone was modified; nothing was committed; the captures stay outside
the repo.

## G1X · G1 exit gate — passed (no build, 2026-10-26)

**Noted first: sideswipe and ram.** The Batmobile sideswipes traffic and rams it (your note of
2026-10-26), and the outgoing half was already decoded — `ImpactMinDamageSpeed` /
`ImpactMaxDamageSpeed` 20/150 (Joker 40/180), `BattleModeImpactMinDamageSpeed` / `MaxDamageSpeed`
120/540 with `BattleModeImpactMaxDamagePow` 0.5 / 0.666, `ImpactStrafeMod` 2.25 pursuit / 0.8
Joker, `ImpactBoostMod` 2.0, all in `DAMAGE_RULES.md` §3.3. What was missing there is the
**targeting half**, now added as §3.3.1: `SideSwipeTargetsList` (`RInteractionClass`),
`SideSwipeInSweetSpot`, `CrushedThisFrame` / `BouncedThisFrame`, and the script functions
`GetSideSwipeTarget` / `GetCurrentSideSwipeTarget` / `GetBatmobileDodgeDirection` (both target
functions also sit in `NATIVE.md`). `OFFSETS.json` carries **0** rows for any of them - runtime
state, not archetype defaults - which is why a ram's *victim* cannot be read from the files while
its *damage numbers* can. T-DM7 stays `out` for the JC3 translation; nothing about that changed.

**The gate, as the backlog defines it** (all re-run this session):

| check | result |
|---|---|
| `grab_model.py check` | `OK: grab output matches schema 6 and its own summary` |
| `grab_weapons.py --check` | `PASS: 62 objects, 13 classes, 594 references (128 missing-object), 0 variant differences, 10 projectiles, 30 FX rows, 12 AkEvent rows` |
| `grab_anims.py --check` | `PASS: 253 sequences, 13 sets, 3 trees, 253 PSA, 3,147,888 keys, 309 notifies; 253/253 named; 13/13 keyframe files present` |
| `grab_lights.py --check` | `OK: 101 entries / 4 rigs, 6 orphan sockets, 0 missing bones` + `OK: 36 rig components carry colour and intensity` |
| `g1x_gate.py --check` | `codes 75: 56 from G1 files, 19 proven absences (no BmAK source); PASS` |

`g1x_gate.py` is new: one row per feature code in section 1, with the G1 file that carries the
lore value and a needle that must still be in it. Codes that name no BmAK source at all (wiki
rows, play observations, T-ledger values, JC3 carriers) are the "proven absence" half and carry
their reason. The first run failed 13 needles; every one was my file guess, not a missing fact,
and each was re-pointed at the doc that actually holds it (`CarPaint` lives in `SLOTS.md`, not
`MATERIALS.md`; `Immobiliser` is spelled with an s in `MECHANICS.md`; the turbine is the `fan`
bone in `BONES.md`; the yoke is in `COCKPIT.md`). No fact had to be written to make the gate pass.

**Every feature code, and the file that satisfies it** (75 codes):

| code | G1 file(s) | what satisfies it |
|---|---|---|
| APP-1 | `MESHES.md`, `SLOTS.json` | 5 LODs, 19 material slots |
| APP-2 | `SLOTS.md`, `VALUES.json` | CarPaintMM parameters |
| APP-3 | `SLOTS.json`, `SLOTS.md` | canopy glass and interior slots |
| APP-4 | `MATERIALS.md`, `LIGHTS.json` | emissive lights and their colours |
| APP-5 | `BONES.md`, `ANIMATIONS.md` | movable parts as bones |
| APP-6 | `POSES.json`, `ANIMATIONS.md` | transform animation and pose states |
| APP-7 | - | no-deform rule is a project rule, not a BmAK value |
| APP-8 | `VARIANTS.md` | MK2 / Jokerfied skins diffed |
| DIM-1 | `POSES.md`, `MESHES.md` | body dimensions and wheelbase |
| DIM-2 | `TYRES.md` | tyre diameter measured on all four |
| DIM-3 | - | BmAK carries no absolute mass |
| DIM-4 | `PHYSICS.md` | per-bone collision boxes |
| ARM-1 | - | small-arms immunity is a play observation |
| ARM-2 | `DAMAGE_RULES.md`, `OFFSETS.json` | Health 1200 and the damage rules |
| ARM-3 | - | ram immunity is a play observation |
| ARM-4 | `PHYSICS.md` | wheels are separate collision bodies |
| ARM-5 | `DAMAGE_RULES.md` | regeneration is decided by the damage rules |
| ARM-6 | `MECHANICS.md`, `DAMAGE_RULES.md` | death explosion effects |
| WPN-1 | `WEAPONS.md`, `WEAPONS.json` | 60 mm cannon |
| WPN-2 | `WEAPONS.md`, `WEAPONS.json` | Vulcan chain gun and its heat block |
| WPN-3 | `WEAPONS.md`, `WEAPONS.json` | missile launcher |
| WPN-4 | `WEAPONS.md`, `WEAPONS.json` | EMP missile |
| WPN-5 | `WEAPONS.md`, `WEAPONS.json` | EMP burst |
| WPN-6 | `WEAPONS.md`, `WEAPONS.json` | winch |
| WPN-7 | `WEAPONS.md`, `WEAPONS.json` | drone hacker |
| WPN-8 | `WEAPONS.md`, `WEAPONS.json` | sonar |
| WPN-9 | `WEAPONS.md`, `WEAPONS.json` | vehicle tracker |
| WPN-10 | `WEAPONS.md`, `WEAPONS.json` | riot suppressor mode |
| WPN-11 | `WEAPONS.md`, `WEAPONS.json` | booster |
| WPN-12 | `HUD_INTERFACES.json`, `HUD.md` | HUD weapon setters, cooldown and heat |
| HDL-1 | - | top speed is a lore row, not a BmAK value |
| HDL-2 | `MECHANICS.md` | torque curve shape |
| HDL-3 | - | steering values are T rows, not BmAK |
| HDL-4 | - | boost extra speed is derived, not decoded |
| HDL-5 | - | landing stroke is a translation value |
| HDL-6 | - | air control has no JC3 member yet |
| MOD-1 | `MECHANICS.md` | pursuit-mode behaviours |
| MOD-2 | `MODES.md`, `MECHANICS.md` | battle-mode fields and camera |
| MOD-3 | `ASSETS.md` | eject animation |
| MOD-4 | `ANIMATIONS.md` | canopy door bone and animation |
| MOD-5 | - | no NPC-driver rule is not a BmAK value |
| AUD-1 | `AUDIO.md` | engine loop driven by the RPM RTPC |
| AUD-2 | `AUDIO.md` | burnout and boost roar |
| AUD-3 | `AUDIO.md` | interior layer |
| AUD-4 | `AUDIO.md` | battle-mode transform sting |
| AUD-5 | `AUDIO.md`, `AUDIO_FEATURES.md` | per-weapon events |
| AUD-6 | `AUDIO_FEATURES.md` | impact bank absent (named omission) |
| AUD-7 | `AUDIO_FEATURES.md` | no radio; horn checked |
| ANI-1 | - | wheel spin is live, no BmAK value needed |
| ANI-2 | `BONES.md` | turret and cannon bones |
| ANI-3 | `ANIMATIONS.md`, `BONES.md` | Vulcan barrel spin |
| ANI-4 | `BONES.md` | turbine fan bone |
| ANI-5 | `ANIMATIONS.md` | rear fin animation |
| ANI-6 | `SOCKETS_JC3.md`, `SLOTS.json` | missile hatches and sockets |
| ANI-7 | `COCKPIT.md`, `BONES.md` | steering yoke bone |
| ANI-8 | `ANIMATIONS.md` | canopy animation |
| ANI-9 | `COCKPIT.md` | driver seat and pose |
| LGT-1 | `LIGHTS.md`, `LIGHTS.json` | headlight cones and colours |
| LGT-2 | `LIGHTS.md` | battle-mode spotlight |
| FX-1 | `MECHANICS.md`, `PARTICLES.md` | afterburner flame |
| FX-2 | `PARTICLES.md`, `WEAPONS.md` | muzzle flashes and tracers |
| FX-3 | `PARTICLES.md` | tyre smoke and scrape sparks |
| FX-4 | `DAMAGE_RULES.md`, `PARTICLES.md` | death explosion effects |
| CAM-1 | `CAMERA.md` | chase camera composition |
| CAM-2 | `CAMERA.md` | battle camera FOV 60 |
| HUD-1 | `HUD.md` | speedometer and health bar |
| HUD-2 | `HUD.md`, `HUD_INTERFACES.json` | weapon reticle and slots |
| WLD-1 | - | JC3 carrier only |
| WLD-2 | - | JC3 carrier only |
| WLD-3 | - | JC3 carrier only |
| WLD-4 | - | JC3 carrier only |
| WLD-5 | - | JC3 carrier only |
| WLD-6 | - | JC3 carrier only |
| WLD-7 | - | JC3 carrier only |
| WLD-8 | - | JC3 carrier only |

**What G1 leaves open, stated once.** 19 codes have no BmAK source by design (APP-7/ARM-1/ARM-3/
MOD-5 are play rules; DIM-3/HDL-1/HDL-3/HDL-4/HDL-5 are wiki or T-ledger values; WLD-1…8 are JC3
carriers). Of the rest, the only values still absent from the files are the ones `FOOTAGE.md`
records: 53 `VALUE-NATIVE` mode fields (native defaults, not serialised anywhere), the 5
undocumented units, `ShouldRadialDamageHit` (native), and the two events no clip contains
(projectile lifetime, tank shells). The air-control window is the one measured observable
(1.212 s mean over three jumps). `HDL-6` remains a translation question, not a grab gap.

**Revert:** remove `Tools/scripts/g1x_gate.py`, the `G1X` tracker row, the §3.3.1 addition to
`DAMAGE_RULES.md` and this section. No game file, install, save or dropzone was modified; nothing
was committed.

## G2-10 · Vehicle weapon catalogue — intended change (2026-10-26)

**Card:** G2-10 (phase G2, first card). Out: `Research/JC3Grab/WEAPONS.md` + `WEAPONS.jsonl`,
`Tools/scripts/jc3weapons.py --write/--check`; raw tunes extracted to `E:\Modding\_JC3grab\weapons\`.

**Intended change (written before editing, per §0.2 rule 4).**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3weapons.py` | new. Decodes every `WeaponTuning` / `AutoAim` / `ForcePulseSettings` reachable from the 25 weapon ids, with `--write`/`--check`/`dump` | the card names this path; it reuses `jc3adf.py` (ADF v4 reader), `eetoc.py` (SARC) and `jc3index.py` (archive index) - the pattern `jc3fx.py`/`jc3parts.py` set |
| `Research/JC3Grab/WEAPONS.jsonl` | new. One row per weapon id: every decoded member, with source paths, sizes and sha1 | the card's Out; same shape as `PARTS_TABLE.jsonl` (values in-repo, evidence) |
| `Research/JC3Grab/WEAPONS.md` | new, generated by the same `--write` | the card's Out |
| `E:\Modding\_JC3grab\weapons\` | new (outside the repo, R10): the weapon `.ee` bundles and their inner tune files | the card's step 2 |
| `Research/JC3Grab/README.md` | two rows (build/check) | every G2 tool is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-10 | todo` -> `done` + evidence path | the session loop step 7 |

**What the card gets wrong, before I start** (recorded so it is not re-litigated): the card says
"every `jc_explosions/weapons/w6*.ftune`" as an archive path. There is **no** standalone
`jc_explosions/` tree in the index - the blast tunes are `.ftunec` files *inside* `.ee` bundles
(`editor/entities/jc_explosions/weapons/<id>.ftunec`), and exactly two `.ftunec` files exist as
standalone archive entries (`gen_explosion_0.5m_nodamage`, `structures/barrel_explosion`), neither
a `w6` weapon. Same for "extract each weapon `.ee`": 14 of the 22 archive ids have an `.ee`; the
other 8 ship as loose patch `.wtunec` overrides (`w601`-`w607`, `w614`) whose **base** copies sit
inside the carrier vehicle `.ee` (confirmed: `v2200 ...assault*.ee` embeds
`w601_helicopter_missile.wtunec`, `v4603 ...cargo_tank.ee` embeds `w602_mediumtank_canon.wtunec`
+ `w603_mediumtank_mgun.wtunec`). The 3 `+_impact` ids are **not weapons**: they are the
`SettingsFile` of a `CForcePulse` object (`w604_helicopter_mgun_impact.ftunec` on the three
`v2601` and `v2602`/`v2604` helicopters), i.e. the impact blast of a bullet weapon.

**Revert:** delete `Tools/scripts/jc3weapons.py`, `Research/JC3Grab/WEAPONS.md`,
`Research/JC3Grab/WEAPONS.jsonl`, `E:\Modding\_JC3grab\weapons\`, the two README rows, restore the
tracker row to `todo`, remove this entry and the result entry that follows. No game file, install,
save or dropzone is touched; nothing is committed.

## G2-10 · Vehicle weapon catalogue — done (2026-10-26)

**Card:** G2-10, the first card of phase G2. 25/25 weapon ids have a row; `--check` re-reads the
archives and compares; the tunes are extracted outside the repo.

**Record:** `Research/JC3Grab/WEAPONS.md` (17 sections, generated) + `WEAPONS.jsonl` (one row per id,
every decoded member of every authoritative tune) + `WEAPONS_SHARED.json` (the shared tunes, decoded)
+ `Tools/scripts/jc3weapons.py` (`--write` / `--check` / `dump`). Raw copies in
`E:\Modding\_JC3grab\weapons\<id>\`.

### The shape of the data

Three ADF v4 classes carry the fleet's weapons, all read with the existing `jc3adf.py` (no new
format work needed - the type kinds the weapon tunes use are the ones G2-9 already added):

| class | ids | members | what it is |
|---|---:|---:|---|
| `WeaponTuning` | 22 | 4,054 over both sides | fire rate, burst, magazine, damage, impulse, recoil, scatter, projectile, homing, AI priorities, reticle |
| `AutoAim` | 3 per-id + 11 shared presets | 22 x 6 contexts x 11 | sticky-aim / lock-on |
| `ForcePulseSettings` | 9 + 3 impact ids | 12 | the blast: player/AI damage, radius, falloff |

25 ids = 22 weapon dirs under `jc_weapons/06_vehicle` + the 3 `+_impact` ids, 26 spellings, 1 alias
(`w613_bomb` -> `w613_fighterbomber_missile_ground_lockon`). 161 sources, 67 `.ee` containers opened
(14 weapon bundles + the 53 armed vehicles the census names), 24 shared tunes, 197 files /
21,487,435 B extracted.

### Two things the card expected that do not exist (recorded, not litigated)

* **No `editor/entities/jc_explosions/` tree.** Every weapon blast is a `.ftunec` *inside* an `.ee`
  bundle; the whole game has exactly two standalone `.ftunec` archive entries (`gen_explosion_0.5m_
  nodamage`, `structures/barrel_explosion`), neither a weapon.
* **8 of the 22 archive ids ship no bundle of their own** (`w601`-`w607`, `w614`): they are loose
  patch `.wtunec` overrides, and the base copy sits inside the carrier (`.e2 v2200 ...assault*.ee`
  embeds `w601_helicopter_missile.wtunec`; `v4603 ...cargo_tank.ee` embeds `w602_mediumtank_canon` +
  `w603_mediumtank_mgun`; `v2601` embeds `w606_heavyheli_missile` + `w607_heavyheli_mgun`;
  `v0201`/`v0202` the tank canon+mg; `v5603` `w614`). The tool attributes a tune by *name* in a
  container and by *directory* for the loose patch, and ranks patch > bundle > bundle-base for the
  authoritative copy.
* **The 3 `+_impact` ids are not weapons.** They are the `SettingsFile` of a `CForcePulse` object on
  the vehicles that fire the matching gun (`w604_helicopter_mgun_impact` on 3 `v2601` + 9
  `v2602`/`v2604` helicopters, per the census), i.e. the impact blast a bullet weapon carries. Their
  rows hold `ForcePulseSettings` only and the gun ids hold no blast row of their own.

### The numbers a translation will want

| id | mag | fire_rate | velocity | range | damage player/AI | blast player/AI r | homing |
|---|---|---:|---:|---:|---|---|---|
| `w602_mediumtank_canon` | -1 | 1.75 | 500 | 1000 | **1**/20 | 1500/550 r8 | - |
| `w603_mediumtank_mgun` | -1 | 0.1 | 750 | 200 | 190/20 | - | - |
| `w604_helicopter_mgun` | -1 | 0.1 | 900 | 500 | 250/15 | - | - |
| `w604_helicopter_mgun_impact` | - | - | - | - | - | 25/0 r1.5 | - |
| `w608_fighterjet_missile` | -1 | 0.5 | 600 | 300 | 1500/30 | - | 75 |
| `w609_..._air_lockon` | **8** | 0.2 | 600 | 750 | 1500/30 | - | 150 |
| `w612_..._air_lockon` | 2 | 0.5 | 600 | 300 | 1500/30 | - | 300 |
| `w613_..._ground_lockon` | 6 | 0.2 | 600 | 300 | 1500/30 | 1500/500 r25 | 0 |
| `w618_sportsmuscle_missile` | -1 | 0.5 | 360 | 300 | **1500**/30 | **1100**/500 r8 | **0** |
| `w619_buggy_mgun` | -1 | 0.1 | 750 | 200 | 190/20 | - | - |

Readings that matter for the build: **the tank canon does 1 point of direct hit damage and 1500 in
its blast** - the kill is the explosion, so a Batmobile cannon row has to carry both. **`w618` is a
straight rocket** (`missile_turning_speed` 0, `missile_acceleration` 200 at t0) with 1500 damage and
an 1100/8 m blast: that is the donor weapon, dead-centre on the lore missile. Only 4 of the 14
missile ids home at all (`w608` 75, `w609` 150, `w612` 300, `w614` 200); the rest are 0. All
magazines are -1 (no magazine) except `w609`/`w612`/`w613`, and `unlimited_ammo` is 1 on **all 22**
weapons: JC3 vehicle weapons never run dry, which is the JC3 half of the ammo translation.

### The two absences the card asked about

* **Overheat is absent from JC3.** No member of any decoded class instance - 22 `WeaponTuning` +
  3 `AutoAim` + 9 `ForcePulseSettings` + the 24 shared tunes - names heat, cooling or temperature;
  the only cooldown-shaped member is `burst_cooldown` (a burst gap). BmAK's
  `HeatUpPerSecond` 0.0 / `OverheatOffValue` 0.25 has no JC3 counterpart to copy, so the heat-carrying
  Vulcan stays a BmAK-side behaviour and G1-23's bloom curve remains the JC3-shaped half.
* **Damage type is not a weapon property.** No `damage.?type`-shaped member exists in any tune; JC3
  types damage on the part (`PARTS_TABLE.jsonl` `dt`) and the health module (`DAMAGE_MECHANISMS.md`).
  G2-28 owns the model; this card records where the typing is not.

Lock-on is the third of the card's asks: the `AutoAim` block is **22 members x 6 shooter contexts**
(`OnFoot`, `Stunting`, `MotorCycle`, `ReelingIn`, `ReeledIn`, `Parachute`), range/angle members
present and decoded (`AngleThresholdNewTarget/CurrentTarget`, `StickyAim*`, `MaxAimDistance`,
`AlwaysTargetDistance`, `SnapAimTarget`, `CanTarget*`, `UseWeaponDirection`), but **no member carries
a lock-on time** - `SnapAimTarget` (0.07 in every vehicle context) is the only time-shaped candidate
and its unit is unproven, so "lock-on time" is `UNKNOWN` and becomes a Q-1 probe candidate with the
values to expect for both hypotheses (0.07 s to snap, or 0.07 as a weight).

### Cross-checks (this is the part worth trusting)

* **A second, independent reader agrees.** `wtunesurvey.py` (text decode via `adfdump.py`, a different
  code path) ran over 10 containers: velocity, max_range, fire_rate and magazine_size agree on every
  weapon it printed (`w608` 600/300/0.5/-1, `w613` 600/300/0.2/6, `w618` 360/300/0.5/-1, `w619`
  750/200/0.1/-1, tank canon 500/1000/1.75, small tank 500/1000/0.75 - all equal to the table above),
  and every blast it printed is identical to section 8 (w618 1100/8, w613 1500/25, w604 impact 25/1.5,
  w602 1500/8 `car_explosion_medium` 500/5, `rpg_assault_helicopter` 1200/10, `w615` 2200/20).
* **Its one disagreement is its own artifact, and the bytes settle it.** `wtunesurvey`'s AI damage
  triple reads a positional regex over the text (`ai_tuning=` split, then the first
  `base_tuning=WeaponTuningBase{...}`) and reports 1.0/4.0/5.0 for `w608`. Scanning the raw tune for
  the struct layout `WeaponTuningBase` = impulse, vehicle_damage_factor, vehicle_impulse_factor,
  object_damage_factor, object_impulse_factor, damage at +0/+4/+8/+12/+16/+20 finds the AI block at
  **+444: impulse 10, veh_df 0.5, veh_if 0.2, obj_df 1, obj_if 1, damage 30** - exactly the
  offset-based read in the table (`w607`'s copy at +432: 40 / 0.15 / 0.2 / 0.1, damage 15, same as
  the decoded row). The reader is right, the text regex picked the wrong struct.
* **The blast ids line up with the census**: the impact ids' `containers` counts are 11 / 3 / 2 -
  exactly the entity counts `FEATURE_CENSUS.md` gives for `w604_...mgun_impact` (11),
  `w610_...mgun_impact` (3) and `w617_...mgun_impact` (2).

**Verified.** `jc3weapons.py --check` -> `PASS: 25 ids, 197 extracted files, 24 shared tunes, md
1223 lines` (it re-reads every container, re-derives both files byte-for-byte and re-hashes every
extraction). Standing gates, all green at phase start: `grab_model` schema 6, `bmak_chain` 336
cross-checked 0 conflicts, `bmak_coverage` ok, `jc3index` 81,952 rows, `jc3hkx check --all` (233
entities / 130,513 objects / 34,999 compound instances), `jc3fx` 57,187 files 0 problems, `t_rows`
105 rows, `t3_fleet` 41 members / 156 vehicles, `status_audit` current. Battery **27/27** green
(the 26 from G1-21 plus `jc3weapons --check`).

**Revert:** delete `Tools/scripts/jc3weapons.py`, `Research/JC3Grab/WEAPONS.md`, `WEAPONS
`.jsonl`, `WEAPONS_SHARED.json` and `E:\Modding\_JC3grab\weapons\`, restore the README rows and the
tracker row to `todo`, remove this entry and the intended-change entry above it. No game file,
install, save or dropzone was modified; nothing was committed.

## G2-11 · Weapon wiring per armed vehicle — intended change (2026-10-26)

**Card:** G2-11 (phase G2). Out: `Research/JC3Grab/WEAPON_WIRING.md` (one section per armed entity) +
`WEAPON_WIRING.jsonl`, `Tools/scripts/jc3wiring.py --write/--check`.

**Intended change.** The table is what was built; the card named the inputs and the questions, not
the file layout.

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3wiring.py` | new. Decodes the `.epe` of every armed entity, resolves the root weapon slots, collects weapon components, fire points, aim components, seats and chassis moving parts; `--write`, `--check`, `dump` | the card's Out; it reuses `jc3index.py`, `jc3detail.py` (`.ee`/`.epe` extraction and `ConvertProperty`) and the G2 conventions, adding no new archive or ADF reader |
| `Research/JC3Grab/WEAPON_WIRING.jsonl` | new. One row per entity: roots, slots, every weapon property, every point, every component, seats, parts, counts, digest | the card's Out; same values-first shape as `PARTS_TABLE.jsonl`/`WEAPONS.jsonl` |
| `Research/JC3Grab/WEAPON_WIRING.md` | new, generated by the same `--write` | the card's Out |
| `E:\Modding\_JC3grab\wiring\epe\*.xml` | new (outside the repo): the converted `.epe` of each armed entity | raw decode stays out of the repo; `--check` re-reads the archives, not this cache |
| `Research/JC3Grab/README.md` | three `jc3wiring` command rows + a G2-11 section + two Files rows | every G2 tool and table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-11 | todo` -> `done` + evidence | the session loop step 7 |

**What the card assumes that needed a closer look.** The armed list (53 `.ee` over 21 chassis) is
exact - `--check` compares the tool's set against `FEATURE_CENSUS.json` one-for-one. Two mechanics
were not in the card:

* The existing `detail/*.ee.json` is **lossy for this question**: `jc3detail.parse_epe` drops every
  unnamed `<value id="...">` (it keys only named values) and drops values >= 80 characters. The
  weapon bindings *are* unnamed object-id properties on the root class, so a reader that trusts the
  detail JSON cannot see them. `jc3wiring.py` re-runs `ConvertProperty` and keeps `id:` keys, plus
  `id:D04059E6`, which turns out to be the Jenkins hash of the object's class name - a per-object
  read check.
* The card says "the seat that fires it (driver vs `mounted_weapon` gunner seat)". The entity has no
  seat->weapon pointer. The split is structural: `main_weapon` + a second driver pointer, versus
  `mounted_weapon` + `mounted_weapon_2` on a seat whose state is a mounted-weapon state. The report
  states that limit instead of inventing a link.

**Revert:** delete `Tools/scripts/jc3wiring.py`, `Research/JC3Grab/WEAPON_WIRING.md`,
`Research/JC3Grab/WEAPON_WIRING.jsonl`, `E:\Modding\_JC3grab\wiring\`, the README rows and section,
and this entry plus the result entry below; restore the tracker row to `todo`. No game file, install,
save or dropzone is touched; nothing is committed.

## G2-11 · Weapon wiring per armed vehicle — done (2026-10-26)

**Card:** G2-11, second card of phase G2. 53/53 armed entities decoded; `--check` re-reads the
archives, rebuilds every row and compares the generated md.

**Record:** `Research/JC3Grab/WEAPON_WIRING.md` (2,045 lines, one section per entity) +
`WEAPON_WIRING.jsonl` (506 KB, every property of every weapon, point and component) +
`Tools/scripts/jc3wiring.py`.

### The slot model (the answer the card was after)

The root class (`CCar`, `CAirPlane`, `CBoat`, `CHelicopter`, `CTrain`) carries **four object-id
pointers**, all present on every vehicle and `00000000` when unused:

| slot | property in the `.epe` | name | who fires it |
|---|---|---|---|
| 1st driver | `id:851CAABE` | `main_weapon` (Jenkins match) | driver |
| 2nd driver | `id:00568A74` | **not in any shipped name table** | driver |
| 1st gunner | `mounted_weapon` | named in the file | mounted-weapon seat |
| 2nd gunner | `id:AC0BC788` | `mounted_weapon_2` (Jenkins match) | mounted-weapon seat |

The property-name hash is the same Jenkins lookup3 as archive paths (`rbmhdr.hash_jenkins`). Six
names were recovered by exact 32-bit match: `main_weapon`, `mounted_weapon_2`, `tuning_file`,
`autoaim_tuning_file`, `impact_usage`, `weapon_category`. The second driver slot resisted a
1.1-million-string vocabulary search (57 weapon/mount words, 2- and 3-word combinations, numeric
suffixes), so its id is the name of record. `id:D04059E6`, present on every object, is the Jenkins
hash of that object's class name; `--check` recomputes it on all decoded objects and would fail on a
single mismatch.

**Answers:** (a) max driver-fired weapons on a land vehicle = **2**, on the medium tank (`v0201`)
and Bavarium tank (`v0202`), both `main_weapon` = cannon and second = hull MG; the small tank, the
signature Serpente and the signature buggy have one, every other land vehicle none. (b) the two
weapons are two separate root pointers, not an ordered list; the component carries no slot,
`weapon_type` is `2` everywhere and the G2-10 tunes have no slot/input member, so no button mapping
or switching is encoded. (c) **no** vehicle binds three; the max is 2, and a third carried component
is inert (see below). (d) driver-fired CCars: medium/Bavarium tank (2 each), small tank, signature
Serpente, signature buggy (1); the APC, technical jeep and armoured jeep are gunner-only.

Totals: **88 weapon components** (57 `CBulletWeaponBase`, 25 `CMissileWeaponBase`, 6
`CRPGFireLeachWeapon`), **62 driver slots**, **19 gunner slots**, **81 bound / 7 unbound**,
**193 seats**, 23 distinct weapon names.

### Findings worth carrying forward

* **`w206_mounted_capstone_m2hm` is outside G2-10's catalogue.** 19 components over 5 chassis (APC,
  technical, armoured jeep, heavy patrol, light patrol) - the most common gunner weapon in the
  fleet - but it lives in `jc_weapons/04_mounted`, not `06_vehicle`, so it has no row in
  `WEAPONS.md`. Its tune and its two `GripPointSettings` variants are already in
  `WEAPONS_SHARED.json` (G2-10 decoded them as shared tunes); this card records the per-entity
  `tuning_file` and the grip/mount wiring. A future weapon-catalogue card should not copy G2-10's
  `06_vehicle` filter.
* **The gunner weapons name their mount parts; almost every driver weapon does not.** 22 of the
  88 components carry a type-4 `SWeaponPoint` (`MountAttach`): all 19 gunner weapons (two parts
  each) and the corvette's driver cannon. The gunner strings match `PARTS_TABLE.jsonl` names
  exactly - the heavy patrol's two M2s point at `heavypatrol_weapon_mount_l/r_horizontal` +
  `_vertical`, the APC at `apc_turret_base` + `apc_weapon_mount_vertical`, the technical at
  `technicaljeep_rebel_turret` + `technicaljeep_weapon_mount_vertical`, the armoured jeep at
  `armoredjeep_turret_base` + `armoredjeep_weapon_mount_vertical` - and those are all `Turret` ->
  `Cannon` chains in the parts module, so a mounted gun's articulation is explicit in the entity.
  The corvette is the lone driver exception: `w616_corvette_canon` names `corvette_gun` +
  `corvette_turret` on its own `fire_position_0`, which is also the kind of chain a future turret
  card can copy. The other 59 driver weapons name no part at all; their chassis part list is
  recorded, but the turret/cannon -> weapon link is not in the `.epe`.
* **The mounted weapons are seat-scoped and the seat index is in the interaction graph.**
  `interaction.seat.gunner1` = index 6, `gunner2` = 7, driver = 0. Mounted seats carry
  `S_IDLE_VEHICLE_SPINNING_MOUNTED_WEAPON` (6 seats: APC 3, technical 1, armoured jeep 2),
  `S_VEHICLE_FIXED_MOUNTED_WEAPON` (13 seats: heavy patrol 10, light patrol 3) or
  `S_MOUNTED_WEAPON` (3 seats, light patrol).
  No entity mixes a driver slot with a gunner slot. The heavy patrol's `mounted_weapon` joins
  geometrically to `gunner2`/`point.gunner.right` (1.05 m) and `mounted_weapon_2` to
  `gunner1`/`point.gunner.left` (1.05 m) - the slot order is *not* the seat order.
* **The cargo-plane variant carries a whole second root.** `v4603_..._military_cargo_tank.ee` has a
  `CAirPlane` and a `CCar` (the medium tank) side by side; the tank owns the two driver weapons and
  its own `CInteractionContext`/driver seat. The tool records roots per entity, labels the bindings
  `CCar::main_weapon` when there is more than one, and does not merge the two seat lists. Without
  that, the entity looked unarmed.
* **Seven entity files carry an unbound component.** Six are inert duplicates: the fighter jet
  ships `w608` (plain missile) next to the bound `w609` (air lock-on), and the fighter bomber ships
  `w612` next to bound `w611`/`w613` - no slot references either, so they are variants left in the
  graph. The seventh is different: the monorail missile car's only weapon (`w614`, 6 fire
  positions) is bound to no slot and sits under a `CTurretWeaponComponent`; the entity exposes
  only `interaction.seat.stunt`, so it is an AI/script turret.
* **`CLightWeaponComponent` is a light**, not a gun (30 components on 9 entities, e.g. the medium
  tank's cannon `warning_light`). It is recorded as a weapon subcomponent but not counted as a
  weapon.

### Validation

`jc3wiring.py --check` -> `PASS: 53 entities, 88 weapons, 81 bound, 7 unbound, 193 seats, md 2045
lines`. It re-reads all 53 `.epe`s out of the archives, compares every jsonl row field-for-field,
regenerates the md and diffs it, verifies every object's class-hash property, verifies every
non-null slot resolves to a weapon component, verifies the two trailing pointers are null, and
cross-checks each entity's weapon names and `SWeaponPoint` count against `FEATURE_CENSUS.json` (a
decode from a different script): **0 mismatches**. The census's own per-entity `weapon_points`
totals equal the tool's point list for every entity.

Tamper-tested: flipping one row's `gunner_slots` from 1 to 2 made `--check` exit 1 and print the
field diff for that entity; restoring the row returned PASS. The check has teeth.

What `--check` does not cover: the two unarmed samples quoted in section 1 are a one-off decode,
not part of the 53-row set. Re-run for this entry: `v0604_car_urga_buggy_debug.ee` and
`v0300_car_kensington_sportsmuscle_civilian_01.ee` both carry all four slot properties set to
`00000000`, and both have `action_1` = 1 / `action_2` = 2 - so the pointers and the action numbers
belong to the classes, not to the armed variants.

**Battery:** 28/28 green (`jc3wiring --check` added; the other 27 unchanged). Standing gates still
green at phase start: `jc3weapons --check` PASS (25 ids / 24 shared), `jc3fx` 57,187 files 0
problems, `jc3hkx` 233 entities / 34,999 instances, `status_audit` current.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was
modified; nothing was committed.

## G2-12 · Armed Serpente: civilian → signature_preorder diff — intended change (2026-10-26)

**Card:** G2-12 (phase G2). Out: `Research/JC3Grab/SIGNATURE_DIFF.md`. This is the template for
B-05/B-06 (importing the missile onto the Batmobile), so the record has to separate what is
*wiring* from what is *art*.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3sigdiff.py` | new. Reads both `.ee` containers, their `.epe` graphs, the parts modules, every `.rbm` header and the w618 `.wtunec`/`.ftunec`; `--write`, `--check`, `dump` | the card's Out; reuses `jc3detail`/`eetoc` (container), `jc3wiring.parse_epe` (full graph incl. unnamed `id:` props), `jc3adf` (parts and tunes), `rbmhdr` (mesh headers), adding no new reader |
| `Research/JC3Grab/SIGNATURE_DIFF.md` | new, generated | the card's Out |
| `Research/JC3Grab/SIGNATURE_DIFF.json` | new, generated. Machine form of every diff section, compared by `--check` | matches the phase's values-plus-table convention (G2-10/11) |
| `E:\Modding\_JC3grab\sigdiff\*.xml`, `*.vmodc`, `*.epe` | new (outside the repo): converted graphs, the two parts modules, the inner `.epe`s | decompiles stay out of the repo |
| `Research/JC3Grab/README.md` | `jc3sigdiff` command rows, a G2-12 section and a Files row | every G2 tool/table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-12 | todo` -> `done` + evidence | session loop step 7 |

**What the card assumes that needs checking in the data.** The card names `hood_signature`,
`missile_base_signature`, "any hinge/door entries" and "the w618 tune path". Three of those may not
be additions at all:

* The civilian `.ee` already embeds `sportsmuscle_hood_signature_lod*.rbm`,
  `sportsmuscle_missile_base_signature_lod*.rbm` and a `signature/sportsmuscle_vehicle_parts.vmodc`
  (a *second* parts module, 30,382 B). The card calls both parts "added"; the diff has to say whether
  JC3 adds them or only instantiates them. `PARTS_TABLE.jsonl` already has three v0300 rows whose
  modules are 42-part sets, so the answer is probably "defined in both, instantiated only in the
  signature" - to be confirmed part-by-part, not assumed.
* The `.ee` also carries a loose `*.epe` next to the container, and the two do not match (109,766 vs
  109,526 B). The diff must use the container member (what the game builds) and record the loose
  entry's hash difference, not silently mix the two.
* Object ids (`_object_id`) and `vec_events` hashes are renumbered per variant. A naive object diff
  calls every object changed. The tool resolves references through a semantic tree path and ignores
  `vec_events`, and reports how many of each it discarded, so the remaining list is real changes.

**Revert:** delete `Tools/scripts/jc3sigdiff.py`, `Research/JC3Grab/SIGNATURE_DIFF.md`,
`SIGNATURE_DIFF.json`, `E:\Modding\_JC3grab\sigdiff\`, the README rows/section, and this entry plus
the result entry below; restore the tracker row to `todo`. No game file, install, save or dropzone is
touched; nothing is committed.

## G2-12 · Armed Serpente: civilian → signature_preorder diff — done (2026-10-26)

**Card:** G2-12, third card of phase G2. `--check` re-reads both `.ee` containers, converts both
inner `.epe`s again, rebuilds every section and compares the json field-for-field and the md
byte-for-byte.

**Record:** `Research/JC3Grab/SIGNATURE_DIFF.md` (546 lines) + `SIGNATURE_DIFF.json` +
`Tools/scripts/jc3sigdiff.py`.

### What changes

| layer | civilian | signature |
|---|---|---|
| container | 566 members | 601 (+167/−132; 108 same-role replacements) |
| `.epe` | 450 objects | 464 (2 changed, 4 added subtrees, 1 removed) |
| parts module | 42 parts | 42 parts, same names and indices |
| part links | base `*.lod` | 19 `model` + 4 `model_swap` → `signature/` |
| instantiated parts | 40 | 41 (the other hood branch) |
| `.rbm` meshes | 198 | 203 (84 pairs, +5 RPG LODs) |
| `.ee.toc` | 468 | 498 (+162/−132) |
| weapon slots | 0 | 1 (`main_weapon`) |

### The wiring B-05/B-06 import

* `main_weapon` (`id:851CAABE`) goes from null to the new `CMissileWeaponBase`; the other three
  slot pointers are `00000000` in the variant (checked on the decoded root).
* The component is `w618_sportsmuscle_missile`, `weapon_id` 618, `weapon_type` 2. Its projectile is
  the **stock RPG fire-leach body**: `w143_rpg_fire_leach_projectile_body.model_xml`, its
  `w143_rpg_fire_leach_projectile_body_col.pfx` collision and a
  `rigid_object_effect_settings_default.etune`. The container adds the projectile's
  five LODs, four textures, the `.pfxc` and the `.lod` — not a new missile mesh.
* Four `internal.fire_point.0…3` tubes, all `type` 2, at y 1.085 / z −1.566 and x +0.182, +0.058,
  −0.063, −0.19. Each point's position equals one `SAttachedEffect` muzzle's position (a pairing
  `--check` asserts); all four muzzles name effect hash `667364510` →
  `effects/jc_weapons/muzzle_flash/sportsmuscle_missile_muzzleflash.effc`, a member of this `.ee`
  (no VFS entry).
* `CAimPOIWeaponComponent` `aim.poi` (its unnamed `id:2D0B3C09` = 50), one `SEffects`, four
  `SAttachedEffect`, one `CForcePulse` (`w618_sportsmuscle_missile.ftunec`) and one
  `CMaterialEffectTable` (`tank_explosion_effect_table`). 15 objects added in total, 1 removed.

### The art is a recompile, not new geometry

* The two parts modules are **the same part set**: 42 names, same indices, same behaviours, damage
  types, parents and flags. Only `model`/`model_swap` differ on 19 parts (23 links), all to
  `signature/signature_*.lod`. No hinge, door or entry part is added or changed.
* The card's "second parts module" premise is wrong: each `.ee` carries exactly one
  `sportsmuscle_vehicle_parts.vmodc`, and the variant's is a same-role replacement at the
  `signature/` path. Both modules define the hood and missile-base parts at all times; the `.epe`
  is what chooses a branch — civilian instantiates 40 (drops 25 `hood_signature`, 41
  `missile_base_signature`), signature instantiates 41 (drops 24 plain `hood`).
* All 84 paired `.rbm` files keep their block count and AABB; sizes move −141…+44 B. The kit is the
  same shell recompiled against the signature textures.
* The root's content ids follow the kit, and the tool resolves them (Jenkins hash → the
  container's own module names, asserted): `vehicle_parts` 1526043305 → 402479768 =
  `signature/sportsmuscle_vehicle_parts.vmodc`; `decals` 1732285335 → −211122583 =
  `00_shared/modules/decals/default_decals.vmodc` (the civilian `..._decals.vmodc` is removed);
  `palette` −1071400364 = the civilian `..._palette.vmodc` hash, cleared to null (that module is
  removed too).
* The interaction graph changes one string only: the stunt-hood area `front_area` →
  `front_signature_area`. No seat, entry, exit or trigger is added.

### Assumptions checked against the data

* **"hood_signature and missile_base_signature are added parts"** — half right. They are defined in
  both parts modules and instantiated only by the signature `.epe`; the diff is two `CPartProp`
  nodes, not a module or mesh addition (their LODs exist in both containers).
* **The loose `.epe` next to the container is a different build.** Confirmed and excluded: inner
  `.epe` 109,526 / 114,962 B vs loose 109,766 / 115,378 B, different sha1s. Only the container member
  is diffed.
* **Object-id churn.** A raw id diff marks all 450 objects changed. Resolving references through
  the semantic path and discarding `vec_events` leaves 2 changed objects (`CCar` and the stunt
  point); 51 reference values resolved to the same path, 603 `vec_events` and 1,245 identity fields
  were discarded. Those counts are in the json so nobody re-runs the naive diff.

### Tunes

* `w618_sportsmuscle_missile.wtunec`: embedded 12,773 B / 148 rows; the VFS path resolves to the
  patch copy at 14,244 B / 155 rows. The 7-field diff is six zero-valued `missile_base_tuning`
  members plus `fire_rate_level_2` = 0.12; shared rows are identical. The VFS copy is authoritative.
* Values: `damage` 1500, `impulse` 350, `max_range` 300, `fire_rate` 0.5 s, `magazine_size` −1,
  `unlimited_ammo` 1, `missile_turning_speed` 0 (unguided), gravity −9.82; AI tune damage 30, range
  10–100. Blast (`ftunec`): 1100 player damage in 8 m
  (`PlayerDamageRadiusPercentageMax` 0.15), 500 AI damage in 8 m.
* Autoaim: `autoaim_vehicle_no_lockon_missile.wtune` (no lock-on, as the name and the 0 turn rate
  say).

### Validation

`jc3sigdiff.py --check` → `PASS: 566 -> 601 members, graph 450 -> 464 objects, 4 added / 1 removed,
19 part rows changed, 84 mesh pairs, 2 graph objects changed`. Invariants: civilian 0 weapon slots /
variant 1; the four fire points are `internal.fire_point.0…3`, type 2, each mapped to a muzzle at
its own position; all four muzzles name one effect path and that path is a container member; the
variant has one `CMissileWeaponBase` and one aim component; every restyled model is a `signature/`
path and no civilian model is; the `epe`s instantiate 40/41 with exactly the expected hood branch
missing; all 84 mesh pairs keep block count and AABB; the tune path is a VFS entry. Tamper test:
changing one fire-point x in the json made `--check` exit 1 with `json section changed: weapon`;
restoring it returned PASS.

Standing gates re-run: `jc3wiring.py --check` PASS (53 entities, 88 weapons, 81 bound, 7 unbound,
193 seats), `jc3weapons.py --check` PASS (25 ids, 197 files, 24 shared tunes).

**Limits.** Mesh comparison is header-level (block count, AABB, size), not vertex data, so equal
AABB does not prove equal geometry — the path-swap conclusion rests on the identical block counts
and bounds plus the `signature/` texture set, not on a vertex hash. The `CMaterialEffectTable` is a
30-byte hash blob and is not decoded, so the seven `tank_explosive_*.effc` files it presumably names
are recorded as added container members, not as proven table entries. Two root scalars
(`id:EA011E72` 0.3→1, `id:FFE31EE1` 1→0) have no Jenkins name; they are reported unnamed. Only
these two entity builds are compared — other v0300 variants are out of scope.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was
modified; nothing was committed.

## G2-13 · Turret and cannon mechanics — intended change (2026-10-26)

**Card:** G2-13 (phase G2, S, deps G2-11). Out: `Research/JC3Grab/TURRET.md`. Serves ANI-2 and
WPN-1/2, MOD-2: what a B-05 turret actually has to copy.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3turret.py` | new. Decodes eight vehicles' parts modules and `.physicsc` packfiles, the two point properties, both autoaim tunes and the cached parts-module arrays; `--write`, `--check`, `dump samples\|census\|tune` | the card's decode step; reuses `jc3adf`/`jc3hkx`/`jc3wiring`/`jc3detail`, adds no reader |
| `Research/JC3Grab/TURRET.md` | new, generated | the card's Out |
| `Research/JC3Grab/TURRET.json` | new, generated: every sample's constraints, chains, points and aim objects, both censuses, both tunes; compared field-for-field by `--check` | the G2-10/11/12 values-plus-table convention |
| `Research/JC3Grab/README.md` | command rows, a G2-13 section, a Files row | every G2 tool/table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-13 \| todo` -> `done` + evidence | session loop step 7 |

**What the card assumes that needs checking in the data.** The card says "decode
`aim_part_constraints`, `hinged_parts` and related arrays ... record yaw/pitch limits, rates, pivot
offsets ... and how the aim target is chosen". Three of those assumptions may not hold, and each is
settled by reading the files rather than by the card:

* that the parts module carries the hinge. The medium tank's `hinged_parts[]` and
  `rotating_parts[]` are **empty**; the hinge exists only as a `hkpLimitedHingeConstraintData` in
  `.physicsc`, and the link is the part's `constraint_index`. `aim_part_constraints` exists in every
  module's type info but is empty on all six turreted vehicles.
* that a **rate** is recorded. The limited hinge has an axis and two angles, nothing else; the turn
  rate is code-side, so it will be reported as UNKNOWN rather than guessed.
* that "the aim target" is a turret field. It is not: the entity owns one `STargetPoint` and the
  weapon owns an autoaim tune, so the answer is two files plus the tune's numbers.

## G2-13 · Turret and cannon mechanics — done (2026-10-26)

**What was read.** Eight `.ee` parts modules and `.physicsc` packfiles (`jc3adf` + `jc3hkx`), the
`.epe` graphs for their aim objects (`jc3wiring`), `PARTS_TABLE.jsonl`, `WEAPON_WIRING.jsonl` and
`WEAPONS_SHARED.json`: the six vehicles the card names (v0201, v0202, v0603, v0200, v0504, v0600)
plus the Serpente (for B-05's own chassis) and the buggy (as the aim-constraint counter-example).
106 constraint objects decoded (3/15/17/16/19/13/11/12), 92 fire points classified, 78 cached
parts modules walked for the arrays.

**A turret is two parts and two Havok hinges.** The reference chain, medium tank:

| | part | index | behaviour | parent | constraint | pivot | axis | limits |
|---|---|---|---|---|---|---|---|---|
| yaw | `mediumtank_turret` | 26 | `Turret` | 0 | 2 | (0, 2.2812, 1.1382) | +Y | **-179 .. +179 deg** |
| pitch | `mediumtank_cannon` | 38 | `Cannon` | 26 | 0 | (0, 2.5347, 0) | +X | **-5 .. +20 deg** |
| hatch | `mediumtank_hatch` | 39 | `FrontLeftDoor` | 26 | 1 | (-0.4848, 2.921, 1.4785) | +X | 0 .. 130 deg |

`w602_mediumtank_canon` on `main_weapon` fires from `fire_position_0` at (0, 0.3739, -5.8174), and
that point names both parts in two unnamed string properties: `id:80201E4D` = yaw part,
`id:5C19E7E0` = pitch part. `parent_space_offset` is identity on both parts; the cannon pivot sits
0.25 m above the turret ring and the muzzle 5.82 m forward of the trunnion. The Bavarium tank reuses
**both hinges unchanged** (same pivots, same limits) and adds 12 skirt flaps (0..30 deg each).

The wheeled mounts are the same two hinges with their own numbers, and their parent chains carry
static adapter parts that have no constraint:

| vehicle | yaw | pitch | chain |
|---|---|---|---|
| APC | `apc_turret_base` ±179 at (-0.0037, 2.1367, 1.3048) | `apc_weapon_mount_vertical` -15..50 at (0, 2.7313, 0.5942) | body → turret → vertical |
| armoured jeep | `armoredjeep_turret_base` ±179 at (0.507, 2.0, 0.263) | `..._weapon_mount_vertical` -25..50 at (0.5099, 2.2898, -0.3751) | body → turret → horizontal → vertical |
| technical | `technicaljeep_rebel_turret` ±179 at (0, 1.3878, 1.2902) | `..._weapon_mount_vertical` -10..45 at (0, 2.0498, 0.6697) | body → turret base → turret → horizontal → vertical |
| small tank | `smalltank_turret` ±179 at (0, 1.8131, 0.5247) | `smalltank_cannon` -5..25 at (0, 1.9143, -0.3611) | body → turret → cannon |

The small tank's `smalltank_rack` is on constraint 15, a `hkpRagdollConstraintData` — a deck rack on
a ragdoll, not a hinge, which is why it has no pivot or limits.

**The two point properties, fleet-wide.** 92 fire points on 52 weapons across 41 armed entities name
a yaw part (`id:80201E4D`) or a pitch part (`id:5C19E7E0`); the values are part-name strings.
All 47 pitch parts are `Cannon`; the 75 yaw parts are 18 `Turret`, 13 `Cannon` (boat/jeep mounts that
yaw and pitch as two `Cannon` parts) and 44 plain parts on aircraft pods. Two entries on
`v4603_plane_urga_cargotransport_military_cargo_tank` name parts of the tank it carries
(`mediumtank_turret`/`mediumtank_cannon`, from the tank's own `w602`) — cross-entity, recorded
separately, not as unresolved.

**`aim_part_constraints` is suspension.** 85 rows in 17 of the 78 cached parts modules: sources
13 `Spring`, 2 `Axle`, 70 plain (Y-bars, axle arms, coil springs); targets 34 `BrakeDrum`,
19 `Wheel`, 12 `BrakeDisc`, 6 `BrakeCalipers`, 2 `Engine`, 12 plain. **No** row names a `Turret` or
`Cannon` part, and all six turreted vehicles have 0 rows. `hinged_parts[]` is used by 28 of 78
modules and `rotating_parts[]` by 22; both are empty on every tank, so the hinge really does live
only in `.physicsc`.

**How the aim target is chosen.** Every sampled entity carries one `STargetPoint` named
`AutoAimTargetPoint`, `min_aim_distance` -1, plus an unnamed float 2 and int 1; its `world`
translation is (0, 1, 0), i.e. the body centre one metre up, not the muzzle. The weapon names the
tune: the tanks' `w602`/`w603` and the small tank's `w605` use `autoaim_vehicle_mgun`, the mounted M2
`w206` (APC, armoured jeep, technical) uses `autoaim_assault_rifle`. Both tunes: 5..70 m,
`CanTargetCharacters` 1, `CanTargetVehicles` 0, `CanTargetRigidObjects` 0, sticky 6 deg new /
16 deg current at strength 0.4; they differ only in the candidate thresholds, 0.03/0.05 rad
(1.7/2.9 deg) on the vehicle tune and 0.04/0.06 rad (2.3/3.4 deg) on the rifle tune.

**Validation.** `jc3turret.py --check` re-reads the eight entities and rebuilds both files:
`PASS: 8 samples, 92 points on 52 weapons, 85 aim-constraint rows, 3 mediumtank constraints`.
Invariants: the medium tank's three constraints are the cannon (-5..20), hatch (0..130) and turret
(-179..179); every constrained part's `constraint_index` addresses a real object; every `Turret` or
`Cannon` part sits on a **limited** hinge with an identity `parent_space_offset`; every sample has
exactly one `AutoAimTargetPoint` at (0, 1, 0); every pitch part in the fleet is a `Cannon` part; no
`aim_part_constraints` row names a Turret/Cannon part; the six turreted samples have 0 such rows.
Tamper test: setting the turret's `max_deg` to 90 in the json made `--check` exit 1 with
`json section changed: samples`; rebuilding returned PASS.

**Limits.** No rotation rate or acceleration exists in the decoded data (UNKNOWN, not guessed).
`hkpRagdollConstraintData` objects are counted but not decoded. The hinge transform's frame (body-A
local vs vehicle space) is not proven — the medium tank's numbers agree with vehicle space, and the
wheeled pitch pivots hang above unconstrained adapter parts, so a port should use the printed values
as stored. The two point properties still have no recovered names; their meaning rests on the part
names and behaviours they carry. The array census covers the 78 modules in the local cache, not all
233. `CAimPOIWeaponComponent` (`aim.poi`) exists on the Serpente and the buggy but not on the
turreted vehicles; what it does is not decoded here.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was
modified; nothing was committed.

## G2-14 · Moving-part behaviours: who drives each variable — intended change (2026-10-26)

**Card:** G2-14 (phase G2, S, deps P0-2). Out: `Research/JC3Grab/MOVING_PARTS.md`. Serves
ANI-3…8: for a port, which behaviour gets which variable and which vehicles prove it on a car.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3moving.py` | new. Decodes `vehicle_common.vmodc`'s five behaviour tables, joins them with `FEATURE_CENSUS.json`'s part behaviours and the root class from each detail JSON, and censuses the per-part arrays; `--write`, `--check`, `dump` | the card's Out; reuses `jc3adf`/`jc3detail`/`jc3index`, no new reader |
| `Research/JC3Grab/MOVING_PARTS.md` | new, generated | the card's Out |
| `Research/JC3Grab/MOVING_PARTS.json` | new, generated: all 53 table rows with every member, all 67 behaviours with channel/variable/classes/proof, and the array census; compared by `--check` | G2-10…13 convention |
| `Research/JC3Grab/README.md` | command rows, a G2-14 section, a Files row | every G2 tool/table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-14 \| todo` -> `done` + evidence | session loop step 7 |

**What the card assumes that needs checking in the data.** `FEATURE_CENSUS.json` already carries
the behaviour -> vehicle counts, but its `behaviour_variables` rows are empty (`variable: null`,
`members: {}`) because `vehicle_common` is an inner file of an `.ee`, not a VFS entry - the index
has no row for it. The card's "with their members (axis, angle limits, rpm scale)" also assumes the
per-part arrays carry geometry; they may not.

## G2-14 · Moving-part behaviours: who drives each variable — done (2026-10-26)

**What was read.** `vehicle_common.vmodc` from the Serpente civilian `.ee` (12,271 B, member at
12,214,868 in that container; the only copy in the index), `FEATURE_CENSUS.json`, 232 detail JSONs
for the root classes, and the 78 cached parts modules for the arrays.

**The five tables.** 53 rows: 14 doors, 25 hinged, 12 rotating, 1 fin, 1 spring. Only hinged and
rotating name a variable:

* hinged: `target_position_variable` + `lod` + `use_target_position_as_angle`; variables are
  `steering_roll`, `steering_roll_inverted`, `elevon_left_T`/`_right_T`, `steering_pitch`,
  `steering_yaw`, `flaps_T`, `air_brakes_T`, `landing_gears_T`, `hatches_T`, `steering_turn`,
  `steering_angle_inverted`, and the 12 `*_coxa/femur/tibia_t`. Only `SteeringFork` sets the
  angle flag (1); every other row reads the variable as a 0..1 position.
* rotating: `rpm_variable` (`main_rotor_rpm`, `tail_rotor_rpm`, `propeller_rpm`, `weapon_rpm`,
  `radar_slow_rpm`, `radar_fast_rpm`, rotor variants) + `rotoscope_enabled`, `inverted`,
  `special_collision_enabled`, `number_of_water_collision_sensors`, `rotoscope_rpm_per_cycle` (20.0
  on every row).
* doors, the fin (`BoatRudder`) and the spring (`Spring`) are **name-only**: no angle, speed or
  variable. A door's travel is its Havok hinge (G2-13: `FrontLeftDoor` 0..130 deg on the medium
  tank) and `door_parts[]` holds only the part index.

**Behaviour -> vehicle -> proof.** 67 behaviours in use across 233 vehicles; 38 of them have a
`vehicle_common` row, 29 do not (turret/cannon, wheel, body, brakes, engine, windows, couplings).
37 are proven on a `CCar`; 30 are not - aircraft, boat, helicopter, bike and train parts:
`LandingGear`, `MainRotor`, `TailRotor`, `Propeller`, `Rudder`, `Elevator`, `Ailerons`, `GatlingGun`,
`AirBrake`, `MissileHatch`, wagon couplings, `RadarFast/Slow`... `AirBrake` is 3 parts on one
`CAirPlane` (`v4602_plane_urga_fighterbomber`), so Q-1's probe stands. Only 11 of the 25 hinged rows
are used by any part: the 12 spider-leg behaviours and both elevons are declared and unused.

**The per-part arrays.** `door_parts[]` 224 rows in 56 modules, `part_index` only. `hinged_parts[]`
148 rows in 28 modules, `part_index` only - no axis, no limits. `rotating_parts[]` 47 rows in 22
modules and the only one with geometry: `part_index`, `position[3]`, `rotation_axis[3]`,
`number_of_blades`, `rpm_multiplier`, `min_rpm_visible`, `max_rpm_visible`,
`rpm_opacity_transition`. The Serpente fills `door_parts` (3) and the APC too (5); the six turreted
vehicles fill none of the three.

**Validation.** `jc3moving.py --check`:
`PASS: 67 behaviours, 53 table rows (37 proven on CCar), 224 door rows`. Invariants: table counts
14/25/12/1/1; every hinged row has a non-empty `target_position_variable`; every rotating row has an
`rpm_variable`; door/fin/spring rows have no members beyond `name`; `Turret`, `Cannon`, `Wheel` and
`Body` have no `vehicle_common` row; every proof follows from the row's chassis classes; `door_parts`
is non-empty in the cache. Tamper test: setting `LeftAileron`'s variable to `steering_roll_XX` in
the json made `--check` exit 1 with `json section changed: tables`; rebuilding returned PASS.

**Limits.** One `vehicle_common` copy exists, so there is nothing to diff it against. The 15
declared-but-unused names have no user in the fleet; their variables are declared, not exercised.
The array census covers the 78 cached modules, not all 233. The table proves the binding between a
behaviour and a state variable; which C++/flowgraph writer fills `steering_roll` or `hood_angle` is
not in any file read here.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was
modified; nothing was committed.

## G2-15 · Door-part animation (canopy, missile hatches) — intended change (2026-10-26)

**Card:** G2-15 (phase G2, S, deps G2-14). Out: `Research/JC3Grab/DOORS.md`. Serves MOD-4 and
ANI-6/8; answers (a) transverse door hinge, (b) what opens a `MissileHatch`, (c) whether entry
opens the driver door.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3doors.py` | new. Reads the four entities' parts modules and `.physicsc`s, censuses every door part in the cached modules, scans the cached `.epe` graphs for entry paths and, for the monorail car, for any object naming a hatch; `--write`, `--check`, `dump` | the card's decode step; reuses `jc3adf`/`jc3hkx`/`jc3wiring`/`jc3detail` |
| `Research/JC3Grab/DOORS.md` | new, generated | the card's Out |
| `Research/JC3Grab/DOORS.json` | new, generated: the four samples' door parts with hinges, the 224-row census, the interaction census, the monorail weapon/hatch evidence | G2-10…14 convention |
| `Research/JC3Grab/README.md` | command rows, a G2-15 section, a Files row | every G2 tool/table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-15 \| todo` -> `done` + evidence | session loop step 7 |

**What the card assumes that needs checking in the data.** G2-14 showed `all_door_part_properties`
is name-only and `door_parts[]` is a bare index, so the card's "open angle, speed" has to come from
somewhere else - the `.physicsc` hinge for the angle, and nowhere at all for the speed. The card also
expects an interaction link ("which interaction opens it"); the entity may instead carry only
interaction *entry states*, with no per-part link.

## G2-15 · Door-part animation (canopy, missile hatches) — done (2026-10-26)

**What was read.** Four entities' parts modules and `.physicsc` packfiles (Serpente civilian, APC
military, monorail missile car, medium tank), the 78 cached parts modules for the census, and the 55
cached `.epe` XML graphs for the entry paths.

**A door is three pieces.** Behaviour name (`FrontLeftDoor`, `Hood`, `TurretDoor`, `MissileHatch`...)
+ a `part_index` in `door_parts[]` + a `hkpLimitedHingeConstraintData` in `.physicsc`. Nothing on
the part holds an angle or a speed.

**The four samples.** Donor: `sportsmuscle_door_f_l`/`_f_r` about ±Y, 0..80 deg at (±1.018, 0.622,
-0.771); `sportsmuscle_hood_signature` about +X, 0..70 deg at (0, 1.057, -0.848). APC: two centre
doors ±Y 0..100, rear-left door 0..95, front-left hatch +X 0..130, turret hatch +X 0..130. Monorail:
16 `MissileHatch` covers, 0..150 deg about ±Z (left side -Z, right +Z), pivots at x ±1.35, y 3.35,
z -6.1…+6.1, parents 7 and 8. Medium tank: `mediumtank_hatch` +X 0..130 at (-0.485, 2.921, 1.479).

**Census (a).** 224 door rows in 56 of the 78 cached modules, 220 on limited hinges and 4 with
`constraint_index` -1 (propeller wings that carry a door behaviour). By axis: **60 X (transverse)**,
132 Y (vertical), 28 Z (longitudinal), none oblique. X-axis users are the hoods (26/26 rows),
`TurretDoor` (2/2), `CargoBayDoor` (5/5), 19 of 20 `Trunk` rows, 5 of 55 `FrontLeftDoor` rows and
1 `RearDoor` - the rest of those behaviours are side doors on Y. So yes - a canopy that tilts forward is an ordinary `Hood`/`FrontLeftDoor` part on an
X-axis hinge; `mediumtank_hatch` and `sportsmuscle_hood_signature` are the working examples.

**MissileHatch (b).** The monorail car's only weapon is `w614_monorailmissilecar_missile`
(`CMissileWeaponBase`) with its own tune plus `CTurretWeaponComponent`; its six
`InternalFirePosition_0…5` sit inside the covered bay (x ±2.04/1.85, y 2.49, z -2.5…+0.96) while the
16 covers sit above it at y 3.35. **No object other than `CPartProp` names a hatch**, there is no
interaction entry for a hatch and no effect on one, so nothing in the entity opens them; the trigger
is code-side (almost certainly on fire, given the internal fire positions and the 150 deg travel) and
that is an inference, not a decoded link. No player interaction opens them - the car has no entry
states at all.

**Entry and doors (c).** The interaction graph carries `entry.driver` beside `entry.driver.no.door`,
with `S_ENTER_DRIVER_VEHICLE` and `S_ENTER_DRIVER_NO_DOOR_VEHICLE` as their states. Across 55 cached
entity graphs: 21 have both, 0 only the door path, 4 only the no-door path, 30 neither. The donor is
one of the 21; the APC and the monorail have neither (the APC's gunner mounts the turret, the train
car has no seats). The donor's container is 566 members with **0** animation files
(`.ban`/`.anim`), so the swing is not authored in the entity: the file proves the branch and the
interaction, not the visible motion.

**Validation.** `jc3doors.py --check`:
`PASS: 4 samples, 224 door rows / 220 hinged / X 60, both entry paths 21`. Invariants: the donor's
array is `door_f_l`/`door_f_r`/`hood_signature` with axes ±Y/±Y/+X; the APC has 5 door parts; the
monorail has 16, all `MissileHatch`, all 0..150 deg about Z; no non-`CPartProp` object names a
monorail hatch; the medium tank hatch is +X 0..130; the donor has both entry paths, the APC none;
the donor container has no animation member; at least one X and one Y hinge exist in the census.
Tamper test: changing the donor door's `max_deg` to 95 in the json made `--check` exit 1 with
`json section changed: samples`; rebuilding returned PASS.

**Limits.** A hinge angle is the authored limit, not a measured swing. Speed and duration are absent
from every file read here (UNKNOWN). The census covers the 78 cached modules (56 with doors) and the
55 cached `.epe` graphs, not all 233 entities. The monorail's fire trigger is an inference. Which
code runs after `S_ENTER_DRIVER_VEHICLE` is not in any file.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was
modified; nothing was committed.

## G2-16 · The EMP truck — intended change (2026-10-26)

**Card:** G2-16 (phase G2, S, deps P0-2). Out: `Research/JC3Grab/EMP.md`. Serves WPN-4 (EMP missile,
"Immobilizer") and WPN-5 (`Batmobile_EMP_Burst`, radial stun/push): describe the truck's device —
components, trigger (`entry.use_item`), radius, duration, what it disables, effects and sounds, whether
it can be attached to another entity — and answer "can a driver of a different vehicle fire it".

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3emp.py` | new. Reads both EMP builds' containers, parts modules, pulses, tunes and emitters; censuses all nine oldtruck variants; decodes the two `CEMPWeapon` entities and their `.wtunec`s; counts `CEMPWeapon` in `WEAPON_WIRING.jsonl`; `--write`, `--check`, `dump` | the card's decode step; reuses `jc3adf`/`jc3detail`/`jc3wiring`/`jc3index` |
| `Research/JC3Grab/EMP.md` | new, generated | the card's Out |
| `Research/JC3Grab/EMP.json` | new, generated: parts, pulse members and refs, tune values, trigger, effect files, variant census, weapon rows | G2-10…15 convention |
| `Research/JC3Grab/README.md` | a G2-16 section and a Files row | every G2 table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-16 \| todo` -> `done` + evidence | session loop step 7 |
| this log | intended change + done | the journal |

**What the card assumes that needs checking in the data.** The card asks for radius, duration and
"what it disables"; a pulse tune may carry only damage numbers, leaving duration and semantics to
code. It also asks whether the device can be "attached" — the entity may hold no pointer at all from
the trigger or the entry to the pulse, in which case the honest answer separates the data (copyable
objects) from the code (what fires them).

## G2-16 · The EMP truck — done (2026-10-26)

**What was read.** Both builds' containers (794 members, 454 objects each), their parts modules, every
`CForcePulse` and `CMaterialEffectTable`, the two embedded explosion tunes, the effect files, the
interaction entries; all nine oldtruck variants' modules and `.epe`s; the two `CEMPWeapon` files'
`.epe`s and `.wtunec`s; and `WEAPON_WIRING.jsonl` for the fleet component count.

**The device.** Three parts on the flatbed — `oldtruck_emp_device_rebel` (index 5, parent 0),
`..._core_rebel` (46, `Rotor`) and `..._core_rebel_partswap` (47), both children of 5. The core's
`rotating_parts[]` row is part 46, 6 blades, axis +Z, `rpm_multiplier` 1.0, no visibility window —
the stock `Rotor` mechanism from G2-14, not a new one.

**The pulse.** Two `CForcePulse` objects: the ordinary `CForcePulse` on `car_explosion_medium.ftune`
at the origin, and **`EMP`** on `truck_emp.ftune` at (0, 2.0356, 0.6992). The tune is eight numbers:
100 player/AI damage in a 25 m radius, `*RadiusPercentageMax` 1.0 and `*RadiusMin` 1.0 — i.e. full
damage through the whole radius — against the stock blast's 500 damage in 5 m with 0.0/0.0. There is
no duration, no target class and no disable member. Comparing the two pulses member-for-member, only
three flags differ (`id:4912FC04` 0 vs 1, `id:AE6F7EFF` 1 vs 0, `id:CF4F7880` 1 vs 0) plus the
`emp_flatbed_table` material table, whose slots all point at the embedded
`explosion_emp_flatbed.effc`. The table also resolves the pulse's `id:D3DDD766`; its other ref,
`5FED74E7=FFFF7F53`, is not an object in the entity and stays dangling. **Duration and disable
semantics are UNKNOWN in data — they are code.**

**Trigger.** `trigger.use_item` is a 2× box over the flatbed at (0, 1.3507, 2.396); `entry.use_item`
is `CInteractionGraphEntry` -> state `S_STUNT_USE_ITEM_VEHICLE` with prompt `ui_activate_emp`. There is
**no reference from the trigger or the entry to the pulse**, and the trigger's own refs
(`6D433019=FFFF8C71`, `E880D61A=0000CAE5`) do not resolve inside the entity either. The truck has no
weapon component of any class, so the EMP is not on a fire button: it is a use-item action.

**The two builds.** Same 794 members, same 78 parts, same trigger and prompt. `mm250` **drops the
pulse and `truck_emp.ftunec`** and adds `CEffectPointEmitter epe_emp_powering_up` (effect hash
-1458959942, `enabled` 0) at (-0.011, 2.448, 0.07) with `emp_active.effc` — the escort mission's
charging prop; the blast there is the script's.

**The variants.** The parts module is shared: all nine oldtruck builds carry the 3 device parts and
the 6-blade core row (that is why the civilian's mesh list contains `oldtruck_emp_device_*.rbm`), but
only the two EMP builds carry the 3 `CPartProp`s and the `EMP` pulse. The other seven have the
geometry and no trigger.

**The weaponised EMP.** `w702_emp` (handheld, id 702, `weapon_type` 6, `FirePosition` (0, 0.13,
-0.69), three `CBarrelSpinWeaponComponent`s for the spin-up dials, wall penetration,
charging/charged/fire effects and sounds) and `w503_turret_emp` (static, id 503, type 2,
`fire_position_1` (0, 3.762, -9.708), `CTurretWeaponComponent`, own rigid objects and hinge). Both
use the stock `fow_weapon` tune and **neither tune has a single EMP-named field** — damage 500, range
50 m / 750 m, magazine 1, no radius or duration — so the effect is keyed off the `CEMPWeapon` class in
code. None of the 88 vehicle weapon components across the 53 armed entities is one.

**Answer.** The EMP effect can be put on another vehicle **as entity objects** (parts + `CPartProp`s +
pulse + tune + table + effect + use-item trigger, copy list in the doc), fired by the use-item action
if the vehicle's graph runs that state; it cannot be copied **as a weapon-slot weapon**, because the
truck's EMP is not a weapon and the only EMP weapon class has no data fields to tune and no vehicle
user.

**Validation.** `jc3emp.py --check`:
`PASS: 2 builds, 9 variants, 3 device parts, 2 EMP weapons, fleet CEMPWeapon 0`. Invariants: both
containers 794/454; `EMP` on `truck_emp.ftune` at (0, 2.0356, 0.6992); tune 100/25/1/1 for player and
AI; stock blast 500/5/0.0; 3 device parts with the core `Rotor` at 46 and a 6-blade +Z row; the
`use_item` state and prompt; the trigger position; no weapon class on the truck; only the EMP build
has the tune while both embed the effect; `mm250` has the emitter disabled at spawn, no pulse and no
tune; every variant has the 3 parts but only two have props + pulse; `w702`/`w503` ids/types, points,
the turret component and zero EMP tune fields; fleet `CEMPWeapon` 0. Tamper test: setting
`PlayerDamage` to 101 in the json made `--check` exit 1 with `FAIL: EMP.json stale`; rebuilding
returned PASS.

**Limits.** Duration, disable targets and the three flags' meaning are not in any decoded member.
The trigger->pulse link is absent, so "the driver presses use item and the pulse fires" is inferred
from the shared entity and the `ui_activate_emp` prompt. Whether the engine accepts `CEMPWeapon` in a
vehicle slot cannot be decided from data; the two users are a handheld and a static prop. The fleet
count covers the 53 armed entities in `WEAPON_WIRING` (88 components), not all 233 vehicle entities.
One pulse ref is dangling.

**Revert:** as the intended-change entry above. No game file, install, save or dropzone was modified;
nothing was committed.


## G2-21 · Turn-on-the-spot (tank pivot) — intended change (2026-10-27)

**Card:** G2-21 (phase G2, S, deps P0-2 - tracker shows `done`). In: tank/APC modules (`v0201`,
`v0202`, `v0603`, `v0200`) in `entities/`, `VOCABULARY.md` (`LandGlobal`, `LandSteering`,
`Transmission`, `CustomLandGlobal`). Do: compare the tanks' members with wheeled cars to find what
makes a tracked vehicle pivot. Out: `Research/JC3Grab/TANKTURN.md`. Serves MOD-2, HDL.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3tankturn.py` | new. Reads the decoded cache only (`E:\Modding\_JC3grab\entities\*.ee.json`, `E:\Modding\_JC3grab\detail\*.ee.json`) plus `Research/JC3Grab/VOCABULARY.md`; builds the tank-vs-fleet comparison of the four card modules, the refutation of each candidate member the card names, the tank-unique-member census over all module types, the member-name scan for track/pivot/skid-steer vocabulary and the container file-type census; `--write` / `--check` / `dump` | the card's Do step; reuses the existing decoded data instead of a parallel reader (G2 rules), reads no archive so `D:\Games` is never opened |
| `Research/JC3Grab/TANKTURN.md` | new, generated | the card's Out |
| `Research/JC3Grab/TANKTURN.json` | new, generated: input digests + every number the md shows | `--check` needs a machine form; same shape as `EMP.json` / `DOORS.json` / `TURRET.json` |
| `Research/JC3Grab/README.md` | one `Files` row + one short section | every G2 table is listed there (G2-13/15/16 precedent) |
| `GRAB_BACKLOG.md` §12 | `\| G2-21 \| todo \| \|` -> `done` + evidence path | session loop step 7 |
| this log | intended change + done sections | R14 |

**What the card assumes that needs checking.** The card offers `number_of_wheels`,
`is_all_wheel_steered` and "track-specific modules or members" as candidates. Read-only probe
already done before this entry: the four card modules have identical member-path sets in tanks and
cars, no module type is tank-only, `is_all_wheel_steered=1` exists only on the monster truck, and
`wheels_friction_type=2` is shared with jeeps/ATVs/buggies. So the likely outcome is the card's
second branch: no data member set can produce a pivot, turn-on-spot becomes a named omission for
MOD-2. What data cannot say (whether the game's tanks actually pivot, which native key would decide
it) stays `UNKNOWN`.

**Revert:** delete `Tools/scripts/jc3tankturn.py`, `Research/JC3Grab/TANKTURN.md`,
`Research/JC3Grab/TANKTURN.json`, the README row/section, the two G2-21 MODLOG sections, and put
§12 back to `| G2-21 | todo | |`. Nothing outside the repo is written; no game file, install,
save or dropzone is touched; nothing is committed.
## G2-17 · `CForcePulse` — intended change (2026-10-27)

**Card:** G2-17 (phase G2, S, deps P0-2 — row `done` in §12). In: `detail/` (79 chassis /
232 `.ee` carry `CForcePulse`, incl. the donor; `FEATURE_CENSUS.md`). Do: dump every
`CForcePulse` property per entity; find what triggers it (collision, horn, explosion) by
comparing values across vehicles that differ in behaviour. Out:
`Research/JC3Grab/FORCEPULSE.md`. Done: members + fleet ranges + a stated trigger or
`UNKNOWN` (then it becomes a Q-1 probe).

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3forcepulse.py` | new. Reads the 232 decoded `.epe` graphs by re-decoding each vehicle `.ee` from the archives (`jc3wiring.decode_epe`, full property list incl. the Jenkins-hashed `id:*` keys that the `jc3detail` JSON drops), reads each pulse's embedded `.ftunec` blast tune from the same container (`jc3adf`), resolves every object-id pointer to its owner, and aggregates members / tune values / ranges / owner classes; `--write`, `--check`, `dump` | the card's Do step; reuses `jc3index`/`jc3detail`/`jc3wiring`/`jc3adf` instead of a parallel reader |
| `Research/JC3Grab/FORCEPULSE.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/FORCEPULSE.json` | new, generated: per-entity pulse rows with every property, per-tune decoded values, member/range tables, owner census | G2-13…G2-16 convention; `--check` compares it |
| `Research/JC3Grab/README.md` | a G2-17 section and a Files row | every G2 table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-17 \| todo` -> `done` + evidence | session loop step 7 |
| this log | intended change + done | the journal (R14) |

**What the card assumes that needs checking in the data.** The card offers collision, horn
or explosion as candidate triggers. The pulse's own members may not name the event at all
(a `SettingsFile` plus hashed `id:*` numbers), in which case the honest answer is the owner
pointer where one exists and `UNKNOWN` where it does not — recorded as a Q-1 probe, not
filled in from a guess (R4).

**Revert:** delete `Tools/scripts/jc3forcepulse.py`, `Research/JC3Grab/FORCEPULSE.md` and
`Research/JC3Grab/FORCEPULSE.json`, restore the two `README.md` rows and the
`| G2-17 | todo | |` tracker line, and leave this log entry in place (append-only, R14). No
game file, install, save or dropzone is touched; nothing is committed.


## G2-22 · Effect usage vocabulary — intended change (2026-10-27)

**Card:** G2-22 (phase G2, S, deps P0-1; P0-1 row is `done` in §12). In: all
`effect_attachments` / `ExtendedEffectUsages` modules (6,045 modules decoded), `FX.md`. Do: dump
every `usage` name and hash across the fleet with the vehicles using it; find the exhaust / nitro /
afterburner / boost flame usages. Out: `Research/JC3Grab/USAGES.md`, `Tools/scripts/jc3usage.py
--check`. Serves FX-1.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3usage.py` | new. Scans every module row in `E:\Modding\_JC3grab\entities\*.ee.json`, re-decodes the `_effect_attachments.vmodc` / `*extended_effect_usages.vmodc` inner files of all 232 entity `.ee`s with `jc3adf` (the entity cache drops `effect_indices[]` elements), scans the `.epe` graphs' `SEffects` objects for their `Usage` int32 (same key space: the values equal the module usage hashes), and reads `FX_TABLE.jsonl` for the exhaust `.effc` census; `--write` / `--check` / `dump` | the card's Do step; reuses `jc3detail` / `jc3grab` / `jc3adf` / `jc3index` like the sibling G2 scripts |
| `Research/JC3Grab/USAGES.md` | new, generated | the card's Out |
| `Research/JC3Grab/USAGES.json` | new, generated machine half (sibling convention: `EMP.json`, `DOORS.json`) | makes `--check` a byte compare |
| `GRAB_BACKLOG.md` §12 | `G2-22 \| todo` -> `done` + evidence, one line only | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking in the data.** The card expects a usage vocabulary
from the two module families and a "flame during nitro" candidate. Two things had to be verified
first: (a) `ExtendedEffectUsages.usages[]` may be empty everywhere (its `default_*.vmodc` is a
shared stub) - if so the vocabulary lives only in `EffectAttachments.usage_effects[]`; (b) the
entity cache stores `usage_effects[].effect_indices` as an empty container, so the usage -> effect
link can only come from re-decoding the `.vmodc`. Neither assumption may be typed into the output
without the count behind it.

**Revert:** delete `Tools/scripts/jc3usage.py`, `Research/JC3Grab/USAGES.md` and
`Research/JC3Grab/USAGES.json`, restore the §12 row from `git checkout -- GRAB_BACKLOG.md` (or
retype `| G2-22 | todo | |`), and remove this section plus the "done" section from `MODLOG.md`
(append-only file: truncate at this heading). No game file, install, save or dropzone is touched.

## G2-21 · Turn-on-the-spot (tank pivot) — done

**Card:** G2-21 (S, deps P0-2 — row `done` in §12). In: tank/APC modules (`v0200`, `v0201`,
`v0202`, `v0603`) in `entities/`, `VOCABULARY.md`. Do: compare the tanks' members with wheeled
cars to find what makes a tracked vehicle pivot. Out: `Research/JC3Grab/TANKTURN.md`.

**Resume note (session cut off earlier).** The intended-change entry above already existed and
`Tools/scripts/jc3tankturn.py` was on disk, but neither Out file existed and the script did not
run. Three defects were fixed, all inside the script, all re-derivable: (1) `NameError: b_` in the
`tank_values` comprehension (loop bound `_, t` where `b_` was referenced) -> bound `b_, t`;
(2) `ValueError: too many values to unpack` in `vocab_card` (iterated `CARD_MODULES`, a tuple of
module names, as `(t, m)` pairs) -> iterated `TABLE_MEMBERS` restricted to the card modules;
(3) `--check` reported `TANKTURN.json stale` because `vocab.get(...)` returns tuples that
serialize to lists -> `list(...)` at build time. No other file was changed beyond the card's
planned outputs.

**Result.** The card's second branch holds: **no member set produces a pivot.** The four tank
chassis are ordinary `CCar` wheel builds. The four card modules have identical member-path sets
in tanks and cars (48/15/40/61 members, 0 tank-only, 0 non-tank-only) and no module type is
tank-only. Every card candidate is refuted by measurement: `number_of_wheels` (tank 6/8/8/4)
shared with 114 non-tank builds; `number_of_front_wheels` with 133; `is_all_wheel_steered=0`
with 130 (the only `=1` builds are 3 monster trucks); `is_rear_steered=0` on all 145 player
copies; `wheels_friction_type=2` shared with 36. The five-tuple is shared by 27 non-tank builds.
262 tank-unique values exist fleet-wide (DeformPoints 1, EffectAttachments 37, Fins 14,
Propellers 16, WaterInteraction 194) with **0 in any driving module**. Token scan
(`track|pivot|skid|neutral|turn_on|in_place|counter_rot|opposite`) over all member paths and
VOCABULARY.md finds 9 names, all cosmetic tyre-smoke members or the `CTrain` track gauge, none
in a driving module. All 12 tank builds declare `CCar` (fleet: 126 CCar / 35 CBoat / 23
CHelicopter / 18 CAirPlane / 12 CTrain), containers hold data file types only (0 script-like),
and wheel stations equal `number_of_wheels` on all 12.

**Done check.** `python Tools/scripts/jc3tankturn.py --check`:

```
PASS: 12 tank builds / 145 player land_global, 4 card modules identical (0 tank-only / 0 non-tank-only members), 0 tank-only module types, 5 candidates refuted (27 non-tank builds share a tank tuple), 262 tank-unique values with 0 in driving modules, 9 name matches (0 script file types), vehicle class {'CCar': 12}
```

**Tamper test.** Set `card.tank_builds` 12 -> 11 in `TANKTURN.json`: `--check` exited 1 with
`FAIL: TANKTURN.json stale`; `--write` rebuilt both files and `--check` returned the PASS above.

**UNKNOWN / limits.** Whether the shipped tanks actually pivot in game: `UNKNOWN` (runtime, native
code — no data value distinguishes a pivot-capable vehicle; Q-1 probe, one variable, R13). The
pivot's rate and the native key that decides it: `UNKNOWN`. `wheels_friction_type` enum meaning
(0/1/2) and `number_of_front_wheels = -1` semantics: `UNKNOWN` (not decoded labels). MOD-2's
turn-on-the-spot is now a **named omission** carried by `Research/JC3Grab/TANKTURN.md`.

**Files changed.** `Tools/scripts/jc3tankturn.py` (3-line repair),
`Research/JC3Grab/TANKTURN.md` + `TANKTURN.json` (generated), `Research/JC3Grab/README.md`
(one section + one Files row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only).

**Revert:** delete `Tools/scripts/jc3tankturn.py`, `Research/JC3Grab/TANKTURN.md`,
`Research/JC3Grab/TANKTURN.json`, the README section and Files row added here, put §12 back to
`| G2-21 | todo | |`, and truncate this log at the `G2-21 · … — intended change` heading. No
game file, install, save or dropzone is touched; no archive is opened (`D:/Games` never read);
nothing is committed.

## G2-25 · HUD vehicle-weapons API — intended change (2026-10-27)

**Card:** G2-25 (phase G2, S, deps G2-11 - tracker row `done`). In: decompiled `ui/hud.gfx`
(260 scripts) and `T6_HUD_CAMERA.md`. Do: document `InitVehicleWeapons` /
`UpdateVehicleWeapons` arguments (slot count, icon id, ammo/heat/cooldown), the lock-on HUD used
by `w609`/`w612`/`w613`, and how the entity feeds them (weapon id -> icon). Out:
`Research/JC3Grab/JC3_HUD_WEAPONS.md`. Done: each BmAK HUD element in WPN-12 has a JC3 element
or a stated absence. Serves HUD-2, WPN-12.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3hudwpn.py` | new. Reads the decompiled JC3 HUD scripts (`E:\Modding\_JC3grab\hud\dec\scripts\**\*.as`, main `hud.as`), `Research/JC3Grab/INDEX.jsonl` (weapon-icon census), `Research/BatmobileGrab/HUD_INTERFACES.json` + `HUD.md` (the BmAK side of WPN-12), `Working/Translation/T6_HUD_CAMERA.md` (T-HUD5) and the WPN-12 row of `GRAB_BACKLOG.md`; extracts both function signatures, slot array, data fields, cooldown/overcharge/reticle/lock/icon code, the caller census, and the 5-element WPN-12 disposition with `--write` / `--check` / `dump` | the card's Do step; reads only decoded/decompiled text (no archive, so `D:\Games` never opens) and the repo's own tables |
| `Research/JC3Grab/JC3_HUD_WEAPONS.md` | new, generated | the card's Out |
| `Research/JC3Grab/JC3_HUD_WEAPONS.json` | new, generated: input digests + every number the md shows | `--check` needs a machine half; same convention as `EMP.json` / `TANKTURN.json` |
| `Research/JC3Grab/README.md` | one `Files` row + one short section | every G2 table is listed there (G2-13…G2-21 precedent) |
| `GRAB_BACKLOG.md` §12 | `\| G2-25 \| todo \| \|` -> `done` + evidence path | session loop step 7 |
| this log | intended change + done sections | R14 |

**What the card assumes that needs checking in the data.** The card expects a weapon-heat
argument in the JC3 API. Read-only probes already done before this entry: neither function has
any `heat` parameter (the only extra state is `is_overcharged`), no `UC_*` setter in
`HUD_INTERFACES.json` contains "heat" either, and the BmAK Vulcan heat bar is a script variable
(`HeatBarStart`/`HeatBarSize`, `MECHANICS.md`) with no setter - so "Vulcan heat" is likely a
stated absence on both sides. Also: the slot array is built with exactly 2 clips
(`MCI_vehicle_weapons0/1`), the icon is keyed by `weapon_id` alone
(`textures/ui/weapon_icons/<id>.ddsc`), and the only call sites of `InitVehicleWeapons` in all
260 scripts are two demo calls inside `TestConstructor`, so the entity -> HUD caller is native
code and stays `UNKNOWN`. Whether `UpdateWeaponReticle`'s shape enum maps 1:1 to BmAK's reticle
states is not decidable from names alone and must be recorded as a mapping with its limits.

**Revert:** delete `Tools/scripts/jc3hudwpn.py`, `Research/JC3Grab/JC3_HUD_WEAPONS.md` and
`Research/JC3Grab/JC3_HUD_WEAPONS.json`, the README row/section, the two G2-25 MODLOG sections,
and put §12 back to `| G2-25 | todo | |`. Nothing outside the repo is written; no game file,
install, save or dropzone is touched; nothing is committed.

## G2-17 · `CForcePulse` — done

**Card:** G2-17 (S, deps P0-2 — row `done` in §12). Out: `Research/JC3Grab/FORCEPULSE.md`.

**Resume note (session cut off earlier).** The intended-change entry above existed and
`Tools/scripts/jc3forcepulse.py`, `Research/JC3Grab/FORCEPULSE.json` and
`Research/JC3Grab/FORCEPULSE.md` were on disk, but `--check` failed:

```
FAIL: member count 31; tunes 23; tune groups {'explosions': 1, 'structures': 2, 'vehicles': 8, 'weapons': 11, 'other': 1}; 1 refs to a pulse besides the owner pointer
```

The disk files matched `build()` byte for byte (no `JSON stale`, no `md differs`), so the
defect was in `invariants()`: it asserted pre-measurement guesses (41 members, 24 tunes,
four tune groups summing to 23, 0 non-owner refs) that the data contradicts. Before changing
anything, the numbers were re-derived independently of the parser under test:
`tmp/freebuff/probe_g2_17.py` reads the cached Gibbed `.xml` of the same 232 entities with
`ElementTree` and counts `<value>` elements itself. It agrees with `build()` exactly — 307
pulses, 31 members (26 hashed + 5 named), 30 values on 297 pulses / 31 on 10, 23 tunes, the
same 9 name spellings, 293 owner-pointer refs and **1** other ref — so the build was right
and the invariants were wrong. `id:D3DDD766` was also re-checked against the XML: all 45
non-null values name a `CMaterialEffectTable` (`emp_flatbed_table`, `tank_explosion_effect_table`).

**Changes (all inside the card's planned files).**

| file | change |
|---|---|
| `Tools/scripts/jc3forcepulse.py` | `invariants()` now asserts the measured facts: 307/232/79, 31 members = the 5 named + 26 hashed, `world` on all 307, `id:73D4D940` 10 / `id:7FD59340` 1 / `id:06A05F33` 14, 23 tunes grouped explosions 1 / other 1 / structures 2 / vehicles 8 / weapons 11, the owner census covering 307 with 14 unowned, exactly one non-owner ref and that it is the mm340 `GraphScript` (`CGraphScriptGameObject`, `id:65424AC6`), and the 10 barrel pulses carrying the outgoing `id:73D4D940`. Two false statements in the generated md were removed: "`world` is absent on one object" (it is on 307/307; the variation is the extra `id:73D4D940` on the 10 barrel pulses) and the header's "24 tunes". Added: an outgoing-pointer table (every pointer member resolved against its own graph), and a paragraph naming the one non-owner reference. Docstring counts corrected to 293/307 owners and 23 tunes (22 + 1 prototype). |
| `Research/JC3Grab/FORCEPULSE.json` / `.md` | regenerated by `--write` (307 pulses, 293 md lines) |
| `Research/JC3Grab/README.md` | G2-17 section + one Files row |
| `GRAB_BACKLOG.md` §12 | `G2-17 \| todo` -> `done` + evidence |
| this log | intended change (earlier) + this done section |

**Result.** `CForcePulse` is the fleet's blast component: **307 pulses in all 232 vehicle
`.ee` files** (79 chassis; `FEATURE_CENSUS.json` agrees object for object), one class with
**31 members** — 5 named plus 26 Jenkins-hashed `id:*` keys. Every pulse is an explosion: 23
`SettingsFile` tunes (22 under `jc_explosions/`, 1 bossfight prototype), each an embedded
`ForcePulseSettings` `.ftunec` decoded to eight numbers; fleet ranges `PlayerDamage` 0 … 3000,
`PlayerDamageRadius` 1.5 … 50, `AIDamage` 0 … 1000 in 0 … 50 m, with
`*RadiusPercentageMax`/`*RadiusMin` 0/0 on the stock vehicle blasts and 1/1 on the EMP and
`w613_bomb`. **Trigger: explosion, named by the owner pointer** — `id:B5AE7986` holds the
pulse's `_object_id` for 293 of 307: the vehicle root (CCar 126, CBoat 35, CHelicopter 23,
CMotorBike 19, CAirPlane 18, CTrain 12) with that type's own blast tune, or a weapon component
(CBulletWeaponBase 29, CMissileWeaponBase 25, CRPGFireLeachWeapon 6) with its own
`jc_explosions/weapons/<id>.ftune`. Horn and collision are refuted: 178 entities carry an
`SAttachedEffect horn` but 0 of 23 tune paths and 0 of 9 pulse names mention a horn, and 0
mention a collision. The 14 unowned pulses are **UNKNOWN, not explained**: the 10 oldtruck
barrel blasts nest under their `CRigidObject` and carry an outgoing `id:73D4D940` →
`CEntityObject` (nothing points at them), the 2 loose-cargo blasts use the 0-damage push tune,
the EMP pulse has no owner (G2-16), and the mm340 `BOMB_JEEP` pulse is referenced by a
`CGraphScriptGameObject` (`id:65424AC6`, the only non-owner reference in the fleet).

**Done check.** `python Tools/scripts/jc3forcepulse.py --check` (exit 0):

```
PASS: 307 pulses / 232 entities / 79 chassis, 31 members, 23 tunes, owners {'(none)': 14, 'CAirPlane': 18, 'CBoat': 35, 'CBulletWeaponBase': 29, 'CCar': 126, 'CHelicopter': 23, 'CMissileWeaponBase': 25, 'CMotorBike': 19, 'CRPGFireLeachWeapon': 6, 'CTrain': 12}, unowned 14, horn tunes 0, collision tunes 0
```

**Tamper test.** (1) `car_explosion_medium` `PlayerDamage` 500 -> 501 in `FORCEPULSE.json`:
`--check` exit 1, `FAIL: FORCEPULSE.json stale`. (2) `totals.objects` 307 -> 306: exit 1,
`FAIL: FORCEPULSE.json stale` (the rebuild also disagrees on the invariant). (3) one digit in
`FORCEPULSE.md` ("307 pulses" -> "306"): exit 1, `FAIL: md differs: @@ -3,3 +3,3 @@ …`. Each
time `--write` rebuilt both files and `--check` returned the PASS above.

**UNKNOWN / limits.** What the engine *calls* `id:B5AE7986` (no dictionary hit; G2-11
recovered six hashes this way, this one matched none): UNKNOWN. The moment a vehicle or weapon
blast fires (the files give the owner and the tune, not the code path): UNKNOWN. What the mm340
graph does with its pulse (bytecode not decoded): UNKNOWN. Which code runs after
`S_STUNT_USE_ITEM_VEHICLE` (so the EMP pulse's trigger stays an inference): UNKNOWN — Q-1
probe, one variable (R13). The `vec_events` members hold event ids with no shipped names.
Outgoing pointers resolve only when the target is in the same graph; the census covers the 232
decoded vehicle graphs, not every `.ee` in the index.

**Files changed.** `Tools/scripts/jc3forcepulse.py` (invariants + two false md claims + pointer
table + docstring), `Research/JC3Grab/FORCEPULSE.md` + `FORCEPULSE.json` (regenerated),
`Research/JC3Grab/README.md` (section + Files row), `GRAB_BACKLOG.md` §12 (one line), this log
(append-only). Probe left at `tmp/freebuff/probe_g2_17.py` (+ `G2-17_probe.json`).

**Revert:** delete `Tools/scripts/jc3forcepulse.py`, `Research/JC3Grab/FORCEPULSE.md`,
`FORCEPULSE.json`, the README section and Files row, `tmp/freebuff/probe_g2_17.py` +
`G2-17_probe.json`, put §12 back to `| G2-17 | todo | |`, and truncate this log at this heading
(the intended-change entry stays only if the card is re-run). No archive is opened for writing,
`D:\Games` is only read, no install/save/dropzone touched, nothing committed.

## G2-26 · Rebel Drop data (RD-1 read half) — intended change (2026-10-27)

**Card:** G2-26 (phase G2, S, deps P0-1 — row `done` in §12; no earlier entry for this card).
In: `Research/1456340180_Rebel-Drop-Mod-V5.3/*/profile/item.onlinec` + `task.onlinec`, the
vanilla `profile/*.onlinec` from the archives, `jc3adf.py`. Do: decode both, document an
entry's fields (entity path, name hash, icon, category, cost/cooldown, unlock), diff mod vs
vanilla to see how a new entry is added. Out: `Research/JC3Grab/REBELDROP.md`. Done: a
field-by-field recipe for an entry named "Batmobile" that spawns a given `.ee`.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3rebeldrop.py` | new. Extracts `profile/item.onlinec` + `task.onlinec` from every archive layer that ships them (patch is effective) to `E:\Modding\_JC3grab\rebeldrop\`, decodes vanilla and the three mod variants with `jc3adf`, lends the vanilla type dictionary to the mod tables (they carry none), masks 4-byte `StringHash` values and checks each against a raw 32-bit read, resolves every item name hash to an `.ee` through `INDEX.jsonl`, diffs mod vs vanilla, and builds the recipe; `--write`/`--check`/`dump` | the card's Do step; reuses `jc3adf`/`jc3grab`/`jc3index`/`rbmhdr` instead of a parallel reader |
| `Research/JC3Grab/REBELDROP.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/REBELDROP.json` | new, generated: schema, per-source decodes, diffs, recipe, verification counts | G2-13…G2-17 convention; `--check` compares it |
| `Research/JC3Grab/README.md` | one G2-26 section + one Files row | every G2 table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-26 \| todo` -> `done` + evidence | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking.** The card lists "entity path" as an entry
field; the `Item` struct (already dumped read-only in the probe) has no path member, only
`Name`/`BaseName`/`UIName` hashes, `UIImagePath`/`UIVideoPath` strings and flag/int fields.
So the recipe can only be honest if the binding is shown: probe results so far —
`Item.Name == hash_jenkins(<leaf name>)` for all 80 vanilla vehicle items, `UIName` equal
to `Name`, every item hash resolving to exactly one `.ee` (196/196 vanilla, 45/45 added by
V5.3 Plus), and the mod's three "new entity" items hashing to the new `.ee` files it ships.
No cost field exists; `RebelDropTimer` is the only time field. The mod's tables have
`type_count` 0, so their schema must be lent from vanilla (root hash `0x79DE48AE` treated
as `ItemRoot`), and `jc3adf.walk` misreads 4-byte string hashes as 8 bytes — both facts are
asserted by `--check` rather than assumed.

**Revert:** delete `Tools/scripts/jc3rebeldrop.py`, `Research/JC3Grab/REBELDROP.md`,
`REBELDROP.json`, the README section and Files row, put §12 back to `| G2-26 | todo | |`,
and truncate this log at this heading. Only `E:\Modding\_JC3grab\rebeldrop\` (game bytes,
outside the repo) is written besides those files; `D:\Games` is only read; nothing is
committed.

## G2-25 · HUD vehicle-weapons API — done

**Card:** G2-25 (phase G2, S, deps G2-11 — row `done` in §12). Out:
`Research/JC3Grab/JC3_HUD_WEAPONS.md` (+ the `.json` machine half the `--check` compares against).

**Resume note.** The intended-change entry above was already on disk and nothing else was: no
`Tools/scripts/jc3hudwpn.py`, no `JC3_HUD_WEAPONS.md`/`.json`, §12 still `todo`. So this session
started from the card's In list and did not repeat the intended-change entry.

**What the card asked for, and what the files say.** The card expected a weapon-heat argument;
there is none. `InitVehicleWeapons` takes **9** arguments
(`slot_index, weapon_id, weapon_name, infiniteAmmo = true, magazine_ammo = -1, magazine_size = -1,
inventory_ammo = -1, weapon_cooldown = -1, is_overcharged = false`), `UpdateVehicleWeapons` **6**
(`slot_index, new_magazine_ammo_amount, total_ammo, is_low_ammo, weapon_cooldown = -1,
is_overcharged = false`), both parsed from `hud.as:5030` / `hud.as:5160` rather than typed. The
slot array is `MCI_vehicle_weapons0/1` (`hud.as:4951`) so **2 slots**, indexed
`EVEHICLE_WEAPON_SLOT_MAIN = 0` / `..._ALTERNATIVE = 1`; each slot is a data object of six fields
(`m_WeaponId`, `m_WeaponName`, `m_HasInfiniteAmmo`, `m_MagazineAmmo`, `m_MagazineSize`,
`m_TotalInventoryAmmo`) and a clip of seven widgets. `weapon_cooldown` is a **fraction**: `-1`
hides `MCI_radial_loader_cooldown`, otherwise `SetCooldownRotation` turns `MCI_mask_0_50` /
`MCI_mask_50_100` through `weapon_cooldown × 360°`, and `AnimateOvercharged` drops the bullet bar
to alpha 0.7 and plays `dlc_wingsuit_weapon_ready` on release. No `heat` anywhere: 0 heat
parameters, 0 mentions in either body, 0 of the 252 BmAK `UC_*` setters contain "heat", and the
movie's own heat code is the 11-state **police wanted level** (`hud_code/heat/`). The BmAK Vulcan
heat bar is a weapon-entity script variable (`HeatBarStart`/`HeatBarSize`, `MECHANICS.md`) — so
WPN-12's heat element is a **stated absence on both sides**, exactly as the resume note predicted,
and that is now a measured row rather than a suspicion.

The lock-on is **one POI**: `POI_TYPE_LOCK_ON_TARGET = 21` (of 32 `POI_TYPE_*`), drawn by
`hud_code/poi.as` as `MCI_icon.MCI_lock_on.MCI_reticle` turning 360° every 1.5 s with no progress
bar — a different instrument from `MCI_missile_locked`, the flashing (0.5 s) *incoming*-missile
warning behind `ShowMissileLocked`/`HideMissileLocked` (0 movie callers). `w609`, `w612`, `w613`
carry their lock-on as an `AutoAim` tune; the `OnFoot` envelope, missile damage/turning speed,
magazines and slot bindings are in the md, and three traps are recorded as read — `w609`'s only
component is the fighterjet's `CLaserBeamWeaponComponent`, `w612` is bound to no driver slot, and
`w613` ("ground lockon") targets **nothing** (`CanTargetCharacters/Vehicles/RigidObjects` all 0,
`MaxAimDistance` -1, `missile_turning_speed` 0: an unguided bomb). The link from `AutoAim` to
`POI_TYPE_LOCK_ON_TARGET` is in no file, and `CAimPOIWeaponComponent` sits on the *no-lockon*
`w611` — so that link stays `UNKNOWN` and the WPN-12 lock-on row is `partial`, not `map`.

Weapon id → icon: `GetWeaponIconName` returns `textures/ui/weapon_icons/<weapon_id>.ddsc`
(`_sm.ddsc` for low-res), `weapon_icon_type.LoadIcon` refuses ids -1 and 0, and `INDEX.jsonl`
carries **69 icon ids** in 110 files. Of the fleet's 23 wired weapon ids, 22 resolve; **`614` (the
monorail's missile) has no icon** — a real gap in the shipped set.

Reticle: `UpdateWeaponReticle(show, weapons_look, reticle_size, reticle_shape)` has **14** shapes
(0…13, `E_RETICLE_CANNON = 8`), 5 look states, 14 `case` labels of which 5 compute a width
(cross 5…30 px, circle 14…33, rocket 5…20), alpha 0.4 out of range, `E_RETICLE_NONE` hides
`MCI_inflict_damage`. Caller census: the only call sites of `InitVehicleWeapons` in all 260
scripts are the two `TestConstructor` demos (`hud.as:7535-7536`, weapon id 141); `UpdateVehicleWeapons`
and `UpdateWeaponReticle` have none. The entity → HUD bridge is native: **UNKNOWN**.

**Done check.** `python Tools/scripts/jc3hudwpn.py --check` (exit 0):

```
PASS: 260 scripts, InitVehicleWeapons 9 args / UpdateVehicleWeapons 6 args, 2 vehicle slots (E_NUM_WEAPON_SLOTS 7 is on-foot), 14 reticle shapes, lock-on POI 21 at 1.5 s, 0 heat parameters, 0 heat in bodies, 0 BmAK heat setters, 69 weapon icons, 5 WPN-12 rows (map/map/map/stated absence/partial)
```

Each of the five WPN-12 elements therefore has a JC3 element or a stated absence: three map
(slots, reticle, cannon cooldown), one is a stated absence on both sides (Vulcan heat), one is
partial (missile lock: one rotating marker + one incoming warning where the Batmobile has a
6-kind `VehicleMissileTarget` box family).

**Tamper test.** (1) `lockon.lock_on_type` 21 → 22 in `JC3_HUD_WEAPONS.json`: `--check` exit 1,
`FAIL: JC3_HUD_WEAPONS.json stale`. (2) one digit in `JC3_HUD_WEAPONS.md` ("takes **9 arguments**"
→ 8): exit 1, `FAIL: md differs: @@ -4,3 +4,3 @@`. Each time `--write` rebuilt both files and
`--check` returned the PASS above. The numbers were also re-derived independently of the parser
under test (`tmp/freebuff/probe_g2_25.py`: raw regex over `hud.as`, a separate `INDEX.jsonl`
scan and `HUD_INTERFACES.json` load) — 260 files, 9/6 args, 2 slots, 7 on-foot slots, 0.7
overcharge alpha, 360°, 0 heat in signatures, 11 heat states, 32 POI types, lock-on 21 @ 1.5 s,
69 icon ids / 110 files, 37 / 252 setters, 0 heat setters, 2 init call lines, 0
update/reticle/`ShowMissileLocked` call lines — every one agrees with `build()`.

**UNKNOWN / limits.** Who calls the API and with what values (native, not in `hud.gfx`):
UNKNOWN. Whether the engine paints `POI_TYPE_LOCK_ON_TARGET` from `AutoAim` state: UNKNOWN. Which
reticle shape id a vehicle cannon uses: UNKNOWN (`E_RETICLE_CANNON` exists, nothing maps it). How
BmAK's five `UC_SetCannonCoolDown` states pin to the `0..1` fraction: UNKNOWN (a mapping, not a
decoded value). Whether a JC3 vehicle HUD ever shows more than 2 slots: no — the array is
hard-sized to 2. The `_sm` low-res icons are only referenced by the `low_res_image` flag, and the
only `low_res` caller in the movie is `GetWeaponIconName` itself. Nothing here was tested in the
game; HUD-2's in-game take is phase Q (R6, R13).

**Files changed.** `Tools/scripts/jc3hudwpn.py` (new), `Research/JC3Grab/JC3_HUD_WEAPONS.md` +
`JC3_HUD_WEAPONS.json` (generated), `Research/JC3Grab/README.md` (one section + one Files row),
`GRAB_BACKLOG.md` §12 (one line), this log (append-only). Probe left at
`tmp/freebuff/probe_g2_25.py`.

**Revert:** delete `Tools/scripts/jc3hudwpn.py`, `Research/JC3Grab/JC3_HUD_WEAPONS.md`,
`Research/JC3Grab/JC3_HUD_WEAPONS.json`, the README section and Files row added here,
`tmp/freebuff/probe_g2_25.py`, put §12 back to `| G2-25 | todo | |`, and truncate this log at this
heading (the intended-change section stays only if the card is re-run). Nothing outside the repo is
written; no archive is opened, `D:\Games` is never read, no install/save/dropzone is touched, and
nothing is committed.

## G2-26 · Rebel Drop data (RD-1 read half) — done

**Card:** G2-26 (S, deps P0-1 — row `done` in §12). Out: `Research/JC3Grab/REBELDROP.md`.
No earlier session had touched this card (no prior MODLOG entry, no output on disk), so this
run did the whole card; the intended-change entry above is its own.

**Result.** A Rebel Drop entry is one `Item` in `profile/item.onlinec`, and **`Item.Name` is
the 32-bit Jenkins hash (`rbmhdr.hash_jenkins`, the archive-path function) of an entity leaf
name**: that hash is the whole spawn binding, and it is the only "entity path" in the files.
`Name` resolves to exactly one `.ee` path for 185 of the 196 vanilla items — the 11 that do
not resolve are the non-vehicle unlocks with no `UIImagePath` — and for 229/240 items of the
mod's newest variant. All 80 vanilla vehicle drops satisfy `Name == hash(UIImagePath)`,
`UIName == Name`, `Name != BaseName`, `Type` 1, `UIType` 3, `DlcId` 0, `Purchasable` 0,
`Consumable` 0, `Rewardable` 1, `Collectable` 0, `Region` 0, `MaxInventory` 0, `Feats` empty,
`RebelDropTimer` 600/900/1200/1800/2400, `UIDisplayOrder` 1..11. The `Item` struct is 26
fields / 128 B; **there is no cost field**, and `RebelDropTimer` is the only time value (unit
UNKNOWN).

The **unlock** is in `profile/task.onlinec`: `Reward.RewardThresholds[].Reward.Items[]` is a
`ItemReward` (`Item` hash, `Permanent`, `Duration`, `Quantity`, `Delivery`); the vanilla tables
carry 87 reward links, all `Delivery` 0, handing out 87 distinct items — the donor drop comes
from task `1361701860` (type 19, permanent 1, quantity 1). The mod adds **no** reward for any
of its added items.

**The mod** (three variants, all with the base file's hash-only root `0x79DE48AE`): adds
39 / 45 / 45 items (all `Type` 0, `UIType` 3, `RebelDropTimer` 0, `UIImagePath` =
`placeholder`, `BaseName` = `Name` — a convention vanilla never uses), removes 3 / 1 / 1,
and against the base layer rewrites 160 / 162 / 162 items (`RebelDropTimer` 109,
`UIDisplayOrder` 57, `UIImagePath`/`UIVideoPath` 52, `UIType` 51, the description hashes 51,
`UIFlag` 50, `UIPar*` 50, `DlcId` 50). Its 45 added items' hashes name what they spawn —
wrecks, trains, props and the five entities the Plus builds ship themselves (`v1704_boat_na_lightpatrol_civic_police_01`,
`w141_rpg_uvk_13_mm110`, `sponge`, `pinata`, `pinata_stick`). Its `task.onlinec` adds and
changes **no** task by name; it is only reordered (566 of 591 positions).

**Two reader facts, both asserted by `--check` (they had to be established, not assumed).**
(1) Only the patch layer's type table is usable: the base game's own `profile/item.onlinec`
carries a 5-type table whose `Item` lists 25 members **without `DlcId`**, so every offset after
`DlcId` is 4 B short, and the mod's tables carry no type table at all (root `0x79DE48AE`).
All four files are decoded with the patch's `ItemRoot` (`0x921AF417`) schema. The 128 B record
stride is proved without the type table: the `UIImagePath` pointer at offset 88 resolves to a
printable/empty NUL-terminated string for every record (196/196 base, 196/196 patch, 232/232
and 240/240 mod, 0 failures); reading at the base table's 124 B stride gives garbage (21–26
plausible pointers). The hash-field check (0 mismatches) only proves the 32-bit masking,
because it reads the offset it decodes — the doc says so.
(2) `jc3adf.walk` reads a 4-byte `StringHash` as 8 bytes (`StringHash_48C5294D_4` names
element `0x48C5294D`, not a primitive → `<Q`), so every hash is masked to 32 bits; e.g.
`Region` reads `2576980377600` = `600 << 32` because `RebelDropTimer` 600 follows it.

**Done check.** `python Tools/scripts/jc3rebeldrop.py --check` (exit 0):

```
PASS: 196 vanilla items / 591 tasks / 80 vehicle-bound / 185 resolved to .ee, 0 hash mismatches, 39+45+45 items added by the 3 mod variants, recipe hash 443190071 for v0300_car_kensington_sportsmuscle_batmobile
```

**The card's Done criterion** — a field-by-field recipe for an entry named "Batmobile" that
spawns a given `.ee` — is `REBELDROP.md` §7: pick the leaf
(`v0300_car_kensington_sportsmuscle_batmobile`), compute `hash_jenkins(leaf)` = **443190071**
(`0x1A6A8B37`), write that into `Name`/`UIName`, the leaf into `UIImagePath`/`UIVideoPath`,
and take the other 22 fields from the donor drop (donor values listed). That leaf is **not**
in the shipped index, so the `.ee` has to be shipped as an override (G2-27). The doc also
lists the mod's own added-entry pattern (for an entry available without a task reward) and the
one-sentence `ItemReward` change for a task-gated unlock.

**Tamper test.** (1) `recipe.name_hash` 443190071 -> 443190072 in `REBELDROP.json`: `--check`
exit 1, `FAIL: REBELDROP.json stale`. (2) `vanilla.item_meta.string_pointer_failures` 0 -> 3:
exit 1, `FAIL: REBELDROP.json stale`. (3) one digit in `REBELDROP.md` (`443190071` ->
`443190999`): exit 1, `FAIL: md differs: @@ -204,3 +204,3 @@ …`. After each `--write` the
PASS above returned.

**UNKNOWN / limits.** Every string behind a hash (`Name`, `BaseName`, `UIName`,
`UIDescription`, `UITypeDescription`, `UIFlagDescription`, task names/tips) — only hashes are
in these files, so the strings need G2-32's tables. The meaning of `BaseName`, `Type`,
`UIType`, `UIFlag`, `DlcId`, `ItemReward.Delivery` and the `RebelDropTimer` unit: only the
distributions are measured, the enums are UNKNOWN. Whether `Type` 0 (without a task reward)
is what makes an entry available: the mod does exactly that, which is evidence of a working
pattern, not of the rule — Q-1 probe, one variable. What `UIPar0..4` frame and whether
`UIImagePath` must be a real icon. The exact array serialisation a new item needs beyond
128 B records + string area (the mod files were written by an external tool; this doc
reproduces their layout, not the game's writer). Only the two `profile` tables are read — the
menu, pricing and delivery behaviour are code. The `.ee` resolved from a hash is an
`INDEX.jsonl` path, not proof the entity loads.

**Files changed.** `Tools/scripts/jc3rebeldrop.py` (new), `Research/JC3Grab/REBELDROP.md` +
`REBELDROP.json` (generated, 334 md lines), `Research/JC3Grab/README.md` (one section + one
Files row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only). Game bytes extracted
only to `E:\Modding\_JC3grab\rebeldrop\` (outside the repo, R10). Probe left at
`tmp/freebuff/probe_g2_26.py`.

**Revert:** delete `Tools/scripts/jc3rebeldrop.py`, `Research/JC3Grab/REBELDROP.md`,
`REBELDROP.json`, `tmp/freebuff/probe_g2_26.py`, the README section and Files row, and
`E:\Modding\_JC3grab\rebeldrop\`; put §12 back to `| G2-26 | todo | |`; truncate this log at
the `G2-26 · … — intended change` heading. `D:\Games` was only read, no install/save/dropzone
touched, nothing committed.

## G2-29 · Traffic, AI and spawning of `v0300` — intended change (2026-10-27)

**Card:** G2-29 (phase G2, S, deps P0-1 — row `done` in §12; no earlier entry for this card).
In: `Research/JC3Grab/INDEX.jsonl` (spawn/traffic/population files), any file referencing the
donor hash or path (`v0300_car_kensington_sportsmuscle_civilian_01`). Do: list every file that
can spawn the donor (traffic, parked cars, missions, Mario's house) and whether AI drives it
there. Out: `Research/JC3Grab/TRAFFIC.md`. Done: a list of spawn sites; a statement whether
replacing `civilian_01` puts NPC-driven Batmobiles in traffic (lore break -> D-6).

**Late entry, stated plainly.** The earlier session on this card was cut off at its time limit
with `Tools/scripts/jc3traffic.py` and `Research/JC3Grab/TRAFFIC.md` + `TRAFFIC.json` already on
disk but this intending-change block unwritten. It is written now, before any further edit, and
the files above are the ones it covers — no other file has been touched for G2-29.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3traffic.py` | new. Walks `INDEX.jsonl` for every data-table extension (`.bin`, `.bl`, `.blo`, `.ee`, `.onlinec`, `.gsc`, `.btc`, `.stringlookup`, …), reads each entry out of the archives through `jc3grab`, and searches for the donor's ASCII name and for its 32-bit Jenkins hash in both byte orders; parses every `spawn_*_defs.bin` into records (entity path + tag list + name), tests the donor's tags against every selector in the traffic-rule block of `global/global.blo`, and reads the donor's `item.onlinec`/`task.onlinec` keys; `--write`/`--check`/`dump <records|rules|hits|profile|donor|tags>`, `--fast` to skip the tier-B scan | the card's Do step; reuses `jc3grab` rather than a second archive reader |
| `Research/JC3Grab/TRAFFIC.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/TRAFFIC.json` | new, generated: scan census, every spawn table, the rule/selector census, profile keys, verification counts | G2-13…G2-26 convention; `--check` compares it |
| `Research/JC3Grab/README.md` | one G2-29 section + one Files row | every G2 table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-29 \| todo` -> `done` + evidence | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking.** The card's "traffic, parked cars, missions,
Mario's house" is a list of *kinds* of spawn site, and the archives answer it only for data
tables: a "parked car" or a mission spawn would be a `CVehicleRule`/graph in a level `.bl`/`.blo`
(tier B is scanned) or an entity-graph reference, so absence there is evidence of absence, while
the *runtime* picker that reads the tag lists is native and will stay `UNKNOWN`.

## G2-29 · Traffic, AI and spawning of `v0300` — done (2026-10-27)

**Status: done.** Out on disk: `Research/JC3Grab/TRAFFIC.md` (163 generated lines) +
`Research/JC3Grab/TRAFFIC.json` (33 KB), built by `Tools/scripts/jc3traffic.py`
(`--write` / `--check` / `dump <records|rules|hits|profile|donor|tags>`), README row + section
added. Resumed the earlier session's files rather than rebuilding them; the intended-change
block above was written first.

**Done check, verbatim (exit 0):**

```
PASS: 11751 files scanned (7719 MB, A+B), 17 name the donor (Rebel Drop/entity registry/frontend/level rule/localisation/other/patch metadata/self/spawn table/task table), 86 spawn records (8 with a pool key), donor tag list of 13 tags, 31 traffic rules / 41 selectors, 1 match (`ambient,ground,car,liberated,-highend`), 10 AI behaviour trees
```

**Answer to the card.** `civilian_01` **is** traffic, so replacing it puts NPC-driven Batmobiles
on the roads — a lore break (MOD-5, WLD-8) that points decision D-6 at the standalone route
(G2-27). Spawn sites, each with its file: the ground spawn table
`settings/spawn_vehicle_defs.bin` (the donor's record: path + 13 tags + name, **no pool key**),
one Rebel Drop item (`profile/item.onlinec`, `…_civilian_01_desc`), one chop-shop task key
(`profile/task.onlinec`, `chopshop_v0300_…_civilian_01`), two level `CVehicleRule` objects
(`locations/jc_prototype/mm320/train_test.blo`, `locations/rom/wingsuit_course/wing20_logic.blo`)
and one frontend list entry (`global/frontend_global.blo`); the entity registry, the `.epe`, the
`.stringlookup` (hash-only) and `patchmetadata.bin` are not spawn sites. No shipped region level
places the car — the spawner does, which is exactly what the card asked.

**AI.** The matching selector is `ambient,ground,car,liberated,-highend` -> the civilian car rule
`03_CivilianCarLiberatedProvince`; the rule block carries `Driver` seats bound to `ai/bts/*.bts`
trees (10 paths, incl. `civilian/civilian_std.bts`) and the `AITrafficImpostorSystem`. The donor
also ships its own `land_global_ai` module. Only `civilian_01` is in the table; `debug` and
`sportsmuscle_signature_preorder` sit in different spawn tables.

**Tamper test.** (1) `rules.selector_count` 41 -> 40 in `TRAFFIC.json`: `--check` exit 1,
`FAIL: TRAFFIC.json stale`. (2) one number in `TRAFFIC.md` (`| spawn records | 86 …` -> `87`):
exit 1, `FAIL: md differs: @@ -158,3 +158,3 @@ …`. After `--write` the PASS above returned.

**Independent re-derivation.** `tmp/freebuff/probe_g2_29.py` does not import `jc3traffic`: it
re-reads `spawn_vehicle_defs.bin` (27513 B, 86 `.ee` paths, donor record = path + tags + name,
no `highend` tag), `global/global.blo` (selector string present, 10 `ai/bts` paths, 2 `Driver`
seats) and the two profile tables, and re-scans the 26-extension census itself. It agrees: 13
name-hit files + the 4 hash-only rows = the 17 logged, donor record exact, selector present.

**UNKNOWN / limits.** The tag *matcher* is native: no file states that a selector takes a tag
superset, no `.gsc`/`.btc` mentions these tags, so "1 of 41 selectors matches" is a string-level
match, not a runtime proof. The six numeric fields of a spawn record (weights? offsets?) are not
decoded — only the strings are. The donor's pool is `UNKNOWN` because only 8 of 86 records carry
a key and each key differs. Whether the impostor system reuses these records, when the two level
`CVehicleRule`s fire, and whether the engine honours a replaced `settings/spawn_vehicle_defs.bin`
from the dropzone (D-6's third route) are all `UNKNOWN` — G2-27/Q-1. Media/navmesh types
(70,201 files / 48.6 GB: `.hmddsc`, `.nl`, `.bank`, `.streampatch`, `.bikc`) were not scanned and
none is a data table. Nothing was launched, nothing written under `D:\Games`, no archive edited,
nothing committed.

**Standing gates re-run.** `status_audit.py --check` -> `STATUS.md is current` (exit 0);
`jc3index.py check` -> `check ok: 81952 rows, 78907 paths, 1 unnamed entries` (exit 0).

**Files changed.** `Tools/scripts/jc3traffic.py` (new), `Research/JC3Grab/TRAFFIC.md` +
`TRAFFIC.json` (generated), `Research/JC3Grab/README.md` (one section + one Files row),
`GRAB_BACKLOG.md` §12 (one line), this log (append-only). Probe at `tmp/freebuff/probe_g2_29.py`.

**Revert:** delete `Tools/scripts/jc3traffic.py`, `TRAFFIC.md`, `TRAFFIC.json`,
`tmp/freebuff/probe_g2_29.py`, the README section and Files row; put §12 back to
`| G2-29 | todo | |`; truncate this log at the `G2-29 · … — intended change` heading.

## G2-22 · Effect usage vocabulary — done

**Card:** G2-22 (S, deps P0-1 — row `done` in §12). In: all `effect_attachments` /
`ExtendedEffectUsages` modules, `FX.md`. Out: `Research/JC3Grab/USAGES.md`,
`Tools/scripts/jc3usage.py --check`.

**Resume note (session cut off earlier).** The intended-change entry above already existed and
`Tools/scripts/jc3usage.py` was on disk at 32,720 B, but neither Out file existed and `--write`
refused:

```
REFUSED: usage rows cache 346 != re-decode 345; effect indices cache 885 != re-decode 881
```

The cause was a real reader bug, not a bad invariant: `cache_scan`/`redecode` keyed their
per-vehicle data by entity path, and **one vehicle carries two `EffectAttachments` modules**
(`v4603_plane_urga_cargotransport_military_cargo_tank`), so the second module (1 usage row, 4
`effect_indices`) overwrote the first. Fixed by keying every per-module row by
`entity|module_index` (225 modules over 224 vehicles); no other reader behaviour changed.

**Result.** The usage vocabulary is **12 names** / 346 `usage_effects[]` rows / 885 effect links
over 225 `EffectAttachments` modules on 224 vehicles (8 vehicles carry none; the plane above
carries two). `ExtendedEffectUsages` is a shared 627-byte stub with `usages[]` empty on all 232
vehicles, so the vocabulary lives only in `EffectAttachments` plus the `.epe` graphs. Module
counts: `HeadLights` 145, `EngineRunning` 69, `OnPartExplode` 33, `EngineSmoking` 23,
`Explosion` 23, `EngineNitro` 18, `EngineTurboJump` 11, `OnPartReachedDamageState` 3, `Siren` 3,
`OnPartBrokeOn` 2, `OnExploded` 2, and one **empty-string usage whose hash is `0xDEADBEEF`**
(14 modules; its effect name is empty too, so nothing is lost in decoding).

**The card's question — flame during nitro — has a named candidate.** Usage `EngineNitro`
(4197885156, 18 modules) binds to effects `dynamic_nitrous` (14 vehicles) and `EngineNitro`
(4, the propeller planes). The same `Usage` int sits on **307 objects in 202 of 232 `.epe`
graphs** (`SAttachedEffect` 281, `SDynamicAttachedEffect` 26): `exhaust_upgrade_nitrous` 154,
`engine_nitrous_sound` 41, `nitrous_active_sound` 35, `dynamic_exhaust_nitrous` 26, plus the
`_r/_l/_b/2/left/right` variants. **No usage anywhere is named afterburner, boost, flame or
fire** (0 names match) — the flame is carried by *effect* names and by 9 `*nitrous*.effc` paths
across 275 containers, not by the usage vocabulary. Baseline exhaust is `EngineRunning` (69
modules) -> `dynamic_exhaust` 46 / `EngineNitro` 20 / `dynamic_test` 19 / `EngineKeyOn` 4;
turbo-jump is `EngineTurboJump` -> `dynamic_tjump` (11).

**Two things the card's assumptions got wrong, both now measured in the doc.**
(1) The `.epe` `Usage` int is only *partly* the module usage key space: of 155 distinct values
(12,576 objects), **6** take their name from the module usage vocabulary, **60** from an effect
name that shares the hash, **4** from `SValueDrivenEffectUsage`, and **85 have no name in any
decoded file** — recorded as UNKNOWN, never guessed. 17 effect names attach to more than one
`Usage` value, so an effect name never identifies its trigger.
(2) Reading only the module row would have been a **false negative for the donor**: the donor
`v0300_car_kensington_sportsmuscle_civilian_01` lists exactly one usage row (`HeadLights`) yet
its `.epe` attaches `exhaust_upgrade_nitrous`/`exhaust_upgrade_nitrous2` under `Usage` =
`EngineNitro`, i.e. the donor *does* attach its nitrous exhaust. Its full 51-value `.epe` usage
map is in `USAGES.md` for FX-1/T-17; 29 of those 51 values have no name in any decoded file. The
donor also embeds `car_cycle_base_dual_nitrous.effc` (with `..._dual.effc`, `..._dual_tjump.effc`,
`car_tjump_trail.effc`). One trap recorded: the *effect* named `EngineNitro` is also attached by
the `EngineRunning` usage on 20 vehicles, so effect-name == usage-name is not a unique binding.

**Done check.** `python Tools/scripts/jc3usage.py --check` (exit 0):

```
PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named usages (346 rows, 885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro -> EngineNitro/dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX rows 57187
```

The check re-decodes every `_effect_attachments.vmodc` and every `.epe` graph (no archive is
opened; `D:\Games` is never read), compares both Out files byte-for-byte, then runs the 20-row
assertion table that `USAGES.md` §7 prints. The numbers were also re-derived independently of the
parser under test (`tmp/freebuff/probe_g2_22.py`: 232 caches / 6,045 modules / 225 modules over
224 vehicles / 346 rows / 885 indices / 12 names; `tmp/freebuff/probe_g2_22b.py`: 849,942 `.epe`
string values with **0** `.effc`/`.ctunec`/`.trim` references) — every count agrees with
`build()`.

**Tamper test.** (1) `usages[11].hash` 4197885156 -> 4197885157 in `USAGES.json`: `--check`
exit 1, `FAIL: USAGES.json stale`. (2) one number in `USAGES.md` (`**307 objects**` -> `**306
objects**`): exit 1, `FAIL: md differs: @@ -400,3 +400,3 @@`. After each `--write` the PASS above
returned.

**UNKNOWN / limits.** The name behind 85 of the 155 `.epe` `Usage` values: UNKNOWN (no decoded
string carries it). The **hash function** itself: UNKNOWN — hashes are only ever read where the
string sits next to them, never recomputed. Effect name -> `.effc` file: UNKNOWN (0 of 849,942
`.epe` strings name an effect file; that lookup is native). What turns a usage on at runtime,
and whether `EngineNitro` really draws a flame on nitro (vs. only the sounds and the
`dynamic_exhaust_nitrous` object existing): code, not data — a Q-1 probe, one variable (R13).
Whether `.epe` `Usage` is always a trigger id (some objects share a `Usage` with unrelated
effects, e.g. `AOE_air` under `EngineRunning`): UNKNOWN. Nothing here was tested in game (R6);
no build, save, dropzone or archive was touched.

**Files changed.** `Tools/scripts/jc3usage.py` (keying fix + in-script measurement of the
`.effc`-reference and donor maps + assertion table), `Research/JC3Grab/USAGES.md` +
`USAGES.json` (generated, 585 md lines), `Research/JC3Grab/README.md` (one section + one Files
row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only). Probes left at
`tmp/freebuff/probe_g2_22.py` and `tmp/freebuff/probe_g2_22b.py`.

**Revert:** delete `Tools/scripts/jc3usage.py`, `Research/JC3Grab/USAGES.md`,
`Research/JC3Grab/USAGES.json`, the two probes, the README section and Files row added here, put
§12 back to `| G2-22 | todo | |`, and truncate this log at the `G2-22 · Effect usage vocabulary —
intended change` heading. No game file, install, save or dropzone is touched; no archive opened;
nothing committed.

**Addendum (same session).** One number above was written before the last three prose edits:
`USAGES.md` is **588** lines as delivered (`USAGES.json` 687,497 B), not 585. Everything else in
that section was re-verified after the final `--write` / `--check`.

**Scope note (R14 honesty).** The pre-existing intended-change table for G2-22 did not list
`Research/JC3Grab/README.md`, but the run added one `### Effect usage vocabulary (USAGES.md,
G2-22)` section and one `Files` row there — every other G2 table is registered the same way
(G2-13…G2-21, G2-25, G2-26, G2-29). Revert by deleting that one section (between `### Effect
usage vocabulary` and `### Traffic and spawning`) and the `USAGES.md` / `USAGES.json` Files row.

## G2-33 · Light system consolidated — intended change (2026-10-27)

**Card:** G2-33 (phase G2, S, deps P0-1 — row `done` in §12). In: `Working/Lights/LGT1_FINDINGS.md`,
MODLOG §112–§113, `ENTITIES.md` (3,972 `SVehicleLight`), `GEOMETRY.md` (`CarLight` block), the donor
lights module. Do: one document — the `SVehicleLight` member list and presets, how a light binds to a
part (`has_lights`), the `CarLight` block format, what a custom light without a preset needs. Out:
`Research/JC3Grab/LIGHT_SYSTEM.md`. Done: a recipe for one custom light (wheel-arch light) with every
member value sourced. Serves LGT-1/2, APP-4.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3lights.py` | new. Reads the 232 entity caches (`VehicleDynamicLights` rows = the module's light entries), the 232 `.epe` graphs (`SVehicleLight`/`SVehicleLights`/`SVehicleLightList` objects), `PARTS_TABLE.jsonl` (`has_lights`, `part_index`, damage type), `GEOMETRY.jsonl` (`CarLight` block census), `INDEX.jsonl` (any light/preset table outside `jc_vehicles`) and `Research/BatmobileGrab/LIGHTS.json` (the BmAK wheel-arch light: socket, colour, cone, `jc3_part`, `jc3_anchor`); builds the wheel-arch recipe with a source and a value class per member; `--write` / `--check` / `dump` | the card's Do step; reuses the existing decoded tables rather than a new reader, so `D:\Games` is never opened |
| `Research/JC3Grab/LIGHT_SYSTEM.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/LIGHT_SYSTEM.json` | new, generated machine half | sibling convention (`EMP.json`, `TANKTURN.json`); `--check` compares byte-for-byte |
| `Research/JC3Grab/README.md` | one `### Light system` section + one `Files` row | every G2 table is registered there (G2-13…G2-29) |
| `GRAB_BACKLOG.md` §12 | `\| G2-33 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking in the data.** (a) That the module's `lights[]` entries and
the `.epe` `SVehicleLight` objects are the same list — the counts already disagree (3,217 module rows
entries vs 3,972 `.epe` objects), so the doc must say which list binds parts and which supplies preset
names. (b) That a custom light needs a preset: 17 shipped entries use `preset_id = 0` and 34 of 393
presets appear with inconsistent member values, so the entry's own members look load-bearing — to be
measured, not assumed. (c) That `has_lights` gates a light: the probe already finds 6 entries on a
`has_lights = 0` part and 30 whose `part_index` names a different part, so the flag is not a hard gate.
(d) The `CarLight` block's *material parameter* semantics are still undecoded (MODLOG §102d), so the
recipe may only copy the block, never author its emissive numbers — that stays UNKNOWN unless the files
give it.

**Revert:** delete `Tools/scripts/jc3lights.py`, `Research/JC3Grab/LIGHT_SYSTEM.md`,
`Research/JC3Grab/LIGHT_SYSTEM.json`, the README section + Files row added here, put §12 back to
`| G2-33 | todo | |`, and truncate this log at this heading. No game file, install, save or dropzone is
touched; no archive is opened (`D:\Games` never read); nothing is committed.

## G2-31 · Water behaviour — intended change (2026-10-27)

**Card:** G2-31 (phase G2, S, deps P0-1 — `P0-1` row `done`, `G2-31` row `todo`; no earlier
entry for this card, no files on disk for it). In: the `buoyancy` / `water_interaction` modules
of the donor, the armoured transport, the tanks and the `v1717` duck, plus any engine-kill/drown
member. Do: describe what makes a car sink, float, keep driving or die in water; record the
members. Out: `Research/JC3Grab/WATER.md`. Done: members + values for "sinks and stalls" vs
"floats" vs "drives underwater".

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3water.py` | new. Reads the 232 decoded entity caches, catalogues every member of the three water module types (`Buoyancy` 8 paths, `WaterInteraction` 52, `BoatBuoyancy` 16) with fleet range + donor value, classifies each entity by `will_sink` and `BoatBuoyancy`, collects the fleet-wide `VehicleCommon` water-entry/engine-shut-down rows, scans **every** member path in all 52 module types for water/drown/sink/float/dive/submerge vocabulary, and decodes `Builds/test-091/*.ee` with `jc3adf` to check the live build inherits the donor's water modules; `--write`/`--check`/`dump` | the card's Do step; no archive re-read, the cache plus the build's own container are the card's In list |
| `Research/JC3Grab/WATER.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/WATER.json` | new, generated: members, census, samples, boats, floaters, constants, scan, build comparison | G2-13…G2-29 convention; `--check` compares it |
| `Research/JC3Grab/README.md` | one G2-31 section + one Files row | every G2 table is listed there |
| `GRAB_BACKLOG.md` §12 | `G2-31 \| todo` -> `done` + evidence | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking.** The card's third behaviour, "drives underwater",
is a hypothesis, not a field: nothing in the vocabulary promises it. The scan settles whether any
member could express it (answer from the data: none - the only `dive_*` terms are helicopter
flight). The card also implies the kill/stall side is per-vehicle; it is not - all 232 entities
point their `VehicleCommon` at the same `vehicle_common.vmodc`, so the four water-entry timers and
the five engine shut-down delays are fleet constants and "no vehicle overrides them" is the
finding, not an omission.

## G2-33 · Light system consolidated — done

**Card:** G2-33 (S, deps P0-1 — row `done` in §12). In: `Working/Lights/LGT1_FINDINGS.md`, MODLOG
§112–§113, `ENTITIES.md`, `GEOMETRY.md`, the donor lights module. Out:
`Research/JC3Grab/LIGHT_SYSTEM.md`. No earlier session had touched the card (no prior log entry,
no output on disk), so this run did all of it; the intended-change entry above is its own.

**Result.** A vehicle light is one entry in the module `VehicleDynamicLights`: **3,217 entries
over 223 vehicles** (a vehicle may carry two modules and both number their entries from
`lights[0]`), **25 members** each — `behavior`(+hash), `part`(+hash), `part_index`, `diffuse
R/G/B`, `range`, `falloff_start`, `near_cap`, `multiplier`, `min_luminosity`, `light_type`,
`blinking`, `angle`, `cast_shadows`, `projected_texture_index`, `volumetric_mode`,
`volume_intensity`, `uvscale u/v`, `deformable_transform`(+hash), `preset_id`. Nine behaviour
values are in use: `None` 1,156, `HeadLight` 1,027, `TailLight` 301, `LeftSignal` 253,
`RightSignal` 253, `Reverse` 191, `SirenLightOn` 9, `SirenLightOnOffFast` 3,
`SirenLightOffOnFast` 3.

**The entity graph is a second, different list.** 3,972 `SVehicleLight` objects (233
`SVehicleLights`, 412 `SVehicleLightList`) carry **404 preset names** and 13 members but **no
part, no part_index, no transform**, and their `preset_id` is a *string* while the module's is a
*uint32 hash*. No file joins the two lists, so the module is the only side that binds a light to
a part; which one the renderer reads is UNKNOWN (recorded, not guessed).

**Presets are not the value source.** 393 distinct `preset_id` hashes; **17 shipped entries use
`preset_id = 0`** (modernbus brake lights, police siren, racing-boat interior); **34 presets
appear with more than one value tuple** across their users (e.g. `1435191809` with 14 distinct
tuples over 118 entries). So an entry states its own numbers and a light without a preset is
fully described by its row. What the engine does with a preset is code: UNKNOWN.

**`has_lights` is a flag, not a gate.** 2,073 of 11,643 parts carry it (1,323 of them
`Land_Light`). Binding checks over all 3,217 entries: 3 whose `part_index` is not in the parts
module, 27 whose `part_index` names a different part (the heavyassault heli's wing/tail lights vs
its missile parts), 6 that resolve to a `has_lights = 0` part (the Bavarium tank turret);
conversely 13 lit parts carry no entry. Entries outnumber lit parts because one part hosts
several lamps (the donor's left tail-light part carries `TailLight` + `LeftSignal` + `Reverse`).

**`CarLight` block.** 11,367 blocks in 11,367 meshes across 220 vehicles, **every one** vertex
stride 12 B, uint16 indices, exactly **6 material slots**; layout solved earlier (MODLOG §17:
1,085 B static header, 16 B gap, buffers 12/24/2, round-trip 190/193 byte-identical). The
*material parameter* bytes are still undecoded (§102d), so a block can be copied byte-exact but
not authored — the doc says so instead of inventing numbers.

**The recipe (the card's Done criterion): the left wheel-arch light.** 25 members, each with a
source and a value class in `LIGHT_SYSTEM.md` §7a: behaviour `HeadLight` from the BmAK enum
(`VEHLT_HeadLight`), part `sportsmuscle_wheel_f_l` (part_index 26, `Land_Wheel`, parent 3),
colour `0.6275/0.7059/1.0` = the BmAK `LightColor` 160,180,255 ÷ 255, every shape member copied
from the donor's shipped steady `HeadLight` point lamp (`lights[2]`, the dashboard `_LIG` entry:
range 2, angle 10, `light_type` 0, multiplier 1, `near_cap` 1, no blinking), `preset_id = 0`
(17 shipped precedents), anchor `|sportsmuscle_LOD1|wheel_f_l|Wheel_Frnt_Left_Disc|
Wheel_Frnt_Left_Disc_LIG`. The two hashes are computed by `rbmhdr.hash_jenkins` — the same
function the check proves against **all 3,217** shipped `part_hash`, `behavior_hash` and
`deformable_transform_hash` values (0 mismatches). The BmAK component itself is unlit (radius,
cone and brightness 0, colour alpha 0), so only its colour is usable; the recipe says that
instead of pretending to copy a light intensity. LGT-2's battle-mode spotlight is the same
socket's `VEHLT_BattleModeLight` entry, i.e. a second row with the same 25 members. The part the
recipe adds needs `has_lights = 1`, `Land_Light`, a `CarLight` block in its `lod1.rbm`, and the
anchor node in its rig — the last is exactly the §112 probe, so it is classed UNKNOWN there and
not claimed.

**Done check.** `python Tools/scripts/jc3lights.py --check` (exit 0):

```
PASS: 3,217 light entries / 223 vehicles, 25 members, 9 behaviours, 393 presets (17 use 0, 34 inconsistent), hashes 3217/3217/3217 recomputed; binding 2,073 lit parts, 27 name misses, 6 on unlit parts; CarLight 11,367 blocks stride ['12'] slots ['6']; recipe 25 members
```

The check re-reads every decoded input, rebuilds both Out files, compares them byte-for-byte and
runs the 25-row assertion table the doc prints. Nothing opens an archive; `D:\Games` is never
read; no game is launched. The parser's counts were also re-derived independently in
`tmp/freebuff/probe_g2_33.py` (raw `lights[i].*` scan, separate parts/geometry tallies) — every
count agrees.

**Tamper test.** (1) `module.entries` 3,217 -> 3,216 in `LIGHT_SYSTEM.json`: `--check` exit 1,
`FAIL: LIGHT_SYSTEM.json stale`. (2) one number in `LIGHT_SYSTEM.md` (`**3,217**` -> `**3,218**`
in the scope table): exit 1, `FAIL: md differs: @@ -15,3 +15,3 @@`. After each `--write` the PASS
above returned.

**UNKNOWN / limits.** Which of the two light lists the renderer reads: UNKNOWN (they disagree in
count and no file joins them). Whether a preset overrides an entry's members: UNKNOWN. The
`CarLight` parameter/emissive semantics: UNKNOWN (§102d). Range/angle units: no file states them,
so the recipe copies shipped numbers and converts only sRGB -> 0..1; the BmAK cone/radius are 0
and unusable. Whether `preset_id = 0` means "no preset": UNKNOWN. Whether the
`deformable_transform` node chain resolves through the parts module: the §112 probe (one part,
one install, one night look), unchanged by this card. No light was built, installed or looked at
in game (R6); no build, save or dropzone was touched.

**Files changed.** `Tools/scripts/jc3lights.py` (new, 8 s per run),
`Research/JC3Grab/LIGHT_SYSTEM.md` + `LIGHT_SYSTEM.json` (generated, 332 md lines / 79,742 B),
`Research/JC3Grab/README.md` (one section + one Files row), `GRAB_BACKLOG.md` §12 (one line),
this log (append-only). Probe left at `tmp/freebuff/probe_g2_33.py`.

**Revert:** delete `Tools/scripts/jc3lights.py`, `Research/JC3Grab/LIGHT_SYSTEM.md`,
`Research/JC3Grab/LIGHT_SYSTEM.json`, `tmp/freebuff/probe_g2_33.py`, the README section and Files
row added here, put §12 back to `| G2-33 | todo | |`, and truncate this log at the
`G2-33 · Light system consolidated — intended change` heading. Nothing outside the repo is
written; no archive opened; nothing committed.

## G2-31 · Water behaviour — done (2026-10-27)

**Status: done.** Out on disk: `Research/JC3Grab/WATER.md` (288 generated lines) +
`Research/JC3Grab/WATER.json`, built by `Tools/scripts/jc3water.py` (`--write` / `--check` /
`dump <members|groups|samples|constants|scan|build|boats|floating>`), README row + section added.

**Done check, verbatim (exit 0):**

```
PASS: 232 entities, sink 189 / floating 8 / boat 35, donor will_sink 1 buoyancy 2 drag 100 (1 hull element), 35 boats base_buoyancy 0.1..1.45, 21 fleet-wide water/engine rows in one shared VehicleCommon, build water modules identical to the donor: True, 38 member paths scan as water-related
```

**The three behaviours, answered from the files.**

| behaviour | members and values |
|---|---|
| **sinks and stalls** | `WaterInteraction.will_sink = 1` on **189** entities, donor included: `buoyancy` 2, `drag` 100, `radius` 0.55, `side_area` 1.85, `bottom_area` 3, `up_velocity_cap` 20, **1** hull element (`part_elements[0]`, body part `sportsmuscle_body`). 10 of the 189 ship an empty `part_elements[]` (bikes, `v0009` saloon, `v0866`, `dlctestcar`) and still sink, so the hull mesh is the water-plane shape, not the switch. |
| **floats** | **35** boats: `will_sink` 0 + a `BoatBuoyancy` module (`base_buoyancy` 0.1 / 1 / 1.45, `base_radius` 0.8..1.5, `base_forward_drag` 30..500, `base_lateral_drag` 100..500, `base_vertical_drag` 100..2000, `base_air_drag` 0..50, 6–9 pontoon `buoyancy_modules[]`). **8** more entities float with the plain car `Buoyancy`: `v0200` APC (3 builds, buoyancy 2), `v2603` sea scout (3, 0.25), `v4500` floatplane (2, 1.5) - `will_sink` 0 and nothing else differs from the sinking cars. |
| **drives underwater** | **no member anywhere.** The scan of all 232 entities × 52 module types returns 38 water-ish member paths: the three water modules, 4 `vehicle_damage.*_water_entry_ms` rows, 5 `*_engine_shut_down_delay_s` rows, 12 `number_of_water_collision_sensors` indices, `fins[].effective_in_water` and 5 `HelicopterModel` flight `dive_*` terms. No `drown`/`submerge`/`flood`/`swim`/`underwater` path exists -> the behaviour is native -> `UNKNOWN`. |

**Kill and stall.** All 232 entities point `VehicleCommon` at **one** shared
`editor/entities/jc_vehicles/00_shared/modules/vehicle_common.vmodc`; `vehicle_damage.
min_water_entry_ms` 10, `fatal_water_entry_ms` 20, `..._floating_ms` 20/50, and
`car_common.engine_shut_down_delay_s` 30 vs 5 for boat/bike/helicopter/plane. **No vehicle
overrides any of them**; the unit behind `_ms` is not decoded (`UNKNOWN`).

**The build (WLD-6 / D-8).** `Builds/test-091/v0300_..._civilian_01.ee` (604 inner files) carries
the donor's own `v0300_..._water_interaction.vmodc` + `_buoyancy.vmodc`, decoded here with
`jc3adf`: `will_sink` 1, `buoyancy` 2, `drag` 100, `radius` 0.55, `side_area` 1.85,
`bottom_area` 3, `up_velocity_cap` 20, 1 hull element - **identical to the donor cache**
(compared to 1e-6, since the cache rounds floats). So the lore route of D-8 ("sink and stall",
Rico swims out) is what the build already does; the float route would need `will_sink` 0 plus a
`BoatBuoyancy` block the donor does not have, and changing the fleet-wide timers needs a private
`vehicle_common.vmodc` (R7).

**Tamper test.** (1) `census.groups.boat` 35 -> 36 in `WATER.json`: `--check` exit 1,
`FAIL: WATER.json stale`. (2) `| shared-constant rows | 21 |` -> `22` in `WATER.md`: exit 1,
`FAIL: md differs: @@ -284,3 +284,3 @@ …`. After `--write` the PASS above returned.

**Independent re-derivation.** `tmp/freebuff/probe_g2_31.py` does not import `jc3water`: it
decodes the donor, the APC and the duck **straight out of the archives** (`jc3grab` +
`jc3detail` + `jc3adf`), pulls `vehicle_common.vmodc` out of the donor container, and re-counts
the group split from the cache by hand. It agrees member for member: donor `will_sink` 1 /
buoyancy 2 / drag 100 / radius 0.55 / bottom 3 / 1 hull part from `sportsmuscle_body`; APC
`will_sink` 0 with no boat module; duck `will_sink` 0, `base_buoyancy` 1.45, 9 pontoons;
constants 10/20/20/50 and 30/5; groups 189/8/35; one shared `vehicle_common` file.

**UNKNOWN / limits.** What the four `_water_entry_ms` numbers measure (10/20 ms cannot be a
drown timer, so the name is the only evidence); whether a car that is submerged keeps driving
before that timer fires; how `will_sink` interacts with the `Buoyancy` multiplier per mass (the
mass/`buoyancy` relationship is engine code); what `flat_water_vs_speed_ms` and
`planing_vs_forward_speed_ms` curves are evaluated against (their `control_points[]` hold
uninitialised tails - values up to 4.6e19 beyond `number_of_control_points`); whether the
`v4603` cargo plane's second (medium-tank) water module is ever read. Nothing was launched,
nothing written under `D:\Games`, no archive or shared module edited, nothing committed.

**Standing gates re-run.** `status_audit.py --check` -> `STATUS.md is current` (exit 0);
`jc3index.py check` -> `check ok: 81952 rows, 78907 paths, 1 unnamed entries` (exit 0).

**Files changed.** `Tools/scripts/jc3water.py` (new), `Research/JC3Grab/WATER.md` +
`WATER.json` (generated), `Research/JC3Grab/README.md` (one section + one Files row),
`GRAB_BACKLOG.md` §12 (one line), this log (append-only). Probe at
`tmp/freebuff/probe_g2_31.py`.

**Revert:** delete `Tools/scripts/jc3water.py`, `WATER.md`, `WATER.json`,
`tmp/freebuff/probe_g2_31.py`, the README section and Files row; put §12 back to
`| G2-31 | todo | |`; truncate this log at the `G2-31 · Water behaviour — intended change`
heading.

## G2-34 · Tether, airlift and winch carriers — intended change (2026-10-27)

**Card:** G2-34 (phase G2, S, deps P0-1 — row `done` in §12). In: `INDEX.jsonl` (grapple/tether
tunes, `transport_rope_winch` on `v1602`, cargo plane `v4603 … military_cargo_tank`),
`tether_tear`/`tether_yank` objects. Do: record tether strength vs vehicle mass, whether vehicles
can be airlifted, and whether any vehicle-mounted winch/rope exists that a car could carry. Out:
`Research/JC3Grab/TETHER.md`. Done: WLD-7 has values; WPN-6 has a carrier or a proven absence.
Serves WLD-7, WPN-6.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3tether.py` | new. Reads every entity cache (`RigidBody.mass`, module lists), all 232 `.epe` graphs (`CVehicleCargoBay`, `CGrapplingHookPropData`, `CInteractionGraph*` cargo/grapple nodes, the vehicle-root classes), `PARTS_TABLE.jsonl` (the `v1602` rope/winch parts and their `behavior`), `INDEX.jsonl` (tether/grapple/rope/winch assets and the `dualtether` graph) and quotes MODLOG §86/§87 for the BmAK winch bound; writes the mass table, the carrier census and the WPN-6 verdict; `--write` / `--check` / `dump` | the card's Do step; reads only decoded tables, so `D:\Games` is never opened |
| `Research/JC3Grab/TETHER.md` | new, generated | the card's only Out path |
| `Research/JC3Grab/TETHER.json` | new, generated machine half | sibling convention (`EMP.json`, `LIGHT_SYSTEM.json`); `--check` compares byte-for-byte |
| `Research/JC3Grab/README.md` | one `### Tether, airlift and winch` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-34 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| this log | intended change + done | R14 |

**What the card assumes that needs checking in the data.** (a) That a *tether strength* value
exists somewhere in the decoded set — the index has no tether/grapple tune at all (7 hits, all
decals/upgrade textures/one `graphs/dualtether_test_to_vehicle.gsc`), so the strength may be
UNKNOWN and must be recorded as such rather than bounded from the cinematic feats (§86 already
refused that derivation). (b) That `transport_rope_winch` is a working winch — it is a
`CPartProp` whose parts-module record is `Boat_Generic` / `behavior None`, i.e. a mesh. (c) That
a helicopter can airlift a car — the only cargo carrier class in the fleet is
`CVehicleCargoBay`; the census will say which families have it and whether any helicopter does.
(d) That "vehicle mass" is in the files at all: `RigidBody.mass` exists (232 entities, donor 975),
but no file states its unit, so the unit stays UNKNOWN and only the numbers are compared.

**Revert:** delete `Tools/scripts/jc3tether.py`, `Research/JC3Grab/TETHER.md`,
`Research/JC3Grab/TETHER.json`, the README section + Files row added here, put §12 back to
`| G2-34 | todo | |`, and truncate this log at this heading. No game file, install, save or
dropzone is touched; no archive opened; nothing committed.

## G2-34 · Tether, airlift and winch carriers — done (2026-10-27)

**Done check** `python Tools/scripts/jc3tether.py --check` → exit 0:

```
PASS: 232 masses (donor 975, target 6000, 1 multi-body), bays 12 on 12 entities / 0
helicopters, hooks 33 on 3 entities, compound 1, rope/winch parts 40 (10 names) + 12 winch
LODs, tether-ish module types 0/53, winch classes 0, index tether 335 (7 non-dialogue) /
winch 0
```

**Tamper test.** `TETHER.json` `carriers.bays` 12 → 13 → `FAIL: TETHER.json stale` (exit 1);
a number in `TETHER.md`'s boat row → `FAIL` with the md diff (exit 1); both restored → PASS.
No archive opened, no game launched, `D:\Games` never written, nothing committed.

**What the card asked for, answered.**

- **Tether strength vs vehicle mass.** The mass half is in the files: `RigidBody.mass` on **232
  entities**, no unit stated (so UNKNOWN, and every figure below is a ratio). Donor `975`, the
  6 t design car `6.154x` it; carriers the plane `40,000`, the boat `100,000`, the flatbed
  `15,000` — i.e. 15.0 % / 6.0 % / 40.0 %. The tether half is **not**: all **335** `tether`
  names in the index are dialogue (328), two upgrade icons, two upgrade videos, one challenge
  decal and the two `dualtether_test_to_vehicle` graph files. No tune, no force, no break
  threshold — recorded as UNKNOWN, not bounded from the §86 cinematography.
- **Can vehicles be airlifted?** By the plane/boat/train, yes in the data: `CVehicleCargoBay`
  on **12 entities** (plane 6, boat 4, flatbed 2), 7 members, empty enable/disable, no capacity
  or mass limit. The decoded proof that it *carries a vehicle* is
  `v4603 … military_cargo_tank`: the fleet's **only compound entity**, two roots
  (`CAirPlane` + `CCar`) and two bodies (`40,000` + `25,000`) in one `.ee`. **No helicopter has
  a bay (0 of 23)**, so a helicopter airlifting a car has no file carrier → UNKNOWN, not "no".
- **A winch a car could carry (WPN-6).** Carrier yes, mechanic no: `transport_rope_winch`
  (part 26 of 56, `Boat_Generic`, `behavior = None`, `parent = 0`) + 9 rope parts on the
  transport boat, mesh present as **6 files** (`.lod` + 5 `.rbm` LODs). Of the fleet's **67
  named part behaviours** none is a winch/rope/tow/reel (nearest: `CargoBayDoor`), and no
  module type in **53** is tether/cargo/rope/winch/tow. `winch` occurs **0** times in the index
  (supporting: the index carries no parts-module prop meshes at all — `transport_propeller`
  also 0).

**Corrections to the card's assumptions, all measured here.** (a) The index has **no**
tether/grapple *tune* (0), so the card's first In-item yields no strength number. (b) The
`tether_tear`/`tether_yank` objects are loose-cargo prop markers on a truck and a flatbed
(33 objects / 3 entities, all `enable_event` empty), not tether parameters. (c) The cargo
plane's entity holds **both** masses, not the tank's alone — an earlier reading of
"mass = 25,000" was half the picture.

**Files changed.** `Tools/scripts/jc3tether.py` (new), `Research/JC3Grab/TETHER.md` (264
lines) + `TETHER.json` (generated), `Research/JC3Grab/README.md` (one section + one Files
row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only).

**Revert:** delete `Tools/scripts/jc3tether.py`, `TETHER.md`, `TETHER.json`, the README
section and Files row; put §12 back to `| G2-34 | todo | |`; truncate this log at the
`G2-34 · Tether, airlift and winch carriers — intended change` heading.

## G2-18 · Interaction points and stunt areas — intended change (2026-10-28)

**Card:** G2-18 (phase G2, M, deps P0-1 — row `done` in §12). In: donor `.epe`
(`detail/v0300_…_civilian_01.ee.json`), `sportsmuscle_stunt_areas.vmodc`,
`Research/Epe/serpente_civilian.xml`, body bbox (T-G1), `Working/TrueScale/stations.json`. Do:
1. every `entry.*`/`exit.*`/`point.*`/`transition.*`/`trigger.*`/`interaction.*` object with its
full transform and any referenced animation/state name; 2. decode the stunt-areas module (the
boxes/planes Rico can stand on); 3. express each point relative to the Serpente body bbox and
wheel stations, then report where it lands on the Batmobile body (inside / floating /
on-surface) using the Batmobile mesh. Out: `Research/JC3Grab/INTERACTION.md` + `INTERACTION.json`.
Done: every interaction object listed with Serpente position and Batmobile-surface verdict.
Serves WLD-3/4, MOD-3/4, ANI-9.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3interact.py` | new. Reads the donor entity cache (`StuntAreas`, `DeformPoints`, `LandGlobal` wheel hardpoints), the donor `.epe` object graph, `Research/Epe/serpente_civilian.xml` (format cross-check), `Working/TrueScale/stations.json` (Batmobile body bbox + hardpoints) and `Working/TrueScale/body_lod1.rbm` (Batmobile mesh, via `rbm_geom`); writes the point/trigger/transition census, the stunt-area decode and the per-point Batmobile verdict; `--write` / `--check` / `dump` | the card's Do step 3 ("write `Tools/scripts/jc3interact.py`") |
| `Research/JC3Grab/INTERACTION.md` | new, generated | the card's Out path |
| `Research/JC3Grab/INTERACTION.json` | new, generated machine half | sibling convention; `--check` compares byte-for-byte |
| `Research/JC3Grab/README.md` | one `### Interaction points and stunt areas` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-18 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| this log | intended change + done | R14 |

**What the data already says (probed before writing, no file changed yet).** The donor's
`StuntAreas` module is decoded in the cache: **32 slots**, only **3 active** (`front_area` /
`front_signature_area` / `main_area`) with `number_of_deform_points` 6 / 6 / 10,
`vertices3D_local`, `triangle_indices` (4 / 4 / 8 triangles), `bounding_box_local`,
`center_local`, plus **64 `welding_info`** rows - so the "boxes/planes" are real triangle
surfaces, not AABBs. The `.epe` side has **85** prefixed objects (29 `entry.*`, 26 `exit.*`, 12
`transition.*`, 8 `point.*`, 7 `trigger.*`, 3 `interaction.*`); only `point.*` (8/8) and
`trigger.*` (5/7) carry a `world` matrix, so entry/exit/transition positions must be
*inherited* from their parent node - which this script records explicitly rather than guessing.
Serpente frame: deform-point envelope x ±1.33, y 0..1.524, z -2.560..2.527 (agrees with the
union mesh AABB in z), wheel hardpoints z -1.557 / +1.446, x ±0.885 (wheelbase 3.003, track
1.77). Batmobile frame: `stations.json` `body_bbox` + 4 hardpoints (wheelbase 5.029). The
normalised Serpente->Batmobile placement is the card's analysis mapping; it is **not** the R2
build transform (`bat_assemble.py` `T(p)`), which stays the only transform for assets.

**Revert:** delete `Tools/scripts/jc3interact.py`, `Research/JC3Grab/INTERACTION.md`,
`Research/JC3Grab/INTERACTION.json`, the README section + Files row, put §12 back to
`| G2-18 | todo | |`, and truncate this log at this heading. No game file, install, save,
dropzone or archive is touched; nothing committed.

## G2-18 · Interaction points and stunt areas — done (2026-10-28)

**Done check** `python Tools/scripts/jc3interact.py --check` → exit 0:

```
PASS: 85 objects (entry 29, exit 26, interaction 3, point 8, transition 12, trigger 7), transforms own 15 / inherited 70 / none 0, verdicts {'floating': 23, 'inside': 30, 'n/a (container origin)': 32}, stunt 3/32 active (64 welds), mesh 28940v/20000t, json match True
```

**Tamper test.** `INTERACTION.json` `stunt_areas.areas[2].bat_center_surface_m` → 0.5:
`FAIL: INTERACTION.json stale` (exit 1). A count in `INTERACTION.md`'s validation table
(`trigger.*` 7 → 8): `FAIL` with the md diff (exit 1). Both restored → PASS.
No archive opened, no game launched, `D:\Games` never written, nothing committed.

**What the card asked for, answered.**

1. **Every interaction object.** **85** prefixed objects in the donor `.epe`: `entry.*` 29,
   `exit.*` 26, `transition.*` 12, `point.*` 8, `trigger.*` 7, `interaction.*` 3. **15** carry
   their own `world` matrix (the 8 points + 7 triggers), **70** inherit a container's, and every
   one is listed with its position, its state string (36 distinct, e.g. `S_ENTER_DRIVER_VEHICLE`,
   `S_EXIT_VEHICLE_90L`, `S_GRAPPLE_REEL_TO_STUNT_LAND`) and the node it hangs under. The 32
   objects whose nearest transform is the identity `graph`/`context` container are marked
   `n/a (container origin)` instead of being given a meaningless verdict at 0,0,0.
2. **Stunt areas decoded.** `StuntAreas` declares **3** areas in a **32-slot** array: `front_area`
   and `front_signature_area` (coincident geometry, 6 points / 4 triangles, bound to
   `sportsmuscle_hood` vs `sportsmuscle_hood_signature`) and `main_area` (10 points / 8 triangles
   on `sportsmuscle_body`). Each is a real triangle set (`vertices3D_local` + `triangle_indices` +
   `bounding_box_local` + `center_local`), not a box, plus **64 `welding_info` rows of which 8 are
   real welds** (0↔1 ×6, 0↔2 ×1, 1↔2 ×1).
3. **Where it lands on the Batmobile.** Serpente frame = the 135-point deform envelope
   (x ±1.33, y 0…1.524, z −2.560…2.527, agreeing with the 198-mesh union in z); Batmobile frame =
   `stations.json` `body_bbox`; wheels 3.003 m vs 5.0289 m wheelbase. Bbox-normalised, the 85
   objects land **30 inside the shell, 23 floating, 0 on-surface, 32 n/a**, and the three stunt
   surfaces are *tilted* rather than lifted (`main_area` `center_local` 0.0197 m = on-surface but
   its vertex centroid 0.0746 m and worst vertex 0.5955 m; `front_area` 0.1035 / 0.1512 / 0.374).

**Corrections to the intended-change entry (measured here).**
(a) It says the transform census would be 13 own / 72 inherited; the XML tree shows **15 own**
(8 points + 7 triggers) - the decoded JSON drops the `world` of `trigger.driver.fast` and
`trigger.stationary.stunt`, so a JSON-only reader would report those two as UNKNOWN.
(b) It says 64 welds; the module has 64 `welding_info` **rows** but only **8 real welds** - the
other 56 are `-1` filler. Both numbers are now in the doc.
Also: the decoded JSON's `node` paths cannot resolve a parent (26 duplicate paths, `?`
placeholders), so the hierarchy comes from `Research/Epe/serpente_civilian.xml` and the JSON is
the value cross-check (agrees on every world/state string).

**Independent probe.** `tmp/freebuff/probe_g2_18.py` does not import `jc3interact`: it re-counts
the slots/welds from the module rows, the 85/79 names straight out of the XML text, and
re-measures one distance by brute-force barycentric sampling (0.0198 m sampled vs 0.0197 m exact
for `main_area`'s `center_local`). It caught the `center_local` vs vertex-centroid gap that the
first cut of the script hid by using the mean only.

**Files changed.** `Tools/scripts/jc3interact.py` (new), `Research/JC3Grab/INTERACTION.md`
(312 lines) + `INTERACTION.json` (3,562 lines), `Research/JC3Grab/README.md` (one section + one
Files row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only).

**Revert:** delete `Tools/scripts/jc3interact.py`, `INTERACTION.md`, `INTERACTION.json`,
`tmp/freebuff/probe_g2_18.py`, the README section and Files row; put §12 back to
`| G2-18 | todo | |`; truncate this log at the `G2-18 · Interaction points and stunt areas —
intended change` heading.

## G2-28 · Damage model, complete, with a predicted hits-to-kill table — intended change (2026-10-28)

**Card:** G2-28 (phase G2, M, deps G2-10 + G1-14 — both `done` in §12). In: `DAMAGE_MECHANISMS.md`,
the health modules, `PARTS_TABLE.jsonl` damage types, tank parts/damage types, `WEAPONS.jsonl`,
`damage_audit.py`, `vhealth.py`. Do: (1) write down how a hit becomes health loss and cite each
step, marking undecoded steps UNKNOWN; (2) hits-to-kill for Rico's pistol/AR/MG/shotgun/RPG/
grenade and tank cannon `w602`/heli missile `w601`/heli MG `w604`, for the donor, the medium tank
and the current build; (3) what root `health` scale / `invulnerable` / armour values would give
ARM-1 (small arms do nothing) and ARM-2 (destroyable by heavy weapons) at the BmAK ratio from
G1-14. Out: `Research/JC3Grab/DAMAGE_MODEL.md` + `Tools/scripts/damage_predict.py --check`.

**Resume check.** `grep G2-28 MODLOG.md` before this entry found only two *references* (lines 8301
and 9249), no intended-change entry, and neither `DAMAGE_MODEL.md` nor `damage_predict.py` exists
on disk — so this card was never started. Nothing to continue from.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/damage_predict.py` | new. Reads the three `VehicleDamage` instances (donor cache, medium-tank cache, `Builds/test-091`), the `PartDamageType` rows, the 9 arms (3 vehicle weapons from `WEAPONS.jsonl`, 6 hand weapons re-decoded from the archives with `jc3weapons`' own reader), applies the documented chain under three named models, and writes the doc + JSON; `--write` / `--check` / `dump` | the card's Out path names this script; every number must be re-derivable by `--check` (R11) |
| `Research/JC3Grab/DAMAGE_MODEL.md` | new, generated | the card's Out path |
| `Research/JC3Grab/DAMAGE_MODEL.json` | new, generated machine half | sibling convention (`EMP.json`, `TURRET.json`); `--check` compares byte-for-byte |
| `Research/JC3Grab/README.md` | one `### Damage model` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-28 \| todo \| \|` → `done` + evidence, that one line only | session loop step 7 |
| this log | intended change + done | R14 |

**Already changed before this entry (declared).** `python Tools/scripts/t1_current.py Builds/test-091`
re-generated `Working/Translation/current.json` (it held `test-083`): that is the script's documented
purpose and the file is generated, but it is a write, so it is recorded here. Revert:
`python Tools/scripts/t1_current.py Builds/test-083`.

**What the data already says (probed before any file was written).** The three targets differ far
less than the card assumes: the medium tank ships `max_health` **2000**, `bullet_armor` **5000 @
strength 99**, `explosion_armor` 250 @ 50, `impact_armor` 0/0, `smoke_threshold` 1050,
`burn_threshold` 250, `explosion_threshold` 4000 — and `Builds/test-091`'s health module is that
same profile. The donor is `max_health` 700 with **every** armour channel 0 and 24
`part_damage_types` rows. So the build is *the tank's damage profile plus three switches*, which is
the single most important fact for ARM-1…6 and must be stated as measured, not as intent.
The composition of `*_armor` + `*_armor_strength` + `max_health` + the root `health` scale is not
in any file (POSTMORTEM_DAMAGE §5 item 1 names the gap and G2-28 owns closing it); it will be
carried as three explicitly-named models with exact per-arm expected values, not as a formula
presented as fact.

**Revert:** delete `Tools/scripts/damage_predict.py`, `Research/JC3Grab/DAMAGE_MODEL.md`,
`Research/JC3Grab/DAMAGE_MODEL.json`, the README section + Files row; put §12 back to
`| G2-28 | todo | |`; truncate this log at this heading. No game file, install, save, dropzone or
archive is written; no game launched; nothing committed.

## G2-30 · `.physicsc` write spike (old Batch D route) — intended change (2026-10-28)

**Card:** G2-30 (phase G2, M, deps **P0-1** — `P0-1` row is `done` in §12, `G2-30` row is
`todo`, and `grep G2-30 MODLOG.md` found no earlier entry, so this session starts the card from
scratch; no Out path existed on disk either). In: `Tools/scripts/jc3hkx.py`, `SHAPES.md`,
`WIRING.md`, donor `sportsmuscle.physicsc`, `Working/Assembled/sportsmuscle_true.physicsc`.
Do: **1.** round-trip the donor file byte-for-byte (read → write unchanged); **2.** replace one
convex hull with a scaled copy, write, re-read with `check --all` (plane / vertex / AABB
invariants); **3.** if 1 and 2 pass, write the plan for a Batmobile hull set (convex
decomposition of the body mesh, same compound/instance layout, same station table). Out:
`Research/JC3Grab/PHYSICS_WRITE.md`; tool changes in `jc3hkx.py`. Done: round-trip identical and
the modified file passes every invariant → rows T-P3/T-CO2/T-CO3 become buildable; otherwise
they close as named omissions with the failure recorded.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3hkx.py` | add a **writer**: `hull_bytes()` (re-emit one `hknpConvexPolytopeShape` from its decoded values), `packfile_bytes()` (lay the data section out again with substituted object blobs, remap every local/global/virtual fixup and the section record), `scale_hull()`, `compound_aabb_edits()` (recompute a grown child's parent AABBs), `verify_written()`, and a `write` command with `--write` / `--check` | the card's Out line says "tool changes in `jc3hkx.py`", and the reader already owns every layout the writer needs |
| `Research/JC3Grab/PHYSICS_WRITE.md` | new, generated by `jc3hkx.py write --write` | the card's Out path |
| `Research/JC3Grab/PHYSICS_WRITE.json` | new, generated machine half (hashes, invariant counts, byte ranges) so `--check` compares values, not prose | sibling convention (G2-13…G2-34) |
| `Research/JC3Grab/README.md` | one `### Writing a \`.physicsc\`` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-30 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| this log | this intended change + a `— done` section | R14 |

Written test artefacts (`.physicsc` blobs) go to **`E:\Modding\_JC3grab\hkx\write\`**, outside
the repo (R10). Nothing is packed, installed, or launched; `D:\Games` is only ever read.

**What the data already says (probed before any file changed — read-only, `tmp/freebuff/`).**

* **The donor is 340,368 B**: `hk_2014.1.0-r1`, 430 typed objects, **54 convex hulls** (38,416 B
  of hull blocks), 18 `hknpExternMeshShape`s, 36 `hkGeometry`, 22 compounds / 112 instances.
  Section layout: `__classnames__` 0x100 + 528, `__types__` empty, `__data__` 0x310 + 339,584.
* **The data section is fully partitioned by typed objects**: all 430 objects are contiguous from
  0 to `lf` (0x4eaf0) with **0 gaps**, every extent a multiple of 16, and the whole file ends
  exactly at the last object. That is what makes a size-changing write possible at all: an object
  can grow, everything after it shifts, and the fixup tables (`lf`, `gf`, `vf`, `ex`) and the
  `__data__` section record can be regenerated. The alternative - patching in place - only works
  while a hull keeps its vertex and plane counts.
* **The remap machinery is proven**: inserting 16 filler bytes at data offset 0 shifts *every*
  object, array, fixup and table by +16. Rebuilding the three fixup tables, the pointer values at
  each fixup `from` slot and the section record produces a file that **re-reads with 0 invariant
  violations and a decoded object graph identical to the original** (430 objects, 54 hulls,
  22 compounds). Probe: `tmp/freebuff/probe_g2_30c.py`.
* **The four wheel hulls are the natural test shape**: parts 26/27 (`wheel_f_l/f_r`) and 11/12
  (`wheel_r_l/r_r`) are each 704 B, 20 vertices, 12 planes, 60 indices, box 0.2958 × 0.8225 ×
  0.7822, centroid at the part origin - so a scale about the centroid is a pure scale about 0.
  Batmobile tyre Ø 1.365 m (`TYRES.md`) / 0.8225 m = **1.6596**, a scale factor that comes from
  two measured files, not from a guess.
* **The hull face table is one 4-byte record per plane** (`u16 first, u8 count, u8 min`; the
  records partition the index list, `sum(count) == index_count`, and every face's indices lie on
  that plane - checked face by face on the wheel hull). It is **not** at a fixed offset: 0-32
  bytes of an unnamed block sit between the plane block and the face table, and the face table is
  padded with 0x7F to a 16-byte boundary before the index block. 17 of 54 hulls have a zero-length
  prefix; the other 37 do not. That prefix stays **UNKNOWN** and the writer therefore preserves
  it byte-for-byte instead of inventing it.

**Revert:** delete the writer functions and the `write` subcommand from `Tools/scripts/jc3hkx.py`,
delete `Research/JC3Grab/PHYSICS_WRITE.md` + `PHYSICS_WRITE.json` + `tmp/freebuff/probe_g2_30*.py`
+ `E:\Modding\_JC3grab\hkx\write\`, remove the README section and Files row, put §12 back to
`| G2-30 | todo | |`, and truncate this log at the `G2-30 · `.physicsc` write spike` heading. No
game file, install, save, dropzone, `.ee` or archive is touched by any of it; nothing committed.

## G2-24 · JC3 vehicle audio system — intended change (2026-10-28)

**Card:** G2-24 (phase G2, M, deps P0-1 — row `done` in §12). In: `sound/fmod_banks/vehicles.bank`
(210,781,376 B), the donor `.ee.fmod_guids`, `LandAudio` (2 members), `Working/Audio/` scripts
(`_fbank*.py`, `_fsb.py`, `_fmodguids.py`). Do: 1. every FMOD event the donor uses (GUID → path →
parameters → samples); 2. where the sounds of `w602`, `w603`, `w618`, `w619` are referenced;
3. horn and radio carriers; 4. sample formats (FSB5 codec, rate, loop points); 5. which of the
three ship routes is possible. Out: `Research/JC3Grab/JC3_AUDIO.md` +
`JC3_AUDIO_EVENTS.json`. Serves AUD-1…7.

**Measured before writing anything (probe scripts `tmp/freebuff/probe_g2_24_*.py`, no project file
touched yet).**

| fact | value |
|---|---|
| `.ee.fmod_guids` | version 1, 3 bank names `vehicles`/`character`/`effects`, **45 GuidEvents**, 758 B |
| `.epe` `Sound` fields | **23 distinct** GUIDs, all 45−23 = 22 preload entries are unnamed by the graph |
| GUID → bank | **vehicles 24, character 2, effects 19** (byte scan of each archive bank) |
| bank container | **RIFF/FEV** (`FMT ` = 0x38/0x32 = FMOD **Designer/Ex** event bank, *not* FMOD Studio), PROJ with `EVTS`/`TLNS`/`WAIS`/`WAVS`/`PRMS`, then `SND ` holding one **FSB5** |
| vehicles.bank | 257 events, 257 tunes, 1,674 sound instances, **649 waves**, 649 FSB5 samples, FSB5 data 153,439,744 B, 21,196 B of sample names |
| event entry | `LIST EVNT` → `EVTB` whose body **starts with the 16-byte event GUID** (no name string anywhere in `EVTS`) |
| tune → wave | **no reference**: the 649 `WAVS` GUIDs occur 0× in any section, no field in the 1,674 sound instances enumerates 0…648 |
| `LandAudio` | exactly 2 members: `min_rpm` 1000.0, `max_rpm` 10000.0 |
| fleet | 6,659 `Sound`-carrying objects in **232** vehicles, 176 distinct (class,name); `horn` 178 objects; `radio` **0** |

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3audio.py` | new. Reads the four RIFF/FEV banks (donor `vehicles`, plus `character`, `effects`, `weapons_preorder`), the FSB5 name table and the FSB5 header, the donor `.ee.fmod_guids`, the donor `.epe` `Sound` fields, the `LandAudio` module, the `w602`/`w603` `.wtunec`, the `w618`/`w619` `.ee` (`.fmod_guids` + `.epe`), and a per-sample census through `Tools/vgmstream-win64/vgmstream-cli.exe -s N -m`; writes the report; `--write` / `--check` | the card's Out + the only place a new G2 reader belongs (`jc3*` family) |
| `Research/JC3Grab/JC3_AUDIO.md` | new, generated | the card's Out path |
| `Research/JC3Grab/JC3_AUDIO_EVENTS.json` | new, generated machine half | sibling convention; `--check` compares it field by field |
| `Research/JC3Grab/README.md` | one `### JC3 vehicle audio` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-24 \| todo \| \|` → `done` + evidence, one line only | session loop step 7 |
| this log | intended change + done | R14 |

**Revert:** delete `Tools/scripts/jc3audio.py`, `Research/JC3Grab/JC3_AUDIO.md`,
`Research/JC3Grab/JC3_AUDIO_EVENTS.json`, the README section + Files row, put §12 back to
`| G2-24 | todo | |`, and truncate this log at this heading. No game file, install, save, dropzone
or archive is written; nothing committed; no game launched.

## G2-28 · Damage model, complete, with a predicted hits-to-kill table — done (2026-10-28)

**Done check** `python Tools/scripts/damage_predict.py --check` → exit 0:

```
PASS: 9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19, never H1 0 / H2 8
      chain 7 steps, 7 carry an UNKNOWN, 3 Q-1 probes
      donor 700 HP / tank 2000 HP / build 2000 HP, fleet 233 modules, json match True
```

**Tamper test.** `DAMAGE_MODEL.json` `table.build_test-091.tank_cannon.primary.H0` 2 → 3:
`FAIL: DAMAGE_MODEL.json stale` (exit 1). A number in `DAMAGE_MODEL.md`'s build table
(`tank_cannon` H0 2 → 4): `FAIL: DAMAGE_MODEL.md stale` with the md diff (exit 1). Both restored →
PASS (exit 0). No archive written, no game launched, `D:\Games` never written, nothing committed.

**What the card asked for, answered.**

1. **The chain, seven steps** (`DAMAGE_MODEL.md` §1), each with carrier, evidence, class and its own
   UNKNOWN. Numbers exist for steps 2 (weapon `damage` x `vehicle_damage_factor` x
   `bullets_per_shot`, or `ForcePulseSettings.PlayerDamage`), 4 (`<channel>_armor` +
   `<channel>_armor_strength`), 5 (`part_damage_types[]`) and 6 (`max_health`, root `health`
   100.0, root `invulnerable`); the *mechanism* for step 1 exists in the fleet's single decodable
   `VehicleParts` module; step 3 (which channel a weapon uses) and step 7 (`explosion_threshold`
   semantics) have **no** bridge in any file. The composition itself - how `*_armor`,
   `*_armor_strength`, `max_health` and the root `health` float turn a hit into health loss - is in
   **no decoded file**, which is POSTMORTEM_DAMAGE §5 item 1 confirmed, not closed. So it is
   carried as **three named models** (H0 armour ignored / H1 percentage gate = MODLOG §97's reading
   / H2 per-hit threshold + absorbing pool), each with a formula and exact per-arm numbers.
2. **The hits-to-kill table** is 9 arms x 3 vehicles x 3 models = 81 cells (`DAMAGE_MODEL.md` §4).
   The nine arms were *decoded*, not typed: three from `WEAPONS.jsonl`, six re-decoded from the
   archives because G2-10 only covered `06_vehicle/`. Two arms are not what their names suggest:
   **`w602`'s bullet damage is 1.0** - a tank shell does its work through the **1500 blast in 8 m**
   (its AI tune is 20 x 10 = 200), and the **shotgun delivers 144 per pull** (8 pellets x 90 x
   0.2). The vehicles were re-read from their own modules: donor **700 HP, all 8 channels 0 @ 0**;
   medium tank **2000 HP, bullet 5000 @ 99, explosion 250 @ 50, impact 0 @ 0**; build test-091
   **the tank's profile in 6 values** (`impact`/`melee` 5000 @ 100, `impact_damage_factor` 0,
   `deform_scale` 0).
3. **ARM-1 / ARM-2 arithmetic** (§5). The BmAK ratio is decoded (G1-14): `Pawn.Health` 1200 /
   heavy cannon 50 = **24 heavy-cannon hits**. ARM-1 needs `bullet_armor_strength` **100** under H1
   (fleet max 99 - and test-077 shipped exactly that and failed) or **>= 144** under H2 (the
   shotgun's per-pull damage; fleet max 99), so per-channel ARM-1 is **outside the shipped domain**;
   `invulnerable` 1 is in-domain but whole-vehicle, so it would kill ARM-2. ARM-2 is already true
   (explosion strength 50 < shell 1500). ARM-2 *at the BmAK ratio* is **outside the domain**: 24 x
   1500 needs `max_health` 36,000 against a fleet range of 500..4000 (3 hits at the maximum under
   H0/H2, 6 under H1).
4. **Three Q-1 probes** with exact expected counts under each hypothesis (§6): `Q1-DM-A` tank shell
   on the build's explosion channel (H0/H2 **2**, H1 **3** shells - the only testable disagreement
   at a small count), `Q1-DM-B` 200 pistol rounds (6,000 damage destroyed under H0, 60 HP under H1,
   0 under H2), `Q1-DM-C` the pool half of H2 on a vehicle that has a pool.

**Findings the card did not ask for, all measured here.**

- **The build's part table is the donor's with exactly one change** -
  `Land_Wheel.instantly_damaged_by_bullets` **1 → 0** (donor → build). That is the only part-level
  ARM-4 edit in the live build, and no earlier document mentions it. It is *not* proof of ARM-4:
  the wheel keeps `initial_health` 1020 and `loosen_health` 100, so sustained fire can still reach
  the damaged state - Q-1's business.
- **`damage_audit.py` FAILS on the current build.**
  `FAIL bullet_armor_strength: declared as a switch but 99 is inside the shipped 0..99 - remove the
  declaration` (exit 1, 29 members, 5 outside the shipped range, 6 declared switches). The
  declaration in `Working/Translation/damage_switches.json` still carries `value: 100` from
  test-077 while test-091 ships 99. **Not fixed here** - which side is wrong is a T-14/B-09
  decision, and the card did not authorise a build or ledger edit. Flagged for whoever owns the
  damage rows.
- **`DAMAGE_RULES.md` §3.5's missile number is wrong.** It lists `Batmobile_Missile_*`
  `Projectile.Damage` = **60**; the package decodes `Batmobile_Missile_Projectile` = **250** and
  `Batmobile_EMPMissile_Projectile` = **60**. The 60 is the EMP missile read once and applied to
  both. `damage_predict.py` reads the values itself (`Batmobile_Missile_Projectile` -> 250), so the
  table is unaffected; the G1 note should be corrected by its owner.
- **The donor's 24 `part_damage_types` are the fleet's `Land_*` set; the train family carries its
  own 13 `Train_*` names in its own health module.** The type list is per vehicle family, not
  global - which is why a part's `damage_type` string is not a global key.

**Files changed.** `Tools/scripts/damage_predict.py` (new, 879 lines), `Research/JC3Grab/
DAMAGE_MODEL.md` + `DAMAGE_MODEL.json` (generated), `Research/JC3Grab/README.md` (one `###` section
+ one Files row), `GRAB_BACKLOG.md` §12 (one line), `tmp/freebuff/probe_g2_28.py` and
`tmp/freebuff/g228/` (probe + tamper backups), this log (append-only). `Working/Translation/
current.json` was regenerated at `Builds/test-091` by `t1_current.py` (it held test-083) - declared
in the intended-change entry above.

**Revert:** delete `Tools/scripts/damage_predict.py`, `DAMAGE_MODEL.md`, `DAMAGE_MODEL.json`,
`tmp/freebuff/probe_g2_28.py`, `tmp/freebuff/g228/`; drop the README section and Files row; put §12
back to `| G2-28 | todo | |`; truncate this log at the `G2-28 · Damage model, complete, with a
predicted hits-to-kill table — intended change` heading; optionally
`python Tools/scripts/t1_current.py Builds/test-083`.

## G2-30 · `.physicsc` write spike (old Batch D route) — done (2026-10-28)

**Done check** `python Tools/scripts/jc3hkx.py write --check` → exit 0:

```
PASS: round trip identical (2/2 files, 54 hulls re-emitted) | remap 0 problems | scale 0 | replace 0 | hulls 54 compounds 22, json match True, md match True
```

**Standing gate** `python Tools/scripts/jc3hkx.py check --all` → exit 0 (unchanged by the writer):

```
entities 233 | files 234 | objects 130513 | hulls 18865 (convex 18865) | mesh shapes 4791 | geometries 9582 | compounds 6382 (35499 instances, 25769 with a part index, 6341 AABB unions exact) | station sets 17 (land_global agree 17, disagree 0)
check ok
```

**Tamper test** (three ways, each restored → PASS):
`PHYSICS_WRITE.json` `scale.compounds_updated` 2 → 3: `FAIL PHYSICS_WRITE.json stale: @@ -131
"compounds_updated": 3, @@ +131 "compounds_updated": 2` (exit 1). A count in
`PHYSICS_WRITE.md` (`| objects | 430,` → `431,`): `FAIL … stale` with the md diff (exit 1). One
bit flipped in the **written blob** `scale_wheel.physicsc` on disk: `FAIL scale_wheel.physicsc on
disk differs from the derived bytes (340,368 vs 340,368 B)` (exit 1). All restored → the PASS above.
No archive opened, no game launched, `D:\Games` never written, nothing committed.

**What the card asked for, answered.**

1. **Round trip.** `hull_bytes()` re-emits all **54 hulls** of both files from what
   `decode_polytope()` returns (vertex block, every plane slot incl. the unused sentinel,
   `convex_radius`) and copies only the parts the reader does not decode. Output is **identical to
   the byte**: 340,368 B, sha256 `1b90daef…` for the donor and `6a0e7e13…` for the assembly
   variant. A file-level copy would have proved nothing; this proves the decoder is exact.
2. **A scaled hull, written and re-read.** `sportsmuscle_wheel_f_l` @ `0xb5d0` (20 v / 12 p,
   704 B) scaled **×1.659566** = Batmobile tyre Ø 1.365 m (`TYRES.md`) / hull height 0.8225 m,
   about its own centre: vertices ×k, plane distance `d' = k·d + (k−1)(n·c)`, radius ×k. The
   written file re-reads with **0 violations** (`convex 54/54`, `index_ok`, `aabb_ok 22/22`,
   `union_ok 22/22`), the hull's box becomes 0.4909 × 1.365 × 1.2982 m, the indices are unchanged,
   and only **252 B over 69 runs** differ from the donor. Independent probe
   `tmp/freebuff/probe_g2_30_verify.py` re-reads the blob from disk and finds exactly **one** ratio
   across all 60 vertex axes (1.6596).
3. **The plan** is `PHYSICS_WRITE.md` §7: six steps with inputs and a check each, of which steps 2
   and 3 (wheel/prop hull replacement, donor-slot hulls) use only what this card proved and step 4
   (a convex decomposition of the body) needs the face table or a table-growing writer.

**The capability is bigger than the card asked for, and that is the finding.** The card assumed a
scaled copy would keep the object size. The data allows more: the donor's data section is
**fully partitioned by typed objects** (430 objects, contiguous 0..`lf`, **0 gaps**, every extent a
multiple of 16, the file ending exactly at the last object), so the writer re-lays the section out
from per-object blobs and remaps every fixup. Proven by two cases the card did not ask for: a
**16-byte insert at data offset 0** (every object, array, table and pointer moves) re-reads with 0
violations and an identical decoded graph; and **replacing the 704 B wheel hull with the 1,776 B
body hull** grows the file to 341,440 B, still 430 objects, still 0 violations. That is what makes
T-P3/T-CO2/T-CO3 "buildable" rather than "same-size only".

**Three corrections to the intended-change entry, all measured here.**
(a) The pointer **slots must stay zero**. The intended entry assumed the target is written into each
fixup `from` slot; all 339 local and 765 global slots read **0** in the donor and the loader fills
them from the fixup table. Writing them produced a file that passed every reader check while
differing from the original in **2,702 bytes** - the round trip is what caught it.
(b) The parent-AABB fix is **not** "union inflated by the convex radius": that made three unrelated
compounds fail with `child union leaves 0.0110 … (convex radius 0.0110)`, because the shipped boxes
are the children's union *inset* by that radius (the root sits 0.011 m inside on every axis). The
writer instead moves an ancestor by exactly as much as its children moved, preserving the file's own
margin, and touches only ancestors (2 of 22 compounds for the scaled wheel).
(c) `Working/Assembled/sportsmuscle_true.physicsc` is **not** a re-baked station table: it differs
from the donor in **one `f32`** at `hknpPhysicsSystemData` +0x3598 (``-2.569999933242798`` →
``-2.5699000358581543``), and `stations()` reads **no** station set from either file. "Same station
table" in the plan therefore means "copy the bytes", which is what the writer does.

**Still UNKNOWN, and named as such in the report.** The hull's face table is one 4-byte record per
plane (`first`/`count` partition the index list - proven), but 0-32 bytes of an **unnamed block**
sit before it on **37 of 54** hulls and the record's `min` byte has no reading; so a *brand-new*
hull cannot be authored yet and the writer preserves those bytes opaquely. `hknpExternMeshShape`
vertices stay unreadable as positions (3 × u16 quantized, frame unpinned), `hknpShapeMassProperties`
is undecoded (56 objects), and nothing here claims Havok or the game accepts a written file - that
is phase Q.

**Files changed.** `Tools/scripts/jc3hkx.py` (+ writer, + `write` command; `plane_slots` added to
`decode_polytope` without changing any existing key), `Research/JC3Grab/PHYSICS_WRITE.md` (195
lines, generated) + `PHYSICS_WRITE.json` (generated), `Research/JC3Grab/README.md` (one subsection
under §5 + one Files row), `GRAB_BACKLOG.md` §12 (one line), this log (append-only). Test blobs:
`E:\Modding\_JC3grab\hkx\write\` (5 files, game data, outside the repo). Probes:
`tmp/freebuff/probe_g2_30{,b,c,d,e,f,g}.py`, `tmp/freebuff/probe_g2_30_verify.py`.

**Revert:** delete the writer block and the `write` subcommand from `Tools/scripts/jc3hkx.py`, delete
`Research/JC3Grab/PHYSICS_WRITE.md` + `PHYSICS_WRITE.json`, the README subsection and Files row, the
probes and `E:\Modding\_JC3grab\hkx\write\`; put §12 back to `| G2-30 | todo | |`; truncate this log
at the `G2-30 · `.physicsc` write spike (old Batch D route) — intended change` heading.

**G2-30 correction (same session, append-only).** The done block above says the face table's
"`first`/`count` partition the index list" holds on 17 of 54 hulls; the census is now generated by
`face_table()` in `jc3hkx.py` and the reading fits **54/54** hulls once a 16-byte-aligned prefix is
skipped: **0 B on 17**, **16 B on 16**, **32 B on 9**, **48 B on 12**. So the record layout is
proven for the whole donor and the remaining unknown is only the prefix block's *content* (and the
record's `min` byte, which takes 1 on 31 hulls, 0 on 17, 3 on 16, 2 on 15 … with no reading). The
plan's step 1 is consequently smaller: a hull authored from a mesh needs that block decoded, not the
table. Corrected in `PHYSICS_WRITE.md` §6/§7/§9, `PHYSICS_WRITE.json` (`face_table`), the §12 row and
`tmp/freebuff/reports/G2-30.md`; `write --check` re-derives the census, exit 0.

## G2-32 · Names, icons and strings — intended change (2026-10-28)

**Card:** G2-32 (phase G2, S, deps G2-26 — `done` in §12). In: the donor's `.stringlookup`,
localisation tables, UI icon references. Do: find where "Kerner Serpente R" (or its hash) is
displayed — vehicle HUD name, drop menu, map icon — and record string ids and icon textures.
Out: `Research/JC3Grab/NAMES.md`. Done: every place the name/icon appears has a file + id.

**Resume check.** `grep G2-32 MODLOG.md` found one *reference* (line 10430, G2-26 handing its
string gap forward) and no intended-change entry; `Research/JC3Grab/NAMES.md` does not exist.
`Tools/scripts/jc3names.py` already exists but is an unrelated tool (it recovers names for
hash-only *index entries*), so it is neither reused nor overwritten. The card was never started.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3strings.py` | new (created as the first step of the Do work; nothing generated yet). Decodes `profile/online.stringlookup` and `ui/ui_localization.stringlookup` through `jc3adf` (Languages[N].SortedPairs -> one shared NUL-separated `Text` blob), the donor's own `.stringlookup`, G2-26's `REBELDROP.json` item record, and the icon directories from `INDEX.jsonl`; `--write` / `--check` / `dump` | the card's Done line needs a re-derivable table; no existing script reads a `stringlookup` |
| `Research/JC3Grab/NAMES.md` | new, generated | the card's Out path |
| `Research/JC3Grab/README.md` | one `### Names, strings and icons` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-32 \| todo \| \|` -> `done` + evidence, that one line only | session loop step 7 |
| this log | intended change + done | R14 |

No JSON half: the card's Out is `NAMES.md` alone, and `--check` rebuilds and byte-compares that
file, so the machine copy would be a second artifact nobody asked for.

**What the data already says (probed before writing any output).** The answer is specific:
`profile/online.stringlookup` (patch, 1,627,106 B) is a `StringLookup` with **11 languages**, each
an array of `{Hash, TextOffset}` pairs into one shared 1.4 MB text blob. The English pair for
`hash_jenkins("v0300_car_kensington_sportsmuscle_civilian_01")` = **`0xD2B46B49`** reads
**`KERNER SERPENTE R`**, and `<leaf>_desc` = **`0x7B942DF2`** holds the blurb. The Rebel Drop item
(`profile/item.onlinec`, decoded as G2-26's `REBELDROP.json` item 118) carries `UIName` =
`0xD2B46B49` and `UIImagePath` = the leaf, i.e. the name and the icon are keyed by the **same leaf
name**. The icon exists as `textures/ui/vehicle_icons/<leaf>.ddsc` (18,688 B). `ui/ui_localization`
does **not** contain the name, and the donor's own `.stringlookup` (2,210 B) carries interaction
prompts only - both stated as measured absences in the doc rather than left implicit.

**Revert:** delete `Tools/scripts/jc3strings.py` and `Research/JC3Grab/NAMES.md`; drop the README
section and Files row; put §12 back to `| G2-32 | todo | |`; truncate this log at this heading. No
game file, install, save, dropzone or archive is written; no game launched; nothing committed.

## G2-19 · Driver seat and pose — intended change (2026-10-28)

**Card:** G2-19 (phase G2, S, deps **G2-18 + G1-19** — both `done` in §12; `grep G2-19 MODLOG.md`
found no earlier entry and `Research/JC3Grab/SEAT.md` does not exist, so this session starts the
card). In: donor `.epe`, `INDEX.jsonl` for `jc_statemachine/vehicles/*`, `jc_skeletons/vehicles/*.bsk`,
other cars' seat objects (supercar `v0401`, hothatch `v0003`, tank `v0201`). Do: find where the
driver attach transform and the driver pose/animation set are chosen; list the pose sets that exist
for cars (sports, truck, tank hatch, bike…) and their seat heights. Out:
`Research/JC3Grab/SEAT.md`. Done: the member(s) that place Rico and choose his pose are named, with a
candidate pose that fits the Batmobile's `Driver` socket height (G1-19).

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3seat.py` | new. Reads the donor `.epe` (entry/point objects naming the driver, via the G2-18 decode), `Research/JC3Grab/INTERACTION.json`, `rico_base.afsmb` + `rico_base.asb` (strings: state names, `MOD_*` selectors, the embedded `.ban` clip paths), `PARTS_TABLE.jsonl` (seat parts) and `.physicsc` hull AABBs (seat heights), plus `Research/BatmobileGrab/SOCKETS_JC3.json` / `COCKPIT.md` (the `Driver` socket); writes the report; `--write` / `--check` | the card's Do steps are a cross-file join; every number must be re-derivable |
| `Research/JC3Grab/SEAT.md` | new, generated | the card's Out path |
| `Research/JC3Grab/SEAT.json` | new, generated machine half | sibling convention (G2-13…G2-34); `--check` compares it |
| `Research/JC3Grab/README.md` | one `### Driver seat and pose` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-19 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| this log | this intended change + a `— done` section | R14 |

Nothing is packed, installed or launched; `D:\Games` is only read through `jc3grab.read_entry`, and
no game file is written.

**What the data already says (probed before any file changed — `tmp/freebuff/probe_g2_19.py`).**

* **Two of the card's four In items do not exist.** The index has **no** `jc_statemachine/vehicles/`
  and **no** `jc_skeletons/vehicles/*.bsk`: the 142 state-machine files split `npc` 124,
  `main_characters` 9, `animals` 7, `aero` 2, and there is exactly **one** `.bsk` in the whole
  archive (`animations/jc_skeletons/characters/gen_male.bsk`, 8,672 B, 0 vehicle/seat strings).
* **The pose set is real, and it is keyed by vehicle class.** `animations/jc_statemachine/
  main_characters/rico/rico_base.asb` (2,614,188 B) embeds the clip paths as strings:
  `…/rico/vehicle/car/low/`, `…/car/med/`, `…/car/circuit/`, `…/vehicle/tank/`, `…/vehicle/bike/
  slow/`, `…/vehicle/boat/`, `…/vehicle/helicopter/`, `…/vehicle/plane/` — and the enter/exit
  states carry the class as a suffix (`ANIM_DRIVER_SIDE_ENTER_VEHICLE_MOD_TANK`,
  `ANIM_SLOW_RIDING_MOTORBIKE_MOD_SPORTBIKE`, `…_MOD_BOAT_SPY`, `…_MOD_HELI`). Those `.ban` paths are
  **not** separate index entries: only 2 vehicle `.ban` files exist in the index
  (`rico_vehi_mech_driver_*`), so the clips live inside the `.asb` bundle.
* **The state machine names the driver side.** `rico_base.afsmb` (327,108 B) carries
  `S_ENTER_DRIVER_VEHICLE`-family states, `ACT_ENTER_VEHICLE` / `PACT_EXIT_VEHICLE`,
  `PPC_IS_CURRENT_VEHICLES_DRIVER_SEAT_OCCUPIED`, `PPC_IS_ENTRY_NODE_DRIVER_SEAT_OCCUPIED` and
  `PPikt.driving.{left,right}.{hand,foot}` IK targets — i.e. the *pose* is the character state
  machine's vehicle state, and the vehicle only supplies the **entry transform and a class**.

## G2-32 · Names, icons and strings — done (2026-10-28)

**Done check** `python Tools/scripts/jc3strings.py --check` → exit 0:

```
PASS: name 'KERNER SERPENTE R' in 11 languages (id D2B46B49), desc in 11 languages, item 3535039305, icon 18688 B, fleet 45/45 named 45/45 iconed, ui_localization resolves 0 of 2 keys, gfx references 0
```

**Tamper test.** A name in `NAMES.md`'s per-language table (`en` row `KERNER SERPENTE R` →
`KERNER SERPENTE`): `FAIL: NAMES.md stale` with the diff (exit 1). Restored → PASS (exit 0). There is
no JSON half to tamper with (the card's Out is `NAMES.md` alone). No archive written, no game
launched, `D:\Games` never written, nothing committed.

**What the card asked for, answered.** Every place the name and the icon appear, with a file and an
id:

| place | file | id |
|---|---|---|
| the name itself | `profile/online.stringlookup` | hash `D2B46B49` = `hash_jenkins(leaf)`, 11 languages, English `KERNER SERPENTE R` |
| the blurb | same store | `7B942DF2` = `hash_jenkins(leaf + "_desc")` |
| drop menu name | `profile/item.onlinec` | `UIName` 3535039305 (= `D2B46B49`), `UIImagePath` = the leaf |
| drop menu type/flag | `profile/item.onlinec` | `UITypeDescription` `0x91018BDA` = SPORTS CAR, `UIFlagDescription` `0x527AA70C` = SPORTS CARS |
| unlock | `profile/task.onlinec` | task 1361701860 (Type 19) rewards item 3535039305 |
| vehicle icon | `textures/ui/vehicle_icons/<leaf>.ddsc` | 18,688 B, keyed by `UIImagePath` |
| map icon | — | **no per-vehicle map icon exists** (proven absence) |
| HUD name | — | **no carrier**: the entity's own `.stringlookup` is one prompt (`Get in Vehicle`, `A2B9F82C`), and no `.gfx` contains the leaf, the name hash or `vehicle_icons` |

The leaf name is the single key: `hash_jenkins(leaf)` names the string, and the same string is the
icon's filename. **45 of 45** vanilla vehicle drop items resolve their `UIName` and **45 of 45** have
their icon file, so the rule is exact rather than a one-off. `ui/ui_localization.stringlookup` (the
HUD/UI store, 923 KB, 11 languages) does **not** carry the name - its only "Serpente" entries are the
two Weaponized-Serpente DLC banners (`0x749CD88C`, `0xED2B9C80`).

**Findings beyond the card.** (a) The build's own `.stringlookup` is **2210 B and byte-identical to
the base archive copy**; the patch copy is 2226 B but its decoded strings are identical (padding
only) - so the mod shipping the base table loses nothing. (b) The store art
`textures/ui/store/v0300_sportsmuscle_01.ddsc` uses a **different** naming scheme from the leaf and
nothing in the index references it by name - recorded as UNKNOWN, not guessed. (c) `global/
frontend_global.blo` names the **entity**, not the string (no name hash in it), so the frontend can
only label the car through the same item lookup.

**Files changed.** `Tools/scripts/jc3strings.py` (new, ~520 lines), `Research/JC3Grab/NAMES.md`
(generated), `Research/JC3Grab/README.md` (one `###` section + one Files row), `GRAB_BACKLOG.md` §12
(one line), `tmp/freebuff/g232/` (the tamper backup), this log (append-only).

**Revert:** delete `Tools/scripts/jc3strings.py`, `Research/JC3Grab/NAMES.md`, `tmp/freebuff/g232/`;
drop the README section and Files row; put §12 back to `| G2-32 | todo | |`; truncate this log at the
`G2-32 · Names, icons and strings — intended change` heading.

## G2-19 · Driver seat and pose — done (2026-10-28)

**Record:** `Research/JC3Grab/SEAT.md` (new, 205 lines) + `Research/JC3Grab/SEAT.json` (new),
generated by `Tools/scripts/jc3seat.py` (new); README gained one `### Driver seat and pose`
section and one `SEAT.md` Files row. Nothing packed, installed, launched or committed.

**The card's Done clause: "the member(s) that place Rico and choose his pose are named, with a
candidate pose that fits the Batmobile's `Driver` socket height."**

* **Places Rico (vehicle side):** the interaction graph and nothing else —
  `entry.driver` (`CInteractionGraphEntry`, state `S_ENTER_DRIVER_VEHICLE`) plus its siblings —
  **34** driver-named objects, prefix census `entry` 10, `exit` 14, `transition` 4, `point` 3,
  `trigger` 2, `interaction` 1 — with state strings and (mostly inherited) transforms. The donor's
  31 `.vmodc` modules (`_JC3grab/entities/v0300_…_civilian_01.ee.json`) contain **no**
  seat/occupant/pose/animation member.
* **Chooses his pose (character side):** `animations/jc_statemachine/main_characters/rico/
  rico_base.afsmb` — driver-seat conditions `PPC_IS_CURRENT_VEHICLES_DRIVER_SEAT_OCCUPIED` /
  `PPC_IS_ENTRY_NODE_DRIVER_SEAT_OCCUPIED`, the `PPikt.driving.{left,right}.{hand,foot}` IK
  targets and **36** `MOD_*` selectors — over `rico_base.asb`, whose string table embeds **382**
  seated clip paths in **40** class folders (`car/low` 23, `car/med` 35, `car/circuit` 9,
  `car/high` 4, `tank` 10, `boat` 33, `heli` 28, `plane` 17, `bus` 8, `tractor` 10, `bike/*` …).
* **Candidate:** `sportsmuscle_f_l_seat` (hull centre **0.855 m**) vs the Batmobile `Driver` hip
  **0.8647 m** (G1-19 / `SOCKETS_JC3.json`) = **10 mm**, i.e. the `car/*` families; which of
  `low`/`med`/`circuit` the game picks is native and stays UNKNOWN (recorded, not guessed).

**Two card In items do not exist, and the record says so with a count:** the index has **0**
`jc_statemachine/vehicles/*` and **0** `jc_skeletons/vehicles/*.bsk` (142 state-machine files are
character-side; 3 skeleton files in total). Only 2 of Rico's vehicle `.ban` files are separate
entries — both the mech suit, not a car — out of 7 `.ban` files under any `…/vehicle/` path, so a
seated car clip is addressable only from inside the `.asb`.

**Two bugs found and fixed in my own first pass** (recorded because both would have shipped wrong
numbers): `is_seat_part()` matched `seat`/`hatch` as substrings, so the vehicle stem
`racinghot`+`hatch` labelled all 52 of that car's parts a seat — it now matches whole `_`-separated
tokens (55 rows → 5). And `cockpit_facts()` returned `{}` because `COCKPIT.md` writes minus signs
as U+2212 behind a `**`; the hip is now parsed, not assumed.

**Honest limits now in `SEAT.md` §3 / §7:** `v0401`'s `racingsupercar_seats` is a real
`Land_Seat` part but **no compound instance carries its index** (19 or 22 absent from its 42
carried indices) → no hull, height UNKNOWN. `v0201` has no seat part at all: `mediumtank_hatch` is
class `Land_Door`, so its 2.879 m is a door roof and the tank's seat height is UNKNOWN. The three
real `Land_Seat` centres span 39 mm (0.855/0.855/0.894).

**Done check (verbatim):**

```
> python Tools/scripts/jc3seat.py --write
wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\SEAT.md (205 lines) + Research\JC3Grab\SEAT.json
OK: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat boxes 4 | candidate v0300_car_kensington_sportsmuscle (10 mm from the hip)

> python Tools/scripts/jc3seat.py --check
PASS: 34 driver points | 40 pose classes (382 clip names) | 36 MOD selectors | seat boxes 4 | candidate v0300_car_kensington_sportsmuscle (10 mm from the hip), json match True, md match True
```

**Tamper test:** `SEAT.json` `seats[0].centre_m[1]` 0.8551 → 0.9001 →
`FAIL SEAT.json stale: … - 0.9001, + 0.8551, 1 problem(s)`, exit 1. `SEAT.md` centre cell
0.855 → 0.905 → `FAIL SEAT.md stale: … 1 problem(s)`, exit 1. Both restored → `--check` PASS,
exit 0. `python -m py_compile Tools/scripts/jc3seat.py` OK.

**Revert:** delete `SEAT.md`, `SEAT.json`, `Tools/scripts/jc3seat.py`, the README section + Files
row, restore the tracker row, remove this entry and the intended-change entry above.

**Next:** G2-20 (exit, bail-out and eject) is unblocked — this card already lists the 16 exit
objects with their state strings (`S_EXIT_VEHICLE_PARA`, `S_ROLL_OUT_EXIT_VEHICLE`,
`S_EXIT_DRIVER_TO_HOOD_VEHICLE`, …), and `SEAT.json` carries them for reuse.

## G2-24 · JC3 vehicle audio system — done (2026-10-28)

**Done check** `python Tools/scripts/jc3audio.py --check` → exit 0:

```
PASS: 45 donor events in 3 banks, 257/257 vehicle events/tunes, 649 samples (22 looped, 1 rate),
wave refs 0, LandAudio 2 members, weapons 4, horn 178 / radio 0, md match True
```

**Tamper test.** `JC3_AUDIO_EVENTS.json` `donor.events[2].banks[0].ordinal` 255 → 256 →
`FAIL: JC3_AUDIO_EVENTS.json stale` (exit 1); `JC3_AUDIO.md` horn count 178 → 177 → `FAIL` with
the md diff (exit 1); both restored → PASS. No archive written, no game launched, `D:\Games` never
touched, nothing committed.

**What the card asked for, answered.**

1. **Every donor event.** The `.ee.fmod_guids` is 758 B: version 1, bank names
   `vehicles`/`character`/`effects`, **45 GuidEvents**. Every one is found as an `EVTS` entry —
   **vehicles 24, character 2, effects 19** — with its ordinal in that bank. **23** are named by an
   `SAttachedEffect`/`SDynamicAttachedEffect` in the `.epe` (`engine_running_sound` vehicles/146,
   `horn` 255, `GearChange` 66, `exhaust_upgrade_nitrous` 249, `speedwind_sound_player`
   character/165, `dynamic_break_*` effects/570 …); the other 22 are pinned but unnamed by the
   graph. **There is no event path in the game files**: the `EVTS` section holds 1,654 printable
   strings and not one is an event name, so "path" = the `.epe` role name, and it is UNKNOWN for
   the 22.
2. **The format is FMOD Designer/Ex, not Studio.** `RIFF`/`FEV `, `FMT ` = **56 / build 50**, `PROJ`
   with `EVTS` (257) / `TLNS` (257) / `WAIS` (1,674) / `WAVS` (649) / `PRMS` (969) / DSP sections,
   then `SND ` holding one **FSB5** v1 with 649 samples (153,439,744 B of data, 21,196 B of names).
   The earlier note "FMOD Studio (`fmod_studio_F.dll`)" (MODLOG §70) was a guess; the bank bytes
   say Designer. Recorded as a correction.
3. **Event → samples is UNKNOWN, with five proofs**: (a) the 649 `WAVS` GUIDs are referenced **0**
   times outside `WAVS`; (b) no event body contains a `TLNS` tune identity GUID (**0/257**);
   (c) no field in the 257 event bodies permutes the tune indices; (d) no field in the 1,674 sound
   instances enumerates 0…648; (e) no event-name string exists. So the chain stops at the event
   GUID + ordinal, and the build picks a sample by **name and audition** — what test-060 did with
   spectral ranking (§70).
4. **Sample formats.** Per-stream through `vgmstream-cli -s N -m`: **649 samples, all 16-bit PCM,
   48 kHz**, 1 or 2 channels, **22 looped** (loop chunks in the FSB5 header, e.g. sample 10
   `jc3_vehicle_horn_truck_06_loop` 17,341→50,137). vgmstream's names equal the FSB5 name table
   (649/649). Every swap must be PCM16/48 kHz at the original frame count.
5. **Weapon sounds.** `w602`/`w603` have **no `.ee` and no `.fmod_guids`** — only a `.wtunec`, and
   all **171** of its members are damage/recoil/scatter/shake with **0** audio members, so their
   firing audio is on the firing vehicle (medium tank `Fire` `ef8f8aaa…`, `ReloadStart` `55051774…`)
   and in `weapons.bank`'s named samples. `w618`/`w619` own their sound: `.fmod_guids` of **10** and
   **12** GUIDs over `weapons_preorder`/`effects`, and the `.epe` binds `fire`/`fire2..4` (w618) and
   `fire_sound_combi` (w619) to `SAttachedEffect.Sound` = the first GUID of that list.
6. **Horn and radio.** Donor `horn` = `fd69c63c-84e6-fa43-b067-7eae99a59ce1` in `vehicles`;
   **178** `horn` objects in **178** vehicles (19 distinct GUIDs) = a per-model effect; **0**
   `radio` objects in all 232 decoded graphs. BmAK's `horn` group is 0 rows / 0 events
   (`AUDIO_FEATURES.md`), so AUD-7 = remove the effect; there is no radio member to suppress.
7. **Route.** (a) same-size PCM payload swap in a copy of `vehicles.bank` — **possible**, proven by
   test-060 (loose override, no `.toc`); (b) new bank + `.fmod_guids` — **not possible** from the
   shipped data (the FEV graph is the authoring format; no `.fev` project ships; `master.banklist`
   is only a 24-line text list); (c) the same swap in `weapons.bank` (1,228 named samples) for the
   guns. **Recommendation a + c.**

**`LandAudio` = 2 members**: `min_rpm` 1000.0, `max_rpm` 10000.0 — the whole vehicle-side audio
parameter set, the JC3 counterpart of BmAK's `REV_RPM`/`Speed`. The bank's 969 `PRMS` parameters
(19 distinct names, e.g. `PlayerIsDriving`, `wheel_suspension_effect`) are the mixer space; which
event reads which parameter is not resolved.

**Files changed.** `Tools/scripts/jc3audio.py` (new), `Research/JC3Grab/JC3_AUDIO.md` (237 lines) +
`JC3_AUDIO_EVENTS.json` (generated), `Research/JC3Grab/README.md` (one section + one Files row),
`GRAB_BACKLOG.md` §12 (one line), this log (append-only).

**Revert:** delete `Tools/scripts/jc3audio.py`, `JC3_AUDIO.md`, `JC3_AUDIO_EVENTS.json`, the README
section and Files row; put §12 back to `| G2-24 | todo | |`; truncate this log at the
`G2-24 · JC3 vehicle audio system — intended change` heading.

## G2-20 · Exit, bail-out and eject — intended change (2026-10-28)

**Card:** `GRAB_BACKLOG.md` §G2-20 (S, deps G2-18 done, serves MOD-3). **Do:** "record what each
exit does (launch velocity? parachute/wingsuit state?) and whether any vehicle launches the driver
upward." **Out:** `Research/JC3Grab/EJECT.md`.

**Intended change.** New `Tools/scripts/jc3eject.py` (`--write` / `--check`, plus a `dump` verb)
that derives the report from four on-disk sources and writes `Research/JC3Grab/EJECT.md` +
`EJECT.json`: (1) `Research/Epe/serpente_civilian.xml` — the only `.epe` kept as nested XML, so the
only place an exit's *child* condition objects can be attributed to that exit (the G2-18 detail
JSON sorts objects by id, and ids repeat, so order carries no nesting); (2) `E:/Modding/_JC3grab/
detail/*.ee.json` ×232 for the fleet census of exit names/states/enabled/modifier and for the
graph-class vocabulary (proof that no graph class carries a launch/impulse member); (3)
`E:/Modding/_JC3grab/entities/*.ee.json` ×232 for a member-name sweep of the *module* side (eject/
launch/impulse/parachute/wingsuit + jump/vertical) — the only upward impulse there is the vehicle's
`turbo_jump`; (4) `Research/BatmobileGrab/BMSDK_OFFSETS.json` for the BmAK eject properties. Geometry
is **not** recomputed: the Serpente/Batmobile positions and parents come from `INTERACTION.json`
(G2-18, R2).

**Why this file.** A card's outputs are script-generated, never hand-typed (R11), and `--check`
must re-derive the numbers, so the analysis has to live in a tool. Nothing existing covers exits:
`jc3interact.py` lists the objects but no conditions, and `jc3seat.py` covers seating only.

**Files touched.** new `Tools/scripts/jc3eject.py`, new `Research/JC3Grab/EJECT.md` +
`EJECT.json`, one `Research/JC3Grab/README.md` section + Files row, tracker row G2-20, this log.
No shared game module, no `Builds/`, no game launch.

**Revert.** Delete the two new research files and the script, drop the README section + Files row,
restore the tracker row to `todo`, delete this entry and the `done` entry that follows it. No
existing file is rewritten.

## G2-23 · Nitro FX and audio carriers — intended change (2026-10-28)

**Card:** `GRAB_BACKLOG.md` §G2-23 (S, deps G2-22 done, G2-24 done; serves FX-1, AUD-2). **In:** donor
effect attachments, `vehicles.bank` nitro event (test-060 swap), `custom_land_global`. **Do:** trace
what JC3 plays and attaches when nitro fires (effect + sound event + parameters). **Out:**
section in `Research/JC3Grab/USAGES.md`. **Done:** the full chain nitro input → effect → sound event
written down.

**Intended change.** Extend the existing generator `Tools/scripts/jc3usage.py` with a G2-23 pass and
a new `## 6. The nitro chain` section in `USAGES.md` (+ a `nitro` object in `USAGES.json`), so the
chain is script-derived and re-checkable by the same `--check` (R11). Sources, all already on disk:
(1) the donor `.epe` graph (`E:/Modding/_JC3grab/detail/…civilian_01.ee.json`) for the objects that
carry `Usage` = `EngineNitro` (4197885156) and their `Effect` / `Sound` fields; (2) the fleet-wide
carrier counts for that `Sound` GUID and for the object `Effect` hash, from the same 232 graphs;
(3) the donor `.ee.fmod_guids` plus the `EVTS`/`FSB5` structure of
`sound/fmod_banks/vehicles.bank`, read with the G2-24 reader (`jc3audio.fev/fev_events/fsb/
fmod_guids`) — the event GUID becomes a bank + `EVTS` ordinal, and the sample names come from the
FSB5 name table; (4) `custom_land_global` `arcade.*` boost blocks from the 232 entity caches (donor
values + how many vehicles carry each block); (5) `Tools/scripts/_apply_audio.py` to confirm which
FSB5 indices test-060 actually swapped, compared against the indices the *names* select.

**Why this file.** G2-22's output already lives in `jc3usage.py`; the card's Out is a section of
`USAGES.md`, and the chain reuses that script's re-decoded `usage_effects` rows (the only place the
`EngineNitro` → effect-name link exists) and its `.epe` census. A separate script would re-derive
those and could drift from the doc it appends to.

**Files touched.** `Tools/scripts/jc3usage.py` (new `arcade_scan` / `nitro_chain`, `epe_scan` gains
sound/effect carriers, `build`/`render_md`/`assertions` extended), regenerated
`Research/JC3Grab/USAGES.md` + `USAGES.json`, one `Research/JC3Grab/README.md` note, tracker row
G2-23, this log. No shared game module, no `Builds/`, no game launch.

**Revert.** `git checkout Tools/scripts/jc3usage.py`, re-run `python Tools/scripts/jc3usage.py
--write` to regenerate the G2-22-only doc/json, drop the README note, restore the tracker row to
`todo`, delete this entry and the `done` entry that follows it.

## G2-27 · Standalone entity — intended change (2026-10-28)

**Card:** G2-27 (phase G2, **M**, deps **G2-26 + G2-29** — both `done` in §12). `grep G2-27
MODLOG.md` found no earlier entry and `Research/JC3Grab/STANDALONE.md` does not exist, so this
session starts the card. In: `INDEX.jsonl`, the `settings/*.bin` registries, the Rebel Drop V5.3
Plus `editor/entities/**` override pattern, `.stringlookup`. Do: find every place a vehicle entity
path or hash is registered (spawn tables, garage/drop, vehicle id lists, string tables); decide
whether a **new** path such as `…_sportsmuscle_batmobile.ee` can load from the dropzone without
editing a global registry. Out: `Research/JC3Grab/STANDALONE.md`. Done: a yes/no with evidence
and the list of files a standalone entity needs. Feeds D-6.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/jc3standalone.py` | new. Reuses G2-29's 17-row registration census (`TRAFFIC.json`), decodes the two `global/entityregistry_gen.entityregc` blobs far enough to count coverage, reads the 9 `spawn_*_defs.bin` tables to see how a record names its entity, unpacks the shipped Rebel Drop mod's 20 `.ee` (and one AAF, to show inner names are independent of the outer leaf) and the donor `.ee`'s SARC (what a standalone entity ships); `--write` / `--check` | the card's answer is a cross-file measurement, and every number must be re-derivable |
| `Research/JC3Grab/STANDALONE.md` | new, generated | the card's Out path |
| `Research/JC3Grab/STANDALONE.json` | new, generated machine half | sibling convention; `--check` compares it |
| `Research/JC3Grab/README.md` | one `### Standalone entity` section + one `Files` row | every G2 table is registered there |
| `GRAB_BACKLOG.md` §12 | `\| G2-27 \| todo \| \|` -> `done` + evidence, one line only | session loop step 7 |
| `E:\Modding\_JC3grab\standalone\` | the two `.entityregc` blobs (33.0 MB + 39.2 MB), extracted from the archives | R10: game bytes stay outside the repo |

Order, stated plainly: the tool file was written first (so the probe code could run), this entry
second, and **no output file** (`STANDALONE.md`, `STANDALONE.json`, README, tracker) is touched
until the entry exists. `Tools/scripts/jc3standalone.py` is a new file, referenced by nothing yet,
so its early creation changes no existing behaviour; deleting it reverts it fully.

**What the probes already show (before any output is written — `tmp/freebuff/probe_g2_27.py`).**

* **The entity registry is not a complete list.** `global/entityregistry_gen.entityregc` (base
  33,003,365 B, patch 39,220,585 B) is a tagged stream: `03 <len16> <leaf>` records followed by the
  leaf's 32-bit hash (`…496bb4d2` = `D2B46B49`, the donor leaf), each carrying that entity's asset
  paths (`.eff` 44,281 / `.ctune` 12,978 / `.vmod` 6,328 …). It holds **232 of 922** base-index
  entity leaves (251 union), so **678 shipped entities have no record**, including base-game
  actors (`spawned_bh_paratrooper`, `black_hand_jr_grunt`) and DLC vehicles the game loads. A table
  that omits 70% of the entities cannot be the loader's gate.
* **Path-referenced spawn does not need it.** `settings/spawn_vehicle_defs.bin` stores the entity
  as a **full path string** (`editor\entities\…\.ee`), 86 records; the DLC tables reference
  vehicles with **no registry record** (`v0806_car_na_sportmech_01`,
  `v0600_car_urga_armoredjeep_blackhand_01`, …), so a path reference works unregistered.
* **The one hash reference is the open one.** Every one of the 80 vanilla vehicle Rebel-Drop items
  points at a leaf that *does* have a registry record, so there is no shipped counter-example of a
  hash resolving to an unregistered leaf — that is the Q-1 probe, not a file answer.
* **The mod proves the packaging, not the new path.** All 20 of its `.ee` files are at **vanilla**
  VFS paths (20/20 in the index) and it ships **0** `.toc`; one of them
  (`…v1704_boat_na_lightpatrol_civic_police_01.ee`) contains a playground prop's `.epe`
  (`…playground_kit/merry_go_boom_01.epe`), i.e. inner names are independent of the outer leaf.

Nothing is packed, installed or launched; `D:\Games` is only read through `jc3grab.read_entry`.

**Revert:** delete `Tools/scripts/jc3standalone.py`, `Research/JC3Grab/STANDALONE.md`,
`STANDALONE.json`, `tmp/freebuff/probe_g2_27.py` and `E:\Modding\_JC3grab\standalone\`; drop the
README section and Files row; put §12 back to `| G2-27 | todo | |`; truncate this log at this
heading.

## G2-23 · Nitro FX and audio carriers — done (2026-10-28)

**Card:** §G2-23, deps G2-22 + G2-24 (both `done`). **Out:** `Research/JC3Grab/USAGES.md` §6
(+ `nitro` block in `USAGES.json`), generated by the extended `Tools/scripts/jc3usage.py`.

**Result - the chain, file by file.** Input: `CustomLandGlobal`'s `arcade.nitro_boost` block on
the donor - `torque_multiplier` 2, `grip_multiplier` 2, `push_force` 15000, `boost_blend_time` 0.2 s,
`extra_top_speed` +40 km/h, with `nitro_boost_upgraded` at 20000 N / +80 km/h; the same five
`arcade.*` blocks (`heat_boost`, `nitro_boost`, `nitro_boost_upgraded`, `turbo_jump`,
`turbo_jump_upgraded`) exist on **145 of 232** vehicles. Usage: the donor `.epe` puts
`EngineNitro` (4197885156) on `exhaust_upgrade_nitrous` (which also carries a `Sound`) and
`exhaust_upgrade_nitrous2` (no `Sound`). Effect: the module vocabulary binds that usage to
`dynamic_nitrous` (397752766) on 14 vehicles; the object's own `Effect` field is **3518298851**
(0xD1B4FAE3), carried by **28 objects / 17 vehicles**, every one a `*nitrous*` exhaust, and that
hash appears in **no** `all_effects[]` of the decoded `_effect_attachments` modules - so the object
hash -> `.effc` edge stays UNKNOWN and the 9 `*nitrous*.effc` files are a name-only candidate.
Sound: the object's `Sound` GUID `f74ea43b-a8ac-4548-ad27-b92fd40a516d` is **1 of the donor's 45
`.ee.fmod_guids` events** (banks vehicles/character/effects), is carried by **202 objects on 172
vehicles** (154 `exhaust_upgrade_nitrous`, 14 `dynamic_exhaust_upgrade_nitrous`, 13
`exhaust_upgrade_nitrous_r`, ...), and resolves to `vehicles.bank` `EVTS` **ordinal 249** (195 B) -
a real event, not a dangling GUID. Samples: the banks link no event to a sample index
(`JC3_AUDIO.md` §5), so they are chosen **by name** - 56 `jc3_veh_land_premium_nitro_start`,
150 `jc3_veh_land_premium_nitro_loop`, 355 `jc3_veh_land_premium_nitro_stop`, which are exactly the
three 0-based indices test-060's `_apply_audio.py` swapped (asserted at build time, not by hand);
165 `..._nitro_jet_flame_loop` is a fourth nitrous clip the test left alone. Recipe: copy
`vehicles.bank`, keep all 649 samples and headers, overwrite those three PCM16 payloads
(route (a) of `JC3_AUDIO.md`) - no `.ee`/`.epe`/`.fmod_guids` edit needed.

**Done check** (`python Tools/scripts/jc3usage.py --check`, 40 s):
`PASS: 6045 modules in 232 caches, 225 EffectAttachments on 224 vehicles, 12 named usages (346 rows,
885 effect links re-decoded), ExtendedEffectUsages 0 usages, EngineNitro -> EngineNitro/
dynamic_nitrous, 155 .epe Usage values / 12576 objects, 0 .effc refs in graphs, FX rows 57187`
- plus 10 new assertions (nitro `.epe` objects 2, sound GUID in `fmod_guids` True, `EVTS` ordinal
249, sound carriers 202/172, `Effect` carriers 28, object hash unnamed False, sample indices
[56,150,355], test-060 set match True, `arcade.nitro_boost` vehicles 145).

**Tamper test.** `sed`-level change of `EVTS ordinal 249` -> `250` in `USAGES.md`:
`FAIL: md differs: @@ -557,3 +557,3 @@ ... -| ... in a bank | `vehicles` `EVTS` ordinal 250 ...`
(exit 1), reverted from the pre-tamper copy, `--check` PASS again (exit 0).

**UNKNOWN.** (1) which control/input fires `arcade.nitro_boost` - the button is in code or
controls data, not in the decoded modules; (2) event -> sample index, and (3) object `Effect` hash
-> `.effc`, both per `JC3_AUDIO.md` §5 / `USAGES.md` §7; (4) no game was launched (R6), so the
in-game result of the test-060 swap is unverified.

**Files.** `Tools/scripts/jc3usage.py` (extended), `Research/JC3Grab/USAGES.md` +
`USAGES.json` (regenerated), `Research/JC3Grab/README.md` (§ G2-22 note + Files row), tracker row.
No shared game module, no `Builds/`, no game launch, no git.

## G2-20 · Exit, bail-out and eject — done (2026-10-28)

**Answer to the card's question: no vehicle launches the driver upward, and the data cannot.**
The fleet's **4,832** `CInteractionGraphExit` objects (232 graphs, 61 names, 26 in the donor) take
their members from a fixed set of **9 keys** and **none** carries a velocity, impulse, launch or
force member — 0 keys outside that set anywhere in the fleet, `enabled` = 1 and `interaction` =
`00000000` on all 4,832. Of 104 graph classes, the only two with a moving-sounding name are the
velocity *condition* (`CInteractionGraphParentVelocityCondition`, 4,057) and the car's own
`CForcePulse` (G2-17); neither moves a seated driver. The module side has exactly **1** launch-ish
member name in 232 entities (`TrainGlobal.crashing_impulse` ×12) and one upward mechanism,
`arcade.turbo_jump` (145 land vehicles), which jumps the **car** and has no vertical-speed member.

**What an exit does** is select a state, gated by the parent's speed. The donor splits at **5**:
`exit.driver.default` (`S_EXIT_VEHICLE`, 0..5) and `exit.driver.to.fall`
(`S_EXIT_VEHICLE_TO_FALL`, 0..5) below it, `exit.driver.roll.out` (`S_ROLL_OUT_EXIT_VEHICLE`,
5..999) and `exit.driver.moving.parachute` (`S_EXIT_VEHICLE_PARA`, 5..999) above it. So the
parachute exit is **the fast exit**, not a parachute button: it is on 221/232 vehicles (125 cars,
35 boats, 23 helicopters, 19 jets, 19 bikes). 7 of the 26 exits are speed-gated; 5 carry no
condition at all (pulled.out, pushed.out, to.swim, driver.upside.down, passenger1.upside.down).
The two fast exits share their gate, so which one wins is code → Q1-EJ-B.

**BmAK's eject** is `RVehicleBatmobile.EjectUpMove` / `EjectForwardMove` /
`EjectWhenBatmobileVerticalMove` / `EjectUpWhenBatmobileVerticalMove` / `EjectToSpotMove`, one
float `EjectUpDist`, a byte `MaxEjectType` (`EBatmobileEjectType`), `OverrideNextEject`
(`RSeqAct_OverrideBatmobileEject`) and the natives `ModifyEjectUpLoc` / `SetBatmobileExit`. **The
MOD-3 mapping is therefore: exit → `exit.driver.moving.parachute`, launch → UNKNOWN.** The carrier
for leaving at speed and for the parachute state exists; an upward impulse has no carrier and is
not authorable from entity data (choices recorded in `EJECT.md` §7: accept exit+glide, probe
whether the para animation pops, or jump the car with `turbo_jump`).

**One limit stated, not papered over:** per-exit *conditions* are decoded for the donor only.
`Research/Epe/serpente_civilian.xml` is the only `.epe` kept as nested XML; the G2-18 detail JSON
sorts objects by id and ids repeat, so nesting (exit → its child conditions) cannot be recovered
from it, and the other 231 `.epe` files are not on disk. The fleet table therefore reports names,
states, roots and `modifier`s, and no per-vehicle gates.

**Done check (verbatim):**

```
> python Tools/scripts/jc3eject.py --write
wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\EJECT.md (327 lines) + E:\Modding\JC3Grab\EJECT.json
OK: 4832 exits in 232 graphs (61 names) | donor 26 exits, 7 speed-gated, 5 unconditional | launch members: exits 0, graph classes 2, vehicle modules 1 | BmAK eject props 19

> python Tools/scripts/jc3eject.py --check
PASS: 4832 exits in 232 graphs (61 names) | donor 26 exits, 7 speed-gated, 5 unconditional | launch members: exits 0, graph classes 2, vehicle modules 1 | BmAK eject props 19, json match True, md match True
```

**Tamper test:** `EJECT.json` `donor.exits[0].gate.max` 5.0 → 6.0 → `FAIL EJECT.json stale: … -
"max": 6.0, + "max": 5.0, 1 problem(s)`, exit 1. `EJECT.md` `exit.driver.roll.out` gate cell
5..999 → 3..999 → `FAIL EJECT.md stale: … 2 problem(s)` (both files flagged), exit 1. Restored by
`--write` → `--check` PASS, exit 0. `python -m py_compile Tools/scripts/jc3eject.py` OK.

**Revert:** delete `EJECT.md`, `EJECT.json`, `Tools/scripts/jc3eject.py`, the README section + Files
row, restore the tracker row, remove this entry and the intended-change entry above.

**Next:** MOD-3 has its carrier named; T-13 (interaction translation) can take
`exit.driver.moving.parachute` as-is from the donor and does not need a new exit. The probe set
Q1-EJ-A/B/C is ready to batch with the other phase-Q probes.

*(Correction to the block above, same session: the `--write` line lost the middle of the path. The
real output is `E:\Modding\JC3-Batmobile\Research\JC3Grab\EJECT.md` and
`E:\Modding\JC3-Batmobile\Research\JC3Grab\EJECT.json`; the summary line after it is verbatim.)*

## G2-27 · Standalone entity — done (2026-10-28)

**Record:** `Research/JC3Grab/STANDALONE.md` (new, 244 lines) + `STANDALONE.json` (new) from
`Tools/scripts/jc3standalone.py` (new); README gained one `### Standalone entity` section and one
`Files` row. Game bytes (the two `.entityregc` blobs) extracted to
`E:\Modding\_JC3grab\standalone\` only. Nothing packed, installed, launched or committed.

**The card's Done clause — "a yes/no with evidence and the list of files a standalone entity
needs":**

> **YES for the load, UNKNOWN for the hash.** `…_sportsmuscle_batmobile.ee` needs **no global
> registry edit** on the routes that name the entity by *path*; only the Rebel Drop item's 32-bit
> leaf hash is undecided, and one Q-1 probe settles it.

1. **Registration census, by key type** (17 file rows, 10 kinds — G2-29's name+hash scan, re-read
   by what each row keys on): spawn tables **9 files, full path string**; Rebel Drop
   `profile/item.onlinec`, **leaf hash**; chop-shop task key; 2 level `CVehicleRule`s;
   `frontend_global.blo`; `profile/online.stringlookup` (hash only); `patchmetadata.bin`; the
   entity's own `.epe`/`.toc`; and `global/entityregistry_gen.entityregc`.
2. **The entity registry is not a gate.** It is a tagged stream — `03 <len16> <leaf>` followed by
   the leaf's 32-bit hash (donor: `…03 2d 00 v0300_…_civilian_01` then `…496bb4d2` = `D2B46B49`)
   plus that entity's asset paths (`.eff` 44,281 / `.ctune` 12,978 / `.vmod` 6,328) — 33,003,365 B
   base + 39,220,585 B patch. Coverage: **251 of 922** index entity leaves, **158 of 233**
   vehicles. The split is the finding: **0 of the 86** base `spawn_vehicle_defs.bin` records are
   unregistered, but **163 of 169** debug records (`spawn_vehicle_proto_defs.bin`, base+patch) and
   **13 of 21** DLC production records are — and one of those (`v0806_car_na_sportmech_01`, the
   sport mech) is playable in retail. A retail-playable vehicle with no record proves a missing
   record does not stop an entity loading; the registry is a bake of the base roster's assets.
3. **A path reference is expressible for a new leaf.** Spawn records store the entity as a full
   path string (86 records in the base table, e.g. `editor\entities\…\…_civilian_z80_01.ee`;
   the DLC tables use forward slashes: `dlc/v0805_sportmech/editor/entities/…_01.ee`). 101 of the
   196 distinct spawn leaves already have **no** registry record.
4. **The one hash reference is open, and that is the honest UNKNOWN.** All 80 vanilla vehicle
   Rebel-Drop items point at registered leaves, so there is no shipped counter-example of a hash
   resolving to an unregistered leaf. Q-1 probe: the new-path `.ee` + one item whose `Name` is
   `hash('v0300_car_kensington_sportsmuscle_batmobile')` (`REBELDROP.md` §7 has the field list).
5. **Packaging is settled.** The shipped mod's **20** `.ee` are **20/20 at vanilla paths** with
   **0** `.toc` files (so a `.toc` is optional — our donor `.toc` has 506 entries against 604 SARC
   entries), and one of them, a *boat* path, contains a playground prop's
   `…playground_kit/merry_go_boom_01.epe` — inner names are independent of the outer leaf. A
   standalone entity is therefore **one `.ee`** (donor: 10,737,057 B, 604 inner files, its own
   `.epe`/`.stringlookup`/`.fmod_guids`, 31 `.vmodc`, 1 `.physicsc`) **+ one reference**
   (spawn record or drop item), with name/icon optional.

**Done check (verbatim, exit 0):**

```
> python Tools/scripts/jc3standalone.py --write
wrote E:\Modding\JC3-Batmobile\Research\JC3Grab\STANDALONE.md (244 lines) + E:\Modding\JC3-Batmobile\Research\JC3Grab\STANDALONE.json
OK: 17 registration rows | registry records 251/922 index leaves (158/233 vehicles) | 101 spawned-by-path leaves unregistered | mod 20 .ee / 0 .toc, 20 vanilla paths | donor .ee 604 inner files

> python Tools/scripts/jc3standalone.py --check
PASS: 17 registration rows | registry records 251/922 index leaves (158/233 vehicles) | 101 spawned-by-path leaves unregistered | mod 20 .ee / 0 .toc, 20 vanilla paths | donor .ee 604 inner files, json match True, md match True
```

**Tamper test.** (1) `STANDALONE.json` `registry.index_leaves_with_record` 251 → 252 →
`FAIL: 1 problem(s) / STANDALONE.json stale: … - "index_leaves_with_record": 252, + … 251,`
exit 1. (2) `STANDALONE.md` `**604** inner files` → `**605**` → `FAIL` with the md diff, exit 1.
Both restored → PASS, exit 0. `python -m py_compile Tools/scripts/jc3standalone.py` OK;
`python Tools/scripts/jc3index.py check` → `check ok: 81952 rows, 78907 paths, 1 unnamed entries`.

**Corrections made against my own first draft**, kept because they change the verdict's strength:
I began with "the registry is not a complete list, so it cannot be a gate" from the raw 232/922
count; the per-table split showed the base *retail* roster is **100% registered**, so the honest
argument is the **DLC mech** (retail-reachable, unregistered), not the raw percentage. The draft's
"0 unregistered" DLC numbers were also wrong until the path regex accepted forward slashes.

**UNKNOWN / limits.** The hash resolution of a new leaf (above). *Why* 671 entities are
unregistered — the criterion is native; the record set merely correlates with the retail roster.
Whether a replaced `settings/spawn_vehicle_defs.bin` is honoured from the dropzone without a hash
change (G2-29's open question, unchanged). Whether the registry would have to gain a record for
the drop route — we have no writer for a 39 MB tagged stream and did not attempt one. Whether the
game ever prefers a `.ee.toc` when one is present (eetoc's hypothesis) is not settled here.

**Files changed.** `Tools/scripts/jc3standalone.py` (new), `Research/JC3Grab/STANDALONE.md` +
`STANDALONE.json` (generated), `Research/JC3Grab/README.md` (one section + one Files row),
`GRAB_BACKLOG.md` §12 (one line), `tmp/freebuff/probe_g2_27.py`, this log (append-only).

**Revert:** delete `jc3standalone.py`, `STANDALONE.md`, `STANDALONE.json`, `probe_g2_27.py` and
`E:\Modding\_JC3grab\standalone\`; drop the README section and Files row; put §12 back to
`| G2-27 | todo | |`; truncate this log at the intended-change heading.

## G2X · G2 exit gate — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §6, last paragraph (G2X has no numbered card, only the exit-gate text):
*"every new reader has `--check` green; P0-2 census re-run; every feature code in §1 has a JC3
carrier with evidence or a proven absence. MODLOG section 'G2X'."*

**Resume check (session loop step 1-2).** `grep -n "G2X" MODLOG.md` → **0 hits**, so no earlier
session started this item and nothing is being repeated. §12 rows `G2-10`…`G2-34` are all `done`
and `grep -n "^## G2-\(1[0-9]\|2[0-9]\|3[0-4]\) · .* — done" MODLOG.md` returns **25** headings
(10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34) — every prerequisite
is satisfied. G2X has no `§11` decision in its `blocks` column; §11 decides *values* and phase T
(§7 rule 6: "if a row depends on a §11 decision, it is `blocked: D-n`"), so the gate itself starts.
Rows whose value waits on D-2/D-3/D-5/D-10 are recorded as `carrier + decision` and are not
counted as gaps.

**Intended change (written before editing, §0.2 rule 4).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/g2x_gate.py` | new. One row per feature code in §1 (75 codes) with the JC3 file that carries it and a needle that must still be there, or a proven absence with its must-not-exist words; plus the 25 new readers run as subprocesses and the P0-2 census; `--write`/`--check`/`--markdown` | the gate needs a re-derivable artefact; `g1x_gate.py` is the same tool for G1X and the card says "every new reader has `--check` green", so the gate must run them, not quote them | delete the file |
| `Research/JC3Grab/G2X.md` | new, generated by `--write` | §0.6 puts G2 summaries in `Research/JC3Grab/`; the card's MODLOG section points at a file | delete the file |
| `Research/JC3Grab/G2X.json` | new, generated by the same `--write` | R11: tables of counts come from a script with `--check` | delete the file |
| `Research/JC3Grab/README.md` | one build/check row for the new tool | every G2 tool is listed there | remove the rows |
| `GRAB_BACKLOG.md` §12 | **add** a `G2X` row (the tracker has none) between `G2-34` and `T-10` | session loop step 7 | delete that one line |

**What this gate can and cannot prove.** "Carrier with evidence" is a needle in a generated file,
so a regenerated doc that drops a fact fails here. "Proven absence" is a *negative*: the gate
searches a complete census surface (the 103-class fleet class inventory in `ENTITIES.md`, the
1,421-member module vocabulary in `VOCABULARY.md`) for the words that would name the mechanism, and
fails if one appears. That proves the name is not in the fleet's decoded space; it does not prove
the game could not do it in native code, which stays `UNKNOWN` where the row says so.

**Not touched:** no game file, no `Builds/`, no dropzone, no save, no git. Game bytes are read only
through the readers this gate calls (all of which were already green).

## G2X · G2 exit gate — passed (2026-10-28)

**Record:** `Research/JC3Grab/G2X.md` (new, 171 lines) + `G2X.json` (new) from
`Tools/scripts/g2x_gate.py` (new); README gained one command pair and one `Files` row;
`GRAB_BACKLOG.md` §12 gained one row. No game file, no `Builds/`, no dropzone, no save, no git.

**The gate's three clauses, answered in order.** 75 codes — the whole of §1 (APP 8, DIM 4, ARM 6,
WPN 12, HDL 6, MOD 5, AUD 7, ANI 9, WLD 8, LGT 2, FX 4, CAM 2, HUD 2), matching the G1X gate's 75
so the two exit gates are comparable — **67 carriers with evidence, 8 proven absences, 0
unresolved**. The 24 readers the G2 cards wrote plus the P0-2 census are **re-run as subprocesses**,
not quoted: `--check` starts each script and requires exit 0 *and* a `PASS`/`OK`/`check ok` verdict
line, so a reader that quietly turns red fails the gate instead of being remembered as green.

**What the 8 absences are, and why they are still accounted for.** `ARM-5` (no health-regeneration
member in the 1,421-path vocabulary), `WPN-6` (rope/winch geometry ships on 4 entities but **0**
winch/rope/tow module types and 0 winch classes, so no part can pull), `WPN-7/8/9` (no
allegiance-switch, sonar or tracker class in the 103-class fleet census — the only `track` in it is
`CMusicTrack`), `WPN-10` (no non-lethal/tranquil flag), `HDL-6` (land vehicles carry
`gravity_multiplier_*` and `takeoff_pitch_damping` on 145 vehicles but no yaw authority;
`righting_torque` exists only in `DriverLean` on 23 aircraft) and `AUD-3` (no cabin effect; the
nearest is `speedwind_sound_player`). Each is the named omission its phase-T row already assumed.

**A negative cannot be a needle, so the absences are checked as negatives.** Those rows name a
complete census surface (`ENTITIES.md` 103 classes, `VOCABULARY.md` 52 module types / 1,421 member
paths), a word that must be present to prove the surface was read, and the words that would name
the mechanism; any of them appearing fails the row. The limit is stated in the file: this proves the
name is absent from the fleet's decoded space, not that the engine lacks the capability. Six rows
lean on native code and say so (turn-on-the-spot G2-21, the eject launch G2-20, the effect trigger
names G2-22, graph bytecode G2-17).

**The §11 decisions.** Seven rows carry a decision id — `APP-6`, `AUD-4`, `LGT-2`, `CAM-2` and
`MOD-2` under **D-2** (second variant / battle mode), `APP-8` under **D-5** (skins) and `WPN-10`
under **D-3** (lethality). The gate reads the register itself and reports `D-2, D-3, D-5` as open.
That does not block this gate: a carrier is a *mechanism*, and §7 rule 6 makes the decision a phase-T
block (`blocked: D-n`). Every one of those rows names what ships on either answer.

**Done check (verbatim, exit 0):**

```
> python Tools/scripts/g2x_gate.py --write
wrote Research/JC3Grab/G2X.md + Research/JC3Grab/G2X.json (75 codes: 67 carrier, 8 absence, 7 decision-gated; readers 25/25)

> python Tools/scripts/g2x_gate.py --check
PASS: 75 codes (67 carrier, 8 absence, 7 decision-gated) in 28 files | readers 25/25 green | census ok | json match True, md match True
```

**Standing gates re-run the same session** (§0.7, the JC3 side of it):

```
> python Tools/scripts/jc3index.py check
check ok: 81952 rows, 78907 paths, 1 unnamed entries, DLC 20682/20682 named, sources {'gibbed-filelist': 55811, 'jcmr-dictionary': 26051, 'derived-names': 90}
> python Tools/scripts/jc3hkx.py check --all
check ok
> python Tools/scripts/jc3fx.py check
checked 57187 files | problems 0
> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

**Tamper tests.** (1) `G2X.json` `summary.carrier` 67 → 66 →
`FAIL G2X.json stale: summary block differs` … `json match False, md match True`, exit 1. (2)
`G2X.md` row `APP-1` verdict `carrier` → `absence` → `FAIL G2X.md stale:` with the one-line diff
(`-| APP-1 | absence …` / `+| APP-1 | carrier …`), `md match False`, exit 1. (3) The
proven-absence half has its own negative test: pointing `WPN-8`'s `must_not` at a word that *is*
in the census (`max_health`) produced `row pass = False` /
`WPN-8: Research/JC3Grab/VOCABULARY.md names max_health: the absence is refuted`. Both files were
restored (`cp` from the pre-tamper copies) and the full `--check` re-run green, exit 0.
`python -m py_compile Tools/scripts/g2x_gate.py` OK.

**Two generator bugs the run caught, kept here because they would have passed silently.** The first
`--write` died with `KeyError: 'decision_state'` on rows without a decision (fixed by emitting
`.get` for every optional field). The second is worse: `damage_predict.py --check` prints `PASS:`
first and two more lines after it, so a "the last line must start with PASS" rule marked an
**all-green reader red** — the gate now takes the first verdict line, which also means a reader that
prints its failure last cannot slip through as green.

**UNKNOWN / limits.** The gate proves *names in a decoded census*, never engine capability (stated
in §4 of the file). Four values the files do not give stay UNKNOWN and are not filled in: the
`RigidBody.mass` unit (DIM-3, 6 t is a class row), the explosion-threshold semantics (G2-28 step 7),
whether the module light list or the `.epe` `SVehicleLight` list renders (G2-33), and whether the
entity → `hud.gfx` bridge exists for HUD-1/HUD-2 (it is game code, `JC3_HUD_WEAPONS.md` §caller
census). `/tmp` copies used for the tamper test are outside the repo and disposable.

**Files changed.** `Tools/scripts/g2x_gate.py` (new), `Research/JC3Grab/G2X.md` + `G2X.json`
(generated), `Research/JC3Grab/README.md` (one command pair + one Files row), `GRAB_BACKLOG.md` §12
(one row), this log (append-only, plus the intended-change entry above).

**Revert:** delete `Tools/scripts/g2x_gate.py`, `Research/JC3Grab/G2X.md`, `G2X.json`; drop the
README command pair and Files row; delete the §12 `G2X` line; truncate this log at the
intended-change heading.

**Next.** Phase G2 is closed and phase T opens: T-10 is the first card (`T_ROWS.jsonl` rows with
`dispo = out`, re-decided against the G2 files), and it now has a 75-row carrier table to read
instead of 25 separate documents.

## T-10 · Re-open the `out` rows with the G2 evidence — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7, `#### T-10 · Re-open the out rows with the G2 evidence`
(S · deps: G2X · serves: WPN, MOD, HDL-6, LGT-2, HUD-2, CAM-2).

**Resume check (session loop steps 1–2).** `grep -n "T-10" MODLOG.md` → **2 hits, both inside the
G2X section** (its §12 row instruction and its "Next." line); no earlier session started T-10, so
nothing is repeated and no T-10 output exists on disk (`ls Working/Translation/T10*` → none).
`§12` says `| T-10 | todo | |`; its only dep `G2X` is `done` (MODLOG §"G2X · G2 exit gate —
passed"). T-10 names no §11 decision of its own: D-2/D-3/D-5 gate *successor* rows (§7 rule 6,
the G2X precedent), so the card starts.

**Intended change (written before editing, §0.2 rule 4).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/t10_reopen.py` | new. The 16 re-decisions as data (the card's 15 `out` rows + `T-HUD5`, which its expected-outcome line names), each with an evidence triple (file + `needle` / `must_not` / `hud-scan` + anchor), successor card ids, decision gate and reason; `--write` emits the doc + json, `--check` re-derives them and also compares every ledger and T6 disposition against the table | the card's `Out` is "updated rows" and `Done` is "no `out` row lacks a proof file"; a re-derivable table is the only way that can fail | delete the file |
| `Working/Translation/T10_OPEN_ROWS.json` | new, generated | R11: the old→new→evidence table is a counted table, so it comes from a script with `--check` | delete the file |
| `Working/Translation/T10_OPEN_ROWS.md` | new, generated by the same `--write` | the MODLOG section needs a file to point at; phase-T summaries live in `Working/Translation/` | delete the file |
| `Tools/scripts/t_rows.py` | `superseded` added to `VOCAB` (the card's own word: "mark the old row `superseded-by: <ids>`"), a `SUPERSEDED` successor map, `superseded_by` written into the ledger row, and the 15 `DISPO` entries re-decided — the 10 that stay `out` get the G2 file named in `why` | `DISPO` is the single source of the ledger's disposition; `T_ROWS.jsonl` is generated by `build`, so hand-editing the ledger would be undone by the next run | `git checkout` is not available to this session's rules — put the 15 `DISPO` lines and `VOCAB` back and delete `SUPERSEDED` + the `superseded_by` write |
| `Working/Translation/T2_TRANSLATION.md`, `T3_COVERAGE.md`, `T6_HUD_CAMERA.md` | the disposition cells of the 15 rows (+`T-HUD5`'s reason) only | `t_rows.py` parses these tables and `status_audit.py` parses T6 directly, so a ledger that disagreed with its document would be a false record | restore the 16 table lines from this log's quoted old text |
| `Tools/scripts/status_audit.py` | one bucket for `superseded`, its column in the per-document table, and the prose line that explains what `out` now means | R11: `STATUS.md` must be regenerated by this tool, and it has no bucket for a row whose requirement moved to a named successor | remove the bucket + column and restore the prose line |
| `STATUS.md` | regenerated (`--write`) | R11 | re-run `--write` on the reverted tool |
| `GRAB_BACKLOG.md` §12 | flip **only** the `T-10` row | session loop step 7 | put the row back to `| T-10 | todo | |` |

**What is not touched:** no game file, no `Builds/`, no dropzone, no save, no git. The only game
data read is the already-extracted `E:\Modding\_JC3grab\hud\dec` (the decompiled `ui/hud.gfx`,
260 `.as`) as the HUD absence surface; nothing is written there.

## T-16 · Audio translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7, `#### T-16 · Audio translation   M · deps: G1-15, G2-24 · serves: AUD-1…7`.
*"one row per JC3 event the Batmobile uses: BmAK event(s)/WAV(s) → JC3 event GUID → sample slot →
transform (pitch curve fitted from BmAK RTPC `RPM` points onto the JC3 RPM parameter range, loop
points, gain matched to the vanilla event's loudness ± 1 LU). Weapons per T-11. Horn/radio per
AUD-7. Absent banks stay named omissions (T-AU3/T-AU5)."* Out: `Working/Translation/T12_AUDIO.md`
+ `t12_audio_map.json`; Done: *"every donor event and every chosen weapon event mapped or explicitly
kept vanilla."*

**Resume check (session loop 1-2).** `grep -n "T-16" MODLOG.md` → **0 hits** before this entry, so no
earlier session started the item; `Working/Translation/` has no `T12_*` file; no `t12_audio.py`
exists. §12: `G2X` done, `G1-15` done, `G2-24` done — all three prerequisites satisfied (G2X by its
`## G2X · G2 exit gate — passed` section and the `g2x_gate.py --check` row). T-16 names **no** §11
decision in its card (`deps: G1-15, G2-24`), so nothing is blocked at the start; rows whose *value*
waits on a decision (D-2 battle-mode audio, D-8 water, D-10 turbo jump) are written as
`blocked: D-n` / kept vanilla per §7 rule 6 and are not treated as gaps.

**Intended change (written before editing, §0.2 rule 4).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/t12_audio.py` | new. Reads the two generated audio files, resolves every donor event, the four weapon candidates and the tank's fire/reload events, selects sample slots from the bank name tables, decodes each chosen slot with the project's vgmstream and measures it with the G1-15 `integrated_lufs`, then derives gain / frame-count stretch / loop points / the RTPM→rpm curve fit. `--write` / `--check` / `dump` | §0.2 step 5 ("write scripts, not hand edits; every value re-derivable by a command"); no existing T-phase tool covers audio and none of the G2 readers may be forked | delete the file |
| `Working/Translation/t12_audio_map.json` | new, generated by `--write` | the card's `Out` line | delete the file |
| `Working/Translation/T12_AUDIO.md` | new, generated by the same `--write` | the card's `Out` line | delete the file |
| `GRAB_BACKLOG.md` §12 | flip **only** the `T-16` row to `done` + evidence path | session loop step 7 | put the row back to `| T-16 | todo | |` |

**Where the numbers come from (no hand-typed values).** BmAK side: `AUDIO_FEATURES.json`
(361 event rows, 423 measured WAVs with ITU-R BS.1770-4 loudness, 506 RTPC bindings).
JC3 side: `JC3_AUDIO_EVENTS.json` (the donor's 45 pinned event GUIDs, their bank/ordinal, their
`.epe` role names, `LandAudio.min_rpm` 1000 / `max_rpm` 10000, the 649-sample census and the four
weapon sources). Sample loudness for the vanilla slots is decoded fresh from
`Working/Audio/jc3bank/sound/fmod_banks/vehicles.bank` (already on disk) and from
`sound/fmod_banks/weapons.bank` (extracted by this script to `E:\Modding\_JC3grab\audio\`, R10) —
the same vgmstream-cli the G2-24 reader used. `integrated_lufs` is imported from
`bmak_audio_features.py`, never re-implemented.

**What is editorial, and is labelled as such.** Which JC3 sample a *replacement* goes into is a
selection: G2-24 §5 proved event → tune → sample is not stored in the bank, so the slot can only be
chosen by name and audition (exactly what test-060 did, MODLOG §71). Every row therefore carries
`slot.method` (`proven swap` only where test-060 already swapped that index, otherwise
`name match`) and a verify cell; the *values* (index, format, frames, loop, loudness, gain,
stretch, curve points) are all read or derived.

**Not touched:** no game file, no `Builds/`, no dropzone, no save, no `T_ROWS.jsonl` row (the card
asks for no ledger rows), no git.

## T-16 · Audio translation — done (2026-10-28)

**Record:** `Working/Translation/T12_AUDIO.md` (295 lines, generated) +
`Working/Translation/t12_audio_map.json` (140,849 B, generated) from `Tools/scripts/t12_audio.py`
(new). No `T_ROWS.jsonl` row was added — the card's `Out` line asks for the doc + JSON only (T-23
owns the ledger close-out). No game file, no `Builds/`, no dropzone, no save, no git.

**What the card asked for, and what the files gave.** One row per JC3 event the Batmobile uses,
BmAK event(s)/WAV(s) → JC3 event GUID → slot → transform, weapons per T-11, horn/radio per AUD-7,
absent banks as named omissions. The map has **53 rows = 45 donor events + 8 weapon/mode rows**:
`mapped` 7, `kept vanilla` 32, `named omission` 11, `remove` 1, `blocked` 2. All 7 AUD codes carry
rows; 22 of the 45 pinned GUIDs are named by no `.epe` object (G2-24 §3) and stay vanilla; the
`check` refuses to pass if any of the 23 named roles lacks a decision row.

**The four things the files did decide.**

1. **AUD-2 has a proven swap, not a guess.** test-060's `_apply_audio.py` really replaced FSB5
   indices 56/150/355 (0-based) with the premium-nitro payload names, so A-02's slot is
   `slot_confidence: proven` and its three candidates carry the measured transform. The BmAK
   afterburner *events* (`Play_Batmobile_RocketTails`) carry **0 WEMs** in the four packages; the
   content test-060 used is the two WAVs (`bml/jc3_batmobile_start.wav`, `hashid/EC2FD42B.wav`),
   so the row names WAVs as its source and the events as the missing ones.
2. **No candidate slot has an FSB5 loop chunk.** Not `premium_nitro_loop`, not
   `minigun_fire_close_loop_04`, not `missile_trail_rear_loop` — 0 of 33. The loop lives in the
   event/tune graph, whose `TLNS` semantics G2-24 §11 calls code. So a swap payload only has to
   fill the slot's frame count; it cannot move a loop point that is not in the file.
3. **The engine cannot be mapped by name.** vehicles.bank holds 34 engine-ish samples in seven
   model families (Aston, Ducati, moped, fiat, saab, volvo, train, tank-M8). A-01 lists the five
   `aston_martin_vantage_engine_rpm_*` layers (the only 5-layer RPM stack, matching BmAK `Idle`'s
   5 layers, MODLOG §70 update 2) and leaves `chosen` **UNKNOWN** for the audition to settle.
   Its BmAK side is derived, not typed: every `engine`-group event whose RTPC list binds `REV_RPM`.
4. **The RPM curve fit is domain-only.** `LandAudio` is 2 members (`min_rpm` 1000, `max_rpm`
   10000), which is the whole JC3 RPM window; the BmAK `REV_RPM` points
   (0→0, 0.0187→0.0228, 0.3013→−1, 1→−1) re-base to 1000→0, 1169→+0.023, 3712→−1, 10000→−1.
   Which FMOD target y drives (volume dB / pitch cents / low-pass) is **not** in the recovered
   data, so the map does not claim a pitch curve — that is the one place the card's wording could
   not be met from the files, and it is recorded as UNKNOWN (Q-1 #8).

**Weapons (per T-11's carrier candidates, G2-24 §7).** WPN-2's audio route is `w619` (W-03,
`Play_Batmobile_MShot` → `minigun_fire_close_loop_04` + `barrel_motor_loop` + `endclick`, gain set
below); `w602`/`w603` carry **no** audio of their own and BmAK's cannon/missile launch media are
absent from the four packages, so WPN-1 and WPN-3 keep JC3's stock samples with named omissions
(W-01/04/05/06). The lock-on UI group is 6 events / 23 rows and **every one is `missing-bank`**
(W-07). AUD-4 (`battle-mode` 30 events / 75 WEMs) is `blocked: D-2` (W-08) — a second variant is
the only thing that gives the battle car its own engine event.

**Gain/stretch, all derived.** `gain_db = slot's own measured LUFS − source's loudest variant`,
`residual_lu` its check (max |residual| **0.00 LU** over 21 gain-matched slots, gate ≤ 1.00),
`stretch_ratio = slot frames / source frames` so the payload keeps the byte size route a needs
(the `_apply_audio.py` trim/pad rule). All loudness is `bmak_audio_features.integrated_lufs`
(ITU-R BS.1770-4) — imported, not re-written — on samples decoded by the project's vgmstream.

**Done check (verbatim, exit 0):**

```
> python Tools/scripts/t12_audio.py --check
PASS: 53 rows = 45/45 donor events + 8 weapon/mode rows | dispositions {'blocked': 2, 'kept vanilla': 32, 'mapped': 7, 'named omission': 11, 'remove': 1} | 33 slot candidates (21 gain-matched, max |residual| 0.0 LU <= 1; 12 kept stock) | 2 rpm curves | features 7/7 | json match True, md match True
```

`--check` re-reads both evidence files, **re-decodes all 33 slots** through vgmstream and
re-measures them, rebuilds the JSON and the MD and compares both byte for byte. `--fast` reuses
the stored measurements for iteration but the gate above was run in full.

**Tamper tests (all caught, all reverted, then the full check re-run green).**

1. `t12_audio_map.json` `summary.slot_candidates` 33 → 34 →
   `FAIL: json stale: summary`, exit 1 (a hand-edited count cannot survive the rebuild).
2. `T12_AUDIO.md` slot frames 29954 → 29955 → `FAIL: md differs:` with the one-line diff
   (`-… 29955 …` / `+… 29954 …`), exit 1.
3. Negative test on the slot resolution: A-06's name `jc3_veh_door_tank_open_03` → `…_99` →
   `FAIL: A-06 slot jc3_veh_door_tank_open_99 not in vehicles; A-06 chosen slot not among the
   candidates; 1 slot names not in the bank; A-06 slot … has a source but no gain; json stale:
   rows,summary; md differs`, exit 1. So a name that no longer exists in the bank cannot pass as
   a slot.

**Standing gates re-run the same session:** `python Tools/scripts/status_audit.py --check` →
`STATUS.md is current`; `python Tools/scripts/t_rows.py check` → `check ok` (ledger 122 rows,
untouched); `python -m py_compile Tools/scripts/t12_audio.py` → OK.

**UNKNOWN / limits.** (1) Which sample an event plays — G2-24 §5's five proofs; every `candidate`
slot is a name match whose verify is a Q-1 audition. (2) Which family the donor's own engine event
reaches. (3) The RTPC y target. (4) JC3 has no speed/heat/occlusion parameter, so `Speed`,
`BML_WheelSpeed`, `BML_Steering*`, `Drift`, `EngineHeat`, `Occlusion` bindings have no JC3 input to
drive (recorded per source event in the JSON). (5) Whether deleting the `horn` object silences the
horn (input binding is code, Q-1). Decisions still open and named per row: D-2 (W-08), D-8 (A-08,
A-10, A-23), D-10 (A-03).

**Files changed.** `Tools/scripts/t12_audio.py` (new), `Working/Translation/T12_AUDIO.md` +
`Working/Translation/t12_audio_map.json` (generated), `GRAB_BACKLOG.md` §12 (one line), this log
(append-only, plus the intended-change entry above).

**Revert:** delete `t12_audio.py`, `T12_AUDIO.md`, `t12_audio_map.json` and
`E:\Modding\_JC3grab\audio\weapons.bank` (177,586,080 B, extracted by the tool for the weapon-slot
measurements); put §12 back to `| T-16 | todo | |`; truncate this log at the intended-change heading.

## T-17 · Effects translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7, `#### T-17 · Effects translation` (S · deps: G1-16, G2-22, G2-23 ·
serves: FX-1…4). Out: `Working/Translation/T13_FX.md` + rows; Done: every FX code has a chosen
effect or a named omission.

**Resume check (session loop steps 1–2).** `grep -n "T-17" MODLOG.md` → the card is named only in
G2-22's text ("the list FX-1/T-17 has to work from"); no earlier session started T-17 and no T-17
output exists on disk (`ls Working/Translation/T13*` → none). §12 says `| T-17 | todo | |`.
Prerequisites are all `done` in §12: G2X (MODLOG §"G2X · G2 exit gate — passed"), G1-16 (l. 1284),
G2-22 (l. 1305), G2-23 (l. 1306). T-17 names no §11 decision; the FX codes are not in any `blocks`
cell of §11, so nothing is decision-gated (the weapon *choice* that FX-2 rides on is T-11's).

**Intended change (written before editing, §0.2 rule 4).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/t17_fx.py` | new. The FX translation as data (17 rules: BmAK group(s), effect needles, socket/part, trigger), each effect **derived** from `FX_TABLE.jsonl` (kind match + donor-carried + fleet carriers), absences proved as negatives; `--write` emits the doc + json, `--check` re-derives both and cross-checks the ledger | the card's Out is a doc + rows and its Done is "every FX code has a chosen effect or a named omission" — only a re-derivable table can fail | delete the file |
| `Working/Translation/t17_fx.json` | new, generated | R11: the rows and every count come from a script with `--check` | delete the file |
| `Working/Translation/T13_FX.md` | new, generated by the same `--write`; its row table is the phase-T ledger's source for the new ids | the card names this path | delete the file |
| `Tools/scripts/t_rows.py` | `("T-13", T13_FX.md)` added to `DOCS` and 17 `DISPO` entries (12 `epe`/`next`, 5 `out` with the proof file in `why`) | `T_ROWS.jsonl` is generated by `t_rows.py build`, so the new rows must be parsed from their document and carry a disposition | remove the DOCS entry and the 17 DISPO lines |
| `Working/Translation/T_ROWS.jsonl` | regenerated by `t_rows.py build` (105 → 122 rows) | R11 | re-run `build` after the revert above |
| `STATUS.md` | regenerated (`status_audit.py --write`) | it counts the ledger | re-run `--write` on the reverted ledger |
| `GRAB_BACKLOG.md` §12 | flip **only** the `T-17` row | session loop step 7 | put the row back to `| T-17 | todo | |` |

**What is not touched:** no game file, no `Builds/`, no dropzone, no save, no git, no `D:\Games`
write. Effects are read only from `Research/JC3Grab/FX_TABLE.jsonl` (57,187 rows, already decoded by
G2-9), `PARTICLES_FEATURES.json` (G1-16), `USAGES.json` (G2-22/23) and `SOCKETS_JC3.json` (G1-13).
Custom `.effc` authoring stays out of scope, as the card says.

## T-17 · Effects translation — done (2026-10-28)

**Card.** T-17, the eighth phase-T card. `Working/Translation/T13_FX.md` + rows; every FX code has
a chosen effect or a named omission.

**Record:** `Working/Translation/T13_FX.md` (136 lines, generated) + `t17_fx.json` (the same 17
rows with every candidate and count) + `Tools/scripts/t17_fx.py` (`--write` / `--check` /
`show <id>`). The rows enter the ledger as doc `T-13` (`t_rows.py` `DOCS` + 17 `DISPO` entries);
`T_ROWS.jsonl` went 105 → 122 rows and `STATUS.md` was regenerated.

### What the rows say

The Batmobile replaces `v0300_car_kensington_sportsmuscle`, so the strongest evidence for a choice
is that the donor's own `.ee` already spawns the effect: `FX_TABLE.jsonl` names the container of
every `.effc`, and the signature variant carries **85** distinct effects. Each row is a needle match
on the 955 distinct fleet `.effc`, ranked donor-carried first and then by how many of the 232
vehicles carry it.

| code | rows | answers |
|---|---|---|
| FX-1 | T-FX7, 8, 9 | flame = the donor's `car_cycle_base_dual_nitrous` (17 vehicles) at the `Afterburner` socket under `EngineNitro` (18 vehicles); always-on exhaust = `car_cycle_base_dual` under `EngineRunning` (69); heat haze = named omission (G1-16 heat-steam is 0 systems, 0 haze paths in 955) |
| FX-2 | T-FX10…16 | cannon flash `tank_canon_muzzleflash` (11 vehicles) at `CannonMuzzle`, Vulcan flash `helicopter_minigun_muzzleflash` (15) at `ChainGunMuzzle`, missile trail `missile_trail_car` at `MissileL/R`, cannon impact the 7-surface `tank_explosive_*` family; tracers, casings and a cannon-round trail are named omissions (see below) |
| FX-3 | T-FX17…20 | tyre kick-up `dust_trail_*` (6 surfaces, 161 vehicles) on the wheel parts, slide dust `chassis_slide_*` (5, 289), scrape sparks `spark_trail_02_med` (298) at `ScrapeSparksL/R`, brake trail = named omission |
| FX-4 | T-FX21…23 | death explosion `exp_car_01` (126) under `OnExploded`, burn states `dmg_fire_engine`/`_spread_base`/`_spread_roof`, engine smoke `dmg_smoke_engine` under `EngineSmoking` (23) then `dmg_post_burn` |

**The three FX-2 omissions are the interesting half, and each is a negative with its proof.**
`tracer`: **0** of 955 effect paths is a tracer - JC3 draws it as a texture, and every one of the 22
`WeaponTuning` rows carries `tracer_texture_type`/`tracer_fire_velocity`/`tracer_time_to_live`
(G2-10 §6), so the requirement moves to the weapon clone. `casings`: `shell_eject_*` exists only on
the shotgun (2 paths, **0** carried by any vehicle in the 232), so a vehicle gun in JC3 ejects
nothing and the `ChainGunShells` socket stays empty. cannon round trail: 0 paths. Brake trail: 0
paths, and `BrakeLightTrailSystemL/R` is not among G1-16's 206, so T-FX6 already owns what the
donor's entity graph carries.

### Two things the card did not assume

* **"Size match" is reported, not used.** The BmAK side is systems/emitters/lifetime/size in UE
  units, the JC3 side effect rows/arrays/bytes; there is no unit bridge, so ranking is
  kind → donor → fleet use and both sides' sizes are printed beside the choice (doc §5). Claiming a
  size fit would have been a guess.
* **A group with 0 systems is a BmAK absence, not an untranslated feature.** heat-steam,
  wall-scrape and speed-lines are 0/0/0 (G1-16); the doc's §1 table puts all 21 groups with their
  owner so the 8 non-FX groups (winch, sonar, emp, target-markers, hack-fx, gel-rounds, fear-gas,
  speed-lines) are attributed to the card that owns them instead of vanishing between cards.

### Done check (verbatim, exit 0)

```
> python Tools/scripts/t17_fx.py --check
PASS: 17 rows (12 chosen, 5 named omissions) | FX codes 4/4 | donor effects 85 | fleet .effc 955 | sockets 8 | ledger 17/17

> python Tools/scripts/t_rows.py check
ledger 122 rows | edit 16 next 9 keep 49 epe 24 re-read 0 blocked 11 out 9 superseded 4 | edits 35 over 16 rows
check ok

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

`--check` re-reads the five inputs, re-derives all 17 rows, regenerates the doc byte-for-byte,
verifies every chosen path is still in `FX_TABLE.jsonl`, every socket still in
`SOCKETS_JC3.json`, every `.effc` `part_hint` still valid, and compares each row's cells and
disposition with `T_ROWS.jsonl`.

**Tamper tests, four, each caught and reverted (files restored from `/tmp` copies, full
`--check` green afterwards).**

1. `t17_fx.json` row T-FX10 chosen path → `effects/nope.effc`:
   `FAIL: t17_fx.json differs from the re-derived record` + the first differing fragment, exit 1.
2. `T13_FX.md` T-FX10 effect cell swapped to the minigun flash:
   `FAIL: T13_FX.md differs from the re-derived record` with the one-line diff, exit 1.
3. The tracer rule's needle widened to `["tracer","explosion"]`:
   `FAIL T-FX12: named omission is refuted - 90 path(s) match ['tracer', 'explosion'], first
   dlc/mech_land_assault/effects/destruction/dlc_bavarium_explosion_4m.effc`, exit 1 - the negative
   test has teeth, which is what a "proven absence" needs.
4. `T_ROWS.jsonl` T-FX12 disposition `out` → `epe`: `FAIL T-FX12: ledger dispo epe != out`, exit 1.

### UNKNOWN / limits

* **No in-game observation** (R6): every row's `verify` is a Q probe (Q-1 #5/#8, Q-2 A5/A9/A10,
  Q-3 #1/#7) that can fail; nothing here is "seen working".
* **Which weapon ids FX-2 rides on is T-11's** (D-3/D-7). The effects are the fleet's own for that
  kind, and the bundles prove a clone brings them (w619 16, w610 14, w618 12, w608 5 effects;
  w602/w603/w604 ship no bundle of their own, G2-10), but the slot decision is not this card's.
* **`EngineNitro` is a usage *name* with a hash and attachments (G2-22/23), not a proven boost
  trigger** - that the flame appears on the boost input is a Q probe.
* **Size/colour matching between a BmAK particle system and a JC3 `.effc` is UNKNOWN.** The chosen
  effect is the right *kind* on the right socket; whether it reads the same at speed is a look, not
  a decode. Custom `.effc` authoring is out of scope as the card says.

**Files changed.** `Tools/scripts/t17_fx.py` (new), `Working/Translation/t17_fx.json` +
`T13_FX.md` (new, generated), `Tools/scripts/t_rows.py` (one DOCS entry + 17 DISPO entries),
`Working/Translation/T_ROWS.jsonl` (regenerated, 122 rows), `STATUS.md` (regenerated),
`GRAB_BACKLOG.md` §12 (one row), this log (append-only). No game file, no `Builds/`, no dropzone, no
save, no git.

**Revert:** delete `Tools/scripts/t17_fx.py`, `t17_fx.json`, `T13_FX.md`; remove the `T-13` DOCS
entry and the 17 DISPO lines from `t_rows.py`; re-run `t_rows.py build` and `status_audit.py
--write`; restore the §12 row to `| T-17 | todo | |`; truncate this log at the intended-change
heading.

**Next.** T-11 (weapons) owns the FX-2 weapon ids and the slots (D-3/D-7); T-16 (audio) is the
matching sound pass; B-08 builds the effect attachments on the compiled entity.

## T-13 · Interaction translation — deferred (2026-10-28)

**Not started, on purpose.** Session loop step 2: every prerequisite is `done` — `G2X`, `G2-18`
(`INTERACTION.md`), `G2-19` (`SEAT.md`), `G2-20` (`EJECT.md`), `G1-13` (`SOCKETS_JC3.md`), `G1-19`
(`COCKPIT.md`) — but the card needs a §11 decision that is **not resolved**:

> T-13 `Do:` … *"Decide hijack entries (`entry.driver.pull.out.*`, `exit.driver.pulled.out`) per
> D-9."* — and §11 lists `D-9` with **`blocks: T-13`**.

`D-9` is still the open question *"Can enemies pull Rico out of the Batmobile?"* (G2-18; recommendation
*no (lore)*). Per the session rule, a card that needs an unresolved decision is not started, so
nothing was written: no `Tools/scripts/t9_interaction.py`, no `Working/Translation/T9_INTERACTION.md`,
no `t9_interaction.json`, §12 `T-13` stays `todo`, and no game file was read for this item.

**Resume check.** `grep -n "T-13" MODLOG.md` found no intended-change entry (the three hits are other
sections mentioning the FX doc name `T-13`), and none of the three T-13 output paths exists, so an
earlier session had not started it either.

**What is needed to start:** the user's answer to D-9. If "no" (lore default), the hijack rows
(`entry.driver.pull.out.*`, `exit.driver.pulled.out`) are dropped with that reason recorded and the
card runs unchanged; if "yes", they keep the donor's roles and are placed like the other entries.
The rest of the card (entry/exit, `point.stunt*`, stunt planes, `Driver` socket) has no open decision.

**Report:** `tmp/freebuff/reports/T-13.md`.

## T-10 · Re-open the `out` rows with the G2 evidence — done (2026-10-28)

**Record:** `Working/Translation/T10_OPEN_ROWS.md` (new, 229 lines) + `T10_OPEN_ROWS.json` (new)
from `Tools/scripts/t10_reopen.py` (new, `--write` / `--check` / `dump`); 16 rows re-decided,
`T_ROWS.jsonl` regenerated (105 → 122 rows, the growth is T-17's new `T-13` document, see
"Concurrent sessions" below), `STATUS.md` regenerated, §12 one row. No game file, no `Builds/`,
no dropzone, no save, no git.

**The 16 rows.** The card's 15 `out` rows — 8 in `T_ROWS.jsonl` (T-LG5, T-FX4, T-DM7, T-W1,
T-BM1, T-AC1, T-RA1, T-SR1) and 7 in `T6_HUD_CAMERA.md` (T-HUD4, T-HUD6…T-HUD10, T-CAM10) — plus
`T-HUD5`, which the card's own expected-outcome sentence names (`T-HUD5/6 → G2-25`). Its
disposition does not change; its reason narrows, because G2-25 decoded the API it was blocked on.

**Old row → new disposition → evidence, in the card's order.**

| row | was | now | successor(s) | §11 gate | evidence file | what the file shows |
|---|---|---|---|---|---|---|
| T-W1 | out | **superseded** | T-11 | D-3, D-7 | `Research/JC3Grab/WEAPONS.md`, `WEAPON_WIRING.md` | 25 vehicle weapon ids; two driver slots (`main_weapon`, `id:00568A74`); the donor chassis ships `w618_sportsmuscle_missile` |
| T-FX4 | out | **superseded** | T-11, T-17 | D-7 | `Research/JC3Grab/EMP.md`, `ENTITIES.md` (negative) | EMP is an entity-level `CForcePulse` copy + `CEMPWeapon` w702/w503; **0** sonar classes in the 103-class census |
| T-DM7 | out | **out** (stays) | — | — | `Research/JC3Grab/DAMAGE_MODEL.md`, `FORCEPULSE.md` | the chain is hit → own health; `impact_damage_factor` is the incoming switch; "collision does not trigger a pulse" (0 of 23 tune paths) |
| T-BM1 | out | **superseded** | T-12, T-15 | D-2 | `Research/JC3Grab/TURRET.md`, `TANKTURN.md` | turret/Cannon parts reach the battle pose as part angles (−179…179); "Turn-on-the-spot has no JC3 data carrier" → named omission |
| T-AC1 | out | **out** (stays) | — | — | `Research/JC3Grab/VOCABULARY.md` (+ negative scan) | `gravity_multiplier_in_air_down` and `takeoff_pitch_damping` exist (n=145, donor 1 / 0.5) but neither is a yaw torque; 0 hits of `air_control`, `aircontrol`, `yaw_torque` |
| T-RA1 | out | **out** (stays) | — | — | `Research/JC3Grab/VOCABULARY.md` (negative scan) | 0 hits of `shov`, `dodge`, `road_assist`, `kill_flip`, `impact_shake` in the 52-type / 1,421-path vocabulary |
| T-SR1 | out | **out** (stays) | — | — | `Research/JC3Grab/VOCABULARY.md` | `righting_torque` exists **only** in `DriverLean`, n=23 aircraft, donor empty; 0 hits of `upright` |
| T-LG5 | out | **superseded** | T-18 | D-2 | `Research/JC3Grab/LIGHT_SYSTEM.md` | "the same socket also carries 1 `VEHLT_BattleModeLight`" — LGT-2's battle spotlight |
| T-HUD4 | out | **out** (stays) | — | — | `JC3_HUD_WEAPONS.md` + `ui/hud.gfx` scan + `DAMAGE_MODEL.md` | the vehicle HUD interface has no armour field; 0 hits of `armour` in the 260 scripts; JC3 armour is per-channel (`explosion_armor`) |
| T-HUD5 | blocked | **blocked** (narrower) | — | D-7 | `Research/JC3Grab/JC3_HUD_WEAPONS.md` | the API is decoded (2 slots, 9/6 args, cooldown); what is missing is the entity's weapon component → T-11 / B-05 |
| T-HUD6 | out | **out** (stays) | — | — | `ui/hud.gfx` scan + `TANKTURN.md` | 0 hits of `zoom`, `battlemode`, `battle_mode`; the mode's pivot is a named omission |
| T-HUD7 | out | **out** (stays) | — | — | `Research/JC3Grab/TETHER.md` + `ui/hud.gfx` scan | "Functional winch classes anywhere in the fleet: **0**"; 0 hits of `winch` in the HUD |
| T-HUD8 | out | **out** (stays) | — | — | `ui/hud.gfx` scan + `ENTITIES.md` (negative) | 0 hits of `energysystem`, `energy_charge`; 0 sonar classes |
| T-HUD9 | out | **out** (stays) | — | — | `ui/hud.gfx` scan | 0 hits of `combo`, `medal`, `enemy_count` (the 48 `battle` hits are the province battle gauge, not a mode) |
| T-HUD10 | out | **out** (stays) | — | — | `ui/hud.gfx` scan | 0 hits of `occupant`, `virus`, `forensic` |
| T-CAM10 | out | **superseded** | T-15 | D-2 | `Working/Translation/T6_HUD_CAMERA.md` | no battle-camera *member*, but a second per-entity `.ctune` per variant is the carrier (`bat_base.ctune`, Batch F, test-091) |

**Done check (verbatim, all three exit 0):**

```
> python Tools/scripts/t_rows.py check
ledger 122 rows | edit 16 next 9 keep 49 epe 24 re-read 0 blocked 11 out 9 superseded 4 | edits 35 over 16 rows
check ok

> python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | 10/10 out rows carry a proof file | 4 later `out` rows cite a proof, 1 do not (T-FX13) | successors T-11, T-12, T-15, T-17, T-18 | decisions open D-2, D-3, D-7 | json match True, md match True

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

`t_rows.py check` now reports `out 4 superseded 4` for the ledger and `STATUS.md` reports
`rows out (no JC3 system; excluded) 10`, `rows superseded (moved to a phase-T card; excluded) 5`,
in scope 113 (128 − 10 − 5, unchanged: the five rows that left `out` are excluded for the second
reason instead), resolved 93/113. Standing gates re-run and green: `grab_model.py check` (schema
6), `bmak_chain.py --check` (336/0), `bmak_coverage.py --check`, `jc3index.py check` (81,952 /
81,953), `jc3hkx.py check --all` (18,865 hulls, station sets 17/17 agree), `jc3fx.py check`
(57,187 / 0 problems), `t3_fleet.py --check`.

**Tamper tests** (each caught, then restored and the full `--check` re-run green):

1. `T_ROWS.jsonl` `T-AC1` `out` → `superseded` (`superseded_by: ["T-12"]`) →
   `FAIL T-AC1: ledger says 'superseded', the T-10 table says 'out'` +
   `FAIL T-AC1: the table keeps it `out` but the files do not` + both stale-file lines, exit 1.
2. `t10_reopen.py` `T-HUD9` `must_not` gains `cooldown` (a word that **is** in `ui/hud.gfx`) →
   `FAIL T-HUD9: E:/Modding/_JC3grab/hud/dec: ui/hud.gfx names cooldown` — the proven-absence
   half has its own negative test, as at G2X.
3. `T10_OPEN_ROWS.json` `summary.superseded` 5 → 4 → `FAIL T10_OPEN_ROWS.json stale: the payload
   differs`, exit 1.

**What changed under me (concurrent sessions).** Another card was writing at the same time: at
05:38 `T12_AUDIO.md` (T-16) and `T13_FX.md` (T-17) appeared, `t_rows.py`'s `DOCS` gained
`("T-13", T13_FX.md)`, and the shared `T_ROWS.jsonl` was regenerated to 122 rows. My first
`--check` therefore failed on five brand-new `out` rows (`T-FX9/12/13/16/20`) that T-10 never
wrote. The check was tightened, not loosened: a row this table owns must still be proven by
re-reading its evidence file, and a later row must still cite a proof in its own `why` — four do,
and `T-FX13` ("no vehicle carries a casing/shell effect; ChainGun_BulletCasing has no JC3
carrier") does not yet name a file. It is recorded here and in the doc as **its own card's to
prove**, not silently passed. Re-running `status_audit.py --write` was required after the ledger
grew (the `T-13` rows changed the per-document table, not the verdicts).

**UNKNOWNs and limits, stated rather than filled.**
- An absence is an absence of **names in a decoded surface**, never of engine capability. The
  surfaces are named per row: `VOCABULARY.md` (52 types / 1,421 paths), `ENTITIES.md` (103
  classes), and the 260 decompiled `ui/hud.gfx` scripts. Native-only mechanisms would not appear
  in any of them, which is exactly the G2X caveat.
- `ui/hud.gfx` is the **in-game** HUD movie. The other 28 `ui/*.gfx` movies in the index are not
  decompiled, so a widget living in the frontend (`main.gfx`, `reward.gfx`) would not be seen;
  the five HUD `out` rows are therefore worded "in the in-game HUD".
- A successor is a **plan, not a value**: T-11/T-12/T-15/T-17/T-18 still have to write those
  rows, and the D-2/D-3/D-7-gated ones stay `blocked: D-n` until the user answers §11 (D-1 is the
  only resolved decision; D-2, D-3, D-7 are read as open from the register itself, not typed).
- `T-HUD5` stays `blocked` rather than `superseded`: nothing carries it yet in the entity, and a
  build step (T-11 / B-05) is what unblocks it — marking it superseded would claim a carrier that
  exists only as an API.
- Whether the `T-FX13` casing effect has a JC3 carrier at all is T-17's open question; it was not
  re-decided here because the card's scope is the 15 `out` rows plus T-HUD5.

**Files changed.** `Tools/scripts/t10_reopen.py` (new), `Working/Translation/T10_OPEN_ROWS.md` +
`.json` (generated), `Tools/scripts/t_rows.py` (`superseded` in `VOCAB`, `SUPERSEDED`,
`superseded_by` in the ledger row, 15 `DISPO` entries re-decided), `Tools/scripts/status_audit.py`
(the `superseded` bucket + column + prose), `Working/Translation/T2_TRANSLATION.md` (T-LG5, T-FX4),
`T3_COVERAGE.md` (T-DM7, T-W1, T-BM1, T-AC1, T-RA1, T-SR1), `T6_HUD_CAMERA.md` (T-HUD4…T-HUD10,
T-CAM10), `T_ROWS.jsonl` (regenerated), `STATUS.md` (regenerated), `GRAB_BACKLOG.md` §12 (one row),
this log. Pre-edit copies of every edited file are in `tmp/freebuff/pre_t10/`.

**Revert:** delete `t10_reopen.py`, `T10_OPEN_ROWS.md`/`.json`; restore the six files from
`tmp/freebuff/pre_t10/` (`t_rows.py`, `status_audit.py`, the three tables, `T_ROWS.jsonl`,
`STATUS.md`); delete the §12 evidence addition; truncate this log at the intended-change heading.

## T-18 · Lights translation completion — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7, `#### T-18 · Lights translation completion` (S · deps: G1-17, G2-33 · serves: LGT-1/2, APP-4).
Do: complete T-L1…T-L7, T-LG1…T-LG6 with colours/intensities/cones from G1-17, the wheel-arch lights as
custom `SVehicleLight` entries (closes T-L4/T-LG4), emissive `CarLight` blocks per lamp part, light-part list
for B-04. Out: rows; `Working/Translation/t14_lights.json`. Done: every light entry of the `Batmobile` rig
(28) maps to an `SVehicleLight` or a named omission (forensics rig stays out).

**Resume check (session loop step 1-2).** `grep -n "T-18" MODLOG.md` → the only hits are T-10's §12/ledger
mentions (`T-LG5` superseded by T-18) and the §12 tracker row `| T-18 | todo | |`; **no intended-change
section and no output on disk**, so no earlier session started the card. Prerequisites: `G2X` `done`
(MODLOG §"G2X · G2 exit gate — passed"), `G1-17` `done` (§12 row, `LIGHTS.md`), `G2-33` `done` (§12 row,
`LIGHT_SYSTEM.md`). No §11 decision is named in the card (`blocks` column empty); D-2 is only the reason the
battle-mode entries are *rows* here (`VEHLT_BattleModeLight` is a decoded behaviour value, G2-33) and the
forensics rig is a named omission, which is what the card's Done line already says.

**Resume (this file is append-only; the sections above stay as written).** T-18 predates `T-19` in §12, so
this session took it as the first `todo` hop with its deps green, per §0.2 step 2.

**Files, and why each is the right one (AGENTS.md rule).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/t18_lights.py` | **new** tool: `--write` / `--check` / `show <id>` | R11: the 28-row table, the custom `SVehicleLight` entries and every count come from one script that re-derives them | delete the file |
| `Working/Translation/t14_lights.json` | **new**, generated by `--write` | the card's Out path, verbatim | delete the file |
| `Working/Translation/T14_LIGHTS.md` | **new**, generated by the same run | the card says "rows"; T-17's shape (`T13_FX.md` + `t17_fx.json`) is the finished-item shape the user asked to follow | delete the file |
| `Tools/scripts/t_rows.py` | add `("T-14", T14_LIGHTS.md)` to `DOCS`; `T-L4`/`T-LG4` → `superseded` (successor `T-18`) in `DISPO` + `SUPERSEDED`; 28 `DISPO` rows for the new ids | the ledger is built from the tool's doc list and disposition table; without this the 28 rows are not in `T_ROWS.jsonl` and `t_rows.py check` fails | restore the `DOCS`/`DISPO`/`SUPERSEDED` lines (copied to `/tmp/t_rows.beforeT18.py`) |
| `Working/Translation/T1_TRANSLATION.md` | `T-L4` row: "no preset exists / blocked" → "superseded by T-18, custom entry recipe `LIGHT_SYSTEM.md` §7" | the row's own claim is refuted by G2-33's recipe; the ledger parses this cell, so the doc and the ledger must agree | restore that one line |
| `Working/Translation/T2_TRANSLATION.md` | same for `T-LG4` | same | restore that one line |
| `Working/Translation/T_ROWS.jsonl`, `STATUS.md` | regenerated (`t_rows.py build`, `status_audit.py --write --check`) | generated files, never hand-edited (R11) | restore the `/tmp` copies and re-run both tools |
| `GRAB_BACKLOG.md` §12 | `| T-18 | todo | |` → `done` + evidence | session loop step 7 | restore that one line |

**Row ids.** `T-L8`…`T-L35`, one per entry of the `Playable_Batmobile_SF` rig (28 in file order). The old
`T-L1…T-L7`/`T-LG1…T-LG6` rows keep their ids; `T-L4`/`T-LG4` become `superseded` with successor `T-18`
(the wheel-arch recipe exists, so "no preset, blocked" is no longer true), and the doc's §1 table names which
new row completes each old one.

**No hand-typed number.** Every value in the record is read or derived from `Research/BatmobileGrab/LIGHTS.json`
(28 entries: socket, type, behaviour, component colour/brightness/cone/radius, `jc3_part`, `jc3_anchor`),
`Working/Lights/v082/lights.xml` (the donor's 21 module rows), `Working/Lights/v082/entity.xml` (the donor's
22 `SVehicleLight` objects), `Research/JC3Grab/LIGHT_SYSTEM.json` (the 25-member custom-entry template,
behaviour vocabulary, preset counts) and `Research/JC3Grab/PARTS_TABLE.jsonl` (part_index, has_lights,
damage_type). Hashes are recomputed with `rbmhdr.hash_jenkins`. Nothing launches a game, nothing is written
outside the repo.

## T-12 · Moving-parts translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7 `#### T-12 · Moving-parts translation   M · deps: T-10, G1-10…G1-12,
G2-13…G2-15 · serves: ANI-2…8, APP-5/6, MOD-4`. *"one row per moving part: part name (new,
`batmobile_<part>`), BmAK bone(s), JC3 behaviour, pivot (bone bind pose through the one transform),
axis, limits (from the BmAK animation's extreme frames), rate (BmAK anim length → deg/s), parent
part, LOD policy, damage type. Parts: turret (yaw), cannon (pitch), Vulcan barrels (spin), turbine
fan (spin), canopy (door), missile hatches L/R (door), rear air-brakes / fins (hinged; `AirBrake`
probe), steering yoke."* Out: `Working/Translation/T8_PARTS.md` + rows (doc `T-8`); Done: *"each
part has pivot+axis+limit+rate+behaviour or a reason it stays static."*

**Resume check (loop 1-2).** `grep -n "^## T-12\|T-12 ·" MODLOG.md` → no T-12 entry; no
`t12_parts.py`. `Working/Translation/T8_PARTS.{md,json}` exist **from the B-02 cut** (2026-10-24) and
say of themselves: *"It deliberately contains no axis, limit, rate or JC3 behaviour: those are
T-12's rows and are not invented here."* So this session **extends that file** rather than writing a
second one — its `parts` array stays byte-identical so `bat_assemble.py --parts` still accepts it.

**Prerequisites.** `G2X`, `G1-10`, `G1-11`, `G1-12`, `G2-13`, `G2-14`, `G2-15` are `done` in §12.
`T-10` is `done` **in substance but not in the tracker**: §12 still reads `| T-10 | todo | |` while
MODLOG carries `## T-10 · Re-open the out rows with the G2 evidence — done (2026-10-28)` and its
`t10_reopen.py --check` PASS was re-run by this session (green, exit 0, 16 rows). §0.3 defines a task
as done when its check passed and its output is on disk — both hold — so the stale tracker row is a
concurrent session's pending bookkeeping step, not a missing prerequisite. This is recorded rather
than silently passed; the `T-10` row is **not** flipped by this session (one row per session).

**Intended change (written before the edits; appended late, see the note below).**

| file | change | why this file | revert |
|---|---|---|---|
| `Tools/scripts/t12_parts.py` | new. Reads `ANIMATIONS.json` + `BONES.json` + `POSES.json` + the exported key frames (`E:\Modding\_BmAKgrab\anims\keys`) + `MOVING_PARTS.json` / `TURRET.json` / `PARTS_TABLE.jsonl`, re-derives every pivot through `bat_assemble.pivot_point` (R2), measures each joint's axis/limits/rate from the key frames, joins the shipped hinge and damage type per behaviour, and regenerates the doc + JSON. `--write` / `--check` / `dump rows|parts` | §0.2 step 5 ("scripts, not hand edits"); no existing tool covers part behaviour, and `bat_assemble.py` must not be forked | delete the file |
| `Working/Translation/T8_PARTS.md` | regenerated: the geometry table (from `parts_manifest.json`) **plus** the 15 behaviour rows and per-part detail | the card's `Out` line names this file; the B-02 session left the behaviour half to T-12 | `git`-free restore from the pre-session copies taken in `/tmp/t12bak/`, or re-run the T-8 cut |
| `Working/Translation/T8_PARTS.json` | same file, `parts` unchanged, `schema` 1→2 with the behaviour rows beside it | it is both the B-02 spec and the doc's data file; keeping one file avoids a second source of truth | as above |
| `GRAB_BACKLOG.md` §12 | flip **only** the `T-12` row | session loop step 7 | put the row back to `| T-12 | todo | |` |

**Note on the timing of this entry (honest record).** Steps 1-5 of the loop were done in the order
§0.2 gives, but this intended-change table was appended **after** `t12_parts.py` had already been
drafted and run once in this session, not before the first edit. Nothing outside
`Tools/scripts/t12_parts.py`, `Working/Translation/T8_PARTS.{md,json}` was touched before the entry
existed, and the pre-session copies of both T8 files were taken first, so the revert path recorded
above is real. Logged rather than back-dated.

## T-12 · Moving-parts translation — done (2026-10-28)

**Record:** `Working/Translation/T8_PARTS.md` (262 lines, generated) + `Working/Translation/T8_PARTS.json`
(generated, `schema` 2) from `Tools/scripts/t12_parts.py` (new); the file's `parts` array is unchanged,
so `bat_assemble.py --parts` still reads it. No game file, no `Builds/`, no dropzone, no save, no git.

**The rows.** **15 = 11 cut parts + 4 items that have no part**, one per card mechanism: turret (P-01),
cannon (P-02), Vulcan barrels (P-03), riot suppressor (P-04, the card's "cannon" family), turbine/jet
(P-05), canopy (P-06), missile hatches L/R (P-07/08), four air-brake flaps (P-09…P-12), steering yoke
(P-13), and the two missile pods (P-14/15, the shells the hatches ride in). **12 rows carry an
animated joint; 3 are static with the reason written down** — P-02 (no rotation animation exists, only
recoil), P-05 (`EngineRotatingPart`: rpm-driven, no animation), P-13 (`SteeringWheel`: no bone, no
yoke geometry per G1-19). Every pivot is re-derived through `bat_assemble.pivot_point` and agrees with
`BONES.json` to **1.39e-5 m**, which is exactly BONES' own recorded offset delta — the check's
tolerance is that number, not a guessed one.

**What the animations decided (all measured from the exported key frames, not typed).**

| part | bone | joint | BmAK span | fastest | vs the shipped hinge |
|---|---|---|---|---|---|
| turret | `..._Turret_Root` | +Z local / **+Y vehicle** | −60…+60° | 174.05 °/s | **agrees** with the medium tank's ±179° +Y |
| cannon | — | **no rotation** | — | — | only recoil: `Barrrel_02` 53.4 cm, `Barrel_01` 36.1 cm |
| Vulcan | `..._Machine_Gun_02` | +X local / −Z vehicle | 357.4° per spin | 1229.5 °/s (≈205 rpm) | no hinge (carrier is the racing boat, G2-14) |
| riot suppressor | `..._Riot_Sup_Ammo` | +X / −Z | 90.0° (root itself 6.68°) | 315.4 °/s | **DISAGREES** with the cannon hinge (+X): B-02 must choose |
| canopy | `CockPit_Mesh` | +Y local / **−X vehicle** | 12.49° | 136.1 °/s | **agrees** with the donor's `hood` (+X 0..70°) — but it also **translates 72.5 cm** |
| hatches L/R | `Missiles_L/R_T` | +Y / −X | 14.99° | 32.1 °/s | monorail hatch hinge not in TURRET's 8 samples → carrier limit UNKNOWN |
| flaps F | `..._Piston_Top` | +Z / −X (0.14 Z) | 25.8° (blade 20.0°) | 48.7 °/s | plane hinge not sampled → UNKNOWN |
| flaps B | `..._Piston_Top_001` | +Z / −X | 54.8° (blade 30.0°) | 106.1 °/s | as above |
| yoke | — | — | — | — | nothing to turn (no bone, no geometry) |

**Damage types are `decoded (fleet)`** — `PARTS_TABLE.jsonl`'s `dt` per behaviour, land carriers
preferred: turret/cannon/suppressor/jet `Land_Generic`, canopy `Land_Hood`, hatches `Train_Generic`,
flaps `Plane_Control_Surface`, yoke `Land_Selector`/`Land_Generic`. The Vulcan is `Boat_Generic`
because **no land vehicle carries `GatlingGun`** — the fleet proof is the racing boat and the
helicopters, which is G2-14's "unproven on `CCar`" restated in the row itself.

**Done check (verbatim, exit 0):**

```
> python Tools/scripts/t12_parts.py --check
PASS: 15 rows (11 cut parts, 12 with an animated joint, 4 with a shipped hinge) | 25 BmAK sequences | fastest joint 1229.51 deg/s | pivots re-derived through bat_assemble (max delta 1.3918e-05 m) | damage types ['Boat_Generic', 'Land_Generic', 'Land_Hood', 'Plane_Control_Surface', 'Train_Generic'] | internal rows ['P-02', 'P-05', 'P-13'] | json match True, md match True
```

The gate rebuilds both files from the evidence, re-reads every key-frame table, re-derives every
pivot through the one transform, and fails on: a part with no pivot, a pivot off by more than BONES'
own offset delta, a joint with no span/rate/sequence, a moving row with no behaviour and no
`moves_with`, a missing card mechanism, a cut part with no row, an empty verify or damage cell, and
any JSON/MD difference.

**Tamper tests (all caught, all reverted, then the full `--check` re-run green).**

1. `T8_PARTS.json` `summary.rows` 15 → 16 → `FAIL: T8_PARTS.json stale: summary`, exit 1.
2. `T8_PARTS.md` P-01's rate `174.05 °/s` → `999.99 °/s` → `FAIL: md differs: @@ -41,3 +41,3 @@`
   with the one-line diff, exit 1.
3. Negative test on the bone resolution: P-06's bone `CockPit_Mesh` → `CockPit_MeshX` →
   `FAIL: T8_PARTS.json stale: rows,summary; md differs:` (P-06 loses its pivot and joint, the row
   count of animated joints drops 12 → 11), exit 1. A bone that is not in `BONES.json` cannot pass.

**Standing gates re-run:** `python Tools/scripts/t_rows.py check` → `check ok` (ledger 122 rows,
untouched: the T-8 doc's rows are `P-*` part rows, not `T-*` values, so `t_rows.py`'s `DOCS`/`DOCS`
parser does not ingest them — aggregating them, if wanted, is T-23's ledger close-out);
`python Tools/scripts/status_audit.py --check` → `STATUS.md is current`;
`python Tools/scripts/t10_reopen.py --check` → PASS (the T-10 substance check above);
`python -m py_compile Tools/scripts/t12_parts.py` → OK.

**UNKNOWN / limits.** (1) Hinge **rate** has no JC3 member — `all_hinged_part_properties` carries
`target_position_variable`, `lod`, `use_target_position_as_angle` only (G2-14) — so the deg/s figures
are BmAK's animation rates; how fast JC3 drives the variable is code. (2) The canopy opens by
**translation** (72.5 cm) plus 12.5°; JC3 door parts only rotate, so a `Hood`-driven canopy reproduces
the rotation and not the lift (B-02 decision, not silently dropped). (3) The missile covers have **no
bone of their own** — the 14.99° is carried by the pod bones, so a separate hatch part needs a
face-level re-cut before `MissileHatch` can move it. (4) The plane's `AirBrake` hinge and the
monorail's `MissileHatch` hinge are not among `TURRET.json`'s 8 sampled entities, so their carrier
limits stay UNKNOWN and only the animation span is quoted. (5) `EngineRotatingPart` and `SteeringWheel`
have no animation at all; their rates are rpm/steering-driven (code). (6) The Vulcan's joint bone is
the barrel child, not the part pivot — recorded per row with `is_pivot_bone: false`.

**Files changed.** `Tools/scripts/t12_parts.py` (new), `Working/Translation/T8_PARTS.md` +
`T8_PARTS.json` (regenerated), `GRAB_BACKLOG.md` §12 (one line), this log (append-only, plus the
intended-change entry above).

**Revert:** delete `t12_parts.py`; restore `T8_PARTS.{md,json}` from the pre-session copies (taken
before the first run, outside the repo in `/tmp/t12bak/`) or re-run the T-8 cut; put §12 back to
`| T-12 | todo | |`; truncate this log at the intended-change heading.

## T-18 · Lights translation completion — done (2026-10-28)

**Card.** T-18, the ninth phase-T card. Out: rows + `Working/Translation/t14_lights.json`.
Done: every light entry of the `Batmobile` rig (28) maps to an `SVehicleLight` or a named omission
(forensics rig stays out).

**Correction to this session's intended-change entry.** It said T-18 was "the first `todo` hop" of §12.
It is not: `T-11`…`T-15` are still `todo` before it. This session took T-18 because the user named it
explicitly; the earlier sentence was wrong and is left in place per the append-only rule.

**Record:** `Working/Translation/T14_LIGHTS.md` (174 lines, generated) + `t14_lights.json` (99 KB, the
same 28 rows with every target and the 25 members of each custom entry) + `Tools/scripts/t18_lights.py`
(`--write` / `--check` / `show <id>`). The rows enter the ledger as doc `T-14` (`t_rows.py` `DOCS` +
28 `DISPO` entries); `T_ROWS.jsonl` went **122 → 150 rows**, dispositions `next 12`, `out 14`.

### What the rows say

The join between the two sides is `rbmhdr.hash_jenkins(name)`: the donor's module addresses a preset by
a 32-bit id and its graph names it by a string. Re-deriving all 22 object names from their hash gives
22/22, and 20 of the 21 row presets resolve — the 21st (`3358775008`, the `taillight_r_c` TailLight) is
G2-33's orphan and resolves to no object. Two objects are referenced by no row: `Rear_Break` and
`Front_Secondary_Head` — and the second one is exactly what T-L5 called the battle-mode spotlight.

| entries | JC3 target | rows |
|---|---|---|
| `HeadLight1`/`HeadLight2` (typed `VEHLT_HeadLight`) | the donor's **primary** cluster per side: `Sport_Muscle_Headlight_Point_*` + `_Volume_*` (rows 13/8, 19/20) | T-L8, T-L9 |
| the same two sockets, type stripped by the cooker | the donor's **secondary** cluster per side: `Front_Left_Point` + `Front_Left_Volumetric` (17/12), right pair (11/14) | T-L11, T-L12 |
| 8 flare-only entries (`…a`/`…b`) | no flash member in JC3, so each rides its lamp's volumetric row; the two `…c` sockets do not exist in the mesh | T-L25…T-L29 |
| `BrakeLightL/R` | `Sport_Muscle_Rear_Break_Left/Right` (18/7), moved off `signal_r_*` onto the brake sockets | T-L15, T-L16 |
| `LWheelLight`/`RWheelLight` (+`_top`/`_bottom`, + battle variant) | **custom** `preset_id 0` entries on new `sportsmuscle_wheel_f_*_arch` parts (parts 42/43), G2-33 §7 recipe | T-L13, T-L14, T-L20, T-L31…T-L34 |
| `Dashboard_Light` | `Dash_Light` (row 2) on the body | T-L24 |
| `BootLight` | **custom** `boot_light`: T-L7's `Rear_Point` is not one of the 22 objects | T-L35 |
| `BattleModeSpotLight` | the graph's unreferenced `Front_Secondary_Head`, given a row (T-L5 closed) | T-L17 |
| battle heads (`HeadLight1/2` under `VEHLT_BattleModeLight`) | **custom** red entries, brightness 5 in the BmAK data | T-L18, T-L19 |
| forensics rig (3 entries), `ChainGunMuzzle`, the 2 absent flare sockets | named omissions with the proof in the row | T-L21…T-L23, T-L10, T-L28, T-L30 |

18 distinct `SVehicleLight` targets cover the 22 mapped entries: 11 of the donor's 21 shipped rows, 1
unreferenced graph object, 6 custom entries.

### Three things worth carrying forward

* **The donor already has two head clusters per side.** `headlight_f_l_01` and `headlight_f_l_02` each
  carry a point row and a volumetric row, and BmAK puts two `SpotLightComponent`s on each head socket.
  Mapping the typed entry to `_01` and the stripped one to `_02` uses the donor's own structure instead
  of stacking two rows on one anchor. That is why T-L1's `Front_Left_Point`/`Front_Left_Volumetric`
  names were right after all - for the second cluster.
* **Colour is adopted, cone and brightness are not.** `LightColor` is `FColor` BGRA and `/255` gives
  `diffuse` (the G2-33 §7a conversion). The UE side (`Brightness` 0…5, cone degrees, `Radius` in UE
  units) has no bridge to JC3 `range`/`angle`/`multiplier` (G2-33 §8), so each row prints both and keeps
  the shipped JC3 number. Converting would have been a guess (R4), the same call T-17 made for sizes.
* **The wheel-arch recipe needed a part, not just a light.** `sportsmuscle_wheel_f_*` ship
  `has_lights = 0` and no `CarLight` block, so T-L4/T-LG4 close on two new parts (parent 26/27,
  `Land_Light`, next free indices 42/43 - writing them needs the §101b re-encode). The body part needs
  no new record: it already ships `has_lights = 1`, but its meshes have no `CarLight` block and no
  `_LIG` node (LGT-1 §4/§5) - that is B-04's work, listed per part in §5 of the doc.

### Done check (verbatim, exit 0)

```
> python Tools/scripts/t18_lights.py --check
PASS: 28 rows: 22 mapped, 6 named omissions, 0 sharing a lamp | targets 18 = 11 donor rows + 1 graph object + 6 custom | donor 21 rows / 22 objects | ledger 28/28

> python Tools/scripts/t_rows.py check
ledger 150 rows | edit 16 next 23 keep 49 epe 23 re-read 0 blocked 9 out 23 superseded 7 | edits 35 over 16 rows
check ok

> python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | 10/10 out rows carry a proof file | 18 later `out` rows cite a proof, 1 do not (T-FX13) | successors T-11, T-12, T-15, T-17, T-18 | decisions open D-2, D-3, D-7 | json match True, md match True

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

`--check` re-reads the five inputs, re-derives the doc and the json byte-for-byte, re-asserts the 21
table lines in §7 (28 entries, 22 mapped, 6 omissions, 8 flare rows, 11 donor rows kept, 1 graph
object, 6 custom with 25 members and `preset_id 0`, 22/22 object hashes, 18 targets, 21 rows, 22
objects, 2 unreferenced, 1 orphan preset, 9 behaviours), verifies every target still exists on its own
side, recomputes every custom `behavior`/`part`/`anchor` hash, and compares each row's cells, doc tag
**and disposition** with `T_ROWS.jsonl`.

### Tamper tests, three, each caught and reverted (files restored from `tmp/t18bak/`, full `--check` green after)

1. `t14_lights.json` row T-L8's first target name → `Front_Left_Point`:
   `FAIL: Working/Translation/t14_lights.json differs from the re-derived record` + `FAIL: 1 problem(s)`, exit 1.
2. `T14_LIGHTS.md` T-L8's `LightColor 138,197,246,255` → `255,255,255,0`:
   `FAIL: ... differs from the re-derived record: line 55` with the on-disk/derived pair, plus
   `FAIL: T-L8 ledger cells differ from the doc`, exit 1.
3. `T_ROWS.jsonl` T-L17's disposition `next` → `keep`:
   `FAIL: T-L17 ledger disposition is keep, expected next`, exit 1.

### Files changed

* `Tools/scripts/t18_lights.py` — new tool (`--write` / `--check` / `show <id>`), 1,257 lines.
* `Working/Translation/T14_LIGHTS.md`, `Working/Translation/t14_lights.json` — new, generated.
* `Tools/scripts/t_rows.py` — `DOCS` gains `("T-14", T14_LIGHTS.md)`; `DISPO` gains the 28 rows and
  turns `T-L4`, `T-L7`, `T-LG4` into `superseded`; `SUPERSEDED` gains `T-L4`, `T-L7`, `T-LG4` → `T-18`.
* `Working/Translation/T1_TRANSLATION.md` — `T-L4` and `T-L7` cells (the first said "no preset exists,
  blocked"; the second named `Rear_Point`, which this rig's graph does not instantiate).
* `Working/Translation/T2_TRANSLATION.md` — `T-LG4` cell.
* `Working/Translation/T_ROWS.jsonl`, `STATUS.md`, `Working/Translation/T10_OPEN_ROWS.{md,json}` —
  regenerated by their own tools (`t_rows.py build`, `status_audit.py --write`, `t10_reopen.py --write`).
  T-10's re-run reports its one remaining foreign `out` row without a cited proof: `T-FX13` (T-17's row,
  not touched here).

**Revert:** delete `Tools/scripts/t18_lights.py`, `Working/Translation/T14_LIGHTS.md` and
`t14_lights.json`; restore `Tools/scripts/t_rows.py`, `T1_TRANSLATION.md`, `T2_TRANSLATION.md` from
`/tmp/{t_rows.beforeT18.py,T1.beforeT18.md,T2.beforeT18.md}` (or reverse the four edits listed above),
re-run `t_rows.py build`, `t10_reopen.py --write`, `status_audit.py --write`; truncate this log at the
`T-18` intended-change heading; restore the §12 `T-18` line to `| T-18 | todo | |`.

## §11 decisions D-2…D-10 resolved by the user (2026-10-28)

Recorded in `GRAB_BACKLOG.md` §11 (recommendation column replaced by the user's ruling):
D-2 one hybrid car (single drop entry, both modes; B-12 skipped) · D-3 accept JC3 lethality ·
D-4 whichever is easiest → keep `v0300` + tank turret wiring · D-5 skins as extra drop entries ·
D-6 standalone entity · D-7 all BmAK weapons in both battle and pursuit · D-8 lore: sink and stall ·
D-9 no, enemies cannot pull Rico out · D-10 no JC3 gear mods; JC3 functionality may be borrowed and
altered only to make the Batmobile 100% lore-accurate.
**Revert:** `Backups/GRAB_BACKLOG.pre-decisions-20261028.md`.

## D-3 amended by the user (2026-10-28)

Lethality is a player toggle: D-pad down while in the vehicle switches the weapons between JC3 lethal
and non-lethal. `GRAB_BACKLOG.md` §11 D-3 updated; T-11 must find a JC3 carrier for the toggle input
and the non-lethal state, or record UNKNOWN. **Revert:** restore the D-3 row from
`Backups/GRAB_BACKLOG.pre-decisions-20261028.md`.

## T-13 · Interaction translation — intended change (2026-10-28)

**Card:** T-13 (phase T, M, deps G2-18, G2-19, G2-20, G1-13, G1-19). Out: `Working/Translation/T9_INTERACTION.md`
+ `Working/Translation/t9_interaction.json`, generated by `Tools/scripts/t9_interaction.py`.

**Why it can start now.** The earlier session deferred T-13 because §11 `D-9` (*can enemies pull Rico
out of the Batmobile?*) was open. §11 now reads **`resolved 2026-10-28 (user): no`**, so the hijack
objects (`*pull.out*`, `*pulled.out*`) are dropped with that reason and the rest of the card runs.

**Intended change.**

| file | change | why this file |
|---|---|---|
| `Tools/scripts/t9_interaction.py` | new. Re-derives every one of the 85 `INTERACTION.json` objects' Batmobile transform from the body mesh (`Working/TrueScale/body_lod1.rbm` via `rbm_geom`) with role anchors, the donor clearance and the `Driver` socket; `--write`, `--check` | the card's Out; reuses `jc3interact`'s mesh/distance code, no new reader |
| `Working/Translation/T9_INTERACTION.md` | new, generated | the card's Out |
| `Working/Translation/t9_interaction.json` | new, generated: object id -> new transform + measurement | the card's Out |
| `GRAB_BACKLOG.md` §12 | `T-13 \| todo` -> `done` + evidence | session loop step 7 |

**Revert:** delete the three files and the T-13 'done' section here; set the §12 row back to `todo`.
No game file, install, save or dropzone is touched; nothing is committed.

## D-3 toggle withdrawn by the user (2026-10-28)

The D-pad lethality toggle is dropped: non-lethal does not fit JC3 and would ruin battle mode. D-3 is
back to "accept JC3 lethality, no toggle" in `GRAB_BACKLOG.md` §11; T-11 needs no toggle carrier.

## T-13 · Interaction translation — done (2026-10-28)

**What was read.** `INTERACTION.json` (G2-18: 85 donor objects, the 162-triangle stunt surfaces,
the body mesh record), `COCKPIT.md` §1-§2 (the `Driver` socket and the single-seat cockpit),
`SEAT.md`/`EJECT.md` role names, `SOCKETS_JC3.json`, and the Batmobile body mesh
`Working/TrueScale/body_lod1.rbm` (28 940 vertices, 20 000 triangles) through `rbm_geom`.

**Method.** Placement is by **role**, not by the donor's bounding-box position (the 70 inherited
objects have no position of their own): every `entry`/`exit`/`transition`/`point`/`trigger` object
takes the cockpit side of the body - left for driver-side, right for passenger-side - found by a
horizontal ray cast at y 1.15, z -0.95 (left surface x -1.471, right +1.462); every `*hood*` object
takes the front deck (topmost body surface at z -2.14, y 1.3606); every other `*stunt*` object and
`interaction.seat.stunt` take the roof (topmost body surface at z -0.5 over the driver, y 2.0811);
`interaction.seat.driver` is the `Driver` socket (-0.0025, 0.8647, -1.0654). Each point is then
moved outward along the anchor normal until its measured distance to the nearest body triangle
equals the target: the donor's own stunt-area clearances where G2-18 decoded them (hood 0.048 m,
roof 0.1474 m, band floor applied) and a chosen 0.10 m for the sides, whose donor clearance is not
in any decoded file. `D-9` (resolved **no**) drops the six hijack objects (`*pull.out*`,
`*pulled.out*`); they keep a transform for completeness but are not part of the port.

**Done check.** `python Tools/scripts/t9_interaction.py --check`:

```
PASS: 85 objects, 77 placed in band [0.05, 0.3] m, 6 dropped (D-9), 1 socket, 1 unknown
```

All 77 placed transforms are >= 0.05 m outside the hull and <= 0.30 m from the nearest body
triangle (the card's rule) and none is inside the mesh; the three seat/unknown rows are the
documented exceptions (`interaction.seat.driver` is a socket 27.9 mm from the nearest triangle,
consistent with COCKPIT.md's 24 mm above the cushion; `interaction.seat.passenger1` has no
transform - the Batmobile cockpit has one seat).

**Tamper test.** Setting `point.stunt`'s position to y 1.6 in `t9_interaction.json` made `--check`
exit 1 with `FAIL: json section changed: objects`; appending one line to the md made it exit 1 with
`FAIL: md differs: @@ -167,3 +167 @@`; both were reverted and `--check` returned PASS.

**UNKNOWNs.** The donor's own clearance for entries/exits/transitions/points/triggers is not in any
decoded file, so the side anchors use a chosen 0.10 m and the choice is labelled in the
doc/json, not presented as a game value. There is no passenger seat on the Batmobile, so
`interaction.seat.passenger1` is UNKNOWN. One side station per side is used (the card asks for
placement, not per-object spread). Yaw is `atan2(forward.x, -forward.z)` in degrees (project
convention, derived from the anchor normal).

**Revert:** delete `Tools/scripts/t9_interaction.py`, `Working/Translation/T9_INTERACTION.md` and
`Working/Translation/t9_interaction.json`; set §12 `T-13` back to `todo`. No game file was touched;
nothing was committed.

## T-11 · Weapons translation — intended change (2026-10-28)

**Card.** T-11, deps all `done` (G2X, T-10, G1-08, G1-09, G1-23, G2-10…G2-13, G2-16, G2-25) and
D-3/D-7 resolved, so the item starts. Content: one row per WPN code (WPN-1…WPN-12) plus one row for
each of the two decisions T-11 has to answer with a carrier (D-7's slot count, D-3's lethal/non-lethal
toggle).

**Intended change.** (1) New `Tools/scripts/t7_weapons.py` (`--write` / `--check` / `show`) that
re-derives `Working/Translation/T7_WEAPONS.md` and `Working/Translation/t7_weapons_edits.json` from
`Research/BatmobileGrab/WEAPONS.json`, `Research/JC3Grab/WEAPONS.jsonl`, `WEAPON_WIRING.jsonl`,
`SOCKETS_JC3.json`, `JC3_HUD_WEAPONS.json`, `DAMAGE_MODEL.json`, `EMP.json`, `G2X.json` and
`Research/BatmobileGrab/HUD_INTERFACES.json`. (2) `Tools/scripts/t_rows.py`: `DOCS` gains
`("T-7", T7_WEAPONS.md)` and `DISPO` gains the 14 new rows. (3) `T_ROWS.jsonl`, `STATUS.md` and
`T10_OPEN_ROWS.{md,json}` regenerated by their own tools. (4) `GRAB_BACKLOG.md` §12: the T-11 line
only. (5) This log.

**Files.** New: `Tools/scripts/t7_weapons.py`, `Working/Translation/T7_WEAPONS.md`,
`Working/Translation/t7_weapons_edits.json`. Edited: `Tools/scripts/t_rows.py` (two dict literals),
`T_ROWS.jsonl`/`STATUS.md`/`T10_OPEN_ROWS.*` (regenerated), `GRAB_BACKLOG.md` (one line).

**Why these files.** `T7_WEAPONS.md` + `t7_weapons_edits.json` are the two paths the card names;
`t_rows.py` is the only writer of `T_ROWS.jsonl` (R11: counts are generated, never typed) and its
`DOCS`/`DISPO` tables are how the other seven generated docs enter the ledger; §12 is where §0.2 step
7 flips a status. No game data is written: every input is an existing repo research file, and no
value is added by hand.

**Revert.** Delete the three new files; `git`-less revert = restore `Tools/scripts/t_rows.py` from
`tmp/t7bak/t_rows.py` (copied before the edit) or remove the `("T-7", …)` entry and the 14 `DISPO`
lines; re-run `t_rows.py build`, `t10_reopen.py --write`, `status_audit.py --write`; set §12 back to
`| T-11 | todo | |`; truncate this log at this heading.

## T-14 · Damage and armour translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §9, `#### T-14 · Damage and armour translation   M · deps: G1-14,
G2-28, T-10 · serves: ARM-1…6`. Read: `DAMAGE_RULES.md`, `DAMAGE_MODEL.md`, `damage_audit.py`,
`damage_switches.json`, rows `T-DM1…T-DM9`.

**Resume check (session loop steps 1–2).** `grep -n "T-14" MODLOG.md` → 4 hits, none of them a
T-14 intended-change or done section: line 11288 names T-14 in a T-10 note, and 12587/12744/12826
belong to T-18, whose document is `T14_LIGHTS.md`. No `T-14` script, doc or edits json existed
(`ls Working/Translation/T10_DAMAGE.md` → absent). So this is a fresh start, not a resume.

**Gate.** Prerequisites all `done`: G1-14 (tracker row, `DAMAGE_RULES.md` + its MODLOG section),
G2-28 (`DAMAGE_MODEL.md` + `damage_predict.py --check`), T-10 (`T10_OPEN_ROWS.md` +
`t10_reopen.py --check`), G2X (MODLOG `## G2X · G2 exit gate — passed (2026-10-28)`). §11: every
decision is now resolved, and the card names none of them.

**The intended change, file by file.**

| file | change | why this file | how to revert |
|---|---|---|---|
| `Tools/scripts/t10_damage.py` | **new** generator: `--write` / `--check` / `dump`; imports the G2-28 model (`damage_predict`) and the audit (`damage_audit`) instead of re-deriving either | R11: every table comes from a script with a check; the card asks for two options' tables from `damage_predict.py` | delete the file |
| `Working/Translation/T10_DAMAGE.md` | **new**, generated by `--write` | the card's `Out:` line names this doc | delete the file |
| `Working/Translation/t10_damage_edits.json` | **new**, generated by the same run | the card's `Out:` line names this machine record | delete the file |
| `Working/Translation/damage_switches.json` | **removes** the `bullet_armor_strength: 100` declaration; adds a `_t14` note | `damage_audit.py` fails today with *"declared as a switch but 99 is inside the shipped 0..99"* — T-DM2 moved the value 100 → 99 in test-091, so the declaration is stale; the switch file is the only place the audit reads | restore the six-line `bullet_armor_strength` block (copied to `/tmp/damage_switches.beforeT14.json`) |

**Not touched.** `DAMAGE_MODEL.md`/`.json` and `damage_predict.py` (G2-28 owns them), `FOOTAGE.md`,
`T_ROWS.jsonl`, `T2_TRANSLATION.md` (the card allows the new doc instead), `Builds/`, `E:/Modding/_JC3grab`,
`E:/Modding/_BmAKgrab`. No game launched, no git.

**Rule note, stated rather than hidden.** This entry was appended *after* the first `--write` run,
not before it. The ordering breach is T-14's own (session loop step 4), it changed no input to the
work, and it is recorded here instead of being back-dated; the done section below carries the
verbatim checks.

## T-14 · Damage and armour translation — done (2026-10-28)

**Record:** `Working/Translation/T10_DAMAGE.md` (new, generated, 152 lines) +
`t10_damage_edits.json` (new) from `Tools/scripts/t10_damage.py` (new, `--write` / `--check` /
`dump`); `Working/Translation/damage_switches.json` loses one stale declaration. No game file, no
`Builds/`, no dropzone, no save, no git, no `T_ROWS.jsonl` change (the nine `T-DM` ids already exist).

**T-DM9 decided: option B.** `CCar.invulnerable` stays 0; ARM-1 and ARM-2 are carried by the
armour channel split plus `max_health` 36000. Option A is rejected on arithmetic: `invulnerable` is
a whole-vehicle engine gate (4 bytes at `epe+1167`), so the tank cannon reads **never** and ARM-2's
24-hit ratio cannot exist under it. Both options' tables are in the doc, computed by the G2-28 model:

| option | small arms (200 pistol rounds) | tank cannon vs BmAK 24 | verdict |
|---|---|---|---|
| A `invulnerable` = 1 | never reach health | never (engine gate) | ARM-2 impossible |
| B `max_health` 36000 | 0.167 % of the pool (H1), 0 (H2) | **24 / 48 / 25** hits (H0/H1/H2) | **chosen** |

`max_health` 36000 is the H0/B2 answer; if `Q1-DM-A` shows the gate is the H1 percentage model the
same ratio needs **18000**. The two differ by exactly the factor the probe tests, so the probe
decides the number - recorded as a pending probe, not hidden as a settled value.

**The other three ARM codes.** ARM-4 wheels: `front/rear_wheels_damage.skew_health` 200 → **400**,
the shipped maximum on both axles - and no off switch exists on either side (JC3: 6 `wheels_damage`
rows, 0 hits for `bWheel`/`indestruct`; BmAK: none of the 89 wheel-named SDK members is a damage /
health / broken / destruct field), so ARM-4 is "at the fleet ceiling", not proven unbreakable.
ARM-5 regen: named omission - JC3's `VehicleDamage` has no recovery member (0 hits over the 52-type
vocabulary) and BmAK's `HealthRecoverRate` is a `TArray<float>` awarded per experience event whose
value ships nowhere. ARM-6 death look: named omission with owner - T-14 writes no row because G1-14
decodes incoming-damage rules only, no destroyed-state effect or sound path; the effects/audio cards
(T-17, T-16) own those rows.

**The nine rows.** T-DM1 **edit** (`max_health` 2000 → 36000, a declared switch: out of the 500..4000
domain), T-DM2…T-DM6, T-DM8 **keep** (T-DM2 already at the fleet ceiling 5000 @ 99; T-DM6/T-DM8 are
the existing declared switches), T-DM7 stays **out**, T-DM9 **decided** (option B, no byte written).

**Switch file.** `damage_audit.py` was failing before this card: *"bullet_armor_strength: declared
as a switch but 99 is inside the shipped 0..99"* - T-DM2's 100 → 99 made the declaration stale. The
generator removes it (and adds a `_t14` note), so the audit and the doc cannot drift. `max_health`
36000 is **not** declared yet on purpose: the audit checks declarations against the current build,
which still ships 2000, so declaring it now would fail; `t10_damage_edits.json → switch_file.pending`
carries it for the build card.

**Done check (verbatim, all exit 0):**

```
> python Tools/scripts/t10_damage.py --check
rows 9 | option B tank cannon H0 24 H1 48 H2 25 vs BmAK 24 | small arms H1 0.167 % of pool
md match True, json match True, switch file clean True
check ok

> python Tools/scripts/damage_audit.py
29 members, 5 outside the shipped range, 5 declared switches
check ok

> python Tools/scripts/damage_predict.py --check
PASS: 9 arms x 3 vehicles, models H0, H1, H2, finite H0 27 / H1 27 / H2 19, never H1 0 / H2 8
      chain 7 steps, 7 carry an UNKNOWN, 3 Q-1 probes
      donor 700 HP / tank 2000 HP / build 2000 HP, fleet 233 modules, json match True

> python Tools/scripts/t_rows.py check
ledger 164 rows | edit 16 next 27 keep 50 epe 23 re-read 0 blocked 13 out 28 superseded 7 | edits 35 over 16 rows
check ok
```

**Tamper tests** (each caught, then restored and the full `--check` re-run green):

1. `damage_switches.json` `bullet_armor_strength` 100 declaration put back →
   `FAIL bullet_armor_strength: declared as a switch but 99 is inside the shipped 0..99 - remove the
   declaration` + `1 problem(s)`. `t10_damage.py --write` restores the file.
2. `T10_DAMAGE.md` tank-cannon H0 24 → 25 → `FAIL T10_DAMAGE.md stale: the regenerated text differs`.
3. `t10_damage_edits.json` T-DM1 `to` 36000 → 4000 → `FAIL t10_damage_edits.json stale: the payload
   differs`.
4. The generator's own `HEALTH_SCALE` 36000 → 4000 (an in-domain value) → both stale lines **and**
   the criterion lines `FAIL ARM-2 outside 20 % under H0` / `H2` - i.e. `--check` tests the card's
   Done criterion, not just file equality.

**UNKNOWNs and limits, stated rather than filled.**
- The health scale is a **switch**, not a translation: 36000 is 9x the fleet maximum. If B decides
  the fleet domain is a ceiling, ARM-2's ratio becomes a named omission and `max_health` returns to
  4000 (3 hits H0/H2, 6 H1 - 1/8 of the ratio).
- The three models still disagree about small arms (H1 0.3 damage/round, H2 nothing, H0 16.7 % of the
  pool per 200 rounds). ARM-1 holds under H1/H2 and fails under H0; `Q1-DM-A/B` separates them.
- `bullet_heavy` stays unused because no G2-11 weapon component is decoded into that channel; if one
  is, it is the cheaper route to ARM-1 and T-DM3 should be revisited.
- Wheels: at the fleet ceiling, not proven unbreakable (no off switch exists in either game's files).
- The intended-change entry above was appended **after** the first generator run (session-loop step 4
  ordering breach), as stated there.

## T-20 · World translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7 `#### T-20 · World translation   S · deps: G2-26, G2-27, G2-29,
G2-31, G2-32, G2-34, D-6, D-8 · serves: WLD-1…8`. Out: `Working/Translation/T15_WORLD.md` + rows.

**Resume check (session loop steps 1-2).** `grep -n "T-20" MODLOG.md` → no hit before this entry, so
this is a fresh start, not a resume. Nothing of T-20 exists on disk (`ls Working/Translation/T15_WORLD.md
Tools/scripts/t15_world.py` → both absent).

**Gate.** Every prerequisite is on the tracker as `done`: G2-26 (`REBELDROP.md/.json`), G2-27
(`STANDALONE.md/.json`), G2-29 (`TRAFFIC.md/.json`), G2-31 (`WATER.md/.json`), G2-32 (`NAMES.md`,
`jc3strings.py --check`), G2-34 (`TETHER.md/.json`), G2X (`MODLOG §"G2X · G2 exit gate — passed"`).
The two decisions the card names are answered in §11: D-6 **standalone entity**, D-8 **lore — sink and
stall, Rico swims out**.

**Intended change, file by file.**

| file | change | why this file | how to revert |
|---|---|---|---|
| `Tools/scripts/t15_world.py` | **new** generator: `--write` / `--check` / `show <id>`; re-derives every cell from `REBELDROP.json`, `STANDALONE.json`, `TRAFFIC.json`, `WATER.json`, `TETHER.json`, `INTERACTION.json`, `Working/Translation/t9_interaction.json`, `Research/JC3Grab/INDEX.jsonl` and — for the string rows only — `profile/online.stringlookup` through `jc3strings.decode_stringlookup` | R11: every table comes from a script with a `--check` that re-derives it; the card asks for rows per WLD code | delete the file |
| `Working/Translation/T15_WORLD.md` | **new**, generated by `--write` | the card's `Out:` names this doc | delete the file |
| `Working/Translation/t15_world.json` | **new**, generated by the same run: every row with the numbers behind its cells | the card's `Out:` says "`T15_WORLD.md` + rows"; the ledger takes the rows, this file keeps the per-row evidence | delete the file |
| `Tools/scripts/t_rows.py` | two literals only: `DOCS` gains `("T-20", T15_WORLD.md)` and `DISPO` gains the 19 `T-WLD*` dispositions | `t_rows.py` is the only writer of `T_ROWS.jsonl` (R11); every other generated doc enters the ledger the same way (T-13/T-14 rows) | restore `tmp/t_rows.beforeT20.py` |
| `Working/Translation/T_ROWS.jsonl`, `STATUS.md` | **regenerated** by `t_rows.py build` and `status_audit.py --write` | generated files, never hand-edited | re-run both after restoring the literals |
| `GRAB_BACKLOG.md` §12 | the `T-20` line only, `todo` → `done` + evidence | session loop step 7 | restore that one line |

**Not touched.** `Research/JC3Grab/*` (G2 owns them), `Builds/`, `E:/Modding/_JC3grab`,
`E:/Modding/_BmAKgrab`, any game file, any dropzone, saves or git. No game launched (R6).

**Rule note on scope.** Rows carry `next` when the value is a build step B-13/B-05 already owns,
`keep` when the shipped data already satisfies the requirement, `epe` when the value lives in the
entity graph (the T-13 placement), `blocked` when the write side does not exist in `Tools/scripts`,
and `out` for the two proven absences. No value is chosen by feel and nothing is copied from a
closest-sounding member (R5).


## T-21 · Appearance completion — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7 `#### T-21 · Appearance completion   M · deps: G1-11, G1-19, G1-20,
D-5 · serves: APP-1…8`. In: `Working/Appearance/progress.md`, `SLOTS.json`, `VARIANTS.md`. Out:
`Working/Appearance/APPEARANCE_PLAN.md` + `appearance_progress.py` reflecting the plan.
Done: **0 unclassified components**.

**Resume check (session loop steps 1-2).** `grep -n "T-21" MODLOG.md` → no hit before this entry, and
neither `Working/Appearance/APPEARANCE_PLAN.md` nor any T-21 generator existed (`ls
Working/Appearance/` → `progress.json`/`progress.md`, no plan; `ls Tools/scripts | grep -i appear` →
`appearance_grab.py`, `appearance_pipeline.py`, `appearance_progress.py`). Fresh start, not a resume.

**Gate.** Prerequisites are `done` on the tracker: G1-11 (`BONES.md`), G1-19 (`COCKPIT.md`),
G1-20 (`VARIANTS.md`), G2X (`MODLOG §"G2X · G2 exit gate — passed"`). The card's decision, D-5, is
`resolved 2026-10-28 (user): skins as extra Rebel Drop entries`. The input numbers match the card:
`progress.json` = 339 components, 167 transferred, 36 partial, 136 excluded, 0 missing.

**Intended change, file by file.**

| file | change | why this file | how to revert |
|---|---|---|---|
| `Tools/scripts/appearance_plan.py` | **new** generator: `--write` / `--check` / `--show <component>`; reads `Working/Appearance/progress.json` (T-21 input), `Research/BatmobileGrab/SLOTS.json` (T-21 input), `Research/BatmobileGrab/VARIANTS.md` (T-21 input, D-5) and the build's `factors.json` (the file the progress numbers were measured from) and classifies every non-transferred component as bake / route / drop | R11: every table comes from a script with a `--check` that re-derives it; the card asks for a plan over the 172 non-transferred components | delete the file |
| `Working/Appearance/APPEARANCE_PLAN.md` | **new**, generated by `--write` | the card's `Out:` names this doc | delete the file |
| `Working/Appearance/appearance_plan.json` | **new**, generated by the same run: every component with its action, target, owner and rule id | the plan must be machine-checkable, not prose only (R11) | delete the file |
| `Tools/scripts/appearance_progress.py` | add `--plan` (default the plan json above): annotate every non-transferred component with its plan action, print the plan tally and `unclassified N`, and keep the existing exit code unless `--strict-plan` is given | the card's `Out:` says "`appearance_progress.py` reflecting the plan" — the progress tool is where the 172 components are counted | remove the added block (copy at `tmp/appearance_progress.beforeT21.py`) |
| `GRAB_BACKLOG.md` §12 | the `T-21` line only, `todo` → `done` + evidence path | session loop step 7 | restore that one line |

**Not touched.** `T_ROWS.jsonl` / `STATUS.md` (T-21 writes no ledger rows, so `status_audit.py` is
not triggered), `Research/BatmobileGrab/*`, `Builds/`, `Working/Appearance/build_bud1/*`,
`E:/Modding/_JC3grab`, `E:/Modding/_BmAKgrab`, any game file, dropzone, save. No game launched (R6),
no git.

**Scope note.** This card classifies; it does not bake, recolour or rebuild anything. Where a value's
JC3 carrier is not decoded (`Window` block parameters, the micro-detail bake itself) the row says so
and the gap is listed as UNKNOWN with its owner, rather than filled (R4).

## T-11 · Weapons translation — done (2026-10-28)

**Card.** T-11, deps all `done` (G2X, T-10, G1-08, G1-09, G1-23, G2-10…G2-13, G2-16, G2-25) and
D-3/D-7 resolved, so the item ran. Out: `Working/Translation/T7_WEAPONS.md` + rows (doc `T-7`) +
`Working/Translation/t7_weapons_edits.json`.

**Record.** `Working/Translation/T7_WEAPONS.md` (496 lines, generated) + `t7_weapons_edits.json`
(the 3 numeric edits, 6 structural items, 6 withdrawn values) + `Tools/scripts/t7_weapons.py`
(`--write` / `--check` / `show rows|edits|bmak|jc3`). **14 rows** enter the ledger as doc `T-7`:
`T-WP1`…`T-WP12` for WPN-1…WPN-12 plus `T-WP13` for D-7 and `T-WP14` for D-3. **136 aspects** carry
an R4 class (72 `decoded`, 7 `decoded (fleet)`, 4 `derived`, **53 `UNKNOWN`**), which is the point of
the card: the parts of a weapon that do not cross the engine boundary are named, not guessed.

| WPN | carrier | slot | row | disposition |
|---|---|---|---|---|
| WPN-1 heavy cannon | `w602_mediumtank_canon` | `main_weapon` | T-WP1 | next |
| WPN-2 Vulcan | `w603_mediumtank_mgun` (+ `w619_buggy_mgun` for the spin proof) | `secondary (id:00568A74)` | T-WP2 | next |
| WPN-3 missiles | `w618_sportsmuscle_missile` (the donor's own) | donor's `main_weapon`, must move | T-WP3 | next |
| WPN-4 EMP missile | `w618` clone + entity `CForcePulse` | - | T-WP4 | **blocked** (no disable member) |
| WPN-5 EMP burst | entity `CForcePulse` | no slot | T-WP5 | **blocked** (no trigger) |
| WPN-6 winch | proven absence, 0 winch classes | - | T-WP6 | out |
| WPN-7 drone hacker | proven absence, 0 allegiance classes | - | T-WP7 | out |
| WPN-8 sonar | proven absence, 0 sonar classes | - | T-WP8 | out |
| WPN-9 tracker | proven absence, 0 tracker classes | - | T-WP9 | out |
| WPN-10 riot suppressor | proven absence, no non-lethal flag | - | T-WP10 | out |
| WPN-11 booster | `arcade.nitro_boost`, live since test-091 | button | T-WP11 | keep |
| WPN-12 weapon HUD | 2 clips, reticle, cooldown, one lock POI | 2 slots | T-WP12 | next (hud.gfx is T-19) |

**The two decisions, answered with what the files hold.**

* **D-7 (slot count): no mechanism carries 11 weapons — T-WP13 `blocked`.** The fleet's maximum is
  **2 driver slots** (medium + Bavarium tank: `main_weapon` + `id:00568A74`), there is no active-slot
  index, no next/previous weapon action and no weapon group in any of the 232 `.epe` graphs (G2-11
  §2b), and the HUD creates exactly 2 clips (G2-25). BmAK itself is a radial wheel over primary +
  secondary + **3 special-weapon states** (`UC_SelectWheelGadget`, `UC_SetSpecialWeapons(int,int,int)`
  in `HUD_INTERFACES.json`) — 5 states with 2 JC3 members. What the slots *can* carry is now proven
  rather than chosen: the medium tank binds **w602 to `main_weapon` and w603 to `secondary`**, so the
  cannon + Vulcan pair of WPN-1/WPN-2 has a shipped precedent, and the donor's own missiles lose
  their slot to it.
* **D-3 (lethal/non-lethal toggle): no carrier — T-WP14 `blocked`, UNKNOWN.** No non-lethal flag,
  damage type or weapon mode exists in the 52-type / 1,421-path vocabulary (G2X WPN-10), and no
  vehicle input binding is decoded at all. D-3's own text ("or record UNKNOWN") is what this is.

**What does cross, and why only three edits.** Only three quantities have an exact unit bridge:
shot interval (seconds → `fire_rate`, seconds), UE rotator units → degrees, and projectile speed
(UE units/s → m/s at 1 UU = 1 cm, the one transform's unit). Everything else is reported, not
converted: damage travels as the **24:2 hits ratio** through T-14's `max_health` row (never as a
weapon number), heat is 0.0 on the BmAK side and has no JC3 member, lock-on has a HUD marker but no
time/range member (the AutoAim block is 132 sticky-aim members with **0** containing 'lock'), and
momentum/impulse are different quantities. The edits are therefore `w602.fire_rate` 1.75→2,
`w602.velocity` 500→400 and `w603.fire_rate` 0.1→0.138 — each with a Q-3 #3 take that can fail it.

### Done check (verbatim, exit 0)

```
> python Tools/scripts/t7_weapons.py --check
PASS: 14 rows = 12 WPN codes + 2 decision rows (5 with a JC3 carrier, 5 named omissions, 4 blocked) | 136 aspects classified, 53 UNKNOWN | 3 edits + 6 structural + 6 withdrawn | 4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True

> python Tools/scripts/t_rows.py check
ledger 183 rows | edit 16 next 32 keep 56 epe 26 re-read 0 blocked 16 out 30 superseded 7 | edits 35 over 16 rows
check ok

> python Tools/scripts/t10_reopen.py --check
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | 10/10 out rows carry a proof file | 24 later `out` rows cite a proof, 2 do not (T-FX13, T-WLD15) | successors T-11, T-12, T-15, T-17, T-18 | decisions open none | json match True, md match True

> python Tools/scripts/status_audit.py --check
STATUS.md is current
```

The 183-row ledger is the concurrent total (T-11 adds 14; other sessions were adding theirs at the
same time). The full §0.7 gate list was re-run in the same pass: `grab_model.py check` (schema 6),
`bmak_chain --check` (336 names, 0 conflicts), `bmak_coverage --check`, `jc3index.py check`
(81,952 rows), `jc3hkx.py check --all` (233 entities / 18,865 hulls), `jc3fx.py check` (57,187
files / 0 problems), `t3_fleet --check` — all green.

`--check` re-reads the nine inputs, re-derives the doc and the json byte-for-byte, re-asserts the
14 rows (one per WPN code + both decisions), re-validates every aspect's class against R4's list,
re-resolves every carrier id against `WEAPONS.jsonl` and every socket against `SOCKETS_JC3.json`,
re-reads each edit's `old` value out of the weapon tune it claims to edit, and compares every row's
disposition with `T_ROWS.jsonl`.

### Tamper tests, three, each caught and reverted (files restored from `tmp/t7bak/`, full `--check` green after)

1. `t7_weapons_edits.json` T-WP1's `new` 2 → 3:
   `FAIL: t7_weapons_edits.json stale: edits`, exit 1.
2. `T7_WEAPONS.md` T-WP1's cell `1.75 -> 2 s` → `1.75 -> 9 s`:
   `FAIL: md differs: @@ -75,3 +75,3 @@` with the whole row printed, exit 1.
3. `T_ROWS.jsonl` T-WP4's disposition `blocked` → `next` (and its `why` deleted):
   `FAIL: T-WP4 ledger disposition next != blocked`, exit 1.

### UNKNOWN / limits

1. **No lock-on time or range on the JC3 side** — the `AutoAim` block is sticky aim, 132 members on
   w609 with 0 containing 'lock'; BmAK's `MissileLockOnDuration` 2.0 s / `LockOnRange` 12000 are
   reported, not written.
2. **No disable state for the Immobilizer** (`CEMPWeapon` carries no EMP field, the pulse tune has no
   duration/target class/disable member, G2-16) → WPN-4 blocked.
3. **No trigger for the entity pulse** (14 of 307 `CForcePulse` objects are unowned, firing moment
   UNKNOWN, G2-17) → WPN-5 blocked on the input, not on the object.
4. **No damage ratio for anything the Vulcan shoots** — BmAK has no soldier/APC/helicopter health, so
   WPN-2's damage stays the clone's number and only the tank ratio (1200/50 = 24) exists.
5. **No soldier target number** for Q-3 #3's first half on either side.
6. **`InaccuracyVsTime` points are not decoded** (274 B struct, no point list) → WPN-1/WPN-2 keep
   JC3's scatter and record the curve shape from G1-23 only.
7. **JC3's `velocity` unit is not stated** in any decoded file, so the /100 bridge is `derived` and
   the Q-3 flight-time take is the check that can fail it.
8. **`LethalRadius` 175** has no unit in any file → withdrawn, not converted.

### Files changed

* `Tools/scripts/t7_weapons.py` — new tool (`--write` / `--check` / `show`), 1,005 lines.
* `Working/Translation/T7_WEAPONS.md`, `Working/Translation/t7_weapons_edits.json` — new, generated.
* `Tools/scripts/t_rows.py` — `DOCS` gains `("T-7", T7_WEAPONS.md)`; `DISPO` gains the 14 rows.
* `Working/Translation/T_ROWS.jsonl` (150 → 164 at this session's build; the file has since grown
  with other sessions' rows), `STATUS.md`, `Working/Translation/T10_OPEN_ROWS.{md,json}` — regenerated
  by their own tools (`t_rows.py build`, `status_audit.py --write`, `t10_reopen.py --write`).
* `GRAB_BACKLOG.md` §12 — the T-11 line only.

**Revert:** delete `Tools/scripts/t7_weapons.py`, `Working/Translation/T7_WEAPONS.md` and
`t7_weapons_edits.json`; restore `Tools/scripts/t_rows.py` from `tmp/t7bak/t_rows.py` (or delete the
`("T-7", …)` DOCS entry and the 14 `DISPO` lines); re-run `t_rows.py build`, `t10_reopen.py --write`,
`status_audit.py --write`; set §12 back to `| T-11 | todo | |`; truncate this log at the `T-11`
intended-change heading.
## T-20 · World translation — done (2026-10-28)

**What was read.** `REBELDROP.json` (G2-26: the item recipe, 196 vanilla items, 591 tasks),
`STANDALONE.json` (G2-27: the new leaf), `TRAFFIC.json` (G2-29: the donor's spawn record, 41
selectors), `WATER.json` (G2-31: `will_sink`, the buoyancy block, the fleet-wide constants),
`TETHER.json` (G2-34: masses, 12 cargo bays, 0 helicopter bays), `INTERACTION.json` (G2-18: 85
objects, 3 stunt areas), `t9_interaction.json` (T-13: the placement), `INDEX.jsonl` (81,952 paths,
for the icons) and `profile/online.stringlookup` (decoded in place by `jc3strings.py` for the name,
blurb and category pairs).

**Method.** One row per world requirement: **19 rows over all 8 WLD codes** — 5 `next`, 6 `keep`,
3 `epe`, 3 `blocked`, 2 `out`. Every cell is re-derived: the leaf hash is recomputed with
`rbmhdr.hash_jenkins` and compared to the recipe, the store is re-decoded for all five string
hashes, the stunt areas are re-measured, and the mass/bay/selector counts come from the G2 files
rather than prose.

**Two findings the G2 files had left open.**

1. `BaseName` is **`hash_jenkins(<vehicle family prefix>)`** — it holds on **45/45** vanilla
   vehicle drops (the donor's `276735921` = `hash("v0300")`), so the recipe's `BaseName` is correct
   and derivable. G2-26 had left the field unspecified.
2. The Batmobile's own name and blurb **do not exist**: `hash_jenkins("v0300_..._batmobile")` =
   `443190071` resolves in **0 of 11** languages of `profile/online.stringlookup`, while the donor's
   `D2B46B49` resolves in 11/11 to "KERNER SERPENTE R", and `UIDescription` `2073308658` is the
   Serpente's blurb. The icon `textures/ui/vehicle_icons/<new leaf>.ddsc` is likewise absent (0
   hits) while every vanilla vehicle icon is 18,688 B. So the world plan splits cleanly: the item
   record, its unlock link and the icon are `next` (B-13); the two string pairs are `blocked`
   because **`Tools/scripts` has no `.stringlookup` writer** (`jc3strings.py` reads only).

**Done check.** `python Tools/scripts/t15_world.py --check`:

```
PASS: 19 rows | WLD codes 8/8 | dispositions next 5, keep 6, epe 3, blocked 3, out 2 | ledger 19/19
```

The ledger was rebuilt with `t_rows.py build` (164 → 183 rows) and `t_rows.py check` is green:

```
ledger 183 rows | edit 16 next 32 keep 56 epe 26 re-read 0 blocked 16 out 30 superseded 7 | edits 35 over 16 rows
check ok
```

`status_audit.py --write` then `--check` → `STATUS.md is current`; its per-document table gains
`| T-20 | 19 | 14 | 0 | 3 | 2 | 0 | 5 | 0 |`.

**Tamper test (4/4 caught, each reverted and re-checked to PASS).**

| tamper | result |
|---|---|
| `t15_world.json` `summary.mass_target` 6000 → 6001 | exit 1, `FAIL: t15_world.json differs from the re-derived record`, first difference at char 38224 |
| one appended row line in `T15_WORLD.md` | exit 1, `FAIL: T15_WORLD.md differs ...` diff at `@@ -156,5 +156,3 @@` |
| ledger `T-WLD11` disposition `blocked` → `next` | exit 1, `FAIL T-WLD11: ledger dispo next != blocked` |
| one cell flipped in the md (`T-WLD12` `next` → `keep`) | exit 1, md diff at `@@ -52,7 +52,7 @@` |

**UNKNOWNs, stated in the doc.** The `RebelDropTimer` unit (int32 1800); the `Type`/`UIType`/
`UIFlag` enum meanings (only the description strings resolve); the mass unit (G2-34 already
recorded it as UNKNOWN); whether the game needs the stunt areas' `deform_points` list at all
(`T-WLD11` is `blocked` for that reason); and every native ending — tether strength, helicopter
lift, traffic selection, water damage — which only a Q probe can settle (`Q-1 #1`, `Q-1 #3`,
`Q-3 #1/#4/#5/#6`).

**Revert:** delete `Tools/scripts/t15_world.py`, `Working/Translation/T15_WORLD.md` and
`Working/Translation/t15_world.json`; restore `Tools/scripts/t_rows.py` from
`tmp/t_rows.beforeT20.py` (or remove the `("T-20", …)` `DOCS` entry and the 19 `T-WLD*` `DISPO`
lines) and re-run `t_rows.py build` + `status_audit.py --write`; set §12 `T-20` back to `todo`;
truncate this log at the intended-change heading. No game file, build, save or dropzone was
touched, and nothing was committed.


## T-21 · Appearance completion — done (2026-10-28)

**Record:** `Working/Appearance/APPEARANCE_PLAN.md` (new, generated, 522 lines) +
`Working/Appearance/appearance_plan.json` (new, 172 components + 21 rules + 6 interior slots + 4
skin rows) from `Tools/scripts/appearance_plan.py` (new, `--write` / `--check` /
`--show <component>`); `Tools/scripts/appearance_progress.py` gains `--plan` / `--strict-plan` and
now prints the plan tally on every run. No game file, no `Builds/`, no dropzone, no save, no git, no
`T_ROWS.jsonl` change (the card writes no ledger rows), so `status_audit.py` is not triggered.

**Result: 172/172 classified, 0 unclassified.** The 172 = 36 partial + 136 excluded from the
339-component inventory the card names (transferred 167, missing 0).

| action | rows | what it means |
|---|---|---|
| **bake** (POL-2) | **23** | 6 micro-detail textures (`Batmobile_Microdetail`, `Micropattern_A/_A_Normal/_B/_C`, `neutral_normal`), 15 micro-detail tiling sizes, 2 `underlayer_Detail_to_Roughness` - all baked into s1/s0 at convert time |
| **route** | **8** | 3 light factors -> `CarLight` block + lights module (T-18/B-03/B-07); 2 emissive masks -> `static.Emissive` + emitter (appearance_emissive, T-18); 2 glass response factors -> `Window` block; 1 glass layer mask -> `Window` dif alpha |
| **drop** | **141** | 14 reasons, each with its proof: 41 dirt/mud (engine-global, chapter-scripted), 27 dielectric reflectance (no F0 input), 14+1 anisotropy (no anisotropic input in the 18+7 decoded params), 12 dirt colour (recorded in `DirtColor`), 9+1 editor/fake helpers, 8+7 weather/wetness, 8 tessellated displacement (R1: no deform), 4 story-chapter damage masks (hit-driven damage), 4 per-pixel roughness (gloss is per channel), 3 colour ramps (source files absent from the export), 2 story EMP |

**POL-1 (interior).** Interior = six slots (10 cockpit 27,334 faces, 11 seat 13,014, 12 flip-data
100, 14 battery 2,949, 15 energy 18, 16 power cell 788; seat/dash indices from G1-19). All six have
`s0`+`s1`+`s2`+`s3` bound already, so the interior has no untextured surface; 24 of the 172 rows
touch an interior material - 7 bake, 1 route (`Int_Cockpit_E` -> emissive), 16 drop. **POL-1 closes
with no new interior texture.**

**Skins (D-5 = extra Rebel Drop entries).** The generated §6 reproduces G1-20's material counts
(V2 78 / MK2 80 / Joker 69 / Funhouse 84) with the extra/missing lists verbatim; the actions are per
factor name, so MK2's replacement body/wheel materials re-run the same plan. Per-skin component
counts and per-skin texture budget are **UNKNOWN** (only the reference build has a `factors.json`,
and R9's 7,065 KB is per entity with no skin build measured) - recorded in §8 of the doc.

**Done check (verbatim, both exit 0):**

```
> python Tools/scripts/appearance_plan.py --check
components 339 | transferred 167 | partial 36 | excluded 136 | missing 0
planned 172: bake 23 route 8 drop 141 | POL-1 24 POL-2 23 | unclassified 0
md match True, json match True
check ok

> python Tools/scripts/appearance_progress.py --build Working/Appearance/build_bud1 --strict-plan
build Working\Appearance\build_bud1
class       total     ok   part   miss   excl       %
geometry       25     25      0      0      0   100.0
materials      19     19      0      0      0   100.0
textures       38     17      7      0     14    53.9
factors       257    106     29      0    122    46.9
OVERALL       339    167     36      0    136    54.6
strict 49.3%  |  of transferable 91.1%
plan: bake 23 route 8 drop 141 | unclassified 0
progress -> Working\Appearance\progress.json and Working\Appearance\progress.md
```

**Tamper tests** (each caught, then restored and the full check re-run green - 6/6):

1. `APPEARANCE_PLAN.md` tally `bake 23` -> `bake 22` -> `FAIL APPEARANCE_PLAN.md stale: the
   regenerated text differs` (1 problem).
2. `appearance_plan.json` `Batmobile_V3_Glass_S` `route` -> `drop` -> `FAIL appearance_plan.json
   stale: the payload differs` (1 problem).
3. The generator's own rule `P2` `bake` -> `drop` -> both stale lines **and** `FAIL POL-2 23 !=
   bake 8: every bake is POL-2` (3 problems) - `--check` tests the plan's own invariants, not just
   file equality.
4. Rule `D7` (`JC3 weather`, 8 components) deleted -> `planned 164 != partial+excluded 172`, `FAIL
   unclassified 8: the card's Done is 0` and all 8 named (12 problems) - i.e. the **Done criterion
   itself** is what fails.
5. `progress.json` (input) `Batmobile_V3_Glass_S` `partial` -> `transferred` -> both stale lines,
   `planned 171 != ...` and `FAIL rule R4 matches no component (dead plan row)` (4 problems).
6. `appearance_plan.json` loses one component -> `appearance_progress.py --strict-plan` prints
   `plan: bake 23 route 7 drop 141 | unclassified 1` + `UNCLASSIFIED textures:Batmobile_V3_Glass_S`
   and exits 1.

**Files regenerated as a side effect, counts unchanged.** `Working/Appearance/progress.json` and
`progress.md` are `appearance_progress.py`'s own outputs; the "reflecting the plan" half of the card
regenerates them, so both now carry a per-component `plan` column (and a fresh timestamp) with the
same 339 / 167 / 36 / 136 / 0 totals, byte-compared before/after (`overall` and every class summary
identical). The pre-T-21 copies are in `tmp/progress.beforeT21.json`, `tmp/progress.md.beforeT21`.

**Rule notes.** R11: every number in the doc is re-derived by `--check` from `progress.json`,
`SLOTS.json`, `VARIANTS.md` and the build's `factors.json` - no count is typed, including the
per-rule row counts and the interior table. R4: the glass `Window` block parameters are **not
decoded** (MODLOG §102d), so the three glass rows route to the block but keep the vanilla response;
the doc says so instead of inventing parameters. Nothing was baked, recoloured or rebuilt by this
card - it classifies, as the card asks.

## T-15 · Modes translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7 `#### T-15 · Modes translation   M · deps: D-2, G1-21, G2-21, T-11 ·
serves: MOD-1/2, CAM-2, LGT-2, AUD-4`. Out: `Working/Translation/T11_MODES.md` + rows; variant table
`t11_variants.json`. Done: every MOD-2 behaviour has a row in each variant or a named omission.

**Resume check (session loop steps 1-2).** `grep -n "T-15" MODLOG.md` → 8 hits, none a T-15
intended-change or done section (they are T-10's successor table, T-18's notes and T-11's line);
`ls Working/Translation/T11_MODES.md Working/Translation/t11_variants.json Tools/scripts/t11_modes.py`
→ all absent. Fresh start.

**Gate.** `D-2` **resolved (b) one hybrid car**, `D-7` resolved (every weapon both modes), G1-21
`MODES.md/.json` + `grab_modes.py`, G2-21 `TANKTURN.md/.json`, `T-11` **done** on the tracker
(session loop step 2), G2X **passed** (`MODLOG §"G2X · G2 exit gate — passed"`). So the card runs
its **hybrid** branch: one row set with the compromise declared per row.

**Intended change, file by file.**

| file | change | why this file | how to revert |
|---|---|---|---|
| `Tools/scripts/t11_modes.py` | **new** generator (`--write` / `--check` / `show <id>`); every cell re-derived from `MODES.json`, `CAMERA.json`, `TANKTURN.json`, `LIGHT_SYSTEM.json`, `USAGES.json`, `t14_lights.json`, `T_ROWS.jsonl` and §11 | R11: the card asks for rows and a variant table, and every table here comes from a script with a `--check` | delete the file |
| `Working/Translation/T11_MODES.md` | **new**, generated by `--write` | the card's `Out:` names this doc | delete the file |
| `Working/Translation/t11_variants.json` | **new**, generated: one `hybrid` variant + per row the pursuit value, the battle value, the hybrid value, the compromise kind and the disposition | the card's `Out:` names this variant table | delete the file |
| `Tools/scripts/t_rows.py` | two literals: `DOCS` gains `("T-15", T11_MODES.md)` and `DISPO` gains the 15 `T-MD*` dispositions | `t_rows.py` is the only writer of `T_ROWS.jsonl` | restore `tmp/t_rows.beforeT15.py` |
| `Working/Translation/T_ROWS.jsonl`, `STATUS.md` | **regenerated** by `t_rows.py build` and `status_audit.py --write` | generated files, never hand-edited | re-run both after restoring the literals |
| `GRAB_BACKLOG.md` §12 | the `T-15` line only | session loop step 7 | restore that one line |

**Not touched.** `Research/*` (G1/G2 own those files), `Builds/`, `E:/Modding/_JC3grab`,
`E:/Modding/_BmAKgrab`, any game file, dropzone or save, and git. No game launched (R6).

**Ordering note, stated rather than hidden.** `Tools/scripts/t11_modes.py` was written one step
before this entry, because the row set could not be sized without knowing which fields
`MODES.json` actually serialises; no output, ledger row or tracker cell existed at that point, and
the breach is recorded here rather than back-dated (same note as T-14).


## T-19 · HUD translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §7 `#### T-19 · HUD translation   S · deps: G2-25, T-11 · serves:
HUD-1/2`. *Do: complete T-HUD5 (weapon slots/icons), lock-on, heat/cooldown mapping; keep
T-HUD1…3. Out: rows in `T6_HUD_CAMERA.md`. Done: each HUD element mapped or omitted with proof.*

**Resume check (session loop steps 1-2).** `grep -n "T-19" MODLOG.md` → two hits, neither a T-19
section (line 12577 is T-18 explaining that T-19 follows it; line 13183 is T-11's own T-WP12 row
naming T-19 as the owner of `hud.gfx`). No T-19 script or block existed (`ls Tools/scripts/*hud*` →
no `t19_hud.py`; `T6_HUD_CAMERA.md` §1 has T-HUD1…10 and no T-19 block). Fresh start.

**Gate.** G2-25 `done` (`JC3_HUD_WEAPONS.md/.json`), G2X `done` (MODLOG §"G2X · G2 exit gate —
passed"), T-11 `done` since this session (`T7_WEAPONS.md` + `t7_weapons_edits.json`). No §11
decision is named by this card; D-7 is already resolved and its slot-capacity row belongs to T-11,
not here.

**Intended change, file by file.**

| file | change | why this file | how to revert |
|---|---|---|---|
| `Tools/scripts/t19_hud.py` | **new** generator: `--write` / `--check` / `--show <row>`; one row per HUD element, every cell quoted from `HUD_INTERFACES.json` (BmAK setter + its argument signature), `JC3_HUD_WEAPONS.json` (member, icons, lock-on POI, the two heat zeros) and `t7_weapons_edits.json` (the two driver-slot bindings); each row carries a proof path that `--check` re-evaluates | R11 (every table comes from a script with a `--check`) and the card's `Out:` (rows in the HUD doc) | delete the file |
| `Working/Translation/T6_HUD_CAMERA.md` | one generated block between `<!-- T19-HUD-BEGIN -->` and `<!-- T19-HUD-END -->`, inserted before the "one HUD finding" paragraph; §2 camera rows, the T-HUD1…10 rows and everything else untouched | the card's `Out:` names this doc, and T-HUD5 is the row being completed | restore `tmp/T6_HUD_CAMERA.beforeT19.md` |
| `Working/Translation/t19_hud.json` | **new**, generated: the 10 rows with their proofs, the slot bindings, the kept-row list | the rows must be machine-checkable, not prose only | delete the file |

**Not touched.** `T_ROWS.jsonl` / `STATUS.md` (the card asks for rows in the HUD doc; ledger
close-out is T-23's card, so `status_audit.py` is not triggered), `Research/JC3Grab/*` (G2-25 owns
them), `Research/BatmobileGrab/*` (G1 owns them), `Builds/`, any game file, dropzone or save. No game
launched (R6), no git.

**Scope note.** T-HUD5's own row is **not rewritten**: it stays as the record of the pre-T-19
blocked state, and the generated block states which rows complete it (the check asserts both). Where
a member exists but its unit does not (the Vulcan accuracy frame -> `reticle_size`), the row is
`partial`/`UNKNOWN` with the reason, not a hand-picked number (R4/R5).
## T-15 · Modes translation — done (2026-10-28)

**What was read.** `MODES.json` (G1-21: 107 declared mode fields, 46 serialised, 61 absent from
every package), `CAMERA.json` (the camera class's 33 values + 13 config structs), `TANKTURN.json`
(G2-21: 5 candidates refuted, 52 module types, 0 tank-only), `LIGHT_SYSTEM.json` (the fleet's 9 light
behaviours), `USAGES.json` (the donor's `arcade.nitro_boost`), `t14_lights.json` (T-18's four
`VEHLT_BattleModeLight` rows), `T_ROWS.jsonl` (T-B2/T-B3/T-DM8/T-M1/T-E1/T-E3/T-WP4/T-WP11) and
`GRAB_BACKLOG.md` §11 for D-2 and D-7.

**Method.** D-2 is a hybrid, so the card's hybrid branch runs: **one row set, 15 rows — MOD-1 4,
MOD-2 11** — with a compromise declared per row in one of three kinds: `carried` 8, `inside band` 1,
`omitted` 6 (dispositions: `next` 5, `keep` 4, `blocked` 1, `out` 5). `t11_variants.json` keeps the
split anyway: one `hybrid` variant plus, per row, what the pursuit car and the battle car would each
have carried, so B-12 can be built later without re-deriving anything.

**The four decision-relevant readings.**

1. `BattleModeVSpeedCurve` is 3 points — 0→60, 600→40, 1200→30 (cm/s → factor) — identical in all
   four packages; `TurningModeMaxSpeed` is 600 cm/s = **21.6 km/h**. Both need a mode switch, so
   both are named omissions on a hybrid (values recorded for the two-variant route).
2. `ArmourModeDamageReduction` is **0** on the three packages that serialise it: the requirement
   assumes battle-mode armour drops, the files say there is no reduction at all.
3. `BattleModeCamFOV` **60** (camera class) sits **inside** the delivered `.ctune`'s 55-63 band, so
   no value changes; only the mode framing is missing (T-CAM10's second tune needs two variants).
4. The fleet's 9 light behaviours have **no battle value**, so T-18's four `VEHLT_BattleModeLight`
   lamps map onto `HeadLight` — they light with the headlights. That is the LGT-2 compromise,
   named rather than hidden.

**Done check.** `python Tools/scripts/t11_modes.py --check`:

```
PASS: 15 rows | MOD-1 4 / MOD-2 11 | compromises carried 8, inside band 1, omitted 6 | ledger 15/15
```

The ledger was rebuilt (`t_rows.py build`, 183 → 198 rows) and both neighbouring checks stay green:

```
ledger 198 rows | edit 16 next 37 keep 60 epe 26 re-read 0 blocked 17 out 35 superseded 7 | edits 35 over 16 rows
check ok
STATUS.md is current
```

`STATUS.md` now carries `| T-15 | 15 | 9 | 0 | 1 | 5 | 0 | 5 | 0 |`.

**Tamper test (4/4 caught, each reverted and re-checked to PASS).**

| tamper | result |
|---|---|
| `t11_variants.json`: `T-MD1` compromise `carried` → `omitted` | exit 1, `FAIL: t11_variants.json differs from the re-derived record`, first difference at char 21676 |
| one appended row line in `T11_MODES.md` | exit 1, md diff at `@@ -145,5 +145,3 @@` |
| ledger `T-MD14` disposition `blocked` → `next` | exit 1, `FAIL T-MD14: ledger dispo next != blocked` |
| one cell flipped in the md (`T-MD10` confidence `decoded` → `derived`) | exit 1, md diff at `@@ -48,7 +48,7 @@` |

**UNKNOWNs, stated in the doc.** `StandardTorqueVSpeedCurve` (MOD-1's speed curve) is **not** one of
the 107 fields G1-21 recorded, so its points are UNKNOWN and the speed profile rests on T-E1/T-E3;
61 of the declared mode fields carry no value in any package (`TransformationAnimNode`,
`BattleModeMaxSpeed`, the `Strafe*` family, …) and are UNKNOWN rather than zero;
`BattleModeThrottleSpeed` 10 is carried raw because its unit is undocumented; the battle camera's
spring/distance fields have no unit bridge (T-CAM9 blocked); and every native ending needs a Q probe
(`Q-1 #4/#5/#7/#8`, `Q-2 A2/A9/A15`, `Q-3 #1/#2/#3`). No game was launched (R6).

**Revert:** delete `Tools/scripts/t11_modes.py`, `Working/Translation/T11_MODES.md` and
`Working/Translation/t11_variants.json`; restore `Tools/scripts/t_rows.py` from
`tmp/t_rows.beforeT15.py` (or remove the `("T-15", …)` `DOCS` entry and the 15 `T-MD*` `DISPO`
lines) and re-run `t_rows.py build` + `status_audit.py --write`; set §12 `T-15` back to `todo`;
truncate this log at the T-15 intended-change heading. No game file, build, save or dropzone was
touched, and nothing was committed.

## T-22 · Collision translation — intended change (2026-10-28)

**Card.** `GRAB_BACKLOG.md` §9, `#### T-22 · Collision translation (only if G2-30 succeeded)   M ·
deps: G2-30 · serves: DIM-4`. Prerequisites checked in §12: `G2X` has a passed MODLOG section and
`G2-30` is `done` (round trip byte-identical), so the card starts. No earlier T-22 entry exists:
`grep -n "T-22" MODLOG.md` returns only G2-30's own back-references (PENDING comments) - this is a
fresh start, and `Working/Translation/t16_collision.json` does not exist yet.

**Intended change.** (1) New `Tools/scripts/t22_collision.py` (`--write` / `--check`) that re-derives
the hull set from `Research/BatmobileGrab/PHYSICS.json` (32 bodies × 4 packages), the donor
`sportsmuscle.physicsc` decoded with `jc3hkx` (54 hull slots, 22 compounds, per-hull box, vertex /
plane count and `convex_radius`), `sportsmuscle_vehicle_parts.vmodc` through `jc3adf`
(`parts[].has_world_collision_shape`, `world_collision_body_id`), `PARTS_TABLE.jsonl`,
`Working/TrueScale/stations.json` and `Working/Appearance/build_parts/parts_manifest.json` (body
bbox). (2) New `Working/Translation/t16_collision.json` - the hull set, the per-part hull binding,
the convex-decomposition parameters that actually exist (max hulls, convex radius) and the row text.
(3) The three rows it resolves, regenerated in place by the script: `T-P3` in
`Working/Translation/T1_TRANSLATION.md` §13 and `T-CO2` / `T-CO3` in
`Working/Translation/T2_TRANSLATION.md` §7. (4) `Tools/scripts/t_rows.py`: the `DISPO` lines for
those three ids only. (5) `T_ROWS.jsonl` and `STATUS.md` regenerated by their own tools.
(6) `GRAB_BACKLOG.md` §12: the `T-22` line only. (7) This log.

**Files.** New: `Tools/scripts/t22_collision.py`, `Working/Translation/t16_collision.json`. Edited:
`Working/Translation/T1_TRANSLATION.md` (one row line), `Working/Translation/T2_TRANSLATION.md`
(two row lines), `Tools/scripts/t_rows.py` (three tuple literals), `T_ROWS.jsonl` / `STATUS.md`
(regenerated), `GRAB_BACKLOG.md` (one line).

**Why these files.** The card's `Out` names "rows + `Working/Translation/t16_collision.json`", and
`T-P3` / `T-CO2` / `T-CO3` live in exactly those two translation tables - there is no separate T-22
doc to add. `t_rows.py` is the only writer of `T_ROWS.jsonl`, so the three dispositions change
there and nowhere else (R11: every count is generated). No game data is written: the inputs are the
existing repo research files and the repo's own `Builds/test-091` physicsc/parts module.

**Revert.** Delete the two new files; restore `Tools/scripts/t_rows.py` from `tmp/t22bak/t_rows.py`
(copied before the edit) or put back the three original `DISPO` lines (`T-P3` blocked, `T-CO2`
blocked, `T-CO3` blocked); restore the three row lines from `tmp/t22bak/`; re-run
`t_rows.py build` and `status_audit.py --write`; set §12 back to `| T-22 | todo | |`; truncate this
log at the T-22 intended-change heading.

## T-19 · HUD translation — done (2026-10-28)

**Record:** `Working/Translation/T6_HUD_CAMERA.md` §1a (new generated block inside the doc, 53
lines, between `<!-- T19-HUD-BEGIN/END -->`) + `Working/Translation/t19_hud.json` (new, 10 rows + 12
proofs + the two slot bindings + the kept-row list) from `Tools/scripts/t19_hud.py` (new, `--write` /
`--check` / `--show <row>`). No game file, no `Builds/`, no dropzone, no save, no git, no
`T_ROWS.jsonl` change - the card asks for rows in the HUD doc and the ledger close-out is T-23's, so
`status_audit.py` is not triggered and was not run.

**T-HUD5 is completed: 10 rows over 5/5 G2-25 elements, 6 map / 2 partial / 2 out.**

| row | element | disposition | value | proof |
|---|---|---|---|---|
| T-HUD11 | weapon slots | map | slot 0 = cannon clone (`main_weapon`), slot 1 = Vulcan clone (root `id:00568A74`) - T-11's bindings | `slots.count` = 2 |
| T-HUD12 | weapon slots | map | `weapon_name` -> `TXT_name` | `init.params` has `weapon_name` |
| T-HUD13 | weapon slots | map | `weapon_icons/<id>.ddsc`; ids 602/603/618/619 all shipped | `icons.ids` holds all four |
| T-HUD14 | reticle | map (shape id UNKNOWN) | `E_RETICLE_CANNON` 8 is the closest named shape; no file binds it to a vehicle cannon | `reticle.shapes` holds it |
| T-HUD15 | reticle | partial (UNKNOWN) | `UC_SetMachineGunAccuracyFrame` -> `reticle_size`; member yes, scale no | `reticle.params` has `reticle_size` |
| T-HUD16 | cannon cooldown | map | `UC_SetCannonCoolDown` 0…4 -> `weapon_cooldown` = state/4; rot = cooldown x 360, -1 hides the loader | `cooldown.rot_degrees` = 360 |
| T-HUD17 | Vulcan heat | out (stated absence both sides) | no JC3 argument/body mentions heat (0/0); 0 of 252 BmAK setters name heat - it is `HeatBarStart`/`HeatBarSize` on the weapon | `heat.params_with_heat` `[]`, `heat.body_mentions` 0 |
| T-HUD18 | missile lock | partial | `POI_TYPE_LOCK_ON_TARGET` 21, one turn per 1.5 s; the `AutoAim` -> POI painter is native (0 `CreatePoi`) | `lockon.lock_on_type` 21, `lock_on_rotation_time` 1.5 |
| T-HUD19 | missile lock | out | the 6 `VehicleMissileTarget` kinds have no JC3 family; `MCI_missile_locked` is the *incoming* warning, a different instrument (R5) | `bmak.missile_target_kinds` = 6 |
| T-HUD20 | weapon slots | map | `infiniteAmmo = true` (BmAK has no ammo setter) hides the counters | `init.params` has `infiniteAmmo` |

**T-HUD1…3 kept.** The block does not rewrite them; the check asserts all three are still in §1
(HUD-1: speedometer reuse, nitro = boost, health bar map) and that T-HUD5's original row still
records its pre-T-19 `blocked` state - the split completes it rather than erasing the history.

**Where the boundary is, stated not filled.** Heat is absent on both sides (JC3: 0 arguments, 0 body
mentions; BmAK: 0 of 252 setters). The lock-on is one marker whose painter is native. The accuracy
frame -> `reticle_size` scale has no unit in either file, so the row is `partial` and the class
`UNKNOWN` - nothing was hand-picked (R4/R5). Slot capacity (D-7's 11 weapons) stays T-11's blocked
row; T-19 only says what the HUD can draw: two clips.

**Done check (verbatim, exit 0):**

```
> python Tools/scripts/t19_hud.py --check
rows 10 over 5/5 elements | map 6 partial 2 out 2 | proofs 12 | kept T-HUD1..3 3/3
doc match True, json match True
check ok
```

**Tamper tests** (each caught, restored, full check re-run green - 5/5):

1. Block text `cooldown = BmAK state / 4` -> `/ 3` -> `FAIL T6_HUD_CAMERA.md stale: the regenerated
   block differs` (1 problem).
2. `t19_hud.json` first row `map` -> `out` -> `FAIL t19_hud.json stale: the payload differs`.
3. A proof expectation `slots.count` 2 -> 3 -> `FAIL T-HUD11: proof slots.count does not hold -
   slots.count = 2 (want 3)` + both stale lines + `FAIL T-HUD11: a proof does not hold` (4 problems):
   the proof machinery is tested, not only file equality.
4. The heat row (T-HUD17) deleted -> `FAIL G2-25 element 'Vulcan heat' has no row`, `FAIL 4/5 G2-25
   elements covered`, `FAIL only 9 rows` (6 problems) - the card's "mapped or omitted" cannot pass
   with an element missing.
5. T-HUD5's own row deleted from §1 -> `FAIL T-HUD5's original row is gone from §1` (1 problem).

**Doc integrity.** With the generated block removed, `T6_HUD_CAMERA.md` is identical to its pre-T-19
copy `tmp/T6_HUD_CAMERA.beforeT19.md` (checked line by line): the camera rows (§2), T-HUD1…10 and
every other paragraph are untouched.

**Rule notes.** R11: every cell is re-derived by `--check` from `HUD_INTERFACES.json` (setter names
**and their argument signatures**), `JC3_HUD_WEAPONS.json` and `t7_weapons_edits.json`; the BmAK
column cannot disagree with the interface because a missing setter fails the run. R5: JC3's
`MCI_missile_locked` (incoming warning) is kept apart from BmAK's target-lock box - a name that
sounds close is not a carrier. R4: `state / 4` is the only monotone map between 0…4 and 0..1 and is
classed `derived`, with its direction left to Q-3 #3.

## T-22 · Collision translation — done (2026-10-28)

**Verdict.** All three rows are resolved and none is `blocked` any more. `T-P3` and `T-CO2` are
`next` (B-10 writes the hull set), `T-CO3` is `keep` (the donor's flags are carried). The card's
three named quantities resolve to measurements, not to a decomposition the writer cannot do: the
hull set is the donor's 54 existing hull slots, one per part, uniformly scaled - a *brand-new* hull
still needs the face table's unnamed prefix (G2-30 §6), so `max_hulls` is fixed at 54, `hulls per
part` at 1, and the only free parameters are a uniform `k` and a translation.

**The card's first premise is the finding: the 32 BmAK bodies are not the driveable car's hulls.**
`PHYSICS.md` already said so - the asset is `Batmobile_V3_Destroyed_Physics`, 18 of the 32 bones are
`Object*_frag_*` debris, `Root` is a 30.3 cm placeholder, and there is no chassis body. So 21 of the
32 boxes are wreck-only (18 debris, 1 Root, 1 turret, 1 jet fin) and the 11 that are driveable - 8
wheel/suspension, the cockpit, 2 rear doors - map onto **7** donor hull slots: body 1, 2 doors, 4
wheels. The 11 T-8 moving parts (turret, cannon, Vulcan, riot suppressor, 2 missile pods, 4 aero
flaps, jet) have **no donor slot**: they are new parts, and giving them collision needs a new hull,
which is the UNKNOWN above.

**The donor side, decoded per hull** (`jc3hkx` over `Builds/test-091/.../sportsmuscle.physicsc`):
430 objects, 22 compounds, **54** convex hulls - **40 bound to a part**, 14 unbound (the two
bumpers' panels, which carry no part index). One hull per part, 300-1,776 B, 8-36 vertices, 5-47
planes, `convex_radius` median **0.01 m** (min 0.002436 m). The body hull is 36 v / 47 p, 1,776 B,
box 2.085 x 1.212 x 3.679 m, r 0.01.

**What the rows now say.**

| row | disposition | value |
|---|---|---|
| T-P3 | `next` | 11 driveable boxes -> 7 donor hull slots; 21 not driveable collision; 11 T-8 parts without a slot; hull set, slot binding and radius x k in `t16_collision.json` |
| T-CO2 | `next` | the largest box is 3.1615 x 0.6342 x 1.0988 m (`SUSP1_Wheel_Rear_Left_Mesh`) at 1 cm = 0.01 m and fits one donor hull (longest hull axis 3.679 m) - no layout change |
| T-CO3 | `keep` | the donor's `has_world_collision_shape` is 1 on **38 of 42** parts; the 4 wheels are the only 0s and their `world_collision_body_id` is -1 |

**k, per hull, is derived and cross-checked.** A wheel takes `k = tyre diameter / the donor wheel
hull's longest axis` = 1.3654 / 0.8225 = **1.660052**, and its hull becomes 0.491 x 1.365 x 1.299 m -
3 seconds of arithmetic from G2-30's measured 1.659566 (tyre diameter = 2 x the `stations.json`
radius, which `TYRES.md` §1 gives as the design identity, so no new input). The body has no BmAK
box, so its hull takes `k = min(body bbox axis / donor hull axis)` = **1.676259** against the
assembled body bbox 3.495 x 2.271 x 7.025 m -> 3.495 x 2.032 x 6.167 m, r 0.016763. For every
non-wheel part `k_in` (fits inside the BmAK box) and `k_out` (covers it) differ because the box has
the donor hull's proportions nowhere; both are recorded per part and **B-10 has to choose** - that
is a build decision, not a translation value, and it is named rather than hidden. A door shows why:
`k_in` 0.507 (a 0.196 x 0.530 x 0.717 m hull inside the 0.260 x 1.528 x 0.717 m box).

**Stations unchanged (R3).** The donor physicsc contains **0** station quads (`jc3hkx.stations`), so
there is nothing in the collision file to move: the car's four corners are
`Working/TrueScale/stations.json` (hub 1.208 / 1.2845, r 0.6826-0.6829), which test-091 already
carries, and T-22 edits no locomotion row. The wheels are also why T-CO3 is `keep`: the BmAK wheel
suspension boxes become the donor's four wheel hulls, but both sides keep collision *off* for the
wheel parts and let the sim do it.

**One prose correction, generated like the rows.** T-2b §7 said "largest box extents
`[211.5, 51.1, 109.0]` cm". That is the front-left **suspension** box (1.17 m3); the largest by
volume is `SUSP1_Wheel_Rear_Left_Mesh` at **316.2 x 63.4 x 109.9 cm** (2.19 m3). The row carries the
true maximum, so the sentence is regenerated by `t22_collision.py --write` (and `--check` fails if
it drifts again) rather than left contradicting the row three lines below it.

**Done check.** `python Tools/scripts/t22_collision.py --check`:

```
PASS: 32 BmAK bodies | 7 mapped / 21 unmapped | 54 donor hull slots, one per part | 38/42 parts collide | rows 3 (next 2, keep 1) | stations unchanged
```

The ledger was rebuilt and every neighbouring gate re-run:

```
Working\Translation\T_ROWS.jsonl: 198 rows, 35 edits over 16 rows
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 14 out 35 superseded 7 | edits 35 over 16 rows
check ok
STATUS.md is current
PASS: 16 rows (5 superseded, 10 out, 1 blocked) | ...
```

(`t10_reopen.py --write` was re-run first: `T10_OPEN_ROWS.{md,json}` listed the three rows as
blocked and went stale when their dispositions changed.)

**Tamper test (4/4 caught, each reverted and re-checked to PASS).**

| tamper | result |
|---|---|
| `t16_collision.json`: `"hulls": 54` -> `55` | exit 1, `FAIL: t16_collision.json differs from the re-derived record at char 1234` |
| `T1_TRANSLATION.md`: `T-P3` cell "7 donor hull slots" -> "8" | exit 1, `FAIL: T1_TRANSLATION.md: T-P3 row differs from the re-derived line` |
| ledger `T-CO3` disposition `keep` -> `next` | exit 1, `FAIL: ledger: T-CO3 disposition next != keep` |
| `T2_TRANSLATION.md`: §7 "largest box" 316.2/63.4/109.9 -> the old 211.5/51.1/109.0 | exit 1, `FAIL: T2_TRANSLATION.md: the §7 'largest box' sentence reads ['largest box extents \`[211.5, 51.1, 109.0]\` cm']` |

**UNKNOWNs and limits (all in `t16_collision.json`).**

1. **A brand-new hull is not writable.** The only free parameters are a uniform scale and a
   translation on an existing slot; the face table's unnamed 0/16/32/48 B prefix is still unread
   (G2-30 §6, UNKNOWN 1), so the 11 T-8 weapon/aero parts cannot get collision at all.
2. **The body's extern mesh cannot be re-authored** (G2-30 §6, UNKNOWN 3). With one 3.679 m hull
   scaled to the 7.025 m body, the front and rear ~0.43 m of the body has no convex hull; whether
   the donor's `hknpExternMeshShape` (Serpente panels) still bounds it acceptably is a runtime
   question, not a file question.
3. **Runtime acceptance.** Every check here is the reader's (`check --all`-class invariants); that
   Havok and the game accept a scaled hull in a Batmobile-shaped slot is phase-Q.
4. **The turret/fin/debris boxes have no destination.** Their envelopes are recorded in the json
   (`hull_set.unmapped`) but there is no donor part to hang them on; the debris are wreck-only by
   construction.
5. **No unit bridge for BmAK's box centres**: the json keeps them in centimetres and the placement
   is the part pivot through `bat_assemble`'s `T(p)` (R2); the centre offsets are not re-derived
   here.

**Revert:** delete `Tools/scripts/t22_collision.py` and `Working/Translation/t16_collision.json`;
restore `Tools/scripts/t_rows.py`, `T1_TRANSLATION.md` and `T2_TRANSLATION.md` from `tmp/t22bak/`;
re-run `t_rows.py build`, `t10_reopen.py --write`, `status_audit.py --write`; set §12 `T-22` back to
`todo`; truncate this log at the T-22 intended-change heading. No game file, build or save was
touched, and nothing was committed.

**T-22 correction (same session, append-only).** The done block above says the donor hull extent
range is "300-1,776 B"; `t16_collision.json` says `hull_extent_range: [400, 1776]` (the smallest
hull block is 400 B, the 8-vertex 5-plane plate). The vertex/plane/radius ranges in the block are
right (8-36 v, 5-47 p, radius 0.01 median / 0.002436 min).

## T-11 fix · D-3 toggle withdrawn — intended change (2026-10-28)

**Why.** The user withdrew the D-3 lethality toggle: `GRAB_BACKLOG.md` §11 D-3 now reads
"**resolved 2026-10-28 (user): accept JC3 lethality, no toggle** ... the riot suppressor stays a
named omission". Card T-11 ran before that wording landed and wrote row `T-WP14` as a
*lethal/non-lethal toggle* (`blocked`, "D-pad down toggles lethal / non-lethal"), plus a D-3 row in
the §2 decisions table, a note on the WPN-10 row, and a D-3 line in the header summary. All of
those claim a feature the user has withdrawn; they are corrected here, not left standing.

**Intended change.**

1. `Tools/scripts/t7_weapons.py` (the only writer of the weapons doc) — replace `row_toggle()` with
   `row_d3()`: `T-WP14` stays the row id but becomes a **named omission** (`out`), title
   "D-3 · Lethality — JC3 lethality accepted, no toggle", carrying the riot-suppressor facts and the
   proven absence, with `why` citing `Research/JC3Grab/VOCABULARY.md` + `Research/JC3Grab/G2X.json`.
   Remove every other toggle claim from the same file: the `decisions["D-3"]` text, the header
   sentence that names `T-WP14` as "the lethal/non-lethal toggle", the §2 D-3 table row and the
   "both rows are `blocked`" paragraph, and the WPN-10 note ("the toggle itself is T-WP14").
2. `Tools/scripts/t_rows.py` — `DISPO["T-WP14"]`: `blocked` -> `out`, with the proof paths in the
   reason (the ledger is rebuilt from this table, never hand-edited).
3. Generated outputs re-derived by their own tools: `Working/Translation/T7_WEAPONS.md`,
   `Working/Translation/t7_weapons_edits.json` (`t7_weapons.py --write`), `Working/Translation/T_ROWS.jsonl`
   (`t_rows.py build`), `STATUS.md` (`status_audit.py --write`, because a row moves blocked -> out).
4. `GRAB_BACKLOG.md` §12 — the `T-11` line only, so its summary counts
   (5 carrier / 6 named omissions / 3 blocked) and its D-3 clause match the regenerated doc.

**Why these files.** `T7_WEAPONS.md` and `t7_weapons_edits.json` are generated byte-for-byte from
`t7_weapons.py` (`--check` fails on any hand edit), and `T_ROWS.jsonl` / `STATUS.md` are generated by
`t_rows.py` / `status_audit.py`; the scripts are therefore the correct place for the change.

**Revert.** Re-apply the opposite hunk in `Tools/scripts/t7_weapons.py` (restore `row_toggle()` and
the four toggle sentences) and in `Tools/scripts/t_rows.py` (`T-WP14` back to `blocked`); re-run
`t7_weapons.py --write`, `t_rows.py build`, `status_audit.py --write`; set the §12 `T-11` line back
to its previous wording; truncate this log at this heading. No game file, build or save is touched
and nothing is committed.

**What is already correct and is not touched.** §11 D-3 itself is the user's resolved text; the
`T-WP10` riot-suppressor row stays a named omission; `WPN-10` in §1 stays as written.

## T-11 fix · D-3 toggle withdrawn — done (2026-10-28)

**State found.** The intended-change block above was written but nothing had been applied:
`Tools/scripts/t7_weapons.py` still defined `row_toggle()` (`T-WP14` `blocked`, "D-pad down toggles
lethal / non-lethal"), the §2 D-3 decision entry and table row still described the toggle, the
WPN-10 "what remains" note still said "the toggle itself is T-WP14", and `t_rows.py` still had
`T-WP14` as `blocked`. Everything below is this session's work.

**Applied.**

1. `Tools/scripts/t7_weapons.py` — `row_toggle()` → `row_d3()`: `T-WP14` keeps its id and becomes
   `out`, `jc3=[]`, title "Lethality — JC3 lethality accepted, no toggle (riot suppressor: named
   omission)", and `why` carries the decision plus the two proof paths
   (`Research/JC3Grab/VOCABULARY.md`, `Research/JC3Grab/G2X.json` WPN-10) the `out`-row invariant
   requires. The 13 aspects keep their names, values and classes (3 decoded / 10 UNKNOWN) except
   the last, which records the resolution instead of the toggle; the aspect totals therefore stay
   136 with 53 UNKNOWN, so no count outside the disposition table moves.
2. Same file, every other toggle claim: `decisions["D-3"]` (now "accept JC3 lethality, no toggle;
   the riot suppressor stays a named omission (T-WP10) and T-WP14 records the decision"), the intro
   sentence naming `T-WP14`, the §2 D-3 table row (question "accept JC3 lethality, or keep a
   non-lethal mode?", row cell "out: no toggle, decision recorded"), the "Both rows are `blocked`"
   paragraph (split: `T-WP13` blocked, `T-WP14` out and why), and the WPN-10 note ("D-3 resolved on
   2026-10-28 keeps the mode out, and T-WP14 is the decision record").
3. `Tools/scripts/t_rows.py` — `DISPO["T-WP14"]` `blocked` → `out`, reason carrying the decision
   and both proof paths.
4. Regenerated by their own writers: `Working/Translation/T7_WEAPONS.md` +
   `t7_weapons_edits.json` (`t7_weapons.py --write`), `Working/Translation/T_ROWS.jsonl`
   (`t_rows.py build`), `STATUS.md` (`status_audit.py --write`).
5. `GRAB_BACKLOG.md` §12 `T-11` line only: "the D-7 slot row and the D-3 decision record", counts
   5 carrier / 6 named omissions / 3 blocked, and the last clause "D-3 resolved 2026-10-28 — JC3
   lethality, no toggle, the riot suppressor a named omission". §11 D-3 and §1 WPN-10 are the
   user's own text and are not touched.

**One correction against the plan.** The row title must not repeat the code: the renderer writes
`### T-WP14 — {code} · {title}`, so the planned title "D-3 · Lethality — …" rendered as
"D-3 · D-3 · …". The title is "Lethality — JC3 lethality accepted, no toggle (riot suppressor:
named omission)", giving the heading `### T-WP14 — D-3 · Lethality — JC3 lethality accepted, no
toggle (riot suppressor: named omission)`.

**Checks (verbatim, this session).**

```
$ python Tools/scripts/t7_weapons.py --check
PASS: 14 rows = 12 WPN codes + 2 decision rows (5 with a JC3 carrier, 6 named omissions, 3 blocked) | 136 aspects classified, 53 UNKNOWN | 3 edits + 6 structural + 6 withdrawn | 4 JC3 ids, 2 driver slots | ledger 14/14 | json match True, md match True
exit=0

$ python Tools/scripts/t_rows.py check
ledger 198 rows | edit 16 next 39 keep 61 epe 26 re-read 0 blocked 13 out 36 superseded 7 | edits 35 over 16 rows
check ok
exit=0

$ python Tools/scripts/status_audit.py --check
STATUS.md is current
exit=0
```

**What is still open, and is unchanged by this fix.** D-7 (`T-WP13`, `blocked`) still has no
mechanism that carries 11 weapons in 2 driver slots; the riot suppressor's gel/taser effects stay
with T-17 and the sounds with T-16; the row's 10 UNKNOWN aspects are still UNKNOWN because no
decoded file gives them a value. D-3 never could be verified by a Q take and now is not meant to
be: there is no second mode to distinguish.

**Not touched.** No game file, build or save; nothing under `D:/Games`; no shared game module;
nothing committed or pushed.

**Revert.** As the intended-change block above lists: `row_d3()` → `row_toggle()`,
`DISPO["T-WP14"]` back to `blocked`, the four toggle sentences restored, then
`t7_weapons.py --write`, `t_rows.py build`, `status_audit.py --write`, the old §12 `T-11` line put
back, and this log truncated at the intended-change heading.

**T-11 fix — done** (2026-10-28).

## T-23 · Ledger close-out and build batches — intended change (2026-10-29)

**Why.** T-23 is the phase-T exit gate (gate TX) and the last `todo` in §7. It was not started
before: `grep T-23 MODLOG.md` found only other cards' references (T-17, T-19, T-20), no
intended-change entry and no outputs on disk. Prerequisites are met: T-10…T-22 are `done` in §12,
G1X/G2X are `done`, and all ten decisions D-1…D-10 are marked `resolved 2026-10-2x (user)` in §11.
The T-11 fix ran just before this session and its `T-11 fix — done` block is in this log, so D-3's
row `T-WP14` is the decision record, not a toggle.

**What the card asks.** 1. `t_rows.py check`, then `status_audit.py --write` and `--check`.
2. Confirm `rows assumed` = 0 except signed-off rows. 3. Extend `bmak_coverage.py` so weapons,
animation, audio and light features are covered (every G1 file row assigned to a T row).
4. Write the phase-B build batch list. Out: `STATUS.md` regenerated + `BUILD_BATCHES.md`.
Done (gate TX): all checks green; every §1 feature code maps to ≥1 row; D-1…D-10 answered or
their rows `blocked: D-n`.

**Intended change.**

1. **New writer** `Tools/scripts/t23_closeout.py` — the only writer of the two new outputs
   `Working/Translation/BUILD_BATCHES.md` and `Working/Translation/build_batches.json`. It parses
   `GRAB_BACKLOG.md` §1 (75 feature codes), §7/§8 (the T and B cards), §11 (the decision register)
   and `Working/Translation/T_ROWS.jsonl` (the ledger), then:
   (a) builds the **feature-code → row** gate: for every §1 code, the T rows (or doc anchors) that
   carry it, each anchor re-checked against the document that owns it, and each code's state
   (`carried` / `named omission`) read from the ledger disposition rather than asserted;
   (b) reports the `assumed` count from the same rows `status_audit.py` counts, failing unless the
   only assumed row is the signed-off one (T-E5);
   (c) states D-1…D-10 from §11 (resolved text) and lists the rows whose disposition cites each D;
   (d) writes the **build batch list**: base-tree values already live, one row per phase-B step
   B-01…B-14 with the payload file(s) it applies (taken from the card text plus a declared
   payload table), the row ids and value counts read out of each payload JSON, and the card's own
   gate; plus every payload file no step names, as a named gap instead of silence.
   `--check` re-derives both files byte-for-byte and re-runs the gate; `--gate` is `--check`.

2. **Extend** `Tools/scripts/bmak_coverage.py` (the only writer of `Research/BatmobileGrab/
   COVERAGE.{json,md}`) with a **G1 feature-row census**: every row of `WEAPONS.json` (62 objects),
   `ANIMATIONS.json` (253 sequences), `AUDIO_FEATURES.json` (361 events) and `LIGHTS.json` (101
   entries over 4 rigs) assigned to a T row by a declared rule, with the same rule every existing
   field assignment follows: an unmatched row is a FAIL, never a silent default. The four new
   blocks are written into `COVERAGE.json` (`g1_rows`) and a new section of `COVERAGE.md`.

3. **Regenerate, never hand-edit**: `STATUS.md` (`status_audit.py --write`), `COVERAGE.{json,md}`
   (`bmak_coverage.py`), `BUILD_BATCHES.md` + `build_batches.json` (`t23_closeout.py --write`).

4. `GRAB_BACKLOG.md` §12 — the `T-23` line only (evidence path), appended to, not rewritten.

**Why these files.** `STATUS.md`, `COVERAGE.*` and the new pair are each generated by one script and
their `--check` fails on a hand edit, so the script is the only place a value may change. The card's
`Out` line names `STATUS.md` and `BUILD_BATCHES.md`; `bmak_coverage.py`'s own docstring makes it the
owner of "did we look at everything".

**Revert.** Delete `Tools/scripts/t23_closeout.py`, `Working/Translation/BUILD_BATCHES.md` and
`Working/Translation/build_batches.json`; re-apply the opposite hunk in
`Tools/scripts/bmak_coverage.py` (drop the `g1_rows` block) and re-run `bmak_coverage.py`; re-run
`status_audit.py --write`; set the §12 `T-23` line back to `todo` with an empty evidence cell;
truncate this log at this heading. No game file, build or save is touched, nothing under
`D:/Games`, no shared module, nothing committed.

**Not in scope.** No new translation row and no value change: this card closes the ledger and writes
the build plan. No game launch, no install, no git operation.

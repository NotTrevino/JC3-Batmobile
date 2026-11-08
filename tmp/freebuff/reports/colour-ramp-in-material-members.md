# Which BmAK material members reference a colour ramp — slot, bound texture, and the parameters beside it

2026-11-06. Read-only: `Research/BatmobileGrab/` (`COLOUR_PARAMS.md/.json`, `COLOUR_FUNCTIONS.json`,
`COLOUR.md/.json`, `SLOTS.md/.json`, `MATERIALS.md`, `SKINS.md`, `TEXTURES.md`, `objects.jsonl`,
`COCKPIT.md/.json`, `ASSETS.md`). No game process, no package written.

Labels: **decoded** = a tag/offset in the named file; **derived** = arithmetic or a format rule over
decoded bytes, shown; **UNKNOWN** = searched and absent, with the settler named.

---

## 0. First finding (as asked), then the full set

The ramp is a **`Colour_Ramp_Map` texture parameter** — one slot, declared by every Batmobile paint
master and overridden per material instance. The body's own material chain resolves it to
`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`; the interior shell uses the same texture and the
seat uses `Maps.Batman_BM3_V2_Leather_Ramp`; the wheel-light/emissive material uses
`Engine.Batmobile_V3_Body_ColourRamp`.

| what | where |
|---|---|
| slot name | `Colour_Ramp_Map` (a `MaterialExpressionTextureSampleParameter2D`, tag `NameProperty @284`, value `ObjectNCRProperty @172`) |
| slot guid | `e9632f4f72e61c418ef58d123890d111` — **the same guid in the master and in the instance**, which is what makes it one slot seen from two levels |
| coordinates input | `StructProperty Coordinates @180`, nested, 10 B, expression `0` (so the ramp is sampled with the default UV set, not a custom coordinate expression) |
| bound on the body chain | `Batmobile_V3_WheelArchs_NEW_MIC` (#767) → `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` (#-588) |
| bound on the master | `Batmobile_V3_Body_NoRain_MAT` (expr **696**) and `Batmobile_Worn` (expr **638**) → `Engine.Batmobile_V3_Tyre_ColourRamp` (#-545 / #-506 per package) |
| second ramp on the same materials | `Anisotropic Ramp` → `Engine.Aniso_ramp_Lacquered` (#-600), guid `a48ac517…` |
| scalar beside it | `colour_ramp_intensity` exists only on the tyre master (default **0.5**), overridden to **0.1** in `Batmobile_V3_Tyre_test_INST` |

So there are **two** ramp slots in play, not one: `Colour_Ramp_Map` (the colour lookup) and
`Anisotropic Ramp` (the highlight lookup, D5's texture). Both are texture **parameters**, both take
a `Coordinates` struct, and both bind the same texture on five of the six materials.

---

## 1. Every material that declares a ramp — slot, binding, level, offset

`level` is where the binding is written: `master` = the `Material`'s own expression default, `MIC` =
the `MaterialInstanceConstant` override. `item byte` is the offset inside the
`TextureParameterValues` array (`field 0x158`), which is how the value can be re-read without
guessing.

| material (slot) | level | ramp slot | bound texture | expression / item | guid |
|---|---|---|---|---|---|
| `Batmobile_Worn` (body master, export 359) | master | `Colour_Ramp_Map` | `Engine.Batmobile_V3_Tyre_ColourRamp` (#-545) | expr **638**, `ObjectNCRProperty @0xac` | `e9632f4f` |
| `Batmobile_V3_Body_NoRain_MAT` (interior master) | master | `Colour_Ramp_Map` | `Engine.Batmobile_V3_Tyre_ColourRamp` (#-506) | expr **696**, name @284, value @172 | `e9632f4f` |
| `Batmobile_V3_Discbreak` (master) | master | `Colour_Ramp_Map` | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` (#-558) | expr **707** | `e9632f4f` |
| `Batmobile_V3_Tyre_V2_MAT` (master) | master | `Colour_Ramp_Map` | `Engine.Batmobile_V3_Tyre_ColourRamp` | `COLOUR_FUNCTIONS.json:4573` | `e9632f4f` |
| `Batmobile_V3_WheelArchs_NEW_MIC` (#767, **body slot 3**, parent of the body) | MIC | `Colour_Ramp_Map` | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` (#-588) | `TextureParameterValues` item byte **62** | `e9632f4f` |
| `Batmobile_V3_Cockpit_MIC` (slot 10) | MIC | `Colour_Ramp_Map` | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `SLOTS.md:35` | `e9632f4f` |
| `Batmobile_V3_Discbreak_MIC` (slot 13) | MIC | `Colour_Ramp_Map` | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` | `SLOTS.md:38` | `e9632f4f` |
| `Batmobile_V3_Emissive` (slot 5) | MIC | `Colour_Ramp_Map` | `Engine.Batmobile_V3_Body_ColourRamp` | `SLOTS.md:30` | `e9632f4f` |
| `BatmobileV3_Cockpit_Seat` (slot 11) | MIC | `Colour_Ramp_Map` | `Maps.Batman_BM3_V2_Leather_Ramp` | `SLOTS.md:36` | `e9632f4f` |
| the six above | master + MIC | `Anisotropic Ramp` | `Engine.Aniso_ramp_Lacquered` (#-600) | expr **646** (Worn), **705** (Body_NoRain), **709** (Discbreak), **686** (Jokerfied) | `a48ac517` |

**Derived:** one guid, one slot, two bindings per chain. The master's `Tyre_ColourRamp` is the
*fallback*; every shipped Batmobile MIC that cares overrides it, and the body's own slot (3, via
767) overrides it to the lacquer underlayer ramp while the cockpit (10) and the disc (13) keep that
same override. The tyre material is the one that actually uses the tyre ramp — which is why the
master default points there (the tyre master is the one whose MIC never overrides it).

---

## 2. The parameters beside each ramp (the "what is it scaled by" part)

`SLOTS.md` carries the whole material row, so the neighbours are decoded, not inferred.

### 2.1 `Batmobile_V3_WheelArchs_NEW_MIC` (#767) — the body's ramp owner

| parameter | value | kind |
|---|---|---|
| `Colour_Ramp_Map` | `Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp` | texture |
| `Anisotropic Ramp` | `Engine.Aniso_ramp_Lacquered` | texture |
| `Material_Microdetail` | `Textures.Batmobile_Microdetail` | texture |
| `Material3_Microdetail_N` | `Engine.Batmobile_Micropattern_A_Normal` | texture |
| `Damage_Chapter_Mask` | `Textures.Batmobile_V3_TEXTURES_WheelArch_Damage_ChapterMask` | texture |
| `Normal_Map` | `Textures.Batmobile_V3_WheelArch_N` | texture |
| `Material0_Roughness` / `Material0_Reflectivity` | 0.4 / 0.15 | scalar |
| `Material2_Roughness` / `Material2_Reflectivity` / `Material2_Metalicity` | 0.15 / 0.9 / 1.0 | scalar |
| `Material3_Roughness` / `Material3_Reflectivity` | 0.02 / 0.5 | scalar |
| `EdgeMask_Metalicity` | 2.0 | scalar |
| `Damage_Dirt2_Opacity` / `Damage_Dirt_Edges` / `Damage_dirt` | 2.0 / 1.5 / 0.5 | scalar |
| `MicroDetail_size` / `MicroDetail_Material3_Size` | 15 / 250 | scalar |
| `Mud2_Opacity` / `Mud_Density` / `Mud_Edges_Opacity` / `Mud_Opacity` | 0.65 / 0.11 / 4 / 2 | scalar |
| `Wetness_Refl_Fresnel` | 0.6 | scalar |
| `Vector_Displacement_Max_Distance` / `_Multiplier` | 40 / 1 | scalar |
| no `colour_ramp_intensity` | — | absent on this material |

`SKINS.md:209-210` lists the same 22 scalars and 6 textures under the MIC, so the ramp's neighbours
are exactly the channel roughness/reflectivity set plus the micro-detail sizes — **nothing on the
body chain scales the ramp**. The ramp has no intensity knob there.

### 2.2 The tyre — the one material that does scale its ramp

| item | value | source |
|---|---|---|
| `colour_ramp_intensity` on `Batmobile_V3_Tyre_V2_MAT` | **0.5** (`FloatProperty @204`) | `objects.jsonl:515`, expression 515, name @172 |
| same, overridden in `Batmobile_V3_Tyre_test_INST` | **0.1** | `SKINS.md:776`, `MATERIALS.md:967` |
| the ramp it scales | `Colour_Ramp_Map` → `Engine.Batmobile_V3_Tyre_ColourRamp` | `COLOUR_FUNCTIONS.json:4573` |
| neighbours in that INST | `Diffuse_Adjust` 1, `EMP` 0, `EMP_Emissive_Multiplier` 650, `Mud_Density` 0.5, `Reflectivity_Multiplier` 0.2, `Roughness_Multiplier` 0.8 | `SKINS.md:776` |

**Derived:** `colour_ramp_intensity` (default 0.5, shipped tyre 0.1) is the only explicit *weight*
on any ramp in the car. It exists on the tyre master only — the body, cockpit, seat, disc and
emissive materials carry no such scalar, so their ramps are used at full strength.

### 2.3 The seat and the cockpit — the two interior bindings

| material | neighbours of `Colour_Ramp_Map` |
|---|---|
| `BatmobileV3_Cockpit_Seat` | `EmissiveMultiply` **15**, `Reflectivity_Multiplier` 1.2, `Fake Aniso Brightness 1/2` 0.01 / 1.0, `fake aniso orientation` 1, `fake aniso uv magnitude` 1, `fake aniso uv shift` 0; textures `Colour_Map` → `Int_Cockpit_D`, `Emissive` → `Int_Cockpit_E`, `Normal_Map_Lacquer` → `Int_Cockpit_N`, `Ref_n_Rough_Map` → `Int_Cockpit_S` |
| `Batmobile_V3_Cockpit_MIC` | `Metalicity` **0.9**, `Reflectivity_BaseMaterial2_Multiplier` **5.0**, `Reflectivity_Material3` 1.0, `BaseMaterial_Microdetail_Size` 45, `Material1/2/3_Microdetail_Size` 120 / 30 / 30, the five fake-aniso scalars; textures `Material_Separation_Mask` → `Int_Cockpit_M`, `Normal_Map` → `Int_Cockpit_N` |

### 2.4 The emissive (wheel-light) material — the body-colour ramp

`Batmobile_V3_Emissive` (slot 5): `Colour_Ramp_Map` → `Engine.Batmobile_V3_Body_ColourRamp`;
`Metalicity` 0.92, `Rain_Constant` 1.0, `Reflectivity_Multiplier` 1.0, `Material1_Microdetail_Size`
250, `Material2/3_Microdetail_Size` 30/30, fake-aniso set; textures `BaseMaterial_Microdetail`
→ `Micropattern_B`, `Emissive_Map` → `Wheel_E`, `Material_Separation_Mask` → `Wheel_Lights_M`,
`Normal_Map` → `Wheel_Lights_N`.

---

## 3. Where the ramp textures actually are — this is why D10 is stuck

| texture | resident in a Batmobile package? | size / format | referenced as |
|---|---|---|---|
| `Batman_BM3_V2_Leather_Ramp` | **yes** — a `Texture2D` row in all four packages | **64×512, PF_DXT1, 1,894 B** | `TEXTURES.md:8,111,212,308`, bound by `BatmobileV3_Cockpit_Seat (Colour_Ramp_Map)` |
| `Batman_BM3_V2_Lacquered_Underlayer_Ramp` | **no** — no `Texture2D` row; bound by a **negative** package index (#-588 / #-558) | UNKNOWN | `COLOUR_PARAMS.md:79` |
| `Batmobile_V3_Tyre_ColourRamp` | **no** — negative index (#-545 / #-506) | UNKNOWN | `COLOUR_PARAMS.md:134` |
| `Batmobile_V3_Body_ColourRamp` | **no** — negative index | UNKNOWN | `SLOTS.md:30` |
| `Aniso_ramp_Lacquered` | **no** — negative index (#-600) | UNKNOWN | `COLOUR_PARAMS.md:78` |

**Derived (format rule):** a negative package index is an **import** entry, not an export — the
texture lives in another package (the `Engine.`/`Maps.` prefix agrees with that). So the four ramps
that matter are *imported*, and only `Leather_Ramp` is serialised inside the Batmobile packages.
A search of the material grab confirms it: `Working/Appearance/grab/**/*Ramp*` → **0 files**, so
nothing named `*Ramp*` was ever exported as a `.tga` for conversion.

That sharpens the earlier reason recorded for rule **D10** ("the ramp texture is referenced by the
material dump but is not in the export"): the ramp is not missing from the *material*, it is an
import from `Engine`/`Maps`, and the grab exported none of them. What would settle it: a grab of the
`Engine`/`Maps` packages that the four imports resolve into (the same export pass that produced
`TEXTURES.md` would then show their size and format), after which the ramp could be converted or
baked like any other map.

---

## 4. The shader side: no ramp uniform anywhere

Searched the shader/uniform dumps in the same folder (`UNIFORM_FORMAT.md` and any `SHADER*`):
**0 matches for `ramp`** (case-insensitive). The ramp is therefore a **material texture sampler**
only — it has no constant-buffer counterpart, so there is no scalar in any shader that says how a
ramp is applied. This matches the project's standing finding that the operator graph is stripped
(944 `FunctionExpressions` slots, 0 non-zero), which is why the *combine rule* for the ramp is
**UNKNOWN** even though the slot, the binding and the guid are decoded.

---

## 5. Answer, in one paragraph

Six Batmobile materials reference a colour ramp through one slot named **`Colour_Ramp_Map`**
(guid `e9632f4f`): the body chain's `Batmobile_V3_WheelArchs_NEW_MIC` and the `Cockpit_MIC` and
`Discbreak_MIC` bind **`Engine.Batman_BM3_V2_Lacquered_Underlayer_Ramp`**; `Batmobile_V3_Emissive`
binds **`Engine.Batmobile_V3_Body_ColourRamp`**; `BatmobileV3_Cockpit_Seat` binds
**`Maps.Batman_BM3_V2_Leather_Ramp`**; and the masters (`Batmobile_Worn`, `Batmobile_V3_Body_NoRain_MAT`,
`Batmobile_V3_Tyre_V2_MAT`) default the same slot to **`Engine.Batmobile_V3_Tyre_ColourRamp`**. A second
ramp slot, **`Anisotropic Ramp`** → `Engine.Aniso_ramp_Lacquered`, sits on the same materials and is
D5's texture. The only parameter that scales a ramp is **`colour_ramp_intensity`** — tyre master 0.5,
shipped tyre 0.1 — and no other material has one. All five ramps except `Leather_Ramp` (64×512 DXT1,
1,894 B) are **imports** from `Engine`/`Maps`, and none was exported to the grab, which is exactly
why D10 cannot be carried yet.

---

## 6. Reproduce

```bash
cd "E:/Modding/JustCause3/JC3-Batmobile"
grep -n "Colour_Ramp_Map" Research/BatmobileGrab/COLOUR_PARAMS.md Research/BatmobileGrab/SLOTS.md
grep -n "e9632f4f\|a48ac517" Research/BatmobileGrab/objects.jsonl | head
grep -n "Ramp" Research/BatmobileGrab/TEXTURES.md
grep -n "colour_ramp_intensity" Research/BatmobileGrab/SKINS.md Research/BatmobileGrab/MATERIALS.md
ls Working/Appearance/grab/*/Texture2D/*Ramp* 2>/dev/null || echo "no ramp TGA in the grab"
grep -ni "ramp" Research/BatmobileGrab/UNIFORM_FORMAT.md || echo "no ramp uniform in the shader dump"
```

## 7. Limits

- **The ramp's content is not decoded.** No channel order, no stop count, no colour values: the
  texture is a sampler input and nothing in the package says how it is indexed.
- **Four of the five ramps have no size or format** because they are imports; only `Leather_Ramp`
  has a `Texture2D` record.
- **The combine rule is UNKNOWN** (operator graph stripped); `colour_ramp_intensity` is a name and a
  number, and what it multiplies is not in any file read here.
- Nothing was converted, baked, written to `Research/`, or opened in a game.

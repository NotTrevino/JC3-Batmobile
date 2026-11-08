# review-hud-cluster-elements - does `HUD_SPEC.json` describe the cluster, and is G3-HUD-CLUSTER right?

## STATUS

**done - `HUD_SPEC.json` names **0** speedometer/health elements with a position or a size, so the
brief's requested list from that file is empty (it is a behaviour contract, not a layout record);
`G3-HUD-CLUSTER.md` names **18** elements, and all **6** placed clips match the decompiled AS3
exactly, so the report **holds**. 13/13 checks pass, `--check` exits 0.**

Files written:

- `Tools/scripts/hud_cluster_elements.py` (`--write` / `--check`)
- `Working/Translation/HUD_CLUSTER_ELEMENTS.md` (the element-by-element audit, 14,095 B)
- `tmp/freebuff/reports/review-hud-cluster-elements.md` (this card)

Nothing else was modified. `HUD_SPEC.json`, `G3-HUD-CLUSTER.md`, `Working/HUD/CLUSTER.json`, the
other tasks' scripts and the game install were opened read-only. No game launched or attached
(INSTRUCTIONS.md §3).

---

## 1. Starting from the HUD side: what the spec names

The brief asks for every element of the speedometer/health cluster in
`Research/BatmobileGrab/HUD_SPEC.json`, with name, position and size. Reading that file, it holds
three top-level keys (`jp_exs`, `bmak`, `jc3`) and under `bmak` eleven keys:

```
scripts, external_images, frame_labels, uc_setters, constants, health_contract,
mode_strings, has_battle_mode, has_boost_gauge, has_energy_system, has_winch
```

There is **no element list and no geometry**. Tested mechanically, not by eye: 20 candidate element
names (`Health`, `BoostMovie`, `Combo`, `RemoteInterface`, `ClockTimer`, `Upgrade1/2`, `FillMovie`,
`Cap`, `Background`, `Healthbar`, `ArmourForeground`, `ArmourBackground`, `BG`, `XPbar`,
`DamageEffectMovie`, `BoostGauge`, `ch1040`, `LeftSideParent`, `RightSideParent`) against every key
and every list value in the file - **zero** hits. Keys matching `x/y/z/position/matrix/matrix3d/
width/height/size/rect/bounds/scale` - **zero** hits.

Four of those names occur in the file as *substrings only*, all inside setter or key names
(`BoostGauge`, `Combo`, `Health`, `RemoteInterface`, e.g. `UC_SetHealth`), which is why a text grep
can look like the spec "contains" the cluster while it does not:

| the brief asks for | in `HUD_SPEC.json`? | evidence |
|---|---|---|
| element names | **no element list** | 20 names as key or list value: none; 4 substrings only |
| positions (x / y / z) | **no** | 12 geometry keys searched, none present |
| sizes (width / height / frames) | **no** | same search; the 112 frame labels are names, not counts |

So **the requested (name, position, size) table does not exist in the spec**, and an element-by-
element comparison cannot start from it. That is a property of the file, proven by checks 1-3, 10-12.

What the file *is*: 31 `UC_*` setter signatures, 112 **flat** frame labels (`Normal`, `Charging`,
`Armour0..4`, `DRIVE`/`DRIVETOBATTLE`/…), 7 constants, and the health contract (two fills, the armour
tier formula, pulse/offscreen/tick timings). Behaviour, not layout.

---

## 2. The report's inventory, and the comparison

`G3-HUD-CLUSTER.md` names 18 elements. Six carry a transform:

| element | report | AS3 source | verdict |
|---|---|---|---|
| `Health` | -479.228 / -328.300 / 8.318, yaw 10° | `LeftSideParentMovie_311.as:184` -479.227722 / -328.299988 / 8.317747 | confirmed |
| `BoostMovie` (left) | -452.867 / 65.550 / 24.110, yaw 26° | `LeftSideParentMovie_311.as:148` -452.866943 / 65.550003 / 24.110035 | confirmed |
| `Combo` | -460.237 / -263.250 / 36.326, yaw 26° | `LeftSideParentMovie_311.as:220` -460.236969 / -263.25 / 36.325874 | confirmed |
| `RemoteInterface` | -525.275 / 225.000 / 51.171, yaw 26° | `LeftSideParentMovie_311.as:112` -525.274841 / 225 / 51.171337 | confirmed |
| `BoostMovie` (right) | 446.000 / 180.500 / 56.890, yaw -40° | `RightSideParentMovie_126.as:125` 445.999695 / 180.5 / 56.889893 | confirmed |
| `ClockTimer` | 399.200 / 60.750 / 0.000, yaw -38° | `RightSideParentMovie_126.as:233` 399.200012 / 60.75 / 0.00001 | confirmed |

Two more carry a position, from the tag stream rather than AS3: `Upgrade1` (-10.0, 96.3) and
`Upgrade2` (-10.5, 100.6). Ten are named but not placed by the report: `FillMovie` (102 frames),
`Cap`, `Background` (32 frames), `Healthbar`, `ArmourForeground`, `ArmourBackground`, `BG`, `XPbar`,
`DamageEffectMovie`, `ch1040`.

**Elements where the report's number differs from the spec's: none** - the spec states none to
differ from. **Elements the report mentions that the spec does not contain: all 18** (the spec
contains no elements at all).

### Which of the two is correct

Neither is contradicted; they answer different questions, and the source settles the layout:

- every report transform equals an authored `____motion_<clip>af1_mat3DVec__[12/13/14]` triple in the
  decompiled `HudModuleBatmobile` AS3 (Δ ≤ 0.00034, i.e. the report's 3-decimal rounding);
- every value the spec *does* state, the report states identically - 7 constants
  (`StageWidth` 1024, `StageHeight` 720, `MovieWidth` 1024, `MovieHeight` 768, `PerspectiveFOV` 56,
  `TickDeltaTime` 0.033, `MaxHealthChangePerFrame` 0.05), 9 health-contract items (both fill
  expressions, the tier formula, `pulse_below` 0.2, `offscreen_seconds` 2.0, 0.6667 s sweep, 30 Hz,
  5 tiers), and all 16 frame labels the report attributes to a clip (membership of the flat set).

So the spec is authoritative for **behaviour** and the report for **layout**, and on the overlap they
agree exactly. Nothing needs correcting in either.

### One display nit

`ClockTimer`'s authored z is `0.00001`; the report prints `0.000`. A 3-decimal rounding of a
5-decimal value (Δ 1e-05), not an error.

---

## 3. Defects this audit found - in its own first pass

Reported because the first two `--check` runs failed and the failure was the audit tool's, not the
report's:

1. **False mismatch on `BoostMovie`.** The first version keyed AS3 transforms by clip name; two
   parents author a `BoostMovie`, so the left row was compared against the right parent's record
   (Δ 898.87 on x). Fixed by keeping a *list* of candidates per name and matching each row to its
   nearest one.
2. **Substring test used `\b`**, so `UC_SetHealth` never matched `Health` and the check reported an
   empty list while asserting the opposite.
3. **Screen-estimate tolerance** was 0.05 against values the report rounds to one decimal; 449.6 vs
   449.55 sits exactly on the bound. Fixed to the rounding bound (0.051) and to expect 4 of 6 rows
   (the two right-side rows say "right group" instead of a number).
4. **A vacuous frames check** (`frames.get(k) not in (json.dumps(spec),)`) replaced with a real one:
   the spec has no per-clip frame/timeline key.

All four are reflected in the final tool; the report under review was right on every point tested.

---

## 4. UNKNOWN (with what was tried)

1. **The badge coordinates and every clip frame count.** `Upgrade1` (-10.0, 96.3), `Upgrade2`
   (-10.5, 100.6), `FillMovie` 102, `Health` 162, `Background` 32, badges 65 frames. These are
   `PlaceObject2` matrices and SWF timeline lengths, not AS3 constants: `grep -rn -E "96\.3|100\.6|
   182\.5"` over the whole decompile returns nothing, and neither file holds frame counts. They rest
   on the report's own tag parse; re-parsing the `BoostGaugeChild` placements from the movie
   `bmak_hud.py` carves would settle them, which this audit did not do. Consistency only:
   `gotoAndStop(this.BoostLevel + 1)` with level 0..100 needs ≥ 101 frames, so 102 is possible.
2. **Which clip owns each frame label.** The spec's 112 labels are one flat set: membership is
   provable, attribution is not. Every label the report attributes is a member; the per-clip mapping
   is the report's tag read.
3. **`ch1040`'s identity** - unnamed 1-frame third child of `BoostMovie` at (5.0, -83.7), no setter.
   Nothing in the spec or the AS3 names it; the report already marks it UNKNOWN.
4. **The `Health` sub-clip offsets** (`Healthbar`, `ArmourForeground`, `BG`, `XPbar`). They sit in
   `PlaceObject3` MATRIX3D records, which the report says its tool does not decode - so it quotes no
   offsets and this audit quotes none either.
5. **Pixel sizes.** Neither file gives an element's width/height in pixels, and the AS3 carries none;
   the only sizes in play are frame counts (UNKNOWN 1).

---

## 5. Commands (verbatim)

```
$ cd E:/Modding/JustCause3/JC3-Batmobile && PYTHONIOENCODING=utf-8 python Tools/scripts/hud_cluster_elements.py --write; echo "write_exit=$?"; PYTHONIOENCODING=utf-8 python Tools/scripts/hud_cluster_elements.py --check; echo "check_exit=$?"
wrote Working/Translation/HUD_CLUSTER_ELEMENTS.md (14065 chars), 13/13 checks pass
write_exit=0
CHECK PASS
check_exit=0
```

The first pass, before the four tool fixes above - kept because a clean-looking final run must not
hide the failed ones:

```
$ python Tools/scripts/hud_cluster_elements.py --check; echo "exit=$?"
FAIL the apparent element hits in the spec are substrings of setter/key names: substring-only:
FAIL every report clip transform equals the source AS3 matrix3D translation: Health delta [0.000278, 1.2e-05, -0.000253]; BoostMovie delta [898.866695, 114.95, 32.779893]; ...
FAIL the report's screen estimates are 512+x / 384+y: Health [32.8, 55.7] vs [32.772, 55.7]; ...
CHECK FAIL
exit=1
```

```
$ python Tools/scripts/hud_cluster_elements.py --write; echo "write_exit=$?"; python Tools/scripts/hud_cluster_elements.py --check; echo "check_exit=$?"
wrote Working/Translation/HUD_CLUSTER_ELEMENTS.md (13993 chars), 12/13 checks pass
write_exit=0
FAIL the report's screen estimates are 512+x / 384+y to its 1-decimal rounding: Health [32.8, 55.7] vs [32.772, 55.7]; BoostMovie [59.1, 449.6] vs [59.133, 449.55]; Combo [51.8, 120.8] vs [51.763, 120.75]; RemoteInterface [-13.3, 609.0] vs [-13.275, 609.0]
CHECK FAIL
check_exit=1
```

```
$ D="E:/Modding/_shared/gamedata/BmAKgrab_early/hud/modules/HudModuleBatmobile/dec/scripts/HudModuleBatmobile_fla"; grep -n "mat3DVec__\[1[234]\]" "$D/LeftSideParentMovie_311.as" | grep -Ei "motion_(Health|BoostMovie|Combo|RemoteInterface)af1"
112:            this.____motion_RemoteInterfaceaf1_mat3DVec__[12] = -525.274841;
113:            this.____motion_RemoteInterfaceaf1_mat3DVec__[13] = 225;
114:            this.____motion_RemoteInterfaceaf1_mat3DVec__[14] = 51.171337;
148:            this.____motion_BoostMovieaf1_mat3DVec__[12] = -452.866943;
149:            this.____motion_BoostMovieaf1_mat3DVec__[13] = 65.550003;
150:            this.____motion_BoostMovieaf1_mat3DVec__[14] = 24.110035;
184:            this.____motion_Healthaf1_mat3DVec__[12] = -479.227722;
185:            this.____motion_Healthaf1_mat3DVec__[13] = -328.299988;
186:            this.____motion_Healthaf1_mat3DVec__[14] = 8.317747;
220:            this.____motion_Comboaf1_mat3DVec__[12] = -460.236969;
221:            this.____motion_Comboaf1_mat3DVec__[13] = -263.25;
222:            this.____motion_Comboaf1_mat3DVec__[14] = 36.325874;

$ grep -n "mat3DVec__\[1[234]\]" "$D/RightSideParentMovie_126.as" | grep -Ei "motion_(BoostMovie|ClockTimer)af1"
125:            this.____motion_BoostMovieaf1_mat3DVec__[12] = 445.999695;
126:            this.____motion_BoostMovieaf1_mat3DVec__[13] = 180.5;
127:            this.____motion_BoostMovieaf1_mat3DVec__[14] = 56.889893;
233:            this.____motion_ClockTimeraf1_mat3DVec__[12] = 399.200012;
234:            this.____motion_ClockTimeraf1_mat3DVec__[13] = 60.75;
235:            this.____motion_ClockTimeraf1_mat3DVec__[14] = 0.00001;

$ grep -rn -E "96\.3|100\.6|182\.5" "$D" | head -5
(no output - badge coordinates are not AS3 constants)

$ ls -l Working/Translation/HUD_CLUSTER_ELEMENTS.md Tools/scripts/hud_cluster_elements.py
-rwxr-xr-x 1 User 197121 28482 Nov  5 15:29 Tools/scripts/hud_cluster_elements.py
-rw-r--r-- 1 User 197121 14095 Nov  5 15:29 Working/Translation/HUD_CLUSTER_ELEMENTS.md
```

The 13 checks (all PASS, recomputed by `--check`): no geometry key in the spec; no element with a
position/size; apparent hits are substrings only; 6 clip rows parsed; every transform equals its
nearest AS3 record; screen estimates are 512+x / 384+y; 7 shared constants agree; 9 contract items
agree; 16 labels are members; no report element appears in the spec; the label set is flat; no
per-clip frame count in the spec; every placed clip has an authored transform.

## 6. Labels used

- **decoded** - read from a file: the AS3 `mat3DVec__[12/13/14]` values, the spec's constants,
  contract strings and label set, the report's stated numbers.
- **derived** - computed here: the Δ columns, the 512+x / 384+y screen estimates, the element
  census, the verdicts.
- **UNKNOWN** - §4, each with what was tried.

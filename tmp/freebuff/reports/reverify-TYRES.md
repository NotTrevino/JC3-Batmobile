STATUS: done — `TYRES.md`'s four wheel numbers are **measured from the mesh**, not read from the game: the cooked wheel components store a 64.0 (0.640 m) `WheelRadius` and **no `WheelWidth` at all**, and none of the 274 `CLASS_DEFAULTS.json` tags is a wheel radius / width / suspension value.

# reverify-TYRES — are the wheel numbers grabbed or shaped?

Task (operator): run `Tools/scripts/bmak_tyres.py --check`, then compare its wheel radius and
width with what the game itself stores — the wheel defaults among the 274 tags in
`Research/BatmobileGrab/CLASS_DEFAULTS.json` (any `SVehicleWheel` / `WheelRadius` /
`SuspensionTravel` value) and the cooked wheel components — and report each wheel number as
**matches-the-package** / **mesh-only** / **disagrees**. Rules: `tmp/freebuff/INSTRUCTIONS.md` §3.

Task-file note: `E:/Modding/JustCause3/JC3-Batmobile/tmp/freebuff/manual/` holds **no `.txt` files**
(`manual/`, `manual/claimed/`, `manual/done/` are all empty), so there was no task file to claim;
this report answers the operator's task verbatim and is written at the `DONE` path given.

## VERDICTS

| wheel number | mesh (this project) | package (the game) | verdict |
|---|---|---|---|
| **radius** | 0.6829 / 0.6826 / 0.6826 / 0.6827 m (mean 0.6827) | `WheelRadius` = **64.0** (0.640 m) at `SVehicleWheel` offset 568, all four wheels | **disagrees** — mesh is +42.7 mm (+6.67%) |
| **tread diameter** | 1.3652–1.3657 m | 1.280 m (2 × 0.640) | **mesh-only** |
| **width** | 0.7314–0.7325 m | **absent** — no tag at offset 572 (`WheelWidth`) on any of the four wheels | **mesh-only** |
| suspension travel | — (no mesh counterpart) | up 30.0 / down 40.0 (fronts); down 40.0 (rears, no `Up`) | **package-only** |
| class defaults | — | **0** wheel-size values among the **274** tags; the only wheel tags are the empty `WheelSpeedMap` array and two `SVehicle.Wheels` arrays of 4 **references** | no value to match |

Consequence for the research reset: `TYRES.md` §1–§5 is a mesh measurement (PSKX wheel-bone
vertices through the ONE transform), and its phrase "1.366 = 2 × the physics radius — the same
number by design" refers to **JC3's** `land_global.*_wheels.radius` (T-G2), which this project
itself set from the mesh — not to a value the game of origin stores. The only package-sourced
wheel number on that page (0.640 m, its §4 BmAK row) is already marked "not imported".

## Evidence (decoded)

* Package: `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\Playable_Batmobile_SF.upk`,
  exports 5394–5397, class `SVehicleWheel`, outer `Batmobile_Archetypes.Vehicle.Batmobile.Wheel*`,
  sizes 191/191/178/166 B, 21/21/21/20 tags, each tag list starting at byte 4 and closing on the
  2-byte property-list terminator (189/191, 189/191, 176/178, 164/166).
* Names: the tag stream carries only (type, class offset); the names come from
  `Research/BatmobileGrab/BMSDK_OFFSETS.json` → `SVehicleWheel` (568 `WheelRadius`,
  572 `WheelWidth`, 576 `SuspensionTravelUp`, 580 `SuspensionTravelDown`, all `FloatProperty`);
  the script asserts that mapping before using it.
* `CLASS_DEFAULTS.json`: 93 tags (`BmScript.Default__RVehicleBatmobile`) + 181 tags
  (`BmGame.Default__RVehicleBatmobileBase`) = **274**; scan for `WheelRadius` / `WheelWidth` /
  `SuspensionTravel` members returns **nothing**; the `Wheels` arrays (subclass tag 80, base tag
  168, `SVehicle.Wheels` @ `0x06ac`) hold `count=4 ref [SVehicleWheel:WheelFL, WheelFR, WheelRL,
  WheelRR]`.
* Cross-check (independent artifact): `CHAIN.json` carries the same 16 wheel rows (4 corners × 4
  variants) with `WheelRadius` 64.0 and `grep -c WheelWidth CHAIN.json` = **0**; the script fails
  if any of them differs from the bytes it decodes.
* Unit: 64.0 is cm (derived: the same layout reads 90.0 on `Default__RVehicleTank`, and
  `CLASS_DEFAULTS.json` stores lengths in cm — `BattleModeLength` 430.0, `PursuitModeWidth` 220.0).
  The verdict is unchanged on any reading: 64.0 vs a 68.3 cm mesh radius.

## Files written

* `Tools/scripts/bmak_tyres_package.py` — new tool, `--write` / `--check`; re-decodes the four
  wheel exports, re-scans the 274 tags, recomputes the mesh numbers through
  `bmak_tyres.build()`, re-derives all verdicts, and fails on drift or on an invariant break
  (four wheels; each tag list closing; one `WheelRadius`; **no** `WheelWidth` tag; 274 tags with
  zero wheel values; `CHAIN.json` agreeing with the bytes).
* `Research/BatmobileGrab/TYRES_PACKAGE.md` (114 lines) and
  `Research/BatmobileGrab/TYRES_PACKAGE.json` — generated, not hand-edited.
* This report.

Scratch (not outputs): `tmp/freebuff/scratch/probe_wheels.py`, `tmp/freebuff/scratch/probe_arch.py`.

## Commands and output (verbatim)

### 0. First `--check` of the card, as asked

```
$ uv run --with numpy python Tools/scripts/bmak_tyres.py --check; echo "EXIT=$?"
EXIT=1
stderr:
Traceback (most recent call last):
  File "E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts\bmak_tyres.py", line 41, in <module>
    import bat_assemble as BA   # noqa: E402  (the ONE transform)
  File "E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts\bat_assemble.py", line 48, in <module>
    import tex2ddsc as TX  # noqa: E402
  File "E:\Modding\JustCause3\JC3-Batmobile\Tools\scripts\tex2ddsc.py", line 31, in <module>
    from PIL import Image
ModuleNotFoundError: No module named 'PIL'
```

The tool's own docstring asks for `pillow` via `bat_assemble`; rerun with it:

```
$ uv run --with numpy --with pillow python Tools/scripts/bmak_tyres.py --check; echo "EXIT=$?"
OK: 4 tyres; tread Ø 1.3652-1.3657, shoulder Ø 1.3711-1.3714, width 0.7314-0.7325; station radius vs mesh <= 0.6 mm
OK: TYRES.md matches the re-derived render (169 lines)
EXIT=0
```

### 1. Where the wheels live in the packages

```
$ uv run --with numpy --with pillow python tmp/freebuff/scratch/probe_wheels.py   (excerpts)
===  Startup.upk
export 171139 WheelFL class=SVehicleWheel size=14 path=BmScript.Default__RVehicleBatmobile.WheelFL
   data error: payload ends at 0x2679670e, past the 0x20000000 decode budget
export 171140 WheelFR class=SVehicleWheel size=14 path=BmScript.Default__RVehicleBatmobile.WheelFR
   data error: payload ends at 0x2679671c, past the 0x20000000 decode budget
export 171141 WheelRL class=SVehicleWheel size=14 path=BmScript.Default__RVehicleBatmobile.WheelRL
   data error: payload ends at 0x2679672a, past the 0x20000000 decode budget
export 171142 WheelRR class=SVehicleWheel size=14 path=BmScript.Default__RVehicleBatmobile.WheelRR
   data error: payload ends at 0x26796738, past the 0x20000000 decode budget
```

(The four class-default wheel components are 14-byte payloads whose decompressed offsets sit at
~645 MiB, past `PartialPackage`'s 512 MiB budget; the values that ship are the archetype's — §2.)

### 2. The cooked wheel components (`Playable_Batmobile_SF.upk`)

```
$ uv run --with numpy --with pillow python tmp/freebuff/scratch/probe_arch.py   (excerpt)
=== export 5394 WheelFL outer=Batmobile_Archetypes.Vehicle.Batmobile.WheelFL size=191
 start=4 tags=21 end=189/191 why=eof
   ...
   FloatProperty      off=568    {"value": 64.0}
   FloatProperty      off=576    {"value": 30.0}
   FloatProperty      off=580    {"value": 40.0}
   FloatProperty      off=584    {"value": 500.0}
   FloatProperty      off=588    {"value": 100.0}
=== export 5395 WheelFR outer=Batmobile_Archetypes.Vehicle.Batmobile.WheelFR size=191
   FloatProperty      off=568    {"value": 64.0}
   FloatProperty      off=576    {"value": 30.0}
   FloatProperty      off=580    {"value": 40.0}
=== export 5396 WheelRL outer=Batmobile_Archetypes.Vehicle.Batmobile.WheelRL size=178
   FloatProperty      off=568    {"value": 64.0}
   FloatProperty      off=580    {"value": 40.0}
=== export 5397 WheelRR outer=Batmobile_Archetypes.Vehicle.Batmobile.WheelRR size=166
   FloatProperty      off=568    {"value": 64.0}
   FloatProperty      off=580    {"value": 40.0}
```

No export emits a tag at offset 572.

### 3. The existing artifacts, scanned

```
$ python - <<'EOF'   (walk CHAIN.json for SVehicleWheel.WheelRadius/SuspensionTravel*)
/fields/SVehicleWheel/Playable_Batmobile_SF.WheelFL[1] {"offset": 568, "name": "SVehicleWheel.WheelRadius", "type": "FloatProperty", "value": 64.0, "named_by": "sdk-layout"}
/fields/SVehicleWheel/Playable_Batmobile_SF.WheelFL[2] {"offset": 576, "name": "SVehicleWheel.SuspensionTravelUp", "type": "FloatProperty", "value": 30.0, "named_by": "sdk-layout"}
/fields/SVehicleWheel/Playable_Batmobile_SF.WheelFL[3] {"offset": 580, "name": "SVehicleWheel.SuspensionTravelDown", "type": "FloatProperty", "value": 40.0, "named_by": "sdk-layout"}
... (WheelFR/RL/RR likewise: 64.0 radius each; fronts also 30.0 up)
$ grep -c WheelRadius Research/BatmobileGrab/CHAIN.json     -> 16
$ grep -c WheelWidth  Research/BatmobileGrab/CHAIN.json     -> 0
```

```
$ python - <<'EOF'   (scan the 274 CLASS_DEFAULTS tags for wheel values)
subclass tags: 93
   77 0x066c ArrayProperty | WheelSpeedMap (empty, count 0)
   80 0x06ac ArrayProperty | Wheels — 4 refs SVehicleWheel:WheelFL/FR/RL/RR
base tags: 181
   168 0x06ac ArrayProperty | Wheels — 4 refs SVehicleWheel:WheelFL/FR/RL/RR
total tags: 274
```

No tag at any offset 568/572/576/580 appears in either CDO.

### 4. The new tool

```
$ uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --write; echo "WRITE_EXIT=$?"
wrote Research\BatmobileGrab\TYRES_PACKAGE.md (114 lines)
wrote Research\BatmobileGrab\TYRES_PACKAGE.json
WRITE_EXIT=0

$ uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --check; echo "CHECK_EXIT=$?"
OK: 4 wheel components in Playable_Batmobile_SF.upk, each closing on its terminator; WheelRadius 64.0 on all four; WheelWidth absent
OK: class defaults: 274 tags, 0 wheel-size values
OK: radius disagrees (mesh 0.6827 m vs package 0.640 m, -42.7 mm); width mesh-only; suspension package-only
OK: TYRES_PACKAGE.md and TYRES_PACKAGE.json match the re-derived render
CHECK_EXIT=0
```

### 5. Final check (after this report was written)

```
$ uv run --with numpy --with pillow python Tools/scripts/bmak_tyres_package.py --check; echo "CHECK_EXIT=$?"
OK: 4 wheel components in Playable_Batmobile_SF.upk, each closing on its terminator; WheelRadius 64.0 on all four; WheelWidth absent
OK: class defaults: 274 tags, 0 wheel-size values
OK: radius disagrees (mesh 0.6827 m vs package 0.640 m, -42.7 mm); width mesh-only; suspension package-only
OK: TYRES_PACKAGE.md and TYRES_PACKAGE.json match the re-derived render
CHECK_EXIT=0
```

## UNKNOWNs

1. **The class-default wheel components' own payloads** (`Startup.upk` exports 171139–171142,
   14 B each): tried `PartialPackage.data()` per export — refused, payload ends at
   `0x2679670e`+ (≈645 MiB), past the tool's 512 MiB decode budget (the same limit
   `REMAINDER.md` §3b records for the 6 CDO component payloads). Whether they override anything
   is therefore unread. It changes no verdict here: the axle/vehicle archetype that spawns
   (`Playable_Batmobile_SF`) carries the four wheels decoded in §2, and those are what
   `CHAIN.json` cites.
2. **The native class default of `SVehicleWheel.WheelWidth`** (offset 572): the class is native
   and no shipped package holds a `Default__SVehicleWheel`, so the value the engine falls back to
   when a wheel stores no tag is UNKNOWN. What *is* known is the thing the task asks — the
   package stores no width for this car, so the mesh width (0.7314–0.7325 m) has no
   package counterpart to compare against.
3. **Whether the tyre's visual width is a *different* quantity from `WheelWidth`** (the 3D tyre vs
   the sim's contact patch): not decidable from the packages alone, because the Batmobile's
   wheels carry no width tag; deciding it would need the runtime oracle (out of scope under §3:
   no game process).

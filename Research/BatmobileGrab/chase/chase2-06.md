# Chase 2-06 — second pass on `BattleModeFrontThrottle` / `BattleModeRearThrottle` (F-44, F-45)

Scope: the only rows `Research/BatmobileGrab/chase/chase-06.md` leaves **STILL UNKNOWN** — F-44
`BattleModeFrontThrottle` (0x2e4) and F-45 `BattleModeRearThrottle` (0x2e8), both on
`RVehicleSimBatmobile`.

Read-only: no existing document, package or game file was changed; nothing written under
`E:/Games` or `D:/Games`, no game launched, nothing committed. Writes: this file, and two new
commands (`findimm`, `func`) added to the already-new `Tools/scripts/chase/chase2_native.py`.

**Smart-search tool:** `tmp/freebuff/reports/smart-search.md` shows `STATUS: deferred`, not `done`,
so `smart_search.py` was not run.

**Result: both rows stay STILL UNKNOWN, but for a sharper reason than chase-06 could state.** The
shipped default is now *proven* to be 0.0 (the CDO of this class omits every zero-valued property —
58 of 58 serialised tags are non-zero, and the same rule holds on two control CDOs), and the
executable still yields no attributable writer for either field. So the row's answer is
"0.0 as a class default, overwritten at runtime, no shipped tunable value".

| row | member | status | finding |
|---|---|---|---|
| F-44 | `BattleModeFrontThrottle` (0x2e4) | **STILL UNKNOWN** | class default **0.0** (proven by CDO omission rule); no serialised override in any layer; no attributable exe writer |
| F-45 | `BattleModeRearThrottle` (0x2e8) | **STILL UNKNOWN** | same, default **0.0** |

---

## What this pass added

### 1. The absence of 0x2e4 / 0x2e8 is the CDO's zero-skip rule, not a parse gap

chase-06 already had a positional control (0x2e0 and 0x2ec are tagged on either side). This pass
adds the rule that explains *why* a property can legitimately be absent, and checks it on three
objects:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RVehicleSimBatmobile | grep -c "^  "
58                       # serialised tags
$ ... | grep -cE " 0$| 0\.0$"
0                        # tags whose value is zero
$ python Tools/scripts/chase/ch1_dlo.py dlo Engine.upk Default__Pawn | grep -c "^  "
59
$ ... | grep -cE " 0$| 0\.0$"
0
```

The class declares 116 offsets in `BMSDK_OFFSETS.json`; its CDO serialises 58, every one of them
non-zero. A cooked CDO writes only the properties that differ from the class default, so **absent
tag = class default**, and on this class every absent property is at zero. That is exactly the rule
chase-01 used implicitly (`Default__Projectile` has no `Damage` tag, its `Damage` is 0) and
chase-2-03 used explicitly for the strafe block.

**Consequence for F-44/F-45:** their class default is **0.0**, not "unreadable". What chase-06
called "no serialised value" is correct but incomplete — the layer that exists says zero.

### 2. The executable has no compiled constructor that duplicates the CDO values

A C++ initialiser that set these fields to the CDO's values would appear as an immediate store at
the field displacement (`c7 8x <disp32> <imm32>`) or as a `movss` from a RIP-relative constant. The
immediate form is absent for every CDO value this class ships:

```
$ python Tools/scripts/chase/chase2_native.py findimm 0x2cc --imm 0x42a00000   # 80.0
0 store(s)
$ ... findimm 0x2f0 --imm 0x44960000                                            # 1200.0
0 store(s)
$ ... findimm 0x2fc --imm 0x42b40000                                            # 90.0
0 store(s)
$ ... findimm 0x31c --imm 0x3f800000                                            # 1.0
0 store(s)
$ ... findimm 0x320 --imm 0xbf000000                                            # -0.5
0 store(s)
$ ... findimm 0x2d0 --imm 0x3f000000                                            # 0.5
0 store(s)
$ ... findimm 0x2dc --imm 0x3ccccccd                                            # 0.025
0 store(s)
```

So this class's non-zero values are **data** (the CDO), not code, and the two throttle fields have
neither: no code default and no data default ⇒ 0.0 by the rule above. This also explains why
chase-06's four-offset control (which looked for a constructor elsewhere) found nothing: for this
class there is no value-setting constructor to find.

### 3. The store sites at 0x2e4 / 0x2e8 are still unattributable — and now measurably so

| form | 0x2e4 | 0x2e8 |
|---|---:|---:|
| `c7 8x <disp32> <imm32>` immediate stores in `.text` | **24** | **9** |
| immediates seen | 0 ×21, 3 ×1, others | 0 ×7, 1 ×1, 0x1af ×1 |
| `movss [reg+disp], xmm` stores | 17 | 25 |
| functions writing **both** offsets | **0** | **0** |

The last line is the new negative: no function in the image writes both fields, so there is no
"throttle split" routine that could be identified by co-location. The values written are 0 or small
integers that cannot be throttle factors, and 0x2e4/0x2e8 are small displacements shared by many
classes (chase-06 already rejected the `AkPlayerVehicleSoundInfo` lookalikes at the same offsets).
With no symbols and no `BattleModeFrontThrottle` string in the exe (verified by chase-06), no store
can be tied to `RVehicleSimBatmobile`.

### 4. Routes not tried by chase-06, checked and negative

- **(a) INI files.** `BmGame/Config/*.ini` (BmGame.ini, BmEngine.ini, BmGame.ini, DefaultGame.ini,
  …) contain no `BattleModeFrontThrottle` / `BattleModeRearThrottle`:

  ```
  $ grep -ri "BattleModeFrontThrottle\|BattleModeRearThrottle" BmGame/Config/
  (no output, exit 1)
  ```

- **(a) CDO re-read with an independent reader.** `ch1_dlo.py dlo BmGame.upk
  Default__RVehicleSimBatmobile` (a different script from chase-06's `chase02_cdo.py`) reproduces the
  same block and the same two gaps: 0x2e0 tagged, 0x2e4/0x2e8 absent, 0x2ec tagged.
- **(b) constructor located by class-unique values.** Attempted (section 2); the class has no
  value-setting constructor, so this route cannot supply the number.
- **(c) captures.** Unchanged: a per-tick throttle factor is not a measurable frame quantity, and no
  capture isolates one (chase-06's clip inventory).
- **(d) published sources.** Not used; a wiki or forum figure would be a gameplay impression, not
  this build's field, and it could not outrank a file value (R4).

---

## F-44 · `BattleModeFrontThrottle` (0x2e4) — STILL UNKNOWN (default 0.0)

**Value:** **no shipped value**; the class default is **0.0** and the field is written at runtime,
by code this pass could not attribute. A port must not read 0.0 as "the battle-mode front throttle
is zero" — the field is state, not a tuned parameter.

**Provenance:** the 0.0 is `decoded` (CDO omission under the zero-skip rule, verified on three
objects); the runtime value is **UNKNOWN**.

**Evidence:** `Default__RVehicleSimBatmobile` (`BmGame.upk`, `export[129779]`, 724 B, 58 tags) has no
tag at 0x2e4, while 0x2e0 = 0.3 and 0x2ec = 5.0 bracket it; all 58 tags are non-zero, and
`Default__Pawn` (59 tags) and `Default__RVehicleBatmobileBase` (201 tags) behave the same way; no
immediate store of any CDO value exists at its own displacement; the 24 immediate stores at 0x2e4 in
`.text` hold 0, 3 or other non-throttle integers, and no function writes both 0x2e4 and 0x2e8.

**Routes tried this pass:** (a) CDO + INIs + a second reader — negative; (b) constructor by
class-unique values — the class has none; store attribution — 24 sites, none bindable; (c), (d) not
applicable.

## F-45 · `BattleModeRearThrottle` (0x2e8) — STILL UNKNOWN (default 0.0)

**Value:** **no shipped value**; class default **0.0**; runtime value UNKNOWN. Same limits as F-44.

**Provenance:** the 0.0 is `decoded` (same omission rule); the runtime value is **UNKNOWN**.

**Evidence:** no tag at 0x2e8 in `Default__RVehicleSimBatmobile`; 9 immediate stores at 0x2e8 in the
whole image (0 ×7, 1 ×1, 0x1af ×1 — none a throttle factor); 25 `movss` sites; no function writes
both throttles; the only 1.0/2.0 values at these offsets belong to `AkPlayerVehicleSoundInfo` and
stay rejected (chase-06's lookalike check, re-confirmed by the class-scoped read here).

**Routes tried this pass:** identical to F-44.

---

## What changed for the project

1. **The two rows keep `UNKNOWN`, but the reason narrows again:** not "the files do not carry the
   field" (they declare it, 0x2e4/0x2e8, `FloatProperty`, in the BmAK SDK binding) and not "the CDO
   is unreadable" (it is read; it omits the field because its value is the class default 0). It is
   that the field is runtime state with no shipped tuning value.
2. **A translation cannot take a number from here.** The other six battle-mode fields in chase-06
   do have values (80.0, 0.5, 0.025, 1200.0, 90.0, 1.0); these two do not, and a mod that wants a
   front/rear throttle split must choose its own, declared as a design choice.
3. **A cheap negative to reuse:** on this class, `findimm` finds no immediate store of any CDO
   value — the class is data-initialised, so any future "is there a constructor?" question about
   `RVehicleSimBatmobile` is already answered.

## Reproduce

```
python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RVehicleSimBatmobile
python Tools/scripts/chase/chase2_native.py findimm 0x2e4
python Tools/scripts/chase/chase2_native.py findimm 0x2e8
python Tools/scripts/chase/chase2_native.py findimm 0x2cc --imm 0x42a00000
grep -ri "BattleModeFrontThrottle" "E:/Games/Batman - Arkham Knight/BmGame/Config/"
```

`chase2_native.py` opens `BatmanAK.exe` with `rb` only. No game was launched, nothing under
`E:/Games` or `D:/Games` was written, `FOOTAGE.md`, `chase-06.md`, `GRAB_BACKLOG.md` and `MODLOG.md`
were not edited, nothing was committed, and no secret is in this file.

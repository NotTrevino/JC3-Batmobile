# The radar setters the plan must drive, checked name-by-name and range-by-range against the grab

Card: 8820-radar-setters-against-hud-grab. 2026-11-08.

**Answer in one paragraph.** The plan
(`tmp/freebuff/reports/radar-setters-to-jc3-minimap-plan.md`) says **15** radar setters must be driven
(plan:31) and gives a value range for **9** of them; the other 6 are `void` or string-only. Against
the two grab documents, **3 of the 15 are named and ranged consistently in both** (`#2`, `#4`, `#14`),
**8 are named in `HUD.md:219` but carry no range there and are not mentioned at all in
`G3-HUD-RADAR.md`**, and **4 are absent from both** (`UC_DoIntro`, `UC_DoOutro`, `UC_SetVisualMode`,
`UC_SetRootsPermanentlyVisible`). Where the plan and `HUD.md` disagree, the plan is **narrower** and
`G3-HUD-RADAR.md` supports the plan: `HUD.md` calls the 4th argument of `UC_UpdateTargetPosition` and
the 2nd argument of `UC_SetLockonValue` a **"kind"**, while the grab's decoded AS3 says they are a
**dot count** and an **urgency threshold** (`G3-HUD-RADAR.md:41-42`, PASS assertion at
`G3-HUD-RADAR.md:101`). `HUD.md:219` also writes `UC_SetPlayerPosition(x,y,z)`; the grab says the first
argument is an **angle** (`G3-HUD-RADAR.md:43`). The one number the grab supports most strongly is
**80 px per distance unit** (`G3-HUD-RADAR.md:38` and `:45`, PASS at `:102`); the units *above* that
scale — a radar radius in metres or in radar units — are **UNKNOWN in every file**, and the plan
doesn't claim them either.

**Intended change / file / revert.** This card *creates one new file*,
`tmp/freebuff/reports/radar-setters-against-hud-grab.md`; it is the file the card's DONE line names.
It edits nothing else. **Revert = delete this file.**

## 0. Which files were read (the brief's paths have no `tmp/freebuff/` prefix)

| brief says | actual path | exists? |
|---|---|---|
| `reports/radar-setters-to-jc3-minimap-plan.md` | `tmp/freebuff/reports/radar-setters-to-jc3-minimap-plan.md` | **yes**, 172 lines |
| `reports/G3-HUD-RADAR.md` | `tmp/freebuff/reports/G3-HUD-RADAR.md` | **yes**, 143 lines |
| `Research/BatmobileGrab/HUD.md` | same, no prefix needed | **yes**, 344 lines |

There is no `reports/` directory at the repository root; `glob reports/*.md` returns only two
unrelated files. Both named documents live under `tmp/freebuff/reports/`, which is also where this
report lives, so "reports/…" is read as `tmp/freebuff/reports/…` throughout. `G3-HUD-RADAR.md`
**does exist**, so the brief's "if it exists" condition is satisfied and every setter is checked
against it.

Citation convention: `file:line` = the line number in that file, read with `grep -n` this session.
`HUD_INTERFACES.json` has no line numbers, so its rows are cited by key path
(`HudModuleBespokeLocalRadar.setters[name].args`). "The grab" = `HUD.md` plus the
`HUD_INTERFACES.json` it points at (`HUD.md:37`) plus `G3-HUD-RADAR.md`; all three describe the same
carved movie — `HUD.md:23` pins `HudModuleBespokeLocalRadar.Image` at 66,317 / 139,264 B,
sha256 `f9f622d5a068…`, and `G3-HUD-RADAR.md:15` pins the same payload to
`Working/HUD/radar.gfx`.

## 1. The 15 setters the plan says must be driven

Read out of the plan's numbered table (`plan:90`–`plan:104`), one row per setter, in the plan's own
order. Every row below is a setter the plan assigns a build step to, i.e. one it says must be driven.

### 1.1 Is each name in the grab?

| # | setter as the plan writes it | plan | `HUD.md` | `G3-HUD-RADAR.md` | `HUD_INTERFACES.json` `.args` | name confirmed? |
|---|---|---|---|---|---|---|
| 1 | `UC_PushHeavyTanksToFlash(int count, Boolean jammed)` | `plan:90` | `HUD.md:219` — bare name, no parameters | **absent** | `param1:int, param2:Boolean` | HUD.md yes (name only); G3 no; JSON confirms arity |
| 2 | `UC_UpdateTargetPosition(Number angle, Number distance, Number bearing, int dots)` | `plan:91` | `HUD.md:219` — `UC_UpdateTargetPosition(x,y,z,kind)` | `G3-HUD-RADAR.md:37` | `param1:Number, param2:Number, param3:Number, param4:int` | **yes in both**; HUD.md's 4th-arg name contradicts |
| 3 | `UC_SetStationaryLockonValue(Number value)` | `plan:92` | `HUD.md:219` — bare name | **absent** | `param1:Number` | HUD.md yes (name only); G3 no |
| 4 | `UC_SetLockonValue(Number value, Number threshold)` | `plan:93` | `HUD.md:219` — `UC_SetLockonValue(value, kind)` | `G3-HUD-RADAR.md:41` | `param1:Number, param2:Number` | **yes in both**; HUD.md's 2nd-arg name contradicts |
| 5 | `UC_SetHealthTitle(String title)` | `plan:94` | `HUD.md:219` — collapsed as `UC_SetHealthTitle/Value` | **absent** | `param1:String` | HUD.md yes (collapsed); G3 no |
| 6 | `UC_SetHealthValue(Number value, Boolean critical)` | `plan:95` | `HUD.md:219` — same collapsed token | **absent** | `param1:Number, param2:Boolean` | HUD.md yes (collapsed); G3 no |
| 7 | `UC_DoOutro()` | `plan:96` | **absent** | **absent** | `""` (no args) | **no in both**; only the JSON has it |
| 8 | `UC_DoIntro()` | `plan:97` | **absent** | **absent** | `""` (no args) | **no in both**; only the JSON has it |
| 9 | `UC_SetVisualMode(Boolean radar, Boolean tanks)` | `plan:98` | **absent** | **absent** | `param1:Boolean, param2:Boolean` | **no in both**; only the JSON has it |
| 10 | `UC_SetRootsPermanentlyVisible(Boolean on)` | `plan:99` | `HUD.md:219` — wildcard `UC_SetRootNetwork*`; the glob does **not** match `SetRoots…` | **absent** | `param1:Boolean` | **no in both** (glob misses it) |
| 11 | `UC_DoPulse(Number seconds)` | `plan:100` | `HUD.md:219` — bare name | **absent** (no formula either) | `param1:Number` | HUD.md yes (name only); G3 no |
| 12 | `UC_SetRootNetwork(String className)` | `plan:101` | `HUD.md:219` — wildcard `UC_SetRootNetwork*` covers it | **absent** | `param1:String` | HUD.md yes (via glob); G3 no |
| 13 | `UC_SetMaskEnormous(Boolean enormous)` | `plan:102` | `HUD.md:219` — bare name | **absent** | `param1:Boolean` | HUD.md yes (name only); G3 no |
| 14 | `UC_SetPlayerPosition(Number angle, Number x, Number z)` | `plan:103` | `HUD.md:219` — `UC_SetPlayerPosition(x,y,z)` | `G3-HUD-RADAR.md:43` | `param1:Number, param2:Number, param3:Number` | **yes in both**; HUD.md's 1st-arg name contradicts |
| 15 | `UC_SetRootNetworkOpacity(Number alpha)` | `plan:104` | `HUD.md:219` — wildcard covers it | **absent** | `param1:Number` | HUD.md yes (via glob); G3 no |

Counting the names: `HUD.md:219` covers **11 of 15** — it names 9, collapses `SetHealthTitle/Value`
into one token (+2 setters) and wildcards `SetRootNetwork*` (+1 more than the token lists). The 4 it
omits are exactly `#7`, `#8`, `#9`, `#10`. `G3-HUD-RADAR.md` names **3 of 15** explicitly
(`#2` at `:37`, `#4` at `:41`, `#14` at `:43`); it confirms the **count** of 15 twice
(`G3-HUD-RADAR.md:5`, and as a passing assertion at `G3-HUD-RADAR.md:100`) but is otherwise silent on
individual names.

### 1.2 What range does the plan give, and does the grab give it?

| # | setter | plan's range / limit (`plan` line) | range in `HUD.md` | range in `G3-HUD-RADAR.md` | who supports it |
|---|---|---|---|---|---|
| 1 | `UC_PushHeavyTanksToFlash` | `count` = number of tanks declared (no upper bound); flat int array of 5 per tank `(ArrayIndex, PositionX, PositionY, Bearing, MovieFrame)`; `ArrayIndex == -1` makes `bearing` the **radius scale**; `MovieFrame` `-10000` = keep previous frame (`plan:90`) | none — name only (`HUD.md:219`) | **`-10000` = keep the previous frame** (`G3-HUD-RADAR.md:33`) | the `-10000` sentinel yes; `count`/array shape only in the plan |
| 2 | `UC_UpdateTargetPosition` | **80 px per distance unit**; `rotation = bearing * 57.3`; 4th arg = a **dot count** (`plan:91`, restated `plan:32`) | none | **80 px/unit** (`G3-HUD-RADAR.md:38`, `:45-46`, PASS `:102`); `57.3` (`:38`); 4th arg = `NumTrackingDots` (`:41`, PASS `:101`) | **the grab supports all three**; absolute range/radius = UNKNOWN (`G3-HUD-RADAR.md:45-46`) |
| 3 | `UC_SetStationaryLockonValue` | bar `scaleX = value`, visible while `value > 0.01` → **0…1** with a 0.01 floor (`plan:92`) | none | **absent** | **neither grab doc states 0…1 or the 0.01 floor** |
| 4 | `UC_SetLockonValue` | `value` is the bar fill with state 0 at `value == 1`; 2nd arg is a **threshold**, constant **0.3** in the debug keys (`plan:93`) | none — and it calls the 2nd arg a "kind" (`HUD.md:219`) | 2nd arg is an **urgency threshold** (`G3-HUD-RADAR.md:41-42`) — **no numeric value** | the *threshold* reading yes; the **0.3** value **no** |
| 5 | `UC_SetHealthTitle` | no numeric range — a `String` (`plan:94`) | none | **absent** | consistent (nothing claimed, nothing contradicted); JSON says `String` |
| 6 | `UC_SetHealthValue` | target bar `scaleX = value`, visible above `0.01` → **0…1**, plus a `critical` boolean (`plan:95`) | none | **absent** | **neither grab doc states 0…1 or the 0.01 floor** |
| 7 | `UC_DoOutro` | no arguments, no range (`plan:96`) | **absent** | **absent** | nothing to support |
| 8 | `UC_DoIntro` | no arguments, no range (`plan:97`) | **absent** | **absent** | nothing to support |
| 9 | `UC_SetVisualMode` | two booleans (`radar`, `tanks`) (`plan:98`) | **absent** | **absent** | types only, via the JSON (`Boolean, Boolean`) |
| 10 | `UC_SetRootsPermanentlyVisible` | one boolean, on/off (`plan:99`) | **absent** | **absent** | type only, via the JSON (`Boolean`) |
| 11 | `UC_DoPulse` | `seconds`, rendered as a frame offset `totalFrames - 55 - seconds*30`, clamped to ≥ 1 frame (`plan:100`) | none | **absent**; `totalFrames` is elsewhere reported UNKNOWN | **neither** — plan-only formula |
| 12 | `UC_SetRootNetwork` | no numeric range — a symbol class-name `String` (`plan:101`) | none | **absent** | consistent; JSON says `String` |
| 13 | `UC_SetMaskEnormous` | mask `scaleX`/`scaleY` = **8 or 1** (`plan:102`) | none | **absent** | **neither** — 8/1 is plan-only |
| 14 | `UC_SetPlayerPosition` | `RootNetwork.rotation = angle * 57.3`; `hypot(x,z)` + `atan2(-x,z) - angle`; **2-D x,z, no altitude** (`plan:103`) | none — and it calls the three args `x,y,z` (`HUD.md:219`) | **`UC_SetPlayerPosition(angle, x, z)`**, `rotation = angle*57.3`, "**2-D x,z** map, no altitude" (`G3-HUD-RADAR.md:43`) | **the grab supports the plan** |
| 15 | `UC_SetRootNetworkOpacity` | `alpha` on `RootNetwork.alpha` → **0…1** (`plan:104`) | none | **absent** | **neither** — 0…1 is plan-only (implied by the POI `m_IconAlpha` row, not stated by a grab doc) |

## 2. Where the plan and the grab disagree, and which one the grab supports

Three name-level conflicts, all inside `HUD.md:219`, all resolved **in the plan's favour** by the
decoded AS3 that `G3-HUD-RADAR.md` records. In each case the plan's range is the **narrower** one:

| conflict | plan says (narrower) | `HUD.md:219` says (wider) | grab's verdict | which the grab supports |
|---|---|---|---|---|
| 4th arg of `UC_UpdateTargetPosition` | `int dots` — a **count** of trailing path dots, so the domain is small non-negative integers | `kind` — implies an icon/enum selector, i.e. an open-ended type space | `G3-HUD-RADAR.md:41`: "The 4th argument is not a kind: it is passed to `Private_VehicleTracker(param1)`, which sets `NumTrackingDots`"; PASS at `:101` | **the plan**; `kind` is refuted |
| 2nd arg of `UC_SetLockonValue` | `Number threshold` — an urgency cut-off compared as `value > threshold` | `kind` — again an enum selector | `G3-HUD-RADAR.md:41-42`: "second argument is an urgency threshold (`value > threshold` → `State1`, else `State2`)" | **the plan**; `kind` is refuted |
| 1st arg of `UC_SetPlayerPosition` | `Number angle` — radians, multiplied by 57.3 | `x` — a coordinate | `G3-HUD-RADAR.md:43`: "`UC_SetPlayerPosition(angle, x, z)` sets `RootNetwork.rotation = angle*57.3`" | **the plan**; `x,y,z` is refuted |

Where the plan is **wider** than the grab, it is a coverage gap rather than a contradiction:

| gap | detail |
|---|---|
| 4 setters the plan drives that `HUD.md:219` never lists | `UC_DoIntro` (`plan:97`), `UC_DoOutro` (`plan:96`), `UC_SetVisualMode` (`plan:98`), `UC_SetRootsPermanentlyVisible` (`plan:99`). The last is missed only because `HUD.md`'s wildcard is spelled `UC_SetRootNetwork*` and does not match `SetRoots…`. All four are present in `HUD_INTERFACES.json` (args `""`, `""`, `Boolean,Boolean`, `Boolean`), so the grab's machine form is wider than its prose. |
| arity the plan splits and `HUD.md` merges | `HUD.md:219`'s `UC_SetHealthTitle/Value` is 2 setters in the plan (`plan:94`, `plan:95`); the JSON splits them too (`String` / `Number,Boolean`), so the grab supports the plan's arity. |
| 15 vs 21 vs 252 | the plan says **15** in the module AS3 and notes `HUD_INTERFACES.json` lists **21** rows, the extra 6 being inherited module calls (`plan:31`). The JSON confirms exactly that: 15 radar setters + `UC_GetDeferredExternalCalls`, `UC_SetColorTransform`, `UC_SetSelectiveVisibilityModule`, `UC_ShakeAndFlashHud`, `UC_ShakeEntireHud`, `UC_TestNextSelectiveVisibilityModule`. `HUD.md:37` reports only the corpus total, **252** setters across 19 movies. So `HUD.md` alone cannot give the radar count; `G3-HUD-RADAR.md:5`/`:100` agrees with the plan's 15. |

## 3. Ranges the plan gives that no grab document supports

Stated plainly, because these are numbers a reader might otherwise assume were verified:

1. **0…1** for `UC_SetStationaryLockonValue` / `UC_SetHealthValue` / `UC_SetRootNetworkOpacity`
   (`plan:92`, `plan:95`, `plan:104`), and the **`> 0.01` visibility floor** in the first two. No
   grab doc gives either. The plan's own basis is the AS3 (`Bar.Element.scaleX = value`), not the
   grab.
2. **Threshold `0.3`** for `UC_SetLockonValue` (`plan:93`). `G3-HUD-RADAR.md:41-42` confirms the
   *role* of the argument, not the constant.
3. **Mask scale `8` or `1`** for `UC_SetMaskEnormous` (`plan:102`). Neither grab doc mentions a
   multiplier.
4. **`totalFrames - 55 - seconds*30`, clamp ≥ 1** for `UC_DoPulse` (`plan:100`). `G3-HUD-RADAR.md`
   never states the formula, and the recheck classifies the pulse period as UNKNOWN.
5. **The array shape** `[count, (ArrayIndex, PositionX, PositionY, Bearing, MovieFrame) × n]` for
   `UC_PushHeavyTanksToFlash` (`plan:90`). `G3-HUD-RADAR.md:33` supports only the `-10000` sentinel.

Conversely, the one numeric range the grab supports and the plan also uses is the **80 px/unit**
scale with the **×57.3** radian→degree factor — `plan:32`, `plan:33`, `plan:91`, `plan:103`, `plan:162`
against `G3-HUD-RADAR.md:38`, `:43`, `:45`, `:102`. Neither document bounds the scale: a radar radius
in metres or in radar units is **UNKNOWN** in the plan too, and `G3-HUD-RADAR.md:45-46` says so
explicitly ("world radius in metres **UNKNOWN** … the native side owns the divisor"). So the plan's
"range" for `#2` is a **scale, not a bound**, and that is the strongest claim available.

## 4. Checks run

| check | result |
|---|---|
| plan setter census | 15 rows in the numbered table, `plan:90`–`plan:104`, names + parameter lists identical to the plan's `§4` and to `HUD_INTERFACES.json` |
| setter names present in this report | 15/15 (one row each in §1.1 and §1.2) |
| `HUD.md:219` coverage | 11 of 15 setters named/wildcarded; the 4 gaps listed in §2 |
| `G3-HUD-RADAR.md` coverage | 3 of 15 named (`:37`, `:41`, `:43`); count 15 confirmed at `:5` and `:100` |
| range conflicts | 3 found (`kind`/`dots`, `kind`/`threshold`, `x,y,z`/`angle,x,z`), all resolved for the plan by `G3-HUD-RADAR.md` |
| `HUD_INTERFACES.json` | read for `HudModuleBespokeLocalRadar`: 21 rows = 15 + 6 inherited; args match the plan's types |
| movie identity | `HUD.md:23` sha `f9f622d5a068…` = `G3-HUD-RADAR.md:15` same payload, so both docs describe the same carve |
| game launched / anything installed | **no** — nothing was launched, packed or written outside this file |

## 5. UNKNOWNs, each with the file that would settle it

1. **A radar radius / distance bound.** No grab doc and no plan row gives one; `G3-HUD-RADAR.md:45-46`
   calls it UNKNOWN. Settle with `upk_read.py` on `RHudModuleLocalRadar`'s function bodies in
   `BmGame.upk` (the native divisor).
2. **The `0.3` threshold's provenance.** Plan-only (`plan:93`, AS3 700/712). Settle by re-reading
   `ModuleStruct_Bespoke_LocalRadar.as` lines ~700 and ~712 — the grab files read here do not quote it.
3. **`UC_SetVisualMode(radar, tanks)` semantics.** Both grab docs are silent and the plan asserts
   `Radar`→`ShowRadar`/`HideRadar`. Settle with the AS3 at 470–496.
4. **Where the plan and the *native* differ on `UC_PushHeavyTanksToFlash`.** The array is caller-filled;
   no grab doc describes it. Settle with `RHudModuleLocalRadar`'s cached function names and bodies.

**Bottom line for the build:** drive all 15. Take the ranges from the plan, except that only
**80 px/unit**, **×57.3**, **`-10000` = keep frame**, **the 4th arg is a dot count** and **the 2nd
lock-on arg is a threshold** are corroborated by the grab; the 0…1 proportions, the 0.01 floors, the
`0.3` threshold, the 8× mask and the pulse frame formula rest on the plan's own AS3 reading and should
be re-checked against the AS3 before they are treated as pinned.

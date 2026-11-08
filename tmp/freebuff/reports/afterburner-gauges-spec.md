# Afterburner HUD: drawing spec for the hook overlay (7985)

**STATUS: done (report only).** No build, hook, `.gfx`, ledger row or queue brief was written or edited;
nothing was launched.

**Provenance / revert.** New file `tmp/freebuff/reports/afterburner-gauges-spec.md`
(= `E:/Modding/JC3-Batmobile/tmp/freebuff/reports/afterburner-gauges-spec.md`). **Revert = delete this file.**

Labels: **decoded** (file:line / field / clip), **derived** (rule + inputs), **operator-stated**, **UNKNOWN**.

---

## 0. The answer, and the one conflict

| question | answer |
|---|---|
| the gauge movie | **`BmGame.upk:HudModuleBatmobile.Image`** (423,138 B export / 423,056 B CFX / 671,744 B inflated), clip **`HudMaster.LeftSideParent.BoostMovie`**, 55 frames, authored at **(−452.867, 65.55, 24.11)**, yaw 26.0°, scale 1.0 |
| its setters | **`UC_SetBoostLevel(param1:int, param2:int)`** (level 0…100, upgrade level), **`UC_HideBoostGauge()`**, **`UC_ShowBoostUpgrade(param1:String, param2:String)`**; native mirror `RHudModuleBatmobile.SetBoostGauge` |
| value range | `BoostLevel` **0…100** (the body hides the gauge at `>= 100`); `FillMovie.gotoAndStop(BoostLevel + 1)` over a 102-frame fill; `param2` (upgrade level) only toggles the two badges |
| fill direction | **vertical, bottom-anchored**: fill `scale-y` 0.011 → 1.0, the `Cap` rides `y` 9.5 → **−182.5** (192 px travel) |
| the two-gauge layout | **`BoostMovie` has exactly three children** — `BoostChild` (the bar), a 1-frame unnamed clip ch1040 at (5.0, −83.7), and `boost_upgrade_msg` (51 frames at (154.5, −12.6)). The only second element **to the left** is the **badge pair** `Upgrade1`/`Upgrade2` at x **−10.0 / −10.5**, y 96.3 / 100.6, 65 frames, labels `Normal`/`Charging`. **No BmAK setter carries a cooldown value** → the operator's second gauge has **no BmAK data source**; it must be hook-driven from the native cooldown (§3) |
| the boost values | `BoostDuration` **2.0 s**, `BoostCooldown[3]` tier0 **12.0 s** (668/672/676), `BoostCooldownUpgradeLevel` (680), `CurrentBoostTimer` 1.0 (808), `BoostDurationDonut` 6.0 (688), `DriftingBoostCooldown` (684) |
| colours | **UNKNOWN** — no colour is decoded anywhere in `Working/HUD/*.md` or the setter records; the art lives in the movie's `Image_I1*.tfc` bitmaps, never read for RGB |

**The conflict, kept as two facts.** `Working/HUD/CLUSTER.md` §5(c) **refutes** a second cooldown gauge as a
movie element and says a retail cooldown gauge is **UNKNOWN** (0 of 252 setters carry one). The operator
states one is on screen, left of the boost gauge. Both stand: the *movie* has no second gauge; the *game*
has a native cooldown (`BoostCooldown` + `BoostCooldownUpgradeLevel`) that never reaches the movie. The hook
can therefore **draw** the second gauge from the cooldown it already simulates — that is the reading this
spec implements.

---

## 1. Where it sits on screen (decoded placement, derived fractions)

Stage facts (`CLUSTER.md` head): SWF **1024×768**, module stage **1024×720**, projection centre **[512, 384]**,
FOV 56.0. Screen estimate = projection centre + authored x/y (derived; z ≤ 25 against a ~10³ focal length
changes the position < 1 %).

| clip | authored (x, y) | screen (x, y) on 1024×768 | fraction of viewport | note |
|---|---|---:|---|---|
| `HudMaster.LeftSideParent.BoostMovie` | (−452.867, 65.55) | **(59.1, 449.6)** | **x 0.0577, y 0.5854** | the afterburner gauge |
| `HudMaster.RightSideParent.BoostMovie` | (446.0, 180.5) | — (right group) | x ≈ 0.936, y ≈ 0.735 | a **second BoostMovie instance** exists in the right group (`CLUSTER.md` line 17); it is not the pursuit-mode gauge the operator describes, and no setter record distinguishes it — noted so the left/right pair is not mistaken for the two-gauge layout |
| badge `Upgrade1` | (−10.0, 96.3) rel. bar | ≈ (49.1, 480.8) | x 0.0480, y 0.6260 | left of the bar |
| badge `Upgrade2` | (−10.5, 100.6) rel. bar | ≈ (48.6, 485.2) | x 0.0475, y 0.6318 | left of the bar |
| `boost_upgrade_msg` | (154.5, −12.6) rel. bar | ≈ (213.6, 372.6) | x 0.2086, y 0.4852 | a **message**, 51 frames |

Left-group ordering by authored x (most negative = furthest left): `RemoteInterface` −525.275,
`Health` −479.228, `Combo` −460.237, **`BoostMovie` −452.867**. By y (highest first): `Health` −328.3,
`Combo` −263.25, **`BoostMovie` 65.55**, `RemoteInterface` 225.0.

**Size.** The only decoded dimension is the fill travel: **192 px** from `Cap` y 9.5 to −182.5 on the
1024×768 stage → **0.25 of viewport height**. The bar's **width is UNKNOWN** (the `BoostChild` bounds were
not printed by the cluster pass; settler §7 U1). The badge pair sits **10 px** left of the bar's origin →
**0.0098 of viewport width** at 1024.

**Derived drawing box (what 7985 draws):**

| element | anchor (viewport fraction) | size (fraction) | status |
|---|---|---|---|
| boost bar (primary) | bottom-left at **(0.0577, 0.8354)** if the anchor above is the top; or bottom at **(0.0577, 0.7104)** — see note | height **0.25**, width **UNKNOWN** (placeholder 0.012) | anchor derived, size partly UNKNOWN |
| second gauge (cooldown) | bottom-left at **x = 0.0479** (0.0577 − 0.0098), same bottom as the bar | height 0.25, width UNKNOWN (placeholder 0.006) | operator-stated + derived |
| upgrade message | (0.2086, 0.4852) | 51-frame clip | decoded |

*Note on the vertical anchor:* (59.1, 449.6) is the **clip origin**, not a corner; the fill grows upward from
its bottom, and the `Cap` travels 192 px, so the bar's drawn box is `[449.6 … 449.6 + 192]` px **or**
`[449.6 − 192 … 449.6]` depending on the origin side. Which one is **UNKNOWN** (§7 U1) — pick one and verify
against a screenshot; the fractions below treat y as the **bottom** edge (0.5854 → 0.8354 box top).

---

## 2. What drives it (decoded values)

From `Working/HUD/CLUSTER.md` §2 and `Working/Translation/BOOST_COVERAGE.md`:

| member | class | offset | value | role |
|---|---|---:|---|---|
| `BoostDuration` | `RVehicleSimBatmobile` | 664 | **2.0 s** | how long one boost lasts |
| `BoostCooldown` | `RVehicleSimBatmobile` | 668 / 672 / 676 (InlineArray 3) | tier0 **12.0 s** | recharge time after the boost |
| `BoostCooldownUpgradeLevel` | `RVehicleSimBatmobile` | 680 | no default | which cooldown tier is active (**the "quick recharge" upgrade**) |
| `DriftingBoostCooldown` | `RVehicleSimBatmobile` | 684 | no default | the drift-shortened cooldown |
| `BoostDurationDonut` | `RVehicleSimBatmobile` | 688 | 6.0 s | donut-mode duration |
| `CurrentBoostTimer` | `RVehicleSimBatmobile` | 808 | 1.0 (initial) | the live timer the HUD level is derived from |
| `InfiniteBoost` | `RVehicleBatmobileBase` | bit @4568, mask 536870912 | bool bit | infinite boost |

Speed side (for the behaviour, not the gauge): `arcade.nitro_boost` torque ×2, grip ×2, push 15,000 N,
`boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h (43.2 derived); upgraded 20,000 N / +80 (100.92 derived).

**The HUD level is not one of these fields.** `UC_SetBoostLevel` takes 0…100, and the native caller is not
decoded (`CLUSTER.md` §7: "caller native, UNKNOWN"), so the mapping from `CurrentBoostTimer` /
`BoostCooldown` to 0…100 is **derived here** and stated as a formula, not as a decoded identity.

---

## 3. The drawing spec (what 7985 implements)

### 3.1 State the hook already has

```
boosting            : bool         (input held and boost available)
t_boost             : float 0..BoostDuration        (time spent boosting)
t_cool              : float 0..cooldown_tier()      (time since the boost ended)
upgrade_level       : int   0..2                    (BoostCooldownUpgradeLevel)
cooldown_tier()     : BoostCooldown[upgrade_level]  (tier0 12.0 s)
```

### 3.2 Primary gauge (afterburner)

| item | value | label |
|---|---|---|
| value `L` | `boosting ? 100 * (1 - t_boost / BoostDuration) : 100 * clamp(t_cool / cooldown_tier(), 0, 1)` | **derived** from the two decoded phases |
| fill `f` | `L / 100` | derived |
| fill geometry | `scale_y = 0.011 + 0.989 * f` (**decoded**: samples `[0.011, 0.021, 0.031, 0.99, 1.0, 1.0]`), anchored at the **bottom**, matching `Cap` travel 192 px | decoded shape / derived formula |
| discrete alternative | `frame = round(L) + 1` of 102 (what `gotoAndStop(BoostLevel + 1)` does) | decoded |
| visibility | **shown while `L < 100`**, `UC_HideBoostGauge()` at full — i.e. the gauge **disappears when the boost is ready** | decoded |
| charging tell | `SetBoostBarCharging(L > previous_L)` — the bar plays `Charging` while it refills, `Normal` otherwise | decoded |
| drain shake | the `Shake` element exists in the fill clip; frequency/amplitude **UNKNOWN** | decoded presence only |

### 3.3 Second gauge (quick recharge / cooldown), left of the primary

| item | value | label |
|---|---|---|
| source | **`BoostCooldownUpgradeLevel` + the active `BoostCooldown` tier** — the only "quick recharge" quantity the files carry | decoded field, operator-stated gauge |
| value `G` | `100 * (1 - cooldown_tier() / BoostCooldown[0])`, i.e. **0 at the stock 12 s tier, 100 when the recharge has been fully upgraded** | **derived** (no decoded mapping; stated as the build's rule) |
| alternative reading | `G` = recharge progress of the *current* cooldown (`100 * t_cool / cooldown_tier()`) — i.e. the same information as the primary bar's refill | derived alternative; **pick one** (the operator's "speed-up" wording favours the first) |
| geometry | bottom-aligned with the bar, **x = bar_x − 0.0098** (the badges' 10 px offset), height 0.25, width ≈ half the bar's | derived from the badge positions |
| visibility | same rule as the bar (visible while the primary is visible) | derived |

### 3.4 Upgrade badges (decoded, cheap to keep)

`Upgrade1.visible = (level > 0)`, `Upgrade2.visible = (level > 1)` (`CLUSTER.md` §2). Two 65-frame badges,
`Normal` / `Charging`. If the second gauge is drawn, the badges are redundant — keep them only if the
operator wants the exact BmAK look (§8 C3).

### 3.5 Pseudo-code for the overlay

```
per frame (30 Hz to match the movie's tick 0.033 s):
  if boosting: L = 100*(1 - t_boost/2.0)
  else:        L = 100*clamp(t_cool/cooldown, 0, 1)
  if L >= 100: hide(bar); hide(second); return
  show(bar); show(second)
  scale_y = 0.011 + 0.989*(L/100)
  draw(bar, anchor=(0.0577, 0.7104), size=(BAR_W, 0.25*H), fill=bottom-up, scale_y)
  G  = 100*(1 - cooldown/BoostCooldown[0])
  draw(second, anchor=(0.0479, 0.7104), size=(BAR_W/2, 0.25*H), fill=bottom-up, scale_y=G/100)
```

### 3.6 Colours — UNKNOWN, and what to do about it

No colour is decoded: `Working/HUD/*.md` carries none, the setter records carry none, and the movie's art is
bitmap (`Image_I1*.tfc`), not vector fills. Options, in order:

1. **Extract** the fill's tint from the bitmap the `Fill` clip uses (settler §7 U2) — one `ffdec`/texture
   dump; this is the only lore-true route.
2. Until then, the overlay needs *some* colour. A neutral ramp is a **placeholder**, and placeholders are a
   compromise the operator must approve (§8 C1).

The fill direction, anchor, scale samples, visibility rule and charging tell are all decoded, so the gauge's
**geometry** is lore-true even while its **palette** is not yet.

---

## 4. JC3 host route (context for 7985)

| route | support | status |
|---|---|---|
| re-skin `MCI_nitro_meter` | `InitVehicleNitrous(recharge)`, `UpdateVehicleNitrous(recharge)`, `HideVehicleNitrous()`; `SetProgress(0..1)`, ready sound at 1; clips `MCI_nitro_meter`, `MCI_safe_area_bottom_left`, `MCI_vehicle` | decoded API; the meter is **horizontal** (C4) |
| private `ui/hud.gfx` copy | `SetVisibilities` sets `MCI_speedo.visible = true` unconditionally, so a private copy is needed anyway for C3 | derived |
| hook overlay (this spec) | draws both gauges itself; no JC3 member needed | the route the operator's second gauge requires |

---

## 5. What the overlay cannot get from JC3

| need | JC3 member | verdict |
|---|---|---|
| a second bar | none — `MCI_nitro_meter` is the only recharge member | hook draws it |
| an upgrade level | none | hook state (`upgrade_level`) |
| a vertical bar | `MCI_nitro_meter` is horizontal | hook draws it, or C4 |
| boost duration/cooldown timing | `arcade.nitro_boost.boost_blend_time` 0.2 s only; no duration field | hook owns the 2.0 s / 12.0 s clock |

---

## 6. Numbers table (one place, for the implementer)

| name | value | label |
|---|---|---|
| boost gauge anchor | x **0.0577**, y **0.5854** of the viewport (clip origin, 1024×768) | derived |
| boost bar height | **0.25** of viewport height (192 px) | decoded travel |
| boost bar width | **UNKNOWN** (placeholder 0.012 W) | UNKNOWN |
| second gauge x | bar_x − **0.0098** | derived |
| fill scale range | **0.011 → 1.0**, bottom-anchored | decoded |
| fill frames | 102 (`level + 1`) | decoded |
| hide rule | `level >= 100` → hidden | decoded |
| tick | **0.033 s** (30 Hz) | decoded |
| `BoostDuration` | **2.0 s** | decoded |
| `BoostCooldown[0]` | **12.0 s** | decoded |
| `BoostDurationDonut` | 6.0 s | decoded |
| colours | **UNKNOWN** | UNKNOWN |

---

## 7. UNKNOWNs

| # | unknown | what was tried | settler |
|---|---|---|---|
| U1 | bar **width**, and whether the anchor y is the top or bottom edge | `CLUSTER.md` prints the clip transform and the `Cap` travel only | one bounds dump of `BoostChild` from the movie (the same tool that produced the cluster table) |
| U2 | the **colour** of the bar / cap / badge art | no colour in any HUD note or setter record; art is in `Image_I1*.tfc` | extract the fill bitmap's RGB; then set the palette |
| U3 | the native caller's 0…100 mapping | caller is native (`CLUSTER.md` §7) | a hook probe: log level vs `CurrentBoostTimer` for one boost |
| U4 | the second gauge's real source in retail | 0 of 252 setters carry a cooldown; the movie has no second bar | a retail screenshot at two different upgrade levels, or the retail `HUD_SPEC` |
| U5 | drain `Shake` frequency/amplitude | the element exists in the fill clip only | movie timeline dump |

---

## 8. COMPROMISES (operator approval required; this report approves none)

### C1 — the palette is a placeholder
No colour is decoded. Until U2 is settled the overlay must use a placeholder ramp. **Accuracy lost:** the
gauge's colour. **Alternative:** extract the bitmap first; then no compromise is needed.

### C2 — the second gauge has no BmAK data source
The movie has no second bar and no setter carries a cooldown (`CLUSTER.md` §5c). Drawing one is
**operator-stated**, driven by a **derived** formula (§3.3). **Accuracy lost:** nothing decoded is dropped;
the risk is that the real gauge shows something else (U4).

### C3 — badges vs the second gauge
Keeping `Upgrade1/2` *and* the second gauge would draw the same information twice. Recommended: keep the
badges only if the second gauge is dropped. **Accuracy lost:** either the badge art or the gauge.

### C4 — vertical vs horizontal fill
JC3's `MCI_nitro_meter` is horizontal; BmAK's fill is vertical, bottom-anchored. The hook overlay draws
vertical (lore-true); the `MCI_nitro_meter` re-skin route cannot. **Accuracy lost (if the re-skin is chosen):**
the vertical rise.

---

## 9. Sources and commands run

```
python Tools/scripts/bmak_hud_cluster.py --write/--check        (generated Working/HUD/CLUSTER.md)
  BoostMovie authored (-452.867, 65.55, 24.11) yaw 26.0, 55 frames
  UC_SetBoostLevel(param1:int, param2:int); fill gotoAndStop(BoostLevel+1); hide at >=100
  Fill 102 frames; scale-y samples [0.011, 0.021, 0.031, 0.99, 1.0, 1.0]; Cap y 9.5 -> -182.5
  badges Upgrade1/2 at (-10.0, 96.3) / (-10.5, 100.6), 65 frames, ['Charging','Normal']

python (HUD_SPEC.json)
  bmak/uc_setters: UC_SetBoostLevel(param1:int, param2:int), UC_HideBoostGauge(),
                   UC_ShowBoostUpgrade(param1:String, param2:String)
  jc3/vehicle_api:  InitVehicleNitrous(recharge:Number), UpdateVehicleNitrous(recharge:Number),
                    HideVehicleNitrous(), InitPrimaryMeter(type:int,big_tick:Number,max_value:Number)
  jc3 clip list:    MCI_nitro_meter, MCI_safe_area_bottom_left, MCI_vehicle

python (HUD_INVENTORY.json)
  native_modules[1] RHudModuleBatmobile, movie HudModuleBatmobile.Image, setter SetBoostGauge (cached)

grep -i boost / recharge / cooldown Working/Translation/BOOST_COVERAGE.md
  BoostDuration 2 s | BoostCooldown tier0 12 s | BoostDurationDonut 6 s | CurrentBoostTimer 1.0
  arcade.nitro_boost: torque x2, grip x2, push 15000, blend 0.2 s, +40 km/h (43.2 derived)
```

**Not done:** no `.gfx`, hook source or build tree was touched; nothing launched. **Revert = delete this
file.**

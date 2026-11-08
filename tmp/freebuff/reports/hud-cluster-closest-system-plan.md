# HUD cluster — the closest-system build plans (closing `G3-HUD-CLUSTER.md`'s "no member" lines)

WHAT THIS IS: the closing half of `tmp/freebuff/reports/G3-HUD-CLUSTER.md`. That report decoded the
BmAK cluster and then, at six places, ended in "none", "no JC3 member", "stated absence" or "UNKNOWN".
Per the memory rule `closest-system-rule` the gap is closed by the build, so each of those six lines
becomes a plan below: the closest JC3 system, the exact members/files, the numbers derived from the
BmAK data, the evidence level with the file that would settle it, and one pilot-card sentence.

WHAT THIS IS NOT: a re-statement of the decode. The clip transforms, the 102-frame fill, the 0.05/frame
sweep and the 5 armour tiers are **taken as read** from `G3-HUD-CLUSTER.md` / `Working/HUD/CLUSTER.md`;
this file only adds the build. Nothing here was built, run or installed.

## 0. The one idea that closes three of the six

`G3-HUD-CLUSTER.md` treats "the native caller" as the blocker for every gauge: `InitVehicleNitrous` /
`InitVehicleWeapons` have 0 call sites in the movie except 2 demo calls in `TestConstructor`
(`Research/JC3Grab/JC3_HUD_WEAPONS.md` §2, §7). But JC3 **already feeds one vehicle HUD element from
native every frame for every armed vehicle**: the two weapon slots. `B-06` bound 4 weapon components
(`w602` on `main_weapon`, `w603` on root `id:00568A74`, both `weapon_type` 2) and `T-HUD11`/`T-HUD16`
map them onto `MCI_vehicle_weapons0/1`; `T-HUD13` proves both icon ids ship.

That slot clip is not one widget, it is **seven** (`MCI_bullet_bar`, `MCI_inventory_infinity`,
`MCI_selected_weapon_icon`, `TXT_bullet_ammo`, `TXT_name`, `TXT_selected_inventory_ammo`,
`TXT_slash_mark`) plus three sub-parts of the bar (`MCI_bullet_bar_anim`,
`MCI_radial_loader_cooldown`, `alpha`) — `Research/JC3Grab/JC3_HUD_WEAPONS.md` §3. Three of those
carry exactly the three gauges this report called absent:

| BmAK gauge the report called absent | widget already in `MCI_vehicle_weapons1` | member that feeds it |
|---|---|---|
| boost **recharge** (the "second gauge", C1) | `MCI_radial_loader_cooldown` | `weapon_cooldown` 0..1, `-1` hides (arg 7 of init, arg 4 of update) |
| **armour** above 1.0 (C2) | `MCI_bullet_bar` + `MCI_bullet_bar_anim` | `magazine_ammo` / `magazine_size` → frame `65 * ammo / size` |
| **upgrade badge** level (C5) | `MCI_selected_weapon_icon` | `weapon_id` → `textures/ui/weapon_icons/<id>.ddsc` |

So the build does not need a HUD caller for three of the six gaps: it needs the **numbers already in the
weapon tune and the entity** to be the gauge values. The trade-off is stated per plan below; it is not
free (the slot's text fields must stay hidden, and one gauge per widget), but it is the cheapest route
that uses only members proven to be driven.

## 1. C1 — the second (cooldown) gauge

**Report's line** (`Working/HUD/CLUSTER.md` §7): "none (JC3 `MCI_nitro_meter` is the only recharge
member)"; compromise C1 = omit it.

**Closest system**: the per-slot **radial loader**, not the nitro meter. `MCI_radial_loader_cooldown`
with `SetCooldownRotation(slot, value)`: `rot = weapon_cooldown * 360`,
`MCI_mask_0_50.rotation = min(rot, 180)`, `MCI_mask_50_100.rotation = max(rot - 180, 0)`;
`-1` hides the loader (`Research/JC3Grab/JC3_HUD_WEAPONS.md` §3; json proof `cooldown.rot_degrees = 360`).
It is a **0..1 fraction**, i.e. the shape BmAK's cooldown actually has once it is decoded as a timer.

**Files / members**
- `Builds/bm-RC4…/aaf/…/w603_batmobile_vulcan.wtune` — the tune the native weapon HUD reads for slot 1;
  written today by `Tools/scripts/bm_weapons.py --check` (`fire_rate` 0.1 → 0.138 at tune offset 0xA0).
- `Working/Weapons/manifest.json` — the slot binding (`main_weapon` = `w602`, root `id:00568A74` = `w603`).
- `Research/JC3Grab/JC3_HUD_WEAPONS.md` §1–§3 — the argument list and the rotation rule.

**Numbers from the BmAK data** (`Working/HUD/CLUSTER.json` → `native.sim_defaults`,
`Research/BatmobileGrab/HUD.md` §2):
- `BoostCooldown[0]` = **12.0 s** (tier 0; the InlineArray holds 3 floats at 668/672/676, tiers 1–2 are
  UNKNOWN — see §8), `BoostDuration` = **2.0 s**, `BoostDurationDonut` = **6.0 s**,
  `CurrentBoostTimer` = **1.0**, `BoostCooldownUpgradeLevel` = int at 680.
- Build value: `weapon_cooldown = 1 - t_remaining / 12.0` while recharging, `1.0` during the 2.0 s burn.
  At 12.0 s the ring turns **30°/s**; `MCI_mask_0_50` covers 0–6.0 s and `MCI_mask_50_100` 6.0–12.0 s —
  the 180° split lands exactly on `BoostDurationDonut` = 6.0 s, so the two-mask mechanism reports both
  the 6.0 s donut and the 12.0 s full recharge with no new member.
- Slot: **slot 1** (`EVEHICLE_WEAPON_SLOT_ALTERNATIVE`), because slot 0's loader is already assigned to
  the cannon's 5-state map (`T-HUD16`: cooldown = state/4) and `w603`'s own `fire_rate` is 0.138 s
  (`B-06`), a ring too short to see.

**Evidence level**: members **decoded** (G2-25 §3 + json); the 12.0 s → fraction map **derived**; the
slot-1 choice **derived** from `T-HUD11`/`T-HUD16` + `B-06`'s fire_rate.
**What would settle the doubt**: whether `UpdateVehicleWeapons` is in fact called for our built vehicle
every frame — `Builds/bm-RC4…/verify/weapon_points_vs_bmak.md` proves the components are wired
(`V-RC2-weapons`: 5/9 points on their socket) but not that the movie receives an update; the settler is
a live read of the slot (Q-3 #3), and the file that would show it offline is
`Research/JC3Grab/JC3_HUD_WEAPONS.md`'s caller census, which is 0 — so **UNKNOWN, settles at Q-3 #3**.

**Pilot card**: "Fire the boost once; the small ring on the right-hand weapon slot turns smoothly from
full to empty and back to full in ≈12.0 s (±0.3 s), and is invisible at rest." Pass band: one full turn
per recharge, ±0.3 s; loader visible only while charging.

## 2. C2 — armour above 1.0

**Report's line**: "none - no armour field in the vehicle HUD" → compromise C2 = drop the overlay.

**Closest system**: the slot's **segmented bullet bar**. `UpdateVehicleWeapons` writes
`m_MagazineAmmo` and frames `MCI_bullet_bar_anim` at `65 * ammo / size`
(`Research/JC3Grab/JC3_HUD_WEAPONS.md` §1 arg 4, §2 arg 1). A 65-frame bar with a 0..1 driver is a
5×13 segment display if it is fed in 13-frame steps — which is exactly BmAK's tier count.

**Numbers from the BmAK data** (`Research/BatmobileGrab/HUD.md` §4.1):
- `ArmourForeground` fill = `Math.max(0, health - 1)`; `max > 1` selects `Armour<n>`,
  `n = int((max - 1) * 4)` → **5 labels, 5 tiers**.
- Build value: `armour_fraction = clamp(h - 1, 0, 1)`;
  `magazine_ammo = 1 + round(64 * armour_fraction)`, `magazine_size = 65` → tier boundaries at
  **13 / 26 / 39 / 52 / 65** frames, i.e. `n` = 0..4 exactly as BmAK selects `Armour0..4`.
- Never send `0`: `UpdateVehicleWeapons` **returns early when `magazine_ammo <= 0`** (§2), so an empty
  armour overlay must be frame 1 or a `HideVehicleSlotAction`.
- `max_health` 36,000 (`T-DM9`, `B-09`) is what makes `h − 1` reach the armour band at all; the BmAK
  health proportion is 0..2 in effect, so the bar's own 0..1 driver (`T-HUD3` identity map) covers the
  first band and this frame covers the second.

**Trade-off, stated**: with `infiniteAmmo = false` the slot's ammo **text** would show the armour
number. The build keeps `infiniteAmmo = true` (hides both counters, shows `MCI_inventory_infinity` —
§1 arg 3) and feeds the bar anyway, which is what the game does at init: the frame is set from
`magazine_ammo` regardless of the flag.

**Evidence level**: the frame formula and the 65-frame bar are **decoded** (G2-25 §1/§2);
`65/5 = 13` tier alignment is **derived**; that the bar draws while `infiniteAmmo = true` is
**derived** and is the single untested step.
**Settler**: `Research/JC3Grab/JC3_HUD_WEAPONS.JSON`'s `init.params` + a live slot read (Q-3 #3);
offline, the body of `InitVehicleWeapons` as quoted in `JC3_HUD_WEAPONS.md` §1 ("true hides the counters
and shows `MCI_inventory_infinity`, false shows magazine/inventory text and frames
`MCI_bullet_bar_anim` at `65 * ammo / size`") is the only file that speaks to it — it names the frame
inside the *false* branch, so the **true** branch hiding only the text is an inference: **UNKNOWN**.

**Pilot card**: "At full armour the right slot's bar is complete; each 20 % of armour lost removes
exactly one of five equal segments, and the armour loss never moves the health bar." Pass band: 5
segments, ±1 segment per 20 % of the 36,000 HP armour band.

## 3. C5 — the upgrade badges

**Report's line**: "none" / "no JC3 member" (C5 = drop them).

**Closest system**: the slot **icon**, which JC3 resolves *by number*:
`GetWeaponIconName(weapon_id)` → `textures/ui/weapon_icons/<weapon_id>.ddsc` (`_sm.ddsc` for low res;
ids −1 and 0 rejected) — `Research/JC3Grab/JC3_HUD_WEAPONS.md` §6. There is no "badge" member, but there
is a per-slot image whose path the mod controls by choosing the id.

**Numbers from the BmAK data**: `Upgrade1` at (−10.0, 96.3), `Upgrade2` at (−10.5, 100.6), 65 frames
each with labels `Normal`/`Charging`, visible when `upgradeLevel > 0` / `> 1`
(`G3-HUD-CLUSTER.md` §2) — **3 states** (0, 1, 2).

**Build**: ship three icons and select by `upgradeLevel`:
- `textures/ui/weapon_icons/614.ddsc` — **badge state 1**. Id 614 is the one fleet id whose icon was
  never shipped (`w614_monorailmissilecar_missile`, G2-25 §6), so the file is free and nothing vanilla
  draws it; the monorail is not in our vehicle graph, so the collision risk is a *shared* id, not a
  visible one.
- badge state 2 → a second free id (the next unused integer in the 69-id set, chosen when the art is
  cut; `ICON` census in `Research/JC3Grab/INDEX.jsonl` decides it).
- badge state 0 → no art: the slot keeps the weapon's own icon (`603`), which is the true state.

Also available and cheaper if the operator prefers no new art: `ShowVehicleSlotAction` /
`HideVehicleSlotAction` on a third slot is **not** possible (JC3 has exactly 2), so the icon swap is the
only per-slot image mechanism.

**Evidence level**: the id→path rule and the −1/0 rejection are **decoded**; "614 is free" is
**decoded** (G2-25 §6, 69 ids enumerated); the badge mapping is **derived**.
**Settler**: whether an id the fleet never wires resolves without a `weapon_icons/614_sm.ddsc` twin —
`Research/JC3Grab/INDEX.jsonl` (110 files = 69 full + 41 `_sm`) shows the twins are not universal, so
ship both.

**Pilot card**: "With one boost upgrade the right slot's icon changes once; with two it changes again,
and with none it shows the Vulcan's own icon." Pass band: exactly 3 distinguishable icons across the
three upgrade states.

## 4. C3 — the speedometer the Batmobile must not draw

**Report's line**: route derived (private `ui/hud.gfx`), **caller UNKNOWN**; C3 approves nothing.

**Closest system**: JC3's own `MCI_speedo` + `SetVisibilities()`, which is literally
`MCI_speedo.visible = true` — so the build is a **suppression**, not an addition. Members:
`SetVisibilities`, `HideVehicleUi` (hides `MCI_speedo`, `MCI_speedometer`, `MCI_nitro_meter`,
`MCI_jump_meter`, `MCI_bavarium_shield`), `SetVehicleType` (writes only `hud_kph`/`hud_knots`),
`InitPrimaryMeter(type, big_tick, max)` (1 call site), `SetPrimaryMeterValue` (0 call sites),
`SPEEDO_DEGREES = 250`, `SPEEDO_SMOOTHING_TIME = 0.05` (`G3-HUD-CLUSTER.md` §4, `HUD.md` §6).

**Build adds**: a **private copy** of `ui/hud.gfx` (R7: never the shared module, exactly as `B-11`
copied the banks) whose `SetVisibilities` guards the one line:

```
if (m_CurrentType != TYPE_BATMOBILE) { MCI_speedo.visible = true; }
```

with `TYPE_BATMOBILE = 4` added to the type enum — a value the movie never receives today, so no
vanilla vehicle can match it. The movie already switches on `m_CurrentType` for the unit label, so the
member exists; only the value 4 is new. Nothing else in the 260 scripts reads that field
(`SetVehicleType` writes it; 0 other call sites for `SetPrimaryMeterValue`).

**The honest failure mode**: the native caller is what sets `m_CurrentType`, and it is not in any file
(0 call sites in the movie, `JC3_HUD_WEAPONS.md` §7). If the engine never sends 4, the speedometer
stays visible and the route degrades to "hide it for every vehicle", which breaks every other car in
the same install. That is why this plan is gated on one 5-minute experiment, not on a build:

**Probe (5 min)**: patch the private copy to `MCI_speedo.visible = false` unconditionally, install it,
drive the Batmobile and a vanilla car in one session. Pass = speedo gone on both (proves the copy
loads); then the guard is worth building. Fail = the copy does not load, and the whole private-`hud.gfx`
route (C3 **and** §5 route B) is dead with one experiment.

**Numbers from the BmAK data** (why the bar must go, not be blanked): 0 of **252** `UC_*` setters are
speed/rev/gear-shaped, 0 speed tokens in the movie, `bDebugSpeedometer` false in both `.ini`
(`G3-HUD-CLUSTER.md` §4). BmAK's own speed readout is the *native debug* one, so there is nothing to
map — the correct disposition is **suppress** (this is the reopen of `T-HUD1`, which still says
"reuse").

**Evidence level**: members **decoded**; the guard **derived**; whether the private copy loads and
whether type 4 can be delivered **UNKNOWN**.
**Settler**: a live session (above); offline, `E:/Modding/_shared/gamedata/JC3grab/hud/dec` for the loader path
and the receipt from the copy experiment.

**Pilot card**: "In the Batmobile at 120 km/h there is no circular speedometer anywhere on screen; in a
vanilla sports car in the same session the speedometer is back and reads correctly." Pass band: 0
speedo pixels in the Batmobile take, 1 working speedo in the control take.

## 5. C4 — fill direction, the shake and the rising cap

**Report's line**: "keep JC3's orientation and drive `SetProgress(level/100)`; accuracy lost: the
vertical rise and the drain shake."

**Closest system, two routes:**

**Route A (no art work) — use the two mechanisms JC3 already has for exactly this motion.**
- Drain warning: `is_low_ammo` pulses `MCI_bullet_bar` alpha to **0.2 every 0.25 s** and
  `ClearTween`s otherwise (`JC3_HUD_WEAPONS.md` §2 arg 3). BmAK's `Shake` plays while draining and
  `Cap`'s `Decrease` label runs 65 frames = **2.167 s at 30 fps**; the 0.25 s pulse is 8.7× faster, so
  the build uses it as the *drain-visible* signal, not as a copy of `Shake`.
- Rise: the nitro meter's `recharge` is a 0..1 progress (`InitVehicleNitrous(recharge)`,
  `UpdateVehicleNitrous`, `HideVehicleNitrous`, ready sound at 1 — `HUD.md` §6). BmAK's 101 steps
  (`102` frames, `frame = level + 1`) map 1:1 onto `level/100`; the **vertical, bottom-anchored**
  direction is a clip property, not a member, and is lost on this route.

**Route B (art work, gated on the same probe as §4) — import the BmAK fill.**
- Import `DefineSprite` **ch1036** (the 102-frame `Fill`, `Cap` at depth 3) into the private
  `hud.gfx` and drive `Fill.gotoAndStop(level + 1)`; the `Cap` then rides its own timeline as authored
  (`y 9.5 → −182.5`, **192.0 px over 101 steps = 1.901 px/step**).
- Placement: BmAK authors on a 1024×768 surface with projection centre (512, 384); JC3's `hud.gfx` is
  **1280×720** with 260 scripts (`HUD.md` §6). Uniform remap x ×1.25, y ×0.9375 gives
  `(x', y') = (640 + 1.25·x_auth, 0.9375·(384 + y_auth))`:

| clip | BmAK authored (x, y) | JC3 placement (x', y') |
|---|---:|---:|
| `Health` | −479.228, −328.300 | 40.965, 52.219 |
| `BoostMovie` (left) | −452.867, 65.550 | 73.916, 421.453 |
| `Combo` | −460.237, −263.250 | 64.704, 113.203 |
| `RemoteInterface` | −525.275, 225.000 | −16.594, 570.938 |

The non-uniform scale is the caveat: the clips carry **yaw 10°–26°** and the right group −38°/−40°, and
a 4:3 instead of 1.25:0.9375 scale skews a 3D-rotated clip. The build must therefore re-parent under a
container with `scaleX = 1.25`, `scaleY = 0.9375` rather than bake the numbers into each clip's matrix,
and the pilot card below measures the result, not the intent.

**Evidence level**: BmAK clip internals **decoded** (frames, scale-y 0.011→1.0, `Cap` travel);
the remap **derived** (projection not re-solved: z ≤ 56 against a focal length of order 10³, < 1 %
projected error, as `G3-HUD-CLUSTER.md` §1 already states); whether AVM2 GFx v0f art imports into JC3's
loader **UNKNOWN**.
**Settler**: the 5-minute `ffdec -dumpSWF` tag comparison of both movies (SWF/AVM version tags); equal
tags → route B is buildable; unequal → route A only, and C4 stands as the report wrote it.

**Pilot card**: "Hold boost: the bar drains to empty over 2.0 s ±0.2 s and the empty bar pulses; on
release it refills without flicker." Pass band: monotone drain, 101 distinct steps (±1), pulse 4 Hz ±0.5.

## 6. The "none" with no gauge behind it — the damage readout

**Report's line**: `UC_SetImpactDamageFlash(part, x, y, frames)` → "none" / "out".

**Closest system**: two members, both already in the movie for other reasons —
1. `MCI_inflict_damage` — the hit marker; reticle shape `E_RETICLE_NONE = 3` hides it, so it is the
   hit-flash widget (`JC3_HUD_WEAPONS.md` §4).
2. `CreatePoi(type, use_progress_bar, is_minor, label)` — a **labelled** POI
   (`JC3_HUD_WEAPONS.md` §5). The `label` argument is the text carrier that BmAK's `String(frames)`
   needs; no vehicle-cluster text field is otherwise free (`TXT_name` and `TXT_bullet_ammo` are the
   weapon slot's).

**Numbers from the BmAK data**: position = `StageWidth * x`, `StageHeight * y` on the **1024×768**
surface, `rotationY = ±60`, text = the integer `frames`; the bar-level flash is `BG`'s `Pulse`/`Idle`
pair below health 0.2 (`G3-HUD-CLUSTER.md` §3, `HUD.md` §4.1).

**Build**: `POI` at `(1.25 · StageWidth_BmAK · x, 0.9375 · StageHeight_BmAK · y)` =
`(1280·x, 720·y)`, `label = str(damage)`, and `MCI_inflict_damage` shown for the flash duration. The
`±60°` rotation is not a POI member (a POI is a screen-space icon), so it is dropped — that is the
accuracy cost, named rather than hidden.

**Evidence level**: `MCI_inflict_damage` and the `CreatePoi` signature **decoded** (G2-25 §4/§5); the
coordinate map **derived**; whether a POI label draws arbitrary text at a caller-chosen position is
**UNKNOWN** — the file that settles it is `hud_code/poi.as`'s case for the chosen type plus a live POI.
**Settler**: `Research/JC3Grab/JC3_HUD_WEAPONS.md` §5 names the icon per type but not the label
placement; the missing evidence is a decoded `poi.as` body, not available in this repo.

**Pilot card**: "Take one hit on the front wing: a number appears within 1 frame of the impact, within
8 px of the wing's screen position, and fades with the hit marker." Pass band: ≤1 frame latency,
≤8 px placement error, value equal to the BmAK `frames` argument.

## 7. The module question — "custom JC3 module" and "reuse BmAK art" (both UNKNOWN)

`G3-HUD-CLUSTER.md` §5 lists both as UNKNOWN with no evidence either way. They are not left there:

- **Reusing BmAK art**: the probe is the tag comparison in §5's settler. If it passes, the build action
  is one `DefineSprite` import plus the container scale above; if it fails, the fallback is route A and
  the vertical fill is lost — a documented compromise, not a blocker.
- **A custom JC3 module**: `HUD.md` §6 records that JC3's HUD is one movie with 260 scripts and 9 DDS
  atlases, and `ModularHudBm3`-style module hosting is a **BmAK** concept; no JC3 file loads a second
  HUD movie. The closest JC3 equivalent is therefore not a module but a **clip inside the private
  `hud.gfx`** — i.e. route B of §4/§5. The build does not attempt a module loader, and the row that
  asked for one collapses into route B.

## 8. UNKNOWNs this plan carries (each with its settler)

| # | unknown | why it matters | file/probe that settles it |
|---|---|---|---|
| U1 | `BoostCooldown` tiers 1 and 2 | the loader's full-turn time is 12.0 s only at tier 0; a tuned car shows a different ring | `RVehicleSimBatmobile.g.cs` InlineArray at 668/672/676 — only the CDO default is decoded (`Working/HUD/CLUSTER.json` `native.sim_defaults`) |
| U2 | does `UpdateVehicleWeapons` run for our built entity every frame | C1, C2 and C5 all ride on it | live slot read at Q-3 #3; offline the caller census is 0 (`JC3_HUD_WEAPONS.md` §7) |
| U3 | does `MCI_bullet_bar` draw when `infiniteAmmo = true` | C2's whole route | the `InitVehicleWeapons` body quoted in §1 of `JC3_HUD_WEAPONS.md` names the frame in the *false* branch only |
| U4 | can the native side deliver `m_CurrentType = 4` | C3's guard, and route B's survival | a live session; the caller is native (0 call sites) |
| U5 | does a private `ui/hud.gfx` copy load at all | C3 and route B share this single gate | the §4 probe (unconditional hide, one session, two cars) |
| U6 | AVM2 GFx v0f → JC3 loader compatibility | route B | `ffdec -dumpSWF` tag compare of `HudModuleBatmobile.Image` vs `ui/hud.gfx` |
| U7 | POI label text placement | §6 | decoded `hud_code/poi.as` (not in this repo); live POI otherwise |
| U8 | what `ch1040` is (1-frame clip in `BoostMovie`) | it is in the clip we would import | the original FLA (not shipped); `SymbolClass` has no entry |

## 9. Build order and the gates that prove each step

| step | change | proof (all offline, read-only where marked `--check`) |
|---|---|---|
| 1 | U6 probe (tag compare) | equal SWF/AVM tags, both movies — 5 min, decides route B |
| 2 | U5 probe (unconditional hide in a private copy) | one session, two cars |
| 3 | slot-1 gauge values in the entity/tune (`weapon_cooldown`, `magazine_ammo`/`size`, icon id) | `python Tools/scripts/bm_entity.py --check`, `python Tools/scripts/bm_weapons.py --check`, `python Tools/scripts/bm_weapons.py --check` against the RC4 tree, `python Tools/scripts/bm_rc4.py --check` |
| 4 | private `ui/hud.gfx` with the type guard (route A gauges) | `python Tools/scripts/bm_rc4.py --check` + V-03 wiring (`python Tools/scripts/v03_wiring.py --check` for the dangling refs) |
| 5 | route B (clip import + container scale) only if steps 1–2 pass | V-01 file gates (`python Tools/scripts/v01_rc4.py --check`) and the pilot card of §5 |
| 6 | badge icons (`614.ddsc` + twin) | `python Tools/scripts/bm_rc4.py --check` file census; `INDEX`-style id uniqueness re-derived by `bm_rc4.py` |

Standing gates unchanged: `python Tools/scripts/bmak_hud_cluster.py --check`,
`python Tools/scripts/hud_spec.py --check`, `python Tools/scripts/bmak_speedometer.py --check`,
`python Tools/scripts/t19_hud.py --check` — none of them is edited by this plan, and all four must stay
green after step 3 because the slot mapping touches `T-HUD11`…`T-HUD20`.

## 10. What changes in the ledger if these plans are adopted (proposal only, nothing edited)

| current row disposition | becomes | why |
|---|---|---|
| `T-HUD2` "upgrade badges have no member" | `map` (badge = icon id, §3) | a per-slot image keyed by id exists |
| `T-HUD4` armour `out` (stated absence) | `map` (armour = 5×13 bar frames, §2) | the bar is a 0..1 member with 65 frames |
| `T-HUD1` "reuse `MCI_speedo`" | `suppress` (already reopened by the report, C3) | BmAK draws none; the private copy hides it |
| `T-HUD19` missile-box family `out` | stays `out` | the six-kind box family and the aim box genuinely have no JC3 element; the closes are `POI_TYPE_LOCK_ON_TARGET` and `MCI_missile_locked` only, both already mapped |
| new row for the damage readout | proposed `T-HUD21` | `MCI_inflict_damage` + `CreatePoi(label)` (§6) |

No tracker, ledger, script or build tree was edited by this pass. Sources read: `G3-HUD-CLUSTER.md`,
`Working/HUD/CLUSTER.md` §6–§7, `Working/HUD/CLUSTER.json`, `Research/BatmobileGrab/HUD.md` §4–§8,
`Research/JC3Grab/JC3_HUD_WEAPONS.md` §1–§7, `Research/JC3Grab/README.md` §G2-25,
`Working/Translation/T6_HUD_CAMERA.md` §1/§1a, `Research/JC3Grab/G2X.md` rows HUD-1/HUD-2/WPN-12.

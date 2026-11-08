# T-19 · HUD translation — assumption challenge

**Read-only challenge.** Nothing was built, launched, installed or committed; the only file written is
this one. Card: `GRAB_BACKLOG.md` §7 `#### T-19 · HUD translation   S · deps: G2-25, T-11 · serves:
HUD-1/2`, §12 line 1328, `MODLOG.md` §"T-19 · HUD translation — intended change" and §"T-19 · HUD
translation — done". Outputs examined: `Working/Translation/T6_HUD_CAMERA.md` §1a (lines 31–83, between
`<!-- T19-HUD-BEGIN/END -->`), `Working/Translation/t19_hud.json`, `Tools/scripts/t19_hud.py`,
`Research/JC3Grab/JC3_HUD_WEAPONS.json` / `.md` (G2-25), `Research/BatmobileGrab/HUD_INTERFACES.json`,
and the decoded movie at `E:/Modding/JustCause3/_grab/hud/dec/scripts` (260 scripts).

The card's gate, re-run today (exit 0):

```
> python Tools/scripts/t19_hud.py --check
rows 10 over 5/5 elements | map 6 partial 2 out 2 | proofs 12 | kept T-HUD1..3 3/3
doc match True, json match True
check ok
```

The gate checks that the doc, the JSON and the 12 proofs agree with each other and with G2-25. It does
not check any of the *readings* the rows were built from. Two of those readings do not survive the
movie, and one pair of rows contradicts itself.

## VERDICT

| # | assumption the result rests on | verdict |
|---|---|---|
| A1 | "JC3 shows ammo, a cooldown loader and an overcharge tint, **never a heat bar**" → T-HUD17 `out` ("stated absence both sides") | **BROKEN** — JC3's mech weapon clip carries `MCI_thermometer` (WeaponTemp1/2/3), `MCI_overHeat_alert` and per-weapon overheat sounds; `hud_fla/mc_lowerRight_overheatAlert_254.as` is an overheat alert in the vehicle HUD cluster. The search covered the car's two weapon functions and the police heat directory, not the mech weapon clip |
| A2 | T-HUD14 picks reticle shape `E_RETICLE_CANNON` 8 **and** T-HUD15 maps the Vulcan accuracy frame to `reticle_size` | **BROKEN** — shape 8 is in the fall-through group of `UpdateWeaponReticle`: `new_width` is computed for 5 shapes only, so `reticle_size` has no effect on shape 8. The two rows cannot both take effect |
| A3 | "`GetWeaponIconName(weapon_id)` … ids -1 and 0 rejected" (T-HUD13) | **WEAK** — the function has no guard; it builds `textures/ui/weapon_icons/-1.ddsc` for -1. The rejection is a property of the *census* (`icons.rejected_ids`), not of the movie |
| A4 | "ids 602, 603, 618, 619: all four are in the shipped icon set, so both slots draw" (T-HUD13) | **HOLDS** — all four `.ddsc` are in the archive index |
| A5 | "the division by 4 is the only monotone map between the two domains" (T-HUD16, classed `derived`) | **WEAK** — `(4 − state) / 4` is equally monotone and is the other direction; the row's own text concedes the direction is a probe, so the uniqueness claim is what makes it "derived" and it is false |
| A6 | "`MCI_missile_locked` … that is the *incoming* warning, a different instrument" (T-HUD19) | **WEAK** — the two clips exist and are separate, but "incoming" is read from the name: `ShowMissileLocked()`/`HideMissileLocked()` have 0 call sites in the movie, so nothing says whether the warning is for a missile aimed at you or for your own lock. The row's `out` also rests on "no target-kind family", which does hold |
| A7 | slot 0 = `main_weapon` (cannon), slot 1 = `id:00568A74` (Vulcan) ↔ `EVEHICLE_WEAPON_SLOT_MAIN` 0 / `_ALTERNATIVE` 1 (T-HUD11) | **WEAK** — the two slots are decoded (a hard-sized 2-element array) and the two root pointers are decoded, but the *index each pointer gets* is an ordering inference ("first … second", `WEAPON_WIRING.md`), not a stored value |
| A8 | The 6 `VehicleMissileTarget` kinds have no JC3 family (T-HUD19 `out`) | **HOLDS** — 32 `POI_TYPE_*` constants, none for bomb/emp/friend/multi |
| A9 | "0 of 252 setters name heat", "0 of the 37 setter names carry ammo/magazine" | **HOLDS** for heat (0/252); **WEAK** for ammo (a substring scan returns `UC_SetImpactDamageFlash` via "da*mag*e"; the semantic claim is true but the scan is not), and both are typed prose with no proof behind them |
| A10 | `infiniteAmmo = true` hides the counters (T-HUD20, classed `derived`) | **HOLDS** — verified in `hud.as`: `m_HasInfiniteAmmo == false` branch shows the counters, the `else` branch hides them and shows `MCI_inventory_infinity`; `true` is also the parameter's own default |
| A11 | The rows are values a caller can set | **HOLDS as stated, but load-bearing** — `InitVehicleWeapons` has 2 call sites, both in `TestConstructor`; `UpdateVehicleWeapons` and `UpdateWeaponReticle` have 0. The doc says the bridge is native/UNKNOWN (§"The one HUD finding"); no row can be observed until a Q probe |
| A12 | Heat is absent on BmAK's side because it is "a weapon-entity script field with no `UC_*` setter" | **WEAK** — true of the setter scan, but the fields are HUD *geometry*: `HeatBarStart` `[0.79, 0.68]` and `HeatBarSize` `[0.125, 0.03]` are a screen-space rect, and `RBatmobileCannon.HeatUpPerSecond` is recorded as **0.0**, so the donor's bar never fills. Neither fact appears in the row |
| A13 | The police heat explanation ("the movie's own heat code is the 11-state police wanted level") | **HOLDS** — 11 `HEAT_STATE_*` constants (0…10) in `hud_code/heat/heat.as` |
| A14 | The 5 elements T-19 must cover | **HOLDS** — the five names match the card's WPN-12 cell; the list is typed in the script (line 54 `ELEMENTS = [...]`), not parsed from the cell (R11 nit) |

Two BROKEN readings (A1, A2), five WEAK (A3, A5, A6, A7, A9-ammo, A12), the rest hold.

---

## A1 — "JC3 … never a heat bar": the claim T-HUD17's `out` rests on

**The claim.** T-HUD17's `limit` cell (`t19_hud.py`, `SPECS`, and the rendered row):

> BmAK's heat is `HeatBarStart`/`HeatBarSize` on `Batmobile_Cannon_V2`, a weapon-entity script
> field with no `UC_*` setter (0 of 252 setters name heat); JC3 shows ammo, a cooldown loader and
> an overcharge tint, **never a heat bar**

and the block's closing paragraph: "the **heat bar** is absent on both sides (0 JC3 arguments, 0 body
mentions, 0 of 252 BmAK setters)". §12 records it as "heat = stated absence both sides".

**Why it matters.** `out` is only allowed when the element is absent. If an instrument exists anywhere
in the HUD movie, the row is at best `partial`, and the card's "each HUD element mapped or omitted with
proof" is being satisfied by an absence that is not one.

**Test 1 — what the two proofs actually measure.** `t19_hud.py` consumes
`heat.params_with_heat` and `heat.body_mentions` from G2-25's JSON. Both are about
`InitVehicleWeapons` / `UpdateVehicleWeapons`:

```
"heat": {"body_mentions": 0, "params_with_heat": [], "police_heat_dir": "hud_code/heat/",
         "police_heat_states": 11}
```

So the measurement is "no heat in the *car's* two weapon functions". That is true and it is what the row
should say.

**Test 2 — search the rest of the movie for a weapon heat instrument.**

```
> cd E:/Modding/JustCause3/_grab/hud/dec/scripts && grep -n "thermometer|WeaponTemp|MCI_therm" \
      hud.as hud_code/mech/mech_weapon.as hud_code/mech/mech_weapons.as
hud_code/mech/mech_weapon.as:16:      public var MCI_thermometer:MovieClip;
hud_code/mech/mech_weapon.as:131:               this.MCI_thermometer.gotoAndPlay("WeaponTemp3");
hud_code/mech/mech_weapon.as:142:                  this.MCI_thermometer.gotoAndPlay("WeaponTemp3");
hud_code/mech/mech_weapon.as:150:                  this.MCI_thermometer.gotoAndPlay("WeaponTemp2");
hud_code/mech/mech_weapon.as:156:               this.MCI_thermometer.gotoAndStop("WeaponTemp1");
```

`hud.as` (the car's weapon path) has none. `mech_weapon.as` — the **mech's** weapon clip, same movie,
same `weapon_cooldown` argument — has a three-state thermometer and a separate overheat alert:

```
hud_code/mech/mech_weapon.as:12:      public var MCI_overHeat_alert:MovieClip;
hud_code/mech/mech_weapon.as:121:                  this.m_BaseMovie.PlaySound("ui_hud_mech_minigun_overheat");
hud_code/mech/mech_weapon.as:125:                  this.m_BaseMovie.PlaySound("ui_hud_mech_cannon_overheat");
```

driven by `SetCooldown(cooldown)`: `m_IsOvercharged` → Temp3, `cooldown > 0.9` → Temp3, `> 0.5` → Temp2,
else Temp1. And the lower-right cluster of the *vehicle* HUD has its own alert clip:

```
> ls hud_fla | grep -i "lowerright|overheat"
mc_lowerRight_alert_249.as
mc_lowerRight_overheatAlert_254.as

> sed -n '1,30p' hud_fla/mc_lowerRight_overheatAlert_254.as
public dynamic class mc_lowerRight_overheatAlert_254 extends MovieClip
   internal function frame8() : * { gotoAndPlay("Overheat"); }
```

`mc_lowerRight_*` is the same corner the vehicle weapon slots live in (`MCI_safe_area_bottom_right`).

**Test 3 — is there any other reading of these symbols?** `MCI_thermometer` is a `MovieClip` with
frames named `WeaponTemp1/2/3`, driven by the weapon's own cooldown value and overheat flag, with
per-weapon overheat sounds (ids 630 minigun, 631 cannon). There is no other thing that name could be.

**Verdict: BROKEN.** JC3 does have a cannon/minigun heat instrument — a 3-level thermometer plus an
overheat alert plus overheat audio — in the mech weapon clip and the lower-right vehicle cluster. What
is true is the narrower statement: *the car's two-slot clip (`MCI_vehicle_weapons0/1`) has no heat
element, and the car's weapon API takes no heat argument*. The row should be `partial` ("JC3 has the
instrument on the mech clip; the car's clip does not carry it") and the "never a heat bar" sentence
should be deleted, in the row and in `JC3_HUD_WEAPONS.md` §7 (where the same sentence first appears).
A1 also weakens the MODLOG's "heat = stated absence both sides".

---

## A2 — shape 8 and `reticle_size` cannot both be used

**The claims.** T-HUD14: "the heavy vehicle reticle is shape 8 (`E_RETICLE_CANNON`)", `map (shape id
UNKNOWN)`. T-HUD15: "accuracy frame -> `reticle_size`", `partial`, verify "the reticle tightens when the
Vulcan settles". Both rows point at the same `UpdateWeaponReticle` call.

**Why it matters.** If `reticle_size` does nothing for shape 8, the accuracy frame has no output at all
— not "a missing scale", but a missing effect — and T-HUD14's chosen shape forecloses T-HUD15's mapping.

**Test — read the switch body** (`hud.as:3866`, only the width computation shown):

```
> sed -n '3866,3956p' hud.as | grep -n "case|reticle_size|width|E_RETICLE"
33:    if(this.m_PrevSize != reticle_size || is_new_shape == true)
37:       case E_RETICLE_SINGLE_SHOT:
38:       case E_RETICLE_AUTO:
39:          new_width = RETICLE_CROSS_WIDTH_MIN + reticle_size * RETICLE_CROSS_WIDTH_MAX_LESS_MIN;
45:       case E_RETICLE_CIRCLE:
46:          new_width = RETICLE_CIRCLE_WIDTH_MIN + reticle_size * RETICLE_CIRCLE_WIDTH_MAX_LESS_MIN;
50:       case E_RETICLE_FLAK:
57:       case E_RETICLE_ROCKET:
62:       case E_RETICLE_DOT:
63:       case E_RETICLE_NONE:
64:       case E_RETICLE_WINGSUIT:
65:       case E_RETICLE_GRENADE_LAUNCHER:
66:       case E_RETICLE_CANNON:
67:       case E_RETICLE_WINGSUIT_WEAPONIZED:
68:       case E_RETICLE_MECH_CANNON:
69:       case E_RETICLE_MECH_MINIGUN:
70:       case E_RETICLE_POWERCORE:
```

`E_RETICLE_CANNON` is on line 66: one of the nine labels grouped under the fall-through with no
assignment to `new_width`. Only five shapes use `reticle_size` (single-shot/auto, circle, flak, rocket).
G2-25 §4 states the same thing in prose ("no size rig" for shape 8) and T-19's own block repeats it
in the reticle row's `limit`, so the file knows it — the two rows just do not meet.

**Also measured, and it helps T-HUD14:** the movie has a real cannon clip at index 8:

```
hud.as:3822  m_WeaponReticleMovieClips = new Array(… MCI_reticle_circle, MCI_reticle_dot,
  MCI_reticle_none, MCI_reticle_auto, MCI_reticle_wingsuit, MCI_reticle_rocket,
  MCI_reticle_grenade_launcher, MCI_reticle_cannon, MCI_reticle_flak, …)
```

so shape 8 is not only a name; a dedicated `MCI_reticle_cannon` clip exists and is switched to by index.
(That array's index 10 is `MCI_reticle_none` where the enum says `E_RETICLE_WINGSUIT_WEAPONIZED` — a
second artefact worth noting in G2-25, not T-19's problem.)

**Verdict: BROKEN** as a pair. Either the shape is 8 and `reticle_size` is inert (then T-HUD15 should be
`out`/UNKNOWN with that reason, and the verify sentence dropped), or the row wants a size-rigged shape —
and then the reticle row's "cannon" reading must change to a shape that both has a rig and is not the
cannon's own clip. The block cannot currently be built either way.

---

## A3 — "ids -1 and 0 rejected" attributed to `GetWeaponIconName`

**The claim.** T-HUD13: "`weapon_icons/<weapon_id>.ddsc` - `GetWeaponIconName(weapon_id)`, `_sm.ddsc` for
low res, **ids -1 and 0 rejected**".

**Test — the function:**

```
> sed -n "$(grep -n 'function GetWeaponIconName' hud.as | cut -d: -f1),+14p" hud.as
public function GetWeaponIconName(weapon_id:int, low_res_image:Boolean) : String
{
   weapon_icon_name = weapon_id.toString();
   if(low_res_image)
   {
      return "textures/ui/weapon_icons/" + weapon_icon_name + "_sm.ddsc";
   }
   return "textures/ui/weapon_icons/" + weapon_icon_name + ".ddsc";
}
```

No guard, no rejection. The caller `SetWeaponIcon` is invoked unconditionally at the end of
`InitVehicleWeapons`:

```
hud.as:5062   this.SetWeaponIcon(this.m_WeaponsArray[slot_index].MCI_selected_weapon_icon,weapon_id,this);
```

so a slot initialised with `weapon_id = -1` would request `weapon_icons/-1.ddsc`. The "-1 and 0
rejected" is `icons.rejected_ids` in G2-25's JSON, i.e. the *census* excluded them because no such
`.ddsc` ships. The sentence reads as movie behaviour and is not.

**Verdict: WEAK.** The row's actual conclusion ("ids 602/603/618/619 are shipped, so both slots draw")
is unaffected (see A4); only the parenthetical attributes a guard to code that has none. It matters
because an empty or unbound slot (`-1`) is a real case in this mod (T-WP13's blocked missile slot), and
the honest statement is: "an unbound slot must be hidden with `HideVehicleSlotAction`, or its icon load
names a file that does not exist".

---

## A4 — "ids 602, 603, 618, 619 all shipped"

**Test — the archive index:**

```
> grep -o "textures/ui/weapon_icons/[0-9a-z_]*\.ddsc" Research/JC3Grab/INDEX.jsonl | sort -u |
    grep -E "/(602|603|618|619)(_sm)?\.ddsc"
textures/ui/weapon_icons/602.ddsc
textures/ui/weapon_icons/603.ddsc
textures/ui/weapon_icons/618.ddsc
textures/ui/weapon_icons/619.ddsc
```

Four for four, hi-res; the `_sm` variants are not in the index for these ids, which the row never claims
(it only says `_sm.ddsc` exists as the low-res convention).

**Verdict: HOLDS.** The icon half of T-HUD13 is the strongest row in the block: the id is the filename
(`GetWeaponIconName` above), the names are on disk, and `SetWeaponIcon` is called by the movie itself.

---

## A5 — "the only monotone map" (T-HUD16, class `derived`)

**The claim.** Row: "cooldown = BmAK state / 4 (state 0…4 -> 0.00, 0.25, 0.50, 0.75, 1.00)", class
`derived`; `limit`: "the division by 4 is the only monotone map between the two domains, and its
direction is a Q check". MODLOG: "R4: `state / 4` is the only monotone map between 0…4 and 0..1".

**Test — the two domains are ordered sets of 5 and a closed interval.** Both `s/4` and `(4 − s)/4` are
monotone bijections {0,1,2,3,4} → {0,0.25,0.5,0.75,1}; they are inverses of each other. So "the only
monotone map" is false, and the choice between them **is** the direction question the same cell says is
open. What the movie fixes is only the shape of the value, verified in code:
`rot = weapon_cooldown * 360`, `MCI_mask_0_50.rotation = min(rot,180)`,
`MCI_mask_50_100.rotation = max(rot - 180, 0)`, and `weapon_cooldown != -1` as the visibility test.

**Verdict: WEAK.** The mapping is the sensible one and the doc flags the direction as a probe, so
nothing is hidden — but the uniqueness sentence is what upgrades the row from `class` to `derived` and
it is false. Say "one of the two monotone bijections; the direction is the probe" and the class stays
honest.

---

## A6 — `MCI_missile_locked` read as the *incoming* warning (R5)

**The claim.** T-HUD19: "`MCI_safe_area_bottom_middle.MCI_missile_locked` flashes every 0.5 s - that is
the *incoming* warning, a different instrument"; `out` reasons "the missile-box family … have no JC3
element". G2-25 §5 states it harder: "`MCI_missile_locked` is the 'a missile is locked on *you*'
warning".

**Test 1 — what the movie shows.**

```
hud.as:5200  public function ShowMissileLocked() : void { this.m_MissileLockedFlashing.start(); }
hud.as:5205  private function FlashMissileLocked(Timer:TimerEvent) : void { toggle alpha/visible every tick }
hud.as:5218  public function HideMissileLocked() : void { stop, alpha 0 }
```

Two API functions named `Show/HideMissileLocked`, a 0.5 s flash timer, and the clip in
`MCI_safe_area_bottom_middle` (its own safe area, not the weapon slots' bottom-right and not the
speedo's bottom-left). That is consistent with "you are being locked", and it is also consistent with
"your missile has lock" — the name contains the state, not the subject. The position is the only
structural signal, and it is a layout convention, not a decoded field.

**Test 2 — is there a caller that would settle it?**

```
JC3_HUD_WEAPONS.json → lockon.show_missile_locked_calls = {"count": 0, "sites": []}
                       lockon.hide_missile_locked_calls = {"count": 0, "sites": []}
```

Nobody in the movie calls it, so the trigger is native and unknown. G2-25's own §5 table records the
same "0 / 0 call sites".

**Test 3 — does the row survive without the reading?** Its `out` also rests on "6 `VehicleMissileTarget`
kinds … have no JC3 element", which is structural and true (A8). So the disposition does not depend on
the "incoming" word; only the sentence does.

**Verdict: WEAK.** The dismissal is a name-and-position reading, exactly the class R5 warns about, and
it is written as a fact ("that is the incoming warning"). It should read: "`MCI_missile_locked` is a
second, separate lock instrument in its own safe area; its trigger is native (0 callers), so whether it
is the incoming warning or the player's own lock state is UNKNOWN — either way it is not the 6-kind
target-box family, which has no JC3 member".

---

## A7 — slot index 0/1 ↔ `main_weapon` / `id:00568A74`

**The claim.** T-HUD11: "slot 0 = the cannon clone … (`main_weapon`, T-11); slot 1 = the Vulcan clone …
(root `id:00568A74`, T-11)".

**Test 1 — the count and the widgets are decoded.**

```
hud.as:3821  this.m_WeaponsArray = new Array(this.MCI_safe_area_bottom_right.MCI_vehicle_weapons0,
                                             this.MCI_safe_area_bottom_right.MCI_vehicle_weapons1);
```

A hard-sized 2-element array (`slots.count = 2`, `clips = [MCI_vehicle_weapons0, MCI_vehicle_weapons1]`).
The "2 slots" half of the row is read, not inferred.

**Test 2 — the entity side is two pointers, in an order, with no enum value stored.**

```
Research/JC3Grab/WEAPON_WIRING.md:31
The root class carries two separate object pointers, not a list with an order. `id:851CAABE` is the
first (`main_weapon`), `id:00568A74` the second. … there is no active-slot index, no next/previous
weapon action and no weapon group anywhere in the `.epe`.
Research/JC3Grab/WEAPON_WIRING.md:305
slots on `CCar` `v0201_car_capstone_mediumtank_generated`: main_weapon `w602_mediumtank_canon` ·
secondary (id:00568A74) `w603_mediumtank_mgun` · …
```

So the donor tank itself carries cannon→`main_weapon`, machine gun→`00568A74`, and the research file
labels the second pointer "secondary". What no file stores is the **number** the HUD receives for each
pointer: `EVEHICLE_WEAPON_SLOT_MAIN = 0` / `_ALTERNATIVE = 1` is a C++ enum, and the entity carries
object pointers, not indices. The row's "slot 0/1" is the ordering of those two pointers.

**Verdict: WEAK.** The structural inference is strong (the tank's own "main" pointer is first, and the
second pointer is the one the research calls secondary), and the mod clones that exact tank. But it is an
inference, and it is the only place in the block where a slot *number* is asserted; the row should say
"first pointer → slot 0, second → slot 1 (ordering inference; a Q-3 probe with the two clips settles it)".

---

## A8 — the 6 target kinds have no JC3 family

**Test.** `poi_types` in G2-25's JSON lists 32 constants; the full set is
`POI_TYPE_LABEL 0 … POI_TYPE_ROM_START_ATTACKWAVE 31`, including `POI_TYPE_GRENADE 18`,
`POI_TYPE_LOCKED 24`, `POI_TYPE_WEAPON_PICKUP 22`. There is no type for a bomb, an EMP, a friendly
target or a multi-target box, and `poi.as` has exactly one lock-on case (21). On the BmAK side the six
kinds are `Invalid, bomb, emp, friend, multi, plain` plus `Tank_Hack_BOMB/EMP/FRIEND` (`HUD.md:218`,
`HUD.md:250`).

**Verdict: HOLDS.** Four of the six kinds have no carrier by any name, and the family is a distinct
widget set (`missile_lockon_square_anim`, `missile_border_anim`), not a variant of the one POI.

---

## A9 — the two "0 of N setters" scans

**Test 1 — counts and heat.**

```
modules 19 total setters 252
Batmobile setters 37
heat in any setter name: []
```

`HUD_INTERFACES.json` sums to 252 across 19 modules, `HudModuleBatmobile` has 37, and no setter name
contains "heat". **HOLDS** for A9-heat, and it is the one place the row's BmAK side is derived rather
than quoted.

**Test 2 — the ammo claim.** T-HUD20 says "0 of the 37 setter names carry ammo/magazine". A naive scan
does not give 0:

```
ammo/mag in batmobile setters: ['UC_SetImpactDamageFlash']
```

`"mag"` is a substring of `"damage"`. The semantic claim (no setter takes ammo or a magazine) is true —
none of the 37 signatures declares such an argument — but the sentence presents a name scan that, run
literally, returns 1, and no proof re-evaluates it.

**Verdict: HOLDS (heat) / WEAK (ammo).** Two typed prose counts inside a block whose whole selling point
is "every cell is re-derived by `--check`". Either add a proof (`setters_named("ammo") == []`) or drop
the number.

---

## A10 — `infiniteAmmo = true` hides the counters

**Test — the branch, read in full:**

```
hud.as:5043  if(this.m_WeaponsDataArray[slot_index].m_HasInfiniteAmmo == false)
             { … TXT_selected_inventory_ammo.visible = true; TXT_bullet_ammo.text = …;
               TXT_slash_mark.visible = true; MCI_inventory_infinity.visible = false; … }
             else
             { … TXT_selected_inventory_ammo.visible = false; TXT_bullet_ammo.visible = false;
               TXT_slash_mark.visible = false; MCI_inventory_infinity.visible = true;
               MCI_bullet_bar.MCI_bullet_bar_anim.gotoAndStop("full"); }

hud.as:5030  … infiniteAmmo:Boolean = true …
```

The behaviour is verified, not inferred from the name (R5 satisfied), and `true` is the parameter's own
default, so the value is `decoded` at least as much as `derived`.

**Verdict: HOLDS.** One nit: the class should probably be `decoded (default)`, and the reason the value
is chosen (BmAK has no ammo setter) belongs in `limit`, which it does.

---

## A11 — the rows describe values for a caller no file contains

**Test — the call sites (G2-25 §8, re-read from the JSON):**

```
callers.init   = 2 sites, both in TestConstructor
                 hud.as:7535  this.InitVehicleWeapons(0,141,"Panther",true,5,15,60);
                 hud.as:7536  this.InitVehicleWeapons(1,141,"Minigun",true,2,20,100);
callers.update = 0 sites
callers.reticle= 0 sites
```

Every parameter in the 10 rows (slot index, weapon id, name, infinite ammo, cooldown, reticle shape and
size) is a value the *native* HUD interface must pass; the movie's only calls are a test constructor
using the Panther's id 141 for both slots.

**Why it is on this list.** It is the assumption that turns 6 `map` rows into build values. The doc does
state it — "what is missing is the bridge from the entity to `hud.gfx`, which is game code, not a
`.vmodc` member" — and each row's verify is a Q-3 probe. That is the correct handling.

**Verdict: HOLDS as stated.** But it means no `map` in this block has a measurable effect before Q-3,
and the rows that assert *values* (name pass-through, `infiniteAmmo`, cooldown fraction) are proposals
to a caller, not mappings of a member. The block's own "Where the boundary is" paragraph should say
that once, plainly, instead of leaving it in §"The one HUD finding" below it.

---

## A12 — BmAK's heat bar: "a script field with no setter"

**Test — the BmAK side is real geometry and a dead rate:**

```
Research/BatmobileGrab/WEAPONS.md:683  | RBatmobileCannon.HeatUpPerSecond  | 0x0A78 | FloatProperty  | 0.0 |
Research/BatmobileGrab/WEAPONS.md:684  | RBatmobileCannon.OverheatOffValue | 0x0A80 | FloatProperty  | 0.25 |
Research/BatmobileGrab/WEAPONS.md:685  | HeatBarStart                      | 0x0A88 | StructProperty | [0.79, 0.68] |
Research/BatmobileGrab/WEAPONS.md:686  | HeatBarSize                       | 0x0A90 | StructProperty | [0.125, 0.03] |
```

and the object is `RBatmobileCannon` / `Batmobile_Cannon_V2` (4 packages,
`objects.jsonl:5202/5706/14143`).

So: the two fields are a **screen-space rect** (position 0.79/0.68, size 0.125/0.03) — i.e. the game
draws this bar natively from weapon-struct data — and the field that would fill it,
`HeatUpPerSecond`, is **0.0** in the recorded dump, i.e. the bar never rises. `OverheatOffValue` 0.25 is
the only non-zero rate-like value.

**Verdict: WEAK.** The row's BmAK sentence is true (0 of 252 setters, so it is not an interface) but it
describes the element as a bare "script field" when the fields are the bar's own geometry, and it omits
the fact that decides whether the element has any behaviour at all: heat never accumulates. With
`HeatUpPerSecond` 0.0 in the donor, "omit it" is not a loss — and that is a much stronger reason for
`out` than "JC3 has nothing", which A1 shows is not true either. (Caveat: the value was read from a
single object dump; a four-package check should confirm it before it is quoted as a fleet fact.)

---

## A13 — "the movie's own heat code is the 11-state police wanted level"

**Test — the constants:**

```
hud_code/heat/heat.as:9   private static const HEAT_STATE_OFF:int = 0;
                          … ON 1, REINFORCEMENT 2, SEARCHING 3, MILITARY 4, SPIKE_EVENT 5,
                          RESTRICTED 6, ESCAPED 7, REINFORCEMENT_FAILED 8,
                          REINFORCEMENT_SUCCEED 9, CAN_APPLY_HEAT_POINTS 10
```

Eleven constants, `police_heat_states: 11`, `police_heat_dir: "hud_code/heat/"`, and the `heat` hits in
`hud.as` are `POI_TYPE_HEAT_RADIO` (11) and the heat-radio icon animation. The police wanted level and
the weapon temperature are unrelated systems that share an English word.

**Verdict: HOLDS.** This is the right way to dispose of a name collision, and it is the one place in the
block where a plausible carrier is explicitly *not* mistaken for one.

---

## A14 — the five elements

**Test.** `t19_hud.py:54  ELEMENTS = ["weapon slots", "reticle", "cannon cooldown", "Vulcan heat",
"missile lock"]`, and the check asserts one row per element (`5/5`) and that a missing element fails.
The five names are the card's WPN-12 cell (`JC3_HUD_WEAPONS.json` → `rows.wpn12`: "HUD: weapon slots,
reticle, cannon cooldown, Vulcan heat, missile lock").

**Verdict: HOLDS**, with one R11 nit: the element list is typed into the script instead of parsed from
the `wpn12` cell, so a change in the card's cell would not reach the check. Small, but it is the same
class of defect as A9's typed scans.

---

## What this challenge did not test

* **Whether the native caller passes the two weapon ids.** Needs Q-3 #3 (and a launch, which this task
  forbids). A11 states the gap; no file can close it.
* **Which reticle shape JC3 uses for a vehicle cannon in the shipped game.** `MCI_reticle_cannon`
  exists and shape 8 selects it, but who passes 8 is native. T-HUD14 already says `UNKNOWN`.
* **Whether the mech thermometer can be driven from a car.** The clip is in the same movie and takes the
  same `weapon_cooldown`, but the car's slot clip does not contain the widget; using it would mean
  repointing the movie, which is a build question, not a translation one.
* **`HeatUpPerSecond` across all four packages** (A12) — read from one object dump only.

"""t17_fx.py - effects translation (T-17).

The Batmobile's 206 BmAK particle systems (G1-16) grouped into 21 features, translated onto
JC3's existing effects. The Batmobile *is* `v0300_car_kensington_sportsmuscle` (the donor the
build replaces), so the strongest evidence for a choice is that the donor's own `.ee` already
carries the effect - `FX_TABLE.jsonl` lists every `.effc` and the container that embeds it
(G2-9), so "the donor spawns it" and "N vehicles spawn it" are counts, not opinions.

For every FX-relevant feature the tool derives the choice from the table:

  kind     a needle list must appear in the effect path (`exhaust/car_cycle_base_dual_nitrous`,
           `muzzle_flash/tank_canon`, `wheels/trail/dust_trail_`, ...)
  donor    a candidate carried by the donor chassis sorts first (the graph the build already has)
  fleet    then the candidate the most vehicles carry
  size     the effect's row/array/byte counts and the BmAK group's systems/emitters/lifetime are
           reported side by side; there is **no unit bridge** between them, so size is recorded
           and reviewed, not used as a rank key (stated in the file)

A keyword search over the 955 effect paths proves nothing on its own: a `.effc` carries no
strings (`FX9_HAZE` §2), so only a *filename* can match. Five rows were filed `out` on that test
(T-FX9, T-FX12, T-FX13, T-FX16, T-FX20); the five reports named below replaced the test with a
shipped carrier or an authoring plan, and each row now states which, with the members a private
copy changes (`T13_FX.md` §5). `absence` is still supported by the tool for any future row: the
needles are searched over all 955 paths (or the vehicle-carried subset) and the row fails if a
match appears.

`--write` writes `Working/Translation/T13_FX.md` + `t17_fx.json`; `--check` re-reads every input,
re-derives both files, compares them, and cross-checks the ids against `T_ROWS.jsonl` (the ledger
`t_rows.py build` makes from this document).

Usage:
  python Tools/scripts/t17_fx.py --write
  python Tools/scripts/t17_fx.py --check
  python Tools/scripts/t17_fx.py show T-FX10
"""
from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "Working", "Translation")
JC3 = os.path.join(ROOT, "Research", "JC3Grab")
BAT = os.path.join(ROOT, "Research", "BatmobileGrab")
FX_TABLE = os.path.join(JC3, "FX_TABLE.jsonl")
PARTICLES = os.path.join(BAT, "PARTICLES_FEATURES.json")
USAGES = os.path.join(JC3, "USAGES.json")
WEAPONS = os.path.join(JC3, "WEAPONS.jsonl")
SOCKETS = os.path.join(BAT, "SOCKETS_JC3.json")
LEDGER = os.path.join(WORK, "T_ROWS.jsonl")
OUT_MD = os.path.join(WORK, "T13_FX.md")
OUT_JSON = os.path.join(WORK, "t17_fx.json")

# the donor the Batmobile replaces (D-4 keeps v0300; the signature variant is the armed one)
DONOR = ("editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/"
         "v0300_car_kensington_sportsmuscle_signature_preorder.ee")

# ---------------------------------------------------------------------------- rules
# Every FX code of §1 gets rows; each row is one effect feature.
#   match/exclude  : needle lists into the .effc path
#   donor          : True = prefer an effect the donor chassis already carries
#   absence        : "no_paths" | "no_vehicle_paths" - a proved negative instead of a choice
#   attach         : ("socket", name) | ("part", name) | ("impact", "") | ("none", "")
#   trigger        : USAGES.json usage name, or a free-form mechanism with its evidence
RULES: list[dict] = [
    # --- FX-1 afterburner flame + heat haze --------------------------------------------
    dict(id="T-FX7", code="FX-1", feature="afterburner flame",
         groups=["afterburner-exhaust"], match=["exhaust/car_cycle_base_dual_nitrous"],
         exclude=[], donor=True, attach=("socket", "Afterburner"), trigger="EngineNitro",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: the donor graph already drives the nitrous exhaust under `EngineNitro`",
         confidence="decoded", verify="Q-1 #5 / Q-2 A9: flame at the tail on boost",
         dispo="epe",
         why="afterburner flame = the exhaust nitrous effect the donor already carries under EngineNitro"
             " (G2-22/G2-23); attachment is the Afterburner socket"),
    dict(id="T-FX8", code="FX-1", feature="base exhaust",
         groups=["afterburner-exhaust"], match=["exhaust/car_cycle_base_dual"],
         exclude=["nitrous", "tjump"], donor=True, attach=("socket", "SideExhaustL"),
         trigger="EngineRunning",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: `EngineRunning` already drives the dual exhaust on the donor",
         confidence="decoded", verify="Q-1 #8: idle exhaust visible",
         dispo="epe",
         why="the always-on exhaust is the donor's `car_cycle_base_dual` effect under the"
             " `EngineRunning` usage (G2-22); the twin side-exhaust sockets carry it"),
    dict(id="T-FX9", code="FX-1", feature="heat haze (distortion at the exhaust)",
         groups=["afterburner-exhaust"], names_filter=["batmobileExhaust_burst"],
         exact=["effects/jc_vehicles/exhaust/car_speedrom_heater.effc"], exclude=[], donor=False,
         attach=("socket", "Afterburner"), trigger="EngineNitro",
         now="carrier found: the fleet's only heat-named effect (12 vehicles; 24 `z80_exhaust_heat_l/r`"
             " attach objects; both JC3 distortion textures ship in its bundle)",
         propose="attach the shipped effect at `Afterburner` (no byte change); a private copy only to"
                 " tune the 4 sprite `RenderBlockData[0]` constants and `MaxParticles` toward BmAK's"
                 " `Engine.Fire_Distortion` emitter - one slot at a time",
         confidence="decoded",
         verify="Q-2 A9: shimmer above the exhaust on boost; one `RenderBlockData` slot changed per probe",
         dispo="next",
         why="heat haze carrier = `car_speedrom_heater.effc` (12 vehicles, 24 `z80_exhaust_heat_l/r`"
             " attachments, distortion textures in the same bundle; `fx9-heat-haze-source.md` §8);"
             " gap = no member names a blend mode or the per-emitter texture (`effc-format-writable.md` §4)",
         authoring=dict(
             copy="`effects/jc_vehicles/exhaust/car_speedrom_heater.effc` - 14,703 B, 5 emitters / 5"
                  " templates (4 sprite + 1 mesh), MaxParticles 10/60/3/7/100, blocks"
                  " `3012430835`×8 + `2199516487`×2; attach first, copy only to tune",
             members=[
                 "`Instantiators[i].RenderBlockData[0]` of the 4 sprite instantiators"
                 " (3125323646, 436538540, 869501834, 124404425) - the per-emitter texture/material"
                 " constant; which slot is which is UNKNOWN, so one slot per probe",
                 "`Instantiators[i].RenderBlockData[]` floats (0.5 / 5.0 / 8.0 / 10.0 / 20.0 ship here)"
                 " - the strength/scale constants",
                 "`EmitterTemplates[i].MaxParticles` 10/60/3/7/100 - the live caps, patched at their"
                 " decoded offsets (the writer's proven field, `EmitterTemplates[0].MaxParticles`)",
             ],
             grows="none - every patch keeps the array lengths, so `A[..]` pairs, data offsets"
                   " and `total_size` stay valid (the writer's proven path)",
             gap="no `.effc` field names a blend mode or the texture an instantiator binds (0 string"
                 " values in 955 files; 8 `RenderBlockTypeHash` values game-wide, the single-use"
                 " `2813794826` the only unnamed lead), so 'does this sprite refract' is UNKNOWN",
             evidence="`tmp/freebuff/reports/fx9-heat-haze-source.md` §4/§5/§8;"
                      " `Research/JC3Grab/FX9_HAZE.json`; `tmp/freebuff/reports/effc-format-writable.md` §4"),
         ),
    # --- FX-2 weapon effects -------------------------------------------------------------
    dict(id="T-FX10", code="FX-2", feature="cannon muzzle flash",
         groups=["muzzle-flash"], match=["muzzle_flash/tank_canon"], exclude=[],
         names_filter=["canon", "cannon", "heavy"],
         donor=False, attach=("socket", "CannonMuzzle"), trigger="weapon fire (weapon component)",
         now="absent: the Batmobile carries no weapon until the T-11 clone",
         propose="use at CannonMuzzle when the cannon is cloned; the effect rides the weapon bundle",
         confidence="decoded", verify="Q-1 #5: flash at the muzzle, not the car origin",
         dispo="next",
         why="cannon muzzle flash = the fleet's tank-canon flash (`tank_canon_muzzleflash`), fired"
             " from the CannonMuzzle socket; needs the T-11 weapon clone"),
    dict(id="T-FX11", code="FX-2", feature="Vulcan muzzle flash",
         groups=["muzzle-flash"], match=["muzzle_flash/helicopter_minigun"], exclude=[],
         names_filter=["muzzle"],
         donor=False, attach=("socket", "ChainGunMuzzle"), trigger="weapon fire (weapon component)",
         now="absent: the Batmobile carries no weapon until the T-11 clone",
         propose="use at ChainGunMuzzle when the Vulcan is cloned",
         confidence="decoded", verify="Q-1 #5: flash at the muzzle",
         dispo="next",
         why="Vulcan/chain-gun muzzle flash = `helicopter_minigun_muzzleflash`, the only vehicle"
             " minigun flash in the fleet; fired from ChainGunMuzzle"),
    dict(id="T-FX12", code="FX-2", feature="tracers (tune + art half)",
         groups=["tracer"],
         exact=["effects/jc_weapons/missile/missile_trail_car.effc"], exclude=[], donor=True,
         attach=("none", ""), trigger="WeaponTuning tracer members",
         now="linear half is the cloned `.wtunec` (8 members); the art half has no shipped"
             " bullet-bound carrier",
         propose="carry the linear half in the private `w602`/`w603` tunes (width 0.5 already,"
                 " TTL 0.0 -> 1.25 s, smoke ribbon on) and author the art half as a private copy of"
                 " `missile_trail_car.effc` with two emitters",
         confidence="decoded",
         verify="Q-1 #5: 0.50 m streak at 1.25 s, plus the two-emitter trail behind the round",
         dispo="next",
         why="tracer = 8 `bullet_base_tuning` members (`tracer_fire_width` 0.5 @0x188 is already the"
             " 50 uu ribbon; TTL 0.0 @0x190 -> 1.25); the art half (2 emitters, colours, offsets) has"
             " no tune member and no bullet-bound effect - authored on `missile_trail_car.effc`"
             " (`fx12-16-tracer-and-trail.md` §8/§9/§10)",
         authoring=dict(
             copy="`effects/jc_weapons/missile/missile_trail_car.effc` - 11,199 B, 1,412 rows, 179"
                  " arrays, 36 types; ships inside `w618_sportsmuscle_missile.ee` (one private copy"
                  " serves T-FX12 and T-FX16)",
             members=[
                 "the tune, in place: `tracer_fire_width` 0.5 @0x188 (already the 50 uu ribbon),"
                 " `tracer_time_to_live` 0.0 @0x190 -> 1.25 s, `tracer_fire_length` 30 @0x184,"
                 " `tracer_fire_velocity` 900 @0x180, `smoke_trail_tile_size` 5.0 @0x198,"
                 " `tracer_per_smoke_trail` 1 @0x19C, `tracer_texture_type` 1 @0x1A0 (enum only)",
                 "the effect, growth: `Emitters[]`/`EmitterTemplates[]`/`Instantiators[]` +1 ribbon"
                 " (0.50 m width, 1.25 s life, 8 per s) and +1 sprite (0.035-0.05 s, 1 per s,"
                 " -0.50 m offset) with their render blocks and `TrimIndex`",
             ],
             grows="yes, for the art half: two emitters need the `A[..]` (offset, count) pairs and"
                   " `total_size` re-laid out - the one step the format report did not build or"
                   " re-read (its UNKNOWN 4), so it is card B-17's last step",
             gap="JC3 binds no effect to a bullet in flight: 0 of the 97 `WeaponTuning` members is an"
                 " effect/trail member, and `RBasicProjectile.ProjectileTrail` (BmAK's binding) has no"
                 " JC3 counterpart",
             evidence="`tmp/freebuff/reports/fx12-16-tracer-and-trail.md` §3/§4/§7/§8/§9/§10;"
                      " `tmp/freebuff/reports/effc-format-writable.md` §4"),
         ),
    dict(id="T-FX13", code="FX-2", feature="shell casings",
         groups=["casings"],
         exact=["effects/jc_weapons/minigun/bullet_eject_minigun.effc"], exclude=[], donor=False,
         attach=("socket", "ChainGunShells"), trigger="`ShellEjection` usage 4131019937 (`Fire`)",
         now="carrier found: `SAttachedEffect ShellEjection` under the mounted-MG entity, Effect"
             " 600259254, Usage 4131019937, `name_hash` 3811014039, no `world` (14 graphs / 5 dirs)",
         propose="copy the shipped pair onto the chain-gun clone: the `ShellEjection` object under the"
                 " weapon entity's `SEffects` plus `bullet_eject_minigun.effc` in its `.ee`; tune only"
                 " `MaxParticles` / `Params[12]` gravity if the cap needs it",
         confidence="decoded",
         verify="Q-3 #4: casings leave the right side of the gun at the first burst and fall at 9.82",
         dispo="next",
         why="casing carrier = `SAttachedEffect ShellEjection` (Effect 600259254 ="
             " `hash_jenkins(effects/jc_weapons/minigun/bullet_eject_minigun.effc)`, Usage"
             " 4131019937 = `Fire`, no `world`) in the mounted-MG entity + the `.effc` in the weapon"
             " `.ee`; 0 of the 226 weapon tunes has an effect member (`fx13-shell-casings.md` §3/§4/§7)",
         authoring=dict(
             copy="`effects/jc_weapons/minigun/bullet_eject_minigun.effc` - 6,703 B, 177 rows, 21"
                  " arrays, MaxParticles 30, gravity `Params[12]` -9.82, cone `Params[9]/[10]`"
                  " 0.1745329 / 0.0872665 rad; the attachment object is copied from `w206`/`w201`"
                  " (`SAttachedEffect ShellEjection`)",
             members=[
                 "`.effc`, in place: `EmitterTemplates[i].MaxParticles` 30 (the live cap; the"
                 " capstone variant ships 15 + 30) and `Params[12]` -9.82 if the fall needs"
                 " changing - `Params[]` floats are writable at their decoded offsets",
                 "`.epe`, one added object: `SAttachedEffect` name `ShellEjection`, `name_hash`"
                 " 3811014039, `Effect` = `hash_jenkins(<private .effc path>)`, `Usage`"
                 " 4131019937, no `world` (the weapon's own frame carries it), parent = the"
                 " chain-gun weapon entity's `SEffects`",
             ],
             grows="no `.effc` growth (patch in place); the graph gains one attachment object",
             gap="no spawn-rate member in the effect: BmAK's 4 per s for 1.0 s is code-side, so the"
                 " build emits per `Fire` shot or gates the emitter, and the cone's local axis is not"
                 " decoded (the attachment has no `world`)",
             evidence="`tmp/freebuff/reports/fx13-shell-casings.md` §3/§4/§7;"
                      " `tmp/freebuff/reports/effc-format-writable.md` §4"),
         ),
    dict(id="T-FX14", code="FX-2", feature="missile launch trail",
         groups=["missile"], match=["missile/missile_trail_car"], exclude=[],
         names_filter=["missile"],
         donor=True, attach=("socket", "MissileL"), trigger="missile weapon (w618 family)",
         now="absent: the missile slot is T-11/D-7",
         propose="use on the missile weapon; the trail follows the round from MissileL/MissileR",
         confidence="decoded", verify="Q-1 #5: trail behind the missile",
         dispo="next",
         why="missile trail = `missile_trail_car`, the only car-body missile trail in the fleet"
             " and already on the donor; needs the T-11 missile clone (D-7 slot)"),
    dict(id="T-FX15", code="FX-2", feature="cannon impacts",
         groups=["cannon-impact"], match=["tank_explosive/"], exclude=[], donor=True,
         attach=("impact", ""), trigger="bullet impact / blast (`w602` ForcePulse)",
         now="absent: the Batmobile carries no cannon until T-11",
         propose="use the `tank_explosive_*` family: one effect per surface (7 variants)",
         confidence="decoded", verify="Q-1 #5: impact effect on the hit surface",
         dispo="next",
         why="cannon impact = the tank-canon `tank_explosive_*` family (7 surface variants) the"
             " donor and the medium tank both carry; needs the T-11 cannon"),
    dict(id="T-FX16", code="FX-2", feature="cannon round trail",
         groups=["projectile-trail"],
         exact=["effects/jc_weapons/missile/missile_trail_car.effc"], exclude=[], donor=True,
         attach=("none", ""), trigger="the cannon round (T-FX12's private copy)",
         now="no bullet-bound carrier; the round trail is the same private copy as T-FX12, using its"
             " sprite emitter",
         propose="author the round trail with T-FX12: one private copy, the sprite emitter"
                 " (0.035-0.05 s, 1 per s, -0.50 m) gives the round its trail and the ribbon gives the"
                 " streak; the earlier `0 of 955` claim named no search term",
         confidence="decoded",
         verify="Q-1 #5: trail behind the cannon round; sprite lifetime distinguishable from the ribbon",
         dispo="next",
         why="`Batmobile_CanonTrail` is a 2-emitter `ParticleSystem` bound to"
             " `RBasicProjectile.ProjectileTrail` with no JC3 effect member; the closest carrier is the"
             " same `.effc` route as T-FX12 (`fx12-16-tracer-and-trail.md` §7/§8/§10), and the old"
             " absence claim was UNKNOWN, not a proved negative (`FX16_TERM.md`)",
         authoring=dict(
             copy="`effects/jc_weapons/missile/missile_trail_car.effc` - the same private copy as"
                  " T-FX12, so one authored effect serves both rows",
             members=[
                 "sprite emitter (the round trail): lifetime 0.035-0.05 s, spawn 1 per s,"
                 " `StartLocation` -0.50 m behind the round, `StartSize` from the 50 uu ribbon width",
                 "ribbon emitter (the streak, shared with T-FX12): 0.50 m, 1.25 s, 8 per s",
                 "the round's own tune, in place: `w602_batmobile_cannon.wtunec`"
                 " `tracer_time_to_live` 0.0 -> 1.25 s so the streak outlives the shot",
             ],
             grows="yes: the emitters are added to the copy (same `A[..]` re-layout as T-FX12)",
             gap="no decoded JC3 carrier attaches a particle system to a bullet in flight; the"
                 " `ProjectileTrail` binding is BmAK-side only",
             evidence="`tmp/freebuff/reports/fx12-16-tracer-and-trail.md` §7/§8/§10;"
                      " `Working/Translation/FX16_TERM.md`; `tmp/freebuff/reports/effc-format-writable.md` §4"),
         ),
    # --- FX-3 tyres, scrape, brake lights -------------------------------------------------
    dict(id="T-FX17", code="FX-3", feature="tyre smoke / kick-up",
         groups=["tyre-surface"], match=["wheels/trail/dust_trail_"], exclude=[],
         names_filter=["burnout", "wheels"], donor=True,
         attach=("part", "wheel_f_l"), trigger="tire_effects (T-EF1)",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: the donor's wheel trail family, one per surface (6 variants)",
         confidence="decoded", verify="Q-2 A10: dust at the wheels when sliding",
         dispo="epe",
         why="tyre kick-up = the donor's `wheel*/dust_trail_*` family (6 surfaces, 161 vehicles"
             " each) driven by `tire_effects` (T-EF1); attachment is the four wheel parts"),
    dict(id="T-FX18", code="FX-3", feature="slide dust",
         groups=["tyre-surface"], match=["collision/chassis_slide_"], exclude=[], donor=True,
         attach=("part", "body"), trigger="tire_effects (T-EF1)",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: the chassis slide family (5 surfaces)",
         confidence="decoded", verify="Q-2 A10: dust under the chassis in a slide",
         dispo="epe",
         why="chassis slide dust = `chassis_slide_*` (5 surfaces, 290 vehicles) already on the"
             " donor; the body part carries it"),
    dict(id="T-FX19", code="FX-3", feature="wall-scrape sparks",
         groups=["wall-scrape"], match=["trails/spark_trail_"], exclude=[], donor=True,
         attach=("socket", "ScrapeSparksL"), trigger="none in BmAK (0 systems)",
         now="socket present, no BmAK system drives it",
         propose="use the nearest fleet effect (`spark_trail_02_med`) on the scrape sockets",
         confidence="derived", verify="Q-3 #1: sparks on contact with a wall",
         dispo="epe",
         why="BmAK's wall-scrape group is 0 systems (G1-16) so there is nothing to copy; the"
             " donor already carries `spark_trail_02_med` and the ScrapeSparks sockets exist"),
    dict(id="T-FX20", code="FX-3", feature="brake-light trails",
         groups=[],
         exact=["effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc"], exclude=[],
         donor=True, attach=("socket", "BrakeTrailL"),
         trigger="authored: no JC3 brake state exists (9 behaviours, no `Brake`)",
         now="no brake-named effect and no brake trigger; BmAK `BrakeTrail0/1` serialise no system",
         propose="author a private copy of the donor's boost-glow effect restyled on the"
                 " `t_velocity_streak_alpha_dif` strip at `BrakeTrailL/R`, and author the brake trigger",
         confidence="derived",
         verify="Q-2 A5: a streak appears at the tail lamps under braking and nowhere else",
         dispo="next",
         why="streak carrier = an `.effc` built on `car_cycle_base_dual_nitrous.effc` (donor-carried,"
             " 20,671 B in its `.ee`) with `t_velocity_streak_alpha_dif.dds.1_1b.trim` (657 B, in the"
             " donor `.ee`); the gap is the trigger - no light member names a trail (25 members), no"
             " `Brake` behaviour (9 states), and BmAK's `BrakeTrail0/1` components carry no template"
             " (`fx20-brake-trail.md` §3/§4/§6/§8)",
         authoring=dict(
             copy="`effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` - the donor's"
                  " boost glow (3,161 rows, 337 arrays, 20,671 B in the donor `.ee`), restyled on"
                  " `effects/textures/t_velocity_streak_alpha_dif.dds.1_1b.trim` (657 B, 28 rows, 3"
                  " arrays; 377 containers carry it)",
             members=[
                 "`Instantiators[i].RenderBlockData[]` floats - the streak's scroll/scale constants"
                 " (slot semantics UNKNOWN: patch one slot per probe)",
                 "`EmitterTemplates[i].MaxParticles` and `StartTime` / `EmitterLifetimeIndex` - how"
                 " much streak exists and when it starts",
                 "the trim binding is not a member: `Instantiators[i].TrimIndex` is the corpus-wide"
                 " constant 14, so which `.trim` an instantiator draws is UNKNOWN",
             ],
             grows="in place for the restyle; the trigger is new build work (a brake-state carrier"
                   " does not exist, so the build authors it)",
             gap="no light member names a trail/streak/ribbon (25 members), the behaviour"
                 " vocabulary has no `Brake` (9 states), and BmAK `BrakeTrail0/1` serialise no"
                 " `ParticleSystem` template, so its width/length/colour are UNKNOWN",
             evidence="`tmp/freebuff/reports/fx20-brake-trail.md` §3/§4/§6/§8;"
                      " `Research/JC3Grab/LIGHT_SYSTEM.md` §1; `tmp/freebuff/reports/effc-format-writable.md` §4"),
         ),
    # --- FX-4 death and burn --------------------------------------------------------------
    dict(id="T-FX21", code="FX-4", feature="death explosion",
         groups=["explosion"], match=["damage/exp_car"], exclude=[], donor=True,
         attach=("part", "body"), trigger="OnExploded",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: the car explosion effect the donor already spawns, plus the blast tune"
                 " (`car_explosion_medium`, G2-10 §8)",
         confidence="decoded", verify="Q-3 #7: explosion on death",
         dispo="epe",
         why="death explosion = the donor's `exp_car_01` effect under the `OnExploded` usage"
             " (G2-22); the blast numbers stay in the WeaponTuning/ForcePulse tune (G2-10)"),
    dict(id="T-FX22", code="FX-4", feature="burn states (engine / base / roof)",
         groups=["vehicle-fire"], match=[], exact=["effects/jc_vehicles/damage/dmg_fire_engine.effc",
                                                "effects/jc_vehicles/damage/dmg_fire_spread_base.effc",
                                                "effects/jc_vehicles/damage/dmg_fire_spread_roof.effc"],
         exclude=[], donor=True,
         attach=("part", "body"), trigger="OnPartReachedDamageState",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: the 3-variant burn family (engine / spread base / spread roof)",
         confidence="decoded", verify="Q-3 #7: fire on the engine, then the roof",
         dispo="epe",
         why="burn states = the donor's `dmg_fire_engine` / `dmg_fire_spread_base` /"
             " `dmg_fire_spread_roof` family under the damage-state usage (G2-22)"),
    dict(id="T-FX23", code="FX-4", feature="post-burn / engine smoke",
         groups=["vehicle-fire"], match=[], exact=["effects/jc_vehicles/damage/dmg_smoke_engine.effc",
                                                "effects/jc_vehicles/damage/dmg_post_burn.effc"],
         exclude=[], donor=True,
         attach=("part", "body"), trigger="EngineSmoking",
         now="carried: the donor .ee lists the effect (FX_TABLE container set)",
         propose="keep: engine smoke, then `dmg_post_burn` when the fire is out",
         confidence="decoded", verify="Q-3 #7: smoke after the fire",
         dispo="epe",
         why="engine smoke = the donor's `dmg_smoke_engine` under the `EngineSmoking` usage"
             " (23 vehicles, G2-22); `dmg_post_burn` is the after-fire state"),
]

# Feature groups of §1 this card does not own (the doc's coverage table; no ledger rows).
OTHER_GROUPS = {
    "winch": "WPN-6 - named omission, no winch/rope module type in the fleet (G2X)",
    "sonar": "WPN-7 - named omission, no sonar class in the fleet (G2X)",
    "emp": "WPN-5 - T-11 (CForcePulse + CEMPWeapon carrier, G2-16)",
    "target-markers": "HUD-2 - T-11/T-13 (marker objects, not an effect file)",
    "hack-fx": "WLD/MOD - not an FX code; the carrier is the interaction graph (G2-18)",
    "gel-rounds": "WPN-10 - named omission under D-3 (non-lethal rounds)",
    "fear-gas": "WPN - T-11 (riot-suppressor family)",
    "speed-lines": "FX? - 0 systems in G1-16; the donor's SpeedLinesSystem is T-FX6 (entity graph)",
}


# ---------------------------------------------------------------------------- inputs
def load_fx() -> dict[str, dict]:
    """One record per distinct `.effc` path: carriers, vehicles, size, rows, arrays."""
    rec: dict[str, dict] = {}
    with open(FX_TABLE, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            r = json.loads(line)
            if r["ext"] != ".effc":
                continue
            e = rec.setdefault(r["path"], {"path": r["path"], "containers": set(),
                                           "rows": r["rows"], "arrays": r["arrays"],
                                           "size": r["size"], "types": r["types"]})
            e["containers"].add(r["container"])
    for e in rec.values():
        e["vehicles"] = sum(1 for c in e["containers"] if "/jc_vehicles/" in c)
        e["donor"] = DONOR in e["containers"]
        e["container_list"] = sorted(e["containers"])
    return rec


def load_groups() -> dict[str, dict]:
    d = json.load(open(PARTICLES, encoding="utf-8"))
    out = {g["name"]: dict(g) for g in d["groups"]}
    for g in out.values():
        g["system_names"] = sorted({s["name"] for s in d["systems"] if s["group"] == g["name"]})
    return out


def load_usages() -> dict[str, dict]:
    d = json.load(open(USAGES, encoding="utf-8"))
    out = {}
    for u in d["usages"]:
        for name in u["names"]:
            if name:
                out[name] = {"hash": u["hash"], "vehicles": len(u["vehicles"]),
                             "effects": [e["effect"] for e in u["effects"]]}
    return out


def load_sockets() -> dict[str, dict]:
    d = json.load(open(SOCKETS, encoding="utf-8"))
    return {s["socket"]: s for s in d["sockets"]}


def load_weapon_facts() -> dict:
    rows = [json.loads(l) for l in open(WEAPONS, encoding="utf-8") if l.strip()]
    tr = {}
    for r in rows:
        s = r["summary"]
        b = next((k for k in s.get("blocks", {})), None)
        if not b:
            continue
        tr[r["id"]] = {"tracer_texture_type": s.get(f"{b}.bullet.tracer_texture_type"),
                       "tracer_fire_velocity": s.get(f"{b}.bullet.tracer_fire_velocity"),
                       "tracer_time_to_live": s.get(f"{b}.bullet.tracer_time_to_live"),
                       "smoke_trail_tile_size": s.get(f"{b}.bullet.smoke_trail_tile_size")}
    return {"ids": len(rows), "tracer": tr,
            "with_texture": sum(1 for v in tr.values() if v["tracer_texture_type"] is not None)}


# ---------------------------------------------------------------------------- derive
def derive(rules: list[dict], fx: dict[str, dict], groups: dict[str, dict],
           usages: dict[str, dict], sockets: dict[str, dict],
           weapons: dict) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    problems: list[str] = []
    for rule in rules:
        if rule.get("exact"):
            cands = sorted(rule["exact"])
            for p in cands:
                if p not in fx:
                    problems.append(f"{rule['id']}: {p} is not in FX_TABLE.jsonl")
        else:
            cands = sorted(p for p in fx
                           if any(m in p for m in rule["match"])
                           and not any(x in p for x in rule["exclude"]))
        veh = [p for p in cands if fx[p]["vehicles"]]
        row = {k: rule[k] for k in ("id", "code", "feature", "groups", "trigger", "now",
                                    "propose", "confidence", "verify", "dispo", "why")}
        row["authoring"] = rule.get("authoring")
        row["why_ledger"] = rule["why"][:120]
        row["absence"] = None
        row["chosen"] = None
        row["donor"] = rule["donor"]
        # --- attachment
        kind, name = rule["attach"]
        row["attachment"] = {"kind": kind, "name": name}
        if kind == "socket":
            s = sockets.get(name)
            if s is None:
                problems.append(f"{rule['id']}: socket {name!r} is not in SOCKETS_JC3.json")
            else:
                row["attachment"]["role"] = s["role"]
                row["attachment"]["part_hint"] = s["part_hint"]
        elif kind == "part":
            parts = {p["part_hint"] for p in sockets.values()}
            if name not in parts:
                problems.append(f"{rule['id']}: part {name!r} is not a SOCKETS_JC3 part_hint")
        # --- trigger
        trig = usages.get(rule["trigger"])
        row["trigger_evidence"] = ({"usage": rule["trigger"], "hash": trig["hash"],
                                    "vehicles": trig["vehicles"]} if trig else None)
        # --- absence vs choice
        if rule.get("absence"):
            test = rule["absence"]
            pool = veh if test == "no_vehicle_paths" else cands
            row["absence"] = {"test": test, "matches": len(pool),
                              "candidates": [{"path": p, "vehicles": fx[p]["vehicles"]}
                                             for p in cands[:8]]}
            if pool:
                problems.append(f"{rule['id']}: named omission is refuted - {len(pool)} path(s)"
                                f" match {rule['match']}, first {pool[0]}")
            row["chosen"] = None
        else:
            if not cands:
                problems.append(f"{rule['id']}: no effect path matches {rule['match']}")
                continue
            ranked = sorted(cands, key=lambda p: (-int(fx[p]["donor"]), -fx[p]["vehicles"],
                                                   -len(fx[p]["containers"]), p))
            chosen = ranked[0]
            if rule.get("head"):
                if rule["head"] not in cands:
                    problems.append(f"{rule['id']}: head {rule['head']} is not a candidate")
                else:
                    chosen = rule["head"]
                    ranked = [chosen] + [p for p in ranked if p != chosen]
            e = fx[chosen]
            row["chosen"] = {"path": chosen, "vehicles": e["vehicles"],
                             "containers": len(e["containers"]), "rows": e["rows"],
                             "arrays": e["arrays"], "size": e["size"], "donor": e["donor"],
                             "family_total": len(ranked),
                             "family": [{"path": p, "vehicles": fx[p]["vehicles"]}
                                        for p in ranked[:8]]}
        # --- BmAK side
        row["bmak"] = []
        for g in rule["groups"]:
            gr = groups.get(g)
            if gr is None:
                problems.append(f"{rule['id']}: group {g!r} is not in PARTICLES_FEATURES.json")
                continue
            names = gr["system_names"]
            nf = rule.get("names_filter")
            if nf:
                picked = [n for n in names if any(f.lower() in n.lower() for f in nf)]
                if picked:
                    names = picked
            row["bmak"].append({"group": g, "systems": gr["systems"], "distinct": gr["distinct"],
                                "emitters": gr["emitters"], "lifetime": gr["lifetime"],
                                "spawn_rate": gr["spawn_rate"], "names": names,
                                "names_filtered": bool(nf and len(names) < len(gr["system_names"]))})
        rows.append(row)
    return rows, problems


def bmak_cell(row: dict) -> str:
    if not row["bmak"]:
        return "no system in G1-16's 206"
    parts = []
    for b in row["bmak"]:
        shown = b["names"][:3]
        names = ", ".join(shown) + ("..." if len(b["names"]) > 3 else "")
        if b.get("names_filtered"):
            names = f"{len(b['names'])} of {b['distinct']} names ({names})"
            label_names = names
        if b["lifetime"] is None:
            parts.append(f"G1-16 {b['group']}: 0 systems (proven absent), 0 emitters")
            continue
        if b.get("names_filtered"):
            label = f"{b['systems']} systems, {names}"
        else:
            label = f"{b['systems']} systems / {b['distinct']} names ({names})"
        parts.append(f"G1-16 {b['group']}: {label}, {b['emitters']} emitters, "
                     f"life {b['lifetime'][0]}..{b['lifetime'][1]} s")
    return "; ".join(parts)


def jc3_cell(row: dict, fleet_total: int) -> str:
    c = row["chosen"]
    if not c:
        cands = row["absence"]["candidates"]
        if not cands:
            return f"**no effect path** in the {fleet_total} distinct `.effc`"
        return ("**no vehicle-carried effect**; non-vehicle matches: "
                + ", ".join(f"`{x['path']}`" for x in cands[:3]))
    fam = "" if c["family_total"] <= 1 else f"; {c['family_total']} variants"
    return (f"`{c['path']}` - {c['vehicles']} vehicles{fam}, {c['size']:,} B, "
            f"{c['arrays']} arrays, {c['rows']} rows")


def attach_cell(row: dict) -> str:
    a = row["attachment"]
    if a["kind"] == "socket":
        return f"socket `{a['name']}` (role {a.get('role')}, G1-13)"
    if a["kind"] == "part":
        return f"part `{a['name']}` (G1-13 part_hint)"
    if a["kind"] == "impact":
        return "impact point (no socket: the bullet's hit position)"
    return "none"


def row_cells(row: dict, fleet_total: int) -> list[str]:
    return [row["id"], bmak_cell(row), jc3_cell(row, fleet_total), attach_cell(row), row["now"],
            row["propose"], row["confidence"], row["verify"]]


# ---------------------------------------------------------------------------- outputs
def build_payload() -> tuple[dict, list[str]]:
    fx = load_fx()
    groups = load_groups()
    usages = load_usages()
    sockets = load_sockets()
    weapons = load_weapon_facts()
    rows, problems = derive(RULES, fx, groups, usages, sockets, weapons)
    for row in rows:
        row["cells"] = row_cells(row, len(fx))
    counts = {
        "rules": len(RULES),
        "rows": len(rows),
        "chosen": sum(1 for r in rows if r["chosen"]),
        "named_omission": sum(1 for r in rows if r["absence"]),
        "authoring_plans": sum(1 for r in rows if r.get("authoring")),
        "fx_codes": sorted({r["code"] for r in rows}),
        "fx_codes_covered": sorted({r["code"] for r in rows
                                    if r["chosen"] or r["absence"]}),
        "donor_effects": sum(1 for e in fx.values() if e["donor"]),
        "fleet_effc": len(fx),
        "fleet_vehicle_effc": sum(1 for e in fx.values() if e["vehicles"]),
        "sockets": sorted({r["attachment"]["name"] for r in rows
                           if r["attachment"]["kind"] == "socket"}),
        "usages": sorted({r["trigger"] for r in rows if r["trigger_evidence"]}),
        "weapon_ids": weapons["ids"],
        "weapon_tracer_ids": weapons["with_texture"],
    }
    payload = {
        "schema": 1,
        "generated_by": "t17_fx.py",
        "card": "T-17 (GRAB_BACKLOG.md §7)",
        "inputs": {
            "fx_table": "Research/JC3Grab/FX_TABLE.jsonl",
            "particles": "Research/BatmobileGrab/PARTICLES_FEATURES.json",
            "usages": "Research/JC3Grab/USAGES.json",
            "weapons": "Research/JC3Grab/WEAPONS.jsonl",
            "sockets": "Research/BatmobileGrab/SOCKETS_JC3.json",
        },
        "donor_entity": DONOR,
        "method": {
            "kind": "needle match on the .effc path",
            "rank": ["donor-carried", "vehicles carrying it", "containers", "path"],
            "size": "reported both sides (BmAK systems/emitters/lifetime vs effect rows/arrays/bytes);"
                    " no unit bridge, so size does not rank",
            "absence": "a named omission fails if its needles match (all paths, or the vehicle-carried"
                       " subset for `no_vehicle_paths`)",
        },
        "summary": counts,
        "rows": rows,
    }
    return payload, problems


def read_doc(payload: dict, groups: dict[str, dict]) -> list[str]:
    s = payload["summary"]
    L: list[str] = []
    a = L.append
    a("# Effects translation (T-17)")
    a("")
    a("Generated by `Tools/scripts/t17_fx.py` from `FX_TABLE.jsonl`, `PARTICLES_FEATURES.json`,")
    a("`USAGES.json`, `WEAPONS.jsonl` and `SOCKETS_JC3.json`; `--check` re-reads all five,")
    a("re-derives this file and `t17_fx.json`, compares both and cross-checks `T_ROWS.jsonl`.")
    a("One row per effect feature, `FX-1`…`FX-4`: the JC3 `.effc` chosen, the socket or part it")
    a("attaches to, and the trigger that fires it - or a named omission with the proof.")
    a("")
    a("| item | value |")
    a("|---|---|")
    a(f"| BmAK systems | {sum(g['systems'] for g in groups.values())} in "
      f"{sum(1 for g in groups.values() if g['systems'])} feature groups (G1-16) |")
    a(f"| JC3 `.effc` paths | {s['fleet_effc']} distinct ({s['fleet_vehicle_effc']} carried by a "
      f"vehicle) in 57,187 FX rows |")
    a(f"| donor chassis effects | **{s['donor_effects']}** carried by `v0300…signature_preorder.ee` |")
    a(f"| rows | **{s['rows']}** - {s['chosen']} with a chosen effect, {s['named_omission']} named "
      f"omissions |")
    a(f"| FX codes covered | **{len(s['fx_codes_covered'])}/4** ({', '.join(s['fx_codes_covered'])}) |")
    a(f"| sockets used | {len(s['sockets'])} |")
    a("")
    a("## 1. The 21 BmAK groups and who owns them")
    a("")
    a("G1-16 put every one of the 206 systems in exactly one group; this card owns the FX codes of")
    a("§1, and a group that serves another code is named with its owner so nothing falls between")
    a("cards. A group with 0 systems is a proven absence on the BmAK side, not an untranslated")
    a("feature.")
    a("")
    a("| group | systems | emitters | lifetime s | owner |")
    a("|---|---:|---:|---|---|")
    for name, g in groups.items():
        owner = OWNER.get(name, OTHER_GROUPS.get(name, "not an FX code"))
        life = "-" if g["lifetime"] is None else f"{g['lifetime'][0]}..{g['lifetime'][1]}"
        a(f"| `{name}` | {g['systems']} | {g['emitters']} | {life} | {owner} |")
    a("")
    a("## 2. The rows")
    a("")
    a("Cells: id, BmAK source, JC3 effect, attachment, now, proposed, confidence, verify. The")
    a("`verify` cell names a §9b probe with a numeric or categorical pass; `confidence` uses the R4")
    a("classes (`decoded` = both sides read from files, `derived` = the mapping needed judgement).")
    a("")
    a("| id | BmAK source | JC3 effect | attachment | now | proposed | confidence | verify |")
    a("|---|---|---|---|---|---|---|---|")
    for row in payload["rows"]:
        a("| " + " | ".join(row["cells"]) + " |")
    a("")
    a("## 3. Sockets and parts used")
    a("")
    a("Every attachment is a `SOCKETS_JC3.json` socket or a named part, so the effect lands on the")
    a("mesh the build already has (G1-13, 65 sockets, 13/13 required anchors present).")
    a("")
    a("| row | attachment | role | part |")
    a("|---|---|---|---|")
    for row in payload["rows"]:
        at = row["attachment"]
        if at["kind"] not in ("socket", "part"):
            continue
        a(f"| `{row['id']}` | `{at['name']}` | {at.get('role', '-')} | {at.get('part_hint', '-')} |")
    a("")
    a("## 4. The five rows that used to be named omissions")
    a("")
    a("Each of these was `out` on a keyword test over the 955 effect paths. Five reports replaced")
    a("that test with a shipped carrier or an authoring plan; the rows are `next`, and the old")
    a("claim is kept here so it is not re-derived from the same keyword search.")
    a("")
    a("| row | what the row used to say | why the keyword test could not see the carrier | now |")
    a("|---|---|---|---|")
    rows_by = {r["id"]: r for r in payload["rows"]}
    for rid in ("T-FX9", "T-FX12", "T-FX13", "T-FX16", "T-FX20"):
        row = rows_by[rid]
        was, blind = FORMER[rid]
        now = f"`{row['chosen']['path']}`" if row.get("chosen") else "authoring plan (§5)"
        if row.get("authoring"):
            now += " + plan (§5)"
        a(f"| `{rid}` | {was} | {blind} | {now} |")
    a("")
    a("## 5. Authoring plans: private copies and the members that change")
    a("")
    a("A private copy is written at its decoded offsets by `Tools/scripts/effc_writer.py`")
    a("(`Working/Effects/EFFC_WRITER.md`): a value patch keeps every array length, so `A[..]`")
    a("pairs, data offsets and `total_size` stay valid. **Growth** - adding an emitter, template or")
    a("instantiator - re-lays out the data block and is the one step the format report did not")
    a("build or re-read; card `B-17` owns it.")
    a("")
    for row in payload["rows"]:
        au = row.get("authoring")
        if not au:
            continue
        a(f"### {row['id']} · {row['feature']}")
        a("")
        a(f"* copy: {au['copy']}")
        a("* members that change: " + "; ".join(au["members"]))
        a(f"* growth: {au['grows']}")
        a(f"* gap the build fills: {au['gap']}")
        a(f"* evidence: {au['evidence']}")
        a("")
    a("## 6. UNKNOWNs and limits")
    a("")
    a("- **Size is reported, not matched.** The BmAK side gives systems/emitters/lifetime/size in")
    a("  UE units; the JC3 side gives effect rows/arrays/bytes. No unit or scaling bridge exists")
    a("  between them, so the ranking is kind -> donor -> fleet use, and the size numbers stand")
    a("  beside the choice for a human to review. A size-fit claim would be `UNKNOWN`.")
    a("- **No in-game proof.** Nothing here is observed in a running game (R6: no launch before")
    a("  phase V). Every `verify` cell is a Q probe that can fail.")
    a("- **Which weapon ids FX-2 rides on is T-11's** (D-3/D-7 decide slots and lethality). The")
    a("  effects named are the fleet's own for that weapon *kind*, measured per id: the weapon")
    a("  bundles carry them, so a clone brings them (w619 16, w610 14, w618 12, w608 5 effects;")
    a("  w602/w603/w604 ship no bundle of their own, G2-10).")
    a("- **`EngineNitro` is a usage name, not a proven boost trigger.** G2-22/23 read the hash and")
    a("  the attachments; that the flame appears on the boost input is a Q-1/Q-2 probe.")
    a("- **The `.effc` writer is proved for in-place patches, not for growth.** `effc_writer.py")
    a("  check` re-encodes 95/95 sampled shipped effects byte-for-byte (91.49% of their bytes from")
    a("  decoded fields, 0 unexplained bytes) and writes one edited copy")
    a("  (`EmitterTemplates[0].MaxParticles` 60 -> 317) that re-reads; adding or removing array")
    a("  elements is expressible (explicit u64 offsets and counts) but was not built or re-read, so")
    a("  T-FX12/T-FX16 carry it as the gap card `B-17` closes (`effc-format-writable.md` §4/§6).")
    a("")
    a("## 7. Outputs and regeneration")
    a("")
    a("| path | what it is |")
    a("|---|---|")
    a("| `Working/Translation/T13_FX.md` | this file, regenerated by `--write` |")
    a("| `Working/Translation/t17_fx.json` | the same rows as data, with every candidate and count |")
    a("| `Tools/scripts/t17_fx.py` | the tool; `--write` / `--check` / `show <id>` |")
    a("")
    a(f"`--check` re-derives {s['rows']} rows over {s['fleet_effc']} effect paths and "
      f"{s['donor_effects']} donor effects, compares both files and the ledger.")
    a("")
    return L


# The five rows this revision replaced, and why a keyword search over effect *paths* could not
# see the carrier. Kept in the generated document so the old claim is not re-litigated.
FORMER = {
    "T-FX9": ("named omission: no `haze` path in the 955",
              "a `.effc` carries no string values (0 in 955/955, `FX9_HAZE` §2), so only a *filename*"
              " could match; the carrier is named after the part (`car_speedrom_heater`) and attached"
              " by 24 `z80_exhaust_heat_l/r` objects in the entity graph"),
    "T-FX12": ("named omission: no `tracer` path (0 of 955)",
               "the tracer is a `WeaponTuning` texture enum, not an effect file, so no path could"
               " match; the art half is a 2-emitter system bound to the projectile in BmAK, a binding"
               " JC3 has no member for"),
    "T-FX13": ("named omission: no vehicle-carried `casing`/`shell` path",
               "the shipped paths are `bullet_eject_*`, and the carrier is an `SAttachedEffect` in the"
               " weapon entity's graph - the search only looked at effect *filenames*"),
    "T-FX16": ("named omission: no `canon_trail`/`shell_trail` path (claim later UNKNOWN)",
               "the row named no search term at all (`FX16_TERM.md`), so its `0 of 955` was never a"
               " negative; the carrier is the same `.effc` route as T-FX12"),
    "T-FX20": ("named omission: no `brake` path, no `BrakeLightTrail` system in G1-16",
               "the 0-of-955 holds for the word `brake`, but BmAK's own `BrakeTrail0/1` components"
               " serialise no system, so there was nothing to copy on either side - the look has to be"
               " authored"),
}

# who owns each non-FX group is data, not prose: the group table is generated from it
OWNER: dict[str, str] = {}
for _r in RULES:
    for _g in _r["groups"]:
        _c = _r["code"]
        OWNER[_g] = (_c if OWNER.get(_g, _c) == _c else f"{OWNER[_g]} + {_c}")


# ---------------------------------------------------------------------------- commands
def write_doc(payload: dict, groups: dict) -> list[str]:
    return read_doc(payload, groups)


def cmd_write() -> int:
    payload, problems = build_payload()
    groups = load_groups()
    lines = write_doc(payload, groups)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=True)
        f.write("\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    for p in problems:
        print("FAIL", p)
    s = payload["summary"]
    print(f"{OUT_JSON}: {s['rows']} rows ({s['chosen']} chosen, {s['named_omission']} named "
          f"omissions), FX codes {len(s['fx_codes_covered'])}/4")
    print(f"{OUT_MD}: {len(lines)} lines")
    return 1 if problems else 0


def cmd_check() -> int:
    payload, problems = build_payload()
    bad = 0
    if not os.path.exists(OUT_JSON):
        print(f"FAIL: no {OUT_JSON} - run --write first")
        return 1
    on_disk = json.load(open(OUT_JSON, encoding="utf-8"))
    if on_disk != payload:
        bad += 1
        print("FAIL: t17_fx.json differs from the re-derived record")
        a, b = json.dumps(on_disk, sort_keys=True), json.dumps(payload, sort_keys=True)
        for i in range(min(len(a), len(b))):
            if a[i] != b[i]:
                print(f"   first difference at char {i}: {a[max(0,i-60):i+60]!r} != "
                      f"{b[max(0,i-60):i+60]!r}")
                break
    groups = load_groups()
    new_md = "\n".join(write_doc(payload, groups)) + "\n"
    disk_md = open(OUT_MD, encoding="utf-8").read() if os.path.exists(OUT_MD) else ""
    if disk_md != new_md:
        bad += 1
        print("FAIL: T13_FX.md differs from the re-derived record")
        import difflib
        for line in list(difflib.unified_diff(disk_md.splitlines(), new_md.splitlines(),
                                              "T13_FX.md", "re-derived", lineterm=""))[:20]:
            print("   " + line)
    # every chosen path must still be in the table, every socket still present
    fx = load_fx()
    sockets = load_sockets()
    for row in payload["rows"]:
        c = row["chosen"]
        if c and c["path"] not in fx:
            bad += 1
            print(f"FAIL {row['id']}: {c['path']} is no longer in FX_TABLE.jsonl")
        if row["attachment"]["kind"] == "socket" and row["attachment"]["name"] not in sockets:
            bad += 1
            print(f"FAIL {row['id']}: socket {row['attachment']['name']} left SOCKETS_JC3.json")
    # the ledger must carry every row with the same disposition and reason
    led = {r["id"]: r for r in (json.loads(l) for l in open(LEDGER, encoding="utf-8")
                                if l.strip())}
    for row in payload["rows"]:
        lr = led.get(row["id"])
        if lr is None:
            bad += 1
            print(f"FAIL {row['id']}: missing from T_ROWS.jsonl - run `t_rows.py build`")
            continue
        if lr["dispo"] != row["dispo"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger dispo {lr['dispo']} != {row['dispo']}")
        if not lr.get("why"):
            bad += 1
            print(f"FAIL {row['id']}: ledger row has no reason")
        if lr["cells"] != row["cells"]:
            bad += 1
            print(f"FAIL {row['id']}: ledger cells differ from the document")
    for p in problems:
        bad += 1
        print("FAIL", p)
    s = payload["summary"]
    covered = len(set(s["fx_codes_covered"]) & {"FX-1", "FX-2", "FX-3", "FX-4"})
    print(f"{'PASS' if not bad else 'FAIL'}: {s['rows']} rows ({s['chosen']} chosen, "
          f"{s['named_omission']} named omissions) | FX codes {covered}/4 | donor effects "
          f"{s['donor_effects']} | fleet .effc {s['fleet_effc']} | sockets {len(s['sockets'])} | "
          f"ledger {sum(1 for r in payload['rows'] if r['id'] in led)}/{s['rows']}")
    return 1 if bad else 0


def cmd_show(want: str) -> int:
    payload, _ = build_payload()
    hit = [r for r in payload["rows"] if want.lower() in r["id"].lower()]
    if not hit:
        raise SystemExit(f"no row matches {want!r}")
    print(json.dumps(hit, indent=1))
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--write", action="store_true")
    p.add_argument("--check", action="store_true")
    sub = p.add_subparsers(dest="cmd")
    s = sub.add_parser("show")
    s.add_argument("want")
    a = p.parse_args()
    if a.cmd == "show":
        return cmd_show(a.want)
    if a.write:
        return cmd_write()
    if a.check:
        return cmd_check()
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

# Hacker and tracker gadgets: T-WP7 / T-WP9

T-7 closed both as omissions because only class names were searched. The wider search finds no `allegiance` member and no `tracker` class, but it finds the systems that do the jobs: the SAM context-act hack, the Rebel Drop item table, and the HUD POI/mission tracker. Each BmAK field is mapped below; where no member exists the field is UNKNOWN with the places searched. Evidence tables: `Research/JC3Grab/GADGETS_HACK_TRACK.md`. Checks 20/20.

## The two gadgets (BmAK)

**`RBatmobileAllegianceSwitcher` / `Drone_Hacker`** - 3 packages, 13 fields, 39 field rows, identical in every package.

**`RPursuitModeMissileLauncher` / `Vehicle_Tracker`** - 3 packages, 7 fields, 21 field rows, identical in every package.

## T-WP7 - field by field

| BmAK field | value | closest JC3 | gap |
|---|---|---|---|
| `BatmobileHackerEffect` | Particles.DroneHacker_Beam | `SAttachedEffect.Effect` + `.Usage` (5,342 objects in 232 graphs) | the beam effect is authored from a beam `.effc` clone and attached at the drone's beam socket; no `DroneHacker_Beam` exists in JC3 |
| `SuccessfulHackEffect` | Particles.DroneHacker_Success | `SAttachedEffect` on the same entity, second `Usage` (`Fire2`/value-driven usage) | a second attachment; JC3 has no 'hack succeeded' event, so the trigger has to come from the weapon that completes the hack |
| `BatmobileHackerEffectHvyTank` | Particles.CobraHacker_Beam | same `SAttachedEffect` slot, different effect path | author a second beam variant; no data chooses it |
| `SuccessfulHackEffectHvyTank` | Particles.CobraHacker_Success | same success attachment | author it, or reuse the first |
| `DroneHackerMaterial` | Materials.DroneHacker_Beam_INST | UNKNOWN - no material member in any decoded weapon tune or `.effc` member path | material must be authored inside the effect (`.effc` texture) - the JC3 effect format has no material-instance member |
| `SucessfullHackSound` | Engine.Play_Batmobile_DroneHacker_Hacked | UNKNOWN - weapon tunes carry no audio member | wire the event in the entity's audio module and add the bank entry |
| `HackingSound` | Engine.Play_Batmobile_DroneHacker_Fire | UNKNOWN - same search | second audio event on the same module |
| `BeamPositionalSound` | Engine.Play_Batmobile_DroneHacker_Loop | UNKNOWN - same search | loop handle on the beam attachment |
| `NotEnoughEnergyThought` | Lines.Char_Batman_Misc_Cobra_Barrage_Energy_B_01 | `CreatePoi(type, use_progress_bar, is_minor, label)` label on `ui/hud.gfx` | JC3 has no 'thought' element; the line becomes a POI label or a HUD string |
| `HackerEffect` | 6 items, 4 B each (payload not decoded) | six `SAttachedEffect`/`SDynamicAttachedEffect` rows (the decoded array is six 4-byte component references) | six attachment rows at six beam sockets; the array itself has no JC3 carrier |
| `RVehicleWeapon.WeaponCoolDown` | 1.0 | `burst_cooldown` in the weapon tuning (22 rows) | use the tune's cooldown field; a 1.0 s value has no unit bridge |
| `RInventoryGadget.Mesh` | Drone_Hacker.GadgetMesh | the mounted weapon entity's mesh (a `w6xx_*.ee` weapon entity) | ship the gadget mesh inside the weapon entity |
| `Actor.Tag` | "RBatmobileAllegianceSwitcher" | entity/part `name` (`part` in `VehicleDynamicLights`, `name` in modules) | none - naming only |

## T-WP9 - field by field

| BmAK field | value | closest JC3 | gap |
|---|---|---|---|
| `RPursuitModeMissileLauncher.ProjectileArchetype` | Projectiles.Batmobile_Tracker_Projectile | the mounted weapon entity `.ee` + `missile_weapon[0].tuning.missile_base_tuning.*` | the tracker projectile becomes a weapon entity + tune; its homing numbers map to those two members, the rest to the projectile entity |
| `RPursuitModeMissileLauncher.LaunchSocketName` | "BattleModeSpotLight" | `SWeaponPoint` fire position in the weapon entity (8 in the SAM dump) | author a fire position and name it; the BmAK socket is `BattleModeSpotLight`, which is also a light socket - the build must decide both uses |
| `RPursuitModeMissileLauncher.LaunchRotationOffset` | [5461, 0, 0] | the `world` matrix of `SWeaponPoint` | bake the rotator into the matrix: 5461/65536*360 = 30.0 deg (derived) |
| `RVehicleWeapon.FireStartEvent` | ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire | UNKNOWN - 0 audio members in the weapon tunes | wire the fire event in the weapon entity's audio module |
| `RVehicleWeapon.IndividualFireEvent` | ww_chr_batmandisruptor.Play_BatSniperRifle_Vehicle_Tracking_Fire | UNKNOWN - same | same event, per-shot |
| `RInventoryGadget.Mesh` | Vehicle_Tracker.GadgetMesh | the mounted weapon entity's mesh | ship the tracker mesh in the weapon entity |
| `Actor.Tag` | "RBatmobileVehicleTracker" | entity/part `name` | none - naming only |

## The tracker projectile (16 fields)

| BmAK field | value | closest JC3 | gap |
|---|---|---|---|
| `RBatmobileMissile.Trail` | Batmobile_Tracker_Projectile.RocketTrail | projectile entity mesh/trail components | author the mesh/trail in the weapon entity |
| `RBatmobileMissile.Mesh` | Batmobile_Tracker_Projectile.Mesh0 | projectile entity mesh/trail components | author the mesh/trail in the weapon entity |
| `homing flag (unnamed bool)` | true | missile tuning: `missile_base_tuning.missile_loose_lock_distance`, `meters_times_speed_in_front_of_target`, plus the projectile entity | no homing-flag/delay/damage members in the tune vocabulary (measured) |
| `RBatmobileMissile.HomingDelay` | 0.2 | missile tuning: `missile_base_tuning.missile_loose_lock_distance`, `meters_times_speed_in_front_of_target`, plus the projectile entity | no homing-flag/delay/damage members in the tune vocabulary (measured) |
| `RBatmobileMissile.AccelRate` | 30000.0 | missile tuning: `missile_base_tuning.missile_loose_lock_distance`, `meters_times_speed_in_front_of_target`, plus the projectile entity | no homing-flag/delay/damage members in the tune vocabulary (measured) |
| `RBasicProjectile.ProjectileMesh` | Batmobile_Tracker_Projectile.Mesh0 | projectile entity mesh/trail components | author the mesh/trail in the weapon entity |
| `RBasicProjectile.ProjectileTrail` | Batmobile_Tracker_Projectile.RocketTrail | projectile entity mesh/trail components | author the mesh/trail in the weapon entity |
| `RProjectile.ImpactRadialImpulseComponent` | Batmobile_Tracker_Projectile.ImpulseComponent0 | projectile entity component | component identity only |
| `Projectile.MaxSpeed` | 20000.0 | missile tuning: `missile_base_tuning.missile_loose_lock_distance`, `meters_times_speed_in_front_of_target`, plus the projectile entity | no homing-flag/delay/damage members in the tune vocabulary (measured) |
| `Projectile.CylinderComponent` | Batmobile_Tracker_Projectile.CollisionCylinder | projectile entity component | component identity only |
| `Projectile.MyDamageType` | 0 (null) | weapon tune damage/momentum members (not the ones BmAK uses) | JC3 tune has no `MomentumTransfer` shape identical to BmAK |
| `Projectile.DamageRadius` | 0.0 | weapon tune damage/momentum members (not the ones BmAK uses) | JC3 tune has no `MomentumTransfer` shape identical to BmAK |
| `Projectile.MomentumTransfer` | 500.0 | weapon tune damage/momentum members (not the ones BmAK uses) | JC3 tune has no `MomentumTransfer` shape identical to BmAK |
| `Actor.DefaultAkAudible` | Batmobile_Tracker_Projectile.DefaultAkAudible_ | UNKNOWN - audio | audio module |
| `Actor.CollisionComponent` | Batmobile_Tracker_Projectile.CollisionCylinder | projectile entity component | component identity only |
| `Actor.Tag` | "RBatmobileMissile" | projectile entity component | component identity only |

## Lead 1: SAM site hacked, then targets enemy aircraft

- `w501_turret_sam_v2.ee` decodes to 333 objects; 1 `CTurretWeaponComponent` carries `faction` = 5
- 8 `SWeaponPoint` fire positions (fire_position_1..6, SWeaponPoint1) and one `STargetPoint` (`min_aim_distance` 5)
- the hack is a local interaction graph: `animations/jc_characters/main_characters/rico/contextact/rico_contextact_hack_sam.anim`, `animations/jc_characters/main_characters/rico/contextact/rico_contextact_hack_sam_enter.anim`, `animations/jc_characters/main_characters/rico/contextact/rico_contextact_hack_sam_exit.anim`, `CInteractionGraph` exit state `use_item`, 2 `CInteractionTrigger` volumes, 0 `ignore_faction`, 0 `radar`, 0 range/radius members
- the only faction values in the entity are 5 (turret weapon component) and 2 (`AreaDamage`, `enabled` 0, interval 3, damage 5..20); `air` matches only `CAIRoadObstacle` (an AI road obstacle), so **no aircraft filter is in the file**

**Closest system:** the SAM context-act hack itself (interaction graph + hack animation) plus `CTurretWeaponComponent.faction` as the side the turret fires for

**Gap:** 'hacked then fires on enemy aircraft' is not carried by the data: the entity has a local use-item graph and a faction int, but no ownership member, no aircraft target filter and no remote delivery. The build composes: the context act (or a weapon that reaches the turret) + a faction flip on the turret component + the target priority the tune carries (`air_vehicle_target_priority` is a real JC3 tune member). **UNKNOWN**: what the SAM hack does to ownership at runtime.


## Lead 2: drones cannot be hacked; Rebel Drop your own drone

- 18 drone entities, root class `CUnmanedQuadcopterDrone` on 9 of them
- no drone root carries `faction`, `sides` or `allegiance`; the only side-like value is `faction` = 5 on 5 weapon points
- 196 vanilla Rebel Drop items, 0 of them name a drone
- 2 drone drop assets do exist: `textures/ui/vehicle_icons/v2901_drone_eden_elitedrone_rebeldrop.ddsc`, `videos/vehicles/v2901_drone_eden_elitedrone_rebeldrop.bikc`
- 1 hack in the whole fleet (`w501`), 0 `hack`-named `.effc`

**Closest system:** `Item.Name` = Jenkins hash of an entity leaf (REBELDROP.md §4): adding the drone `.ee` as a drop item spawns it; the artwork and drop video already exist

**Gap:** the friendly side is the gap: nothing in the data makes a drone yours. The build must ship a drone entity that is on the player's side (faction on its weapon points + whatever the engine reads), name its leaf, and add the `Item` row (Type 1, UIType 3, RebelDropTimer 0, no task reward = the mod's working pattern). The artwork/`videos/...bikc` can be reused as-is.


## Lead 3: missions/random encounters track a vehicle with a distance readout and a yellow or grey circle

- HUD: 32 `POI_TYPE_*` constants, `POI_TYPE_LOCK_ON_TARGET` = 21, drawn as one rotating reticle (1.5 s per turn, `hud_code/poi.as`); `CreatePoi(type, use_progress_bar, is_minor, label)` is the only constructor
- mission carrier: `graphs/mission/mm130/mm130_tracker.gdc/.gsc/.stringlookup`, `graphs/spawner_group_tracker.gdc/.gsc`, 37 random-encounter graphs
- vehicle side: `CAimPOIWeaponComponent` on 11 fleet vehicles (FEATURE_CENSUS) - a weapon component that aims at a POI
- no per-vehicle map marker texture exists (NAMES.md §5); 113 `textures/ui/vehicle_icons/*` are menu icons

**Closest system:** a HUD POI (`CreatePoi` + a label) created by a mission-style tracker graph, with the vehicle's `.ee` as the target; `CAimPOIWeaponComponent` is the only vehicle-side POI reference

**Gap:** **no distance member**: `CreatePoi` takes type, progress bar, minor flag and label only, so a distance readout is not a POI field. No yellow/grey circle pair exists as a decoded POI type (the type -> icon switch is in `poi.as`, not decoded per type). The build composes a graph-style tracker that creates a POI on the target and a HUD element that prints the distance; the marker's colour/shape must be authored (the game's own marker art is not in the index as a separate file).


## UNKNOWN, with the places searched

- **Entity-level allegiance / owner**: 0 in 295 `.ee` wiring dumps (value names, class names, strings tree, ADF type names, entity names). `faction` exists only on weapon points, camera/light/physics structs; `ignore_faction`, `sides`, `side_area` are camera/light/physics hints.

- **Weapon-tune audio / material / socket members**: 0 audio, 0 socket, 0 material out of 444 member paths; audio lives in `.bnk` banks and entity audio objects, which these tables do not decode.

- **What the SAM hack does to ownership**: the entity has the interaction graph and the animation, not the runtime effect. The operator's 'targets enemy aircraft' cannot be confirmed from the file; no aircraft filter exists in it.

- **The distance readout and the yellow/grey circle**: `CreatePoi` takes a type, progress flag, minor flag and label - no distance. The POI type -> icon switch is in `hud_code/poi.as`, not decoded per type; no separate marker art file exists in the index.

- **The friendly drone's ownership**: no drone root carries a side; the drop artwork exists but 0 of 196 items name a drone.

## Checks

- PASS `wp7_fields_13` 13
- PASS `wp7_packages_3` 3
- PASS `wp9_fields_7` 7
- PASS `tracker_projectile_16` 16
- PASS `launch_rotation_30deg` 30.0 deg
- PASS `hack_files_2` 2
- PASS `allegiance_files_0` 0
- PASS `drones_18` 18
- PASS `drone_drop_items_0` 0
- PASS `drone_drop_assets_2` 2
- PASS `vanilla_items_196` 196
- PASS `tune_audio_members_0` 0
- PASS `hostility_members_6` 6
- PASS `air_vehicle_target_priority` 6 priority members
- PASS `fx_hack_0` 0
- PASS `hud_lock_on_21` 21
- PASS `sam_seven_weapon_points` 7
- PASS `sam_no_air_filter` 0 'air' hits
- PASS `sam_two_factions` ['2', '5']
- PASS `every_field_mapped` 20 rows

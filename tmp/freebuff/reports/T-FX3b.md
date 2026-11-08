# T-FX3b - is there ANY JC3 carrier for a vehicle exhaust / boost flame?

STATUS: done - the carrier exists and is decoded end to end (module, member, offset, trigger).
T-FX3's wording ("no usage slot for an exhaust flame") holds only for the *stat* modules it was
looking at; the engine-level answer is YES.

## What the question turned into

An exhaust flame is not a slot in a handling/audio stat module. In JC3 it is an **entity object**
(`SAttachedEffect` / `SDynamicAttachedEffect`) whose `effect` member points at an `.effc` file and
whose `usage` member names the state that fires it. The generated
`<vehicle>_effect_attachments.vmodc` module is the table that binds those objects to a vehicle.
So the row was answered by decoding both halves, not by repeating the claim.

## Answer, with labels

- **carrier class** (decoded, `Research/JC3Grab/USAGES.json` -> `epe.classes`): `SAttachedEffect`
  5342 objects, `SDynamicAttachedEffect` 4344, tables `SAttachedEffectTable` 1678 /
  `SDynamicAttachedEffectTable` 1212, over 232 vehicle detail files.
- **module** (decoded, `jc3adf.Adf` on
  `Builds/bm-001/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/generated/v0300_car_kensington_sportsmuscle_effect_attachments.vmodc`,
  12,163 B): one instance `EffectAttachments`, type `600100251`, data offset 80, size 10,576.
- **member + offset chain for `usage`** (decoded from the ADF type table, offsets read from the
  file, not inferred):
  - `EffectAttachments` (type `600100251`, 48 B): `all_effects` +0, `part_effects` +16,
    `usage_effects` +32;
  - `UsageEffectAttachments` (type `2674124397`): `usage` +0, size 8.
  - path: instance member `usage_effects` +32 -> element `UsageEffectAttachments.usage` +0.
- **member + offset for `effect`** (decoded): `EffectAttachment` (type `3213548423`, 32 B):
  `deform_point` +0 (8 B), `effect` +16 (8 B). The attachment struct has **no** usage and **no**
  transform - both live elsewhere, which is why "no usage slot" was read into it.
- **transform `world`**: not in the module. It is a member of the `.epe` object `SAttachedEffect`,
  and an `.epe` is an RTPC container (`rtpcdump.py`: magic `RTPC`, version 1), not ADF, so no
  typed struct offsets exist for it here. Two byte probes of the base `.epe` (124,488 B) for the
  edit's own matrix text (`-0.4101563`, `-4.371139E-08`) both return "not found": the matrix is
  stored as binary floats. `world`'s struct offset: **UNKNOWN** (see UNKNOWNs).
- **how it is triggered** (decoded, `USAGES.json`):
  - usage ids that carry exhaust/boost effects (12 usage rows, 3 of them matching):
    `2819629913` = `EngineRunning` (69 modules; effects `EngineNitro` x20, `dynamic_exhaust` x46),
    `3877802965` = `EngineTurboJump` (11 modules; `dynamic_tjump` x11),
    `4197885156` = `EngineNitro` (18 modules; `EngineNitro` x4, `dynamic_nitrous` x14).
  - the arcade boost fields that raise that family: `heat_boost`, `nitro_boost`,
    `nitro_boost_upgraded`, `turbo_jump`, `turbo_jump_upgraded`, 145 carriers each.
  - **value-driven** usages (the loop shape): named conditions in the fleet's `.epe` objects -
    `IsInAir` (126 vehicles), `IsInWater` (126), `IsPlayerControlled` (180), `Sinking` (35),
    `z80_speed_threshold` (10), `BavariumShieldOn` (3), `SValueDrivenEffectUsage` (12 objects).
    An effect bound to one of these is enabled while the state holds, not fired once.
- **fleet evidence** (decoded, `Research/JC3Grab/FX_TABLE.jsonl`, `.effc`/`.effp` only): 43
  exhaust/boost effect files across 296 cargo containers in `base`, `dlc`, `patch`.
  Includes `effects/jc_vehicles/exhaust/car_tjump_trail.effc` (car, 135 containers),
  the helicopter boost effect and the boat splash-nitro effect - i.e. jets, boats and Rico's
  boost all use the same carrier the car's exhaust uses.
- **build state** (decoded, `Working/Effects/bm_fx_edits.json`, card B-08 / row T-FX7): the build
  already ships this carrier - the donor's two emitters `exhaust_upgrade_nitrous` /
  `exhaust_upgrade_nitrous2` (class `SAttachedEffect`) point at
  `effects/jc_vehicles/exhaust/car_cycle_base_dual_nitrous.effc` (hash `-776668445`) with
  `usage` = `EngineNitro` (`4197885156`), and their `world` is moved onto the `Afterburner`
  socket (bone `JetSMove`, position `[-0.009578, 0.537762, 3.393177]` m).

## What is genuinely limited (derived from the above, not a carrier gap)

The usable triggers are the fleet's own `usage` values, because an attachment fires only when the
vehicle's state machine raises one. `EngineNitro` is raised by the arcade nitro field, and the
build ships it - so a boost flame is reachable. Inventing a new usage (a Batmobile-only state)
is not decodable from the shipped data, and inventing one is what the brief forbids.

## Files written

- `Tools/scripts/t_fx3b_exhaust.py` (`--write` / `--check`; the check re-decodes the module,
  re-scans `FX_TABLE.jsonl` and rebuilds the `.md` byte for byte)
- `Working/Translation/T_FX3B.md` (181 lines)
- `Working/Translation/T_FX3B.json`
- `tmp/freebuff/reports/T-FX3b.md` (this report)

No existing `Builds/bm-*` tree was touched; nothing was written to a game install; no game was
launched or attached.

## Commands and output (verbatim)

```
$ uv run python Tools/scripts/t_fx3b_exhaust.py --write; echo "WRITE_EXIT=$?"
wrote Working/Translation/T_FX3B.json and Working/Translation/T_FX3B.md (181 lines)
answer YES; module instances 1, types 6, fields 2, offsets 3; fleet 43 effects / 296 containers
WRITE_EXIT=0

$ uv run python Tools/scripts/t_fx3b_exhaust.py --check; echo "CHECK_EXIT=$?"
PASS Working/Translation/T_FX3B.md re-derives byte for byte from the sources
PASS a carrier exists (answer YES)
PASS module decodes: 1 instances
PASS fleet: 43 exhaust/boost effects in 296 containers
PASS a helicopter boost carrier is in the fleet table
PASS a boat boost carrier is in the fleet table
PASS nitro trigger carriers decoded: {'heat_boost': 145, 'nitro_boost': 145, 'nitro_boost_upgraded': 145, 'turbo_jump': 145, 'turbo_jump_upgraded': 145}
PASS: T-FX3b 0 failure(s), answer YES
CHECK_EXIT=0
```

The ADF decode used to choose the offsets printed above:

```
$ uv run python -c "import sys;sys.path.insert(0,'Tools/scripts');import jc3adf,json; ... "
600100251 {"code": 1, "size": 48, "align": 8, "name": "EffectAttachments", ... "members": [
  {"name": "all_effects", "type": 459717905, "size": 8, "offset": 0},
  {"name": "part_effects", "type": 468153434, "size": 8, "offset": 16},
  {"name": "usage_effects", "type": 3128759027, "size": 8, "offset": 32}]}
3213548423 = EffectAttachment, size 32: deform_point offset 0, effect offset 16
```

The `world` probe (negative result that the report relies on):

```
$ uv run python -c "... e=json.load(open('Working/Effects/bm_fx_edits.json')) ..."
base.epe Builds/bm-005/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe True
bytes 124488
exhaust_upgrade_nitrous2 oldlen 82 found -1
exhaust_upgrade_nitrous oldlen 81 found -1
has pos -1 has rot -1
```

## UNKNOWNs

1. **Struct offset of `world` inside the `SAttachedEffect` RTPC object.** Tried: `jc3adf.Adf` on
   the `.epe` (rejected: magic `0x43505452` = `RTPC`, not ADF); byte search of the edit's own
   matrix text (`-0.4101563`, `-4.371139E-08`) inside the base `.epe` (both absent, so the matrix
   is binary floats). Where it would be found: an RTPC property-level decode of that node (node
   record offset + property record offset, layout labelled in `Tools/scripts/decode_depth7.py`);
   no current script resolves per-object members.
2. **Whether a usage can be raised by a script/condition outside the arcade nitro fields.** 85 of
   the 155 usage values have no decoded name (`USAGES.json` `epe.name_provenance.UNKNOWN`), so the
   semantics of most usages are unknown. Search that would settle it: a corpus sweep for the
   trigger member that is not `usage` (e.g. the `SValueDrivenEffectUsage` node's condition field)
   across all 232 detail files.
3. **Whether the `world` matrix alone makes the flame follow the moving exhaust point** - B-08's
   Q-1 #5 records the row-2 axis semantics as undecoded; nothing in this task tested that.

## COMPROMISES

None. This task changed no build output; it only decoded JC3 data and reported it.

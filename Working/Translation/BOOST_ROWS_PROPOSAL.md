# BOOST_ROWS_PROPOSAL - BmAK afterburner values that have no translation row

Proposals only: nothing here edits `Working/Translation/T_ROWS.jsonl` (198 rows, read-only). The
JSON below is the machine-checked form; `python Tools/scripts/t_boost_rows.py --check` re-reads every
cited BmAK source line, re-runs every conversion and verifies that the proposal covers every value
`Working/Translation/BOOST_COVERAGE.md` lists as uncovered.

Decision rule, applied per value: the donor's nitro block (`Research/JC3Grab/USAGES.md` section 6,
line 552) carries **torque_multiplier, grip_multiplier, push_force, boost_blend_time,
extra_top_speed** and nothing else. A BmAK value gets a **map** row only when a JC3 member exists
whose meaning can carry it; otherwise it gets an **omit** row with the reason. Two values (duration,
recharge) have no member in that block but do have JC3 nitro-system members in `VehicleMisc`
(`full_nitro_use_time`, `full_nitro_refill_time`); they are mapped with the semantic difference
stated. The base speed cap has such a member (`official_top_speed`) but it is already claimed by
T-E5's signed-off 336.4 km/h, so it is an explicit conflict-omit rather than a second write.

```json
{
  "schema": 1,
  "card": "BOOST-COVERAGE",
  "generated": "2026-11-05",
  "t_rows": "Working/Translation/T_ROWS.jsonl",
  "t_rows_edited": false,
  "conversion_constants": {
    "cu_per_s_to_kmh": 0.036,
    "s_to_s": 1.0,
    "cu_per_s2_to_kmh_per_s": 0.036
  },
  "donor_block": {
    "path": "Research/JC3Grab/USAGES.md",
    "line": 552,
    "needle": "`arcade.nitro_boost`: torque x2, grip x2, `push_force` 15000, `boost_blend_time` 0.2 s, `extra_top_speed` +40 km/h",
    "members": ["torque", "grip", "push_force", "boost_blend_time", "extra_top_speed"]
  },
  "proposals": [
    {
      "id": "P-B5",
      "bmak_field": "BoostDuration",
      "bmak_value": 2.0,
      "bmak_unit": "s",
      "bmak_source": {"path": "Working/HUD/CLUSTER.md", "line": 50, "needle": "| `BoostDuration` | float | 664 | 2.0 |"},
      "decision": "map",
      "jc3_field": ["VehicleMisc.full_nitro_use_time", "VehicleMisc.full_nitro_use_time_upgraded"],
      "jc3_source": {"path": "Working/Translation/current.json", "line": 29860, "needle": "\"full_nitro_use_time\": 4,"},
      "jc3_domain_source": {"path": "Research/JC3Grab/DRIVE_CARRIERS.md", "line": 301, "needle": "| `full_nitro_use_time` | `VehicleMisc` | 4 (4 .. 4; n=232) |"},
      "converted_value": 2.0,
      "conversion_factor": 1.0,
      "conversion_rule": "BmAK seconds -> JC3 seconds, 1 s = 1 s; 2.0 s written unchanged to both use-time members",
      "semantics": "BmAK runs a fixed 2 s burst; JC3 drains a meter over full_nitro_use_time. The number transfers, the mechanic does not. Both the base and the _upgraded member get 2.0 s because BmAK has one BoostDuration and no upgraded tier (P-B11); leaving _upgraded at the donor 8 s would make the upgraded nitro six times longer than the only BmAK duration.",
      "note": "USAGES.md section 6's arcade.nitro_boost block has no duration member; this row uses the JC3 nitro system's own timing member instead, present on all 232 vehicles.",
      "gate": "Q-2 A2: measure boost active time; expect 2.0 s, not the donor 4/8 s"
    },
    {
      "id": "P-B6",
      "bmak_field": "BoostCooldown",
      "bmak_value": 12.0,
      "bmak_unit": "s",
      "bmak_source": {"path": "Working/HUD/CLUSTER.md", "line": 51, "needle": "| `BoostCooldown` | float | 668 | 12.0 |"},
      "decision": "map",
      "jc3_field": ["VehicleMisc.full_nitro_refill_time"],
      "jc3_source": {"path": "Working/Translation/current.json", "line": 29859, "needle": "\"full_nitro_refill_time\": 2,"},
      "jc3_domain_source": {"path": "Research/JC3Grab/DRIVE_CARRIERS.md", "line": 303, "needle": "| `full_nitro_refill_time` | `VehicleMisc` | 2 (2 .. 2; n=232) |"},
      "converted_value": 12.0,
      "conversion_factor": 1.0,
      "conversion_rule": "BmAK cooldown seconds -> JC3 refill seconds, 1 s = 1 s; 12.0 s written unchanged",
      "semantics": "BmAK waits 12 s after a burst before boosting again; JC3 refills a meter over full_nitro_refill_time. Both are the time from boost-off to boost-available; the meter shape differs, so the number is a deliberate equivalence, not a decoded one. nitro_refill_min_speed_kph (20 km/h donor default) has no BmAK source and is left alone.",
      "note": "Only tier 0 of the 3-slot BoostCooldown InlineArray (668/672/676) has a decoded default (12 s); slots 1/2 are UNKNOWN (BOOST_COVERAGE.md section 7.1).",
      "gate": "Q-2 A2: boost-off to boost-available measured at ~12 s"
    },
    {
      "id": "P-B7",
      "bmak_field": "FakeExtaSpeedDecel",
      "bmak_value": 2000.0,
      "bmak_unit": "cu/s^2",
      "bmak_source": {"path": "Research/BatmobileGrab/CLASS_DEFAULTS.md", "line": 267, "needle": "`FakeExtaSpeedDecel` (RVehicleBatmobileBase) | FloatProperty | 2000.0"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": 72.0,
      "converted_unit": "km/h/s",
      "conversion_factor": 0.036,
      "conversion_rule": "2000 cu/s^2 x 0.036 km/h per cu = 72 km/h/s; recorded, not written",
      "reason": "The donor nitro block has no decel member (only boost_blend_time 0.2 s), and JC3 ends boost by blending torque back rather than by a stated decel rate. Mapping 2000 cu/s^2 onto a blend time needs a velocity step the files do not give (UNKNOWN), so the value stays unmodified. The converted figure 72 km/h/s is kept so a future blend-time derivation has its input.",
      "evidence": [{"path": "Research/JC3Grab/USAGES.md", "line": 552, "needle": "boost_blend_time"}]
    },
    {
      "id": "P-B8",
      "bmak_field": "BoostDurationDonut",
      "bmak_value": 6.0,
      "bmak_unit": "s",
      "bmak_source": {"path": "Working/HUD/CLUSTER.md", "line": 55, "needle": "| `BoostDurationDonut` | float | 688 | 6.0 |"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": 6.0,
      "converted_unit": "s",
      "conversion_factor": 1.0,
      "conversion_rule": "6.0 s stays 6.0 s; recorded, not written",
      "reason": "A donut/heat-boost mode has no JC3 carrier: the donor's separate heat_boost block is kept at Serpente defaults with no BmAK source (T-B4) and no row may add one. Writing 6 s into full_nitro_use_time (P-B5) would make every boost 6 s, contradicting BoostDuration 2 s; a second duration member does not exist.",
      "evidence": [{"row_id": "T-B4", "needle": "no BmAK source exists"}]
    },
    {
      "id": "P-B9",
      "bmak_field": "SVehicle.MaxSpeed",
      "bmak_value": 4000.0,
      "bmak_unit": "cu",
      "bmak_source": {"path": "Research/BatmobileGrab/CLASS_DEFAULTS.md", "line": 163, "needle": "`MaxSpeed` (SVehicle) | FloatProperty | 4000.0"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": 144.0,
      "converted_unit": "km/h",
      "conversion_factor": 0.036,
      "conversion_rule": "4000 cu x 0.036 km/h per cu = 144 km/h; recorded, not written",
      "reason": "A JC3 field exists (VehicleMisc.official_top_speed) but it is already owned by T-E5's signed-off 336.4 km/h (wiki 209 mph, the mod's lore target); writing 144 would overwrite that decision. The 4000 cu value is the engine's base cap, not a boost value: BOOST_COVERAGE.md keeps it out of the boost translation, and the T-E5 comment already flags Transmission.top_speed 437 as the boosted ceiling to re-derive once T-B1 is settled.",
      "evidence": [
        {"path": "Working/Translation/current.json", "line": 29866, "needle": "\"official_top_speed\": 336.399994,"},
        {"row_id": "T-E5", "needle": "336.4"}
      ]
    },
    {
      "id": "P-B10",
      "bmak_field": "RVehicleBatmobileBase.InfiniteBoost",
      "bmak_value": false,
      "bmak_unit": "bool bit (mask 536870912)",
      "bmak_source": {"path": "Research/BatmobileGrab/SAMPLER_FIELDS2.md", "line": 96, "needle": "`RVehicleBatmobileBase.InfiniteBoost` | 4568 (0x11d8) | `bit` | 536870912"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": false,
      "converted_unit": "bool",
      "conversion_factor": null,
      "conversion_rule": "boolean, no conversion; the CDO default is false (bit 29 clear in the class default word, T-B2)",
      "reason": "The donated JC3 nitro is a finite meter: USAGES.md section 6 lists no infinite/unlimited member and the build's own fields are full_nitro_use_time/refill_time, so there is nothing to set false. A flag with no carrier is an explicit omission, not a translation; T-B2 already records the BmAK value as false.",
      "evidence": [
        {"path": "Research/JC3Grab/USAGES.md", "line": 552, "needle": "arcade.nitro_boost"},
        {"row_id": "T-B2", "needle": "InfiniteBoost"}
      ]
    },
    {
      "id": "P-B11",
      "bmak_field": "BoostCooldownUpgradeLevel",
      "bmak_value": null,
      "bmak_unit": "int (no CDO default)",
      "bmak_source": {"path": "Working/HUD/CLUSTER.md", "line": 52, "needle": "| `BoostCooldownUpgradeLevel` | int | 680 | None |"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": null,
      "converted_unit": "int",
      "conversion_factor": null,
      "conversion_rule": "no value to convert (None); the field only selects which cooldown tier applies",
      "reason": "No upgraded nitro tiers are built (user decision recorded for the build batches; T-B4 keeps the donor block only), and the donor block has no tier selector. With one BoostCooldown value written (P-B6) and no upgrade path, the level has nothing to select; writing an int would invent a tier model.",
      "evidence": [
        {"path": "Research/JC3Grab/USAGES.md", "line": 552, "needle": "nitro_boost"},
        {"row_id": "T-B4", "needle": "Serpente defaults"}
      ]
    },
    {
      "id": "P-B12",
      "bmak_field": "CurrentBoostTimer",
      "bmak_value": 1.0,
      "bmak_unit": "s (initial)",
      "bmak_source": {"path": "Working/HUD/CLUSTER.md", "line": 53, "needle": "| `CurrentBoostTimer` | float | 808 | 1.0 |"},
      "decision": "omit",
      "jc3_field": [],
      "converted_value": 1.0,
      "converted_unit": "s",
      "conversion_factor": 1.0,
      "conversion_rule": "1.0 s initial value, no conversion; recorded, not written",
      "reason": "This is the live countdown the sim writes while a burst runs, not a tunable: the CDO's 1.0 is the pre-boot value and the duration it counts is BoostDuration (P-B5). No JC3 member carries a per-frame timer, and writing it would set a state that the engine overwrites.",
      "evidence": [
        {"path": "Research/JC3Grab/USAGES.md", "line": 552, "needle": "boost_blend_time"}
      ]
    }
  ]
}
```

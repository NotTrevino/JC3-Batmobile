STATUS: DONE — BmAK's run-time colour for built light entry 11 is the class-default white `[255, 255, 255, 0]`; the built `0.6039, 0.6039, 0.9529` is JC3's own graph-object colour, so as a BmAK copy it is wrong and the row to change is `T-L17` (not edited). `--check` green: 26/26, exit 0.

## Files

| file | what |
|---|---|
| `Research/BatmobileGrab/LIGHT_ENTRY11.md` | 127 lines: precedence rule with the live byte reads, built side, correction table, UNKNOWNs |
| `Tools/scripts/t_light_entry11.py` | new, `--write` / `--check`; imports `grab_lights.py`'s own chain resolver and re-reads the shipped `.upk`s |
| `tmp/freebuff/reports/light-entry-11.md` | this report |

Not edited: `LIGHTS.md`, `T_ROWS.jsonl`, `bm_lightrig.json`, `t14_lights.json`, any build tree.

## Verbatim commands

```
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_light_entry11.py --write
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 python Tools/scripts/t_light_entry11.py --check
```

`--write` -> exit 0, 26/26 oracles, doc written. `--check` -> exit 0, doc byte-identical.

## Precedence rule, with the bytes

A cooked component serialises only what differs from its archetype, and a tag carries
`(type, offset, value)` with no name. `grab_lights.py` keeps **the first link that carried each
field**: component tags → archetype (export record word 6) → `Default__<class>` in Engine/BmGame.upk →
native default (no file). `LIGHTS.md` states the same rule.

Live read of `Playable_Batmobile_SF.upk`, export **5371** (`Batmobile.SpotLightComponent`), the single
component of `BattleModeSpotLight` / `VEHLT_BattleModeLight`:

| link | bytes | carries LightColor? |
|---|---|---|
| component 5371 | 12 tags; word 6 (archetype) = **0** | **no** — no tag maps to the LightColor offset |
| archetype | word 6 = 0 → inherits straight from the class default | n/a |
| `Default__LightComponent` (Engine.upk) | `LightColor = [255, 255, 255, 0]` (FColor read B,G,R,A) | **yes** |

The component does serialise the 7 fields around the colour (`Brightness 0.0`, `Radius 4500`,
`InnerConeAngle 5`, `OuterConeAngle 15`, `FalloffExponent 1`, both cast flags false); the chain
reports no gap. So the BmAK lamp's colour is white — 1.0, 1.0, 1.0 in JC3's 0..1 form.

## The built value and the correction

Entry 11 (`origin: graph-object (T-L17)`) takes R/G/B from the JC3 graph object
`Front_Secondary_Head` (0.6039 / 0.6039 / 0.9529, preset_id 3189390601). That is a JC3-authored
preset colour, not a BmAK value. `T-L17`'s `now` cell already prints `LightColor 255,255,255,0`,
`B 0.0`, `cone 5.0/15.0`, `R 4500.0`; the build implements the proposal instead.

| field | built | BmAK (correct) |
|---|---|---|
| colour | 0.6039, 0.6039, 0.9529 | **1.0, 1.0, 1.0** (`[255,255,255,0]`) |
| range | 10.0 | 4500.0 |
| angle | 60.0 | 15.0 |

Row to change: **`T-L17`** (`dispo: next`). Range/angle follow the same authorship difference and are
listed so the change is not half-made; whether to keep BmAK's 4500/15 or JC3's 10/60 is a fidelity
decision, not a byte question. Nothing applied.

## UNKNOWNs

- Whether a script/entity-graph override sets the colour at run time: the shipped default is white;
  an override is not decodable here and no game was launched (test ban).
- Whether T-L17 should be BmAK-faithful at all — the row may intend "give the JC3 preset a module row
  that keeps JC3's own look". In that reading the built colour is a deliberate art choice, but it is
  still not the BmAK value the row prints.
- Brightness semantics: BmAK `0.0` has no 1:1 bridge to JC3 `multiplier` / `min_luminosity`; that
  bridge is T-18's.
- No `.epe`, module or install was written; only the two `.upk`s and repo JSONs/MD were read.

## Labels

Decoded: the live package reads, `LIGHTS.json` / `LIGHTS.md` / `bm_lightrig.json` / `t14_lights.json`
/ ledger cells. Derived: the run-time conclusion (white), the 0..1 form, the change list. UNKNOWN: the
list above.

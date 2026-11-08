STATUS: done - the 30 BmAK battle-mode events are listed and each has a nearest JC3 vehicle event that a donor module really references (GUID + bank/ordinal + role); no row claims a trigger, because no module field references a battle-mode event.

# T-MD14 - battle-mode audio events and the nearest JC3 vehicle event

The card was blocked because the donor has no mode-switch event, so the 30 battle-mode
events have no place on a one-variant hybrid.  This pass does the part the brief asks
for: enumerate the 30 events, and for each name the nearest JC3 vehicle event that the
donor `.epe` already fires, with its Wwise GUID, bank/ordinal and function.  Static
only: no game process started or attached, no install, no git.

## What was decided

| family | BmAK events | nearest JC3 event | GUID | bank/ordinal | function | label |
|---|---:|---|---|---|---|---|
| engine bed | 1 (`Play_BattlemodeEngine`) | `engine_running_sound` | `905be2e5-2544-8045-a10b-6034fd27ff11` | vehicles/146 (tune 5) | engine | **decoded** |
| deploy (In / InRev) | 13 | `DoorOpeningStart` | `500e1421-3174-f54c-8b9a-c8c0c74a5baa` | vehicles/84 (tune 154) | mechanical open | **decoded** |
| retract (Out / OutRev) | 16 | `DoorClosingEnd` | `f58a18f7-719a-c64a-8e71-8da234d84ef9` | vehicles/246 (tune 223) | mechanical close | **decoded** |

All three are `SAttachedEffect` objects the donor graph names (`roles` in
`Research/JC3Grab/JC3_AUDIO_EVENTS.json`), so each *pairing* meets the brief's bar
(hash + module).  The *trigger* does not: the built bank manifest has 0 battle-mode
references, and no file under `E:/Modding/_gamedata/JC3grab/entities` contains the
string `Play_BattleMode` (0 files), so nothing is claimed to fire.

Boost, horn and impact were deliberately not used: `exhaust_upgrade_nitrous` is a nitro
layer, the horn ships on no Batmobile event (AUDIO_FEATURES `horn` group = 0 events), and
the impact-adjacent roles are damage-break events, not transformations.

## Files written

- `Tools/scripts/t_md14.py` - new, `--write` / `--check`; the check re-reads
  `AUDIO_FEATURES.json`, `JC3_AUDIO_EVENTS.json`, `bm_bank_manifest.json` and
  `T12_AUDIO.md`, re-runs six oracles and byte-compares the generated document.
- `Working/Translation/T_MD14_EVENTS.md` - the 30-row table, the family rationale, the
  manifest census, the oracles and the UNKNOWN list.
- `Working/Translation/T_MD14_EVENTS.json` - the same data as a machine record.
- This report.  `Working/Translation/T_ROWS.jsonl` was **not** touched.

## Commands and output

```
$ uv run python Tools/scripts/t_md14.py --write && uv run python Tools/scripts/t_md14.py --check; echo "check exit=$?"
wrote Working/Translation/T_MD14_EVENTS.md (113 lines) and .json
battle events 30, wems 75, packages 4, manifest battle refs 0
rows decoded 30 / 30
oracles 6/6
CHECK OK: 6 oracles, 30 battle events, 30/30 pairings decoded, 0 triggers
check exit=0
```

```
$ grep -rl "Play_BattleMode" E:/Modding/_gamedata/JC3grab/entities | wc -l
count=0
```

Schema probes (used to fix the reader against the real files):

```
FEATURES keys: ['schema', 'generated_by', 'inputs', 'method', 'groups', 'events', 'media', 'decode_errors', 'rtpc_params', 'missing', 'summary']
groups: [('sonar', {'name': 'sonar', 'rows': 18, 'events': 6, 'wems': 0, ...}), ('battle-mode', {'name': 'battle-mode', 'rows': 120, 'events': 30, 'wems': 75, 'rtpc_params': 2, 'containers': 2, 'note': ''}) ...]
event0: {"package": "Playable_BatmobileFunhouse_SF", "name": "Play_Batmobile_Dodge", "group": "movement", "event_id_hex": "0x2BD57CA9", "status": "resolved", "bank": "BML_Batmobile", "wems": [...]}
JC3 donor ev0: {"banks": [{"bank": "vehicles", "bytes": 143, "ordinal": 43}], "guid": "249a34b0-...", "roles": [], "samples": null, "tune": {"bank": "vehicles", "index": 230, ...}}
named: 23 count events: 45
MANIFEST keys: ['schema', 'card', 'generator', 'inputs', 'bank', 'written', 'resolved', 'fmod_guids', 'events', 'installer', 'summary', 'slots']
battle refs: 0
slots type/len: list 5
summary: {"mapped_rows": 5, "slots_written": 5, "banks": 2, "sample_count": 1877, ...}
```

T-16's row that blocks the card, read from `Working/Translation/T12_AUDIO.md`:

```
| W-08 | AUD-4 | `battle mode` | `Play_BattleMode_InRev_A` (3 WEMs) ... `Play_BattlemodeEngine` (3 WEMs) | `blocked` | — | — | blocked: D-2 - two variants would give the battle car its own `engine_running_sound`; one hybrid car has no mode-switch event to hook |
```

## Oracles (all PASS, `--check` exit 0)

| oracle | what would make it fail |
|---|---|
| O1-thirty-events | the 120 source rows no longer collapse to 30 unique names, or the packages change |
| O2-media-census | the per-event WEM lists stop adding up to the group's own 75 / 30 census |
| O3-jc3-targets-decoded | any of the three JC3 events loses its GUID, bank/ordinal, tune or `.epe` role |
| O4-no-trigger | the manifest gains a battle-mode reference, or W-08 stops being `blocked` for 'no mode-switch event' |
| O5-every-row-labelled | a row loses its label, or a row starts claiming a trigger |
| O6-md-recomputed | the committed `.md` diverges from what the check rebuilds |

## UNKNOWNs

- **Which BmAK event the battle-mode control would play.** No decoded file maps an input
  action to an event id; the 30 names are the media, not the trigger.  It would be found
  in the BmAK blueprint/`AkComponent` graph, which the grab does not include.
- **Whether the JC3 door pair is actually audible on the Batmobile.** It is a function
  match (the only decoded mechanical open/close a donor vehicle module fires), not an
  audition: G2-24 §5 shows the bank stores no event->tune->sample edge, and the Batmobile
  canopy is a different mechanism from a car door.
- **A per-mode audio graph.** JC3 ships one variant graph; giving battle mode its own bed
  needs a second variant (D-2), which this card does not decide.

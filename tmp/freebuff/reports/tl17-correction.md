STATUS: done — T-L17's colour must change from the built `0.6039/0.6039/0.9529` to **`1.000/1.000/1.000`**, the intensity must **not** change, and the proposed row edit is in `Working/Translation/TL17_PROPOSAL.md` as JSON. The row, `t14_lights.json` and the build were not edited.

## The decision

| question | answer | bytes |
|---|---|---|
| what colour does BmAK run? | class-default white `LightColor [255, 255, 255, 0]` | `LIGHTS.json` vehicles[0].entries[9].components[0].colour, source `class default: Default__LightComponent (Engine.upk)`; `LIGHT_ENTRY11.md:3` |
| what does the JC3 field want? | **0..1 floats** per channel (`diffuse.R/G/B`, typed float, 3,217/3,217 entries; no shipped value above 1.0) | `LIGHT_SYSTEM.md:38-40`, §2 census |
| how is 255 handled? | plain `/ 255`, no gamma | `LIGHT_SYSTEM.md:240` emits `160 → 0.627451` (=160/255 exactly), `180 → 0.705882`, `255 → 1.0` |
| white in JC3 terms | `1.000, 1.000, 1.000` | derived: 255/255 |
| must the intensity change? | **no** — keep `multiplier 1.0`, `min_luminosity 0.0` | see below |

**Why the intensity stays.** BmAK's `Brightness` on this lamp is `0.0` and it is the *component's own* serialised value (`field_sources.Brightness = "component"` - a different link in the chain than the colour, which falls through to the CDO). It means "ships dark until a script raises it", not "scale everything by zero": the radius/cone are authored (4500 / 5..15). JC3's `multiplier` census is `1`×2188, `2`×792, `0.5`×174, `0.7`×30, `3`×12, `5`×12, `0.3`×6, `0.4`×3 - **0 of 3,217 entries use 0**, and `min_luminosity` is 0 on all of them. Writing 0 would delete the lamp, not reproduce BmAK. No file decodes a `Brightness → multiplier` bridge (that is T-18's), and the rig is not even monotone: T-L15/L16 ship `B 1.0`, T-L18/L19 `B 5.0`, this one `B 0.0`. So the intensity is kept and relabelled *JC3 graph value, not a BmAK copy* rather than "converted".

**Proposed row edit** (`T14_LIGHTS.md:64`, `proposed` cell only):
`diffuse 0.604,0.604,0.953 r 10.0 ang 60.0` → `diffuse 1.000,1.000,1.000 r 10.0 ang 60.0`.
`range`/`angle`/`near_cap` are listed as `out_of_scope` in the JSON (their units are UNKNOWN in `LIGHT_SYSTEM.md:289`), not changed.

**One finding worth the operator's attention:** `t14_lights.json` row `T-L17` **already** carries `proposal_diffuse: [1.0, 1.0, 1.0]` - it is only the `.md` cell that still prints the graph colour. The edit therefore makes the two T-14 records agree; it is not a new decision. The build entry 11 still carries `0.6039/0.6039/0.9529` (= `154 154 243`), so applying the row alone does not change the lamp - a rebuild is required and was deliberately out of scope.

## Files written

| file | what |
|---|---|
| `Tools/scripts/tl17_proposal.py` | new tool, `--write` / `--check`; reads LIGHTS.json, LIGHT_ENTRY11.md, LIGHT_SYSTEM.md, t14_lights.json, bm_lightrig.json, T14_LIGHTS.md; recomputes the conversion and the census; emits the proposal and asserts the row/build are untouched |
| `Working/Translation/TL17_PROPOSAL.md` | 10,557 bytes: the edit as one JSON block (row, cells from/to, five field records, out-of-scope list, evidence, not-edited list) + the unit proof, the intensity argument, the current-state table, UNKNOWNs |
| `tmp/freebuff/reports/tl17-correction.md` | this report |

Not edited: `Working/Translation/T14_LIGHTS.md`, `Working/Translation/t14_lights.json`, `Working/Lights/bm_lightrig.json`, every `Builds/` tree. No rebuild, no install, no game.

## Commands run (verbatim)

```
cd /e/Modding/JC3-Batmobile && set -o pipefail && echo "=== write ===" && python Tools/scripts/tl17_proposal.py --write; echo "write exit=$?"; echo "=== check ===" && python Tools/scripts/tl17_proposal.py --check; echo "check exit=$?"
```
```
=== write ===
wrote Working\Translation\TL17_PROPOSAL.md (10557 bytes)
colour [255, 255, 255] / 255 -> [1.0, 1.0, 1.0]; intensity kept at multiplier 1.0
write exit=0
=== check ===
PASS LIGHTS.json entry 9 LightColor is [255, 255, 255, 0]
PASS that colour's recorded source is the class default
PASS Brightness is 0.0 and is the component's own serialised value
PASS the build (entry 11) still carries the graph colour 0.6039/0.6039/0.9529
PASS t14_lights.json already proposes [1.0, 1.0, 1.0]
PASS 255 / 255 = 1.0 on all three channels
PASS LIGHT_SYSTEM's own recipe is LightColor/255 (160 -> 0.627451)
PASS no converted channel exceeds 1.0
PASS multiplier stays 1.0: 0 is outside the 0.3..5 shipped census
PASS the multiplier census parsed and covers all 3,217 entries
PASS min_luminosity is 0 on all 3,217 shipped entries
PASS the proposal leaves the intensity alone
PASS T14_LIGHTS.md:64 holds the old cell (or the applied one) - not edited
PASS the row's 'now' cell is unchanged (BmAK white / B 0.0)
PASS exactly one of the two proposed-cell texts is present
PASS Working\Translation\TL17_PROPOSAL.md matches a fresh render (every value re-read)
PASS the JSON edit carries 1.0 as the corrected channel value
PASS the JSON edit records that the intensity does not change
PASS the edit shows both the from and the to cell

check: all assertions passed
check exit=0
```

The JSON block was also parsed independently out of the written file:

```
cd /e/Modding/JC3-Batmobile && python - <<'PY'
import json, re
body = open("Working/Translation/TL17_PROPOSAL.md", encoding="utf-8").read()
blocks = re.findall(r"```json\n(.*?)\n```", body, re.S)
print("json blocks:", len(blocks))
d = json.loads(blocks[0])
print("row:", d["row"], "| status:", d["status"])
print("from:", d["cells"]["proposed"]["from"])
print("to:  ", d["cells"]["proposed"]["to"])
print("intensity_changes:", d["intensity_changes"])
for fl in d["fields"]:
    print(f"  {fl['field']:16} built={fl['built']!r:24} correct={fl['correct']!r:10} {fl['action']} ({fl['class']})")
print("out_of_scope:", [o["field"] for o in d["out_of_scope"]])
print("evidence lines:", len(d["evidence"]))
PY
```
```
json blocks: 1
row: T-L17 | status: proposed - not applied
from: diffuse 0.604,0.604,0.953 r 10.0 ang 60.0
to:   diffuse 1.000,1.000,1.000 r 10.0 ang 60.0
intensity_changes: False
  diffuse.R        built=0.6039                   correct=1.0        change (derived)
  diffuse.G        built=0.6039                   correct=1.0        change (derived)
  diffuse.B        built=0.9529                   correct=1.0        change (derived)
  multiplier       built=1.0                      correct=1.0        keep (UNKNOWN (no decoded bridge))
  min_luminosity   built=0.0                      correct=0.0        keep (derived)
out_of_scope: ['range', 'angle', 'near_cap']
evidence lines: 5
```

Note on the first run: `--check` caught a real bug in my own census parse (a `startswith("| `multiplier` |")`
selector matched the *type* table, which has no `value x count` tokens, so the list came back empty and
`min()` raised). Fixed by selecting the census row on the `value x count` pattern, plus an assertion that
the parse is non-empty and totals 3,217, so a vacuous pass is impossible.

## Labels

- **Decoded:** the `LightColor` triple and its class-default source; `Brightness 0.0` + its `component`
  source; the graph object's `diffuse`/`multiplier`/`near_cap`; `t14_lights.json`'s `proposal_diffuse`;
  both `.md` cells; the file census lines (`LIGHT_SYSTEM.md:38-40,78,79,240,289`); build entry 11's members.
- **Derived:** 255/255 = 1.0; 160/255 = 0.627451 as the proof that the scale is a plain /255; the
  "0 is outside the shipped 0.3..5 domain" argument; the decision that intensity does not move.
- **UNKNOWN:** the three items below.

## UNKNOWNs

1. **`Brightness` semantics.** 0.0 here vs 1.0/5.0 elsewhere, with no decoded bridge to JC3's
   `multiplier`/`min_luminosity`. Would need a `BatmanAK.exe` read of the light update path or a Q-1 #7
   probe with the battle lamp scripted on. Not guessed; the value is left where it is and labelled.
2. **Whether a preset overrides entry members at run time.** `LIGHT_SYSTEM.md` §3 proves presets do not
   *fix* the numbers, but override semantics are code. This entry's `preset_id` is the graph's own hash and
   no module row references it (T-LG2).
3. **Whether a script recolours/brightens the component at run time.** `LIGHT_ENTRY11.md` records the same
   gap. Nothing was launched (test ban), so the white is the shipped default, not an observation.

## COMPROMISES

None. No value was guessed, no row or build edited, no install, no launch. The one deliberate
non-conversion (intensity) is stated with its reason and labelled UNKNOWN rather than filled.

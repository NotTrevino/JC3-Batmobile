# B-22 droop / bump / rebound length: the members exist on the BmAK side only

**Task.** Starting from the `B-22` row (`GRAB_BACKLOG.md:1534`, tracker `:1875`) and
`suspension-unit-bridge.md` §7/§9 (`:113-114`, `:157-158`), which name `BMRearWheelMaxDroop` 100 cm and
`SuspensionTravelUp` 30 cm, search `Research/` and `Working/` for any member, key or table field carrying a
**droop, bump or rebound length**, and record each hit as path + line. Structured hits:
`Working/Prep/b22_droop_members.json`.

**Result: 31 hit records — 24 FOUND, 4 NOT_FOUND, 3 UNKNOWN.**

* **A droop member exists on the BmAK side, and only there.** `BMRearWheelMaxDroop` is declared at
  `RVehicleSimBatmobile` offset **0x318** (`OFFSETS.md:503`), present in the SDK dump, the chain table and
  the mechanics names. There is a matching front member at **0x314**.
* **No JC3 member, key or table field carries a droop, bump or rebound *length*.** The 166-vehicle census
  states the absence itself (`B-22.md:32`); the only length-adjacent keys are
  `front/rear.max_length_offset` and `front/rear.min_length`, both `0 .. 0` across all 167 samples
  (`VOCABULARY.md:1154-1170`).
* **JC3's "rebound" is a damping term, not a travel.** `BMWheelSuspensionDamping` maps to the
  compression/relaxation *pair* (`SUSPENSION_BRIDGE.md:116`) — the only JC3 key in the corpus that splits
  bump from rebound, and it carries no length.
* **One number needs adjudication, not an edit:** the same offset reads **40.0** in the chase probe
  (`chase-06.md:84-85`) while the B-22 card carries **100 cm** from `TYRES_PACKAGE.md`. Both are recorded
  below; neither file was changed.

---

## 1. Searches run

| term | scope | outcome |
|---|---|---|
| `\bdroop\b` (word) | `Research/` | 29 matches → 12 distinct files; all hits either BmAK members, ledger/prose mentions, or the stated absence |
| `\brebound\b` (word) | `Research/` | 5 matches → 3 files; no length member anywhere |
| `bump.?stop` / `bump_stop` / `bumpstop` | `Research/` | 2 matches, both prose (`B-22.md:32`, `B-23.md:46`) |
| `\bdroop\b|\brebound\b|bump.?stop` | `Working/` | **truncated** — 18 of an unknown total before the 10 s search cap |
| `max_length_offset|min_length` | `Research/JC3Grab/VOCABULARY.md` | 8 rows, all zero-valued |
| `BMRearWheelMaxDroop` / `BMFrontWheelMaxDroop` | `Research/`, `Working/` | 9 member hits |

Bare `bump` was deliberately **not** used as a term: it floods on `bumper` (`BOX_FLAGS.json` has 60+ bone
names such as `Bumper_Front`), which carries no suspension meaning. The bound forms above are the term.

## 2. Hits (path:line, verdict)

### 2.1 The BmAK droop members — FOUND

| query | path:line | quoted |
|---|---|---|
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/OFFSETS.md:503` | `\| RVehicleSimBatmobile \| 0x0318 \| FloatProperty \| - \| 4 \| named-sdk \| BMRearWheelMaxDroop \| …` |
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/BMSDK_OFFSETS.json:24401` | `"member": "BMRearWheelMaxDroop",` |
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/MECHANICS_NAMES.json:1610` | `"decl": "public unsafe float BMRearWheelMaxDroop",` |
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/CHAIN.json:11101` | `"name": "RVehicleSimBatmobile.BMRearWheelMaxDroop",` |
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/DRIVE_MODES.json:69` | `"BMRearWheelMaxDroop": {` |
| `BMRearWheelMaxDroop` | `Research/BatmobileGrab/chase/chase-06.md:85` | `0x318 BMRearWheelMaxDroop                40.0` |
| `BMFrontWheelMaxDroop` | `Research/BatmobileGrab/BMSDK_OFFSETS.json:24394` | `"member": "BMFrontWheelMaxDroop",` |
| `BMFrontWheelMaxDroop` | `Research/BatmobileGrab/chase/chase-06.md:84` | `0x314 BMFrontWheelMaxDroop               40.0` |
| `droop` | `Research/BatmobileGrab/CONFIG.md:1080` | `\| suspension / droop / travel \| \`suspension\|droop\|\btravel\b\` \| 2 \| \`BmGame/Config/BmEngine.ini:555 Package=Ww_BML_Suspension\`…` |
| `droop` | `Research/BatmobileGrab/COVERAGE.md:14` | `\| \`T-S6\` \| 13 \| suspension rate/bias/droop \|` |

Two of these are worth reading closely. `CONFIG.md:1080` is a **package** name (`Ww_BML_Suspension`), not a
value. `chase-06.md:85` is a **value probe**: it reads `40.0` at the offset where the card carries `100`.
`chase-06.md` is a chase/offset dig, not a package serialisation, so the two numbers are measuring
different things — but the card should say which one it quotes. **Not changed here** (see §5).

### 2.2 FOUND, but no length — FOUND

| query | path:line | quoted | why it is not a droop/bump length |
|---|---|---|---|
| `rebound` | `Research/JC3Grab/SUSPENSION_BRIDGE.md:116` | `\| \`BMWheelSuspensionDamping 300\` \| compression + relaxation (ints) \| 1 / 2 \| -31.1% zeta \| PLACEABLE as a pair - JC3 splits bump/rebound, BmAK has one number \|` | a damping pair (ints), no travel |
| `rebound` | `Research/BatmobileGrab/DAMAGE_RULES.json:8317` | `"RecoverFromRebound",` | a reaction/state name |
| `bump stop` | `Research/specs/B-23.md:46` | `its bump stops; the bridge's 13.500 is the mode-neutral pick.` | prose about the spring rate, no member |
| `max_length_offset` | `Research/JC3Grab/VOCABULARY.md:1154` | `\| \`front.max_length_offset\` \| float \| 0 .. 0 (med 0, n=167) \| 0 \|` | the closest carrier; **0 on every sample** |
| `max_length_offset` | `Research/JC3Grab/VOCABULARY.md:1168` | `\| \`rear.max_length_offset\` \| float \| 0 .. 0 (med 0, n=167) \| 0 \|` | same |
| `max_length_offset` | `Research/JC3Grab/VOCABULARY.md:936` | `\| \`land_suspension.front.max_length_offset\` \| float \| 0 .. 0 (med 0, n=19) \|  \|` | same, 19-sample set |
| `max_length_offset` | `Research/JC3Grab/VOCABULARY.md:950` | `\| \`land_suspension.rear.max_length_offset\` \| float \| 0 .. 0 (med 0, n=19) \|  \|` | same |
| `min_length` | `Research/JC3Grab/VOCABULARY.md:1156`, `:1170`, `:938`, `:952` | `\| \`front.min_length\` \| float \| 0 .. 0 (med 0, n=167) \| 0 \|` (and the rear / land_suspension twins) | 0 everywhere, semantics undecoded |
| `droop` | `Working/Translation/BUILD_BATCHES.md:159` | `\| B-22 · Droop and up-travel … \| \`Builds/bm-022/\` \| … reads back \`length\` 0.40 / \`max_length_offset\` 0.30 / \`min_length\` 0 …` | a build-batch row describing the plan, not a member |
| `droop` | `Working/Translation/BLOCKED_PROPOSALS.md:89` | `**Still open:** no member for droop (\`BMRearWheelMaxDroop\` 100) or the up-travel 30 cm (cards B-22)…` | the absence, restated |
| `droop` | `Working/Translation/build_batches.json:2245` | `"B-22": "droop and up-travel: one \`max_length_offset\` write in a private copy, per card B-22",` | generated copy of the batch row |

### 2.3 NOT_FOUND — the absence, with the line that states it

| query | path:line | quoted |
|---|---|---|
| `droop` | `Research/JC3Grab/SUSPENSION_BRIDGE.md:114` | `\| \`BMRearWheelMaxDroop 100\` \| (no member: no droop channel) \| UNKNOWN \| n/a \| NO MEMBER - 1.0 m droop has no authorable field; gap for BUILD \|` |
| `droop` | `Research/specs/B-22.md:32` | `\| (droop / rebound stop) \| **no member** \| 0 rows in the 166-file vocabulary carry droop, rebound, bump-stop or droop-limit \|` |
| `rebound` | `Research/specs/B-22.md:32` | same line |
| `bump stop` | `Research/specs/B-22.md:32` | same line |

These four are scored **NOT_FOUND**, not UNKNOWN, because a decode of the searched corpus *exists* and says
zero: `VOCABULARY.md` is the 166-vehicle member census, and no key in it names droop, rebound or a
bump-stop.

### 2.4 UNKNOWN — and the file that would settle each

| query | path:line | why UNKNOWN | settler |
|---|---|---|---|
| `bump/rebound travel` | `Research/JC3Grab/SUSPENSION_BRIDGE.md:158` | "JC3 carries no separate bump/rebound travel … `max_length_offset 0.30`, same UNKNOWN" — the member exists but **whether the engine reads it as extension is undecoded** | the `Suspension` module consumer in `JustCause3.exe`; a `Tools/scripts/jc3adf.py` re-decode of the built `<chassis>_suspension.vmodc`; a Q-2 take measuring wheel extension |
| `droop` (Working/ scope) | — no hit returned | the `Working/` scan was **truncated at 18 matches by the 10 s cap**, so absence there is unproven | re-run the `Working/**` scan without the cap |
| `bump stop` (Working/ scope) | — no hit returned | same truncation | same |

The one term whose *carrier* is decoded but whose *meaning* is not is therefore `max_length_offset` — which
is exactly B-22's step 2 ("probe whether the wheel can extend past its rest position at all; if the engine
ignores the member … record the reader as absent").

## 3. What the search adds to the card

1. **The droop member is real and its offset is decoded (0x318, front 0x314).** The card's "no member" is
   true of **JC3**, not of BmAK; the JSON records the BmAK member so the distinction cannot be lost.
2. **`max_length_offset` is zero on 167/167 and 19/19** — not "rare", never authored. That is the strongest
   available evidence that authoring it is an experiment, not a translation.
3. **The 100 cm figure has a competing 40.0 read** at the same offset (`chase-06.md:84-85`). Flagged; the
   `B-22` card's number comes from `TYRES_PACKAGE.md` and was not touched.
4. **JC3 "rebound" ≠ JC3 "droop".** The only bump/rebound split in the corpus is the **damping** pair, so a
   droop length cannot be smuggled in through `compression`/`relaxation` either.

## 4. Compliance

* `Research/specs/B-22.md` and the `GRAB_BACKLOG.md` `B-22` rows were **read only** — no edit, no rewrite.
* **No** game install, GOG folder, save file or dropzone was opened. Every path above is inside this
  repository's `Research/` or `Working/`.
* No script was modified or run except the searches; no build, no install.

## 5. Limits

* The `Working/` scan hit the search tool's 10 s cap and returned 18 matches of an unknown total. That is
  why both `Working/`-scoped rows are **UNKNOWN** rather than NOT_FOUND.
* `Research/` results were complete for the three terms (29 / 5 / 2 matches, none truncated).
* `BMRearWheelMaxDroop`'s **value** is not adjudicated here: 100 cm (card, from `TYRES_PACKAGE.md`) and
  40.0 (chase probe) both stand as recorded, and settling them is a decode question, not a search question.

## 6. Revert

Delete this file and `Working/Prep/b22_droop_members.json`. Nothing else was created or changed.

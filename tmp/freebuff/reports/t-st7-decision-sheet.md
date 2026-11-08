# t-st7-decision-sheet - the operator decisions behind the blocked rows

## STATUS

**done - `Working/Translation/DECISIONS_NEEDED.md` written (199 lines). Four rows in
`BLOCKED_PROPOSALS.md` need an operator decision rather than more evidence: `T-ST7` (the brief's
row), `T-FX3`, `T-WP13` and `T-WP4`; the other 13 are listed as evidence-waiting, explicitly not
decisions. No row was edited: `T_ROWS.jsonl` still hashes to `8996b60a5370d932...`, the value
`BLOCKED_PROPOSALS.md` pins.**

Files written:

- `Working/Translation/DECISIONS_NEEDED.md` - the decision sheet: row, what it waited for, the
  refuting evidence with file and line, the options with their lore consequence, a labelled
  recommendation per row, and the evidence-waiting list.
- `tmp/freebuff/reports/t-st7-decision-sheet.md` (this card).

Untouched: `Working/Translation/T_ROWS.jsonl`, `BLOCKED_PROPOSALS.md`/`.json`,
`Working/Translation/T_ST7B_FLOOR.md`, `T_FX3B.md`, `T7_WEAPONS.md`, every build artefact. No game
launched or attached (INSTRUCTIONS.md section 3).

---

## 1. Which rows actually need a decision

The proposals file enumerates 17 blocked rows and classifies six of them. Applying the brief's test -
*does the row wait for a choice, or for a file that does not exist?* - gives four:

| row | why it is a decision |
|---|---|
| `T-ST7` | its blocked reason ("the fleet's fastest rack is 0.5 s") is refuted in `T_ST7B_FLOOR.md`; what remains is which value to ship |
| `T-FX3` | `BLOCKED_PROPOSALS.md:12` states it outright: "what is missing is a decision on which usage raises the flame" |
| `T-WP13` | `BLOCKED_PROPOSALS.md:18`: a mechanism, "or an operator decision to accept 2" driver slots |
| `T-WP4` | the proposed `split` (`BLOCKED_PROPOSALS.md:80`) is a bookkeeping choice that would let a decoded launcher ship |

The other 13 (`T-AU3`, `T-AU5`, `T-S6`, `T-WP5`, `T-WLD4`, `T-WLD6`, `T-WLD11`, `T-MD2`, `T-MD14`,
`T-HUD5`, `T-CAM8`, `T-CAM9`, `T-CAM11`) each wait on a missing decoded member, bank or writer; the
sheet lists them with one line each and says plainly that there is nothing to choose.

## 2. T-ST7, in plain terms

- BmAK: 220 °/s rack, 55° lock -> **0.25 s** to full lock (derived: 55/220).
- The row ships **0.8 s low / 0.6 s high**, blocked on "JC3's steering model cannot be that quick".
- Refuted, with lines:

| claim in the row | file:line | what the file says |
|---|---|---|
| "fleet's fastest rack is 0.5 s" | `T_ST7B_FLOOR.md:16` | `MotorbikeSteering` **player** modules: min **0.3 s**, 2 modules, 9 below 0.5 |
| same | `T_ST7B_FLOOR.md:17` | `LandSteering` **AI twin**: min **0.25 s**, 4 modules, 4 below 0.5 |
| same | `T_ST7B_FLOOR.md:19-20` | "A player module does ship below 0.5 s ... so the player steering path is not floored at 0.5 in the data" |
| the census it rests on | `T_ST7B_FLOOR.md:10` | 6,045 modules over 232 entities, 271 steering modules |
| the member is data | `Research/JC3Grab/DRIVE_CARRIERS.json:600` | `"path": "t_to_full_steer_s"` |

- Still true: **no player car** ships below 0.5 s (`T_ST7B_FLOOR.md:26-29`), so 0.8 s is in family -
  but by convention, not by an engine limit.
- Route R1's mechanics (`T_ST7B_FLOOR.md:43-44`): member at **+8**, file byte **88**, float bytes
  `0000803e` = 0.25.

Options put to the operator, with consequences: **A** 0.25 s (exact lore, 3.2x quicker than today,
2x quicker than any player car, unmeasured in play); **B** keep 0.8/0.6 (0.55 s slower than BmAK,
and the false "model limit" must be withdrawn); **C** 0.5 s (2x slower, in family); **D** other
(R2 motorbike class 0.3 s, R3 high-speed member only, R4 impossible - needs 110°, fleet max 45°).
**Recommendation: A, conditional** on accepting an unmeasured data-only change; otherwise C, never
B-as-labelled.

## 3. Verbatim commands

```
$ cd E:/Modding/JC3-Batmobile && grep -n "T-ST7\|T-FX3\|T-WP13\|T-WP4\|T-S6" Working/Translation/BLOCKED_PROPOSALS.md
3:STATUS: partial - 17 blocked rows enumerated (13 ledger + 4 T6 = STATUS.md's 17 of 180), the first six tested against the repo: 1 unblocked with evidence (T-FX3), 1 reason refuted and needs a decision (T-ST7), 1 partially unblocked (T-WP4), 3 still blocked (T-AU3, T-S6, T-AU5).
12:| 2 | `T-FX3` | T-2b | nothing structural: JC3's `usage_effects` carrier and the `EngineNitro` usage are decoded; what is missing is a decision on which usage raises the flame |
13:| 3 | `T-S6` | T-3 | BmAK's numeric stiffness/damping in a known unit - no project file carries one - and JC3 has no droop member to carry `BM*MaxDroop` |
14:| 4 | `T-ST7` | T-3 | an operator decision: accept 0.8/0.6 s, or route BmAK's 0.25 s through `t_to_full_steer_s` (data-only, unmeasured; the 0.5 s 'floor' is refuted) |
16:| 6 | `T-WP4` | T-7 | a JC3 member that disables an NPC vehicle - the missile half is decoded, the disable half is not |
18:| 8 | `T-WP13` | T-7 | a weapon-switch mechanism (max 2 driver slots, no active-slot index and no next/previous action in the 232 `.epe`) or an operator decision to accept 2 |
22:| 12 | `T-MD2` | T-15 | the disable half of T-WP4 (the launcher is available in both modes, the disable is not carried) |
38:### T-FX3 - unblocked-with-evidence
48:### T-S6 - still-blocked
57:### T-ST7 - reason-refuted-needs-decision
65:**Missing input:** the operator's decision, and if 0.25 s is chosen a game probe to prove the player path honours it (test ban; T-ST7 stays UNAPPROVED either way)
74:### T-WP4 - partially-unblocked
80:**Proposed edit (not applied):** dispo `split`, confidence cell `decoded / UNKNOWN`, value: T-WP4a launcher = `Batmobile_EMP_Missile_Launcher` (3 instances, 63 fields) as a w618 clone; T-WP4b disable = named omission ...
```

```
$ sed -n '10p;16p;17p;19p;20p;26,29p;43p;44p' Working/Translation/T_ST7B_FLOOR.md
**6,045** decoded vehicle modules (232 entities), **271** are steering modules; player copy and
| `MotorbikeSteering` player (bikes) | 0.3 | 2 | 9 |
| `LandSteering` AI twin | 0.25 | 4 | 4 |
* **A player module does ship below 0.5 s**: the bikes (`MotorbikeSteering`) carry
  **0.3 s** on 2 player modules, so the player steering path is
* **No player module reaches 220 deg/s**: the best player rate is
  **116.7 deg/s** (...), the best player **car** rate is
  **80 deg/s** (...), and
  the car minimum time is 0.5 s on 6 modules. So the honest
| R1 | write **0.25** into the player car's `t_to_full_steer_s` | member +8, file byte 88,
  `0000803e`; the AI twin of the same car already ships 0.25 s (same member/type) | **the cheapest route**: data-only, no clamp decoded; whether the player path honours it is UNKNOWN |
```

```
$ sed -n '600p' Research/JC3Grab/DRIVE_CARRIERS.json
   "path": "t_to_full_steer_s",
```

```
$ sed -n '8p;62p;98p' Working/Translation/T_FX3B.md
T-FX3's wording ("no usage slot for an exhaust flame") is **wrong as an engine claim**: JC3 has a
The donor's two emitters carry `usage` = EngineNitro (4197885156) and `world` = ... (decoded, `Working/Effects/bm_fx_edits.json`).
| 4197885156 | `EngineNitro` | 18 | `EngineNitro` (4), `dynamic_nitrous` (14) |
```

```
$ sed -n '63p' Working/Translation/T7_WEAPONS.md | cut -c1-420
| **D-7** | how do all 11 weapons take JC3's driver slots, in both modes? | the fleet has **2 driver slots** at most (medium and Bavarium tank: `main_weapon` + `id:00568A74`); there is no active-slot index, no next/previous weapon action and no weapon group anywhere in the 232 `.epe` graphs (G2-11 section 2b); the HUD has 2 clips (G2-25). BmAK itself has primary + secondary + **3 special-weapon states** and a radial
```

```
$ sed -n '91p;163p' Working/Translation/T_ROWS.jsonl | cut -c1-60
{"id":"T-ST7","doc":"T-3","section":"1. The rows","cells":["
{"id":"T-WP13","doc":"T-7","section":"3. The rows","cells":[
```

```
$ grep -c "4197885156" Research/JC3Grab/USAGES.json
9
```

```
$ sha256sum Working/Translation/T_ROWS.jsonl
8996b60a5370d932... (unchanged - the ledger was not edited)
```

## 4. UNKNOWN (with what was tried)

1. **Whether any option behaves as predicted in play.** The test ban forbids launching the game, so
   all four recommendations are static arguments from decoded bytes. T-ST7's option A in particular
   is data-only but unproven: the AI twin at 0.25 s shows the member and parser accept the value,
   not that the player update uses it (`T_ST7B_FLOOR.md:36-37`; no engine clamp decoded either way -
   `T_ST7B_FLOOR.md:34-35`).
2. **Whether `EngineNitro` can be raised outside the arcade nitro stat fields** (`T_FX3B.md:155,163`).
   Tried: the usage vocabulary (155 values, 18 rows for this id) and the donor entity's own
   attachment; the raising state machine is game code, not decoded. This is why T-FX3's option A is
   a best-effort, not a guaranteed visible flame.
3. **Whether a third weapon slot could be carried by any uncatalogued mechanism.** Tried: 232 `.epe`
   graphs, 53 armed entities, HUD clip count - no active-slot index, no next/previous action. The
   0-of-88 check is for `CEMPWeapon` (T-WP4), not for slots; the slot search is T7_WEAPONS.md:63's
   `G2-11 section 2b`. A mechanism outside the ADF graphs (engine input binding) was not searched,
   because the input map is not in this repo.
4. **What the operator's policy is on shipping unmeasured player-path changes.** Not in any file I
   read; that is exactly why the sheet presents it as a condition instead of assuming an answer.
5. **Line numbers** are 1-based against the files as they stand today; four of the five cited files
   are generated by their own `--check`, so a rewrite would shift them and this card would need
   re-running. `BLOCKED_PROPOSALS.md` is sha-pinned to the ledger, so its own drift fails its check.

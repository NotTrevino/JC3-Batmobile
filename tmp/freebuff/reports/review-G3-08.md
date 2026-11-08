# Review — G3-08 · JC3 vehicle input model (`INPUT.md` / `.json`)

Independent review. I did not write this card. Read-only: `INDEX.jsonl` → the `.arc` archives under
`D:/Games/Just Cause 3` (read only, nothing written there), the 232 entity dumps under
`E:/Modding/_shared/gamedata/JC3grab/entities`, `jc3index.MOUNT_RANK`, `rbmhdr.hash_jenkins`, the card and its
script. I parsed the four keymap files with my own code, not `jc3_input.py`. Only this report was written
(plus the two earlier reviews).

## VERDICT: **minor issues**

The container decode is right. My own parse of all four files reproduces every published number: sizes,
entry offsets, sha256 prefixes, binding counts, root/list and property hashes, property type, string
dedup counts, the tiling/accounting, and the Jenkins match tally (448 / 26). The 474-row action table is a
faithful read of the mounted patch layers, and I confirmed its key rows independently.

The problems are in what the card *says* about its own evidence, and one verdict row:

1. A **factual error that also removes the stated reason for an UNKNOWN**: the card says binding ids are
   "stable across the base and patch copies for the same action". Three keyboard actions contradict it.
2. One **verdict rests on an invented mapping**: "immobilizer → `USE_ITEM` → reachable". Nothing decoded
   ties `USE_ITEM` to the immobiliser; it is bound to the same physical key as enter/exit vehicle.
3. The **completeness claim** "the whole input definition" is labelled `decoded` but its evidence (an
   index-wide search) is not in the artifact, and the card's own nitro UNKNOWN shows actions can exist
   without a keymap row.
4. The **scope rule contradicts its own alternation** for `LOOK_BACK_CAM`.

No decoded byte value needs rework; the verdict column needs re-labelling.

## Check output

Command:

```
cd /e/Modding/JustCause3/JC3-Batmobile && uv run --with numpy python Tools/scripts/jc3_input.py --check 2>&1 | tee /tmp/g308_check.txt; echo "EXIT=${PIPESTATUS[0]}"
```

Output (verbatim):

```
json ok: re-derived data == INPUT.json (474 bindings, 154 actions)
md ok: re-rendered text == INPUT.md (22311 bytes)
string fidelity: 474/474 bindings re-read their input and action strings from the archive at the recorded offsets
CHECK OK
EXIT=0
```

The "string fidelity" pass is the strongest part of `--check`: it re-reads each binding's two strings from
the archive at the recorded offsets, so an offset that drifted would fail. It still judges the card's own
parse with the card's own code; the re-reads below are the independent half.

## Spot-checks

| # | card value | card label | my source | match |
|---|---|---|---|---|
| 1 | gamepad **patch**: `patch_win64/game4`, offset 610914304, size **7207**, 145 bindings, sha `0944e37d8588feed` | decoded | my open/seek on `patch_win64/game4.arc` + my RTPC parse | **yes** |
| 2 | keyboard **patch**: offset 610922496, size **5291**, 104 bindings, sha `5674c38366c69a85` | decoded | same | **yes** |
| 3 | root `AA7D522A`, list `49267ABC`, property hashes `7935F00C`/`8613CCD3`, type 3 | decoded | my parse of **all four** files | **yes** |
| 4 | `ACCELERATE` RTRIGGER/W; `HANDBRAKE` RPADLEFT/LSHIFT; `EXIT_VEHICLE` RPADUP/E | decoded | my mounted-layer action map | **yes** |
| 5 | node hash = `H(action)` for **448**, `input` 6, 26 unexplained | decoded | recomputed `hash_jenkins` over every binding | **yes** (448/6/26) |

Also reproduced: 474 bindings over 4 files, 154 distinct mounted actions, 95 on both devices; base sizes
6427 / 4615 with 131 / 94 bindings; distinct-string counts 154 / 169 / 130 / 147; and the block tiling —
my parser asserts every binding's `data_offset` equals the predicted cursor and every new string starts
exactly where predicted, and it holds in all four files. (The final block ends at the file end with no
padding; 4-byte alignment applies *between* blocks. My always-align loop reported `tail = -1`, which is an
artifact of aligning the last block — the card's `tail 0` is the correct reading.)

Entity census, re-run over **all 154** action names rather than the card's 3 (one pass, whole-token
matching, 265,933,538 bytes): **0 of 232 files** contain any action name as a whole token; `keymap` 0/232;
`nitro_boost` **220**; `arcade.nitro_boost` **145**. The card's conclusion survives a much wider test than
it ran.

## Issues

**I-1 · `INPUT.md` UNKNOWN 6 ("why 26 binding ids are not `H(action name)`") — the stated reason is false.**
Value: "The remaining ids are **stable across the base and patch copies for the same action**, so they
were fixed before the current name or by another rule."
My layer-by-layer comparison: gamepad base→patch, 0 of 131 actions change id; **keyboard base→patch, 3 of
88 change id** — `TURN_LEFT` (base `344C0D32` → patch `231E1B96`), `ACCELERATE` (base `84653419` →
patch `82CBBC77`), `REVERSE` (base `BC055EC1` → patch `86C49D30`). In each case the base id is *not*
`H(action)` and the patch id *is*. So those three of the 26 are stale base-layer ids that the patch
superseded, which is exactly the opposite of "stable". The card's stability argument was the only reason
given for calling the remainder unexplainable. (For the other 23 the ids *are* stable across the four
copies — `9274C792` for `DEBUG_DECREE`, `E45C33F0` for `DEBUG_INCREE`, `AFCC0D8A` for
`MECH_FIRE_GRAVITY_WEAPON_PRIMARY`, … — so the conclusion survives for 23, not 26.)
Impact: a reader is told the ids are immutable and must come from an earlier naming system; three of them
are simply out of date in the base layer.

**I-2 · `INPUT.md`, BmAK verdict "immobilizer (B in track)" — a "reachable" verdict built on an invented mapping.**
Value: "`USE_ITEM`: present → **reachable**".
`USE_ITEM` is bound to `RPADUP` / `E` — the same physical key as `ENTER_VEHICLE`, `EXIT_VEHICLE`,
`OPEN_WINGSUIT`, `GUI_USE_BUTTON` and `WINGSUIT_TAKEOFF`. Nothing decoded connects "use item" to the
Batmobile's immobiliser missile; the row's own citation is "D-11 user mapping", i.e. the user's *play*
description, not a decoded consumer. The card's rule ("reachable when every named action exists") is
applied to a name the author chose, which makes the verdict an assumption wearing a computed result's
clothes. Either mark the row `UNKNOWN (no JC3 action named for it; USE_ITEM is a generic use key, not a
weapon)` or prove the link (G2-16's EMP path is the place).

**I-3 · `INPUT.md`, "Two `settings/*.bin` entries in the archives are the whole input definition (decoded)".**
This is a completeness claim about a 81,952-entry index, but `INPUT.md` contains no census that supports
it and `jc3_input.py` performs no index search at all (it hardcodes `KEYMAPS` and treats their absence as
fatal). The evidence exists only in `tmp/freebuff/reports/G3-08.md` ("searched the index for input,
control, keymap, action, button, keybind, gamepad, joystick"). Worse, the card's *own* nitro UNKNOWN
argues an action can be triggered natively with no keymap row — so "the whole input definition" cannot be
established from the keymap files alone. Label it `derived (search rule: …; index sweep recorded in the
task report)` and state the limit: this is the whole *bound-action* definition, not the whole input path.

**I-4 · `INPUT.md`, "What the vehicle side names" — the claim is broader than the census under it.**
Value: "So **no vehicle entity names an input action**", evidence column: `keymap` 0, `EnterVehicle` 0,
`ENTER_VEHICLE` 0, `ACCELERATE` 0, `FIRE_VEHICLE_WEAPON_PRIMARY` 0 — i.e. **3 action names of 154**.
I re-ran it over all 154 with whole-token matching and got 0/232, so the conclusion is true. But as
shipped, the record asks a reader to trust a 3-name sample for a 154-name claim. Put the 154-name number
in the table (it costs one row) instead of relying on the reader's charity.

**I-5 · `INPUT.md`, verdicts "not reachable" — a name-level negative presented as a functional one.**
Rows: battle mode, ejection, sonar/scan, tag gun, tank pivot, barrage, each `not reachable` because a
regex over action names matched 0. That shows JC3 has **no action with that name**, not that JC3 cannot
do it: the same page records nitro as UNKNOWN precisely because the trigger is native/graph despite
`arcade.nitro_boost` existing. The two treatments are inconsistent. Say `no action named (decoded); whether
JC3 can do it is UNKNOWN` — which is what the data supports — or give the functional evidence.

**I-6 · `INPUT.md`, scope rule vs its own alternation — `LOOK_BACK_CAM` is misrouted.**
`SCOPES` lists `LOOK_BACK_CAM` inside the **land-vehicle** alternation, but `on-foot` is evaluated first
and its `LOOK_` prefix matches, so the action table prints `LOOK_BACK_CAM | RSTICKBUTTON | B | on-foot`
and the per-class table omits it from `land-vehicle` — while the BmAK verdict table uses it as a driving
aid ("look behind → present → reachable"). The land-vehicle alternative is dead code. Either move
`LOOK_BACK_CAM` before `on-foot` in the rule (and re-render) or record why a camera action is classified
on-foot; as it stands the per-class picture contradicts the verdict table for the same action.

**I-7 · `INPUT.md`, container sentences rendered from `files[0]` only.**
"Property types seen: 3×**262**" is file 0's count (2 × 131 bindings) but the sentence says "in every
binding"; "the two property name hashes are … in all four files" and "Root hash … and list hash … are
identical in all four copies" are printed from `d["files"][0]` and never compared across files. All three
claims are **true** — I checked them across all four — but the code does not establish them, so they are
unlabelled assertions dressed as decoded output. (The parser does enforce type 3 everywhere, so that one
half is guaranteed by construction; the hash half is not.)

**I-8 · `INPUT.md`, "Entity-class census from the decoded `.ee` dumps".**
The census is derived from **filenames** (`fn.split("__")[0].split("_")[1]`, e.g. `v0300_car_…`), not from
the dumps' contents. The rule is stated in the same sentence, so this is a wording slip, but the phrase
"from the decoded .ee dumps" implies the files were read for it. Say "from the entity file names".

**I-9 · `jc3_input.py`, latent verdict value.** `evaluate_bm` can return `partial` for an `exact` row
(some names present, some absent), but `INPUT.md`'s key names only `reachable` / `not reachable` /
`UNKNOWN`. No current row triggers it, so it is a latent inconsistency rather than a wrong value.

## Resolvable UNKNOWNs

**U-1 · "why 26 binding ids are not `H(action name)`" — partly resolved, and the rest has a decidable route.**
3 of the 26 are **stale base-layer ids** superseded by the patch (I-1): `TURN_LEFT`, `ACCELERATE`,
`REVERSE` in `keymap_keyboard.bin`. So the count to explain is **23**, not 26, and the justification must
be rewritten. The remaining 23 are action-keyed, not binding-keyed: the same id appears for the same
action across both devices and both layers (`9274C792` `DEBUG_DECREE`, `E45C33F0` `DEBUG_INCREE`,
`AFCC0D8A` `MECH_FIRE_GRAVITY_WEAPON_PRIMARY`, `95F06701` `GUI_PDA`, `DA065048` `GUI_PAUSE`,
`A07939AA` `USE_VEHICLE_MOD`, `C0BFB204`/`3CBCC987` `FIRE_VEHICLE_WEAPON_PRIMARY`/`SECONDARY`). I tested
nine further transforms of `action`/`input` against all 26 (NUL suffix, `PP` prefix, lower, upper,
`input+action`, `action+input`, device suffix, `+2`, title case): **0/26 each**. The decidable next step is
to hash candidates from a name source the project already has — the JCMR dictionary names used by
`jc3index.py` — against those eight distinct ids; one hit would name the older field and close it. No
runtime needed.

**U-2 · "whether `NEXT_WEAPON` / `PREV_WEAPON` reach a vehicle" — partly decidable, not by this file.**
Both are keyboard-only (`MWHEELUP` / `MWHEELDOWN`) and the gamepad map has no wheel. A consumer search is
the same kind of step G3-02b did for the BmAK side: look for the action names in the JC3 script/graph
data rather than the keymap. Nothing in the keymap can answer it, and the card is right to leave it open —
but the "where it would be found" line is missing (it says only that no file says it).

**U-3 · "the `PP` prefix on the stored input string" — still UNKNOWN, and here is the negative result.**
Every input string carries it and no other 2-byte prefix occurs anywhere in the four files (the parser
asserts the literal at each block and the tiling closes), so it is a fixed tag, not a per-binding value.
Whether it names a device or a table kind cannot be decided from these files; it would need a second
container that stores input names without the prefix.

**U-4 · "how the class-specific action sets are selected at runtime" — not resolvable from these bytes; keep it.**
The class tokens live in the *action names* (`HELI_`, `PLANE_`, `BIKE_`, `SUBMERSIBLE_`) and in the `.epe`
root object; nothing in the keymaps or entities maps class → scheme. That selection is in the executable
(out of scope for this card and not attempted here).

**U-5 · "which keymap layer the game loads" — runtime only.** Both copies exist (`base` and `patch`;
`MOUNT_RANK` has no `dlc` copy of either path — my index query returned exactly the four rows the card
tabulates). Nothing static distinguishes them.

## Bottom line

Keep the container decode, the action table and the byte-accounting oracle — I reproduced all of them,
and the 154-name entity census backs the "global keymap" conclusion more strongly than the card's own
3-name table does. Fix the four statements that overreach: the false "ids are stable" premise (23, not 26,
and three are stale base rows), the immobiliser row's invented `USE_ITEM` mapping, "the whole input
definition" (scope it, and cite the index sweep inside the record), and the `not reachable` labels (they
are "no action with that name"). Then correct `LOOK_BACK_CAM`'s scope and the file-0-only hash sentences.

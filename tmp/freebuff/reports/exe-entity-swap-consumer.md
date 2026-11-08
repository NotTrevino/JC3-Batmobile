# Is there a runtime entity-swap consumer in `JustCause3.exe`?

Static, read-only analysis. `D:/Games/Just Cause 3/JustCause3.exe` (51,083,264 bytes, image base
`0x140000000`, **188,670** `.pdata` functions) was opened with pefile, the `.pdata` chunk table
read, `.text` swept for rip-relative operands and disassembled with capstone. Nothing was run,
attached, injected or patched.

Artifacts: `Tools/scripts/exe_entity_swap.py` (`--write` / `--check`, 13/13 checks),
`Research/JC3Grab/ENTITY_SWAP.md` and `ENTITY_SWAP.json` (generated, byte-identical on re-derive).
Method copied from the exe work that already exists here (`Research/JC3Grab/COLOUR_NATIVE.md`,
`RUNTIME_LAYOUT4.md`): a candidate reference is kept only if a real instruction inside a
`.pdata`-bounded function ends exactly at that disp32 and its operand text says `rip`.

Labels: **decoded** = address plus bytes; **derived** = a stated rule over decoded facts;
**UNKNOWN** = not answerable from these bytes, with what was tried. Every claim below carries an
instruction address; a claim without one is marked UNKNOWN.

---

## 1. Verdict

**U1 does not close, but it moves from "nothing found" to "one named type, one consumer, and no
entity-returning call".**

1. The image contains **`SRebelSwap`** at `0x142466618` — once, as a lone string (**decoded**).
2. Exactly **one instruction** loads its address: `lea rdx, [rip + 0x179D9B2]` at **`0x140CC8C5F`**,
   inside function **`0x140CC8950`-`0x140CC93D9`** (2,697 bytes, **0** direct `E8`/`E9` callers)
   (**decoded**). So the swap type is not dead data: the engine names it at runtime.
3. The instructions immediately before the load set up a **length-bounded string comparison**
   (`mov r8d, 0xa` / `cmp rdi, r8` / `cmovb r8, rdi`, `rdi` from `[rbp - 0x19]`), and `0xa` = 10 =
   the character count of `SRebelSwap` (**decoded**, rule stated). The same function also references
   `CCopiedRuntimeContainer_CopyFrom`, `_class`, `,character`, `,vehicle`, `,weapon` and
   `revolution.change` (**decoded**: string refs at `0x140CC92E8`, `0x140CC8ADB`, `0x140CC8ED9`,
   `0x140CC8FC5`, `0x140CC90B1`, `0x140CC9384`).
4. The call that follows the comparison is `call 0x141EBB0B4` at **`0x140CC8C66`**; its target
   begins with `jmp qword ptr [rip + 0x3E7AB6]` — a **jump-table thunk**, not inside `.pdata`, 348
   direct callers (**decoded**). **What the comparison decides is therefore UNKNOWN.**
5. **No function in the image takes an entity and returns a different entity, on this evidence.**
   What exists is: a named swap *type* compared during a container copy, an `Item` record schema, a
   Rebel Drop menu loader, and `rebelsupport.*` script event names. The step that turns an item or a
   swap record into a spawned `.ee` is **not identified**.
6. The strongest negative that survives: **`CDespawnVolume`** (4 references) and
   **`CSpawnSystem` / `CAmbientSpawnUtil`** exist, but the four despawn references are a typeid stub
   (`0x1409DBE40`, 62 bytes, `CDespawnVolume`) and three type-registration sites — none is a
   "replace this actor" call.

Consequence for the mode pair: **T-MD5 / T-MD6 / T-MD15 are still not unlocked by a consumer.** The
two-entity swap is not reachable from an item, an `.ee` or a graph on this evidence; the Rebel Drop
route (spawn the battle leaf) remains the only proven path, exactly as
`reports/mode-toggle-runtime-swap.md` §5 said. What is new is the *reason*: the engine's swap name is
consumed by a **container-copy/compare** path with no direct caller, not by a spawner.

---

## 2. What was measured, in counts

| measure | value |
|---|---:|
| `.pdata` functions | 188,670 |
| names searched (entity / spawn / swap / drop / vehicle) | 33 |
| names present in the image | 32 |
| independent string occurrences (after pruning suffix matches) | 34 |
| suffix occurrences pruned (`Swap` inside `SRebelSwap`, `SpawnRule` inside `CSpawnRule`, …) | 3 |
| verified rip-relative reference sites | 74 |
| functions those sites land in | 60 |
| of those, functions reaching an item/Rebel Drop name | 7 |
| direct `E8`/`E9` caller edges into those functions | 414 |
| argument-register dereference rows (first 40 instructions) | 26 |

`Swap` is **absent as an independent string**: its only occurrence is `SRebelSwap`+6. The census
therefore reports 32 of 33 names present, and `--check` asserts that no term occurrence overlaps
another, so a suffix can never be counted as a name again.

---

## 3. The one swap-name consumer, in full

**decoded** — window around the reference, verbatim from `ENTITY_SWAP.md` §1a:

```
 0x140CC8C44 cmp qword ptr [rbp - 0x11], 0x10
 0x140CC8C49 cmovae rcx, qword ptr [rbp - 0x29]
 0x140CC8C4E mov r8d, 0xa
 0x140CC8C54 mov rdi, qword ptr [rbp - 0x19]
 0x140CC8C58 cmp rdi, r8
 0x140CC8C5B cmovb r8, rdi
>0x140CC8C5F lea rdx, [rip + 0x179d9b2]        ; "SRebelSwap"
 0x140CC8C66 call 0x141ebb0b4
 0x140CC8C6B movsxd rcx, eax
 0x140CC8C6E test eax, eax
 0x140CC8C70 jne 0x140cc8c89
 0x140CC8C72 cmp rdi, 0xa
 0x140CC8C76 jae 0x140cc8c7d
 0x140CC8C78 or ecx, 0xffffffff
 0x140CC8C7B jmp 0x140cc8c89
```

**Derived:** compare-then-branch on the result, with the literal length pre-loaded into `r8`. That
is a bounded name comparison; it is not a `new Entity`, and it is not a call into
`CEntityResourceLoader`.

The identical shape recurs for the spawn-point schema, which is why the swap path looks like the
schema path and not like a spawner:

| function | bytes | name compared | sibling strings (**decoded**) | callers |
|---|---:|---|---|---:|
| `0x140CC8950` | 2,697 | `SRebelSwap` | `CCopiedRuntimeContainer_CopyFrom`, `_class`, `,character`, `,vehicle`, `,weapon` | 0 |
| `0x140D89F70` | 3,510 | `SSpawnPoint` | `CCopiedRuntimeContainer_CopyFrom`, `_class` | 0 |
| `0x140DC1490` | 3,871 | `SSpawnWeaponSeat` | `,character`, `,weapon`, `_class` | 0 |

**Derived:** all three are the same kind of function — a class-name comparison sitting beside
`CCopiedRuntimeContainer_CopyFrom`. On this evidence the family is the **runtime-container copy /
class-name comparison** path, which is how the game notices a record's `_class` while copying it.
That is a *data* path: it says a record of class `SRebelSwap` could be copied, not that a vehicle is
replaced.

---

## 4. Every function that matters, with its entity argument and its data

The `entity argument` column is what the tool decodes: the first dereference of `rcx`/`rdx`/`r8`/`r9`
inside the first 40 instructions, with its address. **None of these functions shows an
entity-typed argument being returned or replaced.** "none in first 40" means exactly that; it is not
a proof of arity, and every semantic type is UNKNOWN.

| function | bytes | what its strings say (**decoded**) | entity argument (**decoded**) | can a mod drive it? |
|---|---:|---|---|---|
| `0x140CC8950` | 2,697 | `SRebelSwap`, `CCopiedRuntimeContainer_CopyFrom`, `_class`, `,vehicle` | none in first 40 | **UNKNOWN** — reads no path, no item field; 0 callers, so nothing in the image calls it directly. A container of that class would have to reach it through the thunk. |
| `0x140CC75A0` | 2,357 | `b_purchasable`, `b_consumable`, `b_rewardable`, `i32_rebel_drop_timer`, `i32_region`, `a_feats`, `a_stats` | none in first 40 | **yes (schema)** — these are the `Item` member names `REBELDROP.md` decoded from data; the table is a mod-owned `profile/item.onlinec`. It does not spawn. |
| `0x140CC82A0` | 480 | `/profile/item.onlinec`, `profile/item.onlinec`, `dlc/` | none in first 40 | **yes (path)** — it names the mod-editable item table by path; 0 direct callers, so how it is entered is UNKNOWN. |
| `0x140FFAE10` | 3,372 | `LoadChallengeItemPickerData`, `rom_picker_rebel_drop_vehicles`, `rom_picker_rebel_drop_weapons`, `rom_picker_default` | none in first 40 | **yes (menu data)** — the Rebel Drop picker's `rom_picker` names; 1 caller. Menu, not spawn. |
| `0x140D18910` | 210 | `rebelsupport.unlock_rebel_drop`, `rebelsupport.cancel_drop`, `rebelsupport.give_max_beacons`, `rebelsupport.reset.timers` | `rcx+0x138` at `0x140D1891A` (`lea rdx, [rcx + 0x138]`) | **yes (script names)** — a table of `rebelsupport.*` script event names; the `rcx+0x138` load is the table it hands on. No entity. |
| `0x141027EC0` | 1,137 | `rebel_drop`, `fast_travel`, `chop_shop_waypoint`, `map`, `tutorials` | `[rcx]` at `0x141027F11` (`mov qword ptr [rcx], r14`) | **yes (map/UI names)** — fast-travel and map marker names; the closest thing to a teleport consumer in the image, and it is a UI/marker name table, not a graph binding. |
| `0x140A16150` | 3,954 | `RebelDrop`, `Abilities`, `CheckActiveMission`, `AreObjectsTethered`, `AddToVariable`, `ButtonHint` | none in first 40 | **partly** — `RebelDrop` appears in a table of script condition/action names (`CheckActiveMission`, `AddToVariable`), i.e. a name the script layer can test; it is not a spawn call. 2 callers. |
| `0x140A02830` | 2,734 | `CSpawnSystem`, `CAmbientSpawnUtil`, `CAISystemJC3`, `CCharacterManager`, `CAmmunitionManager` | none in first 40 | **no** — a managers/update table; the ambient spawner's system list. 2 callers. |
| `0x140A07540` | 115 | `CSpawnRule` | none in first 40 | **no** — 38 callers, a class-name accessor (typeid-shaped). |
| `0x140A0C1E0` | 9,950 | `CAIEntityProxy`, `CAITrafficSpline`, `CAIRoadObstacle`, `CAirTrafficImpostorSystem` | none in first 40 | **no** — AI traffic, not the player's car. |
| `0x1409DBE40` | 62 | `CDespawnVolume` | none in first 40 | **no** — a 62-byte type-name stub; the only "despawn" verb in the image. |
| `0x14061BC60` | 115 | `CEntityObject` | none in first 40 | **no** — class-name accessor, 4 callers. |

Spawn diagnostics are present and referenced, which is what proves the spawner exists in the image
(**decoded** string sites): `Trying to spawn vehicle (fail reason=` at `0x14249FC48`, referenced at
`0x140D7C2F2` and `0x140D7D8AD`; `Trying to spawn (fail reason=` at `0x14249FA10`, referenced at
`0x140D7B5D9`; `on_vehicle_spawn_conditions_are_met_event` referenced at `0x140DB8FB4`. These are
the ambient/roadblock spawner's failure paths, and their strings name *vehicles*, but the functions
around them do not reference `/profile/item.onlinec` (the item-table reach set is 7 functions, and
none of them is these).

---

## 5. The three paths the brief names

**5.1 Garage / Rebel Drop spawn path.** What is decoded is the chain up to the menu and the item
schema: `0x140CC75A0` (Item member names) → `0x140CC82A0` (the `profile/item.onlinec` path) →
`0x140FFAE10` (`rom_picker_rebel_drop_*`) → `0x140D18910` (`rebelsupport.*` events, one of them
`unlock_rebel_drop`). **No function in that chain is identified as "take the item hash, create the
entity".** The entity creation is UNKNOWN: it is either behind one of the 348-caller thunks, or
behind an indirect call the `E8`/`E9` scan cannot resolve.

**5.2 Mission vehicle-replacement scripts.** Nothing in the image is named for it: the census has no
`replace`/`respawn` term with a reference, and the only `despawn` verb is `CDespawnVolume` (§4). The
archive search already found 0 `replace`/`respawn`/`despawn` paths. The two together make "a mission
graph replaces the car" **unsupported**: no path, and no named consumer.

**5.3 Teleport graphs (11 paths, three graphs).** The image carries `fast_travel` and
`chop_shop_waypoint` beside `rebel_drop` in one 1,137-byte function (`0x141027EC0`) — so
fast-travel/teleport *names* exist — but no per-graph binding, no `Teleport` action name, and no
reference to the three `.gsc` graph names (they are not strings in the image; **decoded**: 0
occurrences of any `teleport`-named term in the census because none survived a reference check).
How a graph's target reaches an actor stays **UNKNOWN**; it is a script-binding question, not a
string one.

---

## 6. UNKNOWN, each with the five-minute test that would settle it

| # | unknown | why it is still open | test |
|---|---|---|---|
| E1 | what `0x140CC8C66`'s thunk does with the `SRebelSwap` comparison | the target is a `jmp qword ptr [rip+…]` thunk, not in `.pdata`; its body is behind an IAT-style table | resolve the pointer at `0x141EBB0B4 + 6 + 0x3E7AB6` in a debugger and read the target's first bytes |
| E2 | whether any shipped table instantiates `SRebelSwap` | data question; the image cannot answer it | `grep -i rebelswap Research/JC3Grab/INDEX.jsonl` (expected 0, per the archive report) and grep the extracted `.bl`/`.onlinec` set for the literal |
| E3 | whether `0x140CC8950` is reached at all at runtime | 0 direct callers | set a breakpoint on `0x140CC8C5F`, load a save, request a Rebel Drop; hit or no hit is the answer |
| E4 | what argument `0x140CC8950` takes | no register dereference in the first 40 instructions; it is a leaf of the call graph | read `rcx` at the breakpoint (E3) and follow it |
| E5 | whether the item-hash → entity step exists in the image | not in the 7 item-reaching functions | breakpoint on `0x140CC82A0` (item-table path) and step out to its caller |
| E6 | whether `CDespawnVolume` can be pointed at a vehicle | it is a type-name stub in this scan; 0 entity-arg evidence | one in-game test: place/aim a despawn volume at a car and watch the entity id |

Every one of E1–E6 is a *reading* of the same bytes at run time; none of them needs a build change,
and none of them is claimed here.

---

## 7. Limits of the method

* Rip-relative only. A name pointer stored in a table and loaded through that table is missed
  unless the table entry itself is referenced; `SRebelSwap`'s single `lea` is a direct reference, so
  this limit does not affect the main finding, but it does affect the "0 callers" statement.
* Caller edges are `E8`/`E9` rel32 only. Indirect calls (`FF /2`) are not resolved, which is why a
  function with 0 callers here may still be called.
* `.pdata` chunks define function bounds. The thunk at `0x141EBB0B4` is **not** covered by
  `.pdata`, so it has no function record; that is a fact about the image, not a tool failure.
* Strings are counted as exact NUL-terminated names after suffix pruning; a name embedded in a
  longer unrelated string is not counted.
* Nothing in `Research/JC3Grab/ENTITY_SWAP.md` or this report is a value, a member or a behaviour
  the game was observed to have — only what its bytes carry.

## 8. Reproduce

```
uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --write
uv run --with pefile --with capstone --with numpy python Tools/scripts/exe_entity_swap.py --check
```

`--check` re-derives the PE parse, every string occurrence, every reference site, every function
row, the suffix-pruning invariant and the byte identity of both generated files; it prints
`OK: 13/13 checks` on the image analysed here.

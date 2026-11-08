# Routes for adding new logic or data to Just Cause 3 — the carrier survey

Reference document. Every later carrier brief in this project points here instead of re-deriving
what JC3 can be made to do. Scope: **every route that exists or is documented** for adding logic or
data to JC3, whether it is shipped, proven in this project, or only described in the knowledge base.

Sources, and how they are cited below:

* `C:/Users/User/source/repos/universal-modder/knowledge/games/just-cause-3/` — three notes:
  `reading-the-vehicle-fleet-archives-rtpc-havok.md` (**FLEET**),
  `vehicle-mesh-editing-added-geometry-loads-with-matching-toc.md` (**MESH**),
  `translating-the-batmobile-row-ledger.md` (**LEDGER**).
* `…/knowledge/techniques/` — `static-address-native-hooks-ini-dll.md` (**HOOKS**),
  `installers-load-order-and-loaded-code-checks.md` (**INSTALL**),
  `oracles-how-agents-know-a-mod-works.md` (**ORACLES**).
* This repo: `Research/JC3Grab/` (**REBELDROP**, **STANDALONE**, **ENTITIES**, **FX**,
  **VOCABULARY**), `MODLOG.md`, `tmp/freebuff/rules.txt`, `Tools/scripts/`.

Label legend: **[decoded]** file carries the bytes and a project tool reads them; **[derived]** rule +
stated inputs; **[UNKNOWN]** what was tried and the file that would settle it. Test-ban status is per
route: `offline-provable` = a check runs on the built files today; `in-game-only` = needs a launch,
therefore unprovable today (`tmp/freebuff/rules.txt`: "THE TEST BAN STAYS (no installing, no install
scripts, no launching a game)"; `tmp/freebuff/APPROVED_Q.txt` **absent**).

---

## 0. Change statement (AGENTS.md)

| item | value |
|---|---|
| intended change | add one report: the route survey every carrier brief cites |
| file | `tmp/freebuff/reports/new-behaviour-routes-survey.md` (this file) |
| why this file | the brief names it; project reports live under `tmp/freebuff/reports/`; all evidence is read-only |
| reverted by | deleting this file. No other write: no `Research/`, `Tools/`, `Working/`, `Builds/` edit; no build, no install, no launch |

---

## 1. The route matrix

| # | route | can change | cannot change | evidence | status |
|---:|---|---|---|---|---|
| R1 | **Dropzone override at a vanilla VFS path** (`.ee` + matching `.ee.toc`) | any inner file of an existing `.ee`: meshes, textures, modules, `.epe`, effects, tunes, audio refs | file *sizes* stay consistent only with a regenerated `.toc`; nothing about code | MESH §"The .ee.toc"; `Tools/scripts/eetoc.py` docstring; MODLOG §14 (test-003 loads) | proven in game before the ban; offline-provable |
| R2 | **Standalone `.ee` at a new path** | a whole new entity, no global registry edit on path-keyed routes | the Rebel Drop *hash* binding for a new leaf is UNKNOWN | STANDALONE §1, §4, §5 | structurally derived; in-game-only for the hash question |
| R3 | **In-place `.vmodc` value edit** (same size) | every existing module member value (handling, camera, damage, weapons, doors, wheels) | adding a member that is not in the ADF type table; changing array counts | `t5_apply.py` docstring + `apply_file()`; `vmodcdiff.py` docstring; FLEET "6,045 `.vmodc`, 1,421 member paths" | offline-provable (size + re-read assertions) |
| R4 | **ADF append** (new arrays / strings / string-hash entries) | array contents, strings, new string-hash rows; new records in profile tables | new *members* in a type; moving existing data | `adf_append.py` docstring ("grow … append, never shift") | offline-provable (round-trip + `--check`) |
| R5 | **New entity graph** (`.epe`) | parts list, weapon points, lights, interaction entry/exit, effects tables, health/invulnerable, camera ref | new *classes* the game does not ship; behaviour that has no class | `bm_entity.py` docstring; ENTITIES class inventory; MESH Gotcha 1 (pad-restored `.epe` loads) | offline-provable (ConvertProperty round-trip) |
| R6 | **Private copies of tunes** (`.ctunec`) | camera behaviour (splines, collision, shake, FOV, follow) | anything not in a camera-tune class; no new tune class | FX §`.ctunec` (6,455 files, 34 root classes); STANDALONE §2 (`.ctune` 23,977 refs) | offline-provable (ADF round-trip) |
| R7 | **Private copies of effects** (`.effc`, `.trim`, `.pfxc`) | particle/effect graphs, trims, emitter params, render-block data | new modifier/emitter *types*; new render-block types without a codec | FX §`.effc` (25,025 files, 94 member paths); STANDALONE §5 (74 `.effc`, 60 `.trim`, 4 `.pfxc` inside the donor) | offline-provable (row digest + object census) |
| R8 | **Rebel Drop item data** (`profile/item.onlinec`) | whether an entry exists, its menu slot, icon, timer, display order; the *spawn binding* by leaf hash | price (no field exists); the `.ee` must exist under the hashed leaf | REBELDROP §2, §4, §7; `bm_rebel.py` (Q-1a history) | offline-provable (decode + re-read); menu behaviour in-game-only |
| R9 | **Task / unlock data** (`profile/task.onlinec`) | how an item is granted (task reward, permanent, quantity, delivery) | a grant that no task implements | REBELDROP §3, §7 step 5; `bm_rebel.py` (three unlock variants tried) | offline-provable; behavioural result in-game-only |
| R10 | **Spawn tables** (`settings/spawn_vehicle_defs.bin`) | add a record naming a new `.ee` **by path string** | whether an overridden `settings/*.bin` is honoured from the dropzone | STANDALONE §1, §3, §7.3 | offline-provable; honour question in-game-only |
| R11 | **Global entity registry** (`global/entityregistry_gen.entityregc`) | could add a leaf+hash record | no writer exists (39 MB tagged stream); incomplete anyway (251/922 leaves) | STANDALONE §2, §3, §7.4 | not provable offline (no writer) |
| R12 | **Physics** (`.physicsc`, Havok 2014 packfile) | existing hull remap, uniform scale, hull replacement; wheel-ray stations | adding a **new hull** (unnamed face-table prefix) | FLEET "Writing `.physicsc`", Open questions; `jc3hkx.py` | offline-provable for existing hulls |
| R13 | **Render blocks / materials** (`.rbm`) | CarPaintMM/Window/CarLight bytes, textures, block flags, material constants | `GeneralMkIII` write (no serializer); new block types | `rbm_geom.py:708,743`; LEDGER "no public RBM authoring tool"; `G3-04e` | offline-provable (byte-exact re-encode) |
| R14 | **Textures** (`.ddsc`) | any surface colour/normal/mask; **new paths load** | streamed `.hmddsc` high mips override a vanilla-path texture | MESH §"The .ee.toc" bullet on new textures | offline-provable |
| R15 | **Audio** (FMOD events, `.fmod_guids`, banks) | which event a slot fires, event→tune pairing inside a bank | tune→wave mapping (0 of 649 stored) | FLEET "Audio"; LEDGER "Audio" (53 rows, 45 events) | offline-provable (bank parse) |
| R16 | **Strings / icons** (`profile/online.stringlookup`, `ui/store` `.ddsc`) | display name, description, icon framing, icon art | any behaviour | STANDALONE §5; `bm_rebel.py`; FLEET "Strings and icons" | offline-provable |
| R17 | **DLL / native hooks** | anything code decides: new modes, HUD readouts, camera overrides, spawns, property-file interception | nothing is documented as safe; no SDK; per-build addresses | MODLOG.md:995 (`xinput9_1_0.dll` proxy, `add_event_hook.inject`), MODLOG.md:7481 (native HUD setters), HOOKS (technique) | **in-game-only**; no offline oracle for code |

Two shipped-mod facts worth carrying: the Batman mod's 0 changed RBMs across 634 files
[MODLOG.md:187], and the console-thingy's hooking of the **property-file reader** to lift one
property from every property file loaded [MODLOG.md:995] — that is the only documented DLL route
that changes *what the game knows*, not just what it renders.

---

## 2. R1 — the dropzone override (the load-bearing route)

A JC3 vehicle's editable content is **one `.ee`** (AAF container around a SARC) at a fixed VFS path
[MESH §"Route and why"]. The game reads a dropzone `.ee` **through** the sibling `.ee.toc` — a flat
`u32 name_len, name, u32 offset, u32 size` directory [MESH §"The .ee.toc"; `eetoc.py` docstring].

| fact | evidence |
|---|---|
| a repacked `.ee` at a vanilla path is applied by the game | MESH; MODLOG §14 (test-003) |
| a stale `.toc` is the cause of every "structural change crashes" verdict in the early project | MESH Gotcha 3 |
| offset 0 in a `.toc` means "read from the archives", so a modified file left at offset 0 is **ignored** | MESH §"The .ee.toc" |
| regenerating the `.toc` from the SARC directory is the correct write | `eetoc.py` (`compare` / `write`), `generate_toc.py` |
| a binary diff of two dropzones is a complete offline regression test | `dropzone_sim.py` (`--snapshot`, `--compare`) |

**Can:** replace geometry, materials, textures, modules, `.epe`, effects, tunes, audio references
inside one existing entity; add inner files (with a matching `.toc`).
**Cannot:** change code; make the game read a path that no table names (that is R2/R10/R8);
add a *new* `.rbm` path that the vanilla entity never had — ship meshes at vanilla `.rbm` paths
[MESH §"The .ee.toc", bullet 5]. New `.ddsc` paths **do** load [MESH, same section].

---

## 3. R2 — a standalone entity at a new path

Answer from STANDALONE: **yes to the loading, UNKNOWN to the hash.** A new leaf needs no global
registry edit for the routes that name the entity by **path string** (spawn tables hold the full
`editor\entities\...ee`), and the global registry is not a gate: 163 of 169 debug spawn records and
13 of 21 DLC records are unregistered, and one unregistered DLC vehicle is retail-playable
[STANDALONE §3]. The one route that names the entity by **32-bit leaf hash** is the Rebel Drop item,
and no shipped counter-example resolves a new leaf [STANDALONE §4].

| what a standalone needs | measured |
|---|---|
| one `.ee` (AAF + SARC) | donor: 604 inner files, 10,737,057 B [STANDALONE §5] |
| inner families | `.rbm` 198, `.ddsc` 153, `.effc` 74, `.trim` 60, `.lod` 59, `.vmodc` 31, `.ctunec` 18 [decoded, same table] |
| `.toc` | present in the donor (506 entries) but **optional** — the shipped mod has 20 `.ee` and 0 `.toc` [STANDALONE §4.4] |
| references | one spawn-table record (path) or one Rebel Drop item (hash), optionally a string + icon [STANDALONE §5] |

`Tools/scripts/jc3standalone.py` is the census/check tool; `bm_build.py` is the build scaffold.

---

## 4. R3/R4 — ADF module members: value edits vs new members

A `.vmodc` is ADF v4 with an embedded type table; 6,045 files, 52 module types, 1,421 member paths,
3,111,689 value rows [FLEET "Bundles and ADF v4"; `VOCABULARY.md`]. The project's writer works
**in place**: decode with Gibbed `--e`, assert the old value, write the new value at the element's
`offset-in-file`, re-import, assert size and that no other member moved [decoded: `t5_apply.py`
`apply_file()`].

| capability | status | evidence |
|---|---|---|
| change any existing member value | **proven path** (edit list `Working/Translation/t1_edits.json`) | `t5_apply.py` docstring |
| keep size identical | required by the vanilla `.toc` unless regenerated | `t5_apply.py` ("assert the `.vmodc` size did not change"); MESH |
| add a **new member** to a module type | **not supported**: the member list lives in the ADF type table; no tool rewrites it | `adf_append.py` header (only arrays/strings/string-hash entries) |
| add a **new array element / string / string-hash row** | supported, append-only | `adf_append.py`: `add`, `add_string`, `array`, `repoint`, `add_string_hash`, `build` |
| locate what a mod changed without its source | supported (byte diff + typed decode) | `vmodcdiff.py` docstring |
| read any ADF stat/module/tune offline | supported | `adfdump.py`, `jc3adf.py` |

So "a new ADF module member" is **R4 with a type-table rewrite**, and that rewrite does not exist in
this project or the knowledge base: [UNKNOWN], settled by writing an ADF type-table editor and
proving it on a copy whose vanilla round trip is byte-identical.

---

## 5. R5 — a new entity graph

The `.epe` is an RTPC property container; 103 classes across the fleet, 11,041 `CPartProp`,
3,972 `SVehicleLight`, 5,342 attached + 4,344 dynamic effects, 300 `SWeaponPoint` [ENTITIES;
FLEET "The entity graph"]. The build path is `ConvertProperty --e` → named-member edits →
`--i`, with the pad bytes restored (a naive re-encode crashes; with pads it loads and drives)
[MESH Gotcha 1; `bm_entity.py` docstring].

| can | cannot | evidence |
|---|---|---|
| add parts (`CPartProp`), repoint part names and indices | invent a class the game does not ship | ENTITIES class inventory (0 unknown classes needed for the Batmobile) |
| add/move `SWeaponPoint`, weapon components, light entries, interaction objects, effects tables | express a weapon trigger the class family lacks (`T-WP5` has no trigger in the files) | `bm_entity.py` docstring "Limits" |
| set root `health`, `invulnerable` | express partial invulnerability (all-or-nothing int32) | FLEET "Damage"; LEDGER "Armour" |
| keep the camera reference | reach HUD movies | `bm_entity.py`; LEDGER "HUD" |

Pointer to the pads trap: **any** `.epe` writer must restore the pad bytes, or the entity crashes
on load [MESH Gotcha 1]; the round-trip oracle is `ConvertProperty` producing identical XML.

---

## 6. R6/R7 — private copies of tunes and effects

Effects, camera tunes and trim are **ADF v4, not a bespoke format**: 25,025 `.effc`
(`EffectRTSystem`), 6,455 `.ctunec` (34 root classes), 25,707 `.trim` (`EffectTrimData`), 57,187 files
and 62,504,473 rows decoded with 0 failures [FX; `jc3fx.py`].

| can | cannot | evidence |
|---|---|---|
| change any value in an existing effect graph: timelines, emitter params, modifier params, render-block data | add a modifier/emitter type the schema does not declare | FX §`.effc` member table |
| change camera behaviour: `GenericVehicleCamera`, `CameraCollisionParams`, `FollowSpringModifierParams`, `SphericalCoordinateFramingParams`, splines | add a new camera tune class | FX §`.ctunec` root-class list |
| ship the file inside the entity's `.ee` under its existing path (private copy) | make the entity reference a *new* tune path without an `.epe` edit | STANDALONE §5 inner file counts |
| verify offline | — | FX "Validation": row digest + object census |

The entity registry lists the dependency extensions the game associates with an entity
(`.eff` 81,531, `.ctune` 23,977, `.etune` 1,211, `.wtune` 980, `.ftune` 539) [STANDALONE §2] — that
is the list of what a private copy can shadow.

---

## 7. R8/R9 — Rebel Drop item data and the unlock

A drop entry is an `Item` whose `Name` is the **32-bit Jenkins hash of an entity leaf name**; there
is no entity-path field and no price field anywhere in the table [REBELDROP §1, §2]. 196 vanilla
items, 591 tasks; 80 vehicle drops; 185/196 hashes resolve to an `.ee` in `INDEX.jsonl`
[decoded, REBELDROP §4]. Base layout is 25 members/128 B; the patch layout adds `DlcId` at 8 and
shifts five ints [REBELDROP §1].

| can | cannot | evidence |
|---|---|---|
| add a drop entry bound to a leaf hash, with menu slot, icon path, timer, display order | set a price (no field) | REBELDROP §2 "Cost: there is no cost field" |
| gate it behind a task reward (permanent, quantity, delivery) | make the menu accept an entry with no granting task | `bm_rebel.py`: (1) donor unlock → LOCKED on a passed save; (2) no reward → "Err: No Valid locking reason"; (3) starter task's repeatable reward → works |
| add text via `profile/online.stringlookup` (11 languages) | resolve a hash to a string from these files alone | REBELDROP §8 |
| set up to 45 added entries in a shipped mod (pattern) | prove that *absence* of a reward is what makes an entry available | REBELDROP §6 (mod evidence, rule UNKNOWN) |

Tools: `jc3rebeldrop.py` (`--write/--check`), `bm_rebel.py` (writes item/task/strings/icon into
`Builds/bm-013`), `adf_append.py` (the append mechanics).

---

## 8. R10/R11 — spawn tables and the global registry

`settings/spawn_vehicle_defs.bin` holds 86 base records, each `entity` (full path string) + `tags` +
`name`; 101 of 196 distinct spawn leaves are referenced with **no** registry record [STANDALONE §1,
§3]. The global registry is a tagged stream (`03 <len16> <leaf>` + 32-bit hash + asset paths),
33.0 MB base + 39.2 MB patch, covering 251 of 922 index leaves [STANDALONE §2].

| route | status |
|---|---|
| add a spawn record naming a new `.ee` by path | writable in principle; **whether an overridden `settings/*.bin` is honoured from the dropzone is UNKNOWN** [STANDALONE §7.3] |
| add a registry record | **no writer**; not attempted; the stream's record set criterion is native [STANDALONE §7.4] |

---

## 9. R12 — physics: what a build can and cannot add

`.physicsc` is a **Havok 2014.1 packfile** (`57E0E057`), not a property file; 233 files, 18,865
convex hulls, 4,791 collision meshes [FLEET "Collision"]. A packfile **writer** exists and its round
trip is byte-identical (2/2 files, 54 hulls), with remap, uniform scale and hull replacement passing
their checks [FLEET "Writing `.physicsc`"].

| can | cannot |
|---|---|
| remap, scale or replace existing hulls; move the four wheel-ray stations (must be moved together with `land_global`) | **add a new hull** — the face table has an unnamed prefix [FLEET Open questions] |
| keep collision following the render mesh (extern-mesh shape follows the loaded `.rbm`) | give a new moving part its own collision body without a new hull |

Consequence for any behaviour that needs a new collidable part: the closest carrier is an existing
hull slot (11 Batmobile bodies → 7 donor slots, LEDGER "Collision"), and the gap is the face-table
prefix.

---

## 10. R13/R14 — render blocks and textures

`rbm_geom.py` decodes/encodes `CarPaintMM` (`:708`) and generic blocks (`:730`), and **raises** for
`GeneralMkIII` (`:743`, `encode_block`) — 940 `GeneralMkIII` blocks are framed and decoded but not
writable [FLEET "Render blocks"]. Block types nameable from the published enum include `General`,
`GeneralJC3`, `BavariumShield`, `WaterDisplacementOverride`, `Prop`, `0x90FE086C`
[FLEET "Render blocks"].

| can | cannot |
|---|---|
| rewrite any CarPaintMM/Window/CarLight block: constants, flags, texture table, vertex data | emit `GeneralMkIII` (no serializer); add a new block type |
| ship new `.ddsc` at new paths (they load) | beat the streamed `.hmddsc` high mips at a vanilla path [MESH §"The .ee.toc"] |
| stay inside the hard budgets (Vehicle-HD Model [4096, 4915] KB, Texture [6144, 7065] KB) | exceed them — the whole vehicle vanishes, no crash [MESH §"Memory budgets"] |

---

## 11. R15 — audio

`.ee.fmod_guids` lists the vehicle's events (45 on the donor) across three banks; inside a bank every
`TLNB` body is `[16-byte tune GUID][16-byte owning event GUID]`, so **event → tune is stored on both
sides (257/257) while tune → wave is not (0 of 649)** [FLEET "Audio"; LEDGER "Audio"].

| can | cannot |
|---|---|
| choose which event a vehicle slot fires; retarget event→tune inside a private bank copy | find the wave behind a tune from the game's data alone; add a new event id without a bank writer |
| verify offline by parsing the bank | verify audibly without a launch |

---

## 12. R16 — strings, icons, HUD

Display names are `profile/online.stringlookup`, keyed by `hash_jenkins(leaf)`, 11 languages
[FLEET "Strings and icons"; `jc3strings_write` per `bm_rebel.py`]. Icons are
`textures/ui/vehicle_icons/<leaf>.ddsc`, copied under the new leaf [decoded, `bm_rebel.py`].

No entity reaches `hud.gfx` [LEDGER "HUD"]: HUD rows map to vehicle weapon slots, reticle and
cooldown setters. The one native HUD pair that exists (`RHudModuleExtraSequence.SetSpeedBar`,
`RHudModuleLocalRadar.SetBatmobileRevDisplayActive`, MODLOG.md:7481) is **BmAK-side** evidence and a
JC3 host for it is UNKNOWN.

---

## 13. R17 — script or DLL hooks: what is documented

There is **no JC3 script API** in either source. What is documented:

| evidence | what it shows | limit |
|---|---|---|
| MODLOG.md:995 — `aaronkirkham/jc3-console-thingy`, shipped as a 359 KB `xinput9_1_0.dll` proxy; `add_event_hook.inject(...)` hooks the game's **property-file reader** and lifts one property from every property file loaded | a DLL route that influences spawns by adding property data, not by patching code | `0xF71C2A21` (the harvested property) is in none of the 24 local `.epe` files — where the spawn name is read from is UNKNOWN [MODLOG.md:995] |
| MODLOG.md:7481 — `RHudModuleExtraSequence.SetSpeedBar`, `RHudModuleLocalRadar.SetBatmobileRevDisplayActive` | native HUD entry points exist in BmAK; a JC3 equivalent is not decoded | BmAK, not JC3 |
| HOOKS — the documented technique for "no source, no loader API, no script hook": INI-driven DLL, `WriteMemory`, `MakeNOP`, `MakeJMP`/`MakeCALL` into naked code caves with saved exits | this is the general route for changing magic numbers, limits or control flow | assumes a **32-bit statically-based** exe with ASLR off (HOOKS §"When to use it", `0x400000`); gotchas: version drift, multiple patch sites, cave-exit corruption, INI location |
| INSTALL — load order, loaded-code checks, ownership manifests, DLL replacement | how a hook DLL must be shipped so it loads early and uninstalls cleanly | Steam-wrapped exes are decrypted in memory, so file hashes do not prove the loaded code |

**What a hook can change:** anything the code decides — a mode switch, a HUD readout, a camera
override, a spawn, a property value injected at load, a new dirt/wetness driver.
**What it cannot:** be verified by any current project oracle (there is no offline check for code),
be version-stable (addresses), or be shipped under the test ban.

**Provability:** `in-game-only`, and worse than that — a hook has **no offline oracle at all** in
this project, so under the current rules it is not a build route, only a named route. The structured
alternative to a hook is to move the decision into data (R3/R4/R5/R8) and let the game's own reader
see it; the console-thingy's property-reader hook is the documented precedent for exactly that.

---

## 14. Community tools and the formats each owns

| tool | format | what it does | evidence |
|---|---|---|---|
| `tim42/gibbed-justcause3-tools-fork` (`SmallUnpack`, `SmallPack`, `ConvertAdf`, `ConvertProperty`, `HashName`, `ConvertTexture`) | `.arc/.tab`, `.ee` (AAF/SARC), ADF v4, RTPC `.epe`, `.ddsc` | unpack/pack archives, convert ADF/property, **`ConvertTexture` imports** (byte-identical round trip) | MESH Setup; FLEET Setup |
| stock Gibbed master `ConvertTexture` | `.ddsc` | exports element 0 only; `TextureFile.Serialize` throws | MESH §"Textures" |
| `aaronkirkham/jc-model-renderer` | RBMDL, `dictionary.json` (26,051 names) | block headers, DLC name source; **3 block types only, no vehicle RBM authoring** | FLEET Setup; MODLOG.md:980-990 |
| `aaronkirkham/ava-format-lib` | SARC/`.toc` | `StreamArchive::ParseTOC`, offset-0 semantics | MESH §"The .ee.toc" |
| `aaronkirkham/jc3-console-thingy` | DLL proxy + property hook | spawn command, property harvesting | MODLOG.md:995 |
| `Brooen/RBM-Exporter`, `PredatorCZ/ApexToolset` | RBM / Apex | mesh export/import reference | MESH links |
| Meme Vehicle Pack (videogamemods, lukejc3mp) | `.ee` | proof a custom vehicle ships publicly | MODLOG.md:980-983 |
| Rebel Drop Mod V5.3 (`Research/1456340180_Rebel-Drop-Mod-V5.3`) | `item.onlinec`, `task.onlinec` | working pattern for 45 added entries | REBELDROP §5, §6 |
| Unlimited Edition modpack (`Research/1784361515768-…`) | DLL + data | shipped modpack; raises the texture hard cap 7,065 → 113,040 KB | MESH §"Memory budgets"; MODLOG.md:995 context |
| project tools | — | `jc3adf.py`, `jc3fx.py`, `jc3hkx.py`, `rbm_geom.py`, `eetoc.py`, `dropzone_sim.py`, `adf_append.py`, `jc3rebeldrop.py`, `jc3standalone.py`, `t5_apply.py`, `bm_entity.py`, `bm_rebel.py`, `bm_build.py` | `Tools/scripts/` |

---

## 15. What the test ban makes unprovable, and the offline oracle that stands in

| behaviour | provable today? | offline oracle that replaces it |
|---|---|---|
| the dropzone override loads | **no** | `.toc` vs SARC directory compare (`eetoc.py compare`); `dropzone_sim.py --compare` against a known-good dropzone |
| a new-path entity loads | **no** | STANDALONE §4 structural proof; `.ee` inner-file census |
| a Rebel Drop item appears / spawns | **no** | decode the written `item.onlinec` and re-read every field; hash(leaf) = stored `Name`; leaf exists in the build |
| a task unlock grants the item | **no** | decode `task.onlinec`, assert the `ItemReward` row and its owning task |
| module value takes effect | **no** | `t5_apply.py` re-decode, size check, untouched-members check |
| effects/camera tune change | **no** | row digest + object census (`jc3fx.py check`) |
| new collision hull behaves | **no** | packfile round trip; per-part instance count; AABB containment |
| a DLL hook works at all | **no, and no offline oracle exists** | none — this is why R17 is not a build route under the current rules |
| anything visual | **no** | geometry/texture/budget measurements only (e.g. `spec_check.py`, band censuses) |

Rule: every brief that names a route must name which of these oracles it will run before the ban
lifts, and must not describe an in-game result as measured (ORACLES §"Be honest in the result").

---

## 16. Closest system + gap, per behaviour JC3 does not ship (STAGES.md)

| behaviour with no shipped carrier | closest documented route/system | gap the build fills |
|---|---|---|
| a runtime mode switch (pursuit ↔ battle) | R3 (module values) + R17 (hook) | data can hold two value sets; the switch needs code → closest is two entities/skins selected by drop entry; a true toggle is R17 and unprovable today |
| HUD speedometer | R5 (entity) + native HUD (MODLOG.md:7481) | no JC3 host decoded; closest is the existing weapon/reticle HUD members |
| per-chapter material animation (mud reveal) | R3/R4 (block values, mask authoring) | publish authored states (two drop entries) instead of a script |
| a new collidable moving part | R12 existing hull slot | face-table prefix unnamed → cannot add a hull |
| a new effect *type* | R7 existing modifier set | compose existing modifiers; a new type needs code (R17) |
| weapon trigger variants missing from the class family | R5 weapon components | pick the closest shipped trigger class; unknown trigger is `out` with evidence |
| per-pixel reflectance level on paint | R13 `GeneralMkIII` | block serializer missing (R13) |
| new module member | R4 + type-table rewrite | writer does not exist (UNKNOWN) |

---

## 17. UNKNOWN register

| unknown | tried | file/tool that settles it |
|---|---|---|
| whether a Rebel Drop item resolves a **new** leaf hash | no shipped counter-example; registry incomplete | one in-game drop item (Q-1 probe, STANDALONE §4) — gated on `APPROVED_Q.txt` |
| whether an overridden `settings/spawn_vehicle_defs.bin` is honoured | 86 base records read; no dropzone test | in-game spawn-table probe (STANDALONE §7.3) |
| new ADF **member** in a type | `adf_append.py` handles arrays/strings only | an ADF type-table writer + byte-identical vanilla round trip |
| new Havok hull | writer round-trips/remaps/replaces | the face-table prefix (`jc3hkx.py`, FLEET Open questions) |
| `GeneralMkIII` write | payload framed, no serializer | `Tools/scripts/rbm_geom.py` `encode_block` (G3-04e) |
| where `0xF71C2A21` (spawn property) is read | 0 hits in 24 `.epe` files | a property-file census of every file the game loads (MODLOG.md:995) |
| JC3 native hook surface / build addresses | none decoded | a static disassembly of `JustCause3.exe` (GRAB_BACKLOG.md:913 read-only disassembly card) |

---

## 18. COMPROMISES

1. No route here has been exercised in game during this survey; everything is file-level.
2. R17 is listed because it is documented and shipped in the wild, not because this project can use
   it under the test ban or verify it offline.
3. The "cannot" column is evidence-bounded: a capability nobody has written yet (ADF type-table
   editor, `GeneralMkIII` serializer, new hull) is recorded as UNKNOWN, not as an engine limit.
4. Route 11 (global registry) is documented from its bytes only; no writer was attempted.

---

## 19. Reproduce

```bash
cd E:/Modding/JustCause3/JC3-Batmobile
python Tools/scripts/eetoc.py compare <build.ee> <build.ee.toc>
python Tools/scripts/dropzone_sim.py --snapshot <dir> out.json
python Tools/scripts/t5_apply.py --aaf <tree> --check-only
python Tools/scripts/jc3rebeldrop.py --check
python Tools/scripts/jc3standalone.py --check
python Tools/scripts/jc3fx.py check
python Tools/scripts/spec_check.py <assembly_dir> <template.rbm>
```

Revert: delete this file.

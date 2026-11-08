# Standalone spawn check — what the Batmobile entity needs on disk, and what `Builds/bm-RC4` has

Sources: `tmp/freebuff/reports/G2-27.md` and `Research/JC3Grab/STANDALONE.md` (the standalone decode),
`tmp/freebuff/reports/B-06.md` (private weapon-entity copies). Tree facts below are read from
`Builds/bm-RC4` directly and are marked **measured**; everything else keeps the source's label
(**decoded** / **derived** / **UNKNOWN**).

**Answer in one line:** the RC4 tree carries **every on-disk item** a standalone entity needs — the
`.ee`, its `.toc`, the `.epe` graph inside the AAF, seven private tune/module copies, a spawn-table
record, a **Rebel Drop link that resolves by hash** (leaf hash `0x60A5E7A4`, **3** little-endian hits
in `item.onlinec`), a localisation label and a UI icon — and it has **no registry record**, which
`STANDALONE.md` §3 shows is not required for a load. What stays open is not on disk: whether a
dropzone-overridden `settings/spawn_vehicle_defs.bin` is honoured, and whether the `.toc` is ever
preferred. Of the eleven checks in §3, **two were run this session and both pass** (V6's tag test and
V7's hash test); the rest are specified.

---

## 1. What a standalone entity needs (from STANDALONE.md)

| # | item | requirement, with its source | evidence |
|---|---|---|---|
| N1 | **entity archetype** — one `.ee` at the leaf | donor `.ee` 10,737,057 B, **604** inner files (`STANDALONE.md` §5) | decoded |
| N2 | **AAF graph / EPE** inside that `.ee` | its own `.epe` ships inside the container (§5, "its own `.epe`"); inner names are independent of the outer leaf (§4.3) | decoded |
| N3 | **tune copies** | a private `.wtunec`/`.vmodc` per edited value, registered in `aaf/@files.xml` or SmallPack drops it (`B-06.md` Done 1 / tamper 4) | decoded |
| N4 | **one reference** so anything can ask for it | a record in an overridden `settings/spawn_vehicle_defs.bin` (**path string**) — "the route with no unknown" — or a `profile/item.onlinec` item whose `Name` is `hash(leaf)` (§5, §6) | decoded |
| N5 | **spawn record fields** | `entity` full path + `tags` + `name` (`TRAFFIC.md` §2; `STANDALONE.md` §1) | decoded |
| N6 | **registry record** | **not required**: 251/922 index leaves have one; **101 of 196** spawn leaves are referenced by path with none; a retail-playable DLC mech has none (§3) | decoded |
| N7 | **`.ee.toc`** | **optional**: the shipped mod has 20 `.ee` and **0** `.toc`; the donor's own has 506 records against 604 SARC entries (§4.4) | decoded |
| N8 | **name / icon** | optional: a `.stringlookup` entry and a `ui/vehicle_icons` `.ddsc` — "only affect the label, never the load" (§5) | decoded |
| N9 | **outer leaf ≠ inner paths** | the mod ships a *boat*-path `.ee` containing a playground-prop `.epe` (§4.3) | decoded |

## 2. What `Builds/bm-RC4` carries — measured

Tree: `Builds/bm-RC4/{aaf,drop,verify,install.ps1,receipt.json}`. `receipt.json`: card **B-14**, tag
`bm-RC4`, **leaf `v0300_car_kensington_sportsmuscle_debug`**, `complete: false`, `installed: false`,
`not_deployed: true`, AAF **696** files, `.toc` **714** records, banks
`sound/fmod_banks/vehicles.bank` + `weapons.bank`.

| # | item | present? | path | measured fact |
|---|---|---|---|---|
| N1 | `.ee` | **yes** | `drop/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee` | 11,225,533 B, sha256 `b72690d3…a557b` (`receipt.files`) |
| N7 | `.toc` | **yes** | `…_debug.ee.toc` beside it | **714** records, last record is the `.epe` path; 225 changed vs vanilla (`receipt.toc`) |
| N2 | `.epe` graph | **yes, donor name** | `aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_civilian_01.epe` | 9,025 XML lines after the 4-way merge (`receipt.steps`); the file keeps the **civilian** leaf name while the entity leaf is `_debug` — exactly the inner/outer independence STANDALONE §4.3 documents |
| N3 | private tunes/modules | **yes, 7** | `aaf/editor/entities/jc_weapons/06_vehicle/{w602_batmobile_cannon,w603_batmobile_vulcan,w618_batmobile_missile,w618_batmobile_emp_missile,riot_batmobile_suppressor}/…wtunec`, `…/autoaim_batmobile_emp_lockon.wtunec`, `aaf/editor/entities/jc_vehicles/01_land/…/batmobile_health_medium.vmodc` | 111 `batmobile`-path files in the AAF; `@files.xml` carries **111** `batmobile` rows → all registered |
| N4 | reference: spawn record | **yes** | `drop/settings/spawn_vehicle_defs.bin` | 27,785 B; record bytes `…\v0300_car_kensington_sportsmuscle_debug.ee\0` + `vehicle,batmobile\0` + `v0300_car_kensington_sportsmuscle_debug\0` — path + tags + name, the N5 shape |
| N4 | reference: Rebel Drop item | **yes, by hash** | `drop/profile/item.onlinec` (77,569 B) | **0** literal `batmobile` hits, but the leaf's Jenkins hash **`0x60A5E7A4`** occurs **3×** little-endian (0 big-endian) — the item keys the leaf by 32-bit hash (STANDALONE §1/§4); measured this session with `Tools/scripts/rbmhdr.py:hash_jenkins` |
| — | task table | **not carried** | `drop/profile/task.onlinec` (168,174 B) | 0 `batmobile` hits — expected: the chop-shop key is the donor's vanilla identity, and a standalone leaf should not inherit it (STANDALONE §1) |
| N8 | label | **yes** | `drop/profile/online.stringlookup` (1,746,322 B) | **22** `BATMOBILE` strings |
| N8 | icon | **yes** | `drop/textures/ui/vehicle_icons/v0300_car_kensington_sportsmuscle_debug.ddsc` | present |
| N6 | registry record | **absent, correctly** | `global/entityregistry_gen.entityregc` | no edit in the tree; allowed by STANDALONE §3 |
| — | banks | **yes** | `drop/sound/fmod_banks/{vehicles,weapons}.bank` | `receipt.banks_included` |

**Which it lacks:** nothing. N1-N5, N7 and N8 are all present, and N4's hash link is present **and
verified** (§3 V7); N6 is deliberately absent. `receipt.complete` is **false** for unrelated reasons (12 of 23 texture rows
unfaithful; B-10 collision shapes incomplete) — those are visual/physics gaps, not spawn gaps.

## 3. Verification, item by item — no game needed

| # | check | how (offline) | pass condition |
|---|---|---|---|
| V1 | `.ee` present and unchanged since the receipt | sha256 the drop `.ee` against `receipt.files[?].sha256` | equal bytes; `11,225,533` |
| V2 | `.ee` is the built container | open the `.ee` as AAF+SARC, count inner entries and extensions | count and extension histogram recorded; `_epe` present inside |
| V3 | every graph pointer resolves | run `python Tools/scripts/bm_weapons.py --check` (it already asserts "9 named by the `.epe` — 2 private, 7 shipped, 0 dangling") | **0 dangling**, 2/2 privates present, 2/2 registered in `@files.xml` |
| V4 | edited tunes re-read | `python Tools/scripts/jc3weapons.py --check --root Builds/bm-RC4` | `3/3 edits re-read, 2/2 tunes decode` |
| V5 | every AAF file is packed | count `@files.xml` rows vs files under `aaf/` (and the 111 `batmobile` rows against 111 `batmobile` paths) | equal counts, 0 unregistered |
| V6 | spawn record shape | decode `drop/settings/spawn_vehicle_defs.bin` (RTPC via `ConvertProperty -e`), then assert `entity` == the drop `.ee` path, `name` == the leaf, and `tags` contain none of `ambient`,`car`,`ground`,`liberated` | record present, path exact, **0 of 41** traffic selectors match |
| V7 | drop item resolves the leaf | compute Jenkins hash of `v0300_car_kensington_sportsmuscle_debug`, byte-search `drop/profile/item.onlinec` for it in both byte orders | **run: PASS** — `0x60A5E7A4`, 3 LE hits, 0 BE; 0 hits would mean the item points elsewhere |
| V8 | no registry record is needed | search the two `entityregistry_gen.entityregc` blobs for the leaf and its hash | 0 records, and the count of path-spawned leaves without records is ≥1 (STANDALONE §3: 101) |
| V9 | `.toc` is consistent or honestly optional | count `.toc` records vs SARC entries in the `.ee`; compare with the donor's 506-vs-604 | counts recorded; a mismatch is allowed (N7) but must be in the receipt |
| V10 | diff is only what the cards planned | `python Tools/scripts/aafdiff.py <base>/aaf Builds/bm-RC4/aaf` | `120 differ, 120 planned, 0 unplanned` (`receipt.aafdiff_rc2`) |
| V11 | the tree is not half-installed | read `receipt.installed` / `not_deployed` | `installed: false`, `not_deployed: true` — a stale dropzone copy is the failure this catches |

V1, V5, V6, V7, V9 and V11 are the six that decide "will it spawn"; V3, V4 and V10 are the pointer and
byte checks that decide "will the thing that spawns be ours".

**Run this session (offline, read-only):** V7 → PASS (`0x60A5E7A4`, 3 LE hits in `item.onlinec`, 0 BE)
and V6's tag half → PASS (the record's three strings are the `_debug` `.ee` path, `vehicle,batmobile`,
and the leaf name; the tag set matches **0 of 41** traffic selectors at string level).

## 4. UNKNOWNs, each with the file that settles it

| # | unknown | settles |
|---|---|---|
| U1 | whether a dropzone-overridden `settings/spawn_vehicle_defs.bin` is honoured at all | G2-27's own open question (`G2-27.md` UNKNOWN 3); the settings loader in `JustCause3.exe`; a one-file drop probe |
| U2 | whether an item hash resolves a leaf with no registry record | `STANDALONE.md` §4.5/§7 U1 — one Q-1 drop item, no file decides it |
| U3 | whether the `.ee.toc` is ever preferred when present | `STANDALONE.md` §7 U5 (eetoc's hypothesis); the `.toc` reader in the exe |
| U4 | whether an AAF inner instance name (`w602_mediumtank_canon.wtune` inside a `…_batmobile_cannon` copy) is load-bearing | `B-06.md` limit 3 — no file in the corpus answers it |
| U5 | whether the `_debug` leaf is the final spawn target or a stand-in for the standalone leaf D-6 chose | `MODLOG.md` Q-1a entries (new paths do not spawn; `_debug` is the proven target) — the leaf can change without changing any other item |

## 5. Change record

1. **Intended change:** add one plan listing the on-disk items a standalone entity needs, which of
   them `Builds/bm-RC4` carries (with paths and measured facts), which it lacks, and one offline
   verification per item.
2. **File:** `tmp/freebuff/reports/standalone-entity-spawn-check-plan.md` — the brief names it; no
   build file, no `aaf/`, no `drop/` and no game file was modified.
3. **Revert:** delete this file. Nothing else changed.

**Limits.** Static only: nothing was packed, installed or launched, and the checks in §3 are specified
rather than run except where a receipt field already records the result (V10, and V11's flags). The
drop-item hash (V7) is the one check that can turn a "carried" into a "lacks", because the item's only
link is a 32-bit number.

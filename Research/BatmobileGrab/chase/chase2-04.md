# Chase2 04 — second pass on F-25 … F-32 (only F-25 is still open)

Scope: the rows of `Research/BatmobileGrab/chase/chase-04.md` that are **not** FOUND there. That file
found 7 of its 8 rows in the class default object and left exactly one open:

| row | field | pass-1 status | this pass |
|---|---|---|---|
| F-25 | `ImpactRoadAssistTimer` | STILL UNKNOWN (no shipped value) | **STILL UNKNOWN** — but the *source of its value* is now proven: it is seeded from `ImpactRoadAssistEnemyDuration` |

Every other row in chase-04 (`F-26` … `F-32`) is FOUND with provenance `decoded`, so it was not
re-chased. Read-only work: `chase-04.md`, `FOOTAGE.md`, `GRAB_BACKLOG.md` and every other document are
untouched; the shipped executable and packages were only read; nothing launched, nothing patched,
nothing committed.

`smart_search.py` was **not** used: the card's tool step asks for it only if
`tmp/freebuff/reports/smart-search.md` shows `STATUS: done`, and that report says
`STATUS: deferred (chase_candidates not done)` while `Tools/scripts/chase/smart_search.py` does not
exist (`ls: cannot access … No such file or directory`). The `chase_candidates.py` half now exists
(`tmp/freebuff/reports/chase-candidates.md` = `STATUS: done`), so a later pass can build and use it.

## F-25 · `ImpactRoadAssistTimer`

**STATUS: STILL UNKNOWN — and now provably *not a tunable*.** There is no shipped default anywhere
(unchanged from pass 1), and this pass shows what the field's value *is*: a per-frame countdown that is
**seeded from `ImpactRoadAssistEnemyDuration` (0x1760)**, the sibling field 8 bytes after it. A row
that asks "what value does this field ship with" has no answer, because the field never carries a
designed value — it is derived state.

- value + units: **none** (no default, no constant, no ini entry). The *ceiling* it is set to is
  `ImpactRoadAssistEnemyDuration` — 0.333 s in the shipped `Playable_Batmobile_SF` archetype, 1.5 s in
  `Default__RVehicleBatmobileBase` (both decoded in chase-04, provenance `decoded`).
- provenance of this row's own value: **—** (no value; nothing to build). The seeding relation is
  behaviour read from the executable, not a value, and is marked as such (R4: nothing here is
  `assumed`, and the relation is not used as a value).
- routes tried this pass: (a) package/CDO scan of every DLC and patch vehicle package, the whole
  install by name, and all ini files — new; (b) native: complete store census at 0x1758 (all widths,
  not just the two forms pass 1 matched) plus the seeding site and the update function — new;
  (c) captures — not applicable, with reason; (d) published — searched, nothing exists.

### (b) Native — the store census and the seed (new)

Pass 1 matched only `movss [reg+disp32], xmm` and `mov dword [reg+disp32], imm32`. A seed can also
arrive as a 16-byte SSE copy, an 8-byte copy, an x87 store or a GPR copy of the float bits, so
`Tools/scripts/chase/chase2_04_native.py` scans for **every store whose range overlaps
[0x1758, 0x175c)**: it collects every little-endian 32-bit displacement in [0x1728, 0x175c), starts each
window at the preceding INT3 padding, and keeps only instructions Capstone shows as a memory write whose
displacement + operand width covers the field.

Exactly **4** stores overlap the field in the whole 55,101,440-byte executable:

| # | VA | file offset | instruction | bytes | reading |
|---|---|---|---|---|---|
| 1 | `0x140051f08` | `0x51308` | `movss dword ptr [rcx + 0x1758], xmm0` | `f3 0f 11 81 58 17 00 00` | the `subss` **decrement** chase-04 found |
| 2 | `0x14005f386` | `0x5e786` | `mov dword ptr [rdi + 0x1758], eax` | `89 87 58 17 00 00` | **the seed** — `eax` is loaded from `[rdi+0x1760]` |
| 3 | `0x14010601c` | `0x10541c` | `mov qword ptr [rbx + 0x1758], rdi` | `48 89 bb 58 17 00 00` | an 8-byte **pointer** store — impossible for a 4-byte float field, so another class's layout |
| 4 | `0x1411920ac` | `0x11914ac` | `mov dword ptr [rbx + 0x1758], eax` | `89 83 58 17 00 00` | inside a bit-unpacking routine (it also writes `[rbx+0x15ac]`, `[rbx+0x1850]`); single-offset match, no corroboration — unattributed |

No 16-byte (`movups/movaps/movdqu`), 8-byte (`movsd/movq`), x87 (`fstp`) or byte/word store overlaps
the field anywhere, and no immediate is ever stored to it. So: **no constant is written to
`ImpactRoadAssistTimer` by any instruction in the executable.**

The seed, verbatim (file offsets `0x5e780`/`0x5e786`):

```
VA 0x14005f380  mov  eax, dword ptr [rdi + 0x1760]    ; 8b 87 60 17 00 00  ImpactRoadAssistEnemyDuration
VA 0x14005f386  mov  dword ptr [rdi + 0x1758], eax    ; 89 87 58 17 00 00  -> ImpactRoadAssistTimer
```

taken under a guard that skips the store:

```
VA 0x14005f37b  test rsi, rsi
VA 0x14005f37e  je   0x14005f38c                       ; no hit actor -> leave the timer alone
VA 0x14005f380  mov  eax, dword ptr [rdi + 0x1760]
VA 0x14005f386  mov  dword ptr [rdi + 0x1758], eax
VA 0x14005f38c  mov  eax, dword ptr [r13 + 0x10]
```

**Why this is `rdi` = `RVehicleBatmobileBase` and not a lookalike layout.** Attribution is still by
offset (the exe is stripped), but this site is corroborated by *seven* other fields of the same base
register in the same function, all matching `BMSDK_OFFSETS.json` → `classes.RVehicleBatmobileBase`:

| offset | field in `BMSDK_OFFSETS.json` | site |
|---|---|---|
| 0x1264 | `ImpactSparks` | `0x14005f2df` (`mov rdx, [rdi + 0x1264]`) |
| 0x1624 | `CrushDamageType` | `0x14005ee18` (`mov rdx, [rdi + 0x1624]`) |
| 0x162c | `RamDamageType` | `0x14005f098` (`mov rcx, [rdi + 0x162c]`) |
| 0x1710 | `ImpactSparksSizeName` | `0x14005f304` (`mov rdx, [rdi + 0x1710]`) |
| 0x1758 | `ImpactRoadAssistTimer` | `0x14005f386` |
| 0x1760 | `ImpactRoadAssistEnemyDuration` | `0x14005f380` |
| 0x1c00 | `DamageNumbers` | `0x14005f028` (`mov rdx, [rdi + 0x1c00]`) |
| 0x1cf8 | `VehicleShovingTorque` | `0x14005ef8d` (`movss xmm1, [rdi + 0x1cf8]`) |

Eight independently named fields agreeing on one base register is not a coincidence of a single
displacement, which is the standard chase-09 used to reject lookalikes. The function also branches on a
"rammed something" test and fires event calls (`call 0x140fa41f0` with static FName-like operands), which
fits a collision/road-assist handler.

**What the update function does *not* do.** The function that owns store #1 runs
`0x140051a60` … `0x1400517f7` (VA, 2,455 B, 401 instructions) and references 0x1758 exactly twice —
`0x140051ee2` (`movss xmm0, [rcx+0x1758]`) and `0x140051f08` (the store back after `subss xmm0, xmm1`).
It never reads 0x175c or 0x1760, so it neither seeds nor re-seeds the timer; the countdown and the seed
live in different functions, which is why pass 1 could see the decrement but not its origin.

### (a) Packages, class defaults, ini — the DLC/patch half (new)

Pass 1 read the class default objects inside `BmGame.upk` (235 `Default__*Camera/Batmobile/Vehicle*`)
and the 15 `Playable_Batmobile*` archetypes. This pass closes the DLC and patch side:

1. **Every `.upk` in the install by name** — `chase2_04_pkgscan.py`, 4,145 files / 18,271,910,197 B,
   chunked raw search for `ImpactRoadAssist`, `RVehicleBatmobileBase`, `Default__RVehicleBatmobile`:
   **2 files** contain any of them, and both are the global name cache:
   `BmGame\CookedPCConsole\GlobalPersistentCookerData.upk` (10 `ImpactRoadAssist` hits, 1,428
   `RVehicleBatmobileBase`, 84 `Default__RVehicleBatmobile`) and
   `DLC\350171\Content\…\GlobalPersistentCookerData.upk` (10 / 1,416 / 84).
2. **Why (1) is not the proof, and what is.** `BmGame.upk` itself contains **0** occurrences of
   `RVehicleBatmobileBase`, `StrafeCooldown`, `BattleModeWidth` or `ImpactRoadAssistTimer`, yet pass 1
   read their tags out of it — this install's package name tables are externalised into the global
   cooker data, so a raw string miss proves nothing. The structural test is the real evidence:
   `chase02_cdo.py --scan --offsets 0x1758,0x175c,0x1760,0x176c,0x1774,0x1778` run over **all 125
   packages whose name mentions `Batmobile` or `Vehicle`** (base *and* DLC, including
   `Playable_BatmobileClassic_SF.upk` (DLC 350172), `Playable_BatmobilePrototype_SF.upk` (DLC 350171),
   the MK2/Joker/MK2-Std/`Showcase_*` sets) — every package reports
   `→ 0 object(s) carry any of the card offsets`, i.e. **no Default__ object anywhere in the DLC/
   patch vehicle packages serialises any of these eight offsets**.
3. **ini** — all 20 `BmGame/Config/*.ini` and `Engine/Config/*.ini` grepped for `ImpactRoadAssist`:
   0 hits (also 0 for `RoadAssist`, 0 for `BatmobileBase`).
4. **`.u` script packages** — `find` over the install returns no `*.u` file: the game ships cooked
   `.upk` only, so there is no UnrealScript source to read defaults from.
5. The two `GlobalPersistentCookerData.upk` files themselves cannot be opened as packages
   (`upk_read.UpkError: not chunked and the name table is not where the header says`) — they are name
   caches, not objects; recorded as a limit, not as "no data".

Command and output (trimmed to the parts that carry the claim):

```
$ python Tools/scripts/chase/chase2_04_pkgscan.py
done: 4145 files, 18,271,910,197 B, 2 with any name, 312s
wrote E:\Modding\ArkhamKnight\_grab\chase\chase2_04_pkgscan.txt

$ for f in $(find … -iname "*.upk" | grep -iE "batmobile|vehicle"); do
      python Tools/scripts/chase/chase02_cdo.py --scan --offsets 0x1758,0x175c,0x1760,0x176c,0x1774,0x1778 --package "$f"; done
### …/DLC/350172/…/Playable_BatmobileClassic_SF.upk
package Playable_BatmobileClassic_SF.upk: version 863, licensee 32995, 3250 names, 974 imports, 5364 exports
   -> 0 object(s) carry any of the card offsets
… (125 packages, every one 0 objects) …

$ grep -rn "ImpactRoadAssist" "E:/Games/Batman - Arkham Knight/BmGame/Config/" "E:/Games/Batman - Arkham Knight/Engine/Config/"
(no output)
```

### (c) Captures — not applicable, with the reason

`C:/Users/User/Videos/Captures` holds **29** clips and `ffprobe` is available
(`…/bin/ffprobe`), so the route is runnable — but `ImpactRoadAssistTimer` is internal state with no HUD
readout, and the road-assist effect it gates (a nudge when the car hits scenery vs. an enemy vehicle)
is not separable from the other handling variables in those clips without controlling the one variable
per probe (R13). Fit for a titled in-game probe, not for frame timing of existing footage. No timings
are claimed.

### (d) Published sources — checked, nothing exists

Web search for `"ImpactRoadAssist" Batman Arkham Knight property default value` returns **no organic
results** (Google via Serper, 2026-10-29). There is no published value to cross-check, and per R4 a
published value could not outrank a file value anyway.

### What pass 1 left open, now closed or still open

| pass-1 leftover | this pass |
|---|---|
| "which of `ImpactRoadAssistSceneryDuration` / `…EnemyDuration` seeds the timer — not shown by any file read here" | **answered**: `EnemyDuration` (0x1760), at `0x14005f380` → `0x14005f386`. Provenance: native, read-only static (not a value) |
| "no immediate store for 0x1758" | **strengthened**: no store of *any* width or form anywhere writes a constant to it — only the decrement and the seed |
| "the store is the only write" | **refined**: 4 stores overlap the field; 2 are other layouts (8-byte pointer store; bit-unpacker), 2 are the batmobile's (decrement, seed) |

## Rows not re-chased

`F-26` 45.0 deg, `F-27` 0.25 s, `F-28` 30.0, `F-29` 1.0 s, `F-30`
`Batmobile_V2_Tank_Spread_Open_Game`, `F-31` 265.0 cm, `F-32` 430.0 cm — all FOUND in `chase-04.md`
with provenance `decoded` from `BmGame.upk` export 10923. Nothing in this pass contradicts them (the
independent CDO reads used here touch the same object and never saw a different value), so they are not
re-opened.

## Suggested `FOOTAGE.md` change (not applied — read-only)

F-25 stays `UNKNOWN`, but its *reason* can now be evidence instead of `VALUE-NATIVE`:

> **UNKNOWN** — no shipped default in any archetype, class default object, DLC/patch package or ini;
> the field is a runtime countdown seeded from `ImpactRoadAssistEnemyDuration` (0x1760) at exe VA
> `0x14005f386`, so it has no designed value to carry.

## Limits / UNKNOWNs of this pass

1. Attribution of the seed site is by field offsets on one base register, corroborated by eight
   co-located named fields; the exe is stripped and holds no symbol or string for the class.
2. Whether the *scenery* path also seeds the timer is **not** shown: no store of any width copies
   0x175c into 0x1758 anywhere in the executable, so if scenery hits set a timer they do it through
   code not found here — UNKNOWN, not asserted.
3. The structural DLC scan covers packages whose *name* mentions Batmobile/Vehicle (125). A subclass
   default object hidden in an unrelated package would not be covered by that filter; the whole-install
   name scan argues against it but cannot prove it, because name tables are external.
4. `GlobalPersistentCookerData.upk` (x2) is not parseable with `upk_read` — its content is counted by
   raw search only.
5. The update function's entry is taken from the INT3 padding before store #1; the seed function sits
   in a region with no padding within 16 KB, so its entry is not claimed, only the two instruction
   addresses.

## Reproduce

```bash
# route (b): every store that overlaps the field, with the enclosing function and callers
python Tools/scripts/chase/chase2_04_native.py 0x1758
#   -> 4 store(s) overlap [0x1758, 0x175c)  (seed at VA 0x14005f386, decrement at VA 0x140051f08)

# route (a) step 1: every .upk in the install by name
python Tools/scripts/chase/chase2_04_pkgscan.py
#   -> done: 4145 files, 18,271,910,197 B, 2 with any name, 312s

# route (a) step 2: every DLC/base vehicle package, structurally
for f in $(find "E:/Games/Batman - Arkham Knight" -iname "*.upk" | grep -iE "batmobile|vehicle"); do
  python Tools/scripts/chase/chase02_cdo.py --scan \
    --offsets 0x1758,0x175c,0x1760,0x176c,0x1774,0x1778 --package "$f"
done
```

Extracted data (outside the repo, R10): `E:/Modding/ArkhamKnight/_grab/chase/chase2_04_pkgscan.txt`,
`E:/Modding/ArkhamKnight/_grab/chase/chase2_04_native.json`.

# Review — G3-01e `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`

Reviewed: `tmp/freebuff/reports/G3-01e.md`, `Research/BatmobileGrab/COLLISION_SELECTOR.md`,
`Research/BatmobileGrab/COLLISION_SELECTOR.json`, `Tools/scripts/grab_collision_selector.py`.
Byte sources re-read directly with `Tools/scripts/upk_read.py` (imported, unmodified) and with
throw-away probes that do **not** call the card's functions: `BmGame.upk` (export 10894, 10701),
`Startup.upk` (7399, 7400, 7401, 7402), `Research/BatmobileGrab/runtime/samples-*.jsonl`.
Corpus test re-implemented separately for the branch-encoding claim.

Disclosure: this session also produced the card. To avoid common-mode error every spot-check below is
a fresh byte read with its own inline probe, and the one claim I could not reproduce is reported as
**false** rather than excused.

## VERDICT: **needs rework**

The byte-level decode is real and I reproduced it: 5/5 spot-checks match, and the value→mesh table
survives an independent reading (same export `k` on the detach and the attach side). The
branch-encoding UNKNOWN is justified — I reproduced the corpus rejection (9.6% vs the card's 10.2%,
51.3% of words longer than their own script).

But the card states as **decoded** a fact the bytes contradict: that the two `DriverLeft` branches'
"guard regions" name `BatmobileWinch`/`WinchPullType` and `ArmouredMode`/`IsVehicleAsleep`. Those
names are **not in that function's script at all** (issue 1). The runtime narrative also drops one of
the four `0→1` transitions and misstates its own denominators (issues 2–3). Both are small edits, but
a decoded label that the bytes do not support has to be removed, not softened.

## Check output (verbatim)

Command:

```
cd "E:/Modding/JC3-Batmobile" && PYTHONIOENCODING=utf-8 uv run python Tools/scripts/grab_collision_selector.py --check; echo "CHECK_EXIT=$?"
```

Output:

```
OK selector export 10894, 253 script bytes, 7 calls, 7 comparisons
mesh table: {0: None, 1: 'BatmanCollisionMeshPursuitMode', 2: 'BatmanCollisionMeshBattleMode'}
callers: {'BmGame.upk': 1, 'Startup.upk': 5} constants: [0, 1, 2]
runtime values: {'0': 17, '1': 6} transitions: 7
oracles: {'call_set': True, 'caller_constants': True, 'comparison_shapes': True, 'layout_anchors': True, 'mesh_pair_symmetry': True, 'mode_1_implies_driver_absent': True, 'old_new_split': True, 'runtime_driver_rule': True, 'runtime_in_caller_range': True}
CHECK_EXIT=0
```

Identical to the block in the report (same 4 lines, same oracle set, exit 0). Note only: the report's
`--write` block prints the oracle dict in hash order, which is not reproducible run-to-run; `--check`
prints it sorted. Cosmetic, but the report's `--write` block is not a reproducible artifact.

## Spot-checks (5, my own reads)

| # | value as claimed | my source | match |
|---|---|---|---|
| 1 | export 10894, 291 B export / 253 B script, sha1 `c2f6a2ee667c544876e5317a103072c44ea17788`, class `Function`, outer `RVehicleBatmobileBase` | `pk.data(10894)` → 291 B; `data[22:-16]` → 253 B; `sha1` → `c2f6a2ee667c544876e5317a103072c44ea17788`; `object_path`/`object_class`/outer → as claimed | **yes** |
| 2 | guard @35 `0x9A`, left property `BatmanVsBatmobileCollisionMode` (9777), right byte `1` | bytes 35–47: `9a 38 3a 01 31 26 00 00 38 3a 24 01 16`; ref `0x2631`=9777 → `RVehicleBatmobileBase.BatmanVsBatmobileCollisionMode`; const `24 01`=1 | **yes** |
| 3 | call @48 `Core.DetachComponent`, arg `BatmanCollisionMeshPursuitMode` (9797) | bytes 48–58: `1c 0d fa ff ff 01 45 26 00 00 16`; `0xFFFFFA0D`→import `Core.DetachComponent`; `0x2645`=9797 → `…BatmanCollisionMeshPursuitMode` | **yes** |
| 4 | calls @224/@234 `SetBatmanCanClimb` (FName 69762), args `False`/`True` | bytes 224–240: `1b 82 10 01 00 28 16 06 4d 01 1b 82 10 01 00 27 16`; name `0x00011082`=69762=`SetBatmanCanClimb`; `28`=EX_False, `27`=EX_True | **yes** |
| 5 | caller constants: BmGame `StartSelfDrive` 0; Startup `DriverEnter` 0, `DriverLeft` 2 then 1, `OnWakeRBPhysics` 0, `OnSleepRBPhysics` 1 | raw call sites (`1b <nameidx> 24 <byte>`): 10701@13→0; 7399@237→0; 7400@301→2; 7400@334→1; 7401@17→0; 7402@54→1. `0xE495`=58517=`SetBatmanVsBatmobileCollisionMode`, `0x11085`=69765 same | **yes** |

Checked beyond the five: startup name table has no `Function` export for the selector
(`selector_exports: []`), so "lives only in `BmGame.upk`" holds; the context at 146 is
`19 01 a9 fb ff ff …` = `Core.CollisionComponent` (−1111); the SetCollisionFilter import is −2278.

## Issues

1. **BLOCKING — guard-region names are not in the bytes.** The report says: "2 on the other
   `DriverLeft` branch (its guard region names `BatmobileWinch` and `WinchPullType`; the 1-branch's
   region names `ArmouredMode` and `IsVehicleAsleep`)". I read `Startup.upk` export 7400
   (`RVehicleBatmobile.DriverLeft`, 368 B script) directly:
   - its only `1b` (call-by-name) tokens are @213 `RemoveBatmobileBindsAndSetBatmanBinds` (56660),
     @301 and @334 `SetBatmanVsBatmobileCollisionMode` (58517);
   - no 5-byte export ref in the script (prefix `00`/`01`/`1c`) resolves to any object whose path
     contains `Winch`, `Armoured` or `Asleep`;
   - the four names exist in the package name table (5340, 64413, 2020, 29901) but are never used by
     this function.

   So those names cannot have been read from the script they are attributed to — a naive 5-byte
   window scan over this bytecode returns coincidental export indices (I reproduced that failure
   mode: it "resolves" `1b 95 e4 00 00` as an export ref to `Ww_UI_FrontEnd.Play_…`, which is
   nonsense). The claim is prose only: `callers` in the JSON carries `call_at`/`argument`/name index
   and **no** region-ref field, and no oracle covers it, so `--check` cannot catch it. Fix: delete
   both sentences and the `(ArmouredMode, WinchPullType, IsVehicleAsleep)` clause of UNKNOWN #5, or
   replace them with the actual guard bytes decoded by the existing walker and label the result
   `derived`/`UNKNOWN`.

2. **Runtime denominators are wrong.** The samples contain 23 mode values, `{0: 17, 1: 6}`. A
   `Driver` field is co-sampled in only 21 of them: `11:48:22.898` (mode 0) and `11:48:24.093`
   (mode 1) carry no `Driver` key. Therefore "every sample with mode 1 has no driver seated
   (**5/5**)" is 5 of 6, and "seated (7) … dormant/no driver (9)" sums to 16 of 17. The claims are
   true of the co-sampled subset but the denominators silently drop a sample in each case; the doc
   should say "5 of 6 samples (one did not record `Driver`)" and "7 seated, 9 dormant, 1 not
   recorded".

3. **The transition narrative drops transitions.** Seven transitions = four `0→1` and three `1→0`:
   `10:05:15.778` 0→1 (Driver 0), `11:48:22.562` 0→1 (Driver 0), **`11:48:22.898` 1→0 (no Driver)**,
   **`11:48:24.093` 0→1 (no Driver)**, `11:48:25.206` 1→0 (Driver pointer 1529038352),
   `11:48:38.572` 0→1 (Driver 0), `11:53:43.969` 1→0 (Driver pointer). The report quotes only three
   rises ("the 0→1 transitions at … are exactly the exit events") and one fall ("the re-entry"),
   omitting the two bold records. The `11:48:24.093` rise has no driver evidence at all, so
   "exactly the exit events" is not supported for it. The caller set does explain a flicker
   (`OnWakeRBPhysics` passes 0, `OnSleepRBPhysics` passes 1), but the card must list all seven and say
   that the 22.898/24.093 pair is sleep/wake cycling, not a driver event.

4. **Row-0 label contradicts the table's own label.** `COLLISION_SELECTOR.json`
   `selector.mesh_table.rows[0].label` = `"decoded (constant appears in no mesh pair; …)"`, while
   `selector.mesh_table.label` and the verdict both call the table `derived`. Row 0's meaning
   ("attaches no collision component") is a rule applied to the *absence* of a constant — derived,
   not decoded. The absence itself is decoded; the semantic conclusion is not.

5. **Two oracles are too weak to test what the text claims.**
   `runtime_in_caller_range` only asserts `observed ⊆ {0,1,2}`, which passes for almost any mapping.
   `mode_1_implies_driver_absent` reads the crosstab, which is built only from co-sampled records, so
   it cannot see the 6th mode-1 sample (issue 2). Neither is false; both are stated as if they
   enforce more than they do.

6. **Status wording.** The report says "done, with **one** named UNKNOWN" while the doc lists six.
   The intended one is the branch encoding; the sentence should say so.

Not issues (checked and correct): the selector table is genuinely polarity-independent (same export
`k` on detach and attach; `0` in neither); the decoded negative is real (`SetHidden`,
`SetActorCollision`, `SetBlockRigidBody` occur nowhere in the 253 B body); the argument offset
convention (`@242` = the `24` token, value at 243) is consistent with `@53` in the selector table;
73 unexplained bytes = the 9 listed runs sum exactly (3+15+6+3+6+7+3+27+3).

## Resolvable UNKNOWNs

- **#5 (which `DriverLeft` condition selects 1 vs 2)** — not resolvable as written, because its
  premise is refuted: there are no guard-region name refs in that script (issue 1). What remains
  needs the branch encoding; the card should downgrade this to "the two call sites are at 301 and
  334 with constants 2 and 1 respectively; which predicate guards each is UNKNOWN".
- **#1 (branch encoding)** — the card's rejection is confirmed, not refuted. My own re-implementation
  over 74,582 `0x06`/`0x07` sites / 19,908 functions gives absolute-offset landing on a
  statement-start byte 9.6% (card: 10.2%), token-relative 1.2%, operand-end 1.3%, end-relative 2.9%,
  and 51.3% of words exceed their own script length (card: 51%). Resolvable only from a BmScript VM
  reference or a second build — not from these bytes.
- **#6 (callers in other packages)** — resolvable without brute force: scan each cooked package's
  **name table** for `SetBatmanVsBatmobileCollisionMode`, then decode only the packages that contain
  it. Startup keeps the name (58517) while having no `Function` export that calls it, which shows the
  filter must be "name present **and** a `1b` call site", not "name present". Not run here: 3,266
  packages / 44 GB is outside this review's budget.
- **#2/#3/#4 (operator meaning, `0x19` wrapper, raw control words)** — no local oracle; nothing in
  `Research/` or `Tools/` decodes `0x9A`/`0x9B`, and the corpus test rules out the offset reading of
  the branch words. Remain UNKNOWN.

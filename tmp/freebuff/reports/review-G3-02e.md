# Independent review — G3-02e (native mode flags, the 0.707 test, the exit route)

Reviewed 2026-11-03. I did not write this card. I re-read `BatmanAK.exe` static bytes with my own
`pefile` + `capstone` passes (`.pdata`-aligned), independent of the card's `Image`/`flag_sites`
helpers, and re-read `BMSDK_OFFSETS.json` directly. The game was never launched or attached; nothing
was written except this file; `--write` was not run.

Files reviewed: `tmp/freebuff/reports/G3-02e.md`; `Tools/scripts/grab_controls_native2.py`
(647 lines); `Research/BatmobileGrab/CONTROLS_NATIVE2.md` (145 lines); `CONTROLS_NATIVE2.json`
(60,408 B); `Tools/scripts/grab_controls_native.py` (imported, read for `array_of`/`direct_calls`);
card at `GRAB_BACKLOG.md:1029`.

## VERDICT: **minor issues**

The decode is solid. Every address, instruction, count and byte offset I re-read is exact, including
the ones that are easy to get wrong (15 immediate + 10 computed writes, 170 displacement
occurrences, 165 inside `.pdata` functions, the 347/75 zero-caller arrays, the 5 body call sites).
The status `partial` is honest and correctly scoped.

What needs fixing is **claim strength, not decoding**:

- the (c) conclusion names `ProcessEvent` as the dispatcher, which this card (and G3-02c) never
  decodes — it is UE3 mechanism knowledge;
- the (d) conclusion ("the executable holds no native route from the driving input handler to
  them") is stronger than the test: 0 direct callers is the *normal* shape of every exec thunk, as
  the card's own (c) shows (347/347 and 75/75), so it cannot speak to input routing;
- three minor count-definition problems (14 "test instructions", "callees 5/3", the doc's "31
  members each with its mask") and one truncation (`[:4]` field names presented as complete).

None of these changes a decoded value.

## 1. Check output (my run, verbatim)

```
$ PYTHONIOENCODING=utf-8 uv run --with numpy --with pefile --with capstone python Tools/scripts/grab_controls_native2.py --check
OK 31 flag masks, 15 write sites, 2 comparisons, 3 exit execs
oracles: {'flag_word_is_one_documented_bitfield': True, 'every_decoded_flag_reference_is_an_instruction_operand': True, 'mode_compare_constants_are_pm_0_707': True, 'float_load_chain': True, 'exec_thunks_have_no_direct_caller': True, 'exit_natives_have_no_native_input_link': True}
EXIT=0
```

Exit status 0. It matches the report's quoted `--check` block exactly. I did not run `--write`, so I
could not observe the write path; the `--check` message and oracle set are the ones the code
produces.

## 2. Spot-checks — five values labelled decoded, re-read from the raw source

| # | value in the record | my independent read | source | match |
|---|---|---|---|---|
| 1 | `0x10` = `bWeaponsReady`, set at `0x140058b62: or dword ptr [rbx + 0x11d8], 0x10` and cleared at `0x140058bc8: and dword ptr [rbx + 0x11d8], 0xffffffef` (report (a), doc §a) | decoding the function from its `.pdata` start `0x140058ad0` yields exactly `0x140058b62 or dword ptr [rbx + 0x11d8], 0x10` and `0x140058bc8 and dword ptr [rbx + 0x11d8], 0xffffffef`; SDK: 0x11d8 mask 16 → `bWeaponsReady` | `BatmanAK.exe` `.text` + `BMSDK_OFFSETS.json` | **yes** |
| 2 | `0x140063f04` compares against `0x141bf1cdc` = **-0.707**, `0x140063f22` against `0x141bce8f8` = **+0.707** (report (b)) | both floats read from `.rdata` as `-0.7070000171661377` and `0.7070000171661377`; `comiss xmm1, dword ptr [rip + 0x1b8ddd1]` at `0x140063f04` and `[rip + 0x1b6a9cf]` at `0x140063f22` resolve to those two VAs (`0x140063f04+9+0x1b8ddd1 = 0x141bf1cdc`) | `.rdata` + `.text` | **yes** |
| 3 | the load chain `0x140063ef5: mov rax, qword ptr [rbx + 0x38c]` then `0x140063efc: movss xmm1, dword ptr [rax + 0xd8]` (report (b)) | both instructions present, in that order, exactly as quoted | `.text` | **yes** |
| 4 | the request FName is `0x240` (`BattleMode`), compared at `0x140063ee5` / `0x140063eee` (report (b)) | `0x140063ee5: mov qword ptr [rsp + 0x30], 0x240` then `0x140063eee: cmp rdx, qword ptr [rsp + 0x30]`; `CONTROLS_NATIVE.md:63` records `BattleMode` = 0x240 (lea `0x140f5f9d1`, mov `0x140f5f9e1`) | `.text` + G3-02c doc | **yes** |
| 5 | (c): `DrivingPlayerMove` thunk `0x140501f60` has **0** direct call/jmp; body `0x140254560` has **1** (the thunk's tail jump); the code pointer appears as data at `0x14308fa78` and `0x14309a138`; the body calls the mode impl at 5 sites | E8/E9 rel32 scan: `0x140501f60` → 0 sites; `0x140254560` → 1 site at `0x14050207f`, which lies inside the thunk's `.pdata` range `0x140501f60–0x140502084`; qwords at both data addresses are `0x140501f60`; body call sites to `0x140063e90` are exactly `0x140254a4c, 0x140254a99, 0x140254aca, 0x140255f5e, 0x140255fc5` | `.text` + `.data` + `.pdata` | **yes** |

Extra reads done while checking, all matching the card:

- **occurrence/write census reproduced exactly**: 170 `0x11d8` displacements in `.text`, 165 inside
  `.pdata` functions, 5 outside; **15** immediate writes (11 `and`, 4 `or`) and **10** computed
  writes. Note for the record: my first pass scanned windows without `.pdata` alignment and got
  16/9 — the card's `.pdata`-aligned decode is the correct one, and my 16/9 was my error. The
  aligned pass reproduces the card's numbers to the instruction address.
- **no immediate writer touches bit 15**: none of the 15 immediate writes sets or clears `0x8000`
  (`eff & 0x8000` is false for all 15).
- **SDK word**: `RVehicleBatmobileBase` has **32** `BoolProperty` rows at `0x11d8`, **31** with a
  mask, `VulnerableToEMP` without one; masks `0x10`→`bWeaponsReady`, `0x8000`→`bBattleModeLocked`,
  `0x2`→`ArmouredMode` (the gate at `0x140063f45: test byte ptr [rbx + 0x11d8], 2`, which I also
  read at that address).
- **`0x38c`**: `Pawn.Mesh` (`ComponentProperty`) at 0x38c is the only match in the class chain;
  `RBasicProjectile.TargetActor` also sits at 0x38c but is outside the chain, so the card's
  chain-containment rule is what makes `Mesh` the answer. `0x38c % 8 == 4`, in line with every
  `Pawn` object property in the dump (all ≡ 4 mod 8), so the pointer load is not anomalous.
- **`+0xd8`**: zero properties at 0xd8 in **all 41** classes of `BMSDK_OFFSETS.json` — the card's
  UNKNOWN is correct.
- **exec arrays**: the table at `0x14309a130` is `{name ptr in .rdata, code ptr in .text}` pairs,
  zero-terminated; walking it gives a self-consistent array whose entries all carry `exec` names and
  `.text` code pointers.
- **(d) callee sets** (my own decode): `exit_set` 0 targets; `exit_check` 2 distinct targets, of
  which `0x140549011` is inside its own range (`0x140548f10–0x14054909e`) and the only external one
  is `0x140053850`; `eject_up` 1 distinct target, `0x140548eb3`, inside its own range
  (`0x140548d90–0x140548f0a`); body `0x140254560–0x14025633d` has 68 distinct targets. Intersection
  with the body's set is empty in all three cases, as the card says.

## 3. Issues

### I-1 · moderate — (c)'s "dispatched by FName through ProcessEvent" is not decoded here

The report's (c) conclusion: "So the caller is the script VM: the function is dispatched by FName
through `ProcessEvent`, and there is no native caller to name." The decoded part is only: 0 direct
call/jmp sites, and the code pointer lives in a name→code registration array (and as raw data at two
`.data` addresses). `ProcessEvent` appears nowhere in `CONTROLS_NATIVE2.*`, and `grep -i
processevent` over `CONTROLS_NATIVE.md` (G3-02c) also returns nothing. The name is UE3 mechanism
knowledge, i.e. exactly what the one rule forbids filling in. Fix: either cite a card that decodes
the dispatch (the `ProcessEvent`/exec lookup) or label the sentence as an inference and stop at
"the only references to this code are registration entries, so it is not called natively".

### I-2 · moderate — (d)'s negative is stronger than the test performed

Report (d): "a decoded **negative**: no native route from the driving input handler to the
exit/eject execs exists in the executable", and the doc: "the executable holds **no** native route
from the driving input handler to them". The test is (i) 0 direct call/jmp to each exec and (ii) no
immediate callee shared with the `DrivingPlayerMove` body. Neither can support that sentence:

- (c) itself proves that **every** exec thunk in both arrays has zero direct callers (347/347,
  75/75). A zero-caller result for three more execs is therefore the expected shape of exec code,
  not evidence about input routing.
- the callee test is nearly vacuous for two of the three: `exit_set` has no call/jmp at all
  (a stub), and `eject_up`'s only target is an internal branch, so neither *can* share a callee.
  `exit_check` has exactly one external callee (`0x140053850`) and it is not in the body's 68.
- the test cannot see indirect dispatch (vtable/`call qword ptr [...]`/VM), which is how the card
  says these functions are reached; `0x140056d9b: call qword ptr [rax + 0x3f8]` in the same
  package's flag code shows indirect calls are used here.

Fix: state what was measured ("no direct call-site and no shared immediate callee was found") and
say plainly that this cannot distinguish "no route" from "route through the dispatcher", so the
input→exit question stays open. That keeps the useful part (there is no *native call-site* link)
without asserting a negative the bytes cannot carry.

### I-3 · minor — the doc says 31 members "each with its mask"; the dump has 32 rows and one has no mask

`CONTROLS_NATIVE2.md` §(a): "`RVehicleBatmobileBase` declares **31** `BoolProperty` members at
`0x11d8`, each with its mask in the dump". Read from the dump: **32** rows at 0x11d8, 31 with a
`mask` field, `VulnerableToEMP` with none. The report's own §(a) and the doc's oracle detail
(`{"masked_fields": 31, "distinct_masks": 31, "dump_rows_without_mask": ["VulnerableToEMP"]}`) are
right; only that sentence is wrong, and "each with its mask" is contradicted by its own oracle.
Fix the sentence to "32 rows at 0x11d8: 31 with a mask (the 31-bit table below), one
(`VulnerableToEMP`) with no mask field".

### I-4 · minor — "14 `test` instructions" is a row count, not a count of test instructions

Doc §(a): "**14** `test` instructions near a reference"; the report repeats "14 register tests".
Measured: **40** `test` instructions in `.text` take `[r+0x11d8]` as an operand (e.g.
`0x140050753: test dword ptr [rbx + 0x11d8], 0x200`), and the card's 14 is the number of
(reference, test) pairs it emits — the same test appears under three different preceding
instructions (`0x14005683e` three times). Say "14 (reference, test) pairs covering 11 distinct test
instructions" (or drop the number from the prose and keep it in the JSON as `register_tests`).

### I-5 · minor — (d)'s "callees 5 / 3" are instruction counts that include internal repeats

`exit_check`'s five entries are `0x140549011` four times plus `0x140053850`; `eject_up`'s three are
`0x140548eb3` three times. Both repeated targets lie *inside the same function*, i.e. they are
branches, not calls to other functions. Distinct external callees: `exit_check` 1, `eject_up` 0,
`exit_set` 0. The shared-callee verdict is unaffected (it uses a set), but the table column should
be labelled "call/jmp instructions" and the text should give the distinct-external counts, because
"5 callees" reads as five functions.

### I-6 · minor — the vehicle-field name lists are truncated to four, silently

Doc §(b): "the other vehicle fields the implementation reads: 0x112c=…, **0x11dc=BatmobileAboutTo\
AboveOceanLevel/BatmobileAboutToHitWater/BatmobileAboveOceanLevel/BatmobileHitWater**, …". Those
are the first four names `props_at()` returns from a `[:4]` slice (`grab_controls_native2.py:333`),
not the fields the code uses. 0x11dc has 32 bools in the dump, and the instruction at
`0x140063f3c: test byte ptr [rbx + 0x11dc], 0x40` tests mask 0x40, which the same dump names
`bControlledBySeqAct` — a name the card could state and does not. Fix: mark truncation with `…` and
name the mask actually tested (`0x40` → `bControlledBySeqAct`), or list only the offsets the code
reads with their tested masks.

### I-7 · nit — report §"Card: who calls DrivingPlayerMove" tabulates "347 with zero direct callers 347"

That is correct, and the `fleet()` rule is stated. Worth one clarifying clause in the doc: zero
direct callers for every entry is *consistent with* dispatch and is also the reason I-2's (d) test
is weak. As written, a reader takes (c)'s 347/347 as proof of VM dispatch; it is proof that no exec
thunk is called natively, which is a different (and excellent) fact.

### Labels that held up

`0x10`/`0x8000` names from the dump's mask field; the 15 writes and their `and`/`or` effective
masks; "no immediate writer for 0x8000" (verified); the ±0.707 addresses and values; the
`[this+0x38c]` → `[rax+0xd8]` chain with `Mesh` named only because the chain contains exactly one
match; `+0xd8` UNKNOWN (0 hits in 41 classes); the 5 body call sites; the "mesh field name is
UNKNOWN" refusal in (b); and the honest U-3 rule for computed masks. The card also correctly reports
the two occurrences it could not map (`unmatched_in_functions: 2`) instead of hiding them.

## 4. UNKNOWNs I can resolve or narrow from the bytes

**U-2 (who sets `0x8000`) — narrower than "a full dataflow analysis", and the remaining work is 3
sites.** I decoded the 10 computed stores' immediate predecessors:

- `0x140056db5` — `mov r11d,[rbx+0x11d8]; lea/xor/and 4; xor eax,r11d` → read-modify-write of bit 2.
- `0x140058db2` — `mov eax,[rbx+0x11d8] … bts eax,0xa` → bit 10 (`AudioPlayingIn`).
- `0x140058e02` — same copy, `btr eax,0xa` → clears bit 10.
- `0x140069ac9` — `bts eax,0x17` → bit 23 (`SelfDriveUturn`).
- `0x140069b4a` — `btr eax,0x17` → clears bit 23.
- `0x14006b18c` — `and eax,0xfffffff7` → clears bit 3 (`bTransforming`).
- `0x14006b199` — `or eax,0x10` → sets bit 4 (`bWeaponsReady`).

None of these seven touches bit 15. So the only remaining candidates are the three computed stores
whose source register is not a copy of the word: `0x140056838: or [rbx+0x11d8], eax`,
`0x140058ae5: or [rcx+0x11d8], edx`, `0x14046c69b: xor [rdx+0x11d8], ecx`. The card should record
that (it turns "needs a full dataflow analysis" into "3 backward slices"), and it may not claim bit
15 is unwritten: the evidence still allows a script-side write or one of those three registers.

**U-1 (`[Mesh + 0xd8]`) — the blocker is the dump's class list, and that is fixable.** `Pawn.Mesh`
is typed `SkeletalMeshComponent`, but `BMSDK_OFFSETS.json`'s 41 classes contain **no
`SkeletalMeshComponent` entry** (list: Actor, ActorComponent, AkVehicle, Inventory,
LensFlareComponent, LightComponent, Pawn, PointLightComponent, PrimitiveComponent, Projectile,
R3rdPersonCamera, RBasicProjectile, RBatmobile…, RHelicopterSpotLightComponent, RInventoryGadget,
RProjectile, RPursuitModeMissileLauncher, RVehicle, RVehicleBatmobile, RVehicleBatmobileBase,
RVehicleSimBatmobile, RVehicleSimCar, RVehicleWeapon, SVehicle, SVehicleSimBase, SVehicleSimCar,
SVehicleWheel, SpotLightComponent, Struct, Vehicle). So "no property at +0xd8" is really "the class
that has +0xd8 was never extracted". The fix path is concrete: extend
`Tools/scripts/bmsdk_offsets.py` to emit `SkeletalMeshComponent` (and its parents) from the same
BmSDK-AK source, then re-run this card's `props_at` on that class. Until then, the card's UNKNOWN is
right, but its stated reason ("no property on Pawn or any class reachable here") should name the
missing class instead of implying the field does not exist.

**U-3 (computed masks)** — partly resolved by the same measurement as U-2: 7 of 10 are now resolved
to an explicit bit number, 3 remain.

**U-4 (script side of exit/eject)** — stays out of scope, correctly: it needs `BmGame.upk`, which
this card does not read.

## 5. What a corrected card needs

1. Reword (c): drop "through ProcessEvent" unless an existing decoded file is cited; keep
   "0 native call sites; the code pointer is only in a registration array".
2. Reword (d): "no direct call-site or shared immediate-callee link was found; the dispatcher route
   is not testable here". Keep the measured numbers, give distinct external callee counts.
3. Fix the doc's "31 `BoolProperty` members … each with its mask" to "32 rows, 31 masked".
4. Fix "14 test instructions" and "callees 5/3" definitions.
5. Un-truncate the field lists (or mark the `[:4]` slice) and name `0x11dc` mask 0x40 =
   `bControlledBySeqAct`.
6. Add the 7 resolved read-modify-write sites to U-2 and the missing `SkeletalMeshComponent` class to
   U-1.

The card's `partial` status is correct: (a) is answered with a mask and a writer for `0x10` and a
proven absence for `0x8000`'s immediate writer, (b) is decoded to the exact instructions and stops
where the dump stops, (c) is a real negative with a real (if over-interpreted) explanation, and (d)
is a real measurement whose conclusion needs the weaker wording above.

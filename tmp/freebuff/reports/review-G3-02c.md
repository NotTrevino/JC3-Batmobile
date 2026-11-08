# Review — G3-02c · BmAK native input path (`CONTROLS_NATIVE.md` / `.json`)

Independent review. I did not write this card. Read-only throughout: `BatmanAK.exe` (never launched,
never attached, bytes only), `BmGame.upk` via `Tools/scripts/upk_read.py`, `BMSDK_OFFSETS.json`,
the card, its JSON and `Tools/scripts/grab_controls_native.py`. Nothing was run except the card's own
`--check` and my own read-only decodes. No file outside this report was written.

## VERDICT: **minor issues**

The decoded core is sound. Every address, constant and count I re-read from the executable reproduced
exactly (6 of 6 spot-checks), `--check` is green, and no `decoded` value is refuted by the bytes. The
work is *not* rework-grade for its numbers.

The problems are all in the evidence framing, and one of them misdirects the next card:

1. One UNKNOWN's stated blocker is factually **false**: `DrivingPlayerMove` *is* an export of
   `BmGame.upk` (export 105252). The card tells the reader the static route is closed when it is not.
2. One negative claim stated as fact ("no threshold on it") is **contradicted** by the body's bytes.
3. Three of the five UNKNOWNs are resolvable statically today; one of them I verified end to end
   from the SDK dump.
4. A table caption claims 12 instructions and shows 4; one section and the UNKNOWN list disagree on
   whether the body has a caller (1 vs 0); the card's own Done condition (per-statement verdicts) is
   absent from the artifact.

None of these change an address. All of them change what a reader believes is still unknown.

## Check output

Command:

```
cd /e/Modding/JC3-Batmobile && uv run --with pefile --with capstone --with numpy python Tools/scripts/grab_controls_native.py --check 2>&1 | tee /tmp/g302c_check.txt; echo "EXIT=${PIPESTATUS[0]}"
```

Output (verbatim):

```
check: re-derived output matches the note - ok
EXIT=0
```

Noted limit: `--check` re-derives the note from the script and compares. It proves the note equals the
script's output — not that the script is right. The only independent evidence is the re-reads below.

## Spot-checks

Values re-read by me from the raw source (pefile + capstone on `BatmanAK.exe`; `upk_read` for packages),
not through the card's own code paths.

| # | card value | card label | my source | match |
|---|---|---|---|---|
| 1 | `trytochange` code = `0x140547ce0` | decoded | registration entry `0x1430a48b0`, 16 raw bytes | **yes** |
| 2 | `array_entries` = 75 / 347 / 4 | derived | arrays re-walked from the entry to both zero pairs | **yes** |
| 3 | `BattleMode` = `0x240`, `PursuitMode` = `0x241` | decoded | `0x140f5f9d1`…`0x140f5fa0b` registration block | **yes** |
| 4 | call sites `0x140254a4c/a99/aca` → impl with 0x240/0x240/0x241 | decoded | E8 rel32 + aligned decode from `0x140254a5c` | **yes** |
| 5 | `0x141bf1cdc` = −0.707, `0x141bce8f8` = +0.707 | decoded | 4 raw bytes each in `.rdata` | **yes** |

Also re-read (not counted in the five): the `DrivingPlayerMove` thunk→body link (yes), the ASCII counts
(yes), the `.pdata` function bounds used for every range (yes).

**1. Registration entry → code.** Entry VA `5419714736` = `0x1430a48b0`, raw
`7036e14101000000 e07c544001000000`: name pointer `0x141e13670` → `"ARVehicleBatmobileBaseexecTryToChangeMode"`
(exactly one 8-byte reference to that string in the image) and code pointer `0x140547ce0` in `.text`.
MATCH. The same check on `exit_set`, `battle_factor`, `driving_move`, `emp_lock` gave
`0x1404bdde0`, `0x1404bdb50`, `0x140501f60`, `0x1404bf8a0` — all identical to the JSON.

**2. Array entries.** Walking back to the first non-`exec` name and forward to the `{0,0}` pair:
`ARVehicleBatmobileBaseexec…` 75 entries (first `…GetCameraTrackingOffset`, last
`…IsAnyWheelOnCheckpointBlockade`), `ARPlayerControllerexec…` 347, `ARBatmobileEMPMissileexec…` 4.
MATCH.

**3. Name constants.** `0x140f5f9d1: lea rcx,[rip+0x1a49430]` → `0x1429a8e08` = `"BattleMode"`, then
`mov r9d,1`, `xor r8d,r8d`, `0x140f5f9e1: mov edx,0x240`, `call 0x140f57920`. The surrounding block
registers 0x238, 0x239, 0x23a, 0x23b, 0x23c, 0x23d, 0x23e, 0x23f, 0x240, 0x241 consecutively with the
same `call` — so "edx is a registration index" is supported by an invariant, not assumed. `PursuitMode`
→ `0x140f5fa0b: mov edx,0x241`; `CinematicMode` → `0x140f5f8bb: mov edx,0x239`. MATCH. (The `mov edx`
is 3 instructions after the `lea`, not 1 — the script's 8-instruction window is what finds it; the note
does not say so, which is why I checked the instruction at `0x140f5f9e1` directly.)

**4. Mode call sites.** `0x140254a4c`: bytes `e83ff4e0ff` → target `0x140063e90`; decoded window
`0x140254a2b mov eax,[rdi+0x11d8]` / `0x140254a31 bt eax,0x10` / `0x140254a37 mov qword ptr [rbp+0x180],0x240`
/ `0x140254a4c call 0x140063e90`. MATCH. The two sites MODLOG records as "not re-confirmed (my linear
disassembly desynced there)" both re-decode cleanly when started at an instruction boundary:
`0x140254a99` = `e8f2f3e0ff` → `0x140063e90` (0x240) and `0x140254aca` = `e8c1f3e0ff` → `0x140063e90` (0x241).
That caveat can be dropped.

**5. Float constants.** `0x141bf1cdc` = `f4fd34bf` = −0.7070000171661377; `0x141bce8f8` = `f4fd343f` =
+0.7070000171661377. Both in `.rdata` (`.rdata` starts `0x14195a000`), both consumed by
`comiss` at `0x140063f04` / `0x140063f22` inside `0x140063e90-0x140063fcb`. MATCH. (The note prints
−0.707 / +0.707, i.e. rounded; harmless, and the JSON stores the rounded value.)

**Extra — ASCII counts:** `XboxTypeS_LeftTrigger` 2, `XboxTypeS_LeftShoulder` 1, `aLeftTrigger` 0,
`aLeftShoulder` 0, `RBatmobileEMPMissile` 5, `DrivingPlayerMove` 1, `TryToChangeMode` 1,
`SelectVehicleWeapon` 0. All match the JSON. (See I-6 for what the count does *not* show.)

## Issues

**I-1 · `CONTROLS_NATIVE.md`, UNKNOWN bullet 1 — stated blocker is false (highest priority).**
Value: "the caller of `DrivingPlayerMove` (not an export of BmGame.upk; no native direct caller)".
`BmGame.upk` export **105252** = `RPlayerController.DrivingPlayerMove`, class `Function`, **43 bytes**,
name-table index 27723. (Also 105073 `RPlayerController.SelectVehicleWeapon`, 44 B.)
Why it matters: the parenthetical asserts the static route is closed, so the next card is told only a
runtime session can help. The real blocker is different: the export is a 43-byte native stub with no
bytecode — the same size as the confirmed-native `RPlayerController.PreProcessInput` (43 B) and
`RVehicleBatmobileBase.TryToChangeMode` (43 B), a derived comparison — so the caller has to be found in
*other* objects' bytes that reference it (name 27723 as a virtual-function name, or object 105252 as a
final-function reference).
I ran that search: across all `Function`/`State` exports the 8-byte pair (27723, 0) occurs twice — in
105252 itself (+35) and in **106013** (`RPlayerController`, 20,756 B) at +2036. The bytes at +2036 are a
regular 12-byte table of int32 triples (`0, 105254, 27723`, `0, 105252, 16791`), not a call token. So the
UNKNOWN may survive, but this evidence line must be rewritten: it is *not* "not an export".

**I-2 · `CONTROLS_NATIVE.md`, UNKNOWN bullet 2 — a negative claim the bytes contradict.**
Value: "what the float parameter is (the body moves it into xmm11 and passes it to two helpers; **no
threshold on it**)".
The body copies the incoming float (`xmm1` from the thunk's `0x14050206a: movaps xmm1, xmm6`) into
`xmm11` at `0x1402545ca: movaps xmm11, xmm1`. Later `0x14025623b: addss xmm1, xmm11` is followed by
`0x14025624d: comiss xmm1, xmm6` — a comparison on a value that contains the parameter. So "no threshold
on it" is unsupported; the defensible form is "no instruction compares xmm11 directly against a
constant; the parameter does enter a compare chain at 0x14025624b-0x14025624d". (Separately, "two
helpers" is an unevidenced count: `xmm11` is moved into `xmm1` at ≥8 sites — 0x140254902, 0x1402555b9,
0x140255baf, 0x140255bca, 0x140255be5, 0x140255c15, 0x140255c2d, 0x140255c45 — and which helper each
feeds is not shown.)

**I-3 · `CONTROLS_NATIVE.md`, "## ARPlayerController.DrivingPlayerMove(float)" — a jump counted as a caller.**
Value: "direct native callers of the body: 1 (decoded: E8/E9 scan of .text)".
The single hit is `0x14050207f: jmp 0x140254560`, the exec thunk's own tail jump (`0x140501f60-0x140502084`).
The body's caller count is **0**, which is what the UNKNOWN bullet says. The section and the UNKNOWN
disagree, and the table column "direct calls to code" / the helper `direct_calls()` matches `E8` *and*
`E9`, so the count silently includes jumps.

**I-4 · `CONTROLS_NATIVE.md`, mode-caller table caption — label overstates what is shown.**
Value: column header "window (decoded, 12 instructions before)"; every row prints 3 instructions plus the
call. Cause: `render()` uses `c["window_before"][-4:]` while the JSON stores 13 entries. The data is
fine; the caption is wrong.

**I-5 · `CONTROLS_NATIVE.md`, heading "(float)" — fact stated without label or address.**
The parameter type is asserted in the section title only. It is true and decodable from the card's own
address: the exec thunk `0x140501f60` reads the parameter with `movss xmm6, dword ptr [...]` on every
decode path (`0x140501f9d`, `0x140501fc8`, `0x140502002`, `0x140502010`, `0x140502040`) and passes it on
in `xmm1` at `0x14050206a`. One line with those addresses would make it a `decoded` claim; as written it
is an unlabelled fact.

**I-6 · `CONTROLS_NATIVE.md`, "Script-side and class names counted as ASCII substrings" — decoded count, unlabelled meaning.**
`XboxTypeS_LeftTrigger: 2` and `XboxTypeS_LeftShoulder: 1` are correct counts, but the section sits under
the controls card and a reader will read the hits as evidence that the Batmobile path uses those keys.
A substring count cannot show that; the same strings can be ordinary key-name table entries. The note
should say what a hit means ("the string exists in the image, nothing more") and what it does not.

**I-7 · Card Done condition not met in the artifact.**
The card's Done is "each user statement confirmed/contradicted by an address + instruction trace, or
UNKNOWN with what blocked it". The note never lists the five statements (LT hold/release → battle /
pursuit, B → track / immobiliser, barrage in battle mode, LB → exit, A → ejection) and gives no verdict
per statement; its five UNKNOWNs are generic. The tracker row states "5/5 UNKNOWN", so the verdicts exist
outside this file — but the file a later reader opens does not carry them.

**I-8 · UNKNOWN block hygiene (THE ONE RULE: "what you tried, where it would be found").**
Of the five bullets, only the first names what was tried. The others ("what the float parameter is", "the
identity of the vtable behind `call [+0x1120]` and `call [+0x280]`", "the identity of the weapon classes")
state neither method nor location. Also the implementation has **three** vtable calls —
`0x140063eb3: call [rax+0xaa0]`, `0x140063f8d: call [rax+0x1120]`, `0x140063fa8: call [rax+0x280]` — and
the UNKNOWN silently omits the `+0xaa0` one.

**What I checked and found *correct*, against the risk of a loose review:** the exec→code mapping and all
three array lengths; the registration-index reading of `edx` (consecutive 0x238…0x241 with the same
registration call); the `ld.` of the thunk ("its only non-indirect callee is 0x140063e90" — the thunk's
other calls are `[r9+rax*8]` and `[rip+0x353b3f4]`, both indirect); all five call sites and their FName
constants; the ±0.707 constants, their addresses and their consumers; the thunk→body link
(`0x14050207f jmp 0x140254560`, body `0x140254560-0x14025633d`); and the flag tests, which are
`bt eax,0x10` (0x140254a31, 0x140255f43) and `bt ecx,0xf` (0x140254a7e, 0x140255f8f), i.e. masks 0x10 and
0x8000 as claimed. One extra piece of support the note does not use: the implementation itself
materialises the constant — `0x140063ee5: mov qword ptr [rsp + 0x30], 0x240` — consistent with the
BattleMode reading (the instruction that consumes it was not decoded here, so this is corroboration, not
proof).

## Resolvable UNKNOWNs

**U-1 · "the meaning of the vehicle flag bits the body tests (`[vehicle+0x11d8]` bits 0x10 and 0x8000)" —
resolvable now, statically, and I verified it.**
`Research/BatmobileGrab/BMSDK_OFFSETS.json` → class `RVehicleBatmobileBase` declares **32**
`BoolProperty` members at offset `0x11D8`, each with its mask; `0x10` = **`bWeaponsReady`**, `0x8000` =
**`bBattleModeLocked`** (`0x2` = `ArmouredMode`). The two tests in the body are `bt eax,0x10` = mask 0x10
and `bt ecx,0xf` = bit 15 = mask 0x8000, so the mapping is exact. No runtime session was needed for this
— it is a decoded dump already in the project. (G3-02e has since recorded the same two names, which
confirms the UNKNOWN was resolvable at the time G3-02c was written.)

**U-2 · "the identity of the weapon classes behind SelectVehicleWeapon / ReleaseVehicleWeapon (script-only)" —
resolvable from `BmGame.upk`, not done here.**
The functions exist with real bodies, not as native stubs: `DrivingMode.SelectVehicleWeapon` export
104971 (**486 B**), `DrivingMode.ReleaseVehicleWeapon` export 104975 (**168 B**), `DrivingMode.ToggleBattleMode`
export 105028 (238 B), all class `Function`, outer `DrivingMode` — compared with the 43-byte stubs above.
Method: decode each export's token stream and resolve its object references.
My crude int32 scan of those exports already surfaces plausible targets —
`RVehicleBatmobileBase.ActualWeapons` (9853) and `ActualPMWeapons` (9852) in SelectVehicleWeapon,
`RBatmobileEMPMissile.SetLockOnTarget` (46848) in ReleaseVehicleWeapon, and `RVehicleBatmobileBase.ArmouredMode`
(9983), `bBattleModeLocked` (9969), `TryToChangeMode` (10552) in ToggleBattleMode — **but the same scan
also returns nonsense** (`Tick.RPC`, `AkBank` names, `ResetParameters`), so it is not an oracle and I do
not claim any of these as decoded. One proper token decode with an offset-accounting oracle closes this
UNKNOWN without touching the game.

**U-3 · "the caller of DrivingPlayerMove" — static route exists; my scan did not close it.**
See I-1. The claim "not an export of BmGame.upk" is false (export 105252). What is true: the export is a
bytecode-less 43-byte native stub, and a scan for a call token naming it found none — the only other
object containing the name pair (export 106013) is a 12-byte int32 table, not bytecode. So the UNKNOWN
stands, but for a different and correct reason, and the next card should search object references to
105252 rather than a runtime session.

**U-4 · "the identity of the vtable behind `[rax+0x1120]` and `[rax+0x280]`" — method known, not done.**
`rax` at `0x140063f8d` is loaded within `0x140063e90-0x140063fcb` (the first one, at `0x140063eb3`, comes
from `mov rax,[rcx+0x9c]; mov rcx,[rax+0x5ac]; mov rax,[rcx]` — a component pointer, not necessarily the
same base as the later two). Resolving the base at each site, then matching the vtable's entries against
`.pdata` function starts, identifies the class without running anything. Also still missing: why
`[rax+0xaa0]` is left out of the UNKNOWN list (I-8).

**U-5 · "what the float parameter is" — only partly resolvable, and it is gated on U-3.**
Its type is settled (4-byte float, `movss` in the thunk) and its use in the body is partly decodable (the
`xmm11` accumulator and the compare at `0x14025624d`); the *meaning* (delta time, or a state scalar) is
decided by the caller's argument, so it cannot be resolved before U-3.

## Bottom line

Keep the addresses; fix the evidence. Minimum edit to make this card sound: rewrite I-1's blocker, soften
I-2's "no threshold", make I-3's caller count 0 (calls only), fix I-4's caption, label I-5/I-6, add the
five per-statement verdicts (I-7), and add "what was tried / where it would be" plus the `+0xaa0` site to
the UNKNOWN block (I-8). Then move U-1 into the decoded section, since it is already answered by
`BMSDK_OFFSETS.json`.

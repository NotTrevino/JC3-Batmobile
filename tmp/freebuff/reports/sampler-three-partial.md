STATUS: DONE - three partly-answered sampler rows re-routed; 1 route produced new bytes (U3 press path), 2 remain missing their named input (U2 writer, U7 producer). `Tools/scripts/bmak_sampler_unknowns2.py --check` passes: the 126-line document rebuilds byte-identically (rc=0), all 8 oracles OK, and a one-word tamper is caught (rc=1). No game was run; nothing under an install was written; `SAMPLER_UNKNOWNS.md` and every other task's file are untouched.

## Files written

- `Tools/scripts/bmak_sampler_unknowns2.py` - new `--write` / `--check` generator (read-only inputs).
- `Research/BatmobileGrab/SAMPLER_UNKNOWNS2.md` - the three verdicts, 126 lines.
- `tmp/freebuff/reports/sampler-three-partial.md` - this report.

## The three rows and what the different route found

| U | named missing input | route tried | verdict |
|---|---|---|---|
| U2 | the UFunction body that writes `RVehicleBatmobileBase+5901` `BoostingOut` | decoded bytecode walk of `DrivingMode.EjectFromVehicle` (export 104931, 1297 script bytes) + independent walk of `BmGame.upk` | **still-missing** for the writer; **found bytes:** 6 tokens naming `BoostingOut` at script offsets 332, 338, 388, 394, 457, 463 (3 `EX_LocalVariable`+`EX_InstanceVariable` pairs). A reference is not a write; no `EX_Let`/`EX_LetBool` is present at those sites, and the walk is a reference scan, not a control-flow decoder. |
| U3 | the `QuickGadgetX` body and a meter field read in the same frame as the 783 edge | decoded `DrivingMode.QuickGadgetX` body (export 105040, 10 script bytes) + `SelectVehicleWeapon` call chain (export 104971, 448 script bytes) + meter-key census of both logs | **found-with-bytes** for the press path: the whole X handler is one virtual call `SelectVehicleWeapon` (FName index 69312) with the slot-2 constant, no branch and no field read. The gate chain is `IsButtonInputIgnored`, `ReadyToFire` x2, `IsFiring`, `TryToFireWeapon` x2. **still-missing** for the meter value: no record carries `WeaponGeneratorPower`/`WeaponUnavailableReason`; only `weaponword` was sampled and it is not decoded. |
| U7 | a device trace, a keyboard writer of `Button bCancelButton`, or the B `OnRelease` half | every decoded reference to `RPlayerInput.bCancelButton` (`property_consumers`, 14 refs) + re-read of every ini line in the consumer table | **still-missing** for the producer; **found bytes:** 14 refs in `RGadgetSelectBM3.Tick` (8), `RPlayerController.GetJapanesifiedButton` (4), `RSpecialMoveInstance_RelativeAnimMove.OverrideButtonIsBeingHeld` (2), all `EX_LocalVariable`/`EX_InstanceVariable` read pairs. Exactly 1 of the 40 ini lines carries `Button bCancelButton` (line 268, `XboxTypeS_B`); no keyboard writer exists in the decoded table. |

The taps themselves are unchanged and re-derived: 5 rises of 774, longest hold 0.154 s, first `2026-11-05T07:45:56.744Z`; the 783 edges are 4 rises, longest hold 3.354 s.

## Commands and verbatim output

```
$ python -m py_compile Tools/scripts/bmak_sampler_unknowns2.py; echo "compile rc=$?"; python Tools/scripts/bmak_sampler_unknowns2.py --write; echo "write rc=$?"; python Tools/scripts/bmak_sampler_unknowns2.py --check; echo "check rc=$?"
compile rc=0
wrote Research\BatmobileGrab\SAMPLER_UNKNOWNS2.md (126 lines)
oracles: {"boostingout_offset": true, "cancel_bind_writer": true, "cancel_refs": true, "eject_ref_sites": true, "no_meter_key": true, "quickgadgetx_body": true, "ready_before_fire": true, "tap_count": true}
  boostingout_offset: OK - offset 5901
  cancel_bind_writer: OK - writers ['268'] on XboxTypeS_B
  cancel_refs: OK - 14 refs in 3 functions
  eject_ref_sites: OK - 6 refs at [332, 338, 388, 394, 457, 463]
  no_meter_key: OK - meter-like keys []
  quickgadgetx_body: OK - 10 script bytes, 1 call(s)
  ready_before_fire: OK - ReadyToFire 2x, TryToFireWeapon 2x
  tap_count: OK - 5 rises of 774
write rc=0
OK Research\BatmobileGrab\SAMPLER_UNKNOWNS2.md byte-identical to a fresh rebuild
check rc=0
```

Tamper test (one word changed, then restored):

```
MISMATCH: regenerated document differs from the file on disk
tamper rc=1
OK Research\BatmobileGrab\SAMPLER_UNKNOWNS2.md byte-identical to a fresh rebuild
restored rc=0
```

Independent bytecode probe used for U2/U7 (read-only, `E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole\BmGame.upk`, 214,757,637 bytes, 177,031 exports), run with the repo's own token table and walker (`Tools/scripts/bmak_damage.py`, `D.SHORT_BODY` raised so the trace is returned):

```
==== DrivingMode.EjectFromVehicle script 1297 tokens 248
   332 EX_LocalVariable RVehicleBatmobileBase.BoostingOut
   338 EX_InstanceVariable RVehicleBatmobileBase.BoostingOut
   388 EX_LocalVariable RVehicleBatmobileBase.BoostingOut
   394 EX_InstanceVariable RVehicleBatmobileBase.BoostingOut
   457 EX_LocalVariable RVehicleBatmobileBase.BoostingOut
   463 EX_InstanceVariable RVehicleBatmobileBase.BoostingOut
==== DrivingMode.QuickGadgetX script 10 tokens 3
   0 EX_VirtualFunction RCombatMove_VillainMultiAttackAndCounter.ExitTimer
==== RVehicleBatmobileBase.GiveMaxEnergy 10369
tokens [(1, 'EX_InstanceVariable', 'WeaponGeneratorPower'), (7, 'EX_InstanceVariable', 'CurrentGeneratorLevel'), (12, 'EX_InstanceVariable', 'MaxWeaponGeneratorPower'), ...]
```

`GiveMaxEnergy` is the control case: the card's own §4 calls those three refs "the members of the assignment", and the walk still shows no `EX_Let`, which is why the `BoostingOut` pairs are labelled references, not writes. (The `QuickGadgetX` token name shown by the raw walk is an index-name artefact; the decoded walk in `CONTROLS_CONSUMERS.json` resolves the same token to `SelectVehicleWeapon`, which is what the document cites.)

## UNKNOWNs

- **U2 writer.** The eject body touches `BoostingOut` at three byte offsets, but the accepted-token walk cannot distinguish a read from a write (no Let token is decoded, including in the known-assignment control). Getting the direction needs a Let-aware expression-tree decode of export 104931, not another file. What was tried: `CONTROLS_CONSUMERS.json` walk, an independent `BmGame.upk` token dump, the BmSDK layout (`ByteProperty`, +5901), and the other Batmobile documents (they do not mention it).
- **U3 meter state at the 783 edge.** No captured record contains `WeaponGeneratorPower`, `WeaponUnavailableReason` or any generator key; `weaponword` is the only launcher state sampled and its bit meaning is not decoded anywhere in the repo. What was tried: both `samples2` logs (67 records), `DAMAGE_RULES`/`DAMAGE_LAYOUT_AUDIT` (reads of the field are decoded for `TakeDamage`, `DrainWeaponGeneratorForDamage`, `GiveMaxEnergy`, `LoadHealth`, not for a `ReadyToFire` state), and the `QuickGadgetX`/`SelectVehicleWeapon` bodies. The `ReadyToFire` state bodies are virtual and absent from the drivable class's package.
- **U7 producer.** All 14 decoded references are reads; the only decoded writer is the physical B line. A device trace at the five tap timestamps, or a Let-aware decode of `RGadgetSelectBM3.Tick`, or the native input path in `BatmanAK.exe` would answer it; none exists in the files read here.

STATUS: done — static map built from the exe bytes only (no game process opened, nothing attached, nothing written under a game folder). New tool `Tools/scripts/jc3_rtti_map.py` (`--write` / `--check`, check exit 0), new outputs `Working/RTTI/vehicle_rtti.json` and `.md` (690 vehicle-side rows of 5,259 RTTI names, 683 with a verified vtable).

# JC3 vehicle RTTI static map (2025-12-17 build)

Evidence base: `D:\Games\Just Cause 3\JustCause3.exe`, 51,083,264 B, sha256
`a53c2d6b2837f45d97244fc096e68f27ba9036e0582a0d9aada2e2f222dac293`, image base `0x140000000`.
Every address below is **decoded** by `Tools/scripts/jc3_rtti_map.py` from those bytes; the script's
`--check` re-derives all of them and compares (`PASS: 690 vehicle rows and 6 literal hits recompute
identically from 51083264 bytes`, exit 0).

## 1. RTTI table (vehicle side)

Method (decoded): find `.?AV…`/`.?AU…` names, type descriptor = name − 0x10; complete object locator =
the structure whose `+0` is `1` and whose `+12` is the TD's **image-relative RVA** (the COL's `+12`
field is 32-bit, not a VA); vtable = the 64-bit **VA** of the COL stored at `vtable−8`. That last
detail is a decoded correction: the 32-bit RVA form of a COL also occurs inside class-hierarchy
base-class arrays, so an RVA scan produces false vtables whose slot 0 is not code. The tool requires
slot 0 ∈ `.text`.

| class | kind | type descriptor | COL | vtable | slot 0 |
|---|---|---|---|---|---|
| `CVehicle` | vehicle | `0x142DA3588` | `0x1428DB7B0` | **`0x1424E30B8`** | `0x14107C070` |
| `CLandVehicle` | land vehicle | `0x142DA3638` | `0x1428DC0C0` | **`0x1424E5778`** | `0x14107DCF0` |
| `CCar` | land vehicle | `0x142DA3700` | `0x1428DCAD8` | **`0x1424E8A28`** | `0x14107DAF0` |
| `CAirVehicle` | vehicle | `0x142DA35A8` | `0x1428DBA98` | `0x1424E3B58` | `0x14107D990` |
| `CSeaVehicle` | vehicle | `0x142DA36B8` | `0x1428DC6D0` | `0x1424E7768` | `0x14107BD30` |
| `CPfxVehicle` | vehicle | `0x142D44958` | `0x142872968` | `0x142353B48` | `0x1402E86F0` |
| `CVehicleNetworkComponent` | vehicle | `0x142D841F0` | `0x1428BCC68` | `0x1424382B8` | `0x140B1ECC0` |
| `CVehicleDamageState` | vehicle | `0x142D62AE8` | `0x142890900` | `0x1423BBC38` | `0x140784B80` |
| `CVehicleRule` | vehicle | `0x142D990A0` | `0x1428D0848` | `0x1424A52A8` | `0x140DB8010` |
| `CVehiclePartGameObject` | vehicle | `0x142D8F9E8` | `0x1428CAE60` | `0x142462398` | `0x140CDE640` |
| `CIsInVehicle` (condition) | vehicle | `0x142D64230` | `0x142894530` | **`0x1423C36E8`** | `0x14076C790` |
| `CDamageable` | damage/health | `0x142D656D0` | `0x1428998E8` | **`0x1423DFB78`** | `0x1408AD270` |
| `CDamageController` | damage/health | `0x142D886F0` | `0x1428C3438` | `0x14244B3B8` | `0x140BE85B0` |
| `CHealthControl` | damage/health | `0x142D89448` | `0x1428C4808` | `0x142453278` | `0x140C28C00` |
| `CCharacter` | character | `0x142D656A8` | `0x142897378` | **`0x1423D1848`** | `0x1407F46B0` |
| `CGameObject` | object | `0x142D57C58` | `0x142885E28` | `0x142384588` | `0x140503540` |
| `hknpVehicleInstance` | vehicle | `0x142DBBDF0` | `0x1428EE610` | **`0x14256AC98`** | `0x14151A310` |
| `hknpVehicleData` | vehicle | `0x142DBBF70` | `0x1428EE8D8` | **`0x14256BD38`** | `0x14151B100` |

Counts over the whole scan: 5,259 RTTI names; 690 rows matched (Vehicle / Handling / Damage / Health /
Tune / CCar / LandVehicle / Character / GameObject); 683 of them resolved a vtable; kind split
vehicle 126, object 459, character 70, damage-health 29, land vehicle 4, other 2. `Handling` matches as
an RTTI *class name*: **0** rows. `Tune` appears twice, both `CRenderBlockTypeMaterialTune` (renderer,
not handling). So there is no `CHandling`/`CVehicleHandling` class in this build: the tune block is a
**data** struct, not a class with RTTI (see §3).

Cross-check with the project's own vocabulary (`Research/JC3Grab/VOCABULARY.md`,
`DAMAGE_MECHANISMS.md`, `DAMAGE_MODEL.md`): `CVehicleHealth` does not exist as an RTTI name in this
exe either (0 rows); `invulnerable` at `epe+1167` is an **entity-descriptor file offset**
(`DAMAGE_MECHANISMS.md`: "type 0x0e @1162 … value @1167"), i.e. a payload field, not a runtime class
member — the two live at different layers and cannot be cross-walked by name. That is consistent, not
a conflict: the file says *invulnerable on the CCar root*, the exe says the runtime carrier is
`CVehicle`/`CCar` with `CDamageable`/`CDamageController`.

## 2. Vtables

All vtables are contiguous slot arrays directly after their COL pointer; slot 1 is `0x1404CE230` for
`CVehicle`, `CDamageable` and `CDamageController`, i.e. one shared destructor thunk — useful as a sanity
oracle (three unrelated classes sharing slot 1 is expected for a scalar-deleting destructor).

`CVehicle` slot 0 is `0x14107C070`, slot 1 `0x1404CE230`; the full six-slot list of every class is in
`Working/RTTI/vehicle_rtti.json` (`vehicle_rows[].vtables[].slots`), not inferred here. The five
land/air/sea vtables are **distinct**, so a
per-kind virtual dispatch exists and `CCar` can be distinguished from `CLandVehicle` at runtime by
loading `[obj]` and comparing to `0x1424E8A28` (derived check for a live session).

Two `$_Bind` rows (`…Q8CVehicle@@EAAXX…`) have a TD but no COL point at them: they are compiler
closures bound to `CVehicle` member functions, not polymorphic classes. They still prove the members
`CVehicle::` **exists as a name in this build** and that its member functions are passed to
`std::tr1::bind` — the same pattern the 2018 console uses.

## 3. Handling-editor structures re-found

The 2017 tool's *own* literals are mostly not in the exe: 6 of 36 quoted literals from
`E:/Modding/_tools/jc3-handling-editor/src` exist at all.

| literal | VA | code refs (nearest 0xCC-padded start, derived) |
|---|---|---|
| `CWeaponBase` | `0x1423A3CB8` | `0x1407C8A40`, `0x1407F8F70`, `0x140942180`, `0x140979170` |
| `D3D11CreateDevice` | `0x142D33E7E` | none (import-name table) |
| `GetSystemMetrics` | `0x142D33A26` | none (import-name table) |
| `Vehicles` | `0x1423045C8` | none |
| `Weapons` | `0x1423045D8` | none |
| `d3d11.dll` | `0x142D33E90` | none |

Reading: `d3d11.dll`, `D3D11CreateDevice`, `GetSystemMetrics` are the tool's **own** hook scaffolding,
not game structures; `Vehicles`/`Weapons` are shared category words; `CWeaponBase` is the only
game-class name from that source that survives, and its four referencing functions are the only
2017-name anchors that still resolve. **No handling field name from the 2017 editor exists in the exe**
— those were ImGui labels and jc3mem symbol names in the tool, never strings in the game.

The structures it edited **do** still exist, under Havok's names (decoded, 25 `hknpVehicle*`
descriptors, all with vtables): `hknpVehicleData 0x142DBBF70 / vt 0x14256BD38`,
`hknpVehicleInstance 0x142DBBDF0 / vt 0x14256AC98`, and the per-subsystem tune classes
`hknpVehicleDefaultEngine 0x142DBD6F0 / vt 0x142571DD8`, `…DefaultTransmission 0x142DBD628 /
0x142571648`, `…DefaultBrake 0x142DBBF10 / 0x14256B418`, `…DefaultSteering 0x142DBD690 /
0x142571940`, `…DefaultSuspension 0x142DBBE80 / 0x14256B010`, `…DefaultAerodynamics 0x142DBD750 /
0x1425720D8`, `…DefaultVelocityDamper 0x142DBD5C0 / 0x1425712A0`,
`…DefaultAnalogDriverInput 0x142DBD550 / 0x142570F78`, plus the abstract bases and
`hknpVehicleDriverInputStatus 0x142DBD4A8 / 0x142570EE8`.

So the 2017 editor's addresses are dead (as the brief says) but its **target survives as a class
family**: a new handling editor should resolve `hknpVehicleInstance` → `hknpVehicleData` → the
`Default*` blocks through these vtables instead of re-using 2017 offsets. **UNKNOWN:** the member
offsets inside `hknpVehicleData`/`hknpVehicleInstance` — RTTI gives types and vtables only, never
field layout.

## 4. Player → vehicle path

**In console-thingy's source: absent.** `grep -rn -i "vehicle" src/` returns exactly two hits, both
event *strings* (`ply.vehicle.burn`, `debug.vehicle.incrementtint`) in `commands/event.h`. The decoded
chain stops at the character:

```
CNetworkPlayerManager::instance()  = **(void***)0x142F36958      (decoded, player_manager.h)
  +0x48  -> CNetworkPlayer* m_localPlayer
  m_localPlayer +0x128 -> shared_ptr<CPlayer> m_player            (16-byte shared_ptr)
  m_localPlayer +0x138 -> shared_ptr<CCharacter> m_character
  CPlayer +0x100 -> CCharacter* m_character
  CCharacter +0x2830 -> CMatrix4f m_transform                      (decoded, character.h)
```
`CCharacter.h` is `char _pad[0x2830]; CMatrix4f m_transform;` — **no vehicle member**, so the path
is not in the source and cannot be read out of it.

Static anchors that do exist (decoded): the `CIsInVehicle` condition class
(TD `0x142D64230`, vtable `0x1423C36E8`, predicate slot 0 `0x14076C790`) and
`CVehicleNetworkComponent` (vtable `0x1424382B8`) — both must read the character→vehicle relation, so
`0x14076C790` is the natural first place to look for the offset, without a live process.

**UNKNOWN:** the offset of the vehicle pointer inside `CCharacter` (and whether it is direct or via a
seat/`CVehicleNetworkComponent`). RTTI does not encode field offsets and no repo file records one. It
needs the experiment in §5.1.

## 5. What still needs a live session (one 5-minute experiment each)

1. **Character → vehicle offset.** Attach a debugger or the console DLL to one running game; spawn a
   Serpente (P9 console route), enter it, read `CCharacter*` from `0x142F36958`, then scan its first
   0x4000 bytes for a pointer whose `[0]` equals `CCar` vtable `0x1424E8A28` or `CVehicle` vtable
   `0x1424E30B8`; step out, repeat after exiting the car. PASS = the same offset is non-null only
   while seated. (Static oracle: only one offset should flip.)
2. **Health / invulnerable at runtime.** With the car in frame, find the `CCar` object (vtable compare),
   scan its first 0x4000 bytes for the int32 the epe `1167` byte maps to by firing one pistol round and
   re-reading; PASS = one int32 drops by a constant per hit and `CDamageable`'s vtable
   (`0x1423DFB78`) object is reachable from it.
3. **Linear/angular velocity.** From the same `CCar`, read `hknpVehicleInstance*` (vtable
   `0x14256AC98`) and step through `hknpVehicleData` (`0x14256BD38`); break on a float that equals the
   HUD speed × unit scale while driving at two speeds. PASS = the same field tracks both speeds.
4. **Handling block edit.** Take the `hknpVehicleData` pointer found in (3), change
   `hknpVehicleDefaultEngine` (`0x142571DD8`) max-torque-like float by +10 %, and watch the same
   straight-line acceleration in a 20 s RECORD take; PASS = a repeatable time-to-60 delta, with the
   original value restored afterwards.
5. **`CIsInVehicle` predicate.** Set a breakpoint on slot 0 `0x14076C790`, enter and exit the car; PASS
   = the breakpoint hits on both transitions and its argument chain yields the character pointer
   decoded above — this validates the whole §4 chain in one take.

Every experiment needs `tmp/freebuff/APPROVED_Q.txt` (it exists, scoped Q-0 + L0) and the test-ban
rules: one variable per take, kill by exact PID.

## 6. Files, commands, UNKNOWNs

Files: `Tools/scripts/jc3_rtti_map.py` (new), `Working/RTTI/vehicle_rtti.json` (337 KB),
`Working/RTTI/vehicle_rtti.md` (110 KB).

Commands and output (verbatim, final run):
```
wrote E:\Modding\JC3-Batmobile\Working\RTTI\vehicle_rtti.json
690 vehicle rows, 6/36 literals found
write exit=0
PASS: 690 vehicle rows and 6 literal hits recompute identically from 51083264 bytes
check exit=0
```
Counts from the JSON: total 690, with vtable 683, `hknpVehicle*` 25, `CVehicle` mentions 50,
`Handling` 0, `Damage` 27, `Health` 6, `Tune` 2; kinds {vehicle 126, object 459, character 70,
damage/health 29, land vehicle 4, other 2}.

UNKNOWNs: (a) field offsets inside `CVehicle`/`CCar`/`CCharacter`/`hknpVehicleData` — RTTI has none;
(b) which of the 8 COLs that point at `CVehicle` is the primary one (all 8 resolve to a code vtable,
the first is tabulated); (c) whether any 2017 handling-editor *field* name survives as a non-ASCII
symbol — only ASCII literals were scanned; (d) `CVehicleHealth` as a runtime type does not exist in
this build, so the vocabulary's name must map to `CDamageable`/`CDamageController` or a field inside
`CVehicle`, and that mapping needs experiment (2).

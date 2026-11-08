# T-26 drag offsets — lookup table (Drag / DragNoLoad / DriftDrag)

Card: `GRAB_BACKLOG.md` T-26 (row at line 1271, ledger row at line 1874), scoped by
`Working/Translation/T1_TRANSLATION.md:107` (T-R2). Lookup only: the T-26 row, `Research/specs/` and
every grab file are unchanged. No game install, GOG folder or save file was opened.

**SUMMARY: 0 DECODED, 3 UNKNOWN.** The class dump declares all three members at the recorded offsets,
but no decoded file carries a value at any of those three byte positions. Two of the three are also
**not class members at all** — `Drag` @16 and `DragNoLoad` @20 are struct-relative offsets inside
`FVehicleTransmission`, which `RVehicleSimBatmobile` carries as `TransmissionModel` at object offset
1060. The class dump itself is the only file that names those offsets on the sim class, and it is a
declaration, not a decode.

Output table: `Working/Prep/t26_drag_offsets.json` (3 entries, fields `member`, `offset`,
`source_path`, `source_line`, `value_or_null`, `status`, plus the quoted line and the settling file).

## 1. The three members

| member | offset | what the offset is | decoded value in any file | status |
|---|---:|---|---|---|
| `Drag` | 16 | struct byte 16 of `FVehicleTransmission` (= object 1076 on the CDO) | none | **UNKNOWN** |
| `DragNoLoad` | 20 | struct byte 20 of `FVehicleTransmission` (= object 1080 on the CDO) | none | **UNKNOWN** |
| `DriftDrag` | 712 | class offset 0x2C8 on `RVehicleSimBatmobile` | none | **UNKNOWN** |

## 2. What the class dump says (declaration, not a value)

`Research/BatmobileGrab/BMSDK_OFFSETS.json:24906`

```
     "member": "Drag",
     "name": "Drag",
     "offset": 16,
```

`Research/BatmobileGrab/BMSDK_OFFSETS.json:24912`

```
     "member": "DragNoLoad",
     "name": "DragNoLoad",
     "offset": 20,
```

`Research/BatmobileGrab/BMSDK_OFFSETS.json:24261`

```
     "member": "DriftDrag",
     "name": "DriftDrag",
     "offset": 712,
```

Each block is `"kind": "FloatProperty"` with a name, an offset and a type — no value field exists
anywhere in the dump, so these three lines are the only place the numbers appear.

## 3. `Drag` @16 and `DragNoLoad` @20 are struct offsets, not sim-class offsets

The two blocks above sit inside `"structs": { "FVehicleTransmission": { ... } }` — the struct block
opens at `Research/BatmobileGrab/BMSDK_OFFSETS.json:24878` (`"FVehicleTransmission": {`) and its
member list starts at `RPM` 0, `Gear` 4, `OutputGas` 8, `Friction` 12, then `Drag` 16, `DragNoLoad` 20,
`NumForwardGears` 24, `GearRatios` 28… The class block the struct follows is `RVehicleSimBatmobile`
(`"size": 1220`, ending at `AirControlTimeInAir` 1212 / `BattleModeSlopeFactor` 1216), and that class
carries the struct as a member — `Research/BatmobileGrab/BMSDK_OFFSETS.json:24800`:

```
     "member": "TransmissionModel",
     "name": "TransmissionModel",
     "offset": 1060,
     "type": "FVehicleTransmission"
```

The struct is 112 B (`Research/BatmobileGrab/REGISTRATION.md:73`: "`VehicleTransmission` was counted as
92 bytes instead of its real 112"), which is exactly the gap between `TransmissionModel` 1060 and the
next member `ScaleTopSpeed` 1172. So on a live object `Drag` lands at 1060 + 16 = **1076** and
`DragNoLoad` at 1060 + 20 = **1080**, not at object offsets 16 and 20.

This matters for the T-26 row's wording ("`Drag` @16 (0x10), `DragNoLoad` @20 (0x14)" as members of
the sim class): the offsets are right, the owning scope is not. The row is left as it is, per this
brief.

## 4. Does any decoded file give a value at those byte positions?

**`DriftDrag` (712 / 0x2C8) — no.** The shipped `SimulationModel` object has a complete tag walk in
`Research/BatmobileGrab/REMAINDER.md:1895` (export 169320, 33 tags, closes to the 2-byte terminator):

```
| 169320 | `SimulationModel` | `RVehicleSimBatmobile` | 4920 | 59263 | FloatProperty@0x1d0=0.01; FloatProperty@0x1d4=0.003; StructProperty@0x1dc=None; … StructProperty@0x1a8=None; StructProperty@0xc8=None; FloatProperty@0xdc=110; … FloatProperty@0xb0=2; FloatProperty@0xb4=1 |
```

The line is quoted in full in `Working/Prep/t26_drag_offsets.json`; the elisions above are the only
edits. The tokens `@0x2c8` and `@0x2c4` do not occur anywhere in it — the offsets adjacent to
`DriftDrag` are simply absent, so no tag was written there.

The per-package walk agrees — `Research/BatmobileGrab/MECHANICS.md:99` (`### SimulationModel —
`RVehicleSimBatmobile` (Playable_BatmobileFunhouse_SF, 2328 B)`) lists the offset-only floats as
`0x2C4  600.0000`, `0x2D4  0.7500`, `0x2D8  1.2500` — **no 0x2C8 between them**. The four packages are
byte-identical here (`Research/BatmobileGrab/VARIANTS.md:142-144`: "0 differing tags" for MK2, Joker,
Funhouse), so the absence is not a one-package artefact. `Research/BatmobileGrab/MODES.md` never lists
the member either, but it only covers the mode families, so its silence is not the evidence — the tag
walks are.

**`Drag` / `DragNoLoad` — no.** The one decoded file that resolves the enclosing struct is
`Research/BatmobileGrab/DRIVE_MODES.json`, the class-default-object walk (`archetypes.class_default_object`,
`"object": "Default__RVehicleSimBatmobile"`, 58 tags). It records the struct tag and stops there —
`Research/BatmobileGrab/DRIVE_MODES.json:483`:

```
     "TransmissionModel": {
      "at": 408,
      "bits": null,
      "kind": "StructProperty",
      "offset": 1060,
      "struct": 226,
      "tag_type": "StructProperty",
      "value": null
```

`"value": null` (line 490) with `"struct": 226` means the payload was seen and its nested members were
not decoded. A search of `DRIVE_MODES.json` for `"offset": 712` returns only `7124`, and no file under
`Research/BatmobileGrab/` or `Research/RBM/` contains `"Drag"`, `"DragNoLoad"` or `"DriftDrag"` as a
decoded member (`Research/RBM/` returns 0 hits for all three words, case-insensitive, whole-word).

## 5. What would settle each member

| member | file that would carry it |
|---|---|
| `Drag` (struct 16) | a nested decode of the `TransmissionModel` payload, struct 226, in `Research/BatmobileGrab/DRIVE_MODES.json` (`archetypes.class_default_object`) — the tag is present, only its members are undecoded |
| `DragNoLoad` (struct 20) | same payload, same file |
| `DriftDrag` (712) | the 58-tag `Default__RVehicleSimBatmobile` payload mapped in `Research/BatmobileGrab/DRIVE_MODES.json` (no key resolves to 712 today), or a `Tools/scripts/chase/ch1_dlo.py ... Default__RVehicleSimBatmobile --want DriftDrag` run against `BmGame.upk` |

## 6. Checks and revert

- `Working/Prep/t26_drag_offsets.json` parses as JSON, holds 3 entries in card order (`Drag`,
  `DragNoLoad`, `DriftDrag`) with offsets `16`, `20`, `712` and status `UNKNOWN` on all three; every
  entry names a `settling_file`.
- The T-26 row (`GRAB_BACKLOG.md:1271-1281`, ledger row `1874`) was not edited; no grab file under
  `Research/` and nothing in `Working/Translation/` was written.
- Revert: delete `Working/Prep/t26_drag_offsets.json` and this report.

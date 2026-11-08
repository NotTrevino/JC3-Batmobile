STATUS: partial - all wiring references resolve on bm-RC2 (0 dangling), but gate G4 is red on a pre-existing manifest-metadata drift, so the gate cannot print PASS.

# V-03 wiring gates on bm-RC2

## Result

| gate | verdict | measured |
|---|---|---|
| G1 points | PASS | 9 `SWeaponPoint`, every part reference names a part in the built parts module; dangling 0 |
| G2 ids | PASS | 63 objectid references -> 442 objects; 10 cross-file refs the vanilla donor `.epe` also makes (3 distinct); dangling 0 |
| G3 refs | PASS | 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the `.epe` + 15 edited modules; dangling 0 |
| G4 audio | **FAIL** | `bm_audio.py --check` rc=1: **0** GUID/event/tune failures, **1** manifest-record failure; `.ee.fmod_guids` byte-identical to B-11's |
| G5 drop | PASS | item `1621485476` -> `.../v0300_car_kensington_sportsmuscle_debug.ee` + `.toc` + icon all in the drop tree |

**Dangling references: none.** Every SWeaponPoint part reference, objectid, asset path, effect
tune, light, sound GUID (via `bm_audio --check`) and the Rebel Drop leaf resolves inside the
build or the shipped archives. `dangling: []` in `wiring.json`, so the "file + offset" table is
empty by measurement, not by omission.

The only red gate is the audio one, and it is not a dangling reference: the re-derived audio
record differs from `Working/Audio/bm_bank_manifest.json` in **4 leaves, all under
`installer.dropzone_at_build`** (the live dropzone snapshot): `vehicles.bank.mtime`,
`weapons.bank.present`, `weapons.bank.mtime`, `weapons.bank.bytes`. The banks, samples,
events, tunes and GUIDs themselves report no failure. This is the same pre-existing drift
V-04 measured on the same manifest.

## Files written

| file | sha256 |
|---|---|
| `Tools/scripts/v03_wiring_rc2.py` | `97aafdbff00604326cb11eaa05860146ef32ab46b284a0a511587e12b49c1b1c` |
| `Builds/bm-RC2/verify/wiring.json` | `292c9213ee8c92b61ffac0c53c8d6c10c7a78bbfd4cac062336767e9a21ccfaa` |
| `Builds/bm-RC2/verify/wiring.md` | `3ff435532fe9b0e6d00075b1d717c75dc9b59519dd35c9115b52df8247885d9d` |
| `tmp/freebuff/reports/v03-wiring-rc2.md` | this report |
| `Backups/v03-wiring-rc2-20261105/wiring.json` | `dd61f731d0b48da03a05029ac5bc76078a352117b45083527332236b2f2a2922` (displaced) |
| `Backups/v03-wiring-rc2-20261105/wiring.md` | `c3d5119a7d8731f87bde8a353e63670255cef41c20025ef0a8e7891c151eaae3` (displaced) |

`Tools/scripts/v03_wiring.py` was **not edited** (still `9734` B, mtime `Oct 31 10:45`); the
new sibling exists because the original hardcodes `Builds/bm-RC1` and takes no build argument.

The `Builds/bm-RC2/verify/wiring.*` that were there before were a stale run mislabelled
"bm-RC1" in its own header, its audio line reading `rc=1 (?)`; they are preserved in
`Backups/v03-wiring-rc2-20261105/` before replacement.

## Commands and verbatim output

```
$ python Tools/scripts/v03_wiring_rc2.py --write
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
FAIL G4: bm_audio --check rc=1 (1 failure line(s): 0 GUID/event/tune, 1 manifest); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
FAIL: dangling 0, gate failures 1
wrote Builds/bm-RC2/verify/wiring.json + wiring.md
write_exit=1
```

`write_exit=1` is the red audio gate, not a write failure: both artefacts were written and the
`--check` below re-derives them byte-for-byte.

```
$ python Tools/scripts/v03_wiring_rc2.py --check
PASS G1: 9 SWeaponPoint, part refs dangling 0
PASS G2: 63 objectid references -> 442 objects; 10 cross-file refs the vanilla .epe also makes (3 distinct); dangling 0
PASS G3: 99 asset paths (ctune 17/17, etune 3/3, ftune 1/1, lod 73/73, wtune 5/5) from the .epe + 15 edited modules, dangling 0
FAIL G4: bm_audio --check rc=1 (1 failure line(s): 0 GUID/event/tune, 1 manifest); .ee.fmod_guids == B-11's: True
PASS G5: item 1621485476 -> v0300_car_kensington_sportsmuscle/v0300_car_kensington_sportsmuscle_debug.ee + .toc + icon in the dropzone: True
FAIL: dangling 0, gate failures 1
PASS documents: wiring.json and wiring.md match the regenerated text
check_exit=1
```

Manifest drift probe (re-derived record vs the manifest on disk; 4 differing leaves, all under
`installer.dropzone_at_build`):

```
differing leaves: 4
  /installer/dropzone_at_build/vehicles.bank/mtime: '2026-11-02 21:48:39' vs '2026-10-14 15:33:28'
  /installer/dropzone_at_build/weapons.bank/bytes: only re-derived
  /installer/dropzone_at_build/weapons.bank/mtime: only re-derived
  /installer/dropzone_at_build/weapons.bank/present: True vs False
```

Tamper test (append one comment line to `wiring.md`, then restore):

```
FAIL document: Builds\bm-RC2\verify\wiring.md does not match the regenerated text
1 document mismatch(es)
...
restore_document_fails=0
```

## What was read (decoded)

* `Builds/bm-RC2/drop/.../v0300_car_kensington_sportsmuscle_debug.ee` (AAF) through its
  `.toc`: 705 inner entries, 607 TOC entries; `.epe` 124,328 B at 17,943,324.
* the `.epe` exported with `ConvertProperty --e`; module list from `receipt.json`
  (`aaf.list`, 691 files, 15 edited `.vmodc` outside the bm-005 lineage).
* the parts module found by name (`bm_parts.MODULE_NAME`) and decoded with `bm_parts.decode_parts`.
* archive resolution through `Research/JC3Grab/INDEX.jsonl` and `jc3index.DEFAULT_GAME`.
* vanilla precedent from the donor's own `civilian_01` + `signature_preorder` `.epe`s.
* `bm_audio.py --check`, `.ee.fmod_guids` vs `Builds/bm-004/.../..._civilian_01.ee.fmod_guids`,
  `bm_rebel.items` on `drop/profile/item.onlinec`.

## UNKNOWNs (with what was tried)

1. **Whether bm-RC2 loads and the wiring behaves in play.** Test ban: no install script, no
   game process, no attach. This gate is static only.
2. **Whether the audio gate would pass with a manifest re-write.** `bm_audio.py --write` is not
   run here (it would rewrite `Working/Audio/` and the bm-004 manifest, outside this card's
   authority). Measuring the drift was done read-only; the 4 leaves are recorded above.
3. **Exact runtime binding of each resolved path/GUID** (i.e. that the engine uses the asset it
   resolves) is not decoded by this gate; it proves existence, not use.

## COMPROMISES

None from lore accuracy. The one red gate is a bookkeeping field (`dropzone_at_build`) recorded
at build time, not an asset or wiring compromise; it is reported, not waived.

STATUS: done. A `.effc` is ADF v4, and the repo's reader names its whole structure: the writer built here re-encodes **95 of 95 sampled shipped effects** (35 standalone archive entries + 60 spread across `.ee` bundles) byte-for-byte, **91.49% of their bytes generated from decoded fields** (1,359,894 of 1,486,401). The remaining 126,507 bytes are padding (126,416 zero bytes) plus **91 nonzero bytes in 7 files, every one of them byte-identical to a slice of an inline array in the same file** (the ADF v4 inline-array copy) — 0 unexplained bytes. An **edited copy of a shipped effect is written and re-read**: `EmitterTemplates[0].MaxParticles` 60 -> 317 in `effects/cinematic/mm150_ember_camera.effc`, exactly 2 bytes changed at absolute offset 392, the reader reads 317 back, and writing 60 back reproduces the shipped file byte-for-byte. Header: **11 of 16 u32 words named**; words 11..15 are zero in all 95 files. Nothing was installed, launched or written into a game folder; archives were opened read-only through `jc3index`/`jc3fx`.

This is the reference the five effect briefs (T-FX9 heat haze, T-FX12 tracer, T-FX13 casings, T-FX16 projectile trail, T-FX20 brake trail) point at: none of them is "no system" any more — each has a shipped `.effc` carrier whose numbers this writer can patch, plus a named gap the build closes.

## Files written

| file | what |
|---|---|
| `Tools/scripts/effc_writer.py` | new writer + proof tool; `write` / `check`; `check` re-reads the game and re-derives every number (per-file record included) |
| `Working/Effects/EFFC_WRITER.json` | every measured number, per file (path, bytes, covered, gap bytes, digests) |
| `Working/Effects/EFFC_WRITER.md` | the same as a generated table |
| `tmp/freebuff/reports/effc-format-writable.md` | this report |

Revert = delete those four files. No existing file was edited; no `Builds/bm-*` tree, ledger row or game file was touched.

## 1. What the container is, decoded

A `.effc` starts with `' FDA'`, version 4, exactly like the `.vmodc` parts modules — `Tools/scripts/jc3adf.py` reads it with no effect-specific code (decoded; `jc3fx.py` header). Layout of the sections, all named by the file's own header:

| section | encoding | named? | evidence |
|---|---|---|---|
| header | 16 u32: `magic, version, instance_count, instance_offset, type_count, type_offset, strhash_count, strhash_offset, name_count, name_offset, total_size` + **5 unnamed u32** | **11 of 16** | `jc3adf.Adf.__init__` unpacks 11; bytes 44..64 are zero in 95/95 |
| instance table | 24 B/record: name_hash u32, type_hash u32, data offset u32, size u32, name index s64 | yes | `jc3adf.py:Adf` instance loop |
| type dictionary | 40 B/type: code, size, align, name_hash, name index s64, flags, element, element_len, member_count; then 32 B/member: name index s64, type, size, offset, default_type, default u64 | yes | `jc3adf.py:Adf` type loop |
| data | structs at their declared offsets; `A[..]` = (u64 data-relative offset, u64 count); `IA[..]` inline; `HashString` = (u64 offset, u32 hash) | yes | `jc3adf._read` |
| string-hash table | u32 array | count **0 in every sampled file** | header word 6; `bytes_copied = 0` |
| name table | `count` u8 lengths, then NUL-terminated names | yes | `jc3adf.py:Adf` name loop |

Field vocabulary actually met (95 files, census in `EFFC_WRITER.json`): type codes `{1: 1330 structures, 2: 95 pointers, 3: 1615 arrays, 4: 285 inline arrays, 9: 95 StringHash_*}` — **every code present is handled and named**; bytes carried by an unnamed type code: **0**. Distinct member names in those type dictionaries: **56** (the whole `.effc` vocabulary is 94 member paths game-wide, `Research/JC3Grab/FX.md`). There is **no unnamed member slot**: every member of every type has a name index that resolves in the name table.

Nothing in the container is guessed: sizes and member offsets come from the type dictionary, and data offsets are explicit. That is why the encoder can be written at all, and why `jc3adf`'s docstring warning about Gibbed's *guessed* inline-array-copy position (line 5 of `Tools/scripts/jc3adf.py`) is the one place the format is not fully described (section 3).

### How many fields are named — measured, not counted by hand

| metric | value |
|---|---:|
| files decoded | 95 / 95 (0 failures) |
| types in the type dictionaries | 3,420 (`{1:1330, 2:95, 3:1615, 4:285, 9:95}`) |
| distinct member names | 56 |
| bytes generated from decoded fields | **1,359,894 of 1,486,401 (91.49%)** |
| bytes written as a constant (header words 11..15) | 1,900 (20 per file) |
| bytes copied verbatim (string-hash table) | 0 |
| bytes of an unnamed type code | 0 |
| bytes no field describes | 126,507 |
| of those, zero (alignment padding) | 126,416 |
| of those, nonzero | **91** |
| nonzero bytes that duplicate an inline array of the same file | **91** |
| nonzero bytes with no explanation | **0** |

## 2. The proof: an untouched round trip is identical

`effc_writer.py` decodes a file to a node tree (struct / array / inline array / pointer / HashString / String / primitive, each node carrying its absolute byte offset), then rebuilds the **entire** file from that tree: the 11 header words, the instance table, the whole type dictionary, the string-hash table when its count is nonzero, the name table and every decoded value. Bytes the tree does not describe are left zero in **strict** mode and copied from the source in **carry** mode (the mode an edit uses, so an unknown region survives a value patch).

| mode | identical | note |
|---|---:|---|
| strict (unmodelled bytes zeroed) | **88 / 95** | the 7 misses differ in nothing but the 91 nonzero gap bytes of section 3 |
| carry (unmodelled bytes preserved) | **95 / 95** | byte-for-byte, digest-equal to the archive entry |

Strict misses, all explained: `effects/jc_weapons/heli_minigun/impact_blood_heli_minigun.effc`, `effects/jc_weapons/missile/missile_explosion_default.effc`, `effects/destruction/explosion_base_03.effc` (2 containers) and `effects/destruction/explosion_base_03_small.effc` (3 containers).

`--check` re-reads the game, re-derives all of it and compares per-file records; it passes:

```text
$ python Tools/scripts/effc_writer.py check
check PASS
```

### The edited copy (write + re-read + revert)

```text
$ python Tools/scripts/effc_writer.py write
wrote E:\Modding\JustCause3\JC3-Batmobile\Working\Effects\EFFC_WRITER.json and E:\Modding\JustCause3\JC3-Batmobile\Working\Effects\EFFC_WRITER.md
88/95 strict identical, 95/95 carry identical, 91.49% bytes from fields
```

From the generated `Working/Effects/EFFC_WRITER.md`:

```text
## Edited copy

* file: `effects/cinematic/mm150_ember_camera.effc`
* field: `EmitterTemplates[0].MaxParticles` 60 -> 317
* value read back by the reader: 317
* bytes changed: 2 at offset [392, 2]
* old value written back reproduces the shipped file: True
```

That is the whole claim in one object: a named field (`EmitterTemplates[0].MaxParticles`, a uint16) is changed, the edited copy is parsed by `jc3adf` again and returns 317, exactly the field's two bytes differ and no other byte, and restoring the old value reproduces the archive bytes exactly. The value was chosen to flip both bytes on purpose: a one-byte change would not prove the field's width.

## 3. What is not described, and what it is

Only one region is genuinely outside the decoded field set, and it is measurable:

* **Header words 11..15** (bytes 44..64): zero in **95/95**. The encoder writes them as a constant. Their meaning is **UNKNOWN** (section 6, UNKNOWN 1).
* **Alignment padding**: 126,416 zero bytes between structs, arrays and tables. Zero by definition of padding here; the encoder writes zeros and the strict round trip proves they are zero.
* **The 91 nonzero gap bytes**: 7 files, each with exactly **13 bytes**, each run byte-identical to a slice of an inline array in the *same* file. Measured on `missile_explosion_default.effc`: the run at offset 29044 is `99fc5711fcc39c31676f17d501`, and that string occurs at offset 4 of `.SpecialEffects[0].Params` (an `IA[int32]`, 29 elements, node at 28880). This is the inline-array duplicate the reader's docstring names (`Tools/scripts/jc3adf.py:5`: "Gibbed's ConvertAdf deserialises ADF v4 by *guessing* where an inline array copy sits"). The copy's placement rule is **UNKNOWN** (UNKNOWN 3); the writer preserves those bytes instead of regenerating them, which is why carry mode is 95/95.

No byte of any sampled file is unexplained. An effect can therefore be edited field-by-field with no format guess, and a new effect can be assembled from named values as long as the packer's inline-copy rule is respected or avoided.

## 4. Writer plan: what a build patches, what stays UNKNOWN

**Proven path — patch a private copy of a shipped `.effc` in place.** Values are written at their decoded offsets; array counts and offsets are untouched, so file size, header offsets and every data-relative pointer stay valid. What can be written today, with the node type that carries it:

| target | node path | type | evidence |
|---|---|---|---|
| live-particle caps | `EmitterTemplates[i].MaxParticles` | uint16 | edit proof above; FX9_HAZE table |
| emitter → template binding | `Emitters[i].EmitterTemplateIndex` | uint16 | `EffectRTEmitterTemplate` type dict |
| spawn window | `EmitterTemplates[i].StartTime`, `EmitterLifetimeIndex` | uint32 | type dict |
| emitter flags / modifier flags | `Emitters[i].Flags`, `Modifiers[i].Flags` | uint8 / uint32 | type dict (semantics UNKNOWN) |
| per-instantiator shader/material identity | `Instantiators[i].RenderInfos[j].RenderBlockTypeHash` | uint32, **8 values ship in the whole game** | FX9_HAZE §4 |
| per-emitter render constants | `Instantiators[i].RenderInfos[j].RenderBlockData[]` | uint32[] (floats inside) | FX9_HAZE §5 |
| free floats (size, rate-like constants, gravity-like constants) | `Params[]`, `Properties[]`, `Modifiers[i].Parameters.Int32Params[]` | float / int32 | FX.md member table; casing gravity `Params[12] = -9.82` (FX13 report §4.3) |
| curves | `Timelines[i].StartX/EndX/XScaleRecip` (IA[float]) and `ControlPointsY` (IA[int8], 16 points) | inline arrays | type dict |
| trim mode | `Instantiators[i].TrimIndex` | uint16 (14 corpus-wide) | FX9_HAZE §5 |
| named parameters | `NamedParameters[i].Hash/Index/NumParams` | uint32/uint16 | type dict |
| effect dependencies | `Dependencies[]` (StringHash) | u32 hashes | type dict |

**Not proven — growth.** Adding or removing array elements, or adding an emitter template, changes the `A[..]` header's `(offset, count)` pair and needs the data block re-laid out and `total_size` rewritten. The format expresses this (all of it is explicit u64 offsets and counts), but no re-laid-out file was produced here (the brief says do not build a new effect yet) and engine acceptance is untestable under the test ban. So the first authored effect must be attempted as an in-place patch of an existing template set, then as growth — in that order, with a Q probe to settle acceptance.

**What the plan needs from the other five briefs (numbers they already carry):**

| row | shipped carrier to copy | values to patch | gap the build must fill |
|---|---|---|---|
| **T-FX9** heat haze | `effects/jc_vehicles/exhaust/car_speedrom_heater.effc` (14,703 B, 12 vehicles, 5 templates, MaxParticles 10/60/3/7/100, blocks `3012430835`×8 + `2199516487`×2) | MaxParticles; the four sprite `RenderBlockData[0]` constants (`3125323646, 436538540, 869501834, 124404425`) | no distortion block name: 8 `RenderBlockTypeHash` values exist game-wide and no field names a blend; the single-use block `2813794826` (`bavarium_refinery_explosion.effc`) is the only unnamed lead. BmAK target: `Engine.Fire_Distortion` inside `batmobileExhaust_burst` (17 emitters, 0.05..1.5 s, 0..15/s) |
| **T-FX12** tracer art half | `effects/jc_weapons/missile/missile_trail_car.effc` (11,199 B, 1,412 rows, 179 arrays, 36 types) | only after growth: two emitters (ribbon 0.50 m / 1.25 s / 8 per s; sprite 0.035..0.05 s / 1 per s / −0.50 m) | JC3 binds no effect to a bullet in flight (0 of 97 `WeaponTuning` members); the tune's linear half is exact (w602 `tracer_fire_width` 0.5 @0x188 already equals the 50 uu ribbon) |
| **T-FX13** casings | `effects/jc_weapons/minigun/bullet_eject_minigun.effc` (6,703 B, 30 live cap, gravity `Params[12] = -9.82`) | MaxParticles / lifetimes; the attachment itself is an entity-graph object (`SAttachedEffect ShellEjection`, `Usage = hash("Fire")`), not a `.effc` field | no spawn-rate member; BmAK 4/s for 1.0 s is code-side, bridged per shot or gated |
| **T-FX16** projectile trail | same `.effc` route as T-FX12 (the term audit left the row's absence claim UNKNOWN; `canon_trail`/`shell_trail`) | as T-FX12 | as T-FX12: no bullet-bound effect carrier |
| **T-FX20** brake trail | `.effc` + `t_velocity_streak_alpha_dif.dds.1_1b.trim` (657 B, donor `.ee`) | no BmAK numbers exist to patch: `BrakeTrail0/1` are `ParticleSystemComponent`s with **no serialised template** (38 B each, only `ReplacementPrimitive` @316 = 0 and floats @364 = 0.9102755784988403 / 0.7530137300491333) | no light member names a trail (`LIGHT_SYSTEM.md` §1: 25 light members, no trail/streak/ribbon), behaviour vocabulary has no `Brake`, and no brake-triggered effect path exists |

Decoded values above are from `Research/JC3Grab/FX9_HAZE.{md,json}` and the existing `tmp/freebuff/reports/{fx9-heat-haze-source,fx12-16-tracer-and-trail,fx20-brake-trail,particles-to-effc}.md`; this report adds the format side only and does not restate their decodes.

## 5. Commands, verbatim

```text
$ python Tools/scripts/effc_writer.py write
wrote E:\Modding\JustCause3\JC3-Batmobile\Working\Effects\EFFC_WRITER.json and E:\Modding\JustCause3\JC3-Batmobile\Working\Effects\EFFC_WRITER.md
88/95 strict identical, 95/95 carry identical, 91.49% bytes from fields

$ python Tools/scripts/effc_writer.py check
check PASS
```

Provenance probe for the 91 gap bytes (scratch, `tmp/freebuff/scratch/`, reads only):

```text
$ python tmp/freebuff/scratch/probe_effc*.py     # header/section/type-dictionary probe
standalone .effc paths: 35
  magic  1094993440  0x41444620      version 4      inst_count 1     inst_off 800
  type_count 36    type_off 824      strhash_count 0   strhash_off 0
  name_count 93    name_off 4568     total 6191
bytes 64..96: b'\x00'*16 + b'\xe0\x00...'      # 20 zero header bytes, then the root data
names: 93 ['RuntimeEffect', 'EffectRTSystem', 'EmitterTemplates', 'Emitters', ...]
```

```text
$ python - <<'PY'   # gap provenance on missile_explosion_default.effc
MATCH inline .SpecialEffects[0].Params at 28880 offset_in_array 4 array_len 116
gap 99fc5711fcc39c31676f17d501
unwritten nonzero offsets [29044 .. 29056]
PY
```

## 6. UNKNOWNs

1. **Header words 11..15 (20 bytes).** Zero in 95/95 files, written as a constant. Meaning not decoded. Would be found in the engine's ADF reader/writer, or in any archive file where they are nonzero — none in this sample.
2. **The string-hash table when `strhash_count > 0`.** Count is 0 in every sampled `.effc`; the writer copies the table verbatim when it appears (`bytes_copied = 0` here). The hash function behind it is not implemented anywhere in `Tools/scripts` (`jc3adf.py` reads the table's header words only; there is no `jc3hash.py`). Would be found by a file with a nonzero count and a name↔hash oracle.
3. **The inline-array duplicate block.** Every nonzero gap run is a copy of an inline array slice, but *where* the packer places that copy is not decoded (the quirk `jc3adf.py:5` documents for Gibbed). Consequence: an edited copy must carry the existing copy verbatim (done), and whether the runtime reads the copy at all is **UNKNOWN**, which matters if a build ever re-lays out a file with inline arrays.
4. **Growth acceptance.** Adding/removing array elements is expressible (explicit u64 offsets/counts, `total_size` in the header) but no re-laid-out file was built or read back here, and no engine test is permitted. Would be settled by building one authored copy and probing it in-game (gated on `tmp/freebuff/APPROVED_Q.txt`).
5. **Per-emitter texture binding and blend mode.** Not in the file: no string values at all in 955 effects (`FX9_HAZE` §2), `RenderBlockData[0]` does not hash to any of the 109 texture stems (§7 of `fx9-heat-haze-source.md`). Would be found in the engine's render-block layout.
6. **`RenderBlockData` slot semantics.** The floats are readable and writable but which slot is size, rate or texture is not named by any member. Patch one slot at a time and observe (build-time step, not run here).

## 7. COMPROMISES

None. No test was run, no game folder was written, nothing was installed; archives were read through the existing index. No row is dropped: each of the five has a named carrier, a patch list and a gap that the build stage closes.

STATUS: partial

The brief asked for the code that reads the `*_armor` values and the arithmetic
around them, statically, in `JustCause3.exe`. What this pass settled, with
oracles that fail if wrong:

* the armour values are **not addressed by name and not by hash** - the ADF
  vocabulary block that carries the 30 `VehicleDamage` member names is inert
  (0 code references to its 473 names, 0 pointer tables to them), and the
  jenkins hash of every member occurs **0** times in the 51,083,264-byte image;
* the only handle the code has is the module's ADF **type** hash
  `0xaca39a2d`, and it is used in exactly one instruction,
  `cmp dword ptr [r11 + 8], 0xaca39a2d` at `0x14027100c`, inside the typed
  accessor `0x140270fe0..0x14027104e` that hands back the `VehicleDamage` blob;
* that blob is the compiled struct image: `VehicleDamage` is declared
  **128 bytes** in the module's own type library, and its first 19 members decode
  at 4-byte strides from file offset `0x50`;
* **new finding / correction to `DAMAGE_MODEL.md`**: in the shipped bytes the
  `<channel>_armor` fields decode only as **int32** and every
  `<channel>_armor_strength` only as **float32** (`bullet_armor_strength` at
  `+0x08` is `0x42c60000` = `99.0f`, not `99`). The fleet's 0..100 strength
  domain is a float domain, so any gate on it is float arithmetic over a
  converted int, not integer division.

What it did **not** settle is the composition rule itself - the arithmetic that
turns an armour/strength pair plus a hit into health loss. Three whole-image
sweeps for the consumer are recorded in `ARMOR_STEP.md` §6 (211 / 910-in-330 /
4 candidates, every survivor read by hand, none indexes the block). The rule is
reported as **UNKNOWN** with the reason and the exact place it must live, not
guessed. So: partial, not done, and not blocked - the remaining work needs a
wider call-graph read through virtual dispatch.

Answer to the brief's fallback question ("if the step is data-driven elsewhere,
say where"): it is **not** data-driven anywhere; there is no table, curve or
coefficient block. The *values* are data (the `.vmodc` module), the *ordering and
size* are fixed by the compiled type in the exe - which is why an added member
crashed the game in B-18 (`Tools/scripts/bm_schema.py` records that exact
mechanism for `VehicleParts`: "the engine read `ik_chains` past the old struct").

Files written
-------------
* `Tools/scripts/jc3_armor_step.py` - the pass; `--write` / `--check` / `dump`.
  Recomputes every number from the exe bytes and the module bytes.
* `Research/JC3Grab/ARMOR_STEP.md` - the card (273 lines).
* `Research/JC3Grab/ARMOR_STEP.json` - the same, machine-readable (every offset,
  hash, RTTI slot and oracle result).
* `tmp/freebuff/reports/JC3-armor-step.md` - this report.

Scratch (not outputs): `tmp/freebuff/scratch/rt2.py` (RTTI -> vtable resolver),
`up.py` (caller walk), `scan_pairs.py`, `scan_gate.py`, `narrow_gate.py` (the
three sweeps), `a5.py`/`a6.py`/`a7.py` (earlier RTTI probes).

Inputs, all read-only: `D:/Games/Just Cause 3/JustCause3.exe`,
`E:/Modding/_gamedata/JC3grab/b13b/unpacked/editor/entities/jc_vehicles/00_shared/
modules/health/lave_health_medium.vmodc`, and the project's own
`Research/JC3Grab/DAMAGE_MODEL.md`. The game was never run, attached to or
injected into.

Commands and output
-------------------
All paths relative to `E:/Modding/JC3-Batmobile`. Deps come from `uv run --with`.
Heredoc bodies are summarised in parentheses; everything outside the parentheses
is the captured output, verbatim. Standalone commands are quoted as run.
`[junk]`-style abbreviations are marked with an ellipsis and never used to carry
numbers.

1. The damage classes that exist, by RTTI name (`.?A[VU]...@@` scan):

```
$ uv run --with numpy --with pefile --with capstone python - <<'EOF'
  (regex over the image for .?A[VU]<name>@@ where name mentions Damage/Armor)
EOF
?$CGameObjectCreator@VCDamageControllerArmor@@               0x142d71a70
CAreaDamage                                                  0x142d6bee8
CDamageController                                            0x142d88700
CDamageControllerArmor                                       0x142d870a8
CDamageListenerSystem                                        0x142d6c310
CDamageMsg                                                   0x142d5a740
CDamageNetworkMessage                                        0x142d81688
CDamageable                                                  0x142d656e0
CDamageablePointProxy                                        0x142d6e7b8
CIsTakingDamageCondition                                     0x142d641e0
CVehicleDamageState                                          0x142d62af8
IDamagePartOwner                                             0x142d8f568
```

2. The ADF vocabulary block, and whether code reaches it:

```
$ uv run --with numpy --with pefile --with capstone python - <<'EOF'
  (string_run scan for {VehicleDamage, bullet_armor, max_health}, then refmap)
EOF
run len 473 first (5406942816, 'EulerAngles') last (5406951149, 'UVScale')
index of VehicleDamage: 303
total direct code refs to these names: 0
total qword pointers to member names: 0
```

3. The hash function, proven against the hash the project already recorded for an
   `.epe` field (`DAMAGE_MECHANISMS.md`: `invulnerable` = `af4406fb`):

```
$ uv run python - <<'EOF'
  (jenkins / djb2 / djb2x / fnv1 / fnv1a / joaat / crc32 over b"invulnerable")
EOF
jenkins   invulnerable   0xaf4406fb
jenkins   bullet_armor   0x2b8a8075
target 0xaf4406fb (invulnerable, per DAMAGE_MECHANISMS)
```

4. All 30 member hashes against the whole image:

```
$ uv run --with numpy --with pefile --with capstone python - <<'EOF'
  (hash_jenkins per member, data.count(pack('<I', h)))
EOF
  max_health                     0xf42307c2    0 hits  []
  bullet_armor                   0x2b8a8075    0 hits  []
  bullet_armor_strength          0xa01b4117    0 hits  []
  ...  (all 30 rows: 0)
total hash-value hits: 0
```

5. The module's own type library (`jc3adf.Adf`):

```
$ uv run python - <<'EOF'
  (jc3adf.Adf on lave_health_medium.vmodc; print every type)
EOF
bytes 3741 magic b' FDA'
types: 4 instances: 1
  type 0xaca39a2d code 0x1 size   128 align  8 name VehicleDamage
  type 0xb2477bdd code 0x3 size    16 align  8 name A[PartDamageType]
  type 0x9724e4c1 code 0x1 size    32 align  8 name PartDamageType
  type 0xa62e34f9 code 0x1 size    16 align  8 name HashString

instances:
   {'name': 'lave_health_medium.vmod', 'name_hash': 322891520, 'type': 2896402989, 'offset': 80, 'size': 1300}
```

6. The type hash in code - one site, and it is a compare:

```
$ uv run --with numpy --with pefile --with capstone python - <<'EOF'
  (find pack('<I',0xaca39a2d); for .text hits decode the owning instruction)
EOF
cmp: cmp dword ptr [r11 + 8], 0xaca39a2d size 8
bytes at instruction: 41 81 7b 08 2d 9a a3 ac
fn 0x140270fe0 0x14027104e
```

7. The hash-naming method working one class over, on `CDamageControllerArmor`'s
   property binder - which is what makes the zero in (4) meaningful:

```
$ uv run --with numpy --with pefile --with capstone python - <<'EOF'
  (immediates loaded into r8d in 0x140b96a40, then hash_jenkins('damage_type'))
EOF
binder property hashes: ['0xcf4f7880', '0x7e867cd8', '0x3b731825', '0xcf2cdec9']
jenkins(damage_type)=0x7e867cd8 present=True
2 lines mention af4406fb
```

8. The instance image, read as u32/f32 at 4-byte strides from `data_off = 0x50`
   (this is where the int/float split became visible):

```
$ uv run python - <<'EOF'
  (dump 0x50..0x110 of lave_health_medium.vmodc as u32 and float)
EOF
  +0x00  0x000007d0          2000   float 2.802596928649634e-42
  +0x04  0x00001388          5000   float 7.006492321624085e-42
  +0x08  0x42c60000    1120272384   float 99.0
  +0x0c  0x00000005             5   float 7.006492321624085e-45
  +0x10  0x41a00000    1101004800   float 20.0
  +0x14  0x000000fa           250   float 3.5032461608120427e-43
  +0x18  0x42480000    1112014848   float 50.0
  +0x1c  0x00001388          5000   float 7.006492321624085e-42
  +0x20  0x42c80000    1120403456   float 100.0
  +0x24  0x00000000             0   float 0.0
  +0x28  0x00000000             0   float 0.0
  +0x2c  0x00001388          5000   float 7.006492321624085e-42
  +0x30  0x42c80000    1120403456   float 100.0
  +0x34  0xffffffff    4294967295   float nan
  +0x38  0x42c80000    1120403456   float 100.0
  +0x3c  0xffffffff    4294967295   float nan
  +0x40  0x42c80000    1120403456   float 100.0
  +0x44  0x00000000             0   float 0.0
  +0x48  0x00000000             0   float 0.0
  +0x4c  0x00fa041a      16385050   float 2.2960345402885344e-38
  +0x50  0x0014000a       1310730   float 1.8367239361444675e-39
  +0x54  0x00000005             5   float 7.006492321624085e-45
  +0x58  0x00000fa0          4000   float 5.605193857299268e-42
  ...
```

9. RTTI -> vtable (the layout used by the new script; COL carries u32 RVAs, the
   type descriptor's name is inline at `+0x10`, `pSelf` proves the match):

```
$ uv run --with numpy --with pefile --with capstone python tmp/freebuff/scratch/rt2.py CVehicleDamageState
### CVehicleDamageState: 1 vtable(s)
  td 0x142d62ae8 col 0x142890900 vt 0x1423bbc38 (12 slots)
    [ 0] 0x140784b80  rva 0x00784b80
    [ 1] 0x1407cb000  rva 0x007cb000
    [ 2] 0x1407cb010  rva 0x007cb010
    [ 3] 0x1403dd480  rva 0x003dd480
    [ 4] 0x14041c0f0  rva 0x0041c0f0
    [ 5] 0x140863580  rva 0x00863580
    [ 6] 0x14040c450  rva 0x0040c450
    [ 7] 0x14040c460  rva 0x0040c460
    [ 8] 0x140857850  rva 0x00857850
    [ 9] 0x1403bc130  rva 0x003bc130
    [10] 0x140857860  rva 0x00857860
    [11] 0x140857870  rva 0x00857870
```

10. The three consumer sweeps (candidate generators; every survivor read by hand):

```
$ uv run --with numpy --with pefile --with capstone python tmp/freebuff/scratch/scan_pairs.py
instructions swept: 1989332
scale-8 indexed struct accesses with 0 <= disp <= 0x400: 9003
functions with a 4-apart int32 pair through one base+index: 211

$ uv run --with numpy --with pefile --with capstone python tmp/freebuff/scratch/scan_gate.py
instructions swept: 1989332
int32+float32 4-apart pairs: 910 in 330 functions

$ uv run --with numpy --with pefile --with capstone python tmp/freebuff/scratch/narrow_gate.py
candidate functions with cvtsi2ss + a 100.0/0.01/1.0 constant: 4
  fn 0x14200c89d size  3875 robust-pairs 1 cvtsi2ss 2 float-consts 3 ops ['ucomiss']
  fn 0x1411033c1 size   424 robust-pairs 1 cvtsi2ss 1 float-consts 1 ops ['addss', 'comiss', 'divss', 'mulss', 'subss']
  fn 0x141104520 size   589 robust-pairs 0 cvtsi2ss 3 float-consts 1 ops ['mulss', 'subss']
  fn 0x140736900 size  2251 robust-pairs 0 cvtsi2ss 1 float-consts 2 ops ['addss', 'comiss', 'divss', 'mulss', 'subss']
```

11. The deliverable, and its own re-derivation:

```
$ uv run --with numpy --with pefile --with capstone python Tools/scripts/jc3_armor_step.py --write
ARMOR_STEP.json: vocabulary 473 names / 0 code refs; member hashes 0; struct 128 B; oracle sites 1
ARMOR_STEP.md: 273 lines; oracles 15/15

$ uv run --with numpy --with pefile --with capstone python Tools/scripts/jc3_armor_step.py --check
PASS: vocabulary 473 names with 0 code refs, 0 member-hash hits, 128 B struct, one type-hash site; oracles 15/15
```

UNKNOWNs
--------
* **The composition rule.** Tried: the three sweeps in (10), the typed accessor's
  one direct caller (`0x140288dc0`, which caches the blob at `[this+0x10]`), and
  the RTTI walk of `CDamageControllerArmor` (vtable `0x142445818`) and
  `CVehicleDamageState` (vtable `0x1423bbc38`). Not found because the gate is
  compiled code reached through a cached pointer and virtual dispatch, and the
  executable gives no name or hash handle on any armour member to anchor a
  search. Resolving it needs a wider static call-graph read through the vtables,
  or a live debugger - the latter excluded by the project rules ("never run the
  game"). The next static step is named in `ARMOR_STEP.md` §7.
* **Whether H1 or H2 is the rule.** Unchanged from `DAMAGE_MODEL.md`; nothing in
  this pass separates them. The float encoding of the strengths is consistent
  with a percentage gate (H1) but does not prove it, and this report does not
  claim it.
* **`max_health`'s unit** (pool vs scale) - the field decodes at `+0x00` as int32;
  nothing names a unit. Already carried by `DAMAGE_MODEL.md` step 6.
* **Layout after `deform_scale` (`+0x4c`).** The instance stops being
  4-byte-strided there; `0x00fa041a` fits two u16s (1050, 250) - the medium
  tank's `smoke_threshold` and `burn_threshold` - so the remaining 11 members
  cannot be laid out by stride alone. Not needed for the armour block, which ends
  at `+0x48`.
* **The other three property hashes** in `CDamageControllerArmor`'s binder
  (`0xcf4f7880`, `0x3b731825`, `0xcf2cdec9`). Brute-forced against every string
  in the image (85,775), every `name=` in the held `.epe` XMLs (380 distinct) and
  1,574 decoded JSON/XML files under `_gamedata`: no match. They are properties
  whose names the project has not yet decoded anywhere - not an error in the
  method, since `0x7e867cd8` did resolve to `damage_type`.

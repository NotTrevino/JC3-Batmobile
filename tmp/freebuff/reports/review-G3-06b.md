# review-G3-06b — audit of the Batmobile class-default decode

`VERDICT:` **minor issues**.

The record holds where it matters: both class default objects are read from the shipped packages
exactly as `CLASS_DEFAULTS.md` claims, `--check` is green, and **all five tags I re-read from raw
bytes decode to the values and names the document prints** (float, bool bit, object reference,
struct, int), as do **the two pointer tags whose names rest on the layout alone**. The names come
from a real `(class, offset, kind)` match in the BmSDK bindings, verified line by line.

**One systematic defect, evidence-column only:** all **10** `BoolProperty` rows cite the wrong
member in their `source` column. A `BoolProperty` payload is the whole 32-bit word, so an offset
maps to many members; the generator's `tag_source()` cites `members[0]` — the first member the
class declares at that offset — instead of the member whose bit is actually set. The *name* and
*value* columns are computed from `word & mask` over every member and are correct; the
`file:line` + `mask` that a reader would use to verify the row are not. Example: tag #22 is
correctly named `XrayMaterialsAssigned` from word `0x10` & mask `16`, but cites
`RVehicleBatmobile.g.cs:980 ... mask 0x00000001`, which is `GlidingIn`.

Worked from the two cooked packages read-only (`E:\Games\Batman - Arkham Knight\BmGame\
CookedPCConsole\{Startup,BmGame}.upk`) and the BmSDK-AK bindings (`E:\Modding\_tools\BmSDK-AK\
src\BmSDK\Generated`, MIT). Nothing was launched, attached to or written; **no file of the audited
task was modified** — the only new files are this report and one scratch reader.

## 1. Files written

- `tmp/freebuff/reports/review-G3-06b.md` — this report.
- `tmp/freebuff/scratch/audit06b.py` — the independent re-reader (uses
  `Tools/scripts/upk_read.py`'s `Package`/`walk_tags`, i.e. a **different container path** from
  the audited script, which uses `grab_packages_g305.PartialPackage`).
- `tmp/freebuff/reports/G3-07b1.md` — corrected one sentence about `git status` on the loader this
  card's earlier task only imports (it is untracked, not "unmodified per git").

No edits to `Tools/scripts/grab_class_defaults.py`, `Research/BatmobileGrab/CLASS_DEFAULTS.*`,
`BMSDK_OFFSETS.json` or any other task's output.

## 2. The claim under audit, and the check

`CLASS_DEFAULTS.md` claims 274 tags decoded and named with no `UNKNOWN (offset only)` row:
`BmScript.Default__RVehicleBatmobile` (`Startup.upk` export 7530, **93** tags) and
`BmGame.Default__RVehicleBatmobileBase` (`BmGame.upk` export 10923, **181** tags).

```
$ uv run --with pefile --with capstone python Tools/scripts/grab_class_defaults.py --check
OK BmScript.Default__RVehicleBatmobile 93 tags / BmGame.Default__RVehicleBatmobileBase 181 tags;
layout RVehicleBatmobile -> RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle
-> Pawn -> Actor; masks 449 (0 conflicts); overrides 2, subclass-only 60, base-only 148;
unnamed 0; md+json byte-identical to a fresh rebuild
exit=0
```

My own read of both exports, with a different package reader (`audit06b.py`):

```
object Default__RVehicleBatmobile  class RVehicleBatmobile  size 978  exports 174890  imports 7419
walk_tags from 0: 93 tags, consumed 976/978, stop=eof, tail=0000

object Default__RVehicleBatmobileBase  class RVehicleBatmobileBase  size 3186  exports 177031  imports 3268
walk_tags from 0: 181 tags, consumed 3184/3186, stop=eof, tail=0000
```

So the two headline numbers, the byte sizes, the `eof` stop and the 2-byte `0000` terminator are
**decoded and reproduced independently**. Counts, sizes and termination hold.

## 3. Five tags re-read from raw bytes

For each row: the tag header and payload bytes are printed from the export's own data, the value is
recomputed with `struct`, and the name is then checked against the BmSDK binding.

### 3.1 Float — `ChassisMass` = 210.0 (subclass tag #78)

```
tag #78  FloatProperty  payload_at=0x310  header=04 00 98 06
bytes around payload: 00 00 52 43 10 00 a4 06 ...
float  = 210.0  (bits 0x43520000)
layout SVehicle  offset 1688  kind FloatProperty  member ChassisMass  type=float
BmSDK  Engine/SVehicle.g.cs:1229  /// FloatProperty: ChassisMass
       Engine/SVehicle.g.cs:1233  get { ... ToManaged<float>(Ptr + 1688); }
```

Header `04 00` = FloatProperty, `98 06` = offset 1688, payload `00 00 52 43` = 210.0. Name, kind and
offset agree with the binding. **Holds.**

### 3.2 Bool bit — `XrayMaterialsAssigned` (subclass tag #22) — value holds, citation does not

```
tag #22  BoolProperty  payload_at=0xac  header=03 00 74 21
bytes around payload: 10 00 00 00 04 00 8c 21 ...
word   = 0x00000010  -> bits set [4]
layout RVehicleBatmobile  offset 8564  (5 members)
   GlidingIn                  mask=1      (0x0001)
   bAfterburnerIsOn           mask=2      (0x0002)
   bBattleModeAfterBurnerIsOn mask=4      (0x0004)
   bAfterburnerIsWarming      mask=8      (0x0008)
   XrayMaterialsAssigned      mask=16     (0x0010)
BmSDK  BmScript/RVehicleBatmobile.g.cs:1016  /// BoolProperty: XrayMaterialsAssigned
       ...:1020  get { ... (Ptr + 8564) & 16) != 0; }
```

`0x10 & 16 = 16` → **`XrayMaterialsAssigned = True`, other four false** — exactly what the document
prints. The five masks were confirmed against the five getters (`& 1`, `& 2`, `& 4`, `& 8`, `& 16`
at lines 980, 989, 998, 1007, 1016). Header `03 00` + `74 21` = offset 8564.

But the row's source column reads `BmScript\RVehicleBatmobile.g.cs:980 (off 8564, mask
0x00000001)`; line 980 is **`GlidingIn`**, whose bit is 0. **Value correct, evidence wrong** (see
§5).

### 3.3 Object reference — `AfterburnerSystem` (subclass tag #29)

```
tag #29  ObjectNCRProperty  payload_at=0x114  header=10 00 1c 12
ref    = 130137 -> Default__RVehicleBatmobile.ab  class=ParticleSystemComponent
layout RVehicleBatmobileBase  offset 4636  kind ComponentProperty
       member AfterburnerSystem  type=ParticleSystemComponent
BmSDK  BmGame/RVehicleBatmobileBase.g.cs:5302
       ToManaged<BmSDK.Engine.ParticleSystemComponent>(Ptr + 4636)
```

`0x121c` = 4636; the pointer resolves through the export table to a subobject of the CDO itself,
whose class `ParticleSystemComponent` **is** the declared type — the type oracle is satisfied, not
assumed. **Holds.**

### 3.4 Struct — `HeadLightsColourPursuit` (base tag #85)

```
tag #85  StructProperty  payload_at=0x528
header   0a 00 c4 1b 7c a4 00 00 00 00 00 00 10 00 00 00 00 00 00 00
bytes    00 00 80 3f 00 00 80 3f 00 00 80 3f 00 00 80 3f
struct name='HeadLightsColourPursuit' size=16 floats=[1.0, 1.0, 1.0, 1.0]
layout RVehicleBatmobileBase  offset 7108  kind StructProperty  type=FLinearColor
BmSDK  BmGame/RVehicleBatmobileBase.g.cs:7844  /// StructProperty: HeadLightsColourPursuit
       ...:7847  AsRef<BmSDK.GameObject.FLinearColor>(Ptr + 7108)
```

`0x1bc4` = 7108, name/size/array-index header present, payload 4 × `0000803f` = four 1.0 floats, and
the declared struct type is `FLinearColor` (16 B, RGBA) — the decoded shape matches the declared
type. The document labels this row `decoded (raw only)` / "struct layout not decoded", which is
**more pessimistic than the evidence** (name + type + 16-byte, 4-float payload all agree); that is
an understatement, not an error. **Holds.**

### 3.5 Int — `BattleModeYawOffset` = 16384 (base tag #62)

```
tag #62  IntProperty  payload_at=0x326  header=02 00 10 19
bytes    00 40 00 00
int    = 16384
layout RVehicleBatmobileBase  offset 6416  kind IntProperty  member BattleModeYawOffset  type=int
BmSDK  BmGame/RVehicleBatmobileBase.g.cs:7276  ToManaged<int>(Ptr + 6416)
```

`0x1910` = 6416, `0x4000` = 16384. **Holds.** (The unit — UE rotator units are 65536 per turn — is
not stated in the document and I do not assert it here; that stays UNKNOWN.)

## 4. The two pointer tags whose names rest on the layout alone

Both are `oracle_no-type` in the record: the referenced object is a **`Class`**, and the class
object lives in a package this export table does not resolve (`ref_class = None`), so the type oracle
cannot corroborate the name. For both, what the name rests on is: the offset, the kind alias
`ClassProperty ~ ObjectNCRProperty`, and **uniqueness of the member at that offset in the chain**.

```
--- class offset 5676 (0x162c): 1 tag
  tag #28  ObjectNCRProperty  payload_at=0xdc  header=10 00 2c 16
  ref    = 76614 -> RDmgType_Barge  class=None
  layout RVehicleBatmobileBase  offset 5676  kind ClassProperty  member RamDamageType  type=Class
  BmSDK  BmGame/RVehicleBatmobileBase.g.cs:6458  ToManaged<BmSDK.Class>(Ptr + 5676)

--- class offset 892 (0x37c): 1 tag
  tag #172  ObjectNCRProperty  payload_at=0xbe0  header=10 00 7c 03
  ref    = 89516 -> RInventoryManager  class=None
  layout Pawn  offset 892  kind ClassProperty  member InventoryManagerClass  type=Class
  BmSDK  Engine/Pawn.g.cs:3602  ToManaged<BmSDK.Class>(Ptr + 892)
```

Checks made:

1. **Offset**: the tag header's offset field is `0x162c` = 5676 and `0x037c` = 892, decoded from the
   payload, not from the layout.
2. **Kind**: the binding declares both as `ClassProperty` with `ToManaged<BmSDK.Class>`, and the
   cooked tag is `ObjectNCRProperty` — the same 4-byte pointer slot, mapped by the documented alias
   rule (`TAG_KIND`). Compatible.
3. **Uniqueness**: printing every member in the whole chain at those offsets yields exactly one row
   each (`RamDamageType` in `RVehicleBatmobileBase`, `InventoryManagerClass` in `Pawn`), so the name
   is not a choice between candidates.
4. **Corroboration (not an oracle)**: the referenced object names are `RDmgType_Barge` (a damage
   type class) and `RInventoryManager` (a manager class), which fit the declared `Class` slots.

**Both hold as far as the layout can carry them**, and the document is right to mark them: they are
the only two rows where a same-offset, same-kind *different* name could not have been excluded by
the referenced object's class.

## 5. The defect: all 10 `BoolProperty` rows cite the wrong member

Rule the generator applies (`decode_tag` → `tag_source`): every kind-compatible member at the tag's
offset is collected into `members`, and the source text is built from **`members[0]`** — declaration
order — while the value is `word & mask` per member. For a bool word the two only agree when the
first declared member happens to be set.

Recomputed for every bool row (word from `raw_hex`, masks from the same layout the generator used):

```
role     tag    off    word        true members (recomputed)                     cited
subclass #22    8564   0x00000010  XrayMaterialsAssigned                         RVehicleBatmobile.g.cs:980 mask=0x1
subclass #28    4576   0x00000840  CanBeCrushed,bAllowPMDodge                     RVehicleBatmobileBase.g.cs:5076 mask=0x20
subclass #72    2180   0x01000400  SelfDriveCanJumpDown,bAddNavMeshObstacle       RVehicle.g.cs:3476 mask=0x1000
subclass #73    2184   0x00001020  HeavyArmouredVehicle,TankLightsSwitchedOn      RVehicle.g.cs:3683 mask=0x8
subclass #86    1496   0x00001406  bAttachDriver,bDoExtraNetRelevancyTraces,...   Vehicle.g.cs:869 mask=0x2000
base     #1     4568   0x00400000  SelfDriveAllowBoost                            RVehicleBatmobileBase.g.cs:4572 mask=0x2000
base     #2     4576   0x00000800  bAllowPMDodge                                  RVehicleBatmobileBase.g.cs:5076 mask=0x20
base     #166   1676   0x04001000  bCanFlip,bIsBatmobile                          SVehicle.g.cs:968 mask=0x1
base     #179   256    0x41881800  bAICanStepUpOn,bCanStepUpOn,...                 Actor.g.cs:6555 mask=0x2
base     #180   264    0x003a82d0  bBlockActors,bBlocksTeleport,...               Actor.g.cs:7239 mask=0x2000

bool rows whose cited line/mask does not denote a set bit: 10
```

Spot-checked against the bindings:

- offset 8564: line 980 = `GlidingIn` `& 1`; the set bit is `& 16` = `XrayMaterialsAssigned`
  (line 1016). Cited line/mask = a **false** member.
- offset 4576 has **18** bool members (`& 1 … & 16384` at lines 5035…5162). Line 5076 is
  `BlockThrottleUntilReleased` `& 32`; the word `0x840` sets bits `0x40` and `0x800`. Cited
  line/mask again a false member.

Why this is **minor, not "needs rework"**:

- No *value* is wrong. In every row I checked (5 of 10 re-derived from the getters, all 10 recomputed
  from the word), `name` and `value_text` list exactly the members whose masks are set; `#22`'s
  `XrayMaterialsAssigned=True (other 4 false)` is correct, and `unassigned_bits = 0` in each row
  means the layout explains every set bit.
- No *name* is wrong: each offset resolves to a member set that the binding really declares there.
- The damage is confined to the `source` column of bool rows: the cited `file:line` and `mask` are a
  different property than the row names, so a reader checking the row as written would conclude the
  bit is clear.

Fix location, for whoever takes it: `tag_source()` in `Tools/scripts/grab_class_defaults.py` builds
the citation from `rec["members"][0]`; for `BoolProperty` it should cite the member(s) whose mask is
set in that row's word (or cite all members of the word and say which bits are set). A regression
oracle would be: for every bool row, `word & cited_mask != 0`, and a cited line whose getter mask
equals the cited mask.

## 6. Commands run, with output

```
$ uv run --with pefile --with capstone python Tools/scripts/grab_class_defaults.py --check
OK BmScript.Default__RVehicleBatmobile 93 tags / BmGame.Default__RVehicleBatmobileBase 181 tags;
layout RVehicleBatmobile -> RVehicleBatmobileBase -> RVehicle -> AkVehicle -> SVehicle -> Vehicle
-> Pawn -> Actor; masks 449 (0 conflicts); overrides 2, subclass-only 60, base-only 148;
unnamed 0; md+json byte-identical to a fresh rebuild
check_exit=0
```

```
$ uv run --with pefile --with capstone python tmp/freebuff/scratch/audit06b.py
########## subclass : Startup.upk export 7530 (Startup.upk)
object Default__RVehicleBatmobile  class RVehicleBatmobile  size 978  exports 174890  imports 7419
walk_tags from 0: 93 tags, consumed 976/978, stop=eof, tail=0000

--- class offset 1688 (0x698): 1 tag(s)
  tag #78  FloatProperty  payload_at=0x310  header=04 00 98 06
  bytes around payload: 00 00 52 43 10 00 a4 06 68 95 02 00 09 00 ac 06 47 fb 00 00 00 00 00 00
  float  = 210.0  (bits 0x43520000)
  layout SVehicle               offset 1688  kind FloatProperty    member ChassisMass                      type=float mask=None

--- class offset 8564 (0x2174): 1 tag(s)
  tag #22  BoolProperty  payload_at=0xac  header=03 00 74 21
  bytes around payload: 10 00 00 00 04 00 8c 21 00 00 a0 40 04 00 90 21 00 00 c8 41 04 00 9c 21
  word   = 0x00000010  -> bits set [4]
  layout RVehicleBatmobile      offset 8564  kind BoolProperty     member GlidingIn                        type=bool mask=1
  layout RVehicleBatmobile      offset 8564  kind BoolProperty     member XrayMaterialsAssigned            type=bool mask=16
  layout RVehicleBatmobile      offset 8564  kind BoolProperty     member bAfterburnerIsOn                 type=bool mask=2
  layout RVehicleBatmobile      offset 8564  kind BoolProperty     member bAfterburnerIsWarming            type=bool mask=8
  layout RVehicleBatmobile      offset 8564  kind BoolProperty     member bBattleModeAfterBurnerIsOn       type=bool mask=4

--- class offset 4636 (0x121c): 1 tag(s)
  tag #29  ObjectNCRProperty  payload_at=0x114  header=10 00 1c 12
  bytes around payload: 59 fc 01 00 10 00 24 12 5a fc 01 00 10 00 2c 12 5d fc 01 00 10 00 34 12
  ref    = 130137 -> Default__RVehicleBatmobile.ab  class=ParticleSystemComponent
  layout RVehicleBatmobileBase  offset 4636  kind ComponentProperty member AfterburnerSystem                type=ParticleSystemComponent mask=None
########## base : BmGame.upk export 10923 (BmGame.upk)
object Default__RVehicleBatmobileBase  class RVehicleBatmobileBase  size 3186  exports 177031  imports 3268
walk_tags from 0: 181 tags, consumed 3184/3186, stop=eof, tail=0000

--- class offset 7108 (0x1bc4): 1 tag(s)
  tag #85  StructProperty  payload_at=0x528  header=0a 00 c4 1b 7c a4 00 00 00 00 00 00 10 00 00 00 00 00 00 00
  bytes around payload: 00 00 80 3f 00 00 80 3f 00 00 80 3f 00 00 80 3f 0a 00 d4 1b 7b a4 00 00
  struct name='HeadLightsColourPursuit' size=16 floats=[1.0, 1.0, 1.0, 1.0]
  layout RVehicleBatmobileBase  offset 7108  kind StructProperty   member HeadLightsColourPursuit          type=FLinearColor mask=None

--- class offset 6416 (0x1910): 1 tag(s)
  tag #62  IntProperty  payload_at=0x326  header=02 00 10 19
  bytes around payload: 00 40 00 00 04 00 14 19 00 50 c3 47 02 00 18 19 14 00 00 00 06 00 3c 19
  int    = 16384
  layout RVehicleBatmobileBase  offset 6416  kind IntProperty      member BattleModeYawOffset              type=int mask=None

--- class offset 5676 (0x162c): 1 tag(s)
  tag #28  ObjectNCRProperty  payload_at=0xdc  header=10 00 2c 16
  bytes around payload: 46 2b 01 00 10 00 34 16 63 ae 02 00 10 00 3c 16 06 2d 02 00 10 00 44 16
  ref    = 76614 -> RDmgType_Barge  class=None
  layout RVehicleBatmobileBase  offset 5676  kind ClassProperty    member RamDamageType                    type=Class mask=None

--- class offset 892 (0x37c): 1 tag(s)
  tag #172  ObjectNCRProperty  payload_at=0xbe0  header=10 00 7c 03
  bytes around payload: ac 5d 01 00 10 00 8c 03 64 ae 02 00 01 00 b9 03 1e e8 00 00 00 00 00 00
  ref    = 89516 -> RInventoryManager  class=None
  layout Pawn                   offset 892  kind ClassProperty    member InventoryManagerClass            type=Class mask=None
```

```
$ for n in XrayMaterialsAssigned GlidingIn bAfterburnerIsOn bAfterburnerIsWarming bBattleModeAfterBurnerIsOn;
  do grep -n -A6 "BoolProperty: $n$" BmScript/RVehicleBatmobile.g.cs; done
--- XrayMaterialsAssigned
1016:    /// BoolProperty: XrayMaterialsAssigned
1020:        get { return (...ToManaged<int>(Ptr + 8564) & 16) != 0; }
--- GlidingIn
980:    /// BoolProperty: GlidingIn
984:        get { return (...ToManaged<int>(Ptr + 8564) & 1) != 0; }
--- bAfterburnerIsOn
989:    /// BoolProperty: bAfterburnerIsOn
993:        get { return (...ToManaged<int>(Ptr + 8564) & 2) != 0; }
--- bAfterburnerIsWarming
1007:    /// BoolProperty: bAfterburnerIsWarming
1011:        get { return (...ToManaged<int>(Ptr + 8564) & 8) != 0; }
--- bBattleModeAfterBurnerIsOn
998:    /// BoolProperty: bBattleModeAfterBurnerIsOn
1002:        get { return (...ToManaged<int>(Ptr + 8564) & 4) != 0; }
```

```
$ (JSON) subclass tag #22
offset_hex       0x2174
tag_type         BoolProperty
name             XrayMaterialsAssigned (1 of 5 bools in the word)
word_hex         0x00000010
raw_hex          10000000
value_text       XrayMaterialsAssigned=True (other 4 false)
label            derived
unassigned_bits  0
unknown_masks    []
source           BmScript\RVehicleBatmobile.g.cs:980 (off 8564, mask 0x00000001)
members:
   GlidingIn                      mask=1  mask_hex=0x00000001 value=False file=...:980
   XrayMaterialsAssigned          mask=16 mask_hex=0x00000010 value=True  file=...:1016
   bAfterburnerIsOn               mask=2  mask_hex=0x00000002 value=False file=...:989
   bAfterburnerIsWarming          mask=8  mask_hex=0x00000008 value=False file=...:1007
   bBattleModeAfterBurnerIsOn     mask=4  mask_hex=0x00000004 value=False file=...:998
md row #22:
| 22 | `0x00ac` | 8564 | `XrayMaterialsAssigned (1 of 5 bools in the word)` (RVehicleBatmobile) | BoolProperty |
  XrayMaterialsAssigned=True (other 4 false) | derived | BmScript\RVehicleBatmobile.g.cs:980 (off 8564, mask 0x00000001) |
```

```
$ grep -n -B3 "ToManaged<int>(Ptr + 4576)" BmGame/RVehicleBatmobileBase.g.cs   # 18 members, masks 1..16384
5035: ... & 1)    5044: ... & 2)    5053: ... & 4)    5062: ... & 8)    5071: ... & 16)
5080: ... & 32)   5089: ... & 64)   5098: ... & 128)  5107: ... & 256)  5116: ... & 512)
5125: ... & 1024) 5134: ... & 2048) 5143: ... & 4096) 5152: ... & 8192) 5161: ... & 16384)
$ sed -n '5070,5080p' BmGame/RVehicleBatmobileBase.g.cs
    {
        get { ... (Ptr + 4576) & 16) != 0; }
    ...
    /// BoolProperty: BlockThrottleUntilReleased
    ...
        get { ... (Ptr + 4576) & 32) != 0; }
```

```
$ (offset confirmation for the five tags + two pointers)
--- ChassisMass @ Ptr+1688  (Engine/SVehicle.g.cs)
1233: get { ... ToManaged<float>(Ptr + 1688); }
--- AfterburnerSystem @ Ptr+4636  (BmGame/RVehicleBatmobileBase.g.cs)
5302: get { ... ToManaged<BmSDK.Engine.ParticleSystemComponent>(Ptr + 4636); }
--- HeadLightsColourPursuit @ Ptr+7108  (BmGame/RVehicleBatmobileBase.g.cs)
7844: /// StructProperty: HeadLightsColourPursuit
7847: => ref ... AsRef<BmSDK.GameObject.FLinearColor>(Ptr + 7108);
--- BattleModeYawOffset @ Ptr+6416  (BmGame/RVehicleBatmobileBase.g.cs)
7276: get { ... ToManaged<int>(Ptr + 6416); }
--- RamDamageType @ Ptr+5676  (BmGame/RVehicleBatmobileBase.g.cs)
6458: get { ... ToManaged<BmSDK.Class>(Ptr + 5676); }
--- InventoryManagerClass @ Ptr+892  (Engine/Pawn.g.cs)
3602: get { ... ToManaged<BmSDK.Class>(Ptr + 892); }
```

## 7. What I did not verify (UNKNOWNs)

1. **The other 269 tags.** I re-read 7 of 274 from raw bytes (5 required kinds + both layout-only
   pointers) and recomputed the bool rows from their words; the remaining rows I did not decode
   independently. A full check would re-run the same walk with an independent name resolver; no
   disagreement surfaced in the 7, but that is not proof for the rest.
2. **`masks 449` and `0 conflicts`.** The `--check` output repeats these counts; I confirmed the 5
   masks on one word against the getters and confirmed the direction of the conflict test, but did
   not audit all 449.
3. **Whether a stream is a delta list against the parent class's CDO.** The document itself declares
   this unproven (§9 there); nothing in the bytes I read settles it, so "the subclass overrides
   these 2 values" remains derived from stream comparison only.
4. **The `16384` unit** of `BattleModeYawOffset`. Bytes and name hold; the unit (UE rotator units)
   is a general convention, not something in these files, so it stays unasserted.
5. **§7a's component claims** (`0x13c` = `ReplacementPrimitive`, `0x16c` = `PerInstanceRandom`) were
   outside this audit's brief and were not re-read.

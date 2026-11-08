# review-G3-02f - the 44 sampler fields, checked against the BmSDK generated sources

STATUS: done

## VERDICT

**ACCEPT WITH ONE SCOPE CORRECTION.**

Ten of the 44 offsets were re-read from the `.g.cs` sources, including all seven bool bit-fields.
**10 of 10 are exact**: same offset, same kind, same bit mask, same `Ptr + N` getter. The X
conclusion also survives - there is no X-named field anywhere in the 5,468-file generated tree -
**but the card's "tried" record for X is narrower than its conclusion**, and it never names the
quick-gadget state fields that sit one field away and would let a read-only sampler prove the X
press indirectly.

* **Offsets 10 of 10 exact.** `781`, `786`, `2400`, and the bools `2084 &1`, `2084 &2`,
  `2396 &1`, `2396 &2`, `4568 &0x4000`, `4568 &0x20000000`, `3452 &0x80000`. No off-by-one, no
  decimal/hex slip, no kind mismatch (`u8` stays `u8`, `tarray` stays `tarray`).
* **Every bool mask is the right bit for its word.** Where two card rows share a word, the masks
  are distinct and both are present in the getter: `2084` carries `ContinuousFire &1` and
  `bFiring &2`; `2396` carries `bBoosting &1` and `bWarming &2`; `4568` carries
  `bBoostLocked &16384` and `InfiniteBoost &536870912`; `3452` carries `UsedQuickGadget &524288`
  beside `QuickGadgetOnRT &1048576`. A wrong mask would show up here as a duplicate bit; there is
  none.
* **Every cited `.g.cs` line is the comment line**, verified line-for-line, not just resolvable.
* **The field counts in the card's header table reconcile exactly** - and the only reason my first
  independent parse disagreed (`84` vs `79`) is my own error: the extra five are the nested
  struct block `ControllerSpin` (`InProgress/Triggered/Direction/PrevAngle/TotalSpin`,
  `RPlayerInput.g.cs:412-448`), which the card correctly excludes. Top-level counts per class:
  `RPlayerInput` 79, `RVehicleWeapon` 57, `RBatmobileMissileLauncher` 30, `RBatmobileBooster` 2,
  `RVehicleBatmobileBase` 518, `RPlayerController` 998 - identical to the card.
* **The X claim (UNKNOWN #1) is true as written for `RPlayerInput`**: 79 top-level blocks parsed,
  and none is named for X, a barrage, a quick-gadget slot or a weapon select. Tree-wide, the only
  X-ish property in 5,468 files is `AkDrawBoundsComponent.bX_Enabled` (a debug bounds flag).
* **What the card under-reports for X** (the correction). Six real quick-gadget fields and a
  three-function press/release/timeout trio exist in `RPlayerController` and are absent from the
  card entirely: `bGadgetButtonHeld` (`3448 &512`), `QuickGadgetOnRT` (`3452 &1048576`),
  `QuickGadgetTrigger` (float `5956`), `KeyboardQuickGadget` (int `6644`),
  `KeyboardSuperQuickGadget` (int `6648`), and `QuickGadgetX` / `ReleaseQuickGadgetX` /
  `QuickGadgetXTimeout`. The card does note that `QuickGadgetX` is a *Function* - correct - but
  stops before the press/release pair, which is the closest thing on disk to a named X action and
  the most plausible indirect observation route.
* **Two glosses in the card are unproven hypotheses, not evidence.** §5's
  "`bReadyGadgetButton` ... could be the gadget-wheel open" contradicts its own next row
  (`bGadgetSelectWheel` @784 *is* the wheel input), and `bReadyGadgetButton` @773 is the single
  strongest untested candidate: a real digital button byte in the same run as
  `bCancelButton` 774 / `bForensicsButton` 775 / `bHandBrakeButton` 776.
* **Header vs. body mismatch on scope.** The title says 44 fields "prove the X barrage and Y boost
  live". For Y that is fair (the input byte at 781). For X the set contains no field that observes
  the press: `UsedQuickGadget` is correctly labelled "a consequence of X, not the input byte", and
  every other X-adjacent member is left out. The card is honest row by row, but the headline
  overstates X by one step, and a sampler built from §1-§4 alone will see the barrage's
  *effects*, never its trigger.

Nothing here is a claim about Batman: Arkham Knight, Unreal Engine 3 or JC3 behaviour. Every line
below is a file + line + getter I opened in this session. `bmak_runtime_sampler.py` was **not**
edited (read-only per the brief); the only files I created are the DONE report and scratch
readers under `tmp/freebuff/scratch/`.

## The ten offsets, re-read

`F` = `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/BmGame`. Paths in the card are relative to
`BmSDK/Generated/`.

| # | field | card offset | card kind | card mask | card line | my read | match |
|---|---|---:|---|---:|---|---|---|
| 1 | `RPlayerInput.bVehicleBoostButton` | 781 | `u8` | - | `RPlayerInput.g.cs:944` | 781, `byte`, `Ptr + 781`, comment at 944 | **yes** |
| 2 | `RPlayerInput.bBatmobileEjectModifier` | 786 | `u8` | - | `:989` | 786, `byte`, comment at 989 | **yes** |
| 3 | `RBatmobileMissileLauncher.CurrentTargets` | 2400 | `tarray` | - | `RBatmobileMissileLauncher.g.cs:300` | 2400, `TArray<Actor>`, comment at 300 | **yes** |
| 4 | `RVehicleWeapon.ContinuousFire` | 2084 | `bit` | 1 | `RVehicleWeapon.g.cs:628` | 2084 `& 1`, comment at 628 | **yes** |
| 5 | `RVehicleWeapon.bFiring` | 2084 | `bit` | 2 | `:637` | 2084 `& 2`, comment at 637 | **yes** |
| 6 | `RBatmobileBooster.bBoosting` | 2396 | `bit` | 1 | `RBatmobileBooster.g.cs:82` | 2396 `& 1`, comment at 82 | **yes** |
| 7 | `RBatmobileBooster.bWarming` | 2396 | `bit` | 2 | `:91` | 2396 `& 2`, comment at 91 | **yes** |
| 8 | `RVehicleBatmobileBase.bBoostLocked` | 4568 | `bit` | 16384 (0x4000) | `RVehicleBatmobileBase.g.cs:4581` | 4568 `& 16384`, comment at 4581 | **yes** |
| 9 | `RVehicleBatmobileBase.InfiniteBoost` | 4568 | `bit` | 536870912 (0x20000000) | `:4716` | 4568 `& 536870912`, comment at 4716 | **yes** |
| 10 | `RPlayerController.UsedQuickGadget` | 3452 | `bit` | 524288 (0x80000) | `RPlayerController.g.cs:26194` | 3452 `& 524288`, comment at 26194 | **yes** |

Two card §5 candidates were re-read as well, both correct:
`RPlayerInput.bReadyGadgetButton` = 773 (`:872`) and `RPlayerInput.bGadgetSelectWheel` = 784
(`:971`).

Mask arithmetic in source, verbatim from the getters:

```
RVehicleWeapon.g.cs:628    get { return (ToManaged<int>(Ptr + 2084) & 1) != 0; }        // ContinuousFire
RVehicleWeapon.g.cs:637    get { return (ToManaged<int>(Ptr + 2084) & 2) != 0; }        // bFiring
RBatmobileBooster.g.cs:82  get { return (ToManaged<int>(Ptr + 2396) & 1) != 0; }        // bBoosting
RBatmobileBooster.g.cs:91  get { return (ToManaged<int>(Ptr + 2396) & 2) != 0; }        // bWarming
RVehicleBatmobileBase.g.cs:4581   .... & 16384) != 0;      // bBoostLocked      = 0x4000
RVehicleBatmobileBase.g.cs:4716   .... & 536870912) != 0;  // InfiniteBoost     = 0x20000000
RPlayerController.g.cs:26194      .... & 524288) != 0;     // UsedQuickGadget   = 0x80000
RPlayerController.g.cs:26203      .... & 1048576) != 0;    // QuickGadgetOnRT   = 0x100000 (same word)
```

## The X search - what I ran, and what it found

Searches (all against `E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated`, `--include=*.g.cs`):

| # | pattern | result |
|---|---|---|
| A | `Property: .*gadget` (`-i`) | ~230 hits, all inventory / HUD / prompt / config / gadget-select members. No input byte outside `RPlayerInput`'s two (§5 above). |
| B | `Property: .*(barrage\|quickgadget)` (`-i`) | `RInventoryGadget.QuickGadgetType:1977`, `RPawnPlayer.QuickGadgets:11303-11335` (int array), `RPlayerController.SpecialQuickGadgetAction:24538`, `UsedQuickGadget:26194`, `QuickGadgetOnRT:26203`, `bNewQuickGadgetControls:27031`, `QuickGadgetTrigger:30382`, `KeyboardQuickGadget:31090`, `KeyboardSuperQuickGadget:31099`, plus `bDisableQuickGadgetPrompts`, `bQuickGadgetsOnly`, `QuickGadgetIcons`, `bStartMissileBarrageTutorial`, `PlayedMissileBarrage1stTimeBark`. **No `Barrage` field on any vehicle or input class.** |
| C | `Property: .*(weaponselect\|selectweapon\|nextweapon\|prevweapon\|switchweapon\|changeweapon\|cycleweapon)` | `BattleModeWeaponSelectButtons:31627`, `BattleModeWeaponSelectOrigin/Size/ButtonSize` (`RPlayerController`), `SwitchWeaponBoneNotify` (anim), `bSwitchWeapon` (AI combat moves), `NextWeaponChange` (AI timer). **None is an input byte; the select buttons member is a UI/array property.** |
| D | `Property: .*(xbutton\|buttonx\|bX_\|_x_button)` | one hit: `Engine/AkDrawBoundsComponent.g.cs:118 bX_Enabled` (debug draw flag, different package). |
| E | `grep -rn "ReadyGadgetButton\|QuickGadgetX"` over all of `src` | `RPlayerInput.g.cs:872/874` (the byte), `RHUDPrompt.g.cs:554 CI_ReadyGadgetButton = 128` (prompt enum), `RPlayerController.g.cs:478/480/489/491/11317/11319` (functions), `RPlayerControllerCombat.g.cs:204/206/248/250` (overrides). |
| F | `*Input*.ini` anywhere in `src`; `ls src/BmSDK` | none (`BmSDK.csproj`, `Classes`, `Framework`, `FrameworkInternal`, `Generated`, `Loader.cs`, `NativeMethods.txt`, `packages.lock.json`). The bind table the card points at is not in this tree. |

Relevant decoded members the card does **not** list:

| field | offset | kind | mask | file:line | card? |
|---|---:|---|---:|---|---|
| `RPlayerInput.bReadyGadgetButton` | 773 | `u8` | - | `RPlayerInput.g.cs:872` | §5 only, as a rejected candidate |
| `RPlayerInput.bGadgetSelectWheel` | 784 | `u8` | - | `RPlayerInput.g.cs:971` | §5 only |
| `RPlayerController.bGadgetButtonHeld` | 3448 | `bit` | 512 (0x200) | `RPlayerController.g.cs:25816` | **no** |
| `RPlayerController.QuickGadgetOnRT` | 3452 | `bit` | 1048576 (0x100000) | `RPlayerController.g.cs:26203` | **no** |
| `RPlayerController.QuickGadgetTrigger` | 5956 | `f32` | - | `RPlayerController.g.cs:30382` | **no** |
| `RPlayerController.KeyboardQuickGadget` | 6644 | `i32` | - | `RPlayerController.g.cs:31090` | **no** |
| `RPlayerController.KeyboardSuperQuickGadget` | 6648 | `i32` | - | `RPlayerController.g.cs:31099` | **no** |
| `RPlayerController.QuickGadgetX()` | - | function | - | `RPlayerController.g.cs:491` | noted, but see below |
| `RPlayerController.ReleaseQuickGadgetX()` | - | function | - | `RPlayerController.g.cs:480` | **no** |
| `RPlayerController.QuickGadgetXTimeout()` | - | function | - | `RPlayerController.g.cs:11319` | **no** |

`bGadgetButtonHeld` (3448, bit 0x200) is the only *state* bit named for the gadget button and
sits in the word before `UsedQuickGadget`'s word; `QuickGadgetOnRT` shares `UsedQuickGadget`'s word
and is the pair the card's §4 row should have named next to it, because reading one without the
other cannot tell a press from a hold. What those two fields equal in live play, and whether
`KeyboardQuickGadget` holds a key code or an array index, is **UNKNOWN** - the generated getters
give the offset and type only, and there is no decompiled function body in this tree.

## Files

* `tmp/freebuff/reports/review-G3-02f.md` (this report)
* `tmp/freebuff/scratch/props.py`, `props2.py`, `props3.py`, `indent.py`, `size.py` (throwaway
  readers; no project file touched)

## Commands and output (verbatim, abbreviated only where marked)

Ten-offset read (`scratch/props2.py`; prints the comment line and text for each requested field):

```
### RPlayerInput  (84 property blocks)
  bReadyGadgetButton               ByteProperty   off=773    mask=-                      comment_line=872
      line text: /// ByteProperty: bReadyGadgetButton
  bVehicleBoostButton              ByteProperty   off=781    mask=-                      comment_line=944
      line text: /// ByteProperty: bVehicleBoostButton
  bGadgetSelectWheel               ByteProperty   off=784    mask=-                      comment_line=971
      line text: /// ByteProperty: bGadgetSelectWheel
  bBatmobileEjectModifier          ByteProperty   off=786    mask=-                      comment_line=989
      line text: /// ByteProperty: bBatmobileEjectModifier

### RVehicleWeapon  (57 property blocks)
  ContinuousFire                   BoolProperty   off=2084   mask=1 (0x1)                comment_line=628
  bFiring                          BoolProperty   off=2084   mask=2 (0x2)                comment_line=637

### RBatmobileBooster  (2 property blocks)
  bBoosting                        BoolProperty   off=2396   mask=1 (0x1)                comment_line=82
  bWarming                         BoolProperty   off=2396   mask=2 (0x2)                comment_line=91

### RVehicleBatmobileBase  (567 property blocks)
  bBoostLocked                     BoolProperty   off=4568   mask=16384 (0x4000)         comment_line=4581
  InfiniteBoost                    BoolProperty   off=4568   mask=536870912 (0x20000000) comment_line=4716

### RPlayerController  (1045 property blocks)
  UsedQuickGadget                  BoolProperty   off=3452   mask=524288 (0x80000)       comment_line=26194

### RBatmobileMissileLauncher  (30 property blocks)
  CurrentTargets                   ArrayProperty  off=2400   mask=-                      comment_line=300
```

(The `off=None` this first pass printed for `CurrentTargets` was my regex failing on the nested
generic `ToManaged<BmSDK.TArray<BmSDK.Engine.Actor>>`; the corrected pattern returns
`off=2400`, and the raw getter is `Ptr + 2400`.)

Count reconciliation (`scratch/indent.py`):

```
RPlayerInput                 top-level=79    nested=5     total=84
   nested names: [('InProgress', 412), ('Triggered', 421), ('Direction', 430), ('PrevAngle', 439), ('TotalSpin', 448)]
RVehicleWeapon               top-level=57    nested=0     total=57
RBatmobileMissileLauncher    top-level=30    nested=0     total=30
RBatmobileBooster            top-level=2     nested=0     total=2
RVehicleBatmobileBase        top-level=518   nested=49    total=567
RPlayerController            top-level=998   nested=47    total=1045
```

X carriers found (`scratch/props3.py`):

```
### RPlayerController
  bGadgetButtonHeld            BoolProperty   off=3448   mask=512        line=25816
      get { return (BmSDK.Framework.MarshalUtil.ToManaged<int>(Ptr + 3448) & 512) != 0; }
  QuickGadgetOnRT              BoolProperty   off=3452   mask=1048576    line=26203
      get { return (BmSDK.Framework.MarshalUtil.ToManaged<int>(Ptr + 3452) & 1048576) != 0; }
  bNewQuickGadgetControls      BoolProperty   off=3464   mask=65536      line=27031
  QuickGadgetTrigger           FloatProperty  off=5956   mask=-          line=30382
  KeyboardQuickGadget          IntProperty    off=6644   mask=-          line=31090
  KeyboardSuperQuickGadget     IntProperty    off=6648   mask=-          line=31099

### RPlayerInput
  bReadyGadgetButton           ByteProperty   off=773    mask=-          line=872
  bGadgetSelectWheel           ByteProperty   off=784    mask=-          line=971

### RBatmobileMissileLauncher
  CurrentTargets               ArrayProperty  off=2400   mask=-          line=300
      get { return ...ToManaged<BmSDK.TArray<BmSDK.Engine.Actor>>(Ptr + 2400); }
```

Function trio (`sed -n '470,500p' RPlayerController.g.cs`): `QuickGadgetB`, `ReleaseQuickGadgetX`
(`:480`, body calls `BmGame.RPlayerController.ReleaseQuickGadgetX`), `QuickGadgetX` (`:491`,
same shape as `:492` string above) - all `ProcessEvent` wrappers, i.e. functions, confirming the
card's claim; `QuickGadgetXTimeout` at `:11319` is the same shape and the card does not mention it.

Class size spot check (`scratch/size.py`): `RPlayerInput` declares `(size = 872)` at
`RPlayerInput.g.cs:8`, last top-level field `ControllerSpin` @856 + 4 = 860, so 12 bytes of tail
padding - consistent, and no field lives past 872.

## UNKNOWNs

1. **Is `RPlayerInput.bReadyGadgetButton` @773 the byte the X binding writes?** Tried: its offset,
   type and neighbours (774 `bCancelButton`, 775 `bForensicsButton`, 776 `bHandBrakeButton`) on
   `RPlayerInput.g.cs:872-899`; the name `ReadyGadgetButton` appears in exactly two places in the
   whole tree (`:872`, `:874`) plus a HUD prompt enum (`RHUDPrompt.g.cs:554`). No generated file
   maps a physical button to a field, so the name is all there is. Where it would be answered:
   the `BmInput.ini` bind table or the decompiled `QuickGadgetX` body - neither is in this tree.
2. **Do `bGadgetButtonHeld` / `QuickGadgetOnRT` / `QuickGadgetTrigger` track the X press?** Tried:
   their getters (`25816`, `26203`, `30382`) and the function trio. The offsets are decoded; what
   sets them is inside function bodies that the generated sources do not contain (each wrapper
   only issues a `ProcessEvent`). Where it would be answered: the UFunction bytecode in
   `Startup.upk` / `BmGame.upk`, or a live watch.
3. **What `KeyboardQuickGadget` (6644) / `KeyboardSuperQuickGadget` (6648) hold** - a key code, a
   bind index or an array index. Tried: `RPlayerController.g.cs:31090-31100`; the type is `int`
   and nothing in the tree constrains the value. Where it would be answered: `BmInput.ini`, or the
   function that consumes these ints in the bytecode.
4. **Whether an X press is observable at all through these 44 fields** - the field set gives the
   barrage's consequences (`UsedQuickGadget`, `bGadgetButtonHeld`, `CurrentTargets`, `bFiring`)
   and, at best, an unnamed byte. Tried: the five searches in the table above. Where it would be
   answered: a live watch of @773 with @3452/3448 in the same frame, which is an experiment, not
   a decode.

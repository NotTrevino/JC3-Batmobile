# Review — G3-02j (`Research/BatmobileGrab/EJECT_VELOCITY.md`)

**VERDICT: minor issues.** Every *claim* in the card re-reads correctly against the bytes — the
vector is three literal zero floats, the receiver is `EjectFromVehicle.Car.Mesh`,
`SetRBLinearVelocity` is the only velocity/force call in the body, and the launch-shaped call is
`TriggerSpecialMove` at `+1103`. The issues are of labelling and completeness, not of fact: the
card presents `bAddToCurrent` as if it were decoded (the cooked import stores no parameter names),
it tabulates jump tokens found by a byte scan as if they were parsed statements, and — the one that
matters for the question asked — it reports the third argument as an undecoded `0x4a` and the move
as UNKNOWN, although the same call's *receiver* (`Car.ShortRangeGlideKick`) names the move and the
card already had that evidence class in hand. A second project artifact, `DRIVINGMODE.md`,
decodes the same call differently (four arguments); the bytes show that read is a misparse of the
vector's zero payload, so `EJECT_VELOCITY.md` is the correct one of the two.

Reviewer is independent of the card. Inputs read: `EJECT_VELOCITY.md`, `EJECT_VELOCITY.json`,
`Tools/scripts/grab_eject_velocity.py`, `Tools/scripts/grab_eject_move.py`, `EJECT_MOVE.md`,
`DRIVINGMODE.md` line 49, `CLASS_DEFAULTS.json` (via the cards), `MODLOG.md` G3-02j entry.
Nothing was launched; no game file was written; no git command was run. Only this report was written.

## 1. The bytes I read, and the offset convention

Package `E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/BmGame.upk`,
sha1 `36b5903579b80e7e0d3036a605cbf803c64e5b32` (recomputed, equals the card's).

```
$ python tmp/freebuff/scratch/g2j_probe2.py
export 104931 EjectFromVehicle bytes 1335 class Function outer DrivingMode
export 105028 ToggleBattleMode bytes 238 class Function outer DrivingMode
export data len 1335
driverleave  at 387 (0x183)          canteject at 25     cockpit at 465
special      at 1125 (0x465)
```

All five call strings the card quotes sit exactly **22 bytes further into the export data** than the
card's script offsets (`+3`→25, `+365`→387, `+443`→465, `+513`→535, `+1103`→1125). So the card's
offsets are relative to a script base 22 bytes into the export blob; the delta is constant, which is
why its internal arithmetic is consistent. Below I quote the raw export-data offsets and give the
card's offset in parentheses.

## 2. Claim: the vector is `(0, 0, 0)` and it is a stop — **holds**

Raw bytes (`s[535:555]`, card `+513..+532`):

```
535 (513) 1c                FinalFunction
536..539  04 f7 ff ff       i32 -2300 -> Core.SetRBLinearVelocity   (class Function)
540 (518) 23                VectorConst
541..552  00 00 00 00  00 00 00 00  00 00 00 00      <- 12 bytes, all zero
553 (531) 28                1-byte bare token (the card's `False`)
554 (532) 16                EndFunctionParms
```

Resolved with `upk_read.Package.object_path`:

```
ref -2300 -> Core.SetRBLinearVelocity | class Function
```

**The three components are literals, not expressions.** They are the 12 zero bytes of one `0x23`
vector-constant token; there is no sub-expression, no variable read and no arithmetic inside the
argument, and the argument list closes on `0x16` after exactly 13 + 1 + 1 = 15 bytes, which is what
the card's byte accounting says. A zero vector with the add flag clear leaves the body at rest;
"stop, not launch" is a correct reading of these bytes.

Two label notes (not errors in the arithmetic):

* `bAddToCurrent` is **not** decoded here. `Core.SetRBLinearVelocity` is an imported `Function` with
  no script (the import table stores a class, a name and an outer, no parameter names), so the
  parameter's name and meaning come from the engine signature, not from `BmGame.upk`. The `0x28`
  token itself is identified as the false literal by its pairing with `0x27` in the same body
  (`2d 00 72 97 01 00 27` at `+473..+477` is a `LetBool` to `RPlayerController.bWaitingToDebounceCrouch`),
  which is corroboration, not a naming proof. The card states it as decoded.
* `cm/s` is a unit assertion, not a decoded field; the card does not label it.

## 3. Claim: the call is made on `EjectFromVehicle.Car.Mesh` — **holds**

Bytes `s[509:535]` (card `+487..+512`), decoded as two nested `0x19` Contexts:

```
509 (487) 19      Context
510 (488) 19        Context
511 (489) 00          LocalVariable  512..515 = e2 99 01 00 = 104930 -> EjectFromVehicle.Car
516..517    09 00     skip = 9
518..521    9b fb ff ff = -1125 -> Core.Mesh     (ComponentProperty)
522 (500) 00          flag
523..527    01 9b fb ff ff  InstanceVariable -1125 -> Core.Mesh   (the property read)
528..529    18 00     skip = 24
530..533    00 00 00 00  prop = null
534 (512) 00          flag
535 (513) 1c ...      the call
```

```
ref 104930 -> EjectFromVehicle.Car | class ObjectProperty
ref -1125  -> Core.Mesh            | class ComponentProperty
```

So the receiver is the `Mesh` component of the local `Car`, exactly as the card says — not a pawn
local and not `Self`. What the bytes do **not** say is the *type* of `Car`: the cooked function
stores no local-variable types, so "the Batmobile's rigid body" is the card's reasoning from the
name and from the body's other calls (`CantEjectFromBatmobile`,
`RemoveBatmobileBindsAndSetBatmanBinds`), not a decoded class. It is plausible and it is the only
vehicle local in the body, but the card presents it flatly.

Independent corroboration of the card's "only" claim, measured over the body (script base
`data[22:]`, 1 313 bytes):

```
$ python - <<'EOF'   (count final-call tokens to ref -2300; list calls named Velocity/Force/Impulse/SpecialMove)
script len from base22 1313
final-call token sites for ref -2300: [(513, '0x1c')]
calls mentioning Velocity/Force/Impulse/SpecialMove:
  [(513, '0x1c', -2300, 'Core.SetRBLinearVelocity'), (1103, '0x1b', 79525, 'TriggerSpecialMove')]
```

One velocity call, one special-move call, nothing else in either family.

## 4. Claim: the launch is `TriggerSpecialMove` — **holds, but the card stops one step short**

Bytes `s[1099:1138]` (card `+1077..+1115`):

```
1099 (1077) 19      Context                       <- outer: "virtual call on this expression"
1100 (1078) 19        Context                     <- inner: the object expression
1101 (1079) 00          LocalVariable 1102..1105 = 104930 -> EjectFromVehicle.Car
1106..1107    09 00     skip = 9
1108..1111    64 26 00 00 = 9828 -> RVehicleBatmobileBase.ShortRangeGlideKick   (ObjectProperty)
1112 (1090) 00          flag
1113..1117    01 64 26 00 00  InstanceVariable 9828 -> ShortRangeGlideKick
1118..1119    11 00     skip = 17
1120..1123    00 00 00 00  prop = null
1124 (1102) 00          flag
1125 (1103) 1b      VirtualFunction   1126..1129 = a5 36 01 00 = 79525
1130 (1108) 17      Self
1131..1135    00 e0 99 01 00  LocalVariable 104928 -> EjectFromVehicle.Loc
1136 (1114) 4a      1-byte token, no operand
1137 (1115) 16      EndFunctionParms
```

```
names[79525] = 'TriggerSpecialMove'          (name table, 84 813 names)
ref 104928  -> EjectFromVehicle.Loc | class StructProperty
ref 9828    -> RVehicleBatmobileBase.ShortRangeGlideKick | class ObjectProperty
```

The card's argument table (`Self`, `EjectFromVehicle.Loc`, `<0x4A …>`) is byte-exact, and its
"launch-shaped call" reading is right. What it does not report:

* `0x1b` is a **virtual** call, so the callee is resolved on the receiver's class. The receiver chain
  is `Context(Car).ShortRangeGlideKick` — the card's §4 lists the call but never its receiver, even
  though the same two-Context shape is decoded correctly for the velocity call in §2.
* **No move name or enum is passed as an argument.** The third argument is the one-byte `0x4a`
  (pass-through to the forwarding body's `ForceReplicateToClient`, per G3-02k). The move identity is
  the receiver: `RVehicleBatmobileBase.ShortRangeGlideKick`, whose class default names
  `GlideKick.GlideKickShort_FromBatmobile` — a fact the card had in the same
  `CLASS_DEFAULTS.json` it quotes in §5 (it lists the `Eject.*` special-move refs from that file but
  does not connect them to this call's receiver).
* Consequently §4's "its numeric parameters are not in BmGame.upk. UNKNOWN: the special-move asset"
  is true as written (the *numbers* are in `Startup.upk`), but "the special-move asset" is
  **known** from this package's own class defaults, and the follow-up card `EJECT_MOVE.md` (G3-02k)
  resolves it. The card should have said "asset named by the receiver's class default, numbers
  outside this package" instead of UNKNOWN.

## 5. Claim: the stop sits behind the `FFInRange` guard — **holds**

```
500 (478) 07        JumpIfNot
501..502    4f 03    operand u16 = 847 (0x034f)
503 (481) 2d        BoolVariable  504 flag 0  505..508 = de 99 01 00 = 104926
ref 104926 -> EjectFromVehicle.FFInRange | class BoolProperty
```

The `0x07` layout puts the block after the condition, so the `(0,0,0)` write runs only when
`FFInRange` is true — the card's §3 ordering is correct, and its hedge that the operand's meaning is
not established is honest.

## 6. Issues

1. **`bAddToCurrent` presented as decoded.** The name is not in the package (imported native
   function, no parameter metadata). Fix: label it "the second argument is the one-byte false
   literal; the parameter's name comes from the engine signature, not the bytes".
2. **The special move is called UNKNOWN although the same call's receiver names it.** Fix: decode
   and print the receiver `Context(Car).ShortRangeGlideKick`, and name the class default
   (`GlideKick.GlideKickShort_FromBatmobile`) while keeping the trajectory numbers UNKNOWN.
3. **The jump table is a byte scan presented as parsed jumps.** §6's 20 `EjectFromVehicle` rows and
   5 `ToggleBattleMode` rows come from looking for bytes `0x06`/`0x07`, not from statement tiling, so
   spurious rows are certain (e.g. `+417` and `+436` both with operand 0, and the `+607/+609`,
   `+633`, `+1142`, `+1252` cluster, sit inside multi-byte operands or expression payloads). The
   conclusion drawn from them ("no encoding places every operand inside the body") is safe — a
   200-byte body cannot have a byte operand of 291 — but the table should not be read as a jump
   inventory. Fix: mark the table "byte-scan candidates, not verified jumps", or parse statements.
4. **Conflict with `DRIVINGMODE.md` line 49**, which decodes this same call as
   `SetRBLinearVelocity(0, ref 0, ref 0, false)` with "EX_LocalVariable@521, EX_LocalVariable@526".
   In the bytes those positions are the vector's zero payload (`+521..+530` are twelve `00`), and a
   zero byte is the `LocalVariable` token, so a parser that does not know `0x23` is 13 bytes long
   reads two `ref 0` arguments out of the zeros. `EJECT_VELOCITY.md`'s two-argument decode is the
   correct one; `DRIVINGMODE.md` needs the same fix, and its row was not edited here.
5. **Minor**: §2's "`Core.Mesh` is the component whose native moves the body" is inference stated as
   fact (same class of unlabelled claim as `bAddToCurrent`).

## 7. What I could not check

* The **type of the local `Car`**: cooked function exports carry no local-variable type table, so
  "the Batmobile" is naming evidence (the local is called `Car`, the body is `EjectFromVehicle` on
  `RVehicleBatmobileBase`), not a decoded class. No manifest/registry was searched for it.
* The meaning of the one-byte token **`0x4a`**: it has no operand and no name in this project; both
  `EJECT_VELOCITY.md` and `EJECT_MOVE.md` leave it unnamed, and I did not find a census that fixes
  it. It is definitely not a move name (one byte, no FName index).
* Whether `0x28` is *semantically* false: corroborated only by the `0x27`/`0x28` pairing and by the
  call site; no boolean-typed call elsewhere was used to prove the pair.
* Runtime behaviour of any kind — no game was launched, nothing was injected, and no on-screen claim
  is made here or by the card.

## 8. What the card gets right, in one line

The eject body's only `SetRBLinearVelocity` is a literal `(0,0,0)` with the add flag clear on
`Car.Mesh`, behind an `FFInRange` guard: it is a stop, not the throw; the throw-shaped call is the
virtual `TriggerSpecialMove` on `Car.ShortRangeGlideKick`.

# review-G3-02k — the eject's special move, re-decoded

VERDICT: **minor issues**

The substantive chain holds and every number reproduces: the token at the call site is `0x1b` with
name index **79525 = `TriggerSpecialMove`**, its argument bytes are exactly
`17 00 e0 99 01 00 4a 16`, the vehicle's class defaults really are
**`GlideKick.GlideKickShort_FromBatmobile` (field 5484)** and **`2500.0` (field 6848)**, the move asset
in `Startup.upk` is export 169053 wrapping config 168882, and the animation
`Batmobile_Short_Range_Glide_Kick` (export 75836) carries root translation **(764.945, 0, 0)** over
**113 frames at 30 fps**, which recomputes to **204.896 /s** and **6.8299 /frame**. G3-02j still
agrees.

Two things are wrong in the presentation, neither of which changes a value:

1. **The `+1103` offset does not decode with `upk_read`.** In the export data `upk_read` returns
   (1,335 B), the `0x1b`+79525 token is at **+1125** and the argument bytes start at **+1130**; byte
   `+1103` is `0x99` (mid-way through a `0x19` reference). The card is using a script base **22 bytes
   into** the export data (1125 − 1103 = 22) and never says so, so its "decode at +1103" cannot be
   repeated from the package as returned.
2. **The unit "cm" is stated, not decoded.** Nothing in the animation export carries a unit; 764.945
   is a bare float triple. The card prints "cm" throughout (and 2500 "cm") with no scale field,
   conversion factor or cross-check against a known length, so the unit is a convention, not a
   decoded fact, and should be labelled as such.

## 1. `--check`

```
$ uv run python Tools/scripts/grab_eject_move.py --check; echo "check_exit=$?"
PASS  EjectFromVehicle holds exactly one TriggerSpecialMove call token
PASS  its argument list tiles to the 0x16 terminator and carries three arguments
PASS  the receiver chain re-serialises to the original bytes
PASS  the receiver chain ends on RVehicleBatmobileBase.ShortRangeGlideKick
PASS  the vehicle's class default for that property is GlideKick.GlideKickShort_FromBatmobile
PASS  and its ShortRangeGlideKickRange default is 2500 cm
... 17/17 checks pass
MATCH Research\BatmobileGrab\EJECT_MOVE.md
MATCH Research\BatmobileGrab\EJECT_MOVE.json
check_exit=0
```

## 2. The call site, decoded with `upk_read` (not the card's reader)

```
$ uv run python - <<'PY'   # upk_read.Package(BmGame.upk).data(104931)
export 104931 data bytes: 1335   (card: "script 1297 bytes")
bytes +1096..+1124: 01 00 16 19 19 00 e2 99 01 00 09 00 64 26 00 00 00 01 64 26 00 00 11 00 00 00 00 00
token at +1103: 0x99
0x1b + u32(79525) hits: [1125]
  at 1125: 1b a5 36 01 00 17 00 e0 99
names[79525] = 'TriggerSpecialMove'
```

So: the **claim that the call is a virtual `TriggerSpecialMove` with name index 79525 holds**
(`1b a5 36 01 00`), and the 8 argument bytes `17 00 e0 99 01 00 4a 16` occur verbatim at **1130**,
terminated by `0x16` at 1137. The card's own arithmetic (`+1103` token, args at `+1108`, terminator
`+1114`) is internally consistent but 22 lower than the export data; the report does not state the
base it subtracts, so "decode at +1103" with `upk_read` returns `0x99`, not `0x1b`. That is a
reproducibility defect in the offset label, not in the decode.

The argument structure is also what the card says: `0x17` (`Self`), then a reference word
`e0 99 01 00` (export 104928), then the one-byte token `0x4a`, then `0x16`. The third argument's
meaning stays UNKNOWN, correctly.

## 3. The two class defaults, field 5484 and 6848

```
ShortRangeGlideKick      offset 5484 (0x156c)  tag_type ObjectNCRProperty  value 169053
    value_text "GlideKick.GlideKickShort_FromBatmobile (RSpecialMoveConfigCo…"
    member: RVehicleBatmobileBase.ShortRangeGlideKick  RSpecialMoveConfig  (BmGame\RVehicleBatmobileBase.g.cs:6238)
ShortRangeGlideKickRange offset 6848 (0x1ac0)  tag_type FloatProperty  value 2500.0
    raw_hex "00401c45"  (1.0f-based float 2500.0)  label "decoded"
```

**holds, exact**: 5484 is the `ShortRangeGlideKick` `ObjectNCRProperty` whose value is export 169053
(the card's asset), and 6848 is the `FloatProperty` 2500.0. The card's table gives both numbers and
both owners correctly.

## 4. From the asset to the animation

```
$ uv run python - <<'PY'   # Startup.upk
find('GlideKickShort_FromBatmobile') -> 169053
  export 169053: 10 B  raw: 10 00 90 01 b2 93 02 00 00 00
  export 168882: 122 B  raw head: 09 00 90 01 72 04 00 00 …
```

The wrapper's raw bytes are a single tag: `0x10` (ObjectNCRProperty) with the layout word, then the
reference `b2 93 02 00` = **168882** (0x293b2) and the `00 00` terminator — exactly the card's
"single-property wrapper whose property is the inner config". The config is 122 B, matching the card.

**holds**: asset → config → `AnimName` array (two FNames) → `AnimSet` 81597 → 55 sequences → the two
glide-kick exports.

## 5. Root motion, recomputed from the bytes

```
$ uv run python - <<'PY'   # export 75836, Startup.upk
bytes 392..444: 00 00 00 00 0b 00 6c 00 7b 3c 3f 44 00 00 00 00 00 00 00 00 0c 00 7c 00 …
vec @400: (764.9450073242188, 0.0, 0.0)   rot @416: (0, 0, 0)
NumFrames 113 at 524 ; Rate 30.0 at 532
d = 764.945007  dur = 3.733333  mean = 204.8960 /s  step = 6.8299 /frame
75835 has 949.433167 at 382
```

| card value | re-derived | verdict |
|---|---|---|
| root translation `(764.945, 0, 0)` | float triple at byte 400, preceded by the `0x0b` tag with layout word `0x006c` = 108 | **holds** |
| `(949.433167, 0, 0)` for the mid-range sibling | present at byte 382 of export 75835 | **holds** |
| 113 frames @ 30 fps | `113` at 524, `30.0` at 532; `(113−1)/30 = 3.733333` | **holds** |
| mean 204.9 cm/s | 764.945 / 3.733333 = **204.896** | **holds** |
| 6.83 cm per frame | 764.945 / 112 = **6.8299** | **holds** |
| vertical rise 0 | Y and Z are exactly `0.0` | **holds** |

A note on the offsets in the card's §4 table ("field 108", "124", "156", "160", "168"): those are the
**cooked tag's layout words**, not byte offsets — `0b 00 6c 00` means "vector property, layout offset
108", and the vector itself sits at byte 400. The card calls them "field"/"offset", which is
defensible as a class-layout offset, but reading `upk_read`'s export data *at byte* 108 returns
garbage; only the tag word is 108. Worth a one-line clarification, since the card also says "the
offset is the only handle".

**Units and frame.** The card *does* state both: distance in **cm**, motion over **113 frames at
30 fps**, duration **3.7333 s**. But:
- the frame/rate/duration are decoded (`NumFrames` 113, `Rate` 30.0, and `(n−1)/rate` matches the
  stored length on all 55 sequences), so that half is fine;
- the **unit has no in-file support**. Nothing in the export or the config carries a scale or a unit
  string, and no cross-check against a known length is given. "cm" is the UE3 convention, i.e.
  pretrained knowledge, not a decoded fact. The honest label is **UNKNOWN (cm by convention)**.

## 6. G3-02j — agreement

`tmp/freebuff/reports/G3-02j.md` says the `SetRBLinearVelocity` argument is the literal
`(0, 0, 0)` with `bAddToCurrent = false`, applied to `EjectFromVehicle.Car.Mesh`, and that this
**stops the car**; it also names `TriggerSpecialMove` as the only launch-shaped call and leaves its
numeric parameters UNKNOWN because they are not in `BmGame.upk`.

G3-02k agrees on all of that and supplies what 02j could not: the move asset, its config and the
animation's root translation. The two cards' claims are compatible — 02j's `(0, 0, 0)` is a *clearing*
of the car body's velocity, 02k's animation moves Batman. **No contradiction**; 02k supersedes 02j's
UNKNOWN without changing it.

The one thing to keep straight when citing the pair: 02j calls `0x23` a 13-byte vector literal and
02k's `0x4a` is a *different* token in a *different* call — they are not the same argument, and 02k
does not claim otherwise.

## 7. What I could not check

- **Per-frame root samples.** The keyframe block is zip-compressed and not decoded (as the card
  says); only the total and the mean are verifiable, and both are.
- **The `0x4a` token.** Its meaning is not established by this or the earlier card; I found no
  argument-width table in the project that resolves it.
- **Which of the two animations plays.** `AnimName` is a 2-element array and the parent body calls
  `PickRandomAnim`; I did not decode the selection.
- **The 22-byte base the card's `+1103` implies.** I verified the arithmetic (1125 − 1103) but not
  what the first 22 bytes of the export data are, since the card does not name its reader's base.
- **`AnimZip_LinearMotion` (field 992).** Recorded verbatim by the card, not interpreted; I did not
  decode it either.

## Commands run

```
$ uv run python Tools/scripts/grab_eject_move.py --check        # 17/17, MATCH md+json, exit 0

$ uv run python - <<'PY'   # upk_read on BmGame.upk export 104931
          export 104931 data bytes: 1335 ; token at +1103: 0x99 ; 0x1b+79525 hits: [1125]
          at 1125: 1b a5 36 01 00 17 00 e0 99 ; names[79525] = 'TriggerSpecialMove'
PY

$ uv run python - <<'PY'   # CLASS_DEFAULTS.json
          ShortRangeGlideKick  offset 5484  value 169053  "GlideKick.GlideKickShort_FromBatmobile"
          ShortRangeGlideKickRange offset 6848  value 2500.0  raw "00401c45"
PY

$ uv run python - <<'PY'   # Startup.upk
          169053: 10 B, tag 0x10 -> ref 0x293b2 = 168882 ; 168882: 122 B
          75836: vec@400 (764.945007, 0, 0) rot@416 (0,0,0) frames 113@524 rate 30.0@532
          mean 204.8960 /s ; step 6.8299 /frame ; 75835 has 949.433167 at 382
PY
```

Read-only: `BmGame.upk`, `Startup.upk`, `CLASS_DEFAULTS.json`, `EJECT_MOVE.md/.json`,
`grab_eject_move.py`, `G3-02j.md`, `EJECT_VELOCITY.md`. No file was edited; no new script was needed.

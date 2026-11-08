# DONE — branch polarity in `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode` (BmGame.upk 10894)

STATUS: **done** — the polarity was tested on six Functions in the same package, **6 of 6 agree (4 of 4
decisive)**, verdict: **the guarded body runs when the comparison is TRUE, i.e. `0x07` skips the body when
the expression is FALSE**. `Tools/scripts/grab_selector_polarity.py --check` passes (exit 0) and
`Research/BatmobileGrab/SELECTOR_POLARITY.md` / `.json` are written. No game was run or attached to, the
package was opened read-only, nothing under `Builds/` was touched, no git commit.

Labels: **decoded** = read from the package at the export + script offset shown (or from a named file);
**derived** = computed here by a stated rule; **UNKNOWN** = not established, with what blocked it.

## Result in one paragraph

The selector's guards are `0x07 <2-byte word> <expression>` with the mesh call immediately after the
expression's `0x16` terminator (decoded). Offset arithmetic does **not** settle the branch: across 17,201
scripts that close under a sequential token walk (58.1% of the 29,620 Functions), the 58,761
branch-shaped tokens land on a token start under the best of 11 candidate bases only 28.7% of the time
(derived). So polarity was read from **linear order** and tested on functions whose guarded call is fixed
by their own name: `HideHealthBarIfMax` (hides when `IsMaxHealth()` is true), `ShowHealthBarIfNotMax`
(shows when the negated call is true), `RVehicleNPCWeapon.Tick` (disables tick when
`CanDisableTick()` is true), `Primed.UnequipSelf` (refuses on `IsTimerActive()`, acts otherwise), plus
two supporting cases. In every case the expected
call sits in the bytes **after** the expression, so the body runs on TRUE. Consequence for the selector:
`DetachComponent(BatmanCollisionMeshPursuitMode)` runs when the old
`BatmanVsBatmobileCollisionMode == 1`, `AttachComponent(BatmanCollisionMeshBattleMode)` when the new
parameter `== 2`, etc. — the value→mesh table in `COLLISION_SELECTOR.md` stands as published, now with its
guard order read rather than assumed; the `0 = no mesh` row is unchanged.

## Method

1. **Selector re-read (decoded).** Export 10894, 253-byte script, sha1
   `c2f6a2ee667c544876e5317a103072c44ea17788` — equals the sha1 published in `COLLISION_SELECTOR.md`
   (oracle `sha1 equals G3-01e's`: True). Six `0x07` guard sites at 0, 32, 62, 89, 119, 180 with words
   352, 86, 125, 167, 206, 326; four mesh calls at 48 (detach), 78 (detach), 105 (attach), 135 (attach),
   each paired with the guard whose expression ends at or before it.
2. **Corpus branch-encoding test (derived).** Sequential token walk with a table whose extents are proven
   by closure (a script counts only when the walk consumes it exactly and ends on `0x04`). 17,201 of
   29,620 Functions close; 58,761 branch tokens: `0x06` 14,737, `0x07` 31,394, `0x18` 12,630. Each
   2-byte word was tried as absolute / payload-frame / token-relative / token+3 / end-relative, signed and
   unsigned; the best base is `abs_u` with 28.7%. No base resolves — reproduced on a larger sample than
   G3-01e's 74,632-token test, and the reason the verdict does not rest on offsets.
3. **Polarity test (the task's oracle).** For each case: `0x07` at offset 0, decode the expression, take
   the bytes after it as the guarded body, and check that the call the Function's name demands is there.
   A single disagreement among decisive cases would make the verdict UNKNOWN; none did.

## The six test functions (decoded values; verdict derived)

| Function | export | script B | guard word | expression (decoded bytes) | body call (decoded) | expected | role | agree |
|---|---|---|---|---|---|---|---|---|
| `RPlayerController.HideHealthBarIfMax` | 98241 | 16 | 19 | `1b 9c b1 00 00 16` = `IsMaxHealth()` | `HideHealthBar` | `HideHealthBar` | decisive | yes |
| `RPlayerController.ShowHealthBarIfNotMax` | 98240 | 18 | 21 | `81 1b 9c b1 00 00 16 16` = `0x81 IsMaxHealth()` | `ShowHealthBar` | `ShowHealthBar` | decisive | yes |
| `RPlayerController.ShowHealthBar` | 98237 | 54 | 81 | `f2 2d 01 46 98 01 00 28 16` = `0xf2(bShowHealthBar, FALSE)` | `SetHealthBarVisible` | `SetHealthBarVisible` | supporting | yes |
| `RPlayerController.HideHealthBar` | 98242 | 54 | 81 | `f2 2d 01 46 98 01 00 27 16` = `0xf2(bShowHealthBar, TRUE)` | `SetHealthBarVisible` | `SetHealthBarVisible` | supporting | yes |
| `RVehicleNPCWeapon.Tick` | 129889 | 17 | 16 | `1b 29 3b 00 00 16` = `CanDisableTick()` | `SetTickIsDisabled` | `SetTickIsDisabled` | decisive | yes |
| `Primed.UnequipSelf` | 48190 | 29 | 21 | `1c de f9 ff ff 2b fc 46 01 00 4a 16` = `IsTimerActive(<6-byte literal>)` | `UnequipSelf` | `UnequipSelf` | decisive | yes |

Why each is "certain": the first four come from the Function's own name (hide *if max*, show *if not
max*, show, hide) and the guarded body's own assignment (`bShowHealthBar = true/false` +
`SetHealthBarVisible(true/false)`, decoded); `RVehicleNPCWeapon.Tick` disables its tick under
`CanDisableTick()`; `Primed.UnequipSelf` is decisive by liveness — its guard body is `return false`, and
the inverted reading would make the function permanently unable to unequip, so the early return must fire
on TRUE. The two supporting rows wrap a property in `0xf2`, whose meaning is UNKNOWN, so they are
reported but not counted as decisive.

The sampler logs were checked and **cannot** corroborate these six: they log vehicle fields
(`BatmanVsBatmobileCollisionMode`, `Driver`, weapons, flags), not HUD visibility, tick state or gadget
state. The sampler is used only for the selector's mode/driver context (mode 1 only with no driver
seated, 5/5 samples; every 0→1 rise at a driver exit — `COLLISION_SELECTOR2.md` §3, decoded there), and
that context does not observe component attachment either. Recorded as a limit, not as evidence.

## Files written

| file | what |
|---|---|
| `Tools/scripts/grab_selector_polarity.py` | new script, `--write` / `--check`, re-derives every number from `BmGame.upk` |
| `Research/BatmobileGrab/SELECTOR_POLARITY.md` | the artifact (8,109 B) |
| `Research/BatmobileGrab/SELECTOR_POLARITY.json` | the same data (10,175 B) |
| `tmp/freebuff/reports/COLLISION-polarity.md` | this report |
| `tmp/freebuff/scratch/pol_proto.py`, `pol_enc.py`, `pol_cands.py`, `pol_cands2.py`, `pol_hex.py`, `pol_dump.py` | read-only scratch decoders; `pol_cands2.txt` (500-row candidate listing), `pol_dump.log`, `pol_hex.log` |

No other task's files were edited; `COLLISION_SELECTOR.md` / `COLLISION_SELECTOR2.md` were read only.

## UNKNOWNs

1. **Absolute targets of the `0x06`/`0x07`/`0x18` 2-byte words.** Tried: 11 bases (absolute, payload
   frame −22, token-relative, token+3, end-relative, signed and unsigned, token+2 signed) on 58,761
   branch tokens in 17,201 closed scripts. Best 28.7%, so no base is proven. Consequence: the verdict is
   read from linear order, which is what the six cases test; it does not depend on targets.
2. **The meaning of `0x9A` vs `0x9B`** (`==` / `!=`). Tried: every comparison site in the selector and
   the case set. No file or card in this repo assigns them a meaning; the decisive cases deliberately use
   call-shaped conditions only, so the verdict does not need it.
3. **The meaning of operator tokens `0xf2`, `0x77`, `0x81`, `0x82`, `0x2b`.** Their extents parse (params
   until `0x16`), their semantics do not. This is why the two `0xf2` rows are "supporting" only.
4. **The token walker is 58.1%, not 100%.** 12,419 Functions do not close under the table used here
   (unknown token extents, e.g. shapes that begin `3a 00 00`); they are excluded from the corpus figures
   rather than guessed at. Would be closed by a full statement/expression parser for this build.
5. **Sampler corroboration of any tested function.** The sampler logs no field any of the six guards
   sets; it would need added fields (HUD visibility, tick state) in a future sampler run.

## Commands run and their output

### 1. Prototype walk + unsigned jump-base test (`tmp/freebuff/scratch/pol_proto.py`)

```
$ uv run --with numpy python tmp/freebuff/scratch/pol_proto.py
exports 177031 functions: 29620
functions 29620 closed 17199 (58.1%) branches 58777
fail reasons [('no_return_end', 11940), ('overrun_long', 372), ('overrun_branch', 82), ('string', 27)]
jump targets landing on a token start, of 58777
   absolute             16865 (28.7%)
   after_insn+word      13498 (23.0%)
   word_from_end        13439 (22.9%)
   token_start+word     13290 (22.6%)
```

### 2. Signed/unsigned, per-opcode base test (`pol_enc.py`)

```
$ uv run --with numpy python tmp/freebuff/scratch/pol_enc.py
closed scripts 17199 jumps {'br07': 31404, 'br06': 14743, 'br18': 12630}

br06 (n=14743)
   abs_u          4047   27.5%
   abs_s          4047   27.5%
   tok+s          2764   18.7%
   tok3_s         2715   18.4%
   end-s          2274   15.4%
   payload  -22   2154   14.6%
br07 (n=31404)
   abs_u          7057   22.5%
   payload_u      6579   20.9%
   end-s          6108   19.4%
   tok+s          5147   16.4%
   tok3+s         5142   16.4%
br18 (n=12630)
   abs_u          5761   45.6%
   tok3+s         5656   44.8%
   end-s          5057   40.0%
   payload_u      3447   27.3%
```

(Full table in `tmp/freebuff/scratch/pol_enc.py` output; every base shown there, none dominant.)

### 3. Ground-truth guard bytes (`pol_hex.py`)

```
== RVehicleBatmobileBase.TakeDamage export 10436 script 2028 ==
   106  ff ff 07 cf 00 2d 01 ff 26 00 00 0f 00 c3 28 00  .....-..&.....(.
   122  00 91 90 00 c3 28 00 00 93 2c 64 01 06 26 00 00  .....(...,d..&..
```

This fixed the operand grammar: `0x2D 0x01 <int32>` is a 6-byte member ref (`0x2D 0x01 ff 26 00 00` →
`RVehicleBatmobileBase.ArmouredMode`, int32 9983), and a bare bool expression can follow `0x07` directly.

### 4. Guard+call candidate scans

```
$ uv run --with numpy python tmp/freebuff/scratch/pol_cands.py
wrote tmp/freebuff/scratch/pol_cands.txt rows 0
calls: []
```

(Too strict a grammar — comparison operands use member refs.)

```
$ uv run --with numpy python tmp/freebuff/scratch/pol_cands2.py
wrote tmp/freebuff/scratch/pol_cands2.txt rows 425
[('IsTimerActive', 47), ('NotEqual_InterfaceInterface', 16), ('IsWithinDualPlayTriggerWindow', 14),
 ('ShouldRenderItem', 10), ('IsBeingDisplayed', 9), ('CanDoCombat', 8), ('IsButtonInputIgnored', 8), ...]
```

Full 500-row listing: `tmp/freebuff/scratch/pol_cands2.txt`.

### 5. Body dumps (decisive evidence)

```
$ uv run --with numpy python tmp/freebuff/scratch/pol_dump.py
== RPlayerController.HideHealthBarIfMax export 98241 script 16 ==
     0 07  JUMPIFNOT? word=19 (signed 19)
     3 1b  CALL IsMaxHealth
     8 16  ENDPARMS
     9 1c  CALL RPlayerController.HideHealthBar
    14 16  ENDPARMS
    15 04  RETURN

== RVehicleNPCWeapon.Tick export 129889 script 17 ==
     0 07  JUMPIFNOT? word=16 (signed 16)
     3 1b  CALL CanDisableTick
     8 16  ENDPARMS
     9 1b  CALL SetTickIsDisabled
    14 27  TRUE
    15 16  ENDPARMS
    16 04  RETURN

== Primed.UnequipSelf export 48190 script 29 ==
     0 07  JUMPIFNOT? word=21 (signed 21)
     3 1c  CALL Core.IsTimerActive
    14 16  ENDPARMS
    15 04  RETURN
    16 28  FALSE
    17 04  RETURN
    18 1c  CALL RInventoryGadget.UnequipSelf
    24 04  RETURN
```

Inline dump for the companion health-bar functions (`ShowHealthBarIfNotMax`, `ShowHealthBar`,
`HideHealthBar`) produced:

```
== RPlayerController.ShowHealthBarIfNotMax exp=98240 len=18 ==
     0 07 BR07 word=21
     3 81 0x81
     4 1b CALL IsMaxHealth
     9 16 ENDPARMS
    10 16 ENDPARMS
    11 1c CALL RPlayerController.ShowHealthBar
    16 16 ENDPARMS
    17 04 RETURN

== RPlayerController.ShowHealthBar exp=98237 len=54 ==
     0 07 BR07 word=81
     3 f2
     4 2d MEMBER RPlayerController.bShowHealthBar (BoolProperty)
    10 28 FALSE
    11 16 ENDPARMS
    12 14 LETBOOL
    13 2d MEMBER RPlayerController.bShowHealthBar (BoolProperty)
    19 27 TRUE
    20 50  21 50  22 01 REF RPlayerController.ModularHud
    ...
    46 1c CALL RHudModuleHealthBar.SetHealthBarVisible
    51 27 TRUE
    52 16 ENDPARMS
    53 04 RETURN
```

### 6. Final script: write and check

```
$ uv run --with numpy python Tools/scripts/grab_selector_polarity.py --write
wrote E:\Modding\JC3-Batmobile\Research\BatmobileGrab\SELECTOR_POLARITY.md (8109 bytes)
wrote E:\Modding\JC3-Batmobile\Research\BatmobileGrab\SELECTOR_POLARITY.json (10175 bytes)
cases=6 agree=6 verdict=decided
EXIT=0

$ uv run --with numpy python Tools/scripts/grab_selector_polarity.py --check
json ok (6 cases)
md ok (8109 bytes)
selector sha1 c2f6a2ee667c544876e5317a103072c44ea17788
branch bases: best abs_u at 28.7%
CHECK OK
EXIT=0
```

A first `--write` run failed with `ValueError: expression does not parse at 208` (the selector's 0x18 skip
region); `expr_end` now falls back to the comparison's `0x16` terminator for that guard and records
`expr_rule: terminator-scan` in the JSON. A second run reported 4/6 because `first_call` stepped over an
operand byte `>= 0x80` and swallowed the call; the fixed version scans bytes and validates that the
call's params close inside the body — that is the 6/6 run above.

## Note on the earlier task in this session

The CONFIG refresh task finished before this one: `tmp/freebuff/reports/CONFIG-refresh.md` exists,
`Tools/scripts/grab_config2.py --write/--check` passes, and `Research/BatmobileGrab/CONFIG2.md` +
`CONFIG2.json` are written; `CONFIG.md` was not touched. Its own findings (three rewritten ini files, 41
changed rows) are unaffected by this task.

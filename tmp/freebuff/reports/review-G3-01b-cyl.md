# Independent review — G3-01b-cyl (the two CylinderComponent floats, named)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Read: `tmp/freebuff/reports/G3-01b-cyl.md`, `Research/BatmobileGrab/COLLISION_CYLINDERS.md`,
`Research/BatmobileGrab/COLLISION_CYLINDERS.json`, `Tools/scripts/grab_collision_cylinders.py`,
plus the class/CDO/ancestor/cylinder exports it decodes in `Engine.upk`, `Startup.upk`, `BmGame.upk`
and `Playable_Batmobile_SF.upk`.

Read-only: I ran `--check` only; I did **not** run `--write`. No game launched or read, nothing written
under `E:/Games` or `D:/Games`, no git command.

Method limitation: my spot-checks use the same decoder (`Tools/scripts/upk_read.py`). I compensated with
(a) the project's local BmSDK tree (`E:/Modding/_tools/BmSDK-AK`, MIT, named as a layout source in the
brief), which states the offsets independently, and (b) a package-side oracle the card did not use — the
`SetCylinderSize` parameter chain (§2, spot-check 5).

---

## VERDICT: **minor issues**

The answer is **correct and confirmed**: 540 = `CollisionHeight`, 544 = `CollisionRadius`,
548 = `AABBScale`. Every decoded value in the card reproduces byte for byte, the correction to
`COLLISION.md` (the 78.0/175.0 live in the BmGame base templates 142597/142598, not in the Startup
templates 82147/82148) is real, and the BmSDK layout agrees on all three offsets. The issues are in the
*strength of one derived claim* and in two UNKNOWNs that are resolvable from the same local sources — none
of them changes a value.

---

## 1. Check output (verbatim)

```
cd "E:/Modding/JC3-Batmobile" && uv run --with numpy --with pillow --with pefile --with capstone python Tools/scripts/grab_collision_cylinders.py --check; echo "CHECK_EXIT=$?"
```

```
OK: 540=CollisionHeight 544=CollisionRadius 548=AABBScale, 9/9 checks, md+pairing byte-identical=True
CHECK_EXIT=0
```

Matches the report's quoted line exactly.

---

## 2. Spot-checks — 5 decoded values re-read from the raw packages

| # | decoded value claimed | where I read it | match |
|---|---|---|---|
| 1 | `Engine.upk` export **4062** = class `CylinderComponent`, super `PrimitiveComponent`, with exactly ten members: `bForceGreenWhenSelected` 4048, `bAlwaysRenderIfSelected` 4049, `bDrawNonColliding` 4050, `bDrawBoundingBox` 4051, `CylinderColor` 4052 (Struct), `AABBScale` 4053, `CollisionRadius` 4054, `CollisionHeight` 4055 (Float), `SetCylinderSize` 4058, `GetExtent` 4061 (Function); `next` at +2 | export table + `data(i)` of each member | **yes** (all ten names, classes, sizes and `next` values exact) |
| 2 | CDO export **4063**, 114 B: walk from byte 0 → 10 tags, 114/114 parsed, no tail; `FloatProperty` @**540 = 22.0**, @**544 = 22.0**, @**548 = 1.0**, `StructProperty` @**552 = CylinderColor**, `BoolProperty` @**556**, inherited tags at 316/364/476/480/484 | `walk_tags(pkg, data, 0)` | **yes** (tags, offsets, values and full-consumption all exact) |
| 3 | no ancestor owns 540: `Default__PrimitiveComponent` (exp 3120) tops out at **528**, `Default__ActorComponent` (2635) at **120** | both CDOs walked | **yes** (PrimitiveComponent 18 tags, max offset 528; ActorComponent 1 tag, 120) |
| 4 | the Batmobile values sit in **BmGame base** 142597/142598 (`540 = 78.0`, `544 = 175.0`), and the **Startup** templates 82147/82148 plus the **Playable** instances 277/278 carry **neither** float | all six objects walked to their last byte | **yes** (Startup/Playable show only the offset-364 float; BmGame shows 78.0 / 175.0 on both) |
| 5 | the mapping itself: **540 = CollisionHeight, 544 = CollisionRadius, 548 = AABBScale** | *(a)* BmSDK `src/BmSDK/Generated/Engine/CylinderComponent.g.cs`: `CollisionHeight` → `Ptr + 540` (line 115/117), `CollisionRadius` → `Ptr + 544` (124/126), `AABBScale` → `Ptr + 548` (133/135), `CylinderColor` → `FColor` at `Ptr + 552`, bool bits at `Ptr + 556`; *(b)* package-side: function 4058's own parameter exports 4057 `NewRadius` (next = 4056) → 4056 `NewHeight`, a chain whose order equals BmSDK's declared signature `SetCylinderSize(float NewRadius, float NewHeight)` | **yes** — independently confirmed |

Spot-check 5 is the one that matters: it validates the card's key premise (chain order = declaration
order) with bytes from the same package, and the BmSDK header confirms the offsets outright.

---

## 3. Issues

### I1 — "Ascending is the only reading the types allow" is stronger than the evidence (conclusion unaffected)

The doc argues: the struct (`CylinderColor`, 552) and the bool word (556) sit **above** the three floats
and **after** them in the chain, therefore "the chain ascends with the offset", therefore the three floats
pair in chain order. The first inference is sound for the *block* boundary; the second does not follow by
types alone. Nothing in the types forbids a partial permutation such as `AABBScale = 540,
CollisionHeight = 544, CollisionRadius = 548` — the struct would still be above 548. What actually closes
it is a premise the card uses implicitly and never states: **chain order is declaration order**. That
premise is decodable from the same class and validates cleanly:

- `SetCylinderSize` has exactly two parameter exports: **4057 `NewRadius`** (`next` = 4056) and
  **4056 `NewHeight`** (`next` = 0) → chain order `NewRadius → NewHeight`;
- BmSDK's generated signature is `SetCylinderSize(float NewRadius, float NewHeight)` — the same order;
- the class's member exports are indexed in *reverse* declaration order (4055 `CollisionHeight` before
  4054 `CollisionRadius` before 4053 `AABBScale`), which is why the chain runs 4061 → 4048.

So chain = declaration is proven on an independently-typed case, and with declaration ascending within
the property block (floats 540/544/548, struct 552, bools 556) the mapping follows exactly as the card
states. Fix: replace "the only reading the types allow" with this premise and its evidence; the answer
does not change.

### I2 — two UNKNOWNs are resolvable, and one of them the card calls impossible

- **Which bool bit is which.** The doc: "*the word is serialised once, so its members are not separable
  from this stream*" — true of the stream alone, but the bit assignment is in the local BmSDK header:
  `556 & 1` = `bDrawBoundingBox`, `& 2` = `bDrawNonColliding`, `& 4` = `bAlwaysRenderIfSelected`,
  `& 8` = `bForceGreenWhenSelected`. With that, the CDO's own word is readable: I read
  **`bits = 0x00000009`** at offset 556 (stream offset 52), i.e. **`bDrawBoundingBox` and
  `bForceGreenWhenSelected` true, the other two false**. That is a decoded result, not an inference from
  the class defaults.
- **`CylinderColor`'s "fields (colour channels or flags)".** BmSDK types it `FColor` at 552 (4 bytes),
  matching the tag size 4. Whether it is B,G,R,A order is still not stated by that source, so that part
  stays UNKNOWN — but "channels or flags" narrows to "colour struct".

Neither is needed by the card's Done criterion; both are cheap and would remove two UNKNOWN lines.

### I3 — BmSDK was not used as the independent check, though the brief names it as a layout source

The card is explicit that it derived everything from `Engine.upk` "never from general knowledge", which is
the right instinct. But the project provides a local, MIT-generated layout tree
(`E:/Modding/_tools/BmSDK-AK`), and its `Engine/CylinderComponent.g.cs` states the three offsets
directly. A one-line cross-check would have upgraded "derived, with an ordering argument" to "derived and
independently confirmed", and would have caught the I1 gap without the parameter-chain work. Not an error
— a missed cheap oracle in a project that asks for oracles.

### I4 — check 2 is a drift guard, not an oracle

`check("the member linked list covers all ten and ends at 0", ... and [names] == EXPECTED_CHAIN)` compares
the decoded chain against a list hardcoded in the script from the same walk. It will catch future drift,
but it cannot validate the derivation (if the chain were decoded differently, both sides would need
editing). The genuinely independent checks are 4 (ancestor CDOs), 5 (own float slots), 6 (struct/bool above
the floats) and 9 (the Batmobile values). Say so, so "9/9" is not read as nine independent proofs.

### I5 — minor labelling

- Report's answer table is headed "*Answer (decoded + derived…)*" but the cells do not say which is
  which. The doc's own table header does it correctly (`name (**derived**)`); the report should split
  the columns the same way, since the *names* are the derived part and the *values* are decoded.
- The doc's containment sentence ("the five slots 540, 544, 548, 552, 556 and nothing else fits between
  them") is right, and BmSDK's `PropertiesSize = 560` corroborates the block end (540..559), though that
  number is not readable from the card's own evidence; label it as corroboration if it is added.
- Nothing else: the class export's 128 bytes and BmSDK's "size = 560" are the class object versus the
  instance size, and the card claims neither.

---

## 4. Resolvable UNKNOWNs

1. **Bool bits at 556 — resolved** (BmSDK masks 1/2/4/8) and the CDO word = `0x00000009` → `bDrawBoundingBox`
   and `bForceGreenWhenSelected` set. Where: `Engine/CylinderComponent.g.cs:143-186`; CDO export 4063,
   stream offset 52, offset 556.
2. **`CylinderColor` type — partially resolved**: `FColor` (4 bytes) at 552 per the same header; channel
   order not stated there, so the UNKNOWN narrows rather than closes.
3. **The chain-order premise — resolved from the package** (`SetCylinderSize`: 4057 `NewRadius` → 4056
   `NewHeight`, matching the declared parameter order), which is what lets I1 be fixed without new sources.
4. **Still genuinely UNKNOWN, as the card says:** whether `CollisionHeight` is half or full height (no
   convention in either source); the executable's property-registration table (the card's 336-site probe
   and 0 qualifying radial sites are an honest negative); and the 4-byte instance / 12-byte template
   stream prefixes.

---

## 5. What the card gets right

- All ten member exports, their types, sizes and `next` pointers reproduce exactly; the CDO walk from byte
  0 consumes all 114 bytes with 10 tags and none invented.
- The ancestor argument is real (no ancestor above 528), so 540/544/548 are this class's own slots.
- The correction to `COLLISION.md` is verified: Startup 82147/82148 carry only the offset-364 float, and
  the 78.0/175.0 pair is in BmGame 142597/142598.
- The refuted fleet hypothesis (548 = 1.0 everywhere) is recorded as refuted with the counter-values
  (0.4, 2.0) and explicitly *not* used — exactly the discipline the project asks for, and the same for the
  removed self-contradictory exe paragraph.
- `--check` re-derives the document and the pairing and fails on any check; nothing is stale.

---

## 6. Required changes (none alters a value)

1. Replace "the only reading the types allow" with the chain-order premise and cite the `SetCylinderSize`
   parameter chain (I1).
2. Close the bool-bit UNKNOWN and narrow the `CylinderColor` one (I2).
3. Add the BmSDK cross-check as confirmation, or say explicitly that it was not consulted (I3).
4. Relabel check 2 as a drift guard and list which checks are independent oracles (I4).
5. Split decoded from derived in the report's answer table (I5).

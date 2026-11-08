# WEAPONS.md bit-packed bools, named by offset + mask

STATUS: done

## Summary

`Research/BatmobileGrab/WEAPONS.json` recorded **26** `BoolProperty` tags with no name — a bool
that shares its 32-bit word with another bool cannot be named from an offset, so the record keeps
the raw word (`bits`). All 26 now decode to named members with masks and `.g.cs` file:line:

| quantity | count |
|---|---:|
| offset-only bool records | 26 |
| named | **26** |
| unresolved | **0** |
| distinct bool words | 12 |
| member fields named across those words | **231** |
| words shared by 2+ members | 12 |
| words with an object pair that proves bit order | 2 |
| words identical on every object (no flip exists) | 3 |
| words recorded on a single object | 7 |

The key correction to how these were described: a `BoolProperty` tag **does not carry a bit
index**. It carries the whole packed word, so "the tag's bit position" has to come from the
class's mask — which is exactly what the BmSDK generated getter states:

    get { return (BmSDK.Framework.MarshalUtil.ToManaged<int>(Ptr + 2396) & 8) != 0; }

Word = the tag's offset; bit = `log2(mask)`; the tag's value for that member = `(bits & mask) != 0`.

Examples of resolved members:

- `RBatmobileCannon`, word `0x095C` (2396) — 34 members named, including
  `bHasRiotSurpressor`, `bCanHurtThugs`, `bUseRiotTargettingForChainGun`,
  `bDisableCannonAimAtTargets`.
- `RBasicProjectile` / all four `0x010C` (268) words — **32** bool members declared in `Actor`
  (the 32nd has mask `0x80000000`, written `-2147483648` in C#; see the defect note below).

## Bit-order proof with objects whose words differ

Two multi-member words have objects that disagree, and in both the differing bits are exactly the
masks of named members:

1. word `0x095C` of `RBatmobileCannon`: `Playable_BatmobileFunhouse_SF.Batmobile_Cannon_V2` has
   `0x00000362`, `Playable_BatmobileJoker_SF.Batmobile_JokerCannon_V2` has `0x0000136C`; the XOR
   `0x0000100E` is precisely the masks of `bHasRiotSurpressor`, `bCanHurtThugs`,
   `bUseRiotTargettingForChainGun`, `bDisableCannonAimAtTargets`.
2. word `0x0420` of `RBatmobileMissile`: `Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile`
   has `0x00000018`, `Playable_BatmobileFunhouse_SF.Batmobile_Tracker_Projectile` has
   `0x00000002`; the XOR `0x0000001A` is the masks of `MustHitTarget`, `bForceExplodeAtTarget`,
   `bDisableAllCollision`.

The remaining shared words cannot be proven this way and are not claimed to be: three are
identical on every object that carries them (`RBatmobileCannon 0x0824` = 661,
`RBatmobileMissile 0x0338` = 512, `RBatmobileWinch 0x0970` = 8), and seven were recorded on a
single object. For those, the mask comes from the binding getter and the *ordering* is not
independently demonstrated.

## Files written

- `Tools/scripts/weapons_bools.py` (new, `--write` / `--check`)
- `Research/BatmobileGrab/WEAPONS_BOOLS.md` (21,673 B)
- `Research/BatmobileGrab/WEAPONS_BOOLS.json` (60,987 B)
- this report

`WEAPONS.md` was not edited. Read-only input outside the project: the BmSDK generated sources at
`E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated` (the path the card gave).

## Commands and output

### `--write`

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/weapons_bools.py --write
PASS  the 26 offset-only bool records parse and every class has a generated binding
      26 rows; classes 13, bound 22, missing []
PASS  every row resolves to at least one named bool member
      26 named, 0 unnamed []
PASS  every mask is a power of two and unique inside its word
      12 words, 231 members; non-power-of-two 0, duplicate masks 0
PASS  every bit set in any observed word is covered by a member mask
      words with orphan bits: 0 []
PASS  every shared word whose objects disagree flips only bits its members own
      12 multi-member words: 5 recorded on 2+ objects, 2 disagree and are explained, 0 disagree unexplained [], 3 identical on every object, 7 seen once
PASS  every citation states the member and its getter reads Ptr + offset & mask
      231 members cited, 0 wrong []
PASS  the words decode without residue (bits & ~or(masks) == 0 on all 26 rows)
      26 rows, residue []

7/7 oracles pass
wrote Research\BatmobileGrab\WEAPONS_BOOLS.md (21673 B)
wrote Research\BatmobileGrab\WEAPONS_BOOLS.json (60987 B)
```

Exit status 0.

### `--check`

```
$ PYTHONIOENCODING=utf-8 uv run python Tools/scripts/weapons_bools.py --check
... 7/7 oracles pass ...
CHECK OK: the stored .md/.json are byte-identical to a fresh recompute
```

Exit status 0.

## Defects found and fixed while building this

1. **The lineage search stopped at unparsed base classes.** Thirteen of the 26 rows sit at
   offsets declared far above the object's own class (`0x010C` is `Actor`'s, `0x0824`/`0x095C`
   are weapon-base words), so the first version named only 13 of 26. Fixed by loading ancestors
   recursively from the generated sources; 26/26 named, and the run now parses 22 classes instead
   of 13.
2. **Mask `0x80000000` was invisible.** The generated getter writes bit 31 as
   `& -2147483648`, which the decimal-only mask pattern rejected, leaving an orphan bit 31 in
   every `0x010C` word. Fixed by accepting the sign and taking `abs()`; the orphan-bit oracle
   now passes with 0 residue.
3. **The flip oracle demanded proofs that cannot exist.** Three words are identical on every
   object and seven appear once, so no differing pair exists. The oracle now requires the flip to
   explain the difference *where objects disagree*, and reports the other ten as limitations
   rather than failing (or silently passing) them.

## UNKNOWNs

1. **Bit order for the 10 words with no disagreeing objects.** The mask↔member mapping is the
   binding's own statement (`Ptr + offset & mask`), but no second object exercises those bits, so
   the order is not independently demonstrated for them.
2. **No per-tag bit index exists in the packages.** UE3 writes the whole bool word per tag; if
   two members at one offset are both true, the tag stream alone cannot say which tag is which
   member. This is why the decode is mask-based, not order-based.
3. **What each bool does mechanically.** Names and masks only; no behaviour is inferred.

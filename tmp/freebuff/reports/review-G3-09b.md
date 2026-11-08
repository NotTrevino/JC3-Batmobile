# Independent review — G3-09b (JC3 paint tint in the executable)

Reviewer: independent (did not write the card). Date: 2026-11-03.
Read: `tmp/freebuff/reports/G3-09b.md`, `Research/JC3Grab/COLOUR_NATIVE.md`,
`Research/JC3Grab/COLOUR_NATIVE.json`, `Tools/scripts/jc3_colour_native.py`.

Read-only: I ran `--check` only; no `--write`. `D:/Games/Just Cause 3/JustCause3.exe` was opened
read-only with `pefile`/`capstone`; nothing was run, attached, injected or written under `D:/Games`.
No git command.

Method: I re-parsed the PE myself, counted the strings, resolved the referenced addresses and
disassembled the sites the report names. Shared-dependency caveat: the reference oracle (rip-relative
disp32 + `.pdata` verification) is the card's design; I re-implemented the checks I could and
disassembled the three `CarPaintMM` sites by hand.

---

## VERDICT: **needs rework**

The address map is real: the 216-name schema run, its contiguity, `CarPaintMM` at `0x142332188`, the
`CarPaintMM%s%s%s` format string, the three referencing functions and their `.pdata` ranges all reproduce
exactly. But the card's **central negative evidence is false**: the report and the generated doc both state
that the 15 constants the parameter-block builder copies are `(0,0,0,0)` and that "0 of them are non-zero",
and build on that the conclusion "a call that stores only zeros cannot be what puts a paint colour into a
float4". The bytes are **not** zeros — they are small integers (0…10) that the tool's `round(x, 6)`
collapses to `0.0` because they are denormal floats. The conclusion may still be right, but as written it
rests on a measurement artifact, which is exactly what the ONE RULE forbids.

A second, smaller contradiction: the doc's §4 table and §4 prose disagree with each other and with the
report on the tone-name counts, because "occurrences" silently means *exact NUL-terminated string* in the
table and *substring* in the prose.

---

## 1. Check output (verbatim)

```
cd "E:/Modding/JustCause3/JC3-Batmobile" && uv run --with pefile --with capstone --with numpy python Tools/scripts/jc3_colour_native.py --check; echo "CHECK_EXIT=$?"
```

```
  scanning .rdata string runs ...
  resolving 222 target addresses in .text ...
  4 instruction sites verified
ok   the image is the JC3 executable and the PE parses (base 0x140000000, 188670 functions in .pdata)
ok   the 8 palette fields are one contiguous .rdata run in the ADF order of COLOUR.md (['Tint', 'occurrence', 'tint_r', 'tint_g', 'tint_b', 'specular_gloss', 'metallic', 'clear_coat'])
ok   every palette schema member has 0 code references (0), so the executable does not address tint_r/tint_g/tint_b by name
ok   CarPaintMM has verified rip-relative references landing in 3 function(s)
ok   the shader-variant format string `CarPaintMM%s%s%s` is present
ok   `TintColorR` does not occur in the image at all (0)
ok   no ToneMapping/Exposure occurrence is code-referenced (0 refs total)
ok   every listed constant is a real 16-byte .rdata read with 4 finite floats
ok   every reference site is inside a .pdata-bounded function
ok   no on-screen or tint value is claimed: the measured set is counts only
ok   E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\COLOUR_NATIVE.md is byte-identical to a fresh decode
ok   E:\Modding\JustCause3\JC3-Batmobile\Research\JC3Grab\COLOUR_NATIVE.json is byte-identical to a fresh decode

OK: 10/10 checks, md identical, json identical
CHECK_EXIT=0
```

Green — but see I1/I3: two of these "ok" lines are satisfied by rounded values.

---

## 2. Spot-checks — 5 decoded values re-read from the raw executable

| # | decoded value claimed | where I read it | match |
|---|---|---|---|
| 1 | the 8 palette names form one contiguous `.rdata` run at `0x14247A418 … 0x14247A455`, file offsets `0x2479618 … 0x2479655`, in the order `Tint, occurrence, tint_r, tint_g, tint_b, specular_gloss, metallic, clear_coat` | `pefile` section map + `d[fo:fo+len]`, checking each next string begins exactly at `prev+len+1` | **yes** (all 8, contiguity true, file offsets exact) |
| 2 | `CarPaintMM` occurs once, at VA `0x142332188`; variant format `CarPaintMM%s%s%s` at `0x142332268`; reference site 1 is `lea r8, [rip+…]` at `0x140105767` resolving to it | string bytes + `capstone` at `0x140105767`: `lea r8, [rip + 0x222ca1a]` → `0x142332188` | **yes** (and the third site, `0x140153484`, resolves there too) |
| 3 | the 15 constants the block builder copies are all `(0, 0, 0, 0)`; "0 of them are non-zero" | `struct.unpack_from("<4I", …)` at `0x1423310E0 … 0x1423311C0` | **no** — they are small integers: `(0,1,2,4)`, `(5,1,1,2)`, `(0,3,4,0)`, `(4,5,2,1)`, `(2,4,5,3)`, `(2,2,4,5)`, `(0,4,4,0)`, `(5,0,1,2)`, `(4,5,1,1)`, `(2,4,5,2)`, `(3,2,2,4)`, `(1,4,4,5)`, `(0,0,4,10)`, `(1,2,4,5)`, `(0,4,0,0)` — e.g. `0x142331100 = (0,3,4,0)`, printed by the doc as `0, 0, 0, 0` |
| 4 | the elf/PE counts: 51,083,264 B, base `0x140000000`, `.pdata` "188670 functions"; three reference functions of 458 / 765 / 1203 bytes at the stated ranges | `len(d)`, `OPTIONAL_HEADER.ImageBase`, `.pdata` `SizeOfRawData/12 = 188,672` slots, and the three ranges start on real prologues (`48 89 5c 24`, `48 8b c4`) | **yes**, with a note: `.pdata` has 188,672 12-byte slots; 188,670 have non-zero begin addresses (the tool's count) |
| 5 | tone-name counts: table `ToneMapping 0, ToneMap 0, Exposure 3, exposure 1`; prose "`ToneMapping` and `ToneMap` occur once each"; report `1, 1, 3, 3` | substring and exact-string census over the whole image | **no** — substring `1/1/3/3`, exact-string `0/0/3/1`. The single `ToneMapping` occurrence is inside **`ToneMappingDisabled`**; the three `exposure` substrings are `exposure`, **`exposure.ddsc`**, `exposure (new version): %.2f…` |

---

## 3. Issues

### I1 (blocking) — "all 15 constants are zero" is a rounding artifact, and the conclusion rests on it

`float4_at` returns `[round(x, 6) for x in struct.unpack_from("<4f", …)]`. The constants at
`0x1423310E0…` are denormal floats (`1.4e-45` etc.), so `round(x, 6)` turns every one into `0.0`. The
report's table, the doc's table ("0, 0, 0, 0" for all 15) and the derived sentence "*0 of them are
non-zero … a call that stores only zeros cannot be what puts a paint colour into a float4*" are all
consequences of that rounding. Read as integers the same bytes are `(0,1,2,4)`, `(5,1,1,2)`,
`(0,3,4,0)`, … up to `(0,0,4,10)`: a block seeded with **small integer patterns**, not a cleared block.

This does not make the block the tint writer — 1e-45 is not a colour either — but the card's stated
reason for excluding it is wrong, and the "not the tint writer" verdict is currently unsupported by the
evidence it cites. Two things to fix: print the raw 16 bytes (hex + int32 + float) next to every
constant, and re-derive the sentence from those. The small-integer seeds look like indices/flags, which
is a different (and testable) hypothesis worth stating.

### I2 — tone counts: the table, the prose and the report use three different definitions, and the prose is false

- Doc table (`ToneMapping 0`, `ToneMap 0`, `Exposure 3`, `exposure 1`) = **exact** NUL-terminated string
  occurrences.
- Doc prose "*`ToneMapping` and `ToneMap` occur once each, `Exposure` 3 times and `exposure` 1 times*" —
  the first clause is a **hardcoded string** in `render()`, not read from the data, and it disagrees with
  the table directly above it. It is also false as written: the string that occurs is
  `ToneMappingDisabled`, not `ToneMapping`.
- Report §C6 (`1, 1, 3, 3`) = **substring** counts, with no label saying so.

The column header "occurrences" never defines which. Fix: print both columns (`as substring`,
`as whole string`) or state the definition once, and replace the hardcoded prose with values.

### I3 — two checks cannot fail

- "every listed constant is a real 16-byte `.rdata` read with 4 finite floats" passes on the rounded
  list; it would pass on any bytes (even non-float words, because rounding removes denormals).
- "no ToneMapping/Exposure occurrence is code-referenced (0 refs total)" is **vacuous for
  `ToneMapping`/`ToneMap`**: `string_vas` found no VA for them (exact match fails on
  `ToneMappingDisabled`), so no reference scan was even attempted for those names. The check should
  target the string that exists (`ToneMappingDisabled`) and report what it resolves to.

Together with "no on-screen or tint value is claimed", the 10/10 headline overstates what was tested.

### I4 — `exposure.ddsc` is a lead the card dropped, and "dead data" is too strong for it

Two of the three `exposure` substrings are not debug text: `exposure.ddsc` is an **asset name**, and
`exposure (new version): %.2f` is a format string. I searched the extracted JC3 data
(`E:/Modding/_shared/gamedata/JC3grab`) for any file matching `*exposure*`: **none**, and no index mentions it.
So the useful statement is: the executable names an `exposure.ddsc` resource; that resource is not in the
extracted grab, so its values are still not available statically from what is on disk. The report's
"*the strings are dead data for this purpose*" is right for the bare `Exposure` triples and wrong for
`exposure.ddsc`.

### I5 — scope/status wording

- `.pdata` holds 188,672 slots; 188,670 is the count of non-zero begin addresses. Say which is which.
- The card's Done criterion ("find how a tint is chosen and written; exposure/tonemap constants") is
  **not met**. The report says `STATUS: partial`, which is honest and correct — but the tracker row still
  reads `G3-09b | queued (Freebuff) | task 2017`, so nothing anywhere records the partial result. Under
  §6b's "a card is done only when its Out file exists and its `--check` re-derives it", the file passes
  while the question does not; that gap should be named in the card's status line.

---

## 4. Resolvable UNKNOWNs

1. **U-4 (exposure/tonemap) is partly resolvable now.** The image carries `exposure.ddsc` as a true
   asset name (`0x142332CF1` region) plus a `.ddsc` loader path. Search the game archives for that
   resource id rather than for a constant: if the texture is present, its pixels are the exposure
   reference; if absent from the extracted grab, say so and require a runtime capture. I already checked
   the extracted data: no `*exposure*` file and no index hit, so the next step is the archive-level
   search, not another string scan of the exe.
2. **U-1 (which code writes the tint float4s) has a concrete next address.** The block builder stores the
   `CarPaintMM` name into `[rdi+0x10]` and immediately calls `0x14111A120` (`0x14015348F`). Decoding that
   callee — it receives the material name and the object — is the shortest route to the parameter struct,
   and it is a static read, not a guess.
3. **The "0 references" claim is stronger than the card says, for one specific reason I tested.** I
   searched the whole image for qword and dword copies of each palette string VA: **zero hits**. So there
   is no pointer table holding these names, which supports "not name-addressed" beyond the rip-relative
   scan. That removes one of the card's own caveats (its UNKNOWN 5) for the palette strings specifically
   — worth recording, since it is a positive test rather than a missing one.
4. **U-2/U-3 stay open**: nothing in the file ties a constant to a tint slot, and `Palette`/`tints` are
   still unreferenced as whole strings (I confirmed 0 exact matches for `tints` in code terms via the
   card's oracle; substring counts exist elsewhere, e.g. `PaletteManager`).

---

## 5. What the card gets right (keep it)

- The schema run, its 216 names, the 8 palette fields, their exact VAs/file offsets, and the contiguity
  argument all reproduce; the field order really is the `COLOUR.md` ADF order.
- The three `CarPaintMM` sites are genuine: I disassembled site 1 (`lea r8, [rip+0x222ca1a]`) and site 3
  (`lea rcx, [rip+0x21decfd]`), both resolving to `0x142332188`; the `.pdata` ranges are function-aligned.
- `TintColorR` really is absent (0 substring hits), and the format string really is where the doc says.
- The parameter block *is* copied to a stack frame (`movdqa xmm10, [rip+…]; movdqa [rbp+0x1e0], xmm10`),
  so the "initialises a parameter block" reading of the code shape is right — only the values are wrong.
- `--check` re-derives both files and fails on drift; the JSON matches the doc. The report's honest
  `partial` status and its five UNKNOWNs are the right shape.

---

## 6. Required changes

1. Stop rounding float constants: emit hex, int32 and float; re-derive the "all zero" sentence and the
   conclusion drawn from it (I1).
2. Define "occurrences" (substring vs whole string), print both, and delete the hardcoded
   "occur once each" prose (I2).
3. Make the two vacuous checks test something that can fail; target `ToneMappingDisabled` (I3).
4. Record `exposure.ddsc` as an asset-name lead and correct the "dead data" wording (I4).
5. State the `.pdata` slot count correctly and mark the card partial in the tracker (I5).

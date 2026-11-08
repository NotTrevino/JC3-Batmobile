# Chase 2-01 — second pass on the two rows left open by chase-01 (F-4, F-5)

Scope: the rows `Research/BatmobileGrab/chase/chase-01.md` leaves **STILL UNKNOWN** — **F-4**
(how a radial hit is decided) and **F-5** (tank shells to destroy the Batmobile). The other six
F-rows in that file are FOUND and are not revisited.

Read-only: no existing document was edited, no game was launched or patched, nothing was written
under `E:/Games` or `D:/Games`, nothing was committed. The only writes are
`Tools/scripts/chase/chase2_native.py` (new) and this file.

**Smart-search tool:** `tmp/freebuff/reports/smart-search.md` shows `STATUS: deferred
(chase_candidates not done)`, not `done`, so the condition for running `smart_search.py` first is
not met and it was not run. Both rows below were worked by hand.

**Result: 0 newly FOUND, 2 STILL UNKNOWN — one of them with a new decoded fact (F-5), the other with
the native route now exhausted as a documented negative (F-4).**

| row | fact | status | what changed this pass |
|---|---|---|---|
| F-4 | how a radial hit is decided (`ShouldRadialDamageHit`) | **STILL UNKNOWN** | five independent string/pointer anchor searches on `BatmanAK.exe`, all negative; the "native-binding name" chase-01 recorded is a substring artefact, and its VA was missing the image base |
| F-5 | tank shells to destroy the Batmobile | **STILL UNKNOWN** | the tank projectile class `RTankMissile` was never probed by chase-01; its class default decodes `Projectile.Damage` = **10.0** — the divisor chase-01 reported missing at every layer, now known at the class-default layer only |

---

## F-4 · how a radial hit is decided (`ShouldRadialDamageHit`) — STILL UNKNOWN

**Value:** none. It is a boolean decision in the executable, not a number, and the body was not
located.

**Provenance:** n/a (negative result). Nothing in this section is inferred as behaviour.

### What this pass proved (all new, all negative)

The route chase-01 stopped at was "no pointer from `.data` to the native-binding string". That is one
of six ways the name can be anchored; this pass ran the other five. Tool:
`python Tools/scripts/chase/chase2_native.py <cmd>` (new, reads only).

1. **The string is not a standalone literal.** ASCII `ShouldRadialDamageHit` occurs exactly once in
   the 55 101 440-byte image, at file `0x01E11E42` — and that occurrence is the **suffix** of
   `ARVehicleBatmobileBaseexecShouldRadialDamageHit`, which starts at file `0x01E11E28`
   (`.rdata`, VA **0x141E13028**). chase-01 read the substring as the `exec`-binding name and
   recorded VA `0x1E13028`, which is the RVA: the image base `0x140000000` was dropped.

   ```
   $ python - <<'EOF'
   d=open(r"E:\Games\...\BatmanAK.exe",'rb').read()   # read-only
   for s in (b"ShouldRadialDamageHit", b"execShouldRadialDamageHit", b"ARVehicleBatmobileBaseexec"):
       i=0; n=0
       while True:
           i=d.find(s,i)
           if i<0: break
           n+=1; i+=1
       print(s, n)
   EOF
   b'ShouldRadialDamageHit' 1
   b'execShouldRadialDamageHit' 1
   b'ARVehicleBatmobileBaseexec' 75
   ```

   Consequence: chase-01's sentence *"the native binding name is present exactly once"* is an
   artefact of searching for the bare function name. There is no bare-name literal to anchor on.

2. **No UTF-16 literal either.** UE3 registers natives with a `TEXT()` literal in some builds; the
   wide form is absent:

   ```
   $ python - <<'EOF'   # UTF-16LE + NUL NUL search over the whole image
   "ShouldRadialDamageHit" -> 0 hits
   "RadialDamageHit"       -> 0 hits
   ("AirControl" -> 40 hits, "BattleModeCamConfig" -> 0, "LifeSpan" -> 0: the control strings are
    found by the same scanner, so the zero is a real zero, not a broken search)
   EOF
   ```

3. **No pointer of any width anywhere in the image.** Three forms checked, 0 hits each:
   8-byte VA `0x141E13042` / `0x141E13028`; 4-byte RVA `0x1E13042` / `0x1E13028`; 32-bit offset
   relative to the start of the mangled-name block (`0x26D1B` / `0x26D31`).

   ```
   $ python Tools/scripts/chase/chase2_native.py ptr 0x141e13042
   0 hit(s)
   ```

4. **No RIP-relative reference from `.text`.** Every `48/4C 8D` (lea) with a RIP-relative operand in
   `.text` (raw `0x400`–`0x1958E00`, VA `0x140001000`–`0x14195891E`) was decoded and its target
   computed; **0** reach the string VA.

   ```
   $ python Tools/scripts/chase/chase2_native.py xref ShouldRadialDamageHit
   string VAs ['0x141e13042']
   0 xref(s)
   ```

5. **The mangled-name block is not a table either.** The block chase-01 found is contiguous and
   sorted by class — 2 893 names, VA `0x141DEC220`–`0x141E15F4B`. A lea scan into that whole span
   returns 26 references, and **every one lands mid-string** (relative offsets `0x1c`, `0xec`,
   `0x10c`, `0x14c`, `0x19c`, `0x244`, `0x30c`, … — none is a name start), i.e. they are unrelated
   operands whose displacement happens to fall inside the span, not table lookups.

6. **No other copy of the name in the repo's own records.** `DAMAGE_RULES.json` holds the *script*
   stub only (`Working/vendor/BmAKgrab/scripts/RVehicleBatmobileBase_ShouldRadialDamageHit.hex`):
   two parameter descriptors (`DamageLocation`, `DamageRadius`) and no body —
   `Research/BatmobileGrab/DAMAGE_RULES.json:1920-1950`. `NATIVE.json` lists the name as one of 341
   `ARVehicle*` function names harvested **from the same exe block** (`name_mentions`), so it adds no
   second anchor.

**Why this is a dead end rather than a missing effort:** the engine resolves natives at load time
from a `(class, name)` pair to a function pointer — the pointer only exists in memory after
registration, and this workspace has no PDB, no map, no IDA/Ghidra database and no runtime dump. A
brute-force disassembly of `.text` looking for a two-parameter UE3 `exec` prologue would be a guess
about which of 26.5 MB of code is the function; that is exactly the "plausible-sounding" step R4
forbids.

### What is known about the decision (cited, not re-derived)

`Research/BatmobileGrab/DAMAGE_RULES.md` §3.2 (decoded from the package script): the caller
`RVehicleBatmobileBase.TakeRadiusDamageFromWeapon` (288 B of script) calls the native as
`ShouldRadialDamageHit(HurtOrigin, DamageRadius)` **first**, and computes the distance falloff
(`Dist`, `ColRadius`, `ColHeight`, `Dir`, `DamageFalloffExponent`, literals 1500.0 / 0.5 / 0.1 /
1.0 / 0.0) itself afterwards. So the native's only job is the boolean gate over a blast sphere and
the vehicle, and everything downstream is script. The *inputs* are therefore known; which geometric
test the body runs (bounding-sphere vs. collision-cylinder, whether a line-of-sight trace is
included) is not.

### Routes tried this pass

- **(b) native, finished as a negative.** Six anchor searches (ASCII literal, UTF-16 literal,
  8-byte VA, 4-byte RVA, block-relative offset, `.text` lea xrefs), plus a span-wide xref census of
  the mangled-name block. No anchor exists. Body not located, nothing disassembled, no value
  invented.
- **(a) class defaults, extended.** `Default__RVehicleBatmobileBase` (`BmGame.upk`, export 10 923, 3 186 B)
  carries 201 tags; **none** is a radial/immune/explosion-gate member (`grep -iE
  "radial|immune|damag|explos|armou?r|resist"` returns `ImpactMaxDamage*`, `ArmourModeDamageReduction`
  20, `BatmobileOnFireDamageRadiusScale` 0.005 — all `TakeDamage` inputs, not this gate). So the
  decision has no serialised switch that answers it either.
- **(c) captures.** Not applicable: a boolean rule over a blast sphere has no number to time, and
  chase-01 already recorded that the clips show outcomes, not decisions.
- **(d) published sources.** Not used; the BmSDK-AK bindings re-declare the signature only, and no
  source carries the body (chase-01 checked this; it is not a value source anyway).

**What would close it:** a `.pdb`/`.map` for `BatmanAK.exe`, a runtime capture of the function
pointer after class registration, or an IDA/Ghidra database built elsewhere from this exact build.

---

## F-5 · tank shells to destroy the Batmobile — STILL UNKNOWN (divisor found at the class-default layer)

**Value:** the row's quantity (**how many tank hits destroy the Batmobile**) is **UNKNOWN**. What is
new: the tank projectile class is now decoded, and its class default carries
`Projectile.Damage` = **10.0 damage per direct hit**, `DamageRadius` **0.0 m**, `Speed` **1000.0
uu/s**. That is the divisor chase-01 reported as absent from every layer — but it is a *class
default*, not a proven shipped value, and it is scaled before it reaches health.

**Provenance:** decoded (class default tag) for the 10.0; derived arithmetic for the nominal count;
UNKNOWN for the row's answer.

### The newly decoded object

chase-01 probed `RVehicleNPCWeapon*`, `Projectile`, `RProjectile` and `RBasicProjectile` — the tank
*projectile* class `RTankMissile` was not in that list, and that is where the value is:

```
$ python Tools/scripts/chase/ch1_dlo.py dlo BmGame.upk Default__RTankMissile --want Damage
Default__RTankMissile  export[125214]  class=RTankMissile  size=174  chain=RTankMissile -> RProjectile -> Projectile
  Projectile.Damage (0x02D8)                           FloatProperty                10.0
  Projectile.DamageRadius (0x02DC)                     FloatProperty                0.0
```

Full tag list (16 tags, 8 named): `Projectile.Speed` 1000.0 (0x029C), `Projectile.MaxSpeed` 10000.0
(0x02A0), `Projectile.bSwitchToZeroCollision` True, `Projectile.Damage` 10.0, `Projectile.DamageRadius`
0.0, plus unnamed floats 0.5 / 15000.0 and four object references — no `DamageRadius` of 220 like the
base class, so a tank missile is a **direct-hit** weapon.

Two corroborations that this class is what shoots at the Batmobile:

- `Default__RDmgType_EnemyTankMissile` exists in the same package (`export[76783]`, chain
  `RDmgType_EnemyTankMissile -> RDmgType_EnemyExplosiveWeapons -> RDmgType_Explosion -> RDamageType ->
  DamageType`) — the engine's damage-type class for an **enemy tank missile**, distinct from the
  Batmobile's own types.
- The Batmobile's own damage handler branches on it: `DAMAGE_RULES.md` §3.1 item 6 —
  *"cast `DamageCauser` to `RProjectile`, **`RTankMissile`**, `RVehicleHeavyTank`…"*
  (`Research/BatmobileGrab/DAMAGE_RULES.md:102`).

The class default differs from its parent, which is why chase-01's base-class probes could not see
it: `Default__Projectile` (`Engine.upk`, `export[30536]`) carries `DamageRadius` **220.0** and
`Speed` **2000.0** and **no `Damage` tag at all**, so `RTankMissile` overrides both and adds Damage.

### Why the row is still UNKNOWN (three reasons, all measured)

1. **A class default is not the shipped value.** chase-01 proved this in both directions on F-2/F-3
   (archetype 0.0 vs CDO 0.3333) and F-1/F-7 (nothing overrides). The tank's *weapon archetype* —
   the object that can override `Damage` — is not in `BmGame.upk`; that package holds class defaults
   and states only. The enemy vehicles are placed by level/population packages outside the grab.
2. **The hit is scaled before it reaches health.** `TakeDamage` (script, `DAMAGE_RULES.md` §3.1)
   multiplies through `RGameInfo.VehicleCombatManager.GetDamageMod(DamagedActor, HitNumber,
   IncrementCurrentAttackHits)` — **native**, three parameters, so its value is not in a file — and
   radial hits additionally pass through the falloff in `TakeRadiusDamageFromWeapon` (§3.2). A
   direct missile hit (`DamageRadius` 0.0) skips the falloff but not `GetDamageMod`.
3. **No capture shows a tank hit.** All five clips carry no tank, so the count cannot be measured
   frame-by-frame either (chase-01's `NOT-IN-CLIP` reason is unchanged).

### The arithmetic, labelled as a bound and not as the answer

The Batmobile's health is `RVehicleBatmobile.Health` = [1200, 1200, 1200] (chase-01). At the class
default with no scaling: **1200 / 10.0 = 120 direct hits**. Reported only as a lower-layer figure —
it is implausible as the gameplay answer (tank hits visibly remove large health chunks), which is
itself evidence that an archetype override and/or `GetDamageMod` is doing the real work. Writing 120
into `FOOTAGE.md` as the shells-to-kill value would be a guess dressed as a decode, so it is not
done.

### Routes tried this pass

- **(a) class defaults — extended, and this is what produced the new fact.** Probed
  `Default__RTankMissile` (found 10.0) and the class defaults of every projectile class in
  `BmGame.upk` (`RProjectile`, `RBasicProjectile`, `RMortarProjectile`,
  `RBatmobileRocket_Projectile`, `RTankMissile`, `MSnareTrapProjectile`,
  `MStickyConcussionGrenadeProjectile`, `RBatarangProjectile`); **`RTankMissile` is the only one with
  a `Projectile.Damage` tag**, which is consistent with it being the enemy anti-vehicle round. Also
  re-probed `Default__RVehicleNPCWeapon`, `_Gun`, `_APCMissileTurret` — still no damage field on the
  weapon side. Re-read the showcase tank packages (`names`): `Showcase_Vehicles_HeavyTank.upk`
  (1 155 names / 461 exports), `Showcase_Vehicles_CommanderTank.upk` (1 270 / 393) and
  `Showcase_Vehicles_LightTankMissile.upk` (1 112 / 678) contain only `Batmobile_*_Shell_*` bone
  names and particle/mesh objects — art, not the weapon, confirming chase-01 on a wider set.
- **(a) archetype hunt — ruled out for a cheap scan.** There is no tank weapon/projectile archetype
  in `BmGame.upk` (only `Default__*` classes and properties), and a package-wide byte scan is not
  available: the `.upk` files are compressed, so even `BmGame.upk`, which certainly contains the name
  `RTankMissile` in its name table, returns **0** raw `grep` hits:

  ```
  $ grep -c "RTankMissile" BmGame.upk        # 214 757 637 B
  0
  ```

  A byte-level search for the archetype would therefore need the project reader on every package
  (4 145 files, 50 GB) — out of proportion to one row and not attempted.
- **(b) native** — not applicable beyond `GetDamageMod`: the damage *value* is data, and the native
  body question is F-4's, not this row's.
- **(c) captures** — re-checked: no tank, no hit, nothing to time.
- **(d) published sources** — not used (no cross-check target found that states an in-game hit count;
  a wiki's "3 hits" would be a gameplay report, not this build's number).

**What would close it:** the package (or archetype object name) that places the enemy tanks — one
`ch1_dlo.py dlo <pkg> <Archetype> --want Damage` then gives the shipped value; or a capture of a tank
shell hitting the Batmobile with the health bar visible, which would give the observed count
(falloff and `GetDamageMod` included).

---

## Corrections to chase-01 (recorded, files untouched)

1. **F-4 address.** chase-01 records the native-binding string VA as `0x1E13028`. That is the RVA;
   with the image base the VA is **`0x141E13028`** (section `.rdata` VA `0x14195A000`, raw
   `0x1958E00`, file offset `0x1E11E28`). The pass-1 arithmetic (`0x195a000 + (j - 0x1958e00)`)
   mixes section RVA with file offset and omits the base.
2. **F-4 "present exactly once".** The bare string does not exist as a literal; the one hit is the
   suffix of `ARVehicleBatmobileBaseexecShouldRadialDamageHit`. No literal, wide string, pointer or
   `lea` refers to the name, so it is not an anchor at all.
3. **F-5 "shell damage exists in no file".** True for the *archetype* layer chase-01 was looking at,
   but not for the class-default layer: `Default__RTankMissile` carries `Projectile.Damage` 10.0, and
   the class was simply not in the probe list.

## Method note

`chase2_native.py` is new (`sections` / `string` / `xref` / `disasm` / `ptr` / `ptrtable`) and reads
`BatmanAK.exe` with `rb` only. No game was launched, nothing under `E:/Games` or `D:/Games` was
written, no shared module (`FOOTAGE.md`, `chase-01.md`, `GRAB_BACKLOG.md`, `MODLOG.md`) was edited,
nothing was committed, and no secret is in this file.

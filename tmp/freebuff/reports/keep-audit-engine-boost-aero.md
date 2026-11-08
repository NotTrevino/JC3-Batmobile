# Keep-audit — engine, boost and aero (T-E2, T-E5, T-B1, T-B4, T-A1, T-A3)

Each row the ledger marks **keep** is restated against its BmAK source, then the JC3 value that
would give the same behaviour is derived. All built numbers below are **decoded from the shipped
`bm-RC2` `.vmodc` bytes**, not quoted from the ledger.

**Built values (decoded, `modules/default/batmobile/*.vmodc` at the `offset-in-file` of
`Working/Movement/out/*.xml`)**

| member | built |
|---|---:|
| `land_engine.torque_factor_at_optimal_rpm` | **1393.524536** |
| `land_engine.optimal_rpm` / `min_rpm` / `max_rpm` | **2800 / 800 / 4500** |
| `land_engine.torque_factor_at_min_rpm` / `_at_max_rpm` | **1.0 / 0.65** |
| `vehicle_misc.official_top_speed` | **336.399994** |
| `transmission.top_speed` / `final_drive` / upshift rpm | **437.32 / 5.140125 / 4200** |
| `land_aerodynamics.frontal_area` | **6.634667** |
| `land_aerodynamics.drag_coefficient` | **0.550000** |
| `land_aerodynamics.top_speed_drag_coefficient` | **2.0** |
| `land_aerodynamics.lift_coefficient` / `air_density` | −0.3 / 1.3 |
| `custom_land_global.arcade.nitro_boost` | torque ×**2.0**, grip **1.0**, push **15000**, blend **0.2 s**, extra **+43.2 km/h** |
| `custom_land_global.arcade.heat_boost` | torque ×**2.0**, grip **4.26**, push 0, blend **0**, extra **+100.92 km/h** |
| `custom_land_global.arcade.nitro_boost_upgraded` | torque ×**2.0**, grip **4.26**, push 20000, blend 0.2, extra **+100.92 km/h** |
| `arcade.turbo_jump` / `_upgraded` | punch 0.1 s / 50 kph / top 200 → 0.1 s / 80 kph / top 200, f 15/12 → 30/25 |

**Verdicts: 1 LORE-EXACT (T-A1), 5 COMPROMISE (T-E2, T-E5, T-B1, T-B4, T-A3).**

---

## First, the power the built engine actually makes

This is the arithmetic every row below depends on. [derived from the built torque, the built rpm
band and the two falloff factors.]

```
P(ω) = T_opt × f(rpm) × rpm × 2π/60
at optimal 2800 rpm, f = 1.00 : 1393.524536 × 293.215 = 408,590 W = 408.6 kW = 548 hp
at max     4500 rpm, f = 0.65 : 905.79 × 471.239      = 426,808 W = 426.8 kW = 572 hp
                                                 => built peak power 572 hp
lore target                     : 1200 bhp          = 894.8 kW
                                                       ratio 572/1200 = 0.477
donor sanity check (490 N·m @ 5000, 0.84 @ 7300): 411.6 × 764.49 = 314.7 kW = 422 hp  (matches MODLOG §95)
```

**The rpm edit (T-E1: 1000/5000/7300 → 800/2800/4500) halved the power without touching the
torque.** 490 N·m at 5000 rpm was 344 hp; the same shape at 2800 rpm with 1393.5 N·m is 548 hp —
the torque scale of ×2.844 buys the lore 1200 hp only at the *donor's* rpm band. At the edited
band it buys 47.7 % of it.

---

## T-E2 — absolute torque 1393.5 · **COMPROMISE**

**BmAK number.** None: BmAK's chain has **no absolute torque member** — the class stores only
neutral multipliers (`BatmobileMassRatio` 1.0, `MassScale` 1.0, `InertiaTensorMultiplier`
[1,1,1]) and a **torque-vs-speed curve**, not a scale (`CHAIN.json`, T-M1's own cell). So the
"BmAK number" here is the lore power, 1200 bhp, plus the donor curve (490 N·m @ 5000 rpm,
0.86/0.84 falloff → 422 hp).

**Built number** — `1393.524536` N·m.

**Arithmetic**

```
1393.524536 / 490      = 2.844          (the lore-power ratio 1200/422 = 2.8436, +0.01 %)
class fit median 1100  : 1393.5/1100 = 1.267   (+26.7 %, the ledger's "~+30 %")
class fit 4 t (834.1)  : 1393.5/834.1 = 1.671  (+67.1 %)
the ledger's 1,121     : 1393.5/1121  = 1.243   (+24.3 %)  -- FITS.md contains no 1,121
```

**Verdict: COMPROMISE — and the "+30 %" is not a fix for anything.**

* It is the **lore power ratio** applied to the donor torque, not a correction: 2.844 is
  1200/422 to two decimals. The row's own comparison base is stale (`FITS.md` holds 834.1 at 4 t
  and 1,100 for 6–15 t, no 1,121 — independently audited in `t_vnf_six.py`).
* It is **not** compensating for a mismatch: it predates both later edits (T-E1's rpm band and
  T-A2's Cd 0.55), and after those edits the same torque produces **572 hp, 47.7 % of lore**.
* The real mismatch it would have to fix is the lore acceleration, and it is ~6× too small:

```
lore 0-60 mph 2.7 s (lore_batmobile.json, "recorded, NOT applied")
a      = 26.82 / 2.7                    = 9.93 m/s^2
F      = m a = 6000 × 9.93              = 59,580 N
gear   = 3.15 (1st) × 5.140125          = 16.19
T_wheel= 59,580 × 0.683                 = 40,693 N·m
T_eng  = 40,693 / 16.19                 = 2,513 N·m   (×1.80 over 1393.5)
power route: 894.8 kW at 4500 rpm/0.65  = 2,921 N·m   (×2.10 over 1393.5)
```

So the number that would satisfy the lore acceleration or the lore power is **2.5–2.9 kN·m**,
not 1.4 kN·m — and both sit at or above the fleet's 95th percentile (2,500), i.e. at the edge of
what any shipped JC3 vehicle carries.

**One-line fix.** Re-derive T-E2 against the *edited* rpm band: either restore the optimum toward
5000 rpm (where 1393.5 N·m **is** 1200 hp) or raise torque to ~2,921 N·m and accept that the build
now sits at the fleet ceiling; the current pair quietly promises 1200 hp and delivers 572.

---

## T-E5 — top speed 336.4 km/h · **COMPROMISE**

**BmAK number.** None: no speed member exists in the BmAK chain (the same absence proof as T-A2).
The 336.4 comes from the wiki's 209 mph — **assumed**, signed off 2026-10-23 (ledger class
`assumed`).

**Built number** — `vehicle_misc.official_top_speed = 336.399994` (in the shipped domain 25…350).

**Arithmetic — the terminal-speed balance the ledger never did**

```
Cd·A       = 0.55 × 6.634667            = 3.649 m^2
v_max      = (2P / (rho Cd A))^(1/3), rho 1.3, P = 426.8 kW
           = (853,600 / 4.744)^(1/3)    = 56.5 m/s = 203 km/h
gap to 336.4 km/h (93.44 m/s):          133 km/h
Cd needed at A 6.635 and 426.8 kW:      0.121
power needed at Cd·A 3.649 for 93.44 m/s: 1,935 kW (2,595 hp)
```

So the built driveline + drag tops out at **203 km/h**: `official_top_speed 336.4` is a **label the
physics cannot reach**. QA-1's 138 km/h peak (at the older Cd 0.139) is consistent with a
driveline-limited car, not a drag-limited one.

**Verdict: COMPROMISE.** The value is a wiki number with no BmAK member behind it, and the build's
own aero makes it unreachable by 133 km/h.

**One-line fix.** Either treat `official_top_speed` as a display cap and record that the terminal
speed is 203 km/h (T-A2's Cd), or drop Cd to **0.121** so 336 km/h is physically attainable — the
two cannot both stand.

---

## T-B1 — boost torque multiplier 2.0 · **COMPROMISE**

**BmAK number** [decoded: `CLASS_DEFAULTS.md` l.265-267, `HUD/CLUSTER.md` `BoostDuration` 2.0;
ratios from `CHAIN.json`'s `BoostTorqueVSpeedCurve`, confirmed in `T1_TRANSLATION.md` **C34**]:

```
standard curve: 0 m/s -> 200 cm/s ; 2100 cm/s -> 105
boost curve   : 0 m/s -> 260      ; 2100 cm/s -> 220
ratio 260/200 = 1.30 ; 220/105 = 2.095   -> band 1.30 … 2.10
thrust: FakeExtaSpeedAccel 600 cu/s^2 = 6.00 m/s^2  (FakeExtraSpeedMax 3500 = 126 km/h)
cap:  BoostDuration 2.0 s  ->  min(3500, 600 × 2.0) = 1200 cu = 43.2 km/h
```

**Built numbers** — `nitro_boost.torque_multiplier = 2.0`, `extra_top_speed = 43.2`,
`grip_multiplier = 1.0`, `boost_blend_time = 0.2`.

**Arithmetic**

```
the flat member alone reproduces the band exactly:
  (v + 43.2)/v = 1.30  ->  v = 144.0 km/h
  (v + 43.2)/v = 2.10  ->  v =  39.3 km/h
mid-band of 1.30…2.10 = 1.70, not 2.0

the torque lever, measured against BmAK's 6 m/s^2 thrust:
  built low-speed a   = 6,777 N / 6000 kg = 1.13 m/s^2      (from QA-1's 16.4 s at 4000 kg, same force)
  x2.0 adds           = +1.13 m/s^2 = 18.8 % of BmAK's 6 m/s^2
  multiplier to match = 1 + 6.00/1.13     = 6.31
```

**Verdict: COMPROMISE.** Two separate problems:

1. **2.0 is not a mid-band fit.** The band's midpoint is 1.70, and the number is a ratio of
   *speeds* in BmAK, not of torques in JC3 — "matches at 50 % of the speed band" is a coincidence.
2. **It is far too weak to reproduce BmAK's thrust.** BmAK's afterburner adds 6 m/s²; ×2.0 on a
   1.13 m/s² car adds 1.13 m/s². The *speed* half (43.2 km/h) is faithful; the *thrust* half is
   not.
3. The one part that **is** faithful is the flat term: 43.2 km/h reproduces 1.30–2.10 exactly
   between 39 and 144 km/h.

**One-line fix.** Keep `extra_top_speed 43.2` and `boost_blend_time 0.2`, set the torque
multiplier from a measured low-speed boost take (target 6 m/s² ≈ ×6.3), or leave it at 1.0 and
stop claiming it carries BmAK's ratio.

---

## T-B4 — heat-boost and turbo-jump · **COMPROMISE (and the row's text is false in the bytes)**

**BmAK number.** **None** — chain-proven absence: no arcade heat-boost or turbo-jump member exists
(`HeatSteam*` is exhaust steam, `Jump*` is landing physics). The row's justification is the fleet's
donor column: `heat_boost` blend 0 / extra 80 / grip 1.5 / torque 2; `turbo_jump` punch 0.1 s /
50 km/h / top 200.

**Built numbers vs the row's claim**

| block | row says (donor) | built | difference |
|---|---:|---:|---|
| `heat_boost.extra_top_speed` | 80 | **100.92** | ×1.2615 (= 336.4/250 tier scaling, `lore_stats.py`) |
| `heat_boost.grip_multiplier` | 1.5 | **4.26** | ×2.844 (= the torque ratio: 1.5 × 2.8436) |
| `heat_boost.boost_blend_time` | 0 | 0 | = |
| `heat_boost.torque_multiplier` | 2 | 2.0 | = |
| `nitro_boost_upgraded.grip_multiplier` | 1.5 | **4.26** | ×2.844 |
| `nitro_boost_upgraded.extra_top_speed` | 80 | **100.92** | ×1.2615 |
| `turbo_jump` f/r, punch, top | 15/12, 0.1, 200 | 15/12, 0.1, 200 | = |
| `turbo_jump_upgraded` f/r | 30/25 | 30/25 | = |

**Verdict: COMPROMISE.** The absence claim is **true** (there is no BmAK carrier), but the "keep
the donor's defaults" claim is **not what shipped**: two inherited scalings survive in the bytes —
grip ×2.844 (the torque ratio, MODLOG §81's option (a) "scale grip with torque") and the boost
tier ×1.2615 (`lore_stats.py`). Neither is a BmAK number and neither is in the row.

**One-line fix.** Either restore 1.5 / 80 (what the row claims) or rewrite the cell to say
"grip 4.26 = 1.5 × the torque ratio, extra 100.92 = 80 × the tier scale" — the bytes and the
ledger must agree.

---

## T-A1 — frontal area 6.63 m² · **LORE-EXACT**

**BmAK number.** No area member; the geometric truth is the body cross-section from the mesh:
**3.495 × 2.271 = 7.937 m²** (`GRAB_BACKLOG` DIM-1, `stations.json` `body_bbox`).

**Built number** — `frontal_area = 6.634667`.

**Arithmetic**

```
6.634667 / 7.937            = 0.836   (83.6 % fill of the bounding cross-section)
JC3 heavy band (3-8 t)      = median 6.5, IQR 4 … 6.72  (T3_FLEET.md)
fleet fit at 4 t            = 4.924   (FITS.md, R^2 0.875)
```

A road car's reference area is 0.75–0.9 of its bounding cross-section, so 6.63 is the value the
lore geometry predicts, and it sits inside the heavy-class interquartile band (just above its
p75 of 6.72, below the 6 t+ median of 6.95).

**Verdict: LORE-EXACT** (geometry-consistent; no member to decode — class/inferred by nature).

**What it is not:** a drag-area proof. The behaviour depends on `Cd × A = 3.649 m²`, and that
product is twice what 336 km/h needs (see T-E5, T-A3).

---

## T-A3 — top-speed drag coefficient 2.0 · **COMPROMISE**

**BmAK number.** **None** — the chain has no drag member at all (T-A2's absence proof: grep
`Drag || Lift || Aero || Downforce || Area` returns only `SelfDriveUseTightArea` and
`UprightLiftStrength`).

**Built number** — `top_speed_drag_coefficient = 2.0`, kept because every sampled vehicle is 2.0.

**Arithmetic (both readings, because the semantics are undecoded)**

```
if it multiplies Cd at the top-speed end:
   Cd_eff·A = 2.0 × 0.55 × 6.635 = 7.30 m^2
   v_max = (853,600 / (1.3 × 7.30))^(1/3) = 44.8 m/s = 161 km/h
if it is inert (Cd alone applies):
   v_max = 203 km/h                                     (T-E5)
needed for 336.4 km/h with this power: Cd·A = 0.805 m^2
```

**Verdict: COMPROMISE.** There is no lore number to be faithful to, the member's consumer is
undecoded, and under the multiplying reading the build's ceiling drops to **161 km/h** — 175 km/h
short of T-E5. Keeping the fleet constant is the only evidence-backed choice, but the row cannot
claim it "carries" anything.

**One-line fix.** One probe build with `top_speed_drag_coefficient` 1.0 vs 2.0 and a top-speed
run; the ceiling moves, or the member is inert and the row is documented as such.

---

## The +30 % question, answered in one place

**No, the +30 % torque is not a fix for a mismatch elsewhere.** It is the lore **power ratio**
(1200 bhp / the donor's 422 hp = 2.844) applied to the donor's torque curve, computed at the
donor's rpm band. Three facts make it impossible to read as a correction:

1. the ratio is exact (2.844 vs 2.8436), and it was chosen before any of the edits it could have
   been compensating for;
2. after those edits it under-delivers: **572 hp at the built 2800/4500 rpm band, 47.7 % of 1200**;
3. the numbers that *would* satisfy the lore targets are 2.5 kN·m (acceleration) and 2.9 kN·m
   (power) — i.e. ×1.8 … ×2.1, not ×1.3.

What the edits actually did: T-E1's rpm drop **halved** the power at constant torque, and T-A2's
Cd 0.139 → 0.55 **cost 17 % of terminal speed** (at the old Cd the same power gives 267 km/h).
Neither is patched by the torque scale; both are still in the bytes.

---

## Closest system and the gap for the build (STAGES.md)

| gap | closest JC3 system | what the build must do |
|---|---|---|
| BmAK has **no torque scale** (curve only) | `land_engine.torque_factor_at_optimal_rpm` + min/opt/max factors | torque is a lore-power derivation, not a translation — keep it labelled `assumed/derived`, never `decoded` |
| BmAK has **no aero member** | `land_aerodynamics.{frontal_area, drag_coefficient, top_speed_drag_coefficient, lift_coefficient}` | Cd is the one free parameter; it must be solved **against T-E5's target**, not against the donor (0.121 for 336 km/h at A 6.635) |
| BmAK boost is **speed-additive** (6 m/s², 43.2 km/h), JC3's is torque × multiplier | `arcade.nitro_boost.{torque_multiplier, extra_top_speed, boost_blend_time, grip_multiplier}` | the flat term is the faithful one; the multiplier has to be derived from a measured take (≈ ×6.3 for 6 m/s²) or dropped to 1.0 |
| BmAK has **no heat boost / turbo jump** | `arcade.heat_boost.*`, `turbo_jump*` | not a translation at all; the bytes must at least equal the documented donor defaults |
| two unknowns block the terminal-speed model | — | the consumer of `top_speed_drag_coefficient` and whether `official_top_speed` is a cap or a physical limit |

**Stage placement.** All six rows concern the Q driving takes (A1, A2, A9); none blocks a build
stage, but T-E5, T-A3 and T-E2 cannot be called settled until a terminal-speed model exists — the
prediction table already marks A2 as UNKNOWN for exactly this reason.

---

## UNKNOWN

1. **What `top_speed_drag_coefficient` multiplies** — undecoded; the two readings differ by 42 km/h
   at the top end.
2. **Whether `official_top_speed` is a physical cap or a HUD label** — the Serpente's 250 vs its
   gearing's 333 suggests a label; not decoded.
3. **Where the 572 hp / 1200 hp discrepancy is felt in game** — no measurement exists at the
   edited rpm band; QA-1 was taken at 4000 kg and Cd 0.139.
4. **Whether the 1393.5 scale was ever meant to survive T-E1's rpm edit** — no file records the
   order of intent, only the edit order.
5. **The `grip_multiplier` 4.26 provenance** — 1.5 × 2.844 is the arithmetic, but no doc states
   that heat_boost's grip was included in MODLOG §81's "scale grip with torque" decision.

---

## Checks run

| # | check | result |
|---|---|---|
| 1 | decode of 5 built `.vmodc` modules at the XML offsets | values in the header table; `drag_coefficient` reads **0.55** where the source XML says 0.1393, i.e. the T-A2 edit is in the build |
| 2 | power/re terminal-speed arithmetic | 548–572 hp, 203 km/h, 161 km/h (2.0 reading) — printed in full above |
| 3 | ledger rows T-E2/T-E5/T-B1/T-B4/T-A1/T-A3 + T-A2/T-B2/T-B3/T-A4/E1/E3/E4/M1 read from `T_ROWS.jsonl` | all six `keep`; T-B4's donor-default claim contradicted by the bytes |
| 4 | `Working/Q/PREDICTIONS.md` | A2 absolute top speed UNKNOWN, D-2b boost delta 32.4–43.2 km/h |
| 5 | `FITS.md` torque fit | 834.1 at 4 t, 1,100 for 6–15 t, 2,500 at 15 t+; **no 1,121** |
| 6 | `T3_FLEET.md` aero band | 3–8 t: median 6.5, IQR 4 … 6.72 |

No game process started; static reads plus two read-only decodes.

## Reproduce

```bash
python - <<'EOF'
import xml.etree.ElementTree as ET, struct
MOD="Builds/bm-RC2/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/batmobile/"
for mod in ('land_engine','land_aerodynamics','vehicle_misc','custom_land_global'):
    b=open(MOD+'v0300_car_kensington_sportsmuscle_%s.vmodc'%mod,'rb').read()
    for m in ET.parse('Working/Movement/out/v0300_car_kensington_sportsmuscle_%s.xml'%mod).getroot().iter('member'):
        o=m.get('offset-in-file')
        if o and m.get('name') in ('torque_factor_at_optimal_rpm','optimal_rpm','max_rpm',
                                   'official_top_speed','frontal_area','drag_coefficient',
                                   'top_speed_drag_coefficient','torque_multiplier','extra_top_speed'):
            print(mod, m.get('name'), struct.unpack_from('<f',b,int(o,16))[0])
EOF
```

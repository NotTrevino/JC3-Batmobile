# DONE — turret yaw/pitch limits over the whole JC3 vehicle fleet

STATUS: done

A JC3 turret is a `Turret`-behaviour part (yaw) and a `Cannon`-behaviour part (pitch), each on one
`hkpLimitedHingeConstraintData` (G2-13, `Research/JC3Grab/TURRET.md`). This pass read the two limits of
**every** such pair in the fleet with G3-10e's atom decode — the angular limit atom at **+0x0F8** (u16 type
code **14**), min at **+0x0FC**, max at **+0x100**, radians (`jc3_physics_limits.HINGE_LIMIT`, imported, not
restated; the type code is re-read per hinge as an oracle).

Scope: all **233** vehicle entities in `PARTS_TABLE.jsonl`, each re-read from the game archives (233 with a
parts module, 220 with a `.physicsc`). **40** of them carry a `Turret` or `Cannon` part; those fold into
**11 distinct vehicle models** and **14 turret units** (7 `turret`, 3 `two_cannon`, 4 `pitch_only`). Every
variant of a model decodes identical numbers, asserted by an oracle.

## The numbers

| model | class | yaw part (min .. max, span) | pitch part (min .. max, span) |
|---|---|---|---|
| `mediumtank` | tank | `mediumtank_turret` −179 .. 179 (358) | `mediumtank_cannon` −5 .. 20 (25) |
| `bavariumtank` | tank | `bavariumtank_turret` −179 .. 179 (358) | `bavariumtank_cannon` −5 .. 20 (25) |
| `smalltank` | tank | `smalltank_turret` −179 .. 179 (358) | `smalltank_cannon` −5 .. 25 (30) |
| `apc` | apc | `apc_turret_base` −179 .. 179 (358) | `apc_weapon_mount_vertical` −15 .. 50 (65) |
| `armoredjeep` | armed land | `armoredjeep_turret_base` −179 .. 179 (358) | `armoredjeep_weapon_mount_vertical` −25 .. 50 (75) |
| `technicaljeep` | armed land | `technicaljeep_rebel_turret` −179 .. 179 (358) | `technicaljeep_weapon_mount_vertical` −10 .. 45 (55) |
| `corvette` | boat | `corvette_turret` −150 .. 150 (300) | `corvette_gun` −5 .. 75 (80) |
| `heavypatrol` ×2 | boat | `*_weapon_mount_{l,r}_horizontal` −75 .. 75 (150) | `*_weapon_mount_{l,r}_vertical` −50 .. 50 (100) |
| `lightpatrol` | boat | `lightpatrol_weapon_mount_horizontal` −75 .. 75 (150) | `lightpatrol_weapon_mount_vertical` −50 .. 25 (75) |
| `lightassault` ×2 | aircraft | **no yaw part** (mount parent `*_minigun_mount_*_base`, no hinge) | `*_minigun_mount_*_vertical` −45 .. 35 (80) |
| `advancedassault` ×2 | aircraft | **no yaw part** (mount parent is the body, no hinge) | `*_gatling_*_mount` −45 .. 30 (75) |

## The three questions

1. **Yaw and pitch limits of every turret** — the table above, per model; the `.md`/`.json` carry every part
   index, `constraint_index`, `.physicsc` object offset, axis and pivot.
2. **Which turrets have no yaw limit (full rotation)** — **none have a literally unlimited hinge.** Six model
   yaws ship the −179 .. +179 pair, i.e. **358 deg of travel**, which is all-round with a 2 deg blind wedge dead
   astern: medium tank, Bavarium tank, small tank, APC, armoured jeep, technical. The corvette is narrower
   (300 deg) and the two patrol boats narrower still (150 deg, two-Cannon pintles). The fleet's only
   full-rotation hinges are **not turrets**: 4 `hkpHingeConstraintData` objects (cast-net pivots on
   `mediumoldfishing`, a hose spool on `transport`) and 11 model hinges whose pair is exactly −180 .. +180
   (upper steering forks on `atv`, `combatdirt`, `duck`, `jetski`, `modernmoped`, `modernroad`, `modernsport`,
   `oldmoped`, `oldroad`, `snowmobile`, `trials`). Both mechanisms are therefore proven to exist in shipped
   files — a port could use one — but no vanilla turret does.
3. **How pitch ranges differ** — tanks are the flat shooters (−5 depression, +20/+25 elevation, span 25–30);
   the APC doubles that (−15 .. +50, span 65) and the armed jeeps more (−25 .. +50 and −10 .. +45); **boats
   trade yaw for pitch**: the corvette keeps a narrow-depression, high-elevation gun (−5 .. +75) on a 300 deg
   yaw, while the patrol boats use two-Cannon pintles with ±50 or −50 .. +25 pitch and only ±75 yaw; aircraft
   gun frames pitch −45 .. +35 / −45 .. +30 on plain adapters and have no yaw hinge at all. Every boat pitch
   span exceeds every tank pitch span (asserted as an oracle).

## Files written

| file | what |
|---|---|
| `Tools/scripts/jc3_turret_limits.py` | new pass, `--write` / `--check` (re-reads the archives and recomputes every number; 13 oracles) |
| `Research/JC3Grab/TURRET_LIMITS.md` | 236 lines: methodology, per-model tables, yaw/pitch sections, oracle table, UNKNOWNs |
| `Research/JC3Grab/TURRET_LIMITS.json` | the same machine-readable: every unit, hinge offset, axis, pivot, angle |
| `tmp/freebuff/scratch/probe_turrets.py`, `probe_limits.py`, `probe_classes.py`, `probe_unlimited.py` | throw-away probes (candidate discovery, limit spot-check, wiring, unlimited-hinge owners) |
| `tmp/freebuff/reports/JC3-turret-limits.md` | this report |

Nothing else was modified. Inputs read-only: the game install `D:/Games/Just Cause 3`, `PARTS_TABLE.jsonl`,
`WEAPON_WIRING.jsonl`, the imported `jc3_physics_limits` constants. No game process touched, no `Builds/` edit,
no network.

## Commands and their output

### 1. Fleet shape — which entities can carry a turret

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python -c "
import json,collections
cats=collections.Counter(); tur=collections.Counter(); can=collections.Counter()
n=0
for line in open('Research/JC3Grab/PARTS_TABLE.jsonl',encoding='utf-8'):
    r=json.loads(line); n+=1
    p=r['entity']; parts=p.split('/')
    cat='/'.join(parts[2:4]) if len(parts)>3 else '?'
    cats[cat]+=1
    bs={x.get('b') for x in r['parts']}
    if 'Turret' in bs: tur[cat]+=1
    if 'Cannon' in bs: can[cat]+=1
print(n, 'entities')
print('cats', dict(cats))
print('with Turret', dict(tur), sum(tur.values()))
print('with Cannon', dict(can), sum(can.values()))
"
233 entities
cats {'jc_vehicles/01_land': 156, 'jc_vehicles/02_air': 42, 'jc_vehicles/03_sea': 35}
with Turret {'jc_vehicles/01_land': 19, 'jc_vehicles/03_sea': 3} 22
with Cannon {'jc_vehicles/01_land': 19, 'jc_vehicles/02_air': 9, 'jc_vehicles/03_sea': 12} 40
```

### 2. Candidate scan — 40 entities, 11 models, hinge limits spot-checked (probe output, tail)

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python tmp/freebuff/scratch/probe_turrets.py 2>&1 | tail -70
index rows 81952
candidate entities 40
[1/40] v0200_car_capstone_apc_debug.ee                            parts= 45 phys=1 cons=16 [(30, 'apc_turret_base', 'Turret', 15, 0), (44, 'apc_weapon_mount_vertical', 'Cannon', 14, 30)] (0.2s)
...
[40/40] v1704_boat_na_lightpatrol_rebel_01.ee                     parts= 31 phys=1 cons=4 [(29, 'lightpatrol_weapon_mount_horizontal', 'Cannon', 3, 21), (30, 'lightpatrol_weapon_mount_vertical', 'Cannon', 2, 29)] (0.3s)
total 7.6s
```

(Full listing in the transcript of this session; every one of the 40 entities decodes to one of the 11 models.)

### 3. Limits per turret part (probe, de-duplicated by model)

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python tmp/freebuff/scratch/probe_limits.py 2>&1 | tail -80
== v0201_car_capstone_mediumtank_debug.ee parts 42 cons 3
   mediumtank_turret                              Turret  ci=2   parent=0   hkpLimitedHing -179.0..179.0 axis=[-0.0, 1.0, 0.0] pivot=[0.0, 2.2812, 1.1382] t14=14
   mediumtank_cannon                              Cannon  ci=0   parent=26  hkpLimitedHing -5.0..20.0 axis=[1.0, 0.0, 0.0] pivot=[0.0, 2.5347, 0.0] t14=14
== v1202_boat_capstone_corvette_debug.ee parts 58 cons 7
   corvette_turret                                Turret  ci=6   parent=0   hkpLimitedHing -150.0..150.0 axis=[-0.0, 1.0, 0.0] pivot=[0.0, 2.5787, -8.8316] t14=14
   corvette_gun                                   Cannon  ci=5   parent=24  hkpLimitedHing -5.0..75.0 axis=[1.0, -0.0, 0.0] pivot=[0.0212, 3.7889, -9.0548] t14=14
== v1200_boat_capstone_heavypatrol_debug.ee parts 70 cons 7
   heavypatrol_weapon_mount_l_horizontal          Cannon  ci=4   parent=45  hkpLimitedHing -75.0..75.0 axis=[-0.0, 1.0, 0.0] pivot=[-2.7544, 2.7423, -0.2488] t14=14
   heavypatrol_weapon_mount_l_vertical            Cannon  ci=3   parent=66  hkpLimitedHing -50.0..50.0 axis=[-0.0, 0.0, -1.0] pivot=[-2.7851, 2.9218, -0.2488] t14=14
== v1704_boat_na_lightpatrol_civic_police_01.ee parts 31 cons 4
   lightpatrol_weapon_mount_horizontal            Cannon  ci=3   parent=21  hkpLimitedHing -75.0..75.0 axis=[-0.0, 1.0, 0.0] pivot=[-0.0176, 1.4733, -3.0386] t14=14
   lightpatrol_weapon_mount_vertical              Cannon  ci=2   parent=29  hkpLimitedHing -50.0..25.0 axis=[1.0, 0.0, 0.0] pivot=[-0.0176, 1.6429, -3.0668] t14=14
```

### 4. Fleet-wide unlimited / full-360 hinge census and its owners

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python -c "
import glob,os,math,struct,sys
sys.path.insert(0,'Tools/scripts')
import jc3hkx
for path in sorted(glob.glob(r'E:/Modding/_shared/gamedata/JC3grab/**/*.physicsc',recursive=True)):
    pf=jc3hkx.Packfile(open(path,'rb').read())
    objs=sorted((o for o in pf.objects if 'Constraint' in o.cls),key=lambda o:o.offset)
    hits=[]
    for i,o in enumerate(objs):
        if o.cls=='hkpHingeConstraintData':
            hits.append((i,o.cls,o.offset))
        elif o.cls=='hkpLimitedHingeConstraintData':
            raw=pf.raw(o.offset,pf.extents[o.offset])
            lo,hi=struct.unpack_from('<2f',raw,0xFC)
            d=(round(math.degrees(lo),2),round(math.degrees(hi),2))
            if d[1]-d[0]>=359: hits.append((i,o.cls,d))
    if hits: print(os.path.basename(path), len(objs), hits)
"
atv.physicsc 6 [(5, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
combatdirt.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
mediumoldfishing.physicsc 38 [(34, 'hkpHingeConstraintData', 530352), (35, 'hkpHingeConstraintData', 530576), (36, 'hkpHingeConstraintData', 530800)]
modernmoped.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
modernroad.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
modernsport.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
oldmoped.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
oldroad.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
transport.physicsc 12 [(9, 'hkpHingeConstraintData', 153872)]
trials.physicsc 1 [(0, 'hkpLimitedHingeConstraintData', (-180.0, 180.0))]
```

Which part owns each — the same walk, resolving `constraint_index` to the owning part:

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python -c "
import glob,json,math,os,struct,sys
sys.path.insert(0,'Tools/scripts')
import jc3adf,jc3detail,jc3grab,jc3hkx,jc3index
OUT='Research/JC3Grab'; GAME=jc3index.DEFAULT_GAME
rows=jc3index.load_index(OUT)
tab={}
for line in open(os.path.join(OUT,'PARTS_TABLE.jsonl'),encoding='utf-8'):
    r=json.loads(line); tab[r['entity']]=r
def parts_of(ee):
    r=jc3detail.pick(rows,ee); blob=jc3grab.read_entry(r,GAME)
    stream,entries=jc3detail.inner_files(blob)
    hit=next((e for e in entries if e[0].endswith('_vehicle_parts.vmodc')),None)
    return jc3adf.parts(jc3adf.Adf(stream[hit[1]:hit[1]+hit[2]]))
for mod in ['atv','combatdirt','modernmoped','modernroad','modernsport','oldmoped','oldroad','trials','mediumoldfishing','transport']:
    ents=sorted(e for e in tab if tab[e]['module'].startswith(mod+'_'))
    if not ents: print('no entity',mod); continue
    ee=ents[0]; ps=parts_of(ee); by={p['part_index']:p for p in ps}
    pf=jc3hkx.Packfile(open('E:/Modding/_shared/gamedata/JC3grab/hkx/all/%s.physicsc'%mod,'rb').read())
    objs=sorted((o for o in pf.objects if 'Constraint' in o.cls),key=lambda o:o.offset)
    for i,o in enumerate(objs):
        cls=o.cls; d=None
        if cls=='hkpLimitedHingeConstraintData':
            raw=pf.raw(o.offset,pf.extents[o.offset]); lo,hi=struct.unpack_from('<2f',raw,0xFC)
            d=(round(math.degrees(lo),1),round(math.degrees(hi),1))
            if d[1]-d[0]<359: continue
        elif cls!='hkpHingeConstraintData': continue
        users=[(p['name'],p['behavior'],p.get('parent_part_index')) for p in ps if p.get('constraint_index')==i]
        print('%-18s %-28s %-24s %s %s'%(mod,ee.rsplit('/',1)[-1][:26],cls,d,users))
" 2>&1 | head -40
atv              v0012_car_autostraad_atv_c   hkpLimitedHingeConstraintData (-180.0, 180.0) [('atv_upper_steering', 'SteeringFork', 0)]
combatdirt       v3600_bike_urga_combatdirt   hkpLimitedHingeConstraintData (-180.0, 180.0) [('combatdirt_upper_steering', 'SteeringFork', 0)]
modernmoped      v3501_bike_solar_modernmop   hkpLimitedHingeConstraintData (-180.0, 180.0) [('modernmoped_upper_steering', 'SteeringFork', 0)]
modernroad       v3502_bike_solar_modernroa   hkpLimitedHingeConstraintData (-180.0, 180.0) [('modernroad_upper_steering', 'SteeringFork', 0)]
modernsport      v3401_bike_mugello_moderns   hkpLimitedHingeConstraintData (-180.0, 180.0) [('modernsport_upper_steering', 'SteeringFork', 0)]
oldmoped         v3500_bike_solar_oldmoped_   hkpLimitedHingeConstraintData (-180.0, 180.0) [('oldmoped_upper_steering', 'SteeringFork', 0)]
oldroad          v3503_bike_solar_oldroad_c   hkpLimitedHingeConstraintData (-180.0, 180.0) [('oldroad_upper_steering', 'SteeringFork', 0)]
trials           v3000_bike_autostraad_tria   hkpLimitedHingeConstraintData (-180.0, 180.0) [('trials_upper_steering', 'SteeringFork', 0)]
mediumoldfishing v1705_boat_na_mediumoldfis   hkpHingeConstraintData   None [('mediumoldfishing_cast_net_c', 'None', 39)]
mediumoldfishing v1705_boat_na_mediumoldfis   hkpHingeConstraintData   None [('mediumoldfishing_cast_net_l', 'None', 39)]
mediumoldfishing v1705_boat_na_mediumoldfis   hkpHingeConstraintData   None [('mediumoldfishing_cast_net_r', 'None', 39)]
transport        v1602_boat_urga_transport_   hkpHingeConstraintData   None [('transport_spool', 'None', 26)]
```

The local `hkx/all` cache misses `duck`, `jetski` and `snowmobile`, which is why the shipped script re-reads
all 233 entity bundles instead of the cache. The script's own census (`fleet_full_rotation_hinges`) is
**36 objects on 32 entities**, folding to **15 model hinges**: 4 unlimited (10 objects) and 11 at a full
360 deg span (26 objects), adding `duck`, `jetski` and `snowmobile` to the twelve above.

### 5. Axis cross-check (frame A row 0 vs frame B row 0), 5 models

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python -c "
import math,os,struct,sys
sys.path.insert(0,'Tools/scripts')
import jc3adf,jc3detail,jc3grab,jc3hkx,jc3index
OUT='Research/JC3Grab'; GAME=jc3index.DEFAULT_GAME
rows=jc3index.load_index(OUT)
def parts_of(ee):
    r=jc3detail.pick(rows,ee); blob=jc3grab.read_entry(r,GAME)
    stream,entries=jc3detail.inner_files(blob)
    hit=next((e for e in entries if e[0].endswith('_vehicle_parts.vmodc')),None)
    return jc3adf.parts(jc3adf.Adf(stream[hit[1]:hit[1]+hit[2]]))
def cons_of(ee):
    out=[]
    for name,blob in jc3hkx.physicsc_of(ee,rows,GAME):
        pf=jc3hkx.Packfile(blob)
        for o in sorted((o for o in pf.objects if 'Constraint' in o.cls),key=lambda o:o.offset):
            out.append((o.cls,pf.raw(o.offset,pf.extents[o.offset])))
    return out
for ee,tag in [('editor/entities/jc_vehicles/01_land/v0201_car_capstone_mediumtank/v0201_car_capstone_mediumtank_military_01.ee','mt'),
 ('editor/entities/jc_vehicles/03_sea/v1200_boat_capstone_heavypatrol/v1200_boat_capstone_heavypatrol_military_01.ee','hp'),
 ('editor/entities/jc_vehicles/02_air/v2602_helicopter_urga_lightassault/v2602_helicopter_urga_lightassault_military_01.ee','la'),
 ('editor/entities/jc_vehicles/02_air/v2604_helicopter_urga_advancedassault/v2604_helicopter_urga_advancedassault_military_01.ee','aa'),
 ('editor/entities/jc_vehicles/03_sea/v1704_boat_na_lightpatrol/v1704_boat_na_lightpatrol_military_01.ee','lp')]:
    ps=parts_of(ee); cons=cons_of(ee)
    print('==',tag)
    for p in ps:
        ci=p.get('constraint_index')
        if not isinstance(ci,int) or ci<0: continue
        cls,raw=cons[ci]
        if cls!='hkpLimitedHingeConstraintData': continue
        a=struct.unpack_from('<4f',raw,0x30); b=struct.unpack_from('<4f',raw,0x70)
        lo,hi=struct.unpack_from('<2f',raw,0xFC)
        dot=sum(a[k]*b[k] for k in range(3))
        print('  %-42s %-7s ci=%-2d parent=%-3s A=%s B=%s dot=%.4f lim=%s..%s'%(p['name'],p['behavior'],ci,p.get('parent_part_index'),[round(x,3) for x in a[:3]],[round(x,3) for x in b[:3]],dot,round(math.degrees(lo),1),round(math.degrees(hi),1)))
"
== mt
  mediumtank_turret                          Turret  ci=2  parent=0   A=[-0.0, 1.0, 0.0] B=[0.0, 1.0, 0.0] dot=1.0000 lim=-179.0..179.0
  mediumtank_cannon                          Cannon  ci=0  parent=26  A=[1.0, 0.0, 0.0] B=[1.0, 0.0, 0.0] dot=1.0000 lim=-5.0..20.0
== hp
  heavypatrol_weapon_mount_l_horizontal      Cannon  ci=4  parent=45  A=[-0.0, 1.0, 0.0] B=[0.0, 1.0, 0.0] dot=1.0000 lim=-75.0..75.0
  heavypatrol_weapon_mount_l_vertical        Cannon  ci=3  parent=66  A=[-0.0, 0.0, -1.0] B=[-0.0, 0.0, -1.0] dot=1.0000 lim=-50.0..50.0
== la
  lightassault_minigun_mount_l_vertical      Cannon  ci=6  parent=9   A=[1.0, -0.0, 0.0] B=[1.0, -0.0, 0.0] dot=1.0000 lim=-45.0..35.0
== aa
  advancedassault_gatling_l_mount            Cannon  ci=11 parent=0   A=[1.0, 0.0, 0.0] B=[1.0, 0.0, 0.0] dot=1.0000 lim=-45.0..30.0
== lp
  lightpatrol_weapon_mount_horizontal        Cannon  ci=3  parent=21  A=[-0.0, 1.0, 0.0] B=[0.0, 1.0, 0.0] dot=1.0000 lim=-75.0..75.0
  lightpatrol_weapon_mount_vertical          Cannon  ci=2  parent=29  A=[1.0, 0.0, 0.0] B=[1.0, 0.0, 0.0] dot=1.0000 lim=-50.0..25.0
```

### 6. The deliverables

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python Tools/scripts/jc3_turret_limits.py --write
TURRET_LIMITS.json: 14 units on 11 models, 10 yaw / 14 pitch hinges, 15 full-rotation hinges in the fleet
TURRET_LIMITS.md: 236 lines; oracles 13/13
```

```
cd E:/Modding/JustCause3/JC3-Batmobile && uv run python Tools/scripts/jc3_turret_limits.py --check
PASS: 233 entities, 14 turret units on 11 models, yaw spans [150.0, 300.0, 358.0], pitch spans [25.0, 30.0, 55.0, 65.0, 75.0, 80.0, 100.0]
oracles: {"TURRET_md_samples_reproduce": true, "boat_pitch_spans_exceed_tank_pitch_spans": true, "every_Turret_part_on_a_limited_hinge_type_14": true, "every_entity_scanned": true, "every_pitch_axis_is_horizontal": true, "every_yaw_axis_is_vertical": true, "frame_A_and_frame_B_share_the_axis": true, "full_rotation_hinges_are_variant_stable": true, "limits_ordered_and_within_pi": true, "no_turret_part_on_a_full_rotation_hinge": true, "turret_parts_identity_parent_offset": true, "turret_yaw_all_round_two_cannon_yaw_not": true, "variants_of_a_model_agree": true}
```

Exit status 0 for both. `--write` takes ~21 s (233 entity bundles, read-only).

## Oracles (all pass; `--check` re-runs them)

`every_Turret_part_on_a_limited_hinge_type_14`, `every_yaw_axis_is_vertical`,
`every_pitch_axis_is_horizontal`, `frame_A_and_frame_B_share_the_axis`,
`limits_ordered_and_within_pi`, `turret_parts_identity_parent_offset`, `TURRET_md_samples_reproduce` (the six
turreted vehicles G2-13 printed must come out at exactly its numbers), `variants_of_a_model_agree`,
`no_turret_part_on_a_full_rotation_hinge`, `full_rotation_hinges_are_variant_stable`,
`boat_pitch_spans_exceed_tank_pitch_spans`, `turret_yaw_all_round_two_cannon_yaw_not`, `every_entity_scanned`.

## UNKNOWNs

1. **The hinge axis frame** (body-A local vs vehicle space). Tried: compared pivots/axes with the art — the
   medium tank's turret pivot (0, 2.2812, 1.1382) and +Y axis agree with vehicle space, but the patrol boats'
   pitch hinge reads ±Z inside a yawing parent's frame (`heavypatrol_weapon_mount_*_vertical`). Still unknown:
   no byte names the frame; only the parent part's rest orientation settles it, and that matrix is in the
   `.lod`, not decoded here. Consequence: the angles are exact, the *direction* of elevation/depression rests
   on the sign convention G2-13 already used (−5 = depression on the tank), which the APC and jeeps' wider
   negative ranges corroborate.
2. **Rotation speed / acceleration.** Tried: read all of the limited hinge's atoms (type 14 carries only the
   pair) and the parts module (no such field). Still unknown: code-side (unchanged from G3-10e).
3. **Which part of a two-Cannon pintle is "the turret" in game logic.** Tried: the fire point names the
   horizontal part as yaw and the vertical as pitch, and the vertical's parent is the horizontal. Still
   unknown: both carry behaviour `Cannon`; no decoded ordinal.
4. **A full-rotation turret in vanilla.** Tried: censused every hinge in 233 entities — the two mechanisms
   (unlimited class, ±180 pair) exist but on nets/spools/steering forks only. Still unknown whether the
   turret logic would accept one; that is a build experiment, not a decode.
5. **Entities without constraints.** 13 of 233 ship no constraint object at all (220 have a `.physicsc`); none
   of them carries a `Turret`/`Cannon` part, so the turret census is unaffected.

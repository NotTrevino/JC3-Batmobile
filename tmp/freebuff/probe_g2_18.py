"""Independent re-derivation for G2-18: does NOT import jc3interact."""
import json, re, sys
import numpy as np
sys.path.insert(0, 'Tools/scripts')
import rbm_geom

P = ('v0300_car_kensington_sportsmuscle',
     'v0300_car_kensington_sportsmuscle_civilian_01')
ent = json.load(open(f'E:/Modding/JustCause3/_grab/entities/{P[0]}__{P[1]}.ee.json', encoding='utf-8'))
det = json.load(open(f'E:/Modding/JustCause3/_grab/detail/{P[0]}__{P[1]}.ee.json', encoding='utf-8'))

# 1. stunt areas straight from the module rows
sa = [m for m in ent['modules'] if m.get('type') == 'StuntAreas'][0]
g = {r['path']: r['value'] for r in sa['rows']}
slots = len({m.group(1) for m in (re.match(r'stunt_areas\[(\d+)\]', k) for k in g) if m})
active = sum(1 for i in range(slots) if g.get(f'stunt_areas[{i}].active'))
welds = len([1 for i in range(64) if f'welding_info[{i}].stunt_area_a_index' in g])
real = len([1 for i in range(welds)
            if g[f'welding_info[{i}].stunt_area_a_index'] >= 0
            and g[f'welding_info[{i}].stunt_area_b_index'] >= 0])
print('slots', slots, 'active', active, 'declared', g.get('number_of_stunt_areas'),
      'weld rows', welds, 'real', real)

# 2. .epe objects counted from the XML text, not through the script
xml = open('Research/Epe/serpente_civilian.xml', encoding='utf-8-sig').read()
names = re.findall(r'<value name="name" type="string">((?:entry|exit|point|transition|trigger|interaction)\.[^<]*)</value>', xml)
print('xml objects', len(names), 'distinct', len(set(names)),
      {p: sum(1 for n in names if n.split('.')[0] == p)
       for p in ('entry', 'exit', 'point', 'transition', 'trigger', 'interaction')})

# 3. mesh + one distance by brute force over vertices and a dense barycentric sample
v, t, _ = rbm_geom.collect_mesh(rbm_geom.decode(open('Working/TrueScale/body_lod1.rbm', 'rb').read()))
v = np.array(v); t = np.array(t)
print('mesh', len(v), 'v', len(t), 't', 'bbox', v.min(0).round(3), v.max(0).round(3))

dp_mod = [m for m in ent['modules'] if m.get('type') == 'DeformPoints'][0]
pts = {}
for r in dp_mod['rows']:
    mm = re.match(r'points\[(\d+)\]\.start_transform\[(\d+)\]$', r['path'])
    if mm:
        pts.setdefault(int(mm.group(1)), {})[int(mm.group(2))] = r['value']
P3 = np.array([[pts[i][12], pts[i][13], pts[i][14]] for i in sorted(pts)])
serr = np.vstack([P3.min(0), P3.max(0)])
st = json.load(open('Working/TrueScale/stations.json', encoding='utf-8'))
bat = np.array(st['body_bbox'], float)
print('deform', len(P3), 'serpente bbox', serr.round(4).tolist(), 'bat body', bat.round(4).tolist())

def to_bat(p):
    return bat[0] + (p - serr[0]) / (serr[1] - serr[0]) * (bat[1] - bat[0])

# area 2 centre, mapped, brute-force barycentric sample distance
cen = np.array([g[f'stunt_areas[2].center_local[{k}]'] for k in range(3)], float)
q = to_bat(cen)
tri = v[t]
uu, vv = np.meshgrid(np.linspace(0, 1, 41), np.linspace(0, 1, 41))
m = uu + vv <= 1
uu, vv = uu[m], vv[m]
best = 1e9
for chunk in np.array_split(np.arange(len(tri)), 64):
    A = tri[chunk][:, 0][:, None, :]
    AB = (tri[chunk][:, 1] - tri[chunk][:, 0])[:, None, :]
    AC = (tri[chunk][:, 2] - tri[chunk][:, 0])[:, None, :]
    S = A + AB * uu[None, :, None] + AC * vv[None, :, None]
    d = np.linalg.norm(S - q, axis=2).min()
    best = min(best, d)
print('main_area centre mapped', q.round(4).tolist(), 'sampled surface distance', round(best, 4),
      '(exact 41x41 sampling >= true distance)')
near = np.linalg.norm(v - q, axis=1).min()
print('nearest vertex distance', round(near, 4))

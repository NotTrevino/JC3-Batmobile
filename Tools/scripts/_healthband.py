"""Compare the decoded VehicleDamage/PartDamageType tables of several .vmodc files.

Usage: python _healthband.py <file.xml> [<file.xml> ...] [--baseline <n>]

Prints, per file, the VehicleDamage header and the 24 PartDamageType rows, in a
form that can be diffed by eye. Files are decoded separately with
Gibbed ConvertAdf (see _members.py for the one-file dumper).
"""
import re
import sys

args = [a for a in sys.argv[1:] if not a.startswith('--')]
base = 0
if '--baseline' in sys.argv:
    base = int(sys.argv[sys.argv.index('--baseline') + 1])

HEAD = ['max_health', 'bullet_armor', 'bullet_armor_strength', 'bullet_heavy_armor',
        'bullet_heavy_armor_strength', 'explosion_armor', 'explosion_armor_strength',
        'impact_armor', 'impact_armor_strength', 'fire_armor', 'fire_armor_strength',
        'melee_armor', 'melee_armor_strength', 'electricity_armor',
        'electricity_armor_strength', 'grapple_pull_armor', 'grapple_pull_armor_strength',
        'impact_damage_factor', 'deform_scale', 'smoke_threshold', 'burn_threshold',
        'explosion_delay_s', 'burn_duration_s', 'vulnerable_duration_s',
        'explosion_threshold', 'npc_explosion_threshold', 'vulnerable_explosion_threshold',
        'impact_deform_threshold', 'weapon_deform_threshold']

MEM = re.compile(r'<member name="([^"]+)"(?:[^>]*?offset-in-file="([0-9A-Fa-f]+)")?[^>]*?'
                 r'type="([A-Za-z_0-9\[\]]+)">([^<]*)</member>')

data = []
for path in args:
    x = open(path, encoding='utf-8-sig').read()
    body = x[x.find('<instances'):]
    hdr, rows, cur = {}, [], None
    for m in MEM.finditer(body):
        nm, off, ty, val = m.group(1), m.group(2), m.group(3), m.group(4).strip()
        if ty == 'string':
            # starts a new PartDamageType row: the string is the row's `type` name
            cur = {'name': val, 'off': off}
            rows.append(cur)
        elif ty == 'uint32' and cur is not None and 'hash' not in cur:
            cur['hash'] = val
        elif nm in ('initial_health', 'damaged_health', 'loosen_health',
                    'instantly_damaged_by_bullets', 'instantly_loosened_by_bullets',
                    'instantly_broken_by_bullets', 'damages_owning_vehicle') and cur is not None:
            cur[nm] = val
        elif nm in HEAD:
            hdr[nm] = val
    data.append((path.split('\\')[-1], hdr, rows))

print('### VehicleDamage header')
for nm in HEAD:
    vals = [d[1].get(nm, '-') for d in data]
    mark = '' if len(set(vals)) == 1 else '   <-- DIFFERS'
    print('%-32s %s%s' % (nm, ' | '.join('%-10s' % v for v in vals), mark))
print('\nfiles: ' + ' | '.join(d[0] for d in data))

print('\n### PartDamageType rows   (initial/damaged/loosen  idb ilb ibb dov)')
n = max(len(d[2]) for d in data)
for i in range(n):
    names = [d[2][i]['name'] if i < len(d[2]) else '-' for d in data]
    if len(set(names)) != 1:
        print('!! row %d name mismatch: %s' % (i, names))
    cells = []
    for d in data:
        r = d[2][i] if i < len(d[2]) else {}
        cells.append('%s/%s/%s %s%s%s%s' % (r.get('initial_health', '-'), r.get('damaged_health', '-'),
                                            r.get('loosen_health', '-'),
                                            r.get('instantly_damaged_by_bullets', '-'),
                                            r.get('instantly_loosened_by_bullets', '-'),
                                            r.get('instantly_broken_by_bullets', '-'),
                                            r.get('damages_owning_vehicle', '-')))
    mark = '' if len(set(cells)) == 1 else '   <-- DIFFERS'
    print('%-22s %s%s' % (names[0], ' | '.join('%-16s' % c for c in cells), mark))

import json, glob, collections, os, re

ps = glob.glob('E:/Modding/JustCause3/_grab/entities/*.ee.json')
paths = collections.Counter()
vals = []
ea_paths = collections.Counter()
nmod = 0
ea_nmod = 0
for p in ps:
    d = json.load(open(p, encoding='utf-8'))
    base = os.path.basename(p)
    for m in d['modules']:
        t = m.get('type')
        if t == 'ExtendedEffectUsages':
            nmod += 1
            for r in m['rows']:
                paths[r['path'].split('[')[0]] += 1
                if 'string' in r['path'] and r['value']:
                    vals.append((base, r['path'], r['value']))
        elif t == 'EffectAttachments':
            ea_nmod += 1
            for r in m['rows']:
                if r['path'].startswith('usage_effects'):
                    key = re.sub(r'\[\d+\]', '[]', r['path'])
                    ea_paths[key] += 1
print('ExtendedEffectUsages modules:', nmod)
print('row path prefixes:', paths.most_common(40))
print('EEU non-empty strings:', len(vals))
for v in vals[:25]:
    print('   ', v)
print('EffectAttachments modules:', ea_nmod)
print('EA usage row paths:', ea_paths.most_common(20))

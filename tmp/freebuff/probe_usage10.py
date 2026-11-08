import json, glob, re, collections

hits = collections.Counter()
types = collections.Counter()
for p in glob.glob('E:/Modding/JustCause3/_grab/entities/*.ee.json'):
    d = json.load(open(p, encoding='utf-8'))
    for m in d.get('modules', []):
        for r in m.get('rows', []):
            if 'usage' in r['path'].lower():
                key = (m.get('type'), re.sub(r'\[\d+\]', '[]', r['path']))
                hits[key] += 1
                types[m.get('type')] += 1
for k, c in hits.most_common(40):
    print(k, c)
print('module types with usage rows:', dict(types))

# also check detail .epe object property keys containing 'usage'
pk = collections.Counter()
n = 0
for p in glob.glob('E:/Modding/JustCause3/_grab/detail/*.ee.json')[:60]:
    d = json.load(open(p, encoding='utf-8'))
    epe = d.get('epe') or {}
    for o in (epe.get('objects') or []):
        n += 1
        for k in list(o.keys()) + list((o.get('values') or {}).keys() if isinstance(o.get('values'), dict) else []):
            if 'usage' in str(k).lower():
                pk[k] += 1
print('epe objects scanned', n, 'usage keys:', pk.most_common(20))

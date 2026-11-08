import json, glob, collections, re, os

hits = collections.Counter()
paths = []
for p in glob.glob('E:/Modding/_JC3grab/entities/*.ee.json'):
    d = json.load(open(p, encoding='utf-8'))
    for m in d['modules']:
        for r in m.get('rows', []):
            v = r.get('value')
            if isinstance(v, str) and '.effc' in v:
                key = (m.get('type'), re.sub(r'\[\d+\]', '[]', r['path']))
                hits[key] += 1
                if '/exhaust/' in v:
                    paths.append((os.path.basename(p)[:50], m.get('type'), r['path'], v))
print('module/type + row path carrying .effc:')
for k, c in hits.most_common(30):
    print('  ', k, c)
print('exhaust .effc rows:', len(paths))
for x in paths[:40]:
    print('  ', x)

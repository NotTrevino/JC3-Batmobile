import json, glob, collections

by_class = collections.Counter()
vals = collections.Counter()
samples = []
for p in glob.glob('E:/Modding/JustCause3/_grab/detail/*.ee.json'):
    d = json.load(open(p, encoding='utf-8'))
    epe = d.get('epe') or {}
    for o in (epe.get('objects') or []):
        keys = o.keys()
        v = None
        if 'Usage' in keys:
            v = o['Usage']
        elif isinstance(o.get('values'), dict) and 'Usage' in o['values']:
            v = o['values']['Usage']
        if v is None:
            continue
        cls = o.get('cls') or o.get('class')
        by_class[cls] += 1
        vals[str(v)] += 1
        if len(samples) < 15:
            samples.append({k: o.get(k) for k in list(o)[:8]} | {'Usage': v})
print('classes with Usage:', by_class.most_common(20))
print('distinct Usage values:', len(vals))
for k, c in vals.most_common(40):
    print('   ', repr(k), c)
for s in samples:
    print(s)

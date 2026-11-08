import json, glob, collections, os

cnt = collections.Counter()
by_ent = {}
for p in glob.glob('E:/Modding/JustCause3/_grab/entities/*.ee.json'):
    d = json.load(open(p, encoding='utf-8'))
    base = os.path.basename(p).split('__')[0]
    ex = [f['path'] for f in d['files'] if isinstance(f, dict) and '/exhaust/' in f.get('path', '')]
    if ex:
        by_ent.setdefault(base, set()).update(os.path.basename(x) for x in ex)
for k in sorted(by_ent):
    print(k, sorted(by_ent[k]))
print('entities with exhaust files:', len(by_ent))

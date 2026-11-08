import json, glob, collections, os, re

ps = glob.glob('E:/Modding/_JC3grab/entities/*.ee.json')

idx_rows = 0
usage_to_effects = collections.defaultdict(collections.Counter)  # usage -> effect idx -> count?
usage_entity = collections.defaultdict(set)
example = None
for p in sorted(ps):
    d = json.load(open(p, encoding='utf-8'))
    base = os.path.basename(p)
    for m in d['modules']:
        if m.get('type') != 'EffectAttachments':
            continue
        ea = collections.defaultdict(dict)
        ua = collections.defaultdict(dict)
        for r in m['rows']:
            mm = re.match(r'all_effects\[(\d+)\]\.(.*)$', r['path'])
            if mm:
                ea[int(mm.group(1))][mm.group(2)] = r['value']
                continue
            mm = re.match(r'usage_effects\[(\d+)\]\.(\S.*)$', r['path'])
            if mm:
                ua[int(mm.group(1))][mm.group(2)] = r['value']
                if mm.group(2).startswith('effect_indices['):
                    idx_rows += 1
                    if example is None:
                        example = (base, r['path'], r['value'])
        for i, u in ua.items():
            name = u.get('usage.string', '')
            usage_entity[name].add(base)
            for k, v in u.items():
                if k.startswith('effect_indices['):
                    usage_to_effects[name][int(k.split('[')[1].rstrip(']'))] = v

print('effect_indices element rows:', idx_rows, 'example:', example)
for name, ents in sorted(usage_entity.items(), key=lambda x: -len(x[1])):
    print(repr(name), 'entities:', len(ents), 'rows:', sum(usage_to_effects[name].values()))
print()
# show EngineNitro detail: which effects does it point at
for p in sorted(ps):
    d = json.load(open(p, encoding='utf-8'))
    base = os.path.basename(p)
    for m in d['modules']:
        if m.get('type') != 'EffectAttachments':
            continue
        ea = collections.defaultdict(dict)
        ua = collections.defaultdict(dict)
        for r in m['rows']:
            mm = re.match(r'all_effects\[(\d+)\]\.(.*)$', r['path'])
            if mm:
                ea[int(mm.group(1))][mm.group(2)] = r['value']
                continue
            mm = re.match(r'usage_effects\[(\d+)\]\.(\S.*)$', r['path'])
            if mm:
                ua[int(mm.group(1))][mm.group(2)] = r['value']
        for i, u in ua.items():
            if u.get('usage.string') in ('EngineNitro', 'EngineTurboJump'):
                print('---', base, u.get('usage.string'), json.dumps(u))
                print('   all_effects sample:', json.dumps({str(k): v for k, v in sorted(ea.items())[:6]}))

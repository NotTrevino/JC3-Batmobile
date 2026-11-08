import json, glob, collections, os, re

ps = glob.glob('E:/Modding/_JC3grab/entities/*.ee.json')

usage_rows = []   # (entity, module_file, usage string, hash, effect_indices)
effect_rows = collections.defaultdict(dict)  # effect index -> rows? per module
module_files = collections.Counter()
shown = 0
all_effect_names = collections.Counter()
usage_names = collections.Counter()

for p in sorted(ps):
    d = json.load(open(p, encoding='utf-8'))
    base = os.path.basename(p)
    for m in d['modules']:
        if m.get('type') != 'EffectAttachments':
            continue
        module_files[m.get('file')] += 1
        # gather element rows
        ea = collections.defaultdict(dict)   # idx -> {member: value}
        ua = collections.defaultdict(dict)
        for r in m['rows']:
            mm = re.match(r'all_effects\[(\d+)\]\.(.*)$', r['path'])
            if mm:
                ea[int(mm.group(1))][mm.group(2)] = r['value']
                continue
            mm = re.match(r'usage_effects\[(\d+)\]\.(.*)$', r['path'])
            if mm:
                ua[int(mm.group(1))][mm.group(2)] = r['value']
        for i, u in sorted(ua.items()):
            usage_rows.append((base, m.get('file'), i, u))
            usage_names[u.get('usage.string', '')] += 1
        for i, e in sorted(ea.items()):
            nm = e.get('effect.string', '')
            if nm:
                all_effect_names[nm] += 1
        if ua and shown < 1:
            shown += 1
            print('=== sample', base, m.get('file'))
            print('usage_effects:', json.dumps({str(k): v for k, v in ua.items()}, indent=1))
            print('all_effects count:', len(ea), 'indices sample:', sorted(ea)[:15])
            print('effect names:', collections.Counter(e.get('effect.string') for e in ea.values()).most_common(10))

print('usage names:', usage_names.most_common())
print('distinct effect names:', len(all_effect_names))
print(all_effect_names.most_common(30))
print('module files top:', module_files.most_common(10), 'distinct', len(module_files))

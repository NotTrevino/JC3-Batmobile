import json, glob, collections, zlib, struct

# 1. which hash function? known pairs
known = {'EngineNitro': 4197885156, 'EngineRunning': 2819629913,
         'HeadLights': 3551535361, 'GearChange': 768006784,
         'burn_engine': 3824625250, 'effect_trail': 1376299179}
for s, h in known.items():
    c = zlib.crc32(s.encode()) & 0xFFFFFFFF
    print('crc32', s, c, c == h, 'signed', struct.unpack('<i', struct.pack('<I', c))[0])

# 2. objects whose Usage equals a known usage-name hash
targets = {4197885156: 'EngineNitro', 2819629913: 'EngineRunning',
           3877802965: 'EngineTurboJump', 3551535361: 'HeadLights'}
hits = collections.defaultdict(list)
allusage = collections.Counter()
for p in glob.glob('E:/Modding/JustCause3/_grab/detail/*.ee.json'):
    d = json.load(open(p, encoding='utf-8'))
    ent = d.get('entity', '')
    epe = d.get('epe') or {}
    for o in (epe.get('objects') or []):
        v = o.get('Usage')
        if v is None and isinstance(o.get('values'), dict):
            v = o['values'].get('Usage')
        if v is None:
            continue
        iv = int(v) & 0xFFFFFFFF
        allusage[iv] += 1
        if iv in targets:
            hits[targets[iv]].append((ent.split('/')[-1], o.get('class'), o.get('name')))
print('distinct usage values (uint32):', len(allusage))
for k, v in hits.items():
    print('---', k, len(v))
    for x in v[:20]:
        print('   ', x)
    ents = sorted(set(x[0] for x in v))
    print('   entities:', len(ents), ents[:12])

import os, sys, json, glob
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'Tools', 'scripts'))
sys.path.insert(0, 'E:/Modding/JC3-Batmobile/Tools/scripts')
import jc3adf, jc3detail, jc3grab, jc3index

GAME = jc3index.DEFAULT_GAME
rows = []
with open('E:/Modding/JC3-Batmobile/Research/JC3Grab/INDEX.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            rows.append(json.loads(line))

ee = 'editor/entities/jc_vehicles/01_land/v3000_bike_autostraad_trials/v3000_bike_autostraad_trials_civilian_01.ee'
r = jc3detail.pick(rows, ee)
blob = jc3grab.read_entry(r, GAME)
stream, entries = jc3detail.inner_files(blob)
hits = [e for e in entries if 'effect_attachments' in e[0] or 'extended_effect_usages' in e[0]]
print(hits)
for name, off, size in hits:
    data = stream[off:off + size]
    adf = jc3adf.Adf(data)
    print('---', name, 'size', size)
    try:
        doc = list(jc3adf.walk(adf))
        ua = [r for r in doc if 'usage' in str(r[0])]
        print('usage rows:', len(ua))
        for r in ua:
            print('   ', r)
    except Exception as e:
        print('walk failed:', e)
        # dump type info
        print('type names:', [t for t in dir(adf) if not t.startswith('_')][:40])

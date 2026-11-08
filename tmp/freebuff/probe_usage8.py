import os, sys, json
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
for name, off, size in entries:
    if name.endswith('car_cycle_base_nitrous.effc') or name.endswith('car_cycle_base.effc'):
        adf = jc3adf.Adf(stream[off:off + size])
        print('===', name, size)
        doc = list(jc3adf.walk(adf))
        print('rows', len(doc))
        # strings anywhere
        strs = [x for x in doc if isinstance(x[2], str) and x[2]]
        for x in strs[:60]:
            print('   ', x)
        # root object names
        for a in dir(adf):
            if not a.startswith('_'):
                pass
        try:
            print('header names:', adf.strings[:20] if hasattr(adf, 'strings') else 'n/a')
        except Exception as e:
            print('no strings attr:', e)

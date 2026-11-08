import os, sys, json
sys.path.insert(0, 'E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts')
import jc3adf, jc3detail, jc3grab, jc3index

GAME = jc3index.DEFAULT_GAME
rows = []
with open('E:/Modding/JustCause3/JC3-Batmobile/Research/JC3Grab/INDEX.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            rows.append(json.loads(line))

ee = 'editor/entities/jc_vehicles/01_land/v3000_bike_autostraad_trials/v3000_bike_autostraad_trials_civilian_01.ee'
r = jc3detail.pick(rows, ee)
blob = jc3grab.read_entry(r, GAME)
stream, entries = jc3detail.inner_files(blob)
for name, off, size in entries:
    if 'physics_effects' in name or 'usage' in name.lower():
        adf = jc3adf.Adf(stream[off:off + size])
        print('===', name, size)
        for row in jc3adf.walk(adf):
            print('   ', row)

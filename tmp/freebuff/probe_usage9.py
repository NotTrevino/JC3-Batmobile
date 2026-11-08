import os, sys, json, time, glob
sys.path.insert(0, 'E:/Modding/JC3-Batmobile/Tools/scripts')
import jc3detail, jc3grab, jc3index

GAME = jc3index.DEFAULT_GAME
rows = []
with open('E:/Modding/JC3-Batmobile/Research/JC3Grab/INDEX.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            rows.append(json.loads(line))

ees = [json.load(open(p, encoding='utf-8'))['entity'] for p in
       sorted(glob.glob('E:/Modding/_JC3grab/entities/*.ee.json'))[:10]]
t0 = time.time()
nbytes = 0
for ee in ees:
    r = jc3detail.pick(rows, ee)
    blob = jc3grab.read_entry(r, GAME)
    nbytes += len(blob)
t1 = time.time()
print('10 reads:', round(t1 - t0, 2), 's, bytes', nbytes)

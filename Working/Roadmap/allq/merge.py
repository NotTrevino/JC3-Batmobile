"""Merge the 8 landmark staging manifests into tmp/freebuff/queue with numbers, AFTER deps, similarity and cycle checks.
Usage: python merge.py [--write]   (default dry run)"""
import json, os, re, sys
from pathlib import Path

S = Path(__file__).parent
PROJ = Path('E:/Modding/JC3-Batmobile')
FB = PROJ / 'tmp' / 'freebuff'
REP = 'E:/Modding/JC3-Batmobile/tmp/freebuff/reports'
FULL = 'E:/Modding/JC3-Batmobile/tmp/freebuff/APPROVED_Q_FULL.txt'
TAIL = 'Shared rules: E:/Modding/JC3-Batmobile/tmp/freebuff/INSTRUCTIONS.md.'
ORDER = ['integration', 'appearance', 'weapons', 'handling', 'sound', 'modes_controls_anim', 'hud_cam_lights_fx', 'damage_world']
LM_OF = {'appearance': 'L2', 'weapons': 'L4', 'handling': 'L3', 'sound': 'L5', 'modes_controls_anim': 'L8',
         'hud_cam_lights_fx': 'L7', 'damage_world': 'L6', 'integration': 'L1'}
WRITE = '--write' in sys.argv

index = json.loads((S / 'brief_index.json').read_text(encoding='utf-8'))
by_num = {}
for b in index:
    by_num.setdefault(b['num'], b)
existing_done = {b['done'] for b in index if b['done']}


def tri(text):
    w = re.findall(r'[a-z0-9]+', text.lower().replace(TAIL.lower(), ''))
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


def overlap(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


# existing bodies for the similarity check (queued + held + recent done)
exist_bodies = []
for d in ('queue', 'queue/held'):
    for f in (FB / d).glob('*.txt'):
        t = f.read_text(encoding='utf-8', errors='ignore')
        exist_bodies.append((f.name, tri(re.sub(r'^(DONE|ONLY|EST|BRIEF|AFTER|NEEDS):.*\n', '', t, flags=re.M))))

briefs, errors, warn = [], [], []
for name in ORDER:
    p = S / 'staging' / (name + '.json')
    if not p.exists():
        errors.append('missing staging file ' + p.name)
        continue
    try:
        man = json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        errors.append('%s does not parse: %s' % (p.name, e))
        continue
    for b in man.get('briefs', []):
        b['_lm'] = name
        briefs.append(b)

keys = {}
for b in briefs:
    if b['key'] in keys:
        errors.append('duplicate key ' + b['key'])
    keys[b['key']] = b

# numbering 9200..9999 in landmark order
num = 9200
for b in briefs:
    if num > 9999:
        errors.append('ran out of numbers at ' + b['key'])
        break
    b['_num'] = str(num)
    slug = re.sub(r'[^a-z0-9-]+', '-', b.get('slug', b['key']).lower()).strip('-')[:60] or b['key']
    b['_file'] = '%s-%s.txt' % (b['_num'], slug)
    done = '%s/%s.md' % (REP, slug)
    if done in existing_done:
        done = '%s/%s-%s.md' % (REP, slug, b['_num'])
    existing_done.add(done)
    b['_done'] = done
    num += 1

# resolve deps
for b in briefs:
    after = []
    for d in b.get('deps', []):
        d = str(d).strip()
        if d == 'APPROVED_Q':
            after.append(FULL)
        elif d in keys:
            after.append(keys[d]['_done'])
        elif re.fullmatch(r'\d{4}', d) and d in by_num and by_num[d]['done']:
            after.append(by_num[d]['done'])
        else:
            warn.append('%s: unknown dep %r dropped' % (b['key'], d))
    if b.get('ingame') and FULL not in after:
        after.append(FULL)
    b['_after'] = list(dict.fromkeys(after))

# cycle check among new keys
graph = {b['key']: [d for d in b.get('deps', []) if d in keys] for b in briefs}
state = {}


def visit(k, stack):
    if state.get(k) == 1:
        errors.append('cycle: ' + ' -> '.join(stack + [k]))
        return
    if state.get(k) == 2:
        return
    state[k] = 1
    for d in graph.get(k, []):
        visit(d, stack + [k])
    state[k] = 2


for k in graph:
    visit(k, [])

# similarity
tris = {b['key']: tri(b['body']) for b in briefs}
too_similar = []
ks = list(tris)
for i, a in enumerate(ks):
    for bk in ks[i + 1:]:
        o = overlap(tris[a], tris[bk])
        if o >= 0.5:
            too_similar.append((a, bk, round(o, 2)))
    for fname, t in exist_bodies:
        o = overlap(tris[a], t)
        if o >= 0.5:
            too_similar.append((a, fname, round(o, 2)))
bad_keys = {a for a, _, _ in too_similar}
for b in briefs:
    if not b.get('body') or len(b['body'].split()) < 40:
        errors.append('%s: body too short' % b['key'])

print('briefs %d | in-game %d | errors %d | warnings %d | too similar %d' % (
    len(briefs), sum(bool(b.get('ingame')) for b in briefs), len(errors), len(warn), len(too_similar)))
for e in errors[:40]:
    print('ERROR', e)
for w in warn[:60]:
    print('WARN', w)
for s in too_similar[:40]:
    print('SIMILAR', s)
from collections import Counter
print(Counter(b['_lm'] for b in briefs))

if WRITE and not errors:
    written = 0
    for b in briefs:
        if b['key'] in bad_keys:
            continue
        body = b['body'].strip()
        if not body.endswith(TAIL):
            body += ' ' + TAIL
        head = ['DONE: ' + b['_done'], 'ONLY: freebuff', 'EST: %d' % int(b.get('est', 30)), 'BRIEF: hand-written 2026-11-08']
        if b['_after']:
            head.append('AFTER: ' + ', '.join(b['_after']))
        (FB / 'queue' / b['_file']).write_text('\n'.join(head) + '\n' + body + '\n', encoding='utf-8')
        written += 1
    # register in landmarks.json
    lmp = PROJ / 'Working' / 'Roadmap' / 'landmarks.json'
    lm = json.loads(lmp.read_text(encoding='utf-8'))
    byid = {L['id']: L for L in lm['landmarks']}
    for b in briefs:
        if b['key'] in bad_keys:
            continue
        L = byid.get(b.get('landmark_override') or LM_OF[b['_lm']])
        field = 'q_briefs' if b.get('ingame') else 'briefs'
        if L and b['_num'] not in L[field]:
            L[field].append(b['_num'])
    lmp.write_text(json.dumps(lm, indent=1), encoding='utf-8')
    (S / 'merge_result.json').write_text(json.dumps([{k: b.get(k) for k in ('key', '_num', '_file', '_done', '_after', 'ingame', 'covers')} for b in briefs], indent=1))
    print('WROTE %d briefs; skipped %d too-similar (rewrite them)' % (written, len(bad_keys)))
elif WRITE:
    print('NOT WRITTEN: fix errors first')

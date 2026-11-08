"""Bounded last attempt on patch_win64/game4 016DE9D1 (read-only probe)."""
import json, os, struct, sys, collections, re
sys.path.insert(0, 'Tools/scripts')
from rbmhdr import hash_jenkins
GAME = r'D:/Games/Just Cause 3'
TARGET = 0x016DE9D1
rows = [json.loads(l) for l in open('Research/JC3Grab/INDEX.jsonl', encoding='utf-8') if l.strip()]
by_hash = {int(r['hash'], 16): r for r in rows}
HANDLES = {}

def payload(arc_key, o, s):
    if arc_key not in HANDLES:
        p = os.path.join(GAME, (arc_key + '.arc').replace('/', os.sep))
        HANDLES[arc_key] = open(p, 'rb')
    f = HANDLES[arc_key]; f.seek(o); return f.read(s)

def read_tab(arc_key):
    b = open(os.path.join(GAME, (arc_key + '.tab').replace('/', os.sep)), 'rb').read()
    out = {}; o = 12
    while o + 12 <= len(b):
        nh, off, sz = struct.unpack_from('<III', b, o); out[nh] = (off, sz); o += 12
    return out

FREQ = [4000, 8000, 11000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000]
def fsb(buf):
    f5 = buf.find(b'FSB5')
    if f5 < 0 or len(buf) < f5 + 60: return None
    ver, n, shdr, ntl = struct.unpack_from('<IIII', buf, f5 + 4)
    tok = None
    if ntl >= 4 and len(buf) >= f5 + 60 + n * shdr + 4:
        nt = f5 + 60 + n * shdr
        (o0,) = struct.unpack_from('<I', buf, nt)
        s = buf[nt + o0:nt + ntl].split(b'\x00')[0]
        try: tok = s.decode('ascii')
        except Exception: pass
    v = struct.unpack_from('<Q', buf, f5 + 60)[0] if n else 0
    fi = v & 0xF; ch = ((v >> 5) & 1) + 1; samples = v >> 34
    return dict(tok=tok, n=n, shdr=shdr, ntl=ntl, freq=FREQ[fi] if fi < len(FREQ) else None,
                ch=ch, samples=samples,
                dur=round(samples / float(FREQ[fi]), 3) if fi < len(FREQ) and FREQ[fi] else None)

# ---------------- 1. neighbours
ARC = 'patch_win64/game4'
tab = read_tab(ARC)
off, size = tab[TARGET]
ents = sorted(tab.items(), key=lambda kv: kv[1][0])
i = [n for n, (k, v) in enumerate(ents) if v[0] == off][0]
print("== 1. physical neighbours, %s (tab records %d) ==" % (ARC, len(tab)))
for k, (o, s) in ents[max(0, i - 4):i + 5]:
    buf = payload(ARC, o, s); f = fsb(buf); r = by_hash.get(k)
    fmt = ("%sHz/%dch/%.3fs" % (f['freq'], f['ch'], f['dur'])) if f else (
          "TAB" if buf[:4] == b'TAB\x00' else "?%s" % buf[:4].hex())
    print("  %10d %7d %08X tok=%-11s %-18s %s" % (o, s, k, (f or {}).get('tok'), fmt,
          (r['path'] if r else '<UNNAMED 016DE9D1>')))

# ---------------- 2. token census over every named .wavc
print("\n== 2. token census over named .wavc ==")
tok2paths = collections.defaultdict(list)
scanned = 0
for r in rows:
    if not r['path'].lower().endswith('.wavc'): continue
    try: buf = payload(r['archive'], r['offset'], min(r['size'], 4096))
    except Exception: continue
    f = fsb(buf); scanned += 1
    if f and f['tok']: tok2paths[f['tok']].append(r['path'])
print("  scanned %d .wavc, distinct tokens %d" % (scanned, len(tok2paths)))
print("  token 1606523576 in named set:", tok2paths.get('1606523576', 'NO'))
dup = sum(1 for t, p in tok2paths.items() if len(p) > 1)
print("  tokens shared by >1 named file:", dup, " (language copies)")

# ---------------- 3. mm320 census and cross-language token invariance
print("\n== 3. mission_mm320 census ==")
mm = [r for r in rows if 'mission_mm320' in r['path']]
bylang = collections.defaultdict(set)
for r in mm:
    m = re.match(r'sound/dialogue/([^/]+)/(.+)$', r['path'])
    if m: bylang[m.group(1)].add(m.group(2))
print("  paths %d, language dirs %d" % (len(mm), len(bylang)))
for lang in sorted(bylang):
    if lang in ('ara', 'eng'):
        print("  %s (%d):" % (lang, len(bylang[lang])))
        for b in sorted(bylang[lang]): print("     ", b)
agree = disagree = 0; examples = []
tokof = {}
for r in mm:
    m = re.match(r'sound/dialogue/([^/]+)/(.+)$', r['path'])
    if not m: continue
    f = fsb(payload(r['archive'], r['offset'], min(r['size'], 4096)))
    if f and f['tok']: tokof[(m.group(2), m.group(1))] = f['tok']
names = collections.defaultdict(dict)
for (b, l), t in tokof.items(): names[b][l] = t
for b, d in names.items():
    if len(d) >= 2:
        tset = set(d.values())
        if len(tset) == 1: agree += 1
        else:
            disagree += 1
            if len(examples) < 4: examples.append((b, d))
print("  basenames with >=2 language copies: token-agree %d, token-disagree %d" % (agree, disagree))
for b, d in examples: print("    DISAGREE", b, d)

# ---------------- 4. hash-space search
print("\n== 4. candidate hash space ==")
langs = sorted({m.group(1) for r in rows for m in [re.match(r'sound/dialogue/([^/]+)/', r['path'])] if m})
brk = None
r_prev, r_next = by_hash.get(ents[i - 1][0]), by_hash.get(ents[i + 1][0])
for rr in (r_prev, r_next):
    if rr:
        m = re.match(r'(sound/dialogue/[^/]+/)', rr['path']); brk = m.group(1) if m else None
print("  bracket dir:", brk, "| langs", len(langs))
nums = [str(n) for n in range(0, 10000)] + [str(n).zfill(w) for w in (2, 3, 4) for n in range(0, 1000)]
letters = [n + c for n in (str(x).zfill(3) for x in range(0, 1000)) for c in 'abcdefghijklmnopqrstuvwxyz']
starts = ['start' + str(n) for n in range(0, 21)] + ['start0%d' % n for n in range(0, 10)] + \
         ['start05', 'start050', 'start_05', 'start5', 'startA']
words = ['a', 'b', 'c', 'start', 'startup', 'intro', 'outro', 'end', 'loop']
suffixes = list(dict.fromkeys(nums + letters + starts + words))
print("  suffix space per prefix: %d" % len(suffixes))
found = []; tried = 0
def trypath(p):
    global tried
    tried += 1
    try:
        if hash_jenkins(p) == TARGET: found.append(p)
    except Exception:
        pass
prefixes_bracket = [brk] if brk else []
for pre in prefixes_bracket:
    for s in suffixes: trypath(pre + 'mission_mm320_dial_gameplay_' + s + '.wavc')
for lang in langs:
    pre = 'sound/dialogue/%s/' % lang
    for s in nums: trypath(pre + 'mission_mm320_dial_gameplay_' + s + '.wavc')
# path-shape variants of the most likely candidate
for pre in (brk or 'sound/dialogue/ara/'):
    for base in ('mission_mm320_dial_gameplay_090.wavc', 'mission_mm320_dial_gameplay_091.wavc'):
        for p in (pre + base, '/' + pre + base, pre.upper() + base,
                  pre + base.replace('/', chr(92)), 'patch_win64/' + pre + base):
            trypath(p)
print("  tried %d candidate paths, hits %d" % (tried, len(found)))
for p in found: print("   HIT", p)

# ---------------- 5. stringlookup / .fl mentions of mm320 take names
print("\n== 5. in-archive name sources mentioning mm320 ==")
seen = 0
for r in rows:
    if not r['path'].lower().endswith(('.stringlookup', '.fl')): continue
    try: buf = payload(r['archive'], r['offset'], min(r['size'], 400000))
    except Exception: continue
    if b'mm320' not in buf: continue
    seen += 1
    toks = sorted({s.decode('ascii', 'ignore') for s in re.findall(rb'[ -~]{6,}', buf)
                   if b'mm320' in s})
    print("  %s -> %s" % (r['path'], toks[:6]))
print("  files naming mm320:", seen)

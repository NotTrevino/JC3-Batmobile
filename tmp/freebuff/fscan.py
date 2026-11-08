import sys, os, json, glob, re, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "Tools/scripts")
import bmak_ramp_sweep as s

PAT = re.compile(r"(ramp|lacquered|colourlut|colorlut)", re.I)
files = sorted(glob.glob(os.path.join(s.CK, "*.upk")))

def one(p):
    try:
        size = os.path.getsize(p)
        with open(p, "rb") as f:
            raw = f.read(min(size, 4 << 20))
        names = s._parse(raw)
        return os.path.basename(p), names, None
    except s._Short:
        try:
            names = s.upk_read.Package(p).names
            return os.path.basename(p), names, "full-read"
        except Exception as e:
            return os.path.basename(p), None, "%s: %s" % (type(e).__name__, e)
    except Exception as e:
        return os.path.basename(p), None, "%s: %s" % (type(e).__name__, e)

t0 = time.time(); res = []
with ThreadPoolExecutor(max_workers=8) as ex:
    for i, r in enumerate(ex.map(one, files)):
        res.append(r)
        if i % 300 == 0:
            print("  %d/%d %.0fs" % (i, len(files), time.time() - t0), flush=True)

rows, bad = {}, []
for base, names, err in res:
    if not names:
        bad.append([base, err]); continue
    hits = sorted({n for n in names if PAT.search(n)})
    if hits:
        rows[base] = {"names": hits, "exact": [x for x in s.EXACT if x in names]}
print("read %d/%d unreadable %d naming-ramp %d in %.0fs" % (len(files)-len(bad), len(files), len(bad), len(rows), time.time()-t0), flush=True)
print("unreadable:", bad[:10], flush=True)
json.dump({"package_count": len(files), "scanned": len(files)-len(bad), "unreadable": bad, "packages": rows},
          open("Working/Ramp/ramp_scan.json", "w"), indent=1)
print("WROTE Working/Ramp/ramp_scan.json", flush=True)

import sys, os, json, glob, re, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "Tools/scripts")
import bmak_ramp_sweep as s

files = sorted(glob.glob(os.path.join(s.CK, "*.upk")))
print("packages on disk:", len(files), flush=True)
t0 = time.time()
res = []
with ThreadPoolExecutor(max_workers=12) as ex:
    for i, r in enumerate(ex.map(s._one, files)):
        res.append(r)
        if i % 400 == 0:
            print("  %d/%d  %.0fs" % (i, len(files), time.time()-t0), flush=True)

rows, bad, n = {}, [], 0
for base, got, err in res:
    if err:
        bad.append([base, err]); continue
    n += 1
    names, hits = got
    if hits:
        rows[base] = {"names": hits, "exact_referenced": [x for x in s.EXACT if x in names]}
print("read %d of %d, unreadable %d, naming a ramp %d" % (n, len(files), len(bad), len(rows)), flush=True)
print("unreadable:", bad[:5], flush=True)
json.dump({"package_count": len(files), "scanned": n, "unreadable": bad, "packages": rows},
          open("Working/Ramp/ramp_scan.json", "w"), indent=1)
for b, r in sorted(rows.items()):
    print("%-46s refs=%s" % (b, ",".join(r["exact_referenced"]) or "-"), flush=True)
    for nm in r["names"]:
        print("      ", nm, flush=True)
print("WROTE Working/Ramp/ramp_scan.json", flush=True)

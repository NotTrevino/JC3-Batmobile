import sys, os, json, glob, re
sys.path.insert(0, "Tools/scripts")
import bmak_ramp_sweep as s

class _Serial:
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def map(self, f, it, chunksize=None):
        out = []
        for i, x in enumerate(it):
            out.append(f(x))
            if i % 250 == 0:
                print("  ...%d/%d" % (i, len(it)), flush=True)
        return out

s.mp.Pool = lambda *a, **k: _Serial()
npkgs, bad = s.validate()
print("validate: %d sampled, %d mismatches" % (npkgs, len(bad)), flush=True)
for b in bad[:6]: print("  MISMATCH", b, flush=True)
got = s.scan()
print("upks on disk %d | name tables read %d | unreadable %d | naming a ramp %d"
      % (got["package_count"], got["scanned"], len(got["unreadable"]), len(got["packages"])), flush=True)
json.dump(got, open("Working/Ramp/ramp_scan.json", "w"), indent=1)
print("WROTE Working/Ramp/ramp_scan.json", flush=True)

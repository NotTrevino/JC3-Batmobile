import sys, os, json, glob, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, "Tools/scripts")
import upk_read

NAMES = ["Batman_BM3_V2_Lacquered_Underlayer_Ramp", "Batman_BM3_V2_Leather_Ramp",
         "Batmobile_V3_Body_ColourRamp", "Batmobile_V3_Tyre_ColourRamp",
         "Aniso_ramp_Lacquered", "Aniso_ramp_D2"]
files = sorted(glob.glob(os.path.join(r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole", "*.upk")))
out = open("Working/Ramp/ramp_hits.jsonl", "w", encoding="utf-8")
log = open("Working/Ramp/ramp_scan_progress.txt", "w", encoding="utf-8")

def one(p):
    pkg = upk_read.Package(p)
    rows = []
    for n in NAMES:
        i = pkg.find(n)
        if not i:
            continue
        if i > 0:
            rows.append({"name": n, "kind": "export", "index": i,
                         "class": pkg.object_class(i), "size": pkg.exports[i - 1]["size"]})
        else:
            imp = pkg.imports[-i - 1]
            rows.append({"name": n, "kind": "import", "index": i,
                         "class": imp["class_name"], "outer": pkg.object_path(imp["outer"])})
    return os.path.basename(p), rows

t0 = time.time(); done = 0; bad = []
with ThreadPoolExecutor(max_workers=6) as ex:
    futs = {ex.submit(one, p): p for p in files}
    for f in as_completed(futs):
        p = futs[f]; done += 1
        try:
            base, rows = f.result()
        except Exception as e:
            bad.append((os.path.basename(p), "%s: %s" % (type(e).__name__, e)))
            continue
        if rows:
            out.write(json.dumps({"package": base, "rows": rows}) + "\n"); out.flush()
            print("HIT", base, rows, flush=True)
        if done % 200 == 0:
            msg = "%d/%d %.0fs bad=%d" % (done, len(files), time.time() - t0, len(bad))
            print(msg, flush=True); log.write(msg + "\n"); log.flush()
log.write("DONE %d/%d %.0fs unreadable=%d\n" % (done, len(files), time.time() - t0, len(bad)))
log.write(json.dumps(bad[:20]) + "\n"); log.flush()
print("FINISHED", done, "of", len(files), "bad", len(bad), flush=True)

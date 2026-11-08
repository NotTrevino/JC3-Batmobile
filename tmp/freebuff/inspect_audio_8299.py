"""One-off: print the shapes B-11-rc4 has to consume, bounded output."""
import json
import os
import shutil

ROOT = r"E:/Modding/JC3-Batmobile"


def p(*a):
    return os.path.join(ROOT, *a)


def show(name, obj, depth=0, maxlist=6):
    pad = "  " * depth
    if isinstance(obj, dict):
        keys = list(obj)
        print(f"{pad}{name}: dict[{len(keys)}] {keys[:maxlist]}")
        for k in keys[:maxlist]:
            show(k, obj[k], depth + 1, maxlist)
    elif isinstance(obj, list):
        print(f"{pad}{name}: list[{len(obj)}]")
        if obj:
            show("[0]", obj[0], depth + 1, maxlist)
    else:
        s = str(obj)
        print(f"{pad}{name}: {type(obj).__name__} {s[:100]}")


print("=== manifest")
m = json.load(open(p("Working/Audio/bm_bank_manifest.json"), encoding="utf-8"))
print("top keys:", list(m))
print("summary:", json.dumps(m["summary"], indent=0)[:600])
print("written:", [(w["bank"], w["bytes"], w["samples"], w["sha256"][:12]) for w in m["written"]])
print("banks:", {k: {kk: vv for kk, vv in v.items() if kk != "bytes"} for k, v in m["bank"].items()})
print("slots:", len(m["slots"]))
for s in m["slots"]:
    print(" slot", s["bank"], s["index"], s["name"], s["row"], "frames", s["frames"], "ch", s["channels"],
          "guid", (s.get("guid") or "")[:8], "map_lufs", s.get("map_lufs"),
          "meas", {k: s["measured"].get(k) for k in ("delivered_lufs", "padded_frames", "trimmed_frames", "src_frames", "gain_db_loopfill")})
print("fmod_guids:", {k: v for k, v in m["fmod_guids"].items() if k != "guids"})
print("installer files:", m["installer"]["files"])

print("\n=== manifest v2 delta")
m2 = json.load(open(p("Working/Audio/bm_bank_manifest_v2.json"), encoding="utf-8"))
print("same top keys:", list(m2) == list(m))
for a, b in zip(m["slots"], m2["slots"]):
    if a != b:
        print(" changed", a["bank"], a["index"], a["name"])
        for k in set(a) | set(b):
            if a.get(k) != b.get(k):
                print("   ", k, "->", str(a.get(k))[:80], "||", str(b.get(k))[:80])
print("written v2:", [(w["bank"], w["sha256"][:12]) for w in m2["written"]])

print("\n=== t12 audio map")
mp = json.load(open(p("Working/Translation/t12_audio_map.json"), encoding="utf-8"))
print("keys:", list(mp))
print("rows:", len(mp["rows"]))
for r in mp["rows"]:
    print(" row", r["id"], r.get("feature"), r.get("dispo"), "guid", (r.get("guid") or "")[:8],
          "slots", [(s["bank"], s["index_1based"], s["name"], s.get("chosen")) for s in r.get("slots", [])])
print("method:", str(mp.get("method"))[:400])

print("\n=== event roles")
er = json.load(open(p("Working/Audio/jc3_event_roles.json"), encoding="utf-8"))
show("jc3_event_roles", er, maxlist=4)

print("\n=== AUDIO_BANKS evidence")
for f in ("Research/BatmobileGrab/AUDIO_BANKS.json", "Research/BatmobileGrab/AUDIO_BANKS.md"):
    fp = p(f)
    print(f, os.path.exists(fp), os.path.getsize(fp) if os.path.exists(fp) else "")
if os.path.exists(p("Research/BatmobileGrab/AUDIO_BANKS.json")):
    ab = json.load(open(p("Research/BatmobileGrab/AUDIO_BANKS.json"), encoding="utf-8"))
    show("AUDIO_BANKS", ab, maxlist=5)

print("\n=== builds")
for d in ("Builds/bm-004", "Builds/bm-004c", "Builds/bm-RC4-base", "Builds/bm-RC1"):
    fp = p(d)
    if os.path.exists(fp):
        print(d, sorted(os.listdir(fp))[:12])
        for sub in ("banks", "drop/sound/fmod_banks", "verify"):
            sp = os.path.join(fp, sub)
            if os.path.exists(sp):
                print("  ", sub, [(f, os.path.getsize(os.path.join(sp, f))) for f in sorted(os.listdir(sp))[:8]])
print("RF4-audio exists:", os.path.exists(p("Builds/bm-RC4-audio")))
free = shutil.disk_usage("E:/")
print("disk E: free %.1f GB of %.1f GB" % (free.free / 1e9, free.total / 1e9))

print("\n=== v04 gate doc")
for f in ("Builds/bm-RC1/verify/audio.json", "Builds/bm-004c/verify/audio_004c.json"):
    fp = p(f)
    if os.path.exists(fp):
        d = json.load(open(fp, encoding="utf-8"))
        print(f, "gates:", d.get("gates"), "verdict:", d.get("verdict"))
        for r in d.get("rows", []):
            print("  ", r["slot"], r["name"][:40], "lufs", r["loudness"]["lufs_built"], "van",
                  r["loudness"]["lufs_vanilla"], "d", r["loudness"]["delta_lu"],
                  "seam", (r.get("loop") or {}).get("seam_dbfs"),
                  "click", (r.get("loop") or {}).get("click"))

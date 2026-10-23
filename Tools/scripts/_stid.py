"""STID section parser: ID->name map inside bank packages. Grep vehicle names."""
import os, re, struct, sys

def stid_names(d, base=0):
    out = {}
    i = d.find(b"STID", base)
    while i >= 0:
        (sz,) = struct.unpack_from("<I", d, i + 4)
        body = d[i + 8:i + 8 + sz]
        if len(body) < 8:
            break
        # layout try: u32 unk, u32 count, entries: u32 id + u8/u16 len + name
        (a, n) = struct.unpack_from("<II", body, 0)
        o = 8
        names = {}
        ok = True
        for _ in range(min(n, 100000)):
            if o + 5 > len(body):
                ok = False; break
            (iid,) = struct.unpack_from("<I", body, o); o += 4
            ln = body[o]; o += 1
            if o + ln > len(body):
                # try u16 len
                o -= 1
                (ln,) = struct.unpack_from("<H", body, o); o += 2
                if o + ln > len(body):
                    ok = False; break
            try:
                nm = body[o:o+ln].decode()
            except Exception:
                ok = False; break
            o += ln
            names[iid] = nm
        if ok and names:
            # verify: names look sane?
            samp = list(names.values())[:5]
            if all(re.fullmatch(r"[A-Za-z0-9_]+", s) for s in samp):
                out.update(names)
        i = d.find(b"STID", i + 1)
    return out

ck = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
targets = sys.argv[1:] or ["CityX_08.upk"]
for t in targets:
    p = os.path.join(ck, t)
    d = open(p, "rb").read()
    names = stid_names(d)
    print("== %s (%d MB): %d STID names" % (t, len(d) >> 20, len(names)))
    veh = {i: n for i, n in names.items() if any(w in n.lower() for w in
           ["batmobile", "vehicle", "car", "engine", "exhaust", "boost", "afterburn",
            "turbine", "tire", "tyre", "skid", "throttle", "rpm", "chase"])}
    print("   vehicle-ish:", len(veh))
    for i, n in sorted(veh.items(), key=lambda kv: kv[1])[:80]:
        print("   %08X %s" % (i, n))

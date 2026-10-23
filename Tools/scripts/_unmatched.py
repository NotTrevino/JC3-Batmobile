"""Unmatched-event forensics: action types/targets + media profile -> functional labels."""
import json, os, struct, wave

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
d = open(os.path.join(A, "bank_BML_Engine.bank"), "rb").read()
hi = d.find(b"HIRC"); o = hi + 8
(n,) = struct.unpack_from("<I", d, o); o += 4
objs = {}
for _ in range(n):
    t = d[o]; (sz,) = struct.unpack_from("<I", d, o + 1); body = d[o+5:o+5+sz]
    oid, = struct.unpack_from("<I", body, 0)
    objs.setdefault(t, {})[oid] = body; o += 5 + sz
S = set(objs.get(2, {})); C = set()
for t in (5, 6, 7, 9): C.update(objs.get(t, {}))
SC = S | C

depth1 = {}
for row in json.load(open(os.path.join(A, "bml", "engine_depth1.json"))):
    for ev in row["events"]:
        depth1.setdefault(ev, []).append(row["info"]["tag"])

UN = {0x2099606B, 0x2479106C, 0x388CE6FC, 0x3C3F43C0, 0x9AF38C66, 0xA88826DB, 0xBD2FEE58}
for eid in sorted(UN):
    body = objs[4][eid]
    (cnt,) = struct.unpack_from("<I", body, 4)
    acts = [struct.unpack_from("<I", body, 8 + 4*k)[0] for k in range(cnt)]
    print("== event %08X (%d actions)" % (eid, cnt))
    for aid in acts:
        ab = objs[3].get(aid)
        if ab is None:
            print("   action %08X MISSING from bank" % aid); continue
        atype = ab[4]
        tgt = struct.unpack_from("<I", ab, 6)[0] if len(ab) >= 10 else None
        ttype = {k: t for t in objs for k in objs[t]}.get(tgt, "?")
        print("   action %08X atype=%d -> %08X (hirc-type %s)" % (aid, atype, tgt, ttype))
    tags = depth1.get("(unmatched-%08X)" % eid, [])
    print("   depth1 media (%d): %s" % (len(tags), tags))
    for tag in tags[:8]:
        p = os.path.join(A, "bml", tag + ".wav")
        if os.path.exists(p):
            w = wave.open(p, "rb")
            print("     %-16s %dch %.1fs" % (tag, w.getnchannels(), w.getnframes() / w.getframerate()))
            w.close()

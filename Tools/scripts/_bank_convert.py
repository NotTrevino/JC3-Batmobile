"""Clean converter: package -> AkBank exports -> event/media resolve -> wav.
Usage: python _bank_convert.py <package.upk> [comma,sepsubstr,...]
Default wants: BML_Battlemode bank + Play_Batmobile_Turbo/Play_BattlemodeEngine events.
Writes Working/Audio/conv/<pkg>/{banks,media}. No QuickBMS/vgmstream-python needed
(vgmstream-cli.exe must sit in Tools/vgmstream-win64/).
Codecs: zlib + LZO1X (pure-Python _lzo1x, no installs).
"""
import json, os, struct, subprocess, sys, zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _lzo1x import lzo1x_decompress  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
A = r"E:\Modding\JC3-Batmobile\Working\Audio"
CLI = os.path.join(r"E:\Modding\JC3-Batmobile\Tools", "vgmstream-win64", "vgmstream-cli.exe")
TAG = b"\xc1\x83\x2a\x9e"

def fnv1(s):
    h = 0x811C9DC5
    for b in s.encode():
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h

def dechunk(d, start):
    out = []
    i = d.find(TAG, start)
    while i >= 0 and i + 24 <= len(d):
        x, tc, tu = struct.unpack_from("<III", d, i + 4)
        if x != 0x20000:
            i = d.find(TAG, i + 4); continue
        q = i + 16
        pairs, su = [], 0
        while su < tu:
            if q + 8 > len(d) or len(pairs) > 512: break
            bc, bu = struct.unpack_from("<II", d, q); q += 8
            pairs.append((bc, bu)); su += bu
        if su != tu:
            i = d.find(TAG, i + 4); continue
        cat = bytearray(); bad = False
        for bc, bu in pairs:
            blk = d[q:q+bc]
            raw = None
            if blk[:2] in (b"\x78\x9c", b"\x78\x01", b"\x78\xda"):
                try: raw = zlib.decompress(blk)
                except Exception: pass
            if raw is None:
                try: raw = lzo1x_decompress(blk)
                except Exception: bad = True; break
            if len(raw) != bu: bad = True; break
            cat += raw; q += bc
        if not bad: out.append(bytes(cat))
        i = d.find(TAG, q)
    return out

def parse_image(img):
    (ln,) = struct.unpack_from("<i", img, 12)
    o = 16 + ln
    flags, nc, noff, ec, eoff, ic, ioff, doff = struct.unpack_from("<iiiiiiii", img, o)
    names = []
    oo = noff
    for _ in range(nc):
        (ln,) = struct.unpack_from("<i", img, oo); oo += 4
        if ln > 0:
            raw = img[oo:oo+ln]; oo += ln
            names.append(raw[:-1].decode("ascii", "replace"))
        else:
            names.append(img[oo:oo+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); oo += (-ln)*2
        oo += 8
    oo = ioff; impcls = []
    for _ in range(ic):
        cnn, _ = struct.unpack_from("<ii", img, oo + 8)
        onn, _ = struct.unpack_from("<ii", img, oo + 20)
        impcls.append((names[cnn], names[onn])); oo += 28
    akimps = [i for i, (c, n) in enumerate(impcls) if c == "Class" and n == "AkBank"]
    assert (doff - eoff) % ec == 0, ("export stride not exact", doff - eoff, ec)
    STR = (doff - eoff) // ec
    banks = []
    oo = eoff
    for _ in range(ec):
        ci, = struct.unpack_from("<i", img, oo)
        ni, _ = struct.unpack_from("<ii", img, oo + 12)
        _, _, _, _, size, off = struct.unpack_from("<IIIIII", img, oo + 20)
        if any(ci == -(a + 1) for a in akimps):
            banks.append((names[ni], size, off))
        oo += STR
    return names, banks

def carve_bank(img, size, off):
    seg = img[off:off+size]
    i = seg.find(b"BKHD")
    if i < 0: return None
    o = i; end = None
    while o + 8 <= len(seg):
        tag = seg[o:o+4]
        (sz,) = struct.unpack_from("<I", seg, o + 4)
        if tag in (b"HIRC", b"STID", b"ENVS"): end = o + 8 + sz
        o += 8 + sz
        if tag == b"DATA" and seg[o:o+4] not in (b"HIRC", b"STID", b"ENVS"): break
        if tag not in (b"BKHD", b"DIDX", b"DATA", b"HIRC", b"STID", b"ENVS", b"STMG", b"PLAT", b"INIT"): break
    return seg[i:end or o]

def resolve_bank(bank, want_names):
    name_by_id = {}
    for nm in want_names:
        name_by_id.setdefault(fnv1(nm.lower()), []).append(nm)
    hi = bank.find(b"HIRC")
    if hi < 0: return {}, set()
    o = hi + 8
    (n,) = struct.unpack_from("<I", bank, o); o += 4
    objs = {}
    for _ in range(n):
        t = bank[o]; (sz,) = struct.unpack_from("<I", bank, o + 1); body = bank[o+5:o+5+sz]
        oid, = struct.unpack_from("<I", body, 0)
        objs.setdefault(t, {})[oid] = body; o += 5 + sz
    S = set(objs.get(2, {})); C = set()
    for t in (5, 6, 7, 9): C.update(objs.get(t, {}))
    SC = S | C; A3 = set(objs.get(3, {}))
    def hits(body, ids):
        return {struct.unpack_from("<I", body, k)[0] for k in range(len(body) - 3)} & ids
    evmap = {}
    for eid, body in objs.get(4, {}).items():
        (cnt,) = struct.unpack_from("<I", body, 4)
        if 8 + 4 * cnt > len(body): continue
        acts = {struct.unpack_from("<I", body, 8 + 4 * k)[0] for k in range(cnt)} & A3
        evmap[eid] = (body, acts)
    di = bank.find(b"DIDX")
    didx = {}
    if di >= 0:
        (dsz,) = struct.unpack_from("<I", bank, di + 4)
        for k in range(dsz // 12):
            mid, off, sz = struct.unpack_from("<III", bank, di + 8 + 12 * k)
            didx[mid] = (off, sz)
    data = bank.find(b"DATA"); dbase = data + 8 if data >= 0 else None
    act_tgt, cont_ch, snd_f = {}, {}, {}
    for aid, body in objs.get(3, {}).items():
        tgt6 = struct.unpack_from("<I", body, 6)[0] if len(body) >= 10 else None
        act_tgt[aid] = {tgt6} & SC if tgt6 in SC else hits(body, SC) - {aid}
    for t in (5, 6, 7, 9):
        for oid, body in objs.get(t, {}).items():
            cont_ch[oid] = hits(body, SC) - {oid}
    for sid, body in objs.get(2, {}).items():
        f = hits(body, set(didx))
        if f: snd_f[sid] = f
    def media_of(node, depth=0):
        out = set()
        if node in snd_f: out.update(snd_f[node])
        if node in cont_ch and depth < 8:
            for ch in cont_ch[node]: out.update(media_of(ch, depth + 1))
        return out
    got = {}
    for eid, (body, acts) in evmap.items():
        files = set()
        for aid in acts:
            for tgt in act_tgt.get(aid, ()): files.update(media_of(tgt))
        if files: got[eid] = files
    return got, (didx, dbase, name_by_id)

def main():
    pkg = sys.argv[1]
    subs = sys.argv[2].split(",") if len(sys.argv) > 2 else ["BML_Battlemode"]
    d = open(os.path.join(CK, pkg), "rb").read()
    (ln,) = struct.unpack_from("<i", d, 12)
    o = 16 + ln
    _, _, noff = struct.unpack_from("<iii", d, o)[:3]
    H = noff
    stream = b"".join(dechunk(d, H))
    img = d[:H] + stream
    print("%s: file=%d stream=%d" % (pkg, len(d), len(stream)))
    outdir = os.path.join(A, "conv", os.path.splitext(pkg)[0])
    os.makedirs(outdir, exist_ok=True)
    open(os.path.join(outdir, "stream.bin"), "wb").write(stream)
    names, banks = parse_image(img)
    print("names=%d banks=%d" % (len(names), len(banks)))
    for nm, size, off in banks:
        print("  bank-export: %s (%d B)" % (nm, size))
    open(os.path.join(outdir, "names.txt"), "w").write("\n".join(names))
    want_events = ["Play_Batmobile_Turbo", "Stop_Batmobile_Turbo_Warmup", "Stop_Batmobile_Turbo_Destroyed",
                   "Play_BattlemodeEngine", "Play_Batmobile_Engine_Transition_In",
                   "Play_Batmobile_Engine_Transition_Out", "Play_Batmobile_Idle"] + \
                  [n for n in names if (n.startswith("Play_") or n.startswith("Stop_")) and "atmobile" in n]
    for nm, size, off in banks:
        if not any(s.lower() in nm.lower() for s in subs):
            continue
        bank = carve_bank(img, size, off)
        if not bank:
            print("  %s: carve failed" % nm); continue
        open(os.path.join(outdir, "bank_%s.bank" % nm), "wb").write(bank)
        got, (didx, dbase, name_by_id) = resolve_bank(bank, want_events)
        print("  %s: bank=%dB events-with-media=%d" % (nm, len(bank), len(got)))
        meta = []
        for eid, files in sorted(got.items()):
            nms = name_by_id.get(eid, ["?%08X" % eid])
            for f in sorted(files):
                off2, sz = didx[f]
                wem = bank[dbase+off2:dbase+off2+sz]
                if wem[:4] != b"RIFF": continue
                tag = "%s_%08X" % (nm, f)
                open(os.path.join(outdir, tag + ".wem"), "wb").write(wem)
                wav = os.path.join(outdir, tag + ".wav")
                r = subprocess.run([CLI, "-o", wav, os.path.join(outdir, tag + ".wem")], capture_output=True)
                ok = r.returncode == 0 and os.path.exists(wav)
                meta.append({"bank": nm, "event": nms[0], "eid": "%08X" % eid,
                             "media": "%08X" % f, "wav": ok})
                print("    %-40s %08X %8dB %s" % (nms[0][:40], f, sz, "WAV-OK" if ok else "FAIL"))
        json.dump(meta, open(os.path.join(outdir, "media_%s.json" % nm), "w"), indent=1)

main()

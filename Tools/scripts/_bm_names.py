"""Parse name table at stream+0; dump; grep audio/batmobile."""
import struct

s = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
names, o, trailers = [], 0, set()
for i in range(3151):
    (ln,) = struct.unpack_from("<i", s, o); o += 4
    assert 0 < ln < 512 or -512 < ln < 0, (i, ln)
    if ln > 0:
        raw = s[o:o+ln]; o += ln
        names.append(raw[:-1].decode("ascii", "replace"))
    else:
        names.append(s[o:o+(-ln)*2].decode("utf-16-le", "replace").rstrip("\x00")); o += (-ln)*2
    trailers.add(s[o:o+8]); o += 8
print("names:", len(names), "trailer variants:", len(trailers), [t.hex(" ") for t in trailers])
open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\bm_names.txt", "w").write("\n".join(names))
audio = [n for n in names if any(w in n.lower() for w in
    ["ak_", "akbank", "akevent", "sound", "cue", "wwise", "audio", "bank", "wavedata",
     "soundnode", "event", "ambient", "reverb", "attenuat", "rtpc", "switch", "state"])]
print("audio-ish:", len(audio))
for n in sorted(set(audio)):
    print("  A:", n)
bm = [n for n in names if "batmobile" in n.lower()]
print("batmobile:", len(bm))
for n in sorted(set(bm)):
    print("  BM:", n)
eng = [n for n in names if any(w in n.lower() for w in ["engine", "exhaust", "turbine", "afterburn", "boost", "throttle"])]
print("engine-ish:", len(eng))
for n in sorted(set(eng))[:40]:
    print("  E:", n)

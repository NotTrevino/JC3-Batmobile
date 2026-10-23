import binascii

def fnv1(s):
    h = 0x811C9DC5
    for b in s:
        h = ((h * 0x01000193) & 0xFFFFFFFF) ^ b
    return h
def fnv1a(s):
    h = 0x811C9DC5
    for b in s:
        h = (((h ^ b)) * 0x01000193) & 0xFFFFFFFF
    return h
def crc(s): return binascii.crc32(s) & 0xFFFFFFFF
def jenkins(s):
    h = 0
    for b in s:
        h = (h + b) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= (h >> 6)
    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= (h >> 11)
    h = (h + (h << 15)) & 0xFFFFFFFF
    return h
def djb2(s):
    h = 5381
    for b in s:
        h = ((h * 33) + b) & 0xFFFFFFFF
    return h

pairs = [("Play_BattlemodeEngine", 0x388710DB),
         ("Play_Batmobile_Engine_Transition_In", 0x102067E6)]
algos = {"fnv1": fnv1, "fnv1a": fnv1a, "crc32": crc, "jenkins": jenkins, "djb2": djb2}
for nm, want in pairs:
    print("== %s want %08X" % (nm, want))
    for v in [nm, nm.lower(), nm.upper(), nm.lower() + "\x00", nm + "\x00"]:
        for an, fn in algos.items():
            if fn(v.encode()) == want:
                print("   CALIBRATED: %s variant=%r" % (an, v))
print("done")

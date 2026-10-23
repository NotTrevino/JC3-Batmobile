"""FMOD bank recon: magic, version, GUID hits, FSB layout."""
import os, struct

p = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks\vehicles.bank"
d = open(p, "rb").read()
print("size:", len(d))
print("magic:", d[:8])
# BKHD-like? FMOD banks: 'FSB5' inside; header has version u32s
for tag in [b"FSB5", b"BANK", b"FMOD", b"GUID", b"LIST", b"STR"]:
    idxs = []
    i = d.find(tag)
    while i >= 0 and len(idxs) < 6:
        idxs.append("0x%X" % i); i = d.find(tag, i + 1)
    print("  %r: %d @ %s" % (tag, len(idxs), idxs))
evs = [l.strip() for l in open(r"E:\Modding\JC3-Batmobile\Working\Audio\serpente_fmod_events.txt")]
print("serpente events:", len(evs))
# GUIDs in file are binary LE mixed-endian; file stores {xxxxxxxx-...} -> bytes?
import re
found = 0
for g in evs:
    h = g.strip("{}").replace("-", "")
    raw = bytes.fromhex(h)
    # try raw BE and mixed-endian LE (GUID struct: first 3 fields LE)
    le = struct.pack("<IHH", struct.unpack(">IHH", raw[:8])[0], struct.unpack(">H", raw[8:10])[0], struct.unpack(">H", raw[10:12])[0]) + raw[12:] if False else None
    if d.find(raw) >= 0:
        found += 1
print("events found as raw-BE bytes:", found)

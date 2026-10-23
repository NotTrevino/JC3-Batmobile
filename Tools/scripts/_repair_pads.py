"""Repair 0x50 pad/flag bytes in a structurally edited .epe by STRING CONTEXT.

Background (MODLOG sect 31): ConvertProperty's writer emits 0x00 where the game
expects 0x50 (single bytes after null-terminated strings, plus 12-byte runs).
With no same-structure baseline, match each `string\\0` from the edited XML
against the repaired vanilla .epe (whose pads are known good) and copy the
0x50-run length, pairing occurrences in order.
"""
import re
import sys

BASE = r"Builds\test-027\repaired.epe"      # pads known good
RAW = r"Builds\test-029\fivepart_raw.epe"
OUT = r"Builds\test-029\fivepart_repaired.epe"
XML = r"Builds\test-029\fivepart.xml"

base = open(BASE, "rb").read()
raw = bytearray(open(RAW, "rb").read())

text = open(XML, encoding="utf-8").read()
# candidate strings: text between > and <, plus attribute-ish tokens
strs = set(re.findall(r">([A-Za-z0-9_][A-Za-z0-9_ .\-]{1,120})<", text))
print("distinct xml strings:", len(strs))

fixed = 0
unmatched = []
for s in sorted(strs):
    needle = s.encode() + b"\x00"
    blocs = []
    o = 0
    while True:
        o = base.find(needle, o)
        if o < 0:
            break
        # count 0x50 run right after terminator (cap 12: the sentinel runs)
        k = o + len(needle)
        n = 0
        while n < 12 and k + n < len(base) and base[k + n] == 0x50:
            n += 1
        blocs.append(n)
        o += 1
    rocs = []
    o = 0
    while True:
        o = bytes(raw).find(needle, o)
        if o < 0:
            break
        rocs.append(o)
        o += 1
    if not blocs or not rocs:
        unmatched.append(s)
        continue
    for rb, nb in zip(rocs, blocs * ((len(rocs) + len(blocs) - 1) // len(blocs))):
        k = rb + len(needle)
        m = 0
        while m < nb and k + m < len(raw) and raw[k + m] == 0x00:
            raw[k + m] = 0x50
            m += 1
        fixed += m

print("pad bytes restored:", fixed)
print("strings without baseline match:", len(unmatched))
open(OUT, "wb").write(raw)
print("wrote", OUT, len(raw), "bytes")

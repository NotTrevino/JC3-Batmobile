"""Parse the native-property table inside BmAK GlobalPersistentCookerData.upk.

Records look like:  FString "<Pkg>.<Class>:<Property>", FString "<TypeProperty>", int32 <n>
This script finds them, validates the structure, and groups by class.

Usage: python _gpcdtable.py <gpcd.upk> [out.json]
"""
import json
import re
import sys

path = sys.argv[1]
out = sys.argv[2] if len(sys.argv) > 2 else None
data = open(path, "rb").read()

name_re = re.compile(rb"[A-Za-z_0-9]+\.[A-Za-z_0-9]+:[A-Za-z_0-9]+")
TYPE_RE = re.compile(rb"^[A-Za-z_0-9]{3,30}Property$")

records = []
for m in name_re.finditer(data):
    start, end = m.start(), m.end()
    # name must be a null-terminated string: next byte 0
    if data[end:end + 1] != b"\x00":
        continue
    p = end + 1
    # next: FString type -> int32 length (includes null), then bytes
    if p + 4 > len(data):
        continue
    ln = int.from_bytes(data[p:p + 4], "little")
    if not (3 <= ln <= 64):
        continue
    tbytes = data[p + 4:p + 4 + ln]
    if not tbytes.endswith(b"\x00"):
        continue
    tname = tbytes[:-1]
    if not TYPE_RE.match(tname):
        continue
    q = p + 4 + ln
    if q + 4 > len(data):
        continue
    n = int.from_bytes(data[q:q + 4], "little")
    full = data[start:end].decode("ascii")
    pkg_class, prop = full.split(":", 1)
    if "." not in pkg_class:
        continue
    pkg, cls = pkg_class.split(".", 1)
    records.append({"offset": start, "class": cls, "package": pkg,
                    "prop": prop, "type": tname.decode("ascii"), "n": n})

print("records:", len(records))
classes = {}
for r in records:
    classes.setdefault(r["class"], []).append(r)
print("classes:", len(classes))
for cls, rows in sorted(classes.items(), key=lambda kv: -len(kv[1]))[:20]:
    types = {}
    for r in rows:
        types[r["type"]] = types.get(r["type"], 0) + 1
    print("  %-40s %3d props  %s" % (cls, len(rows), types))

if out:
    json.dump(records, open(out, "w"), indent=1)
    print("wrote", out)

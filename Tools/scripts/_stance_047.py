"""test-047 stance: move hardpoints to Tumbler stations in the PATCHED land_global.

Tumbler source ratios (measured from the PSKX wheel clusters): wheelbase/length
0.697, track/width 0.703. JC3 body is 5.001 m: Tumbler stations are front -1.945
/ rear +1.539 (front overhang 11%, rear 19%, matching the source). Track/X/Y and
radius untouched (lateral already conforms: 0.711 vs 0.703).

Edits the ConvertAdf XML (values only), re-imports, and asserts: same size,
byte-diff confined to the 4 patched floats, re-export shows the new values.
"""
import re
import subprocess

SRC = r"Research\PartsForensics\patched_land_global.xml"
NEW = {"-1.55700004": "-1.945", "1.44599998": "1.539"}

x = open(SRC, encoding="utf-8-sig").read()
counts = {old: len(re.findall(re.escape(">%s<" % old), x)) for old in NEW}
print("occurrences:", counts)
assert counts == {"-1.55700004": 2, "1.44599998": 2}, counts
for old, new in NEW.items():
    x = x.replace(">%s<" % old, ">%s<" % new)
open(r"Working\Stance\land_global_stance.xml", "w", encoding="utf-8").write(x)

r = subprocess.run(["Tools\\Gibbed\\Gibbed.JustCause3.ConvertAdf.exe", "--i",
                    r"Working\Stance\land_global_stance.xml",
                    r"Working\Stance\land_global_stance.vmodc"])
assert r.returncode == 0, r.returncode
new = open(r"Working\Stance\land_global_stance.vmodc", "rb").read()
old = open(r"Research\PartsForensics\patched_land_global.vmodc", "rb").read()
assert len(new) == len(old) == 1600, (len(new), len(old))
diffs = [i for i in range(len(old)) if old[i] != new[i]]
print("size ok; diff bytes:", len(diffs), "first/last:",
      hex(diffs[0]) if diffs else None, hex(diffs[-1]) if diffs else None)
assert diffs == [232, 233, 234, 244, 245, 246, 256, 257, 258, 268, 269, 270], diffs
print("offsets match the XML offset-in-file values (0xE8/0xF4/0x100/0x10C)")

r = subprocess.run(["Tools\\Gibbed\\Gibbed.JustCause3.ConvertAdf.exe", "--e",
                    r"Working\Stance\land_global_stance.vmodc",
                    r"Working\Stance\land_global_check.xml"])
assert r.returncode == 0, r.returncode
c = open(r"Working\Stance\land_global_check.xml", encoding="utf-8-sig").read()
zs = re.findall(r"type=\"float\">(-?[\d.]+)</member>", c)
print("hardpoint Z values now:", [z for z in zs if abs(float(z)) > 1.0])
assert c.count(">-1.94500005<") == 2 and c.count(">1.53900003<") == 2
print("STANCE OK")

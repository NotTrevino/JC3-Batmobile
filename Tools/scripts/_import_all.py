"""Run every spec in Working/Batmobile/specs/ (the whole asset matrix, one command).

For specs with an 'expect' block the outputs are regression-gated:
  expect: {sha256 | bytes-of: <reference file>}  -> mismatch is a hard failure.
Specs without 'expect' must still VERIFY PASS (byte roundtrip, counts, u16,
finite) and meet their tri budget. Usage: python _import_all.py
"""
import glob
import hashlib
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

fails = []
ran = 0
for spec_path in sorted(glob.glob("Working/Batmobile/specs/*.json")):
    spec = json.load(open(spec_path))
    print("=" * 20, os.path.basename(spec_path))
    r = subprocess.run([sys.executable, "Tools/scripts/_import_part.py", spec_path])
    if r.returncode != 0:
        fails.append(spec_path + " (importer failed)")
        continue
    ran += 1
    exp = spec.get("expect")
    if not exp:
        continue
    raw = open(spec["out"], "rb").read()
    if "bytes-of" in exp:
        ref = open(exp["bytes-of"], "rb").read()
        ok = raw == ref
        print("  regression bytes-identical to %s: %s (%d B)" %
              (exp["bytes-of"], ok, len(raw)))
    else:
        ok = hashlib.sha256(raw).hexdigest() == exp["sha256"].lower()
        print("  regression sha256 match: %s" % ok)
    if not ok:
        fails.append(spec_path + " (regression mismatch)")
print("=" * 20)
print("ran %d specs, %d failures" % (ran, len(fails)))
for f in fails:
    print("  FAIL:", f)
sys.exit(1 if fails else 0)

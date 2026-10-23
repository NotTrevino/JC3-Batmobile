"""Dump members of a .vmodc: python _members.py <vmodc> [regex-filter]"""
import re, subprocess, sys, os, tempfile
GIBBED = r'E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe'
vm = sys.argv[1]
flt = re.compile(sys.argv[2], re.I) if len(sys.argv) > 2 else None
with tempfile.TemporaryDirectory() as td:
    out = os.path.join(td, 'x.xml')
    r = subprocess.run([GIBBED, '--e', vm, out], capture_output=True)
    if r.returncode != 0:
        print('DECODE FAIL', vm); sys.exit(1)
    x = open(out, encoding='utf-8-sig').read()
i = x.find('<instances')
body = x[i:] if i >= 0 else x
print('== %s (%d B)  instances at %d' % (os.path.basename(vm), os.path.getsize(vm), i))
pat = re.compile(r'<member name="([^"]+)"[^>]*?offset-in-file="([0-9A-Fa-f]+)"[^>]*?type="([A-Za-z_0-9]+)"[^>]*>([^<]*)</member>')
for m in pat.finditer(body):
    nm, off, typ, val = m.group(1), m.group(2), m.group(3), m.group(4).strip()
    if flt and not flt.search(nm):
        continue
    print('  @%-10s %-38s %-12s %s' % (off, nm, typ, val[:60]))
# also list instance headers
for m in re.finditer(r'<instance name="([^"]+)"', body):
    print('  [instance] %s' % m.group(1))

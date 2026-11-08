import glob
import os
import re
import subprocess
import sys
import tempfile

GIBBED = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"
vm = glob.glob(r"E:\Modding\JustCause3\JC3-Batmobile\Builds\test-003\aaf\editor\entities\jc_vehicles\00_shared\modules\health\*.vmodc")[0]
print("module:", os.path.basename(vm), os.path.getsize(vm))
with tempfile.TemporaryDirectory() as td:
    xml = os.path.join(td, "x.xml")
    r = subprocess.run([GIBBED, "--e", vm, xml], capture_output=True)
    assert r.returncode == 0
    x = open(xml, encoding="utf-8-sig").read()
    i = x.find("<instances")
    for m in re.finditer(
            r"<member name=\"([^\"]+)\"[^>]*?(?:offset-in-file=\"([0-9A-Fa-f]+)\"[^>]*?)?"
            r"type=\"(int32|uint32|float|int8|string)\"[^>]*>([^<]*)</member>",
            x[i:] if i >= 0 else x):
        nm, off, typ, val = m.group(1), m.group(2) or "?", m.group(3), m.group(4).strip()[:44]
        if re.search(r"armor|armour|health|damage|explos|fire|bullet|collision|ram|crush|resist|immune|threshold|break|wreck", nm, re.I):
            print("  @%s %-38s %-7s %s" % (off, nm, typ, val))
epe = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_epe.xml", encoding="utf-8").read()
print("epe refs to lave/health:", len(re.findall(r"[Ll]ave|[Hh]ealth", epe)))
for m in set(re.findall(r"[A-Za-z_]*(?:[Hh]ealth|[Ll]ave)[A-Za-z_]*", epe)):
    print("  epe:", m)

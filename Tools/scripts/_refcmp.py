"""Compare circuit-racer suspension/rigid_body/steering/brakes vs Serpente."""
import glob
import os
import re
import subprocess
import sys
import tempfile

GIBBED = r"E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"
REF = r"E:\Modding\JC3-Batmobile\Working\Movement\refcar\aaf\editor\entities\jc_vehicles\01_land\v0405_car_mugello_moderncircuitracer\modules\default"
DONOR = r"E:\Modding\JC3-Batmobile\Builds\test-003\aaf\editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default"

def members(vm):
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as t:
        xml = t.name
    r = subprocess.run([GIBBED, "--e", vm, xml], capture_output=True)
    if r.returncode != 0:
        return None
    x = open(xml, encoding="utf-8-sig").read()
    i = x.find("<instances")
    rows = []
    for m in re.finditer(
            r"<member name=\"([^\"]+)\"[^>]*?(?:offset-in-file=\"([0-9A-Fa-f]+)\"[^>]*?)?"
            r"type=\"(int32|uint32|float|int8|string)\"[^>]*>([^<]*)</member>",
            x[i:] if i >= 0 else x):
        rows.append((m.group(1), m.group(3), m.group(4).strip()[:44]))
    os.unlink(xml)
    return rows

for mod in ["suspension", "rigid_body", "land_steering", "brakes"]:
    r = glob.glob(os.path.join(REF, "*_%s.vmodc" % mod))
    d = glob.glob(os.path.join(DONOR, "*_%s.vmodc" % mod))
    if not r or not d:
        print("MISSING", mod)
        continue
    rm, dm = members(r[0]), members(d[0])
    print("== %s (ref=%d donor=%d members)" % (mod, len(rm), len(dm)))
    from collections import defaultdict
    dd = defaultdict(list)
    for n, t, v in dm:
        dd[n].append(v)
    seen = set()
    for n, t, v in rm:
        if n not in seen:
            seen.add(n)
            print("   %-34s ref=%-14s donor=%s" % (n, v, "|".join(dd.get(n, ["--"]))))

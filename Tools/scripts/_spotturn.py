import glob
import os
import re
import subprocess
import tempfile

GIBBED = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"
pat = re.compile(r"<member name=\"([^\"]+)\"[^>]*>([^<]*)</member>")
keys = re.compile(r"spot|tank|skid.?steer|oppos|counter|turn_on|forward_ratio|diff|split|awd|4wd|lock|distribut", re.I)
with tempfile.TemporaryDirectory() as td:
    for root, ds, fs in os.walk(r"E:\Modding\JustCause3\JC3-Batmobile\Builds\test-003\aaf"):
        for f in fs:
            if f.endswith("custom_land_global.vmodc") or f.endswith("land_global.vmodc") \
                    or f.endswith("transmission.vmodc") or f.endswith("land_steering.vmodc"):
                vm = os.path.join(root, f)
                xml = os.path.join(td, "x.xml")
                r = subprocess.run([GIBBED, "--e", vm, xml], capture_output=True)
                if r.returncode != 0:
                    continue
                x = open(xml, encoding="utf-8-sig").read()
                i = x.find("<instances")
                for m in pat.finditer(x[i:] if i >= 0 else x):
                    if keys.search(m.group(1)):
                        print("%-28s | %-38s = %s" % (f.split("muscle_")[-1][:28], m.group(1), m.group(2)[:44]))

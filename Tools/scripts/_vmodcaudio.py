import glob, os, re, subprocess, tempfile

mods = glob.glob("Builds/test-003/aaf/editor/entities/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/modules/default/*.vmodc")
G = r"E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"
pat = re.compile(r'<member name="([^"]*(?:audio|sound|stream|fsb|bank|event|voice|exhaust|engine|nitro|turbo)[^"]*)"[^>]*>([^<]*)</member>', re.I)
for vm in sorted(mods):
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as t:
        xml = t.name
    r = subprocess.run([G, "--e", vm, xml], capture_output=True)
    if r.returncode != 0:
        print("DECODE-FAIL", os.path.basename(vm))
        continue
    x = open(xml, encoding="utf-8-sig").read()
    for m in pat.finditer(x):
        print("%-45s | %s = %s" % (os.path.basename(vm)[:45], m.group(1), m.group(2)[:60]))
    os.unlink(xml)

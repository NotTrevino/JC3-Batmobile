"""Full decode of JC3 physics modules (all members) -> phys inventory JSON."""
import glob, os, re, subprocess, sys, tempfile

GIBBED = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"

def members(xml_path):
    x = open(xml_path, encoding="utf-8-sig").read()
    i = x.find("<instances")
    rows = []
    for m in re.finditer(
            r"<member name=\"([^\"]+)\"[^>]*?(?:offset-in-file=\"([0-9A-Fa-f]+)\"[^>]*?)?"
            r"type=\"(int32|uint32|float|int8|string)\"[^>]*>([^<]*)</member>",
            x[i:] if i >= 0 else x):
        rows.append({"name": m.group(1), "type": m.group(3), "off": m.group(2) or "?",
                     "val": m.group(4).strip()[:48]})
    return rows

def main():
    root = os.path.join("Builds", "test-003", "aaf")
    phys = ["brakes", "buoyancy", "land_aerodynamics", "rigid_body", "suspension",
            "land_steering", "front_tire", "rear_tire", "land_global", "custom_land_global",
            "transmission", "land_engine"]
    inv = {}
    with tempfile.TemporaryDirectory() as td:
        for mod in phys:
            pat = os.path.join(root, "**", "*_%s.vmodc" % mod)
            fs = glob.glob(pat, recursive=True)
            if not fs:
                print("MISSING", mod)
                continue
            vm = fs[0]
            out = os.path.join(td, "x.xml")
            r = subprocess.run([GIBBED, "--e", vm, out], capture_output=True)
            if r.returncode != 0:
                print("DECODE-FAIL", mod)
                continue
            rows = members(out)
            inv[mod] = {"file": os.path.basename(vm), "size": os.path.getsize(vm), "members": rows}
            print("== %s (%d members)" % (mod, len(rows)))
            for rr in rows:
                print("   @%s %-36s %-7s %s" % (rr["off"], rr["name"], rr["type"], rr["val"]))
    import json
    json.dump(inv, open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\jc3_phys.json", "w"), indent=1)
    print("wrote jc3_phys.json")

main()

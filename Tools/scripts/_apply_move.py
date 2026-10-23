"""Apply movement-target edits to Serpente stat modules (handling only).

Takes a targets file (see Working/Movement/bmak_targets.json): a list of
{file, member, occurrence, old, new}. For each file: decode with ConvertAdf,
assert the old value, replace that occurrence, re-import, assert same size,
re-export and assert the new value. Refuses UNKNOWN values. Nothing here
touches collision (physicsc/RAYs) — movement modules only.
Usage: python _apply_move.py <targets.json> <aaf-dir> [--check-only]
"""
import re
import subprocess
import sys

GIBBED = r"E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe"


def decode(vm, xml):
    r = subprocess.run([GIBBED, "--e", vm, xml], capture_output=True)
    assert r.returncode == 0, ("decode failed", vm, r.returncode)
    return open(xml, encoding="utf-8-sig").read()


def encode(xml, vm):
    r = subprocess.run([GIBBED, "--i", xml, vm], capture_output=True)
    assert r.returncode == 0, ("import failed", vm, r.returncode)


def set_member(xml, member, occurrence, old, new):
    pat = re.compile(r"(<member name=\"%s\"[^>]*>)([^<]*)(</member>)" % re.escape(member))
    hits = list(pat.finditer(xml))
    assert len(hits) > occurrence, (member, len(hits))
    assert hits[occurrence].group(2) == old, (member, hits[occurrence].group(2), old)
    s, e = hits[occurrence].span(2)
    return xml[:s] + new + xml[e:]


def main():
    import json
    import os
    import tempfile
    spec = json.load(open(sys.argv[1]))
    aaf = sys.argv[2]
    check_only = "--check-only" in sys.argv
    if spec.get("status") != "final":
        raise SystemExit("targets are not final (BmAK numbers still UNKNOWN) — refusing")
    with tempfile.TemporaryDirectory() as td:
        for ed in spec["edits"]:
            vm = os.path.join(aaf, *ed["file"].split("/"))
            before = open(vm, "rb").read()
            xml = os.path.join(td, "x.xml")
            text = decode(vm, xml)
            text = set_member(text, ed["member"], ed.get("occurrence", 0),
                              ed["old"], ed["new"])
            if check_only:
                print("OK %s %s: %s -> %s" % (ed["file"].split("/")[-1],
                                              ed["member"], ed["old"], ed["new"]))
                continue
            open(xml, "w", encoding="utf-8").write(text)
            encode(xml, vm)
            after = open(vm, "rb").read()
            assert len(after) == len(before), (ed["file"], len(before), len(after))
            text2 = decode(vm, os.path.join(td, "y.xml"))
            hits = re.findall(r"<member name=\"%s\"[^>]*>([^<]*)</member>" % re.escape(ed["member"]), text2)
            assert len(hits) > ed.get("occurrence", 0), (ed["file"], ed["member"])
            got = hits[ed.get("occurrence", 0)]
            try:
                ok = abs(float(got) - float(ed["new"])) < 1e-4
            except ValueError:
                ok = got == ed["new"]
            assert ok, (ed["file"], ed["member"], got, ed["new"])
            print("APPLIED %s %s = %s (%d B unchanged)" %
                  (ed["file"].split("/")[-1], ed["member"], ed["new"], len(after)))
    print("done")


main()

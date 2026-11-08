"""Parse .epe tree: every Sound GUID with its component path (system roles)."""
import json, os
import xml.etree.ElementTree as ET

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
t = ET.parse(os.path.join(A, "serpente_epe.xml"))
rows = []

def walk(el, path):
    nm = el.get("name", "")
    newp = path + "/" + nm if nm else path
    for v in el.findall("value"):
        if v.get("name") == "Sound" and (v.text or "").strip():
            rows.append((newp, v.text.strip()[:48]))
    for ch in el:
        walk(ch, newp)

walk(t.getroot(), "")
print("sound refs:", len(rows))
for p, g in rows:
    print("  %-70s %s" % (p[-70:], g))
json.dump(rows, open(os.path.join(A, "epe_tree.json"), "w"), indent=1)

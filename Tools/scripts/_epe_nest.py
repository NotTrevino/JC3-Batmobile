import xml.etree.ElementTree as ET


def walk(elem, depth, out):
    for obj in elem.findall("object"):
        cls = None
        name = idx = None
        for v in obj.findall("value"):
            if v.get("name") == "_class":
                cls = v.text
            elif v.get("name") == "name":
                name = v.text
            elif v.get("name") == "part_index":
                idx = v.text
        if cls == "CPartProp":
            out.append(("  " * depth + "%s idx=%s" % (name, idx)))
        walk(obj, depth + 1, out)


for tag, path in [("dababy", r"Research\PartsForensics\dababy_epe.xml"),
                  ("serpente", r"Builds\test-027\vanilla.xml")]:
    root = ET.parse(path).getroot()
    out = []
    walk(root, 0, out)
    print("=" * 15, tag, len(out))
    for line in out:
        print(line)

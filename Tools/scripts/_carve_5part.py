"""Carve the 5-part .epe for test-029: keep body idx 0 + wheels 26/27/11/12
(all direct children of body, mirroring the DaBaby's flat tree), drop the rest.
Verifies the kept set before writing."""
import xml.etree.ElementTree as ET

KEEP = {"0", "26", "27", "11", "12"}

src = r"Builds\test-027\vanilla.xml"
dst = r"Builds\test-029\fivepart.xml"

tree = ET.parse(src)
root = tree.getroot()


def part_index(obj):
    for v in obj.findall("value"):
        if v.get("name") == "part_index":
            return v.text
    return None


def is_part(obj):
    return any(v.get("name") == "_class" and v.text == "CPartProp"
               for v in obj.findall("value"))


removed = []
kept = []
front_wheels = []


def prune(parent):
    for obj in list(parent.findall("object")):
        if is_part(obj):
            idx = part_index(obj)
            if idx in ("26", "27"):
                # nested under engine in vanilla; the DaBaby parents all four
                # wheels directly under the body, so relocate them there
                front_wheels.append(obj)
                parent.remove(obj)
            elif idx in KEEP:
                kept.append(idx)
                prune(obj)  # may still hold dropped children (none expected)
            else:
                # rescue kept descendants first (front wheels nest under engine)
                for sub in list(obj.iter("object")):
                    if is_part(sub) and part_index(sub) in ("26", "27"):
                        front_wheels.append((part_index(sub), sub))
                name = next((v.text for v in obj.findall("value")
                             if v.get("name") == "name"), "?")
                removed.append("%s idx=%s" % (name, idx))
                parent.remove(obj)
        else:
            prune(obj)


prune(root)
assert sorted(kept) == ["0", "11", "12"], kept
assert sorted(i for i, _ in front_wheels) == ["26", "27"], front_wheels
body = next(o for o in root.iter("object")
            if is_part(o) and part_index(o) == "0")
for _, o in sorted(front_wheels):
    body.append(o)
    kept.append(part_index(o))
assert sorted(kept) == ["0", "11", "12", "26", "27"], kept
kids = [part_index(o) for o in body.findall("object") if is_part(o)]
assert sorted(kids) == ["11", "12", "26", "27"], kids
print("body children now:", kids)
print("kept:", sorted(kept), "removed:", len(removed))
tree.write(dst, encoding="utf-8", xml_declaration=True)
print("wrote", dst)

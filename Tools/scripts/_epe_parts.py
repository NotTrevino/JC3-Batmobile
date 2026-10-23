import re
import sys

jobs = [(sys.argv[i], sys.argv[i + 1]) for i in range(1, len(sys.argv), 2)] or \
    [("dababy", r"Research\PartsForensics\dababy_epe.xml"),
     ("serpente", r"Research\PartsForensics\serpente_epe.xml")]
for tag, path in jobs:
    x = open(path, encoding="utf-8").read()
    print("=" * 20, tag, "CPartProp:", x.count("CPartProp"))
    # name lines immediately followed by name_hash lines
    pairs = re.findall(
        r'<value name="name" type="string">([^<]*)</value>\s*'
        r'<value name="name_hash" type="int">(-?\d+)</value>\s*'
        r'<value name="part_index" type="int">(-?\d+)</value>', x)
    print("parts:", len(pairs))
    for name, h, idx in pairs:
        print("  idx=%s %s (%s)" % (idx, name, h))

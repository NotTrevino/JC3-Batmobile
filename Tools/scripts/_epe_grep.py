import sys

term = sys.argv[1].lower()
for tag, path in [("dababy", r"Research\PartsForensics\dababy_epe.xml"),
                  ("serpente", r"Research\PartsForensics\serpente_epe.xml")]:
    print("=" * 20, tag)
    for i, line in enumerate(open(path, encoding="utf-8")):
        if term in line.lower():
            print("L%d: %s" % (i + 1, line.strip()[:220]))

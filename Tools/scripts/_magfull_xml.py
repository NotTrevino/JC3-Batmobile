import re

p = "Working/TexProbe/magfull/body_dif.xml"
x = open(p, encoding="utf-8").read()
x2, n1 = re.subn(r'(<element offset="128" size=")\d+(")',
                 lambda m: m.group(1) + "2796216" + m.group(2), x, count=1)
x2, n2 = re.subn(r'<element offset="\d+" size="\d+" external="True"[^/]*/>',
                 '<element offset="0" size="0" external="False" '
                 'unknown8="00000000" unknownA="00000000" />', x2)
open(p, "w", encoding="utf-8").write(x2)
print("element0 resized:", n1, "externals zeroed:", n2)
for line in x2.splitlines():
    if "element" in line:
        print("  ", line.strip())

"""JC3 camera inventory: car_base instances (values) + Serpente camera refs."""
import json, os, re, struct

x = open(r"E:\Modding\JC3-Batmobile\Working\Audio\car_base.xml", encoding="utf-8").read()
i = x.find("<instances")
print("instances at:", i, "total len:", len(x))
rows = []
for m in re.finditer(
        r"<member name=\"([^\"]+)\"[^>]*?(?:offset-in-file=\"([0-9A-Fa-f]+)\"[^>]*?)?"
        r"type=\"(int32|uint32|float|int8|string)\"[^>]*>([^<]*)</member>",
        x[i:] if i >= 0 else x):
    rows.append({"name": m.group(1), "type": m.group(3), "off": m.group(2) or "?",
                 "val": m.group(4).strip()[:48]})
print("members:", len(rows))
for r in rows:
    print("  @%s %-34s %-7s %s" % (r["off"], r["name"], r["type"], r["val"]))

e = open(r"E:\Modding\JC3-Batmobile\Working\Audio\serpente_epe.xml", encoding="utf-8").read()
print("== Serpente camera refs:")
for m in re.finditer(r"<object name=\"(CCamera[^\"]+)\">(.*?)</object>", e, re.S):
    cls, body = m.group(1), m.group(2)
    nm = re.search(r'<value name="name" type="string">([^<]+)</value>', body)
    det = re.findall(r"<value[^>]*>([^<]{0,120})</value>", body)
    print("  %s name=%s" % (cls, nm.group(1) if nm else "?"))
    for dd in det[:6]:
        if dd.strip() and "class" not in dd:
            print("     ", dd.strip()[:110])
json.dump(rows, open(r"E:\Modding\JC3-Batmobile\Working\Audio\jc3_cam.json", "w"), indent=1)

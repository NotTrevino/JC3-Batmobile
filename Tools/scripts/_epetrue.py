"""TRUE per-object name->Sound map (same <object> element only)."""
import json, os, re

x = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_epe.xml", encoding="utf-8").read()
objs = re.findall(r"<object id=\"[0-9A-F]+\">(.*?)</object>", x, re.S)
print("objects:", len(objs))
rows = []
for o in objs:
    nm = re.search(r'<value name="name" type="string">([^<]+)</value>', o)
    sm = re.search(r'<value name="Sound" type="vec_byte">([0-9A-F,]+)</value>', o)
    cl = re.search(r'<value name="_class" type="string">([^<]+)</value>', o)
    if sm:
        rows.append(((nm.group(1) if nm else "(noname)"), (cl.group(1) if cl else "?"),
                     bytes(int(b, 16) for b in sm.group(1).split(",")).hex()))
print("objects with Sound:", len(rows))
for nm, cl, g in rows:
    print("  %-32s %-18s %s" % (nm, cl, g[:16] + "..."))
json.dump(rows, open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\epe_true.json", "w"), indent=1)

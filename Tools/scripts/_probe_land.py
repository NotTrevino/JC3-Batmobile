import re


def members(path):
    x = open(path, encoding="utf-8-sig").read()
    i = x.find("<instances")
    inst = x[i:]
    return re.findall(r"<member name=\"([^\"]+)\"[^>]*>([^<]*)</member>", inst)


a = members(r"Research\PartsForensics\ee_land_global.xml")
b = members(r"Research\PartsForensics\patched_land_global.xml")
da = {k: v for k, v in a}
db = {k: v for k, v in b}
print("ee members:", len(a), "patched members:", len(b))
for k in db:
    if k not in da:
        print("NEW in patched: %-30s %s" % (k, db[k][:60]))
for k, v in da.items():
    if k in db and db[k] != v:
        print("CHANGED %-30s ee=%s patched=%s" % (k, v[:50], db[k][:50]))

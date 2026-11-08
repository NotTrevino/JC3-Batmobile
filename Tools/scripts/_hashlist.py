import os
base = r"E:\Modding\JustCause3\JC3-Batmobile\Research\Arkham Knight SFX\Arkham Knight SFX\batman_bnk"
for root, ds, fs in os.walk(base):
    for f in fs:
        print(os.path.getsize(os.path.join(root, f)), os.path.relpath(os.path.join(root, f), base))
h = os.path.join(base, "bnk", "hashlist.txt")
d = open(h, "rb").read()
print("hashlist bytes:", len(d))
lines = d.splitlines()
print("lines:", len(lines))
for l in lines[:15]:
    print("  ", l[:120])

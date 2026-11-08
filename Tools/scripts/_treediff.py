import os

def snap(root):
    out = {}
    for dp, dn, fs in os.walk(root):
        for f in fs:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, root).replace(os.sep, "/")] = os.path.getsize(p)
    return out

a059 = snap(r"E:\Modding\JustCause3\JC3-Batmobile\Builds\test-059\aaf")
a062 = snap(r"E:\Modding\JustCause3\JC3-Batmobile\Builds\test-062\aaf")
k59, k62 = set(a059), set(a062)
print("059 files:", len(k59), "bytes:", sum(a059.values()))
print("062 files:", len(k62), "bytes:", sum(a062.values()))
only59 = sorted(k59 - k62)
only62 = sorted(k62 - k62)
print("only in 059:", len(only59))
for f in only59[:20]:
    print("  -", f, a059[f])
print("only in 062:", len(only62))
for f in only62[:20]:
    print("  +", f, a062[f])
diff = 0
for f in sorted(k59 & k62):
    if a059[f] != a062[f]:
        diff += 1
        if abs(a059[f] - a062[f]) > 1000:
            print("  CHG %-80s %d -> %d" % (f[-80:], a059[f], a062[f]))
print("changed-size files:", diff)

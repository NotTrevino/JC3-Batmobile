import re,struct,sys,glob
exe=open(r"D:/Games/Just Cause 3/JustCause3.exe","rb").read()
pe=struct.unpack_from("<I",exe,0x3c)[0]; n=struct.unpack_from("<H",exe,pe+6)[0]; opt=struct.unpack_from("<H",exe,pe+20)[0]
base=struct.unpack_from("<Q",exe,pe+24+24)[0]; secs=[]
for i in range(n):
    o=pe+24+opt+40*i; name=exe[o:o+8].rstrip(b"\0").decode(); vs,va,rs,ra=struct.unpack_from("<IIII",exe,o+8); ch=struct.unpack_from("<I",exe,o+36)[0]; secs.append((name,va,vs,ra,rs,ch))
print("base",hex(base),[ (s[0],hex(s[1]),hex(s[2])) for s in secs])
def f(v):
    r=v-base
    for nm,va,vs,ra,rs,ch in secs:
        if va<=r<va+max(vs,rs): return nm,(ra+r-va if r-va<rs else None),ch
    return None,None,0
src=" ".join(open(p,encoding="utf-8",errors="ignore").read() for p in glob.glob(sys.argv[1]+"/src/**/*.*",recursive=True))
for m in sorted(set(re.findall(r"0x14[0-9A-Fa-f]{7}",src))):
    v=int(m,16); nm,off,ch=f(v)
    if off is None: print(m,nm,"bss/none"); continue
    b=exe[off-2:off+6].hex(" ")
    exe_ = bool(ch & 0x20000000)
    print(m,nm,"code" if exe_ else "data", b)

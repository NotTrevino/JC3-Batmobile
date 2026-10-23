"""Read a Windows minidump far enough to attribute a JC3 crash: exception code,
fault address, and faulting module + offset. stdlib only (pip is blocked here).

Usage: python dumpfault.py <file.dmp> [more.dmp ...]
"""
import struct
import sys

EXCEPTION = 6
MODULE_LIST = 4


def u32(d, o):
    return struct.unpack_from("<I", d, o)[0]


def u64(d, o):
    return struct.unpack_from("<Q", d, o)[0]


def mstring(d, rva):
    n = u32(d, rva)
    return d[rva + 4:rva + 4 + n].decode("utf-16-le", errors="replace")


def parse(path):
    d = open(path, "rb").read()
    assert d[:4] == b"MDMP", path
    nstreams, dirstart = struct.unpack_from("<II", d, 8)
    streams = {}
    for i in range(nstreams):
        t, size, rva = struct.unpack_from("<III", d, dirstart + 12 * i)
        streams[t] = (rva, size)
    # exception
    erva, _ = streams[EXCEPTION]
    code = u32(d, erva + 8)
    addr = u64(d, erva + 8 + 16)
    # modules
    mrva, _ = streams[MODULE_LIST]
    n = u32(d, mrva)
    mods = []
    for i in range(n):
        o = mrva + 4 + 108 * i
        base = u64(d, o)
        size = u32(d, o + 8)
        name = mstring(d, u32(d, o + 20))
        mods.append((base, size, name))
    owner = "???"
    off = 0
    # ExceptionAddress is the faulting *instruction*; attribute by containing module
    for base, size, name in mods:
        if base <= addr < base + size:
            owner = name.split("\\")[-1]
            off = addr - base
            break
    # params of the access violation: type (0=read) + address
    # EXCEPTION_RECORD at erva+8: code(+0) flags(+4) record(+8) addr(+16) count(+24) info(+32)
    rec = erva + 8
    pcount = u32(d, rec + 24)
    base = rec + 32
    params = [u64(d, base + 8 * i) for i in range(min(pcount, 15))]
    return code, addr, owner, off, params


for path in sys.argv[1:]:
    try:
        code, addr, mod, off, params = parse(path)
        rw = {0: "READ", 1: "WRITE", 8: "EXEC"}.get(params[0], "?") if params else "?"
        target = "0x%x" % params[1] if len(params) > 1 else "?"
        print("%s: code=0x%08x %s of %s at %s+0x%x (rip=0x%x)" %
              (path.split("\\")[-1], code, rw, target, mod, off, addr))
    except Exception as e:
        print("%s: UNREADABLE (%s)" % (path, e))

"""LZO1X-1 decompressor, ported from lzo1x_d.ch (nemequ/lzo). States, no gotos."""
M2_MAX_OFFSET = 0xBFFF

class Ctx:
    def __init__(self, data):
        self.d = data
        self.n = len(data)
        self.ip = 0
        self.op = bytearray()

    def u8(self):
        if self.ip >= self.n: raise ValueError("overrun")
        b = self.d[self.ip]; self.ip += 1
        return b

    def take(self, k):
        if self.ip + k > self.n: raise ValueError("overrun")
        self.op += self.d[self.ip:self.ip+k]; self.ip += k

    def match_copy(self, m, extra):
        # copy 2 + extra bytes, overlap-safe (m advances each byte, like C)
        if m < 0: raise ValueError("lookbehind")
        if m + 2 + extra <= len(self.op):
            self.op += self.op[m:m+2+extra]
            return
        for _ in range(2 + extra):
            self.op.append(self.op[m]); m += 1

def lzo1x_decompress(data):
    c = Ctx(data)
    op = c.op
    # ---- start ----
    t = c.d[c.ip]  # PEEK (C tests *ip without consuming)
    if t > 17:
        c.ip += 1
        t -= 17
        if t < 4:
            c.take(t)
            t = c.u8()
            inner = True
        else:
            c.take(t)
            inner = False  # -> FLR below
            t = c.u8()
            if t >= 16:
                inner = True
            else:
                m = len(op) - (1 + M2_MAX_OFFSET) - (t >> 2) - (c.u8() << 2)
                if m < 0: raise ValueError("lb-flr")
                c.match_copy(m, 1)
                # match_done
                t = c.d[c.ip-2] & 3
                if t == 0:
                    inner = False  # outer loop
                    t = None
                else:
                    c.take(t)
                    t = c.u8()
                    inner = True
    else:
        inner = False  # outer loop with t already read? no: outer reads fresh
        t = None

    if inner:
        inner_loop(c, t)
        t = None
    # ---- outer loop ----
    while True:
        if t is None:
            if c.ip >= c.n: break
            t = c.u8()
        if t >= 16:
            inner_loop(c, t)
            t = None
            continue
        # literal run: length t (+3), t==0 extended
        if t == 0:
            while c.d[c.ip] == 0:
                t += 255; c.ip += 1
            t += 15 + c.d[c.ip]; c.ip += 1
        c.take(t + 3)
        # FLR
        if c.ip >= c.n: break
        t = c.u8()
        if t >= 16:
            inner_loop(c, t)
            t = None
            continue
        m = len(op) - (1 + M2_MAX_OFFSET) - (t >> 2) - (c.u8() << 2)
        if m < 0: raise ValueError("lb-flr2")
        c.match_copy(m, 1)
        t = c.d[c.ip-2] & 3
        if t == 0:
            t = None
            continue
        c.take(t)
        t = None  # outer re-reads? NO -- after FLR literals, C falls to inner loop!
        # C code: match_done -> match_next copies t lits -> t=*ip++ -> inner loop
        if c.ip >= c.n: break
        t = c.u8()
        inner_loop(c, t)
        t = None
    return bytes(op)

def inner_loop(c, t):
    op = c.op
    while True:
        # dispatch on t (already read)
        if t >= 64:
            m = len(op) - 1 - ((t >> 2) & 7) - (c.u8() << 3)
            t = (t >> 5) - 1
            if m < 0 or t <= 0: raise ValueError("m2")
            c.match_copy(m, t)
        elif t >= 32:
            t &= 31
            if t == 0:
                while c.d[c.ip] == 0:
                    t += 255; c.ip += 1
                t += 31 + c.d[c.ip]; c.ip += 1
            m = len(op) - 1 - ((c.d[c.ip] >> 2) + (c.d[c.ip+1] << 6)); c.ip += 2
            if m < 0: raise ValueError("m3")
            c.match_copy(m, t)
        elif t >= 16:
            m = len(op) - ((t & 8) << 11)
            t &= 7
            if t == 0:
                while c.d[c.ip] == 0:
                    t += 255; c.ip += 1
                t += 7 + c.d[c.ip]; c.ip += 1
            m -= (c.d[c.ip] >> 2) + (c.d[c.ip+1] << 6); c.ip += 2
            if m == len(op): return bytes(op)  # eof_found
            m -= 0x4000
            if m < 0: raise ValueError("m4")
            c.match_copy(m, t)
        else:
            m = len(op) - 1 - (t >> 2) - (c.u8() << 2)
            if m < 0: raise ValueError("lb-m1")
            c.match_copy(m, 0)
        # match_done
        t = c.d[c.ip-2] & 3
        if t == 0:
            return
        c.take(t)
        t = c.u8()

if __name__ == "__main__":
    d = open("E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole/CityX.upk", "rb").read()
    i = 0xACD
    blk = d[i+64:i+64+45961]
    print("block head:", blk[:8].hex())
    try:
        out = lzo1x_decompress(blk)
        print("OUT:", len(out), "want 131072", "MATCH" if len(out) == 131072 else "MISMATCH")
        print("head:", bytes(out[:64]))
        print("ip-consumed check: tail bytes:", blk[-8:].hex())
    except Exception:
        import traceback; traceback.print_exc()

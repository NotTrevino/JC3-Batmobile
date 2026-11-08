"""adf_append.py - grow an ADF v4 file by appending, never by shifting data (B-13).

The JC3 profile tables (`item.onlinec`, `task.onlinec`, `online.stringlookup`) are ADF v4: one
instance whose arrays are (u64 data-relative offset, u64 count) headers. Moving bytes inside the data
block would mean finding and fixing every pointer; appending does not. This module:

  * appends new arrays / strings at the END of the instance's data block (8-aligned) and returns
    their data-relative offsets;
  * repoints existing array headers (an absolute position inside the data block) at them - the old
    arrays stay behind as unreferenced bytes;
  * appends entries to the string-hash table (`name\\0` + u64 hash, the format the files use);
  * moves the trailing sections (instance table, type table, string-hash table, name table - none of
    them holds a data-relative offset) and fixes the header offsets, the instance size and the total.

Nothing that was in the data block moves, so every pointer the edit does not touch stays valid.
`build()` with no edits returns the input unchanged.
"""
from __future__ import annotations

import struct


class Append:
    def __init__(self, blob: bytes):
        self.blob = bytes(blob)
        hdr = struct.unpack_from("<11I", blob, 0)
        (self.magic, self.version, self.inst_n, self.inst_off, self.type_n, self.type_off,
         self.sh_n, self.sh_off, self.name_n, self.name_off, self.total) = hdr
        if self.magic != 0x41444620 or self.version != 4:
            raise SystemExit("not ADF v4")
        if self.inst_n != 1:
            raise SystemExit("only single-instance files are supported")
        _nh, _th, self.D, self.size = struct.unpack_from("<4I", blob, self.inst_off)
        if not (self.D + self.size <= self.inst_off < self.type_off <= self.sh_off <= self.name_off
                <= self.total == len(blob)):
            raise SystemExit("unexpected section order")
        self.data = bytearray(blob[self.D:self.D + self.size])
        self.sh_add: list[tuple[str, int]] = []
        self.touched = False

    # --- data block
    def add(self, payload: bytes, align: int = 8) -> int:
        """Append bytes to the data block; return their data-relative offset."""
        while len(self.data) % align:
            self.data.append(0)
        off = len(self.data)
        self.data += payload
        self.touched = True
        return off

    def add_string(self, s: str) -> int:
        return self.add(s.encode("utf-8") + b"\x00", 1)

    def u(self, fmt: str, rel: int):
        return struct.unpack_from(fmt, self.data, rel)

    def put(self, fmt: str, rel: int, *v) -> None:
        struct.pack_into(fmt, self.data, rel, *v)
        self.touched = True

    def array(self, header_rel: int) -> tuple[int, int]:
        return struct.unpack_from("<QQ", self.data, header_rel)

    def repoint(self, header_rel: int, off: int, count: int) -> None:
        self.put("<QQ", header_rel, off, count)

    # --- string-hash table
    def string_hashes(self) -> dict[int, str]:
        out, p = {}, self.sh_off
        for _ in range(self.sh_n):
            e = self.blob.index(b"\x00", p)
            s = self.blob[p:e].decode("latin-1")
            h, = struct.unpack_from("<Q", self.blob, e + 1)
            out[h] = s
            p = e + 9
        if p != self.name_off:
            raise SystemExit(f"string-hash table ends at {p}, name table starts at {self.name_off}")
        return out

    def add_string_hash(self, s: str, h: int) -> None:
        if h in self.string_hashes() or any(x[1] == h for x in self.sh_add):
            return
        self.sh_add.append((s, h))
        self.touched = True

    # --- write
    def build(self) -> bytes:
        if not self.touched:
            return self.blob
        b = self.blob
        new_inst = (self.D + len(self.data) + 15) // 16 * 16
        d1 = new_inst - self.inst_off
        if d1 < 0:
            raise SystemExit("internal: data shrank")
        sh_extra = b"".join(s.encode("latin-1") + b"\x00" + struct.pack("<Q", h) for s, h in self.sh_add)
        out = bytearray(b[:self.D]) + self.data
        out += b"\x00" * (new_inst - len(out))
        out += b[self.inst_off:self.name_off]          # instance, type, string-hash tables
        out += sh_extra                                # new string-hash entries
        out += b[self.name_off:]                       # name table
        hdr = [self.magic, self.version, self.inst_n, self.inst_off + d1, self.type_n,
               self.type_off + d1, self.sh_n + len(self.sh_add), self.sh_off + d1, self.name_n,
               self.name_off + d1 + len(sh_extra), len(out)]
        struct.pack_into("<11I", out, 0, *hdr)
        struct.pack_into("<I", out, hdr[3] + 12, len(self.data))
        return bytes(out)

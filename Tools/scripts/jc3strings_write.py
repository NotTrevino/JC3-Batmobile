"""jc3strings_write.py - add string pairs to a JC3 `.stringlookup` (B-13a, blocker B-2 of B-13).

Gibbed's ConvertAdf is NOT usable here: its export/import round trip of `profile/online.stringlookup`
keeps the counts but re-lays the shared `Text` blob, so 14,360 of 14,712 strings point at the wrong
bytes (`MUGELLO QUIPOZZA F` -> `F`, MODLOG 2026-10-31). This writer patches the ADF v4 file directly.

Layout it relies on (read by `jc3adf`, checked at run time, refused otherwise):

  root `StringLookup` at data offset 0:  Languages A[LanguageStringLookup], Text A[int8]
  LanguageStringLookup:  SortedPairs A[HashPropertiesPair {Hash u32, TextOffset u32}], SortedDialogueLines
  `Text` is the LAST array in the data block (it ends exactly at the instance's end), and the
  sections after the data (instance table, type table, string-hash table, name table) hold no
  data-relative offsets.

Edit, in that layout:
  1. the new strings are appended to `Text` in place (NUL-terminated); old TextOffsets are unchanged;
  2. each language that gains a pair gets a NEW SortedPairs array after `Text`, the pair inserted at
     its ascending-hash position; the language's (offset, count) header is repointed to it (the old
     array stays as unreferenced bytes);
  3. the four trailing sections move by one 16-byte-aligned delta; header offsets, the instance
     size and the total size are fixed up.
An empty edit set writes the input unchanged (byte-identical).

Usage:
  python jc3strings_write.py IN OUT EDITS.json
EDITS.json: {"<hash>": {"<lang index 0-10 or code en/fr/...>": "text", ...}, ...}
A hash that already exists in a language is refused (this tool only adds).
Always write from the VANILLA patch-layer file with the full edit set in one pass: an output of this
tool is refused as input (its Text is no longer the last array), by design.
"""
from __future__ import annotations

import json
import struct
import sys

import jc3adf

LANG_ORDER = ["en", "fr", "de", "it", "es", "ru", "pl", "ja", "pt", "es-MX", "ar"]


def _align(n: int, a: int) -> int:
    return (n + a - 1) // a * a


def write(blob: bytes, edits: dict[int, dict[int, str]]) -> bytes:
    if not edits:
        return bytes(blob)
    adf = jc3adf.Adf(blob)
    if len(adf.instances) != 1 or adf.type_name(adf.instances[0]["type"]) != "StringLookup":
        raise SystemExit("not a single-instance StringLookup")
    inst = adf.instances[0]
    D, size = inst["offset"], inst["size"]
    lang_off, lang_n = struct.unpack_from("<QQ", blob, D + 0)
    text_off, text_n = struct.unpack_from("<QQ", blob, D + 16)
    if text_off + text_n != size:
        raise SystemExit(f"Text is not the last array in the data ({text_off}+{text_n} != {size})")
    hdr = list(struct.unpack_from("<11I", blob, 0))
    # header: magic, version, inst_n, inst_off, type_n, type_off, sh_n, sh_off, name_n, name_off, total
    tail_off = hdr[3]
    if not (D + size <= tail_off <= hdr[5] <= hdr[7] <= hdr[9] <= hdr[10] == len(blob)):
        raise SystemExit("unexpected section order after the data block")

    # 1) text: append, remember offsets
    text_add = bytearray()
    off_of: dict[tuple[int, int], int] = {}
    for h in sorted(edits):
        for lang in sorted(edits[h]):
            off_of[(h, lang)] = text_n + len(text_add)
            text_add += edits[h][lang].encode("utf-8") + b"\x00"
    new_text_n = text_n + len(text_add)

    # 2) new SortedPairs arrays, placed after the grown Text
    data = bytearray(blob[D:D + size]) + text_add
    langs_touched = sorted({lang for h in edits for lang in edits[h]})
    for lang in langs_touched:
        if not 0 <= lang < lang_n:
            raise SystemExit(f"language {lang} out of range 0..{lang_n - 1}")
        rec = lang_off + lang * 32
        p_off, p_n = struct.unpack_from("<QQ", data, rec)
        pairs = [struct.unpack_from("<II", data, p_off + 8 * i) for i in range(p_n)]
        hashes = [h for h, _ in pairs]
        if hashes != sorted(hashes):
            raise SystemExit(f"language {lang}: SortedPairs not ascending in the input")
        have = set(hashes)
        for h in edits:
            if lang in edits[h]:
                if h in have:
                    raise SystemExit(f"hash {h} already present in language {lang}")
                pairs.append((h, off_of[(h, lang)]))
        pairs.sort()
        while len(data) % 8:
            data.append(0)
        new_off = len(data)
        for h, o in pairs:
            data += struct.pack("<II", h, o)
        struct.pack_into("<QQ", data, rec, new_off, len(pairs))
    struct.pack_into("<QQ", data, 16, text_off, new_text_n)

    # 3) move the trailing sections by one aligned delta, fix the header and the instance record
    gap_old = tail_off - (D + size)
    new_tail = _align(D + len(data), 16)
    delta = new_tail - tail_off
    if delta % 16:
        raise SystemExit("internal: delta not 16-aligned")
    out = bytearray(blob[:D]) + data + b"\x00" * (new_tail - D - len(data)) + blob[tail_off:]
    for i in (3, 5, 7, 9):
        hdr[i] += delta
    hdr[10] = len(out)
    struct.pack_into("<11I", out, 0, *hdr)
    # instance record: name_hash, type_hash, offset, size, name_index - at the moved instance table
    struct.pack_into("<I", out, hdr[3] + 12, len(data))
    _ = gap_old
    return bytes(out)


def parse_edits(path: str) -> dict[int, dict[int, str]]:
    raw = json.load(open(path, encoding="utf-8"))
    out: dict[int, dict[int, str]] = {}
    for h, per in raw.items():
        d = {}
        for lang, text in per.items():
            li = LANG_ORDER.index(lang) if lang in LANG_ORDER else int(lang)
            d[li] = text
        out[int(h)] = d
    return out


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    src, dst, edits = sys.argv[1:]
    blob = open(src, "rb").read()
    res = write(blob, parse_edits(edits))
    open(dst, "wb").write(res)
    jc3adf.Adf(res)  # re-read
    print(f"wrote {dst}: {len(blob):,} -> {len(res):,} B")
    return 0


if __name__ == "__main__":
    sys.exit(main())

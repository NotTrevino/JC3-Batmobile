"""stringlookup_compare.py - compare two JC3 `.stringlookup` files by CONTENT (B-13a acceptance).

    python Tools/scripts/stringlookup_compare.py BEFORE AFTER

Prints: instance layout equal, language and pair counts, whether every pre-existing hash still
resolves to exactly its old text, whether each language's SortedPairs is ascending, whether the
SortedDialogueLines are untouched, and the hashes AFTER adds per language (with their text).
Exit 0 only if nothing pre-existing changed and every SortedPairs is ascending.
"""
import re
import sys

import jc3adf


def load(p):
    blob = open(p, "rb").read()
    adf = jc3adf.Adf(blob)
    text = bytearray(); order = {}; offs = {}; pend = {}; dlg = []
    for path, _t, v in jc3adf.walk(adf, 0):
        if path.startswith("Text["):
            text.append(v & 0xFF); continue
        if ".SortedDialogueLines" in path:
            dlg.append((path, v)); continue
        m = re.match(r"Languages\[(\d+)\]\.SortedPairs\[(\d+)\]\.(Hash|TextOffset)$", path)
        if not m:
            continue
        l, i, f = int(m[1]), int(m[2]), m[3]
        if f == "Hash":
            pend[(l, i)] = v; order.setdefault(l, []).append(v)
        else:
            offs.setdefault(l, {})[pend[(l, i)]] = v
    t = bytes(text)
    s = lambda o: t[o:t.find(b"\0", o)]
    strings = {l: {h: s(o) for h, o in offs[l].items()} for l in offs}
    return adf, strings, order, dlg


def main() -> int:
    a, sa, oa, da = load(sys.argv[1])
    b, sb, ob, db = load(sys.argv[2])
    lay = lambda x: [(i["name"], x.type_name(i["type"])) for i in x.instances]
    print("instances", lay(a) == lay(b))
    print("languages", len(sa), len(sb))
    print("pairs", sum(map(len, sa.values())), sum(map(len, sb.values())))
    pre = all(h in sb.get(l, {}) and sb[l][h] == v for l in sa for h, v in sa[l].items())
    print("preexisting strings equal", pre)
    asc = all(v == sorted(v) for v in ob.values())
    print("SortedPairs ascending", asc)
    print("dialogue lines equal", da == db)
    added = {l: {h: sb[l][h].decode("utf-8", "replace") for h in sorted(set(sb[l]) - set(sa.get(l, {})))}
             for l in sb}
    added = {l: v for l, v in added.items() if v}
    print("added hashes", {l: list(v) for l, v in added.items()})
    if added:
        print("added text", sorted({t for v in added.values() for t in v.values()}))
    return 0 if (pre and asc and da == db) else 1


if __name__ == "__main__":
    sys.exit(main())

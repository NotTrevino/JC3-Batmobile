"""G2-27 probe: does `global/entityregistry_gen.entityregc` list every entity, and is every
index `.ee` in it?  Structure: `03 <len16> <ascii>` string records interleaved with 32-bit hashes.
"""
import collections
import os
import re
import struct
import sys

sys.path.insert(0, r"E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts")
import jc3index  # noqa: E402

RAW = r"E:/Modding/JustCause3/_grab/standalone"
REG = {"base": os.path.join(RAW, "base_entityregistry_gen.entityregc"),
       "patch": os.path.join(RAW, "patch_entityregistry_gen.entityregc")}


def strings(blob):
    """Every `03 <len16> <bytes>` record, in file order."""
    out = []
    i, n = 0, len(blob)
    while True:
        i = blob.find(b"\x03", i)
        if i < 0 or i + 3 > n:
            break
        ln = struct.unpack_from("<H", blob, i + 1)[0]
        if 1 <= ln <= 512 and i + 3 + ln <= n:
            s = blob[i + 3:i + 3 + ln]
            if all(0x20 <= c < 0x7f for c in s):
                out.append((i, s.decode("latin-1")))
                i += 3 + ln
                continue
        i += 1
    return out


def main():
    rows = jc3index.load_index(jc3index.DEFAULT_OUT)
    ee = [r["path"] for r in rows if r["path"].endswith(".ee")]
    ee_leaves = {}
    for p in ee:
        leaf = p.rsplit("/", 1)[-1][:-3]
        ee_leaves.setdefault(leaf, []).append(p)
    print(f"index .ee files {len(ee)}, distinct leaves {len(ee_leaves)}")

    for mount, path in REG.items():
        blob = open(path, "rb").read()
        ss = strings(blob)
        leaf_like = [(o, s) for o, s in ss if "/" not in s and s in ee_leaves]
        paths = [(o, s) for o, s in ss if "/" in s]
        print(f"\n== {mount} {len(blob)} B: {len(ss)} tag-03 strings, "
              f"{len(leaf_like)} are index entity leaves, {len(paths)} contain '/'")
        found = {s for _, s in leaf_like}
        print(f"   distinct leaves {len(found)}, index leaves missing "
              f"{len(set(ee_leaves) - found)}")
        miss = sorted(set(ee_leaves) - found)
        print("   missing sample:", miss[:6])
        # how many of the whole index leaf set appear anywhere in the blob as ASCII
        raw = blob
        absent = [l for l in ee_leaves if l.encode() not in raw]
        print(f"   index leaves absent from the blob entirely: {len(absent)}",
              absent[:4])
        # record sentinel / hash adjacency for the donor
        donor = "v0300_car_kensington_sportsmuscle_civilian_01"
        hits = [o for o, s in ss if s == donor]
        print(f"   donor leaf records: {len(hits)}")
        if hits:
            o = hits[0]
            ln = struct.unpack_from("<H", blob, o + 1)[0]
            end = o + 3 + ln
            print(f"     at {o}, len {ln}, next 16 B {blob[end:end+16].hex()}")
            print(f"     prev 8 B {blob[o-8:o].hex()}")
        # tag census
        print("   tag-03 payload kinds:",
              collections.Counter(
                  "path" if "/" in s else "class" if s[:1] == "C" and s[1:2].isupper()
                  else "leaf" if s in ee_leaves else "other" for _, s in ss).most_common())


if __name__ == "__main__":
    main()

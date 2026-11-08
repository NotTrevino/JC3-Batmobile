#!/usr/bin/env python
"""hud_gfx_roundtrip.py -- compare JC3's ui/hud.gfx with FFDec round trip / text-edit copies.

Reads three CFX (compressed ScaleForm GFx) files and parses the tag stream itself, so every
number is recomputed from the source bytes:

    orig  the extracted patch hud.gfx                     (input, read-only)
    rt    FFDec -swf2xml then -xml2swf, no edit           (no-edit round trip)
    p3    FFDec -replace 401 <text> on orig               (the P3 probe payload)

  python Tools/scripts/hud_gfx_roundtrip.py --write   # writes Working/HUD_GFX_ROUNDTRIP.json
  python Tools/scripts/hud_gfx_roundtrip.py --check   # recomputes and diffs against that JSON

No game file is touched: the three inputs live in a scratch folder outside the repo.
"""
import argparse
import hashlib
import json
import os
import struct
import sys
import zlib

SCRATCH = "E:/Modding/_JC3grab/hud_roundtrip"
OUT = "Working/HUD_GFX_ROUNDTRIP.json"
# The payload edits this DefineEditText (chid 2241 'VEHICLE', TXT_label in MCI_life_bar_with_text).
EXPECT_TEXT_CHID = 2241

TAG_NAMES = {
    0: "End", 1: "ShowFrame", 2: "DefineShape", 4: "PlaceObject", 5: "RemoveObject",
    6: "DefineBits", 7: "DefineButton", 8: "JPEGTables", 9: "SetBackgroundColor",
    10: "DefineFont", 11: "DefineText", 12: "DoAction", 13: "DefineFontInfo",
    14: "DefineSound", 15: "StartSound", 17: "DefineButtonSound", 18: "SoundStreamHead",
    19: "SoundStreamBlock", 20: "DefineBitsLossless", 21: "DefineBitsJPEG2",
    22: "DefineShape2", 23: "DefineButtonCxform", 24: "Protect", 26: "PlaceObject2",
    28: "RemoveObject2", 32: "DefineShape3", 33: "DefineText2", 34: "DefineButton2",
    35: "DefineBitsJPEG3", 36: "DefineBitsLossless2", 37: "DefineEditText",
    39: "DefineSprite", 43: "FrameLabel", 45: "SoundStreamHead2", 46: "DefineMorphShape",
    48: "DefineFont2", 56: "ExportAssets", 57: "ImportAssets", 58: "EnableDebugger",
    59: "DoInitAction", 60: "DefineVideoStream", 61: "VideoFrame", 62: "DefineFontInfo2",
    65: "ScriptLimits", 66: "SetTabIndex", 69: "FileAttributes", 70: "PlaceObject3",
    71: "ImportAssets2", 73: "DefineFontAlignZones", 74: "CSMTextSettings",
    75: "DefineFont3", 76: "SymbolClass", 77: "Metadata", 78: "DefineScalingGrid",
    82: "DoABC", 83: "DefineShape4", 84: "DefineMorphShape2", 86: "DefineSceneAndFrameLabelData",
    87: "DefineBinaryData", 88: "DefineFontName", 89: "StartSound2", 90: "DefineBitsJPEG4",
    91: "DefineFont4",
}
# ScaleForm GFx extensions seen in JC3/modern Scaleform movies.
for _i, _n in ((1000, "GFx ExporterInfo"), (1001, "GFx DefineExternalImage"),
               (1002, "GFx DefineText"), (1003, "GFx DefineFontCompressed"),
               (1004, "GFx VideoFrame"), (1005, "GFx DefineExternalImage2")):
    TAG_NAMES.setdefault(_i, _n)


class Bits(object):
    def __init__(self, data, pos):
        self.d = data
        self.p = pos * 8
        self.bit = 0

    def read(self, n):
        v = 0
        for _ in range(n):
            byte = self.d[self.p >> 3]
            v = (v << 1) | ((byte >> (7 - (self.p & 7))) & 1)
            self.p += 1
        return v

    def align(self):
        self.p = (self.p + 7) // 8 * 8


def parse_container(raw):
    """CFX/CWS/FWS header -> (sig, version, declared length, decompressed body)."""
    sig = raw[0:3].decode("ascii")
    version = raw[3]
    declared = struct.unpack("<I", raw[4:8])[0]
    if sig == "CFX":
        body = zlib.decompressobj().decompress(raw[8:])
    elif sig == "CWS":
        body = zlib.decompressobj().decompress(raw[8:])
    else:
        body = raw[8:]
    return sig, version, declared, body


def parse_tags(body):
    """body -> (frame_rect_nbits, frame_rate_fixed, frame_count, [(tagid, body_bytes, offset)])"""
    br = Bits(body, 0)
    nbits = br.read(5)
    rect = [br.read(nbits) for _ in range(4)]
    br.align()
    pos = br.p // 8
    frame_rate = struct.unpack("<H", body[pos:pos + 2])[0]
    frame_count = struct.unpack("<H", body[pos + 2:pos + 4])[0]
    pos += 4
    tags = []
    while pos + 2 <= len(body):
        code = struct.unpack("<H", body[pos:pos + 2])[0]
        tagid, length = code >> 6, code & 0x3F
        start = pos
        pos += 2
        if length == 0x3F:
            length = struct.unpack("<I", body[pos:pos + 4])[0]
            pos += 4
        payload = body[pos:pos + length]
        pos += length
        tags.append((tagid, payload, start))
        if tagid == 0:
            break
    return nbits, rect, frame_rate, frame_count, tags, len(body) - pos


def describe(path):
    raw = open(path, "rb").read()
    sig, version, declared, body = parse_container(raw)
    nbits, rect, fr, fc, tags, tail = parse_tags(body)
    return {
        "path": path,
        "file": os.path.basename(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "size_on_disk": len(raw),
        "signature": sig,
        "version": version,
        "declared_length": declared,
        "decompressed_length": len(body),
        "frame_rect_nbits": nbits,
        "frame_rect_twips": rect,
        "frame_rate_fixed": fr,
        "frame_count": fc,
        "tag_count": len(tags),
        "tag_ids": [t[0] for t in tags],
        "lengths": [len(t[1]) for t in tags],
        "bodies": [t[1] for t in tags],
        "trailing_bytes": tail,
    }


def compare(a, b, label):
    """Compare two parsed movies tag by tag (same index)."""
    same_ids = a["tag_ids"] == b["tag_ids"]
    id_diff = [(i, x, y) for i, (x, y) in enumerate(zip(a["tag_ids"], b["tag_ids"])) if x != y]
    len_diff = []
    body_diff = {}
    for i, (ta, tb) in enumerate(zip(a["bodies"], b["bodies"])):
        la, lb = len(ta), len(tb)
        if la != lb:
            len_diff.append({"index": i, "tagId": a["tag_ids"][i],
                             "name": TAG_NAMES.get(a["tag_ids"][i], "tag%d" % a["tag_ids"][i]),
                             "from_len": la, "to_len": lb})
        elif ta != tb:
            nm = TAG_NAMES.get(a["tag_ids"][i], "tag%d" % a["tag_ids"][i])
            body_diff[nm] = body_diff.get(nm, 0) + 1
    return {
        "pair": label,
        "tag_counts": [a["tag_count"], b["tag_count"]],
        "tag_id_sequence_identical": same_ids,
        "tag_id_diffs": id_diff[:20],
        "length_diffs": len(len_diff),
        "length_diff_deltas": sorted({d["to_len"] - d["from_len"] for d in len_diff}),
        "length_diff_by_name": _by_name(len_diff, "name"),
        "body_diffs_same_length": sum(body_diff.values()),
        "body_diffs_by_name": body_diff,
        "frames_equal": a["frame_count"] == b["frame_count"],
        "frame_rate_equal": a["frame_rate_fixed"] == b["frame_rate_fixed"],
        "rect_equal": a["frame_rect_twips"] == b["frame_rect_twips"],
        "decompressed_length_delta": b["decompressed_length"] - a["decompressed_length"],
        "size_on_disk_delta": b["size_on_disk"] - a["size_on_disk"],
    }


def _by_name(rows, key):
    out = {}
    for r in rows:
        out[r[key]] = out.get(r[key], 0) + 1
    return out


def edit_report(orig, p3, chid_expect=401):
    """Which tags differ between the original and the P3 payload, and is it just the text tag?"""
    rows = []
    for i, (ta, tb) in enumerate(zip(orig["bodies"], p3["bodies"])):
        if ta != tb:
            rows.append({"index": i, "tagId": orig["tag_ids"][i],
                         "name": TAG_NAMES.get(orig["tag_ids"][i], "tag%d" % orig["tag_ids"][i]),
                         "from_len": len(ta), "to_len": len(tb)})
    return {
        "pair": "orig->p3",
        "differing_tags": len(rows),
        "rows": rows[:20],
        "only_text_tag": len(rows) == 1 and rows[0]["tagId"] == 37,
        "text_tag_index": rows[0]["index"] if rows else None,
        "tag_counts": [orig["tag_count"], p3["tag_count"]],
    }


def build():
    orig = describe(os.path.join(SCRATCH, "orig.gfx"))
    rt = describe(os.path.join(SCRATCH, "rt.gfx"))
    p3 = describe(os.path.join(SCRATCH, "p3_candidate.gfx"))
    result = {
        "inputs": {k: {kk: v[kk] for kk in ("path", "file", "sha256", "size_on_disk",
                                           "signature", "version", "declared_length",
                                           "decompressed_length", "frame_rect_nbits",
                                           "frame_rect_twips", "frame_rate_fixed",
                                           "frame_count", "tag_count", "trailing_bytes")}
                   for k, v in (("orig", orig), ("rt", rt), ("p3", p3))},
        "tag_census": _census(orig),
        "roundtrip": compare(orig, rt, "orig->rt"),
        "payload_vs_roundtrip": compare(rt, p3, "rt->p3"),
        "edit": edit_report(orig, p3, EXPECT_TEXT_CHID),
        "unknown_tag_ids": sorted({t for t in orig["tag_ids"] if t not in TAG_NAMES}),
        "container": {
            "trailing_bytes_orig": orig["trailing_bytes"],
            "trailing_bytes_rt": rt["trailing_bytes"],
            "trailing_bytes_p3": p3["trailing_bytes"],
            "declared_minus_decompressed_orig": orig["declared_length"] - orig["decompressed_length"],
            "declared_minus_decompressed_rt": rt["declared_length"] - rt["decompressed_length"],
            "declared_minus_decompressed_p3": p3["declared_length"] - p3["decompressed_length"],
        },
    }
    return result


def _census(m):
    out = {}
    for t in m["tag_ids"]:
        nm = TAG_NAMES.get(t, "tag%d" % t)
        out[nm] = out.get(nm, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: -kv[1]))


LAYOUT_PREFIXES = ("DefineShape", "DefineSprite")


def is_layout_tag(name):
    """Only shape/sprite layout tags may drift: their records are bit-packed and re-serialised."""
    return name.startswith(LAYOUT_PREFIXES)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")
    for name in ("orig.gfx", "rt.gfx", "p3_candidate.gfx"):
        p = os.path.join(SCRATCH, name)
        if not os.path.exists(p):
            print("MISSING input: %s" % p)
            return 2
    result = build()
    if args.write:
        os.makedirs(os.path.dirname(OUT), exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1, sort_keys=True)
            fh.write("\n")
        print("wrote %s" % OUT)

    problems = []
    if args.check:
        if not os.path.exists(OUT):
            print("FAIL no %s to check against (run --write first)" % OUT)
            return 1
        ref = json.load(open(OUT, encoding="utf-8"))
        if ref != result:
            problems.append("recomputed result differs from %s" % OUT)
        rt = result["roundtrip"]
        ed = result["edit"]
        if not rt["tag_id_sequence_identical"]:
            problems.append("round trip changed the tag id sequence")
        if rt["tag_counts"][0] != rt["tag_counts"][1]:
            problems.append("round trip changed the tag count")
        drift = set(rt["body_diffs_by_name"]) | set(rt["length_diff_by_name"])
        outside = sorted(n for n in drift if not is_layout_tag(n))
        if outside:
            problems.append("round trip changed tags that carry code, text, fonts or assets: %s"
                            % ", ".join(outside))
        if not rt["body_diffs_by_name"] and not rt["length_diff_by_name"]:
            problems.append("round trip reported no shape drift at all -- parser or inputs suspect")
        if not ed["only_text_tag"]:
            problems.append("payload differs from the original in something other than one text tag")
        if ed["tag_counts"][0] != ed["tag_counts"][1]:
            problems.append("payload changed the tag count")
        if result["inputs"]["orig"]["signature"] != "CFX":
            problems.append("original is not a compressed GFx movie")

    c = result["container"]
    if c["trailing_bytes_orig"] and not c["trailing_bytes_rt"]:
        print("WARN original carries %d undeclared trailing bytes that FFDec drops"
              % c["trailing_bytes_orig"])
    print(json.dumps({
        "sizes": {k: v["size_on_disk"] for k, v in result["inputs"].items()},
        "sha256": {k: v["sha256"][:16] for k, v in result["inputs"].items()},
        "tags": {k: v["tag_count"] for k, v in result["inputs"].items()},
        "rt_len_diffs": result["roundtrip"]["length_diffs"],
        "rt_len_deltas": result["roundtrip"]["length_diff_deltas"],
        "rt_body_diffs": result["roundtrip"]["body_diffs_same_length"],
        "rt_ids_same": result["roundtrip"]["tag_id_sequence_identical"],
        "edit_diffs": result["edit"]["differing_tags"],
        "edit_only_text": result["edit"]["only_text_tag"],
        "unknown_tag_ids": result["unknown_tag_ids"],
    }, indent=1, sort_keys=True))
    if problems:
        for p in problems:
            print("FAIL " + p)
        return 1
    print("CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

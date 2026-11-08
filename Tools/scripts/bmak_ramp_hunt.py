"""bmak_ramp_hunt.py - the BmAK colour-ramp textures, extracted to pixels.

Rule D10 says the BmAK ramp files are "missing on disk".  They are not: each ramp is a
`Texture2D` export whose mip 0 lives in a `.tfc` chunk stream.  This tool proves where
each one lives and what it contains.

Chain, each step read from the install:

  1. package name table -> export named e.g. `Batman_BM3_V2_Leather_Ramp`
  2. export property tags -> SizeX, SizeY, Format (PF_*), TextureFileCacheName (Chunk0..8)
  3. the mip-0 record in the export payload: 16 bytes before the SizeX/SizeY pair,
     `{sizeOnDisk, storedBytes, tfcOffset, 0, sizeX, sizeY, flags}`.  Accepted only if
     sizeOnDisk == the format's byte size for those dims AND the cache bytes at
     `tfcOffset` begin with the UE3 package tag (c1 83 2a 9e).
  4. the cache chunk at `tfcOffset` is a zlib sub-block list -> `upk_read._dechunk`
  5. PF_DXT1 / PF_BC5 decoded to RGB with numpy
  6. a CSV profile: mean over x for every row (a colour ramp varies along one axis only)

Nothing here is hand-typed from a reference: every value is the file's.  `--check`
re-derives and fails on drift.

Usage:
    python Tools/scripts/bmak_ramp_hunt.py            # write Working/Ramp/ramps.json + PNGs
    python Tools/scripts/bmak_ramp_hunt.py --check    # re-derive, compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read  # noqa: E402

CK = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OUT = os.path.join(ROOT, "Working", "Ramp")

# packages that export a ramp Texture2D (found by bmak_ramp_sweep.py)
TARGETS = {
    "Playable_Batmobile_SF": ["Batman_BM3_V2_Leather_Ramp"],
    "Showcase_Batmobiles_Standard": ["Batman_BM3_V2_Leather_Ramp"],
}
# names the Batmobile materials bind that are NOT local exports: the import's outer names
# the package that would carry them, so the report can say where they are supposed to live.
IMPORTS = {
    "Playable_Batmobile_SF": ["Batman_BM3_V2_Lacquered_Underlayer_Ramp",
                              "Batmobile_V3_Body_ColourRamp"],
}
BPP = {"PF_DXT1": 0.5, "PF_BC5": 1.0, "PF_BC4": 0.5, "PF_DXT5": 1.0}


# ---------------- codecs ----------------

def dxt1(blob, w, h):
    a = np.frombuffer(blob[: (w * h) // 2], dtype=np.uint8).reshape(-1, 8)
    c0 = a[:, 0].astype(np.uint16) | (a[:, 1].astype(np.uint16) << 8)
    c1 = a[:, 2].astype(np.uint16) | (a[:, 3].astype(np.uint16) << 8)
    idx = np.frombuffer(np.ascontiguousarray(a[:, 4:8]).tobytes(), dtype=np.uint32).reshape(-1)

    def ex(c):
        return np.stack([((c >> 11) & 31) * 255 // 31,
                         ((c >> 5) & 63) * 255 // 63,
                         (c & 31) * 255 // 31], 1).astype(np.float32)

    e0, e1 = ex(c0), ex(c1)
    pal = np.zeros((len(c0), 4, 3), np.float32)
    pal[:, 0], pal[:, 1] = e0, e1
    pal[:, 2], pal[:, 3] = (2 * e0 + e1) / 3, (e0 + 2 * e1) / 3
    m = c0 <= c1                                  # 3-colour + transparent-black mode
    pal[m, 2] = (e0[m] + e1[m]) / 2
    pal[m, 3] = 0
    sel = np.stack([(idx >> (2 * k)) & 3 for k in range(16)], 1)
    px = np.take_along_axis(pal, np.repeat(sel[:, :, None], 3, 2), 1)
    return px.reshape(h // 4, w // 4, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(h, w, 3)


def bc5(blob, w, h):
    """Two BC4 blocks (R, G) per 4x4; B is reconstructed as sqrt(1 - r^2 - g^2)."""
    a = np.frombuffer(blob[: w * h], dtype=np.uint8).reshape(-1, 16)
    out = []
    for ch in (0, 8):
        e0, e1 = a[:, ch].astype(np.float32), a[:, ch + 1].astype(np.float32)
        bits = np.frombuffer(np.ascontiguousarray(a[:, ch + 2:ch + 8]).tobytes(),
                             dtype=np.uint64).reshape(-1)
        pal = np.zeros((len(a), 8), np.float32)
        pal[:, 0], pal[:, 1] = e0, e1
        big = e0 > e1
        for i in range(2, 8):
            t = (i - 1) / 7.0
            pal[big, i] = e0[big] * (1 - t) + e1[big] * t
        for i in range(2, 6):
            t = (i - 1) / 5.0
            pal[~big, i] = e0[~big] * (1 - t) + e1[~big] * t
        pal[~big, 6] = 0
        pal[~big, 7] = 255
        sel = np.stack([((bits >> np.uint64(3 * k)) & np.uint64(7)).astype(np.int64)
                        for k in range(16)], 1)
        out.append(np.take_along_axis(pal, sel, 1))
    r, g = out
    b = np.sqrt(np.clip(1.0 - (r / 255.0) ** 2 - (g / 255.0) ** 2, 0, 1)) * 255
    px = np.stack([r, g, b], 2)
    return px.reshape(h // 4, w // 4, 4, 4, 3).transpose(0, 2, 1, 3, 4).reshape(h, w, 3)


DECODE = {"PF_DXT1": dxt1, "PF_BC5": bc5}


# ---------------- extraction ----------------

def tags_of(pkg, idx):
    tags, _end, _why = upk_read.walk_tags(pkg, pkg.data(idx))
    ints = [t["value"] for t in tags if t["type"] == "IntProperty"]
    fmt = next((t.get("value") for t in tags if t.get("name") == "Format"), None)
    cache = next((t.get("value") for t in tags if t["type"] == "NameProperty"), None)
    return ints, fmt, cache


def mip0(pkg, idx):
    d = pkg.data(idx)
    ints, fmt, cache = tags_of(pkg, idx)
    w, h = ints[0], ints[1]
    u = lambda o: struct.unpack_from("<I", d, o)[0]  # noqa: E731
    want = int(w * h * BPP[fmt])
    hits = []
    for o in range(16, len(d) - 8):
        if u(o) != w or u(o + 4) != h:
            continue
        size, stored, off = u(o - 16), u(o - 12), u(o - 8)
        if size != want:
            continue
        path = os.path.join(CK, cache + ".tfc")
        with open(path, "rb") as f:
            f.seek(off)
            head = f.read(4)
            if head != upk_read.PKG_TAG:
                continue
            f.seek(off)
            blob = f.read(stored)
        raw, _ = upk_read._dechunk(blob, 0)
        if len(raw) < size:
            continue
        hits.append({"record_at": o, "size_on_disk": size, "stored_bytes": stored,
                     "tfc": cache, "tfc_offset": off, "raw_bytes": len(raw)})
    if not hits:
        return None, {"w": w, "h": h, "format": fmt, "cache": cache,
                      "note": "no mip-0 record passed the oracle"}
    rec = dict(hits[0], w=w, h=h, format=fmt, cache=cache)
    raw, _ = upk_read._dechunk(open(os.path.join(CK, cache + ".tfc"), "rb").read()
                               [rec["tfc_offset"]:rec["tfc_offset"] + rec["stored_bytes"]], 0)
    img = DECODE[fmt](raw, w, h)
    rec["records_found"] = len(hits)
    return img, rec


def to_linear(c):
    v = c / 255.0
    return v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4


def profile(img):
    mean = img.mean(axis=1)                       # (h, 3)
    h = img.shape[0]
    rows = [0, 1, 2, h // 8, h // 4, h // 2, (3 * h) // 4, (7 * h) // 8, h - 2, h - 1]
    return {
        "linear_at_rows": [{"row": int(r),
                            "linear": [round(float(to_linear(v)), 5) for v in mean[r]]}
                           for r in rows],
        "x_mean_variation": float(np.abs(np.diff(img, axis=1)).mean()),
        "y_mean_variation": float(np.abs(np.diff(img, axis=0)).mean()),
        "rows": [{"row": int(r), "rgb": [int(round(v)) for v in mean[r]]} for r in rows],
        "column_mean_min": [int(round(v)) for v in mean.min(0)],
        "column_mean_max": [int(round(v)) for v in mean.max(0)],
        "unique_rows": int(len(np.unique(np.round(mean, 0), axis=0))),
    }


def run(check):
    out = {"imports": {}}
    for pkgname, names in IMPORTS.items():
        path = os.path.join(CK, pkgname + ".upk")
        if not os.path.exists(path):
            out["imports"][pkgname] = {"missing_package": path}
            continue
        pkg = upk_read.Package(path)
        for name in names:
            idx = pkg.find(name)
            row = {"export": idx}
            if idx and idx < 0:
                imp = pkg.imports[-idx - 1]
                row.update({"imported": True, "class": imp["class_name"],
                            "outer_package": pkg.object_path(imp["outer"]),
                            "candidate_file": os.path.join(CK, (pkg.object_path(imp["outer"]) or "").split(".")[-1] + ".upk"),
                            "candidate_on_disk": None})
                outer = (pkg.object_path(imp["outer"]) or "").split(".")[-1]
                row["candidate_on_disk"] = bool(outer) and os.path.exists(os.path.join(CK, outer + ".upk"))
            out["imports"][name] = dict(row, package=pkgname)
    for pkgname, names in TARGETS.items():
        path = os.path.join(CK, pkgname + ".upk")
        if not os.path.exists(path):
            out[pkgname] = {"missing_package": path}
            continue
        pkg = upk_read.Package(path)
        for name in names:
            idx = pkg.find(name)
            if not idx or idx < 0:
                out[name] = {"package": pkgname, "export": idx,
                             "note": "not a local export (import only)" if idx else "not found"}
                continue
            img, rec = mip0(pkg, idx)
            row = {"package": pkgname, "export": idx, "class": pkg.object_class(idx),
                   "record": rec}
            if img is not None:
                row.update({"w": img.shape[1], "h": img.shape[0],
                            "profile": profile(img)})
                os.makedirs(OUT, exist_ok=True)
                png = Image.fromarray(img.astype(np.uint8))
                png = png.resize((img.shape[1] * 4, img.shape[0]), Image.NEAREST)
                png.save(os.path.join(OUT, name.replace(".", "_") + ".png"))
            out["%s::%s" % (pkgname, name)] = dict(row, name=name)
    if check:
        old = json.load(open(os.path.join(OUT, "ramps.json")))
        same = old == out
        print("CHECK:", "match" if same else "DRIFT")
        if not same:
            for k in out:
                if old.get(k) != out[k]:
                    print("  differs:", k)
        return 0 if same else 1
    os.makedirs(OUT, exist_ok=True)
    json.dump(out, open(os.path.join(OUT, "ramps.json"), "w"), indent=1)
    for name, row in out.get("imports", {}).items():
        print("== IMPORT", name, row.get("package"), "export", row.get("export"),
              "outer", row.get("outer_package"), "candidate on disk:", row.get("candidate_on_disk"))
    for name, row in out.items():
        if name == "imports":
            continue
        print("==", name, "export", row.get("export"), row.get("class"))
        rec = row.get("record") or {}
        print("   dims %sx%s fmt %s cache %s" % (rec.get("w"), rec.get("h"),
                                                 rec.get("format"), rec.get("cache")))
        if row.get("profile"):
            p = row["profile"]
            print("   x-var %.3f y-var %.3f unique rows %d" %
                  (p["x_mean_variation"], p["y_mean_variation"], p["unique_rows"]))
            print("   rows:", [(r["row"], r["rgb"]) for r in p["rows"]])
        else:
            print("   ", rec.get("note"))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    sys.exit(run(ap.parse_args().check))

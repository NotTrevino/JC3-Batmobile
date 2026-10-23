"""palette_black.py - repaint every tint of a vehicle palette .vmodc, in place. MODLOG §55.

The Serpente's paint comes from editor/.../modules/default/v0300_car_kensington_sportsmuscle_palette.vmodc
(ADF, read from the .ee: its .toc record is internal). It holds 10 Tint records (White, Evergreen
Pearl, Garnet Red Metallic, Black, Grey, Silver, Blue, Brown, Red, Green) with tint_r/g/b ColorRGBA,
occurrence (spawn weight), specular_gloss, metallic, clear_coat.

Offsets come from Gibbed ConvertAdf's export (`offset-in-file`), so only float bytes change: same
size, no ADF writer involved. Occurrence weights are kept.

Usage: python palette_black.py <palette.vmodc> <palette.xml from ConvertAdf --e> -o <out.vmodc>
       [--rgb 0.05] [--gloss 0.45] [--metallic 1] [--coat 1]
"""
import argparse
import struct
import xml.etree.ElementTree as ET


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("vmodc")
    ap.add_argument("xml")
    ap.add_argument("-o", required=True)
    ap.add_argument("--rgb", type=float, default=0.05)
    ap.add_argument("--gloss", type=float, default=0.45)
    ap.add_argument("--metallic", type=float, default=1.0)
    ap.add_argument("--coat", type=float, default=1.0)
    a = ap.parse_args()

    b = bytearray(open(a.vmodc, "rb").read())
    root = ET.parse(a.xml).getroot()
    n = 0
    for t in root.iter("member"):
        if t.get("type") != "Tint":
            continue
        n += 1
        for m in t.iter("member"):
            off = m.get("offset-in-file")
            if off is None or m.get("type") != "float":
                continue
            off, name = int(off, 16), m.get("name")
            if name in ("R", "G", "B"):
                v = a.rgb
            elif name == "A":
                v = 1.0
            elif name == "specular_gloss":
                v = a.gloss
            elif name == "metallic":
                v = a.metallic
            elif name == "clear_coat":
                v = a.coat
            else:
                continue
            old = struct.unpack_from("<f", b, off)[0]
            if abs(old - float(m.text)) > 1e-5:
                raise SystemExit(f"offset {off:#x} holds {old}, xml says {m.text}: wrong xml for this file")
            struct.pack_into("<f", b, off, v)
    if n == 0:
        raise SystemExit("no Tint records found")
    open(a.o, "wb").write(bytes(b))
    print(f"repainted {n} tints -> rgb {a.rgb} gloss {a.gloss} metallic {a.metallic} coat {a.coat}; "
          f"{len(b)} B (same size)")


if __name__ == "__main__":
    main()

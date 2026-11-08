"""t_paint_gaps.py - verify the anchors of the paint-gaps closest-system plan.

The plan `tmp/freebuff/reports/paint-gaps-closest-system-plan.md` routes four BmAK
parameters (reflectivity, wet, edge wear, anisotropy) to JC3 carriers and quotes
numbers from the BmAK decode, the current build and the shader headers.  This
checker re-reads those sources and redoes the arithmetic; it does not bake, build
or touch the game data.

Usage:
  python Tools/scripts/t_paint_gaps.py --check
"""
from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "paint-gaps-closest-system-plan.md")
VALUES = os.path.join(ROOT, "Research", "BatmobileGrab", "VALUES.json")
FACTORS = os.path.join(ROOT, "Working", "Appearance", "build_bud1", "factors.json")
FACTORS_PY = os.path.join(ROOT, "Tools", "scripts", "factors.py")
ASSEMBLE = os.path.join(ROOT, "Tools", "scripts", "bat_assemble.py")

F0_D = 0.04          # project convention, not decoded (see the report)
CAP = 0.40           # VALUES.json paint.gloss_cap (the donor palette ships 0.45)


def srgb_byte(c: float) -> int:
    s = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return round(s * 255)


def f0(m: float, albedo: float) -> float:
    return F0_D * (1.0 - m) + albedo * m


def main() -> int:
    fails: list[str] = []
    ok: list[str] = []

    def check(name: str, cond: bool, detail: str = "") -> None:
        (ok if cond else fails).append(f"{name}{(': ' + detail) if detail else ''}")

    # ---------------------------------------------------------------- report
    if not os.path.isfile(REPORT):
        print(f"FAIL missing report {REPORT}")
        return 1
    md = open(REPORT, encoding="utf-8").read()
    for head in ("## 3. Reflectivity", "## 4. Wet", "## 5. Edge wear", "## 6. Anisotropic"):
        check(f"section present {head!r}", head in md)
    for token in ("0.0320", "0.0128", "0.8875", "0.985", "0.97", "0.75", "0.45", "4,593.6", "54.4"):
        check(f"quote present {token}", token in md)

    # ------------------------------------------------------------ BmAK values
    v = json.load(open(VALUES, encoding="utf-8"))
    base = [round(x, 5) for x in v["paint"]["base_colour"][:3]]
    check("base colour decoded", base == [0.02579, 0.02579, 0.03], str(base))
    check("authored gloss 0.6", abs(v["paint"]["authored_gloss"] - 0.6) < 1e-9,
          str(v["paint"]["authored_gloss"]))
    check("gloss cap 0.40", abs(v["paint"]["gloss_cap"] - CAP) < 1e-9,
          str(v["paint"]["gloss_cap"]))
    pal = os.path.join(ROOT, "Working", "Palette", "serpente_palette.xml")
    if os.path.isfile(pal):
        import re
        gl = re.findall(r'name="specular_gloss"[^>]*>([0-9.]+)</member>',
                        open(pal, encoding="utf-8", errors="replace").read())
        vals = [round(float(x), 2) for x in gl]
        check("donor palette ships 0.45", vals.count(0.45) == 8, f"{vals.count(0.45)} of {len(vals)}")

    # ------------------------------------------------------------ sRGB bytes
    for lin, byte in ((0.025787, 45), (0.036, 53), (0.02, 39), (0.1, 89), (0.65, 211)):
        got = srgb_byte(lin)
        check(f"sRGB {lin} -> {byte}", got == byte, str(got))

    # -------------------------------------------------------------- F0 table
    rows = [
        # name, R, metallic, albedo, achieved
        ("ch0 dry", 0.20, 0.0, 0.025787, f0(0.0, 0.025787)),
        ("ch2 metal", 0.90, 1.0, 0.036, f0(1.0, 0.036)),
        ("ch3 clear", 0.50, 1.0, 0.020, f0(1.0, 0.020)),
        ("MK2", 0.50, 0.0, 0.5, f0(0.0, 0.5)),
        ("wet ch0", 0.32, 0.0, 0.025787, f0(0.0, 0.025787)),
    ]
    expect = {"ch0 dry": (0.008, 0.032), "ch2 metal": (0.036, 0.0),
              "ch3 clear": (0.020, 0.0), "MK2": (0.020, 0.020),
              "wet ch0": (0.0128, 0.0272)}
    for name, r, m, alb, got in rows:
        target, err = expect[name]
        check(f"{name} target F0 = 0.04*R", abs(F0_D * r - target) < 1e-9,
              f"{F0_D * r:.4f} vs {target}")
        check(f"{name} achieved F0", abs(got - (target + err)) < 1e-6,
              f"{got:.4f} vs {target + err:.4f}")
    check("wet reflectivity 0.2*1.6", abs(0.2 * 1.6 - 0.32) < 1e-9)
    check("wet roughness 0.4*0.75", abs(0.4 * 0.75 - 0.30) < 1e-9)
    check("wet gloss 0.70", abs((1 - 0.4 * 0.75) - 0.70) < 1e-9)
    check("wet ch2 gloss 0.8875", abs((1 - 0.15 * 0.75) - 0.8875) < 1e-9)
    check("wet ch3 gloss 0.985", abs((1 - 0.02 * 0.75) - 0.985) < 1e-9)
    check("aniso broad contrast 0.51", abs((0.972 - 0.462) - 0.51) < 1e-9)
    check("aniso thin contrast 0.134", abs((0.33 - 0.196) - 0.134) < 1e-9)

    # ----------------------------------------------------------- build state
    f = json.load(open(FACTORS, encoding="utf-8"))
    body = f["materials"]["Batmobile_V3_Mainbody_NEW_MIC"]
    check("body gloss 0.4", body["inputs"]["static.SpecularGloss"]["value"] == [0.4] * 4)
    check("body metallic [0,0,1,0]",
          body["inputs"]["static.Metallic"]["value"] == [0.0, 0.0, 1.0, 0.0],
          str(body["inputs"]["static.Metallic"]["value"]))
    check("body clearcoat 0", body["inputs"]["static.ClearCoat"]["value"] == [0.0] * 4)
    for slot in ("s2", "s3"):
        src = body["textures"][slot]
        check(f"body {slot} dummy", src.get("vanilla", "").endswith("a00_dummy_black_mpm.ddsc"),
              str(src)[:80])

    ddsc = glob.glob(os.path.join(ROOT, "Working", "Appearance", "build_bud1", "**", "*.ddsc"),
                     recursive=True)
    kb = sum(os.path.getsize(p) for p in ddsc) / 1024
    check("28 textures", len(ddsc) == 28, str(len(ddsc)))
    check("texture total 3953.6 KB", abs(kb - 3953.6) < 1.0, f"{kb:.1f}")
    check("budget 4593.6", abs((kb + 128 + 512) - 4593.6) < 1.5, f"{kb + 640:.1f}")
    check("free 54.4", abs((4648 - (kb + 640)) - 54.4) < 1.5)

    # ------------------------------------------------------------ write path
    fps = open(FACTORS_PY, encoding="utf-8").read()
    asm = open(ASSEMBLE, encoding="utf-8").read()
    check("factors.py clamps gloss", "min(g, GLOSS_CAP)" in fps)
    check("bat_assemble packs 72 floats", 'struct.pack("<72f"' in asm)

    for line in ok:
        print("PASS", line)
    for line in fails:
        print("FAIL", line)
    print(f"\n{len(ok)} passed, {len(fails)} failed")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

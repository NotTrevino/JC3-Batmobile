"""v02b_lights_check.py - the RC4 lights module: 24 rows, the 70-degree headlights, the .toc record and
the 24 CarLight blocks over the 8 lamp parts. Read-only.

    python Tools/scripts/v02b_lights_check.py
"""
from __future__ import annotations

import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bm_lightrig as L  # noqa: E402
import bm_rc4_lights as RL  # noqa: E402
from eetoc import read_toc, sarc_dir, unaaf  # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC4")
A = os.path.join(RC, "aaf")
OUT = os.path.join(RC, "verify", "v02b")


def main() -> int:
    mod = os.path.join(A, L.MODULE.replace("/", os.sep))
    if not os.path.exists(mod):
        print("FAIL module missing:", mod)
        return 1
    raw = open(mod, "rb").read()
    rows = L.decode_module_bytes(raw)

    ee = os.path.join(A, L.EE)
    if not os.path.exists(ee):
        cand = glob.glob(os.path.join(A, "*.ee"))
        print("note: expected .ee", L.EE, "found", [os.path.basename(c) for c in cand][:4])
        ee = cand[0] if cand else None
    rec = None
    if ee and os.path.exists(ee + ".toc"):
        recs = read_toc(open(ee + ".toc", "rb").read())
        real = {n: (o, s) for n, o, s in sarc_dir(unaaf(open(ee, "rb").read()))}
        hit = next((x for x in recs if x[0] == L.MODULE), None)
        rec = {"name": L.MODULE, "toc": hit, "ee": real.get(L.MODULE), "toc_records": len(recs),
               "ee_bytes": os.path.getsize(ee), "toc_bytes": os.path.getsize(ee + ".toc")}

    dom = {}
    spec = os.path.join(ROOT, "Working", "Lights", "bm_rc4_lights.json")
    if os.path.exists(spec):
        dom = json.load(open(spec, encoding="utf-8")).get("domain", {})

    kinds = {}
    for r in rows:
        kinds[r["behavior"]] = kinds.get(r["behavior"], 0) + 1
    head = [r for r in rows if r["part"].startswith("sportsmuscle_headlight")]
    beam = [r for r in head if abs(float(r["angle"]) - 70.0) < 1e-6]
    reaches = sorted(float(r["range"]) for r in beam)
    out_dom = [r for r in rows if float(r["range"]) > 50.0 or float(r["angle"]) > 50.0]

    census = RL.carlight_census(A)
    blocks = sum(v.get("car_light_blocks", 0) for v in census.values())
    lamp_parts = [p for p in RL.LAMP_PARTS if p in census]

    res = {"module": {"path": L.MODULE, "bytes": len(raw),
                      "sha256_prefix": __import__("hashlib").sha256(raw).hexdigest()[:16],
                      "rows": len(rows), "behaviours": kinds},
           "toc": rec, "domain": {"shipped_max": dom.get("shipped_max")},
           "headlight": {"rows": len(head), "angle70": len(beam), "reaches": reaches},
           "out_of_domain": [{"part": r["part"], "behavior": r["behavior"],
                              "range": float(r["range"]), "angle": float(r["angle"])} for r in out_dom],
           "census": census, "car_light_blocks": blocks, "lamp_parts_present": len(lamp_parts),
           "lamp_parts": list(RL.LAMP_PARTS)}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, "lights.json"), "w", encoding="utf-8"), indent=1)

    print(f"module {L.MODULE}")
    print(f"  bytes {len(raw)}  rows {len(rows)}  behaviours {kinds}")
    if rec:
        print(f"  .toc record {rec['toc'][1] if rec['toc'] else None} / {rec['toc'][2] if rec['toc'] else None}"
              f"  .ee dir {rec['ee']}  .toc {rec['toc_records']} records")
    print(f"headlight rows {len(head)}, of which angle 70: {len(beam)}; reaches {reaches}")
    print(f"out-of-domain rows (range > 50 or angle > 50): {len(out_dom)}")
    for r in out_dom[:12]:
        print(f"   {r['part']:32s} {r['behavior']:12s} range {float(r['range']):6.2f} angle {float(r['angle']):5.1f}")
    print(f"CarLight blocks {blocks} over {len(lamp_parts)} lamp parts:")
    for p in RL.LAMP_PARTS:
        v = census.get(p) or {}
        print(f"   {p:34s} blocks {v.get('car_light_blocks', 0)}")
    print("CHECK", "PASS" if len(rows) == 24 and blocks >= 24 and len(lamp_parts) == 8 else "FAIL")
    return 0 if len(rows) == 24 and blocks >= 24 and len(lamp_parts) == 8 else 1


if __name__ == "__main__":
    raise SystemExit(main())

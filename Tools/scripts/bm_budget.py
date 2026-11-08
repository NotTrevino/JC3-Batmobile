"""bm_budget.py - B-15: fit the Batmobile's model memory under the game's hard cap (R9).

Found by V-01 (2026-10-31): the RC's parts module reaches 5,972.9 KB of NON-vanilla .rbm, over the
Vehicle-HD Model hard cap of 4,915 KB (vanilla settings/asset_memory_budgets.bin, MODLOG section 76).
Over the cap the whole vehicle vanishes (test-064).

What counts (calibrated on builds that rendered in game, not assumed): every mesh a part's `.lod`
reaches, MINUS meshes byte-identical to the vanilla Serpente's (shared with the shipped car):
    test-065 3,757.5 | test-081 4,091.5 | test-085/091 4,657.6 KB non-vanilla -> all rendered,
    while their reachable totals (6,132-7,032 KB, vanilla included) were far over 4,915.
User decision 2026-10-31: "unbind panels + trim LODs". The calibration shows the 12 Serpente panels
(vanilla-identical, 2,104.5 KB) do not count against the cap, so only the trim is needed for R9;
whether those panels DRAW is a V-02 render question, not a budget one.

Trim rule (near detail untouched): every non-vanilla 5-slot `.lod` becomes
[slot1, slot2, last, last, last] (body, wheels), or [slot1, last x4] for the small `batmobile_*`
add-ons, so the dropped meshes stop loading. Precedent: the shipped front
wheel .lod already reads [lod1, lod1, lod2, lod3, lod3] (a mesh repeated across slots draws fine;
test-037: a .lod naming an already-listed mesh drew). Now-unreferenced .rbm stay in the tree:
resident-but-unbound bytes do not count (test-091 had 8,456 KB resident .rbm and rendered).

    python Tools/scripts/bm_budget.py <aaf>        # dry run: print the before/after budget
As a module: bm_budget.trim(aaf) -> dict (bm_rc.py applies it, card owner B-15).
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
CAP_KB = 4915.0
TARGET_KB = 4800.0   # margin under the cap


def _vanilla():
    import eetoc, bm_rc  # noqa: E401
    van = eetoc.unaaf(bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + ".ee"))
    return {n: van[o:o + s] for n, o, s in eetoc.sarc_dir(van)}


def measure(aaf: str, V=None) -> dict:
    import bm_parts
    V = V if V is not None else _vanilla()
    parts = bm_parts.decode_parts(open(os.path.join(aaf, bm_parts.MODULE), "rb").read())
    seen, tot, own = set(), 0, 0
    for p in parts:
        lod = os.path.join(aaf, p["model"])
        if not os.path.exists(lod):
            continue
        for l in open(lod, encoding="utf-8").read().splitlines():
            l = l.strip()
            if not l.endswith(".rbm") or l in seen:
                continue
            seen.add(l)
            f = os.path.join(aaf, l)
            if os.path.exists(f):
                b = open(f, "rb").read()
                tot += len(b)
                own += 0 if V.get(l) == b else len(b)
    return {"reachable_kb": round(tot / 1024, 1), "non_vanilla_kb": round(own / 1024, 1), "rbm": len(seen)}


def trim(aaf: str) -> dict:
    import bm_parts
    V = _vanilla()
    before = measure(aaf, V)
    parts = bm_parts.decode_parts(open(os.path.join(aaf, bm_parts.MODULE), "rb").read())
    changed = []
    for model in sorted({p["model"] for p in parts}):
        path = os.path.join(aaf, model)
        if not os.path.exists(path):
            continue
        text = open(path, encoding="utf-8").read()
        lines = text.splitlines()
        slots = [i for i, l in enumerate(lines) if l.strip().endswith(".rbm")]
        if len(slots) != 5:
            continue
        meshes = [lines[i].strip() for i in slots]
        own = [m for m in meshes if os.path.exists(os.path.join(aaf, m))
               and V.get(m) != open(os.path.join(aaf, m), "rb").read()]
        if not own:
            continue                      # vanilla-identical part: shared, not counted, not touched
        # body/wheels keep slot 2; the small B-02 add-ons (turret, guns, pods, jet, flaps) also
        # drop it - at mid range they are a few pixels (first pass left 35 KB over the cap)
        keep = 1 if os.path.basename(model).startswith("batmobile_") else 2
        new = meshes[:keep] + [meshes[-1]] * (5 - keep)
        if new == meshes:
            continue
        for i, m in zip(slots, new):
            lines[i] = m
        open(path, "w", encoding="utf-8", newline="\n" if "\r\n" not in text else "\r\n").write(
            "\n".join(lines) + ("\n" if text.endswith("\n") else ""))
        changed.append({"lod": model, "before": [os.path.basename(m) for m in meshes],
                        "after": [os.path.basename(m) for m in new]})
    after = measure(aaf, V)
    if after["non_vanilla_kb"] > CAP_KB:
        raise SystemExit(f"B-15 trim not enough: {after['non_vanilla_kb']} KB > {CAP_KB}")
    return {"card": "B-15", "cap_kb": CAP_KB, "target_kb": TARGET_KB, "before": before, "after": after,
            "lods_changed": changed, "within_target": after["non_vanilla_kb"] <= TARGET_KB}


if __name__ == "__main__":
    import shutil, tempfile, json
    src = sys.argv[1]
    tmp = tempfile.mkdtemp()
    dst = os.path.join(tmp, "aaf")
    shutil.copytree(src, dst)
    r = trim(dst)
    print(json.dumps({k: r[k] for k in ("before", "after", "within_target")}, indent=1),
          f"\n{len(r['lods_changed'])} .lod changed")
    shutil.rmtree(tmp)

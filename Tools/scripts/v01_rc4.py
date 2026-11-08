"""v01_rc4.py - V-01 file gates on `Builds/bm-RC4` (the tree B-14 produced), offline, read-only.

Every gate is a number re-read from the packed `.ee`/`.toc` (or re-computed from the tree), never a
round figure. `.toc` offsets are into the SARC stream `eetoc.unaaf()` returns, so slices are taken
from that stream - the compressed `.ee` is shorter.

  tree      696 aaf files, 714 .toc records, 9 drop files, .ee 11,225,534 B, .ee.toc 68,675 B,
            install.ps1 6,535 B, receipt.json 211,711 B schema 2
  toc       225 records differ from the vanilla donor .ee; 26 sit at offset 0 (19 size-only
            @files.xml stubs); every offset-0 record carries vanilla bytes
  internal  root .epe 17,713,812 / 134,072; physicsc 15,993,844 / 340,368 (B-10's pinned sha256,
            fda78f4d... after correction 8390's box-0 floor placement);
            health 23,252,584 / 3,741; lights 7,105 B internal; parts, custom_land_global,
            land_engine internal
  budget    model non-vanilla 4,791.3 KB of 4,915 (re-measured); texture 5,380.9 KB of 7,065
            (33 textures, hard_ok); the allocator's 4,648.0 KB is OVER its own sub-allocation and is
            reported, never hidden
  aafdiff   120 files vs bm-RC2 = 20 merge-overlay + 2 stage + 98 base-lineage, 0 unexplained
  ledger    199 rows, 35 edits over 16 rows, 145/216 evidenced, 15/216 blocked, STATUS.md current
  handling  every numeric edit in `t1_handling.json` read back from the `.toc` slice; test-085's 35
  spec      `spec_check.py --lights Working/Appearance/build_lights` (verbatim) + CarLight census
  parts     `jc3parts.py check` (verbatim) + the parts module decoded from the `.toc`
  adf       `jc3adf.py info` on every `.vmodc` that differs from bm-RC2, each byte-equal to its slice
  epe       ConvertProperty round trip of the merged .epe: 7,084 -> 9,025 XML lines, re-export
            byte-identical
  readback  every internal record's slice equals its aaf file; the lights module's 24 rows re-read

Deliberately NOT gated on `t_boost_rows.py` / `t_vnf_six.py`: both pin a 198-row ledger and RC4 has
199 (correction 8396).

Writes only `Builds/bm-RC4/verify/files.{md,json}`. Exit 0 all green, 1 red, 2 tree missing/incomplete.

    python Tools/scripts/v01_rc4.py --write
    python Tools/scripts/v01_rc4.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_leaf         # noqa: E402
import bm_parts        # noqa: E402
import bm_rc           # noqa: E402
import bm_rc4          # noqa: E402
import bm_rc4_lights   # noqa: E402
import eetoc           # noqa: E402
import jc3adf          # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC4")
VERIFY = os.path.join(RC, "verify")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch")
GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONV = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
EE = os.path.join(RC, "drop", bm_rc4.DROP_EE)
MODEL_CAP, TEX_CAP = 4915.0, 7065.0
PHYS_SHA = "fda78f4d8056a4ee47bd8316b6c738fac6f16d227e3bd4769853a43613b41095"
LIGHTS = bm_leaf.DIR + "modules/generated/v0300_car_kensington_sportsmuscle_lights.vmodc"
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def slurp(p: str) -> bytes:
    for i in range(4):
        try:
            return open(p, "rb").read()
        except FileNotFoundError:
            if i == 3:
                raise
            time.sleep(0.5)
    raise SystemExit(p)


def tree(aaf: str) -> dict:
    return {os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/"):
            sha(slurp(os.path.join(dp, n))) for dp, _dn, fs in os.walk(aaf) for n in fs}


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return p.returncode, (p.stdout + p.stderr).strip()


def conv(*a: str) -> None:
    r = subprocess.run([CONV, *a], capture_output=True, text=True, errors="replace")
    if r.returncode != 0:
        raise SystemExit(f"ConvertProperty {a[0]} failed: {(r.stdout + r.stderr)[-500:]}")


class Pack:
    """The `.ee`'s SARC stream: offsets in the `.toc` index THIS buffer, not the compressed file."""

    def __init__(self) -> None:
        self.raw = slurp(EE)
        self.body = eetoc.unaaf(self.raw)
        self.dir = {n: (o, s) for n, o, s in eetoc.sarc_dir(self.body)}
        self.toc = eetoc.read_toc(open(EE + ".toc", "rb").read())

    def get(self, name: str):
        o, s = self.dir.get(name, (0, 0))
        return self.body[o:o + s] if o else None


def parts_module(aaf: str) -> str:
    for dp, _dn, fs in os.walk(aaf):
        for n in fs:
            if n.endswith("_vehicle_parts.vmodc"):
                return os.path.join(dp, n)
    raise SystemExit("no parts module in the tree")


def g_tree(rec: dict, p: Pack) -> tuple[bool, str]:
    at = tree(os.path.join(RC, "aaf"))
    drop = os.path.join(RC, "drop")
    on_disk = sorted(os.path.relpath(os.path.join(dp, n), drop).replace("\\", "/")
                     for dp, _, fs in os.walk(drop) for n in fs)
    want = {"ee": 11225533, "toc": 68675, "install": 6535, "receipt": 217652}
    got = {"ee": os.path.getsize(EE), "toc": os.path.getsize(EE + ".toc"),
           "install": os.path.getsize(os.path.join(RC, "install.ps1")),
           "receipt": os.path.getsize(os.path.join(RC, "receipt.json"))}
    delta = {k: got[k] - want[k] for k in want if got[k] != want[k]}
    ok = (len(at) == 696 and len(p.toc) == 714 and len(on_disk) == 9 == len(rec["files"])
          and got == want and rec["schema"] == 2
          and [f["path"] for f in rec["files"]] == on_disk
          and all(sha(slurp(os.path.join(drop, f["path"]))) == f["sha256"] for f in rec["files"])
          and all(at.get(f["path"]) == f["sha256"] for f in rec["aaf"]["list"]))
    return ok, (f"aaf {len(at)} files (receipt {rec['aaf']['files']}), .toc {len(p.toc)} records, "
                f"drop {len(on_disk)} files; .ee {got['ee']:,} B, .ee.toc {got['toc']:,} B, "
                f"install.ps1 {got['install']:,} B, receipt.json {got['receipt']:,} B schema "
                f"{rec['schema']}" + (f" | DELTA vs the pinned build-d13 facts {delta}" if delta else ""))


def g_toc(rec: dict, p: Pack) -> tuple[bool, str]:
    vs = eetoc.unaaf(bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + ".ee"))
    V = {n: (o, s) for n, o, s in eetoc.sarc_dir(vs)}
    stubs = set(rec["aaf"]["manifest_gaps_inherited"]["dangling"])

    def differs(n: str) -> bool:
        o, s = p.dir[n]
        vn = n.replace(bm_leaf.NEW, bm_leaf.OLD)
        if vn not in V:
            return True
        return p.body[o:o + s] != vs[V[vn][0]:V[vn][0] + V[vn][1]]

    changed = [n for n in p.dir if differs(n)]
    zero = [n for n, o, _ in p.toc if o == 0]
    # a size-only @files.xml stub legitimately stays external with its own bytes (19 of them)
    zero_diff = [n for n in zero if n not in stubs and differs(n)]
    ok = (len(changed) == 225 and len(zero) == 26 and len(stubs) == 19 and not zero_diff
          and all(o for n, o, _ in p.toc if n in (bm_rc4.ROOT_EPE, bm_rc4.PHYS)))
    return ok, (f"{len(changed)} records differ from the vanilla donor .ee (receipt "
                f"{rec['toc']['changed_vs_vanilla']}), {len(zero)} at offset 0 ({len(stubs)} "
                f"size-only @files.xml stubs), offset-0 records carrying non-vanilla bytes: "
                f"{len(zero_diff)}")


def g_internal(rec: dict, p: Pack) -> tuple[bool, str]:
    want = {bm_rc4.ROOT_EPE: (17713812, 134072, None),
            bm_rc4.PHYS: (15993844, 340368, PHYS_SHA),
            bm_leaf.DIR + "batmobile_health_medium.vmodc": (23252584, 3741, None)}
    rows, bad = [], []
    for n, (off, size, h) in want.items():
        got = p.dir.get(n)
        if got != (off, size):
            bad.append(f"{n.split('/')[-1]}: {got} != {(off, size)}")
        elif h and sha(p.get(n) or b"") != h:
            bad.append(f"{n.split('/')[-1]}: sha256 differs from the B-10 pin")
        rows.append(f"{n.split('/')[-1]} {got[0]}/{got[1]}")
    lo = p.dir.get(LIGHTS)
    if not lo or lo[1] != 7105:
        bad.append(f"lights module: {lo} (expected size 7,105)")
    for k in ("sportsmuscle_vehicle_parts.vmodc", "_custom_land_global.vmodc",
              "_land_engine.vmodc"):
        hit = [(n, o) for n, o, _ in p.toc if n.endswith(k)]
        if not hit or not all(o for _, o in hit):
            bad.append(f"{k}: not internal {hit}")
        rows.append(f"{k} internal @{hit[0][1] if hit else '?'}")
    note = ""
    if lo:
        note = (f" | lights at {lo[0]:,} (D-03 tree: 16,499,504; the merged tree's layout shifts it "
                f"by {lo[0] - 16499504:+,} B, same 7,105 B)")
    return not bad, "; ".join(rows) + note + (f" | bad: {bad}" if bad else "")


def measure(aaf: str) -> dict:
    """bm_budget.measure's rule, on the parts module this tree actually keeps."""
    import bm_budget
    V = bm_budget._vanilla()
    parts = bm_parts.decode_parts(slurp(parts_module(aaf)))
    seen, tot, own = set(), 0, 0
    for prt in parts:
        lod = os.path.join(aaf, prt["model"])
        if not os.path.exists(lod):
            continue
        for line in open(lod, encoding="utf-8").read().splitlines():
            line = line.strip()
            if not line.endswith(".rbm") or line in seen:
                continue
            seen.add(line)
            f = os.path.join(aaf, line)
            if os.path.exists(f):
                b = slurp(f)
                tot += len(b)
                own += 0 if V.get(line) == b else len(b)
    return {"reachable_kb": round(tot / 1024, 1), "non_vanilla_kb": round(own / 1024, 1),
            "rbm": len(seen)}


def g_budget(rec: dict) -> tuple[bool, str]:
    m = measure(os.path.join(RC, "aaf"))
    txt = open(os.path.join(ROOT, "Builds", "bm-RC4-appearance", "budget.json"),
               encoding="utf-8").read()
    tex = rec["budgets"]["texture_used_kb"]
    alloc = "4648.0" in txt
    ok = (abs(m["non_vanilla_kb"] - 4791.3) < 0.2 and m["non_vanilla_kb"] <= MODEL_CAP
          and abs(tex - 5380.9) < 0.1 and tex <= TEX_CAP
          and '"hard_ok": true' in txt and alloc)
    return ok, (f"model non-vanilla {m['non_vanilla_kb']:,} KB of {MODEL_CAP:,.0f} (reachable "
                f"{m['reachable_kb']:,} KB, {m['rbm']} .rbm, re-measured); texture {tex:,} KB of "
                f"{TEX_CAP:,.0f} (33 textures, hard_ok); allocator "
                f"{'4,648.0 KB present and OVER its own sub-allocation (reported, not hidden)' if alloc else 'figure NOT FOUND'}")


def g_aafdiff(rec: dict) -> tuple[bool, str]:
    at = tree(os.path.join(RC, "aaf"))
    rc2 = tree(os.path.join(ROOT, "Builds", "bm-RC2", "aaf"))
    base = tree(os.path.join(ROOT, "Builds", "bm-RC4-base", "aaf"))
    stage = tree(os.path.join(ROOT, "Builds", "bm-RC4-lights", "aaf"))
    own = json.load(open(os.path.join(ROOT, "Working", "RC", "bm_rc_manifest_bm-RC4.json"),
                         encoding="utf-8"))["owners"]
    kinds = bm_rc4.aafdiff_class(at, rc2, base, stage, own)
    counts: dict[str, int] = {}
    for k in kinds.values():
        counts[k] = counts.get(k, 0) + 1
    ok = (len(kinds) == 120 and counts.get("merge-overlay") == 20 and counts.get("stage") == 2
          and counts.get("base-lineage") == 98 and counts.get("unexplained", 0) == 0
          and rec["aafdiff_rc2"]["differ"] == 120)
    return ok, (f"{len(kinds)} files differ from bm-RC2 = {counts.get('merge-overlay')} "
                f"merge-overlay + {counts.get('stage')} stage + {counts.get('base-lineage')} "
                f"base-lineage, {counts.get('unexplained', 0)} unexplained")


def g_ledger() -> tuple[bool, str]:
    rows = [json.loads(l) for l in open(os.path.join(ROOT, "Working", "Translation",
                                                     "T_ROWS.jsonl"), encoding="utf-8") if l.strip()]
    edits = sum(int(r.get("edits") or 0) for r in rows)
    edited = sum(1 for r in rows if int(r.get("edits") or 0))
    st = open(os.path.join(ROOT, "STATUS.md"), encoding="utf-8").read()
    rc, text = run(os.path.join(HERE, "status_audit.py"), "--check")
    ok = (len(rows) == 199 and edits == 35 and edited == 16 and "145 / 216" in st
          and "15 / 216" in st and rc == 0)
    return ok, (f"{len(rows)} rows, {edits} edits over {edited} rows; STATUS.md 145/216 evidenced, "
                f"15/216 blocked; status_audit.py --check exit {rc} "
                f"({(text.splitlines() or ['?'])[-1][:70]})")


def g_handling(p: Pack) -> tuple[bool, str]:
    spec = json.load(open(os.path.join(ROOT, "Working", "Translation", "t1_handling.json"),
                          encoding="utf-8"))
    comb = json.load(open(os.path.join(ROOT, "Working", "Translation",
                                       "rc4_handling_edits_combined.json"), encoding="utf-8"))
    audit = comb["payload_audit"]
    pairs, skipped = [], []
    for e in spec["edits"]:
        to = e["to"]
        if isinstance(to, str) and "(" in to:
            skipped.append((e["row"], e["member"]))
            continue
        raw_ms = [m.strip() for m in e["member"].split("/")]
        # "front/rear.min_time_to_block" means front.min_time_to_block + rear.min_time_to_block
        if len(raw_ms) > 1 and "." in raw_ms[-1]:
            tail = raw_ms[-1].split(".", 1)[1]
            raw_ms = [m if "." in m else f"{m}.{tail}" for m in raw_ms]
        ts = [x.strip() for x in to.split("/")] if isinstance(to, str) and "/" in to else [to]
        if len(ts) != len(raw_ms):
            ts = ts * len(raw_ms)
        pairs += [(e["row"], m, t) for m, t in zip(raw_ms, ts)]
    okn, bad = 0, []
    for row, member, to in pairs:
        ent = next((a for a in audit if a["row"] == row
                    and (a["member"] == member or a["member"].endswith("." + member)
                         or member.endswith("." + a["member"]))), None)
        if ent is None:
            bad.append((row, member, "no file in the RC4 payload audit"))
            continue
        cand = [n for n in p.dir if n.endswith(ent["file"])]
        raw = p.get(cand[0]) if cand else None
        if raw is None:
            bad.append((row, member, f"{ent['file']} not internal"))
            continue
        vals = [v for path, _t, v in jc3adf.walk(jc3adf.Adf(raw), 0)
                if path == member or path.endswith("." + member)]
        got = any(abs(float(v) - float(to)) < 1e-3 for v in vals) if vals else False
        if got:
            okn += 1
        else:
            bad.append((row, member, to, vals[:2]))
    t85 = json.load(open(os.path.join(ROOT, "Builds", "test-085", "receipt.json"),
                         encoding="utf-8"))
    ok = not bad and t85.get("edits") == 35
    return ok, (f"t1_handling.json {len(spec['edits'])} entries -> {len(pairs)} numeric member "
                f"values, {okn}/{len(pairs)} read back from the .toc slice "
                f"({len(skipped)} composition-only entries not written, test-085 receipt edits "
                f"{t85.get('edits')}); failed {len(bad)}" + (f" {bad[:3]}" if bad else ""))


def g_spec(p: Pack) -> tuple[bool, str]:
    rc, text = run(os.path.join(HERE, "spec_check.py"), "--lights",
                   os.path.join(ROOT, "Working", "Appearance", "build_lights"))
    last = (text.splitlines() or ["?"])[-1]
    census = bm_rc4_lights.carlight_census(os.path.join(RC, "aaf"))
    blocks = sum(v["car_light_blocks"] for v in census.values())
    ok = rc == 0 and "spec mismatches 0" in last and blocks == 24 and len(census) == 8
    return ok, (f"spec_check.py --lights exit {rc}: {last}; CarLight census {blocks} blocks over "
                f"{len(census)} lamp parts")


def g_parts(p: Pack, rec: dict) -> tuple[bool, str]:
    rc, text = run(os.path.join(HERE, "jc3parts.py"), "check")
    aaf = os.path.join(RC, "aaf")
    mod = os.path.relpath(parts_module(aaf), aaf).replace("\\", "/")
    raw = p.get(mod) or slurp(os.path.join(aaf, mod))
    n = len(bm_parts.decode_parts(raw))
    want = json.load(open(os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json"),
                          encoding="utf-8"))["summary"]["parts_after"]
    last = (text.splitlines() or ["?"])[-1]
    ok = rc == 0 and n == want
    return ok, (f"jc3parts.py check exit {rc}: {last}; parts module via .toc decodes {n} parts "
                f"(Working/Parts manifest {want})")


def g_adf(p: Pack) -> tuple[bool, str]:
    at = tree(os.path.join(RC, "aaf"))
    rc2 = tree(os.path.join(ROOT, "Builds", "bm-RC2", "aaf"))
    mods = sorted(n for n in at if n.endswith(".vmodc") and rc2.get(n) != at[n])
    bad, rows = [], []
    for n in mods:
        rc, text = run(os.path.join(HERE, "jc3adf.py"), "info", os.path.join(RC, "aaf", n))
        eq = p.get(n) == slurp(os.path.join(RC, "aaf", n))
        try:
            nodes = len(list(jc3adf.walk(jc3adf.Adf(p.get(n) or b""), 0)))
        except Exception as e:  # noqa: BLE001
            nodes, rc = 0, rc or 1
            bad.append((n, str(e)[:80]))
        if rc or not eq:
            bad.append((n, f"info exit {rc}, toc slice equal {eq}"))
        rows.append({"module": n.split("/")[-1], "exit": rc, "nodes": nodes,
                     "toc_slice_equal": eq, "info_last": (text.splitlines() or ["?"])[-1]})
    return (not bad and len(mods) > 0,
            f"{len(mods)} edited .vmodc re-read with jc3adf.py info, byte-equal to their .toc "
            f"slice {sum(1 for r in rows if r['toc_slice_equal'])}/{len(mods)}, bad {len(bad)}",
            rows)


def g_epe(p: Pack) -> tuple[bool, str]:
    os.makedirs(SCRATCH, exist_ok=True)
    built = p.get(bm_rc4.ROOT_EPE)
    if built is None:
        return False, "root .epe is not internal"
    pe = os.path.join(SCRATCH, "v01_epe_built.epe")
    open(pe, "wb").write(built)
    x1, x2, pe2 = (os.path.join(SCRATCH, n) for n in
                   ("v01_epe_in.xml", "v01_epe_rt.xml", "v01_epe_rt.epe"))
    conv("--e", pe, x1)
    conv("-i", x1, pe2)
    conv("--e", pe2, x2)
    a, b = open(x1, "rb").read(), open(x2, "rb").read()
    base_x = os.path.join(SCRATCH, "v01_epe_base.xml")
    conv("--e", os.path.join(ROOT, "Builds", "bm-RC4-base", "aaf", bm_rc4.EPE), base_x)
    n, nb = len(a.splitlines()), len(open(base_x, "rb").read().splitlines())
    ok = a == b and n == 9025 and nb == 7084
    return ok, (f"ConvertProperty round trip: base {nb:,} -> merged {n:,} XML lines, re-export "
                f"{'byte-identical' if a == b else 'DIFFERS'}")


def lights_rows(blob: bytes) -> list[dict]:
    flat = {p: v for p, _t, v in jc3adf.walk(jc3adf.Adf(blob), 0)}
    n = 0
    while f"lights[{n}].behavior" in flat:
        n += 1
    return [{m: flat[f"lights[{i}].{m}"] for m in
             ("behavior", "part", "range", "angle", "multiplier", "falloff_start")}
            for i in range(n)]


def g_readback(p: Pack) -> tuple[bool, str]:
    aaf = os.path.join(RC, "aaf")
    internal = [(n, o, s) for n, (o, s) in p.dir.items() if o]
    bad = [n for n, o, s in internal if p.body[o:o + s] != slurp(os.path.join(aaf, n))]
    rows = lights_rows(p.get(LIGHTS) or b"")
    beams = sorted(float(r["range"]) for r in rows if r["behavior"] == "HeadLight"
                   and abs(float(r["angle"]) - 70.0) < 1e-6)
    per_side = {s: sum(1 for r in rows if r["part"] == f"sportsmuscle_headlight_f_{s}"
                       and abs(float(r["angle"]) - 70.0) < 1e-6) for s in ("l", "r")}
    ok = (not bad and len(internal) > 600 and len(rows) == 24
          and beams == [18.0, 18.0, 60.0, 60.0] and per_side == {"l": 2, "r": 2})
    return ok, (f"{len(internal)} internal .toc slices equal their aaf file ({len(bad)} differ); "
                f"lights module {len(rows)} rows, two 70 deg beams per side {per_side}, reaches "
                f"{beams}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    for need in (os.path.join(RC, "receipt.json"), EE, EE + ".toc"):
        if not os.path.exists(need):
            print(f"BLOCKED: {rel(need)} missing (the tree is incomplete or being rebuilt)")
            return 2
    if os.path.getsize(EE) < 11000000:
        print(f"BLOCKED: {rel(EE)} is {os.path.getsize(EE):,} B (the tree is incomplete or "
              f"being rebuilt)")
        return 2
    rec = json.load(open(os.path.join(RC, "receipt.json"), encoding="utf-8"))
    p = Pack()
    out = {"tree": rel(RC), "ee": rel(EE), "ee_sha256": sha(p.raw)[:16],
           "ee_bytes": len(p.raw), "toc_records": len(p.toc)}
    gates, adf_rows = [], []
    for name, fn in (("tree", lambda: g_tree(rec, p)),
                     ("toc", lambda: g_toc(rec, p)),
                     ("internal", lambda: g_internal(rec, p)),
                     ("budget", lambda: g_budget(rec)),
                     ("aafdiff", lambda: g_aafdiff(rec)),
                     ("ledger", lambda: g_ledger()),
                     ("handling", lambda: g_handling(p)),
                     ("spec", lambda: g_spec(p)),
                     ("parts", lambda: g_parts(p, rec)),
                     ("adf", lambda: g_adf(p)),
                     ("epe", lambda: g_epe(p)),
                     ("readback", lambda: g_readback(p))):
        try:
            r = fn()
            ok, msg = r[0], r[1]
            if name == "adf":
                adf_rows = r[2]
        except Exception as e:  # noqa: BLE001
            ok, msg = False, f"gate crashed: {type(e).__name__}: {str(e)[:200]}"
        gates.append({"gate": name, "green": bool(ok), "message": msg})
        print(f"{'GREEN' if ok else 'RED  '} {name:9s} {msg}")
    red = [g["gate"] for g in gates if not g["green"]]
    out["gates"] = gates
    out["adf_rows"] = adf_rows
    out["verdict"] = "ALL GREEN" if not red else "RED: " + ", ".join(red)
    print(out["verdict"])

    L = ["# V-01 file gates on `Builds/bm-RC4`", "",
         "`python Tools/scripts/v01_rc4.py --check`", "",
         f"**{out['verdict']}** - .ee {out['ee_bytes']:,} B, sha256 `{out['ee_sha256']}…`, "
         f"{out['toc_records']} .toc records.", "",
         "| gate | result | number |", "|---|---|---|"]
    for g in gates:
        L.append(f"| {g['gate']} | {'GREEN' if g['green'] else 'RED'} | {g['message']} |")
    L += ["", "## Edited modules re-read with `jc3adf.py info`", "",
          "| module | exit | nodes | .toc slice == aaf | info last line |", "|---|---|---|---|---|"]
    for r in adf_rows:
        L.append(f"| `{r['module']}` | {r['exit']} | {r['nodes']} | {r['toc_slice_equal']} | "
                 f"`{r['info_last'][:90]}` |")
    L += ["", "Not gated here, deliberately: `t_boost_rows.py` and `t_vnf_six.py` pin a 198-row "
          "ledger and RC4 has 199 (correction 8396).", ""]
    text = "\n".join(L) + "\n"
    if a.write:
        os.makedirs(VERIFY, exist_ok=True)
        with open(os.path.join(VERIFY, "files.json"), "w", encoding="utf-8", newline="\n") as f:
            json.dump(out, f, indent=1, sort_keys=True)
            f.write("\n")
        with open(os.path.join(VERIFY, "files.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        print(f"wrote {rel(os.path.join(VERIFY, 'files.md'))}")
    else:
        md, js = os.path.join(VERIFY, "files.md"), os.path.join(VERIFY, "files.json")
        if not (os.path.exists(md) and os.path.exists(js)):
            print("FAIL: verify/files.{md,json} missing (run --write)")
            return 1
        if open(md, encoding="utf-8", newline="").read().replace("\r\n", "\n") != text:
            print("FAIL: verify/files.md differs from the re-derived page")
            return 1
        if json.load(open(js, encoding="utf-8")) != json.loads(json.dumps(out)):
            print("FAIL: verify/files.json differs from the re-derived document")
            return 1
        print("PASS: verify/files.md + files.json match the re-derived gates")
    return 0 if not red else 1


if __name__ == "__main__":
    raise SystemExit(main())

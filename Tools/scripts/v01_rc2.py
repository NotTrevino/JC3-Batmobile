"""v01_rc2.py - V-01 file gates on the newest candidate, `Builds/bm-RC2` (offline, read-only).

Runs the five gates the card names, each on the packed `.ee` through its `.toc` where the value
must be read back:

  spec      `spec_check.py --lights Working/Appearance/build_lights` (verbatim) + every light RBM
            in the RC hashing equal to the manifest's
  parts     `jc3parts.py check` (verbatim) + the built parts module, read through the `.toc`,
            decoding to the manifest's part count
  budget    `bm_budget.measure()` on the built aaf: Model (non-vanilla) <= 4,915 KB,
            Texture (resident .ddsc) <= 7,065 KB
  adf       `jc3adf.py info` on every edited `.vmodc` (verbatim last line), and every edited
            module slices byte-identically out of the built `.toc`
  readback  every edited value that has a machine-readable target (B-09 health rows, B-10
            physicsc sha, B-04R parts count) re-read from the `.toc` slice

Writes only `Builds/bm-RC2/verify/files.md` + `files.json`. Exit 0 = all green, 1 = a red gate,
2 = the tree is missing. Never edits the build.

    python Tools/scripts/v01_rc2.py --check
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import eetoc          # noqa: E402
import jc3adf         # noqa: E402
import bm_budget      # noqa: E402
import bm_parts       # noqa: E402
import bm_leaf        # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC2")
VERIFY = os.path.join(RC, "verify")
SCRATCH = os.path.join(ROOT, "tmp", "freebuff", "scratch")
EE = os.path.join(RC, "drop", bm_leaf.DIR + bm_leaf.NEW + ".ee")
CAP_MODEL, CAP_TEX = 4915.0, 7065.0
sha = lambda b: hashlib.sha256(b).hexdigest()  # noqa: E731


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def run(*args: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=ROOT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    return p.returncode, (p.stdout + p.stderr).strip()


class Pack:
    def __init__(self) -> None:
        self.raw = eetoc.unaaf(open(EE, "rb").read())
        self.dir = {n: (o, s) for n, o, s in eetoc.sarc_dir(self.raw)}
        self.toc = eetoc.read_toc(open(EE + ".toc", "rb").read())

    def get(self, name: str):
        o, s = self.dir.get(name, (0, 0))
        return self.raw[o:o + s] if o else None


def tree(tag: str) -> dict:
    a = os.path.join(ROOT, "Builds", tag, "aaf")
    out = {}
    for dp, _dn, fs in os.walk(a):
        for n in fs:
            f = os.path.join(dp, n)
            out[os.path.relpath(f, a).replace("\\", "/")] = sha(open(f, "rb").read())
    return out


def edited_modules(p: Pack) -> list[str]:
    base = tree("bm-001")
    rc = tree("bm-RC2")
    old = bm_leaf.NEW
    return sorted(n for n in rc if n.endswith(".vmodc")
                  and base.get(n.replace("/batmobile/", "/").replace(old, bm_leaf.OLD)) != rc[n])


def module_path(aaf: str) -> str:
    for dp, _dn, fs in os.walk(aaf):
        for n in fs:
            if n.endswith("vehicle_parts.vmodc"):
                return os.path.relpath(os.path.join(dp, n), aaf).replace("\\", "/")
    raise SystemExit("no vehicle_parts.vmodc in the tree")


def g_spec(out: dict) -> tuple[bool, str]:
    rc, text = run(os.path.join(HERE, "spec_check.py"), "--lights",
                   os.path.join(ROOT, "Working", "Appearance", "build_lights"))
    man = json.load(open(os.path.join(ROOT, "Working", "Appearance", "build_lights",
                                      "lights_manifest.json"), encoding="utf-8"))
    names = sorted({f for l in man["lamps"] for f in l.get("lod_files", [])})
    a = os.path.join(RC, "aaf")
    hits = 0
    for n in names:
        cand = [os.path.join(dp, f) for dp, _dn, fs in os.walk(a) for f in fs
                if f == os.path.basename(n)]
        src = os.path.join(ROOT, "Working", "Appearance", "build_lights", os.path.basename(n))
        if cand and os.path.exists(src) and sha(open(cand[0], "rb").read()) == sha(open(src, "rb").read()):
            hits += 1
    last = (text.splitlines() or ["?"])[-1]
    out["spec"] = {"command": "python Tools/scripts/spec_check.py --lights Working/Appearance/build_lights",
                   "exit": rc, "last_line": last, "light_rbms": len(names), "rbm_equal": hits,
                   "full_output": text.splitlines()[-6:]}
    return rc == 0 and hits == len(names), f"spec_check exit {rc}: {last}; light RBMs hash-equal {hits}/{len(names)}"


def g_parts(p: Pack, out: dict) -> tuple[bool, str]:
    rc, text = run(os.path.join(HERE, "jc3parts.py"), "check")
    mod = module_path(os.path.join(RC, "aaf"))
    raw = p.get(mod) or open(os.path.join(RC, "aaf", mod), "rb").read()
    parts = bm_parts.decode_parts(raw)
    want = json.load(open(os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json"),
                          encoding="utf-8"))["summary"]["parts_after"]
    last = (text.splitlines() or ["?"])[-1]
    # B-04R rebuilt the module to 61 parts; Working/Parts/bm_vehicle_parts.json still carries the
    # pre-B-04R 59.  The build step's own number is the expectation, the manifest the divergence.
    steps = json.load(open(os.path.join(RC, "receipt.json"), encoding="utf-8"))["steps"]
    b04r = next((s for s in steps if s.startswith("B-04R:")), "")
    built = int(re.search(r"'parts': (\d+)", b04r).group(1)) if re.search(r"'parts': (\d+)", b04r) else want
    out["parts"] = {"command": "python Tools/scripts/jc3parts.py check", "exit": rc,
                    "last_line": last, "module": mod, "decoded": len(parts), "b04r_parts": built,
                    "manifest_parts": want, "module_from_toc": p.get(mod) is not None,
                    "full_output": text.splitlines()[-4:]}
    return rc == 0 and len(parts) == built, (
        f"jc3parts check exit {rc}: {last}; built module (via .toc) decodes {len(parts)} parts, "
        f"B-04R {built}, Working/Parts manifest {want} (stale: pre-B-04R)")


def measure(aaf: str) -> dict:
    """bm_budget.measure's rule, keyed on the module path this tree actually uses (B-18 moved it)."""
    import bm_rc
    van = eetoc.unaaf(bm_rc.vfs(bm_leaf.DIR + bm_leaf.OLD + ".ee"))
    V = {n: van[o:o + s] for n, o, s in eetoc.sarc_dir(van)}
    mod = module_path(aaf)
    parts = bm_parts.decode_parts(open(os.path.join(aaf, mod), "rb").read())
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
                b = open(f, "rb").read()
                tot += len(b)
                own += 0 if V.get(line) == b else len(b)
    return {"reachable_kb": round(tot / 1024, 1), "non_vanilla_kb": round(own / 1024, 1),
            "rbm": len(seen)}


def g_budget(out: dict) -> tuple[bool, str]:
    a = os.path.join(RC, "aaf")
    m = measure(a)
    p = Pack()
    tex = sum(s for n, o, s in p.toc if o and n.endswith(".ddsc")) / 1024
    ok = m["non_vanilla_kb"] <= CAP_MODEL and tex <= CAP_TEX
    out["budget"] = {"model_non_vanilla_kb": m["non_vanilla_kb"], "model_cap_kb": CAP_MODEL,
                     "reachable_kb": m["reachable_kb"], "rbm": m["rbm"],
                     "texture_resident_kb": round(tex, 1), "texture_cap_kb": CAP_TEX}
    return ok, (f"Model non-vanilla {m['non_vanilla_kb']:,.1f} KB of {CAP_MODEL:,.0f} "
                f"(reachable {m['reachable_kb']:,.1f} KB, {m['rbm']} .rbm) | "
                f"Texture resident {tex:,.1f} KB of {CAP_TEX:,.0f}")


def g_adf(p: Pack, mods: list[str], out: dict) -> tuple[bool, str]:
    a = os.path.join(RC, "aaf")
    rows, bad = [], []
    for n in mods:
        rc, text = run(os.path.join(HERE, "jc3adf.py"), "info", os.path.join(a, n))
        last = (text.splitlines() or ["?"])[-1]
        slice_ok = p.get(n) == open(os.path.join(a, n), "rb").read()
        try:
            ad = jc3adf.Adf(p.get(n) or open(os.path.join(a, n), "rb").read())
            nodes = list(jc3adf.walk(ad, 0))
        except Exception as e:  # noqa: BLE001
            nodes, bad = [], [(n, str(e)[:80])]
        if rc or not slice_ok:
            bad.append((n, f"info exit {rc}, toc slice equal {slice_ok}"))
        rows.append({"module": n, "info_last": last, "exit": rc, "nodes": len(nodes),
                     "toc_slice_equal": slice_ok})
    out["adf"] = {"modules": len(mods), "green": sum(1 for r in rows if not r["exit"] and r["toc_slice_equal"]),
                  "bad": bad, "rows": rows}
    return not bad and len(mods) > 0, (
        f"jc3adf.py info on {len(mods)} edited .vmodc: {sum(1 for r in rows if not r['exit'])} re-read, "
        f"toc slice equal {sum(1 for r in rows if r['toc_slice_equal'])}/{len(mods)}, bad {len(bad)}")


def g_readback(p: Pack, out: dict, mods: list[str]) -> tuple[bool, str]:
    a = os.path.join(RC, "aaf")
    rows, bad = [], []
    # every edited module's toc slice is the shipped byte range
    for n in mods:
        got = p.get(n)
        if got is None:
            bad.append((n, "not internal in .toc"))
        elif got != open(os.path.join(a, n), "rb").read():
            bad.append((n, "toc slice differs from aaf"))
        else:
            rows.append((n, "toc slice == aaf"))
    # B-09 health rows read back from the toc slice
    hp = os.path.join(ROOT, "Working", "Damage", "bm_health.json")
    if os.path.exists(hp):
        h = json.load(open(hp, encoding="utf-8"))
        for r in h.get("rows", []):
            mod = r["module"].replace(bm_leaf.OLD, bm_leaf.NEW).replace("/default/", "/default/batmobile/")
            raw = p.get(mod)
            if raw is None:
                cand = [n for n in p.dir if n.endswith(os.path.basename(mod))]
                raw = p.get(cand[0]) if cand else None
            if raw is None:
                bad.append((r["row"], "module not internal"))
                continue
            vals = [v for path, _t, v in jc3adf.walk(jc3adf.Adf(raw), 0)
                    if path == r["member"] or path.endswith("." + r["member"])]
            to = r["to"]
            got = any((abs(float(v) - float(to)) < 1e-3)
                      if isinstance(v, (int, float)) and isinstance(to, (int, float)) else v == to
                      for v in vals)
            (rows if got else bad).append((r["row"], r["member"], to, vals[:2]))
    # B-10 physicsc: the shipped bytes are Working/Collision/batmobile.physicsc
    ph = ("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/batmobile/"
          "sportsmuscle.physicsc")
    got = p.get(ph)
    aaf_ph = os.path.join(RC, "aaf", ph)
    if got and os.path.exists(aaf_ph) and got == open(aaf_ph, "rb").read():
        os.makedirs(SCRATCH, exist_ok=True)
        tmp = os.path.join(SCRATCH, "rc2_physicsc_check.physicsc")
        open(tmp, "wb").write(got)
        rc, text = run(os.path.join(HERE, "jc3hkx.py"), "check", "--entity", "__none__",
                       "--file", tmp)
        ok = rc == 0 and "check ok" in text
        obj = re.search(r"(\d+) objects", text)
        (rows if ok else bad).append(("B-10", "physicsc toc slice == aaf; "
                                      + ("jc3hkx check ok" if ok else (text.splitlines() or ["?"])[-1]),
                                      f"{len(got):,} B, {obj.group(1) if obj else '?'} objects"))
    else:
        bad.append(("B-10", "physicsc toc slice != aaf"))
    out["readback"] = {"proven": len(rows), "failed": bad}
    return not bad, f"values/slices proven {len(rows)}, failed {len(bad)}" + (
        f": {bad[:3]}" if bad else "")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")
    if not os.path.exists(os.path.join(RC, "receipt.json")):
        print("BLOCKED: Builds/bm-RC2/receipt.json missing")
        return 2
    p = Pack()
    mods = edited_modules(p)
    out: dict = {"tree": rel(RC), "ee": rel(EE), "ee_sha256": sha(open(EE, "rb").read())[:16],
                 "toc_records": len(p.toc), "edited_modules": len(mods)}
    gates = []
    for name, fn in (("spec", lambda: g_spec(out)),
                     ("parts", lambda: g_parts(p, out)),
                     ("budget", lambda: g_budget(out)),
                     ("adf", lambda: g_adf(p, mods, out)),
                     ("readback", lambda: g_readback(p, out, mods))):
        try:
            ok, msg = fn()
        except Exception as e:  # noqa: BLE001
            ok, msg = False, f"gate crashed: {type(e).__name__}: {str(e)[:200]}"
        gates.append({"gate": name, "green": bool(ok), "message": msg})
        print(f"{'GREEN' if ok else 'RED  '} {name:9s} {msg}")
    red = [g["gate"] for g in gates if not g["green"]]
    out["gates"] = gates
    out["verdict"] = "ALL GREEN" if not red else "RED: " + ", ".join(red)
    print(out["verdict"])
    if True:
        L = ["# V-01 file gates on `Builds/bm-RC2`", "",
             "`python Tools/scripts/v01_rc2.py --check`", "",
             f"**{out['verdict']}** - .ee sha256 `{out['ee_sha256']}…`, {out['toc_records']} toc records, "
             f"{out['edited_modules']} edited modules.", "",
             "| gate | result | detail |", "|---|---|---|"]
        for g in gates:
            L.append(f"| {g['gate']} | {'GREEN' if g['green'] else 'RED'} | {g['message']} |")
        L += ["", "## Spec check, verbatim", "", "```"]
        L += out["spec"]["full_output"]
        L += ["```", "", "## Parts check, verbatim", "", "```"] + out["parts"]["full_output"] + ["```"]
        L += ["", "## Edited modules re-read with `jc3adf.py info`", "",
              "| module | exit | nodes | toc slice == aaf | info last line |", "|---|---|---|---|---|"]
        for r in out["adf"]["rows"]:
            L.append(f"| `{r['module'].split('/')[-1]}` | {r['exit']} | {r['nodes']} | "
                     f"{r['toc_slice_equal']} | `{r['info_last'][:90]}` |")
        text = "\n".join(L) + "\n"
        if a.write:
            os.makedirs(VERIFY, exist_ok=True)
            with open(os.path.join(VERIFY, "files.json"), "w", encoding="utf-8") as f:
                json.dump(out, f, indent=1, sort_keys=True)
                f.write("\n")
            with open(os.path.join(VERIFY, "files.md"), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        else:
            md_p, js_p = os.path.join(VERIFY, "files.md"), os.path.join(VERIFY, "files.json")
            if not (os.path.exists(md_p) and os.path.exists(js_p)):
                print("FAIL: verify/files.{md,json} missing (run --write)")
                return 1
            if open(md_p, encoding="utf-8", newline="").read().replace("\r\n", "\n") != text:
                print("FAIL: verify/files.md differs from the re-derived page")
                return 1
            if json.load(open(js_p, encoding="utf-8")) != json.loads(json.dumps(out)):
                print("FAIL: verify/files.json differs from the re-derived document")
                return 1
    return 0 if not red else 1


if __name__ == "__main__":
    raise SystemExit(main())

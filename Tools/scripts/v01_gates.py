"""v01_gates.py - V-01: file gates on the release candidate `Builds/bm-RC1` (offline, read-only).

Card (GRAB_BACKLOG.md V-01): aafdiff (only planned files), .toc records (internal where required),
spec_check.py, budgets (Model <= 4,915 KB, Texture <= 7,065 KB), parts re-read, jc3adf re-read of
every edited module, ConvertProperty round trip of the .epe, read-back of every edited value through
the built .toc. Done: all green; output in Builds/bm-RC1/verify/.

Every gate reads the PACKED .ee through its .toc (the bytes the game would read), never the source
tree alone. Writes only Builds/bm-RC1/verify/v01/. Exit 0 = all green, 1 = a gate is red, 2 = no RC.

Budget method (R9, MODLOG section 76): the game's hard caps from vanilla
`settings/asset_memory_budgets.bin` (Vehicle-HD Model 4,915 KB, Texture 7,065 KB). Model = every .rbm
reachable from the built parts module that is NOT byte-identical to the vanilla Serpente's (calibrated
on builds that rendered; see bm_budget.py); texture = resident .ddsc. Over a cap is RED, never a note.

Usage: python Tools/scripts/v01_gates.py --check   (or one gate: diff toc spec budget parts adf epe readback)
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
import eetoc  # noqa: E402
import jc3adf  # noqa: E402
import bm_leaf  # noqa: E402

RC = os.path.join(ROOT, "Builds", "bm-RC1")
OUTD = os.path.join(RC, "verify", "v01")
DIR, OLD, NEW = bm_leaf.DIR, bm_leaf.OLD, bm_leaf.NEW
EE = os.path.join(RC, "drop", DIR + NEW + ".ee")
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
CAP_MODEL, CAP_TEX = 4915.0, 7065.0
LINEAGE = [("bm-001", "bm-002", "B-02/B-03/B-04"), ("bm-002", "bm-009", "B-09"), ("bm-009", "bm-005", "B-05"),
           ("bm-005", "bm-006", "B-06"), ("bm-005", "bm-007", "B-07"), ("bm-005", "bm-008", "B-08")]
sha = lambda b: hashlib.sha256(b).hexdigest()


class Pack:
    def __init__(self):
        self.raw = eetoc.unaaf(open(EE, "rb").read())
        self.dir = {n: (o, s) for n, o, s in eetoc.sarc_dir(self.raw)}
        self.toc = eetoc.read_toc(open(EE + ".toc", "rb").read())
        self.T = {n: (o, s) for n, o, s in self.toc}

    def get(self, n):  # bytes the game reads for n via the .toc (None if the toc says "from the archives")
        o, s = self.T.get(n, (0, 0))
        return self.raw[o:o + s] if o else None


def tree(t):
    a = os.path.join(ROOT, "Builds", t, "aaf")
    return {os.path.relpath(os.path.join(dp, n), a).replace("\\", "/"): sha(open(os.path.join(dp, n), "rb").read())
            for dp, _, fs in os.walk(a) for n, in [(x,) for x in fs]}


def g_diff(p, out):
    trees = {t: tree(t) for t in {x for a, b, _ in LINEAGE for x in (a, b)}}
    rc = {k.replace(NEW, OLD): v for k, v in tree("bm-RC1").items()}
    owner = {}
    for a, b, card in LINEAGE:
        for k, v in trees[b].items():
            if trees[a].get(k) != v:
                owner.setdefault(k, []).append(card)
    owner.setdefault("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc", []).append("B-10")
    for e in bm_leaf.INNER:
        owner.setdefault(DIR + OLD + e, []).append("B-13b")
    for f in json.load(open(os.path.join(RC, "receipt.json")))["aaf"]["list"]:
        if f["owner_card"] == "B-15":
            owner.setdefault(f["path"], []).append("B-15")
    owner.setdefault("@files.xml", []).append("B-13b")
    base = trees["bm-001"]
    changed = sorted(k for k in rc if base.get(k) != rc[k])
    removed = sorted(set(base) - set(rc))
    unplanned = [k for k in changed if k not in owner]
    out["diff"] = {"changed_or_added": len(changed), "removed": removed, "unplanned": unplanned,
                   "by_card": {c: sum(1 for k in changed if c in owner.get(k, [])) for c in
                               sorted({c for v in owner.values() for c in v})}}
    ok = not removed and not unplanned
    return ok, f"vs bm-001: {len(changed)} changed/added, every one owned by a card ({out['diff']['by_card']}); removed {len(removed)}; unplanned {len(unplanned)}"


def g_toc(p, out):
    bounds = sum(1 for n, o, s in p.toc if not o or o + s <= len(p.raw))
    match = sum(1 for n, o, s in p.toc if o and p.dir.get(n) == (o, s))
    nonzero = sum(1 for _, o, _ in p.toc if o)
    a = os.path.join(RC, "aaf")
    sliced = sum(1 for n, o, s in p.toc if o and os.path.exists(os.path.join(a, n))
                 and sha(p.get(n)) == sha(open(os.path.join(a, n), "rb").read()))
    in_tree = sum(1 for n, o, _ in p.toc if o and os.path.exists(os.path.join(a, n)))
    stubs = set(json.load(open(os.path.join(RC, "receipt.json")))["aaf"]["manifest_gaps_inherited"]["dangling"])
    rc_t = tree("bm-RC1")
    edited = [n for n in p.T if n.endswith((".vmodc", ".epe")) and n not in stubs]
    ext_mods = [n for n in edited if not p.T[n][0] and rc_t.get(n) and n in p.dir]
    # an external module is fine only if its bytes are the vanilla ones (else the edit is ignored)
    import bm_rc
    van = eetoc.unaaf(bm_rc.vfs(DIR + OLD + ".ee"))
    V = {n: (o, s) for n, o, s in eetoc.sarc_dir(van)}
    bad_ext = [n for n in ext_mods if n.replace(NEW, OLD) not in V or
               p.raw[p.dir[n][0]:p.dir[n][0] + p.dir[n][1]] != van[V[n.replace(NEW, OLD)][0]:][:V[n.replace(NEW, OLD)][1]]]
    out["toc"] = {"records": len(p.toc), "internal": nonzero, "bounds_ok": bounds, "dir_match": match,
                  "sliced_eq_tree": sliced, "in_tree": in_tree, "edited_external_bad": bad_ext}
    ok = bounds == len(p.toc) and match == nonzero and sliced == in_tree and not bad_ext and p.toc[-1][0].endswith(NEW + ".epe")
    return ok, (f"records {len(p.toc)}, internal {nonzero}, bounds ok {bounds}/{len(p.toc)}, .ee dir match "
                f"{match}/{nonzero}, sliced==tree {sliced}/{in_tree}, edited modules left external with "
                f"non-vanilla bytes {len(bad_ext)}, last record {p.toc[-1][0].split('/')[-1]}")


def g_spec(p, out):
    r = subprocess.run([sys.executable, os.path.join(HERE, "spec_check.py"), "--lights",
                        os.path.join(ROOT, "Working", "Appearance", "build_lights")], capture_output=True, text=True)
    m = json.load(open(os.path.join(ROOT, "Working", "Appearance", "build_lights", "lights_manifest.json")))
    names = sorted({f for l in m["lamps"] for f in l.get("lod_files", [])})
    a = os.path.join(RC, "aaf")
    hits = []
    for n in names:
        cand = [os.path.join(dp, f) for dp, _, fs in os.walk(a) for f in fs if f == os.path.basename(n)]
        src = [os.path.join(dp, f) for dp, _, fs in os.walk(os.path.join(ROOT, "Working", "Appearance", "build_lights"))
               for f in fs if f == os.path.basename(n)]
        hits.append(bool(cand and src and sha(open(cand[0], "rb").read()) == sha(open(src[0], "rb").read())))
    last = (r.stdout.strip().splitlines() or ["?"])[-1]
    out["spec"] = {"spec_check": last, "rc": r.returncode, "light_rbms": len(names), "rbm_equal": sum(hits)}
    return r.returncode == 0 and all(hits) and names, f"spec_check --lights: {last}; light RBMs in the RC hash-equal the manifest's {sum(hits)}/{len(names)}"


def g_budget(p, out):
    import bm_parts
    a = os.path.join(RC, "aaf")
    parts = bm_parts.decode_parts(open(os.path.join(a, bm_parts.MODULE), "rb").read())
    seen = []
    for prt in parts:
        lod = os.path.join(a, prt["model"])
        if os.path.exists(lod):
            for line in open(lod, encoding="utf-8").read().splitlines():
                line = line.strip()
                if line.endswith(".rbm") and line not in seen:
                    seen.append(line)
    files = seen
    used = sum(os.path.getsize(os.path.join(a, n)) for n in seen if os.path.exists(os.path.join(a, n)))
    used_ref, _n = bm_parts.used_model_bytes(a, parts)
    if used_ref != used:
        raise SystemExit(f"budget recount {used} != bm_parts.used_model_bytes {used_ref}")
    import bm_rc
    van = eetoc.unaaf(bm_rc.vfs(DIR + OLD + ".ee"))
    V = {n: van[o:o + s] for n, o, s in eetoc.sarc_dir(van)}
    names = files if isinstance(files, (list, tuple, set)) else []
    shipped = [n for n in names if os.path.exists(os.path.join(a, n)) and V.get(n) == open(os.path.join(a, n), "rb").read()]
    ship_kb = sum(os.path.getsize(os.path.join(a, n)) for n in shipped) / 1024
    tex = sum(s for n, o, s in p.toc if o and n.endswith(".ddsc")) / 1024
    model = used / 1024
    out["budget"] = {"model_kb": round(model, 1), "model_cap_kb": CAP_MODEL, "model_files": len(names),
                     "of_which_shipped_serpente_kb": round(ship_kb, 1), "shipped_files": len(shipped),
                     "batmobile_only_kb": round(model - ship_kb, 1),
                     "texture_resident_kb": round(tex, 1), "texture_cap_kb": CAP_TEX}
    # Calibrated (bm_budget.py): builds that rendered had 3,757-4,657 KB NON-vanilla reachable while their
    # totals incl. vanilla-identical meshes were 6,132-7,032 KB, so the cap applies to the non-vanilla part.
    own_kb = model - ship_kb
    ok = own_kb <= CAP_MODEL and tex <= CAP_TEX
    return ok, (f"Model non-vanilla {own_kb:,.1f} KB of {CAP_MODEL:,.0f} (calibrated: test-091 rendered at 4,657.6) | "
                f"reachable {model:,.1f} KB incl. {len(shipped)} vanilla-identical Serpente meshes {ship_kb:,.1f} KB (shared, not counted) | "
                f"Texture resident {tex:,.1f} KB of {CAP_TEX:,.0f}")


def g_parts(p, out):
    import bm_parts
    raw = p.get(bm_parts.MODULE.replace(OLD, NEW)) or p.get(bm_parts.MODULE)
    if raw is None:
        return False, "parts module not internal in the .toc"
    parts = bm_parts.decode_parts(raw)
    spec = json.load(open(os.path.join(ROOT, "Working", "Parts", "bm_vehicle_parts.json")))
    want = spec["summary"]["parts_after"]
    names = {x.get("name") for x in parts} if isinstance(parts, list) else set(parts)
    a = os.path.join(RC, "aaf")
    lods = [x.get("model") or x.get("lod") for x in parts] if isinstance(parts, list) else []
    resolve = sum(1 for m in lods if m and (os.path.exists(os.path.join(a, m)) or p.T.get(m)))
    out["parts"] = {"decoded": len(parts), "spec": want, "models_resolve": resolve, "models": len([m for m in lods if m])}
    return len(parts) == want and resolve == len([m for m in lods if m]), \
        f"parts module (via .toc) decodes {len(parts)} parts, spec {want}; models resolve {resolve}/{len([m for m in lods if m])}"


def g_adf(p, out):
    a = os.path.join(RC, "aaf")
    rc_t, b1 = tree("bm-RC1"), tree("bm-001")
    mods = [n for n in rc_t if n.endswith(".vmodc") and b1.get(n.replace(NEW, OLD)) != rc_t[n]]
    okn, bad = 0, []
    for n in mods:
        raw = p.get(n) or open(os.path.join(a, n), "rb").read()
        try:
            ad = jc3adf.Adf(raw); list(jc3adf.walk(ad, 0)); okn += 1
        except Exception as e:  # noqa: BLE001
            bad.append((n, str(e)[:80]))
    prof = []
    for n in ("profile/item.onlinec", "profile/task.onlinec", "profile/online.stringlookup"):
        try:
            jc3adf.Adf(open(os.path.join(RC, "drop", n), "rb").read()); prof.append(n)
        except Exception as e:  # noqa: BLE001
            bad.append((n, str(e)[:80]))
    out["adf"] = {"modules": len(mods), "reread": okn, "profile": len(prof), "bad": bad}
    return not bad, f"edited modules re-read {okn}/{len(mods)} (via .toc where internal), profile tables {len(prof)}/3, errors {len(bad)}"


def g_epe(p, out):
    n = DIR + NEW + ".epe"
    raw = p.get(n)
    if raw is None:
        return False, ".epe has no internal record"
    os.makedirs(OUTD, exist_ok=True)
    f1, x1, f2 = (os.path.join(OUTD, x) for x in ("rc.epe", "rc_epe.xml", "rc_rt.epe"))
    open(f1, "wb").write(raw)
    for args in (["--e", f1, x1], ["-i", x1, f2]):
        r = subprocess.run([CONV, *args], capture_output=True, text=True)
        if r.returncode:
            return False, f"ConvertProperty {args[0]} failed"
    same = sha(open(f1, "rb").read()) == sha(open(f2, "rb").read())
    xml = open(x1, encoding="utf-8").read()
    objs = xml.count("<object ")
    want = json.load(open(os.path.join(ROOT, "Working", "Entity", "bm_epe_edits.json")))["counts"]["expected_objects"]
    root = bm_leaf.root_fields(x1)
    out["epe"] = {"roundtrip_identical": same, "objects": objs, "expected_objects_b05": want, "root": root}
    for f in (f1, f2):
        os.remove(f)
    return same and objs >= want and root["name"] == NEW, \
        f"ConvertProperty binary->XML->binary identical={same}; objects {objs} (B-05 expected {want}; B-06/07/08 merged on top); root {root}"


def g_readback(p, out):
    rows, bad, unproven = [], [], []
    a = os.path.join(RC, "aaf")
    xml = open(os.path.join(OUTD, "rc_epe.xml"), encoding="utf-8").read() if os.path.exists(os.path.join(OUTD, "rc_epe.xml")) else ""
    # B-09 health rows: module member values through the .toc
    h = json.load(open(os.path.join(ROOT, "Working", "Damage", "bm_health.json")))
    for r in h["rows"]:
        mod = r["module"].replace(OLD, NEW)
        raw = p.get(mod) or p.get(mod.split("/")[-1])
        if raw is None:
            cand = [n for n in p.T if n.endswith(mod.split("/")[-1])]
            raw = p.get(cand[0]) if cand else None
        if raw is None:
            bad.append((r["row"], "module not internal")); continue
        vals = [v for path, _t, v in jc3adf.walk(jc3adf.Adf(raw), 0) if (path == r["member"] or path.endswith("." + r["member"]) or path.split(".")[-1] == r["member"])]
        to = r["to"]
        got = any((abs(float(v) - float(to)) < 1e-3) if isinstance(v, (int, float)) and isinstance(to, (int, float)) else v == to for v in vals)
        (rows if got else bad).append((r["row"], r["member"], to, vals[:3]))
    # B-05/06/07/08 .epe edits: the edited member carries the 'to' value in the RC .epe
    e = json.load(open(os.path.join(ROOT, "Working", "Entity", "bm_epe_edits.json")))
    no_target = []
    for r in e["edits"]:
        if "to" not in r or re.fullmatch(r"\d+ object\(s\)", str(r.get("to"))):
            no_target.append(f"{r['row']}:{r['node']}"); continue
        mem = r["member"].replace("id:", "")
        to = str(r["to"])
        pat = (rf'(id|name)="{re.escape(mem)}"[^>]*>[^<]*{re.escape(to)}' if to else None)
        if to and re.search(pat, xml):
            rows.append((r["row"], r["member"], to))
        else:
            # the value may be stored as the name's hash
            from rbmhdr import hash_jenkins
            hv = hash_jenkins(to.encode()) if to else None
            alt = re.search(rf'(id|name)="{re.escape(mem)}"[^>]*>(-?\d+)<', xml)
            ref = re.search(rf'(id|name)="{re.escape(mem)}" type="objectid">([0-9A-Fa-f]+)=([0-9A-Fa-f]+)<', xml)
            # an objectid member points at another object: resolve it and compare that object's name
            ref_ok = False
            if ref:
                # objects carry their id as a `_object_id` value right after `<object name="...">`
                ids = {m.group(2).upper(): m.group(1) for m in re.finditer(
                    r'<object name="([^"]+)">\s*<value name="_class"[^>]*>[^<]*</value>\s*'
                    r'<value name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)</value>', xml)}
                ref_ok = ids.get(f"{ref.group(2)}={ref.group(3)}".upper()) == to
            if alt and hv is not None and int(alt.group(2)) & 0xFFFFFFFF == hv:
                rows.append((r["row"], r["member"], to, "as hash"))
            elif ref_ok:
                rows.append((r["row"], r["member"], to, "objectid -> named object"))
            else:
                bad.append((r["row"], r["member"], to))
    for r in e["skipped"]:
        if "UNKNOWN" in r.get("why", ""):
            unproven.append(r.get("name"))
    # B-10 collision, B-13 profile
    phys = p.get("models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc")
    import bm_rc
    phys = phys if phys is not None else open(os.path.join(a, "models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc"), "rb").read()
    (rows if sha(phys) == bm_rc.B10_SHA else bad).append(("B-10", "physicsc sha256", bm_rc.B10_SHA[:12]))
    r = subprocess.run([sys.executable, os.path.join(HERE, "bm_rebel.py"), "--check"], capture_output=True, text=True)
    (rows if r.returncode == 0 else bad).append(("B-13", "bm_rebel --check", (r.stdout.strip().splitlines() or ["?"])[-1]))
    out["readback"] = {"proven": len(rows), "failed": bad, "no_target_in_spec": no_target, "unproven_unknown_not_built": len(unproven),
                       "unproven_names": unproven[:80]}
    json.dump(out["readback"] | {"rows": rows}, open(os.path.join(OUTD, "readback.json"), "w"), indent=1, default=str)
    return not bad and not unproven, (f"values proven {len(rows)}/{len(rows) + len(bad)} (B-09 health, B-05..08 .epe edits, "
                                      f"B-10, B-13); failed {len(bad)}{': ' + str(bad[:3]) if bad else ''}; "
                                      f"no target value in the spec row {len(no_target)} (T-18 light blocks: see spec gate); "
                                      f"unproven {len(unproven)} (B-05 rows skipped as UNKNOWN, never built)")


GATES = [("diff", g_diff), ("toc", g_toc), ("spec", g_spec), ("budget", g_budget), ("parts", g_parts),
         ("adf", g_adf), ("epe", g_epe), ("readback", g_readback)]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gate", nargs="?", default="all")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if not os.path.exists(os.path.join(RC, "receipt.json")):
        print("BLOCKED: Builds/bm-RC1/receipt.json missing"); return 2
    os.makedirs(OUTD, exist_ok=True)
    p, out, lines, red = Pack(), {}, [], 0
    for name, fn in GATES:
        if a.gate not in ("all", name):
            continue
        try:
            ok, msg = fn(p, out)
        except Exception as e:  # noqa: BLE001
            ok, msg = False, f"gate crashed: {type(e).__name__}: {str(e)[:200]}"
        lines.append(f"{'GREEN' if ok else 'RED  '} {name:8s} {msg}")
        print(lines[-1]); red += 0 if ok else 1
    verdict = "ALL GREEN" if not red else f"{red} gate(s) RED"
    print(verdict)
    open(os.path.join(OUTD, "report.md"), "w", encoding="utf-8").write(
        "# V-01 file gates on bm-RC1\n\n`python Tools/scripts/v01_gates.py --check`\n\n```\n" + "\n".join(lines) + f"\n{verdict}\n```\n")
    json.dump(out, open(os.path.join(OUTD, "report.json"), "w"), indent=1, default=str)
    return 0 if not red else 1


if __name__ == "__main__":
    sys.exit(main())

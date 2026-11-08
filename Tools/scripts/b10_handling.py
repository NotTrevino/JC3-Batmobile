"""b10_handling.py - D-10: the handling-value build, and the read-back through the built .toc.

Card: `GRAB_BACKLOG.md` D-10. What this file does, in order:

  1. expands the two machine-readable value lists into one edit file for `t5_apply.py`
     (`Working/Translation/t1_handling_edits.json`):
       * the 35 values over 16 rows of `Working/Translation/t1_edits.json` (already carried
         by the RC4 base - this build re-reads them, it does not re-apply them);
       * the 14 edit entries of `Working/Translation/t1_handling.json` (B-24), which are
         12 rows / 17 concrete members once `front/rear` and the three platform exponents
         are expanded and the unchanged `counter_steer_torque_handbrake` composition is not.
         T-E5 is **not** among them: its drag write (0.55 -> 0.1213) was a balance value
         reverse-engineered from an assumed label, withdrawn by correction 8391 - the member
         keeps T-A2's 0.55 and T-E5 carries a 300-336 km/h labelled band (267 km/h predicted
         terminal at that Cd), so no aero member is written here.
     `old` is the value decoded from `Builds/bm-RC4-base/aaf`, never the ledger's prose;
     a ledger `from` that disagrees with the base is reported, not silently accepted.
  2. builds `Builds/bm-RC4-handling` with `bm_build.py` (which copies the base tree, runs
     `t5_apply.py` - ConvertAdf offset-in-file patching - and packs with `t5_build.py`,
     rebuilding the `.toc`).
  3. reads every edited member back **through the built `.toc`**: the `.toc` record gives
     (offset, size) into the decompressed SARC stream of the `.ee`; that slice is written
     out and decoded with Gibbed ConvertAdf, and the member compared with the target.
     Nothing is read from the `aaf` tree for this check.

Usage:
    python Tools/scripts/b10_handling.py --write
    python Tools/scripts/b10_handling.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import t5_apply as T5  # noqa: E402
from eetoc import read_toc, unaaf  # noqa: E402

TAG = "bm-RC4-handling"
BASE = "bm-RC4-base"
EE = "v0300_car_kensington_sportsmuscle_civilian_01.ee"
BASE_DIR = os.path.join(ROOT, "Builds", BASE)
OUT_DIR = os.path.join(ROOT, "Builds", TAG)
EDITS = os.path.join(ROOT, "Working", "Translation", "t1_handling_edits.json")
CURRENT = os.path.join(ROOT, "Working", "Translation", "rc4_current.json")
SPEC = os.path.join(ROOT, "Working", "Translation", "d10_spec.json")
T1_EDITS = os.path.join(ROOT, "Working", "Translation", "t1_edits.json")
HANDLING = os.path.join(ROOT, "Working", "Translation", "t1_handling.json")
LEDGER = os.path.join(ROOT, "Working", "Translation", "T_ROWS.jsonl")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "build-d10-handling-values.md")
VERIFY = os.path.join(OUT_DIR, "verify")

TOL = T5.TOL

# The B-24 payload, expanded to concrete members. `ledger_old` is what the payload says the
# value is; `measured_exception` marks a member whose base value is known to differ and is
# declared (T-K4's bytes carry 1, its own derivation says so).
PAYLOAD = [
    ("T-G4", "LandGlobal", "ground_clearance", 0.7037, 0.071, "derived", None),
    ("T-ST2", "LandSteering", "t_to_full_steer_s", 0.8, 0.25, "derived", None),
    ("T-ST3", "LandSteering", "max_speed_t_to_full_steer_s", 0.6, 0.091, "derived (R3)", None),
    ("T-ST4", "LandSteering", "steer_input_power_pc", 3, 1, "derived (absence)", None),
    ("T-ST4", "LandSteering", "steer_input_power_durango", 3, 1, "derived (absence)", None),
    ("T-ST4", "LandSteering", "steer_input_power_orbis", 3, 1, "derived (absence)", None),
    ("T-ST6", "LandSteering", "wheel_drift_aligning_strength", 0.3, 0.625,
     "derived (INFERRED reciprocal)", None),
    ("T-K3", "Brakes", "handbrake_friction_factor", 1, 4.0, "derived (R3)", None),
    ("T-K4", "Brakes", "front.min_time_to_block", 5, 0.3, "INFERRED (kind-match)", 1),
    ("T-K4", "Brakes", "rear.min_time_to_block", 5, 0.3, "INFERRED (kind-match)", 1),
    ("T-DR1", "CustomLandGlobal", "drift.min_speed_to_drift_kmph", 10, 0, "derived", None),
    ("T-DR1", "CustomLandGlobal", "drift.steering_sensitivity", 4, 2, "derived", None),
    ("T-E2", "LandEngine", "torque_factor_at_optimal_rpm", 1393.5, 2921, "derived (R3)", None),
    ("T-A3", "LandAerodynamics", "top_speed_drag_coefficient", 2.0, 1.0,
     "derived (absence)", None),
    ("T-B1", "CustomLandGlobal", "arcade.nitro_boost.torque_multiplier", 2.0, 6.3,
     "derived", None),
    ("T-B4", "CustomLandGlobal", "arcade.heat_boost.grip_multiplier", 4.26, 1.5,
     "derived (removes two non-BmAK scales)", None),
    ("T-B4", "CustomLandGlobal", "arcade.nitro_boost_upgraded.extra_top_speed", 100.92, 80,
     "derived (removes two non-BmAK scales)", None),
]


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def load_current() -> dict:
    return json.load(open(CURRENT, encoding="utf-8"))["modules"]


def near(a, b) -> bool:
    return abs(float(a) - float(b)) <= TOL * max(1.0, abs(float(b)))


def ledger_rows() -> dict:
    return {json.loads(l)["id"]: json.loads(l)
            for l in open(LEDGER, encoding="utf-8") if l.strip()}


def bmak_source(rows: dict, rid: str) -> str:
    """The row's own BmAK-side cell, trimmed - never a re-typed number."""
    r = rows.get(rid)
    if not r or len(r["cells"]) < 2:
        return "UNKNOWN (row has no BmAK cell)"
    t = r["cells"][1].replace("\n", " ").strip()
    return t if len(t) <= 220 else t[:217] + "..."


def handling_derivation() -> dict:
    """row+member -> the B-24 derivation string (the BmAK field each number comes from)."""
    out = {}
    for e in json.load(open(HANDLING, encoding="utf-8"))["edits"]:
        out[e["row"]] = e.get("derivation", "")
    return out


def payload_edits() -> tuple[list[dict], list[dict]]:
    """(edits for t5_apply, audit rows) - `old` always measured from the RC4 base."""
    cur = load_current()
    rows = ledger_rows()
    deriv = handling_derivation()
    edits, audit = [], []
    for rid, mod, member, ledger_old, new, conf, exc in PAYLOAD:
        m = cur.get(mod)
        if not m or "values" not in m:
            raise SystemExit(f"{rid}: module {mod} not in {rel(CURRENT)}")
        have = m["values"].get(member, "<<missing>>")
        if not isinstance(have, (int, float)):
            raise SystemExit(f"{rid}: {mod}.{member} not numeric in the base: {have!r}")
        declared = exc if exc is not None else ledger_old
        if not near(have, declared):
            raise SystemExit(f"{rid}: base holds {have!r} for {mod}.{member}; the ledger/payload "
                             f"says {declared!r}. Refusing to write over unexplained drift.")
        if near(have, new):
            raise SystemExit(f"{rid}: {mod}.{member} already reads {new!r} - no-op edit")
        edits.append({"row": rid, "module": mod, "member": member, "old": have,
                      "new": new, "conf": conf, "kind": "number"})
        audit.append({
            "row": rid, "module": mod, "member": member, "file": m["file"],
            "ledger_from": ledger_old, "base": have, "new": new, "conf": conf,
            "ledger_from_matches_base": near(have, ledger_old),
            "bmak_source": bmak_source(rows, rid),
            "derivation": deriv.get(rid, ""),
        })
    return edits, audit


def t1_edits_rows() -> list[dict]:
    doc = json.load(open(T1_EDITS, encoding="utf-8"))
    return [dict(e) for e in doc["edits"]]


def write_edits() -> dict:
    edits, audit = payload_edits()
    doc = {"schema": 1, "card": "D-10", "tag": TAG, "base": rel(BASE_DIR),
           "source": [rel(T1_EDITS), rel(HANDLING)],
           "generated_by": "Tools/scripts/b10_handling.py --write",
           "note": ("The 35 t1_edits values are already in bm-RC4-base and are read back by this "
                    "step, not re-written; these 18 are the B-24 writes this build makes. "
                    "`old` is measured from the base tree, not copied from the ledger."),
           "not_numeric": [],
           "payload_audit": audit, "edits": edits}
    with open(EDITS, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    spec = {"schema": 1, "tag": TAG,
            "steps": [{"applier": "t5_apply", "edits": rel(EDITS), "current": rel(CURRENT)}]}
    with open(SPEC, "w", encoding="utf-8", newline="\n") as f:
        json.dump(spec, f, indent=1)
        f.write("\n")
    return doc


def build() -> None:
    write_edits()
    # t1_apply validates the list against the same snapshot before t5_apply touches a byte
    r = subprocess.run([sys.executable, os.path.join(HERE, "t1_apply.py"),
                        "--edits", EDITS, "--current", CURRENT],
                       capture_output=True, text=True, errors="replace")
    print((r.stdout or "").strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-400:])
    if r.returncode != 0:
        raise SystemExit("t1_apply refused the list:\n" + (r.stdout + r.stderr)[-2000:])
    r = subprocess.run([sys.executable, os.path.join(HERE, "bm_build.py"), "--tag", TAG,
                        "--base", BASE, "--edits", SPEC, "--force"],
                       capture_output=True, text=True, errors="replace")
    print((r.stdout or "").strip()[-4000:])
    if r.returncode != 0:
        raise SystemExit("bm_build failed:\n" + (r.stdout + r.stderr)[-3000:])


def flatten(vmodc: str, td: str) -> dict:
    xml = os.path.join(td, os.path.basename(vmodc) + ".xml")
    T5.decode(vmodc, xml)
    root = ET.fromstring(open(xml, encoding="utf-8-sig").read())
    inst = root.find("instances/instance")
    if inst is None:
        raise SystemExit(f"no instance in {vmodc}")
    return T5.paths(inst)


def readback() -> dict:
    """Every target member, read from the built .ee through the built .toc."""
    cur = load_current()
    ee = os.path.join(OUT_DIR, EE)
    toc = ee + ".toc"
    base_toc = os.path.join(BASE_DIR, EE + ".toc")
    if not os.path.exists(toc):
        raise SystemExit(f"{rel(toc)} missing - run --write")
    stream = unaaf(open(ee, "rb").read())
    recs = {n: (o, s) for n, o, s in read_toc(open(toc, "rb").read())}
    base = {n: (o, s) for n, o, s in read_toc(open(base_toc, "rb").read())}
    payload, audit = payload_edits()
    rows = ledger_rows()
    checks, modules = [], {}

    def target_file(mod: str) -> str:
        m = cur[mod]
        hits = [n for n in recs if n.endswith("/" + m["file"]) or n == m["file"]]
        if len(hits) != 1:
            raise SystemExit(f"{mod}: {len(hits)} .toc records name {m['file']} "
                             f"(a module the .toc does not carry cannot be read back)")
        return hits[0]

    def module_table(name: str) -> dict:
        if name not in modules:
            off, size = recs[name]
            if not off:
                raise SystemExit(f"{name}: offset 0 in the .toc (external, not in this .ee)")
            with tempfile.TemporaryDirectory() as td:
                p = os.path.join(td, os.path.basename(name))
                open(p, "wb").write(stream[off:off + size])
                modules[name] = flatten(p, td)
            if size != len(stream[off:off + size]):
                raise SystemExit(f"{name}: .toc size {size} overruns the stream")
        return modules[name]

    for e in payload:
        name = target_file(e["module"])
        table = module_table(name)
        el = table.get(e["member"])
        if el is None:
            raise SystemExit(f"{e['row']}: {e['member']} missing from the packed {name}")
        got = (el.text or "").strip()
        ok = near(got, e["new"])
        checks.append({"set": "B-24 (written by this build)", "row": e["row"],
                       "module": e["module"], "member": e["member"], "file": name,
                       "want": e["new"], "read_back": float(got), "ok": ok,
                       "size_before": base[name][1] if name in base else None,
                       "size_after": recs[name][1]})

    for e in t1_edits_rows():
        name = target_file(e["module"])
        table = module_table(name)
        el = table.get(e["member"])
        if el is None:
            raise SystemExit(f"{e['row']}: {e['member']} missing from the packed {name}")
        got = (el.text or "").strip()
        checks.append({"set": "t1_edits (already in the base)", "row": e["row"],
                       "module": e["module"], "member": e["member"], "file": name,
                       "want": e["new"], "read_back": float(got), "ok": near(got, e["new"]),
                       "size_before": base[name][1] if name in base else None,
                       "size_after": recs[name][1]})

    receipt = json.load(open(os.path.join(OUT_DIR, "receipt.json"), encoding="utf-8"))
    changed = receipt.get("modules_changed") or []
    payload_files = sorted({c["file"] for c in checks if c["set"].startswith("B-24")})
    untouched_changed = [c for c in changed if c not in payload_files]

    doc = {
        "schema": 1, "card": "D-10", "tag": TAG, "base": rel(BASE_DIR),
        "ee": {"bytes": os.path.getsize(ee),
               "sha256": receipt["ee"]["sha256"]},
        "toc": {"bytes": os.path.getsize(toc), "sha256": receipt["toc"]["sha256"],
                "records": len(recs)},
        "payload_audit": audit,
        "readback": checks,
        "summary": {
            "targets": len(checks),
            "read_back_ok": sum(c["ok"] for c in checks),
            "payload_targets": len(payload),
            "payload_ok": sum(c["ok"] for c in checks if c["set"].startswith("B-24")),
            "pre_existing_targets": len(checks) - len(payload),
            "modules_changed": changed,
            "payload_modules": payload_files,
            "changed_outside_payload": untouched_changed,
            "module_sizes_equal": all(c["size_before"] == c["size_after"] for c in checks
                                      if c["size_before"] is not None),
            "red": [f"{c['row']} {c['module']}.{c['member']}" for c in checks if not c["ok"]],
        },
        "rows": rows_of_interest(rows),
    }
    os.makedirs(VERIFY, exist_ok=True)
    with open(os.path.join(VERIFY, "d10_readback.json"), "w", encoding="utf-8",
              newline="\n") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    return doc


def rows_of_interest(rows: dict) -> dict:
    items = [r for r in rows.values() if r["dispo"] == "next"]
    return {
        "ledger_total": len(rows),
        "next": len(items),
        "next_with_machine_edits": sum(1 for r in items if r.get("edits")),
        "next_ids": [r["id"] for r in items],
        "edit_rows": sum(1 for r in rows.values() if r["dispo"] == "edit"),
        "keep_rows": sum(1 for r in rows.values() if r["dispo"] == "keep"),
    }


def report(doc: dict, audit: list[dict]) -> str:
    s = doc["summary"]
    rb = {f"{c['row']}|{c['module']}.{c['member']}": c for c in doc["readback"]}
    bu = {f"{a['row']}|{a['module']}.{a['member']}": a for a in audit}
    L = []
    L.append("# D-10 - the handling-value build (`Builds/bm-RC4-handling`)")
    L.append("")
    L.append(f"Generated by `Tools/scripts/b10_handling.py --write`; `--check` rebuilds the edit "
             f"list, re-reads the built `.toc` and compares `verify/d10_readback.json`.")
    L.append("")
    L.append(f"**STATUS: {s['read_back_ok']}/{s['targets']} values read back through the built "
             f"`.toc`; {s['payload_ok']}/{s['payload_targets']} are the writes this build makes; "
             f"{len(s['modules_changed'])} module(s) changed; red: "
             f"{', '.join(s['red']) if s['red'] else 'none'}.**")
    L.append("")
    L.append(f"Build: `{doc['tag']}`, base `{doc['base']}`, `.ee` {doc['ee']['bytes']:,} B "
             f"sha256 `{doc['ee']['sha256'][:16]}...`, `.toc` {doc['toc']['bytes']:,} B / "
             f"{doc['toc']['records']} records. Nothing was installed or launched.")
    L.append("")
    L.append("## 1. Scope: what the ledger actually queues (and what it does not)")
    L.append("")
    r = doc["rows"]
    L.append(f"The review's correction holds: the ledger has **{r['next']} `next` rows**, not 40 "
             f"(of {r['ledger_total']} rows: {r['edit_rows']} `edit`, {r['keep_rows']} `keep`, plus "
             f"blocked/epe/out/superseded). But **{r['next_with_machine_edits']} of those "
             f"{r['next']} rows carry a machine edit** (`edits: []` on every one of them): they are "
             f"prose values, cards waiting on a phase-Q take, or rows whose member is already in "
             f"the `edit` set. So there is no hidden 109-value payload to apply - a number with no "
             f"`(module, member, old, new)` record cannot be written without inventing it.")
    L.append("")
    L.append(f"Concretely, this step applies:")
    L.append("")
    L.append(f"* the **{len(audit)} B-24 members** over 12 rows (the 14 payload entries expand to 17 "
             f"because `front/rear.min_time_to_block` is two members and the three "
             f"`steer_input_power_*` platforms are three; "
             f"`counter_steer_torque_handbrake` is 30000 unchanged - a composition, not an edit);")
    L.append(f"* and it **re-reads the 35 `t1_edits` values over 16 rows** that the RC4 base already "
             f"carries. They are not re-written: the base decodes them at the ledger's `new` value, "
             f"and re-applying them would be a no-op `t5_apply` refuses.")
    L.append("")
    L.append("`T-ST7`'s 0.25 s is `T-ST2`'s member (`t_to_full_steer_s`): the row ruling is applied "
             "here as 0.25 s; the turning-circle re-derivation is still open (F3 - "
             "`v05_driving.py --check` fails on the old blocked pin).")
    L.append("")
    L.append(f"## 2. The {len(audit)} writes, with their BmAK source")
    L.append("")
    L.append("| row | module.member | base (measured) | new | class | read back | match | "
             "module size before -> after |")
    L.append("|---|---|---|---|---|---|---|---|")
    for e in sorted(audit, key=lambda x: (x["row"], x["member"])):
        c = rb[f"{e['row']}|{e['module']}.{e['member']}"]
        L.append(f"| `{e['row']}` | `{e['module']}.{e['member']}` | {e['base']} | {e['new']} | "
                 f"{e['conf']} | {c['read_back']} | {'PASS' if c['ok'] else 'RED'} | "
                 f"{c['size_before']} -> {c['size_after']} |")
    L.append("")
    L.append("### The BmAK source of each number")
    L.append("")
    for e in sorted(audit, key=lambda x: (x["row"], x["member"])):
        L.append(f"* **`{e['row']}` {e['module']}.{e['member']} = {e['new']}** - {e['bmak_source']}")
        if e["derivation"]:
            L.append(f"  * derivation: {e['derivation']}")
    L.append("")
    L.append("## 3. The 35 pre-existing edit values, read back from the same packed `.toc`")
    L.append("")
    L.append("| row | module.member | value | read back | match |")
    L.append("|---|---|---|---|---|")
    for c in doc["readback"]:
        if not c["set"].startswith("B-24"):
            L.append(f"| `{c['row']}` | `{c['module']}.{c['member']}` | {c['want']} | "
                     f"{c['read_back']} | {'PASS' if c['ok'] else 'RED'} |")
    L.append("")
    L.append("These were applied in the lineage before `bm-RC4-base` (the base decodes every one at "
             "the ledger's `new`). Reading them back here proves the pack/`.toc` round trip did not "
             "disturb them.")
    L.append("")
    L.append("## 4. What the read-back actually reads")
    L.append("")
    L.append("`verify/d10_readback.json` is produced by taking the built `.ee.toc`, finding the "
             "record for each target module, slicing the decompressed `.ee` SARC stream at that "
             "record's `(offset, size)`, writing the slice to a temporary `.vmodc` and decoding it "
             "with Gibbed ConvertAdf. The `aaf` tree is not consulted - a stale tree would not "
             "pass. `t5_build.py`'s own guard (every internal `.toc` record equals its `.ee` "
             "member, record list identical to the base) runs inside the build.")
    L.append("")
    L.append("## 5. Findings")
    L.append("")
    mismatch = [a for a in audit if not a["ledger_from_matches_base"]]
    for a in mismatch:
        L.append(f"1. **`{a['row']}`'s ledger `from` ({a['ledger_from']}) is not the build value "
                 f"({a['base']}).** The row's own derivation says the bytes already carry "
                 f"{a['base']} (T-K2), so the build value is what was used; the ledger cell still "
                 f"reads {a['ledger_from']} and should say `{a['base']} -> 0.3`. This is a ledger "
                 f"label drift, not a build fault.")
    L.append(f"2. **`T-E5` is a labelled band, not a translation, and the drag is not tuned to it.** "
             f"336.4 km/h is the operator's signed-off 2026-10-23 wiki figure, carried as the top of "
             f"a **300-336 km/h** band labelled `assumed`, not as a measured speed. This build does "
             f"**not** write `drag_coefficient`: the 0.1213 that used to be written here was "
             f"reverse-engineered to make the label reachable and is withdrawn (correction 8391). "
             f"The member keeps `T-A2`'s class fit 0.55 and reads back at 0.55; at `T-E2`'s 894.7 kW "
             f"that predicts a **267 km/h** terminal (74.2 m/s, rho 1.2), which is what a take "
             f"compares with - a top-speed take tests reachability of a label, not fidelity to BmAK. "
             f"The arithmetic also retires the old numbers: 0.1213 x 6.635 = 0.805 m^2 needs only "
             f"394 kW at 93.44 m/s, and the 260 km/h the old cell quoted did not follow from its own "
             f"inputs either (336.4 km/h at 894.7 kW needs Cd 0.276).")
    L.append(f"3. **Declared out-of-domain values:** `T-ST3` 0.091 s is below the 0.2 s fleet "
             f"minimum (R3); `T-ST6` 0.625 is an INFERRED reciprocal with falsifier 0.48; `T-K3` "
             f"4.0 sits above the 6 t band 1..2.25. All three are labelled in their cells.")
    L.append(f"4. **`T-G4` 0.071 m is a probe, not a decoded consumer** (Q2-A6). It is written and "
             f"read back; what `land_global.ground_clearance` controls is still UNKNOWN.")
    L.append("")
    L.append("## 6. Checks run")
    L.append("")
    L.append("```bash")
    L.append("python Tools/scripts/t1_apply.py --edits Working/Translation/t1_handling_edits.json "
             "--current Working/Translation/rc4_current.json")
    L.append("python Tools/scripts/bm_build.py --tag bm-RC4-handling --base bm-RC4-base "
             "--edits Working/Translation/d10_spec.json")
    L.append("python Tools/scripts/b10_handling.py --check")
    L.append("python Tools/scripts/bm_build.py --tag bm-RC4-handling --check")
    L.append("```")
    L.append("")
    L.append("## 7. Limits")
    L.append("")
    L.append("* No install and no game: the values are proven in the packed file, not in play. "
             "Whether 0.25 s / 0.091 s are honoured or filtered by the engine is UNKNOWN (test "
             "ban) - neither is measured.")
    L.append("* `T-E5`'s label and `T-G4`'s consumer, above.")
    L.append("* The 109 `next` rows that carry no edit record were not written: they need a card "
             "or a take first, and inventing members would break R4/R5.")
    L.append("")
    return "\n".join(L)


def write_report() -> dict:
    doc = readback()
    md = report(doc, doc["payload_audit"])
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8", newline="\n") as f:
        f.write(md)
    with open(os.path.join(VERIFY, "d10_readback.md"), "w", encoding="utf-8",
              newline="\n") as f:
        f.write(md)
    return doc


def check() -> int:
    doc = readback()
    s = doc["summary"]
    on_disk = os.path.join(VERIFY, "d10_readback.json")
    if not os.path.exists(on_disk):
        print("FAIL: verify/d10_readback.json missing (run --write)")
        return 1
    prev = json.load(open(on_disk, encoding="utf-8"))
    if prev != json.loads(json.dumps(doc)):
        print("FAIL: verify/d10_readback.json no longer matches the packed build")
        return 1
    if s["read_back_ok"] != s["targets"] or s["red"]:
        print(f"FAIL: {s['read_back_ok']}/{s['targets']} read back; red: {s['red']}")
        return 1
    if s["changed_outside_payload"]:
        print(f"FAIL: modules changed outside the payload: {s['changed_outside_payload']}")
        return 1
    print(f"CHECK PASS - {s['read_back_ok']}/{s['targets']} read back through the .toc "
          f"({s['payload_ok']}/{s['payload_targets']} payload), "
          f"{len(s['modules_changed'])} module(s) changed, sizes equal "
          f"{s['module_sizes_equal']}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--write", action="store_true", help=f"build Builds/{TAG} and read back")
    ap.add_argument("--check", action="store_true", help="re-read the packed build, no writes")
    a = ap.parse_args()
    if not (a.write or a.check):
        ap.print_help()
        return 2
    if a.write:
        build()
        doc = write_report()
        s = doc["summary"]
        print(f"{s['read_back_ok']}/{s['targets']} read back through the .toc, "
              f"{s['payload_ok']}/{s['payload_targets']} payload, red: "
              f"{', '.join(s['red']) if s['red'] else 'none'}")
        print(f"report -> {rel(REPORT)}")
        return 0
    return check()


if __name__ == "__main__":
    raise SystemExit(main())

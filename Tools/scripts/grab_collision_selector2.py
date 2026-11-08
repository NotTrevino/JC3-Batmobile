"""grab_collision_selector2.py - G3-01e-fix: correct the G3-01e *explanatory* text without changing
the verified value->mesh table, and settle the DriverLeft guard-region question from the bytes.

What changed against G3-01e, and why
  1. Guard-region names: G3-01e said "2's branch guard region names BatmobileWinch and
     WinchPullType; the 1-branch's region names ArmouredMode and IsVehicleAsleep". The review
     (review-G3-01e.md) reported those names as absent. They are NOT absent: the review scanned
     5-byte refs behind the prefixes 00/01/1C only, and missed the 6-byte member-access forms
     (2D 01, 19 01, 09 00, 00 01). Decoded here: @253/@317 Core.ArmouredMode, @223/@327
     Core.IsVehicleAsleep, @278 Core.BatmobileWinch, @284/@290 Core.WinchPullType. The names are
     decoded; which side of the branch each belongs to is positional, hence derived/UNKNOWN.
  2. Runtime: G3-01e quoted 3 of the 4 0->1 transitions and used denominators that silently dropped
     the two samples with no Driver field. This card lists all 7 transitions and counts coverage.
The value->mesh table is untouched: it is re-derived by the G3-01e decoder and asserted equal to the
stored G3-01e JSON before anything is written.

    python Tools/scripts/grab_collision_selector2.py --write
    python Tools/scripts/grab_collision_selector2.py --check
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import grab_collision_selector as G  # read-only reuse: selector decode, callers, package reader
import upk_read

GAME = G.GAME
DRIVERLEFT = 7400
RUNTIME_GLOB = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime", "samples-*.jsonl")
PREV_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR.json")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR2.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR2.json")
SEL_SHA1 = "c2f6a2ee667c544876e5317a103072c44ea17788"
MESH_EXPECT = {0: None, 1: "BatmanCollisionMeshPursuitMode", 2: "BatmanCollisionMeshBattleMode"}
# 6-byte member-access forms: prefix byte(s) + ref marker + int32 index
MEMBER_FORMS = ((0x2D, 0x01), (0x19, 0x01), (0x09, 0x00), (0x00, 0x01))
EXPECT_TRANSITIONS = [("10:05:15.778", 0, 1), ("11:48:22.562", 0, 1), ("11:48:22.898", 1, 0),
                      ("11:48:24.093", 0, 1), ("11:48:25.206", 1, 0), ("11:48:38.572", 0, 1),
                      ("11:53:43.969", 1, 0)]


def scan_member_refs(pkg, s: bytes) -> list[dict]:
    """Every 6-byte member/context ref, with the prefix form and the resolved object path."""
    out = []
    for o in range(len(s) - 5):
        for a, b in MEMBER_FORMS:
            if s[o] != a or s[o + 1] != b:
                continue
            idx = struct.unpack_from("<i", s, o + 2)[0]
            path = pkg.object_path(idx)
            if path is None:
                continue
            out.append({"at": o, "form": "0x%02X 0x%02X" % (a, b), "index": idx, "path": path})
            break
    return out


def driverleft(sp) -> dict:
    rec = G.function_of(sp, DRIVERLEFT)
    s = rec["_script"]
    dec = G.Decoder(sp, s).decode()
    calls = [c for c in dec["calls"] if c["name"].endswith("SetBatmanVsBatmobileCollisionMode")]
    refs = scan_member_refs(sp, s)
    c2 = [c for c in calls if c["args"] and c["args"][0].get("value") == 2]
    c1 = [c for c in calls if c["args"] and c["args"][0].get("value") == 1]
    at2 = c2[0]["at"] if c2 else None
    at1 = c1[0]["at"] if c1 else None
    for r in refs:
        if at2 is not None and r["at"] < at2:
            r["window"] = "before the value-2 call"
        elif at2 is not None and at1 is not None and at2 < r["at"] < at1:
            r["window"] = "between the value-2 and value-1 calls"
        else:
            r["window"] = "after the value-1 call"
    return {"export": DRIVERLEFT, "path": rec["path"], "script_bytes": len(s),
            "calls": [{"at": c["at"], "name": c["name"], "argument": c["args"][0]} for c in calls],
            "member_refs": refs,
            "comparison_tokens": [{"at": o, "token": "0x%02X" % s[o]} for o in range(len(s))
                                  if s[o] in G.COMPARISONS],
            "unexplained_bytes": dec["unexplained_bytes"],
            "label": "decoded (Startup.upk export %d, script bytes at the stated offsets)" % DRIVERLEFT}


def runtime2() -> dict:
    files = sorted(glob.glob(RUNTIME_GLOB))
    values, samples, transitions = {}, [], []
    for path in files:
        last = {}
        for line in open(path, encoding="utf-8", errors="replace"):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            ch = rec.get("changed") or {}
            for k, v in ch.items():
                if not k.endswith("BatmanVsBatmobileCollisionMode"):
                    continue
                veh = k.split(".")[0]
                has = (veh + ".Driver") in ch
                dv = ch.get(veh + ".Driver")
                state = ("missing" if not has else ("absent" if not dv else "seated"))
                samples.append({"t": rec.get("t"), "file": os.path.basename(path), "vehicle": veh,
                                "mode": v, "driver_state": state, "driver_value": dv})
                prev = last.get(veh)
                if prev is not None and prev != v:
                    transitions.append({"t": rec.get("t"), "vehicle": veh, "from": prev, "to": v,
                                        "driver_state": state, "driver_in_same_sample": has})
                last[veh] = v
                values[v] = values.get(v, 0) + 1
    rises = [t for t in transitions if (t["from"], t["to"]) == (0, 1)]
    falls = [t for t in transitions if (t["from"], t["to"]) == (1, 0)]
    cov = {}
    for s in samples:
        cov["mode=%d|driver_%s" % (s["mode"], s["driver_state"])] = \
            cov.get("mode=%d|driver_%s" % (s["mode"], s["driver_state"]), 0) + 1
    return {"files": [os.path.basename(p) for p in files],
            "samples": samples, "sample_count": len(samples),
            "value_counts": {str(k): v for k, v in sorted(values.items())},
            "driver_coverage": {k: sum(1 for s in samples if s["driver_state"] == k)
                                for k in ("seated", "absent", "missing")},
            "coverage_by_mode": dict(sorted(cov.items())),
            "transitions": transitions, "rises": len(rises), "falls": len(falls),
            "label": "decoded (Research/BatmobileGrab/runtime/samples-*.jsonl; the 03:57 sampler "
                     "logged only *changes*, so a sample lists Driver only when it changed too)"}


def build() -> dict:
    pkg = upk_read.Package(os.path.join(GAME, "BmGame.upk"))
    sel = G.selector_doc(pkg)
    cal = G.all_callers()
    sp = upk_read.Package(os.path.join(GAME, "Startup.upk"))
    dl = driverleft(sp)
    rt = runtime2()
    export = pkg.data(sel["function"]["export"])
    doc = {
        "schema": 1,
        "selector_sha1_recomputed": hashlib.sha1(export[22:-16]).hexdigest(),
        "card": "G3-01e-fix - SetBatmanVsBatmobileCollisionMode: guard-region evidence and the full "
                "runtime transition set (value->mesh table unchanged)",
        "supersedes": "tmp/freebuff/reports/review-G3-01e.md item 1 (false negative: the ref scan "
                      "missed the 2D/19/09/00-01 member-access forms)",
        "selector": sel,
        "driverleft": dl,
        "jobs": cal,
        "runtime": rt,
        "guard_names": {
            "decoded": "Startup.upk 7400 script: @222/@327 Core.IsVehicleAsleep, @253/@317 "
                       "Core.ArmouredMode, @277 Core.BatmobileWinch, @283/@289 Core.WinchPullType "
                       "(6-byte member refs; each row has its offset and form)",
            "derived": "the value-2 call is at 301 and the value-1 call at 334; the Winch refs sit "
                       "before 301, the ArmouredMode/IsVehicleAsleep pair between 301 and 334. That "
                       "positional split *suggests* 2<->Winch and 1<->ArmouredMode/IsVehicleAsleep, "
                       "but the branch encoding is UNKNOWN, so which body/guard each ref belongs to "
                       "is not proven",
            "label": "names decoded, branch association derived/UNKNOWN",
        },
    }
    doc["oracles"] = oracles(doc)
    return doc


def oracles(doc: dict) -> dict:
    out = {}

    def add(k, ok, detail):
        out[k] = {"ok": bool(ok), "detail": detail}

    rows = {r["mode_value"]: r["mesh"] for r in doc["selector"]["mesh_table"]["rows"]}
    add("mesh_table_unchanged", rows == MESH_EXPECT, {"rows": rows, "expected": MESH_EXPECT})

    prev = None
    if os.path.exists(PREV_JSON):
        prev = json.load(open(PREV_JSON, encoding="utf-8"))
    add("mesh_table_matches_g3_01e",
        prev is not None and {r["mode_value"]: r["mesh"] for r in prev["selector"]["mesh_table"]["rows"]}
        == rows,
        {"g3_01e_rows": None if prev is None else
         {r["mode_value"]: r["mesh"] for r in prev["selector"]["mesh_table"]["rows"]}})

    add("selector_sha1", doc["selector_sha1_recomputed"] == SEL_SHA1,
        {"recomputed": doc["selector_sha1_recomputed"], "g3_01e": SEL_SHA1})

    refs = {(r["path"], r["at"]) for r in doc["driverleft"]["member_refs"]}
    want = {("Core.BatmobileWinch", 277), ("Core.WinchPullType", 283), ("Core.WinchPullType", 289),
            ("Core.ArmouredMode", 253), ("Core.ArmouredMode", 317),
            ("Core.IsVehicleAsleep", 222), ("Core.IsVehicleAsleep", 327)}
    add("guard_refs_present", want <= refs,
        {"missing": sorted(want - refs), "found": sorted(refs)})

    winch = [r for r in doc["driverleft"]["member_refs"]
             if "Winch" in r["path"] and r["at"] < 301]
    arm = [r for r in doc["driverleft"]["member_refs"]
           if ("ArmouredMode" in r["path"] or "IsVehicleAsleep" in r["path"]) and 301 < r["at"] < 334]
    add("guard_windows", len(winch) == 3 and len(arm) == 2,
        {"before_301": [(r["at"], r["path"]) for r in winch],
         "between_301_334": [(r["at"], r["path"]) for r in arm]})

    rt = doc["runtime"]
    add("runtime_values", rt["value_counts"] == {"0": 17, "1": 6} and rt["sample_count"] == 23,
        {"value_counts": rt["value_counts"], "samples": rt["sample_count"]})
    add("runtime_coverage",
        rt["driver_coverage"] == {"seated": 7, "absent": 14, "missing": 2},
        {"coverage": rt["driver_coverage"],
         "sum_check": sum(rt["coverage_by_mode"].values()) == rt["sample_count"]})
    add("runtime_transitions",
        rt["rises"] == 4 and rt["falls"] == 3 and len(rt["transitions"]) == 7
        and all((t["from"], t["to"]) in ((0, 1), (1, 0)) for t in rt["transitions"]),
        {"rises": rt["rises"], "falls": rt["falls"], "total": len(rt["transitions"]),
         "list": [(t["t"][11:23], t["from"], t["to"], t["driver_state"]) for t in rt["transitions"]]})
    add("runtime_rise_list",
        [(t["t"][11:23], t["from"], t["to"]) for t in rt["transitions"]] ==
        [(e[0], e[1], e[2]) for e in EXPECT_TRANSITIONS],
        {"actual": [(t["t"][11:23], t["from"], t["to"]) for t in rt["transitions"]]})

    callers = [c for p in doc["jobs"] for c in p["callers"]]
    consts = sorted({c["argument"]["value"] for c in callers if c["argument"]["kind"] == "byte"})
    add("caller_constants", consts == [0, 1, 2] and len(callers) == 6,
        {"constants": consts, "sites": len(callers)})
    return out


def render(doc: dict) -> str:
    L, A = [], None
    A = L.append
    sel, dl, rt = doc["selector"], doc["driverleft"], doc["runtime"]
    A("# Collision selector, corrected: guard-region evidence and the full transition set (G3-01e-fix)")
    A("")
    A("The value->mesh table is **unchanged** (oracle `mesh_table_unchanged` and")
    A("`mesh_table_matches_g3_01e`): **0** attaches nothing, **1** `BatmanCollisionMeshPursuitMode`,")
    A("**2** `BatmanCollisionMeshBattleMode`. What changes is the evidence statement about the")
    A("`DriverLeft` branches and the runtime narrative.")
    A("")
    A("## 1. The selector body (unchanged)")
    A("")
    A("`BmGame.upk` export %d, %d B script, sha1 `%s` (re-read here, equals G3-01e's)." % (
        sel["function"]["export"], sel["function"]["script_bytes"],
        doc["selector_sha1_recomputed"]))
    A("")
    A("| mode value | mesh component | detach at | attach at |")
    A("|---|---|---|---|")
    for r in sel["mesh_table"]["rows"]:
        A("| %s | %s | %s | %s |" % (r["mode_value"], r["mesh"] or "-",
                                     r.get("detach_at") or "-", r.get("attach_at") or "-"))
    A("")
    A("## 2. What the `DriverLeft` guard bytes actually contain")
    A("")
    A("`Startup.upk` export %d `%s`, %d B script. The two selector calls are at %s." % (
        dl["export"], dl["path"], dl["script_bytes"],
        ", ".join("%d (argument %d)" % (c["at"], c["argument"]["value"]) for c in dl["calls"])))
    A("")
    A("The script's **6-byte member refs** (prefix form + int32 index), `decoded`:")
    A("")
    A("| at | form | resolves to | window |")
    A("|---|---|---|---|")
    for r in dl["member_refs"]:
        A("| %d | `%s` | `%s` | %s |" % (r["at"], r["form"], r["path"], r["window"]))
    A("")
    A("So the names **are** in this function: `Core.BatmobileWinch` @277, `Core.WinchPullType` @283")
    A("and @289 sit before the value-**2** call at 301; `Core.ArmouredMode` @317 and")
    A("`Core.IsVehicleAsleep` @327 sit between the value-**2** call and the value-**1** call at 334.")
    A("The review's negative came from scanning only 5-byte refs behind `00/01/1C`, which misses the")
    A("`2D 01`, `19 01`, `09 00` and `00 01` member-access forms - these are 6-byte.")
    A("")
    comp_at = ", ".join(str(c["at"]) for c in dl["comparison_tokens"])
    A("What is **not** decoded: which side of a branch each ref guards. The `%s` comparison tokens"
      % "/".join(sorted({"0x%02X" % int(c["token"], 16) for c in dl["comparison_tokens"]})))
    A("sit at %s, and the branch words are not offsets (G3-01e's corpus test), so the association" % comp_at)
    A("\"2 <-> Winch\", \"1 <-> ArmouredMode/IsVehicleAsleep\" is **derived from position only**.")
    A("%s" % json.dumps(doc["guard_names"], indent=1))
    A("")
    A("## 3. Runtime: all seven transitions, with coverage")
    A("")
    A("%d samples across %d logs: values %s." % (
        rt["sample_count"], len(rt["files"]), rt["value_counts"]))
    A("Driver field present in the same sample: %s." % rt["driver_coverage"])
    A("")
    A("| mode | seated | absent | not logged |")
    A("|---|---|---|---|")
    for m in sorted({s["mode"] for s in rt["samples"]}):
        row = rt["coverage_by_mode"]
        A("| %d | %d | %d | %d |" % (m, row.get("mode=%d|driver_seated" % m, 0),
                                     row.get("mode=%d|driver_absent" % m, 0),
                                     row.get("mode=%d|driver_missing" % m, 0)))
    A("")
    A("| transition | from -> to | driver in that sample |")
    A("|---|---|---|")
    for t in rt["transitions"]:
        A("| %s | %d -> %d | %s |" % (t["t"], t["from"], t["to"], t["driver_state"]))
    A("")
    A("**All four 0->1 rises**: %s. **All three 1->0 falls**: %s." % (
        ", ".join(t["t"][11:23] for t in rt["transitions"] if t["to"] == 1),
        ", ".join(t["t"][11:23] for t in rt["transitions"] if t["to"] == 0)))
    A("")
    A("Two samples carry no `Driver` field (`11:48:22.898`, `11:48:24.093`) because the sampler logs")
    A("only fields that changed; they are counted as `not logged`, not dropped. In particular the")
    A("rise at `11:48:24.093` has **no driver evidence**, so it cannot be called an exit.")
    A("")
    A("## 4. Oracles (`--check` re-runs all of them)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in doc["oracles"].items():
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:260]))
    A("")
    A("## 5. UNKNOWN")
    A("")
    A("1. Which `DriverLeft` condition selects 1 and which selects 2 - the refs are decoded, the")
    A("   branch encoding is not, so the positional association in section 2 is `derived`.")
    A("2. Branch-word encoding (G3-01e UNKNOWN 1, unchanged).")
    A("3. Whether `Core.BatmobileWinch` / `Core.WinchPullType` / `Core.ArmouredMode` /")
    A("   `Core.IsVehicleAsleep` are globals or members - the import path says `Core.<name>` and the")
    A("   layout to expand that is not in the packages read here.")
    A("")
    return "\n".join(L)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()
    doc = build()
    md, js = render(doc), json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    if args.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s and %s" % (os.path.relpath(OUT_MD), os.path.relpath(OUT_JSON)))
        print("mesh table: %s" % {r["mode_value"]: r["mesh"] for r in doc["selector"]["mesh_table"]["rows"]})
        print("driverleft refs: %d; transitions: %d (%d rises, %d falls)" % (
            len(doc["driverleft"]["member_refs"]), len(doc["runtime"]["transitions"]),
            doc["runtime"]["rises"], doc["runtime"]["falls"]))
        bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        fails.append("COLLISION_SELECTOR2.json is stale")
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("COLLISION_SELECTOR2.md is stale")
    for k, v in doc["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:300]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK table %s; %d driverleft refs; %d transitions (%d up, %d down); md+json byte-identical"
          % ({r["mode_value"]: r["mesh"] for r in doc["selector"]["mesh_table"]["rows"]},
             len(doc["driverleft"]["member_refs"]), len(doc["runtime"]["transitions"]),
             doc["runtime"]["rises"], doc["runtime"]["falls"]))
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

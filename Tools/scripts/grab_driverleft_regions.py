"""grab_driverleft_regions.py - card DRIVERLEFT-regions.

Settles the one `decoded` claim in G3-01e that its own function contradicts: that the two
`DriverLeft` selector-call sites guard on `BatmobileWinch`/`WinchPullType` and on
`ArmouredMode`/`IsVehicleAsleep`. It also re-derives the collision-mode 0 -> 1 transitions from the
sampler logs (G3-01e's narrative dropped one) and says which statements of
`COLLISION_SELECTOR2.md` survive.

Decoded here, with the project reader (`Tools/scripts/upk_read.py`, imported unmodified):
  * `Startup.upk` export 7400 (`RVehicleBatmobile.DriverLeft`): 368 B ScriptText, every reference
    scanned independently and cross-checked against the 28 published reference offsets; the calls
    (0x1B FName) and the two comparison tokens (0x9A/0x9B) are located, and every reference is
    assigned to the call-site region it sits in (before the value-2 call at 301, between 301 and
    334, after 334).
  * the caller constants: which function passes 0, 1 and 2 to
    `SetBatmanVsBatmobileCollisionMode` in `BmGame.upk` and `Startup.upk`.
  * every collision-mode transition in `Research/BatmobileGrab/runtime/samples-*.jsonl`, with the
    log file and line number, so the four 0 -> 1 rises can be named exactly.

Region assignment is a position, not a control-flow branch: the branch word encoding is UNKNOWN
(G3-01e), so the card reports positions and says so, and it does not restate the association the
review rejected.

    python Tools/scripts/grab_driverleft_regions.py --write
    python Tools/scripts/grab_driverleft_regions.py --check    # rebuilds and byte-compares

Read-only inputs: the two packages, the sampler logs, `DRIVERLEFT_7400.md` and
`COLLISION_SELECTOR2.md` (the claims under adjudication), `Tools/scripts/upk_read.py`.
Output: `Research/BatmobileGrab/DRIVERLEFT_REGIONS.md`. Nothing else is written.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import upk_read as U  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
STARTUP = os.path.join(GAME, "Startup.upk")
BMGAME = os.path.join(GAME, "BmGame.upk")
LOGS = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime", "samples-*.jsonl")
DL7400_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVERLEFT_7400.md")
SEL2_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR2.md")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVERLEFT_REGIONS.md")

DL_EXPORT = 7400
SEL_EXPORT = 10894
SEL_FN = "SetBatmanVsBatmobileCollisionMode"
MESH = {1: "BatmanCollisionMeshPursuitMode", 2: "BatmanCollisionMeshBattleMode"}

# the 28 reference token offsets this script must reproduce from the bytes on its own
EXPECTED_REFS = [5, 21, 43, 54, 61, 70, 76, 82, 88, 94, 100, 149, 155, 161, 167, 173, 179,
                 223, 230, 254, 263, 278, 284, 290, 318, 328, 344, 351]
# the four names G3-01e attributed to the two branches, as (name, expected token offsets)
FOUR = {"Core.ArmouredMode": [254, 318], "Core.BatmobileWinch": [263, 278],
        "Core.WinchPullType": [284, 290], "Core.IsVehicleAsleep": [223, 328]}
# the published loader constants: function -> constants passed
EXPECTED_CALLERS = {"DriverEnter": {0}, "OnWakeRBPhysics": {0}, "StartSelfDrive": {0},
                    "OnSleepRBPhysics": {1}, "DriverLeft": {1, 2}}
# the four rises COLLISION_SELECTOR2.md names (read when the logs held 23 mode samples)
FOUR_RISES = ["2026-11-03T10:05:15.778Z", "2026-11-03T11:48:22.562Z",
              "2026-11-03T11:48:24.093Z", "2026-11-03T11:48:38.572Z"]


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def i32(s: bytes, o: int) -> int:
    return struct.unpack_from("<i", s, o)[0]


def script_of(data: bytes) -> bytes:
    return data[22:len(data) - 16]


# ------------------------------------------------------------------ DriverLeft export + references
def refs_of(pkg, script: bytes) -> tuple[list[dict], int]:
    """Every 5-byte reference `00|01|02 <int32>` in the script, resolved. Returns (refs, raw_hits)."""
    hits = []
    for o in range(0, len(script) - 4):
        if script[o] not in (0x00, 0x01, 0x02):
            continue
        idx = i32(script, o + 1)
        if idx == 0:
            continue
        path = pkg.object_path(idx)
        if path is None:
            continue
        hits.append({"at": o, "form": "0x%02X" % script[o], "index": idx, "path": path,
                     "class": pkg.object_class(idx),
                     "prefix_byte": ("0x%02X" % script[o - 1]) if o else None})
    # drop hits that start inside an earlier hit's 5-byte extent
    kept, last = [], -1
    for h in hits:
        if h["at"] <= last:
            continue
        kept.append(h)
        last = h["at"] + 4
    return kept, len(hits)


def calls_of(pkg, script: bytes) -> list[dict]:
    """0x1B virtual calls (FName) and 0x1C final calls (export), with a byte argument if present."""
    out = []
    for o in range(0, len(script) - 4):
        t = script[o]
        if t not in (0x1B, 0x1C):
            continue
        idx = i32(script, o + 1)
        if t == 0x1B:
            if not (0 <= idx < pkg.name_count):
                continue
            name, operand = pkg.names[idx], {"kind": "fname", "index": idx}
        else:
            name, operand = pkg.object_path(idx), {"kind": "export", "index": idx}
            if name is None:
                continue
        arg = None
        a = o + 5
        if a < len(script):
            if script[a] == 0x24:
                arg = {"kind": "byte", "value": script[a + 1], "at": a}
            elif script[a] in (0x25, 0x26):
                arg = {"kind": "int", "value": 0 if script[a] == 0x25 else 1, "at": a}
        out.append({"at": o, "token": "0x%02X" % t, "name": name, "operand": operand,
                    "arg": arg})
    return out


def comparisons_of(script: bytes) -> list[dict]:
    """0x9A/0x9B at an offset, with the raw bytes around it (not an operator meaning)."""
    out = []
    for o in range(0, len(script)):
        if script[o] in (0x9A, 0x9B):
            out.append({"at": o, "token": "0x%02X" % script[o],
                        "window": script[max(0, o - 2):o + 10].hex(" ")})
    return out


def driverleft() -> dict:
    pkg = U.Package(STARTUP)
    e = pkg.exports[DL_EXPORT - 1]
    data = pkg.data(DL_EXPORT)
    script = script_of(data)
    refs, raw = refs_of(pkg, script)
    calls = calls_of(pkg, script)
    comps = comparisons_of(script)
    sel = [c for c in calls if c["name"] == SEL_FN]
    sel_offsets = [c["at"] for c in sel]
    # region boundaries: the value-2 call, the value-1 call, and the bind call before both
    v2 = next((c["at"] for c in sel if c["arg"] and c["arg"]["value"] == 2), None)
    v1 = next((c["at"] for c in sel if c["arg"] and c["arg"]["value"] == 1), None)
    if v2 is None or v1 is None:
        raise SystemExit("could not find the two selector calls with constants 2 and 1")
    bind = next((c["at"] for c in calls
                 if c["name"] and "RemoveBatmobileBinds" in c["name"]), None)

    def region(at: int) -> str:
        if at < v2:
            return "A: before the value-2 call"
        if at < v1:
            return "B: between the value-2 and value-1 calls"
        return "C: after the value-1 call"

    for r in refs:
        r["region"] = region(r["at"])
    return {
        "package": os.path.basename(STARTUP),
        "export": DL_EXPORT,
        "path": pkg.object_path(DL_EXPORT),
        "outer": pkg.object_name(e["outer_index"]),
        "class": pkg.object_class(DL_EXPORT),
        "export_bytes": len(data),
        "script_bytes": len(script),
        "script_sha1": hashlib.sha1(script).hexdigest(),
        "size_field": i32(data, 18),
        "name_index": i32(data, len(data) - 8),
        "name_at_trailer": pkg.names[i32(data, len(data) - 8)]
                           if 0 <= i32(data, len(data) - 8) < pkg.name_count else None,
        "refs": refs,
        "raw_hits": raw,
        "calls": calls,
        "comparisons": comps,
        "selector_calls": sel,
        "v2": v2, "v1": v1, "bind": bind,
    }


# ------------------------------------------------------------------ caller constants
def caller_constants(pkg) -> list[dict]:
    name_ix = [k for k, v in enumerate(pkg.names) if v == SEL_FN]
    rows = []
    for j in range(1, pkg.export_count + 1):
        if pkg.object_class(j) != "Function":
            continue
        data = pkg.data(j)
        if len(data) < 38:
            continue
        s = script_of(data)
        for o in range(0, len(s) - 4):
            if s[o] != 0x1B or i32(s, o + 1) not in name_ix:
                continue
            a = o + 5
            val = None
            if a < len(s):
                if s[a] == 0x24:
                    val = s[a + 1]
                elif s[a] in (0x25, 0x26):
                    val = 0 if s[a] == 0x25 else 1
            rows.append({"package": os.path.basename(pkg.path), "export": j,
                         "function": pkg.object_path(j), "short": pkg.object_name(j),
                         "call_at": o, "arg_at": a, "value": val})
    return rows


# ------------------------------------------------------------------ runtime transitions
def runtime() -> dict:
    """Per-vehicle mode timeline. Records whose value is not 0/1/2 are corrupt reads, not modes."""
    files = sorted(glob.glob(LOGS))
    samples, per_vehicle, transitions, coverage, invalid = 0, {}, [], {}, []
    for path in files:
        last = {}
        with open(path, encoding="utf-8", errors="replace") as fh:
            for ln, line in enumerate(fh, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                changed = rec.get("changed") or {}
                for k, v in changed.items():
                    if not k.endswith("BatmanVsBatmobileCollisionMode"):
                        continue
                    veh = k.split(".")[0]
                    driver = changed.get(veh + ".Driver", "not logged")
                    prev = last.get(veh)
                    valid = isinstance(v, int) and v in (0, 1, 2)
                    if not valid:
                        # the mode value itself is out of range; count it and the other junk fields
                        junk = sum(1 for x in changed.values()
                                   if x is None or (isinstance(x, int)
                                                    and (x > 1 << 31 or x < 0)))
                        if v is not None:
                            junk += 1          # the out-of-range mode value itself
                        invalid.append({"file": os.path.basename(path), "line": ln,
                                        "t": rec.get("t"), "vehicle": veh, "value": v,
                                        "from": prev, "junk_fields": junk,
                                        "record_fields": len(changed)})
                    if valid and prev is not None and prev != v:
                        transitions.append({"file": os.path.basename(path), "line": ln,
                                            "t": rec.get("t"), "vehicle": veh,
                                            "from": prev, "to": v, "driver": driver})
                    if valid:
                        last[veh] = v
                    samples += 1
                    pv = per_vehicle.setdefault(veh, {"samples": 0, "values": {}})
                    pv["samples"] += 1
                    pv["values"][str(v)] = pv["values"].get(str(v), 0) + 1
                    key = ("seated" if driver not in ("not logged", None, 0)
                           else ("absent" if driver == 0 else "missing"))
                    coverage[key] = coverage.get(key, 0) + 1
    rises = [t for t in transitions if t["from"] == 0 and t["to"] == 1]
    falls = [t for t in transitions if t["from"] == 1 and t["to"] == 0]
    return {"files": [os.path.basename(p) for p in files], "samples": samples,
            "per_vehicle": per_vehicle, "coverage": coverage, "transitions": transitions,
            "rises": rises, "falls": falls, "invalid": invalid}


# ------------------------------------------------------------------ selector (only what survives)
def selector() -> dict:
    pkg = U.Package(BMGAME)
    data = pkg.data(SEL_EXPORT)
    script = script_of(data)
    calls = [c for c in calls_of(pkg, script)
             if c["name"] in ("Core.DetachComponent", "Core.AttachComponent")]
    for c in calls:
        c["mesh"] = None
        a = c["at"] + 5
        if a + 5 <= len(script) and script[a] in (0x00, 0x01):
            idx = i32(script, a + 1)
            c["mesh"] = pkg.object_path(idx)
            c["mesh_at"] = a
        # the guard constant is the byte operand of the comparison just before this call
        prev = [x for x in comparisons_of(script) if x["at"] < c["at"]]
        c["guard_at"] = prev[-1]["at"] if prev else None
    rows = {}
    for value, mesh in MESH.items():
        det = [c for c in calls if c["name"].endswith("DetachComponent")
               and c["mesh"].endswith(mesh)]
        att = [c for c in calls if c["name"].endswith("AttachComponent")
               and c["mesh"].endswith(mesh)]
        rows[value] = {"mesh": mesh,
                       "detach_at": [c["at"] for c in det],
                       "attach_at": [c["at"] for c in att]}
    return {"export": SEL_EXPORT, "path": pkg.object_path(SEL_EXPORT),
            "script_bytes": len(script), "script_sha1": hashlib.sha1(script).hexdigest(),
            "rows": rows, "calls": calls}


# ------------------------------------------------------------------ build
def build() -> str:
    dl = driverleft()
    startup = U.Package(STARTUP)
    bmgame = U.Package(BMGAME)
    callers = caller_constants(startup) + caller_constants(bmgame)
    rt = runtime()
    sl = selector()

    by_region = {}
    for r in dl["refs"]:
        by_region.setdefault(r["region"], []).append(r)
    names_in = {k: [r["path"] for r in v] for k, v in by_region.items()}
    expected_names = {"A: before the value-2 call", "B: between the value-2 and value-1 calls",
                      "C: after the value-1 call"}
    four_regions = {n: [r["region"] for r in dl["refs"] if r["path"] == n] for n in FOUR}

    by_fn = {}
    for c in callers:
        if c["value"] is not None:
            by_fn.setdefault(c["short"], set()).add(c["value"])

    oracles = {}
    oracles["export_identity"] = {
        "ok": (dl["path"] == "RVehicleBatmobile.DriverLeft" and dl["class"] == "Function"
               and dl["script_bytes"] == 368
               and dl["script_sha1"] == "70471c04b9526a2616e27c3c3830155112765efb"
               and dl["size_field"] == 369 and dl["name_at_trailer"] == "DriverLeft"),
        "detail": {"path": dl["path"], "outer": dl["outer"], "script_bytes": dl["script_bytes"],
                   "sha1": dl["script_sha1"], "size_field": dl["size_field"]}}
    oracles["refs_reproduce_the_published_28"] = {
        "ok": [r["at"] for r in dl["refs"]] == EXPECTED_REFS,
        "detail": {"found": len(dl["refs"]), "raw_hits": dl["raw_hits"],
                   "offsets_match": [r["at"] for r in dl["refs"]] == EXPECTED_REFS}}
    oracles["every_ref_resolves"] = {
        "ok": all(r["path"] and r["class"] for r in dl["refs"]),
        "detail": {"refs": len(dl["refs"]), "unresolved": sum(1 for r in dl["refs"] if not r["path"])}}
    oracles["regions_partition_the_refs"] = {
        "ok": (set(names_in) == expected_names
               and sum(len(v) for v in names_in.values()) == len(dl["refs"])),
        "detail": {k: len(v) for k, v in names_in.items()}}
    oracles["four_names_present_twice"] = {
        "ok": all(sorted(r["at"] for r in dl["refs"] if r["path"] == n) == offs
                  for n, offs in FOUR.items()),
        "detail": {n: sorted(r["at"] for r in dl["refs"] if r["path"] == n) for n in FOUR}}
    oracles["armouredmode_and_asleep_sit_in_region_A_too"] = {
        "ok": (len(four_regions["Core.ArmouredMode"]) == 2
               and four_regions["Core.ArmouredMode"][0] == "A: before the value-2 call"
               and four_regions["Core.IsVehicleAsleep"][0] == "A: before the value-2 call"),
        "detail": four_regions}
    oracles["selector_calls_at_301_and_334"] = {
        "ok": (dl["v2"] == 301 and dl["v1"] == 334
               and [c["arg"]["value"] for c in dl["selector_calls"]] == [2, 1]),
        "detail": {"v2": dl["v2"], "v1": dl["v1"],
                   "calls": [[c["at"], c["arg"]["value"]] for c in dl["selector_calls"]]}}
    oracles["comparison_tokens_at_6_and_274"] = {
        "ok": [c["at"] for c in dl["comparisons"]] == [6, 274],
        "detail": {"compare_offsets": [c["at"] for c in dl["comparisons"]]}}
    oracles["caller_constants"] = {
        "ok": all(by_fn.get(k) == v for k, v in EXPECTED_CALLERS.items()),
        "detail": {k: sorted(v) for k, v in sorted(by_fn.items())}}
    oracles["runtime_counts"] = {
        "ok": (rt["samples"] == 30 and len(rt["invalid"]) == 2
               and rt["coverage"].get("seated") == 9 and rt["coverage"].get("absent") == 16
               and rt["coverage"].get("missing") == 5),
        "detail": {"samples": rt["samples"], "coverage": rt["coverage"],
                   "per_vehicle": rt["per_vehicle"], "invalid": len(rt["invalid"])}}
    oracles["valid_transitions_six_rises_five_falls"] = {
        "ok": (len(rt["transitions"]) == 11 and len(rt["rises"]) == 6
               and len(rt["falls"]) == 5),
        "detail": {"transitions": len(rt["transitions"]), "rises": len(rt["rises"]),
                   "falls": len(rt["falls"])}}
    oracles["four_named_rises_still_present"] = {
        "ok": all(any(t["t"] == ts for t in rt["rises"]) for ts in FOUR_RISES),
        "detail": {"named": FOUR_RISES, "all_rises": [t["t"] for t in rt["rises"]]}}
    oracles["rise_114824093_has_no_driver"] = {
        "ok": any(t["t"].endswith("11:48:24.093Z") and t["driver"] == "not logged"
                  for t in rt["rises"]),
        "detail": [[t["t"], t["driver"]] for t in rt["rises"]]}
    oracles["invalid_records_are_corrupt"] = {
        "ok": all(r["junk_fields"] >= 3 and r["value"] not in (0, 1, 2) for r in rt["invalid"]),
        "detail": rt["invalid"]}
    oracles["selector_sha1_unchanged"] = {
        "ok": (sl["script_bytes"] == 253
               and sl["script_sha1"] == "c2f6a2ee667c544876e5317a103072c44ea17788"),
        "detail": {"script_bytes": sl["script_bytes"], "sha1": sl["script_sha1"]}}
    oracles["mesh_rows_rederived"] = {
        "ok": (sl["rows"][1]["detach_at"] == [48] and sl["rows"][1]["attach_at"] == [105]
               and sl["rows"][2]["detach_at"] == [78] and sl["rows"][2]["attach_at"] == [135]),
        "detail": {str(k): v for k, v in sl["rows"].items()}}

    L = []
    A = L.append
    A("# DRIVERLEFT_REGIONS - what `DriverLeft` actually references around each selector call")
    A("")
    A("**Card:** DRIVERLEFT-regions (follow-on to the review of **G3-01e**, issue 1).")
    A("**Verdict:** the four names are in the function, but the sentence that is labelled `decoded`")
    A("is still wrong: `ArmouredMode` and `IsVehicleAsleep` are referenced **before** the value-2")
    A("call as well as between the two calls, so no positional split assigns them to one branch.")
    A("`COLLISION_SELECTOR2.md`'s offset table is a **partial list read one byte early**, and its")
    A("runtime section survives: it carries all four `0 -> 1` rises, and they are re-derived here with")
    A("the log file and line of each.")
    A("")
    A("## 1. The export (decoded)")
    A("")
    A("| field | value |")
    A("|---|---|")
    A(f"| package | `{dl['package']}` |")
    A(f"| export | {dl['export']} |")
    A(f"| path | `{dl['path']}` |")
    A(f"| outer | `{dl['outer']}` |")
    A(f"| class | `{dl['class']}` |")
    A(f"| export bytes | {dl['export_bytes']} |")
    A(f"| script bytes (`payload[22:-16]`) | {dl['script_bytes']} |")
    A(f"| script sha1 | `{dl['script_sha1']}` |")
    A(f"| size field @18 | {dl['size_field']} (= script + 1) |")
    A(f"| trailer name index | {dl['name_index']} (`{dl['name_at_trailer']}`) |")
    A("")
    A("The brief says `RVehicleBatmobileBase`; the export's own outer is "
      f"`{dl['outer']}`, and its path is `{dl['path']}`.")
    A("`RVehicleBatmobileBase` is the outer of the *selector* (`BmGame.upk` "
      f"{sl['export']}, `{sl['path']}`), which is where the value->mesh table lives. The function the")
    A("brief asks about is therefore this one, and the brief's class name is a slip, recorded rather")
    A("than silently corrected.")
    A("")
    A("## 2. How the references were found (decoded)")
    A("")
    A("Every offset in the 368-byte script is tested for the reference form `<0x00|0x01|0x02>` + int32,")
    A("and the int32 is resolved through the package object table. Matches that start inside an earlier")
    A("match's 5-byte extent are dropped. The result is compared against the 28 reference offsets")
    A("`DRIVERLEFT_7400.md` publishes, so a false positive or a miss fails the oracle:")
    A("")
    A(f"- raw pattern hits: **{dl['raw_hits']}**; after de-overlap: **{len(dl['refs'])}**")
    A(f"- oracle `refs_reproduce_the_published_28`: **{[r['at'] for r in dl['refs']] == EXPECTED_REFS}**")
    A("- the scan is a byte pattern, not a token walk: it can only mislabel a reference if a random")
    A("  int32 lands on a named object at a non-reference offset. The 28/28 agreement with the")
    A("  published set, and with the call sites at 301/334 below, is the check that this does not")
    A("  happen here. The *token* shape of the bytes between references is not re-derived (see")
    A("  UNKNOWN 1) - this card needs offsets and names, not a full grammar.")
    A("")
    A("## 3. Every reference, with the region it sits in (decoded)")
    A("")
    A(f"`region` is a byte position relative to the two selector calls: **A** before the value-2 call")
    A(f"(@{dl['v2']}), **B** between it and the value-1 call (@{dl['v1']}), **C** after the value-1 call.")
    A("It is a position, not a proven branch body - the branch-word encoding is UNKNOWN (G3-01e).")
    A("`prefix` is the byte immediately before the reference token.")
    A("")
    A("| # | token at | prefix | form | index | resolves to | class | region |")
    A("|---:|---:|---|---|---:|---|---|---|")
    for n, r in enumerate(dl["refs"], 1):
        A(f"| {n} | {r['at']} | `{r['prefix_byte']}` | `{r['form']}` | {r['index']} | "
          f"`{r['path']}` | {r['class']} | {r['region'][0]} |")
    A("")
    A("## 4. The real names in each region (decoded)")
    A("")
    A("**A - before the value-2 call (@%d):**" % dl["v2"])
    A("")
    for n in names_in["A: before the value-2 call"]:
        A(f"- `{n}`")
    A("")
    A("**B - between the value-2 call (@%d) and the value-1 call (@%d):**" % (dl["v2"], dl["v1"]))
    A("")
    for n in names_in["B: between the value-2 and value-1 calls"]:
        A(f"- `{n}`")
    A("")
    A(f"**C - after the value-1 call (@{dl['v1']}):**")
    A("")
    for n in names_in["C: after the value-1 call"]:
        A(f"- `{n}`")
    A("")
    A("Read as a whole function, the distinct names are: " +
      ", ".join(f"`{n}`" for n in sorted({r['path'] for r in dl['refs']})) + ".")
    A("")
    A("### What this does to the G3-01e sentence")
    A("")
    A("G3-01e said, labelled `decoded`: *\"2 on the other `DriverLeft` branch (its guard region names")
    A("`BatmobileWinch` and `WinchPullType`; the 1-branch's region names `ArmouredMode` and")
    A("`IsVehicleAsleep`)\"*. The bytes say:")
    A("")
    A("- `Core.BatmobileWinch` is referenced at 263 and 278, both **before** the value-2 call;")
    A("  `Core.WinchPullType` at 284 and 290, also both before it. That half of the claim is")
    A("  positionally consistent with the bytes.")
    A("- `Core.ArmouredMode` is referenced at **254** (before the value-2 call) **and** 318 (between")
    A("  the calls). `Core.IsVehicleAsleep` at **223** (before the value-2 call) **and** 328")
    A("  (between). So the pair G3-01e assigns to the 1-branch is also present in the region it")
    A("  assigns to the 2-branch, once each.")
    A("- Therefore the assignment is not merely unproven (branch encoding UNKNOWN): even the purely")
    A("  positional reading it relies on does not separate the two pairs. What the bytes support is")
    A("  that **all four names are in this function, twice each**, with `ArmouredMode`/")
    A("  `IsVehicleAsleep` occurring on both sides of the value-2 call.")
    A("- The honest statement is: the function references these four properties around its two")
    A("  `SetBatmanVsBatmobileCollisionMode` calls; **which reference guards which call is UNKNOWN**.")
    A("  A predicate that reads a winch property before choosing 2 is plausible, but nothing in the")
    A("  bytes orders the references into branch bodies.")
    A("")
    A("## 5. The calls and comparisons (decoded)")
    A("")
    A("| at | token | call | argument |")
    A("|---:|---|---|---|")
    for c in dl["calls"]:
        arg = (f"{c['arg']['kind']} {c['arg']['value']} @{c['arg']['at']}"
               if c["arg"] else "-")
        A(f"| {c['at']} | `{c['token']}` | `{c['name']}` | {arg} |")
    A("")
    A(f"Comparison tokens (`0x9A`/`0x9B`) are at {', '.join(str(c['at']) for c in dl['comparisons'])};")
    A("their operator meaning (`==` vs `!=`) is UNKNOWN. The branch words that would associate a")
    A("comparison with a body are not offsets in any encoding tried (G3-01e's corpus test), so this")
    A("card does not group the references into bodies.")
    A("")
    A("## 6. The `0 -> 1` transitions of the collision mode (decoded from the logs)")
    A("")
    A(f"Re-derived from `samples-*.jsonl` ({len(rt['files'])} files, {rt['samples']} mode records "
      f"across {len(rt['per_vehicle'])} vehicle instances): **{len(rt['transitions'])}** valid "
      f"transitions, **{len(rt['rises'])}** rises, **{len(rt['falls'])}** falls, and "
      f"**{len(rt['invalid'])}** records whose value is not a mode (6.3).")
    A("")
    A("### 6.1 The four rises the brief and the card name - all still present")
    A("")
    A("| # | timestamp | log file | line | vehicle | transition | Driver in the sample | callers that can pass 1 |")
    A("|---:|---|---|---:|---|---|---|---|")
    n = 0
    for t in rt["rises"]:
        if t["t"] not in FOUR_RISES:
            continue
        n += 1
        A(f"| {n} | `{t['t']}` | `{t['file']}` | {t['line']} | `{t['vehicle']}` | "
          f"{t['from']} -> {t['to']} | {t['driver']} | `OnSleepRBPhysics` (Startup 7402 @54) or "
          f"`DriverLeft`'s second call (Startup 7400 @{dl['v1']}) |")
    A("")
    A("### 6.2 Two further rises in the same logs")
    A("")
    A("The card was written against 23 mode samples; the sampler kept writing, and the same directory")
    A(f"now holds {rt['samples']}. Two more `0 -> 1` rises are in `samples-20261103T120003Z.jsonl`:")
    A("")
    A("| timestamp | log file | line | vehicle | transition | Driver in the sample |")
    A("|---|---|---:|---|---|---|")
    for t in rt["rises"]:
        if t["t"] in FOUR_RISES:
            continue
        A(f"| `{t['t']}` | `{t['file']}` | {t['line']} | `{t['vehicle']}` | "
          f"{t['from']} -> {t['to']} | {t['driver']} |")
    A("")
    A("So \"all four 0 -> 1 rises\" was right for the read it describes, and is no longer the whole")
    A(f"set: there are {len(rt['rises'])} now. The four it named are unchanged, which is what the fix to")
    A("G3-01e's three-rise narrative needed.")
    A("")
    A("### 6.3 Two records that are not mode changes")
    A("")
    A("| timestamp | log file | line | vehicle | value | junk fields in the same record | transition from |")
    A("|---|---|---:|---|---:|---:|---|")
    for r in rt["invalid"]:
        A(f"| `{r['t']}` | `{r['file']}` | {r['line']} | `{r['vehicle']}` | `{r['value']}` | "
          f"{r['junk_fields']} of {r['record_fields']} | {r['from']} |")
    A("")
    A("These are corrupt reads, not modes: `234` arrives in a record where `veh1.Driver` is")
    A("`768603295890743556` and the flag fields are 32-bit garbage, and the `None` record nulls every")
    A("`veh0` field. They are excluded from the transition count and listed here rather than dropped.")
    A("")
    A("### 6.4 Per-vehicle census")
    A("")
    A("| vehicle instance | mode records | values seen |")
    A("|---|---:|---|")
    for veh, pv in sorted(rt["per_vehicle"].items()):
        A(f"| `{veh}` | {pv['samples']} | `{json.dumps(pv['values'], sort_keys=True)}` |")
    A("")
    A("The earlier cards counted these three instances together (23 records then, 30 now). Every rise")
    A("in 6.1 and 6.2 is a single instance's, which the table's `vehicle` column shows.")
    A("")
    A("### Callers and the constant each passes (decoded)")
    A("")
    A("| package | export | function | call at | constant |")
    A("|---|---:|---|---:|---:|")
    for c in sorted(callers, key=lambda x: (x["package"], x["export"])):
        A(f"| `{c['package']}` | {c['export']} | `{c['function']}` | {c['call_at']} | "
          f"{c['value'] if c['value'] is not None else '-'} |")
    A("")
    A("`0` is passed by `DriverEnter`, `OnWakeRBPhysics` and `StartSelfDrive`; `1` by")
    A("`OnSleepRBPhysics` and one `DriverLeft` call; `2` by the other. The `11:48:22.898` fall and the")
    A("`11:48:24.093` rise are 0.3 s and 1.2 s apart with no driver field in either sample, which is")
    A("the sleep/wake pair (`OnSleepRBPhysics` passes 1, `OnWakeRBPhysics` passes 0) rather than a")
    A("driver event - `derived`, since the log does not name the caller.")
    A("")
    A("## 7. Runtime coverage (decoded)")
    A("")
    A(f"- mode records: {rt['samples']}; `Driver` co-sampled: seated {rt['coverage'].get('seated', 0)}, "
      f"absent {rt['coverage'].get('absent', 0)}, not logged {rt['coverage'].get('missing', 0)}")
    A(f"- of those, {len(rt['invalid'])} carry a value that is not a mode (6.3), so "
      f"{rt['samples'] - len(rt['invalid'])} are usable mode readings")
    A("- \"not logged\" means the sampler writes only changed fields, so a sample without a `Driver`")
    A("  key is missing evidence, not evidence of absence. The `11:48:24.093` rise is such a sample,")
    A("  so it cannot be called an exit.")
    A("")
    A("## 8. Which statements of `COLLISION_SELECTOR2.md` survive")
    A("")
    A("| statement | verdict | evidence |")
    A("|---|---|---|")
    A(f"| selector body: `BmGame.upk` {sl['export']}, {sl['script_bytes']} B, sha1 "
      f"`{sl['script_sha1'][:12]}` | **survives** | re-read here: same size, same sha1 |")
    A("| value->mesh table: 0 attaches nothing, 1 Pursuit, 2 Battle | **survives** | re-derived here "
      "from the four component calls (detach 48/78, attach 105/135) with the mesh properties they name |")
    A("| \"the two selector calls are at 301 (argument 2), 334 (argument 1)\" | **survives** | "
      f"decoded: `{SEL_FN}` at {dl['v2']} with `0x24 2`, at {dl['v1']} with `0x24 1` |")
    A("| \"the names `BatmobileWinch`/`WinchPullType`/`ArmouredMode`/`IsVehicleAsleep` **are** in this "
      "function\" | **survives** | all four present, twice each, table in §3 |")
    A("| the 22-row \"6-byte member refs\" table with an `at` column | **partly** | the names are "
      "right; each `at` is the byte **before** the reference token (e.g. 277 is `0x19`, the token is "
      "278), so the column is a prefix offset, not a reference offset |")
    A("| that table presented as *the* list of the script's member refs | **does not survive** | it "
      f"lists 22 of {len(dl['refs'])}; missing `Core.Driver` @54, `Core.InteriorLightsSwitchedOn` @61, "
      "`Core.ReturnValue` @100 and @179, `Core.BatmobileWinch` @263, "
      "`Core.WheelspinSmokeMomentum` @351 |")
    A("| \"the review's negative came from scanning only 5-byte refs behind `00/01/1C`\" | **survives "
      "in substance** | the names are there and the earlier negative was a scan artefact; but the ref "
      "form is 5 bytes, so \"6-byte\" counts the leading byte, which is a convention, not a width |")
    A("| \"the refs that sit between the two calls are `ArmouredMode` @317 and `IsVehicleAsleep` @327\" "
      "| **survives positionally** | prefix 317/327 -> tokens 318/328, both between 301 and 334 |")
    A("| \"what is not decoded: which side of a branch each ref guards\" | **survives, and is now "
      "stronger** | `ArmouredMode` @254 and `IsVehicleAsleep` @223 also sit **before** the value-2 "
      "call, so position cannot even separate the two pairs |")
    A("| \"all four `0 -> 1` rises: 10:05:15.778, 11:48:22.562, 11:48:24.093, 11:48:38.572\" | "
      "**survives for the 23-record read it describes** | all four re-derived with file + line in "
      "§6.1; the logs now hold 30 records and six rises, so \"all\" is no longer the whole set (§6.2) |")
    A("| \"the rise at `11:48:24.093` has no driver evidence\" | **survives** | that sample carries "
      "no `Driver` key (oracle `rise_114824093_has_no_driver`) |")
    A("| coverage \"seated 7, absent 14, not logged 2\" over 23 samples | **superseded, not wrong "
      "when written** | the 23 records are all still present; the directory now holds 30, with "
      "seated 9 / absent 16 / not logged 5 (§7) |")
    A("| the runtime section treats the mode as one vehicle's | **does not survive as a scope** | "
      "the logs carry `veh0`, `veh1` and `veh2`; §6.4 counts them separately |")
    A("| UNKNOWN 1 (\"which condition selects 1 and which selects 2\") | **survives, reframed** | it "
      "is UNKNOWN, but not for the reason given: the claimed guard regions are not separated by the "
      "bytes at all (§4) |")
    A("")
    A("What G3-01e itself still gets wrong: its runtime narrative named three rises and one fall,")
    A("omitting `11:48:22.898` and `11:48:24.093`. `COLLISION_SELECTOR2.md` fixed that; this card")
    A("confirms the fix rather than repeating the error.")
    A("")
    A("## 9. Oracles (`--check` re-runs each)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k in sorted(oracles):
        A(f"| `{k}` | {oracles[k]['ok']} | `{json.dumps(oracles[k]['detail'], sort_keys=True)[:240]}` |")
    A("")
    A("## 10. Result")
    A("")
    A(f"- the function: `{dl['path']}`, {dl['script_bytes']} B script, {len(dl['refs'])} references "
      "[decoded]")
    A(f"- value-2 call @{dl['v2']}, value-1 call @{dl['v1']} [decoded]")
    A("- region A (before 301) names: " + ", ".join(
        f"`{n}`" for n in dict.fromkeys(names_in["A: before the value-2 call"])) + " [decoded]")
    A("- region B (301-334): " + ", ".join(
        f"`{n}`" for n in names_in["B: between the value-2 and value-1 calls"]) + " [decoded]")
    A("- region C (after 334): " + ", ".join(
        f"`{n}`" for n in names_in["C: after the value-1 call"]) + " [decoded]")
    A("- `ArmouredMode`/`IsVehicleAsleep` occur in **both** A and B, so the G3-01e branch attribution "
      "does not survive [decoded offsets; conclusion derived]")
    A(f"- {len(rt['rises'])} `0 -> 1` rises, with file + line: §6.1 for the four the card named, "
      "§6.2 for the two added since [decoded]")
    A("- which reference guards which call: **UNKNOWN** (branch encoding)")
    A("")
    A("## 11. UNKNOWN")
    A("")
    A("1. **The token grammar between references.** This card scans for the reference form; it does")
    A("   not re-derive why the bytes at 100/179 parse as references rather than constants, nor the")
    A("   extent of the `0x19` contexts. Tried: 28/28 offset agreement and the call sites, which")
    A("   pins the references but not the surrounding tokens. Would need a token table for this build.")
    A("2. **Which reference guards which call.** The `0x9A/0x9B` tokens are decoded as bytes at 6 and")
    A("   274; the branch bodies are not. Tried: G3-01e's corpus test (branch words are not offsets)")
    A("   and the positional check in §4, which fails to separate the pairs.")
    A("3. **Which function produced each runtime transition.** The logs record the value, not the")
    A("   caller. Tried: caller constants (§6); two functions can pass 1, so a given rise is")
    A("   attributed by the caller set, not per sample.")
    A("")
    return "\n".join(L)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "--help"
    if mode not in ("--write", "--check"):
        print(__doc__)
        return 2
    md = build()
    if mode == "--write":
        with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print(f"wrote {rel(OUT_MD)} ({len(md):,} chars)")
        return 0
    with open(OUT_MD, encoding="utf-8", newline="") as fh:
        on_disk = fh.read()
    if on_disk != md:
        print("FAIL: DRIVERLEFT_REGIONS.md differs from a fresh rebuild")
        return 1
    print("OK rebuilt byte-identical from the two packages and the sampler logs")
    return 0


if __name__ == "__main__":
    sys.exit(main())

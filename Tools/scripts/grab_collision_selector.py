"""G3-01e - RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode: what the body does, and who calls it.

The rework of the G3-01b-mode item.  That card concluded the collision selector was native and
referenced by no UnrealScript; the review found `BmGame.upk` export 10894, a 291-byte Function that
names the mode property and **both** collision-mesh component properties.  This script decodes it
and every caller in `BmGame.upk` and `Startup.upk`.

What is decoded here, and how
  1. The operand layer, from the byte stream itself.  This body uses a small set of shapes that are
     recognised exactly, not guessed:
        ref operand       `01|00|02 <int32>`            (instance / local / default variable)
        comparison unit   `9A|9B 38 3A <operand> 38 3A <operand> 16`
        call              `1C <int32>` or `1B <FName>`, then parameters, then `16`
        constants         `24 <byte>`, `1D <int32>`, `25`(0) `26`(1) `27`(true) `28`(false)
        assignment        `0F <ref> <expr> 04`
     Every shape is asserted to fit its declared extent; the number of bytes no shape explains is
     counted and listed rather than hidden.
  2. The call sequence with argument byte offsets, and the two guards that compare the *property*
     (the old value) against 1 and 2 and the two that compare the *parameter* (the new value)
     against 1 and 2.  So the mesh table is read from the bytes; see the label on each row.
  3. Every caller: a scan of all 29,620 Functions in `BmGame.upk` and all 1,886 in `Startup.upk`
     for a virtual call whose FName is `SetBatmanVsBatmobileCollisionMode`, plus a final-function
     reference to the export itself.  The constant each caller passes is read from the byte after
     the call's name operand.
  4. The runtime read that this card has to explain: `veh1.BatmanVsBatmobileCollisionMode` 0 -> 1
     when the driver left (2026-11-03).  Recomputed here from the sampler logs in
     `Research/BatmobileGrab/runtime/`, never from a running game.

What is NOT decoded, and is labelled UNKNOWN
  * The branch encoding.  The repo token table names 0x06 `EX_Jump` and 0x07 `EX_JumpIfNot`, but
    those names do not survive a test: reading the 2-byte word after them as an offset into the
    script fails in every encoding tried (absolute, relative to token, relative to operand end,
    from the script end), and 51% of the words in the package are larger than the script they sit
    in.  So *whether a comparison's body runs when the comparison is true or false* is not in the
    bytes here.  The mesh table below is derived from which constant is paired with which mesh,
    which is polarity-independent, plus the old-value/new-value structure (rule stated in
    `mesh_table.rule`) and the live 0/1 read.
  * The comparison operator's meaning (`0x9A` vs `0x9B`): the two tokens are reported separately
    per comparison, but whether either is `==` or `!=` is UNKNOWN.
  * The operator tokens `0x81`, `0x82`, `0x96`, `0x35`, `0x2D`, `0x19`-context skip and the
    `0x18` skip word are reported as raw bytes with their offsets, not named.

Outputs (never hand-edited): `Research/BatmobileGrab/COLLISION_SELECTOR.md` + `.json`.

Usage:
  python Tools/scripts/grab_collision_selector.py --write
  python Tools/scripts/grab_collision_selector.py --check    # re-derive, compare, exit 1 on drift
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

import upk_read  # noqa: E402

GAME = r"E:/Games/Batman - Arkham Knight/BmGame/CookedPCConsole"
PKGS = ("BmGame.upk", "Startup.upk")
SEL_PATH = "RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode"
SEL_EXPORT_EXPECTED = 10894
MODE_PROP = "BatmanVsBatmobileCollisionMode"
MESH_PROPS = {"BatmanCollisionMeshPursuitMode": "PursuitMode0",
              "BatmanCollisionMeshBattleMode": "BattleMode0"}
RUNTIME_GLOB = os.path.join(ROOT, "Research", "BatmobileGrab", "runtime", "samples-*.jsonl")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "COLLISION_SELECTOR.json")

# token bytes this body uses, named only where the extent is proven by the shape it must fit
REF_TOKENS = {0x00: "EX_LocalVariable", 0x01: "EX_InstanceVariable", 0x02: "EX_DefaultVariable"}
BYTE_CONST, INT_CONST = 0x24, 0x1D
FALSE, TRUE = 0x28, 0x27
ZERO, ONE = 0x25, 0x26
END_PARMS = 0x16
LET, RETURN = 0x0F, 0x04
FINAL, VIRTUAL = 0x1C, 0x1B
CONTEXT, SKIP = 0x19, 0x18
COMPARISONS = (0x9A, 0x9B)
OPERAND_PREFIX = (0x38, 0x3A)          # observed before every operand of every comparison unit
PREFIX_TOKENS = (0x81, 0x82)           # unary/binary wrappers seen before a comparison unit


def sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace("\\", "/")


def i32(s: bytes, o: int) -> int:
    return struct.unpack_from("<i", s, o)[0]


# --------------------------------------------------------------------------- package / function layout
def function_of(pkg, index: int) -> dict:
    data = pkg.data(index)
    rec = {
        "package": os.path.basename(pkg.path),
        "export": index,
        "path": pkg.object_path(index),
        "class": pkg.object_class(index),
        "outer": pkg.object_name(pkg.exports[index - 1]["outer_index"]),
        "export_bytes": len(data),
    }
    if len(data) < 38:
        rec.update({"script_bytes": 0, "script_sha1": None, "anchors": {}})
        return rec
    script = data[22:len(data) - 16]
    rec.update({
        "script_bytes": len(script),
        "script_sha1": sha1(script),
        "script_size_field": i32(data, 18),
        "name_index_field": i32(data, len(data) - 8),
        "pre_name_word": i32(data, len(data) - 12),
        "anchors": {
            "script_size_field_eq_len_plus_1": i32(data, 18) == len(script) + 1,
            "name_index_matches_export_name": (0 <= i32(data, len(data) - 8) < pkg.name_count
                                               and pkg.names[i32(data, len(data) - 8)]
                                               == pkg.exports[index - 1]["name"]),
            "pre_name_word_0x0002xxxx": (i32(data, len(data) - 12) & 0xFFFF0000) == 0x00020000,
        },
        "_script": script,
    })
    return rec


# --------------------------------------------------------------------------- operand / call decode
class Decoder:
    """Shaped scanner for the operand forms this function uses; anything else is left unnamed."""

    def __init__(self, pkg, script: bytes):
        self.pkg = pkg
        self.s = script
        self.used = bytearray(len(script))
        self.unexplained = []

    # ---- operands
    def operand(self, p: int):
        """Parse one operand at p. Returns (record, next_p) or (None, p)."""
        s = self.s
        start = p
        pre = None
        if p + 2 <= len(s) and (s[p], s[p + 1]) == OPERAND_PREFIX:
            pre = "38 3A"
            p += 2
            self.mark(start, p)
        if p >= len(s):
            return None, p
        t = s[p]
        if t in REF_TOKENS and p + 5 <= len(s):
            idx = i32(s, p + 1)
            path = self.pkg.object_path(idx)
            if path is None:
                return None, p
            rec = {"kind": "ref", "token": REF_TOKENS[t], "index": idx, "path": path,
                   "object_class": self.pkg.object_class(idx), "at": p, "prefix": pre}
            self.mark(p, p + 5)
            return rec, p + 5
        if t == BYTE_CONST and p + 2 <= len(s):
            self.mark(p, p + 2)
            return {"kind": "byte", "value": s[p + 1], "at": p, "prefix": pre}, p + 2
        if t == INT_CONST and p + 5 <= len(s):
            self.mark(p, p + 5)
            return {"kind": "int", "value": i32(s, p + 1), "at": p, "prefix": pre}, p + 5
        if t in (ZERO, ONE):
            self.mark(p, p + 1)
            return {"kind": "int", "value": 0 if t == ZERO else 1, "at": p, "prefix": pre}, p + 1
        if t in (TRUE, FALSE):
            self.mark(p, p + 1)
            return {"kind": "bool", "value": t == TRUE, "at": p, "prefix": pre}, p + 1
        if t in COMPARISONS:
            return self.comparison(p)
        return None, p

    def comparison(self, p: int):
        s = self.s
        start = p
        pre = None
        while p < len(s) and s[p] in PREFIX_TOKENS:
            pre = (pre or []) + ["0x%02X" % s[p]]
            self.mark(p, p + 1)
            p += 1
        if p >= len(s) or s[p] not in COMPARISONS:
            return None, start
        op = s[p]
        self.mark(p, p + 1)
        left, q = self.operand(p + 1)
        if left is None:
            return None, start
        right, q2 = self.operand(q)
        if right is None or q2 >= len(s) or s[q2] != END_PARMS:
            return None, start
        self.mark(q2, q2 + 1)
        rec = {"kind": "comparison", "op_token": "0x%02X" % op, "at": start,
               "left": left, "right": right, "prefix_tokens": pre,
               "terminator_at": q2, "next": q2 + 1}
        return rec, q2 + 1

    def call(self, p: int):
        """Parse a 1B/1C call with its parameter list. Returns (record, next_p) or (None, p)."""
        s = self.s
        t = s[p]
        name = None
        if t == FINAL and p + 5 <= len(s):
            idx = i32(s, p + 1)
            name = self.pkg.object_path(idx)
            operand = {"kind": "export", "index": idx}
        elif t == VIRTUAL and p + 5 <= len(s):
            idx = i32(s, p + 1)
            if not (0 <= idx < self.pkg.name_count):
                return None, p
            name = self.pkg.names[idx]
            operand = {"kind": "fname", "index": idx}
        else:
            return None, p
        if name is None:
            return None, p
        self.mark(p, p + 5)
        args, q = [], p + 5
        while q < len(s) and s[q] != END_PARMS:
            before = q
            arg, q = self.operand(q)
            if arg is None:
                # an argument form this decoder does not name: report where it stops being clear
                return {"kind": "call", "at": p, "token": "0x%02X" % t, "name": name,
                        "operand": operand, "args": args,
                        "undecoded_argument_at": before, "complete": False}, before
            args.append(arg)
        if q >= len(s):
            return None, p
        self.mark(q, q + 1)
        return {"kind": "call", "at": p, "token": "0x%02X" % t, "name": name,
                "operand": operand, "args": args, "end_parms_at": q, "complete": True}, q + 1

    def mark(self, a: int, b: int):
        for k in range(a, min(b, len(self.used))):
            self.used[k] = 1

    # ---- whole body
    def decode(self):
        s = self.s
        calls, comps, lets, returns, contexts = [], [], [], [], []
        p = 0
        while p < len(s):
            if s[p] == CONTEXT and p + 6 <= len(s) and s[p + 1] in REF_TOKENS:
                idx = i32(s, p + 2)
                path = self.pkg.object_path(idx)
                if path:
                    self.mark(p, p + 6)
                    contexts.append({"at": p, "token": "0x19", "object": path,
                                     "object_class": self.pkg.object_class(idx),
                                     "label": "decoded"})
                    p += 6
                    continue
            if s[p] in (FINAL, VIRTUAL):
                rec, q = self.call(p)
                if rec and (rec.get("complete") or q > p):
                    calls.append(rec)
                    p = q if rec.get("complete") else rec["undecoded_argument_at"]
                    continue
            if s[p] in COMPARISONS or s[p] in PREFIX_TOKENS:
                rec, q = self.comparison(p)
                if rec:
                    comps.append(rec)
                    p = q
                    continue
            if s[p] == LET and p + 10 <= len(s):
                prop, q = self.operand(p + 1)
                val, q2 = self.operand(q) if prop else (None, q)
                if prop and val and q2 < len(s) and s[q2] == RETURN:
                    self.mark(p, p + 1)
                    self.mark(q2, q2 + 1)
                    lets.append({"at": p, "property": prop, "value": val, "return_at": q2})
                    returns.append({"at": q2, "after_let": True})
                    p = q2 + 1
                    continue
            p += 1
        self.unexplained = [k for k, v in enumerate(self.used) if not v]
        return {"calls": calls, "comparisons": comps, "assignments": lets,
                "returns": returns, "contexts": contexts,
                "unexplained_bytes": len(self.unexplained),
                "unexplained_offsets": self.unexplained}


# --------------------------------------------------------------------------- selector (BmGame 10894)
def selector_doc(pkg) -> dict:
    rec = function_of(pkg, SEL_EXPORT_EXPECTED)
    assert rec["path"] == SEL_PATH, "export %d is %r, not the selector" % (SEL_EXPORT_EXPECTED, rec["path"])
    dec = Decoder(pkg, rec["_script"]).decode()
    # a comparison can also sit inside a call's arguments (SetCollisionFilter's bool argument)
    comps = {c["at"]: c for c in dec["comparisons"]}
    for c in dec["calls"]:
        for a in c["args"]:
            if a["kind"] == "comparison":
                comps[a["at"]] = a
    dec["comparisons"] = [comps[k] for k in sorted(comps)]

    # pair each mesh call with the comparison that sits immediately before it
    pairs = []
    for c in dec["calls"]:
        if c["name"] not in ("Core.DetachComponent", "Core.AttachComponent"):
            continue
        prev = [x for x in dec["comparisons"] if x["next"] <= c["at"]]
        guard = max(prev, key=lambda x: x["next"]) if prev else None
        gap = c["at"] - (guard["next"] if guard else c["at"])
        pairs.append({"call_at": c["at"], "call": c["name"].split(".")[-1],
                      "mesh": (c["args"][0]["path"].split(".")[-1] if c["args"]
                               and c["args"][0].get("kind") == "ref" else None),
                      "guard_comparison_at": guard["at"] if guard else None,
                      "guard_constant": (guard["right"].get("value") if guard and guard["right"].get("kind") == "byte" else None),
                      "guard_operand": (guard["left"].get("path") if guard and guard["left"].get("kind") == "ref" else None),
                      "bytes_between": gap})
    mesh_rows = []
    for value in (0, 1, 2):
        det = [p for p in pairs if p["guard_constant"] == value and p["call"] == "DetachComponent"]
        att = [p for p in pairs if p["guard_constant"] == value and p["call"] == "AttachComponent"]
        mesh_rows.append({
            "mode_value": value,
            "mesh": (att[0]["mesh"] if att else (det[0]["mesh"] if det else None)),
            "detach_at": [p["call_at"] for p in det],
            "attach_at": [p["call_at"] for p in att],
            "label": "decoded" if (det and att) else ("decoded (constant appears in no mesh pair; the old-value detach of the previous mode is what removes a mesh)" if value == 0 else "UNKNOWN"),
        })
    other = [c for c in dec["calls"]
             if c["name"].split(".")[-1] not in ("DetachComponent", "AttachComponent",
                                                  "SetCollisionFilter", "SetBatmanCanClimb")]
    rec.pop("_script", None)
    return {
        "function": rec,
        "calls": dec["calls"],
        "comparisons": dec["comparisons"],
        "contexts": dec["contexts"],
        "assignments": dec["assignments"],
        "returns": dec["returns"],
        "mesh_pairs": pairs,
        "mesh_table": {
            "rows": mesh_rows,
            "rule": ("a comparison unit's byte constant (0x24 xx) is paired with the DetachComponent/"
                     "AttachComponent call that begins immediately after that comparison's 0x16 "
                     "terminator; the call's argument names the mesh property. The first two "
                     "comparisons read the property (the OLD value) and call DetachComponent; the "
                     "next two read the parameter (the NEW value) and call AttachComponent. "
                     "Guard polarity (body-on-true vs body-on-false) is UNKNOWN here, and the table "
                     "is polarity-independent: whichever polarity 0x9A is, detach(old=k) and "
                     "attach(new=k) use the same k for the same mesh, so k names the mesh. Under the "
                     "inverted polarity the function would attach a mesh whenever the value is not k, "
                     "which contradicts the detach/attach pair; that reading is rejected."),
            "label": "derived (rule above; inputs: decoded comparison constants at 45/75/102/132, "
                     "decoded call targets at 48/78/105/135, decoded mesh properties 9797/9798)",
        },
        "no_set_hidden": {
            "calls_present": sorted({c["name"].split(".")[-1] for c in dec["calls"]}),
            "set_hidden": False, "set_actor_collision": False, "set_block_rigid_body": False,
            "label": "decoded (the selector body names none of those three functions)",
        },
        "unexpected_calls": other,
        "unexplained": {"bytes": dec["unexplained_bytes"], "offsets": dec["unexplained_offsets"],
                        "label": "UNKNOWN (byte shapes this decoder does not name: 0x07/0x06 words, "
                                 "0x18 skip, 0x96/0x35, the 0x19 context wrapper)"},
    }


# --------------------------------------------------------------------------- callers
def callers(pkg) -> dict:
    name_ix = [k for k, v in enumerate(pkg.names) if v == "SetBatmanVsBatmobileCollisionMode"]
    sel_exports = [j for j in range(1, pkg.export_count + 1)
                   if pkg.object_class(j) == "Function" and pkg.exports[j - 1]["name"] == SEL_PATH.rsplit(".", 1)[-1]
                   and pkg.object_path(j) == SEL_PATH]
    needles = set(name_ix) | set(sel_exports)
    rows, scanned = [], 0
    for j in range(1, pkg.export_count + 1):
        if pkg.object_class(j) != "Function":
            continue
        scanned += 1
        data = pkg.data(j)
        if len(data) < 38:
            continue
        s = data[22:len(data) - 16]
        if not any(struct.pack("<i", n) in s for n in needles):
            continue
        p = 0
        while True:
            p = s.find(b"\x1b", p)
            if p < 0 or p + 9 > len(s):
                break
            idx = i32(s, p + 1)
            if idx in name_ix:
                arg_at, arg = p + 5, None
                if arg_at < len(s):
                    if s[arg_at] == BYTE_CONST:
                        arg = {"kind": "byte", "value": s[arg_at + 1], "at": arg_at}
                    elif s[arg_at] in (ZERO, ONE):
                        arg = {"kind": "int", "value": 0 if s[arg_at] == ZERO else 1, "at": arg_at}
                rows.append({"function": pkg.object_path(j), "export": j, "call_at": p,
                             "call_name_index": idx, "argument": arg,
                             "script_bytes": len(s),
                             "arg_label": "decoded (byte after the FName operand)"})
            p += 1
    return {"package": os.path.basename(pkg.path), "functions_scanned": scanned,
            "selector_name_indices": name_ix, "selector_exports": sel_exports, "callers": rows}


def all_callers() -> list[dict]:
    out = []
    for name in PKGS:
        pkg = upk_read.Package(os.path.join(GAME, name))
        res = callers(pkg)
        out.append(res)
    return out


# --------------------------------------------------------------------------- runtime logs
def runtime() -> dict:
    files = sorted(glob.glob(RUNTIME_GLOB))
    rows, transitions = [], []
    values = {}
    crosstab = {}
    for path in files:
        last = {}
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                t = rec.get("t")
                for k, v in (rec.get("changed") or {}).items():
                    if not k.endswith("BatmanVsBatmobileCollisionMode"):
                        continue
                    veh = k.split(".")[0]
                    dv = (rec.get("changed") or {}).get(veh + ".Driver", None)
                    prev = last.get(veh)
                    if prev is not None and prev != v:
                        transitions.append({"file": os.path.basename(path), "t": t, "vehicle": veh,
                                            "from": prev, "to": v, "driver_in_same_sample": dv})
                    last[veh] = v
                    values[v] = values.get(v, 0) + 1
                    if dv is not None:
                        present = "driver_present" if dv else "driver_absent"
                        key = "mode=%s|%s" % (v, present)
                        crosstab[key] = crosstab.get(key, 0) + 1
    rows = [{"files": [os.path.basename(p) for p in files],
             "samples_with_mode": sum(values.values()),
             "value_counts": {str(k): v for k, v in sorted(values.items())},
             "driver_crosstab": dict(sorted(crosstab.items())),
             "transitions": transitions,
             "label": "decoded (Research/BatmobileGrab/runtime/*.jsonl, written by the G3-02d sampler; "
                      "not read from a running game here)"}]
    return rows[0]


# --------------------------------------------------------------------------- oracles
def oracles(sel: dict, callers_by_pkg: list[dict], rt: dict) -> dict:
    rows = sel["mesh_table"]["rows"]
    pairs = sel["mesh_pairs"]
    meshes = {r["mode_value"]: r["mesh"] for r in rows}
    detach = {p["guard_constant"]: p["mesh"] for p in pairs if p["call"] == "DetachComponent"}
    attach = {p["guard_constant"]: p["mesh"] for p in pairs if p["call"] == "AttachComponent"}
    cal = [c for pkg in callers_by_pkg for c in pkg["callers"]]
    consts = sorted({c["argument"]["value"] for c in cal
                     if c["argument"] and c["argument"]["kind"] == "byte"})
    by_fn = {}
    for c in cal:
        if c["argument"] and c["argument"]["kind"] == "byte":
            by_fn.setdefault(c["function"].split(".", 1)[-1], set()).add(c["argument"]["value"])
    observed = {int(k) for k in rt["value_counts"]}
    return {
        "layout_anchors": {
            "ok": all(sel["function"]["anchors"].values()) and all(
                all(c["argument"] is not None for c in pkg["callers"]) for pkg in callers_by_pkg),
            "detail": {"selector": sel["function"]["anchors"],
                       "caller_scripts_sized": sum(len(pkg["callers"]) for pkg in callers_by_pkg)},
        },
        "comparison_shapes": {
            "ok": (len(sel["comparisons"]) == 7
                   and all(c["left"].get("kind") == "ref"
                           and c["right"].get("kind") in ("ref", "byte")
                           for c in sel["comparisons"])
                   and sum(1 for c in sel["comparisons"]
                           if c["right"].get("kind") == "byte") == 6),
            "detail": {"comparisons": len(sel["comparisons"]),
                       "byte_constant_guards": sum(1 for c in sel["comparisons"]
                                                   if c["right"].get("kind") == "byte"),
                       "shapes": ["%s(%s,%s)" % (c["op_token"], c["left"].get("path", c["left"].get("value")),
                                                 c["right"].get("path", c["right"].get("value")))
                                  for c in sel["comparisons"]]},
        },
        "old_new_split": {
            "ok": (all(str(c["left"].get("path", "")).endswith("." + MODE_PROP)
                       for c in sel["comparisons"][1:3])
                   and all(str(c["left"].get("path", "")).endswith(".Mode")
                           for c in sel["comparisons"][3:5])),
            "detail": {"detach_guards_read": [c["left"].get("path") for c in sel["comparisons"][1:3]],
                       "attach_guards_read": [c["left"].get("path") for c in sel["comparisons"][3:5]]},
        },
        "mesh_pair_symmetry": {
            "ok": (detach.get(1) == attach.get(1) and detach.get(2) == attach.get(2)
                   and detach.get(1) != detach.get(2) and 0 not in detach and 0 not in attach),
            "detail": {"detach": {str(k): v for k, v in detach.items()},
                       "attach": {str(k): v for k, v in attach.items()},
                       "mesh_1": meshes.get(1), "mesh_2": meshes.get(2)},
        },
        "call_set": {
            "ok": (set(sel["no_set_hidden"]["calls_present"])
                   == {"AttachComponent", "DetachComponent", "SetBatmanCanClimb",
                       "SetCollisionFilter"} and not sel["unexpected_calls"]),
            "detail": {"calls": sel["no_set_hidden"]["calls_present"],
                       "set_hidden": sel["no_set_hidden"]["set_hidden"]},
        },
        "caller_constants": {
            "ok": (consts == [0, 1, 2] and by_fn.get("DriverEnter") == {0}
                   and by_fn.get("OnWakeRBPhysics") == {0}
                   and by_fn.get("StartSelfDrive") == {0}
                   and by_fn.get("OnSleepRBPhysics") == {1}
                   and by_fn.get("DriverLeft") == {1, 2}),
            "detail": {"constants": consts,
                       "per_function": {k: sorted(v) for k, v in sorted(by_fn.items())}},
        },
        "runtime_in_caller_range": {
            "ok": observed and observed <= set(consts),
            "detail": {"observed_mode_values": sorted(observed), "caller_constants": consts,
                       "driver_crosstab": rt["driver_crosstab"]},
        },
        "runtime_driver_rule": {
            "ok": all((t["from"], t["to"]) in ((0, 1), (1, 0)) for t in rt["transitions"]),
            "detail": {"transitions": len(rt["transitions"]),
                       "pairs": sorted({"%s->%s" % (t["from"], t["to"]) for t in rt["transitions"]})},
        },
        "mode_1_implies_driver_absent": {
            "ok": ("mode=1|driver_present" not in rt["driver_crosstab"]
                   and rt["driver_crosstab"].get("mode=1|driver_absent", 0) > 0),
            "detail": {k: v for k, v in rt["driver_crosstab"].items() if k.startswith("mode=1")},
        },
    }


# --------------------------------------------------------------------------- build
def build() -> dict:
    pkg = upk_read.Package(os.path.join(GAME, "BmGame.upk"))
    sel = selector_doc(pkg)
    cls = all_callers()
    rt = runtime()
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/grab_collision_selector.py --write",
        "card": "GRB-G3-01e - SetBatmanVsBatmobileCollisionMode (rework of the G3-01b-mode item)",
        "labels": {
            "decoded": "read from the package at the stated export + byte offset, or from a named file",
            "derived": "computed from decoded facts by the stated rule",
            "UNKNOWN": "not in the bytes read; what was tried is recorded",
        },
        "packages": [{"file": n, "bytes": os.path.getsize(os.path.join(GAME, n))} for n in PKGS],
        "selector": sel,
        "callers": cls,
        "runtime": rt,
        "runtime_explanation": {
            "observed": "veh1.BatmanVsBatmobileCollisionMode 0 -> 1 when the driver left (sampler logs). "
                        "Every sample with mode 1 has no driver seated (5/5); mode 0 occurs both seated "
                        "(7) and with the vehicle dormant/no driver (9), so 0 is not 'seated' but 'not "
                        "outside the car'",
            "decoded": "0 is passed by DriverEnter, OnWakeRBPhysics and StartSelfDrive; 1 by "
                       "OnSleepRBPhysics and by one DriverLeft branch; 2 by the other DriverLeft branch",
            "derived": "0 is 'Batman not outside the car' - all enter/wake/self-drive callers pass 0, and "
                       "live it appears both seated (7 samples) and with the vehicle dormant/no driver (9); "
                       "1 is 'Batman outside' (5/5 samples with mode 1 have no driver) and carries the "
                       "pursuit collision mesh; 2 is DriverLeft's other branch, whose guard region names "
                       "BatmobileWinch and WinchPullType - which condition selects it is UNKNOWN",
            "label": "derived (inputs: decoded caller constants, decoded guard operands, live values)",
        },
        "unknowns": [
            "branch encoding: the 2-byte word after 0x06/0x07 is not an offset into the script under "
            "absolute, token-relative, operand-end-relative or end-relative reading (corpus test over "
            "74,632 branch-like tokens: best 10.2%, chance ~3-8%, and 51% of the words exceed their "
            "own script length), so body-on-true vs body-on-false is UNKNOWN",
            "comparison operator: 0x9A and 0x9B are reported as distinct tokens per comparison; "
            "whether either is == or != is UNKNOWN (no repo doc decodes them)",
            "the 0x19 context wrapper around SetCollisionFilter: the call target and both arguments "
            "are decoded, but the wrapper's skip encoding and the seven bytes at 152-158 are not",
            "the 0x18 skip word at 197 (0x0024), the 0x96/0x35 tokens at 200-201 and the int -1500 at "
            "217 (0x1D) are reported as raw bytes; their meanings are UNKNOWN",
            "which DriverLeft condition selects 1 and which selects 2 is UNKNOWN beyond the guard "
            "region's named refs (ArmouredMode, WinchPullType, IsVehicleAsleep)",
            "packages other than BmGame.upk and Startup.upk were not scanned for callers (card scope); "
            "NPC Batmobile classes in other packages would be the place to look",
        ],
    }
    doc["oracles"] = oracles(sel, cls, rt)
    doc["verdict"] = {
        "which_mesh_per_mode": "derived - 1 = BatmanCollisionMeshPursuitMode, 2 = "
                               "BatmanCollisionMeshBattleMode, 0 = neither attached; the guard "
                               "polarity is UNKNOWN and the table does not depend on it",
        "set_hidden_or_set_actor_collision": "decoded negative - the selector names neither, nor "
                                             "SetBlockRigidBody; it uses DetachComponent/AttachComponent, "
                                             "SetCollisionFilter(0, mode) and SetBatmanCanClimb",
        "runtime_0_to_1_at_exit": "explained by decoded caller constants: OnSleepRBPhysics passes 1 and "
                                  "DriverLeft passes 1 on one branch; 0 is the not-outside state "
                                  "(seated or dormant)",
    }
    return doc


# --------------------------------------------------------------------------- render
def render(doc: dict) -> str:
    L: list[str] = []
    A = L.append
    sel = doc["selector"]
    fn = sel["function"]
    A("# BmAK collision selector: `RVehicleBatmobileBase.SetBatmanVsBatmobileCollisionMode`")
    A("")
    A("GRB-G3-01e. Generated by `Tools/scripts/grab_collision_selector.py --write`; `--check` re-derives "
      "every number and fails on drift. Replaces the G3-01b-mode conclusion that the selector was native "
      "and referenced by no UnrealScript.")
    A("")
    A("Labels: `decoded` = read from the package at the export + byte offset shown, or from a named file; "
      "`derived` = a stated rule applied to decoded facts; `UNKNOWN` = not in the bytes read.")
    A("")
    A("## The function")
    A("")
    A("| field | value |")
    A("|---|---|")
    for k in ("package", "export", "path", "class", "outer", "export_bytes", "script_bytes"):
        A("| %s | `%s` |" % (k, fn[k]))
    A("| script sha1 | `%s` |" % fn["script_sha1"])
    A("| script size field | %d (== script bytes + 1: %s) |" % (
        fn["script_size_field"], fn["anchors"]["script_size_field_eq_len_plus_1"]))
    A("")
    A("## Decoded call sequence")
    A("")
    A("| at | token | call | arguments (byte offsets) |")
    A("|---|---|---|---|")
    for c in sel["calls"]:
        args = []
        for a in c["args"]:
            if a["kind"] == "ref":
                args.append("`%s` (%s@%d)" % (a["path"], a["token"], a["at"]))
            elif a["kind"] == "comparison":
                args.append("comparison `%s`(%s, %s) @%d" % (
                    a["op_token"],
                    a["left"].get("path", a["left"].get("value")),
                    a["right"].get("path", a["right"].get("value")), a["at"]))
            else:
                args.append("%s=%s @%d" % (a["kind"], a["value"], a["at"]))
        A("| %d | `%s` | `%s` | %s |" % (c["at"], c["token"], c["name"], ", ".join(args) or "-"))
    A("")
    A("## Decoded contexts (the object a call is made on)")
    A("")
    A("| at | token | object | class |")
    A("|---|---|---|---|")
    for c in sel["contexts"]:
        A("| %d | `%s` | `%s` | `%s` |" % (c["at"], c["token"], c["object"], c["object_class"]))
    A("")
    A("## Decoded guards (comparison units)")
    A("")
    A("| at | op token | left operand | right operand | terminator |")
    A("|---|---|---|---|---|")
    for c in sel["comparisons"]:
        l = c["left"]
        r = c["right"]
        A("| %d | `%s` | %s | %s | %d |" % (
            c["at"], c["op_token"],
            ("`%s`" % l["path"]) if l["kind"] == "ref" else ("%s %s" % (l["kind"], l["value"])),
            ("`%s`" % r["path"]) if r["kind"] == "ref" else ("%s %s" % (r["kind"], r["value"])),
            c["terminator_at"]))
    A("")
    A("Operator *meaning* (`==` vs `!=`) is UNKNOWN; the token bytes are decoded. The guard polarity "
      "(body on true vs on false) is UNKNOWN for the reason in UNKNOWN 1.")
    A("")
    A("## Value -> mesh table")
    A("")
    A("**Label: %s**" % sel["mesh_table"]["label"])
    A("")
    A("| mode value | mesh component property | detach at | attach at |")
    A("|---|---|---|---|")
    for r in sel["mesh_table"]["rows"]:
        A("| %d | `%s` | %s | %s |" % (
            r["mode_value"], r["mesh"] or "-",
            ", ".join(str(x) for x in r["detach_at"]) or "-",
            ", ".join(str(x) for x in r["attach_at"]) or "-"))
    A("")
    A("Rule: %s" % sel["mesh_table"]["rule"])
    A("")
    A("Value 0 never appears in a mesh pair: the mode that attaches no collision component. The mesh of "
      "the mode being left is removed by that mode's own old-value detach (the property is the guard "
      "operand for the two `DetachComponent` calls).")
    A("")
    A("`SetHidden`, `SetActorCollision`, `SetBlockRigidBody`: **%s/%s/%s** - the selector names none of "
      "them (decoded negative). It uses `DetachComponent`, `AttachComponent`, "
      "`SetCollisionFilter(ECollisionFilter=0, bool)` and `SetBatmanCanClimb(bool)`." % (
          sel["no_set_hidden"]["set_hidden"], sel["no_set_hidden"]["set_actor_collision"],
          sel["no_set_hidden"]["set_block_rigid_body"]))
    A("")
    A("## Assignment and return")
    A("")
    for a in sel["assignments"]:
        A("- at %d: `%s` := `%s` (return at %d, %s)" % (
            a["at"], a["property"].get("path"), a["value"].get("path"), a["return_at"],
            "decoded"))
    A("")
    A("## Callers (decoded by FName / export reference, whole-package scan)")
    A("")
    for pkg in doc["callers"]:
        A("### `%s` - %d Functions scanned, selector name indices %s, selector export %s" % (
            pkg["package"], pkg["functions_scanned"], pkg["selector_name_indices"],
            pkg["selector_exports"] or "-"))
        A("")
        A("| function | export | call at | call name index | argument |")
        A("|---|---|---|---|---|")
        for c in pkg["callers"]:
            a = c["argument"]
            A("| `%s` | %d | %d | %d | %s |" % (
                c["function"], c["export"], c["call_at"], c["call_name_index"],
                ("byte %d @%d" % (a["value"], a["at"])) if a else "-"))
        A("")
    A("## Runtime read this card has to explain")
    A("")
    rt = doc["runtime"]
    A("Files: %s" % ", ".join("`%s`" % f for f in rt["files"]))
    A("")
    A("- samples with a mode value: %d; value counts %s" % (rt["samples_with_mode"], rt["value_counts"]))
    A("- mode x driver cross-tab: %s" % rt["driver_crosstab"])
    A("- mode transitions: %d" % len(rt["transitions"]))
    for t in rt["transitions"]:
        A("  - `%s` %s: %s -> %s (vehicle %s, Driver in same sample: %s)" % (
            t["file"], t["t"], t["from"], t["to"], t["vehicle"], t["driver_in_same_sample"]))
    A("")
    A("Label: %s" % rt["label"])
    A("")
    A("### Explanation")
    A("")
    for k in ("observed", "decoded", "derived"):
        A("- **%s**: %s" % (k, doc["runtime_explanation"][k]))
    A("- Label: %s" % doc["runtime_explanation"]["label"])
    A("")
    A("## Oracles (each can fail; `--check` re-runs them)")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in sorted(doc["oracles"].items()):
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"], sort_keys=True)[:260]))
    A("")
    A("## Verdicts")
    A("")
    for k, v in sorted(doc["verdict"].items()):
        A("- `%s`: %s" % (k, v))
    A("")
    A("## UNKNOWN")
    A("")
    for i, u in enumerate(doc["unknowns"], 1):
        A("%d. %s" % (i, u))
    A("")
    groups = []
    for o in sel["unexplained"]["offsets"]:
        if groups and o == groups[-1][1] + 1:
            groups[-1][1] = o
        else:
            groups.append([o, o])
    A("Unexplained bytes in the selector body: **%d of %d**, in %d run(s): %s." % (
        sel["unexplained"]["bytes"], fn["script_bytes"], len(groups),
        ", ".join("%d-%d" % (a, b) if a != b else "%d" % a for a, b in groups)))
    A("")
    A("These are the control-flow words and wrapper tokens this decoder does not name - not operands "
      "it failed to resolve: every 5-byte reference in the body resolves to a named object.")
    A("")
    return "\n".join(L)


def write() -> int:
    doc = build()
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, sort_keys=True, ensure_ascii=False)
        fh.write("\n")
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(render(doc))
    print("wrote", rel(OUT_MD), "and", rel(OUT_JSON))
    print("selector: export %d, %d bytes, %d calls, %d comparisons, %d unexplained bytes"
          % (doc["selector"]["function"]["export"], doc["selector"]["function"]["script_bytes"],
             len(doc["selector"]["calls"]), len(doc["selector"]["comparisons"]),
             doc["selector"]["unexplained"]["bytes"]))
    print("callers:", {p["package"]: len(p["callers"]) for p in doc["callers"]})
    print("mesh table:", {r["mode_value"]: r["mesh"] for r in doc["selector"]["mesh_table"]["rows"]})
    print("oracles:", {k: v["ok"] for k, v in doc["oracles"].items()})
    return 0


def check() -> int:
    fails = []
    for p in (OUT_MD, OUT_JSON):
        if not os.path.exists(p):
            print("FAIL: %s missing - run --write" % rel(p))
            return 1
    stored = json.load(open(OUT_JSON, encoding="utf-8"))
    md = open(OUT_MD, encoding="utf-8").read()
    fresh = build()
    if json.dumps(fresh, sort_keys=True) != json.dumps(stored, sort_keys=True):
        a, b = json.dumps(stored, sort_keys=True), json.dumps(fresh, sort_keys=True)
        pos = next((i for i in range(min(len(a), len(b))) if a[i] != b[i]), 0)
        fails.append("re-derivation differs at %d: stored %r vs fresh %r"
                     % (pos, a[pos:pos + 90], b[pos:pos + 90]))
    if md != render(stored):
        fails.append("COLLISION_SELECTOR.md is not the render of COLLISION_SELECTOR.json")
    for k, v in stored["oracles"].items():
        if not v["ok"]:
            fails.append("oracle %s failed: %s" % (k, json.dumps(v["detail"])[:200]))
    if len(stored["selector"]["calls"]) != 7:
        fails.append("expected 7 calls in the selector body, got %d" % len(stored["selector"]["calls"]))
    if stored["selector"]["function"]["script_bytes"] != 253:
        fails.append("selector script length changed: %d" % stored["selector"]["function"]["script_bytes"])
    if sum(len(p["callers"]) for p in stored["callers"]) != 6:
        fails.append("expected 6 caller call-sites, got %d"
                     % sum(len(p["callers"]) for p in stored["callers"]))
    if len(stored["selector"]["comparisons"]) != 7:
        fails.append("expected 7 comparison units, got %d"
                     % len(stored["selector"]["comparisons"]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK selector export %d, %d script bytes, %d calls, %d comparisons"
          % (stored["selector"]["function"]["export"], stored["selector"]["function"]["script_bytes"],
             len(stored["selector"]["calls"]), len(stored["selector"]["comparisons"])))
    print("mesh table:", {r["mode_value"]: r["mesh"] for r in stored["selector"]["mesh_table"]["rows"]})
    print("callers:", {p["package"]: len(p["callers"]) for p in stored["callers"]},
          "constants:", sorted({c["argument"]["value"] for p in stored["callers"]
                                for c in p["callers"] if c["argument"]}))
    print("runtime values:", stored["runtime"]["value_counts"],
          "transitions:", len(stored["runtime"]["transitions"]))
    print("oracles:", {k: v["ok"] for k, v in stored["oracles"].items()})
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())

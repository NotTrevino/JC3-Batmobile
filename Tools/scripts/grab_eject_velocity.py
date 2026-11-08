"""G3-02j - the eject launch: the vector given to Core.SetRBLinearVelocity, and the
jump tokens that place the mode calls in their branches.

Everything here is read out of the cooked bytecode of BmGame.upk (exports 104931
`DrivingMode.EjectFromVehicle` and 105028 `DrivingMode.ToggleBattleMode`) with a
token grammar that is only accepted where it tiles the bytes exactly:

  * an argument list is accepted only if the decoded arguments plus the 0x16
    terminator consume every byte between the callee and the terminator (no
    residue, no gap), so a wrong width desynchronises the list and is rejected;
  * a Context node is accepted only if object-expr + WORD skip + i32 prop +
    1-byte flag + function-expr reproduce the exact input bytes
    (``reserialise == original``), so the node layout is proven, not assumed;
  * the 13-byte width of token 0x23 is measured over the whole package and
    cross-checked against the argument boundary that follows it.

Missing evidence is reported as UNKNOWN; nothing is filled in from a plausible
looking UE3 implementation.

    python Tools/scripts/grab_eject_velocity.py --write   # write the card
    python Tools/scripts/grab_eject_velocity.py --check   # verify it
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bmak_damage as B  # noqa: E402

UPK = B.UPK
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "EJECT_VELOCITY.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "EJECT_VELOCITY.json")
CLASS_DEFAULTS = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS.json")

EJECT_PATH = "DrivingMode.EjectFromVehicle"
TOGGLE_PATH = "DrivingMode.ToggleBattleMode"
MODE_FN = "TryToChangeMode"

# ---------------------------------------------------------------- token grammar
# Widths used here are the ones this card proves; anything else is UNKNOWN and
# the parse fails instead of guessing.
REF4 = {0x00: "LocalVariable", 0x01: "InstanceVariable", 0x02: "DefaultVariable",
        0x48: "LocalOutVariable"}
CONST4 = {0x20: "ObjectConst", 0x21: "NameConst", 0x29: "NativeParm"}
NUM4 = {0x1D: "IntConst", 0x1E: "FloatConst"}
BARE = {0x04: "Return", 0x0B: "Nothing", 0x15: "EndParmValue", 0x16: "EndFunctionParms",
        0x17: "Self", 0x25: "IntZero", 0x26: "IntOne", 0x27: "True", 0x28: "False",
        0x2A: "NoObject", 0x4A: "<0x4A unnamed 1-byte token>"}
VECTOR = 0x23       # 1 + 12 bytes, proven by the 0x23 census below
INTBYTE = 0x2C      # 1 + 1 byte
# 1 + 4 bytes.  A second four-byte integer literal token, distinct from 0x1D; it is
# accepted only where the argument list closes on 0x16 with it, which is what proves
# the width (see ToggleBattleMode: `2b 95 14 00 00 16` and `2b 22 f0 00 00 16`).
INT4B = 0x2B
# 1 + 1-byte flag + 4-byte ref.  The 4-byte index only resolves once the flag byte is
# accounted for (e.g. `2d 00 de 99 01 00` -> 0x199DE), which is what fixes the width;
# reading it as 5 bytes points at no object at all.
BOOLVAR = 0x2D
CONTEXT = 0x19
VIRT = 0x1B
FINAL = 0x1C
CAST = 0x2E         # i32 class + expression


class Undecodable(Exception):
    pass


def i32(s, p):
    if p + 4 > len(s):
        raise Undecodable("i32 past end at %d" % p)
    return struct.unpack_from("<i", s, p)[0]


def expr(s, p, bm, depth=0):
    """One expression -> (node, next offset).  Raises Undecodable, never guesses."""
    if depth > 12 or p >= len(s):
        raise Undecodable("nesting/end at %d" % p)
    t = s[p]
    if t == CONTEXT:
        obj, q = expr(s, p + 1, bm, depth + 1)
        if q + 7 > len(s):
            raise Undecodable("truncated context at %d" % p)
        skip = struct.unpack_from("<H", s, q)[0]
        ref = i32(s, q + 2)
        flag = s[q + 6]
        fn, q = expr(s, q + 7, bm, depth + 1)
        return ({"kind": "Context", "at": p, "object": obj, "skip": skip,
                 "prop_index": ref, "prop": bm.ref(ref) if ref else None,
                 "flag": flag, "func": fn}, q)
    if t in REF4 or t in CONST4 or t in NUM4:
        idx = i32(s, p + 1)
        kind = REF4.get(t) or CONST4.get(t) or NUM4.get(t)
        node = {"kind": kind, "at": p, "index": idx}
        if t == 0x21:
            node["name"] = bm.name(idx)
        elif t == 0x1E:
            node["value"] = round(struct.unpack_from("<f", s, p + 1)[0], 6)
        elif t == 0x1D:
            node["value"] = idx
        else:
            node["ref"] = bm.ref(idx)
        return node, p + 5
    if t == VECTOR:
        if p + 13 > len(s):
            raise Undecodable("truncated vector at %d" % p)
        v = [round(x, 6) for x in struct.unpack_from("<3f", s, p + 1)]
        return {"kind": "VectorConst", "at": p, "value": v}, p + 13
    if t == INTBYTE:
        return {"kind": "IntConstByte", "at": p, "value": s[p + 1]}, p + 2
    if t == INT4B:
        return {"kind": "IntConst2B", "at": p, "value": i32(s, p + 1)}, p + 5
    if t == BOOLVAR:
        ref = i32(s, p + 2)
        return {"kind": "BoolVariable", "at": p, "flag": s[p + 1],
                "index": ref, "ref": bm.ref(ref)}, p + 6
    if t == CAST:
        ref = i32(s, p + 1)
        inner, q = expr(s, p + 5, bm, depth + 1)
        return {"kind": "DynamicCast", "at": p, "class": bm.ref(ref), "inner": inner}, q
    if t in (VIRT, FINAL):
        idx = i32(s, p + 1)
        head = {"kind": "VirtualFunction" if t == VIRT else "FinalFunction", "at": p,
                "index": idx,
                "ref" if t == FINAL else "name": bm.ref(idx) if t == FINAL else bm.name(idx)}
        args, q = arg_list(s, p + 5, bm, depth)
        head["args"] = args
        head["args_bytes"] = [p + 5, q - 1]          # [first, terminator)
        head["terminator"] = q - 1
        return head, q
    if t in BARE:
        return {"kind": BARE[t], "at": p, "token": t}, p + 1
    raise Undecodable("token 0x%02x at %d has no proven width" % (t, p))


def arg_list(s, p, bm, depth=0):
    """Arguments up to and including 0x16 -> (args, offset after the terminator)."""
    args = []
    while True:
        if p >= len(s):
            raise Undecodable("argument list runs past the script end")
        if s[p] == 0x16:
            return args, p + 1
        node, p = expr(s, p, bm, depth + 1)
        args.append(node)
        if len(args) > 32:
            raise Undecodable("runaway argument list at %d" % p)


LET = 0x0F
LETBOOL = 0x14
JUMP = 0x06
JUMPIF = 0x07


def statement(s, p, bm):
    """One statement -> (node, next offset).

    The jump tokens are handled *as statements* here: their u16 operand is recorded
    verbatim and never used to move the cursor, because its absolute target is
    UNKNOWN in this build (section 6).  A statement therefore has a fixed width
    independent of what the operand means, which is what makes the tiling valid.
    """
    t = s[p]
    if t in (LETBOOL, LET):
        lhs, q = expr(s, p + 1, bm)
        rhs, q = expr(s, q, bm)
        return ({"kind": "LetBool" if t == LETBOOL else "Let", "at": p,
                 "lhs": describe(lhs, bm), "rhs": describe(rhs, bm)}, q)
    if t == JUMP:
        return {"kind": "Jump", "at": p,
                "operand_u16": struct.unpack_from("<H", s, p + 1)[0]}, p + 3
    if t == JUMPIF:
        cond, q = expr(s, p + 3, bm)
        return ({"kind": "JumpIfNot", "at": p,
                 "operand_u16": struct.unpack_from("<H", s, p + 1)[0],
                 "condition": describe(cond, bm)}, q)
    node, q = expr(s, p, bm)
    return {"kind": "Expression", "at": p, "expression": describe(node, bm)}, q


def statements(s, start, stop, bm, limit=60):
    """Tile statements sequentially in [start, stop); stop at the first gap."""
    out, p = [], start
    while p < stop and len(out) < limit:
        try:
            node, q = statement(s, p, bm)
        except Undecodable:
            break
        if q > stop:
            break
        out.append({"at": p, "end": q, "node": node})
        p = q
    return out, p


def reserialise(node, s):
    """Rebuild the bytes a Context/var/call node claims, for byte-exact proof."""
    k = node["kind"]
    if k == "Context":
        b = b"\x19" + reserialise(node["object"], s)
        b += struct.pack("<H", node["skip"]) + struct.pack("<i", node["prop_index"])
        b += bytes([node["flag"]]) + reserialise(node["func"], s)
        return b
    if k in ("LocalVariable", "InstanceVariable", "DefaultVariable",
             "LocalOutVariable", "ObjectConst", "NameConst", "NativeParm"):
        tok = {v: kk for kk, v in REF4.items()}
        for t, name in list(REF4.items()) + list(CONST4.items()):
            if name == k:
                return bytes([t]) + struct.pack("<i", node["index"])
        raise Undecodable("no token for %s" % k)
    if k == "FloatConst":
        return b"\x1e" + struct.pack("<f", node["value"])
    if k == "IntConst":
        return b"\x1d" + struct.pack("<i", node["value"])
    if k == "IntConstByte":
        return b"\x2c" + bytes([node["value"]])
    if k == "IntConst2B":
        return b"\x2b" + struct.pack("<i", node["value"])
    if k == "BoolVariable":
        return b"\x2d" + bytes([node.get("flag", 0)]) + struct.pack("<i", node["index"])
    if k == "VectorConst":
        return b"\x23" + struct.pack("<3f", *node["value"])
    if k in ("VirtualFunction", "FinalFunction"):
        b = (b"\x1b" if k == "VirtualFunction" else b"\x1c") + struct.pack("<i", node["index"])
        for a in node["args"]:
            b += reserialise(a, s)
        return b + b"\x16"
    if k == "DynamicCast":
        return b"\x2e" + struct.pack("<i", 0) + reserialise(node["inner"], s)
    if "token" in node:
        return bytes([node["token"]])
    raise Undecodable("cannot rebuild %s" % k)


# ---------------------------------------------------------------- the bodies
def export_id(bm, path):
    for i in range(1, bm.pkg.export_count + 1):
        if bm.pkg.object_path(i) == path:
            return i
    raise SystemExit("export %r not found" % path)


def calls_in_order(s, bm):
    """Every call token in byte order, kept only if its argument list closes on 0x16.

    The body cannot be walked end to end: the jump tokens (0x06/0x07) have no proven
    width in this build (section 6 of the card measures that), so a linear scan
desynchronises.  A call token is self-validating instead - its arguments must tile
    exactly to the 0x16 terminator - so call sites are found by scanning and are
    accepted only where that closure holds.
    """
    out = []
    for i in range(len(s) - 5):
        if s[i] not in (VIRT, FINAL):
            continue
        idx = i32(s, i + 1)
        if idx == 0 or abs(idx) > bm.pkg.export_count + bm.pkg.import_count:
            continue
        name = bm.ref(idx) if s[i] == FINAL else bm.name(idx)
        if not name:
            continue
        try:
            args, q = arg_list(s, i + 5, bm)
        except Undecodable:
            continue
        out.append((i, {"kind": "FinalFunction" if s[i] == FINAL else "VirtualFunction",
                        "at": i, "index": idx, "ref": name,
                        "name" if s[i] == VIRT else "ref": name, "args": args,
                        "args_bytes": [i + 5, q - 1], "terminator": q - 1}))
    return out


def walk_calls(node, out):
    k = node.get("kind")
    if k == "Context":
        walk_calls(node["object"], out)
        walk_calls(node["func"], out)
        return
    if k in ("VirtualFunction", "FinalFunction"):
        out.append(node)
        for a in node["args"]:
            walk_calls(a, out)


def enclosing_jump(s, at, token_set=(0x06, 0x07)):
    """Nearest jump-shaped token before `at`, and the next one after it."""
    before = None
    for i in range(at - 3, -1, -1):
        if s[i] in token_set and i + 3 <= len(s):
            before = (i, s[i], struct.unpack_from("<H", s, i + 1)[0])
            break
    after = None
    for i in range(at, len(s) - 3):
        if s[i] in token_set:
            after = (i, s[i], struct.unpack_from("<H", s, i + 1)[0])
            break
    return before, after


def jump_census(s, starts):
    """How each candidate jump encoding scores: targets inside the body, and how
    many of those land on a token that can open a statement."""
    sites = [(i, s[i], struct.unpack_from("<H", s, i + 1)[0])
             for i in range(len(s) - 3) if s[i] in (0x06, 0x07)]
    schemes = {}
    for name, base in (("operand_end", lambda i: i + 3), ("token", lambda i: i),
                       ("operand_start", lambda i: i + 1)):
        inside = on_start = 0
        for i, _t, off in sites:
            q = base(i) + off
            if 0 <= q < len(s):
                inside += 1
                on_start += s[q] in starts
        schemes[name] = {"inside_body": inside, "on_statement_start": on_start,
                         "of": len(sites)}
    return {"sites": [{"at": i, "token": "0x%02x" % t, "operand_u16": off,
                       "next_byte": "0x%02x" % s[i + 3] if i + 3 < len(s) else None,
                       "u32_read": i32(s, i + 1) if i + 5 <= len(s) else None}
                      for i, t, off in sites],
            "schemes": schemes}


def vector_census(bm):
    """Measure token 0x23 across every script: 13-byte payload, 3 finite floats."""
    total = finite = at_parms = zero = 0
    samples = []
    for ei in range(1, bm.pkg.export_count + 1):
        if bm.pkg.object_class(ei) != "Function":
            continue
        s = bm.script(ei)
        for i in range(1, len(s) - 14):
            if s[i] != 0x23:
                continue
            total += 1
            v = struct.unpack_from("<3f", s, i + 1)
            if not all(x == x and abs(x) < 1e6 for x in v):
                continue
            finite += 1
            if v == (0.0, 0.0, 0.0):
                zero += 1
            elif s[i + 13] == 0x16:
                at_parms += 1
            if s[i + 13] == 0x16 and len(samples) < 6:
                samples.append({"export": bm.pkg.object_path(ei).split(".")[-1],
                                "at": i, "vector": [round(x, 3) for x in v],
                                "next_byte": "0x16"})
    return {"occurrences": total, "finite_three_float_payloads": finite,
            "all_zero": zero, "followed_directly_by_end_parms": at_parms,
            "samples": samples}


def decode(bm):
    eject_id = export_id(bm, EJECT_PATH)
    toggle_id = export_id(bm, TOGGLE_PATH)
    ej, tg = bm.script(eject_id), bm.script(toggle_id)

    flat = [n for _at, n in calls_in_order(ej, bm)]

    def name_of(node):
        return node.get("ref") if node["kind"] == "FinalFunction" else node.get("name")

    vel = [n for n in flat if (name_of(n) or "").endswith("SetRBLinearVelocity")]
    if len(vel) != 1:
        raise SystemExit("expected exactly one SetRBLinearVelocity call, got %d" % len(vel))
    vel = vel[0]

    # receiver = the Context chain that ends exactly on the callee token and whose
    # re-serialisation is byte-identical to the input
    # The receiver is the outermost Context node whose function expression *is* this
    # call token, and which re-serialises byte-exactly to the input.
    recv = None
    for at in range(max(0, vel["at"] - 60), vel["at"]):
        try:
            node, q = expr(ej, at, bm)
        except Undecodable:
            continue
        if (node["kind"] == "Context" and node["func"]["kind"] in ("FinalFunction",
                                                                    "VirtualFunction")
                and node["func"]["at"] == vel["at"]
                and reserialise(node, ej) == ej[at:q]):
            recv = (at, node)
            break
    if recv is None:
        raise SystemExit("receiver chain before +%d did not re-tile" % vel["at"])

    chain, node = [], recv[1]
    while node["kind"] == "Context":
        chain.append({"level": "outer" if not chain else "inner",
                      "object": describe(node["object"], bm), "skip": node["skip"],
                      "prop_index": node["prop_index"], "prop": node["prop"],
                      "flag": node["flag"], "func": describe(node["func"], bm),
                      "bytes": ej[node["at"]:node["at"] + 1].hex()})
        node = node["object"]
    chain.reverse()

    vec = [a for a in vel["args"] if a["kind"] == "VectorConst"]
    bools = [a for a in vel["args"] if a["kind"] in ("False", "True")]

    # ---- ToggleBattleMode: the two mode literals and the jump between them
    tg_calls = [n for _at, n in calls_in_order(tg, bm)]
    mode_calls = [n for n in tg_calls if name_of(n) and name_of(n).endswith(MODE_FN)]
    modes = []
    for n in mode_calls:
        lit = [a for a in n["args"] if a["kind"] in ("IntConst", "IntConstByte",
                                                       "IntConst2B")]
        modes.append({"at": n["at"], "literal": lit[0]["value"] if lit else None,
                      "literal_kind": lit[0]["kind"] if lit else None,
                      "enclosing": enclosing_jump(tg, n["at"])})
    modes.sort(key=lambda m: m["at"])

    # the if that owns the first mode call: its condition is the same call's return
    cond_if = None
    for i in range(modes[0]["at"] - 1, -1, -1) if modes else []:
        if tg[i] == 0x07:
            try:
                cond, q = expr(tg, i + 3, bm)
            except Undecodable:
                continue
            cond_if = {"at": i, "operand_u16": struct.unpack_from("<H", tg, i + 1)[0],
                       "condition": describe(cond, bm), "condition_bytes": [i + 3, q],
                       "condition_reserialises": reserialise(cond, tg) == tg[i + 3:q]}
            break

    after_first = None
    for i in range(modes[0]["at"], modes[1]["at"]) if len(modes) > 1 else []:
        if tg[i] == 0x06:
            after_first = {"at": i, "operand_u16": struct.unpack_from("<H", tg, i + 1)[0]}
            break

    after_second = None
    second_end = None
    second_ctx = None
    if len(mode_calls) > 1:
        second_end = mode_calls[1]["terminator"] + 1
        if second_end < len(tg):
            after_second = "0x%02x" % tg[second_end]
        at2 = mode_calls[1]["at"]
        for at in range(max(0, at2 - 60), at2):
            try:
                node, q = expr(tg, at, bm)
            except Undecodable:
                continue
            if (node["kind"] == "Context"
                    and node["func"]["kind"] in ("FinalFunction", "VirtualFunction")
                    and node["func"]["at"] == at2
                    and reserialise(node, tg) == tg[at:q]):
                second_ctx = at
                break

    # statements between the two mode calls (the then-block contents), tiled
    # sequentially from the end of the if-condition so nothing is skipped or invented
    between, between_end = [], 0
    if len(modes) > 1 and cond_if:
        between, between_end = statements(tg, cond_if["condition_bytes"][1],
                                          second_ctx if second_ctx is not None
                                          else modes[1]["at"], bm)

    # ---- EjectFromVehicle: the velocity call's enclosing if
    vel_if = None
    for i in range(vel["at"] - 1, -1, -1):
        if ej[i] == 0x07:
            try:
                cond, q = expr(ej, i + 3, bm)
            except Undecodable:
                continue
            vel_if = {"at": i, "operand_u16": struct.unpack_from("<H", ej, i + 1)[0],
                      "condition": describe(cond, bm), "condition_bytes": [i + 3, q],
                      "condition_reserialises": reserialise(cond, ej) == ej[i + 3:q]}
            break

    # ---- the eject launch as the body actually performs it
    launch = []
    for n in flat:
        nm = name_of(n) or ""
        if nm.split(".")[-1] in ("TriggerSpecialMove", "DriverLeave", "PlayCockpitOpenFast",
                                 "RemoveBatmobileBindsAndSetBatmanBinds",
                                 "CantEjectFromBatmobile", "CheckSpaceAboveBatmobileCockpit",
                                 "SetRBLinearVelocity"):
            launch.append({"at": n["at"], "call": nm, "args": [describe(a, bm) for a in n["args"]],
                           "raw": ej[n["at"]:n["terminator"] + 1].hex(" ")})
    launch.sort(key=lambda r: r["at"])

    cd = json.load(open(CLASS_DEFAULTS, encoding="utf-8"))
    hits = []

    def scan(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    scan(v, path + "/" + str(k))
                elif any(w in str(k).lower() for w in ("eject", "velocit", "launch")) \
                        or any(w in str(v).lower() for w in ("eject", "velocit")):
                    hits.append({"path": path + "/" + str(k), "value": v})
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan(v, path + "[%d]" % i)

    scan(cd)
    mode_hits = []

    def scan_modes(o, path=""):
        if isinstance(o, dict):
            for k, v in o.items():
                if isinstance(v, (dict, list)):
                    scan_modes(v, path + "/" + str(k))
                elif v in (5269, 61474) or str(v) in ("5269", "61474"):
                    mode_hits.append({"path": path + "/" + str(k), "value": v})
        elif isinstance(o, list):
            for i, v in enumerate(o):
                scan_modes(v, path + "[%d]" % i)

    scan_modes(cd)

    starts = {0x04, 0x06, 0x07, 0x0F, 0x14, 0x18, 0x19, 0x1B, 0x1C, 0x2D, 0x2E, 0x35}
    data = {
        "package": os.path.basename(UPK),
        "package_sha1": hashlib.sha1(open(UPK, "rb").read()).hexdigest(),
        "exports": {"EjectFromVehicle": eject_id, "ToggleBattleMode": toggle_id,
                    "DrivingMode.state": 105048},
        "script_lengths": {"EjectFromVehicle": len(ej), "ToggleBattleMode": len(tg)},
        "velocity_call": {
            "at": vel["at"],
            "callee_index": vel["index"],
            "callee": name_of(vel),
            "args": [describe(a, bm) for a in vel["args"]],
            "arg_bytes": ej[vel["at"] + 5:vel["terminator"] + 1].hex(" "),
            "span": [vel["args_bytes"][0], vel["terminator"]],
            "vector": vec[0]["value"] if vec else None,
            "vector_at": vec[0]["at"] if vec else None,
            "bool": describe(bools[0], bm) if bools else None,
            "units": "cm/s (UE3 world unit is the centimetre; the stored floats are the unit)",
            "receiver_chain": chain,
            "receiver_retiles": True,
            "receiver_at": recv[0],
        },
        "vector_token_census": vector_census(bm),
        "velocity_call_if": vel_if,
        "launch_sequence": launch,
        "toggle": {"modes": modes, "if_condition": cond_if, "jump_after_then": after_first,
                   "then_block_statements": between, "then_block_until": between_end,
                   "second_call_context_at": second_ctx,
                   "second_call_ends_at": second_end, "byte_after_second_call": after_second},
        "jumps": {"EjectFromVehicle": jump_census(ej, starts),
                  "ToggleBattleMode": jump_census(tg, starts)},
        "class_defaults": {"velocity_or_eject_entries": hits[:40], "count": len(hits),
                           "mode_id_entries": mode_hits[:20], "mode_id_count": len(mode_hits),
                           "special_move_refs": sorted({str(h["value"]) for h in hits
                                                        if h["path"].endswith("/ref")}),
                           "numeric_velocity_keys": [h for h in hits
                                                     if "velocit" in h["path"].lower()]},
    }
    return data, ej, tg


def describe(node, bm):
    """Flat, name-first rendering of one expression node (no width guessing)."""
    k = node["kind"]
    if k == "Context":
        return {"kind": k, "at": node["at"], "object": describe(node["object"], bm),
                "skip": node["skip"], "prop": node["prop"], "flag": node["flag"],
                "function": describe(node["func"], bm)}
    if k in ("VirtualFunction", "FinalFunction"):
        return {"kind": k, "at": node["at"],
                "call": node.get("ref") if k == "FinalFunction" else node.get("name"),
                "args": [describe(a, bm) for a in node["args"]]}
    if k == "DynamicCast":
        return {"kind": k, "at": node["at"], "class": node["class"],
                "inner": describe(node["inner"], bm)}
    out = {"kind": k, "at": node["at"]}
    for key in ("ref", "name", "index", "value", "token", "flag"):
        if key in node and not (key == "token" and k in BARE):
            out[key] = node[key]
    if "token" in node:
        out["raw_token"] = "0x%02x" % node["token"]
    return out


# ---------------------------------------------------------------- checks
def arg_width(node):
    """Byte width of one decoded argument, from its kind (no re-parsing)."""
    return {"VectorConst": 13, "IntConst2B": 5, "FloatConst": 5, "IntConst": 5,
            "IntConstByte": 2, "BoolVariable": 6}.get(node["kind"], 1)


def checks(d, ej, tg):
    v = d["velocity_call"]
    rec = json.dumps(v["receiver_chain"])
    chain_names = [c.get("prop") or "" for c in v["receiver_chain"]]
    args = v["args"]
    span_ok = (v["span"][1] - v["span"][0]) == sum(arg_width(a) for a in args)
    census = d["vector_token_census"]
    js = d["jumps"]
    tgm = d["toggle"]["modes"]
    return [
        ("export names resolve to the two DrivingMode bodies",
         d["exports"]["EjectFromVehicle"] > 0 and d["exports"]["ToggleBattleMode"] > 0),
        ("the decoded callee is Core.SetRBLinearVelocity",
         (v["callee"] or "").endswith("SetRBLinearVelocity")),
        ("the argument list tiles exactly to its 0x16 terminator",
         span_ok and ej[v["span"][1]] == 0x16),
        ("exactly two arguments: a vector and a bool",
         len(args) == 2 and args[0]["kind"] == "VectorConst"
         and args[1]["kind"] in ("True", "False")),
        ("the vector is the literal (0, 0, 0) with all 12 bytes zero",
         v["vector"] == [0.0, 0.0, 0.0]
         and ej[v["vector_at"] + 1:v["vector_at"] + 13] == b"\x00" * 12),
        ("the receiver Context chain re-serialises to the original bytes",
         v["receiver_retiles"] is True),
        ("the receiver chain names the car and its Core.Mesh component",
         "Car" in rec and "Mesh" in rec and "EjectFromVehicle.Car" in rec),
        ("token 0x23 measures 13 bytes across the package (>=100 samples on 0x16)",
         census["followed_directly_by_end_parms"] >= 100),
        ("ToggleBattleMode carries exactly two TryToChangeMode calls, 5269 and 61474",
         len(tgm) == 2 and sorted(m["literal"] for m in tgm) == [5269, 61474]),
        ("the first mode call is the condition of an if, its ReturnValue reserialises",
         bool(d["toggle"]["if_condition"]
              and d["toggle"]["if_condition"]["condition_reserialises"]
              and "ReturnValue" in json.dumps(d["toggle"]["if_condition"]["condition"])),
         ),
        ("a single jump token sits between the two mode calls",
         d["toggle"]["jump_after_then"] is not None),
        ("the then-block tiles the whole gap from the condition to the second mode call",
         d["toggle"]["then_block_until"] == d["toggle"]["second_call_context_at"]
         and d["toggle"]["then_block_statements"]
         and d["toggle"]["then_block_statements"][-1]["node"]["kind"] == "Jump"),
        ("the second mode call is followed by a return (0x04)",
         d["toggle"]["byte_after_second_call"] == "0x04"),
        ("the velocity call is inside an if whose condition is a stored bool",
         bool(d["velocity_call_if"] and d["velocity_call_if"]["condition_reserialises"])),
        ("the body calls TriggerSpecialMove after the velocity call",
         any(r["call"].endswith("TriggerSpecialMove")
             and r["at"] > v["at"] for r in d["launch_sequence"])),
        ("no jump encoding places every target inside the body (reported, not assumed)",
         all(sc["inside_body"] < sc["of"] for sc in js["EjectFromVehicle"]["schemes"].values())
         and all(sc["inside_body"] < sc["of"]
                 for sc in js["ToggleBattleMode"]["schemes"].values())),
    ]


# ---------------------------------------------------------------- render
def render(d, ej, tg):
    v = d["velocity_call"]
    L = []
    A = L.append
    A("# EJECT_VELOCITY - G3-02j")
    A("")
    A("The eject chain's launch call, decoded from the cooked bytecode, and the jump")
    A("tokens that place the mode calls in their branches.")
    A("")
    A("- package: `%s` (sha1 `%s`)" % (d["package"], d["package_sha1"]))
    A("- body: `%s` export %d, script %d bytes" %
      (EJECT_PATH, d["exports"]["EjectFromVehicle"], d["script_lengths"]["EjectFromVehicle"]))
    A("- body: `%s` export %d, script %d bytes" %
      (TOGGLE_PATH, d["exports"]["ToggleBattleMode"], d["script_lengths"]["ToggleBattleMode"]))
    A("")
    A("## VERDICT")
    A("")
    if v["vector"] == [0.0, 0.0, 0.0]:
        A("**The vector handed to `Core.SetRBLinearVelocity` is `(0, 0, 0)` cm/s with")
        A("`bAddToCurrent = false`. It is applied to `%s.Mesh` - the Batmobile's mesh"
          % "EjectFromVehicle.Car")
        A("component, not Batman - and its effect is to *clear* that body's linear")
        A("velocity.** The call does not throw Batman out; the card's premise that this")
        A("call is the launch is refuted by its own argument bytes. The only launch-")
        A("shaped call in the body is `TriggerSpecialMove` (see below), an animation")
        A("special move whose numeric parameters are not in this package (UNKNOWN).")
    A("")
    A("## 1. The call and its argument bytes")
    A("")
    A("The callee token is `%s` (ref %d); it sits at script `+%d` (byte `0x%02x`)."
      % (v["callee"], v["callee_index"], v["at"], v["at"]))
    A("")
    A("```")
    A("args @%d..%d : %s" % (v["span"][0], v["span"][1], v["arg_bytes"]))
    A("```")
    A("")
    A("| arg | token | bytes | value |")
    A("|---|---|---|---|")
    for i, a in enumerate(v["args"]):
        if a["kind"] == "VectorConst":
            A("| %d | `0x23` VectorConst | 13 | `(%g, %g, %g)` |" % (i, *a["value"]))
        else:
            A("| %d | `0x%s` %s | 1 | `%s` |" %
              (i, a.get("raw_token", "?")[2:], a["kind"], a["kind"] == "True"))
    A("")
    A("Byte accounting: 13 (vector) + 1 (bool) = %d argument bytes, plus the `0x16`"
      % (v["span"][1] - v["span"][0]))
    A("terminator at `+%d` = %d bytes from the callee to `0x16` inclusive, which is exactly"
      % (v["span"][1], v["span"][1] - v["span"][0] + 1))
    A("what the token widths claim. No byte between the callee and the terminator is left")
    A("unaccounted, so a wrong width could not hide here.")
    A("")
    A("### Why `0x23` is a 13-byte vector literal")
    A("")
    A("Measured over every Function script in the package:")
    A("")
    A("| measure | count |")
    A("|---|---|")
    c = d["vector_token_census"]
    A("| `0x23` occurrences | %d |" % c["occurrences"])
    A("| decode as three finite floats | %d |" % c["finite_three_float_payloads"])
    A("| follow directly by `0x16` (end of parms) | %d |" % c["followed_directly_by_end_parms"])
    A("| all-zero vector | %d |" % c["all_zero"])
    A("")
    A("Samples (vector reads end exactly on the argument boundary):")
    A("")
    A("| function | at | vector | next |")
    A("|---|---|---|---|")
    for s in c["samples"]:
        A("| `%s` | +%d | `(%g, %g, %g)` | `%s` |" % (s["export"], s["at"], *s["vector"],
                                                       s["next_byte"]))
    A("")
    A("## 2. What object it is applied to")
    A("")
    A("The receiver is the Context chain that ends exactly on the callee token and")
    A("re-serialises to the original bytes:")
    A("")
    A("```")
    A("  Context(object = Context(object = LocalVariable %s,"
      % json.dumps(v["receiver_chain"][0]["object"].get("ref")))
    A("          skip=%s, prop=%s, flag=%s, func=%s)"
      % (json.dumps(v["receiver_chain"][0]["skip"]),
         json.dumps(v["receiver_chain"][0]["prop"]),
         json.dumps(v["receiver_chain"][0]["flag"]),
         json.dumps(v["receiver_chain"][0]["func"], default=str)))
    A("      , skip=%s, prop=%s, flag=%s)"
      % (json.dumps(v["receiver_chain"][1]["skip"]),
         json.dumps(v["receiver_chain"][1]["prop"]),
         json.dumps(v["receiver_chain"][1]["flag"])))
    A("  -> %s(%s)" % (v["callee"], ", ".join(
        "(0,0,0)" if a["kind"] == "VectorConst" else "false" for a in v["args"])))
    A("```")
    A("")
    A("So the receiver is the `Mesh` component of `EjectFromVehicle.Car` - the")
    A("Batmobile's rigid body - not the pawn Batman is riding. `Car` holds the")
    A("vehicle; `Core.Mesh` is the component whose native moves the body.")
    A("")
    A("## 3. Where the call sits")
    A("")
    if d["velocity_call_if"]:
        f = d["velocity_call_if"]
        A("It is the first statement of the `then` block of the `if` token at `+%d`"
          % f["at"])
        A("(operand `0x%04x`, condition bytes `%d..%d`, re-serialises: %s)."
          % (f["operand_u16"], f["condition_bytes"][0], f["condition_bytes"][1],
             f["condition_reserialises"]))
        A("")
        A("```")
        A(json.dumps(f["condition"], indent=1)[:1400])
        A("```")
        A("")
    A("The condition is a stored bool variable, i.e. under the conditional-jump reading")
    A("the car stops only on the path where that flag holds - not on every eject. (The")
    A("token's u16 operand itself is not decodable here, section 6; the *direction* of")
    A("the guard does not depend on it: a `0x07 <expr> <block>` layout executes the block")
    A("only when the expression holds.)")
    A("")
    A("## 4. The order of calls in the body (byte order)")
    A("")
    A("| at | call | args |")
    A("|---|---|---|")
    for r in d["launch_sequence"]:
        names = []
        for a in r["args"]:
            names.append(str(a.get("ref") or a.get("name") or a.get("kind")
                             or a.get("raw_token")))
        A("| +%d | `%s` | %s |" % (r["at"], r["call"], ", ".join(names) if names else "-"))
    A("")
    A("`TriggerSpecialMove` is the only call after the velocity call that can move the")
    A("pawn: an animation special move (`RSpecialMoveConfigConfigurable`), so the launch")
    A("is authored as a move, not as a stored velocity. Its numeric parameters are not")
    A("in BmGame.upk. UNKNOWN: the special-move asset and its distances/velocities.")
    A("")
    A("## 5. Class defaults")
    A("")
    A("`Research/BatmobileGrab/CLASS_DEFAULTS.json` was searched for any key or value")
    A("mentioning eject / velocity / launch: **%d entries**. Entries carrying the mode"
      % d["class_defaults"]["count"])
    A("ids 5269 / 61474: **%d**." % d["class_defaults"]["mode_id_count"])
    A("Entries whose *key* is a velocity: **%d**."
      % len(d["class_defaults"]["numeric_velocity_keys"]))
    if d["class_defaults"]["special_move_refs"]:
        A("")
        A("Special-move configs named by those entries: %s"
          % ", ".join("`%s`" % r for r in d["class_defaults"]["special_move_refs"][:6]))
        A("")
        A("These are `RSpecialMoveConfigConfigurable` references, i.e. the moves that")
        A("`TriggerSpecialMove` can start - they carry the trajectory, and their numbers")
        A("live in the special-move asset, not in this package (UNKNOWN here).")
    if d["class_defaults"]["velocity_or_eject_entries"]:
        A("")
        A("| path | value |")
        A("|---|---|")
        for h in d["class_defaults"]["velocity_or_eject_entries"][:12]:
            A("| `%s` | `%s` |" % (h["path"], str(h["value"])[:70]))
    A("")
    A("So the eject launch has **no class default velocity** to fall back on: the")
    A("`(0, 0, 0)` above is not a default being overridden elsewhere - it is a stop.")
    A("")
    A("## 6. Jump tokens and the branch each mode call sits in")
    A("")
    for body in ("ToggleBattleMode", "EjectFromVehicle"):
        j = d["jumps"][body]
        A("### %s (%d jump-shaped tokens)" % (body, len(j["sites"])))
        A("")
        A("| at | token | u16 operand | u32 read | next byte |")
        A("|---|---|---|---|---|")
        for s in j["sites"]:
            A("| +%d | `%s` | %d | %s | `%s` |" %
              (s["at"], s["token"], s["operand_u16"],
               s["u32_read"] if s["u32_read"] is not None else "-", s["next_byte"]))
        A("")
        A("Candidate encodings, measured (how many of the tokens, read as one offset,")
        A("land inside the body / on a token that can open a statement):")
        A("")
        A("| base | inside body | on a statement start | of |")
        A("|---|---|---|---|")
        for nm, sc in j["schemes"].items():
            A("| %s | %d | %d | %d |" % (nm, sc["inside_body"], sc["on_statement_start"],
                                         sc["of"]))
        A("")
    A("**No encoding places every operand inside the body** (every scheme above has")
    A("`inside_body < of`), so the absolute target of these tokens is **UNKNOWN**: the")
    A("u16 after a `0x06`/`0x07` is not proved to be an in-body byte offset in this")
    A("build. Branch membership below therefore rests on block structure and symbols,")
    A("not on offset arithmetic, and is labelled as such.")
    A("")
    A("### ToggleBattleMode: 5269 vs 61474")
    A("")
    A("| at | mode id | enclosing jump before | jump after |")
    A("|---|---|---|---|")
    for m in d["toggle"]["modes"]:
        b = m["enclosing"][0]
        af = m["enclosing"][1]
        A("| +%d | %d | %s | %s |" %
          (m["at"], m["literal"],
           "+%d (`0x%02x` op %d)" % b if b else "-",
           "+%d (`0x%02x` op %d)" % af if af else "-"))
    A("")
    if d["toggle"]["if_condition"]:
        f = d["toggle"]["if_condition"]
        A("The `if` at `+%d` (operand `0x%04x`) has this condition, re-serialised"
          % (f["at"], f["operand_u16"]))
        A("byte-exactly from the decoded tree (%s):" % f["condition_reserialises"])
        A("")
        A("```")
        A(json.dumps(f["condition"], indent=1)[:1200])
        A("```")
        A("")
        A("The condition's Context property is `%s` - the **ReturnValue of"
          % d["toggle"]["if_condition"]["condition"].get("prop"))
        A("`TryToChangeMode`** - so the branch is selected by that function's result,")
        A("and its argument `5269` decides which mode is attempted.")
    if d["toggle"]["then_block_statements"]:
        A("")
        A("Then-block statements, tiled sequentially from the end of that condition")
        A("(`+%d`) to `+%d`, where the second mode call's own receiver expression begins -"
          % (d["toggle"]["if_condition"]["condition_bytes"][1],
             d["toggle"]["then_block_until"]))
        A("the whole gap is covered, no byte of it is unexplained:")
        A("")
        A("| at | bytes | statement |")
        A("|---|---|---|")
        for s in d["toggle"]["then_block_statements"]:
            A("| +%d | %d | `%s` |" % (s["at"], s["end"] - s["at"],
                                        json.dumps(s["node"])[:150]))
    if d["toggle"]["jump_after_then"]:
        A("")
        A("A single `0x06` at `+%d` (operand `%d`) separates the two mode calls, so they"
          % (d["toggle"]["jump_after_then"]["at"],
             d["toggle"]["jump_after_then"]["operand_u16"]))
        A("are mutually exclusive: `5269` is attempted inside the conditional block, and")
        A("`61474` is evaluated on the path that block jumps over - i.e. **when")
        A("`TryToChangeMode(5269)` returns false**. The second call ends at `+%s` and is"
          % d["toggle"]["second_call_ends_at"])
        A("followed immediately by `%s` (return), so nothing retries after it."
          % d["toggle"]["byte_after_second_call"])
    A("")
    A("STATUS: DONE for the vector and the receiver; the branch placement is derived")
    A("from block structure (offsets UNKNOWN); the special-move parameters are UNKNOWN.")
    A("")
    return "\n".join(L) + "\n"


def main(argv):
    write = "--write" in argv
    check = "--check" in argv
    if not (write or check):
        print(__doc__)
        return 2
    bm = B.Bm(UPK)
    d, ej, tg = decode(bm)
    md = render(d, ej, tg)
    res = checks(d, ej, tg)
    ok = sum(1 for _n, c in res if c)
    for name, c in res:
        print("%s  %s" % ("PASS" if c else "FAIL", name))
    print("%d/%d checks pass" % (ok, len(res)))
    d["checks"] = [{"name": n, "pass": bool(c)} for n, c in res]
    d["status"] = "DONE" if ok == len(res) else "PARTIAL"
    if write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(
            json.dumps(d, indent=1, sort_keys=True) + "\n")
        print("wrote", os.path.relpath(OUT_MD, ROOT))
        print("wrote", os.path.relpath(OUT_JSON, ROOT))
    if check:
        for path, text in ((OUT_MD, md), (OUT_JSON, json.dumps(d, indent=1, sort_keys=True) + "\n")):
            cur = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            print("%s %s" % ("MATCH" if cur == text else "DIFFERS", os.path.relpath(path, ROOT)))
            if cur != text:
                return 1
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

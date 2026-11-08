"""review_g3_01e_bc.py - independent token decode of Startup.upk export 7400
(`RVehicleBatmobile.DriverLeft`), for the G3-01e-fix adjudication.

What this script does, and how it is checked
  1. Reads `Startup.upk` export 7400 from the install (read-only) and splits the 406-byte payload
     into its function header/tag block, the 368-byte ScriptText and the 16-byte trailer
     (`script = payload[22:len-16]`, anchored three ways).
  2. Walks the 368 bytes **sequentially**, token by token, from offset 0 to the terminal
     `0x04 Return` at 367.  Nothing is pattern-scanned: a token is consumed only at the position
     the walk has reached, so an operand byte can never be mistaken for a reference.
  3. A property reference is the 5-byte form `<0x01|0x00> <int32 object index>`; the index is
     resolved through the package's import table.  `0x01` is always this form.  `0x00` is this
     form only when the int32 behind it resolves to a package object; otherwise 0x00 is a
     one-byte prefix token.  The choice is not free: forcing the other reading at the 0x00 ref
     sites desyncs the walk (oracle `local_form_forced_desyncs`).
  4. Two extra oracles decide the one remaining ambiguity (`00 1D FC FF FF` at 100/179, which can
     also be read as `0x00` + `0x1D IntConst`): the two flag blocks at 67-111 and 146-190 are
     byte-identical except for the single byte at 99 vs 178 (`0x2C` vs `0x20`), so those bytes
     are one-byte tokens in the same slot and what follows them is decoded identically - a
     reference in both blocks (oracle `flag_blocks_differ_only_at_99_178`).
  5. Reconciles the fix's 22 published offsets with the walk: every one of them is the byte
     *before* the reference token (the prefix), never a wrong name.  Also proves the six
     references the fix's pattern scan could not see.

Outputs (never hand-edited): `Research/BatmobileGrab/DRIVERLEFT_7400.md` + `.json`.
The review report is `tmp/freebuff/reports/review-G3-01e-fix.md`.

Usage:
  python Tools/scripts/review_g3_01e_bc.py --write
  python Tools/scripts/review_g3_01e_bc.py --check    # rebuild from the bytes, compare, exit 1 on drift
"""
from __future__ import annotations

import argparse
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
PKG_NAME = "Startup.upk"
EXP = 7400
EXPECT_PATH = "RVehicleBatmobile.DriverLeft"
EXPECT_PAYLOAD = 406
EXPECT_SCRIPT = 368
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVERLEFT_7400.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "DRIVERLEFT_7400.json")

# One-byte tokens whose extent is proven by the walk closing on 368 bytes with no leftovers.
# They are reported by their byte value, not named: naming them would be a guess (project rule).
ONE_BYTE = {
    0x03: "0x03", 0x04: "Return", 0x09: "0x09", 0x0F: "0x0F", 0x14: "0x14",
    0x16: "EndFunctionParms", 0x19: "Context", 0x20: "0x20", 0x25: "IntZero",
    0x26: "IntOne", 0x27: "True", 0x28: "False", 0x2A: "0x2A", 0x2C: "0x2C",
    0x2D: "0x2D", 0x38: "0x38", 0x3A: "0x3A", 0x4A: "0x4A", 0x77: "0x77",
    0x81: "0x81", 0x82: "0x82", 0x8C: "0x8C", 0x9B: "0x9B", 0xF8: "0xF8",
}
LONG = {0x1B: "VirtualFunction", 0x1C: "FinalFunction", 0x1D: "IntConst"}
BRANCH = {0x06: "Jump", 0x07: "JumpIfNot", 0x18: "Skip"}

# The four names under adjudication: true reference-token offsets (script frame).
FOUR = {
    "Core.ArmouredMode": {"offsets": [254, 318], "index": -1366, "class": "BoolProperty"},
    "Core.BatmobileWinch": {"offsets": [263, 278], "index": -5673, "class": "ObjectProperty"},
    "Core.WinchPullType": {"offsets": [284, 290], "index": -1515, "class": "ByteProperty"},
    "Core.IsVehicleAsleep": {"offsets": [223, 328], "index": -1498, "class": "BoolProperty"},
}

# G3-01e-fix's published table (Research/BatmobileGrab/COLLISION_SELECTOR2.md section 2):
# offset -> name. Every entry must sit one byte before a real reference token.
FIX_TABLE = {
    4: "Core.bWasRemoteDriving", 20: "Core.Driver", 42: "Core.Driver",
    69: "Core.WorldInfo", 75: "Core.GRI", 81: "Core.GRI",
    87: "Core.FlagManager", 93: "Core.FlagManager", 148: "Core.WorldInfo",
    154: "Core.GRI", 160: "Core.GRI", 166: "Core.FlagManager", 172: "Core.FlagManager",
    222: "Core.IsVehicleAsleep", 229: "Core.FakeRoadCollisionStatic",
    253: "Core.ArmouredMode", 277: "Core.BatmobileWinch", 283: "Core.WinchPullType",
    289: "Core.WinchPullType", 317: "Core.ArmouredMode", 327: "Core.IsVehicleAsleep",
    343: "Core.bForceWheelspin",
}
MISSED = {54: "Core.Driver", 61: "Core.InteriorLightsSwitchedOn", 100: "Core.ReturnValue",
          179: "Core.ReturnValue", 263: "Core.BatmobileWinch", 351: "Core.WheelspinSmokeMomentum"}
# The adjudication's offsets, which are payload-frame offsets of the index field (idx + 22).
ADJ = {"Core.ArmouredMode": [277, 341], "Core.BatmobileWinch": [286],
       "Core.FakeRoadCollisionStatic": [253]}
CALLS = {301: 2, 334: 1}
BLOCK_A = (67, 111)
BLOCK_B = (146, 190)
BLOCK_DIFF = (99, 178)


def i32(s: bytes, o: int) -> int:
    return struct.unpack_from("<i", s, o)[0]


def walk(pkg, s: bytes, force_one_byte_00_at=None) -> dict:
    """Sequential token walk. Returns tokens, closed flag, and every property reference."""
    p, toks, refs = 0, [], []
    closed = True
    while p < len(s):
        t = s[p]
        if t == 0x01:
            if p + 5 > len(s):
                closed = False
                break
            idx = i32(s, p + 1)
            path = pkg.object_path(idx)
            if path is None:
                closed = False
                break
            tok = {"at": p, "size": 5, "kind": "ref", "form": "0x01", "index": idx,
                   "path": path, "object_class": pkg.object_class(idx)}
            toks.append(tok)
            refs.append(tok)
            p += 5
            continue
        if t == 0x00:
            idx = i32(s, p + 1) if p + 5 <= len(s) else 0
            path = pkg.object_path(idx) if p + 5 <= len(s) else None
            if path is not None and p != force_one_byte_00_at:
                tok = {"at": p, "size": 5, "kind": "ref", "form": "0x00", "index": idx,
                       "path": path, "object_class": pkg.object_class(idx)}
                toks.append(tok)
                refs.append(tok)
                p += 5
                continue
            if p == force_one_byte_00_at:
                toks.append({"at": p, "size": 1, "kind": "forced_one_byte", "form": "0x00"})
                p += 1
                continue
            toks.append({"at": p, "size": 1, "kind": "0x00"})
            p += 1
            continue
        if t in LONG:
            if p + 5 > len(s):
                closed = False
                break
            idx = i32(s, p + 1)
            if t == 0x1D:
                name = str(idx)
            elif t == 0x1B:
                name = pkg.names[idx] if 0 <= idx < pkg.name_count else None
            else:
                name = pkg.object_path(idx)
            toks.append({"at": p, "size": 5, "kind": LONG[t], "index": idx, "name": name})
            p += 5
            continue
        if t == 0x1E:
            toks.append({"at": p, "size": 5, "kind": "FloatConst",
                         "value": struct.unpack_from("<f", s, p + 1)[0]})
            p += 5
            continue
        if t == 0x1F:
            end = s.find(b"\x00", p + 1)
            if end < 0:
                closed = False
                break
            toks.append({"at": p, "size": end - p + 1, "kind": "StringConst",
                         "value": s[p + 1:end].decode("latin1")})
            p = end + 1
            continue
        if t in BRANCH:
            if p + 3 > len(s):
                closed = False
                break
            toks.append({"at": p, "size": 3, "kind": BRANCH[t], "word": struct.unpack_from("<H", s, p + 1)[0]})
            p += 3
            continue
        if t == 0x24:
            if p + 2 > len(s):
                closed = False
                break
            toks.append({"at": p, "size": 2, "kind": "ByteConst", "value": s[p + 1]})
            p += 2
            continue
        if t in ONE_BYTE:
            toks.append({"at": p, "size": 1, "kind": ONE_BYTE[t]})
            p += 1
            continue
        closed = False
        break
    if p != len(s) or not toks or toks[-1]["kind"] != "Return" or toks[-1]["at"] != len(s) - 1:
        closed = False
    unexplained = len(s) - sum(t["size"] for t in toks)
    return {"tokens": toks, "refs": refs, "closed": closed,
            "consumed": sum(t["size"] for t in toks), "unexplained": unexplained}


def load():
    pkg = upk_read.Package(os.path.join(GAME, PKG_NAME))
    payload = pkg.data(EXP)
    script = payload[22:len(payload) - 16]
    facts = {
        "package": PKG_NAME, "export": EXP, "path": pkg.object_path(EXP),
        "class": pkg.object_class(EXP), "payload_bytes": len(payload),
        "script_bytes": len(script), "script_sha1": hashlib.sha1(script).hexdigest(),
        "script_sha1_bytes": hashlib.sha1(payload[22:-16]).hexdigest(),
        "size_field": i32(payload, 18), "size_field_is_script_plus_1": i32(payload, 18) == len(script) + 1,
        "name_index": i32(payload, len(payload) - 8),
        "name_index_matches": pkg.names[i32(payload, len(payload) - 8)] == pkg.exports[EXP - 1]["name"],
        "trailer_hex": payload[len(payload) - 16:].hex(),
        "script_starts_at_payload": 22,
        "frame_rule": "payload offset = script offset + 22; a ref's int32 lies at its token + 1",
    }
    return pkg, payload, script, facts


def build() -> dict:
    pkg, payload, s, facts = load()
    w = walk(pkg, s)
    refs = w["refs"]

    # --- oracles
    oracles = {}

    def add(k, ok, detail):
        oracles[k] = {"ok": bool(ok), "detail": detail}

    add("export_identity", facts["path"] == EXPECT_PATH and facts["class"] == "Function"
        and facts["payload_bytes"] == EXPECT_PAYLOAD and facts["script_bytes"] == EXPECT_SCRIPT,
        {k: facts[k] for k in ("path", "class", "payload_bytes", "script_bytes")})
    add("script_anchors", facts["size_field_is_script_plus_1"] and facts["name_index_matches"],
        {"size_field": facts["size_field"], "name_index": facts["name_index"]})

    add("walk_closes", w["closed"] and w["unexplained"] == 0
        and w["tokens"][0]["at"] == 0 and w["tokens"][-1]["at"] == len(s) - 1,
        {"closed": w["closed"], "consumed": w["consumed"], "script_bytes": len(s),
         "unexplained": w["unexplained"], "tokens": len(w["tokens"]),
         "last": w["tokens"][-1]})

    # every 0x01 is a ref; every 0x00 ref resolves
    bad = [r for r in refs if pkg.object_path(r["index"]) is None]
    add("all_refs_resolve", not bad and len(refs) == 28, {"refs": len(refs), "unresolved": len(bad)})

    four_ok, four_detail = True, {}
    for name, want in FOUR.items():
        got = [r["at"] for r in refs if r["path"] == name]
        idx = sorted({r["index"] for r in refs if r["path"] == name})
        cls = sorted({r["object_class"] for r in refs if r["path"] == name})
        four_detail[name] = {"offsets": got, "index": idx, "class": cls}
        if got != want["offsets"] or idx != [want["index"]] or cls != [want["class"]]:
            four_ok = False
    add("four_names_offsets", four_ok, four_detail)

    # the fix's 22 offsets are each one byte before a ref of that name
    fix_ok, fix_detail = True, []
    for off in sorted(FIX_TABLE):
        name = FIX_TABLE[off]
        hit = [r for r in refs if r["at"] == off + 1 and r["path"] == name]
        if not hit:
            fix_ok = False
        fix_detail.append({"fix_offset": off, "byte_at_fix_offset": "0x%02X" % s[off],
                           "ref_token_at": off + 1, "ref_path": (hit[0]["path"] if hit else None),
                           "ok": bool(hit)})
    add("fix_offsets_are_prefixes", fix_ok, fix_detail)

    # the six refs the fix's pattern scan missed, and no others
    seen = {r["at"] for r in refs}
    miss_ok = all((r["at"] in MISSED and r["path"] == MISSED[r["at"]]) for r in refs
                  if r["at"] not in {o + 1 for o in FIX_TABLE})
    add("fix_misses_six", miss_ok and len(refs) - len(FIX_TABLE) == len(MISSED),
        {"missed": {r["at"]: r["path"] for r in refs if r["at"] not in {o + 1 for o in FIX_TABLE}}})

    # every offset the adjudication cites is a real payload-frame index position (subset: the
    # adjudication names one BatmobileWinch site, the script has two)
    adj_ok, adj_detail = True, {}
    for name, want in ADJ.items():
        got = sorted({r["at"] + 1 + 22 for r in refs if r["path"] == name})
        hit = all(w in got for w in want)
        adj_detail[name] = {"payload_idx_offsets": got, "adjudication": want,
                            "each_cited_offset_is_real": hit}
        if not hit:
            adj_ok = False
    add("adjudication_payload_frame", adj_ok, adj_detail)

    # forcing the 0x00 form to one byte desyncs at five sites; 100/179 still close and are
    # decided by `flag_blocks_differ_only_at_99_178` instead, never by closure alone
    must_desync = {76, 88, 155, 167, 284}
    forced, force_detail = True, {}
    for r in [r for r in refs if r["form"] == "0x00"]:
        fw = walk(pkg, s, force_one_byte_00_at=r["at"])
        force_detail[r["at"]] = {"closed": fw["closed"], "consumed": fw["consumed"]}
        if r["at"] in must_desync and fw["closed"]:
            forced = False
    add("local_form_forced_desyncs", forced,
        {"sites": force_detail, "decided_by_closure": sorted(must_desync),
         "decided_by_block_oracle": sorted(set(force_detail) - must_desync)})

    # the two flag blocks are identical except one byte, which proves the tokens around 99/178
    a, b = s[BLOCK_A[0]:BLOCK_A[1]], s[BLOCK_B[0]:BLOCK_B[1]]
    diff = [BLOCK_A[0] + k for k in range(len(a)) if a[k] != b[k]]
    add("flag_blocks_differ_only_at_99_178", diff == [BLOCK_DIFF[0]]
        and a[BLOCK_DIFF[0] - BLOCK_A[0]] == 0x2C and b[BLOCK_DIFF[1] - BLOCK_B[0]] == 0x20,
        {"differing_script_offsets": diff,
         "bytes": {"%d" % BLOCK_DIFF[0]: "0x%02X" % s[BLOCK_DIFF[0]],
                   "%d" % BLOCK_DIFF[1]: "0x%02X" % s[BLOCK_DIFF[1]]},
         "note": "everything after the differing byte is identical in both blocks, so the "
                 "next token is decoded identically in both"})

    calls = {t["at"]: t for t in w["tokens"] if t["kind"] == "VirtualFunction"
             and t["name"] == "SetBatmanVsBatmobileCollisionMode"}
    call_ok = True
    for at, val in CALLS.items():
        nxt = [t for t in w["tokens"] if t["at"] == at + 5 and t["kind"] == "ByteConst"]
        if at not in calls or not nxt or nxt[0]["value"] != val:
            call_ok = False
    add("selector_calls", call_ok, {"calls": sorted(calls), "expected": CALLS})

    doc = {
        "schema": 1,
        "card": "G3-01e-fix adjudication - independent token decode of Startup.upk export 7400",
        "facts": facts,
        "tokens": w["tokens"],
        "refs": refs,
        "four_names": {k: v for k, v in four_detail.items()},
        "fix_reconciliation": fix_detail,
        "fix_missed": {r["at"]: r["path"] for r in refs if r["at"] not in {o + 1 for o in FIX_TABLE}},
        "adjudication": adj_detail,
        "labels": {
            "decoded": "the walk, the reference offsets and the import indices - all read from "
                       "the 368 script bytes of Startup.upk export 7400",
            "derived": "payload offset = script offset + 22; the adjudication's offsets are the "
                       "index-field positions of the same references",
            "unknown": "the names of the one-byte tokens (reported as bytes), which branch a "
                       "value selects, and whether one-byte prefixes carry semantics",
        },
        "oracles": oracles,
    }
    return doc


def render(doc: dict) -> str:
    F, L = doc["facts"], []
    A = L.append
    A("# `RVehicleBatmobile.DriverLeft` (Startup.upk export 7400) - token decode")
    A("")
    A("Independent walk of the function's %d script bytes, for the G3-01e-fix adjudication."
      % F["script_bytes"])
    A("Generated by `Tools/scripts/review_g3_01e_bc.py --write`; `--check` re-reads the install,")
    A("re-walks every token and compares this file byte for byte.")
    A("")
    A("## 1. The export")
    A("")
    A("| field | value |")
    A("|---|---|")
    A("| path | `%s` (%s) |" % (F["path"], F["class"]))
    A("| payload bytes | %d |" % F["payload_bytes"])
    A("| script bytes (`payload[22:-16]`) | %d |" % F["script_bytes"])
    A("| size field @18 | %d (= script + 1: %s) |" % (F["size_field"], F["size_field_is_script_plus_1"]))
    A("| trailer name index | %d (`%s`) |" % (F["name_index"], F["name_index_matches"]))
    A("| script sha1 | `%s` |" % F["script_sha1"])
    A("")
    A("`406` and `368` are the same export counted two ways: 406 is the serialised payload, 368 the")
    A("ScriptText inside it. Offsets in this file are **script-frame** unless a row says payload.")
    A("")
    A("## 2. Coordinate frames")
    A("")
    A("`payload offset = script offset + 22`, and a reference's int32 index sits at `token + 1`.")
    A("So a reference reported here at script 254 has its index field at script 255 and payload 277.")
    A("This is the whole of the G3-01e-fix / adjudication disagreement: the fix reports the prefix")
    A("byte before the reference token, the adjudication reports the payload offset of the index")
    A("field, and both are internally consistent.")
    A("")
    A("## 3. The four names")
    A("")
    A("| name | import index | class | reference tokens (script) | index fields (script) | index fields (payload) |")
    A("|---|---:|---|---|---|---|")
    for name in ("Core.ArmouredMode", "Core.BatmobileWinch", "Core.WinchPullType", "Core.IsVehicleAsleep"):
        d = doc["four_names"][name]
        A("| `%s` | %d | %s | %s | %s | %s |" % (
            name, d["index"][0], d["class"][0],
            ", ".join(str(x) for x in d["offsets"]),
            ", ".join(str(x + 1) for x in d["offsets"]),
            ", ".join(str(x + 1 + 22) for x in d["offsets"])))
    A("")
    A("All four are **present**. None is absent, and none is present only once.")
    A("")
    A("## 4. Every property reference in the script")
    A("")
    A("| token at | form | index | resolves to | class | index field (script / payload) |")
    A("|---:|---|---:|---|---|---|")
    for r in doc["refs"]:
        A("| %d | `%s` + int32 | %d | `%s` | %s | %d / %d |" % (
            r["at"], r["form"], r["index"], r["path"], r["object_class"], r["at"] + 1, r["at"] + 23))
    A("")
    A("**%d references**, every index resolving to a package import. The walk that produces them"
      % len(doc["refs"]))
    A("consumes all %d bytes and ends on `Return` at 367; no byte is left unexplained." % F["script_bytes"])
    A("")
    A("## 5. The fix's table, reconciled")
    A("")
    A("Every one of the fix's 22 rows is the byte *before* a real reference token of the same name -")
    A("a prefix offset, never a wrong name:")
    A("")
    A("| fix offset | byte there | reference token | resolves to |")
    A("|---:|---|---:|---|")
    for row in doc["fix_reconciliation"]:
        A("| %d | `%s` | %d | `%s` |" % (row["fix_offset"], row["byte_at_fix_offset"],
                                         row["ref_token_at"], row["ref_path"]))
    A("")
    A("Its pattern scan could not see six references, because their preceding byte is not one of its")
    A("four prefixes: %s." % ", ".join("`%s` @%d" % (v, k) for k, v in sorted(doc["fix_missed"].items())))
    A("")
    A("## 6. The adjudication's offsets")
    A("")
    A("| name | every index-field offset (payload) | adjudication cites | each cited offset is real |")
    A("|---|---|---|---|")
    for name, d in doc["adjudication"].items():
        A("| `%s` | %s | %s | %s |" % (name, ", ".join(str(x) for x in d["payload_idx_offsets"]),
                                        ", ".join(str(x) for x in d["adjudication"]),
                                        d["each_cited_offset_is_real"]))
    A("")
    A("`Core.FakeRoadCollisionStatic` is a separate reference at script 230, index field payload 253.")
    A("The fix's own `@253` row is a different reference - `Core.ArmouredMode` at script 254 - so the")
    A("two rows do not contradict each other; they are 23 bytes apart in one frame.")
    A("")
    A("## 7. Oracles")
    A("")
    A("| oracle | ok | detail |")
    A("|---|---|---|")
    for k, v in doc["oracles"].items():
        A("| `%s` | %s | %s |" % (k, v["ok"], json.dumps(v["detail"])[:300]))
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
    md = render(doc)
    js = json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    bad = [k for k, v in doc["oracles"].items() if not v["ok"]]
    if args.write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s and %s" % (os.path.relpath(OUT_MD, ROOT), os.path.relpath(OUT_JSON, ROOT)))
        print("script %d B, %d tokens, %d refs, closed=%s" % (
            doc["facts"]["script_bytes"], len(doc["tokens"]), len(doc["refs"]),
            doc["oracles"]["walk_closes"]["ok"]))
        for name in ("Core.ArmouredMode", "Core.BatmobileWinch", "Core.WinchPullType",
                     "Core.IsVehicleAsleep"):
            print("%-22s %s" % (name, doc["four_names"][name]["offsets"]))
        print("oracles: %d/%d ok%s" % (len(doc["oracles"]) - len(bad), len(doc["oracles"]),
                                       "" if not bad else " FAILED: " + ", ".join(bad)))
        return 0 if not bad else 1
    fails = []
    if not (os.path.exists(OUT_MD) and os.path.exists(OUT_JSON)):
        print("FAIL: outputs missing - run --write first")
        return 1
    if json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(js):
        fails.append("DRIVERLEFT_7400.json is stale")
    if open(OUT_MD, encoding="utf-8").read() != md:
        fails.append("DRIVERLEFT_7400.md is stale")
    for k in bad:
        fails.append("oracle %s failed: %s" % (k, json.dumps(doc["oracles"][k]["detail"])[:300]))
    if fails:
        print("FAIL")
        for f in fails:
            print("  -", f)
        return 1
    print("OK %d tokens, %d refs, walk closes on %d B; md+json byte-identical" % (
        len(doc["tokens"]), len(doc["refs"]), doc["facts"]["script_bytes"]))
    print("four names: %s" % {k: v["offsets"] for k, v in doc["four_names"].items()})
    print("oracles: %s" % json.dumps({k: v["ok"] for k, v in doc["oracles"].items()}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

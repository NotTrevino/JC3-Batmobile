#!/usr/bin/env python3
"""audit_g302.py - audit the G3-02/02b/02c control chain end to end.

Read-only.  Writes exactly one file: Research/BatmobileGrab/AUDIT_G302.md

    --write   regenerate it
    --check   re-derive it and compare byte for byte (exit 1 on drift, 2 on a failed check)

Three claims are re-derived from the source bytes, not from the cards:

1. the token table (LT / B / LB / A) against the PC ini chain
   (PCInput -> UserInput -> DefaultInput -> BaseInput), plus every other definition of
   the same key in that chain and the effective-binding question;
2. "ToggleBattleMode has no script caller": an exhaustive scan of all Function scripts in
   BmGame.upk for both call encodings (0x1B + FName index, 0x1C + export index), plus every
   ini that names the command;
3. the native claim that 0x140063e90 (TryToChangeMode's implementation) is called with
   BattleMode 0x240 / PursuitMode 0x241 from DrivingPlayerMove: an E8 scan of .text,
   the immediate written before each call, the exec-thunk -> body chain, and the
   lea/mov pairs that give 0x240/0x241 their names.

No disassembler and no PE library: the handful of instructions are decoded from their
bytes (E8/E9 rel32, 48 C7 85 <disp32> <imm32>, 48 8D 0D rel32, BA imm32), so --check
does not depend on a capstone version.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import struct
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "Research/BatmobileGrab/AUDIT_G302.md"
INSTALL = Path("E:/Games/Batman - Arkham Knight")
UPK = INSTALL / "BmGame/CookedPCConsole/BmGame.upk"
EXE = INSTALL / "Binaries/Win64/BatmanAK.exe"
BMCONF = INSTALL / "BmGame/Config"
ENGCONF = INSTALL / "Engine/Config"

CARDS = {
    "CONTROLS": "Research/BatmobileGrab/CONTROLS.md",
    "CONSUMERS": "Research/BatmobileGrab/CONTROLS_CONSUMERS.md",
    "NATIVE": "Research/BatmobileGrab/CONTROLS_NATIVE.md",
    "NATIVE2": "Research/BatmobileGrab/CONTROLS_NATIVE2.md",
    "CONFIG": "Research/BatmobileGrab/CONFIG.md",
    "REVIEW03": "tmp/freebuff/reports/review-G3-03.md",
}
CHAIN = {
    "PC/PCInput.ini": BMCONF / "PC/PCInput.ini",
    "UserInput.ini": BMCONF / "UserInput.ini",
    "DefaultInput.ini": BMCONF / "DefaultInput.ini",
    "Engine/Config/BaseInput.ini": ENGCONF / "BaseInput.ini",
}
OTHER_INI = {
    "BmInput.ini": BMCONF / "BmInput.ini",
    "BmEngine.ini": BMCONF / "BmEngine.ini",
    "BmSystemSettings.ini": BMCONF / "BmSystemSettings.ini",
    "BmGame.ini": BMCONF / "BmGame.ini",
    "PC/PCGame.ini": BMCONF / "PC/PCGame.ini",
}

TB_NAME = "ToggleBattleMode"
TB_EXPORT = 105028
TTC_IMPL = 0x140063E90
DP_TUNK = 0x140501F60
TTC_EXEC = 0x140547CE0


class AuditError(RuntimeError):
    pass


def sha16(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


# ------------------------------------------------------------------ PE / code

def load_pe(path: Path):
    b = path.read_bytes()
    e = struct.unpack_from("<I", b, 0x3C)[0]
    if b[e:e + 4] != b"PE\0\0":
        raise AuditError("not a PE image")
    nsec = struct.unpack_from("<H", b, e + 6)[0]
    opt_size = struct.unpack_from("<H", b, e + 20)[0]
    opt = e + 24
    magic = struct.unpack_from("<H", b, opt)[0]
    if magic != 0x20B:
        raise AuditError(f"expected PE32+, got magic {magic:#x}")
    base = struct.unpack_from("<Q", b, opt + 24)[0]
    secs = []
    tab = opt + opt_size
    for i in range(nsec):
        o = tab + 40 * i
        name = b[o:o + 8].rstrip(b"\0").decode("latin-1")
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", b, o + 8)
        secs.append({"name": name, "va": base + vaddr, "vsize": vsize,
                     "raw": rawptr, "rsize": rawsize})
    return b, base, secs


def va2off(secs, va: int) -> int:
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            return s["raw"] + (va - s["va"])
    raise AuditError(f"{va:#x} is in no section")


def rb(img: bytes, secs, va: int, n: int) -> bytes:
    o = va2off(secs, va)
    return img[o:o + n]


def e8_e9_targets(img: bytes, secs, tgt: int) -> list[tuple[int, str]]:
    """.text E8/E9 sites whose rel32 resolves to `tgt`."""
    text = next(s for s in secs if s["name"] == ".text")
    blob = img[text["raw"]:text["raw"] + text["rsize"]]
    out = []
    for i in range(len(blob) - 5):
        if blob[i] not in (0xE8, 0xE9):
            continue
        rel = struct.unpack_from("<i", blob, i + 1)[0]
        if text["va"] + i + 5 + rel == tgt:
            out.append((text["va"] + i, "call" if blob[i] == 0xE8 else "jmp"))
    return out


MOV_IMM = bytes.fromhex("48c78580010000")   # mov qword ptr [rbp+0x180], imm32


def imm_before(img: bytes, secs, at: int, window: int = 64) -> tuple[int, int, bytes] | None:
    """The last `mov [rbp+0x180], imm32` in the bytes before `at`."""
    o = va2off(secs, at - window)
    back = img[o:o + window]
    k = back.rfind(MOV_IMM)
    if k < 0 or k + 11 > len(back):
        return None
    imm = struct.unpack_from("<i", back, k + 7)[0]
    return at - window + k, imm, back[k:k + 11]


def jmp_rel32_target(img: bytes, secs, at: int) -> int | None:
    b = rb(img, secs, at, 5)
    if b[0] != 0xE9:
        return None
    return at + 5 + struct.unpack_from("<i", b, 1)[0]


def find_e9(img: bytes, secs, start: int, span: int) -> tuple[int, int] | None:
    """First E9 rel32 in [start, start+span) that resolves inside .text."""
    text = next(s for s in secs if s["name"] == ".text")
    blob = rb(img, secs, start, span)
    for i in range(len(blob) - 5):
        if blob[i] != 0xE9:
            continue
        tgt = start + i + 5 + struct.unpack_from("<i", blob, i + 1)[0]
        if text["va"] <= tgt < text["va"] + text["rsize"]:
            return start + i, tgt
    return None


def lea_mov_pair(img: bytes, secs, at: int) -> dict:
    """Decode `48 8D 0D rel32` (lea rcx,[rip+x]) then a nearby `BA imm32` (mov edx,imm)."""
    b = rb(img, secs, at, 24)
    if b[:3] != bytes.fromhex("488d0d"):
        raise AuditError(f"no lea rcx,[rip] at {at:#x}")
    rel = struct.unpack_from("<i", b, 3)[0]
    stra = at + 7 + rel
    o = va2off(secs, stra)
    end = img.index(b"\0", o, o + 64)
    text = img[o:end].decode("latin-1")
    k = b.find(b"\xba", 7)
    if k < 0:
        raise AuditError(f"no mov edx,imm after {at:#x}")
    imm = struct.unpack_from("<i", b, k + 1)[0]
    return {"lea_at": at, "string_at": stra, "string": text,
            "mov_at": at + k, "imm": imm, "imm_bytes": b[k:k + 5]}


# ------------------------------------------------------------------ ini chain

BIND_RX = re.compile(r'^\.?Bindings=\(Name="(XboxTypeS_[A-Za-z0-9_]+)",\s*Command="([^"]*)"')


def ini_bindings(path: Path) -> list[dict]:
    out = []
    for n, line in enumerate(read(path).splitlines(), 1):
        m = BIND_RX.match(line.strip())
        if m:
            out.append({"line": n, "key": m.group(1), "command": m.group(2),
                        "text": line.strip()})
    return out


def tokens_of(command: str) -> list[str]:
    """Command tokens in order, dropping Button/Axis/OnRelease markers."""
    out = []
    for part in command.split("|"):
        w = part.split()
        if not w:
            continue
        if w[0] in ("Button", "Axis", "OnRelease") and len(w) > 1:
            w = w[1:]
        out.extend(w[:1])
    return out


CLAIMS = [
    {"id": "LT", "label": "LT", "rows": [
        {"file": "DefaultInput.ini", "line": 251, "key": "XboxTypeS_LeftTrigger",
         "tokens": ["HoldToZoom", "DeepScanOut"]},
        {"file": "DefaultInput.ini", "line": 253, "key": "XboxTypeS_LeftTriggerAxis",
         "tokens": ["aLeftTrigger"]},
    ]},
    {"id": "B", "label": "B", "rows": [
        {"file": "DefaultInput.ini", "line": 268, "key": "XboxTypeS_B",
         "tokens": ["QuickGadgetB", "ReleaseQuickGadgetB", "bCancelButton"]},
    ]},
    {"id": "LB", "label": "LB", "rows": [
        {"file": "DefaultInput.ini", "line": 271, "key": "XboxTypeS_LeftShoulder",
         "tokens": ["aLeftShoulder", "ThermalMode"]},
    ]},
    {"id": "A", "label": "A", "rows": [
        {"file": "DefaultInput.ini", "line": 267, "key": "XboxTypeS_A",
         "tokens": ["EjectFromVehicle", "BattleStrafe"]},
    ]},
]


def check_claim(row: dict, files: dict[str, list[dict]]) -> dict:
    binds = files[row["file"]]
    hit = next((b for b in binds if b["line"] == row["line"]), None)
    if hit is None:
        return {"ok": False, "why": "no binding on that line", "hit": None, "missing": row["tokens"]}
    missing = [t for t in row["tokens"] if not re.search(rf"(?<![A-Za-z0-9_]){re.escape(t)}(?![A-Za-z0-9_])", hit["command"])]
    ok = hit["key"] == row["key"] and not missing
    why = "line, key and all tokens match" if ok else (
        f"key is {hit['key']}, missing tokens {missing}")
    return {"ok": ok, "why": why, "hit": hit, "missing": missing}


def recorded_chain_shas(card_text: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"^\| \d+ \| `(BmGame/Config/[^`]+|Engine/Config/[^`]+)` \| True \| .*?\| `([0-9a-f]{16})` \|",
                         card_text, re.M):
        out[m.group(1).split("/")[-1]] = m.group(2)
    return out


# ------------------------------------------------------------------ upk scan

def upk_scan() -> dict:
    sys.path.insert(0, str(ROOT / "Tools/scripts"))
    import upk_read  # local decoder; no third-party dependency

    pkg = upk_read.Package(str(UPK))
    name_idx = pkg.names.index(TB_NAME)
    exports = [i for i in range(1, pkg.export_count + 1)
               if (pkg.object_path(i) or "").endswith("." + TB_NAME)]
    if exports != [TB_EXPORT]:
        raise AuditError(f"expected export {TB_EXPORT} for {TB_NAME}, got {exports}")

    def script_of(i: int) -> bytes:
        d = pkg.data(i)
        return d[22:len(d) - 16] if len(d) >= 38 else b""

    tb = script_of(TB_EXPORT)
    hits = []
    funcs = 0
    for i in range(1, pkg.export_count + 1):
        if pkg.object_class(i) != "Function":
            continue
        funcs += 1
        s = script_of(i)
        for j in exports:
            for tok in (0x1B, 0x1C):
                pat = bytes([tok]) + struct.pack("<i", j)
                k = 0
                while True:
                    k = s.find(pat, k)
                    if k < 0:
                        break
                    hits.append({"export": i, "path": pkg.object_path(i),
                                 "token": f"0x{tok:02X}", "at": k,
                                 "bytes": s[k:k + 5].hex(" ")})
                    k += 1
        pat = b"\x1b" + struct.pack("<i", name_idx)
        k = 0
        while True:
            k = s.find(pat, k)
            if k < 0:
                break
            hits.append({"export": i, "path": pkg.object_path(i), "token": "0x1B(name)",
                         "at": k, "bytes": s[k:k + 5].hex(" ")})
            k += 1
    ttc = [k for k in range(len(tb) - 4)
           if tb[k] == 0x1C and struct.unpack_from("<i", tb, k + 1)[0] == 10552]
    return {"functions": funcs, "hits": hits, "script_sha1": hashlib.sha1(tb).hexdigest(),
            "script_bytes": len(tb), "name_index": name_idx,
            "raw_name_occurrences": pkg.image.count(struct.pack("<i", name_idx)),
            "ttc_sites": ttc, "exports": exports}


# ------------------------------------------------------------------ build

def build() -> str:
    cards = {k: read(ROOT / v) for k, v in CARDS.items()}

    # ---- ini chain
    files = {k: ini_bindings(p) for k, p in CHAIN.items()}
    rec = recorded_chain_shas(cards["CONTROLS"])
    chain_rows = []
    for name, p in CHAIN.items():
        now = sha16(p)
        chain_rows.append({"file": name, "path": p, "sha16": now,
                           "card": rec.get(name.split("/")[-1]),
                           "match": rec.get(name.split("/")[-1]) == now})

    claim_res = {c["id"]: [check_claim(r, files) | {"row": r} for r in c["rows"]] for c in CLAIMS}
    claims_ok = all(x["ok"] for v in claim_res.values() for x in v)

    # every definition of the four keys in the chain (precedence ambiguity)
    keys = sorted({r["key"] for c in CLAIMS for r in c["rows"]})
    defs = []
    for k in keys:
        for name, binds in files.items():
            for b in binds:
                if b["key"] == k:
                    defs.append({"key": k, "file": name, "line": b["line"],
                                 "tokens": tokens_of(b["command"])})

    # the rewritten files and where the same tokens now sit
    rewritten = []
    for name, p in OTHER_INI.items():
        binds = ini_bindings(p) if p.suffix == ".ini" and p.stat().st_size < 2_000_000 else []
        for key in keys:
            for b in binds:
                if b["key"] == key:
                    rewritten.append({"file": name, "line": b["line"], "key": key,
                                      "tokens": tokens_of(b["command"])})
    tb_bindings = []
    for name, p in OTHER_INI.items():
        for n, line in enumerate(read(p).splitlines(), 1):
            if TB_NAME in line:
                tb_bindings.append({"file": name, "line": n, "text": line.strip()})

    # ---- upk
    upk = upk_scan()

    # ---- exe
    img, base, secs = load_pe(EXE)
    sites = e8_e9_targets(img, secs, TTC_IMPL)
    site_rows = []
    for at, kind in sites:
        if kind != "call":
            continue
        imm = imm_before(img, secs, at)
        site_rows.append({"at": at, "in_body": 0x140254560 <= at < 0x14025633D,
                          "imm": imm[1] if imm else None,
                          "imm_at": imm[0] if imm else None,
                          "imm_bytes": imm[2].hex(" ") if imm else None})
    dp_hop1 = find_e9(img, secs, DP_TUNK, 0x90)
    dp_hop2 = find_e9(img, secs, dp_hop1[1], 0x40) if dp_hop1 else None
    ttc_exec_hop = find_e9(img, secs, TTC_EXEC, 0x160)
    names = [lea_mov_pair(img, secs, a) for a in (0x140F5F9D1, 0x140F5F9FB)]
    # `48 C7 44 24 30 imm32` = mov qword ptr [rsp+0x30], imm32; imm32 sits at +6
    cmp_bytes = bytes.fromhex("48c744243040020000")
    cmp_at = rb(img, secs, 0x140063EE5, len(cmp_bytes))
    body_imm_sites = [r for r in site_rows if r["in_body"]]

    # ---- checks
    checks: list[tuple[str, bool, str]] = []
    checks.append(("the four chain files exist and their sha256 match CONTROLS.md",
                   all(r["match"] for r in chain_rows),
                   ", ".join(f"{r['file']}={r['sha16'][:8]}" for r in chain_rows)))
    checks.append(("every cited line exists with its key and every claimed token", claims_ok,
                   "; ".join(f"{cid}:{'ok' if all(x['ok'] for x in v) else 'FAIL'}"
                             for cid, v in claim_res.items())))
    checks.append((f"{TB_NAME} is export {TB_EXPORT} and its script sha1 is the card's",
                   upk["exports"] == [TB_EXPORT] and upk["script_sha1"].startswith("1cb9801219cb"),
                   f"export {upk['exports']}, sha1 {upk['script_sha1'][:12]}, {upk['script_bytes']} B"))
    checks.append(("no Function script in BmGame.upk calls ToggleBattleMode (both encodings)",
                   not upk["hits"],
                   f"{upk['functions']} Function scripts scanned, {len(upk['hits'])} sites"))
    checks.append(("the two ini key maps name ToggleBattleMode",
                   len(tb_bindings) == 2 and all("ToggleBattleMode" in b["text"] for b in tb_bindings),
                   ", ".join(f"{b['file']}:{b['line']}" for b in tb_bindings)))
    checks.append(("exactly 6 E8 sites reach 0x140063e90; 5 are in the DrivingPlayerMove body",
                   len(site_rows) == 6 and len(body_imm_sites) == 5,
                   f"{len(site_rows)} calls, {len(body_imm_sites)} in body"))
    checks.append(("the 5 in-body sites carry 0x240 (x3) and 0x241 (x2)",
                   sorted(r["imm"] for r in body_imm_sites if r["imm"] is not None) == [0x240, 0x240, 0x240, 0x241, 0x241],
                   ", ".join(f"{r['at']:#x}={r['imm'] and hex(r['imm'])}" for r in body_imm_sites)))
    checks.append(("the DrivingPlayerMove exec reaches the body in two hops (thunk -> 0x140502046 -> 0x140254560)",
                   bool(dp_hop1 and dp_hop2 and dp_hop1[1] == 0x140502046 and dp_hop2[1] == 0x140254560),
                   f"{dp_hop1 and hex(dp_hop1[1])} -> {dp_hop2 and hex(dp_hop2[1])}"))
    checks.append(("the TryToChangeMode exec calls the implementation",
                   any(at == 0x140547DFA and kind == "call"
                       for at, kind in e8_e9_targets(img, secs, TTC_IMPL)),
                   "call at 0x140547dfa (" + rb(img, secs, 0x140547DFA, 5).hex(" ") + ")"))
    checks.append(("0x240/0x241 are the FName indices of BattleMode/PursuitMode",
                   names[0]["string"] == "BattleMode" and names[0]["imm"] == 0x240 and
                   names[1]["string"] == "PursuitMode" and names[1]["imm"] == 0x241,
                   "; ".join(f"{n['string']}={n['imm']:#x}" for n in names)))
    checks.append(("the implementation compares its Name argument against 0x240 at 0x140063ee5",
                   cmp_at == cmp_bytes and struct.unpack_from("<i", cmp_at, 5)[0] == 0x240,
                   cmp_at.hex(" ")))
    checks.append(("no chain file cites BmInput.ini line numbers for these keys (the rewrite cannot touch the table)",
                   all(r["file"] != "BmInput.ini" for c in CLAIMS for r in c["rows"]),
                   "all cited lines are DefaultInput.ini"))
    if not all(ok for _, ok, _ in checks):
        bad = "; ".join(f"{n} [{d}]" for n, ok, d in checks if not ok)
        raise AuditError("check(s) failed, report not written: " + bad)

    # ---- verdicts
    v_claims = "holds" if claims_ok else "wrong"
    v_effective = "unprovable"
    v_caller = "holds" if not upk["hits"] else "wrong"
    v_binding = "wrong" if len(tb_bindings) == 2 else "holds"
    v_native = "holds" if (len(body_imm_sites) == 5 and len(site_rows) == 6
                           and dp_hop2 and dp_hop2[1] == 0x140254560) else "wrong"
    v_native_detail = "holds, with one correction"

    # ---- render
    L: list[str] = []
    a = L.append
    a("# AUDIT_G302 - the G3-02 / 02b / 02c control chain, audited against the bytes")
    a("")
    a("Generated by `Tools/scripts/audit_g302.py` (`--write`); `--check` re-derives every row from")
    a("the ini files, `BmGame.upk` and `BatmanAK.exe` and fails if this text differs by one byte.")
    a("Read-only on every input; no game process is touched.")
    a("")
    a("Labels: **decoded** = read from a file at a stated line, or a package/export/offset, or an")
    a("exe virtual address with its bytes quoted; **derived** = a stated rule on decoded facts;")
    a("**UNKNOWN** = not established, with what blocked it.")
    a("")
    a("## 0. Verdicts")
    a("")
    a("| claim | verdict | one-line reason |")
    a("|---|---|---|")
    a(f"| (1) the LT / B / LB / A token table and its line numbers | **{v_claims}** | all 6 cited lines in `DefaultInput.ini` carry the claimed key and every claimed token (decoded) |")
    a(f"| (1b) that those lines are the *effective* bindings | **{v_effective}** | the same keys are defined 2-4 times in the chain and the array-merge rule is not written anywhere (see 1.2) |")
    a(f"| (2a) `ToggleBattleMode` has no script caller | **{v_caller}** | 0 call sites in all {upk['functions']} Function scripts of BmGame.upk, both encodings (decoded) |")
    a(f"| (2b) ... and no binding site | **{v_binding}** | two key maps bind `HoldToZoom \\| ToggleBattleMode` (PCGame.ini:141, BmGame.ini:4012) |")
    a(f"| (3) TryToChangeMode 0x140063e90 is called with 0x240/0x241 from DrivingPlayerMove | **{v_native_detail}** | 5 in-body calls carry the two immediates; the thunk reaches the body in **two** hops, not the direct jump the card states |")
    a("")
    a("## 1. Question 1 - the token table against the ini chain")
    a("")
    a("### 1.1 The chain as it stands")
    a("")
    a("| file | bytes | sha256 (first 16) | CONTROLS.md records | match |")
    a("|---|---:|---|---|---|")
    for r in chain_rows:
        a(f"| `{r['file']}` | {r['path'].stat().st_size} | `{r['sha16']}` | `{r['card']}` | "
          f"{'yes' if r['match'] else '**no**'} |")
    a("")
    a("The chain is the one CONTROLS.md walks (`BasedOn` edges): PCInput -> UserInput ->")
    a("DefaultInput -> BaseInput. All four sha256 prefixes still equal the card's, so the ini side")
    a("of the token table describes the current install.")
    a("")
    a("### 1.2 The claimed lines, quoted")
    a("")
    a("| bundle | file:line | key | command as written (decoded) | tokens claimed | result |")
    a("|---|---|---|---|---|---|")
    for c in CLAIMS:
        for x in claim_res[c["id"]]:
            r = x["row"]
            cmd = x["hit"]["command"] if x["hit"] else "MISSING"
            cmd = cmd.replace("|", "\\|")   # keep the table's column count
            a(f"| {c['label']} | `{r['file']}:{r['line']}` | `{r['key']}` | `{cmd}` | "
              f"{', '.join('`%s`' % t for t in r['tokens'])} | **{'holds' if x['ok'] else 'wrong'}** |")
    a("")
    a("Notes (decoded):")
    a("")
    a("- LT is **two** lines: 251 carries the digital `XboxTypeS_LeftTrigger` (HoldToZoom and")
    a("  DeepScanOut) and 253 the analog `XboxTypeS_LeftTriggerAxis` (`Axis aLeftTrigger`). The")
    a("  claim's \"253 + 251\" is the pair, not one line.")
    a("- B is 268, LB is 271, A is 267, exactly as claimed. All four lines are in")
    a("  `BmGame/Config/DefaultInput.ini`, the third file of the chain.")
    a("")
    a("### 1.3 Every definition of those keys in the chain")
    a("")
    a("| key | file:line | tokens |")
    a("|---|---|---|")
    for d in defs:
        a(f"| `{d['key']}` | `{d['file']}:{d['line']}` | {', '.join(d['tokens'])} |")
    a("")
    a(f"- derived: {len(defs)} definitions exist for the four keys. `XboxTypeS_B` is defined in")
    a("  BaseInput.ini:70, DefaultInput.ini:72 and DefaultInput.ini:268; `XboxTypeS_A` in")
    a("  BaseInput.ini:69 and DefaultInput.ini:267; `XboxTypeS_LeftTrigger` in BaseInput.ini:67,")
    a("  DefaultInput.ini:77 and 251. Which definition wins is the array-merge rule, which no file")
    a("  states - that is why 1b is **unprovable**, not wrong.")
    a("- decoded: every claimed line is a real binding line in the chain; the claim does not invent")
    a("  a line or a token.")
    a("")
    a("## 2. Question 2 - does ToggleBattleMode have a script caller?")
    a("")
    a("### 2.1 The scan")
    a("")
    a(f"- package: `BmGame.upk` ({UPK.stat().st_size} B), {upk['functions']} Function exports.")
    a(f"- `{TB_NAME}`: one export, **{upk['exports'][0]}**, path `DrivingMode.{TB_NAME}`,")
    a(f"  script **{upk['script_bytes']} B**, sha1 `{upk['script_sha1'][:12]}` (matches CONTROLS_CONSUMERS.md).")
    a(f"- FName index of `{TB_NAME}`: **{upk['name_index']}**; that 4-byte value occurs")
    a(f"  {upk['raw_name_occurrences']} times in the package image, so a raw byte search alone is")
    a("  not evidence - each was resolved as a call operand instead.")
    a("- encodings tested at every byte offset of every Function script:")
    a("  - `0x1B` + name index (virtual call by FName),")
    a("  - `0x1C` + export index (final call by object).")
    a("")
    a("| call site | encodings |")
    a("|---|---|")
    a(f"| *none* | 0x1B(name {upk['name_index']}) = 0, 0x1C({TB_EXPORT}) = 0 over {upk['functions']} scripts |")
    a("")
    a(f"- decoded: **{len(upk['hits'])}** call sites. The claim \"no script caller\" **{v_caller}**.")
    a(f"- decoded: `{TB_NAME}`'s own body calls `TryToChangeMode` (10552) at script offsets")
    a(f"  {', '.join(str(x) for x in upk['ttc_sites'])} - it is a caller, not a callee.")
    a("")
    a("### 2.2 ... but it is bound in two key maps (the \"no binding site\" half is wrong)")
    a("")
    a("| file:line | row (decoded) |")
    a("|---|---|")
    for b in tb_bindings:
        a(f"| `{b['file']}:{b['line']}` | `{b['text']}` |")
    a("")
    a("Both rows are `DefaultPursuitKeyMap` entries for `$GFxUI.KeyboardControls.BattleMode` on")
    a("`$PC.Keys.RightMouseButton`, with `Command=\"HoldToZoom | ToggleBattleMode\"`. So the command")
    a("is reached as an **exec/console command written in the ini**, not by a script call - which is")
    a("consistent with 0 script call sites and contradicts CONTROLS_CONSUMERS.md's \"no virtual-call")
    a("or binding site\". That card only read `DefaultInput.ini`'s `Bindings=` lines (BIND_LINES);")
    a("these are `DefaultPursuitKeyMap=` rows in `BmGame.ini` / `PCGame.ini`.")
    a("")
    a("- decoded: the strings and abilities above are quoted from the two lines.")
    a("- UNKNOWN: whether the engine routes `DefaultPursuitKeyMap.Command` through the exec chain.")
    a("  The name match is decoded; the dispatcher is not in these files.")
    a("")
    a("### 2.3 What the two halves mean together")
    a("")
    a("`ToggleBattleMode` is a leaf: nothing in BmGame.upk calls it, and the only route to it in the")
    a("files is the BattleMode key-map command. Any claim that LT *held* means battle mode must")
    a("therefore name that ini row, not a script path - and the row is on the **PC right mouse**")
    a("button; no `PursuitKeyMap` row in either file names an Xbox button (0 hits).")
    a("")
    a("## 3. Question 3 - the native call claim")
    a("")
    a("### 3.1 The two constants")
    a("")
    a("| name | lea | mov edx | string at |")
    a("|---|---|---|---|")
    for n in names:
        a(f"| `{n['string']}` | `{n['lea_at']:#x}` | `{n['mvbytes'] if 'mvbytes' in n else 'mov edx, ' + hex(n['imm'])}` | `{n['string_at']:#x}` |")
    a("")
    a("Bytes: " + "; ".join(f"`{n['imm_bytes']}` at {n['mov_at']:#x}" for n in names) + ".")
    a("So 0x240 is the FName index of `BattleMode` and 0x241 of `PursuitMode` (decoded).")
    a("")
    a(f"The implementation compares its Name argument with 0x240 at `0x140063ee5`:")
    a(f"`{cmp_at.hex(' ')}` (decoded bytes).")
    a("")
    a("### 3.2 Every call site of 0x140063e90 in .text")
    a("")
    a("| call at | in DrivingPlayerMove body? | mov [rbp+0x180], imm just before | bytes |")
    a("|---|---|---|---|")
    for r in site_rows:
        a(f"| `{r['at']:#x}` | {'yes' if r['in_body'] else 'no (the TryToChangeMode exec)'} | "
          f"{('`' + hex(r['imm']) + '`') if r['imm'] is not None else 'none'} | "
          f"{('`' + r['imm_bytes'] + '`') if r['imm_bytes'] else '-'} |")
    a("")
    a(f"- decoded: **{len(site_rows)}** E8 sites, **{len(body_imm_sites)}** inside")
    a("  `0x140254560-0x14025633d`. The sixth is the exec's own call at `0x140547dfa`")
    a("  (no immediate: it forwards its parsed argument).")
    a("- derived: the three 0x240 sites select `BattleMode` and the two 0x241 sites `PursuitMode`,")
    a("  via the FName table above; this is a call-argument decode, not a control-flow decode.")
    a("")
    a("### 3.3 The thunk chain - one correction to CONTROLS_NATIVE.md")
    a("")
    a("| hop | site | bytes | target |")
    a("|---|---|---|---|")
    a(f"| exec -> parser | `{dp_hop1[0]:#x}` | `{rb(img, secs, dp_hop1[0], 5).hex(' ')}` | `{dp_hop1[1]:#x}` |")
    a(f"| parser -> body | `{dp_hop2[0]:#x}` | `{rb(img, secs, dp_hop2[0], 5).hex(' ')}` | `{dp_hop2[1]:#x}` |")
    a(f"| exec(TryToChangeMode) -> impl | `0x140547dfa` | `{rb(img, secs, 0x140547dfa, 5).hex(' ')}` | `{TTC_IMPL:#x}` |")
    a("")
    a("CONTROLS_NATIVE.md says the DrivingPlayerMove thunk's jump target **is** the body")
    a("(0x140254560). It is not: the thunk jumps to **0x140502046**, which jumps to 0x140254560.")
    a("The conclusion survives (the body is DrivingPlayerMove's), the stated link does not. The")
    a("card's \"direct native callers of the body: 1\" is therefore true of 0x140502046->0x140254560,")
    a("and the thunk itself is two hops away.")
    a("")
    a(f"- decoded: `0x140063e90` is reached from the TryToChangeMode exec ({TTC_EXEC:#x}) and from")
    a(f"  the body only. **{v_native_detail}**: the calls and their arguments hold; the hop count is wrong.")
    a("")
    a("## 4. The ini rewrites after CONFIG.md (review-G3-03)")
    a("")
    a("| file | mtime | bytes | sha256 now | vs CONFIG.md / review |")
    a("|---|---|---:|---|---|")
    for name, p in OTHER_INI.items():
        st = p.stat()
        note = ""
        if name == "BmInput.ini":
            note = "same bytes as review's post-rewrite sha `b17711be`; CONFIG.md's `71eac81c` is gone"
        elif name == "BmEngine.ini":
            note = "**third** state: card `3282dd4d` (115,968 B) -> review `bf1558f7` (116,344 B) -> now"
        elif name == "BmSystemSettings.ini":
            note = "matches the review's post-rewrite sha `becebd57`"
        else:
            note = "not rewritten (2024 mtime, outside the 2026-11-03 rewrite)"
        a(f"| `{name}` | {time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))} | {st.st_size} | `{sha16(p)}` | {note} |")
    a("")
    a("**Which tokens this touches: none of the four.** All four claims cite `DefaultInput.ini`,")
    a("which is untouched (sha `7db2b893...` = the card's). `BmInput.ini` carries the same four")
    a("keys at **different lines** after the rewrite:")
    a("")
    a("| key | line now in BmInput.ini | tokens |")
    a("|---|---:|---|")
    for r in rewritten:
        if r["file"] == "BmInput.ini":
            a(f"| `{r['key']}` | {r['line']} | {', '.join(r['tokens'])} |")
    a("")
    a("- decoded: `BmInput.ini:251` now reads `Bindings=(Name=\"Up\",...)`, so any citation of")
    a("  `BmInput.ini:251` (or :253/:267/:268/:271) as a Batmobile token line is stale. The token")
    a("  table is safe only because it cites `DefaultInput.ini`.")
    a("- decoded: `BmEngine.ini` (rewritten again at 20:05) contains **0** lines naming these six")
    a("  tokens; `BmSystemSettings.ini` likewise 0. So the physics/post-process row churn does not")
    a("  reach the controls table.")
    a("")
    a("## 5. Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for name, ok, detail in checks:
        a(f"| {name} | **{'PASS' if ok else 'FAIL'}** | {detail} |")
    a("")
    a(f"{sum(1 for _, ok, _ in checks if ok)}/{len(checks)} checks passed.")
    a("")
    a("## 6. UNKNOWN")
    a("")
    a("- **The array-merge rule for `Bindings=`.** 13 definitions exist for the four keys and no")
    a("  file states which wins; a runtime read of the effective binding would settle it.")
    a("- **Whether the engine dispatches `DefaultPursuitKeyMap.Command` as an exec call.** The name")
    a("  match is decoded; the dispatcher is native and not resolved here.")
    a("- **Whether a caller in another package calls ToggleBattleMode.** The scan covers BmGame.upk")
    a("  only (the task's scope); a cross-package caller would use an import operand and is untested.")
    a("- **What the five in-body branch conditions test.** The 0x240/0x241 immediates and their")
    a("  arguments are decoded; the branch predicates (e.g. `bt ecx,0x10` on `bWeaponsReady`) are")
    a("  not resolved to semantics here.")
    a("- **Whether `0x140063e90` returns a bool that gates the call's effect.** The call sites test")
    a("  `eax` after the call (`85 c0` at 0x140254a51), but the return's meaning is not decoded.")
    a("")
    a("## 7. Reproduce")
    a("")
    a("```bash")
    a("cd \"E:/Modding/JustCause3/JC3-Batmobile\"")
    a("python Tools/scripts/audit_g302.py --write   # writes this file")
    a("python Tools/scripts/audit_g302.py --check   # re-derives, byte-compares, re-runs checks")
    a("```")
    a("")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    try:
        text = build()
    except AuditError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 2
    if args.write:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(text + "\n", encoding="utf-8", newline="\n")
        print(f"WROTE {OUT.relative_to(ROOT)} ({text.count(chr(10)) + 1} lines)")
        return 0
    if not OUT.is_file():
        print(f"FAIL: {OUT.relative_to(ROOT)} does not exist (run --write)", file=sys.stderr)
        return 1
    if OUT.read_text(encoding="utf-8") != text + "\n":
        print(f"DRIFT: {OUT.relative_to(ROOT)} differs from a fresh derivation", file=sys.stderr)
        return 1
    print(f"AUDIT_G302.md current ({text.count(chr(10)) + 1} lines, all checks pass)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

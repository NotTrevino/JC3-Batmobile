"""bmak_tool_claims_check.py - recompute the local numbers quoted by the BmAK UE3 tool report.

The report `tmp/freebuff/reports/bmak-ue3-runtime-tools-check.md` is a web survey, but every
*local* number in it (the GOG exe's PE identity, the three validated globals, the 22 UNKNOWN
symbols, the five startup prologue patterns) is a quote from an earlier report in this repo.
This tool re-reads those three reports and re-extracts those numbers, so a misquote fails the
check instead of shipping. It never opens the game folder and never touches a process: every
input is a text file another task already wrote.

Sources (read-only):
  tmp/freebuff/reports/bmsdk-gog-address-hunt.md   - PE identity, .pdata count, scan patterns
  tmp/freebuff/reports/bmsdk-gog-copy-port.md      - the 25-symbol table, the 22 UNKNOWN list
  tmp/freebuff/reports/bmsdk-port-to-repack-exe.md - the repack (dead end) baseline

Usage:
    python Tools/scripts/bmak_tool_claims_check.py --write   # regenerate the JSON
    python Tools/scripts/bmak_tool_claims_check.py --check   # fail if stale or misquoted
"""
import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))

HUNT = os.path.join(ROOT, "tmp", "freebuff", "reports", "bmsdk-gog-address-hunt.md")
PORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "bmsdk-gog-copy-port.md")
REPACK = os.path.join(ROOT, "tmp", "freebuff", "reports", "bmsdk-port-to-repack-exe.md")
REPORT = os.path.join(ROOT, "tmp", "freebuff", "reports", "bmak-ue3-runtime-tools-check.md")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "BMAK_TOOL_CLAIMS.json")

SECTIONS = [
    "## 1. Tools table",
    "## 2. Arkham Knight-specific evidence",
    "## 3. Signatures we could reuse",
    "## 4. Recommended route to the 22 addresses",
    "## 5. UNKNOWNs",
]


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def one(pat, text, name, flags=0):
    m = re.search(pat, text, flags)
    if not m:
        raise SystemExit("FACT NOT FOUND (%s): pattern %r" % (name, pat))
    return m.group(1) if m.groups() else m.group(0)


def extract():
    hunt, port, repack = read(HUNT), read(PORT), read(REPACK)
    facts = {}

    # --- GOG exe identity: address-hunt section 1 -----------------------------
    facts["gog_exe_size_bytes"] = int(one(r"Measured this session: ([\d,]+) bytes", hunt,
                                          "size").replace(",", ""))
    facts["gog_pe_timestamp"] = one(r"Measured this session: [\d,]+ bytes, PE timestamp"
                                    r" `(0x[0-9a-f]+)`", hunt, "pe")
    facts["gog_image_base"] = one(r"image base\s*\n?`(0x14[0-9a-fA-F]+)`", hunt, "base", re.S)
    facts["gog_size_of_image"] = one(r"`SizeOfImage` `(0x[0-9a-f]+)`", hunt, "soi")
    facts["gog_text_rva"] = one(r"`\.text`\s*\|\s*(0x[0-9a-f]+)", hunt, "text rva")

    # --- .pdata / function population ----------------------------------------
    facts["pdata_function_count"] = int(one(r"\*\*([\d,]+)\*\* entries", hunt,
                                            "pdata").replace(",", ""))

    # --- the data-segment drift rule -----------------------------------------
    facts["data_delta"] = one(r"\*\*BmSDK value \+ (0x[0-9A-Fa-f]+)\*\*", hunt, "delta")

    # --- the 25-symbol table in the copy-port report --------------------------
    rows = {}
    for sym in ("GNames", "GObjObjects", "EngineTick"):
        pat = r"\|\s*`%s`\s*\|\s*(0x[0-9A-Fa-f]+)\s*\|\s*\*\*(0x[0-9A-Fa-f]+)\*\*\s*\|\s*(0x[0-9A-Fa-f]+)" % sym
        m = re.search(pat, port)
        if not m:
            raise SystemExit("FACT NOT FOUND (%s row)" % sym)
        rows[sym] = {"steam": m.group(1), "gog": m.group(2), "file_offset": m.group(3)}
    facts["patched"] = rows

    # --- the deliberately-unpatched symbols ----------------------------------
    # The prose says "the other 22 addresses" but the enumeration that follows names 23
    # symbols (3 patched + 23 = 26, so one of the two figures is off by one). Both numbers
    # are kept so the report has to state the discrepancy instead of silently picking one.
    m = re.search(r"\*\*Deliberately not patched:\*\* the other (\d+) addresses \((.*?)\)\.",
                  port, re.S)
    if not m:
        raise SystemExit("FACT NOT FOUND (unpatched list)")
    body = m.group(2)
    syms = re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)`", body)
    facts["unknown_symbol_count_prose"] = int(m.group(1))
    facts["unknown_symbols"] = syms
    facts["unknown_symbol_count_listed"] = len(syms)
    if facts["unknown_symbol_count_prose"] == len(syms):
        raise SystemExit("source report now self-consistent (%d); drop the discrepancy note"
                         % len(syms))

    # --- the five startup prologue patterns (address-hunt section 6) ----------
    pats = {}
    for name, body in re.findall(r"^(PreInit|Init|Tick|Exit|WinMain)\s*:\s*([0-9a-f ]+)$",
                                 hunt, re.M):
        pats[name] = body.strip()
    if len(pats) != 5:
        raise SystemExit("FACT MISMATCH: expected 5 prologue patterns, found %d" % len(pats))
    facts["startup_patterns"] = pats

    # --- the repack baseline (the dead end this report must not re-open) ------
    facts["repack_sha256"] = one(r"sha256 `([0-9a-f]{64})`", repack, "repack sha")
    facts["repack_size_bytes"] = int(one(r"([\d,]+) bytes\. Measured", repack,
                                         "repack size").replace(",", ""))
    return facts


def write(facts):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(facts, f, indent=1, sort_keys=True)
        f.write("\n")
    print("wrote", os.path.relpath(OUT, ROOT))


def check(facts):
    ok = True
    if not os.path.exists(OUT):
        print("FAIL: %s missing (run --write)" % os.path.relpath(OUT, ROOT))
        return False
    stored = json.loads(read(OUT))
    for k in sorted(set(facts) | set(stored)):
        if facts.get(k) != stored.get(k):
            print("FAIL: stale JSON field %r" % k)
            ok = False
    if not os.path.exists(REPORT):
        print("FAIL: report missing")
        return False
    rep = read(REPORT)
    for sec in SECTIONS:
        if sec not in rep:
            print("FAIL: report missing section %r" % sec)
            ok = False

    # every local number the report quotes must appear verbatim, in lower or upper case hex
    quoted = {
        "gog_exe_size_bytes": "{:,}".format(facts["gog_exe_size_bytes"]),
        "gog_pe_timestamp": facts["gog_pe_timestamp"],
        "gog_image_base": facts["gog_image_base"],
        "gog_size_of_image": facts["gog_size_of_image"],
        "pdata_function_count": "{:,}".format(facts["pdata_function_count"]),
        "data_delta": facts["data_delta"],
        "repack_sha256": facts["repack_sha256"],
        "repack_size_bytes": "{:,}".format(facts["repack_size_bytes"]),
    }
    for sym, row in facts["patched"].items():
        quoted["patched.%s.steam" % sym] = row["steam"].upper().replace("0X", "0x")
        quoted["patched.%s.gog" % sym] = row["gog"].upper().replace("0X", "0x")
    for sym in facts["unknown_symbols"]:
        quoted["unknown.%s" % sym] = "`%s`" % sym
    for name, body in facts["startup_patterns"].items():
        quoted["pattern.%s" % name] = body

    for label, needle in sorted(quoted.items()):
        hay = rep if needle.startswith("`") or len(needle) < 40 else rep
        if needle.lower() not in hay.lower():
            print("FAIL: report does not quote %s (%r)" % (label, needle))
            ok = False

    # the count itself must be stated, and the prose/list mismatch must be disclosed
    if not re.search(r"22 of (?:the )?25|22 `/|of 25|the 22", rep):
        print("FAIL: report does not state the 22-of-25 ratio")
        ok = False
    for word in ("count discrepancy", str(facts["unknown_symbol_count_listed"])):
        if word not in rep:
            print("FAIL: report does not disclose %r" % word)
            ok = False
    print("PASS: %d facts, %d quoted values, %d sections"
          % (len(facts), len(quoted), len(SECTIONS)) if ok else "CHECK FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    a = ap.parse_args()
    facts = extract()
    if a.write:
        write(facts)
        return 0
    return 0 if check(facts) else 1


if __name__ == "__main__":
    sys.exit(main())

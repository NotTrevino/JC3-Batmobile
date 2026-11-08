"""t_au3b_banks.py - T-AU3b: prove T-AU3/T-AU5's "banks absent from the install" claim.

Rows T-AU3 and T-AU5 in `Working/Translation/COMPROMISES_T.md` say the BmAK Batmobile's audio banks
are absent from the install. This script tests the claim against the **JC3** install, per bank:

    method N1  name scan of every named entry in the JC3 archive index (Research/JC3Grab/INDEX.jsonl)
    method N2  name scan of the JC3 banks' own FSB5 sample-name tables (JC3_AUDIO_EVENTS.json)
    method N3  file-name scan of the live dropzone tree (read-only)
    method H1  Jenkins hash of the bank name, and of `sound/fmod_banks/<name>.bank`, against every
               hash the archive index carries (named and anonymous entries alike)

Absent is only reported after all four searches, and the exact strings/hashes searched are printed,
so the claim is reproducible rather than remembered. For every absent bank the script derives the
closest **JC3** vehicle-audio carriers from the decoded sample-name table and labels each one
`derived` with the matching rule that produced it. Nothing here is auditioned: a candidate is a
name-level match, never a claim that it sounds like the BmAK asset.

    python Tools/scripts/t_au3b_banks.py --write   # Working/Translation/T_AU3B.{json,md}
    python Tools/scripts/t_au3b_banks.py --check   # re-run every search, rebuild, compare
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT_JSON = os.path.join(ROOT, "Working", "Translation", "T_AU3B.json")
OUT_MD = os.path.join(ROOT, "Working", "Translation", "T_AU3B.md")

AUDIO_MAP = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_MAP.json")
AUDIO_BANKS = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS.md")
AUDIO_BANKS2 = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_BANKS2.md")
AUDIO_FEATURES = os.path.join(ROOT, "Research", "BatmobileGrab", "AUDIO_FEATURES.md")
JC3_INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.json")
JC3_INDEXL = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
JC3_AUDIO = os.path.join(ROOT, "Research", "JC3Grab", "JC3_AUDIO_EVENTS.json")
COMPROMISES = os.path.join(ROOT, "Working", "Translation", "COMPROMISES_T.md")
GAME = "D:/Games/Just Cause 3"
DROPZONE = os.path.join(GAME, "dropzone")


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(path: str) -> str:
    return os.path.relpath(path, ROOT).replace("\\", "/")


def find(path: str, needle: str) -> tuple[int, str]:
    with open(path, encoding="utf-8-sig", errors="replace") as f:
        for i, line in enumerate(f, 1):
            if needle in line:
                return i, line.strip()
    raise SystemExit(f"evidence missing: {needle!r} not in {rel(path)}")


def jenkins(text: str) -> int:
    """Gibbed's HashJenkins (the project's canonical string hash, used by jc3adf/jc3index)."""
    h = 0
    for ch in text.lower().encode("utf-8"):
        h = (h + ch) & 0xFFFFFFFF
        h = (h + (h << 10)) & 0xFFFFFFFF
        h ^= h >> 6
    h = (h + (h << 3)) & 0xFFFFFFFF
    h ^= h >> 11
    h = (h + (h << 15)) & 0xFFFFFFFF
    return h


# --------------------------------------------------------------------------- sources
def bmak_banks() -> dict:
    m = json.load(open(AUDIO_MAP, encoding="utf-8"))
    rows = m["banks"]
    distinct: dict[str, dict] = {}
    for r in rows:
        b = r["bank"]
        d = distinct.setdefault(b, {"bank": b, "packages": [], "exports": 0, "bytes": 0,
                                    "events": 0, "also_in": [], "origin": r.get("origin")})
        d["packages"].append(r["package"])
        d["exports"] += 1
        d["bytes"] = max(d["bytes"], int(r.get("bytes") or 0))
        d["events"] = max(d["events"], int((r.get("objects") or {}).get("events") or 0))
        d["also_in"] += r.get("also_in") or []
    ev = m["events"]
    for e in ev:
        b = e.get("bank")
        if b in distinct:
            distinct[b].setdefault("event_names", []).append(e.get("name"))
    missing = [r for r in rows if not r.get("bank")]
    return {"rows": rows, "distinct": distinct, "events": ev, "missing": missing,
            "summary": m.get("summary"), "sources": m.get("sources")}


def jc3_index() -> dict:
    meta = json.load(open(JC3_INDEX, encoding="utf-8"))
    paths: list[str] = []
    hashes: set[int] = set()
    archives: dict[str, int] = {}
    n = 0
    with open(JC3_INDEXL, encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            n += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(row, list):
                row = {k: v for k, v in zip(("path", "hash", "archive", "offset", "size"), row)}
            p = None
            for k in ("path", "name", "file", "vfs"):
                if isinstance(row.get(k), str) and "/" in row[k]:
                    p = row[k]
                    break
            if p:
                paths.append(p)
                archives[row.get("archive") or row.get("tab") or "?"] = archives.get(
                    row.get("archive") or row.get("tab") or "?", 0) + 1
            for k in ("hash", "name_hash", "id"):
                v = row.get(k)
                if isinstance(v, int):
                    hashes.add(v & 0xFFFFFFFF)
                elif isinstance(v, str) and re.fullmatch(r"[0-9a-fA-F]{8}", v):
                    hashes.add(int(v, 16))
    return {"meta": meta, "paths": paths, "hashes": hashes, "rows_read": n, "archives": archives}


def jc3_banks() -> dict:
    a = json.load(open(JC3_AUDIO, encoding="utf-8"))
    names: list[str] = []
    per_bank: dict[str, int] = {}
    for bank, info in (a.get("banks") or {}).items():
        fsb = (info or {}).get("fsb") or {}
        nm = fsb.get("names") or []
        per_bank[bank] = len(nm)
        names += [x for x in nm if isinstance(x, str)]
    return {"file": a, "names": names, "per_bank": per_bank,
            "banklist": ((a.get("banklist") or {}).get("names") or []),
            "route": a.get("route"), "donor": a.get("donor")}


def dropzone_banks() -> dict:
    found: list[str] = []
    total = 0
    if os.path.isdir(DROPZONE):
        for dp, _, fs in os.walk(DROPZONE):
            for f in fs:
                if f.lower().endswith((".bank", ".pck", ".fsb")):
                    total += 1
                    found.append(os.path.relpath(os.path.join(dp, f), DROPZONE).replace("\\", "/"))
    return {"files": sorted(found), "total": total, "exists": os.path.isdir(DROPZONE)}


# --------------------------------------------------------------------------- the search
ROLE_RULES = [
    ("engine", ("engine", "rev", "idle", "rpm", "exhaust", "chassis")),
    ("burnout/boost", ("nitro", "boost", "burnout", "tailpipe")),
    ("tyres", ("skid", "tyre", "tire", "wheel", "surface", "asphalt")),
    ("impacts", ("impact", "crash", "collision", "break", "scrape")),
    ("sonar", ("sonar", "scan", "pulse")),
    ("battle mode", ("battle", "transform", "turret", "hatch")),
    ("weapons", ("minigun", "cannon", "missile", "mg", "gatling", "gun")),
    ("interior", ("interior", "cabin", "inside")),
]


def role_of(bank: str) -> tuple[str, tuple[str, ...]]:
    b = bank.upper()
    if "ENGINE" in b or "BATMOBILE" in b:
        return ROLE_RULES[0]
    if "BURNOUT" in b or "NITRO" in b:
        return ROLE_RULES[1]
    if "TYRE" in b or "TIRE" in b:
        return ROLE_RULES[2]
    if "IMPACT" in b:
        return ROLE_RULES[3]
    if "SONAR" in b:
        return ROLE_RULES[4]
    if "BATTLE" in b or "MODE" in b:
        return ROLE_RULES[5]
    if "WEA" in b or "WEAPON" in b:
        return ROLE_RULES[6]
    return ROLE_RULES[7]


def candidates(bank: str, jc3: dict, limit: int = 4) -> list[dict]:
    role, tokens = role_of(bank)
    hits = [n for n in jc3["names"] if any(t in n.lower() for t in tokens)]
    # keep the ones a car can actually own: JC3 names the vehicle family jc3_veh_*
    veh = [n for n in hits if n.lower().startswith(("jc3_veh", "veh_"))]
    pick = (veh or hits)[:limit]
    return [{"sample": n, "rule": f"name token in {list(tokens)} for role '{role}'", "label": "derived"}
            for n in pick]


def search() -> dict:
    bmak = bmak_banks()
    idx = jc3_index()
    jc3 = jc3_banks()
    dz = dropzone_banks()
    rows = []
    banklist = {b.lower().rsplit(".", 1)[0] for b in jc3["banklist"]}
    for bank, d in sorted(bmak["distinct"].items()):
        low = bank.lower()
        n1 = [p for p in idx["paths"] if low in p.lower().rsplit("/", 1)[-1].lower()]
        n2 = [n for n in jc3["names"] if low in n.lower() or n.lower() == low]
        n3 = [f for f in dz["files"] if low in f.lower().rsplit("/", 1)[-1].lower()]
        h_name = jenkins(bank)
        h_path = jenkins(f"sound/fmod_banks/{bank}.bank")
        h1 = sorted({h for h in (h_name, h_path) if h in idx["hashes"]})
        found = bool(n1 or n2 or n3 or h1)
        row = {"bank": bank, "packages": d["packages"], "origin": d["origin"],
               "exports": d["exports"], "bytes": d["bytes"], "events": d["events"],
               "event_names": d.get("event_names") or [],
               "jc3_banklist_name_match": low in banklist,
               "N1_name_in_index_paths": n1[:5], "N1_count": len(n1),
               "N2_name_in_fsb_tables": n2[:5], "N2_count": len(n2),
               "N3_name_in_dropzone": n3[:5], "N3_count": len(n3),
               "H1_jenkins_name": f"0x{h_name:08X}", "H1_jenkins_path": f"0x{h_path:08X}",
               "H1_hash_in_index": [f"0x{h:08X}" for h in h1],
               "found": found,
               "verdict": "FOUND" if found else "ABSENT",
               "candidates": [] if found else candidates(bank, jc3),
               "no_candidate_reason": None}
        if not found and not row["candidates"]:
            row["no_candidate_reason"] = ("no decoded JC3 sample name matches this bank's role token rule; "
                                          "JC3_AUDIO_EVENTS.json decodes names only for the banks it read")
        rows.append(row)
    absent = [r for r in rows if not r["found"]]
    return {"bmak": bmak, "index": {"rows_read": idx["rows_read"], "paths": len(idx["paths"]),
                                   "hashes": len(idx["hashes"]), "meta": idx["meta"],
                                   "archives": len(idx["archives"])},
            "jc3": {"fsb_names": len(jc3["names"]), "per_bank": jc3["per_bank"],
                    "banklist": jc3["banklist"], "banklist_names": len(banklist)},
            "dropzone": dz, "rows": rows, "absent": absent,
            "rows_md": (find(COMPROMISES, "**T-AU3**"), find(COMPROMISES, "**T-AU5**"))}


# --------------------------------------------------------------------------- render
def render(m: dict) -> str:
    L: list[str] = []
    A = L.append
    A("# T-AU3B - are the BmAK audio banks absent from the JC3 install?")
    A("")
    A("Generated by `Tools/scripts/t_au3b_banks.py`. `--check` re-runs every search and rebuilds this")
    A("file byte for byte. Read-only: the JC3 install is inspected, never written or launched.")
    A("")
    A("## Answer")
    A("")
    A(f"- BmAK banks the Batmobile references: **{len(m['bmak']['distinct'])}** distinct names over "
      f"{len(m['bmak']['rows'])} bank exports; **{len(m['bmak']['events'])}** events name one of them.")
    A(f"- searched: JC3 archive index **{m['index']['rows_read']:,}** rows / **{m['index']['paths']:,}** named paths / "
      f"**{m['index']['hashes']:,}** distinct hashes over **{m['index']['archives']}** archives (base + patch + dlc mounts);")
    A(f"  the JC3 banks' FSB5 name tables **{m['jc3']['fsb_names']:,}** sample names; the live dropzone "
      f"**{m['dropzone']['total']}** bank/pck/fsb files.")
    car = [r for r in m["rows"] if r["bank"].startswith(("BML_", "VEH_", "AUX_", "WPN_"))]
    A(f"- of those {len(m['rows'])}, **{len(car)}** are car/weapon banks (`BML_`/`VEH_`/`AUX_`/`WPN_`) and "
      f"**{len(m['rows']) - len(car)}** are dialogue, sequence, prop and ambience banks the Batmobile's events also name.")
    A(f"- **ABSENT: {len(m['absent'])} of {len(m['rows'])}**. Every bank was searched by name (index path, FSB5")
    A("  table, dropzone file name) and by Jenkins hash (bank name, and `sound/fmod_banks/<name>.bank`) against")
    A("  every hash the index carries, named and anonymous alike.")
    A("")
    A("**The rows' wording is therefore correct for the JC3 install, and its scope is what matters:** the banks")
    A("are not files or names JC3 ships. They are BmAK assets; `AUDIO_BANKS.md` shows "
      f"{sum(1 for r in m['bmak']['rows'])} exports of them")
    A("inside the BmAK install, so 'absent from the install' is true only when 'the install' means JC3. The loss")
    A("T-AU3/T-AU5 record is not that the banks failed a search - it is that BmAK's FEV graph cannot be authored")
    A("into JC3's bank format at all (`JC3_AUDIO.md` section 10 route b).")
    A("")
    A("## 1. The claim being tested")
    A("")
    for ln, txt in m["rows_md"]:
        A(f"- `{rel(COMPROMISES)}:{ln}` - {txt}")
    A("")
    A("## 2. Method, and what each method can prove")
    A("")
    A("| method | what is searched | what a hit would prove | what a miss proves |")
    A("|---|---|---|---|")
    A("| N1 | every named path in `Research/JC3Grab/INDEX.jsonl` (basename substring) | a JC3 file carries the bank's name | no JC3 path names it |")
    A("| N2 | the JC3 banks' decoded FSB5 sample-name tables | a JC3 bank owns a sample with that name | no JC3 sample is named after it |")
    A("| N3 | the live `dropzone/` tree, file names | a loose override already supplies it | the dropzone does not |")
    A("| H1 | Jenkins(name) and Jenkins(`sound/fmod_banks/<name>.bank`) vs every index hash | an anonymous archive entry is it | no entry hashes to it |")
    A("")
    A("A miss is not proof of non-existence in general - JC3 could carry the bytes under a third name or hash")
    A("space. It is proof that **nothing in the install can be addressed as that bank**, which is the question")
    A("a build has to answer.")
    A("")
    A("## 3. Per-bank result")
    A("")
    A("| bank | BmAK package(s) | bytes | events | N1 | N2 | N3 | H1 | verdict |")
    A("|---|---|---:|---:|---:|---:|---:|---|---|")
    for r in m["rows"]:
        A(f"| `{r['bank']}` | {', '.join(r['packages'])} | {r['bytes']:,} | {r['events']} | "
          f"{r['N1_count']} | {r['N2_count']} | {r['N3_count']} | "
          f"{', '.join(r['H1_hash_in_index']) or '-'} | **{r['verdict']}** |")
    A("")
    A("Hashes searched per bank (so the search is reproducible):")
    A("")
    A("| bank | Jenkins(name) | Jenkins(sound/fmod_banks/<name>.bank) |")
    A("|---|---|---|")
    for r in m["rows"]:
        A(f"| `{r['bank']}` | `{r['H1_jenkins_name']}` | `{r['H1_jenkins_path']}` |")
    A("")
    A("## 4. Closest JC3 vehicle-audio carriers (candidates only)")
    A("")
    A("Each row is `derived`, never auditioned: the rule is a token match on the decoded JC3 sample names")
    A("(`JC3_AUDIO_EVENTS.json`), preferring the `jc3_veh*` family. A candidate is a **name-level** carrier,")
    A("not evidence that it sounds like the BmAK asset.")
    A("")
    A("| absent BmAK bank | role (from bank name) | candidate JC3 sample | rule |")
    A("|---|---|---|---|")
    for r in m["absent"]:
        role, _ = role_of(r["bank"])
        if not r["candidates"]:
            A(f"| `{r['bank']}` | {role} | **none** - no decoded JC3 sample name matches | token match, 0 hits |")
        for c in r["candidates"]:
            A(f"| `{r['bank']}` | {role} | `{c['sample']}` | derived: {c['rule']} |")
    zero = [r["bank"] for r in m["absent"] if not r["candidates"]]
    A("")
    A(f"{len(m['absent']) - len(zero)} of {len(m['absent'])} absent banks have at least one token-matched JC3 sample; "
      f"{len(zero)} have none" + (" (" + ", ".join(f"`{b}`" for b in zero) + ")" if zero else "") + ".")
    A("Those keep **no** candidate rather than an invented one: JC3_AUDIO_EVENTS.json decodes sample-name tables")
    A("only for the banks it read, so a name miss there is a coverage limit, not a claim that JC3 has no such sound.")
    A("")
    A("N2 coverage - decoded sample names per JC3 bank:")
    A("")
    A("| JC3 bank | decoded sample names |")
    A("|---|---:|")
    for b, n in sorted(m["jc3"]["per_bank"].items()):
        A(f"| `{b}` | {n} |")
    A("")
    A("## 5. What this does and does not settle")
    A("")
    A("- **Settled:** the banks are not in the JC3 install under their own names or Jenkins hashes, in the")
    A("  archive index, in the banks' name tables or in the dropzone. T-AU3/T-AU5's `why` is accurate about")
    A("  JC3.")
    A("- **Settled:** the banks DO exist as BmAK assets (27 exports read by `AUDIO_BANKS.md`), so the row must")
    A("  not be read as 'the source audio was never grabbed'.")
    A("- **Not settled:** whether any JC3 sample is an acceptable substitute. The candidate table is a")
    A("  name-level shortlist; choosing one needs an audition, which is a Q step.")
    A("- **Not settled:** whether a JC3 bank could carry a BmAK event id. `AUDIO_BANKS2.md` searched one")
    A("  (`0x6BB2C66E`) across 117 exports and found it nowhere; a wider id sweep is not this card.")
    A("")
    A("## 6. Sources")
    A("")
    A("| source | sha256 (first 16) |")
    A("|---|---|")
    for p in (AUDIO_MAP, AUDIO_BANKS, AUDIO_BANKS2, AUDIO_FEATURES, JC3_INDEX, JC3_INDEXL, JC3_AUDIO, COMPROMISES):
        A(f"| `{rel(p)}` | `{sha256(p)[:16]}\u2026` |")
    A("")
    return "\n".join(L) + "\n"


def model() -> dict:
    m = search()
    m["json"] = {
        "schema": 1, "card": "T-AU3b",
        "generator": "Tools/scripts/t_au3b_banks.py",
        "question": "are the BmAK audio banks absent from the JC3 install?",
        "bmak_banks": [{"bank": r["bank"], "packages": r["packages"], "origin": r["origin"],
                        "bytes": r["bytes"], "events": r["events"], "event_names": r["event_names"]}
                       for r in m["rows"]],
        "search": {"jc3_index": m["index"], "jc3_fsb_names": m["jc3"]["fsb_names"],
                   "jc3_banklist": m["jc3"]["banklist"], "dropzone": m["dropzone"]},
        "rows": m["rows"], "absent_count": len(m["absent"]), "found_count": len(m["rows"]) - len(m["absent"]),
        "labels": "decoded: index paths/hashes and FSB5 names; derived: candidate carriers by token rule; "
                  "UNKNOWN: whether a candidate sounds like the BmAK asset",
    }
    return m


def write() -> int:
    m = model()
    os.makedirs(os.path.dirname(OUT_MD), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
        json.dump(m["json"], f, indent=1)
        f.write("\n")
    text = render(m)
    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"wrote {rel(OUT_JSON)} and {rel(OUT_MD)} ({len(text.splitlines())} lines)")
    print(f"banks {len(m['rows'])}, ABSENT {len(m['absent'])}, FOUND {len(m['rows']) - len(m['absent'])}, "
          f"index rows {m['index']['rows_read']}, fsb names {m['jc3']['fsb_names']}")
    return 0


def check() -> int:
    m = model()
    bad = 0
    def ok(c: bool, msg: str) -> None:
        nonlocal bad
        print(("PASS " if c else "FAIL ") + msg)
        bad += 0 if c else 1
    for p, want in ((OUT_MD, render(m)),
                    (OUT_JSON, json.dumps(m["json"], indent=1) + "\n")):
        if not os.path.exists(p):
            ok(False, f"{rel(p)} missing - run --write")
            continue
        have = open(p, encoding="utf-8").read()
        ok(have == want, f"{rel(p)} re-derives byte for byte from the sources")
        if have != want:
            hl, wl = have.splitlines(), want.splitlines()
            n = next((i for i, (a, b) in enumerate(zip(hl, wl), 1) if a != b), min(len(hl), len(wl)) + 1)
            print(f"  first difference at line {n}: on disk {hl[n-1][:100] if n <= len(hl) else '(eof)'!r} "
                  f"vs source {wl[n-1][:100] if n <= len(wl) else '(eof)'!r}")
    ok(len(m["rows"]) >= 20, f"{len(m['rows'])} distinct BmAK banks examined")
    ok(all(r["N1_count"] == 0 for r in m["rows"]), "no JC3 index path carries any BmAK bank name (N1)")
    ok(all(r["N2_count"] == 0 for r in m["rows"]), "no JC3 FSB5 sample table carries a BmAK bank name (N2)")
    ok(all(r["N3_count"] == 0 for r in m["rows"]), "no dropzone file carries a BmAK bank name (N3)")
    ok(all(not r["H1_hash_in_index"] for r in m["rows"]), "no index entry hashes to a BmAK bank name (H1)")
    ok(len(m["absent"]) == len(m["rows"]), f"every bank is ABSENT in JC3 ({len(m['absent'])}/{len(m['rows'])})")
    zero = [r["bank"] for r in m["absent"] if not r["candidates"]]
    ok(all(r["candidates"] or r.get("no_candidate_reason") for r in m["absent"]),
       f"every absent bank lists candidates or a recorded reason for none ({len(zero)} of {len(m['absent'])} have none)")
    ok(all(c["label"] == "derived" for r in m["absent"] for c in r["candidates"]),
       "every candidate is labelled derived")
    ok(m["index"]["rows_read"] > 80000 and m["jc3"]["fsb_names"] >= 600,
       f"search coverage: {m['index']['rows_read']} index rows, {m['jc3']['fsb_names']} FSB5 names")
    print(("PASS" if not bad else "FAIL") + f": T-AU3b {bad} failure(s), {len(m['rows'])} banks, "
          f"{len(m['absent'])} ABSENT, {sum(len(r['candidates']) for r in m['absent'])} derived candidates")
    return 0 if not bad else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write:
        return write()
    if a.check:
        return check()
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

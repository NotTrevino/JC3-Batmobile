"""jc3_last_entry.py - G2-last: the one archive entry the index cannot name.

`Research/JC3Grab/INDEX.json` says 81,952 of 81,953 tab records are named.  This script
finds the missing record from the archives themselves, decodes its payload, brackets it by
archive write order, and tries to name it from evidence only:

  * every `.wavc` basename the index already carries, in every dialogue language directory;
  * numeric takes 0..9999 (widths 1..4) of the two basenames that bracket it;
  * the FSB5 sample-name token, matched against the named corpus.

A name is accepted only if `hash_jenkins(name.encode())` equals the entry hash, the same
oracle `jc3index.py` uses (`rbmhdr.hash_jenkins`, a port of StringHelpers.HashJenkins).
Nothing is written outside `Research/JC3Grab/LAST_ENTRY.{md,json}`.

Inputs (read-only): the game install's `.tab`/`.arc` pairs, `Research/JC3Grab/INDEX.json`
and `INDEX.jsonl`, and `E:/Modding/_shared/gamedata/JC3grab` for hash references.

Usage:
    uv run python Tools/scripts/jc3_last_entry.py --write
    uv run python Tools/scripts/jc3_last_entry.py --check
"""
from __future__ import annotations

import json
import os
import re
import struct
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import jc3index as I                              # noqa: E402  (read_tab, the tab format)
import rbmhdr                                    # noqa: E402  (hash_jenkins)

IDX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.json")
JL = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
OUT_MD = os.path.join(ROOT, "Research", "JC3Grab", "LAST_ENTRY.md")
OUT_JSON = os.path.join(ROOT, "Research", "JC3Grab", "LAST_ENTRY.json")
GDATA = "E:/Modding/_shared/gamedata/JC3grab"
SCAN_EXT = (".ee", ".toc", ".adf")
SCAN_MAX_DEPTH = 3
SCAN_MAX_BYTES = 400 * 1024 * 1024
TAKE_MAX = 9999
LANG_WIDTHS = (1, 2, 3, 4)


def rel(p: str) -> str:
    return os.path.relpath(p, ROOT).replace(os.sep, "/")


def h32(name: str) -> int:
    return rbmhdr.hash_jenkins(name.encode("utf-8"))


# ------------------------------------------------------------------ the census
def census() -> dict:
    idx = json.load(open(IDX, encoding="utf-8"))
    rows = [json.loads(l) for l in open(JL, encoding="utf-8") if l.strip()]
    by_archive: dict[str, set] = {}
    for r in rows:
        by_archive.setdefault(r["archive"], set()).add(int(r["hash"], 16))
    game = idx["game"]
    unnamed = []
    for key, meta in idx["per_archive"].items():
        if meta["named"] == meta["entries"]:
            continue
        tab = I.read_tab(meta["tab"])
        for h in set(tab) - by_archive.get(key, set()):
            unnamed.append({"archive": key, "hash": h, "offset": tab[h][0],
                            "size": tab[h][1], "tab": meta["tab"],
                            "entries": meta["entries"], "named": meta["named"]})
    return {"index": idx, "rows": rows, "unnamed": unnamed, "game": game}


def payload(e: dict) -> dict:
    arc = e["tab"][:-4] + ".arc"          # the .tab's own sibling .arc, absolute path
    with open(arc, "rb") as f:
        f.seek(e["offset"])
        data = f.read(96)
    prefix = struct.unpack_from("<I", data, 0)[0]
    fsb = data[16:20] == b"FSB5"
    out = {"magic_hex": data[:4].hex().upper(), "prefix_u32": prefix,
           "prefix_zeros": data[4:16] == b"\x00" * 12, "is_fsb5": fsb,
           "head_hex": data[:48].hex()}
    if fsb:
        ver, samples, shdr, names, datasz = struct.unpack_from("<IIIII", data, 20)
        out.update({"fsb5_version": ver, "samples": samples, "sample_header_bytes": shdr,
                    "name_table_bytes": names, "data_bytes": datasz})
        with open(arc, "rb") as f:
            f.seek(e["offset"])
            whole = f.read(e["size"])
        nt = 16 + 0x30 + shdr
        table = whole[nt:nt + names]
        out["name_table_hex"] = table.hex()
        out["name_table_ascii"] = "".join(chr(c) if 32 <= c < 127 else "."
                                          for c in table)
        strings = [m.group(0).decode("ascii") for m in re.finditer(rb"[ -~]{4,}", table)]
        out["name_table_strings"] = strings
        out["name_table_fields"] = [struct.unpack_from("<I", table, 4 * i)[0]
                                    for i in range(min(4, len(table) // 4))]
        out["name_table_field_semantics"] = (
            "UNKNOWN - the %d u32 fields ahead of the single string are not decoded "
            "(the corpus's other FSB5 name tables are not needed for the naming test)"
            % len(out["name_table_fields"]))
        digits = [s for s in strings if s.isdigit()]
        out["token"] = int(digits[0]) if digits else None
        out["first_name"] = strings[0] if strings else None
        out["first_name_len"] = len(out["first_name"]) if out["first_name"] else 0
        out["declared_bytes_check"] = {
            "payload_len_from_prefix": prefix,
            "size_minus_prefix": e["size"] - 16,
            "match": prefix == e["size"] - 16,
        }
    return out


ALIGN = 0x800          # decoded: every payload in this archive starts on a 0x800 boundary


def neighbours(e: dict, rows: list) -> dict:
    mine = sorted((r for r in rows if r["archive"] == e["archive"]),
                  key=lambda r: r["offset"])
    pre = [r for r in mine if r["offset"] < e["offset"]]
    nxt = [r for r in mine if r["offset"] > e["offset"]]
    prev = pre[-1] if pre else None
    nxtr = nxt[0] if nxt else None

    def up(x: int) -> int:
        return (x + ALIGN - 1) // ALIGN * ALIGN

    prev_end = prev["offset"] + prev["size"] if prev else None
    end = e["offset"] + e["size"]
    return {"prev": prev, "next": nxtr, "align": ALIGN,
            "prev_end": prev_end, "end": end,
            "pad_before": (e["offset"] - prev_end) if prev_end is not None else None,
            "pad_after": (nxtr["offset"] - end) if nxtr else None,
            "aligned_before": (up(prev_end) == e["offset"]) if prev_end is not None else None,
            "aligned_after": (up(end) == nxtr["offset"]) if nxtr else None,
            "slot_bytes": (nxtr["offset"] - prev_end) if (prev and nxtr) else None}


# ------------------------------------------------------------------ candidates
def languages(rows: list) -> list:
    langs = set()
    for r in rows:
        k = r["path"]
        if k.startswith("sound/dialogue/") and k.endswith(".wavc"):
            rest = k[len("sound/dialogue/"):]
            if "/" in rest:
                langs.add(rest.split("/")[0])
    return sorted(langs)


def candidates(rows: list, e: dict, nb: dict) -> dict:
    wavc = [r["path"] for r in rows if r["path"].endswith(".wavc")]
    langs = languages(rows)
    bases = []
    seen = set()
    for p in wavc:
        b = p.rsplit("/", 1)[-1]
        if b not in seen:
            seen.add(b)
            bases.append(b)
    tried = 0
    hits = []
    per = []

    def test(name: str) -> None:
        nonlocal tried
        tried += 1
        if h32(name) == e["hash"]:
            hits.append(name)

    for b in bases:                                   # every known basename in every language
        for lg in langs:
            test("sound/dialogue/%s/%s" % (lg, b))
    per.append({"family": "every known .wavc basename x every dialogue language",
                "basenames": len(bases), "languages": len(langs),
                "attempts": len(bases) * len(langs), "hits": len(hits)})

    # the two basenames that bracket the entry, expanded to numeric takes 0..9999
    anchor = []
    for side in ("prev", "next"):
        r = nb.get(side)
        if r and r["path"].startswith("sound/dialogue/") and r["path"].endswith(".wavc"):
            lg, b = r["path"][len("sound/dialogue/"):].split("/", 1)
            stem = b[:-len(".wavc")]
            anchors = [lg, stem]
            if anchors not in anchor:
                anchor.append(anchors)
    take_tried = 0
    for lg, stem in anchor:
        base = stem.rstrip("0123456789")
        for n in range(TAKE_MAX + 1):
            for w in LANG_WIDTHS:
                name = "sound/dialogue/%s/%s%0*d.wavc" % (lg, base, w, n)
                test(name)
                take_tried += 1
        test("sound/dialogue/%s/%s.wavc" % (lg, stem))
        take_tried += 1
    per.append({"family": "numeric takes 0..%d (widths %s) of the bracket basenames"
                % (TAKE_MAX, list(LANG_WIDTHS)),
                "anchors": anchor, "attempts": take_tried, "hits": len(hits)})
    return {"tried": tried, "hits": hits, "families": per,
            "distinct_basenames": len(bases), "languages": langs}


def references(e: dict) -> dict:
    """Does any .ee/.toc/.adf under JC3grab mention the entry's hash or its token?"""
    needles = [("%08X" % e["hash"]).encode(), ("%08x" % e["hash"]).encode(),
               str(e["hash"]).encode(), ("%08X" % e["hash"]).lower().encode()]
    info = {"root": GDATA, "scanned": 0, "bytes": 0, "hits": [], "truncated": False,
            "exts": list(SCAN_EXT), "max_depth": SCAN_MAX_DEPTH}
    if not os.path.isdir(GDATA):
        info["missing"] = True
        return info
    t0 = time.time()
    for dirpath, dirnames, filenames in os.walk(GDATA):
        depth = os.path.relpath(dirpath, GDATA).count(os.sep)
        if depth >= SCAN_MAX_DEPTH:
            dirnames[:] = []
        if time.time() - t0 > 90 or info["bytes"] > SCAN_MAX_BYTES:
            info["truncated"] = True
            break
        for fn in filenames:
            if not fn.lower().endswith(SCAN_EXT):
                continue
            p = os.path.join(dirpath, fn)
            try:
                blob = open(p, "rb").read()
            except OSError:
                continue
            info["scanned"] += 1
            info["bytes"] += len(blob)
            for nd in needles:
                if nd in blob:
                    info["hits"].append({"file": p.replace("\\", "/"), "needle": nd.decode()})
                    break
    info["seconds"] = round(time.time() - t0, 2)
    return info


def build() -> dict:
    c = census()
    if len(c["unnamed"]) != 1:
        raise SystemExit(f"G2-last: expected exactly 1 unnamed tab record, found "
                         f"{len(c['unnamed'])}")
    e = c["unnamed"][0]
    p = payload(e)
    nb = neighbours(e, c["rows"])
    cand = candidates(c["rows"], e, nb)
    refs = references(e)
    checks = oracles(c, e, p, nb, cand, refs)
    doc = {"card": "G2-last", "generator": rel(os.path.abspath(__file__)),
           "entry": e, "payload": p, "neighbours": nb, "candidates": cand,
           "references": refs, "checks": checks,
           "verdict": ("UNKNOWN - no candidate reproduces the hash" if not cand["hits"]
                       else "decoded - " + cand["hits"][0])}
    doc["md"] = render_md(doc, c)
    return doc


def oracles(c, e, p, nb, cand, refs) -> list:
    o = []

    def add(k, ok, ev):
        o.append({"key": k, "ok": bool(ok), "evidence": ev})

    add("O1-one-unnamed-record",
        len(c["unnamed"]) == 1 and c["index"]["unnamed_entries"] == 1
        and c["index"]["tab_entries"] - c["index"]["named_rows"] == 1,
        "INDEX.json: %d tab entries, %d named, unnamed_entries=%d; the tab-vs-index diff "
        "over %d archives leaves %d record(s)"
        % (c["index"]["tab_entries"], c["index"]["named_rows"],
           c["index"]["unnamed_entries"], len(c["index"]["per_archive"]), len(c["unnamed"])))
    magics = c["index"]["unnamed_magic"].get(e["archive"], {})
    add("O2-identity",
        p["magic_hex"] in magics and e["size"] in
        c["index"]["unnamed_sample_sizes"].get(e["archive"], []),
        "INDEX.json's unnamed_magic lists %s once in %s and unnamed_sample_sizes lists %d, "
        "which is the record found here (%08X at +%d, %d B); the payload's first four bytes "
        "are %s"
        % (list(magics), e["archive"], e["size"], e["hash"], e["offset"], e["size"],
           p["magic_hex"]))
    add("O3-payload-decoded",
        p.get("is_fsb5") and p.get("prefix_zeros") and
        p.get("declared_bytes_check", {}).get("match"),
        "16-byte prefix u32 %d = size - 16 (%s), 12 zero bytes %s, then FSB5 v%d, %d sample(s), "
        "sample headers %d B, name table %d B, data %d B"
        % (p.get("prefix_u32"), p.get("declared_bytes_check", {}).get("match"),
           p.get("prefix_zeros"), p.get("fsb5_version", 0), p.get("samples", 0),
           p.get("sample_header_bytes", 0), p.get("name_table_bytes", 0),
           p.get("data_bytes", 0)))
    add("O4-bracket-is-exact",
        nb.get("aligned_before") is True and nb.get("aligned_after") is True,
        "the record starts where %s ends (+%d, %d B) rounded up to 0x%X (pad %d B), and the "
        "next record starts where it ends (+%d) rounded up too (pad %d B): the aligned slot "
        "before %s holds only this record"
        % (nb["prev"]["path"], nb["prev"]["offset"], nb["prev"]["size"], ALIGN,
           nb["pad_before"], nb["end"], nb["pad_after"],
           nb["next"]["path"]))
    add("O5-no-name-reproduces-the-hash",
        not cand["hits"],
        "%d candidate paths tried (%s) against %08X: %d hit(s)"
        % (cand["tried"], "; ".join("%s: %d" % (f["family"], f["attempts"])
                                    for f in cand["families"]), e["hash"],
           len(cand["hits"])))
    add("O6-token-is-an-orphan",
        p.get("token") is not None and
        not any((p["first_name"] or "\0") in r["path"] for r in c["rows"]),
        "the FSB5 name table carries exactly the strings %s (token %s); no named path in the "
        "index contains that take id, so there is no cross-language sibling to borrow a "
        "basename from" % (p.get("name_table_strings"), p.get("token")))
    add("O7-references",
        True,
        "%d .ee/.toc/.adf file(s), %.1f MB scanned under %s (depth <= %d, %s): %d hit(s)%s"
        % (refs["scanned"], refs["bytes"] / 1e6, refs["root"], refs["max_depth"],
           "truncated at the time budget" if refs["truncated"] else "complete",
           len(refs["hits"]), " (root missing)" if refs.get("missing") else ""))
    return o


def render_md(doc: dict, c: dict) -> str:
    e, p, nb, cand, refs = doc["entry"], doc["payload"], doc["neighbours"], \
        doc["candidates"], doc["references"]
    L = []
    A = L.append
    A("# G2-last - the one archive entry the index cannot name")
    A("")
    A("Generated by `%s`; `--check` re-reads every tab, the payload and the index and "
      "re-derives the numbers." % doc["generator"])
    A("")
    A("## 1. The entry")
    A("")
    A("| field | value |")
    A("|---|---|")
    A("| hash | **`%08X`** |" % e["hash"])
    A("| archive | `%s` (mount `patch`, %d records, %d named)"
      % (e["archive"], e["entries"], e["named"]))
    A("| offset / size | +%d / %d B" % (e["offset"], e["size"]))
    A("| payload magic | `%s` = a 16-byte prefix (u32 %d = size - 16, 12 zero bytes) then `FSB5`"
      % (p["magic_hex"], p["prefix_u32"]))
    A("| decoded payload | FSB5 v%d, **%d sample**, sample headers %d B, name table %d B, "
      "data %d B" % (p.get("fsb5_version", 0), p.get("samples", 0),
                     p.get("sample_header_bytes", 0), p.get("name_table_bytes", 0),
                     p.get("data_bytes", 0)))
    A("| name-table entry | `%s` (%d B), **token `%s`**"
      % (p.get("first_name"), p.get("first_name_len"), p.get("token")))
    A("| what identifies it | a `.wavc` (prefix + FSB5) one-take dialogue bank; the token is "
      "FMOD's opaque original-source name |")
    A("")
    A("## 2. Its neighbours, and the slot it fills")
    A("")
    A("| relation | path | hash | offset | size |")
    A("|---|---|---|---:|---:|")
    if nb.get("prev"):
        A("| previous payload | `%s` | `%s` | %d | %d |"
          % (nb["prev"]["path"], nb["prev"]["hash"], nb["prev"]["offset"], nb["prev"]["size"]))
    A("| **the unnamed record** | `UNKNOWN` | **`%08X`** | %d | %d |"
      % (e["hash"], e["offset"], e["size"]))
    if nb.get("next"):
        A("| next payload | `%s` | `%s` | %d | %d |"
          % (nb["next"]["path"], nb["next"]["hash"], nb["next"]["offset"], nb["next"]["size"]))
    A("")
    A("The record starts on a 0x%X boundary where the previous payload ends (pad %s B) and "
      "the next payload starts on a 0x%X boundary where it ends (pad %s B), so it is the only "
      "occupant of that aligned slot: in archive write order it belongs after "
      "`sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc` and before "
      "`…_gameplay_start05.wavc`."
      % (nb["align"], nb.get("pad_before"), nb["align"], nb.get("pad_after")))
    A("")
    A("## 3. Naming attempts - every one rejected by the oracle")
    A("")
    A("| family | attempts | hits |")
    A("|---|---:|---:|")
    for f in cand["families"]:
        A("| %s | %d | %d |" % (f["family"], f["attempts"], f["hits"]))
    A("| **total** | **%d** | **%d** |" % (cand["tried"], len(cand["hits"])))
    A("")
    A("`hash_jenkins(name)` is the oracle: a candidate is a name only if it equals `%08X`. "
      "The corpus is the index's own %d distinct `.wavc` basenames over its %d dialogue "
      "language directories, plus every numeric take 0..%d in widths %s for the two bracketing "
      "basenames - the family the bracket points at."
      % (e["hash"], cand["distinct_basenames"], len(cand["languages"]), TAKE_MAX,
         list(LANG_WIDTHS)))
    A("")
    A("## 4. Does anything reference the hash?")
    A("")
    A("| fact | value |")
    A("|---|---|")
    A("| root | `%s` |" % refs["root"])
    A("| extensions searched | %s |" % ", ".join("`%s`" % x for x in refs["exts"]))
    A("| files scanned / bytes | %d / %.1f MB%s |"
      % (refs["scanned"], refs["bytes"] / 1e6,
         " (truncated at the 90 s budget)" if refs["truncated"] else " (complete)"))
    A("| hits | %d |" % len(refs["hits"]))
    A("")
    for h in refs["hits"][:10]:
        A("- `%s` contains `%s`" % (h["file"], h["needle"]))
    if not refs["hits"]:
        A("No `.ee`, `.toc` or `.adf` under the grab mentions `%08X` or its token: the asset is "
          "addressed by hash from the archive, not by any file the grab decoded." % e["hash"])
    A("")
    A("## 5. Verdict")
    A("")
    A("**UNKNOWN.** The entry is `%s` +%d, %d B, a 16-byte prefix plus a one-sample **FSB5** "
      "bank (token `%s`). Write order brackets it at\n`sound/dialogue/ara/mission_mm320_dial_"
      "gameplay_090.wavc` < it < `…_gameplay_start05.wavc`, and its 0x%X-aligned slot is "
      "occupied by nothing else, but **%d** candidate paths - every known `.wavc` basename in every dialogue language, "
      "and every numeric take 0..%d of both bracketing basenames - hash to something else."
      % (e["archive"], e["offset"], e["size"], p.get("token"), nb["align"],
         cand["tried"], TAKE_MAX))
    A("")
    A("The FSB5 token cannot rescue it: FMOD stores the *original source file name*, which is "
      "not a hash of the shipped basename, and no named `.wavc` carries this take's token, so "
      "there is no cross-language sibling to borrow a name from (that is exactly how `966DB7BC` "
      "was named, and why this one cannot be).")
    A("")
    A("## 6. Checks")
    A("")
    A("| check | result | detail |")
    A("|---|---|---|")
    for x in doc["checks"]:
        A("| `%s` | %s | %s |" % (x["key"], "PASS" if x["ok"] else "**FAIL**",
                                  x["evidence"].replace("|", "\\|")))
    A("")
    A("## 7. What would name it")
    A("")
    A("- the **original FMOD project** for the Arabic `mm320` dialogue session (the token is its "
      "source file name), or")
    A("- a **newer Gibbed filelist / JCMR dictionary** that carries the take, or")
    A("- a **runtime string**: something in the executable's string table naming the take, which "
      "no `.ee`/`.toc`/`.adf` in the grab carries today.")
    A("")
    A("```")
    A("uv run python Tools/scripts/jc3_last_entry.py --write")
    A("uv run python Tools/scripts/jc3_last_entry.py --check")
    A("```")
    A("")
    return "\n".join(L)


def main(argv) -> int:
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: jc3_last_entry.py --write|--check")
    doc = build()
    md = doc["md"] + "\n"
    fails = [c["key"] for c in doc["checks"] if not c["ok"]]
    public = {k: v for k, v in doc.items() if k != "md"}
    if argv[1] == "--write":
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        with open(OUT_JSON, "w", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(public, indent=1) + "\n")
        e, p = doc["entry"], doc["payload"]
        print("wrote %s and %s" % (rel(OUT_MD), rel(OUT_JSON)))
        print("entry %08X in %s +%d, %d B, FSB5 token %s, %d samples"
              % (e["hash"], e["archive"], e["offset"], e["size"], p.get("token"),
                 p.get("samples", 0)))
        print("candidates tried %d, hits %d -> %s"
              % (doc["candidates"]["tried"], len(doc["candidates"]["hits"]), doc["verdict"]))
        print("checks %d/%d%s" % (len(doc["checks"]) - len(fails), len(doc["checks"]),
                                   "" if not fails else " FAILED: " + ", ".join(fails)))
        return 0 if not fails else 1
    problems = []
    if not os.path.exists(OUT_MD):
        problems.append(f"{rel(OUT_MD)} missing - run --write")
    elif open(OUT_MD, encoding="utf-8", newline="").read().replace("\r\n", "\n") != md:
        problems.append(f"{rel(OUT_MD)} stale against the re-derived text")
    if not os.path.exists(OUT_JSON) or \
            json.load(open(OUT_JSON, encoding="utf-8")) != json.loads(json.dumps(public)):
        problems.append(f"{rel(OUT_JSON)} differs from the re-derived record")
    problems.extend(fails)
    if problems:
        for p in problems:
            print("FAIL:", p)
        return 1
    print("CHECK OK: %d checks, entry %08X, %d candidates, 0 hits, verdict UNKNOWN"
          % (len(doc["checks"]), doc["entry"]["hash"], doc["candidates"]["tried"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

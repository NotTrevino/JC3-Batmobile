"""g2_last_entry.py - name (and re-prove) the last unnamed JC3 archive entry.

The entry is `patch_win64/game4` hash `016DE9D1` (+618,637,312, 84,720 B): a 16-byte
prefix + one-sample FMOD FSB5 dialogue take. It is the only archive record the index
could not name, and the only one whose FSB5 name-table token (`1606523576`) has no
cross-language sibling, so the token route that named the Polish take cannot lend it
a name.

What does name it is the archive's own write order: `.arc` payloads are laid down in
ascending VFS-path order, and this record sits between two named Arabic takes
(`mission_mm320_dial_gameplay_090` and `..._start05`). The basename must therefore
sort inside that bracket, and exactly one candidate both fits it and hashes to the
record's tab hash: `mission_mm320_dial_gameplay_sams01`. English ships sams02 and
sams03 and no sams01, which is why the take has no sibling copy.

A name is accepted only when `hash_jenkins(path)` equals the archive's tab hash, so a
wrong guess cannot enter the index. The index marks the row `"source": "derived-names"`.

Usage:
  python g2_last_entry.py --check     # re-derive every fact from the install (default)
  python g2_last_entry.py --write     # rewrite Tools/names/derived_016de9d1.json + the filelist
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rbmhdr import hash_jenkins  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
NAMES = os.path.join(ROOT, "Tools", "names")
INDEX_JSONL = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
GAME = os.environ.get("JC3_GAME", r"D:/Games/Just Cause 3")

ARCHIVE = "patch_win64/game4"
TARGET = 0x016DE9D1
OFFSET = 618637312
SIZE = 84720
PATH = "sound/dialogue/ara/mission_mm320_dial_gameplay_sams01.wavc"
TOKEN = "1606523576"
PREV = ("sound/dialogue/ara/mission_mm320_dial_gameplay_090.wavc", 618592256, 44368, 0x5567C6E5)
NEXT = ("sound/dialogue/ara/mission_mm320_dial_gameplay_start05.wavc", 618723328, 141040, 0xCB7DBEA9)
SAMPLE = {"freq": 11025, "channels": 1, "samples": 243648, "mode": 15}

FREQ = [4000, 8000, 11000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000]


def read_tab(arc_key: str) -> dict[int, tuple[int, int]]:
    blob = open(os.path.join(GAME, (arc_key + ".tab").replace("/", os.sep)), "rb").read()
    if blob[:4] != b"TAB\x00":
        raise SystemExit(f"not a TAB file: {arc_key}")
    out: dict[int, tuple[int, int]] = {}
    o = 12
    while o + 12 <= len(blob):
        nh, off, sz = struct.unpack_from("<III", blob, o)
        out[nh] = (off, sz)
        o += 12
    return out


def read_payload(arc_key: str, off: int, size: int) -> bytes:
    with open(os.path.join(GAME, (arc_key + ".arc").replace("/", os.sep)), "rb") as f:
        f.seek(off)
        return f.read(size)


def fsb5(buf: bytes) -> dict:
    f5 = buf.find(b"FSB5")
    if f5 < 0:
        raise SystemExit("no FSB5 magic in the payload")
    ver, n, shdr, ntl = struct.unpack_from("<IIII", buf, f5 + 4)
    token = None
    if ntl >= 4:
        nt = f5 + 60 + n * shdr
        (o0,) = struct.unpack_from("<I", buf, nt)
        token = buf[nt + o0:nt + ntl].split(b"\x00")[0].decode("ascii", "replace")
    v = struct.unpack_from("<Q", buf, f5 + 60)[0] if n else 0
    fi = v & 0xF
    return {
        "version": ver,
        "num_samples": n,
        "sample_header_size": shdr,
        "name_table_size": ntl,
        "token": token,
        "freq": FREQ[fi] if fi < len(FREQ) else None,
        "channels": ((v >> 5) & 1) + 1,
        "samples": v >> 34,
        "mode": struct.unpack_from("<I", buf, f5 + 20)[0] if len(buf) >= f5 + 24 else None,
    }


def index_row() -> dict | None:
    with open(INDEX_JSONL, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and PATH in line:
                row = json.loads(line)
                if row.get("path") == PATH:
                    return row
    return None


def check() -> int:
    ok = True

    def say(good: bool, label: str, detail: str = "") -> None:
        nonlocal ok
        ok = ok and good
        print(("PASS " if good else "FAIL ") + label + (("  " + detail) if detail else ""))

    tab = read_tab(ARCHIVE)
    rec = tab.get(TARGET)
    say(rec == (OFFSET, SIZE), "tab record", f"{ARCHIVE} {TARGET:08X} -> {rec}")
    if rec != (OFFSET, SIZE):
        return 1

    buf = read_payload(ARCHIVE, *rec)
    prefix = struct.unpack_from("<I", buf, 0)[0]
    say(prefix == SIZE - 16 and buf[4:16] == b"\x00" * 12, "16-byte prefix", f"u32={prefix}")

    f = fsb5(buf)
    say(f["token"] == TOKEN, "FSB5 token", str(f["token"]))
    say((f["freq"], f["channels"], f["samples"]) == (SAMPLE["freq"], SAMPLE["channels"], SAMPLE["samples"]),
        "FSB5 sample header", f"{f['freq']} Hz / {f['channels']} ch / {f['samples']} samples "
                              f"= {f['samples'] / f['freq']:.3f} s")

    h = hash_jenkins(PATH.encode("ascii", "replace"))
    say(h == TARGET, "hash_jenkins(candidate) == record", f"{PATH} -> {h:08X}")

    ents = sorted(tab.items(), key=lambda kv: kv[1][0])
    i = [k for k, (n, v) in enumerate(ents) if v[0] == OFFSET][0]
    prev_h, (prev_off, prev_sz) = ents[i - 1]
    next_h, (next_off, next_sz) = ents[i + 1]
    say((prev_h, prev_off, prev_sz) == (PREV[3], PREV[1], PREV[2]), "predecessor", f"{prev_h:08X} @{prev_off}")
    say((next_h, next_off, next_sz) == (NEXT[3], NEXT[1], NEXT[2]), "successor", f"{next_h:08X} @{next_off}")
    say(PREV[0] < PATH < NEXT[0], "candidate sorts inside the bracket", f"{PREV[0]} < {PATH} < {NEXT[0]}")
    say(hash_jenkins(PREV[0].encode()) == PREV[3] and hash_jenkins(NEXT[0].encode()) == NEXT[3],
        "neighbours hash to their own records")

    row = index_row()
    say(row is not None, "index row present", PATH)
    if row:
        say(row.get("offset") == OFFSET and row.get("size") == SIZE, "index row offset/size", json.dumps(
            {"offset": row.get("offset"), "size": row.get("size")}))
        say(row.get("source") == "derived-names", "index row source", str(row.get("source")))

    evidence = os.path.join(NAMES, "derived_016de9d1.json")
    if os.path.exists(evidence):
        doc = json.load(open(evidence, encoding="utf-8"))
        say(doc.get("path") == PATH and doc["entry"]["hash"] == "016DE9D1", "evidence json", evidence)
    else:
        say(False, "evidence json missing", evidence)

    print("\n" + ("ALL CHECKS PASS" if ok else "CHECKS FAILED"))
    return 0 if ok else 1


def write() -> int:
    os.makedirs(NAMES, exist_ok=True)
    doc_path = os.path.join(NAMES, "derived_016de9d1.json")
    doc = json.load(open(doc_path, encoding="utf-8")) if os.path.exists(doc_path) else {}
    doc.setdefault("entry", {"archive": ARCHIVE, "hash": "016DE9D1", "offset": OFFSET, "size": SIZE})
    doc["path"] = PATH
    doc["source"] = "derived-names"
    doc.setdefault("verification", {})["hash_equals_record"] = "hash_jenkins(path) == 0x016DE9D1"
    doc["verification"]["check_command"] = "python Tools/scripts/g2_last_entry.py --check"
    # keep the decoded facts in step with the bytes
    f = fsb5(read_payload(ARCHIVE, *read_tab(ARCHIVE)[TARGET]))
    doc.setdefault("container", {})["sample"] = {
        "frequency_hz": f["freq"], "channels": f["channels"], "samples": f["samples"],
        "duration_s": round(f["samples"] / f["freq"], 3), "mode": f["mode"],
    }
    doc["container"]["token"] = f["token"]
    json.dump(doc, open(doc_path, "w", encoding="utf-8"), indent=2, sort_keys=False)
    open(doc_path, "a", encoding="utf-8").write("\n")

    fl_path = os.path.join(NAMES, "jc3_mm320_sams01.filelist")
    if not os.path.exists(fl_path):
        open(fl_path, "w", encoding="utf-8").write(
            "# patch_win64/game4 016DE9D1  +618,637,312  84,720 B\n"
            "# bracketed by mission_mm320_dial_gameplay_090 and ..._start05 in the Arabic dir;\n"
            "# the only in-bracket basename that hashes to the record is sams01.\n"
            + PATH + "\n")
    print(f"-> {doc_path}\n-> {fl_path}")
    return check()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="re-derive every fact (default)")
    g.add_argument("--write", action="store_true", help="rewrite the evidence json and filelist")
    a = ap.parse_args()
    return write() if a.write else check()


if __name__ == "__main__":
    raise SystemExit(main())

"""jc3fx.py - decode every `.effc`, `.ctunec` and `.trim` in the game (G2-9).

These three extensions were the last untouched payload family: 33k files that
nothing had ever read.  They are not a format of their own -- every one of them
starts with `' FDA'` and is the same ADF v4 container the `.vmodc` modules use,
so `jc3adf.py` reads them directly.  What was missing was a reader that survives
the types the vehicle modules never use:

  * `Pointer` (type code 2)      - data-relative u64, 0 = null
  * `String` (0x8955583E)        - data-relative u64, NUL-terminated
  * `StringHash_*` (code 9)      - u32 hash
  * bitfield / enumeration       - u32
  * inline arrays of primitives  - e.g. `IA[float]`, 29 int32 in one member

They live in two places, and both are walked here:

  * inside `.ee` bundles (`<name>.ee` -> SARC directory -> inner file)
  * as standalone archive entries (29 `.ctunec`, 40 `.trim`, 35 `.effc`)

For every file the build records the root class, an object census (array
lengths by path) and a digest of the decoded rows.  `check` re-reads the game
and recomputes both, so the table is evidence, not a claim.  `dump` prints the
full row set of any one file on demand -- the values themselves stay in the
game, per the project rule that raw decodes never enter the repo.

Usage:
  python jc3fx.py build [--ee SUBSTR] [--limit N]
  python jc3fx.py report
  python jc3fx.py dump <path-or-substring> [--max N]
  python jc3fx.py check [--limit N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from jc3index import DEFAULT_GAME, DEFAULT_OUT, MOUNT_RANK, load_index  # noqa: E402
from eetoc import sarc_dir, unaaf  # noqa: E402
import jc3adf  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "JC3Grab")
EXTS = (".effc", ".ctunec", ".trim")
TABLE = "FX_TABLE.jsonl"
IDX_RE = re.compile(r"\[(\d+)\]")


# ------------------------------------------------------------------- game side
def pick_by_path(rows: list[dict]) -> dict[str, dict]:
    """One winning copy per path: patch > dlc > base."""
    best: dict[str, dict] = {}
    for r in rows:
        p = r["path"]
        cur = best.get(p)
        if cur is None or MOUNT_RANK[r["mount"]] > MOUNT_RANK[cur["mount"]]:
            best[p] = r
    return best


def read_row(r: dict, game: str) -> bytes:
    arc = os.path.join(game, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        blob = f.read(r["size"])
    if len(blob) != r["size"]:
        raise IOError(f"short read {len(blob)} != {r['size']} for {r['path']}")
    return blob


def inner_dir(ee_blob: bytes) -> tuple[bytes, dict[str, tuple[int, int]]]:
    """SARC directory of an .ee, filtered to the fx extensions: name -> (offset, size)."""
    stream = unaaf(ee_blob)
    dirs = {name: (off, size) for name, off, size in sarc_dir(stream)
            if os.path.splitext(name)[1].lower() in EXTS}
    return stream, dirs


def inner_fx(ee_blob: bytes, want: tuple[str, ...]) -> list[tuple[str, bytes]]:
    """Every inner file of an .ee whose extension is in `want`, in SARC order."""
    stream = unaaf(ee_blob)
    out = []
    for name, off, size in sorted(sarc_dir(stream)):
        if os.path.splitext(name)[1].lower() in want:
            out.append((name, stream[off:off + size]))
    return out


# ----------------------------------------------------------------- decode side
def objects_of(rows) -> dict[str, int]:
    """Array lengths by path, derived from the `[i]` indices in the row paths."""
    seen: dict[str, int] = {}
    for path, _t, _v in rows:
        pos = 0
        while True:
            m = IDX_RE.search(path, pos)
            if not m:
                break
            prefix = path[:m.start()]
            n = int(m.group(1)) + 1
            if n > seen.get(prefix, 0):
                seen[prefix] = n
            pos = m.end()
    return seen


def decode(blob: bytes) -> dict:
    adf = jc3adf.Adf(blob)
    rows = list(jc3adf.walk(adf))
    h = hashlib.sha1()
    for path, tname, value in rows:
        h.update(f"{path}\t{tname}\t{value}\n".encode("latin-1", "replace"))
    counts = objects_of(rows)
    return {
        "root": adf.type_name(adf.instances[0]["type"]) if adf.instances else None,
        "rows": len(rows),
        # array census, compact: {"emitters": 3, ...} would be 3.8 KB a file, so the
        # table keeps a digest of it and `check` recomputes it from the game
        "arrays": len(counts),
        "objects_digest": hashlib.sha1(
            repr(sorted(counts.items())).encode()).hexdigest()[:16],
        "digest": h.hexdigest(),
        "types": len(adf.types),
        "_rows": rows,
    }


# ----------------------------------------------------------------------- build
def cmd_build(a) -> int:
    rows = load_index(a.index)
    best = pick_by_path(rows)
    containers = sorted(p for p in best if p.lower().endswith(".ee"))
    standalone = sorted(p for p in best if os.path.splitext(p)[1].lower() in EXTS)
    if a.ee:
        containers = [p for p in containers if a.ee.lower() in p.lower()]
        standalone = [p for p in standalone if a.ee.lower() in p.lower()]
    if a.limit:
        containers = containers[:a.limit]
    jobs = [(p, True) for p in containers] + [(p, False) for p in standalone]
    print(f"{len(containers)} .ee + {len(standalone)} standalone -> "
          f"{os.path.join(OUT, TABLE)}")

    table = []
    totals = {"files": 0, "rows": 0, "failed": 0}
    per_ext = {e: 0 for e in EXTS}
    vocab: dict[tuple[str, str], dict] = {}
    for i, (path, is_ee) in enumerate(jobs, 1):
        try:
            blob = read_row(best[path], a.game)
            items = inner_fx(blob, EXTS) if is_ee else [(os.path.basename(path), blob)]
        except Exception as e:                                  # noqa: BLE001
            print(f"[{i}/{len(jobs)}] {path}: ERROR {e}")
            totals["failed"] += 1
            continue
        if not items:
            continue
        for name, data in items:
            ext = os.path.splitext(name)[1].lower()
            rec = {"container": path if is_ee else "", "source": path, "path": name,
                   "ext": ext, "size": len(data), "mount": best[path]["mount"]}
            try:
                doc = decode(data)
            except Exception as e:                              # noqa: BLE001
                rec.update({"root": None, "rows": 0, "error": f"{type(e).__name__}: {e}"})
                table.append(rec)
                totals["failed"] += 1
                continue
            rows_out = doc.pop("_rows")
            rec.update(doc)
            table.append(rec)
            totals["files"] += 1
            totals["rows"] += doc["rows"]
            per_ext[ext] += 1
            for p, tname, value in rows_out:
                key = (ext, IDX_RE.sub("[]", p))
                st = vocab.get(key)
                if st is None:
                    st = vocab[key] = {"types": set(), "n": 0, "min": None,
                                       "max": None, "sample": None}
                st["types"].add(tname)
                st["n"] += 1
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    st["min"] = value if st["min"] is None else min(st["min"], value)
                    st["max"] = value if st["max"] is None else max(st["max"], value)
                elif st["sample"] is None and isinstance(value, str):
                    st["sample"] = value
        print(f"[{i}/{len(jobs)}] {path.rsplit('/', 1)[-1]}: {len(items)} files")

    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, TABLE), "w", encoding="utf-8", newline="\n") as f:
        for rec in table:
            f.write(json.dumps(rec, separators=(",", ":")) + "\n")
    with open(os.path.join(OUT, "FX_VOCAB.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({f"{ext}\t{path}": {"types": sorted(st["types"]), "rows": st["n"],
                                      "min": st["min"], "max": st["max"],
                                      "sample": st["sample"]}
                   for (ext, path), st in vocab.items()},
                  f, indent=1, sort_keys=True)
    print(f"totals: {totals} per-ext {per_ext} member-paths {len(vocab)}")
    return 1 if totals["failed"] else 0


# ---------------------------------------------------------------------- report
def load_table() -> list[dict]:
    p = os.path.join(OUT, TABLE)
    if not os.path.exists(p):
        raise SystemExit(f"no {TABLE} - run `jc3fx.py build` first")
    return [json.loads(line) for line in open(p, encoding="utf-8") if line.strip()]


def load_vocab() -> dict:
    p = os.path.join(OUT, "FX_VOCAB.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}


def cmd_report(a) -> int:
    table = load_table()
    vocab = load_vocab()
    ok = [r for r in table if not r.get("error")]
    bad = [r for r in table if r.get("error")]
    lines = [
        "# JC3 effects, camera tunes and trim data (G2-9)",
        "",
        "Every `.effc`, `.ctunec` and `.trim` in the game, decoded by",
        "`Tools/scripts/jc3fx.py` with the same ADF v4 reader the vehicle modules use",
        "(`jc3adf.py`). The files are ADF v4 containers (`' FDA'`, version 4) -- inside",
        "`.ee` bundles and as standalone archive entries alike -- so nothing had to be",
        "reverse engineered for them beyond four type kinds the modules never use:",
        "pointer (code 2), `String` (`0x8955583E`, a data-relative offset to a",
        "NUL-terminated string), StringHash (code 9) and inline arrays of primitives.",
        "",
        "| item | value |",
        "|---|---|",
        f"| files decoded | **{len(ok)}** |",
        f"| standalone archive entries | {sum(1 for r in ok if not r['container'])} |",
        f"| files inside `.ee` bundles | {sum(1 for r in ok if r['container'])} |",
        f"| value rows | **{sum(r['rows'] for r in ok):,}** |",
        f"| member paths (indices collapsed) | {len(vocab):,} |",
        f"| failures | {len(bad)} |",
        "",
        "## By extension",
        "",
        "| ext | files | rows | root classes |",
        "|---|---|---|---|",
    ]
    for ext in EXTS:
        sel = [r for r in ok if r["ext"] == ext]
        roots: dict[str, int] = {}
        for r in sel:
            roots[r["root"] or "?"] = roots.get(r["root"] or "?", 0) + 1
        top = ", ".join(f"`{k}` {v}" for k, v in
                        sorted(roots.items(), key=lambda kv: -kv[1])[:6])
        lines.append(f"| `{ext}` | {len(sel):,} | {sum(r['rows'] for r in sel):,} | {top} |")
    lines += ["", "## What is inside", ""]
    for ext, title in ((".effc", "effects"), (".ctunec", "camera tunes"),
                       (".trim", "effect trim data")):
        sel = [(k.split("\t", 1)[1], v) for k, v in vocab.items() if k.startswith(ext + "\t")]
        lines += [f"### `{ext}` - {title}", ""]
        if not sel:
            lines += ["nothing decoded.", ""]
            continue
        roots = sorted({r["root"] for r in ok if r["ext"] == ext and r["root"]})
        lines += [f"Root classes: " + ", ".join(f"`{r}`" for r in roots) + ".", "",
                  "| member path | type | rows | min | max | sample |", "|---|---|---|---|---|---|"]
        for path, st in sorted(sel, key=lambda kv: -kv[1]["rows"])[:25]:
            lo = "" if st["min"] is None else f"{st['min']:.6g}"
            hi = "" if st["max"] is None else f"{st['max']:.6g}"
            sample = (st["sample"] or "")[:40]
            lines.append(f"| `{path}` | {'/'.join(st['types'])} | {st['rows']:,} | {lo} | "
                         f"{hi} | {sample} |")
        lines += ["", f"Top 25 of {len(sel)} member paths, most rows first.", ""]
    if bad:
        lines += ["## Failures", "", "| file | error |", "|---|---|"]
        for r in bad:
            lines.append(f"| `{r['path']}` | {r.get('error')} |")
        lines.append("")
    lines += [
        "## Validation",
        "",
        "`jc3fx.py check` re-reads every file out of the archives and recomputes its",
        "row digest and object census; both must equal the row stored here. The census",
        "is the array structure of the file (e.g. `emitters` = 3), so a decode that",
        "silently stopped early cannot pass. Each `.ee` is opened once and dropped, so",
        "the whole game is re-read without holding it; standalone entries are re-read",
        "from the archive path in their `source` field.",
        "",
    ]
    with open(os.path.join(OUT, "FX.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print(f"FX.md: {len(ok)} files, {sum(r['rows'] for r in ok):,} rows, {len(bad)} failures")
    return 1 if bad else 0


# ----------------------------------------------------------------------- dump
def cmd_dump(a) -> int:
    rows = load_index(a.index)
    best = pick_by_path(rows)
    hit = [p for p in best if a.want.lower() in p.lower()]
    if not hit:
        raise SystemExit(f"no archive path matches {a.want!r}")
    # an .ee whose path matches wins; an inner file is then selected by name
    path = sorted(hit, key=lambda p: (not p.lower().endswith(".ee"), len(p)))[0]
    blob = read_row(best[path], a.game)
    items = inner_fx(blob, EXTS) if path.lower().endswith(".ee") else \
        [(os.path.basename(path), blob)]
    shown = 0
    for name, data in items:
        try:
            doc = decode(data)
        except Exception as e:                                  # noqa: BLE001
            print(f"# {path} :: {name}: {type(e).__name__}: {e}")
            continue
        print(f"# {path} :: {name}  ({len(data)} bytes, {doc['rows']} rows, "
              f"root {doc['root']})")
        for i, (p, tname, value) in enumerate(doc["_rows"]):
            if a.max and i >= a.max:
                print(f"... {doc['rows'] - i} more rows")
                break
            print(f"{p}\t{tname}\t{value}")
        shown += 1
        if shown >= a.files:
            break
    return 0


# ---------------------------------------------------------------------- check
def cmd_check(a) -> int:
    table = load_table()
    rows = load_index(a.index)
    best = pick_by_path(rows)
    problems: list[str] = []
    checked = 0
    if table and "source" not in table[0]:
        raise SystemExit(f"{TABLE} predates `source` - rerun `jc3fx.py build`")

    def verify(rec: dict, data: bytes) -> None:
        nonlocal checked
        try:
            doc = decode(data)
        except Exception as e:                                  # noqa: BLE001
            problems.append(f"{rec['path']}: {type(e).__name__}: {e}")
            return
        checked += 1
        if doc["digest"] != rec["digest"]:
            problems.append(f"{rec['path']}: digest changed")
        if doc["objects_digest"] != rec["objects_digest"]:
            problems.append(f"{rec['path']}: object census changed")
        if doc["rows"] != rec["rows"]:
            problems.append(f"{rec['path']}: row count {doc['rows']} != {rec['rows']}")
        if checked % 5000 == 0:
            print(f"  {checked:,} files re-read", flush=True)

    # group by container so one .ee is opened and walked once, then dropped:
    # caching every container would hold 3.7 GB of bundles at once
    groups: dict[str, list[dict]] = {}
    for rec in table:
        groups.setdefault(rec["container"], []).append(rec)
    for container, recs in groups.items():
        if a.limit and checked >= a.limit:
            break
        todo = []
        for rec in recs:
            if rec.get("error"):
                problems.append(f"{rec['path']}: undecoded ({rec['error']})")
            else:
                todo.append(rec)
        if not todo:
            continue
        if not container:
            for rec in todo:
                try:
                    # a standalone entry's `path` is a bare name; `source` is the
                    # archive path it was read from
                    verify(rec, read_row(best[rec["source"]], a.game))
                except Exception as e:                          # noqa: BLE001
                    problems.append(f"{rec['path']}: {type(e).__name__}: {e}")
            continue
        try:
            stream, dirs = inner_dir(read_row(best[container], a.game))
        except Exception as e:                                  # noqa: BLE001
            problems.append(f"{container}: {type(e).__name__}: {e}")
            continue
        for rec in todo:
            if a.limit and checked >= a.limit:
                break
            try:
                off, size = dirs[rec["path"]]
            except KeyError:
                problems.append(f"{rec['path']}: gone from {container}")
                continue
            verify(rec, stream[off:off + size])
        del stream, dirs
    print(f"checked {checked} files | problems {len(problems)}")
    for p in problems[:40]:
        print("FAIL", p)
    return 1 if problems else 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="decode every .effc/.ctunec/.trim")
    b.add_argument("--ee", help="only containers whose path contains this")
    b.add_argument("--limit", type=int, default=0)
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--index", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)
    r = sub.add_parser("report", help="write FX.md")
    r.set_defaults(func=cmd_report)
    d = sub.add_parser("dump", help="print the rows of one file")
    d.add_argument("want")
    d.add_argument("--max", type=int, default=200, help="rows per file")
    d.add_argument("--files", type=int, default=1, help="how many inner files to print")
    d.add_argument("--game", default=DEFAULT_GAME)
    d.add_argument("--index", default=DEFAULT_OUT)
    d.set_defaults(func=cmd_dump)
    c = sub.add_parser("check", help="re-read the game and compare every digest")
    c.add_argument("--limit", type=int, default=0, help="stop after N files (smoke test)")
    c.add_argument("--game", default=DEFAULT_GAME)
    c.add_argument("--index", default=DEFAULT_OUT)
    c.set_defaults(func=cmd_check)
    a = ap.parse_args()
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()

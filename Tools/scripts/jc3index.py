"""jc3index.py - name every entry in the installed JC3 archives (GRB-G2-1).

The archives are addressed by hash: each `<name>.tab` is a flat list of
(name_hash u32, offset u32, size u32) records, and the game finds a file by
hashing its VFS path (Gibbed's Jenkins lookup3 over the ASCII path with
FORWARD slashes).  Gibbed ships the reverse mapping as text: one
`<name>.filelist` per archive under
`Tools/Gibbed/projects/<project>/files/<mount>/`, one VFS path per line.

Gibbed's filelists stop at the base game and a pre-patch snapshot: they contain
no DLC names at all (the `dlc*` directories hold placeholder filelists with a
`; 0/1 (0%)` comment). `Tools/JCMR-src/assets/jc3/dictionary.json` is a second,
independent name source that maps every VFS path to the archive(s) it lives in,
DLC included. Both sources are accepted only when `hash_jenkins(path)` is an
exact tab hash of the archive being named, so a name is proof, never a guess.

This script joins tab, filelists and dictionary and writes a single index, so
any path in the game resolves to (archive, offset, size) without guessing -
which is what every later GRAB step needs. Each row records where its name came
from (`source`).

Scanned trees (relative to the game root):
  archives_win64/*.tab          base game
  patch_win64/*.tab             patch (overrides base)
  dlc_win64/<dlc>/*.tab         owned DLC

Resolution order (highest first): patch, dlc, base.  The index keeps *every*
location a path has, because "which copy did the game load" is itself a
question this grab has to answer.

Usage:
  python jc3index.py build [--game DIR] [--gibbed DIR] [--dictionary FILE] [-o DIR]
  python jc3index.py resolve <path-or-prefix> [...]      # uses the built index
  python jc3index.py check
  python jc3index.py summary

Outputs (default `Research/JC3Grab/`):
  INDEX.jsonl   one object per named entry:
                {path, hash, archive, mount, offset, size, source}
  INDEX.json    counts, per-archive table, unnamed entries, verification

Read-only w.r.t. the game install; only writes under -o.
"""
from __future__ import annotations

import argparse
import json
import os
import struct
import sys
from typing import Iterable

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rbmhdr import hash_jenkins  # noqa: E402

DEFAULT_GAME = os.environ.get("JC3_GAME", r"D:/Games/Just Cause 3")
HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GIBBED = os.path.join(os.path.dirname(HERE), "Gibbed")
DEFAULT_DICTIONARY = os.path.join(os.path.dirname(HERE), "JCMR-src", "assets", "jc3",
                                   "dictionary.json")
DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "Research", "JC3Grab")
# Plain path lists whose names were *derived* rather than shipped in a filelist
# (see Tools/names/README.md).  Every line is hashed like any other path and only
# accepted where that archive's tab actually carries the hash.
DEFAULT_NAMES = os.path.join(os.path.dirname(HERE), "names")

MOUNT_RANK = {"patch": 2, "dlc": 1, "base": 0}


def mount_of(rel: str) -> str:
    """Classify an archive's path relative to the game root."""
    head = rel.split("/")[0].lower()
    if head.startswith("patch"):
        return "patch"
    if head.startswith("dlc"):
        return "dlc"
    return "base"


def read_tab(path: str) -> dict[int, tuple[int, int]]:
    """Parse a .tab into {name_hash: (offset, size)}."""
    with open(path, "rb") as f:
        blob = f.read()
    if blob[0:4] != b"TAB\0":
        raise SystemExit(f"not a TAB file: {path}")
    v1, v2 = struct.unpack_from("<HH", blob, 4)
    (align,) = struct.unpack_from("<I", blob, 8)
    if (v1, v2, align) != (2, 1, 0x800):
        raise SystemExit(f"unexpected TAB header {(v1, v2, align)} in {path}")
    entries: dict[int, tuple[int, int]] = {}
    o = 12
    while o + 12 <= len(blob):
        nh, off, size = struct.unpack_from("<III", blob, o)
        entries[nh] = (off, size)
        o += 12
    return entries


def scan_archives(game: str) -> list[dict]:
    """Every .tab in the install, with the game-root-relative key."""
    found: list[dict] = []
    roots = ("archives_win64", "patch_win64", "dlc_win64")
    for root in roots:
        base = os.path.join(game, root)
        if not os.path.isdir(base):
            continue
        # one level deep is enough for dlc_win64/<dlc>/game0.tab
        for dirpath, _dirnames, filenames in os.walk(base):
            depth = os.path.relpath(dirpath, game).count(os.sep)
            if depth > 2:
                _dirnames[:] = []
                continue
            for fn in filenames:
                if not fn.lower().endswith(".tab"):
                    continue
                tab = os.path.join(dirpath, fn)
                arc = tab[:-4] + ".arc"
                if not os.path.exists(arc):
                    continue
                rel = os.path.relpath(tab, game).replace("\\", "/")
                found.append({
                    "key": rel[:-4],
                    "rel": rel,
                    "tab": tab,
                    "arc": arc,
                    "stem": fn[:-4].lower(),
                    "mount": mount_of(rel),
                    "arc_size": os.path.getsize(arc),
                })
    found.sort(key=lambda a: (MOUNT_RANK[a["mount"]], a["key"]))
    return found


def find_filelists(gibbed: str) -> list[dict]:
    """Every *.filelist under Tools/Gibbed/projects/*/files/*/."""
    out: list[dict] = []
    proj = os.path.join(gibbed, "projects")
    if not os.path.isdir(proj):
        return out
    for project in sorted(os.listdir(proj)):
        files = os.path.join(proj, project, "files")
        if not os.path.isdir(files):
            continue
        for dirpath, _dirnames, filenames in os.walk(files):
            for fn in filenames:
                if not fn.lower().endswith(".filelist"):
                    continue
                mount_dir = os.path.basename(dirpath).lower()
                out.append({
                    "path": os.path.join(dirpath, fn),
                    "project": project,
                    "mount_dir": mount_dir,
                    "stem": fn[: -len(".filelist")].lower(),
                })
    out.sort(key=lambda f: (f["project"], f["mount_dir"], f["stem"]))
    return out


def read_paths(path: str) -> Iterable[str]:
    """VFS paths from a filelist, normalized to forward slashes.

    Gibbed's filelists carry a `; <hit>/<total> (<pct>%)` trailer line; it is a
    comment, not a path, and taking it as one produced 63 phantom "unresolved"
    entries whose hashes exist in no archive because they are not content at all.
    """
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            p = line.strip().replace("\\", "/")
            if not p or p[0] in "#;":
                continue
            yield p


def find_extra_names(root: str) -> list[str]:
    """Every plain path list under `root` (any depth, *.filelist / *.names / *.txt)."""
    out: list[str] = []
    if not root or not os.path.isdir(root):
        return out
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in sorted(filenames):
            if fn.lower().endswith((".filelist", ".names", ".txt")):
                out.append(os.path.join(dirpath, fn))
    return out


def pick_archives(archives: list[dict], fl: dict) -> list[dict]:
    """Which archives a filelist describes.

    Exact match on `<mount>/<stem>` first; a filelist under a flat `dlc/` or
    `dlc_win64/` mount matches every dlc archive with the same stem.
    """
    stem = fl["stem"]
    exact = [a for a in archives
             if a["key"].lower() == f"{fl['mount_dir']}/{stem}"]
    if exact:
        return exact
    if fl["mount_dir"].startswith("dlc"):
        return [a for a in archives if a["mount"] == "dlc" and a["stem"] == stem]
    return [a for a in archives if a["mount"] == mount_of(fl["mount_dir"])
            and a["key"].lower().split("/")[0] == fl["mount_dir"]
            and a["stem"] == stem]


def cmd_build(a: argparse.Namespace) -> int:
    archives = scan_archives(a.game)
    if not archives:
        raise SystemExit(f"no .tab/.arc pairs under {a.game}")
    tabs = {arc["key"]: read_tab(arc["tab"]) for arc in archives}
    print(f"archives: {len(archives)}  entries: {sum(len(t) for t in tabs.values())}")

    filelists = find_filelists(a.gibbed)
    print(f"filelists: {len(filelists)}")

    rows: list[dict] = []            # named entries
    named_in_archive: dict[str, set[int]] = {k: set() for k in tabs}
    unresolved: list[dict] = []      # filelist paths with no entry (unowned DLC etc.)
    per_archive: dict[str, dict] = {
        arc["key"]: {"mount": arc["mount"], "tab": arc["tab"], "entries": len(tabs[arc["key"]]),
                     "arc_size": arc["arc_size"], "named": 0, "filelist_paths": 0}
        for arc in archives
    }

    for fl in filelists:
        targets = pick_archives(archives, fl)
        if not targets:
            continue
        paths = list(read_paths(fl["path"]))
        for arc in targets:
            per_archive[arc["key"]]["filelist_paths"] += len(paths)
        hit = 0
        for p in paths:
            h = hash_jenkins(p.encode("ascii", "replace"))
            for arc in targets:
                ent = tabs[arc["key"]].get(h)
                if ent is None:
                    continue
                off, size = ent
                rows.append({
                    "path": p,
                    "hash": f"{h:08X}",
                    "archive": arc["key"],
                    "mount": arc["mount"],
                    "offset": off,
                    "size": size,
                    "source": "gibbed-filelist",
                })
                named_in_archive[arc["key"]].add(h)
                hit += 1
        if not hit:
            unresolved.extend({"archive": arc["key"], "path": p}
                              for arc in targets for p in paths)
        elif hit < len(paths) * len(targets):
            known = {r["path"] for r in rows}
            unresolved.extend({"archive": arc["key"], "path": p}
                              for arc in targets for p in paths if p not in known)

    # Second name source: JCMR's dictionary, which is the only file that names
    # DLC content.  A path is accepted only when its hash is an exact tab hash of
    # the archive the dictionary says it belongs to, so this cannot invent a name.
    dictionary_rows = 0
    if a.dictionary and os.path.isfile(a.dictionary):
        with open(a.dictionary, "r", encoding="utf-8") as f:
            dictionary = json.load(f)
        for p, archives_of_path in dictionary.items():
            p = p.replace("\\", "/")
            h = hash_jenkins(p.encode("ascii", "replace"))
            for key in archives_of_path:
                key = key.replace("\\", "/")
                if key not in tabs or h not in tabs[key] or h in named_in_archive[key]:
                    continue
                off, size = tabs[key][h]
                rows.append({
                    "path": p,
                    "hash": f"{h:08X}",
                    "archive": key,
                    "mount": mount_of(key),
                    "offset": off,
                    "size": size,
                    "source": "jcmr-dictionary",
                })
                named_in_archive[key].add(h)
                dictionary_rows += 1
        print(f"dictionary: {a.dictionary} -> {dictionary_rows} extra named entries")

    # Third name source: derived lists (Tools/names).  A path is accepted for an
    # archive only when its own hash is a tab record there, so a wrong guess
    # cannot enter the index - but the *origin* is a hash search, not a filelist,
    # and the rows say so.
    extra_rows = 0
    extra_files = find_extra_names(getattr(a, "extra_names", DEFAULT_NAMES))
    if extra_files:
        already = {r["path"] for r in rows}
        for path in extra_files:
            for p in read_paths(path):
                if p in already:
                    continue
                h = hash_jenkins(p.encode("ascii", "replace"))
                took = False
                for key, tab in tabs.items():
                    if h not in tab or h in named_in_archive[key]:
                        continue
                    off, size = tab[h]
                    rows.append({
                        "path": p,
                        "hash": f"{h:08X}",
                        "archive": key,
                        "mount": mount_of(key),
                        "offset": off,
                        "size": size,
                        "source": "derived-names",
                    })
                    named_in_archive[key].add(h)
                    extra_rows += 1
                    took = True
                if took:
                    already.add(p)
        print(f"derived names: {len(extra_files)} files -> {extra_rows} named entries")

    for key, named in named_in_archive.items():
        per_archive[key]["named"] = len(named)

    unnamed = {k: sorted(set(tabs[k]) - named_in_archive[k]) for k in tabs}
    unnamed_total = sum(len(v) for v in unnamed.values())

    # Characterise the gap: what are the entries we cannot name?  Four magic bytes
    # each says whether the unreachable bytes are textures, models or code.
    unnamed_magic: dict[str, dict[str, int]] = {}
    for key, hashes in unnamed.items():
        if not hashes:
            continue
        arc_path = os.path.join(a.game, key + ".arc")
        census: dict[str, int] = {}
        for h in hashes:
            tag = magic_of(arc_path, tabs[key][h][0])
            census[tag] = census.get(tag, 0) + 1
        unnamed_magic[key] = dict(sorted(census.items(), key=lambda kv: -kv[1])[:8])

    rows.sort(key=lambda r: (r["path"], MOUNT_RANK[r["mount"]], r["archive"]))
    os.makedirs(a.out, exist_ok=True)
    jsonl = os.path.join(a.out, "INDEX.jsonl")
    with open(jsonl, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":")) + "\n")

    summary = {
        "_comment": [
            "JC3 archive index: every named entry in the installed game as",
            "(path, hash, archive, offset, size).  Generated by jc3index.py; do not hand-edit.",
            "A path may appear more than once; the game loads the highest-ranked copy:",
            "patch > dlc > base (MOUNT_RANK in jc3index.py).",
            "Anonymous entries are tab records whose hash is not in any Gibbed filelist:",
            "they exist in the archives and cannot be addressed by path yet.",
        ],
        "game": a.game.replace("\\", "/"),
        "gibbed": a.gibbed.replace("\\", "/"),
        "archives": len(archives),
        "tab_entries": sum(len(t) for t in tabs.values()),
        "named_rows": len(rows),
        "unique_paths": len({r["path"] for r in rows}),
        "named_by_source": {
            s: sum(1 for r in rows if r["source"] == s)
            for s in sorted({r["source"] for r in rows})
        },
        "dictionary": a.dictionary.replace("\\", "/") if a.dictionary else None,
        "unnamed_entries": unnamed_total,
        "unresolved_filelist_paths": len(unresolved),
        "per_archive": per_archive,
        "unnamed_sample_sizes": {
            k: [tabs[k][h][1] for h in v[:8]] for k, v in unnamed.items() if v
        },
        "unnamed_magic": unnamed_magic,
        "by_extension": {},
    }
    ext: dict[str, int] = {}
    for r in rows:
        e = os.path.splitext(r["path"])[1].lower() or "(none)"
        ext[e] = ext.get(e, 0) + 1
    summary["by_extension"] = dict(sorted(ext.items(), key=lambda kv: -kv[1])[:40])

    with open(os.path.join(a.out, "INDEX.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(summary, f, indent=1)
        f.write("\n")

    print(f"named rows: {len(rows)}  unique paths: {summary['unique_paths']}")
    print(f"unnamed tab entries: {unnamed_total}  unresolved filelist paths: {len(unresolved)}")
    print(f"-> {jsonl}")
    return cmd_check(argparse.Namespace(out=a.out, game=a.game))


def magic_of(arc: str, offset: int) -> str:
    """First four bytes of an archive entry, as a printable tag."""
    try:
        with open(arc, "rb") as f:
            f.seek(offset)
            b = f.read(4)
    except OSError:
        return "err"
    if all(32 <= c < 127 for c in b):
        return b.decode("ascii")
    return b.hex().upper()


def cmd_extract(a: argparse.Namespace) -> int:
    """Write one indexed file out, preferring patch > dlc > base."""
    rows = [r for r in load_index(a.out) if r["path"].lower() == a.path.lower().replace("\\", "/")]
    if not rows:
        raise SystemExit(f"not in index: {a.path}")
    r = sorted(rows, key=lambda r: MOUNT_RANK[r["mount"]])[-1]
    arc = os.path.join(a.game, r["archive"] + ".arc")
    with open(arc, "rb") as f:
        f.seek(r["offset"])
        data = f.read(r["size"])
    if len(data) != r["size"]:
        raise SystemExit(f"short read {len(data)} != {r['size']}")
    with open(a.o, "wb") as f:
        f.write(data)
    print(f"{r['path']} <- {r['archive']}+{r['offset']} {len(data)} B magic {data[:4]!r} -> {a.o}")
    return 0


def load_index(out: str) -> list[dict]:
    p = os.path.join(out, "INDEX.jsonl")
    if not os.path.exists(p):
        raise SystemExit(f"no index at {p} - run `jc3index.py build` first")
    rows = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def cmd_resolve(a: argparse.Namespace) -> int:
    rows = load_index(a.out)
    for q in a.query:
        ql = q.replace("\\", "/").lower()
        hits = [r for r in rows if r["path"].lower() == ql]
        if not hits:
            hits = [r for r in rows if r["path"].lower().startswith(ql)]
        if not hits:
            print(f"{q}: NOT IN INDEX")
            continue
        for r in hits[:a.limit]:
            print(f"{r['path']}  {r['archive']}  off={r['offset']} size={r['size']}")
        if len(hits) > a.limit:
            print(f"  ... {len(hits) - a.limit} more")
    return 0


def cmd_check(a: argparse.Namespace) -> int:
    rows = load_index(a.out)
    with open(os.path.join(a.out, "INDEX.json"), encoding="utf-8") as f:
        summary = json.load(f)
    problems = []
    if summary["named_rows"] != len(rows):
        problems.append(f"row count {len(rows)} != summary {summary['named_rows']}")

    # Every name must still hash to its entry: re-hash a sample of each source and
    # check the DLC archives, which are the ones the filelists never named.
    by_source: dict[str, int] = {}
    for r in rows:
        by_source[r.get("source", "(none)")] = by_source.get(r.get("source", "(none)"), 0) + 1
    for src, n in by_source.items():
        if src != "(none)" and summary.get("named_by_source", {}).get(src) != n:
            problems.append(f"source {src}: {n} rows != summary")
    dlc = {k: v for k, v in summary["per_archive"].items() if v["mount"] == "dlc"}
    dlc_entries = sum(v["entries"] for v in dlc.values())
    dlc_named = sum(v["named"] for v in dlc.values())
    if dlc_entries and dlc_named != dlc_entries:
        problems.append(f"DLC named {dlc_named}/{dlc_entries}")
    step = max(1, len(rows) // 500)
    for r in rows[::step]:
        if hash_jenkins(r["path"].encode("ascii", "replace")) != int(r["hash"], 16):
            problems.append(f"hash mismatch for {r['path']}")
            break

    # byte check: the base vehicle entity really is an AAF container
    probe = ("editor/entities/jc_vehicles/01_land/"
             "v0300_car_kensington_sportsmuscle/"
             "v0300_car_kensington_sportsmuscle_civilian_01.ee")
    hit = [r for r in rows if r["path"] == probe]
    if not hit:
        problems.append(f"probe path missing: {probe}")
    else:
        r = sorted(hit, key=lambda r: MOUNT_RANK[r["mount"]])[0]
        arc = os.path.join(a.game, r["archive"] + ".arc")
        with open(arc, "rb") as f:
            f.seek(r["offset"])
            head = f.read(8)
        if head[:4] != b"AAF\0":
            problems.append(f"probe magic {head[:4]!r} at {r['archive']}+{r['offset']}")
        else:
            print(f"probe ok: {probe} -> {r['archive']}+{r['offset']} {head!r}")

    if problems:
        for p in problems:
            print("FAIL", p)
        return 1
    print(f"check ok: {len(rows)} rows, {summary['unique_paths']} paths, "
          f"{summary['unnamed_entries']} unnamed entries, "
          f"DLC {dlc_named}/{dlc_entries} named, sources {by_source}")
    return 0


def cmd_summary(a: argparse.Namespace) -> int:
    with open(os.path.join(a.out, "INDEX.json"), encoding="utf-8") as f:
        s = json.load(f)
    print(f"archives {s['archives']}  tab entries {s['tab_entries']}  "
          f"named {s['named_rows']} ({100 * s['named_rows'] / max(1, s['tab_entries']):.1f}%)")
    print("top extensions:", ", ".join(f"{k} {v}" for k, v in list(s["by_extension"].items())[:12]))
    rows = load_index(a.out)
    veh = [r for r in rows if "/jc_vehicles/" in r["path"]]
    ee = [r for r in veh if r["path"].endswith(".ee")]
    print(f"vehicle entries {len(veh)}  .ee {len(ee)}  "
          f"entities {len({r['path'].rsplit('/',1)[0] for r in ee})}")
    for key, v in s["per_archive"].items():
        if v["named"] < v["entries"]:
            print(f"  {key}: {v['named']}/{v['entries']} named")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="scan archives + filelists, write the index")
    b.add_argument("--game", default=DEFAULT_GAME)
    b.add_argument("--gibbed", default=DEFAULT_GIBBED)
    b.add_argument("--dictionary", default=DEFAULT_DICTIONARY,
                   help="extra path -> archives name source (JCMR dictionary.json)")
    b.add_argument("--extra-names", default=DEFAULT_NAMES,
                   help="directory of plain path lists whose names were derived (Tools/names)")
    b.add_argument("-o", "--out", default=DEFAULT_OUT)
    b.set_defaults(func=cmd_build)

    r = sub.add_parser("resolve", help="look up paths (exact, else prefix)")
    r.add_argument("query", nargs="+")
    r.add_argument("--limit", type=int, default=40)
    r.add_argument("-o", "--out", default=DEFAULT_OUT)
    r.set_defaults(func=cmd_resolve)

    e = sub.add_parser("extract", help="write one indexed file out (patch > dlc > base)")
    e.add_argument("path")
    e.add_argument("-o", "--out-file", dest="o", required=True)
    e.add_argument("--game", default=DEFAULT_GAME)
    e.add_argument("--index-dir", dest="out", default=DEFAULT_OUT)
    e.set_defaults(func=cmd_extract)

    c = sub.add_parser("check", help="verify the index against the archives")
    c.add_argument("--game", default=DEFAULT_GAME)
    c.add_argument("-o", "--out", default=DEFAULT_OUT)
    c.set_defaults(func=cmd_check)

    s = sub.add_parser("summary", help="print index statistics")
    s.add_argument("-o", "--out", default=DEFAULT_OUT)
    s.set_defaults(func=cmd_summary)

    a = ap.parse_args()
    if not hasattr(a, "game"):
        a.game = DEFAULT_GAME
    sys.exit(a.func(a))


if __name__ == "__main__":
    main()

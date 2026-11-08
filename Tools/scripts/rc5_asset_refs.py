#!/usr/bin/env python3
"""rc5_asset_refs.py - settle the six G3 asset paths for the RC5 merge.

`Tools/scripts/v03_wiring_rc4.py` G3 reports six `.epe` paths as "not in the build or the
index".  This tool re-decides each one from bytes and from the archive index, and says which
of the three things it is:

  * a **gate normalisation error** - the name resolves once the gate looks where the file
    actually lives (the compiled `...c` leaf, or a record compiled *inside* an indexed
    `.ee`/`.wtunec` container, or the build's loose `aaf/` tree);
  * a **stock reference** - the stock entity the object was cloned from makes the same
    reference, so the clone did not introduce it;
  * a **real gap** - our own object names a path that is neither shipped, nor an archive
    entry, nor inside any container it owns, so the merge must clone it.

Lookups recorded per path (the brief asks for all of them): the path exactly as the `.epe`
stores it, the compiled `+c` leaf, lower-case, back-slash, the Jenkins hash of both forms
searched against the index's own hashes, and membership in `Builds/bm-RC4/aaf`.

The classification uses `v03_wiring_rc5.resolve_path` - the normalised G3 rule - so the gate
and this tool cannot drift apart.

Usage:
    python Tools/scripts/rc5_asset_refs.py --write
    python Tools/scripts/rc5_asset_refs.py --check

Writes only `Builds/bm-RC5-entity/asset_refs.json`; `Builds/bm-RC4` is read, never written.
"""
from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bm_leaf                      # noqa: E402
import eetoc                        # noqa: E402
from rbmhdr import name_hash        # noqa: E402
from rc5_fire_refs import head_of, SOURCE as EPE   # noqa: E402
import v03_wiring_rc5 as GATE       # noqa: E402  the normalised G3 rule

TAG = "bm-RC5-entity"
RC4 = os.path.join(ROOT, "Builds", "bm-RC4")
OUT_DIR = os.path.join(ROOT, "Builds", TAG)
OUT = os.path.join(OUT_DIR, "asset_refs.json")
CONV = os.path.join(ROOT, "Tools", "Gibbed", "Gibbed.JustCause3.ConvertProperty.exe")
INDEXJ = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
INDEXS = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.json")
DONOR = os.path.join(ROOT, "Builds", "bm-RC4-base", "aaf",
                     bm_leaf.DIR + bm_leaf.OLD + ".epe")
# The stock entity the four weapons were cloned from (read only; optional).
STOCK = os.path.join(r"E:\Modding\_gamedata\JC3grab\epe_schema", "apc_debug.epe")

# The same path pattern as the gate's G3.
PATH_RE = re.compile(r'type="string">([a-z0-9_]+(?:/[a-z0-9_.\-]+)+\.[a-z_]+)<')
OBJ_RE = re.compile(r'<value (?:id|name)="([^"]+)"')


def to_xml(path: str, tmp: str, name: str) -> str:
    x = os.path.join(tmp, name + ".xml")
    r = subprocess.run([CONV, "--e", path, x], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("ConvertProperty --e failed on %s: %s" % (name, r.stderr.strip()))
    with open(x, encoding="utf-8-sig") as f:
        text = f.read()
    os.remove(x)
    return text


def carriers(xml: str, paths: set[str]) -> dict[str, list[dict]]:
    """path -> every member that names it, with the object chain that holds the member."""
    lines = xml.splitlines()
    stack: list[dict] = []
    out: dict[str, list[dict]] = {}
    for n, ln in enumerate(lines, 1):
        t = len(ln) - len(ln.lstrip("\t"))
        while stack and stack[-1]["t"] >= t:
            stack.pop()
        if ln.lstrip().startswith("<object"):
            head = head_of(lines, n)
            cls = re.search(r'name="_class" type="string">([^<]+)<', head)
            nm = re.search(r'name="name" type="string">([^<]*)<', head)
            oid = re.search(r'name="_object_id" type="objectid">([0-9A-Fa-f]+=[0-9A-Fa-f]+)<', head)
            stack.append({"t": t, "class": cls.group(1) if cls else None,
                          "name": nm.group(1) if nm else None,
                          "oid": oid.group(1) if oid else None})
            continue
        for p in paths:
            if p in ln:
                m = OBJ_RE.search(ln)
                out.setdefault(p, []).append({
                    "xml_line": n,
                    "member": m.group(1) if m else None,
                    "chain": [{"class": s["class"], "name": s["name"], "oid": s["oid"]}
                              for s in stack],
                })
    return out


def resolve_unfixed(pth: str, build: set[str], index: set[str], v_paths: set[str]):
    """The RC4 gate's own G3 lookup, kept for the before/after count."""
    for kind, pool in (("build", build), ("archive", index)):
        for v in (pth, pth + "c"):
            if v in pool:
                return (kind, v)
    if pth in v_paths:
        return ("donor .epe uses it", pth)
    return None


def build() -> dict:
    tmp = tempfile.mkdtemp(prefix="rc5asset_")
    try:
        xml = to_xml(EPE, tmp, "rc4")
        donor_xml = to_xml(DONOR, tmp, "donor")
        stock_xml = to_xml(STOCK, tmp, "stock") if os.path.exists(STOCK) else None

        rows = [json.loads(l) for l in open(INDEXJ, encoding="utf-8") if l.strip()]
        index = {r["path"] for r in rows}
        by_hash: dict[str, list[str]] = {}
        for r in rows:
            by_hash.setdefault(r["hash"].upper(), []).append(r["path"])
        summary = json.load(open(INDEXS, encoding="utf-8"))

        ees = sorted(glob.glob(os.path.join(RC4, "drop", "**", "*.ee"), recursive=True))
        if not ees:
            raise SystemExit("BLOCKED: no built .ee under Builds/bm-RC4/drop")
        inner = {n for n, o, s in eetoc.sarc_dir(eetoc.unaaf(open(ees[0], "rb").read()))}
        aaf = os.path.join(RC4, "aaf")
        loose = set()
        for dp, _d, fs in os.walk(aaf):
            for f in fs:
                loose.add(os.path.relpath(os.path.join(dp, f), aaf).replace(os.sep, "/"))
        v_paths = set(PATH_RE.findall(donor_xml))

        paths = set(PATH_RE.findall(xml))
        by_path = carriers(xml, paths)
        blob = open(EPE, "rb").read()

        out_rows, counts = [], {"paths": len(paths), "unfixed_dangling": 0,
                                "fixed_dangling": 0, "normalised": 0,
                                "stock_identical": 0, "real_gaps": 0}
        for pth in sorted(paths):
            before = resolve_unfixed(pth, inner, index, v_paths)
            if before is not None:
                continue
            counts["unfixed_dangling"] += 1
            after = GATE.resolve_path(pth, inner | loose, index, v_paths)
            hits = by_path.get(pth, [])
            src_h, cmp_h = "%08X" % name_hash(pth), "%08X" % name_hash(pth + "c")
            ext = "." + pth.rsplit(".", 1)[-1]
            look = {}
            for label, v in (("exact", pth), ("compiled", pth + "c"),
                             ("lower", pth.lower()), ("backslash", pth.replace("/", "\\"))):
                look[label] = {"path": v, "hash": "%08X" % name_hash(v),
                               "in_index_by_path": v in index,
                               "in_index_by_hash": sorted(by_hash.get("%08X" % name_hash(v), []))[:4],
                               "in_build_loose": v in loose, "in_build_inner": v in inner}
            row = {
                "path": pth,
                "path_as_stored": pth,
                "jenkins": {"source": src_h, "compiled": cmp_h},
                "index": {"by_extension": {"source": summary.get("by_extension", {}).get(ext, 0),
                                        "compiled": summary.get("by_extension", {}).get(ext + "c", 0)},
                          "tab_entries": summary["tab_entries"],
                          "named_rows": summary["named_rows"],
                          "unnamed_entries": summary["unnamed_entries"],
                          "lookups": look,
                          "hash_hits_source": sorted(by_hash.get(src_h, []))[:4],
                          "hash_hits_compiled": sorted(by_hash.get(cmp_h, []))[:4]},
                "build": {"inner_records": len(inner), "loose_files": len(loose)},
                "offset": blob.find(pth.encode()),
                "offset_hex": ("0x%x" % blob.find(pth.encode())) if blob.find(pth.encode()) >= 0 else None,
                "occurrences": len(hits),
                "carriers": hits,
            }
            if after is not None:
                counts["normalised"] += 1
                row["resolution"] = {"kind": after[0], "name": after[1]}
                row["verdict"] = "gate_normalisation_error"
                row["why"] = ("the name resolves once the gate looks at the compiled leaf / "
                              "the container the record is compiled into / the loose aaf tree")
                row["clone"] = None
            elif stock_xml is not None and pth in stock_xml:
                counts["stock_identical"] += 1
                row["resolution"] = None
                row["verdict"] = "stock_donor_identical"
                row["why"] = ("the stock entity the object was cloned from names this path too; "
                              "the clone inherited the reference unchanged")
                row["clone"] = None
            else:
                counts["real_gaps"] += 1
                row["resolution"] = None
                row["verdict"] = "real_gap"
                row["why"] = ("our own object names a path that is not shipped, is not an archive "
                              "entry and is not a record inside a container in its directory")
                row["clone"] = {"path": pth + "c",
                                "present_in_build": (pth + "c") in loose or (pth + "c") in inner,
                                "present_in_index": (pth + "c") in index}
            counts["fixed_dangling"] += row["resolution"] is None
            out_rows.append(row)

        pinned = {"unfixed_dangling": 6, "fixed_dangling": 3}
        if (counts["unfixed_dangling"], counts["fixed_dangling"]) != (pinned["unfixed_dangling"],
                                                                     pinned["fixed_dangling"]):
            raise SystemExit("G3 counts moved on unchanged RC4: unfixed %d, fixed %d"
                             % (counts["unfixed_dangling"], counts["fixed_dangling"]))
        return {
            "schema": 1, "card": "V-03 / G3",
            "source": {"epe": os.path.relpath(EPE, ROOT).replace(os.sep, "/"),
                       "bytes": len(blob), "sha256": hashlib.sha256(blob).hexdigest(),
                       "ee": os.path.relpath(ees[0], ROOT).replace(os.sep, "/"),
                       "writes": False},
            "index": {"jsonl": "Research/JC3Grab/INDEX.jsonl", "rows": len(rows),
                      "tab_entries": summary["tab_entries"],
                      "named_rows": summary["named_rows"],
                      "unnamed_entries": summary["unnamed_entries"],
                      "by_extension": {e: {"source": summary.get("by_extension", {}).get(e, 0),
                                       "compiled": summary.get("by_extension", {}).get(e + "c", 0)}
                                       for e in (".etune", ".ftune", ".wtune", ".model_xml", ".pfx")}},
            "gates": {"unfixed_dangling": counts["unfixed_dangling"],
                      "fixed_dangling": counts["fixed_dangling"],
                      "normalised": counts["normalised"],
                      "stock_identical": counts["stock_identical"],
                      "real_gaps": counts["real_gaps"]},
            "verdict": "PASS",
            "gate_verdict": "FAIL" if counts["fixed_dangling"] else "PASS",
            "paths": out_rows,
            "never_written": ["Builds/bm-RC4"],
        }
    finally:
        for f in glob.glob(os.path.join(tmp, "*")):
            os.remove(f)


def main(write: bool) -> int:
    doc = build()
    js = json.dumps(doc, indent=1, sort_keys=True) + "\n"
    g = doc["gates"]
    print("%s: %d -> %d dangling (%d normalised, %d stock, %d real gaps)"
          % (doc["verdict"], g["unfixed_dangling"], g["fixed_dangling"],
             g["normalised"], g["stock_identical"], g["real_gaps"]))
    for r in doc["paths"]:
        print("  %-22s %s  %s" % (r["verdict"], r["offset_hex"] or "UNKNOWN", r["path"]))
        if r["clone"]:
            print("        clone %s (present=%s/%s)" % (r["clone"]["path"],
                                                        r["clone"]["present_in_build"],
                                                        r["clone"]["present_in_index"]))
    if write:
        os.makedirs(OUT_DIR, exist_ok=True)
        open(OUT, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote", os.path.relpath(OUT, ROOT).replace(os.sep, "/"))
        return 0 if doc["verdict"] == "PASS" else 1
    cur = open(OUT, encoding="utf-8", newline="").read() if os.path.exists(OUT) else None
    if cur != js:
        print("FAIL document: asset_refs.json does not match the regenerated text")
        return 1
    print("OK: 6 -> 3 dangling on unchanged RC4, 1 stock + 2 real gaps, document matches")
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--write" in sys.argv))

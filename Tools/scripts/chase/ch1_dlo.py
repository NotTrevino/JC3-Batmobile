#!/usr/bin/env python3
"""ch1_dlo.py - class-default (DLO) reader with names resolved from the SDK offset table.

The G1 grab read the archetypes in the 15 `Playable_Batmobile*` packages. The *class*
defaults live in `BmGame.upk` / `Engine.upk` and were out of its scope: `Default__<Class>`
objects whose property tags carry no FName, only the native class offset. This script
maps that offset back to a field name using `Research/BatmobileGrab/BMSDK_OFFSETS.json`
(BmSDK-AK bindings; its note states the offsets are the same number space as the cooked
tag offsets), walking the DLO class's super chain so an inherited field still resolves.

    python Tools/scripts/chase/ch1_dlo.py dlo    <pkg.upk> <Default__X> [--want TEXT]
    python Tools/scripts/chase/ch1_dlo.py findoff <pkg.upk> <Class> <offset> [--dlo-only]
    python Tools/scripts/chase/ch1_dlo.py chain  <pkg.upk> <Default__X>

Read-only: game packages are opened, never written. Nothing is copied out of the game tree.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
SDK = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")


def sdk_table():
    d = json.load(open(SDK, encoding="utf-8"))
    tab = {}
    for cls, rec in d["classes"].items():
        tab[cls] = {}
        for p in rec.get("properties", []):
            tab[cls][p["offset"]] = p
    return d, tab


def sdk_structs():
    """struct name -> {member offset: member record}, from every class that declares one."""
    d = json.load(open(SDK, encoding="utf-8"))
    out = {}
    for rec in d["classes"].values():
        for name, srec in (rec.get("structs") or {}).items():
            m = out.setdefault(name, {})
            for mem in srec.get("members", []):
                m[mem["offset"]] = mem
    return out


def _pkg(path):
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(GAME, path)
    return Package(path)


def class_chain(pkg, dlo_index):
    """Names of the DLO's class and its supers, nearest first."""
    e = pkg.exports[dlo_index - 1]
    ci = e["class_index"]
    out = []
    for _ in range(24):
        if ci <= 0:
            if ci < 0:
                out.append(pkg.class_name(ci))
            break
        out.append(pkg.exports[ci - 1]["name"])
        ci = pkg.exports[ci - 1]["super_index"]
    return [c for c in out if c]


def resolve(tab, chain, offset):
    for cls in chain:
        if cls in tab and offset in tab[cls]:
            p = tab[cls][offset]
            return cls, p
    return None, None


def _walk(p, idx):
    tags, _end, _status = best_walk(p, p.data(idx))
    return tags


def _flatten(tags, prefix=""):
    for t in tags:
        if not isinstance(t, dict) or "_error" in t:
            continue
        name = t.get("name")
        if name:
            path = "%s.%s" % (prefix, name) if prefix else name
            yield path, t
            src = [t]
        else:
            yield None, t          # offset-only: the caller resolves it
            src = []
        for k in src:
            for j, it in enumerate(k.get("items") or []):
                if isinstance(it, list):
                    for x in _flatten(it, "%s[%d]" % (path, j)):
                        yield x


def value_of(t):
    for k in ("value", "float", "num", "bool", "str", "name"):
        if k in t:
            return t[k]
    if "bits" in t:
        return t["bits"]
    if "props" in t:
        return "struct<%d>" % len(t["props"])
    if "items" in t:
        return "array<%d>" % len(t["items"])
    return None


def find_dlo(p, name):
    for i, e in enumerate(p.exports, 1):
        if (p.object_path(i) or e["name"] or "").lower() == name.lower():
            return i
    for i, e in enumerate(p.exports, 1):
        if (p.object_path(i) or "").lower().endswith("." + name.lower()):
            return i
    return None


def cmd_struct(a):
    """Dump one serialised struct tag of a DLO, member names from the SDK struct table."""
    _d, tab = sdk_table()
    structs = sdk_structs()
    p = _pkg(a.package)
    i = find_dlo(p, a.name)
    if i is None:
        print("no export %r in %s" % (a.name, a.package))
        return 1
    chain = class_chain(p, i)
    off = int(a.offset, 0)
    for t in _walk(p, i):
        if not isinstance(t, dict) or (t.get("offset") or 0) != off:
            continue
        cls, pr = resolve(tab, chain, off)
        sname = (pr or {}).get("type")
        print("tag 0x%04X %s = %s : %d member(s)\n"
              % (off, ("%s.%s" % (cls, pr["name"])) if pr else "?", sname, len(t.get("props") or [])))
        members = structs.get(sname, {})
        for m in t.get("props") or []:
            mo = m.get("offset") or 0
            mm = members.get(mo)
            sub = m.get("props") or []
            subnames = []
            for s in sub:
                sno = s.get("offset") or 0
                # nested vectors/rotators carry no member names; label by index
                subnames.append("%s=%s" % (s.get("type", "?"), value_of(s)))
            val = value_of(m)
            if val is None and subnames:
                val = "{" + ", ".join(subnames) + "}"
            print("  %-44s (0x%04X) %-20s %s"
                  % (mm["name"] if mm else "?", mo, m.get("type", ""), val))
        return 0
    print("no tag at 0x%04X in %s" % (off, a.name))
    return 2


def cmd_chain(a):
    p = _pkg(a.package)
    i = find_dlo(p, a.name)
    if i is None:
        print("no export %r" % a.name)
        return 1
    print("%s -> %s" % (a.name, " -> ".join(class_chain(p, i))))
    return 0


def cmd_dlo(a):
    _d, tab = sdk_table()
    p = _pkg(a.package)
    i = find_dlo(p, a.name)
    if i is None:
        print("no export %r in %s" % (a.name, a.package))
        return 1
    chain = class_chain(p, i)
    e = p.exports[i - 1]
    print("%s  export[%d]  class=%s  size=%d  chain=%s"
          % (a.name, i, p.class_name(e["class_index"]), e["size"], " -> ".join(chain)))
    want = (a.want or "").lower()
    n = named = 0
    for path, t in _flatten(_walk(p, i)):
        off = t.get("offset") or 0
        if t.get("name"):
            label = "%s (0x%04X)" % (t["name"], off)
        else:
            cls, pr = resolve(tab, chain, off)
            label = "%s (0x%04X)" % ("%s.%s" % (cls, pr["name"]) if pr else "?", off)
        if want and want not in label.lower():
            continue
        n += 1
        if t.get("name") or resolve(tab, chain, off)[1]:
            named += 1
        print("  %-52s %-28s %s" % (label, t.get("type", ""), value_of(t)))
    print("%d tag(s) shown, %d named by the SDK table" % (n, named))
    return 0


def cmd_findoff(a):
    """Every Default__* DLO in the package whose chain contains <Class> and that carries
    a tag at <offset> - the decisive test for "no class default serialises this field"."""
    _d, tab = sdk_table()
    p = _pkg(a.package)
    off = int(a.offset, 0)
    seen = 0
    hits = 0
    for i, e in enumerate(p.exports, 1):
        nm = e["name"] or ""
        if not a.any and not nm.startswith("Default__"):
            continue
        chain = class_chain(p, i)
        if a.klass not in chain:
            continue
        seen += 1
        tags = _walk(p, i)
        hit = [t for t in _flatten(tags) if (t[1].get("offset") or 0) == off]
        hits += len(hit)
        for _path, t in hit:
            print("%-56s chain=%-26s 0x%04X = %s"
                  % (p.object_path(i), chain[0], off, value_of(t)))
    print("%d object(s) with %s in the chain, %d tag(s) at 0x%04X"
          % (seen, a.klass, hits, off))
    return 0


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("dlo")
    s.add_argument("package")
    s.add_argument("name")
    s.add_argument("--want")
    s.set_defaults(func=cmd_dlo)
    s = sub.add_parser("findoff")
    s.add_argument("package")
    s.add_argument("klass")
    s.add_argument("offset")
    s.add_argument("--any", action="store_true")
    s.set_defaults(func=cmd_findoff)
    s = sub.add_parser("struct")
    s.add_argument("package")
    s.add_argument("name")
    s.add_argument("offset")
    s.set_defaults(func=cmd_struct)
    s = sub.add_parser("chain")
    s.add_argument("package")
    s.add_argument("name")
    s.set_defaults(func=cmd_chain)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())

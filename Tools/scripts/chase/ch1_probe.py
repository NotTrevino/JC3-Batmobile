#!/usr/bin/env python3
"""ch1_probe.py - read-only probe for the G1 value chase (chase-01).

The G1 grab only read the 15 `Playable_Batmobile*` packages (+ BmGame/Startup). The chase
extends the *read* scope to any package under the cooked folder, never writing to it:

    python Tools/scripts/chase/ch1_probe.py names  <pkg.upk> [-g REGEX]
    python Tools/scripts/chase/ch1_probe.py census <pkg.upk>
    python Tools/scripts/chase/ch1_probe.py defaults <pkg.upk> [-g REGEX]
    python Tools/scripts/chase/ch1_probe.py fields <pkg.upk> <ObjectName> [--want F1,F2]
    python Tools/scripts/chase/ch1_probe.py scanfield <pkg.upk> <FieldName>

`names` greps the decoded FName table (cheap evidence that a class or field exists in the
package at all). `defaults` lists `Default__*` exports with their class. `fields` walks one
object's property tags and prints every field, with the value where the tag is simple.
`scanfield` walks every export looking for one field name - the honest way to say
"no object in this package serialises X".

Everything is decoded with the project reader (`Tools/scripts/upk_read.py`); nothing here
invents a value. Game files are opened read-only and nothing is copied out of the game tree.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from upk_read import Package, best_walk, walk_tags  # noqa: E402

GAME = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"


def _pkg(path):
    if not os.path.isabs(path) and not os.path.exists(path):
        path = os.path.join(GAME, path)
    return Package(path)


def cmd_names(a):
    p = _pkg(a.package)
    rx = re.compile(a.grep or ".", re.I)
    hits = [(i, n) for i, n in enumerate(p.names) if rx.search(n)]
    print("%s: %d names, %d exports, %d imports"
          % (os.path.basename(a.package), len(p.names), len(p.exports), len(p.imports)))
    for i, n in hits:
        print("  name[%d] %s" % (i, n))
    ex = [(i, e) for i, e in enumerate(p.exports, 1)
          if rx.search(e["name"] or "") or rx.search(p.object_path(i) or "")]
    for i, e in ex[:60]:
        print("  export[%d] %-50s class=%s size=%d"
              % (i, p.object_path(i), p.class_name(e["class_index"]), e["size"]))
    return 0


def cmd_census(a):
    p = _pkg(a.package)
    buckets = {}
    for i, e in enumerate(p.exports, 1):
        c = p.class_name(e["class_index"]) or "?"
        buckets.setdefault(c, []).append(i)
    print("%s: %d exports" % (os.path.basename(a.package), len(p.exports)))
    for c in sorted(buckets, key=lambda k: -len(buckets[k])):
        print("  %-34s %4d   e.g. %s" % (c, len(buckets[c]), p.exports[buckets[c][0] - 1]["name"]))
    return 0


def _walk(p, idx):
    try:
        tags, _end, _status = best_walk(p, p.data(idx))   # best_walk returns (tags, end, status)
        return tags
    except Exception as e:                       # keep the probe honest, not fatal
        return [{"_error": str(e)}]


def cmd_defaults(a):
    p = _pkg(a.package)
    rx = re.compile(a.grep or "Default__", re.I)
    for i, e in enumerate(p.exports, 1):
        path = p.object_path(i) or e["name"]
        if rx.search(path):
            print("export[%d] %-60s class=%-28s size=%d"
                  % (i, path, p.class_name(e["class_index"]), e["size"]))
    return 0


def _flatten(tags, prefix=""):
    for t in tags:
        if not isinstance(t, dict) or "_error" in t:
            continue
        name = t.get("name")
        if not name:
            # cooked DLO properties carry no FName: keep them, labelled by class offset
            off = t.get("offset") or 0
            name = "<0x%04X>" % off
            yield ("%s%s" % (prefix + "." if prefix else "", name)), t
            continue
        path = "%s.%s" % (prefix, name) if prefix else name
        yield path, t
        for k in ("props",):
            if isinstance(t.get(k), list):
                yield from _flatten(t[k], path)
        for j, it in enumerate(t.get("items") or []):
            if isinstance(it, list):
                yield from _flatten(it, "%s[%d]" % (path, j))
            elif isinstance(it, dict):
                yield from _flatten([it], "%s[%d]" % (path, j))


def _show(path, t):
    for k in ("value", "float", "num", "bool", "str", "name"):
        if k in t:
            v = t[k]
            extra = " (%s)" % t["ref_path"] if t.get("ref_path") else ""
            return "%s=%r%s" % (k, v, extra)
    if "bits" in t:
        return "bits=%s" % t["bits"]
    if "props" in t:
        return "struct<%d props>" % len(t["props"])
    if "items" in t:
        return "array<%d items>" % len(t["items"])
    return "type=%s off=%s (no scalar)" % (t.get("type"), t.get("offset"))


def find_path(p, want):
    """Export by object path (outer.name), then by bare name - paths matter for DLO fields."""
    for i, _e in enumerate(p.exports, 1):
        if (p.object_path(i) or "").lower() == want.lower():
            return i
    for i, _e in enumerate(p.exports, 1):
        if (p.object_path(i) or "").lower().endswith("." + want.lower()):
            return i
    return p.find(want)


def cmd_fields(a):
    p = _pkg(a.package)
    idx = find_path(p, a.object)
    if idx is None:
        print("no object named %r in %s" % (a.object, a.package))
        return 1
    want = [w.strip() for w in (a.want or "").split(",") if w.strip()]
    print("export[%d] %s  class=%s  size=%d"
          % (idx, p.object_path(idx), p.class_name(p.exports[idx - 1]["class_index"]),
             p.exports[idx - 1]["size"]))
    tags = _walk(p, idx)
    if tags and "_error" in tags[0]:
        print("walk error:", tags[0]["_error"])
        return 1
    n = 0
    for path, t in _flatten(tags):
        if want and not any(w.lower() in path.lower() for w in want):
            continue
        n += 1
        print("  %-56s %s" % (path, _show(path, t)))
    if not n:
        print("  raw payload: %s%s" % (p.data(idx)[:64].hex(), "..." if len(p.data(idx)) > 64 else ""))
    print("%d field(s) shown" % n)
    return 0


def cmd_scanpath(a):
    """Every export whose path matches the regex, with its decoded fields (or raw payload)."""
    p = _pkg(a.package)
    rx = re.compile(a.grep, re.I)
    hits = 0
    for i in range(1, len(p.exports) + 1):
        path = p.object_path(i) or p.exports[i - 1]["name"]
        if not rx.search(path):
            continue
        hits += 1
        e = p.exports[i - 1]
        print("export[%d] %-52s class=%-22s size=%d"
              % (i, path, p.class_name(e["class_index"]), e["size"]))
        tags = _walk(p, i)
        shown = 0
        for tp, t in _flatten(tags):
            print("    %-44s %s" % (tp, _show(tp, t)))
            shown += 1
        if not shown:
            d = p.data(i)
            print("    raw %s%s" % (d[:64].hex(), "..." if len(d) > 64 else ""))
    print("%d export(s) matched %r" % (hits, a.grep))
    return 0 if hits else 2


def cmd_scanfield(a):
    """Every export in the package that carries the named field, with the value."""
    p = _pkg(a.package)
    needle = a.field.lower()
    hits = 0
    for i, e in enumerate(p.exports, 1):
        if e["size"] < 8:
            continue
        try:
            tags = best_walk(p, p.data(i))
        except Exception:
            continue
        for path, t in _flatten(tags):
            if needle in path.lower():
                hits += 1
                print("%-52s %-44s %s"
                      % (p.object_path(i), path, _show(path, t)))
    print("%d field hit(s) for %r in %s" % (hits, a.field, os.path.basename(a.package)))
    return 0 if hits else 2


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("names")
    s.add_argument("package")
    s.add_argument("-g", "--grep")
    s.set_defaults(func=cmd_names)
    s = sub.add_parser("census")
    s.add_argument("package")
    s.set_defaults(func=cmd_census)
    s = sub.add_parser("defaults")
    s.add_argument("package")
    s.add_argument("-g", "--grep")
    s.set_defaults(func=cmd_defaults)
    s = sub.add_parser("fields")
    s.add_argument("package")
    s.add_argument("object")
    s.add_argument("--want")
    s.set_defaults(func=cmd_fields)
    s = sub.add_parser("scanpath")
    s.add_argument("package")
    s.add_argument("grep")
    s.set_defaults(func=cmd_scanpath)
    s = sub.add_parser("scanfield")
    s.add_argument("package")
    s.add_argument("field")
    s.set_defaults(func=cmd_scanfield)
    a = ap.parse_args()
    return a.func(a)


if __name__ == "__main__":
    sys.exit(main())

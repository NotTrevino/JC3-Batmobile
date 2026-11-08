"""bmsdk_offsets.py - index the BmSDK-AK class dump and name cooked offsets from it (G1-1).

`BmGame.upk` ships only part of each class: the vehicle packages were cooked against a build whose
classes carry fields the shipped script copy does not declare, so a layout walk over the upk cannot
reach those slots (`OFFSETS.md`, the 116 fields left undecided).

The BmSDK-AK project (Team-BmSDK, MIT) generates C# bindings *from the running game*: every
`UProperty` is emitted with the absolute object offset the engine linked it to (`Ptr + 944`), and
every `ScriptStruct` with `[StructLayout(LayoutKind.Explicit, Size = N)]` and each member's offset.
That is the same number space as the cooked `FPropertyTagBat2.Offset`, so it resolves a cooked field
by `(class, offset, type)` directly.

This tool parses the vendored `.g.cs` files (never the game's files), writes
`Research/BatmobileGrab/BMSDK_OFFSETS.json`, and `--report` lays the shipped upk declaration out
again to check the dump against it: one constant base, the same names, the same class extent. A
build mismatch shows up there as a size or a name delta.

A `BoolProperty` entry also carries its `mask`: consecutive bools share one 32-bit word (the cooked
tag stores the whole word as `bits`), so the offset alone does not say which flag was set - G1-17
reads `CastShadows` / `CastDynamicShadows` that way.

Usage:
    python Tools/scripts/bmsdk_offsets.py            # write BMSDK_OFFSETS.json
    python Tools/scripts/bmsdk_offsets.py --check    # fail if the index is stale
    python Tools/scripts/bmsdk_offsets.py --report   # class-by-class cross-check of the upk walk
"""
import argparse
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
VENDOR = os.path.join(ROOT, "Working", "vendor", "BmSDK")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.json")

REPO = "https://github.com/Team-BmSDK/BmSDK-AK"
BRANCH = "main-bm4"

PROP_KINDS = {
    "ByteProperty", "IntProperty", "BoolProperty", "FloatProperty", "ObjectProperty",
    "NameProperty", "StrProperty", "StringProperty", "ClassProperty", "ArrayProperty",
    "StructProperty", "VectorProperty", "RotatorProperty", "MapProperty", "GuidProperty",
    "ComponentProperty", "InterfaceProperty", "DelegateProperty",
}

# One documented property looks like:
#     /// <summary>
#     /// FloatProperty: HoldingBrakeTime
#     /// </summary>
#     public unsafe float HoldingBrakeTime
#     {
#         get { ... Ptr + 656); }
#         set { ... }
#     }
DOC = re.compile(r"///\s*<summary>\s*\n\s*///\s*(\w+):\s*([A-Za-z0-9_]+)\s*\n\s*///\s*</summary>")
MEMBER = re.compile(r"public\s+(?:unsafe\s+)?(?:partial\s+|readonly\s+)*[^\n=;{]*?\b([A-Za-z0-9_]+)\s*\n")
PTR = re.compile(r"Ptr\s*\+\s*(\d+)")
SIZE = re.compile(r"\(size = (\d+)\)")
STRUCT_ATTR = re.compile(r"\[StructLayout\(LayoutKind\.Explicit,\s*Size\s*=\s*(\d+)\)\]\s*\n\s*public partial record struct (\w+)")
CLASS_DOC = re.compile(r"///\s*(?:ABSTRACT\s+)?Class:\s*(\w+)")


def struct_body(text, start):
    """`text[start:]` up to the closing brace of the struct that starts at `start`."""
    open_at = text.find("{", start)
    if open_at < 0:
        return text[start:]
    depth = 0
    for i in range(open_at, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[start:i + 1]
    return text[start:]


def parse_file(path):
    text = open(path, encoding="utf-8-sig").read()
    ns = re.search(r"^namespace\s+([\w\.]+);", text, re.M)
    cls = CLASS_DOC.search(text)
    size = SIZE.search(text)
    out = {
        "file": os.path.basename(path),
        "namespace": ns.group(1) if ns else None,
        "class": cls.group(1) if cls else None,
        "size": int(size.group(1)) if size else None,
        "super": None,
        "properties": [],
        "structs": {},
    }
    if cls:
        m = re.search(re.escape(cls.group(1)) + r"\s*:\s*BmSDK\.[\w\.]+?\.(\w+)", text)
        if m:
            out["super"] = m.group(1)

    # The struct layout attribute both names the struct and gives its runtime size; parse each
    # struct body up to the next struct attribute or the end of the class.
    struct_spans = []
    for m in STRUCT_ATTR.finditer(text):
        struct_spans.append((m.start(), int(m.group(1)), m.group(2)))
    for start, ssize, sname in struct_spans:
        body = struct_body(text, start)
        members = []
        docs = list(DOC.finditer(body))
        for i, d in enumerate(docs):
            kind, name = d.group(1), d.group(2)
            if kind not in PROP_KINDS:
                continue
            tail = body[d.end():docs[i + 1].start() if i + 1 < len(docs) else len(body)]
            mem = MEMBER.search(tail)
            off = PTR.search(tail)
            if mem and off:
                m = {"offset": int(off.group(1)), "name": name,
                     "member": mem.group(1), "kind": kind}
                if kind == "BoolProperty":
                    # consecutive bools share one 32-bit word; the getter carries the bit mask
                    # (`(Ptr + 544) & 16) != 0`), which is what tells the members apart.
                    bit = re.search(r"Ptr \+ \d+\) & (\d+)\)", tail)
                    if bit:
                        m["mask"] = int(bit.group(1))
                members.append(m)
            members.sort(key=lambda x: (x["offset"], x["name"]))
        out["structs"][sname] = {"size": ssize, "members": members}

    # Class-level properties: documented entries with a `Ptr + N` outside any struct body.
    span = text
    if struct_spans:
        keep = []
        pos = 0
        for start, _size, _name in struct_spans:
            keep.append(text[pos:start])
            pos = start + len(struct_body(text, start))
        keep.append(text[pos:])
        span = "".join(keep)
    docs = list(DOC.finditer(span))
    for i, d in enumerate(docs):
        kind, name = d.group(1), d.group(2)
        if kind not in PROP_KINDS:
            continue
        tail = span[d.end():docs[i + 1].start() if i + 1 < len(docs) else len(span)]
        mem = MEMBER.search(tail)
        off = PTR.search(tail)
        if mem and off:
            entry = {"offset": int(off.group(1)), "name": name, "member": mem.group(1),
                     "kind": kind}
            if kind == "BoolProperty":
                bit = re.search(r"Ptr \+ \d+\) & (\d+)\)", tail)
                if bit:
                    entry["mask"] = int(bit.group(1))
            decl = MEMBER.search(tail)
            if decl:
                # the declared type, last identifier: `BmSDK.Engine.AkEvent` -> `AkEvent`
                line = re.search(r"public\s+[^\n]*", tail).group(0)
                t = re.match(r"public\s+(?:unsafe\s+)?(?:ref\s+)?([\w\.<>]+)\s+\w+\s*$", line)
                if t:
                    entry["type"] = re.findall(r"[A-Za-z0-9_]+", t.group(1))[-1]
            struc = STRUCT_ATTR.search(tail)
            if kind == "StructProperty" and struc:
                entry["struct"] = struc.group(2)
            out["properties"].append(entry)
    out["properties"].sort(key=lambda x: (x["offset"], x["name"]))
    return out


def build():
    doc = {
        "schema": 1,
        "generated_by": "Tools/scripts/bmsdk_offsets.py",
        "source": {
            "repo": REPO,
            "branch": BRANCH,
            "license": "MIT",
            "note": "Generated C# bindings; each property carries the offset the engine linked it "
                    "to, so the offsets are the same number space as FPropertyTagBat2.Offset.",
        },
        "classes": {},
    }
    for path in sorted(glob.glob(os.path.join(VENDOR, "*.g.cs"))):
        cls = parse_file(path)
        if cls["class"]:
            doc["classes"][cls["class"]] = cls
    return doc


def lookup(doc, cls, offset, kind):
    """Find the SDK property at `offset` in `cls` (or an ancestor), with the same kind."""
    seen = set()
    while cls and cls not in seen:
        seen.add(cls)
        c = doc["classes"].get(cls)
        if not c:
            return None
        for p in c["properties"]:
            if p["offset"] == offset and same_kind(p["kind"], kind):
                return dict(p, owner=cls)
        cls = c.get("super")
    return None


TAG_KIND = {"ObjectNCRProperty": "ObjectProperty", "ObjectProperty": "ObjectProperty",
            "ClassProperty": "ObjectProperty", "ObjectPropertyNCR": "ObjectProperty",
            # the cooked tag stream calls a pointer slot ObjectNCRProperty whatever the class's
            # UProperty subclass is, so the UObjectProperty family has to collapse to one kind
            "ComponentProperty": "ObjectProperty", "InterfaceProperty": "ObjectProperty"}


def same_kind(a, b):
    a, b = TAG_KIND.get(a, a), TAG_KIND.get(b, b)
    if a == b:
        return True
    # A native Vector/Rotator/Guid is declared as a StructProperty of a native struct, but the
    # cooked tag names the slot by its value type.  Both spellings are the same 12/16-byte slot.
    native = {"VectorProperty", "RotatorProperty", "GuidProperty"}
    return (a in native and b == "StructProperty") or (b in native and a == "StructProperty")


def report(doc):
    """Independent check: does the upk's own class layout reproduce the dump?

    For every class in both, walk the shipped declaration and look for a single base offset at
    which the upk's property names equal the dump's.  A build mismatch would show as a class
    extent (walk + base) that differs from the dump's `(size = N)`; a wrong slot rule would show
    as names landing at more than one delta.
    """
    import bmak_layout as L
    import bmak_bind as B

    lay = L.Layout(overrides=B.TYPED)
    bad = 0
    for name in sorted(doc["classes"]):
        c = doc["classes"][name]
        cls = lay.find_class(name)
        if not cls:
            print("%-28s not in BmGame.upk (dump size %#06x)" % (name, c["size"]))
            continue
        rows, total = lay.layout(cls)
        want = {p["name"]: p["offset"] for p in c["properties"]}
        deltas = {}
        for r in rows:
            if r["name"] in want:
                d = want[r["name"]] - r["offset"]
                deltas[d] = deltas.get(d, 0) + 1
        if not deltas:
            continue
        d, hits = max(deltas.items(), key=lambda kv: kv[1])
        same_size = total + d == c["size"]
        print("%-28s base %#06x  %3d names agree  extent %#06x vs %#06x %s%s" % (
            name, d, hits, total + d, c["size"], "OK" if same_size else "MISMATCH",
            "" if len(deltas) == 1 else "  other deltas %s" %
            [hex(k) for k in deltas if k != d]))
        if not same_size:
            bad += 1
    if bad:
        print("\n%d class extent(s) disagree with the dump. Those are the classes where the shipped "
              "copy in BmGame.upk is not the linked class (extra or missing fields), or where a slot "
              "type is still unmodelled; the names come from the dump's absolute offsets either way "
              "- see REGISTRATION.md, 'The class dump: BmSDK-AK'." % bad)
    else:
        print("\nevery class extent matches the dump")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    doc = build()
    if a.check:
        if not os.path.exists(OUT):
            print("missing", OUT)
            return 1
        old = json.load(open(OUT, encoding="utf-8"))
        if old.get("classes") != doc["classes"]:
            print("BMSDK_OFFSETS.json is stale; re-run without --check")
            return 1
        print("ok: %d classes, %d properties, %d structs"
              % (len(doc["classes"]),
                 sum(len(c["properties"]) for c in doc["classes"].values()),
                 sum(len(c["structs"]) for c in doc["classes"].values())))
        return 0
    if a.report:
        return report(doc)
    json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1, sort_keys=True)
    open(OUT, "a", encoding="utf-8").write("\n")
    print("wrote %s: %d classes, %d properties, %d structs"
          % (OUT, len(doc["classes"]),
             sum(len(c["properties"]) for c in doc["classes"].values()),
             sum(len(c["structs"]) for c in doc["classes"].values())))
    return 0


if __name__ == "__main__":
    sys.exit(main())

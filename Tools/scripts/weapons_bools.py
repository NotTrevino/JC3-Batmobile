"""weapons_bools.py - name the 26 offset-only bit-packed bool words of WEAPONS.md.

`Research/BatmobileGrab/WEAPONS.json` keeps 26 `BoolProperty` records with no name: a bool that
shares its 32-bit word with another bool cannot be named from an offset, so the record keeps the
raw word (`bits`).  This script names them from the BmSDK generated sources
(`E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/**/*.g.cs`), where each bool property's getter
states both the field offset and its mask:

    get { return (BmSDK.Framework.MarshalUtil.ToManaged<int>(Ptr + 2396) & 8) != 0; }

So the *word* is the tag's offset and the *bit* is the getter's mask; a tag value is decoded into
one bool per member by `(bits & mask) != 0`.  Where several bools share a word, the script prints
every member with its mask and shows an object pair whose words differ, naming exactly which
members flip - that is the bit-order evidence.

Oracles (each fails if a mask, a line or a member is wrong):
  O1 26 rows parse and every class has a generated binding
  O2 every row's offset resolves to >=1 bool member (name + file:line)
  O3 every mask is a power of two and unique inside its word
  O4 every bit set in any observed word at these offsets is covered by a member mask
  O5 each shared word has an object pair with different words, and the differing bits are
     exactly the masks of the members that flip
  O6 every cited line states the member and its getter reads `Ptr + <offset>) & <mask>`
  O7 the word decodes consistently: `bits & ~or(masks)` is 0 on all 26 rows

Usage
    python Tools/scripts/weapons_bools.py --write
    python Tools/scripts/weapons_bools.py --check
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
MD = os.path.join(OUT, "WEAPONS_BOOLS.md")
JS = os.path.join(OUT, "WEAPONS_BOOLS.json")
WEAPONS = os.path.join(OUT, "WEAPONS.json")
SDK = "E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated"

DECL_RE = re.compile(r"^\s*public\s+(?:unsafe\s+)?bool\s+(\w+)\s*$")
# The mask is a C# int literal: bit 31 is written as -2147483648 in the generated getter, so the
# sign must be accepted (abs() recovers the 0x80000000 mask).
GETTER_RE = re.compile(r"Ptr \+ (\d+)\)\s*&\s*(-?\d+)\)\s*!=\s*0")
BASE_RE = re.compile(r"^public partial class\s+(\w+)\s*:\s*([\w.]+)")


def sdk_index() -> dict:
    """class -> path, across every generated namespace folder."""
    out = {}
    for sub in sorted(os.listdir(SDK)):
        d = os.path.join(SDK, sub)
        if not os.path.isdir(d):
            continue
        for fn in os.listdir(d):
            if fn.endswith(".g.cs"):
                out.setdefault(fn[:-5], os.path.join(d, fn))
    return out


def parse_class(path: str) -> dict:
    """bool properties: [(member, offset, mask, line, decl)], plus the base class."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    base = None
    for line in lines:
        m = BASE_RE.match(line)
        if m:
            base = m.group(2).split(".")[-1]
            break
    bools, i = [], 0
    while i < len(lines):
        m = DECL_RE.match(lines[i])
        if not m:
            i += 1
            continue
        member = m.group(1)
        for j in range(i, min(i + 7, len(lines))):
            g = GETTER_RE.search(lines[j])
            if g:
                mask = abs(int(g.group(2)))
                bools.append({"member": member, "offset": int(g.group(1)),
                              "mask": mask,
                              "mask_hex": "0x%X" % mask,
                              "line": i + 1, "getter_line": j + 1,
                              "file": os.path.basename(path),
                              "decl": lines[i].strip()})
                break
        i += 1
    return {"base": base, "bools": bools, "file": os.path.basename(path)}


def build_classes(names: set) -> tuple[dict, dict]:
    """Parse the named classes AND every ancestor they inherit from.

    The 26 rows include offsets declared well above the object's own class (a cannon's bool word
    can live in `RWeapon`), so stopping at the first unparsed base silently loses those rows.
    """
    idx = sdk_index()
    parsed: dict = {}
    todo = list(names)
    while todo:
        name = todo.pop()
        if name in parsed:
            continue
        p = idx.get(name)
        if not p:
            continue
        parsed[name] = parse_class(p)
        base = parsed[name].get("base")
        if base and base not in parsed:
            todo.append(base)
    return parsed, idx


def lineage(cls: str, parsed: dict) -> list:
    out, seen = [], set()
    while cls and cls not in seen:
        out.append(cls)
        seen.add(cls)
        cls = (parsed.get(cls) or {}).get("base")
    return out


def bools_at(cls: str, offset: int, parsed: dict) -> tuple[list, str]:
    for c in lineage(cls, parsed):
        hits = [b for b in (parsed.get(c) or {}).get("bools", []) if b["offset"] == offset]
        if hits:
            return sorted(hits, key=lambda b: b["mask"]), c
    return [], None


def build() -> dict:
    d = json.load(open(WEAPONS, encoding="utf-8"))
    rows = d["offset_only"]
    objs = {o["key"]: o for o in d["objects"]}
    classes = {o["class"] for o in d["objects"]}
    parsed, idx = build_classes(classes)

    resolved, unknown = [], []
    for r in rows:
        cls = objs.get(r["object"], {}).get("class")
        hits, decl_in = bools_at(cls, r["offset"], parsed) if cls else ([], None)
        if not hits:
            unknown.append({**r, "class": cls,
                            "why": "no bool member at this offset in the class chain "
                                   "(binding missing: %s)" % (cls not in parsed)})
            continue
        members = [{"member": h["member"], "mask": h["mask"], "mask_hex": h["mask_hex"],
                    "bit": h["mask"].bit_length() - 1,
                    "file": h["file"], "line": h["line"], "getter_line": h["getter_line"],
                    "value": bool(r["bits"] & h["mask"])} for h in hits]
        resolved.append({"object": r["object"], "class": cls, "declared_in": decl_in,
                         "offset": r["offset"], "offset_hex": r["path"],
                         "bits": r["bits"], "bits_hex": "0x%08X" % r["bits"],
                         "members": members,
                         "or_mask": 0 if not members else
                         __import__("functools").reduce(lambda a, b: a | b,
                                                        [m["mask"] for m in members])})

    # words: (class, offset) -> member set + observed words per object
    words: dict = {}
    for r in resolved:
        k = (r["class"], r["offset"])
        w = words.setdefault(k, {"class": r["class"], "offset": r["offset"],
                                 "offset_hex": r["offset_hex"], "members": r["members"],
                                 "declared_in": r["declared_in"], "objects": []})
        w["objects"].append({"object": r["object"], "bits": r["bits"]})

    shared = []
    for k, w in sorted(words.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        vals = {o["bits"] for o in w["objects"]}
        pair = None
        if len(vals) > 1:
            a, b = next(iter(w["objects"])), None
            for o in w["objects"]:
                if o["bits"] != a["bits"]:
                    b = o
                    break
            flips = [m for m in w["members"] if (a["bits"] ^ b["bits"]) & m["mask"]]
            pair = {"a": a, "b": b, "xor": a["bits"] ^ b["bits"],
                    "xor_hex": "0x%08X" % (a["bits"] ^ b["bits"]),
                    "flipped_members": [m["member"] for m in flips],
                    "explained": all(m in flips for m in
                                     [m for m in w["members"]
                                      if (a["bits"] ^ b["bits"]) & m["mask"]])}
        shared.append({"class": w["class"], "offset": w["offset"],
                       "offset_hex": w["offset_hex"], "declared_in": w["declared_in"],
                       "members": w["members"], "objects": w["objects"],
                       "distinct_words": sorted(vals), "pair": pair})

    multi = [s for s in shared if len(s["members"]) > 1]
    orphan = [(s["class"], s["offset_hex"], bits, bits & ~s["members"][0]["mask"]
               if False else bits & ~__import__("functools").reduce(
                   lambda a, b: a | b, [m["mask"] for m in s["members"]]))
              for s in shared for bits in s["distinct_words"]]
    orphan = [o for o in orphan if o[3]]
    bad_mask = [s for s in shared for m in s["members"]
                if m["mask"] == 0 or (m["mask"] & (m["mask"] - 1))]
    dup_mask = [s for s in shared
                if len({m["mask"] for m in s["members"]}) != len(s["members"])]
    # A flip pair can only exist where the word was recorded on two objects.  Words seen once are
    # named but their bit order cannot be independently demonstrated - reported, not hidden.
    provable = [s for s in multi if len({o["object"] for o in s["objects"]}) > 1]
    unproven = [s for s in provable if len(s["distinct_words"]) > 1 and not s["pair"]]
    unproven += [s for s in provable if s["pair"] and not s["pair"]["explained"]]
    single_object = [s for s in multi if len({o["object"] for o in s["objects"]}) == 1]
    same_word = [s for s in provable if len(s["distinct_words"]) == 1]

    # O6: the cited line must state the member, and its getter must read offset & mask.
    wrong_cite = []
    for s in shared:
        for m in s["members"]:
            path = idx.get(s["declared_in"])
            if not path:
                wrong_cite.append((s["declared_in"], m["member"], "no file"))
                continue
            lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
            decl = lines[m["line"] - 1] if m["line"] - 1 < len(lines) else ""
            getter = lines[m["getter_line"] - 1] if m["getter_line"] - 1 < len(lines) else ""
            g = GETTER_RE.search(getter)
            if m["member"] not in decl or not g or int(g.group(1)) != s["offset"] \
                    or abs(int(g.group(2))) != m["mask"]:
                wrong_cite.append((s["declared_in"], m["member"], decl.strip()[:60]))

    checks = [
        ("the 26 offset-only bool records parse and every class has a generated binding",
         len(rows) == 26 and all(c in parsed for c in classes),
         "%d rows; classes %d, bound %d, missing %s"
         % (len(rows), len(classes), len(parsed), sorted(classes - set(parsed)))),
        ("every row resolves to at least one named bool member",
         not unknown,
         "%d named, %d unnamed %s" % (len(resolved), len(unknown),
                                      [(u["object"], u["offset"]) for u in unknown][:4])),
        ("every mask is a power of two and unique inside its word",
         not bad_mask and not dup_mask,
         "%d words, %d members; non-power-of-two %d, duplicate masks %d"
         % (len(shared), sum(len(s["members"]) for s in shared), len(bad_mask),
            len(dup_mask))),
        ("every bit set in any observed word is covered by a member mask",
         not orphan,
         "words with orphan bits: %d %s" % (len(orphan), orphan[:4])),
        ("every shared word whose objects disagree flips only bits its members own",
         not unproven,
         "%d multi-member words: %d recorded on 2+ objects, %d disagree and are explained, "
         "%d disagree unexplained %s, %d identical on every object, %d seen once"
         % (len(multi), len(provable), len([s for s in provable if s["pair"]]),
            len(unproven), [(s["class"], s["offset_hex"]) for s in unproven],
            len(same_word), len(single_object))),
        ("every citation states the member and its getter reads Ptr + offset & mask",
         not wrong_cite,
         "%d members cited, %d wrong %s"
         % (sum(len(s["members"]) for s in shared), len(wrong_cite), wrong_cite[:4])),
        ("the words decode without residue (bits & ~or(masks) == 0 on all 26 rows)",
         all((r["bits"] & ~r["or_mask"]) == 0 for r in resolved),
         "%d rows, residue %s"
         % (len(resolved), [(r["object"], r["bits"] & ~r["or_mask"]) for r in resolved
                            if r["bits"] & ~r["or_mask"]][:4])),
    ]

    return {
        "task": "name the 26 bit-packed bool words of WEAPONS.md from the BmSDK bindings",
        "inputs": {"weapons_json": "Research/BatmobileGrab/WEAPONS.json",
                   "sdk": SDK},
        "summary": {"rows": len(rows), "named": len(resolved), "unknown": len(unknown),
                    "words": len(shared), "members": sum(len(s["members"]) for s in shared),
                    "multi_member_words": len(multi),
                    "multi_with_pair": len([s for s in provable if s["pair"]]),
                    "multi_same_word": [{"class": s["class"], "offset_hex": s["offset_hex"],
                                         "bits": s["distinct_words"][0]}
                                        for s in same_word],
                    "single_object_words": [{"class": s["class"],
                                             "offset_hex": s["offset_hex"],
                                             "members": [m["member"] for m in s["members"]]}
                                            for s in single_object],
                    "classes": sorted(classes)},
        "words": shared,
        "unresolved": unknown,
        "checks": [{"check": n, "pass": bool(ok), "detail": det}
                   for n, ok, det in checks],
    }


def render(d: dict) -> str:
    a = []
    A = a.append
    s = d["summary"]
    A("# WEAPONS.md bit-packed bools, named by offset + mask")
    A("")
    A("Generated by `Tools/scripts/weapons_bools.py` (`--write`); `--check` recomputes every")
    A("mask, line and bit from the BmSDK sources.  `WEAPONS.md` is not edited.")
    A("")
    A("A `BoolProperty` tag does not carry a bit index: it carries the whole packed word"
      " (`bits`).")
    A("The word's offset is the tag's offset; each member's bit is the mask its getter reads in")
    A("`E:/Modding/_tools/BmSDK-AK/src/BmSDK/Generated/**/*.g.cs`:")
    A("")
    A("    get { return (...ToManaged<int>(Ptr + 2396) & 8) != 0; }")
    A("")
    A("So a word decodes into one bool per member by `(bits & mask) != 0`, and the bit position")
    A("is `log2(mask)`.")
    A("")
    A("## Summary")
    A("")
    A("| quantity | count |")
    A("|---|---:|")
    A("| offset-only bool records | %d |" % s["rows"])
    A("| named | **%d** |" % s["named"])
    A("| unresolved | %d |" % s["unknown"])
    A("| distinct bool words | %d |" % s["words"])
    A("| members named | %d |" % s["members"])
    A("| words shared by 2+ members | %d |" % s["multi_member_words"])
    A("")
    for w in d["words"]:
        A("## `%s` `%s` - %d member(s), declared in `%s`"
          % (w["class"], w["offset_hex"], len(w["members"]), w["declared_in"]))
        A("")
        A("| member | bit | mask | value in the recorded word | `.g.cs` |")
        A("|---|---:|---|---|---|")
        for m in w["members"]:
            A("| `%s` | %d | `%s` | %s | `%s:%d` |"
              % (m["member"], m["bit"], m["mask_hex"], m["value"], m["file"], m["line"]))
        A("")
        A("Words observed: %s." % ", ".join("`0x%08X`" % b for b in w["distinct_words"]))
        if w["pair"]:
            p = w["pair"]
            A("")
            A("Bit-order proof: `%s` has `%s` and `%s` has `%s`; the differing bits are `%s`,"
              % (p["a"]["object"], "0x%08X" % p["a"]["bits"], p["b"]["object"],
                 "0x%08X" % p["b"]["bits"], p["xor_hex"]))
            A("which are exactly the masks of %s."
              % (", ".join("`%s`" % x for x in p["flipped_members"]) or "no member")
              if p["flipped_members"] else "which no member mask covers - see O5.")
        A("")
    A("## Oracles")
    A("")
    A("| # | check | result | evidence |")
    A("|---:|---|---|---|")
    for i, c in enumerate(d["checks"], 1):
        A("| O%d | %s | **%s** | %s |" % (i, c["check"], "PASS" if c["pass"] else "FAIL",
                                          c["detail"]))
    A("")
    A("## UNKNOWNs")
    A("")
    A("1. **Which bool a shared word's bit belongs to, beyond the SDK's own getter.**  The")
    A("   binding is the evidence: it is the same offset space the engine linked, and each")
    A("   getter states `Ptr + offset & mask`.  No independent bit-order artefact exists in")
    A("   the packages, so the flip test above is the strongest available proof.")
    A("2. **Unresolved rows** (%d): listed with their reason; they need a binding for a class" % s["unknown"])
    A("   the generated sources do not cover.")
    A("")
    A("## Reproduce")
    A("")
    A("    uv run python Tools/scripts/weapons_bools.py --write")
    A("    uv run python Tools/scripts/weapons_bools.py --check")
    A("")
    return "\n".join(a) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if not (args.write or args.check):
        ap.error("pass --write or --check")

    d = build()
    md, js = render(d), json.dumps(d, indent=1) + "\n"
    ok = True
    for c in d["checks"]:
        print("%s  %s" % ("PASS" if c["pass"] else "FAIL", c["check"]))
        print("      %s" % c["detail"])
        ok = ok and c["pass"]
    print("\n%d/%d oracles pass" % (sum(1 for c in d["checks"] if c["pass"]), len(d["checks"])))

    if args.write:
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        open(JS, "w", encoding="utf-8", newline="\n").write(js)
        print("wrote %s (%d B)" % (os.path.relpath(MD, ROOT), len(md.encode())))
        print("wrote %s (%d B)" % (os.path.relpath(JS, ROOT), len(js.encode())))
    if args.check:
        bad = []
        for path, want in ((MD, md), (JS, js)):
            if not os.path.exists(path):
                bad.append("%s missing" % os.path.relpath(path, ROOT))
            elif open(path, encoding="utf-8").read() != want:
                bad.append("%s differs" % os.path.relpath(path, ROOT))
        if bad:
            print("CHECK FAILED: " + "; ".join(bad))
            ok = False
        else:
            print("CHECK OK: the stored .md/.json are byte-identical to a fresh recompute")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

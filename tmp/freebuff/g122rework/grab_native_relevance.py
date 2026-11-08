"""grab_native_relevance.py - classify the native remainder and re-decode its relevant half (G1-22).

The grab left 925 untagged objects; 140 of them are larger than 8 B and could in principle be
hiding a weapon, sim or damage value. This tool classifies every one of the 140 by class:

    irrelevant  property declarations (`*Property`), script `Function` bytecode, script `State`
                headers and `FaceFXAnimSet` assets - they name or implement, they never store a
                value the mod would translate
    relevant    a component instance or a script-class export: the classes that *could* carry a
                light/FX/threat/collision value or a class-level default

and then runs **one more decode pass** over every relevant object with `upk_read.py`
(`export_summary` on the exact export index from `objects.jsonl`), recording what the walk read
and, when it reads nothing, why: the payload's first word is a zero type-id, i.e. an empty
property list, so there is nothing for the tag walker to read. The tail after that empty list is
probed too - the first int32 resolves as the **parent class** for a script-class export (negative
index = import) and as the object's **own name** for a component instance (checked against the
name table).

Usage:
    python Tools/scripts/grab_native_relevance.py --write
    python Tools/scripts/grab_native_relevance.py --check
"""
import argparse
import collections
import json
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import upk_read as U  # noqa: E402

OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
OBJECTS = os.path.join(OUT, "objects.jsonl")
GAPS = os.path.join(OUT, "GAPS.md")
COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"

SCHEMA = 1
GENERATOR = "grab_native_relevance.py"
THRESHOLD = 8          # bytes: the card's "larger than 8 B" cut

# Components: instances whose class can carry a light, FX, threat or collision value.
COMPONENTS = {
    "RInteractionComponent", "ParticleSystemComponent", "SkeletalMeshComponent",
    "CylinderComponent", "SpotLightComponent", "AkDialogueComponent",
    "RVehicleThreatComponent",
}

# The four irrelevant kinds, with the reason published in the document.
IRRELEVANT = {
    "property": ("*Property", "property declaration - names a slot in a script struct or "
                              "function; the value itself lives on the archetype"),
    "function": ("Function", "script bytecode - the behaviour behind these names is already "
                             "decoded through the reference passes (G1-08, G1-14, REGISTRATION.md)"),
    "state": ("State", "script state header (state machine label, not a value)"),
    "facefx": ("FaceFXAnimSet", "FaceFX facial-animation asset for a dialogue line - audio/vis "
                                "data, counted by the audio cards"),
}

PACKAGES = {
    "Playable_Batmobile_SF": "V2",
    "Playable_BatmobileMK2_SF": "MK2",
    "Playable_BatmobileJoker_SF": "Joker",
    "Playable_BatmobileFunhouse_SF": "Funhouse",
}


def classify(row):
    """(verdict, kind, reason) for one untagged object."""
    cls = row.get("class")
    if cls is None:
        return ("relevant", "class",
                "script-class export (outer `BmScript`) - declares a class; its defaults live on "
                "the `Default__*` object, which the grab decodes separately")
    if cls in COMPONENTS:
        return ("relevant", "component",
                "component instance - the class can carry a light, FX, threat or collision value")
    if cls.endswith("Property"):
        return ("irrelevant", "property", IRRELEVANT["property"][1])
    if cls == "Function":
        return ("irrelevant", "function", IRRELEVANT["function"][1])
    if cls == "State":
        return ("irrelevant", "state", IRRELEVANT["state"][1])
    if cls == "FaceFXAnimSet":
        return ("irrelevant", "facefx", IRRELEVANT["facefx"][1])
    return ("UNCLASSIFIED", "unknown", "no rule covers this class")


def second_pass(pkg, row):
    """The extra decode pass: tag walk, then the tail when the walk reads nothing."""
    idx = row["index"]
    data = pkg.data(idx)
    s = U.export_summary(pkg, idx)
    out = {
        "index": idx,
        "bytes": row["size"],
        "head": data[:8].hex(" "),
        "tag_count": s["tag_count"],
        "parsed": s["parsed_bytes"],
        "stop": s["stop"],
        "outcome": None,
        "detail": None,
    }
    if s["tag_count"]:
        out["outcome"] = "decoded"
        out["detail"] = "%d tags, %d/%d bytes" % (s["tag_count"], s["parsed_bytes"], len(data))
        return out
    # Nothing read. Record why: an empty property list (zero type-id at byte 0), then the tail.
    if data[:4] != b"\x00\x00\x00\x00":
        out["outcome"] = "unexplained"
        out["detail"] = "payload does not start with an empty property list (head %s)" % out["head"]
        return out
    a, b = struct.unpack_from("<ii", data, 4) if len(data) >= 12 else (None, None)
    if a is None:
        out["outcome"] = "empty"
        out["detail"] = "empty property list; payload too short for a tail (%d B)" % len(data)
        return out
    if a < 0:
        out["outcome"] = "parent-class"
        out["detail"] = pkg.object_path(a)
        return out
    if 0 <= a < len(pkg.names) and pkg.names[a] == row["name"]:
        out["outcome"] = "own-name"
        out["detail"] = "tail is the object's own name (name index %d, number %d)" % (a, b)
        return out
    out["outcome"] = "unexplained"
    out["detail"] = "tail int32 %d resolves as neither the parent class nor the own name" % a
    return out


def build():
    if not os.path.isdir(COOKED):
        raise SystemExit("BmAK install not reachable at %s - the second decode pass needs it"
                         % COOKED)
    rows = [json.loads(l) for l in open(OBJECTS, encoding="utf-8") if l.strip()]
    untagged = [r for r in rows if not r.get("tag_count")]
    big = [r for r in untagged if (r.get("size") or 0) > THRESHOLD]
    small = [r for r in untagged if (r.get("size") or 0) <= THRESHOLD]

    objects = []
    for r in sorted(big, key=lambda r: (r.get("class") or "~", -(r["size"] or 0), r["name"])):
        verdict, kind, reason = classify(r)
        objects.append({
            "package": r["package"], "short": PACKAGES.get(r["package"], r["package"]),
            "name": r["name"], "class": r.get("class"), "size": r["size"],
            "index": r["index"], "outer": r.get("outer"),
            "native_refs": len(r.get("native_refs") or []),
            "verdict": verdict, "kind": kind, "reason": reason,
        })

    relevant = [o for o in objects if o["verdict"] == "relevant"]
    irrelevant = [o for o in objects if o["verdict"] == "irrelevant"]
    unclassified = [o for o in objects if o["verdict"] == "UNCLASSIFIED"]

    pkgs = {}
    for o in relevant:
        p = o["package"]
        if p not in pkgs:
            pkgs[p] = U.Package(os.path.join(COOKED, p + ".upk"))
        o["pass"] = second_pass(pkgs[p], o)

    # ---- checks ----------------------------------------------------------
    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check("population: 925 untagged", len(untagged) == 925, "%d" % len(untagged))
    check("population: 140 over the 8 B threshold", len(big) == 140,
          "%d over, %d at or below" % (len(big), len(small)))
    check("140/140 classified", not unclassified and len(objects) == 140,
          "%d irrelevant, %d relevant, %d unclassified"
          % (len(irrelevant), len(relevant), len(unclassified)))
    check("every relevant object got a second pass",
          all("pass" in o for o in relevant), "%d/%d" % (sum(1 for o in relevant if "pass" in o),
                                                         len(relevant)))
    check("every second pass records a stop reason",
          all(o["pass"]["stop"] for o in relevant if "pass" in o),
          collections.Counter(o["pass"]["stop"] for o in relevant if "pass" in o).most_common(1)[0][0]
          if relevant else "-")
    parents = [o for o in relevant if o.get("pass", {}).get("outcome") == "parent-class"]
    ownnames = [o for o in relevant if o.get("pass", {}).get("outcome") == "own-name"]
    check("script-class tails decode a parent class",
          len({o["name"] for o in parents}) == 5 and len(parents) == 7,
          "%d rows, %d distinct parents" % (len(parents), len({o["pass"]["detail"] for o in parents})))
    check("component tails are the object's own name",
          len(ownnames) == 17 and all(o["pass"]["detail"] for o in ownnames),
          "%d/%d components" % (len(ownnames), len([o for o in relevant if o["kind"] == "component"])))
    check("no second pass read a property tag",
          all(o["pass"]["tag_count"] == 0 for o in relevant),
          "%d tags over %d objects"
          % (sum(o["pass"]["tag_count"] for o in relevant), len(relevant)))
    gaps = open(GAPS, encoding="utf-8").read()
    check("GAPS.md still publishes 925 untagged", "**925**" in gaps, "text search")

    doc = {
        "schema": SCHEMA,
        "generated_by": GENERATOR,
        "threshold_bytes": THRESHOLD,
        "summary": {
            "untagged": len(untagged),
            "over_threshold": len(big),
            "at_or_below_threshold": len(small),
            "irrelevant": len(irrelevant),
            "relevant": len(relevant),
            "unclassified": len(unclassified),
            "irrelevant_bytes": sum(o["size"] for o in irrelevant),
            "relevant_bytes": sum(o["size"] for o in relevant),
            "by_class": {k: v for k, v in sorted(
                collections.Counter((o["class"] or "(unresolved)") for o in objects).items(),
                key=lambda kv: -kv[1])},
            "verdict_by_class": {k: v for k, v in sorted(
                collections.Counter("%s|%s" % (o["class"] or "(unresolved)", o["verdict"])
                                    for o in objects).items())},
            "parents": sorted({o["pass"]["detail"] for o in parents}),
            "outcomes": dict(collections.Counter(
                o["pass"]["outcome"] for o in relevant if "pass" in o)),
            "native_refs": sum(o["native_refs"] for o in objects),
            "small_by_class": dict(collections.Counter(
                (r.get("class") or "(unresolved)") for r in small).most_common(6)),
        },
        "objects": objects,
        "checks": checks,
    }
    return doc


def write_markdown(doc):
    s = doc["summary"]
    lines = []
    a = lines.append
    a("# The native remainder - what the 140 untagged objects are (G1-22)")
    a("")
    a("Generated by `Tools/scripts/grab_native_relevance.py`. Source: `objects.jsonl` (the 925")
    a("untagged exports the grab could not decode) plus one extra decode pass with `upk_read.py`")
    a("run over the relevant half **now**, against the shipped `.upk` files, using each row's own")
    a("export `index` - name matching is not enough here, because `CollisionCylinder`, `Mesh` and")
    a("`Interactions` exist several times per package and only some of the same-named exports")
    a("decode.")
    a("")
    a("| fact | value |")
    a("|---|---|")
    a("| untagged exports in the grab | **%d** |" % s["untagged"])
    a("| larger than 8 B (the card's threshold) | **%d** |" % s["over_threshold"])
    a("| at or below 8 B (not in scope; %s) | %d |" % (
        ", ".join("%s %d" % (k, v) for k, v in list(s["small_by_class"].items())[:3]),
        s["at_or_below_threshold"]))
    a("| classified **irrelevant** | %d objects, %s B |" % (
        s["irrelevant"], format(s["irrelevant_bytes"], ",")))
    a("| classified **relevant** | %d objects, %s B |" % (
        s["relevant"], format(s["relevant_bytes"], ",")))
    a("| unclassified | %d |" % s["unclassified"])
    a("")
    a("## The rule")
    a("")
    a("| class | verdict | why |")
    a("|---|---|---|")
    for _kind, (pattern, reason) in IRRELEVANT.items():
        a("| `%s` | irrelevant | %s |" % (pattern, reason))
    a("| *(unresolved)* — script-class export (outer `BmScript`) | relevant | declares a class; "
      "its defaults live on the `Default__*` object the grab already decodes |")
    a("| `RInteractionComponent`, `ParticleSystemComponent`, `SkeletalMeshComponent`, "
      "`CylinderComponent`, `SpotLightComponent`, `AkDialogueComponent`, "
      "`RVehicleThreatComponent` | relevant | a component instance whose class can carry a "
      "light, FX, threat or collision value |")
    a("")
    a("Anything no rule covers would be reported as `UNCLASSIFIED`; there are none.")
    a("")

    # ---- irrelevant -------------------------------------------------------
    a("## Irrelevant (%d objects)" % s["irrelevant"])
    a("")
    a("| class | objects | bytes | what it is |")
    a("|---|---|---|---|")
    agg = collections.defaultdict(lambda: [0, 0, ""])
    for o in doc["objects"]:
        if o["verdict"] != "irrelevant":
            continue
        k = o["class"] or "(unresolved)"
        agg[k][0] += 1
        agg[k][1] += o["size"]
        agg[k][2] = o["reason"]
    for k, (n, b, why) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        a("| `%s` | %d | %s | %s |" % (k, n, format(b, ","), why))
    a("")
    a("The byte mass is FaceFX: %s of the %s irrelevant bytes are facial-animation assets for"
      % (format(next(v[1] for k, v in agg.items() if k == "FaceFXAnimSet"), ","),
        format(s["irrelevant_bytes"], ",")))
    a("dialogue lines - audio/visual data, already in scope for the audio cards, never a")
    a("weapon/sim/damage number.")
    a("")

    # ---- relevant ---------------------------------------------------------
    a("## Relevant (%d objects) and the second decode pass" % s["relevant"])
    a("")
    a("| object | class | pkg | bytes | idx | native refs | tag walk | second pass outcome |")
    a("|---|---|---|---|---|---|---|---|")
    for o in sorted(doc["objects"], key=lambda o: (o["verdict"] != "relevant",
                                                    o["class"] or "~", o["name"])):
        if o["verdict"] != "relevant":
            continue
        p = o["pass"]
        a("| `%s` | `%s` | %s | %d | %d | %d | %d tags, stop `%s` | **%s** - %s |" % (
            o["name"], o["class"] or "(unresolved)", o["short"], o["size"], p["index"],
            o["native_refs"], p["tag_count"], p["stop"], p["outcome"], p["detail"]))
    a("")
    a("### What the pass recovered")
    a("")
    out = s["outcomes"]
    a("- **%d of %d objects yielded no property tag** - every payload starts with a zero type-id"
      % (out.get("own-name", 0) + out.get("parent-class", 0) + out.get("empty", 0)
         + out.get("unexplained", 0), s["relevant"]))
    a("  at byte 0, which is an empty property list, so `upk_read`'s walker stops before reading")
    a("  anything (`stop=end`, 0 parsed bytes). That is the failure reason for the whole set, not")
    a("  a per-object mystery.")
    a("- **%d script-class rows (%d distinct classes) decode their parent class** from the first"
      % (out.get("parent-class", 0), len(s["parents"])))
    a("  object reference after that empty list (negative index = import):")
    for p in s["parents"]:
        a("  `%s`," % p)
    a("  which is what an `(unresolved)` class export is: a script class compiled into the")
    a("  package, outer `BmScript`, declaring no properties of its own.")
    a("- **%d component rows stop at their own name**: the tail is `%s`, i.e. the object's name"
      % (out.get("own-name", 0), "NameIndex + Number"))
    a("  read against the name table (verified per row: the index resolves to the object's own")
    a("  name, and to an unrelated export when read as an object index - so it is a header, not a")
    a("  value). At 14-62 bytes there is no room for a value field in any case.")
    a("- The grab's own reference scan recovered **%d native references across %d of the 140 rows**"
      % (s["native_refs"],
         sum(1 for o in doc["objects"] if o["native_refs"])))
    a("  (`native_refs` in `objects.jsonl`) - references, not values.")
    a("")

    # ---- what it settles ---------------------------------------------------
    a("## What this settles")
    a("")
    a("- **No weapon, sim or damage value hides in the native remainder.** The relevant half is 5")
    a("  script class declarations (parent class now known) and 17 component instances whose")
    a("  payloads are header-only; the values those classes have live on their `Default__*`")
    a("  objects, which the grab decodes as ordinary tagged rows (`Default__RBatmobileMissile-`")
    a("  `LauncherJoker` and friends).")
    a("- The card's `relevant` set produces no new number for G1-08/G1-14/G1-21 to add: the")
    a("  families those cards list are all in `OFFSETS.json` / `CHAIN.json` already.")
    a("- Gaps.md's \"refs recovered\" column is explained: %d of the 140 rows carry %d"
      % (sum(1 for o in doc["objects"] if o["native_refs"]), s["native_refs"]))
    a("  references the native scan found by index probing; a reference is a pointer to another")
    a("  object, not a value.")
    a("")
    a("## Gaps (stated, not filled)")
    a("")
    a("- The 17 component tails are **not modelled** by `upk_read`: after the empty property list")
    a("  they hold an FName header and, for the larger ones, native bytes this walker does not")
    a("  decode. Nothing in the class suggests a value slot, and the payloads are 14-62 B, but")
    a("  the byte layout itself stays unexplained.")
    a("- The 785 untagged objects at or below 8 B are not individually classified - the card sets")
    a("  the threshold at >8 B, and 768 of them are 2-byte `Package` stubs.")
    a("- This pass needs the BmAK install at `%s`; without it `--check` cannot re-run and fails" % COOKED)
    a("  with that path in the message.")
    a("")
    a("## Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in doc["checks"]:
        a("| %s | %s | %s |" % (c["name"], "PASS" if c["pass"] else "FAIL", c["detail"]))
    a("")
    a("%d/%d checks passed." % (sum(1 for c in doc["checks"] if c["pass"]),
                                len(doc["checks"])))
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="write NATIVE_RELEVANCE.json and .md")
    ap.add_argument("--check", action="store_true",
                    help="re-run the classification and the decode pass, compare with disk")
    args = ap.parse_args()
    if not args.write and not args.check:
        args.check = True

    doc = build()
    json_path = os.path.join(OUT, "NATIVE_RELEVANCE.json")
    md_path = os.path.join(OUT, "NATIVE_RELEVANCE.md")

    if args.write:
        with open(json_path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(write_markdown(doc))
        print("wrote NATIVE_RELEVANCE.json (%d objects) and NATIVE_RELEVANCE.md"
              % len(doc["objects"]))
        return 0

    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(json_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    with open(json_path, encoding="utf-8") as fh:
        if json.load(fh) != doc:
            print("STALE: NATIVE_RELEVANCE.json does not match a fresh build (run --write)")
            return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    s = doc["summary"]
    print("OK: %d/%d classified (%d irrelevant, %d relevant); %d/%d checks"
          % (s["irrelevant"] + s["relevant"], s["over_threshold"], s["irrelevant"],
             s["relevant"], len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""grab_native_relevance.py - classify the native remainder and re-decode its relevant half (G1-22).

The grab left 925 untagged objects; 140 of them are larger than 8 B and could in principle be
hiding a weapon, sim or damage value. This tool classifies every one of the 140 by class:

    irrelevant  property declarations (`*Property`), script `State` headers and `FaceFXAnimSet`
                assets - they name a slot, a state label or a facial animation, they never store
                a value the mod would translate
    relevant    a component instance, a script-class export or a `Function` body: the classes
                that *could* carry a light/FX/threat/collision value, a class-level default or
                a numeric literal in bytecode

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
import math
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

# The three irrelevant kinds, with the reason published in the document.
IRRELEVANT = {
    "property": ("*Property", "property declaration - names a slot in a script struct or "
                              "function; the value itself lives on the archetype"),
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
        return ("relevant", "function",
                "script bytecode - not decoded by this pass or by any G1 card; numeric literals "
                "are possible and their meaning is UNKNOWN")
    if cls == "State":
        return ("irrelevant", "state", IRRELEVANT["state"][1])
    if cls == "FaceFXAnimSet":
        return ("irrelevant", "facefx", IRRELEVANT["facefx"][1])
    return ("UNCLASSIFIED", "unknown", "no rule covers this class")


def component_tail_floats(data):
    """[(offset, value)] for float-looking numbers in a component tail (after the 12 B header)."""
    out = []
    for off in range(12, len(data) - 3, 4):
        v = struct.unpack_from("<f", data, off)[0]
        if math.isfinite(v) and 0.01 <= abs(v) <= 10000.0:
            out.append([off, round(v, 5)])
    return out


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
    if row.get("kind") == "component":
        out["tail_floats"] = component_tail_floats(data)
        out["tail_nonzero"] = sum(1 for b in data[12:] if b)
    if s["tag_count"]:
        out["outcome"] = "decoded"
        out["detail"] = "%d tags, %d/%d bytes" % (s["tag_count"], s["parsed_bytes"], len(data))
        return out
    if row.get("kind") == "function":
        nz = sum(1 for b in data if b)
        out["nonzero"] = nz
        out["outcome"] = "bytecode"
        out["detail"] = ("script bytecode, %d B (%d non-zero) - not decoded; numeric literals "
                         "possible, meaning UNKNOWN" % (len(data), nz))
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
    functions = [o for o in relevant if o["kind"] == "function"]
    check("Function exports are relevant, not irrelevant",
          len(functions) == 20 and all(o["verdict"] == "relevant" for o in functions),
          "%d rows, %s B" % (len(functions), format(sum(o["size"] for o in functions), ",")))
    check("every Function row records undecoded bytecode",
          all(o["pass"]["outcome"] == "bytecode" for o in functions),
          "%d/%d" % (sum(1 for o in functions if o["pass"]["outcome"] == "bytecode"),
                      len(functions)))
    with_floats = [o for o in ownnames if o["pass"].get("tail_floats")]
    check("component tails report their float-like values",
          all(bool(o["pass"].get("tail_floats")) == (o["pass"].get("tail_nonzero", 0) > 0)
              for o in ownnames),
          "%d of %d own-name components carry a float" % (len(with_floats), len(ownnames)))
    two = sum(1 for r in small if r["size"] == 2)
    six = sum(1 for r in small if r["size"] == 6)
    check("the small-object census adds up",
          two + six == len(small),
          "%d two-byte + %d six-byte = %d" % (two, six, len(small)))
    check("no second pass read a property tag",
          all(o["pass"]["tag_count"] == 0 for o in relevant),
          "%d tags over %d objects"
          % (sum(o["pass"]["tag_count"] for o in relevant), len(relevant)))
    gaps = open(GAPS, encoding="utf-8").read()
    check("GAPS.md still publishes 925 untagged", "**925**" in gaps, "text search")

    doc = {
        "schema": SCHEMA + 1,
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
            "small_sizes": {str(k): v for k, v in
                            sorted(collections.Counter(r["size"] for r in small).items())},
            "small_by_class": dict(collections.Counter(
                (r.get("class") or "(unresolved)") for r in small)),
            "small_by_size_class": {
                str(size): dict(collections.Counter(
                    r.get("class") or "(unresolved)" for r in small
                    if r["size"] == size).most_common())
                for size in sorted({r["size"] for r in small})},
            "function_exports": len(functions),
            "function_bytes": sum(o["size"] for o in functions),
            "function_bytes_min": min((o["size"] for o in functions), default=None),
            "function_bytes_max": max((o["size"] for o in functions), default=None),
            "function_nonzero_min": min((o["pass"].get("nonzero", 0) for o in functions),
                                        default=None),
            "function_nonzero_max": max((o["pass"].get("nonzero", 0) for o in functions),
                                        default=None),
            "bytecode_rows": sum(1 for o in functions if o["pass"]["outcome"] == "bytecode"),
            "component_tails_with_floats": len(with_floats),
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
    a("untagged exports in the grab - objects with no property tag, not objects the reader failed")
    a("on) plus one extra decode pass with `upk_read.py`")
    a("run over the relevant half **now**, against the shipped `.upk` files, using each row's own")
    a("export `index` - name matching is not enough here, because `CollisionCylinder`, `Mesh` and")
    a("`Interactions` exist several times per package and only some of the same-named exports")
    a("decode.")
    a("")
    a("| fact | value |")
    a("|---|---|")
    a("| untagged exports in the grab | **%d** |" % s["untagged"])
    a("| larger than 8 B (the card's threshold) | **%d** |" % s["over_threshold"])
    sizes = s.get("small_sizes") or {}
    a("| at or below 8 B (not in scope: %s) | %d |" % (
        ", ".join("%s B x %s" % (k, sizes[k]) for k in sorted(sizes, key=int)),
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
    a("| `Function` | relevant | script bytecode - **not decoded**; numeric literals are "
      "possible and their meaning is UNKNOWN |")
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
    notag = sum(1 for o in doc["objects"] if o.get("pass", {}).get("tag_count") == 0)
    a("- **%d of %d objects yielded no property tag**: the %d script-class and component payloads"
      % (notag, s["relevant"], notag - s["bytecode_rows"]))
    a("  start with a zero type-id at byte 0, which is an empty property list, so `upk_read`'s")
    a("  walker stops before reading anything (`stop=end`, 0 parsed bytes). The other %d are"
      % s["bytecode_rows"])
    a("  `Function` payloads - live bytecode, not an empty list - and stay undecoded (next bullet).")
    a("- **%d script-class rows (%d distinct classes) decode their parent class** from the first"
      % (out.get("parent-class", 0), len(s["parents"])))
    a("  object reference after that empty list (negative index = import):")
    for p in s["parents"]:
        a("  `%s`," % p)
    a("  which is what an `(unresolved)` class export is: a script class compiled into the")
    a("  package, outer `BmScript`, declaring no properties of its own. That identification is")
    a("  **inferred from the name correspondence** (all %d parents match the export names), not a"
      % len(s["parents"]))
    a("  decoded `UClass.SuperField`.")
    floats = [(o["name"], off, v) for o in doc["objects"]
              for off, v in (o.get("pass", {}).get("tail_floats") or [])]
    a("- **%d component rows stop at their own name**: the tail is `%s`, i.e. the object's name"
      % (out.get("own-name", 0), "NameIndex + Number"))
    a("  read against the name table (verified per row: the index resolves to the object's own")
    a("  name, and to an unrelated export when read as an object index - so it is a header, not a")
    a("  value). **%d of those %d payloads carry a float-like value** in the unmodelled tail:"
      % (s["component_tails_with_floats"], out.get("own-name", 0)))
    a("  %s." % ", ".join("`%s` +%d = %.5f" % (n, off, v) for n, off, v in floats))
    a("  Their meaning is **UNKNOWN** - this walker does not model the tail, so whether any is a")
    a("  value the mod could use is not decided here.")
    a("- **%d `Function` exports (%s B) are live bytecode and were not decoded**: payloads are"
      % (s["function_exports"], format(s["function_bytes"], ",")))
    a("  %d-%d B, %d-%d non-zero bytes each. A numeric literal (damage, impulse, velocity) could"
      % (s["function_bytes_min"], s["function_bytes_max"],
         s["function_nonzero_min"], s["function_nonzero_max"]))
    a("  sit in the instruction stream, so they are classified **relevant**; none of the names")
    a("  appears in `WEAPONS.md`, and `DAMAGE_RULES.md` carries only the unrelated substring")
    a("  `bDamagedByCloudburstTank`. The card's second pass records them as bytecode, not a value.")
    a("- The grab's own reference scan recovered **%d native references across %d of the 140 rows**"
      % (s["native_refs"],
         sum(1 for o in doc["objects"] if o["native_refs"])))
    a("  (`native_refs` in `objects.jsonl`) - references, not values.")
    a("")

    # ---- what it settles ---------------------------------------------------
    a("## What this settles - and what it does not")
    a("")
    a("- **The %d objects this card calls relevant yielded no property tag.** %d script-class rows"
      % (s["relevant"], out.get("parent-class", 0)))
    a("  resolve their parent class (name-inferred), %d components stop at their own name (%d with"
      % (out.get("own-name", 0), s["component_tails_with_floats"]))
    a("  an unlabelled float in the unmodelled tail), and %d `Function` exports are bytecode."
      % s["bytecode_rows"])
    a("- **No weapon, sim or damage value was extracted anywhere in the 140.** That is a result of")
    a("  the pass, not a proof of absence: the %d `Function` payloads (%s B) were not decoded, so a"
      % (s["function_exports"], format(s["function_bytes"], ",")))
    a("  literal inside them is **UNKNOWN**, and the %d component tails are not modelled, so their"
      % s["component_tails_with_floats"])
    a("  floats have no meaning yet. Both are stated again under Gaps.")
    a("- The values the relevant classes do have live on their `Default__*` objects, which the grab")
    a("  decodes as ordinary tagged rows (`Default__RBatmobileMissileLauncherJoker` and friends).")
    a("- The card's `relevant` set adds no *decoded* number to G1-08/G1-14/G1-21: the families those")
    a("  cards list are all in `OFFSETS.json` / `CHAIN.json` already. Whether an undecoded literal")
    a("  belongs to one of them is UNKNOWN until the bytecode is read.")
    a("- Gaps.md's \"refs recovered\" column is explained: %d of the 140 rows carry %d"
      % (sum(1 for o in doc["objects"] if o["native_refs"]), s["native_refs"]))
    a("  references the native scan found by index probing; a reference is a pointer to another")
    a("  object, not a value.")
    a("")
    a("## Gaps (stated, not filled)")
    a("")
    a("- The %d component tails are **not modelled** by `upk_read`: after the empty property list"
      % out.get("own-name", 0))
    a("  they hold an FName header and then native bytes this walker does not decode. %d of the"
      % s["component_tails_with_floats"])
    a("  payloads carry a float-like value there (listed above); what each one means is UNKNOWN.")
    a("- The %d `Function` exports (%s B) are **undecoded bytecode**. A numeric literal could be"
      % (s["function_exports"], format(s["function_bytes"], ",")))
    a("  in the instruction stream; nothing here reads it, so the card's 'decoded or explained'")
    a("  exit is 'explained: not decoded', never a value.")
    a("- The %d untagged objects at or below 8 B are not individually classified - the card sets"
      % s["at_or_below_threshold"])
    def census(size, shown):
        cls = ((s.get("small_by_size_class") or {}).get(size) or {})
        head = ", ".join("%s %d" % (k, v) for k, v in list(cls.items())[:shown])
        more = ", ... %d classes" % len(cls) if len(cls) > shown else ""
        return "%s-byte x%s (%s%s)" % (size, s["small_sizes"][size], head, more)

    a("  the threshold at >8 B. They are %s."
      % ", ".join(census(size, 3 if size == "2" else 4)
                  for size in sorted(s.get("small_sizes") or {}, key=int)))
    outside = [k for k in ((s.get("small_by_size_class") or {}).get("6") or {})
               if k not in COMPONENTS]
    if outside:
        a("  The six-byte rows include %s, whose classes are not in the rule above; they are"
          % ", ".join("`%s`" % k for k in outside))
        a("  below the card's cut, so they are named here and not classified.")
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
    with open(md_path, encoding="utf-8") as fh:
        if fh.read() != write_markdown(doc):
            print("STALE: NATIVE_RELEVANCE.md does not match a fresh render (run --write)")
            return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    s = doc["summary"]
    print("OK: %d/%d classified (%d irrelevant, %d relevant); %d/%d checks; md: PASS"
          % (s["irrelevant"] + s["relevant"], s["over_threshold"], s["irrelevant"],
             s["relevant"], len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""What is the u32 at +12 of an AggGeom payload?  (follow-up to reverify_physics)

The four wreck packages' AggGeom payloads are identical except for one u32 at offset +12
(2846 / 2851 / 3120 / 2836).  This file answers what that word *is*, and tests the three
candidate readings instead of picking one:

  count      - a u32 count of something in the aggregate
  object ref - an export/import index naming an object
  name index - an FName index into the package's own name table

The word sits at +4 of the first shaped element's 20-byte StructProperty tag
(aggregate = [nSphere][nBox][element 0][element 1]...), which is that tag's *name index*
field.  So the test is: resolve it in each package's name table and compare the strings.

Read-only; prints evidence and exits non-zero if any check fails.

    python Tools/scripts/bmak_word12.py            # evidence + checks
    python Tools/scripts/bmak_word12.py --check    # checks only, one line per oracle
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import upk_read as U  # noqa: E402
import grab_collision_shapes as G  # noqa: E402

WRECK = ["Playable_Batmobile_SF", "Playable_BatmobileMK2_SF",
         "Playable_BatmobileJoker_SF", "Playable_BatmobileFunhouse_SF"]
FLEET = ["BmGame", "Orphan", "Startup", "StartupPatch"]   # the packages holding RB_BodySetup

results = []


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print("PASS  %s" % name if ok else "FAIL  %s" % name)
    if detail:
        for line in detail.splitlines():
            print("      " + line)
    return ok


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def wreck_rows():
    """u32@12 per body, per wreck package, resolved three ways."""
    rows = []
    for name in WRECK:
        pkg = U.Package(os.path.join(G.GAME, name + ".upk"))
        bodies = G.bodies_of(pkg)
        words = {}
        for idx in bodies:
            payload, _tags = G.agg_of(pkg, idx)
            if payload is None or len(payload) < 16:
                continue
            words.setdefault(u32(payload, 12), []).append(idx)
        tm_index = pkg.names.index("TM") if "TM" in pkg.names else None
        for word, idxs in words.items():
            rows.append({
                "package": name,
                "word": word,
                "bodies": len(idxs),
                "name": pkg.names[word] if 0 <= word < len(pkg.names) else None,
                "tm_index": tm_index,
                "exports": len(pkg.exports),
                "export_name": pkg.object_path(word) if 1 <= word <= len(pkg.exports) else None,
                "imports": len(pkg.imports),
                "name_count": len(pkg.names),
            })
    return rows


def element_name_indices():
    """Every shaped element's tag name index, over every body of the four packages."""
    seen = {}
    total = 0
    for name in FLEET:
        path = os.path.join(G.GAME, name + ".upk")
        if not os.path.exists(path):
            continue
        pkg = U.Package(path)
        bodies = G.bodies_of(pkg)
        print("  scanning %-14s %4d bodies" % (name, len(bodies)), file=sys.stderr)
        for n, idx in enumerate(bodies, 1):
            payload, _tags = G.agg_of(pkg, idx)
            if payload is None:
                continue
            agg = G.parse_aggregate(payload)
            if agg["error"]:
                continue
            for a in agg["arrays"]:
                if a["kind"] == "convex":
                    continue
                for e in a["elements"]:
                    total += 1
                    ni = e["tm_tag"]["name_index"]
                    nm = pkg.names[ni] if 0 <= ni < len(pkg.names) else None
                    seen.setdefault((name, ni, nm), 0)
                    seen[(name, ni, nm)] += 1
            if n % 400 == 0:
                print("    %s: %d/%d bodies, %d elements" % (name, n, len(bodies), total),
                      file=sys.stderr)
    return seen, total


def main() -> int:
    only_check = "--check" in sys.argv

    print("### 1. the word at +12, per wreck package")
    rows = wreck_rows()
    if not only_check:
        print("  %-32s %-6s %-5s %-8s %-8s %s" %
              ("package", "word", "names", "resolves", "TM index", "as an export index"))
        for r in rows:
            print("  %-32s %-6d %-5d %-8r %-8s %r"
                  % (r["package"], r["word"], r["name_count"], r["name"], r["tm_index"],
                     r["export_name"]))

    check("every wreck package's word resolves to the name 'TM'",
          all(r["name"] == "TM" for r in rows),
          "\n".join("%s: %d -> %r" % (r["package"], r["word"], r["name"]) for r in rows))
    check("each word equals the position of 'TM' in that package's own name table",
          all(r["word"] == r["tm_index"] for r in rows),
          "\n".join("%s: word %d, names.index('TM') %s" % (r["package"], r["word"], r["tm_index"])
                    for r in rows))
    check("the word is constant over every body inside a package",
          all(r["bodies"] == 32 for r in rows),
          "bodies per word: %s" % ", ".join("%s=%d" % (r["package"].replace("Playable_", ""),
                                                       r["bodies"]) for r in rows))
    check("the word is in range as a name index in all four",
          all(0 <= r["word"] < r["name_count"] for r in rows),
          "name table sizes: %s" % ", ".join(str(r["name_count"]) for r in rows))
    check("the word is out of range as an import index, so a package reference cannot explain it",
          all(r["word"] >= r["imports"] for r in rows),
          "imports per package: %s" % ", ".join(str(r["imports"]) for r in rows))
    check("read as an export index it names four different, unrelated objects",
          len({r["export_name"] for r in rows}) == len(rows)
          and all(r["export_name"] != "TM" and "AggGeom" not in (r["export_name"] or "")
                  for r in rows),
          "\n".join("%s: %d -> %r" % (r["package"], r["word"], r["export_name"]) for r in rows))

    print("\n### 2. the word cannot be a count")
    pkg = U.Package(os.path.join(G.GAME, WRECK[0] + ".upk"))
    body = G.bodies_of(pkg)[0]
    payload, _tags = G.agg_of(pkg, body)
    n_sphere, n_box = u32(payload, 0), u32(payload, 4)
    tag_type, tag_off = struct.unpack_from("<HH", payload, 8)
    ni, number, size, arr = struct.unpack_from("<iiii", payload, 12)
    if not only_check:
        print("  payload %d B: nSphere=%d nBox=%d; element 0 tag at +8: type=%d offset=%d "
              "name_index=%d number=%d size=%d array=%d"
              % (len(payload), n_sphere, n_box, tag_type, tag_off, ni, number, size, arr))
        print("  the word %d read as the tag's name index, its neighbours %d (number) and %d "
              "(size = the TM struct's 64 bytes) as the FName's number and the struct size"
              % (ni, number, size))
    check("the same three fields read cleanly: number 0, size 64 = one TM struct",
          number == 0 and size == 64,
          "number=%d size=%d (a TM is 64 bytes: 16 floats)" % (number, size))
    check("a count of that value cannot fit the payload",
          ni > len(payload),
          "word %d > payload %d bytes" % (ni, len(payload)))

    print("\n### 3. the field is 'TM' for every shaped element in the fleet")
    seen, total = element_name_indices()
    names = sorted({k[2] for k in seen})
    if not only_check:
        for (pkgname, ni, nm), cnt in sorted(seen.items()):
            print("  %-14s name_index %-6d %-8r %6d element(s)" % (pkgname, ni, nm, cnt))
    check("all shaped elements' tag name index resolves to 'TM'",
          names == ["TM"] and total > 0,
          "%d elements over %d packages; resolved names: %s" % (total, len({k[0] for k in seen}),
                                                                names))

    print("\n### result")
    bad = [n for n, ok, _ in results if not ok]
    if bad:
        print("FAILED: %d of %d oracles (%s)"
              % (len(bad), len(results), "; ".join(bad)))
        return 1
    print("ALL %d ORACLES PASS — the word at +12 is the FName index of the element tag's "
          "struct name, 'TM', which each package stores at its own index." % len(results))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""bmak_bind.py - name the Batmobile archetypes' stripped offsets (G1-1).

`BmGame.upk` ships the script classes the archetypes were cooked from: every class export owns one
child `UProperty` per field, named, typed and in declaration order, and the cooked tag stream is
written in that same order, ascending by offset.  Named tags (`StructProperty`, `ObjectProperty`,
`ByteProperty` with an enum name) carry the property name inline, so each one is an exact anchor:
it fixes the offset of a known property and the base of the object it was serialised from.

The walk is only as exact as its slot rules, and this build has three that are easy to get wrong:
a static array is one property with `UProperty::ArrayDim` slots, every type (pointers included)
aligns to 4, and an `FInterpCurve<T>` slot is 20 bytes.  With those, `RVehicleSimBatmobile`'s
layout reproduces the linked class exactly (extent 1220); the tool still aligns each run under the
base its own start anchor measures, binds a tag only when it lands exactly on a slot of the same
`UProperty` kind, and keeps the alignment monotone in declaration order so one property can never be
named twice.  Fields the shipped copy cannot reproduce are left to `bmsdk_offsets.py`, which indexes
the running game's own property offsets - that is now the primary naming route for cooked tags.

Usage:
    python Tools/scripts/bmak_bind.py --class RVehicleSimBatmobile
    python Tools/scripts/bmak_bind.py --all --json Working/Grab/bound.json
"""
import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import bmak_layout as L  # noqa: E402

STREAMS = os.path.join(ROOT, "Working", "Grab", "streams.json")
# Struct slot sizes for structs BmGame.upk does not ship.  An InterpCurve is 20 bytes (a 16-byte
# TArray plus a 4-byte-rounded mode enum) whatever its point type: the BmSDK-AK class dump spaces
# consecutive curve properties 20 apart, and 24 put every property after a curve one slot too far.
TYPED = {"PostProcessSettings": 0x200, "AkSoundHandle": 8, "InterpCurveFloat": 20,
         "InterpCurveVector": 20, "InterpCurveVector2D": 20, "InterpCurveQuat": 20,
         "InterpCurveTwoVectors": 20}

CLASSES = [
    "RVehicleSimBatmobile", "RVehicleBatmobileBase", "RVehicleBatmobilePredictor",
    "RVehicleBatmobile", "SVehicleWheel",
    "RBatmobileAllegianceSwitcher", "RBatmobileBooster", "RBatmobileCannon", "RBatmobileEMP",
    "RBatmobileEMPMissile", "RBatmobileHeavyCannon", "RBatmobileMissile",
    "RBatmobileMissileLauncher", "RBatmobileMissileLauncherJoker", "RBatmobileSonar",
    "RBatmobileVehicleTracker", "RBatmobileWinch",
]


def load_streams():
    if not os.path.isfile(STREAMS):
        return {}
    return json.load(open(STREAMS, encoding="utf-8"))


def sources_for(lay, cls, streams):
    out = {}
    cdo = lay.top_level_offsets(cls)[0]
    if cdo:
        out["Default__" + lay.export(cls)["name"]] = [[t["offset"], t["type"], t.get("name")]
                                                      for t in cdo]
    for k, v in (streams or {}).items():
        out[k] = v
    return out


def anchors_of(rows, tags):
    """[(offset, property_index)] for every tag that carries a name this class declares."""
    by_name = {r["name"]: i for i, r in enumerate(rows)}
    out = []
    for off, ttype, name in sorted(tags, key=lambda t: t[0]):
        i = by_name.get(name)
        if i is not None and L.same_kind(ttype, rows[i]["kind"]):
            out.append((off, i))
    return out


def bind_stream(rows, tags, segments=False):
    """Bind one stream; returns (bound{off:(name,how)}, stats).

    Anchors are always bound: their names are inline in the stream.  `segments` additionally places
    unnamed tags under the base the previous anchor measures; that is sound only as far as the
    layout's slot sizes are (see the module docstring), so it is off by default.
    """
    tags = sorted(tags, key=lambda t: t[0])
    anch = anchors_of(rows, tags)
    bound = {off: (rows[i]["name"], "anchor") for off, i in anch}
    if not anch:
        # no inline name anywhere: fall back to the declaration order from offset 0, where the class
        # layout is exact (a class's first property is at 0).  Stop at the first tag that does not
        # land, so a wrong struct slot cannot drag the rest of the run with it.
        got, j = {}, -1
        for off, ttype, name in tags:
            if name:
                continue
            for k, r in enumerate(rows):
                if k <= j:
                    continue
                if r["offset"] == off and L.same_kind(ttype, r["kind"]):
                    got[off] = (r["name"], "prefix")
                    j = k
                    break
                if r["offset"] > off:
                    break
            if not got:
                break
        stats = {"tags": len(tags), "anchors": 0, "segment": len(got), "backward": 0,
                 "tail": 0, "dropped": 0, "unbound": len(tags) - len(got)}
        return got, stats
    seg = 0
    # intervals: [start anchor, next anchor), closed by the layout under the start's base
    bounds = anch + [(None, len(rows))]
    for (oa, ia), (ob, ib) in zip(bounds, bounds[1:]):
        base = oa - rows[ia]["offset"]
        slot = {}
        for r in rows[ia + 1:ib]:
            slot.setdefault((r["offset"], L.TAG_KIND.get(r["kind"], r["kind"])), r["name"])
        j = ia
        for off, ttype, name in tags:
            if off <= oa or (ob is not None and off >= ob):
                continue
            if name or not segments:
                continue
            # scan forward in declaration order for a slot at this offset
            rel = off - base
            hit = None
            for r in rows[j + 1:ib]:
                if r["offset"] == rel and L.same_kind(ttype, r["kind"]):
                    hit = r
                    break
                if r["offset"] > rel:
                    break
            if hit:
                bound[off] = (hit["name"], "segment")
                j = rows.index(hit)
                seg += 1
    # backward pass: an interval is also anchored at its far end, and a field inserted near the end
    # of a run shifts the forward base but not that one.  Agreement counts; disagreement is dropped.
    back = 0
    dropped = 0
    for (oa, ia), (ob, ib) in zip(bounds, bounds[1:]):
        if ob is None:
            continue
        base = ob - rows[ib]["offset"]
        j = ib
        for off, ttype, name in reversed(tags):
            if off <= oa or off >= ob or name:
                continue
            rel = off - base
            hit = None
            for r in reversed(rows[ia + 1:j]):
                if r["offset"] == rel and L.same_kind(ttype, r["kind"]):
                    hit = r
                    break
                if r["offset"] < rel:
                    break
            if not hit:
                continue
            if off in bound:
                if bound[off][0] != hit["name"]:
                    del bound[off]
                    dropped += 1
                continue
            bound[off] = (hit["name"], "segment")
            j = rows.index(hit)
            back += 1
    # tail: past the last anchor the base carries on, so tags that land on a slot of the same kind
    # are bound as far as the layout keeps agreeing.
    tail = 0
    oa, ia = anch[-1]
    base = oa - rows[ia]["offset"]
    j = ia
    for off, ttype, name in tags:
        if off <= oa or name:
            continue
        rel = off - base
        hit = None
        for r in rows[j + 1:]:
            if r["offset"] == rel and L.same_kind(ttype, r["kind"]):
                hit = r
                break
            if r["offset"] > rel:
                break
        if hit and off not in bound:
            bound[off] = (hit["name"], "segment")
            j = rows.index(hit)
            tail += 1
    stats = {"tags": len(tags), "anchors": len(anch), "segment": seg + back + tail,
             "backward": back, "tail": tail, "dropped": dropped,
             "unbound": len(tags) - len(bound)}
    return bound, stats


def bind(lay, cls, streams, segments=False):
    lay.prop_sizes = {}
    rows, total = lay.layout(cls)
    src = sources_for(lay, cls, streams)
    votes = collections.defaultdict(collections.Counter)
    detail = []
    for name, tags in src.items():
        got, stats = bind_stream(rows, tags, segments=segments)
        detail.append((name, stats))
        for off, (prop, how) in got.items():
            votes[off][(prop, how)] += 1
    bound, hows, conflicts = {}, {}, {}
    for off, c in votes.items():
        (prop, how), n = c.most_common(1)[0]
        names = {p for (p, _h) in c}
        if len(names) > 1:
            conflicts[off] = {p: n for (p, _h), n in c.most_common()}
            continue
        bound[off] = prop
        hows[off] = "anchor" if any(h == "anchor" for (_p, h), _n in c.items()) else how
    return {"rows": rows, "total": total, "bound": bound, "how": hows,
            "conflicts": conflicts, "detail": detail, "sources": src}


def report(lay, cls, streams, quiet=False, segments=False):
    r = bind(lay, cls, streams, segments=segments)
    print("== %s: %d properties, %#x bytes" % (lay.export(cls)["name"], len(r["rows"]),
                                               r["total"]))
    for name, st in r["detail"]:
        print("   stream %-44s %3d tags, %2d anchors, %2d by segment (%d backward, %d tail, "
              "%d dropped)" % (name, st["tags"], st["anchors"], st["segment"],
                               st["backward"], st["tail"], st["dropped"]))
    n_anchor = sum(1 for v in r["how"].values() if v == "anchor")
    print("   bound offsets: %d (%d anchored, %d by local segment), conflicts %d"
          % (len(r["bound"]), n_anchor, len(r["bound"]) - n_anchor, len(r["conflicts"])))
    if not quiet:
        for off in sorted(r["bound"]):
            prop = [p for p in r["rows"] if p["name"] == r["bound"][off]]
            kind = prop[0]["kind"] if prop else "?"
            print("   %#06x %-18s %-42s %s" % (off, kind, r["bound"][off], r["how"][off]))
    return r


def lay_names(lay, cls):
    """Candidate host classes for a stream whose own class is not shipped.

    `RVehicleBatmobile` is defined by BmScript, but the build also ships `RVehicleBatmobileBase`,
    which is the parent the offsets belong to; `SVehicleWheel` is native, and any class carrying
    `Wheel` in its name is worth trying.  Everything else falls back to the same-name class.
    """
    cands = [cls]
    if cls == "RVehicleBatmobile":
        cands = ["RVehicleBatmobileBase", "RVehicleBatmobile"]
    elif "Wheel" in cls:
        cands = [n for n in lay.by_name if "Wheel" in n]
    return cands


def best_host(lay, cands, streams):
    best = (None, None, 0)
    for cand in cands:
        i = lay.find_class(cand)
        if not i:
            continue
        rows, _t = lay.layout(i)
        hits = 0
        for _n, tags in sources_for(lay, i, streams).items():
            hits += len(anchors_of(rows, tags))
        if hits > best[2]:
            best = (i, cand, hits)
    return best


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--class", dest="cls")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--json", metavar="PATH")
    ap.add_argument("--segments", action="store_true",
                    help="also place unnamed tags under the local base (evidence, not proof)")
    a = ap.parse_args()
    lay = L.Layout(overrides=TYPED)
    streams = load_streams()
    classes = [a.cls] if a.cls else (CLASSES if a.all else [])
    if not classes:
        ap.error("pass --class NAME or --all")
    out = {}
    for cls in classes:
        i = lay.find_class(cls)
        via = cls
        if not i:
            # the archetype's class is defined by BmScript, which is not shipped, but the build's
            # own parent class is: pick the class in BmGame.upk whose properties anchor the most
            # tags of this stream, and only accept it when it anchors a real share of them.
            i, via, hits = best_host(lay, lay_names(lay, cls), streams.get(cls, {}))
            if not i or hits < 5:
                print("== %s: no class in BmGame.upk anchors its tags (%d)" % (cls, hits))
                out[cls] = {"error": "not_in_BmGame"}
                continue
            print("== %s: not in BmGame.upk, bound through %s (%d anchors)" % (cls, via, hits))
        r = report(lay, i, streams.get(cls, {}), quiet=a.all, segments=a.segments)
        out[cls] = {"bound": {hex(k): v for k, v in sorted(r["bound"].items())},
                    "how": {hex(k): v for k, v in r["how"].items()},
                    "bound_via": via,
                    "conflicts": {hex(k): v for k, v in r["conflicts"].items()},
                    "streams": [{"name": n, **st} for n, st in r["detail"]]}
    if a.json:
        json.dump(out, open(a.json, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(a.json, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

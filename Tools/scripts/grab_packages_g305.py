"""grab_packages_g305.py - the BmAK packages the Batmobile grab never read (G3-05).

The grab's scope was `Playable_Batmobile*_SF` only (`Research/BatmobileGrab/GAPS.md`,
"Excluded packages"). This tool censuses the packages that were named as never read, plus
the `Playable_Batmobile_Std_*_SF` family whose decode coverage GAPS.md reports as 25-50 %:

    Gad_RBatmobileRemoteBm_SF          the remote-control gadget
    Showcase_Batmobiles*               the four showcase levels
    Showcase_UI_Batmobile*             six thumbnail packages
    Startup.upk / StartupPatch.upk     their Batmobile exports only
    Playable_Batmobile_Std_*_SF        seven add-content packages

For each package it records the export census by class, the Batmobile-relevant exports (by
name / owner path / class), the decode status of each of those payloads, and what the package
exports that `Playable_Batmobile_SF` does not.

**Reading the two big packages.** `Startup.upk` (434 869 146 B, 174 890 exports) and
`StartupPatch.upk` (248 812 096 B, 142 232 exports) are chunked: an 18 185 B header prefix,
then one compressed body holding the name/import/export tables *and* the object data. The
image is therefore many times the file, and `upk_read.Package` would decompress all of it.
`PartialPackage` decompresses chunk by chunk and stops as soon as the tables (or, later, the
one payload being read) are inside. `DECODE_BUDGET` bounds how far it will ever go; a payload
past the budget is recorded as not read rather than guessed.

**Decode vocabulary** (byte accounting, not opinion). For one object payload:

    empty              size 2 and the bytes are `0000` - the property-list terminator with no
                       properties behind it; a class-default stub
    untagged           0 tags and 0 bytes consumed: the payload does not begin with a property
                       tag (byte 0 reads as type 0 = end). These are GAPS.md's "native"
                       objects; their format is G3-06's scope, not this card's
    closed_prefix      untagged at byte 0, but a later start closes a stream of >= 2 tags. The
                       tags are recorded verbatim; they are **not** interpreted (which class slot
                       each one is stays open). The 12-byte prefix of the component payloads
                       measured here carries the export's own name index at offset 4, which is
                       checked against the export record's name index
    closed            the tag list terminates exactly at the last byte
    closed_payload    the tag list terminates early; the bytes behind it are the asset payload
                       (texture mips, material expressions), not properties
    closed_terminator the tag list consumed every byte but the final 2-byte `0000` terminator
                       (the walker needs 4 bytes to read a tag, so it reports `eof` 2 bytes short)
    partial           tags were found and the stream did not terminate

`GAPS.md`'s per-package percentage counts **objects with at least one tag**, which is why a
package of zero-property class stubs reads as 25 %. This tool recomputes that same metric and
checks it against the published figure, then reports the byte-accounted status next to it.

Read-only outside its own two outputs. Nothing here launches, attaches to or writes the game.

Usage:
    python Tools/scripts/grab_packages_g305.py --write
    python Tools/scripts/grab_packages_g305.py --check
"""
import argparse
import json
import os
import re
import struct
import sys
import zlib
from collections import Counter, OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(ROOT, "Research", "BatmobileGrab")
sys.path.insert(0, HERE)
import upk_read as U            # noqa: E402
from _lzo1x import lzo1x_decompress  # noqa: E402

COOKED = r"E:\Games\Batman - Arkham Knight\BmGame\CookedPCConsole"
OBJECTS = os.path.join(OUT, "objects.jsonl")
OFFSETS = os.path.join(OUT, "OFFSETS.json")
GAPS = os.path.join(OUT, "GAPS.md")
BASE_PACKAGE = "Playable_Batmobile_SF"

SCHEMA = 1
GENERATOR = "grab_packages_g305.py"

# A package is censused by name. `kind` selects the relevance rule and the verdict wording.
PACKAGES = [
    {"package": "Gad_RBatmobileRemoteBm_SF", "kind": "ui-movie"},
    {"package": "Showcase_Batmobiles", "kind": "level"},
    {"package": "Showcase_Batmobiles_Jokerfied", "kind": "level"},
    {"package": "Showcase_Batmobiles_MK2", "kind": "level"},
    {"package": "Showcase_Batmobiles_Standard", "kind": "level"},
    {"package": "Showcase_UI_Batmobile_SF", "kind": "ui-thumb"},
    {"package": "Showcase_UI_Batmobile_S_SF", "kind": "ui-thumb"},
    {"package": "Showcase_UI_Batmobile1966_SF", "kind": "ui-thumb"},
    {"package": "Showcase_UI_BatmobileJokerfied_SF", "kind": "ui-thumb"},
    {"package": "Showcase_UI_BatmobileMK2_SF", "kind": "ui-thumb"},
    {"package": "Showcase_UI_BatmobilePrototype_SF", "kind": "ui-thumb"},
    {"package": "Startup", "kind": "startup"},
    {"package": "StartupPatch", "kind": "startup"},
    {"package": "Playable_Batmobile_Std_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_1_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_2_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_3_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_4_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_5_SF", "kind": "std"},
    {"package": "Playable_Batmobile_Std_6_SF", "kind": "std"},
]

# GAPS.md's table, verbatim: package -> (objects, decoded) where "decoded" is that file's own
# metric (objects whose tag stream yielded at least one tag). Reproducing it here is the check
# that this tool is looking at the same thing GAPS.md counted.
GAPS_PUBLISHED = {
    "Playable_Batmobile_Std_SF": (4, 1),
    "Playable_Batmobile_Std_1_SF": (4, 2),
    "Playable_Batmobile_Std_2_SF": (4, 2),
    "Playable_Batmobile_Std_3_SF": (4, 2),
    "Playable_Batmobile_Std_4_SF": (4, 2),
    "Playable_Batmobile_Std_5_SF": (4, 2),
    "Playable_Batmobile_Std_6_SF": (92, 80),
}
BASE_EXPORTS_PUBLISHED = 5490

TOKEN_TEXT = r"batmobile|tumbler|jokerfied|interrogation|bml_|_bml"
TOKEN = re.compile(TOKEN_TEXT, re.I)

# How far into a chunked image a payload read may decompress (bytes). The furthest object this
# card needs is a Default__RVehicleBatmobile child at 0x1AE84683; anything past this is recorded
# as not read instead of silently consuming gigabytes.
DECODE_BUDGET = 512 * 1024 * 1024

# The classes whose presence alone makes a package vehicle-relevant, regardless of its names.
VEHICLE_CLASS = re.compile(r"^(RVehicle|RAddContentBatmobile|RBatmobile|SVehicleWheel)")

# The asset classes whose names are worth listing for a package (what it actually carries).
ASSET_CLASSES = ("SkeletalMesh", "SkeletalMeshComponent", "SkeletalMeshSocket", "AnimSet",
                 "AnimSequence", "AnimTree", "AkBank", "RSkeletalMeshActor", "PhysicsAsset",
                 "PhysicsAssetInstance", "PhysicalMaterial", "PostProcessVolume",
                 "PrefabSequence", "Sequence", "RCinematicCameraActor")

# Exports listed per package in the note and the JSON. The counts are always complete; only the
# row list is capped, and the cap is recorded so a reader knows.
LIST_CAP = 400

# Start offsets tried when asking whether an "untagged" payload parses from anywhere. The walker
# tries 0/1/2/4; this is the wider sweep used by the negative result recorded in the note.
START_SWEEP = 20


class PartialPackage(U.Package):
    """A cooked package whose compressed body is decompressed only as far as a reader needs.

    Everything the base class does with names/imports/exports is reused unchanged; only the
    image construction (`_image`) and payload access (`data`) are lazy. A package that is not
    chunked (every small one here) behaves exactly like `upk_read.Package`.
    """

    def _image(self):
        raw = self.raw
        self._chunked = not (raw[self.name_offset:self.name_offset + 4]
                             and self._looks_like_names(raw))
        if not self._chunked:
            self._prefix = raw
            self._body = b""
            self._q = None
            return raw
        start = raw.find(U.PKG_TAG, self.name_offset)
        if start < 0:
            raise U.UpkError("not chunked and the name table is not where the header says")
        self._prefix = raw[:self.name_offset]
        self._q = start
        need = max(self.export_offset + self.export_count * 72,
                   self.import_offset + self.import_count * 28) + 16
        self._body = b""
        self._pump(need - len(self._prefix))
        return self._prefix + self._body

    def _pump(self, want_len):
        """Decompress chunks forward until the body is at least `want_len` bytes."""
        raw = self.raw
        q = self._q
        body = bytearray(self._body)
        while len(body) < want_len and q is not None and q + 16 <= len(raw) \
                and raw[q:q + 4] == U.PKG_TAG:
            block, csize, usize = struct.unpack_from("<III", raw, q + 4)
            if block == 0 and csize == 0 and usize == 0:
                q = None
                break
            p = q + 16
            pairs, total = [], 0
            while total < usize:
                if p + 8 > len(raw):
                    raise U.UpkError("chunk at %#x is truncated" % q)
                bc, bu = struct.unpack_from("<II", raw, p)
                p += 8
                if bc == 0 or bu == 0:
                    raise U.UpkError("zero sub-block in chunk at %#x" % q)
                pairs.append((bc, bu))
                total += bu
            if total != usize:
                raise U.UpkError("chunk at %#x lists %d bytes, header says %d" % (q, total, usize))
            for bc, bu in pairs:
                blob = raw[p:p + bc]
                try:
                    part = zlib.decompress(blob)
                except zlib.error:
                    part = lzo1x_decompress(blob)
                if len(part) != bu:
                    raise U.UpkError("sub-block at %#x decoded to %d, expected %d"
                                     % (p, len(part), bu))
                body += part
                p += bc
            q = p
        self._body = bytes(body)
        self._q = q
        self.image = self._prefix + self._body

    def data(self, index):
        e = self.exports[index - 1]
        end = e["offset"] + e["size"]
        if end > len(self.image):
            if not self._chunked:
                raise U.UpkError("payload past the file end in a non-chunked package")
            if end > DECODE_BUDGET:
                raise U.UpkError("payload ends at %#x, past the %#x decode budget"
                                 % (end, DECODE_BUDGET))
            self._pump(end - len(self._prefix))
        return self.image[e["offset"]:end]


def export_name_index(pkg, index):
    """The name-table index the export record itself stores (ints[3] of its 72-byte row).

    Used as an oracle for `closed_prefix`: a component payload's 12-byte prefix carries this
    number at offset 4, so a matching index proves the prefix is the object's own record and not
    read noise.
    """
    o = pkg.export_offset + (index - 1) * 72 + 12
    return struct.unpack_from("<i", pkg.image, o)[0]


def full_path(pkg, index, depth=0):
    """Owner path of an export or import, following the whole outer chain.

    `upk_read.object_path` prints one level; a class's property objects live under
    `Package.Class`, and a class's own components under `Package.Default__Class`, so the chain
    has to be walked to group them.
    """
    if index == 0 or depth > 16:
        return ""
    if index > 0:
        if index > len(pkg.exports):
            return ""
        e = pkg.exports[index - 1]
        outer = full_path(pkg, e["outer_index"], depth + 1)
        return (outer + "." if outer else "") + e["name"]
    i = -index - 1
    if i >= len(pkg.imports):
        return ""
    imp = pkg.imports[i]
    return (imp["class_package"] + "." if imp["class_package"] else "") + imp["name"]


def match_why(row):
    for field in ("name", "outer", "class"):
        if TOKEN.search(row[field] or ""):
            return field
    return None


def payload_status(pkg, index):
    """(status, tags, consumed, size) for one export payload. See the module docstring."""
    data = pkg.data(index)
    n = len(data)
    if n == 0:
        return "empty", 0, 0, 0
    if n <= 4 and data == b"\x00" * n:
        return "empty", 0, n, n
    tags, end, why = U.best_walk(pkg, data)
    if not tags and end == 0:
        return "untagged", 0, 0, n
    if why == "end":
        return ("closed" if end == n else "closed_payload"), len(tags), end, n
    if why == "eof" and n - end == 2 and data[-2:] == b"\x00\x00":
        return "closed_terminator", len(tags), n, n
    return "partial", len(tags), end, n


def close_at_any_start(pkg, data):
    """First start offset in [0, START_SWEEP) whose walk closes this payload, or None."""
    for start in range(START_SWEEP):
        tags, end, why = U.walk_tags(pkg, data, start)
        if tags and why in ("end", "eof") and end >= len(data) - 2:
            return start, len(tags)
    return None


def load_base():
    """{(name, class)} for every object the grab read from Playable_Batmobile_SF."""
    pairs, rows = set(), 0
    with open(OBJECTS, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("package") != BASE_PACKAGE:
                continue
            rows += 1
            pairs.add((r.get("name"), r.get("class")))
    return pairs, rows


def offsets_field_names():
    doc = json.load(open(OFFSETS, encoding="utf-8"))
    return {f["field_name"] for f in doc["fields"] if f.get("field_name")}, len(doc["fields"])


def census_one(spec, base_pairs, base_rows, offsets_names, offsets_total):
    name, kind = spec["package"], spec["kind"]
    path = os.path.join(COOKED, name + ".upk")
    rec = OrderedDict(package=name, file=name + ".upk", path=path, kind=kind)
    if not os.path.isfile(path):
        rec["error"] = "file not found"
        rec["verdict"] = "not-read"
        return rec
    rec["bytes"] = os.path.getsize(path)
    try:
        pkg = PartialPackage(path)
    except (U.UpkError, OSError) as exc:
        rec["error"] = "%s: %s" % (type(exc).__name__, exc)
        rec["verdict"] = "not-read"
        return rec

    rec["version"] = pkg.version
    rec["licensee"] = pkg.licensee
    rec["names"] = pkg.name_count
    rec["imports"] = pkg.import_count
    rec["exports"] = pkg.export_count
    rec["chunked"] = bool(getattr(pkg, "_chunked", False))
    rec["table_image_bytes"] = len(pkg.image)

    classes = Counter()
    token_all = Counter()
    token_all_n = 0
    vehicles = 0
    violations = 0
    assets = {}
    new_pairs = Counter()
    new_pairs_n = 0
    examples = []
    relevant = []
    owners = Counter()
    owner_classes = {}
    decode = Counter()
    undecoded = []

    for i in range(1, pkg.export_count + 1):
        e = pkg.exports[i - 1]
        cls = pkg.object_class(i) or "?"
        outer = full_path(pkg, e["outer_index"])
        row = {"index": i, "name": e["name"], "class": cls, "outer": outer, "size": e["size"]}
        classes[cls] += 1
        if VEHICLE_CLASS.match(cls):
            vehicles += 1
        if cls in ASSET_CLASSES:
            assets.setdefault(cls, []).append(e["name"])
        why = match_why(row)
        if why:
            token_all[cls] += 1
            token_all_n += 1
        if (e["name"], cls) not in base_pairs:
            new_pairs[cls] += 1
            new_pairs_n += 1
            if len(examples) < 20:
                examples.append({"name": e["name"], "class": cls, "outer": outer})
        take = False
        if kind == "std":
            take, why = True, "all"
        elif kind == "startup":
            # Only the objects BmScript owns: those are the class defaults and functions of the
            # unshipped script package. The other token hits are dialogue/anim/sound objects that
            # merely mention the Batmobile in their name.
            take = bool(why) and outer.startswith("BmScript.")
        elif kind in ("ui-movie", "ui-thumb"):
            # A UI package's own name sits in every owner path inside it, so an owner match says
            # nothing about the car. Only a vehicle class, or an export literally named for the
            # car that is not one of the package's own name stubs, counts here.
            take = bool(VEHICLE_CLASS.match(cls)) or (
                cls != "Package" and bool(TOKEN.search(e["name"])))
            if take:
                why = "class" if VEHICLE_CLASS.match(cls) else "name"
        else:
            take = bool(why)
        if not take:
            continue
        if why not in ("name", "outer", "class", "all"):
            violations += 1
        row["why"] = why
        row["offset"] = e["offset"]
        try:
            status, tags, consumed, size = payload_status(pkg, i)
        except U.UpkError as exc:
            status, tags, consumed, size = "not-read", 0, 0, e["size"]
            row["read_error"] = str(exc)
        row["status"] = status
        row["tags"] = tags
        row["parsed"] = consumed
        if status == "untagged":
            # A wider start sweep can close a stream behind a prefix. Only a stream of two or more
            # tags is taken as a record; a single tag is the coincidence signature (see
            # `close_at_any_start`). The tags are stored, not interpreted.
            try:
                data = pkg.data(i)
            except U.UpkError:
                data = b""
            hit = close_at_any_start(pkg, data) if data else None
            if hit and hit[1] >= 2:
                stream, _end, _why = U.walk_tags(pkg, data, hit[0])
                name_index = export_name_index(pkg, i)
                prefix_index = (struct.unpack_from("<i", data, 4)[0]
                                if len(data) >= 8 else None)
                status = row["status"] = "closed_prefix"
                tags = row["tags"] = len(stream)
                row["prefix"] = hit[0]
                row["prefix_name_index"] = prefix_index
                row["export_name_index"] = name_index
                row["prefix_name_matches"] = prefix_index == name_index
                # type/offset/value only: the offset and the value are unambiguous, while a tag
                # *name* would assert a name-table index this card has not verified.
                row["prefix_tags"] = [
                    {k: t[k] for k in ("type", "offset", "value", "bits", "ref")
                     if k in t} for t in stream[:24]]
        decode[status] += 1
        if status in ("untagged", "partial"):
            undecoded.append({"name": e["name"], "class": cls, "size": e["size"],
                              "status": status, "outer": outer})
        if outer:
            owners[outer] += 1
            owner_classes.setdefault(outer, Counter())[cls] += 1
        relevant.append(row)

    rec["classes"] = dict(classes.most_common())
    rec["class_count"] = len(classes)
    rec["vehicle_class_exports"] = vehicles
    rec["assets"] = {k: v[:40] for k, v in assets.items()}
    rec["rule_violations"] = violations
    rec["relevant"] = {
        "rule": ("every export (this is the add-content package)" if kind == "std" else
                 "class is a vehicle class only, or the export's own name matches /%s/i and is "
                 "not a Package stub (a UI package's own name appears in every owner path inside "
                 "it)" % TOKEN_TEXT if kind in ("ui-movie", "ui-thumb") else
                 "name/owner/class matches /%s/i%s" % (
                     TOKEN_TEXT,
                     "; and the owner path starts with BmScript." if kind == "startup" else "")),
        "count": len(relevant),
        "listed": min(len(relevant), LIST_CAP),
        "by_class": dict(Counter(r["class"] for r in relevant).most_common()),
        "exports": relevant[:LIST_CAP],
    }
    rec["token_all"] = {"count": token_all_n, "by_class": dict(token_all.most_common())}
    rec["adds_over_base"] = {
        "base": BASE_PACKAGE,
        "base_exports": base_rows,
        "all_new_pairs": new_pairs_n,
        "all_new_by_class": dict(new_pairs.most_common(15)),
        "new_relevant_pairs": sum(1 for r in relevant
                                  if (r["name"], r["class"]) not in base_pairs),
        "examples": examples,
    }
    rec["decode"] = {
        "objects": len(relevant),
        "by_status": dict(decode.most_common()),
        "with_tags": sum(1 for r in relevant if r["tags"] > 0),
        "prefixed": [r for r in relevant if r["status"] == "closed_prefix"],
        "prefixed_count": sum(1 for r in relevant if r["status"] == "closed_prefix"),
        "not_read": decode.get("not-read", 0),
        "undecoded": undecoded[:20],
        "undecoded_count": len(undecoded),
    }
    rec["owners"] = [{"outer": o, "exports": n, "classes": dict(owner_classes[o].most_common())}
                     for o, n in owners.most_common()]

    # -------- the package's own verdict, from its census --------
    if kind in ("ui-movie", "ui-thumb"):
        rec["verdict"] = "irrelevant" if not relevant and not vehicles else "relevant"
        rec["note"] = ("%d exports, all UI: %s; %d token hits, all of them the package's own name"
                       % (pkg.export_count,
                          ", ".join("%s×%d" % kv for kv in classes.most_common()),
                          token_all_n))
    elif kind == "level":
        new_assets = [c for c in ("SkeletalMesh", "AnimSet", "AkBank")
                      if any((n, c) not in base_pairs for n in assets.get(c, []))]
        rec["verdict"] = "asset-source" if new_assets else "scene-only"
        rec["note"] = ("level package: %d exports, %d non-Package%s" % (
            pkg.export_count,
            sum(1 for i in range(1, pkg.export_count + 1) if pkg.object_class(i) != "Package"),
            ("; assets absent from %s: %s" % (BASE_PACKAGE, ", ".join(new_assets)))
            if new_assets else "; every asset it carries is also in %s" % BASE_PACKAGE))
    elif kind == "startup":
        rec["verdict"] = "vehicle-class-defaults" if len(relevant) else "irrelevant"
        rec["note"] = ("%d of %d exports are BmScript-owned objects whose name or owner names the "
                       "Batmobile; %d exports anywhere in the package match the token"
                       % (len(relevant), pkg.export_count, token_all_n))
    else:
        rec["verdict"] = "add-content-stub" if pkg.export_count <= 8 else "add-content"
        rec["note"] = ("%d exports; %d carry properties, %d are zero-property class stubs"
                       % (pkg.export_count, sum(1 for r in relevant if r["tags"] > 0),
                          sum(1 for r in relevant if r["status"] == "empty")))

    if kind == "startup":
        rec["startup"] = startup_detail(pkg, relevant, undecoded, offsets_names, offsets_total)
    return rec


def startup_detail(pkg, relevant, undecoded, offsets_names, offsets_total):
    """The BmScript class-default / CDO view of a Startup package."""
    by_owner = OrderedDict()
    for r in relevant:
        by_owner.setdefault(r["outer"], []).append(r)
    groups = []
    for outer in sorted(by_owner, key=lambda o: (-len(by_owner[o]), o)):
        rows = by_owner[outer]
        groups.append({"outer": outer, "exports": len(rows),
                       "classes": dict(Counter(r["class"] for r in rows).most_common()),
                       "status": dict(Counter(r["status"] for r in rows).most_common()),
                       "names": [r["name"] for r in rows]})

    def sweep(rows):
        """How many untagged payloads a wider start sweep closes, and with how many tags.

        A payload whose stream really starts behind a prefix would close with several tags. A
        single-tag close is the signature of a coincidence: one tag whose empty/short payload
        happens to end on the `0000` terminator the object carries anyway.
        """
        closes, multi, examples = 0, 0, []
        for r in rows:
            if r["status"] != "untagged":
                continue
            try:
                data = pkg.data(r["index"])
            except U.UpkError:
                continue
            hit = close_at_any_start(pkg, data)
            if not hit:
                continue
            closes += 1
            if hit[1] > 1:
                multi += 1
                examples.append({"name": r["name"], "class": r["class"], "size": r["size"],
                                 "start": hit[0], "tags": hit[1]})
        return closes, multi, examples

    def props(outer):
        rows = by_owner.get(outer, [])
        names = [r["name"] for r in rows]
        closes, multi, examples = sweep(rows)
        return {"exports": len(rows), "property_names": names,
                "names_not_in_offsets": [n for n in names if n not in offsets_names],
                "by_class": dict(Counter(r["class"] for r in rows).most_common()),
                "status": dict(Counter(r["status"] for r in rows).most_common()),
                "closed_at_any_start": closes, "multi_tag": multi,
                "multi_tag_examples": examples[:5]}

    cdo = by_owner.get("BmScript.Default__RVehicleBatmobile", [])
    closes, multi, examples = sweep(relevant)
    return {
        "class_defaults": {
            "BmScript.RVehicleBatmobile": props("BmScript.RVehicleBatmobile"),
            "BmScript.RBatmobileRemoteBm": props("BmScript.RBatmobileRemoteBm"),
        },
        "cdo_children": [{"name": r["name"], "class": r["class"], "size": r["size"],
                          "status": r["status"]} for r in cdo],
        "groups": groups,
        "untagged": {
            "count": sum(1 for r in relevant if r["status"] == "untagged"),
            "closed_at_any_start": closes,
            "multi_tag": multi,
            "multi_tag_examples": examples[:5],
            "starts_tried": START_SWEEP,
        },
        "offsets_fields_compared": offsets_total,
    }


def build():
    base_pairs, base_rows = load_base()
    offsets_names, offsets_total = offsets_field_names()
    packages = [census_one(spec, base_pairs, base_rows, offsets_names, offsets_total)
                for spec in PACKAGES]

    checks = []

    def check(name, ok, detail=""):
        checks.append({"name": name, "pass": bool(ok), "detail": detail})

    check("every package in the card is on disk at the recorded path",
          all("error" not in p for p in packages),
          "%d/%d read" % (sum(1 for p in packages if "error" not in p), len(packages)))
    check("every package parsed (name/import/export tables) and its class counts add up",
          all("error" in p or sum(p["classes"].values()) == p["exports"] for p in packages),
          ", ".join("%s %d" % (p["package"], p.get("exports", -1)) for p in packages
                    if "error" not in p)[:200])
    check("every relevant row matched the stated rule (or is an all-export package)",
          sum(p.get("rule_violations", 0) for p in packages) == 0,
          "%d violation(s) over %d relevant row(s)" % (
              sum(p.get("rule_violations", 0) for p in packages),
              sum(p.get("relevant", {}).get("count", 0) for p in packages)))
    check("every relevant export carries a decode status (none silently skipped)",
          all(sum(p["decode"]["by_status"].values()) == p["relevant"]["count"]
              for p in packages),
          "; ".join("%s %d/%d" % (p["package"], sum(p["decode"]["by_status"].values()),
                                  p["relevant"]["count"]) for p in packages))
    check("every payload past the decode budget is counted, not decoded",
          all(p["decode"]["not_read"] == p["decode"]["by_status"].get("not-read", 0)
              for p in packages),
          "%d not-read payload(s), all in %s" % (
              sum(p["decode"]["not_read"] for p in packages),
              ", ".join("%s×%d" % (p["package"], p["decode"]["not_read"])
                        for p in packages if p["decode"]["not_read"])))
    check("the base package's object count matches GAPS.md's 5490",
          base_rows == BASE_EXPORTS_PUBLISHED, str(base_rows))

    stds = [p for p in packages if p["kind"] == "std"]
    gaps_ok = [p for p in stds
               if GAPS_PUBLISHED.get(p["package"]) == (p["exports"], p["decode"]["with_tags"])]
    check("recomputing GAPS.md's own metric (objects with >= 1 tag) reproduces its %d Std figures"
          % len(GAPS_PUBLISHED),
          len(stds) == len(GAPS_PUBLISHED) and len(gaps_ok) == len(stds),
          ", ".join("%s %d/%d vs published %s" % (p["package"], p["exports"],
                                                  p["decode"]["with_tags"],
                                                  GAPS_PUBLISHED.get(p["package"]))
                    for p in stds))
    prefixed = [r for p in packages for r in p.get("decode", {}).get("prefixed", [])]
    check("every closed_prefix payload carries the export's own name index in its prefix",
          all(r.get("prefix_name_matches") for r in prefixed),
          "%d payload(s): %s" % (len(prefixed),
                                 ", ".join("%s/%s %d tags" % (r["name"], r["class"], r["tags"])
                                           for r in prefixed[:6])))
    check("no closed_prefix payload's tags are presented as named values (they stay offsets)",
          all("prefix_tags" in r and all("offset" in t for t in r["prefix_tags"])
              for r in prefixed),
          "%d payload(s), %d tags recorded verbatim" % (
              len(prefixed), sum(len(r["prefix_tags"]) for r in prefixed)))
    check("no Std package has an undecoded object left after byte accounting",
          all(p["decode"]["undecoded_count"] == 0 for p in stds),
          ", ".join("%s %d" % (p["package"], p["decode"]["undecoded_count"]) for p in stds))
    check("every Std zero-tag object is a 2-byte `0000` class stub",
          all(r["size"] == 2 and r["status"] == "empty"
              for p in stds for r in p["relevant"]["exports"] if r["tags"] == 0
              and r["status"] != "closed_terminator"),
          "checked %d object(s)" % sum(1 for p in stds for r in p["relevant"]["exports"]
                                       if r["tags"] == 0))

    gad = next(p for p in packages if p["package"] == "Gad_RBatmobileRemoteBm_SF")
    check("Gad_RBatmobileRemoteBm_SF exports no vehicle class and nothing named for the car "
          "outside its own name (it is a movie + its texture)",
          gad["vehicle_class_exports"] == 0 and gad["relevant"]["count"] == 0
          and "SwfMovie" in gad["classes"] and "Texture2D" in gad["classes"],
          "%s; %d token hits" % (", ".join(gad["classes"]), gad["token_all"]["count"]))

    uis = [p for p in packages if p["kind"] == "ui-thumb"]
    check("the six Showcase_UI_Batmobile packages hold the same four real objects",
          len({(p["exports"], tuple(sorted(p["classes"].items()))) for p in uis}) == 1,
          "%d package(s), %s" % (len(uis), sorted(uis[0]["classes"].items())))

    startup = next(p for p in packages if p["package"] == "Startup")
    patch = next(p for p in packages if p["package"] == "StartupPatch")
    sd, pd = startup["startup"], patch["startup"]
    cdp = (sd["class_defaults"]["BmScript.RVehicleBatmobile"],
           sd["class_defaults"]["BmScript.RBatmobileRemoteBm"],
           pd["class_defaults"]["BmScript.RBatmobileRemoteBm"])
    check("Startup carries the RVehicleBatmobile class-default properties (97 exports)",
          sd["class_defaults"]["BmScript.RVehicleBatmobile"]["exports"] == 97,
          str(sd["class_defaults"]["BmScript.RVehicleBatmobile"]["exports"]))
    check("Startup carries the Default__RVehicleBatmobile components (37 exports)",
          len(sd["cdo_children"]) == 37, str(len(sd["cdo_children"])))
    check("StartupPatch carries no RVehicleBatmobile class defaults (the patch does not "
          "redefine the class)",
          pd["class_defaults"]["BmScript.RVehicleBatmobile"]["exports"] == 0,
          str(pd["class_defaults"]["BmScript.RVehicleBatmobile"]["exports"]))
    check("the class-default payloads yield no property stream: a start sweep finds only "
          "single-tag coincidences",
          all(v["multi_tag"] == 0 for v in cdp),
          "; ".join("%d close at some start of %d untagged, %d with more than one tag"
                    % (v["closed_at_any_start"], v["status"].get("untagged", 0), v["multi_tag"])
                    for v in cdp))
    check("the remote-gadget property names are the same set in both packages",
          set(sd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["property_names"]) ==
          set(pd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["property_names"]),
          "Startup %d, StartupPatch %d, symmetric difference %d" % (
              sd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["exports"],
              pd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["exports"],
              len(set(sd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["property_names"]) ^
                  set(pd["class_defaults"]["BmScript.RBatmobileRemoteBm"]["property_names"]))))

    levels = [p for p in packages if p["kind"] == "level"]
    empty_level = next(p for p in levels if p["package"] == "Showcase_Batmobiles")
    populated = [p for p in levels if p is not empty_level]
    check("the three populated showcase levels each export exactly one SkeletalMesh and one "
          "AnimSet",
          all(p["classes"].get("SkeletalMesh") == 1 and p["classes"].get("AnimSet") == 1
              for p in populated),
          ", ".join("%s %s/%s" % (p["package"], p["classes"].get("SkeletalMesh"),
                                  p["classes"].get("AnimSet")) for p in populated))
    check("each populated level's SkeletalMesh is a mesh the base package does not carry",
          all(p["verdict"] == "asset-source" for p in populated),
          ", ".join("%s %s" % (p["package"], p["assets"].get("SkeletalMesh")) for p in populated))
    check("Showcase_Batmobiles.upk is an empty level (no mesh, anim set, bank or actor)",
          empty_level["exports"] == 6
          and not any(c in empty_level["classes"] for c in
                      ("SkeletalMesh", "AnimSet", "AkBank", "RSkeletalMeshActor")),
          "%d exports: %s" % (empty_level["exports"], ", ".join(empty_level["classes"])))
    check("every undecoded relevant payload sits in a Startup package (the class-default "
          "format); the asset, level, UI and Std packages decode completely",
          all(p["decode"]["undecoded_count"] + p["decode"]["not_read"] == 0
              for p in packages if p["kind"] != "startup"),
          ", ".join("%s %d+%d" % (p["package"], p["decode"]["undecoded_count"],
                                  p["decode"]["not_read"])
                    for p in packages if p["kind"] != "startup"))

    summary = {
        "packages": len(packages),
        "read": sum(1 for p in packages if "error" not in p),
        "exports_total": sum(p.get("exports", 0) for p in packages),
        "relevant_total": sum(p.get("relevant", {}).get("count", 0) for p in packages),
        "undecoded_total": sum(p.get("decode", {}).get("undecoded_count", 0) for p in packages),
        "not_read_total": sum(p.get("decode", {}).get("not_read", 0) for p in packages),
        "verdicts": dict(Counter(p["verdict"] for p in packages).most_common()),
        "by_kind": dict(Counter(p["kind"] for p in packages).most_common()),
        "std_exports": sum(p["exports"] for p in stds),
        "std_undecoded": sum(p["decode"]["undecoded_count"] for p in stds),
    }
    return {
        "schema": SCHEMA,
        "generated_by": GENERATOR,
        "scope": ("the packages GAPS.md lists as excluded and never read, plus the "
                  "Playable_Batmobile_Std_*_SF decode coverage question"),
        "rules": {
            "token": TOKEN_TEXT,
            "startup_owner_prefix": "BmScript.",
            "status_vocabulary": {
                "empty": "2-byte `0000` payload: the property-list terminator, no properties",
                "untagged": "0 tags and 0 bytes consumed; the payload is not a tag stream "
                            "(GAPS.md's native objects, G3-06 scope)",
                "closed": "the tag list terminates on the last byte",
                "closed_payload": "the tag list terminates early; asset bytes follow",
                "closed_terminator": "everything but the final 2-byte `0000` terminator parsed",
                "closed_prefix": "untagged at byte 0; a later start closes a >= 2-tag stream, "
                                 "recorded verbatim and not interpreted",
                "partial": "tags found, stream not terminated",
            },
            "decode_budget_bytes": DECODE_BUDGET,
            "start_sweep": START_SWEEP,
        },
        "base": {"package": BASE_PACKAGE, "exports": base_rows},
        "offsets_json": {"fields": offsets_total, "named": len(offsets_names)},
        "summary": summary,
        "packages": packages,
        "checks": checks,
    }


def fmt_int(n):
    return "{:,}".format(n) if isinstance(n, int) else str(n)


def md_census_table(p):
    lines = ["| class | exports |", "|---|---:|"]
    for cls, n in p["classes"].items():
        lines.append("| %s | %d |" % (cls, n))
    return lines


def md_relevant_table(p, limit=120):
    rows = p["relevant"]["exports"]
    lines = ["| # | export | class | owner | size | status | tags | matched by |",
             "|---:|---|---|---|---:|---|---:|---|"]
    for r in rows[:limit]:
        lines.append("| %d | `%s` | %s | %s | %d | %s | %d | %s |" % (
            r["index"], r["name"], r["class"], r["outer"] or "—", r["size"],
            r["status"], r["tags"], r["why"]))
    return lines


def write_md(doc):
    s = doc["summary"]
    L = []
    a = L.append
    a("# BmAK packages the Batmobile grab never read (G3-05)")
    a("")
    a("Generated by `Tools/scripts/grab_packages_g305.py` from the packages themselves. The grab's")
    a("scope was `Playable_Batmobile*_SF`; `GAPS.md` lists the rest as excluded and never read.")
    a("The card asks for each of them: exports by class, the Batmobile-relevant exports (by name /")
    a("owner / class), and what they add over `Playable_Batmobile_SF` - or the census that shows the")
    a("package is irrelevant. Nothing here is inferred from Arkham Knight, UE3 or JC3 knowledge.")
    a("")
    a("**Method.** Names, imports and exports come from the package's own tables, read with")
    a("`Tools/scripts/upk_read.py`. `Startup.upk` and `StartupPatch.upk` are chunked with their tables")
    a("inside the compressed body, so this tool decompresses chunk by chunk and stops as soon as the")
    a("bytes a reader needs are inside (`PartialPackage`); payloads are read only for the exports named")
    a("below. Every payload is classified by byte accounting (closed / closed_payload /")
    a("closed_terminator / empty / untagged / partial), never by \"looks right\".")
    a("")
    a("| fact | value |")
    a("|---|---|")
    a("| packages censused | **%d** (%d read) |" % (s["packages"], s["read"]))
    a("| exports across them | **%s** |" % fmt_int(s["exports_total"]))
    a("| Batmobile-relevant exports | **%s** |" % fmt_int(s["relevant_total"]))
    a("| relevant payloads left undecoded | **%s** (+%d past the decode budget) |"
      % (fmt_int(s["undecoded_total"]), s["not_read_total"]))
    a("| Playable_Batmobile_Std_* exports / undecoded | %d / %d |"
      % (s["std_exports"], s["std_undecoded"]))
    a("")
    a("| package | kind | exports | classes | relevant | undecoded | verdict |")
    a("|---|---|---:|---:|---:|---:|---|")
    for p in doc["packages"]:
        if "error" in p:
            a("| `%s` | %s | — | — | — | — | **%s** (%s) |"
              % (p["package"], p["kind"], p["verdict"], p["error"]))
            continue
        a("| `%s` | %s | %s | %d | %s | %d | **%s** |" % (
            p["package"], p["kind"], fmt_int(p["exports"]), p["class_count"],
            fmt_int(p["relevant"]["count"]), p["decode"]["undecoded_count"], p["verdict"]))
    a("")

    # ---- 1. Gad ----
    a("## 1. `Gad_RBatmobileRemoteBm_SF` - the remote-control gadget is a screen, not the gadget")
    p = next(x for x in doc["packages"] if x["package"] == "Gad_RBatmobileRemoteBm_SF")
    a("")
    a("%s B, %d exports, %d imports." % (fmt_int(p["bytes"]), p["exports"], p["imports"]))
    a("")
    L.extend(md_census_table(p))
    a("")
    a("The package contains a `SwfMovie` and one `Texture2D` - a Scaleform screen - and **no**")
    a("export of any vehicle class (`RVehicle*`, `RBatmobile*`, `RAddContentBatmobile*`): **%d**."
      % p["vehicle_class_exports"])
    a("Exports named for the car that are not one of the package's own name stubs: **%d**. The %d"
      % (p["relevant"]["count"], p["token_all"]["count"]))
    a("token hits in the package are its own name appearing in owner paths and in its `Package`")
    a("exports: %s." % ", ".join("%s×%s" % kv for kv in p["token_all"]["by_class"].items()))
    a("")
    a("The gadget's *parameters* are not here. They are class defaults in `Startup.upk` under")
    a("`BmScript.RBatmobileRemoteBm` (48 property objects, section 5), whose class the unshipped")
    a("`BmScript` package defines. What this package adds is the on-screen UI of that gadget.")
    a("")

    # ---- 2. levels ----
    a("## 2. `Showcase_Batmobiles*` - four levels, not vehicle assets")
    a("")
    for p in [x for x in doc["packages"] if x["kind"] == "level"]:
        a("### `%s`" % p["package"])
        a("")
        a("%s B, %d exports (%d non-Package), %d classes. Batmobile-relevant exports: **%d**."
          % (fmt_int(p["bytes"]), p["exports"],
             p["exports"] - p["classes"].get("Package", 0), p["class_count"],
             p["relevant"]["count"]))
        a("")
        L.extend(md_census_table(p))
        a("")
        single = [(i, r) for i, r in enumerate(p["relevant"]["exports"])
                  if r["class"] in ("PhysicalMaterial", "PostProcessVolume", "PrefabSequence",
                                    "Sequence", "RCinematicCameraActor", "RBMScreenShakeModifier",
                                    "RCameraOverlayPlayer", "Level", "World")]
        if p["assets"]:
            a("The assets it owns (every export of these classes, by name):")
            a("")
            a("| class | exports | names |")
            a("|---|---:|---|")
            for cls, names in p["assets"].items():
                uniq = Counter(names)
                shown = [n if uniq[n] == 1 else "%s (×%d)" % (n, uniq[n])
                         for n in list(uniq)[:8]]
                a("| %s | %d | %s |" % (cls, len(names),
                                        ", ".join("`%s`" % s for s in shown)
                                        + (" …" if len(uniq) > 8 else "")))
            a("")
        if single:
            a("The scene's single-instance objects:")
            a("")
            a("| export | class | owner |")
            a("|---|---|---|")
            for _i, r in single[:20]:
                a("| `%s` | %s | %s |" % (r["name"], r["class"], r["outer"] or "—"))
            a("")
        mesh = p["assets"].get("SkeletalMesh") or []
        bank = p["assets"].get("AkBank") or []
        actors = p["classes"].get("RSkeletalMeshActor", 0)
        clauses = ["%d `RSkeletalMeshActor`" % actors if actors else "no `RSkeletalMeshActor`",
                   ("mesh `%s`" % mesh[0]) if mesh else "no `SkeletalMesh`",
                   ("bank `%s`" % bank[0]) if bank else "no `AkBank`"]
        for cls in ("AnimSet", "PhysicsAsset", "PrefabSequence", "Sequence"):
            if p["assets"].get(cls):
                clauses.append("%s %s" % (cls, ", ".join("`%s`" % n
                                                        for n in p["assets"][cls][:2])))
        a("What it adds over `Playable_Batmobile_SF`: %s new export `(name, class)` pairs. The"
          % fmt_int(p["adds_over_base"]["all_new_pairs"]))
        a("level carries %s." % "; ".join(clauses))
        a("The vehicle it shows is an instance of an archetype in another package: **no**")
        a("`RVehicleBatmobile`/`RAddContentBatmobileMesh` export is in the package (confirmed by the")
        a("class census above).")
        a("")

    # ---- 3. UI ----
    a("## 3. `Showcase_UI_Batmobile*` - six thumbnail packages")
    a("")
    a("| package | bytes | exports | classes |")
    a("|---|---:|---:|---|")
    for p in [x for x in doc["packages"] if x["kind"] == "ui-thumb"]:
        a("| `%s` | %s | %d | %s |" % (p["package"], fmt_int(p["bytes"]), p["exports"],
                                       ", ".join("%s×%d" % kv for kv in p["classes"].items())))
    a("")
    a("All six hold the **same four real objects**: an `ObjectReferencer`, a `SwfMovie` named")
    a("`Thumb` and a `Texture2D` named `Thumb_I1`. Batmobile-relevant exports: **0** in every one;")
    a("no vehicle class appears. They add nothing to the vehicle - they are the Batmobile's")
    a("thumbnail in a menu.")
    a("")

    # ---- 4. Startup ----
    a("## 4. `Startup.upk` / `StartupPatch.upk` - the Batmobile class defaults")
    a("")
    a("These two are the whole install's startup packages (174 890 and 142 232 exports). The")
    a("Batmobile-relevant part is the `BmScript` branch: the class default property objects of the")
    a("drivable vehicle class, its CDO's components, the remote-gadget class, and the Kismet")
    a("actions that drive the car.")
    a("")
    a("| package | bytes | exports | token hits anywhere | BmScript-owned, Batmobile-named |")
    a("|---|---:|---:|---:|---:|")
    for p in [x for x in doc["packages"] if x["kind"] == "startup"]:
        a("| `%s` | %s | %s | %s | **%s** |" % (
            p["package"], fmt_int(p["bytes"]), fmt_int(p["exports"]),
            fmt_int(p["token_all"]["count"]), fmt_int(p["relevant"]["count"])))
    a("")
    a("Only the `BmScript`-owned rows are decoded here. The rest of the token hits are dialogue,")
    a("animation and sound objects whose names mention the Batmobile")
    a("(`%s`); they are counted, not read - they cannot change the car's numbers." %
      ", ".join("%s×%s" % kv for kv in
                list(next(x for x in doc["packages"] if x["package"] == "Startup")
                     ["token_all"]["by_class"].items())[:6]))
    a("")
    for p in [x for x in doc["packages"] if x["kind"] == "startup"]:
        d = p["startup"]
        a("### `%s.upk`" % p["package"])
        a("")
        a("BmScript owners, by export count (owner = the export's full outer path):")
        a("")
        a("| owner | exports | classes | decode status |")
        a("|---|---:|---|---|")
        for g in d["groups"]:
            a("| `%s` | %d | %s | %s |" % (g["outer"], g["exports"],
                                           ", ".join("%s×%d" % kv for kv in g["classes"].items()),
                                           ", ".join("%s×%d" % kv for kv in g["status"].items())))
        a("")
        cd = d["class_defaults"]
        for owner in ("BmScript.RVehicleBatmobile", "BmScript.RBatmobileRemoteBm"):
            v = cd[owner]
            if not v["exports"]:
                a("**`%s`**: no export in this package." % owner)
                a("")
                continue
            a("**`%s`** - %d property objects, classes %s, decode %s."
              % (owner, v["exports"], ", ".join("%s×%d" % kv for kv in v["by_class"].items()),
                 ", ".join("%s×%d" % kv for kv in v["status"].items())))
            a("")
            names = v["property_names"]
            new = v["names_not_in_offsets"]
            a("Property names (%d), as the exports spell them:" % len(names))
            a("")
            for i in range(0, len(names), 4):
                a("`" + "` `".join(names[i:i + 4]) + "`")
                a("")
            a("%d of these names do not appear as a field name in `OFFSETS.json` (which resolved the"
              % len(new))
            a("names of the tags the *archetypes* carry out of the BmSDK-AK dump): %s."
              % (", ".join("`%s`" % n for n in new[:24]) + (" …" if len(new) > 24 else "")
                 if new else "none"))
            a("")
        if d["cdo_children"]:
            a("**`BmScript.Default__RVehicleBatmobile`** - %d components the class default object"
              % len(d["cdo_children"]))
            a("carries:") 
            a("")
            a("| component | class | size | decode status |")
            a("|---|---|---:|---|")
            for c in d["cdo_children"]:
                a("| `%s` | %s | %d | %s |" % (c["name"], c["class"], c["size"], c["status"]))
            a("")
            a("This is the class-default *component set* G3-01 was asked for (the two collision")
            a("cylinders among them), now sourced to a file: `Startup.upk` export names under")
            a("`BmScript.Default__RVehicleBatmobile`. Their payloads do **not** decode from byte 0")
            a("(see UNKNOWNs), so the cylinders' radius/height are still not read.")
            a("")
    a("**Two payload shapes hide behind \"untagged\", and the sweep separates them.**")
    a("")
    a("1. **The 30-byte class-default property objects do not parse.** Byte 0 reads as `int16 0`,")
    a("   the property-list terminator, so the walk that resolves every other object in the grab")
    a("   stops at once (0 tags, 0 bytes). Sweeping start offsets 0..%d closes %d of the %d"
      % (doc["rules"]["start_sweep"] - 1,
         next(x for x in doc["packages"] if x["package"] == "Startup")
         ["startup"]["class_defaults"]["BmScript.RVehicleBatmobile"]["closed_at_any_start"] +
         next(x for x in doc["packages"] if x["package"] == "Startup")
         ["startup"]["class_defaults"]["BmScript.RBatmobileRemoteBm"]["closed_at_any_start"],
         next(x for x in doc["packages"] if x["package"] == "Startup")
         ["startup"]["class_defaults"]["BmScript.RVehicleBatmobile"]["status"].get("untagged", 0) +
         next(x for x in doc["packages"] if x["package"] == "Startup")
         ["startup"]["class_defaults"]["BmScript.RBatmobileRemoteBm"]["status"].get(
             "untagged", 0)))
    a("   `RVehicleBatmobile` + `RBatmobileRemoteBm` payloads, and **every close is a single**")
    a("   `ByteProperty` at offset `0x0000` with an empty payload - a payload that happens to end")
    a("   on the `0000` terminator the object carries, not a property stream. No value is taken")
    a("   from them; the names are the deliverable.")
    a("2. **The component payloads are a record with a 12-byte prefix.** %d Startup payloads and"
      % next(x for x in doc["packages"] if x["package"] == "Startup")
      ["decode"]["prefixed_count"])
    a("   %d StartupPatch payloads close a **two-tag** stream from start 12. That prefix is the"
      % next(x for x in doc["packages"] if x["package"] == "StartupPatch")
      ["decode"]["prefixed_count"])
    a("   object's own record: its `int32` at offset 4 equals the export record's name index on")
    a("   every one of them (checked against the export table - `0x64E3` = "
      "`FrontCollisionCylinder`,")
    a("   `0xDB8E` = `RearCollisionCylinder`). The tags behind it are recorded verbatim in the")
    a("   JSON and are **not interpreted**: which class slot each offset is - and therefore what")
    a("   the cylinder dimensions are - is G3-01's question, not this census's.")
    a("")

    # ---- 5. Std coverage ----
    a("## 5. `Playable_Batmobile_Std_*_SF` - the 25-50 % coverage is a counting artifact")
    a("")
    a("`GAPS.md` reports these packages at 25-50 % decoded. Its metric is **objects whose tag")
    a("stream yielded at least one tag**, so an object that has no properties at all counts as")
    a("undecoded. This tool recomputes that metric and prints it next to the byte-accounted status:")
    a("")
    a("| package | exports | GAPS.md decoded | recomputed (>=1 tag) | empty | closed | closed_terminator | undecoded |")
    a("|---|---:|---|---:|---:|---:|---:|---:|")
    for p in [x for x in doc["packages"] if x["kind"] == "std"]:
        st = p["decode"]["by_status"]
        published = GAPS_PUBLISHED.get(p["package"], (0, 0))
        a("| `%s` | %d | %d / %d | **%d** | %d | %d | %d | **%d** |" % (
            p["package"], p["exports"], published[1], published[0],
            p["decode"]["with_tags"], st.get("empty", 0), st.get("closed", 0),
            st.get("closed_terminator", 0), p["decode"]["undecoded_count"]))
    a("")
    a("The recomputed column reproduces every published figure exactly (checked below), which is")
    a("what identifies the metric. Every object that GAPS.md's metric calls undecoded is one of:")
    a("")
    a("- a **2-byte `0000` payload** - the property-list terminator with no properties behind it, a")
    a("  class-default stub (`Package` entries, empty `RAddContentBatmobileMesh`). There is nothing")
    a("  to decode;")
    a("- an **`ObjectReferencer`** whose tag list closes on the 2-byte terminator the walker cannot")
    a("  read back (it needs 4 bytes to read a tag), reported as `eof` 2 bytes short;")
    a("- in `Std_6`, real payloads whose tag list closes and where the bytes behind it are the")
    a("  asset's own data (texture mips, material expressions, a 124-byte")
    a("  `RAddContentBatmobileMesh`).")
    a("")
    a("So **no** object in these packages is undecoded: %d exports, %d undecoded."
      % (s["std_exports"], s["std_undecoded"]))
    a("")
    p6 = next(x for x in doc["packages"] if x["package"] == "Playable_Batmobile_Std_6_SF")
    a("`Std_6` is the only one with substance (%d exports): %s." %
      (p6["exports"], ", ".join("%s×%d" % kv for kv in p6["classes"].items())))
    a("")

    # ---- 6. adds ----
    a("## 6. What each package adds over `Playable_Batmobile_SF`")
    a("")
    a("Counted as export `(name, class)` pairs that the base package's %s objects do not contain."
      % fmt_int(doc["base"]["exports"]))
    a("")
    a("| package | new pairs | of which relevant | new classes (top) |")
    a("|---|---:|---:|---|")
    for p in doc["packages"]:
        if "error" in p:
            continue
        a("| `%s` | %s | %s | %s |" % (
            p["package"], fmt_int(p["adds_over_base"]["all_new_pairs"]),
            fmt_int(p["adds_over_base"]["new_relevant_pairs"]),
            ", ".join("%s×%s" % kv for kv in
                      list(p["adds_over_base"]["all_new_by_class"].items())[:5])))
    a("")

    # ---- 7. UNKNOWNs ----
    a("## 7. UNKNOWN")
    a("")
    a("These stay UNKNOWN. Each names what was tried and where the value would be.")
    a("")
    a("| # | unknown | what was tried | where it would be found |")
    a("|---|---|---|---|")
    su = next(x for x in doc["packages"] if x["package"] == "Startup")["startup"]
    a("| U-1 | the values of the `BmScript.RVehicleBatmobile` class-default properties (%d objects) "
      "| walked each 30-byte payload with the grab's tag walker: byte 0 reads as `int16 0`, the "
      "terminator, so 0 tags and 0 bytes consumed; of the %d objects whose payload never parses, a "
      "0..%d start sweep closes %d and every close is a single `ByteProperty` at offset 0 - a "
      "coincidence, not a stream | the untagged-object format, G3-06 (`REMAINDER.md`); the same "
      "shape as `GAPS.md`'s native objects |"
      % (su["class_defaults"]["BmScript.RVehicleBatmobile"]["exports"],
         su["class_defaults"]["BmScript.RVehicleBatmobile"]["status"].get("untagged", 0),
         doc["rules"]["start_sweep"] - 1,
         su["class_defaults"]["BmScript.RVehicleBatmobile"]["closed_at_any_start"]))
    a("| U-2 | the values of the `BmScript.RBatmobileRemoteBm` gadget parameters (%d objects: "
      "`CursorSpeed`, `MaxAimX/Y`, `JammerTime`, …) | same walk, same result - only the names decode "
      "| same as U-1 |" % next(x for x in doc["packages"] if x["package"] == "Startup")["startup"]
      ["class_defaults"]["BmScript.RBatmobileRemoteBm"]["exports"])
    cyl = [r for p in doc["packages"] if p["package"] == "Startup"
           for r in p["decode"]["prefixed"]
           if r["name"] in ("FrontCollisionCylinder", "RearCollisionCylinder")]
    a("| U-3 | the two collision cylinders' radius/height (`FrontCollisionCylinder`, "
      "`RearCollisionCylinder`) | both are 46-byte payloads that read as `int16 0` at byte 0; a "
      "start sweep closes each from byte 12 with two tags, whose prefix carries the export's own "
      "name index (%s). The tags are recorded, not adopted: the stream says an empty "
      "`ObjectProperty` at `0x013C` and one float at `0x016C`, and nothing in the package says "
      "which `CylinderComponent` slot `0x016C` is | the BmSDK-AK layout for `CylinderComponent` "
      "(G3-06), then G3-01 owns the values |"
      % (", ".join("%s: %s" % (r["name"], "name index matches"
                                if r["prefix_name_matches"] else "MISMATCH") for r in cyl)
         or "no such row"))
    a("| U-4 | whether `StartupPatch.upk` overrides any value `Startup.upk` carries | the property "
      "*name* sets are compared and agree; payloads decode in neither package | U-1 format first, "
      "then a diff of the decoded defaults |")
    a("| U-5 | which of the %s non-`BmScript` token hits in `Startup.upk` can affect the drivable "
      "car | counted by class, not read (dialogue, animation, sound) | a name-level read would not "
      "show influence; it needs a runtime oracle (G3-07) |"
      % fmt_int(next(x for x in doc["packages"] if x["package"] == "Startup")["token_all"]["count"]
                - next(x for x in doc["packages"] if x["package"] == "Startup")
                ["relevant"]["count"]))
    a("| U-6 | whether the game loads `Gad_RBatmobileRemoteBm_SF`'s `SwfMovie` for the remote "
      "gadget, or the showcase levels' bank, at the times this project cares about | the census "
      "shows what the files hold, not what the game binds at runtime | G3-07 (read-only runtime "
      "oracle) |")
    a("| U-7 | %d relevant `Startup` payloads that end past the %d MiB decode budget | recorded as "
      "`not-read`, not walked (decompressing further would need the full image) | the same objects, "
      "read once the budget is raised or a random-access chunk index exists |"
      % (next(x for x in doc["packages"] if x["package"] == "Startup")["decode"]["not_read"],
         doc["rules"]["decode_budget_bytes"] // (1024 * 1024)))
    a("")

    # ---- 8. checks ----
    a("## 8. Checks")
    a("")
    a("| check | result | detail |")
    a("|---|---|---|")
    for c in doc["checks"]:
        a("| %s | %s | %s |" % (c["name"], "PASS" if c["pass"] else "FAIL",
                                str(c["detail"]).replace("|", "/")))
    a("")
    a("%d/%d checks passed." % (sum(1 for c in doc["checks"] if c["pass"]), len(doc["checks"])))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="write PACKAGES_G305.json and .md")
    ap.add_argument("--check", action="store_true",
                    help="re-read every package and compare with the record on disk")
    args = ap.parse_args()
    if not args.write and not args.check:
        args.check = True

    doc = build()
    json_path = os.path.join(OUT, "PACKAGES_G305.json")
    md_path = os.path.join(OUT, "PACKAGES_G305.md")
    md = write_md(doc)

    if args.write:
        with open(json_path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, indent=1, sort_keys=True)
            fh.write("\n")
        with open(md_path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(md)
        print("wrote PACKAGES_G305.json and PACKAGES_G305.md (%d packages, %d exports)"
              % (doc["summary"]["packages"], doc["summary"]["exports_total"]))
        return 0

    problems = [c for c in doc["checks"] if not c["pass"]]
    if not os.path.isfile(json_path) or not os.path.isfile(md_path):
        print("MISSING: run --write")
        return 1
    with open(json_path, encoding="utf-8") as fh:
        if json.load(fh) != json.loads(json.dumps(doc, sort_keys=True)):
            print("STALE: PACKAGES_G305.json does not match a fresh build (run --write)")
            return 1
    if open(md_path, encoding="utf-8").read() != md:
        print("STALE: PACKAGES_G305.md does not match a fresh render (run --write)")
        return 1
    if problems:
        for c in problems:
            print("FAIL %s: %s" % (c["name"], c["detail"]))
        return 1
    print("OK: %d packages, %s exports, %s relevant, %d undecoded; %d/%d checks; md byte-identical"
          % (doc["summary"]["packages"], fmt_int(doc["summary"]["exports_total"]),
             fmt_int(doc["summary"]["relevant_total"]), doc["summary"]["undecoded_total"],
             len(doc["checks"]), len(doc["checks"])))
    return 0


if __name__ == "__main__":
    sys.exit(main())

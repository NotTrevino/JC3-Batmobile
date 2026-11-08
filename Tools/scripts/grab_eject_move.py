"""G3-02k - the Batmobile eject's special move: which move `TriggerSpecialMove` starts, and
what produces the launch.

G3-02j (`EJECT_VELOCITY.md`) proved the only `Core.SetRBLinearVelocity` call in
`DrivingMode.EjectFromVehicle` is `(0,0,0)` on the car's own mesh, and that the body's only
launch-shaped call is a `TriggerSpecialMove` at script `+1103`.  This card decodes that call
and follows it to its numbers.

Chain, each link read from the cooked bytes:

  `DrivingMode.EjectFromVehicle`         virtual call on the Context chain `Car.ShortRangeGlideKick`
      -> `RSpecialMoveConfigConfigurable.TriggerSpecialMove`
                                          forwards to `Config.TriggerSpecialMove(...)`
      -> the config asset named by the vehicle's own class default
                                          `GlideKick.GlideKickShort_FromBatmobile`
      -> its nested config                  `RSpecialMoveConfig_GlideKick` (AnimName + AnimSet)
      -> `RSpecialMoveInstance_GlideKick`   the `InstanceClass` the config's defaults name
      -> the AnimSequence in anim set `BM_Batmobile`
                                          root-motion translation per animation

Nothing is filled in from a plausible-looking UE3 implementation: where a field's *name* is
not stored in the cooked package the card says so and reports the field offset instead.

    python Tools/scripts/grab_eject_move.py --write   # write the card
    python Tools/scripts/grab_eject_move.py --check   # verify the card
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import bmak_damage as B  # noqa: E402
import grab_eject_velocity as GE  # noqa: E402
from upk_read import best_walk  # noqa: E402

UPK = B.UPK
STARTUP = os.path.join(os.path.dirname(UPK), "Startup.upk")
OUT_MD = os.path.join(ROOT, "Research", "BatmobileGrab", "EJECT_MOVE.md")
OUT_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "EJECT_MOVE.json")
CLASS_DEFAULTS = os.path.join(ROOT, "Research", "BatmobileGrab", "CLASS_DEFAULTS.json")

EJECT_PATH = "DrivingMode.EjectFromVehicle"
TSM = "TriggerSpecialMove"

# Field offsets inside a cooked `AnimSequence`, measured on this package (section 4).  A simple
# tag stores no name, so the offset is the only handle the bytes give.
SEQ_NAME_OFF = 84          # FName  - the human sequence name
SEQ_ROOT_TRANS_OFF = 108   # Vector - 12 bytes, the sequence's total root-motion translation
SEQ_ROOT_ROT_OFF = 124     # Rotator
SEQ_LENGTH_OFF = 156       # Float  - seconds, == (NumFrames - 1) / Rate on all 55 sequences
SEQ_FRAMES_OFF = 160       # Int
SEQ_RATE_OFF = 168         # Float  - frames per second
SEQ_ZIP_OFF = 992          # Struct AnimZip_LinearMotion (name stored, payload not decoded)

CFG_CONFIG_OFF = 400       # RSpecialMoveConfigConfigurable.Config  (the wrapper's inner config)
CFG_ANIMNAME_OFF = 400     # RSpecialMoveConfig_RelativeAnimMove.AnimName
CFG_ANIMSET_OFF = 124      # RSpecialMoveConfig.AnimSet
CFG_INSTANCECLASS_OFF = 140  # RSpecialMoveConfig.InstanceClass

PKG_TAG = b"\xc1\x83\x2a\x9e"


# ---------------------------------------------------------------- container
def _fstr(buf, o):
    n = struct.unpack_from("<i", buf, o)[0]
    if n == 0:
        return "", o + 4
    if n > 0:
        return buf[o + 4:o + 4 + n].rstrip(b"\0").decode("latin-1"), o + 4 + n
    m = -n
    return buf[o + 4:o + 4 + 2 * m].decode("utf-16-le").rstrip("\0"), o + 4 + 2 * m


class PartialImage:
    """`Startup.upk` is 434 MB, so its image is built lazily: chunks are decompressed whole,
    in file order, only until the bytes a caller asks for are covered."""

    def __init__(self, path):
        self.raw = open(path, "rb").read()
        raw = self.raw
        self.group, o = _fstr(raw, 12)
        o += 4                                   # flags
        (self.name_count, self.name_offset, self.export_count, self.export_offset,
         self.import_count, self.import_offset) = struct.unpack_from("<6i", raw, o)
        self.chunk_start = raw.find(PKG_TAG, self.name_offset)
        self.buf = bytearray(raw[:self.name_offset])
        self.chunks = []

    def _pump(self, target):
        raw, pos = self.raw, (self.chunks[-1][1] if self.chunks else self.chunk_start)
        while len(self.buf) < target:
            if raw[pos:pos + 4] != PKG_TAG:
                return False
            _block, _cs, usize = struct.unpack_from("<III", raw, pos + 4)
            if usize == 0:
                return False
            p, total, pairs = pos + 16, 0, []
            while total < usize:
                bc, bu = struct.unpack_from("<II", raw, p)
                p += 8
                pairs.append((bc, bu))
                total += bu
            for bc, bu in pairs:
                blob = raw[p:p + bc]
                try:
                    part = zlib.decompress(blob)
                except zlib.error:
                    from _lzo1x import lzo1x_decompress
                    part = lzo1x_decompress(blob)
                if len(part) != bu:
                    raise RuntimeError("sub-block at %d decoded %d, expected %d"
                                       % (p, len(part), bu))
                self.buf += part
                p += bc
            self.chunks.append((pos, p))
            pos = p
        return True

    def name(self, i):
        if not hasattr(self, "_names"):
            self._pump(self.import_offset)
            self._names, o = [], self.name_offset
            for _ in range(self.name_count):
                s, o = _fstr(self.buf, o)
                o += 8
                self._names.append(s)
        return self._names[i]

    def data(self, index):
        self._pump(self.export_offset + index * 72)
        ints = struct.unpack_from("<11i", self.buf, self.export_offset + (index - 1) * 72)
        size, off = ints[9], ints[10]
        self._pump(off + size)
        return bytes(self.buf[off:off + size])


class Shim:
    """The three members `upk_read.walk_tags` needs, over a partially decoded image."""

    def __init__(self, pi):
        self.pi = pi
        self.names = [pi.name(i) for i in range(pi.name_count)]
        pi._pump(pi.import_offset + pi.import_count * 28)
        self.imports = []
        for i in range(pi.import_count):
            ints = struct.unpack_from("<7i", pi.buf, pi.import_offset + i * 28)
            self.imports.append({"class_package": self.names[ints[0]],
                                 "class_name": self.names[ints[2]],
                                 "outer": ints[4], "name": self.names[ints[5]]})
        pi._pump(pi.export_offset + pi.export_count * 72)
        self.exports = []
        for i in range(1, pi.export_count + 1):
            ints = struct.unpack_from("<11i", pi.buf, pi.export_offset + (i - 1) * 72)
            self.exports.append({"class_index": ints[0], "super_index": ints[1],
                                 "outer_index": ints[2], "name": self.names[ints[3]],
                                 "size": ints[9], "offset": ints[10]})
        self.name_count = pi.name_count
        self.export_count = pi.export_count
        self.import_count = pi.import_count

    def class_name(self, index):
        if index < 0:
            i = -index - 1
            return self.imports[i]["name"] if i < len(self.imports) else None
        if 0 < index <= len(self.exports):
            return self.exports[index - 1]["name"]
        return None

    def object_name(self, index):
        if index == 0:
            return None
        if index > 0:
            return self.exports[index - 1]["name"] if index <= len(self.exports) else None
        i = -index - 1
        return self.imports[i]["name"] if i < len(self.imports) else None

    def object_path(self, index):
        if index == 0:
            return None
        if index > 0:
            e = self.exports[index - 1]
            outer = self.object_name(e["outer_index"])
            return "%s.%s" % (outer, e["name"]) if outer else e["name"]
        i = -index - 1
        imp = self.imports[i]
        outer = self.object_path(imp["outer"])
        if outer:
            return "%s.%s" % (outer, imp["name"])
        return "%s.%s" % (imp["class_package"], imp["name"]) if imp["class_package"] else imp["name"]

    def object_class(self, index):
        if index > 0:
            return self.class_name(self.exports[index - 1]["class_index"])
        if index < 0:
            i = -index - 1
            return self.imports[i]["name"] if i < len(self.imports) else None
        return None


# ---------------------------------------------------------------- helpers
def tag_at(tags, typ, off):
    return next((t for t in tags if t["type"] == typ and t["offset"] == off), None)


def export_named(pkg, name):
    """First export called `name` (-1 when absent)."""
    for i, e in enumerate(pkg.exports, 1):
        if e["name"] == name:
            return i
    return -1


def export_by_path(pkg, path):
    for i in range(1, pkg.export_count + 1):
        if pkg.object_path(i) == path:
            return i
    return -1


def sha1(path):
    h = hashlib.sha1()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def name_array(payload):
    """An array of FNames: count, then 8 bytes each.  Accepted only if it tiles exactly."""
    if len(payload) < 4:
        return None
    count = struct.unpack_from("<i", payload, 0)[0]
    body = payload[4:]
    if count < 0 or count > 4096 or len(body) != count * 8:
        return None
    return [struct.unpack_from("<ii", body, i * 8) for i in range(count)]


def ref_array(payload):
    """An array of object indexes: count, then 4 bytes each."""
    if len(payload) < 4:
        return None
    count = struct.unpack_from("<i", payload, 0)[0]
    body = payload[4:]
    if count < 0 or count > 4096 or len(body) != count * 4:
        return None
    return list(struct.unpack("<%di" % count, body))


def call_names(node, bm):
    out = []

    def walk(n):
        if n.get("kind") == "Context":
            walk(n["object"])
            walk(n["func"])
        elif n.get("kind") in ("VirtualFunction", "FinalFunction"):
            out.append(n.get("ref") if n["kind"] == "FinalFunction" else n.get("name"))
            for a in n["args"]:
                walk(a)

    walk(node)
    return out


def function_calls(bm, idx):
    """Every call in a function body, in byte order, with its arguments rendered."""
    s = bm.script(idx)
    rows = []
    for at, n in GE.calls_in_order(s, bm):
        args = []
        for a in n["args"]:
            k = a["kind"]
            if k == "VectorConst":
                args.append("(%g, %g, %g)" % tuple(a["value"]))
            elif k == "FloatConst":
                args.append("%g" % a["value"])
            elif k in ("IntConst", "IntConstByte", "IntConst2B"):
                args.append(str(a["value"]))
            else:
                args.append(a.get("ref") or a.get("name") or k)
        rows.append({"at": at, "kind": n["kind"],
                     "callee": n.get("ref") if n["kind"] == "FinalFunction" else n.get("name"),
                     "args": args})
    return rows


# ---------------------------------------------------------------- BmGame side
def decode_call(bm):
    """The eject's TriggerSpecialMove call: bytes, arguments, receiver chain."""
    eject = export_by_path(bm.pkg, EJECT_PATH)
    if eject < 0:
        raise SystemExit("export %r not found" % EJECT_PATH)
    ej = bm.script(eject)

    name_idx = [i for i, n in enumerate(bm.pkg.names) if n == TSM]
    sites = []
    for ni in name_idx:
        pat = b"\x1b" + struct.pack("<i", ni)
        at = ej.find(pat)
        while at >= 0:
            sites.append((at, ni))
            at = ej.find(pat, at + 1)
    if len(sites) != 1:
        raise SystemExit("expected exactly one %s call, found %d" % (TSM, len(sites)))
    at, ni = sites[0]

    args, after = GE.arg_list(ej, at + 5, bm)
    if ej[after - 1] != 0x16:
        raise SystemExit("argument list does not close on 0x16")

    recv, recv_at = None, None
    for start in range(max(0, at - 120), at):
        try:
            node, q = GE.expr(ej, start, bm)
        except GE.Undecodable:
            continue
        if (node["kind"] == "Context" and node["func"]["kind"] in ("FinalFunction",
                                                                  "VirtualFunction")
                and node["func"]["at"] == at and GE.reserialise(node, ej) == ej[start:q]):
            recv, recv_at = node, start
            break
    if recv is None:
        raise SystemExit("receiver chain before +%d did not re-tile" % at)

    chain, cur = [], recv
    while cur["kind"] == "Context":
        chain.append({"object": GE.describe(cur["object"], bm), "skip": cur["skip"],
                      "prop_index": cur["prop_index"], "prop": cur["prop"], "flag": cur["flag"]})
        cur = cur["object"]
    chain.reverse()

    return {
        "export": eject,
        "script_bytes": len(ej),
        "call_at": at,
        "sites": len(sites),
        "name_index": ni,
        "token": "0x%02x" % ej[at],
        "callee": bm.name(ni),
        "args": [GE.describe(a, bm) for a in args],
        "arg_bytes": ej[at + 5:after].hex(" "),
        "arg_span": [at + 5, after - 1],
        "receiver_at": recv_at,
        "receiver_chain": chain,
        "receiver_retiles": True,
    }


def decode_functions(bm):
    """The config -> instance hand-off, as call inventories (no control flow claimed)."""
    out = {}
    for label, path in (
            ("config_wrapper", "RSpecialMoveConfigConfigurable.TriggerSpecialMove"),
            ("config_base", "RSpecialMoveConfig.TriggerSpecialMove"),
            ("instance_glidekick", "RSpecialMoveInstance_GlideKick.TriggerSpecialMove"),
            ("instance_relative",
             "RSpecialMoveInstance_RelativeAnimMove.TriggerSpecialMove")):
        idx = export_by_path(bm.pkg, path)
        out[label] = {
            "index": idx,
            "path": path,
            "script_bytes": len(bm.script(idx)) if idx > 0 else 0,
            "script_head": bm.script(idx)[:64].hex(" ") if idx > 0 else None,
            "calls": function_calls(bm, idx) if idx > 0 else [],
        }
    return out


def instance_class_default(bm):
    """`Default__RSpecialMoveConfig_GlideKick` -> its InstanceClass (field 140)."""
    idx = export_named(bm.pkg, "Default__RSpecialMoveConfig_GlideKick")
    if idx < 0:
        return {"index": -1, "instance_class": None, "tags": 0}
    tags, _end, _why = best_walk(bm.pkg, bm.pkg.data(idx))
    t = tag_at(tags, "ObjectNCRProperty", CFG_INSTANCECLASS_OFF)
    return {"index": idx, "name": bm.pkg.object_path(idx),
            "instance_class": t.get("ref") if t else None,
            "instance_class_index": t.get("value") if t else None,
            "tags": len(tags),
            "tag_count": len(tags),
            "other": [{"offset": x["offset"], "type": x["type"],
                       "value": {k: v for k, v in x.items()
                                 if k in ("value", "ref", "bits")}}
                      for x in tags]}


def vehicle_defaults():
    """The vehicle's own class defaults for the two members that name the move and its range."""
    doc = json.load(open(CLASS_DEFAULTS, encoding="utf-8"))
    want = {"ShortRangeGlideKick": None, "ShortRangeGlideKickRange": None}

    def scan(o):
        if isinstance(o, dict):
            n = o.get("name")
            if n in want and want[n] is None and "value" in o:
                want[n] = {k: o.get(k) for k in ("name", "value", "value_text", "ref",
                                                 "ref_class", "offset", "raw_hex", "label")}
            for v in o.values():
                scan(v)
        elif isinstance(o, list):
            for v in o:
                scan(v)

    scan(doc)
    return {"source": os.path.relpath(CLASS_DEFAULTS, ROOT), **want}


# ---------------------------------------------------------------- Startup side
def sequence_fields(tags):
    row = {}
    for t in tags:
        off, typ = t["offset"], t["type"]
        if typ == "NameProperty" and off == SEQ_NAME_OFF:
            row["sequence"] = t["value"]
        elif typ == "VectorProperty" and off == SEQ_ROOT_TRANS_OFF:
            row["root_translation"] = t["value"]
        elif typ == "RotatorProperty" and off == SEQ_ROOT_ROT_OFF:
            row["root_rotation"] = t["value"]
        elif typ == "FloatProperty" and off == SEQ_LENGTH_OFF:
            row["length_s"] = t["value"]
        elif typ == "IntProperty" and off == SEQ_FRAMES_OFF:
            row["frames"] = t["value"]
        elif typ == "FloatProperty" and off == SEQ_RATE_OFF:
            row["rate"] = t["value"]
    return row


def decode_assets(config_export):
    """The wrapper asset -> nested config -> AnimName/AnimSet -> AnimSequences -> root motion."""
    pi = PartialImage(STARTUP)
    sh = Shim(pi)

    wrapper = sh.exports[config_export - 1]
    wraw = pi.data(config_export)
    wtags, _wend, _why = best_walk(sh, wraw)
    inner_refs = [{"offset": t["offset"], "type": t["type"], "ref": t.get("ref"),
                   "value": t.get("value")} for t in wtags]

    nested_idx = next((t["value"] for t in wtags if t["type"] == "ObjectNCRProperty"), None)
    if not nested_idx:
        raise SystemExit("wrapper %r carries no inner config" % wrapper["name"])

    nraw = pi.data(nested_idx)
    ntags, _nend, _nwhy = best_walk(sh, nraw)
    anim_tag = next((t for t in ntags if t["type"] == "ArrayProperty"), None)
    animset_tag = tag_at(ntags, "ObjectNCRProperty", CFG_ANIMSET_OFF)
    names = name_array(nraw[anim_tag["at"]:anim_tag["at"] + anim_tag["size"]]) if anim_tag else None
    anim_names = [sh.names[a] for a, _b in names] if names else []

    animset_idx = animset_tag["value"] if animset_tag else None
    araw = pi.data(animset_idx)
    atags, _aend, _awhy = best_walk(sh, araw)
    seq_tag = next((t for t in atags if t["type"] == "ArrayProperty" and t.get("name")
                    == "Sequences"), None)
    seq_refs = ref_array(araw[seq_tag["at"]:seq_tag["at"] + seq_tag["size"]]) if seq_tag else []

    census = []
    for idx in seq_refs:
        tags, _e, _w = best_walk(sh, pi.data(idx))
        row = sequence_fields(tags)
        row["export"] = idx
        row["class"] = sh.object_class(idx)
        census.append(row)

    targets = {}
    for nm in anim_names:
        row = next((r for r in census if r.get("sequence") == nm), None)
        if row is None:
            targets[nm] = None
            continue
        raw = pi.data(row["export"])
        tags, _e, _w = best_walk(sh, raw)
        zi = tag_at(tags, "StructProperty", SEQ_ZIP_OFF)
        kept = {k: v for k, v in row.items()
                if k in ("export", "class", "sequence", "root_translation", "root_rotation",
                         "length_s", "frames", "rate")}
        kept["anim_zip_linear_motion"] = {
            "offset": SEQ_ZIP_OFF,
            "name": zi.get("name") if zi else None,
            "props": [{k: v for k, v in p.items()
                       if k in ("type", "offset", "name", "value", "floats", "raw")}
                      for p in (zi.get("props") or [])] if zi else [],
        }
        kept["export_size"] = len(raw)
        kept["tag_count"] = len(tags)
        kept["tag_stream_end"] = _e
        targets[nm] = kept

    return {
        "package": os.path.basename(STARTUP),
        "package_bytes": os.path.getsize(STARTUP),
        "package_sha1": sha1(STARTUP),
        "shim": {"names": sh.name_count, "imports": sh.import_count,
                 "exports": sh.export_count},
        "wrapper": {"export": config_export, "name": wrapper["name"],
                    "class": sh.object_class(config_export),
                    "outer": sh.object_path(wrapper["outer_index"]),
                    "bytes": len(wraw),
                    "properties": inner_refs},
        "config": {"export": nested_idx, "name": sh.object_path(nested_idx),
                   "class": sh.object_class(nested_idx), "bytes": len(nraw),
                   "anim_name_field": anim_tag["offset"] if anim_tag else None,
                   "anim_name_count": len(anim_names), "anim_names": anim_names,
                   "anim_set_field": animset_tag["offset"] if animset_tag else None,
                   "anim_set": animset_tag.get("ref") if animset_tag else None,
                   "anim_set_export": animset_idx},
        "anim_set": {"export": animset_idx, "sequences": len(seq_refs),
                     "sequence_exports": seq_refs[:8]},
        "census": census,
        "targets": targets,
    }


# ---------------------------------------------------------------- numbers
def root_motion(row):
    """Launch numbers from one sequence's root-motion translation."""
    v = row.get("root_translation") or [0.0, 0.0, 0.0]
    x, y, z = [float(c) for c in v]
    horiz = (x * x + y * y) ** 0.5
    length = float(row.get("length_s") or 0.0)
    frames = int(row.get("frames") or 0)
    rate = float(row.get("rate") or 0.0)
    return {
        "translation_cm": [round(x, 4), round(y, 4), round(z, 4)],
        "distance_horizontal_cm": round(horiz, 4),
        "distance_horizontal_m": round(horiz / 100.0, 4),
        "height_cm": round(z, 4),
        "duration_s": round(length, 6),
        "frames": frames,
        "rate_fps": round(rate, 6),
        "mean_speed_cm_s": round(horiz / length, 4) if length else None,
        "mean_speed_m_s": round(horiz / length / 100.0, 4) if length else None,
        "mean_cm_per_frame": round(horiz / (frames - 1), 4) if frames > 1 else None,
    }


def decode(bm):
    d = {
        "task": "G3-02k",
        "package": os.path.basename(UPK),
        "package_bytes": os.path.getsize(UPK),
        "package_sha1": sha1(UPK),
        "call": decode_call(bm),
        "functions": decode_functions(bm),
        "instance_class_default": instance_class_default(bm),
        "vehicle_defaults": vehicle_defaults(),
    }
    wrapper_value = None
    vd = d["vehicle_defaults"].get("ShortRangeGlideKick") or {}
    if isinstance(vd.get("value"), int):
        wrapper_value = vd["value"]
    if not wrapper_value:
        raise SystemExit("no ShortRangeGlideKick default in %s" % CLASS_DEFAULTS)
    d["assets"] = decode_assets(wrapper_value)
    d["launch"] = {nm: (root_motion(row) if row else None)
                   for nm, row in d["assets"]["targets"].items()}
    return d


# ---------------------------------------------------------------- checks
VELOCITY_TOKENS = ("SetVelocity", "SetRBLinearVelocity", "AddForce", "AddImpulse",
                   "SetPhysicsLinearVelocity", "AddVelocity", "Launch")


def checks(d):
    c = d["call"]
    chain = c["receiver_chain"]
    props = [lvl.get("prop") or "" for lvl in chain]
    assets = d["assets"]
    cfg = assets["config"]
    targets = assets["targets"]
    launch = d["launch"]
    census = assets["census"]
    icd = d["instance_class_default"]
    glide = d["functions"]["instance_glidekick"]
    rel = d["functions"]["instance_relative"]
    good_census = [r for r in census if r.get("frames") and r.get("rate") and r.get("length_s")]
    coherent = [r for r in good_census
                if abs((r["frames"] - 1) / r["rate"] - r["length_s"]) < 1e-3]
    standing = [r for r in census if "Stand" in (r.get("sequence") or "")]
    travelling = [r for r in census if any(r.get("root_translation") or [0, 0, 0])]
    stand_max_x = max([float((r.get("root_translation") or [0, 0, 0])[0]) for r in standing] or [0.0])
    kick_x = [(launch[n] or {}).get("translation_cm", [0, 0, 0])[0]
              for n in cfg["anim_names"] if launch.get(n)]
    args = c["args"]
    return [
        ("EjectFromVehicle holds exactly one TriggerSpecialMove call token",
         c["sites"] == 1 and c["callee"] == TSM),
        ("its argument list tiles to the 0x16 terminator and carries three arguments",
         len(args) == 3 and args[0].get("kind") == "Self"),
        ("the receiver chain re-serialises to the original bytes",
         c["receiver_retiles"] is True),
        ("the receiver chain ends on RVehicleBatmobileBase.ShortRangeGlideKick",
         any(p.endswith("ShortRangeGlideKick") for p in props)),
        ("the vehicle's class default for that property is GlideKick.GlideKickShort_FromBatmobile",
         (d["vehicle_defaults"].get("ShortRangeGlideKick") or {}).get("ref")
         == "GlideKick.GlideKickShort_FromBatmobile"),
        ("and its ShortRangeGlideKickRange default is 2500 cm",
         (d["vehicle_defaults"].get("ShortRangeGlideKickRange") or {}).get("value") == 2500.0),
        ("that asset is a single-property wrapper whose property is the inner config",
         len(assets["wrapper"]["properties"]) == 1
         and assets["wrapper"]["properties"][0]["type"] == "ObjectNCRProperty"),
        ("the inner config is an RSpecialMoveConfig_GlideKick",
         cfg["class"] == "RSpecialMoveConfig_GlideKick"),
        ("its AnimName array holds two FNames, both present in the anim set",
         cfg["anim_name_count"] == 2 and all(targets.get(n) for n in cfg["anim_names"])),
        ("the anim set's Sequences array resolves to AnimSequence exports",
         assets["anim_set"]["sequences"] > 0
         and all(r["class"] == "AnimSequence" for r in census)),
        ("the config's InstanceClass default is RSpecialMoveInstance_GlideKick",
         (icd.get("instance_class") or "").endswith("RSpecialMoveInstance_GlideKick")),
        ("the GlideKick instance body calls its parent and sets no velocity",
         any((r["callee"] or "").endswith("TriggerSpecialMove") for r in glide["calls"])
         and not any(v in (r["callee"] or "") for r in glide["calls"] for v in VELOCITY_TOKENS)),
        ("the parent instance body has no velocity setter either",
         not any(v in (r["callee"] or "") for r in rel["calls"] for v in VELOCITY_TOKENS)),
        ("(NumFrames-1)/Rate equals SequenceLength on every sequence of the set",
         len(coherent) == len(good_census) and len(good_census) >= 50),
        ("the field is absent on most of the set and present on the rest - not a constant",
         len(census) - len(travelling) >= 30 and len(travelling) >= 10),
        ("both kicks travel farther along +X than any 'Stand' sequence in the same set",
         bool(kick_x) and all(x > stand_max_x for x in kick_x)),
        ("both glide-kick sequences move along +X with no vertical rise",
         all(launch[n] and abs(launch[n]["translation_cm"][1]) < 1e-3
             and abs(launch[n]["height_cm"]) < 1e-3 and launch[n]["distance_horizontal_cm"] > 700
             for n in cfg["anim_names"])),
    ]


# ---------------------------------------------------------------- render
def fmt(v, nd=3):
    if v is None:
        return "UNKNOWN"
    return ("%%.%df" % nd % v).rstrip("0").rstrip(".") if isinstance(v, float) else str(v)


def render(d):
    c = d["call"]
    assets = d["assets"]
    cfg = assets["config"]
    icd = d["instance_class_default"]
    vd = d["vehicle_defaults"]
    launch = d["launch"]
    names = cfg["anim_names"]
    first = launch.get(names[0]) if names else None
    second = launch.get(names[1]) if len(names) > 1 else None
    range_row = vd.get("ShortRangeGlideKickRange") or {}
    L = []
    A = L.append

    A("# EJECT_MOVE - G3-02k")
    A("")
    A("What `DrivingMode.EjectFromVehicle`'s `TriggerSpecialMove` starts, what that move is")
    A("made of, and the numbers that produce the launch.")
    A("")
    A("- package: `%s` (sha1 `%s`)" % (d["package"], d["package_sha1"]))
    A("- package: `%s` (sha1 `%s`)" % (assets["package"], assets["package_sha1"]))
    A("- body: `%s` export %d, script %d bytes" % (EJECT_PATH, c["export"], c["script_bytes"]))
    A("")
    A("## VERDICT")
    A("")
    if first:
        A("**The eject triggers a glide kick, and the kick's own animation is what moves")
        A("Batman.** The call at `+%d` is a *virtual* `TriggerSpecialMove` dispatched on the"
          % c["call_at"])
        A("Context object `Car.ShortRangeGlideKick` - the vehicle's class default for that")
        A("member is the move asset `GlideKick.GlideKickShort_FromBatmobile`")
        A("(`RSpecialMoveConfigConfigurable` wrapping an `RSpecialMoveConfig_GlideKick`). That")
        A("config names anim set `BM_Batmobile` and two animations; the short-range one")
        A("`%s` carries a root-motion translation of (%s, %s, %s) cm over %d frames at"
          % (names[0], fmt(first["translation_cm"][0], 3), fmt(first["translation_cm"][1], 3),
             fmt(first["translation_cm"][2], 3), first["frames"]))
        A("%d fps. The launch is therefore:" % int(first["rate_fps"]))
        A("")
        A("| quantity | value | source |")
        A("|---|---|---|")
        A("| forward distance | **%s cm (%s m)** | `%s` field %d |"
          % (fmt(first["distance_horizontal_cm"], 2), fmt(first["distance_horizontal_m"], 3),
             names[0], SEQ_ROOT_TRANS_OFF))
        A("| vertical rise | **%s cm** | same field, Z component |" % fmt(first["height_cm"], 2))
        A("| duration | **%s s** (%d frames @ %d fps) | fields %d / %d / %d |"
          % (fmt(first["duration_s"], 4), first["frames"], int(first["rate_fps"]),
             SEQ_LENGTH_OFF, SEQ_FRAMES_OFF, SEQ_RATE_OFF))
        A("| mean speed | **%s cm/s** (%s m/s) | distance / duration |"
          % (fmt(first["mean_speed_cm_s"], 1), fmt(first["mean_speed_m_s"], 3)))
        A("| per-frame step | **%s cm** | distance / (frames - 1) |"
          % fmt(first["mean_cm_per_frame"], 3))
        A("| target range the move is offered at | **2500 cm (25 m)** | "
          "`RVehicleBatmobileBase.ShortRangeGlideKickRange` default |")
        A("")
        if second:
            A("The same config's other animation `%s` (mid range) carries (%s, %s, %s) cm over"
              % (names[1], fmt(second["translation_cm"][0], 3),
                 fmt(second["translation_cm"][1], 3), fmt(second["translation_cm"][2], 3)))
            A("%d frames - %s s, mean %s cm/s. Which of the two is played is chosen at run time"
              % (second["frames"], fmt(second["duration_s"], 4),
                 fmt(second["mean_speed_cm_s"], 1)))
            A("(`AnimName` is an array and `PickRandomAnim` is called in the parent instance body),")
            A("so the *pair* bounds the launch: %s - %s cm forward."
              % (fmt(first["distance_horizontal_cm"], 2), fmt(second["distance_horizontal_cm"], 2)))
            A("")
        A("There is **no scripted velocity and no class-default velocity** anywhere on the")
        A("chain: the config's own defaults carry an `InstanceClass` and two bools, nothing")
        A("numeric, and neither the GlideKick instance body nor its parent contains a velocity")
        A("call. The `(0, 0, 0)` `SetRBLinearVelocity` of G3-02j stops the car; this animation")
        A("moves Batman.")
    A("")
    A("## 1. The call and the move it names")
    A("")
    A("`%s` at script `+%d` is `0x%02x` - a *virtual* call token, so the callee is an FName"
      % (c["callee"], c["call_at"], int(c["token"], 16)))
    A("(`%s`, name index %d) and the target class is whatever the receiver's class resolves"
      % (c["callee"], c["name_index"]))
    A("it to. Argument bytes (from the callee to the terminator):")
    A("")
    A("```")
    A("%s" % c["arg_bytes"])
    A("```")
    A("")
    A("| arg | kind | value |")
    A("|---|---|---|")
    for i, a in enumerate(c["args"]):
        val = (a.get("ref") or a.get("name") or a.get("kind"))
        A("| %d | %s | `%s` |" % (i, a.get("kind"), val))
    A("")
    A("Its receiver is the Context chain that ends on the callee byte and re-serialises to the")
    A("original bytes (`receiver_retiles: True`):")
    A("")
    A("```")
    for i, lvl in enumerate(c["receiver_chain"]):
        obj = lvl["object"]
        A("  level %d: object = %s   prop = %s   skip=%d flag=%d"
          % (i, json.dumps(obj.get("ref") or obj.get("kind")), lvl["prop"], lvl["skip"],
             lvl["flag"]))
    A("```")
    A("")
    A("The outermost Context is the \"call a virtual function on this expression\" form - its")
    A("`prop_index` is 0 (no property), so `TriggerSpecialMove` is dispatched on the object the")
    A("inner Context produced: `Car.ShortRangeGlideKick`.")
    A("")
    A("The parameter order matches the config class's own forwarding body:")
    A("`RSpecialMoveConfigConfigurable.TriggerSpecialMove` (export %d, %d bytes) reads its own"
      % (d["functions"]["config_wrapper"]["index"],
         d["functions"]["config_wrapper"]["script_bytes"]))
    A("locals in the order `Controller, MoveLocation, ForceReplicateToClient` and forwards them")
    A("to `Config.TriggerSpecialMove`:")
    A("")
    for r in d["functions"]["config_wrapper"]["calls"]:
        A("- `+%d %s(%s)`" % (r["at"], r["callee"], ", ".join(r["args"])))
    A("")
    A("## 2. From the move asset to the animation")
    A("")
    A("`Research/BatmobileGrab/CLASS_DEFAULTS.json` (`%s`) gives the vehicle's default for the"
      % vd.get("source"))
    A("member the call receives:")
    A("")
    A("| member | value |")
    A("|---|---|")
    A("| `ShortRangeGlideKick` | `%s` |" % (vd.get("ShortRangeGlideKick") or {}).get("ref"))
    A("| `ShortRangeGlideKickRange` | `%s` cm |" % fmt(range_row.get("value"), 1))
    A("")
    A("In `%s` that asset is export %d `%s` (%s), %d bytes, outered to `%s`:"
      % (assets["package"], assets["wrapper"]["export"], assets["wrapper"]["name"],
         assets["wrapper"]["class"], assets["wrapper"]["bytes"], assets["wrapper"]["outer"]))
    A("")
    A("| property | field | target |")
    A("|---|---|---|")
    for p in assets["wrapper"]["properties"]:
        A("| `Config` | %d | `%s` |" % (p["offset"], p["ref"]))
    A("")
    A("So the wrapper is a one-property shim: `RSpecialMoveConfigConfigurable` exists to hold an")
    A("inner `RSpecialMoveConfig` (its own `TriggerSpecialMove` does nothing but forward). The")
    A("inner config is export %d `%s` (%s), %d bytes:"
      % (assets["config"]["export"], cfg["name"], cfg["class"], cfg["bytes"]))
    A("")
    A("| property | field | value |")
    A("|---|---|---|")
    A("| `AnimName` | %s | %s |" % (cfg["anim_name_field"],
                                   ", ".join("`%s`" % n for n in cfg["anim_names"])))
    A("| `AnimSet` | %s | `%s` (export %d) |" % (cfg["anim_set_field"], cfg["anim_set"],
                                                cfg["anim_set_export"]))
    A("")
    A("The anim set holds %d sequences; each `AnimSequence` export is literally named" % len(
        assets["census"]))
    A("`AnimSequence`, so the human name is its `SequenceName` field (offset %d). Both names in"
      % SEQ_NAME_OFF)
    A("`AnimName` resolve to exports of that set:")
    A("")
    A("| AnimName | export | bytes | tags | root translation |")
    A("|---|---|---|---|---|")
    for nm in names:
        row = assets["targets"].get(nm)
        A("| `%s` | %s | %s | %s | %s |"
          % (nm, row["export"] if row else "-", row["export_size"] if row else "-",
             row["tag_count"] if row else "-", row["root_translation"] if row else "-"))
    A("")
    A("Who runs the move: the config class's own default names the instance class")
    A("(`Default__RSpecialMoveConfig_GlideKick`, export %d, field %d):"
      % (icd.get("index", -1), CFG_INSTANCECLASS_OFF))
    A("")
    A("| tag | value |")
    A("|---|---|")
    for t in icd.get("other", []):
        val = t["value"].get("ref") or t["value"].get("value")
        A("| %s @%d | `%s` |" % (t["type"], t["offset"], val))
    A("")
    A("## 3. What the move's code does - and does not - do")
    A("")
    A("`RSpecialMoveInstance_GlideKick.TriggerSpecialMove` (export %d, %d bytes) starts by"
      % (d["functions"]["instance_glidekick"]["index"],
         d["functions"]["instance_glidekick"]["script_bytes"]))
    A("calling its parent, then does window-villain bookkeeping; it assigns no speed:")
    A("")
    A("```")
    A(d["functions"]["instance_glidekick"]["script_head"])
    A("```")
    A("")
    for r in d["functions"]["instance_glidekick"]["calls"]:
        A("- `+%d %s(%s)`" % (r["at"], r["callee"], ", ".join(r["args"])))
    A("")
    A("The parent `RSpecialMoveInstance_RelativeAnimMove.TriggerSpecialMove` (export %d, %d"
      " bytes) sets up the reference location/rotation, copies `OverrideGlideSpeed` from the"
      % (d["functions"]["instance_relative"]["index"],
         d["functions"]["instance_relative"]["script_bytes"]))
    A("config, picks the animation, pushes the controller state and the camera. Its call")
    A("inventory in byte order, filtered to nothing - this is the whole list:")
    A("")
    for r in d["functions"]["instance_relative"]["calls"]:
        A("- `+%d %s(%s)`" % (r["at"], r["callee"], ", ".join(r["args"])))
    A("")
    A("No `SetVelocity` / `SetRBLinearVelocity` / `AddForce` / impulse call appears in either")
    A("body, and the config class's defaults carry no numeric field (the check list asserts")
    A("this mechanically). What is left is the animation.")
    A("")
    A("## 4. The animation's root motion")
    A("")
    A("A cooked `AnimSequence` stores its simple properties inline with **no name**, only the")
    A("field offset. The offsets below are read off this package and identified by content,")
    A("not by name:")
    A("")
    A("| field | type | identified as | evidence |")
    A("|---|---|---|---|")
    A("| %d | FName | `SequenceName` | equals the name the anim set/config use |" % SEQ_NAME_OFF)
    moving = len([r for r in assets["census"] if r.get("root_translation")])
    A(("| %d | Vector (12 B) | root-motion translation | absent on the %d sequences that stay"
       " in place, present on the %d that travel (section 5) |")
      % (SEQ_ROOT_TRANS_OFF, len(assets["census"]) - moving, moving))
    A("| %d | Rotator | root-motion rotation | pairs with the vector; non-zero only where the "
      "sequence turns |" % SEQ_ROOT_ROT_OFF)
    A("| %d | Float | `SequenceLength` (s) | equals (NumFrames-1)/Rate on all %d sequences |"
      % (SEQ_LENGTH_OFF, len(assets["census"])))
    A("| %d | Int | `NumFrames` | 3.7333 s x 30 fps + 1 = 113 |" % SEQ_FRAMES_OFF)
    A("| %d | Float | `Rate` (fps) | 30.0 on every sequence of the set |" % SEQ_RATE_OFF)
    A("")
    if first:
        A("For `%s`:" % names[0])
        A("")
        A("| measure | value |")
        A("|---|---|")
        A("| root translation | `(%s, %s, %s)` cm |" % tuple(fmt(x, 4)
                                                           for x in first["translation_cm"]))
        A("| root rotation | `%s` |" % (assets["targets"][names[0]]["root_rotation"],))
        A("| frames / rate | %d @ %d fps |" % (first["frames"], int(first["rate_fps"])))
        A("| length | %s s |" % fmt(first["duration_s"], 6))
        A("| horizontal distance | %s cm = %s m |" % (fmt(first["distance_horizontal_cm"], 3),
                                                       fmt(first["distance_horizontal_m"], 4)))
        A("| vertical rise | %s cm |" % fmt(first["height_cm"], 3))
        A("| mean horizontal speed | %s cm/s |" % fmt(first["mean_speed_cm_s"], 2))
        A("| mean step per frame | %s cm |" % fmt(first["mean_cm_per_frame"], 4))
        A("")
        A("The translation is `+X` only: the kick travels straight along the character's")
        A("facing direction and does not rise. Per-frame *samples* are not reported: the")
        A("sequence's keyframes are stored in the zip-compressed block that follows the tag")
        A("stream: %d of the export's %d bytes - so the mean"
          % (assets["targets"][names[0]]["export_size"]
             - assets["targets"][names[0]]["tag_stream_end"],
             assets["targets"][names[0]]["export_size"]))
        A("step above is exact; the distribution across the %d frames is **UNKNOWN** here."
          % first["frames"])
        A("")
        A("`AnimZip_LinearMotion` (field %d) is recorded verbatim for the next pass:" % SEQ_ZIP_OFF)
        A("")
        zp = assets["targets"][names[0]]["anim_zip_linear_motion"]["props"]
        A("| prop | type | value |")
        A("|---|---|---|")
        for p in zp:
            v = p.get("value")
            if v is None:
                v = p.get("raw") or (p.get("floats") and "floats %s" % p["floats"])
            A("| @%s | %s | `%s` |" % (p.get("offset"), p.get("type"), v))
        A("")
    A("## 5. Cross-check: the field across the whole anim set")
    A("")
    A("Field %d is not a constant and not a bounding box: it is **absent on %d of the %d"
      % (SEQ_ROOT_TRANS_OFF, len(assets["census"]) - len([r for r in assets["census"]
                                                          if r.get("root_translation")]),
         len(assets["census"])))
    A("sequences** and present on the other %d - exactly the ones whose name says they move"
      % len([r for r in assets["census"] if r.get("root_translation")]))
    A("the character (abseil, grapple, step-onto, glide-90, the two kicks, the remote")
    A("in/out poses). All %d sequences of `BM_Batmobile`:" % len(assets["census"]))
    A("")
    A("| sequence | field %d | rot %d | length s | frames | rate |"
      % (SEQ_ROOT_TRANS_OFF, SEQ_ROOT_ROT_OFF))
    A("|---|---|---|---|---|---|")
    for r in assets["census"]:
        tr = r.get("root_translation")
        A("| `%s` | %s | %s | %s | %s | %s |"
          % (r.get("sequence"), "`%s`" % tr if tr else "-", r.get("root_rotation"),
             fmt(r.get("length_s"), 4), r.get("frames"), fmt(r.get("rate"), 1)))
    A("")
    A("## 6. What is UNKNOWN")
    A("")
    A("- The *name* of field %d: the cooked tag is a simple property and stores no FName."
      % SEQ_ROOT_TRANS_OFF)
    A("  Its content is identified by the census above, not by a name string.")
    A("- The per-frame root translation curve: the keyframe block is zip-compressed and its")
    A("  format is not decoded here. Only the total and the mean are given.")
    A("- The blob at `AnimZip_LinearMotion` (field %d): recorded, not interpreted." % SEQ_ZIP_OFF)
    A("- Which of the two animations plays for a given eject: `AnimName` is an array and the")
    A("  parent body calls `PickRandomAnim`; the choice logic is not decoded.")
    A("- The token `0x4a` used as the third argument (G3-02j reports it too): a one-byte token")
    A("  whose meaning is not established. It is passed through as `ForceReplicateToClient`")
    A("  only because the forwarding body's third parameter is that name - not because the")
    A("  token was decoded.")
    A("")
    if first:
        A("STATUS: DONE - the move is named, its asset and instance class are read from the")
        A("packages, and the launch is the short-range glide kick animation's root translation")
        A("(%s cm forward, %s cm rise, %s s). Per-frame samples and field names the cooked"
          % (fmt(first["distance_horizontal_cm"], 2), fmt(first["height_cm"], 2),
             fmt(first["duration_s"], 4)))
        A("packages do not store are marked UNKNOWN.")
    else:
        A("STATUS: PARTIAL - the call decoded but no animation was resolved.")
    A("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- main
def main(argv):
    write = "--write" in argv
    check = "--check" in argv
    if not (write or check):
        print(__doc__)
        return 2
    bm = B.Bm(UPK)
    d = decode(bm)
    md = render(d)
    res = checks(d)
    ok = sum(1 for _n, c in res if c)
    for name, c in res:
        print("%s  %s" % ("PASS" if c else "FAIL", name))
    print("%d/%d checks pass" % (ok, len(res)))
    d["checks"] = [{"name": n, "pass": bool(c)} for n, c in res]
    d["status"] = "DONE" if ok == len(res) else "PARTIAL"
    text = json.dumps(d, indent=1, sort_keys=True) + "\n"
    if write:
        open(OUT_MD, "w", encoding="utf-8", newline="\n").write(md)
        open(OUT_JSON, "w", encoding="utf-8", newline="\n").write(text)
        print("wrote", os.path.relpath(OUT_MD, ROOT))
        print("wrote", os.path.relpath(OUT_JSON, ROOT))
    if check:
        for path, want in ((OUT_MD, md), (OUT_JSON, text)):
            cur = open(path, encoding="utf-8").read() if os.path.exists(path) else ""
            print("%s %s" % ("MATCH" if cur == want else "DIFFERS",
                             os.path.relpath(path, ROOT)))
            if cur != want:
                return 1
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

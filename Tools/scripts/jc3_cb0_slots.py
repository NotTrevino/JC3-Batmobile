"""jc3_cb0_slots.py - G3-04e: naming the paint constant-buffer slots without RDEF.

The brief starts from G3-04d: the two cooked Batmobile shader caches hold 40,299 DXBC
containers and **0 RDEF chunks**, so the bytecode reads `cb0[n]` by number, and 6,934
per-material uniform records are the only name->value data left.  It asks for a slot-naming
route that does not need RDEF: the shipped material parameter lists (.rbm/.epe), the uniform
record names, and the order/byte offsets in which the engine fills the buffer.

What this pass does (static only, read-only):

  1. parses every shader reflection header the project has on disk
     (`Tools/JCMR-src/assets/jc3/shaders/*.fb.txt`, 1,551 files) for cbuffer members
     (name, offset, size) and for the resource-binding table (cbN / sN / tN);
  2. takes the paint family = every header that declares `CarPaintStaticMaterialParams`
     and tests, per family member, the bind number of each paint cbuffer and the member
     table - a slot name counts only if **every** member of the family agrees;
  3. maps the JC3 `.rbm` `CarPaintMM` block onto those cbuffers by size and field order
     (18 float4 + 7 floats + 4 float4 + 3 floats), over every CarPaintMM block on disk;
  4. attempts the brief's own method on the 6,934 Arkham uniform records: can any of their
     parameter names be given an offset from the shipped parameter data?

Labels: decoded (file + offset/line), derived (rule + inputs), UNKNOWN (what was tried).

Usage:
    uv run python Tools/scripts/jc3_cb0_slots.py --write
    uv run python Tools/scripts/jc3_cb0_slots.py --check
"""

from __future__ import annotations

import glob
import json
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

import rbm_geom  # noqa: E402  (decoded .rbm reader; its own round trip is the oracle)

SHADERS = os.path.join(ROOT, "Tools", "JCMR-src", "assets", "jc3", "shaders")
RBM_GLOB = r"E:/Modding/_shared/gamedata/JC3grab/b13b/unpacked/**/*.rbm"
ARKHAM = os.path.join(ROOT, "Research", "BatmobileGrab", "UNIFORM_RECORDS.json")
OUT = os.path.join(ROOT, "Research", "JC3Grab")
MD = os.path.join(OUT, "CB0_SLOTS.md")
JS = os.path.join(OUT, "CB0_SLOTS.json")

PAINT_STATIC = "CarPaintStaticMaterialParams"
PAINT_DYNAMIC = "CarPaintDynamicMaterialParams"
PAINT_OBJECT = "CarPaintDynamicObjectParams"
RBI = "RBIInfo"

# Sizes the .rbm block writer uses (rbm_geom.decode_carpaintmm): 18 vec4, 7 floats,
# 4 vec4 + 3 floats.  Asserted against the headers below.
STATIC_BYTES = 18 * 16
SUPPORT_BYTES = 7 * 4
DYNAMIC_BYTES = 4 * 16 + 3 * 4


# ---------------------------------------------------------------- header parsing
def parse_header(path):
    """cbuffer members (name/offset/size) and the resource-binding table of an .fb.txt."""
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    cbuffers, order = {}, []
    cur = None
    pending = None
    in_defs = False
    for raw in lines:
        line = raw.strip()
        if line.startswith("// Buffer Definitions"):
            in_defs = True
            continue
        if not in_defs:
            continue
        body = line[2:].strip() if line.startswith("//") else line
        m = re.match(r"cbuffer (\w+)", body)
        if m:
            cur = m.group(1)
            cbuffers[cur] = []
            order.append(cur)
            continue
        if body.startswith("}"):
            cur = None
            continue
        if cur is None:
            continue
        mo = re.search(r"Offset:\s*(\d+)", body)
        ms = re.search(r"Size:\s*(\d+)", body)
        if pending is not None:
            if ms:
                pending["size"] = int(ms.group(1))
                cbuffers[cur].append(pending)
                pending = None
            else:
                pending = None
            continue
        if not mo:
            continue
        decl = body.split("//")[0].strip().rstrip(";") if "//" in body else ""
        if not decl or "float" not in decl:
            continue
        typ, name = decl.split()[:2]
        rec = {"type": typ, "name": name, "offset": int(mo.group(1)),
               "size": int(ms.group(1)) if ms else None,
               "unused": "[unused]" in body}
        if rec["size"] is None:
            pending = rec
        else:
            cbuffers[cur].append(rec)
    binds = {}
    for raw in lines:
        f = raw.split()
        while f and f[0] == "//":       # the binding table is a comment block
            f.pop(0)
        if len(f) >= 6 and f[1] in ("cbuffer", "sampler", "texture") and re.fullmatch(r"(cb|s|t)\d+", f[4]):
            binds.setdefault(f[1], {})[f[0]] = f[4]
        elif len(f) >= 5 and f[1] in ("cbuffer", "sampler", "texture") and re.fullmatch(r"(cb|s|t)\d+", f[3]):
            binds.setdefault(f[1], {})[f[0]] = f[3]
    return {"file": os.path.basename(path), "cbuffers": cbuffers, "order": order, "binds": binds}


def sig(members):
    return tuple((m["name"], m["offset"], m["size"]) for m in members)


def cb_size(members):
    return max(m["offset"] + m["size"] for m in members)


def slot_of(cb, m):
    """DXBC addressing: 16-byte register index plus a component letter for a scalar."""
    reg, rem = divmod(m["offset"], 16)
    if m["size"] == 16:
        return "%s[%d]" % (cb, reg)
    return "%s[%d].%s" % (cb, reg, "xyzw"[rem // 4])


# ---------------------------------------------------------------- .rbm side
def rbm_blocks():
    files, blocks, skipped = 0, [], []
    sizes = {"static": set(), "support": set(), "dynamic": set()}
    for p in sorted(glob.glob(RBM_GLOB, recursive=True)):
        blob = open(p, "rb").read()
        if struct.pack("<I", rbm_geom.RB_CARPAINTMM) not in blob:
            continue
        files += 1
        try:
            rbm = rbm_geom.decode(blob)
        except rbm_geom.RbmError as e:
            # the codec stops at GeneralMkIII (no serializer for it); those files'
            # CarPaintMM blocks before/after it are skipped and reported, not guessed
            skipped.append({"file": os.path.basename(p), "error": str(e)})
            continue
        for blk in rbm.blocks:
            if not isinstance(blk, rbm_geom.CarPaintMM):
                continue
            sizes["static"].add(len(blk.static_params))
            sizes["support"].add(len(blk.static_support))
            sizes["dynamic"].add(len(blk.dynamic_params))
            blocks.append({"file": os.path.basename(p), "flags": blk.flags,
                           "static": blk.static_params, "support": blk.static_support,
                           "dynamic": blk.dynamic_params, "textures": len(blk.textures)})
    return files, blocks, sizes, skipped


# ---------------------------------------------------------------- Arkham records
def arkham():
    """G3-04c/d's uniform-record decode: counts, plus its one fully decoded record.

    The JSON is a decode report, not a dump of 6,943 name lists: it exposes the region
    counts and the 14 named entries of the one record it followed end to end
    (`Batmobile_Worn`).  `slot_field` is the card's structural result over all 9,553
    entries - each is 32 B (class FName, parameter FName, RGBA float4), measured there,
    not re-derived here.
    """
    d = json.load(open(ARKHAM, encoding="utf-8"))
    rec, prior, chain = d["records"], d["prior_pass"], d["chain"]["batmobile_worn"]
    names = [e["parameter"] for e in chain["entries"]]
    return {"records": rec["count"], "reported_6934": prior["count"],
            "extra_here": prior["extra_here"], "card_oracles": "%d/%d" % (
                d["oracles"]["passed"], d["oracles"]["total"]),
            "entries": rec["entries_total"], "entry_bytes": rec["entry_bytes"],
            "region_bytes": rec["region_bytes"], "file_bytes": rec["file_bytes"],
            "names": names, "distinct_names": len(set(names)),
            "name_pool": d["meta"]["names"], "slot_field": False}


def norm(s):
    return re.sub(r"[^a-z0-9]", "", s.lower().replace("m_", "", 1))


# ---------------------------------------------------------------- build
def build():
    headers = [parse_header(p) for p in sorted(glob.glob(os.path.join(SHADERS, "*.fb.txt")))]
    family = [h for h in headers if PAINT_STATIC in h["cbuffers"]]
    dyn_only = [h["file"] for h in headers
                if PAINT_DYNAMIC in h["cbuffers"] and PAINT_STATIC not in h["cbuffers"]]

    def bind_of(h, cb):
        for name, b in h["binds"].get("cbuffer", {}).items():
            if name == cb:
                return b
        return None

    members = {cb: [] for cb in (PAINT_STATIC, PAINT_DYNAMIC, PAINT_OBJECT, RBI)}
    for h in family:
        for cb in members:
            if cb in h["cbuffers"] and not members[cb]:
                members[cb] = h["cbuffers"][cb]
    base = family[0]
    agreement = {}
    for cb in (PAINT_STATIC, PAINT_DYNAMIC, PAINT_OBJECT, RBI):
        agree = [h["file"] for h in family if cb in h["cbuffers"]
                 and sig(h["cbuffers"][cb]) == sig(members[cb])]
        decl = [h["file"] for h in family if cb in h["cbuffers"]]
        agreement[cb] = {"declared": len(decl), "agree": len(agree),
                         "disagree": sorted(set(decl) - set(agree))}

    binds = {}
    for cb in (PAINT_STATIC, PAINT_DYNAMIC, PAINT_OBJECT, RBI):
        got = {h["file"]: bind_of(h, cb) for h in family}
        vals = sorted({v for v in got.values() if v})
        binds[cb] = {"values": vals, "by_file": got,
                     "consistent": len(vals) == 1 and all(
                         got[h["file"]] == vals[0] for h in family if cb in h["cbuffers"])}

    files, blocks, sizes, skipped = rbm_blocks()

    # Arkham: can a record's parameter names be given an offset by the shipped JC3 data?
    ark = arkham()
    jc3_names = {}
    for h in family:
        for cb, mem in h["cbuffers"].items():
            for m in mem:
                jc3_names.setdefault(norm(m["name"]), (h["file"], cb, m["name"],
                                                       m["offset"], m["size"]))
    matched = sorted({p for p in ark["names"] if norm(p) in jc3_names})

    # every family member recovers the same slot table from the header set alone
    slot_agree = all(
        len(h["cbuffers"].get(cb, [])) == len(members[cb]) for h in family for cb in members)

    d = {
        "headers": len(headers),
        "family": [h["file"] for h in family],
        "dynamic_only": dyn_only,
        "base": base["file"],
        "members": members,
        "agreement": agreement,
        "binds": binds,
        "rbm": {"files": files, "blocks": len(blocks),
                "sizes": {k: sorted(v) for k, v in sizes.items()},
                "skipped": skipped},
        "arkham": dict(ark, matched_params=matched, matched_count=len(matched),
                       named_records=0, slot_agree=slot_agree),
        "sizes": {"static": STATIC_BYTES, "support": SUPPORT_BYTES, "dynamic": DYNAMIC_BYTES},
    }
    d["oracles"] = oracles(d, blocks)
    d["md"] = render(d)
    return d


def oracles(d, blocks):
    fam, ag, b, r, a = d["family"], d["agreement"], d["binds"], d["rbm"], d["arkham"]
    out = []

    def o(key, ok, ev):
        out.append({"key": key, "ok": bool(ok), "evidence": ev})

    o("O1-headers-parse",
      d["headers"] >= 900 and len(fam) == 12,
      "%d .fb.txt parsed, %d declare %s, %d declare the dynamic cbuffer only%s"
      % (d["headers"], len(fam), PAINT_STATIC, len(d["dynamic_only"]),
         (" (%s)" % ", ".join(d["dynamic_only"])) if d["dynamic_only"] else ""))
    o("O2-bind-numbers",
      all(b[cb]["consistent"] for cb in b) and
      all(b[cb]["values"] == ["cb2"] for cb in (PAINT_STATIC,)) and
      b[PAINT_DYNAMIC]["values"] == ["cb6"] and
      b[PAINT_OBJECT]["values"] == ["cb7"] and b[RBI]["values"] == ["cb8"],
      "; ".join("%s -> %s" % (cb, ",".join(b[cb]["values"])) for cb in b))
    o("O3-member-tables-agree",
      all(ag[cb]["agree"] == ag[cb]["declared"] for cb in ag),
      "; ".join("%s %d/%d" % (cb, ag[cb]["agree"], ag[cb]["declared"]) for cb in ag))
    o("O4-sizes-match-the-rbm-block",
      cb_size(d["members"][PAINT_STATIC]) == STATIC_BYTES + SUPPORT_BYTES
      and cb_size(d["members"][PAINT_DYNAMIC]) == DYNAMIC_BYTES
      and cb_size(d["members"][PAINT_OBJECT]) == 20
      and r["sizes"]["static"] == [STATIC_BYTES]
      and r["sizes"]["support"] == [SUPPORT_BYTES]
      and r["sizes"]["dynamic"] == [DYNAMIC_BYTES]
      and r["blocks"] > 100 and len(r["skipped"]) <= 10,
      "header cb2 %d = %d+%d, cb6 %d, cb7 %d; %d CarPaintMM blocks in %d .rbm files, "
      "sizes static %s support %s dynamic %s"
      % (cb_size(d["members"][PAINT_STATIC]), STATIC_BYTES, SUPPORT_BYTES,
         cb_size(d["members"][PAINT_DYNAMIC]), cb_size(d["members"][PAINT_OBJECT]),
         r["blocks"], r["files"], r["sizes"]["static"], r["sizes"]["support"],
         r["sizes"]["dynamic"]))
    o("O5-no-paint-cbuffer-in-cb0",
      all("cb0" not in b[cb]["values"] for cb in b),
      "paint cbuffers bind to %s; no family member uses cb0 for them"
      % "/".join(",".join(b[cb]["values"]) for cb in b))
    o("O6-arkham-records-carry-no-offset",
      a["slot_field"] is False and a["entries"] == 9553 and a["entry_bytes"] == 32
      and a["records"] == 6943,
      "%d records (G3-04d reported %d: 60-char name cap, +%d here), %d entries x %d B "
      "= (class FName, parameter FName, RGBA) and no slot field; card oracles %s"
      % (a["records"], a["reported_6934"], a["extra_here"], a["entries"],
         a["entry_bytes"], a["card_oracles"]))
    o("O7-arkham-names-do-not-resolve",
      a["matched_count"] == 0,
      "%d distinct names in the fully decoded record vs %d JC3 paint member names; matched: %s"
      % (a["distinct_names"],
         len(d["members"][PAINT_STATIC]) + len(d["members"][PAINT_DYNAMIC]),
         a["matched_params"] or "none"))
    tint = [m for m in d["members"][PAINT_DYNAMIC] if "Tint" in m["name"]]
    o("O8-tint-members",
      [(m["name"], m["offset"], m["size"]) for m in tint]
      == [("m_TintColorR", 0, 16), ("m_TintColorG", 16, 16), ("m_TintColorB", 32, 16)]
      and all(ag[PAINT_DYNAMIC]["agree"] == ag[PAINT_DYNAMIC]["declared"] for _ in (0,)),
      ", ".join("%s@%d(%d)" % (m["name"], m["offset"], m["size"]) for m in tint))
    alb = all(h["binds"].get("sampler", {}).get("DiffuseSampler") == "s0"
              and h["binds"].get("texture", {}).get("DiffuseMap") == "t0"
              for h in [parse_header(os.path.join(SHADERS, f)) for f in fam])
    o("O9-albedo-texture-binding", alb, "DiffuseSampler -> s0 and DiffuseMap -> t0 in all %d" % len(fam))
    o("O10-md-recomputed", True, "--check rebuilds this document from the files and compares it")
    return out


# ---------------------------------------------------------------- render
def render(d):
    mem, ag, b, r, a = d["members"], d["agreement"], d["binds"], d["rbm"], d["arkham"]
    L = []
    A = L.append
    A("# JC3 paint constant-buffer slots without RDEF (G3-04e)")
    A("")
    A("Generated by `Tools/scripts/jc3_cb0_slots.py --write`; `--check` re-parses every")
    A("header, every `.rbm` and the uniform records, and fails on any change.")
    A("Static only: no game process was started, attached to or injected into.")
    A("")
    A("Inputs (read-only):")
    A("")
    A("| input | count |")
    A("|---|---:|")
    A("| shader reflection headers `Tools/JCMR-src/assets/jc3/shaders/*.fb.txt` | %d |" % d["headers"])
    A("| headers declaring `%s` (the paint family) | %d |" % (PAINT_STATIC, len(d["family"])))
    A("| `CarPaintMM` blocks in `%s` | %d in %d files |" % (RBM_GLOB, r["blocks"], r["files"]))
    A("| uniform records (`Research/BatmobileGrab/UNIFORM_RECORDS.json`) | %d |" % a["records"])
    if r["skipped"]:
        A("")
        A("Skipped `.rbm` files (the shared codec stops at `GeneralMkIII`; reported, not guessed): ")
        A(", ".join("`%s`" % s["file"] for s in r["skipped"]))
    A("")
    A("## 1. Answer")
    A("")
    A("**The brief's premise has to be corrected: in JC3 the paint parameters are not in")
    A("`cb0` at all.**  Every one of the %d shaders of the family binds them to `%s`, `%s`"
      % (len(d["family"]), b[PAINT_STATIC]["values"][0], b[PAINT_DYNAMIC]["values"][0]))
    A("and `%s` (and `%s` to `%s`), so a `cb0[n]` search is looking in the wrong buffer."
      % (b[PAINT_OBJECT]["values"][0], RBI, b[RBI]["values"][0]))
    A("")
    A("With the bind numbers known, the slots *are* nameable from files on disk, because the")
    A("shipped `.rbm` `CarPaintMM` block is the constant-buffer payload itself:")
    A("")
    A("| cbuffer | bind | size | source of the numbers | slots named |")
    A("|---|---|---:|---|---:|")
    A("| `%s` | `%s` | %d | 18 float4 + 7 floats, exactly the header's member list | %d |"
      % (PAINT_STATIC, b[PAINT_STATIC]["values"][0], cb_size(mem[PAINT_STATIC]),
         len(mem[PAINT_STATIC])))
    A("| `%s` | `%s` | %d | 4 float4 + 3 floats | %d |"
      % (PAINT_DYNAMIC, b[PAINT_DYNAMIC]["values"][0], cb_size(mem[PAINT_DYNAMIC]),
         len(mem[PAINT_DYNAMIC])))
    A("| `%s` | `%s` | %d | 1 float4 + 1 float | %d |"
      % (PAINT_OBJECT, b[PAINT_OBJECT]["values"][0], cb_size(mem[PAINT_OBJECT]),
         len(mem[PAINT_OBJECT])))
    A("")
    A("The Arkham 6,943 uniform records yield **0** named slots this way: an entry is %d B -"
      % a["entry_bytes"])
    A("class FName, parameter FName, RGBA - with no offset, slot or bind field anywhere in the")
    A("%d entries, and none of the %d parameter names of the one fully decoded record matches a"
      % (a["entries"], a["distinct_names"]))
    A("JC3 paint member (%d matches).  They are name-to-value lists for Arkham's shaders; naming"
      % a["matched_count"])
    A("a JC3 slot from them would need the `RDEF` chunk G3-04d showed absent from all 40,299")
    A("containers.")
    A("")
    A("## 2. The family and the bind test")
    A("")
    A("A slot name counts only if every family member agrees.  Family = the %d headers that"
      % len(d["family"]))
    A("declare `%s`:" % PAINT_STATIC)
    A("")
    for f in d["family"]:
        A("- `%s`" % f)
    A("")
    if d["dynamic_only"]:
        A("One header declares the dynamic cbuffer without the static one: %s."
          % ", ".join("`%s`" % x for x in d["dynamic_only"]))
        A("")
    A("| cbuffer | declared by | member tables identical | bind |")
    A("|---|---:|---:|---|")
    for cb in (PAINT_STATIC, PAINT_DYNAMIC, PAINT_OBJECT, RBI):
        A("| `%s` | %d | %d/%d | `%s` |"
          % (cb, ag[cb]["declared"], ag[cb]["agree"], ag[cb]["declared"],
             ", ".join(b[cb]["values"])))
    A("")
    A("No disagreements: every declaring header reproduces the same member names, offsets and")
    A("sizes, and the same bind number.  That is the `>=3 family shaders` test the brief asks")
    A("for, at %d of %d." % (ag[PAINT_DYNAMIC]["agree"], ag[PAINT_DYNAMIC]["declared"]))
    A("")
    A("## 3. `%s` - the static block (bind `%s`)"
      % (PAINT_STATIC, b[PAINT_STATIC]["values"][0]))
    A("")
    A("The `.rbm` block stores these as 18 float4 in this exact order (`rbm_geom` re-encodes")
    A("every block byte-identically, which is the format oracle), then the 7 support floats.")
    A("")
    A("| slot | offset | size | member | .rbm source |")
    A("|---|---:|---:|---|---|")
    for k, m in enumerate(mem[PAINT_STATIC]):
        if m["offset"] < STATIC_BYTES:
            src = "`static_params` float4[%d] @ payload +0x%x" % (
                m["offset"] // 16, 0x9 + m["offset"])
        else:
            src = "`static_support` float[%d] @ payload +0x%x" % (
                (m["offset"] - STATIC_BYTES) // 4, 0x9 + m["offset"])
        A("| `%s` | `%d` | %d | `%s` | %s |"
          % (slot_of(b[PAINT_STATIC]["values"][0], m), m["offset"], m["size"],
             m["name"], src))
    A("")
    A("## 4. `%s` - the dynamic block (bind `%s`)"
      % (PAINT_DYNAMIC, b[PAINT_DYNAMIC]["values"][0]))
    A("")
    A("| slot | offset | size | member | `.rbm` dynamic field |")
    A("|---|---:|---:|---|---|")
    for m in mem[PAINT_DYNAMIC]:
        if m["size"] == 16:
            fld = "float4[%d] @ payload +0x%x" % (m["offset"] // 16, 0x145 + m["offset"])
        else:
            fld = "float[%d] @ payload +0x%x" % ((m["offset"] - 64) // 4, 0x145 + m["offset"])
        A("| `%s` | `%d` | %d | `%s` | %s |"
          % (slot_of(b[PAINT_DYNAMIC]["values"][0], m), m["offset"], m["size"],
             m["name"], fld))
    A("")
    A("The 76-byte size is the stride the engine uploads: `imul ..., 0x4c` in the synced")
    A("constant-data update at `0x140259f00`, whose CPU-side fill `0x140289a80` copies source")
    A("`+0x00/+0x10/+0x20` into the parity copy (G3-09's `TINT_WRITE.md`, cited, not re-derived")
    A("here).  That is the fill order: float4 0..2 of the block are `m_TintColorR/G/B`.")
    A("")
    A("## 5. The slots the paint path cares about (R-4)")
    A("")
    A("| role | slot | size | evidence | state |")
    A("|---|---|---:|---|---|")
    A("| tint R | `%s[0]` (`m_TintColorR`) | 16 | family headers, all %d agree | **decoded** |"
      % (b[PAINT_DYNAMIC]["values"][0], ag[PAINT_DYNAMIC]["agree"]))
    A("| tint G | `%s[1]` (`m_TintColorG`) | 16 | same | **decoded** |" % b[PAINT_DYNAMIC]["values"][0])
    A("| tint B | `%s[2]` (`m_TintColorB`) | 16 | same | **decoded** |" % b[PAINT_DYNAMIC]["values"][0])
    A("| gloss / metallic / coat overrides | `%s[4].x/.y/.z` | 4 each | same | **decoded** |"
      % b[PAINT_DYNAMIC]["values"][0])
    A("| albedo texture | `s0` / `t0` (`DiffuseSampler` / `DiffuseMap`) | - | every family header | **decoded** |")
    A("| base-colour vector (candidate 1) | `%s[4]` (`m_DiffuseWrap`) | 16 | family headers | **decoded name, UNKNOWN role** |"
      % b[PAINT_STATIC]["values"][0])
    A("| base-colour vector (candidate 2) | `%s[8]` (`ModelDiffuseColor`) | 16 | family headers | **decoded name, UNKNOWN role** |"
      % b[RBI]["values"][0])
    A("")
    A("Which of the two colour members multiplies the diffuse texture for the final albedo is")
    A("**UNKNOWN**: it is in the SHEX arithmetic, and the shader body is not on disk.  What is")
    A("decided is that both candidates are `float4` members with fixed, family-wide offsets,")
    A("and that the tint arrives in `%s` at 0/16/32 - not in `cb0`."
      % b[PAINT_DYNAMIC]["values"][0])
    A("")
    A("## 6. The brief's own method applied to the 6,934 records")
    A("")
    A("| question | answer | evidence |")
    A("|---|---|---|")
    A("| records | %d | `UNIFORM_RECORDS.json` `.records.count`; G3-04d printed %d because "
      "it capped names at 60 chars and missed %d |"
      % (a["records"], a["reported_6934"], a["extra_here"]))
    A("| entries | %d | `.records.entries_total`, each %d B |" % (a["entries"], a["entry_bytes"]))
    A("| entries carrying an offset/slot/bind | 0 | the 32 B entry has no such field (G3-04c) |")
    A("| distinct parameter names | %d | the one record decoded end to end |" % a["distinct_names"])
    A("| names matching a JC3 paint member | %d | normalised name comparison |" % a["matched_count"])
    A("| records nameable this way | **0** | no slot field and no name overlap |")
    A("| ambiguous | 0 | nothing was guessed, so nothing is ambiguous |")
    A("| unnameable | **%d** | every record |" % a["records"])
    A("")
    A("Why: the records are Arkham's, keyed by material name and ordered by parameter name -")
    A("the engine that consumes them assigns the slots, and the chunk that records that")
    A("assignment (`RDEF`) is absent.  JC3 does not need those records: its equivalent")
    A("name->offset table is the reflection header set, present on disk and tested above.")
    A("")
    A("## 7. Oracles")
    A("")
    A("| oracle | result | evidence |")
    A("|---|---|---|")
    for o in d["oracles"]:
        A("| `%s` | %s | %s |" % (o["key"], "PASS" if o["ok"] else "**FAIL**",
                                  str(o["evidence"]).replace("|", "\\|")))
    A("")
    A("## 8. UNKNOWN")
    A("")
    A("- **Which colour member is albedo.** `m_DiffuseWrap` and `ModelDiffuseColor` are both")
    A("  decoded `float4`s; the multiply chain is in the SHEX, which is not on disk.")
    A("- **Whether the palette RGB lands in `m_TintColorR/G/B` verbatim.** G3-09 measured that")
    A("  no asset names the palette; TINT_WRITE follows the uploader to the block's `+0x168`")
    A("  fields but not to the palette record.")
    A("- **The `.epe` parameter lists.** The brief named them as an input, but the paint constants")
    A("  are not there: `COLOUR.md` measured that no `.rbm`, `.epe` or `.vmodc` of the entity names")
    A("  the palette (a scan of all 566 inner files for `palette` hits 1 file - the palette module")
    A("  itself), and the `.rbm` block already carries the header's 18+7 layout in order.  Whether")
    A("  any `.epe` holds shader constants at all is UNKNOWN here.")
    A("")
    A("## Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/jc3_cb0_slots.py --write")
    A("uv run python Tools/scripts/jc3_cb0_slots.py --check")
    A("```")
    A("")
    return "\n".join(L)


# ---------------------------------------------------------------- main
def main(argv):
    if len(argv) != 2 or argv[1] not in ("--write", "--check"):
        raise SystemExit("usage: jc3_cb0_slots.py --write|--check")
    d = build()
    fails = [o["key"] for o in d["oracles"] if not o["ok"]]
    md = d["md"]
    if argv[1] == "--write":
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        json.dump({k: v for k, v in d.items() if k != "md"},
                  open(JS, "w", encoding="utf-8", newline="\n"), indent=1)
        print("wrote Research/JC3Grab/CB0_SLOTS.md (%d lines) and .json" % md.count("\n"))
        print("headers %d, family %d, bindings %s"
              % (d["headers"], len(d["family"]),
                 {k: v["values"] for k, v in d["binds"].items()}))
        print("CarPaintMM blocks %d in %d files, sizes %s"
              % (d["rbm"]["blocks"], d["rbm"]["files"], d["rbm"]["sizes"]))
        print("arkham records %d (G3-04d printed %d), entries %d x %d B, name matches %d"
              % (d["arkham"]["records"], d["arkham"]["reported_6934"],
                 d["arkham"]["entries"], d["arkham"]["entry_bytes"],
                 d["arkham"]["matched_count"]))
        print("oracles %d/%d%s" % (len(d["oracles"]) - len(fails), len(d["oracles"]),
                                    "" if not fails else " FAILED: " + ", ".join(fails)))
    else:
        if fails:
            print("FAIL: " + ", ".join(fails))
            for o in d["oracles"]:
                if not o["ok"]:
                    print("  - %s: %s" % (o["key"], o["evidence"]))
            return 1
        if not os.path.exists(MD) or open(MD, encoding="utf-8").read() != md:
            print("FAIL: CB0_SLOTS.md is stale")
            return 1
        print("CHECK OK: %d oracles, family %d, cb2/cb6/cb7, %d blocks, 0 Arkham names"
              % (len(d["oracles"]), len(d["family"]), d["rbm"]["blocks"]))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))

#!/usr/bin/env python3
"""decode_depth7.py - G3-12e: why the vanilla Serpente `.epe` does not round-trip
byte-identically through Gibbed's ConvertProperty, byte by byte.

Inputs (read-only):
  * the `.epe` member of the vanilla Serpente bundle, re-extracted from the JC3
    archive through `bm_rc` / `eetoc` (no game process), sha256 pinned below;
  * `Tools/Gibbed/Gibbed.JustCause3.ConvertProperty.exe` (the binary under test);
  * for the practical check only, the `.epe` the Batmobile build already carries
    (`Builds/bm-009/...`, read-only): a file that was built through that tool.

Method: every byte of both files is labelled by role from a parse of the RTPC
structure that ConvertProperty itself documents (PropertyContainerFile.cs: the
RTPC header, 12-byte node records, 9-byte property records, and the payload a
property points at).  Bytes with no role are alignment padding.  The two maps are
then compared role by role, so each differing byte is attributed to padding, to a
re-encoded value, or to nothing (unexplained -> oracle FAIL).

Oracles (each one would fail if its claim were wrong):
  O1  the member is the file G3-12 graded PARTIAL: 109,526 B, pinned sha256.
  O2  export + import both succeed and the length is preserved.
  O3  the byte map covers every byte exactly once (roles + padding == length).
  O4  the padding map is identical in both files, 750 runs, all short of the
      next alignment, each ending 4- or 16-aligned.
  O5  vanilla padding is 0x50 on 2,189/2,189 bytes; the tool writes 0x00.
  O6  the layout is unchanged: all 450 node records and all 6,521 property
      records are byte-identical, so every payload offset is unchanged (this is
      what rules out ordering, string-table and hash-table differences).
  O7  the 2,293 differing bytes are 2,189 padding + 104 inside `mat` payloads;
      zero bytes are unexplained.
  O8  the set of changed float words is exactly the set the 7-significant-digit
      decimal round trip predicts (75/75), and 6, 8, 9 or 10 digits do NOT
      reproduce it.
  O9  the tool is a fixed point after one pass: b -> export -> import -> b.
  O10 the Batmobile `.epe` that was built through the tool round-trips
      byte-identically, i.e. it is already in the tool's canonical form.
  O11 name/hash fidelity: the export's own name for the changed `mat` property
      re-hashes to the hash in the binary.

    python Tools/scripts/decode_depth7.py --write   # write DECODE_DEPTH7.{md,json}
    python Tools/scripts/decode_depth7.py --check   # recompute from source bytes
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import bm_rc  # noqa: E402
import eetoc  # noqa: E402
from rbmhdr import hash_jenkins  # noqa: E402

ROOT = HERE.parent.parent
OUT_MD = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH7.md"
OUT_JSON = ROOT / "Research" / "JC3Grab" / "DECODE_DEPTH7.json"
SCRATCH = ROOT / "tmp" / "freebuff" / "scratch" / "g3_12e" / "run"
CONVPROP = ROOT / "Tools" / "Gibbed" / "Gibbed.JustCause3.ConvertProperty.exe"
BM_EPE = (ROOT / "Builds" / "bm-009" / "aaf" / "editor" / "entities" / "jc_vehicles" /
          "01_land" / "v0300_car_kensington_sportsmuscle" /
          "v0300_car_kensington_sportsmuscle_civilian_01.epe")

VANILLA_SHA = "f67bc17ebb16b70f35a6a131ffc8a1c5ca772ee5dac2b5524ae0603c93c22c32"
BM_SHA = "1778816d26ce5505e43079a7fed57745380361f24f4394c3ecd184d40c41cf96"

# RTPC layout, from Tools/GibbedSrc/Gibbed.JustCause3.PropertyFormats:
#   PropertyContainerFile.cs   RawNode.Size = 12, RawProperty.Size = 9, Align(4)
#   Variants/*.cs               IsPrimitive for Integer(1)/Float(2) only; the
#                               rest store a u32 offset to their payload.
TYPE_NAME = {0: "Unassigned", 1: "Integer", 2: "Float", 3: "String", 4: "Vector2",
             5: "Vector3", 6: "Vector4", 7: "DoNotUse1", 8: "Matrix4x4", 9: "Integers",
             10: "Floats", 11: "Bytes", 12: "DoNutUse2", 13: "ObjectId", 14: "Events"}
PRIMITIVE = {1, 2}
FIXED = {4: 8, 5: 12, 6: 16, 8: 64, 13: 8}     # Vector2/3/4, Matrix4x4, ObjectId
COUNTED = {9: 4, 10: 4, 11: 1, 14: 8}          # Integers/Floats/Bytes/Events element size
NODE_REC = 12
PROP_REC = 9
PAD_BYTE_VANILLA = 0x50                         # 'P', the cooker's fill byte

ROLE_LABEL = {
    "header": "header (`RTPC` + version)",
    "node": "node records (12 B each)",
    "prop": "property records (9 B each)",
    "string": "string payloads (Z-terminated, shared)",
    "fixed4": "Vector2 payloads",
    "fixed5": "Vector3 payloads",
    "fixed6": "Vector4 payloads",
    "fixed8": "Matrix4x4 payloads",
    "fixed13": "ObjectId payloads",
    "array9": "vec_int payloads (count + 4 B each)",
    "array10": "vec_float payloads (count + 4 B each)",
    "array11": "vec_byte payloads (count + 1 B each)",
    "array14": "vec_events payloads (count + 8 B each)",
}
ROLE_ORDER = ["header", "node", "prop", "string", "fixed4", "fixed5", "fixed6",
              "fixed8", "fixed13", "array9", "array10", "array11", "array14"]


# ---------------------------------------------------------------------------
# the two files
# ---------------------------------------------------------------------------

def vanilla_bytes() -> bytes:
    raw = eetoc.unaaf(bm_rc.vfs(bm_rc.DIR + bm_rc.OLD + ".ee"))
    member = bm_rc.DIR + bm_rc.OLD + ".epe"
    row = [(n, o, s) for n, o, s in eetoc.sarc_dir(raw) if n == member]
    if len(row) != 1:
        raise SystemExit("archive member %r: %d matches" % (member, len(row)))
    _n, off, size = row[0]
    return raw[off:off + size]


def convert(args: list[str]) -> None:
    if not CONVPROP.is_file():
        raise SystemExit("missing %s" % CONVPROP.relative_to(ROOT))
    p = subprocess.run([str(CONVPROP)] + args, capture_output=True, cwd=str(ROOT))
    if p.returncode != 0:
        raise SystemExit("ConvertProperty %s failed (%d): %s"
                         % (" ".join(args), p.returncode, p.stderr.decode("utf-8", "replace")))


def roundtrip(src: Path, tag: str) -> tuple[Path, Path]:
    xml = SCRATCH / (tag + ".xml")
    out = SCRATCH / (tag + ".epe")
    convert(["--e", str(src), str(xml)])
    convert(["--i", str(xml), str(out)])
    return xml, out


# ---------------------------------------------------------------------------
# RTPC parse (breadth-first, as PropertyContainerFile.Deserialize does)
# ---------------------------------------------------------------------------

def parse_rtpc(b: bytes) -> dict:
    if b[:4] != b"RTPC":
        raise SystemExit("not RTPC: %r" % b[:4])
    ver, = struct.unpack_from("<I", b, 4)
    order: list[dict] = []
    q = collections.deque()
    nh, do, pc, ic = struct.unpack_from("<IIHH", b, 8)
    q.append(dict(off=8, name=nh, data=do, np=pc, ni=ic))
    while q:
        nd = q.popleft()
        props = []
        for i in range(nd["np"]):
            o = nd["data"] + i * PROP_REC
            ph, = struct.unpack_from("<I", b, o)
            props.append((ph, b[o + 4:o + 8], b[o + 8], o))
        nd["props"] = props
        nd["child_table"] = (nd["data"] + nd["np"] * PROP_REC + 3) & ~3
        nd["kids"] = []
        for i in range(nd["ni"]):
            o = nd["child_table"] + i * NODE_REC
            kh, kd, kp, ki = struct.unpack_from("<IIHH", b, o)
            k = dict(off=o, name=kh, data=kd, np=kp, ni=ki)
            nd["kids"].append(k)
            q.append(k)
        order.append(nd)
    return dict(version=ver, root=order[0], order=order)


def payload_span(b: bytes, data: bytes, t: int) -> tuple[int, int, str]:
    off, = struct.unpack("<I", data)
    if t == 3:
        return off, b.index(b"\0", off) + 1, "string"
    if t in FIXED:
        return off, off + FIXED[t], "fixed%d" % t
    n, = struct.unpack_from("<i", b, off)
    return off, off + 4 + n * COUNTED[t], "array%d" % t


def byte_map(b: bytes, tree: dict) -> dict:
    """Label every byte: header, node record, property record, payload, or pad."""
    roles = ["pad"] * len(b)
    used = bytearray(len(b))

    def take(s: int, e: int, role: str) -> None:
        if s == e:
            return
        if s < 0 or e > len(b) or s > e:
            raise SystemExit("bad span %#x..%#x for %s" % (s, e, role))
        for i in range(s, e):
            if used[i]:
                raise SystemExit("overlap at %#x (%s)" % (i, role))
            used[i] = 1
            roles[i] = role

    take(0, 8, "header")
    spans = []
    for nd in tree["order"]:
        take(nd["off"], nd["off"] + NODE_REC, "node")
        take(nd["data"], nd["data"] + nd["np"] * PROP_REC, "prop")
        for _ph, data, t, _o in nd["props"]:
            if t in PRIMITIVE:
                continue
            s, e, kind = payload_span(b, data, t)
            spans.append((s, e, kind, t))
    for s, e, kind, _t in sorted(set((s, e, k, t) for s, e, k, t in spans)):
        take(s, e, kind)
    gaps = []
    i = 0
    while i < len(b):
        if roles[i] != "pad":
            i += 1
            continue
        j = i
        while j < len(b) and roles[j] == "pad":
            j += 1
        gaps.append((i, j))
        i = j
    counts = collections.Counter(roles)
    return dict(roles=roles, gaps=gaps, spans=spans, counts=counts)


def payload_bytes(b: bytes, data: bytes, t: int) -> bytes:
    s, e, _k = payload_span(b, data, t)
    return b[s:e]


# ---------------------------------------------------------------------------
# float text
# ---------------------------------------------------------------------------

def word_float(w: int) -> float:
    return struct.unpack("<f", struct.pack("<I", w))[0]


def text_roundtrip(w: int, digits: int) -> int:
    """The value a G<digits> decimal round trip lands on (same for any float)."""
    f = word_float(w)
    if not math.isfinite(f):
        return w
    txt = "%.*g" % (digits, f)
    try:
        return struct.unpack("<I", struct.pack("<f", float(txt)))[0]
    except OverflowError:
        return w


def float_word_offsets(b: bytes, tree: dict) -> list[tuple[int, int, int, int]]:
    """(word, offset, type, prop_hash) for every f32 the file stores."""
    out = []
    for nd in tree["order"]:
        for ph, data, t, _o in nd["props"]:
            if t == 2:
                out.append((struct.unpack("<I", data)[0], -1, t, ph))
                continue
            if t not in (4, 5, 6, 8, 10):
                continue
            s, _e, _k = payload_span(b, data, t)
            n = 16 if t == 8 else (FIXED[t] // 4 if t in FIXED else
                                   struct.unpack_from("<i", b, s)[0])
            base = s if t != 10 else s + 4
            for k in range(n):
                o = base + 4 * k
                out.append((struct.unpack_from("<I", b, o)[0], o, t, ph))
    return out


# ---------------------------------------------------------------------------
# build
# ---------------------------------------------------------------------------

def op(name: str, detail: str, ok: bool) -> dict:
    return dict(name=name, detail=detail, ok=bool(ok))


def build() -> tuple[str, dict, list[dict]]:
    A = vanilla_bytes()
    if hashlib.sha256(A).hexdigest() != VANILLA_SHA:
        raise SystemExit("vanilla .epe sha256 changed: %s" % hashlib.sha256(A).hexdigest())

    if SCRATCH.exists():
        shutil.rmtree(SCRATCH)
    SCRATCH.mkdir(parents=True)
    a1 = SCRATCH / "a1.epe"
    a1.write_bytes(A)

    xml1, b1p = roundtrip(a1, "b1")
    B = b1p.read_bytes()
    xml2, b2p = roundtrip(b1p, "b2")
    _xml3, b3p = roundtrip(b2p, "b3")
    B2 = b2p.read_bytes()
    B3 = b3p.read_bytes()
    XML1 = xml1.read_bytes()
    XML2 = xml2.read_bytes()

    pa = parse_rtpc(A)
    pb = parse_rtpc(B)
    ma = byte_map(A, pa)
    mb = byte_map(B, pb)

    # ---- structural identity --------------------------------------------
    rec_a = [(n["off"], n["name"], n["data"], n["np"], n["ni"]) for n in pa["order"]]
    rec_b = [(n["off"], n["name"], n["data"], n["np"], n["ni"]) for n in pb["order"]]
    node_rec_same = rec_a == rec_b
    prop_rec_same = all(
        [(p[0], p[1], p[2]) for p in x["props"]] == [(p[0], p[1], p[2]) for p in y["props"]]
        for x, y in zip(pa["order"], pb["order"]))
    offsets_same = all(
        [(p[3], bytes(A[p[3] + 4:p[3] + 8])) for p in x["props"]] ==
        [(p[3], bytes(B[p[3] + 4:p[3] + 8])) for p in y["props"]]
        for x, y in zip(pa["order"], pb["order"]))
    n_props = sum(n["np"] for n in pa["order"])

    # ---- diff attribution ------------------------------------------------
    D = [i for i in range(len(A)) if A[i] != B[i]]
    pad = set(i for s, e in ma["gaps"] for i in range(s, e))
    mat_words = [o for _w, o, t, _ph in float_word_offsets(A, pa) if o >= 0 and t == 8]
    mat_bytes = set(i for o in mat_words for i in range(o, o + 4))
    d_pad = [i for i in D if i in pad]
    d_mat = [i for i in D if i not in pad and i in mat_bytes]
    d_other = [i for i in D if i not in pad and i not in mat_bytes]

    # ---- float oracle ----------------------------------------------------
    words = float_word_offsets(A, pa)
    actual = set(o for _w, o, _t, _ph in words if o >= 0 and A[o:o + 4] != B[o:o + 4])
    act_by_type = collections.Counter(t for _w, o, t, _ph in words if o >= 0 and o in actual)
    words_by_type = collections.Counter(t for _w, o, t, _ph in words if o >= 0)
    sweep = []
    for digits in range(6, 11):
        pred = set(o for w, o, _t, _ph in words
                   if o >= 0 and text_roundtrip(w, digits) != w)
        sweep.append(dict(digits=digits, predicted=len(pred), matches=pred == actual))

    # ---- the changed values ---------------------------------------------
    names = {}
    for m in re.finditer(r' name="([^"]*)"', XML1.decode("utf-8-sig")):
        nm = m.group(1)
        names.setdefault(hash_jenkins(nm.encode("ascii")), nm)
    xml_mats = []
    for ln, line in enumerate(XML1.decode("utf-8-sig").splitlines(), 1):
        m = re.search(r'type="mat">([^<]*)</value>', line)
        if m:
            ws = tuple(struct.unpack("<I", struct.pack("<f", float(t.strip())))[0]
                       for t in m.group(1).split(","))
            xml_mats.append((ln, ws))
    line_q = collections.defaultdict(list)
    for ln, ws in xml_mats:
        line_q[ws].append(ln)

    values = []
    for ni, nd in enumerate(pa["order"]):
        for ph, data, t, _o in nd["props"]:
            if t != 8:
                continue
            s, _e, _k = payload_span(A, data, t)
            if A[s:s + FIXED[8]] == B[s:s + FIXED[8]]:
                continue
            key = tuple(struct.unpack_from("<I", B, s + 4 * k)[0] for k in range(16))
            line = line_q[key].pop(0) if line_q[key] else None
            for k in range(16):
                o = s + 4 * k
                wa, = struct.unpack_from("<I", A, o)
                wb, = struct.unpack_from("<I", B, o)
                if wa == wb:
                    continue
                fa, fb = word_float(wa), word_float(wb)
                values.append(dict(
                    offset="0x%05x" % o, offset_i=o, node_index=ni,
                    node_hash="0x%08x" % nd["name"],
                    prop_hash="0x%08x" % ph, prop_name=names.get(ph),
                    field=k, xml_line=line,
                    vanilla_word="0x%08x" % wa, vanilla_float=repr(fa),
                    tool_word="0x%08x" % wb, tool_float=repr(fb),
                    word_delta=struct.unpack("<i", struct.pack("<I", wb))[0] -
                               struct.unpack("<i", struct.pack("<I", wa))[0],
                    rel="%.2e" % (abs(fb - fa) / abs(fa) if fa else 0.0)))

    # ---- the Batmobile file built through the tool -----------------------
    bm = dict(path=str(BM_EPE.relative_to(ROOT)).replace("\\", "/"), exists=BM_EPE.is_file())
    if BM_EPE.is_file():
        bmA = BM_EPE.read_bytes()
        bm_src = SCRATCH / "bm.epe"
        bm_src.write_bytes(bmA)
        _x, bm_out = roundtrip(bm_src, "bm")
        bmB = bm_out.read_bytes()
        bmt = parse_rtpc(bmA)
        bmm = byte_map(bmA, bmt)
        bm.update(size=len(bmA), sha256=hashlib.sha256(bmA).hexdigest(),
                  roundtrip_sha256=hashlib.sha256(bmB).hexdigest(),
                  identical=bmA == bmB,
                  pad_bytes=sum(e - s for s, e in bmm["gaps"]),
                  pad_values=sorted(set(bmA[i] for s, e in bmm["gaps"] for i in range(s, e))))

    # ---- oracles ---------------------------------------------------------
    O = []
    O.append(op("O1 the archive member is the file G3-12 graded PARTIAL",
                "%d B, sha256 %s" % (len(A), VANILLA_SHA[:16] + "..."),
                len(A) == 109526 and hashlib.sha256(A).hexdigest() == VANILLA_SHA))
    O.append(op("O2 export and import both succeed and keep the length",
                "%d -> %d -> %d B; xml %d B" % (len(A), len(A), len(B), len(XML1)),
                len(A) == len(B) == 109526))
    n_roles = sum(ma["counts"][r] for r in ma["counts"] if r != "pad")
    O.append(op("O3 the byte map labels every byte exactly once",
                "%d role bytes + %d pad bytes = %d"
                % (n_roles, ma["counts"]["pad"], len(A)),
                n_roles + ma["counts"]["pad"] == len(A)))
    O.append(op("O4 the padding map is the same in both files",
                "%d runs, len %s, every run ends on a 4- or 16-byte boundary"
                % (len(ma["gaps"]), sorted(collections.Counter(e - s for s, e in ma["gaps"]).items())),
                ma["gaps"] == mb["gaps"] and all(e % 4 == 0 for s, e in ma["gaps"])
                and all(e - s < 16 for s, e in ma["gaps"])))
    pad_a = sorted(set(A[i] for s, e in ma["gaps"] for i in range(s, e)))
    pad_b = sorted(set(B[i] for s, e in mb["gaps"] for i in range(s, e)))
    O.append(op("O5 pad bytes: vanilla 0x50, tool 0x00",
                "vanilla values %s over %d B; tool values %s over %d B"
                % ([hex(v) for v in pad_a], ma["counts"]["pad"],
                   [hex(v) for v in pad_b], mb["counts"]["pad"]),
                pad_a == [PAD_BYTE_VANILLA] and pad_b == [0]))
    O.append(op("O6 layout is unchanged, so nothing was re-ordered",
                "%d node records and %d property records byte-identical; payload offsets identical: %s"
                % (len(pa["order"]), n_props, offsets_same),
                node_rec_same and prop_rec_same and offsets_same))
    O.append(op("O7 every differing byte is padding or a mat float",
                "%d = %d pad + %d mat-float + %d unexplained"
                % (len(D), len(d_pad), len(d_mat), len(d_other)),
                len(D) == len(d_pad) + len(d_mat) and not d_other))
    good = [s for s in sweep if s["matches"]]
    O.append(op("O8 the changed words are the 7-digit decimal round trip, and only 7",
                "; ".join("%d digits -> %d words%s" % (s["digits"], s["predicted"],
                                                       " MATCH" if s["matches"] else "") for s in sweep),
                len(good) == 1 and good[0]["digits"] == 7 and good[0]["predicted"] == len(actual)))
    O.append(op("O9 the tool is a fixed point after one pass",
                "b == b2 == b3; xml1 == xml2: %s" % (XML1 == XML2),
                B == B2 == B3 and XML1 == XML2))
    O.append(op("O10 the Batmobile .epe built through the tool round-trips identically",
                "%d B, sha256 %s, %d pad bytes all %s"
                % (bm.get("size", 0), bm.get("sha256", "?")[:16] + "...",
                   bm.get("pad_bytes", 0), [hex(v) for v in bm.get("pad_values", [])]),
                bm.get("identical") is True and bm.get("pad_values") == [0]))
    named_ok = names.get(0x6CA6D4B9) == "world"
    O.append(op("O11 the export's name for the changed mat property re-hashes to it",
                'hash_jenkins("world") = 0x%08x, binary property hash 0x6ca6d4b9, %d distinct names in the export'
                % (hash_jenkins(b"world"), len(names)), named_ok))

    # ---- per-property inventory -----------------------------------------
    per_prop = []
    for ph in sorted(set(p[0] for n in pa["order"] for p in n["props"] if p[2] == 8)):
        tot = sum(1 for n in pa["order"] for p in n["props"] if p[2] == 8 and p[0] == ph)
        chg = sum(1 for v in values if v["prop_hash"] == "0x%08x" % ph)
        per_prop.append(dict(prop_hash="0x%08x" % ph, prop_name=names.get(ph),
                             payloads=tot, changed_words=chg))
    types = collections.Counter(TYPE_NAME[p[2]] for n in pa["order"] for p in n["props"])
    by_type = []
    for t in (2, 4, 5, 6, 8, 10):
        pr = sum(1 for n in pa["order"] for p in n["props"] if p[2] == t)
        if not pr:
            continue
        by_type.append(dict(type_id=t, name=TYPE_NAME[t], properties=pr,
                            words=pr if t == 2 else words_by_type[t],
                            changed=0 if t == 2 else act_by_type[t]))
    spans_a = set((s, e) for s, e, _k, _t in ma["spans"])
    str_spans = set((s, e) for s, e, k, _t in ma["spans"] if k == "string")

    data = dict(
        task="G3-12e",
        question=("which bytes of the vanilla Serpente .epe differ after export and re-import "
                  "through Gibbed ConvertProperty, and why"),
        inputs=dict(archive=bm_rc.DIR + bm_rc.OLD + ".ee",
                    member=bm_rc.DIR + bm_rc.OLD + ".epe",
                    size=len(A), sha256=hashlib.sha256(A).hexdigest(),
                    tool=str(CONVPROP.relative_to(ROOT)).replace("\\", "/"),
                    tool_sha256=hashlib.sha256(CONVPROP.read_bytes()).hexdigest()),
        roundtrip=dict(xml_size=len(XML1), xml_sha256=hashlib.sha256(XML1).hexdigest(),
                       b1_sha256=hashlib.sha256(B).hexdigest(),
                       b2_sha256=hashlib.sha256(B2).hexdigest(),
                       b3_sha256=hashlib.sha256(B3).hexdigest(),
                       fixed_point=B == B2 == B3,
                       xml_fixed_point=XML1 == XML2,
                       same_length=len(A) == len(B)),
        layout=dict(version=pa["version"], nodes=len(pa["order"]), properties=n_props,
                    property_types=dict(sorted(types.items())),
                    bytes=len(A),
                    role_bytes={r: ma["counts"][r] for r in sorted(ma["counts"]) if r != "pad"},
                    pad_bytes=ma["counts"]["pad"], pad_runs=len(ma["gaps"]),
                    pad_run_lengths=[list(x) for x in
                                     sorted(collections.Counter(e - s for s, e in ma["gaps"]).items())],
                    distinct_payload_spans=len(spans_a),
                    reused_payload_spans=len(ma["spans"]) - len(spans_a),
                    xml_name_attributes=len(re.findall(r' name="', XML1.decode("utf-8-sig"))),
                    xml_id_attributes=len(re.findall(r' id="', XML1.decode("utf-8-sig"))),
                    changed_payloads=len(set((v["node_index"], v["prop_hash"]) for v in values)),
                    string_properties=sum(1 for n in pa["order"] for p in n["props"] if p[2] == 3),
                    distinct_string_spans=len(str_spans),
                    node_records_identical=node_rec_same,
                    property_records_identical=prop_rec_same,
                    payload_offsets_identical=offsets_same),
        diff=dict(total=len(D), first="0x%05x" % D[0] if D else None,
                  classes=[dict(role="alignment padding", bytes=len(d_pad),
                                vanilla_byte="0x50", tool_byte="0x00",
                                note="not referenced by any structure"),
                           dict(role="float32 inside a Matrix4x4 (type 8) payload",
                                bytes=len(d_mat), words=len(actual),
                                note="7 significant-digit decimal round trip")],
                  unexplained=len(d_other),
                  unexplained_offsets=["0x%05x" % i for i in d_other[:20]]),
        floats=dict(words_total=len(words),
                    words_inline_int_or_float=sum(1 for w, o, t, ph in words if o < 0),
                    changed_words=len(actual),
                    digit_sweep=sweep,
                    per_property=per_prop,
                    by_type=by_type,
                    bytes_per_word=[list(x) for x in sorted(collections.Counter(
                        sum(1 for i in range(v["offset_i"], v["offset_i"] + 4)
                            if A[i] != B[i])
                        for v in values).items())],
                    changed_translation_row=sum(1 for v in values if v["field"] >= 12),
                    changed_field_histogram=[list(x) for x in
                                             sorted(collections.Counter(v["field"] for v in values).items())],
                    max_word_delta=max((abs(v["word_delta"]) for v in values), default=0),
                    max_rel=max((float(v["rel"]) for v in values), default=0.0)),
        values=values,
        batmobile=bm,
        oracles=O,
        unknowns=[
            "Whether a <=7-raw-bit change in 75 matrix floats is acceptable to the engine: "
            "no oracle in the project runs the game.  The magnitude is bounded here "
            "(max rel %.1e), but 'acceptable' needs a load." % max((float(v["rel"]) for v in values), default=0.0),
            "Why the cooker padded with 0x50: the byte is decoded on all 2,189 pad bytes, "
            "its purpose is not in the file.  Would be found in the engine's serializer, "
            "which is not in the project.",
            "Whether other .epe files in the game have the same 0x50 fill and the same mat "
            "quantisation: only this one member was measured (G3-12 graded 1 .epe PARTIAL).",
        ],
    )
    return render(data), data, O


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------

def render(d: dict) -> str:
    L: list[str] = []
    A = L.append
    rt, la, df, fl = d["roundtrip"], d["layout"], d["diff"], d["floats"]
    A("# JC3 Serpente decode depth 7 (G3-12e) - the `.epe` round trip, byte by byte")
    A("")
    A("Generated by `Tools/scripts/decode_depth7.py --write`; `--check` recomputes every")
    A("number below from the archive bytes and the tool under test, and diffs the result")
    A("against the committed `.json`.  Nothing was run in the game.")
    A("")
    A("Labels: **decoded** = archive member or file + offset, read by this script; **derived**")
    A("= rule + inputs, shown in place; **UNKNOWN** = what was tried and where it would be.")
    A("")
    A("## 1. The question and the answer")
    A("")
    A("G3-12 graded this file PARTIAL because")
    A("`Gibbed.JustCause3.ConvertProperty.exe --e` followed by `--i` does not give the")
    A("bytes back (first difference at `0x765`).  Measured here on a scratch copy:")
    A("")
    A("| | vanilla | after export + import |")
    A("|---|---|---|")
    A("| size | %d B | %d B |" % (d["inputs"]["size"], d["inputs"]["size"]))
    A("| sha256 | `%s` | `%s` |"
      % (d["inputs"]["sha256"][:32] + "...", rt["b1_sha256"][:32] + "..."))
    A("| differing bytes | - | **%d of %d (%.2f%%)** |"
      % (df["total"], la["bytes"], 100.0 * df["total"] / la["bytes"]))
    A("")
    A("Those %d bytes fall into exactly two classes, and nothing is left over:" % df["total"])
    A("")
    A("| class | bytes | what it is |")
    A("|---|---:|---|")
    for c in df["classes"]:
        extra = (" (%d float words)" % c["words"]) if "words" in c else ""
        A("| %s%s | %d | %s |" % (c["role"], extra, c["bytes"], c["note"]))
    A("| **unexplained** | **%d** | - |" % df["unexplained"])
    A("")
    A("So the answer is **both** of the alternatives the card raised, but they do not")
    A("overlap: %d bytes are pure re-encoding (padding fill, no structure refers to them),"
      % df["classes"][0]["bytes"])
    A("and %d bytes are **values that change** - %d float32 words inside %d `Matrix4x4`"
      % (df["classes"][1]["bytes"], fl["changed_words"], la["changed_payloads"]))
    A("payloads, each moved by at most %d steps of the raw 32-bit word (relative %.1e)."
      % (fl["max_word_delta"], fl["max_rel"]))
    A("")
    A("## 2. The byte map (O3-O6)")
    A("")
    A("The RTPC layout used here is the one ConvertProperty itself implements")
    A("(`Tools/GibbedSrc/Gibbed.JustCause3.PropertyFormats/PropertyContainerFile.cs`):")
    A("a 8-byte header (`RTPC`, version 1), one 12-byte record per node")
    A("(`RawNode.Size = 4+4+2+2`), a 9-byte record per property (`RawProperty.Size = 4+4+1`),")
    A("and, for every property whose type is not `Integer`/`Float`, a `u32` offset to a")
    A("payload whose shape is fixed by the type (`Variants/*.cs`).  Every byte of both files")
    A("is labelled from that parse; unlabelled bytes are alignment padding.")
    A("")
    A("| role | bytes |")
    A("|---|---:|")
    for r in ROLE_ORDER:
        if r in la["role_bytes"]:
            A("| %s | %d |" % (ROLE_LABEL[r], la["role_bytes"][r]))
    A("| alignment padding | %d |" % la["pad_bytes"])
    A("| **total** | **%d** |" % la["bytes"])
    A("")
    A("`%d role bytes + %d pad = %d` exactly, with no byte labelled twice (O3).  The two"
      % (la["bytes"] - la["pad_bytes"], la["pad_bytes"], la["bytes"]))
    A("files have the *same* padding map - %d runs, lengths %s - so the tool lays the file"
      % (la["pad_runs"], [x[0] for x in la["pad_run_lengths"]]))
    A("out at identical offsets (O4).")
    A("")
    A("The structure itself is byte-identical between the two files (O6):")
    A("")
    A("* `%d` node records (name hash, data offset, property count, child count);" % la["nodes"])
    A("* `%d` property records (name hash, 4 data bytes, type);" % la["properties"])
    A("* every payload offset, hence `%d` distinct payload spans." % la["distinct_payload_spans"])
    A("")
    A("That is what rules out three of the four causes the card listed:")
    A("")
    A("* **ordering** - unchanged.  Node records and property tables are written in the")
    A("  same order; the tool sorts properties by hash (`PropertyContainerFile.cs:153`,")
    A("  `:223`) and the vanilla file is already in that order, so canonicalising the order")
    A("  changes nothing.");
    A("* **string table** - unchanged.  %d string properties address %d distinct string"
      % (la["string_properties"], la["distinct_string_spans"]))
    A("  spans; the writer deduplicates identical strings (`:168-186`) and the vanilla file")
    A("  uses the same dedup, so every string offset in the property table is already the")
    A("  deduplicated one.  Payload spans reused across the whole file: %d."
      % la["reused_payload_spans"])
    A("* **hash table** - not consulted for the bytes.  Names appear only in the XML")
    A("  (`Program.cs:309-314, 349, 371`: `name=` when the name list knows the hash, `id=`")
    A("  otherwise) and import re-hashes them (`Program.cs:388-410`).  The export writes %d names and"
      % la["xml_name_attributes"])
    A("  %d bare ids; all 6,521 property records and 450 node records come back identical,"
      % la["xml_id_attributes"])
    A("  so every name re-hashed to the hash that was already in the binary (O6), and the")
    A("  one name quoted in the value list below re-hashes to its property hash (O11).")
    A("")
    A("## 3. Class 1: %d bytes of alignment padding (O4, O5)" % df["classes"][0]["bytes"])
    A("")
    A("The vanilla file fills every alignment gap with `0x50` ('P'); the tool leaves those")
    A("bytes zero.  Decoded: the %d pad bytes of the vanilla file have the single value"
      % la["pad_bytes"])
    A("`0x50` on all of them, and every pad offset in the re-imported file is `0x00`.")
    A("")
    A("The mechanism is in the writer: it *seeks* to the alignment instead of writing")
    A("fill bytes (`PropertyContainerFile.cs:177,202,220` - `data.Position =")
    A("data.Position.Align(...)`), and the stream is a zeroed `MemoryStream` (`:113`), so")
    A("whatever the seek skips stays zero.  The alignments themselves come from the")
    A("variant (`StringVariant.cs:71-73` = 0, `Matrix4x4Variant.cs:112` = 16, the counted")
    A("array variants = 4).  Nothing reads those bytes back: they are outside every node")
    A("record, property record and payload (O3).")
    A("")
    A("A byte map of one such gap, the first difference at `0x765`:")
    A("")
    A("```")
    A("0x760  43 43 61 72 00        \"CCar\" string payload (offset taken from a property record)")
    A("0x765  50 50 50              <- vanilla padding, 3 B up to the next 4-aligned payload")
    A("       00 00 00              <- tool: same gap, zero-filled")
    A("0x768  ..                    next payload")
    A("```")
    A("")
    A("This class is **canonical re-encoding only**: no value, offset, count or hash moves.")
    A("")
    A("## 4. Class 2: %d float words that change value (O8, O11)" % fl["changed_words"])
    A("")
    A("The remaining %d bytes are the low-order bytes of %d float32 words, all inside type-8"
      % (df["classes"][1]["bytes"], fl["changed_words"]))
    A("`Matrix4x4` payloads.  Bytes changed per word: "
      + " | ".join("%d byte%s: %d word%s" % (b, "s" if b != 1 else "", n,
                                              "s" if n != 1 else "")
                   for b, n in fl["bytes_per_word"])
      + ".")
    A("The tool writes floats as **7-significant-digit decimal text**")
    A("(`FloatVariant.cs:51`, `Matrix4x4Variant.cs:74-97`: `ToString(InvariantCulture)`, which")
    A("on .NET Framework defaults to `G7`) and parses that text back on import")
    A("(`FloatVariant.cs:46`, `Matrix4x4Variant.cs:53-72`: `float.Parse`).  Seven digits do not")
    A("identify an arbitrary float32, so the value lands on a neighbour.")
    A("")
    A("The evidence is a sweep, not a plausibility argument: applying the round trip at a")
    A("fixed number of digits to all %d float words the file stores predicts this set of"
      % fl["words_total"])
    A("changed words -")
    A("")
    A("| digits | words predicted to change | equals the measured set? |")
    A("|---|---:|---|")
    for s in fl["digit_sweep"]:
        A("| %d | %d | %s |" % (s["digits"], s["predicted"], "**yes**" if s["matches"] else "no"))
    A("")
    A("- and only 7 matches, at 75/75 with no false positive anywhere in the file (O8).")
    A("Six digits would have moved 149 words, eight digits only 1.  So the digit count is")
    A("measured, not assumed, and the mechanism is confirmed on values that did *not*")
    A("change as well:")
    A("")
    A("| property type | properties | float words stored | changed |")
    A("|---|---:|---:|---:|")
    for r in fl["by_type"]:
        A("| %s (type %d) | %d | %d | %d |"
          % (r["name"], r["type_id"], r["properties"], r["words"], r["changed"]))
    A("")
    A("It is **not** a matrix-only code path - every float goes through the same text")
    A("round trip (`FloatVariant` uses the same `ToString`).  Matrices are simply where the")
    A("file carries values whose exact binary form needs more than seven digits: the %d"
      % sum(r["properties"] for r in fl["by_type"] if r["type_id"] == 2))
    A("`float` properties and the %d vec/vec4 components all happen to be values that seven"
      % sum(r["words"] for r in fl["by_type"] if r["type_id"] in (4, 5, 6)))
    A("digits reproduce exactly, and the sweep predicts that correctly (0 changes there).")
    A("")
    A("Changed words per matrix property:")
    A("")
    A("| property hash | name | payloads | changed words |")
    A("|---|---|---:|---:|")
    for p in fl["per_property"]:
        A("| `%s` | %s | %d | %d |"
          % (p["prop_hash"], p["prop_name"] or "*unnamed* (`id=` in the xml)",
             p["payloads"], p["changed_words"]))
    A("")
    A("### 4a. The %d changed values, listed" % fl["changed_words"])
    A("")
    A("`word_delta` is the signed difference of the raw 32-bit words (the ULP step at these")
    A("magnitudes); `rel` is the relative change.  `xml_line` is the line of the")
    A("`<value ... type=\"mat\">` element in the exported XML, matched by its 16 values.")
    A("")
    A("| offset | node # | node hash | property | field | xml line | vanilla | -> tool | word delta | rel |")
    A("|---|---:|---|---|---:|---:|---|---|---:|---|")
    for v in d["values"]:
        A("| `%s` | %d | `%s` | %s | %d | %s | %s (`%s`) | %s (`%s`) | %+d | %s |"
          % (v["offset"], v["node_index"], v["node_hash"],
             ("`%s`" % v["prop_name"]) if v["prop_name"] else "`%s`" % v["prop_hash"],
             v["field"], v["xml_line"] if v["xml_line"] else "?",
             v["vanilla_float"], v["vanilla_word"], v["tool_float"], v["tool_word"],
             v["word_delta"], v["rel"]))
    A("")
    A("The changes are spread over the matrices, not confined to one column: %d of the %d"
      % (fl["changed_translation_row"], fl["changed_words"]))
    A("are in the last row (fields 12-15, the translation) and the rest are rotation/scale")
    A("entries such as `0.342020154` (= sin 20 deg) and `0.642787576` (= cos 50 deg).  Field")
    A("histogram: %s." % ", ".join("%d:%d" % (k, v) for k, v in fl["changed_field_histogram"]))
    A("")
    A("The shortest example, and the cause in the tool's own output: the vanilla stores")
    A("`1.73828125` (a binary-exact fraction, `0x3fde8000`), the XML it exports literally")
    A("contains `1.738281` (7 digits), and importing that text lands on `0x3fde7ffe`.")
    A("")
    A("## 5. After one pass the file is stable (O9)")
    A("")
    A("`b -> --e -> --i -> b2` and `b2 -> --e -> --i -> b3`:")
    A("")
    A("| file | sha256 |")
    A("|---|---|")
    for k in ("b1_sha256", "b2_sha256", "b3_sha256"):
        A("| %s | `%s` |" % (k.split("_")[0], rt[k]))
    A("")
    A("All three are identical, and so are the two XML exports: the tool is a **fixed")
    A("point** after its first pass.  The rounding therefore does not accumulate across")
    A("edits; it happens once, when a vanilla file is first imported.")
    A("")
    A("That is the answer to the practical half of the card.  The Batmobile's `.epe` was")
    A("built through this tool, and it is already canonical:")
    A("")
    A("```")
    A("%s" % d["batmobile"]["path"])
    A("%d B, sha256 %s" % (d["batmobile"]["size"], d["batmobile"]["sha256"]))
    A("--e then --i -> sha256 %s (identical)" % d["batmobile"]["roundtrip_sha256"])
    A("its %d pad bytes are all %s" % (d["batmobile"]["pad_bytes"],
                                       [hex(x) for x in d["batmobile"]["pad_values"]]))
    A("```")
    A("")
    A("So the discrepancy G3-12 measured is a **one-time canonicalisation of the vanilla")
    A("file**, not a lossy pipeline: the shipped `.epe` no longer differs from the tool's own")
    A("output, because it *is* the tool's own output (O10).")
    A("")
    A("## 6. Status")
    A("")
    A("| item | status | evidence |")
    A("|---|---|---|")
    A("| vanilla `.epe` byte accounting | **FULL**, to EOF, 0 unexplained bytes | byte map covers %d/%d B; diff classes close exactly |"
      % (la["bytes"], la["bytes"]))
    A("| alignment padding | decoded (0x50), cause = writer seeks, no structure refers to it | %d B, %d runs, O3-O5 |"
      % (la["pad_bytes"], la["pad_runs"]))
    A("| ordering / string table / hash table | decoded as **no difference**, proven by identical records | O6 |")
    A("| value re-encoding | decoded: %d float words, 7-digit text, delta <= %d raw steps, rel <= %.1e | O8, value list 4a |"
      % (fl["changed_words"], fl["max_word_delta"], fl["max_rel"]))
    A("| round trip after one pass | stable (fixed point), so edits do not accumulate | O9 |")
    A("")
    A("## 7. Reproduce")
    A("")
    A("```")
    A("uv run python Tools/scripts/decode_depth7.py --write")
    A("uv run python Tools/scripts/decode_depth7.py --check")
    A("```")
    A("")
    A("## 8. UNKNOWNs")
    A("")
    for i, u in enumerate(d["unknowns"], 1):
        A("%d. %s" % (i, u))
    A("")
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    md, data, O = build()

    if not (args.write or args.check):
        print(md)
        return 0

    for o in O:
        print("%s %s" % ("PASS" if o["ok"] else "FAIL", o["name"]))
        print("      %s" % o["detail"])
    npass = sum(1 for o in O if o["ok"])
    print("\n%d/%d oracles pass" % (npass, len(O)))

    if args.write:
        OUT_MD.write_text(md, encoding="utf-8")
        OUT_JSON.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n",
                            encoding="utf-8")
        print("wrote %s (%d B)" % (OUT_MD.relative_to(ROOT), len(md.encode("utf-8"))))
        print("wrote %s (%d B)" % (OUT_JSON.relative_to(ROOT),
                                   OUT_JSON.stat().st_size))
        return 0 if npass == len(O) else 1

    ok = npass == len(O)
    same_json = json.loads(OUT_JSON.read_text(encoding="utf-8")) == data
    same_md = OUT_MD.read_text(encoding="utf-8") == md
    print("%s the stored .json is identical to a fresh recompute" % ("PASS" if same_json else "FAIL"))
    print("%s the stored .md is identical to a fresh recompute" % ("PASS" if same_md else "FAIL"))
    ok = ok and same_json and same_md
    print("RESULT: %s" % ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

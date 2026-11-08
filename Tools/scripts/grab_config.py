#!/usr/bin/env python3
"""G3-03: Batman: Arkham Knight config (ini) set, read from the shipped files.

Read-only. Writes (with --write) or re-derives and compares (with --check):
  Research/BatmobileGrab/CONFIG.md    human-readable tables + UNKNOWN list
  Research/BatmobileGrab/CONFIG.json  the same data, row by row

Sources (nothing is guessed; every row carries a label):
  decoded  read from a file (file + line)
  derived  computed from decoded facts; the rule is stated where it is used
  UNKNOWN  not decodable here; the attempt and where it would be are recorded

Steps:
  1. Every *.ini in BmGame/Config, BmGame/Config/PC and Engine/Config is read
     (encoding detected from the bytes: UTF-16LE+BOM / UTF-16LE / UTF-8+BOM / latin-1).
  2. Every [section] and every key=value line is parsed with its 1-based line number
     and its UE3 operator prefix (none, '+', '-', '.', '!').
  3. Every BasedOn= line is recorded with its section. A BasedOn inside [Configuration]
     is a file-chain edge; any other section's BasedOn is a settings-profile
     inheritance, recorded separately and NOT followed.
  4. File chains are followed from each file to its terminal by resolving the BasedOn
     text against BmGame\\ (the parent of Config). All edges are listed with the
     resolved path and whether it exists; that existence is the rule's oracle.
  5. Rows are matched into five categories by the regexes in CATEGORIES, matched
     against "<section> <key> <value>" of the row.
  6. A containment oracle tests the "the cooked *Bm*.ini is the merge of its chain"
     hypothesis per ini family; the measured numbers are reported, not a conclusion.
  7. Absence probes count rows matching keywords that would have to be present if the
     ini set carried the Batmobile's handling/colour pipeline, and list examples.

Usage:
  python -I grab_config.py --write
  python -I grab_config.py --check
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter, OrderedDict
from pathlib import Path

GAME = Path("E:/Games/Batman - Arkham Knight")
BM = GAME / "BmGame"
ROOTS = [BM / "Config", BM / "Config" / "PC", GAME / "Engine" / "Config"]
OUT_DIR = Path("E:/Modding/JustCause3/JC3-Batmobile/Research/BatmobileGrab")
OUT_MD = OUT_DIR / "CONFIG.md"
OUT_JSON = OUT_DIR / "CONFIG.json"

SCHEMA = "g3-03-config/1"

SECTION_RE = re.compile(r"^\s*\[(.+?)\]\s*$")
KV_RE = re.compile(r"^\s*([+\-.!]?)([A-Za-z0-9_.%\[\] ]+?)\s*=\s*(.*)$")
BASEDON_RE = re.compile(r"^\s*BasedOn\s*=\s*(.*?)\s*$", re.I)

# Category rules. Each pattern list is matched against the single string
# "<section> <key_as_written> <value>" of a row; a row is in the category if any pattern
# matches. The rules are printed in the MD next to the table, so the reader can re-run
# them by hand. Two patterns are deliberately case-sensitive: bare `LookUp`/`LookRight`
# would otherwise match `CountryCodeLookup` (measured false positive).
CATEGORIES = OrderedDict([
    ("batmobile", [re.compile(r"batmobile", re.I)]),
    ("vehicle", [re.compile(
        r"(?:\bvehicle|\bvehicles|\bcar\b|\bcars\b|wheel|tyre|tire\b|suspension|"
        r"steer|handbrake|\bthrottle|chassis|torque|bVehicle)", re.I)]),
    ("physics", [re.compile(
        r"(?:\bRB[A-Z_]|RigidBody|PhysX|Physics|PhysMaterial|(?-i:Apex)|\bGravity|"
        r"Substep|Collision|Friction|Damping|AsyncScene|bEnablePhys)", re.I)]),
    ("postprocess", [re.compile(
        r"(?:PostProcess|(?-i:\bPP_)|(?-i:Tonemap|ToneMap)|Exposure|EyeAdapt|ColorGrad|"
        r"ColorCorrect|GammaCorrection|\bBloom|MotionBlur|DepthOfField|\bDOF\b|"
        r"WhitePoint|MLAA|ScreenDirt|GlareBeam)", re.I)]),
    ("camera", [re.compile(
        r"(?:camera|\bFOV|ViewPitch|ScreenShake|bInvertJoystick|bInvertCapeGlide)", re.I),
        re.compile(r"LookUp|LookRight")]),
])

# Rows whose key matches this are printed with their full value (the "expanded" list).
HIGHLIGHT_RE = re.compile(
    r"(?:Gravity|Substep|PhysX|PhysMaterial|Physics|(?-i:Apex)|PostProcess|\bPP_[A-Z]|Bloom|"
    r"Grading|Gamma|Exposure|(?<![A-Za-z])Tonemap|EnableCameraAssist|FOV|Collision|"
    r"Friction)", re.I)

# Absence probes: keywords that would have to appear somewhere if this ini set carried
# the feature. The count and up to three examples are reported; no conclusion is drawn
# beyond "measured N rows".
PROBES = OrderedDict([
    ("suspension / droop / travel", re.compile(r"suspension|droop|\btravel\b", re.I)),
    ("steering rate / assist", re.compile(r"steer", re.I)),
    ("torque / horsepower / gear", re.compile(r"torque|horsepower|gearratio|\bgear\b", re.I)),
    ("wheel radius / size", re.compile(r"wheelradius|wheelsize|wheel_?scale", re.I)),
    ("RVehicle class reference", re.compile(r"RVehicle", re.I)),
    ("vehicle sim / kVehicle", re.compile(r"vehiclesim|kvehicle|vehicle_?sim", re.I)),
    ("tonemap / exposure / colour grade", re.compile(
        r"(?<![a-z])tonemap|exposure|eyeadapt|colorgrade|colorcorrect|whitepoint|\blut\b",
        re.I)),
    ("camera lag / turn rate / spring", re.compile(
        r"camera.{0,20}(lag|turnrate|spring|damp)|turnrate", re.I)),
])

UNKNOWNS = [
    ("which of these files the shipped game reads, and in which order",
     "the BasedOn lines give a chain order, but no file in the set states that the "
     "runtime reads the derived files first or the base last. No runtime oracle was "
     "used (G3-03 is a file-only card)."),
    ("the merge rule across a chain for a key defined more than once",
     "duplicate keys and the UE3 operators '+', '-', '.', '!' are written in the files; "
     "their effect at load time is not stated in any file here."),
    ("the relationship between the cooked *Bm*.ini and its chain",
     "measured by the containment oracle (above); the numbers leave a remainder in every "
     "family, so the relationship stays UNKNOWN."),
    ("where the Batmobile's handling values (steering, suspension, torque, wheel setup) live",
     "the absence probes below count the matches in this ini set. What they would be is "
     "not in these files; class defaults / archetype properties in packages were not "
     "read in this card (that is G3-01 / G3-06 territory)."),
    ("which tonemap / exposure / colour-grading values reach the screen",
     "the ini set carries PP_* multipliers, Bloom and MLAA switches only. Whether BmAK's "
     "on-screen tonemap and exposure come from a post-process chain held in packages or "
     "from level volumes was not decoded here."),
    ("the consumer of EnableCameraAssist ([BmGame.R3rdPersonCamera])",
     "the key is decoded with its value; the class property that reads it was not looked "
     "up in this card."),
    ("which [SystemSettingsBucketN] profile applies at runtime",
     "the buckets exist in the files with BasedOn=SystemSettings / SystemSettingsMobile "
     "/ SystemSettingsMobileTextureBias; the selection logic is not in the ini set."),
    ("the semantics of the settings-profile BasedOn (bucket composition)",
     "the BasedOn=SystemSettings lines inside bucket sections are decoded as text; how a "
     "bucket composes its parent is not stated in any file here."),
    ("DefaultCompat.ini's chain terminal",
     "BasedOn='..\\Engine\\Config\\BaseCompat.ini' resolves to a file that does not exist "
     "in the install (recorded as MISSING below)."),
    ("[IniVersion] semantics",
     "the section exists in several files with numeric rows; what reads it is not stated "
     "in the set."),
    ("the byte-level encoding of values containing non-ASCII text",
     "latin-1 decoding is lossless for the ASCII files here; no non-ASCII key or value "
     "was found that would need a code page."),
]


# ------------------------------------------------------------------ read / parse

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def decode_ini(path):
    """Return (text, encoding_label). Detection is from the bytes only."""
    b = path.read_bytes()
    if b[:2] == b"\xff\xfe":
        t, enc = b.decode("utf-16-le"), "utf-16-le+bom"
    elif b[:2] == b"\xfe\xff":
        t, enc = b.decode("utf-16-be"), "utf-16-be+bom"
    elif b[:3] == b"\xef\xbb\xbf":
        t, enc = b[3:].decode("utf-8"), "utf-8+bom"
    elif b and b.count(b"\x00") > len(b) // 4:
        t, enc = b.decode("utf-16-le"), "utf-16-le(no bom)"
    else:
        t, enc = b.decode("latin-1"), "latin-1"
    if t and t[0] == "\ufeff":
        t = t[1:]
    return t.replace("\r\n", "\n").replace("\r", "\n"), enc


def rel(p):
    p = Path(p)
    try:
        return p.relative_to(GAME).as_posix()
    except ValueError:
        return p.as_posix()


def parse_file(path):
    """Return dict with file facts, rows and basedon edges for one ini."""
    raw = path.read_bytes()
    text, enc = decode_ini(path)
    lines = text.split("\n")
    rows, basedon, malformed = [], [], []
    comments = 0
    section = ""
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if not s:
            continue
        if s.startswith(";"):
            comments += 1
            continue
        m = SECTION_RE.match(s)
        if m:
            section = m.group(1)
            continue
        b = BASEDON_RE.match(s)
        if b:
            basedon.append({
                "line": i,
                "section": section,
                "text": b.group(1),
                "kind": "file_chain" if section.strip().lower() == "configuration"
                        else "profile_inheritance",
            })
            continue
        m = KV_RE.match(line)
        if not m:
            malformed.append({"line": i, "section": section, "text": s})
            continue
        op, key, value = m.group(1) or "", m.group(2).strip(), m.group(3).rstrip()
        rows.append({
            "file": rel(path),
            "line": i,
            "section": section,
            "key": key,
            "operator": op,
            "value": value,
            "inline_comment": has_inline_comment(value),
        })
    return {
        "file": rel(path),
        "bytes": len(raw),
        "lines": len(lines),
        "encoding": enc,
        "sha256": sha256_bytes(raw),
        "rows": rows,
        "basedon": basedon,
        "malformed": malformed,
        "comment_lines": comments,
        "blank_lines": lines.count(""),
    }


def has_inline_comment(value):
    """True if a ';' appears outside double quotes (UE3 inline comment)."""
    inq = False
    for ch in value:
        if ch == '"':
            inq = not inq
        elif ch == ";" and not inq:
            return True
    return False


# ------------------------------------------------------------------ chains

def resolve(basedon_text):
    """Derived rule: BasedOn paths resolve against BmGame\\ (the parent of Config).

    Inputs: the text as written in the file. Oracle: every resolved target in the set
    that is not the known-missing BaseCompat.ini exists on disk (see the chain table).
    """
    txt = basedon_text.strip().strip('"').replace("\\", "/")
    return (BM / txt).resolve()


def build_chains(files):
    """Assign every file a chain id and an ordered ancestor list (base -> derived)."""
    by_path = {f["file"]: f for f in files}
    edge = {}
    for f in files:
        fs = [b for b in f["basedon"] if b["kind"] == "file_chain"]
        if len(fs) > 1:
            raise SystemExit(f"more than one [Configuration] BasedOn in {f['file']}")
        if fs:
            edge[f["file"]] = fs[0]

    def walk(f):
        seq, seen = [f], {f}
        while seq[-1] in edge:
            nxt = rel(resolve(edge[seq[-1]]["text"]))
            if nxt in seen:
                seq.append(nxt + " (CYCLE)")
                break
            seen.add(nxt)
            seq.append(nxt)
        return seq

    comps = {}
    for f in by_path:
        seq = walk(f)
        terminal = seq[-1]
        comps.setdefault(terminal, set()).update(seq)
    # A file's walk may cover a terminal shared with others; group by terminal.
    order = sorted(comps)
    for idx, terminal in enumerate(order, 1):
        cid = f"C{idx:02d}"
        for f in comps[terminal]:
            if f in by_path:
                by_path[f]["chain"] = cid
                by_path[f]["chain_terminal"] = terminal
    chains = []
    for idx, terminal in enumerate(order, 1):
        cid = f"C{idx:02d}"
        members = sorted((f for f in comps[terminal] if f in by_path),
                         key=lambda p: len(walk(p)), reverse=True)
        hops = []
        for order_i, m in enumerate(members, 1):
            e = edge.get(m)
            hop = {"order": order_i, "file": m,
                   "basedon_text": e["text"] if e else "",
                   "basedon_line": e["line"] if e else None,
                   "section": e["section"] if e else ""}
            if e:
                target = resolve(e["text"])
                hop["resolves_to"] = rel(target)
                hop["target_exists"] = target.exists()
            else:
                hop["resolves_to"] = ""
                hop["target_exists"] = None
            hops.append(hop)
        chains.append({"id": cid, "terminal": terminal, "members": hops})
    return chains


# ------------------------------------------------------------------ oracle / probes

def kv_map(f):
    """(section, key) -> list of values, in file order."""
    out = {}
    for r in f["rows"]:
        out.setdefault((r["section"], r["key"]), []).append(r["value"])
    return out


def containment(files, chains):
    """Derived: test 'the cooked Bm*.ini is the merge of its ini family'.

    Family = files whose basename ends with the same suffix, where the suffix is the
    basename of the cooked file minus its leading 'Bm'. The cooked member is the file
    whose basename starts with 'Bm'. Oracle: kitchen-sink containment of (section,key)
    pairs and value equality on the shared pairs.
    """
    by_name = {f["file"]: f for f in files}
    out = []
    for f in files:
        base = Path(f["file"]).name
        if not base.startswith("Bm"):
            continue
        suffix = base[2:]
        family = [g for g in files if Path(g["file"]).name.endswith(suffix)]
        if len(family) < 2:
            continue
        cooked = kv_map(f)
        other = {}
        for g in family:
            if g["file"] == f["file"]:
                continue
            for k, v in kv_map(g).items():
                other.setdefault(k, []).extend(v)
        shared = set(cooked) & set(other)
        agree = sum(1 for k in shared if sorted(cooked[k]) == sorted(other[k]))
        out.append({
            "cooked": f["file"],
            "suffix": suffix,
            "family": sorted(g["file"] for g in family),
            "chain": f.get("chain"),
            "cooked_pairs": len(cooked),
            "family_pairs": len(other),
            "shared_pairs": len(shared),
            "cooked_only": len(set(cooked) - set(other)),
            "family_only": len(set(other) - set(cooked)),
            "shared_value_equal": agree,
            "verdict": ("consistent with 'cooked = merge of family'"
                        if not (set(cooked) - set(other)) and not (set(other) - set(cooked))
                        else "not exact: relationship UNKNOWN"),
        })
    return out


def probes(all_rows):
    out = []
    for name, rx in PROBES.items():
        hits = [r for r in all_rows if rx.search(f"{r['section']} {r['key']} {r['value']}")]
        out.append({
            "name": name,
            "pattern": rx.pattern,
            "rows": len(hits),
            "examples": [f"{h['file']}:{h['line']} {h['key']}={md(h['value'])[:160]}"
                         for h in hits[:3]],
        })
    return out


# ------------------------------------------------------------------ md helpers

def md(s):
    return str(s).replace("|", "\\|").replace("\n", " ")


def short(v, n=200):
    v = md(v)
    return v if len(v) <= n else v[:n] + f" …({len(v)} chars)"


def lines_text(ls):
    ls = sorted(ls)
    if len(ls) <= 3:
        return ", ".join(str(x) for x in ls)
    return f"{ls[0]}–{ls[-1]} ({len(ls)})"


def group_rows(rows):
    groups = OrderedDict()
    for r in rows:
        groups.setdefault((r["file"], r["section"], r["key"]), []).append(r)
    return groups


def group_table(rows):
    out = ["| file | section | key | rows | line(s) | value (decoded) |",
           "|---|---|---|---|---|---|"]
    for (f, sec, key), rs in group_rows(rows).items():
        vals = [r["value"] for r in rs]
        distinct = sorted(set(vals))
        if len(distinct) == 1:
            v = short(distinct[0])
        else:
            v = f"{len(distinct)} distinct; e.g. {short(distinct[0], 120)}"
        out.append(f"| `{md(f)}` | `{md(sec) or '(none)'}` | `{md(key)}` | {len(rs)} | "
                   f"{lines_text([r['line'] for r in rs])} | {v} |")
    return out


# ------------------------------------------------------------------ build

def build():
    paths = []
    for root in ROOTS:
        if not root.exists():
            raise SystemExit(f"missing root: {root}")
        for p in sorted(root.glob("*.ini")):
            paths.append(p)
    seen = set()
    uniq = []
    for p in paths:
        k = str(p).lower()
        if k not in seen:
            seen.add(k)
            uniq.append(p)
    files = [parse_file(p) for p in uniq]

    chains = build_chains(files)
    for f in files:
        f["rows"].sort(key=lambda r: r["line"])
        for r in f["rows"]:
            hay = f"{r['section']} {r['key']} {r['value']}"
            r["categories"] = [c for c, rxs in CATEGORIES.items()
                               if any(rx.search(hay) for rx in rxs)]
            r["chain"] = f["chain"]

    all_rows = [r for f in files for r in f["rows"]]
    by_cat = OrderedDict((c, [r for r in all_rows if c in r["categories"]]) for c in CATEGORIES)
    highlights = [r for r in all_rows if HIGHLIGHT_RE.search(r["key"])]
    probe_list = probes(all_rows)
    contain = containment(files, chains)

    profile_basedon = [dict(f=b["file"], **b) for b in
                       (dict(bb, file=f["file"]) for f in files for bb in f["basedon"]
                        if bb["kind"] == "profile_inheritance")]

    data = {
        "schema": SCHEMA,
        "game_root": str(GAME),
        "roots": [rel(r) for r in ROOTS],
        "category_rules": {c: [rx.pattern for rx in rxs] for c, rxs in CATEGORIES.items()},
        "counts": {
            "files": len(files),
            "rows": len(all_rows),
            "basedon_file_chain": sum(len([b for b in f["basedon"]
                                           if b["kind"] == "file_chain"]) for f in files),
            "basedon_profile": len(profile_basedon),
            "malformed": sum(len(f["malformed"]) for f in files),
            "comment_lines": sum(f["comment_lines"] for f in files),
            "by_category": {c: len(rows) for c, rows in by_cat.items()},
            "rows_in_no_category": sum(1 for r in all_rows if not r["categories"]),
        },
        "files": [{k: f[k] for k in
                   ("file", "bytes", "lines", "encoding", "sha256", "chain",
                    "chain_terminal", "comment_lines", "blank_lines")}
                  for f in files],
        "chains": chains,
        "profile_basedon": profile_basedon,
        "containment": contain,
        "categories": {c: rows for c, rows in by_cat.items()},
        "highlights": highlights,
        "probes": probe_list,
        "malformed": [dict(m, file=f["file"]) for f in files for m in f["malformed"]],
        "unknowns": [{"what": w, "why": y} for w, y in UNKNOWNS],
    }
    return data


# ------------------------------------------------------------------ markdown

def render(data):
    L = []
    A = L.append
    c = data["counts"]
    A("# CONFIG - Batman: Arkham Knight ini set (G3-03)")
    A("")
    A("Generated by `Tools/scripts/grab_config.py --write`. Do not edit by hand; "
      "`--check` re-derives and compares.")
    A("")
    A("Labels: `decoded` = read from a file (file:line); `derived` = computed from "
      "decoded facts (rule given); `UNKNOWN` = not decodable here, see the UNKNOWN list.")
    A("")
    A(f"Files parsed: **{c['files']}** ({', '.join('`' + r + '`' for r in data['roots'])}). "
      f"Data rows: **{c['rows']}**. `[Configuration] BasedOn` edges: "
      f"**{c['basedon_file_chain']}**. Settings-profile BasedOn lines (not followed): "
      f"**{c['basedon_profile']}**. Malformed key lines: **{c['malformed']}**.")
    A("")
    A("Rows per category (derived, one row can be in several): " +
      ", ".join(f"{k} {v}" for k, v in c["by_category"].items()) +
      f"; rows in no category {c['rows_in_no_category']}.")
    A("")

    A("## Files (decoded)")
    A("")
    A("| file | bytes | lines | encoding | sha256 (first 16) | chain | BasedOn (line) |")
    A("|---|---|---|---|---|---|---|")
    bo = {}
    for ch in data["chains"]:
        for h in ch["members"]:
            bo[h["file"]] = h
    for f in data["files"]:
        h = bo.get(f["file"], {})
        b = (f"`{md(h['basedon_text'])}` ({h['basedon_line']})" if h.get("basedon_text") else "—")
        A(f"| `{md(f['file'])}` | {f['bytes']} | {f['lines']} | {f['encoding']} | "
          f"`{f['sha256'][:16]}` | {f['chain']} | {b} |")
    A("")

    A("## Chains (decoded `BasedOn` lines; derived resolution rule)")
    A("")
    A("Derived rule: each `BasedOn` in `[Configuration]` is resolved against `BmGame\\` "
      "(the parent of `BmGame\\Config`), not against the directory of the file that "
      "names it (`PCInput.ini` sits in `Config\\PC\\`). Oracle: every resolved target "
      "exists on disk except the one recorded MISSING. Order is base → derived as "
      "written; whether the runtime reads them in this order is **UNKNOWN**.")
    A("")
    for ch in data["chains"]:
        A(f"### {ch['id']} — terminal `{md(ch['terminal'])}` ({len(ch['members'])} file(s))")
        A("")
        A("| # | file | BasedOn (line, section) | resolves to | exists |")
        A("|---|---|---|---|---|")
        for h in ch["members"]:
            if h["basedon_text"]:
                b = f"`{md(h['basedon_text'])}` ({h['basedon_line']}, `{md(h['section'])}`)"
                A(f"| {h['order']} | `{md(h['file'])}` | {b} | `{md(h['resolves_to'])}` | "
                  f"{h['target_exists']} |")
            else:
                A(f"| {h['order']} | `{md(h['file'])}` | — (terminal) | — | — |")
        A("")

    A("## Settings-profile BasedOn lines (decoded, not followed)")
    A("")
    A("These `BasedOn=` lines are inside settings sections, not in `[Configuration]`; "
      "they name a profile to inherit from, so they are not file-chain edges. How a "
      "profile composes its parent is **UNKNOWN**.")
    A("")
    A("| file | line | section | BasedOn |")
    A("|---|---|---|---|")
    for b in data["profile_basedon"]:
        A(f"| `{md(b['file'])}` | {b['line']} | `{md(b['section'])}` | `{md(b['text'])}` |")
    A("")

    A("## Containment oracle (derived): is the cooked `Bm*.ini` the merge of its family?")
    A("")
    A("Family = the files whose basename ends with the cooked file's basename minus its "
      "leading `Bm` (e.g. `BmGame.ini` ↔ `*Game.ini`). Compared are `(section, key)` "
      "pairs and, on the shared pairs, the value sets. No conclusion is drawn where the "
      "numbers leave a remainder; those rows are UNKNOWN.")
    A("")
    A("| cooked | family size | cooked pairs | family pairs | shared | cooked-only | "
      "family-only | value-equal | verdict |")
    A("|---|---|---|---|---|---|---|---|---|")
    for t in data["containment"]:
        A(f"| `{md(t['cooked'])}` | {len(t['family'])} | {t['cooked_pairs']} | "
          f"{t['family_pairs']} | {t['shared_pairs']} | {t['cooked_only']} | "
          f"{t['family_only']} | {t['shared_value_equal']} | {t['verdict']} |")
    A("")

    titles = {
        "batmobile": "Batmobile",
        "vehicle": "Vehicles (vehicle / car / wheel / tyre / suspension / steer / "
                   "handbrake / throttle / chassis / torque)",
        "physics": "Physics (RB / PhysX / Apex / gravity / substeps / collision / friction)",
        "postprocess": "Post-process, tonemap, exposure, colour grading",
        "camera": "Camera",
    }
    for cat, rows in data["categories"].items():
        A(f"## {titles[cat]} — {len(rows)} row(s), "
          f"{len(group_rows(rows))} (file, section, key) group(s)")
        A("")
        A(f"Rule (decoded name match) on `<section> <key> <value>`: "
          f"`{md(' OR '.join(data['category_rules'][cat]))}`. A name match is **not** a "
          f"claim that the engine reads the key for the Batmobile.")
        A("")
        if not rows:
            A("No row in the set matches.")
            A("")
            continue
        L.extend(group_table(rows))
        A("")

    A(f"## Expanded key values — {len(data['highlights'])} row(s)")
    A("")
    A(f"Every row whose key matches `{md(HIGHLIGHT_RE.pattern)}`, with the value as "
      f"written (inline comment included).")
    A("")
    A("| file | line | section | key | value |")
    A("|---|---|---|---|---|")
    for r in data["highlights"]:
        A(f"| `{md(r['file'])}` | {r['line']} | `{md(r['section'])}` | `{md(r['key'])}` | "
          f"{short(r['value'], 300)} |")
    A("")

    A("## Absence probes (measured)")
    A("")
    A("Keywords that would have to appear somewhere in the set if it carried the "
      "feature. Counts are decoded; the reading is left to the UNKNOWN list.")
    A("")
    A("| probe | pattern | rows | example (file:line key=value) |")
    A("|---|---|---|---|")
    for p in data["probes"]:
        ex = "<br>".join(f"`{md(e)}`" for e in p["examples"]) or "—"
        A(f"| {p['name']} | `{md(p['pattern'])}` | {p['rows']} | {ex} |")
    A("")

    if data["malformed"]:
        A("## Malformed key lines (decoded, kept as written)")
        A("")
        for m in data["malformed"]:
            A(f"- `{md(m['file'])}:{m['line']}` `{md(m['section'])}` — `{short(m['text'], 200)}`")
        A("")

    A("## UNKNOWN")
    A("")
    for u in data["unknowns"]:
        A(f"- **{md(u['what'])}** — {md(u['why'])}")
    A("")
    return "\n".join(L) + "\n"


# ------------------------------------------------------------------ main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.write == a.check:
        ap.error("pass exactly one of --write / --check")

    data = build()
    md_text = render(data)
    js_text = json.dumps(data, indent=1, ensure_ascii=False) + "\n"

    if a.write:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        OUT_MD.write_text(md_text, encoding="utf-8", newline="\n")
        OUT_JSON.write_text(js_text, encoding="utf-8", newline="\n")
        c = data["counts"]
        print(f"wrote {OUT_MD} ({len(md_text)} bytes)")
        print(f"wrote {OUT_JSON} ({len(js_text)} bytes)")
        print(f"files={c['files']} rows={c['rows']} "
              f"basedon_file_chain={c['basedon_file_chain']} "
              f"basedon_profile={c['basedon_profile']} malformed={c['malformed']} "
              f"categories={c['by_category']} uncategorised={c['rows_in_no_category']}")
        return 0

    ok = True
    if not OUT_JSON.exists() or not OUT_MD.exists():
        print(f"MISSING output(s): {OUT_JSON} {OUT_MD}")
        return 1
    on_disk = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    if on_disk == data:
        print(f"json ok: re-derived data == {OUT_JSON.name} "
              f"({data['counts']['rows']} rows, {data['counts']['files']} files)")
    else:
        ok = False
        print("json MISMATCH")
        for k in data:
            if on_disk.get(k) != data[k]:
                print(f"  differs: {k}")
    disk_md = OUT_MD.read_text(encoding="utf-8")
    if disk_md == md_text:
        print(f"md ok: re-rendered text == {OUT_MD.name} ({len(md_text)} bytes)")
    else:
        ok = False
        print(f"md MISMATCH ({len(disk_md)} on disk vs {len(md_text)} re-rendered)")

    # Row fidelity: every row's (file, line) must re-read as a line that contains the
    # recorded key and value verbatim. This is the containment oracle for the table.
    cache, bad, checked = {}, 0, 0
    for f in data["files"]:
        cache[f["file"]] = decode_ini(GAME / f["file"])[0].split("\n")
    for cat_rows in data["categories"].values():
        for r in cat_rows:
            checked += 1
            line = cache[r["file"]][r["line"] - 1]
            if r["key"] not in line or r["value"] not in line:
                bad += 1
                if bad <= 5:
                    print(f"  row mismatch {r['file']}:{r['line']} key={r['key']!r}")
    print(f"row fidelity: {checked - bad}/{checked} rows re-read from disk contain "
          f"their key and value verbatim")
    if bad:
        ok = False
    print("CHECK OK" if ok else "CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

"""t_md2_emp_state.py - T-MD2 / T-WP4 / T-WP5: does JC3 carry an EMP vehicle-disable state?

The question the ledger rows leave open is the *disable*, not the blast: a w618 missile
clone can fly and an entity-level `CForcePulse` can explode, but nothing observed so far
stalls the target.

This script answers the data half of that question by measurement, read-only:

  1. **Engine vocabulary.** The executable's string table is searched for every EMP /
     electricity / disable token, each is pinned to its file offset, and the run of
     vehicle-variable names around `is_disabled_by_emp` is printed as context.
  2. **Data bindings.** Every `.ee` / `.epe` / `.vmodc` / `.afsmb` / `.asb` entry named in
     `Research/JC3Grab/INDEX.jsonl` is read out of the live archives and searched twice:
     for the literal token, and for its **Jenkins hash** (an `.epe` stores property names
     as `type byte + uint32 hash`, so a literal search alone proves nothing). Two controls
     that shipped data does use (`invulnerable`, `is_in_water`) must hit, or the method is
     not calibrated.
  3. **Pulse flags.** `FORCEPULSE.json` is counted for the three flag members that differ
     between the EMP truck's pulse and the plain car blast, so the report can say whether
     that combination is unique to the EMP.
  4. **Module vocabulary.** `VOCABULARY.md` (52 module types, 1,421 members) is scanned for
     any member named emp / disable / stall / immobil.
  5. **BmAK side.** `BMSDK_OFFSETS.json` gives `RBatmobileEMP` / `RBatmobileEMPMissile` with
     member offsets; `objects.jsonl` gives which of those members the three shipped EMP
     burst archetypes actually serialise (a member absent from the tags is not populated).

Writes `Research/JC3Grab/EMP_DISABLE.json`. `--check` re-derives and compares it to disk and
exits 1 on any drift, so the report's numbers are re-provable without re-reading this prose.

Read-only: no game launch, nothing installed, no archive written.

Usage:
  python Tools/scripts/t_md2_emp_state.py --write
  python Tools/scripts/t_md2_emp_state.py --check
  python Tools/scripts/t_md2_emp_state.py dump
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)

from rbmhdr import hash_jenkins  # noqa: E402

OUT = os.path.join(ROOT, "Research", "JC3Grab", "EMP_DISABLE.json")
INDEX = os.path.join(ROOT, "Research", "JC3Grab", "INDEX.jsonl")
PULSES = os.path.join(ROOT, "Research", "JC3Grab", "FORCEPULSE.json")
VOCAB = os.path.join(ROOT, "Research", "JC3Grab", "VOCABULARY.md")
OFFSETS = os.path.join(ROOT, "Research", "BatmobileGrab", "BMSDK_OFFSETS.json")
OBJECTS = os.path.join(ROOT, "Research", "BatmobileGrab", "objects.jsonl")
GAME = os.environ.get("JC3_GAME", r"D:\Games\Just Cause 3")
EXE = os.path.join(GAME, "JustCause3.exe")

# Tokens pinned in this session's read of JustCause3.exe (51,083,264 B). `--check` fails if any
# token is no longer at its offset, so a repatched executable is detected rather than tolerated.
EXE_TOKENS = {
    "is_disabled_by_emp": 0x24EA080,
    "enemy.mech.exit_emp_state": 0x24D5238,
    "dlc3.electrical_damage_hud.off": 0x2468B28,
    "dlc3.electrical_damage_hud.on": 0x2468B48,
    "UpdateElectricityWarning": 0x24AFFE8,
    "electricity_armor": 0x2476EB3,
    "SetVehiclePartVulnerability": 0x241B020,
    "CEMPWeapon": 0x23E9428,
    ".?AVCEMPWeapon@@": 0x2D6E058,
}

# Probe names for the data scan. `invulnerable` and `is_in_water` are controls: shipped
# entities are known/proven to carry them, so a 0 on the controls means the scan is broken.
PROBES = ["invulnerable", "is_in_water", "is_disabled_by_emp", "electricity_armor"]
CONTROLS = {"invulnerable", "is_in_water"}
ENTRY_EXTS = (".ee", ".epe", ".vmodc", ".afsmb", ".asb")

BMAK_CLASSES = ["RBatmobileEMP", "RBatmobileEMPMissile", "RBatmobileMissile"]


def exe_probe() -> dict:
    data = open(EXE, "rb").read()
    rows = {}
    for tok, off in EXE_TOKENS.items():
        b = tok.encode()
        rows[tok] = {
            "offset": f"0x{off:X}",
            "at_offset": data[off:off + len(b)] == b,
            "occurrences": data.count(b),
        }
    # the block `is_disabled_by_emp` sits in: 24 printable names either side, in file order
    block, start = [], EXE_TOKENS["is_disabled_by_emp"]
    runs = [m for m in re.finditer(rb"[\x20-\x7e]{3,80}\x00", data[
        max(0, start - 0x600):start + 0x600])]
    for m in runs:
        block.append({"addr": hex(max(0, start - 0x600) + m.start()),
                      "name": m.group()[:-1].decode("ascii")})
    return {
        "exe": EXE,
        "size": len(data),
        "sha_ok_tokens": all(r["at_offset"] for r in rows.values()),
        "tokens": rows,
        "variable_name_block": block,
    }


def data_scan() -> dict:
    probes = {n: hash_jenkins(n.encode()).to_bytes(4, "little") for n in PROBES}
    literal = {n: 0 for n in PROBES}
    hashed = {n: [] for n in PROBES}
    entries = 0
    nbytes = 0
    files: dict[str, object] = {}
    for line in open(INDEX, encoding="utf-8"):
        r = json.loads(line)
        path = r["path"]
        if not path.endswith(ENTRY_EXTS):
            continue
        arc = os.path.join(GAME, *r["archive"].split("/")) + ".arc"
        if arc not in files:
            try:
                files[arc] = open(arc, "rb")
            except OSError:
                files[arc] = None
        f = files[arc]
        if f is None:
            continue
        entries += 1
        f.seek(r["offset"])
        buf = f.read(r["size"])
        nbytes += len(buf)
        for name in PROBES:
            literal[name] += buf.count(name.encode())
            if probes[name] in buf:
                hashed[name].append(path)
    for f in files.values():
        if f:
            f.close()
    return {
        "entries": entries,
        "bytes": nbytes,
        "literal_occurrences": literal,
        "hash_occurrences": {k: len(v) for k, v in hashed.items()},
        "hash_hit_paths": {k: v[:5] for k, v in hashed.items() if v},
        "probe_hashes": {n: f"0x{int.from_bytes(h, 'little'):08X}" for n, h in probes.items()},
        # An `.epe` stores property names as hashes, so the controls are calibrated by the
        # hash hit (289 / 160 in this session), not by a literal string.
        "calibrated": all(hashed[c] for c in CONTROLS),
    }


def pulse_flags() -> dict:
    d = json.load(open(PULSES, encoding="utf-8"))
    triples: dict[str, int] = {}
    emp = None
    total = 0
    for e in d["entities"]:
        for p in e["pulses"]:
            total += 1
            pr = p["props"]
            t = (pr.get("id:4912FC04"), pr.get("id:AE6F7EFF"), pr.get("id:CF4F7880"))
            triples[",".join("" if x is None else str(x) for x in t)] = \
                triples.get(",".join("" if x is None else str(x) for x in t), 0) + 1
            if p.get("name") == "EMP":
                emp = {"entity": e.get("entity"), "props": pr}
    return {"pulses": total, "flag_triples": triples, "emp_pulse": emp}


def vocabulary_absence() -> dict:
    hits = []
    for line in open(VOCAB, encoding="utf-8"):
        if not line.startswith("| `"):
            continue
        member = line.split("|")[1]
        if re.search(r"emp|disab|stall|immobil", member, re.I):
            hits.append(member.strip())
    return {"member_rows_scanned": sum(1 for line in open(VOCAB, encoding="utf-8")
                                       if line.startswith("| `")),
            "hits": hits}


def bmak_side() -> dict:
    off = json.load(open(OFFSETS, encoding="utf-8"))
    out = {}
    for cls in BMAK_CLASSES:
        c = off.get(cls)
        if not c:
            continue
        out[cls] = {
            "size": c.get("size"),
            "super": c.get("super"),
            "members": [{"name": m["member"], "kind": m["kind"], "offset": m["offset"]}
                        for m in c["properties"]],
        }
    serialized = {}
    for line in open(OBJECTS, encoding="utf-8"):
        if '"RBatmobileEMP"' not in line and '"RBatmobileEMPMissile"' not in line:
            continue
        o = json.loads(line)
        cls = o.get("class")
        if cls not in ("RBatmobileEMP", "RBatmobileEMPMissile"):
            continue
        serialized.setdefault(cls, []).append({
            "object": o.get("name"),
            "package": o.get("package"),
            "members_offsets": [t.get("offset") for t in o.get("tags", [])],
            "named": [t.get("name") for t in o.get("tags", []) if t.get("name")],
        })
    return {"classes": out, "serialized": serialized}


def build() -> dict:
    return {
        "schema": 1,
        "task": "T-MD2 / T-WP4 / T-WP5 - is the EMP vehicle-disable reachable from JC3 data?",
        "generated_by": "Tools/scripts/t_md2_emp_state.py --write",
        "exe": exe_probe(),
        "data": data_scan(),
        "pulse": pulse_flags(),
        "vocabulary": vocabulary_absence(),
        "bmak": bmak_side(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("dump", nargs="?")
    a = ap.parse_args()
    fresh = build()
    if a.write:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(fresh, f, indent=1, sort_keys=True)
            f.write("\n")
        print(f"wrote {OUT}")
        d = fresh["data"]
        print(f"PASS: {d['entries']} entries / {d['bytes']} B scanned; "
              f"controls calibrated={d['calibrated']}; "
              f"is_disabled_by_emp literal={d['literal_occurrences']['is_disabled_by_emp']} "
              f"hash={d['hash_occurrences']['is_disabled_by_emp']}")
        return 0
    old = json.load(open(OUT, encoding="utf-8"))
    if fresh != old:
        for k in fresh:
            if fresh[k] != old.get(k):
                print(f"FAIL: {k} drifted")
        return 1
    d = fresh["data"]
    assert d["calibrated"], "controls did not hit: the scan is not calibrated"
    assert d["hash_occurrences"]["is_disabled_by_emp"] == 0
    assert fresh["exe"]["sha_ok_tokens"]
    print(f"PASS: EMP_DISABLE.json re-derives byte for byte "
          f"({d['entries']} entries / {d['bytes']} B; controls hit; "
          f"is_disabled_by_emp 0 literal / 0 hash)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

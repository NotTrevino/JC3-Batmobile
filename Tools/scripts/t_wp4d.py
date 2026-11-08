#!/usr/bin/env python3
"""T-WP4d - the corrective re-issue of T-WP4c (tracker + Immobiliser).

Two labels in `Working/Translation/T_WP4C_TRACKER_EMP.md` are wrong:
  (1) the tracker's `bInstantFire = true` was borrowed from the EMP launcher's archetype row;
  (2) the Immobiliser impact sound and `Projectile.Damage 60.0` were quoted from
      `Batmobile_EMPMissile_Projectile`, which no launcher points at, while *both* of the
      launcher's payload pointers resolve to `Batmobile_EMPMissile_Projectile_ForCars`.

This script never edits `t_wp4c.py` or the T-WP4c document. It re-reads the cooked packages
through `Tools/scripts/upk_read.py`, the BmSDK layout under `Working/vendor/BmSDK`, and the
frozen T-WP4c text (only to quote what it used to say), and writes:

  Working/Translation/T_WP4D_TRACKER_EMP.md
  Working/Translation/T_WP4D_TRACKER_EMP.json

--write  write both
--check  recompute every number from the bytes and compare byte for byte

Read-only on the game install: no launch, no injection, no attach.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "Tools", "scripts"))

from upk_read import Package, export_summary  # noqa: E402

OUT_MD = "Working/Translation/T_WP4D_TRACKER_EMP.md"
OUT_JSON = "Working/Translation/T_WP4D_TRACKER_EMP.json"
WP4C_MD = "Working/Translation/T_WP4C_TRACKER_EMP.md"

PACKAGES = ("Playable_Batmobile_SF.upk", "Playable_BatmobileMK2_SF.upk",
            "Playable_BatmobileFunhouse_SF.upk", "Playable_BatmobileJoker_SF.upk")

LAUNCHER = "Batmobile_EMP_Missile_Launcher"
TRACKER = "Vehicle_Tracker"
SIBLING = "Batmobile_EMPMissile_Projectile"
FIRED = "Batmobile_EMPMissile_Projectile_ForCars"

# (doc name, offset, exact SDK field name) - the offset is what this card adjudicates,
# the name is checked against Working/vendor/BmSDK on every run (see sdk_probe()).
FIELDS = (
    ("Actor.Tag", 360, "Tag"),
    ("RInventoryGadget.Mesh", 792, "Mesh"),
    ("RVehicleWeapon.FireStartEvent", 2176, "FireStartEvent"),
    ("RVehicleWeapon.IndividualFireEvent", 2200, "IndividualFireEvent"),
    ("Projectile.MyDamageType", 712, "MyDamageType"),
    ("Projectile.Damage", 728, "Damage"),
    ("Projectile.DamageRadius", 732, "DamageRadius"),
    ("RBatmobileMissile.ExplosionTemplate", 960, "ExplosionTemplate"),
    ("RBatmobileMissile.ExlposionSound", 968, "ExlposionSound"),
    ("RBatmobileMissile.AccelRate", 1064, "AccelRate"),
    ("RPursuitModeMissileLauncher.ProjectileArchetype", 2428, "ProjectileArchetype"),
    ("RPursuitModeMissileLauncher.LaunchSocketName", 2436, "LaunchSocketName"),
    ("RPursuitModeMissileLauncher.LaunchRotationOffset", 2452, "LaunchRotationOffset"),
    ("RPursuitModeMissileLauncher.bInstantFire", 2464, "bInstantFire"),
    ("RBatmobileEMPMissile.ProjectileForCarsArchetype", 2492, "ProjectileForCarsArchetype"),
    ("RBatmobileEMPMissile.MissileLockOnDuration", 2560, "MissileLockOnDuration"),
    ("RBatmobileEMPMissile.CivilianMissileLockOnDuration", 2564, "CivilianMissileLockOnDuration"),
)
NAME_OF = {off: name for name, off, _sdk in FIELDS}


def p(rel: str) -> str:
    return os.path.join(ROOT, rel)


def read(rel: str) -> str:
    with open(p(rel), "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def install_root() -> str:
    hits = sorted(glob.glob("E:/Games/*/BmGame/CookedPCConsole"))
    if not hits:
        hits = sorted(glob.glob("D:/Games/*/BmGame/CookedPCConsole"))
    if not hits:
        raise SystemExit("no BmGame/CookedPCConsole under E:/Games or D:/Games")
    return hits[0]


# ---------------------------------------------------------------- package reads

class Pkg:
    """One cooked package: a name index, cached tag walks, and a full census."""

    def __init__(self, path: str):
        self.path = path
        self.name = os.path.basename(path)
        self.pkg = Package(path)
        self.exports = self.pkg.exports
        self._index: dict[str, int] = {}
        for i, e in enumerate(self.exports, 1):
            self._index.setdefault(e["name"], i)
        self._sum: dict[int, dict] = {}
        self._all: list[dict] | None = None

    @property
    def count(self) -> int:
        return len(self.exports)

    def index_of(self, name: str) -> int | None:
        return self._index.get(name)

    def summary(self, name: str) -> dict | None:
        i = self.index_of(name)
        return None if i is None else self.get(i)

    def get(self, i: int) -> dict:
        if i not in self._sum:
            self._sum[i] = export_summary(self.pkg, i)
        return self._sum[i]

    def all(self) -> list[dict]:
        if self._all is None:
            self._all = [self.get(i) for i in range(1, self.count + 1)]
        return self._all

    def tag_at(self, name: str, offset: int) -> dict | None:
        s = self.summary(name)
        if not s:
            return None
        for t in s["tags"]:
            if t["offset"] == offset:
                return t
        return None

    def refs_to(self, targets: set[str]) -> list[dict]:
        out = []
        for i, s in enumerate(self.all(), 1):
            for t in s["tags"]:
                ref = t.get("ref") or ""
                if ref and ref.split(".")[-1] in targets:
                    out.append({"export": i, "name": self.exports[i - 1]["name"],
                                "offset": t["offset"], "field": t.get("name") or "",
                                "ref": ref, "ref_class": t.get("ref_class")})
        return out

    def carriers(self, offset: int) -> list[dict]:
        out = []
        for i, s in enumerate(self.all(), 1):
            for t in s["tags"]:
                if t["offset"] == offset:
                    out.append({"export": i, "name": self.exports[i - 1]["name"],
                                "class": s["class"], "type": t["type"],
                                "value": t.get("value") if not t.get("ref") else t.get("ref")})
        return out


def tag_view(t: dict | None) -> dict | None:
    if t is None:
        return None
    return {"offset": t["offset"], "type": t["type"], "name": t.get("name"),
            "value": t.get("value"), "ref": t.get("ref"), "ref_class": t.get("ref_class")}


# ------------------------------------------------------------------ SDK layout

def sdk_layout() -> tuple[dict[str, dict[str, int]], dict[str, str]]:
    """({class: {field: offset}}, {class: superclass}) from the generated BmSDK headers."""
    out: dict[str, dict[str, int]] = {}
    supers: dict[str, str] = {}
    for path in sorted(glob.glob(p("Working/vendor/BmSDK/*.g.cs"))):
        cls = os.path.basename(path)[: -len(".g.cs")]
        try:
            txt = read(os.path.relpath(path, ROOT).replace("\\", "/"))
        except OSError:
            continue
        fields: dict[str, int] = {}
        for m in re.finditer(
            r"/// (?:Class|Object|Float|Bool|Byte|Int|Name|Array|Struct|Component)Property: (\w+)"
            r"[\s\S]{0,400}?Ptr \+ (\d+)", txt):
            fields.setdefault(m.group(1), int(m.group(2)))
        out[cls] = fields
        m = re.search(r"public partial class (\w+) : BmSDK\.BmGame\.(\w+),", txt)
        if m:
            supers[m.group(1)] = m.group(2)
    return out, supers


def class_chain(supers: dict[str, str], cls: str) -> list[str]:
    """The superclass chain of `cls`, most derived first (the sdk headers are the witness)."""
    out: list[str] = []
    cur = cls
    while cur and cur not in out:
        out.append(cur)
        cur = supers.get(cur, "")
    return out


def sdk_probe(sdk: dict[str, dict[str, int]], offset: int, name: str) -> list[str]:
    """Every `Class.name` in the SDK that puts `name` at `offset`.

    An empty list is the oracle failing: the offset would not be the field this doc names.
    """
    hits = []
    for cls, fields in sdk.items():
        if fields.get(name) == offset:
            hits.append(f"{cls}.{name}")
    return sorted(hits)


# --------------------------------------------------------- frozen T-WP4c quotes

def md_sections(text: str) -> dict[str, str]:
    """`## <heading>` -> that heading and its body, verbatim."""
    out: dict[str, str] = {}
    cur, buf = None, []
    for line in text.splitlines():
        if line.startswith("## "):
            if cur is not None:
                out[cur] = "\n".join(buf)
            cur, buf = line[3:].strip(), [line]
        elif cur is not None:
            buf.append(line)
    if cur is not None:
        out[cur] = "\n".join(buf)
    return out


def carry(sections: dict[str, str], prefix: str) -> tuple[str, str]:
    for head, body in sections.items():
        if head.startswith(prefix):
            return head, body.strip("\n")
    raise SystemExit(f"T-WP4c has no section starting {prefix!r} - the frozen source moved")


def quote(text: str, needle: str, lines: int = 1) -> tuple[int, str]:
    """(line number, the `lines` consecutive non-empty lines starting at the match)."""
    raw = text.splitlines()
    for i, line in enumerate(raw):
        if needle in line:
            block = [line.strip()]
            j = i + 1
            while len(block) < lines and j < len(raw) and raw[j].strip():
                block.append(raw[j].strip())
                j += 1
            return i + 1, " ".join(block)
    raise SystemExit(f"T-WP4c no longer contains {needle!r} - the frozen source moved")


def rot_deg(v: int) -> float:
    return v * 360.0 / 65536.0


# -------------------------------------------------------------------- derive

def derive() -> dict:
    root = install_root()
    wp4c = read(WP4C_MD)
    secs = md_sections(wp4c)
    sdk, supers = sdk_layout()

    base = Pkg(os.path.join(root, PACKAGES[0]))
    cdo = Pkg(os.path.join(root, "BmGame.upk"))

    # -- field-name witnesses ---------------------------------------------
    witnesses = {name: {"offset": off, "sdk": sdk_probe(sdk, off, sname)}
                 for name, off, sname in FIELDS}

    # -- the launcher's payload pointers, and who points at what -----------
    refs = base.refs_to({FIRED, SIBLING})
    by_target: dict[str, list[dict]] = {SIBLING: [], FIRED: []}
    for r in refs:
        by_target[r["ref"].split(".")[-1]].append(r)

    launcher_rows = {}
    for key, off in (("ProjectileArchetype", 2428), ("ProjectileForCarsArchetype", 2492)):
        launcher_rows[key] = {"offset": off, "tag": tag_view(base.tag_at(LAUNCHER, off))}

    # -- the tracker ---------------------------------------------------------
    trk = base.summary(TRACKER)
    trk_tags = []
    for t in trk["tags"]:
        trk_tags.append({"offset": t["offset"], "type": t["type"],
                         "doc_name": NAME_OF.get(t["offset"]),
                         "value": t.get("value") if not t.get("ref") else t.get("ref"),
                         "ref_class": t.get("ref_class")})
    trk_tags.sort(key=lambda r: r["offset"])

    # Offset 2464 is class-relative: three unrelated classes also have *a* tag there, holding a
    # different field. Only exports whose chain declares RPursuitModeMissileLauncher put
    # `bInstantFire` at 2464, so the census is filtered to that lineage.
    owner = "RPursuitModeMissileLauncher"

    def in_lineage(cls: str) -> bool:
        return owner in class_chain(supers, cls)

    carriers_2464_all = base.carriers(2464)
    carriers_2464 = [c for c in carriers_2464_all if in_lineage(c["class"])]
    collisions = [c for c in carriers_2464_all if not in_lineage(c["class"])]
    trk_has_2464 = any(r["export"] == (base.index_of(TRACKER) or -1) for r in carriers_2464_all)
    lineage_classes = [c for c in sdk if owner in class_chain(supers, c)]

    # -- the two projectile archetypes --------------------------------------
    def projectile(name: str) -> dict:
        s = base.summary(name)
        rows = []
        for t in s["tags"]:
            rows.append({"offset": t["offset"], "type": t["type"],
                         "doc_name": NAME_OF.get(t["offset"]),
                         "value": t.get("value") if not t.get("ref") else t.get("ref"),
                         "ref_class": t.get("ref_class")})
        rows.sort(key=lambda r: r["offset"])
        return {
            "export": base.index_of(name),
            "class": s["class"],
            "size": s["size"],
            "tag_count": s["tag_count"],
            "tags": rows,
            "scalars": [r for r in rows if r["type"] in ("FloatProperty", "IntProperty", "ByteProperty")],
            "ak_events": [r for r in rows if r["ref_class"] == "AkEvent"],
            "at": {NAME_OF.get(o, str(o)): next((r for r in rows if r["offset"] == o), None)
                   for _n, o, _s in FIELDS},
        }

    fired = projectile(FIRED)
    sibling = projectile(SIBLING)

    # -- variants ------------------------------------------------------------
    variants = []
    for name in PACKAGES[1:]:
        pk = Pkg(os.path.join(root, name))
        variants.append({
            "package": name,
            "exports": pk.count,
            "launcher_export": pk.index_of(LAUNCHER),
            "tracker_export": pk.index_of(TRACKER),
            "fired_export": pk.index_of(FIRED),
            "sibling_export": pk.index_of(SIBLING),
            "launcher_bInstantFire": tag_view(pk.tag_at(LAUNCHER, 2464)),
            "launcher_pointer_cars": tag_view(pk.tag_at(LAUNCHER, 2492)),
            "launcher_pointer_base": tag_view(pk.tag_at(LAUNCHER, 2428)),
            "tracker_tags": (pk.summary(TRACKER) or {}).get("tag_count"),
            "carriers_2464": [c for c in pk.carriers(2464) if in_lineage(c["class"])],
            "collisions_2464": [c for c in pk.carriers(2464) if not in_lineage(c["class"])],
            "refs_sibling": len(pk.refs_to({SIBLING})),
            "refs_fired": len(pk.refs_to({FIRED})),
        })

    # -- class defaults ------------------------------------------------------
    defaults = {}
    for name in ("Default__RPursuitModeMissileLauncher", "Default__RBatmobileVehicleTracker",
                 "Default__RBatmobileMissile"):
        s = cdo.summary(name)
        if s is None:
            defaults[name] = None
            continue
        offs = sorted(t["offset"] for t in s["tags"])
        defaults[name] = {
            "export": cdo.index_of(name), "class": s["class"], "tags": s["tag_count"],
            "offsets": offs,
            "at": {str(o): (o in offs) for o in (712, 728, 732, 960, 968, 2464, 2560, 2564)},
        }

    # -- rotators (the rounding nit the review raised) -----------------------
    rot = {}
    for key, arche, off in (("tracker", TRACKER, 2452), ("launcher", LAUNCHER, 2452)):
        t = base.tag_at(arche, off)
        raw = (t or {}).get("value") or []
        rot[key] = {"raw": raw, "deg": [round(rot_deg(v), 4) for v in raw],
                    "deg_1dp": [round(rot_deg(v), 1) for v in raw]}

    # -- lock durations, read at their own offsets ---------------------------
    lock = {}
    for key, off in (("military", 2560), ("civilian", 2564)):
        t = base.tag_at(LAUNCHER, off)
        lock[key] = {"offset": off, "value": (t or {}).get("value")}

    # ------------------------------------------------------------------ changes
    q_instant = quote(wp4c, "how it fires")
    q_sound = quote(wp4c, "impact sound field", 2)
    q_damage = quote(wp4c, "| projectile damage |")
    q_payload = quote(wp4c, "| anti-car payload |")
    q_pitch = quote(wp4c, "| launch point and pitch |")

    changes = [
        {
            "id": "C1",
            "object": TRACKER,
            "field": "RPursuitModeMissileLauncher.bInstantFire",
            "offset": 2464,
            "was": "true (class default), labelled decoded",
            "now": None,
            "label_now": "UNKNOWN",
            "because": (
                "no decoded record carries it. 2464 is the offset of the inherited field only inside "
                f"the `{owner}` chain (classes: {', '.join('`%s`' % c for c in lineage_classes)}); "
                f"among every export of that lineage in the four packages only the "
                f"{len(carriers_2464)} `{LAUNCHER}` tag(s) serialize it, and no `{TRACKER}` does; the "
                f"class default object has no tag at 2464 either. The {len(collisions)} other tags at "
                "that offset in the base package belong to classes outside the chain and are a "
                "different field at the same number"),
            "was_quote": {"line": q_instant[0], "text": q_instant[1]},
        },
        {
            "id": "C2",
            "object": SIBLING,
            "field": "RBatmobileMissile.ExlposionSound",
            "offset": 968,
            "was": "`Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact` presented as the "
                   "fired missile's impact sound (decoded)",
            "now": (sibling["at"]["RBatmobileMissile.ExlposionSound"] or {}).get("value"),
            "label_now": "decoded on the sibling / UNKNOWN on the fired archetype",
            "because": (
                f"both launcher payload pointers resolve to `{FIRED}` (export {base.index_of(FIRED)}); "
                f"the sibling (export {base.index_of(SIBLING)}) is referenced by "
                f"{len(by_target[SIBLING])} export(s) in `{base.name}`. The fired archetype "
                "serializes no AkEvent at all"),
            "was_quote": {"line": q_sound[0], "text": q_sound[1]},
        },
        {
            "id": "C3",
            "object": SIBLING,
            "field": "Projectile.Damage",
            "offset": 728,
            "was": "60.0, labelled decoded, presented as the EMP missile's damage",
            "now": (sibling["at"]["Projectile.Damage"] or {}).get("value"),
            "label_now": "decoded on the sibling / UNKNOWN on the fired archetype",
            "because": (
                f"`{FIRED}` serializes {fired['tag_count']} tags, {len(fired['scalars'])} of them "
                f"scalar and {len(fired['ak_events'])} of them an AkEvent; the 60.0 sits on the "
                "sibling, which no launcher points at"),
            "was_quote": {"line": q_damage[0], "text": q_damage[1]},
        },
        {
            "id": "C4",
            "object": "T-WP4c §2.3",
            "field": "one table row covering two archetypes",
            "offset": None,
            "was": "one table that credits the fired weapon with the sibling's damage numbers "
                   "while naming the fired archetype's explosion",
            "now": "split into two tables, one per archetype, each read from its own bytes",
            "label_now": "decoded (per archetype)",
            "because": "the two rows of that table resolve to two different exports",
            "was_quote": {"line": q_damage[0], "text": q_damage[1]},
            "was_quote2": {"line": q_payload[0], "text": q_payload[1]},
        },
        {
            "id": "C5",
            "object": TRACKER,
            "field": "RPursuitModeMissileLauncher.LaunchRotationOffset",
            "offset": 2452,
            "was": "`[5461, 0, 0]` printed as `30.0 deg` with the rounding unstated",
            "now": (f"{rot['tracker']['raw']} = {rot['tracker']['deg'][0]} deg, i.e. "
                    f"{rot['tracker']['deg_1dp'][0]} deg to 1 dp"),
            "label_now": "decoded / derived",
            "because": "5461 * 360 / 65536 = 29.9981689..., not exactly 30; the sign convention "
                       "(which way +pitch tilts the socket) is not in any decoded file",
            "was_quote": {"line": q_pitch[0], "text": q_pitch[1]},
        },
    ]

    # ------------------------------------------------------------- carried text
    carried_heads = ("3.", "4.", "6.", "7.", "8.")
    carried = []
    for prefix in carried_heads:
        head, body = carry(secs, prefix)
        carried.append({"heading": head, "chars": len(body), "sha256": sha256(body), "text": body})
    carried_blob = "\n\n".join(c["text"] for c in carried)

    data = {
        "status": "done (corrective)",
        "root": root.replace("\\", "/"),
        "packages": [{"name": base.name, "exports": base.count},
                     *[{"name": v["package"], "exports": v["exports"]} for v in variants]],
        "witnesses": witnesses,
        "launcher": {"export": base.index_of(LAUNCHER), "class": (base.summary(LAUNCHER) or {}).get("class"),
                     "tag_count": (base.summary(LAUNCHER) or {}).get("tag_count"),
                     "pointers": launcher_rows},
        "reference_census": {"by_target": {k: v for k, v in by_target.items()},
                             "counts": {k: len(v) for k, v in by_target.items()}},
        "lineage": {"field_owner": owner, "classes": lineage_classes,
                    "carriers_all_at_2464": len(carriers_2464_all),
                    "collisions": collisions},
        "tracker": {
            "export": base.index_of(TRACKER),
            "class": trk["class"],
            "size": trk["size"],
            "tag_count": trk["tag_count"],
            "tags": trk_tags,
            "has_bInstantFire": trk_has_2464,
            "carriers_2464": carriers_2464,
        },
        "payload": {"fired": fired, "sibling": sibling},
        "variants": variants,
        "defaults": defaults,
        "rotators": rot,
        "lock": lock,
        "changes": changes,
        "wp4c": {"path": WP4C_MD, "sha256": sha256(wp4c), "lines": len(wp4c.splitlines()),
                 "carried": [{k: v for k, v in c.items() if k != "text"} for c in carried],
                 "carried_sha256": sha256(carried_blob)},
        "carried": carried,
    }
    return data


# -------------------------------------------------------------------- render

def fnum(v) -> str:
    if v is None:
        return "absent"
    if isinstance(v, float):
        s = f"{v:g}"
        return s if ("." in s or "e" in s) else s + ".0"
    return str(v)


def render(d: dict) -> str:
    base_pkg = d["packages"][0]["name"]
    emp = d["launcher"]
    trk = d["tracker"]
    fired, sib = d["payload"]["fired"], d["payload"]["sibling"]
    cdo = d["defaults"]
    rot, lock = d["rotators"], d["lock"]
    ch = {c["id"]: c for c in d["changes"]}

    owner_short = d["lineage"]["field_owner"]
    L: list[str] = []
    w = L.append
    w("# T-WP4d - the tracker and the Immobiliser, re-issued: what each projectile actually carries")
    w("")
    w("Generated by `Tools/scripts/t_wp4d.py` from the cooked packages (re-read on every run through")
    w("`Tools/scripts/upk_read.py`), the BmSDK layout, and the frozen `Working/Translation/T_WP4C_TRACKER_EMP.md`")
    w("(quoted only to show what it used to say). It replaces **two wrong labels** and one merged table")
    w("in T-WP4c. `--check` re-derives this file and the JSON from the bytes and refuses to pass if any")
    w("value moved.")
    w("")
    w("## STATUS")
    w("")
    w(f"**{d['status']}.** C1: the tracker's `bInstantFire` is **UNKNOWN** (no decoded record carries")
    w("it). C2/C3: the Immobiliser impact sound and `Projectile.Damage 60.0` are **the sibling")
    w(f"archetype's** values; the archetype the launcher actually fires (`{FIRED}`)")
    w("serializes neither, so both are **UNKNOWN** for the fired missile. C4: the merged §2.3 table is")
    w("split. C5: the rotator degrees are printed with their rounding.")
    w("")
    w("Labels: **decoded** = a value read at the file and offset named; **derived** = the arithmetic or")
    w("inference is printed with it; **UNKNOWN** = searched and not in the files, with the route that")
    w("would settle it. Every offset below is checked against the SDK field name at run time")
    w("(`## 9`), so a wrong offset/name pairing fails the check rather than printing.")
    w("")
    w("## 0. Every value this card changes")
    w("")
    w("| # | object | field @ offset | T-WP4c said | value now (and whose) | label now |")
    w("|---|---|---|---|---|---|")
    for c in d["changes"]:
        off = f"@{c['offset']}" if c["offset"] is not None else "-"
        w(f"| {c['id']} | `{c['object']}` | `{c['field']}` {off} | {c['was']} | {c['now'] if c['now'] is not None else '**UNKNOWN**'} | {c['label_now']} |")
    w("")
    w("### 0.1 Why each change, in one line of evidence")
    w("")
    for c in d["changes"]:
        w(f"- **{c['id']}** - {c['because']}.")
    w("")
    w("### 0.2 The exact T-WP4c text each change replaces")
    w("")
    w("Quoted verbatim from the frozen file, with its line number, so the correction can be audited")
    w("against the thing it corrects (`t_wp4c.py` itself is never edited):")
    w("")
    for c in d["changes"]:
        w(f"- **{c['id']}**, T-WP4c line {c['was_quote']['line']}:")
        w(f"  > {c['was_quote']['text']}")
        if c.get("was_quote2"):
            w(f"- **{c['id']}**, the second row it merged, T-WP4c line {c['was_quote2']['line']}:")
            w(f"  > {c['was_quote2']['text']}")
    w("")
    w("## 1. The launcher's payload pointers - both resolve to `_ForCars`")
    w("")
    w(f"`{LAUNCHER}` (export {emp['export']}, class `{emp['class']}`, {emp['tag_count']} tags) in")
    w(f"`{base_pkg}`:")
    w("")
    w("| field | offset | serialized value | resolves to |")
    w("|---|---:|---|---|")
    for key, row in emp["pointers"].items():
        t = row["tag"] or {}
        w(f"| `{NAME_OF.get(row['offset'], key)}` | {row['offset']} (0x{row['offset']:03X}) | "
          f"{t.get('ref') or 'absent'} | export {d['payload']['fired']['export']} = `{FIRED}` |")
    w("")
    w("The reverse direction, over every export of each package:")
    w("")
    w("| package | exports | references to `_ForCars` | references to `Batmobile_EMPMissile_Projectile` |")
    w("|---|---:|---:|---:|")
    w(f"| `{base_pkg}` | {d['packages'][0]['exports']} | {d['reference_census']['counts'][FIRED]} | "
      f"{d['reference_census']['counts'][SIBLING]} |")
    for v in d["variants"]:
        w(f"| `{v['package']}` | {v['exports']} | {v['refs_fired']} | {v['refs_sibling']} |")
    w("")
    w(f"Every reference found in `{base_pkg}`, in full:")
    w("")
    w("| referring export | name | offset | field | target |")
    w("|---:|---|---:|---|---|")
    for r in d["reference_census"]["by_target"][FIRED] + d["reference_census"]["by_target"][SIBLING]:
        w(f"| {r['export']} | `{r['name']}` | {r['offset']} | {r['field'] or '(offset-only)'} | `{r['ref']}` |")
    w("")
    w(f"So `{SIBLING}` is an **orphan archetype**: decoded, complete, and pointed at by nothing. It is")
    w("still a legitimate object to quote - but only as *its own* values, which is what section 3 does.")
    w("")
    w("## 2. The tracker, corrected")
    w("")
    w(f"`{TRACKER}` (export {trk['export']}, class `{trk['class']}`, export payload {trk['size']} B, "
      f"{trk['tag_count']} serialized tags). Its whole serialized record, with the SDK name at each")
    w("offset:")
    w("")
    w("| offset | type | field (SDK) | value |")
    w("|---:|---|---|---|")
    for t in trk["tags"]:
        w(f"| {t['offset']} | {t['type']} | `{t['doc_name'] or '(offset-only)'}` | {fnum(t['value'])} |")
    w("")
    w("| behaviour | evidence | label |")
    w("|---|---|---|")
    w(f"| when it may fire / instant fire | `bInstantFire` **is not serialized on this archetype**: 0 of "
      f"the {trk['tag_count']} tags sit at 2464, and the value T-WP4c printed belongs to `{LAUNCHER}` "
      f"(the only holder of that field in the {owner_short} chain, section 2.1); the class default "
      f"carries no member at that offset either. The other two tracker overrides (`ReadyToFire`, "
      f"`CheckAutoTarget`) are decoded as overrides but their rule is native | UNKNOWN (value) / "
      f"decoded (that the override exists) |")
    trk_at = {t["offset"]: t for t in trk["tags"]}
    w(f"| launch socket | `LaunchSocketName` @2436 = `{fnum((trk_at.get(2436) or {}).get('value'))}` | decoded |")
    w(f"| launch pitch | `LaunchRotationOffset` @2452 = {rot['tracker']['raw']}; "
      f"{rot['tracker']['raw'][0] if rot['tracker']['raw'] else 0} * 360 / 65536 = "
      f"{rot['tracker']['deg'][0] if rot['tracker']['deg'] else 'UNKNOWN'} deg "
      f"({rot['tracker']['deg_1dp'][0] if rot['tracker']['deg_1dp'] else ''} to 1 dp). Whether +pitch "
      f"tilts the socket up or down is **not** decoded in any file, so this note does not say | "
      f"decoded / derived |")
    w(f"| payload | `ProjectileArchetype` @2428 -> `{fnum((trk_at.get(2428) or {}).get('value'))}` "
      f"(the tracker's own pointer, not the EMP launcher's) | decoded |")
    w(f"| the tag it writes | `TagTarget` (`RVehicle`), `LastLockTarget`, `LockOnTarget` live on the "
      f"launcher class, not on the target; no `Tagged`-named member exists on any `RVehicle*` class | "
      f"decoded (types) / UNKNOWN (target-side flag) |")
    w(f"| lock time | `MissileLockOnDuration` @2560 = {fnum(lock['military']['value'])} s, "
      f"`CivilianMissileLockOnDuration` @2564 = {fnum(lock['civilian']['value'])} s - both read from "
      f"the launcher's own tags | decoded |")
    w("")
    w("### 2.1 The `bInstantFire` census (the oracle behind C1)")
    w("")
    w("A raw `offset == 2464` scan is **not** a valid oracle here: the offset is class-relative, and")
    w(f"{d['lineage']['carriers_all_at_2464']} exports in `{base_pkg}` have *some* tag at 2464. Only the "
      f"classes whose chain declares `{d['lineage']['field_owner']}` put `bInstantFire` there")
    w(f"(the SDK chain gives: {', '.join('`%s`' % c for c in d['lineage']['classes'])}). So the census is")
    w("filtered to that lineage, and the collisions are listed separately.")
    w("")
    w("| package | `bInstantFire` carriers (lineage only) | which export |")
    w("|---|---:|---|")
    w(f"| `{base_pkg}` | {len(trk['carriers_2464'])} | "
      + (", ".join(f"`{c['name']}` (export {c['export']}, {c['class']}) = {c['value']}"
                   for c in trk["carriers_2464"]) or "-") + " |")
    for v in d["variants"]:
        w(f"| `{v['package']}` | {len(v['carriers_2464'])} | "
          + (", ".join(f"`{c['name']}` (export {c['export']}) = {c['value']}"
                       for c in v["carriers_2464"]) or "-") + " |")
    w("")
    w("The tags at 2464 that are **not** this field (different classes, same number):")
    w("")
    w("| package | export | name | class | value there |")
    w("|---|---:|---|---|---|")
    for pkgname, coll in [(base_pkg, d["lineage"]["collisions"])] + [
            (v["package"], v["collisions_2464"]) for v in d["variants"]]:
        for c in coll:
            w(f"| `{pkgname}` | {c['export']} | `{c['name']}` | {c['class']} | {c['value']} |")
    w("")
    w(f"None of the `{TRACKER}` instances is in either table's lineage row set; the raw scan's")
    w("hits are a Cannon's muzzle flash, a Winch sound, a Drone-Hacker loop - all at the same number,")
    w("all a different member.")
    w("")
    w("| class default object (`BmGame.upk`) | export | tags | offsets serialized | 2464? |")
    w("|---|---:|---:|---|---|")
    for name, row in cdo.items():
        if row is None:
            w(f"| `{name}` | not found | - | - | - |")
            continue
        w(f"| `{name}` | {row['export']} | {row['tags']} | {row['offsets']} | "
          f"{'yes' if row['at']['2464'] else '**no**'} |")
    w("")
    w("A value can only be *decoded* if some record carries it. For the tracker's `bInstantFire` no")
    w("record does - not the archetype, not the class default - so it is **UNKNOWN**, and the")
    w("`true` that T-WP4c printed is the EMP launcher's. That is the whole of C1.")
    w("")
    w("## 3. The Immobiliser impact - fired archetype and sibling, side by side")
    w("")
    w(f"Both are class `{fired['class']}`. Everything below is read from each archetype's own tags.")
    w("")
    w("| quantity | field @ offset | fired `_ForCars` (export %d) | sibling `Batmobile_EMPMissile_Projectile` (export %d) |"
      % (fired["export"], sib["export"]))
    w("|---|---|---|---|")
    for label, name, off in (
        ("damage", "Projectile.Damage", 728),
        ("damage radius", "Projectile.DamageRadius", 732),
        ("damage type", "Projectile.MyDamageType", 712),
        ("impact sound", "RBatmobileMissile.ExlposionSound", 968),
        ("explosion", "RBatmobileMissile.ExplosionTemplate", 960),
    ):
        a = fired["at"].get(name) or {}
        b = sib["at"].get(name) or {}
        w(f"| {label} | `{name}` @{off} | {fnum(a.get('value'))} | {fnum(b.get('value'))} |")
    w(f"| tags / scalars / AkEvents | - | {fired['tag_count']} / {len(fired['scalars'])} / "
      f"{len(fired['ak_events'])} | {sib['tag_count']} / {len(sib['scalars'])} / "
      f"{len(sib['ak_events'])} |")
    w("")
    w("**The fired archetype** (`_ForCars`) is reference-only: every one of its tags is an object")
    w("reference, and they are all its own components/particles plus one `RAkAudible` component. It")
    w("carries **no** damage, **no** damage type, **no** damage radius and **no** impact `AkEvent`.")
    w("")
    w("**The sibling** carries the numbers and the sound: `Projectile.Damage` 60.0,")
    w("`Projectile.DamageRadius` 0.0, `Projectile.MyDamageType` `Core.RDmgType_BatmobileCannon`, and")
    w("`RBatmobileMissile.ExlposionSound` -> `Ww_VFX_Tank_Explosion.Play_Batmobile_Immobiliser_Impact`")
    w("(the game's own `ExlposionSound` typo is reproduced). But it is the archetype **no launcher")
    w("points at** (section 1).")
    w("")
    w("**So what does the fired missile do?** Its damage and its impact sound are **UNKNOWN**:")
    w("")
    w("| candidate source | decoded? | result |")
    w("|---|---|---|")
    w(f"| the fired archetype's own tags | {fired['tag_count']} tags, none of them a damage or an event | absent |")
    w("| `Default__RBatmobileMissile` (`BmGame.upk`) | the class default object serializes "
      f"{(cdo.get('Default__RBatmobileMissile') or {}).get('tags', 'UNKNOWN')} tags at offsets "
      f"{(cdo.get('Default__RBatmobileMissile') or {}).get('offsets', [])} - none at 728/732/712/968 | "
      "no class default for damage or impact sound is decoded |")
    w("| `RProjectile`/`RBasicProjectile` defaults | same check | none at 728/968 |")
    w("")
    w("One nuance, so a reader does not mistake it for a sound: `_ForCars` does reference")
    w("`Batmobile_EMPMissile_Projectile_ForCars.DefaultAkAudible_` (`RAkAudible`), a per-actor audible")
    w("**component**, not an `AkEvent` field. Which event that component plays is not in the packages.")
    w("")
    w("## 4. Behaviour rows, corrected")
    w("")
    w("| BmAK behaviour | decoded value | JC3 route (T-WP4c §4) | status |")
    w("|---|---|---|---|")
    w(f"| tracker fires a homing tagging projectile | `Vehicle_Tracker` -> `Batmobile_Tracker_Projectile` "
      f"(T-WP4c §1) | R1 | partial: the projectile translates, the tag does not |")
    w(f"| tracker's acquire rule | `CheckAutoTarget` override; `AutoTargetAngle`/`Range` not serialized | R3 | "
      f"UNKNOWN (two class defaults no file carries) |")
    w(f"| tracker's instant fire | `bInstantFire` not serialized on `{TRACKER}`; the only carrier in the "
      f"four packages is `{LAUNCHER}` = true | - | **UNKNOWN** (was wrongly decoded as true - C1) |")
    w("| one tag on one vehicle | `TagTarget` (`RVehicle`), `LastLockTarget`, `LockOnTarget` singular | R3 | "
      "UNKNOWN: no tag member in JC3; only the HUD marker exists |")
    w(f"| tag -> lock {fnum(lock['military']['value'])} s | `MissileLockOnDuration` @2560 = "
      f"{fnum(lock['military']['value'])} s (civilian {fnum(lock['civilian']['value'])} s @2564) | R3 | "
      f"UNKNOWN (no lock time on either side of the bridge) |")
    w("| losing a tag is warned | `UntagWarningEvent` `Play_HUD_fail`, `LoseLockTime`, `PromoteUntagPromptTime` | "
      "R3 | partial: JC3 can play a fail event; no untag state to hang it on |")
    w(f"| Immobilizer missile = `RBatmobileEMPMissile` | the class, its archetype, and **both** payload "
      f"pointers resolving to `{FIRED}` | - | decoded (the sound leg is now section 3, not a proof) |")
    w(f"| impact sound | only on the orphan sibling; the fired archetype serializes none | - | **decoded "
      f"(sibling) / UNKNOWN (fired)** - C2 |")
    w(f"| missile damage | 60.0 only on the orphan sibling; the fired archetype serializes none | - | "
      f"**decoded (sibling) / UNKNOWN (fired)** - C3 |")
    w("| payload for cars only | `ProjectileForCarsArchetype`, `CantFireOnPenguinVanDialogue` | R1 | "
      "decoded (BmAK) / route open |")
    w("| disable duration and look | no member on either side; only `DisabledByEMP`/`SetDisabledByEMP` "
      "state names | R1, R2 | UNKNOWN - not invented |")
    w("| both modes | `BattleModeFireButtonPressed` beside the pursuit lock | R1 | derived |")
    w("| booster mesh | `Batmobile_Booster.GadgetMesh`; class has only `bBoosting`/`bWarming` | R5 | "
      "partial: the force is live, the mesh is absent |")
    w("")
    w("## 5. UNKNOWNs (with what was tried)")
    w("")
    w("1. **The fired missile's `Projectile.Damage` / `DamageRadius` / `MyDamageType`.** Tried: every")
    w(f"   tag of `{FIRED}` in all four vehicle packages ({fired['tag_count']} tags: all object")
    w("   references), the class default object in `BmGame.upk`, and the `RProjectile`/")
    w("   `RBasicProjectile` defaults. None carries a damage. Route: the engine's projectile default")
    w("   for `RBatmobileMissile`, which is native data, or a runtime sample.")
    w("2. **The fired missile's impact sound.** Same search; the only `Immobiliser` event in the")
    w("   weapon data sits on the orphan sibling, and the fired archetype's only audio member is an")
    w(f"   `RAkAudible` component (`DefaultAkAudible_`, offset 124) whose event is not serialized here.")
    w("3. **The tracker's `bInstantFire`.** Tried: the `Vehicle_Tracker` record in all four packages,")
    w("   every 2464 carrier in those packages, `Default__RPursuitModeMissileLauncher` and")
    w("   `Default__RBatmobileVehicleTracker`. The value is not in the bytes; only the launcher's is.")
    w("4. **Which way +pitch tilts the tracker's socket** (`LaunchRotationOffset` "
      f"{rot['tracker']['raw']}). The unit rule is decoded (65536 per turn); the sign convention is")
    w("   not stated in any file, so the rotation is printed in units and in degrees, without a")
    w("   direction.")
    w("5. **The disable's duration and look.** Unchanged from T-WP4c §2.4: no member on the missile")
    w("   class or the projectile, only the burst gadget's per-level durations.")
    w("")
    w("## 6. Appendix - the part of T-WP4c this card does not change (verbatim)")
    w("")
    w("Sections §3 (booster mesh), §4 (the JC3 house), §6 (compromises), §7 (reopened closures) and")
    w("§8 (checks) carry no value this card corrects. They are reproduced **verbatim** from the frozen")
    w("`Working/Translation/T_WP4C_TRACKER_EMP.md` so this file can be read on its own; the SHA-256 of")
    w("each carried block is printed so the copy can be proven byte-identical (and `--check` fails if")
    w("the frozen file is rewritten under it). Their section numbers are T-WP4c's, not this file's.")
    w("")
    w(f"- carried blocks: {len(d['carried'])}, sha256 of the concatenation "
      f"`{d['wp4c']['carried_sha256']}`")
    w(f"- frozen T-WP4c: {d['wp4c']['lines']} lines, sha256 `{d['wp4c']['sha256']}`")
    w("")
    w("One reading note: the carried §8 describes **T-WP4c's** checks (`t_wp4c.py --check`). This")
    w("file's own check is §9 above; the carried text is kept unchanged so it stays provably identical.")
    w("")
    for c in d["carried"]:
        w(f"<!-- carried: {c['heading']} | {c['chars']} chars | sha256 {c['sha256']} -->")
        w("")
        w(c["text"])
        w("")
    w("## 9. Reproduce and the offset oracle")
    w("")
    w("```")
    w("cd E:/Modding/JustCause3/JC3-Batmobile")
    w("uv run python Tools/scripts/t_wp4d.py --write    # writes this file and the JSON")
    w("uv run python Tools/scripts/t_wp4d.py --check    # recomputes from the bytes, byte-compares")
    w("```")
    w("")
    w("Every offset this document names is cross-checked at run time against")
    w("`Working/vendor/BmSDK/*.g.cs`: the tool records which `Class.field` puts the expected field at")
    w("that offset, so an offset/name mismatch would print `(none)` here rather than pass silently.")
    w("")
    w("| doc name | offset | SDK witness |")
    w("|---|---:|---|")
    for name, row in d["witnesses"].items():
        w(f"| `{name}` | {row['offset']} | {', '.join('`%s`' % h for h in row['sdk']) or '(none)'} |")
    w("")
    w(f"Packages opened: {', '.join('`%s` (%d exports)' % (q['name'], q['exports']) for q in d['packages'])}, `BmGame.upk`.")
    w("Read-only; no game process was launched or attached (INSTRUCTIONS.md §3 test ban honoured).")
    w("")
    return "\n".join(L)


# ----------------------------------------------------------------------- main

def build() -> tuple[str, str]:
    d = derive()
    md = render(d)
    js = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + "\n"
    return md, js


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    md, js = build()
    if args.write:
        for rel, text in ((OUT_MD, md), (OUT_JSON, js)):
            os.makedirs(os.path.dirname(p(rel)), exist_ok=True)
            with open(p(rel), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(text)
            print(f"wrote {rel} ({len(text)} chars)")
        return 0
    if args.check:
        ok = True
        for rel, want in ((OUT_MD, md), (OUT_JSON, js)):
            try:
                got = read(rel)
            except FileNotFoundError:
                print(f"MISSING {rel}")
                ok = False
                continue
            if got != want:
                print(f"DRIFT {rel}: on disk {len(got)} chars, derived {len(want)}")
                ok = False
            else:
                print(f"OK {rel} ({len(got)} chars)")
        print("CHECK", "PASS" if ok else "FAIL")
        return 0 if ok else 1
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

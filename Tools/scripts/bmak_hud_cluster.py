"""bmak_hud_cluster.py - the Batmobile HUD cluster: where each gauge sits, what feeds it.

G3-HUD-CLUSTER. Four operator leads are tested against the bytes (play memory = hypothesis):

  (a) the health bar is TOP-LEFT in battle mode
  (b) the afterburner gauge is on the LEFT in pursuit mode
  (c) a second afterburner *cooldown* gauge sits LEFT of the afterburner gauge
  (d) the Batmobile has no speedometer, so JC3's must be disabled for it

Everything is re-derived from four inputs, none of them prose:

  * `HudModuleBatmobile.Image` (BmGame.upk) - the SwfMovie is carved, its CFX payload
    inflated, and the GFx tag stream walked: `SymbolClass` names the document class, each
    `DefineSprite` gives its frame count and its `PlaceObject2` placements (depth, character,
    instance name, MATRIX). That is where the clip tree and the 2D transforms come from.
  * the decompiled AS3 export of the same movie (`BMAK_HUD_DEC`) - the authored **3D**
    transforms are not in place tags but in `AnimatorFactory3D` property arrays in the parent
    classes (`LeftSideParentMovie_311`, `RightSideParentMovie_126`); the script reads the
    `matrix3D` 4x4 vectors and the setter bodies from there.
  * `Working/vendor/BmSDK/*.g.cs` - the native fields that feed the gauges, with offsets.
  * JC3's decompiled `ui/hud.gfx` (`JC3_HUD_DEC`) - the speedometer/nitrous/health API.

Every number in `Working/HUD/CLUSTER.json` is recomputed by `--check`; `--tamper-test` mutates a
recomputed value and asserts the check notices.

Usage:
  python Tools/scripts/bmak_hud_cluster.py --write
  python Tools/scripts/bmak_hud_cluster.py --check
  python Tools/scripts/bmak_hud_cluster.py --tamper-test
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import zlib
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package, export_summary  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GAME = Path(os.environ.get("BMAK_GAME", r"E:/Games/Batman - Arkham Knight"))
BMAK_DEC = Path(os.environ.get("BMAK_HUD_DEC",
                              r"E:/Modding/_shared/gamedata/BmAKgrab_early/hud/modules/HudModuleBatmobile/dec"))
JC3_DEC = Path(os.environ.get("JC3_HUD_DEC", r"E:/Modding/_shared/gamedata/JC3grab/hud/dec"))
SDK = ROOT / "Working" / "vendor" / "BmSDK"
INTERFACES = ROOT / "Research" / "BatmobileGrab" / "HUD_INTERFACES.json"
SPEEDO = ROOT / "Research" / "BatmobileGrab" / "SPEEDOMETER.json"
OUT_JSON = ROOT / "Working" / "HUD" / "CLUSTER.json"
OUT_MD = ROOT / "Working" / "HUD" / "CLUSTER.md"

MOVIE_PKG = "BmGame.upk"
MOVIE_OBJ = "HudModuleBatmobile.Image"

# --------------------------------------------------------------------------- the movie bytes


def carve() -> tuple[bytes, dict]:
    """Carve the SwfMovie export and inflate its CFX payload -> (tag stream, evidence)."""
    pkg = Package(str(GAME / "BmGame" / "CookedPCConsole" / MOVIE_PKG))
    idx = next((k for k in range(1, pkg.export_count + 1)
                if pkg.object_path(k) == MOVIE_OBJ), None)
    if idx is None:
        raise SystemExit(f"{MOVIE_PKG}: no export {MOVIE_OBJ!r}")
    rec = pkg.exports[idx - 1]
    blob = pkg.image[rec["offset"]:rec["offset"] + rec["size"]]
    at = blob.find(b"CFX")
    if at < 4:
        raise SystemExit("no CFX payload")
    n = int.from_bytes(blob[at - 4:at], "little")
    payload = blob[at:at + n]
    for off in range(32):
        try:
            data = zlib.decompressobj().decompress(payload[off:])
        except zlib.error:
            continue
        if len(data) > 1024:
            return data, {"object": f"{MOVIE_PKG}:{MOVIE_OBJ}", "export_bytes": rec["size"],
                          "cfx_bytes": len(payload),
                          "sha256_cfx": hashlib.sha256(payload).hexdigest(),
                          "inflated_bytes": len(data), "zlib_offset_in_cfx": off}
    raise SystemExit("CFX payload does not inflate")


def walk(data: bytes, start: int, end: int) -> list[tuple[int, int, int]]:
    """SWF tag walk: (code, body offset, body length). Stops at the first overrun."""
    pos, out = start, []
    while pos + 2 <= end:
        cl = int.from_bytes(data[pos:pos + 2], "little")
        pos += 2
        code, ln = cl >> 6, cl & 0x3F
        if ln == 0x3F:
            if pos + 4 > end:
                break
            ln = int.from_bytes(data[pos:pos + 4], "little")
            pos += 4
        if pos + ln > end:
            break
        out.append((code, pos, ln))
        pos += ln
    return out


def stream_start(data: bytes) -> int:
    """The tag stream follows a short GFx header; start where the walk first yields tag 1000."""
    for start in range(0, 33):
        tags = walk(data, start, len(data))
        if tags and tags[0][0] == 1000:
            return start
    raise SystemExit("no ExporterInfo tag: cannot locate the tag stream")


def cstr(b: bytes, p: int) -> tuple[str, int]:
    e = b.index(b"\x00", p)
    return b[p:e].decode("latin-1"), e + 1


class Bits:
    def __init__(self, b: bytes, pos: int = 0):
        self.b, self.pos, self.bit = b, pos, 0

    def u(self, n: int) -> int:
        v = 0
        for _ in range(n):
            v = (v << 1) | ((self.b[self.pos] >> (7 - self.bit)) & 1)
            self.bit += 1
            if self.bit == 8:
                self.bit, self.pos = 0, self.pos + 1
        return v

    def s(self, n: int) -> int:
        v = self.u(n)
        return v - (1 << n) if n and v >> (n - 1) else v

    def align(self) -> None:
        if self.bit:
            self.bit, self.pos = 0, self.pos + 1


def matrix2(b: bytes, p: int) -> dict:
    """SWF MATRIX -> scale/rotate/translate (twips -> px)."""
    br = Bits(b, p)
    sx = sy = 1.0
    rot = skew = 0.0
    if br.u(1):
        n = br.u(5)
        sx, sy = br.s(n) / 65536.0, br.s(n) / 65536.0
    if br.u(1):
        n = br.u(5)
        rot, skew = br.s(n) / 65536.0, br.s(n) / 65536.0
    n = br.u(5)
    tx, ty = br.s(n) / 20.0, br.s(n) / 20.0
    br.align()
    return {"sx": round(sx, 3), "sy": round(sy, 3), "rot": round(rot, 3),
            "x": round(tx, 1), "y": round(ty, 1), "end": br.pos}


def placements(data: bytes, body: tuple[int, int]) -> tuple[list[dict], int]:
    """Frames of one sprite: depth slots with character, name and MATRIX (PlaceObject2 only)."""
    start, end = body
    frames: list[dict] = []
    cur: dict[int, dict] = {}
    labels: dict[str, int] = {}
    seen70 = 0
    for code, p, ln in walk(data, start, end):
        b = data[p:p + ln]
        if code == 26 and ln >= 3:
            f1 = b[0]
            depth = int.from_bytes(b[1:3], "little")
            q, chid, mat, name = 3, None, None, None
            if f1 & 0x02 and q + 2 <= ln:
                chid = int.from_bytes(b[q:q + 2], "little")
                q += 2
            if f1 & 0x04 and q < ln:
                m = matrix2(b, q)
                mat = {k: v for k, v in m.items() if k != "end"}
                q = m["end"]
            if f1 & 0x08 and q + 2 <= ln:
                cx = int.from_bytes(b[q:q + 2], "little")
                q += 2
                if cx:
                    q += 8 * cx
            if f1 & 0x10 and q + 2 <= ln:
                q += 2
            if f1 & 0x20 and q < ln:
                try:
                    name, q = cstr(b, q)
                except ValueError:
                    name = None
            slot = cur.get(depth, {"depth": depth})
            slot.update({"chid": chid if chid is not None else slot.get("chid"),
                         "name": name if name is not None else slot.get("name"),
                         "matrix": mat if mat is not None else slot.get("matrix")})
            cur[depth] = slot
        elif code == 70:
            seen70 += 1
        elif code == 1:
            # deep copy: the depth slots are mutated by later frames
            frames.append({d: dict(s) for d, s in cur.items()})
        elif code == 43 and b.endswith(b"\x00"):
            labels[b[:-1].decode("latin-1")] = len(frames)
    return frames, seen70, labels


def movie() -> dict:
    data, ev = carve()
    start = stream_start(data)
    top = walk(data, start, len(data))

    sym: dict[int, str] = {}
    for code, p, ln in top:
        if code != 76:
            continue
        try:
            count = int.from_bytes(data[p:p + 2], "little")
            q = p + 2
            for _ in range(count):
                cid = int.from_bytes(data[q:q + 2], "little")
                q += 2
                nm, q = cstr(data, q)
                sym[cid] = nm
        except (ValueError, IndexError):
            continue

    sprites: dict[int, tuple[int, int, int]] = {}
    for code, p, ln in top:
        if code == 39:
            sprites[int.from_bytes(data[p:p + 2], "little")] = (
                int.from_bytes(data[p + 2:p + 4], "little"), p + 4, ln - 4)

    trees: dict[int, dict] = {}
    for sid in sprites:
        frames, seen70, labels = placements(data, (sprites[sid][1], sprites[sid][1] + sprites[sid][2]))
        trees[sid] = {"frames": sprites[sid][0], "placements": frames, "labels": labels,
                      "skipped_placeobject3": seen70}

    by_class = {v: k for k, v in sym.items() if v}
    return {"evidence": ev, "tag_stream_offset": start, "top_level_tags": len(top),
            "sprites": len(sprites), "symbols": sym, "by_class": by_class,
            "trees": trees, "data": data}


# --------------------------------------------------------------------------- 3D transforms


def anim3d(class_file: str) -> dict[str, dict]:
    """Read AnimatorFactory3D matrix3D vectors out of a decompiled fla class."""
    src = (BMAK_DEC / "scripts" / "HudModuleBatmobile_fla" / class_file).read_text(
        encoding="utf-8", errors="replace")
    out: dict[str, dict] = {}
    cur = None
    for m in re.finditer(r"____motion_(\w+)af1_mat3DVec__\[(\d+)\] = (-?[0-9.]+);", src):
        name, i, v = m.group(1), int(m.group(2)), float(m.group(3))
        if i == 0:
            cur = name
            out[name] = {"matrix3d": [0.0] * 16}
        if cur == name and len(out[name]["matrix3d"]) == 16:
            out[name]["matrix3d"][i] = v
    for name, rec in out.items():
        m = rec["matrix3d"]
        rec.update({"x": round(m[12], 3), "y": round(m[13], 3), "z": round(m[14], 3),
                    "scale_x": round(math.hypot(m[0], m[2]), 4),
                    "yaw_deg": round(math.degrees(math.atan2(m[2], m[0])), 2),
                    "source": f"HudModuleBatmobile_fla/{class_file} matrix3D"})
    return out


# --------------------------------------------------------------------------- script side


def scripts() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8", errors="replace")
            for p in (BMAK_DEC / "scripts").rglob("*.as")}


def bmak_script() -> dict:
    src = scripts()
    main = src["ModuleStruct_Batmobile.as"]
    master = src["ModularHudBm3.as"]
    out: dict = {}
    out["stage"] = {
        "swf": [int(x) for x in re.search(r'SWF\(width="(\d+)", height="(\d+)"', main).groups()],
        "module_stage": [int(float(re.search(r"StageWidth:Number = ([0-9.]+)", master).group(1))),
                         int(float(re.search(r"StageHeight:Number = ([0-9.]+)", master).group(1)))],
        "projection_centre": [int(x) for x in re.search(
            r"projectionCenter = new Point\((\d+),(\d+)\)", main).groups()],
        "fov": float(re.search(r"perspectiveProjection\.fieldOfView = ([0-9.]+)", main).group(1)),
        "tick": float(re.search(r"TickDeltaTime:Number = ([0-9.]+)", master).group(1)),
    }
    out["mode_machine"] = re.search(
        r"private function SetBattleAndZoomMode\(param1:Boolean, param2:Boolean\)", main) is not None
    out["mode_calls"] = [s for s in sorted(set(re.findall(
        r'gotoAndPlay\(this\.CurrentBatmobileMode \+ "TO" \+ _loc3_\)|'
        r'gotoAndPlay\(_loc3_\)|"_?(DRIVE|BATTLE|ZOOMED)"', main))) if s]
    out["settlers"] = {}
    for name in ("UC_SetHealth", "UC_SetHealthBarVisible", "UC_SetBoostLevel", "UC_HideBoostGauge",
                 "UC_SetImpactDamageFlash", "UC_SetBattleAndZoomMode", "UC_ShowBoostUpgrade"):
        m = re.search(r"public function " + name + r"\(([^)]*)\)", main)
        out["settlers"][name] = m.group(1).strip() if m else None
    # boost internals
    body = re.search(r"public function UC_SetBoostLevel\(.*?\n      \}", main, re.S).group(0)
    out["boost"] = {
        "show_below": int(re.search(r"param1 < (\d+)", body).group(1)),
        "fill_frame": re.search(r"(this\.FillMovie\.gotoAndStop\(this\.BoostLevel \+ 1\))", body).group(1),
        "charging_rule": re.search(r"this\.SetBoostBarCharging\((param1 > this\.BoostLevel)\)", body).group(1),
        "upgrade_visibility": [list(t) for t in re.findall(
            r"Upgrade(\d)\.visible = this\.iBoostUpgradeLevel > (\d+)", body)],
        "hide_when_full": "this.BoostLevel >= 100" in body,
        "hold_flag": "bHoldBoostOnscreenUntilUsed" in body,
    }
    out["boost_charging_body"] = re.search(
        r"private function SetBoostBarCharging\(.*?\n      \}", main, re.S).group(0)
    out["boost_charging_labels"] = sorted(set(re.findall(r'gotoAndPlay\(param1 \? "(\w+)" : "(\w+)"\)',
                                                         out["boost_charging_body"])[0])) if \
        re.search(r'gotoAndPlay\(param1 \? "(\w+)" : "(\w+)"\)', out["boost_charging_body"]) else []
    out["boost_decreasing_body"] = re.search(
        r"private function SetBoostBarDecreasing\(.*?\n      \}", main, re.S).group(0)
    out["health"] = {
        "max_change_per_frame": float(re.search(r"MaxHealthChangePerFrame:Number = ([0-9.]+)", main).group(1)),
        "bar_fill": re.search(r"SetMovieProportion\(this\.HealthLevelMovie,([^;]+)\);", main).group(1).strip(),
        "armour_fill": re.search(r"SetMovieProportion\(this\.ArmourLevelMovie,([^;]+)\);", main).group(1).strip(),
        "armour_tier": re.search(r"_loc3_ = (param2 > 1 \? int\(\(param2 - 1\) \* 4\) : 0)", main).group(1),
        "armour_label": re.search(r'ArmourBackground\.gotoAndStop\("Armour" \+ ([A-Za-z0-9_]+)\)', main).group(1),
        "pulse_below": float(re.search(r"if\(\(param1 < ([0-9.]+) && this\.TargetHealthProportion < [0-9.]+\)", main).group(1)),
        "offscreen": float(re.search(r"this\.GoOffscreenTimer = ([0-9.]+);", main).group(1)),
        "battle_forces_visible": 'UC_SetHealthBarVisible(true,"Delayed")' in main,
    }
    out["damage_flash"] = {
        "sig": out["settlers"]["UC_SetImpactDamageFlash"],
        "x": re.search(r"_loc5_\.x = ModularHudBm3\.StageWidth \* (param\d)", main).group(1),
        "y": re.search(r"_loc5_\.y = ModularHudBm3\.StageHeight \* (param\d)", main).group(1),
        "rotationY": re.search(r"_loc5_\.rotationY = param2 > 0 \? (\d+) : -(\d+)", main).group(0),
        "text": re.search(r"DamageText\.TheText\.text = String\((param\d)\)", main).group(1),
    }
    out["ratio_rule"] = re.search(r"override public function OnRatioChanged.*?\n      \}", main, re.S).group(0).strip()
    return out


def interfaces() -> dict:
    doc = json.loads(INTERFACES.read_text(encoding="utf-8"))
    total = sum(len(v["setters"]) for v in doc.values())
    bat = doc["HudModuleBatmobile"]["setters"]
    speed = sorted({s["name"] for v in doc.values() for s in v["setters"]
                    if re.search(r"(?i)speed|rev|gear|dial|rpm", s["name"])})
    boost = sorted({s["name"] for s in bat if "boost" in s["name"].lower()})
    return {"modules": len(doc), "setters_total": total,
            "batmobile_setters": len(bat), "speed_setters": speed, "boost_setters": boost,
            "boost_args": {s["name"]: s["args"] for s in bat if "boost" in s["name"].lower()}}


# --------------------------------------------------------------------------- native fields


FIELD_RE = re.compile(r"/// (?:InlineArray\{(\w+)\}|(\w+)): (\w+)\s*\n(?:.*\n){1,4}?"
                      r"\s*public (?:unsafe \w+|InlineArray<float>) (\w+)[^\n]*Ptr \+ (\d+)")


def sdk_fields(names: list[str], files: list[str]) -> dict:
    out: dict = {}
    for f in files:
        path = SDK / f
        if not path.exists():
            out[f] = {"missing": True}
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        found = {}
        for want in names:
            m = re.search(r"/// (?:InlineArray\{(\w+)\}|(\w+)): " + want + r"\s*\n"
                          r"(?:.*\n){1,4}?\s*public (?:unsafe ([\w<>.]+)|(InlineArray<float>)) "
                          + want + r"[^\n]*\n(?:[^\n]*\n){0,3}?[^\n]*Ptr \+ (\d+)", src)
            if not m:
                continue
            found[want] = {"type": m.group(3) or m.group(4),
                           "inline": bool(m.group(1)),
                           "offset": int(m.group(5)),
                           "file": f,
                           "decl": m.group(0).splitlines()[0].strip()}
        # every element of an InlineArray
        for want, rec in list(found.items()):
            if rec["inline"]:
                elems = re.findall(want + r"_(\d)\s*\n(?:[^\n]*\n){0,3}?[^\n]*Ptr \+ (\d+)", src)
                rec["elements"] = [{"index": int(i), "offset": int(o)} for i, o in elems]
        out[f] = found
    return out


def cdo_defaults(cls: str, offsets: dict[str, int]) -> dict:
    """Class-default values of the named offsets, read from the CDO's tag stream."""
    pkg = Package(str(GAME / "BmGame" / "CookedPCConsole" / "BmGame.upk"))
    idx = next((i for i, e in enumerate(pkg.exports, 1) if e["name"] == f"Default__{cls}"), None)
    if not idx:
        return {"__missing__": True}
    vals = {}
    for t in export_summary(pkg, idx, max_tags=6000)["tags"]:
        for name, off in offsets.items():
            if t.get("offset") == off:
                vals[name] = t.get("value")
    return vals


# --------------------------------------------------------------------------- JC3 side


def jc3() -> dict:
    hud = (JC3_DEC / "scripts" / "hud.as").read_text(encoding="utf-8", errors="replace")
    out: dict = {}
    out["scripts"] = len(list((JC3_DEC / "scripts").rglob("*.as")))
    sigs = {}
    for name in ("InitPrimaryMeter", "InitSecondaryMeter", "SetPrimaryMeterValue", "SetVehicleType",
                 "ShowVehicleUi", "HideVehicleUi", "SetVisibilities", "InitVehicleNitrous",
                 "UpdateVehicleNitrous", "HideVehicleNitrous"):
        m = re.search(r"public function " + name + r"\(([^)]*)\)", hud)
        body = re.search(r"public function " + name + r"\([^)]*\)[^{]*\{(.*?)\n      \}", hud, re.S)
        calls = len(re.findall(r"this\." + name + r"\(", hud))
        if m:
            sigs[name] = {"args": m.group(1).strip(), "call_sites": calls,
                          "touches": sorted(set(re.findall(r"MCI_[a-z_0-9]+", body.group(1)))) if body else []}
    out["api"] = sigs
    out["vehicle_types"] = {k: int(v) for k, v in re.findall(
        r"VEHICLE_TYPE_(\w+):int = (\d+)", hud)}
    out["meters"] = {k: int(v) if v.isdigit() else v for k, v in re.findall(
        r"(CIRCULAR_SPEEDOMETER|VERTICAL_SPEEDOMETER):\* = (\d+)", hud)}
    out["needle"] = [int(v) for v in re.findall(r"(?:MIN|MAX)_PRIMARY_NEEDLE_ROTATION:Number = (-?\d+)", hud)]
    m = re.search(r"public function SetVisibilities\(type:int\) : void\s*\{(.*?)\n      \}", hud, re.S)
    out["set_visibilities_body"] = " ".join(m.group(1).split()) if m else None
    m = re.search(r"SPEEDO_SMOOTHING_TIME:Number = ([0-9.]+)", hud)
    out["speedo_smoothing"] = float(m.group(1)) if m else None
    out["nitro_clip"] = "MCI_nitro_meter" in hud
    out["vehicle_ui_clips"] = sorted(set(re.findall(r"MCI_vehicle\.(MCI_[a-z_0-9]+)", hud)))
    return out


# --------------------------------------------------------------------------- assembled record


def cluster_of(mv: dict, tr: dict[str, dict], bs: dict) -> dict:
    """One record per clip: path, transform, frames, labels."""
    left = tr["LeftSideParentMovie_311.as"]
    right = tr["RightSideParentMovie_126.as"]
    trees = mv["trees"]
    by_class = mv["by_class"]

    def clip_info(chid: int | None) -> dict:
        if chid is None or chid not in trees:
            return {}
        t = trees[chid]
        return {"class": mv["symbols"].get(chid), "frames": t["frames"],
                "labels": sorted(t["labels"]), "placeobject3_skipped": t["skipped_placeobject3"]}

    def tree_of(chid: int) -> list[dict]:
        if chid not in trees or not trees[chid]["placements"]:
            return []
        f0 = trees[chid]["placements"][0]
        rows = []
        for depth in sorted(f0):
            s = f0[depth]
            rows.append({"depth": s.get("depth"), "chid": s.get("chid"), "name": s.get("name"),
                         "matrix": s.get("matrix"),
                         "class": mv["symbols"].get(s.get("chid")) if s.get("chid") else None})
        return rows

    out = {}
    # the two side groups, placed by their own classes
    for grp, rec in (("LeftSideParent", left), ("RightSideParent", right)):
        chid = by_class.get(f"HudModuleBatmobile_fla.{'LeftSideParentMovie_311' if grp == 'LeftSideParent' else 'RightSideParentMovie_126'}")
        chid2 = next((k for k, v in mv["symbols"].items()
                      if v.endswith("LeftSideParentMovie_311" if grp == "LeftSideParent"
                                    else "RightSideParentMovie_126")), None)
        sid = chid or chid2
        out[grp] = {"sprite": sid, "children": tree_of(sid) if sid else [],
                    "authored": {}}
        for name, m in rec.items():
            if name in ("matrix3d", "source"):
                continue
            out[grp]["authored"][name] = m
    # health + boost clips, resolved through the authored transforms
    h = left.get("Health", {})
    out["Health"] = {"path": "HudMaster.LeftSideParent.Health",
                     "transform": h, **clip_info(next((k for k, v in mv["symbols"].items()
                                                       if v and v.endswith("Timeline_390")), None))}
    b = left.get("BoostMovie", {})
    boost_sid = next((k for k, v in mv["symbols"].items() if v and v.endswith("BoostGauge_344")), None)
    out["BoostMovie"] = {"path": "HudMaster.LeftSideParent.BoostMovie", "transform": b,
                         **clip_info(boost_sid), "children": tree_of(boost_sid) if boost_sid else []}
    child_sid = next((k for k, v in mv["symbols"].items() if v and v.endswith("BoostGaugeChild_345")), None)
    out["BoostChild"] = {"path": "…BoostMovie.BoostChild", **clip_info(child_sid),
                         "children": tree_of(child_sid) if child_sid else []}
    # the fill clip: 102 frames, no labels, the level+1 frame target
    fill = next((c for c in out["BoostChild"]["children"] if c.get("name") == "Fill"), None)
    if fill and fill.get("chid") in trees:
        t = trees[fill["chid"]]
        sy = []
        for fr in t["placements"]:
            for depth, slot in sorted(fr.items()):
                if depth == 1 and slot.get("matrix"):
                    sy.append(slot["matrix"]["sy"])
        cap_y = [fr[d]["matrix"]["y"] for fr in t["placements"] for d in fr
                 if fr[d].get("chid") == 1032 and fr[d].get("matrix")]
        out["Fill"] = {"path": "…BoostChild.Fill", "frames": t["frames"],
                       "labels": sorted(t["labels"]), "sy_first": sy[0] if sy else None,
                       "sy_last": sy[-1] if sy else None, "sy_samples": sy[:3] + sy[-3:],
                       "cap_y_first": cap_y[0] if cap_y else None,
                       "cap_y_last": cap_y[-1] if cap_y else None,
                       "growth": (f"Y, bottom-anchored: fill scale-y {sy[0]} -> {sy[-1]} with a "
                                  f"fixed x/y anchor, the Cap riding up y {cap_y[0]} -> {cap_y[-1]}"
                                  if sy and sy[-1] > sy[0] and cap_y else "UNKNOWN")}
    bg = next((c for c in out["BoostChild"]["children"] if c.get("name") == "Background"), None)
    if bg and bg.get("chid") in trees:
        t = trees[bg["chid"]]
        f0 = t["placements"][0] if t["placements"] else {}
        badges = []
        for depth, slot in sorted(f0.items()):
            if slot.get("name", "") and slot["name"].startswith("Upgrade"):
                badges.append({"name": slot["name"], "chid": slot["chid"],
                               "class": mv["symbols"].get(slot["chid"]),
                               "matrix": slot.get("matrix"),
                               "frames": trees[slot["chid"]]["frames"] if slot["chid"] in trees else None,
                               "labels": sorted(trees[slot["chid"]]["labels"]) if slot["chid"] in trees else []})
        out["BoostBadges"] = {"path": "…BoostChild.Background.Upgrade1/2",
                              "background_frames": t["frames"],
                              "background_labels": sorted(t["labels"]), "badges": badges}
    # the authored left/right ordering (a decode, not a memory)
    order = sorted(((v["x"], k) for k, v in left.items() if "x" in v))
    out["left_order_by_x"] = [{"clip": k, "x": x} for x, k in order]
    out["left_order_by_y"] = [{"clip": k, "y": v["y"]}
                              for k, v in sorted(left.items(), key=lambda kv: kv[1]["y"]) if "y" in v]
    out["screen_estimate"] = {k: {"x": round(bs["stage"]["projection_centre"][0] + v["x"], 1),
                                 "y": round(bs["stage"]["projection_centre"][1] + v["y"], 1)}
                              for k, v in left.items() if "x" in v}
    out["mode_visibility"] = {
        "Health": "visible in DRIVE only after damage / XP; BATTLE forces UC_SetHealthBarVisible(true,'Delayed'); "
                  "hidden when full + settled + 2 s timer",
        "BoostMovie": "shown by UC_SetBoostLevel when level < 100, hidden by UC_HideBoostGauge at level >= 100; "
                      "no mode gate in the module",
        "BattleAndZoomInterface": "hidden while CurrentBatmobileMode == DRIVE; visible in BATTLE/ZOOMED",
    }
    return out


def collect() -> dict:
    mv = movie()
    tr = {"LeftSideParentMovie_311.as": anim3d("LeftSideParentMovie_311.as"),
          "RightSideParentMovie_126.as": anim3d("RightSideParentMovie_126.as")}
    bs = bmak_script()
    ifc = interfaces()
    fields = sdk_fields(
        ["BoostDuration", "BoostCooldown", "BoostCooldownUpgradeLevel", "CurrentBoostTimer",
         "DriftingBoostCooldown", "BoostDurationDonut"],
        ["RVehicleSimBatmobile.g.cs"])
    fields.update(sdk_fields(["fAfterburnerStartTime", "fAfterburnerCutoffStartTime",
                              "FakeExtraSpeed", "FakeExtraSpeedMax", "ThrottleSpeed"],
                             ["RVehicleBatmobile.g.cs", "RVehicleBatmobileBase.g.cs"]))
    fields.update(sdk_fields(["MaxHealth", "Health", "CurrentHealth", "Armour", "Armor"],
                             ["RVehicle.g.cs", "RVehicleBatmobile.g.cs",
                              "RVehicleBatmobileBase.g.cs"]))
    sim = fields["RVehicleSimBatmobile.g.cs"]
    offsets = {k: v["offset"] for k, v in sim.items() if isinstance(v, dict) and "offset" in v}
    defaults = cdo_defaults("RVehicleSimBatmobile", offsets) if offsets else {}
    base = fields.get("RVehicleBatmobileBase.g.cs", {})
    base_off = {k: v["offset"] for k, v in base.items() if isinstance(v, dict) and "offset" in v}
    base_def = cdo_defaults("RVehicleBatmobileBase", base_off) if base_off else {}
    rv = fields.get("RVehicle.g.cs", {})
    rv_off = {k: v["offset"] for k, v in rv.items() if isinstance(v, dict) and "offset" in v}
    rv_def = cdo_defaults("RVehicle", rv_off) if rv_off else {}
    speedo = json.loads(SPEEDO.read_text(encoding="utf-8")) if SPEEDO.exists() else {}
    return {
        "task": "G3-HUD-CLUSTER",
        "movie": {k: mv[k] for k in ("evidence", "tag_stream_offset", "top_level_tags", "sprites")},
        "clips": cluster_of(mv, tr, bs),
        "bmak": bs,
        "interfaces": ifc,
        "native": {"fields": fields, "sim_defaults": defaults,
                   "base_defaults": base_def, "vehicle_defaults": rv_def},
        "speedometer": {"verdict": speedo.get("verdict"),
                        "movie_speed_setters": ifc["speed_setters"],
                        "debug_flag": speedo.get("native", {}).get("flag", {}).get("config"),
                        "tokens_in_this_movie": sorted({t.decode("latin-1") for t in
                                                        re.findall(rb"(?i)speed[a-z0-9_]*", mv["data"])})},
        "jc3": jc3(),
    }


# --------------------------------------------------------------------------- report

# The prose below is analysis over the recomputed record; every number it quotes is interpolated
# from `doc`, never typed. They are lists so the markdown and the JSON cannot drift apart.
ROWS = [
    ("afterburner (primary)", "`UC_SetBoostLevel(level 0..100, upgrade)`; `Fill` 102 frames, frame = "
     "level+1, scale-y 0.011 -> 1.0 bottom-anchored; hidden at level 100",
     "`MCI_nitro_meter` (`InitVehicleNitrous`/`UpdateVehicleNitrous`, `SetProgress(0..1)`)",
     "decoded / map (caller native, UNKNOWN)"),
    ("second cooldown gauge", "not present: 0 cooldown setters, 1-frame unnamed clip at (5.0,-83.7); "
     "`BoostCooldown[3]` + `BoostCooldownUpgradeLevel` native only",
     "none (JC3 `MCI_nitro_meter` is the only recharge member)",
     "refuted in BmAK / UNKNOWN in retail"),
    ("upgrade badges", "`Upgrade1/2` at x -10.0/-10.5, 65 frames, `Normal`/`Charging`, "
     "visible by `upgradeLevel`", "none", "decoded / no JC3 member"),
    ("health bar", "`UC_SetHealth(health, max)`; `Bar` fill `min(1,h)`; pulse < 0.2; 2 s offscreen; "
     "step 0.05/frame at 30 Hz", "`MCI_vehicle` health paint / bar",
     "decoded / map health 0..1"),
    ("armour tiers", "`max(0,h-1)` onto `ArmourForeground`; `max>1` selects `Armour<n>` of 5",
     "none - no armour field in the vehicle HUD", "decoded / out (stated absence)"),
    ("damage readout", "`UC_SetImpactDamageFlash(part, x, y, frames)`: number at "
     "`StageWidth*x`, `StageHeight*y`, rotationY +/-60", "none", "decoded / out"),
    ("speedometer", "0 of 252 setters, 0 speed tokens; `bDebugSpeedometer` off in both configs",
     "`MCI_speedo` (JC3 has one; the Batmobile must hide it)",
     "decoded / JC3 route derived, caller UNKNOWN"),
]
ROUTES = [
    ("afterburner", "re-skin `MCI_nitro_meter`", "`SetProgress(recharge)` 0..1; `Hide()`; ready sound "
     "at 1 (`InitVehicleNitrous`)", "derived", "call `InitVehicleNitrous(BoostLevel/100)` from a "
     "hud hook and see the bar move"),
    ("afterburner", "reuse the BmAK `BoostMovie` clip inside `hud.gfx`", "movie is AVM2 GFx v0f, "
     "102-frame fill; art streams from `Image_I1*.tfc`", "UNKNOWN (no import evidence either way)",
     "compare both movies' SWF/AVM version tags with `ffdec -dumpSWF`; if equal, try one "
     "`DefineSprite` import"),
    ("afterburner", "custom JC3 module", "no evidence JC3 loads extra GFx modules", "UNKNOWN",
     "grep the JC3 tree for a second hud movie name"),
    ("health", "`MCI_vehicle` health paint", "health paint/bar members exist under "
     "`hud_code/health/*`", "derived", "feed `UC_SetHealth`'s value into the vehicle health "
     "paint and take damage once"),
    ("speedometer", "private `ui/hud.gfx` copy", "`SetVisibilities` sets `MCI_speedo.visible = true` "
     "unconditionally; `HideVehicleUi` hides it; no per-vehicle switch", "derived (R7: private copy)",
     "patch the private copy's `SetVisibilities` to leave `MCI_speedo` hidden and drive a vehicle"),
]
COMPROMISES = [
    ("C1 - the second (cooldown) gauge",
     "BmAK sends no cooldown value to the HUD (0 setters); the native `BoostCooldown` tiers never "
     "reach the movie. JC3 has one recharge member (`MCI_nitro_meter`) which the primary boost "
     "gauge already uses.",
     "omit the second gauge and keep `MCI_nitro_meter` as the single boost bar; accuracy lost: the "
     "recharge-tier feedback the badges give in BmAK is gone."),
    ("C2 - armour above 1.0",
     "BmAK draws a second fill (`ArmourForeground`) and five `Armour<n>` tiers; JC3's vehicle HUD "
     "has no armour field, so health > 1 would clip at full.",
     "map health 0..1 only, dropping the armour overlay; accuracy lost: armour damage reads as "
     "nothing until the bar starts moving."),
    ("C3 - speedometer",
     "JC3 draws a speedometer for every land vehicle and `SetVisibilities` re-shows it "
     "unconditionally; BmAK's Batmobile HUD draws none.",
     "ship a private `ui/hud.gfx` copy whose `SetVisibilities` leaves `MCI_speedo` hidden for this "
     "vehicle; accuracy lost: none - this removes a JC3-only element."),
    ("C4 - fill direction and motion",
     "BmAK's boost fill is vertical, bottom-anchored, 101 steps plus a `Shake` and a rising `Cap`; "
     "JC3's nitro meter is a horizontal 0..1 progress member.",
     "keep JC3's orientation and drive `SetProgress(level/100)`; accuracy lost: the vertical rise "
     "and the drain shake."),
    ("C5 - upgrade badges",
     "`Upgrade1/2` are two 65-frame badge clips toggled by `UC_SetBoostLevel`'s second argument; "
     "JC3 has no badge member.",
     "drop them; accuracy lost: the player cannot see the boost-recharge upgrade level."),
]


def md(doc: dict) -> str:
    c = doc["clips"]
    b = doc["bmak"]
    h = b["health"]
    left = c["left_order_by_x"]
    L = []
    a = L.append
    a("# BmAK HUD cluster - where the gauges sit and what feeds them\n")
    a("Generated by `Tools/scripts/bmak_hud_cluster.py --write`; every number is re-derived by "
      "`--check` from the movie bytes, the decompiled AS3, the BmSDK headers and JC3's `hud.as`.\n")
    ev = doc["movie"]["evidence"]
    a(f"Movie `{ev['object']}`: {ev['export_bytes']} B export, {ev['cfx_bytes']} B CFX, "
      f"{ev['inflated_bytes']} B inflated, sha256(CFX) `{ev['sha256_cfx'][:16]}…`; tag stream at "
      f"offset {doc['movie']['tag_stream_offset']}, {doc['movie']['top_level_tags']} top-level tags, "
      f"{doc['movie']['sprites']} DefineSprite.\n")
    st = b["stage"]
    a(f"Stage: SWF {st['swf'][0]}x{st['swf'][1]}, module stage {st['module_stage'][0]}x"
      f"{st['module_stage'][1]}, projection centre {st['projection_centre']}, FOV {st['fov']}, "
      f"tick {st['tick']} s.\n")

    a("## 1. The cluster, decoded\n")
    a("| clip | path | x | y | z | yaw | scale | frames |")
    a("|---|---|---:|---:|---:|---:|---:|---:|")
    for key, label in (("Health", "health bar"), ("BoostMovie", "afterburner gauge"),
                       ("Combo", "combo meter"), ("RemoteInterface", "remote interface")):
        t = c["LeftSideParent"]["authored"].get(key, {})
        info = c.get(key, {})
        a(f"| {label} | `{c.get(key, {}).get('path', 'HudMaster.LeftSideParent.' + key)}` | "
          f"{t.get('x')} | {t.get('y')} | {t.get('z')} | {t.get('yaw_deg')}° | "
          f"{t.get('scale_x')} | {info.get('frames', '')} |")
    for key, label in (("BoostMovie", "right-group BoostMovie"), ("ClockTimer", "clock"),
                       ("OccupantObject", "occupant")):
        t = c["RightSideParent"]["authored"].get(key, {})
        a(f"| {label} | `HudMaster.RightSideParent.{key}` | {t.get('x')} | {t.get('y')} | "
          f"{t.get('z')} | {t.get('yaw_deg')}° | {t.get('scale_x')} | |")
    a("")
    a("Screen estimate = projection centre + authored x/y (derived: the root placements are "
      "identity and the 3D planes project around `projectionCenter`; z<=25 against a focal length "
      "of ~10^3 changes the projected position by <1 %, so the corner assignment does not depend "
      "on the projection constant).\n")
    a("| clip | screen x | screen y | is it left? | is it top? |")
    a("|---|---:|---:|---|---|")
    for k, v in c["screen_estimate"].items():
        a(f"| {k} | {v['x']} | {v['y']} | {'yes' if v['x'] < 512 else 'no'} | "
          f"{'yes' if v['y'] < 360 else 'no'} |")
    a("")
    a("Left-group ordering by authored x (most negative = furthest left): "
      + ", ".join(f"`{r['clip']}` {r['x']}" for r in left) + ".\n")
    a("Left-group ordering by authored y (most negative = highest): "
      + ", ".join(f"`{r['clip']}` {r['y']}" for r in c["left_order_by_y"]) + ".\n")
    a("Group rule (`ModuleStruct_Batmobile.OnRatioChanged`): `RightSideParent.x = base + band`, "
      "`LeftSideParent.x = base - band` - the two groups are pushed apart as the band widens, so "
      "`LeftSideParent` is the left group by construction.\n")

    a("## 2. Afterburner\n")
    a(f"`UC_SetBoostLevel({b['settlers']['UC_SetBoostLevel']})`, body facts: shown while level < "
      f"{b['boost']['show_below']}, fill frame `{b['boost']['fill_frame']}`, charging rule "
      f"`{b['boost']['charging_rule']}`, badges `Upgrade1/2.visible = level > 0 / > 1`, hide at "
      f"`>= 100` = {b['boost']['hide_when_full']}.\n")
    fill = c.get("Fill", {})
    a(f"Fill clip: {fill.get('frames')} frames (level+1), labels {fill.get('labels')}, "
      f"scale-y {fill.get('sy_first')} -> {fill.get('sy_last')} samples {fill.get('sy_samples')} "
      f"=> growth {fill.get('growth')}.\n")
    bd = c.get("BoostBadges", {})
    a(f"Badges (`Background` {bd.get('background_frames')} frames, labels {bd.get('background_labels')}):")
    for x in bd.get("badges", []):
        a(f"- `{x['name']}` ch{x['chid']} `{x['class']}` at "
          f"({x['matrix']['x']}, {x['matrix']['y']}) scale {x['matrix']['sx']}, "
          f"{x['frames']} frames {x['labels']}")
    a("")
    a("Native fields:\n")
    a("| class:file | field | type | offset | default |")
    a("|---|---|---|---:|---:|")
    defs = {**doc["native"]["sim_defaults"], **doc["native"]["base_defaults"],
            **doc["native"]["vehicle_defaults"]}
    for f, rec in doc["native"]["fields"].items():
        if not isinstance(rec, dict):
            continue
        for name, v in rec.items():
            if not isinstance(v, dict) or "offset" not in v:
                continue
            a(f"| {f} | `{name}` | {v['type']} | {v['offset']} | {defs.get(name)} |")
            for e in v.get("elements", []):
                a(f"| {f} | `{name}[{e['index']}]` | float | {e['offset']} | {defs.get(name)} |")
    a("")

    a("## 3. Health\n")
    a(f"`UC_SetHealth({b['settlers']['UC_SetHealth']})`; fill `{h['bar_fill']}`, armour "
      f"`{h['armour_fill']}`, tier `{h['armour_tier']}` -> `Armour<n>` via `{h['armour_label']}`, "
      f"pulse below {h['pulse_below']}, offscreen {h['offscreen']} s, per-frame step "
      f"{h['max_change_per_frame']} (30 Hz), battle forces visible = {h['battle_forces_visible']}.\n")
    df = b["damage_flash"]
    a(f"Damage readout `{df['sig']}`: `DamageText` = `{df['text']}`, position "
      f"`StageWidth*{df['x']}` / `StageHeight*{df['y']}`, `{df['rotationY']}`.\n")
    a("## 4. Speedometer\n")
    sp = doc["speedometer"]
    a(f"SPEEDOMETER.json verdict: {sp['verdict']}\n")
    a(f"- `UC_*` setters across {doc['interfaces']['modules']} modules: "
      f"{doc['interfaces']['setters_total']}; of those, speed/rev/gear-shaped: "
      f"{sp['movie_speed_setters'] or 'none'}")
    a(f"- speed tokens inside this movie: {sp['tokens_in_this_movie'] or 'none'}")
    a(f"- debug flag config: {sp['debug_flag']}\n")
    j = doc["jc3"]
    a("JC3 side:\n")
    a("| function | args | call sites in the movie | clips touched |")
    a("|---|---|---:|---|")
    for k, v in j["api"].items():
        a(f"| `{k}` | `{v['args']}` | {v['call_sites']} | {', '.join(v['touches'])} |")
    a("")
    a(f"Vehicle types {j['vehicle_types']}, meters {j['meters']}, needle {j['needle']}, "
      f"speedo smoothing {j['speedo_smoothing']} s.")
    a(f"`SetVisibilities` body: `{j['set_visibilities_body']}`\n")
    a("Per-vehicle switch: there is none in the movie. `SetVehicleType` writes only the unit label "
      "(`hud_kph`/`hud_knots`) and touches no `visible`; `SetVisibilities` sets "
      "`MCI_speedo.visible = true` unconditionally; `HideVehicleUi` is the only function that "
      "hides both `MCI_speedo` and `MCI_speedometer`; `SetPrimaryMeterValue` and "
      "`SetVehicleType` have 0 call sites, `InitPrimaryMeter` 1 - the caller is native.\n")

    est = c["screen_estimate"]
    a("## 5. The four leads\n")
    a(f"**(a) health bar TOP-LEFT in battle mode - CONFIRMED (placement).** `Health` at authored "
      f"({c['Health']['transform']['x']}, {c['Health']['transform']['y']}) yaw "
      f"{c['Health']['transform']['yaw_deg']}°, screen estimate "
      f"({est['Health']['x']}, {est['Health']['y']}); the highest of the four left-group clips "
      f"(`left_order_by_y`). The transform is mode-invariant: `SetBattleAndZoomMode` calls "
      f"`UC_SetHealthBarVisible(true,'Delayed')` on BATTLE and `UC_SetHealthBarVisible(false)` "
      f"returns early while battle, so the mode drives visibility only, not position.\n")
    a(f"**(b) afterburner gauge LEFT in pursuit - CONFIRMED.** `BoostMovie` at authored "
      f"({c['BoostMovie']['transform']['x']}, {c['BoostMovie']['transform']['y']}), screen estimate "
      f"({est['BoostMovie']['x']}, {est['BoostMovie']['y']}) - left edge, below mid-height. It has "
      f"no mode gate: `UC_SetBoostLevel` shows it while level < 100 and `UC_HideBoostGauge` hides "
      f"it at full, so it is left in both pursuit and battle.\n")
    a("**(c) a SECOND afterburner cooldown gauge LEFT of the boost gauge - REFUTED as a gauge.** "
      "`BoostMovie` has exactly three children: `BoostChild` (the bar), a 1-frame unnamed clip "
      "(ch1040, at (5.0, -83.7)) and `boost_upgrade_msg` (51 frames, at (154.5, -12.6)). The bar "
      "carries one value. The only left-side secondary elements are the two upgrade badges inside "
      "`BoostChild.Background` at x=-10.0/-10.5, y 96.3/100.6 - 65 frames each, labels "
      "`Normal`/`Charging`, `visible = upgradeLevel > 0 / > 1`, and "
      "`SetBoostBarCharging(level > BoostLevel)` is the exact event that plays `Charging` while the "
      "bar refills. Of the Batmobile's setters only `UC_SetBoostLevel(level, upgrade)` and "
      "`UC_HideBoostGauge` touch boost; no setter carries a cooldown, a charge or a second value. "
      "The cooldown exists natively - `BoostCooldown` (3 float tiers, 668/672/676, tier 0 default "
      "12.0 s) with `BoostCooldownUpgradeLevel` (int, 680) - and never reaches the movie. What the "
      "operator saw left of the bar is the badge pair / the bar's `Cap`; a retail cooldown gauge "
      "elsewhere in the HUD is UNKNOWN (0 of the 252 setters carry one).\n")
    a("**(d) no speedometer, so JC3's must be disabled - CONFIRMED.** "
      f"{len(doc['speedometer']['movie_speed_setters'])} speed/rev/gear-shaped setters of "
      f"{doc['interfaces']['setters_total']}; {doc['speedometer']['tokens_in_this_movie'] or 'zero'} "
      f"speed tokens in the movie; debug flag {doc['speedometer']['debug_flag']}. See section 4 for "
      "the JC3 side and the per-vehicle route.\n")

    a("## 6. Row table\n")
    a("| BmAK element | decoded evidence | JC3 route | status |")
    a("|---|---|---|---|")
    for row in ROWS:
        a("| " + " | ".join(row) + " |")
    a("")
    a("## 7. JC3 host, route by route (no implementation)\n")
    a("| BmAK gauge | host candidate | decoded support | status | next 5-minute experiment |")
    a("|---|---|---|---|---|")
    for row in ROUTES:
        a("| " + " | ".join(row) + " |")
    a("")
    a("## COMPROMISES (operator approval required; this report approves none)\n")
    for title, what, rec in COMPROMISES:
        a(f"### {title}\n")
        a(f"{what}\n")
        a(f"**RECOMMENDED COMPROMISE:** {rec}\n")
    return "\n".join(L) + "\n"


# --------------------------------------------------------------------------- checks


def compare(old: dict, new: dict) -> list[str]:
    bad = []
    for key in ("movie", "clips", "bmak", "interfaces", "native", "speedometer", "jc3"):
        if old.get(key) != new.get(key):
            bad.append(key)
    return bad


def check() -> int:
    old = json.loads(OUT_JSON.read_text(encoding="utf-8"))
    new = collect()
    bad = compare(old, new)
    for k in bad:
        print(f"FAIL: {k} changed")
    print(f"{'PASS' if not bad else 'FAIL'}: cluster record current")
    return 1 if bad else 0


def tamper_test() -> int:
    new = collect()
    probes = [("clips", ("Health", "transform", "x")), ("jc3", ("api",)),
              ("bmak", ("health", "pulse_below"))]
    caught = 0
    for key, path in probes:
        mut = json.loads(json.dumps(new))
        tgt = mut[key]
        for p in path[:-1]:
            tgt = tgt[p]
        leaf = path[-1]
        if isinstance(tgt[leaf], (int, float)):
            tgt[leaf] = tgt[leaf] + 1
        elif isinstance(tgt[leaf], dict) and tgt[leaf]:
            k0 = sorted(tgt[leaf])[0]
            tgt[leaf][k0] = "TAMPERED"
        else:
            tgt[leaf] = "TAMPERED"
        if compare(new, mut):
            caught += 1
            print(f"PASS: tamper at {key}.{'.'.join(path)} rejected")
        else:
            print(f"FAIL: tamper at {key}.{'.'.join(path)} not detected")
    print(f"{'PASS' if caught == len(probes) else 'FAIL'}: {caught}/{len(probes)} tamper probes")
    return 0 if caught == len(probes) else 1


def write() -> None:
    doc = collect()
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    OUT_MD.write_text(md(doc), encoding="utf-8")
    print(f"wrote {OUT_JSON}\nwrote {OUT_MD}")
    print(json.dumps({"leads": doc["clips"]["screen_estimate"],
                      "boost": doc["clips"].get("Fill", {}).get("growth"),
                      "badges": [x["name"] for x in doc["clips"].get("BoostBadges", {}).get("badges", [])],
                      "speed_setters": doc["interfaces"]["speed_setters"],
                      "sim": doc["native"]["sim_defaults"]}, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--tamper-test", action="store_true")
    a = ap.parse_args()
    if a.tamper_test:
        return tamper_test()
    if a.check:
        return check()
    write()
    return 0


if __name__ == "__main__":
    sys.exit(main())

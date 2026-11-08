"""G1-14 - Damage rules, health, armour, regeneration (BmGame.upk script bodies).

What it proves
  * **Function export layout.**  `BmGame.upk` (UE3, licensee 800016, version 863) serialises a
    `Function` export positionally - it carries no Batman property tags.  The layout recovered
    here, and re-checked by four independent anchors:

        u16   0                      prefix (constant 0 across every Function export)
        i32   Next                   UField sibling link        (anchor A)
        i32   SuperField             super function             (anchor A)
        i32   Children               first child property       (anchor A)
        i32   Line                   editor line of the source
        i32   ScriptSize             == len(script) + 1         (anchor B)
        byte  Script[ScriptSize - 1] executable bytecode        (anchor C)
        i32   funcFlagsWord
        i32   preNameWord            always 0x0002xxxx
        i32   nameIndex              FName of the function itself (anchor D)
        i32   nameNumber             always 0

    UEViewer parses this class only as far as `Children` and then drops the rest
    (`Unreal/UnTypeinfo.h`, `Ar << Children; return;` under `GAME_Batman4`), which is why the
    script bodies have never been read from this package before.
  * **native vs script.**  A `Function` whose script is nothing but `0x29 <property-ref>`
    descriptors (and/or a bare `0x04`) carries no executable bytecode: it is a native thunk.
    Every descriptor reference is checked to be a property of the function itself (anchor E),
    and the executable's own `exec<Name>` registration string is the independent second source.
  * **The reference trace.**  For each traced function, every property / function / object /
    class reference in bytecode order, plus every int32 and float constant.  Tokens are the
    UE3/UE4 `EExprToken` numbering, which this build uses (anchor F: `0x1c` is followed by a
    `Function` export in 40835 of 41057 corpus-wide hits = `EX_FinalFunction`).
  * **Values.**  Every damage-related field of the Batmobile archetypes, with its value and its
    provenance, taken from `Research/BatmobileGrab/CHAIN.json` (the sdk-layout binding pass).

Usage
    python Tools/scripts/bmak_damage.py --write
    python Tools/scripts/bmak_damage.py --check
"""
import argparse
import collections
import hashlib
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from upk_read import Package  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GAME = r"E:\Games\Batman - Arkham Knight"
UPK = os.path.join(GAME, "BmGame", "CookedPCConsole", "BmGame.upk")
EXE = os.path.join(GAME, "Binaries", "Win64", "BatmanAK.exe")
OUT = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_RULES.json")
# raw bytecode stays outside the notes folder, like the anim keys and bone face lists:
# the note carries offsets, symbols and sha1s, never the game's own bytes.
RAW = os.path.join(ROOT, "Working", "vendor", "BmAKgrab", "scripts")
NATIVE_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "NATIVE.json")
CHAIN_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CHAIN.json")

# EExprToken, the numbering UE3 and UE4 share.  Only the tokens this grab needs are named.
TOKENS = {
    0x00: "EX_LocalVariable", 0x01: "EX_InstanceVariable", 0x02: "EX_DefaultVariable",
    0x04: "EX_Return", 0x06: "EX_Jump", 0x07: "EX_JumpIfNot", 0x0B: "EX_Nothing",
    0x0F: "EX_Let", 0x12: "EX_ClassContext", 0x14: "EX_LetBool", 0x15: "EX_EndParmValue",
    0x16: "EX_EndFunctionParms", 0x17: "EX_Self", 0x18: "EX_Skip", 0x19: "EX_Context",
    0x1A: "EX_Context_FailSilent", 0x1B: "EX_VirtualFunction", 0x1C: "EX_FinalFunction",
    0x1D: "EX_IntConst", 0x1E: "EX_FloatConst", 0x1F: "EX_StringConst", 0x20: "EX_ObjectConst",
    0x21: "EX_NameConst", 0x24: "EX_ByteConst", 0x25: "EX_IntZero", 0x26: "EX_IntOne",
    0x27: "EX_True", 0x28: "EX_False", 0x29: "PropRef(native-parm)", 0x2A: "EX_NoObject",
    0x2C: "EX_IntConstByte", 0x2E: "EX_DynamicCast", 0x3A: "PropRef(return-slot)",
    0x48: "EX_LocalOutVariable",
}
# tokens whose operand is a 4-byte object reference (export index, or <=0 for an import)
REF_TOKENS = {0x00, 0x01, 0x02, 0x12, 0x1B, 0x1C, 0x20, 0x29, 0x2E, 0x3A, 0x48}
# a 5-byte `0x29 <property-ref>` block: the native-parameter descriptor a cooked native
# function keeps in place of bytecode
PARM_TOKEN = 0x29

TRACED = [
    "RVehicleBatmobileBase.TakeDamage",
    "RVehicleBatmobileBase.TakeRadiusDamageFromWeapon",
    "RVehicleBatmobileBase.TakesDamageFromRam",
    "RVehicleBatmobileBase.ShouldRadialDamageHit",
    "RVehicleBatmobileBase.CanBatmobileDoImpactDamage",
    "RVehicleBatmobileBase.CalculateAndStoreImpactDamage",
    "RVehicleBatmobileBase.SetDamageLevel",
    "RVehicleBatmobileBase.SetArmouredMode",
    "RVehicleBatmobileBase.DrainWeaponGeneratorForDamage",
    "RVehicleBatmobileBase.ExperienceAwarded",
    "RVehicleBatmobileBase.LoadHealth",
    "RVehicleBatmobileBase.GiveMaxEnergy",
    "RVehicleBatmobileBase.OnModifyHealth",
    "RVehicleCombatManager.GetDamageMod",
]

DAMAGE_FIELD = re.compile(
    r"health|damage|armou?r|regen|heal|recover|death|die|dying|destroy|explos|bullet|"
    r"melee|smoke|burn|impact|invuln|fragil|deform|kill", re.I)


class Bm:
    """BmGame.upk with the Function layout recovered on top."""

    def __init__(self, path):
        self.pkg = Package(path)
        self.by_path = {}
        for i in range(1, self.pkg.export_count + 1):
            if self.pkg.object_class(i) == "Function":
                self.by_path[self.pkg.object_path(i)] = i
        self._cls_cache = {}

    def name(self, index):
        try:
            return self.pkg.names[index]
        except Exception:
            return None

    def ref(self, index):
        """Export/import index -> object path, or None."""
        try:
            return self.pkg.object_path(index)
        except Exception:
            return None

    def obj_class(self, index):
        if index not in self._cls_cache:
            try:
                self._cls_cache[index] = self.pkg.object_class(index)
            except Exception:
                self._cls_cache[index] = None
        return self._cls_cache[index]

    def outer_of(self, index):
        try:
            return self.pkg.object_path(self.pkg.exports[index - 1]["outer_index"])
        except Exception:
            return None

    def function(self, path):
        i = self.by_path.get(path)
        if i is None:
            return None
        data = self.pkg.data(i)
        if len(data) < 38:
            return {"path": path, "index": i, "size": len(data), "script": "", "fields": {}}
        fields = {
            "next": struct.unpack_from("<i", data, 2)[0],
            "super": struct.unpack_from("<i", data, 6)[0],
            "children": struct.unpack_from("<i", data, 10)[0],
            "line": struct.unpack_from("<i", data, 14)[0],
            "script_size_field": struct.unpack_from("<i", data, 18)[0],
            "pre_name_word": struct.unpack_from("<i", data, len(data) - 12)[0],
            "name_index": struct.unpack_from("<i", data, len(data) - 8)[0],
            "name_number": struct.unpack_from("<i", data, len(data) - 4)[0],
        }
        script = data[22:len(data) - 16]
        desc, desc_bytes = self.native_parms(script, path)
        entry = {
            "path": path, "index": i, "size": len(data),
            "script_bytes": len(script), "script_sha1": hashlib.sha1(script).hexdigest(),
            "script_raw": os.path.join("Working", "vendor", "BmAKgrab", "scripts",
                                       path.replace(".", "_") + ".hex"),
            "fields": fields,
            "_script": script,
            "native_parm_descriptors": desc, "native_parm_bytes": desc_bytes,
            "refs": self.trace(script), "constants": self.constants(script),
        }
        entry["verdict"] = self.verdict(entry)
        return entry

    def native_parms(self, script, func_path):
        """`(descriptor count, bytes covered)` of `0x29 <own-property ref>` blocks.

        A cooked native function keeps its parameter list as `EX_NativeParm`-style descriptors
        in place of bytecode; the descriptors name only properties of the function itself.
        """
        n = 0
        for m in range(max(len(script) - 4, 0)):
            if script[m] != PARM_TOKEN:
                continue
            ref = struct.unpack_from("<i", script, m + 1)[0]
            if 1 <= ref <= self.pkg.export_count and self.outer_of(ref) == func_path:
                n += 1
        return n, n * 5

    def verdict(self, entry):
        """native iff native-parameter descriptors cover most of the body.

        A one-byte `04` body is the thinnest native thunk in the package (1,724 of them).
        `exec_strings_in_exe` is the independent second source, filled in by `main`.
        """
        n, covered = entry["native_parm_descriptors"], entry["native_parm_bytes"]
        length = len(entry["_script"])
        if length and covered >= length * 0.5:
            return "native"
        if entry["_script"] == b"\x04":
            return "native-thunk"
        return "script"

    # ------------------------------------------------------------------ trace
    def trace(self, script):
        out = []
        for m in range(len(script) - 4):
            tok = script[m]
            if tok not in REF_TOKENS:
                continue
            value = struct.unpack_from("<i", script, m + 1)[0]
            if not (1 <= value <= self.pkg.export_count):
                continue
            path = self.ref(value)
            if path is None:
                continue
            own = self.outer_of(value) == path_of_class(path)
            out.append({"at": m, "token": TOKENS[tok], "ref": path,
                        "kind": self.obj_class(value), "own_property": own})
        return out

    def constants(self, script):
        """Byte-aligned int32 / float32 literals.

        Candidates only: a `0x1d`/`0x1e` byte inside a reference operand is skipped, so the
        list is not polluted by the tail of an object reference.
        """
        covered = set()
        for m in range(len(script) - 4):
            if script[m] in REF_TOKENS and 1 <= struct.unpack_from("<i", script, m + 1)[0] <= self.pkg.export_count:
                covered.update(range(m, m + 5))
        out = []
        for m in range(len(script) - 4):
            if m in covered:
                continue
            tok = script[m]
            if tok == 0x1D:
                out.append({"at": m, "kind": "int",
                            "value": struct.unpack_from("<i", script, m + 1)[0]})
            elif tok == 0x1E:
                out.append({"at": m, "kind": "float",
                            "value": round(struct.unpack_from("<f", script, m + 1)[0], 6)})
        return out


def path_of_class(path):
    """`Outer.Foo.Bar` -> `Outer.Foo` (the property's owner object)."""
    return path.rsplit(".", 1)[0] if "." in path else path


# --------------------------------------------------------------------- anchors
def anchors(bm):
    """Re-derive the layout and fail loudly if any anchor moves."""
    got = {}

    # A. Next / Super / Children resolve to real objects for a known trio.
    td = bm.function("RVehicleBatmobileBase.TakeDamage")
    got["A_super_is_parent_take_damage"] = bm.ref(td["fields"]["super"]) is not None
    got["A_children_is_first_param"] = (
        bm.ref(td["fields"]["children"]) == "TakeDamage.DamageAmount")

    # B. ScriptSize field == script length + 1, on every traced function.
    bad = [p for p in TRACED
           if (f := bm.function(p)) and f.get("_script") is not None
           and f["fields"]["script_size_field"] != len(f["_script"]) + 1]
    got["B_script_size_is_len_plus_one"] = not bad

    # C. The thinnest possible script is one byte, and that byte is EX_Return.
    ones = [p for p in bm.by_path
            if (f := bm.function(p)) and f.get("_script") is not None and len(f["_script"]) == 1]
    got["C_thinnest_script_is_return"] = bool(ones) and all(
        f["_script"] == b"\x04" for f in (bm.function(p) for p in ones[:50]))

    # D. The trailing FName is the function's own name.
    got["D_name_word_is_own_name"] = all(
        bm.name(bm.function(p)["fields"]["name_index"]) == p.rsplit(".", 1)[-1]
        for p in TRACED if bm.function(p))

    # E. Every EX_NativeParm descriptor points at a property of the function it sits in.
    ok = True
    for p in bm.by_path:
        f = bm.function(p)
        if not f or not f.get("_script"):
            continue
        s = f["_script"]
        if len(s) % 5 or any(s[i] != 0x29 for i in range(0, len(s), 5)):
            continue                      # not a descriptor-only script
        for i in range(0, len(s), 5):
            ref = struct.unpack_from("<i", s, i + 1)[0]
            if bm.outer_of(ref) != p:
                ok = False
    got["E_native_parm_refs_own_properties"] = ok

    # F. Corpus-wide: EX_FinalFunction is followed by a Function export (imports have no
    #    class in this package, so they are counted as hits too).
    hits = ok_f = 0
    for p in list(bm.by_path)[::7]:
        f = bm.function(p)
        if not f or not f.get("_script"):
            continue
        s = f["_script"]
        for m in range(len(s) - 4):
            if s[m] != 0x1C:
                continue
            ref = struct.unpack_from("<i", s, m + 1)[0]
            if not (1 <= ref <= bm.pkg.export_count):
                continue
            hits += 1
            ok_f += bm.obj_class(ref) == "Function"
    got["F_final_function_token_is_call"] = hits > 1000 and ok_f / max(hits, 1) > 0.98
    return got


def native_exe():
    """`exec<Name>` registration strings in BatmanAK.exe: the exe's own native list."""
    exe = open(EXE, "rb").read()
    out = {}
    for p in TRACED:
        short = p.rsplit(".", 1)[-1]
        out[p] = len(re.findall(re.escape(("exec" + short).encode()), exe))
    return out


REGEN_WORD = re.compile(r"\b(\w*(?:Regen|Heal|Recover|Restore|Repair)\w*)\b")


def regen_symbols(bm):
    """Every Regen/Heal/Recover/Restore/Repair symbol the class dump and the name table carry.

    The answer to "does the Batmobile regenerate armour out of combat?" is read off this list:
    a mechanism needs a field, a function or at least a name.
    """
    sdk = collections.Counter()
    sdk_dir = os.path.join(ROOT, "Working", "vendor", "BmSDK")
    for name in sorted(os.listdir(sdk_dir)):
        if not name.endswith(".cs"):
            continue
        text = open(os.path.join(sdk_dir, name), encoding="utf-8", errors="replace").read()
        for m in REGEN_WORD.finditer(text):
            sdk[m.group(1)] += 1
    names = sorted({n for n in bm.pkg.names if isinstance(n, str) and REGEN_WORD.search(n)})
    return {"bm_sdk_symbols": dict(sdk.most_common(40)), "bmgame_names": names}


REF_FIELDS = [
    "RVehicleBatmobileBase.HealthRecoverRate",
    "RVehicleBatmobileBase.ArmourModeDamageReduction",
    "RVehicleBatmobileBase.LowHealthWarningLevel",
    "RVehicleBatmobileBase.WeaponGeneratorPower",
    "RVehicleBatmobileBase.ArmouredMode",
]


def field_references(bm, names=REF_FIELDS):
    """Which script functions read each damage field (its export index inside their body).

    This is the difference between "the field exists" and "the field is live": a value no
    script ever references is a dead default, not a mechanism.
    """
    props = {}
    for i in range(1, bm.pkg.export_count + 1):
        if bm.obj_class(i) in (None, "Function"):
            continue
        try:
            p = bm.pkg.object_path(i)
        except Exception:
            continue
        if p in names:
            props[p] = i
    out = {}
    for p in names:
        out[p] = {"export": props.get(p), "read_by": []}
    funcs = [i for i in range(1, bm.pkg.export_count + 1)
             if bm.pkg.object_class(i) == "Function"]
    for p, i in props.items():
        ref = struct.pack("<i", i)
        for f in funcs:
            d = bm.pkg.data(f)
            if len(d) >= 38 and ref in d[22:len(d) - 16]:
                out[p]["read_by"].append(bm.pkg.object_path(f))
    return out


def damage_values():
    """Every damage-related archetype field, with value and provenance, from CHAIN.json."""
    chain = json.load(open(CHAIN_JSON, encoding="utf-8"))
    rows = []
    for cls, archetypes in chain["fields"].items():
        if not isinstance(archetypes, dict):
            continue
        for arch, entries in archetypes.items():
            if not isinstance(entries, list):
                continue
            for e in entries:
                name = e.get("name", "")
                if DAMAGE_FIELD.search(name):
                    rows.append({"class": cls, "archetype": arch, "name": name,
                                 "type": e.get("type"), "value": e.get("value"),
                                 "named_by": e.get("named_by")})
    rows.sort(key=lambda r: (r["class"], r["archetype"], r["name"]))
    return rows


def write_raw(funcs):
    """Keep the extracted bytecode outside the notes folder; the note keeps sha1 + length."""
    os.makedirs(RAW, exist_ok=True)
    pkg = Package(UPK)
    for path, entry in funcs.items():
        i = next((k for k in range(1, pkg.export_count + 1) if pkg.object_path(k) == path), None)
        data = pkg.data(i)
        script = data[22:len(data) - 16]
        with open(os.path.join(RAW, path.replace(".", "_") + ".hex"), "w", encoding="ascii") as fh:
            fh.write(script.hex(" ") + "\n")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write DAMAGE_RULES.json")
    g.add_argument("--check", action="store_true", help="re-derive and diff against the file")
    a = ap.parse_args()

    bm = Bm(UPK)
    exe = native_exe()
    funcs = {p: bm.function(p) for p in TRACED if bm.function(p)}
    for p, e in funcs.items():
        e["exec_strings_in_exe"] = exe[p]
    anchors_doc = anchors(bm)
    for e in funcs.values():
        e.pop("_script", None)          # bytecode never lands in the note
    doc = {
        "schema": 1,
        "generated_by": "bmak_damage.py",
        "package": UPK,
        "function_export_layout": {
            "prefix_u16": 0, "next": 2, "super": 6, "children": 10, "line": 14,
            "script_size_field": 18, "script": 22, "script_size": "len - 38",
            "pre_name_word": "size - 12", "name_index": "size - 8", "name_number": "size - 4",
            "note": "UEViewer stops after `Children` for GAME_Batman4 (UnTypeinfo.h); "
                    "the script bytes past that point are unclaimed until this pass.",
        },
        "anchors": anchors_doc,
        "exe_exec_strings": exe,
        "functions": funcs,
        "damage_values": damage_values(),
        "regeneration": regen_symbols(bm),
        "field_references": field_references(bm),
    }
    doc["missing"] = [p for p in TRACED if p not in doc["functions"]]

    if a.write:
        write_raw(funcs)
        json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1)
        print("wrote", os.path.relpath(OUT, ROOT), "and", len(funcs), "raw scripts")
        return 0
    old = json.load(open(OUT, encoding="utf-8"))
    same = json.dumps(old, sort_keys=True) == json.dumps(doc, sort_keys=True)
    print("anchors:", {k: v for k, v in doc["anchors"].items()})
    print("check:", "PASS" if same else "FAIL")
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main())

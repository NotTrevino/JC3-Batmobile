"""G1-14 - Damage rules, health, armour, regeneration (BmGame.upk script bodies).

What it proves
  * **Function export layout.**  `BmGame.upk` (UE3, licensee 800016, version 863) serialises a
    `Function` export positionally - it carries no Batman property tags.  The layout recovered
    here, and re-checked by seven independent anchors:

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
  * **The reference trace.**  One left-to-right token walk (`walk()`), not a byte scan: a
    candidate is accepted only if it starts at or after the end of the last accepted token, so a
    reference index can no longer hide a literal that begins inside it.  Each accepted token is
    recorded with its byte offset; the candidates that lost an overlap are kept beside it as
    `walk.rejected`, which is the noise the note must not present as a call.
  * **Values.**  Every damage-related field of the Batmobile archetypes, with its value and its
    provenance, taken from `Research/BatmobileGrab/CHAIN.json` (the sdk-layout binding pass).

Outputs
  * `DAMAGE_RULES.json` - the machine record.
  * `DAMAGE_RULES.md`   - rendered from that record by `render_md()`; never hand-edited.
  * `Working/vendor/BmAKgrab/scripts/*.hex` - the extracted bodies, outside the notes folder.

Usage
    python Tools/scripts/bmak_damage.py --write
    python Tools/scripts/bmak_damage.py --check     # re-derives, diffs JSON *and* the note
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
MD = os.path.join(ROOT, "Research", "BatmobileGrab", "DAMAGE_RULES.md")
# raw bytecode stays outside the notes folder, like the anim keys and bone face lists:
# the note carries offsets, symbols and sha1s, never the game's own bytes.
RAW = os.path.join(ROOT, "Working", "vendor", "BmAKgrab", "scripts")
CHAIN_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "CHAIN.json")
OFFSETS_JSON = os.path.join(ROOT, "Research", "BatmobileGrab", "OFFSETS.json")
SDK_DIR = os.path.join(ROOT, "Working", "vendor", "BmSDK")

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
# tokens whose operand is a 4-byte literal
LITERAL_TOKENS = {0x1D, 0x1E}
# tokens that carry no operand (one byte each) - recognised so the walk stays aligned and so a
# short body can be read out by name instead of quoted as bytes
BARE_TOKENS = {
    0x04: "EX_Return", 0x0B: "EX_Nothing", 0x15: "EX_EndParmValue",
    0x16: "EX_EndFunctionParms", 0x17: "EX_Self", 0x25: "EX_IntZero", 0x26: "EX_IntOne",
    0x27: "EX_True", 0x28: "EX_False", 0x2A: "EX_NoObject",
}
# a 5-byte `0x29 <property-ref>` block: the native-parameter descriptor a cooked native
# function keeps in place of bytecode
PARM_TOKEN = 0x29
# how many rejected (overlapping) candidates to keep per function; the count is always exact
MAX_REJECTED = 40
# how short a body must be for its whole token trace to go into the JSON
SHORT_BODY = 64

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

    # -------------------------------------------------------------- object helpers
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
        """Full path of the object that owns `index` (`Outer.Name`), or None."""
        try:
            return self.pkg.object_path(self.pkg.exports[index - 1]["outer_index"])
        except Exception:
            return None

    def script(self, index):
        data = self.pkg.data(index)
        return data[22:len(data) - 16] if len(data) >= 38 else b""

    def function_exports(self):
        return [i for i in range(1, self.pkg.export_count + 1)
                if self.pkg.object_class(i) == "Function"]

    # -------------------------------------------------------------- the token walk
    def walk(self, script, own=None):
        """One left-to-right, non-overlapping token scan of a function body.

        A candidate is accepted only if it starts at or after the end of the last accepted
        token.  This is what the previous byte-scan got wrong: it masked every byte inside a
        *candidate* window it had found anywhere, including windows that themselves started on
        the high zero byte of a reference index, so a literal that began inside such a phantom
        window (`1e 00 00 00 3f` after `00 a3 28 00 00`) disappeared.  Leftmost-wins removes
        that class of loss and keeps the rejected candidates visible.

        The scan is aligned but not a decoder: it does not resolve control flow, nested contexts
        or expression trees, and a byte that belongs to no recognised token is left unnamed.
        """
        limit = self.pkg.export_count
        imports = self.pkg.import_count
        refs, consts, rejected, tokens = [], [], [], []
        covered = bytearray(len(script))
        accepted_starts = set()
        m, end = 0, 0
        while m < len(script):
            tok = script[m]
            if tok in REF_TOKENS and m + 5 <= len(script):
                value = struct.unpack_from("<i", script, m + 1)[0]
                if 1 <= value <= limit or -imports <= value <= -1:
                    path = self.ref(value)
                    if path is not None:
                        refs.append({"at": m, "token": TOKENS[tok], "ref_index": value,
                                     "ref": path, "kind": self.obj_class(value),
                                     "local": bool(own) and path.split(".")[0] == own})
                        tokens.append({"at": m, "token": TOKENS[tok], "ref": path})
                        for k in range(m, m + 5):
                            covered[k] = 1
                        accepted_starts.add(m)
                        end = m + 5
                        m += 5
                        continue
            elif tok in LITERAL_TOKENS and m + 5 <= len(script):
                value = (struct.unpack_from("<f", script, m + 1)[0] if tok == 0x1E
                         else struct.unpack_from("<i", script, m + 1)[0])
                value = round(value, 6) if tok == 0x1E else value
                consts.append({"at": m, "kind": "float" if tok == 0x1E else "int",
                               "value": value})
                tokens.append({"at": m, "token": TOKENS[tok], "value": value})
                for k in range(m, m + 5):
                    covered[k] = 1
                accepted_starts.add(m)
                end = m + 5
                m += 5
                continue
            elif tok in BARE_TOKENS:
                tokens.append({"at": m, "token": BARE_TOKENS[tok]})
                covered[m] = 1
                accepted_starts.add(m)
                end = m + 1
                m += 1
                continue
            m += 1
        # Candidates that the walk did not accept because an earlier token owns their bytes.
        # This is exactly the noise the old trace reported as calls (a `0x00`-shaped index run
        # inside another operand); it is counted and sampled, never presented as a reference.
        unaligned = 0
        for m in range(len(script) - 4):
            if m in accepted_starts or script[m] not in REF_TOKENS:
                continue
            value = struct.unpack_from("<i", script, m + 1)[0]
            if not (1 <= value <= limit or -imports <= value <= -1):
                continue
            unaligned += 1
            if len(rejected) < MAX_REJECTED:
                rejected.append({"at": m, "token": TOKENS[script[m]], "ref": self.ref(value)})
        return {
            "refs": refs,
            "constants": consts,
            "unaligned_ref_candidates": unaligned,
            "unaligned_sample": rejected,
            "accepted_tokens": len(tokens),
            "bare_tokens": sum(1 for t in tokens if t["token"] in BARE_TOKENS.values()),
            "unparsed_tail_bytes": len(script) - end,
            "unexplained_bytes": covered.count(0),
            "short_trace": tokens if len(script) <= SHORT_BODY else None,
        }

    # -------------------------------------------------------------- one function
    def function(self, path):
        i = self.by_path.get(path)
        if i is None:
            return None
        data = self.pkg.data(i)
        if len(data) < 38:
            return {"path": path, "index": i, "size": len(data), "script": "",
                    "fields": {}}
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
        walk = self.walk(script, own=path.rsplit(".", 1)[-1])
        entry = {
            "path": path, "index": i, "size": len(data),
            "script_bytes": len(script), "script_sha1": hashlib.sha1(script).hexdigest(),
            "script_raw": os.path.join("Working", "vendor", "BmAKgrab", "scripts",
                                       path.replace(".", "_") + ".hex"),
            "fields": fields,
            "_script": script,
            "native_parm_descriptors": desc, "native_parm_bytes": desc_bytes,
            "refs": walk["refs"], "constants": walk["constants"],
            "walk": {k: v for k, v in walk.items() if k not in ("refs", "constants")},
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

        A one-byte `04` body is the thinnest native thunk in the package.
        `exec_strings_in_exe` is the independent second source, filled in by `main`.
        """
        n, covered = entry["native_parm_descriptors"], entry["native_parm_bytes"]
        length = len(entry["_script"])
        if length and covered >= length * 0.5:
            return "native"
        if entry["_script"] == b"\x04":
            return "native-thunk"
        return "script"


def path_of_class(path):
    """`Outer.Foo.Bar` -> `Outer.Foo` (the property's owner object)."""
    return path.rsplit(".", 1)[0] if "." in path else path


# --------------------------------------------------------------------- package stats
def package_stats(bm):
    """Counts the note quotes, so none of them is typed by hand (R11)."""
    pkg = bm.pkg
    funcs = bm.function_exports()
    one_byte = 0
    for i in funcs:
        script = bm.script(i)
        if len(script) == 1 and script[0] == 0x04:
            one_byte += 1
    return {
        "path": UPK,
        "bytes": os.path.getsize(UPK),
        "version": pkg.version,
        "licensee": pkg.licensee,
        "names": len(pkg.names),
        "imports": pkg.import_count,
        "exports": pkg.export_count,
        "function_exports": len(funcs),
        "one_byte_return_bodies": one_byte,
    }


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
    bad = []
    for p in TRACED:
        i = bm.by_path.get(p)
        if i is None:
            bad.append(p)
            continue
        data = bm.pkg.data(i)
        script = bm.script(i)
        if struct.unpack_from("<i", data, 18)[0] != len(script) + 1:
            bad.append(p)
    got["B_script_size_is_len_plus_one"] = not bad

    # C. The thinnest possible script is one byte, and that byte is EX_Return.
    thin = [i for i in bm.function_exports() if len(bm.script(i)) == 1]
    got["C_thinnest_script_is_return"] = bool(thin) and all(
        bm.script(i) == b"\x04" for i in thin[:500])

    # D. The trailing FName is the function's own name.
    names_ok = True
    for p in TRACED:
        i = bm.by_path.get(p)
        if i is None:
            names_ok = False
            continue
        data = bm.pkg.data(i)
        if bm.name(struct.unpack_from("<i", data, len(data) - 8)[0]) != p.rsplit(".", 1)[-1]:
            names_ok = False
    got["D_name_word_is_own_name"] = names_ok

    # E. Every EX_NativeParm descriptor points at a property of the function it sits in.
    ok = True
    for p in bm.by_path:
        script = bm.script(bm.by_path[p])
        if not script:
            continue
        if len(script) % 5 or any(script[i] != 0x29 for i in range(0, len(script), 5)):
            continue                      # not a descriptor-only script
        for i in range(0, len(script), 5):
            ref = struct.unpack_from("<i", script, i + 1)[0]
            if bm.outer_of(ref) != p:
                ok = False
    got["E_native_parm_refs_own_properties"] = ok

    # F. Corpus-wide: EX_FinalFunction is followed by a Function export (imports have no
    #    class in this package, so they are counted as hits too).
    hits = ok_f = 0
    for p in list(bm.by_path)[::7]:
        script = bm.script(bm.by_path[p])
        for m in range(len(script) - 4):
            if script[m] != 0x1C:
                continue
            ref = struct.unpack_from("<i", script, m + 1)[0]
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


# --------------------------------------------------------------------- regeneration
REGEN_WORD = re.compile(r"\b(\w*(?:Regen|Heal|Recover|Restore|Repair|Replenish)\w*)\b")
REGEN_ONLY = re.compile(r"Regen", re.I)
VEHICLE_CLASS = re.compile(r"^(?:RVehicle|Pawn|AkVehicle)")


def sdk_health_recover_rate():
    """Offset and declared type of `HealthRecoverRate`, read off the BmSDK dump."""
    path = os.path.join(SDK_DIR, "RVehicleBatmobileBase.g.cs")
    rel = os.path.relpath(path, ROOT)
    lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    prop_class, decl, offset, decl_line = None, None, None, None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("///") and "Property:" in stripped \
                and "HealthRecoverRate" in stripped:
            prop_class = stripped.split(":", 1)[0].replace("///", "").strip()
        if stripped.startswith("public") and "HealthRecoverRate" in stripped:
            decl = stripped
            decl_line = i + 1
            for j in range(i, min(i + 5, len(lines))):
                m = re.search(r"Ptr \+ (\d+)", lines[j])
                if m:
                    offset = int(m.group(1))
                    break
            break
    declared = None
    if decl:
        m = re.search(r"unsafe\s+(.+?)\s+HealthRecoverRate", decl)
        declared = m.group(1) if m else None
    return {"file": rel, "line": decl_line, "declaration": decl,
            "declared_type": declared, "property_class": prop_class, "offset": offset}


def regeneration(bm):
    """Who owns every Regen/Heal/Recover/Restore/Repair/Replenish symbol, in both sources.

    The answer to "does the Batmobile regenerate armour out of combat?" is read off this block;
    the previous pass counted names without their owner, which made the per-class negation
    unprovable (`bRegenerateChildren` is a top-level BmGame name and belongs to a crowd spawner).
    """
    pkg = bm.pkg
    kids = collections.defaultdict(list)
    for i, e in enumerate(pkg.exports, 1):
        kids[e["outer_index"]].append(i)

    sdk = collections.defaultdict(set)
    for file in sorted(os.listdir(SDK_DIR)):
        if not file.endswith(".cs"):
            continue
        text = open(os.path.join(SDK_DIR, file), encoding="utf-8", errors="replace").read()
        owner = file[:-5] if file.endswith(".g.cs") else file[:-3]
        for m in REGEN_WORD.finditer(text):
            sdk[m.group(1)].add(owner)

    regen_owners = collections.defaultdict(list)
    for e in pkg.exports:
        if REGEN_ONLY.search(e["name"]):
            regen_owners[e["name"]].append([pkg.object_name(e["outer_index"]) or "UNKNOWN",
                                            pkg.class_name(e["class_index"]) or "UNKNOWN"])

    classes = [(i, e["name"]) for i, e in enumerate(pkg.exports, 1) if e["class_index"] == 0]
    vehicle_classes = [(i, n) for i, n in classes if VEHICLE_CLASS.match(n)]
    members = []
    for i, cls in vehicle_classes:
        for c in kids.get(i, []):
            ce = pkg.exports[c - 1]
            if REGEN_WORD.search(ce["name"]):
                members.append({"class": cls, "member": ce["name"],
                                "kind": pkg.class_name(ce["class_index"]) or "UNKNOWN"})
    members.sort(key=lambda r: (r["class"], r["member"]))

    chain_text = open(CHAIN_JSON, encoding="utf-8").read()
    offsets = json.load(open(OFFSETS_JSON, encoding="utf-8"))["fields"]
    offsets_names = [f.get("name") if isinstance(f, dict) else f for f in offsets]
    hrr = "HealthRecoverRate"
    return {
        "bm_sdk_symbols": {k: sorted(v) for k, v in sorted(sdk.items())},
        "bmgame_names": sorted({n for n in pkg.names
                                if isinstance(n, str) and REGEN_WORD.search(n)}),
        "bmgame_regen_owners": {k: v for k, v in sorted(regen_owners.items())},
        "vehicle_family": {
            "class_pattern": VEHICLE_CLASS.pattern,
            "classes": len(vehicle_classes),
            "members": members,
            "regen_members": [m for m in members if REGEN_ONLY.search(m["member"])],
        },
        "health_recover_rate": {
            "sdk": sdk_health_recover_rate(),
            "chain_mentions": chain_text.count(hrr),
            "offsets_total": len(offsets_names),
            "offsets_rows": sum(1 for n in offsets_names if n and hrr in n),
        },
    }


# --------------------------------------------------------------------- readers
REF_FIELDS = [
    "RVehicleBatmobileBase.HealthRecoverRate",
    "RVehicleBatmobileBase.ArmourModeDamageReduction",
    "RVehicleBatmobileBase.LowHealthWarningLevel",
    "RVehicleBatmobileBase.WeaponGeneratorPower",
    "RVehicleBatmobileBase.ArmouredMode",
]


def field_references(bm, names=REF_FIELDS):
    """Which script functions reference each damage field - as a token, not as four bytes.

    `read_by` used to be a raw 4-byte containment test, which counts any byte run that ends in
    the field's index (41 "readers" of `ArmouredMode` where 30 tokens exist).  Both numbers are
    kept: `read_by` is the token-aligned list, `containment_only` the names the old test added.
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
    funcs = bm.function_exports()
    out = {}
    for p in names:
        out[p] = {"export": props.get(p), "read_by": [], "containment_only": [],
                  "containment_count": 0}
    for p, index in props.items():
        packed = struct.pack("<i", index)
        contained, aligned = [], []
        for f in funcs:
            data = bm.pkg.data(f)
            if len(data) < 38:
                continue
            script = data[22:len(data) - 16]
            if packed not in script:
                continue
            path = bm.pkg.object_path(f)
            contained.append(path)
            walk = bm.walk(script, own=path.rsplit(".", 1)[-1])
            if any(r["ref_index"] == index for r in walk["refs"]):
                aligned.append(path)
        out[p]["read_by"] = sorted(aligned)
        out[p]["containment_only"] = sorted(set(contained) - set(aligned))
        out[p]["containment_count"] = len(contained)
    return out


# --------------------------------------------------------------------- values
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
    for path in funcs:
        i = next((k for k in range(1, pkg.export_count + 1)
                  if pkg.object_path(k) == path), None)
        data = pkg.data(i)
        script = data[22:len(data) - 16]
        with open(os.path.join(RAW, path.replace(".", "_") + ".hex"), "w",
                  encoding="ascii") as fh:
            fh.write(script.hex(" ") + "\n")


# ===================================================================== the note
def fmt(v):
    """A CHAIN value: integers keep no decimal tail, fractions keep six significant digits."""
    if v is None:
        return "\u2014"
    if isinstance(v, bool):
        return str(v).lower()
    if isinstance(v, float):
        if v == int(v):
            return str(int(v))
        return "%.6g" % v
    return str(v)


def flit(v):
    """A bytecode literal: always shown as a float, so `2.0` does not read as the int 2."""
    if isinstance(v, float):
        text = "%.6g" % v
        if "." not in text and "e" not in text:
            text += ".0"
        return text
    return str(v)


def short(path):
    return path.rsplit(".", 1)[-1]


def table(header, rows, align=None):
    """Markdown table; `align` is a list of '---', '---:' or ':---' per column."""
    align = align or ["---"] * len(header)
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return out


class Render:
    """Renders DAMAGE_RULES.md from the JSON record.

    Prose may only name a member that the trace actually carries: `need()` raises otherwise, so
    a narrative claim cannot outlive its evidence (the fault the review found in `§3.3`/`§3.5`).
    """

    def __init__(self, doc):
        self.d = doc
        self.f = doc["functions"]
        self.values = {(r["class"], r["archetype"], r["name"]): r
                       for r in doc["damage_values"]}

    # -- helpers --------------------------------------------------------------
    def fun(self, path):
        return self.f[path]

    def need(self, path, names):
        have = {r["ref"] for r in self.f[path]["refs"]}
        missing = [n for n in names if n not in have]
        if missing:
            raise SystemExit("G1-14 render invariant: %s no longer references %s"
                             % (short(path), ", ".join(missing)))
        return ", ".join("`%s`" % short(n) for n in names)

    def value(self, cls, archetype, field):
        row = self.values.get((cls, archetype, field))
        return row["value"] if row else None

    def literals(self, path):
        return [c["value"] for c in self.f[path]["constants"]]

    def lit_summary(self, path):
        vals = self.literals(path)
        if not vals:
            return "none"
        return "**%d** found, distinct %s" % (
            len(vals), ", ".join("`%s`" % flit(v) for v in sorted(set(vals))))

    def lit_text(self, path, distinct=False):
        vals = self.literals(path)
        if distinct:
            vals = sorted(set(vals))
        if not vals:
            return "none"
        return ", ".join("`%s`" % flit(v) for v in vals)

    def readers(self, name):
        return self.d["field_references"][name]["read_by"]

    def projectile_rows(self):
        rows = [r for r in self.d["damage_values"]
                if r["class"] in ("RBasicProjectile", "RBatmobileMissile")]
        archetypes = sorted({r["archetype"] for r in rows})
        return rows, archetypes

    # -- sections -------------------------------------------------------------
    def build(self):
        d, ps = self.d, self.d["package_stats"]
        L = []
        A = L.append
        anchors = d["anchors"]
        n_true = sum(1 for v in anchors.values() if v)
        A("# Damage rules, health, armour, regeneration (G1-14)")
        A("")
        A("The Arkham Knight Batmobile's damage model, read out of `BmGame.upk` "
          "(%s B; %s names /" % (format(ps["bytes"], ","), format(ps["names"], ",")))
        A("%s imports / %s exports, of which **%s** are `Function`) with the class dump"
          % (format(ps["imports"], ","), format(ps["exports"], ","),
             format(ps["function_exports"], ",")))
        A("(`Working/vendor/BmSDK`) and the archetype tag chain "
          "(`Research/BatmobileGrab/CHAIN.json`).")
        A("")
        A("Two things had to be recovered before any of it was readable, and both are recorded in")
        A("\u00a71: the `Function` export layout (UEViewer stops parsing this class early, so the")
        A("script bodies past that point have never been read from this package), and a")
        A("native/script test that does not depend on anybody's guess.")
        A("")
        A("**This note is generated.** `Tools/scripts/bmak_damage.py --write` renders it from")
        A("`DAMAGE_RULES.json`; `--check` re-derives that JSON, re-renders this file and diffs both,")
        A("so a hand edit to either fails the check (R11: no typed number). Every count, table row")
        A("and literal list below is read from the record. The extracted bytecode itself lives")
        A("outside this folder, in `Working/vendor/BmAKgrab/scripts/` - this note carries offsets,")
        A("symbols, constants and sha1s only.")
        A("")
        A("---")
        A("")
        # ---------------------------------------------------------------- §1
        A("## 1. The `Function` export layout, recovered")
        A("")
        A("`BmGame.upk` is UE3 (version %s / licensee %s) and a `Function` export carries **no"
          % (ps["version"], ps["licensee"]))
        A("Batman property tags** - it is positional. Reading it from byte 0 of the export:")
        A("")
        layout = d["function_export_layout"]
        L.extend(table(
            ["bytes", "field", "note"],
            [["`u16`", "prefix", "constant `0` on every `Function` export"],
             ["`i32` @%d" % layout["next"], "`Next`", "`UField` sibling link"],
             ["`i32` @%d" % layout["super"], "`SuperField`",
              "super function, `0` when the class declares it"],
             ["`i32` @%d" % layout["children"], "`Children`",
              "first child property (the first parameter)"],
             ["`i32` @%d" % layout["line"], "`Line`", "editor line of the source"],
             ["`i32` @%d" % layout["script_size_field"], "`ScriptSize`",
              "== `len(script) + 1`"],
             ["`byte[]` @%d" % layout["script"], "`Script`",
              "`len(export) - 38` bytes of executable bytecode"],
             ["`i32` @size-16", "flags word", ""],
             ["`i32` @size-12", "pre-name word", "always `0x0002xxxx`"],
             ["`i32` @size-8", "name `FName` index", "the function's own name"],
             ["`i32` @size-4", "name number", "always `0`"]],
            ["---", "---", "---"]))
        A("")
        A("UEViewer knows only the first four fields: `Unreal/UnTypeinfo.h` handles `GAME_Batman4`")
        A("with `Ar << Children; return;   //!! remaining data will be dropped anyway`, so the")
        A("script bytes from offset 22 onwards were unclaimed until this pass.")
        A("")
        A("**Anchors** (re-derived by `--check` on every run; %d of %d hold):" % (n_true, len(anchors)))
        A("")
        A("| anchor | holds | what it proves |")
        A("|---|---|---|")
        for key, text in ANCHOR_TEXT.items():
            if key not in anchors:
                raise SystemExit("G1-14 render invariant: anchor %s is gone" % key)
            A("| `%s` | `%s` | %s |" % (key, str(anchors[key]).lower(), text))
        A("")
        A("Token numbering is the one UE3 and UE4 share (`EX_Return`=0x04, `EX_Let`=0x0F,")
        A("`EX_Context`=0x19, `EX_VirtualFunction`=0x1B, `EX_FinalFunction`=0x1C,")
        A("`EX_IntConst`=0x1D, `EX_FloatConst`=0x1E, `EX_DynamicCast`=0x2E).")
        A("")
        # ---------------------------------------------------------------- §2
        A("## 2. Native or script: the entry points, decided")
        A("")
        A("A cooked **native** function keeps its parameter list as `0x29 <own-property ref>`")
        A("descriptors (five bytes each) in place of bytecode; a **script** function has a statement")
        A("body. Two independent sources are recorded per row: the body itself, and the executable's")
        A("own `exec<Name>` registration string in `BatmanAK.exe`.")
        A("")
        rows = []
        for p in TRACED:
            f = self.fun(p)
            rows.append([("`%s`" % p), format(f["size"], ","),
                         format(f["script_bytes"], ","), f["native_parm_descriptors"],
                         f["exec_strings_in_exe"], "**%s**" % f["verdict"]])
        L.extend(table(["function", "export B", "body B", "parm descs", "`exec<>` in exe",
                        "verdict"], rows, ["---", "---:", "---:", "---:", "---:", "---"]))
        A("")
        n_native = sum(1 for p in TRACED if self.fun(p)["verdict"] != "script")
        A("Verdict counts, read from the record: **%d native / %d script** of %d traced entry"
          % (n_native, len(TRACED) - n_native, len(TRACED)))
        A("points. The `exec<>` count for `TakeDamage` is %d and does not make *this* override native:"
          % self.fun("RVehicleBatmobileBase.TakeDamage")["exec_strings_in_exe"])
        A("those strings belong to parent registrations. The body decides, and the two sources only")
        A("ever disagree where the body is a stub - they do not.")
        A("")
        # ---------------------------------------------------------------- §3
        A("## 3. The rule: damage type \u2192 entry \u2192 what scales it \u2192 mode")
        A("")
        td = "RVehicleBatmobileBase.TakeDamage"
        f_td = self.fun(td)
        A("### 3.1 Direct incoming damage - `TakeDamage` (script, %s B)" % format(f_td["script_bytes"], ","))
        A("")
        A("Aligned reference trace in byte order: %d references, %d distinct, listed with their"
          % (len(f_td["refs"]), len({r["ref"] for r in f_td["refs"]})))
        A("offsets in `DAMAGE_RULES.json \u2192 functions.*.refs`. Reading the byte order:")
        A("")
        A("1. %s and %s gate the hit (cinematic mode returns early - no damage taken while the"
          % (self.need(td, ["RPlayerControllerBase.InCinematicMode"]),
             self.need(td, ["RVehicle.SelfDriveMode"])))
        A("   camera is scripted).")
        n_amdr = len(self.readers("RVehicleBatmobileBase.ArmourModeDamageReduction"))
        A("2. **`ArmouredMode` \u2192 `ArmourModeDamageReduction`** - **%d** script function%s in the"
          % (n_amdr, "" if n_amdr == 1 else "s"))
        A("   whole package read%s that field, and this body is %s. The shipped archetype value is"
          % ("s" if n_amdr == 1 else "", "it" if n_amdr == 1 else "one of them"))
        A("   **`%s`** (`CHAIN.json`), so armoured/battle mode reduces incoming damage by *nothing* as"
          % fmt(self.value("RVehicleBatmobile", "Playable_Batmobile_SF.Batmobile",
                           "RVehicleBatmobileBase.ArmourModeDamageReduction")))
        A("   shipped.")
        A("3. %s - native, %d parameters; the encounter layer scales the hit."
          % (self.need(td, ["RVehicleCombatManager.GetDamageMod"]),
             self.fun("RVehicleCombatManager.GetDamageMod")["native_parm_descriptors"]))
        A("4. Cosmetic/state response: %s"
          % self.need(td, ["RVehicle.UnStickTyres", "RPlayerController.AddScreenShake"]))
        A("   with `ExplosiveImpactScreenShake`, `ExplosiveImpactSound`.")
        A("5. Counters: %s, each followed by"
          % self.need(td, ["RPlayerController.NumBatmobileMissileHits",
                           "RPlayerController.NumBatmobileCannonHits"]))
        A("   `%s`." % short("RPersistentData.AutoActivateTutorial"))
        self.need(td, ["RPersistentData.AutoActivateTutorial"])
        A("6. Source-specific branches: casts of `DamageCauser` to %s, %s and %s,"
          % (self.need(td, ["RProjectile"]), self.need(td, ["RTankMissile"]),
             self.need(td, ["RVehicleHeavyTank"])))
        A("   the `Cloudburst` flag %s, the beacon type %s;"
          % (self.need(td, ["RVehicleCombatManager.bDamagedByCloudburstTank"]),
             self.need(td, ["RCommandBeaconBase"])))
        A("   %s is stored." % self.need(td, ["RPlayerController.LastDamageType"]))
        A("7. **The weapon generator is drained here** - the body references")
        A("   %s, then %s and"
          % (self.need(td, ["RVehicleBatmobileBase.DrainWeaponGeneratorForDamage"]),
             self.need(td, ["RVehicleBatmobileBase.bEmergencyWeaponGenerator"])))
        A("   %s (that function is decoded in \u00a74)."
          % self.need(td, ["RVehicleBatmobileBase.WeaponGeneratorPower"]))
        A("8. Thresholds: %s \u2192"
          % self.need(td, ["TakeDamage.QuarterHealth", "RVehicleBatmobileBase.LowHealthWarningLevel"]))
        A("   %s, %s, %s,"
          % (self.need(td, ["RHudModuleStoryMode.SetOneShotWarningMessage"]),
             self.need(td, ["RVehicleCombatManager.PlayCommanderBark"]),
             self.need(td, ["RVehicleBatmobileBase.DisableUnderAttackWarning"])))
        A("   %s." % self.need(td, ["RVehicleBatmobileBase.bIsJokerfiedBatmobile"]))
        A("")
        A("Body literals, from the same walk: %s." % self.lit_summary(td))
        A("")
        # --- 3.2
        tw = "RVehicleBatmobileBase.TakeRadiusDamageFromWeapon"
        f_tw = self.fun(tw)
        A("### 3.2 Radial / explosion incoming - `TakeRadiusDamageFromWeapon` (script, %s B)"
          % f_tw["script_bytes"])
        A("")
        A("Calls the **native** %s first (that gate's body is %d parameter descriptor%s, so"
          % (self.need(tw, ["RVehicleBatmobileBase.ShouldRadialDamageHit"]),
             self.fun("RVehicleBatmobileBase.ShouldRadialDamageHit")["native_parm_descriptors"],
             "" if self.fun("RVehicleBatmobileBase.ShouldRadialDamageHit")[
                 "native_parm_descriptors"] == 1 else "s"))
        A("*whether* a radial hit lands is decided in `BatmanAK.exe` and is not readable from script),")
        A("then computes a distance falloff from")
        A("%s and `DamageFalloffExponent` with the"
          % self.need(tw, ["TakeRadiusDamageFromWeapon.Dist", "TakeRadiusDamageFromWeapon.ColRadius",
                           "TakeRadiusDamageFromWeapon.ColHeight", "TakeRadiusDamageFromWeapon.Dir"]))
        A("body literals **%s**, clamps the result into"
          % ", ".join("`%s`" % flit(v) for v in sorted(set(self.literals(tw)))))
        A("`Reduce`, and pushes the parameter set")
        A("(%s) into the imported"
          % self.need(tw, ["TakeRadiusDamageFromWeapon.InstigatedBy",
                           "TakeRadiusDamageFromWeapon.BaseDamage",
                           "TakeRadiusDamageFromWeapon.DamageRadius",
                           "TakeRadiusDamageFromWeapon.DamageType",
                           "TakeRadiusDamageFromWeapon.Momentum",
                           "TakeRadiusDamageFromWeapon.HurtOrigin",
                           "TakeRadiusDamageFromWeapon.DamageCauser"]))
        A("`Core.TakeRadiusDamageFromWeapon` (import ref %d). **No token in this body references"
          % self.import_ref(tw, "Core.TakeRadiusDamageFromWeapon"))
        A("the script `TakeDamage`**: the hand-off to the override above is engine-side, so that")
        A("step is UNKNOWN. The engine call is recorded as an import reference, which the old trace")
        A("dropped.")
        fnrefs = [r for r in f_tw["refs"] if r["kind"] == "Function"]
        A("The body carries **%d** aligned function references (%s); this section explains the two"
          % (len(fnrefs), ", ".join("`%s`@%d" % (short(r["ref"]), r["at"]) for r in fnrefs)))
        A("engine-side ones above and builds no claim on the rest (§7: aligned is a candidate,")
        A("not a call).")
        A("")
        # --- 3.3
        ca = "RVehicleBatmobileBase.CalculateAndStoreImpactDamage"
        f_ca = self.fun(ca)
        A("### 3.3 Ram / collision - **outgoing** (matches T-DM7 \u2192 `out`)")
        A("")
        A("`CalculateAndStoreImpactDamage` (script, %s B) reads only the vehicle's own fields, and"
          % format(f_ca["script_bytes"], ","))
        A("every one of them is an *outgoing* multiplier. Values from `CHAIN.json`, presence from")
        A("this body's aligned trace:")
        A("")
        bats = ["Playable_Batmobile_SF.Batmobile", "Playable_BatmobileJoker_SF.JokersBatmobile"]
        impact = sorted({short(r["ref"]) for r in f_ca["refs"]
                         if r["ref"].startswith("RVehicleBatmobileBase.")
                         and "Impact" in short(r["ref"])})
        rows = []
        for field in impact:
            v1 = self.value("RVehicleBatmobile", bats[0], "RVehicleBatmobileBase." + field)
            v2 = self.value("RVehicleBatmobile", bats[1], "RVehicleBatmobileBase." + field)
            rows.append(["`%s`" % field, fmt(v1), fmt(v2)])
        L.extend(table(["field", "shipped (`%s`)" % short(bats[0]),
                        "Joker (`%s`)" % short(bats[1])], rows,
                       ["---", "---:", "---:"]))
        A("")
        A("Every field in that table is in this body's trace (%d distinct class fields match"
          % len(impact))
        A("`*Impact*`). A `\u2014` in a value column means no archetype tag carries the field: its")
        A("shipped number is whatever the native CDO holds - UNKNOWN from the files.")
        A("")
        A("The body also reads %s,"
          % self.need(ca, ["RVehicleSimBatmobile.bBoosting", "RVehicle.HeavyArmouredVehicle"]))
        A("%s and the floating %s UI."
          % (self.need(ca, ["RVehicleBatmobileBase.CurrentStrafeCooldown",
                            "RVehicleBatmobileBase.StrafeCooldown"]),
             self.need(ca, ["RVehicleBatmobileBase.DamageNumbers"])))
        A("It branches on %s and, on a car, calls %s; it also gates on %s."
          % (self.need(ca, ["RVehicle.bHasAPCStyleWeakSpot"]),
             self.need(ca, ["RVehicleCar.RemoveWeakSpot"]),
             self.need(ca, ["RGameInfo.IsChallengeMode"])))
        gate = "RVehicleBatmobileBase.CanBatmobileDoImpactDamage"
        gate_in_body = any(r["ref"] == gate for r in f_ca["refs"])
        A("The gate `%s(OtherVehicle)` is native (%d descriptor%s, %d `exec<>` string%s)."
          % (short(gate),
             self.fun(gate)["native_parm_descriptors"],
             "" if self.fun(gate)["native_parm_descriptors"] == 1 else "s",
             self.fun(gate)["exec_strings_in_exe"],
             "" if self.fun(gate)["exec_strings_in_exe"] == 1 else "s"))
        A("This body %s that gate, so whether the impact is allowed at all is decided"
          % ("does reference" if gate_in_body else "does **not** reference"))
        A("elsewhere - UNKNOWN from here.")
        A("")
        A("#### 3.3.1 Sideswipe - the targeting half (noted 2026-10-26)")
        A("")
        A("The block above decides *how much* damage a hit deals. What decides *which* car is hit is")
        A("a second, runtime mechanism on the same class, and it is why no archetype value exists")
        A("for it:")
        A("")
        L.extend(table(["member", "type", "role"], [
            ["`SideSwipeTargetsList`", "`RInteractionClass`", "the candidate set a sideswipe picks from"],
            ["`SideSwipeInSweetSpot`", "`bool`", "true on the frames the hit lands in the sweet spot"],
            ["`GetSideSwipeTarget(Targets, Direction, out Distance)`", "function",
             "picks a target for a direction"],
            ["`GetCurrentSideSwipeTarget()`", "function", "the target currently held"],
            ["`GetBatmobileDodgeDirection(Target)`", "function", "the dodge direction for that target"],
            ["`CrushedThisFrame` / `BouncedThisFrame`", "`bool`", "per-frame contact state"],
        ]))
        A("")
        A("`OFFSETS.json` carries **%d** rows for any of these: they are runtime state and script"
          % self.d["sideswipe_offsets"])
        A("functions, not serialised defaults. So the numbers for a ram are the ones in the table")
        A("above, while *choosing* the victim and landing in the sweet spot is native and not")
        A("readable from the files.")
        A("")
        A("In play the Batmobile does sideswipe traffic and ram it (user, 2026-10-26). The behaviour")
        A("is therefore real and the outgoing numbers are decoded; T-DM7 still routes the damage")
        A("itself to JC3's own collision response (`out`), and that translation decision is untouched")
        A("by this note.")
        A("")
        # --- 3.4
        ram = "RVehicleBatmobileBase.TakesDamageFromRam"
        f_ram = self.fun(ram)
        trace = f_ram["walk"]["short_trace"] or []
        head = ", ".join("%s@%d" % (t["token"], t["at"]) for t in trace)
        tail = f_ram["walk"]["unparsed_tail_bytes"]
        A("### 3.4 Ram - **incoming**, and unconditional")
        A("")
        A("`TakesDamageFromRam(Target, RamSpeed)` is a **script** function whose whole body is %d"
          % f_ram["script_bytes"])
        A("bytes (sha1 `%s`). The walk finds %s and then **%d trailing byte%s that do not form a"
          % (f_ram["script_sha1"], head if head else "no recognised token", tail, "" if tail == 1 else "s"))
        A("complete descriptor**. The first two tokens read as `return true`; what the tail does is")
        A("**UNKNOWN** - it is not a property reference (the body's aligned refs are %d) and not a"
          % len(f_ram["refs"]))
        A("literal (constants: %d), so the earlier reading of it as \"a read of the function's own"
          % len(f_ram["constants"]))
        A("ReturnValue slot\" was not supported by the trace and is withdrawn.")
        A("")
        A("**`return true`, with no condition and no field read.** So the postmortem's statement that")
        A("\"there is no incoming-impact entry point on the class\" is too strong: the entry point")
        A("exists and is open. Whatever makes ramming survivable, it is not this function, and no")
        A("archetype value can switch it off from here. How the tail is executed is UNKNOWN.")
        A("")
        # --- 3.5
        rows, archetypes = self.projectile_rows()
        fields = ["Projectile.Damage", "Projectile.DamageRadius", "Projectile.MyDamageType",
                  "RBasicProjectile.TurretShotDamage"]
        A("### 3.5 Outgoing weapon damage - archetypes, not rules")
        A("")
        A("Every projectile archetype that carries a damage-related tag, rendered from the **%d**"
          % len(self.d["damage_values"]))
        A("damage rows in `DAMAGE_RULES.json`:")
        A("")
        rowsout = []
        for arch in archetypes:
            cells = []
            for field in fields:
                v = self.value("RBasicProjectile", arch, field)
                if v is None:
                    v = self.value("RBatmobileMissile", arch, field)
                cells.append(fmt(v))
            rowsout.append(["`%s`" % arch.split(".", 1)[0],
                            "`%s`" % arch.split(".", 1)[1]] + cells)
        L.extend(table(["package", "archetype"] + ["`%s`" % f.split(".")[-1] for f in fields],
                       rowsout, ["---", "---"] + ["---:"] * len(fields)))
        A("")
        empty = [a.split(".", 1)[1] for a in archetypes
                 if all(self.value("RBasicProjectile", a, f) is None
                        and self.value("RBatmobileMissile", a, f) is None for f in fields)]
        if empty:
            A("An all-`\u2014` row is an archetype that carries none of these four tags; %d do"
              % len(empty))
            A("not (%s). They are in the record for their" % ", ".join("`%s`" % e for e in empty))
            A("`RProjectile.Impact*` object references only.")
        else:
            A("Every archetype in the table carries at least one of these four tags.")
        with_mdt = [a for a in archetypes
                    if self.value("RBasicProjectile", a, "Projectile.MyDamageType") is not None
                    or self.value("RBatmobileMissile", a, "Projectile.MyDamageType") is not None]
        A("**`Projectile.MyDamageType` is not on every projectile:** %d of the %d archetypes carry"
          % (len(with_mdt), len(archetypes)))
        A("it (an import reference, e.g. `-104`, `-113`, `-121`), and %d do not:"
          % (len(archetypes) - len(with_mdt)))
        A("")
        for a in archetypes:
            if a not in with_mdt:
                A("- `%s` (`%s` package)" % (a.split(".", 1)[1], a.split(".", 1)[0]))
        A("")
        A("For those %d the per-type multiplier is absent from the archetype as well. The damage"
          % (len(archetypes) - len(with_mdt)))
        A("class of every projectile that does carry `MyDamageType` lives in that class, not in the")
        A("vehicle.")
        A("")
        A("Read the missiles by name, not by family: `Batmobile_Missile_Projectile` is **%s** and"
          % fmt(self.value("RBatmobileMissile", "Playable_Batmobile_SF.Batmobile_Missile_Projectile",
                           "Projectile.Damage")))
        A("`Batmobile_EMPMissile_Projectile` is **%s**; the Joker missile is **%s**."
          % (fmt(self.value("RBatmobileMissile",
                            "Playable_Batmobile_SF.Batmobile_EMPMissile_Projectile",
                            "Projectile.Damage")),
             fmt(self.value("RBatmobileMissile",
                            "Playable_BatmobileJoker_SF.Batmobile_JokerMissile_Projectile",
                            "Projectile.Damage"))))
        A("The EMP missile is the outlier on the low side, not a second missile class.")
        A("")
        # --- 3.6
        A("### 3.6 Summary table")
        A("")
        L.extend(table(["damage type", "entry point", "what scales it", "mode"], [
            ["direct hit (bullet, shell, melee)", "`TakeDamage` (script)",
             "`GetDamageMod` (native, encounter) \u00d7 `ArmourModeDamageReduction` (ships **%s**), "
             "after the weapon-generator pool absorbs it" % fmt(
                 self.value("RVehicleBatmobile", bats[0],
                            "RVehicleBatmobileBase.ArmourModeDamageReduction")),
             "armoured/battle mode is the only mode gate"],
            ["radial / explosive", "`TakeRadiusDamageFromWeapon` (script)",
             "native `ShouldRadialDamageHit` gate, then distance falloff (%s)"
             % " / ".join(flit(v) for v in sorted(set(self.literals(tw)))),
             "any"],
            ["ram into the Batmobile", "`TakesDamageFromRam` (script)",
             "**none - `return true`**; the body's tail is UNKNOWN", "none"],
            ["ram by the Batmobile",
             "`CanBatmobileDoImpactDamage` (native) + `CalculateAndStoreImpactDamage` (script)",
             "speed band %s\u2192%s (%s\u2192%s battle), `ImpactStrafeMod` \u00d7%s, "
             "`ImpactBoostMod` \u00d7%s, civilian mod, weak-spot removal"
             % (fmt(self.value("RVehicleBatmobile", bats[0], "RVehicleBatmobileBase.ImpactMinDamageSpeed")),
                fmt(self.value("RVehicleBatmobile", bats[0], "RVehicleBatmobileBase.ImpactMaxDamageSpeed")),
                fmt(self.value("RVehicleBatmobile", bats[0],
                               "RVehicleBatmobileBase.BattleModeImpactMinDamageSpeed")),
                fmt(self.value("RVehicleBatmobile", bats[0],
                               "RVehicleBatmobileBase.BattleModeImpactMaxDamageSpeed")),
                fmt(self.value("RVehicleBatmobile", bats[0], "RVehicleBatmobileBase.ImpactStrafeMod")),
                fmt(self.value("RVehicleBatmobile", bats[0], "RVehicleBatmobileBase.ImpactBoostMod"))),
             "pursuit vs battle"],
            ["weapons fired", "projectile archetypes (\u00a73.5)",
             "per-archetype `Projectile.Damage` / `TurretShotDamage` / `DamageRadius`; "
             "no rule in this class", "per weapon"],
            ["cinematic", "`TakeDamage` early-out", "\u2014", "`InCinematicMode`"],
        ]))
        A("")
        # ---------------------------------------------------------------- §4
        A("## 4. Health, the weapon generator, and the numbers")
        A("")
        health_rows = [r for r in self.d["damage_values"]
                       if r["class"] == "RVehicleBatmobile" and r["name"] == "Pawn.Health"]
        health_vals = sorted({r["value"] for r in health_rows})
        if len(health_vals) != 1:
            raise SystemExit("G1-14 render invariant: Pawn.Health is no longer one value")
        A("- **`Pawn.Health` = %s** on all **%d** Batmobile archetypes (%s)."
          % (fmt(health_vals[0]), len(health_rows),
             ", ".join("`%s`" % r["archetype"].split(".", 1)[1] for r in health_rows)))
        lh = "RVehicleBatmobileBase.LoadHealth"
        A("- **Persisted**: `%s` (script, %s B) reads" % (short(lh), self.fun(lh)["script_bytes"]))
        A("  %s and" % self.need(lh, ["RPersistentData.BatmobileHealth",
                                      "RPersistentData.BatmobileEnergy"]))
        A("  %s - Batmobile health and energy are"
          % self.need(lh, ["RGameRI.PersistentOptions", "RPersistentOptions.DDA_DeathsInRoom"]))
        A("  saved, and **dynamic difficulty reads the death count in the room** before deciding")
        A("  them. Body literals: %s." % self.lit_text(lh))
        dw = "RVehicleBatmobileBase.DrainWeaponGeneratorForDamage"
        A("- **The weapon generator is the shield**: `TakeDamage` calls")
        A("  `DrainWeaponGeneratorForDamage(DamageAmount, HitNumber)` (script, %s B), which reads"
          % self.fun(dw)["script_bytes"])
        A("  %s, with body literals"
          % self.need(dw, ["RVehicleBatmobileBase.WeaponGeneratorPower",
                           "RVehicleBatmobileBase.bWeaponGeneratorShielding",
                           "RVehicleBatmobileBase.WeaponUnavailableReason",
                           "RVehicleBatmobileBase.bIsJokerfiedBatmobile",
                           "RGameInfo.GetDifficulty"]))
        A("  %s, and ends in `IncSteamEffect` + %s."
          % (self.lit_summary(dw), self.need(dw, ["RBatmobileCannon.OverHeat"])))
        wgp = self.d["field_references"]["RVehicleBatmobileBase.WeaponGeneratorPower"]
        A("  `WeaponGeneratorPower` is read by **%d** script functions in total (%s)."
          % (len(wgp["read_by"]),
             "the same count the old four-byte test gave"
             if wgp["containment_count"] == len(wgp["read_by"])
             else "%d by the old four-byte test" % wgp["containment_count"]))
        gm = "RVehicleBatmobileBase.GiveMaxEnergy"
        A("- **`GiveMaxEnergy`** (%d B) reads %s and %s"
          % (self.fun(gm)["script_bytes"],
             self.need(gm, ["RVehicleBatmobileBase.WeaponGeneratorPower"]),
             self.need(gm, ["RVehicleBatmobileBase.MaxWeaponGeneratorPower"])))
        A("  - the three members of the assignment are in the body: %s."
          % self.need(gm, ["RVehicleBatmobileBase.WeaponGeneratorPower",
                           "RVehicleBatmobileBase.MaxWeaponGeneratorPower",
                           "RVehicleBatmobileBase.CurrentGeneratorLevel"]))
        A("- **`QuarterHealth` / `LowHealthWarningLevel`** drive the low-health HUD warning")
        A("  (`%s`); `LowHealthWarningLevel` has exactly **%d** reader in the whole package -"
          % (short("RHudModuleStoryMode.SetOneShotWarningMessage"),
             len(self.readers("RVehicleBatmobileBase.LowHealthWarningLevel"))))
        A("  %s." % ", ".join("`%s`" % short(r) for r in
                             self.readers("RVehicleBatmobileBase.LowHealthWarningLevel")))
        om = "RVehicleBatmobileBase.OnModifyHealth"
        A("- **`OnModifyHealth`** (%d B) takes an `Action`, casts the PC and calls"
          % self.fun(om)["script_bytes"])
        A("  %s - that is the **Batsuit** bar (`HUD.md`), not the car's."
          % self.need(om, ["RPlayerController.InstantUpdateHealth"]))
        A("")
        # ---------------------------------------------------------------- §5
        reg = self.d["regeneration"]
        hrr = reg["health_recover_rate"]
        fam = reg["vehicle_family"]
        ea = "RVehicleBatmobileBase.ExperienceAwarded"
        A("## 5. Regeneration - answered: a mechanism exists, its value does not ship")
        A("")
        A("`ARM-5` asked whether BmAK has a regen value. It does, and it is **not** a passive timer:")
        A("")
        A("- `RVehicleBatmobileBase.HealthRecoverRate` is a **`%s` at +%s** in the class dump"
          % ((hrr["sdk"]["declared_type"] or "UNKNOWN").replace("BmSDK.", ""),
             hrr["sdk"]["offset"] if hrr["sdk"]["offset"] is not None else "UNKNOWN"))
        A("  (`%s:%d`, `%s`)." % (hrr["sdk"]["file"], hrr["sdk"]["line"],
                                  hrr["sdk"]["property_class"]))
        A("- **No archetype overrides it** - it is absent from `CHAIN.json` (%d mentions) and from"
          % hrr["chain_mentions"])
        A("  the %d-field `OFFSETS.json` binding (%d rows), so the tags carry no value; the shipped"
          % (hrr["offsets_total"], hrr["offsets_rows"]))
        A("  number is whatever the native CDO in `BmScript` (not shipped) holds.")
        A("- Exactly **%d** script function in all %s reads it:"
          % (len(self.readers("RVehicleBatmobileBase.HealthRecoverRate")),
             format(ps["function_exports"], ",")))
        A("  **`%s`** (%d B), which also reads %s."
          % (short(ea), self.fun(ea)["script_bytes"],
             self.need(ea, ["RGameInfo.GetDifficulty"])))
        A("")
        A("So recovery is **awarded per experience event, indexed by difficulty**, not a")
        A("health-per-second regen out of combat, and the rate table itself is not in the files.")
        A("Verdict for the row: **mechanism = yes (decoded), value = unknown from the files**")
        A("(readable only from a running game's CDO, same class of gap as `CAMERA.md` \u00a72b).")
        A("")
        A("**The `*Regen*` negation, now per class.** The old sentence checked a global name list,")
        A("which cannot answer an owner question. The export scan can:")
        A("")
        A("- **%d** classes match `%s`. Their members matching"
          % (fam["classes"], fam["class_pattern"]))
        A("  `Regen|Heal|Recover|Restore|Repair|Replenish` number **%d**, and **%d** of them match"
          % (len(fam["members"]), len(fam["regen_members"])))
        A("  `Regen`: %s."
          % (", ".join("`%s`" % m["member"] for m in fam["regen_members"])
             if fam["regen_members"] else "none"))
        owners = reg["bmgame_regen_owners"]
        if not owners:
            raise SystemExit("G1-14 render invariant: no *Regen* owner left in the record")
        owned = "; ".join("`%s` owned by %s"
                          % (name, ", ".join("`%s` (%s)" % (o[0], o[1]) for o in lst))
                          for name, lst in owners.items())
        A("- The `Regen`-named symbols in the name table, with owners from the BmGame export")
        A("  scan: %s." % owned)
        A("- The %d vehicle-family members the scan does find are state and restore triggers:"
          % len(fam["members"]))
        A("  %s." % ", ".join("`%s.%s`" % (m["class"], m["member"]) for m in fam["members"]))
        A("- Name-table match count for the whole package (superset, `Heal` matches `Health`): **%d**."
          % len(reg["bmgame_names"]))
        A("")
        corr = [n for n in reg["bmgame_names"]
                if re.search(r"^(?:HealthRecover|RestoreHealth|RestoreArmour|KOHealthRegain|"
                             r"BatmobileHealth|PDVer_BatmobileHealth|Play_BML_LowHealth)", n)
                or re.search(r"Replenish\w*Health", n)]
        if not corr:
            raise SystemExit("G1-14 render invariant: no regen-family name left in the table")
        A("Corroboration, from the same name table (%d names): %s -"
          % (len(corr), ", ".join("`%s`" % n for n in corr)))
        A("health is a *state* with restore triggers and a persisted version key, not a regenerating")
        A("counter. No `*Regen*` member exists on any `RVehicle*`, `Pawn` or `AkVehicle` class (%d"
          % len(fam["regen_members"]))
        A("of %d members), and the one `bRegenerateChildren` belongs to a crowd spawner." %
          len(fam["members"]))
        A("")
        A("The SDK dump, with the class that declares each symbol (%d symbols):" % len(
            reg["bm_sdk_symbols"]))
        A("")
        L.extend(table(["symbol", "classes"],
                       [["`%s`" % k, ", ".join("`%s`" % c for c in v)]
                        for k, v in list(reg["bm_sdk_symbols"].items())]))
        A("")
        # ---------------------------------------------------------------- §6
        A("## 6. What this corrects in `POSTMORTEM_DAMAGE.md`")
        A("")
        A("1. **T-DM7 \u2192 `out` is confirmed.** Every field `CalculateAndStoreImpactDamage` reads is")
        A("   an outgoing multiplier (`Impact*`, `BattleModeImpact*`, strafe/boost/civilian mods);")
        A("   the class still has no *scaling* expression for incoming impact damage.")
        A("2. **But the sentence \"there is no incoming-impact entry point on the class\" is wrong.**")
        A("   `TakesDamageFromRam` is exactly that entry point, it is script, and its body begins")
        A("   with `return true`. Incoming-impact immunity therefore cannot be a value row here.")
        A("   What its trailing %d bytes do is UNKNOWN." % tail)
        A("3. **The armour-mode reduction is real but shipped at zero.** `ArmourModeDamageReduction`")
        A("   = `%s` is *not* an undeclared switch: that is the value the archetype authors set,"
          % fmt(self.value("RVehicleBatmobile", bats[0],
                           "RVehicleBatmobileBase.ArmourModeDamageReduction")))
        A("   and `TakeDamage` is its only reader. The undeclared switches remain the ones the")
        A("   postmortem listed")
        A("   (`impact_damage_factor`, `impact_armor`, `deform_scale`, \u2026) - those live in the")
        A("   **JC3** build, not in BmAK.")
        A("4. **`ShouldRadialDamageHit` is native, so \"how a radial hit is decided\" cannot be")
        A("   answered from script.** Any claim about it needs the exe, and it belongs in `G1-22`.")
        A("")
        # ---------------------------------------------------------------- §7
        A("## 7. Open, honestly")
        A("")
        A("- `HealthRecoverRate[difficulty]` values \u2192 needs the running game's CDO (`G1-22` / a probe).")
        A("- `GetDamageMod` is native: the encounter scaling behind ARM-2's hits-to-kill is in")
        A("  `BatmanAK.exe` (`execGetDamageMod`), not in script. `G2-28` needs this number.")
        A("- The per-`DamageType` multipliers live in the damage classes (each projectile's")
        A("  `MyDamageType` import); those classes are engine-side and were not opened here.")
        A("- **The trace is token-aligned, not decoded.** `walk()` accepts a reference/literal only")
        A("  at a byte where no earlier accepted token covers it, and leaves every other byte")
        A("  unnamed: **%d** reference candidates are unaligned across the %d traced functions"
          % (sum(f["walk"]["unaligned_ref_candidates"] for f in self.f.values()), len(self.f)))
        A("  (sampled under `functions.*.walk.unaligned_sample`) and %d body bytes belong to no"
          % sum(f["walk"]["unexplained_bytes"] for f in self.f.values()))
        A("  recognised token. That is the difference between \"a token references X\" and \"these")
        A("  four bytes occur somewhere\": the old trace listed `PawnDied` and `SetupResolution` as")
        A("  calls of a distance-falloff function, and the walk shows both were unaligned.")
        A("  No reader count or call claim in this note comes from an unaligned candidate.")
        A("- **Literals are candidates, not an expression tree.** The walk finds each `EX_IntConst`")
        A("  / `EX_FloatConst` at an aligned offset; it does not prove which operand the compiler")
        A("  built it for. Branches, jump offsets and nesting are not resolved into source, so where")
        A("  \u00a73 says \"gates\" or \"afterwards\" it is following byte order, not a disassembled AST.")
        A("- `read_by` is now token-aligned; the old containment count is kept beside it per field")
        A("  (`field_references.*.containment_only`), so no reader claim rests on four bytes.")
        A("- **Aligned is still a candidate, not a call.** A recognised token can sit after a byte")
        A("  the size table does not cover, so an aligned name can be a mis-parse. The walk must not")
        A("  be read as a decompiler; every count in this note is a token count, and each name it")
        A("  uses is also present in the record with its offset so a reader can re-check it.")
        A("")
        # ---------------------------------------------------------------- §8
        A("## 8. Tool and gates")
        A("")
        A("```")
        A("python Tools/scripts/bmak_damage.py --write    # JSON + this note + the raw bodies")
        A("python Tools/scripts/bmak_damage.py --check    # re-derive, diff both, assert the anchors")
        A("```")
        A("")
        A("`--check` prints the anchor dict, `anchors true: %d/%d`, `json: PASS|FAIL`," % (n_true, len(anchors)))
        A("`md: PASS|FAIL` and `check: PASS|FAIL`, and exits 1 if any anchor is `False`, if the")
        A("JSON differs, or if this file differs by a byte.")
        A("")
        A("`DAMAGE_RULES.json` carries the layout, the anchors, the `exec<>` counts, all %d traced"
          % len(self.f))
        A("functions (offsets, symbols, constants, walk summary, sha1s), the package stats, %d"
          % len(self.d["damage_values"]))
        A("damage values, the per-field reader lists and the per-class regen scan. Raw bytecode stays")
        A("in `Working/vendor/BmAKgrab/scripts/` (%d files), outside this folder, by the same rule"
          % len(self.f))
        A("that keeps the animation keys and bone face lists outside the notes.")
        A("")
        # ---------------------------------------------------------------- appendix
        A("## Appendix A. Every damage-related field (%d rows)" % len(self.d["damage_values"]))
        A("")
        A("The selection is the tool's own field regex (`health|damage|armou?r|regen|heal|recover|")
        A("death|die|dying|destroy|explos|bullet|melee|smoke|burn|impact|invuln|fragil|deform|kill`,")
        A("case-insensitive) over every archetype tag in `CHAIN.json`. `named_by` is the binding that")
        A("gave the row its name (`sdk-layout` = class-dump layout, `stream` = the tag stream itself).")
        A("")
        L.extend(table(["class", "archetype", "field", "type", "value", "named_by"],
                       [["`%s`" % r["class"], "`%s`" % r["archetype"], "`%s`" % r["name"],
                         r["type"] or "\u2014", fmt(r["value"]), r["named_by"] or "\u2014"]
                        for r in self.d["damage_values"]],
                       ["---", "---", "---", "---", "---:", "---"]))
        A("")
        return "\n".join(L) + "\n"

    def import_ref(self, path, target):
        for r in self.f[path]["refs"]:
            if r["ref"] == target:
                return r["ref_index"]
        raise SystemExit("G1-14 render invariant: %s lost the import %s"
                         % (short(path), target))


ANCHOR_TEXT = {
    "A_super_is_parent_take_damage":
        "`SuperField` of `RVehicleBatmobileBase.TakeDamage` resolves to an inherited `TakeDamage`",
    "A_children_is_first_param":
        "`Children` of the same export is `TakeDamage.DamageAmount`, the first parameter",
    "B_script_size_is_len_plus_one":
        "`ScriptSize == len(script) + 1` for every traced function",
    "C_thinnest_script_is_return":
        "the thinnest script in the package is one byte and it is `0x04` (`EX_Return`)",
    "D_name_word_is_own_name":
        "the trailing `FName` is the function's own short name, on every traced function",
    "E_native_parm_refs_own_properties":
        "every `0x29` descriptor reference names a property of the function it sits in",
    "F_final_function_token_is_call":
        "`0x1c` is followed by a `Function` export in 99%+ of corpus hits (`EX_FinalFunction`)",
}


def sideswipe_offsets():
    """`OFFSETS.json` rows for the sideswipe runtime members (expected 0)."""
    offsets = json.load(open(OFFSETS_JSON, encoding="utf-8"))["fields"]
    names = [f.get("name") if isinstance(f, dict) else f for f in offsets]
    wanted = ("SideSwipeTargetsList", "SideSwipeInSweetSpot", "GetSideSwipeTarget",
              "GetCurrentSideSwipeTarget", "GetBatmobileDodgeDirection",
              "CrushedThisFrame", "BouncedThisFrame")
    return sum(1 for n in names if n and any(w in n for w in wanted))


def render_md(doc):
    return Render(doc).build()


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true", help="write DAMAGE_RULES.json + .md")
    g.add_argument("--check", action="store_true", help="re-derive and diff against both files")
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
        "schema": 2,
        "generated_by": "bmak_damage.py",
        "package": UPK,
        "package_stats": package_stats(bm),
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
        "regeneration": regeneration(bm),
        "field_references": field_references(bm),
        "sideswipe_offsets": sideswipe_offsets(),
        "missing": [p for p in TRACED if p not in funcs],
    }
    md = render_md(doc)

    if a.write:
        write_raw(funcs)
        json.dump(doc, open(OUT, "w", encoding="utf-8"), indent=1)
        open(MD, "w", encoding="utf-8", newline="\n").write(md)
        print("wrote", os.path.relpath(OUT, ROOT), "+",
              os.path.relpath(MD, ROOT), "and", len(funcs), "raw scripts")
        return 0

    old = json.load(open(OUT, encoding="utf-8"))
    old_md = open(MD, encoding="utf-8").read()
    same_json = json.dumps(old, sort_keys=True) == json.dumps(doc, sort_keys=True)
    same_md = old_md == md
    n_true = sum(1 for v in anchors_doc.values() if v)
    print("anchors:", {k: v for k, v in anchors_doc.items()})
    print("anchors true: %d/%d" % (n_true, len(anchors_doc)))
    print("json:", "PASS" if same_json else "FAIL")
    print("md:", "PASS" if same_md else "FAIL")
    if not same_md:
        import difflib
        diff = list(difflib.unified_diff(old_md.splitlines(), md.splitlines(),
                                         "file", "rendered", n=1, lineterm=""))
        for line in diff[:20]:
            print(line)
    ok = n_true == len(anchors_doc) and same_json and same_md
    print("check:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

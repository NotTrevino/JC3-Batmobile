import json, sys, collections, struct
sys.path.insert(0, "Tools/scripts")
import bmak_damage as B

d = json.load(open("Research/BatmobileGrab/DAMAGE_RULES.json", encoding="utf-8"))
rows = d["damage_values"]

print("[1] missile / EMP / cannon rows")
for r in rows:
    if r["class"] in ("RBatmobileMissile", "RBasicProjectile") and "Projectile.Damage" in r["name"] \
            and any(k in r["archetype"] for k in ("Missile_Projectile", "EMPMissile_Projectile",
                                                  "JokerMissile_Projectile", "Primary_Projectile",
                                                  "Fully_Upgraded_Projectile")):
        print("   %-32s %-60s %s" % (r["archetype"].split(".")[1], r["name"],
                                     r["value"] if r["class"] == "RBatmobileMissile" else r["value"]))

print("[2] projectile archetypes and MyDamageType coverage")
arch = {r["archetype"] for r in rows if r["class"] in ("RBasicProjectile", "RBatmobileMissile")}
myd = {r["archetype"] for r in rows if r["name"] == "Projectile.MyDamageType"}
print("   archetypes %d | with MyDamageType %d | without %d" % (len(arch), len(myd & arch), len(arch - myd)))

print("[3] where 110 lives")
for r in rows:
    if r["value"] == 110:
        print("   %-28s %-70s %s" % (r["name"], r["archetype"].split(".")[1], r["value"]))

print("[4] old scan's mask, per literal (tool's own covered set)")
bm = B.Bm(B.UPK)
for path in ("RVehicleBatmobileBase.TakeRadiusDamageFromWeapon",
             "RVehicleBatmobileBase.DrainWeaponGeneratorForDamage",
             "RVehicleBatmobileBase.LoadHealth"):
    s = bm.script(bm.by_path[path])
    covered = {}
    for m in range(len(s) - 4):
        if s[m] in B.REF_TOKENS and 1 <= struct.unpack_from("<i", s, m + 1)[0] <= bm.pkg.export_count:
            for k in range(m, m + 5):
                covered[k] = m
    old = [c["at"] for c in json.load(open("tmp/freebuff/g114rework/DAMAGE_RULES.json", encoding="utf-8"))["functions"][path]["constants"]]
    for m in range(len(s) - 4):
        if s[m] == 0x1E:
            v = round(struct.unpack_from("<f", s, m + 1)[0], 6)
            if v in (0.5, 0.0):
                print("   %-46s literal %s @%d masked_by_offset=%s" %
                      (path.split(".")[1], v, m, covered.get(m)))

print("[5] ImpactMaxDamage reference")
c = d["functions"]["RVehicleBatmobileBase.CalculateAndStoreImpactDamage"]["refs"]
print("   %s" % [(r["at"], r["ref"]) for r in c
                 if r["ref"] == "RVehicleBatmobileBase.ImpactMaxDamage"])

print("[6] regen symbols and owners")
print("   sdk counter (old artifact): %s" % dict(list(d["regeneration"]["bm_sdk_symbols"].items())[:3]))
print("   name-table *Regen* names: %s" % [n for n in d["regeneration"]["bmgame_names"] if "Regen" in n])
print("   owners: %s" % d["regeneration"]["bmgame_regen_owners"])
fam = d["regeneration"]["vehicle_family"]
print("   vehicle-family classes %d | family members %d | matching Regen %d"
      % (fam["classes"], len(fam["members"]), len(fam["regen_members"])))

print("[7] trace noise and containment-vs-token readers")
w = d["functions"]["RVehicleBatmobileBase.TakeRadiusDamageFromWeapon"]
print("   refs %d | accepted tokens %d | unaligned candidates %d"
      % (len(w["refs"]), w["walk"]["accepted_tokens"], w["walk"]["unaligned_ref_candidates"]))
print("   sample: %s" % [(u["at"], u["ref"]) for u in w["walk"]["unaligned_sample"]])
for k, v in d["field_references"].items():
    print("   %-46s containment %2d | token %2d | containment_only %d"
          % (k.split(".")[-1], v["containment_count"], len(v["read_by"]), len(v["containment_only"])))
print("   unaligned across all 14 traced functions: %d"
      % sum(f["walk"]["unaligned_ref_candidates"] for f in d["functions"].values()))

print("[8] anchors")
print("   keys %d: %s" % (len(d["anchors"]), list(d["anchors"])))

print("[9] TakesDamageFromRam trace")
r = d["functions"]["RVehicleBatmobileBase.TakesDamageFromRam"]
print("   body %d B, sha1 %s" % (r["script_bytes"], r["script_sha1"]))
print("   trace %s | refs %d | constants %d | unparsed tail %d"
      % ([t["token"] for t in r["walk"]["short_trace"]], len(r["refs"]), len(r["constants"]),
         r["walk"]["unparsed_tail_bytes"]))

print("[10] row inventory")
print("   damage_values %d rows | note appendix rows %d"
      % (len(rows), open("Research/BatmobileGrab/DAMAGE_RULES.md", encoding="utf-8").read().count("| `R")))

"""EVENTMAP: every JC3 Serpente sound-component x BmAK equivalent (role rules stated)."""
import json, os

A = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio"
epe = json.load(open(os.path.join(A, "epe_true.json")))  # [name, class, guidhex]
grab = json.load(open(os.path.join(A, "grab_manifest.json")))

BML = "Working/Audio/bml"
HASHID = "Working/Audio/hashid"
GRAB = "Working/Audio/grab"

# BmAK pool: (key, files, provenance). Roles from BmAK bank graph / hashlist / verify.
POOL = {
 "engine_loop": (["%s/jc3_batmobile_loop.wav" % BML,
                  "%s/eng_001BD1C9.wav" % BML, "%s/eng_1808E883.wav" % BML],
                 "BML_Engine Idle layers; 1808E883 in-game verified startup+loop"),
 "engine_start": (["%s/jc3_batmobile_start.wav" % BML, "%s/eng_1808E883.wav" % BML],
                 "eng_1808E883 head; crank/catch trajectory + in-game verify"),
 "turbo_sustain": (["%s/EC2FD42B.wav" % HASHID], "hashlist BML_Turbo SFX_1/EC2FD42B; steady 4kHz"),
 "turbo_whoosh": (["%s/eng_209CCD2A.wav" % BML], "2099606B blend media (unmatched ev; whoosh-labeled by inference)"),
 "signature_bed": (["%s/E7BD5AD0.wav" % HASHID], "hashlist BML_Batmobile SFX_1/E7BD5AD0; 15s bed"),
 "reverse": (["%s/eng_0615BDDD.wav" % BML, "%s/eng_1BDA6A88.wav" % BML], "Play_Batmobile_Reverse + BD2FEE58 media"),
 "clutch_rev": (["%s/eng_06CEA240.wav" % BML], "Play_Batmobile_Clutch media"),
 "transition": (["%s/eng_38BFA88C.wav" % BML], "Transition_In/Out one-shots"),
 "positional": (["%s/eng_26E87848.wav" % BML], "Play_Batmobile_Positional beds"),
 "burnout": (["%s/BML_Burnout_03B8EEFB.wav" % BML], "BML_Burnout bank; Play_Batmobile_Burnout"),
 "mshot": (["%s/eng_209CCD2A.wav" % BML], "Play_Batmobile_MShot 1.3-1.9s"),
}

# pairing rules: JC3 role -> BmAK pool key | KEEP (no equivalent exists)
RULES = [
 ("engine_running_sound", "engine_loop+engine_start", "role:Start/running/shutdown markers; same-role loop+ignition"),
 ("exhaust_upgrade_nitrous", "turbo_sustain", "role: hashlist BML_Turbo == afterburner sustain"),
 ("exhaust_upgrade_tjump", "turbo_whoosh", "role: jump whoosh; inference-labeled"),
 ("exhaust_upgrade_tjump_trail", "turbo_whoosh", "role: same event family (shared GUID a5d32c2e)"),
 ("speedwind_sound_player", "signature_bed", "role: character bed for speed wind"),
 ("GearChange", "transition", "role: shift clunk <- Transition one-shots (inference)"),
 ("jump_air_whoosh_sound", "turbo_whoosh", "role: whoosh (inference)"),
 ("ground_roughness_sound_attached", "positional", "role: positional beds (inference)"),
 ("chassis_spinning_sound", "positional", "role: positional beds (inference)"),
 ("sinking_sound", "KEEP", "no Batmobile sinking equivalent"),
 ("in_water_move_sound", "KEEP", "no Batmobile water equivalent"),
 ("water_explosion", "KEEP", "generic explosion; keep stock"),
 ("fire_post_explosion", "KEEP", "generic explosion; keep stock"),
 ("explosion", "KEEP", "generic explosion; keep stock"),
 ("damage_smoke", "KEEP", "generic damage; keep stock"),
 ("horn", "KEEP", "Batmobile has no horn"),
 ("DoorOpeningStart", "KEEP", "Batmobile has no doors"),
 ("DoorClosingEnd", "KEEP", "Batmobile has no doors"),
 ("dynamic_break_*", "KEEP", "Batmobile armored; no breakables (7 comps)"),
]
STARTER = {"engine_running_sound", "exhaust_upgrade_nitrous", "exhaust_upgrade_tjump",
           "exhaust_upgrade_tjump_trail", "speedwind_sound_player", "GearChange",
           "jump_air_whoosh_sound", "ground_roughness_sound_attached", "chassis_spinning_sound"}

lines = ["# JC3 Serpente x BmAK Batmobile EVENTMAP",
         "",
         "Rule: pair by role scraped from files on both sides. Evidence tags: "
         "[scraped] = file link, [role] = same-role match, [infer] = graph-position "
         "inference, [none] = no equivalent exists (keep stock).",
         "",
         "| # | JC3 component (epe) | JC3 GUID | BmAK equivalent | BmAK source | evidence |",
         "|---|---------------------|----------|-----------------|-------------|----------|"]
used = set()
for i, (nm, cl, g) in enumerate(epe):
    rule = next((r for r in RULES if r[0] == nm or (r[0].endswith("*") and nm.startswith(r[0][:-1]))), None)
    if rule is None:
        rule = (nm, "KEEP", "no mapping rule; keep stock (explicit)")
    _, bkey, ev = rule
    if bkey == "KEEP":
        equiv, src = "KEEP STOCK", "-"
    else:
        keys = [k.strip() for k in bkey.split("+")]
        equiv = " + ".join(keys)
        src = "; ".join(POOL[k][0][0] for k in keys)
        used.update(keys)
    if nm in STARTER or bkey != "KEEP":
        tag = "STARTER-SET" if nm in STARTER else ""
    else:
        tag = ""
    lines.append("| %d | %s | `%s` | %s | %s | %s %s |" % (i, nm, g[:8], equiv, src, ev, tag))
open(os.path.join(A, "EVENTMAP.md"), "w").write("\n".join(lines) + "\n")

# starter-set file list for the ADD phase
starter = []
for nm, cl, g in epe:
    rule = next((r for r in RULES if r[0] == nm or (r[0].endswith("*") and nm.startswith(r[0][:-1]))), None)
    if rule and rule[1] != "KEEP":
        for k in [x.strip() for x in rule[1].split("+")]:
            starter.append((nm, g, k, POOL[k][0][0]))
json.dump(starter, open(os.path.join(A, "starter_set.json"), "w"), indent=1)
print("eventmap rows:", len(epe), "| starter pairs:", len(starter))
for nm, g, k, f in starter:
    print("  %-28s %-8s -> %-14s %s" % (nm, g[:8], k, f))

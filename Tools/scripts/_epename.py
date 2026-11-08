import re

x = open(r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\serpente_epe.xml", encoding="utf-8").read()
pat = re.compile(r'<value name="Sound" type="vec_byte">([0-9A-F,]+)</value>')
for nm in ["engine_running_sound", "damage_fire_right", "exhaust_upgrade_nitrous2",
           "exhaust_upgrade_tjump", "speedwind_sound_player", "sportsmuscle_engine",
           "jump_air_whoosh_sound", "in_water_move_sound", "horn", "DoorClosingEnd"]:
    i = x.find(nm)
    if i < 0:
        print(nm, "ABSENT")
        continue
    seg = x[max(0, i-200):i+2500]
    m = pat.search(seg)
    print(nm, "->", m.group(1)[:48] if m else "NO-SOUND-NEARBY")

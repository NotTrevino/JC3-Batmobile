"""All 45 Serpente GUIDs: bank, epe name, TMLN markers, nested track GUIDs."""
import json, os, re, struct

A = r"E:\Modding\JC3-Batmobile\Working\Audio"
J = r"E:\Modding\JC3-Batmobile\Working\Audio\jc3bank\sound\fmod_banks"
evs = [l.strip() for l in open(os.path.join(A, "serpente_fmod_events.txt"))]

# epe name -> guid
x = open(os.path.join(A, "serpente_epe.xml"), encoding="utf-8").read()
epe = {}
for m in re.finditer(r'<value name="name" type="string">([^<]+)</value>(.*?)<value name="Sound" type="vec_byte">([0-9A-F,]+)</value>', x, re.S):
    if len(m.group(2)) < 3000:
        g = bytes(int(b, 16) for b in m.group(3).split(",")).hex()
        epe[g] = m.group(1)
print("epe named:", len(epe))

banks = {}
for b in ["vehicles.bank", "effects.bank", "character.bank"]:
    banks[b] = open(os.path.join(J, b), "rb").read()

rows = []
for g in evs:
    raw = bytes.fromhex(g.strip("{}").replace("-", ""))
    row = {"guid": g, "epe": "", "bank": "", "markers": [], "ntracks": 0}
    for e, n in epe.items():
        if e == raw.hex():
            row["epe"] = n
    for b, d in banks.items():
        o = 0
        while True:
            o = d.find(b"LIST", o)
            if o < 0: break
            if d[o+8:o+12] == b"TMLN":
                (sz,) = struct.unpack_from("<I", d, o + 4)
                body = d[o+12:o+12+sz]
                if raw in body:
                    row["bank"] = b
                    row["markers"] = sorted(set(m.decode() for m in re.findall(rb"[A-Za-z][A-Za-z0-9_]{3,20}", body)
                        if m.decode() not in ("LIST", "TMLN", "TLNB", "TRAN", "TRNB", "TRTL")))
                    # nested TRAN guids count
                    row["ntracks"] = body.count(b"TRNB") - 1
                    break
            o += 4
        if row["bank"]:
            break
    rows.append(row)
    print("%-38s %-22s %-15s tracks=%d markers=%s" % (
        row["epe"] or "(unnamed)", g[:18] + "...", row["bank"].split(".")[0],
        row["ntracks"], row["markers"][:8]))
json.dump(rows, open(os.path.join(A, "jc3_event_roles.json"), "w"), indent=1)
print("wrote jc3_event_roles.json")

import struct
stream = open(r"E:\Modding\JC3-Batmobile\Working\Audio\bm_stream.bin", "rb").read()
for img_off, tag in ((8454056, "BattlemodeEngine"), (8454510, "Transition_In")):
    o = img_off - 0x369
    print(tag, "serial@stream+0x%X (26B):" % o, stream[o:o+26].hex(" "))
    # UE3 property stream: try tagged parse: nameidx(8) type(8) size(8?) ...
    # AKEvent props: look for u32 event id candidates
    print("   u32s:", struct.unpack("<6I", stream[o:o+24]))

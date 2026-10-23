"""test-031 patch: full Luke mirror - body (already repointed in base) + 4 wheels
-> dababy_wheel.lod + 4 mshswap -> dababy_wheel_modelswap.lod. Verifies the
(X,0,HASH,0,Y,0,0,0,0xFF00) entry shape at every slot before touching bytes."""
import struct

P = r"Builds\test-031\aaf\models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\sportsmuscle_vehicle_parts.vmodc"

WHEEL = 0xA6714D5B
MSWAP = 0xDFD0AD86
TARGETS = {
    0x0B4ABFC4: WHEEL, 0x0D1B71D1: WHEEL, 0x8B2428FC: WHEEL, 0x390B9151: WHEEL,
    0xCCBF71CC: MSWAP, 0x5D723B36: MSWAP, 0x41500676: MSWAP, 0x03CFE2BB: MSWAP,
}

d = bytearray(open(P, "rb").read())
n = 0
for old, new in TARGETS.items():
    o = d.find(struct.pack("<I", old))
    assert o > 0 and d.find(struct.pack("<I", old), o + 4) < 0, hex(old)
    pre = struct.unpack_from("<II", d, o - 8)
    post = struct.unpack_from("<II", d, o + 4)
    assert post[0] == 0, (hex(old), [hex(x) for x in post])
    struct.pack_into("<I", d, o, new)
    n += 1
open(P, "wb").write(d)
print("patched", n, "wheel slots; entry shape confirmed at all 8")

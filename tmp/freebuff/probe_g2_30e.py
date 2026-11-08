"""G2-30 probe 5: pin the hull face table.

Hypothesis: one 4-byte record per plane, `u16 first, u8 count, u8 min`, the records
partitioning the index list (sum(count) == index_count, firsts contiguous from 0).
Checked on every hull of both files; a layout that holds 54/54 is evidence, not a guess.
"""
import sys

sys.path.insert(0, r"E:/Modding/JustCause3/JC3-Batmobile/Tools/scripts")
import jc3hkx  # noqa: E402

FILES = {
    "donor": (r"E:/Modding/JustCause3/JC3-Batmobile/Builds/test-091/aaf/models/jc_vehicles/01_land/"
              r"v0300_car_kensington_sportsmuscle/sportsmuscle.physicsc"),
    "assembled": r"E:/Modding/JustCause3/JC3-Batmobile/Working/Assembled/sportsmuscle_true.physicsc",
}

for tag, path in FILES.items():
    blob = open(path, "rb").read()
    pf = jc3hkx.Packfile(blob)
    ok_part, ok_sum, n, bad = 0, 0, 0, []
    for o in pf.objects:
        if o.cls != jc3hkx.POLYTOPE:
            continue
        n += 1
        d = jc3hkx.decode_polytope(pf, o.offset)
        face_at = o.offset + jc3hkx.POLYTOPE_HEAD + 16 * d["vertex_count"] + 16 * (
            d["plane_count"] + d["unused_planes"])
        recs = [pf.u32(face_at + 4 * i) for i in range(d["face_bytes"] // 4)]
        firsts = [r & 0xFFFF for r in recs]
        counts = [(r >> 16) & 0xFF for r in recs]
        mins = [(r >> 24) & 0xFF for r in recs]
        contiguous = firsts == sorted(firsts) and (
            not firsts or (firsts[0] == 0 and all(
                firsts[i] + counts[i] == firsts[i + 1] for i in range(len(firsts) - 1))))
        total = sum(counts)
        if contiguous:
            ok_part += 1
        if total == d["index_count"]:
            ok_sum += 1
        if not (contiguous and total == d["index_count"]):
            bad.append((hex(o.offset), d["vertex_count"], d["plane_count"],
                        d["index_count"], d["face_bytes"], firsts[:6], counts[:6], total))
    print(f"== {tag}: hulls {n} | face records = plane count: "
          f"{sum(1 for o in pf.objects if o.cls == jc3hkx.POLYTOPE and 4 * jc3hkx.decode_polytope(pf, o.offset)['face_bytes'] // 4 == jc3hkx.decode_polytope(pf, o.offset)['plane_count'] + jc3hkx.decode_polytope(pf, o.offset)['unused_planes'])}"
          f" | firsts partition the index list {ok_part} | sum(count) == index_count {ok_sum}")
    for b in bad[:6]:
        print("   bad", b)

# one worked example, in full
blob = open(FILES["donor"], "rb").read()
pf = jc3hkx.Packfile(blob)
for o in pf.objects:
    if o.cls == jc3hkx.POLYTOPE and o.offset == 0xB5D0:
        d = jc3hkx.decode_polytope(pf, o.offset)
        face_at = o.offset + jc3hkx.POLYTOPE_HEAD + 16 * d["vertex_count"] + 16 * (
            d["plane_count"] + d["unused_planes"])
        print(f"\nwheel_f_l @{o.offset:#x}: v={d['vertex_count']} p={d['plane_count']} "
              f"i={d['index_count']} faces={d['face_bytes'] // 4}")
        for i in range(d["face_bytes"] // 4):
            r = pf.u32(face_at + 4 * i)
            f, c, m = r & 0xFFFF, (r >> 16) & 0xFF, (r >> 24) & 0xFF
            idx = d["indices"][f:f + c]
            pl = d["planes"][i] if i < len(d["planes"]) else None
            n = pl["n"] if pl else None
            # are all the indices on that plane?
            on = all(abs(sum(n[k] * d["vertices"][j][k] for k in range(3)) + pl["d"]) < 0.02
                     for j in idx) if pl else None
            print(f"  face {i:2d} first={f:3d} count={c:2d} min={m:3d} idx={idx} "
                  f"plane={[round(x, 3) for x in n] if n else None} d={round(pl['d'], 3) if pl else None} "
                  f"on_plane={on}")

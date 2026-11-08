"""G2-30 probe 7: isolate the round-trip byte diff and the failing case."""
import sys

sys.path.insert(0, r"E:/Modding/JC3-Batmobile/Tools/scripts")
import jc3hkx as H  # noqa: E402

blob = open(H.DONOR, "rb").read()
pf = H.Packfile(blob)
edits = {o.offset: H.hull_bytes(pf, o.offset) for o in pf.objects if o.cls == H.POLYTOPE}
bad = {off: H.diff_ranges(blob[pf.base + off:pf.base + off + pf.extents[off]], b)
       for off, b in edits.items()
       if b != blob[pf.base + off:pf.base + off + pf.extents[off]]}
print("hulls whose re-emit differs:", len(bad))
for off, ranges in list(bad.items())[:4]:
    d = H.decode_polytope(pf, off)
    print(f"  @{off:#x} v={d['vertex_count']} p={d['plane_count']} ranges={ranges[:6]}")
    for r0, rn in ranges[:3]:
        print("     src", blob[pf.base + off + r0:pf.base + off + r0 + rn].hex())
        print("     new", edits[off][r0:r0 + rn].hex())

out, info = H.packfile_bytes(pf, edits)
print("whole-file diff:", len(H.diff_ranges(blob, out)), "ranges",
      sum(n for _s, n in H.diff_ranges(blob, out)), "bytes; shifts", info["shifts"])

print("\n-- per case --")
for name, fn in (("shift", lambda: H._case_shift(pf)),
                 ("scale", lambda: H._case_scale(pf, 0xB5D0, 1.6596, "wheel_f_l")),
                 ("replace", lambda: H._case_replace(pf, 0xB5D0, 0x5250, {}))):
    c = fn()
    print(name, "problems:", c["problems"][:3], "| n:", len(c["problems"]))
    if name == "scale":
        print("  stale:", c["stale_problems"][:3])
        print("  ranges:", c["changed_ranges"][:12], "bytes", c["changed_bytes"])

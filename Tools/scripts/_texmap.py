"""Texture -> asset mapping, derived from the meshes (no hand list).

Walks every .rbm in a tree, reads each block's texture table, and inverts it:
which texture file feeds which meshes, in which slot positions. Answers "which
texture goes to which asset" from data. Usage: python _texmap.py <aaf-dir>
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import rbm_geom as R  # noqa: E402


def main(root):
    files = sorted(glob.glob(os.path.join(root, "**", "*.rbm"), recursive=True))
    tex2mesh, meshnoused = {}, {}
    for f in files:
        try:
            m = R.decode(open(f, "rb").read())
        except Exception as e:
            print("SKIP", f, e)
            continue
        rel = os.path.relpath(f, root).replace(os.sep, "/")
        slots = []
        for b in m.blocks:
            for t in getattr(b, "textures", []) or []:
                if t:
                    slots.append(t)
        meshslots = sorted(set(slots))
        meshnoused[rel] = meshslots
        for i, s in enumerate(meshslots):
            tex2mesh.setdefault(s, []).append("%s[%d]" % (rel, i))
    print("== %d rbms, %d distinct textures" % (len(files), len(tex2mesh)))
    print("-- textures by consumer count:")
    for s, users in sorted(tex2mesh.items(), key=lambda kv: -len(kv[1])):
        print("  x%-3d %-100s" % (len(users), s))
        for u in users[:8]:
            print("        %s" % u)
        if len(users) > 8:
            print("        ... +%d" % (len(users) - 8))
    json.dump({"tex2mesh": tex2mesh},
              open("Working/TexProbe/texmap.json", "w"), indent=1)
    print("wrote Working/TexProbe/texmap.json")


main(sys.argv[1])

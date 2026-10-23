"""Material -> texture manifest from UE .props.txt dumps + PSKX material list.

Authoritative where props exist (TextureParameterValues incl. parent-chain
inheritance); token-overlap fallback where they don't. Answers "which texture
goes to which asset" repeatably: same script, any PSKX + props folder.
Usage: python _texmatch.py <pskx> <props-dir>
"""
import glob
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
from psk2rbm import read_pskx  # noqa: E402


def parse_props(path):
    text = open(path, encoding="utf-8", errors="replace").read()
    parent = re.search(r"^Parent = (\S+)", text, re.M)
    tex = re.findall(
        r"ParameterValue\s*=\s*Texture2D'[^.]*\.(?:[^.\s]*\.)?([A-Za-z0-9_]+)'\s*"
        r"ParameterName\s*=\s*([A-Za-z0-9_]+)", text)
    scal = re.findall(
        r"ParameterValue\s*=\s*([0-9.eE+-]+)\s*ParameterName\s*=\s*([A-Za-z0-9_]+)",
        text)
    return (parent.group(1) if parent else None,
            {name: texname for texname, name in tex},
            {name: val for val, name in scal})


def _tokens(name):
    return {t for t in re.split(r"[_\W]+", re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower()) if t}


def texture_bindings(mats, srcdir):
    """{material: {param: (texture_name, tga_path_or_None)}} for EVERY material, no name lists.

    1. props bindings with parent-chain inheritance (authoritative);
    2. materials left without any binding fall back to name-token overlap with the texture files on
       disk; stopwords are tokens shared by more than half of all texture names (data-derived), and
       the param is named after the file's last token (its role suffix: d/n/r/s/e/a/m).
    """
    props = {}
    for p in glob.glob(os.path.join(srcdir, "**", "*.props.txt"), recursive=True):
        props[os.path.basename(p)[:-len(".props.txt")]] = parse_props(p)
    files = {os.path.splitext(os.path.basename(f))[0]: f
             for f in glob.glob(os.path.join(srcdir, "**", "*.tga"), recursive=True)}
    toks = {n: _tokens(n) for n in files}
    from collections import Counter
    freq = Counter(t for ts in toks.values() for t in ts)
    stop = {t for t, c in freq.items() if c > len(files) / 2}

    def chain(mat, depth=0):
        out = {}
        if mat in props and depth < 6:
            parent, tex, _ = props[mat]
            if parent:
                out.update(chain(parent.split(".")[-1], depth + 1))
            out.update(tex)
        return out

    res = {}
    for m in mats:
        b = {k: (v, files.get(v)) for k, v in chain(m).items()}
        if not b:
            # the material's distinctive tokens must appear in the texture name (one may be
            # missing when there are 3+, e.g. a generic "textures"); per role suffix (last token:
            # d/n/r/s/e/a/m/glow) keep the shortest such texture
            mt = _tokens(m) - stop - {"mic", "inst", "mat", "new"}
            need = len(mt) - (1 if len(mt) >= 3 else 0)
            cand = {}
            for n, ts in toks.items():
                if mt and len(mt & ts) >= need:
                    role = n.split("_")[-1].lower()
                    if role not in cand or len(ts) < len(toks[cand[role]]):
                        cand[role] = n
            b = {"fallback:" + role: (n, files[n]) for role, n in sorted(cand.items())}
        res[m] = b
    return res


def main(pskx, propsdir):
    P, W, F, mats = read_pskx(pskx)
    from collections import Counter
    counts = Counter(int(x) for x in F["m"])
    tb = texture_bindings(mats, propsdir)
    print("== %d pskx materials" % len(mats))
    for i, nm in enumerate(mats):
        b = tb[nm]
        print("%6d %-38s %s" % (counts.get(i, 0), nm, ", ".join(
            "%s=%s%s" % (k, v, "" if path else " (MISSING)") for k, (v, path) in sorted(b.items()))
            or "(no textures)"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])

"""bm_paths.py - B-18 (translate): every Batmobile file gets a Batmobile-only path.

Found by Q-1a re-test 3 (2026-11-02, MODLOG): the drop delivered a Serpente cabin on Batmobile wheels. The RC
.ee carried its body mesh, wheels, physics, parts module and 13 tuning modules at the donor's SHARED paths
(models/.../sportsmuscle_body.lod, modules/default/..._brakes.vmodc, ...). JC3 shares a loaded resource by
path: bm-001 (loaded with the world) turned every Serpente into a Batmobile; at the `_debug` leaf the traffic
Serpentes load first and the drop gets their vanilla files. Fix the translation, not the symptom: a file
whose bytes are the Batmobile's must not sit at a path a vanilla entity also loads.

Rules (computed from the tree, nothing listed by hand):
  * changed = files at a path the vanilla donor .ee also holds, bytes != vanilla (not @files.xml, not the
    leaf's own files, not the size-only stubs @files.xml declares).
  * a changed file that no Batmobile file reaches (path string or Jenkins hash of the path, directly or
    through unchanged shared files) is a leftover at a shared path (lave_health_medium from test-075, the far
    LOD .rbm B-15 unlinked): it is reverted to the vanilla bytes - shipping it could change vanilla cars.
    So is a known test marker (TEST_MARKERS, matched by sha256).
  * every other changed file moves to <dir>/batmobile/<name>; any shared-path file that references a
    moved one moves too (closure), and every reference is repointed through the file's own format:
      .lod   text lines                      (path string)
      .vmodc ConvertAdf XML, HashString       (string + uint32 hash)
      .epe   ConvertProperty XML, int value   (signed Jenkins hash)
    any other referrer type stops the build.
  * after: 0 changed files at a shared path; 0 references to an old path (string or hash) anywhere;
    every moved file is referenced at its new path (except the ones nothing referenced before either).

    bm_paths.apply(aaf, vanilla_files: dict[name, bytes], stubs: set, leaf: str, workdir) -> dict
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
from rbmhdr import hash_jenkins  # noqa: E402

GIBBED = os.path.join(ROOT, "Tools", "Gibbed")
CONV = os.path.join(GIBBED, "Gibbed.JustCause3.ConvertProperty.exe")
ADF = os.path.join(ROOT, "Tools", "Gibbed-patched", "Gibbed.JustCause3.ConvertAdf.exe")
SUB = "batmobile"
# Test leftovers found by bytes (sha256), not by path: they are reachable (vanilla Serpente panel meshes
# sample them) but carry no Batmobile content, so they go back to vanilla.
TEST_MARKERS = {"d6fa6bc9f2e2a04198280890368ab09ab6fce40f23dd98ac8ed408bea1ed5f16":
                "test-003/test-020 Mugello body_dif marker (MODLOG 2415)"}


def new_path(p: str) -> str:
    d, b = p.rsplit("/", 1)
    return f"{d}/{SUB}/{b}"


def s32(v: int) -> int:
    return v - (1 << 32) if v >= 1 << 31 else v


def _h(p: str) -> int:
    return hash_jenkins(p.encode())


def _read(aaf: str) -> dict[str, bytes]:
    out = {}
    for dp, _, fs in os.walk(aaf):
        for f in fs:
            p = os.path.join(dp, f)
            out[os.path.relpath(p, aaf).replace("\\", "/")] = open(p, "rb").read()
    return out


def _refs(files: dict[str, bytes], target: str) -> set[str]:
    pb, hb = target.encode(), _h(target).to_bytes(4, "little")
    return {m for m, b in files.items() if m != target and m != "@files.xml" and (pb in b or hb in b)}


def _run(args, what):
    r = subprocess.run(args, capture_output=True, text=True, errors="replace")
    if r.returncode:
        raise SystemExit(f"B-18: {what} failed: {(r.stdout + r.stderr)[-400:]}")


def _repoint(path: str, rel: str, pairs: list[tuple[str, str]], workdir: str) -> dict:
    """Rewrite the references `pairs` (old, new) inside one file, through its own format."""
    counts = {}
    if rel.endswith(".lod"):
        b = open(path, "rb").read()
        for o, n in pairs:
            counts[o] = b.count(o.encode())
            b = b.replace(o.encode(), n.encode())
        open(path, "wb").write(b)
    elif rel.endswith(".vmodc"):
        xi, xo = os.path.join(workdir, "adf_in.xml"), os.path.join(workdir, "adf_out.xml")
        _run([ADF, "--e", path, xi], "ConvertAdf --e " + rel)
        t = open(xi, encoding="utf-8-sig").read()
        for o, n in pairs:
            ns, nh = t.count(f">{o}<"), t.count(f">{_h(o)}<")
            if ns != nh:
                raise SystemExit(f"B-18: {rel}: {o} as string x{ns} but as hash x{nh}")
            t = t.replace(f">{o}<", f">{n}<").replace(f">{_h(o)}<", f">{_h(n)}<")
            counts[o] = ns
        open(xo, "w", encoding="utf-8").write(t)
        _run([ADF, "--i", xo, path], "ConvertAdf --i " + rel)
    elif rel.endswith(".epe"):
        xi, xo = os.path.join(workdir, "epe_in.xml"), os.path.join(workdir, "epe_out.xml")
        _run([CONV, "--e", path, xi], "ConvertProperty --e " + rel)
        t = open(xi, encoding="utf-8").read()
        for o, n in pairs:
            pat = re.compile(rf'(type="int">){s32(_h(o))}(</value>)')
            t, k = pat.subn(rf"\g<1>{s32(_h(n))}\g<2>", t)
            counts[o] = k
        open(xo, "w", encoding="utf-8").write(t)
        _run([CONV, "--i", xo, path], "ConvertProperty --i " + rel)
    else:
        raise SystemExit(f"B-18: no repoint route for {rel} (refs {[o for o, _ in pairs]})")
    zero = [o for o, k in counts.items() if not k]
    if zero:
        raise SystemExit(f"B-18: {rel}: byte-level ref found but no format-level ref for {zero}")
    return counts


def apply(aaf: str, vanilla: dict[str, bytes], stubs: set[str], leaf: str, workdir: str) -> dict:
    os.makedirs(workdir, exist_ok=True)
    files = _read(aaf)
    own_leaf = {n for n in files if leaf in n}

    def shared(n):
        return n in vanilla and n != "@files.xml" and n not in own_leaf and n not in stubs

    changed = sorted(n for n in files if shared(n) and files[n] != vanilla[n])
    bat = {n for n in files if n not in vanilla or n in own_leaf} | set(changed)   # Batmobile-owned files
    def reachable(n):   # referenced by a Batmobile file, directly or through unchanged shared files
        seen, todo = {n}, [n]
        while todo:
            for m in _refs(files, todo.pop()):
                if m in bat and m != n:
                    return True
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        return False

    import hashlib
    marker = {n for n in changed if hashlib.sha256(files[n]).hexdigest() in TEST_MARKERS}
    revert = sorted(marker | {n for n in changed if not reachable(n)})
    move = set(changed) - set(revert)
    only = [s for s in os.environ.get("BM_B18_ONLY", "").split(",") if s]   # Q bisect: move only these
    if only:
        move = {n for n in move if any(s in n for s in only)}
    while True:   # closure: a shared-path file referencing a moved one is changed by the repoint -> moves too
        more = {m for r in move for m in _refs(files, r) if shared(m) and m not in move and m not in revert}
        if not more:
            break
        move |= more
    move = sorted(move)
    clash = [n for n in move if new_path(n) in files]
    if clash:
        raise SystemExit(f"B-18: new path already taken: {clash[:3]}")

    # 1. revert leftovers to the vanilla bytes
    for n in revert:
        open(os.path.join(aaf, n), "wb").write(vanilla[n])
    # 2. repoint every referrer (in place, before moving)
    pairs_by: dict[str, list] = {}
    for r in move:
        for m in _refs(files, r):
            if m in revert:
                continue
            pairs_by.setdefault(m, []).append((r, new_path(r)))
    repointed = {m: _repoint(os.path.join(aaf, m), m, sorted(ps), workdir) for m, ps in sorted(pairs_by.items())}
    # 3. move
    for r in move:
        dst = os.path.join(aaf, new_path(r))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(os.path.join(aaf, r), dst)
    fx = os.path.join(aaf, "@files.xml")
    t = open(fx, encoding="utf-8-sig").read()
    listed = 0
    for r in move:
        bs, nbs = r.replace("/", "\\"), new_path(r).replace("/", "\\")
        k = t.count(f'name="{r}"')
        if k > 1 or t.count(f">{bs}<") != k:
            raise SystemExit(f"B-18: @files.xml row for {r}: name x{k}, source x{t.count(f'>{bs}<')}")
        listed += k
        t = t.replace(f'name="{r}"', f'name="{new_path(r)}"').replace(f">{bs}<", f">{nbs}<")
    open(fx, "w", encoding="utf-8-sig", newline="").write(t)

    # 4. checks
    after = _read(aaf)
    left = sorted(n for n in after if shared(n) and after[n] != vanilla[n] and not (only and n in changed))
    old_refs = {r: sorted(_refs(after, r)) for r in move if _refs(after, r)}
    had = {o for ps in pairs_by.values() for o, _ in ps}
    unref = sorted(r for r in had if not _refs(after, new_path(r)))
    if left or old_refs or unref:
        raise SystemExit(f"B-18 check: changed at shared path {left[:5]} | old refs {list(old_refs)[:5]} | "
                         f"moved but unreferenced {unref[:5]}")
    return {"card": "B-18", "moved": {r: new_path(r) for r in move}, "reverted_to_vanilla": revert,
            "repointed": repointed, "files_xml_rows": listed, "changed_at_shared_path_after": 0}

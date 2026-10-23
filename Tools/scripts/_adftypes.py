"""Dump an ADF-derived XML's embedded type library + the instance tree.

Usage: python _adftypes.py <xml> [types|instances]

The XML that Gibbed ConvertAdf writes carries the file's own type library:
struct names, sizes, member offsets and the type-system DEFAULT values. That is
the actual damage-model definition for a .vmodc, so it is worth keeping.

`types`    (default) prints every <type> and its <member> layout.
`instances` prints the <instances> tree, indented, with offsets and values.
"""
import re
import sys

xml = open(sys.argv[1], encoding='utf-8-sig').read()
mode = sys.argv[2] if len(sys.argv) > 2 else 'types'


def unesc(s):
    return (s.replace('&lt;', '<').replace('&gt;', '>')
             .replace('&quot;', '"').replace('&amp;', '&'))


def f32(u):
    """Render a defval that is a float32 bit pattern as both forms."""
    try:
        import struct
        v = struct.unpack('<f', struct.pack('<I', int(u) & 0xFFFFFFFF))[0]
        return ' float=%.6g' % v
    except Exception:
        return ''


if mode == 'types':
    sec = xml[xml.find('<type-definitions'):xml.find('</type-definitions>')]
    # top-level <type> blocks only (members are nested one level deeper)
    for tm in re.finditer(r'<type type="([^"]+)"(?: size="([^"]*)")?[^>]*?name="([^"]+)"[^>]*?(?:/>|>(.*?)</type>)',
                          sec, re.S):
        kind, size, name, body = tm.group(1), tm.group(2) or '-', tm.group(3), tm.group(4) or ''
        print('\n=== %s  (%s, size %s)' % (name, kind, size))
        if not body:
            continue
        for mm in re.finditer(r'<member name="([^"]+)" type-hash="([^"]*)" size="([^"]*)" offset="([^"]*)"'
                              r'(?:[^>]*?defval="([^"]*)")?[^>]*?/>', body):
            mn, th, ms, mo, dv = mm.groups()
            extra = ''
            if dv is not None:
                extra = '  defval=%s (0x%08X)%s' % (dv, int(dv), f32(dv))
            print('    +%-4s %-34s type-hash=%-12s size=%s' % (mo, mn, th, ms))
            if extra:
                print('           %s' % extra)
else:
    sec = xml[xml.find('<instances'):]
    depth = 0
    for tok in re.finditer(r'<instance\b([^>]*)>|</instance>|<member\b([^>]*?)(?:/>|>(.*?)</member>)',
                           sec, re.S):
        if tok.group(1) is not None:                     # <instance ...>
            a = tok.group(1)
            nm = re.search(r'name="([^"]*)"', a)
            tn = re.search(r'type-name="([^"]*)"', a)
            print('%s<instance %s : %s>' % ('  ' * depth,
                                            unesc(nm.group(1)) if nm else '?',
                                            tn.group(1) if tn else '?'))
            depth += 1
        elif '</instance>' in tok.group(0):
            depth -= 1
        else:                                            # <member ...>
            a = tok.group(2) or ''
            nm = re.search(r'name="([^"]*)"', a)
            off = re.search(r'offset-in-file="([0-9A-Fa-f]*)"', a)
            ty = re.search(r'\btype="([^"]*)"', a)
            val = unesc((tok.group(3) or '').strip())
            print('%s%-40s %-10s @%-8s %s' % ('  ' * depth,
                                              nm.group(1) if nm else '?',
                                              ty.group(1) if ty else '',
                                              off.group(1) if off else '',
                                              val[:60]))

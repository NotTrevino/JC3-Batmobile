"""Round-trip cleanliness check: python _rtcheck.py <vmodc> [...]"""
import os, shutil, subprocess, sys, tempfile
GIBBED = r'E:\Modding\JC3-Batmobile\Tools\Gibbed\Gibbed.JustCause3.ConvertAdf.exe'
for vm in sys.argv[1:]:
    if not os.path.exists(vm):
        print('MISSING', vm); continue
    with tempfile.TemporaryDirectory() as td:
        rt = os.path.join(td, os.path.basename(vm))
        shutil.copyfile(vm, rt)
        x = os.path.join(td, 'x.xml')
        r = subprocess.run([GIBBED, '--e', rt, x], capture_output=True)
        if r.returncode != 0:
            print('%-58s DECODE FAIL' % os.path.basename(vm)); continue
        r = subprocess.run([GIBBED, '--i', x, rt], capture_output=True)
        if r.returncode != 0:
            print('%-58s ENCODE FAIL' % os.path.basename(vm)); continue
        a, b = os.path.getsize(vm), os.path.getsize(rt)
        print('%-58s %6d -> %6d  %+d  %s' % (os.path.basename(vm), a, b, b - a, 'OK' if a == b else 'SIZE-DRIFT'))

import glob, os, subprocess
CLI = r"E:\Modding\JustCause3\JC3-Batmobile\Tools\vgmstream-win64\vgmstream-cli.exe"
WEMD = r"E:\Modding\JustCause3\JC3-Batmobile\Working\Audio\wem"
for wem in sorted(glob.glob(os.path.join(WEMD, "*.wem"))):
    r = subprocess.run([CLI, "-m", wem], capture_output=True, text=True)
    out = (r.stdout or "") + (r.stderr or "")
    keep = [l for l in out.splitlines() if any(k in l for k in
            ["stream count", "stream index", "stream name", "encoding", "channels",
             "sample rate", "samples", "loop", "title", "STREAM"])]
    print("==", os.path.basename(wem))
    for l in keep[:14]:
        print("   ", l.strip()[:130])

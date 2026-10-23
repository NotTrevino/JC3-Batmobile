# Build test-033 (control) and test-034 (repoint) on the PATCHED parts vmodc. MODLOG §48.
#
# Every live-repoint crash (024..032, +0x2d49e0) read sportsmuscle_vehicle_parts.vmodc from
# the .ee -- and the .ee's copy (29,886 B) is the PRE-PATCH version. The game's own copy is
# patch_win64\game4 (30,540 B); the .toc marks the record offset 0 precisely so the patched
# one wins. So we ship the patched bytes inside the .ee and internalize THAT.
#
#   test-033 = test-022 tree, parts vmodc := patched (unmodified), internal   -> expect: normal car
#   test-034 = test-033 + body hash 0x63A04A76 -> 0x5EEE7AFB at +328          -> expect: DaBaby head
#
# LOCAL TEST ONLY: the tree carries Luke JC's dababy_head / convertible files.
$ErrorActionPreference = 'Stop'
$root    = 'E:\Modding\JC3-Batmobile'
$g       = "$root\Tools\Gibbed"
$patched = "$root\Research\SerpenteParts\parts_patch_win64_game4_24012.bin"
$rel     = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\sportsmuscle_vehicle_parts.vmodc'
$ee      = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$vtoc    = "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc"

if ((Get-Item $patched).Length -ne 30540) { throw 'patched vmodc is not the 30,540 B game4 copy' }

foreach ($t in @(@{Tag='test-033'; Repoint=$false}, @{Tag='test-034'; Repoint=$true})) {
    $b = "$root\Builds\$($t.Tag)"
    Write-Host "=== $($t.Tag)"
    if (Test-Path $b) { Remove-Item $b -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $b | Out-Null
    Copy-Item "$root\Builds\test-022\aaf" "$b\aaf" -Recurse -Force

    $bytes = [IO.File]::ReadAllBytes($patched)
    if ($t.Repoint) {
        $old = [BitConverter]::ToUInt32($bytes, 328)
        if ($old -ne 0x63A04A76) { throw ('unexpected u32 at 328: 0x{0:X8}' -f $old) }
        [BitConverter]::GetBytes([uint32]0x5EEE7AFB).CopyTo($bytes, 328)
        Write-Host '  body 0x63A04A76 -> 0x5EEE7AFB at +328'
    }
    [IO.File]::WriteAllBytes("$b\aaf\$rel", $bytes)

    & "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
    if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
    python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" $vtoc --base-ee "$root\Builds\test-003\$ee" `
        --internal sportsmuscle_vehicle_parts.vmodc -o "$b\$ee.toc" 2>&1 |
        Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    foreach ($f in "$b\$ee", "$b\$ee.toc") {
        Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
    }
}

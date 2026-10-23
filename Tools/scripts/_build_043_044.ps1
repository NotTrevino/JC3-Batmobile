# test-043 / test-044: the clean Batmobile build. MODLOG §55.
#
# Lessons applied: new .rbm FILES are never loaded (035-039), vanilla rbm paths are (040),
# the 5-part .epe removes the other 35 parts (030/042). So no repoint, no new .lod, no
# DaBaby leftovers, and the parts vmodc stays EXTERNAL (the game's patched copy):
#   base       = test-003 tree (vanilla geometry)
#   .epe       = test-030's 5-part .epe (body + 4 wheels), internal
#   body LODs  = sportsmuscle_body_lod1..5.rbm := Batmobile 20k / 8k / 3k / 1.5k / 0.8k tris
#   test-043: deform format (as drawn in 040/042)   test-044: plain, non-deform (0x001F)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir  = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$epe  = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\v0300_car_kensington_sportsmuscle_civilian_01.epe'

if ((Get-Item "$root\Builds\test-030\aaf\$epe").Length -ne 105302) { throw 'test-030 .epe is not the 5-part file' }
foreach ($t in @(@{Tag='test-043'; Fmt='deform'}, @{Tag='test-044'; Fmt='plain'})) {
    $b = "$root\Builds\$($t.Tag)"
    Write-Host "=== $($t.Tag)  ($($t.Fmt))"
    if (Test-Path $b) { Remove-Item $b -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $b | Out-Null
    Copy-Item "$root\Builds\test-003\aaf" "$b\aaf" -Recurse -Force
    Copy-Item "$root\Builds\test-030\aaf\$epe" "$b\aaf\$epe" -Force
    foreach ($i in 1..5) {
        Copy-Item "$root\Working\Batmobile\lod\$($t.Fmt)_lod$i.rbm" "$b\aaf\$dir\sportsmuscle_body_lod$i.rbm" -Force
    }
    & "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
    if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
    python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
        --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe -o "$b\$ee.toc" 2>&1 |
        Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    foreach ($f in "$b\$ee", "$b\$ee.toc") {
        Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
    }
}

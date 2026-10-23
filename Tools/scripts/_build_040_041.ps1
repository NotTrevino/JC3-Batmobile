# test-040 / test-041: Batmobile bytes at a VANILLA rbm path. MODLOG §53.
#
# test-037 drew sportsmuscle_body_lod5.rbm through a new .lod in the body slot. 038/039 (new
# rbm file, record appended / moved before the .epe) drew nothing. Here the .lod, the repoint
# and the .toc record position are all exactly 037's; ONLY the bytes of
# sportsmuscle_body_lod5.rbm change.
#   test-040: := bat_body_deform_20k.rbm   (24,125 verts in one block)
#   test-041: := bat_body_deform_1000v.rbm (1,000 verts / 522 largest tris: under the vanilla per-block max)
# drawn in 040            -> new FILES are the problem, not the mesh
# empty in 040, drawn 041 -> a per-block size limit
# empty in both           -> something in our block content
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$lod5 = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\sportsmuscle_body_lod5.rbm'

foreach ($t in @(@{Tag='test-040'; Src='Working\Batmobile\bat_body_deform_20k.rbm'},
                 @{Tag='test-041'; Src='Working\Batmobile\bat_body_deform_1000v.rbm'})) {
    $b = "$root\Builds\$($t.Tag)"
    Write-Host "=== $($t.Tag)  lod5 := $($t.Src)"
    if (Test-Path $b) { Remove-Item $b -Recurse -Force }
    New-Item -ItemType Directory -Force -Path $b | Out-Null
    Copy-Item "$root\Builds\test-037\aaf" "$b\aaf" -Recurse -Force
    Copy-Item (Join-Path $root $t.Src) "$b\aaf\$lod5" -Force
    & "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
    if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
    python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
        --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_vehicle_parts.vmodc --include-lod `
        -o "$b\$ee.toc" 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
    foreach ($f in "$b\$ee", "$b\$ee.toc") {
        Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
    }
}

# Deploy a bat_assemble.py output onto a base build. MODLOG §73.
#   -Base test-061 -Src Working\Assembled -Tag test-062
# Src must hold body_lod1..5.rbm, wheel_<c>_lod1..5.rbm, land_global_true.vmodc and
# sportsmuscle_true.physicsc (physics_stations.py from the SAME stations.json).
# Every vanilla wheel path (incl. mshswap) gets its own corner's LOD; the .toc keeps the base's
# internal set (.epe, land_global, land_engine) -- all of them present in every true-scale base.
param(
    [Parameter(Mandatory = $true)][string]$Base,
    [Parameter(Mandatory = $true)][string]$Src,
    [Parameter(Mandatory = $true)][string]$Tag
)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$src  = Join-Path $root $Src
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir  = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$lg   = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default\v0300_car_kensington_sportsmuscle_land_global.vmodc'
$b    = "$root\Builds\$Tag"

if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\$Base\aaf" "$b\aaf" -Recurse -Force
if ((Get-Item "$b\aaf\$lg").Length -ne 1600) { throw "base $Base has no patched (1,600 B) land_global: not a true-scale base" }

$n = 0
foreach ($i in 1..5) { Copy-Item "$src\body_lod$i.rbm" "$b\aaf\$dir\sportsmuscle_body_lod$i.rbm" -Force; $n++ }
Get-ChildItem "$b\aaf\$dir" -Filter 'sportsmuscle_wheel_*_lod*.rbm' | ForEach-Object {
    if ($_.Name -notmatch '^sportsmuscle_wheel_([fr]_[lr])(mshswap)?_lod(\d)\.rbm$') { throw "unexpected wheel file $($_.Name)" }
    Copy-Item "$src\wheel_$($Matches[1])_lod$($Matches[3]).rbm" $_.FullName -Force; $n++
}
# converted textures (bat_assemble.py assembly.json: VFS path -> local .ddsc), at NEW paths:
# copied into the tree and registered in @files.xml (SmallPack drops unregistered files);
# eetoc.py then lists them before the root .epe record
$asm = "$src\assembly.json"
if (Test-Path $asm) {
    $tex = (Get-Content $asm -Raw | ConvertFrom-Json).textures
    $manifest = "$b\aaf\@files.xml"
    $xml = [IO.File]::ReadAllText($manifest)
    $t = 0
    foreach ($p in $tex.PSObject.Properties) {
        $vfs = $p.Name; $w = $vfs -replace '/', '\'
        $dst = Join-Path "$b\aaf" $w
        New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
        $from = if ([IO.Path]::IsPathRooted($p.Value)) { $p.Value } else { Join-Path $root $p.Value }
        Copy-Item $from $dst -Force
        if (-not ($xml -match [regex]::Escape("name=`"$vfs`""))) {
            $xml = $xml -replace '</files>', ("  <file name=`"$vfs`">$w</file>`r`n</files>")
        }
        $t++
    }
    [IO.File]::WriteAllText($manifest, $xml, (New-Object Text.UTF8Encoding($true)))
    Write-Host "textures added: $t"
}
$pal = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default\v0300_car_kensington_sportsmuscle_palette.vmodc'
if (Test-Path "$src\palette_true.vmodc") {
    if ((Get-Item "$src\palette_true.vmodc").Length -ne (Get-Item "$b\aaf\$pal").Length) { throw 'palette size changed' }
    Copy-Item "$src\palette_true.vmodc" "$b\aaf\$pal" -Force
    Write-Host 'palette: from the paint material scalars'
}
Copy-Item "$src\land_global_true.vmodc" "$b\aaf\$lg" -Force
Copy-Item "$src\sportsmuscle_true.physicsc" "$b\aaf\$dir\sportsmuscle.physicsc" -Force
Write-Host "meshes replaced: $n; land_global + physicsc from $Src"

& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe `
    --internal sportsmuscle_land_global.vmodc --internal sportsmuscle_land_engine.vmodc `
    -o "$b\$ee.toc" 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

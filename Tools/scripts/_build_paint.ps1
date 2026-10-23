# Repaint a build: <Base> tree + Working\Palette\palette_black.vmodc. MODLOG §55.
# The palette record is internal in the vanilla .toc and the file keeps its size, so the .toc
# only needs regenerating for the new offsets downstream (same patch flags as 043/044).
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Base
)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$pal  = 'editor\entities\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle\modules\default\v0300_car_kensington_sportsmuscle_palette.vmodc'
$b    = "$root\Builds\$Tag"

if ((Get-Item "$root\Working\Palette\palette_black.vmodc").Length -ne (Get-Item "$root\Builds\$Base\aaf\$pal").Length) {
    throw 'repainted palette is not the same size as the base palette' }
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\$Base\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Working\Palette\palette_black.vmodc" "$b\aaf\$pal" -Force

& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

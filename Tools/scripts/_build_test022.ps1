# Build test-022: the DaBaby recipe applied to the Serpente, one variable only.
#
# The Meme Vehicle Pack's DaBaby jeep (MODLOG §37) never edits a vanilla RBM. Its
# vehicle_parts.vmodc points the body part at a NEW .lod -> NEW .rbm by PATH HASH, and the
# jeep's own .physicsc (extern mesh + body_COL, same structure as ours) is left untouched.
#
# test-022 = test-003 (vanilla geometry, proven in game) plus:
#   - dababy_head.lod / dababy_head.rbm / textures/convertible.ddsc, copied verbatim from the
#     DaBaby .ee at their original VFS paths, registered in @files.xml
#   - sportsmuscle_vehicle_parts.vmodc: the single u32 at offset 312,
#     hash(".../sportsmuscle_body.lod") 0x63A04A76 -> hash(".../dababy_head.lod") 0x5EEE7AFB
#
# LOCAL TEST ONLY: the three DaBaby files are Luke JC's work. Never publish this build.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$b    = "$root\Builds\test-022"
$dab  = "$root\Research\DaBaby\aaf"
$serp = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$new  = @(
    'models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/dababy/dababy_head.lod',
    'models/jc_vehicles/01_land/v0000_car_autostraad_oldjeep/dababy/dababy_head.rbm',
    'textures/convertible.ddsc'
)

if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-003\aaf" "$b\aaf" -Recurse -Force

Write-Host '=== 1/4  add the DaBaby head files'
$manifest = "$b\aaf\@files.xml"
$xml = [IO.File]::ReadAllText($manifest)
$lines = ''
foreach ($p in $new) {
    $w = $p -replace '/', '\'
    $dst = Join-Path "$b\aaf" $w
    New-Item -ItemType Directory -Force -Path (Split-Path $dst) | Out-Null
    Copy-Item (Join-Path $dab $w) $dst -Force
    if ($xml -match [regex]::Escape("name=`"$p`"")) { throw "already registered: $p" }
    $lines += "  <file name=`"$p`">$w</file>`r`n"
}
$xml = $xml -replace '</files>', ($lines + '</files>')
[IO.File]::WriteAllText($manifest, $xml, (New-Object Text.UTF8Encoding($true)))

Write-Host '=== 2/4  repoint the body part (4 bytes)'
$vm = "$b\aaf\$serp\sportsmuscle_vehicle_parts.vmodc"
$bytes = [IO.File]::ReadAllBytes($vm)
$old = [BitConverter]::ToUInt32($bytes, 312)
if ($old -ne 0x63A04A76) { throw ('unexpected u32 at 312: 0x{0:X8}' -f $old) }
[BitConverter]::GetBytes([uint32]0x5EEE7AFB).CopyTo($bytes, 312)
[IO.File]::WriteAllBytes($vm, $bytes)
Write-Host '  0x63A04A76 -> 0x5EEE7AFB at 312'

Write-Host '=== 3/4  pack and re-unpack'
$ee = "$b\v0300_car_kensington_sportsmuscle_civilian_01.ee"
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" $ee | Out-Null
if (-not (Test-Path $ee) -or (Get-Item $ee).Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" $ee "$b\verify" | Out-Null

Write-Host '=== 4/4  prove the delta vs test-003'
$ErrorActionPreference = 'Continue'
python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-003\aaf" "$b\verify" --hash 2>&1 |
    Select-String 'only in|identical content|different content|^\s*-\s|models/|textures/' | ForEach-Object { "  $_" }
$ErrorActionPreference = 'Stop'

$size = (Get-Item $ee).Length
$sha  = (Get-FileHash $ee -Algorithm SHA256).Hash
@{ Tag = 'test-022'; Size = $size; Sha = $sha } | ConvertTo-Json | Set-Content "$b\build.json" -Encoding UTF8
Write-Host "artifact: $ee"
Write-Host "  size   $size"
Write-Host "  sha256 $sha"

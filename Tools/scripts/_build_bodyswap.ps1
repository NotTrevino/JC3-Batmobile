# Body swap on the Serpente: new .lod (+ optional new .rbm) in the body slot. MODLOG §50-51.
#
# Base: test-033's tree (patched parts vmodc, read from the .ee; it also carries the unused
# DaBaby files from test-022). Adds <Name>.lod listing <Rbm> in all five LOD slots, registers
# the new files in @files.xml, repoints the body hash at +328 of the PATCHED parts vmodc, packs,
# and writes a .toc with the parts vmodc internal and new .lod files listed.
#
#   -Tag test-038 -Name sportsmuscle_body_bat -RbmSource Working\Batmobile\bat_body_deform_20k.rbm
#   -Tag test-037 -Name sportsmuscle_body_um  -RbmVfs .../sportsmuscle_body_lod5.rbm   (existing rbm)
param(
    [Parameter(Mandatory = $true)][string]$Tag,
    [Parameter(Mandatory = $true)][string]$Name,     # file stem, placed in the Serpente folder
    [string]$RbmSource = '',                         # local .rbm to add as <Name>.rbm
    [string]$RbmVfs = ''                             # or: an rbm already in the tree
)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir  = 'models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle'
$lod  = "$dir/$Name.lod"
$b    = "$root\Builds\$Tag"
if (-not $RbmSource -and -not $RbmVfs) { throw 'give -RbmSource or -RbmVfs' }

$hashLine = & "$g\HashName.exe" $lod 2>$null | Select-String '^[0-9A-F]{8} models' | Select-Object -First 1
$hash = [Convert]::ToUInt32(($hashLine.ToString().Split(' ')[0]), 16)

if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-033\aaf" "$b\aaf" -Recurse -Force

$manifest = "$b\aaf\@files.xml"
$xml = [IO.File]::ReadAllText($manifest)
function Register($vfs) {
    $w = $vfs -replace '/', '\'
    if ($script:xml -match [regex]::Escape("name=`"$vfs`"")) { throw "already registered: $vfs" }
    $script:xml = $script:xml -replace '</files>', ("  <file name=`"$vfs`">$w</file>`r`n</files>")
}

if ($RbmSource) {
    $rbm = "$dir/$Name.rbm"
    Copy-Item (Join-Path $root $RbmSource) ("$b\aaf\" + ($rbm -replace '/', '\')) -Force
    Register $rbm
} else { $rbm = $RbmVfs }

$text = (($rbm + "`r`n") * 5) + "1.0`r`n"
[IO.File]::WriteAllText("$b\aaf\" + ($lod -replace '/', '\'), $text, (New-Object Text.ASCIIEncoding))
Register $lod
[IO.File]::WriteAllText($manifest, $xml, (New-Object Text.UTF8Encoding($true)))

$vm = "$b\aaf\" + ("$dir/sportsmuscle_vehicle_parts.vmodc" -replace '/', '\')
$bytes = [IO.File]::ReadAllBytes($vm)
if ($bytes.Length -ne 30540) { throw 'parts vmodc is not the patched 30,540 B copy' }
$old = [BitConverter]::ToUInt32($bytes, 328)
if ($old -ne 0x63A04A76) { throw ('unexpected u32 at 328: 0x{0:X8}' -f $old) }
[BitConverter]::GetBytes([uint32]$hash).CopyTo($bytes, 328)
[IO.File]::WriteAllBytes($vm, $bytes)
Write-Host ('body 0x63A04A76 -> 0x{0:X8} ({1}) at +328; lod lists {2}' -f $hash, $lod, $rbm)

& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_vehicle_parts.vmodc --include-lod `
    -o "$b\$ee.toc" 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
python -I "$root\Tools\scripts\eetoc.py" compare "$b\$ee" "$b\$ee.toc" -q 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

# test-037: does a NEW .lod in the body slot render at all? MODLOG §50.
#
# 034/035/036 load with the body slot EMPTY, whether the new .lod is listed or not and
# whether it names the DaBaby head or the Batmobile. Two candidate causes:
#   (a) a new .lod file is not resolved at all, or
#   (b) the foreign mesh (1 non-deform block, flags 0x80) is not drawn in this body slot.
#
# test-037 = test-033 tree (patched parts vmodc, internal)
#          + sportsmuscle_body_um.lod listing the Serpente's OWN sportsmuscle_body_lod5.rbm
#            (vanilla, deform, 787 tris, full 5 m shell) in all five slots
#          + body hash 0x63A04A76 -> 0x6AD11F5B (that .lod) at +328
#   crude low-poly shell appears -> (a) is fine, the cause is the foreign mesh (b)
#   body slot still empty        -> new .lod files do not resolve (a)
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$ee   = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir  = 'models/jc_vehicles/01_land/v0300_car_kensington_sportsmuscle'
$lod  = "$dir/sportsmuscle_body_um.lod"
$b    = "$root\Builds\test-037"

if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-033\aaf" "$b\aaf" -Recurse -Force

# the new .lod: vanilla CRLF text format, five rbm paths + scale
$rbm  = "$dir/sportsmuscle_body_lod5.rbm"
$text = (($rbm + "`r`n") * 5) + "1.0`r`n"
$lodw = $lod -replace '/', '\'
[IO.File]::WriteAllText("$b\aaf\$lodw", $text, (New-Object Text.ASCIIEncoding))
$manifest = "$b\aaf\@files.xml"
$xml = [IO.File]::ReadAllText($manifest)
if ($xml -match [regex]::Escape("name=`"$lod`"")) { throw "already registered: $lod" }
$xml = $xml -replace '</files>', ("  <file name=`"$lod`">$lodw</file>`r`n</files>")
[IO.File]::WriteAllText($manifest, $xml, (New-Object Text.UTF8Encoding($true)))

$vm = "$b\aaf\" + ("$dir/sportsmuscle_vehicle_parts.vmodc" -replace '/', '\')
$bytes = [IO.File]::ReadAllBytes($vm)
if ($bytes.Length -ne 30540) { throw 'parts vmodc is not the patched 30,540 B copy' }
$old = [BitConverter]::ToUInt32($bytes, 328)
if ($old -ne 0x63A04A76) { throw ('unexpected u32 at 328: 0x{0:X8}' -f $old) }
[BitConverter]::GetBytes([uint32]0x6AD11F5B).CopyTo($bytes, 328)
[IO.File]::WriteAllBytes($vm, $bytes)
Write-Host 'body 0x63A04A76 -> 0x6AD11F5B (sportsmuscle_body_um.lod) at +328'

& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
python -I "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_vehicle_parts.vmodc --include-lod `
    -o "$b\$ee.toc" 2>&1 | Where-Object { $_ -notmatch 'Warning|warnings.warn' }
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

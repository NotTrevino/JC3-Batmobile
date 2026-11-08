# Sweep tumbler-carve parameters: displace the donor tree, then render the RESULT.
#
# The preview must be taken of the written output, not of the inputs, or every variant
# looks identical.
#
# It renders sportsmuscle_body_lod1 -- the shell -- rather than the whole 160-part
# vehicle. Two reasons: that block is where the Tumbler silhouette actually has to
# change, and it is also the block the 1024-vertex / 3168-index constraint the user is
# working around lives in. The merged 160-part triangle render takes ~64 s; the shell
# alone is under a second and far more legible than the point-splat fallback.
#
# Usage:
#   powershell -File _sweep_tumbler.ps1 g040 "guard=0.40;top_pct=99.5"
#
# Pairs are semicolon-separated in one string on purpose: `powershell -File` does not
# parse PowerShell syntax in its arguments, so `-Params 'a','b'` arrives as the single
# literal "'a','b'" and `-p a -p b` silently binds to this script's own `-Params`.
param(
  [Parameter(Mandatory=$true)][string]$Name,
  [string]$Kv = ''
)

$ErrorActionPreference = 'Stop'
$scripts = 'E:\Modding\JC3-Batmobile\Tools\scripts'
$w       = 'E:\Modding\JC3-Batmobile\Working\Tumbler'
$psk     = 'E:\Modding\_gamedata\bmak_early\Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx'
$files   = Get-Content "$w\parts.txt"
$out     = "$w\$Name"
$donor   = 'E:\Modding\_gamedata\jc3_early\SerpenteR-EE\models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'

Set-Location $scripts
$flag = @()
foreach ($p in ($Kv -split ';' | Where-Object { $_ -ne '' })) { $flag += @('-p', $p) }

Write-Host "=== $Name   $Kv"
$log = python rbm_geom.py displace @files --profile tumbler --cloud $psk -o $out @flag 2>&1
$log | Select-String -Pattern 'ORACLE FAILED' | ForEach-Object { Write-Host "  !! $_" }
$log | Select-String -Pattern 'ORACLE PASS' | Measure-Object | ForEach-Object { Write-Host "  oracle pass : $($_.Count)" }
$log | Select-String -Pattern 'target extent' | ForEach-Object { Write-Host "  $_".Trim() }

# row 0 = the vanilla shell for reference, row 1 = this variant
python rbm_geom.py preview "$donor\sportsmuscle_body_lod1.rbm" "$out\sportsmuscle_body_lod1.rbm" `
    -o "$w\sh_$Name.png" --color-blocks 2>&1 |
    Select-String -Pattern 'body_lod1' | ForEach-Object { Write-Host "  $_".Trim() }
Write-Host "  wrote $w\sh_$Name.png"

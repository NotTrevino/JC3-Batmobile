# Build test-020: the Batmobile-envelope reshape, packaged as a .ee.
#
# Provenance: test-020 is test-010 with the same 160 files touched and the same two
# non-geometry changes inherited (the Mugello body texture from test-003/test-010). The
# ONLY difference from test-010 is the 160 RBM byte streams. That is deliberate: test-010
# is a known-good in-game result, so if test-020 crashes, the delta is exactly the new
# displacement and nothing else.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File _build_tumbler.ps1 -Variant sk10 -Kv "guard=0.40;..."
param(
  [string]$Variant = 'sk10',
  [string]$Kv      = 'guard=0.40;top_pct=99;h_clip=0;pinch=0.85;skirt=0.10',
  [string]$Tag     = 'test-020'
)

$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$g    = "$root\Tools\Gibbed"
$w    = "$root\Working\Tumbler"
$psk  = "$root\Playable_Batmobile_SF\SkeletalMesh3\Batmobile_V2.pskx"
$donorRel = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'

# 1 ---------------------------------------------------------------- displace
Set-Location "$root\Tools\scripts"
$files = Get-Content "$w\parts.txt"
$stage = "$w\_stage"
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }

Write-Host '=== 1/5  displace (this is the oracle gate)'
$flag = @(); foreach ($p in ($Kv -split ';' | Where-Object { $_ -ne '' })) { $flag += @('-p', $p) }
$log = python rbm_geom.py displace @files --profile tumbler --cloud $psk -o $stage @flag 2>&1
$pass = ($log | Select-String 'ORACLE PASS').Count
$fail = ($log | Select-String 'ORACLE FAILED')
if ($fail) { $fail | ForEach-Object { Write-Host "  !! $_" }; throw 'oracle failed -- refusing to package' }
$written = (Get-ChildItem $stage -Filter *.rbm).Count
Write-Host "  $pass / $written ORACLE PASS"

Write-Host '=== 2/5  round-trip every written file'
$rt = python rbm_geom.py roundtrip "$stage\*.rbm" 2>&1 | Select-String 'byte-identical'
Write-Host "  $rt"

# 3 ------------------------------------------------------------ stage the tree
Write-Host "=== 3/5  stage into $Tag\aaf (from test-010, so only the RBMs differ)"
$b = "$root\Builds\$Tag"
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-010\aaf" "$b\aaf" -Recurse -Force
$n = 0
Get-ChildItem $stage -Filter *.rbm | ForEach-Object {
    $dst = Join-Path "$b\aaf\$donorRel" $_.Name
    if (-not (Test-Path $dst)) { throw "manifest has no place for $($_.Name)" }
    Copy-Item $_.FullName $dst -Force
    $n++
}
Write-Host "  overlaid $n RBMs"
Copy-Item "$w\parts.txt" "$b\parts.txt" -Force

# 4 ------------------------------------------------------------------- pack
Write-Host '=== 4/5  pack and re-unpack'
$ee = "$b\v0300_car_kensington_sportsmuscle_civilian_01.ee"
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" $ee | Out-Null
if (-not (Test-Path $ee)) { throw 'pack produced nothing' }
if (Test-Path "$b\verify") { Remove-Item "$b\verify" -Recurse -Force }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" $ee "$b\verify" | Out-Null
$size = (Get-Item $ee).Length
$sha  = (Get-FileHash $ee -Algorithm SHA256).Hash
Write-Host "  packed $size B  sha256 $sha"

Write-Host '=== 5/5  prove the delta is only the 160 RBMs'
# aafdiff writes its report to stderr, which PowerShell surfaces as NativeCommandError
# and $ErrorActionPreference='Stop' would turn into a terminating failure. Relax it for
# these two calls only.
$ErrorActionPreference = 'Continue'
Write-Host '-- vs test-010 (same base, new displacement):'
python aafdiff.py "$root\Builds\test-010\aaf" "$b\verify" --hash 2>&1 |
    Select-String 'only in|identical content|different content' | ForEach-Object { "  $_" }
Write-Host '-- vs test-003 (the proven in-game good build):'
python aafdiff.py "$root\Builds\test-003\aaf" "$b\verify" --hash 2>&1 |
    Select-String 'only in|identical content|different content' | ForEach-Object { "  $_" }
$ErrorActionPreference = 'Stop'

@{ Tag = $Tag; Kv = $Kv; Size = $size; Sha = $sha; Oracle = "$pass/$written" } |
    ConvertTo-Json | Set-Content "$b\build.json" -Encoding UTF8
Write-Host ''
Write-Host "artifact: $ee"
Write-Host "  size   $size"
Write-Host "  sha256 $sha"

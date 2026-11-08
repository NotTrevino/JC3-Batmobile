# test-056: magenta lows discriminator (which texture path is live?).
# Base = test-055 tree; ONLY v0300..._body_dif.ddsc swapped for the all-magenta
# build (same size, header-identical). .toc regenerates byte-identical to 055's.
# Oracle: pink everywhere -> the .ee shadows all mips (D13 confirmed, 256 cap);
# pink only far -> highs come from game36 .hmddsc (author highs next).
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JustCause3\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$tex = "$dir\textures\v0300_car_kensington_sportsmuscle_body_dif.ddsc"

$b = "$root\Builds\test-056"
Write-Host '=== test-056 (magenta lows discriminator)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-055\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Working\TexProbe\mag\body_dif.ddsc.ddsc" "$b\aaf\$($tex -replace '/', '\')" -Force
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe --internal sportsmuscle_land_global.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
$a = (Get-FileHash "$b\$ee.toc").Hash; $r = (Get-FileHash "$root\Builds\test-055\$ee.toc").Hash
if ($a -ne $r) { throw 'test-056 .toc differs from 055' }
& $py run python "$root\Tools\scripts\_make_installer.py" test-056 "Magenta body_dif lows (texture-path discriminator)" test-055 "RAY quads moved to stance stations (physics matches visuals)" test-053 "Stance reverted to RAY stations, mirrored L/R wheels kept" test-045 "CLEAN plain Batmobile + black palette" test-003 "vanilla geometry, no .toc"
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
& $py run python "$root\Tools\scripts\aafdiff.py" "$root\Builds\test-055\aaf" "$b\verify" --hash 2>&1 | Select-Object -First 4
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

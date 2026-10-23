# test-057: magenta FULL chain (all 12 mips) in the .ee body_dif.ddsc.
# Base = test-056 tree; ONLY body_dif.ddsc changes (43,832 -> 2,796,344 B).
# Oracle: pink everywhere -> the .ee shadows all mips (full-chain .ddsc is the
# whole texture story); vanilla-near persists -> highs come from elsewhere
# (.hmddsc preferred) and full-chain shadowing does not apply.
$ErrorActionPreference = 'Stop'
$root = 'E:\Modding\JC3-Batmobile'
$py = 'uv'
$g  = "$root\Tools\Gibbed"
$ee = 'v0300_car_kensington_sportsmuscle_civilian_01.ee'
$dir = 'models\jc_vehicles\01_land\v0300_car_kensington_sportsmuscle'
$tex = "$dir\textures\v0300_car_kensington_sportsmuscle_body_dif.ddsc"

$b = "$root\Builds\test-057"
Write-Host '=== test-057 (magenta full chain)'
if (Test-Path $b) { Remove-Item $b -Recurse -Force }
New-Item -ItemType Directory -Force -Path $b | Out-Null
Copy-Item "$root\Builds\test-056\aaf" "$b\aaf" -Recurse -Force
Copy-Item "$root\Working\TexProbe\magfull\body_dif.ddsc.ddsc" "$b\aaf\$($tex -replace '/', '\')" -Force
& "$g\Gibbed.JustCause3.SmallPack.exe" "$b\aaf" "$b\$ee" | Out-Null
if (-not (Test-Path "$b\$ee") -or (Get-Item "$b\$ee").Length -eq 0) { throw 'pack produced nothing' }
& "$g\Gibbed.JustCause3.SmallUnpack.exe" "$b\$ee" "$b\verify" | Out-Null
& $py run python "$root\Tools\scripts\eetoc.py" patch "$b\$ee" "$root\Research\SerpenteToc\vanilla_civilian_01.ee.toc" `
    --base-ee "$root\Builds\test-003\$ee" --internal sportsmuscle_civilian_01.epe --internal sportsmuscle_land_global.vmodc -o "$b\$ee.toc" 2>&1 |
    Where-Object { $_ -notmatch 'Warning|warnings.warn' }
& $py run python "$root\Tools\scripts\_make_installer.py" test-057 "Magenta full-chain body_dif (.ee shadows all mips?)" test-056 "Magenta body_dif lows (texture-path discriminator)" test-055 "RAY quads moved to stance stations (physics matches visuals)" test-053 "Stance reverted to RAY stations, mirrored L/R wheels kept" test-003 "vanilla geometry, no .toc"
foreach ($f in "$b\$ee", "$b\$ee.toc") {
    Write-Host ('  {0,9} B  {1}  {2}' -f (Get-Item $f).Length, (Get-FileHash $f).Hash, (Split-Path $f -Leaf))
}

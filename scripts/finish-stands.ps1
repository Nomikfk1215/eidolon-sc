# 等指定的素材拉取容器结束，然后生成衣装清单和缩略图。
param([Parameter(Mandatory = $true)][string]$ContainerName)
$repo = Split-Path -Parent $PSScriptRoot
$log  = "$repo\logs\stands-finish.log"
$container = $ContainerName
New-Item -ItemType Directory -Force (Join-Path $repo "logs") | Out-Null

function Log($m) { "$(Get-Date -Format 'HH:mm:ss') $m" | Add-Content -Path $log -Encoding utf8 }

Set-Location $repo
Log "waiting for $container"

# 容器在 --rm 下跑完会消失，所以轮询 Running 状态而不是 docker wait
while ($true) {
    $running = $null
    try { $running = (docker inspect -f '{{.State.Running}}' $container 2>$null) } catch { $running = $null }
    if ($running -ne 'true') { break }
    Start-Sleep -Seconds 30
}
Log "fetch finished"

docker compose run --rm -T -v "$repo\corpus\stand:/stands" backend eidolon stand outfits --build /stands *>> $log
Log "outfits exit=$LASTEXITCODE"

Set-Location "$repo\frontend"
npm.cmd run stand:thumbnails -- --build ../corpus/stand *>> $log
Log "thumbnails exit=$LASTEXITCODE"

Set-Location $repo
$files = (Get-ChildItem "$repo\corpus\stand" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum)
Log ("done: {0} files, {1:N1} MB" -f $files.Count, ($files.Sum / 1MB))

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.env')) { & (Join-Path $PSScriptRoot 'Preparar.ps1') }
& docker info *> $null
if ($LASTEXITCODE -ne 0) { throw 'Abra o Docker Desktop e aguarde informar que esta em funcionamento. Depois execute este arquivo novamente.' }
& docker compose up -d --build
if ($LASTEXITCODE -ne 0) { throw 'Falha ao iniciar. Consulte docker compose logs --tail 30.' }
$ready = $false
for ($i = 0; $i -lt 60; $i++) {
    try { $health = Invoke-RestMethod 'http://127.0.0.1:8090/health'; $ready = $health.status -eq 'ok' } catch {}
    if ($ready) { break }
    Start-Sleep -Seconds 3
}
if (-not $ready) { throw 'Os servicos ainda nao ficaram prontos. Consulte docker compose logs fila.' }
Write-Host 'Fila pronta em modo de simulacao (salvo alteracao explicita no .env).'
Write-Host 'Execute Operar.ps1 para revisar contatos e simular.'
Write-Host 'Editor de automacao: http://localhost:5678'
Write-Host 'Evolution: http://localhost:8080/manager'

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
& docker compose stop
if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel parar os servicos.' }
Write-Host 'Servicos parados. Dados e conversas preservados.'

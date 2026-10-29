$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.env')) {
    $lines = @()
    foreach ($name in @('POSTGRES_PASSWORD','EVOLUTION_API_KEY','N8N_ENCRYPTION_KEY','ADMIN_KEY','WEBHOOK_SECRET')) {
        $bytes = New-Object byte[] 32
        $rng = [Security.Cryptography.RandomNumberGenerator]::Create()
        $rng.GetBytes($bytes)
        $rng.Dispose()
        $secret = -join ($bytes | ForEach-Object { $_.ToString('x2') })
        $lines += "$name=$secret"
    }
    $lines += 'LIVE_SEND_ENABLED=false'
    [IO.File]::WriteAllLines((Join-Path $PSScriptRoot '.env'), $lines)
    Write-Host 'Credenciais locais geradas. Guarde o arquivo .env junto dos backups.'
} else { Write-Host 'Credenciais existentes preservadas.' }
& docker compose config --quiet
if ($LASTEXITCODE -ne 0) { throw 'Docker/Compose indisponivel ou configuracao invalida.' }
Write-Host 'Preparacao concluida. Execute Iniciar.ps1 no computador definitivo.'

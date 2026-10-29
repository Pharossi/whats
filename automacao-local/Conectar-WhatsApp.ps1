$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$config = @{}
Get-Content -LiteralPath '.env' | ForEach-Object { if ($_ -match '^([A-Z_]+)=(.*)$') { $config[$matches[1]] = $matches[2] } }
$headers = @{apikey=$config['EVOLUTION_API_KEY']}
$instances = @(Invoke-RestMethod 'http://127.0.0.1:8080/instance/fetchInstances' -Headers $headers)
if (-not ($instances | Where-Object { $_.name -eq 'crescer' -or $_.instance.instanceName -eq 'crescer' })) {
    $body = @{instanceName='crescer';integration='WHATSAPP-BAILEYS';qrcode=$true} | ConvertTo-Json
    Invoke-RestMethod 'http://127.0.0.1:8080/instance/create' -Method Post -Headers $headers -ContentType 'application/json' -Body $body | Out-Null
}
$connection = Invoke-RestMethod 'http://127.0.0.1:8080/instance/connect/crescer' -Headers $headers
if ($connection.base64) {
    $target = Join-Path $PSScriptRoot 'qr-whatsapp.png'
    [IO.File]::WriteAllBytes($target,[Convert]::FromBase64String(($connection.base64 -replace '^data:image/[^;]+;base64,','')))
    Write-Host "QR temporario salvo em $target. Abra a imagem e leia em WhatsApp > Aparelhos conectados."
    Write-Host 'Se expirar, execute este arquivo novamente. Nao compartilhe a imagem.'
} else { Write-Host 'Sem QR disponivel. Consulte o estado da instancia no Evolution Manager.' }
Write-Host 'Conectar o numero nao habilita os envios reais.'

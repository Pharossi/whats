$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$config = @{}
Get-Content -LiteralPath '.env' | ForEach-Object {
    if ($_ -match '^([A-Z_]+)=(.*)$') { $config[$matches[1]] = $matches[2] }
}
$headers = @{ 'X-Api-Key' = $config['ADMIN_KEY'] }
function Request-Local($path, $body = $null) {
    if ($null -eq $body) { return Invoke-RestMethod ("http://127.0.0.1:8090" + $path) -Headers $headers }
    $json = $body | ConvertTo-Json -Depth 10
    return Invoke-RestMethod ("http://127.0.0.1:8090" + $path) -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($json))
}
while ($true) {
    Write-Host "`n1 - Ver contatos | 2 - Revisar contato | 3 - Simular proximo | 4 - Ver respostas | 0 - Sair"
    $option = Read-Host 'Escolha'
    try {
        switch ($option) {
            '1' { Request-Local '/contacts' | Select-Object id,company,city,phone,reviewed,paused,opted_out | Format-Table -AutoSize }
            '2' {
                $id = [int](Read-Host 'ID do contato')
                $contact = @(Request-Local '/contacts') | Where-Object { $_.id -eq $id } | Select-Object -First 1
                if (-not $contact) { throw 'ID nao consta na lista atual.' }
                $contact | Select-Object company,city,phone,source | Format-List
                if ((Read-Host 'Conferiu que este numero pertence a empresa? Digite SIM') -cne 'SIM') { continue }
                $consent = Read-Host 'Onde e quando o destinatario autorizou o contato? (vazio cancela)'
                if ([string]::IsNullOrWhiteSpace($consent)) { continue }
                $draft = Read-Host 'Digite a mensagem revisada, identificando voce e a Crescer Capital'
                if ([string]::IsNullOrWhiteSpace($draft)) { continue }
                Request-Local '/review' @{contact_id=$id;verified=$true;consent_source=$consent;draft=$draft} | Format-List
            }
            '3' { Request-Local '/dispatch' @{live=$false} | Format-List }
            '4' { Request-Local '/inbox' | Select-Object created_at,phone,text,classification | Format-List }
            '0' { return }
        }
    } catch { Write-Host ('Nao foi possivel concluir: ' + $_.Exception.Message) -ForegroundColor Yellow }
}

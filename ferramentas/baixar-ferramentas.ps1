<#
    Sistema2D SM-T225 - baixa as ferramentas de terceiros

    Este projeto NAO redistribui software proprietario da Samsung nem o SDK do
    Google. Este script busca cada item na fonte oficial e confere o SHA-256
    contra a versao com que o projeto foi de fato testado - se o fornecedor
    publicar outra build, voce fica sabendo em vez de descobrir depois.

    O TWRP e o Magisk sao abertos e estao na release do repositorio, nas builds
    exatas usadas. Nao precisam deste script.

    Uso:
        .\baixar-ferramentas.ps1
        .\baixar-ferramentas.ps1 -Destino "D:\SM-T225"
#>

[CmdletBinding()]
param(
    [string]$Destino = "$PSScriptRoot\baixados"
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'   # acelera muito o Invoke-WebRequest

# Hashes conferidos em 28/08/2026, no ambiente em que a ROM foi construida.
$Itens = @(
    @{
        Nome  = 'platform-tools-latest-windows.zip'
        Url   = 'https://dl.google.com/android/repository/platform-tools-latest-windows.zip'
        Sha   = '45f4d63113e895ebde0c90f194099a4676b6ac653bd28d54314a9e022bbc1a99'
        Sobre = 'ADB e Fastboot oficiais do Google'
        Movel = $true    # o Google atualiza esta URL; divergencia e esperada
    }
)

# Itens sem download direto estavel: exigem a pagina do fornecedor.
$Manuais = @(
    @{
        Nome  = 'Odin3 v3.14.4'
        Onde  = 'https://odindownload.com/  (ou XDA)'
        Sha   = 'bafdbf3948f8e1d8752716ada84485c1a42fcf3fd5dc0b119cecb024e0813505'
        Sobre = 'Ferramenta da Samsung para o Modo Download. Proprietaria - nao redistribuida.'
    },
    @{
        Nome  = 'SAMSUNG USB Driver for Mobile Phones'
        Onde  = 'https://developer.samsung.com/android-usb-driver'
        Sha   = '0ecc9e47d836a7cff7215ec9cdf33dc7f3e416a7d5ededad522b978b2eb84a20'
        Sobre = 'Sem ele o Windows nao enxerga o Modo Download.'
    },
    @{
        Nome  = 'Firmware de fabrica T225XXSBEYE1 (ZTO)'
        Onde  = 'https://samfw.com/firmware/SM-T225  (~6 GB)'
        Sha   = '(varia por CSC - confira o build T225XXSBEYE1)'
        Sobre = 'So e necessario para voltar ao estoque. Proprietario da Samsung.'
    },
    @{
        Nome  = 'GSI lineage-21.0-arm64_bgN.img.gz'
        Onde  = 'veja as notas da release do repositorio'
        Sha   = '2b0141d22271d38dcc9a1f5116deb50f8b8abc9af7480216f24edba0fc0fed5d'
        Sobre = 'A base do sistema. Trabalho do LineageOS/TrebleDroid, nao deste projeto.'
    }
)

function Confere-Sha {
    param([string]$Arquivo, [string]$Esperado, [bool]$Movel)
    $real = (Get-FileHash -Path $Arquivo -Algorithm SHA256).Hash.ToLower()
    if ($real -eq $Esperado) {
        Write-Host "    sha256 confere" -ForegroundColor Green
        return $true
    }
    if ($Movel) {
        Write-Host "    sha256 diferente do testado (esperado para esta URL)" -ForegroundColor Yellow
        Write-Host "      testado: $Esperado" -ForegroundColor DarkGray
        Write-Host "      baixado: $real" -ForegroundColor DarkGray
        return $true
    }
    Write-Host "    SHA-256 NAO CONFERE" -ForegroundColor Red
    Write-Host "      esperado: $Esperado" -ForegroundColor DarkGray
    Write-Host "      obtido:   $real" -ForegroundColor DarkGray
    return $false
}

New-Item -ItemType Directory -Force -Path $Destino | Out-Null

Write-Host ''
Write-Host 'Sistema2D SM-T225 - ferramentas de terceiros' -ForegroundColor Cyan
Write-Host '============================================='
Write-Host "destino: $Destino"
Write-Host ''

$falhas = 0
foreach ($item in $Itens) {
    $alvo = Join-Path $Destino $item.Nome
    Write-Host "[baixando] $($item.Nome)" -ForegroundColor White
    Write-Host "    $($item.Sobre)" -ForegroundColor DarkGray
    if (Test-Path $alvo) {
        Write-Host "    ja existe, pulando download" -ForegroundColor DarkGray
    } else {
        try {
            Invoke-WebRequest -Uri $item.Url -OutFile $alvo -UseBasicParsing
        } catch {
            Write-Host "    FALHOU: $($_.Exception.Message)" -ForegroundColor Red
            $falhas++
            continue
        }
    }
    if (-not (Confere-Sha -Arquivo $alvo -Esperado $item.Sha -Movel ([bool]$item.Movel))) { $falhas++ }
    Write-Host ''
}

Write-Host 'Estes precisam ser baixados na mao:' -ForegroundColor Yellow
Write-Host ''
foreach ($m in $Manuais) {
    Write-Host "  $($m.Nome)" -ForegroundColor White
    Write-Host "    $($m.Sobre)" -ForegroundColor DarkGray
    Write-Host "    onde  : $($m.Onde)"
    Write-Host "    sha256: $($m.Sha)" -ForegroundColor DarkGray
    Write-Host ''
}

Write-Host 'TWRP e Magisk estao na release do repositorio:' -ForegroundColor Cyan
Write-Host '  https://github.com/Sistema2D/SM-T225/releases'
Write-Host ''

if ($falhas -gt 0) {
    Write-Host "$falhas item(ns) com problema. Nao prossiga sem resolver." -ForegroundColor Red
    exit 1
}
Write-Host 'Pronto. Siga o INSTALL.md a partir do passo 1.' -ForegroundColor Green

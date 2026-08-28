<#
    Sistema2D - Reverte os ajustes de aplicar-ajustes.ps1
    Devolve o aparelho aos valores medidos na auditoria de 28/08/2026,
    ANTES das mudancas (ver ..\30-BASELINE\).

    Nao mexe no modulo sistema2d_tweaks. Para desfazer aquele:
        adb shell rm -rf /data/adb/modules/sistema2d_tweaks
        adb shell 'resetprop persist.traced.enable 1'
        adb reboot
#>

$ErrorActionPreference = 'Stop'
$adb = 'C:\Users\meloha\Desktop\Triar 1\UAD\platform-tools\adb.exe'

if (-not (Test-Path $adb)) { throw "adb nao encontrado em $adb" }

$estado = & $adb get-state 2>&1
if ($estado -notmatch 'device') { throw "Nenhum aparelho conectado (adb get-state: $estado)" }

Write-Host ''
Write-Host 'Sistema2D - revertendo ajustes' -ForegroundColor Cyan
Write-Host '=============================='

Write-Host '[V1] densidade -> 220 dpi (valor original medido; note que isso'
Write-Host '     REMOVE a taskbar e os layouts de tablet)'
& $adb shell wm density 220 | Out-Null

Write-Host '[V4] escalas de animacao -> 0,75'
& $adb shell settings put global window_animation_scale 0.75     | Out-Null
& $adb shell settings put global transition_animation_scale 0.75 | Out-Null
& $adb shell settings put global animator_duration_scale 0.75    | Out-Null

Write-Host '[V5] escala de fonte -> 1,0'
& $adb shell settings put system font_scale 1.0 | Out-Null

Write-Host '[V5] modo escuro -> sempre ligado'
& $adb shell settings put secure ui_night_mode 2 | Out-Null

Write-Host ''
Write-Host 'Revertido.' -ForegroundColor Green
Write-Host 'A grade do launcher NAO volta sozinha para 5x5: ela migrou para 6x5'
Write-Host 'porque a densidade mudou. Se quiser 5x5 de novo, ajuste em'
Write-Host 'Estilo e papel de parede > Grade da tela inicial.'
Write-Host ''

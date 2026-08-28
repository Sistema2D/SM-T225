<#
    Sistema2D - Ajustes de interface e desempenho
    Alvo: Galaxy Tab A7 Lite SM-T225 rodando a GSI TrebleDroid/LineageOS 21.

    Aplica os ajustes que vivem em "settings" e nao em arquivos de ROM, entao
    precisam ser reaplicados depois de um wipe de /data. O que e persistente
    via Magisk (Perfetto desligado) esta no modulo sistema2d_tweaks e NAO
    precisa deste script.

    Uso:  .\aplicar-ajustes.ps1
    Desfazer: .\reverter-ajustes.ps1
#>

$ErrorActionPreference = 'Stop'
$adb = 'C:\Users\meloha\Desktop\Triar 1\UAD\platform-tools\adb.exe'

if (-not (Test-Path $adb)) { throw "adb nao encontrado em $adb" }

$estado = & $adb get-state 2>&1
if ($estado -notmatch 'device') { throw "Nenhum aparelho conectado (adb get-state: $estado)" }

Write-Host ''
Write-Host 'Sistema2D - aplicando ajustes' -ForegroundColor Cyan
Write-Host '=============================='

# --- V1: densidade -----------------------------------------------------------
# A tela tem 800 px de largura. A densidade define quantos dp isso vale, e o
# Android so ativa os layouts de tela grande a partir de 600 dp:
#     220 dpi -> 582 dp  (layout de TELEFONE: sem taskbar, sem duas colunas)
#     213 dpi -> 601 dp  (passa raspando)
#     200 dpi -> 640 dp  (folga confortavel)  <-- escolhido
# Efeito colateral desejado: o Launcher3 migra sozinho para a grade 6x5 e a
# Taskbar de tablet passa a existir.
Write-Host '[V1] densidade -> 200 dpi (640 dp, libera a interface de tablet)'
& $adb shell wm density 200 | Out-Null

# --- V4: animacoes -----------------------------------------------------------
# Estavam em 0,75. O proprio projeto pretendia 0,5 e nunca aplicou.
Write-Host '[V4] escalas de animacao -> 0,5'
& $adb shell settings put global window_animation_scale 0.5     | Out-Null
& $adb shell settings put global transition_animation_scale 0.5 | Out-Null
& $adb shell settings put global animator_duration_scale 0.5    | Out-Null

# --- V5: leitura -------------------------------------------------------------
# A queda de 220 para 200 dpi encolhe o texto em ~10%. Compensar pela FONTE, e
# nunca voltando a densidade, e o que preserva os layouts de tablet.
Write-Host '[V5] escala de fonte -> 1,05 (compensa a queda de densidade)'
& $adb shell settings put system font_scale 1.05 | Out-Null

# Modo escuro estava fixo em "sempre". Em LCD isso nao economiza bateria como
# em AMOLED. 0 = automatico por horario. Este e um ajuste de GOSTO: se voce
# prefere escuro o tempo todo, rode reverter-ajustes.ps1 ou apenas:
#     adb shell settings put secure ui_night_mode 2
Write-Host '[V5] modo escuro -> automatico por horario'
& $adb shell settings put secure ui_night_mode 0 | Out-Null

Write-Host ''
Write-Host 'Aplicado. Confira com:' -ForegroundColor Green
Write-Host '    adb shell am get-config'
Write-Host '    (deve mostrar sw640dp e 200dpi)'
Write-Host ''
Write-Host 'NAO automatizavel neste aparelho:' -ForegroundColor Yellow
Write-Host '  P2  O Play Store esta na allowlist "system-excidle" do sistema, entao'
Write-Host '      am set-standby-bucket e ignorado silenciosamente (o bucket volta'
Write-Host '      para 5 = EXEMPTED). Para reduzir os ~131 MB dele, o caminho e'
Write-Host '      manual: Play Store > Configuracoes > Preferencias de rede >'
Write-Host '      Atualizar apps automaticamente > Nao atualizar automaticamente.'
Write-Host '  V5  Esta build do LineageOS 21 nao expoe ajuste para ocultar o texto'
Write-Host '      de operadora ("Sem chip") na tela de bloqueio - a chave nao existe'
Write-Host '      nem em settings nem no provider lineagesettings.'
Write-Host ''

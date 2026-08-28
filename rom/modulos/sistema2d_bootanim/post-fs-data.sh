#!/system/bin/sh

MODDIR="${0%/*}"
LOG="$MODDIR/brightness_boot.log"
SPLASH="$MODDIR/splash_fb0.raw"
FB=/dev/graphics/fb0

# ---------------------------------------------------------------------------
# 1) Preenche a tela preta do boot.
#
# Cronologia medida neste aparelho (ro.boottime.*):
#     ~13,8 s  o bootloader some com a tela SAMSUNG
#      22,5 s  surfaceflinger
#      31,2 s  bootanimation comeca a desenhar
#
# Entre o bootloader sair e a animacao entrar ninguem desenha, e o painel fica
# preto. Aqui despejamos a mesma tela SAMSUNG direto no framebuffer, bem antes
# do surfaceflinger existir.
#
# Reescreve ate a BOOTANIM assumir, nao ate o surfaceflinger subir. Medido:
# o surfaceflinger sobe aos 22,5 s mas a bootanim so desenha aos 31,1 s - sao
# 8,6 s com o SF de pe e ninguem desenhando. Parar no surfaceflinger deixava
# exatamente esse vazio preto. Custa ~13 ms por passada e para sozinho.
# ---------------------------------------------------------------------------
(
  if [ -r "$SPLASH" ] && [ -w "$FB" ]; then
    dd if="$SPLASH" of="$FB" bs=4M 2>/dev/null
    n=0
    while [ "$n" -lt 45 ] \
       && [ "$(getprop init.svc.bootanim)" != "running" ] \
       && [ "$(getprop sys.boot_completed)" != "1" ]; do
      sleep 1
      dd if="$SPLASH" of="$FB" bs=4M 2>/dev/null
      n=$((n + 1))
    done
    echo "splash: passadas=$((n + 1)) sf=$(getprop init.svc.surfaceflinger) bootanim=$(getprop init.svc.bootanim)" >> "$LOG"
  else
    echo "splash: indisponivel (raw=$([ -r "$SPLASH" ] && echo ok || echo nao) fb=$([ -w "$FB" ] && echo ok || echo nao))" >> "$LOG"
  fi
) &

# ---------------------------------------------------------------------------
# 2) Mantem o backlight no maximo durante a fase Android do boot.
# O bootloader anterior ao kernel nao e alterado. O laco e assincrono para nao
# bloquear o boot e termina assim que sys.boot_completed e publicado.
# ---------------------------------------------------------------------------
(
  round=0
  : > "$LOG"
  while [ "$round" -lt 140 ] && [ "$(getprop sys.boot_completed)" != "1" ]; do
    for node in /sys/class/leds/lcd-backlight /sys/class/leds/mt6370_pmu_bled; do
      if [ -r "$node/max_brightness" ] && [ -w "$node/brightness" ]; then
        maximum="$(cat "$node/max_brightness" 2>/dev/null)"
        case "$maximum" in *[!0-9]*|'') ;; *) echo "$maximum" > "$node/brightness" ;; esac
      fi
    done
    if [ "$round" -eq 0 ]; then
      echo "started=$(date +%s) lcd=$(cat /sys/class/leds/lcd-backlight/brightness 2>/dev/null) pmic=$(cat /sys/class/leds/mt6370_pmu_bled/brightness 2>/dev/null)" >> "$LOG"
    fi
    round=$((round + 1))
    sleep 0.5
  done

  # Devolve o controle ao ajuste escolhido pelo usuario quando o Android termina.
  selected="$(settings get system screen_brightness 2>/dev/null)"
  case "$selected" in
    *[!0-9]*|'') ;;
    *)
      for node in /sys/class/leds/lcd-backlight /sys/class/leds/mt6370_pmu_bled; do
        [ -w "$node/brightness" ] && echo "$selected" > "$node/brightness"
      done
      ;;
  esac
  sleep 0.2
  echo "finished=$(date +%s) rounds=$round restored=$selected lcd=$(cat /sys/class/leds/lcd-backlight/brightness 2>/dev/null) pmic=$(cat /sys/class/leds/mt6370_pmu_bled/brightness 2>/dev/null)" >> "$LOG"
) &

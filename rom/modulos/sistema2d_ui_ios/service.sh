#!/system/bin/sh

# Ativa os overlays do visual iOS. Idempotente: em instalacao limpa o /data
# nao tem estado de overlay, entao a ROM precisa liga-los sozinha para o visual
# ja vir aplicado sem o usuario mexer em nada.

round=0
while [ "$(getprop sys.boot_completed)" != "1" ] && [ "$round" -lt 180 ]; do
  sleep 2
  round=$((round + 1))
done
sleep 4

# A forma de icone e exclusiva por categoria: ligar a nossa desliga a squircle.
cmd overlay enable --user 0 com.sistema2d.theme.icon.ios >/dev/null 2>&1
cmd overlay enable --user 0 com.sistema2d.theme.corners  >/dev/null 2>&1
cmd overlay enable --user 0 com.sistema2d.theme.taskbar  >/dev/null 2>&1
cmd overlay enable --user 0 com.sistema2d.theme.settings >/dev/null 2>&1
cmd overlay disable --user 0 com.android.theme.icon.squircle >/dev/null 2>&1

# Registra a escolha no seletor de tema, para a interface refletir o estado.
settings put secure theme_customization_overlay_packages \
  '{"android.theme.customization.adaptive_icon_shape":"com.sistema2d.theme.icon.ios","android.theme.customization.color_source":"home_wallpaper","android.theme.customization.theme_style":"TONAL_SPOT"}' \
  >/dev/null 2>&1

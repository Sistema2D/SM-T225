#!/system/bin/sh

# Provisionamento idempotente: executa uma vez no usuário principal e nunca
# copia contas, credenciais, histórico de apps ou outros dados pessoais.
#
# v1.2 (28/08/2026) - o provisionamento do dock do Net Ripper foi removido junto
# com a descontinuação do aplicativo. Resta apenas o ajuste de idioma.
MODDIR="${0%/*}"
MARKER="$MODDIR/.provisioned_user0_v1"
[ -f "$MARKER" ] && exit 0

round=0
while [ "$(getprop sys.boot_completed)" != "1" ] && [ "$round" -lt 180 ]; do
  sleep 2
  round=$((round + 1))
done

settings put system system_locales "pt-BR,en-US" >/dev/null 2>&1
setprop persist.sys.locale pt-BR >/dev/null 2>&1

date +%s > "$MARKER"
chmod 0600 "$MARKER"

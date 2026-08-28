"""
Sistema2D SM-T225 - empacota os modulos Magisk em ZIPs flashaveis.

Gera um ZIP por modulo, no formato padrao do Magisk (v20.4+), instalavel pelo
app do Magisk ou pelo TWRP. Tambem descomprime o splash_fb0.raw, que fica
guardado em .gz no repositorio (sao 4,3 MB de quase tudo preto, que comprimem
para ~18 KB).

Uso:
    python empacotar.py            gera em ./dist
"""

from __future__ import annotations

import gzip
import hashlib
import shutil
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MODULOS = ROOT / "modulos"
DIST = ROOT.parent / "dist"

# Script padrao do Magisk. Ele so carrega util_functions.sh e chama
# install_module; toda a logica de instalacao e do proprio Magisk.
UPDATE_BINARY = """#!/sbin/sh
umask 022
ui_print() { echo "$1"; }

require_new_magisk() {
  ui_print "*******************************"
  ui_print " Please install Magisk v20.4+! "
  ui_print "*******************************"
  exit 1
}

OUTFD=$2
ZIPFILE=$3

mount /data 2>/dev/null

[ -f /data/adb/magisk/util_functions.sh ] || require_new_magisk
. /data/adb/magisk/util_functions.sh
[ $MAGISK_VER_CODE -lt 20400 ] && require_new_magisk

install_module
exit 0
"""

# Roda na instalacao. O contexto SELinux e o ponto critico: sem
# u:object_r:system_file:s0 o system_server leva 'denied' ao parsear os
# overlays e eles nunca sao registrados - sem erro visivel.
CUSTOMIZE_OVERLAY = """#!/system/bin/sh

ui_print "- Sistema2D iOS Look"
ui_print "- Aplicando contexto SELinux nos overlays"

set_perm_recursive "$MODPATH/system" 0 0 0755 0644 u:object_r:system_file:s0
set_perm "$MODPATH/service.sh" 0 0 0755

ui_print "- Os overlays sao ativados no primeiro boot"
"""

CUSTOMIZE_BOOTANIM = """#!/system/bin/sh

ui_print "- Sistema2D Boot"

if [ -f "$MODPATH/splash_fb0.raw.gz" ]; then
  ui_print "- Descomprimindo a splash do framebuffer"
  gzip -d "$MODPATH/splash_fb0.raw.gz" 2>/dev/null || \\
    busybox gzip -d "$MODPATH/splash_fb0.raw.gz" 2>/dev/null
fi

set_perm_recursive "$MODPATH/system" 0 0 0755 0644 u:object_r:system_file:s0
set_perm "$MODPATH/post-fs-data.sh" 0 0 0755
[ -f "$MODPATH/splash_fb0.raw" ] && set_perm "$MODPATH/splash_fb0.raw" 0 0 0644
"""

CUSTOMIZE_SIMPLES = """#!/system/bin/sh

ui_print "- $MODNAME"
[ -f "$MODPATH/service.sh" ] && set_perm "$MODPATH/service.sh" 0 0 0755
[ -d "$MODPATH/system" ] && \\
  set_perm_recursive "$MODPATH/system" 0 0 0755 0644 u:object_r:system_file:s0
"""

CUSTOMIZE = {
    "sistema2d_ui_ios": CUSTOMIZE_OVERLAY,
    "sistema2d_bootanim": CUSTOMIZE_BOOTANIM,
}

IGNORAR = {"brightness_boot.log", ".provisioned_user0_v1", "customize.sh"}


def empacota(modulo: Path) -> Path:
    nome = modulo.name
    destino = DIST / f"{nome}.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("META-INF/com/google/android/update-binary", UPDATE_BINARY)
        zf.writestr("META-INF/com/google/android/updater-script", "#MAGISK\n")
        zf.writestr("customize.sh", CUSTOMIZE.get(nome, CUSTOMIZE_SIMPLES))
        for item in sorted(modulo.rglob("*")):
            if item.is_file() and item.name not in IGNORAR:
                zf.write(item, item.relative_to(modulo).as_posix())
    return destino


def main() -> None:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)

    modulos = sorted(d for d in MODULOS.iterdir()
                     if d.is_dir() and (d / "module.prop").exists())
    print(f"empacotando {len(modulos)} modulos:\n")
    for m in modulos:
        z = empacota(m)
        versao = ""
        for linha in (m / "module.prop").read_text(encoding="utf-8").splitlines():
            if linha.startswith("version="):
                versao = linha.split("=", 1)[1]
        sha = hashlib.sha256(z.read_bytes()).hexdigest()
        print(f"  {m.name:32s} v{versao:6s} {z.stat().st_size:>9,d} bytes")
        print(f"    sha256: {sha}")

    # o script de sysctl nao e modulo: vai avulso para /data/adb/service.d
    svc = MODULOS / "service.d"
    if svc.is_dir():
        shutil.copytree(svc, DIST / "service.d")
        print(f"\n  service.d/ copiado avulso (vai para /data/adb/service.d)")

    print(f"\npronto em {DIST}")


if __name__ == "__main__":
    main()

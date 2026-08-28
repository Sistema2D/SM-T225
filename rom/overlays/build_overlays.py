"""
Sistema2D - build dos overlays RRO do visual iPad (28/08/2026)

Gera, compila, alinha e assina os RROs que dao ao sistema a aparencia de iPad.
Sao sobrescritas de RECURSO apenas: nenhum desenho a mais por quadro, nenhum
processo novo. O custo em desempenho e o idmap do overlay, dezenas de KB.

OVERLAYS
--------
1. IconShapeIOS      alvo `android`, categoria adaptive_icon_shape
   - config_icon_mask ......... superelipse |x|^n+|y|^n=1 com n=5, 96 pontos
   - config_useRoundIcon ...... false
   - config_dialogCornerRadius  14dp (iOS usa 14pt; o AOSP usa 28dp)
   - config_bottomDialogCornerRadius 14dp

2. ScreenCornersIOS  alvo `android`, sem categoria
   - rounded_corner_radius (e _top/_bottom) 20dp
     O iPad mini arredonda o painel em ~2,9% da largura. Com 640dp de largura
     util, 20dp fica proporcionalmente fiel - e nao exagerado como 30-40dp.

POR QUE NAO SAO UM OVERLAY SO
-----------------------------
O primeiro pertence a categoria adaptive_icon_shape, gerenciada pelo seletor de
tema: trocar a forma do icone por la desativaria o overlay inteiro e levaria os
cantos de tela junto. Separados, cada coisa vive seu proprio ciclo.

PRE-REQUISITOS
--------------
- .tools/build-tools/android-14 (aapt2, zipalign, apksigner)
- keytool do Java 8
- framework-res.apk do PROPRIO aparelho, em 60-OVERLAY-UI/framework-res.apk
  (e o alvo exato contra o qual o overlay precisa linkar)

O script NAO instala nada. A instalacao e por modulo Magisk, e exige contexto
SELinux u:object_r:system_file:s0 - ver ARMADILHA no LEIA-ME.
"""

from __future__ import annotations

import hashlib
import math
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PROJ = ROOT.parent.parent                      # C:\Users\meloha\Desktop\SM-T225
BT = PROJ / ".tools/build-tools/android-14"
AAPT2 = BT / "aapt2.exe"
ZIPALIGN = BT / "zipalign.exe"
APKSIGNER = BT / "apksigner.bat"
KEYTOOL = Path("C:/Program Files/Java/jre1.8.0_481/bin/keytool.exe")

FRAMEWORK = ROOT / "framework-res.apk"
KEYSTORE = ROOT / "chave/sistema2d.keystore"
KS_PASS = "sistema2d"
KS_ALIAS = "sistema2d"
BUILD = ROOT / "build"
SAIDA = ROOT / "apk"


def sh(cmd: list, **kw) -> subprocess.CompletedProcess:
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.returncode != 0:
        print("COMANDO FALHOU:", " ".join(str(c) for c in cmd))
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
        sys.exit(1)
    return r


def superelipse_path(n: float = 5.0, pontos: int = 96, lado: float = 100.0) -> str:
    """A curva que o icone do iOS segue. n=5 e o valor classico."""
    r = lado / 2.0
    ps = []
    for i in range(pontos):
        t = 2 * math.pi * i / pontos
        ct, st = math.cos(t), math.sin(t)
        x = r + r * math.copysign(abs(ct) ** (2.0 / n), ct)
        y = r + r * math.copysign(abs(st) ** (2.0 / n), st)
        ps.append((x, y))
    return "M" + " L".join(f"{x:.3f},{y:.3f}" for x, y in ps) + " Z"


def garante_keystore() -> None:
    if KEYSTORE.exists():
        return
    KEYSTORE.parent.mkdir(parents=True, exist_ok=True)
    sh([KEYTOOL, "-genkeypair", "-keystore", KEYSTORE, "-alias", KS_ALIAS,
        "-keyalg", "RSA", "-keysize", "2048", "-validity", "10950",
        "-storepass", KS_PASS, "-keypass", KS_PASS,
        "-dname", "CN=Sistema2D, OU=ROM, O=Sistema2D, C=BR"])
    print(f"keystore criada: {KEYSTORE}")


def monta(nome: str, pacote: str, categoria: str | None,
          prioridade: int, valores, rotulo: str,
          alvo: str = "android") -> Path:
    """valores: str (só values/) ou dict {"values": xml, "values-night": xml}."""
    src = BUILD / nome
    if src.exists():
        shutil.rmtree(src)
    if isinstance(valores, str):
        valores = {"values": valores}
    for pasta in valores:
        (src / "res" / pasta).mkdir(parents=True)

    cat = f'\n        android:category="{categoria}"' if categoria else ""
    (src / "AndroidManifest.xml").write_text(f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pacote}"
    android:versionCode="1"
    android:versionName="1.0">
    <uses-sdk android:minSdkVersion="34" android:targetSdkVersion="34" />
    <overlay
        android:targetPackage="{alvo}"{cat}
        android:priority="{prioridade}" />
    <application
        android:label="{rotulo}"
        android:hasCode="false" />
</manifest>
''', encoding="utf-8", newline="\n")

    for pasta, xml in valores.items():
        (src / "res" / pasta / "config.xml").write_text(xml, encoding="utf-8", newline="\n")

    sh([AAPT2, "compile", "--dir", src / "res", "-o", src / "compiled.zip"])
    sh([AAPT2, "link", "-I", FRAMEWORK, "--manifest", src / "AndroidManifest.xml",
        "-R", src / "compiled.zip", "--auto-add-overlay", "-o", src / "unsigned.apk"])
    sh([ZIPALIGN, "-f", "-p", "4", src / "unsigned.apk", src / "aligned.apk"])

    SAIDA.mkdir(parents=True, exist_ok=True)
    apk = SAIDA / f"{nome}.apk"
    if apk.exists():
        apk.unlink()
    sh([APKSIGNER, "sign", "--ks", KEYSTORE, "--ks-pass", f"pass:{KS_PASS}",
        "--key-pass", f"pass:{KS_PASS}", "--ks-key-alias", KS_ALIAS,
        "--out", apk, src / "aligned.apk"])
    print(f"  {nome:18s} {apk.stat().st_size:>7,d} bytes  "
          f"sha256 {hashlib.sha256(apk.read_bytes()).hexdigest()[:16]}...")
    return apk


def main() -> None:
    for f in (AAPT2, ZIPALIGN, APKSIGNER, FRAMEWORK):
        if not f.exists():
            print(f"FALTA: {f}")
            sys.exit(1)
    garante_keystore()
    BUILD.mkdir(parents=True, exist_ok=True)

    mascara = superelipse_path()
    (ROOT / "icon_mask_ios.txt").write_text(mascara, encoding="utf-8", newline="\n")

    print("overlays:")
    monta(
        "IconShapeIOS", "com.sistema2d.theme.icon.ios",
        "android.theme.customization.adaptive_icon_shape", 2,
        f'''<?xml version="1.0" encoding="utf-8"?>
<!-- Forma de icone do iOS: superelipse |x|^n + |y|^n = 1 com n = 5, amostrada
     em 96 pontos sobre a caixa 100x100. Lados bem mais retos que a squircle do
     AOSP, com transicao suave nos cantos. Raios de dialogo em 14dp, como o iOS,
     no lugar dos 28dp do AOSP. -->
<resources>
    <bool name="config_useRoundIcon">false</bool>
    <dimen name="config_dialogCornerRadius">14dp</dimen>
    <dimen name="config_bottomDialogCornerRadius">14dp</dimen>
    <string name="config_icon_mask" translatable="false">{mascara}</string>
</resources>
''', "iOS")

    monta(
        "ScreenCornersIOS", "com.sistema2d.theme.corners", None, 3,
        '''<?xml version="1.0" encoding="utf-8"?>
<!-- Cantos de tela arredondados, como no iPad. O iPad mini arredonda o painel
     em cerca de 2,9% da largura; com 640dp uteis isso da ~19dp. 20dp fica
     proporcionalmente fiel sem exagerar.
     Custo: a SystemUI desenha as quinas por sobreposicao (ScreenDecorations).
     Medir o jank antes e depois - ver 40-DOCS. -->
<resources>
    <dimen name="rounded_corner_radius">20dp</dimen>
    <dimen name="rounded_corner_radius_top">20dp</dimen>
    <dimen name="rounded_corner_radius_bottom">20dp</dimen>
</resources>
''', "iOS corners")

    # --- dock translucido, no espirito do dock do iPad ---
    # taskbar_background e um seletor apontando para cor dinamica do sistema.
    # Trocar por cor simples e valido: o tipo do recurso (color) e o mesmo.
    monta(
        "TaskbarTranslucentIOS", "com.sistema2d.theme.taskbar", None, 3,
        {"values": '''<?xml version="1.0" encoding="utf-8"?>
<!-- Dock translucido. O iPad usa vidro; aqui e alfa puro, porque blur nesta
     GPU (PowerVR GE8320) foi descartado na auditoria. 70% de opacidade sobre
     o cinza claro do iOS. -->
<resources>
    <color name="taskbar_background">#B3F2F2F7</color>
</resources>
''',
         "values-night": '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="taskbar_background">#B31C1C1E</color>
</resources>
'''},
        "iOS dock", alvo="com.android.launcher3")

    # --- densidade das Configuracoes ---
    monta(
        "SettingsDensityIOS", "com.sistema2d.theme.settings", None, 3,
        '''<?xml version="1.0" encoding="utf-8"?>
<!-- Densidade de lista no espirito do iPad: margens laterais mais generosas e
     icone um pouco maior. A altura minima de toque FICA em 48dp - e piso de
     acessibilidade, nao estilo, e reduzi-la prejudicaria o uso.
     Raio de dialogo alinhado aos 14dp do framework. -->
<resources>
    <dimen name="settingslib_listPreferredItemPaddingStart">32dp</dimen>
    <dimen name="settingslib_listPreferredItemPaddingEnd">32dp</dimen>
    <dimen name="settingslib_preferenceIconSize">29dp</dimen>
    <dimen name="settingslib_dialogCornerRadius">14dp</dimen>
</resources>
''', "iOS settings", alvo="com.android.settings")

    print("\npronto. Instalar por modulo Magisk em system/product/overlay/,")
    print("com chcon u:object_r:system_file:s0 - sem isso o system_server")
    print("leva 'denied' no package-parsing e o overlay nem e registrado.")


if __name__ == "__main__":
    main()

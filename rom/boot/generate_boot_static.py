"""
Sistema2D - boot estatico SAMSUNG (28/08/2026)

MEDICAO QUE MOTIVOU ISTO
------------------------
Tempo ate boot_progress_enable_screen, medido no aparelho:

    com a animacao de 150 quadros .... 44.475 ms
    sem animacao nenhuma ............. 42.497 ms
                                       -------
    diferenca .......................  ~2,0 s

A animacao custa mesmo ~2 s. Mas removе-la sem mais nada deixaria o painel
PRETO dos 22,5 s (surfaceflinger) ate os 42,5 s - vinte segundos de tela preta,
bem pior que o problema original.

A SAIDA
-------
Trocar a animacao por um UNICO quadro estatico da tela SAMSUNG. Assim:

  - some o custo dos 150 quadros (150 decodificacoes de PNG a menos e 4,3 MB
    a menos de leitura), que era de onde vinham os ~2 s;
  - a tela SAMSUNG fica visivel o boot inteiro, em vez de preto.

O MESMO PIXEL EM TODAS AS FASES
-------------------------------
Este script gera a partir da MESMA imagem:

    splash_fb0.raw ....... despejado no framebuffer em post-fs-data
    bootanimation.zip .... quadro unico, exibido pelo bootanimation

E a mesma composicao ja gravada nos seis recursos do up_param. Ou seja, do
bootloader ate a tela inicial o pixel na tela nao muda - nao ha salto visual
entre as fases, so os intervalos em que ninguem desenha.
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
STOCK_RES = BASE / "up_param-recursos-stock"
SAIDA_FB = BASE / "fb-splash"
BUILD = BASE / "build_estatico"
BOOT_ZIP = BASE / "bootanimation_sistema2d_estatico.zip"

LARGURA, ALTURA = 800, 1340
ALTURA_FB, STRIDE = 1344, 3200
FPS = 15

MODELO = "Galaxy Tab A7 Lite  \u2022  SM-T225"
ESCALA = 0.92
CINZA = (145, 145, 145)


def ui_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", size)


def samsung_mark() -> Image.Image:
    source = Image.open(STOCK_RES / "letter.jpg").convert("L")
    region = source.crop((190, 515, 610, 625))
    bbox = region.point(lambda v: 255 if v > 12 else 0).getbbox()
    if bbox is None:
        raise RuntimeError("marca SAMSUNG nao encontrada")
    alpha = region.crop(bbox)
    mark = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    mark.putalpha(alpha)
    return mark


def contain(image: Image.Image, w: int, h: int) -> Image.Image:
    r = min(w / image.width, h / image.height)
    return image.resize((max(1, round(image.width * r)), max(1, round(image.height * r))),
                        Image.Resampling.LANCZOS)


def splash() -> Image.Image:
    canvas = Image.new("RGB", (LARGURA, ALTURA), "black")
    draw = ImageDraw.Draw(canvas)
    logo = contain(samsung_mark(), round(330 * ESCALA), round(72 * ESCALA))
    fonte = ui_font(max(14, round(18 * ESCALA)))
    caixa = draw.textbbox((0, 0), MODELO, font=fonte)
    tw, th = caixa[2] - caixa[0], caixa[3] - caixa[1]
    gap = round(28 * ESCALA)
    topo = (ALTURA - (logo.height + gap + th)) // 2
    canvas.paste(logo, ((LARGURA - logo.width) // 2, topo), logo)
    draw.text(((LARGURA - tw) // 2, topo + logo.height + gap), MODELO, font=fonte, fill=CINZA)
    return canvas


def escreve_raw(img: Image.Image) -> Path:
    fb = Image.new("RGB", (LARGURA, ALTURA_FB), "black")
    fb.paste(img, (0, 0))
    px = fb.load()
    buf = bytearray()
    for y in range(ALTURA_FB):
        linha = bytearray()
        for x in range(LARGURA):
            r, g, b = px[x, y]
            linha += bytes((b, g, r, 0xFF))   # cinza puro: ordem irrelevante
        if len(linha) < STRIDE:
            linha += bytes(STRIDE - len(linha))
        buf += linha
    SAIDA_FB.mkdir(parents=True, exist_ok=True)
    destino = SAIDA_FB / "splash_fb0.raw"
    destino.write_bytes(bytes(buf))
    return destino


def stored(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name)
    info.compress_type = zipfile.ZIP_STORED     # o bootanimation exige sem compressao
    info.date_time = (2026, 8, 28, 0, 0, 0)
    info.external_attr = 0o644 << 16
    return info


def escreve_zip(img: Image.Image) -> Path:
    if BUILD.exists():
        shutil.rmtree(BUILD)
    part = BUILD / "part0"
    part.mkdir(parents=True)
    img.save(part / "0000.png", "PNG", optimize=True)

    # p 0 0 part0 = repete para sempre. Quadro unico: nao ha animacao, so a tela.
    desc = f"{LARGURA} {ALTURA} {FPS}\np 0 0 part0\n"
    if BOOT_ZIP.exists():
        BOOT_ZIP.unlink()
    with zipfile.ZipFile(BOOT_ZIP, "w") as zf:
        zf.writestr(stored("desc.txt"), desc)
        zf.writestr(stored("part0/0000.png"), (part / "0000.png").read_bytes())
    return BOOT_ZIP


def main() -> None:
    img = splash()
    raw = escreve_raw(img)
    zp = escreve_zip(img)
    print(f"framebuffer : {raw.name}  {raw.stat().st_size:,} bytes")
    print(f"  sha256    : {hashlib.sha256(raw.read_bytes()).hexdigest()}")
    print(f"animacao    : {zp.name}  {zp.stat().st_size:,} bytes  (1 quadro)")
    print(f"  sha256    : {hashlib.sha256(zp.read_bytes()).hexdigest()}")
    print(f"  antes     : 1.954.762 bytes com 151 quadros")


if __name__ == "__main__":
    main()

"""
Sistema2D - splash cru para o framebuffer (28/08/2026)

O PROBLEMA
----------
Cronologia real do boot, medida por `ro.boottime.*` neste aparelho:

    ~13,8 s   o bootloader (LK) termina e some com a tela SAMSUNG
    22,0 s    zygote
    22,5 s    surfaceflinger
    31,2 s    bootanimation comeca a desenhar
    ~46,6 s   sf_stop_bootanim

Ou seja: entre o bootloader sair e a animacao entrar existem cerca de 17
segundos em que NINGUEM desenha, e o painel fica preto. E a "tela preta por
alguns segundos" relatada.

A SOLUCAO
---------
O aparelho expoe /dev/graphics/fb0 (mtkfb, 32 bpp, stride 3200). Da para
escrever pixels direto nele bem antes do surfaceflinger existir. Um script em
post-fs-data despeja esta imagem crua no framebuffer, e o painel passa a
mostrar a tela SAMSUNG em vez de preto.

POR QUE A ORDEM DOS BYTES NAO IMPORTA AQUI
------------------------------------------
Nao da para saber de antemao se o mtkfb espera BGRA ou RGBA. Normalmente isso
exigiria tentativa e erro. Mas a tela SAMSUNG e composta so de PRETO, BRANCO e
CINZA - tons em que R = G = B. Trocar a ordem dos canais nao muda nada. A
imagem sai correta nos dois casos, por construcao.

O QUADRADO PRETO NOS AVISOS
---------------------------
A mesma composicao ja usada no up_param v11: marca SAMSUNG + modelo, sem
nenhum texto de aviso. Nao existe "aviso" a cobrir aqui, porque a imagem e
desenhada do zero - o resultado e o mesmo que o pedido "quadrado preto por
cima", so que na origem.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
STOCK_RES = BASE / "up_param-recursos-stock"
SAIDA = BASE / "fb-splash"

# Parametros lidos de /sys/class/graphics/fb0 no aparelho.
LARGURA = 800
ALTURA_VISIVEL = 1340
ALTURA_FB = 1344          # virtual_size 800,4032 -> 4032/3 buffers
STRIDE = 3200             # 800 px * 4 bytes
BPP = 4

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
        raise RuntimeError("marca SAMSUNG nao encontrada em letter.jpg")
    alpha = region.crop(bbox)
    mark = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    mark.putalpha(alpha)
    return mark


def contain(image: Image.Image, w: int, h: int) -> Image.Image:
    r = min(w / image.width, h / image.height)
    return image.resize((max(1, round(image.width * r)), max(1, round(image.height * r))),
                        Image.Resampling.LANCZOS)


def splash() -> Image.Image:
    """Identica a do up_param v11, para nao haver salto visual entre as fases."""
    canvas = Image.new("RGB", (LARGURA, ALTURA_VISIVEL), "black")
    draw = ImageDraw.Draw(canvas)
    logo = contain(samsung_mark(), round(330 * ESCALA), round(72 * ESCALA))
    fonte = ui_font(max(14, round(18 * ESCALA)))
    caixa = draw.textbbox((0, 0), MODELO, font=fonte)
    tw, th = caixa[2] - caixa[0], caixa[3] - caixa[1]
    gap = round(28 * ESCALA)
    grupo = logo.height + gap + th
    topo = (ALTURA_VISIVEL - grupo) // 2
    canvas.paste(logo, ((LARGURA - logo.width) // 2, topo), logo)
    draw.text(((LARGURA - tw) // 2, topo + logo.height + gap), MODELO, font=fonte, fill=CINZA)
    return canvas


def main() -> None:
    SAIDA.mkdir(parents=True, exist_ok=True)
    img = splash()
    img.save(SAIDA / "previa_fb.png")

    # canvas do tamanho do framebuffer; as 4 linhas extras ficam pretas
    fb = Image.new("RGB", (LARGURA, ALTURA_FB), "black")
    fb.paste(img, (0, 0))

    px = fb.load()
    linhas = bytearray()
    for y in range(ALTURA_FB):
        linha = bytearray()
        for x in range(LARGURA):
            r, g, b = px[x, y]
            # R=G=B em toda a arte, entao BGRA e RGBA dao o mesmo resultado
            linha += bytes((b, g, r, 0xFF))
        # completa ate o stride, caso stride > largura*4
        if len(linha) < STRIDE:
            linha += bytes(STRIDE - len(linha))
        linhas += linha

    destino = SAIDA / "splash_fb0.raw"
    destino.write_bytes(bytes(linhas))
    esperado = STRIDE * ALTURA_FB

    cinza_puro = all(px[x, y][0] == px[x, y][1] == px[x, y][2]
                     for y in range(0, ALTURA_FB, 7) for x in range(0, LARGURA, 7))

    print(f"framebuffer   : {LARGURA}x{ALTURA_FB}  stride {STRIDE}  {BPP*8} bpp")
    print(f"arquivo       : {destino.name}  {len(linhas):,} bytes (esperado {esperado:,})")
    print(f"  sha256      : {hashlib.sha256(bytes(linhas)).hexdigest()}")
    print(f"tons de cinza : {cinza_puro}  -> ordem de bytes irrelevante")
    if len(linhas) != esperado:
        raise SystemExit("tamanho inesperado")


if __name__ == "__main__":
    main()

"""
Sistema2D - up_param v11 (28/08/2026)

Evolucao da v9. Alem do que a v9 ja fazia, atende o refinamento 1:

    "exiba um quadrado preto em cima dos avisos de software nao original
     Samsung, exibidos no boot (para ficarem invisiveis)"

CORRECAO DA v10 - POR QUE NAO USAR PRETO
----------------------------------------
A v10 substituiu `booting_warning.jpg` por um retangulo preto do tamanho nativo
(624x292), na suposicao de que ele fosse um banner sobreposto ao splash. Estava
ERRADO: o bootloader AMPLIA esse recurso para a tela inteira. Com ele preto, a
segunda tela do boot (a que vem depois do blink) ficou TODA preta, engolindo a
marca Samsung que aparecia ali.

A v11 corrige dando a `booting_warning.jpg` a MESMA composicao Samsung dos
outros cinco, em 800x1340. O texto de aviso some igual - que era o pedido - mas
a tela continua identica a primeira, em vez de apagada. E, como agora os SEIS
recursos do caminho de boot sao byte a byte iguais, tambem nao ha zoom possivel
entre nenhum deles.

Licao para o futuro: neste bootloader, recurso do caminho de boot e desenhado em
tela cheia, nao como sobreposicao. Para "esconder" um aviso, troque a arte dele
pela arte desejada - nunca por preto.

O QUE E O AVISO
---------------
E o recurso `booting_warning.jpg`, 624x292, que a v9 NAO tocou. Conteudo:
triangulo amarelo + texto vermelho "This phone is not running Samsung's
official software. You may have problems with features or security, and you
won't be able to install software updates."

Como o fundo da tela de boot ja e preto, substituir esse recurso por um
retangulo preto solido do MESMO tamanho o torna efetivamente invisivel - que e
exatamente o "quadrado preto por cima" pedido, so que feito na origem, sem
depender de sobreposicao.

O QUE NAO E TOCADO, DE PROPOSITO
--------------------------------
`secure_error.jpg` (620x676) - "This phone has been flashed with unauthorized
software & is locked. Call your mobile operator." NAO e um aviso de rotina do
boot: e uma tela de FALHA GRAVE. Apaga-la esconderia o diagnostico caso o
aparelho um dia entre nesse estado. Fica como esta.

`SUD_0..10.jpg` (202x38) - sao rotulos "USB Port #00".."#10" do download mode.
Nao tem relacao com aviso de software.

`download*.jpg`, `device_lock/unlock.jpg`, `broken_cable.jpg`, `grdm_*`,
`low_battery_alert.jpg`, `lpm.jpg` - recursos de servico, preservados.

ESTE SCRIPT NAO GRAVA NADA.
"""

from __future__ import annotations

import copy
import hashlib
import io
import tarfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
BASE_DIR = ROOT.parent
STOCK_TAR = BASE_DIR / "up_param-imagens/up_param_STOCK_backup.tar"
STOCK_RES = BASE_DIR / "up_param-recursos-stock"
BUILD = BASE_DIR / "build_up_param_v11"
OUT_IMG = BASE_DIR / "up_param-imagens/up_param_v11_SM-T225.img"

WIDTH, HEIGHT = 800, 1340
PARTICAO_BYTES = 4 * 1024 * 1024

# Telas do boot normal: recebem a composicao Samsung, todas identicas.
ALVOS_SPLASH = ("letter.jpg", "logo.jpg", "warning.jpg", "warning_svb.jpg",
                "svb_orange.jpg", "booting_warning.jpg")
# Nenhum recurso vira preto solido. Ver a nota da v11 no cabecalho.
ALVOS_PRETO = ()

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
        raise RuntimeError("Nao foi possivel localizar a marca SAMSUNG em letter.jpg")
    alpha = region.crop(bbox)
    mark = Image.new("RGBA", alpha.size, (255, 255, 255, 0))
    mark.putalpha(alpha)
    return mark


def contain(image: Image.Image, width: int, height: int) -> Image.Image:
    ratio = min(width / image.width, height / image.height)
    return image.resize(
        (max(1, round(image.width * ratio)), max(1, round(image.height * ratio))),
        Image.Resampling.LANCZOS,
    )


def splash(mark: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (WIDTH, HEIGHT), "black")
    draw = ImageDraw.Draw(canvas)
    logo = contain(mark, round(330 * ESCALA), round(72 * ESCALA))
    fonte = ui_font(max(14, round(18 * ESCALA)))
    caixa = draw.textbbox((0, 0), MODELO, font=fonte)
    texto_w, texto_h = caixa[2] - caixa[0], caixa[3] - caixa[1]
    gap = round(28 * ESCALA)
    grupo_h = logo.height + gap + texto_h
    topo = (HEIGHT - grupo_h) // 2
    canvas.paste(logo, ((WIDTH - logo.width) // 2, topo), logo)
    draw.text(((WIDTH - texto_w) // 2, topo + logo.height + gap),
              MODELO, font=fonte, fill=CINZA)
    return canvas


def jpeg_bytes(img: Image.Image, quality: int = 98) -> bytes:
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    tela = splash(samsung_mark())
    tela.save(BUILD / "previa_splash.png")
    jpeg_splash = jpeg_bytes(tela)

    with tarfile.open(STOCK_TAR, "r:") as origem:
        membros = [copy.copy(m) for m in origem.getmembers()]
        conteudo = {m.name: origem.extractfile(m).read()
                    for m in membros if m.isfile()}

    for nome in ALVOS_SPLASH + ALVOS_PRETO:
        if nome not in conteudo:
            raise RuntimeError(f"recurso ausente no container: {nome}")

    for nome in ALVOS_SPLASH:
        conteudo[nome] = jpeg_splash

    pretos = []
    for nome in ALVOS_PRETO:
        w, h = Image.open(io.BytesIO(conteudo[nome])).size
        preto = Image.new("RGB", (w, h), "black")
        # qualidade alta evita qualquer artefato de bloco visivel sobre preto
        conteudo[nome] = jpeg_bytes(preto, quality=100)
        preto.save(BUILD / f"previa_{nome}.png")
        pretos.append((nome, (w, h)))

    saida = io.BytesIO()
    with tarfile.open(fileobj=saida, mode="w") as destino:
        for antigo in membros:
            m = copy.copy(antigo)
            if m.isfile():
                dados = conteudo[m.name]
                m.size = len(dados)
                destino.addfile(m, io.BytesIO(dados))
            else:
                destino.addfile(m)
    payload = saida.getvalue()

    if len(payload) > PARTICAO_BYTES:
        raise RuntimeError(f"up_param excedeu 4 MiB: {len(payload):,}")
    imagem = payload + bytes(PARTICAO_BYTES - len(payload))
    OUT_IMG.write_bytes(imagem)

    intocados = len(conteudo) - len(ALVOS_SPLASH) - len(ALVOS_PRETO)
    print(f"splash Samsung : {WIDTH}x{HEIGHT} em {len(ALVOS_SPLASH)} recursos, identicos entre si")
    for nome, sz in pretos:
        print(f"preto solido   : {nome} {sz[0]}x{sz[1]} (aviso de software nao oficial)")
    print(f"preservados    : {intocados} recursos byte a byte")
    print(f"  inclui secure_error.jpg (tela de falha) e os 11 SUD_* do download mode")
    print()
    print(f"imagem         : {OUT_IMG.name}")
    print(f"  tamanho      : {len(imagem):,} bytes (payload {len(payload):,})")
    print(f"  sha256       : {hashlib.sha256(imagem).hexdigest()}")


if __name__ == "__main__":
    main()

"""
Sistema2D - visual de boot v9 (28/08/2026)

Evolucao do v8. Atende o refinamento 2:

    "ao final do carregamento da barra de progresso, faca com que ela se
     recolha das bordas para o centro ate sumir, e deixe exibido apenas o
     conjunto logo do GitHub + Sistema2D quando o progresso chegar em 100%"

LINHA DO TEMPO (150 quadros a 15 FPS = 10 s)

    0   .. 119   barra enche de 0 a 100%
    120 .. 126   segura em 100%, para o olho registrar
    127 .. 144   a barra RECOLHE das duas bordas para o centro ate sumir;
                 rotulo e porcentagem esmaecem junto
    145 .. 149   so a marca, ja centralizada
    part1        so a marca (quadro persistente ate o Android liberar a tela)

O ACERTO DE CENTRO
------------------
Durante o progresso, o conjunto centralizado e "marca + barra". Quando a barra
some, a marca sozinha ficaria ACIMA do centro real - o grupo tinha outra altura.
Por isso a marca desliza suavemente da posicao de grupo (cy=616) para o centro
verdadeiro da tela (cy=670) durante o mesmo intervalo do recolhimento. Sem isso
o final pareceria desalinhado.

ESTE SCRIPT NAO TOCA NO up_param.
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parent
GITHUB_SOURCE = ROOT / "github_mark.png"
BUILD = ROOT.parent / "build_v9"
PART0 = BUILD / "bootanimation/part0"
PART1 = BUILD / "bootanimation/part1"
BOOT_ZIP = ROOT.parent / "bootanimation_sistema2d_v9.zip"
MODULE_DIR = ROOT.parent / "modulo_bootanim_v10"
MODULE_ZIP = ROOT.parent / "sistema2d_bootanim_module_v10.zip"

WIDTH, HEIGHT = 800, 1340
FPS, FRAMES = 15, 150

PROGRESS_END = 119          # 100% em ~7,9 s
HOLD_END = 126              # segura em 100%
COLLAPSE_END = 144          # barra recolhida por completo

WHITE = (242, 245, 246)
MUTED = (135, 149, 153)
CYAN = (112, 222, 235)
DIM = (42, 51, 54)

TITLE_SIZE = 42
ICON_SIZE = 58
ICON_GAP = 18
BRAND_TO_BAR = 58
LABEL_TO_BAR = 22
BAR_W, BAR_H = 620, 18
BAR_X = (WIDTH - BAR_W) // 2


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ui_font(bold: bool, size: int) -> ImageFont.FreeTypeFont:
    name = "segoeuib.ttf" if bold else "segoeui.ttf"
    return ImageFont.truetype(str(Path("C:/Windows/Fonts") / name), size)


def mono_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype("C:/Windows/Fonts/consola.ttf", size)


def github_mark() -> Image.Image:
    source = Image.open(GITHUB_SOURCE).convert("L")
    alpha = source.point(lambda value: 255 - value)
    mark = Image.new("RGBA", source.size, (245, 245, 245, 0))
    mark.putalpha(alpha)
    return mark


def contain(image: Image.Image, width: int, height: int) -> Image.Image:
    ratio = min(width / image.width, height / image.height)
    return image.resize(
        (max(1, round(image.width * ratio)), max(1, round(image.height * ratio))),
        Image.Resampling.LANCZOS,
    )


def ease(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def layout() -> dict:
    probe = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    title_font = ui_font(True, TITLE_SIZE)
    small = mono_font(15)
    title_w = probe.textlength("Sistema2D", font=title_font)
    tb = probe.textbbox((0, 0), "Sistema2D", font=title_font)
    title_h = tb[3] - tb[1]
    lb = probe.textbbox((0, 0), "Inicializando Android", font=small)
    label_h = lb[3] - lb[1]

    brand_h = max(ICON_SIZE, title_h)
    group_h = brand_h + BRAND_TO_BAR + label_h + LABEL_TO_BAR + BAR_H
    top = (HEIGHT - group_h) // 2
    total_w = ICON_SIZE + ICON_GAP + title_w
    icon_x = round((WIDTH - total_w) / 2)

    return {
        "title_font": title_font,
        "small": small,
        "brand_cy_grupo": top + brand_h / 2,     # centrado como grupo (com barra)
        "brand_cy_final": HEIGHT / 2,            # centrado sozinho (sem barra)
        "icon_x": icon_x,
        "title_x": icon_x + ICON_SIZE + ICON_GAP,
        "label_y": top + brand_h + BRAND_TO_BAR,
        "bar_y": top + brand_h + BRAND_TO_BAR + label_h + LABEL_TO_BAR,
    }


L = layout()
ICON = contain(github_mark(), ICON_SIZE, ICON_SIZE)


def fase(frame: int) -> float:
    """0.0 antes do recolhimento, 1.0 com a barra totalmente recolhida."""
    if frame <= HOLD_END:
        return 0.0
    if frame >= COLLAPSE_END:
        return 1.0
    return ease((frame - HOLD_END) / (COLLAPSE_END - HOLD_END))


def brand_layer(frame: int) -> Image.Image:
    """Marca do GitHub a esquerda + Sistema2D. Desliza ao centro no recolhimento."""
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    c = fase(frame)
    cy = L["brand_cy_grupo"] + (L["brand_cy_final"] - L["brand_cy_grupo"]) * c
    layer.alpha_composite(ICON, (L["icon_x"], round(cy - ICON.height / 2)))
    draw.text((L["title_x"], cy), "Sistema2D",
              font=L["title_font"], fill=WHITE + (255,), anchor="lm")
    return layer


def progress_layer(frame: int) -> Image.Image:
    """Rotulo, porcentagem e barra. Recolhe das bordas para o centro no fim."""
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    c = fase(frame)
    if c >= 1.0:
        return layer                      # barra sumiu: nada a desenhar

    draw = ImageDraw.Draw(layer)
    progresso = ease(min(1.0, frame / PROGRESS_END))

    # rotulo e porcentagem esmaecem mais rapido que o recolhimento
    texto_alpha = round(255 * max(0.0, 1.0 - c * 1.6))
    if texto_alpha > 0:
        draw.text((BAR_X, L["label_y"]), "Inicializando Android",
                  font=L["small"], fill=MUTED + (texto_alpha,), anchor="lt")
        draw.text((BAR_X + BAR_W, L["label_y"]), f"{round(progresso * 100):3d}%",
                  font=L["small"], fill=WHITE + (texto_alpha,), anchor="rt")

    # o recolhimento come a barra pelas duas pontas, simetricamente
    meia = (BAR_W / 2) * (1.0 - c)
    centro = BAR_X + BAR_W / 2
    x0, x1 = centro - meia, centro + meia
    if x1 - x0 < 1:
        return layer

    y0, y1 = L["bar_y"], L["bar_y"] + BAR_H
    raio = min(9, (x1 - x0) / 2)
    draw.rounded_rectangle((x0, y0, x1, y1), radius=raio, fill=DIM + (255,))

    # a parte preenchida tambem encolhe junto, mantendo a proporcao
    cheio_x1 = x0 + (x1 - x0) * progresso
    if cheio_x1 - x0 >= 1:
        draw.rounded_rectangle((x0, y0, max(cheio_x1, x0 + raio * 2), y1),
                               radius=raio, fill=CYAN + (255,))
    return layer


def animation_frame(frame: int) -> Image.Image:
    canvas = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 255))
    canvas.alpha_composite(progress_layer(frame))
    canvas.alpha_composite(brand_layer(frame))
    return canvas.convert("RGB")


def stored_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name)
    info.compress_type = zipfile.ZIP_STORED
    info.date_time = (2026, 8, 28, 0, 0, 0)
    info.external_attr = 0o644 << 16
    return info


def build_animation() -> None:
    for folder in (PART0, PART1):
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)

    for frame in range(FRAMES):
        animation_frame(frame).save(PART0 / f"{frame:04d}.png", "PNG", optimize=True)
    # persistente: so a marca, ja no centro
    animation_frame(FRAMES).save(PART1 / "0000.png", "PNG", optimize=True)

    desc = f"{WIDTH} {HEIGHT} {FPS}\np 1 0 part0\np 0 0 part1\n"
    if BOOT_ZIP.exists():
        BOOT_ZIP.unlink()
    with zipfile.ZipFile(BOOT_ZIP, "w") as zf:
        zf.writestr(stored_info("desc.txt"), desc)
        for frame in range(FRAMES):
            zf.writestr(stored_info(f"part0/{frame:04d}.png"),
                        (PART0 / f"{frame:04d}.png").read_bytes())
        zf.writestr(stored_info("part1/0000.png"), (PART1 / "0000.png").read_bytes())


def build_module() -> None:
    if MODULE_DIR.exists():
        shutil.rmtree(MODULE_DIR)
    media = MODULE_DIR / "system/product/media"
    media.mkdir(parents=True)
    shutil.copy2(BOOT_ZIP, media / "bootanimation.zip")
    shutil.copy2(ROOT.parent.parent / "10-MODULOS/sistema2d_bootanim/post-fs-data.sh",
                 MODULE_DIR / "post-fs-data.sh")
    (MODULE_DIR / "auto_mount").write_bytes(b"")
    (MODULE_DIR / "customize.sh").write_text(
        '#!/system/bin/sh\n\nset_perm "$MODPATH/post-fs-data.sh" 0 0 0755\n',
        encoding="utf-8", newline="\n")
    (MODULE_DIR / "module.prop").write_text(
        "id=sistema2d_bootanim\n"
        "name=Sistema2D Boot\n"
        "version=10.0\n"
        "versionCode=10\n"
        "author=Sistema2D\n"
        "description=Centered Sistema2D mark with the GitHub logo on the left. At 100% "
        "the progress bar retracts from both edges into the centre and disappears, "
        "leaving only the mark.\n",
        encoding="utf-8", newline="\n")

    if MODULE_ZIP.exists():
        MODULE_ZIP.unlink()
    with zipfile.ZipFile(MODULE_ZIP, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(MODULE_DIR.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(MODULE_DIR).as_posix())


def main() -> None:
    BUILD.mkdir(parents=True, exist_ok=True)
    build_animation()
    build_module()
    print(f"linha do tempo : 0-{PROGRESS_END} enche | {PROGRESS_END+1}-{HOLD_END} segura "
          f"| {HOLD_END+1}-{COLLAPSE_END} recolhe | {COLLAPSE_END+1}-{FRAMES-1} so a marca")
    print(f"marca desliza  : cy {round(L['brand_cy_grupo'])} -> {round(L['brand_cy_final'])}")
    print(f"animacao       : {BOOT_ZIP.name}  {BOOT_ZIP.stat().st_size:,} bytes")
    print(f"  sha256       : {sha256(BOOT_ZIP)}")
    print(f"modulo         : {MODULE_ZIP.name}  {MODULE_ZIP.stat().st_size:,} bytes")


if __name__ == "__main__":
    main()

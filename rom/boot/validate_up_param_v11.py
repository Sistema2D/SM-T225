"""
Valida a imagem up_param v11 ANTES de gravar em particao.

Alem do que a v9 conferia, checa que o aviso de software nao oficial ficou
PRETO DE VERDADE (todo pixel preto), e que a tela de falha secure_error.jpg
continua intacta - ela nao deve ser apagada.

Sai com codigo 1 se qualquer verificacao falhar.
"""

from __future__ import annotations

import hashlib
import io
import sys
import tarfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / "up_param-imagens"
STOCK = BASE / "up_param_STOCK_backup.tar"
NOVA = BASE / "up_param_v11_SM-T225.img"

SPLASH = {"letter.jpg", "logo.jpg", "warning.jpg", "warning_svb.jpg",
          "svb_orange.jpg", "booting_warning.jpg"}
PRETO: set[str] = set()
PARTICAO_BYTES = 4 * 1024 * 1024

falhas: list[str] = []


def checa(cond: bool, ok: str, erro: str) -> None:
    if cond:
        print(f"  OK    {ok}")
    else:
        print(f"  FALHA {erro}")
        falhas.append(erro)


def carrega(p: Path) -> dict[str, bytes]:
    with tarfile.open(p, "r:") as t:
        return {m.name: t.extractfile(m).read() for m in t.getmembers() if m.isfile()}


def nomes(p: Path) -> list[str]:
    with tarfile.open(p, "r:") as t:
        return [m.name for m in t.getmembers()]


def main() -> None:
    dados = NOVA.read_bytes()
    print(f"imagem: {NOVA.name}")
    print(f"sha256: {hashlib.sha256(dados).hexdigest()}\n")

    print("tamanho e estrutura")
    checa(len(dados) == PARTICAO_BYTES,
          f"tamanho exato de particao: {len(dados):,} bytes",
          f"tamanho {len(dados):,} != {PARTICAO_BYTES:,}")

    estoque = carrega(STOCK)
    novo = carrega(NOVA)
    checa(nomes(NOVA) == nomes(STOCK),
          f"{len(novo)} membros, mesmos nomes e mesma ordem do estoque",
          "a lista ou a ordem dos membros mudou")

    print("\nrecursos de servico preservados byte a byte")
    mexidos = SPLASH | PRETO
    divergentes = [n for n in estoque if n not in mexidos and estoque[n] != novo.get(n)]
    checa(not divergentes,
          f"{len(estoque) - len(mexidos)} recursos intactos",
          f"alterados indevidamente: {divergentes}")
    for critico in ("secure_error.jpg", "download.jpg", "download_error.jpg",
                    "device_unlock.jpg", "device_lock.jpg", "broken_cable.jpg",
                    "low_battery_alert.jpg", "SUD_0.jpg", "SUD_10.jpg"):
        if critico in estoque:
            checa(estoque[critico] == novo.get(critico),
                  f"{critico} intacto", f"{critico} FOI ALTERADO")

    print("\ntelas do boot normal")
    conteudos = {novo[a] for a in SPLASH}
    checa(len(conteudos) == 1,
          "as 6 sao identicas entre si (zoom impossivel por construcao)",
          f"as telas diferem: {len(conteudos)} versoes distintas")
    for alvo in sorted(SPLASH):
        img = Image.open(io.BytesIO(novo[alvo]))
        checa(img.size == (800, 1340), f"{alvo} em 800x1340",
              f"{alvo} em {img.size}, esperado 800x1340")

    print("\naviso de software nao oficial")
    for alvo in sorted(PRETO):
        orig = Image.open(io.BytesIO(estoque[alvo]))
        img = Image.open(io.BytesIO(novo[alvo])).convert("RGB")
        checa(img.size == orig.size,
              f"{alvo} manteve o tamanho nativo {img.size[0]}x{img.size[1]}",
              f"{alvo} mudou de {orig.size} para {img.size}")
        extremos = img.getextrema()          # ((minR,maxR),(minG,maxG),(minB,maxB))
        maximo = max(canal[1] for canal in extremos)
        checa(maximo == 0,
              f"{alvo} totalmente preto (canal maximo = {maximo})",
              f"{alvo} NAO esta totalmente preto: canal maximo = {maximo}")

    print("\ntodo JPEG decodificavel")
    ruins = []
    for nome, blob in novo.items():
        if nome.lower().endswith((".jpg", ".jpeg")):
            try:
                Image.open(io.BytesIO(blob)).load()
            except Exception as exc:
                ruins.append(f"{nome}: {exc}")
    checa(not ruins, f"{sum(1 for n in novo if n.lower().endswith('.jpg'))} JPEGs abrem",
          f"corrompidos: {ruins}")

    print()
    if falhas:
        print(f"REPROVADO - {len(falhas)} falha(s). NAO GRAVAR.")
        sys.exit(1)
    print("APROVADO")


if __name__ == "__main__":
    main()

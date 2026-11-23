"""
Teste visual: abre a tela principal e salva um screenshot da janela.
Nao mexe nos dados (modo local, apenas leitura da planilha da pasta).

    python teste_visual.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura.png"


def capturar(app, caminho, titulo="captura"):
    app.update_idletasks()
    app.update()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    imagem = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    imagem.save(caminho)
    print(f"[{titulo}] {caminho} ({imagem.width}x{imagem.height}) "
          f"janela={w}x{h} pos=({x},{y})")
    return imagem


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.attributes("-topmost", True)
    app.lift()
    app.update()
    time.sleep(1.2)
    app.update()
    caminho = os.path.abspath(SAIDA)
    imagem = capturar(app, caminho, "tela")

    # Amostra de pixels para conferir se o fundo (foto) aparece nas margens
    pontos = {
        "margem_esquerda": (6, imagem.height // 2),
        "margem_direita": (imagem.width - 6, imagem.height // 2),
        "entre_cartoes": (imagem.width // 2, int(imagem.height * 0.42)),
    }
    for nome, ponto in pontos.items():
        print(f"   {nome}: {imagem.getpixel(ponto)}")
    app.destroy()


if __name__ == "__main__":
    main()

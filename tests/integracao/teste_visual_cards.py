"""
Teste visual dos cards: abre a tela principal, rola a pagina e captura
os cards de personagem.

    python teste_visual_cards.py [saida1.png] [saida2.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA1 = sys.argv[1] if len(sys.argv) > 1 else "cards_hero.png"
SAIDA2 = sys.argv[2] if len(sys.argv) > 2 else "cards_lista.png"


def capturar(app, caminho, titulo):
    app.update_idletasks()
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    imagem = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    imagem.save(caminho)
    print(f"[{titulo}] {caminho} ({w}x{h})")
    return imagem


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.attributes("-topmost", True)
    app.lift()
    app.update()
    time.sleep(1.2)
    app.update()
    capturar(app, os.path.abspath(SAIDA1), "hero")

    # rola ate os cards
    app.canvas.yview_moveto(0.42)
    app._fixar_cenario()
    app.update()
    time.sleep(0.6)
    app.update()
    capturar(app, os.path.abspath(SAIDA2), "cards")
    print("cards desenhados:", len(getattr(app, "cards_personagem", [])))
    app.destroy()


if __name__ == "__main__":
    main()

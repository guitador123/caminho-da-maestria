"""
Teste de resolucao: como os cards ficam em FullHD (1920x1080) e QuadHD
(2560x1440).

    python teste_resolucoes.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\guilh\AppData\Local\Temp\opencode"
RESOLUCOES = [(1920, 1080), (2560, 1440)]


def capturar(app, nome):
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    caminho = os.path.join(SAIDA, f"res_{nome}.png")
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(caminho)
    print(f"   -> {caminho} ({w}x{h})")
    return caminho


def main():
    for largura, altura in RESOLUCOES:
        print(f"\n=== {largura}x{altura} ===")
        app = GrandChaseApp(user=None, supabase=None)
        app.geometry(f"{largura}x{altura}+0+0")
        app.attributes("-topmost", True)
        app.lift()
        app.update_idletasks()
        app.update()
        time.sleep(1.5)
        app.update()

        print(f"   janela: {app.winfo_width()}x{app.winfo_height()}")
        print(f"   lay.s = {app.lay.s:.3f}")
        print(f"   cards: {len(app.cards_personagem)}")
        if app.cards_personagem:
            card = app.cards_personagem[0]
            print(f"   card 0: '{card.dados.get('nome')}' x0={card.x0:.0f} "
                  f"y0={card.y0:.0f} escala={card.s:.2f} altura={card.altura:.0f}")
            print(f"   fim da grade: y={max(c.y0 + c.altura for c in app.cards_personagem):.0f}")
        print(f"   scrollregion: {app.canvas.cget('scrollregion')}")

        # topo
        app.canvas.yview_moveto(0)
        app._fixar_cenario()
        app.update()
        time.sleep(0.6)
        app.update()
        capturar(app, f"{largura}x{altura}_topo")

        # primeiro card: rola ate ele
        if app.cards_personagem:
            card = app.cards_personagem[0]
            total = float(app.canvas.cget("scrollregion").split()[3])
            app.canvas.yview_moveto(card.y0 / max(1.0, total))
            app._fixar_cenario()
            app.update()
            time.sleep(0.6)
            app.update()
            print(f"   scroll y = {app.canvas.canvasy(0):.0f}")
            capturar(app, f"{largura}x{altura}_cards")

        app.destroy()
        time.sleep(0.5)

    print("\nOK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

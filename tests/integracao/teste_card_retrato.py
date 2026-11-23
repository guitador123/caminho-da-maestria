"""
Previa de UM card de personagem com o retrato real (assets/personagens).

    python teste_card_retrato.py [saida.png] [personagem]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from card_personagem import CardPersonagem
from app_grandchase import GrandChaseApp, _num

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_card_retrato.png"
ALVO = sys.argv[2] if len(sys.argv) > 2 else "Ai"


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(1.0)
    app.update()

    dados = app._dados_personagem(ALVO)
    print(f"personagem: {ALVO} | retrato: {dados.get('nome')}")

    # desenha o card sozinho num canvas para a captura
    import tkinter as tk
    janela = tk.Toplevel(app)
    janela.title(f"preview {ALVO}")
    janela.configure(bg="#141221")
    janela.geometry("380x900")
    tela = tk.Canvas(janela, bg="#141221", highlightthickness=0, bd=0)
    tela.place(relx=0, rely=0, relwidth=1, relheight=1)
    card = CardPersonagem(tela, 20, 20, dados,
                          pasta_retratos=os.path.join("assets", "personagens"))
    janela.update()
    time.sleep(0.8)
    janela.update()
    x, y = janela.winfo_rootx(), janela.winfo_rooty()
    w, h = janela.winfo_width(), janela.winfo_height()
    caminho = os.path.abspath(SAIDA)
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(caminho)
    print(f"[card] {caminho} ({w}x{h})")
    janela.destroy()
    app.destroy()


if __name__ == "__main__":
    main()

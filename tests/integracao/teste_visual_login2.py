"""
Teste visual da tela de login: abre a janela e salva um PNG.

    python teste_visual_login2.py [saida.png] [modo]
        modo: entrar (padrao) | conta | recuperar
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from login import LoginApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_login.png"
MODO = sys.argv[2] if len(sys.argv) > 2 else "entrar"


def main():
    resultado = {}
    app = LoginApp(resultado)
    app.attributes("-topmost", True)
    app.lift()
    app.update()
    if MODO != "entrar":
        app.mostrar_modo(MODO)
    app.update()
    time.sleep(1.2)
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    caminho = os.path.abspath(SAIDA)
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(caminho)
    print(f"[login] {caminho} ({w}x{h}) modo={app.modo}")
    print("   destaque:", app.destaque)
    app.destroy()


if __name__ == "__main__":
    main()

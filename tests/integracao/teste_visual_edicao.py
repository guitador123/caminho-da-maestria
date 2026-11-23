"""
Teste visual da tela de edicao de personagem (Toplevel).

    python teste_visual_edicao.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_edicao.png"


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.attributes("-topmost", True)
    app.lift()
    app.update()
    time.sleep(1.0)
    app.update()

    # abre a edicao do primeiro personagem
    primeiro = app.dfs["Geral"]["Nome"].iloc[0]
    app._abrir_personagem({"nome": primeiro})
    app.update()
    time.sleep(1.2)
    app.update()

    import ctypes
    from ctypes import wintypes
    hwnd = ctypes.windll.user32.FindWindowW(None, f"{primeiro} — Caminho da Maestria")
    if hwnd:
        # esconde a janela principal para a edicao ficar visivel na captura
        app.withdraw()
        # truque do ALT para o Windows permitir o SetForegroundWindow
        user32 = ctypes.windll.user32
        user32.keybd_event(0x12, 0, 0, 0)          # ALT
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 0x0002, 0)     # ALT (solta)
        time.sleep(1.5)
        r = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(r))
        imagem = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
        imagem.save(os.path.abspath(SAIDA))
        print(f"[edicao] {os.path.abspath(SAIDA)} ({imagem.width}x{imagem.height})")
    else:
        print("FALHOU: a janela de edicao nao abriu")
    app.destroy()


if __name__ == "__main__":
    main()

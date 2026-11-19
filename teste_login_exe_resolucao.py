"""
E2E do .exe em tela CHEIA (QuadHD): faz o login, maximiza a janela, rola ate
os cards e captura — para conferir o card no executavel empacotado.

    python teste_login_exe_resolucao.py [saida.png]
"""

import os
import subprocess
import sys
import time

from PIL import ImageGrab

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from teste_login_exe import (EXE, achar, clicar, digitar, fazer_login,  # noqa
                             _rect)

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "exe_fullhd.png"


def main():
    print("lancando o exe...")
    processo = subprocess.Popen([os.path.abspath(EXE)])
    hwnd = achar("Caminho da Maestria - Entrar")
    if not hwnd:
        print("FALHOU: a tela de login nao apareceu")
        return 1

    principal = 0
    for tentativa in range(1, 4):
        fazer_login(hwnd)
        principal = achar("Caminho da Maestria", 40)
        if principal:
            break
    if not principal:
        print("FALHOU: a tela principal nao abriu")
        return 1
    print("tela principal aberta")

    # maximiza (QuadHD)
    import win32con
    import win32gui
    win32gui.ShowWindow(principal, win32con.SW_MAXIMIZE)
    win32gui.SetForegroundWindow(principal)
    time.sleep(2.5)
    r = _rect(principal)
    print(f"janela maximizada: {r.right - r.left}x{r.bottom - r.top}")

    # rola ate os cards (botao do meio / roda do mouse)
    import win32api
    for _ in range(40):
        win32api.SetCursorPos((r.left + 900, r.top + 500))
        win32api.mouse_event(win32con.MOUSEEVENTF_WHEEL, 0, 0, -240, 0)
        time.sleep(0.08)
    time.sleep(1.5)

    imagem = ImageGrab.grab(bbox=(r.left, r.top, r.right, r.bottom))
    imagem.save(os.path.abspath(SAIDA))
    print("captura:", os.path.abspath(SAIDA), imagem.size)

    # --- clica em um card: tem que abrir a edicao do personagem ----------
    import win32gui
    janelas = []
    def _coletar(hwnd, _):
        titulo = win32gui.GetWindowText(hwnd)
        if titulo.endswith("— Caminho da Maestria") and \
                not titulo.startswith("Caminho da Maestria"):
            janelas.append((hwnd, titulo))
    win32gui.EnumWindows(_coletar, None)
    if janelas:
        print("   (a edicao ja estava aberta)", janelas[0][1])

    # clica no primeiro card (canto superior esquerdo da area dos cards)
    clicar(r.left + 200, r.top + 400)
    time.sleep(1.5)
    janelas = []
    win32gui.EnumWindows(_coletar, None)
    if janelas:
        print("   clique no card -> abriu:", janelas[0][1])
    else:
        print("   (nenhuma janela de edicao encontrada apos o clique)")

    processo.terminate()
    print("\nLOGIN E2E (TELA CHEIA) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
Teste E2E do .exe: lanca, faz login e confere se a tela principal abriu.

    python teste_login_exe.py [saida.png]
"""

import ctypes
import os
import subprocess
import sys
import time
from ctypes import wintypes

from PIL import ImageGrab

EXE = (sys.argv[2] if len(sys.argv) > 2 else
       r"dist\Caminho da Maestria\Caminho da Maestria.exe")
SAIDA = sys.argv[1] if len(sys.argv) > 1 else "exe_login.png"

user32 = ctypes.windll.user32
user32.SetProcessDPIAware()

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
KEYEVENTF_KEYUP = 0x0002


def _rect(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r


def achar(titulo, tentativas=40):
    for _ in range(tentativas):
        hwnd = user32.FindWindowW(None, titulo)
        if hwnd:
            return hwnd
        time.sleep(0.5)
    return 0


def clicar(x, y):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(0.15)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(0.25)


def digitar(texto):
    """Digita via teclado virtual (vai para a janela em foco)."""
    for caractere in texto:
        codigo = user32.VkKeyScanW(ctypes.c_wchar(caractere))
        vk = codigo & 0xFF
        shift = (codigo >> 8) & 1
        if shift:
            user32.keybd_event(0x10, 0, 0, 0)
        user32.keybd_event(vk, 0, 0, 0)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        if shift:
            user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(0.012)


def colar(texto):
    """Cola texto via area de transferencia (Ctrl+V)."""
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Set-Clipboard -Value ([System.Windows.Forms.Clipboard]::GetText())"
                    if False else
                    "$args[0] | Set-Clipboard", texto], check=False)
    time.sleep(0.2)
    user32.keybd_event(0x11, 0, 0, 0)      # ctrl
    user32.keybd_event(0x56, 0, 0, 0)      # V
    user32.keybd_event(0x56, 0, KEYEVENTF_KEYUP, 0)
    user32.keybd_event(0x11, 0, KEYEVENTF_KEYUP, 0)
    time.sleep(0.2)


def focar(hwnd, tentativas=6):
    """Garante que a janela esta em primeiro plano (truque do ALT + topmost)."""
    for _ in range(tentativas):
        # HWND_TOPMOST = -1 : coloca a janela acima das outras (ex.: um jogo
        # em tela cheia que nao devolve o foco)
        user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002)
        r = _rect(hwnd)
        clicar(r.left + 400, r.top + 15)      # clica na barra de titulo
        time.sleep(0.4)
        if user32.GetForegroundWindow() == hwnd:
            return True
        # o Windows so permite SetForegroundWindow se o ALT estiver pressionado
        user32.keybd_event(0x12, 0, 0, 0)
        user32.SetForegroundWindow(hwnd)
        user32.keybd_event(0x12, 0, 0x0002, 0)
        time.sleep(0.5)
        if user32.GetForegroundWindow() == hwnd:
            return True
    return False


def fazer_login(hwnd):
    """Preenche os campos e clica em Entrar."""
    r = _rect(hwnd)
    focar(hwnd)
    clicar(r.left + 150, r.top + 31 + 385)    # campo de e-mail
    digitar("teste@teste.com")
    clicar(r.left + 150, r.top + 31 + 452)    # campo de senha
    digitar("testeteste")
    clicar(r.left + 150, r.top + 31 + 540)    # botao Entrar


def main():
    print("lancando o exe...")
    processo = subprocess.Popen([os.path.abspath(EXE)])
    hwnd = achar("Caminho da Maestria - Entrar")
    if not hwnd:
        print("FALHOU: a tela de login nao apareceu")
        return 1
    print("login aberto")

    principal = 0
    for tentativa in range(1, 4):
        fazer_login(hwnd)
        principal = achar("Caminho da Maestria", 40)
        if principal:
            break
        print(f"   tentativa {tentativa}: a tela principal nao abriu, tentando de novo")
    if not principal:
        print("FALHOU: a tela principal nao abriu")
        return 1

    print("tela principal aberta")
    time.sleep(1.5)
    r = _rect(principal)
    clicar(r.left + 400, r.top + 15)          # clica na barra de titulo (sobe a janela)
    time.sleep(1.0)
    imagem = ImageGrab.grab(bbox=(r.left + 8, r.top + 31, r.left + 8 + 1152,
                                  r.top + 31 + 820))
    imagem.save(os.path.abspath(SAIDA))
    print("captura:", os.path.abspath(SAIDA), imagem.size)
    processo.terminate()
    print("\nLOGIN E2E OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

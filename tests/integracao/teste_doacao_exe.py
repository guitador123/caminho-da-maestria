"""
E2E do .exe: clica no botao "Apoiar" e decodifica o QR que aparece.

Confere que o **executavel** gera o QR Code com a chave atual
(o app monta o payload e o QR em memoria \u2014 sem depender do
`assets/doacao/qr_pix.png`).

    python teste_doacao_exe.py [caminho_do_exe]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np
from PIL import Image, ImageGrab

import pix_pagamento
from teste_login_exe import (EXE, achar, _rect, fazer_login, clicar, focar)

SAIDA = os.path.join(_raiz.RAIZ, "_capturas")


def main(argv):
    exe = os.path.abspath(argv[1] if len(argv) > 1 else EXE)
    if not os.path.exists(exe):
        print(f"FALHOU: o executavel nao existe: {exe}")
        return 1
    print(f"exe: {exe}")

    esperado = pix_pagamento.payload()
    print(f"payload do app: {esperado[:70]}...")

    processo = subprocess.Popen([exe])
    try:
        hwnd = achar("Caminho da Maestria - Entrar")
        if not hwnd:
            print("FALHOU: a tela de login nao abriu")
            return 1
        time.sleep(1.5)

        fazer_login(hwnd)
        principal = achar("Caminho da Maestria", 20)
        if not principal:
            print("FALHOU: a tela principal nao abriu")
            return 1

        # espera a janela ficar no tamanho
        for _ in range(40):
            r = _rect(principal)
            if (r.right - r.left) > 900 and (r.bottom - r.top) > 600:
                break
            time.sleep(0.5)
        r = _rect(principal)
        largura = r.right - r.left
        altura = r.bottom - r.top
        escala = min(largura / 1152, altura / 820)
        ox = (largura - 1152 * escala) / 2
        oy = (altura - 820 * escala) / 2
        # o botao "Apoiar" fica no lugar do antigo "English" (574..677)
        x = r.left + ox + 625 * escala
        y = r.top + oy + 153 * escala

        focar(principal)
        time.sleep(0.6)
        clicar(x, y)
        time.sleep(3.0)

        imagem = ImageGrab.grab()
        try:
            os.makedirs(SAIDA, exist_ok=True)
            imagem.save(os.path.join(SAIDA, "tela_exe.png"))
        except Exception:
            pass

        # o QR e o unico bloco BRANCO da tela (o painel e escuro):
        # achamos os pixels brancos e recortamos o QR em volta deles
        array_tela = np.array(imagem.convert("RGB"))
        brancos = np.all(array_tela > 235, axis=2)
        ys, xs = np.where(brancos)
        recorte = None
        if len(xs):
            x1, x2 = int(xs.min()) - 6, int(xs.max()) + 6
            y1, y2 = int(ys.min()) - 6, int(ys.max()) + 6
            recorte = imagem.crop((max(0, x1), max(0, y1),
                                   min(imagem.width, x2),
                                   min(imagem.height, y2)))
            recorte.save(os.path.join(SAIDA, "painel_doacao_exe.png"))
        else:
            recorte = imagem.crop((max(0, r.right - 650), max(0, r.top),
                                   min(imagem.width, r.right + 10),
                                   min(imagem.height, r.top + 830)))
            recorte.save(os.path.join(SAIDA, "painel_doacao_exe.png"))

        array = np.array(recorte.convert("RGB"))
        detector = cv2.QRCodeDetector()
        decodificado, _pontos, _ = detector.detectAndDecode(array)
        if not decodificado:
            ok, pontos, _ = detector.detectAndDecodeMulti(array)
            for texto in (pontos or []):
                if esperado and texto == esperado:
                    decodificado = texto
                    break
        print(f"QR no painel: {(decodificado or '')[:90]}")
        if not decodificado:
            print("FALHOU: nao achou o QR do painel na tela")
            return 1
        if esperado and decodificado != esperado:
            print(f"FALHOU: o QR do painel nao e o payload do app\n"
                  f"      painel: {decodificado}\n"
                  f"      app:    {esperado}")
            return 1


        print("DOACAO (EXE) OK")
        return 0
    finally:
        try:
            processo.terminate()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))

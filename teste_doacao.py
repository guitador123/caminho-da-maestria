"""
Teste do BOTAO DE DOACAO e do painel lateral.

  1) o botao "Apoiar" substitui o "English" no cabecalho
  2) o painel abre, mostra a chave Pix e o QR
  3) "Copiar chave Pix" coloca a chave na area de transferencia

    python teste_doacao.py [email] [senha]
"""

import os
import sys
import time
from credenciais_teste import conta_teste

import customtkinter as ctk

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)
mb.askyesno = lambda *a, **k: True

import auth
import tema_visual as tv
from app_grandchase import GrandChaseApp
from janela_doacao import PainelDoacao, chave_pix, pasta_doacao

# o script que gera o QR (para conferir que o payload esta em dia)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "assets", "doacao"))
from gerar_qr import monta_payload  # noqa: E402

import pix_pagamento  # noqa: E402


def main(argv):
    email, senha = conta_teste(argv)

    print("1) o botao 'Apoiar' no cabecalho:")
    rotulos = [rotulo for _icone, rotulo, _caixa in tv.BOTOES_LINHA1]
    print(f"   botoes da linha 1: {rotulos}")
    if "Apoiar" not in rotulos:
        print("   FALHOU: o botao 'Apoiar' nao esta no cabecalho")
        return 1
    if "English" in rotulos:
        print("   FALHOU: o botao 'English' ainda esta no cabecalho")
        return 1
    print("   -> OK (o 'Apoiar' ocupa o lugar do 'English')")

    print("\n2) os arquivos da doacao:")
    for nome in ("pix.txt", "qr_pix.png"):
        caminho = os.path.join(pasta_doacao(), nome)
        ok = os.path.exists(caminho)
        print(f"   {nome}: {'OK' if ok else 'FALTA'}")
        if not ok:
            print("   FALHOU: falta o arquivo", nome)
            return 1
    chave = chave_pix()
    print(f"   chave Pix: {chave[:60]}{'...' if len(chave) > 60 else ''}")
    if not chave:
        print("   FALHOU: a chave Pix esta vazia")
        return 1
    if "BR.GOV.BCB.PIX" not in chave:
        print("   FALHOU: a chave nao parece um payload Pix")
        return 1
    print("   -> OK")

    print("\n2b) o payload e o QR que o app mostra:")
    pasta = pasta_doacao()
    with open(os.path.join(pasta, "pix_payload.txt"), encoding="utf-8") as arq:
        esperado = arq.read().strip()
    if not esperado:
        print("   FALHOU: o pix_payload.txt esta vazio")
        return 1
    print(f"   payload: {esperado[:70]}...")

    # o app tem que mostrar exatamente esse payload
    if chave != esperado:
        print(f"   FALHOU: o app mostra outro payload!\n"
              f"      app:    {chave}\n"
              f"      arquivo:{esperado}")
        return 1
    print("   o app usa o payload do arquivo: OK")

    # o CRC do payload tem que estar certo
    import pix_pagamento
    if pix_pagamento._crc16(esperado[:-4]) != esperado[-4:]:
        print(f"   FALHOU: o CRC do payload esta errado "
              f"({esperado[-4:]})")
        return 1
    print("   CRC16 do payload: OK")

    # o QR que o app mostra tem que ser o do payload
    imagem = pix_pagamento.qr_imagem(264)
    if imagem is None:
        print("   FALHOU: o app nao conseguiu pegar o QR")
        return 1
    try:
        import numpy as np
        import cv2
        array = np.array(imagem.convert("RGB").resize((330, 330),
                                                      cv2.INTER_NEAREST))
        array = array[:, :, ::-1].copy()
        texto, _pontos, _ = cv2.QRCodeDetector().detectAndDecode(array)
        if texto != esperado:
            print(f"   FALHOU: o QR do app nao bate com o payload:\n"
                  f"      QR:    {texto}\n"
                  f"      certo: {esperado}")
            return 1
        print("   QR do app bate com o payload: OK")
    except ImportError:
        print("   (sem OpenCV: nao decodifiquei o QR)")

    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=resp.user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.0)
    app.update()

    print("\n3) o painel lateral:")
    painel = app._abrir_doacao()
    if painel is None:
        print("   FALHOU: o painel nao abriu")
        return 1
    fim = time.time() + 1.0
    while time.time() < fim:
        app.update()
        time.sleep(0.01)
    print(f"   painel: {painel.winfo_width()}x{painel.winfo_height()}")
    if not isinstance(painel, PainelDoacao):
        print("   FALHOU: o painel nao e da classe PainelDoacao")
        return 1

    print("\n4) copiar a chave Pix:")
    painel.copiar_chave()
    app.update()
    mensagem = painel.status.cget("text")
    print(f"   status: {mensagem!r}")
    if "copiada" not in mensagem:
        print("   FALHOU: a chave nao foi copiada")
        return 1
    print("   -> OK")

    # fecha pelo botao "Apoiar" (alterna)
    app._abrir_doacao()
    app.update()
    time.sleep(0.3)
    app.update()
    if app._painel_doacao is not None:
        print("   FALHOU: o painel nao fechou ao clicar de novo")
        return 1
    print("   -> OK (clicar de novo fecha o painel)")

    app.destroy()
    print("\nDOACAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

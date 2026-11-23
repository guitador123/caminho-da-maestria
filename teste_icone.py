"""
Teste do ICONE do aplicativo.

  1) o `assets/app.ico` foi gerado a partir do `assets/app.png`
  2) o `.spec` do build usa esse .ico no executavel
  3) todas as janelas (abas) recebem o icone

    python teste_icone.py [email] [senha]
"""

import ctypes
import io
import os
import sys
import time
from credenciais_teste import conta_teste

from PIL import Image

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)
mb.askyesno = lambda *a, **k: True

import auth
import caminhos
import login as mod_login
from app_grandchase import GrandChaseApp

user32 = ctypes.windll.user32
WM_GETICON = 0x007F
ICON_BIG = 1
ICON_SMALL = 0


def icone_da_janela(widget):
    """O handle do icone da janela (0 = sem icone)."""
    try:
        hwnd = user32.GetParent(widget.winfo_id())
        if not hwnd:
            hwnd = widget.winfo_id()
        return user32.SendMessageW(hwnd, WM_GETICON, ICON_BIG, 0)
    except Exception:
        return 0


def main(argv):
    email, senha = conta_teste(argv)

    print("1) o .ico do app:")
    ico = caminhos.icone_app()
    print(f"   ico: {ico}")
    if not os.path.exists(ico):
        print("   FALHOU: o .ico nao existe")
        return 1

    imagem = Image.open(ico)
    if imagem.format != "ICO":
        print(f"   FALHOU: o arquivo nao e um .ico ({imagem.format})")
        return 1
    tamanhos = sorted(imagem.info.get("sizes", []))
    print(f"   formato: {imagem.format} | quadros: {tamanhos}")
    for lado in (16, 32, 48, 64, 128, 256):
        if (lado, lado) not in tamanhos:
            print(f"   FALHOU: falta o quadro {lado}x{lado}")
            return 1

    # o quadro maior tem que ter arte (nao pode estar vazio)
    quadro = imagem.ico.getimage((256, 256)).convert("RGBA")
    visiveis = [p for p in quadro.getdata() if p[3] > 20]
    print(f"   pixels visiveis no quadro 256: {len(visiveis)}")
    if len(visiveis) < 1000:
        print("   FALHOU: o quadro 256 esta vazio")
        return 1
    print("   -> OK")

    print("\n2) o build usa esse .ico:")
    spec = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "Controle Grand Chase.spec")
    with io.open(spec, encoding="utf-8") as arquivo:
        texto = arquivo.read()
    if "assets', 'app.ico" not in texto:
        print("   FALHOU: o spec nao usa o app.ico")
        return 1
    print("   -> OK")

    print("\n3) o icone em cada janela:")
    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1

    # --- login ---------------------------------------------------------
    janela_login = mod_login.LoginApp({})
    janela_login.geometry("1000x760+40+40")
    janela_login.update()
    time.sleep(0.5)
    janela_login.update()
    if not icone_da_janela(janela_login):
        print("   FALHOU: a janela de login ficou sem icone")
        return 1
    print("   login: OK")
    janela_login.destroy()

    # --- tela principal -------------------------------------------------
    app = GrandChaseApp(user=resp.user, supabase=sb)
    app.geometry("1152x820+30+30")
    app.update()
    time.sleep(1.2)
    app.update()
    if not icone_da_janela(app):
        print("   FALHOU: a tela principal ficou sem icone")
        return 1
    print("   tela principal: OK")

    # --- as demais abas --------------------------------------------------
    from janela_nivel import JanelaNivelChaser
    from janela_perfil import JanelaPerfil
    from janela_personagem import JanelaPersonagem

    app._abrir_perfil()
    app.update()
    time.sleep(0.8)
    app.update()
    perfil = [w for w in app.winfo_children() if isinstance(w, JanelaPerfil)]
    if perfil and not icone_da_janela(perfil[0]):
        print("   FALHOU: a janela 'Minha conta' ficou sem icone")
        return 1
    print("   Minha conta: OK")

    app._abrir_nivel()
    app.update()
    time.sleep(0.8)
    app.update()
    nivel = [w for w in app.winfo_children() if isinstance(w, JanelaNivelChaser)]
    if nivel and not icone_da_janela(nivel[0]):
        print("   FALHOU: a janela 'Nivel do Chaser' ficou sem icone")
        return 1
    print("   Nivel do Chaser: OK")

    app._abrir_personagem({"nome": "Elesis"})
    app.update()
    time.sleep(0.8)
    app.update()
    edicao = [w for w in app.winfo_children() if isinstance(w, JanelaPersonagem)]
    if edicao and not icone_da_janela(edicao[0]):
        print("   FALHOU: a janela de edicao ficou sem icone")
        return 1
    print("   Edicao do personagem: OK")

    app.destroy()
    print("\nICONE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

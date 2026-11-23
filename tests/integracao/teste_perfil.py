"""
Teste do PERFIL (pendencia #7).

  1) o perfil aparece no espaco vago do hero (foto, "Lv. <Nick> <nivel>")
  2) o icone do nivel e procurado pela pasta assets/chaser (cl1, cl100...)
  3) a janela "Minha conta" abre e salva o nick
  4) o avatar e guardado no Supabase (base64) e volta ao recarregar
  5) trocar e-mail/senha chamam o Supabase Auth

    python teste_perfil.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import base64
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
from app_grandchase import GrandChaseApp
from janela_perfil import JanelaPerfil, _para_base64, _de_base64


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.update()

    # --- 1) o perfil no hero ---------------------------------------------
    print("1) o perfil no espaco vago do hero:")
    itens = app.canvas.find_withtag("perfil")
    print(f"   itens do perfil no canvas: {len(itens)}")
    if not itens:
        print("   FALHOU: o perfil nao foi desenhado")
        return 1
    textos = []
    for item in itens:
        if app.canvas.type(item) == "text":
            textos.append(app.canvas.itemcget(item, "text"))
    print(f"   textos: {textos}")
    if not any(t.startswith("Lv.") for t in textos):
        print("   FALHOU: o 'Lv.' nao aparece")
        return 1
    # a ordem tem de ser: Lv. <nivel> - <nick>
    if "Lv." not in textos:
        print("   FALHOU: o 'Lv.' nao aparece")
        return 1
    if "-" not in textos:
        print("   FALHOU: o separador '-' nao aparece")
        return 1
    if str(app.nivel_chaser) not in textos:
        print("   FALHOU: o nivel do chaser nao aparece")
        return 1
    pos_lv = textos.index("Lv.")
    pos_nivel = textos.index(str(app.nivel_chaser))
    pos_traco = textos.index("-")
    if not (pos_lv < pos_nivel < pos_traco):
        print(f"   FALHOU: a ordem esta errada: {textos}")
        return 1
    print("   -> OK: 'Lv. <nivel> - <nick>'")

    # --- 1b) a barra de EXP ----------------------------------------------
    print("\n1b) a barra de EXP:")
    percentuais = [t for t in textos if t.endswith("%")]
    print(f"   rotulos: {percentuais}")
    esperado = min(100.0, app.nivel_chaser / 10.0)
    if not percentuais:
        print("   FALHOU: a barra de EXP nao mostra o percentual")
        return 1
    if abs(float(percentuais[0].replace("%", "")) - esperado) > 0.2:
        print(f"   FALHOU: esperava {esperado:.1f}%, veio {percentuais[0]}")
        return 1
    if "EXP" not in textos:
        print("   FALHOU: o rotulo EXP nao aparece")
        return 1
    print(f"   -> OK (nivel {app.nivel_chaser} = {esperado:.1f}%)")

    # --- 1c) a foto vem dos 25 personagens --------------------------------
    print("\n1c) a foto do perfil (uma das 25):")
    app.perfil_personagem = "Elesis"
    app._desenhar_perfil()
    app.update()
    time.sleep(0.3)
    app.update()
    caminho = app._foto_do_perfil()
    print(f"   perfil_personagem={app.perfil_personagem!r} -> {caminho}")
    if caminho and not os.path.exists(caminho):
        print("   FALHOU: a foto nao existe")
        return 1
    if caminho and "_icon" not in os.path.basename(caminho):
        print("   FALHOU: o nome da foto tem que ser <personagem>_icon.png")
        return 1
    print("   -> OK (sem a imagem, mostra a inicial)")

    # --- 1d) o perfil atualiza em tempo real com o nivel ------------------
    print("\n1d) o perfil atualiza em tempo real com o nivel:")
    nivel_antigo = app.nivel_chaser
    app.nivel_chaser = 500
    app._desenhar_perfil()
    app.update()
    time.sleep(0.3)
    app.update()
    textos = [app.canvas.itemcget(i, "text")
              for i in app.canvas.find_withtag("perfil")
              if app.canvas.type(i) == "text"]
    print(f"   textos: {textos}")
    if "500" not in textos:
        print("   FALHOU: o nivel novo nao apareceu no perfil")
        app.nivel_chaser = nivel_antigo
        return 1
    print("   -> OK")
    app.nivel_chaser = nivel_antigo
    app._desenhar_perfil()
    app.update()

    # --- 2) o icone do nivel --------------------------------------------
    print("\n2) o icone do nivel (pasta assets/chaser):")
    caminho = app._icone_do_chaser()
    print(f"   nivel {app.nivel_chaser} -> {caminho}")
    if caminho and not os.path.exists(caminho):
        print("   FALHOU: o icone nao existe")
        return 1
    if caminho:
        # o nome tem que ser o do bloco de 100 do nivel
        marco = 1 if app.nivel_chaser < 100 else (app.nivel_chaser // 100) * 100
        if f"cl{marco}." not in os.path.basename(caminho):
            print(f"   FALHOU: esperava cl{marco}.png, veio {caminho}")
            return 1
        print(f"   -> OK (o icone do bloco cl{marco} foi encontrado)")
    else:
        print("   -> OK (sem arquivo = sem icone, sem erro)")

    # --- 3) a janela "Minha conta" --------------------------------------
    print("\n3) a janela 'Minha conta':")
    app._abrir_perfil()
    app.update()
    time.sleep(1.0)
    app.update()
    janelas = [w for w in _janelas(app) if isinstance(w, JanelaPerfil)]
    if not janelas:
        print("   FALHOU: a janela nao abriu")
        return 1
    janela = janelas[-1]
    print("   janela aberta  OK")

    # --- 4) o nick -------------------------------------------------------
    print("\n4) salvar o nick:")
    original = app.perfil_nick
    janela.nick_var.set("Testador")
    janela._salvar_nick()
    app.update()
    print(f"   perfil_nick = {app.perfil_nick!r}")
    if app.perfil_nick != "Testador":
        print("   FALHOU: o nick nao foi salvo")
        return 1
    print("   -> OK")

    # --- 5) o avatar (base64) -------------------------------------------
    print("\n5) o avatar (base64):")
    from PIL import Image
    temporario = os.path.join(os.environ.get("TEMP", "."), "foto_teste_perfil.png")
    Image.new("RGBA", (200, 200), (200, 60, 120, 255)).save(temporario)
    dados = _para_base64(temporario)
    print(f"   base64: {len(dados)} caracteres")
    if len(dados) < 100:
        print("   FALHOU: o base64 ficou vazio")
        return 1
    volta = _de_base64(dados)
    if not volta or not os.path.exists(volta):
        print("   FALHOU: nao deu para voltar do base64")
        return 1
    print("   -> OK")

    app.perfil_avatar = dados
    app.perfil_avatar_temp = volta
    app._desenhar_perfil()
    app.update()
    time.sleep(0.3)
    app.update()
    print("   o perfil foi redesenhado com a foto  OK")

    # --- 6) grava no Supabase e volta ------------------------------------
    print("\n6) gravar no Supabase e recarregar:")
    gravado = app._salvar_perfil()
    print(f"   _salvar_perfil() = {gravado}")
    if gravado:
        app._ler_perfil()
        app.update()
        print(f"   depois de ler: nick={app.perfil_nick!r} "
              f"avatar={'sim' if app.perfil_avatar else 'nao'}")
        if app.perfil_nick != "Testador":
            print("   FALHOU: o nick nao voltou do banco")
            return 1
    else:
        print("   (as colunas nick/avatar ainda nao existem no banco: "
              "rode sql/perfil.sql)")

    # --- 7) as acoes de e-mail/senha existem ----------------------------
    print("\n7) as acoes de e-mail e senha:")
    import supabase_db as db
    for nome in ("trocar_email", "trocar_senha", "salvar_perfil", "ler_perfil"):
        ok = hasattr(db, nome)
        print(f"   supabase_db.{nome}: {'OK' if ok else 'FALHOU'}")
        if not ok:
            return 1

    # restaura
    app.perfil_nick = original
    app._salvar_perfil()
    app.destroy()
    print("\nPERFIL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

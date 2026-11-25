"""
Varios titulos por personagem (item 15.2).

    python teste_titulos.py [email] [senha]

Valida (Supabase real, restaura no fim):
  1. a janela do personagem tem uma caixa por titulo do jogo (sem "Outro")
  2. marcando 3 titulos, o card mostra o MAIS FORTE e "+2" (ao vivo)
  3. passar o mouse no "+2" abre a lista com os 3; sair fecha
  4. salvar grava "mais forte | ... | mais fraco" na coluna titulo
  5. recarregar do banco mostra o mesmo card
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from dados_app import titulos_do_jogo

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True

MARCAR = ["Aniquilador do Vazio", "Renak", "Origem do Caos"]
NO_BANCO = "Origem do Caos | Renak | Aniquilador do Vazio"


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.02)


def _esperar_salvamento(app, limite=15):
    fim = time.time() + limite
    while time.time() < fim:
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            _esperar(app, 0.6)
            return True
    return False


def _card(app, nome):
    return next(c for c in app.cards_personagem if c.dados.get("nome") == nome)


def _textos(canvas, itens):
    return [str(canvas.itemcget(i, "text")) for i in itens
            if canvas.type(i) == "text"]


def _titulo_no_banco(sb, user_id, nome):
    pers = db.carregar_personagens(sb, user_id)
    acess = db.carregar_acessorios_titulo(sb, pers)
    linha = next(a for a in acess if a.get("Nome") == nome)
    return linha.get("titulo") or ""


def _conferir_card(app, nome, falhas, quando):
    card = _card(app, nome)
    textos = _textos(app.canvas, card._itens)
    if "Origem do Caos" not in textos or "+2" not in textos:
        falhas.append(f"{quando}: card sem 'Origem do Caos' e '+2'")
    if "Renak" in textos:
        falhas.append(f"{quando}: os outros titulos apareceram fora da lista")
    return card


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 1.5)
    nome = app.cards_personagem[0].dados["nome"]
    original = _titulo_no_banco(sb, user.id, nome)
    print(f"personagem: {nome} | titulo original: {original!r}")
    falhas = []

    try:
        print("1) janela do personagem")
        app._abrir_personagem({"nome": nome})
        _esperar(app, 1.0)
        janela = [w for w in app.winfo_children()
                  if isinstance(w, ctk.CTkToplevel)][-1]
        seletor = next(item for (tipo, _c), item in janela._linhas.items()
                       if tipo == "acesso" and hasattr(item, "caixas"))
        nomes = [t for t, _caixa in seletor.caixas]
        print(f"   {len(nomes)} caixas de titulo")
        if nomes[:len(titulos_do_jogo())] != titulos_do_jogo() or "Outro" in nomes:
            falhas.append(f"caixas erradas: {nomes}")
        for titulo, caixa in seletor.caixas:
            caixa.select() if titulo in MARCAR else caixa.deselect()
        janela._propagar()
        _esperar(app, 0.3)

        print("2) card ao vivo")
        card = _conferir_card(app, nome, falhas, "ao vivo")

        print("3) lista ao passar o mouse")
        card._mostrar_titulos()
        app.update()
        balao = app.canvas.find_withtag(f"{card.tag}_balao")
        lista = _textos(app.canvas, balao)
        print(f"   balao: {lista}")
        if lista[1:] != NO_BANCO.split(" | "):
            falhas.append(f"balao = {lista}")
        if app.canvas.find_above(balao[-1]):
            falhas.append("o balao ficou por baixo de outros itens")
        card._esconder_titulos()
        if app.canvas.find_withtag(f"{card.tag}_balao"):
            falhas.append("o balao nao fechou")

        print("4) salvar no Supabase")
        janela._salvar()
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        gravado = _titulo_no_banco(sb, user.id, nome)
        print(f"   no banco: {gravado!r}")
        if gravado != NO_BANCO:
            falhas.append(f"banco = {gravado!r} (esperado {NO_BANCO!r})")

        print("5) recarregar do banco")
        app.carregar_do_supabase()
        _esperar(app, 1.0)
        _conferir_card(app, nome, falhas, "depois de recarregar")
    finally:
        df = app.dfs["Acessórios Título"]
        coluna = next(c for c in df.columns if c.lower() in ("titulo", "título"))
        df.loc[df["Nome"].astype(str) == str(nome), coluna] = original
        app._marcar_modificado()
        app.salvar_supabase()
        _esperar_salvamento(app)
        volta = _titulo_no_banco(sb, user.id, nome)
        print(f"6) restaurado: {volta!r}")
        if volta != original:
            falhas.append("nao restaurou o titulo original")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nTITULOS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

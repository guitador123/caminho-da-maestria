"""
Colar nos acessorios (item 15.5).

    python teste_colar.py [email] [senha]

Valida (Supabase real, restaura no fim):
  1. a coluna existe (sql/colar.sql)
  2. a janela do personagem tem o dropdown "Colar" com as 2 opcoes
  3. escolher um colar mostra no card, com a borda da cor da regra
  4. salvar grava no banco; recarregar mostra o mesmo card
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True

JULGAMENTO = "Colar do Julgamento Radiante ( Fogo Infernal )"


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


def _colar_no_banco(sb, user_id, nome):
    pers = db.carregar_personagens(sb, user_id)
    acess = db.carregar_acessorios_titulo(sb, pers)
    return next(a for a in acess if a.get("Nome") == nome).get("colar") or ""


def _textos_do_card(app, nome):
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == nome)
    return " ".join(str(app.canvas.itemcget(i, "text")) for i in card._itens
                    if app.canvas.type(i) == "text")


def _abrir(app, nome):
    app._abrir_personagem({"nome": nome})
    _esperar(app, 1.0)
    janela = [w for w in app.winfo_children()
              if isinstance(w, ctk.CTkToplevel)][-1]
    combo = next((item for (tipo, chave), item in janela._linhas.items()
                  if tipo == "acesso" and str(chave).lower() == "colar"), None)
    return janela, combo


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    print("1) coluna no banco")
    if "colar" not in db._extras(sb, "acessorios_titulo"):
        print("   FALHOU: falta user_acessorios_titulo.colar "
              "(rode sql/colar.sql)")
        return 1
    print("   OK")

    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 1.5)
    nome = app.cards_personagem[0].dados["nome"]
    original = _colar_no_banco(sb, user.id, nome)
    print(f"   personagem: {nome} | colar original: {original!r}")
    falhas = []

    try:
        print("2) dropdown na janela")
        janela, combo = _abrir(app, nome)
        if combo is None:
            falhas.append("a janela nao tem o dropdown do Colar")
            return 1
        opcoes = list(combo.cget("values"))
        print(f"   opcoes: {opcoes}")
        if opcoes[-2:] != [JULGAMENTO, "Outro"]:
            falhas.append(f"opcoes erradas: {opcoes}")

        print("3) card ao vivo")
        combo.set(JULGAMENTO)
        janela._propagar()
        _esperar(app, 0.3)
        textos = _textos_do_card(app, nome)
        if "Colar do" not in textos or "Julgamento" not in textos:
            falhas.append("o colar nao aparece no card")
        card = next(c for c in app.cards_personagem
                    if c.dados.get("nome") == nome)
        from card_personagem import CORES_NOME, cor_do_acessorio
        if cor_do_acessorio("colar", card.dados["acessorios"].get("colar")) \
                != CORES_NOME["azul"]:
            falhas.append("o colar nao ficou azul")

        print("4) salvar no Supabase")
        janela._salvar()
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        gravado = _colar_no_banco(sb, user.id, nome)
        print(f"   no banco: {gravado!r}")
        if gravado != JULGAMENTO:
            falhas.append(f"banco = {gravado!r}")

        app.carregar_do_supabase()
        _esperar(app, 1.0)
        if "Julgamento" not in _textos_do_card(app, nome):
            falhas.append("depois de recarregar, o colar sumiu do card")
        else:
            print("   OK: o card voltou igual")
    finally:
        df = app.dfs["Acessórios Título"]
        coluna = next(c for c in df.columns if c.lower() == "colar")
        df.loc[df["Nome"].astype(str) == str(nome), coluna] = original
        app._marcar_modificado()
        app.salvar_supabase()
        _esperar_salvamento(app)
        volta = _colar_no_banco(sb, user.id, nome)
        print(f"5) restaurado: {volta!r}")
        if volta != original:
            falhas.append("nao restaurou o colar original")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nCOLAR OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

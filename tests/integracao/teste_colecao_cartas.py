"""
Nivel da colecao de cartas (item 15.4).

    python teste_colecao_cartas.py [email] [senha]

Valida (Supabase real, restaura no fim):
  1. as colunas existem (user_characters e user_historico_semanal)
  2. o painel do perfil mostra a colecao, e clicar nela abre a edicao
     (e nao o perfil)
  3. a janela recusa 2501 e "abc" (erro dentro da janela, nao fecha)
  4. salvar 1840 grava em TODAS as linhas da conta e o perfil mostra 1.840
  5. recarregar do banco traz 1840; a semana atual da Evolucao tambem
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from janela_nivel import JanelaColecaoCartas
from janela_perfil import JanelaPerfil

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True


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


def _no_banco(sb, user_id):
    return {p["Nome"]: p.get("colecao_cartas")
            for p in db.carregar_personagens(sb, user_id)}


def _janelas(app, classe):
    return [w for w in app.winfo_children() if isinstance(w, classe)]


def _textos_da_colecao(app):
    return [app.canvas.itemcget(i, "text")
            for i in app.canvas.find_withtag("perfil_colecao")
            if app.canvas.type(i) == "text"]


def _clicar(app, item):
    """Clique de verdade no meio do item (evento sintetico no canvas)."""
    x1, y1, x2, y2 = app.canvas.bbox(item)
    cx = (x1 + x2) / 2 - app.canvas.canvasx(0)
    cy = (y1 + y2) / 2 - app.canvas.canvasy(0)
    app.canvas.event_generate("<Motion>", x=int(cx), y=int(cy))
    app.canvas.event_generate("<Button-1>", x=int(cx), y=int(cy))
    app.canvas.event_generate("<ButtonRelease-1>", x=int(cx), y=int(cy))
    _esperar(app, 0.8)


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    print("1) colunas no banco")
    if "colecao_cartas" not in db._extras(sb, "personagens"):
        print("   FALHOU: falta user_characters.colecao_cartas "
              "(rode sql/colecao_cartas.sql)")
        return 1
    try:
        (sb.table("user_historico_semanal").select("colecao_cartas")
         .limit(1).execute())
    except Exception as erro:
        print(f"   FALHOU: falta user_historico_semanal.colecao_cartas: {erro}")
        return 1
    print("   OK")

    originais = _no_banco(sb, user.id)
    app = GrandChaseApp(user=user, supabase=sb)
    app.geometry("1152x820+0+0")
    _esperar(app, 2.0)
    falhas = []

    try:
        print("2) painel do perfil")
        textos = _textos_da_colecao(app)
        print(f"   {textos}")
        if "COLEÇÃO" not in textos:
            falhas.append("a colecao nao aparece no perfil")
        app.canvas.yview_moveto(0)
        _esperar(app, 0.3)
        valor_item = next(i for i in app.canvas.find_withtag("perfil_colecao")
                          if app.canvas.type(i) == "text"
                          and app.canvas.itemcget(i, "text") == "COLEÇÃO")
        _clicar(app, valor_item)
        janelas = _janelas(app, JanelaColecaoCartas)
        if not janelas:
            falhas.append("clicar na colecao nao abriu a edicao")
            return 1
        if _janelas(app, JanelaPerfil):
            falhas.append("clicar na colecao abriu o perfil junto")
        janela = janelas[-1]

        print("3) valores invalidos")
        for texto in ("2501", "abc"):
            janela.entrada.delete(0, "end")
            janela.entrada.insert(0, texto)
            janela._salvar()
            _esperar(app, 0.2)
            if not janela.winfo_exists() or not janela.erro_var.get():
                falhas.append(f"{texto!r} foi aceito")
            print(f"   {texto!r}: {janela.erro_var.get()}")

        print("4) salvar 1840")
        janela.entrada.delete(0, "end")
        janela.entrada.insert(0, "1840")
        janela._salvar()
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        banco = _no_banco(sb, user.id)
        diferentes = {n: v for n, v in banco.items() if v != 1840}
        print(f"   no banco: {len(banco) - len(diferentes)}/{len(banco)} "
              "linhas com 1840")
        if diferentes:
            falhas.append(f"linhas sem 1840: {diferentes}")
        if "1.840" not in _textos_da_colecao(app):
            falhas.append("o perfil nao mostra 1.840")

        print("5) recarregar do banco")
        app.colecao_cartas = 0
        app.carregar_do_supabase()
        _esperar(app, 1.0)
        semana = app._semana_atual()
        print(f"   app: {app.colecao_cartas} | evolucao (semana atual): "
              f"{semana.get('colecao_cartas')}")
        if app.colecao_cartas != 1840 or semana.get("colecao_cartas") != 1840:
            falhas.append("a colecao nao voltou do banco")
        if "1.840" not in _textos_da_colecao(app):
            falhas.append("depois de recarregar, o perfil nao mostra 1.840")
    finally:
        # restaura (o valor da conta e o mesmo em todas as linhas)
        anterior = next((v for v in originais.values() if v is not None), 0)
        app.definir_colecao_cartas(int(anterior or 0))
        _esperar_salvamento(app)
        volta = _no_banco(sb, user.id)
        print(f"6) restaurado: {set(volta.values())}")
        if set(volta.values()) != {int(anterior or 0)}:
            falhas.append("nao restaurou a colecao original")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nCOLECAO DE CARTAS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

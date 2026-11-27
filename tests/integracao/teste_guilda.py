"""
O HUB da guilda (item 12), no banco e na tela.

    python tests/integracao/teste_guilda.py [email] [senha]

Valida:
  1. perfis_da_guilda: todas as contas, em ordem de Level Chaser
     (desempate: Ataque medio), com a conta de teste no meio; sem
     username/e-mail na resposta
  2. sem login (anon) as funcoes NAO respondem
  3. conta_da_guilda devolve os personagens de uma conta
  4. SEGURANCA: gravar na conta de OUTRA pessoa nao muda nada (o RLS
     continua so do dono). O teste "grava" o mesmo valor que ja esta la,
     entao mesmo que falhasse nao mudaria os dados de ninguem
  5. na tela: a guia Guilda mostra um painel por conta; clicar em outra
     conta abre a pagina SO PARA VER (cards sem edicao; clicar num card
     nao abre nada); "Voltar para a Guilda" volta
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import auth
import guilda
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from dados_app import _num


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.02)


def _clicar(app, canvas, tag):
    x1, y1, x2, y2 = canvas.bbox(tag)
    total = float(str(canvas.cget("scrollregion")).split()[3])
    canvas.yview_moveto(max(0.0, (y1 - 150) / total))
    _esperar(app, 0.3)
    x = int((x1 + x2) / 2 - canvas.canvasx(0))
    y = int((y1 + y2) / 2 - canvas.canvasy(0))
    canvas.event_generate("<Motion>", x=x, y=y)
    canvas.event_generate("<Button-1>", x=x, y=y)
    canvas.event_generate("<ButtonRelease-1>", x=x, y=y)


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    falhas = []

    print("1) perfis_da_guilda")
    try:
        perfis = db.perfis_da_guilda(sb)
    except Exception as erro:
        print(f"   FALHOU: {erro} (rode sql/guilda.sql)")
        return 1
    print(f"   {len(perfis)} contas: "
          f"{[(p.get('nick'), p.get('nivel_chaser')) for p in perfis]}")
    if not any(p.get("user_id") == user.id for p in perfis):
        falhas.append("a conta de teste nao aparece")
    if perfis != guilda.ordenar(perfis):
        falhas.append("a ordem do banco nao e a do Level Chaser/ataque")
    if any("username" in p or "email" in p for p in perfis):
        falhas.append("o perfil vazou username/e-mail")

    print("2) sem login (anon)")
    anon = db.get_supabase()
    for nome, chamar in (("perfis_da_guilda", lambda: db.perfis_da_guilda(anon)),
                         ("conta_da_guilda",
                          lambda: db.conta_da_guilda(anon, user.id))):
        try:
            chamar()
            falhas.append(f"anon conseguiu chamar {nome}")
        except Exception:
            print(f"   {nome}: recusado  OK")

    outro = next((p for p in perfis if p.get("user_id") != user.id), None)

    print("3) conta_da_guilda")
    meus = db.conta_da_guilda(sb, user.id)["personagens"]
    print(f"   a conta de teste: {len(meus)} personagens")
    if not meus:
        falhas.append("conta_da_guilda nao devolveu os personagens")

    print("4) seguranca: gravar na conta de outra pessoa")
    if outro is None:
        print("   (so existe a conta de teste: pulado)")
    else:
        alvo = db.conta_da_guilda(sb, outro["user_id"])["personagens"][0]
        mesmo = {"nivel_chaser": alvo.get("nivel_chaser")}   # nao muda nada
        resp_upd = (sb.table("user_characters").update(mesmo)
                    .eq("id", alvo["id"]).execute())
        alteradas = len(getattr(resp_upd, "data", None) or [])
        print(f"   linhas alteradas na conta de outra pessoa: {alteradas}")
        if alteradas:
            falhas.append("CONSEGUIU GRAVAR NA CONTA DE OUTRA PESSOA")

    print("5) na tela")
    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 2.5)
    app.ir_para("guilda")
    pagina = app._paginas["guilda"]
    fim = time.time() + 15
    while time.time() < fim and pagina.perfis is None:
        _esperar(app, 0.2)
    _esperar(app, 0.5)
    paineis = [t for t in range(len(pagina.perfis or []))
               if pagina.find_withtag(f"perfil_{t}")]
    print(f"   paineis na guia: {len(paineis)} (contas: {len(perfis)})")
    if len(paineis) != len(perfis):
        falhas.append("a guia nao mostrou um painel por conta")

    if outro is not None:
        indice = next(i for i, p in enumerate(pagina.perfis)
                      if p.get("user_id") == outro["user_id"])
        _clicar(app, pagina, f"perfil_{indice}")
        conta = app._paginas.get("conta")
        fim = time.time() + 15
        while time.time() < fim and (conta is None or conta.abas is None):
            _esperar(app, 0.2)
            conta = app._paginas.get("conta")
        _esperar(app, 1.0)
        print(f"   abriu: {app.pagina_atual} | {len(conta._cards)} cards de "
              f"{guilda.nome_do_perfil(outro)}")
        if app.pagina_atual != "conta" or not conta._cards:
            falhas.append("clicar no perfil nao abriu a conta")
        elif any(c.ao_abrir or c.ao_cartas or c.ao_missao for c in conta._cards):
            falhas.append("os cards da outra conta podem ser editados")
        else:
            # clicar num card de outra pessoa nao abre edicao nenhuma
            antes = [w for w in app.winfo_children()
                     if isinstance(w, ctk.CTkToplevel)]
            _clicar(app, conta, conta._cards[0].tag)
            _esperar(app, 0.8)
            depois = [w for w in app.winfo_children()
                      if isinstance(w, ctk.CTkToplevel) and w.winfo_exists()]
            if len(depois) > len(antes):
                falhas.append("clicar num card de outra pessoa abriu uma janela")
            nivel = _num(outro.get("nivel_chaser"))
            if app.nivel_chaser == nivel and nivel != _num(
                    next(p for p in perfis if p["user_id"] == user.id)
                    ["nivel_chaser"]):
                falhas.append("os dados da outra conta vazaram para a sua")
        _clicar(app, conta, "botao_voltar")
        _esperar(app, 1.0)
        if app.pagina_atual != "guilda":
            falhas.append("Voltar para a Guilda nao voltou")
    app.modified = False
    app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nGUILDA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

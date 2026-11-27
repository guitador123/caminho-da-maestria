"""
A guia Ranking (item 19), no banco e na tela.

    python tests/integracao/teste_ranking.py [email] [senha]

Valida:
  1. ranking_da_guilda: todas as contas (as mesmas do HUB) e os
     personagens delas; sem username/e-mail; anon recusado
  2. as dungeons da conta de teste batem com as marcadas NA SEMANA ATUAL
  3. na tela: o podio mostra os 3 primeiros da categoria; a lista mostra
     TODAS as contas; trocar a categoria (clique de verdade) muda o podio
  4. trocar de personagem (clique no retrato) mostra o placar dele, do
     mais forte ao mais fraco
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
import ranking
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from dados_app import _verdadeiro

DUNGEONS = ("fornalha_infernal", "altar_da_runha", "torre_das_ilusoes_semanal",
            "void_123", "void_4", "caminho_abissal", "terra_do_julgamento")


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.02)


def _clicar(app, canvas, tag):
    x1, y1, x2, y2 = canvas.bbox(tag)
    total = float(str(canvas.cget("scrollregion")).split()[3])
    canvas.yview_moveto(max(0.0, (y1 - 150) / total))
    canvas._fixar()
    _esperar(app, 0.3)
    x = int((x1 + x2) / 2 - canvas.canvasx(0))
    y = int((y1 + y2) / 2 - canvas.canvasy(0))
    canvas.event_generate("<Motion>", x=x, y=y)
    canvas.event_generate("<Button-1>", x=x, y=y)
    canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
    _esperar(app, 0.8)


def _textos(canvas, tag):
    return [canvas.itemcget(i, "text") for i in canvas.find_withtag(tag)
            if canvas.type(i) == "text"]


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    falhas = []

    print("1) ranking_da_guilda")
    try:
        dados = db.ranking_da_guilda(sb)
    except Exception as erro:
        print(f"   FALHOU: {erro} (rode sql/ranking.sql)")
        return 1
    contas, personagens = dados["contas"], dados["personagens"]
    print(f"   {len(contas)} contas | {len(personagens)} personagens")
    hub = {p["user_id"] for p in db.perfis_da_guilda(sb)}
    if {c["user_id"] for c in contas} != hub:
        falhas.append("as contas do ranking nao sao as mesmas do HUB")
    if any("username" in c or "email" in c for c in contas):
        falhas.append("o ranking vazou username/e-mail")
    try:
        db.ranking_da_guilda(db.get_supabase())
        falhas.append("anon conseguiu chamar ranking_da_guilda")
    except Exception:
        print("   anon: recusado  OK")

    print("2) dungeons da semana atual (conta de teste)")
    pers = db.carregar_personagens(sb, user.id)
    feitas = sum(sum(1 for c in DUNGEONS if _verdadeiro(s.get(c)))
                 for s in db.carregar_semanais(sb, pers))
    minha = next(c for c in contas if c["user_id"] == user.id)
    print(f"   banco: {feitas} | ranking: {minha.get('dungeons')}")
    if int(minha.get("dungeons") or 0) != feitas:
        falhas.append("as dungeons do ranking nao batem com a semana atual")

    print("3) na tela")
    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 2.5)
    app.ir_para("ranking")
    pagina = app._paginas["ranking"]
    fim = time.time() + 15
    while time.time() < fim and pagina.dados is None:
        _esperar(app, 0.2)
    _esperar(app, 1.0)
    for chave, _rotulo, _titulo in ranking.CATEGORIAS:
        if chave != pagina.categoria:
            _clicar(app, pagina, f"cat_{chave}")
            _esperar(app, 0.5)
        if pagina.categoria != chave:
            falhas.append(f"o clique em {chave} nao trocou a categoria")
            continue
        esperado = ranking.podio(contas, chave, personagens)
        nomes_podio = _textos(pagina, "podio")
        lista = _textos(pagina, "lista")
        posicoes = [t for t in lista if t.endswith("º")]
        print(f"   {chave}: podio ok={len(nomes_podio) > 0} | lista "
              f"{len(posicoes)} contas")
        if len(posicoes) != len(contas):
            falhas.append(f"{chave}: a lista nao mostra todas as contas")
        primeiro = ranking.texto_do_valor(chave, esperado[0][1])
        if primeiro not in nomes_podio:
            falhas.append(f"{chave}: o 1o do podio nao e o esperado")

    print("4) trocar de personagem")
    alvo = next((n for n in ("Ai", "Elesis", "Uno")
                 if ranking.placar_do_personagem(personagens, n)
                 and n != pagina.personagem), None)
    if alvo:
        _clicar(app, pagina, f"ret_{alvo}")
        placar = ranking.placar_do_personagem(personagens, alvo)
        linhas = [t for t in _textos(pagina, "placar") if t.endswith("º")]
        print(f"   {alvo}: {len(linhas)} linhas (esperado {len(placar)})")
        if pagina.personagem != alvo or len(linhas) != len(placar):
            falhas.append("o placar do personagem nao abriu certo")
    app.modified = False
    app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nRANKING OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

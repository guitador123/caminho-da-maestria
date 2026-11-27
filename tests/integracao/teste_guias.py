"""
As guias do topo (Maestria, Guilda, Evolucao), com cliques de verdade.

    python tests/integracao/teste_guias.py [email] [senha]

Valida, em 1152x820 e 1920x1040:
  1. a barra esta centralizada no topo, com as 3 guias e "Maestria" ativa
  2. clicar em "Guilda" (evento no canvas) mostra a pagina da Guilda, com
     a guia dela ativa
  3. clicar em "Evolucao" na barra da Guilda mostra a Evolucao
  4. Esc volta para a Maestria NA MESMA rolagem de antes
  5. rolando a Maestria, a barra continua no topo da vista (e por cima
     dos cards)
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

RESOLUCOES = ("1152x820", "1920x1040")


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.02)


def _clicar_guia(app, canvas, barra, chave):
    """Clique de verdade no texto da guia (coordenadas da vista)."""
    x1, y1, x2, y2 = canvas.bbox(barra.itens_texto[chave])
    x = int((x1 + x2) / 2 - canvas.canvasx(0))
    y = int((y1 + y2) / 2 - canvas.canvasy(0))
    canvas.event_generate("<Motion>", x=x, y=y)
    canvas.event_generate("<Button-1>", x=x, y=y)
    canvas.event_generate("<ButtonRelease-1>", x=x, y=y)
    _esperar(app, 1.5)


def _barra_ok(canvas, barra, ativa, largura, falhas, rotulo):
    textos = [canvas.itemcget(barra.itens_texto[c], "text")
              for c in ("maestria", "guilda", "ranking", "evolucao")]
    if textos != ["Maestria", "Guilda", "Ranking", "Evolução"]:
        falhas.append(f"{rotulo}: guias = {textos}")
    if barra.ativa != ativa:
        falhas.append(f"{rotulo}: ativa = {barra.ativa} (esperado {ativa})")
    x1, y1, x2, y2 = canvas.bbox("abas")
    centro = (x1 + x2) / 2
    topo = y1 - canvas.canvasy(0)
    if abs(centro - largura / 2) > 3:
        falhas.append(f"{rotulo}: barra fora do centro ({centro} vs {largura / 2})")
    if not 0 <= topo <= 40:
        falhas.append(f"{rotulo}: barra fora do topo da vista ({topo:.0f} px)")


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    app = GrandChaseApp(user=resp.user, supabase=sb)
    _esperar(app, 2.5)
    app.ir_para("maestria")             # (o resumo semanal pode abrir sozinho)
    falhas = []

    for resolucao in RESOLUCOES:
        app.geometry(resolucao + "+0+0")
        _esperar(app, 2.0)
        largura = app.winfo_width()
        print(f"== {resolucao}")

        print("1) a barra na Maestria")
        _barra_ok(app.canvas, app._barra_maestria, "maestria", largura,
                  falhas, f"{resolucao} maestria")

        app._rolagem.ir_para(600)
        _esperar(app, 0.3)
        rolagem = app._rolagem.topo()

        print("5) rolando, a barra fica no topo e por cima")
        _barra_ok(app.canvas, app._barra_maestria, "maestria", largura,
                  falhas, f"{resolucao} rolada")
        acima = app.canvas.find_above(app.canvas.find_withtag("abas")[-1])
        if acima:
            falhas.append(f"{resolucao}: tem item por cima da barra")

        print("2) clicar em Guilda")
        _clicar_guia(app, app.canvas, app._barra_maestria, "guilda")
        guilda = app._paginas.get("guilda")
        if app.pagina_atual != "guilda" or not guilda or not guilda.visivel():
            falhas.append(f"{resolucao}: o clique em Guilda nao abriu a pagina")
            continue
        _barra_ok(guilda, guilda.barra, "guilda", largura, falhas,
                  f"{resolucao} guilda")

        print("3) clicar em Evolucao (na barra da Guilda)")
        _clicar_guia(app, guilda, guilda.barra, "evolucao")
        evolucao = app._paginas.get("evolucao")
        if app.pagina_atual != "evolucao" or not evolucao.visivel():
            falhas.append(f"{resolucao}: o clique em Evolucao nao abriu")
        elif guilda.visivel():
            falhas.append(f"{resolucao}: a Guilda continuou por cima")
        else:
            _barra_ok(evolucao, evolucao.barra, "evolucao", largura, falhas,
                      f"{resolucao} evolucao")

        print("4) Esc volta para a Maestria na mesma rolagem")
        app.focus_force()
        app.event_generate("<Escape>")
        _esperar(app, 0.6)
        if app.pagina_atual != "maestria" or evolucao.visivel():
            falhas.append(f"{resolucao}: Esc nao voltou para a Maestria")
        if abs(app._rolagem.topo() - rolagem) > 1:
            falhas.append(f"{resolucao}: a rolagem mudou "
                          f"({rolagem} -> {app._rolagem.topo()})")
        app._rolagem.ir_para(0)
        _esperar(app, 0.3)

    print(f"   cartoes da grade: {len(app.itens_valores)} (sem a Evolucao)")
    if "evolucao" in app.itens_valores:
        falhas.append("o 9o cartao ainda existe")

    app.modified = False
    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in sorted(set(falhas)):
            print("  -", f)
        return 1
    print("\nGUIAS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""
A tela NAO pula ao clicar nos filtros (Caminho Abissal, Torre das Ilusoes).

O bug: com a pagina rolada ate a barra de filtros, ligar um filtro que
esconde cards fazia a tela saltar para cima (a rolagem era guardada como
FRACAO da pagina, que encolhia) e a arte de fundo ficava deslocada (o
cenario "fixo" nao era reposicionado).

Valida, rolando ate a barra de filtros e ligando/desligando os filtros:
  1. o topo da tela fica no MESMO pixel
  2. a arte de fundo continua colada no topo da tela
  3. depois de desligar tudo, volta a lista completa no mesmo lugar

Nao grava nada no banco.

    python tests/integracao/teste_filtro_rolagem.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
import tema_visual as tv
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste


def _esperar(app, segundos=0.6):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.03)


def _situacao(app):
    topo = app.canvas.canvasy(0)
    cenario = app.canvas.coords(app._item_cenario)[1]
    visiveis = sum(1 for c in app.cards_personagem
                   if app.canvas.itemcget(c._itens[0], "state") != "hidden")
    return topo, cenario, visiveis


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    app = GrandChaseApp(user=resp.user, supabase=sb)
    app.geometry("1152x820+0+0")
    _esperar(app, 2.0)
    app.usar_supabase = False                    # NAO grava no banco
    falhas = []

    # quase todos ja fizeram Caminho Abissal e Torre (so na memoria):
    # assim o filtro "nao fez" esconde a maioria e a pagina ENCOLHE
    nomes = [c.dados.get("nome") for c in app.cards_personagem]
    for nome in nomes[3:]:
        app.marcar_missoes(nome, {"caminhoabissal": True,
                                  "torredasilusoes": True})
    _esperar(app)

    for rotulo, desce in (("na barra de filtros", -30),
                          ("no meio dos cards", 700)):
        print(f"\nrolado {rotulo}:")
        falhas += _ligar_e_desligar(app, desce)

    app.modified = False
    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nFILTRO SEM PULO OK")
    return 0


def _ligar_e_desligar(app, desce):
    falhas = []
    # rola ate a barra de filtros (+ `desce` px), como o usuario faria
    total = float(str(app.canvas.cget("scrollregion")).split()[3])
    alvo = app.lay.y(tv.FILTROS_BUSCA[1]) + desce
    app.canvas.yview_moveto(alvo / total)
    app._fixar_cenario()
    _esperar(app)
    topo0, _cen, todos = _situacao(app)
    print(f"  topo {topo0:.0f} px | {todos} cards")

    passos = [("caminhoabissal", "liga Caminho Abissal"),
              ("torredasilusoes", "liga Torre das Ilusoes"),
              ("void123", "liga Vazio 1, 2 e 3"),
              ("void4", "liga Vazio 4"),
              ("void4", "desliga Vazio 4"),
              ("void123", "desliga Vazio 1, 2 e 3"),
              ("torredasilusoes", "desliga Torre"),
              ("caminhoabissal", "desliga Caminho Abissal")]
    # o canvas rola em passos de yscrollincrement (40 px)
    passo = float(app.canvas.cget("yscrollincrement")) or 1
    anterior = topo0
    for chave, texto in passos:
        app._alternar_filtro("mazmorras", chave)
        _esperar(app)
        topo, cenario, visiveis = _situacao(app)
        # fica parada; so sobe (o necessario, nunca acima da barra de
        # filtros) quando sobraria espaco vazio embaixo
        barra = app.lay.y(tv.FILTROS_BUSCA[1]) - app.lay.h(30)
        esperado = min(anterior, max(barra, app._fim_dos_cards
                                     + app.lay.h(40)
                                     - app.canvas.winfo_height()))
        anterior = topo
        ok = abs(topo - esperado) < passo and abs(cenario - topo) <= 1
        print(f"  {texto:28s} topo {topo:6.0f} | fundo {cenario:6.0f} | "
              f"{visiveis:2d} cards  {'OK' if ok else 'FALHOU'}")
        if abs(topo - esperado) >= passo:
            falhas.append(f"{texto}: a tela foi para {topo:.0f} "
                          f"(esperado {esperado:.0f})")
        baixo = topo + app.canvas.winfo_height()
        if not any(topo - c.altura < c.y0 < baixo for c in app.cards_personagem
                   if app.canvas.itemcget(c._itens[0], "state") != "hidden"):
            if app._fim_dos_cards > topo:
                falhas.append(f"{texto}: nenhum card aparece na tela")
        if abs(cenario - topo) > 1:
            falhas.append(f"{texto}: o fundo ficou deslocado")

    if _situacao(app)[2] != todos:
        falhas.append("desligando tudo, a lista nao voltou inteira")
    return falhas


if __name__ == "__main__":
    sys.exit(main(sys.argv))

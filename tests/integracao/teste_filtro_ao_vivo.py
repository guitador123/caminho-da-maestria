"""
Os cards se reorganizam NA HORA quando um personagem muda (sem mexer em
nenhum filtro):

  1. mudar o Ataque Total troca a ordem (o maior sempre na frente)
  2. com o filtro "nao fez Caminho Abissal" ligado, marcar o Caminho
     Abissal tira o card da lista; desmarcar traz de volta
  3. o mesmo com a Torre das Ilusoes (a da SEMANA)
  4. "Zerar dungeons" traz todo mundo de volta ao filtro

Nao grava nada no banco (o salvamento fica desligado neste teste).

    python tests/integracao/teste_filtro_ao_vivo.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import tkinter.messagebox as mb

import auth
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from dados_app import _coluna_no_df


def _na_tela(app):
    """Os nomes dos cards visiveis, na ordem em que aparecem."""
    visiveis = []
    for card in app.cards_personagem:
        itens = getattr(card, "_itens", [])
        if itens and app.canvas.itemcget(itens[0], "state") != "hidden":
            visiveis.append((round(card.y0), round(card.x0),
                             card.dados.get("nome")))
    return [nome for _y, _x, nome in sorted(visiveis)]


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    mb.askyesno = lambda *a, **k: True          # o "Zerar dungeons" pergunta
    app = GrandChaseApp(user=user, supabase=sb)
    app.update()
    app.usar_supabase = False                    # NAO grava no banco
    falhas = []

    geral = app.dfs["Geral"]
    coluna_poder = _coluna_no_df(geral, "poder")
    print("1) mudar o Ataque Total troca a ordem na hora")
    antes = _na_tela(app)
    ultimo = antes[-1]
    geral[coluna_poder] = geral[coluna_poder].astype(object)
    geral.loc[geral["Nome"].astype(str) == ultimo, coluna_poder] = 999_999_999
    app._atualizar_card(ultimo)                  # o que a edicao chama
    app.update()
    depois = _na_tela(app)
    print(f"   {ultimo}: ultimo -> posicao {depois.index(ultimo) + 1}")
    if depois[0] != ultimo:
        falhas.append("o card com o maior Ataque Total nao foi para a frente")

    for chave, nome_dungeon in (("caminhoabissal", "Caminho Abissal"),
                                ("torredasilusoes", "Torre das Ilusoes")):
        print(f"2/3) filtro 'nao fez {nome_dungeon}'")
        app.filtro_mazmorras = {chave}
        app._aplicar_filtros()
        app.update()
        lista = _na_tela(app)
        alvo = lista[0]
        app.marcar_missoes(alvo, {chave: True})
        app.update()
        lista2 = _na_tela(app)
        print(f"   marcou {alvo}: {len(lista)} -> {len(lista2)} cards; "
              f"saiu da lista: {alvo not in lista2}")
        if alvo in lista2:
            falhas.append(f"marcar {nome_dungeon} nao tirou o card do filtro")
        app.marcar_missoes(alvo, {chave: False})
        app.update()
        if alvo not in _na_tela(app):
            falhas.append(f"desmarcar {nome_dungeon} nao trouxe o card de volta")

    print("4) zerar dungeons traz todo mundo de volta")
    app.filtro_mazmorras = {"caminhoabissal"}
    app._aplicar_filtros()
    for nome in _na_tela(app)[:3]:
        app.marcar_missoes(nome, {"caminhoabissal": True})
    app.update()
    escondidos = len(app.cards_personagem) - len(_na_tela(app))
    app.zerar_dungeons()
    app.update()
    print(f"   escondidos antes: {escondidos}; depois de zerar: "
          f"{len(app.cards_personagem) - len(_na_tela(app))}")
    if len(_na_tela(app)) != len(app.cards_personagem):
        falhas.append("depois de zerar, nem todos voltaram ao filtro")

    app.modified = False
    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nFILTRO AO VIVO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

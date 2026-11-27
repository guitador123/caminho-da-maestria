# -*- coding: utf-8 -*-
"""
A guia "Ranking" (item 19): regras puras, sem Tk.

  - Personagens: para cada um dos 25, todas as contas em ordem de Ataque
    Total (empate: a Soma = Ataque + Ataque Especial). O 1o e o campeao.
  - 5 podios de contas (empate: Ataque Total medio):
      fortes   - de quantos personagens a conta e a campea (1o lugar)
      level    - Level Chaser
      colecao  - colecao de cartas
      dungeons - dungeons semanais feitas na SEMANA ATUAL
      ataque   - Ataque Total medio
"""

from dados_app import _decimal, _num
from opcoes import PERSONAGENS, normalizar

CATEGORIAS = [
    # (chave, rotulo do botao, titulo)
    ("fortes", "Mais personagens fortes", "Mais personagens em 1º lugar"),
    ("level", "Level Chaser", "Maior Level Chaser"),
    ("colecao", "Coleção", "Maior coleção de cartas"),
    ("dungeons", "Dungeons", "Mais dungeons na semana"),
    ("ataque", "Ataque médio", "Maior Ataque Total médio"),
]


def soma_bruta(linha):
    return max(0, _num(linha.get("ataque"))) + max(0, _num(linha.get("ataque_especial")))


def placar_do_personagem(personagens, nome):
    """As contas com esse personagem (Ataque Total > 0), do mais forte ao
    mais fraco; empate: a Soma."""
    alvo = normalizar(nome)
    linhas = [p for p in personagens or ()
              if normalizar(p.get("character_name")) == alvo
              and _num(p.get("poder")) > 0]
    return sorted(linhas, key=lambda p: (_num(p.get("poder")), soma_bruta(p)),
                  reverse=True)


def campeoes(personagens):
    """{nome do personagem: a linha do campeao} (so quem tem Ataque > 0)."""
    saida = {}
    for nome in PERSONAGENS:
        placar = placar_do_personagem(personagens, nome)
        if placar:
            saida[nome] = placar[0]
    return saida


def titulos_por_conta(personagens):
    """{user_id: quantos personagens a conta e a campea}."""
    contagem = {}
    for linha in campeoes(personagens).values():
        uid = linha.get("user_id")
        contagem[uid] = contagem.get(uid, 0) + 1
    return contagem


def valor(conta, categoria, titulos=None):
    """O numero da conta naquela categoria."""
    if categoria == "fortes":
        return (titulos or {}).get(conta.get("user_id"), 0)
    coluna = {"level": "nivel_chaser", "colecao": "colecao_cartas",
              "dungeons": "dungeons", "ataque": "ataque_medio"}[categoria]
    return _num(conta.get(coluna))


def podio(contas, categoria, personagens=()):
    """Todas as contas em ordem na categoria (empate: Ataque medio):
    [(conta, valor), ...]."""
    titulos = titulos_por_conta(personagens) if categoria == "fortes" else None
    lista = [(c, valor(c, categoria, titulos)) for c in contas or ()]
    return sorted(lista, key=lambda par: (par[1], _num(par[0].get("ataque_medio"))),
                  reverse=True)


def texto_do_valor(categoria, numero):
    """Como o numero aparece no podio e na lista."""
    n = _num(numero)
    milhar = f"{n:,}".replace(",", ".")
    if categoria == "fortes":
        return "1 campeão" if n == 1 else f"{n} campeões"
    if categoria == "level":
        return f"Lv. {n}"
    if categoria == "dungeons":
        return f"{n} dungeon{'s' if n != 1 else ''}"
    return milhar


def status_do_personagem(linha):
    """Os 4 status mostrados no placar."""
    return {"ataque": _num(linha.get("ataque")),
            "ataque_especial": _num(linha.get("ataque_especial")),
            "critico": _decimal(linha.get("critico")),
            "dano_critico": _decimal(linha.get("dano_critico"))}

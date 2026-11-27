# -*- coding: utf-8 -*-
"""
A guilda (item 12): regras puras do HUB e da conta de outra pessoa.

  - todas as contas do app aparecem (sem opcao de ficar de fora);
  - ordem: Level Chaser (maior primeiro); empate: Ataque Total medio;
  - o top 3 ganha selo de ouro, prata e bronze;
  - a conta de outra pessoa vira as mesmas abas do app (so para ver).

Sem nada de Tk: da para testar sem abrir janela.
"""

import pandas as pd

import filtros
from config_app import ABA_ACESSORIOS, ABA_GERAL, ABA_PECAS, ABA_SEMANAIS
from dados_app import _num, _ordenar_colunas, _rotular_colunas

SEM_NICK = "Sem nick"
MEDALHAS = {1: "ouro", 2: "prata", 3: "bronze"}

ABAS_DA_CONTA = {
    "personagens": ABA_GERAL,
    "pecas_void": ABA_PECAS,
    "acessorios_titulo": ABA_ACESSORIOS,
    "semanais": ABA_SEMANAIS,
}


def ordenar(perfis):
    """Level Chaser (maior primeiro); empate: Ataque Total medio."""
    return sorted(perfis or [],
                  key=lambda p: (_num(p.get("nivel_chaser")),
                                 _num(p.get("ataque_medio"))),
                  reverse=True)


def medalha(posicao):
    """1 -> 'ouro', 2 -> 'prata', 3 -> 'bronze'; dali para baixo, None."""
    return MEDALHAS.get(posicao)


def nome_do_perfil(perfil):
    return str((perfil or {}).get("nick") or "").strip() or SEM_NICK


def abas_da_conta(conta):
    """{"personagens": [...], ...} (supabase_db.conta_da_guilda) -> as
    abas do app {"Geral": DataFrame, ...}, como no carregamento da conta."""
    abas = {}
    for logica, aba in ABAS_DA_CONTA.items():
        linhas = (conta or {}).get(logica) or []
        if not linhas:
            continue
        abas[aba] = _ordenar_colunas(_rotular_colunas(pd.DataFrame(linhas)))
    return abas


def ordem_dos_personagens(abas):
    """Os nomes do mais forte ao mais fraco (a mesma ordem da Maestria)."""
    geral = abas.get(ABA_GERAL)
    if geral is None or geral.empty or "Nome" not in geral.columns:
        return []
    nomes = [str(n) for n in geral["Nome"].tolist()]
    dados = {n: filtros.dados_filtro(geral, abas.get(ABA_SEMANAIS), n)
             for n in nomes}
    return filtros.filtrar_e_ordenar(nomes, dados)

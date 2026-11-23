# -*- coding: utf-8 -*-
"""
Funcoes puras sobre os dados das abas (dataframes, colunas, valores).

Sem nada de Tk: dá para testar sem abrir janela.
"""

import os
from config_app import ROTULOS_COLUNAS
from opcoes import coluna_banco
from supabase_db import COLUNAS


def _mesmo_arquivo(a, b):
    """True se os dois caminhos apontam para o mesmo arquivo."""
    try:
        return (os.path.normcase(os.path.abspath(a))
                == os.path.normcase(os.path.abspath(b)))
    except (TypeError, ValueError):
        return False


def _colunas_conhecidas(df, logica):
    """Colunas do dataframe que existem de verdade na tabela do banco."""
    if df is None or df.empty:
        return []
    permitidas = {coluna_banco(c) for c in COLUNAS.get(logica, [])}
    if logica == "semanais":
        permitidas.add(coluna_banco("torre_das_ilusoes"))
    if logica == "personagens":
        permitidas.add(coluna_banco("nivel_chaser"))
    achadas = []
    for coluna in df.columns:
        if coluna in ("Nome", "id", "character_id"):
            continue
        if coluna_banco(coluna) in permitidas:
            achadas.append(coluna)
    return achadas


def _rotular_colunas(df):
    """Troca os nomes do banco (snake_case) pelos rotulos da planilha."""
    if df is None or df.empty:
        return df
    troca = {}
    for coluna in df.columns:
        rotulo = ROTULOS_COLUNAS.get(coluna_banco(coluna))
        if rotulo and coluna != rotulo:
            troca[coluna] = rotulo
    return df.rename(columns=troca) if troca else df


def _verdadeiro(valor) -> bool:
    """'VERDADEIRO' / 'Verdadeiro' / True / 1 -> True."""
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    texto = str(valor).strip().lower()
    return texto in ("verdadeiro", "true", "1", "t", "sim", "x")


def _num(valor, padrao=0):
    """Converte para int (aceita None, '' e texto)."""
    if valor is None or valor == "":
        return padrao
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return padrao


def _ordenar_colunas(df):
    """Coloca 'Nome' como PRIMEIRA coluna e move 'id'/'character_id' para o FIM."""
    cols = list(df.columns)
    internas = [c for c in ("id", "character_id") if c in cols]
    if "Nome" in cols and cols[0] == "Nome" and not internas:
        return df
    nome = ["Nome"] if "Nome" in cols else []
    meio = [c for c in cols if c not in internas and c != "Nome"]
    return df[nome + meio + internas]


def _coluna_dungeon_semanal(df, chave):
    """Coluna de uma dungeon SEMANAL no dataframe.

    A Torre das Ilusoes semanal esta no banco como
    "torre_das_ilusoes_semanal", mas a chave do app e
    "torredasilusoes" - sem esta equivalencia a Torre nunca era
    encontrada (e por isso o filtro dela nao filtrava nada).
    """
    coluna = _coluna_no_df(df, chave)
    if coluna:
        return coluna
    from opcoes import mesmo_dado
    for coluna_df in (df.columns if df is not None else ()):
        if mesmo_dado(coluna_df, chave):
            return coluna_df
    return None


def _coluna_no_df(df, chave):
    """Descobre a coluna real do dataframe que corresponde a chave do banco.

    Ex.: chave 'caminho_abissal' encontra 'Caminho Abissal' na planilha e
    'caminho_abissal' no Supabase (comparacao normalizada).
    """
    if df is None or df.empty:
        return None
    alvo = coluna_banco(chave)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None

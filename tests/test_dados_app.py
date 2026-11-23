"""Funcoes puras sobre os dataframes das abas (dados_app.py)."""

import os

import pandas as pd
import pytest

from dados_app import (_coluna_dungeon_semanal, _coluna_no_df,
                       _colunas_conhecidas, _mesmo_arquivo, _num,
                       _ordenar_colunas, _rotular_colunas, _verdadeiro)


@pytest.mark.parametrize("valor, esperado", [
    (None, 0), ("", 0), ("12", 12), ("618002.0", 618002), (7.9, 7),
    ("abc", 0),
])
def test_num(valor, esperado):
    assert _num(valor) == esperado


def test_num_usa_o_padrao():
    assert _num("abc", padrao=-1) == -1


@pytest.mark.parametrize("valor, esperado", [
    (True, True), ("VERDADEIRO", True), ("x", True), ("Falso", False),
    (None, False), (0, False),
])
def test_verdadeiro(valor, esperado):
    assert _verdadeiro(valor) is esperado


def test_mesmo_arquivo(tmp_path):
    caminho = str(tmp_path / "Planilha.xlsx")
    assert _mesmo_arquivo(caminho, caminho.upper() if os.name == "nt" else caminho)
    assert _mesmo_arquivo(caminho, os.path.join(str(tmp_path), ".", "Planilha.xlsx"))
    assert not _mesmo_arquivo(caminho, str(tmp_path / "outra.xlsx"))
    assert not _mesmo_arquivo(None, caminho)


def test_ordenar_colunas_nome_primeiro_ids_no_fim():
    df = pd.DataFrame(columns=["id", "poder", "Nome", "character_id", "capa"])
    assert list(_ordenar_colunas(df).columns) == [
        "Nome", "poder", "capa", "id", "character_id"]


def test_rotular_colunas_do_banco():
    df = pd.DataFrame({"character_name": ["Elesis"], "poder": [1],
                       "fragmento_vazio_disperso": [0], "id": ["x"]})
    assert list(_rotular_colunas(df).columns) == [
        "Nome", "Poder", "Fragmento do Vazio Disperso", "id"]


def test_coluna_no_df_acha_pelo_nome_normalizado():
    df = pd.DataFrame([["Lire", True, False]],
                      columns=["Nome", "Caminho Abissal", "Void 4"])
    assert _coluna_no_df(df, "caminho_abissal") == "Caminho Abissal"
    assert _coluna_no_df(df, "void_4") == "Void 4"
    assert _coluna_no_df(df, "fornalha_infernal") is None
    assert _coluna_no_df(pd.DataFrame(), "void_4") is None


def test_torre_semanal_e_achada_pelos_dois_nomes():
    df = pd.DataFrame({"Nome": ["Lire"], "torre_das_ilusoes_semanal": [True]})
    assert _coluna_dungeon_semanal(df, "torredasilusoes") == \
        "torre_das_ilusoes_semanal"


def test_colunas_conhecidas_ignora_internas_e_estranhas():
    df = pd.DataFrame([["Lire", "a", "b", True, False, 1]],
                      columns=["Nome", "id", "character_id", "void_4",
                               "Caminho Abissal", "coluna_inventada"])
    assert _colunas_conhecidas(df, "semanais") == ["void_4", "Caminho Abissal"]

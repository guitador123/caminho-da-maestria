"""Colar nos acessorios (15.5): opcoes, cores e gravacao."""

import pytest

import supabase_db as db
from card_personagem import ACESSORIOS_CARD, CORES_NOME, cor_do_acessorio
from opcoes import coluna_banco, obter_opcoes

JULGAMENTO = "Colar do Julgamento Radiante ( Fogo Infernal )"


def test_opcoes_do_dropdown_do_mais_forte_ao_mais_fraco():
    assert obter_opcoes("Acessórios Título", "Colar") == [JULGAMENTO, "Outro"]


@pytest.mark.parametrize("valor, cor", [
    (JULGAMENTO, "azul"),
    ("colar do julgamento radiante (fogo infernal)", "azul"),  # sem acento
    ("Outro", "cinza"),
    ("", None),
    (None, None),
    ("Colar Qualquer", None),
])
def test_cor_do_colar(valor, cor):
    assert cor_do_acessorio("colar", valor) == (CORES_NOME[cor] if cor
                                                else None)


def test_as_regras_antigas_nao_mudaram():
    assert cor_do_acessorio("anel", "Anel do Ciclo Infinito") == \
        CORES_NOME["vermelho"]
    assert cor_do_acessorio("piercing", "Piercing do Piu Piu") == \
        CORES_NOME["azul"]
    assert cor_do_acessorio("tornozeleira", "Outra") is None


def test_colar_aparece_no_card_por_ultimo():
    assert ACESSORIOS_CARD[-1] == ("colar", "Colar")


def test_gravacao_so_com_a_coluna_no_banco():
    linha = {"Nome": "Ai", "Colar": JULGAMENTO, "Anel": "Anel do Piu Piu"}
    com = db._limpar(linha, "acessorios_titulo", {"colar"})
    assert com["colar"] == JULGAMENTO and com["anel"] == "Anel do Piu Piu"
    sem = db._limpar(linha, "acessorios_titulo", ())
    assert "colar" not in sem
    assert coluna_banco("Colar") == "colar"

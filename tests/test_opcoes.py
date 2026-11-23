"""Nomes de colunas e abas (opcoes.py)."""

import pytest

from opcoes import (PERSONAGENS, canonizar_aba, chave_semanal, coluna_banco,
                    mesmo_dado, normalizar, obter_opcoes)


@pytest.mark.parametrize("texto, esperado", [
    ("Torre Das Ilusões", "torredasilusoes"),
    ("  Peças (Void) ", "pecasvoid"),
    ("nivel_chaser", "nivelchaser"),
    (None, ""),
    (123, "123"),
])
def test_normalizar(texto, esperado):
    assert normalizar(texto) == esperado


def test_coluna_banco_junta_rotulo_e_coluna():
    # rotulo da planilha (com "do") e coluna do banco (sem) = mesma chave
    assert coluna_banco("Fragmento do Vazio Disperso") == \
        coluna_banco("fragmento_vazio_disperso")
    assert coluna_banco("Nível do Chaser") == coluna_banco("nivel_chaser")
    assert coluna_banco("Nome") == "charactername"


def test_torre_semanal_tem_dois_nomes():
    assert mesmo_dado("torre_das_ilusoes", "torre_das_ilusoes_semanal")
    assert chave_semanal("torre_das_ilusoes_semanal") == "torredasilusoes"
    assert chave_semanal("void_4") == "void4"


def test_canonizar_aba_tolera_espacos():
    assert canonizar_aba("Geral") == "Geral"
    assert canonizar_aba("  Semanais  ") == "Semanais"


def test_personagens_sao_25_sem_repetir():
    assert len(PERSONAGENS) == 25
    assert len(set(PERSONAGENS)) == 25


def test_obter_opcoes_campo_livre_devolve_none():
    assert obter_opcoes("Geral", "coluna_que_nao_existe") is None

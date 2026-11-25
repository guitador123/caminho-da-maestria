"""Status do personagem (15.1): soma no milhar, formatos e gravacao."""

import pytest

import supabase_db as db
from config_app import ROTULOS_COLUNAS
from dados_app import (STATUS_PERSONAGEM, abreviar_ataque, formatar_decimal,
                       formatar_percentual, soma_no_milhar)
from opcoes import coluna_banco


@pytest.mark.parametrize("ataque, especial, esperado", [
    (20000, 20000, "4.0"),          # o exemplo do usuario
    (45990, 0, "4.5"),              # corta, NAO arredonda
    (123000, 0, "12.3"),
    (9999, 0, "0.9"),
    (0, 0, "0.0"),
    ("20.000", "25.990", "4.5"),    # ponto de milhar, como no card
    (None, "", "0.0"),
    (-5000, 20000, "2.0"),          # negativo nao conta
])
def test_soma_no_milhar(ataque, especial, esperado):
    assert soma_no_milhar(ataque, especial) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (0, "0"), (850, "850"), (20000, "20k"), (20500, "20,5k"),
    (19990, "19,9k"), (99999, "99,9k"), (123456, "123k"),
    (1234567, "1,2M"), (None, "0"),
])
def test_abreviar_ataque(valor, esperado):
    assert abreviar_ataque(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (45, "45%"), (35.25, "35,25%"), (180.5, "180,5%"), ("35,259", "35,25%"),
    ("35.999", "35,99%"), ("1.250,75", "1250,75%"), ("", "0%"), (None, "0%"),
    ("abc", "0%"), (-3, "0%"), (float("nan"), "0%"), (0.1 + 0.2, "0,3%"),
])
def test_formatar_percentual(valor, esperado):
    assert formatar_percentual(valor) == esperado


def test_formatar_decimal_para_o_campo():
    assert formatar_decimal(45.0) == "45"
    assert formatar_decimal(35.25) == "35,25"
    assert formatar_decimal(None) == "0"


@pytest.mark.parametrize("valor, esperado", [
    ("35,25", 35.25), ("35.25", 35.25), ("35,259", 35.25), (35.259, 35.25),
    ("45%", 45.0), (" 1.250,5 ", 1250.5), (-1, 0.0),
    ("abc", None), ("", None), (None, None), (True, None),
])
def test_decimal_2_corta_em_2_casas(valor, esperado):
    assert db.decimal_2(valor) == esperado


def test_gravacao_converte_os_tipos():
    linha = {"Nome": "Ai", "Ataque": "20.000", "Ataque Especial": 25990.0,
             "Acerto Crítico %": "35,259", "Dano Crítico %": 180.5,
             "Dano nas Costas %": ""}
    extras = {"ataque", "ataque_especial", "critico", "dano_critico",
              "dano_costas"}
    saida = db._limpar(linha, "personagens", extras)
    assert saida["ataque"] == 20000
    assert saida["ataque_especial"] == 25990
    assert saida["critico"] == 35.25
    assert saida["dano_critico"] == 180.5
    assert saida["dano_costas"] == 0.0
    with pytest.raises(ValueError):
        db._limpar({"Acerto Crítico %": "abc"}, "personagens", extras)


def test_sem_as_colunas_no_banco_nao_envia():
    """Antes do SQL rodar, os status ficam de fora (nao quebram o salvar)."""
    saida = db._limpar({"Nome": "Ai", "Ataque": 1, "critico": 2},
                       "personagens", extras=())
    assert "ataque" not in saida and "critico" not in saida


def test_rotulos_voltam_para_a_coluna_do_banco():
    for _chave, coluna, rotulo, _tipo in STATUS_PERSONAGEM:
        assert coluna_banco(rotulo) == coluna_banco(coluna)
        assert ROTULOS_COLUNAS[coluna_banco(coluna)] == rotulo
    for chave, rotulo in ROTULOS_COLUNAS.items():
        assert coluna_banco(rotulo) == chave

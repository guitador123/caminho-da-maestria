"""Funcoes pequenas de conversao (cards, nivel do chaser, Pix)."""

import pytest

import pix_pagamento as pix
from card_personagem import _fracao, _inteiro, _verdadeiro
from dados_app import progresso_exp
from janela_nivel import validar_nivel


@pytest.mark.parametrize("valor, esperado", [
    ("13 / 13", (13, 13)), ("7/30", (7, 30)), ("5", (5, 0)),
    (None, (0, 0)), ("abc", (0, 0)),
])
def test_fracao(valor, esperado):
    assert _fracao(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    ("16 / 30", 16), (16, 16), ("618002.0", 618002), ("", 0), (None, 0),
    ("abc", 0),
])
def test_inteiro(valor, esperado):
    assert _inteiro(valor) == esperado


@pytest.mark.parametrize("valor, esperado", [
    (True, True), ("Verdadeiro", True), ("sim", True), ("FALSO", False),
    (None, False), ("", False),
])
def test_verdadeiro(valor, esperado):
    assert _verdadeiro(valor) is esperado


@pytest.mark.parametrize("texto, valor, tem_erro", [
    ("385", 385, False), (" 0 ", 0, False), ("", None, True),
    ("abc", None, True), ("3.5", None, True), ("-1", None, True),
    ("999", 999, False), ("1000", None, True),
])
def test_validar_nivel(texto, valor, tem_erro):
    resultado, erro = validar_nivel(texto)
    assert resultado == valor
    assert bool(erro) is tem_erro


@pytest.mark.parametrize("nivel, percentual, proximo", [
    (0, 0.0, 100), (5, 5.0, 100), (99, 99.0, 100),
    (100, 0.0, 200), (150, 50.0, 200), (385, 85.0, 400),
    (899, 99.0, 900), (900, 0.0, None), (999 - 33, 66 * 100 / 99, None),
    (999, 100.0, None),
    (1500, 100.0, None),          # acima do maximo: trata como 999
    (None, 0.0, 100), ("abc", 0.0, 100),
])
def test_progresso_exp_ate_o_proximo_distintivo(nivel, percentual, proximo):
    assert progresso_exp(nivel) == (percentual, proximo)


def test_barra_exp_tem_o_tamanho_pedido():
    import tema_visual as tv
    for pct in (0, 5, 100):
        assert tv.barra_exp(352, 22, pct, f"{pct}%").size == (352, 22)


@pytest.mark.parametrize("bruto, esperado", [
    ("+55 (19) 98146-6471", "+5519981466471"),
    (" fulano @email.com ", "fulano@email.com"),
    ("123e4567-e89b-12d3-a456-426614174000",
     "123e4567-e89b-12d3-a456-426614174000"),
    ("", ""),
])
def test_normalizar_chave_pix(bruto, esperado):
    assert pix.normalizar_chave(bruto) == esperado


def test_crc16_do_pix():
    # vetor conhecido do CRC16-CCITT (0x1021, inicio 0xFFFF)
    assert pix._crc16("123456789") == "29B1"


def test_payload_pix_termina_com_crc_valido():
    payload = pix.monta_payload("+5519981466471", "Fulano", valor=10)
    assert payload.startswith("000201")
    assert "BR.GOV.BCB.PIX" in payload
    assert "540510.00" in payload
    corpo, crc = payload[:-4], payload[-4:]
    assert corpo.endswith("6304")
    assert pix._crc16(corpo) == crc


# exemplo oficial do manual do BR Code (Banco Central)
EXEMPLO_BCB = ("00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-"
               "4266554400005204000053039865802BR5913Fulano de Tal6008"
               "BRASILIA62070503***63041D3D")


def test_payload_pix_igual_ao_exemplo_oficial_do_banco_central():
    assert pix.monta_payload("123e4567-e12b-12d1-a456-426655440000",
                             "Fulano de Tal", cidade="BRASILIA",
                             gui="br.gov.bcb.pix") == EXEMPLO_BCB


def test_payload_pix_tem_os_campos_do_padrao():
    campos = pix.campos_do_payload(
        pix.monta_payload("+55 (19) 98146-6471", "Fulano"))
    assert campos["00"] == "01"
    assert "01" not in campos                 # o campo invalido antigo
    assert campos["26.00"] == "BR.GOV.BCB.PIX"
    assert campos["26.01"] == "+5519981466471"   # chave normalizada
    assert campos["53"] == "986" and campos["58"] == "BR"
    assert campos["62.05"] == "***"


@pytest.mark.parametrize("estragado", [
    EXEMPLO_BCB[:-1] + "E",                   # CRC errado
    EXEMPLO_BCB.replace("5913", "5920", 1),    # tamanho de campo errado
    "lixo",
])
def test_campos_do_payload_recusa_payload_invalido(estragado):
    with pytest.raises(ValueError):
        pix.campos_do_payload(estragado)


@pytest.mark.parametrize("texto, valor, tem_erro", [
    ("0", 0, False), ("1840", 1840, False), ("2500", 2500, False),
    (" 12 ", 12, False), ("2501", None, True), ("-1", None, True),
    ("", None, True), ("abc", None, True), ("12.5", None, True),
])
def test_validar_colecao(texto, valor, tem_erro):
    from janela_nivel import validar_colecao
    resultado, erro = validar_colecao(texto)
    assert resultado == valor
    assert bool(erro) == tem_erro

"""Funcoes pequenas de conversao (cards, nivel do chaser, Pix)."""

import pytest

import pix_pagamento as pix
from card_personagem import _fracao, _inteiro, _verdadeiro
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
])
def test_validar_nivel(texto, valor, tem_erro):
    resultado, erro = validar_nivel(texto)
    assert resultado == valor
    assert bool(erro) is tem_erro


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

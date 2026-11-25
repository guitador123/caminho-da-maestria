"""Varios titulos por personagem (15.2): ordem, "Outro" e gravacao."""

import pytest

from dados_app import juntar_titulos, ler_titulos, titulos_do_jogo


def test_lista_do_jogo_sem_outro_e_na_ordem_do_dropdown():
    lista = titulos_do_jogo()
    assert lista[0] == "Origem do Caos"
    assert lista[-1] == "O Dia do Julgamento"
    assert "Outro" not in lista


@pytest.mark.parametrize("valor, esperado", [
    ("Origem do Caos", ["Origem do Caos"]),                 # dado antigo
    ("Renak | Origem do Caos", ["Origem do Caos", "Renak"]),  # reordena
    ("O Dia do Julgamento|Renak", ["Renak", "O Dia do Julgamento"]),
    ("Outro", []),                                          # nao conta
    ("Renak | Outro", ["Renak"]),
    ("renak | RENAK | Renak", ["Renak"]),     # sem repetidos, nome oficial
    ("Titulo Velho | Renak", ["Renak", "Titulo Velho"]),    # fora da lista
    ("", []), ("  |  ", []), (None, []), (float("nan"), []),
    (["Renak", "Origem do Caos"], ["Origem do Caos", "Renak"]),
])
def test_ler_titulos(valor, esperado):
    assert ler_titulos(valor) == esperado


def test_juntar_titulos_grava_do_mais_forte_ao_mais_fraco():
    assert (juntar_titulos(["Aniquilador do Vazio", "Outro", "Renak",
                            "Origem do Caos"])
            == "Origem do Caos | Renak | Aniquilador do Vazio")
    assert juntar_titulos([]) == ""
    assert juntar_titulos(None) == ""


def test_ida_e_volta():
    texto = juntar_titulos(titulos_do_jogo()[::-1])
    assert ler_titulos(texto) == titulos_do_jogo()

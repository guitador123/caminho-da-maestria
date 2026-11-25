"""Cartas dos equipamentos do Void (15.3): listas, slots, cores e banco."""

import pytest

import supabase_db as db
from card_personagem import PECAS_VOID, coluna_banco_cartas
from config_app import ROTULOS_COLUNAS
from dados_app import (CARTA_OUTRA, CARTAS_VOID, PECAS_COM_CARTAS,
                       SLOTS_CARTAS, coluna_cartas, estado_da_carta,
                       juntar_cartas, ler_cartas)
from opcoes import coluna_banco


def test_os_7_equipamentos_e_nao_os_acessorios():
    assert set(PECAS_COM_CARTAS) == {"arma", "luvas", "cota", "botas",
                                     "capa", "calca", "elmo"}
    assert set(CARTAS_VOID) == set(PECAS_COM_CARTAS)
    for acessorio in ("escudos", "asas", "facas", "mascara", "diadema"):
        assert acessorio not in CARTAS_VOID
    # todas as pecas com cartas existem no card
    assert set(PECAS_COM_CARTAS) <= {chave for chave, _ in PECAS_VOID}


def test_5_opcoes_por_peca_e_2_no_elmo_com_outra_por_ultimo():
    for peca, opcoes in CARTAS_VOID.items():
        assert len(opcoes) == (2 if peca == "elmo" else 5), peca
        assert opcoes[-1] == CARTA_OUTRA
        assert len(set(opcoes)) == len(opcoes)
    assert CARTAS_VOID["elmo"] == ["Ataque +100", "Outra"]
    assert CARTAS_VOID["cota"] == CARTAS_VOID["capa"]
    assert CARTAS_VOID["botas"] == CARTAS_VOID["calca"]
    assert CARTAS_VOID["arma"] == CARTAS_VOID["luvas"]
    assert CARTAS_VOID["cota"][2] == "Ataque +515"          # sem espaco


@pytest.mark.parametrize("valor, slots", [
    ("Ataque +555|Ataque +530||Outra", ["Ataque +555", "Ataque +530", "",
                                        "Outra"]),
    ("Ataque +100", ["Ataque +100", "", "", ""]),
    ("a|b|c|d|e", ["a", "b", "c", "d"]),                    # so 4 slots
    ("", ["", "", "", ""]), (None, ["", "", "", ""]),
    (float("nan"), ["", "", "", ""]),
])
def test_ler_cartas_sempre_4_slots(valor, slots):
    assert ler_cartas(valor) == slots
    assert len(ler_cartas(valor)) == SLOTS_CARTAS


def test_juntar_cartas_guarda_a_posicao():
    assert juntar_cartas(["", "Outra"]) == "|Outra||"
    assert juntar_cartas(["Ataque +555"] * 4) == "|".join(["Ataque +555"] * 4)
    assert juntar_cartas(["", "", "", ""]) == ""
    assert juntar_cartas(None) == ""
    texto = "Dano Crítico +31,5%/Ataque Especial +530||Outra|"
    assert juntar_cartas(ler_cartas(texto)) == texto


@pytest.mark.parametrize("carta, estado", [
    ("Ataque +555", "status"), ("Dano Crítico +28,75%", "status"),
    ("Outra", "outra"), ("outra", "outra"), ("", None), (None, None),
])
def test_cor_do_quadradinho(carta, estado):
    assert estado_da_carta(carta) == estado


def test_colunas_do_banco_e_rotulos():
    extras = db.EXTRAS_OPCIONAIS["pecas_void"]
    for peca in PECAS_COM_CARTAS:
        coluna = coluna_cartas(peca)
        assert coluna in extras
        rotulo = ROTULOS_COLUNAS[coluna_banco(coluna)]
        assert coluna_banco(rotulo) == coluna_banco(coluna)
        assert coluna_banco_cartas(peca) == coluna_banco(coluna)


def test_gravacao_e_texto_e_nao_mexe_nas_pecas():
    linha = {"Nome": "Ai", "Arma": "VERDADEIRO",
             "Cartas Cota": "Ataque +555||Outra|"}
    saida = db._limpar(linha, "pecas_void", {"cartas_cota"})
    assert saida["cartas_cota"] == "Ataque +555||Outra|"
    assert saida["arma"] is True
    assert "cartas_cota" not in db._limpar(linha, "pecas_void", ())


# ------------------------------------------------- pedra do Void (16) --
from dados_app import (NIVEL_PEDRA_MAXIMO, PEDRAS_VOID, coluna_pedra,  # noqa: E402
                       forca_da_pedra, juntar_pedra, ler_pedra, validar_pedra)


def test_status_das_pedras_fraco_e_forte():
    assert set(PEDRAS_VOID) == set(PECAS_COM_CARTAS)
    for opcoes in PEDRAS_VOID.values():
        assert len(opcoes) == 2
    assert PEDRAS_VOID["elmo"] == PEDRAS_VOID["capa"] == ["Ataque +300",
                                                          "Ataque +600"]
    assert PEDRAS_VOID["cota"] == PEDRAS_VOID["botas"]
    assert PEDRAS_VOID["arma"] == ["7% Dano Crítico", "10% Dano Crítico"]
    assert forca_da_pedra("arma", "10% Dano Crítico") == "forte"
    assert forca_da_pedra("arma", "7% Dano Crítico") == "fraca"
    assert forca_da_pedra("arma", "Ataque +600") is None   # de outra peca
    assert NIVEL_PEDRA_MAXIMO == 18


@pytest.mark.parametrize("valor, pedra", [
    ("18|10% Dano Crítico", (18, "10% Dano Crítico")),
    ("0|Ataque +300", (0, "Ataque +300")),               # +0 tambem tem status
    ("+5|Ataque +300", (5, "Ataque +300")),
    ("19|Ataque +300", (None, "")), ("-1|Ataque +300", (None, "")),
    ("18|", (None, "")), ("18", (None, "")), ("abc|x", (None, "")),
    ("", (None, "")), (None, (None, "")), (float("nan"), (None, "")),
])
def test_ler_pedra(valor, pedra):
    assert ler_pedra(valor) == pedra


@pytest.mark.parametrize("nivel, status, valido", [
    (None, "", True), ("", None, True),                 # sem pedra
    (18, "10% Dano Crítico", True), ("+0", "Ataque +300", True),
    (18, "", False),                                     # status obrigatorio
    ("", "Ataque +300", False),                          # nivel tambem
    (19, "Ataque +300", False), ("abc", "Ataque +300", False),
])
def test_status_obrigatorio_junto_do_nivel(nivel, status, valido):
    assert (validar_pedra(nivel, status) is None) == valido


def test_juntar_pedra():
    assert juntar_pedra("+18", "10% Dano Crítico") == "18|10% Dano Crítico"
    assert juntar_pedra(0, "Ataque +300") == "0|Ataque +300"
    assert juntar_pedra(None, "") == ""
    with pytest.raises(ValueError):
        juntar_pedra(18, "")
    texto = "12|Recuperação de MP 10%"
    assert juntar_pedra(*ler_pedra(texto)) == texto


def test_colunas_da_pedra():
    for peca in PECAS_COM_CARTAS:
        coluna = coluna_pedra(peca)
        assert coluna in db.EXTRAS_OPCIONAIS["pecas_void"]
        assert coluna_banco(ROTULOS_COLUNAS[coluna_banco(coluna)]) == \
            coluna_banco(coluna)

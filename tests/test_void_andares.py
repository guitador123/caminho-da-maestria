"""Void na Missao Rapida (item 17): andares 1F/2F/3F, soma e desfazer."""

from datetime import date

import pandas as pd
import pytest

import supabase_db as db
from app_missao import MissaoMixin
from config_app import ABA_GERAL, ABA_SEMANAIS, ROTULOS_COLUNAS
from dados_app import (ANDARES_VOID, VOID_CONTADOR, andar_da_semana,
                       coluna_andar, marca_andar, novo_contador)
from opcoes import coluna_banco

SEMANA = date(2026, 11, 25)


def test_tabela_de_andares():
    assert ANDARES_VOID == {"1F": 4, "2F": 8, "3F": 10}
    assert VOID_CONTADOR["void123"][0] == "vazio_uni"
    assert VOID_CONTADOR["void4"][0] == "vazio_apo"


def test_marca_e_le_o_andar_da_semana():
    assert marca_andar("3F", SEMANA) == "3F|2026-11-25"
    assert andar_da_semana("3F|2026-11-25", SEMANA) == "3F"
    # de outra semana (o reset ja zerou a dungeon): nao desfaz
    assert andar_da_semana("3F|2026-11-18", SEMANA) is None
    for invalido in ("", None, "3F", "4F|2026-11-25", float("nan")):
        assert andar_da_semana(invalido, SEMANA) is None
    with pytest.raises(ValueError):
        marca_andar("4F", SEMANA)


@pytest.mark.parametrize("atual, andar, desfazer, esperado", [
    (20, "1F", None, 24), (20, "2F", None, 28), (20, "3F", None, 30),
    ("20", "3F", None, 30), (None, "1F", None, 4),
    (30, None, "3F", 20), (5, None, "3F", 0),          # nao fica negativo
    (20, None, None, 20),
])
def test_novo_contador(atual, andar, desfazer, esperado):
    assert novo_contador(atual, andar, desfazer) == esperado


def test_colunas_do_banco_e_rotulos():
    for chave in VOID_CONTADOR:
        coluna = coluna_andar(chave)
        assert coluna in db.EXTRAS_OPCIONAIS["semanais"]
        rotulo = ROTULOS_COLUNAS[coluna_banco(coluna)]
        assert coluna_banco(rotulo) == coluna_banco(coluna)
        # a coluna do andar NAO e confundida com a da dungeon
        assert coluna_banco(coluna) != coluna_banco(chave)


# ------------------------------------------------ a logica do app ------
class _App(MissaoMixin):
    """So o que a Missao Rapida usa (sem Tk, sem banco)."""

    def __init__(self):
        self.dfs = {
            ABA_GERAL: pd.DataFrame([
                {"Nome": "Ai", "Vazio Uni.": 20, "Vazio Apo.": 5},
                {"Nome": "Lire", "Vazio Uni.": 1, "Vazio Apo.": 1}]),
            ABA_SEMANAIS: pd.DataFrame([
                {"Nome": "Ai", "Void ( 1, 2 e 3 )": "Falso", "Void 4": "Falso"},
                {"Nome": "Lire", "Void ( 1, 2 e 3 )": "Falso",
                 "Void 4": "Falso"}]),
        }
        self.usar_supabase = False
        self.salvou = 0

    def _atualizar_card(self, nome):
        pass

    def _atualizar_cards(self):
        pass

    def _marcar_modificado(self):
        pass

    def status(self, texto):
        self.ultimo_status = texto

    def valor(self, nome, coluna):
        df = self.dfs[ABA_GERAL]
        return int(df.loc[df["Nome"] == nome, coluna].iloc[0])


def test_painel_soma_no_salvar_e_so_no_personagem_certo():
    app = _App()
    assert app.marcar_missoes("Ai", {"void123": True, "void4": True},
                              andares={"void123": "3F", "void4": "1F"})
    assert app.valor("Ai", "Vazio Uni.") == 30
    assert app.valor("Ai", "Vazio Apo.") == 9
    assert app.valor("Lire", "Vazio Uni.") == 1
    assert "Void Unificado 20 → 30 (3F)" in app._ultimo_aviso_void


def test_desmarcar_desfaz_a_soma_da_semana():
    app = _App()
    app.marcar_missoes("Ai", {"void123": True}, andares={"void123": "2F"})
    assert app.valor("Ai", "Vazio Uni.") == 28
    app.marcar_missoes("Ai", {"void123": False})
    assert app.valor("Ai", "Vazio Uni.") == 20
    # desmarcar de novo (ja desmarcada) nao subtrai outra vez
    app.marcar_missoes("Ai", {"void123": False})
    assert app.valor("Ai", "Vazio Uni.") == 20


def test_marca_de_outra_semana_nao_desfaz():
    app = _App()
    app.marcar_missoes("Ai", {"void4": True}, andares={"void4": "3F"})
    df = app.dfs[ABA_SEMANAIS]
    coluna = next(c for c in df.columns if coluna_banco(c) == "void4andar")
    df.loc[df["Nome"] == "Ai", coluna] = "3F|2020-01-01"   # semana antiga
    app.marcar_missoes("Ai", {"void4": False})
    assert app.valor("Ai", "Vazio Apo.") == 15                # nao desfez


def test_outras_dungeons_nao_mexem_nos_contadores():
    app = _App()
    app.dfs[ABA_SEMANAIS]["Caminho Abissal"] = "Falso"
    app.marcar_missoes("Ai", {"caminhoabissal": True})
    assert app.valor("Ai", "Vazio Uni.") == 20
    assert app.valor("Ai", "Vazio Apo.") == 5


def test_modo_card_marca_e_soma_na_hora():
    app = _App()
    assert app._marcar_no_card("Ai", "void4", True, "2F")
    assert app.valor("Ai", "Vazio Apo.") == 13
    assert "Void Apocalipse 5 → 13 (2F)" in app.ultimo_status
    app._marcar_no_card("Ai", "void4", False)
    assert app.valor("Ai", "Vazio Apo.") == 5
    assert "desfeito o 2F" in app.ultimo_status

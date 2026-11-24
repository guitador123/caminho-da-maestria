"""Historico semanal (historico.py): fotos do banco, semana atual, numeros
e o reset de quarta 03h."""

from datetime import date, datetime, timezone

import pandas as pd
import pytest

import historico as h


def _linha(nome, semana, poder, pecas=(), desafios=()):
    """Uma linha como o banco devolve (chaves cruas do banco)."""
    todas_pecas = ["arma", "luvas", "cota", "botas", "capa", "calca", "elmo",
                   "escudos", "asas", "facas", "mascara", "diadema"]
    todos = ["fornalha_infernal", "altar_da_runha",
             "torre_das_ilusoes_semanal", "void_123", "void_4",
             "caminho_abissal", "terra_do_julgamento"]
    return {"character_name": nome, "semana": semana, "poder": poder,
            "pecas_void": {p: p in pecas for p in todas_pecas},
            "desafios": {d: d in desafios for d in todos}}


HISTORICO = [
    _linha("Elesis", "2026-11-25", 500_000, pecas=["elmo", "arma"],
           desafios=["void_4", "torre_das_ilusoes_semanal"]),
    _linha("Lire", "2026-11-25", 300_000, pecas=["diadema"],
           desafios=["caminho_abissal"]),
    _linha("Elesis", "2026-12-02", 550_000,
           pecas=["elmo", "arma", "cota", "asas"],
           desafios=["void_4", "void_123", "caminho_abissal"]),
    _linha("Lire", "2026-12-02", 310_000, pecas=["diadema", "mascara"]),
]


def test_de_historico_agrupa_por_semana_em_ordem():
    semanas = h.de_historico(list(reversed(HISTORICO)))
    assert [s["data"] for s in semanas] == [date(2026, 11, 25),
                                             date(2026, 12, 2)]
    elesis = semanas[0]["personagens"]["Elesis"]
    assert elesis["poder"] == 500_000
    assert elesis["pecas"] == {"elmo", "arma"}
    # a torre semanal do banco vira a chave do app
    assert elesis["desafios"] == {"void4", "torredasilusoes"}


def test_ataque_medio_da_conta():
    semanas = h.de_historico(HISTORICO)
    assert h.ataque_medio(semanas[0]) == 400_000
    assert h.ataque_medio(semanas[1]) == 430_000
    assert h.variacao(430_000, 400_000) == (30_000, 7.5)


def test_pecas_separadas_em_equipamentos_e_acessorios():
    semana = h.de_historico(HISTORICO)[1]
    pecas = h.contagem_pecas(semana)
    assert pecas["equipamentos"] == 3          # elmo, arma, cota (Elesis)
    assert pecas["acessorios"] == 3            # asas + diadema, mascara
    assert pecas["max_equipamentos"] == 2 * 7
    assert pecas["max_acessorios"] == 2 * 5
    assert pecas["por_peca"]["diadema"] == 1
    assert pecas["por_peca"]["escudos"] == 0


def test_desafios_semanais_feitos():
    semana = h.de_historico(HISTORICO)[0]
    desafios = h.contagem_desafios(semana)
    assert desafios["total"] == 3
    assert desafios["maximo"] == 2 * 7
    assert desafios["por_desafio"]["caminhoabissal"] == 1


def test_evolucao_por_personagem_do_mais_forte_ao_mais_fraco():
    linhas = h.evolucao_personagens(h.de_historico(HISTORICO))
    assert linhas[0] == ("Elesis", [500_000, 550_000], 550_000, 50_000)
    assert linhas[1] == ("Lire", [300_000, 310_000], 310_000, 10_000)


def test_semana_atual_a_partir_das_abas_da_tela():
    geral = pd.DataFrame([{"Nome": "Elesis", "Poder": "618.002"},
                          {"Nome": "Lire", "Poder": 10}])
    pecas = pd.DataFrame([{"Nome": "Elesis", "Elmo": "VERDADEIRO",
                           "Calça": "Verdadeiro", "Máscara": "FALSO",
                           "Escudos": True}])
    semanais = pd.DataFrame([{"Nome": "Elesis",
                              "Torre Das Ilusões": "Verdadeiro",
                              "Void ( 1, 2 e 3 )": "Verdadeiro",
                              "Void 4": "Falso"}])
    semana = h.da_tela(geral, pecas, semanais)
    elesis = semana["personagens"]["Elesis"]
    assert semana["data"] is None
    assert elesis["poder"] == 618002
    assert elesis["pecas"] == {"elmo", "calca", "escudos"}
    assert elesis["desafios"] == {"torredasilusoes", "void123"}
    assert semana["personagens"]["Lire"]["pecas"] == set()


@pytest.mark.parametrize("agora_utc, esperado", [
    # quarta 25/11 06:00 UTC = 03:00 em Brasilia: o reset acabou de rodar
    (datetime(2026, 11, 25, 6, 0, tzinfo=timezone.utc), date(2026, 11, 25)),
    # quarta 25/11 05:59 UTC = 02:59 em Brasilia: ainda vale o anterior
    (datetime(2026, 11, 25, 5, 59, tzinfo=timezone.utc), date(2026, 11, 18)),
    # domingo
    (datetime(2026, 11, 29, 15, 0, tzinfo=timezone.utc), date(2026, 11, 25)),
    # terca a noite em Brasilia (ja quarta em UTC)
    (datetime(2026, 12, 2, 2, 0, tzinfo=timezone.utc), date(2026, 11, 25)),
])
def test_ultimo_reset_quarta_tres_da_manha(agora_utc, esperado):
    assert h.ultimo_reset(agora_utc) == esperado


def test_intervalo_da_semana():
    assert h.intervalo_da_semana(date(2026, 11, 25)) == (
        date(2026, 11, 18), date(2026, 11, 24))


def test_deve_mostrar_uma_vez_por_reset():
    semanas = h.de_historico(HISTORICO)
    assert h.deve_mostrar(semanas, None) == date(2026, 12, 2)
    assert h.deve_mostrar(semanas, "2026-11-25") == date(2026, 12, 2)
    assert h.deve_mostrar(semanas, "2026-12-02") is None
    assert h.deve_mostrar([], None) is None


def test_pagina_compara_a_semana_em_destaque_com_a_anterior():
    """A tabela de personagens da pagina usa a semana EM DESTAQUE (um laco
    de desenho sobrescrevia o indice e ela mostrava a 2a semana)."""
    import pagina_evolucao as p
    semanas = h.de_historico(HISTORICO + [
        _linha("Elesis", "2026-12-09", 600_000),
        _linha("Lire", "2026-12-09", 320_000)])
    chamadas = []
    original = h.evolucao_personagens
    try:
        h.evolucao_personagens = lambda s: chamadas.append(s) or original(s)
        imagem = p.montar(semanas, None, destaque=date(2026, 12, 9))
    finally:
        h.evolucao_personagens = original
    assert imagem.width == p.LARGURA
    assert [s["data"] for s in chamadas[0]] == [
        date(2026, 11, 25), date(2026, 12, 2), date(2026, 12, 9)]


def test_marcas_do_eixo_sao_redondas():
    import pagina_evolucao as p
    assert p.marcas(0, 1) == [0, 1]
    assert p.marcas(0, 113, quantas=4) == [0, 50, 100, 150]
    assert p.marcas(620_000, 731_000) == [600_000, 650_000, 700_000, 750_000]

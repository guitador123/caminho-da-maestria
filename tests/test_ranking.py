"""A guia Ranking (item 19): campeoes, podios e desempates."""

import pytest

import ranking
import supabase_db as db


def _p(uid, nome, poder, ataque=0, especial=0, critico=0, dano=0):
    return {"user_id": uid, "character_name": nome, "poder": poder,
            "ataque": ataque, "ataque_especial": especial,
            "critico": critico, "dano_critico": dano}


PERSONAGENS = [
    _p("a", "Elesis", 900), _p("b", "Elesis", 1200), _p("c", "Elesis", 0),
    # empate no Ataque Total: a Soma desempata (b tem 30k contra 25k)
    _p("a", "Ai", 1000, 20000, 5000), _p("b", "Ai", 1000, 20000, 10000),
    _p("a", "Lire", 500),
    _p("c", "Uno", 0),                       # ninguem com Ataque: sem campeao
]
CONTAS = [
    {"user_id": "a", "nick": "A", "nivel_chaser": 300, "colecao_cartas": 10,
     "dungeons": 40, "ataque_medio": 800},
    {"user_id": "b", "nick": "B", "nivel_chaser": 300, "colecao_cartas": 99,
     "dungeons": 40, "ataque_medio": 1100},
    {"user_id": "c", "nick": "C", "nivel_chaser": 500, "colecao_cartas": 5,
     "dungeons": 175, "ataque_medio": 0},
]


def test_placar_do_personagem_e_desempate_pela_soma():
    assert [p["user_id"] for p in ranking.placar_do_personagem(PERSONAGENS, "Elesis")] \
        == ["b", "a"]                         # quem tem 0 fica de fora
    assert [p["user_id"] for p in ranking.placar_do_personagem(PERSONAGENS, "ai")] \
        == ["b", "a"]                         # mesma forca, Soma maior
    assert ranking.placar_do_personagem(PERSONAGENS, "Uno") == []


def test_campeoes_e_titulos_por_conta():
    campeoes = ranking.campeoes(PERSONAGENS)
    assert {n: c["user_id"] for n, c in campeoes.items()} == {
        "Elesis": "b", "Ai": "b", "Lire": "a"}
    assert ranking.titulos_por_conta(PERSONAGENS) == {"b": 2, "a": 1}


@pytest.mark.parametrize("categoria, ordem", [
    ("fortes", ["b", "a", "c"]),
    # empate no Level (300 x 300): o Ataque medio desempata
    ("level", ["c", "b", "a"]),
    ("colecao", ["b", "a", "c"]),
    ("dungeons", ["c", "b", "a"]),            # 40 x 40: Ataque medio
    ("ataque", ["b", "a", "c"]),
])
def test_podios(categoria, ordem):
    lista = ranking.podio(CONTAS, categoria, PERSONAGENS)
    assert [c["user_id"] for c, _n in lista] == ordem
    assert len(lista) == len(CONTAS)          # TODAS as contas na lista


def test_texto_do_valor():
    assert ranking.texto_do_valor("fortes", 1) == "1 campeão"
    assert ranking.texto_do_valor("fortes", 9) == "9 campeões"
    assert ranking.texto_do_valor("level", 431) == "Lv. 431"
    assert ranking.texto_do_valor("dungeons", 1) == "1 dungeon"
    assert ranking.texto_do_valor("colecao", 1384) == "1.384"
    assert ranking.texto_do_valor("ataque", 686758) == "686.758"


def test_as_5_categorias():
    assert [c for c, _r, _t in ranking.CATEGORIAS] == [
        "fortes", "level", "colecao", "dungeons", "ataque"]


def test_ranking_da_guilda_chama_a_funcao_do_banco():
    class _Cliente:
        def rpc(self, nome, params):
            assert (nome, params) == ("ranking_da_guilda", {})

            class _R:
                data = {"contas": CONTAS}

            class _C:
                def execute(self):
                    return _R()
            return _C()
    assert db.ranking_da_guilda(_Cliente()) == {"contas": CONTAS,
                                                "personagens": []}

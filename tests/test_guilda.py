"""A guilda (item 12): ordem do HUB, medalhas e a conta de outra pessoa."""

import guilda
import supabase_db as db
from config_app import ABA_ACESSORIOS, ABA_GERAL, ABA_PECAS, ABA_SEMANAIS


def test_ordem_por_level_chaser_e_desempate_pelo_ataque_medio():
    perfis = [
        {"nick": "A", "nivel_chaser": 300, "ataque_medio": 900_000},
        {"nick": "B", "nivel_chaser": 431, "ataque_medio": 990_000},
        {"nick": "C", "nivel_chaser": 431, "ataque_medio": 1_060_839},
        {"nick": "D", "nivel_chaser": None, "ataque_medio": None},
        {"nick": "E", "nivel_chaser": "612", "ataque_medio": "1.203.651"},
    ]
    assert [p["nick"] for p in guilda.ordenar(perfis)] == ["E", "C", "B", "A", "D"]
    assert guilda.ordenar(None) == []


def test_medalhas_so_no_top_3():
    assert [guilda.medalha(n) for n in range(1, 6)] == [
        "ouro", "prata", "bronze", None, None]


def test_nome_do_perfil():
    assert guilda.nome_do_perfil({"nick": " Kaiser "}) == "Kaiser"
    assert guilda.nome_do_perfil({"nick": ""}) == guilda.SEM_NICK
    assert guilda.nome_do_perfil(None) == guilda.SEM_NICK


class _ClienteFalso:
    def __init__(self, dados):
        self.dados = dados
        self.chamadas = []

    def rpc(self, nome, params):
        self.chamadas.append((nome, params))
        cliente = self

        class _Resp:
            data = cliente.dados

        class _Chamada:
            def execute(self):
                return _Resp()
        return _Chamada()


CONTA = {
    "perfil": {"nick": "Kaiser", "avatar": "sieghart"},
    "personagens": [
        {"id": "p1", "character_name": "Ai", "poder": 900, "nivel_chaser": 612},
        {"id": "p2", "character_name": "Lire", "poder": 1200, "nivel_chaser": 612},
    ],
    "pecas_void": [{"id": "x", "character_id": "p1", "arma": True,
                    "elmo": False, "cartas_cota": "Ataque +555|||"}],
    "acessorios_titulo": [{"id": "y", "character_id": "p2",
                           "titulo": "Renak | Origem do Caos"}],
    "semanais": [{"id": "z", "character_id": "p2", "void_4": True}],
}


def test_conta_da_guilda_vem_no_formato_das_abas():
    cliente = _ClienteFalso(CONTA)
    conta = db.conta_da_guilda(cliente, "uid-kaiser")
    assert cliente.chamadas == [("conta_da_guilda", {"p_user": "uid-kaiser"})]
    assert [p["Nome"] for p in conta["personagens"]] == ["Ai", "Lire"]
    assert conta["pecas_void"][0]["Nome"] == "Ai"
    # booleanos como no carregamento da sua conta (planilha)
    assert conta["pecas_void"][0]["arma"] == "VERDADEIRO"
    assert conta["semanais"][0]["void_4"] == "Verdadeiro"
    assert conta["acessorios_titulo"][0]["Nome"] == "Lire"

    abas = guilda.abas_da_conta(conta)
    assert set(abas) == {ABA_GERAL, ABA_PECAS, ABA_ACESSORIOS, ABA_SEMANAIS}
    assert abas[ABA_GERAL].columns[0] == "Nome"
    assert "Poder" in abas[ABA_GERAL].columns          # rotulo da planilha
    # do mais forte ao mais fraco, como na Maestria
    assert guilda.ordem_dos_personagens(abas) == ["Lire", "Ai"]


def test_conta_vazia_nao_quebra():
    abas = guilda.abas_da_conta(db.conta_da_guilda(_ClienteFalso({}), "x"))
    assert abas == {}
    assert guilda.ordem_dos_personagens(abas) == []


def test_perfis_da_guilda_chama_a_funcao_do_banco():
    cliente = _ClienteFalso([{"user_id": "a", "nivel_chaser": 1}])
    assert db.perfis_da_guilda(cliente) == [{"user_id": "a", "nivel_chaser": 1}]
    assert cliente.chamadas == [("perfis_da_guilda", {})]

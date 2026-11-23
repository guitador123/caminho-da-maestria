"""Conversao e salvamento (supabase_db.py), com um cliente Supabase FALSO."""

import pytest

import supabase_db as db


class _Resposta:
    def __init__(self, data=None):
        self.data = data


class _Consulta:
    """table(...).select(...).limit(...).execute() sempre funciona
    (= todas as colunas opcionais existem)."""

    def __getattr__(self, _nome):
        return lambda *a, **k: self

    def execute(self):
        return _Resposta([])


class ClienteFalso:
    def __init__(self, erro_rpc=None):
        self.chamadas = []
        self.erro_rpc = erro_rpc
        self.lotes = []

    def table(self, nome):
        cliente = self

        class _Tabela(_Consulta):
            def upsert(self, linhas, **k):
                cliente.lotes.append((nome, "upsert", linhas))
                return self

            def insert(self, linhas, **k):
                cliente.lotes.append((nome, "insert", linhas))
                return self
        return _Tabela()

    def rpc(self, nome, params):
        self.chamadas.append((nome, params))
        cliente = self

        class _Rpc:
            def execute(self):
                if cliente.erro_rpc:
                    raise cliente.erro_rpc
                dados = params["dados"]
                return _Resposta({k: len(v) for k, v in dados.items()})
        return _Rpc()


class ErroApi(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


# ----------------------------------------------------------- conversoes
@pytest.mark.parametrize("valor, esperado", [
    (True, True), (0, False), (1.0, True), ("Verdadeiro", True),
    ("FALSO", False), ("", False), ("sim", True), ("não", False),
])
def test_bool(valor, esperado):
    assert db._bool(valor) is esperado


def test_bool_recusa_texto_qualquer():
    with pytest.raises(ValueError):
        db._bool("talvez")


def test_limpar_converte_tipos_e_ignora_colunas_estranhas():
    saida = db._limpar({"Nome": "Elesis", "poder": "618002.0",
                        "vazio_uni": None, "libertacao": None,
                        "coluna_inventada": 1, "id": None},
                       "personagens")
    assert saida["character_name"] == "Elesis"
    assert saida["poder"] == 618002
    assert saida["vazio_uni"] == 0          # inteiro vazio vira 0
    assert saida["libertacao"] == ""        # texto vazio vira ""
    assert "coluna_inventada" not in saida
    assert "id" not in saida                # id vazio nao vai


def test_limpar_booleanas_da_planilha():
    saida = db._limpar({"arma": "VERDADEIRO", "luvas": "FALSO",
                        "cota": None}, "pecas_void")
    assert saida == {"arma": True, "luvas": False, "cota": False}


def test_limpar_numero_invalido_avisa():
    with pytest.raises(ValueError):
        db._limpar({"poder": "muito"}, "personagens")


# --------------------------------------------------------- so_alteradas
def test_so_alteradas_fica_com_o_que_mudou_e_com_o_novo():
    original = {"semanais": [{"id": "a", "void_4": False},
                             {"id": "b", "void_4": False}]}
    atual = {"semanais": [{"id": "a", "void_4": False},
                          {"id": "b", "void_4": True},
                          {"void_4": True, "_nome": "Lire"}]}
    saida = db.so_alteradas(atual, original)
    assert saida["semanais"] == [{"id": "b", "void_4": True},
                                 {"void_4": True, "_nome": "Lire"}]


# ------------------------------------------------- deteccao de erros
def test_coluna_ausente():
    assert db.coluna_ausente(ErroApi("42703", "column x does not exist"))
    assert db.coluna_ausente(ErroApi("PGRST204", "nao achei"))
    assert not db.coluna_ausente(ErroApi("08006", "sem conexao"))


def test_rpc_indisponivel():
    assert db._rpc_indisponivel(ErroApi(
        "PGRST202", "Could not find the function public.salvar_conta"))
    assert not db._rpc_indisponivel(ErroApi("42501", "permission denied"))


# --------------------------------------------------------- salvar_conta
def _conta():
    geral = [{"Nome": n, "id": f"id-{n}", "poder": 10} for n in ("Elesis", "Lire")]
    semanais = [{"Nome": n, "id": f"s-{n}", "character_id": f"id-{n}",
                 "void_4": False} for n in ("Elesis", "Lire")]
    return {"Geral": geral, "Semanais": semanais}


def test_salvar_conta_manda_so_o_que_mudou_pela_rpc():
    cliente = ClienteFalso()
    originais = _conta()
    dados = _conta()
    dados["Geral"][1]["poder"] = 99
    res = db.salvar_conta(cliente, "uid", dados, originais)

    assert len(cliente.chamadas) == 1
    nome, params = cliente.chamadas[0]
    assert nome == "salvar_conta"
    enviados = params["dados"]
    assert [p["id"] for p in enviados["personagens"]] == ["id-Lire"]
    assert enviados["semanais"] == []
    assert "user_id" not in enviados["personagens"][0]   # o banco poe
    assert res["atomico"] is True
    assert res["salvos"]["personagens"] == 1


def test_salvar_conta_sem_mudanca_nao_chama_o_banco():
    cliente = ClienteFalso()
    res = db.salvar_conta(cliente, "uid", _conta(), _conta())
    assert cliente.chamadas == []
    assert sum(res["salvos"].values()) == 0


def test_salvar_conta_sem_originais_manda_tudo():
    cliente = ClienteFalso()
    db.salvar_conta(cliente, "uid", _conta())
    enviados = cliente.chamadas[0][1]["dados"]
    assert len(enviados["personagens"]) == 2
    assert len(enviados["semanais"]) == 2


def test_salvar_conta_sem_a_funcao_no_banco_usa_o_jeito_antigo():
    erro = ErroApi("PGRST202", "Could not find the function salvar_conta")
    cliente = ClienteFalso(erro_rpc=erro)
    res = db.salvar_conta(cliente, "uid", _conta())
    assert res["atomico"] is False
    tabelas = [nome for nome, _modo, _linhas in cliente.lotes]
    assert "user_characters" in tabelas and "user_semanais" in tabelas


def test_salvar_conta_outro_erro_do_banco_sobe():
    cliente = ClienteFalso(erro_rpc=ErroApi("42501", "permission denied"))
    with pytest.raises(ErroApi):
        db.salvar_conta(cliente, "uid", _conta())
    assert cliente.lotes == []      # nao tenta gravar pela metade


def test_linha_filha_sem_character_id_vai_com_o_nome():
    cliente = ClienteFalso()
    dados = {"Semanais": [{"Nome": "Lire", "void_4": True}]}
    db.salvar_conta(cliente, "uid", dados)
    linha = cliente.chamadas[0][1]["dados"]["semanais"][0]
    assert linha["_nome"] == "Lire"
    assert "character_id" not in linha

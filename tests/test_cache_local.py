"""Modo offline (cache_local.py): copia da conta, contas memorizadas
(protegidas pelo Windows) e o que conta como "sem internet"."""

import socket

import httpx
import pytest

import cache_local as c


@pytest.fixture(autouse=True)
def pasta_temporaria(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "PASTA", str(tmp_path))
    monkeypatch.setattr(c, "ITERACOES", 1_000)     # rapido nos testes
    return tmp_path


DADOS = {"Geral": [{"Nome": "Elesis", "Poder": 600_000}]}


def test_copia_ida_e_volta():
    assert c.ler_copia("u1") is None
    assert c.salvar_copia("u1", DADOS, DADOS, {"nick": "Fulano"})
    copia = c.ler_copia("u1")
    assert copia["dados"] == DADOS and copia["pendente"] is False
    assert copia["perfil"] == {"nick": "Fulano"}
    # sem perfil novo: mantem o anterior
    c.salvar_copia("u1", {"Geral": []}, DADOS, pendente=True)
    copia = c.ler_copia("u1")
    assert copia["pendente"] is True and copia["perfil"]["nick"] == "Fulano"
    assert c.salvar_perfil("u1", {"nick": "Outro"})
    assert c.ler_copia("u1")["pendente"] is True


def test_copia_corrompida_vira_none(pasta_temporaria):
    (pasta_temporaria / "u2.json").write_text("{quebrado", encoding="utf-8")
    assert c.ler_copia("u2") is None


def test_login_offline_confere_a_senha_e_exige_copia():
    c.memorizar_conta("Fulano@Email.com ", "u1", "segredo1", "tok-1")
    # sem copia dos dados ainda: nao ha o que abrir
    assert c.conta_offline("fulano@email.com", "segredo1") is None
    c.salvar_copia("u1", DADOS, DADOS)
    assert c.conta_offline("fulano@email.com", "segredo1") == {
        "user_id": "u1", "email": "fulano@email.com"}
    assert c.conta_offline("fulano@email.com", "errada") is None
    assert c.conta_offline("outro@email.com", "segredo1") is None


def test_arquivo_de_contas_nao_tem_senha_nem_token_legivel(pasta_temporaria):
    c.memorizar_conta("a@b.com", "u1", "minhasenha123", "tok-secreto")
    bruto = (pasta_temporaria / "contas.bin").read_bytes()
    for trecho in (b"minhasenha123", b"tok-secreto", b"a@b.com"):
        assert trecho not in bruto


def test_token_trocado_e_esquecer():
    c.memorizar_conta("a@b.com", "u1", "x", "tok-1")
    c.atualizar_token("u1", "tok-2")
    assert c.token_da_conta("u1") == "tok-2"
    c.atualizar_token("u9", "tok-3")             # conta nao memorizada
    assert c.token_da_conta("u9") is None
    c.esquecer_conta("A@B.com")
    assert c.token_da_conta("u1") is None


@pytest.mark.parametrize("erro, esperado", [
    (httpx.ConnectError("[Errno 11001] getaddrinfo failed"), True),
    (httpx.ReadTimeout("timed out"), True),
    (socket.gaierror(11001, "getaddrinfo failed"), True),
    (ConnectionResetError(), True),
    (ValueError("Invalid login credentials"), False),
    (RuntimeError("new row violates row-level security policy"), False),
])
def test_erro_de_rede(erro, esperado):
    assert c.eh_erro_de_rede(erro) is esperado


def test_erro_de_rede_embrulhado():
    try:
        try:
            raise httpx.ConnectError("sem rede")
        except httpx.ConnectError as interno:
            raise RuntimeError("falhou ao salvar") from interno
    except RuntimeError as externo:
        assert c.eh_erro_de_rede(externo)

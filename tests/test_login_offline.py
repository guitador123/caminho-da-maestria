"""Login sem internet (login.entrar): so a conta memorizada, com a senha
certa e com copia dos dados neste PC."""

import httpx
import pytest

import auth
import cache_local
import login


@pytest.fixture(autouse=True)
def sem_internet(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_local, "PASTA", str(tmp_path))
    monkeypatch.setattr(cache_local, "ITERACOES", 1_000)

    def falhar(_email, _senha):
        raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")
    monkeypatch.setattr(auth, "login", falhar)


def test_conta_memorizada_entra_offline():
    cache_local.memorizar_conta("a@b.com", "u1", "senha123", "tok")
    cache_local.salvar_copia("u1", {"Geral": []}, {"Geral": []})
    sb, resp = login.entrar("A@b.com", "senha123")
    assert resp.offline is True
    assert resp.user.id == "u1" and resp.user.email == "a@b.com"
    assert sb is not None


def test_senha_errada_offline():
    cache_local.memorizar_conta("a@b.com", "u1", "senha123")
    cache_local.salvar_copia("u1", {"Geral": []}, {"Geral": []})
    with pytest.raises(RuntimeError, match="senha não confere"):
        login.entrar("a@b.com", "outra")


def test_conta_nao_memorizada_explica_como_liberar():
    with pytest.raises(RuntimeError, match="Memorizar conta"):
        login.entrar("a@b.com", "senha123")


def test_senha_errada_com_internet_nao_vira_offline(monkeypatch):
    def recusar(_email, _senha):
        raise RuntimeError("Invalid login credentials")
    monkeypatch.setattr(auth, "login", recusar)
    cache_local.memorizar_conta("a@b.com", "u1", "senha123")
    cache_local.salvar_copia("u1", {"Geral": []}, {"Geral": []})
    with pytest.raises(RuntimeError, match="Invalid login"):
        login.entrar("a@b.com", "senha123")

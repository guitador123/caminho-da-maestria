"""Assinatura das releases (assinatura.py), com uma chave de TESTE gerada
na hora (a chave real nunca e usada aqui)."""

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

import assinatura


@pytest.fixture
def chave_teste(tmp_path, monkeypatch):
    privada = Ed25519PrivateKey.generate()
    pem = tmp_path / "chave_teste.pem"
    pem.write_bytes(privada.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption()))
    monkeypatch.setenv("GC_CHAVE_RELEASE", str(pem))
    publica = privada.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    return publica


@pytest.fixture
def pacote(tmp_path):
    caminho = tmp_path / "Caminho-da-Maestria.zip"
    caminho.write_bytes(b"conteudo do programa" * 1000)
    return caminho


def test_chave_publica_embutida_tem_32_bytes():
    assert len(bytes.fromhex(assinatura.CHAVE_PUBLICA_HEX)) == 32


def test_assinatura_valida_confere(chave_teste, pacote):
    sig = assinatura.assinar(str(pacote))
    assert assinatura.verificar(str(pacote), sig, chave_teste)


def test_zip_adulterado_e_recusado(chave_teste, pacote):
    sig = assinatura.assinar(str(pacote))
    pacote.write_bytes(pacote.read_bytes() + b"codigo do invasor")
    assert not assinatura.verificar(str(pacote), sig, chave_teste)


def test_sig_adulterado_e_recusado(chave_teste, pacote):
    sig = assinatura.assinar(str(pacote))
    linhas = sig.splitlines()
    ultimo = linhas[1][-1]
    linhas[1] = linhas[1][:-1] + ("0" if ultimo != "0" else "1")
    assert not assinatura.verificar(str(pacote), "\n".join(linhas), chave_teste)


@pytest.mark.parametrize("sig", ["", "lixo", "sha256 abc\n", None])
def test_sig_vazio_ou_incompleto_e_recusado(chave_teste, pacote, sig):
    assert not assinatura.verificar(str(pacote), sig, chave_teste)


def test_chave_de_invasor_e_recusada(chave_teste, pacote):
    sig = assinatura.assinar(str(pacote))
    # a chave REAL embutida no app nao aceita a assinatura da chave de teste
    assert not assinatura.verificar(str(pacote), sig)

# -*- coding: utf-8 -*-
"""
Teste da assinatura das releases (sem rede, sem GitHub).

Simula o download da release (troca o `_pedir` do atualizacao.py por uma
copia local) e confere que o app:

  1) INSTALA uma release com assinatura valida;
  2) RECUSA um .zip adulterado (1 byte diferente);
  3) RECUSA um .sig adulterado;
  4) RECUSA uma release SEM .sig;
  5) RECUSA uma release assinada por OUTRA chave (ex.: um invasor);
  6) a chave publica embutida e a da chave privada deste PC (se houver).

Nada e instalado de verdade: o `_agendar_troca` tambem e trocado.

    python teste_assinatura.py
"""

import os
import shutil
import sys
import tempfile
import zipfile

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import assinatura
import atualizacao

falhas = []


def checar(ok, texto):
    print(("   OK  " if ok else "   FALHOU  ") + texto)
    if not ok:
        falhas.append(texto)


def _montar_release(pasta, chave_pem):
    """Cria um zip de release falso e assina com a chave dada."""
    zip_caminho = os.path.join(pasta, "release.zip")
    with zipfile.ZipFile(zip_caminho, "w") as pacote:
        pacote.writestr("Caminho da Maestria.exe", b"MZ" + b"\0" * 64)
        pacote.writestr("_internal/assets/versao.txt", "abc1234\n")
    antes = os.environ.get("GC_CHAVE_RELEASE")
    os.environ["GC_CHAVE_RELEASE"] = chave_pem
    try:
        sig = assinatura.assinar(zip_caminho)
    finally:
        if antes is None:
            os.environ.pop("GC_CHAVE_RELEASE", None)
        else:
            os.environ["GC_CHAVE_RELEASE"] = antes
    return zip_caminho, sig


def _instalaria(zip_caminho, sig):
    """Roda o _atualizar_com_release com o 'download' local."""
    agendado = {}

    def pedir(url, destino=None):
        if url.endswith(".sig"):
            if sig is None:
                raise OSError("404 (sem .sig na release)")
            with open(destino, "w", encoding="ascii") as arquivo:
                arquivo.write(sig)
        else:
            shutil.copyfile(zip_caminho, destino)
        return True

    originais = (atualizacao._pedir, atualizacao._agendar_troca)
    atualizacao._pedir = pedir
    atualizacao._agendar_troca = lambda novos, **k: agendado.setdefault(
        "pasta", novos)
    try:
        resultado = atualizacao._atualizar_com_release()
    finally:
        atualizacao._pedir, atualizacao._agendar_troca = originais
        if agendado.get("pasta"):
            # a pasta temporaria que o auxiliar apagaria
            shutil.rmtree(os.path.dirname(agendado["pasta"].rstrip("\\/")),
                          ignore_errors=True)
    return resultado and bool(agendado)


def _chave_temporaria(pasta, nome):
    """Uma chave de teste (NAO e a chave real de publicacao)."""
    caminho = os.path.join(pasta, nome)
    with open(caminho, "wb") as arquivo:
        arquivo.write(Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()))
    return caminho


def main():
    pasta = tempfile.mkdtemp(prefix="teste_assinatura_")
    chave_publica_real = assinatura.CHAVE_PUBLICA_HEX
    try:
        # chave "do projeto" para o teste (a real nao precisa estar aqui)
        chave_ok = _chave_temporaria(pasta, "projeto.pem")
        os.environ["GC_CHAVE_RELEASE"] = chave_ok
        assinatura.CHAVE_PUBLICA_HEX = assinatura.chave_publica_da_privada()
        os.environ.pop("GC_CHAVE_RELEASE")

        print("1) release com assinatura valida:")
        zip_ok, sig_ok = _montar_release(pasta, chave_ok)
        checar(_instalaria(zip_ok, sig_ok), "instalou")

        print("2) .zip adulterado (1 byte):")
        adulterado = os.path.join(pasta, "adulterado.zip")
        dados = bytearray(open(zip_ok, "rb").read())
        dados[-30] ^= 0xFF
        open(adulterado, "wb").write(bytes(dados))
        checar(not _instalaria(adulterado, sig_ok), "recusou")

        print("3) .sig adulterado:")
        linhas = sig_ok.splitlines()
        assinatura_hex = linhas[1].split()[1]
        trocado = ("0" if assinatura_hex[0] != "0" else "1") + assinatura_hex[1:]
        sig_ruim = f"{linhas[0]}\ned25519 {trocado}\n"
        checar(not _instalaria(zip_ok, sig_ruim), "recusou")

        print("4) release SEM .sig:")
        checar(not _instalaria(zip_ok, None), "recusou")

        print("5) assinada por OUTRA chave (invasor):")
        chave_invasor = _chave_temporaria(pasta, "invasor.pem")
        zip_inv, sig_inv = _montar_release(pasta, chave_invasor)
        checar(not _instalaria(zip_inv, sig_inv), "recusou")
    finally:
        assinatura.CHAVE_PUBLICA_HEX = chave_publica_real
        shutil.rmtree(pasta, ignore_errors=True)

    print("6) a chave publica embutida no app:")
    checar(len(chave_publica_real) == 64, "esta preenchida (32 bytes)")
    if os.path.exists(assinatura.caminho_chave_privada()):
        checar(assinatura.chave_publica_da_privada() == chave_publica_real,
               "e a da chave privada deste PC")
    else:
        print("   (sem a chave privada neste PC: nao da para comparar)")

    print()
    if falhas:
        print(f"ASSINATURA COM PROBLEMA ({len(falhas)})")
        return 1
    print("ASSINATURA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

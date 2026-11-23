# -*- coding: utf-8 -*-
"""
Assinatura das releases (Ed25519).

Por que assinar (e nao so publicar um hash): se alguem invadir a conta do
GitHub, ele troca o .zip E o hash juntos. Com assinatura, a CHAVE PRIVADA
fica so no PC de quem publica (fora do repositorio e fora do GitHub) e o
app instalado traz a CHAVE PUBLICA embutida. Sem a chave privada nao da
para fazer uma release que o app aceite.

  - `publicar_release.py` assina o .zip e sobe o `<zip>.sig` junto;
  - `atualizacao.py` baixa os dois e SO instala se a assinatura bater.

A chave privada fica em (nessa ordem):
  1. a variavel de ambiente GC_CHAVE_RELEASE (caminho do .pem);
  2. %USERPROFILE%\\.caminho-da-maestria\\chave_release.pem

    python assinatura.py gerar        (cria a chave; so uma vez na vida)
    python assinatura.py publica      (mostra a chave publica)

GUARDE UMA COPIA DA CHAVE PRIVADA (pendrive, gerenciador de senhas).
Se ela se perder, os .exe instalados nao aceitam mais atualizacao
automatica: so reinstalando com um instalador novo (com a chave nova).
"""

import hashlib
import os
import sys

# a chave PUBLICA (pode ficar no codigo: so serve para CONFERIR)
CHAVE_PUBLICA_HEX = "30112f3e8417e5f9a5d63c19e373c44799f9c72b4fea97e59ba8791bb771ebec"

# o texto assinado leva um prefixo (a assinatura nao serve para outro uso)
_PREFIXO = b"caminho-da-maestria/release/v1\n"


def caminho_chave_privada():
    """Onde fica a chave privada (fora do repositorio)."""
    caminho = os.environ.get("GC_CHAVE_RELEASE")
    if caminho:
        return caminho
    return os.path.join(os.path.expanduser("~"), ".caminho-da-maestria",
                        "chave_release.pem")


def sha256_arquivo(caminho):
    """O SHA-256 (hex) de um arquivo, lido aos pedacos."""
    resumo = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _mensagem(sha256_hex):
    return _PREFIXO + sha256_hex.lower().encode("ascii")


def assinar(caminho_zip):
    """Conteudo do arquivo .sig: 'sha256 <hex>' e 'ed25519 <hex>'."""
    from cryptography.hazmat.primitives import serialization

    with open(caminho_chave_privada(), "rb") as arquivo:
        chave = serialization.load_pem_private_key(arquivo.read(),
                                                   password=None)
    sha = sha256_arquivo(caminho_zip)
    assinatura = chave.sign(_mensagem(sha)).hex()
    return f"sha256 {sha}\ned25519 {assinatura}\n"


def verificar(caminho_zip, conteudo_sig, chave_publica_hex=None):
    """True se o .sig confere com o arquivo e com a chave publica."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PublicKey)

    chave_hex = chave_publica_hex or CHAVE_PUBLICA_HEX
    if not chave_hex:
        return False
    campos = {}
    for linha in (conteudo_sig or "").splitlines():
        partes = linha.strip().split()
        if len(partes) == 2:
            campos[partes[0].lower()] = partes[1].strip().lower()
    sha_declarado = campos.get("sha256", "")
    assinatura_hex = campos.get("ed25519", "")
    if not sha_declarado or not assinatura_hex:
        return False
    sha_real = sha256_arquivo(caminho_zip)
    if sha_real != sha_declarado:
        return False
    try:
        chave = Ed25519PublicKey.from_public_bytes(bytes.fromhex(chave_hex))
        chave.verify(bytes.fromhex(assinatura_hex), _mensagem(sha_real))
        return True
    except (InvalidSignature, ValueError):
        return False


def chave_publica_da_privada():
    """A chave publica (hex) da chave privada guardada neste PC."""
    from cryptography.hazmat.primitives import serialization

    with open(caminho_chave_privada(), "rb") as arquivo:
        chave = serialization.load_pem_private_key(arquivo.read(),
                                                   password=None)
    return chave.public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()


def gerar():
    """Cria a chave privada (se ainda nao existir) e mostra a publica."""
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey)

    caminho = caminho_chave_privada()
    if os.path.exists(caminho):
        print(f"a chave ja existe: {caminho} (nao foi sobrescrita)")
    else:
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        pem = Ed25519PrivateKey.generate().private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption())
        with open(caminho, "xb") as arquivo:
            arquivo.write(pem)
        print(f"chave privada criada: {caminho}")
        print("GUARDE UMA COPIA DELA EM LUGAR SEGURO (fora do PC).")
    print(f"chave publica: {chave_publica_da_privada()}")


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else ""
    if comando == "gerar":
        gerar()
    elif comando == "publica":
        print(chave_publica_da_privada())
    else:
        print(__doc__)

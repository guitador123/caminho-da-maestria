# -*- coding: utf-8 -*-
"""
Modo offline: a copia local da conta e o login sem internet (sem Tk).

Fica em %LOCALAPPDATA%\\Caminho da Maestria\\offline\\ (junto do log):

  <user_id>.json   a copia da conta, gravada a cada carga e a cada
                   salvamento:
                     {"dados":     {aba: [linhas]},  # o que esta na tela
                      "originais": {aba: [linhas]},  # o que esta no banco
                      "perfil":    {...},            # nick, foto, preferencias
                      "pendente":  true/false,       # falta enviar ao banco?
                      "atualizado_em": "..."}
                   Com "pendente", o envio manda so as linhas que mudaram
                   (dados x originais): personagens nao mexidos aqui ficam
                   como estao no banco.

  contas.bin       as contas MEMORIZADAS neste PC, protegidas pelo Windows
                   (DPAPI: so este usuario do Windows abre o arquivo):
                     {email: {"user_id", "verificador", "refresh_token"}}
                   "verificador" e um hash PBKDF2 da senha (nunca a senha):
                   confere a senha no login offline. "refresh_token"
                   reabre a sessao do Supabase quando a internet volta.

So contas com "Memorizar conta" marcado entram offline; desmarcar apaga a
conta deste arquivo.
"""

import base64
import ctypes
import hashlib
import hmac
import json
import os
import socket
from ctypes import wintypes
from datetime import datetime

from registro import PASTA as _PASTA_LOG, falha

PASTA = os.path.join(_PASTA_LOG, "offline")
ITERACOES = 200_000


def _caminho(nome):
    os.makedirs(PASTA, exist_ok=True)
    return os.path.join(PASTA, nome)


def _gravar(caminho, conteudo: bytes):
    """Grava de uma vez (arquivo temporario + troca): nunca fica pela metade."""
    temporario = caminho + ".tmp"
    with open(temporario, "wb") as arquivo:
        arquivo.write(conteudo)
    os.replace(temporario, caminho)


# ------------------------------------------------------------ erro de rede
def eh_erro_de_rede(erro) -> bool:
    """A falha foi falta de conexao (e nao senha errada, RLS, etc.)?"""
    try:
        import httpx
        tipos_httpx = (httpx.TransportError,)
    except Exception:
        tipos_httpx = ()
    visto = set()
    while erro is not None and id(erro) not in visto:
        visto.add(id(erro))
        if isinstance(erro, tipos_httpx + (socket.gaierror, ConnectionError,
                                           TimeoutError)):
            return True
        texto = str(erro).lower()
        if any(trecho in texto for trecho in (
                "getaddrinfo failed", "name or service not known",
                "connection refused", "network is unreachable",
                "timed out", "connecterror", "failed to establish")):
            return True
        erro = erro.__cause__ or erro.__context__
    return False


# ------------------------------------------------------- a copia da conta
def _arquivo_copia(user_id):
    return _caminho(f"{user_id}.json")


def salvar_copia(user_id, dados, originais, perfil=None, pendente=False):
    """Grava a copia da conta. Devolve True se gravou."""
    if not user_id:
        return False
    try:
        anterior = ler_copia(user_id) or {}
        copia = {
            "dados": dados,
            "originais": originais,
            "perfil": perfil if perfil is not None
            else anterior.get("perfil", {}),
            "pendente": bool(pendente),
            "atualizado_em": datetime.now().isoformat(timespec="seconds"),
        }
        _gravar(_arquivo_copia(user_id),
                json.dumps(copia, ensure_ascii=False, default=str)
                .encode("utf-8"))
        return True
    except Exception as erro:
        falha("[Offline] gravar a copia local", erro)
        return False


def ler_copia(user_id):
    """A copia da conta (dict) ou None."""
    if not user_id:
        return None
    try:
        with open(_arquivo_copia(user_id), "r", encoding="utf-8") as arquivo:
            copia = json.load(arquivo)
        return copia if isinstance(copia.get("dados"), dict) else None
    except FileNotFoundError:
        return None
    except Exception as erro:
        falha("[Offline] ler a copia local", erro)
        return None


def salvar_perfil(user_id, perfil):
    """Atualiza so o perfil da copia (nick, foto, preferencias)."""
    copia = ler_copia(user_id)
    if copia is None:
        return False
    return salvar_copia(user_id, copia["dados"], copia.get("originais"),
                        perfil, copia.get("pendente", False))


# --------------------------------------------- DPAPI (protecao do Windows)
class _Blob(ctypes.Structure):
    _fields_ = [("cbData", wintypes.DWORD),
                ("pbData", ctypes.POINTER(ctypes.c_char))]


def _dpapi(dados: bytes, proteger: bool) -> bytes:
    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    buffer = ctypes.create_string_buffer(dados, len(dados))
    entrada = _Blob(len(dados), ctypes.cast(buffer, ctypes.POINTER(ctypes.c_char)))
    saida = _Blob()
    funcao = crypt32.CryptProtectData if proteger else crypt32.CryptUnprotectData
    # CRYPTPROTECT_UI_FORBIDDEN = 0x1: nunca abre janela
    if not funcao(ctypes.byref(entrada), None, None, None, None, 0x1,
                  ctypes.byref(saida)):
        raise OSError("DPAPI falhou")
    try:
        return ctypes.string_at(saida.pbData, saida.cbData)
    finally:
        kernel32.LocalFree(saida.pbData)


def _ler_contas():
    try:
        with open(_caminho("contas.bin"), "rb") as arquivo:
            return json.loads(_dpapi(arquivo.read(), proteger=False))
    except FileNotFoundError:
        return {}
    except Exception as erro:
        falha("[Offline] ler as contas memorizadas", erro)
        return {}


def _gravar_contas(contas):
    try:
        _gravar(_caminho("contas.bin"),
                _dpapi(json.dumps(contas).encode("utf-8"), proteger=True))
        return True
    except Exception as erro:
        falha("[Offline] gravar as contas memorizadas", erro)
        return False


def _verificador(senha, sal=None):
    sal = sal or os.urandom(16)
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal,
                                ITERACOES)
    return (base64.b64encode(sal).decode() + "$"
            + base64.b64encode(chave).decode())


def _senha_confere(senha, verificador):
    try:
        sal, _chave = verificador.split("$", 1)
        esperado = _verificador(senha, base64.b64decode(sal))
        return hmac.compare_digest(esperado, verificador)
    except Exception:
        return False


def _normal(email):
    return str(email or "").strip().lower()


# ------------------------------------------------- contas memorizadas ----
def memorizar_conta(email, user_id, senha, refresh_token=None):
    """Guarda a conta para entrar offline (depois de um login com internet)."""
    contas = _ler_contas()
    contas[_normal(email)] = {"user_id": str(user_id),
                              "verificador": _verificador(senha),
                              "refresh_token": refresh_token or ""}
    return _gravar_contas(contas)


def esquecer_conta(email):
    """'Memorizar conta' desmarcado: a conta nao entra mais offline."""
    contas = _ler_contas()
    if contas.pop(_normal(email), None) is not None:
        _gravar_contas(contas)


def conta_memorizada(email):
    """A conta pode entrar offline neste PC (ja tem dados guardados)?"""
    conta = _ler_contas().get(_normal(email))
    return bool(conta) and ler_copia(conta.get("user_id")) is not None


def conta_offline(email, senha):
    """{"user_id", "email"} se a conta esta memorizada, a senha confere e
    ha uma copia dos dados; senao None."""
    conta = _ler_contas().get(_normal(email))
    if not conta or not _senha_confere(senha, conta.get("verificador", "")):
        return None
    if ler_copia(conta["user_id"]) is None:
        return None
    return {"user_id": conta["user_id"], "email": _normal(email)}


def atualizar_token(user_id, refresh_token):
    """O Supabase troca o refresh token de tempos em tempos: guarda o novo
    (so para contas memorizadas)."""
    if not refresh_token:
        return
    contas = _ler_contas()
    for conta in contas.values():
        if conta.get("user_id") == str(user_id):
            if conta.get("refresh_token") != refresh_token:
                conta["refresh_token"] = refresh_token
                _gravar_contas(contas)
            return


def token_da_conta(user_id):
    for conta in _ler_contas().values():
        if conta.get("user_id") == str(user_id):
            return conta.get("refresh_token") or None
    return None

"""Log de erros (registro.py)."""

import os
import sys
from tkinter import TclError

import registro


def _log():
    return open(registro.ARQUIVO, encoding="utf-8").read()


def test_registrar_grava_linha():
    registro.registrar("linha simples")
    assert "linha simples" in _log()


def test_falha_grava_traceback_uma_vez_por_sessao():
    def quebra():
        return 1 / 0
    for _ in range(3):
        try:
            quebra()
        except ZeroDivisionError:
            resumo = registro.falha("dividir")
    assert resumo == "ZeroDivisionError: division by zero"
    texto = _log()
    assert texto.count("[ERRO] dividir") == 1
    assert "Traceback" in texto and "quebra" in texto


def test_protegido_ignora_o_esperado_e_registra_o_resto():
    with registro.protegido("tk", ignorar=TclError):
        raise TclError("janela fechada")
    with registro.protegido("outro", ignorar=TclError):
        raise KeyError("x")
    texto = _log()
    assert "janela fechada" not in texto
    assert "[ERRO] outro: KeyError" in texto


def test_roda_o_arquivo_quando_fica_grande(monkeypatch):
    registro.registrar("primeira")
    monkeypatch.setattr(registro, "LIMITE_BYTES", 10)
    registro.registrar("depois de rodar")
    assert os.path.exists(registro.ARQUIVO + ".1")
    assert _log().strip().endswith("depois de rodar")


def test_funciona_sem_console(monkeypatch):
    # no .exe sem console o sys.stdout e None
    monkeypatch.setattr(sys, "stdout", None)
    registro.registrar("sem console")
    assert "sem console" in _log()

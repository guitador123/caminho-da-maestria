"""Configuracao comum dos testes (pytest).

- Os modulos do app ficam em src/: entram no sys.path (a raiz NAO entra:
  la o app_grandchase.py e so o atalho).
- Os logs (registro.py e atualizacao.py) vao para uma pasta temporaria,
  para os testes nao sujarem o log real.
- `raiz`: UMA janela Tk para a suite inteira. Criar varios tk.Tk() no
  mesmo processo as vezes falha no Python do Anaconda ("Can't find a
  usable tk.tcl"); os testes de canvas usam esta e destroem so o que criam.
"""

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(RAIZ, "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)


@pytest.fixture(autouse=True)
def _logs_temporarios(tmp_path, monkeypatch):
    import registro
    import atualizacao
    monkeypatch.setattr(registro, "PASTA", str(tmp_path))
    monkeypatch.setattr(registro, "ARQUIVO", str(tmp_path / "gc_app.log"))
    monkeypatch.setattr(registro, "_ja_registrados", set())
    monkeypatch.setattr(atualizacao, "LOG",
                        str(tmp_path / "log_atualizacao.log"))
    yield


@pytest.fixture(scope="session")
def raiz():
    import tkinter as tk
    try:
        janela = tk.Tk()
    except tk.TclError as erro:
        pytest.skip(f"sem tela para o Tk: {erro}")
    janela.geometry("400x500+0+0")
    yield janela
    janela.destroy()

"""Configuracao comum dos testes (pytest).

- Os modulos do app ficam na raiz do projeto: entram no sys.path.
- Os logs (registro.py e atualizacao.py) vao para uma pasta temporaria,
  para os testes nao sujarem o log real.
"""

import os
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


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

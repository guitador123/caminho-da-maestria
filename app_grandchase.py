# -*- coding: utf-8 -*-
"""
Atalho para abrir o Caminho da Maestria a partir do codigo-fonte.

O codigo do app fica em `src/`. Este arquivo continua na raiz porque os
PCs da guilda que usam o modo git (`iniciar.bat`, `atualizar.bat` e o
auto-update de versoes antigas) abrem exatamente `app_grandchase.py`
nesta pasta. NAO mova nem renomeie.

    python app_grandchase.py
"""

import os
import runpy
import sys

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")

if __name__ == "__main__":
    sys.path.insert(0, SRC)
    runpy.run_path(os.path.join(SRC, "app_grandchase.py"),
                   run_name="__main__")
else:
    raise ImportError(
        "o app fica em src/: coloque src/ no sys.path antes de "
        "'import app_grandchase' (este arquivo e so o atalho da raiz)")

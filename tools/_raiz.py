"""Coloca src/ (o codigo do app) no sys.path.

Os scripts desta pasta fazem `import _raiz` antes de importar os modulos
do app (auth, supabase_db, app_grandchase...).
"""

import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = AQUI
while not os.path.isdir(os.path.join(RAIZ, "src")):
    RAIZ = os.path.dirname(RAIZ)
for _pasta in (os.path.join(RAIZ, "src"),
               os.path.join(RAIZ, "tests", "integracao")):
    if _pasta not in sys.path:
        sys.path.insert(0, _pasta)

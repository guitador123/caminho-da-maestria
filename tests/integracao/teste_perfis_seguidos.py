"""
Bug (1.5.0): abrir perfis na Guilda FECHAVA o app.

Cada imagem do Tk ocupa um bitmap do Windows (limite ~10.000 por
programa). A Maestria sozinha usava ~3.400 e cada conta aberta somava
~3.500 sem soltar a anterior: no 3o perfil o Tk fechava o app ("Fail to
allocate bitmap"). Agora as imagens iguais dos cards sao compartilhadas e
a conta anterior e liberada.

    python tests/integracao/teste_perfis_seguidos.py [email] [senha]

Valida: a Maestria usa poucos bitmaps; abrir 10 perfis seguidos (o
fluxo do usuario, com a lista da Guilda carregando junto) nao faz o
numero crescer e o app continua vivo.
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import ctypes
import sys
import time

import auth
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

_k = ctypes.windll.kernel32
_u = ctypes.windll.user32
_k.GetCurrentProcess.restype = ctypes.c_void_p
_u.GetGuiResources.argtypes = [ctypes.c_void_p, ctypes.c_uint]

LIMITE_MAESTRIA = 1500      # antes: ~3.400
LIMITE_CRESCIMENTO = 400    # bitmaps a mais depois de 10 perfis


def _bitmaps():
    return _u.GetGuiResources(_k.GetCurrentProcess(), 0)   # GDI objects


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.01)


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    falhas = []
    app = GrandChaseApp(user=resp.user, supabase=sb)
    _esperar(app, 2.5)
    app.ir_para("maestria")
    _esperar(app, 0.5)
    maestria = _bitmaps()
    print(f"Maestria: {maestria} bitmaps (antes: ~3.400)")
    if maestria > LIMITE_MAESTRIA:
        falhas.append(f"a Maestria usa {maestria} bitmaps")

    app.ir_para("guilda")
    guilda = app._paginas["guilda"]
    fim = time.time() + 15
    while time.time() < fim and guilda.perfis is None:
        _esperar(app, 0.2)
    outros = [p for p in guilda.perfis if p.get("user_id") != app.user_id]
    if not outros:
        print("so existe a conta de teste: nada para abrir")
        app.destroy()
        return 0

    depois_do_1o = None
    for vez in range(10):
        # o fluxo do usuario: volta para a Guilda (que recarrega a lista)
        # e ja clica num perfil, com as duas buscas ao mesmo tempo
        app.ir_para("guilda")
        _esperar(app, 0.05)
        app.ver_conta(outros[vez % len(outros)])
        conta = app._paginas["conta"]
        fim = time.time() + 15
        while time.time() < fim and conta.abas is None:
            _esperar(app, 0.2)
        _esperar(app, 0.6)
        agora = _bitmaps()
        print(f"   perfil {vez + 1}: {agora} bitmaps")
        if depois_do_1o is None:
            depois_do_1o = agora
    if agora - depois_do_1o > LIMITE_CRESCIMENTO:
        falhas.append(f"os bitmaps crescem a cada perfil ({depois_do_1o} -> {agora})")

    app.modified = False
    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nPERFIS SEGUIDOS OK (o app continua vivo)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

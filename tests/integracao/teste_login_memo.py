"""
Teste do fluxo "Memorizar conta" da tela de login.

    python teste_login_memo.py [email] [senha]

Valida:
  1. a conta e salva em login_prefs.json depois de um login bem-sucedido
  2. a conta volta preenchida (+ checkbox marcada) na proxima abertura
  3. desmarcar "Memorizar conta" apaga a conta salva
  4. o botao do canvas realmente dispara o login
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import json
import os
import sys
import time
from credenciais_teste import conta_teste

import caminhos
from login import LoginApp, _ler_prefs, _salvar_prefs


def main(argv):
    email, senha = conta_teste(argv)

    arquivo = caminhos.preferencias()
    print("prefs:", arquivo)
    _salvar_prefs({})          # comeca limpo

    # ---- 1) login com a opcao marcada ----------------------------------
    app = LoginApp({})
    app.update_idletasks()
    app._aplicar_conta_memorizada()
    app.update()

    app.ent_email.insert(0, email)
    app.ent_senha.insert(0, senha)
    app._alternar_check("memorizar")     # marca a caixa (e redesenha)
    app.update()

    print("   caixa marcada:", app._checks["memorizar"])
    if not app._checks["memorizar"]:
        print("   FALHOU: a caixa nao marcou")
        return 1

    # dispara o login pelo botao do canvas
    app._acao_principal()
    app.update()
    for _ in range(40):
        app.update()
        time.sleep(0.15)
        if app.resultado.get("user"):
            break
    usuario = app.resultado.get("user")
    print("   login:", usuario.email if usuario else "FALHOU")
    try:
        app.destroy()
    except Exception:
        pass                      # a janela ja foi fechada pelo login
    if not usuario:
        return 1

    prefs = _ler_prefs()
    print("   prefs:", prefs)
    if prefs.get("email") != email or not prefs.get("lembrar"):
        print("   FALHOU: a conta nao foi memorizada")
        return 1

    # ---- 2) proxima abertura: conta preenchida --------------------------
    app2 = LoginApp({})
    app2.update_idletasks()
    app2._aplicar_conta_memorizada()
    app2.update()
    print("   email preenchido:", repr(app2.ent_email.get()))
    print("   caixa marcada:", app2._checks["memorizar"])
    if app2.ent_email.get() != email:
        print("   FALHOU: o email nao voltou preenchido")
        app2.destroy()
        return 1
    if not app2._checks["memorizar"]:
        print("   FALHOU: a caixa nao voltou marcada")
        app2.destroy()
        return 1

    # ---- 3) desmarcar apaga a conta --------------------------------------
    app2._checks["memorizar"] = False
    app2._alternar_memorizar()
    prefs = _ler_prefs()
    print("   prefs depois de desmarcar:", prefs)
    if prefs.get("email"):
        print("   FALHOU: a conta nao foi apagada")
        app2.destroy()
        return 1
    app2.destroy()

    print("\nMEMORIZAR CONTA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

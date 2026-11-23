"""
Teste do Nivel do Chaser no Supabase (pendencia #3).

    python teste_nivel_supabase.py [email] [senha]

Valida:
  1. se a coluna `user_characters.nivel_chaser` existe no banco
  2. se existe: grava o nivel, recarrega o app do zero e confere que voltou
  3. se NAO existe: o app continua funcionando (o salvamento nao quebra)
  4. o valor e restaurado ao final
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from credenciais_teste import conta_teste

import customtkinter as ctk

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

import auth
from app_grandchase import GrandChaseApp


def _esperar_salvamento(app, limite=400):
    for _ in range(limite):
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            for _ in range(20):
                app.update()
                time.sleep(0.03)
            return True
    return False


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.update()

    tem_coluna = app._nivel_no_banco()
    print(f"1) coluna user_characters.nivel_chaser existe? {tem_coluna}")
    print(f"   nivel carregado: {app.nivel_chaser}")
    if not tem_coluna:
        print("   -> rode sql/nivel_chaser.sql no Supabase para gravar")
        print("   -> conferindo que o app NAO quebra sem a coluna...")

    # o valor original (para restaurar no final)
    original = app.nivel_chaser
    valor_teste = 4242 if tem_coluna else original

    # --- grava -----------------------------------------------------------
    print(f"\n2) gravando o nivel {valor_teste}:")
    if not app.definir_nivel_chaser(valor_teste):
        print("   FALHOU: definir_nivel_chaser retornou False")
        return 1
    app.update()
    time.sleep(0.3)
    app.update()
    if app.usar_supabase:
        app.salvar_supabase()
    if not _esperar_salvamento(app):
        print("   FALHOU: o salvamento nao terminou")
        return 1
    print(f"   status: {app.status_var.get()}")

    # o salvamento nao pode ter falhado (a coluna opcional e ignorada)
    if "Erro ao salvar" in app.status_var.get():
        print("   FALHOU: o salvamento deu erro")
        return 1
    print("   -> salvamento OK")

    if not tem_coluna:
        app.destroy()
        print("\nNIVEL DO CHASER (sem a coluna) OK")
        print("Falta apenas rodar: sql/nivel_chaser.sql")
        return 0

    # --- recarrega do zero ----------------------------------------------
    print("\n3) recarregando o app do zero:")
    app.destroy()
    time.sleep(1.0)

    app2 = GrandChaseApp(user=user, supabase=sb)
    app2.update_idletasks()
    app2.update()
    time.sleep(1.5)
    app2.update()
    print(f"   nivel recarregado: {app2.nivel_chaser}")
    if app2.nivel_chaser != valor_teste:
        print(f"   FALHOU: veio {app2.nivel_chaser} (esperado {valor_teste})")
        app2.destroy()
        return 1
    print("   -> OK: o nivel voltou do banco")

    # --- restaura --------------------------------------------------------
    app2.definir_nivel_chaser(original)
    app2.update()
    time.sleep(0.3)
    app2.update()
    app2.salvar_supabase()
    _esperar_salvamento(app2)
    print(f"   restaurado para {original}")
    app2.destroy()

    print("\nNIVEL DO CHASER (Supabase) OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""
Teste do salvamento em SEGUNDO PLANO (pendencia #1).

Valida:
  1. `salvar_supabase()` devolve imediatamente (a interface nao congela)
  2. durante o envio a interface continua respondendo (update() nao trava)
  3. o resultado aparece na barra de status (sem nenhuma janela de aviso)
  4. o valor gravado chega no Supabase (e e restaurado no final)
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from credenciais_teste import conta_teste

import tkinter.messagebox as mb

# nenhuma janela de aviso pode aparecer durante o teste
mb.showinfo = lambda *a, **k: print("!!! showinfo:", a)
mb.showwarning = lambda *a, **k: print("!!! showwarning:", a)
mb.showerror = lambda *a, **k: print("!!! showerror:", a)
mb.askyesno = lambda *a, **k: True

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp

ALVO = "Ai"
COLUNA = "Poder"


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = resp.user
    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(0.6)
    app.update()

    df = app.dfs["Geral"]
    mask = df["Nome"].astype(str) == ALVO
    original = df.loc[mask, COLUNA].iloc[0]
    print(f"1) {ALVO}.{COLUNA} original = {original}")

    # altera o valor
    df.loc[mask, COLUNA] = 987654
    app.modified = True

    # --- 1) o chamador nao pode bloquear ------------------------------
    inicio = time.time()
    app.salvar_supabase()
    decorrido = time.time() - inicio
    print(f"2) salvar_supabase() retornou em {decorrido:.3f}s "
          f"(precisa ser < 1s)")
    if decorrido > 1.0:
        print("   FALHOU: a chamada travou a interface")
        return 1

    # --- 2) a interface continua viva durante o envio ------------------
    ticks = 0
    while app._salvando and ticks < 200:
        app.update()
        ticks += 1
        time.sleep(0.02)
    print(f"3) interface responsiva durante o envio ({ticks} ciclos de update)")
    if ticks >= 200:
        print("   FALHOU: o envio nao terminou")
        return 1

    # deixa o polling da UI aplicar o resultado
    for _ in range(40):
        app.update()
        time.sleep(0.05)
        if not app._salvando and app.status_var.get().startswith("Salvo"):
            break

    status = app.status_var.get()
    print(f"4) status: {status!r}")
    if not status.startswith("Salvo"):
        print("   FALHOU: o status nao confirmou o salvamento")
        return 1
    if "fora do banco" in status:
        print("   AVISO: colunas fora do banco ->", status)

    # --- 3) o valor chegou no banco -----------------------------------
    p = db.carregar_personagens(sb, user.id)
    gravado = next(x for x in p if x["Nome"] == ALVO)["poder"]
    print(f"5) no Supabase: poder = {gravado}")
    if int(gravado) != 987654:
        print("   FALHOU: o valor nao chegou no banco")
        return 1

    # --- 4) restaura ---------------------------------------------------
    df.loc[mask, COLUNA] = original
    app.modified = True
    app.salvar_supabase()
    for _ in range(200):
        app.update()
        time.sleep(0.03)
        if not app._salvando:
            break
    for _ in range(20):
        app.update()
        time.sleep(0.05)
    p = db.carregar_personagens(sb, user.id)
    voltou = next(x for x in p if x["Nome"] == ALVO)["poder"]
    print(f"6) restaurado: poder = {voltou}")
    if int(voltou) != int(original):
        print("   FALHOU: nao restaurou")
        return 1

    # --- 5) nenhuma linha duplicada nas tabelas filhas -----------------
    from collections import Counter
    for logica, func in (("pecas", db.carregar_pecas_void),
                         ("acess", db.carregar_acessorios_titulo),
                         ("sem", db.carregar_semanais)):
        linhas = func(sb, db.carregar_personagens(sb, user.id))
        c = Counter(l.get("character_id") for l in linhas)
        dups = [k for k, v in c.items() if v > 1]
        print(f"7) {logica}: {len(linhas)} linhas | duplicados: {dups}")
        if dups:
            print("   FALHOU: ha linhas duplicadas")
            return 1

    app.destroy()
    print("\nSALVAMENTO ASYNC OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

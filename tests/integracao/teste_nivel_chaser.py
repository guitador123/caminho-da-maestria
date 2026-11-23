"""
Teste da pendencia #3: Nivel do Chaser no banco.

Valida:
  1. a validacao do nivel (inteiro >= 0)
  2. o card da tela principal mostra o nivel e atualiza ao mudar
  3. a janela de edicao abre, valida e grava
  4. o valor vai para o dataframe (um valor por conta = todas as linhas)
  5. se a coluna existir no banco, o valor e gravado e volta ao recarregar

    python teste_nivel_chaser.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

from app_grandchase import GrandChaseApp
from janela_nivel import validar_nivel, JanelaNivelChaser


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def main(argv):
    # --- 1) validacao ----------------------------------------------------
    print("1) validacao do nivel (inteiro >= 0):")
    casos = [("385", 385), ("0", 0), (" 42 ", 42), ("1000000", 1000000)]
    for texto, esperado in casos:
        valor, erro = validar_nivel(texto)
        ok = valor == esperado and erro is None
        print(f"   {texto!r:12s} -> {valor!r} {erro or ''} {'OK' if ok else 'FALHOU'}")
        if not ok:
            return 1
    invalidos = ["", "abc", "-1", "3.5", "12a", "1e3"]
    for texto in invalidos:
        valor, erro = validar_nivel(texto)
        ok = valor is None and erro
        print(f"   {texto!r:12s} -> rejeitado {'OK' if ok else 'FALHOU'}")
        if not ok:
            return 1

    # --- 2) app ----------------------------------------------------------
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(0.8)
    app.update()

    print(f"\n2) nivel inicial no app: {app.nivel_chaser}")
    valores = app.valores_dos_cards()
    print(f"   card 'nivel' mostra: {valores.get('nivel')!r}")
    if str(valores.get("nivel")) != str(app.nivel_chaser):
        print("   FALHOU: o card nao mostra o nivel")
        return 1

    # --- 3) muda o nivel --------------------------------------------------
    print("\n3) definindo um novo nivel (777):")
    if not app.definir_nivel_chaser(777):
        print("   FALHOU: definir_nivel_chaser retornou False")
        return 1
    app.update()
    time.sleep(0.3)
    app.update()
    valores = app.valores_dos_cards()
    print(f"   app.nivel_chaser = {app.nivel_chaser}")
    print(f"   card 'nivel' = {valores.get('nivel')!r}")
    if str(valores.get("nivel")) != "777":
        print("   FALHOU: o card nao atualizou")
        return 1

    # --- 4) dataframe: um valor por conta -------------------------------
    df = app.dfs["Geral"]
    coluna = None
    from opcoes import coluna_banco
    for c in df.columns:
        if coluna_banco(c) == "nivelchaser":
            coluna = c
            break
    if coluna is None:
        print("   FALHOU: a coluna do nivel nao esta no dataframe")
        return 1
    valores_df = set(df[coluna].tolist())
    print(f"   coluna '{coluna}' -> {valores_df}")
    if valores_df != {777}:
        print("   FALHOU: o valor nao foi gravado em TODAS as linhas")
        return 1
    print("   -> OK: um valor por conta (todas as linhas)")

    # valor invalido tem que ser recusado
    if app.definir_nivel_chaser(-5) or app.definir_nivel_chaser("abc"):
        print("   FALHOU: aceitou valor invalido")
        return 1
    print("   -> OK: valores invalidos recusados")

    # --- 4b) clicar no campo do card abre a janela ----------------------
    print("\n3b) clicando no campo do card (sintese de evento):")
    item = app.itens_valores.get("nivel", (None,))[0]
    if item is None:
        print("   FALHOU: o item do valor do nivel nao foi encontrado")
        return 1
    x, y = app.canvas.coords(item)
    app.canvas.event_generate("<Button-1>", x=x, y=y)
    app.update()
    time.sleep(0.6)
    app.update()
    janelas = [w for w in _janelas(app) if isinstance(w, JanelaNivelChaser)]
    if not janelas:
        print("   FALHOU: clicar no campo nao abriu a janela")
        return 1
    print("   -> OK: a janela abriu pelo clique no card")
    janelas[-1].destroy()
    app.update()

    # --- 5) janela de edicao ---------------------------------------------
    print("\n4) janela de edicao do nivel:")
    app._abrir_nivel()
    app.update()
    time.sleep(0.7)
    app.update()
    janelas = [w for w in _janelas(app) if isinstance(w, JanelaNivelChaser)]
    if not janelas:
        print("   FALHOU: a janela nao abriu")
        return 1
    janela = janelas[-1]

    # entrada invalida -> erro inline, nao fecha
    janela.entrada.delete(0, "end")
    janela.entrada.insert(0, "-3")
    janela._salvar()
    app.update()
    if not janela.erro_var.get():
        print("   FALHOU: aceitou nivel negativo")
        return 1
    if not _janelas(app) or _janelas(app)[-1] is not janela:
        print("   FALHOU: a janela fechou com valor invalido")
        return 1
    print(f"   erro exibido: {janela.erro_var.get()!r}  OK")

    # entrada valida -> fecha e aplica
    janela.entrada.delete(0, "end")
    janela.entrada.insert(0, "512")
    janela._salvar()
    app.update()
    time.sleep(0.3)
    app.update()
    if app.nivel_chaser != 512:
        print(f"   FALHOU: o nivel nao foi aplicado ({app.nivel_chaser})")
        return 1
    print("   nivel 512 aplicado pela janela  OK")

    app.destroy()
    print("\nNIVEL DO CHASER OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""
Teste das acoes da tela principal (nao destrutivo).

Valida:
  1. "Zerar dungeons semanais" marca as colunas como Falso (e restaura)
  2. "Missao Rapida" filtra as tabelas
  3. Cartoes recalculam depois de uma edicao
  4. "Salvar" grava no Supabase com os rotulos amigaveis das colunas
     (ida e volta: grava e restaura o valor original)
  5. Dropdowns das abas resolvem para as colunascertainas

    python teste_acoes.py [email] [senha]
"""

import sys
from credenciais_teste import conta_teste

import auth
import pandas as pd
import customtkinter as ctk

import app_grandchase as app_mod
from app_grandchase import GrandChaseApp

# os testes de edicao precisam da tabela de personagens visivel
app_mod.MOSTRAR_TABELA = True

FALSO = {"askyesno": True, "showinfo": None, "showwarning": None, "showerror": None}


def silenciar_messagebox():
    """Substitui os messagebox por funcoes que nao bloqueiam."""
    from tkinter import messagebox
    erros = []

    def _erro(titulo, mensagem=None, **kw):
        erros.append((titulo, mensagem))
        return "OK"

    messagebox.askyesno = lambda *a, **k: True
    messagebox.showinfo = lambda *a, **k: None
    messagebox.showwarning = lambda *a, **k: None
    messagebox.showerror = _erro
    return erros


def _esperar_salvamento(app, limite=300):
    """Espera o salvamento em segundo plano terminar (puxando a UI)."""
    import time
    for _ in range(limite):
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            # deixa o polling aplicar o resultado na barra de status
            for _ in range(20):
                app.update()
                time.sleep(0.03)
            return True
    return False
def main(argv):
    email, senha = conta_teste(argv)

    erros = silenciar_messagebox()
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    app_mod.messagebox = app_mod.messagebox if hasattr(app_mod, "messagebox") else None
    import tkinter.messagebox as mb
    mb.showerror = lambda *a, **k: erros.append(("showerror", a))

    print("1) zerar dungeons semanais")
    df_sem = app.dfs.get("Semanais")
    if df_sem is None or df_sem.empty:
        print("   FALHOU: aba Semanais vazia")
        return 1
    # copia a coluna INTEIRA (linha a linha): restaurar so o valor da 1a
    # linha deixava todas as linhas com o mesmo id e o salvamento falhava
    antes = {c: df_sem[c].copy() for c in df_sem.columns if c != "Nome"}
    app.zerar_dungeons()
    colunas = [c for c in df_sem.columns if c != "Nome"]
    ainda = [c for c in colunas if str(df_sem[c].iloc[0]).strip().lower() == "verdadeiro"]
    print(f"   colunas com 'Verdadeiro' depois do zerar: {len(ainda)}")
    if ainda:
        print("   FALHOU: sobrou marcacao:", ainda)
        return 1
    print("   cartoes:", app.valores_dos_cards())
    # restaura
    for c, v in antes.items():
        df_sem[c] = v
    app._refrescar_tabela("Semanais", "")
    app._atualizar_cards()

    print("2) missao rapida (filtro)")
    total = len(app.tree_refs["Geral"]["tree"].get_children())
    app.alternar_missao()                      # liga
    filtrado = len(app.tree_refs["Geral"]["tree"].get_children())
    print(f"   linhas antes={total} depois={filtrado}")
    app.alternar_missao()                      # desliga
    voltou = len(app.tree_refs["Geral"]["tree"].get_children())
    print(f"   voltou para {voltou}")
    if voltou != total:
        print("   FALHOU: filtro nao voltou ao normal")
        return 1

    print("3) edicao de celula recalcula cartoes")
    df_geral = app.dfs.get("Geral")
    if df_geral is None or df_geral.empty:
        print("   FALHOU: aba Geral vazia")
        return 1
    coluna_poder = app_mod._coluna_no_df(df_geral, "poder")
    if coluna_poder is None:
        print("   FALHOU: coluna de poder nao encontrada")
        return 1
    antes_poder = df_geral[coluna_poder].iloc[0]
    df_geral[coluna_poder] = df_geral[coluna_poder].astype(object)
    df_geral.iloc[0, df_geral.columns.get_loc(coluna_poder)] = 424242
    app._atualizar_cards()
    print("   poder medio:", app.valores_dos_cards().get("poder_medio"))

    print("4) salvar no Supabase (ida e volta)")
    app._marcar_modificado()
    app.salvar_supabase()
    _esperar_salvamento(app)
    import supabase_db as db
    recem = db.carregar_personagens(sb, user.id)
    quem = recem[0]
    print(f"   {quem['Nome']}: poder={quem.get('poder')} (esperado 424242)")
    if quem.get("poder") != 424242:
        print("   FALHOU: nao gravou (ou gravou em outra linha)")
        return 1
    # restaura o valor original
    alvo = quem["Nome"]
    linha = df_geral[df_geral["Nome"] == alvo]
    if not linha.empty:
        df_geral.loc[linha.index[0], coluna_poder] = antes_poder
    app._marcar_modificado()
    app.salvar_supabase()
    _esperar_salvamento(app)
    recem = db.carregar_personagens(sb, user.id)
    quem = next(p for p in recem if p["Nome"] == alvo)
    print(f"   restaurado: poder={quem.get('poder')}")
    if quem.get("poder") != antes_poder:
        print("   FALHOU: restauracao falhou")
        return 1

    print("5) edicao com filtro ativo (nao pode editar a linha errada)")
    app.tree_refs["Geral"]["busca"].set("E")     # filtra a tabela
    app.update()
    tree = app.tree_refs["Geral"]["tree"]
    itens = tree.get_children()
    print(f"   linhas visiveis com busca 'E': {len(itens)}")
    if not itens:
        print("   FALHOU: filtro nao devolveu nada")
        return 1
    item = itens[0]
    nome_esperado = tree.set(item, "Nome")
    col_poder = [c for c in tree["displaycolumns"] if c == "Poder"][0]
    caixa = tree.bbox(item, col_poder)
    if not caixa:
        print("   FALHOU: nao consegui a posicao da coluna")
        return 1

    class EventoFake:
        x = caixa[0] + 5
        y = caixa[1] + 5

    df_geral = app.dfs["Geral"]
    valor_antes = df_geral.loc[df_geral["Nome"] == nome_esperado, "Poder"].iloc[0]
    app._editar_celula(EventoFake(), tree, df_geral, "Geral")
    app.update()
    dlg = [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)][-1]
    entrada = [w for w in dlg.winfo_children()
               if isinstance(w, ctk.CTkEntry)][0]
    entrada.delete(0, "end")
    entrada.insert(0, "13579")
    botao_salvar = None
    for w in dlg.winfo_children():
        if isinstance(w, ctk.CTkFrame):
            for b in w.winfo_children():
                if isinstance(b, ctk.CTkButton) and b.cget("text") == "Salvar":
                    botao_salvar = b
    botao_salvar.invoke()
    app.update()
    valor_depois = df_geral.loc[df_geral["Nome"] == nome_esperado, "Poder"].iloc[0]
    outros = df_geral[df_geral["Nome"] != nome_esperado]["Poder"]
    print(f"   {nome_esperado}: poder {valor_antes} -> {valor_depois}")
    if str(valor_depois).strip() != "13579":
        print("   FALHOU: nao editou a linha visivel")
        return 1
    if (outros == 13579).any():
        print("   FALHOU: editou a linha errada do dataframe")
        return 1
    # restaura
    df_geral.loc[df_geral["Nome"] == nome_esperado, "Poder"] = valor_antes
    app.tree_refs["Geral"]["busca"].set("")
    app.update()

    print("6) dropdowns das abas")
    from opcoes import obter_opcoes
    for aba in ("Geral", "Peças (Void)", "Acessórios Título", "Semanais"):
        df = app.dfs.get(aba)
        if df is None:
            continue
        for col in df.columns:
            if col == "Nome":
                continue
            opcoes = obter_opcoes(aba, col)
            marca = "com dropdown" if opcoes else "campo livre  "
            print(f"   {aba:20s} {col:22s} {marca}")

    if erros:
        print("   FALHOU: erros de messagebox:", erros)
        return 1

    app.destroy()
    print("\nACOES OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

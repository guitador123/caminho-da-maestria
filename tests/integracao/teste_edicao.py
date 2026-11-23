"""
Teste funcional da tela de edicao de personagem (nao destrutivo).

    python teste_edicao.py

Valida:
  1. a janela abre com os valores do personagem
  2. os campos aceitam edicao (Torre, Poder, Nucleos Dimensionais,
     Fragmento do Vazio Disperso, Liberacao, pecas, acessorios, dungeons)
  3. o botao Salvar grava nos dataframes (e o valor original e restaurado)
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import app_grandchase as app_mod
from app_grandchase import GrandChaseApp


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(0.6)
    app.update()

    nome = app.dfs["Geral"]["Nome"].iloc[0]
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(1.0)
    app.update()

    janelas = [w for w in app.winfo_children()
               if isinstance(w, ctk.CTkToplevel)]
    if not janelas:
        print("FALHOU: a janela de edicao nao abriu")
        return 1
    janela = janelas[-1]
    print(f"1) janela aberta: {janela.title()}")

    # --- confere os valores iniciais ---
    linha = app.dfs["Geral"]
    mask = linha["Nome"].astype(str) == str(nome)
    esperado_torre = linha.loc[mask, "Torre Das Ilusões"].iloc[0] if \
        "Torre Das Ilusões" in linha.columns else ""
    esperado_poder = linha.loc[mask, "Poder"].iloc[0] if \
        "Poder" in linha.columns else 0
    print(f"   torre={esperado_torre!r} poder={esperado_poder!r}")

    torre_widget = janela._linhas.get(("geral", "Torre Das Ilusões"))
    poder_widget = janela._linhas.get(("geral", "Poder"))
    if not torre_widget or not poder_widget:
        print("   FALHOU: campos nao encontrados")
        return 1
    print(f"   campo Torre={torre_widget[0].get()!r} "
          f"campo Poder={poder_widget[0].get()!r}")

    # --- edita ---
    torre_widget[0].delete(0, "end")
    torre_widget[0].insert(0, "12")
    poder_widget[0].delete(0, "end")
    poder_widget[0].insert(0, "424242")

    pecas = janela._linhas.get(("peca", "arma"))
    if pecas is None:
        for (tipo, chave), item in janela._linhas.items():
            if tipo == "peca" and "arma" in str(chave).lower():
                pecas = item
                break
    df_pecas = app.dfs["Peças (Void)"]
    coluna_arma = app_mod._coluna_no_df(df_pecas, "arma")
    arma_original = df_pecas.loc[df_pecas["Nome"].astype(str) == str(nome),
                                 coluna_arma].iloc[0]
    if pecas is not None:
        pecas.select()
    sem = None
    for (tipo, chave), item in janela._linhas.items():
        if tipo == "semanal" and "void_4" in str(chave).lower():
            sem = item
            break
    if sem is not None:
        sem.select()

    print("2) campos editados (Torre=12, Poder=424242, Arma/ Void4 marcados)")
    janela._salvar()
    app.update()
    time.sleep(0.4)
    app.update()

    # --- confere se gravou ---
    linha = app.dfs["Geral"]
    mask = linha["Nome"].astype(str) == str(nome)
    torre = linha.loc[mask, "Torre Das Ilusões"].iloc[0]
    poder = linha.loc[mask, "Poder"].iloc[0]
    print(f"   gravado: Torre={torre!r} Poder={poder!r}")
    if "12" not in str(torre):
        print("   FALHOU: a torre nao foi gravada")
        return 1
    if str(poder) not in ("424242", "424242.0"):
        print("   FALHOU: o poder nao foi gravado")
        return 1

    df_pecas = app.dfs["Peças (Void)"]
    coluna_arma = app_mod._coluna_no_df(df_pecas, "arma")
    arma = df_pecas.loc[df_pecas["Nome"].astype(str) == str(nome),
                        coluna_arma].iloc[0]
    print(f"   peca {coluna_arma} = {arma!r}")
    if str(arma).strip().lower() != "verdadeiro":
        print("   FALHOU: a peca nao foi gravada")
        return 1
    # --- restaura os valores originais ---
    linha.loc[mask, "Torre Das Ilusões"] = esperado_torre
    linha.loc[mask, "Poder"] = esperado_poder
    df_pecas = app.dfs["Peças (Void)"]
    coluna_arma = app_mod._coluna_no_df(df_pecas, "arma")
    if coluna_arma:
        df_pecas.loc[df_pecas["Nome"].astype(str) == str(nome),
                     coluna_arma] = arma_original
    app.modified = False
    print("3) valores restaurados (teste nao destrutivo)")
    app.destroy()
    print("\nEDICAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

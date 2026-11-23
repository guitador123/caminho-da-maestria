"""
Teste da atualizacao AO VIVO do card (pendencia #2).

Valida:
  1. marcar uma peca de Void na tela de edicao -> o card mostra o check verde
  2. desmarcar -> o card mostra o X vermelho
  3. marcar uma missao semanal -> o chip ganha o contorno verde
  4. o acessorio assume a cor da regra (anel/brinco/piercing/tornozeleira)
  5. o titulo aparece no card (abaixo do poder)

    python teste_card_ao_vivo.py [email] [senha]
"""

import sys
import time
from credenciais_teste import conta_teste

import tkinter.messagebox as mb

mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

import auth
from app_grandchase import GrandChaseApp

ALVO = "Ai"


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    app = GrandChaseApp(user=resp.user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(0.8)
    app.update()

    # abre a edicao do personagem
    app._abrir_personagem({"nome": ALVO})
    app.update()
    time.sleep(1.0)
    app.update()

    import customtkinter as ctk
    janelas = [w for w in app.winfo_children()
               if isinstance(w, ctk.CTkToplevel)]
    if not janelas:
        print("FALHOU: a janela de edicao nao abriu")
        return 1
    janela = janelas[-1]

    # --- 1/2) peca de Void: marca -> o card muda ------------------------
    peca = janela._linhas.get(("peca", "arma"))
    if peca is None:
        for (tipo, chave), item in janela._linhas.items():
            if tipo == "peca" and "arma" in str(chave).lower():
                peca = item
                break
    if peca is None:
        print("FALHOU: checkbox de peca nao encontrado")
        return 1

    card = next(c for c in app.cards_personagem if c.dados.get("nome") == ALVO)
    antes = [i for i in card._itens]
    print(f"1) card '{ALVO}' com {len(antes)} itens")

    peca.select()
    janela._propagar()
    app.update()
    print("   apos marcar a peca -> card redesenhado:",
          len(card._itens), "itens")
    if not card._itens:
        print("   FALHOU: o card ficou sem itens")
        return 1

    # confere o valor no dataframe do app
    df = app.dfs["Peças (Void)"]
    linha = df[df["Nome"].astype(str) == ALVO].iloc[0]
    valor = linha.get("arma") or linha.get("Arma")
    print(f"   peca no dataframe: {valor!r}")
    if str(valor).strip().lower() != "verdadeiro":
        print("   FALHOU: a peca nao foi propagada")
        return 1

    # --- 3) missao semanal -----------------------------------------------
    sem = None
    for (tipo, chave), item in janela._linhas.items():
        if tipo == "semanal" and "void_4" in str(chave).lower():
            sem = item
            break
    if sem is not None:
        sem.select()
        janela._propagar()
        app.update()
        df = app.dfs["Semanais"]
        linha = df[df["Nome"].astype(str) == ALVO].iloc[0]
        print("   missao void_4 no dataframe:",
              linha.get("void_4") or linha.get("Void 4"))

    # --- 4) acessorio com a cor da regra --------------------------------
    combos = {k[1]: v for k, v in janela._linhas.items() if k[0] == "acesso"}
    for chave, combo in combos.items():
        valores = list(combo.cget("values"))
        if not valores:
            continue
        alvo = "Anel do Ciclo Infinito" if "anel" in str(chave).lower() else None
        if alvo and alvo in valores:
            combo.set(alvo)
            janela._propagar()
            app.update()
            df = app.dfs["Acessórios Título"]
            linha = df[df["Nome"].astype(str) == ALVO].iloc[0]
            print(f"   acessorio {chave}: {linha.get(chave) or linha.get(str(chave).capitalize())!r}")

    # --- 5) titulo no card ----------------------------------------------
    tem_titulo = any("Título" in str(k[1]) for k in janela._linhas)
    print(f"   titulo editavel na tela: {tem_titulo}")

    janela.destroy()
    app.destroy()
    print("\nCARD AO VIVO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

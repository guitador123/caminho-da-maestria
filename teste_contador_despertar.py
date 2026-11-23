"""
Teste do contador "DESPERTAR COMPLETO" da tela Caminho da Maestria.

Regra: o contador sobe 1 para cada personagem com o DESPERTAR completo
(Núcleos 13/13 e Épicos+ 9/9) — e tem que mudar AO VIVO na hora da edicao.

    python teste_contador_despertar.py [email] [senha]
"""

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
from opcoes import coluna_banco


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def _widget(janela, tipo, logico):
    alvo = coluna_banco(logico)
    for (tipo_item, chave), item in janela._linhas.items():
        if tipo_item == tipo and coluna_banco(chave) == alvo:
            return item
    return None


def _combo(widget):
    if isinstance(widget, tuple):
        return widget[0]
    return widget


def _coluna(df, logico):
    alvo = coluna_banco(logico)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None


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

    df = app.dfs["Geral"]
    col_nuc = _coluna(df, "Núcleo")
    col_epi = _coluna(df, "Núcleos Épicos+")
    if not col_nuc or not col_epi:
        print("FALHOU: as colunas do despertar nao existem")
        return 1

    # --- 1) o contador bate com os dados ----------------------------------
    print("1) dados do despertar:")
    completo = 0
    for _, linha in df.iterrows():
        nucleo = str(linha.get(col_nuc, ""))
        epicos = str(linha.get(col_epi, ""))
        n = _num_fracao(nucleo)
        e = _num_fracao(epicos)
        if n == 13 and e == 9:
            completo += 1
            print(f"   {str(linha['Nome']):10s} {nucleo:10s} {epicos:10s} "
                  f"-> DESPERTAR COMPLETO")
    valor = app.valores_dos_cards().get("despertar")
    print(f"2) contador no card: {valor} (esperado {completo})")
    if str(valor) != str(completo):
        print("   FALHOU: o contador nao bate com os dados")
        return 1

    # --- 2) completar o despertar de um personagem sobe 1 ------------------
    print("\n3) completando o despertar de um personagem (ao vivo):")
    # acha um que NAO esta completo
    alvo = None
    for _, linha in df.iterrows():
        n = _num_fracao(str(linha.get(col_nuc, "")))
        e = _num_fracao(str(linha.get(col_epi, "")))
        if not (n == 13 and e == 9):
            alvo = str(linha["Nome"])
            break
    if alvo is None:
        print("   (todos ja estao completos — pulando)")
        app.destroy()
        print("\nCONTADOR DO DESPERTAR OK")
        return 0

    antes = int(app.valores_dos_cards().get("despertar"))
    mask = df["Nome"].astype(str) == alvo
    original_nuc = df.loc[mask, col_nuc].iloc[0]
    original_epi = df.loc[mask, col_epi].iloc[0]
    print(f"   alvo: {alvo} | contador antes: {antes} | "
          f"valores originais: {original_nuc!r} / {original_epi!r}")

    app._abrir_personagem({"nome": alvo})
    app.update()
    time.sleep(0.9)
    app.update()
    janela = _janelas(app)[-1]
    combo_nuc = _combo(_widget(janela, "geral", "Núcleo"))
    combo_epi = _combo(_widget(janela, "geral", "Núcleos Épicos+"))
    if combo_nuc is None or combo_epi is None:
        print("   FALHOU: dropdowns do despertar nao encontrados")
        return 1

    combo_nuc.set("13 / 13")
    combo_epi.set("9 / 9")
    janela._propagar()
    app.update()
    time.sleep(0.3)
    app.update()

    depois = int(app.valores_dos_cards().get("despertar"))
    print(f"   contador depois: {depois}")
    if depois != antes + 1:
        print(f"   FALHOU: o contador deveria ter subido 1 "
              f"({antes} -> {antes + 1}), veio {depois}")
        return 1
    print("   -> OK: subiu 1 na hora (sem clicar em Salvar)")

    # --- 3) desfaz -------------------------------------------------------
    for janela in _janelas(app):
        janela.destroy()
    app.update()
    df.loc[mask, col_nuc] = original_nuc
    df.loc[mask, col_epi] = original_epi
    app._atualizar_cards()
    app.update()
    volta = int(app.valores_dos_cards().get("despertar"))
    print(f"\n4) restaurado {alvo}: contador = {volta} (antes {antes})")
    if volta != antes:
        print("   FALHOU: nao voltou ao valor anterior")
        return 1

    app.destroy()
    print("\nCONTADOR DO DESPERTAR OK")
    return 0


def _num_fracao(valor):
    """'13 / 13' -> 13 (o numerador)."""
    try:
        return int(float(str(valor).split("/")[0]))
    except (TypeError, ValueError):
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

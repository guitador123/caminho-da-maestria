"""
Teste do contador "LIBERTAÇÃO COMPLETA" (regras de 14/11).

O contador sobe 1 quando o personagem tem as 3 condicoes:
  1. o campo "Libertação" (estado) = VERDADEIRO
  2. Núcleos = 9/9
  3. Épicos+ = 4/4

O teste tambem confere que cada condicao sozinha NAO conta.

    python teste_contador_libertacao.py [email] [senha]
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
    col_estado = _coluna(df, "Libertação")
    col_nuc = _coluna(df, "Libertação Núcleos")
    col_epi = _coluna(df, "Libertação Épicos+")
    if not all((col_estado, col_nuc, col_epi)):
        print("FALHOU: as colunas da liberacao nao existem")
        return 1

    mask = df["Nome"].astype(str) == df["Nome"].iloc[0]
    alvo = str(df["Nome"].iloc[0])
    originais = {c: df.loc[mask, c].iloc[0]
                 for c in (col_estado, col_nuc, col_epi)}
    print(f"1) personagem de teste: {alvo} | originais: {originais}")

    def contar():
        app._atualizar_cards()
        app.update()
        return int(app.valores_dos_cards().get("libertacao"))

    def por(estado, nucleo, epico):
        """Coloca os 3 valores e devolve o contador."""
        df.loc[mask, col_estado] = estado
        df.loc[mask, col_nuc] = nucleo
        df.loc[mask, col_epi] = epico
        return contar()

    # --- 1) as 3 condicoes juntas contam ----------------------------------
    print("\n2) as 3 condicoes juntas:")
    # base: o personagem de teste nao conta (estado FALSO)
    base = por("FALSO", 0, 0)
    completo = por("VERDADEIRO", 9, 4)
    print(f"   VERDADEIRO + 9/9 + 4/4 -> contador {base} -> {completo}")
    if completo != base + 1:
        print("   FALHOU: o contador nao subiu 1")
        return 1
    print("   -> OK: subiu 1")

    # --- 2) cada condicao sozinha NAO conta ------------------------------
    print("\n3) cada condicao faltando NAO conta:")
    casos = [
        ("estado FALSO", ("FALSO", 9, 4)),
        ("núcleos 8/9", ("VERDADEIRO", 8, 4)),
        ("épicos+ 3/4", ("VERDADEIRO", 9, 3)),
        ("estado INEXISTENTE", ("INEXISTENTE", 9, 4)),
    ]
    for rotulo, (estado, nucleo, epico) in casos:
        valor = por(estado, nucleo, epico)
        print(f"   {rotulo:22s} -> contador {valor} (base {base})")
        if valor != base:
            print(f"   FALHOU: '{rotulo}' contou (esperado {base})")
            return 1
    print("   -> OK: so conta com as 3 condicoes")

    # --- 3) volta as 3 condicoes e confere que volta a contar -----------
    print("\n4) voltando as 3 condicoes:")
    volta = por("VERDADEIRO", 9, 4)
    print(f"   contador = {volta}")
    if volta != completo:
        print("   FALHOU: nao voltou a contar")
        return 1

    # --- 4) pela tela de edicao (ao vivo) --------------------------------
    print("\n5) pela tela de edicao (ao vivo):")
    for janela in _janelas(app):
        janela.destroy()
    app.update()
    app._abrir_personagem({"nome": alvo})
    app.update()
    time.sleep(0.9)
    app.update()
    janela = _janelas(app)[-1]
    combo_estado = _combo(_widget(janela, "geral", "Libertação"))
    combo_nuc = _combo(_widget(janela, "geral", "Libertação Núcleos"))
    combo_epi = _combo(_widget(janela, "geral", "Libertação Épicos+"))
    if not all((combo_estado, combo_nuc, combo_epi)):
        print("   FALHOU: dropdowns da liberacao nao encontrados")
        return 1

    por("FALSO", 0, 0)
    antes = contar()
    combo_estado.set("VERDADEIRO")
    combo_nuc.set("9 / 9")
    combo_epi.set("4 / 4")
    janela._propagar()
    app.update()
    time.sleep(0.3)
    app.update()
    depois = int(app.valores_dos_cards().get("libertacao"))
    print(f"   contador: {antes} -> {depois}")
    if depois != antes + 1:
        print(f"   FALHOU: o contador nao subiu 1 ao vivo")
        return 1
    print("   -> OK: subiu 1 na hora")

    # --- 5) restaura -----------------------------------------------------
    for janela in _janelas(app):
        janela.destroy()
    app.update()
    for coluna, valor in originais.items():
        df.loc[mask, coluna] = valor
    app._atualizar_cards()
    app.update()
    print(f"\n6) restaurado: {contar()}")
    app.destroy()
    print("\nCONTADOR DA LIBERTACAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

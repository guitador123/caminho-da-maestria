"""
Teste dos dropdowns do Despertar e da Liberacao (pedido de 14/11).

  DESPERTAR  Núcleos -> 0/13 ... 13/13 (sem o resto da lista)
             Épicos+ -> 0/9 ... 9/9
  LIBERTACAO Núcleos -> 0/9 ... 9/9   (dropdown; grava NUMERO no banco)
             Épicos+ -> 0/4 ... 4/4

Roda no Supabase (as colunas da liberacao so existem no banco) e restaura
os valores originais no fim.

    python teste_dropdowns_liberacao.py [email] [senha]
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
from janela_personagem import (OPCOES_DESPERTAR_EPICOS,
                               OPCOES_DESPERTAR_NUCLEOS,
                               OPCOES_LIBERTACAO_EPICOS,
                               OPCOES_LIBERTACAO_NUCLEOS)
from opcoes import coluna_banco


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def _widget(janela, tipo, logico):
    """Widget pelo nome LOGICO da coluna."""
    alvo = coluna_banco(logico)
    for (tipo_item, chave), item in janela._linhas.items():
        if tipo_item == tipo and coluna_banco(chave) == alvo:
            return item
    return None


def _combo(widget):
    """O combo (pode vir como (widget, 'fracao'))."""
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

    nome = app.dfs["Geral"]["Nome"].iloc[0]
    df = app.dfs["Geral"]
    mask = df["Nome"].astype(str) == str(nome)
    col_nuc = _coluna(df, "Libertação Núcleos")
    col_epi = _coluna(df, "Libertação Épicos+")
    col_dnuc = _coluna(df, "Núcleo")
    col_depi = _coluna(df, "Núcleos Épicos+")
    print(f"1) editando: {nome}")
    print(f"   colunas: {col_nuc} | {col_epi} | {col_dnuc} | {col_depi}")
    if not all((col_nuc, col_epi, col_dnuc, col_depi)):
        print("   FALHOU: alguma coluna nao existe no banco")
        return 1
    originais = {c: df.loc[mask, c].iloc[0]
                 for c in (col_nuc, col_epi, col_dnuc, col_depi)}
    print(f"   originais: {originais}")

    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(0.9)
    app.update()
    janelas = _janelas(app)
    if not janelas:
        print("FALHOU: a janela de edicao nao abriu")
        return 1
    janela = janelas[-1]

    # --- 1) as listas de opcoes ------------------------------------------
    print("\n2) listas dos dropdowns:")
    esperado = [
        ("Núcleos (Despertar)", "Núcleo", OPCOES_DESPERTAR_NUCLEOS),
        ("Épicos+ (Despertar)", "Núcleos Épicos+", OPCOES_DESPERTAR_EPICOS),
        ("Núcleos (Libertação)", "Libertação Núcleos", OPCOES_LIBERTACAO_NUCLEOS),
        ("Épicos+ (Libertação)", "Libertação Épicos+", OPCOES_LIBERTACAO_EPICOS),
    ]
    for rotulo, coluna, lista in esperado:
        widget = _widget(janela, "geral", coluna)
        if widget is None:
            print(f"   FALHOU: '{rotulo}' nao encontrado")
            return 1
        combo = _combo(widget)
        valores = list(combo.cget("values"))
        ok = valores == lista
        print(f"   {rotulo:22s} {len(valores):>2} opcoes "
              f"[{valores[0]} .. {valores[-1]}] "
              f"{'OK' if ok else 'FALHOU -> ' + str(valores)}")
        if not ok:
            return 1

    despertar = _combo(_widget(janela, "geral", "Núcleo"))
    if any("/ 9" in v for v in despertar.cget("values")):
        print("   FALHOU: o Despertar ainda tem as opcoes de /9")
        return 1
    print("   -> OK: o Despertar parou em 13/13 (sem o resto)")

    # --- 2) a liberacao grava NUMERO no dataframe ------------------------
    print("\n3) gravando a liberacao (numeros):")
    lib_nuc = _combo(_widget(janela, "geral", "Libertação Núcleos"))
    lib_epi = _combo(_widget(janela, "geral", "Libertação Épicos+"))
    lib_nuc.set("7 / 9")
    lib_epi.set("3 / 4")
    janela._propagar()
    app.update()

    valor_nuc = df.loc[mask, col_nuc].iloc[0]
    valor_epi = df.loc[mask, col_epi].iloc[0]
    print(f"   Núcleos='{valor_nuc!r}' ({type(valor_nuc).__name__}) | "
          f"Épicos+='{valor_epi!r}' ({type(valor_epi).__name__})")
    if valor_nuc != 7 or valor_epi != 3:
        print("   FALHOU: a liberacao nao foi gravada como numero")
        return 1
    # o pandas devolve np.int64 (que e numero inteiro) — so nao pode ser
    # texto ("7 / 9"), que o banco bigint recusaria
    if isinstance(valor_nuc, str) or isinstance(valor_epi, str):
        print("   FALHOU: o valor gravado e texto (a coluna do banco e bigint)")
        return 1
    print("   -> OK: gravado como numero (7 e 3)")

    # --- 3) o card mostra o valor -----------------------------------------
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == nome)
    print(f"   card: {card.dados.get('libertacao_nucleos')} / "
          f"{card.dados.get('libertacao_epicos')}")
    if card.dados.get("libertacao_nucleos") != 7 or \
            card.dados.get("libertacao_epicos") != 3:
        print("   FALHOU: o card nao pegou o valor novo")
        return 1

    # --- 4) reabrir mostra o salvo ---------------------------------------
    print("\n4) reabrindo a edicao (o salvo tem que estar no dropdown):")
    _fechar(app)
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(0.9)
    app.update()
    janela = _janelas(app)[-1]
    lib_nuc = _combo(_widget(janela, "geral", "Libertação Núcleos"))
    lib_epi = _combo(_widget(janela, "geral", "Libertação Épicos+"))
    print(f"   Núcleos='{lib_nuc.get()}' | Épicos+='{lib_epi.get()}'")
    if lib_nuc.get() != "7 / 9" or lib_epi.get() != "3 / 4":
        print("   FALHOU: o valor salvo nao voltou no dropdown")
        return 1
    print("   -> OK")

    # --- 5) grava no banco e restaura ------------------------------------
    print("\n5) gravando no Supabase e restaurando:")
    _fechar(app)
    for coluna, valor in ((col_nuc, 7), (col_epi, 3)):
        df.loc[mask, coluna] = valor
    app._marcar_modificado()
    app.salvar_supabase()
    if not _esperar(app):
        print("   FALHOU: o salvamento nao terminou")
        return 1
    print("   status:", app.status_var.get())

    volta = sb.table("user_characters").select(
        "character_name,libertacao_nucleos,libertacao_epicos") \
        .eq("user_id", user.id).eq("character_name", nome).execute()
    if volta.data and volta.data[0].get("libertacao_nucleos") != 7:
        print("   FALHOU: nao gravou no banco:", volta.data)
        return 1
    print("   no banco:", volta.data)

    for coluna, valor in originais.items():
        df.loc[mask, coluna] = valor
    app._marcar_modificado()
    app.salvar_supabase()
    _esperar(app)
    print("   restaurado:", {c: df.loc[mask, c].iloc[0] for c in originais})

    app.destroy()
    print("\nDROPDOWNS DE DESPERTAR/LIBERTACAO OK")
    return 0


def _fechar(app):
    for janela in _janelas(app):
        try:
            janela.destroy()
        except Exception:
            pass
    app.update()
    time.sleep(0.3)
    app.update()


def _esperar(app, limite=400):
    for _ in range(limite):
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            for _ in range(20):
                app.update()
                time.sleep(0.03)
            return True
    return False


if __name__ == "__main__":
    sys.exit(main(sys.argv))

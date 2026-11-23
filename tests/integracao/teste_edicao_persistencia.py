"""
Teste de PERSISTENCIA da tela de edicao (bug reportado pelo usuario):

    "assim que uma informacao for salva, quando abrir a tela de edicao
     novamente, tem que estar marcado tudo aquilo que foi feito na ultima vez"

Fluxo real:
  1. login no Supabase
  2. abre a edicao de um personagem e marca uma peca + uma missao semanal
  3. salva (envio em 2o plano) e ESPERA o envio terminar
  4. DESTRUI o app e cria um NOVO app (recarrega tudo do Supabase)
  5. abre a edicao de novo -> a peca e a missao tem que estar MARCADAS
  6. restaura o valor original

    python teste_edicao_persistencia.py [email] [senha]
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


def _coluna_real(df, logico):
    alvo = coluna_banco(logico)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None


def _verdadeiro(valor):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in ("verdadeiro", "true", "1", "t", "sim")


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
    time.sleep(1.0)
    app.update()

    nomes = [str(n) for n in app.dfs["Geral"]["Nome"].tolist()]
    nome = nomes[0]
    print(f"1) personagem: {nome}")

    df_pecas = app.dfs["Peças (Void)"]
    df_sem = app.dfs["Semanais"]
    col_peca = _coluna_real(df_pecas, "diadema")
    col_sem = _coluna_real(df_sem, "void4")
    mask_p = df_pecas["Nome"].astype(str) == nome
    mask_s = df_sem["Nome"].astype(str) == nome
    original_peca = df_pecas.loc[mask_p, col_peca].iloc[0] if col_peca else None
    original_sem = df_sem.loc[mask_s, col_sem].iloc[0] if col_sem else None
    print(f"   original: peca={original_peca!r} dungeon={original_sem!r}")

    # ---- 1) marca e salva ------------------------------------------------
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(0.9)
    app.update()
    janela = _janelas(app)[-1]

    peca = _widget(janela, "peca", "diadema")
    dungeon = _widget(janela, "semanal", "void4")
    if peca is None or dungeon is None:
        print("FALHOU: widgets nao encontrados")
        return 1
    peca.select()
    dungeon.select()
    janela._salvar()
    app.update()
    time.sleep(0.4)
    app.update()
    if app.usar_supabase:
        app.salvar_supabase()
    if not _esperar_salvamento(app):
        print("FALHOU: o salvamento nao terminou")
        return 1
    print("2) marcado e salvo no Supabase")

    # ---- 2) DESTRUI o app e recarrega do zero ---------------------------
    app.destroy()
    time.sleep(1.0)

    app2 = GrandChaseApp(user=user, supabase=sb)
    app2.update_idletasks()
    app2.update()
    time.sleep(1.2)
    app2.update()

    # ---- 3) reabre a edicao: tem que estar marcado ----------------------
    app2._abrir_personagem({"nome": nome})
    app2.update()
    time.sleep(0.9)
    app2.update()
    janela = _janelas(app2)[-1]

    peca = _widget(janela, "peca", "diadema")
    dungeon = _widget(janela, "semanal", "void4")
    ok = True
    if not _verdadeiro(peca.get()):
        print(f"   FALHOU: a peca 'diadema' NAO veio marcada ao reabrir")
        ok = False
    else:
        print("   peca 'diadema' veio marcada  OK")
    if not _verdadeiro(dungeon.get()):
        print(f"   FALHOU: a missao 'void4' NAO veio marcada ao reabrir")
        ok = False
    else:
        print("   missao 'void4' veio marcada  OK")

    # ---- 4) restaura -----------------------------------------------------
    if col_peca:
        df_pecas.loc[mask_p, col_peca] = original_peca
    if col_sem:
        df_sem.loc[mask_s, col_sem] = original_sem
    app2._marcar_modificado()
    app2.salvar_supabase()
    _esperar_salvamento(app2)
    print(f"   restaurado: peca={original_peca!r} dungeon={original_sem!r}")

    app2.destroy()
    if not ok:
        print("\nPERSISTENCIA DA EDICAO FALHOU")
        return 1
    print("\nPERSISTENCIA DA EDICAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

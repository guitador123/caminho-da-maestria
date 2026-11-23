"""
Teste app dos campos novos: abre a tela de edicao, mexe nos contadores e
salva no Supabase (depois restaura).

    python teste_edicao_supabase.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from credenciais_teste import conta_teste

import customtkinter as ctk

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp

# os messagebox bloqueiam o script
import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True

CAMPOS = ["nucleos_dimensionais", "fragmento_vazio_disperso",
           "libertacao_nucleos", "libertacao_epicos"]


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

    # valores originais no banco
    personagens = db.carregar_personagens(sb, user.id)
    alvo = personagens[0]
    nome = alvo["Nome"]
    originais = {c: alvo.get(c, 0) for c in CAMPOS}
    print(f"1) personagem: {nome} | originais: {originais}")

    # abre a edicao
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(1.0)
    app.update()
    janelas = [w for w in app.winfo_children()
               if isinstance(w, ctk.CTkToplevel)]
    if not janelas:
        print("   FALHOU: a janela nao abriu")
        return 1
    janela = janelas[-1]

    # mexe nos contadores
    from opcoes import normalizar
    encontrados = 0
    alvos = ["nucleosdimensionais", "fragmentodovaziodisperso",
             "libertacaonucleos", "libertacaoepicos"]
    for (tipo, chave), item in janela._linhas.items():
        if tipo != "geral" or not isinstance(item, tuple):
            continue
        plano = normalizar(chave)
        if any(a in plano for a in alvos):
            entrada, _max = item
            if hasattr(entrada, "delete"):      # CTkEntry (campo livre)
                entrada.delete(0, "end")
                entrada.insert(0, "2")          # dentro dos limites de todos
            else:                               # CTkComboBox (lista)
                entrada.set("2")
            encontrados += 1
    print(f"2) campos novos encontrados na edicao: {encontrados}")
    print("   chaves da edicao:",
          [str(k[1]) for k in janela._linhas if k[0] == "geral"])
    if encontrados < 4:
        print("   FALHOU: os campos novos nao apareceram na edicao")
        return 1

    janela._salvar()
    app.update()
    time.sleep(0.5)
    app.update()
    if app.usar_supabase:
        app.salvar_supabase()
    _esperar_salvamento(app)

    volta = next(p for p in db.carregar_personagens(sb, user.id)
                 if p["Nome"] == nome)
    print("3) no Supabase:", {c: volta.get(c) for c in CAMPOS})
    if any(volta.get(c) != 2 for c in CAMPOS):
        print("   FALHOU: nao gravou no Supabase")
        return 1

    # restaura
    linha = app.dfs["Geral"]
    mask = linha["Nome"].astype(str) == str(nome)
    for coluna in CAMPOS:
        real = app_mod_coluna(app, linha, coluna)
        if real:
            linha.loc[mask, real] = originais[coluna]
    app._marcar_modificado()
    app.salvar_supabase()
    _esperar_salvamento(app)
    volta = next(p for p in db.carregar_personagens(sb, user.id)
                 if p["Nome"] == nome)
    print("4) restaurado:", {c: volta.get(c) for c in CAMPOS})
    for coluna in CAMPOS:
        if volta.get(coluna) != originais[coluna]:
            print(f"   FALHOU: nao restaurou {coluna}")
            return 1

    app.destroy()
    print("\nEDICAO SUPABASE OK")
    return 0


def app_mod_coluna(app, df, coluna):
    from opcoes import coluna_banco
    alvo = coluna_banco(coluna)
    for c in df.columns:
        if coluna_banco(c) == alvo:
            return c
    return None


if __name__ == "__main__":
    sys.exit(main(sys.argv))

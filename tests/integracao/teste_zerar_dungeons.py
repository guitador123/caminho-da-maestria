"""
Teste do botao "Zerar dungeons semanais".

Bug reportado: depois de zerar, as missoes continuavam MARCADAS no card do
personagem (o card nao era redesenhado).

    python teste_zerar_dungeons.py
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)
mb.askyesno = lambda *a, **k: True      # confirma o "zerar"

from app_grandchase import GrandChaseApp
from card_personagem import DUNGEONS


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(1.0)
    app.update()

    df = app.dfs["Semanais"]
    nomes = [str(n) for n in app.dfs["Geral"]["Nome"].tolist()]
    alvo = nomes[0]

    # --- 1) marca algumas missoes de verdade -----------------------------
    print("1) marcando missoes (para ter o que desmarcar):")
    from opcoes import coluna_banco

    def col(chave):
        for coluna in df.columns:
            if coluna_banco(coluna) == coluna_banco(chave):
                return coluna
        return None

    mask = df["Nome"].astype(str) == alvo
    marcadas = []
    for chave, _rotulo in DUNGEONS[:4]:
        coluna = col(chave)
        if coluna:
            df.loc[mask, coluna] = "Verdadeiro"
            marcadas.append((chave, coluna))
    app._atualizar_todos_os_cards()
    app.update()
    time.sleep(0.3)
    app.update()

    card = next(c for c in app.cards_personagem if c.dados.get("nome") == alvo)
    print(f"   card antes: { {k: card.dados['semanais'].get(k) for k, _ in DUNGEONS} }")
    feitas = [k for k, _ in DUNGEONS
              if str(card.dados["semanais"].get(k)).strip().lower() == "verdadeiro"]
    print(f"   marcadas no card: {feitas}")
    if not feitas:
        print("   FALHOU: nao consegui marcar nada para o teste")
        return 1

    # --- 2) clica em "Zerar dungeons semanais" ----------------------------
    print("\n2) clicando em 'Zerar dungeons semanais':")
    app.zerar_dungeons()
    app.update()
    time.sleep(0.5)
    app.update()

    # --- 3) o dataframe foi zerado? -------------------------------------
    restantes = [coluna for _chave, coluna in marcadas
                 if df.loc[mask, coluna].iloc[0] is not None
                 and str(df.loc[mask, coluna].iloc[0]).strip().lower() == "verdadeiro"]
    print(f"   colunas ainda marcadas no dataframe: {restantes}")
    if restantes:
        print("   FALHOU: o dataframe nao foi zerado")
        return 1

    # --- 4) o CARD foi desmarcado? ---------------------------------------
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == alvo)
    feitas_card = [k for k, _ in DUNGEONS
                   if str(card.dados["semanais"].get(k)).strip().lower() == "verdadeiro"]
    print(f"   card depois: { {k: card.dados['semanais'].get(k) for k, _ in DUNGEONS} }")
    print(f"   marcadas no card: {feitas_card}")
    if feitas_card:
        print(f"   FALHOU: o card continua com {feitas_card} marcado(s)")
        return 1
    print("   -> OK: o card foi desmarcado junto")

    # --- 5) os contadores do hero tambem zeraram -------------------------
    contadores = app.valores_dos_cards()
    print(f"   contadores: void4={contadores.get('void4')} "
          f"void123={contadores.get('void123')} "
          f"caminho_abissal={contadores.get('caminho_abissal')}")
    for chave in ("void4", "void123", "caminho_abissal"):
        if str(contadores.get(chave)) not in ("0", "—"):
            print(f"   FALHOU: o contador {chave} nao zerou")
            return 1
    print("   -> OK: os contadores zeraram")

    app.destroy()
    print("\nZERAR DUNGEONS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

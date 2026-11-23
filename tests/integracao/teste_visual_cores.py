"""
Previa das regras de cor dos cards (acessorios, pecas e missoes).

    python teste_visual_cores.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_cores.png"

app = GrandChaseApp(user=None, supabase=None)
app.attributes("-topmost", True)
app.lift()
app.update_idletasks()
app.update()
time.sleep(1.0)
app.update()

PRIMEIRO = app.dfs["Geral"]["Nome"].iloc[0]
print("personagem:", PRIMEIRO)

# deixa o primeiro personagem com os acessorios de todas as cores
df = app.dfs.get("Acessórios Título")
if df is not None and not df.empty:
    mask = df["Nome"].astype(str) == PRIMEIRO
    for coluna, valor in (("Anel", "Anel do Ciclo Infinito"),
                          ("Tornozeleira", "Apocalipse"),
                          ("Brinco", "Brinco do Outro Mundo do Caos"),
                          ("Piercing", "Piercing do Piu Piu"),
                          ("Título", "Origem do Caos")):
        if coluna in df.columns:
            df.loc[mask, coluna] = valor

# duas peças marcadas e duas não
df_pecas = app.dfs.get("Peças (Void)")
if df_pecas is not None and not df_pecas.empty:
    mask = df_pecas["Nome"].astype(str) == PRIMEIRO
    for coluna, valor in (("Arma", "VERDADEIRO"), ("Luvas", "VERDADEIRO"),
                          ("Cota", "FALSO"), ("Botas", "FALSO")):
        if coluna in df_pecas.columns:
            df_pecas.loc[mask, coluna] = valor

# missoes: duas feitas, uma nao
df_sem = app.dfs.get("Semanais")
if df_sem is not None and not df_sem.empty:
    mask = df_sem["Nome"].astype(str) == PRIMEIRO
    for coluna, valor in (("Void 4", "Verdadeiro"), ("Caminho Abissal", "Verdadeiro"),
                          ("Void ( 1, 2 e 3 )", "Falso")):
        if coluna in df_sem.columns:
            df_sem.loc[mask, coluna] = valor

for card in app.cards_personagem:
    if card.dados.get("nome") == PRIMEIRO:
        card.atualizar(app._dados_personagem(PRIMEIRO))
        print("   card:", card.dados["acessorios"])
app.update()
time.sleep(0.6)
app.update()

# rola ate o primeiro card e captura
app.canvas.yview_moveto(1145)
app._fixar_cenario()
app.update()
time.sleep(0.6)
app.update()

x, y = app.winfo_rootx(), app.winfo_rooty()
w, h = app.winfo_width(), app.winfo_height()
imagem = ImageGrab.grab(bbox=(x, y, x + w, y + h))
imagem.save(os.path.abspath(SAIDA))
print(f"[cores] {os.path.abspath(SAIDA)} ({w}x{h})")
app.destroy()

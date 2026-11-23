"""Captura a 1a linha de cards (com o retrato) na tela principal."""
import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

from app_grandchase import GrandChaseApp

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "cards_retrato.png"
POSICAO = float(sys.argv[2]) if len(sys.argv) > 2 else 900.0

app = GrandChaseApp(user=None, supabase=None)
app.attributes("-topmost", True)
app.lift()
app.update()
time.sleep(1.2)
app.update()

app.canvas.yview_moveto(POSICAO)
app._fixar_cenario()
app.update()
time.sleep(0.8)
app.update()

x, y = app.winfo_rootx(), app.winfo_rooty()
w, h = app.winfo_width(), app.winfo_height()
caminho = os.path.abspath(SAIDA)
ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(caminho)
print(f"[cards] {caminho} ({w}x{h}) scroll={POSICAO}")
print("cards:", len(getattr(app, "cards_personagem", [])))
app.destroy()

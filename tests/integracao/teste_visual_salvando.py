"""
Prova visual: dispara um salvamento e mostra que a interface continua
usavel (a barra de status mostra "Salvando..." e a tela responde).

    python teste_visual_salvando.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time

from PIL import ImageGrab

import auth
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_salvando.png"

sb, resp = auth.login(*conta_teste([]))
app = GrandChaseApp(user=resp.user, supabase=sb)
app.attributes("-topmost", True)
app.lift()
app.update()
time.sleep(1.2)
app.update()

df = app.dfs["Geral"]
mask = df["Nome"].astype(str) == "Ai"
original = df.loc[mask, "Poder"].iloc[0]
df.loc[mask, "Poder"] = 123456
app._marcar_modificado()

t0 = time.time()
app.salvar_supabase()
retorno = time.time() - t0

# enquanto salva, a interface responde: rola a pagina e redesenha
app.canvas.yview_moveto(0.25)
app._fixar_cenario()
app.update()
tela_responsiva = time.time() - t0

x, y = app.winfo_rootx(), app.winfo_rooty()
w, h = app.winfo_width(), app.winfo_height()
ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(os.path.abspath(SAIDA))
print(f"[salvando] {SAIDA}")
print(f"   a UI voltou a responder em {retorno:.3f}s")
print(f"   redesenho durante o envio em {tela_responsiva:.3f}s")
print(f"   status: {app.status_var.get()!r}")

while app._salvando:
    app.update()
    time.sleep(0.05)
for _ in range(30):
    app.update()
    time.sleep(0.05)
print(f"   status final: {app.status_var.get()!r}")

# restaura
df.loc[mask, "Poder"] = original
app._marcar_modificado()
app.salvar_supabase()
while app._salvando:
    app.update()
    time.sleep(0.05)
app.destroy()
print("   restaurado")

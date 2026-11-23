"""Analisa as cores dominantes da logo (assets/login.png) para escolher a cor
de destaque da tela de login (botao Entrar, foco dos campos, etc.)."""
import colorsys

from PIL import Image

im = Image.open(r"assets\login.png").convert("RGBA")
pequeno = im.resize((160, 160), Image.LANCZOS)

pixels = list(pequeno.getdata())
opacos = [(r, g, b) for (r, g, b, a) in pixels if a > 200]
print(f"pixels opacos: {len(opacos)} de {len(pixels)}")

# cores saturadas (o "destaque")
saturados = []
for r, g, b in opacos:
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if s > 0.45 and l > 0.30:
        saturados.append((r, g, b, h, s, l))
print(f"saturados: {len(saturados)}")

# agrupa por faixa de matiz
faixas = {}
for r, g, b, h, s, l in saturados:
    faixa = int(h * 12) % 12
    faixas.setdefault(faixa, []).append((r, g, b, l))
for faixa, itens in sorted(faixas.items(), key=lambda kv: -len(kv[1])):
    r = sum(i[0] for i in itens) // len(itens)
    g = sum(i[1] for i in itens) // len(itens)
    b = sum(i[2] for i in itens) // len(itens)
    l = sum(i[3] for i in itens) / len(itens)
    print(f"  matiz {faixa * 30:3d}-{faixa * 30 + 30:3d}  n={len(itens):5d}  "
          f"rgb({r},{g},{b})  #{r:02x}{g:02x}{b:02x}  brilho={l:.2f}")

# cor mais viva (maior sat * brilho)
if saturados:
    melhor = max(saturados, key=lambda p: p[4] * p[5])
    r, g, b, h, s, l = melhor
    print(f"\nmais viva: #{r:02x}{g:02x}{b:02x} (h={h * 360:.0f} s={s:.2f} l={l:.2f})")
    # versao escura/ clara para hover
    h2, l2, s2 = colorsys.hls_to_rgb(h, min(0.95, l * 1.12), s)
    print(f"  claro:  #{int(h2 * 255):02x}{int(l2 * 255):02x}{int(s2 * 255):02x}")
    h3, l3, s3 = colorsys.hls_to_rgb(h, max(0.12, l * 0.82), s)
    print(f"  escuro: #{int(h3 * 255):02x}{int(l3 * 255):02x}{int(s3 * 255):02x}")

# -*- coding: utf-8 -*-
"""
Tema visual da tela de login.

Mesma ideia da tela principal (tema_visual.py): o fundo e ASSADO no PIL
(logotipo Akkatsuki + gradiente + glow + cartao de vidro) e o canvas do Tk
desenha os textos por cima; os campos de texto e as caixas de selecao sao
widgets CTk (fundo solido) e o botao principal e desenhado no canvas com um
gradiente na cor de destaque extraida da propria imagem.
"""

import colorsys

from PIL import Image, ImageDraw, ImageFilter

from caminhos import fundo_login
from registro import falha

DESIGN_W = 1000
DESIGN_H = 760

# ------------------------------------------------------------------ cores ---
CORES = {
    "texto": "#ffffff",
    "suave": "#c3bbe0",
    "olho": "#9a92b8",
    "erro": "#ff7a7a",
    "ok": "#4ade80",
    "vidro": (14, 10, 28),
    "vidro_alfa": 178,
    "borda": (255, 255, 255),
    "borda_alfa": 26,
    "campo": "#1b1530",
    "campo_borda": "#2f2750",
    "segmento": "#241c40",
    "segmento_hover": "#312757",
}

# cartao do formulario (unidades de design)
CARTAO = (48, 84, 512, 676)
PADDING = 32
COLUNA = (CARTAO[0] + PADDING, CARTAO[2] - PADDING)   # x inicial / x final

# cabecalho dentro do cartao
EYEBROW_Y = 128
TITULO_Y = 150
SUBTITULO_Y = 202
SEGMENTO_Y = 236
SEGMENTO_H = 38
FORM_TOPO = 300
FORM_BASE = 648

# logotipo (centralizado no espaco livre A DIREITA do cartao do formulario
# e com folga para nao ser cortado na borda da janela)
LOGO_CX = 754
LOGO_CY = 378
LOGO_LADO = 424


# ------------------------------------------------------- cor de destaque ---
def cor_de_destaque(caminho=None):
    """Extrai do logo a cor de destaque (matiz mais dominante e saturado).

    Usa a imagem real: se o logo mudar, o botao muda junto.
    """
    caminho = caminho or fundo_login()
    try:
        img = Image.open(caminho).convert("RGBA").resize((128, 128), Image.LANCZOS)
    except Exception:
        falha("calcular a cor de destaque")
        return "#2fd9a0"

    grupos = {}
    for r, g, b, a in img.getdata():
        if a < 200:
            continue
        matiz, luz, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
        if sat < 0.40 or luz < 0.28 or luz > 0.78:
            continue
        faixa = int(matiz * 12) % 12
        grupos.setdefault(faixa, []).append((r, g, b))

    if not grupos:
        return "#2fd9a0"

    faixa = max(grupos, key=lambda f: len(grupos[f]))
    itens = grupos[faixa]
    r = sum(i[0] for i in itens) / len(itens)
    g = sum(i[1] for i in itens) / len(itens)
    b = sum(i[2] for i in itens) / len(itens)

    matiz, luz, sat = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    matiz, luz, sat = colorsys.hls_to_rgb(matiz, min(0.62, max(0.42, luz * 1.25)),
                                         min(0.95, sat * 1.15))
    return "#%02x%02x%02x" % (int(matiz * 255), int(luz * 255), int(sat * 255))


def _variar(cor, fator=1.0, alpha=1.0):
    """Clareia/escurece uma cor hex (fator > 1 clareia)."""
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    if fator >= 1:
        r = int(r + (255 - r) * (fator - 1))
        g = int(g + (255 - g) * (fator - 1))
        b = int(b + (255 - b) * (fator - 1))
    else:
        r, g, b = int(r * fator), int(g * fator), int(b * fator)
    return "#%02x%02x%02x" % (r, g, b)


def tom_texto_sobre(cor):
    """Texto preto ou branco, conforme o brilho da cor de fundo."""
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    brilho = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#08130f" if brilho > 0.55 else "#ffffff"


# --------------------------------------------------------------- cenario ---
def _gradiente_base(largura, altura):
    """Fundo escuro com um brilho na cor de destaque."""
    import numpy as np

    yy, xx = np.mgrid[0:altura, 0:largura]
    base = np.zeros((altura, largura, 3), dtype=np.float32)
    # vertical: quase preto no topo -> violeta escuro embaixo
    grad = (yy / max(1, altura - 1))[..., None]
    topo = np.array([9.0, 7.0, 18.0], dtype=np.float32)
    baixo = np.array([21.0, 13.0, 38.0], dtype=np.float32)
    base += topo + (baixo - topo) * grad

    # brilho radial atras do logo
    dist = np.sqrt(((xx - LOGO_CX * largura / DESIGN_W) / (largura * 0.45)) ** 2 +
                   ((yy - LOGO_CY * altura / DESIGN_H) / (altura * 0.55)) ** 2)
    brilho = (np.clip(1 - dist, 0, 1) ** 2)[..., None]
    base += brilho * np.array([26.0, 60.0, 46.0], dtype=np.float32)
    return Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))


def _vidro(img, caixa, raio):
    """Cartao de vidro translucido com borda fina."""
    sobre = Image.new("RGBA", img.size, (0, 0, 0, 0))
    desenho = ImageDraw.Draw(sobre)
    desenho.rounded_rectangle(
        caixa, radius=raio,
        fill=CORES["vidro"] + (CORES["vidro_alfa"],),
        outline=CORES["borda"] + (CORES["borda_alfa"],), width=1)
    return Image.alpha_composite(img.convert("RGBA"), sobre).convert("RGB")


def renderizar_cenario(caminho, largura, altura, destaque="#2fd9a0"):
    """Fundo da tela de login: gradiente + logo com glow + cartao de vidro."""
    img = _gradiente_base(largura, altura)

    # --- logotipo com brilho atras -------------------------------------
    try:
        logo = Image.open(caminho).convert("RGBA")
    except Exception:
        logo = None

    if logo is not None:
        lado = int(LOGO_LADO * largura / DESIGN_W)
        logo = logo.resize((lado, lado), Image.LANCZOS)
        pos_x = int(LOGO_CX * largura / DESIGN_W - lado / 2)
        pos_y = int(LOGO_CY * altura / DESIGN_H - lado / 2)

        brilho = logo.filter(ImageFilter.GaussianBlur(radius=lado * 0.045))
        brilho.putalpha(brilho.getchannel("A").point(lambda v: int(v * 0.55)))
        img = Image.alpha_composite(
            img.convert("RGBA"),
            Image.new("RGBA", img.size, (0, 0, 0, 0))).convert("RGB")
        fundo = Image.new("RGBA", img.size, (0, 0, 0, 0))
        fundo.paste(brilho, (pos_x, pos_y), brilho)
        img = Image.alpha_composite(img.convert("RGBA"), fundo).convert("RGB")

        frente = Image.new("RGBA", img.size, (0, 0, 0, 0))
        frente.paste(logo, (pos_x, pos_y), logo)
        img = Image.alpha_composite(img.convert("RGBA"), frente).convert("RGB")

    # --- cartao do formulario -------------------------------------------
    escala_x = largura / DESIGN_W
    escala_y = altura / DESIGN_H
    x1, y1, x2, y2 = CARTAO
    caixa = (x1 * escala_x, y1 * escala_y, x2 * escala_x, y2 * escala_y)
    img = _vidro(img, caixa, int(24 * min(escala_x, escala_y)))

    return img


# ------------------------------------------------------- botao com gradiente -
def retangulo_arredondado(cor, largura, altura, raio=10, alfa=255):
    """Retangulo de cor solida com cantos arredondados (imagem RGBA)."""
    largura = max(2, int(largura))
    altura = max(2, int(altura))
    cor = cor.lstrip("#")
    rgb = tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle((0, 0, largura - 1, altura - 1),
                                          radius=int(raio),
                                          fill=rgb + (alfa,))
    return img


def botao_gradiente(cor, largura, altura, raio=12, clarear=0.0):
    """Retangulo arredondado com gradiente vertical (imagem RGBA)."""
    from tema_visual import botao_gradiente as _gradiente
    return _gradiente(cor, largura, altura, raio, clarear)


def caixa_marcada(cor="#35e3ab", lado=16, marcada=False, borda=(140, 130, 180)):
    """Caixa de selecao arredondada (RGBA) para desenhar no canvas."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(img)
    if marcada:
        desenho.rounded_rectangle((0, 0, lado - 1, lado - 1), radius=4,
                                  fill=tuple(int(cor.lstrip("#")[i:i + 2], 16)
                                             for i in (0, 2, 4)) + (255,))
    else:
        desenho.rounded_rectangle((1, 1, lado - 2, lado - 2), radius=4,
                                  outline=borda + (255,), width=2)
    return img


def texto_espacado(canvas, x, y, texto, fonte, cor, espaco=2.0):
    """Desenha texto com espacamento entre letras (o Tk nao tem tracking)."""
    cursor = x
    for caractere in texto:
        canvas.create_text(cursor, y, text=caractere, font=fonte, fill=cor,
                           anchor="nw")
        cursor += fonte.measure(caractere) + espaco
    return cursor

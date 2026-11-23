# -*- coding: utf-8 -*-
"""
Tema visual da tela "Caminho da Maestria".

A tela e montada em 3 camadas:

  1. CENARIO (PIL): arte do Grand Chase com gradaçao roxa, brilho radial e
     vinheta + os paineis de "vidro" (retangulos translucidos com borda).
  2. CANVAS (Tk): a imagem do cenario + TODOS os textos e icones.
     Como o canvas e opaco, o texto compoe exatamente sobre o vidro.
  3. WIDGETS (CTk): campos e botoes de fundo SOLIDO (entrada de arquivo,
     ESCOLHER ARQUIVO, Import Excel, campo do nivel do chaser e o check).

O layout e descrito em unidades de design (1152 x 820, o tamanho do mockup)
e escalado proporcionalmente para o tamanho da janela.
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from registro import falha
from versao_app import VERSAO

DESIGN_W = 1152
DESIGN_H = 820

FONTE_EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"

# --------------------------------------------------------------------- cores
CORES = {
    "texto": "#ffffff",
    "suave": "#b8b2ce",          # subtitulos, titulos dos cards
    "olho": "#a49dbb",           # eyebrow
    "roxo": "#8b5cf6",           # botao roxo
    "roxo_hover": "#7c3aed",
    "entrada": "#f2f0f8",        # campo de arquivo
    "entrada_texto": "#241d3d",
    "botao_escuro": "#2b2542",   # botao ESCOLHER ARQUIVO
    "botao_claro": "#f4f2fa",    # botao Zerar dungeons
    "botao_claro_texto": "#1c1533",
    "chaser": "#b9a6e8",         # campo do nivel do chaser
    "laranja": "#f5c451",         # o nivel do chaser no perfil
    "vidro": (26, 18, 52),       # cor dos paineis translucidos
    "vidro_alfa": 170,
    "vidro_borda": (255, 255, 255),
    "vidro_borda_alfa": 30,
}

# icones (o Tk nao desenha emoji: sao assados pelo PIL)
ICONES = {
    "globo": "\U0001F310",
    "monitor": "\U0001F5A5",
    "documento": "\U0001F4C4",
    "entrada": "\U0001F4E5",
    "reiniciar": "\u21bb",
    "cronometro": "\u23f1",
    "progresso": "\U0001F4C8",
    "lupa": "\U0001F50D",
}

# ------------------------------------------------------------------ layout --
# (x1, y1, x2, y2) em unidades de design
TITULO_LINHA1 = (54, 74)
TITULO_LINHA2 = (54, 120)
EYEBROW = (56, 48)
SUBTITULO = (56, 188)

BOTOES_LINHA1 = [
    # o "Apoiar" (doacao) ocupa o lugar do antigo botao "English"
    ("coracao", "Apoiar", (574, 131, 677, 175)),
    # a versao instalada; clicar procura atualizacao (app_atualizacao.py)
    ("reiniciar", f"Versão {VERSAO}", (689, 131, 857, 175)),
    ("documento", "Exportar Excel", (869, 131, 1009, 175)),
]

# o botao de doacao tem fundo proprio (gradiente roxo), assado no cenario
BOTAO_DOACAO = "Apoiar"
BOTOES_LINHA2 = [
    ("reiniciar", "Zerar dungeons semanais", (574, 189, 790, 233)),
    ("cronometro", "Miss\u00e3o R\u00e1pida: Alternar", (802, 189, 1009, 233)),
]

# --------------------------------------------------------- perfil (hero) --
# o painel de vidro vago do hero (56, 258, 790, 415) vira o perfil
PERFIL_PAINEL = (56, 258, 790, 415)
PERFIL_AVATAR = (56 + 80, 258 + 78, 46)     # centro x, centro y, raio
PERFIL_TEXTO = (56 + 132, 258 + 52)          # x, y do texto
PERFIL_ICONE = (790 - 76, 258 + 76)         # centro do icone do nivel
PERFIL_ICONE_LADO = 142                      # tamanho do icone (design)
# a barra de EXP (preenche conforme o nivel do chaser)
PERFIL_EXP = (56 + 132, 258 + 106, 790 - 250, 16)   # x1, y1, x2, altura
# a pasta com os icones por nivel do chaser (cl1.png, cl100.png, ...)
PASTA_CHASER = "chaser"
# a pasta com as 25 fotos de perfil (<personagem>_icon.png)
PASTA_PERFIL = "perfil"

# ------------------------------------------------------- barra de filtros --
# (acima dos cards, depois do hero)
FILTROS_BUSCA = (56, 872, 1096, 916)
FILTROS_PAINEL1 = (56, 928, 400, 1142)
FILTROS_PAINEL2 = (412, 928, 756, 1142)
FILTROS_PAINEL3 = (768, 928, 1096, 1142)
# a grade de cards comeca depois da barra
FILTROS_FIM = 1166

# opcao do MODO da Missao Rapida (check embaixo do botao "Missao Rapida")
MISSAO_MODO = (802, 243, 1009, 267)

IMPORT_BLOCO = (56, 258, 790, 415)
IMPORT_TITULO = (78, 280)
IMPORT_DESCRICAO = (78, 308)
IMPORT_BOTOES = {
    "escolher": (78, 341, 240, 385),
    "entrada": (240, 341, 652, 385),
    "importar": (660, 341, 792, 385),
}

CART_COLUNAS = [(56, 398), (410, 750), (762, 1100)]
CART_LINHAS = [(452, 543), (555, 646), (658, 749)]

# cartoes: (chave, titulo, subtitulo)
CARDS = [
    ("caminho_abissal", "CAMINHO ABISSAL", "personagens conclu\u00eddos"),
    ("poder_medio", "ATAQUE TOTAL M\u00c9DIO", ""),
    ("torre", "TORRE DAS ILUS\u00d5ES", "personagens conclu\u00eddos"),
    ("void123", "VOID (1, 2 E 3)", "personagens conclu\u00eddos"),
    ("void4", "VOID 4", "personagens conclu\u00eddos"),
    ("nivel", "N\u00cdVEL DO CHASER", ""),
    ("despertar", "DESPERTAR COMPLETO", "characters complete"),
    ("libertacao", "LIBERTA\u00c7\u00c3O COMPLETA", "characters complete"),
]

# posicao do campo/botao do nivel do chaser (dentro do 6o cartao)
CHASER_CAMPO = (780, 601, 1030, 641)
CHASER_CHECK = (1044, 601, 1084, 641)


class Layout:
    """Converte as unidades de design para pixels da janela."""

    def __init__(self, largura, altura):
        self.largura = largura
        self.altura = altura
        self.s = min(largura / DESIGN_W, altura / DESIGN_H)
        self.ox = (largura - DESIGN_W * self.s) / 2
        self.oy = (altura - DESIGN_H * self.s) / 2

    # coordenadas
    def x(self, v):
        return self.ox + v * self.s

    def y(self, v):
        return self.oy + v * self.s

    def w(self, v):
        return v * self.s

    def h(self, v):
        return v * self.s

    def f(self, tamanho):
        """Tamanho de fonte em pixels (tk so aceita inteiro)."""
        return max(1, int(round(tamanho * self.s)))

    def caixa(self, valores):
        """(x1, y1, x2, y2) de design -> (x1, y1, x2, y2) em pixels."""
        x1, y1, x2, y2 = valores
        return (self.x(x1), self.y(y1), self.x(x2), self.y(y2))

    def ponto(self, valores):
        x, y = valores
        return (self.x(x), self.y(y))


# --------------------------------------------------------------- cenenario --
def _vidro(img, caixa, raio, cor=None, alfa=None, borda_alfa=None, largura=1):
    """Desenha um retangulo de vidro (translucido, com borda) na imagem."""
    if alfa is None:
        alfa = CORES["vidro_alfa"]
    if borda_alfa is None:
        borda_alfa = CORES["vidro_borda_alfa"]
    sobre = Image.new("RGBA", img.size, (0, 0, 0, 0))
    desenho = ImageDraw.Draw(sobre)
    desenho.rounded_rectangle(
        caixa, radius=raio,
        fill=(cor or CORES["vidro"]) + (alfa,),
        outline=CORES["vidro_borda"] + (borda_alfa,),
        width=largura,
    )
    return Image.alpha_composite(img.convert("RGBA"), sobre).convert("RGB")


def _arte(caminho, largura, altura, recorte=1.0):
    """A arte do fundo: MESMA enquadracao ja usada no app (cobre a janela).

    O recorte fica em 1.0 de proposito: a imagem continua como esta
    posicionada, so mudando a cor (gradaçao roxa) e o desfoque.
    """
    base = Image.open(caminho).convert("RGB")
    if recorte < 1.0:
        base = base.crop((0, 0, base.width, int(base.height * recorte)))
    escala = max(largura / base.width, altura / base.height)
    base = base.resize((max(1, round(base.width * escala)),
                        max(1, round(base.height * escala))), Image.LANCZOS)
    esquerda = (base.width - largura) // 2
    base = base.crop((esquerda, 0, esquerda + largura, altura))
    return base


def _gradiente(base):
    """Brilho radial violeta + vinheta (da a 'fumaça' do mockup)."""
    try:
        import numpy as np
    except Exception:
        falha("importar numpy (gradiente)")
        return base

    w, h = base.size
    yy, xx = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.66, h * 0.28
    dist = np.sqrt(((xx - cx) / (w * 0.78)) ** 2 + ((yy - cy) / (h * 0.78)) ** 2)

    arr = np.asarray(base).astype(np.float32)
    # 1) puxa a arte para o violeta (o mockup e todo roxo)
    arr = arr * 0.42 + np.array([38.0, 16.0, 74.0], dtype=np.float32)
    # 2) brilho radial violeta no alto a direita
    brilho = (np.clip(1.0 - dist, 0, 1) ** 2)[..., None]
    arr = arr + brilho * np.array([86.0, 34.0, 150.0], dtype=np.float32)
    # 3) vinheta forte (as bordas somem no roxo)
    vinheta = np.clip((dist - 0.18) / 0.62, 0, 1)
    arr = arr * (1.0 - 0.62 * vinheta[..., None])
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def render_arte(caminho_fundo, largura, altura):
    """Somente a arte de fundo (ja graduada em roxo) — usada como fundo FIXO."""
    img = _arte(caminho_fundo, largura, altura)
    img = _gradiente(img)
    return img.filter(ImageFilter.GaussianBlur(1.8))


def render_paineis(largura, altura, lay):
    """Somente os paineis de vidro (RGBA) — rolem junto com o conteudo."""
    from PIL import Image as _Image
    base = _Image.new("RGBA", (largura, altura), (0, 0, 0, 0))

    def _vidro(img, caixa, raio, cor=None, alfa=None, borda_alfa=None):
        if alfa is None:
            alfa = CORES["vidro_alfa"]
        if borda_alfa is None:
            borda_alfa = CORES["vidro_borda_alfa"]
        sobre = _Image.new("RGBA", img.size, (0, 0, 0, 0))
        desenho = ImageDraw.Draw(sobre)
        desenho.rounded_rectangle(
            caixa, radius=raio,
            fill=(cor or CORES["vidro"]) + (alfa,),
            outline=CORES["vidro_borda"] + (borda_alfa,), width=1)
        return _Image.alpha_composite(img, sobre)

    # --- botoes do cabecalho (linha 1) --------------------------------
    for _icone, _rotulo, caixa in BOTOES_LINHA1:
        x1, y1, x2, y2 = lay.caixa(caixa)
        if _rotulo == BOTAO_DOACAO:
            # o botao de doacao e roxo (gradiente assado no cenario)
            grad = botao_gradiente(CORES["roxo"], int(x2 - x1), int(y2 - y1),
                                   raio=lay.f(10))
            sobre = Image.new("RGBA", base.size, (0, 0, 0, 0))
            sobre.alpha_composite(grad, (int(x1), int(y1)))
            base = Image.alpha_composite(base, sobre)
        else:
            base = _vidro(base, (x1, y1, x2, y2), lay.f(10), alfa=150,
                          borda_alfa=42)

    # --- botoes do cabecalho (linha 2) --------------------------------
    for indice, (_icone, _rotulo, caixa) in enumerate(BOTOES_LINHA2):
        x1, y1, x2, y2 = lay.caixa(caixa)
        if indice == 0:
            base = _vidro(base, (x1, y1, x2, y2), lay.f(10),
                          cor=(244, 242, 250), alfa=248, borda_alfa=0)
        else:
            base = _vidro(base, (x1, y1, x2, y2), lay.f(10), alfa=150,
                          borda_alfa=42)

    # --- bloco de importacao -------------------------------------------
    x1, y1, x2, y2 = lay.caixa(IMPORT_BLOCO)
    base = _vidro(base, (x1, y1, x2, y2), lay.f(16))

    # --- cartoes -------------------------------------------------------
    for _chave, _titulo, _sub in CARDS:
        caixa = lay.caixa(_caixa_do_cartao(_chave))
        base = _vidro(base, caixa, lay.f(12))

    return base


def render_cenario(caminho_fundo, largura, altura, lay):
    """Fundo completo (arte + paineis de vidro) — usado em telas unicas."""
    img = render_arte(caminho_fundo, largura, altura).convert("RGBA")
    img = Image.alpha_composite(img, render_paineis(largura, altura, lay))
    return img.convert("RGB")


def _caixa_do_cartao(chave):
    """Caixa (design) do cartao a partir da sua chave."""
    for indice, (chave_cartao, _t, _s) in enumerate(CARDS):
        if chave_cartao == chave:
            coluna = indice % 3
            linha = indice // 3
            x1, x2 = CART_COLUNAS[coluna]
            y1, y2 = CART_LINHAS[linha]
            return (x1, y1, x2, y2)
    return CART_COLUNAS[0] + CART_LINHAS[0]


def posicao_do_cartao(chave):
    """(caixa, linha, coluna) do cartao em unidades de design."""
    for indice, (chave_cartao, _t, _s) in enumerate(CARDS):
        if chave_cartao == chave:
            return _caixa_do_cartao(chave), indice // 3, indice % 3
    return (CART_COLUNAS[0][0], CART_LINHAS[0][0], CART_COLUNAS[0][1],
            CART_LINHAS[0][1]), 0, 0


def retangulo_alfa(cor=(139, 92, 246), alfa=70, tamanho=(8, 8), raio=0):
    """Imagem RGBA translucida (usada como destaque de botao no canvas)."""
    if raio:
        from PIL import ImageDraw
        img = Image.new("RGBA", (int(tamanho[0]), int(tamanho[1])), (0, 0, 0, 0))
        ImageDraw.Draw(img).rounded_rectangle(
            (0, 0, img.width - 1, img.height - 1), radius=int(raio),
            fill=(cor[0], cor[1], cor[2], alfa))
        return img
    img = Image.new("RGBA", tamanho, (cor[0], cor[1], cor[2], alfa))
    return img


def caixa_check(cor_fundo, cor_borda, tamanho=(18, 18), raio=5,
                 largura_borda=2):
    """Caixa de selecao (vazia ou marcada) para o canvas."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (int(tamanho[0]), int(tamanho[1])), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle(
        (largura_borda // 2, largura_borda // 2,
         img.width - largura_borda // 2 - 1, img.height - largura_borda // 2 - 1),
        radius=int(raio), fill=cor_fundo, outline=cor_borda,
        width=largura_borda)
    return img


def recorte_quadrado(img):
    """Recorta a imagem num quadrado (o topo, se for vertical)."""
    m = min(img.width, img.height)
    if img.height > img.width:
        # imagem alta: pega o topo (onde Usually fica o rosto)
        topo = (img.height - m) // 4
        return img.crop((0, topo, m, topo + m))
    esquerda = (img.width - m) // 2
    return img.crop((esquerda, 0, esquerda + m, m))


def avatar_circular(caminho, lado=96, cor_fundo=(58, 50, 92)):
    """Foto do usuario recortada em circulo (ou um circulo vazio)."""
    from PIL import Image, ImageDraw
    lado = max(16, int(lado))
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    if caminho:
        try:
            foto = recorte_quadrado(Image.open(caminho).convert("RGBA"))
            foto = foto.resize((lado, lado), Image.LANCZOS)
            mascara = Image.new("L", (lado, lado), 0)
            ImageDraw.Draw(mascara).ellipse((0, 0, lado - 1, lado - 1), fill=255)
            img.paste(foto, (0, 0), mascara)
            return img
        except Exception:
            falha("montar o avatar circular")
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, lado - 2, lado - 2), fill=cor_fundo + (255,),
              outline=(255, 255, 255, 40), width=2)
    return img


def icone_chaser(caminho, lado=142, opacidade=0.7):
    """Icone do nivel do chaser, com opacidade reduzida (ou vazio)."""
    from PIL import Image
    lado = max(16, int(lado))
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    if not caminho:
        return img
    try:
        arte = Image.open(caminho).convert("RGBA")
        m = min(arte.width, arte.height)
        arte = arte.crop(((arte.width - m) // 2, (arte.height - m) // 2,
                           (arte.width - m) // 2 + m, (arte.height - m) // 2 + m))
        arte = arte.resize((lado, lado), Image.LANCZOS)
        alfa = arte.getchannel("A").point(lambda v: int(v * opacidade))
        arte.putalpha(alfa)
        img.paste(arte, (0, 0), arte)
    except Exception:
        falha("montar o icone do chaser")
    return img


def circulo_opcao(marcado, tamanho=20, cor_marca=(139, 92, 246),
                  cor_borda=(150, 140, 190), cor_fundo=(35, 30, 60),
                  cor_check=(255, 255, 255)):
    """Circulo de opcao dos filtros: vazio ou com um CHECK."""
    from PIL import Image, ImageDraw
    lado = max(8, int(tamanho))
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((1, 1, lado - 2, lado - 2),
              fill=cor_fundo + (255,), outline=cor_borda + (255,), width=2)
    if marcado:
        # check (v) desenhado com o PIL (o Tk nao desenha emoji no canvas)
        m = lado * 0.28
        largura = max(2, int(lado * 0.11))
        d.line((m, lado * 0.52, lado * 0.44, lado * 0.68),
               fill=cor_check + (255,), width=largura)
        d.line((lado * 0.44, lado * 0.68, lado - m, lado * 0.34),
               fill=cor_check + (255,), width=largura)
    return img


def botao_gradiente(cor, largura, altura, raio=12, clarear=0.0):
    """Retangulo arredondado com gradiente vertical SUAVE (imagem RGBA)."""
    largura = max(4, int(largura))
    altura = max(4, int(altura))

    def _rgb(hexcor):
        hexcor = hexcor.lstrip("#")
        return tuple(int(hexcor[i:i + 2], 16) for i in (0, 2, 4))

    topo = _rgb(_variar(cor, 1.0 + clarear))
    baixo = _rgb(_variar(cor, 0.76))

    try:
        import numpy as np
        arr = np.zeros((altura, largura, 4), dtype=np.float32)
        for indice in range(3):
            arr[:, :, indice] = np.linspace(topo[indice], baixo[indice],
                                            altura)[:, None]
        arr[:, :, 3] = 255.0
        img = Image.fromarray(arr.astype("uint8"), "RGBA")
    except Exception:
        img = Image.new("RGBA", (largura, altura), topo + (255,))

    mascara = Image.new("L", (largura, altura), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, largura - 1, altura - 1),
                                               radius=raio, fill=255)
    img.putalpha(mascara)
    return img


def _variar(cor, fator=1.0):
    """Clareia (fator > 1) ou escurece (fator < 1) uma cor hex."""
    cor = cor.lstrip("#")
    r, g, b = (int(cor[i:i + 2], 16) for i in (0, 2, 4))
    if fator >= 1:
        r = int(r + (255 - r) * (fator - 1))
        g = int(g + (255 - g) * (fator - 1))
        b = int(b + (255 - b) * (fator - 1))
    else:
        r, g, b = int(r * fator), int(g * fator), int(b * fator)
    return "#%02x%02x%02x" % (r, g, b)


# ----------------------------------------------------------------- icones --
_cache_emoji = {}


def _desenhar_funil(lado, cor):
    """Funil (filtro) desenhado com PIL."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = lado * 0.18
    espessura = max(2, int(lado * 0.11))
    topo = (m, m * 0.8)
    baixo = (lado - m, lado * 0.42)
    d.polygon([topo, baixo, (lado / 2, lado - m * 0.6),
                (lado / 2, lado * 0.55)], fill=cor)
    return img


def _desenhar_ordenar(lado, cor):
    """Ordenar (linhas com setas) desenhado com PIL."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = lado * 0.20
    espessura = max(2, int(lado * 0.10))
    for i, largura in enumerate((0.62, 0.44, 0.26)):
        y = m + i * (lado - 2 * m) / 2.4
        d.line((m, y, m + (lado - 2 * m) * largura, y), fill=cor,
               width=espessura)
    # seta para baixo (a ordenacao e decrescente)
    x = lado - m
    d.polygon([(x - lado * 0.13, lado * 0.44), (x + lado * 0.13, lado * 0.44),
                (x, lado * 0.72)], fill=cor)
    return img


def _desenhar_coracao(lado, cor):
    """Coracao (doacao) desenhado com PIL: o emoji ❤ sairia vermelho
    demais no botao roxo."""
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = lado * 0.16
    raio = lado * 0.23
    # duas circunferencias (as "orelhas") + o triangulo de baixo
    d.ellipse((m, m, m + 2 * raio, m + 2 * raio), fill=cor)
    d.ellipse((lado - m - 2 * raio, m, lado - m, m + 2 * raio), fill=cor)
    d.polygon([(m - lado * 0.01, m + raio * 0.95),
               (lado - m + lado * 0.01, m + raio * 0.95),
               (lado / 2, lado - m * 0.92)], fill=cor)
    return img


def _desenhar_reiniciar(lado, cor):
    """Seta circular (↻) desenhada com PIL: em tamanho pequeno o emoji
    fica fino demais para ler."""
    import math

    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(img)
    margem = lado * 0.26
    espessura = max(2, int(lado * 0.13))
    caixa = (margem, margem, lado - margem, lado - margem)
    desenho.arc(caixa, 55, 340, fill=cor, width=espessura)

    angulo = math.radians(340)
    cx = (caixa[0] + caixa[2]) / 2
    cy = (caixa[1] + caixa[3]) / 2
    raio = (caixa[2] - caixa[0]) / 2
    px = cx + raio * math.cos(angulo)
    py = cy + raio * math.sin(angulo)
    # tangente no sentido horario (y para baixo)
    tx, ty = -math.sin(angulo), math.cos(angulo)
    tam = lado * 0.30
    desenho.polygon([
        (px + tx * tam, py + ty * tam),
        (px - tx * tam * 0.25 + ty * tam * 0.45,
         py - ty * tam * 0.25 - tx * tam * 0.45),
        (px - tx * tam * 0.25 - ty * tam * 0.45,
         py - ty * tam * 0.25 + tx * tam * 0.45),
    ], fill=cor)
    return img


def icone(nome, tamanho, cor=None):
    """Desenha um emoji com PIL e devolve uma imagem RGBA QUADRADA.

    O quadrado garante que o layout do botao (icone + texto) possa ser
    calculado com precisao: o glifo fica centralizado dentro dele.
    """
    chave = (nome, int(tamanho), cor)
    if chave in _cache_emoji:
        return _cache_emoji[chave]
    lado = max(8, int(tamanho))

    if nome == "coracao":
        img = _desenhar_coracao(lado, cor or (255, 255, 255, 255))
        _cache_emoji[chave] = img
        return img

    if nome == "reiniciar":
        img = _desenhar_reiniciar(lado, cor or (255, 255, 255, 255))
        _cache_emoji[chave] = img
        return img

    if nome == "funil":
        img = _desenhar_funil(lado, cor or (255, 255, 255, 255))
        _cache_emoji[chave] = img
        return img

    if nome == "ordenar":
        img = _desenhar_ordenar(lado, cor or (255, 255, 255, 255))
        _cache_emoji[chave] = img
        return img

    glifo = ICONES.get(nome, "")
    fonte = ImageFont.truetype(FONTE_EMOJI, lado)
    img = Image.new("RGBA", (lado, lado), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(img)
    if glifo:
        caixa = fonte.getbbox(glifo)
        largura = caixa[2] - caixa[0]
        altura = caixa[3] - caixa[1]
        x = (lado - largura) / 2 - caixa[0]
        y = (lado - altura) / 2 - caixa[1]
        desenho.text((x, y), glifo, font=fonte, embedded_color=True)
    _cache_emoji[chave] = img
    return img

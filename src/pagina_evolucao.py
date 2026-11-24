# -*- coding: utf-8 -*-
"""
A pagina "Evolucao semanal" desenhada como UMA imagem (PIL).

A janela mostra esta imagem e o "Copiar imagem" / "Salvar PNG" exportam
a MESMA imagem: o que se ve e o que se compartilha. O visual segue o do
app (a arte do cenario no topo, paineis de vidro roxos, Segoe UI).

    imagem = montar(semanas, atual, destaque=date(2026, 11, 25),
                    nick="Fulano", versao="1.0.1")

`semanas` sao as fotos do banco (historico.de_historico) e `atual` a
semana parcial da tela (historico.da_tela). Os numeros vem de
historico.py; aqui e so desenho.
"""

import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

import caminhos
import historico as h
import tema_visual as tv
from registro import falha

LARGURA = 1080
MARGEM = 48
VAO = 20

FUNDO = (22, 17, 43)
TEXTO = (255, 255, 255)
SUAVE = (184, 178, 206)
APAGADO = (122, 114, 152)
ROXO = (139, 92, 246)
LILAS = (196, 181, 253)
VERDE = (52, 211, 153)
VERMELHO = (251, 113, 133)
AMARELO = (245, 196, 81)
GRADE = (61, 52, 96)

_ARQUIVOS_FONTE = {
    "normal": "segoeui.ttf", "semi": "seguisb.ttf",
    "bold": "segoeuib.ttf", "black": "seguibl.ttf",
}
_cache_fontes = {}


def _fonte(tamanho, peso="normal"):
    chave = (tamanho, peso)
    if chave not in _cache_fontes:
        caminho = os.path.join(os.environ.get("WINDIR", r"C:\Windows"),
                               "Fonts", _ARQUIVOS_FONTE[peso])
        try:
            _cache_fontes[chave] = ImageFont.truetype(caminho, tamanho)
        except OSError:
            _cache_fontes[chave] = ImageFont.load_default(tamanho)
    return _cache_fontes[chave]


# ------------------------------------------------------------ formatacao
def numero(valor):
    """618002 -> '618.002' (milhar com ponto, como o app)."""
    if valor is None:
        return "—"
    return f"{int(round(valor)):,}".replace(",", ".")


def curto(valor):
    """618002 -> '618 mil'; 1250000 -> '1,25 mi' (eixos dos graficos)."""
    if valor is None:
        return ""
    valor = float(valor)
    if abs(valor) >= 1_000_000:
        return f"{valor / 1_000_000:.2f}".rstrip("0").rstrip(".").replace(
            ".", ",") + " mi"
    if abs(valor) >= 1_000:
        return f"{valor / 1_000:.0f} mil"
    return f"{valor:.0f}"


def diferenca_texto(diferenca, percentual=None):
    """'+30.000 (+7,5%)' / '−12' / 'sem mudança'."""
    if diferenca is None:
        return ""
    if round(diferenca) == 0:
        return "sem mudança"
    sinal = "+" if diferenca > 0 else "\u2212"
    texto = sinal + numero(abs(diferenca))
    if percentual is not None:
        texto += f" ({sinal}{abs(percentual):.1f}%)".replace(".", ",")
    return texto


def _cor_da_diferenca(diferenca):
    if diferenca is None or round(diferenca) == 0:
        return SUAVE
    return VERDE if diferenca > 0 else VERMELHO


def rotulo_semana(semana):
    """O rotulo do eixo: inicio da semana (dd/mm) ou 'atual'."""
    if semana["data"] is None:
        return "atual"
    inicio, _fim = h.intervalo_da_semana(semana["data"])
    return inicio.strftime("%d/%m")


# ---------------------------------------------------------------- desenho
def _texto(d, xy, texto, tamanho, cor=TEXTO, peso="normal", ancora="la"):
    d.text(xy, texto, font=_fonte(tamanho, peso), fill=cor, anchor=ancora)


def _largura(texto, tamanho, peso="normal"):
    return _fonte(tamanho, peso).getlength(texto)


def _painel(img, caixa, raio=16):
    return tv._vidro(img, caixa, raio, alfa=200, borda_alfa=36)


def _titulo_secao(d, x, y, texto):
    _texto(d, (x, y), texto.upper(), 13, ROXO, "bold")


def _escala(valores, minimo_zero=False):
    """(menor, maior) do eixo, com folga, para os valores dados."""
    numeros = [v for v in valores if v is not None]
    if not numeros:
        return 0, 1
    menor, maior = min(numeros), max(numeros)
    if minimo_zero:
        menor = 0
    if maior == menor:
        # ataque, pecas e desafios nunca sao negativos: o eixo nao desce
        # abaixo de zero
        folga = abs(maior) * 0.1 or 1
        return max(0, menor - folga), maior + folga
    folga = (maior - menor) * 0.15
    return (menor if minimo_zero else max(0, menor - folga)), maior + folga


def marcas(menor, maior, quantas=3):
    """Marcas "redondas" do eixo (1, 2, 2,5 ou 5 x 10^n; passo >= 1)."""
    import math
    bruto = max((maior - menor) / quantas, 1e-9)
    potencia = 10 ** math.floor(math.log10(bruto))
    passo = next(m * potencia for m in (1, 2, 2.5, 5, 10)
                 if m * potencia >= bruto)
    passo = max(passo, 1)
    inicio = math.floor(menor / passo) * passo
    fim = math.ceil(maior / passo) * passo
    if fim == inicio:
        fim = inicio + passo
    return [inicio + passo * i
            for i in range(int(round((fim - inicio) / passo)) + 1)]


def _grafico_linha(d, caixa, rotulos, valores, cor, parcial_ultimo):
    """Linha com pontos; o ultimo ponto (semana atual) fica vazado."""
    x1, y1, x2, y2 = caixa
    area_x1 = x1 + 64
    eixo = marcas(*_escala(valores))
    menor, maior = eixo[0], eixo[-1]
    for valor in eixo:
        y = y2 - (y2 - y1) * (valor - menor) / (maior - menor)
        d.line((area_x1, y, x2, y), fill=GRADE, width=1)
        _texto(d, (area_x1 - 10, y), curto(valor), 12, APAGADO, ancora="rm")
    n = len(valores)
    passo = (x2 - area_x1 - 30) / max(1, n - 1)
    pontos = []
    for i, valor in enumerate(valores):
        x = area_x1 + 15 + (passo * i if n > 1 else (x2 - area_x1 - 30) / 2)
        y = None if valor is None else \
            y2 - (y2 - y1) * (valor - menor) / (maior - menor)
        pontos.append((x, y))
        _texto(d, (x, y2 + 12), rotulos[i], 12, SUAVE, ancora="mt")
    validos = [(i, p) for i, p in enumerate(pontos) if p[1] is not None]
    for (i, a), (_j, b) in zip(validos, validos[1:]):
        if parcial_ultimo and _j == n - 1:
            _tracejado(d, a, b, cor)
        else:
            d.line((a, b), fill=cor, width=3)
    for i, (x, y) in validos:
        raio = 6
        if parcial_ultimo and i == n - 1:
            d.ellipse((x - raio, y - raio, x + raio, y + raio),
                      fill=FUNDO, outline=cor, width=3)
        else:
            d.ellipse((x - raio, y - raio, x + raio, y + raio), fill=cor)
    if validos:
        i, (x, y) = validos[-1]
        _texto(d, (x, y - 14), numero(valores[i]), 13, TEXTO, "semi",
               ancora="mb")


def _tracejado(d, a, b, cor, traco=8):
    (xa, ya), (xb, yb) = a, b
    comprimento = max(1.0, ((xb - xa) ** 2 + (yb - ya) ** 2) ** 0.5)
    passos = int(comprimento // traco)
    for k in range(0, passos, 2):
        t1, t2 = k / passos, min(1, (k + 1) / passos)
        d.line((xa + (xb - xa) * t1, ya + (yb - ya) * t1,
                xa + (xb - xa) * t2, ya + (yb - ya) * t2), fill=cor, width=3)


def _grafico_barras(d, caixa, rotulos, series, maximo, parcial_ultimo):
    """Barras empilhadas por semana. series = [(valores, cor), ...]."""
    x1, y1, x2, y2 = caixa
    area_x1 = x1 + 40
    eixo = marcas(0, max(1, maximo), quantas=4)
    maximo = eixo[-1]
    for valor in eixo:
        y = y2 - (y2 - y1) * valor / maximo
        d.line((area_x1, y, x2, y), fill=GRADE, width=1)
        _texto(d, (area_x1 - 8, y), numero(valor), 12, APAGADO, ancora="rm")
    n = len(rotulos)
    largura_faixa = (x2 - area_x1) / max(1, n)
    largura_barra = min(46, largura_faixa * 0.6)
    for i in range(n):
        cx = area_x1 + largura_faixa * (i + 0.5)
        base = y2
        total = 0
        for valores, cor in series:
            valor = valores[i] or 0
            total += valor
            altura = (y2 - y1) * valor / maximo
            if altura <= 0:
                continue
            caixa_barra = (cx - largura_barra / 2, base - altura,
                           cx + largura_barra / 2, base)
            if parcial_ultimo and i == n - 1:
                d.rectangle(caixa_barra, outline=cor, width=2)
            else:
                d.rectangle(caixa_barra, fill=cor)
            base -= altura
        _texto(d, (cx, base - 6), numero(total), 12, TEXTO, "semi", ancora="mb")
        _texto(d, (cx, y2 + 12), rotulos[i], 12, SUAVE, ancora="mt")


def _barra_horizontal(d, x, y, largura, rotulo, valor, maximo, cor,
                      largura_rotulo=96):
    """Rotulo a esquerda, barra no meio e 'valor/maximo' a direita."""
    _texto(d, (x, y + 9), rotulo, 14, SUAVE, ancora="lm")
    bx1, bx2 = x + largura_rotulo, x + largura - 56
    d.rounded_rectangle((bx1, y + 3, bx2, y + 15), radius=6, fill=GRADE)
    if maximo and valor:
        fim = bx1 + (bx2 - bx1) * min(1, valor / maximo)
        d.rounded_rectangle((bx1, y + 3, max(bx1 + 12, fim), y + 15),
                            radius=6, fill=cor)
    _texto(d, (x + largura, y + 9), f"{valor}/{maximo}", 13, TEXTO, "semi",
           ancora="rm")


def _sparkline(d, caixa, valores, cor):
    x1, y1, x2, y2 = caixa
    numeros = [v for v in valores if v is not None]
    if len(numeros) < 2:
        d.line((x1, (y1 + y2) / 2, x2, (y1 + y2) / 2), fill=GRADE, width=2)
        return
    menor, maior = min(numeros), max(numeros)
    faixa = (maior - menor) or 1
    passo = (x2 - x1) / (len(valores) - 1)
    pontos = [(x1 + passo * i, y2 - (y2 - y1) * (v - menor) / faixa)
              for i, v in enumerate(valores) if v is not None]
    d.line(pontos, fill=cor, width=2)
    fx, fy = pontos[-1]
    d.ellipse((fx - 3, fy - 3, fx + 3, fy + 3), fill=cor)


# ------------------------------------------------------------ a pagina
def _cabecalho(img, titulo_semana, nick):
    altura = 210
    try:
        arte = tv.render_arte(caminhos.fundo_principal(), LARGURA, altura)
        img.paste(arte, (0, 0))
    except Exception:
        falha("desenhar a arte da pagina de evolucao")
    # escurece a base para o texto e o resto da pagina se encontrarem
    sombra = Image.new("RGBA", (LARGURA, altura), (0, 0, 0, 0))
    ds = ImageDraw.Draw(sombra)
    for y in range(altura):
        alfa = int(255 * max(0, (y - altura * 0.35) / (altura * 0.65)) ** 1.4)
        ds.line((0, y, LARGURA, y), fill=FUNDO + (alfa,))
    img.paste(Image.alpha_composite(img.crop((0, 0, LARGURA, altura))
                                    .convert("RGBA"), sombra).convert("RGB"),
              (0, 0))
    d = ImageDraw.Draw(img)
    _texto(d, (MARGEM, 50), "EVOLUÇÃO SEMANAL", 14, LILAS, "bold")
    _texto(d, (MARGEM, 70), "Caminho da Maestria", 44, TEXTO, "black")
    linha = titulo_semana + (f"  ·  {nick}" if nick else "")
    _texto(d, (MARGEM, 134), linha, 17, SUAVE, "semi")
    return altura


def _indice_destaque(todas, destaque):
    if destaque is not None:
        for i, semana in enumerate(todas):
            if semana["data"] == destaque:
                return i
    return len(todas) - 1


def montar(semanas, atual, destaque=None, nick="", versao=""):
    """A pagina inteira (PIL.Image RGB)."""
    todas = list(semanas) + ([atual] if atual else [])
    if not todas:
        todas = [{"data": None, "personagens": {}}]
    indice = _indice_destaque(todas, destaque)
    semana = todas[indice]
    anterior = todas[indice - 1] if indice > 0 else None
    parcial = todas[-1]["data"] is None

    if semana["data"] is None:
        titulo = ("Semana atual (parcial), desde "
                  f"{h.ultimo_reset().strftime('%d/%m/%Y')}")
    else:
        inicio, fim = h.intervalo_da_semana(semana["data"])
        titulo = (f"Semana de {inicio.strftime('%d/%m')} a "
                  f"{fim.strftime('%d/%m/%Y')}")

    img = Image.new("RGB", (LARGURA, 3200), FUNDO)
    y = _cabecalho(img, titulo, nick) + 6
    largura_util = LARGURA - 2 * MARGEM

    # --- 3 numeros de destaque -----------------------------------------
    medio = h.ataque_medio(semana)
    medio_ant = h.ataque_medio(anterior) if anterior else None
    pecas = h.contagem_pecas(semana)
    pecas_ant = h.contagem_pecas(anterior) if anterior else None
    desafios = h.contagem_desafios(semana)
    desafios_ant = h.contagem_desafios(anterior) if anterior else None

    total_pecas = pecas["equipamentos"] + pecas["acessorios"]
    max_pecas = pecas["max_equipamentos"] + pecas["max_acessorios"]
    tiles = [
        ("Ataque Total médio", numero(medio), "",
         h.variacao(medio, medio_ant)),
        ("Peças do Void", f"{total_pecas}/{max_pecas}",
         f"Equipamentos {pecas['equipamentos']}/{pecas['max_equipamentos']}"
         f"  ·  Acessórios {pecas['acessorios']}/{pecas['max_acessorios']}",
         h.variacao(total_pecas, (pecas_ant["equipamentos"]
                                  + pecas_ant["acessorios"])
                    if pecas_ant else None)),
        ("Desafios semanais", f"{desafios['total']}/{desafios['maximo']}",
         "feitos na semana",
         h.variacao(desafios["total"],
                    desafios_ant["total"] if desafios_ant else None)),
    ]
    largura_tile = (largura_util - 2 * VAO) / 3
    altura_tile = 132
    for i, (rotulo, valor, sub, (dif, pct)) in enumerate(tiles):
        x = MARGEM + i * (largura_tile + VAO)
        img = _painel(img, (x, y, x + largura_tile, y + altura_tile))
        d = ImageDraw.Draw(img)
        _texto(d, (x + 22, y + 20), rotulo.upper(), 12, SUAVE, "bold")
        _texto(d, (x + 22, y + 40), valor, 34, TEXTO, "bold")
        if sub:
            _texto(d, (x + 22, y + 88), sub, 12, APAGADO)
        texto_dif = diferenca_texto(dif, pct if i == 0 else None)
        if texto_dif:
            texto_dif += " vs semana anterior"
        elif anterior is None and semana["data"] is None:
            texto_dif = "o histórico começa no próximo reset (quarta, 3h)"
        elif anterior is None:
            texto_dif = "primeira semana registrada"
        _texto(d, (x + 22, y + 106), texto_dif, 12, _cor_da_diferenca(dif),
               "semi")
    y += altura_tile + VAO

    rotulos = [rotulo_semana(s) for s in todas]

    # --- ataque total medio por semana -----------------------------------
    altura_painel = 300
    img = _painel(img, (MARGEM, y, LARGURA - MARGEM, y + altura_painel))
    d = ImageDraw.Draw(img)
    _titulo_secao(d, MARGEM + 24, y + 22, "Ataque Total médio da conta")
    _grafico_linha(d, (MARGEM + 24, y + 70, LARGURA - MARGEM - 30,
                       y + altura_painel - 50),
                   rotulos, [h.ataque_medio(s) for s in todas], ROXO, parcial)
    y += altura_painel + VAO

    # --- pecas e desafios por semana (lado a lado) -----------------------
    meia = (largura_util - VAO) / 2
    altura_painel = 290
    quantos = max(len(s["personagens"]) for s in todas) or 1
    for lado, (titulo_painel, series, maximo, legenda) in enumerate([
            ("Peças do Void por semana",
             [([h.contagem_pecas(s)["equipamentos"] for s in todas], ROXO),
              ([h.contagem_pecas(s)["acessorios"] for s in todas], LILAS)],
             quantos * (len(h.EQUIPAMENTOS) + len(h.ACESSORIOS)),
             [("Equipamentos", ROXO), ("Acessórios", LILAS)]),
            ("Desafios semanais feitos",
             [([h.contagem_desafios(s)["total"] for s in todas], AMARELO)],
             quantos * len(h.DESAFIOS), [("Desafios", AMARELO)])]):
        x = MARGEM + lado * (meia + VAO)
        img = _painel(img, (x, y, x + meia, y + altura_painel))
        d = ImageDraw.Draw(img)
        _titulo_secao(d, x + 24, y + 22, titulo_painel)
        lx = x + 24
        for nome, cor in legenda:
            d.rounded_rectangle((lx, y + 48, lx + 12, y + 60), radius=3,
                                fill=cor)
            _texto(d, (lx + 18, y + 54), nome, 12, SUAVE, ancora="lm")
            lx += 28 + _largura(nome, 12)
        maior = max(sum(v[i] or 0 for v, _ in series)
                    for i in range(len(todas)))
        _grafico_barras(d, (x + 24, y + 96, x + meia - 20,
                            y + altura_painel - 46),
                        rotulos, series, max(maior, 1), parcial)
    y += altura_painel + VAO

    # --- pecas por tipo (semana em destaque) ------------------------------
    linhas = max(len(h.EQUIPAMENTOS), len(h.ACESSORIOS))
    altura_painel = 70 + linhas * 30 + 12
    img = _painel(img, (MARGEM, y, LARGURA - MARGEM, y + altura_painel))
    d = ImageDraw.Draw(img)
    _titulo_secao(d, MARGEM + 24, y + 22,
                  "Peças do Void: quantos personagens têm cada uma")
    n = len(semana["personagens"])
    for coluna, (nome_grupo, grupo, cor) in enumerate([
            ("EQUIPAMENTOS", h.EQUIPAMENTOS, ROXO),
            ("ACESSÓRIOS", h.ACESSORIOS, LILAS)]):
        x = MARGEM + 24 + coluna * (meia + VAO)
        _texto(d, (x, y + 52), nome_grupo, 11, APAGADO, "bold")
        for linha, (chave, rotulo) in enumerate(grupo):
            _barra_horizontal(d, x, y + 74 + linha * 30, meia - 48, rotulo,
                              pecas["por_peca"][chave], n, cor)
    y += altura_painel + VAO

    # --- desafios por tipo (semana em destaque) -----------------------
    altura_painel = 70 + 4 * 30 + 12
    img = _painel(img, (MARGEM, y, LARGURA - MARGEM, y + altura_painel))
    d = ImageDraw.Draw(img)
    _titulo_secao(d, MARGEM + 24, y + 22, "Desafios semanais: quantos "
                                          "personagens fizeram cada um")
    for i, (chave, rotulo) in enumerate(h.DESAFIOS):
        coluna, linha = i // 4, i % 4
        x = MARGEM + 24 + coluna * (meia + VAO)
        _barra_horizontal(d, x, y + 56 + linha * 30, meia - 48,
                          rotulo, desafios["por_desafio"][chave], n, AMARELO,
                          largura_rotulo=150)
    y += altura_painel + VAO

    # --- ataque total por personagem ------------------------------------
    # ate a semana em destaque (a mesma dos numeros do topo)
    evolucao = h.evolucao_personagens(todas[:indice + 1])
    por_coluna = (len(evolucao) + 1) // 2
    altura_linha = 34
    altura_painel = 66 + max(1, por_coluna) * altura_linha + 14
    img = _painel(img, (MARGEM, y, LARGURA - MARGEM, y + altura_painel))
    d = ImageDraw.Draw(img)
    _titulo_secao(d, MARGEM + 24, y + 22, "Ataque Total por personagem "
                                          "(e a variação na semana)")
    for i, (nome, serie, atual_poder, dif) in enumerate(evolucao):
        coluna, linha = i // max(1, por_coluna), i % max(1, por_coluna)
        x = MARGEM + 24 + coluna * (meia + VAO)
        ly = y + 58 + linha * altura_linha
        _texto(d, (x, ly + 12), f"{i + 1}.", 13, APAGADO, ancora="lm")
        _texto(d, (x + 30, ly + 12), nome, 15, TEXTO, "semi", ancora="lm")
        _sparkline(d, (x + 150, ly + 3, x + 230, ly + 21), serie, LILAS)
        _texto(d, (x + 330, ly + 12), numero(atual_poder), 15, TEXTO, "bold",
               ancora="rm")
        _texto(d, (x + meia - 48, ly + 12), diferenca_texto(dif) or "—", 13,
               _cor_da_diferenca(dif), "semi", ancora="rm")
    y += altura_painel + 16

    # --- rodape -----------------------------------------------------------
    d = ImageDraw.Draw(img)
    rodape = (f"Caminho da Maestria {versao}  ·  gerado em "
              f"{datetime.now():%d/%m/%Y %H:%M}")
    if parcial:
        rodape += "  ·  'atual' = semana em andamento (parcial)"
    _texto(d, (LARGURA / 2, y + 8), rodape, 12, APAGADO, ancora="mt")
    return img.crop((0, 0, LARGURA, y + 40))

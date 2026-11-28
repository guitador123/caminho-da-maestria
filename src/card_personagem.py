# -*- coding: utf-8 -*-
"""
Card de personagem da tela "Caminho da Maestria".

Desenhado direto no canvas principal (NÃO é um widget): a classe delega
create_text/create_image/... ao canvas pai aplicando a origem (x0, y0) e a
escala. Assim os 25 cards ficam no mesmo canvas e rolam junto com a tela.

Escala: 1.0 no tamanho de design (1152px) e até 1.6 no QHD (2560px).
"""

import os

import tkinter as tk
from PIL import Image, ImageDraw, ImageTk

from opcoes import normalizar
from registro import falha
from dados_app import (abreviar_ataque, formatar_percentual, soma_no_milhar,
                       ler_titulos, ler_cartas, estado_da_carta,
                       coluna_cartas, PECAS_COM_CARTAS, SLOTS_CARTAS,
                       coluna_pedra, ler_pedra, cor_da_pedra, status_forte)

# --------------------------------------------------------------------- cores
CORES = {
    "fundo": "#141221",
    "cartao": "#1b1930",
    "cartao_borda": "#2f2a48",
    "cabecalho": "#241f3d",
    "painel": "#232034",
    "painel_borda": "#2f2b47",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "fraco": "#6f688f",
    "roxo": "#a78bfa",
    "roxo_forte": "#8b5cf6",
    "verde": "#22c55e",
    "vermelho": "#f43f5e",
    "dourado": "#f5c451",
    "chip_verde": "#15803d",
    "chip_vermelho": "#b91c1c",
    "chip_violeta": "#6d28d9",
}

LARGURA = 340            # largura base (design 1152)
MARGEM = 16
ALTURA_CABECALHO = 150
# Area FIXA do retrato no cabecalho: assim o texto (eyebrow, titulo,
# credito) fica igual em TODOS os cards e o retrato nunca invade o badge
# do nome.
RETRATO_LARGURA = 112
RETRATO_TOPO = 46
ESCALA_MAX = 1.6         # no QHD (2560)
# onde comeca o nome das pecas do Void (antes dele: check + chip da pedra)
X_NOME_PECA = 61
# Altura do card no design (escala 1.0). O app usa isso para escolher a
# escala do card conforme a resolucao (para o card caber inteiro na tela).
ALTURA_CARD_BASE = 1014       # +64 da faixa de status (15.1)

PECAS_VOID = [
    ("arma", "Arma"), ("luvas", "Luvas"), ("cota", "Cota"), ("botas", "Botas"),
    ("capa", "Capa"), ("calca", "Cal\u00e7a"), ("elmo", "Elmo"),
    ("escudos", "Escudo"), ("asas", "Asas"), ("facas", "Facas"),
    ("mascara", "M\u00e1scara"), ("diadema", "Diadema"),
]

ACESSORIOS_CARD = [
    ("anel", "Anel"), ("tornozeleira", "Tornozeleira"),
    ("brinco", "Brinco"), ("piercing", "Piercing"),
    ("colar", "Colar"),                  # 15.5
]

# as 7 dungeons semanais (chaves NORMALIZADAS: "Void 4" -> "void4")
DUNGEONS = [
    ("void4", "Void 4"),
    ("altardarunha", "Altar da Ru\u00edna"),
    ("caminhoabissal", "Caminho Abissal"),
    ("fornalhainfernal", "Fornalha Infernal"),
    ("void123", "Void (1, 2 e 3)"),
    ("torredasilusoes", "Torre das Ilus\u00f5es"),
    ("terradojulgamento", "Terra do Julgamento"),
]

# metas da Torre das Ilusoes
TORRE_MAX = 30
LIBERTA_NUCLEOS_MAX = 9
LIBERTA_EPICOS_MAX = 4

# ------------------------------------------------------------------ cores ---
CORES_NOME = {
    "azul": "#60a5fa",
    "amarelo": "#fbbf24",
    "verde": "#4ade80",
    "roxo": "#c084fc",
    "vermelho": "#fb7185",
    "cinza": "#9ca3af",
}

# Cor do chip da pedra do Void pelo nivel (dados_app.cor_da_pedra):
# (fundo, texto)
CORES_PEDRA = {
    "vermelho": ("#e11d48", "#ffffff"),     # +18
    "dourado": ("#f5c451", "#241a05"),      # +17
    "verde": ("#16a34a", "#ffffff"),        # +11 a +16
    "cinza": ("#4b5563", "#e5e7eb"),        # +0 a +10
}

# Regras de cor dos acessórios (definidas pelo usuario em 14/11).
# A busca e por trecho do TEXTO (sem acento e minusculo) e a PRIMEIRA regra que
# casar vence -> as regras especificas vem antes das genericas.
REGRAS_ACESSORIOS = {
    "anel": [
        ("ciclo infinito", "vermelho"),
        ("promessa", "verde"),
        ("infinito iii", "verde"),
        ("infinito ii", "amarelo"),
        ("harkyon", "amarelo"),
        ("piu piu", "azul"),
    ],
    "brinco": [
        ("outro mundo do caos", "vermelho"),
        ("lendario", "roxo"),
        ("perfeita", "roxo"),
        ("epico", "amarelo"),
        ("completa", "amarelo"),
        ("raro", "azul"),
        ("enfraquecida", "azul"),
        ("harkyon", "azul"),
        ("piu piu", "azul"),
    ],
    "tornozeleira": [
        ("apocalipse", "vermelho"),
        ("escuridao", "roxo"),
        ("harmonia", "amarelo"),
        ("consolacao", "amarelo"),
        ("eternidade", "azul"),
    ],
}
# Colar (definido pelo usuario em 24/11)
REGRAS_ACESSORIOS["colar"] = [
    ("julgamento radiante", "azul"),
    ("outro", "cinza"),
]
# brinco e piercing seguem as mesmas regras
REGRAS_ACESSORIOS["piercing"] = REGRAS_ACESSORIOS["brinco"]


def coluna_banco_cartas(peca):
    """A chave das cartas da peca no dict "pecas" do card ("cartascota")."""
    return normalizar(coluna_cartas(peca))


def cor_do_acessorio(chave, valor):
    """Cor de destaque de um acessorio (pelas regras do usuario)."""
    if not valor:
        return None
    alvo = normalizar(valor)
    for trecho, cor in REGRAS_ACESSORIOS.get(chave, ()):
        if normalizar(trecho) in alvo:
            return CORES_NOME[cor]
    return None


# Retratos ATIVOS.
#   USAR_TODOS_OS_RETRATOS = True  -> usa todos os PNG da pasta
#   False -> libera um a um (durante a revisao visual), via RETRATOS_ATIVOS
USAR_TODOS_OS_RETRATOS = True
RETRATOS_ATIVOS = {
    "ai",
}


# Imagens do Tk COMPARTILHADAS entre os cards. Cada PhotoImage ocupa um
# bitmap do Windows (o limite e ~10.000 por programa): com 25 cards de
# dezenas de imagens cada, abrir a conta de outra pessoa na Guilda passava
# do limite e o Tk fechava o app ("Fail to allocate bitmap"). Quase tudo
# no card se repete (quadradinhos, chips, paineis, o fundo): a mesma
# imagem vira UM bitmap, reaproveitado por todos.
LIMITE_FOTOS_COMPARTILHADAS = 1500


def foto_compartilhada(widget, imagem):
    """A PhotoImage de `imagem` (PIL), a mesma para imagens iguais."""
    raiz = widget._root()
    cache = getattr(raiz, "_cache_fotos_card", None)
    if cache is None:
        cache = {}
        raiz._cache_fotos_card = cache
    chave = (imagem.mode, imagem.size, hash(imagem.tobytes()))
    foto = cache.get(chave)
    if foto is None:
        if len(cache) >= LIMITE_FOTOS_COMPARTILHADAS:
            # quem ainda usa uma imagem guarda a propria referencia
            cache.clear()
        foto = ImageTk.PhotoImage(imagem, master=widget)
        cache[chave] = foto
    return foto


# Cache dos retratos ja redimensionados (o resize com LANCZOS de 25 PNGs a
# cada redesenho era o que travava a tela quando o filtro mudava).
_CACHE_RETRATOS = {}


def retrato_pronto(caminho, largura, altura):
    """Retrato recortado e redimensionado (com cache)."""
    chave = (caminho, int(largura), int(altura))
    if chave in _CACHE_RETRATOS:
        return _CACHE_RETRATOS[chave]
    img = Image.open(caminho).convert("RGBA")
    # corta a borda transparente (a arte vem com muito vazio)
    try:
        caixa = img.getchannel("A").getbbox()
        if caixa:
            img = img.crop(caixa)
    except Exception:
        falha("recortar o retrato")
    escala = min(largura / img.width, altura / img.height)
    img = img.resize((max(1, int(img.width * escala)),
                      max(1, int(img.height * escala))), Image.LANCZOS)
    _CACHE_RETRATOS[chave] = img
    return img


def caminho_retrato(nome, pasta):
    """Arquivo do retrato do personagem (assets/personagens/<nome>.png).

    Se USAR_TODOS_OS_RETRATOS estiver ligado, devolve o arquivo de qualquer
    personagem que tenha PNG na pasta; senao, so os que estiverem em
    RETRATOS_ATIVOS.
    """
    if not nome or not pasta or not os.path.isdir(pasta):
        return None
    base = normalizar(nome)
    if not USAR_TODOS_OS_RETRATOS and base not in RETRATOS_ATIVOS:
        return None
    for arquivo in os.listdir(pasta):
        nome_arquivo, _ = os.path.splitext(arquivo)
        if normalizar(nome_arquivo) == base:
            return os.path.join(pasta, arquivo)
    return None


def _verdadeiro(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in ("verdadeiro", "true", "1", "t", "sim")


def _fracao(valor):
    """'13 / 13' -> (13, 13)."""
    if valor is None:
        return (0, 0)
    texto = str(valor).replace("/", " ").split()
    try:
        atual = int(texto[0])
        total = int(texto[1]) if len(texto) > 1 else 0
        return (atual, total)
    except (ValueError, IndexError):
        return (0, 0)


def _inteiro(valor, padrao=0):
    """'16 / 30' ou 16 -> 16."""
    if valor is None or valor == "":
        return padrao
    try:
        return int(float(str(valor).replace("/", " ").split()[0]))
    except (ValueError, IndexError):
        return padrao


class CardPersonagem:
    """Card de um personagem (como no mockup, no tema escuro do app)."""

    _contador = 0

    def __init__(self, canvas, x, y, dados, ao_abrir=None, pasta_retratos=None,
                 escala=1.0, ao_missao=None, ao_cartas=None):
        self.canvas = canvas
        self.x0 = x
        self.y0 = y
        self.s = escala
        self.dados = dados
        self.ao_abrir = ao_abrir
        # callback do modo "missao rapida": (chave_da_missao, nome)
        self.ao_missao = ao_missao
        # callback das cartas do Void (15.3): (nome, peca)
        self.ao_cartas = ao_cartas
        # o clique numa peca com cartas NAO abre a edicao do personagem
        # (o Tk chama os handlers de TODAS as tags do item)
        self._clique_tratado = False
        self.pasta_retratos = pasta_retratos
        self._fotos = {}
        self._fontes = {}
        # Tags EXCLUSIVAS deste card. Se a tag fosse compartilhada ("seta"),
        # o `tag_bind` do ultimo card desenhado atenderia a TODOS os cliques
        # (bug: clicar em editar em qualquer card abria o Zero).
        # O contador global evita colisao caso o `id()` seja reusado pelo GC.
        CardPersonagem._contador += 1
        self.tag = f"card_{CardPersonagem._contador}"
        self.tag_seta = f"seta_{CardPersonagem._contador}"
        # tag dos CHIPS de missao: criada DEPOIS da tag do card, entao tem
        # prioridade no canvas (o clique no chip nao abre a edicao)
        self.tag_missao = f"missao_{CardPersonagem._contador}"
        self.altura = self._calcular_altura()
        self._desenhar()
        self._ligar_clique()

    # ------------------------------------------------ mover / mostrar -----
    def mover_para(self, x, y):
        """Move o card (sem redesenhar) — usado quando o filtro muda."""
        dx = x - self.x0
        dy = y - self.y0
        if abs(dx) < 0.5 and abs(dy) < 0.5:
            return
        for item in getattr(self, "_itens", []):
            try:
                # move TODOS os pontos do item. Antes so o 1o par andava:
                # bastava para texto e imagem (1 ponto), mas o pontinho da
                # pedra (um oval, 2 cantos) esticava ate virar arcos
                # gigantes atravessando a tela
                self.canvas.move(item, dx, dy)
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("mover o card")
        self.x0 = x
        self.y0 = y

    def definir_visivel(self, visivel):
        """Mostra/esconde o card (sem redesenhar)."""
        estado = "normal" if visivel else "hidden"
        for item in getattr(self, "_itens", []):
            try:
                self.canvas.itemconfigure(item, state=estado)
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("mostrar/esconder o card")

    # ------------------------------------------------- clique no card todo --
    def _ligar_clique(self):
        """Clique em QUALQUER parte do card abre a edicao do personagem.

        A tag do card e exclusiva (um por card), entao o binding so vale
        para os itens deste card — os outros 24 cards nao sao afetados.
        """
        if not self.ao_abrir:
            return
        self.canvas.tag_bind(self.tag, "<Button-1>",
                             lambda e, c=self: c._clicar_card())
        self.canvas.tag_bind(self.tag, "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind(self.tag, "<Leave>",
                             lambda e: self.canvas.configure(cursor=""))
        # cada missao tem a sua tag (para saber qual foi clicada)
        for chave, _rotulo in DUNGEONS:
            tag = f"{self.tag_missao}_{chave}"
            self.canvas.tag_bind(
                tag, "<Button-1>",
                lambda e, c=chave, n=self.dados.get("nome"): self._clicar_missao(c, n))
            self.canvas.tag_bind(tag, "<Enter>",
                                 lambda e: self.canvas.configure(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>",
                                 lambda e: self.canvas.configure(cursor=""))

    def _clicar_card(self):
        if self._clique_tratado:
            self._clique_tratado = False
            return
        self.ao_abrir(self.dados)

    def _clicar_cartas(self, peca):
        """Clique na linha de uma peca do Void: abre a edicao rapida das
        cartas dela (e nao a do personagem)."""
        self._clique_tratado = True
        if self.ao_cartas:
            self.ao_cartas(self.dados.get("nome"), peca)

    def _clicar_missao(self, chave, nome):
        """Clique num chip de missao (so age se o app estiver no modo)."""
        if self.ao_missao:
            self.ao_missao(chave, nome)

    # ---------------------------------------------- desenho no canvas pai --
    def _tag(self, kw):
        """Garante que o item pertenca ao card (tag exclusiva)."""
        tags = tuple(kw.get("tags", ()))
        if self.tag not in tags:
            kw["tags"] = tags + (self.tag,)
        return kw

    def create_text(self, x, y, **kw):
        """Cria um texto no canvas do card.

        ⚠ A fonte NAO e escalada aqui: quem chama ja passa a fonte JA
        escalada (`self.f(...)`). Escalar de novo fazia o texto crescer
        duas vezes (quadrado da escala) -> em telas grandes o texto invadia
        o vizinho e o card ficava ilegivel.
        """
        return self.canvas.create_text(self.x0 + x * self.s, self.y0 + y * self.s,
                                       **self._tag(kw))

    def create_image(self, x, y, **kw):
        return self.canvas.create_image(self.x0 + x * self.s, self.y0 + y * self.s,
                                        **self._tag(kw))

    def create_oval(self, x1, y1, x2, y2, **kw):
        return self.canvas.create_oval(self.x0 + x1 * self.s, self.y0 + y1 * self.s,
                                       self.x0 + x2 * self.s, self.y0 + y2 * self.s,
                                       **self._tag(kw))

    def create_rectangle(self, x1, y1, x2, y2, **kw):
        return self.canvas.create_rectangle(self.x0 + x1 * self.s,
                                            self.y0 + y1 * self.s,
                                            self.x0 + x2 * self.s,
                                            self.y0 + y2 * self.s, **self._tag(kw))

    # ------------------------------------------------------------ helpers --
    def _escala_fonte(self, fonte):
        return (fonte[0], max(1, int(round(fonte[1] * self.s))), fonte[2])

    def f(self, tamanho, peso="normal", familia="Segoe UI"):
        """Fonte ja escalada."""
        return (familia, max(1, int(round(tamanho * self.s))), peso)

    def _img(self, chave, imagem):
        foto = foto_compartilhada(self.canvas, imagem)
        self._fotos[chave] = foto
        return foto

    def _painel(self, cor, largura, altura, raio=12, borda=None, largura_borda=1):
        return _painel(cor, largura * self.s, altura * self.s,
                       radius=raio * self.s, borda=borda,
                       largura_borda=largura_borda)

    def _cabecalho_img(self, cor, largura, altura, raio=14, borda=None):
        return _cabecalho(cor, largura * self.s, altura * self.s,
                           radius=raio * self.s, borda=borda)

    def _fonte_obj(self, fonte):
        if fonte not in self._fontes:
            from tkinter import font as tkfont
            self._fontes[fonte] = tkfont.Font(family=fonte[0], size=fonte[1],
                                              weight=fonte[2])
        return self._fontes[fonte]

    def _largura_texto(self, texto, tamanho=10, peso="bold"):
        return self._fonte_obj(self.f(tamanho, peso)).measure(texto)

    def _texto_contorno(self, x, y, texto, cor_contorno, tamanho=10,
                        peso="bold", anchor="nw", cor_texto=None,
                        familia="Segoe UI", tags=()):
        """Texto com contorno (stroke) na cor — para ficar legivel no fundo."""
        fonte = self.f(tamanho, peso, familia)
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1),
                        (-1, -1), (1, -1), (-1, 1), (1, 1)):
            self.create_text(x + dx, y + dy, text=texto,
                             font=fonte, fill=cor_contorno, anchor=anchor,
                             tags=tags)
        return self.create_text(x, y, text=texto, font=fonte,
                                fill=cor_texto or CORES["texto"], anchor=anchor,
                                tags=tags)

    def _texto(self, x, y, texto, tamanho, cor=None, peso="normal", anchor="nw",
               familia="Segoe UI", espaco=None, largura_max=None):
        if espaco is None:
            return self.create_text(x, y, text=texto, font=self.f(tamanho, peso,
                                                                    familia),
                                    fill=cor or CORES["texto"], anchor=anchor)
        # texto com espacamento entre letras (o Tk nao tem tracking)
        fonte = self.f(tamanho, peso, familia)
        medida = self._fonte_obj(fonte)
        caracteres = list(texto)
        if largura_max is not None:
            # corta (com reticencias) para nao invadir o que esta a direita
            while caracteres and self._largura_espacada(caracteres, medida,
                                                        espaco) > largura_max:
                caracteres.pop()
            if caracteres and len(caracteres) < len(texto):
                caracteres = caracteres[:-1] + ["\u2026"]
        cursor = x
        for caractere in caracteres:
            self.create_text(cursor, y, text=caractere, font=fonte,
                             fill=cor or CORES["texto"], anchor=anchor)
            cursor += medida.measure(caractere) / self.s + espaco
        return cursor

    def _largura_espacada(self, caracteres, medida, espaco):
        """Largura do texto espacado, em unidades de DESIGN."""
        if not caracteres:
            return 0
        total = sum(medida.measure(c) for c in caracteres) / self.s
        return total + espaco * (len(caracteres) - 1)

    def _chip(self, x, y, texto, cor_fundo, cor_texto, tamanho=11, padding=8,
              altura=22, radius=11, cor_borda=None, largura_max=None, tags=()):
        """Chip de texto (trunca com reticencias se nao couber em largura_max)."""
        if largura_max:
            # largura_max = largura DISPONIVEL em unidades de DESIGN
            disponivel = (largura_max - padding * 2) * self.s
            medida = self._fonte_obj(self.f(tamanho, "bold"))
            # so coloca reticencia se o texto NAO couber (antes colocava
            # sempre -> "Origem do Caos" virava "Origem do Caos...")
            if medida.measure(texto) > disponivel:
                while texto and medida.measure(texto + "…") > disponivel:
                    texto = texto[:-1]
                if texto:
                    texto += "…"
        largura = self._largura_design(texto, tamanho) + padding * 2
        img = self._img(f"chip_{texto}_{x}_{y}",
                        self._painel(cor_fundo, largura, altura, raio=radius,
                                     borda=cor_borda))
        self.create_image(x, y, anchor="nw", image=img, tags=tags)
        self.create_text(x + largura / 2, y + altura / 2, text=texto,
                         font=self.f(tamanho, "bold"), fill=cor_texto,
                         anchor="center", tags=tags)
        return largura

    # ------------------------------------------------- metricas e medidas --
    def _alt(self, tamanho, peso="normal"):
        """Altura da linha da fonte, em unidades de DESIGN.

        Mede a fonte de verdade (o Tk leva em conta o DPI da tela): assim o
        layout acompanha o texto em QUALQUER escala e em QUALQUER monitor
        (sem texto por cima de texto).
        """
        chave = (tamanho, peso)
        alturas = getattr(self, "_alturas", None)
        if alturas is None:
            alturas = {}
            self._alturas = alturas
        if chave not in alturas:
            alturas[chave] = (self._fonte_obj(self.f(tamanho, peso))
                              .metrics("linespace") / self.s)
        return alturas[chave]

    def _largura_design(self, texto, tamanho=10, peso="bold"):
        """Largura do texto em unidades de DESIGN (nao em px reais)."""
        return self._largura_texto(texto, tamanho, peso) / self.s

    def _cortar(self, texto, tamanho, peso, largura_max):
        """Corta o texto (com reticencias) para caber na largura (px reais)."""
        medida = self._fonte_obj(self.f(tamanho, peso))
        if medida.measure(texto) <= largura_max:
            return texto
        while texto and medida.measure(texto + "\u2026") > largura_max:
            texto = texto[:-1]
        return (texto + "\u2026") if texto else ""

    # ------------------------------------------------------- calculo altura -
    def _layout(self):
        """Geometria do card em unidades de DESIGN.

        Mesma fonte de verdade do desenho: o card nunca "desanda" e a altura
        final bate com o que foi desenhado.
        """
        alt = self._alt
        L = {}

        # --- cabecalho ---
        L["badge_y"] = 14
        L["badge_h"] = max(alt(17, "bold"), 26)
        L["eyebrow_y"] = L["badge_y"] + L["badge_h"] + 13
        L["titulo_y"] = L["eyebrow_y"] + alt(9, "bold") + 5
        L["titulo_h"] = max(alt(12) + 3, 24)
        L["credito_y"] = L["titulo_y"] + L["titulo_h"] + 14
        # + a area do retrato (que fica abaixo do badge do nome)
        L["alt_cabecalho"] = L["credito_y"] + alt(9) + 33

        # --- faixa de status (15.1), logo abaixo do cabecalho ---
        L["status_y"] = L["alt_cabecalho"] + 12
        L["status_rotulo_h"] = alt(8)
        L["status_valor_h"] = alt(13, "bold")
        L["status_h"] = 8 + L["status_rotulo_h"] + L["status_valor_h"] + 8

        # --- progresso ---
        L["prog_titulo_y"] = L["status_y"] + L["status_h"] + 14
        L["painel_y"] = L["prog_titulo_y"] + alt(12, "bold") + 8
        L["stat_rotulo_h"] = alt(8)
        L["stat_valor_h"] = alt(15, "bold")
        L["stat_h"] = L["stat_rotulo_h"] + L["stat_valor_h"]
        L["painel_h"] = 16 + L["stat_h"] + 6 + L["stat_h"] + 12
        L["prog_fim_y"] = L["painel_y"] + L["painel_h"] + 14

        # --- dungeons ---
        L["dung_titulo_y"] = L["prog_fim_y"]
        L["barra_y"] = L["dung_titulo_y"] + alt(13) + 6
        L["barra_h"] = 9
        L["chips_y"] = L["barra_y"] + L["barra_h"] + 12
        L["chip_h"] = max(alt(10, "bold") + 6, 20)
        L["chip_passo"] = L["chip_h"] + 6
        x = MARGEM
        linhas = 1
        for _chave, rotulo in DUNGEONS:
            largura = self._largura_design(rotulo, 10) + 14
            if x + largura > LARGURA - MARGEM:
                x = MARGEM
                linhas += 1
            x += largura + 6
        L["chip_linhas"] = linhas
        L["dung_fim_y"] = (L["chips_y"] + (linhas - 1) * L["chip_passo"]
                           + L["chip_h"] + 12)

        # --- blocos (despertar / liberacao) ---
        L["bloco_h"] = 12 + alt(12, "bold") + 2 + alt(12, "bold") + 12
        L["bloco_titulo_y"] = 12
        L["bloco_texto_y"] = 12 + alt(12, "bold") + 2
        L["blocos_fim_y"] = (L["dung_fim_y"] + L["bloco_h"] + 10
                             + L["bloco_h"] + 12)

        # --- equipamentos ---
        L["eq_titulo_y"] = 10
        L["eq_sub_y"] = 10 + alt(11, "bold") + 2
        L["eq_pecas_y"] = L["eq_sub_y"] + alt(11, "bold") + 6
        L["peca_passo"] = max(alt(9), alt(10, "bold"))
        L["eq_pecas_h"] = (L["eq_pecas_y"] + len(PECAS_VOID) * L["peca_passo"]
                           + 10)
        L["acc_rotulo_y"] = 30
        L["acc_rotulo_h"] = alt(9)
        L["acc_valor_h"] = 2 * alt(9, "bold") + 8
        L["eq_acess_h"] = 30
        acessorios = self.dados.get("acessorios") or {}
        for chave, _rotulo in ACESSORIOS_CARD:
            valor = acessorios.get(chave) or ""
            L["eq_acess_h"] += L["acc_rotulo_h"]
            L["eq_acess_h"] += L["acc_valor_h"] if valor else 8
        L["eq_acess_h"] += 8             # o ultimo nao encosta na borda
        L["eq_h"] = max(L["eq_pecas_h"], L["eq_acess_h"])

        # --- rodape ---
        L["eq_y"] = L["blocos_fim_y"]
        L["rodape_y"] = L["eq_y"] + L["eq_h"] + 12
        L["alt_total"] = L["rodape_y"] + 24 + MARGEM
        return L

    def _calcular_altura(self):
        """Altura final do card (em px reais)."""
        return int(self._layout()["alt_total"] * self.s)

    # ------------------------------------------------------------ desenho --
    def _desenhar(self):
        antes = set(self.canvas.find_all())
        self._fotos.clear()

        # fundo do card
        self.create_image(0, 0, anchor="nw", image=self._img(
            "cartao", self._painel(CORES["cartao"], LARGURA,
                                    self.altura / self.s, raio=14,
                                    borda=CORES["cartao_borda"])))

        self._desenhar_cabecalho()
        self._desenhar_status()
        self._desenhar_progresso()
        self._desenhar_dungeons()
        self._desenhar_blocos()
        self._desenhar_equipamentos()
        self._itens = [i for i in self.canvas.find_all() if i not in antes]

    def atualizar(self, dados=None):
        """Redesenha o card (edicao ao vivo)."""
        self._esconder_titulos()
        if dados is not None:
            self.dados = dados
        # a altura depende dos dados (ex.: um acessorio a mais ocupa mais
        # linhas): sem recalcular, o fundo ficava com a altura antiga e o
        # rodape (Libertacao e a seta) saia para fora do card. Quem chama
        # reposiciona a grade pela altura nova (_reordenar_cards)
        self.altura = self._calcular_altura()
        for item in getattr(self, "_itens", []):
            try:
                self.canvas.delete(item)
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("apagar itens do card")
        self._itens = []
        self._desenhar()

    # --------------------------------------------------------- cabecalho --
    def _desenhar_cabecalho(self):
        dados = self.dados
        lay = self._layout()
        altura = lay["alt_cabecalho"]
        self.create_image(0, 0, anchor="nw", image=self._img(
            "cabecalho", self._cabecalho_img(CORES["cabecalho"], LARGURA, altura,
                                              borda=CORES["cartao_borda"])))

        # retrato (direita) ou placeholder
        self._largura_retrato = 0
        retrato = caminho_retrato(dados.get("nome"), self.pasta_retratos or "")
        if retrato and os.path.exists(retrato):
            try:
                # cabe na AREA FIXA do retrato (mesma para todos)
                img = retrato_pronto(
                    retrato,
                    RETRATO_LARGURA * self.s,
                    (altura - RETRATO_TOPO - 2) * self.s)
                # largura do retrato em unidades de DESIGN
                self._largura_retrato = img.width / self.s
                self.create_image(LARGURA - 2, altura - 2, anchor="se",
                                  image=self._img("retrato", img))
            except Exception:
                falha("desenhar o retrato do card")
        else:
            inicial = (dados.get("nome") or "?")[0].upper()
            self.create_oval(LARGURA - 62, 54, LARGURA - 14, 102,
                             fill=CORES["painel"], outline=CORES["painel_borda"])
            self.create_text(LARGURA - 38, 77, text=inicial,
                             font=self.f(22, "bold"), fill=CORES["fraco"],
                             anchor="center")

        # badge de poder
        poder = dados.get("poder") or 0
        texto_poder = f"{poder:,}".replace(",", ".")
        largura_poder = self._chip(MARGEM, lay["badge_y"], "\u26a1 " + texto_poder,
                                   CORES["painel"], CORES["texto"], tamanho=12,
                                   altura=lay["badge_h"],
                                   radius=lay["badge_h"] / 2)

        # soma Ataque + Ataque Especial "no milhar" (15.1): so aparece
        # quando ha ataque preenchido
        if _inteiro(dados.get("ataque")) + _inteiro(dados.get("ataque_especial")):
            soma = soma_no_milhar(dados.get("ataque"),
                                  dados.get("ataque_especial"))
            self._chip(MARGEM + largura_poder + 6, lay["badge_y"], soma,
                       CORES["chip_violeta"], "#ffffff", tamanho=12,
                       altura=lay["badge_h"], radius=lay["badge_h"] / 2)

        # badge do nome
        nome = dados.get("nome") or "?"
        # em unidades de DESIGN (antes era em px reais e a escala era
        # aplicada de novo: o badge crescia demais em telas grandes)
        largura_nome = self._largura_design(nome, 17)
        self.create_image(LARGURA - MARGEM - largura_nome - 20, lay["badge_y"],
                          anchor="nw",
                          image=self._img(
                              f"nome_{nome}",
                              self._painel("#e9e6f4", largura_nome + 20,
                                           lay["badge_h"], raio=lay["badge_h"] / 2)))
        self.create_text(LARGURA - MARGEM - largura_nome / 2 - 10,
                         lay["badge_y"] + lay["badge_h"] / 2, text=nome,
                         font=self.f(17, "bold"), fill="#1b1730", anchor="center")

        # eyebrow (compacto: nao pode invadir o retrato a direita)
        # a area do retrato e FIXA -> o texto fica igual em todos os cards
        largura_livre = (LARGURA - RETRATO_LARGURA - MARGEM - 8
                         if self._largura_retrato else LARGURA - MARGEM * 2)
        self._texto(MARGEM, lay["eyebrow_y"], "PERSONAGEM DE GRAND CHASE", 9,
                    cor=CORES["fraco"], peso="normal", espaco=1.0,
                    largura_max=largura_livre)

        # titulos (15.2): o mais forte no chip dourado; os outros viram
        # um "+N" ao lado, e passar o mouse nele mostra a lista inteira
        titulos = ler_titulos(dados.get("titulo"))
        if titulos:
            # nao pode invadir o retrato a direita
            largura_max = (LARGURA - RETRATO_LARGURA - MARGEM - 8
                           if self._largura_retrato else LARGURA - MARGEM * 2)
            mais = f"+{len(titulos) - 1}" if len(titulos) > 1 else ""
            largura_mais = (self._largura_design(mais, 11) + 14) if mais else 0
            tag_titulos = f"{self.tag}_titulos"
            largura = self._chip(
                MARGEM, lay["titulo_y"], titulos[0], CORES["dourado"],
                "#241a05", tamanho=11, altura=lay["titulo_h"],
                radius=lay["titulo_h"] / 2,
                largura_max=largura_max - (largura_mais + 6 if mais else 0),
                tags=(tag_titulos,))
            if mais:
                self._chip(MARGEM + largura + 6, lay["titulo_y"], mais,
                           CORES["painel"], CORES["dourado"], tamanho=11,
                           padding=7, altura=lay["titulo_h"],
                           radius=lay["titulo_h"] / 2,
                           cor_borda=CORES["dourado"], tags=(tag_titulos,))
            # a lista aparece passando o mouse em qualquer um dos dois chips
            self._titulos = titulos
            self.canvas.tag_bind(tag_titulos, "<Enter>",
                                 lambda e: self._mostrar_titulos())
            self.canvas.tag_bind(tag_titulos, "<Leave>",
                                 lambda e: self._esconder_titulos())

        # credito
        self._texto(MARGEM, lay["credito_y"], "Arte via Grand Chase Wiki", 9,
                    cor=CORES["fraco"])

    # ---------------------------------------------------- lista de titulos --
    def _mostrar_titulos(self):
        """Balao com TODOS os titulos (o mais forte em dourado), logo abaixo
        do chip. Fica por cima dos outros itens do canvas."""
        titulos = getattr(self, "_titulos", [])
        if not titulos:
            return
        lay = self._layout()
        self._mostrar_balao(MARGEM, lay["titulo_y"] + lay["titulo_h"] + 4,
                            f"T\u00cdTULOS ({len(titulos)})", titulos)

    def _mostrar_balao(self, x, y, cabecalho, linhas, borda=None):
        """Balao (em unidades de DESIGN, a partir de x, y) com um cabecalho
        pequeno e as linhas (a 1a em dourado). Fica por cima de tudo e nao
        passa da borda direita do card."""
        self._esconder_titulos()
        tag = f"{self.tag}_balao"
        passo = self._alt(10, "bold") + 3
        alto_cabecalho = self._alt(8) + 6
        largura = max(self._largura_design(t, 10) for t in linhas) + 24
        largura = min(max(largura, 120), LARGURA - MARGEM * 2)
        x = min(x, LARGURA - MARGEM - largura)
        altura = 10 + alto_cabecalho + passo * len(linhas) + 6
        self._fotos["balao"] = ImageTk.PhotoImage(
            self._painel("#1b1930", largura, altura, raio=8,
                         borda=borda or CORES["dourado"]))
        self.canvas.create_image(self.x0 + x * self.s, self.y0 + y * self.s,
                                 anchor="nw", tags=(tag,),
                                 image=self._fotos["balao"])
        self.canvas.create_text(self.x0 + (x + 12) * self.s,
                                self.y0 + (y + 8) * self.s, text=cabecalho,
                                font=self.f(8), fill=CORES["suave"],
                                anchor="nw", tags=(tag,))
        for indice, linha in enumerate(linhas):
            texto = self._cortar(linha, 10, "bold", (largura - 24) * self.s)
            self.canvas.create_text(
                self.x0 + (x + 12) * self.s,
                self.y0 + (y + 8 + alto_cabecalho + indice * passo) * self.s,
                text=texto, font=self.f(10, "bold"),
                fill=CORES["dourado"] if indice == 0 else CORES["texto"],
                anchor="nw", tags=(tag,))
        self.canvas.tag_raise(tag)

    def _esconder_titulos(self):
        try:
            self.canvas.delete(f"{self.tag}_balao")
        except tk.TclError:
            pass                          # janela ja fechada

    # ------------------------------------------------------------ status --
    def _desenhar_status(self):
        """Faixa com os 5 status (15.1): ATQ, ESP, CRIT, D.CRIT, COSTAS."""
        dados = self.dados
        lay = self._layout()
        y = lay["status_y"]
        largura = LARGURA - MARGEM * 2
        self.create_image(MARGEM, y, anchor="nw", image=self._img(
            "painel_status", self._painel(CORES["painel"], largura,
                                          lay["status_h"],
                                          borda=CORES["painel_borda"])))
        itens = [
            ("ATQ", abreviar_ataque(dados.get("ataque"))),
            ("ESP", abreviar_ataque(dados.get("ataque_especial"))),
            ("CRIT", formatar_percentual(dados.get("critico"))),
            ("D.CRIT", formatar_percentual(dados.get("dano_critico"))),
            ("COSTAS", formatar_percentual(dados.get("dano_costas"))),
        ]
        coluna = (largura - 8) / len(itens)
        for indice, (rotulo, valor) in enumerate(itens):
            cx = MARGEM + 4 + coluna * (indice + 0.5)
            self.create_text(cx, y + 8, text=rotulo, font=self.f(8),
                             fill=CORES["suave"], anchor="n")
            # "1250,75%" nao cabe em 13: a fonte encolhe ate caber
            tamanho = 13
            while (tamanho > 9 and self._largura_texto(valor, tamanho)
                   > (coluna - 4) * self.s):
                tamanho -= 1
            self.create_text(cx, y + 8 + lay["status_rotulo_h"], text=valor,
                             font=self.f(tamanho, "bold"),
                             fill=CORES["texto"], anchor="n")

    # --------------------------------------------------------- progresso --
    def _desenhar_progresso(self):
        dados = self.dados
        lay = self._layout()
        y = lay["prog_titulo_y"]
        self._texto(MARGEM, y, "PROGRESSO DO PERSONAGEM", 12, cor=CORES["roxo"],
                    peso="bold", espaco=1.4)

        y = lay["painel_y"]
        self.create_image(MARGEM, y, anchor="nw", image=self._img(
            "painel_stats", self._painel(CORES["painel"], LARGURA - MARGEM * 2,
                                         lay["painel_h"],
                                         borda=CORES["painel_borda"])))

        andar = _inteiro(dados.get("torre"))
        linha1 = [
            ("TORRE", f"{andar} / {TORRE_MAX}"),
            ("VOID UNIFICADO", str(dados.get("vazio_uni", 0))),
            ("VOID APOCALIPSE", str(dados.get("vazio_apo", 0))),
        ]
        linha2 = [
            ("N\u00facleos Dimensionais", str(dados.get("nucleos_dimensionais", 0))),
            ("Fragmento do Vazio Disperso",
             str(dados.get("fragmento_vazio_disperso", 0))),
        ]
        largura_util = LARGURA - MARGEM * 2 - 14

        def _linha(estatisticas, py, colunas):
            """Cada coluna fica com a largura do seu rotulo (+ a sobra)."""
            larguras = [self._largura_texto(rotulo, 8) / self.s
                        for rotulo, _v in estatisticas]
            sobra = max(largura_util - sum(larguras), 0) / max(colunas, 1)
            x = MARGEM + 10
            for indice, (rotulo, valor) in enumerate(estatisticas):
                largura_col = larguras[indice] + sobra
                cx = x + largura_col / 2
                # o rotulo nunca invade o vizinho
                rotulo = self._cortar(rotulo, 8, "normal", largura_col * self.s)
                self.create_text(cx, py, text=rotulo, font=self.f(8),
                                 fill=CORES["suave"], anchor="n")
                self.create_text(cx, py + lay["stat_rotulo_h"], text=valor,
                                 font=self.f(15, "bold"),
                                 fill=CORES["texto"], anchor="n")
                x += largura_col

        _linha(linha1, y + 16, 3)
        _linha(linha2, y + 16 + lay["stat_h"] + 6, 2)

    # --------------------------------------------------------- dungeons --
    def _desenhar_dungeons(self):
        dados = self.dados
        lay = self._layout()
        semanais = dados.get("semanais") or {}
        feitos = [chave for chave, _ in DUNGEONS
                  if _verdadeiro(semanais.get(chave))]
        total = len(DUNGEONS)

        y = lay["dung_titulo_y"]
        self.create_text(MARGEM, y, text="Dungeons semanais", font=self.f(13),
                         fill=CORES["suave"], anchor="nw")
        self.create_text(LARGURA - MARGEM, y, text=f"{len(feitos)}/{total}",
                         font=self.f(13, "bold"), fill=CORES["roxo"], anchor="ne")

        y = lay["barra_y"]
        largura = LARGURA - MARGEM * 2
        self.create_image(MARGEM, y, anchor="nw", image=self._img(
            "trilha", self._painel("#2c2745", largura, lay["barra_h"], raio=5)))
        if total:
            preenchimento = max(lay["barra_h"],
                                int(largura * len(feitos) / total))
            self.create_image(MARGEM, y, anchor="nw", image=self._img(
                "preenchimento", self._painel(CORES["roxo_forte"], preenchimento,
                                             lay["barra_h"], raio=5)))

        y = lay["chips_y"]
        x = MARGEM
        for chave, rotulo in DUNGEONS:
            feito = _verdadeiro(semanais.get(chave))
            cor = CORES["chip_verde"] if feito else CORES["chip_vermelho"]
            largura_chip = self._largura_design(rotulo, 10) + 14
            if x + largura_chip > LARGURA - MARGEM:
                x = MARGEM
                y += lay["chip_passo"]
            tag_missao = f"{self.tag_missao}_{chave}"
            self.create_image(x, y, anchor="nw", image=self._img(
                f"dungeon_{chave}", self._painel(cor, largura_chip,
                                                 lay["chip_h"], raio=10)),
                tags=(tag_missao,))
            # o texto recebe contorno na cor da missao (verde = concluida)
            contorno = "#4ade80" if feito else "#fca5a5"
            self._texto_contorno(x + largura_chip / 2, y + lay["chip_h"] / 2,
                                 rotulo, contorno, tamanho=10, anchor="center",
                                 cor_texto="#ffffff", tags=(tag_missao,))
            x += largura_chip + 6

    # ------------------------------------------------------------ blocos --
    def _desenhar_blocos(self):
        dados = self.dados
        lay = self._layout()

        nucleo = _fracao(dados.get("nucleo"))
        epicos = _fracao(dados.get("nucleos_epicos"))
        y = lay["dung_fim_y"]
        self._bloco(y, "DESPERTAR",
                    f"N\u00facleos: {nucleo[0]}/{nucleo[1]} \u00b7 "
                    f"\u00c9picos+: {epicos[0]}/{epicos[1]}",
                    completo=(nucleo[1] > 0 and nucleo[0] >= nucleo[1] and
                              epicos[1] > 0 and epicos[0] >= epicos[1]))
        y += lay["bloco_h"] + 10

        lib_nucleos = dados.get("libertacao_nucleos", 0)
        lib_epicos = dados.get("libertacao_epicos", 0)
        self._bloco(y, "LIBERTA\u00c7\u00c3O",
                    f"N\u00facleos: {lib_nucleos}/{LIBERTA_NUCLEOS_MAX} \u00b7 "
                    f"\u00c9picos+: {lib_epicos}/{LIBERTA_EPICOS_MAX}",
                    completo=(lib_nucleos >= LIBERTA_NUCLEOS_MAX and
                              lib_epicos >= LIBERTA_EPICOS_MAX))

    def _bloco(self, y, titulo, texto, completo):
        lay = self._layout()
        if completo:
            fundo, borda, cor = "#143d2a", "#1f7a4d", "#7ef0b0"
        else:
            fundo, borda, cor = "#4a1028", "#8a1c3c", "#ff9ab5"
        self.create_image(MARGEM, y, anchor="nw", image=self._img(
            f"bloco_{titulo}", self._painel(fundo, LARGURA - MARGEM * 2,
                                            lay["bloco_h"], borda=borda)))
        self.create_text(MARGEM + 14, y + lay["bloco_titulo_y"],
                         text="\u2691", font=self.f(12, "bold"),
                         fill=cor, anchor="nw")
        self.create_text(MARGEM + 34, y + lay["bloco_titulo_y"], text=titulo,
                         font=self.f(12, "bold"), fill=cor, anchor="nw")
        self.create_text(MARGEM + 14, y + lay["bloco_texto_y"], text=texto,
                         font=self.f(12, "bold"), fill=CORES["texto"], anchor="nw")

    # ------------------------------------------------------- equipamentos --
    def _desenhar_equipamentos(self):
        dados = self.dados
        lay = self._layout()
        pecas = dados.get("pecas") or {}
        acessorios = dados.get("acessorios") or {}

        largura_esq = 164
        largura_dir = LARGURA - MARGEM * 2 - largura_esq - 10
        altura = lay["eq_h"]
        y = lay["eq_y"]

        # --- equipamentos void ---
        x = MARGEM
        self.create_image(x, y, anchor="nw", image=self._img(
            "painel_pecas", self._painel(CORES["painel"], largura_esq, altura,
                                          borda=CORES["painel_borda"])))
        self.create_text(x + 14, y + lay["eq_titulo_y"], text="\U0001F6E1",
                         font=self.f(11, "bold"), fill=CORES["roxo"], anchor="nw")
        self.create_text(x + 38, y + lay["eq_titulo_y"], text="EQUIPAMENTOS",
                         font=self.f(11, "bold"), fill=CORES["suave"], anchor="nw")
        self.create_text(x + 38, y + lay["eq_sub_y"], text="VOID",
                         font=self.f(11, "bold"), fill=CORES["suave"], anchor="nw")
        completos = sum(1 for chave, _ in PECAS_VOID if _verdadeiro(pecas.get(chave)))
        self.create_text(x + largura_esq - 14, y + lay["eq_sub_y"],
                         text=f"{completos}/{len(PECAS_VOID)} pe\u00e7as",
                         font=self.f(10), fill=CORES["fraco"], anchor="ne")
        for indice, (chave, rotulo) in enumerate(PECAS_VOID):
            ok = _verdadeiro(pecas.get(chave))
            py = y + lay["eq_pecas_y"] + indice * lay["peca_passo"]
            # tem -> check verde | nao tem -> X vermelho
            self.create_text(x + 14, py, text="\u2713" if ok else "\u2717",
                             font=self.f(10, "bold"),
                             fill=CORES["verde"] if ok else "#fb7185",
                             anchor="nw")
            self.create_text(x + X_NOME_PECA, py, text=rotulo, font=self.f(9),
                             fill=CORES["texto"] if ok else CORES["fraco"],
                             anchor="nw")
            if chave in PECAS_COM_CARTAS:
                self._desenhar_cartas(chave, x, py, largura_esq,
                                      lay["peca_passo"], pecas)

        # --- acessorios ---
        x2 = x + largura_esq + 10
        self.create_image(x2, y, anchor="nw", image=self._img(
            "painel_acess", self._painel(CORES["painel"], largura_dir, altura,
                                          borda=CORES["painel_borda"])))
        self.create_text(x2 + 12, y + lay["eq_titulo_y"], text="\U0001F48D",
                         font=self.f(11, "bold"), fill=CORES["roxo"], anchor="nw")
        self.create_text(x2 + 36, y + lay["eq_titulo_y"], text="ACESS\u00d3RIOS",
                         font=self.f(11, "bold"), fill=CORES["suave"], anchor="nw")
        ay = y + lay["acc_rotulo_y"]
        for chave, rotulo in ACESSORIOS_CARD:
            valor = acessorios.get(chave) or ""
            self.create_text(x2 + 12, ay, text=rotulo, font=self.f(9),
                             fill=CORES["fraco"], anchor="nw")
            ay += lay["acc_rotulo_h"]
            if valor:
                self._valor_acessorio(x2 + 12, ay, valor, largura_dir - 24,
                                      cor=cor_do_acessorio(chave, valor))
                ay += lay["acc_valor_h"]
            else:
                ay += 8

        # --- rodape ---
        y = lay["rodape_y"]
        libertacao = dados.get("libertacao") or ""
        self.create_text(MARGEM, y, text="Liberta\u00e7\u00e3o:", font=self.f(11),
                         fill=CORES["suave"], anchor="nw")
        largura_rotulo = self._largura_texto("Liberta\u00e7\u00e3o:", 11, "normal")
        self.create_text(MARGEM + largura_rotulo + 6, y, text=libertacao or "-",
                         font=self.f(11, "bold"), fill=CORES["texto"], anchor="nw")

        tamanho = 30
        bx = LARGURA - MARGEM - tamanho
        by = y - 7
        self.create_image(bx, by, anchor="nw", image=self._img(
            "seta", self._painel(CORES["painel"], tamanho, tamanho, raio=10,
                                 borda=CORES["painel_borda"])),
            tags=(self.tag, self.tag_seta))
        self.create_text(bx + tamanho / 2, by + tamanho / 2, text="\u2192",
                         font=self.f(15, "bold"), fill=CORES["roxo"], anchor="center",
                         tags=(self.tag, self.tag_seta))
        if self.ao_abrir:
            self.canvas.tag_bind(self.tag_seta, "<Button-1>",
                                 lambda e, c=self: c.ao_abrir(c.dados))
            self.canvas.tag_bind(self.tag_seta, "<Enter>",
                                 lambda e: self.canvas.configure(cursor="hand2"))
            self.canvas.tag_bind(self.tag_seta, "<Leave>",
                                 lambda e: self.canvas.configure(cursor=""))

    def _desenhar_cartas(self, peca, x, py, largura, passo, pecas):
        """Os 4 quadradinhos das cartas da peca (15.3), alinhados a direita:
        verde = carta que da status; vermelho = "Outra"; vazado = vazio.
        A linha inteira e clicavel (abre a edicao rapida)."""
        slots = ler_cartas(pecas.get(coluna_banco_cartas(peca)))
        lado = 9
        vao = 3
        topo = py + (passo - lado) / 2
        inicio = x + largura - 12 - SLOTS_CARTAS * lado - (SLOTS_CARTAS - 1) * vao
        tag = f"{self.tag}_cartas_{peca}"
        for indice, carta in enumerate(slots):
            estado = estado_da_carta(carta)
            qx = inicio + indice * (lado + vao)
            if estado == "status":
                cor, borda = CORES["verde"], CORES["verde"]
            elif estado == "outra":
                cor, borda = CORES["vermelho"], CORES["vermelho"]
            else:
                cor, borda = CORES["painel"], CORES["fraco"]
            self.create_image(qx, topo, anchor="nw", tags=(tag,),
                              image=self._img(
                                  f"carta_{peca}_{indice}",
                                  self._painel(cor, lado, lado, raio=2,
                                               borda=borda)))
        # area clicavel da linha inteira: uma imagem transparente por cima
        # (um retangulo sem preenchimento so responde na borda)
        area = Image.new("RGBA", (max(1, int((largura - 12) * self.s)),
                                  max(1, int(passo * self.s))), (0, 0, 0, 0))
        self.create_image(x + 6, py - 1, anchor="nw", tags=(tag,),
                          image=self._img(f"area_cartas_{peca}", area))
        self.canvas.tag_bind(tag, "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind(tag, "<Button-1>",
                             lambda e, p=peca: self._clicar_cartas(p))
        # a pedra (16): por cima da area clicavel, para o mouse "ver" o chip
        self._desenhar_pedra(peca, x, py, passo, pecas, tag)

    def _desenhar_pedra(self, peca, x, py, passo, pecas, tag_linha):
        """Chip do nivel da pedra antes do nome da peca, na cor do NIVEL
        (+18 vermelho, +17 dourado, +11 a +16 verde, +0 a +10 cinza; ver
        CORES_PEDRA); vazado = pedra nao informada. Passar o mouse mostra
        o status; clicar abre a edicao rapida (como a linha). Com o status
        MAIS FORTE da peca, um pontinho branco no canto de cima do chip."""
        nivel, status = ler_pedra(pecas.get(normalizar(coluna_pedra(peca))))
        cor_nivel = cor_da_pedra(nivel)
        if cor_nivel:
            fundo, cor = CORES_PEDRA[cor_nivel]
            borda = None
        else:
            fundo, borda, cor = CORES["painel"], CORES["fraco"], CORES["fraco"]
        largura, altura = X_NOME_PECA - 32, max(12, passo - 3)
        topo = py + (passo - altura) / 2 - 1
        tag = f"{self.tag}_pedra_{peca}"
        self.create_image(x + 30, topo, anchor="nw", tags=(tag, tag_linha),
                          image=self._img(f"pedra_{peca}", self._painel(
                              fundo, largura, altura, raio=4, borda=borda)))
        self.create_text(x + 30 + largura / 2, topo + altura / 2,
                         text=f"+{nivel}" if nivel is not None else "\u2013",
                         font=self.f(8, "bold"), fill=cor, anchor="center",
                         tags=(tag, tag_linha))
        if nivel is None:
            return
        forte = status_forte(peca, status)
        if forte:
            # o selo: pontinho branco com contorno escuro, no canto de cima
            raio = 3
            cx, cy = x + 30 + largura - 1, topo + 1
            self.create_oval(cx - raio, cy - raio, cx + raio, cy + raio,
                             fill="#ffffff", outline=CORES["fundo"],
                             width=max(1, round(self.s)),
                             tags=(tag, tag_linha))
        linhas = [f"+{nivel}  \u00b7  {status}"]
        if forte:
            linhas.append("\u25cf status mais forte")
        nome = dict(PECAS_VOID).get(peca, peca)
        self.canvas.tag_bind(
            tag, "<Enter>",
            lambda e: self._mostrar_balao(
                x + 30, py + passo + 2, f"PEDRA \u00b7 {nome.upper()}",
                linhas,
                borda=CORES_PEDRA[cor_nivel][0]))
        self.canvas.tag_bind(tag, "<Leave>", lambda e: self._esconder_titulos())

    def _valor_acessorio(self, x, y, valor, largura_max, cor=None):
        """Chip do acessorio: texto quebrando em ate 2 linhas, com a cor da
        regra do usuario (e contorno para ficar legivel)."""
        lay = self._layout()
        fonte = self.f(9, "bold")
        palavras = valor.split()
        linhas = []
        atual = ""
        for palavra in palavras:
            teste = (atual + " " + palavra).strip()
            if self._fonte_obj(fonte).measure(teste) <= largura_max - 12 or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        if len(linhas) > 2:
            # nao cabe em 2 linhas: corta a 2a com reticencias (antes o
            # resto sumia sem aviso: "Colar do Julgamento")
            linhas = [linhas[0], self._cortar(
                " ".join(linhas[1:]), 9, "bold", largura_max - 12)]
        linhas = linhas[:2]
        altura = lay["acc_valor_h"]
        borda = cor or "#6d28d9"
        self.create_image(x, y, anchor="nw", image=self._img(
            f"acc_{valor}", self._painel("#221a3d", largura_max, altura, raio=8,
                                         borda=borda)))
        passo = self._alt(9, "bold") + 2
        for indice, linha in enumerate(linhas):
            if cor:
                self._texto_contorno(x + 8, y + 4 + indice * passo, linha, cor,
                                     tamanho=9, peso="bold")
            else:
                self.create_text(x + 8, y + 4 + indice * passo, text=linha,
                                 font=fonte, fill="#d9c8ff", anchor="nw")
        return altura


# --------------------------------------------------------------------- PIL --
def _painel(cor, largura, altura, radius=12, borda=None, largura_borda=1):
    """Imagem RGBA de um painel arredondado."""
    largura = max(2, int(largura))
    altura = max(2, int(altura))
    cor = cor.lstrip("#")
    rgb = tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(img)
    if borda:
        borda = borda.lstrip("#")
        rgb_borda = tuple(int(borda[i:i + 2], 16) for i in (0, 2, 4))
        desenho.rounded_rectangle((0, 0, largura - 1, altura - 1), radius=radius,
                                  fill=rgb + (255,), outline=rgb_borda + (255,),
                                  width=largura_borda)
    else:
        desenho.rounded_rectangle((0, 0, largura - 1, altura - 1), radius=radius,
                                  fill=rgb + (255,))
    return img


def _cabecalho(cor, largura, altura, radius=14, borda=None):
    """Painel com os cantos de cima arredondados."""
    largura = max(2, int(largura))
    altura = max(2, int(altura))
    cor = cor.lstrip("#")
    rgb = tuple(int(cor[i:i + 2], 16) for i in (0, 2, 4))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    desenho = ImageDraw.Draw(img)
    cantos = (True, True, False, False)
    if borda:
        borda = borda.lstrip("#")
        rgb_borda = tuple(int(borda[i:i + 2], 16) for i in (0, 2, 4))
        desenho.rounded_rectangle((0, 0, largura - 1, altura - 1), radius=radius,
                                  fill=rgb + (255,), outline=rgb_borda + (255,),
                                  width=1, corners=cantos)
    else:
        desenho.rounded_rectangle((0, 0, largura - 1, altura - 1), radius=radius,
                                  fill=rgb + (255,), corners=cantos)
    return img

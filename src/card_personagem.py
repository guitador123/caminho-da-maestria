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
# Altura do card no design (escala 1.0). O app usa isso para escolher a
# escala do card conforme a resolucao (para o card caber inteiro na tela).
ALTURA_CARD_BASE = 950

PECAS_VOID = [
    ("arma", "Arma"), ("luvas", "Luvas"), ("cota", "Cota"), ("botas", "Botas"),
    ("capa", "Capa"), ("calca", "Cal\u00e7a"), ("elmo", "Elmo"),
    ("escudos", "Escudo"), ("asas", "Asas"), ("facas", "Facas"),
    ("mascara", "M\u00e1scara"), ("diadema", "Diadema"),
]

ACESSORIOS_CARD = [
    ("anel", "Anel"), ("tornozeleira", "Tornozeleira"),
    ("brinco", "Brinco"), ("piercing", "Piercing"),
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
# brinco e piercing seguem as mesmas regras
REGRAS_ACESSORIOS["piercing"] = REGRAS_ACESSORIOS["brinco"]


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
                 escala=1.0, ao_missao=None):
        self.canvas = canvas
        self.x0 = x
        self.y0 = y
        self.s = escala
        self.dados = dados
        self.ao_abrir = ao_abrir
        # callback do modo "missao rapida": (chave_da_missao, nome)
        self.ao_missao = ao_missao
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
                coords = self.canvas.coords(item)
                if not coords:
                    continue
                novos = [coords[0] + dx, coords[1] + dy]
                novos += list(coords[2:])
                self.canvas.coords(item, *novos)
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
                             lambda e, c=self: c.ao_abrir(c.dados))
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
        foto = ImageTk.PhotoImage(imagem)
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
              altura=22, radius=11, cor_borda=None, largura_max=None):
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
        self.create_image(x, y, anchor="nw", image=img)
        self.create_text(x + largura / 2, y + altura / 2, text=texto,
                         font=self.f(tamanho, "bold"), fill=cor_texto,
                         anchor="center")
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

        # --- progresso ---
        L["prog_titulo_y"] = L["alt_cabecalho"] + 14
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
        self._desenhar_progresso()
        self._desenhar_dungeons()
        self._desenhar_blocos()
        self._desenhar_equipamentos()
        self._itens = [i for i in self.canvas.find_all() if i not in antes]

    def atualizar(self, dados=None):
        """Redesenha o card (edicao ao vivo)."""
        if dados is not None:
            self.dados = dados
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
        self._chip(MARGEM, lay["badge_y"], "\u26a1 " + texto_poder,
                   CORES["painel"], CORES["texto"], tamanho=12,
                   altura=lay["badge_h"], radius=lay["badge_h"] / 2)

        # badge do nome
        nome = dados.get("nome") or "?"
        largura_nome = self._largura_texto(nome, 17)
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

        # titulo/origem (titulo obtido no jogo - dropdown na tela de edicao)
        titulo = dados.get("titulo") or ""
        if titulo:
            # nao pode invadir o retrato a direita
            largura_max = (LARGURA - RETRATO_LARGURA - MARGEM - 8
                           if self._largura_retrato else LARGURA - MARGEM * 2)
            self._chip(MARGEM, lay["titulo_y"], titulo, CORES["dourado"], "#241a05",
                       tamanho=11, altura=lay["titulo_h"],
                       radius=lay["titulo_h"] / 2,
                       largura_max=largura_max)

        # credito
        self._texto(MARGEM, lay["credito_y"], "Arte via Grand Chase Wiki", 9,
                    cor=CORES["fraco"])

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
            self.create_text(x + 36, py, text=rotulo, font=self.f(9),
                             fill=CORES["texto"] if ok else CORES["fraco"],
                             anchor="nw")

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

# -*- coding: utf-8 -*-
"""
As GUIAS do app (Maestria, Guilda, Evolucao) e as paginas que nao sao a
tela principal.

  - BarraAbas: a "pilula de vidro" centralizada no topo (trilho
    translucido; a guia ativa preenchida de roxo, como o botao "Apoiar").
    Desenhada num canvas e FIXA no topo enquanto a pagina rola.
  - PaginaBase: um canvas por cima da tela principal, com a mesma arte de
    fundo (fixa) e a barra de guias. A tela principal (Maestria) fica
    intacta por baixo: voltar para ela mantem a rolagem e os filtros.
  - PaginaGuilda: por enquanto, o que vem ai (item 12 do AFAZERES).
  - PaginaEvolucao: a pagina "Evolucao semanal" (pagina_evolucao.py), com
    "Copiar imagem" e "Salvar PNG" (antes era uma janela separada, aberta
    pelo 9o cartao).
"""

import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog
from tkinter import font as tkfont

from PIL import Image, ImageDraw, ImageTk

import pagina_evolucao
import tema_visual as tv
from area_transferencia import copiar_imagem
from config_app import BACKGROUND_PATH
from registro import falha
from rolagem import RolagemSuave
from versao_app import VERSAO

# (chave, rotulo) das guias, na ordem da barra
ABAS = [
    ("maestria", "Maestria"),
    ("guilda", "Guilda"),
    ("ranking", "Ranking"),
    ("evolucao", "Evolução"),
]

ROXO = (139, 92, 246)
LILAS = (167, 139, 250)
TEXTO = "#ffffff"
TEXTO_INATIVO = "#d9d3f0"
TEXTO_HOVER = "#ffffff"
TOPO_ABAS = 14            # y (design) da barra


def _pilula(largura, altura, fundo, borda=None):
    """Imagem RGBA de uma pilula (cantos totalmente redondos)."""
    largura, altura = max(2, int(largura)), max(2, int(altura))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        (0, 0, largura - 1, altura - 1), radius=altura // 2, fill=fundo,
        outline=borda, width=1 if borda else 0)
    return img


def _vidro(largura, altura, raio, alfa=170):
    """Painel de vidro (o mesmo dos cartoes da tela principal)."""
    largura, altura = max(2, int(largura)), max(2, int(altura))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    ImageDraw.Draw(img).rounded_rectangle(
        (0, 0, largura - 1, altura - 1), radius=int(raio),
        fill=tv.CORES["vidro"] + (alfa,),
        outline=tv.CORES["vidro_borda"] + (tv.CORES["vidro_borda_alfa"],),
        width=1)
    return img


class BarraAbas:
    """A barra de guias num canvas (tag "abas"), fixa no topo da vista."""

    TAG = "abas"

    def __init__(self, canvas, ao_trocar):
        self.canvas = canvas
        self.ao_trocar = ao_trocar
        self._fotos = {}
        self._topo = 0.0          # canvasy(0) quando foi desenhada
        self.itens_texto = {}     # chave -> item do texto (testes)
        self.ativa = None

    def desenhar(self, lay, ativa):
        """Desenha (ou redesenha) a barra com a guia `ativa` em destaque."""
        canvas = self.canvas
        canvas.delete(self.TAG)
        self.itens_texto = {}
        self.ativa = ativa
        tamanho = lay.f(14)
        fonte_ativa = ("Segoe UI", tamanho, "bold")
        fonte = ("Segoe UI", tamanho, "normal")
        medida = tkfont.Font(family="Segoe UI", size=tamanho, weight="bold")
        folga = lay.f(20)
        altura = lay.f(34)
        margem = lay.f(4)
        larguras = [medida.measure(rotulo) + 2 * folga for _c, rotulo in ABAS]
        total = sum(larguras) + 2 * margem
        topo = canvas.canvasy(0)
        self._topo = topo
        # centro pela largura da TELA (o layout ja sabe; o canvas recem
        # criado ainda pode dizer 1 px)
        x0 = lay.largura / 2 - total / 2
        y0 = topo + lay.y(TOPO_ABAS)

        self._fotos["trilho"] = ImageTk.PhotoImage(_pilula(
            total, altura + 2 * margem, (20, 18, 33, 225), LILAS + (90,)))
        canvas.create_image(x0, y0, anchor="nw", image=self._fotos["trilho"],
                            tags=(self.TAG,))
        x = x0 + margem
        for (chave, rotulo), largura in zip(ABAS, larguras):
            tag = f"aba_{chave}"
            if chave == ativa:
                self._fotos[chave] = ImageTk.PhotoImage(
                    _pilula(largura, altura, ROXO + (255,)))
            else:
                # area de clique (e o clareado do hover), quase invisivel
                self._fotos[chave] = ImageTk.PhotoImage(
                    _pilula(largura, altura, (255, 255, 255, 1)))
                self._fotos[f"{chave}_hover"] = ImageTk.PhotoImage(
                    _pilula(largura, altura, (255, 255, 255, 34)))
            fundo = canvas.create_image(x, y0 + margem, anchor="nw",
                                        image=self._fotos[chave],
                                        tags=(self.TAG, tag))
            texto = canvas.create_text(
                x + largura / 2, y0 + margem + altura / 2, text=rotulo,
                font=fonte_ativa if chave == ativa else fonte,
                fill=TEXTO if chave == ativa else TEXTO_INATIVO,
                anchor="center", tags=(self.TAG, tag))
            self.itens_texto[chave] = texto
            if chave != ativa:
                canvas.tag_bind(tag, "<Enter>", lambda e, c=chave, f=fundo, t=texto:
                                self._hover(c, f, t, True))
                canvas.tag_bind(tag, "<Leave>", lambda e, c=chave, f=fundo, t=texto:
                                self._hover(c, f, t, False))
                canvas.tag_bind(tag, "<Button-1>",
                                lambda e, c=chave: self.ao_trocar(c))
            x += largura
        canvas.tag_raise(self.TAG)

    def _hover(self, chave, fundo, texto, dentro):
        try:
            self.canvas.itemconfigure(
                fundo, image=self._fotos[f"{chave}_hover" if dentro else chave])
            self.canvas.itemconfigure(
                texto, fill=TEXTO_HOVER if dentro else TEXTO_INATIVO)
            self.canvas.configure(cursor="hand2" if dentro else "")
        except tk.TclError:
            pass                      # janela ja fechada

    def fixar(self):
        """Mantem a barra no topo da vista enquanto a pagina rola."""
        try:
            topo = self.canvas.canvasy(0)
            if abs(topo - self._topo) >= 0.5:
                self.canvas.move(self.TAG, 0, topo - self._topo)
                self._topo = topo
            self.elevar()
        except tk.TclError:
            pass                      # janela ja fechada

    def elevar(self):
        try:
            self.canvas.tag_raise(self.TAG)
        except tk.TclError:
            pass


class PaginaBase(tk.Canvas):
    """Uma pagina por cima da tela principal: arte de fundo fixa, a barra
    de guias fixa e o conteudo (que rola)."""

    CHAVE = ""

    def __init__(self, app):
        super().__init__(app, bg="#191334", highlightthickness=0, bd=0,
                         yscrollincrement=1)
        self.app = app
        self._fotos = {}
        self._tamanho = (0, 0)
        self._job = None
        self._item_arte = None
        self.barra = BarraAbas(self, app.ir_para)
        self._rolagem = RolagemSuave(self, ao_mover=self._fixar)
        self.bind("<MouseWheel>", lambda e: self._rolagem.roda(e.delta))
        self.bind("<Configure>", self._ao_redimensionar)

    # ------------------------------------------------------------ mostrar
    def mostrar(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Misc.tkraise(self)
        self.update_idletasks()
        self.redesenhar(forcar=True)

    def esconder(self):
        self.place_forget()

    def visivel(self):
        return bool(self.winfo_ismapped())

    # --------------------------------------------------------- desenhar
    def _ao_redimensionar(self, _evento):
        if self._job is not None:
            self.after_cancel(self._job)
        self._job = self.after(120, self.redesenhar)

    def redesenhar(self, forcar=False):
        self._job = None
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 50 or altura < 50:
            largura, altura = self.app.winfo_width(), self.app.winfo_height()
        if not forcar and (largura, altura) == self._tamanho:
            return
        self._tamanho = (largura, altura)
        lay = tv.Layout(largura, altura)
        self._rolagem.parar()
        self.delete("all")
        self.yview_moveto(0)
        try:
            if os.path.exists(BACKGROUND_PATH):
                self._fotos["arte"] = ImageTk.PhotoImage(
                    tv.render_arte(BACKGROUND_PATH, largura, altura))
                self._item_arte = self.create_image(
                    0, 0, anchor="nw", image=self._fotos["arte"])
        except Exception as erro:
            falha("[Pagina] desenhar a arte", erro)
        fim = self.desenhar_conteudo(lay, largura, altura)
        self.configure(scrollregion=(0, 0, largura, max(altura, fim)))
        self.barra.desenhar(lay, self.CHAVE)

    def desenhar_conteudo(self, lay, largura, altura):
        """Desenha o conteudo; devolve o y do fim (para a rolagem)."""
        return altura

    def _fixar(self):
        if self._item_arte is not None:
            try:
                self.coords(self._item_arte, 0, self.canvasy(0))
            except tk.TclError:
                pass
        self.barra.fixar()

    # ----------------------------------------------------------- helpers
    def _texto(self, x, y, texto, tamanho, cor="#ffffff", peso="normal",
               anchor="nw", familia="Segoe UI", **extra):
        return self.create_text(x, y, text=texto, fill=cor, anchor=anchor,
                                font=(familia, tamanho, peso), **extra)

    def _botao(self, chave, x, y, rotulo, comando, lay, cheio=False):
        """Botao de vidro (ou roxo, cheio=True) desenhado no canvas.
        Devolve a largura."""
        tamanho = lay.f(13)
        medida = tkfont.Font(family="Segoe UI", size=tamanho, weight="bold")
        largura = medida.measure(rotulo) + 2 * lay.f(18)
        altura = lay.f(36)
        if cheio:
            imagem = tv.botao_gradiente(tv.CORES["roxo"], largura, altura,
                                        raio=lay.f(10))
        else:
            imagem = _vidro(largura, altura, lay.f(10), alfa=200)
        self._fotos[chave] = ImageTk.PhotoImage(imagem)
        tag = f"botao_{chave}"
        self.create_image(x, y, anchor="nw", image=self._fotos[chave],
                          tags=(tag,))
        self._texto(x + largura / 2, y + altura / 2, rotulo, tamanho,
                    peso="bold", anchor="center", tags=(tag,))
        self.tag_bind(tag, "<Button-1>", lambda e: comando())
        self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
        self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))
        return largura


# ------------------------------------------------------------ a guilda --
MEDALHA_COR = {"ouro": (245, 196, 81), "prata": (192, 199, 214),
               "bronze": (205, 138, 78)}
COR_VOCE = (167, 139, 250)


def caminho_foto(avatar):
    """assets/perfil/<personagem>_icon.png (a foto do perfil) ou None."""
    if not avatar:
        return None
    import caminhos
    pasta = os.path.join(caminhos.assets_dir(), "assets", tv.PASTA_PERFIL)
    base = str(avatar).strip()
    for nome in (f"{base.lower()}_icon.png", f"{base}_icon.png"):
        caminho = os.path.join(pasta, nome)
        if os.path.exists(caminho):
            return caminho
    return None


def caminho_distintivo(nivel):
    """O distintivo do Level Chaser (cl1.png, cl100.png, ...) ou None."""
    import caminhos
    from dados_app import _num
    nivel = max(1, _num(nivel))
    marco = 1 if nivel < 100 else min(900, (nivel // 100) * 100)
    pasta = os.path.join(caminhos.assets_dir(), "assets", tv.PASTA_CHASER)
    for nome in (f"cl{marco}.png", f"cl{marco}.jpg", f"cl{marco}.webp"):
        caminho = os.path.join(pasta, nome)
        if os.path.exists(caminho):
            return caminho
    return None


_CACHE_IMAGENS = {}


def _fonte_pil(tamanho):
    from PIL import ImageFont
    try:
        return ImageFont.truetype("segoeuib.ttf", max(8, tamanho))
    except OSError:
        return ImageFont.load_default()


def _imagem_cache(chave, fazer):
    if chave not in _CACHE_IMAGENS:
        _CACHE_IMAGENS[chave] = fazer()
    return _CACHE_IMAGENS[chave]


def avatar_de(perfil, lado):
    """A foto do perfil num circulo; sem foto, a inicial do nick (ou "?")."""
    import guilda
    avatar = (perfil or {}).get("avatar")
    lado = max(16, int(lado))
    foto = _imagem_cache(("foto", avatar, lado), lambda: tv.avatar_circular(
        caminho_foto(avatar), lado))
    if caminho_foto(avatar) is None:
        foto = foto.copy()
        inicial = (guilda.nome_do_perfil(perfil) if (perfil or {}).get("nick")
                   else "?")[:1].upper()
        ImageDraw.Draw(foto).text((lado / 2, lado / 2), inicial, anchor="mm",
                                  fill=(210, 200, 240, 255),
                                  font=_fonte_pil(int(lado * 0.42)))
    return foto


def _milhar(valor):
    from dados_app import _num
    return f"{_num(valor):,}".replace(",", ".")


class _PerfilMixin:
    """Desenha um painel de perfil (foto, Lv., nick, EXP, distintivo)."""

    def _painel_perfil(self, x, y, largura, perfil, lay, posicao=None,
                       medalha=None, voce=False, tag=None, grande=False):
        from dados_app import progresso_exp, _num
        import guilda
        k = lay.s * (1.25 if grande else 1.0)
        altura = int(118 * k)
        borda = (MEDALHA_COR.get(medalha) if medalha
                 else COR_VOCE if voce else None)
        img = _vidro(largura, altura, 14 * k)
        if borda:
            ImageDraw.Draw(img).rounded_rectangle(
                (1, 1, img.width - 2, img.height - 2), radius=int(14 * k),
                outline=borda + (255,), width=max(2, int(2 * k)))
        tags = (tag,) if tag else ()
        chave = f"painel_{tag or 'conta'}"
        self._fotos[chave] = ImageTk.PhotoImage(img)
        self.create_image(x, y, anchor="nw", image=self._fotos[chave], tags=tags)

        # foto (circulo)
        lado = int(70 * k)
        foto = avatar_de(perfil, lado)
        self._fotos[chave + "_foto"] = ImageTk.PhotoImage(foto)
        self.create_image(x + 14 * k, y + (altura - lado) / 2, anchor="nw",
                          image=self._fotos[chave + "_foto"], tags=tags)

        # distintivo do Level Chaser (direita)
        lado_d = int(64 * k)
        caminho_d = caminho_distintivo(perfil.get("nivel_chaser"))
        if caminho_d:
            dist = _imagem_cache(("dist", caminho_d, lado_d),
                                 lambda: tv.icone_chaser(caminho_d, lado_d, 0.8))
            self._fotos[chave + "_dist"] = ImageTk.PhotoImage(dist)
            self.create_image(x + largura - 10 * k, y + altura / 2, anchor="e",
                              image=self._fotos[chave + "_dist"], tags=tags)

        # textos
        tx = x + (14 + 70 + 14) * k
        largura_texto = largura - (14 + 70 + 14 + 70) * k
        nivel = _num(perfil.get("nivel_chaser"))
        tamanho = max(9, int(15 * k))
        fonte = tkfont.Font(family="Segoe UI", size=tamanho, weight="bold")
        ty = y + 16 * k
        item = self._texto(tx, ty, f"Lv. {nivel}", tamanho, "#f5c451", "bold",
                           tags=tags)
        cursor = self.bbox(item)[2] + 6 * k
        nome = guilda.nome_do_perfil(perfil)
        while nome and fonte.measure("· " + nome) > tx + largura_texto - cursor:
            nome = nome[:-2] + "…" if len(nome) > 2 else ""
        self._texto(cursor, ty, "· " + nome, tamanho, "#ffffff", "bold",
                    tags=tags)
        pequeno = max(8, int(11 * k))
        self._texto(tx, ty + 26 * k,
                    f"Coleção {_milhar(perfil.get('colecao_cartas'))}",
                    pequeno, tv.CORES["suave"], tags=tags)
        self._texto(tx, ty + 44 * k,
                    f"Ataque médio {_milhar(perfil.get('ataque_medio'))}",
                    pequeno, tv.CORES["suave"], tags=tags)
        percentual, _proximo = progresso_exp(nivel)
        barra = tv.barra_exp(int(largura_texto), max(10, int(16 * k)),
                             percentual, f"{percentual:.0f}%" if percentual < 100
                             else "100%  ·  MÁX")
        self._fotos[chave + "_exp"] = ImageTk.PhotoImage(barra)
        self.create_image(tx, y + altura - (16 + 18) * k, anchor="nw",
                          image=self._fotos[chave + "_exp"], tags=tags)

        # "VOCE" (a sua conta), no pe do painel, a direita
        if voce:
            chip = _pilula(int(48 * k), int(20 * k), COR_VOCE + (255,))
            self._fotos[chave + "_voce"] = ImageTk.PhotoImage(chip)
            self.create_image(x + largura - 10 * k, y + altura - 8 * k,
                              anchor="se", image=self._fotos[chave + "_voce"],
                              tags=tags)
            self._texto(x + largura - 10 * k - 24 * k, y + altura - 8 * k - 10 * k,
                        "VOCÊ", max(7, int(10 * k)), "#1b1730", "bold",
                        anchor="center", tags=tags)

        # posicao (1o, 2o...) no canto
        if posicao:
            cor = MEDALHA_COR.get(medalha, (58, 50, 92))
            texto_cor = "#241a05" if medalha in ("ouro", "prata") else "#ffffff"
            chip = _pilula(int(38 * k), int(22 * k), cor + (255,))
            self._fotos[chave + "_pos"] = ImageTk.PhotoImage(chip)
            self.create_image(x + 8 * k, y + 8 * k, anchor="nw",
                              image=self._fotos[chave + "_pos"], tags=tags)
            self._texto(x + 8 * k + 19 * k, y + 8 * k + 11 * k, f"{posicao}º",
                        max(8, int(11 * k)), texto_cor, "bold", anchor="center",
                        tags=tags)
        return altura


class PaginaGuilda(_PerfilMixin, PaginaBase):
    """O HUB da guilda: o perfil de todas as contas do app, em ordem de
    Level Chaser (empate: Ataque Total medio). Clicar abre a conta da
    pessoa so para ver (a sua volta para a Maestria)."""

    CHAVE = "guilda"
    LARGURA_PAINEL = 360

    def __init__(self, app):
        super().__init__(app)
        self.perfis = None        # None = ainda carregando
        self.erro = ""

    def mostrar(self):
        super().mostrar()
        self.carregar()

    def carregar(self):
        """Busca a lista no banco (em segundo plano) e redesenha."""
        app = self.app
        if not getattr(app, "usar_supabase", False) or getattr(app, "offline", False):
            self.perfis, self.erro = [], "O HUB da guilda precisa de internet."
            self.redesenhar(forcar=True)
            return
        from supabase_db import perfis_da_guilda
        import guilda

        def ao_terminar(ok, resultado):
            if ok:
                self.perfis, self.erro = guilda.ordenar(resultado), ""
            else:
                self.perfis = self.perfis or []
                self.erro = ("Não deu para carregar a guilda agora "
                             "(sem internet ou sql/guilda.sql não rodado).")
            if self.visivel():
                self.redesenhar(forcar=True)

        app._em_segundo_plano(lambda: perfis_da_guilda(app.supabase),
                              ao_terminar)

    def desenhar_conteudo(self, lay, largura, altura):
        import guilda
        margem = lay.f(24)
        y = lay.y(TOPO_ABAS) + lay.f(34 + 8) + lay.f(26)
        gap = lay.f(14)
        largura_painel = lay.w(self.LARGURA_PAINEL)
        colunas = max(1, int((largura - 2 * margem + gap) // (largura_painel + gap)))
        colunas = min(colunas, 4)
        total = colunas * largura_painel + (colunas - 1) * gap
        x0 = (largura - total) / 2

        self._texto(x0, y, "Guilda", lay.f(26), "#ffffff", "bold",
                    familia="Segoe UI Black")
        if self.perfis is None:
            subtitulo = "Carregando os perfis..."
        elif self.erro:
            subtitulo = self.erro
        else:
            subtitulo = (f"{len(self.perfis)} jogadores  ·  em ordem de Level "
                         "Chaser  ·  clique num perfil para ver a conta")
        self._texto(x0, y + lay.f(40), subtitulo, lay.f(13),
                    "#fb7185" if self.erro else tv.CORES["suave"])
        y += lay.f(78)

        meu = getattr(self.app, "user_id", None)
        altura_linha = 0
        for indice, perfil in enumerate(self.perfis or []):
            coluna = indice % colunas
            if coluna == 0 and indice:
                y += altura_linha + gap
            x = x0 + coluna * (largura_painel + gap)
            tag = f"perfil_{indice}"
            voce = perfil.get("user_id") == meu
            altura_linha = self._painel_perfil(
                x, y, largura_painel, perfil, lay, posicao=indice + 1,
                medalha=guilda.medalha(indice + 1), voce=voce, tag=tag)
            self.tag_bind(tag, "<Button-1>",
                          lambda e, p=perfil, v=voce: self._abrir(p, v))
            self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
            self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))
        return y + altura_linha + lay.f(40)

    def _abrir(self, perfil, voce):
        if voce:
            self.app.ir_para("maestria")      # a sua conta e a Maestria
        else:
            self.app.ver_conta(perfil)


class PaginaConta(_PerfilMixin, PaginaBase):
    """A conta de outra pessoa, SO PARA VER: o perfil e os cards (os
    baloes funcionam; nada abre edicao nem salva)."""

    CHAVE = "guilda"              # a guia acesa continua sendo a Guilda

    def __init__(self, app):
        super().__init__(app)
        self.perfil = {}
        self.abas = None          # None = carregando
        self.erro = ""
        self._cards = []

    def definir(self, perfil, abas=None, erro=""):
        self.perfil, self.abas, self.erro = dict(perfil or {}), abas, erro
        if self.visivel():
            self.redesenhar(forcar=True)

    def desenhar_conteudo(self, lay, largura, altura):
        import guilda
        from card_personagem import CardPersonagem, LARGURA as CARD_LARGURA
        import caminhos
        self._cards = []
        nome = guilda.nome_do_perfil(self.perfil)
        y = lay.y(TOPO_ABAS) + lay.f(34 + 8) + lay.f(20)

        # faixa "somente leitura" + voltar
        margem = lay.f(24)
        faixa_l = min(largura - 2 * margem, lay.w(1100))
        fx = (largura - faixa_l) / 2
        faixa_a = lay.f(44)
        faixa = Image.new("RGBA", (int(faixa_l), int(faixa_a)), (0, 0, 0, 0))
        ImageDraw.Draw(faixa).rounded_rectangle(
            (0, 0, faixa.width - 1, faixa.height - 1), radius=lay.f(10),
            fill=(59, 47, 18, 235), outline=(245, 158, 11, 255), width=1)
        self._fotos["faixa"] = ImageTk.PhotoImage(faixa)
        self.create_image(fx, y, anchor="nw", image=self._fotos["faixa"])
        self._texto(fx + lay.f(16), y + faixa_a / 2,
                    f"Vendo a conta de {nome}  ·  somente leitura", lay.f(13),
                    "#f59e0b", "bold", anchor="w")
        rotulo = "‹  Voltar para a Guilda"
        largura_b = self._largura_texto(rotulo, lay) + 2 * lay.f(16)
        self._botao("voltar", fx + faixa_l - largura_b - lay.f(6),
                    y + (faixa_a - lay.f(36)) / 2, rotulo,
                    lambda: self.app.ir_para("guilda"), lay, cheio=True)
        y += faixa_a + lay.f(18)

        # o perfil
        perfil_l = min(faixa_l, lay.w(620))
        altura_p = self._painel_perfil((largura - perfil_l) / 2, y, perfil_l,
                                       self.perfil, lay, grande=True)
        y += altura_p + lay.f(22)

        if self.abas is None or self.erro:
            self._texto(largura / 2, y, self.erro or "Carregando a conta...",
                        lay.f(14), "#fb7185" if self.erro else tv.CORES["suave"],
                        anchor="n")
            return y + lay.f(60)
        nomes = guilda.ordem_dos_personagens(self.abas)
        if not nomes:
            self._texto(largura / 2, y, "Esta conta ainda não tem personagens.",
                        lay.f(14), tv.CORES["suave"], anchor="n")
            return y + lay.f(60)

        # os cards (os mesmos da Maestria, sem edicao)
        escala = self.app._escala_dos_cards(largura, altura)
        largura_card = CARD_LARGURA * escala
        gap = 16 * escala
        colunas = max(1, int((largura - 2 * 20 + gap) // (largura_card + gap)))
        total = colunas * largura_card + (colunas - 1) * gap
        x0 = max(20, (largura - total) / 2)
        pasta = os.path.join(caminhos.assets_dir(), "assets", "personagens")
        altura_linha = 0
        for indice, nome_p in enumerate(nomes):
            coluna = indice % colunas
            if coluna == 0 and indice:
                y += altura_linha + gap
                altura_linha = 0
            card = CardPersonagem(
                self, x0 + coluna * (largura_card + gap), y,
                self.app._dados_personagem(nome_p, self.abas),
                ao_abrir=None, pasta_retratos=pasta, escala=escala,
                ao_missao=None, ao_cartas=None)
            self._cards.append(card)
            altura_linha = max(altura_linha, card.altura)
        return y + altura_linha + lay.f(40)

    @staticmethod
    def _largura_texto(texto, lay):
        return tkfont.Font(family="Segoe UI", size=lay.f(13),
                           weight="bold").measure(texto)


class PaginaEvolucao(PaginaBase):
    """A guia Evolucao: a pagina da evolucao semanal + copiar e salvar."""

    CHAVE = "evolucao"

    def __init__(self, app):
        super().__init__(app)
        self.imagem = None
        self._aviso = None
        self._job_aviso = None

    def definir(self, semanas, atual, destaque=None, nick=""):
        """Monta a pagina (imagem) com os dados; redesenha se visivel."""
        self.imagem = pagina_evolucao.montar(semanas, atual, destaque=destaque,
                                             nick=nick, versao=VERSAO)
        if self.visivel():
            self.redesenhar(forcar=True)

    def desenhar_conteudo(self, lay, largura, altura):
        if self.imagem is None:
            self._texto(largura / 2, lay.y(140), "Carregando a evolução...",
                        lay.f(16), tv.CORES["suave"], anchor="n")
            return altura
        margem = lay.f(24)
        escala = min(1.0, (largura - 2 * margem) / self.imagem.width)
        largura_img = int(self.imagem.width * escala)
        imagem = (self.imagem if escala >= 1.0 else self.imagem.resize(
            (largura_img, int(self.imagem.height * escala)), Image.LANCZOS))
        x = (largura - largura_img) / 2
        y = lay.y(TOPO_ABAS) + lay.f(34 + 8) + lay.f(22)

        # botoes (a direita, alinhados com a pagina)
        xb = x + largura_img
        xb -= self._botao("salvar", xb - self._largura_botao("Salvar PNG", lay),
                          y, "Salvar PNG", self.salvar_png, lay)
        xb -= lay.f(10)
        self._botao("copiar", xb - self._largura_botao("Copiar imagem", lay),
                    y, "Copiar imagem", self.copiar, lay, cheio=True)
        self._aviso = self._texto(x, y + lay.f(18), "", lay.f(13), "#34d399",
                                  "bold", anchor="w")

        y += lay.f(36) + lay.f(16)
        self._fotos["pagina"] = ImageTk.PhotoImage(imagem)
        self.create_image(x, y, anchor="nw", image=self._fotos["pagina"])
        return y + imagem.height + lay.f(30)

    @staticmethod
    def _largura_botao(rotulo, lay):
        medida = tkfont.Font(family="Segoe UI", size=lay.f(13), weight="bold")
        return medida.measure(rotulo) + 2 * lay.f(18)

    # ------------------------------------------------------------- acoes
    def copiar(self):
        if self.imagem is not None and copiar_imagem(self.imagem):
            self._avisar("Imagem copiada! Cole no Discord com Ctrl+V.")
        else:
            self._avisar("Não consegui copiar. Use Salvar PNG.", erro=True)

    def salvar_png(self, caminho=None):
        if self.imagem is None:
            return
        if caminho is None:
            nome = f"evolucao-semanal-{datetime.now():%Y-%m-%d}.png"
            caminho = filedialog.asksaveasfilename(
                parent=self.app, title="Salvar a página como imagem",
                defaultextension=".png", initialfile=nome,
                filetypes=[("Imagem PNG", "*.png")],
                initialdir=os.path.join(os.path.expanduser("~"), "Pictures"))
        if not caminho:
            return
        try:
            self.imagem.save(caminho, "PNG")
            self._avisar(f"Salvo em {os.path.basename(caminho)}")
        except OSError as erro:
            falha("salvar a pagina de evolucao", erro)
            self._avisar("Não consegui salvar o arquivo.", erro=True)

    def _avisar(self, texto, erro=False):
        if self._aviso is None:
            return
        try:
            self.itemconfigure(self._aviso, text=texto,
                               fill="#fb7185" if erro else "#34d399")
            if self._job_aviso is not None:
                self.after_cancel(self._job_aviso)
            self._job_aviso = self.after(
                4000, lambda: self.winfo_exists()
                and self.itemconfigure(self._aviso, text=""))
        except tk.TclError:
            pass                      # janela ja fechada


# ------------------------------------------------------------- o ranking --
COR_DEGRAU = {
    "ouro": ((214, 158, 46), (245, 196, 81), "#241a05"),
    "prata": ((128, 137, 156), (192, 199, 214), "#14161c"),
    "bronze": ((160, 98, 52), (205, 138, 78), "#ffffff"),
}


def _degrau(largura, altura, medalha):
    """O degrau do podio: bloco com o topo arredondado e um brilho em cima."""
    largura, altura = max(4, int(largura)), max(4, int(altura))
    base, brilho, _texto = COR_DEGRAU[medalha]
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    raio = max(4, largura // 14)
    d.rounded_rectangle((0, 0, largura - 1, altura + raio), radius=raio,
                        fill=base + (255,))
    d.rounded_rectangle((0, 0, largura - 1, min(altura, raio * 2)),
                        radius=raio, fill=brilho + (255,))
    d.rectangle((0, raio, largura - 1, min(altura, raio * 2)),
                fill=base + (255,))
    return img


def _barra(largura, altura, fracao, cor):
    largura, altura = max(4, int(largura)), max(3, int(altura))
    img = Image.new("RGBA", (largura, altura), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, largura - 1, altura - 1), radius=altura // 2,
                        fill=(15, 11, 34, 255))
    cheio = int((largura - 1) * max(0.0, min(1.0, fracao)))
    if cheio >= altura:
        d.rounded_rectangle((0, 0, cheio, altura - 1), radius=altura // 2,
                            fill=cor + (255,))
    return img


class PaginaRanking(PaginaBase):
    """A guia Ranking: o podio (5 categorias, com a lista de TODAS as
    contas embaixo) e o placar de cada um dos 25 personagens."""

    CHAVE = "ranking"

    def __init__(self, app):
        super().__init__(app)
        self.dados = None          # None = carregando
        self.erro = ""
        self.categoria = "fortes"
        self.personagem = None
        self._job_anim = None
        self._lay = None

    # ------------------------------------------------------------ dados
    def mostrar(self):
        super().mostrar()
        self.carregar()

    def carregar(self):
        app = self.app
        if not getattr(app, "usar_supabase", False) or getattr(app, "offline", False):
            self.dados, self.erro = {"contas": [], "personagens": []}, \
                "O ranking precisa de internet."
            self.redesenhar(forcar=True)
            return
        from supabase_db import ranking_da_guilda

        def ao_terminar(ok, resultado):
            if ok:
                self.dados, self.erro = resultado, ""
            else:
                self.dados = self.dados or {"contas": [], "personagens": []}
                self.erro = ("Não deu para carregar o ranking agora "
                             "(sem internet ou sql/ranking.sql não rodado).")
            if self.visivel():
                self.redesenhar(forcar=True)

        app._em_segundo_plano(lambda: ranking_da_guilda(app.supabase),
                              ao_terminar)

    def _contas(self):
        return {c.get("user_id"): c for c in (self.dados or {}).get("contas", [])}

    # --------------------------------------------------------- desenho
    def desenhar_conteudo(self, lay, largura, altura):
        import ranking
        self._lay = lay
        margem = lay.f(24)
        self._largura_util = min(largura - 2 * margem, lay.w(1100))
        self._x0 = (largura - self._largura_util) / 2
        y = lay.y(TOPO_ABAS) + lay.f(34 + 8) + lay.f(24)
        x0 = self._x0
        self._texto(x0, y, "Ranking", lay.f(26), "#ffffff", "bold",
                    familia="Segoe UI Black")
        if self.dados is None:
            sub = "Carregando o ranking..."
        elif self.erro:
            sub = self.erro
        else:
            sub = (f"{len(self.dados['contas'])} contas  ·  todas do app  ·  "
                   "dungeons da semana atual")
        self._texto(x0, y + lay.f(40), sub, lay.f(13),
                    "#fb7185" if self.erro else tv.CORES["suave"])
        y += lay.f(80)
        if self.dados is None or not self.dados.get("contas"):
            return y + lay.f(40)

        # --- podios ---------------------------------------------------
        self._secao(x0, y, "PÓDIOS", lay)
        y += lay.f(30)
        self._y_chips = y
        self._desenhar_chips()
        y += lay.f(52)
        self._y_podio = y
        self._altura_podio = lay.f(340)
        self._desenhar_podio(1.0)
        y += self._altura_podio + lay.f(18)
        self._y_lista = y
        y = self._desenhar_lista()
        y += lay.f(40)

        # --- personagens ----------------------------------------------
        self._secao(x0, y, "PERSONAGENS", lay)
        self._texto(x0 + lay.f(150), y + lay.f(2),
                    "o mais forte de cada um, entre todas as contas",
                    lay.f(12), tv.CORES["suave"])
        y += lay.f(32)
        if self.personagem is None:
            campeoes = ranking.campeoes(self.dados["personagens"])
            meu = getattr(self.app, "user_id", None)
            meus = [n for n, c in campeoes.items() if c.get("user_id") == meu]
            self.personagem = (meus or list(campeoes) or ["Elesis"])[0]
        self._y_retratos = y
        y = self._desenhar_retratos()
        self._y_placar = y + lay.f(18)
        return self._desenhar_placar() + lay.f(40)

    def _secao(self, x, y, texto, lay):
        self._texto(x, y, texto, lay.f(13), "#a78bfa", "bold")

    # ------------------------------------------------------- categorias
    def _desenhar_chips(self):
        import ranking
        lay = self._lay
        self.delete("chips")
        tamanho = lay.f(13)
        medida = tkfont.Font(family="Segoe UI", size=tamanho, weight="bold")
        folga, altura, gap = lay.f(16), lay.f(34), lay.f(8)
        larguras = [medida.measure(r) + 2 * folga for _c, r, _t in ranking.CATEGORIAS]
        total = sum(larguras) + gap * (len(larguras) - 1)
        x = self._x0 + (self._largura_util - total) / 2
        for (chave, rotulo, _titulo), largura in zip(ranking.CATEGORIAS, larguras):
            ativa = chave == self.categoria
            img = _pilula(largura, altura,
                          ROXO + (255,) if ativa else (30, 24, 56, 230),
                          None if ativa else LILAS + (110,))
            self._fotos[f"chip_{chave}"] = ImageTk.PhotoImage(img)
            tag = f"cat_{chave}"
            self.create_image(x, self._y_chips, anchor="nw", tags=("chips", tag),
                              image=self._fotos[f"chip_{chave}"])
            self._texto(x + largura / 2, self._y_chips + altura / 2, rotulo,
                        tamanho, "#ffffff" if ativa else TEXTO_INATIVO,
                        "bold" if ativa else "normal", anchor="center",
                        tags=("chips", tag))
            if not ativa:
                self.tag_bind(tag, "<Button-1>",
                              lambda e, c=chave: self.trocar_categoria(c))
                self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
                self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))
            x += largura + gap

    def trocar_categoria(self, chave):
        if chave == self.categoria:
            return
        self.categoria = chave
        self._desenhar_chips()
        self._desenhar_lista()
        self._animar_podio(0)

    def _animar_podio(self, quadro):
        """Os degraus sobem do chao (8 quadros, ~240 ms)."""
        if self._job_anim is not None:
            self.after_cancel(self._job_anim)
            self._job_anim = None
        t = min(1.0, (quadro + 1) / 8)
        self._desenhar_podio(1 - (1 - t) ** 3)
        if t < 1.0:
            self._job_anim = self.after(30, lambda: self._animar_podio(quadro + 1))

    # ------------------------------------------------------------ podio
    def _desenhar_podio(self, t):
        import guilda
        import ranking
        lay = self._lay
        self.delete("podio")
        lista = ranking.podio(self.dados["contas"], self.categoria,
                              self.dados["personagens"])
        titulo = dict((c, ti) for c, _r, ti in ranking.CATEGORIAS)[self.categoria]
        cx = self._x0 + self._largura_util / 2
        topo = self._y_podio
        base = topo + self._altura_podio - lay.f(16)
        self._texto(cx, topo, titulo.upper(), lay.f(12), tv.CORES["suave"],
                    "bold", anchor="n", tags=("podio",))
        largura_degrau = min(lay.w(190), self._largura_util / 3.4)
        alturas = {1: lay.f(130), 2: lay.f(92), 3: lay.f(64)}
        posicoes = {2: cx - largura_degrau - lay.f(6), 1: cx,
                    3: cx + largura_degrau + lay.f(6)}
        meu = getattr(self.app, "user_id", None)
        # a base (o chao do podio)
        chao = _pilula(largura_degrau * 3 + lay.f(60), lay.f(10), (42, 35, 71, 255))
        self._fotos["podio_chao"] = ImageTk.PhotoImage(chao)
        self.create_image(cx, base, anchor="n", image=self._fotos["podio_chao"],
                          tags=("podio",))
        for posicao in (2, 3, 1):
            if posicao > len(lista):
                continue
            conta, numero = lista[posicao - 1]
            medalha = guilda.medalha(posicao)
            altura = max(lay.f(6), alturas[posicao] * t)
            x = posicoes[posicao]
            self._fotos[f"degrau_{posicao}"] = ImageTk.PhotoImage(
                _degrau(largura_degrau, altura, medalha))
            self.create_image(x, base, anchor="s",
                              image=self._fotos[f"degrau_{posicao}"],
                              tags=("podio",))
            _b, _br, cor_texto = COR_DEGRAU[medalha]
            if altura > lay.f(40):
                self._texto(x, base - altura + lay.f(8), str(posicao),
                            lay.f(30 if posicao == 1 else 24), cor_texto,
                            "bold", anchor="n", familia="Segoe UI Black",
                            tags=("podio",))
            # foto, nick e o valor acima do degrau
            lado = lay.f(86 if posicao == 1 else 66)
            topo_foto = base - altura - lay.f(46) - lado
            anel = Image.new("RGBA", (lado + lay.f(8), lado + lay.f(8)), (0, 0, 0, 0))
            ImageDraw.Draw(anel).ellipse(
                (0, 0, anel.width - 1, anel.height - 1),
                fill=COR_DEGRAU[medalha][1] + (255,))
            anel.alpha_composite(avatar_de(conta, lado), (lay.f(4), lay.f(4)))
            self._fotos[f"foto_{posicao}"] = ImageTk.PhotoImage(anel)
            self.create_image(x, topo_foto, anchor="n",
                              image=self._fotos[f"foto_{posicao}"], tags=("podio",))
            if posicao == 1:
                self._coroa(x, topo_foto - lay.f(4), lay.f(34))
            nome = guilda.nome_do_perfil(conta)
            if conta.get("user_id") == meu:
                nome += "  (você)"
            self._texto(x, base - altura - lay.f(40), nome,
                        lay.f(14 if posicao == 1 else 13), "#ffffff", "bold",
                        anchor="n", tags=("podio",))
            self._texto(x, base - altura - lay.f(20),
                        ranking.texto_do_valor(self.categoria, numero),
                        lay.f(12), "#f5c451" if posicao == 1 else "#d9d3f0",
                        "bold", anchor="n",
                        tags=("podio",))

    def _coroa(self, x, y_base, largura):
        """Uma coroa dourada (poligono) com a ponta em y_base."""
        h = largura * 0.62
        pontos = [x - largura / 2, y_base, x - largura / 2, y_base - h * 0.55,
                  x - largura / 4, y_base - h * 0.25, x, y_base - h,
                  x + largura / 4, y_base - h * 0.25, x + largura / 2,
                  y_base - h * 0.55, x + largura / 2, y_base]
        self.create_polygon(*pontos, fill="#f5c451", outline="#b8860b",
                            width=1, tags=("podio",))
        r = largura * 0.07
        for px, py in ((x, y_base - h), (x - largura / 2, y_base - h * 0.55),
                       (x + largura / 2, y_base - h * 0.55)):
            self.create_oval(px - r, py - r, px + r, py + r, fill="#fb7185",
                             outline="", tags=("podio",))

    # ------------------------------------------------- lista de contas
    def _desenhar_lista(self):
        """TODAS as contas na categoria (quem nao esta no podio se ve aqui)."""
        import guilda
        import ranking
        lay = self._lay
        self.delete("lista")
        lista = ranking.podio(self.dados["contas"], self.categoria,
                              self.dados["personagens"])
        x0, largura = self._x0, self._largura_util
        linha_a = lay.f(40)
        y = self._y_lista
        painel_a = lay.f(16) + linha_a * len(lista)
        self._fotos["lista_painel"] = ImageTk.PhotoImage(
            _vidro(largura, painel_a, lay.f(14)))
        self.create_image(x0, y, anchor="nw", image=self._fotos["lista_painel"],
                          tags=("lista",))
        maior = max([n for _c, n in lista] + [1])
        meu = getattr(self.app, "user_id", None)
        y += lay.f(8)
        for indice, (conta, numero) in enumerate(lista):
            posicao = indice + 1
            medalha = guilda.medalha(posicao)
            voce = conta.get("user_id") == meu
            if voce:
                fundo = _pilula(largura - lay.f(16), linha_a - lay.f(4),
                                LILAS + (60,))
                self._fotos["lista_voce"] = ImageTk.PhotoImage(fundo)
                self.create_image(x0 + lay.f(8), y + lay.f(2), anchor="nw",
                                  image=self._fotos["lista_voce"], tags=("lista",))
            meio = y + linha_a / 2
            cor_pos = ("#f5c451" if medalha == "ouro" else "#d4d4d8"
                       if medalha == "prata" else "#d08a4e" if medalha
                       else tv.CORES["suave"])
            self._texto(x0 + lay.f(36), meio, f"{posicao}º", lay.f(14), cor_pos,
                        "bold", anchor="e", tags=("lista",))
            lado = lay.f(28)
            self._fotos[f"lista_foto_{indice}"] = ImageTk.PhotoImage(
                avatar_de(conta, lado))
            self.create_image(x0 + lay.f(50), meio, anchor="w",
                              image=self._fotos[f"lista_foto_{indice}"],
                              tags=("lista",))
            nome = guilda.nome_do_perfil(conta) + ("  (você)" if voce else "")
            self._texto(x0 + lay.f(90), meio, nome, lay.f(14), "#ffffff",
                        "bold" if voce or medalha else "normal", anchor="w",
                        tags=("lista",))
            xb = x0 + largura * 0.46
            lb = largura * 0.34
            self._fotos[f"lista_barra_{indice}"] = ImageTk.PhotoImage(_barra(
                lb, lay.f(10), _num_seguro(numero) / maior,
                COR_DEGRAU[medalha][1] if medalha else ROXO))
            self.create_image(xb, meio, anchor="w",
                              image=self._fotos[f"lista_barra_{indice}"],
                              tags=("lista",))
            self._texto(x0 + largura - lay.f(18), meio,
                        ranking.texto_do_valor(self.categoria, numero),
                        lay.f(14), "#ffffff", "bold", anchor="e", tags=("lista",))
            y += linha_a
        self.tag_raise("lista")
        return self._y_lista + painel_a

    # ------------------------------------------------------- retratos
    def _desenhar_retratos(self):
        from card_personagem import caminho_retrato, retrato_pronto
        from opcoes import PERSONAGENS
        import caminhos
        import ranking
        lay = self._lay
        self.delete("retratos")
        pasta = os.path.join(caminhos.assets_dir(), "assets", "personagens")
        campeoes = ranking.campeoes(self.dados["personagens"])
        meu = getattr(self.app, "user_id", None)
        lado, gap = lay.f(74), lay.f(8)
        altura = lado + lay.f(22)
        colunas = max(1, int((self._largura_util + gap) // (lado + gap)))
        linhas = -(-len(PERSONAGENS) // colunas)
        total_l = min(colunas, len(PERSONAGENS)) * (lado + gap) - gap
        x0 = self._x0 + (self._largura_util - total_l) / 2
        y0 = self._y_retratos
        for indice, nome in enumerate(PERSONAGENS):
            x = x0 + (indice % colunas) * (lado + gap)
            y = y0 + (indice // colunas) * (altura + gap)
            ativo = nome == self.personagem
            seu = campeoes.get(nome, {}).get("user_id") == meu and meu
            img = _vidro(lado, lado, lay.f(12), alfa=210)
            if ativo or seu:
                ImageDraw.Draw(img).rounded_rectangle(
                    (1, 1, lado - 2, lado - 2), radius=lay.f(12),
                    outline=(ROXO if ativo else (245, 196, 81)) + (255,),
                    width=max(2, lay.f(3) if ativo else lay.f(2)))
            caminho = caminho_retrato(nome, pasta)
            if caminho:
                try:
                    arte = retrato_pronto(caminho, lado - lay.f(10), lado - lay.f(10))
                    img.alpha_composite(arte, ((lado - arte.width) // 2,
                                               lado - lay.f(5) - arte.height))
                except Exception as erro:
                    falha("[Ranking] retrato", erro)
            if not ativo:
                veu = Image.new("RGBA", img.size, (20, 15, 40, 90))
                img = Image.alpha_composite(img, veu)
            tag = f"ret_{nome}"
            self._fotos[f"ret_{nome}"] = ImageTk.PhotoImage(img)
            self.create_image(x, y, anchor="nw", image=self._fotos[f"ret_{nome}"],
                              tags=("retratos", tag))
            self._texto(x + lado / 2, y + lado + lay.f(3), nome, lay.f(10),
                        "#ffffff" if ativo else TEXTO_INATIVO,
                        "bold" if ativo else "normal", anchor="n",
                        tags=("retratos", tag))
            if not ativo:
                self.tag_bind(tag, "<Button-1>",
                              lambda e, n=nome: self.trocar_personagem(n))
                self.tag_bind(tag, "<Enter>", lambda e: self.configure(cursor="hand2"))
                self.tag_bind(tag, "<Leave>", lambda e: self.configure(cursor=""))
        return y0 + linhas * (altura + gap) - gap

    def trocar_personagem(self, nome):
        self.personagem = nome
        self._desenhar_retratos()
        fim = self._desenhar_placar() + self._lay.f(40)
        largura, altura = self._tamanho
        self.configure(scrollregion=(0, 0, largura, max(altura, fim)))
        self.barra.fixar()

    # --------------------------------------------------------- placar
    def _desenhar_placar(self):
        """O placar completo do personagem escolhido (todas as contas)."""
        from card_personagem import caminho_retrato, retrato_pronto
        from dados_app import abreviar_ataque, formatar_percentual, soma_no_milhar
        import caminhos
        import guilda
        import ranking
        lay = self._lay
        self.delete("placar")
        placar = ranking.placar_do_personagem(self.dados["personagens"],
                                              self.personagem)
        contas = self._contas()
        meu = getattr(self.app, "user_id", None)
        x0, largura, y = self._x0, self._largura_util, self._y_placar
        arte_l = lay.f(190)
        linha_a = lay.f(46)
        cabecalho_a = lay.f(92)
        painel_a = max(lay.f(250), cabecalho_a + lay.f(30)
                       + linha_a * max(1, len(placar)) + lay.f(16))
        self._fotos["placar_painel"] = ImageTk.PhotoImage(
            _vidro(largura, painel_a, lay.f(16)))
        self.create_image(x0, y, anchor="nw", image=self._fotos["placar_painel"],
                          tags=("placar",))
        # a arte grande do personagem
        pasta = os.path.join(caminhos.assets_dir(), "assets", "personagens")
        caminho = caminho_retrato(self.personagem, pasta)
        if caminho:
            try:
                arte = retrato_pronto(caminho, arte_l, lay.f(230))
                self._fotos["placar_arte"] = ImageTk.PhotoImage(arte)
                self.create_image(x0 + lay.f(16) + arte_l / 2, y + lay.f(16),
                                  anchor="n", image=self._fotos["placar_arte"],
                                  tags=("placar",))
            except Exception as erro:
                falha("[Ranking] arte do personagem", erro)
        tx = x0 + arte_l + lay.f(40)
        tw = largura - (tx - x0) - lay.f(20)
        self._texto(tx, y + lay.f(18), self.personagem, lay.f(28), "#ffffff",
                    "bold", familia="Segoe UI Black", tags=("placar",))
        if placar:
            lider = placar[0]
            nome = guilda.nome_do_perfil(contas.get(lider.get("user_id")))
            self._texto(tx, y + lay.f(62),
                        f"Campeão: {nome}   ⚡ {_milhar(lider.get('poder'))}",
                        lay.f(14), "#f5c451", "bold", tags=("placar",))
        else:
            self._texto(tx, y + lay.f(62), "Ninguém com Ataque Total ainda.",
                        lay.f(14), tv.CORES["suave"], tags=("placar",))
            return y + painel_a

        # colunas (fracoes da largura da tabela)
        colunas = [("#", 0.0, "w"), ("JOGADOR", 0.07, "w"),
                   ("ATAQUE TOTAL", 0.36, "w"), ("SOMA", 0.62, "center"),
                   ("ATQ", 0.71, "center"), ("ESP", 0.79, "center"),
                   ("CRIT", 0.87, "center"), ("D.CRIT", 0.96, "center")]
        hy = y + cabecalho_a + lay.f(8)
        for rotulo, fracao, ancora in colunas:
            self._texto(tx + tw * fracao, hy, rotulo, lay.f(10),
                        tv.CORES["suave"], "bold", anchor=ancora,
                        tags=("placar",))
        maior = max(1, max(_num_seguro(p.get("poder")) for p in placar))
        ly = hy + lay.f(16)
        for indice, linha in enumerate(placar):
            posicao = indice + 1
            medalha = guilda.medalha(posicao)
            conta = contas.get(linha.get("user_id"), {})
            voce = linha.get("user_id") == meu
            meio = ly + linha_a / 2
            if voce:
                fundo = _pilula(tw + lay.f(12), linha_a - lay.f(6), LILAS + (60,))
                self._fotos["placar_voce"] = ImageTk.PhotoImage(fundo)
                self.create_image(tx - lay.f(8), ly + lay.f(3), anchor="nw",
                                  image=self._fotos["placar_voce"], tags=("placar",))
            cor_pos = ("#f5c451" if medalha == "ouro" else "#d4d4d8"
                       if medalha == "prata" else "#d08a4e" if medalha
                       else tv.CORES["suave"])
            self._texto(tx, meio, f"{posicao}º", lay.f(14), cor_pos, "bold",
                        anchor="w", tags=("placar",))
            lado = lay.f(30)
            self._fotos[f"placar_foto_{indice}"] = ImageTk.PhotoImage(
                avatar_de(conta, lado))
            self.create_image(tx + tw * 0.07, meio, anchor="w",
                              image=self._fotos[f"placar_foto_{indice}"],
                              tags=("placar",))
            nome = guilda.nome_do_perfil(conta) + ("  (você)" if voce else "")
            nome_x = tx + tw * 0.07 + lado + lay.f(8)
            fonte = tkfont.Font(family="Segoe UI", size=lay.f(13), weight="bold")
            limite = tx + tw * 0.35 - nome_x
            while nome and fonte.measure(nome) > limite:
                nome = nome[:-2] + "…" if len(nome) > 2 else ""
            self._texto(nome_x, meio, nome, lay.f(13), "#ffffff", "bold",
                        anchor="w", tags=("placar",))
            self._texto(tx + tw * 0.36, meio - lay.f(8),
                        _milhar(linha.get("poder")), lay.f(14),
                        "#f5c451" if posicao == 1 else "#ffffff", "bold",
                        anchor="w", tags=("placar",))
            self._fotos[f"placar_barra_{indice}"] = ImageTk.PhotoImage(_barra(
                tw * 0.22, lay.f(6), _num_seguro(linha.get("poder")) / maior,
                COR_DEGRAU[medalha][1] if medalha else ROXO))
            self.create_image(tx + tw * 0.36, meio + lay.f(10), anchor="w",
                              image=self._fotos[f"placar_barra_{indice}"],
                              tags=("placar",))
            status = ranking.status_do_personagem(linha)
            soma = soma_no_milhar(status["ataque"], status["ataque_especial"])
            chip = _pilula(lay.f(44), lay.f(22), (109, 40, 217, 255))
            self._fotos[f"placar_soma_{indice}"] = ImageTk.PhotoImage(chip)
            self.create_image(tx + tw * 0.62, meio, anchor="center",
                              image=self._fotos[f"placar_soma_{indice}"],
                              tags=("placar",))
            self._texto(tx + tw * 0.62, meio, soma, lay.f(12), "#ffffff", "bold",
                        anchor="center", tags=("placar",))
            for chave, fracao in (("ataque", 0.71), ("ataque_especial", 0.79)):
                self._texto(tx + tw * fracao, meio, abreviar_ataque(status[chave]),
                            lay.f(12), "#ffffff", anchor="center", tags=("placar",))
            for chave, fracao in (("critico", 0.87), ("dano_critico", 0.96)):
                self._texto(tx + tw * fracao, meio, formatar_percentual(status[chave]),
                            lay.f(12), "#ffffff", anchor="center", tags=("placar",))
            ly += linha_a
        return y + painel_a


def _num_seguro(valor):
    from dados_app import _num
    return max(0, _num(valor))

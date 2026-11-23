# -*- coding: utf-8 -*-
"""
Painel lateral de DOACAO (o drawer).

O botao "Apoiar" do cabecalho abre este painel: ele desliza da direita
por cima da tela principal (sem fechar o app) e mostra como apoiar o
projeto:

  - emblema do app;
  - texto curto ("este app e de graca e vive de doacoes");
  - valores sugeridos (o Pix e copia e cola: quem escolhe o valor no app
    do banco);
  - QR Code da chave Pix + a chave em texto (botao "Copiar");
  - opcionalmente um link externo (assets/doacao/link.txt) que abre no
    navegador.

**Para mudar a chave Pix:** edite `assets/doacao/pix.txt` e rode
`assets/doacao/gerar_qr.py` (gera o QR de novo).
"""

import os
import subprocess
import sys
import webbrowser

import customtkinter as ctk
from PIL import Image

import caminhos
import pix_pagamento
import tema_visual as tv
from tkinter import TclError

from registro import falha

CORES = {
    "fundo": "#16112b",
    "painel": "#1e1a30",
    "painel_borda": "#3a3159",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "roxo_hover": "#7c3aed",
    "verde": "#22c55e",
}

LARGURA = 640          # o QR (360) + a coluna da chave
VALORES = [("R$ 5", "O gelo"), ("R$ 20", "Humilde"),
           ("R$ 50", "Ganha VIP <3")]


def pasta_doacao():
    return os.path.join(caminhos.assets_dir(), "assets", "doacao")


def chave_pix():
    """O payload "copia e cola" do Pix.

    Montado na hora a partir de `assets/doacao/pix.txt` (a fonte da
    verdade). Se o `pix_payload.txt` existir, ele e conferido: quando a
    chave mudou e o arquivo ainda e o velho, o payload antigo e
    descartado e o novo e usado.
    """
    dados = pix_pagamento.payload()
    if not dados:
        return ""
    caminho = os.path.join(pasta_doacao(), "pix_payload.txt")
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            velho = arquivo.read().strip()
    except Exception:
        velho = ""
    if velho and velho != dados:
        # o arquivo gerado ainda e da chave antiga: usa o payload novo
        pass
    return dados


def link_externo():
    """Link opcional de uma pagina de apoio (assets/doacao/link.txt)."""
    caminho = os.path.join(pasta_doacao(), "link.txt")
    try:
        with open(caminho, "r", encoding="utf-8") as arquivo:
            return arquivo.read().strip()
    except FileNotFoundError:
        return ""                 # sem link configurado (opcional)
    except Exception:
        falha("ler o link de doacao")
        return ""


def copiar_para_area(texto):
    """Copia um texto para a area de transferencia (Windows)."""
    try:
        subprocess.run(["clip"], input=texto.encode("utf-8"), check=False)
        return True
    except Exception:
        try:
            self_clip = None
            raiz = ctk.CTk()
            raiz.withdraw()
            raiz.clipboard_clear()
            raiz.clipboard_append(texto)
            raiz.update()
            raiz.after(150, raiz.destroy)
            return True
        except Exception:
            falha("copiar para a area de transferencia")
            return False


def _quadro_do_ico(caminho, lado=256):
    """Abre um .ico e devolve o quadro maior (o .ico tem varios tamanhos)."""
    imagem = Image.open(caminho)
    try:
        return imagem.ico.getimage((lado, lado)).convert("RGBA")
    except Exception:
        falha("ler quadro do .ico")
        return imagem.convert("RGBA")


class PainelDoacao(ctk.CTkToplevel):
    """O drawer de doacao (desliza da direita)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Apoie o Caminho da Maestria")
        caminhos.aplicar_icone(self)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=CORES["fundo"])

        self._montar()
        self._posicionar(final=False)
        self.after(30, self._animar_entrada)

    # ------------------------------------------------------------- UI ------
    def _montar(self):
        # --- cabecalho do painel -------------------------------------------
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(16, 0))

        emblema = os.path.join(caminhos.assets_dir(), "assets", "app.ico")
        if not os.path.exists(emblema):
            emblema = os.path.join(caminhos.assets_dir(), "assets",
                                   "login.png")
        if os.path.exists(emblema):
            try:
                foto = _quadro_do_ico(emblema)
                foto = foto.resize((46, 46), Image.LANCZOS)
                self._foto_emblema = ctk.CTkImage(light_image=foto,
                                                   dark_image=foto, size=(46, 46))
                ctk.CTkLabel(topo, text="", image=self._foto_emblema,
                             width=46, height=46).pack(side="left")
            except Exception:
                falha("desenhar o emblema da doacao")

        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(textos, text="APOIE O PROJETO",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w")
        ctk.CTkLabel(textos, text="Caminho da Maestria",
                     font=ctk.CTkFont(size=19, weight="bold"),
                     text_color=CORES["texto"]).pack(anchor="w")

        ctk.CTkButton(topo, text="\u2715", width=32, height=32,
                      corner_radius=8, fg_color="transparent",
                      hover_color="#2f2949", text_color=CORES["suave"],
                      font=ctk.CTkFont(size=15),
                      command=self.fechar).pack(side="right")

        # --- texto -----------------------------------------------------------
        ctk.CTkLabel(
            self,
            text="Este app e de graca e sem anuncios. Se ele te ajuda no "
                 "acompanhamento dos seus personagens, um pixinho ajuda a "
                 "manter o projeto vivo (servidor, dominio e manutencao).",
            font=ctk.CTkFont(size=13), text_color=CORES["suave"],
            wraplength=LARGURA - 300, justify="left",
        ).pack(anchor="w", padx=22, pady=(18, 4))

        # --- valores sugeridos ----------------------------------------------
        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=22, pady=(14, 2))
        for i, (valor, legenda) in enumerate(VALORES):
            caixa = ctk.CTkFrame(linha, fg_color=CORES["painel"],
                                 width=190, corner_radius=14, border_width=1,
                                 border_color=CORES["painel_borda"])
            caixa.pack(side="left", padx=(0 if i == 0 else 8, 0))
            # a largura dos rotulos e o que impoe a largura do cartao
            ctk.CTkLabel(caixa, text=valor, width=170,
                         font=ctk.CTkFont(size=22, weight="bold"),
                         text_color=CORES["texto"]).pack(pady=(14, 0))
            ctk.CTkLabel(caixa, text=legenda, width=170,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=CORES["suave"]).pack(pady=(0, 14))

        # --- QR + chave ------------------------------------------------------
        # o QR so e legivel a partir de 200 px (ele tem o payload longo),
        # entao ele fica grande e centralizado, com a chave abaixo
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="x", padx=22, pady=(16, 0))

        # o QR so e legivel no tamanho original (360 px): encolher ele
        # embaralha os modulos e o celular nao le
        LADO_QR = 360
        foto = pix_pagamento.qr_imagem(LADO_QR)
        if foto is None:
            reserva = os.path.join(pasta_doacao(), "qr_pix.png")
            if os.path.exists(reserva):
                try:
                    foto = Image.open(reserva).convert("RGB").resize(
                        (LADO_QR, LADO_QR), Image.LANCZOS)
                except Exception:
                    foto = None
        if foto is not None:
            try:
                self._foto_qr = ctk.CTkImage(light_image=foto, dark_image=foto,
                                             size=(LADO_QR, LADO_QR))
                ctk.CTkLabel(corpo, text="", image=self._foto_qr,
                             width=LADO_QR, height=LADO_QR).pack(side="left")
            except Exception:
                falha("desenhar o QR Code")

        lado = ctk.CTkFrame(corpo, fg_color="transparent")
        lado.pack(side="left", fill="both", expand=True, padx=(18, 0))

        ctk.CTkLabel(lado, text="PIX COPIA E COLA",
                     font=ctk.CTkFont(size=10, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w")

        self.caixa_chave = ctk.CTkFrame(lado, fg_color=CORES["painel"],
                                        corner_radius=8, border_width=1,
                                        border_color=CORES["painel_borda"])
        self.caixa_chave.pack(fill="x", pady=(8, 0))
        self.rotulo_chave = ctk.CTkLabel(
            self.caixa_chave, text="", anchor="w", justify="left",
            wraplength=LARGURA - 430,
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color=CORES["texto"])
        self.rotulo_chave.pack(fill="both", expand=True, padx=10, pady=8)
        self._preencher_chave()

        self.botao_copiar = ctk.CTkButton(
            lado, text="Copiar chave Pix", height=34, corner_radius=8,
            fg_color=CORES["roxo"], hover_color=CORES["roxo_hover"],
            text_color="#ffffff", font=ctk.CTkFont(size=13, weight="bold"),
            command=self.copiar_chave)
        self.botao_copiar.pack(fill="x", pady=(10, 0))

        link = link_externo()
        if link:
            ctk.CTkButton(
                lado, text="Abrir pagina de apoio", height=34, corner_radius=8,
                fg_color="transparent", hover_color="#2f2949",
                border_width=1, border_color=CORES["painel_borda"],
                text_color=CORES["texto"], font=ctk.CTkFont(size=13),
                command=lambda: self._abrir_link(link),
            ).pack(fill="x", pady=(8, 0))

        ctk.CTkLabel(
            self,
            text="Prefere outro valor? Qualquer quantia ajuda.  ·  Pix  ·  "
                 "Cartao",
            font=ctk.CTkFont(size=11), text_color=CORES["suave"],
        ).pack(anchor="w", padx=22, pady=(14, 0))

        # --- o que o apoio cobre -------------------------------------------
        ctk.CTkLabel(
            self, text="O QUE O SEU APOIO COBRE",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color=CORES["roxo"],
        ).pack(anchor="w", padx=22, pady=(22, 8))

        for texto in ("Servidor e banco de dados (Supabase)",
                      "Dominio e o endereco da pagina de apoio",
                      "Tempo de manutencao e as novas atualizacoes"):
            linha = ctk.CTkFrame(self, fg_color="transparent")
            linha.pack(fill="x", padx=22, pady=3)
            ctk.CTkLabel(linha, text="\u2713", width=18,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=CORES["verde"]).pack(side="left")
            ctk.CTkLabel(linha, text=texto, anchor="w",
                         font=ctk.CTkFont(size=12),
                         text_color=CORES["suave"]).pack(side="left", fill="x",
                                                         expand=True)

        # --- rodape -----------------------------------------------------------
        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", side="bottom", padx=22, pady=(0, 18))
        self.status = ctk.CTkLabel(rodape, text="",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=CORES["verde"])
        self.status.pack(side="left")
        ctk.CTkButton(rodape, text="Fechar", width=96, height=32,
                      corner_radius=8, fg_color="transparent",
                      hover_color="#2f2949", border_width=1,
                      border_color=CORES["painel_borda"],
                      text_color=CORES["suave"],
                      font=ctk.CTkFont(size=12),
                      command=self.fechar).pack(side="right")

    # --------------------------------------------------------- acoes --------
    def _preencher_chave(self):
        chave = chave_pix()
        if not chave:
            self.rotulo_chave.configure(
                text="sem chave (edite assets/doacao/pix.txt)")
            return
        try:
            self.rotulo_chave.configure(text=chave)
        except TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("mostrar a chave Pix")

    def copiar_chave(self):
        chave = chave_pix()
        if not chave:
            self._avisar("sem chave para copiar", erro=True)
            return
        if copiar_para_area(chave):
            self._avisar("chave copiada! cole no Pix")
        else:
            self._avisar("nao consegui copiar", erro=True)

    def _abrir_link(self, link):
        try:
            webbrowser.open(link)
        except Exception:
            self._avisar("nao consegui abrir o navegador", erro=True)

    def _avisar(self, texto, erro=False):
        self.status.configure(text=texto,
                              text_color=CORES["erro"] if erro
                              else CORES["verde"])
        self.after(3200, lambda: self.status.configure(text=""))

    # ------------------------------------------------------- animacao -------
    def _posicao_final(self):
        """(x, y) onde o painel fica quando aberto."""
        try:
            x = self.app.winfo_rootx() + self.app.winfo_width() - LARGURA
            y = self.app.winfo_rooty()
            altura = min(self.app.winfo_height(), 920)
            return x, y, altura
        except TclError:
            return 100, 100, 700
        except Exception:
            falha("posicionar o painel de doacao")
            return 100, 100, 700

    def _posicionar(self, final=True):
        x, y, altura = self._posicao_final()
        if not final:
            x = x + LARGURA + 10        # comeca fora da tela
        self.geometry(f"{LARGURA}x{altura}+{int(x)}+{int(y)}")

    def _animar_entrada(self):
        """Desliza da direita para dentro."""
        alvo = self._posicao_final()

        def passo():
            if not self.winfo_exists():
                return
            atual = self.winfo_x()
            novo = atual - (atual - alvo[0]) * 0.28
            if abs(novo - alvo[0]) < 2:
                self.geometry(f"{LARGURA}x{alvo[2]}+{int(alvo[0])}+"
                              f"{int(alvo[1])}")
                return
            self.geometry(f"{LARGURA}x{alvo[2]}+{int(novo)}+{int(alvo[1])}")
            self.after(16, passo)

        passo()

    def fechar(self):
        try:
            self.destroy()
        except TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("fechar o painel de doacao")

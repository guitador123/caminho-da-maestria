# -*- coding: utf-8 -*-
"""
Painel lateral de DOACAO (o drawer).

O botao "Apoiar" do cabecalho abre este painel: ele desliza da direita
por cima da tela principal (sem fechar o app) e mostra como apoiar o
projeto, numa coluna so:

  - emblema + titulo;
  - texto curto ("este app e de graca e vive de doacoes");
  - valores sugeridos (o Pix e estatico: quem escolhe o valor e o app do
    banco);
  - QR Code (no tamanho nativo, sem esticar) + para quem vai o Pix;
  - o Pix copia e cola + botao "Copiar codigo Pix";
  - o que o apoio cobre.

Esc ou o X fecham.

**Para mudar a chave Pix:** edite `assets/doacao/pix.txt` e rode
`python assets/doacao/gerar_qr.py --forcar` (gera o QR e o copia e cola).
"""

import os
import subprocess
import webbrowser
from tkinter import TclError

import customtkinter as ctk
from PIL import Image

import caminhos
import pix_pagamento
from registro import falha

CORES = {
    "fundo": "#16112b",
    "painel": "#1e1a30",
    "painel_borda": "#3a3159",
    "hover": "#2f2949",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "roxo_hover": "#7c3aed",
    "verde": "#22c55e",
    "erro": "#fb7185",
}

LARGURA = 480          # largura do painel
MARGEM = 24            # margem lateral (todas as secoes alinham nela)
LADO_QR = 250          # o QR e gerado (gerar_qr.py) para caber neste tamanho
VALORES = [("R$ 5", "O gelo"), ("R$ 20", "Humilde"),
           ("R$ 50", "Ganha VIP <3")]


def pasta_doacao():
    return os.path.join(caminhos.assets_dir(), "assets", "doacao")


def chave_pix():
    """O Pix "copia e cola" (o payload de `assets/doacao/pix_payload.txt`;
    sem ele, montado na hora a partir da chave do `pix.txt`)."""
    return pix_pagamento.payload()


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
    """Copia um texto para a area de transferencia do Windows (clip.exe,
    sem abrir janela). O conteudo continua la depois que o app fecha."""
    try:
        subprocess.run(["clip"], input=texto.encode("utf-8"), check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
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


def _imagem_do_qr():
    """O QR que o painel mostra, no tamanho NATIVO (sem esticar)."""
    foto = pix_pagamento.qr_imagem(0)          # 0 = nao redimensiona
    if foto is None:
        reserva = os.path.join(pasta_doacao(), "qr_pix.png")
        if os.path.exists(reserva):
            try:
                foto = Image.open(reserva).convert("RGB")
            except Exception:
                falha("abrir o QR de reserva")
    if foto is not None and foto.width > LADO_QR:
        # imagem antiga, maior que o painel: reduz sem misturar os pixels
        foto = foto.resize((LADO_QR, LADO_QR), Image.NEAREST)
    return foto


class PainelDoacao(ctk.CTkToplevel):
    """O drawer de doacao (desliza da direita)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Apoie o Caminho da Maestria")
        caminhos.aplicar_icone(self)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=CORES["fundo"], border_width=1,
                       border_color=CORES["painel_borda"])
        self.bind("<Escape>", lambda _e: self.fechar())

        self._montar()
        self._posicionar(final=False)
        self.after(30, self._animar_entrada)
        self.after(60, self.focus_force)

    # ------------------------------------------------------------- UI ------
    def _titulo_secao(self, pai, texto, topo=16):
        ctk.CTkLabel(pai, text=texto, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=MARGEM,
                                                   pady=(topo, 8))

    def _montar(self):
        largura_util = LARGURA - 2 * MARGEM

        # --- cabecalho -----------------------------------------------------
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=MARGEM, pady=(16, 0))

        emblema = os.path.join(caminhos.assets_dir(), "assets", "app.ico")
        if os.path.exists(emblema):
            try:
                foto = _quadro_do_ico(emblema).resize((44, 44), Image.LANCZOS)
                self._foto_emblema = ctk.CTkImage(light_image=foto,
                                                   dark_image=foto, size=(44, 44))
                ctk.CTkLabel(topo, text="", image=self._foto_emblema,
                             width=44, height=44).pack(side="left")
            except Exception:
                falha("desenhar o emblema da doacao")

        textos = ctk.CTkFrame(topo, fg_color="transparent")
        textos.pack(side="left", padx=(12, 0))
        ctk.CTkLabel(textos, text="APOIE O PROJETO",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w")
        ctk.CTkLabel(textos, text="Caminho da Maestria",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CORES["texto"]).pack(anchor="w")

        ctk.CTkButton(topo, text="✕", width=32, height=32,
                      corner_radius=8, fg_color="transparent",
                      hover_color=CORES["hover"], text_color=CORES["suave"],
                      font=ctk.CTkFont(size=15),
                      command=self.fechar).pack(side="right", anchor="n")

        # --- conteudo (rola com a roda do mouse se a janela for baixa) ----
        self.rolagem = ctk.CTkScrollableFrame(
            self, fg_color="transparent", corner_radius=0,
            scrollbar_button_color=CORES["painel_borda"],
            scrollbar_button_hover_color=CORES["roxo"])
        self.rolagem.pack(fill="both", expand=True, padx=(1, 1), pady=(4, 1))
        corpo = self.rolagem
        self.after(400, self._ajustar_rolagem)

        ctk.CTkLabel(
            corpo,
            text="Este app é de graça e sem anúncios. Se ele te ajuda a "
                 "acompanhar seus personagens, um pixinho ajuda a manter o "
                 "projeto vivo.",
            font=ctk.CTkFont(size=13), text_color=CORES["suave"],
            wraplength=largura_util, justify="left",
        ).pack(anchor="w", padx=MARGEM, pady=(4, 0))

        # --- valores sugeridos (3 colunas iguais) --------------------------
        linha = ctk.CTkFrame(corpo, fg_color="transparent")
        linha.pack(fill="x", padx=MARGEM, pady=(14, 0))
        for coluna, (valor, legenda) in enumerate(VALORES):
            linha.grid_columnconfigure(coluna, weight=1, uniform="valor")
            caixa = ctk.CTkFrame(linha, fg_color=CORES["painel"],
                                 corner_radius=12, border_width=1,
                                 border_color=CORES["painel_borda"])
            caixa.grid(row=0, column=coluna, sticky="nsew",
                       padx=(0 if coluna == 0 else 5,
                             0 if coluna == len(VALORES) - 1 else 5))
            ctk.CTkLabel(caixa, text=valor,
                         font=ctk.CTkFont(size=20, weight="bold"),
                         text_color=CORES["texto"]).pack(pady=(12, 0))
            ctk.CTkLabel(caixa, text=legenda,
                         font=ctk.CTkFont(size=12),
                         text_color=CORES["suave"]).pack(pady=(0, 12))
        ctk.CTkLabel(corpo, text="Qualquer valor ajuda: você escolhe a quantia "
                                "no app do banco.",
                     font=ctk.CTkFont(size=11), text_color=CORES["suave"]
                     ).pack(anchor="w", padx=MARGEM, pady=(8, 0))

        # --- QR Code -------------------------------------------------------
        self._titulo_secao(corpo, "PAGUE COM PIX")
        cartao = ctk.CTkFrame(corpo, fg_color=CORES["painel"], corner_radius=14,
                              border_width=1, border_color=CORES["painel_borda"])
        cartao.pack(fill="x", padx=MARGEM)

        foto = _imagem_do_qr()
        if foto is not None:
            try:
                # o QR ja tem a margem branca; a moldura branca arredondada
                # so acompanha o contorno
                moldura = ctk.CTkFrame(cartao, fg_color="#ffffff",
                                       corner_radius=12)
                moldura.pack(pady=(16, 0))
                self._foto_qr = ctk.CTkImage(light_image=foto,
                                             dark_image=foto, size=foto.size)
                ctk.CTkLabel(moldura, text="", image=self._foto_qr,
                             width=foto.width, height=foto.height
                             ).pack(padx=2, pady=2)
            except Exception:
                falha("desenhar o QR Code")

        ctk.CTkLabel(cartao, text="Escaneie com o app do seu banco",
                     font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=CORES["texto"]).pack(pady=(10, 0))
        ctk.CTkLabel(cartao, text=f"Para: {pix_pagamento.nome()}",
                     font=ctk.CTkFont(size=12), text_color=CORES["suave"]
                     ).pack(pady=(0, 12))

        # --- copia e cola --------------------------------------------------
        self._titulo_secao(corpo, "OU USE O PIX COPIA E COLA")
        self.caixa_chave = ctk.CTkFrame(corpo, fg_color=CORES["painel"],
                                        corner_radius=10, border_width=1,
                                        border_color=CORES["painel_borda"])
        self.caixa_chave.pack(fill="x", padx=MARGEM)
        self.rotulo_chave = ctk.CTkLabel(
            self.caixa_chave, text="", anchor="w", justify="left",
            wraplength=largura_util - 28,
            font=ctk.CTkFont(family="Consolas", size=11),
            text_color=CORES["texto"])
        self.rotulo_chave.pack(fill="x", padx=14, pady=8)
        self._preencher_chave()

        self.botao_copiar = ctk.CTkButton(
            corpo, text="Copiar código Pix", height=40, corner_radius=10,
            fg_color=CORES["roxo"], hover_color=CORES["roxo_hover"],
            text_color="#ffffff", font=ctk.CTkFont(size=14, weight="bold"),
            command=self.copiar_chave)
        self.botao_copiar.pack(fill="x", padx=MARGEM, pady=(10, 0))
        # o aviso aparece logo abaixo do botao (perto de quem clicou)
        self.status = ctk.CTkLabel(corpo, text="", height=20,
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=CORES["verde"])
        self.status.pack(pady=(4, 0))

        link = link_externo()
        if link:
            ctk.CTkButton(
                corpo, text="Abrir página de apoio", height=36, corner_radius=10,
                fg_color="transparent", hover_color=CORES["hover"],
                border_width=1, border_color=CORES["painel_borda"],
                text_color=CORES["texto"], font=ctk.CTkFont(size=13),
                command=lambda: self._abrir_link(link),
            ).pack(fill="x", padx=MARGEM, pady=(4, 0))

        # --- o que o apoio cobre (uma frase, sem lista) --------------------
        ctk.CTkLabel(
            corpo,
            text="Seu apoio paga o servidor (Supabase), o domínio e o tempo "
                 "de manutenção e das novas atualizações. Obrigado!",
            font=ctk.CTkFont(size=12), text_color=CORES["suave"],
            wraplength=largura_util, justify="left",
        ).pack(anchor="w", padx=MARGEM, pady=(6, 16))

    def _ajustar_rolagem(self):
        """Esconde a barra de rolagem quando tudo cabe na janela."""
        try:
            barra = getattr(self.rolagem, "_scrollbar", None)
            visivel = getattr(self.rolagem, "_parent_canvas", self.rolagem)
            # reqheight do quadro interno ja conta os espacamentos (pady)
            if barra is not None and \
                    self.rolagem.winfo_reqheight() <= visivel.winfo_height():
                barra.grid_remove()
        except TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("ajustar a rolagem do painel de doacao")

    # --------------------------------------------------------- acoes --------
    def _preencher_chave(self):
        chave = chave_pix()
        texto = chave or "sem chave (edite assets/doacao/pix.txt)"
        try:
            self.rotulo_chave.configure(text=texto)
        except TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("mostrar a chave Pix")

    def copiar_chave(self):
        chave = chave_pix()
        if not chave:
            self._avisar("Sem código Pix para copiar.", erro=True)
            return
        # no Windows o clip.exe (sem janela) e o principal: o que o Tk copia
        # some da area de transferencia quando o app fecha
        copiou = os.name == "nt" and copiar_para_area(chave)
        if not copiou:
            try:
                self.clipboard_clear()
                self.clipboard_append(chave)
                self.update()
                copiou = True
            except TclError:
                copiou = False
        if copiou:
            self._avisar("Código copiado! Cole no Pix do seu banco.")
        else:
            self._avisar("Não consegui copiar. Selecione o código acima.",
                         erro=True)

    def _abrir_link(self, link):
        try:
            webbrowser.open(link)
        except Exception:
            falha("abrir a pagina de apoio")
            self._avisar("Não consegui abrir o navegador.", erro=True)

    def _avisar(self, texto, erro=False):
        self.status.configure(text=texto,
                              text_color=CORES["erro"] if erro
                              else CORES["verde"])
        self.after(3200, lambda: self.status.winfo_exists()
                   and self.status.configure(text=""))

    # ------------------------------------------------------- animacao -------
    def _posicao_final(self):
        """(x, y, altura) de onde o painel fica quando aberto."""
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

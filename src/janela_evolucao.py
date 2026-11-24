# -*- coding: utf-8 -*-
"""
A janela "Evolucao semanal": mostra a pagina (uma imagem, ver
pagina_evolucao.py) com rolagem e permite exportar:

  - "Copiar imagem": vai para a area de transferencia (Ctrl+V no Discord);
  - "Salvar PNG": grava o arquivo onde voce escolher.

Esc ou "Fechar" fecham.
"""

import os
from datetime import datetime
from tkinter import TclError, filedialog

import customtkinter as ctk
from PIL import ImageTk

import caminhos
import pagina_evolucao
from area_transferencia import copiar_imagem
from registro import falha
from versao_app import VERSAO

CORES = {
    "fundo": "#16112b",
    "barra": "#1e1a30",
    "borda": "#3a3159",
    "hover": "#2f2949",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "roxo_hover": "#7c3aed",
    "verde": "#34d399",
    "erro": "#fb7185",
}


class JanelaEvolucao(ctk.CTkToplevel):

    def __init__(self, app, semanas, atual, destaque=None, nick=""):
        super().__init__(app)
        self.app = app
        self.title("Evolução semanal - Caminho da Maestria")
        caminhos.aplicar_icone(self)
        self.configure(fg_color=CORES["fundo"])
        self.imagem = pagina_evolucao.montar(semanas, atual, destaque=destaque,
                                             nick=nick, versao=VERSAO)
        self._montar()
        self._posicionar()
        self.bind("<Escape>", lambda _e: self.fechar())
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.after(80, self._trazer)

    # ------------------------------------------------------------------ UI
    def _montar(self):
        barra = ctk.CTkFrame(self, fg_color=CORES["barra"], corner_radius=0,
                             height=60)
        barra.pack(fill="x", side="top")
        barra.pack_propagate(False)
        ctk.CTkLabel(barra, text="Evolução semanal",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left", padx=20)
        self.status = ctk.CTkLabel(barra, text="",
                                   font=ctk.CTkFont(size=12, weight="bold"),
                                   text_color=CORES["verde"])
        self.status.pack(side="left", padx=8)

        ctk.CTkButton(barra, text="Fechar", width=90, height=34,
                      corner_radius=8, fg_color="transparent",
                      hover_color=CORES["hover"], border_width=1,
                      border_color=CORES["borda"], text_color=CORES["suave"],
                      command=self.fechar).pack(side="right", padx=(8, 20))
        ctk.CTkButton(barra, text="Salvar PNG", width=110, height=34,
                      corner_radius=8, fg_color="transparent",
                      hover_color=CORES["hover"], border_width=1,
                      border_color=CORES["borda"], text_color=CORES["texto"],
                      command=self.salvar_png).pack(side="right", padx=4)
        ctk.CTkButton(barra, text="Copiar imagem", width=140, height=34,
                      corner_radius=8, fg_color=CORES["roxo"],
                      hover_color=CORES["roxo_hover"], text_color="#ffffff",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.copiar).pack(side="right", padx=4)

        # a pagina (imagem) num canvas que rola
        corpo = ctk.CTkFrame(self, fg_color=CORES["fundo"], corner_radius=0)
        corpo.pack(fill="both", expand=True)
        self.canvas = ctk.CTkCanvas(corpo, bg=CORES["fundo"],
                                    highlightthickness=0)
        rolagem = ctk.CTkScrollbar(corpo, command=self.canvas.yview,
                                   button_color=CORES["borda"],
                                   button_hover_color=CORES["roxo"])
        self.canvas.configure(yscrollcommand=rolagem.set)
        rolagem.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self._foto = ImageTk.PhotoImage(self.imagem)
        self._item = self.canvas.create_image(0, 0, anchor="n",
                                              image=self._foto)
        self.canvas.configure(scrollregion=(0, 0, self.imagem.width,
                                            self.imagem.height))
        self.canvas.bind("<Configure>", self._centralizar)
        # so nesta janela (a Toplevel recebe a roda dos filhos dela)
        self.bind("<MouseWheel>", self._rolar)

    def _centralizar(self, evento):
        largura = max(evento.width, self.imagem.width)
        self.canvas.coords(self._item, largura / 2, 0)
        self.canvas.configure(scrollregion=(0, 0, largura,
                                            self.imagem.height))

    def _rolar(self, evento):
        try:
            self.canvas.yview_scroll(int(-evento.delta / 120) * 3, "units")
        except TclError:
            pass                      # janela ja fechada

    def _posicionar(self):
        try:
            largura = self.imagem.width + 40
            altura = min(900, self.app.winfo_height() + 40,
                         self.winfo_screenheight() - 80)
            x = self.app.winfo_rootx() + (self.app.winfo_width() - largura) // 2
            y = max(10, self.app.winfo_rooty() - 20)
            self.geometry(f"{largura}x{altura}+{max(0, x)}+{y}")
        except TclError:
            self.geometry("1120x860")

    def _trazer(self):
        try:
            self.lift()
            self.focus_force()
        except TclError:
            pass                      # janela ja fechada

    # -------------------------------------------------------------- acoes
    def copiar(self):
        if copiar_imagem(self.imagem):
            self._avisar("Imagem copiada! Cole no Discord com Ctrl+V.")
        else:
            self._avisar("Não consegui copiar. Use Salvar PNG.", erro=True)

    def salvar_png(self):
        nome = f"evolucao-semanal-{datetime.now():%Y-%m-%d}.png"
        caminho = filedialog.asksaveasfilename(
            parent=self, title="Salvar a página como imagem",
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
        self.status.configure(text=texto, text_color=CORES["erro"] if erro
                              else CORES["verde"])
        self.after(4000, lambda: self.status.winfo_exists()
                   and self.status.configure(text=""))

    def fechar(self):
        try:
            self.destroy()
        except TclError:
            pass                      # janela ja fechada

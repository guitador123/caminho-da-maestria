# -*- coding: utf-8 -*-
"""
Pergunta do Void na Missao Rapida (item 17): quantos andares a pessoa fez?

Abre ao marcar "Void (1, 2 e 3)" ou "Void 4" (no painel e no card). Cada
andar mostra quanto soma, e passar o mouse mostra o contador antes -> depois
("Void Unificado: 20 -> 30"). Teclas 1, 2 e 3 escolhem; Esc cancela.

A janela nao grava nada: ela so chama `ao_escolher(andar)` (o painel
guarda para o "Salvar"; o card marca e salva na hora).
"""

import tkinter as tk

import customtkinter as ctk

import caminhos
from dados_app import ANDARES_VOID, VOID_CONTADOR, novo_contador

CORES = {
    "fundo": "#141221",
    "painel": "#2a2440",
    "borda": "#4c4370",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "fraco": "#6f688f",
    "verde": "#7ef0b0",
    "roxo": "#8b5cf6",
}


class JanelaAndares(ctk.CTkToplevel):
    """1F / 2F / 3F do Void, com o antes e o depois do contador."""

    def __init__(self, app, nome, chave, rotulo, atual, ao_escolher):
        super().__init__(app)
        self.app = app
        self.chave = chave
        self.atual = atual
        self.ao_escolher = ao_escolher
        self.escolhido = None
        self.contador = VOID_CONTADOR[chave][1]
        self.title("Andares do Void")
        caminhos.aplicar_icone(self)
        self.geometry("380x250")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)

        ctk.CTkLabel(self, text=f"{nome}  ·  {rotulo}",
                     font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=CORES["texto"]).pack(anchor="w", padx=22,
                                                     pady=(18, 0))
        ctk.CTkLabel(self, text="Quantos andares você fez?",
                     font=ctk.CTkFont(size=13),
                     text_color=CORES["suave"]).pack(anchor="w", padx=22,
                                                     pady=(0, 10))

        linha = ctk.CTkFrame(self, fg_color="transparent")
        linha.pack(fill="x", padx=20)
        self.botoes = {}
        for indice, (andar, soma) in enumerate(ANDARES_VOID.items()):
            botao = ctk.CTkButton(
                linha, text=f"{andar}\n+{soma}", width=104, height=58,
                corner_radius=10, fg_color=CORES["painel"],
                hover_color="#3a3358", border_width=1,
                border_color=CORES["borda"], text_color=CORES["texto"],
                font=ctk.CTkFont(size=16, weight="bold"),
                command=lambda a=andar: self.escolher(a))
            botao.grid(row=0, column=indice, padx=4)
            botao.bind("<Enter>", lambda e, a=andar: self._mostrar(a))
            botao.bind("<Leave>", lambda e: self._mostrar(None))
            self.botoes[andar] = botao

        self.previa = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=13),
                                   text_color=CORES["texto"])
        self.previa.pack(anchor="w", padx=22, pady=(12, 0))
        self._mostrar(None)

        rodape = ctk.CTkFrame(self, fg_color="transparent")
        rodape.pack(fill="x", padx=22, pady=(8, 14))
        ctk.CTkLabel(rodape, text="teclas 1, 2, 3  ·  Esc cancela",
                     font=ctk.CTkFont(size=11),
                     text_color=CORES["fraco"]).pack(side="left")
        ctk.CTkButton(rodape, text="Cancelar", width=100, height=32,
                      corner_radius=8, fg_color="#2a2440",
                      hover_color="#372f52", text_color=CORES["texto"],
                      command=self.cancelar).pack(side="right")

        for indice, andar in enumerate(ANDARES_VOID, start=1):
            self.bind(str(indice), lambda e, a=andar: self.escolher(a))
            self.bind(f"<KP_{indice}>", lambda e, a=andar: self.escolher(a))
        self.bind("<Escape>", lambda e: self.cancelar())
        self.protocol("WM_DELETE_WINDOW", self.cancelar)
        self.after(60, self._focar)

    def _mostrar(self, andar):
        """'Void Unificado: 20 -> 30' (sem andar: so o valor de agora)."""
        if andar is None:
            texto = f"{self.contador} agora: {self.atual}"
        else:
            texto = (f"{self.contador}: {self.atual}  →  "
                     f"{novo_contador(self.atual, andar)}")
        try:
            self.previa.configure(text=texto)
        except tk.TclError:
            pass                      # janela ja fechada

    def _focar(self):
        try:
            self.lift()
            self.focus_force()
            self.grab_set()           # o resto do app espera a resposta
        except tk.TclError:
            pass                      # janela ja fechada

    def escolher(self, andar):
        if self.escolhido is not None:
            return                    # clique duplo / tecla repetida
        self.escolhido = andar
        self._fechar()
        self.ao_escolher(andar)

    def cancelar(self):
        self._fechar()

    def _fechar(self):
        try:
            self.grab_release()
        except tk.TclError:
            pass
        try:
            self.destroy()
        except tk.TclError:
            pass

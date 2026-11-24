# -*- coding: utf-8 -*-
"""
Janela de edicao do Nível do Chaser.

O nível do Chaser é **um valor por conta** (vale para todos os personagens):
ele fica na coluna `user_characters.nivel_chaser` e é gravado em todas as
linhas da conta.

Regra: número **inteiro >= 0**.

O erro de validação aparece **dentro** da janela (sem messagebox, para não
travar o app).
"""

import tkinter as tk

import customtkinter as ctk

import caminhos
from config_app import NIVEL_CHASER_MAXIMO
from registro import falha

CORES = {
    "fundo": "#141221",
    "painel": "#1e1a30",
    "painel_borda": "#332d4d",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "verde": "#22c55e",
    "erro": "#fb7185",
}

NIVEL_MINIMO = 0


def validar_nivel(texto):
    """'385' -> (385, None).  'abc' -> (None, 'mensagem de erro').

    Regra do usuario: numero INTEIRO de 0 a 999 (o maximo do jogo).
    """
    bruto = str(texto).strip()
    if bruto == "":
        return None, "Informe o nível do chaser."
    try:
        valor = int(bruto)
    except ValueError:
        return None, ("O nível do chaser é um número INTEIRO "
                      f"(ex.: {385}).")
    if valor < NIVEL_MINIMO:
        return None, f"O nível do chaser não pode ser menor que {NIVEL_MINIMO}."
    if valor > NIVEL_CHASER_MAXIMO:
        return None, f"O nível máximo do chaser é {NIVEL_CHASER_MAXIMO}."
    return valor, None


class JanelaNivelChaser(ctk.CTkToplevel):
    """Edição do nível do chaser (um valor por conta)."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Nível do Chaser")
        caminhos.aplicar_icone(self)
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)

        self.erro_var = tk.StringVar(value="")

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(20, 4))
        ctk.CTkLabel(topo, text="NÍVEL DO CHASER",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left")
        ctk.CTkLabel(topo, text="(um valor para toda a conta)",
                     font=ctk.CTkFont(size=12),
                     text_color=CORES["suave"]).pack(side="left", padx=10, pady=(8, 0))

        ctk.CTkLabel(self, text="Número inteiro maior ou igual a zero.",
                     font=ctk.CTkFont(size=13),
                     text_color=CORES["suave"]).pack(anchor="w", padx=22, pady=(6, 10))

        # aviso: a coluna do banco ainda nao existe (o SQL precisa ser rodado)
        if getattr(app, "usar_supabase", False) and \
                hasattr(app, "_nivel_no_banco") and not app._nivel_no_banco():
            ctk.CTkLabel(self, text="A coluna nivel_chaser ainda não existe no "
                                    "banco: rode sql/nivel_chaser.sql no "
                                    "Supabase para gravar.",
                         font=ctk.CTkFont(size=11),
                         text_color="#fbbf24", wraplength=350,
                         justify="left").pack(anchor="w", padx=22, pady=(0, 8))

        self.entrada = ctk.CTkEntry(self, width=320, height=46, corner_radius=10,
                                    fg_color=CORES["painel"],
                                    border_color=CORES["painel_borda"],
                                    border_width=2,
                                    text_color=CORES["texto"],
                                    font=ctk.CTkFont(size=22, weight="bold"),
                                    justify="center")
        self.entrada.pack(pady=(0, 8))
        self.entrada.insert(0, str(getattr(app, "nivel_chaser", 385)))
        self.entrada.bind("<Return>", lambda e: self._salvar())
        self.entrada.bind("<KP_Enter>", lambda e: self._salvar())

        ctk.CTkLabel(self, textvariable=self.erro_var,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CORES["erro"]).pack(anchor="w", padx=22, pady=(2, 6))

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=22, pady=(6, 20))
        ctk.CTkButton(barra, text="Cancelar", width=130, height=42,
                      corner_radius=10, fg_color="#2a2440", hover_color="#372f52",
                      text_color=CORES["texto"],
                      font=ctk.CTkFont(size=14),
                      command=self.destroy).pack(side="right")
        ctk.CTkButton(barra, text="Salvar", width=150, height=42, corner_radius=10,
                      fg_color=CORES["verde"], hover_color="#16a34a",
                      text_color="#08130d",
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._salvar).pack(side="right", padx=(0, 12))

        self.after(80, self._focar)

    def _focar(self):
        try:
            self.entrada.focus_set()
            self.entrada.select_range(0, "end")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("focar a janela do nivel")

    def _salvar(self):
        valor, erro = validar_nivel(self.entrada.get())
        if erro:
            self.erro_var.set(erro)
            self.entrada.focus_set()
            self.entrada.select_range(0, "end")
            return
        try:
            ok = self.app.definir_nivel_chaser(valor)
        except Exception as exc:
            self.erro_var.set(f"Erro ao salvar: {exc}")
            return
        if not ok:
            self.erro_var.set("Não foi possível salvar o nível do chaser.")
            return
        self.destroy()

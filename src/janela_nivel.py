# -*- coding: utf-8 -*-
"""
Janelas de edicao dos valores DA CONTA (um valor para todos os personagens):

  - Nível do Chaser      (user_characters.nivel_chaser, 0 a 999)
  - Coleção de cartas    (user_characters.colecao_cartas, 0 a 2500; 15.4)

Os dois sao gravados em todas as linhas da conta.

Regra: número **inteiro** de 0 até o máximo.

O erro de validação aparece **dentro** da janela (sem messagebox, para não
travar o app).
"""

import tkinter as tk

import customtkinter as ctk

import caminhos
from config_app import COLECAO_CARTAS_MAXIMO, NIVEL_CHASER_MAXIMO
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


def validar_inteiro(texto, nome, maximo, exemplo, artigo="o"):
    """'385' -> (385, None).  'abc' -> (None, 'mensagem de erro').

    `nome` vai na mensagem ("nível do chaser"); `artigo` concorda com ele
    ("o nível", "a coleção")."""
    bruto = str(texto).strip()
    if bruto == "":
        return None, f"Informe {artigo} {nome}."
    try:
        valor = int(bruto)
    except ValueError:
        return None, (f"{artigo.upper()} {nome} é um número INTEIRO "
                      f"(ex.: {exemplo}).")
    if valor < NIVEL_MINIMO:
        return None, (f"{artigo.upper()} {nome} não pode ser menor que "
                      f"{NIVEL_MINIMO}.")
    if valor > maximo:
        return None, f"O máximo d{artigo} {nome} é {maximo}."
    return valor, None


def validar_nivel(texto):
    """Nivel do chaser: inteiro de 0 a 999 (o maximo do jogo)."""
    valor, erro = validar_inteiro(texto, "nível do chaser",
                                  NIVEL_CHASER_MAXIMO, 385)
    if erro and "máximo" in erro:
        erro = f"O nível máximo do chaser é {NIVEL_CHASER_MAXIMO}."
    return valor, erro


def validar_colecao(texto):
    """Colecao de cartas: inteiro de 0 a 2500."""
    return validar_inteiro(texto, "coleção de cartas", COLECAO_CARTAS_MAXIMO,
                           1840, artigo="a")


class JanelaValorDaConta(ctk.CTkToplevel):
    """Edicao de um numero da conta (um valor para todos os personagens).

    As subclasses definem o texto, a validacao e onde gravar."""

    TITULO = ""
    CABECALHO = ""
    DICA = ""
    ATRIBUTO = ""           # o valor atual no app (app.<ATRIBUTO>)
    PADRAO = 0
    AVISO_SEM_COLUNA = ""

    def validar(self, texto):
        raise NotImplementedError

    def gravar(self, valor):
        raise NotImplementedError

    def coluna_existe(self):
        return True

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title(self.TITULO)
        caminhos.aplicar_icone(self)
        self.geometry("400x300")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)

        self.erro_var = tk.StringVar(value="")

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(20, 4))
        ctk.CTkLabel(topo, text=self.CABECALHO,
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left")
        ctk.CTkLabel(topo, text="(um valor para toda a conta)",
                     font=ctk.CTkFont(size=12),
                     text_color=CORES["suave"]).pack(side="left", padx=10, pady=(8, 0))

        ctk.CTkLabel(self, text=self.DICA,
                     font=ctk.CTkFont(size=13),
                     text_color=CORES["suave"]).pack(anchor="w", padx=22, pady=(6, 10))

        # aviso: a coluna do banco ainda nao existe (o SQL precisa ser rodado)
        if getattr(app, "usar_supabase", False) and not self.coluna_existe():
            ctk.CTkLabel(self, text=self.AVISO_SEM_COLUNA,
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
        self.entrada.insert(0, str(getattr(app, self.ATRIBUTO, self.PADRAO)))
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
            falha(f"focar a janela {self.TITULO}")

    def _salvar(self):
        valor, erro = self.validar(self.entrada.get())
        if erro:
            self.erro_var.set(erro)
            self.entrada.focus_set()
            self.entrada.select_range(0, "end")
            return
        try:
            ok = self.gravar(valor)
        except Exception as exc:
            self.erro_var.set(f"Erro ao salvar: {exc}")
            return
        if not ok:
            self.erro_var.set("Não foi possível salvar.")
            return
        self.destroy()


class JanelaNivelChaser(JanelaValorDaConta):
    """Edição do nível do chaser (um valor por conta)."""

    TITULO = "Nível do Chaser"
    CABECALHO = "NÍVEL DO CHASER"
    DICA = "Número inteiro de 0 a 999."
    ATRIBUTO = "nivel_chaser"
    PADRAO = 385
    AVISO_SEM_COLUNA = ("A coluna nivel_chaser ainda não existe no banco: "
                        "rode sql/nivel_chaser.sql no Supabase para gravar.")

    def validar(self, texto):
        return validar_nivel(texto)

    def gravar(self, valor):
        return self.app.definir_nivel_chaser(valor)

    def coluna_existe(self):
        return (not hasattr(self.app, "_nivel_no_banco")
                or self.app._nivel_no_banco())


class JanelaColecaoCartas(JanelaValorDaConta):
    """Edição do nível da coleção de cartas (15.4, um valor por conta)."""

    TITULO = "Coleção de cartas"
    CABECALHO = "COLEÇÃO DE CARTAS"
    DICA = f"Número inteiro de 0 a {COLECAO_CARTAS_MAXIMO:,}.".replace(",", ".")
    ATRIBUTO = "colecao_cartas"
    PADRAO = 0
    AVISO_SEM_COLUNA = ("A coluna colecao_cartas ainda não existe no banco: "
                        "rode sql/colecao_cartas.sql no Supabase para gravar.")

    def validar(self, texto):
        return validar_colecao(texto)

    def gravar(self, valor):
        return self.app.definir_colecao_cartas(valor)

    def coluna_existe(self):
        return (not hasattr(self.app, "_colecao_no_banco")
                or self.app._colecao_no_banco())

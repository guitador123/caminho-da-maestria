# -*- coding: utf-8 -*-
"""
Edicao rapida de um equipamento do Void: a PEDRA (item 16) e as 4 CARTAS
(item 15.3).

Abre ao clicar na linha de uma peca no card (ou no botao "Cartas" da janela
do personagem). As setas passam para a peca anterior/seguinte sem fechar.

A pedra tem nivel (+0 a +18) e status, e um nao vale sem o outro: com so
um dos dois escolhido, a janela avisa e nao deixa trocar de peca nem fechar
(escolha o outro, ou volte os dois para "-" para tirar a pedra).

Cada escolha valida vale na hora (o card atualiza). Fechar (botao ou X)
salva no Supabase se algo mudou.
"""

import tkinter as tk

import customtkinter as ctk

import caminhos
from card_personagem import CORES_PEDRA, PECAS_VOID
from config_app import ABA_PECAS, ROTULOS_COLUNAS
from dados_app import (CARTAS_VOID, NIVEL_PEDRA_MAXIMO, PECAS_COM_CARTAS,
                       PEDRAS_VOID, SLOTS_CARTAS, coluna_cartas, coluna_pedra,
                       cor_da_pedra,
                       estado_da_carta, juntar_cartas, juntar_pedra,
                       ler_cartas, ler_pedra, validar_pedra)
from opcoes import coluna_banco
from registro import falha

CORES = {
    "fundo": "#141221",
    "painel": "#1e1a30",
    "painel_borda": "#332d4d",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "fraco": "#6f688f",
    "roxo": "#8b5cf6",
    "verde": "#22c55e",
    "vermelho": "#f43f5e",
}

VAZIO = "(vazio)"
SEM_PEDRA = "\u2013"           # "-": pedra nao informada
NIVEIS_PEDRA = [f"+{n}" for n in range(NIVEL_PEDRA_MAXIMO + 1)]
NOMES_PECAS = dict(PECAS_VOID)


def cor_do_slot(carta):
    """A cor do quadradinho (a mesma do card)."""
    estado = estado_da_carta(carta)
    if estado == "status":
        return CORES["verde"]
    if estado == "outra":
        return CORES["vermelho"]
    return None


class JanelaCartas(ctk.CTkToplevel):
    """As 4 cartas de uma peca do Void de um personagem."""

    def __init__(self, app, nome, peca):
        super().__init__(app)
        self.app = app
        self.nome = None
        self.peca = None
        self.mudou = False
        self.title("Pedra e cartas do Void")
        caminhos.aplicar_icone(self)
        self.geometry("460x450")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)
        self.protocol("WM_DELETE_WINDOW", self.fechar)
        self.bind("<Escape>", lambda e: self.fechar())

        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(16, 2))
        self.botao_anterior = ctk.CTkButton(
            topo, text="‹", width=36, height=32, corner_radius=8,
            fg_color="#2a2440", hover_color="#372f52",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda: self._andar(-1))
        self.botao_anterior.pack(side="left")
        self.titulo = ctk.CTkLabel(topo, text="",
                                   font=ctk.CTkFont(size=18, weight="bold"),
                                   text_color=CORES["texto"])
        self.titulo.pack(side="left", padx=12)
        self.botao_seguinte = ctk.CTkButton(
            topo, text="›", width=36, height=32, corner_radius=8,
            fg_color="#2a2440", hover_color="#372f52",
            font=ctk.CTkFont(size=18, weight="bold"),
            command=lambda: self._andar(1))
        self.botao_seguinte.pack(side="right")

        self.subtitulo = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12),
                                      text_color=CORES["suave"])
        self.subtitulo.pack(anchor="w", padx=22, pady=(0, 8))

        # --- a pedra (16): nivel + status, um nao vale sem o outro ---------
        ctk.CTkLabel(self, text="PEDRA", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=22)
        linha_pedra = ctk.CTkFrame(self, fg_color="transparent")
        linha_pedra.pack(fill="x", padx=20, pady=(2, 0))
        estilo = dict(height=32, corner_radius=8, fg_color=CORES["painel"],
                      button_color=CORES["roxo"], button_hover_color="#a78bfa",
                      dropdown_fg_color=CORES["painel"],
                      dropdown_hover_color="#3a3358",
                      text_color=CORES["texto"], font=ctk.CTkFont(size=13))
        # a cor do nivel (a mesma do chip do card)
        self.marca_pedra = ctk.CTkLabel(linha_pedra, text="", width=14,
                                        height=14, corner_radius=3,
                                        fg_color=CORES["painel"])
        self.marca_pedra.pack(side="left", padx=(2, 8))
        self.menu_nivel = ctk.CTkOptionMenu(
            linha_pedra, width=90, values=[SEM_PEDRA] + NIVEIS_PEDRA,
            command=lambda _v: self._escolher_pedra(), **estilo)
        self.menu_nivel.pack(side="left", padx=(0, 8))
        self.menu_status = ctk.CTkOptionMenu(
            linha_pedra, width=290, values=[SEM_PEDRA],
            command=lambda _v: self._escolher_pedra(), **estilo)
        self.menu_status.pack(side="left")
        self.erro_pedra = ctk.CTkLabel(self, text="", height=18,
                                       font=ctk.CTkFont(size=12, weight="bold"),
                                       text_color=CORES["vermelho"])
        self.erro_pedra.pack(anchor="w", padx=22, pady=(2, 4))

        ctk.CTkLabel(self, text="CARTAS", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=22)
        self.slots = []
        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="x", padx=20)
        for indice in range(SLOTS_CARTAS):
            linha = ctk.CTkFrame(corpo, fg_color="transparent")
            linha.pack(fill="x", pady=4)
            marca = ctk.CTkLabel(linha, text="", width=14, height=14,
                                 corner_radius=3, fg_color=CORES["painel"])
            marca.pack(side="left", padx=(2, 10))
            ctk.CTkLabel(linha, text=f"{indice + 1}", width=16,
                         font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=CORES["suave"]).pack(side="left")
            menu = ctk.CTkOptionMenu(
                linha, width=360, height=32, corner_radius=8,
                fg_color=CORES["painel"], button_color=CORES["roxo"],
                button_hover_color="#a78bfa",
                dropdown_fg_color=CORES["painel"],
                dropdown_hover_color="#3a3358",
                text_color=CORES["texto"], font=ctk.CTkFont(size=13),
                values=[VAZIO],
                command=lambda _v, i=indice: self._escolher(i))
            menu.pack(side="left", padx=(6, 0))
            self.slots.append((marca, menu))

        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(14, 16))
        ctk.CTkButton(barra, text="Salvar e fechar", width=170, height=40,
                      corner_radius=10, fg_color=CORES["verde"],
                      hover_color="#16a34a", text_color="#08130d",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self.fechar).pack(side="right")
        ctk.CTkLabel(barra, text="Cartas: verde = com status · vermelho = Outra",
                     font=ctk.CTkFont(size=11),
                     text_color=CORES["fraco"]).pack(side="left")

        self.mostrar(nome, peca)
        self.after(80, self._focar)

    # ------------------------------------------------------------ dados --
    def _df(self):
        return self.app.dfs.get(ABA_PECAS)

    def _coluna(self, df, peca, criar=False):
        """A coluna das cartas da peca no dataframe (cria se faltar)."""
        return self._coluna_por_nome(df, coluna_cartas(peca), criar)

    def _coluna_por_nome(self, df, nome_banco, criar=False):
        """A coluna do dataframe para a coluna do banco (cria se faltar)."""
        alvo = coluna_banco(nome_banco)
        for coluna in df.columns:
            if coluna_banco(coluna) == alvo:
                return coluna
        if not criar:
            return None
        # a coluna ainda nao veio do banco (o SQL nao rodou): cria vazia
        coluna = ROTULOS_COLUNAS.get(alvo, nome_banco)
        df[coluna] = ""
        return coluna

    def _mascara(self, df):
        return df["Nome"].astype(str) == str(self.nome)

    def _ler(self):
        df = self._df()
        if df is None or df.empty or "Nome" not in df.columns:
            return ler_cartas("")
        coluna = self._coluna(df, self.peca)
        linhas = df.loc[self._mascara(df)]
        if coluna is None or linhas.empty:
            return ler_cartas("")
        return ler_cartas(linhas.iloc[0][coluna])

    def _gravar(self, slots):
        df = self._df()
        if df is None or df.empty or "Nome" not in df.columns:
            return
        coluna = self._coluna(df, self.peca, criar=True)
        if df[coluna].dtype != object:
            df[coluna] = df[coluna].astype(object)
        df.loc[self._mascara(df), coluna] = juntar_cartas(slots)

    def _ler_pedra(self):
        df = self._df()
        if df is None or df.empty or "Nome" not in df.columns:
            return None, ""
        coluna = self._coluna_por_nome(df, coluna_pedra(self.peca))
        linhas = df.loc[self._mascara(df)]
        if coluna is None or linhas.empty:
            return None, ""
        return ler_pedra(linhas.iloc[0][coluna])

    def _gravar_pedra(self, texto):
        df = self._df()
        if df is None or df.empty or "Nome" not in df.columns:
            return
        coluna = self._coluna_por_nome(df, coluna_pedra(self.peca), criar=True)
        if df[coluna].dtype != object:
            df[coluna] = df[coluna].astype(object)
        df.loc[self._mascara(df), coluna] = texto

    def _pedra_escolhida(self):
        """(nivel, status) dos menus ("-" vira vazio)."""
        nivel = self.menu_nivel.get()
        status = self.menu_status.get()
        return ("" if nivel == SEM_PEDRA else nivel,
                "" if status == SEM_PEDRA else status)

    def _pintar_nivel(self):
        """O quadradinho ao lado do nivel: +18 vermelho, +17 dourado,
        +11 a +16 verde, +0 a +10 cinza."""
        texto = self.menu_nivel.get()
        nivel = None if texto == SEM_PEDRA else int(texto.lstrip("+"))
        cor = cor_da_pedra(nivel)
        self.marca_pedra.configure(
            fg_color=CORES_PEDRA[cor][0] if cor else CORES["painel"])

    def pedra_valida(self):
        """A pedra escolhida pode ficar? (mostra o erro se nao)."""
        self._pintar_nivel()
        erro = validar_pedra(*self._pedra_escolhida())
        self.erro_pedra.configure(text=erro or "")
        return erro is None

    def _escolher_pedra(self):
        if not self.pedra_valida():
            return                     # incompleta: espera o outro campo
        texto = juntar_pedra(*self._pedra_escolhida())
        self._gravar_pedra(texto)
        self.mudou = True
        try:
            self.app._marcar_modificado()
            self.app._atualizar_card(self.nome)
        except Exception as erro:
            falha("[Pedra] atualizar o card", erro)

    # --------------------------------------------------------------- tela --
    def mostrar(self, nome, peca):
        """Troca o personagem/peca mostrados (a janela continua aberta)."""
        self.nome = str(nome)
        self.peca = peca if peca in PECAS_COM_CARTAS else PECAS_COM_CARTAS[0]
        self.titulo.configure(
            text=f"{self.nome}  ·  {NOMES_PECAS.get(self.peca, self.peca)}")
        posicao = PECAS_COM_CARTAS.index(self.peca) + 1
        self.subtitulo.configure(
            text=f"Peça {posicao} de {len(PECAS_COM_CARTAS)}  ·  as setas "
                 "trocam de peça")
        nivel, status = self._ler_pedra()
        self.menu_status.configure(values=[SEM_PEDRA] + PEDRAS_VOID[self.peca])
        self.menu_nivel.set(SEM_PEDRA if nivel is None else f"+{nivel}")
        self.menu_status.set(status or SEM_PEDRA)
        self.erro_pedra.configure(text="")
        self._pintar_nivel()
        opcoes = list(CARTAS_VOID[self.peca])
        for (marca, menu), carta in zip(self.slots, self._ler()):
            valores = [VAZIO] + opcoes
            if carta and carta not in opcoes:
                valores.append(carta)      # valor antigo fora da lista
            menu.configure(values=valores)
            menu.set(carta or VAZIO)
            marca.configure(fg_color=cor_do_slot(carta) or CORES["painel"])
        try:
            self.lift()
        except tk.TclError:
            pass                      # janela ja fechada

    def _escolher(self, _indice):
        slots = []
        for marca, menu in self.slots:
            carta = "" if menu.get() == VAZIO else menu.get()
            marca.configure(fg_color=cor_do_slot(carta) or CORES["painel"])
            slots.append(carta)
        self._gravar(slots)
        self.mudou = True
        try:
            self.app._marcar_modificado()
            self.app._atualizar_card(self.nome)
        except Exception as erro:
            falha("[Cartas] atualizar o card", erro)

    def _andar(self, passo):
        if not self.pedra_valida():
            return                     # pedra incompleta: nao sai da peca
        indice = PECAS_COM_CARTAS.index(self.peca)
        self.mostrar(self.nome,
                     PECAS_COM_CARTAS[(indice + passo) % len(PECAS_COM_CARTAS)])

    def _focar(self):
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass                      # janela ja fechada

    def fechar(self):
        """Fecha; se algo mudou, salva no Supabase. Com a pedra incompleta
        (nivel sem status ou o contrario) nao fecha: o status e obrigatorio."""
        if not self.pedra_valida():
            return
        mudou = self.mudou
        try:
            self.destroy()
        except tk.TclError:
            pass
        if mudou and getattr(self.app, "usar_supabase", False):
            self.app.salvar_supabase()
        elif mudou:
            self.app.status(f"{self.nome}: cartas alteradas.")

# -*- coding: utf-8 -*-
"""
Painel flutuante da MISSAO RAPIDA.

Abre com o botao "Missao Rapida" do hero (ou com a tecla M) e permite:

  - escolher o personagem (lista com busca);
  - marcar/desmarcar as 7 missoes semanais (varias de uma vez);
  - salvar tudo em UMA gravacao (o "Salvar (N)");
  - atalhos: 1-7 marcam, Ctrl+Enter salva, Esc fecha.

O painel nao escreve no banco sozinho: ele monta o que mudou e o app
grava de uma vez (o salvamento continua em 2o plano).
"""

import tkinter as tk

import customtkinter as ctk

import caminhos
from registro import falha

from card_personagem import DUNGEONS

CORES = {
    "fundo": "#141221",
    "painel": "#1e1a30",
    "painel_borda": "#332d4d",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "verde": "#22c55e",
    "vermelho": "#f43f5e",
    "pendente": "#f59e0b",
}

# (chave, rotulo)
MISSOES = [(chave, rotulo) for chave, rotulo in DUNGEONS]


class JanelaMissaoRapida(ctk.CTkToplevel):
    """Painel de marcacao rapida das missoes semanais."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Missão Rápida")
        caminhos.aplicar_icone(self)
        self.geometry("640x600")
        self.minsize(560, 480)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)

        self.pendentes = {}      # chave -> True/False (o que mudou)
        self.salvo = {}           # chave -> bool (estado no banco)
        self.personagem = None
        self._botoes_missao = {}
        self._botoes_personagem = {}
        self._selecionado = None

        self._montar()
        self._carregar_personagens()
        self.after(80, self._focar)

    # ------------------------------------------------------------- UI ------
    def _montar(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(16, 2))
        ctk.CTkLabel(topo, text="MISSÃO RÁPIDA",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left")
        ctk.CTkLabel(topo, text="marque as dungeons concluídas",
                     font=ctk.CTkFont(size=12),
                     text_color=CORES["suave"]).pack(side="left", padx=10,
                                                     pady=(8, 0))

        corpo = ctk.CTkFrame(self, fg_color="transparent")
        corpo.pack(fill="both", expand=True, padx=16, pady=(6, 4))

        # --- coluna 1: personagens ---
        esquerda = ctk.CTkFrame(corpo, fg_color="transparent")
        esquerda.pack(side="left", fill="both", expand=True, padx=(0, 10))
        ctk.CTkLabel(esquerda, text="PERSONAGEM", font=ctk.CTkFont(size=11,
                                                                   weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=4, pady=(4, 4))
        self.busca = ctk.CTkEntry(esquerda, height=34, corner_radius=8,
                                  fg_color=CORES["painel"],
                                  border_color=CORES["painel_borda"],
                                  text_color=CORES["texto"],
                                  placeholder_text="buscar...",
                                  placeholder_text_color="#6b6480",
                                  font=ctk.CTkFont(size=13))
        self.busca.pack(fill="x", padx=2, pady=(0, 6))
        self.busca.bind("<KeyRelease>", lambda e: self._filtrar())
        self.lista = ctk.CTkScrollableFrame(esquerda, fg_color=CORES["painel"],
                                             corner_radius=10,
                                             scrollbar_button_color="#3a3358")
        self.lista.pack(fill="both", expand=True)

        # --- coluna 2: missoes ---
        direita = ctk.CTkFrame(corpo, fg_color="transparent")
        direita.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(direita, text="MISSÕES SEMANAIS",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=4, pady=(4, 4))
        self.info = ctk.CTkLabel(direita, text="Escolha um personagem",
                                 font=ctk.CTkFont(size=12),
                                 text_color=CORES["suave"], anchor="w")
        self.info.pack(fill="x", padx=4, pady=(0, 6))

        for indice, (chave, rotulo) in enumerate(MISSOES, start=1):
            botao = ctk.CTkButton(
                direita, text=f"{indice}. {rotulo}", height=36, corner_radius=8,
                fg_color=CORES["painel"], hover_color="#2f2949",
                text_color=CORES["suave"], border_width=1,
                border_color=CORES["painel_borda"],
                font=ctk.CTkFont(size=13),
                command=lambda c=chave: self._alternar(c))
            botao.pack(fill="x", padx=2, pady=3)
            self._botoes_missao[chave] = botao

        # --- rodape ---
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(6, 16))
        ctk.CTkLabel(barra, text="1-7 marca · Ctrl+Enter salva · Esc fecha",
                     font=ctk.CTkFont(size=11),
                     text_color="#6b6480").pack(side="left")
        ctk.CTkButton(barra, text="Fechar", width=110, height=40,
                      corner_radius=8, fg_color="#2a2440", hover_color="#372f52",
                      text_color=CORES["texto"], font=ctk.CTkFont(size=14),
                      command=self.destroy).pack(side="right")
        self.btn_salvar = ctk.CTkButton(barra, text="Salvar", width=150, height=40,
                                        corner_radius=8,
                                        fg_color=CORES["verde"],
                                        hover_color="#16a34a",
                                        text_color="#08130d",
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        command=self._salvar)
        self.btn_salvar.pack(side="right", padx=(0, 10))
        self.btn_salvar.configure(state="disabled")

        self.bind("<Escape>", lambda e: self.destroy())
        self.bind("<Control-Return>", lambda e: self._salvar())
        for indice, (chave, _r) in enumerate(MISSOES, start=1):
            self.bind(str(indice), lambda e, c=chave: self._alternar(c))

    # ------------------------------------------------------ personagens -----
    def _carregar_personagens(self):
        df = self.app.dfs.get("Geral")
        nomes = []
        if df is not None and not df.empty and "Nome" in df.columns:
            nomes = [str(n) for n in df["Nome"].tolist()]
        self.nomes = nomes
        self._filtrar()
        # ja comeca no ultimo personagem usado
        ultimo = getattr(self.app, "ultimo_personagem_missao", None)
        if ultimo and ultimo in nomes:
            self._selecionar(ultimo)
        elif nomes:
            self._selecionar(nomes[0])

    def _filtrar(self):
        termo = (self.busca.get() or "").strip().lower()
        for nome in list(self._botoes_personagem):
            try:
                self._botoes_personagem[nome].destroy()
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("filtrar os botoes da missao")
        self._botoes_personagem = {}
        for nome in self.nomes:
            if termo and termo not in nome.lower():
                continue
            selecionado = nome == self._selecionado
            botao = ctk.CTkButton(
                self.lista, text=nome, height=32, corner_radius=6,
                fg_color=CORES["roxo"] if selecionado else "transparent",
                hover_color="#2f2949",
                text_color="#ffffff" if selecionado else CORES["suave"],
                font=ctk.CTkFont(size=13, weight="bold" if selecionado else "normal"),
                command=lambda n=nome: self._selecionar(n))
            botao.pack(fill="x", padx=2, pady=2)
            self._botoes_personagem[nome] = botao

    def _selecionar(self, nome):
        self._selecionado = nome
        self.personagem = nome
        self.salvo = self.app._missoes_do_personagem(nome)
        self.pendentes = {}
        self.info.configure(text=f"{nome} — clique para marcar/desmarcar")
        self._atualizar_botoes()
        self._filtrar()

    # --------------------------------------------------------- missoes -----
    def _estado(self, chave):
        """Estado shown: pendente > salvo > False."""
        if chave in self.pendentes:
            return self.pendentes[chave]
        return self.salvo.get(chave, False)

    def _alternar(self, chave):
        if self.personagem is None:
            return
        atual = self._estado(chave)
        novo = not atual
        self.pendentes[chave] = novo
        self._atualizar_botoes()

    def _atualizar_botoes(self):
        for chave, botao in self._botoes_missao.items():
            feito = self._estado(chave)
            pendente = chave in self.pendentes
            if pendente:
                botao.configure(fg_color="#3b2f12", text_color=CORES["pendente"],
                                border_color=CORES["pendente"])
            elif feito:
                botao.configure(fg_color="#143d2a", text_color="#7ef0b0",
                                border_color="#1f7a4d")
            else:
                botao.configure(fg_color=CORES["painel"], text_color=CORES["suave"],
                                border_color=CORES["painel_borda"])
            rotulo = dict(MISSOES).get(chave, chave)
            botao.configure(text=("✓ " if feito else "") + f"{rotulo}")

        if self.pendentes:
            self.btn_salvar.configure(state="normal",
                                      text=f"Salvar ({len(self.pendentes)})")
        else:
            self.btn_salvar.configure(state="disabled", text="Salvar")

    # ---------------------------------------------------------- salvar -----
    def _salvar(self):
        if not self.pendentes or self.personagem is None:
            self.destroy()
            return
        missoes = dict(self.pendentes)
        ok = self.app.marcar_missoes(self.personagem, missoes)
        if ok:
            self.app._lembrar_personagem_missao(self.personagem)
            self.salvo = self.app._missoes_do_personagem(self.personagem)
            self.pendentes = {}
            self._atualizar_botoes()
            self.app.status(f"{self.personagem}: {len(missoes)} missao(oes) "
                            f"gravada(s).")
        self.destroy()

    def _focar(self):
        try:
            self.focus_set()
            self.busca.focus_set()
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("focar a missao rapida")

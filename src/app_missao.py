# -*- coding: utf-8 -*-
"""
Missao Rapida e as acoes de dungeons (zerar, marcar).

Parte da tela principal (`GrandChaseApp` herda de `MissaoMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import customtkinter as ctk
import tema_visual as tv
import tkinter as tk
from PIL import ImageTk
from card_personagem import DUNGEONS as DUNGEONS_CARD
from config_app import ABA_SEMANAIS, MODO_MISSAO_CARD, MODO_MISSAO_JANELA
from dados_app import _coluna_dungeon_semanal, _colunas_conhecidas, _verdadeiro
from registro import falha
from tkinter import messagebox


class MissaoMixin:
    # ------------------------------ acoes da tela principal -----------------
    def zerar_dungeons(self):
        """Marca todas as colunas da aba Semanais como 'Falso'."""
        df = self.dfs.get(ABA_SEMANAIS)
        if df is None or df.empty:
            messagebox.showinfo("Semanais", "Nao ha dados semanais carregados.")
            return
        colunas = _colunas_conhecidas(df, "semanais")
        if not colunas:
            messagebox.showinfo("Semanais", "A aba Semanais nao tem colunas de dungeon.")
            return
        marcadas = sum(1 for c in colunas if df[c].map(_verdadeiro).any())
        if not messagebox.askyesno(
                "Zerar dungeons semanais",
                f"Marcar todas as {len(colunas)} colunas semanais como 'Falso'?\n\n"
                f"({marcadas} colunas tem marcacoes ativas)"):
            return

        for coluna in colunas:
            df[coluna] = "Falso"
        self._marcar_modificado()
        busca = self.tree_refs.get(ABA_SEMANAIS, {}).get("busca")
        self._refrescar_tabela(ABA_SEMANAIS, busca.get() if busca else "")
        self._atualizar_cards()
        # e os CARDS de personagem (as missoes tem que sumir deles tambem)
        self._atualizar_todos_os_cards()
        if self.usar_supabase:
            self.salvar_supabase()
        else:
            self.status("Dungeons semanais zeradas (use 'Salvar' para gravar).")

    # --------------------------------------------------- missao rapida ----
    def _coluna_missao(self, chave):
        """Coluna da missao semanal no dataframe (pelo nome logico)."""
        df = self.dfs.get(ABA_SEMANAIS)
        return _coluna_dungeon_semanal(df, chave)

    def _missoes_do_personagem(self, nome):
        """Estado atual das 7 missoes de um personagem {chave: bool}."""
        df = self.dfs.get(ABA_SEMANAIS)
        estado = {}
        if df is None or df.empty or "Nome" not in df.columns:
            return estado
        achada = df[df["Nome"].astype(str) == str(nome)]
        if achada.empty:
            return estado
        linha = achada.iloc[0]
        for chave, _rotulo in DUNGEONS_CARD:
            coluna = self._coluna_missao(chave)
            if coluna is None:
                continue
            estado[chave] = _verdadeiro(linha.get(coluna))
        return estado

    def marcar_missoes(self, nome, missoes):
        """Marca/desmarca varias missoes semanais de um personagem.

        Tudo em UMA gravacao (o app ja salva em 2o plano).
        """
        df = self.dfs.get(ABA_SEMANAIS)
        if df is None or df.empty or "Nome" not in df.columns:
            return False
        mask = df["Nome"].astype(str) == str(nome)
        if not mask.any():
            return False
        alteradas = 0
        for chave, feito in missoes.items():
            coluna = self._coluna_missao(chave)
            if coluna is None or coluna not in df.columns:
                continue
            df.loc[mask, coluna] = "Verdadeiro" if feito else "Falso"
            alteradas += 1
        if not alteradas:
            return False
        self._atualizar_card(str(nome))
        self._atualizar_cards()
        self._marcar_modificado()
        if self.usar_supabase:
            self.salvar_supabase()
        return True

    def alternar_missao_rapida(self, chave, nome):
        """Clique no chip de uma missao (no modo missao rapida).

        Fora do modo, o clique no chip abre a edicao do personagem (como
        antes) — o chip tem prioridade de tag no canvas.
        """
        if not (self.missao_rapida and self.missao_modo == MODO_MISSAO_CARD):
            # fora do modo CARD: o clique no chip abre a edicao (como antes)
            self._abrir_personagem({"nome": nome})
            return False
        df = self.dfs.get(ABA_SEMANAIS)
        coluna = self._coluna_missao(chave)
        if df is None or coluna is None:
            return False
        mask = df["Nome"].astype(str) == str(nome)
        if not mask.any():
            return False
        atual = _verdadeiro(df.loc[mask, coluna].iloc[0])
        novo = not atual
        df.loc[mask, coluna] = "Verdadeiro" if novo else "Falso"
        self._atualizar_card(str(nome))
        self._atualizar_cards()
        self._marcar_modificado()
        if self.usar_supabase:
            self.salvar_supabase()
        rotulo = dict(DUNGEONS_CARD).get(chave, chave)
        self.status(f"{nome}: {rotulo} {'MARCADA' if novo else 'desmarcada'}")
        return True

    def alternar_missao(self):
        """Liga/desliga o MODO MISSÃO RÁPIDA (e abre/fecha o painel)."""
        estado = not self.missao_rapida
        self.missao_rapida = estado
        self._marcar_botao("topo4", estado)
        if estado:
            if self.missao_modo == MODO_MISSAO_JANELA:
                self._abrir_painel_missao()
                self.status("Missao rapida (PAINEL): marque as dungeons no "
                            "painel. Esc fecha.")
            else:
                self._fechar_painel_missao()
                self.status("Missao rapida (CARD): clique na missao do card "
                            "para marcar (o card nao abre a edicao).")
        else:
            self._fechar_painel_missao()
            self.status("Missao rapida desligada.")
        # a preferencia antiga (filtro da tabela) nao e mais usada
        self._salvar_preferencia("missao_rapida", estado)

    def _rotulo_modo_missao(self):
        """Texto da opcao (mostra o modo que esta ativo)."""
        if self.missao_modo == MODO_MISSAO_CARD:
            return "Modo: clicar no card"
        return "Modo: painel (janela)"

    def _desenhar_chave_missao(self):
        """Check (abaixo do botao Missao Rapida) que escolhe o MODO."""
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(tv.MISSAO_MODO)
        tamanho = lay.f(17)
        cy = (y1 + y2) / 2

        self._fotos_extra = getattr(self, "_fotos_extra", {})
        self._fotos_extra["missao_caixa"] = ImageTk.PhotoImage(
            tv.caixa_check("#241d3d", "#6d5fa8", (tamanho, tamanho), raio=5))
        self._fotos_extra["missao_caixa_marcada"] = ImageTk.PhotoImage(
            tv.caixa_check("#22c55e", "#22c55e", (tamanho, tamanho), raio=5))

        item_caixa = self.canvas.create_image(
            x1, cy - tamanho / 2, anchor="nw",
            image=self._fotos_extra["missao_caixa"], tags=("missao_modo",))
        item_v = self.canvas.create_text(
            x1 + tamanho / 2, cy, text="\u2713", font=self._fonte(11, "bold"),
            fill="#08130d", anchor="center", state="hidden", tags=("missao_modo",))
        item_texto = self._texto(x1 + tamanho + lay.w(9), cy,
                                 self._rotulo_modo_missao(), 11,
                                 cor=tv.CORES["suave"], anchor="w")
        self.canvas.itemconfig(item_texto, tags=("missao_modo",))

        self.canvas.tag_bind("missao_modo", "<Button-1>",
                             lambda e: self.alternar_modo_missao())
        self.canvas.tag_bind("missao_modo", "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind("missao_modo", "<Leave>",
                             lambda e: self.canvas.configure(cursor=""))

        self.itens_chave_missao = {"caixa": item_caixa, "v": item_v,
                                   "texto": item_texto}
        self._atualizar_chave_missao()

    def _atualizar_chave_missao(self):
        """Pinta o check conforme o modo ativo."""
        marcado = self.missao_modo == MODO_MISSAO_CARD
        item_caixa = self.itens_chave_missao.get("caixa")
        if item_caixa is not None:
            self.canvas.itemconfigure(
                item_caixa,
                image=self._fotos_extra.get(
                    "missao_caixa_marcada" if marcado else "missao_caixa"))
        item_v = self.itens_chave_missao.get("v")
        if item_v is not None:
            self.canvas.itemconfigure(item_v,
                                      state="normal" if marcado else "hidden")
        item_texto = self.itens_chave_missao.get("texto")
        if item_texto is not None:
            self.canvas.itemconfigure(item_texto,
                                      text=self._rotulo_modo_missao())

    def alternar_modo_missao(self):
        """Alterna entre o MODO PAINEL e o MODO CARD (so um por vez)."""
        self.missao_modo = (MODO_MISSAO_CARD if self.missao_modo == MODO_MISSAO_JANELA
                            else MODO_MISSAO_JANELA)
        self._atualizar_chave_missao()
        if self.missao_rapida:
            if self.missao_modo == MODO_MISSAO_JANELA:
                self._abrir_painel_missao()
            else:
                self._fechar_painel_missao()
        self.status("Missao rapida: " +
                    ("clicando no CARD (o card nao abre a edicao)."
                     if self.missao_modo == MODO_MISSAO_CARD
                     else "no PAINEL (o card continua abrindo a edicao)."))

    def _abrir_painel_missao(self):
        """Abre (ou foca) o painel flutuante da missao rapida."""
        if getattr(self, "_painel_missao", None) is not None:
            try:
                self._painel_missao.lift()
                self._painel_missao.focus_force()
                return self._painel_missao
            except tk.TclError:
                self._painel_missao = None
            except Exception:
                falha("trazer o painel da missao")
                self._painel_missao = None
        try:
            from janela_missao_rapida import JanelaMissaoRapida
            self._painel_missao = JanelaMissaoRapida(self)
            return self._painel_missao
        except Exception as erro:
            falha("[Missao] abrir o painel", erro)
            self.status(f"Erro ao abrir o painel da missao rapida: {erro}")
            return None

    def _fechar_painel_missao(self):
        painel = getattr(self, "_painel_missao", None)
        if painel is not None:
            try:
                painel.destroy()
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("fechar o painel da missao")
        self._painel_missao = None

    def _atalho_missao(self, evento):
        """Atalho de teclado: 'M' liga/desliga o modo missao rapida."""
        if isinstance(evento.widget, (tk.Entry, tk.Text, ctk.CTkEntry)):
            return
        if str(evento.keysym).lower() != "m":
            return
        self.alternar_missao()

    def _marcar_botao(self, chave, ativo):
        """Estado LIGADO do botao: fundo VERDE + texto escuro.

        (o modo Missao Rapida fica com o botao verde, sinalizando que
        o card esta em modo de marcacao e nao abre a edicao)
        """
        verde = self.itens_verde.get(chave)
        if verde is not None:
            self.canvas.itemconfigure(verde,
                                      state="normal" if ativo else "hidden")
        destaque = self.itens_destaque.get(chave)
        if destaque is not None:
            self.canvas.itemconfigure(destaque, state="hidden")
        texto = self.itens_texto_botao.get(chave)
        if texto is not None:
            self.canvas.itemconfigure(
                texto, fill="#08130d" if ativo else tv.CORES["texto"])

    def marcar_chaser(self):
        """Abre a edicao do nivel do chaser (o card e clicavel)."""
        self._abrir_nivel()

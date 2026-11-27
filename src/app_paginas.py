# -*- coding: utf-8 -*-
"""
As guias do topo (Maestria, Guilda, Evolucao) na tela principal.

Parte da tela principal (`GrandChaseApp` herda de `PaginasMixin`).

A Maestria e o proprio canvas principal (a barra de guias e desenhada nele
e fica fixa no topo). Guilda e Evolucao sao paginas por cima dele
(paginas.py): voltar para a Maestria so esconde a pagina, entao a rolagem
e os filtros continuam como estavam.
"""

import tkinter as tk

from paginas import (BarraAbas, PaginaConta, PaginaEvolucao, PaginaGuilda,
                     PaginaRanking)
from registro import falha


class PaginasMixin:

    def _iniciar_paginas(self):
        self.pagina_atual = "maestria"
        self._paginas = {}
        self._barra_maestria = BarraAbas(self.canvas, self.ir_para)
        # Esc volta para a Maestria
        self.bind("<Escape>", lambda e: self.ir_para("maestria"), add="+")

    # --------------------------------------------------- barra na Maestria
    def _desenhar_abas_maestria(self):
        try:
            self._barra_maestria.desenhar(self.lay, "maestria")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception as erro:
            falha("[Guias] desenhar a barra", erro)

    def _elevar_abas(self):
        """Itens novos (cards redesenhados) nascem por cima: a barra volta
        para o topo."""
        barra = getattr(self, "_barra_maestria", None)
        if barra is not None:
            barra.fixar()

    # ------------------------------------------------------------ trocar
    def _pagina(self, chave):
        pagina = self._paginas.get(chave)
        if pagina is None:
            classe = {"guilda": PaginaGuilda, "evolucao": PaginaEvolucao,
                      "conta": PaginaConta, "ranking": PaginaRanking}[chave]
            pagina = classe(self)
            self._paginas[chave] = pagina
        return pagina

    def _mostrar_pagina(self, chave):
        for outra, pagina in self._paginas.items():
            if outra != chave:
                pagina.esconder()
        if chave != "maestria":
            self._pagina(chave).mostrar()
        self.pagina_atual = chave

    def ver_conta(self, perfil):
        """A conta de outra pessoa, SO PARA VER (clique no HUB da Guilda).
        Abre na hora e carrega a conta em segundo plano."""
        from supabase_db import conta_da_guilda
        import guilda
        pagina = self._pagina("conta")
        pagina.definir(perfil, None)
        self._mostrar_pagina("conta")
        uid = perfil.get("user_id")

        def ao_terminar(ok, resultado):
            if pagina.perfil.get("user_id") != uid:
                return                # ja abriram outra conta
            if ok and resultado is not None:
                pagina.definir(perfil, guilda.abas_da_conta(resultado))
            else:
                pagina.definir(perfil, {}, erro="Não deu para carregar esta "
                               "conta agora. Tente de novo.")

        self._em_segundo_plano(lambda: conta_da_guilda(self.supabase, uid),
                               ao_terminar)

    def ir_para(self, chave):
        """Clique numa guia (ou Esc, que volta para a Maestria)."""
        try:
            if chave == "evolucao":
                # mostra na hora com o que ja tem; o historico atualiza em
                # segundo plano (abrir_evolucao)
                self.abrir_evolucao()
                return
            if chave == self.pagina_atual:
                return
            self._mostrar_pagina(chave)
            if chave == "maestria":
                self.canvas.focus_set()
        except Exception as erro:
            falha(f"[Guias] ir para {chave}", erro)
            self.status(f"Erro ao abrir {chave}: {erro}")

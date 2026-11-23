# -*- coding: utf-8 -*-
"""
Os cartoes de estatistica do topo (contagens e medias).

Parte da tela principal (`GrandChaseApp` herda de `CartoesMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import pandas as pd
import tkinter as tk
from card_personagem import _fracao
from config_app import ABA_GERAL, ABA_SEMANAIS
from dados_app import _coluna_no_df, _verdadeiro
from registro import falha


class CartoesMixin:
    # ---------------------------------------------------------- cartoes -----
    def _contar_verdadeiros(self, df, chave):
        """Conta as linhas 'Verdadeiro' da coluna (pelo nome logico do banco)."""
        coluna = _coluna_no_df(df, chave)
        if coluna is None:
            return 0
        return int(df[coluna].map(_verdadeiro).sum())

    def _despertar_completo(self):
        """Personagens com o DESPERTAR completo: Núcleos 13/13 e Épicos+ 9/9.

        Compara o VALOR (o numerador da fração), então funciona tanto para
        "9 / 9" (formato do dropdown novo) quanto para "9 / 13" (formato
        antigo da planilha, em que o denominador dos épicos+ estava errado).
        """
        df = self.dfs.get(ABA_GERAL)
        coluna_nucleo = _coluna_no_df(df, "nucleo")
        coluna_epicos = _coluna_no_df(df, "nucleos_epicos")
        if coluna_nucleo is None or coluna_epicos is None:
            return 0
        completos = 0
        for nucleo, epicos in zip(df[coluna_nucleo], df[coluna_epicos]):
            if _fracao(nucleo)[0] == 13 and _fracao(epicos)[0] == 9:
                completos += 1
        return completos

    def _libertacao_completo(self):
        """Personagens com a LIBERTAÇÃO completa (3 condições):

        1. o campo "Libertação" (estado) = VERDADEIRO
        2. Núcleos = 9/9
        3. Épicos+ = 4/4

        Se as colunas de progresso (libertacao_nucleos/libertacao_epicos)
        nao existirem na tabela (ex.: planilha antiga, modo local), conta
        apenas pelo estado — que era a regra antiga.
        """
        df = self.dfs.get(ABA_GERAL)
        col_estado = _coluna_no_df(df, "libertacao")
        col_nucleo = _coluna_no_df(df, "libertacao_nucleos")
        col_epicos = _coluna_no_df(df, "libertacao_epicos")
        if col_estado is None:
            return 0
        if col_nucleo is None or col_epicos is None:
            # sem as colunas de progresso: fica so o estado
            return int(df[col_estado].map(_verdadeiro).sum())
        completos = 0
        for estado, nucleos, epicos in zip(df[col_estado],
                                           df[col_nucleo], df[col_epicos]):
            if not _verdadeiro(estado):
                continue
            if _fracao(nucleos)[0] == 9 and _fracao(epicos)[0] == 4:
                completos += 1
        return completos

    def _poder_medio(self):
        df = self.dfs.get(ABA_GERAL)
        coluna = _coluna_no_df(df, "poder")
        if coluna is None:
            return None
        numeros = pd.to_numeric(df[coluna], errors="coerce").dropna()
        if numeros.empty:
            return None
        return float(numeros.mean())

    def _torre_concluida(self):
        """Personagens com a Torre das Ilusoes concluida."""
        df_sem = self.dfs.get(ABA_SEMANAIS)
        coluna = _coluna_no_df(df_sem, "torre_das_ilusoes")
        if coluna:
            return self._contar_verdadeiros(df_sem, "torre_das_ilusoes")
        df = self.dfs.get(ABA_GERAL)
        coluna = _coluna_no_df(df, "torre_das_ilusoes")
        if coluna is None:
            return 0
        valores = df[coluna].astype(str).str.strip()
        return int(valores.isin(("30 / 30", "30/30")).sum())

    def _atualizar_cards(self):
        """Recalcula os cards de estatistica a partir de self.dfs."""
        if not self.itens_valores:
            return
        df_sem = self.dfs.get(ABA_SEMANAIS)
        df_geral = self.dfs.get(ABA_GERAL)

        caminho = self._contar_verdadeiros(df_sem, "caminho_abissal")
        void123 = self._contar_verdadeiros(df_sem, "void_123")
        void4 = self._contar_verdadeiros(df_sem, "void_4")
        torre = self._torre_concluida()
        despertar = self._despertar_completo()
        libertacao = self._libertacao_completo()
        poder = self._poder_medio()
        nivel = self.nivel_chaser

        valores = {
            "caminho_abissal": str(caminho),
            "poder_medio": ("—" if poder is None else f"{poder:,.0f}".replace(",", ".")),
            "torre": str(torre),
            "void123": str(void123),
            "void4": str(void4),
            "nivel": str(nivel),
            "despertar": str(despertar),
            "libertacao": str(libertacao),
        }
        for chave, valor in valores.items():
            dados = self.itens_valores.get(chave)
            if not dados:
                continue
            item_valor = dados[0]
            self.canvas.itemconfig(item_valor, text=valor)
            self._posicionar_legenda(chave, valor)

    def valores_dos_cards(self):
        """Texto atual de cada card de estatistica (util para testes)."""
        valores = {}
        for chave, dados in self.itens_valores.items():
            try:
                valores[chave] = self.canvas.itemcget(dados[0], "text")
            except tk.TclError:
                valores[chave] = ""
            except Exception:
                falha("ler os valores da tela")
                valores[chave] = ""
        return valores

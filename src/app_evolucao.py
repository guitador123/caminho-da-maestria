# -*- coding: utf-8 -*-
"""
Pagina "Evolucao semanal" na tela principal.

Parte da tela principal (`GrandChaseApp` herda de `EvolucaoMixin`).

  - a guia "Evolucao" (no topo, ver app_paginas.py) mostra a pagina; antes
    era uma janela separada, aberta pelo 9o cartao da grade;
  - no 1o login depois do reset (quarta 03h) a guia abre sozinha,
    destacando a semana que acabou (uma vez por reset, por conta).

O historico vem do banco (user_historico_semanal) numa thread; a semana
atual vem das abas da tela.
"""

import historico
from config_app import ABA_GERAL, ABA_PECAS, ABA_SEMANAIS
from registro import falha, registrar
from supabase_db import carregar_historico, ler_perfil, marcar_resumo_visto


class EvolucaoMixin:

    # ----------------------------------------------------------- dados ----
    def _semana_atual(self):
        return historico.da_tela(self.dfs.get(ABA_GERAL),
                                 self.dfs.get(ABA_PECAS),
                                 self.dfs.get(ABA_SEMANAIS),
                                 getattr(self, "nivel_chaser", None),
                                 getattr(self, "colecao_cartas", None))

    def _buscar_historico(self):
        """(semanas, disponivel, resumo_visto) - roda na thread de rede."""
        linhas, disponivel = carregar_historico(self.supabase)
        perfil = ler_perfil(self.supabase, self.user_id) if disponivel else {}
        return (historico.de_historico(linhas), disponivel,
                perfil.get("resumo_visto"))

    # ----------------------------------------------------------- abrir ----
    def abrir_evolucao(self, destaque=None):
        """Vai para a guia Evolucao: mostra na hora com o historico que ja
        tem e atualiza com o do banco em segundo plano."""
        semanas = getattr(self, "_semanas_historico", None) or []
        self._mostrar_evolucao(semanas, destaque)
        if not self.usar_supabase or getattr(self, "offline", False):
            return
        self.status("Atualizando a evolução semanal...")

        def ao_terminar(ok, resultado):
            if ok and resultado:
                novas, disponivel, _visto = resultado
                if not disponivel:
                    registrar("[Evolucao] historico ainda nao configurado "
                              "(rode sql/historico_semanal.sql)")
                if novas != semanas:
                    self._semanas_historico = novas
                    self._mostrar_evolucao(novas, destaque)
                self.status("Evolução semanal atualizada.")
            else:
                self.status("Não deu para ler o histórico agora; mostrando "
                            "o que já estava carregado.")

        self._em_segundo_plano(self._buscar_historico, ao_terminar)

    def _mostrar_evolucao(self, semanas, destaque):
        """Monta a pagina e mostra a guia Evolucao."""
        try:
            pagina = self._pagina("evolucao")
            pagina.definir(semanas, self._semana_atual(), destaque=destaque,
                           nick=getattr(self, "perfil_nick", "") or "")
            if self.pagina_atual != "evolucao":
                self._mostrar_pagina("evolucao")
        except Exception as erro:
            falha("[Evolucao] abrir a pagina", erro)
            self.status(f"Erro ao abrir a evolução: {erro}")

    # ------------------------------------------- abertura automatica ----
    def _verificar_resumo_semanal(self):
        """Depois de carregar a conta: abre a pagina sozinha se houve um
        reset que a conta ainda nao viu."""
        if (not self.usar_supabase or not self.user_id
                or getattr(self, "offline", False)):
            return

        def ao_terminar(ok, resultado):
            if not ok or not resultado:
                return
            semanas, disponivel, visto = resultado
            self._semanas_historico = semanas
            if not disponivel:
                return
            destaque = historico.deve_mostrar(semanas, visto)
            if destaque is None:
                return
            registrar(f"[Evolucao] resumo da semana {destaque} (1a vez)")
            self._mostrar_evolucao(semanas, destaque)
            # grava em segundo plano (nao trava a tela)
            self._em_segundo_plano(
                lambda: marcar_resumo_visto(self.supabase, self.user_id,
                                            destaque),
                lambda _ok, _r: None)

        self._em_segundo_plano(self._buscar_historico, ao_terminar)

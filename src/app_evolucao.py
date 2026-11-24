# -*- coding: utf-8 -*-
"""
Pagina "Evolucao semanal" na tela principal.

Parte da tela principal (`GrandChaseApp` herda de `EvolucaoMixin`).

  - o 9o cartao da grade ("EVOLUCAO SEMANAL") mostra a variacao do
    Ataque Total medio na ultima semana e abre a pagina ao clicar;
  - no 1o login depois do reset (quarta 03h) a pagina abre sozinha,
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
                                 getattr(self, "nivel_chaser", None))

    def _buscar_historico(self):
        """(semanas, disponivel, resumo_visto) - roda na thread de rede."""
        linhas, disponivel = carregar_historico(self.supabase)
        perfil = ler_perfil(self.supabase, self.user_id) if disponivel else {}
        return (historico.de_historico(linhas), disponivel,
                perfil.get("resumo_visto"))

    # ---------------------------------------------------------- cartao ----
    def _texto_cartao_evolucao(self):
        """(valor, legenda) do 9o cartao."""
        semanas = getattr(self, "_semanas_historico", None) or []
        if len(semanas) >= 2:
            dif, pct = historico.variacao(
                historico.ataque_medio(semanas[-1]),
                historico.ataque_medio(semanas[-2]))
            if pct is not None:
                sinal = "+" if pct >= 0 else "−"
                valor = f"{sinal}{abs(pct):.1f}%".replace(".", ",")
                return valor, "ataque médio na semana  ›"
        if semanas:
            return str(len(semanas)), "semana registrada  ›"
        return "↗", "ver a evolução  ›"

    def _atualizar_cartao_evolucao(self):
        dados = getattr(self, "itens_valores", {}).get("evolucao")
        if not dados:
            return
        valor, legenda = self._texto_cartao_evolucao()
        item_valor, item_legenda, _x, _y = dados
        try:
            self.canvas.itemconfig(item_valor, text=valor)
            if item_legenda is not None:
                self.canvas.itemconfig(item_legenda, text=legenda)
            self._posicionar_legenda("evolucao", valor)
        except Exception:
            falha("atualizar o cartao de evolucao")

    # ----------------------------------------------------------- abrir ----
    def abrir_evolucao(self, destaque=None):
        """Abre a pagina (busca o historico em segundo plano)."""
        if not self.usar_supabase:
            self._mostrar_evolucao([], destaque)
            return
        self.status("Carregando a evolução semanal...")

        def ao_terminar(ok, resultado):
            semanas = []
            if ok and resultado:
                semanas, disponivel, _visto = resultado
                self._semanas_historico = semanas
                self._atualizar_cartao_evolucao()
                if not disponivel:
                    registrar("[Evolucao] historico ainda nao configurado "
                              "(rode sql/historico_semanal.sql)")
            else:
                self.status("Não deu para ler o histórico agora; mostrando "
                            "só a semana atual.")
            self._mostrar_evolucao(semanas, destaque)

        self._em_segundo_plano(self._buscar_historico, ao_terminar)

    def _mostrar_evolucao(self, semanas, destaque):
        janela = getattr(self, "_janela_evolucao", None)
        try:
            if janela is not None and janela.winfo_exists():
                janela.fechar()
        except Exception:
            falha("fechar a evolucao anterior")
        try:
            from janela_evolucao import JanelaEvolucao
            self._janela_evolucao = JanelaEvolucao(
                self, semanas, self._semana_atual(), destaque=destaque,
                nick=getattr(self, "perfil_nick", "") or "")
            self.status("Evolução semanal aberta.")
        except Exception as erro:
            falha("[Evolucao] abrir a pagina", erro)
            self.status(f"Erro ao abrir a evolução: {erro}")

    # ------------------------------------------- abertura automatica ----
    def _verificar_resumo_semanal(self):
        """Depois de carregar a conta: abre a pagina sozinha se houve um
        reset que a conta ainda nao viu (e atualiza o 9o cartao)."""
        if not self.usar_supabase or not self.user_id:
            return

        def ao_terminar(ok, resultado):
            if not ok or not resultado:
                return
            semanas, disponivel, visto = resultado
            self._semanas_historico = semanas
            self._atualizar_cartao_evolucao()
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

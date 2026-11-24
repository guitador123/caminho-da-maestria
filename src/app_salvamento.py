# -*- coding: utf-8 -*-
"""
Carregar/salvar no Supabase (em segundo plano), nivel do chaser e preferencias da conta.

Parte da tela principal (`GrandChaseApp` herda de `SalvamentoMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import gc
import pandas as pd
import queue
import threading
from config_app import (
    ABA_ACESSORIOS,
    ABA_GERAL,
    ABA_PECAS,
    ABA_SEMANAIS,
    COLUNA_NIVEL,
    NIVEL_CHASER_PADRAO)
from dados_app import _ordenar_colunas, _rotular_colunas
from opcoes import coluna_banco
from registro import falha
import cache_local
from supabase_db import (
    carregar_acessorios_titulo,
    carregar_pecas_void,
    carregar_personagens,
    carregar_semanais,
    garantir_estrutura,
    salvar_conta)
from tkinter import messagebox


class SalvamentoMixin:
    # --------------------------------------------------- carregar Supabase --
    def carregar_do_supabase(self):
        if getattr(self, "offline", False):
            self._carregar_da_copia()
            return
        self._nota_sincronia = ""
        if not self._enviar_pendente_da_copia():
            return
        try:
            self._limpar_abas()

            nota_estrutura = ""
            try:
                criado = garantir_estrutura(self.supabase, self.user_id)
                total = sum(v for k, v in criado.items()
                            if k != "erro" and isinstance(v, int))
                if total:
                    nota_estrutura = f" | estrutura criada: {total} linhas novas"
                elif criado.get("erro"):
                    nota_estrutura = (" | sem permissao para criar a estrutura "
                                      "(rode o SQL do HANDOFF.md)")
            except Exception:
                falha("garantir a estrutura da conta")
                nota_estrutura = ""

            personagens = carregar_personagens(self.supabase, self.user_id)
            if not personagens:
                self.status("Nenhum personagem encontrado para o seu usuario. "
                            "Use 'Escolher arquivo' para importar dados." + nota_estrutura)
                return

            df_geral = _ordenar_colunas(_rotular_colunas(pd.DataFrame(personagens)))

            pecas = carregar_pecas_void(self.supabase, personagens)
            df_pecas = _ordenar_colunas(_rotular_colunas(pd.DataFrame(pecas))) \
                if pecas else pd.DataFrame()

            acessorios = carregar_acessorios_titulo(self.supabase, personagens)
            df_acess = _ordenar_colunas(_rotular_colunas(pd.DataFrame(acessorios))) \
                if acessorios else pd.DataFrame()

            semanais = carregar_semanais(self.supabase, personagens)
            df_sem = _ordenar_colunas(_rotular_colunas(pd.DataFrame(semanais))) \
                if semanais else pd.DataFrame()

            abas_dados = {
                ABA_GERAL: df_geral,
                ABA_PECAS: df_pecas,
                ABA_ACESSORIOS: df_acess,
                ABA_SEMANAIS: df_sem,
            }

            for nome, df in abas_dados.items():
                if df.empty:
                    continue
                self.dfs[nome] = df
                self.originals[nome] = df.copy()
                if self.mostrar_tabela:
                    self._criar_aba(nome, df)

            self.modified = False
            self._versao = 0
            self._originais_do_banco = True
            self._ler_nivel_chaser()
            self._atualizar_cards()
            self._ler_preferencia()
            self._ler_ultimo_personagem()
            self._ler_perfil()
            # a copia deste PC (para abrir sem internet)
            self._guardar_copia(pendente=False)
            total = sum(len(d) for d in self.dfs.values())
            self.status(f"Carregado do Supabase: {len(personagens)} personagens "
                        f"| {total} registros nas abas" + nota_estrutura
                        + self._nota_sincronia)
        except Exception as e:
            if cache_local.eh_erro_de_rede(e):
                falha("[Supabase] carregar a conta (sem internet)", e)
                self.offline = True
                if self._carregar_da_copia():
                    return
            falha("[Supabase] carregar a conta", e)
            messagebox.showerror("Erro Supabase", str(e))
            self.status("Erro ao conectar com Supabase")

    # ----------------------------------------------------- salvar Supabase --
    def salvar(self):
        """Salva os dados: no Supabase (conta logada) ou na planilha (local)."""
        if self.usar_supabase:
            self.salvar_supabase()
        else:
            self.save_excel()

    def _marcar_modificado(self):
        """Marca os dados como alterados (versiona para o salvamento em bg)."""
        self.modified = True
        self._versao += 1

    def _snapshot_dados(self, dfs=None):
        """Copia dos dataframes para enviar (sem depender da UI durante o envio)."""
        dados = {}
        for aba, df in (self.dfs if dfs is None else dfs).items():
            if df is None or df.empty:
                continue
            limpo = df.astype(object).where(pd.notnull(df), None)
            dados[aba] = limpo.to_dict("records")
        return dados

    # ------------------------------------------------ nivel do chaser ----
    def _coluna_nivel(self, df):
        """Coluna do nivel do chaser no dataframe (None se nao existir)."""
        if df is None or df.empty:
            return None
        for coluna in df.columns:
            if coluna_banco(coluna) == "nivelchaser":
                return coluna
        return None

    def _ler_nivel_chaser(self):
        """Le o nivel do chaser do dataframe (um valor por conta)."""
        df = self.dfs.get(ABA_GERAL)
        if df is None or df.empty:
            self.nivel_chaser = NIVEL_CHASER_PADRAO
            return self.nivel_chaser
        coluna = self._coluna_nivel(df)
        if coluna is None:
            # a coluna ainda nao existe no banco: cria no dataframe (so e
            # gravada se a coluna existir de fato no Supabase)
            df[COLUNA_NIVEL] = NIVEL_CHASER_PADRAO
            self.nivel_chaser = NIVEL_CHASER_PADRAO
            return self.nivel_chaser
        for valor in df[coluna].tolist():
            if valor is None:
                continue
            texto = str(valor).strip()
            if texto in ("", "nan", "None"):
                continue
            try:
                self.nivel_chaser = max(0, int(float(texto.split(".")[0])))
            except (TypeError, ValueError):
                continue
            break
        return self.nivel_chaser

    def _nivel_no_banco(self):
        """A coluna user_characters.nivel_chaser existe de verdade?"""
        if not self.usar_supabase:
            return False
        try:
            from supabase_db import colunas_salvaveis
            return "nivelchaser" in colunas_salvaveis(self.supabase, "personagens")
        except Exception:
            falha("conferir a coluna nivelchaser")
            return False

    def definir_nivel_chaser(self, valor):
        """Grava o nivel do chaser (um valor por conta) e salva no banco.

        O valor e um numero INTEIRO >= 0. O salvamento acontece em segundo
        plano (sem travar a tela e sem janela de aviso).
        """
        try:
            numero = int(str(valor).strip())
        except (TypeError, ValueError):
            return False
        if numero < 0:
            return False
        self.nivel_chaser = numero
        df = self.dfs.get(ABA_GERAL)
        if df is not None and not df.empty:
            coluna = self._coluna_nivel(df)
            if coluna is None:
                coluna = COLUNA_NIVEL
                df[coluna] = numero
            else:
                # um valor por conta: grava em todas as linhas
                df[coluna] = numero
        self._atualizar_cards()
        # o perfil do hero mostra o nivel: atualiza em tempo real
        self._desenhar_perfil()
        self._marcar_modificado()
        if self.usar_supabase:
            self._aviso_nivel = ("" if getattr(self, "offline", False)
                                 or self._nivel_no_banco() else
                                 " | nivel_chaser: rode sql/nivel_chaser.sql "
                                 "no Supabase para gravar")
            self.salvar_supabase()
            return True
        self.status(f"Nivel do chaser: {numero}")
        return True

    def _abrir_nivel(self):
        """Abre a janela de edicao do nivel do chaser."""
        try:
            from janela_nivel import JanelaNivelChaser
            JanelaNivelChaser(self)
        except Exception as erro:
            falha("[Nivel] abrir a edicao", erro)
            self.status(f"Erro ao abrir a edicao do nivel: {erro}")

    def salvar_supabase(self):
        """Envia as alteracoes ao Supabase em SEGUNDO PLANO.

        A interface continua utilizavel durante o envio e o resultado aparece
        na barra de status (sem nenhuma janela de aviso).
        """
        if not self.usar_supabase:
            self.status("Supabase nao esta ativado (modo local).")
            return
        if not self.modified:
            self.status("Nenhuma alteracao para salvar.")
            return
        if getattr(self, "offline", False):
            self._guardar_copia(pendente=True)
            self.status("Sem internet: alteração guardada neste computador. "
                        "Ela vai para o banco quando a conexão voltar.")
            return
        if self._salvando:
            self._salvar_pendente = True
            self.status("Salvando… (o proximo salvamento ja esta na fila)")
            return

        self._salvando = True
        self._salvar_pendente = False
        self._versao_salva = self._versao
        self.status("Salvando no Supabase…")
        dados = self._snapshot_dados()
        originais = (self._snapshot_dados(self.originals)
                     if self._originais_do_banco else None)
        # guarda no PC ANTES de enviar: se cair a internet (ou o app
        # fechar) no meio, nada se perde
        self._guardar_copia(pendente=True, dados=dados, originais=originais)

        # O GC nao pode rodar na thread de rede: ele pode finalizar um
        # tkinter.font.Font e travar o Tcl (GIL x Tcl). Desligamos durante o
        # envio e religamos na thread da UI.
        gc.collect()
        gc.disable()
        threading.Thread(target=self._salvar_em_segundo_plano,
                         args=(dados, originais), daemon=True).start()

    def _salvar_em_segundo_plano(self, dados, originais=None):
        """Executa APENAS a parte de rede (nada de Tk nesta thread)."""
        try:
            resultado = salvar_conta(self.supabase, self.user_id, dados,
                                     originais)
            self._fila_salvamento.put(("ok", resultado))
        except Exception as erro:
            falha("[Salvar] enviar ao Supabase", erro)
            self._fila_salvamento.put(("erro", erro))

    def _verificar_salvamento(self):
        """Le o resultado do salvamento (na thread da UI) e atualiza a tela."""
        try:
            while True:
                tipo, payload = self._fila_salvamento.get_nowait()
                self._aplicar_resultado_salvamento(tipo, payload)
        except queue.Empty:
            pass
        except Exception as erro:
            falha("[Salvar] aplicar o resultado", erro)
            self.status(f"Erro ao ler o resultado do salvamento: {erro}")
        self.after(120, self._verificar_salvamento)

    def _aplicar_resultado_salvamento(self, tipo, payload):
        """Aplica o resultado do salvamento (status + cards), sem messagebox."""
        gc.enable()
        try:
            gc.collect()
        except Exception:
            falha("coletar o lixo apos salvar")

        self._salvando = False

        if tipo == "erro":
            self.modified = True
            if cache_local.eh_erro_de_rede(payload):
                # a copia pendente ja foi gravada antes do envio
                self.offline = True
                self.status("Sem internet: alteração guardada neste "
                            "computador. Ela vai para o banco quando a "
                            "conexão voltar.")
                return
            self.status(f"Erro ao salvar no Supabase: {payload}")
            self._salvar_pendente = True
        else:
            salvos = payload.get("salvos") or {}
            perdidas = payload.get("perdidas") or []
            total = sum(salvos.values())
            if self._versao == self._versao_salva:
                # nada mudou durante o envio: pode marcar como salvo
                self.modified = False
                self.originals = {k: v.copy() for k, v in self.dfs.items()}
                self._originais_do_banco = True
                self._guardar_copia(pendente=False)
            else:
                # houve alteracao durante o envio -> salva de novo
                self.modified = True
                self._salvar_pendente = True
            self._atualizar_cards()
            if perdidas:
                self.status("Salvo no Supabase! (" + str(total) + " registros) | "
                            "colunas fora do banco: " + ", ".join(perdidas))
            else:
                self.status(f"Salvo no Supabase! ({total} registros)"
                            + self._aviso_nivel)

        if self._salvar_pendente and self.modified:
            self._salvar_pendente = False
            self.salvar_supabase()

    # ------------------------------------------------------ preferencias ----
    def _ler_preferencia(self):
        """Le a preferencia 'missao_rapida' do user_profiles (se existir)."""
        if not self.usar_supabase or not self.user_id:
            return
        try:
            resp = (self.supabase.table("user_profiles")
                    .select("*").eq("id", self.user_id).limit(1).execute())
            linhas = getattr(resp, "data", None) or []
            if linhas and "missao_rapida" in linhas[0]:
                self.missao_rapida = bool(linhas[0]["missao_rapida"])
        except Exception:
            falha("ler preferencia do perfil")

    def _coluna_perfil_existe(self, coluna):
        """A coluna opcional existe no user_profiles? (sonda, com cache)."""
        cache = getattr(self, "_cache_perfil", None)
        if cache is None:
            cache = {}
            self._cache_perfil = cache
        if coluna not in cache:
            try:
                self.supabase.table("user_profiles").select(coluna) \
                    .limit(1).execute()
                cache[coluna] = True
            except Exception as erro:
                from supabase_db import coluna_ausente
                if not coluna_ausente(erro):
                    falha("conferir coluna do perfil", erro)
                cache[coluna] = False
        return cache[coluna]

    def _ler_ultimo_personagem(self):
        """Le o ultimo personagem usado na missao rapida (se a coluna
        existir no banco; senao, so nesta sessao)."""
        self.ultimo_personagem_missao = None
        if not self.usar_supabase or not self.user_id:
            return
        if not self._coluna_perfil_existe("missao_rapida_personagem"):
            return
        try:
            resp = (self.supabase.table("user_profiles")
                    .select("missao_rapida_personagem")
                    .eq("id", self.user_id).limit(1).execute())
            linhas = getattr(resp, "data", None) or []
            if linhas and linhas[0].get("missao_rapida_personagem"):
                self.ultimo_personagem_missao = \
                    linhas[0]["missao_rapida_personagem"]
        except Exception:
            falha("ler o ultimo personagem da missao")

    def _lembrar_personagem_missao(self, nome):
        """Guarda o ultimo personagem usado (o painel ja abre nele)."""
        self.ultimo_personagem_missao = str(nome)
        if not self.usar_supabase or not self.user_id:
            return False
        if not self._coluna_perfil_existe("missao_rapida_personagem"):
            return False
        try:
            self.supabase.table("user_profiles") \
                .update({"missao_rapida_personagem": str(nome)}) \
                .eq("id", self.user_id).execute()
            return True
        except Exception:
            falha("lembrar o personagem da missao")
            return False

    def _salvar_preferencia(self, nome, valor):
        """Grava uma preferencia no user_profiles (best effort)."""
        if not self.usar_supabase or not self.user_id:
            return False
        try:
            self.supabase.table("user_profiles").update({nome: bool(valor)}) \
                .eq("id", self.user_id).execute()
            return True
        except Exception:
            falha("salvar preferencia do perfil")
            return False

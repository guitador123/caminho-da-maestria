# -*- coding: utf-8 -*-
"""
Modo offline da tela principal (`GrandChaseApp` herda de `OfflineMixin`).

  - cada carga e cada salvamento gravam a copia da conta neste PC
    (cache_local.py);
  - sem internet (no login ou no meio do uso), o app trabalha com a copia:
    salvar guarda a alteracao no PC, marcada como pendente;
  - a cada 20 s, offline, ele tenta reconectar (com a sessao guardada; se
    ela tiver expirado, pede a senha UMA vez) e, de volta, envia o que
    ficou pendente pelo salvamento normal: so os personagens alterados
    aqui (o resto fica como esta no banco).
"""

from datetime import datetime

import customtkinter as ctk
import pandas as pd

import auth
import cache_local
from registro import falha, registrar

INTERVALO_SINCRONIA = 20_000      # ms


class OfflineMixin:

    def _iniciar_offline(self, offline=False):
        self.offline = bool(offline) and self.usar_supabase
        self._sincronizando = False
        self._pediu_senha = False
        self._versao_no_pc = -1        # versao ja guardada na copia local
        self._ouvir_token()
        self.after(INTERVALO_SINCRONIA, self._tentar_sincronizar)

    def _ouvir_token(self):
        """O Supabase troca o token da sessao de tempos em tempos: guarda o
        novo (e com ele que o app reconecta depois de abrir offline)."""
        if not self.user_id:
            return
        uid = self.user_id

        def ao_mudar(_evento, sessao):
            if sessao is not None:
                cache_local.atualizar_token(
                    uid, getattr(sessao, "refresh_token", None))
        try:
            self.supabase.auth.on_auth_state_change(ao_mudar)
        except Exception:
            falha("[Offline] ouvir a troca do token")

    # ------------------------------------------------------ a copia ----
    def _perfil_para_copia(self):
        return {"nick": self.perfil_nick,
                "avatar": self.perfil_personagem or self.perfil_avatar or "",
                "missao_rapida": bool(self.missao_rapida),
                "missao_rapida_personagem": self.ultimo_personagem_missao}

    def _guardar_copia(self, pendente, dados=None, originais=False):
        """Grava a copia da conta neste PC (pendente = falta enviar)."""
        if not self.usar_supabase or not self.user_id:
            return False
        if dados is None:
            dados = self._snapshot_dados()
        if originais is False:
            originais = (self._snapshot_dados(self.originals)
                         if self._originais_do_banco else None)
        ok = cache_local.salvar_copia(self.user_id, dados, originais,
                                      self._perfil_para_copia(), pendente)
        if ok:
            self._versao_no_pc = self._versao if pendente else -1
        return ok

    def _salvo_neste_pc(self):
        """A alteracao atual ja esta guardada na copia local?"""
        return getattr(self, "_versao_no_pc", -1) == self._versao

    def _carregar_da_copia(self):
        """Mostra a copia deste PC (sem internet). True se havia copia."""
        copia = cache_local.ler_copia(self.user_id)
        if not copia:
            self.status("Sem conexão com o Supabase e sem cópia dos dados "
                        "neste computador.")
            return False
        self._limpar_abas()
        originais = copia.get("originais")
        for nome, linhas in copia["dados"].items():
            if not linhas:
                continue
            df = pd.DataFrame(linhas)
            self.dfs[nome] = df
            base = (originais or {}).get(nome)
            self.originals[nome] = (pd.DataFrame(base) if base is not None
                                    else df.copy())
            if self.mostrar_tabela:
                self._criar_aba(nome, df)
        self._originais_do_banco = originais is not None
        self._versao = 0
        self.modified = bool(copia.get("pendente"))
        self._versao_no_pc = 0 if self.modified else -1
        perfil = copia.get("perfil") or {}
        self._aplicar_perfil(perfil)
        self.missao_rapida = bool(perfil.get("missao_rapida",
                                             self.missao_rapida))
        self.ultimo_personagem_missao = perfil.get("missao_rapida_personagem")
        self._ler_nivel_chaser()
        self._atualizar_cards()
        try:
            self._desenhar_perfil()
        except Exception:
            falha("[Offline] desenhar o perfil")
        quando = _data_curta(copia.get("atualizado_em"))
        pendente = (" | alterações pendentes: vão para o banco quando a "
                    "internet voltar" if self.modified else "")
        self.status(f"Modo offline: cópia deste computador ({quando})"
                    + pendente)
        registrar(f"[Offline] carregou a copia local ({quando})")
        return True

    def _enviar_pendente_da_copia(self):
        """Antes de carregar do banco: o que ficou pendente de uma sessao
        offline anterior vai primeiro (senao a carga apagaria). Devolve
        True para seguir com a carga normal."""
        copia = cache_local.ler_copia(self.user_id)
        if not copia or not copia.get("pendente"):
            return True
        from supabase_db import salvar_conta
        try:
            salvar_conta(self.supabase, self.user_id, copia["dados"],
                         copia.get("originais"))
            cache_local.salvar_copia(self.user_id, copia["dados"],
                                     copia["dados"], copia.get("perfil"),
                                     pendente=False)
            registrar("[Offline] alteracoes pendentes enviadas na abertura")
            self._nota_sincronia = " | alterações feitas offline enviadas"
            return True
        except Exception as erro:
            falha("[Offline] enviar as alteracoes pendentes", erro)
            if cache_local.eh_erro_de_rede(erro):
                self.offline = True
            self._carregar_da_copia()
            return False

    # ---------------------------------------------------- reconectar ----
    def _tentar_sincronizar(self):
        try:
            if (getattr(self, "offline", False) and self.usar_supabase
                    and not self._sincronizando):
                self._sincronizando = True
                self._em_segundo_plano(self._reconectar, self._ao_reconectar)
        except Exception:
            falha("[Offline] tentar sincronizar")
        finally:
            try:
                self.after(INTERVALO_SINCRONIA, self._tentar_sincronizar)
            except Exception:
                pass                    # janela fechada

    def _reconectar(self):
        """(thread de rede) 'online', 'rede' (ainda sem internet) ou
        'senha' (a sessao guardada expirou)."""
        try:
            autenticacao = self.supabase.auth
            if autenticacao.get_session() is None:
                token = cache_local.token_da_conta(self.user_id)
                if not token:
                    return "senha"
                autenticacao.refresh_session(token)
            (self.supabase.table("user_profiles").select("id")
             .limit(1).execute())
            return "online"
        except Exception as erro:
            if cache_local.eh_erro_de_rede(erro):
                return "rede"
            falha("[Offline] reabrir a sessao", erro)
            return "senha"

    def _ao_reconectar(self, _ok, resultado):
        self._sincronizando = False
        if resultado == "online":
            self._voltou_online()
        elif resultado == "senha" and not self._pediu_senha:
            self._pediu_senha = True
            self._pedir_senha()

    def _voltou_online(self):
        self.offline = False
        registrar("[Offline] conexao de volta")
        if self.modified:
            self.status("Conexão de volta: enviando as alterações feitas "
                        "offline…")
            self.salvar_supabase()
        else:
            self.status("Conexão de volta.")
        # o que nao deu para ler offline (resumo semanal, 9o cartao)
        try:
            self._verificar_resumo_semanal()
        except Exception:
            falha("[Offline] resumo semanal ao reconectar")

    def _pedir_senha(self):
        try:
            JanelaSenha(self)
        except Exception as erro:
            falha("[Offline] pedir a senha", erro)

    def _entrar_de_novo(self, senha):
        """Login com a senha (sessao expirada). Devolve a mensagem de erro
        ou None se entrou."""
        try:
            sb, resp = auth.login(self.email_usuario, senha)
        except Exception as erro:
            if cache_local.eh_erro_de_rede(erro):
                return "Ainda sem internet. Tente de novo em instantes."
            from login import mensagem_erro
            return mensagem_erro(erro)
        user = getattr(resp, "user", None)
        if user is None or str(user.id) != str(self.user_id):
            return "Essa não é a conta aberta no aplicativo."
        self.supabase = sb
        self._ouvir_token()
        if cache_local.conta_memorizada(self.email_usuario):
            cache_local.memorizar_conta(
                self.email_usuario, user.id, senha,
                getattr(getattr(resp, "session", None), "refresh_token", None))
        self._voltou_online()
        return None


def _data_curta(texto):
    try:
        return datetime.fromisoformat(texto).strftime("%d/%m %H:%M")
    except Exception:
        return "sem data"


class JanelaSenha(ctk.CTkToplevel):
    """A internet voltou, mas a sessao guardada expirou: pede a senha uma
    vez para enviar o que foi feito offline."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Reconectar")
        self.resizable(False, False)
        self.configure(fg_color="#191334")
        try:
            import caminhos
            caminhos.aplicar_icone(self)
        except Exception:
            falha("icone da janela de senha")
        ctk.CTkLabel(self, text="A internet voltou", text_color="#ffffff",
                     font=ctk.CTkFont(size=18, weight="bold")).pack(
            padx=24, pady=(20, 4), anchor="w")
        ctk.CTkLabel(self, justify="left", wraplength=340,
                     text_color="#b8b2ce",
                     text=("Para enviar ao banco o que foi feito offline, "
                           f"confirme a senha de {app.email_usuario}.")).pack(
            padx=24, anchor="w")
        self.entrada = ctk.CTkEntry(self, show="*", width=340)
        self.entrada.pack(padx=24, pady=(14, 4))
        self.erro = ctk.CTkLabel(self, text="", text_color="#fb7185",
                                 wraplength=340, justify="left")
        self.erro.pack(padx=24, anchor="w")
        botoes = ctk.CTkFrame(self, fg_color="transparent")
        botoes.pack(padx=24, pady=(8, 20), fill="x")
        ctk.CTkButton(botoes, text="Agora não", width=110,
                      fg_color="#3d3460", command=self.destroy).pack(
            side="right")
        ctk.CTkButton(botoes, text="Entrar", width=110,
                      fg_color="#8b5cf6", command=self.entrar).pack(
            side="right", padx=(0, 8))
        self.entrada.bind("<Return>", lambda _e: self.entrar())
        self.after(150, self.entrada.focus_set)
        self.transient(app)

    def entrar(self):
        self.erro.configure(text="Conferindo…")
        self.update()
        mensagem = self.app._entrar_de_novo(self.entrada.get())
        if mensagem:
            self.erro.configure(text=mensagem)
            return
        self.destroy()

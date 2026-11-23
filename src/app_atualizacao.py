# -*- coding: utf-8 -*-
"""
Botao "Versao X.Y.Z" da tela principal: procura atualizacao na hora.

Parte da tela principal (`GrandChaseApp` herda de `AtualizacaoMixin`).

O trabalho de rede (verificar, baixar) roda numa thread SEM nada de Tk; o
resultado volta para a thread da UI por polling (`after`), como no
salvamento. O GC fica desligado durante a thread (senao ele pode finalizar
um objeto do Tk na thread de rede e travar o Tcl: GIL x Tcl).
"""

import gc
import os
import threading
from tkinter import messagebox

import atualizacao
from registro import falha, registrar
from versao_app import VERSAO


class AtualizacaoMixin:

    def procurar_atualizacao(self):
        """Clique no botao da versao: verifica se ha versao nova."""
        if getattr(self, "_atualizando", False):
            self.status("Já estou procurando atualização...")
            return
        self._atualizando = True
        self.status(f"Versão {VERSAO}: procurando atualização...")
        self._em_segundo_plano(atualizacao.procurar_atualizacao,
                               self._resultado_da_procura)

    def _resultado_da_procura(self, ok, resultado):
        self._atualizando = False
        if not ok or resultado.get("erro"):
            self.status("Não foi possível procurar atualização agora "
                        "(sem internet ou o GitHub fora do ar).")
            return
        if not resultado.get("nova"):
            self.status(f"Você já está na versão mais recente ({VERSAO}).")
            return

        nova = resultado.get("versao") or ""
        titulo = f"Versão {nova} disponível" if nova else "Versão nova disponível"
        if self.modified or getattr(self, "_salvando", False):
            self.status(titulo + ": salve as alterações antes de atualizar.")
            messagebox.showwarning(
                titulo,
                "Você tem alterações que ainda não foram salvas.\n\n"
                "Salve primeiro e clique de novo em "
                f"\"Versão {VERSAO}\" para atualizar.", parent=self)
            return
        if not messagebox.askyesno(
                titulo,
                f"Você está na versão {VERSAO}.\n\n"
                "O programa vai fechar, atualizar e abrir de novo sozinho "
                "(leva cerca de um minuto).\n\nAtualizar agora?", parent=self):
            self.status(titulo + " (atualize quando quiser pelo botão "
                        f"\"Versão {VERSAO}\").")
            return

        self._atualizando = True
        self.status("Baixando a atualização... (o programa vai fechar e "
                    "abrir de novo)")
        self._em_segundo_plano(atualizacao.aplicar_atualizacao,
                               self._resultado_da_atualizacao)

    def _resultado_da_atualizacao(self, ok, deu_certo):
        self._atualizando = False
        if ok and deu_certo:
            registrar("[Atualizacao] aplicada pelo botao; o programa vai "
                      "abrir de novo")
            # o auxiliar (ja agendado) troca os arquivos depois que o app
            # fecha e abre a versao nova; o app precisa sair AGORA
            try:
                self._liberar_recursos()
            except Exception:
                falha("liberar recursos antes de atualizar")
            os._exit(0)
        self.status("Não foi possível atualizar agora. O programa continua "
                    f"na versão {VERSAO} (detalhes no log).")
        messagebox.showerror(
            "Atualização",
            "Não foi possível atualizar agora.\n\nO programa continua na "
            f"versão {VERSAO}. Tente de novo mais tarde.", parent=self)

    # ------------------------------------------------------------ thread --
    def _em_segundo_plano(self, trabalho, ao_terminar):
        """Roda `trabalho()` numa thread e chama `ao_terminar(ok, valor)`
        na thread da UI."""
        caixa = {}

        def alvo():
            try:
                caixa["valor"] = trabalho()
                caixa["ok"] = True
            except Exception as erro:
                falha(f"[Atualizacao] {getattr(trabalho, '__name__', '')}",
                      erro)
                caixa["valor"] = None
                caixa["ok"] = False

        def conferir():
            if "ok" not in caixa:
                self.after(150, conferir)
                return
            gc.enable()
            ao_terminar(caixa["ok"], caixa["valor"])

        gc.collect()
        gc.disable()
        threading.Thread(target=alvo, daemon=True).start()
        self.after(150, conferir)

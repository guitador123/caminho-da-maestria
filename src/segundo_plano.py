# -*- coding: utf-8 -*-
"""
O coletor de lixo (gc) durante o trabalho em segundo plano.

O gc NAO pode rodar numa thread de rede: ele pode finalizar uma imagem ou
fonte do Tk fora da thread da tela, e o Tcl derruba o app sem mensagem.
Por isso o gc fica DESLIGADO enquanto ha trabalho em segundo plano.

Antes, cada trabalho desligava ao comecar e religava ao terminar. Com dois
ao mesmo tempo (ex.: a lista da Guilda e a conta de alguem), o primeiro a
terminar religava o gc com o outro ainda rodando. Agora e uma CONTAGEM:
religa so quando o ultimo termina.

Chame `comecar()` e `terminar()` na thread da tela.
"""

import gc
import threading

_trava = threading.Lock()
_ativos = 0


def comecar():
    """Um trabalho vai comecar: o 1o desliga o gc (depois de uma coleta)."""
    global _ativos
    with _trava:
        if _ativos == 0:
            gc.collect()
            gc.disable()
        _ativos += 1


def terminar():
    """Um trabalho terminou: o ultimo religa o gc e coleta o que sobrou."""
    global _ativos
    with _trava:
        _ativos = max(0, _ativos - 1)
        if _ativos:
            return
        gc.enable()
    gc.collect()


def ativos():
    return _ativos

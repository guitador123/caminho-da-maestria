# -*- coding: utf-8 -*-
"""
Registro (log) de erros do app.

Antes, cerca de 70 `except Exception: pass` escondiam qualquer erro, e bugs
reais passavam despercebidos (o aviso do auto-update ficou quebrado assim).
Agora todo erro inesperado vai para o log:

    %LOCALAPPDATA%\\Caminho da Maestria\\gc_app.log

Uso:

    from registro import registrar, falha, protegido

    registrar("[Salvar] 3 linhas enviadas")      # uma linha no log

    try:
        ...
    except Exception:
        falha("ler o perfil")                    # tipo, mensagem e traceback
        return {}

    with protegido("apagar os cards", ignorar=TclError):
        self.canvas.delete(item)                 # TclError = janela ja
                                                 # fechada (esperado, sem log)

O mesmo erro no mesmo lugar so e registrado uma vez por sessao, para que um
erro dentro de um laco de desenho nao encha o arquivo.
"""

import contextlib
import os
import sys
import threading
import time
import traceback

PASTA = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                     "Caminho da Maestria")
ARQUIVO = os.path.join(PASTA, "gc_app.log")
LIMITE_BYTES = 1_000_000          # acima disso, vira gc_app.log.1

_trava = threading.Lock()
_ja_registrados = set()


def _rodar_se_grande():
    try:
        if os.path.getsize(ARQUIVO) > LIMITE_BYTES:
            antigo = ARQUIVO + ".1"
            if os.path.exists(antigo):
                os.remove(antigo)
            os.replace(ARQUIVO, antigo)
    except OSError:
        pass                      # ainda nao existe, ou outro processo usa


def registrar(mensagem):
    """Escreve uma linha no console (se houver) e no arquivo de log."""
    texto = str(mensagem)
    # no .exe sem console o sys.stdout e None: o print levantaria excecao
    if sys.stdout is not None:
        try:
            print(texto)
        except (OSError, ValueError, UnicodeError):
            pass                  # console fechado ou sem suporte ao texto
    linha = f"{time.strftime('%d/%m %H:%M:%S')} {texto}\n"
    with _trava:
        try:
            os.makedirs(PASTA, exist_ok=True)
            _rodar_se_grande()
            with open(ARQUIVO, "a", encoding="utf-8") as arquivo:
                arquivo.write(linha)
        except OSError:
            pass                  # sem onde gravar: o log e o ultimo recurso


def falha(contexto, erro=None):
    """Registra a excecao atual (ou `erro`) com o traceback.

    Chame dentro de um `except`. Devolve o texto curto do erro, util para
    mostrar na barra de status.
    """
    if erro is None:
        erro = sys.exc_info()[1]
    resumo = f"{type(erro).__name__}: {erro}" if erro else "erro desconhecido"
    chave = (contexto, type(erro).__name__)
    if chave in _ja_registrados:
        return resumo
    _ja_registrados.add(chave)
    detalhes = ""
    if erro is not None and erro.__traceback__ is not None:
        detalhes = "".join(traceback.format_exception(
            type(erro), erro, erro.__traceback__)).rstrip()
        detalhes = "\n    " + detalhes.replace("\n", "\n    ")
    registrar(f"[ERRO] {contexto}: {resumo}{detalhes}")
    return resumo


@contextlib.contextmanager
def protegido(contexto, ignorar=()):
    """Bloco que nunca derruba o app: erros esperados (`ignorar`) passam em
    silencio; qualquer outro vai para o log com `falha(contexto)`."""
    try:
        yield
    except ignorar:
        pass
    except Exception:
        falha(contexto)

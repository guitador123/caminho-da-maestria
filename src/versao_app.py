# -*- coding: utf-8 -*-
"""
A versao do Caminho da Maestria que aparece para o usuario (botao
"Versao X.Y.Z" da tela principal).

Suba o numero ANTES de publicar uma release (scripts/publicar_release.py
se recusa a publicar a mesma versao duas vezes):

    1.0.0 -> 1.0.1   correcao (nada novo para o usuario)
    1.0.0 -> 1.1.0   novidade (funcionalidade nova)
    1.0.0 -> 2.0.0   mudanca grande (muda o jeito de usar)

Por baixo, o auto-update continua comparando o COMMIT (o nome da release
no GitHub e v<data>-<commit>); este numero vai no TITULO da release.
"""

VERSAO = "1.3.2"

# -*- coding: utf-8 -*-
"""
Caminhos de arquivos do app (fonte e executavel congelado).

O build onedir do PyInstaller 6 coloca os arquivos de dados em `_internal`.
"""

import os
import sys


def app_dir():
    """Pasta do app: fonte = pasta do .py; congelado = pasta do .exe."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def assets_dir():
    """Pasta dos arquivos que acompanham o app (imagens)."""
    if getattr(sys, "frozen", False):
        interno = os.path.join(os.path.dirname(sys.executable), "_internal")
        if os.path.isdir(interno):
            return interno
    return app_dir()


def icone_app():
    """Icone do app (o emblema do Akkatsuki, em .ico)."""
    return os.path.join(assets_dir(), "assets", "app.ico")


def aplicar_icone(widget):
    """Coloca o icone do app (assets/app.ico) na janela."""
    try:
        caminho = icone_app()
        if os.path.exists(caminho):
            widget.iconbitmap(caminho)
    except Exception:
        from registro import falha
        falha("aplicar o icone da janela")


def fundo_principal():
    """Imagem de fundo da tela principal."""
    return os.path.join(assets_dir(), "assets", "background.jpg")


def fundo_login():
    """Imagem (logo) de fundo da tela de login."""
    return os.path.join(assets_dir(), "assets", "login.png")


def planilha_padrao():
    return os.path.join(app_dir(), "Controle Grand Chase (1).xlsx")


def banco_sqlite():
    return os.path.join(app_dir(), "controle_gc.db")


def arquivo_log():
    """Log do app (fora da pasta do programa, que pode nao ser gravavel)."""
    from registro import ARQUIVO
    return ARQUIVO


def preferencias():
    """Arquivo JSON com as preferencias locais (conta memorizada)."""
    return os.path.join(app_dir(), "login_prefs.json")

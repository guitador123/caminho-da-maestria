# -*- coding: utf-8 -*-
"""Diagnóstico local do Caminho da Maestria.

Execute com:
    python tools/debug_app.py

O relatório é salvo em gc_app_debug.txt, próximo ao app.
Não envia dados nem imprime chaves ou credenciais.
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import platform
import sys
import traceback
from datetime import datetime

import caminhos


def verificar_arquivo(relativo: str) -> tuple[bool, str]:
    caminho = os.path.abspath(os.path.join(caminhos.app_dir(), relativo))
    if os.path.exists(caminho):
        tamanho = os.path.getsize(caminho)
        return True, f"OK  {relativo} ({tamanho:,} bytes)"
    return False, f"FALTA  {relativo}"


def verificar_import(nome: str) -> str:
    try:
        modulo = __import__(nome)
        versao = getattr(modulo, "__version__", "")
        return f"OK  {nome}" + (f" {versao}" if versao else "")
    except Exception as exc:
        return f"ERRO  {nome}: {type(exc).__name__}: {exc}"


def main() -> int:
    linhas = [
        "CAMINHO DA MAESTRIA - RELATORIO DE DIAGNOSTICO",
        "=" * 62,
        f"Data/hora: {datetime.now():%d/%m/%Y %H:%M:%S}",
        f"Sistema: {platform.system()} {platform.release()} ({platform.machine()})",
        f"Python: {sys.version.replace(chr(10), ' ')}",
        f"Modo executável: {bool(getattr(sys, 'frozen', False))}",
        f"Pasta do app: {caminhos.app_dir()}",
        f"Pasta dos assets: {caminhos.assets_dir()}",
        "",
        "DEPENDENCIAS",
        "-" * 62,
    ]

    for pacote in ("customtkinter", "pandas", "openpyxl", "PIL", "supabase", "qrcode", "numpy"):
        linhas.append(verificar_import(pacote))

    linhas.extend(["", "ARQUIVOS ESSENCIAIS", "-" * 62])
    problemas = 0
    for arquivo in (
        "app_grandchase.py", "src/app_grandchase.py", "src/login.py",
        "src/auth.py", "src/supabase_db.py",
        "assets/background.jpg", "assets/login.png", "assets/app.ico",
        "assets/personagens", "assets/perfil", "assets/chaser",
    ):
        ok, texto = verificar_arquivo(arquivo)
        linhas.append(texto)
        problemas += not ok

    linhas.extend(["", "CONEXAO SUPABASE", "-" * 62])
    try:
        import auth
        client = auth.get_supabase()
        resp = client.auth.get_session()
        linhas.append("OK  Cliente Supabase criado")
        linhas.append("OK  Endpoint respondeu" if resp is not None else "AVISO  Sem sessão ativa")
    except Exception as exc:
        linhas.append(f"ERRO  Supabase: {type(exc).__name__}: {exc}")
        problemas += 1

    linhas.extend(["", "LOGS LOCAIS", "-" * 62])
    for titulo, caminho in (
        ("App", caminhos.arquivo_log()),
        ("Atualização", os.path.join(os.environ.get("LOCALAPPDATA", ""),
                                     "Caminho da Maestria", "log_atualizacao.log")),
    ):
        if caminho and os.path.exists(caminho):
            linhas.append(f"OK  {titulo}: {caminho}")
        else:
            linhas.append(f"SEM LOG  {titulo}")

    linhas.extend(["", "RESUMO", "-" * 62])
    linhas.append("Problemas encontrados: " + str(problemas))
    linhas.append("Teste o app normalmente e, em caso de falha, envie este relatório.")

    destino = os.path.join(caminhos.app_dir(), "gc_app_debug.txt")
    texto = "\n".join(linhas) + "\n"
    try:
        with open(destino, "w", encoding="utf-8") as arquivo:
            arquivo.write(texto)
    except Exception as exc:
        traceback.print_exc()
        print("Não foi possível salvar o relatório:", exc)
        return 1

    print(texto)
    print(f"Relatório salvo em: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

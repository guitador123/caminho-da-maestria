# -*- coding: utf-8 -*-
"""
Credenciais da conta de teste (para os scripts teste_*.py).

A senha NUNCA fica no codigo (o repositorio e publico). Ordem de busca:

  1. argumentos da linha de comando:  python teste_x.py email senha
  2. variaveis de ambiente:           GC_TESTE_EMAIL e GC_TESTE_SENHA
  3. arquivo local `.env.teste` (fica fora do git), com as linhas:

        GC_TESTE_EMAIL=teste@teste.com
        GC_TESTE_SENHA=a-senha-da-conta-de-teste

O e-mail tem um padrao (teste@teste.com); a senha nao.
"""

import os
import sys

EMAIL_PADRAO = "teste@teste.com"
ARQUIVO_LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             ".env.teste")


def _ler_arquivo_local():
    """Le o `.env.teste` (CHAVE=valor por linha); {} se nao existir."""
    valores = {}
    try:
        with open(ARQUIVO_LOCAL, "r", encoding="utf-8-sig") as arquivo:
            for linha in arquivo:
                linha = linha.strip()
                if not linha or linha.startswith("#") or "=" not in linha:
                    continue
                chave, valor = linha.split("=", 1)
                valores[chave.strip()] = valor.strip().strip('"').strip("'")
    except OSError:
        pass
    return valores


def conta_teste(argv=None, inicio=1):
    """(email, senha) da conta de teste.

    `argv[inicio]` e `argv[inicio + 1]`, se vierem, tem prioridade.
    Sem senha em lugar nenhum, encerra com uma explicacao.
    """
    argv = sys.argv if argv is None else argv
    email = argv[inicio] if len(argv) > inicio else None
    senha = argv[inicio + 1] if len(argv) > inicio + 1 else None

    local = _ler_arquivo_local()
    email = (email or os.environ.get("GC_TESTE_EMAIL")
             or local.get("GC_TESTE_EMAIL") or EMAIL_PADRAO)
    senha = (senha or os.environ.get("GC_TESTE_SENHA")
             or local.get("GC_TESTE_SENHA"))
    if not senha:
        raise SystemExit(
            "Falta a senha da conta de teste.\n"
            "  - defina a variavel de ambiente GC_TESTE_SENHA, ou\n"
            "  - crie o arquivo .env.teste com a linha GC_TESTE_SENHA=...\n"
            "  - ou passe na linha de comando: python <teste>.py email senha")
    return email, senha

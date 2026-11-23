# -*- coding: utf-8 -*-
"""
Grava a versao (o commit) no arquivo `assets/versao.txt`.

O .exe usa esse arquivo para saber de qual commit ele foi feito: e
com isso que ele descobre que ha versao nova no GitHub.

    python gravar_versao.py

(roda antes de empacotar o .exe)
"""

import io
import os
import subprocess
import sys
from datetime import datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
DESTINO = os.path.join(RAIZ, "assets", "versao.txt")


def commit_atual():
    """O commit atual (acha o git mesmo fora do PATH)."""
    try:
        from atualizacao import caminho_git
        git = caminho_git()
    except Exception:
        git = "git"
    try:
        resultado = subprocess.run([git, "rev-parse", "HEAD"], cwd=RAIZ,
                                   capture_output=True, text=True,
                                   encoding="utf-8", errors="replace",
                                   timeout=60)
        sha = resultado.stdout.strip()
        if sha:
            return sha[:40]
        print(f"AVISO: git rev-parse nao devolveu o commit: "
              f"{resultado.stderr.strip()}")
    except Exception as erro:
        print(f"AVISO: nao deu para ler o commit ({erro})")
    return ""


def main():
    sha = commit_atual()
    if not sha:
        print("[AVISO] nao consegui ler o commit do git")
        sha = "sem-git"
    agora = datetime.now().strftime("%Y-%m-%d %H:%M")
    os.makedirs(os.path.dirname(DESTINO), exist_ok=True)
    with io.open(DESTINO, "w", encoding="utf-8", newline="\n") as arquivo:
        arquivo.write(sha + "\n")
        arquivo.write(agora + "\n")
    print(f"[OK] {DESTINO}")
    print(f"     versao: {sha} ({agora})")


if __name__ == "__main__":
    main()

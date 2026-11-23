# -*- coding: utf-8 -*-
"""
Publica uma versao nova no GitHub, para o **.exe** se atualizar sozinho.

O que ele faz:
  1. grava a versao (o commit) em `assets/versao.txt`;
  2. empacota o programa (pyinstaller);
  3. monta o .zip da release;
  4. assina o .zip (assinatura.py) e gera o `<zip>.sig`;
  5. cria a release no GitHub (com `gh release create`).

Precisa da chave privada de assinatura neste PC (veja assinatura.py).

Depois disso, qualquer .exe instalado que abrir o programa:
  - ve que a release e nova;
  - baixa o .zip;
  - troca os arquivos e abre de novo.

    python scripts/publicar_release.py

A VERSAO que aparece para o usuario ("1.4.0") vem de src/versao_app.py:
suba o numero (e faca o commit) ANTES de publicar. O script recusa
publicar uma versao que ja saiu. O NOME da release continua
v<data>-<commit> (e por ele que os .exe instalados se atualizam); a versao
vai no titulo.
"""

import io
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime

# este script fica em scripts/; a raiz do projeto e a pasta de cima
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(RAIZ, "src"))   # assinatura, atualizacao
DIST = os.path.join(RAIZ, "dist", "Caminho da Maestria")
SAIDA = os.path.join(RAIZ, "instalador")
# sem espaco: o GitHub troca espaco por ponto no nome do asset
# e o app baixa por este nome
NOME_ZIP = "Caminho-da-Maestria.zip"
GH = r"C:\Program Files\GitHub CLI\gh.exe"
PYTHON = sys.executable


def rodar(comando, **opcoes):
    print("   $", " ".join(str(c) for c in comando[:6]), "...")
    return subprocess.run(comando, capture_output=True, text=True,
                          encoding="utf-8", errors="replace",
                          cwd=opcoes.get("cwd", RAIZ),
                          timeout=opcoes.get("timeout", 3600))


def versoes_publicadas():
    """Os numeros de versao (1.4.0) que ja estao no titulo de alguma
    release no GitHub."""
    from atualizacao import _numero_da_versao
    resultado = rodar([GH, "release", "list", "--limit", "200", "--json",
                       "name", "--repo", "guitador123/caminho-da-maestria"])
    if resultado.returncode != 0:
        raise SystemExit("ERRO: nao deu para listar as releases no GitHub:\n"
                         + resultado.stderr.strip()[-600:])
    import json
    return {_numero_da_versao(item.get("name", ""))
            for item in json.loads(resultado.stdout or "[]")} - {""}


def main():
    if sys.argv[1:]:
        raise SystemExit("A versao agora vem de src/versao_app.py (nao "
                         "passe argumentos). Suba o numero la e rode de novo.")

    from versao_app import VERSAO
    if VERSAO in versoes_publicadas():
        raise SystemExit(
            f"ERRO: a versao {VERSAO} ja foi publicada.\n"
            "Suba o numero em src/versao_app.py (1.0.1 = correcao, "
            "1.1.0 = novidade, 2.0.0 = mudanca grande), faca o commit e "
            "rode de novo.")
    print(f"versao: {VERSAO}")

    # o NOME da release (tag) leva o commit: e assim o .exe sabe se a
    # release e mais nova que ele (sem isso ele ficaria tentando atualizar)
    try:
        from atualizacao import caminho_git
        sha = subprocess.run([caminho_git(), "rev-parse", "HEAD"],
                             cwd=RAIZ, capture_output=True, text=True,
                             encoding="utf-8", errors="replace",
                             timeout=60).stdout.strip()[:7]
    except Exception:
        sha = ""
    if not sha:
        raise SystemExit("ERRO: nao deu para ler o commit (git): sem ele os "
                         ".exe instalados nao reconhecem a release")
    versao = "v" + datetime.now().strftime("%Y.%m.%d") + "-" + sha

    # sem a chave privada nao da para assinar: para ANTES do build longo
    import assinatura
    if not os.path.exists(assinatura.caminho_chave_privada()):
        raise SystemExit(
            "ERRO: a chave de assinatura nao existe neste PC:\n"
            f"  {assinatura.caminho_chave_privada()}\n"
            "Restaure a sua copia (ou, so na primeira vez: "
            "python assinatura.py gerar)")
    if assinatura.chave_publica_da_privada() != assinatura.CHAVE_PUBLICA_HEX:
        raise SystemExit("ERRO: a chave privada deste PC nao e a da chave "
                         "publica embutida no app (assinatura.py)")

    print("1) gravando a versao...")
    resultado = rodar([PYTHON, os.path.join("scripts", "gravar_versao.py")])
    print(resultado.stdout.strip())

    print("\n2) empacotando o programa (pyinstaller)...")
    resultado = rodar([PYTHON, "-m", "PyInstaller", "Controle Grand Chase.spec",
                        "--noconfirm", "--distpath", "dist",
                        "--workpath", "build"], timeout=3600)
    if resultado.returncode != 0:
        print(resultado.stdout[-1500:])
        print(resultado.stderr[-800:])
        raise SystemExit("ERRO no build")

    # 3) o instalador (ele RECRIA a pasta instalador/, entao vem
    #    antes do .zip do programa)
    print("\n3) montando o instalador (com o programa dentro)...")
    instalador = os.path.join(RAIZ, "instalador")
    try:
        resultado = rodar([PYTHON, os.path.join("scripts", "gerar_instalador.py")],
                          timeout=3600)
        print(resultado.stdout.strip()[-400:])
    except Exception as erro:
        print("AVISO: nao consegui montar o instalador:", erro)

    # 4) o .zip do programa (o que o .exe baixa para se atualizar)
    print("\n4) montando o .zip da release...")
    if not os.path.exists(os.path.join(DIST, "Caminho da Maestria.exe")):
        raise SystemExit(f"o build nao esta em {DIST}")
    os.makedirs(SAIDA, exist_ok=True)
    zip_caminho = os.path.join(SAIDA, NOME_ZIP)
    if os.path.exists(zip_caminho):
        os.remove(zip_caminho)
    with zipfile.ZipFile(zip_caminho, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as pacote:
        for base, _pastas, arquivos in os.walk(DIST):
            for arquivo in arquivos:
                caminho = os.path.join(base, arquivo)
                pacote.write(caminho,
                             os.path.relpath(caminho, DIST))
    print(f"    {zip_caminho} "
          f"({os.path.getsize(zip_caminho) / (1024 * 1024):.0f} MB)")

    # 5) a auditoria (o pacote nao pode ter segredo)
    print("\n5) auditando o pacote...")
    resultado = rodar([PYTHON, os.path.join("scripts", "auditoria_instalador.py")])
    if "APROVADO" not in resultado.stdout:
        print(resultado.stdout[-800:])
        raise SystemExit("ERRO: o pacote tem segredo (veja o relatorio)")

    # 6) a assinatura (o .exe instalado SO aceita a atualizacao se bater)
    print("\n6) assinando o .zip (Ed25519)...")
    import assinatura
    sig_caminho = zip_caminho + ".sig"
    conteudo_sig = assinatura.assinar(zip_caminho)
    with open(sig_caminho, "w", encoding="ascii", newline="\n") as arquivo:
        arquivo.write(conteudo_sig)
    if not assinatura.verificar(zip_caminho, conteudo_sig):
        raise SystemExit("ERRO: a assinatura nao confere com a chave "
                         "publica embutida no app (assinatura.py)")
    print(f"    {sig_caminho}")

    print("\n7) publicando a release no GitHub...")
    # se ja existe uma release com esse nome, apaga (para republicar)
    antigo_release = rodar([GH, "release", "view", versao, "--repo",
                            "guitador123/caminho-da-maestria"])
    if antigo_release.returncode == 0:
        print("    (a release antiga existe, apagando...)")
        rodar([GH, "release", "delete", versao, "--yes", "--cleanup-tag",
               "--repo", "guitador123/caminho-da-maestria"])
    notas = (f"Versao {VERSAO} de {datetime.now():%d/%m/%Y %H:%M} "
             f"(commit {versao.rsplit('-', 1)[-1]}).\n\n"
             "O .exe instalado baixa esta versao sozinho na proxima vez "
             "que for aberto.")
    arquivos = [zip_caminho, sig_caminho]
    instalador_zip = os.path.join(instalador, "Caminho-da-Maestria-Instalador.zip")
    if os.path.exists(instalador_zip):
        arquivos.append(instalador_zip)
    resultado = rodar([GH, "release", "create", versao] + arquivos +
                       ["--repo", "guitador123/caminho-da-maestria",
                        "--title", f"Caminho da Maestria {VERSAO}",
                        "--notes", notas])
    print(resultado.stdout.strip() or resultado.stderr.strip()[-600:])
    if resultado.returncode != 0:
        raise SystemExit("ERRO ao publicar a release")

    print(f"\n[OK] versao {VERSAO} publicada (release {versao})!")
    print("     os .exe instalados vao se atualizar sozinhos")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Atualizacao automatica.

Toda vez que o programa abre, ele confere no GitHub se tem commit novo
e, se tiver, atualiza sozinho e abre de novo.

Duas situacoes (o app se adapta):

1. **Instalado do repositorio** (tem a pasta `.git` ao lado): ele roda
   `git pull` e atualiza as dependencias. Como o codigo ja esta carregado
   na memoria, so precisa reiniciar.

2. **Instalado do .exe / instalador** (sem `.git`): ele baixa a ultima
   Release do GitHub, troca os arquivos e abre de novo. Como o .exe esta
   rodando (o Windows nao deixa trocar um arquivo em uso), a troca e feita
   por um script auxiliar depois que o app fecha.

Nada aqui trava o programa: se a internet cair, o GitHub estiver fora do
ar ou der qualquer erro, o app abre normalmente.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import zipfile

REPOSITORIO = "guitador123/caminho-da-maestria"
BRANCH = "main"
API = f"https://api.github.com/repos/{REPOSITORIO}"
SITE = f"https://github.com/{REPOSITORIO}"
# os feeds Atom do GitHub NAO tem limite de requisicoes (a API tem 60/hora
# por IP, o que acabaria com varios PCs da guilda ao mesmo tempo)
FEED_COMMITS = f"{SITE}/commits/{BRANCH}.atom"
FEED_RELEASES = f"{SITE}/releases.atom"
# o nome do arquivo da release (sem espaco: o GitHub troca por ponto)
NOME_ASSET = "Caminho-da-Maestria.zip"
URL_DOWNLOAD = f"{SITE}/releases/latest/download/{NOME_ASSET}"
ARQUIVO_VERSAO = os.path.join("assets", "versao.txt")
TIMEOUT = 5           # segundos de espera pela rede (o app nao pode
                      # ficar segurado na tela de atualizacao)


# ------------------------------------------------------------- ferramentas
LOG = os.path.join(os.environ.get("LOCALAPPDATA",
                                    os.path.expanduser("~")),
                     "Caminho da Maestria", "log_atualizacao.log")


def _registrar(texto):
    """Deixa um registro do que a atualizacao fez (para depurar)."""
    try:
        from datetime import datetime
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write(f"{datetime.now():%d/%m %H:%M:%S} | {texto}\n")
    except Exception:
        pass


def _app_dir():
    """A pasta do programa (no .exe, a pasta do executavel)."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _caminho_versao():
    """O arquivo com o commit em que esta versao foi montada."""
    candidatos = []
    if getattr(sys, "frozen", False):
        # no .exe, a pasta _internal fica IRMA do executavel
        candidatos.append(os.path.join(os.path.dirname(sys.executable),
                                       "_internal", ARQUIVO_VERSAO))
    candidatos.append(os.path.join(_app_dir(), "_internal", ARQUIVO_VERSAO))
    candidatos.append(os.path.join(_app_dir(), ARQUIVO_VERSAO))
    for caminho in candidatos:
        if os.path.exists(caminho):
            return caminho
    return candidatos[-1]


def versao_local():
    """O commit com que esta versao foi montada.

    - rodando de um clone do git: e o HEAD local (exatamente o que esta
      rodando);
    - rodando do .exe: e o commit gravado em `assets/versao.txt` na hora
      do build.
    """
    if tem_git():
        try:
            return _git("rev-parse", "HEAD").stdout.strip()[:40]
        except Exception:
            return ""
    try:
        with open(_caminho_versao(), "r", encoding="utf-8") as arquivo:
            return arquivo.read().strip().splitlines()[0].strip()[:40]
    except Exception:
        return ""


def _pedir(url, destino=None):
    """GET na API do GitHub (ou baixa o arquivo)."""
    requisicao = urllib.request.Request(
        url, headers={"User-Agent": "Caminho-da-Maestria",
                      "Accept": "application/vnd.github+json"})
    if destino:
        with urllib.request.urlopen(requisicao, timeout=TIMEOUT) as resposta:
            with open(destino, "wb") as arquivo:
                shutil.copyfileobj(resposta, arquivo)
        return True
    with urllib.request.urlopen(requisicao, timeout=TIMEOUT) as resposta:
        return json.loads(resposta.read().decode("utf-8"))


def _atom(url):
    """Baixa um feed Atom do GitHub (sem limite de requisicoes)."""
    requisicao = urllib.request.Request(
        url, headers={"User-Agent": "Caminho-da-Maestria"})
    with urllib.request.urlopen(requisicao, timeout=TIMEOUT) as resposta:
        return resposta.read().decode("utf-8", errors="replace")


def commit_remoto():
    """(sha, mensagem) do ultimo commit da branch principal."""
    texto = _atom(FEED_COMMITS)
    sha = ""
    mensagem = ""
    achado = re.search(r"Grit::Commit/([0-9a-f]{40})", texto)
    if achado:
        sha = achado.group(1)
    achado = re.search(r"<entry>.*?<title>(.*?)</title>", texto, re.S)
    if achado:
        mensagem = achado.group(1).strip()
    return sha, mensagem


GIT_PADRAO = [
    r"C:\Program Files\Git\cmd\git.exe",
    r"C:\Program Files (x86)\Git\cmd\git.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""),
                 "Programs", "Git", "cmd", "git.exe"),
]


def caminho_git():
    """O executavel do git (no PATH ou nos caminhos padrao)."""
    achado = shutil.which("git")
    if achado:
        return achado
    for caminho in GIT_PADRAO:
        if caminho and os.path.exists(caminho):
            return caminho
    return "git"


def _git(*argumentos):
    """Roda um comando do git na pasta do programa."""
    return subprocess.run([caminho_git()] + list(argumentos), cwd=_app_dir(),
                          capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=60)


def tem_git():
    """O programa esta rodando de dentro de um clone do git?"""
    return os.path.isdir(os.path.join(_app_dir(), ".git"))


# --------------------------------------------------------------- atualizar
def _atualizar_com_git():
    """git pull + dependencias (o app esta num clone)."""
    pasta = _app_dir()
    resultado = subprocess.run([caminho_git(), "pull", "--ff-only"], cwd=pasta,
                               capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               timeout=180)
    if resultado.returncode != 0:
        return False
    # atualiza as dependencias (se houver um venv)
    python = os.path.join(pasta, ".venv", "Scripts", "python.exe")
    if os.path.exists(python) and os.path.exists(
            os.path.join(pasta, "requirements.txt")):
        subprocess.run([python, "-m", "pip", "install", "-r",
                        "requirements.txt", "--quiet"], cwd=pasta,
                       capture_output=True, timeout=900)
    # quem abre o programa de novo e o auxiliar (o app vai sair).
    # Num clone NAO existe o .exe: abre de novo pelo Python.
    _agendar_troca(pasta, copiar=False, abrir=_comando_python())
    return True


def _comando_python():
    """Linha de comando (cmd) que abre o app pelo Python (modo clone)."""
    pasta = _app_dir()
    python = ""
    for nome in ("pythonw.exe", "python.exe"):
        candidato = os.path.join(pasta, ".venv", "Scripts", nome)
        if os.path.exists(candidato):
            python = candidato
            break
    if not python:
        python = sys.executable
        # prefere o pythonw (sem a janela preta do console)
        pythonw = os.path.join(os.path.dirname(python), "pythonw.exe")
        if os.path.exists(pythonw):
            python = pythonw
    script = os.path.join(pasta, "app_grandchase.py")
    return f'start "" /d "{pasta}" "{python}" "{script}"'


def _sha_da_release(tag):
    """O commit de uma release, pelo nome da tag (v2026.11.17-9008aef)."""
    parte = (tag or "").rsplit("-", 1)[-1].strip()
    if parte and all(c in "0123456789abcdefABCDEF" for c in parte) \
            and 7 <= len(parte) <= 40:
        return parte.lower()
    return ""


def _ultima_release():
    """(url_do_zip, sha_do_commit) da release mais recente."""
    return URL_DOWNLOAD, _versao_da_release()


def _versao_da_release():
    """A versao (sha) da release mais recente, ou "" se nao houver.

    O feed vem em ordem de criacao, entao a gente procura a entrada com a
    data de `updated` mais nova (e a mesma que o GitHub chama de "latest").
    """
    try:
        texto = _atom(FEED_RELEASES)
    except Exception:
        return ""
    melhor = ("", "")
    for entrada in re.findall(r"<entry>(.*?)</entry>", texto, re.S):
        tag = re.search(r"/v[0-9]{4}\.[0-9]{2}\.[0-9]{2}-([0-9a-f]{7,40})",
                        entrada)
        quando = re.search(r"<updated>(.*?)</updated>", entrada)
        if not tag or not quando:
            continue
        if quando.group(1) > melhor[1]:
            melhor = (tag.group(1).lower(), quando.group(1))
    return melhor[0]


def _assinatura_confere(url_zip, zip_arquivo, temporario):
    """Baixa o `<zip>.sig` e confere (Ed25519). False = NAO instalar."""
    sig_arquivo = os.path.join(temporario, "programa.zip.sig")
    try:
        _pedir(url_zip + ".sig", sig_arquivo)
        with open(sig_arquivo, "r", encoding="ascii",
                  errors="replace") as arquivo:
            conteudo = arquivo.read(4096)
    except Exception as erro:
        _registrar(f"RECUSADA: release sem assinatura ({erro!r})")
        return False
    try:
        import assinatura
        if assinatura.verificar(zip_arquivo, conteudo):
            _registrar("assinatura da release: OK")
            return True
    except Exception as erro:
        _registrar(f"RECUSADA: erro ao conferir a assinatura ({erro!r})")
        return False
    _registrar("RECUSADA: a assinatura da release NAO confere "
               "(arquivo adulterado ou chave errada)")
    return False


def _atualizar_com_release():
    """Baixa a ultima Release e troca os arquivos (depois de fechar)."""
    url, _sha = _ultima_release()
    if not url:
        return False
    temporario = tempfile.mkdtemp(prefix="cm_atualizacao_")
    try:
        zip_arquivo = os.path.join(temporario, "programa.zip")
        _pedir(url, zip_arquivo)
        # SO instala se a assinatura bater com a chave publica embutida
        # (assim uma release falsa, mesmo no GitHub certo, e recusada)
        if not _assinatura_confere(url, zip_arquivo, temporario):
            shutil.rmtree(temporario, ignore_errors=True)
            return False
        destino = os.path.join(temporario, "programa")
        with zipfile.ZipFile(zip_arquivo) as pacote:
            pacote.extractall(destino)
        # o zip (~200 MB) ja foi extraido: nao precisa ficar no Temp
        for arquivo in (zip_arquivo, zip_arquivo + ".sig"):
            try:
                os.remove(arquivo)
            except OSError:
                pass
        # a release pode ter uma pasta dentro do zip
        if not os.path.exists(os.path.join(destino, "Caminho da Maestria.exe")):
            for item in os.listdir(destino):
                sub = os.path.join(destino, item)
                if os.path.isdir(sub) and os.path.exists(
                        os.path.join(sub, "Caminho da Maestria.exe")):
                    destino = sub
                    break
        if not os.path.exists(os.path.join(destino, "Caminho da Maestria.exe")):
            _registrar("o zip da release nao tem o executavel")
            shutil.rmtree(temporario, ignore_errors=True)
            return False
        _registrar(f"release baixada: {url}")
        _agendar_troca(destino, limpar=temporario)
        _registrar("troca agendada; o programa vai abrir de novo")
        # NAO apaga a pasta temporaria agora: o auxiliar precisa dela
        # para copiar os arquivos (e ele apaga a pasta INTEIRA no final)
        return True
    except Exception as erro:
        _registrar(f"ERRO ao baixar a release: {erro!r}")
        shutil.rmtree(temporario, ignore_errors=True)
        return False


def _agendar_troca(novos, copiar=True, abrir=None, limpar=None):
    """Cria o script que troca os arquivos e abre o programa de novo.

    O Windows nao deixa trocar um arquivo que esta em uso, entao a troca
    so pode acontecer DEPOIS que o programa atual fecha. Por isso quem
    abre de novo e este script (e nao o app).

    `abrir` e a linha (cmd) que abre o programa; o padrao e o .exe. Mesmo
    se a troca falhar, o programa (a versao antiga) e aberto de novo.
    `limpar` e a pasta temporaria a apagar no final (padrao: `novos`).
    """
    destino = _app_dir()
    auxiliar = os.path.join(tempfile.gettempdir(), "cm_trocar_arquivos.cmd")
    exe = os.path.join(destino, "Caminho da Maestria.exe")
    if abrir is None:
        abrir = f'start "" "{exe}"'
    if copiar:
        copia = (f'robocopy "{novos}" "{destino}" /MIR /XF login_prefs.json '
                 "/NFL /NDL /NJH /NJS /NP >nul\r\n"
                 "if errorlevel 8 (\r\n"
                 "    set /a tentativas+=1\r\n"
                 "    if !tentativas! GEQ 5 goto :falhou\r\n"
                 "    ping 127.0.0.1 -n 3 >nul\r\n"
                 "    goto :copia\r\n"
                 ")\r\n")
        limpeza = f'rmdir /s /q "{limpar or novos}" >nul 2>&1\r\n'
    else:
        copia = ""
        limpeza = ""
    # newline="": as linhas ja tem \r\n (senao viraria \r\r\n)
    with open(auxiliar, "w", encoding="utf-8", newline="") as arquivo:
        arquivo.write(
            "@echo off\r\n"
            "setlocal enabledelayedexpansion\r\n"
            "set /a tentativas=0\r\n"
            "rem espera o programa atual fechar, troca os arquivos e abre\r\n"
            "ping 127.0.0.1 -n 5 >nul\r\n"
            ":copia\r\n"
            + copia
            + abrir + "\r\n"
            + limpeza +
            f'del /q "{auxiliar}" >nul 2>&1\r\n'
            "exit /b 0\r\n"
            ":falhou\r\n"
            "rem a troca falhou: abre a versao que ja estava instalada\r\n"
            + abrir + "\r\n"
            + limpeza +
            f'del /q "{auxiliar}" >nul 2>&1\r\n')
    subprocess.Popen(["cmd", "/c", auxiliar], creationflags=0x08000000)


def aplicar_atualizacao():
    """Aplica a atualizacao. Devolve True se deu certo."""
    if tem_git():
        return _atualizar_com_git()
    return _atualizar_com_release()


def reiniciar():
    """Abre o programa de novo e fecha este."""
    if getattr(sys, "frozen", False):
        comando = [sys.executable]
    else:
        comando = [sys.executable,
                   os.path.join(_app_dir(), "app_grandchase.py")]
    try:
        subprocess.Popen(comando, cwd=_app_dir(),
                         creationflags=0x08000000 if os.name == "nt" else 0)
    except Exception:
        pass
    os._exit(0)


# ------------------------------------------------------------------ splash
def _splash(texto):
    """Uma janelinha mostrando o que esta acontecendo (some depois)."""
    try:
        import tkinter as tk
        janela = tk.Tk()
        janela.title("Caminho da Maestria")
        janela.configure(bg="#16112b")
        janela.resizable(False, False)
        tk.Label(janela, text=texto, bg="#16112b", fg="#f2f0fa",
                 font=("Segoe UI", 11)).pack(padx=26, pady=18)
        janela.update()
        janela.attributes("-topmost", True)
        return janela
    except Exception:
        return None


def limpar_sobras(idade_minima=3600):
    """Apaga pastas `cm_atualizacao_*` antigas do Temp (~200 MB cada).

    Versoes antigas do auxiliar apagavam so a pasta extraida e deixavam o
    zip para tras. So mexe nas pastas com mais de `idade_minima` segundos
    (uma atualizacao em andamento nunca e tocada). Devolve quantas apagou.
    """
    apagadas = 0
    agora = time.time()
    try:
        temp = tempfile.gettempdir()
        for nome in os.listdir(temp):
            if not nome.startswith("cm_atualizacao_"):
                continue
            caminho = os.path.join(temp, nome)
            try:
                if not os.path.isdir(caminho) or os.path.islink(caminho):
                    continue
                if agora - os.path.getmtime(caminho) < idade_minima:
                    continue
                shutil.rmtree(caminho, ignore_errors=True)
                if not os.path.exists(caminho):
                    apagadas += 1
            except OSError:
                pass
    except OSError:
        pass
    if apagadas:
        _registrar(f"limpeza: {apagadas} pasta(s) antiga(s) de atualizacao "
                   "apagada(s) do Temp")
    return apagadas


def verificar_e_atualizar(mostrar=True):
    """Confere o GitHub e atualiza se precisar. Devolve True se atualizou."""
    limpar_sobras()
    splash = _splash("Verificando atualizacoes...") if mostrar else None

    def fechar_splash():
        if splash is not None:
            try:
                splash.destroy()
            except Exception:
                pass

    try:
        sha_local = versao_local()
        if tem_git():
            # num clone: compara com o commit do GitHub
            sha_remoto, mensagem = commit_remoto()
            if not sha_remoto:
                fechar_splash()
                return False
            if sha_local and sha_local[:40] == sha_remoto[:40]:
                fechar_splash()
                return False   # ja esta na ultima
        else:
            # no .exe: compara com a ULTIMA RELEASE (assim o app nao fica
            # tentando atualizar sem ter release nova)
            sha_release = _versao_da_release()
            if not sha_release:
                _registrar("nao ha release nova (ou sem rede)")
                fechar_splash()
                return False
            if sha_local and sha_local.lower().startswith(sha_release):
                fechar_splash()
                return False   # ja esta na ultima release
            mensagem = "versao nova disponivel"
    except Exception:
        fechar_splash()
        return False      # sem internet/GitHub: segue normal

    # tem coisa nova: avisa na MESMA janelinha (ela continua aberta) e
    # atualiza
    if splash is not None:
        try:
            splash.children[next(iter(splash.children))].configure(
                text=f"Nova versao disponivel!\n{mensagem}\nAtualizando...")
            splash.update()
        except Exception:
            pass

    try:
        deu_certo = aplicar_atualizacao()
    except Exception:
        deu_certo = False

    fechar_splash()
    if deu_certo:
        _registrar("atualizacao aplicada; o programa vai abrir de novo")
        # o app sai agora: quem abre de novo e o auxiliar (que ja foi
        # criado). Se o app abrisse agora, os arquivos ficariam em uso e
        # a troca nao aconteceria.
        os._exit(0)
    return deu_certo


def checar_em_segundo_plano(callback):
    """Roda a verificacao numa thread (para nao travar a abertura)."""
    def alvo():
        try:
            verificar_e_atualizar(mostrar=False)
        except Exception:
            pass
        try:
            callback()
        except Exception:
            pass

    thread = threading.Thread(target=alvo, daemon=True)
    thread.start()
    return thread

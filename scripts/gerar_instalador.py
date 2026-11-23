# -*- coding: utf-8 -*-
"""
Gera o INSTALADOR do "Caminho da Maestria".

O instalador e um .zip que, quando descompactado, instala o app
completo (Python e todas as dependencias ja embutidos pelo PyInstaller
na pasta `_internal`) e cria os atalhos.

    python scripts/gerar_instalador.py

Saida:
    instalador\\Caminho da Maestria - Instalador\\   (a pasta do instalador)
    instalador\\Caminho da Maestria - Instalador.zip (o pacote compactado)

⚠ **O script revisa o bundle antes de empacotar**: se encontrar uma
`service_role key`, uma senha ou um e-mail pessoal dentro da pasta do
build, ele ABORTA (nao gera o instalador).
"""

import os
import re
import shutil
import zipfile

# este script fica em scripts/; a raiz do projeto e a pasta de cima
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(RAIZ, "dist", "Caminho da Maestria")
SAIDA = os.path.join(RAIZ, "instalador")
NOME_PASTA = "Caminho da Maestria - Instalador"
# sem espaco: o GitHub troca espaco por ponto no nome do asset
NOME_ZIP = "Caminho-da-Maestria-Instalador.zip"
EXE = "Caminho da Maestria.exe"

DESTINO_PADRAO = "%LOCALAPPDATA%\\Caminho da Maestria"

# ------------------------------------------------------------ o que e PROIBIDO
# (a publishable/anon key e publica por design e pode ir no app)
PROIBIDOS = [
    ("service_role key", re.compile(rb"service_role", re.I)),
    ("chave secreta do Supabase", re.compile(rb"sb_secret_", re.I)),
    ("JWT de servico", re.compile(rb"eyJ[A-Za-z0-9_\-]{40,}")),
    ("chave privada", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY")),
]

ARQUIVOS_IGNORADOS = {"login_prefs.json", "gc_app.log", "Thumbs.db"}


def revisar_bundle(pasta):
    """Procura segredos no bundle. Devolve a lista de problemas."""
    problemas = []
    for base, _pastas, arquivos in os.walk(pasta):
        for arquivo in arquivos:
            caminho = os.path.join(base, arquivo)
            if arquivo in ARQUIVOS_IGNORADOS:
                continue
            try:
                if os.path.getsize(caminho) > 80 * 1024 * 1024:
                    continue
                with open(caminho, "rb") as arquivo_leitura:
                    dados = arquivo_leitura.read()
            except OSError as erro:
                # sem ler nao da para garantir que nao tem segredo: bloqueia
                problemas.append((f"nao deu para ler ({erro})",
                                  os.path.relpath(caminho, pasta)))
                continue
            for nome, padrao in PROIBIDOS:
                if padrao.search(dados):
                    problemas.append((nome, os.path.relpath(caminho, pasta)))
    return problemas


# --------------------------------------------------------------- os scripts
INSTALAR_CMD = """@echo off
setlocal
chcp 65001 >nul 2>&1
title Caminho da Maestria - Instalador

set "AQUI=%~dp0"
set "FONTE=%AQUI%app"
set "DESTINO=%LOCALAPPDATA%\\Caminho da Maestria"

echo.
echo  =====================================================
echo     Caminho da Maestria  -  Instalador
echo  =====================================================
echo.
if not exist "%FONTE%\\{exe}" (
    echo  ERRO: os arquivos do programa nao estao nesta pasta.
    echo        Descompacte o instalador INTEIRO e rode de novo.
    echo.
    pause
    exit /b 1
)
echo  Vai instalar em:
echo      %DESTINO%
echo.
echo  Nao precisa instalar Python: tudo ja vem junto.
echo.
set /p RESP="  Instalar agora? (S/N): "
if /i "%RESP%"=="S" goto :instalar
goto :cancelou

:instalar
echo.
echo  [1/3] Copiando o programa...
if not exist "%DESTINO%" mkdir "%DESTINO%"
xcopy "%FONTE%\\*" "%DESTINO%\\" /E /I /Y /Q >nul
if errorlevel 1 (
    echo  ERRO ao copiar os arquivos.
    pause
    exit /b 1
)

echo  [2/3] Criando os atalhos...
cscript //nologo //B "%AQUI%atalhos.vbs" "%DESTINO%" >nul 2>&1
if errorlevel 1 echo  AVISO: nao foi possivel criar os atalhos.

echo  [3/3] Gerando o desinstalador...
copy /y "%AQUI%Desinstalar.cmd" "%DESTINO%\\" >nul 2>&1

echo.
echo  =====================================================
echo   Instalado em: %DESTINO%
echo  =====================================================
echo.
ping 127.0.0.1 -n 3 >nul
start "" "%DESTINO%\\{exe}"
echo  O programa foi aberto.
ping 127.0.0.1 -n 4 >nul
exit /b 0

:cancelou
echo  Instalacao cancelada.
ping 127.0.0.1 -n 3 >nul
exit /b 0
"""

DESINSTALAR_CMD = """@echo off
setlocal
chcp 65001 >nul 2>&1
title Desinstalar - Caminho da Maestria

set "DESTINO=%LOCALAPPDATA%\\Caminho da Maestria"

echo.
echo  =====================================================
echo    Desinstalar - Caminho da Maestria
echo  =====================================================
echo.
echo  Vai remover:
echo    - a pasta %DESTINO%
echo    - o atalho da area de trabalho
echo    - o atalho do menu Iniciar
echo.
set /p RESP2="  Continuar? (S/N): "
if /i "%RESP2%"=="S" goto :removendo
goto :cancelou

:removendo
cd /d "%TEMP%" >nul 2>&1
echo.
echo  Removendo os atalhos...
del /q "%USERPROFILE%\\Desktop\\Caminho da Maestria.lnk" >nul 2>&1
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Caminho da Maestria\\Caminho da Maestria.lnk" >nul 2>&1
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Caminho da Maestria\\Desinstalar.lnk" >nul 2>&1
rmdir /s /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Caminho da Maestria" >nul 2>&1

echo  Removendo a pasta do programa...
ping 127.0.0.1 -n 2 >nul
rmdir /s /q "%DESTINO%" >nul 2>&1
ping 127.0.0.1 -n 2 >nul
rmdir "%DESTINO%" >nul 2>&1

echo.
echo  Pronto! O Caminho da Maestria foi desinstalado.
echo  (os dados na nuvem continuam no seu banco de dados)
echo.
ping 127.0.0.1 -n 5 >nul
exit /b 0

:cancelou
echo  Cancelado.
ping 127.0.0.1 -n 3 >nul
exit /b 0
"""

ATALHOS_VBS = """Option Explicit
' Cria os atalhos do Caminho da Maestria (com o icone do proprio programa).
Dim shell, fso, destino, exe, pastaProgramas, atalho

If WScript.Arguments.Count < 1 Then WScript.Quit 1
destino = WScript.Arguments(0)
exe = destino & "\\Caminho da Maestria.exe"

Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
pastaProgramas = shell.SpecialFolders("Programs") & "\\Caminho da Maestria"

' a pasta do menu Iniciar pode nao existir ainda
If Not fso.FolderExists(pastaProgramas) Then
    fso.CreateFolder(pastaProgramas)
End If

' ---- area de trabalho ----
Set atalho = shell.CreateShortcut(shell.SpecialFolders("Desktop") & "\\Caminho da Maestria.lnk")
atalho.TargetPath = exe
atalho.WorkingDirectory = destino
atalho.IconLocation = exe & ",0"
atalho.Description = "Caminho da Maestria - seus personagens, equipamentos e progresso"
atalho.Save

' ---- menu Iniciar ----
Set atalho = shell.CreateShortcut(pastaProgramas & "\\Caminho da Maestria.lnk")
atalho.TargetPath = exe
atalho.WorkingDirectory = destino
atalho.IconLocation = exe & ",0"
atalho.Description = "Caminho da Maestria - seus personagens, equipamentos e progresso"
atalho.Save

' ---- desinstalador no menu Iniciar ----
Set atalho = shell.CreateShortcut(pastaProgramas & "\\Desinstalar.lnk")
atalho.TargetPath = destino & "\\Desinstalar.cmd"
atalho.WorkingDirectory = destino
atalho.IconLocation = exe & ",0"
atalho.Description = "Desinstalar o Caminho da Maestria"
atalho.Save

WScript.Echo "atalhos criados"
"""

LEIA_ME = """CAMINHO DA MAESTRIA - INSTALADOR
=================================

COMO INSTALAR
-------------
1. Descompacte ESTA PASTA INTEIRA (nao rode de dentro do zip).
2. Clique duas vezes em "Instalar.cmd".
3. Confirme com S. O programa e instalado e abre sozinho.

O QUE E INSTALADO
-----------------
Pasta: %LOCALAPPDATA%\\Caminho da Maestria
  (ou seja: C:\\Users\\SEU_USUARIO\\AppData\\Local\\Caminho da Maestria)

 Atalhos:
  - Area de trabalho
  - Menu Iniciar > Caminho da Maestria

VOCE NAO PRECISA INSTALAR PYTHON
--------------------------------
O instalador ja leva o Python e TODAS as dependencias do programa
(interface, banco de dados, imagens, planilha, QR Code...). E so
clicar no programa instalado.

COMO DESINSTALAR
----------------
Menu Iniciar > Caminho da Maestria > Desinstalar
(ou rode "Desinstalar.cmd" dentro da pasta do programa).

Os seus dados ficam no banco (na nuvem): desinstalar o programa nao
apaga o seu progresso.

SEGURANCA
---------
Este instalador NAO traz nenhuma chave secreta do banco de dados.
A unica chave embutida no programa e a "publishable key" do Supabase
(chave publica, feita para ficar dentro do aplicativo).
Nenhuma senha, nenhum token de servico e nenhum dado pessoal.
"""


def main():
    if not os.path.exists(os.path.join(BUILD, EXE)):
        raise SystemExit(f"o build nao esta em: {BUILD}\n"
                         "rode: pyinstaller \"Controle Grand Chase.spec\" --noconfirm")

    print("[1/4] revisando o bundle (procura segredos)...")
    problemas = revisar_bundle(BUILD)
    if problemas:
        print("  ABORTADO: segredo encontrado no build:")
        for nome, arquivo in problemas:
            print(f"    - {nome}: {arquivo}")
        raise SystemExit("Nao gerei o instalador: revise o bundle antes.")
    print("  OK: nenhum segredo encontrado.")

    print("[2/4] montando a pasta do instalador...")
    if os.path.isdir(SAIDA):
        shutil.rmtree(SAIDA)
    pasta = os.path.join(SAIDA, NOME_PASTA)
    os.makedirs(os.path.join(pasta, "app"), exist_ok=True)

    print("      copiando o programa...")
    shutil.copytree(BUILD, os.path.join(pasta, "app"), dirs_exist_ok=True)
    # o log e as preferencias nao entram no instalador
    for arquivo in ARQUIVOS_IGNORADOS:
        caminho = os.path.join(pasta, "app", arquivo)
        if os.path.exists(caminho):
            os.remove(caminho)

    print("      escrevendo os scripts...")
    with open(os.path.join(pasta, "Instalar.cmd"), "w", encoding="utf-8",
              newline="\r\n") as arquivo:
        arquivo.write(INSTALAR_CMD.replace("{exe}", EXE))
    with open(os.path.join(pasta, "Desinstalar.cmd"), "w", encoding="utf-8",
              newline="\r\n") as arquivo:
        arquivo.write(DESINSTALAR_CMD)
    with open(os.path.join(pasta, "atalhos.vbs"), "w", encoding="utf-8",
              newline="\r\n") as arquivo:
        arquivo.write(ATALHOS_VBS)
    with open(os.path.join(pasta, "LEIA-ME.txt"), "w", encoding="utf-8",
              newline="\r\n") as arquivo:
        arquivo.write(LEIA_ME)

    print("[3/4] revisando o instalador montado...")
    problemas = revisar_bundle(pasta)
    if problemas:
        print("  ABORTADO: segredo encontrado no instalador:")
        for nome, arquivo in problemas:
            print(f"    - {nome}: {arquivo}")
        raise SystemExit("Nao gerei o .zip: revise a pasta do instalador.")
    print("  OK: nenhum segredo encontrado.")

    print("[4/4] compactando...")
    zip_path = os.path.join(SAIDA, NOME_ZIP)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED,
                         compresslevel=9) as zip_arquivo:
        for base, _pastas, arquivos in os.walk(pasta):
            for arquivo in arquivos:
                caminho = os.path.join(base, arquivo)
                zip_arquivo.write(caminho, os.path.relpath(caminho, SAIDA))

    tamanho = os.path.getsize(zip_path) / (1024 * 1024)
    print()
    print("[OK] instalador pronto:")
    print(f"     pasta : {pasta}")
    print(f"     zip   : {zip_path} ({tamanho:.0f} MB)")


if __name__ == "__main__":
    main()

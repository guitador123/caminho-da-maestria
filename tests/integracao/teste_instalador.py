"""
Teste do INSTALADOR (pendencia #8).

Faz o ciclo completo: extrai o .zip, instala, confere os atalhos, abre o
programa instalado e desinstala.

    python teste_instalador.py
"""

"""Teste final do instalador: instala, confere e desinstala."""
import _raiz  # noqa: F401  (coloca src/ no sys.path)
import io
import os
import shutil
import subprocess
import sys
import zipfile
import time

ZIP = (r"C:\Users\guilh\Downloads\Controle GrandChase\instalador"
       r"\Caminho da Maestria - Instalador.zip")
TESTE = r"C:\Users\guilh\AppData\Local\Temp\opencode\teste_instalador"
DESTINO = os.path.join(os.environ["LOCALAPPDATA"], "Caminho da Maestria")
ATALHO_DESKTOP = os.path.join(os.environ["USERPROFILE"], "Desktop",
                              "Caminho da Maestria.lnk")
ATALHOS = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows",
                       "Start Menu", "Programs", "Caminho da Maestria")

erros = []


def rodar(comando, pasta, entrada=b"S\n", log=None):
    alvo = open(log, "wb") if log else subprocess.DEVNULL
    try:
        subprocess.run(comando, cwd=pasta, input=entrada, stdout=alvo,
                       stderr=subprocess.STDOUT, timeout=1800)
    finally:
        if log:
            alvo.close()


print("1) limpando rastros de testes anteriores")
shutil.rmtree(TESTE, ignore_errors=True)
shutil.rmtree(DESTINO, ignore_errors=True)
shutil.rmtree(ATALHOS, ignore_errors=True)
for caminho in (ATALHO_DESKTOP,
                os.path.join(ATALHOS, "Caminho da Maestria.lnk"),
                os.path.join(ATALHOS, "Desinstalar.lnk")):
    if os.path.exists(caminho):
        os.remove(caminho)

print("2) extraindo o zip")
os.makedirs(TESTE, exist_ok=True)
with zipfile.ZipFile(ZIP) as pacote:
    pacote.extractall(TESTE)
pasta = os.path.join(TESTE, "Caminho da Maestria - Instalador")

print("3) instalando")
rodar(["cmd", "/c", "Instalar.cmd"], pasta,
      log=os.path.join(TESTE, "instalar.log"))

print("4) conferindo")
for descricao, condicao in [
        ("executavel instalado",
         os.path.exists(os.path.join(DESTINO, "Caminho da Maestria.exe"))),
        ("dependencias (_internal)",
         os.path.exists(os.path.join(DESTINO, "_internal"))),
        ("desinstalador copiado",
         os.path.exists(os.path.join(DESTINO, "Desinstalar.cmd"))),
        ("atalho da area de trabalho", os.path.exists(ATALHO_DESKTOP)),
        ("atalho do menu iniciar",
         os.path.exists(os.path.join(ATALHOS, "Caminho da Maestria.lnk"))),
        ("atalho do desinstalador",
         os.path.exists(os.path.join(ATALHOS, "Desinstalar.lnk"))),
]:
    print(f"   {'OK ' if condicao else '!! '}{descricao}")
    if not condicao:
        erros.append(descricao)

print("5) abrindo o programa instalado")
processo = subprocess.Popen([os.path.join(DESTINO, "Caminho da Maestria.exe")])
time.sleep(12)
abriu = processo.poll() is None
print(f"   {'OK ' if abriu else '!! '}abriu (janela de login)")
if not abriu:
    erros.append("o programa nao abriu")
else:
    subprocess.run(["taskkill", "/IM", "Caminho da Maestria.exe", "/F"],
                   capture_output=True)
time.sleep(2)

print("6) desinstalando")
rodar(["cmd", "/c", "Desinstalar.cmd"], DESTINO,
      log=os.path.join(TESTE, "desinstalar.log"))
for descricao, condicao in [
        ("pasta do programa removida", not os.path.exists(DESTINO)),
        ("atalho da area de trabalho removido", not os.path.exists(ATALHO_DESKTOP)),
        ("atalhos do menu iniciar removidos",
         not os.path.exists(os.path.join(ATALHOS, "Caminho da Maestria.lnk"))),
]:
    print(f"   {'OK ' if condicao else '!! '}{descricao}")
    if not condicao:
        erros.append(descricao)

if erros:
    print("\nFALHOU:")
    for erro in erros:
        print("   -", erro)
    sys.exit(1)

print("\nINSTALADOR OK (instalar + abrir + desinstalar)")

# -*- coding: utf-8 -*-
"""
Zera as missoes semanais de TODAS as contas do Supabase.

Roda as Quartas-Feiras as 03h (horario de Brasilia) pelo Agendador de
Tarefas do Windows. Faz exatamente o que o botao "Zerar dungeons
semanais" do app faz, mas para todas as contas de uma vez.

O que ele grava: as 7 colunas booleanas da tabela `user_semanais`
(fornalha_infernal, altar_da_runha, torre_das_ilusoes_semanal, void_123,
void_4, caminho_abissal, terra_do_julgamento) voltam para False.

⚠ **A CHAVE SERVICE_ROLE**
Para mexer nas linhas de todos os usuarios o script precisa da
**service_role key** (a anon/publishable nao passa nas politicas de
seguranca do banco). A chave **NAO** fica no codigo nem no instalador:
o script procura ela em:

  1. a variavel de ambiente  SUPABASE_SERVICE_ROLE_KEY
  2. o arquivo  %LOCALAPPDATA%\\Caminho da Maestria\\service_role.txt
  3. o arquivo  service_role.txt ao lado deste script

Para pegar a chave: painel do Supabase > Settings > API > Service Role
(e o arquivo deve ter a chave SOZINHA, sem aspas).

Uso:
    python scripts/zerar_semanais_semanal.py            # zera de verdade
    python scripts/zerar_semanais_semanal.py --testar    # so mostra o que seria
    python scripts/zerar_semanais_semanal.py --colunas   # lista as colunas do banco
"""

import datetime
import io
import os
import sys
import time

SUPABASE_URL = "https://rtpwvfrdhrvtulvvctze.supabase.co"
TABELA = "user_semanais"

# as 7 missoes semanais (o banco pode nao ter todas)
COLUNAS = [
    "fornalha_infernal",
    "altar_da_runha",
    "torre_das_ilusoes_semanal",
    "void_123",
    "void_4",
    "caminho_abissal",
    "terra_do_julgamento",
]

LOG = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                   "Caminho da Maestria", "log_zerar_semanais.log")


# --------------------------------------------------------------- utilidades
def registrar(texto, imprime=True):
    """Escreve no log (com data) e mostra na tela."""
    linha = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} | {texto}"
    if imprime:
        print(linha, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with io.open(LOG, "a", encoding="utf-8") as arquivo:
            arquivo.write(linha + "\n")
    except OSError as erro:
        print(f"(nao deu para gravar o log: {erro})", flush=True)


def chave_service_role():
    """A service_role key (de ambiente, do LocalAppData ou de lado)."""
    # 1) variavel de ambiente
    chave = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if chave:
        return chave
    # 2) arquivo no LocalAppData (fora do projeto e do instalador)
    pasta = os.path.join(os.environ.get("LOCALAPPDATA",
                                        os.path.expanduser("~")),
                         "Caminho da Maestria")
    # 3) arquivo ao lado do script (scripts/) ou na raiz do projeto
    aqui = os.path.dirname(os.path.abspath(__file__))
    for caminho in (os.path.join(pasta, "service_role.txt"),
                    os.path.join(aqui, "service_role.txt"),
                    os.path.join(os.path.dirname(aqui), "service_role.txt")):
        if os.path.exists(caminho):
            try:
                with io.open(caminho, "r", encoding="utf-8") as arquivo:
                    texto = arquivo.read().strip()
                if texto:
                    return texto
            except OSError as erro:
                registrar(f"ERRO ao ler {caminho}: {erro}")
                continue
    return ""


def cliente(chave):
    from supabase import create_client
    return create_client(SUPABASE_URL, chave)


def colunas_do_banco(sb):
    """As colunas de missoes que existem de fato na tabela."""
    try:
        resposta = sb.table(TABELA).select("*").limit(1).execute()
    except Exception as erro:
        registrar(f"ERRO ao ler a tabela: {erro}")
        return []
    if not resposta.data:
        # tabela vazia: descobre pelas colunas de uma linha de qualquer conta
        try:
            resposta = sb.table(TABELA).select("*").limit(1).execute()
        except Exception as erro:
            registrar(f"ERRO ao reler a tabela: {erro}")
            return []
        if not resposta.data:
            registrar("AVISO: nao ha linhas para inspecionar; "
                      "usando a lista padrao")
            return list(COLUNAS)
    existentes = set(resposta.data[0].keys())
    achadas = [coluna for coluna in COLUNAS if coluna in existentes]
    if not achadas:
        registrar("AVISO: nenhuma coluna de missao encontrada na tabela")
    return achadas


# ------------------------------------------------------------------- acoes
def main():
    agora = datetime.datetime.now()
    print("=" * 64)
    print("  ZERAR MISSOES SEMANAIS - todas as contas")
    print("=" * 64)
    print(f"  agora: {agora:%A %d/%m/%Y %H:%M:%S}")
    print()

    registrar(f"--- execucao iniciada ({agora:%d/%m/%Y %H:%M}) ---")

    if "--colunas" in sys.argv:
        chave = chave_service_role()
        if not chave:
            registrar("ERRO: service_role key nao encontrada")
            return 1
        sb = cliente(chave)
        for coluna in colunas_do_banco(sb):
            print("   ", coluna)
        return 0

    chave = chave_service_role()
    if not chave:
        registrar("ERRO: a service_role key nao foi encontrada.")
        print()
        print("  Coloque a chave em UM destes lugares:")
        print("   1) variavel de ambiente SUPABASE_SERVICE_ROLE_KEY")
        print("   2) %LOCALAPPDATA%\\Caminho da Maestria\\service_role.txt")
        print("   3) service_role.txt ao lado deste script")
        print()
        print("  (painel do Supabase > Settings > API > Service Role)")
        return 1

    try:
        sb = cliente(chave)
    except Exception as erro:
        registrar(f"ERRO ao conectar no Supabase: {erro}")
        return 1

    colunas = colunas_do_banco(sb)
    if not colunas:
        registrar("ERRO: nenhuma coluna de missao encontrada")
        return 1
    registrar(f"colunas semanais: {', '.join(colunas)}")

    # --- quantas linhas tem marcacao ativa (por coluna) ------------------
    ativos = {}
    for coluna in colunas:
        try:
            resposta = sb.table(TABELA).select("id").eq(coluna, True).execute()
            ativos[coluna] = len(resposta.data or [])
        except Exception as erro:
            registrar(f"AVISO ao contar {coluna}: {erro}")
            ativos[coluna] = 0
    total = sum(ativos.values())
    registrar("marcacoes ativas antes: " +
              ", ".join(f"{c}={n}" for c, n in ativos.items()) +
              f" (total {total})")

    if "--testar" in sys.argv:
        print()
        print("  MODO TESTE: nada foi alterado.")
        return 0

    # --- zera ------------------------------------------------------------
    zeradas = 0
    for coluna in colunas:
        for tentativa in range(3):
            try:
                sb.table(TABELA).update({coluna: False}).eq(coluna, True).execute()
                zeradas += ativos[coluna]
                break
            except Exception as erro:
                if tentativa == 2:
                    registrar(f"ERRO ao zerar {coluna}: {erro}")
                else:
                    time.sleep(2)

    # --- confere ----------------------------------------------------------
    restantes = 0
    sem_conferir = 0
    for coluna in colunas:
        try:
            resposta = sb.table(TABELA).select("id").eq(coluna, True).execute()
            restantes += len(resposta.data or [])
        except Exception as erro:
            # sem conferir nao da para afirmar que zerou
            registrar(f"ERRO ao conferir a coluna {coluna}: {erro}")
            sem_conferir += 1

    registrar(f"marcacoes zeradas: {zeradas} | ainda ativas: {restantes}")
    print()
    if sem_conferir:
        print(f"  ATENCAO: {sem_conferir} coluna(s) nao puderam ser "
              "conferidas (veja o log)")
        return 1
    if restantes == 0:
        registrar("OK - todas as missoes semanais foram zeradas")
        print("  CONCLUIDO: todas as missoes semanais foram zeradas.")
        return 0
    print(f"  ATENCAO: sobraram {restantes} marcacoes ativas (veja o log)")
    return 1


if __name__ == "__main__":
    sys.exit(main())

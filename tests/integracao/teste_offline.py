"""
Modo offline (item 14) na tela de verdade, com a conta de teste.

A copia local vai para uma pasta TEMPORARIA (nao mexe na do usuario).
Valida:
  1. online: abrir a conta grava a copia neste PC (sem pendencia)
  2. abrir offline (sem sessao): a tela vem da copia, igual
  3. editar offline: fica pendente no PC, o banco NAO muda, e sair nao
     pergunta "alteracoes nao salvas"
  4. a internet volta: reabre a sessao com o token guardado e envia
  5. pendencia de uma sessao offline anterior vai antes da carga normal
  6. a internet cai no meio do uso: o salvamento vira pendencia no PC e
     sobe quando reconecta
O Ataque Total do personagem de teste volta ao valor original no final.

    python tests/integracao/teste_offline.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import tempfile
import time
from types import SimpleNamespace

import httpx

import app_salvamento
import auth
import cache_local
import supabase_db as db
from app_grandchase import GrandChaseApp
from config_app import ABA_GERAL
from credenciais_teste import conta_teste
from opcoes import coluna_banco

cache_local.PASTA = tempfile.mkdtemp(prefix="offline_teste_")


def esperar(app, condicao=lambda: False, segundos=3.0):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        if condicao():
            return True
        time.sleep(0.05)
    return condicao()


def coluna_poder(df):
    return next(c for c in df.columns if coluna_banco(c) == "poder")


def editar_poder(app, nome, valor):
    df = app.dfs[ABA_GERAL]
    df.loc[df["Nome"] == nome, coluna_poder(df)] = valor
    app._marcar_modificado()
    app.salvar_supabase()


def poder_na_copia(uid, nome, chave="dados"):
    linhas = cache_local.ler_copia(uid)[chave][ABA_GERAL]
    linha = next(l for l in linhas if l["Nome"] == nome)
    return int(float(next(v for c, v in linha.items()
                          if coluna_banco(c) == "poder")))


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    uid = user.id
    falhas = []

    def poder_no_banco():
        linha = (sb.table("user_characters").select("poder")
                 .eq("id", char_id).limit(1).execute()).data[0]
        return int(linha["poder"] or 0)

    print("1) online: grava a copia")
    app = GrandChaseApp(user=user, supabase=sb)
    esperar(app, segundos=2)
    copia = cache_local.ler_copia(uid)
    df = app.dfs[ABA_GERAL]
    nome = str(df.iloc[0]["Nome"])
    char_id = next(p["id"] for p in db.carregar_personagens(sb, uid)
                   if p["Nome"] == nome)
    original = poder_no_banco()
    total = len(df)
    print(f"   copia: {copia is not None} | pendente: "
          f"{copia and copia['pendente']} | {nome} = {original}")
    if not copia or copia["pendente"] or len(copia["dados"][ABA_GERAL]) != total:
        falhas.append("a copia nao foi gravada certa na abertura")
    app.destroy()
    cache_local.memorizar_conta(email, uid, senha,
                                resp.session.refresh_token)

    try:
        print("2) abrir offline")
        app = GrandChaseApp(user=SimpleNamespace(id=uid, email=email),
                            supabase=auth.get_supabase(), offline=True)
        esperar(app, segundos=1)
        print(f"   offline: {app.offline} | personagens: "
              f"{len(app.dfs.get(ABA_GERAL, []))}/{total} | status: "
              f"{app.status_var.get()[:60]!r}")
        if not app.offline or len(app.dfs.get(ABA_GERAL, [])) != total:
            falhas.append("offline nao abriu a copia")

        print("3) editar offline")
        editar_poder(app, nome, original + 7)
        copia = cache_local.ler_copia(uid)
        print(f"   pendente: {copia['pendente']} | copia: "
              f"{poder_na_copia(uid, nome)} | banco: {poder_no_banco()} | "
              f"sair sem perguntar: {app._salvo_neste_pc()}")
        if (not copia["pendente"] or poder_na_copia(uid, nome) != original + 7
                or poder_no_banco() != original or not app._salvo_neste_pc()):
            falhas.append("a edicao offline nao ficou pendente no PC")

        print("4) a internet volta")
        situacao = app._reconectar()
        app._ao_reconectar(True, situacao)
        esperar(app, lambda: not app.modified and not app._salvando, 20)
        print(f"   reconectar: {situacao} | banco: {poder_no_banco()} | "
              f"pendente: {cache_local.ler_copia(uid)['pendente']}")
        if (situacao != "online" or poder_no_banco() != original + 7
                or cache_local.ler_copia(uid)["pendente"]):
            falhas.append("nao sincronizou ao reconectar")
        app.destroy()

        print("5) pendencia de uma sessao anterior vai antes da carga")
        copia = cache_local.ler_copia(uid)
        for linha in copia["dados"][ABA_GERAL]:
            if linha["Nome"] == nome:
                for c in linha:
                    if coluna_banco(c) == "poder":
                        linha[c] = original + 2
        cache_local.salvar_copia(uid, copia["dados"], copia["originais"],
                                 pendente=True)
        app = GrandChaseApp(user=user, supabase=sb)
        esperar(app, segundos=1)
        print(f"   banco: {poder_no_banco()} | status: "
              f"{app.status_var.get()[-40:]!r}")
        if poder_no_banco() != original + 2 or app.offline:
            falhas.append("a pendencia nao foi enviada na abertura")

        print("6) a internet cai no meio do uso")
        real = app_salvamento.salvar_conta

        def sem_rede(*_a, **_k):
            raise httpx.ConnectError("[Errno 11001] getaddrinfo failed")
        app_salvamento.salvar_conta = sem_rede
        editar_poder(app, nome, original + 3)
        esperar(app, lambda: app.offline and not app._salvando, 10)
        app_salvamento.salvar_conta = real
        copia = cache_local.ler_copia(uid)
        print(f"   offline: {app.offline} | pendente: {copia['pendente']} | "
              f"copia: {poder_na_copia(uid, nome)} | banco: {poder_no_banco()}")
        if not app.offline or not copia["pendente"] or \
                poder_na_copia(uid, nome) != original + 3:
            falhas.append("a queda nao virou pendencia no PC")
        app._ao_reconectar(True, app._reconectar())
        esperar(app, lambda: not app.modified and not app._salvando, 20)
        print(f"   depois de reconectar: banco {poder_no_banco()}")
        if poder_no_banco() != original + 3:
            falhas.append("a pendencia da queda nao subiu")

        editar_poder(app, nome, original)
        esperar(app, lambda: not app.modified and not app._salvando, 20)
        app.destroy()
    finally:
        if poder_no_banco() != original:
            sb.table("user_characters").update({"poder": original}) \
                .eq("id", char_id).execute()
        print(f"   restaurado: {nome} = {poder_no_banco()}")

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nOFFLINE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

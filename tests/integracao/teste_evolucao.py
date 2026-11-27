"""
A guia "Evolucao" na tela de verdade.

Valida (o historico do banco e SIMULADO: nada e gravado):
  1. o 9o cartao "EVOLUCAO SEMANAL" NAO existe mais (virou a guia)
  2. a guia mostra as semanas do historico + a atual, e "Copiar imagem"
     poe uma imagem na area de transferencia
  3. "Salvar PNG" grava o arquivo
  4. 1o login depois do reset: a guia abre sozinha destacando a semana
     que acabou e marca como vista
  5. depois de vista, NAO abre de novo
  6. sem a tabela no banco (SQL nao rodado): nao abre sozinha e a guia
     mostra so a semana atual

    python tests/integracao/teste_evolucao.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import tempfile
import time
from datetime import date

import app_evolucao
import auth
import paginas
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

LINHAS = [
    {"character_name": nome, "semana": semana, "poder": poder,
     "nivel_chaser": poder // 300,
     "pecas_void": {"elmo": True, "diadema": semana == "2026-11-25"},
     "desafios": {"void_4": True, "caminho_abissal": semana == "2026-11-25"}}
    for semana, poder in (("2026-11-18", 100_000), ("2026-11-25", 120_000))
    for nome in ("Elesis", "Lire")
]


def _esperar(app, segundos=3.0):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.03)


def _na_evolucao(app):
    pagina = getattr(app, "_paginas", {}).get("evolucao")
    return (app.pagina_atual == "evolucao" and pagina is not None
            and pagina.visivel())


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    falhas = []
    estado = {"visto": None, "marcados": [], "tabela": True}

    def carregar(_sb):
        return (list(LINHAS), True) if estado["tabela"] else ([], False)

    def marcar(_sb, _uid, data):
        estado["marcados"].append(data)
        estado["visto"] = data.isoformat()
        return True

    app_evolucao.carregar_historico = carregar
    app_evolucao.ler_perfil = lambda _sb, _uid: {"resumo_visto": estado["visto"]}
    app_evolucao.marcar_resumo_visto = marcar

    app = GrandChaseApp(user=user, supabase=sb)
    # espera a abertura automatica (a 1a chamada ao banco pode demorar)
    fim = time.time() + 15
    while time.time() < fim and not _na_evolucao(app):
        _esperar(app, 0.2)
    _esperar(app, 0.8)

    print("4) 1o login depois do reset: a guia abre sozinha")
    aberta = _na_evolucao(app)
    print(f"   abriu sozinha: {aberta} | marcada como vista: "
          f"{estado['marcados']}")
    if not aberta or estado["marcados"] != [date(2026, 11, 25)]:
        falhas.append("nao abriu sozinha / nao marcou como vista")

    print("1) o 9o cartao virou a guia")
    if "evolucao" in app.itens_valores:
        falhas.append("o 9o cartao ainda existe")
    print(f"   cartoes: {len(app.itens_valores)}")

    print("2) a guia e o copiar")
    app.ir_para("maestria")
    _esperar(app, 0.3)
    app.ir_para("evolucao")
    _esperar(app, 2.0)
    pagina = app._paginas["evolucao"]
    if not _na_evolucao(app):
        falhas.append("a guia Evolucao nao abriu")
    print(f"   imagem: {pagina.imagem.size}")
    pagina.copiar()
    app.update()
    aviso = pagina.itemcget(pagina._aviso, "text")
    print(f"   aviso: {aviso!r}")
    if "copiada" not in aviso.lower():
        falhas.append("copiar imagem falhou")

    print("3) salvar PNG")
    destino = os.path.join(tempfile.mkdtemp(), "evolucao.png")
    paginas.filedialog.asksaveasfilename = lambda **k: destino
    pagina.salvar_png()
    print(f"   arquivo: {os.path.exists(destino)} "
          f"({os.path.getsize(destino) if os.path.exists(destino) else 0} bytes)")
    if not os.path.exists(destino):
        falhas.append("salvar PNG nao gravou")

    print("5) depois de vista, nao abre de novo")
    app.ir_para("maestria")
    _esperar(app, 0.3)
    app._verificar_resumo_semanal()
    _esperar(app, 2.0)
    if app.pagina_atual != "maestria":
        falhas.append("abriu de novo depois de vista")
    print(f"   marcacoes: {len(estado['marcados'])} (continua 1)")

    print("6) sem a tabela no banco")
    estado.update(tabela=False, visto=None)
    app._semanas_historico = []
    app._verificar_resumo_semanal()
    _esperar(app, 2.0)
    if app.pagina_atual != "maestria":
        falhas.append("abriu sozinha sem a tabela")
    app.ir_para("evolucao")
    _esperar(app, 2.0)
    if not _na_evolucao(app) or app._paginas["evolucao"].imagem is None:
        falhas.append("sem a tabela, a guia nao mostrou a semana atual")

    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nEVOLUCAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

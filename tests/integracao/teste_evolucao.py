"""
A pagina "Evolucao semanal" na tela de verdade.

Valida (o historico do banco e SIMULADO: nada e gravado):
  1. o 9o cartao "EVOLUCAO SEMANAL" existe e abre a pagina
  2. a pagina tem as semanas do historico + a atual, e "Copiar imagem"
     poe uma imagem na area de transferencia
  3. "Salvar PNG" grava o arquivo
  4. 1o login depois do reset: abre sozinha destacando a semana que
     acabou e marca como vista
  5. depois de vista, NAO abre de novo
  6. sem a tabela no banco (SQL nao rodado): nao abre e nao quebra

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
import janela_evolucao
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

LINHAS = [
    {"character_name": nome, "semana": semana, "poder": poder,
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
    while time.time() < fim and getattr(app, "_janela_evolucao", None) is None:
        _esperar(app, 0.2)
    _esperar(app, 0.5)

    print("4) 1o login depois do reset: abre sozinha")
    janela = getattr(app, "_janela_evolucao", None)
    aberta = janela is not None and janela.winfo_exists()
    print(f"   abriu sozinha: {aberta} | marcada como vista: "
          f"{estado['marcados']}")
    if not aberta or estado["marcados"] != [date(2026, 11, 25)]:
        falhas.append("nao abriu sozinha / nao marcou como vista")

    print("1) o 9o cartao")
    valor, legenda = (app.canvas.itemcget(i, "text")
                      for i in app.itens_valores["evolucao"][:2])
    print(f"   cartao: {valor!r} {legenda!r}")
    if "%" not in valor:
        falhas.append("o cartao nao mostra a variacao do ataque medio")
    if aberta:
        janela.fechar()
    app.abrir_evolucao()
    _esperar(app, 2.0)
    janela = app._janela_evolucao
    if not janela.winfo_exists():
        falhas.append("o cartao nao abriu a pagina")

    print("2) a pagina e o copiar")
    print(f"   imagem: {janela.imagem.size}")
    janela.copiar()
    app.update()
    print(f"   status: {janela.status.cget('text')!r}")
    if "copiada" not in janela.status.cget("text").lower():
        falhas.append("copiar imagem falhou")

    print("3) salvar PNG")
    destino = os.path.join(tempfile.mkdtemp(), "evolucao.png")
    janela_evolucao.filedialog.asksaveasfilename = lambda **k: destino
    janela.salvar_png()
    print(f"   arquivo: {os.path.exists(destino)} "
          f"({os.path.getsize(destino) if os.path.exists(destino) else 0} bytes)")
    if not os.path.exists(destino):
        falhas.append("salvar PNG nao gravou")
    janela.fechar()

    print("5) depois de vista, nao abre de novo")
    app._janela_evolucao = None
    app._verificar_resumo_semanal()
    _esperar(app, 2.0)
    if app._janela_evolucao is not None:
        falhas.append("abriu de novo depois de vista")
    print(f"   marcacoes: {len(estado['marcados'])} (continua 1)")

    print("6) sem a tabela no banco")
    estado.update(tabela=False, visto=None)
    app._verificar_resumo_semanal()
    _esperar(app, 2.0)
    if app._janela_evolucao is not None:
        falhas.append("abriu sem a tabela")
    app.abrir_evolucao()
    _esperar(app, 2.0)
    if not app._janela_evolucao.winfo_exists():
        falhas.append("sem a tabela, o cartao nao abriu a semana atual")
    app._janela_evolucao.fechar()

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

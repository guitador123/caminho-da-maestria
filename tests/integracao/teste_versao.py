"""
Teste do botao "Versao X.Y.Z" (procurar atualizacao) na tela principal.

Abre a tela de verdade (Supabase), mas a verificacao e a instalacao sao
SIMULADAS: nada e baixado nem instalado.

Valida:
  1. o botao mostra a versao (versao_app.VERSAO)
  2. "ja esta na mais recente" -> so a barra de status
  3. sem internet -> aviso na barra, sem travar
  4. versao nova + alteracao nao salva -> avisa e NAO atualiza
  5. versao nova + "Nao" -> nao atualiza
  6. versao nova + "Sim" -> chama a instalacao; se falhar, avisa e continua
  7. a tela continua respondendo durante a verificacao (thread)

    python tests/integracao/teste_versao.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
import tkinter.messagebox as mb

import auth
import atualizacao
import app_atualizacao
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from versao_app import VERSAO


def _status(app):
    return app.status_var.get()


def _esperar(app, limite=5.0):
    """Puxa a UI ate a verificacao em segundo plano terminar."""
    fim = time.time() + limite
    while time.time() < fim:
        app.update()
        time.sleep(0.03)
        if not getattr(app, "_atualizando", False):
            for _ in range(5):
                app.update()
            return True
    return False


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    app = GrandChaseApp(user=user, supabase=sb)
    app.update()
    falhas = []
    perguntas, avisos, erros, instalacoes = [], [], [], []
    resposta_sim = [False]
    mb.askyesno = lambda *a, **k: perguntas.append(a) or resposta_sim[0]
    mb.showwarning = lambda *a, **k: avisos.append(a)
    mb.showerror = lambda *a, **k: erros.append(a)
    app_atualizacao.messagebox = mb

    def simular(resultado, demora=0.0):
        def procurar():
            time.sleep(demora)
            return resultado
        atualizacao.procurar_atualizacao = procurar

    def instalar_falhando():
        instalacoes.append(True)
        return False
    atualizacao.aplicar_atualizacao = instalar_falhando

    print("1) o botao mostra a versao")
    rotulo = app.canvas.itemcget(app.itens_botoes["topo1"], "tags")
    textos = [app.canvas.itemcget(i, "text")
              for i in app.canvas.find_all()
              if app.canvas.type(i) == "text"]
    print(f"   procurando 'Versao {VERSAO}' nos textos da tela")
    if f"Versão {VERSAO}" not in textos:
        falhas.append("o botao nao mostra a versao")
    del rotulo

    print("2) ja esta na mais recente")
    simular({"nova": False, "versao": "", "erro": ""})
    app._clic_botao("topo1")
    _esperar(app)
    print("   status:", _status(app))
    if VERSAO not in _status(app) or perguntas:
        falhas.append("mensagem de 'mais recente' errada")

    print("3) sem internet")
    simular({"nova": False, "versao": "", "erro": "sem rede"})
    app._clic_botao("topo1")
    _esperar(app)
    print("   status:", _status(app))
    if "Não foi possível" not in _status(app):
        falhas.append("sem internet nao avisou")

    print("4) versao nova + alteracao nao salva")
    simular({"nova": True, "versao": "9.9.9", "erro": ""})
    app.modified = True
    app._clic_botao("topo1")
    _esperar(app)
    print("   avisos:", len(avisos), "| status:", _status(app))
    if len(avisos) != 1 or instalacoes or perguntas:
        falhas.append("nao bloqueou com alteracao nao salva")
    app.modified = False

    print("5) versao nova + Nao")
    resposta_sim[0] = False
    app._clic_botao("topo1")
    _esperar(app)
    print("   perguntou:", perguntas[-1][0] if perguntas else "-")
    if len(perguntas) != 1 or instalacoes or "9.9.9" not in perguntas[-1][0]:
        falhas.append("o 'Nao' nao respeitado ou titulo sem a versao nova")

    print("6) versao nova + Sim (instalacao simulada falhando)")
    resposta_sim[0] = True
    app._clic_botao("topo1")
    _esperar(app)
    _esperar(app)
    print("   instalou:", len(instalacoes), "| erros:", len(erros),
          "| status:", _status(app))
    if len(instalacoes) != 1 or len(erros) != 1:
        falhas.append("o 'Sim' nao chamou a instalacao / nao avisou a falha")

    print("7) a tela responde durante a verificacao")
    simular({"nova": False, "versao": "", "erro": ""}, demora=1.0)
    app._clic_botao("topo1")
    inicio = time.time()
    app.update()
    gasto = time.time() - inicio
    print(f"   update() levou {gasto:.3f}s com a verificacao rodando")
    _esperar(app)
    if gasto > 0.5:
        falhas.append("a verificacao travou a tela")

    app.quit_app() if hasattr(app, "quit_app") else app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nVERSAO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

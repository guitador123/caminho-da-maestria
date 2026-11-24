"""
Rolagem suave da tela principal, em varias resolucoes.

Valida, rolando com a roda do mouse (eventos simulados) ate o ultimo card:
  1. cada clique anda uma fracao da TELA (nao 40 px fixos): ir do topo ao
     fim leva poucos cliques em qualquer resolucao
  2. a tela desliza (varios quadros) e termina rapido (< 400 ms)
  3. a arte de fundo fica colada no topo em TODOS os quadros
  4. no fim da pagina ela para (nao passa do ultimo card) e volta ao topo

    python tests/integracao/teste_rolagem_suave.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from types import SimpleNamespace

import auth
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste

RESOLUCOES = ("1152x820", "1366x700", "1600x900", "1920x1040")


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.01)


def _clique(app, delta, falhas, rotulo):
    """Um clique da roda; devolve (px andados, ms, quadros)."""
    rolagem = app._rolagem
    rolagem._ultimo_clique = 0.0          # clique "devagar" (sem acelerar)
    antes = rolagem.topo()
    quadros = []
    original = rolagem.ao_mover

    def contar():
        original()
        topo = app.canvas.canvasy(0)
        fundo = app.canvas.coords(app._item_cenario)[1]
        quadros.append(abs(fundo - topo))
    rolagem.ao_mover = contar
    inicio = time.perf_counter()
    app._rolar(SimpleNamespace(delta=delta))
    while rolagem.alvo is not None and time.perf_counter() - inicio < 2:
        app.update()
        time.sleep(0.001)
    ms = (time.perf_counter() - inicio) * 1000
    rolagem.ao_mover = original
    if any(d > 1 for d in quadros):
        falhas.append(f"{rotulo}: o fundo saiu do lugar num quadro")
    return abs(rolagem.topo() - antes), ms, len(quadros)


def _girar_rapido(app, delta, intervalo_ms=40):
    """Cliques a cada 40 ms (girar a roda rapido) ate a ponta; devolve
    quantos cliques foram precisos.

    Os cliques entram como TIMERS do Tk, intercalados com os quadros da
    animacao, como os eventos da roda no app de verdade (um update()
    sozinho roda a animacao inteira antes de voltar)."""
    rolagem = app._rolagem
    estado = {"cliques": 0, "parou": False}

    def clicar():
        antes = rolagem.alvo if rolagem.alvo is not None else rolagem.topo()
        app._rolar(SimpleNamespace(delta=delta))
        depois = rolagem.alvo if rolagem.alvo is not None else rolagem.topo()
        if abs(depois - antes) < 1:        # chegou na ponta
            estado["parou"] = True
            return
        estado["cliques"] += 1
        if estado["cliques"] < 200:
            app.after(intervalo_ms, clicar)

    clicar()
    limite = time.time() + 20
    while not estado["parou"] and time.time() < limite:
        app.update()
        time.sleep(0.001)
    _esperar(app, 0.6)
    return estado["cliques"]


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    app = GrandChaseApp(user=resp.user, supabase=sb)
    _esperar(app, 2.0)
    falhas = []

    for resolucao in RESOLUCOES:
        app.geometry(resolucao + "+0+0")
        _esperar(app, 1.5)
        app._rolagem.ir_para(0)
        app.update()
        total = float(str(app.canvas.cget("scrollregion")).split()[3])
        visivel = app.canvas.winfo_height()
        fim = total - visivel

        # cliques devagar (um de cada vez), ate o fim
        cliques, tempos, quadros = 0, [], []
        while app._rolagem.topo() < fim - 1 and cliques < 200:
            andou, ms, q = _clique(app, -120, falhas, resolucao)
            cliques += 1
            if app._rolagem.topo() < fim - 1:   # o ultimo encosta no fim
                tempos.append(ms)
                quadros.append(q)
        antigo = int(fim // 40) + 1          # 40 px por clique, antes
        tempos.sort()
        mediana = tempos[len(tempos) // 2]
        print(f"{resolucao}: pagina {total:.0f} px | ate o fim: {cliques} "
              f"cliques devagar (antes: {antigo}) | deslize {mediana:.0f} ms "
              f"(pior {tempos[-1]:.0f}) em {min(quadros)}-{max(quadros)} "
              "quadros")

        if cliques > antigo / 3:
            falhas.append(f"{resolucao}: ainda precisa de muitos cliques")
        # o 1o clique de cada resolucao inclui o 1o desenho da pagina
        if mediana > 400:
            falhas.append(f"{resolucao}: o deslize demorou {mediana:.0f} ms")
        if min(quadros) < 3:
            falhas.append(f"{resolucao}: nao deslizou (pulou de uma vez)")

        # no fim, mais um clique nao passa do ultimo card
        _clique(app, -120, falhas, resolucao)
        if app._rolagem.topo() > fim + 1:
            falhas.append(f"{resolucao}: passou do fim da pagina")

        # girando rapido (a aceleracao): sobe ate o topo e desce ate o fim
        subir = _girar_rapido(app, 120)
        if app._rolagem.topo() > 1:
            falhas.append(f"{resolucao}: nao voltou ao topo")
        descer = _girar_rapido(app, -120)
        if app._rolagem.topo() < fim - 1:
            falhas.append(f"{resolucao}: girando rapido nao chegou ao fim")
        print(f"   girando rapido: {descer} cliques para descer, "
              f"{subir} para subir")
        if descer > cliques * 0.6:
            falhas.append(f"{resolucao}: girar rapido nao acelerou")

    app.destroy()
    if falhas:
        print("\nFALHOU:")
        for f in sorted(set(falhas)):
            print("  -", f)
        return 1
    print("\nROLAGEM SUAVE OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

"""Rolagem suave (rolagem.py): a conta da desaceleracao e o canvas."""

import time
import tkinter as tk

import pytest

import rolagem as r


def test_desaceleracao_nao_depende_do_quadro():
    """Dois quadros de 8 ms andam o mesmo que um de 16 ms."""
    dois = r.proximo_passo(r.proximo_passo(0, 1000, 0.008), 1000, 0.008)
    um = r.proximo_passo(0, 1000, 0.016)
    assert abs(dois - um) < 0.5


def test_chega_e_encosta_no_alvo():
    atual, passos = 0.0, 0
    while atual != 500 and passos < 200:
        atual = r.proximo_passo(atual, 500, 0.016)
        passos += 1
    assert atual == 500
    # ~150-250 ms a 60 quadros por segundo
    assert 8 <= passos <= 30


def test_sobe_e_desce():
    assert 0 < r.proximo_passo(0, 300, 0.016) < 300
    assert 0 < r.proximo_passo(300, 0, 0.016) < 300


@pytest.fixture(scope="module")
def raiz():
    """UMA janela Tk para o arquivo: criar varios tk.Tk() seguidos no
    mesmo processo as vezes falha no Python do Anaconda ("Can't find a
    usable tk.tcl")."""
    try:
        janela = tk.Tk()
    except tk.TclError as erro:
        pytest.skip(f"sem tela para o Tk: {erro}")
    janela.geometry("400x500+0+0")
    yield janela
    janela.destroy()


@pytest.fixture
def canvas(raiz):
    tela = tk.Canvas(raiz, highlightthickness=0, yscrollincrement=1)
    tela.pack(fill="both", expand=True)
    tela.configure(scrollregion=(0, 0, 400, 5000))
    raiz.update()
    yield tela
    tela.destroy()


def _esperar(tela, rolagem, limite=2.0):
    fim = time.time() + limite
    while rolagem.alvo is not None and time.time() < fim:
        tela.update()
        time.sleep(0.005)


def test_passo_proporcional_a_tela_e_cliques_somam(canvas):
    movidos = []
    rolagem = r.RolagemSuave(canvas, ao_mover=lambda: movidos.append(1))
    rolagem.roda(-120)                    # 1 clique para baixo
    _esperar(canvas, rolagem)
    passo = rolagem.topo()
    assert passo == pytest.approx(max(r.PASSO_MINIMO, 500 * r.FRACAO_DA_TELA),
                                  abs=1)
    assert len(movidos) > 3               # deslizou (varios quadros)
    rolagem._ultimo_clique = 0.0          # o 1o dos 3 nao e "rapido"
    for _ in range(3):                    # 3 cliques rapidos: somam e aceleram
        rolagem.roda(-120)
    _esperar(canvas, rolagem)
    esperado = passo * (1 + (1 + r.ACELERACAO) + (1 + 2 * r.ACELERACAO))
    assert rolagem.topo() == pytest.approx(passo + esperado, abs=2)


def test_aceleracao_so_com_cliques_rapidos_no_mesmo_sentido(canvas):
    rolagem = r.RolagemSuave(canvas)
    rolagem.roda(-120)
    rolagem.roda(-120)
    assert rolagem.ritmo == pytest.approx(1 + r.ACELERACAO)
    for _ in range(20):
        rolagem.roda(-120)
    assert rolagem.ritmo == r.RITMO_MAXIMO            # tem teto
    rolagem.roda(120)                                 # mudou o sentido
    assert rolagem.ritmo == 1.0
    rolagem._ultimo_clique -= 1.0                     # clique devagar
    rolagem.roda(120)
    assert rolagem.ritmo == 1.0


def test_nao_passa_do_fim_nem_do_comeco(canvas):
    rolagem = r.RolagemSuave(canvas)
    for _ in range(200):
        rolagem.roda(-120)
    _esperar(canvas, rolagem, 4)
    assert rolagem.topo() == pytest.approx(5000 - 500, abs=1)
    rolagem.roda(120 * 500)
    _esperar(canvas, rolagem, 4)
    assert rolagem.topo() == 0


def test_parar_esquece_o_destino(canvas):
    rolagem = r.RolagemSuave(canvas)
    rolagem.roda(-120 * 10)
    canvas.update()
    rolagem.parar()
    onde = rolagem.topo()
    for _ in range(10):
        canvas.update()
        time.sleep(0.01)
    assert rolagem.topo() == onde and rolagem.alvo is None

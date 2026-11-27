"""A barra de guias do topo (paginas.py): ordem, ativa, centro e fixa."""

import tkinter as tk

import tema_visual as tv
from paginas import ABAS, BarraAbas


def test_as_guias_e_a_ordem():
    assert ABAS == [("maestria", "Maestria"), ("guilda", "Guilda"),
                    ("ranking", "Ranking"), ("evolucao", "Evolução")]
    # o 9o cartao virou a guia
    assert "evolucao" not in [chave for chave, _t, _s in tv.CARDS]


def test_barra_centralizada_com_a_ativa_em_destaque(raiz):
    canvas = tk.Canvas(raiz, width=1152, height=500)
    canvas.pack()
    trocas = []
    try:
        barra = BarraAbas(canvas, trocas.append)
        barra.desenhar(tv.Layout(1152, 820), "guilda")
        raiz.update()
        assert barra.ativa == "guilda"
        fontes = {c: canvas.itemcget(i, "font") for c, i in barra.itens_texto.items()}
        assert "bold" in fontes["guilda"]
        assert "bold" not in fontes["maestria"]
        x1, _y1, x2, _y2 = canvas.bbox("abas")
        assert abs((x1 + x2) / 2 - 576) <= 2
        # na ordem, da esquerda para a direita
        xs = [canvas.bbox(barra.itens_texto[c])[0] for c, _r in ABAS]
        assert xs == sorted(xs)
    finally:
        canvas.destroy()


def test_barra_fica_no_topo_ao_rolar(raiz):
    canvas = tk.Canvas(raiz, width=800, height=300, yscrollincrement=1)
    canvas.pack()
    try:
        canvas.configure(scrollregion=(0, 0, 800, 3000))
        canvas.create_rectangle(0, 0, 800, 3000, fill="#222")  # o conteudo
        barra = BarraAbas(canvas, lambda c: None)
        barra.desenhar(tv.Layout(800, 300), "maestria")
        raiz.update()
        antes = canvas.bbox("abas")[1] - canvas.canvasy(0)
        canvas.yview_moveto(0.5)
        barra.fixar()
        raiz.update()
        depois = canvas.bbox("abas")[1] - canvas.canvasy(0)
        assert abs(depois - antes) < 1
        # um item novo (card redesenhado) nao fica por cima da barra
        canvas.create_rectangle(0, 0, 800, 3000, fill="#333")
        barra.fixar()
        assert not canvas.find_above(canvas.find_withtag("abas")[-1])
    finally:
        canvas.destroy()

"""O gc e as imagens do Tk (o app fechava ao abrir perfis na Guilda)."""

import gc
import tkinter as tk

from PIL import Image

import segundo_plano
from card_personagem import CardPersonagem, foto_compartilhada


def test_gc_so_volta_quando_todos_os_trabalhos_terminam():
    assert gc.isenabled()
    segundo_plano.comecar()                 # a lista da Guilda
    segundo_plano.comecar()                 # a conta de alguem, junto
    assert not gc.isenabled()
    segundo_plano.terminar()                # a lista terminou primeiro...
    assert not gc.isenabled()               # ...mas a conta ainda roda
    segundo_plano.terminar()
    assert gc.isenabled()
    assert segundo_plano.ativos() == 0
    segundo_plano.terminar()                # terminar a mais nao quebra
    assert gc.isenabled() and segundo_plano.ativos() == 0


def test_imagens_iguais_viram_uma_so(raiz):
    a = Image.new("RGBA", (9, 9), (34, 197, 94, 255))
    b = Image.new("RGBA", (9, 9), (34, 197, 94, 255))
    c = Image.new("RGBA", (9, 9), (244, 63, 94, 255))
    assert foto_compartilhada(raiz, a) is foto_compartilhada(raiz, b)
    assert foto_compartilhada(raiz, a) is not foto_compartilhada(raiz, c)


def test_25_cards_quase_nao_criam_imagens_novas(raiz):
    """Cada card desenha dezenas de imagens; os 25 juntos tem que ficar
    longe do limite de bitmaps do Windows (~10.000)."""
    canvas = tk.Canvas(raiz)
    try:
        raiz._cache_fotos_card = {}
        dados = {"nome": "Ai", "poder": 1000, "titulo": "Renak",
                 "pecas": {"cartascota": "Ataque +555|Outra||",
                           "pedraarma": "18|10% Dano Crítico"},
                 "acessorios": {"anel": "Anel do Piu Piu", "colar": "Outro"},
                 "semanais": {"void4": "Verdadeiro"}}
        cards = [CardPersonagem(canvas, 0, i * 10, dict(dados)) for i in range(25)]
        um_card = len({id(f) for f in cards[0]._fotos.values()})
        todos = len({id(f) for c in cards for f in c._fotos.values()})
        assert um_card > 20                 # um card tem muitas imagens...
        assert todos == um_card             # ...mas 25 iguais usam as mesmas
    finally:
        canvas.destroy()

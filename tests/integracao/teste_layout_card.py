"""
Teste de LAYOUT do card (pendencia #6): os cards tem que se adaptar a
QUALQUER resolucao.

Valida:
  1. nenhuma sobreposicao de texto no card, em varias escalas
  2. o card cabe inteiro na altura da tela (1152, FullHD, QuadHD)
  3. a grade preenche a largura da tela (nada de metade vazia)

    python teste_layout_card.py
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

from app_grandchase import GrandChaseApp
from card_personagem import CardPersonagem

RESOLUCOES = [(1152, 820), (1920, 1080), (2560, 1440)]
ESCALAS = [1.0, 1.2, 1.4, 1.6]


def sobreposicoes(canvas, itens):
    """Pares de textos DIFERENTES que se sobrepoem (ignora o contorno)."""
    textos = []
    for item in itens:
        if canvas.type(item) != "text":
            continue
        txt = canvas.itemcget(item, "text")
        if not str(txt).strip():
            continue
        bbox = canvas.bbox(item)
        if bbox:
            textos.append((bbox, txt))
    achados = []
    for i in range(len(textos)):
        for j in range(i + 1, len(textos)):
            b1, t1 = textos[i]
            b2, t2 = textos[j]
            if t1 == t2:
                continue          # copias do contorno
            ox = min(b1[2], b2[2]) - max(b1[0], b2[0])
            oy = min(b1[3], b2[3]) - max(b1[1], b2[1])
            if ox > 2 and oy > 2:
                achados.append((t1[:24], t2[:24], ox, oy))
    return achados


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(1.0)
    app.update()

    card = app.cards_personagem[0]
    print(f"1) card de teste: {card.dados.get('nome')}")

    # --- 1) sobreposicoes em varias escalas -------------------------------
    print("\n2) sobreposicao de texto por escala:")
    falhas = 0
    for escala in ESCALAS:
        canvas = app.canvas
        novo = CardPersonagem(canvas, 4000, 4000, card.dados,
                               pasta_retratos=None, escala=escala)
        app.update()
        achados = sobreposicoes(canvas, novo._itens)
        print(f"   escala {escala:.1f}: {len(achados)} sobreposicao(oes)")
        for achado in achados[:5]:
            linha = (f"      {achado[0]!r} x {achado[1]!r} "
                     f"({achado[2]}x{achado[3]}px)")
            print(linha.encode("ascii", "replace").decode("ascii"))
        if achados:
            falhas += 1
        for item in novo._itens:
            canvas.delete(item)
    if falhas:
        print(f"   FALHOU: {falhas} escala(s) com texto sobreposto")
        app.destroy()
        return 1

    # --- 2) resolucoes ----------------------------------------------------
    print("\n3) resolucoes:")
    for largura, altura in RESOLUCOES:
        app.geometry(f"{largura}x{altura}+0+0")
        app.update_idletasks()
        app.update()
        time.sleep(1.2)
        app.update()

        cards = app.cards_personagem
        if not cards:
            print(f"   FALHOU: {largura}x{altura} sem cards")
            app.destroy()
            return 1
        escala = cards[0].s
        altura_card = cards[0].altura
        # colunas: quantos cards comem lado a lado
        x0 = cards[0].x0
        colunas = sum(1 for c in cards if abs(c.y0 - cards[0].y0) < 1)
        # largura usada pela grade
        largura_grade = (cards[colunas - 1].x0 + largura_card(cards[colunas - 1])
                         - x0)
        print(f"   {largura}x{altura}: escala={escala:.2f} "
              f"colunas={colunas} card={altura_card}px "
              f"(altura da tela {altura})")
        if altura_card > altura and escala > 1.001:
            print(f"   FALHOU: o card ({altura_card}px) nao cabe na tela "
                  f"({altura}px) com escala {escala:.2f}")
            app.destroy()
            return 1
        if largura_grade < (largura - 60) * 0.85:
            print(f"   FALHOU: a grade so usa {largura_grade:.0f}px de {largura}px")
            app.destroy()
            return 1

    app.destroy()
    print("\nLAYOUT DO CARD OK")
    return 0


def largura_card(card):
    from card_personagem import LARGURA
    return LARGURA * card.s


if __name__ == "__main__":
    sys.exit(main())

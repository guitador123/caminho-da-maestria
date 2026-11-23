"""
Teste da pendencia #5: o CARD INTEIRO e clicavel.

Clica em varias partes do card (nome, titulo, peca, fundo, rodape) e confere
que a edicao do personagem CERTO abre — e que clicar num card nao interfere
nos outros.

    python teste_card_clicavel.py
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

from app_grandchase import GrandChaseApp


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def _fechar(app):
    for janela in _janelas(app):
        try:
            janela.destroy()
        except Exception:
            pass
    app.update()
    time.sleep(0.2)
    app.update()


def _rolar_para(app, card, item):
    """Garante que o item do card esteja visivel na viewport."""
    canvas = card.canvas
    bbox = canvas.bbox(item)
    if not bbox:
        return False
    cy = (bbox[1] + bbox[3]) / 2
    visivel = max(canvas.winfo_height(), 200)
    try:
        total = float(canvas.cget("scrollregion").split()[3])
    except (ValueError, IndexError):
        total = 1.0
    canvas.yview_moveto(max(0.0, min(1.0, (cy - visivel / 2) / total)))
    app.update_idletasks()
    app.update()
    return True


def _clicar_item(app, card, item):
    """Clique de verdade (evento sintetico) no item do card."""
    canvas = card.canvas
    bbox = canvas.bbox(item)
    if not bbox:
        return False
    x = (bbox[0] + bbox[2]) / 2 - canvas.canvasx(0)
    y = (bbox[1] + bbox[3]) / 2 - canvas.canvasy(0)
    canvas.event_generate("<Button-1>", x=x, y=y)
    app.update()
    time.sleep(0.4)
    app.update()
    return True


def _item_por_texto(card, texto):
    canvas = card.canvas
    for item in card._itens:
        if canvas.type(item) != "text":
            continue
        if canvas.itemcget(item, "text") == texto:
            return item
    return None


def _fundo_do_card(card):
    """A imagem de fundo do card (o painel grande)."""
    canvas = card.canvas
    for item in card._itens:
        if canvas.type(item) == "image":
            bbox = canvas.bbox(item)
            if bbox and (bbox[2] - bbox[0]) > card.s * 200:
                return item
    return None


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(1.0)
    app.update()

    nomes = [c.dados.get("nome") for c in app.cards_personagem]
    print(f"1) {len(nomes)} cards na tela")

    alvos = [nomes[0], nomes[len(nomes) // 2], nomes[-1]]
    partes = ["nome", "titulo", "peca", "fundo", "rodape"]

    print("\n2) clique em cada parte do card:")
    falhas = 0
    for nome in alvos:
        card = next(c for c in app.cards_personagem if c.dados.get("nome") == nome)
        for parte in partes:
            _fechar(app)
            if parte == "nome":
                item = _item_por_texto(card, str(nome))
            elif parte == "titulo":
                # "PROGRESSO DO PERSONAGEM" e desenhado letra a letra
                # (tracking), entao procuro o bloco "DESPERTAR"
                item = _item_por_texto(card, "DESPERTAR")
            elif parte == "peca":
                item = _item_por_texto(card, "Arma")
            elif parte == "fundo":
                item = _fundo_do_card(card)
            else:
                item = None
                for cand in card._itens:
                    if card.canvas.type(cand) == "text" and \
                            card.canvas.itemcget(cand, "text").startswith("Liberta"):
                        item = cand
                        break

            if item is None:
                print(f"   FALHOU: {nome} - item '{parte}' nao encontrado")
                falhas += 1
                continue
            if not _rolar_para(app, card, item):
                print(f"   FALHOU: {nome} - '{parte}' sem bbox")
                falhas += 1
                continue
            _clicar_item(app, card, item)
            janelas = _janelas(app)
            if not janelas:
                print(f"   FALHOU: clicar em '{parte}' do card {nome} "
                      f"nao abriu nada")
                falhas += 1
                continue
            aberta = janelas[-1]
            ok = str(aberta.nome) == str(nome)
            print(f"   {nome:10s} clique em {parte:8s} -> abriu {aberta.nome}"
                  f"{'' if ok else '   FALHOU (personagem errado)'}")
            if not ok:
                falhas += 1

    # --- clicar num card nao mexe nos outros ------------------------------
    print("\n3) o clique e por card (sem mistura):")
    _fechar(app)
    primeiro = app.cards_personagem[0]
    segundo = app.cards_personagem[1]
    item = _item_por_texto(primeiro, str(primeiro.dados.get("nome")))
    _rolar_para(app, primeiro, item)
    _clicar_item(app, primeiro, item)
    janelas = _janelas(app)
    if not janelas:
        print("   FALHOU: nao abriu")
        return 1
    print(f"   card '{primeiro.dados.get('nome')}' -> "
          f"abriu '{janelas[-1].nome}'")
    if str(janelas[-1].nome) != str(primeiro.dados.get("nome")):
        print("   FALHOU")
        falhas += 1
    _fechar(app)

    # o segundo card nao pode ter herdado o binding do primeiro
    item = _item_por_texto(segundo, str(segundo.dados.get("nome")))
    _rolar_para(app, segundo, item)
    _clicar_item(app, segundo, item)
    janelas = _janelas(app)
    if not janelas:
        print("   FALHOU: nao abriu")
        return 1
    print(f"   card '{segundo.dados.get('nome')}' -> "
          f"abriu '{janelas[-1].nome}'")
    if str(janelas[-1].nome) != str(segundo.dados.get("nome")):
        print("   FALHOU: abriu o personagem errado")
        falhas += 1

    _fechar(app)
    app.destroy()

    if falhas:
        print(f"\nCARD CLICAVEL: {falhas} FALHA(S)")
        return 1
    print("\nCARD INTEIRO CLICAVEL OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

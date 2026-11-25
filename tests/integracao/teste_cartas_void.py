"""
Cartas e pedra dos equipamentos do Void (itens 15.3 e 16).

    python teste_cartas_void.py [email] [senha] [--print caminho.png]

Valida (Supabase real, restaura no fim):
  1. as 7 colunas existem (sql/cartas_void.sql)
  2. clicar na linha da Cota no card abre a edicao rapida das cartas (e
     NAO a edicao do personagem)
  3. cada slot oferece as cartas da peca (Elmo: so 2 + vazio)
  4. escolher cartas atualiza o card na hora (verde / vermelho / vazio)
  5. as setas passam para a peca seguinte sem fechar
  6. a pedra: nivel sem status avisa e NAO deixa trocar de peca nem fechar;
     completa, aparece no card (chip +12) na hora
  7. fechar salva no banco (cartas e pedra); recarregar mostra o mesmo card
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from card_personagem import coluna_banco_cartas
from credenciais_teste import conta_teste
from dados_app import (CARTAS_VOID, PECAS_COM_CARTAS, estado_da_carta,
                       ler_cartas, ler_pedra)
from janela_cartas import VAZIO, JanelaCartas
from janela_personagem import JanelaPersonagem

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True

COTA = ["Ataque +555", "Outra", VAZIO, "Ataque +507"]
NO_BANCO = "Ataque +555|Outra||Ataque +507"
PEDRA = ("+12", "Ataque Especial +800")
PEDRA_NO_BANCO = "12|Ataque Especial +800"


def _esperar(app, segundos):
    fim = time.time() + segundos
    while time.time() < fim:
        app.update()
        time.sleep(0.02)


def _esperar_salvamento(app, limite=15):
    fim = time.time() + limite
    while time.time() < fim:
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            _esperar(app, 0.6)
            return True
    return False


def _no_banco(sb, user_id, nome):
    pers = db.carregar_personagens(sb, user_id)
    pecas = db.carregar_pecas_void(sb, pers)
    linha = next(p for p in pecas if p.get("Nome") == nome)
    return {f"{tipo}_{p}": linha.get(f"{tipo}_{p}") or ""
            for p in PECAS_COM_CARTAS for tipo in ("cartas", "pedra")}


def _card(app, nome):
    return next(c for c in app.cards_personagem if c.dados.get("nome") == nome)


def _janelas(app, classe):
    return [w for w in app.winfo_children()
            if isinstance(w, classe) and w.winfo_exists()]


def _clicar_na_linha(app, card, peca):
    """Clique de verdade na linha da peca (evento sintetico no canvas)."""
    canvas = app.canvas
    itens = canvas.find_withtag(f"{card.tag}_cartas_{peca}")
    x1, y1, x2, y2 = canvas.bbox(itens[-1])
    # rola ate a linha ficar visivel
    total = float(str(canvas.cget("scrollregion")).split()[3])
    canvas.yview_moveto(max(0.0, (y1 - 200) / total))
    _esperar(app, 0.3)
    cx = int((x1 + x2) / 2 - canvas.canvasx(0))
    cy = int((y1 + y2) / 2 - canvas.canvasy(0))
    canvas.event_generate("<Motion>", x=cx, y=cy)
    canvas.event_generate("<Button-1>", x=cx, y=cy)
    canvas.event_generate("<ButtonRelease-1>", x=cx, y=cy)
    _esperar(app, 1.0)


def main(argv):
    imprimir = None
    if "--print" in argv:
        imprimir = argv[argv.index("--print") + 1]
        argv = argv[:argv.index("--print")]
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    print("1) colunas no banco")
    faltam = [f"{tipo}_{p}" for p in PECAS_COM_CARTAS
              for tipo in ("cartas", "pedra")
              if f"{tipo}_{p}" not in db._extras(sb, "pecas_void")]
    if faltam:
        print(f"   FALHOU: faltam {faltam} (rode sql/cartas_void.sql e "
              "sql/pedras_void.sql)")
        return 1
    print("   OK: as 14 colunas existem")

    app = GrandChaseApp(user=user, supabase=sb)
    app.geometry("1152x820+0+0")
    _esperar(app, 2.0)
    nome = app.cards_personagem[0].dados["nome"]
    originais = _no_banco(sb, user.id, nome)
    print(f"   personagem: {nome}")
    falhas = []

    try:
        print("2) clicar na Cota do card")
        _clicar_na_linha(app, _card(app, nome), "cota")
        janelas = _janelas(app, JanelaCartas)
        if not janelas:
            falhas.append("clicar na Cota nao abriu as cartas")
            return 1
        if _janelas(app, JanelaPersonagem):
            falhas.append("abriu a edicao do personagem junto")
        janela = janelas[-1]
        if janela.peca != "cota":
            falhas.append(f"abriu a peca errada: {janela.peca}")

        print("3) opcoes de cada slot")
        for _marca, menu in janela.slots:
            if list(menu.cget("values")) != [VAZIO] + CARTAS_VOID["cota"]:
                falhas.append(f"opcoes da Cota: {menu.cget('values')}")
                break

        print("4) escolher as cartas (card ao vivo)")
        for (_marca, menu), carta in zip(janela.slots, COTA):
            menu.set(carta)
            janela._escolher(0)
        _esperar(app, 0.3)
        slots = ler_cartas(_card(app, nome).dados["pecas"].get(
            coluna_banco_cartas("cota")))
        estados = [estado_da_carta(c) for c in slots]
        print(f"   card: {estados}")
        if estados != ["status", "outra", None, "status"]:
            falhas.append(f"card = {estados}")

        print("5) setas")
        janela._andar(1)
        _esperar(app, 0.3)
        print(f"   depois da Cota: {janela.peca}")
        if janela.peca != PECAS_COM_CARTAS[PECAS_COM_CARTAS.index("cota") + 1]:
            falhas.append(f"a seta foi para {janela.peca}")
        janela.mostrar(nome, "elmo")
        valores = list(janela.slots[0][1].cget("values"))
        if valores != [VAZIO, "Ataque +100", "Outra"]:
            falhas.append(f"opcoes do Elmo: {valores}")
        janela._andar(1)
        if janela.peca != PECAS_COM_CARTAS[0]:
            falhas.append("a seta nao deu a volta do Elmo para a Arma")
        janela.mostrar(nome, "cota")
        _esperar(app, 0.5)

        print("6) pedra")
        janela.menu_nivel.set(PEDRA[0])
        janela._escolher_pedra()
        if not janela.erro_pedra.cget("text"):
            falhas.append("nivel sem status nao avisou")
        janela._andar(1)
        if janela.peca != "cota":
            falhas.append("trocou de peca com a pedra incompleta")
        janela.fechar()
        _esperar(app, 0.2)
        if not janela.winfo_exists():
            falhas.append("fechou com a pedra incompleta")
            return 1
        janela.menu_status.set(PEDRA[1])
        janela._escolher_pedra()
        _esperar(app, 0.3)
        if janela.erro_pedra.cget("text"):
            falhas.append("a pedra completa ainda mostra erro")
        card = _card(app, nome)
        pedra = ler_pedra(card.dados["pecas"].get("pedracota"))
        textos = [app.canvas.itemcget(i, "text") for i in
                  app.canvas.find_withtag(f"{card.tag}_pedra_cota")
                  if app.canvas.type(i) == "text"]
        print(f"   card: {pedra} | chip {textos}")
        if pedra != (12, PEDRA[1]) or textos != ["+12"]:
            falhas.append(f"card da pedra = {pedra} / {textos}")
        if imprimir:
            from PIL import ImageGrab
            janela.attributes("-topmost", True)
            _esperar(app, 0.5)
            x, y = janela.winfo_rootx(), janela.winfo_rooty()
            ImageGrab.grab((x, y, x + janela.winfo_width(),
                            y + janela.winfo_height()),
                           all_screens=True).save(imprimir)

        print("7) fechar salva")
        janela.fechar()
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        banco = _no_banco(sb, user.id, nome)
        print(f"   no banco: {banco['cartas_cota']!r} | {banco['pedra_cota']!r}")
        if banco["cartas_cota"] != NO_BANCO:
            falhas.append(f"cartas = {banco['cartas_cota']!r}")
        if banco["pedra_cota"] != PEDRA_NO_BANCO:
            falhas.append(f"pedra = {banco['pedra_cota']!r}")
        app.carregar_do_supabase()
        _esperar(app, 1.0)
        volta = _card(app, nome).dados["pecas"].get(coluna_banco_cartas("cota"))
        if volta != NO_BANCO:
            falhas.append(f"depois de recarregar, card = {volta!r}")
        else:
            print("   OK: o card voltou igual")
    finally:
        df = app.dfs["Peças (Void)"]
        mascara = df["Nome"].astype(str) == str(nome)
        from opcoes import coluna_banco
        for nome_banco, valor in originais.items():
            coluna = next((c for c in df.columns
                           if coluna_banco(c) == coluna_banco(nome_banco)),
                          None)
            if coluna:
                df.loc[mascara, coluna] = valor
        app._marcar_modificado()
        app.salvar_supabase()
        _esperar_salvamento(app)
        volta = _no_banco(sb, user.id, nome)
        print(f"8) restaurado: {volta == originais}")
        if volta != originais:
            falhas.append("nao restaurou as cartas originais")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nCARTAS DO VOID OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

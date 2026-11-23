"""
Teste dos bugs reportados na tela de edicao de personagem:

  BUG A) "clicar em editar em qualquer card abre a edicao do Zero"
          -> cada card tem que abrir a SUA propria tela de edicao.

  BUG B) "ao reabrir a edicao, o que foi salvo nao aparece marcado"
          -> a tela de edicao tem que ler os valores SALVOS do personagem
             certo (pecas, acessorios, dungeons, numeros).

O teste clica de verdade na seta (>) de cada card (evento sintetico no
canvas) e confere qual personagem abriu.

    python teste_edicao_personagem.py
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

from app_grandchase import GrandChaseApp
from opcoes import coluna_banco

ABA_GERAL = "Geral"
ABA_PECAS = "Peças (Void)"
ABA_ACESSORIOS = "Acessórios Título"
ABA_SEMANAIS = "Semanais"

# valores bem diferentes por personagem (para nao confundir um com o outro)
CENARIOS = {
    "peca": "arma",
    "dungeon": "void4",
    "anel": "Anel do Piu Piu",
    "poder": 111,
}


# ------------------------------------------------------------------ utils --
def _widget(janela, tipo, logico):
    """Widget da tela de edicao pelo nome LOGICO da coluna."""
    alvo = coluna_banco(logico)
    for (tipo_item, chave), item in janela._linhas.items():
        if tipo_item == tipo and coluna_banco(chave) == alvo:
            return item
    return None


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


def _centro_seta(card):
    canvas = card.canvas
    itens = canvas.find_withtag(card.tag_seta)
    if not itens:
        return None
    for item in itens:
        if canvas.type(item) == "text":
            x, y = canvas.coords(item)
            return x, y
    x, y = canvas.coords(itens[0])
    return x, y


def _clicar_seta(app, card):
    """Clica de verdade na seta do card (evento sintetico no canvas)."""
    canvas = card.canvas
    centro = _centro_seta(card)
    if centro is None:
        return False
    ax, ay = centro
    try:
        total = float(canvas.cget("scrollregion").split()[3])
    except (ValueError, IndexError):
        total = 1.0
    visivel = max(canvas.winfo_height(), 200)
    frac = (ay - visivel / 2) / max(total, 1.0)
    canvas.yview_moveto(max(0.0, min(1.0, frac)))
    app.update_idletasks()
    app.update()
    x = ax - canvas.canvasx(0)
    y = ay - canvas.canvasy(0)
    canvas.event_generate("<Button-1>", x=x, y=y)
    app.update()
    time.sleep(0.3)
    app.update()
    return True


# ------------------------------------------------------------------ teste --
def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(0.8)
    app.update()

    nomes = [str(n) for n in app.dfs[ABA_GERAL]["Nome"].tolist()]
    print(f"1) {len(nomes)} personagens na lista")

    # ---- preenche um cenario diferente para 3 personagens -----------------
    alvos = [nomes[0], nomes[len(nomes) // 2], nomes[-1]]
    df_pecas = app.dfs[ABA_PECAS]
    df_acess = app.dfs[ABA_ACESSORIOS]
    df_sem = app.dfs[ABA_SEMANAIS]
    df_geral = app.dfs[ABA_GERAL]

    pecas_distintas = ["arma", "luvas", "cota"]
    dungeons_distintas = ["void4", "caminhoabissal", "fornalhainfernal"]
    aneis = ["Anel do Piu Piu", "Anel do Ciclo Infinito",
             "Promessa Incumprível III"]

    for indice, nome in enumerate(alvos):
        # limpa as pecas/dungeons/acessorios desses 3 antes de marcar
        for peca in ("arma", "luvas", "cota", "botas"):
            real = _coluna_real(df_pecas, peca)
            if real:
                df_pecas.loc[df_pecas["Nome"].astype(str) == nome, real] = "FALSO"
        for dungeon in ("void4", "caminhoabissal", "fornalhainfernal"):
            real = _coluna_real(df_sem, dungeon)
            if real:
                df_sem.loc[df_sem["Nome"].astype(str) == nome, real] = "Falso"

        real = _coluna_real(df_pecas, pecas_distintas[indice])
        if real:
            df_pecas.loc[df_pecas["Nome"].astype(str) == nome, real] = "VERDADEIRO"
        real = _coluna_real(df_sem, dungeons_distintas[indice])
        if real:
            df_sem.loc[df_sem["Nome"].astype(str) == nome, real] = "Verdadeiro"
        real = _coluna_real(df_acess, "anel")
        if real:
            df_acess.loc[df_acess["Nome"].astype(str) == nome, real] = aneis[indice]
        real = _coluna_real(df_geral, "Poder")
        if real:
            df_geral.loc[df_geral["Nome"].astype(str) == nome, real] = CENARIOS["poder"]

    # ---- BUG A: cada seta abre o SEU personagem --------------------------
    print("\n2) BUG A - cada card abre a sua propria edicao:")
    falhas = 0
    for indice, nome in enumerate(alvos):
        card = next((c for c in app.cards_personagem
                     if c.dados.get("nome") == nome), None)
        if card is None:
            print(f"   FALHOU: card de {nome} nao encontrado")
            falhas += 1
            continue
        _fechar(app)
        if not _clicar_seta(app, card):
            print(f"   FALHOU: nao consegui clicar na seta de {nome}")
            falhas += 1
            continue
        janelas = _janelas(app)
        if not janelas:
            print(f"   FALHOU: clicar na seta de {nome} nao abriu nada")
            falhas += 1
            continue
        aberta = janelas[-1]
        print(f"   seta de {nome:10s} -> abriu {aberta.nome}")
        if str(aberta.nome) != str(nome):
            print(f"   FALHOU: abriu {aberta.nome} em vez de {nome}")
            falhas += 1
    if falhas:
        print(f"   -> {falhas} FALHAS no BUG A")
        app.destroy()
        return 1
    print("   -> OK: cada card abriu o seu proprio personagem")

    # ---- BUG B: o salvo aparece marcado ----------------------------------
    print("\n3) BUG B - o estado salvo aparece marcado ao reabrir:")
    for indice, nome in enumerate(alvos):
        _fechar(app)
        app._abrir_personagem({"nome": nome})
        app.update()
        time.sleep(0.8)
        app.update()
        janelas = _janelas(app)
        if not janelas:
            print(f"   FALHOU: edicao de {nome} nao abriu")
            return 1
        janela = janelas[-1]

        peca = _widget(janela, "peca", pecas_distintas[indice])
        if peca is None:
            print(f"   FALHOU: {nome} - checkbox de peca nao encontrado")
            return 1
        if not _verdadeiro(peca.get()):
            print(f"   FALHOU: {nome} - peca '{pecas_distintas[indice]}' "
                  f"nao veio marcada")
            return 1

        # as outras pecas tem que vir DESMARCADAS
        for outra in ("botas",):
            widget = _widget(janela, "peca", outra)
            if widget is not None and _verdadeiro(widget.get()):
                print(f"   FALHOU: {nome} - peca '{outra}' veio marcada sem ser")
                return 1

        dungeon = _widget(janela, "semanal", dungeons_distintas[indice])
        if dungeon is None:
            print(f"   FALHOU: {nome} - checkbox de dungeon nao encontrado")
            return 1
        if not _verdadeiro(dungeon.get()):
            print(f"   FALHOU: {nome} - dungeon '{dungeons_distintas[indice]}' "
                  f"nao veio marcada")
            return 1

        anel = _widget(janela, "acesso", "anel")
        if anel is None:
            print(f"   FALHOU: {nome} - dropdown de anel nao encontrado")
            return 1
        if anel.get() != aneis[indice]:
            print(f"   FALHOU: {nome} - anel veio {anel.get()!r} "
                  f"(esperado {aneis[indice]!r})")
            return 1

        poder = _widget(janela, "geral", "Poder")
        if poder is None:
            print(f"   FALHOU: {nome} - campo de Poder nao encontrado")
            return 1
        valor = poder[0].get() if isinstance(poder, tuple) else poder.get()
        if str(valor).strip() != str(CENARIOS["poder"]):
            print(f"   FALHOU: {nome} - Poder veio {valor!r} "
                  f"(esperado {CENARIOS['poder']})")
            return 1

        print(f"   {nome:10s} peca={pecas_distintas[indice]} "
              f"dungeon={dungeons_distintas[indice]} "
              f"anel={anel.get()} poder={valor}  OK")

    # ---- BUG B (2o round): salva, fecha e reabre --------------------------
    print("\n4) BUG B - salva, fecha e reabre (o estado continua marcado):")
    nome = alvos[0]
    _fechar(app)
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(0.8)
    app.update()
    janela = _janelas(app)[-1]

    # marca uma peca que estava desmarcada e salva
    alvo_peca = "diadema"
    caixa = _widget(janela, "peca", alvo_peca)
    if caixa is None:
        print("   FALHOU: checkbox da peca diadema nao encontrado")
        return 1
    if not _verdadeiro(caixa.get()):
        caixa.select()
    janela._salvar()
    app.update()
    time.sleep(0.4)
    app.update()

    # reabre e confere
    _fechar(app)
    app._abrir_personagem({"nome": nome})
    app.update()
    time.sleep(0.8)
    app.update()
    janela = _janelas(app)[-1]
    caixa = _widget(janela, "peca", alvo_peca)
    if not _verdadeiro(caixa.get()):
        print("   FALHOU: a peca marcada nao continuou marcada ao reabrir")
        return 1
    print(f"   {nome}: peca '{alvo_peca}' continua marcada apos salvar/reabrir  OK")

    # e o card tambem tem que mostrar
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == nome)
    print("   card:", card.dados["pecas"].get("diadema"),
          "| anel:", card.dados["acessorios"].get("anel"))

    app.destroy()
    print("\nEDICAO POR PERSONAGEM OK")
    return 0


def _coluna_real(df, logico):
    from opcoes import coluna_banco
    alvo = coluna_banco(logico)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None


def _verdadeiro(valor):
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in ("verdadeiro", "true", "1", "t", "sim")


if __name__ == "__main__":
    sys.exit(main())

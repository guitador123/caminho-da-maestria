"""
Teste da MISSAO RAPIDA (pendencia #4).

Valida:
  1. o painel abre com o botao (e com a tecla M)
  2. marcar varias missoes de uma vez e salvar (1 gravacao)
  3. o card e os contadores da tela principal atualizam na hora
  4. o MODO CARD: clicar no chip do card marca/desmarca
  5. o MODO PAINEL (padrao): o painel marca e o card continua abrindo a edicao
  6. no MODO CARD o card NAO abre a edicao
  7. o botao fica VERDE quando o modo esta ligado
  8. o check escolhe entre os dois modos (so um por vez)
  9. o ultimo personagem usado fica guardado

    python teste_missao_rapida.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from credenciais_teste import conta_teste

import customtkinter as ctk

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

import auth
from app_grandchase import (GrandChaseApp, MODO_MISSAO_CARD,
                            MODO_MISSAO_JANELA)
from card_personagem import DUNGEONS
from janela_missao_rapida import JanelaMissaoRapida


def _janelas(app):
    return [w for w in app.winfo_children() if isinstance(w, ctk.CTkToplevel)]


def _painel(app):
    for janela in _janelas(app):
        if isinstance(janela, JanelaMissaoRapida):
            return janela
    return None


def _esperar_painel(app, limite=20.0):
    """Espera a janela do painel aparecer (o Toplevel e criado em fila)."""
    fim = time.time() + limite
    while time.time() < fim:
        app.update()
        painel = _painel(app)
        if painel is not None:
            time.sleep(0.3)
            app.update()
            return painel
        time.sleep(0.15)
    print(f"   (status do app: {app.status_var.get()})")
    return None


def _fechar_painel(app):
    for janela in _janelas(app):
        if isinstance(janela, JanelaMissaoRapida):
            janela.destroy()
    app.update()


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.update()

    df = app.dfs["Semanais"]
    nomes = [str(n) for n in app.dfs["Geral"]["Nome"].tolist()]
    alvo = nomes[0]

    def estado(nome, chave):
        """Estado da missao (True = feita) — usa o proprio metodo do app."""
        return app._missoes_do_personagem(nome).get(chave)

    # --- 0) o modo comeca no PAINEL -------------------------------------
    print(f"0) modo inicial: {app.missao_modo} "
          f"(esperado '{MODO_MISSAO_JANELA}')")
    if app.missao_modo != MODO_MISSAO_JANELA:
        print("   FALHOU: o modo inicial nao e o painel")
        return 1

    # --- 1) o painel abre -----------------------------------------------
    print("\n1) abrindo o painel (botao do hero):")
    app.alternar_missao()
    app.update()
    painel = _esperar_painel(app)
    if painel is None:
        print("   FALHOU: o painel nao abriu")
        return 1
    print(f"   painel aberto | modo missao rapida = {app.missao_rapida}")

    # --- 2) marcar varias missoes de uma vez ----------------------------
    print("\n2) marcando 3 missoes de uma vez:")
    painel._selecionar(alvo)
    app.update()
    chaves = [chave for chave, _ in DUNGEONS][:3]
    originais = {chave: estado(alvo, chave) for chave in chaves}
    print(f"   originais: {originais}")
    for chave in chaves:
        painel._alternar(chave)
    print(f"   pendentes: {painel.pendentes}")
    if len(painel.pendentes) != 3:
        print("   FALHOU: as missoes nao ficaram pendentes")
        return 1
    if painel.btn_salvar.cget("state") != "normal":
        print("   FALHOU: o botao Salvar nao ficou habilitado")
        return 1

    antes_contador = app.valores_dos_cards().get("void4")
    painel._salvar()
    app.update()
    time.sleep(0.5)
    app.update()

    for chave in chaves:
        if estado(alvo, chave) == originais[chave]:
            print(f"   FALHOU: a missao {chave} nao mudou")
            return 1
    print("   -> OK: as 3 missoes mudaram no dataframe")
    print(f"   contador VOID 4: {antes_contador} -> "
          f"{app.valores_dos_cards().get('void4')}")

    # --- 3) o card mostra a mudanca --------------------------------------
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == alvo)
    esperado = {chave: (not valor) for chave, valor in originais.items()}
    print(f"   card: { {k: card.dados['semanais'].get(k) for k in chaves} }")
    for chave, valor in esperado.items():
        atual = card.dados["semanais"].get(chave)
        feito = str(atual).strip().lower() == "verdadeiro"
        if feito != valor:
            print(f"   FALHOU: o card nao pegou {chave}")
            return 1
    print("   -> OK: o card atualizou")

    # --- 4) o check escolhe o modo ---------------------------------------
    print("\n3) o check escolhe entre PAINEL e CARD:")
    app.alternar_modo_missao()
    app.update()
    time.sleep(0.3)
    app.update()
    print(f"   agora: {app.missao_modo}")
    if app.missao_modo != MODO_MISSAO_CARD:
        print("   FALHOU: o check nao mudou para o modo CARD")
        return 1
    item_caixa = app.itens_chave_missao.get("caixa")
    item_v = app.itens_chave_missao.get("v")
    if item_caixa is None or item_v is None:
        print("   FALHOU: o check nao foi desenhado")
        return 1
    img_marcada = app.canvas.itemcget(item_caixa, "image")
    estado_v = app.canvas.itemcget(item_v, "state")
    print(f"   caixa marcada (v = '{estado_v}')")
    if estado_v != "normal":
        print("   FALHOU: o check nao ficou marcado no modo CARD")
        return 1
    app.alternar_modo_missao()
    app.update()
    time.sleep(0.3)
    app.update()
    print(f"   voltou para: {app.missao_modo}")
    if app.missao_modo != MODO_MISSAO_JANELA:
        print("   FALHOU: o check nao voltou para o modo PAINEL")
        return 1
    if app.canvas.itemcget(item_v, "state") != "hidden":
        print("   FALHOU: o check continua marcado no modo PAINEL")
        return 1
    if app.canvas.itemcget(item_caixa, "image") == img_marcada:
        print("   FALHOU: a caixa do check nao mudou de imagem")
        return 1
    print("   -> OK: alterna entre os dois (so um por vez)")

    # --- 5) MODO CARD: clicar no chip do card marca ----------------------
    print("\n4) MODO CARD: clicar no chip do card marca:")
    app.alternar_modo_missao()          # para no modo CARD
    app.update()
    time.sleep(0.3)
    app.update()
    _fechar_painel(app)
    antes = estado(alvo, chaves[0])
    app.alternar_missao_rapida(chaves[0], alvo)
    app.update()
    depois = estado(alvo, chaves[0])
    print(f"   {chaves[0]}: {antes} -> {depois}")
    if antes == depois:
        print("   FALHOU: o clique no chip nao marcou a missao")
        return 1
    print("   -> OK: marcou (e o app salva em 2o plano)")

    # --- 6) no MODO CARD o card nao abre a edicao -----------------------
    print("\n5) no MODO CARD o card NAO abre a edicao:")
    card = next(c for c in app.cards_personagem if c.dados.get("nome") == alvo)
    item = None
    for cand in card._itens:
        if card.canvas.type(cand) == "text" and \
                card.canvas.itemcget(cand, "text") == str(alvo):
            item = cand
            break
    if item is None:
        print("   FALHOU: nao achei o item do nome do card")
        return 1
    canvas = card.canvas
    bbox = canvas.bbox(item)
    x = (bbox[0] + bbox[2]) / 2 - canvas.canvasx(0)
    y = (bbox[1] + bbox[3]) / 2 - canvas.canvasy(0)
    canvas.event_generate("<Button-1>", x=x, y=y)
    app.update()
    time.sleep(0.6)
    app.update()
    if _janelas(app):
        print(f"   FALHOU: abriu '{_janelas(app)[-1].nome}' mesmo no modo CARD")
        return 1
    print("   -> OK: clicar no card no modo CARD NAO abre a edicao")

    # --- 7) o botao fica VERDE quando o modo esta ligado ----------------
    print("\n6) o botao fica verde quando ligado:")
    verde = app.itens_verde.get("topo4")
    if verde is None:
        print("   FALHOU: o botao nao tem o fundo verde")
        return 1
    estado_item = app.canvas.itemcget(verde, "state")
    cor_texto = app.canvas.itemcget(app.itens_texto_botao["topo4"], "fill")
    print(f"   estado do fundo verde = {estado_item} | cor do texto = {cor_texto}")
    if estado_item != "normal":
        print("   FALHOU: o botao nao ficou verde (modo ligado)")
        return 1
    if cor_texto != "#08130d":
        print("   FALHOU: o texto do botao nao ficou escuro")
        return 1
    print("   -> OK: botao verde com texto escuro")

    app.alternar_missao()          # desliga o modo rapida
    app.update()
    time.sleep(0.3)
    app.update()
    if app.canvas.itemcget(verde, "state") != "hidden":
        print("   FALHOU: o botao continua verde com o modo desligado")
        return 1
    print("   -> OK: desliga e o verde some")

    # --- 8) fora do modo, o clique no chip abre a edicao ----------------
    print("\n7) fora do modo, o clique no chip abre a edicao:")
    app.alternar_modo_missao()          # volta para o modo PAINEL
    app.update()
    time.sleep(0.3)
    app.update()
    app.alternar_missao_rapida(chaves[0], alvo)
    app.update()
    time.sleep(0.6)
    app.update()
    if not _janelas(app):
        print("   FALHOU: nao abriu a edicao")
        return 1
    print(f"   -> OK: abriu '{_janelas(app)[-1].nome}'")
    for janela in _janelas(app):
        janela.destroy()
    app.update()

    # --- 9) no MODO PAINEL o card continua abrindo a edicao ------------
    print("\n8) no MODO PAINEL o card continua abrindo a edicao:")
    app.alternar_missao()          # liga o modo rapida (painel)
    app.update()
    time.sleep(0.6)
    app.update()
    _fechar_painel(app)
    app.alternar_missao_rapida(chaves[0], alvo)
    app.update()
    time.sleep(0.6)
    app.update()
    if not _janelas(app):
        print("   FALHOU: no modo PAINEL o card deveria abrir a edicao")
        return 1
    print(f"   -> OK: abriu '{_janelas(app)[-1].nome}'")
    for janela in _janelas(app):
        janela.destroy()
    app.update()
    app.alternar_missao()          # desliga
    app.update()

    # --- 10) o ultimo personagem fica guardado --------------------------
    print("\n9) ultimo personagem guardado:")
    app._lembrar_personagem_missao(alvo)
    app.update()
    print(f"   app.ultimo_personagem_missao = {app.ultimo_personagem_missao}")
    if app.ultimo_personagem_missao != alvo:
        print("   FALHOU: nao guardou o ultimo personagem")
        return 1

    # --- 11) restaura os valores originais ------------------------------
    print("\n10) restaurando os valores originais:")
    app.marcar_missoes(alvo, dict(originais))
    app.update()
    time.sleep(0.3)
    app.update()
    for chave, valor in originais.items():
        if estado(alvo, chave) != valor:
            print(f"   FALHOU: nao restaurou {chave}")
            return 1
    print("   -> OK")

    app.destroy()
    print("\nMISSAO RAPIDA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

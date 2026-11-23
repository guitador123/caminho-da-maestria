"""
Teste dos FILTROS (15/11).

  1) a lista vem SEMPRE do mais forte para o mais fraco (pelo Ataque Total)
  2) os filtros respondem ao CLIQUE (e mostram o CHECK do ativo)
  3) "Nao fez estas masmorras" e "Progresso incompleto"
  4) "Ordenar por Void" troca a ordenacao
  5) a ordem se atualiza em tempo real quando os dados mudam
  6) o tempo de aplicar um filtro e pequeno (sem congelar a tela)

    python teste_filtros.py
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

from app_grandchase import (GrandChaseApp, FILTRO_MAZMORRAS, FILTRO_VOID,
                            FILTRO_PROGRESSO)
from opcoes import coluna_banco

LIMITE_SEGUNDOS = 1.2   # um filtro nao pode congelar a tela


def _clicar_opcao(app, grupo, chave):
    """Clica de verdade na opcao do filtro (evento sintetico no canvas)."""
    tag = f"filtro:{grupo}:{chave}"
    itens = app.canvas.find_withtag(tag)
    if not itens:
        return False
    bbox = None
    for item in itens:
        b = app.canvas.bbox(item)
        if b and (b[2] - b[0]) > 4:
            bbox = b
            break
    if bbox is None:
        bbox = app.canvas.bbox(itens[0])
    x = (bbox[0] + bbox[2]) / 2 - app.canvas.canvasx(0)
    y = (bbox[1] + bbox[3]) / 2 - app.canvas.canvasy(0)
    app.canvas.event_generate("<Button-1>", x=x, y=y)
    app.update()
    return True


def main():
    app = GrandChaseApp(user=None, supabase=None)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.update()

    df = app.dfs["Geral"]
    nomes = [str(n) for n in df["Nome"].tolist()]

    def visiveis():
        return app._nomes_visiveis()

    # --- 1) a ordem padrao: pelo Ataque Total ----------------------------
    print("1) a lista vem do mais forte para o mais fraco (Ataque Total):")
    lista = visiveis()
    print(f"   {len(lista)} cards | {lista[:5]}")
    ataques = [app._dados_filtro(n)["ataque"] for n in lista]
    print(f"   ataques: {ataques[:5]}")
    if ataques != sorted(ataques, reverse=True):
        print("   FALHOU: a lista nao esta em ordem de Ataque Total decrescente")
        return 1
    print("   -> OK")

    # --- 2) o clique nos filtros funciona --------------------------------
    print("\n2) clicar nas opcoes do filtro:")
    chave = FILTRO_MAZMORRAS[0][0]
    if not _clicar_opcao(app, "mazmorras", chave):
        print("   FALHOU: a opcao do filtro nao foi encontrada no canvas")
        return 1
    time.sleep(0.4)
    app.update()
    if chave not in app.filtro_mazmorras:
        print("   FALHOU: o clique nao ligou o filtro")
        return 1
    print(f"   filtro 'mazmorras' = {app.filtro_mazmorras}  OK")

    tag = f"filtro:mazmorras:{chave}"
    if not app.canvas.find_withtag(tag):
        print("   FALHOU: o item do filtro sumiu")
        return 1
    print(f"   {len(app.canvas.find_withtag(tag))} itens com a tag do filtro  OK")

    _clicar_opcao(app, "mazmorras", chave)
    time.sleep(0.4)
    app.update()
    if chave in app.filtro_mazmorras:
        print("   FALHOU: o clique nao desligou o filtro")
        return 1
    print("   -> OK: liga e desliga")

    # --- 3) "ordenar por Void" troca a ordenacao -------------------------
    print("\n3) 'Ordenar por Void' troca a ordenacao:")
    _clicar_opcao(app, "ordem", FILTRO_VOID[0][0])
    time.sleep(0.4)
    app.update()
    if FILTRO_VOID[0][0] not in app.filtro_ordem_void:
        print("   FALHOU: o filtro de Void nao ligou")
        return 1
    lista = visiveis()
    voids = [app._dados_filtro(n)["vazio_uni"] for n in lista]
    print(f"   por Vazio Unificado: {voids[:6]}")
    if voids != sorted(voids, reverse=True):
        print("   FALHOU: a ordem por Void nao foi aplicada")
        return 1
    print("   -> OK")
    _clicar_opcao(app, "ordem", FILTRO_VOID[0][0])
    time.sleep(0.4)
    app.update()

    # volta a ordenar pelo Ataque Total
    lista = visiveis()
    ataques = [app._dados_filtro(n)["ataque"] for n in lista]
    if ataques != sorted(ataques, reverse=True):
        print("   FALHOU: nao voltou a ordenar pelo Ataque Total")
        return 1
    print("   -> OK: volta para o Ataque Total")

    # --- 4) "nao fez estas masmorras" e "progresso incompleto" ----------
    print("\n4) 'nao fez estas masmorras' e 'progresso incompleto':")
    df_sem = app.dfs["Semanais"]
    coluna = None
    for c in df_sem.columns:
        if coluna_banco(c) == coluna_banco(FILTRO_MAZMORRAS[0][0]):
            coluna = c
            break
    marcados = nomes[:2]
    for nome in marcados:
        df_sem.loc[df_sem["Nome"].astype(str) == nome, coluna] = "Verdadeiro"
    app.filtro_mazmorras.add(FILTRO_MAZMORRAS[0][0])
    app._aplicar_filtros()
    app.update()
    lista = visiveis()
    print(f"   marcados: {marcados} | nao aparecem: "
          f"{[n for n in marcados if n not in lista]}")
    if any(n in lista for n in marcados):
        print("   FALHOU: quem ja concluiu a mazmorra continua na lista")
        return 1
    app.filtro_mazmorras.clear()
    app._aplicar_filtros()

    app.filtro_progresso = {"despertar"}
    app._aplicar_filtros()
    app.update()
    lista = visiveis()
    errados = [n for n in lista if app._dados_filtro(n)["despertar"]]
    print(f"   {len(lista)} cards | com despertar completo (erro): {errados}")
    if errados:
        print("   FALHOU: entrou alguem que ja completou o despertar")
        return 1
    app.filtro_progresso.clear()
    app._aplicar_filtros()
    app.update()
    print("   -> OK")

    # --- 5) o tempo de aplicar um filtro (sem congelar) ------------------
    print("\n5) tempo para aplicar um filtro (sem congelar a tela):")
    pior = 0
    for grupo, chave_t in (("mazmorras", FILTRO_MAZMORRAS[1][0]),
                           ("progresso", FILTRO_PROGRESSO[1][0]),
                           ("ordem", FILTRO_VOID[0][0])):
        inicio = time.time()
        app._alternar_filtro(grupo, chave_t)
        app.update()
        decorrido = time.time() - inicio
        pior = max(pior, decorrido)
        print(f"   filtro '{grupo}' -> {decorrido:.3f}s")
        app._alternar_filtro(grupo, chave_t)
        app.update()
    print(f"   pior tempo: {pior:.3f}s (limite {LIMITE_SEGUNDOS}s)")
    if pior > LIMITE_SEGUNDOS:
        print("   FALHOU: o filtro congela a tela")
        return 1
    print("   -> OK: sem congelamento")

    # --- 6) a ordem se atualiza em tempo real ----------------------------
    print("\n6) a ordem se atualiza quando os dados mudam:")
    antes = visiveis()
    ultimo = antes[-1]
    df_local = app.dfs["Geral"]
    mask = df_local["Nome"].astype(str) == ultimo
    for coluna, valor in (("Poder", 999999999), ("Vazio Uni.", 999999),
                           ("Vazio Apo.", 999999)):
        real = None
        for c in df_local.columns:
            if coluna_banco(c) == coluna_banco(coluna):
                real = c
                break
        if real:
            df_local.loc[mask, real] = valor
    app._aplicar_filtros()
    app.update()
    depois = visiveis()
    print(f"   {ultimo}: posicao {antes.index(ultimo)} -> {depois.index(ultimo)}")
    if depois.index(ultimo) != 0:
        print("   FALHOU: a ordem nao se atualizou em tempo real")
        return 1
    print("   -> OK")

    app.destroy()
    print("\nFILTROS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

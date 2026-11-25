"""
Status do personagem (item 15.1): Ataque, Ataque Especial e os 3 %.

    python teste_status_personagem.py [email] [senha]

Valida (Supabase real, restaura no fim):
  1. as 5 colunas existem no banco (sql/status_personagem.sql)
  2. a janela do personagem tem os 5 campos e a soma "no milhar"
  3. o card mostra a soma ao lado do Ataque Total e a faixa com os status
     (ao vivo, antes de salvar)
  4. salvar grava no banco com 2 casas decimais, cortando (35,259 -> 35.25)
  5. recarregar do banco mostra o mesmo card
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import customtkinter as ctk

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from credenciais_teste import conta_teste
from opcoes import coluna_banco

# os messagebox bloqueiam o script
import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True

COLUNAS = ["ataque", "ataque_especial", "critico", "dano_critico",
           "dano_costas"]
DIGITADO = {"ataque": "20.000", "ataque_especial": "25990",
            "critico": "35,259", "dano_critico": "180.5",
            "dano_costas": "30"}
NO_BANCO = {"ataque": 20000, "ataque_especial": 25990, "critico": 35.25,
            "dano_critico": 180.5, "dano_costas": 30}
NO_CARD = ["4.5", "20k", "25,9k", "35,25%", "180,5%", "30%"]


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


def _textos_do_card(app, nome):
    card = next(c for c in app.cards_personagem
                if c.dados.get("nome") == nome)
    return {str(app.canvas.itemcget(i, "text")) for i in card._itens
            if app.canvas.type(i) == "text"}


def _do_banco(sb, user_id, nome):
    linha = next(p for p in db.carregar_personagens(sb, user_id)
                 if p["Nome"] == nome)
    return {c: linha.get(c) for c in COLUNAS}


def _iguais(lido, esperado):
    return all(abs(float(lido.get(c) or 0) - float(esperado[c])) < 1e-9
               for c in COLUNAS)


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    print("1) colunas no banco")
    faltam = [c for c in COLUNAS
              if c not in db._extras(sb, "personagens")]
    if faltam:
        print(f"   FALHOU: faltam {faltam} (rode sql/status_personagem.sql)")
        return 1
    print("   OK: as 5 colunas existem")

    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 1.5)
    nome = app.cards_personagem[0].dados["nome"]
    originais = _do_banco(sb, user.id, nome)
    print(f"   personagem: {nome} | originais: {originais}")
    falhas = []

    try:
        print("2) janela do personagem")
        app._abrir_personagem({"nome": nome})
        _esperar(app, 1.0)
        janela = [w for w in app.winfo_children()
                  if isinstance(w, ctk.CTkToplevel)][-1]
        campos = {}
        for (tipo, chave), item in janela._linhas.items():
            if tipo == "geral" and isinstance(item, tuple):
                campos[coluna_banco(chave)] = item[0]
        for coluna, texto in DIGITADO.items():
            entrada = campos.get(coluna_banco(coluna))
            if entrada is None:
                falhas.append(f"campo {coluna} nao esta na janela")
                continue
            entrada.delete(0, "end")
            entrada.insert(0, texto)
        janela._propagar()
        _esperar(app, 0.3)
        soma = janela._rotulo_soma.cget("text")
        print(f"   soma na janela: {soma}")
        if soma != "4.5":
            falhas.append(f"soma na janela = {soma} (esperado 4.5)")

        print("3) card ao vivo")
        textos = _textos_do_card(app, nome)
        faltando = [t for t in NO_CARD if t not in textos]
        print(f"   no card: {[t for t in NO_CARD if t in textos]}")
        if faltando:
            falhas.append(f"card sem {faltando}")

        print("4) salvar no Supabase")
        janela._salvar()
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        lido = _do_banco(sb, user.id, nome)
        print(f"   no banco: {lido}")
        if not _iguais(lido, NO_BANCO):
            falhas.append(f"banco = {lido} (esperado {NO_BANCO})")

        print("5) recarregar do banco")
        app.carregar_do_supabase()
        _esperar(app, 1.0)
        textos = _textos_do_card(app, nome)
        faltando = [t for t in NO_CARD if t not in textos]
        if faltando:
            falhas.append(f"depois de recarregar, card sem {faltando}")
        else:
            print("   OK: o card voltou igual")
    finally:
        # restaura os valores originais
        df = app.dfs["Geral"]
        mascara = df["Nome"].astype(str) == str(nome)
        for coluna in COLUNAS:
            real = next((c for c in df.columns
                         if coluna_banco(c) == coluna_banco(coluna)), None)
            if real:
                df.loc[mascara, real] = originais[coluna] or 0
        app._marcar_modificado()
        app.salvar_supabase()
        _esperar_salvamento(app)
        lido = _do_banco(sb, user.id, nome)
        restaurado = _iguais(lido, {c: originais[c] or 0 for c in COLUNAS})
        print(f"6) restaurado: {lido}")
        if not restaurado:
            falhas.append("nao restaurou os valores originais")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nSTATUS DO PERSONAGEM OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

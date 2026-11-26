"""
Void na Missao Rapida: andares 1F/2F/3F (item 17).

    python teste_void_andares.py [email] [senha] [--print caminho.png]

Valida (Supabase real, restaura no fim):
  1. as colunas do andar existem (sql/void_andares.sql)
  2. MODO CARD: clicar no chip do Void (1, 2 e 3) abre a pergunta; a
     tecla "3" escolhe 3F -> marca, soma +10 no Void Unificado e salva
  3. cancelar (Esc) nao marca nem soma
  4. desmarcar no card desfaz o +10
  5. MODO PAINEL: marcar o Void 4 com 2F NAO soma antes do "Salvar";
     ao salvar soma +8 no Void Apocalipse e grava o andar no banco
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp
from config_app import MODO_MISSAO_CARD, MODO_MISSAO_JANELA
from credenciais_teste import conta_teste
from dados_app import _verdadeiro
from janela_andares import JanelaAndares
from janela_missao_rapida import JanelaMissaoRapida

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.askyesno = lambda *a, **k: True


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


def _banco(sb, user_id, nome):
    pers = db.carregar_personagens(sb, user_id)
    geral = next(p for p in pers if p["Nome"] == nome)
    sem = next(s for s in db.carregar_semanais(sb, pers) if s["Nome"] == nome)
    return {"vazio_uni": geral.get("vazio_uni"),
            "vazio_apo": geral.get("vazio_apo"),
            # (o banco devolve "Falso"/"Verdadeiro": vira bool)
            "void_123": _verdadeiro(sem.get("void_123")),
            "void_4": _verdadeiro(sem.get("void_4")),
            "void123_andar": sem.get("void123_andar") or "",
            "void4_andar": sem.get("void4_andar") or ""}


def _janelas(app, classe):
    return [w for w in app.winfo_children()
            if isinstance(w, classe) and w.winfo_exists()]


def _tecla(janela, tecla):
    janela.focus_force()
    janela.update()
    janela.event_generate(f"<KeyPress-{tecla}>")


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
    faltam = [c for c in ("void123_andar", "void4_andar")
              if c not in db._extras(sb, "semanais")]
    if faltam:
        print(f"   FALHOU: faltam {faltam} (rode sql/void_andares.sql)")
        return 1
    print("   OK")

    app = GrandChaseApp(user=user, supabase=sb)
    _esperar(app, 2.0)
    nome = app.cards_personagem[0].dados["nome"]
    original = _banco(sb, user.id, nome)
    print(f"   personagem: {nome} | original: {original}")
    falhas = []

    try:
        # comeca com os dois Void desmarcados
        app.marcar_missoes(nome, {"void123": False, "void4": False})
        _esperar_salvamento(app)
        base = _banco(sb, user.id, nome)
        uni, apo = int(base["vazio_uni"] or 0), int(base["vazio_apo"] or 0)

        print("2) modo card: Void (1, 2 e 3) com 3F")
        app.missao_rapida, app.missao_modo = True, MODO_MISSAO_CARD
        app.alternar_missao_rapida("void123", nome)
        _esperar(app, 0.6)
        pergunta = _janelas(app, JanelaAndares)
        if not pergunta:
            falhas.append("o card nao perguntou os andares")
            return 1
        if imprimir:
            from PIL import ImageGrab
            pergunta[-1]._mostrar("3F")
            pergunta[-1].attributes("-topmost", True)
            _esperar(app, 0.5)
            j = pergunta[-1]
            x, y = j.winfo_rootx(), j.winfo_rooty()
            ImageGrab.grab((x, y, x + j.winfo_width(), y + j.winfo_height()),
                           all_screens=True).save(imprimir)
        _tecla(pergunta[-1], "3")
        _esperar(app, 0.3)
        if not _esperar_salvamento(app):
            falhas.append("o salvamento nao terminou")
        agora = _banco(sb, user.id, nome)
        print(f"   banco: Void Unificado {uni} -> {agora['vazio_uni']} | "
              f"andar {agora['void123_andar']!r}")
        if agora["vazio_uni"] != uni + 10 or not agora["void_123"]:
            falhas.append(f"3F nao somou +10: {agora}")
        if not agora["void123_andar"].startswith("3F|"):
            falhas.append(f"andar nao gravado: {agora['void123_andar']!r}")

        print("3) cancelar nao marca")
        app.alternar_missao_rapida("void4", nome)
        _esperar(app, 0.6)
        _tecla(_janelas(app, JanelaAndares)[-1], "Escape")
        _esperar(app, 0.5)
        if _janelas(app, JanelaAndares):
            falhas.append("Esc nao fechou a pergunta")
        if app._missoes_do_personagem(nome).get("void4"):
            falhas.append("cancelar marcou o Void 4")

        print("4) desmarcar no card desfaz")
        app.alternar_missao_rapida("void123", nome)
        _esperar(app, 0.3)
        _esperar_salvamento(app)
        agora = _banco(sb, user.id, nome)
        print(f"   Void Unificado: {agora['vazio_uni']} (esperado {uni})")
        if agora["vazio_uni"] != uni or agora["void_123"]:
            falhas.append(f"desmarcar nao desfez: {agora}")

        print("5) modo painel: Void 4 com 2F so soma no Salvar")
        app.missao_rapida, app.missao_modo = True, MODO_MISSAO_JANELA
        painel = JanelaMissaoRapida(app)
        _esperar(app, 0.8)
        painel._selecionar(nome)
        painel._alternar("void4")
        _esperar(app, 0.6)
        _tecla(_janelas(app, JanelaAndares)[-1], "2")
        _esperar(app, 0.3)
        _rotulo, antes_salvar = app.contador_void(nome, "void4")
        print(f"   antes do Salvar: {antes_salvar} | botao: "
              f"{painel._botoes_missao['void4'].cget('text')!r}")
        if antes_salvar != apo:
            falhas.append("o painel somou antes do Salvar")
        if "2F +8" not in painel._botoes_missao["void4"].cget("text"):
            falhas.append("o botao nao mostra o 2F +8")
        painel._salvar()
        _esperar(app, 0.3)
        _esperar_salvamento(app)
        agora = _banco(sb, user.id, nome)
        print(f"   banco: Void Apocalipse {apo} -> {agora['vazio_apo']} | "
              f"andar {agora['void4_andar']!r}")
        if agora["vazio_apo"] != apo + 8 or not agora["void_4"]:
            falhas.append(f"o Salvar nao somou +8: {agora}")
    finally:
        # restaura tudo como estava
        app.missao_rapida, app.missao_modo = False, MODO_MISSAO_JANELA
        from opcoes import coluna_banco
        geral, sem = app.dfs["Geral"], app.dfs["Semanais"]
        mg = geral["Nome"].astype(str) == str(nome)
        ms = sem["Nome"].astype(str) == str(nome)
        for df, mascara, chaves in (
                (geral, mg, ("vazio_uni", "vazio_apo")),
                (sem, ms, ("void_123", "void_4", "void123_andar",
                           "void4_andar"))):
            for chave in chaves:
                coluna = next((c for c in df.columns
                               if coluna_banco(c) == coluna_banco(chave)), None)
                if coluna is None:
                    continue
                valor = original[chave]
                if chave.startswith("void_"):
                    valor = "Verdadeiro" if valor else "Falso"
                if df[coluna].dtype != object:
                    df[coluna] = df[coluna].astype(object)
                df.loc[mascara, coluna] = valor
        app._marcar_modificado()
        app.salvar_supabase()
        _esperar_salvamento(app)
        volta = _banco(sb, user.id, nome)
        print(f"6) restaurado: {volta == original}")
        if volta != original:
            falhas.append(f"nao restaurou: {volta} != {original}")
        app.destroy()

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nVOID NA MISSAO RAPIDA OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

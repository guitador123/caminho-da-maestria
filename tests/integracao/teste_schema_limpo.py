"""
Teste do SCHEMA do banco (pendencia #10: limpar a coluna antiga).

Confirma que:
  1. a coluna antiga `fragmentos_facis` NAO existe mais;
  2. nenhuma tabela tem coluna fora do que o app conhece (sem sobras);
  3. o app carrega e salva sem reclamar de "colunas fora do banco".

    python teste_schema_limpo.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import time
from credenciais_teste import conta_teste

import tkinter.messagebox as mb
mb.showinfo = lambda *a, **k: None
mb.showwarning = lambda *a, **k: None
mb.showerror = lambda *a, **k: print("!!! showerror:", a)

import auth
import supabase_db as db
from app_grandchase import GrandChaseApp

# colunas que o app aceita em cada tabela (alem das de controle)
PERMITIDAS = {
    "personagens": {"id", "user_id", "updated_at", "nivel_chaser"},
    "pecas_void": {"id", "character_id", "updated_at"},
    "acessorios_titulo": {"id", "character_id", "updated_at"},
    "semanais": {"id", "character_id", "updated_at",
                 "torre_das_ilusoes", db.TORRE_SEMANAL},
}

COLUNA_ANTIGA = "fragmentos_facis"


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    uid = user.id

    # --- 1) a coluna antiga nao existe ------------------------------------
    print("1) a coluna antiga esta removida?")
    try:
        sb.table("user_characters").select(COLUNA_ANTIGA).limit(1).execute()
        print(f"   FALHOU: '{COLUNA_ANTIGA}' AINDA EXISTE")
        return 1
    except Exception:
        print(f"   -> OK: '{COLUNA_ANTIGA}' nao existe mais")

    # --- 2) nenhuma coluna fora do que o app conhece ---------------------
    print("\n2) sobrando coluna no banco?")
    problemas = 0
    for logica, tabela in db.TABELAS.items():
        if logica == "personagens":
            consulta = sb.table(tabela).select("*").eq("user_id", uid)
        else:
            consulta = sb.table(tabela).select("*")
        try:
            dados = consulta.limit(1).execute().data or []
        except Exception as erro:
            print(f"   {tabela}: FALHOU ao ler ({str(erro)[:80]})")
            problemas += 1
            continue
        if not dados:
            print(f"   {tabela}: (vazia)")
            continue
        colunas = set(dados[0].keys())
        desconhecidas = sorted(colunas - set(db.COLUNAS[logica])
                               - PERMITIDAS[logica])
        if desconhecidas:
            print(f"   {tabela}: FALHOU -> colunas fora: {desconhecidas}")
            problemas += 1
        else:
            print(f"   {tabela}: OK ({len(colunas)} colunas)")
    if problemas:
        return 1

    # --- 3) o app carrega e salva sem reclamar ---------------------------
    print("\n3) o app carrega e salva sem 'colunas fora do banco':")
    app = GrandChaseApp(user=user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.2)
    app.update()

    app._marcar_modificado()
    app.salvar_supabase()
    for _ in range(400):
        app.update()
        time.sleep(0.05)
        if not app._salvando:
            break
    for _ in range(20):
        app.update()
        time.sleep(0.03)
    status = app.status_var.get()
    print(f"   status: {status}")
    if "fora do banco" in status:
        print("   FALHOU: o app reclamou de coluna fora do banco")
        return 1
    if "Erro" in status:
        print("   FALHOU: erro ao salvar")
        return 1
    print("   -> OK")

    app.destroy()
    print("\nSCHEMA LIMPO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

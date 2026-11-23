# -*- coding: utf-8 -*-
"""
Teste do RLS (Row Level Security) visto DE FORA, com a chave publica.

A chave publishable vai dentro do app (qualquer um pode extrai-la), entao
o RLS e a UNICA coisa que impede um usuario de mexer nos dados de outro.
Este teste confere, sem estragar nada:

  1) SEM LOGIN (anon): nao le nenhuma linha e nao consegue inserir;
  2) COM LOGIN (conta de teste): so enxerga as PROPRIAS linhas, mesmo
     pedindo a tabela inteira sem filtro;
  3) COM LOGIN: nao consegue inserir linha em nome de OUTRO usuario
     (nem filha apontando para personagem que nao e dele).

Se alguma escrita indevida passar, o teste apaga a linha na hora e
reprova.

    python teste_rls.py [email] [senha]
"""

import sys
import uuid

from supabase import create_client

import auth
from credenciais_teste import conta_teste
from supabase_db import SUPABASE_KEY, SUPABASE_URL, TABELAS

FILHAS = [TABELAS[k] for k in ("pecas_void", "acessorios_titulo", "semanais")]
TODAS = ["user_characters", "user_profiles"] + FILHAS

falhas = []


def checar(ok, texto):
    print(("   OK  " if ok else "   FALHOU  ") + texto)
    if not ok:
        falhas.append(texto)


def _codigo(erro):
    """O codigo do Postgres/PostgREST de um erro (42501 = RLS)."""
    for atributo in ("code",):
        valor = getattr(erro, atributo, None)
        if valor:
            return str(valor)
    texto = str(erro)
    for codigo in ("42501", "23503", "23502", "PGRST"):
        if codigo in texto:
            return codigo
    return texto[:60]


def tentar_inserir(cliente, tabela, linha, descricao):
    """Tenta uma escrita que o RLS DEVE barrar (e desfaz se passar)."""
    try:
        resposta = cliente.table(tabela).insert(linha).execute()
    except Exception as erro:
        codigo = _codigo(erro)
        # 42501 = violou a politica de RLS (o esperado). Outro erro
        # (ex.: chave estrangeira) tambem barra, mas nao prova o RLS.
        if codigo == "42501":
            checar(True, f"{descricao}: barrado pelo RLS (42501)")
        else:
            checar(True, f"{descricao}: barrado (codigo {codigo}, "
                         "nao foi o RLS: confira a policy de insert)")
        return
    # passou: desfaz e reprova
    for criada in resposta.data or []:
        try:
            cliente.table(tabela).delete().eq("id", criada["id"]).execute()
        except Exception:
            pass
    checar(False, f"{descricao}: a escrita PASSOU (linha apagada em seguida)")


def main(argv):
    email, senha = conta_teste(argv)

    print("1) SEM LOGIN (so a chave publica):")
    anon = create_client(SUPABASE_URL, SUPABASE_KEY)
    for tabela in TODAS:
        try:
            linhas = anon.table(tabela).select("*").limit(5).execute().data
            checar(not linhas, f"anon le {tabela}: {len(linhas)} linha(s)")
        except Exception as erro:
            checar(True, f"anon le {tabela}: negado ({_codigo(erro)})")
    tentar_inserir(anon, "user_characters",
                   {"user_id": str(uuid.uuid4()), "character_name": "Elesis"},
                   "anon insere personagem")

    print("\n2) COM LOGIN: so as proprias linhas (tabela inteira, sem filtro):")
    sb, resposta = auth.login(email, senha)
    uid = resposta.user.id
    meus = sb.table("user_characters").select("id,user_id").execute().data
    ids_meus = {p["id"] for p in meus}
    alheios = [p for p in meus if p["user_id"] != uid]
    checar(bool(meus) and not alheios,
           f"user_characters: {len(meus)} linha(s), {len(alheios)} de outro usuario")

    perfis = sb.table("user_profiles").select("id").execute().data
    alheios = [p for p in perfis if p["id"] != uid]
    checar(not alheios,
           f"user_profiles: {len(perfis)} linha(s), {len(alheios)} de outro usuario")

    for tabela in FILHAS:
        linhas = sb.table(tabela).select("id,character_id").execute().data
        alheios = [l for l in linhas if l["character_id"] not in ids_meus]
        checar(not alheios,
               f"{tabela}: {len(linhas)} linha(s), {len(alheios)} de personagem alheio")

    print("\n3) COM LOGIN: escrever em nome de outro usuario:")
    outro = str(uuid.uuid4())
    tentar_inserir(sb, "user_characters",
                   {"user_id": outro, "character_name": "Elesis"},
                   "personagem com user_id de outro")
    for tabela in FILHAS:
        tentar_inserir(sb, tabela, {"character_id": str(uuid.uuid4())},
                       f"{tabela} apontando para personagem alheio")
    try:
        sb.auth.sign_out()
    except Exception:
        pass

    print()
    if falhas:
        print(f"RLS COM PROBLEMA ({len(falhas)}):")
        for texto in falhas:
            print("  -", texto)
        return 1
    print("RLS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

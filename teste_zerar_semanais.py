# -*- coding: utf-8 -*-
"""
Teste da PROTECAO da limpeza semanal (`public.zerar_semanais()`).

A funcao e SECURITY DEFINER (ignora o RLS) e zera as missoes semanais de
TODAS as contas. Ela so pode ser chamada pelo pg_cron (postgres) e pelo
service_role. Este teste confere que um usuario COMUM (e o anon) recebem
"permissao negada" ao chamar o RPC.

ATENCAO: se a protecao estiver QUEBRADA, a chamada do teste ZERA as
semanais da guilda inteira. Por isso ele so roda com --confirmar, e so
depois de aplicar o sql/corrigir_permissoes.sql (confira antes, no SQL
Editor, o bloco 1 daquele arquivo).

    python teste_zerar_semanais.py --confirmar [email] [senha]

O funcionamento da limpeza em si se confere no SQL Editor:
    sql/zerar_semanais_verificar.sql
"""

import sys

from supabase import create_client

from credenciais_teste import conta_teste


def _negado(cliente):
    """True se o RPC foi recusado por permissao (42501)."""
    try:
        cliente.rpc("zerar_semanais").execute()
    except Exception as erro:
        texto = f"{getattr(erro, 'code', '')} {erro}"
        return "42501" in texto or "permission denied" in texto.lower()
    return False


def main(argv):
    if "--confirmar" not in argv:
        print(__doc__)
        print("Nao rodei: falta --confirmar (leia o aviso acima).")
        return 1
    argv = [a for a in argv if a != "--confirmar"]
    email, senha = conta_teste(argv)

    import auth
    from supabase_db import SUPABASE_KEY, SUPABASE_URL

    falhas = []
    print("1) sem login (anon) chamando zerar_semanais():")
    if _negado(create_client(SUPABASE_URL, SUPABASE_KEY)):
        print("   OK  permissao negada")
    else:
        falhas.append("o anon conseguiu chamar a funcao")

    print("2) usuario comum chamando zerar_semanais():")
    sb, _resp = auth.login(email, senha)
    if _negado(sb):
        print("   OK  permissao negada")
    else:
        falhas.append("um usuario comum conseguiu chamar a funcao")

    print()
    if falhas:
        print("FALHOU (rode o sql/corrigir_permissoes.sql):")
        for texto in falhas:
            print("   -", texto)
        return 1
    print("LIMPEZA SEMANAL PROTEGIDA (so o pg_cron/service_role chamam)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

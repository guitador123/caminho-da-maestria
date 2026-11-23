# -*- coding: utf-8 -*-
"""
Teste da limpeza semanal (a funcao `public.zerar_semanais()` do Supabase).

Faz o ciclo completo na conta de teste:
  1. marca as 7 missoes semanais como true em todas as linhas;
  2. chama a funcao do banco (a mesma que o pg_cron roda);
  3. confere que tudo voltou para false;
  4. chama de novo e confere que devolve 0 (e idempotente).

    python teste_zerar_semanais.py [email] [senha]

Se a funcao nao existir (ainda nao rodou o SQL), o teste avisa e
devolve 1 (sem quebrar).
"""

import os
import sys
from credenciais_teste import conta_teste

COLUNAS = ["fornalha_infernal", "altar_da_runha", "torre_das_ilusoes_semanal",
           "void_123", "void_4", "caminho_abissal", "terra_do_julgamento"]


def _valor(resultado):
    """O retorno do RPC: um escalar (ou uma lista com um escalar)."""
    dados = resultado.data
    if isinstance(dados, list):
        return dados[0] if dados else None
    return dados


def main(argv):
    email, senha = conta_teste(argv)

    import auth

    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    print("logado:", resp.user.id)

    def ativas():
        linhas = sb.table("user_semanais").select("*").execute().data or []
        return ({c: sum(1 for l in linhas if l.get(c)) for c in COLUNAS},
                len(linhas))

    # 1) a funcao existe?
    print("\n1) a funcao public.zerar_semanais() existe?")
    try:
        sb.rpc("zerar_semanais").execute()
    except Exception as erro:
        print(f"   FALHOU: {str(erro)[:200]}")
        print("   rode o SQL: sql/zerar_semanais_pg_cron.sql")
        return 1
    print("   OK (respondeu)")

    # 2) marca tudo
    print("\n2) marcando as 7 missoes como true...")
    for coluna in COLUNAS:
        sb.table("user_semanais").update({coluna: True}).eq(coluna, False).execute()
    antes, total = ativas()
    print(f"   {antes} (total de linhas: {total})")
    if not any(antes.values()):
        print("   FALHOU: nao consegui marcar nada")
        return 1

    # 3) a funcao zera
    print("\n3) chamando a funcao do banco...")
    resultado = sb.rpc("zerar_semanais").execute()
    devolvido = _valor(resultado)
    print(f"   devolveu: {devolvido}")

    depois, _ = ativas()
    print(f"   depois: {depois}")

    # 4) idempotencia
    print("\n4) chamando de novo (tem que devolver 0)...")
    resultado2 = sb.rpc("zerar_semanais").execute()
    devolvido2 = _valor(resultado2)
    print(f"   devolveu: {devolvido2}")

    print()
    problemas = []
    if any(depois.values()):
        problemas.append("sobrou marcacao depois da limpeza")
    if devolvido2 not in (0, None):
        problemas.append(f"a segunda chamada devolveu {devolvido2} (esperado 0)")
    if problemas:
        print("FALHOU:")
        for problema in problemas:
            print("   -", problema)
        return 1

    print("LIMPEZA SEMANAL OK (marcou -> zerou -> idempotente)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

# -*- coding: utf-8 -*-
"""
Teste dos filtros de dungeon SEMANAL ("Nao fez estas masmorras
semanais").

O bug: as opcoes do filtro usavam as chaves COM underscore
("torre_das_ilusoes", "caminho_abissal") e os dados usam as chaves
NORMALIZADAS ("torredasilusoes", "caminhoabissal") -> a opcao nunca era
encontrada e o filtro nao filtrava nada (mostrava todos os cards).

O teste marca cada dungeon de um personagem no banco e confere que o
filtro esconde justamente esse personagem.

    python teste_filtro_dungeons.py [email] [senha]
"""

import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import auth  # noqa
import supabase_db as db  # noqa
from app_grandchase import GrandChaseApp  # noqa

# (chave do filtro, coluna no banco)
OPCOES = [
    ("torredasilusoes", "torre_das_ilusoes_semanal"),
    ("caminhoabissal", "caminho_abissal"),
    ("void123", "void_123"),
    ("void4", "void_4"),
]


def main(argv):
    email = argv[1] if len(argv) > 1 else "teste@teste.com"
    senha = argv[2] if len(argv) > 2 else "testeteste"

    sb, resp = auth.login(email, senha)
    if getattr(resp, "user", None) is None:
        print("FALHA NO LOGIN")
        return 1
    user_id = resp.user.id

    personagens = db.carregar_personagens(sb, user_id)
    if not personagens:
        print("FALHOU: a conta nao tem personagens")
        return 1
    alvo = personagens[0]
    alvo_id = alvo.get("id")
    nome_alvo = (alvo.get("Nome") or alvo.get("character_name")
                 or alvo.get("nome") or "")
    print(f"personagem de teste: {nome_alvo!r}")

    linha = (sb.table("user_semanais").select("*")
             .eq("character_id", alvo_id).limit(1).execute())
    if not linha.data:
        print("FALHOU: nao achei a linha semanal do personagem")
        return 1
    id_semanal = linha.data[0].get("id")

    app = GrandChaseApp(user=resp.user, supabase=sb)
    app.update_idletasks()
    app.update()
    time.sleep(1.5)
    app.update()

    nomes = [str(n) for n in app.dfs["Geral"]["Nome"].tolist()]
    erros = []

    for chave_filtro, coluna_banco in OPCOES:
        print(f"\n--- {chave_filtro} (coluna {coluna_banco}) ---")
        antes = (sb.table("user_semanais").select(coluna_banco)
                 .eq("id", id_semanal).execute().data or [{}])[0].get(coluna_banco)
        sb.table("user_semanais").update({coluna_banco: True}).eq("id", id_semanal).execute()

        try:
            # recarrega os dados do banco (o app so carrega na abertura)
            app.carregar_do_supabase()
            app.update()
            time.sleep(0.4)
            app.update()

            # o card conta a dungeon como feita?
            dados = app._dados_filtro(nome_alvo)
            feito = (dados.get("mazmorras") or {}).get(chave_filtro)
            print(f"   mazmorras[{chave_filtro!r}] = {feito}")
            if not feito:
                erros.append(f"{chave_filtro}: o card nao contou a dungeon")

            # o filtro esconde quem ja fez?
            app.filtro_mazmorras = {chave_filtro}
            visiveis = app._nomes_visiveis()
            print(f"   visiveis com o filtro: {len(visiveis)} de {len(nomes)}")
            if nome_alvo in visiveis:
                erros.append(f"{chave_filtro}: o filtro NAO escondeu quem ja fez")
            else:
                print("   -> escondeu quem ja fez (OK)")

            # sem o filtro, ele volta?
            app.filtro_mazmorras = set()
            if nome_alvo not in app._nomes_visiveis():
                erros.append(f"{chave_filtro}: o personagem sumiu sem o filtro")
        finally:
            sb.table("user_semanais").update({coluna_banco: antes}).eq("id", id_semanal).execute()
            print(f"   (valor restaurado: {antes})")

    app.destroy()

    if erros:
        print("\nFALHOU:")
        for erro in erros:
            print("   -", erro)
        return 1
    print("\nFILTROS DE DUNGEON OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

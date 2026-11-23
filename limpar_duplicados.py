"""
Limpeza pontual: remove linhas duplicadas das tabelas filhas (um personagem
nao pode ter mais de uma linha em user_pecas_void / user_acessorios_titulo /
user_semanais).

    python limpar_duplicados.py [email] [senha]
"""

import sys
from collections import Counter
from credenciais_teste import conta_teste

import auth
import supabase_db as db

TABELAS = {
    "pecas_void": "user_pecas_void",
    "acessorios_titulo": "user_acessorios_titulo",
    "semanais": "user_semanais",
}


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    uid = resp.user.id
    personagens = db.carregar_personagens(sb, uid)
    print(f"personagens: {len(personagens)}")

    total_removidos = 0
    for logica, tabela in TABELAS.items():
        resp = sb.table(tabela).select("id,character_id").execute()
        linhas = resp.data or []
        contagem = Counter(l.get("character_id") for l in linhas)
        duplicados = [cid for cid, q in contagem.items() if q > 1]

        for cid in duplicados:
            ids = [l["id"] for l in linhas if l.get("character_id") == cid]
            # mantem o mais recente (o id maior costuma ser o ultimo insert)
            for id_antigo in ids[:-1]:
                sb.table(tabela).delete().eq("id", id_antigo).execute()
                total_removidos += 1
            print(f"  {tabela}: {len(ids)} linhas -> 1 (character_id {cid[:8]}...)")

        # e apaga as linhas orfas (character_id sem personagem)
        orfas = [l for l in linhas if l.get("character_id") not in
                 {p.get("id") for p in personagens}]
        for l in orfas:
            sb.table(tabela).delete().eq("id", l["id"]).execute()
            total_removidos += 1
            print(f"  {tabela}: removida linha orfa {l['id'][:8]}...")

    print(f"\ntotal de linhas removidas: {total_removidos}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

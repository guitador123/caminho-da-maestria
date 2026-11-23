"""
Teste dos campos novos dos personagens (Supabase real, nao destrutivo).

    python teste_campos_novos.py [email] [senha]

Valida:
  1. as colunas novas existem e sao lidas
  2. o app nao acusa "coluna fora do banco"
  3. ida e volta: grava -> le -> restaura
"""

import sys
from credenciais_teste import conta_teste

import auth
import supabase_db as db
from opcoes import coluna_banco

CAMPOS = ["nucleos_dimensionais", "fragmento_vazio_disperso",
           "libertacao_nucleos", "libertacao_epicos"]


def main(argv):
    email, senha = conta_teste(argv)

    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1

    print("1) colunas reconhecidas pela camada de dados")
    permitidas = db.colunas_salvaveis(sb, "personagens")
    for coluna in CAMPOS:
        ok = coluna_banco(coluna) in permitidas
        print(f"   {coluna:28s} {'OK' if ok else 'FALHOU (fora do banco)'}")
        if not ok:
            return 1

    print("2) leitura dos valores")
    personagens = db.carregar_personagens(sb, user.id)
    alvo = personagens[0]
    print("   colunas lidas:", [c for c in CAMPOS if c in alvo])
    originais = {c: alvo.get(c, 0) for c in CAMPOS}

    print("3) ida e volta (grava -> le -> restaura)")
    dados = {k: v for k, v in alvo.items() if k != "updated_at"}
    dados["nucleos_dimensionais"] = 111
    dados["fragmento_vazio_disperso"] = 222
    dados["libertacao_nucleos"] = 3
    dados["libertacao_epicos"] = 2
    db.upsert_personagem(sb, dados, user.id)
    volta = next(p for p in db.carregar_personagens(sb, user.id)
                 if p["id"] == alvo["id"])
    for coluna, esperado in (("nucleos_dimensionais", 111),
                             ("fragmento_vazio_disperso", 222),
                             ("libertacao_nucleos", 3),
                             ("libertacao_epicos", 2)):
        print(f"   {coluna:28s} = {volta.get(coluna)} (esperado {esperado})")
        if volta.get(coluna) != esperado:
            print("   FALHOU: nao gravou")
            return 1

    # restaura
    restaurar = {k: v for k, v in alvo.items() if k != "updated_at"}
    db.upsert_personagem(sb, restaurar, user.id)
    volta = next(p for p in db.carregar_personagens(sb, user.id)
                 if p["id"] == alvo["id"])
    print("   restaurado:", {c: volta.get(c) for c in CAMPOS})
    for coluna in CAMPOS:
        if volta.get(coluna) != originais.get(coluna):
            print(f"   FALHOU: nao restaurou {coluna}")
            return 1

    print("\nCAMPOS NOVOS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

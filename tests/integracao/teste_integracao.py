"""
Teste de integracao completo com o Supabase (roda com uma CONTA JA CONFIRMADA).

Uso:
    python teste_integracao.py seu@email.com sua_senha

O que valida:
  1. login e perfil
  2. garantir_estrutura: 25 personagens + slots das tabelas filhas
  3. atualizacao de personagem e das filhas com os tipos corretos
     (inteiro, booleano com rotulo FALSO/VERDADEIRO, texto)
  4. limite de 25 personagens
  5. RLS (outro usuario / sem sessao nao enxerga os dados)
  6. restauracao dos valores alterados (teste NAO destrutivo)

Obs.: seguro para conta real: o teste apenas ALTERA campos de um personagem
e os restaura ao final. Em conta vazia, a estrutura de 25 personagens fica
criada (que e o comportamento desejado do app).
"""
import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys

import auth
import opcoes
import supabase_db as db
from credenciais_teste import conta_teste


def main(argv):
    email, senha = conta_teste(argv)

    print("1) login:", email)
    try:
        sb, resp = auth.login(email, senha)
    except Exception as erro:
        print("   FALHOU:", erro)
        print("   (se a conta ainda nao confirmou o e-mail, confirme antes.)")
        return 1
    user = getattr(resp, "user", None)
    if user is None:
        print("   FALHOU: resposta sem usuario")
        return 1
    print("   user_id:", user.id)
    print("   perfil:", auth.garantir_perfil(sb, user.id,
                                             (user.email or "").split("@")[0]))

    print("2) estrutura inicial (25 personagens + slots das filhas)")
    antes = db.carregar_personagens(sb, user.id)
    print(f"   personagens antes: {len(antes)}")
    res = db.garantir_estrutura(sb, user.id)
    print("   garantir_estrutura:", res)
    if res.get("erro"):
        print("   FALHOU: insercao bloqueada (RLS sem politica de INSERT?)")
        return 1
    pessoa = db.carregar_personagens(sb, user.id)
    if len(antes) < db.LIMITE_PERSONAGENS:
        faltando = [n for n in opcoes.PERSONAGENS
                    if n not in {p["Nome"] for p in pessoa}]
        if faltando:
            print("   FALHOU: personagens ausentes:", faltando)
            return 1
        print(f"   OK: {len(pessoa)} personagens, roster completo")
    else:
        print(f"   conta ja tinha {len(antes)} (cheia); roster nao exigido")
    if len(pessoa) < db.LIMITE_PERSONAGENS:
        print("   FALHOU: esperava no minimo 25 personagens")
        return 1
    # cada personagem precisa de linha em cada filha
    pecas = db.carregar_pecas_void(sb, pessoa)
    acess = db.carregar_acessorios_titulo(sb, pessoa)
    sem = db.carregar_semanais(sb, pessoa)
    print(f"   filhas: pecas={len(pecas)} acessorios={len(acess)} "
          f"semanais={len(sem)}")
    if not (len(pecas) >= len(pessoa) and len(acess) >= len(pessoa)
            and len(sem) >= len(pessoa)):
        print("   FALHOU: ha personagem sem linha nas tabelas filhas")
        return 1

    print("3) atualizacao com tipos corretos (nao destrutivo)")
    alvo = next((p for p in pessoa if p["Nome"] == "Elesis"), pessoa[0])
    pid, nome = alvo["id"], alvo["Nome"]
    originais = dict(alvo)                      # guarda tudo para restaurar

    # personagem: inteiro + texto (payload completo p/ upsert seguro)
    alterado = {k: v for k, v in originais.items() if k != "updated_at"}
    alterado["poder"] = 777777
    alterado["libertacao"] = "INEXISTENTE"
    db.upsert_personagem(sb, alterado, user.id)
    conferido = next(p for p in db.carregar_personagens(sb, user.id)
                     if p["id"] == pid)
    print("   personagem:", conferido.get("poder"),
          conferido.get("libertacao"))
    if conferido.get("poder") != 777777:
        print("   FALHOU: inteiro nao gravou")
        return 1

    # filhas: booleano (rotulo da planilha) + texto (payload completo)
    peca_orig = next((p for p in pecas if p.get("character_id") == pid), None)
    acess_orig = next((a for a in acess if a.get("character_id") == pid), None)
    sem_orig = next((s for s in sem if s.get("character_id") == pid), None)
    if not (peca_orig and acess_orig and sem_orig):
        print("   FALHOU: linha filha ausente para o personagem alvo")
        return 1
    p = {k: v for k, v in peca_orig.items() if k != "updated_at"}
    p["arma"], p["elmo"] = "VERDADEIRO", "FALSO"
    db.upsert_peca_void(sb, p)
    a = {k: v for k, v in acess_orig.items() if k != "updated_at"}
    a["titulo"], a["anel"] = "Teste Integracao", "Anel do Piu Piu"
    db.upsert_acessorio(sb, a)
    s = {k: v for k, v in sem_orig.items() if k != "updated_at"}
    s["void_4"], s["void_123"] = "Verdadeiro", "Falso"
    db.upsert_semanal(sb, s)
    pessoa2 = db.carregar_personagens(sb, user.id)
    peca2 = next(p for p in db.carregar_pecas_void(sb, pessoa2)
                 if p.get("character_id") == pid)
    acess2 = next(a for a in db.carregar_acessorios_titulo(sb, pessoa2)
                  if a.get("character_id") == pid)
    sem2 = next(s for s in db.carregar_semanais(sb, pessoa2)
                if s.get("character_id") == pid)
    print("   pecas:", peca2.get("arma"), "| acess:", acess2.get("titulo"),
          "| sem:", sem2.get("void_4"))
    if peca2.get("arma") != "VERDADEIRO":
        print("   FALHOU: booleano nao gravou/nao voltou como rotulo")
        return 1
    if acess2.get("titulo") != "Teste Integracao":
        print("   FALHOU: texto nao gravou")
        return 1
    if sem2.get("void_4") != "Verdadeiro":
        print("   FALHOU: booleano semanal nao gravou")
        return 1

    print("4) limite de 25 personagens")
    try:
        db.upsert_personagem(sb, {"Nome": "Personagem Extra"}, user.id)
    except ValueError as erro:
        print("   OK bloqueado:", erro)
    else:
        print("   FALHOU: conseguiu criar um 26o personagem")
        return 1

    print("5) RLS")
    sem_login = db.carregar_personagens(db.get_supabase(), None)
    print("   sem sessao ->", len(sem_login), "linhas (esperado 0)")
    outro = db.carregar_personagens(sb, "00000000-0000-0000-0000-000000000000")
    print("   user_id alheio ->", len(outro), "linhas (esperado 0)")
    if sem_login or outro:
        print("   FALHOU: RLS deixou vazar dados")
        return 1

    print("6) restauracao dos valores originais")
    restaurar = {k: v for k, v in originais.items()
                 if k not in ("updated_at",)}
    db.upsert_personagem(sb, restaurar, user.id)
    db.upsert_peca_void(sb, {k: v for k, v in peca_orig.items()
                             if k != "updated_at"})
    db.upsert_acessorio(sb, {k: v for k, v in acess_orig.items()
                             if k != "updated_at"})
    db.upsert_semanal(sb, {k: v for k, v in sem_orig.items()
                           if k != "updated_at"})
    volta = next(p for p in db.carregar_personagens(sb, user.id)
                 if p["id"] == pid)
    print("   restaurado:", volta.get("poder"), volta.get("libertacao"))
    if volta.get("poder") != originais.get("poder"):
        print("   FALHOU: restauracao nao aplicou")
        return 1

    print("\nINTEGRACAO OK")
    print(f"conta com {len(db.carregar_personagens(sb, user.id))} "
          "personagens (estrutura pronta)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

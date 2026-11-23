"""
Teste do salvamento ATOMICO (funcao salvar_conta, sql/salvar_conta.sql).

Valida, na conta de teste:
  1. A funcao existe e anon NAO pode chamar
  2. So as linhas alteradas sao enviadas (comparando com o original)
  3. Ida e volta: grava um valor e le de volta
  4. Atomico: um lote com 1 linha boa + 1 linha invalida nao grava NADA
  5. Nao da para mexer em linha de outra conta / inexistente (id falso)
  6. Um update nao consegue trocar o dono (user_id) nem o character_id
Tudo volta ao valor original no final.

    python teste_salvar_atomico.py [email] [senha]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys
import uuid

from credenciais_teste import conta_teste

import auth
import supabase_db as db


def _poder(sb, char_id):
    resp = (sb.table("user_characters").select("poder,user_id")
            .eq("id", char_id).limit(1).execute())
    return resp.data[0]


def main(argv):
    email, senha = conta_teste(argv)
    sb, resp = auth.login(email, senha)
    user = getattr(resp, "user", None)
    if user is None:
        print("FALHA NO LOGIN")
        return 1
    uid = user.id
    falhas = []

    # --- 1. anon nao pode chamar ------------------------------------------
    print("1) anon nao pode chamar a funcao")
    try:
        db.get_supabase().rpc("salvar_conta", {"dados": {}}).execute()
        falhas.append("anon conseguiu chamar salvar_conta")
    except Exception as erro:
        texto = str(erro)
        if "Could not find" in texto:
            print("   a funcao NAO existe: rode sql/salvar_conta.sql")
            return 1
        print(f"   recusado: {texto[:90]}")

    personagens = db.carregar_personagens(sb, uid)
    alvo = personagens[0]
    char_id, nome = alvo["id"], alvo["Nome"]
    original = _poder(sb, char_id)["poder"] or 0
    print(f"   personagem de teste: {nome} (poder {original})")

    try:
        # --- 2. so as linhas alteradas ------------------------------------
        print("2) so as linhas alteradas vao para o banco")
        enviados = []
        rpc_real = sb.rpc

        def espia(nome_funcao, params):
            enviados.append(params)
            return rpc_real(nome_funcao, params)

        sb.rpc = espia
        dados = {"Geral": [dict(p) for p in personagens]}
        originais = {"Geral": [dict(p) for p in personagens]}
        dados["Geral"][0]["poder"] = original + 1
        res = db.salvar_conta(sb, uid, dados, originais)
        sb.rpc = rpc_real
        linhas = enviados[0]["dados"]["personagens"] if enviados else []
        print(f"   {len(personagens)} personagens, enviados: {len(linhas)}, "
              f"resultado: {res['salvos']} atomico={res['atomico']}")
        if len(linhas) != 1 or not res["atomico"]:
            falhas.append("nao enviou so a linha alterada pela RPC")

        # --- 3. ida e volta -----------------------------------------------
        print("3) ida e volta")
        agora = _poder(sb, char_id)["poder"]
        print(f"   poder no banco: {agora}")
        if agora != original + 1:
            falhas.append("o valor nao foi gravado")

        # --- 4. atomico ---------------------------------------------------
        print("4) lote com 1 linha boa + 1 invalida nao grava nada")
        lote = {"personagens": [{"id": char_id, "poder": original + 999}],
                "semanais": [{"id": str(uuid.uuid4()),
                              "character_id": char_id, "void_4": True}]}
        try:
            sb.rpc("salvar_conta", {"dados": lote}).execute()
            falhas.append("lote invalido foi aceito")
        except Exception as erro:
            print(f"   recusado: {str(erro)[:100]}")
        depois = _poder(sb, char_id)["poder"]
        print(f"   poder continua {depois}")
        if depois != original + 1:
            falhas.append("a linha boa foi gravada mesmo com o lote falhando")

        # --- 5. id falso / de outra conta ---------------------------------
        print("5) id que nao e da conta e recusado")
        try:
            sb.rpc("salvar_conta", {"dados": {"personagens": [
                {"id": str(uuid.uuid4()), "poder": 1}]}}).execute()
            falhas.append("update em id falso passou em silencio")
        except Exception as erro:
            print(f"   recusado: {str(erro)[:100]}")

        # --- 6. nao troca dono nem personagem ------------------------------
        print("6) update nao troca user_id nem character_id")
        outro = str(uuid.uuid4())
        sb.rpc("salvar_conta", {"dados": {"personagens": [
            {"id": char_id, "user_id": outro, "poder": original + 1}]}}).execute()
        dono = _poder(sb, char_id)["user_id"]
        print(f"   dono continua o mesmo: {dono == uid}")
        if dono != uid:
            falhas.append("o update trocou o dono da linha")
        sem = (sb.table("user_semanais").select("id,character_id")
               .eq("character_id", char_id).limit(1).execute()).data
        if sem:
            sb.rpc("salvar_conta", {"dados": {"semanais": [
                {"id": sem[0]["id"], "character_id": personagens[1]["id"]}]}}
                   ).execute()
            volta = (sb.table("user_semanais").select("character_id")
                     .eq("id", sem[0]["id"]).execute()).data[0]
            print(f"   character_id continua o mesmo: "
                  f"{volta['character_id'] == char_id}")
            if volta["character_id"] != char_id:
                falhas.append("o update trocou o character_id")
    finally:
        sb.rpc("salvar_conta", {"dados": {"personagens": [
            {"id": char_id, "poder": original}]}}).execute()
        print(f"restaurado: poder {_poder(sb, char_id)['poder']}")

    if falhas:
        print("\nFALHOU:")
        for f in falhas:
            print("  -", f)
        return 1
    print("\nSALVAMENTO ATOMICO OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

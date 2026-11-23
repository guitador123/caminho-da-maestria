"""
Autenticação com Supabase Auth.

A sessão fica em memória dentro do objeto Client, por isso as funções de
autenticação devolvem o cliente junto com a resposta: é esse cliente que
precisa ser reaproveitado pelas demais chamadas (RLS depende dele).
"""

from supabase import create_client, Client
from registro import falha

SUPABASE_URL = "https://rtpwvfrdhrvtulvvctze.supabase.co"
SUPABASE_KEY = "sb_publishable_PsTxETk25rwmweJE17gyqA_MhRBgBAI"


def get_supabase() -> Client:
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def login(email: str, password: str):
    """Autentica. Retorna (client_com_sessao, resposta_auth)."""
    sb = get_supabase()
    resp = sb.auth.sign_in_with_password({"email": email, "password": password})
    return sb, resp


def cadastro(email: str, password: str, username: str):
    """Cria conta. Retorna (client, resposta_auth).

    Se a confirmacao de e-mail estiver ativa, resp.session vem None e o
    usuario precisara confirmar o e-mail antes de entrar.
    """
    sb = get_supabase()
    resp = sb.auth.sign_up({"email": email, "password": password})
    if resp.user and resp.session:
        garantir_perfil(sb, resp.user.id, username)
    return sb, resp


def garantir_perfil(sb: Client, user_id: str, username: str = None) -> bool:
    """Garante uma linha em user_profiles para o usuario logado (best effort)."""
    try:
        existe = (
            sb.table("user_profiles")
            .select("id")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        if existe.data:
            return True
        sb.table("user_profiles").insert(
            {"id": user_id, "username": username or "membro"}
        ).execute()
        return True
    except Exception:
        falha("garantir o perfil")
        return False


def resetar_senha(email: str):
    """Envia o link de redefinicao de senha. Retorna (client, resposta)."""
    sb = get_supabase()
    resp = sb.auth.reset_password_for_email(email)
    return sb, resp


def obter_usuario_logado(sb: Client):
    return sb.auth.get_user()

"""
Camada de dados Supabase para o app Controle Grand Chase.
Usa apenas a anon/publishable key (segura para app desktop distribuido).

Tabelas (RLS ativo: cada usuario acessa somente os proprios dados):
  user_characters        -> aba "Geral"
  user_pecas_void        -> aba "Pecas (Void)"
  user_acessorios_titulo -> aba "Acessorios Titulo"
  user_semanais          -> aba "Semanais"
  user_profiles          -> perfil do usuario (username)

Observacoes:
  - A sessao de autenticacao fica em memoria no objeto Client, por isso o
    cliente autenticado deve ser criado no login e reaproveitado no app.
  - No app/plancheta a coluna de nome aparece como "Nome"; no banco ela se
    chama "character_name" (traduzida pelos aliases abaixo).
"""

import math
import re

from supabase import create_client, Client

from opcoes import PERSONAGENS, coluna_banco, normalizar
from registro import falha

# CONFIGURACOES DO SUPABASE (substitua se necessario)
SUPABASE_URL = "https://rtpwvfrdhrvtulvvctze.supabase.co"
SUPABASE_KEY = "sb_publishable_PsTxETk25rwmweJE17gyqA_MhRBgBAI"

# Colunas realmente existentes em cada tabela
COLUNAS = {
    "personagens": [
        "character_name", "poder", "torre_das_ilusoes", "vazio_uni",
        "vazio_apo", "libertacao", "nucleo", "nucleos_epicos",
        # contadores proprios (13/11): recompensa de missao e libertacao
        "nucleos_dimensionais", "fragmento_vazio_disperso",
        "libertacao_nucleos", "libertacao_epicos",
    ],
    "pecas_void": [
        "arma", "asas", "botas", "calca", "capa", "cota", "elmo",
        "escudos", "facas", "luvas", "mascara", "diadema",
    ],
    "acessorios_titulo": ["anel", "brinco", "piercing", "tornozeleira", "titulo"],
    "semanais": [
        "fornalha_infernal", "altar_da_runha", "void_123", "void_4",
        "caminho_abissal", "terra_do_julgamento",
    ],
}

TABELAS = {
    "personagens": "user_characters",
    "pecas_void": "user_pecas_void",
    "acessorios_titulo": "user_acessorios_titulo",
    "semanais": "user_semanais",
}

# Chaves de exibicao -> colunas do banco
ALIAS = {"Nome": "character_name", "nome": "character_name"}

# Tipos REAIS das colunas (descobertos por sonda no PostgREST):
#   pecas_void e semanais -> boolean (a planilha usa "FALSO"/"VERDADEIRO")
#   poder -> bigint; vazio_uni/vazio_apo -> integer; demais -> text
BOOLEANAS = {
    "personagens": set(),
    "pecas_void": set(COLUNAS["pecas_void"]),
    "acessorios_titulo": set(),
    "semanais": set(COLUNAS["semanais"]),
}
INTEIRAS = {
    "personagens": {"poder", "vazio_uni", "vazio_apo",
                    "nucleos_dimensionais", "fragmento_vazio_disperso",
                    "libertacao_nucleos", "libertacao_epicos",
                    "nivel_chaser", "ataque", "ataque_especial",
                    "colecao_cartas"},
    "pecas_void": set(),
    "acessorios_titulo": set(),
    "semanais": set(),
}

# Colunas numeric(8, 2): os % dos status (15.1). Gravadas com ate 2 casas
# decimais, cortando (nunca arredondando para cima).
DECIMAIS = {
    "personagens": {"critico", "dano_critico", "dano_costas"},
}

# Rotulos de exibicao (banco bool -> texto da planilha) por tabela filha
ROTULOS_BOOLEANOS = {
    "pecas_void": ("FALSO", "VERDADEIRO"),
    "semanais": ("Falso", "Verdadeiro"),
}

# Nome da coluna da Torre das Ilusões semanal. O banco pode ter
# 'torre_das_ilusoes' (SQL do HANDOFF) ou 'torre_das_ilusoes_semanal'.
TORRE_SEMANAL = "torre_das_ilusoes_semanal"

# Colunas OPCIONAIS: so existem no banco se o usuario rodar o SQL do HANDOFF.
# Verificadas uma vez por sessao (cache no proprio client).
EXTRAS_OPCIONAIS = {
    "semanais": {"torre_das_ilusoes", TORRE_SEMANAL},
    # nivel do chaser (pendencia #3): um valor por conta, gravado em todas
    # as linhas de user_characters. So e enviado se a coluna existir.
    "personagens": {"nivel_chaser",
                    # status do personagem (15.1, sql/status_personagem.sql)
                    "ataque", "ataque_especial", "critico", "dano_critico",
                    "dano_costas",
                    # colecao de cartas (15.4, sql/colecao_cartas.sql)
                    "colecao_cartas"},
    # o Colar (15.5, sql/colar.sql)
    "acessorios_titulo": {"colar"},
    # as 4 cartas de cada equipamento (15.3, sql/cartas_void.sql)
    "pecas_void": {"cartas_arma", "cartas_luvas", "cartas_cota",
                   "cartas_botas", "cartas_capa", "cartas_calca",
                   "cartas_elmo",
                   # a pedra de cada equipamento (16, sql/pedras_void.sql)
                   "pedra_arma", "pedra_luvas", "pedra_cota", "pedra_botas",
                   "pedra_capa", "pedra_calca", "pedra_elmo"},
}

# Colunas OPCIONAIS do user_profiles (perfil do usuario).
# "missao_rapida" e o filtro antigo; "nick" e "avatar" sao do perfil (#7).
COLUNAS_PERFIL = ("missao_rapida", "nick", "avatar")
EXTRAS_BOOLEANAS = {
    "semanais": {"torre_das_ilusoes", TORRE_SEMANAL},
}

# Limite de personagens por conta
LIMITE_PERSONAGENS = 25

# 'user_pecas_void' -> 'pecas_void' (nome do banco -> nome logico)
LOGICA = {v: k for k, v in TABELAS.items()}


def get_supabase() -> Client:
    """Retorna cliente Supabase com a anon key (sem sessao de usuario)."""
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def coluna_ausente(erro) -> bool:
    """O erro do PostgREST e "essa coluna nao existe"? (esperado para as
    colunas opcionais; qualquer outro erro, como falta de rede, nao e)."""
    codigo = str(getattr(erro, "code", "") or "")
    return (codigo in ("42703", "PGRST204")
            or "does not exist" in str(erro).lower())


def _extras(supabase: Client, logica: str) -> set:
    """Colunas opcionais que existem de fato no banco (cache por sessao)."""
    cache = getattr(supabase, "_extras_cache", None)
    if cache is None:
        cache = {}
        try:
            supabase._extras_cache = cache
        except Exception:
            falha("guardar o cache de colunas")
    if logica in cache:
        return cache[logica]
    achadas = set()
    for col in EXTRAS_OPCIONAIS.get(logica, ()):
        try:
            supabase.table(TABELAS[logica]).select(col).limit(1).execute()
            achadas.add(col)
        except Exception as erro:
            if not coluna_ausente(erro):
                falha("conferir colunas extras", erro)
    cache[logica] = achadas
    return achadas


def colunas_salvaveis(supabase: Client, logica: str) -> set:
    """Conjunto (normalizado) das colunas que seriam gravadas na tabela."""
    permitidas = (set(COLUNAS[logica]) | _extras(supabase, logica)
                  | {"id", "character_id", "user_id"})
    norm = {normalizar(c) for c in permitidas}
    # a coluna da Torre semanal tambem responde pelo nome logico do app
    if logica == "semanais" and normalizar(TORRE_SEMANAL) in norm:
        norm.add(normalizar("torre_das_ilusoes"))
    return norm


# "618.002" e "1.234.567": ponto de MILHAR (como o card mostra os numeros)
_MILHAR = re.compile(r"^[+-]?[0-9]{1,3}(\.[0-9]{3})+$")


def decimal_2(valor):
    """'35,25' / '35.25' / '35,256%' / 35.256 -> 35.25 (ate 2 casas,
    CORTANDO). Aceita ponto de milhar junto com virgula ('1.250,5').
    Devolve None se nao for numero; negativo vira 0."""
    from decimal import Decimal, InvalidOperation, ROUND_DOWN
    if valor is None or isinstance(valor, bool):
        return None
    if isinstance(valor, (int, float)):
        if isinstance(valor, float) and math.isnan(valor):
            return None
        texto = repr(valor) if isinstance(valor, float) else str(valor)
    else:
        texto = str(valor).strip().replace(" ", "").replace("%", "")
        if "," in texto:
            texto = texto.replace(".", "").replace(",", ".")
    try:
        numero = Decimal(texto)
    except InvalidOperation:
        return None
    if not numero.is_finite():
        return None
    numero = numero.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    return max(0.0, float(numero))


def _bool(valor) -> bool:
    """Converte rotulos da planilha/banco em booleano real."""
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, (int, float)):
        return bool(valor)
    n = normalizar(valor)
    if n in ("", "0", "falso", "false", "f", "nao"):
        return False
    if n in ("1", "verdadeiro", "true", "t", "sim"):
        return True
    raise ValueError(f"'{valor}' nao e um valor booleano (use FALSO/VERDADEIRO).")


def _limpar(dados: dict, tabela: str, extras=()) -> dict:
    """Mapeia as chaves (coluna do banco OU cabecalho da planilha) para as
    colunas reais e converte para os tipos do banco:
      boolean -> True/False   (aceita "FALSO"/"Verdadeiro"/vazio)
      inteiro -> int          (aceita "618002.0")
      text    -> str          (None vira "")
    """
    permitidas = (set(COLUNAS[tabela]) | set(extras)
                  | {"id", "character_id", "user_id"})
    nome_real = {normalizar(c): c for c in permitidas}
    # compatibilidade: o app usa o nome logico 'torre_das_ilusoes'; no banco a
    # coluna pode se chamar 'torre_das_ilusoes_semanal'.
    if normalizar("torre_das_ilusoes") not in nome_real and \
            normalizar(TORRE_SEMANAL) in nome_real:
        nome_real[normalizar("torre_das_ilusoes")] = TORRE_SEMANAL
    bools = {normalizar(c) for c in
             (BOOLEANAS.get(tabela, set()) | EXTRAS_BOOLEANAS.get(tabela, set()))}
    inteiras = {normalizar(c) for c in INTEIRAS.get(tabela, set())}
    decimais = {normalizar(c) for c in DECIMAIS.get(tabela, set())}

    saida = {}
    for chave, valor in dados.items():
        if chave is None:
            continue
        col = coluna_banco(chave)
        if col not in nome_real:
            continue
        vazio = (valor is None or str(valor) == "nan"
                 or (isinstance(valor, float) and math.isnan(valor)))
        if col in ("id", "character_id") and vazio:
            continue
        if col in bools:
            saida[nome_real[col]] = False if vazio else _bool(valor)
        elif col in decimais:
            numero = (0.0 if vazio or str(valor).strip() == ""
                      else decimal_2(valor))
            if numero is None:
                raise ValueError(
                    f"'{valor}' nao e um numero valido para '{chave}'.")
            saida[nome_real[col]] = numero
        elif col in inteiras:
            if vazio:
                saida[nome_real[col]] = 0
            else:
                texto = str(valor).strip()
                if _MILHAR.match(texto):        # "618.002" -> 618002
                    valor = texto.replace(".", "")
                try:
                    saida[nome_real[col]] = int(float(valor))
                except (TypeError, ValueError):
                    raise ValueError(
                        f"'{valor}' nao e um numero valido para '{chave}'.")
        else:
            if vazio:
                saida[nome_real[col]] = ""
            elif isinstance(valor, str):
                saida[nome_real[col]] = valor
            else:
                saida[nome_real[col]] = str(valor)
    return saida


# ---------------------------------------------------------------------------
# PERSONAGENS (aba Geral)
# ---------------------------------------------------------------------------
def carregar_personagens(supabase: Client, user_id: str):
    """Lista os personagens de um usuario. A coluna de nome vem como 'Nome'."""
    consulta = supabase.table("user_characters").select("*")
    if user_id:
        consulta = consulta.eq("user_id", user_id)
    resp = consulta.order("character_name").execute()
    linhas = resp.data or []
    for linha in linhas:
        linha["Nome"] = linha.pop("character_name", "")
        linha.pop("user_id", None)
        linha.pop("updated_at", None)
    return linhas


def upsert_personagem(supabase: Client, personagem: dict, user_id: str):
    """Insere ou atualiza um personagem do usuario logado."""
    dados = _limpar(personagem, "personagens")
    if not dados.get("character_name"):
        raise ValueError("Personagem sem nome: nada foi salvo.")
    if user_id:
        dados["user_id"] = user_id
    if not dados.get("user_id"):
        raise ValueError("Usuario nao autenticado: nada foi salvo.")

    if dados.get("id"):
        supabase.table("user_characters").upsert(dados, on_conflict="id").execute()
        return

    # Linha nova: evita duplicar o mesmo nome dentro do usuario
    existente = (
        supabase.table("user_characters")
        .select("id")
        .eq("user_id", dados["user_id"])
        .eq("character_name", dados["character_name"])
        .limit(1)
        .execute()
    )
    if existente.data:
        dados["id"] = existente.data[0]["id"]
        supabase.table("user_characters").upsert(dados, on_conflict="id").execute()
        return

    # Respeita o limite de personagens por conta
    contagem = (
        supabase.table("user_characters")
        .select("id", count="exact")
        .eq("user_id", dados["user_id"])
        .limit(1)
        .execute()
    )
    if (getattr(contagem, "count", None) or 0) >= LIMITE_PERSONAGENS:
        raise ValueError(
            f"Limite de {LIMITE_PERSONAGENS} personagens por usuario atingido.")
    supabase.table("user_characters").insert(dados).execute()


def deletar_personagem(supabase: Client, personagem_id):
    supabase.table("user_characters").delete().eq("id", personagem_id).execute()


# ---------------------------------------------------------------------------
# ESTRUTURA INICIAL (25 personagens + uma linha por tabela filha)
# ---------------------------------------------------------------------------
def _padroes_personagem() -> dict:
    """Valores iniciais de um personagem novo (slot vazio da planilha)."""
    return {"poder": 0, "torre_das_ilusoes": "", "vazio_uni": 0,
            "vazio_apo": 0, "libertacao": "", "nucleo": "", "nucleos_epicos": ""}


def _padroes_filha(logica: str, extras) -> dict:
    """Valores iniciais das tabelas filhas (FALSO / texto vazio)."""
    saida = {}
    for col in COLUNAS[logica]:
        saida[col] = False if col in BOOLEANAS[logica] else ""
    for col in extras:
        saida[col] = False if col in EXTRAS_BOOLEANAS.get(logica, set()) else ""
    return saida


def _insert_lote(supabase: Client, tabela: str, linhas: list) -> int:
    """Insere varias linhas em uma unica requisicao; se falhar, tenta uma a
    uma (util quando so uma linha conflita). Falha de permissao/RLS nao
    vale a pena repetir. Devolve quantas linhas foram criadas."""
    try:
        supabase.table(tabela).insert(linhas).execute()
        return len(linhas)
    except Exception as erro:
        msg = str(erro).lower()
        if any(t in msg for t in ("permission", "policy", "row-level",
                                  "unauthorized", "401", "403")):
            return 0
    criadas = 0
    for linha in linhas:
        try:
            supabase.table(tabela).insert(linha).execute()
            criadas += 1
        except Exception:
            falha("inserir linha avulsa")
            continue
    return criadas


def garantir_estrutura(supabase: Client, user_id: str) -> dict:
    """Garante os 25 personagens iniciais e uma linha em cada tabela filha
    por personagem (contas NOVAS e EXISTENTES).

    - Preenche somente o que falta: nunca altera dados ja existentes.
    - Respeita LIMITE_PERSONAGENS por conta.
    - Devolve contagens do que criou:
        {"personagens": n, "pecas_void": n, "acessorios_titulo": n, "semanais": n}
      e a chave "erro" quando alguma insercao falhou (ex.: RLS sem INSERT).
    """
    resultado = {"personagens": 0, "pecas_void": 0,
                 "acessorios_titulo": 0, "semanais": 0}
    if not user_id:
        return resultado
    try:
        existentes = carregar_personagens(supabase, user_id)
    except Exception:
        falha("carregar personagens (estrutura)")
        resultado["erro"] = True
        return resultado

    # 1) personagens (slots) que faltam
    nomes = {p.get("Nome") for p in existentes}
    faltantes = [n for n in PERSONAGENS if n not in nomes]
    if faltantes and len(existentes) < LIMITE_PERSONAGENS:
        cabe = LIMITE_PERSONAGENS - len(existentes)
        novos = []
        for nome in faltantes[:cabe]:
            linha = {"user_id": user_id, "character_name": nome}
            linha.update(_padroes_personagem())
            novos.append(linha)
        criados = _insert_lote(supabase, "user_characters", novos)
        resultado["personagens"] = criados
        if not criados:
            resultado["erro"] = True
        try:
            existentes = carregar_personagens(supabase, user_id)
        except Exception:
            falha("recarregar personagens (estrutura)")
            return resultado

    # 2) uma linha por personagem em cada tabela filha
    if not existentes:
        return resultado
    filhas = (("pecas_void", carregar_pecas_void),
              ("acessorios_titulo", carregar_acessorios_titulo),
              ("semanais", carregar_semanais))
    for logica, carregar in filhas:
        try:
            atuais = carregar(supabase, existentes)
        except Exception:
            falha("carregar tabela filha (estrutura)")
            atuais = []
        tem = {linha.get("character_id") for linha in atuais}
        extras = _extras(supabase, logica)
        padroes = _padroes_filha(logica, extras)
        novos = []
        for p in existentes:
            if p.get("id") and p["id"] not in tem:
                linha = dict(padroes)
                linha["character_id"] = p["id"]
                novos.append(linha)
        if not novos:
            continue
        criados = _insert_lote(supabase, TABELAS[logica], novos)
        resultado[logica] = criados
        if not criados:
            resultado["erro"] = True
    return resultado


# ---------------------------------------------------------------------------
# TABELAS FILHAS (ligadas por character_id)
# ---------------------------------------------------------------------------
def _extrair_ids_nomes(personagens):
    ids = [p["id"] for p in personagens if p.get("id")]
    nomes = {p["id"]: p.get("Nome", "") for p in personagens if p.get("id")}
    return ids, nomes


def _carregar_filha(supabase: Client, tabela: str, personagens):
    """Carrega uma tabela filha ja com a coluna 'Nome' (do personagem) e os
    booleanos convertidos para os rotulos da planilha (FALSO/VERDADEIRO)."""
    logica = LOGICA.get(tabela, tabela)
    ids, nomes = _extrair_ids_nomes(personagens)
    if not ids:
        return []
    resp = (
        supabase.table(tabela)
        .select("*")
        .in_("character_id", ids)
        .order("character_id")
        .execute()
    )
    linhas = resp.data or []
    rotulos = ROTULOS_BOOLEANOS.get(logica)
    # protecao: um personagem nao pode ter mais de uma linha na tabela filha
    # (historico ja teve duplicatas -> a UI mostraria o mesmo char N vezes)
    vistas = {}
    for linha in linhas:
        chave = linha.get("character_id")
        if chave in vistas:
            vistas[chave].update(linha)      # a ultima gravada prevalece
            continue
        vistas[chave] = linha
    linhas = list(vistas.values())
    for linha in linhas:
        linha["Nome"] = nomes.get(linha.get("character_id"), "")
        linha.pop("updated_at", None)
        if rotulos:
            for chave, valor in list(linha.items()):
                if isinstance(valor, bool):
                    linha[chave] = rotulos[1] if valor else rotulos[0]
    return linhas


def _upsert_filha(supabase: Client, tabela: str, dados: dict):
    """Insere/atualiza uma linha filha pelo id ou pelo personagem vinculado.
    `tabela` pode vir como nome do banco ('user_pecas_void') ou logico
    ('pecas_void')."""
    logica = LOGICA.get(tabela, tabela)
    extras = _extras(supabase, logica)
    payload = _limpar(dados, logica, extras)
    if not payload:
        return
    if payload.get("id"):
        supabase.table(tabela).upsert(payload, on_conflict="id").execute()
        return

    character_id = payload.get("character_id")
    if not character_id:
        return  # sem vinculo com personagem: nada a salvar

    existente = (
        supabase.table(tabela)
        .select("id")
        .eq("character_id", character_id)
        .limit(1)
        .execute()
    )
    if existente.data:
        payload["id"] = existente.data[0]["id"]
        supabase.table(tabela).upsert(payload, on_conflict="id").execute()
    else:
        supabase.table(tabela).insert(payload).execute()


# ---------------------------------------------------------------------------
# SALVAMENTO EM LOTE (poucas requisicoes -> nao trava a interface)
# ---------------------------------------------------------------------------
# nome da aba no app -> nome logico da tabela
ABAS_TABELAS = {
    "Geral": "personagens",
    "Peças (Void)": "pecas_void",
    "Acessórios Título": "acessorios_titulo",
    "Semanais": "semanais",
}


# ------------------------------------------------------------- perfil ----
def ler_perfil(supabase: Client, user_id: str) -> dict:
    """Le o perfil do usuario (nick, avatar, missoes).

    Devolve {} se a coluna nao existir (o app funciona sem elas).
    """
    if not user_id:
        return {}
    try:
        resp = (supabase.table("user_profiles").select("*")
                .eq("id", user_id).limit(1).execute())
        linhas = getattr(resp, "data", None) or []
        if linhas:
            return linhas[0]
    except Exception:
        falha("ler o perfil")
    return {}


def _coluna_perfil_existe(supabase: Client, coluna: str) -> bool:
    """A coluna opcional existe no user_profiles?"""
    try:
        supabase.table("user_profiles").select(coluna).limit(1).execute()
        return True
    except Exception as erro:
        if not coluna_ausente(erro):
            falha("conferir coluna do perfil", erro)
        return False


def salvar_perfil(supabase: Client, user_id: str, dados: dict) -> bool:
    """Grava os campos do perfil (ignora os que nao existem no banco)."""
    if not user_id:
        return False
    campos = {k: v for k, v in dados.items() if v is not None}
    if not campos:
        return False
    gravados = {}
    for chave, valor in campos.items():
        if _coluna_perfil_existe(supabase, chave):
            gravados[chave] = valor
    if not gravados:
        return False
    try:
        supabase.table("user_profiles").update(gravados).eq("id", user_id).execute()
        return True
    except Exception:
        falha("salvar o perfil")
        return False


def trocar_email(supabase: Client, email: str) -> str:
    """Troca o e-mail do usuario (Supabase Auth). Devolve '' ou a mensagem."""
    try:
        resp = supabase.auth.update_user({"email": email})
        erro = getattr(resp, "error", None)
        if erro:
            return str(erro)
        return ""
    except Exception as erro:
        falha("trocar o e-mail", erro)
        return str(erro)


def trocar_senha(supabase: Client, senha: str) -> str:
    """Troca a senha do usuario (Supabase Auth). Devolve '' ou a mensagem."""
    try:
        resp = supabase.auth.update_user({"password": senha})
        erro = getattr(resp, "error", None)
        if erro:
            return str(erro)
        return ""
    except Exception as erro:
        falha("trocar a senha", erro)
        return str(erro)


def _upsert_lote(supabase: Client, tabela: str, payloads: list) -> int:
    """Grava varias linhas em poucas requisicoes.

    Separa as linhas que ja tem `id` (merge) das novas (insert): o
    PostgREST exige que todos os objetos de um lote tenham as mesmas
    chaves, e uma linha nova nao tem `id`.
    """
    if not payloads:
        return 0
    com_id = [p for p in payloads if p.get("id")]
    sem_id = [p for p in payloads if not p.get("id")]
    total = 0
    if com_id:
        supabase.table(tabela).upsert(com_id, on_conflict="id").execute()
        total += len(com_id)
    if sem_id:
        supabase.table(tabela).insert(sem_id).execute()
        total += len(sem_id)
    return total


def _montar_payloads(supabase: Client, user_id: str, dados_por_aba: dict,
                     perdidas=None) -> dict:
    """Converte as abas em linhas do banco: {logica: [payload, ...]}.

    Linhas filhas sem `character_id` levam `_nome` (o nome do personagem),
    para o banco achar o id. `perdidas` recebe as colunas da planilha que
    nao existem no banco.
    """
    permitidas_geral = colunas_salvaveis(supabase, "personagens")
    saida = {}
    for aba, logica in ABAS_TABELAS.items():
        linhas = dados_por_aba.get(aba) or []
        extras = _extras(supabase, logica)
        payloads = []
        for linha in linhas:
            payload = _limpar(linha, logica, extras)
            if logica == "personagens":
                if not payload.get("character_name"):
                    continue
                payload["user_id"] = user_id
                if perdidas is not None:
                    for coluna in linha:
                        if coluna in ("Nome", "id", "updated_at"):
                            continue
                        if coluna_banco(coluna) not in permitidas_geral:
                            perdidas.append(str(coluna))
            else:
                if not payload:
                    continue
                nome = linha.get("Nome") or linha.get("nome")
                if not payload.get("character_id"):
                    if not nome:
                        continue
                    payload["_nome"] = str(nome)
            payloads.append(payload)
        saida[logica] = payloads
    return saida


def so_alteradas(payloads: dict, originais: dict) -> dict:
    """Fica so com as linhas que mudaram em relacao ao `originais` (o que
    foi carregado do banco ou salvo por ultimo). Linha sem `id` (nova)
    sempre vai."""
    saida = {}
    for logica, linhas in payloads.items():
        antes = {p.get("id"): p for p in originais.get(logica, ()) if p.get("id")}
        saida[logica] = [p for p in linhas
                         if not p.get("id") or antes.get(p["id"]) != p]
    return saida


def _rpc_indisponivel(erro) -> bool:
    """A funcao salvar_conta ainda nao foi criada no banco?"""
    codigo = str(getattr(erro, "code", "") or "")
    texto = str(erro).lower()
    return codigo in ("PGRST202", "42883") or (
        "salvar_conta" in texto and ("could not find" in texto
                                     or "does not exist" in texto))


def _salvar_por_tabela(supabase: Client, user_id: str, payloads: dict) -> dict:
    """Jeito antigo (1 requisicao por tabela, SEM transacao). So e usado se
    a funcao `salvar_conta` (sql/salvar_conta.sql) nao existir no banco."""
    salvos = {"personagens": _upsert_lote(supabase, "user_characters",
                                          payloads.get("personagens", []))}
    mapa = {}
    try:
        for p in carregar_personagens(supabase, user_id):
            if p.get("id") and p.get("Nome"):
                mapa[p["Nome"]] = p["id"]
    except Exception:
        falha("mapear personagens ao salvar")
    for logica in ("pecas_void", "acessorios_titulo", "semanais"):
        linhas = []
        for p in payloads.get(logica, []):
            p = dict(p)
            nome = p.pop("_nome", None)
            if not p.get("character_id"):
                if nome not in mapa:
                    continue
                p["character_id"] = mapa[nome]
            linhas.append(p)
        salvos[logica] = _upsert_lote(supabase, TABELAS[logica], linhas)
    return salvos


def salvar_conta(supabase: Client, user_id: str, dados_por_aba: dict,
                 originais_por_aba: dict = None) -> dict:
    """Salva a conta numa TRANSACAO so (funcao `salvar_conta` no banco).

    `dados_por_aba` = {"Geral": [records...], "Peças (Void)": [...], ...}
    Cada record tem a coluna "Nome" (nome do personagem).
    `originais_por_aba` (mesmo formato) = o que esta no banco; se vier, so
    as linhas diferentes sao enviadas.

    Se qualquer linha falhar, nada e gravado (levanta a excecao).

    Devolve:
      {"salvos": {"personagens": n, ...}, "perdidas": [colunas],
       "erro": None, "atomico": True/False}
    """
    resultado = {"salvos": {}, "perdidas": [], "erro": None, "atomico": True}
    payloads = _montar_payloads(supabase, user_id, dados_por_aba,
                                resultado["perdidas"])
    if originais_por_aba is not None:
        payloads = so_alteradas(
            payloads, _montar_payloads(supabase, user_id, originais_por_aba))
    resultado["perdidas"] = sorted(set(resultado["perdidas"]))

    if not any(payloads.values()):
        resultado["salvos"] = {logica: 0 for logica in payloads}
        return resultado

    envio = {logica: [{k: v for k, v in p.items() if k != "user_id"}
                      for p in linhas]
             for logica, linhas in payloads.items()}
    try:
        resp = supabase.rpc("salvar_conta", {"dados": envio}).execute()
        contagem = getattr(resp, "data", None) or {}
        resultado["salvos"] = {logica: int(contagem.get(logica, 0))
                               for logica in payloads}
        return resultado
    except Exception as erro:
        if not _rpc_indisponivel(erro):
            raise
        falha("salvar_conta (RPC) indisponivel: rode sql/salvar_conta.sql "
              "no Supabase; salvando tabela por tabela", erro)

    resultado["atomico"] = False
    resultado["salvos"] = _salvar_por_tabela(supabase, user_id, payloads)
    return resultado


# ---------------------------------------------------------------------------
# PECAS VOID
# ---------------------------------------------------------------------------
def carregar_pecas_void(supabase: Client, personagens):
    return _carregar_filha(supabase, "user_pecas_void", personagens)


def upsert_peca_void(supabase: Client, dados: dict):
    _upsert_filha(supabase, "user_pecas_void", dados)


# ---------------------------------------------------------------------------
# ACESSORIOS / TITULO
# ---------------------------------------------------------------------------
def carregar_acessorios_titulo(supabase: Client, personagens):
    return _carregar_filha(supabase, "user_acessorios_titulo", personagens)


def upsert_acessorio(supabase: Client, dados: dict):
    _upsert_filha(supabase, "user_acessorios_titulo", dados)


# ---------------------------------------------------------------------------
# SEMANAIS
# ---------------------------------------------------------------------------
def carregar_semanais(supabase: Client, personagens):
    return _carregar_filha(supabase, "user_semanais", personagens)


def upsert_semanal(supabase: Client, dados: dict):
    _upsert_filha(supabase, "user_semanais", dados)


# ---------------------------------------------------------------------------
# EXPORTACAO PARA EXCEL (backup local)
# ---------------------------------------------------------------------------
def exportar_para_excel(dados_por_tabela: dict, caminho="backup_gc.xlsx"):
    """Exporta dicionario {nome_tabela: lista_de_dicts} para Excel."""
    import pandas as pd
    with pd.ExcelWriter(caminho, engine="openpyxl") as writer:
        for nome_tabela, lista in dados_por_tabela.items():
            df = pd.DataFrame(lista)
            if not df.empty:
                df.to_excel(writer, sheet_name=nome_tabela, index=False)


# ---------------------------------------------------------------------------
# HISTORICO SEMANAL (pagina "Evolucao"; ver sql/historico_semanal.sql)
# ---------------------------------------------------------------------------
def _tabela_ausente(erro) -> bool:
    """O erro e "essa tabela nao existe" (o SQL ainda nao foi rodado)?"""
    codigo = str(getattr(erro, "code", "") or "")
    texto = str(erro).lower()
    return codigo in ("PGRST205", "42P01") or (
        "user_historico_semanal" in texto and (
            "could not find" in texto or "does not exist" in texto))


def carregar_historico(supabase: Client):
    """As fotos semanais da conta logada (o RLS so devolve as suas).

    Devolve (linhas, disponivel): disponivel=False quando a tabela ainda
    nao existe no banco (o app segue so com a semana atual).
    """
    colunas = "character_name,semana,poder,pecas_void,desafios"

    def buscar(selecao):
        return (supabase.table("user_historico_semanal").select(selecao)
                .order("semana").execute())

    # colunas que dependem de um SQL que pode nao ter sido rodado: se o
    # banco disser que uma delas nao existe, busca de novo sem ela
    opcionais = ["nivel_chaser", "colecao_cartas"]
    try:
        while True:
            try:
                resp = buscar(",".join([colunas] + opcionais))
                break
            except Exception as erro:
                # (a mensagem cita a tabela, por isso o teste da COLUNA)
                texto = str(erro).lower()
                ausente = next((c for c in opcionais if c in texto), None)
                if ausente is None or not coluna_ausente(erro):
                    raise
                opcionais.remove(ausente)
        return list(getattr(resp, "data", None) or []), True
    except Exception as erro:
        if _tabela_ausente(erro):
            return [], False
        raise


def marcar_resumo_visto(supabase: Client, user_id: str, data) -> bool:
    """Grava que a conta ja viu o resumo da semana `data` (abre 1 vez)."""
    try:
        supabase.table("user_profiles").update(
            {"resumo_visto": data.isoformat()}).eq("id", user_id).execute()
        return True
    except Exception as erro:
        if not coluna_ausente(erro):
            falha("marcar o resumo semanal como visto", erro)
        return False

# -*- coding: utf-8 -*-
"""
Historico semanal da conta (logica pura, sem Tk): base da pagina
"Evolucao".

Uma SEMANA e uma foto de todos os personagens:

    {"data": date(2026, 11, 25) ou None,   # None = semana atual (parcial)
     "personagens": {"Elesis": {"poder": 618002,
                                "pecas": {"elmo", "arma", ...},
                                "desafios": {"void4", ...}}, ...}}

As fotos vem do banco (user_historico_semanal, gravada pelo reset de
quarta as 03h) e a semana atual vem das abas da tela. As chaves de pecas
e desafios sao NORMALIZADAS (ex.: "calca", "torredasilusoes"), para o
banco ("torre_das_ilusoes_semanal") e a planilha ("Torre Das Ilusoes")
cairem no mesmo lugar.
"""

from datetime import date, datetime, timedelta, timezone

from card_personagem import DUNGEONS
from dados_app import _num, _verdadeiro
from opcoes import chave_semanal, coluna_banco

# (chave normalizada, rotulo)
EQUIPAMENTOS = [("elmo", "Elmo"), ("cota", "Cota"), ("calca", "Calça"),
                ("luvas", "Luva"), ("botas", "Bota"), ("capa", "Capa"),
                ("arma", "Arma")]
ACESSORIOS = [("diadema", "Diadema"), ("mascara", "Máscara"),
              ("asas", "Asas"), ("facas", "Facas"), ("escudos", "Escudo")]
DESAFIOS = list(DUNGEONS)          # os 7 desafios semanais do card

_CHAVES_PECAS = {c for c, _ in EQUIPAMENTOS + ACESSORIOS}
_CHAVES_DESAFIOS = {c for c, _ in DESAFIOS}

# reset semanal: quarta-feira, 03h de Brasilia (UTC-3, sem horario de verao)
FUSO_BRASILIA = timezone(timedelta(hours=-3))
DIA_RESET = 2                      # segunda=0 ... quarta=2
HORA_RESET = 3


# ------------------------------------------------------------ montar semana
def _marcadas(valores, validas, normalizar_chave):
    """{chave: valor} -> as chaves validas marcadas como feitas."""
    saida = set()
    for chave, valor in (valores or {}).items():
        normal = normalizar_chave(chave)
        if normal in validas and _verdadeiro(valor):
            saida.add(normal)
    return saida


def de_historico(linhas):
    """Linhas de user_historico_semanal -> lista de semanas (mais antiga
    primeiro)."""
    por_data = {}
    for linha in linhas or ():
        data = linha.get("semana")
        if isinstance(data, str):
            data = date.fromisoformat(data[:10])
        if not isinstance(data, date):
            continue
        nome = str(linha.get("character_name") or "")
        if not nome:
            continue
        semana = por_data.setdefault(data, {"data": data, "personagens": {}})
        semana["personagens"][nome] = {
            "poder": _num(linha.get("poder")),
            "pecas": _marcadas(linha.get("pecas_void"), _CHAVES_PECAS,
                               coluna_banco),
            "desafios": _marcadas(linha.get("desafios"), _CHAVES_DESAFIOS,
                                  chave_semanal),
        }
    return [por_data[d] for d in sorted(por_data)]


def _linhas_por_nome(df):
    if df is None or df.empty or "Nome" not in df.columns:
        return {}
    return {str(linha["Nome"]): linha
            for linha in df.to_dict("records")}


def da_tela(df_geral, df_pecas, df_semanais):
    """A semana ATUAL (parcial), a partir das abas carregadas no app."""
    geral = _linhas_por_nome(df_geral)
    pecas = _linhas_por_nome(df_pecas)
    semanais = _linhas_por_nome(df_semanais)
    personagens = {}
    for nome, linha in geral.items():
        poder = next((linha[c] for c in linha if coluna_banco(c) == "poder"),
                     0)
        personagens[nome] = {
            "poder": _num(poder),
            "pecas": _marcadas(pecas.get(nome), _CHAVES_PECAS, coluna_banco),
            "desafios": _marcadas(semanais.get(nome), _CHAVES_DESAFIOS,
                                  chave_semanal),
        }
    return {"data": None, "personagens": personagens}


# ----------------------------------------------------------------- numeros
def ataque_medio(semana):
    """A media do Ataque Total (como o cartao da tela principal)."""
    poderes = [p["poder"] for p in semana["personagens"].values()]
    return sum(poderes) / len(poderes) if poderes else None


def contagem_pecas(semana):
    """Pecas do Void feitas: total de equipamentos, de acessorios e quantos
    personagens tem cada peca."""
    personagens = semana["personagens"].values()
    por_peca = {chave: sum(chave in p["pecas"] for p in personagens)
                for chave, _ in EQUIPAMENTOS + ACESSORIOS}
    quantos = len(semana["personagens"])
    return {
        "equipamentos": sum(por_peca[c] for c, _ in EQUIPAMENTOS),
        "acessorios": sum(por_peca[c] for c, _ in ACESSORIOS),
        "max_equipamentos": quantos * len(EQUIPAMENTOS),
        "max_acessorios": quantos * len(ACESSORIOS),
        "por_peca": por_peca,
    }


def contagem_desafios(semana):
    """Desafios semanais feitos (total e por desafio)."""
    personagens = semana["personagens"].values()
    por_desafio = {chave: sum(chave in p["desafios"] for p in personagens)
                   for chave, _ in DESAFIOS}
    return {"total": sum(por_desafio.values()),
            "maximo": len(semana["personagens"]) * len(DESAFIOS),
            "por_desafio": por_desafio}


def variacao(atual, anterior):
    """(diferenca, percentual) entre dois numeros; None se faltar um."""
    if atual is None or anterior is None:
        return None, None
    diferenca = atual - anterior
    percentual = (diferenca / anterior * 100) if anterior else None
    return diferenca, percentual


def evolucao_personagens(semanas):
    """[(nome, [poder por semana], poder atual, diferenca da ultima semana)]
    do mais forte para o mais fraco."""
    if not semanas:
        return []
    nomes = list(semanas[-1]["personagens"])
    saida = []
    for nome in nomes:
        serie = [s["personagens"].get(nome, {}).get("poder") for s in semanas]
        valores = [v for v in serie if v is not None]
        atual = valores[-1] if valores else 0
        anterior = valores[-2] if len(valores) > 1 else None
        diferenca = None if anterior is None else atual - anterior
        saida.append((nome, serie, atual, diferenca))
    return sorted(saida, key=lambda item: item[2], reverse=True)


# ------------------------------------------------------------------- datas
def ultimo_reset(agora=None):
    """A data (Brasilia) do reset mais recente (quarta 03h) ate `agora`."""
    agora = (agora or datetime.now(timezone.utc)).astimezone(FUSO_BRASILIA)
    dias = (agora.weekday() - DIA_RESET) % 7
    reset = (agora - timedelta(days=dias)).replace(
        hour=HORA_RESET, minute=0, second=0, microsecond=0)
    if reset > agora:
        reset -= timedelta(days=7)
    return reset.date()


def intervalo_da_semana(data_reset):
    """A semana que o reset de `data_reset` fechou: (quarta, terca)."""
    return data_reset - timedelta(days=7), data_reset - timedelta(days=1)


def deve_mostrar(semanas, visto):
    """A data da semana a destacar na abertura automatica, ou None.

    Mostra uma vez por reset: quando ha uma foto mais nova do que a que a
    conta ja viu (`visto`, data ou texto ISO).
    """
    if not semanas:
        return None
    mais_nova = semanas[-1]["data"]
    if isinstance(visto, str) and visto:
        visto = date.fromisoformat(visto[:10])
    if visto and visto >= mais_nova:
        return None
    return mais_nova

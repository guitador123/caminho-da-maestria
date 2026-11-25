# -*- coding: utf-8 -*-
"""
Opções de preenchimento dos "slots" da planilha + normalização de nomes.

ARQUIVO GERADO a partir de "Controle Grand Chase (1).xlsx" (listas de
validação de dados / dropdowns das 4 abas). Os dicionários PERSONAGENS
e OPCOES não devem ser editados à mão; as funções de normalização e os
mapas ALIAS_EXATA/ALIASES/ABAS_CANONICAS podem ser ajustados se aparecer
um cabeçalho novo.

Chaves de coluna ficam NORMALIZADAS (minúsculas, sem acentos, sem
espaços/pontuação) para casar tanto com os nomes do banco (ex.:
altar_da_runha) quanto com os cabeçalhos da planilha (ex.: "Altar da Ruína").
"""

import re
import unicodedata

# Cabeçalho exato -> coluna do banco (aplicado antes da normalização)
ALIAS_EXATA = {
    "Nome": "character_name",
    "nome": "character_name",
}

# Cabeçalho da planilha (normalizado) -> coluna do banco, quando a
# normalização por si só não casa (nomes reais do banco, inclusive o
# erro de digitação "runha" em altar_da_runha).
ALIASES = {
    "altardaruina": "altar_da_runha",
    "void12e3": "void_123",
}

# Nome da aba na planilha -> nome canônico usado pelo app
ABAS_CANONICAS = {
    "Geral": "Geral",
    "Peças ( Void )": "Peças (Void)",
    "Peças (Void)": "Peças (Void)",
    "Acessórios Título": "Acessórios Título",
    "Semanais": "Semanais",
}


def normalizar(texto):
    """'Torre Das Ilusões' -> 'torredasilusoes'."""
    if texto is None:
        return ""
    s = str(texto).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFD", s)
                if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]+", "", s)


# A Torre das Ilusoes SEMANAL aparece com DOIS nomes:
#   "torre_das_ilusoes"          (como o app e a planilha chamam)
#   "torre_das_ilusoes_semanal"  (como esta no banco, em user_semanais)
# A Torre MENSAL (que fica na aba Geral, com o "30 / 30") e so a primeira.
ALIAS_TORRE_SEMANAL = {
    "torredasilusoes": "torredasilusoesemanal",
    "torredasilusoesemanal": "torredasilusoes",
}

CHAVE_TORRE_SEMANAL = "torredasilusoes"


def coluna_banco(chave):
    """Nome (do banco OU cabeçalho da planilha) -> chave normalizada da coluna."""
    base = ALIAS_EXATA.get(str(chave).strip(), chave)
    base = ALIASES.get(normalizar(base), base)
    return normalizar(base)


def mesmo_dado(chave_a, chave_b):
    """As duas chaves apontam para o mesmo dado?

    Serve para a Torre das Ilusoes SEMANAL, que tem dois nomes (no app e
    no banco) - sem isso o app nunca encontrava a coluna dela.
    """
    a = coluna_banco(chave_a)
    b = coluna_banco(chave_b)
    if a == b:
        return True
    return ALIAS_TORRE_SEMANAL.get(a) == b


def chave_semanal(chave):
    """A chave da dungeon SEMANAL como o app espera.

    A Torre do banco ("torre_das_ilusoes_semanal") vira
    "torredasilusoes", que e a chave usada pelos cards e pelos filtros.
    """
    base = coluna_banco(chave)
    if base == "torredasilusoesemanal":
        return CHAVE_TORRE_SEMANAL
    return base


def canonizar_aba(nome):
    """Nome de aba da planilha -> nome canônico do app."""
    n = re.sub(r"\s+", " ", str(nome)).strip()
    return ABAS_CANONICAS.get(n, n)


# A coluna semanal da Torre das Ilusões pode existir no banco com o sufixo
# "_semanal" (coluna antiga) — os dois nomes viram a mesma chave lógica.
ALIASES[normalizar("torre_das_ilusoes_semanal")] = "torre_das_ilusoes"

# O rótulo é "Fragmento do Vazio Disperso" (com "do") e a coluna do banco é
# "fragmento_vazio_disperso" (sem) — o alias junta os dois.
ALIASES[normalizar("Fragmento do Vazio Disperso")] = "fragmento_vazio_disperso"

# O rótulo é "Nível do Chaser" (com "do") e a coluna do banco é
# "nivel_chaser" (sem) — o alias junta os dois.
ALIASES[normalizar("Nível do Chaser")] = "nivel_chaser"

# Status do personagem (15.1): os rótulos têm "%" e palavras a mais que a
# coluna do banco ("Dano nas Costas %" -> "dano_costas").
ALIASES[normalizar("Acerto Crítico %")] = "critico"
ALIASES[normalizar("Dano Crítico %")] = "dano_critico"
ALIASES[normalizar("Dano nas Costas %")] = "dano_costas"

# Coleção de cartas (15.4): "Coleção de Cartas" -> "colecao_cartas"
ALIASES[normalizar("Coleção de Cartas")] = "colecao_cartas"


def obter_opcoes(aba, coluna):
    """Lista de opções (dropdown) da coluna, ou None se for campo livre."""
    return OPCOES.get(canonizar_aba(aba), {}).get(coluna_banco(coluna))


# ---------------------------------------------------------------------------
# DADOS GERADOS DA PLANILHA
# ---------------------------------------------------------------------------
# Os 25 personagens (slots) que toda conta recebe automaticamente.
PERSONAGENS = ["Elesis", "Lire", "Arme", "Lass", "Ryan", "Ronan", "Amy", "Jin", "Sieghart", "Mari", "Dio", "Zero", "Rey", "Lupus", "Lin", "Azin", "Holy", "Edel", "Veigas", "Decane", "Ai", "Kallia", "Uno", "Iris", "Ereb"]

# Dropdowns por aba: {coluna_normalizada: [opções...]}
# Colunas ausentes (Poder, Vazio Uni., Vazio Apo., Nome) são campos livres.
OPCOES = {
    "Geral": {
        "torredasilusoes": ["1 / 30", "2 / 30", "3 / 30", "4 / 30", "5 / 30", "6 / 30", "7 /30", "8 / 30", "9 /30", "10 / 30", "11 / 30", "12 / 30", "13 / 30", "14 /30", "15 / 30", "16 / 30", "17 / 30", "18 / 30", "19 / 30", "20 / 30", "21 / 30", "22 / 30", "23 / 30", "24 / 30", "25 / 30", "26 / 30", "27 /30", "28 / 30", "29 / 30", "30 / 30"],
        "libertacao": ["FALSO", "VERDADEIRO", "INEXISTENTE"],
        # A tela de EDICAO usa as listas do usuario (14/11), que ficam em
        # janela_personagem.OPCOES_DESPERTAR_* / OPCOES_LIBERTACAO_*:
        #   Despertar Núcleos -> 0/13 ... 13/13 (sem o "1/9 ... 9/9" que a
        #   planilha tinha); Despertar Épicos+ -> 0/9 ... 9/9; Libertação
        #   Núcleos -> 0/9 ... 9/9 e Épicos+ -> 0/4 ... 4/4.
        "nucleo": ["0 / 13", "1 / 13", "2 / 13", "3 / 13", "4 / 13", "5 / 13", "6 / 13", "7 / 13", "8 / 13", "9 / 13", "10 / 13", "11 / 13", "12 / 13", "13 / 13", "1 / 9", "2 / 9", "3 / 9", "4 / 9", "5 / 9", "6 / 9", "7 / 9", "8 / 9", "9 / 9"],
        "nucleosepicos": ["0 / 13", "1 / 13", "2 / 13", "3 / 13", "4 / 13", "5 / 13", "6 / 13", "7 / 13", "8 / 13", "9 / 13", "10 / 13", "11 / 13", "12 / 13", "13 / 13"],
    },
    "Peças (Void)": {
        "arma": ["FALSO", "VERDADEIRO"],
        "luvas": ["FALSO", "VERDADEIRO"],
        "cota": ["FALSO", "VERDADEIRO"],
        "botas": ["FALSO", "VERDADEIRO"],
        "capa": ["FALSO", "VERDADEIRO"],
        "calca": ["FALSO", "VERDADEIRO"],
        "elmo": ["FALSO", "VERDADEIRO"],
        "escudos": ["FALSO", "VERDADEIRO"],
        "asas": ["FALSO", "VERDADEIRO"],
        "facas": ["FALSO", "VERDADEIRO"],
        "mascara": ["FALSO", "VERDADEIRO"],
        "diadema": ["FALSO", "VERDADEIRO"],
    },
    "Acessórios Título": {
        "anel": ["Anel do Ciclo Infinito", "Promessa Incumprível III", "Anel do Infinito III", "Anel do Infinito II", "Anel do Infinito I", "Anel do Harkyon", "Anel do Piu Piu"],
        "brinco": ["Brinco do Outro Mundo do Caos", "Brinco da Dimensão Lendário", "Brinco da Dimensão Épico", "Brinco da Dimensão Raro", "Brinco do Piu Piu"],
        "piercing": ["Piercing do Outro Mundo do Caos", "Piercing da Dimensão Lendário", "Piercing da Dimensão Épico", "Piercing da Dimensão Raro", "Piercing do Piu Piu"],
        "tornozeleira": ["Outra", "Eternidade", "Harmonia", "Consolação", "Escuridão", "Apocalipse"],
        "titulo": ["Origem do Caos", "Renak", "Portador da Grande Coragem", "Aquele que Superou a Morte", "( Verdadeiro ) Iluminador Abissal", "O Sacrifício dos 12 Discípulos Escolhidos", "Aniquilador do Vazio", "Aquele que Consome o Caos", "Fim de Uma Noite Tranquila", "Apocalipse do Mundo", "O Dia do Julgamento", "Outro"],
    },
    "Semanais": {
        "fornalhainfernal": ["Falso", "Verdadeiro"],
        "altardarunha": ["Falso", "Verdadeiro"],
        "torredasilusoes": ["Falso", "Verdadeiro"],
        "void123": ["Falso", "Verdadeiro"],
        "void4": ["Falso", "Verdadeiro"],
        "caminhoabissal": ["Falso", "Verdadeiro"],
        "terradojulgamento": ["Falso", "Verdadeiro"],
    },
}


# ---------------------------------------------------------------------------
# Opcoes que NAO vem da planilha (acrescentadas depois)
# ---------------------------------------------------------------------------
# Colar (15.5, regra do usuario em 24/11): do mais forte ao mais fraco
OPCOES["Acessórios Título"]["colar"] = [
    "Colar do Julgamento Radiante ( Fogo Infernal )",
    "Outro",
]

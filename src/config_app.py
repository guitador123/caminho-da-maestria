# -*- coding: utf-8 -*-
"""
Constantes da tela principal (filtros, abas, rotulos, caminhos).
"""

import caminhos

# (chave, rotulo) de cada opcao dos filtros
# ⚠ as chaves aqui tem que ser IGUAIS as de card_personagem.DUNGEONS
# (normalizadas: sem acento, sem espaco e sem underscore). Com o
# underscore a opcao nunca era encontrada nos dados e o filtro nao
# filtrava nada.
FILTRO_MAZMORRAS = [
    ("void123", "Vazio 1, 2 e 3"),
    ("void4", "Vazio 4"),
    ("caminhoabissal", "Caminho Abissal"),
    ("torredasilusoes", "Torre das Ilusões"),
]

FILTRO_VOID = [
    ("vazio_uni", "Vazio Unificado"),
    ("vazio_apo", "Vazio Apocalipse"),
]

FILTRO_PROGRESSO = [
    ("despertar", "Não completou o despertar"),
    ("libertacao", "Não completou a libertação"),
]

# Modos da Missao Rapida (apenas UM por vez)
MODO_MISSAO_JANELA = "janela"   # o painel flutuante marca as missoes

MODO_MISSAO_CARD = "card"      # clicar no chip do card marca

# Nivel do Chaser: UM valor por conta (todos os personagens). Antes era uma
# constante; agora vem do banco (coluna user_characters.nivel_chaser) e pode
# ser alterado na tela principal.
NIVEL_CHASER_PADRAO = 385
NIVEL_CHASER_MAXIMO = 999       # o nivel maximo do jogo

# Colecao de cartas (15.4): tambem UM valor por conta, de 0 a 2500
# (coluna user_characters.colecao_cartas).
COLUNA_COLECAO = "Coleção de Cartas"
COLECAO_CARTAS_MAXIMO = 2500

COLUNA_NIVEL = "Nível do Chaser"

# Abas de dados conhecidas (chaves de self.dfs)
ABA_GERAL = "Geral"

ABA_PECAS = "Peças (Void)"

ABA_ACESSORIOS = "Acessórios Título"

ABA_SEMANAIS = "Semanais"

# Rotulos amigaveis para as colunas do banco (chave normalizada -> rotulo)
ROTULOS_COLUNAS = {
    "charactername": "Nome",
    "poder": "Poder",
    "torredasilusoes": "Torre Das Ilusões",
    "vaziouni": "Vazio Uni.",
    "vazioapo": "Vazio Apo.",
    "libertacao": "Libertação",
    "nucleo": "Núcleo",
    "nucleosepicos": "Núcleos Épicos+",
    "arma": "Arma",
    "asas": "Asas",
    "botas": "Botas",
    "calca": "Calça",
    "capa": "Capa",
    "cota": "Cota",
    "elmo": "Elmo",
    "escudos": "Escudos",
    "facas": "Facas",
    "luvas": "Luvas",
    "mascara": "Máscara",
    "diadema": "Diadema",
    "anel": "Anel",
    "brinco": "Brinco",
    "piercing": "Piercing",
    "tornozeleira": "Tornozeleira",
    "titulo": "Título",
    "fornalhainfernal": "Fornalha Infernal",
    "altardarunha": "Altar da Ruína",
    "void123": "Void ( 1, 2 e 3 )",
    "void4": "Void 4",
    "caminhoabissal": "Caminho Abissal",
    "terradojulgamento": "Terra do Julgamento",
    # campos novos (13/11) — ATENCAO: a chave e o nome normalizado da COLUNA
    # do banco ("fragmento_vazio_disperso" -> "fragmentovaziodisperso")
    "nucleosdimensionais": "Núcleos Dimensionais",
    "fragmentovaziodisperso": "Fragmento do Vazio Disperso",
    "libertacaonucleos": "Libertação Núcleos",
    "libertacaoepicos": "Libertação Épicos+",
    "nivelchaser": "Nível do Chaser",
    # status do personagem (15.1)
    "ataque": "Ataque",
    "ataqueespecial": "Ataque Especial",
    "critico": "Acerto Crítico %",
    "danocritico": "Dano Crítico %",
    "danocostas": "Dano nas Costas %",
    # colecao de cartas da conta (15.4)
    "colecaocartas": "Coleção de Cartas",
    "colar": "Colar",                     # 15.5
    # as cartas de cada equipamento do Void (15.3)
    "cartasarma": "Cartas Arma",
    "cartasluvas": "Cartas Luvas",
    "cartascota": "Cartas Cota",
    "cartasbotas": "Cartas Botas",
    "cartascapa": "Cartas Capa",
    "cartascalca": "Cartas Calça",
    "cartaselmo": "Cartas Elmo",
    # a pedra de cada equipamento do Void (16)
    "pedraarma": "Pedra Arma",
    "pedraluvas": "Pedra Luvas",
    "pedracota": "Pedra Cota",
    "pedrabotas": "Pedra Botas",
    "pedracapa": "Pedra Capa",
    "pedracalca": "Pedra Calça",
    "pedraelmo": "Pedra Elmo",
    # o andar do Void marcado pela Missao Rapida (17)
    "void123andar": "Void (1, 2 e 3) Andar",
    "void4andar": "Void 4 Andar",
}

BASE_DIR = caminhos.app_dir()

BACKGROUND_PATH = caminhos.fundo_principal()

EXCEL_DEFAULT = caminhos.planilha_padrao()

DB_FILE = caminhos.banco_sqlite()

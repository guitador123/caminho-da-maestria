# -*- coding: utf-8 -*-
"""
Funcoes puras sobre os dados das abas (dataframes, colunas, valores).

Sem nada de Tk: dá para testar sem abrir janela.
"""

import os
import re
from config_app import NIVEL_CHASER_MAXIMO, ROTULOS_COLUNAS
from opcoes import coluna_banco
from supabase_db import COLUNAS


def _mesmo_arquivo(a, b):
    """True se os dois caminhos apontam para o mesmo arquivo."""
    try:
        return (os.path.normcase(os.path.abspath(a))
                == os.path.normcase(os.path.abspath(b)))
    except (TypeError, ValueError):
        return False


def _colunas_conhecidas(df, logica):
    """Colunas do dataframe que existem de verdade na tabela do banco."""
    if df is None or df.empty:
        return []
    permitidas = {coluna_banco(c) for c in COLUNAS.get(logica, [])}
    if logica == "semanais":
        permitidas.add(coluna_banco("torre_das_ilusoes"))
    if logica == "personagens":
        permitidas.add(coluna_banco("nivel_chaser"))
        permitidas.add(coluna_banco("colecao_cartas"))
    achadas = []
    for coluna in df.columns:
        if coluna in ("Nome", "id", "character_id"):
            continue
        if coluna_banco(coluna) in permitidas:
            achadas.append(coluna)
    return achadas


def _rotular_colunas(df):
    """Troca os nomes do banco (snake_case) pelos rotulos da planilha."""
    if df is None or df.empty:
        return df
    troca = {}
    for coluna in df.columns:
        rotulo = ROTULOS_COLUNAS.get(coluna_banco(coluna))
        if rotulo and coluna != rotulo:
            troca[coluna] = rotulo
    return df.rename(columns=troca) if troca else df


def _verdadeiro(valor) -> bool:
    """'VERDADEIRO' / 'Verdadeiro' / True / 1 -> True."""
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    texto = str(valor).strip().lower()
    return texto in ("verdadeiro", "true", "1", "t", "sim", "x")


# "618.002" e "1.234.567": ponto de MILHAR (como o card mostra o Ataque
# Total). Sem isso "618.002" virava 618 e o personagem ia para o fim da
# lista. "618002.0" (como vem do Excel) continua sendo decimal.
_MILHAR = re.compile(r"^[+-]?[0-9]{1,3}(\.[0-9]{3})+$")


def _num(valor, padrao=0):
    """Converte para int (aceita None, '', texto e ponto de milhar)."""
    if valor is None or valor == "":
        return padrao
    if isinstance(valor, str):
        texto = valor.strip().replace(" ", "")
        if _MILHAR.match(texto):
            texto = texto.replace(".", "")
        valor = texto
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return padrao


def _ordenar_colunas(df):
    """Coloca 'Nome' como PRIMEIRA coluna e move 'id'/'character_id' para o FIM."""
    cols = list(df.columns)
    internas = [c for c in ("id", "character_id") if c in cols]
    if "Nome" in cols and cols[0] == "Nome" and not internas:
        return df
    nome = ["Nome"] if "Nome" in cols else []
    meio = [c for c in cols if c not in internas and c != "Nome"]
    return df[nome + meio + internas]


def _coluna_dungeon_semanal(df, chave):
    """Coluna de uma dungeon SEMANAL no dataframe.

    A Torre das Ilusoes semanal esta no banco como
    "torre_das_ilusoes_semanal", mas a chave do app e
    "torredasilusoes" - sem esta equivalencia a Torre nunca era
    encontrada (e por isso o filtro dela nao filtrava nada).
    """
    coluna = _coluna_no_df(df, chave)
    if coluna:
        return coluna
    from opcoes import mesmo_dado
    for coluna_df in (df.columns if df is not None else ()):
        if mesmo_dado(coluna_df, chave):
            return coluna_df
    return None


def _coluna_no_df(df, chave):
    """Descobre a coluna real do dataframe que corresponde a chave do banco.

    Ex.: chave 'caminho_abissal' encontra 'Caminho Abissal' na planilha e
    'caminho_abissal' no Supabase (comparacao normalizada).
    """
    if df is None or df.empty:
        return None
    alvo = coluna_banco(chave)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None


DISTINTIVO_MAXIMO = 900       # o ultimo distintivo (cl900.png)


def progresso_exp(nivel):
    """A barra de EXP do perfil: (percentual, proximo distintivo).

    Os distintivos mudam a cada 100 niveis (1-99, 100-199, 200-299...): o
    percentual e quanto ja andou ate o proximo. Nivel 5 -> 5% (faltam 95
    para o 100); 150 -> 50%. O ultimo distintivo e o do 900: dali em diante
    nao ha proximo (None) e a barra vai de 0% (900) a 100% (999, o maximo).
    """
    try:
        n = int(float(nivel or 0))
    except (TypeError, ValueError):
        n = 0
    n = min(NIVEL_CHASER_MAXIMO, max(0, n))
    if n >= DISTINTIVO_MAXIMO:
        faixa = NIVEL_CHASER_MAXIMO - DISTINTIVO_MAXIMO
        return (n - DISTINTIVO_MAXIMO) * 100.0 / faixa, None
    return float(n % 100), (n // 100 + 1) * 100


# ------------------------------------------------- status do personagem --
# (item 15.1) Ataque, Ataque Especial e os 3 percentuais.
STATUS_PERSONAGEM = [
    # (chave no card, coluna do banco, rotulo da janela, tipo)
    ("ataque", "ataque", "Ataque", "numero"),
    ("ataque_especial", "ataque_especial", "Ataque Especial", "numero"),
    ("critico", "critico", "Acerto Crítico %", "percentual"),
    ("dano_critico", "dano_critico", "Dano Crítico %", "percentual"),
    ("dano_costas", "dano_costas", "Dano nas Costas %", "percentual"),
]


def _decimal(valor, padrao=0.0):
    """'35,25' / '35.256%' / 35.256 -> 35.25 (ate 2 casas, CORTANDO)."""
    from supabase_db import decimal_2
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        return padrao
    numero = decimal_2(valor)
    return padrao if numero is None else numero


def soma_no_milhar(ataque, especial):
    """Ataque + Ataque Especial "no milhar", SEM arredondar.

    So conta o milhar e poe um ponto antes do ultimo digito:
    20.000 + 20.000 = 40.000 -> 40 -> "4.0"; 45.990 -> "4.5";
    123.000 -> "12.3"; 9.999 -> "0.9".
    """
    total = max(0, _num(ataque)) + max(0, _num(especial))
    milhares = total // 1000
    return f"{milhares // 10}.{milhares % 10}"


def _virgula(numero, casas):
    """35.5 -> '35,5' (sem zeros sobrando no fim)."""
    texto = f"{numero:.{casas}f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",")


def abreviar_ataque(valor):
    """O valor curto da faixa do card: 850, '20k', '20,5k', '123k',
    '1,2M'. Corta, nao arredonda (19.990 -> '19,9k')."""
    n = max(0, _num(valor))
    if n < 1000:
        return str(n)
    if n < 100_000:
        return _virgula((n // 100) / 10, 1) + "k"
    if n < 1_000_000:
        return f"{n // 1000}k"
    return _virgula((n // 100_000) / 10, 1) + "M"


def formatar_percentual(valor):
    """45 -> '45%'; 35.25 -> '35,25%'; 180.5 -> '180,5%'."""
    return _virgula(_decimal(valor), 2) + "%"


def formatar_decimal(valor):
    """Para o campo da janela: 35.25 -> '35,25'; 45.0 -> '45'."""
    return _virgula(_decimal(valor), 2)


# ------------------------------------------------------ varios titulos --
# (item 15.2) Um personagem pode ter varios titulos. Ficam todos na mesma
# coluna `titulo` do banco, separados por " | ", do mais forte ao mais
# fraco (a ordem do dropdown da planilha). "Outro" nao conta como titulo.
SEPARADOR_TITULOS = " | "
TITULO_IGNORADO = "outro"


def titulos_do_jogo():
    """Os titulos do jogo, do mais forte ao mais fraco (sem "Outro")."""
    from opcoes import OPCOES, normalizar
    lista = OPCOES.get("Acessórios Título", {}).get("titulo", [])
    return [t for t in lista if normalizar(t) != TITULO_IGNORADO]


def ler_titulos(valor):
    """'Renak | Origem do Caos' -> ['Origem do Caos', 'Renak'].

    Ordena do mais forte ao mais fraco, tira repetidos, vazios e "Outro".
    Um titulo fora da lista (digitado em versao antiga) vai para o fim.
    """
    from opcoes import normalizar
    if valor is None or not isinstance(valor, (str, list, tuple)):
        return []
    partes = valor.split("|") if isinstance(valor, str) else list(valor)
    ordem = {normalizar(t): (i, t) for i, t in enumerate(titulos_do_jogo())}
    vistos, conhecidos, outros = set(), [], []
    for parte in partes:
        texto = str(parte).strip()
        chave = normalizar(texto)
        if not chave or chave == TITULO_IGNORADO or chave in vistos:
            continue
        vistos.add(chave)
        if chave in ordem:
            conhecidos.append(ordem[chave])
        else:
            outros.append(texto)
    return [t for _i, t in sorted(conhecidos)] + outros


def juntar_titulos(titulos):
    """['Renak', 'Origem do Caos'] -> 'Origem do Caos | Renak'."""
    return SEPARADOR_TITULOS.join(ler_titulos(list(titulos or [])))


# --------------------------------------------- cartas do Void (15.3) --
# Cada um dos 7 equipamentos do Void tem 4 slots; cada slot aceita uma das
# cartas da lista do equipamento (do mais forte ao mais fraco). No banco,
# uma coluna de texto por equipamento (cartas_<peca>) com os 4 slots
# separados por "|": 'Ataque +555|Ataque +530||Outra' (slot vazio = vazio).
SLOTS_CARTAS = 4
CARTA_OUTRA = "Outra"
_CRITICO = "Dano Crítico +31,5%"
CARTAS_VOID = {
    "arma": [f"{_CRITICO}/Ataque Especial +530",
             f"{_CRITICO}/Ataque Especial +265",
             _CRITICO, "Dano Crítico +28,75%", CARTA_OUTRA],
    "luvas": [f"{_CRITICO}/Ataque Especial +530",
              f"{_CRITICO}/Ataque Especial +265",
              _CRITICO, "Dano Crítico +28,75%", CARTA_OUTRA],
    "cota": ["Ataque +555", "Ataque +530", "Ataque +515", "Ataque +507",
             CARTA_OUTRA],
    # +835 entrou no lugar do +765 (27/11)
    "botas": ["Ataque Especial +835", "Ataque Especial +785",
              "Ataque Especial +774", "Ataque Especial +772", CARTA_OUTRA],
    "capa": ["Ataque +555", "Ataque +530", "Ataque +515", "Ataque +507",
             CARTA_OUTRA],
    "calca": ["Ataque Especial +835", "Ataque Especial +785",
              "Ataque Especial +774", "Ataque Especial +772", CARTA_OUTRA],
    "elmo": ["Ataque +100", CARTA_OUTRA],
}
# a ordem do card (a mesma da lista de pecas do card)
PECAS_COM_CARTAS = ["arma", "luvas", "cota", "botas", "capa", "calca", "elmo"]


def coluna_cartas(peca):
    """'cota' -> 'cartas_cota' (a coluna do banco)."""
    return f"cartas_{peca}"


def ler_cartas(valor):
    """'Ataque +555||Outra' -> ['Ataque +555', '', 'Outra', ''] (sempre 4)."""
    if not isinstance(valor, str):
        return [""] * SLOTS_CARTAS
    slots = [parte.strip() for parte in valor.split("|")][:SLOTS_CARTAS]
    return slots + [""] * (SLOTS_CARTAS - len(slots))


def juntar_cartas(slots):
    """['Ataque +555', '', 'Outra', ''] -> 'Ataque +555||Outra|'.
    Todos vazios -> '' (nada equipado)."""
    lista = [str(s or "").strip() for s in list(slots or [])][:SLOTS_CARTAS]
    lista += [""] * (SLOTS_CARTAS - len(lista))
    return "|".join(lista) if any(lista) else ""


def estado_da_carta(carta):
    """O quadradinho do card: None (slot vazio), 'outra' (vermelho) ou
    'status' (verde: a carta da status)."""
    texto = str(carta or "").strip()
    if not texto:
        return None
    if texto.lower() == CARTA_OUTRA.lower():
        return "outra"
    return "status"


# --------------------------------------------- pedra do Void (item 16) --
# Cada equipamento tem uma pedra de +0 a +18 com um status (2 opcoes por
# peca: a FRACA primeiro, a FORTE depois). Toda pedra tem status, e o
# nivel so vale junto com ele. No banco: pedra_<peca> = '18|10% Dano Crítico'.
NIVEL_PEDRA_MAXIMO = 18
PEDRAS_VOID = {
    "arma": ["7% Dano Crítico", "10% Dano Crítico"],
    "luvas": ["15% Dano no fatal", "20% Dano no fatal"],
    "cota": ["Ataque Especial +400", "Ataque Especial +800"],
    "botas": ["Ataque Especial +400", "Ataque Especial +800"],
    "capa": ["Ataque +300", "Ataque +600"],
    "calca": ["Recuperação de MP 7%", "Recuperação de MP 10%"],
    "elmo": ["Ataque +300", "Ataque +600"],
}


def coluna_pedra(peca):
    """'arma' -> 'pedra_arma' (a coluna do banco)."""
    return f"pedra_{peca}"


def ler_pedra(valor):
    """'18|10% Dano Crítico' -> (18, '10% Dano Crítico').
    Vazio ou quebrado -> (None, '') (pedra nao informada)."""
    if not isinstance(valor, str) or "|" not in valor:
        return None, ""
    nivel, status = valor.split("|", 1)
    try:
        numero = int(nivel.strip().lstrip("+"))
    except ValueError:
        return None, ""
    if not 0 <= numero <= NIVEL_PEDRA_MAXIMO or not status.strip():
        return None, ""
    return numero, status.strip()


def validar_pedra(nivel, status):
    """Mensagem de erro, ou None se a pedra pode ser gravada.
    Nada escolhido = sem pedra (vale); so um dos dois = erro."""
    tem_nivel = nivel is not None and str(nivel).strip() != ""
    tem_status = bool(str(status or "").strip())
    if not tem_nivel and not tem_status:
        return None
    if not tem_status:
        return "Escolha o status da pedra junto com o nível."
    if not tem_nivel:
        return "Escolha o nível da pedra junto com o status."
    try:
        numero = int(str(nivel).strip().lstrip("+"))
    except ValueError:
        return "O nível da pedra é um número de +0 a +18."
    if not 0 <= numero <= NIVEL_PEDRA_MAXIMO:
        return "O nível da pedra vai de +0 a +18."
    return None


def juntar_pedra(nivel, status):
    """(18, '10% Dano Crítico') -> '18|10% Dano Crítico'; sem pedra -> ''.
    Pedra incompleta levanta ValueError (o status e obrigatorio)."""
    erro = validar_pedra(nivel, status)
    if erro:
        raise ValueError(erro)
    if nivel is None or str(nivel).strip() == "":
        return ""
    return f"{int(str(nivel).strip().lstrip('+'))}|{str(status).strip()}"


def cor_da_pedra(nivel):
    """A cor do chip pelo NIVEL da pedra (regra do usuario, 24/11):
    +18 vermelho, +17 dourado, +11 a +16 verde, +0 a +10 cinza; None =
    pedra nao informada."""
    if nivel is None:
        return None
    if nivel >= 18:
        return "vermelho"
    if nivel == 17:
        return "dourado"
    if nivel >= 11:
        return "verde"
    return "cinza"


def status_forte(peca, status):
    """O status e o MAIS FORTE da pedra da peca? (o ultimo da lista: +600,
    +800, 10%, 20%...). O card marca com um pontinho no chip."""
    opcoes = PEDRAS_VOID.get(peca, [])
    return bool(opcoes) and status == opcoes[-1]


# ------------------------------------- Void na Missao Rapida (item 17) --
# Marcar o Void na Missao Rapida pergunta quantos andares (1F, 2F, 3F) e
# soma no contador do personagem. O andar fica guardado com a SEMANA
# ("3F|2026-11-25") para desmarcar desfazer a soma; de outra semana, nao
# desfaz (o reset de quarta ja zerou a dungeon).
ANDARES_VOID = {"1F": 4, "2F": 8, "3F": 10}
# dungeon (chave do app) -> (coluna do contador no banco, rotulo)
VOID_CONTADOR = {
    "void123": ("vazio_uni", "Void Unificado"),
    "void4": ("vazio_apo", "Void Apocalipse"),
}


def coluna_andar(chave):
    """'void123' -> 'void123_andar' (a coluna do banco, em user_semanais)."""
    return f"{chave}_andar"


def marca_andar(andar, semana):
    """('3F', date(2026, 11, 25)) -> '3F|2026-11-25'."""
    if andar not in ANDARES_VOID:
        raise ValueError(f"andar invalido: {andar!r}")
    return f"{andar}|{semana.isoformat() if hasattr(semana, 'isoformat') else semana}"


def andar_da_semana(valor, semana):
    """O andar guardado, se for DESTA semana ('3F'); senao None."""
    if not isinstance(valor, str) or "|" not in valor:
        return None
    andar, data = valor.split("|", 1)
    atual = semana.isoformat() if hasattr(semana, "isoformat") else str(semana)
    if andar.strip() in ANDARES_VOID and data.strip() == atual:
        return andar.strip()
    return None


def novo_contador(atual, andar=None, desfazer=None):
    """O contador depois de marcar `andar` (soma) ou desmarcar com o
    `desfazer` guardado (subtrai, sem ficar negativo)."""
    valor = max(0, _num(atual))
    if andar:
        valor += ANDARES_VOID[andar]
    if desfazer:
        valor = max(0, valor - ANDARES_VOID[desfazer])
    return valor

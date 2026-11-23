# -*- coding: utf-8 -*-
"""
Filtros e ordem dos cards de personagem (logica pura, sem Tk).

    dados = dados_filtro(df_geral, df_semanais, "Elesis")
    visiveis = filtrar_e_ordenar(nomes, {nome: dados...},
                                 mazmorras={"caminhoabissal"})

Regras:
  - Ordem: do mais forte para o mais fraco, pelo Ataque Total. Com
    "Ordenar por Void" marcado, pela soma dos Void escolhidos. Empate
    mantem a ordem original (alfabetica, como vem do banco).
  - "Nao fez estas masmorras": fica quem ainda NAO concluiu pelo menos uma
    das dungeons marcadas (ex.: Caminho Abissal ou Torre das Ilusoes desta
    semana).
  - "Progresso incompleto": fica quem esta incompleto em TODOS os marcados.

Atencao a Torre das Ilusoes: o nome aparece nas DUAS abas. Na Geral e o
andar do mes ("30 / 30"); na Semanais e "fez esta semana"
(Verdadeiro/Falso). O filtro de masmorras usa SEMPRE a da Semanais.
"""

from card_personagem import DUNGEONS as DUNGEONS_CARD, _fracao
from dados_app import _coluna_dungeon_semanal, _num, _verdadeiro
from opcoes import normalizar


def _linha(df, nome):
    """A linha do personagem como dict ({} se nao houver)."""
    if df is None or df.empty or "Nome" not in df.columns:
        return {}
    achada = df[df["Nome"].astype(str) == str(nome)]
    if achada.empty:
        return {}
    return achada.iloc[0].to_dict()


def dados_filtro(df_geral, df_semanais, nome):
    """O que os filtros precisam saber de um personagem."""
    geral = _linha(df_geral, nome)
    semanal = _linha(df_semanais, nome)

    # --- void (forca do personagem) ---
    vazio_uni = _num(geral.get("Vazio Uni.") or geral.get("vazio_uni"))
    vazio_apo = _num(geral.get("Vazio Apo.") or geral.get("vazio_apo"))

    # --- masmorras semanais (SEMPRE da aba Semanais) ---
    mazmorras = {}
    for chave, _rotulo in DUNGEONS_CARD:
        coluna = _coluna_dungeon_semanal(df_semanais, chave)
        mazmorras[chave] = (_verdadeiro(semanal.get(coluna))
                            if coluna else False)

    # --- despertar / liberacao ---
    nucleo = _fracao(geral.get("Núcleo") or geral.get("nucleo"))
    epicos = _fracao(geral.get("Núcleos Épicos+")
                     or geral.get("nucleos_epicos"))
    despertar = nucleo[0] == 13 and epicos[0] == 9
    libertacao = False
    if _verdadeiro(geral.get("Libertação") or geral.get("libertacao")):
        lib_nuc = _num(geral.get("Libertação Núcleos")
                       or geral.get("libertacao_nucleos"))
        lib_epi = _num(geral.get("Libertação Épicos+")
                       or geral.get("libertacao_epicos"))
        libertacao = (lib_nuc == 9 and lib_epi == 4)

    return {"vazio_uni": vazio_uni, "vazio_apo": vazio_apo,
            "ataque": _num(geral.get("Poder") or geral.get("poder")),
            "mazmorras": mazmorras, "despertar": despertar,
            "libertacao": libertacao}


def _fez(mazmorras, chave):
    """O personagem ja fez a dungeon `chave` esta semana?"""
    if chave in mazmorras:
        return bool(mazmorras[chave])
    alvo = normalizar(chave)
    for outra, feito in mazmorras.items():
        if normalizar(outra) == alvo:
            return bool(feito)
    return False


def filtrar_e_ordenar(nomes, dados, mazmorras=(), progresso=(),
                      ordem_void=()):
    """Os nomes que passam pelos filtros, do mais forte ao mais fraco."""
    selecionados = list(nomes)

    if mazmorras:
        selecionados = [
            n for n in selecionados
            if any(not _fez((dados.get(n) or {}).get("mazmorras") or {}, c)
                   for c in mazmorras)]

    if progresso:
        selecionados = [
            n for n in selecionados
            if all(not (dados.get(n) or {}).get(c, False) for c in progresso)]

    if ordem_void:
        def forca(nome):
            info = dados.get(nome) or {}
            return sum(info.get(chave, 0) for chave in ordem_void)
    else:
        def forca(nome):
            return (dados.get(nome) or {}).get("ataque", 0)
    return sorted(selecionados, key=forca, reverse=True)

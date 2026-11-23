"""Filtros e ordem dos cards (filtros.py): Ataque Total, Caminho Abissal e
Torre das Ilusoes."""

import pandas as pd
import pytest

from filtros import dados_filtro, filtrar_e_ordenar


def _abas(personagens, nomes_do_banco=False):
    """Monta as abas Geral e Semanais como o app carrega.

    personagens: {nome: (poder, torre_mes, abissal_semana, torre_semana)}
    nomes_do_banco=True usa os nomes crus das colunas (como vem do Supabase
    antes de rotular), com booleanos de verdade.
    """
    geral, semanais = [], []
    for nome, (poder, torre_mes, abissal, torre) in personagens.items():
        geral.append({"Nome": nome, "Poder": poder,
                      "Torre Das Ilusões": torre_mes})
        if nomes_do_banco:
            semanais.append({"Nome": nome, "caminho_abissal": abissal,
                             "torre_das_ilusoes_semanal": torre})
        else:
            semanais.append({
                "Nome": nome,
                "Caminho Abissal": "Verdadeiro" if abissal else "Falso",
                "Torre Das Ilusões": "Verdadeiro" if torre else "Falso"})
    return pd.DataFrame(geral), pd.DataFrame(semanais)


def _visiveis(personagens, **filtros_ligados):
    df_geral, df_sem = _abas(personagens,
                             filtros_ligados.pop("nomes_do_banco", False))
    nomes = list(personagens)
    dados = {n: dados_filtro(df_geral, df_sem, n) for n in nomes}
    return filtrar_e_ordenar(nomes, dados, **filtros_ligados)


CONTA = {
    #          poder     torre do mes  abissal  torre da semana
    "Elesis": (500_000, "30 / 30", True, False),
    "Lire": (900_000, "0 / 30", False, True),
    "Arme": (700_000, "12 / 30", False, False),
    "Lass": (300_000, "30 / 30", True, True),
}


# --------------------------------------------------------------- ordem
def test_ordem_pelo_ataque_total_do_maior_para_o_menor():
    assert _visiveis(CONTA) == ["Lire", "Arme", "Elesis", "Lass"]


def test_empate_mantem_a_ordem_original():
    conta = {"Ai": (0, "", False, False), "Amy": (0, "", False, False),
             "Arme": (10, "", False, False)}
    assert _visiveis(conta) == ["Arme", "Ai", "Amy"]


def test_ataque_com_ponto_de_milhar_ordena_certo():
    conta = {"Elesis": ("618.002", "", False, False),
             "Lire": ("99999", "", False, False)}
    assert _visiveis(conta) == ["Elesis", "Lire"]


def test_ordenar_por_void_usa_a_soma_escolhida():
    df_geral = pd.DataFrame([
        {"Nome": "Elesis", "Poder": 900, "Vazio Uni.": 1, "Vazio Apo.": 1},
        {"Nome": "Lire", "Poder": 100, "Vazio Uni.": 5, "Vazio Apo.": 0}])
    dados = {n: dados_filtro(df_geral, None, n) for n in ("Elesis", "Lire")}
    assert filtrar_e_ordenar(["Elesis", "Lire"], dados,
                             ordem_void={"vazio_uni"}) == ["Lire", "Elesis"]
    assert filtrar_e_ordenar(["Elesis", "Lire"], dados,
                             ordem_void={"vazio_uni", "vazio_apo"}) == \
        ["Lire", "Elesis"]


# ----------------------------------------------------- Caminho Abissal
@pytest.mark.parametrize("nomes_do_banco", [False, True])
def test_filtro_caminho_abissal_mostra_quem_nao_fez(nomes_do_banco):
    assert _visiveis(CONTA, mazmorras={"caminhoabissal"},
                     nomes_do_banco=nomes_do_banco) == ["Lire", "Arme"]


# ------------------------------------------------- Torre das Ilusoes
@pytest.mark.parametrize("nomes_do_banco", [False, True])
def test_filtro_torre_usa_a_semana_e_nao_o_andar_do_mes(nomes_do_banco):
    # Elesis tem 30/30 no MES mas nao fez a torre ESTA SEMANA: aparece.
    # Lire tem 0/30 no mes mas fez esta semana: some.
    assert _visiveis(CONTA, mazmorras={"torredasilusoes"},
                     nomes_do_banco=nomes_do_banco) == ["Arme", "Elesis"]


def test_torre_semanal_e_lida_mesmo_com_o_mesmo_rotulo_da_geral():
    df_geral, df_sem = _abas(CONTA)
    # as duas abas tem a coluna "Torre Das Ilusoes"
    assert "Torre Das Ilusões" in df_geral and "Torre Das Ilusões" in df_sem
    assert dados_filtro(df_geral, df_sem, "Lire")["mazmorras"][
        "torredasilusoes"] is True
    assert dados_filtro(df_geral, df_sem, "Elesis")["mazmorras"][
        "torredasilusoes"] is False


# ------------------------------------------------------- combinacoes
def test_abissal_e_torre_juntos_mostra_quem_falta_qualquer_uma():
    assert _visiveis(CONTA, mazmorras={"caminhoabissal", "torredasilusoes"}) \
        == ["Lire", "Arme", "Elesis"]


def test_personagem_sem_linha_na_semanais_conta_como_nao_fez():
    df_geral, df_sem = _abas(CONTA)
    df_geral = pd.concat([df_geral, pd.DataFrame(
        [{"Nome": "Ronan", "Poder": 1, "Torre Das Ilusões": ""}])])
    nomes = list(CONTA) + ["Ronan"]
    dados = {n: dados_filtro(df_geral, df_sem, n) for n in nomes}
    assert "Ronan" in filtrar_e_ordenar(nomes, dados,
                                        mazmorras={"caminhoabissal"})


@pytest.mark.parametrize("valor, fez", [
    ("Verdadeiro", True), ("VERDADEIRO", True), (True, True), ("sim", True),
    ("Falso", False), (False, False), ("", False), (None, False),
])
def test_valores_aceitos_como_feito(valor, fez):
    df_sem = pd.DataFrame([{"Nome": "Lire", "Caminho Abissal": valor}])
    assert dados_filtro(None, df_sem, "Lire")["mazmorras"][
        "caminhoabissal"] is fez


def test_progresso_incompleto():
    df_geral = pd.DataFrame([
        {"Nome": "Elesis", "Poder": 2, "Núcleo": "13 / 13",
         "Núcleos Épicos+": "9 / 9"},
        {"Nome": "Lire", "Poder": 1, "Núcleo": "5 / 13",
         "Núcleos Épicos+": "0 / 9"}])
    dados = {n: dados_filtro(df_geral, None, n) for n in ("Elesis", "Lire")}
    assert filtrar_e_ordenar(["Elesis", "Lire"], dados,
                             progresso={"despertar"}) == ["Lire"]

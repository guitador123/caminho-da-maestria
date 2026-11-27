"""Testes de INTEGRACAO: os scripts `tests/integracao/teste_*.py`, que precisam do
Supabase (conta de teste) e/ou abrem janelas.

Nao rodam por padrao nem no GitHub Actions. Para rodar (no PC, com o
`.env.teste` ou as variaveis GC_TESTE_EMAIL/GC_TESTE_SENHA):

    python -m pytest -m integracao

Cada script roda num processo proprio e passa se sair com codigo 0.
Todos sao NAO destrutivos (restauram o que mexem). O
`teste_zerar_semanais.py` fica de fora de proposito: se a protecao do
banco quebrar, ele zeraria as semanais de verdade.
"""

import os
import subprocess
import sys

import pytest

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SCRIPTS = [
    # so Supabase
    "teste_rls.py",
    "teste_salvar_atomico.py",
    "teste_integracao.py",
    # Supabase + janela do app
    "teste_salvamento_async.py",
    "teste_acoes.py",
    "teste_edicao_persistencia.py",
    "teste_edicao_supabase.py",
    "teste_nivel_supabase.py",
    "teste_nivel_chaser.py",
    "teste_zerar_dungeons.py",
    "teste_campos_novos.py",
    "teste_status_personagem.py",
    "teste_titulos.py",
    "teste_colecao_cartas.py",
    "teste_colar.py",
    "teste_cartas_void.py",
    "teste_void_andares.py",
    "teste_guias.py",
    "teste_guilda.py",
    "teste_ranking.py",
    "teste_missao_rapida.py",
    "teste_filtros.py",
    "teste_filtro_ao_vivo.py",
    "teste_filtro_rolagem.py",
    "teste_rolagem_suave.py",
    "teste_perfil.py",
    "teste_doacao.py",
    "teste_login_memo.py",
    "teste_versao.py",
    "teste_evolucao.py",
    "teste_offline.py",
    # precisa da chave privada REAL da release (so no PC de quem publica)
    "teste_assinatura.py",
]


def _tem_credenciais():
    return bool(os.environ.get("GC_TESTE_SENHA")) or \
        os.path.exists(os.path.join(RAIZ, ".env.teste"))


@pytest.mark.integracao
@pytest.mark.parametrize("script", SCRIPTS)
def test_script(script):
    if not _tem_credenciais():
        pytest.skip("sem credenciais da conta de teste (.env.teste)")
    resultado = subprocess.run(
        [sys.executable, os.path.join("tests", "integracao", script)],
        cwd=RAIZ, capture_output=True, text=True, encoding="utf-8",
        errors="replace", timeout=600,
        # o filho escreve em UTF-8 (senao o cp1252 do console quebra em
        # caracteres como o "↗" do 9o cartao)
        env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    saida = (resultado.stdout + resultado.stderr).strip()
    assert resultado.returncode == 0, saida[-3000:]

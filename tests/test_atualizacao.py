"""Auto-update (atualizacao.py): versao da release e script de troca."""

import os
import time

import pytest

import atualizacao as a


@pytest.mark.parametrize("tag, esperado", [
    ("v2026.11.17-9008aef", "9008aef"),
    ("v2026.11.23-BC78342", "bc78342"),
    ("v2026.11.23", ""),               # sem sha
    ("v2026.11.23-xyz1234", ""),        # nao e hexadecimal
    ("", ""),
    (None, ""),
])
def test_sha_da_release(tag, esperado):
    assert a._sha_da_release(tag) == esperado


FEED = """<feed>
<entry><link href="https://github.com/x/y/releases/tag/v2026.11.20-aaaaaaa"/>
  <updated>2026-11-20T10:00:00Z</updated></entry>
<entry><link href="https://github.com/x/y/releases/tag/v2026.11.23-bbbbbbb"/>
  <updated>2026-11-23T18:00:00Z</updated></entry>
<entry><link href="https://github.com/x/y/releases/tag/v2026.11.22-ccccccc"/>
  <updated>2026-11-22T09:00:00Z</updated></entry>
</feed>"""


def test_versao_da_release_pega_a_mais_nova(monkeypatch):
    monkeypatch.setattr(a, "_atom", lambda url: FEED)
    assert a._versao_da_release() == "bbbbbbb"


def test_versao_da_release_sem_rede_devolve_vazio_e_registra(monkeypatch):
    def sem_rede(url):
        raise OSError("sem internet")
    monkeypatch.setattr(a, "_atom", sem_rede)
    assert a._versao_da_release() == ""
    assert "ler o feed de releases" in open(a.LOG, encoding="utf-8").read()


@pytest.fixture
def script_de_troca(tmp_path, monkeypatch):
    """Gera o .cmd de troca sem executar nada."""
    monkeypatch.setattr(a.tempfile, "gettempdir", lambda: str(tmp_path))
    monkeypatch.setattr(a, "_app_dir", lambda: r"C:\Programa")

    class _SemExecutar:
        @staticmethod
        def Popen(*args, **kwargs):
            return None
    monkeypatch.setattr(a, "subprocess", _SemExecutar)

    def gerar(**kwargs):
        a._agendar_troca(r"C:\Temp\novos", **kwargs)
        caminho = tmp_path / "cm_trocar_arquivos.cmd"
        return caminho.read_bytes().decode("utf-8")
    return gerar


def test_script_de_troca_espelha_e_preserva_logs_e_login(script_de_troca):
    texto = script_de_troca(limpar=r"C:\Temp\cm_atualizacao_1")
    assert r'robocopy "C:\Temp\novos" "C:\Programa" /MIR' in texto
    for preservado in ("login_prefs.json", "*.log", "*.log.1"):
        assert preservado in texto.split("/XF", 1)[1].split("/NFL")[0]
    assert r'rmdir /s /q "C:\Temp\cm_atualizacao_1"' in texto


def test_script_de_troca_usa_crlf_sem_cr_duplicado(script_de_troca):
    texto = script_de_troca()
    assert "\r\r\n" not in texto
    assert texto.count("\r\n") == texto.count("\n")


def test_script_de_troca_abre_o_programa_mesmo_se_falhar(script_de_troca):
    texto = script_de_troca()
    sucesso, falha = texto.split("\r\n:falhou\r\n", 1)   # o rotulo
    abrir = 'start "" "C:\\Programa\\Caminho da Maestria.exe"'
    assert abrir in sucesso and abrir in falha


def test_script_de_troca_modo_git_nao_copia(script_de_troca):
    texto = script_de_troca(copiar=False, abrir='start "" python app.py')
    assert "robocopy" not in texto
    assert 'start "" python app.py' in texto


def test_limpar_sobras_apaga_so_as_antigas(tmp_path, monkeypatch):
    monkeypatch.setattr(a.tempfile, "gettempdir", lambda: str(tmp_path))
    antiga = tmp_path / "cm_atualizacao_velha"
    nova = tmp_path / "cm_atualizacao_nova"
    outra = tmp_path / "outra_pasta"
    for pasta in (antiga, nova, outra):
        pasta.mkdir()
        (pasta / "arquivo.bin").write_bytes(b"x")
    duas_horas = time.time() - 7200
    os.utime(antiga, (duas_horas, duas_horas))
    os.utime(outra, (duas_horas, duas_horas))

    assert a.limpar_sobras() == 1
    assert not antiga.exists()
    assert nova.exists()          # pode ser uma atualizacao em andamento
    assert outra.exists()         # nao e do app


def test_pasta_do_programa_e_a_raiz_com_o_atalho():
    """No modo fonte, o auto-update (git pull, reabrir) e os arquivos
    locais (login_prefs.json, planilha) usam a RAIZ do projeto, onde fica
    o atalho app_grandchase.py, e nao a pasta src/."""
    import caminhos
    raiz = a._app_dir()
    assert raiz == caminhos.app_dir()
    assert os.path.isfile(os.path.join(raiz, "app_grandchase.py"))
    assert os.path.isdir(os.path.join(raiz, "src"))
    assert os.path.isdir(os.path.join(raiz, "assets"))
    assert a._comando_python().endswith(
        '"' + os.path.join(raiz, "app_grandchase.py") + '"')


FEED_COM_TITULOS = """<feed>
<entry><link href="https://github.com/x/y/releases/tag/v2026.11.23-aaaaaaa"/>
  <title>Caminho da Maestria v2026.11.23-aaaaaaa</title>
  <updated>2026-11-23T10:00:00Z</updated></entry>
<entry><link href="https://github.com/x/y/releases/tag/v2026.11.24-bbbbbbb"/>
  <title>Caminho da Maestria 1.0.0</title>
  <updated>2026-11-24T10:00:00Z</updated></entry>
</feed>"""


@pytest.mark.parametrize("titulo, esperado", [
    ("Caminho da Maestria 1.4.0", "1.4.0"),
    ("Caminho da Maestria 10.20.30", "10.20.30"),
    ("Caminho da Maestria v2026.11.23-053f554", ""),   # release antiga
    ("", ""),
    (None, ""),
])
def test_numero_da_versao(titulo, esperado):
    assert a._numero_da_versao(titulo) == esperado


def test_ultima_release_traz_sha_e_versao(monkeypatch):
    monkeypatch.setattr(a, "_atom", lambda url: FEED_COM_TITULOS)
    assert a.ultima_release() == ("bbbbbbb", "1.0.0")


@pytest.fixture
def modo_exe(monkeypatch):
    monkeypatch.setattr(a, "tem_git", lambda: False)
    monkeypatch.setattr(a, "_atom", lambda url: FEED_COM_TITULOS)


def test_procurar_atualizacao_acha_versao_nova(modo_exe, monkeypatch):
    monkeypatch.setattr(a, "versao_local", lambda: "aaaaaaa1234")
    assert a.procurar_atualizacao() == {"nova": True, "versao": "1.0.0",
                                        "erro": ""}


def test_procurar_atualizacao_ja_na_ultima(modo_exe, monkeypatch):
    monkeypatch.setattr(a, "versao_local", lambda: "bbbbbbb9999")
    assert a.procurar_atualizacao()["nova"] is False


def test_procurar_atualizacao_sem_internet(monkeypatch):
    monkeypatch.setattr(a, "tem_git", lambda: False)
    monkeypatch.setattr(a, "versao_local", lambda: "aaaaaaa")

    def sem_rede(url):
        raise OSError("sem internet")
    monkeypatch.setattr(a, "_atom", sem_rede)
    resultado = a.procurar_atualizacao()
    assert resultado["nova"] is False and resultado["erro"]


def test_procurar_atualizacao_nao_instala_nada(modo_exe, monkeypatch):
    def proibido(*args, **kwargs):
        raise AssertionError("so verificar: nao pode aplicar")
    monkeypatch.setattr(a, "aplicar_atualizacao", proibido)
    monkeypatch.setattr(a, "_agendar_troca", proibido)
    monkeypatch.setattr(a, "versao_local", lambda: "aaaaaaa")
    a.procurar_atualizacao()

# -*- coding: utf-8 -*-
"""
A chave Pix do projeto e o payload "copia e cola".

A **fonte da verdade e o `assets/doacao/pix.txt`**: o app le esse arquivo
a cada abertura e monta o payload na hora. Assim, trocar a chave e so
editar o arquivo (e reiniciar o app) \u2014 nao precisa rodar nenhum
script nem rebuildar o `.exe`.

O `assets/doacao/gerar_qr.py` continua existindo para quem quiser
salvar o QR como PNG (e para conferir o CRC), mas o app **nao depende**
dele: ele gera o QR Code em memoria.

    chave -> monta_payload() -> payload "copia e cola" + QR Code
"""

import io
import os
import re

import caminhos
from registro import falha

PASTA = "doacao"


def pasta_doacao():
    """A pasta assets/doacao (funciona no fonte e no .exe)."""
    return os.path.join(caminhos.assets_dir(), "assets", PASTA)


def _ler(linhas):
    """Ignora as linhas de comentario (comecam com #) e as vazias."""
    return [linha.strip() for linha in linhas
            if linha.strip() and not linha.strip().startswith("#")]


_CHAVE_ALEATORIA = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}"
    r"-[0-9a-fA-F]{12}$")


def normalizar_chave(bruto):
    """Deixa a chave no formato que o Pix aceita.

    - **e-mail**: so sem espacos (`fulano@email.com`);
    - **chave aleatoria** (EVP): como esta;
    - **telefone**: so os digitos, com o `+` do DDI na frente
      (`+55 (19) 98146-6471` vira `+5519981466471`).
    """
    texto = bruto.strip()
    if not texto:
        return ""
    if "@" in texto:                       # e-mail
        return texto.replace(" ", "")
    if _CHAVE_ALEATORIA.match(texto):      # chave aleatoria
        return texto
    digitos = "".join(caractere for caractere in texto if caractere.isdigit())
    if not digitos:
        return texto
    return ("+" + digitos) if texto.startswith("+") else digitos


def chave():
    """A chave Pix (e-mail, telefone ou chave aleatoria), ja normalizada."""
    caminho = os.path.join(pasta_doacao(), "pix.txt")
    try:
        with io.open(caminho, "r", encoding="utf-8") as arquivo:
            linhas = _ler(arquivo)
        return normalizar_chave(linhas[0]) if linhas else ""
    except FileNotFoundError:
        return ""
    except Exception:
        falha("ler a chave Pix")
        return ""


def nome():
    """O nome que aparece no recibo."""
    caminho = os.path.join(pasta_doacao(), "nome.txt")
    try:
        with io.open(caminho, "r", encoding="utf-8") as arquivo:
            linhas = _ler(arquivo)
        return linhas[0] if linhas else "Caminho da Maestria"
    except FileNotFoundError:
        return "Caminho da Maestria"
    except Exception:
        falha("ler o nome do Pix")
        return "Caminho da Maestria"


def _crc16(payload):
    """CRC16-CCITT (0x1021) usado no payload do Pix."""
    crc = 0xFFFF
    for byte in payload.encode("utf-8"):
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return "%04X" % crc


def monta_payload(chave_pix, nome_pix, cidade="SAO PAULO", valor=None,
                  txid="***", gui="BR.GOV.BCB.PIX"):
    """Monta o payload "copia e cola" (BR Code) de um Pix estatico.

    Segue o manual do BR Code do Banco Central:
      00 versao | 26 conta (00 = GUI, 01 = chave) | 52 categoria |
      53 moeda (986 = real) | 54 valor (opcional) | 58 pais | 59 nome |
      60 cidade | 62 dados extras (05 = identificador) | 63 CRC16

    A chave vai normalizada (telefone so com + e digitos), senao o banco
    de quem paga nao acha a conta.

    Antes (ate 24/11/2026) havia um campo "01" invalido (= "26") e faltava
    o "00" do GUI dentro do campo 26: o payload gerado aqui nao era um Pix
    valido. O app usa o payload pronto (pix_payload.txt), entao o QR da
    doacao nao foi afetado; so o qr_pix.png (reserva) estava quebrado.
    """
    def campo(tag, conteudo):
        return "%s%02d%s" % (tag, len(conteudo), conteudo)

    conta = campo("00", gui) + campo("01", normalizar_chave(chave_pix))
    partes = [
        campo("00", "01"),
        campo("26", conta),
        campo("52", "0000"),
        campo("53", "986"),
    ]
    if valor:
        partes.append(campo("54", "%.2f" % valor))
    partes.append(campo("58", "BR"))
    partes.append(campo("59", nome_pix[:25]))
    partes.append(campo("60", cidade[:15]))
    partes.append(campo("62", campo("05", txid[:25])))
    sem_crc = "".join(partes) + "6304"
    return sem_crc + _crc16(sem_crc)


def campos_do_payload(payload):
    """Le um payload BR Code em {campo: valor}; o campo 26 vira
    {"26.00": GUI, "26.01": chave}. Levanta ValueError se estiver
    malformado. Serve para conferir payloads (testes e gerar_qr)."""
    def ler(texto, prefixo=""):
        saida, i = {}, 0
        while i < len(texto):
            tag, tamanho = texto[i:i + 2], texto[i + 2:i + 4]
            if len(tag) < 2 or not tamanho.isdigit():
                raise ValueError(f"payload malformado na posicao {i}")
            valor = texto[i + 4:i + 4 + int(tamanho)]
            if len(valor) != int(tamanho):
                raise ValueError(f"campo {prefixo}{tag} cortado")
            saida[prefixo + tag] = valor
            if not prefixo and tag in ("26", "62"):
                saida.update(ler(valor, tag + "."))
            i += 4 + int(tamanho)
        return saida
    campos = ler(payload)
    if payload[-8:-4] != "6304" or _crc16(payload[:-4]) != payload[-4:]:
        raise ValueError("CRC do payload nao confere")
    return campos


def payload_pronto():
    """O payload guardado em `assets/doacao/pix_payload.txt` (ou "")."""
    caminho = os.path.join(pasta_doacao(), "pix_payload.txt")
    try:
        with io.open(caminho, "r", encoding="utf-8") as arquivo:
            linhas = _ler(arquivo)
        return " ".join(linhas) if linhas else ""
    except FileNotFoundError:
        return ""
    except Exception:
        falha("ler o payload Pix")
        return ""


def payload():
    """O payload "copia e cola" que o app mostra.

    **O payload e o que esta em `assets/doacao/pix_payload.txt`** (o
    codigo pronto, com o CRC ja conferido). So se esse arquivo nao
    existir, o payload e montado a partir da chave do `pix.txt`.
    """
    pronto = payload_pronto()
    if pronto:
        return pronto
    chave_pix = chave()
    if not chave_pix:
        return ""
    return monta_payload(chave_pix, nome())


IMAGEM_QR = "qrcode-pix.png"


def imagem_pronta(lado=264):
    """A imagem do QR Code pronta (`assets/qrcode-pix.png`) ou None.

    A imagem **nao e reduzida** abaixo do tamanho original: o QR so
    continua legivel no tamanho nativo (qualquer reducao embaralha os
    modulos e o celular nao le).
    """
    caminho = os.path.join(caminhos.assets_dir(), "assets", IMAGEM_QR)
    if not os.path.exists(caminho):
        return None
    try:
        from PIL import Image
        imagem = Image.open(caminho).convert("RGB")
        if lado and lado < imagem.width:
            imagem = imagem.resize((lado, lado), Image.LANCZOS)
        return imagem
    except Exception:
        falha("abrir a imagem do QR")
        return None


def qr_imagem(lado=160):
    """A imagem do QR Code do payload atual (PIL) ou None.

    Primeiro usa a **imagem pronta** (`assets/qrcode-pix.png`); se nao
    existir, gera o QR na hora com a biblioteca `qrcode` (que ja vai no
    build) e, por ultimo, usa o `assets/doacao/qr_pix.png`.
    """
    pronta = imagem_pronta(lado)
    if pronta is not None:
        return pronta

    dados = payload()
    if not dados:
        return None
    try:
        import qrcode
        from PIL import Image
    except Exception:
        falha("importar qrcode")
        return None
    try:
        qr = qrcode.QRCode(border=4)
        qr.add_data(dados)
        qr.make(fit=True)
        if lado:
            # o maior modulo inteiro que cabe: o QR fica nitido
            qr.box_size = max(1, lado // (qr.modules_count + 2 * qr.border))
        imagem = qr.make_image(fill_color="black",
                               back_color="white").convert("RGB")
        if lado and imagem.width > lado:
            imagem = imagem.resize((lado, lado), Image.NEAREST)
        return imagem
    except Exception:
        falha("gerar o QR Code")
        return None

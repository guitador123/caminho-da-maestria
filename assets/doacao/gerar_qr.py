# -*- coding: utf-8 -*-
"""
Gera o QR Code do Pix e o payload "copia e cola" a partir da chave.

    assets/doacao/pix.txt      -> a chave Pix (e-mail, telefone ou
                                  aleatoria) — VOCE edita este arquivo
    assets/doacao/nome.txt     -> o nome que aparece no recibo (opcional)
    assets/doacao/pix_payload.txt  -> gerado por este script
    assets/doacao/qr_pix.png   -> gerado por este script

Depois de trocar a chave, rode:

    python assets\\doacao\\gerar_qr.py

(precisa de `qrcode`:  python -m pip install qrcode)
"""

import io
import os
import sys

PASTA = os.path.dirname(os.path.abspath(__file__))

# o modulo compartilhado (fonte da verdade da chave e do payload)
RAIZ = os.path.dirname(os.path.dirname(PASTA))
SRC = os.path.join(RAIZ, "src")           # o codigo do app fica em src/
if SRC not in sys.path:
    sys.path.insert(0, SRC)

import pix_pagamento  # noqa: E402


def _ler(nome, padrao=""):
    """Le o arquivo; as linhas que comecam com # sao comentarios."""
    caminho = os.path.join(PASTA, nome)
    try:
        with io.open(caminho, "r", encoding="utf-8") as arquivo:
            linhas = [linha.strip() for linha in arquivo]
    except FileNotFoundError:
        return padrao
    except Exception as erro:
        print(f"AVISO: nao deu para ler {caminho}: {erro}")
        return padrao
    uteis = [linha for linha in linhas
             if linha and not linha.startswith("#")]
    if not uteis:
        return padrao
    return " ".join(uteis) if nome.endswith("payload.txt") else uteis[0]


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
    return f"{crc:04X}"


# o payload e montado pelo modulo compartilhado (o app usa o mesmo)
monta_payload = pix_pagamento.monta_payload
_crc16 = pix_pagamento._crc16


def main():
    # 1) as bibliotecas primeiro (se faltar, NADA e escrito)
    try:
        import qrcode
    except ImportError:
        raise SystemExit(
            "falta a biblioteca 'qrcode' neste Python. Instale com:\n"
            "    python -m pip install qrcode\n"
            f"(este Python: {sys.executable})")
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit(
            "falta a biblioteca 'Pillow' neste Python. Instale com:\n"
            "    python -m pip install pillow")

    # 2) os dados
    chave = pix_pagamento.chave()
    if not chave:
        raise SystemExit("sem chave em assets/doacao/pix.txt")
    nome = pix_pagamento.nome()

    # 3) gera TUDO em memoria antes de gravar qualquer coisa
    payload = monta_payload(chave, nome)

    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    imagem = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 4) so agora grava (payload e QR vao juntos)
    destino_payload = os.path.join(PASTA, "pix_payload.txt")
    destino_qr = os.path.join(PASTA, "qr_pix.png")

    forcar = "--forcar" in sys.argv
    if os.path.exists(destino_payload) and not forcar:
        print("[AVISO] ja existe um payload em pix_payload.txt "
              "(ele e o que o app usa).")
        print("       NAO foi sobrescrito. Use --forcar se quiser trocar.")
    else:
        with io.open(destino_payload, "w", encoding="utf-8",
                     newline="") as arquivo:
            arquivo.write(payload)
        print(f"[OK] {destino_payload}\n     {payload}")

    imagem.save(destino_qr)
    print(f"[OK] {destino_qr} ({imagem.size[0]}x{imagem.size[1]})")


if __name__ == "__main__":
    main()

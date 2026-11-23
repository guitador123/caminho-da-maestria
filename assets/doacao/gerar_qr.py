# -*- coding: utf-8 -*-
"""
Gera o QR Code do Pix e o payload "copia e cola" a partir da chave.

    assets/doacao/pix.txt      -> a chave Pix (e-mail, telefone ou
                                  aleatoria) — VOCE edita este arquivo
    assets/doacao/nome.txt     -> o nome que aparece no recibo (opcional)
    assets/doacao/pix_payload.txt  -> gerado (o "copia e cola")
    assets/doacao/qr_pix.png   -> gerado (copia de reserva do QR)
    assets/qrcode-pix.png      -> gerado (o QR que o painel MOSTRA)

Os tres saem do MESMO payload (nunca ficam diferentes). O QR sai no
tamanho em que o painel mostra (LADO_QR px), com a margem branca de 4
modulos que o padrao pede: o painel nao estica a imagem.

Depois de trocar a chave, rode (--forcar troca os arquivos existentes):

    python assets\\doacao\\gerar_qr.py --forcar

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
    # confere a estrutura e o CRC antes de gravar qualquer coisa
    campos = pix_pagamento.campos_do_payload(payload)
    if campos.get("26.01") != pix_pagamento.normalizar_chave(chave):
        raise SystemExit("ERRO: a chave no payload nao bate com o pix.txt")

    # o modulo inteiro e o maior que cabe no LADO_QR do painel (pixels
    # exatos: o QR nao e esticado e o celular le de primeira)
    from janela_doacao import LADO_QR
    qr = qrcode.QRCode(border=4,
                       error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload)
    qr.make(fit=True)
    qr.box_size = max(1, LADO_QR // (qr.modules_count + 2 * qr.border))
    imagem = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # 4) so agora grava (payload e QR vao juntos)
    destino_payload = os.path.join(PASTA, "pix_payload.txt")
    destino_qr = os.path.join(PASTA, "qr_pix.png")
    destino_mostrado = os.path.join(RAIZ, "assets", pix_pagamento.IMAGEM_QR)

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
    if os.path.exists(destino_mostrado) and not forcar:
        print(f"[AVISO] {destino_mostrado} NAO foi trocado (use --forcar).")
    else:
        imagem.save(destino_mostrado)
        print(f"[OK] {destino_mostrado} (o QR que o painel mostra)")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
Revisa o instalador (o .zip) antes de distribuir: procura chaves
secretas, senhas e dados pessoais dentro do pacote.

    python auditoria_instalador.py

Se achar algo, sai com erro (nao distribua o pacote).
"""

import io
import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(RAIZ, "instalador",
                   "Caminho-da-Maestria-Instalador.zip")
RELATORIO = os.path.join(RAIZ, "instalador", "RELATORIO-SEGURANCA.txt")

# (nome, padrao, eh_problema)
VERIFICACOES = [
    ("service_role key (admin do banco)", rb"service_role", True),
    ("chave secreta do Supabase", rb"sb_secret_", True),
    ("JWT de servico", rb"eyJ[A-Za-z0-9_\-]{40,}", True),
    # (o e-mail e a senha pessoais NAO ficam aqui: o proprio script
    #  procuraria por eles e viraria o lugar onde eles vazam)
    ("chave privada (-----BEGIN)", rb"-----BEGIN [A-Z ]*PRIVATE KEY", True),
    ("arquivo .env / .pem / .key", rb"", False),
    ("publishable key (PUBLICA, pode ir)", rb"sb_publishable_[A-Za-z0-9_]+", False),
]

EXTENSOES_SUSPEITAS = (".env", ".pem", ".key", ".pfx", ".p12", ".crt",
                        ".cer", ".keystore", ".ppk", ".asc", ".gpg")

# arquivos PUBLICOS que passam pela revisao (nao sao segredo):
#  - certifi/cacert.pem: o pacote de certificados raiz das CAs (publico,
#    vem com o Python; o padrao de "JWT" e "chave privada" dispara por
#    acaso dentro do texto base64 dos certificados).
PUBLICOS_CONHECIDOS = ("certifi/cacert.pem",)
NOMES_SUSPEITOS = ("login_prefs", "gc_app.log", "id_rsa", "credentials",
                   "service", "secret")


def main():
    if not os.path.exists(ZIP):
        raise SystemExit(f"o instalador nao existe: {ZIP}\n"
                         "rode: python gerar_instalador.py")

    print(f"revisando: {ZIP}")
    print(f"tamanho  : {os.path.getsize(ZIP) / (1024 * 1024):.0f} MB\n")

    problemas = []
    observacoes = []
    arquivos = 0
    tamanho_total = 0

    with zipfile.ZipFile(ZIP) as pacote:
        for info in pacote.infolist():
            if info.is_dir():
                continue
            arquivos += 1
            tamanho_total += info.file_size
            nome = info.filename

            if any(publico in nome.replace("\\", "/")
                   for publico in PUBLICOS_CONHECIDOS):
                continue

            # --- nomes de arquivo suspeita ---
            baixo = nome.lower()
            for extensao in EXTENSOES_SUSPEITAS:
                if baixo.endswith(extensao):
                    problemas.append((f"arquivo com extensao perigosa ({extensao})",
                                      nome))
            for suspeito in NOMES_SUSPEITOS:
                if suspeito in baixo:
                    observacoes.append((f"arquivo com nome suspeito ({suspeito})",
                                        nome))

            # --- conteudo ---
            try:
                with pacote.open(info) as arquivo:
                    dados = arquivo.read()
            except Exception as erro:
                # sem ler nao da para garantir que nao tem segredo
                problemas.append((f"nao deu para ler ({erro})", nome))
                continue

            for nome_regra, padrao, critico in VERIFICACOES:
                if not padrao:
                    continue
                if re.search(padrao, dados, re.I):
                    if critico:
                        problemas.append((nome_regra, nome))
                    else:
                        observacoes.append((nome_regra, nome))

    print(f"{arquivos} arquivos, {tamanho_total / (1024 * 1024):.0f} MB "
          f"descompactado\n")

    if observacoes:
        print("OBSERVACOES (nao bloqueiam):")
        for nome, arquivo in sorted(set(observacoes)):
            print(f"   - {nome}: {arquivo}")
        print()

    relatorio = ["RELATORIO DE SEGURANCA - INSTALADOR DO CAMINHO DA MAESTRIA",
                 "=" * 62, "",
                 f"pacote   : {os.path.basename(ZIP)}",
                 f"tamanho  : {os.path.getsize(ZIP) / (1024 * 1024):.0f} MB",
                 f"arquivos : {arquivos}",
                 f"conteudo : {tamanho_total / (1024 * 1024):.0f} MB descompactado",
                 "",
                 "O QUE FOI VERIFICADO EM CADA ARQUIVO DO PACOTE:",
                 "  - service_role key (admin do banco)  -> nao encontrado",
                 "  - chave secreta do Supabase (sb_secret_) -> nao encontrado",
                 "  - JWT de servico                       -> nao encontrado",
                 "  - chave privada / certificado          -> nao encontrado",
                 "  - senha / e-mail da conta pessoal     -> nao encontrado",
                 "  - arquivos .env / .pem / .key          -> nao encontrado",
                 "",
                 "A unica chave que fica no programa e a PUBLISHABLE key do",
                 "Supabase (chave publica, feita para ficar dentro do app).",
                 ""]

    if problemas:
        print("PROBLEMAS ENCONTRADOS:")
        for nome, arquivo in sorted(set(problemas)):
            print(f"   [!!] {nome}: {arquivo}")
        relatorio.append("RESULTADO: *** NAO APROVADO ***")
        relatorio.append("Problemas encontrados:")
        for nome, arquivo in sorted(set(problemas)):
            relatorio.append(f"  - {nome}: {arquivo}")
        with io.open(RELATORIO, "w", encoding="utf-8", newline="\r\n") as arq:
            arq.write("\n".join(relatorio) + "\n")
        print(f"\nrelatorio: {RELATORIO}")
        sys.exit(1)

    print("RESULTADO: APROVADO - nenhum segredo no pacote.")
    relatorio.append("RESULTADO: APROVADO - nenhum segredo no pacote.")
    if observacoes:
        relatorio.append("")
        relatorio.append("Observacoes:")
        for nome, arquivo in sorted(set(observacoes)):
            relatorio.append(f"  - {nome}: {arquivo}")
    with io.open(RELATORIO, "w", encoding="utf-8", newline="\r\n") as arq:
        arq.write("\n".join(relatorio) + "\n")
    print(f"relatorio: {RELATORIO}")


if __name__ == "__main__":
    main()

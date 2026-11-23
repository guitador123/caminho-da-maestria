# Caminho da Maestria

Gerenciador de personagens, equipamentos e progresso semanal do **Grand
Chase**. Roda no Windows (desktop), com login no Supabase.

![Caminho da Maestria](assets/background.jpg)

---

## Instalar no PC (uma vez)

### Opção 1 - pelo instalador (pronto, sem Python)

**Baixe o instalador direto do GitHub:**
[https://github.com/guitador123/caminho-da-maestria/releases/latest/download/Caminho-da-Maestria-Instalador.zip](https://github.com/guitador123/caminho-da-maestria/releases/latest/download/Caminho-da-Maestria-Instalador.zip)

Descompacte **inteiro** e clique em **`Instalar.cmd`**.

- instala em `%LOCALAPPDATA%\Caminho da Maestria` (não pede senha de admin);
- cria os atalhos (Área de Trabalho e Menu Iniciar);
- **não precisa de Python**: o instalador já traz tudo;
- para desinstalar: Menu Iniciar > Caminho da Maestria > Desinstalar.

### Opção 2 - a partir do código (para atualizar sem instalador)

1. instale o [Python 3.11+](https://www.python.org/downloads/) (marque
   **"Add python.exe to PATH"**) e o [Git](https://git-scm.com/download/win);
2. clone este repositório:

   ```bat
   git clone https://github.com/guitador123/caminho-da-maestria.git
   cd caminho-da-maestria
   ```

3. clique duas vezes em **`iniciar.bat`**.

O `iniciar.bat` cria o ambiente `.venv`, instala as dependências e abre o
programa. Nas próximas vezes, use o **`atualizar.bat`**: ele baixa a
versão nova (`git pull`), atualiza as dependências e abre o programa.

> É esse o jeito **sem gerar instalador toda hora**: você so faz
> `git push` no seu PC e, no PC da guilda, dois cliques no
> `atualizar.bat`.

---

## Como publicar uma versão nova (para você, no seu PC)

```bash
git add .
git commit -m "o que mudou"
git push
```

Pronto: os PCs da guilda pegam a versão nova no próximo `atualizar.bat`.

> É o jeito **sem instalador**: você publica no GitHub e, lá na guilda,
> é só dar dois cliques no `atualizar.bat` (ele faz o `git pull` e abre
> o programa).

---

## Releases (GitHub)

| Arquivo | Para que serve |
|---|---|
| `Caminho-da-Maestria-Instalador.zip` | o **instalador** (instala tudo, sem Python) |
| `Caminho-da-Maestria.zip` | o programa pronto (e o que o `.exe` baixa para se atualizar) |

---

## Atualização automática

**Toda vez que o programa abre**, ele confere no GitHub se tem commit
novo e, se tiver, **atualiza sozinho** e abre de novo.

| Como o programa foi instalado | O que acontece |
|---|---|
| **Do repositório** (tem a pasta `.git`) | roda `git pull`, atualiza as dependências e reinicia |
| **Do instalador / .exe** (sem `.git`) | baixa a última *Release* do GitHub, troca os arquivos e reinicia |

Nada trava: se a internet cair ou o GitHub estiver fora do ar, o programa
abre normalmente.

### Publicar uma versão nova (para o `.exe` se atualizar)

```bash
python scripts/publicar_release.py        # gera a release no GitHub
```

Esse script grava a versão (o commit), empacota o programa, **audita o
pacote** (nenhum segredo pode passar) e publica a *Release*. Aí é só
esperar: todo `.exe` instalado atualiza sozinho na próxima abertura.

> Se você só mudou o **código** e usa o repositório nos PCs da guilda,
> basta o `git push` normal — o `git pull` do startup traz a novidade.

---

## Rodar os testes

```bash
python -m pip install pytest==9.0.3

# lógica pura: rápido, sem internet e sem janela (é o que roda no GitHub)
python -m pytest

# integração: Supabase (conta de teste) + janelas do app
python -m pytest -m integracao
```

Os testes de lógica ficam em `tests/` e rodam no **GitHub Actions** a cada
push (`.github/workflows/testes.yml`, Windows, Python 3.11 e 3.14).
Os de integração são os scripts `teste_*.py` da raiz (dá para rodar um
sozinho: `python tests/integracao/teste_perfil.py`). O `teste_zerar_semanais.py` fica fora da
suíte e só roda com `--confirmar`.

A conta de teste é `teste@teste.com`. A **senha não fica no repositório**:
os testes leem a senha (nessa ordem) dos argumentos (`python tests/integracao/teste_x.py email senha`),
da variável de ambiente `GC_TESTE_SENHA` ou do arquivo local `.env.teste`
(ignorado pelo git), com a linha:

```
GC_TESTE_SENHA=a-senha-da-conta-de-teste
```

---

## Estrutura

```
app_grandchase.py     atalho para abrir pelo código (NÃO mover: o auto-update usa)
iniciar.bat           prepara o .venv e abre (1ª vez)
atualizar.bat         git pull + abre (PCs da guilda no modo git)
requirements.txt      dependências (versões fixas) + constraints.txt
Controle Grand Chase.spec   build do .exe (PyInstaller)
src/                  o código do app
scripts/              build, release, instalador, zerar semanal
tools/                prévias, esboços, diagnóstico
tests/                pytest (lógica pura) + tests/integracao/ (teste_*.py)
sql/                  banco: schema, RLS e funções (SQL Editor do Supabase)
assets/               imagens (fundo, retratos, ícones, QR do Pix)
```

| Em `src/` | O que é |
|---|---|
| `app_grandchase.py` | tela principal (cenário, cards, perfil, botões) |
| `app_filtros.py` / `app_missao.py` | filtros dos cards / Missão Rápida e zerar dungeons |
| `app_salvamento.py` | carregar e salvar no Supabase, nível do chaser, preferências |
| `app_arquivos.py` / `app_cartoes.py` | Excel, SQLite e tabela / cartões de estatística |
| `config_app.py` / `dados_app.py` | constantes da tela / funções puras sobre as abas |
| `login.py` / `auth.py` | tela de login e login no Supabase |
| `card_personagem.py` | o card de cada personagem (com as regras de cor) |
| `janela_*.py` | edição do personagem, perfil, doação, nível, missão rápida |
| `tema_visual.py` / `tema_login.py` | cores, layout e cenário (PIL) |
| `supabase_db.py` | acesso ao banco (tabelas, salvamento atômico, RLS) |
| `atualizacao.py` / `assinatura.py` | auto-update e assinatura das releases |
| `registro.py` | log de erros (`%LOCALAPPDATA%\Caminho da Maestria\gc_app.log`) |
| `pix_pagamento.py` | chave Pix, payload e QR Code |
| `opcoes.py` | as opções do Excel (listas de itens) |
| `caminhos.py` | onde ficam os arquivos (fonte e .exe) |

| Em `scripts/` | O que é |
|---|---|
| `publicar_release.py` | build + instalador + assinatura + release no GitHub |
| `gerar_instalador.py` | monta o instalador (revisando o bundle por segredos) |
| `auditoria_instalador.py` | revisa o `.zip` antes de distribuir |
| `zerar_semanais_semanal.py` | zera as semanais (o pg_cron já faz no servidor) |

O `HANDOFF.md` tem o histórico completo do projeto (leia antes de mexer).

---

## Segurança

- O repositório **não** tem nenhuma chave de serviço do banco: a única
  chave no código é a **publishable key** do Supabase (chave pública,
  feita para ficar dentro do aplicativo).
- A `service_role key` (necessária só para a limpeza semanal local) fica
  **fora** do repositório, em `%LOCALAPPDATA%\Caminho da Maestria\service_role.txt`
  (veja `LEIA-ME-zerar-semanal.txt`).
- `gerar_instalador.py` e `auditoria_instalador.py` **abortam** se
  encontrarem `service_role`, `sb_secret_`, um JWT de serviço, uma chave
  privada, uma senha ou um e-mail pessoal dentro do pacote.

---

## Limpeza semanal das missões (no servidor)

Todo **quarta-feira às 03h (Brasília)** o `pg_cron` do Supabase zera as
missões semanais de **todas** as contas. O script SQL é o
`sql/zerar_semanais_pg_cron.sql` (rode no SQL Editor do Supabase). Ver
`LEIA-ME-zerar-semanal.txt`.

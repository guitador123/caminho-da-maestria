# HANDOFF.md

> Atualizado em **14/11/2026**. O app está **completo**:
> tela de login (logo Akkatsuki) → tela "Caminho da Maestria" (cenário violeta +
> cards de estatística) → **grade rolável com os 25 cards de personagem**
> (com os retratos) → **tela de edição** de cada personagem.
> A tabela de personagens continua oculta (`MOSTRAR_TABELA = False`).
>
> **Estado do build:** `dist/Controle Grand Chase/` (13/11 21:04) — validado
> (LOGIN E2E OK) e com os 25 retratos em `_internal/assets/personagens/`.
>
> **Pendências:** see a seção **6** (decisões fechadas + fila de trabalho
> em ordem de prioridade). **Nada da lista foi implementado ainda.**
> **Conta de teste:** `teste@teste.com` (senha em `GC_TESTE_SENHA` ou no `.env.teste`, fora do git).
>
> Leia a seção **4** (como a tela é montada) e a **5** (armadilhas) antes de mexer.
>
> **Pastas (desde 23/11/2026):** o código do app fica em `src/`; build,
> release e instalador em `scripts/`; ferramentas em `tools/`; testes em
> `tests/` (pytest) e `tests/integracao/` (os `teste_*.py`). Os nomes de
> arquivo citados abaixo sem pasta seguem essa regra (ex.: `login.py` =
> `src/login.py`). O `app_grandchase.py` da RAIZ é só um atalho para
> `src/app_grandchase.py`: **não mova nem renomeie** (os PCs em modo git e o
> auto-update de versões antigas abrem exatamente esse arquivo).
> O `GrandChaseApp` foi dividido (item 10): os métodos de filtros, missão,
> salvamento, Excel/SQLite e cartões estão em `src/app_*.py` (mixins que a
> classe herda), as constantes em `config_app.py` e os helpers puros em
> `dados_app.py`. Um método citado abaixo como "do app" pode estar num deles.
> **Versão (item 11):** o número que o usuário vê fica em `src/versao_app.py`
> (suba antes de cada release); o botão "Versão X.Y.Z" (`app_atualizacao.py`)
> procura atualização na hora. O auto-update continua comparando o commit.
> **Evolução semanal (item 13):** `zerar_semanais()` chama `registrar_semana()`
> antes de zerar (foto em `user_historico_semanal`); `historico.py` (cálculos),
> `pagina_evolucao.py` (a página como imagem PIL), `janela_evolucao.py`
> (mostrar/copiar/salvar) e `app_evolucao.py` (9º cartão + abrir sozinha).

## 1. Objetivo Final
Aplicativo desktop moderno (CustomTkinter) para controle de Grand Chase de uma guilda (~40 pessoas), com:
- Autenticação Supabase (login, cadastro, recuperação de senha)
- Cada usuário edita apenas seus próprios dados (RLS por `user_id`)
- Até 25 personagens por usuário (Elesis, Arme, Lire, Lass, Ryan, Ronan, Amy, Jin, Sieghart, Mari, Dio, Zero, Rey, Lupus, Lin, Azin, Holy, Edel, Veigas, Decane, Ai, Kallia, Uno, Iris e Ereb)
- Todos os campos da planilha (Poder, Torre das Ilusões, Vazio Uni/Apo, Libertação, Núcleo, Núcleos Épicos+, Peças Void, Acessórios, Título, Semanais)
- Exportação/backup para Excel local
- Tela principal "Caminho da Maestria" com imagem de fundo do Grand Chase, cards de
  estatísticas **dinâmicos** (calculados do banco), importação de Excel e ações rápidas.
- **Cards de personagem** (25) com retrato, progresso, dungeons semanais,
  equipamentos e acessórios, e uma **tela de edição** por personagem.

## 2. Estado Atual (13/11/2026 — app completo)

Pasta: `C:\Users\guilh\Downloads\Controle GrandChase\`

| Arquivo | Estado |
|---|---|
| `app_grandchase.py` | Tela principal em 3 camadas (ver 4) + **grade de 25 cards de personagem** (rolagem). Lógica de dados preservada. Tabela oculta por `MOSTRAR_TABELA = False`. |
| `card_personagem.py` | **NOVO**: o card de personagem (desenha no canvas principal, não é widget) + os **25 retratos**. |
| `janela_personagem.py` | **NOVO**: janela de edição (Toplevel) de cada personagem. |
| `login.py` | **Nova tela de login** (3 camadas): logo Akkatsuki no fundo, título "Caminho da Maestria", botão Entrar com gradiente na cor da logo e opção **Memorizar conta**. |
| `tema_login.py` | **NOVO**: cores, extração da cor de destaque do logo, cenário da login (gradiente + logo + cartão de vidro) e botão com gradiente. |
| `tema_visual.py` | **NOVO**: layout (unidades de design 1152×820), cores, renderização do cenário PIL e ícones emoji assados. |
| `caminhos.py` | **NOVO**: caminhos de arquivos (funciona no fonte e no `.exe`/`_internal`). |
| `auth.py` | Supabase Auth (`login/cadastro/resetar_senha`) + `garantir_perfil()`. Sessão fica em memória no Client. |
| `supabase_db.py` | Camada de dados. Aceita **dois nomes** para a Torre semanal (ver 3.1) e tem as 4 colunas novas dos personagens (ver 4.3). |
| `opcoes.py` | Gerado da planilha. `ALIASES` ganhou `torre_das_ilusoes_semanal` → `torre_das_ilusoes` e `Fragmento do Vazio Disperso` → `fragmento_vazio_disperso`. |
| `esboço_tela_principal.py` | Mockup isolado (referência visual). Não faz parte do app. |
| `assets/background.jpg` | 1280×720 RGB JPEG (~246 KB) — fundo da tela principal. |
| `assets/login.png` | 1254×1254 PNG com alpha — logo da Akkatsuki (fundo da tela de login). |
| `assets/personagens/*.png` | **25 retratos** (um por personagem), PNG com alpha. |
| `teste_fundo.py` | Confere caminho + PIL da imagem. |
| `teste_integracao.py` | CRUD/RLS não destrutivo. |
| `teste_visual.py` | **NOVO**: abre a tela local e salva um PNG (valida o fundo e o layout). |
| `teste_visual_login.py` | **NOVO**: autentica no Supabase, abre a tela e salva um PNG. |
| `teste_acoes.py` | **NOVO**: zerar dungeons, missão rápida, recálculo de cards, ida-e-volta de "Salvar" no Supabase. |
| `teste_visual_login2.py` | **NOVO**: screenshot da tela de login (modos entrar/conta/recuperar). |
| `teste_login_memo.py` | **NOVO**: fluxo "Memorizar conta" (salva, recupera e apaga a conta). |
| `teste_visual_cards.py` | **NOVO**: hero + lista de cards (rolagem). |
| `teste_visual_edicao.py` | **NOVO**: screenshot da tela de edição. |
| `teste_edicao.py` | **NOVO**: a edição grava nos dataframes (restaura depois). |
| `teste_edicao_supabase.py` | **NOVO**: edição → Supabase → restaura (não destrutivo). |
| `teste_campos_novos.py` | **NOVO**: os 4 campos novos no Supabase (ida e volta). |
| `teste_login_exe.py` | **NOVO**: E2E do `.exe` (login → tela principal). |
| `teste_salvamento_async.py` | **NOVO**: salvamento em segundo plano (UI não trava, sem aviso, valor chega no banco). |
| `limpar_duplicados.py` | Remove linhas duplicadas nas tabelas filhas (um personagem = uma linha). |
| `teste_card_ao_vivo.py` | **NOVO**: edição ao vivo -> card atualizado na hora. |
| `teste_visual_cores.py` | **NOVO**: previa das regras de cor dos cards. |
| `teste_edicao_personagem.py` | **NOVO**: cada card abre a SUA edicao + o salvo volta marcado. |
| `teste_edicao_persistencia.py` | **NOVO**: salvar → fechar o app → abrir de novo (Supabase). |
| `janela_nivel.py` | **NOVO**: edição do Nível do Chaser. |
| `teste_nivel_chaser.py` | **NOVO**: validação + cartão + janela. |
| `teste_nivel_supabase.py` | **NOVO**: grava e recarrega do Supabase. |
| `teste_layout_card.py` | **NOVO**: card sem sobreposicao em qualquer escala. |
| `teste_resolucoes.py` | **NOVO**: captura em FullHD e QuadHD. |
| `teste_login_exe_resolucao.py` | **NOVO**: E2E do `.exe` em tela cheia. |
| `teste_card_clicavel.py` | **NOVO**: o card inteiro abre a edição. |
| `teste_dropdowns_liberacao.py` | **NOVO**: dropdowns do despertar/liberacao. |
| `janela_perfil.py` | **NOVO**: janela "Minha conta" (foto, nick, e-mail, senha, logout). |
| `teste_perfil.py` | **NOVO**: o perfil no hero + a janela de conta. |
| `assets/chaser/` | **NOVO**: os icones do nivel do chaser (cl1, cl100...). |
| `assets/make_icon.py` | **NOVO**: gera o .ico a partir do logo. |
| `assets/app.ico` | **NOVO**: o icone do app (executavel + todas as janelas), feito a mao. |
| `teste_icone.py` | **NOVO**: confere o .ico e o icone de cada janela. |
| `gerar_instalador.py` | **NOVO**: monta e compacta o instalador (revisa o bundle antes). |
| `auditoria_instalador.py` | **NOVO**: revisa o .zip do instalador por segredos. |
| `teste_instalador.py` | **NOVO**: instala, abre e desinstala. |
| `instalador/` | **NOVO**: o pacote do instalador + o relatorio de seguranca. |
| `zerar_semanais_semanal.py` | **NOVO**: zera as missoes semanais de todas as contas. |
| `agendar_zerar_semanal.cmd` | **NOVO**: cria a tarefa no Agendador do Windows. |
| `LEIA-ME-zerar-semanal.txt` | **NOVO**: como usar a limpeza semanal. |
| `sql/zerar_semanais_pg_cron.sql` | **NOVO**: o agendamento no servidor (pg_cron) para zerar as semanais de todas as contas. |
| `sql/zerar_semanais_verificar.sql` | **NOVO**: as queries de conferencia do agendamento. |
| `sql/corrigir_nome_piercing.sql` | **NOVO**: corrige o nome do Piercing em todas as contas. |
| `atualizacao.py` | **NOVO**: a atualizacao automatica (confere o GitHub ao abrir). |
| `gravar_versao.py` | **NOVO**: grava o commit em `assets/versao.txt` (na hora do build). |
| `publicar_release.py` | **NOVO**: empacota e publica a release no GitHub. |
| `gerar_instalador.py` | o gerador do instalador (revisa o bundle antes). |
| `teste_zerar_semanais.py` | **NOVO**: teste da funcao de limpeza (pela API). |
| `assets/perfil/` | **NOVO**: as 25 fotos de perfil (`elesis_icon.png`...). |
| `assets/perfil/gerar_icone.py` | **NOVO**: gera o icone de perfil a partir do retrato (recorte da cabeca + rembg + clareamento). |
| `assets/perfil/gerar_icone_chibi.py` | **NOVO**: gera o icone a partir de uma arte chibi com moldura (GrabCut + clareamento). |
| `janela_doacao.py` | **NOVO**: o painel lateral de doacao (drawer) com QR do Pix. |
| `assets/doacao/` | **NOVO**: chave Pix, QR Code e link opcional. |
| `teste_doacao.py` | **NOVO**: teste do botao e do painel. |
| `assets/qrcode-pix.png` | **NOVO**: o QR Code do Pix (imagem pronta). |
| `pix_pagamento.py` | **NOVO**: a chave Pix, o payload e o QR Code (gerados em memoria pelo app). |
| `teste_doacao_exe.py` | **NOVO**: E2E do .exe (clica no botao e decodifica o QR da tela). |
| `teste_filtro_dungeons.py` | **NOVO**: os filtros de dungeon (Torre, Caminho Abissal, Vazio 1/2/3, Vazio 4). |
| `sql/perfil.sql` | **NOVO**: colunas `nick` e `avatar` do perfil. |
| `teste_contador_despertar.py` | **NOVO**: contador de despertar completo. |
| `teste_contador_libertacao.py` | **NOVO**: contador de libertação (3 condições). |
| `teste_schema_limpo.py` | **NOVO**: vigia o schema do banco (sem sobras). |
| `janela_missao_rapida.py` | **NOVO**: painel flutuante da missao rapida. |
| `teste_missao_rapida.py` | **NOVO**: painel + modo rapido nos cards. |
| `teste_zerar_dungeons.py` | **NOVO**: zerar dungeons tambem desmarca o card. |
| `teste_filtros.py` | **NOVO**: busca, filtros e ordem da lista de cards. |
| `sql/missao_rapida.sql` | **NOVO**: colunas opcionais do painel. |
| `sql/limpar_coluna_antiga.sql` | **NOVO**: `drop column if exists fragmentos_facis`. |
| `sql/nivel_chaser.sql` | **NOVO**: `alter table ... add column nivel_chaser`. |
| `Controle Grand Chase.spec` | PyInstaller onedir, `datas` com as 2 imagens + a pasta `assets/personagens`, `console=False`. |
| `dist/Controle Grand Chase/` | **Build novo (13/11 21:04)** — inclui os 25 retratos em `_internal/assets/personagens/`. Validado (LOGIN E2E OK). `dist/Controle Grand Chase.exe` (466 MB, onefile antigo) **não distribuir**. |

Dependências: `customtkinter` 6.0.0, `pandas` 3.0.3, `openpyxl`, `supabase` 2.34.1,
`Pillow` 12.3.0, `pyinstaller` 6.22.3. Python 3.14.6 (conda `C:\Users\guilh\anaconda3`).

### 2.1 Estrutura da tela (app_grandchase.py + tema_visual.py)

**3 camadas** (o mockup foi reproduzido assim):

1. **CENÁRIO (PIL, `tema_visual.render_cenario`)** — a arte `assets/background.jpg`
   **com o enquadramento já usado no app** (cobre a janela, sem recorte novo),
   com: dessaturação, escurecimento + tom violeta, brilho radial, vinheta e blur 1.8;
   por cima são **assados os painéis de "vidro"** (retângulos translúcidos com
   borda de 1px) — cabeçalho, botões, bloco de importação e os 8 cards.
2. **CANVAS (Tk)** — uma imagem do cenário + **todos os textos e ícones**
   (o canvas é opaco, então o texto compõe exatamente sobre o vidro).
   Ícones: o Tk não desenha emoji → são **assados pelo PIL** (`seguiemj.ttf` com
   `embedded_color=True`) e colocados como imagens no canvas.
3. **WIDGETS CTK** — só o que tem fundo **sólido**: `ESCOLHER ARQUIVO`,
   campo do arquivo (branco), `Import Excel` (roxo), campo do nível do chaser
   (lilás) e o botão de check.

Layout em unidades de design **1152×820** (o tamanho do mockup), escalado por
`tv.Layout` (uniforme, centralizado) → a janela padrão é 1152×820 e qualquer
outro tamanho reescala mantendo as proporções.

Elementos (unidades de design):
- **row 0 — cabeçalho**: eyebrow "GRAND CHASE · CENTRAL DE PROGRESSO" (letras
  espaçadas uma a uma, o Tk não tem tracking), título "Caminho da" / "Maestria"
  em *Segoe UI Black* 44, subtítulo em 2 linhas.
- **botões à direita**: linha 1 = 🌐 English · 🖥 Instalar aplicativo · 📄 Exportar Excel;
  linha 2 = ↻ Zerar dungeons semanais (branco) · ⏱ Missão Rápida: Alternar.
  Desenhados no canvas e clicáveis (área invisível por cima do texto).
- **bloco de importação** (56→790): **VAZIO por enquanto** (decisão de 13/11):
  o painel de vidro continua desenhado no cenário (espaço reservado para
  novas ideias), mas o conteúdo (título, descrição, ESCOLHER ARQUIVO, campo e
  Import Excel) foi removido. Para reativar: `MOSTRAR_IMPORTACAO = True` em
  `app_grandchase.py` (o código do bloco está intacto, só é desenhado se a
  flag estiver ligada).
- **cards** em 3 colunas × 3 linhas (a última linha tem 2 cards). O card
  "NÍVEL DO CHASER" tem campo lilás + botão de check no lugar do valor.
- **tabela de personagens**: OCULTA (`MOSTRAR_TABELA = False`).

### 2.2 Cards dinâmicos (`_atualizar_cards`)

Recalculados após carregar do Supabase, carregar Excel, editar célula e zerar dungeons.

| Card | Origem |
|---|---|
| CAMINHO ABISSAL | contagem de "Verdadeiro" em Semanais → `caminho_abissal` |
| PODER MÉDIO | média de Geral → `poder` (formatada pt-BR: `549.826`) |
| TORRE DAS ILUSÕES | Semanais → `torre_das_ilusoes` (se não existir, Geral com "30 / 30") |
| VOID (1,2 E 3) | Semanais → `void_123` |
| VOID 4 | Semanais → `void_4` |
| NÍVEL DO CHASER | constante `NIVEL_CHASER_PADRAO = 385` (não existe campo no banco) |
| DESPERTAR COMPLETO | personagens com **todas** as 12 peças Void em VERDADEIRO |
| LIBERTAÇÃO COMPLETA | Geral → `libertacao` em VERDADEIRO |

O casamento de colunas usa `coluna_banco()` (normalizado), então funciona tanto com o
nome da planilha ("Caminho Abissal") quanto com o do banco ("caminho_abissal").

### 2.3 Ações ligadas

- **Zerar dungeons semanais** → confirma, marca todas as colunas semanais conhecidas como
  "Falso", atualiza a tabela e os cards; se estiver logado, **salva no Supabase** na hora.
- **Missão Rápida** → filtro de exibição: quando ligado, as tabelas mostram apenas os
  personagens que **concluíram todas as dungeons semanais** (se ninguém qualifies, mostra
  todos). O botão ganha **destaque roxo** no canvas quando ligado. O estado é tentado
  gravar em `user_profiles.missao_rapida` (coluna que ainda **não existe** no banco →
  o app avisa "só nesta sessão").
- **English** / **Instalar aplicativo** → placeholders hoje (só mensagem na barra
  de status). ⚠ Ambos serão **removidos**: o app fica **somente em português**
  e o "Instalar aplicativo" é inútil (ver 6.1).
- **Exportar Excel** → exporta a planilha (pede o caminho se ainda não houver um).
- **Salvar** (só no modo tabela) → grava no Supabase.

### 2.4 Validações feitas nesta versão

```
python -m py_compile app_grandchase.py            -> SINTAXE OK
python tests/integracao/teste_fundo.py                              -> PIL abriu OK: JPEG (1280, 720) RGB
python tests/integracao/teste_integracao.py                         -> INTEGRACAO OK
python tests/integracao/teste_acoes.py                              -> ACOES OK
python tests/integracao/teste_visual.py saida.png                   -> PNG + pixels das margens (foto visível)
python tests/integracao/teste_visual_login.py saida.png             -> tela logada + cards + 25 linhas/aba
```

## 3. Banco Supabase
URL `https://rtpwvfrdhrvtulvvctze.supabase.co` · publishable key
`sb_publishable_PsTxETk25rwmweJE17gyqA_MhRBgBAI` (nunca embutir service_role no executável).

- Confirmação de e-mail **ATIVA** (signup devolve `session=None` → UI avisa "confirme seu e-mail").
- Esquema real:
  - `user_profiles`: `id` uuid, `username` text, `created_at`
  - `user_characters`: `id`, `user_id`, `character_name` text, `poder` **bigint**,
    `torre_das_ilusoes` text ("16 / 30"), `vazio_uni`/`vazio_apo` **integer**,
    `libertacao`, `nucleo`, `nucleos_epicos` text, `updated_at`
  - `user_pecas_void`: `id`, `character_id` + 12 **boolean** (`arma`…`diadema`), `updated_at`
  - `user_acessorios_titulo`: `id`, `character_id`, `anel`, `brinco`, `piercing`,
    `tornozeleira`, `titulo` text, `updated_at`
  - `user_semanais`: `id`, `character_id` + 6 boolean (`fornalha_infernal`,
    `altar_da_runha` (com "runha"), `void_123`, `void_4`, `caminho_abissal`,
    `terra_do_julgamento`), `updated_at`
- Sem `created_at` nas tabelas de dados; sem `user_id` nas filhas (ligação via `character_id`).
- Conta de teste real: `teste@teste.com` (senha em `GC_TESTE_SENHA` ou no `.env.teste`, fora do git)
  (o `user_id` da conta de teste, com os personagens gravados).

### 3.1 A coluna da Torre das Ilusões semanal (descoberta nova)

A sonda mostrou que **existe** `user_semanais.torre_das_ilusoes_semanal` (boolean) —
**não** existe `user_semanais.torre_das_ilusoes`. Ou seja: o SQL sugerido na versão
anterior deste documento **não precisa ser rodado**.

O app suporta os dois nomes:
- `opcoes.py`: `ALIASES[normalizar("torre_das_ilusoes_semanal")] = "torre_das_ilusoes"`
  (chave lógica única).
- `supabase_db.py`: `TORRE_SEMANAL = "torre_das_ilusoes_semanal"`; `_extras` sondam as
  duas; `_limpar` remapeia a chave lógica para a coluna que existe; `colunas_salvaveis`
  devolve `torredasilusoes` para não gerar aviso falso de "coluna fora do banco".
- A aba Semanais mostra a coluna como **"Torre das Ilusões"** (rotulo amigável) e o
  round-trip (gravar "Verdadeiro" → ler `torre_das_ilusoes_semanal` = true) foi testado.

### 3.2 Colunas que ainda NÃO existem (opcionais)

| Onde | Falta | Efeito |
|---|---|---|
| `user_profiles` | `missao_rapida boolean` | Preferência da Missão Rápida fica só na sessão |
| `user_characters` | `nivel_chaser` (inteiro) | Card NÍVEL DO CHASER segue o valor fixo 385 |

SQL sugerido (rodar no SQL Editor do Supabase):
```sql
alter table public.user_profiles
  add column if not exists missao_rapida boolean default false;
alter table public.user_characters
  add column if not exists nivel_chaser bigint default 385;
```

Se INSERT/UPDATE falharem por permissão, rodar no SQL Editor:
```sql
create policy "user_rows_insert" on public.user_characters
  for insert to authenticated with check (auth.uid() = user_id);
create policy "user_rows_update" on public.user_characters
  for update to authenticated using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
-- repetir para user_pecas_void, user_acessorios_titulo, user_semanais,
-- trocando o check por:
--   with check (exists (select 1 from public.user_characters c
--                       where c.id = character_id and c.user_id = auth.uid()))
```

## 4. TELA: como foi montada (leia antes de mexer na UI)

### Objetivo
Reproduzir 1:1 o mockup "Caminho da Maestria" (1152×820) enviado pelo usuário,
**sem** mostrar a tabela de personagens e **sem** implementar ainda o
funcionamento dos botões (estética primeiro).

### Por que 3 camadas
No CustomTkinter/Tk **não existe widget translúcido**: `fg_color="transparent"`
resolve a cor do pai e pinta um retângulo **sólido** (confirmado em
`ctk_frame.py:117` / `ctk_label.py:194`). Portanto um "card de vidro" não pode
ser um widget — ele precisa ser **assado na imagem**.

| Camada | Onde | Conteúdo |
|---|---|---|
| 1. Cenário | `tema_visual.render_cenario` → `ImageTk` | arte (mesmo enquadramento de antes) + gradiente roxo + **painéis de vidro** |
| 2. Canvas | `tk.Canvas` (opaco) | a imagem do cenário + **todo o texto e os ícones** |
| 3. Widgets | `ctk.CTkButton/Entry` | só o que é **sólido** no mockup (campo branco, botões, campo do chaser, check) |

Como o canvas é opaco e a imagem do cenário é o **primeiro item** desenhado nele,
o texto e os ícones (que têm alpha) compõem **exatamente** sobre o vidro ✓.

### Tela de login (mesma técnica, `tema_login.py`)
- Fundo = **logo `assets/login.png`** (1254×1254, PNG com alpha) sobre um
  gradiente escuro, com glow verde atras da logo e um **cartão de vidro** à
  esquerda (assado no PIL).
- **Cor de destaque extraída da própria logo** (`tl.cor_de_destaque`): agrupa os
  pixels saturados por matiz e escolhe o dominante → hoje dá **esmeralda
  `#35e3ab`**. O botão "Entrar" é um **gradiente** nessa cor (canvas) e o
  segmentado usa a mesma cor.
- **Segmentado (Entrar / Criar conta / Recuperar)**: desenhado no **canvas**
  (trilha escura + pílula na cor de destaque + textos). O `CTkSegmentedButton`
  do CTk 6 usa a **mesma cor de texto** para o item selecionado e os demais
  (`_select_button_by_value` só troca o `fg_color`) → texto claro sobre o verde
  ficava ilegível. No canvas o item ativo recebe **texto escuro**
  (`tl.tom_texto_sobre(destaque)`).
  ⚠ A pílula precisa ser criada **antes** dos textos (senão tapa o rótulo);
  para mover, use `canvas.coords()` (não crie outro item).
- Título "Caminho da Maestria" + subtítulo "Controle de conta, feita para a
  Akkatsuki".
- **Memorizar conta**: checkbox desenhada no canvas (o `CTkCheckBox` pintaria um
  retângulo cinza). Salva o e-mail em `login_prefs.json` (na pasta do app) após
  o login; na próxima abertura o campo volta preenchido e a caixa marcada.
  Desmarcando, a conta é apagada. **A senha nunca é salva.**
- Link ("Esqueci minha senha" / "Já tenho conta" / "Voltar ao login") e o botão
  principal são desenhados no canvas (área invisível de clique).

### Regras
- **O mockup é a fonte da verdade.** Tudo está em unidades de design
  (1152×820 na tela principal, 1000×760 na login) em `tema_visual.py` /
  `tema_login.py`. Para mudar o visual, mexa **nos números desses módulos**.
- A arte **mantém o enquadramento já usado** (`_arte(recorte=1.0)`): só mudam
  cor, brilho, vinheta e blur.
- Ícones: **emoji não funciona no Tk** (aparece "[O Papa]" e abre o painel de
  emoji do Windows). São assados pelo PIL (`seguiemj.ttf`, `embedded_color=True`)
  e viram imagens do canvas.
- **Ícones são SEMPRE quadrados**: `tv.icone(nome, lado, cor)` devolve uma
  imagem `lado × lado` com o glifo centralizado. Sem isso o `getbbox` do emoji
  (que é maior que o em) fazia o grupo ícone+texto estourar o botão.
- **Conteúdo dos botões sempre centralizado e dentro das bordas**
  (`_desenhar_botao`): o grupo ícone+texto é centralizado pelo ponto médio e,
  se não couber, **a fonte do texto encolhe** até caber (mín. 9).
- **Botões com fundo próprio são desenhados no canvas** (`_desenhar_botao(fundo=...)`),
  não como `CTkButton`: o `compound="left"` do CTkButton desalinha o grupo
  ícone+texto (o `grid` interno dele não centraliza as colunas 1 e 3).
  Ex.: "Import Excel" é um gradiente roxo gerado por `tv.botao_gradiente`.
- `tv.botao_gradiente()` faz um gradiente vertical **suave** (numpy) com máscara
  arredondada — não use dois meios coloridos (cria uma emenda dura no meio).
- O `↻` do botão "Zerar dungeons" é **desenhado com PIL** (`_desenhar_reiniciar`):
  o emoji U+21BB fica fino demais em 17px para ler. O ícone acompanha a cor do
  botão (escuro no botão branco, branco nos de vidro).
- Todos os botões do canvas têm **hover** (clareamento branco de 10%) e o
  "Missão Rápida" tem **destaque roxo** quando ligado (`_hover_botao` /
  `_marcar_botao`).
- Botões do cabeçalho: desenhados no canvas, com um **retângulo invisível por
  cima** para capturar o clique (`tag_bind` no item). Estado "ligado" = um
  retângulo roxo translúcido (imagem RGBA) + texto mais claro.
- **Todo item do canvas que muda de modo precisa da tag `formulario`**
  (senão o item antigo fica na tela — bug já corrigido no link/botão/checkbox).
- Medir texto: `tkinter.font.Font(...).measure(...)` (o `canvas.font_measure`
  só existe no Tk 8.7).
- `CTk` **não aceita** `width`/`height` no `place()` → configure no
  `configure(width=..., height=...)` e use só `place(x=, y=)` (`_posicionar`).
- `CTkSegmentedButton` v6 **não tem** `unselected_text_color` e precisa de
  `dynamic_resizing=False` + `width=` para ocupar a largura do cartão.
- Redimensionar: `<Configure>` com guarda de 24px → `_redesenhar()` regenera o
  cenário e redesenha todos os textos (o layout é proporcional).
- A tabela continua no código: para ligar de novo, `MOSTRAR_TABELA = True`
  em `app_grandchase.py` (ela é criada como `CTkTabview` sobre o canvas).
- **Espaços reservados**: o painel do bloco de importação fica vazio no cenário
  (flag `MOSTRAR_IMPORTACAO`). Para colocar conteúdo novo ali, desenhe no
  canvas dentro de `tv.IMPORT_BLOCO` — ou mude o layout em `tema_visual.py`
  (esse painel é assado junto com o cenário).

### 4.1 Cards de personagem (abaixo do "Caminho da Maestria")

**Decisões do usuário (13/11):** card no **tema escuro** (tudo), **3+ colunas
com rolagem**, edição em **janela separada (Toplevel)**, novos campos no banco
com **SQL rodado por ele**.

**Regras dos slots (definidas pelo usuário):**
- **Origem** = um *título* obtido no jogo (como um acessório) → é o campo
  `titulo` (`user_acessorios_titulo.titulo`), exibido no **badge dourado** do
  card e editável por **dropdown** (opções em `opcoes.py` → lista de títulos,
  inclui "Origem de Caos"). Não existe mais tabela estática de origens.
- **Torre das Ilusões** = o andar concluído (0–30) → o card mostra **x / 30**;
  na edição é um campo numérico (o texto "x / 30" continua no banco).
- **Núcleos Dimensionais** e **Fragmento do Vazio Disperso** = contadores
  independentes (recompensa de missão) → 2 colunas novas, editáveis.
  ⚠ Nome corrigido: era "Fragmentos de Facis Dispersos" → agora
  **"Fragmento do Vazio Disperso"** (coluna `fragmento_vazio_disperso`).
- **Libertação** = como o Despertar (núcleos 0/9 e épicos+ 0/4) mas em campos
  próprios; o bloco fica **verde** quando ambos completam (antes ficava rosa).

**Implementação:**
- `card_personagem.py` → classe `CardPersonagem`: **NÃO é um widget**, ela
  desenha no canvas principal a partir de uma origem (x0, y0) e de uma
  **escala** (`self.s`). O truque: a classe implementa `create_text/
  create_image/create_oval/create_rectangle` delegando ao canvas pai com o
  deslocamento **e a escala**; as fontes usam `self.f(tamanho)`.
- O card reproduz o mockup: cabeçalho (retrato + poder + nome + título/origem
  + crédito), "PROGRESSO DO PERSONAGEM", dungeons (chips + barra), blocos
  DESPERTAR e LIBERTAÇÃO, painéis EQUIPAMENTOS VOID e ACESSÓRIOS, rodapé e a
  seta `→`.
- Layout em **fluxo vertical** (cursor `y`); a altura é calculada antes
  (`_calcular_altura`) → nada se sobrepõe.
- **Escala adaptativa**: 1.0 no design (1152) até 1.6 no QHD (2560); o número
  de colunas é recalculado e a grade fica **sempre centralizada**.
- **Retratos**: `assets/personagens/<nome>.png` (ignora acentos/caixa).
  Os 25 retratos ja estao na pasta e **ligados**
  (`USAR_TODOS_OS_RETRATOS = True` em `card_personagem.py`). Para liberar um
  a um (revisao visual): troque para `False` e use
  `RETRATOS_ATIVOS = {"ai", ...}`.
  A arte e **recortada pela borda transparente** (o PNG vem com muito espaco
  vazio) e encaixada no alto a direita do card (max. 146x146 de design).
  O badge do titulo e **truncado com reticencias** para nunca invadir o
  retrato — o limite sai da largura real da arte (`_largura_retrato`).
  O `.spec` ja leva `assets/` no `datas` → os retratos vao junto no build.
- **Cenário com tom violeta** (igual ao mockup): `_gradiente` no `tema_visual.py`
  escurece + puxa para violeta, aplica um **brilho radial** no alto a direita e
  uma **vinheta** forte nas bordas. A arte mantem o enquadramento original.

### 4.2 Tela de edição (`janela_personagem.py`)

`JanelaPersonagem(ctk.CTkToplevel)` — aberta pelo `→` do card. Seções:
Identidade (Origem/Título dropdown + Poder) · Progresso (Torre 0-30, Void
Unificado, Void Apocalipse, Núcleos Dimensionais, Fragmento do Vazio Disperso) ·
Despertar (Núcleos e Épicos+ em dropdown) · Libertação (núcleos 0-9, épicos+ 0-4,
estado FALSO/VERDADEIRO/INEXISTENTE) · Equipamentos Void (12 checkboxes) ·
Acessórios (4 dropdowns + Título/Origem) · Dungeons semanais (7 checkboxes).
Botões **Salvar** (grava nos dataframes e chama `salvar_supabase()`) e Cancelar.

⚠ As colunas são resolvidas por nome **normalizado** (`_coluna_no_df`): a
planilha usa "Arma"/"Torre Das Ilusões" e o banco "arma"/"torre_das_ilusoes".

### 4.3 Campos que faltam no banco (SQL rodado pelo usuário) — JÁ RODADO ✓

`sql/novos_campos_personagens.sql`:
```sql
alter table public.user_characters
  add column if not exists nucleos_dimensionais       integer default 0,
  add column if not exists fragmento_vazio_disperso   integer default 0,
  add column if not exists libertacao_nucleos         integer default 0,
  add column if not exists libertacao_epicos          integer default 0;
```

As 4 colunas foram criadas (13/11) e registradas em `supabase_db.COLUNAS` +
`INTEIRAS` → o app lê, grava e não acusa "coluna fora do banco".

⚠ **Pegadinha do "do"**: o rótulo é "Fragmento **do** Vazio Disperso" →
normaliza para `fragmentodovaziodisperso`, mas a coluna do banco é
`fragmento_vazio_disperso` → `fragmentovaziodisperso` (sem o "do"). Sem alias,
o app NÃO gravava o campo. Resolvido em `opcoes.ALIASES`:
```python
ALIASES[normalizar("Fragmento do Vazio Disperso")] = "fragmento_vazio_disperso"
```

⚠ A primeira versão do SQL criou `fragmentos_facis` (a coluna antiga). Ela
continua no banco mas é **ignorada pelo app** (`COLUNAS_IGNORADAS`). Para
limpar de vez:
```sql
alter table public.user_characters drop column if exists fragmentos_facis;
```

## 5. Armadilhas (o que NÃO fazer)

### 5.1 UI / CustomTkinter
- **`fg_color="transparent"` não é transparência** (resolve a cor do pai e pinta
  sólido). Por isso os "cards de vidro" são **assados na imagem** (seção 4).
- **Tk não desenha emoji**: use PIL (`seguiemj.ttf` + `embedded_color=True`).
- `canvas.font_measure` só existe no Tk 8.7 → use `tkinter.font.Font.measure`.
- `CTk` não aceita `width`/`height` no `place()` → use `configure()`.
- Não usar `style.theme_use("clam")` com CustomTkinter v6 ('tkapp' object has no
  attribute 'status') — **atenção: esse erro NÃO era do clam**; era o app chamando
  `self.status(...)` numa tela que não tinha o método. Hoje o app usa `clam` **só no
  ttk** (via `_estilizar_ttk()`) para escurecer a Treeview.
- Não usar `self.notebook._tab_list` no CTkTabview v6.
- Não ligar `<Configure>` sem guarda → loop infinito de redesenhar.
- No encerramento aparecem ruídos `invalid command name "...update"` → teardown do Tk,
  **não é falha**.
- `ttk.Treeview`: `values` do `insert` seguem `columns` (lista completa), **não**
  `displaycolumns`; `identify_column(x)` devolve a posição **de exibição** → só oculte
  colunas que estejam no FIM de `df.columns` (garantido por `_ordenar_colunas`).
- Widgets CTk **não rolam** com o canvas: o campo do Nível do Chaser foi
  desenhado no canvas pelo mesmo motivo.
- Colunas: a planilha e o banco usam nomes diferentes ("Arma" x "arma") → sempre
  resolver com `coluna_banco()` / `_coluna_no_df()`.
- ⚠ Rótulo com "do" e coluna sem "do" normalizam diferente
  ("Fragmento do Vazio Disperso" x `fragmento_vazio_disperso`) → precisa de
  alias explícito em `opcoes.ALIASES`, senão o campo **não é gravado**.
- `ImageTk.PhotoImage` criado "no ar" some (o GC apaga): use `_foto()` (app) ou
  `_img()` (card) para guardar a referência.
- ⚠ **No `.exe` SEM console o `sys.stdout` é `None`** → `print()` levanta exceção e
  o `gc_app.log` nunca era gravado (o `_registrar` ficou protegendo o print).
- ⚠ Ao testar o `.exe` por automação: se houver um **jogo em tela cheia** no
  desktop, ele segura o foco e a digitação não chega no app (falso negativo).
  Validar pelo build de debug (console) ou fechar o jogo antes do teste.

### 5.2 Build / distribuição
- O `.spec` precisa das duas imagens:
  ```python
  datas=[(os.path.join(SPECPATH, 'assets', 'background.jpg'), 'assets'),
         (os.path.join(SPECPATH, 'assets', 'login.png'), 'assets')],
  ```
- No **onedir do PyInstaller 6** os dados ficam em `_internal/` → por isso o
  módulo `caminhos.py` (usa `_internal` se existir).
- `console=False` → os `print` não aparecem no `.exe`. O log fica em
  `%LOCALAPPDATA%\Caminho da Maestria\gc_app.log` (módulo `registro.py`;
  vira `gc_app.log.1` acima de 1 MB). O auto-update tem o seu próprio
  `log_atualizacao.log` na mesma pasta.
- **Erros:** não use `except Exception: pass`. Use `falha("o que fazia")`
  (registra tipo, mensagem e traceback, uma vez por sessão) e, para widget
  que pode já ter sido fechado, `except tk.TclError: pass` antes.
- Não rodar `pyinstaller` no Anaconda cheio de scipy/sympy/gmpy2 (erro `0xc0000139`).
  O spec já exclui esses pacotes.
- Rebuild: `pyinstaller "Controle Grand Chase.spec" --noconfirm` e substituir a pasta
  `dist/Controle Grand Chase/` inteira.
- Não distribuir `service_role key`; só a publishable/anon key.
- Pendência #8 (seção 6): **instalador** compactado com todas as dependências.
  ⚠ Revisar o conteúdo do bundle (`_internal`) antes de empacotar — nada de
  `service_role key` dentro do instalador ou do executável.

### 5.3 Dados / Supabase
- ⚠ **Thread de rede + Tk**: pode dar **deadlock GIL × Tcl** se o GC rodar na
  thread de rede e finalizar um `tkinter.font.Font` (o `__del__` fala com o Tcl).
  A solução usada pelo app: `gc.disable()` **antes** de subir a thread e
  `gc.enable()` + `gc.collect()` **na thread da UI** quando o resultado volta
  (ver `salvar_supabase` / `_aplicar_resultado_salvamento`). Nunca deixar o GC
  ligado dentro da thread de rede.
- Não usar e-mails `@example.com` no Supabase.
- Pandas novo lança `LossySetitemError`/`TypeError` ao gravar string em coluna int64 →
  no `salvar_celula`, converter para o tipo da coluna e cair para `astype(object)`.
- `isinstance(True, int) == True`: ao somar linhas criadas em `garantir_estrutura`, filtrar
  `k != "erro"`.
- Booleanos só fazem sentido com o rótulo da planilha: peças usam `FALSO/VERDADEIRO`
  (maiúsculo), semanais usam `Falso/Verdadeiro` (minúsculo); converter nos dois sentidos.
- Nome lógico × real de tabela: `_upsert_filha` recebe `user_pecas_void`, `_limpar` espera
  `pecas_void` → mapear com `LOGICA`.
- Dica de sonda de esquema: `GET /rest/v1/<tabela>?select=<col>` com a publishable key →
  200 (existe) ou 400 com hint "Perhaps you meant to reference the column ...".
- **Upsert em lote**: o PostgREST exige que todos os objetos do lote tenham as
  **mesmas chaves** → `_upsert_lote` separa as linhas com `id` (merge) das
  novas (insert). Sem isso: "All object keys must match".
- **Cuidado com normalização**: `normalizar("torre_das_ilusoes_semanal")` =
  `"torredasiluoessemanal"` (dois "ss" no meio). Use sempre `normalizar(...)` no código
  em vez de digitar a chave normalizada à mão (foi o bug que impediu a Torre semanal de
  ser salva).

### 5.4 Testes
- `messagebox.showinfo/showwarning/askyesno` **bloqueiam** o script. Nos testes,
  substituir antes de chamar qualquer ação (ver `teste_acoes.py`).
- Ao testar escrita no Supabase, restaurar o valor original no fim (o teste de
  integração faz isso).
- `login_prefs.json` fica na pasta do app (conta memorizada). Os testes devem
  limpá-lo antes/depois (`_salvar_prefs({})`).

### 5.5 💥 BUG CRÍTICO: "passa do login e a tela principal não abre"

**Sintoma:** depois do login bem-sucedido o app **fecha sozinho** (no `.exe`
e no fonte). Sem exceção no Python: o processo morre com
`alloc: invalid block` (erro de memória do C) e o `mainloop` do login nunca
retorna.

**Causa:** as telas novas usam `ImageTk.PhotoImage` (cenário, botão com
gradiente, ícones). Ao destruir a janela do login, o interpretador Tk é
finalizado; mas os `PhotoImage` continuavam referenciados pelo objeto
`LoginApp` → o `__del__` deles roda **depois** do interpretador e chama
`image delete` num Tk morto → corrupção de memória → o processo morre.

**Correção (já aplicada):** `_liberar_recursos()` em `login.py` e
`app_grandchase.py` — solta as imagens **antes** de `destroy()`:

```python
def _liberar_recursos(self):
    try:
        self.canvas.delete("all")
    except Exception:
        pass
    self.cenario_tk = None          # PhotoImage liberado com o Tk vivo
    self._fotos.clear()             # demais imagens (botao, icones)
```

**Regra:** sempre que uma janela com `ImageTk` for destruída, liberar as
imagens primeiro. Sem isso o crash aparece como "alloc: invalid block"
(sem traceback) ou como `invalid command name "...update"` no fechamento.

### 5.6 💡 Salvamento em segundo plano (implementado em 14/11)

**Problema:** `salvar_supabase()` rodava **sincrônico na thread da UI** e fazia
~100 requisições (uma por linha) → o app **congelava** por vários segundos a
cada salvamento, e ainda abria um `messagebox` de confirmação.

**Solução (3 peças):**

1. **Batch** — `supabase_db.salvar_conta()` grava cada tabela em **1 requisição**
   (25 personagens = 1 upsert; +1 para reler os ids; +1 por tabela filha)
   → de ~100 requisições para ~5. `_upsert_lote` separa linhas com `id`
   (merge) das novas (insert) porque o PostgREST exige chaves iguais no lote.
   **Atualizado (23/11, item 6 do AFAZERES):** agora vai **só o que mudou**
   (`so_alteradas()` compara com `self.originals` quando eles vieram do banco)
   numa **requisição só** à função `salvar_conta(dados jsonb)` do Postgres
   (`sql/salvar_conta.sql`), que grava as 4 tabelas numa **transação**: se uma
   linha falha, nada é gravado. Ela é `security invoker` (o RLS vale), não
   troca `user_id`/`character_id` num update e recusa `id` que não é da conta.
   Sem a função no banco, o app cai no jeito antigo e registra no log.
   Teste: `python tests/integracao/teste_salvar_atomico.py`.
2. **Thread de rede** — `salvar_supabase()` tira um *snapshot* dos dataframes e
   sobe uma `threading.Thread` que só faz I/O (nada de Tk). O resultado volta
   por `queue.Queue` e é lido na thread da UI por `after()` (`_verificar_salvamento`).
   O GC fica **desligado** durante o envio (senão ele pode finalizar um
   `tkinter.font.Font` na thread de rede → deadlock GIL × Tcl).
3. **Sem janelas de aviso** — o resultado (sucesso, erro ou colunas fora do
   banco) aparece **só na barra de status**. O `messagebox` foi removido do
   caminho do banco.

**Versionamento:** cada alteração passa por `_marcar_modificado()` (incrementa
`self._versao`). O salvamento guarda a versão enviada; se algo mudou durante o
envio, `_aplicar_resultado_salvamento` mantém `modified = True` e enfileira outro
salvamento (sem perder a edição).

**Números medidos (conta de teste, 25 personagens):** UI volta a responder em
**0,09s**; o envio termina em **1,7s** em background (antes: ~20s congelando).



### 5.7 💡 Card atualizando ao vivo + regras de cor (implementado em 14/11)

**Atualização ao vivo (pendência #2):**
- `CardPersonagem` deixou de ser "um desenho fixo": guarda os ids dos seus itens
  (`_itens`) e tem o metodo `atualizar(dados)` que apaga e redesenha.
- `app._atualizar_card(nome)` refaz os dados do personagem a partir dos
  dataframes (`_dados_personagem`) e chama `card.atualizar(...)`.
- A tela de edição (`janela_personagem.py`) tem `_aplicar_ao_df()` (escreve nos
  dataframes) e `_propagar()` (aplica + redesenha o card). E disparado por:
  cada checkbox (peças e dungeons), cada entry (`<Return>` e `<FocusOut>`) e cada
  dropdown (`<<ComboboxSelected>>`).
- ⚠ As chaves das tabelas filhas sao **normalizadas** ("Anel" -> "anel",
  "Void 4" -> "void4") — senao o card nao encontra os valores da planilha.

**Regras de cor dos acessorios** (`card_personagem.REGRAS_ACESSORIOS`):

| Acessório | Azul | Amarelo | Roxo | Vermelho |
|---|---|---|---|---|
| Anel | Piu Piu | Harkyon, Infinito II | — | Ciclo Infinito |
| Brinco / Piercing | Piu Piu, Harkyon, Dimensao Raro | Dimensao Epico | Dimensao Lendario | Outro Mundo do Caos |
| Tornozeleira | Eternidade | Harmonia, Consolacao | Escuridao | Apocalipse |

O texto do acessório e desenhado **com contorno (stroke) na cor da regra**
(8 cópias deslocadas + o texto por cima) -> sempre legível no fundo escuro.
As regras casam por **trecho do texto sem acento**, entao funcionam tanto com os
nomes da planilha ("Dimensão Épico") quanto com os do usuário
("Dimensão Completa").

**Peças de Void:** ✓ verde (tem) / ✗ **vermelho** (não tem), com o contador
"n/12 peças".

**Missões semanais:** o texto do chip ganha **contorno verde** (concluída) ou
vermelho-claro (pendente), além do fundo verde/vermelho.

**Título:** aparece no card no **badge dourado, abaixo do poder** ✓ (e o campo
`titulo` do personagem — o "Origem do Caos" e um dos títulos do jogo).

### 5.8 🐛 Bugs da tela de edição corrigidos (14/11)

**BUG A — "todos os cards abrem a edição do Zero"**

*O que acontecia:* o `tag_bind` da seta (>) usava a tag **"seta"**, que era
compartilhada por **todos** os 25 cards do canvas. Cada card novo sobrescrevia
o binding anterior — o último card desenhado (Zero) respondia a
**todos** os cliques.

*Correção:* cada card tem uma tag **exclusiva**
(`self.tag_seta = f"seta_{id(self)}"`), aplicada nos itens da seta e usada no
`tag_bind` (`card_personagem.py`).

```python
self.tag_seta = f"seta_{id(self)}"
...
self.create_text(..., tags=(self.tag, self.tag_seta))
self.canvas.tag_bind(self.tag_seta, "<Button-1>", lambda e, c=self: c.ao_abrir(c.dados))
```

⚠ Não usar tag literal compartilhada em item de canvas: o `tag_bind`
substitui o callback anterior.

**BUG B — "o que foi salvo não aparece marcado ao reabrir a edição"**

*O que acontecia:* a tela de edição lia a linha do dataframe com a
**chave lógica** ("arma", "anel", "void4"), mas o dataframe tem os
**cabeçalhos da planilha** ("Arma", "Anel", "Void 4"). O `dict.get()`
não casava → todos os campos crashavam de volta para o vazio (ou
mostravam o valor de outro personagem).

*Correção:*

1. `_linha_da_tabela()` agora devolve a linha com as chaves **normalizadas**
   (via `opcoes.coluna_banco`), que resolve a planilha e o banco:
   "Arma"/"arma" → `arma`; "Anel" → `anel`;
   "Altar da Ruína"/"altar_da_runha" → `altardarunha`;
   "Void 4" → `void4`.
2. Novo helper `_valor(linha, chave)` — le o campo pelo nome **resolvido**
   (com fallback para a chave crua).
3. `app._dados_personagem()` também normaliza as chaves das tabelas filhas
   com `coluna_banco` (antes usava `normalizar`, que **não** resolvia o
   alias "Altar da Ruína" → "altar_da_runha").

*Resultado:* salvar → fechar o app → abrir de novo → a edição
mostra tudo marcado (peças, dungeons, acessórios, números).

**Testes novos:**
- `teste_edicao_personagem.py` — clica **de verdade** na seta de 3 cards
  (evento sintético no canvas) e confere qual personagem abriu; confere
  que os campos marcados são os do personagem certo; salva, fecha, reabre.
- `teste_edicao_persistencia.py` — fluxo completo no Supabase: marca, salva,
  **destrói o app**, recria (recarrega do banco) e confere que voltou
  marcado (depois restaura o valor original).

### 5.9 💡 Nivel do Chaser no banco (implementado em 14/11)

**Regra:** o nivel do chaser e **um numero INTEIRO >= 0** e e **um valor por
conta** (vale para todos os 25 personagens).

**SQL (rodar no Supabase — SQL Editor):**

```sql
alter table public.user_characters
  add column if not exists nivel_chaser bigint default 385;
```

O arquivo esta pronto em `sql/nivel_chaser.sql`.

**STATUS (14/11): o SQL JA FOI RODADO** - a coluna existe e o app le e
grave o valor normalmente (validado no teste de persistencia: 384 ->
4242 -> app recriado -> 4242 -> restaurado para 384).

**Como funciona:**
- O valor fica na coluna `user_characters.nivel_chaser` e e gravado em **todas
  as linhas** da conta (um valor por conta).
- O app guarda o valor em `self.nivel_chaser` (inteiro) e o mostra no cartao
  "NIVEL DO CHASER" da tela principal.
- **Clicar no campo (ou no check) do cartao** abre a janela de edicao
  (`janela_nivel.py`): campo com o valor, validacao e botoes Salvar/Cancelar.
  O erro de validacao aparece **dentro** da janela (sem messagebox).
- Ao salvar: `app.definir_nivel_chaser(valor)` grava em todas as linhas do
  dataframe, atualiza o cartao e dispara o **salvamento em segundo plano**
  (sem travar e sem janela de aviso).

**Coluna opcional (degrade seguro):** `nivel_chaser` foi colocado em
`EXTRAS_OPCIONAIS["personagens"]` do `supabase_db.py` — a coluna so e enviada
se existir de fato no banco (sonda `select nivel_chaser limit 1`). Sem rodar o
SQL o app **continua funcionando** (usa 385 e mostra um aviso amarelo na
janela + na barra de status) em vez de quebrar todo o salvamento.

**Roteiro do dado (ida e volta):**

| Onde | Como |
|---|---|
| Banco -> app | `user_characters.nivel_chaser` -> `carregar_personagens()` -> rotulo "Nivel do Chaser" -> `app._ler_nivel_chaser()` |
| app -> banco | `app.definir_nivel_chaser()` -> coluna no dataframe (todas as linhas) -> `salvar_conta()` -> `_limpar(..., extras_geral)` -> `nivel_chaser` (bigint) |

**Alias necessario:** o rotulo e "Nivel do Chaser" (com "do") e a coluna do
banco e `nivel_chaser` (sem) — o alias em `opcoes.py`
(`ALIASES[normalizar("Nivel do Chaser")] = "nivel_chaser"`) junta os dois.
Sem ele a coluna nao seria gravada.

**Testes:** `teste_nivel_chaser.py` (validacao, cartao, janela, valor em todas
as linhas) e `teste_nivel_supabase.py` (grava, recarrega do zero e confere;
tambem prova que o app nao quebra quando a coluna ainda nao existe).

### 5.10 💡 Cards adaptaveis a QUALQUER resolucao (implementado em 14/11)

**Sintoma:** em FullHD (1920x1080) e QuadHD (2560x1440) o card ficava
ilegivel: os textos se sobrepunham ("TORRE"/"VOID UNIFICADO" em cima um do
outro, "DESPERTAR" por cima do numero, etc.).

**CAUSA RAIZ (3 bugs no `card_personagem.py`):**

1. **A fonte era escalada DUAS VEZES.** `self.f(tamanho)` ja devolve a fonte
   escalada e o `create_text` do card escalava de novo
   (`_escala_fonte`). Em escala 1.0 (1152) dava 1x1 = invisivel; em 1.6 o
   texto crescia 2.56x enquanto o layout crescia so 1.6x -> textos por cima
   de textos.
   *Correcao:* `create_text` **nao** mexe mais na fonte.

2. **Larguras misturavam px REAIS com px de DESIGN.** A quebra de linha dos
   chips de dungeon comparava uma largura em px reais com `LARGURA` (design)
   -> em telas grandes cada chip quebrava sozinho e sobrava metade do card
   vazia. O mesmo acontecia com o `_chip()` (que ainda era escalado 2x pelo
   `_painel`) e com a largura do retrato.
   *Correcao:* tudo em unidades de DESIGN (`_largura_design()`), o retrato
   tambem (`img.width / self.s`).

3. **O layout usava offsets fixos** enquanto a fonte do Tk e medida em
   PONTOS (depende do DPI da tela e nao escala de forma linear: 8pt = 13px
   em 1.0, mas 23px em 1.6).
   *Correcao:* o layout virou **metrico** - todas as alturas vem das
   metricas REAIS das fontes (`_alt()`, medida em runtime) e o card inteiro
   e montado por um unico metodo `_layout()` (usado tanto no desenho quanto
   no calculo da altura, para nunca divergirem).

**Gradacao da grade (`app_grandchase._escala_dos_cards`):**

| Tela | escala | colunas | card |
|---|---|---|---|
| 1152x820 (design) | 1.00 | 3 | 948px (cabe na rolagem) |
| 1920x1080 (FullHD) | 1.06 | 5 | 1044px (cabe na tela) |
| 2560x1440 (QuadHD) | 1.41 | 5 | 1369px (cabe na tela) |

Regras: (1) o card tem que CABER na altura da tela; (2) nunca fica menor
que o design aprovado (escala 1.0); (3) a grade tem que PREENCHER a largura
(evita metade da tela vazia). O `ALTURA_CARD_BASE` (950) e a altura do card
no design, usada para calcular a escala.

**Testes:** `teste_layout_card.py` (0 sobreposicoes em 4 escalas + o card
cabe na tela nas 3 resolucoes + a grade preenche a largura) e
`teste_resolucoes.py` (captura de tela em FullHD e QuadHD).

### 5.11 👉 Card INTEIRO clicavel (implementado em 14/11)

**Antes:** so a seta (→) abria a edicao do personagem.

**Agora:** clicar em **qualquer parte** do card abre a edicao **daquele**
personagem (nome, badges, titulo, painel de progresso, chips de dungeon,
pecas, acessorios, rodape, fundo do card).

**Como foi feito (`card_personagem.py`):**

1. Todos os itens criados pelo card recebem a tag **exclusiva** do card
   (`self.tag` = `card_<n>`) — o metodo `_tag()` injeta a tag em todo
   `create_text/create_image/create_oval/create_rectangle`.
2. Um unico `tag_bind` da tag do card abre a edicao:

```python
self.canvas.tag_bind(self.tag, "<Button-1>", lambda e, c=self: c.ao_abrir(c.dados))
self.canvas.tag_bind(self.tag, "<Enter>", lambda e: self.canvas.configure(cursor="hand2"))
self.canvas.tag_bind(self.tag, "<Leave>", lambda e: self.canvas.configure(cursor=""))
```

3. A seta continua com a tag dela (`tag_seta`), que tem **prioridade maior**
   no Tk (tag criada depois) — abre a mesma tela.

⚠ Como a tag e **exclusiva por card**, clicar num card nao interfere
nos outros 24 (testado). O scroll da pagina (<MouseWheel> no canvas)
nao conflita com o clique.

**Teste:** `teste_card_clicavel.py` — clica em 5 partes diferentes do card
(nome, bloco, peca, fundo, rodape) de 3 personagens e confere que a edicao
do personagem **certo** abre, alem de conferir que nao ha mistura entre
cards.

### 5.12 🔢 Dropdowns do Despertar e da Liberacao (14/11)

**Regras do usuario:**

| Secao | Campo | Opcoes |
|---|---|---|
| DESPERTAR | Núcleos | `0 / 13` ... `13 / 13` (so ate 13/13, **sem** o resto da lista da planilha) |
| DESPERTAR | Épicos+ | `0 / 9` ... `9 / 9` |
| LIBERTAÇÃO | Núcleos | `0 / 9` ... `9 / 9` (agora **dropdown**, era campo numerico) |
| LIBERTAÇÃO | Épicos+ | `0 / 4` ... `4 / 4` (agora **dropdown**) |

**Implementacao (`janela_personagem.py`):**

```python
OPCOES_DESPERTAR_NUCLEOS = [f"{i} / 13" for i in range(14)]
OPCOES_DESPERTAR_EPICOS = [f"{i} / 9" for i in range(10)]
OPCOES_LIBERTACAO_NUCLEOS = [f"{i} / 9" for i in range(10)]
OPCOES_LIBERTACAO_EPICOS = [f"{i} / 4" for i in range(5)]
```

- `_campo_combo()` ganhou o parametro `fracao=True`: o combo mostra
  "5 / 9" mas o **banco guarda so o numero** (a coluna
  `libertacao_nucleos`/`libertacao_epicos` e bigint — gravar "5 / 9"
  seria recusado pelo PostgREST).
- `_aplicar_ao_df()` trata o item `("geral", coluna) -> (combo, "fracao")`:
  grava `_num(combo.get())` (o numero), sem o limite/maximo dos campos
  numericos.
- `_fracao_texto(valor, maximo)` normaliza o que vem do banco
  ("13/13" ou 13 -> "13 / 13") e **nao inventa** "0 / 13" para quem esta
  vazio (continua vazio).
- As listas da tela de edicao **substituem** a lista da planilha
  (`opcoes.OPCOES["Geral"]["nucleo"]` ainda tem o "1/9 ... 9/9" porque
  aquele arquivo e gerado da planilha e nao se mexe a mao).

**Teste:** `teste_dropdowns_liberacao.py` — confere as 4 listas, grava a
liberacao (7/9 e 3/4), confere que o dataframe recebe **numero** (7 e 3, nao
texto), que o card mostra o valor, que ao reabrir o dropdown vem preenchido,
que grava no Supabase e que o original e restaurado.

### 5.13 📃 Contador "DESPERTAR COMPLETO" (corrigido em 14/11)

**Sintoma:** o contador "DESPERTAR COMPLETO" da tela *Caminho da Maestria* nao
mudava quando o personagem terminava o despertar.

**Causa (dois bugs):**

1. `app._despertar_completo()` contava os personagens com **TODAS as pecas de
   Void em VERDADEIRO** — nao tinha nada a ver com o despertar. Agora
   conta quem tem **Núcleos 13/13 e Épicos+ 9/9**.
2. A tela de edicao (`_propagar`) redesenhava o **card do personagem**, mas
   nao os **cartões de estatistica** do hero — entao o contador so
   mudava ao fechar/reabrir. Agora `_propagar()` tambem chama
   `app._atualizar_cards()` (muda **ao vivo**).

**Regra da comparacao:** o codigo compara o **valor** (o numerador da
fracão), e nao o texto inteiro:

```python
if _fracao(nucleo)[0] == 13 and _fracao(epicos)[0] == 9:
    completos += 1
```

Assim funciona tanto para "9 / 9" (formato do dropdown novo) quanto para
"9 / 13" (formato antigo da planilha, em que o denominador dos épicos+
estava errado) — e bate com o que o dropdown mostra na tela
(`_fracao_texto` normaliza para "9 / 9").

**Teste:** `teste_contador_despertar.py` — confere que o contador bate com
os dados, completa o despertar de um personagem pela tela de edicao e
confere que o contador **sobe 1 na hora** (sem clicar em Salvar), e depois
restaura.

**Observacao:** o contador "LIBERTAÇÃO COMPLETA" foi corrigido
depois (ver 5.14): agora usa as **3 condições** (estado VERDADEIRO +
Núcleos 9/9 + Épicos+ 4/4).

### 5.14 📃 Contador "LIBERTAÇÃO COMPLETA" (14/11)

**Regra do usuario:** a liberação só esta **completa** quando as
**3 condições** acontece ao mesmo tempo:

1. o campo **Libertação** (estado) = `VERDADEIRO`
2. **Núcleos** = `9 / 9`
3. **Épicos+** = `4 / 4`

**Implementacao (`app_grandchase._libertacao_completo`):**

```python
for estado, nucleos, epicos in zip(df[col_estado], df[col_nucleo], df[col_epicos]):
    if not _verdadeiro(estado):
        continue
    if _fracao(nucleos)[0] == 9 and _fracao(epicos)[0] == 4:
        completos += 1
```

- Compara o **valor** (numerador) da fração — funciona com "9 / 9"
  (formato do dropdown) e com o numero puro (como o banco guarda).
- Se as colunas de progresso não existirem na tabela (planilha antiga, modo
  local), conta só pelo estado (regra antiga) em vez de zerar.
- Grava no mesmo contador "LIBERTAÇÃO COMPLETA" do hero e atualiza
  **ao vivo** na tela de edição (ver 5.13).

**Teste:** `teste_contador_libertacao.py` — confere que as 3 condições
juntas sobem 1, que **cada uma faltando** não conta, e que a mudança pela
tela de edição acontece ao vivo.

### 5.15 🧹 Pendencia #10: coluna antiga removida (14/11)

**A coluna `fragmentos_facis`** era a versão ANTIGA do contador de
"Fragmento do Vazio Disperso" (hoje é `fragmento_vazio_disperso`).

**Estado do banco (verificado):** a coluna **JA NAO EXISTIA** — o schema
estava limpo. O que ainda existia era o **código morto** que falava
nela:

| Onde | O que era | O que ficou |
|---|---|---|
| `app_grandchase.COLUNAS_IGNORADAS` | lista de colunas obsoletas a descartar ao carregar | removida (o mecanismo inteiro) |
| `app_grandchase._rotular_colunas` | descartava a coluna do dataframe | removido |
| `app_grandchase._dados_personagem` | `or linha_geral.get("fragmentos_facis")` (fallback) | removido |
| `teste_card.py` | dado de exemplo com a coluna velha | trocado por `fragmento_vazio_disperso` |

**Schema atual (checado pelo teste):**

| Tabela | Colunas | Fora do esperado |
|---|---|---|
| `user_characters` | 16 | nenhuma |
| `user_pecas_void` | 15 | nenhuma |
| `user_acessorios_titulo` | 8 | nenhuma |
| `user_semanais` | 10 | nenhuma (a `torre_das_ilusoes_semanal` é a opção esperada) |

**Teste:** `teste_schema_limpo.py` — confirma que a coluna antiga não
existe, que **nenhuma** tabela tem coluna fora do que o app conhece e que o
app salva sem reclamar de "colunas fora do banco".

**Bônus:** `teste_card.py` (que estava quebrado desde a mudança do card
para o canvas) foi arrumado e voltou a funcionar — gera a previa do card
do Uno.

### 5.16 🎯 MISSÃO RÁPIDA (implementado em 14/11)

O botao **"Missao Rapida"** do hero antes so ligava/desligava um *filtro* da
tabela de personagens (que esta oculta) — nao marcava nada. Agora ele abre o
**painel flutuante** e liga o **modo rapido nos cards**.

**Como usar (3 formas de marcar):**

| Forma | Como | Atalho |
|---|---|---|
| **Painel flutuante** (modo PAINEL) | Botao "Missao Rapida" (ou tecla **M**) -> escolhe o personagem -> clica nas missoes -> **Salvar (N)** | `M`, `1`-`7`, `Ctrl+Enter`, `Esc` |
| **Modo rapido nos cards** (modo CARD) | Com o modo ligado, **clica direto no chip** da missao no card (marca/desmarca) | — |

**So UM dos dois por vez:** abaixo do botao "Missao Rapida" tem um **check**
que escolhe o modo:

```
[x] Modo: clicar no card      -> o card NAO abre a edicao (so marca)
[ ] Modo: painel (janela)     -> o card continua abrindo a edicao normal
```

O check fica **marcado** (verde) no modo CARD e **desmarcado** no modo
PAINEL (padrao). O texto ao lado mostra sempre o modo ativo.
| **Fora do modo** | Clicar no chip ainda **abre a edicao** do personagem (como antes) | — |

**No modo CARD o card NAO abre a edicao** (pedido do usuario): o card
vira so um marcador de missao. `app._abrir_personagem()` bloqueia a
abertura enquanto `self.missao_rapida` estiver ligado **e** o modo for
CARD (e avisa na barra de status que e preciso desligar o modo para
editar). No modo PAINEL o card abre a edicao normalmente.

**Implementacao do check:** `app._desenhar_chave_missao()` (desenha a caixa
+ o rotulo no hero, em `tema_visual.MISSAO_MODO`), `app.alternar_modo_missao()`
(alterna `app.missao_modo` entre `MODO_MISSAO_JANELA` e `MODO_MISSAO_CARD` e
reaplica o modo) e `tema_visual.caixa_check()` (a caixa vazia/marcada).

- O painel tem **busca** de personagem (lista filtrada) e mostra o estado
  atual: **verde** = ja feita no banco, **amarelo** = mudanca pendente.
- Varias missoes podem ser marcadas **de uma vez** e gravadas em **UMA**
  gravacao (o app ja salva em 2o plano, sem travar).
- O **ultimo personagem usado** fica guardado (para o painel ja abrir nele).
- O card e os **contadores** da tela principal (VOID 4, CAMINHO ABISSAL...)
  atualizam **na hora**.
- O botao fica **VERDE** (fundo solido + texto escuro) enquanto o modo esta
  ligado, e volta ao normal quando desliga. O fundo verde e criado ANTES
  do icone/texto (`_desenhar_botao` -> `self.itens_verde[chave]`) para
  ficar atras deles; `_marcar_botao()` mostra/esconde.

**Implementacao:**

- `janela_missao_rapida.py` (novo) — o painel.
- `app.marcar_missoes(nome, {chave: bool})` — aplica e grava (1 gravacao).
- `app.alternar_missao_rapida(chave, nome)` — clique no chip do card.
- `app.alternar_missao()` — liga/desliga o modo (e abre/fecha o painel).
- `card_personagem.py` — os chips ganharam a tag `missao_<n>_<chave>`, criada
  **depois** da tag do card, entao tem **prioridade** no canvas: o clique no
  chip NAO abre a edicao quando o modo esta ligado.
- `app._lembrar_personagem_missao()` / `_ler_ultimo_personagem()` — guardam o
  ultimo personagem (coluna opcional `user_profiles.missao_rapida_personagem`).

**SQL (opcional):** `sql/missao_rapida.sql` —

```sql
alter table public.user_profiles add column if not exists missao_rapida boolean default false;
alter table public.user_profiles add column if not exists missao_rapida_personagem text;
```

Sem essas colunas o app funciona normal (so o ultimo personagem fica
nesta sessao).

**Teste:** `teste_missao_rapida.py` — abre o painel, marca 3 missoes de uma
vez, confere o dataframe/o card/o contador, marca pelo chip do card, confere
que fora do modo o chip abre a edicao, guarda o ultimo personagem e restaura
os valores.

### 5.17 🐛 Bug: "Zerar dungeons semanais" nao desmarrava o card

**Sintoma:** ao clicar em **"Zerar dungeons semanais"**, os cartões de
estatística do hero zeravam, mas os **cards de personagem continuavam
com as missoes marcadas** (o chip ficava verde).

**Causa:** `app.zerar_dungeons()` escrevia "Falso" no dataframe e chamava
**so** `_atualizar_cards()` — que atualiza os **cartões de estatística**
do hero. Os **cards de personagem** sao outra coisa: cada um e um
`CardPersonagem` desenhado no canvas, que so e redesenhado por
`_atualizar_card(nome)` (um a um).

**Correção:** novo metodo `app._atualizar_todos_os_cards()` que redesenha
todos os cards de personagem, e `zerar_dungeons()` passou a chama-lo:

```python
self._atualizar_cards()          # os cartoes do hero
self._atualizar_todos_os_cards() # os cards de personagem
```

**Teste:** `teste_zerar_dungeons.py` — marca missoes, clica em zerar e confere
que o dataframe zerou, que **o card desmarcou** e que os contadores do hero
zeraram. (O teste foi validado: revertendo a correção ele falha.)

### 5.18 🎨 Ajustes finos de estetica (14/11)

**1) CARD — o retrato agora ocupa uma AREA FIXA**

O retrato tinha proporcoes diferentes em cada personagem (a largura variava
de 76 a 156 px de design), entao ele **invadia o badge do nome** e o texto
do cabecalho era cortado de um jeito diferente em cada card.

*Correcao:* `card_personagem.RETRATO_LARGURA = 112` e `RETRATO_TOPO = 46`
(definem a area reservada, logo abaixo do badge do nome). O retrato e
escalado para caber nessa area (proporcao mantida) e o texto
(eyebrow/titulo/credito) usa a **largura fixa** da area — assim todos
os cards ficam iguais. O cabecalho ficou um pouco mais alto
(`alt_cabecalho` = credito + 33) para dar espaco ao retrato.

**2) CARD — bug do `_chip`: reticencia sempre**

O `_chip()` colocava "…" **mesmo quando o texto cabia inteiro** (a
condicao era "se cabe com reticencia, acrescenta"). Por isso aparecia
"Origem do Caos..." e "Outro...". Agora a reticencia so entra quando o
texto **nao** cabe.

**3) CARD — titulo e eyebrow mais refinados**

- O titulo/origem ("Origem do Caos") foi de 12 para **11** (mais leve).
- O eyebrow "PERSONAGEM DE GRAND CHASE" perdeu o **negrito** (ficou normal,
  com tracking 1.0) — mais elegante, e agora cabe **inteiro** em
  todos os cards.

**4) LOGIN — o logo nao e mais cortado**

`tema_login.LOGO_*`: o logo (545 px) ultrapassava a borda direita da janela
e invadia o cartao do formulario. Agora e **424 px**, centralizado no
espaco livre a direita do cartao (`LOGO_CX = 754`, `LOGO_CY = 378`).

### 5.19 🔍 BARRA DE FILTROS (feature nova, 14/11)

Ficou **acima dos cards**, no mesmo estilo do mockup: um campo de busca +
tres paineis de vidro com as opcoes circulares.

**Como funciona**

| Parte | Regra |
|---|---|
| **Não fez estas masmorras semanais** | mostra quem **ainda não concluiu pelo menos uma** das mazmorras marcadas (Vazio 1,2 e 3 / Vazio 4 / Caminho Abissal / Torre das Ilusões) |
| **Ordenar por Void** | a lista fica em **ordem decrescente pela soma** dos Void marcados (Vazio Unificado / Vazio Apocalipse) |
| **Progresso incompleto** | mostra quem **não completou** o despertar e/ou a libertação (com os dois marcados, quem está incompleto **nos dois**) |

**Ordem sempre do mais forte para o mais fraco:** pelo **Ataque Total**
(maior -> menor) — ou pela soma do Void, se o filtro "Ordenar por Void"
estiver marcado. A lista se **reordena em tempo real** quando os dados mudam
(marcar missão, zerar, editar).

**Implementacao**

- `tema_visual.py`: `FILTROS_PAINEL1..3`, `FILTROS_FIM` (onde a grade de
  cards começa), `circulo_opcao()` (o botão redondo) e os icones
  **funil** e **ordenar** (desenhados com PIL, como o ↻).
- `app_grandchase.py`:
  - `FILTRO_MAZMORRAS`, `FILTRO_VOID`, `FILTRO_PROGRESSO`, `FILTRO_ATAQUE`
    (as opcoes);
  - `app.filtro_mazmorras`, `app.filtro_ordem_void`, `app.filtro_progresso`
    (o estado);
  - `_dados_filtro(nome)` (os dados de cada personagem), `_filtrar_personagens()`
    (filtra + ordena), `_alternar_filtro()`, `_aplicar_filtros()`,
    `_redesenhar_cards()`;
  - `_desenhar_filtros()` / `_desenhar_painel_filtro()` (o desenho no canvas) e
    `_quebrar()` (o texto de ajuda quebra dentro do painel);
  - `_redesenhar_filtros()` (redesenha a barra ao clicar num filtro — sem
    isso o CHECK nao aparecia) e `_reposicionar_cards()` (move/esconde os
    cards sem recriar tudo — ver 5.20);


**Armadilhas resolvidas (nao repetir):**

- `lay.caixa()` ja devolve **pixels**: usar `lay.f()` (não `lay.w()/lay.h()`)
  nosOffsets, senão a barra escala **duas vezes** (só aparecia
  certo em 1152 e quebrava em FullHD).
- `CTkEntry.insert(0, "")` faz o **placeholder sumir**: so inserir se
  houver texto.
- O texto de ajuda precisa ser **quebrado em linhas** (o canvas nao faz
  wrap automatico) — senao ele vaza por cima do painel vizinho.

**Teste:** `teste_filtros.py` — confere a ordem (mais forte -> mais fraco), a
busca em tempo real, os tres filtros e a reordenação em tempo real.

### 5.20 🔄 Ajustes dos filtros + "Ataque Total" (15/11)

**1) Rótulos**
- Tela de edição: **"Poder" -> "Ataque Total"**.
- Tela Caminho da Maestria: **"PODER MÉDIO" -> "ATAQUE TOTAL MÉDIO"**.

**2) Novo filtro "Ordenar por Ataque Total"**

Uma 4ª barra (slim, abaixo dos 3 paineis) com a opção **Ataque
Total**: a lista passa a ser ordenada pelo ataque, do maior para o menor.
⚠ E um grupo **separado** do "Ordenar por Void" — misturar as duas
somas nao faria sentido (o Void e da ordem de dezenas, o Ataque de milhoes).

**3) Os filtros passaram a responder ao clique**

O motivo: `_aplicar_filtros()` redesenhava **so os cards** — a barra de
filtros ficava com o desenho antigo, entao o CHECK nunca aparecia (e a barra
duplicava). Agora `_aplicar_filtros()` tambem chama `_redesenhar_filtros()`
(apaga os itens com a tag "filtros" e desenha de novo).

A opção ativa mostra um **CHECK** dentro do circulo
(`tema_visual.circulo_opcao()` desenha o "✓" com o PIL).

**4) O congelamento: 8,2x mais rápido**

| | antes | agora |
|---|---|---|
| aplicar um filtro | **1,64s** | **0,20s** |

Duas causas e duas solucões:

- **os 25 cards eram recriados do zero** a cada mudança de filtro (25
  cards x ~200 itens no canvas + os retratos redimensionados). Agora os cards
  sao apenas **movidos** (`CardPersonagem.mover_para()`) ou **escondidos**
  (`definir_visivel()`) — `_reposicionar_cards()`.
- **os retratos eram redimensionados (LANCZOS) toda vez** — agora tem
  **cache** (`card_personagem.retrato_pronto()`).
- A busca tem um **debounce de 120ms** (`_busca_digitada`): continua
  "tempo real", mas nao redesenha a lista a cada tecla.

**Teste:** `teste_filtros.py` — clica nas opcoes de verdade (evento
sintetico), confere o CHECK, o filtro de Ataque Total, a busca, os filtros
e mede o **tempo** de aplicar um filtro (limite de 1,2s).

### 5.21 🗑 Ajustes de 15/11 (sem busca e sem o filtro de Ataque Total)

**1) "Poder" -> "Ataque Total"** na tela de edição.

⚠ O rótulo estava **fixo** na chamada (`_campo_numero(..., "Poder", "Poder", ...)`)
e não vinha do `CAMPOS_GERAIS` — por isso a troca anterior não
aparecia na tela.

**2) A busca por texto foi REMOVIDA**

Deu muitos bugs (deslocamento visual, o campo "travando" ao digitar) e o
utilitário ficou limitado: o filtro por nome não é mais confortável
deixar a lista inteira preparada (ordem fixa) e usar os filtros.

Saiu: o `CTkEntry`, a lupa, o placeholder, o `_busca_digitada`, o debounce e o
`filtro_busca`.

**3) O filtro "Ordenar por Ataque Total" foi REMOVIDO**

Agora **não existe filtro para isso**: a lista e **sempre** ordenada pelo
**Ataque Total** (do maior para o menor). O filtro "Ordenar por Void" continua
existindo e, quando marcado, troca a ordenação para a soma do Void
selecionado.

```python
if self.filtro_ordem_void:      # marcado: ordena pelo Void
    ...
else:                           # padrao: SEMPRE pelo Ataque Total
    return sorted(nomes, key=lambda n: (dados.get(n) or {}).get("ataque", 0),
                  reverse=True)
```

A barra ficou com **3 paineis** (sem a busca e sem a 4ãa barra) e os cards
começam logo depois (`FILTROS_FIM = 1136`).

**4) O congelamento dos filtros caiu ainda mais**

| | antes | agora |
|---|---|---|
| aplicar um filtro | 1,64s | **0,10s** |

**Teste:** `teste_filtros.py` (a busca saiu do teste; a ordem padrao agora e
verificada pelo **Ataque Total**).

### 5.22 👤 PERFIL no espaco vago do hero (15/11)

O painel de vidro que estava vazio no "Caminho da Maestria" (o bloco que
antes era o "Import Excel") virou o **PERFIL**:

```
[ (foto) ]  Lv. 402 - Testador               (icone do nivel, a direita)
             Clique para abrir o perfil e editar
```

O texto e **"Lv. <nivel do chaser> - <nick>"** (o nivel em laranja, o nick
em branco).

**O que tem:**

| Item | Detalhe |
|---|---|
| **Foto** | qualquer imagem do computador (PNG/JPG/WEBP); redimensionada para 128x128, em circulo, e guardada **no Supabase** (base64 na coluna `user_profiles.avatar`) |
| **Nick** | vem **depois** do nivel (padrao: o nome do e-mail) e e **editavel** na tela de perfil (coluna `user_profiles.nick`) |
| **Nivel** | o **Nivel do Chaser** da conta (a mesma coluna `nivel_chaser`), em laranja, **sem parenteses** |
| **Icone do nivel** | no lado direito, com **opacidade reduzida** (35%), vem da pasta `assets/chaser/` |
| **Sem barra de EXP** | como pedido |

**O icone por nivel:** o app procura na pasta `assets/chaser/` o arquivo do
"bloco" de 100 em que o nivel cai:

| Nivel | Arquivo | Nivel | Arquivo |
|---|---|---|---|
| 1-99 | `cl1.png` | 500-599 | `cl500.png` |
| 100-199 | `cl100.png` | 600-699 | `cl600.png` |
| 200-299 | `cl200.png` | 700-799 | `cl700.png` |
| 300-399 | `cl300.png` | 800-899 | `cl800.png` |
| 400-499 | `cl400.png` | 900-999 | `cl900.png` |

```python
marco = 1 if nivel < 100 else (nivel // 100) * 100
```

Se o arquivo nao existir, o app **nao desenha** o icone (sem erro). A pasta
`assets/chaser/` tem um `LEIA-ME.md` com essa regra, e o `.spec` ja leva a
pasta para o build.

**Cache:** os PNGs do usuario tem ~1 MB cada (10 icones = ~12 MB). O app
guarda o icone ja redimensionado em cache (`app._cache_icone_chaser`, com a
data do arquivo na chave) - sem isso, cada redesenho da tela carregava e
redimensionava 1 MB de novo.

**A janela "Minha conta"** (`janela_perfil.py`): foto, Nick, **trocar
e-mail**, **trocar senha** e **SAIR DA CONTA (logout)**. O e-mail e a senha
usam o **Supabase Auth** (`supabase_db.trocar_email` / `trocar_senha`).

**SQL (opcional):** `sql/perfil.sql` —

```sql
alter table public.user_profiles add column if not exists nick text;
alter table public.user_profiles add column if not exists avatar text;
```

Sem essas colunas o app funciona normal (o nick e a foto so valem nesta
sessao — o app avisa).

**Teste:** `teste_perfil.py` — confere o perfil no hero, o icone do nivel, a
janela, o nick, o avatar (base64) e a ida e volta no Supabase.

**A versao final do perfil** (foto dos 25, barra de EXP e tempo real) esta
na secao **5.23**.

### 5.23 🔄 Perfil v2: foto dos 25, barra de EXP e tempo real (15/11)

**1) A foto do perfil NAO e mais livre: e uma das 25**

A tela "Minha conta" virou uma **grade com os 25 personagens**; clicar em
um usa a foto dele. Os arquivos ficam na pasta `assets/perfil/` e se chamam
**`<personagem>_icon.png`** (em minusculas): `elesis_icon.png`, `lire_icon.png`,
`arme_icon.png` ... `ereb_icon.png` (a lista completa esta no `LEIA-ME.md`
da pasta).

O que e guardado no Supabase (coluna `user_profiles.avatar`) e o **NOME do
personagem** (ex.: "Elesis") — bem mais leve que guardar a imagem em
base64. (O formato antigo, base64, ainda e lido.)

**2) A barra de EXP**

Como no esboço: a barra preenche conforme o **Nivel do Chaser**:

| Nivel | Preenchimento | Nivel | Preenchimento |
|---|---|---|---|
| 1 | 0,1% | 100 | 10% |
| 10 | 1% | 402 | 40,2% |
| 50 | 5% | 999 | 99,9% |

```python
percentual = min(100.0, float(self.nivel_chaser or 0) / 10.0)
```

A barra fica abaixo do texto, com o rotulo "EXP" a esquerda e o percentual a
direita.

**3) O icone do nivel maior e mais visivel**

O icone (`assets/chaser/clN.png`) preenche o espaco vazio do painel:
**142 px** (redimensionando se preciso), com a opacidade em **70%**. Ele
fica dentro do painel do perfil (nao invade o texto, a barra de EXP nem os
botoes do cabecalho).

| | antes | agora |
|---|---|---|
| tamanho | 92 px | **142 px** |
| opacidade | 35% | **70%** |

**4) Atualizacao em tempo real**

O perfil do hero e redesenhado quando o **Nick** muda (na tela de perfil), o
**Nivel do Chaser** muda (`definir_nivel_chaser`) e a **foto** e trocada
(clicar em outro personagem na grade) — sem precisar recarregar o app.

**Detalhes que evitam bug:**

- `_desenhar_perfil()` **apaga** o desenho anterior (`canvas.delete("perfil")`)
  — sem isso os itens se acumulavam a cada atualizacao e o texto ficava
  sobreposto;
- as fotos da janela usam **`CTkImage`** (o `CTkButton`/`CTkLabel` do CTk 6
  nao escala uma `ImageTk.PhotoImage` em telas HiDPI);
- o recorte quadrado pega o **topo** de uma imagem vertical (onde fica o
  rosto) e o centro das quadradas (`tema_visual.recorte_quadrado`).

**Teste:** `teste_perfil.py` — confere a ordem do texto, a **barra de EXP**,
a **foto dos 25**, a atualizacao em tempo real e a persistencia.

### 5.24 🎨 Pendencia #9: ajustes finos de estetica (15/11)

**1) A grade das 25 fotos cabia na tela**

A janela "Minha conta" era pequena (480x640) e a grade rolava: dava para ver
so 3 colunas e meia. Agora a janela e **620x900** e a grade tem altura para
as **5 linhas de 5** — **os 25 icones aparecem de uma vez**, sem rolar.

⚠ As colunas da grade tem **largura fixa** (`grid_columnconfigure(...,
weight=0, minsize=62)`): sem isso o Tk espalha as colunas e a 5a saia da
tela (eram 4 visiveis).

**2) O circulo do filtro estava desalinhado do texto**

O circulo e desenhado com `anchor="w"` (o meio dele fica em `y`), mas o texto
usava `anchor="nw"` (o topo em `y`) — o circulo ficava ~9 px **acima** da
linha do texto. Agora o texto tambem usa `anchor="w"` (centralizado na
vertical), entao os dois ficam na **mesma linha**.

**3) Pente fino no resto**

| Onde | Ajuste |
|---|---|
| Paineis de filtro | a altura encolheu (240 -> 214 px): o texto de ajuda encosta embaixo e **some o espaco vazio** do rodape |
| Card — "VOID" | estava 6 px a esquerda do "EQUIPAMENTOS"; agora sai do mesmo `x` (alinhado) |
| `tema_visual` | removidos os constantes mortos (`FILTROS_PAINEL4`, `FILTROS_BUSCA`) |
| `.spec` | a pasta `assets/perfil/` entra **so com os PNG** (o `.venv` que o script de icones deixou tem **400 MB** e nao pode ir no build) |

**Teste:** a suite completa segue verde (o `teste_layout_card.py` garante que
o card continua sem sobreposicao em 4 escalas).

> **O icone do SIEGHART tambem foi refeito**: o `sieghart_icon.png`
> estava "completamente apagado" e o `SIEGHART.png` que o usuario tinha
> colocado nao servia (89x90, quase branco). O icone foi gerado a partir do
> **retrato original** (`assets/personagens/sieghart.png`), com o mesmo
> processo dos outros 24 (rembg -> auto-crop -> 128x128 -> nitidez).
>
> **O `elesis_icon.png` foi gerado** (a partir do `ELESIS.png` que o
> usuario colocou na pasta), com o mesmo processo do script dele: `rembg`
> (remove o fundo) -> auto-crop -> 128x128 com margem de 4px -> centro +
> `UnsharpMask`. O `.venv/Scripts/python.exe` tem o `rembg` instalado (o
> erro do log foi no `pip install`, mas as libs ficaram).
>
> ⚠ O `ELESIS.png` (a fonte) pode ficar na pasta: o app so procura
> `<personagem>_icon.png`.
### 5.25 🖥 Nome do app no Windows + icone proprio (16/11)

**O nome agora e so "Caminho da Maestria":**

| Onde | Antes | Agora |
|---|---|---|
| Titulo da janela principal | `Controle Grand Chase - Caminho da Maestria` | **`Caminho da Maestria`** |
| Titulo do login | `Controle Grand Chase - Entrar` | `Caminho da Maestria - Entrar` |
| Executavel | `Controle Grand Chase.exe` | **`Caminho da Maestria.exe`** |
| Exportacao do Excel | `Controle Grand Chase.xlsx` | `Caminho da Maestria.xlsx` |

(O titulo do login ficou diferente de proposito: o `FindWindow` dos testes
E2E busca o titulo **exato**, e as duas janelas nao podem ter o mesmo.)

**O icone do .exe E da janela**

O executavel usava o icone padrao do PyInstaller. Agora usa o **emblema do
Akkatsuki** (o logo do app), gerado em **`assets/app.ico`** (16, 24, 32, 48,
64, 128 e 256 px) pelo novo script **`assets/make_icon.py`** (ele recorta a
parte visivel do `assets/login.png` e grava o .ico).

O icone tambem foi aplicado **na janela** (`iconbitmap`), que usava o icone
padrao do Tk (o quadrado azul):

```python
def _aplicar_icone(self):
    caminho = caminhos.icone_app()          # assets/app.ico
    if os.path.exists(caminho):
        self.iconbitmap(caminho)
```

O `.ico` tambem entra no `datas` do build (o `icon=` do spec so vale para o
executavel).

```python
# no "Controle Grand Chase.spec"
EXE(name='Caminho da Maestria', icon=os.path.join(SPECPATH, 'assets', 'app.ico'))
```

**Testes:** `teste_login_exe.py` e `teste_login_exe_resolucao.py` foram
atualizados (titulos e caminho do executavel).

> ℹ️ O `assets/app.ico` foi **trocado depois** pelo usuario (o
> grimorio dourado, feito a mao) e virou o icone de **todas** as janelas.
> Ver 5.30.

### 5.26 🎨 Os 4 icones de perfil refeitos (16/11)

**O que estava ruim:** os icones do **Rey**, **Sieghart**, **Ryan** e
**Lupus** tinham ficado **escuros**, **recortados demais** (so viravam um
fragmento do personagem) e o do **Sieghart** com uma **arte diferente** dos
outros 21.

**Causa:** o `rembg` (remocao de fundo) nao funciona bem nessas 4 artes
(vira so um pedaco) e as artes escuras do jogo continuavam escuras depois
do recorte. Alem disso, o `rembg` so existe no venv da pasta:
`assets\perfil\.venv\Scripts\python.exe`.

**Correcao:** os 4 foram refeitos a partir dos **retratos que o app ja
usa** (`assets/personagens/<nome>.png` — a mesma arte dos cards), com o
mesmo esquema dos outros 21:

1. **recorte da CABECA** (caixa por personagem, em porcentagem da arte);
2. `rembg` para tirar o fundo;
3. auto-crop + 128x128 com margem de 6 px;
4. **clareamento automatico** — `gamma 0.72` (levanta as sombras) +
   `autocontrast` + brilho automatico ate a luminancia media de 132
   (as artes escuras do jogo ficavam "apagadas");
5. `UnsharpMask` para definir os detalhes.

**O script ficou no projeto:** **`assets/perfil/gerar_icone.py`**

```
assets\perfil\.venv\Scripts\python.exe assets\perfil\gerar_icone.py rey
```

As caixas de recorte ficam no dicionario `RECORTES` do proprio script (cada
retrato tem a personagem em um lugar diferente):

| Personagem | Caixa (x1, y1, x2, y2) | Extra |
|---|---|---|
| rey | 0.29, 0.00, 0.60, 0.30 | — |
| sieghart | 0.20, 0.02, 0.47, 0.33 | brilho 1.55 (cabelo preto) |
| ryan | 0.52, 0.05, 0.80, 0.40 | — |
| lupus | 0.28, 0.00, 0.48, 0.28 | — |

**Resultado (luminancia media dos pixels visiveis):**

| Icone | antes | agora | (outros 21 ficam entre 83 e 130) |
|---|---|---|---|
| rey | 70 | **83** | |
| sieghart | 68 | **111** | |
| ryan | 32 | **106** | |
| lupus | 78 | **92** | |

Agora os 4 mostram a **cabeca com o rosto** (como os outros 21), claros e
com a **mesma arte dos cards**.

⚠ **Armadilha do Windows (aconteceu 2x):** `REY.png` e `rey_icon.png`
sao arquivos **diferentes**, mas `REY.png` e `rey.png` sao o **mesmo
arquivo** (o Windows ignora as maiusculas). Ao gerar um icone a partir de
uma fonte, o destino tem que ser o nome **completo** (`rey_icon.png`),
senao a fonte e sobrescrita. As 4 PNGs que o usuario havia colocado em
`assets/perfil/` foram sobrescritas por esse bug — por isso os icones
foram refeitos a partir de `assets/personagens/`.

### 5.27 🎨 Icone do Sieghart a partir da arte chibi (16/11)

O usuario colocou de novo a arte **chibi com moldura** do Sieghart em
`assets/perfil/SIEGHART.png` (89x90). Ela e o mesmo estilo dos outros 21
icones (cabeca chibi, fundo transparente), mas:

- tem uma **moldura** clara em volta (o desenho fica num painel cinza);
- o **cabelo e preto** — no icone antigo ele ficava "apagado"/escuro.

**Novo script:** **`assets/perfil/gerar_icone_chibi.py`**

```
python assets\perfil\gerar_icone_chibi.py assets\perfil\SIEGHART.png sieghart
```

O que ele faz:

1. **tira a moldura** — varre a linha do meio de cada lado de fora para
   dentro e para na ultima linha clara antes de uma falha grande
   (a moldura e formada por varias linhas brancas separadas por falhas
   escuras); o resultado foi `esq=7 dir=5 topo=3 base=4`;
2. **separa o personagem do painel** com o **GrabCut** (OpenCV) — o
   `rembg` **nao funciona** nesse tipo de arte: ele apaga o cabelo preto e
   deixa so o colete (testado com `u2net` e `isnet-anime`);
3. **abre a mascara** (morfologia) para tirar a faixa fina do painel que
   sobrava embaixo;
4. recorta o personagem e encaixa em **128x128** (116x116, com margem);
5. **clareia** com `gamma 0.62` (levanta as sombras sem deixar o cabelo
   cinza) + contraste 1.06 + `UnsharpMask`.

**Resultado:** luminancia media **108** (os outros 21 ficam entre 94 e
139), fundo transparente, cabeca em foco — igual aos demais.

**Dependencia nova (so para gerar o icone):** `opencv-python-headless`
(instalado no Python do sistema; o app em si nao usa).

> ⚠ **No Windows `REY.png` e `rey.png` sao o mesmo arquivo.** O destino
> tem que ser sempre o nome completo (`rey_icon.png`).

### 5.28 🎨 Os 25 icones no mesmo estilo (chibi) (16/11)

O usuario colocou as artes **chibi com moldura** dos outros 3 na pasta:

| Arquivo | Tamanho | Moldura detectada | Icone gerado |
|---|---|---|---|
| `SIEGHART.png` | 89x90 | esq=7 dir=5 topo=3 base=4 | 116x116 |
| `LUPUS.png` | 90x91 | esq=7 dir=6 topo=5 base=7 | 116x109 |
| `REY.png` | 88x87 | (nao detectada — o GrabCut tirou a moldura) | 109x116 |
| `RYAN.png` | 86x88 | esq=5 dir=4 topo=0 base=1 | 111x116 |

Comandos (o `gerar_icone_chibi.py` **nao** precisa do venv — so do
`opencv-python-headless`):

```
python assets\perfil\gerar_icone_chibi.py assets\perfil\SIEGHART.png sieghart
python assets\perfil\gerar_icone_chibi.py assets\perfil\LUPUS.png lupus
python assets\perfil\gerar_icone_chibi.py assets\perfil\REY.png rey
python assets\perfil\gerar_icone_chibi.py assets\perfil\RYAN.png ryan
```

**Agora os 25 icones estao no mesmo estilo** (cabeca chibi, fundo
transparente, 128x128). Luminancia media dos 25: entre **67 e 162**
(os 4 novos: sieghart 108, ryan 136, lupus 154, rey 162).

> ⚠ Os 4 PNGs de origem (`SIEGHART.png`, `LUPUS.png`, `REY.png`,
> `RYAN.png`) ficaram na pasta — sao as fontes para regerar os icones.
> O `.spec` leva `assets/perfil/*.png` para o `.exe`, entao eles vao junto
> (uns 60 KB, sem problema).

### 5.29 💝 Botao de doacao + painel lateral (16/11)

O projeto ganhou um **botao "Apoiar"** que abre um **painel lateral
(drawer)** de doacao, sem fechar o app.

**O botao** (tema + app):

| Onde | Antes | Agora |
|---|---|---|
| Cabecalho, 1a linha | `English` (fora de uso) | **`❤ Apoiar`** |
| Fundo | vidro escuro | **gradiente roxo** (assado no cenario) |
| Clique | "Idioma: em breve." | **abre o painel de doacao** |

- o icone do coracao e **desenhado com PIL** (`_desenhar_coracao` no
  `tema_visual.py`) — o emoji ❤ sairia vermelho demais no botao roxo;
- o gradiente do botao e assado no **cenario** (`render_paineis`), como os
  outros paineis de vidro;
- o botao **alterna**: clicar de novo fecha o painel.

**O painel** (`janela_doacao.py`, classe `PainelDoacao`):

- `CTkToplevel` **sem barra de titulo** (`overrideredirect`) posicionado
  sobre a borda direita da tela principal;
- **desliza** da direita para dentro (animacao de ~20 passos em `after`);
- conteudo: emblema, texto, 3 valores sugeridos (R$ 5 / R$ 20 / R$ 50),
  **QR Code do Pix**, a chave "copia e cola" (texto que quebra),
  "Copiar chave Pix" e a lista do que o apoio cobre;
- se existir `assets/doacao/link.txt`, aparece tambem o botao
  "Abrir pagina de apoio" (abre no navegador).

**Os arquivos da doacao** (`assets/doacao/`, vao no build):

| Arquivo | Para que serve |
|---|---|
| `pix.txt` | **a chave Pix** (e-mail/telefone) — o unico arquivo que o usuario edita |
| `nome.txt` | o nome que aparece no recibo |
| `pix_payload.txt` | o payload "copia e cola" (gerado) |
| `qr_pix.png` | o QR Code (gerado) |
| `link.txt` | link opcional de uma pagina de apoio (vazio = nao aparece) |
| `gerar_qr.py` | **regera** o payload e o QR depois de trocar a chave |

```bash
# trocar a chave e regerar o QR:
#   1. edite assets/doacao/pix.txt
#   2. python assets\doacao\gerar_qr.py     (precisa de `qrcode`)
```

> ⚠ **A chave atual e um telefone com DDI:**
> **`+5519981466471`** (trocada pelo usuario). O `pix_payload.txt` e o
> `qr_pix.png` foram regerados e conferidos: **CRC16 valido** e o QR
> **decodifica** para o payload.
>
> O build leva **so os 4 arquivos** que o app usa
> (`pix.txt`, `nome.txt`, `pix_payload.txt`, `qr_pix.png`) — o
> `gerar_qr.py` e o `__pycache__` ficam de fora do `.exe`.
>
> ⚠ **O `gerar_qr.py` nao grava mais pela metade:** ele confere as
> bibliotecas (`qrcode`, `Pillow`) **antes** de escrever qualquer
> arquivo e so grava o payload e o QR depois de gerar os dois em
> memoria. Antes, se faltasse a biblioteca, ele escrevia o payload e
> morria — o app ficava com a chave nova no "copia e cola" e o **QR
> velho** na tela.
>
> O `qrcode` esta instalado **nos dois** Pythons (o do sistema e o venv
> `assets/perfil/.venv`).
>
> **O `teste_doacao.py` agora confere a sincronia:** o payload tem que
> ser o que o `monta_payload` gera a partir da chave atual e o QR Code
> tem que **decodificar** para esse payload. Se ficarem velhos, o teste
> falha e diz o que rodar.

> ✅ **A chave Pix ja foi trocada** pelo usuario (chave aleatoria
> `7554f72b-3ee1-4293-ac52-fad62da7f93e`) e o QR/payload foram regerados
> com `python assets\doacao\gerar_qr.py`. O payload em
> `assets/doacao/pix_payload.txt` foi conferido: **CRC16 valido** e o QR
> **decodifica** para o mesmo payload.
>
> Para trocar a chave de novo: edite `assets/doacao/pix.txt` e rode o
> script (o `link.txt` opcional ainda nao existe).

**Teste:** `teste_doacao.py` (botao no lugar do "English", arquivos da
doacao, painel abrindo, copia da chave e o botao alternando).

### 5.30 🗂️ Icone do app em todas as janelas (16/11)

O icone do aplicativo vem do arquivo **`assets/app.ico`** (feito a mao
pelo usuario — o grimorio dourado com o emblema de rubi). Ele e:

- o **icone do executavel** (Explorer, barra de tarefas, atalhos);
- o **icone de todas as janelas** do app.

**O `.ico`** tem 6 quadros: 16, 32, 48, 64, 128 e 256 px.

```python
# no "Controle Grand Chase.spec"
EXE(name='Caminho da Maestria',
    icon=os.path.join(SPECPATH, 'assets', 'app.ico'))
```

**O `assets/make_icon.py`** continua no projeto, mas agora e so um
**gerador opcional** (o `.ico` atual nao precisa dele): a fonte pode ser
qualquer PNG.

```bash
python assets\make_icon.py assets\login.png   # gera o app.ico de novo
```

**Em todas as janelas:** o icone deixou de estar duplicado em cada
arquivo e virou um helper so, no `caminhos.py`:

```python
def aplicar_icone(widget):
    """Coloca o icone do app (assets/app.ico) na janela."""
    try:
        caminho = icone_app()
        if os.path.exists(caminho):
            widget.iconbitmap(caminho)
    except Exception:
        pass
```

Chamadas (todas logo depois do `self.title(...)`):

| Janela | Arquivo |
|---|---|
| Login | `login.py` |
| Tela principal | `app_grandchase.py` |
| Minha conta | `janela_perfil.py` |
| Edicao do personagem | `janela_personagem.py` |
| Nivel do Chaser | `janela_nivel.py` |
| Missao Rapida | `janela_missao_rapida.py` |
| Painel de doacao | `janela_doacao.py` |

(o painel de doacao e `overrideredirect` — sem barra de titulo — mas
o icone continua sendo definido e o **emblema do painel** tambem passou
a ser o `app.ico`.)

**Teste:** `teste_icone.py` confere que o `.ico` e um ICO valido com os 6
quadros, que o `.spec` usa o `.ico` e que **cada janela tem icone**
(via `WM_GETICON`).

### 5.31 📳 O app gera o QR Code sozinho (16/11)

**O problema:** trocar a chave Pix exigia rodar o `gerar_qr.py` E
rebuildar o `.exe`. Quando o script nao rodava (ou rodava num Python
sem a biblioteca `qrcode`), o app ficava com a chave nova no "copia e
cola" e o **QR velho** na tela — e isso aconteceu 3 vezes.

**A solucao:** o app passa a ter a chave como **fonte da verdade** e
monta tudo em memoria, a cada abertura do painel:

| Antes | Agora |
|---|---|
| `pix.txt` -> `gerar_qr.py` -> `pix_payload.txt` + `qr_pix.png` -> build | **`pix.txt` -> o app monta o payload e gera o QR** |

**Modulo novo: `pix_pagamento.py`** (na raiz do projeto)

```python
pix_pagamento.chave()        # a chave de assets/doacao/pix.txt
pix_pagamento.nome()         # o nome do recibo (nome.txt)
pix_pagamento.payload()       # o payload "copia e cola" (montado na hora)
pix_pagamento.qr_imagem(264)  # a imagem do QR Code (PIL)
```

- o payload e montado pelo app (o `monta_payload` e o mesmo do script);
- o QR e gerado com a biblioteca `qrcode` (que agora vai no build do
  PyInstaller);
- o `assets/doacao/qr_pix.png` virou **reserva**: so e usado se a
  biblioteca nao estiver disponivel.

**Agora para trocar a chave:**

1. edite `assets/doacao/pix.txt`;
2. **reinicie o app** (ou o `.exe`).

Nao precisa rodar script nem rebuildar. (O `gerar_qr.py` continua
existindo para gerar o PNG e conferir o CRC, e usa o mesmo modulo.)

**O `teste_doacao.py`** agora confere as 3 coisas:
- o `pix_payload.txt` e o `qr_pix.png` estao em dia com a chave;
- o **QR gerado pelo app** decodifica para o payload da chave atual.

> ⚠ **O payload e o QR sao os FIXOS do usuario** (ele pegou o
> "copia e cola" no app do banco). O app **nao gera mais nada**:
>
> - o **payload** vem de `assets/doacao/pix_payload.txt` (usado como
>   esta, sem normalizar a chave — o CRC do codigo do banco foi
>   conferido: `BCC8` = CRC calculado);
> - o **QR Code** e a imagem **`assets/qrcode-pix.png`** (360x360), que
>   decodifica exatamente para esse payload.
>
> O `pix_pagamento.py` ficou assim:
>
> | Funcao | O que faz |
> |---|---|
> | `payload()` | devolve o `pix_payload.txt`; se nao existir, monta da chave |
> | `imagem_pronta(lado)` | a `assets/qrcode-pix.png` (a imagem do usuario) |
> | `qr_imagem(lado)` | a imagem pronta; se nao existir, gera com `qrcode` |
> | `chave()` / `normalizar_chave()` | a chave do `pix.txt` (so como reserva) |
>
> O `gerar_qr.py` **nao sobrescreve** o payload fixo (ele avisa e
> precisa de `--forcar`).
>
> **O QR so e legivel no tamanho nativo (360 px).** A imagem do usuario
> tem o modulo em ~8,6 px (nao inteiro) e qualquer reducao embaralha os
> modulos: em 200 px o QR **nao decodifica** (testado: so passa a partir
> de ~300 px, e em 360 px decodifica certinho). Por isso:
>
> - o painel ficou com **640 px de largura** e **duas colunas** (o QR de
>   360 px a esquerda, a chave e os botoes a direita);
> - `imagem_pronta()` **nao reduz** a imagem abaixo do tamanho original;
> - o `teste_doacao_exe.py` recorta **so o QR** da tela do `.exe` (a tela
>   tem outros QRs por perto e o detector se confunde).
>
> **Os cartoes de valor** (`janela_doacao.py`, `VALORES`) foram aumentados
> (190 px de largura, fonte 22/13) e os textos trocados pelo usuario:
>
> | Valor | Texto |
> |---|---|
> | R$ 5 | **O gelo** |
> | R$ 20 | **Humilde** |
> | R$ 50 | **Ganha VIP <3** |
>
> (a largura do cartao e imposta pelos **rotulos** (`width=170`) — o
> `width` do `CTkFrame` sozinho nao segura a largura, o cartao encolhe
> e o texto fica cortado).
>
> **A chave e NORMALIZADA pelo app** (`pix_pagamento.normalizar_chave`):
> o usuario pode escrever o telefone como quiser no `pix.txt`
> (`+55 (19) 98146-6471`, com espaco, parenteses e traco) que o app
> monta o payload com o formato canonico (`+5519981466471`) — o Pix
> **rejeita** a chave com mascara.
>
> - e-mail: so sem espacos;
> - chave aleatoria (EVP): como esta;
> - telefone: so os digitos, com o `+` do DDI na frente.

### 5.32 🔐 A conta de teste trocada (17/11)

Para **nao usar mais a conta pessoal** nos testes, a conta de teste agora e:

```
teste@teste.com  (senha: GC_TESTE_SENHA / .env.teste)
```

**O que foi trocado:** todos os `teste_*.py` (e o `limpar_duplicados.py`)
passam a usar a conta nova no lugar da conta pessoal antiga. O
`teste_integracao.py` antes **exigia** e-mail e senha na linha de
comando; agora ele usa a conta de teste por padrao (e so aceita os
argumentos se voce quiser outra conta).

> ⚠ **Sobrou um usuario duplicado no Supabase:** o `sign_up` da conta
> nova criou um segundo usuario **sem confirmacao de e-mail**
> (`2de35412-51f6-4073-b198-53db1f07f38e`). Ele **nao consegue entrar**
> (sem confirmacao), mas aparece na lista de usuarios do painel do
> Supabase. Para apagar: painel > Authentication > Users > remover esse
> id (ou a API `admin`, que precisa da `service_role key`).

### 5.33 📦 O instalador do programa (17/11)

**Pendencia #8 (a ultima) resolvida.** O instalador esta em:

```
instalador\Caminho da Maestria - Instalador.zip      (218 MB)
instalador\Caminho da Maestria - Instalador\         (a pasta)
instalador\RELATORIO-SEGURANCA.txt                   (a auditoria)
```

**Como o usuario instala**

1. descompacta o zip **inteiro**;
2. clica em **`Instalar.cmd`**;
3. o programa e instalado e abre sozinho.

| Item | Detalhe |
|---|---|
| Instala em | `%LOCALAPPDATA%\Caminho da Maestria` (sem pedir admin) |
| Dependencias | **todas embutidas** (Python + libs na pasta `_internal`) — nao precisa instalar nada |
| Atalhos | area de trabalho + Menu Iniciar (com o icone do programa) |
| Desinstalar | Menu Iniciar > Caminho da Maestria > Desinstalar (ou o `Desinstalar.cmd`) |

**Os scripts do instalador**

| Arquivo | Funcao |
|---|---|
| `Instalar.cmd` | copia, cria atalhos, gera o desinstalador e abre o app |
| `atalhos.vbs` | cria os 3 atalhos (WshShortcut, com o icone do `.exe`) |
| `Desinstalar.cmd` | remove a pasta e os atalhos |
| `LEIA-ME.txt` | as instrucoes para o usuario |

**Como gerar de novo**

```bash
python scripts/gerar_instalador.py      # monta a pasta e compacta o .zip
python scripts/auditoria_instalador.py  # revisa o pacote antes de distribuir
```

**Seguranca (o ponto mais importante)**

O `gerar_instalador.py` **revisa o bundle ANTES de empacotar** e
**ABORTA** se encontrar: `service_role key`, `sb_secret_`, JWT de
servico, chave privada, senha ou e-mail pessoal. O
`auditoria_instalador.py` faz a mesma revisao **dentro do .zip** e
escreve o `RELATORIO-SEGURANCA.txt`.

Resultado da auditoria: **APROVADO** (3778 arquivos, 538 MB
descompactado). A unica chave que fica no programa e a **publishable
key** do Supabase (`sb_publishable_...`), que e publica por design.

> ℹ️ O `certifi/cacert.pem` (pacote publico de certificados
> raiz) e ignorado pela auditoria: ele dispara o padrao de "JWT" por
> acaso dentro do texto base64 dos certificados. Nao e chave nenhuma.

**Teste:** `teste_instalador.py` faz o ciclo completo — extrai o zip,
instala, confere os atalhos, **abre o programa instalado** e desinstala.

> ⚠ **O zip tem 218 MB** porque o `pandas`/`numpy` arrastam a MKL
> (~ 309 MB de DLLs). O app usa `pandas` na importacao/exportacao de
> Excel e `numpy` no fundo da tela de login; reduzir isso exigiria
> reescrever essas partes.

### 5.34 🗓️ Zerar as missoes semanais de TODAS as contas (17/11)

Pedido: **toda quarta-feira as 03h (Brasilia)** zerar as missoes
semanais de **todas** as contas do Supabase, sozinho.

**O que foi feito**

| Arquivo | Funcao |
|---|---|
| `zerar_semanais_semanal.py` | o script que zera (as 7 colunas booleanas da tabela `user_semanais`) |
| `agendar_zerar_semanal.cmd` | cria/apaga a tarefa no Agendador do Windows |
| `LEIA-ME-zerar-semanal.txt` | as instrucoes (tem a chave, como agendar, como testar) |

**A tabela `user_semanais`** (as colunas que o script zera):

```
fornalha_infernal | altar_da_runha | torre_das_ilusoes_semanal |
void_123 | void_4 | caminho_abissal | terra_do_julgamento
```

(o script descobre sozinha quais existem no banco)

**A tarefa agendada (CRIADA E CONFERIDA em 17/11)**

```
jobid    : 4
jobname  : zerar-missoes-semanais
schedule : 0 06 * * 3              (06h UTC = 03h de Brasilia, toda quarta)
command  : select public.zerar_semanais();
active   : true
```

**A tarefa agendada (JA CRIADA)**

```
Nome : Caminho da Maestria - Zerar missoes semanais
Quando: toda quarta-feira as 03:00 (a maquina esta em UTC-3/Brasilia)
Roda  : C:\Users\guilh\anaconda3\python.exe zerar_semanais_semanal.py
```

Foi testada de ponta a ponta: `schtasks /Run` executa o script (ele
gravou o log) e o logico de zerar foi validado com a sessao da conta de
teste (175 marcacoes ativas -> 0).

> **Falta a `service_role key`.** O script precisa dela para mexer nas
> linhas dos OUTROS usuarios (a anon nao passa na RLS). Sem a chave a
> tarefa roda e registra "ERRO: a service_role key nao foi encontrada"
> no log.
>
> A chave e procurada em 3 lugares (nenhum e o codigo):
> 1. variavel de ambiente `SUPABASE_SERVICE_ROLE_KEY`
> 2. `%LOCALAPPDATA%\Caminho da Maestria\service_role.txt`
> 3. `service_role.txt` ao lado do script
>
> **A chave NUNCA vai no app nem no instalador** (a auditoria do
> instalador aborta se encontrar `service_role`/`sb_secret_`).

### 5.35 🗓️ O pg_cron que zera as semanais de todas as contas (17/11)

**Versao final (a recomendada): roda no SERVIDOR.** O usuario pediu um
script para colar no **SQL Editor do Supabase** usando o **pg_cron**.

**Arquivos:**
- `sql/zerar_semanais_pg_cron.sql` — **cole e rode no SQL Editor**
  (Só cria: nada de query de conferencia, para nunca dar erro e
  rollback)
- `sql/zerar_semanais_verificar.sql` — as queries de conferencia
  (opcional, so leitura)

O que ele cria:

| Objeto | O que e |
|---|---|
| `public.zerar_semanais()` | funcao `security definer` que marca as 7 colunas booleanas de `public.user_semanais` como `false` para **TODAS** as contas (ela ve sozinha quais colunas existem) |
| `zerar-missoes-semanais` | tarefa do **pg_cron**: `0 3 * * 3` (quarta 03h) |

**Sobre o fuso:** o Brasil nao usa horario de verao desde 2019, entao
03h e sempre 03h (UTC-3). O script detecta se a instalacao do pg_cron
aceita **fuso por tarefa** (coluna `cron.job.timezone`, pg_cron 1.4+):
- o script le `current_setting('TimeZone')` do servidor e calcula a
  hora (e o dia) da 03h de Brasilia nesse fuso — no Supabase (UTC)
  da `0 06 * * 3`.

**Detalhe do `cron.unschedule`:** ele lanca erro se a tarefa nao existir,
entao o bloco `DO` protege com `exception when others then null` (para o
script poder ser rodado quantas vezes quiser, sem duplicar).

**Seguranca:** `security definer` + `set search_path = public, pg_temp` +
`revoke all ... from public` (so o `postgres` executa). **Nao precisa
da `service_role key`** — por isso nao ha nenhum segredo novo no
projeto.

**Validacao (tudo certo em 17/11):**
- a sintaxe dos 10 comandos (5 + 5) foi checada com o parser real do
  Postgres (`pglast`): `SINTAXE OK`;
- a funcao foi testada **de verdade**, chamando por RPC:
  `teste_zerar_semanais.py` marca as 7 colunas como `true` em todas as
  linhas, chama `public.zerar_semanais()` e confere que tudo voltou
  para `false` — e que a segunda chamada devolve `0` (idempotente).
  Resultado: `LIMPEZA SEMANAL OK (marcou -> zerou -> idempotente)`.

  > Esse teste foi o que pegou os bugs: ele chama a funcao do banco de
  > verdade (via `POST /rest/v1/rpc/zerar_semanais`).

**Bugs corrigidos (achados chamando a funcao por RPC):**

1. `partes := partes || 'updated_at = now()'` — com um literal solto o
   Postgres resolve o `||` como **concatenacao de arrays** e tenta
   converter o texto para `text[]` -> `malformed array literal`.
   Agora usa `array_append(...)`.
2. O `update ... set ...` **sem WHERE** — o Postgres exige o WHERE
   (`UPDATE requires a WHERE clause`, codigo 21000). Agora o WHERE e
   montado: `where (col1 or col2 or ...)`, ou seja, so as linhas que
   **tinham marcacao** sao tocadas (e o numero devolvido pela funcao e
   quantas linhas tinham marcacao).

**Agendamento adaptativo:** o `cron.schedule(nome, schedule, command)`
so existe no pg_cron novo; o antigo so tem `cron.schedule(schedule,
command)`. O bloco `DO` tenta o novo e, se falhar, usa o antigo e
renomeia a tarefa (`update cron.job set jobname = ...`).

**Atencao (bug corrigido):** a primeira versao tinha no fim uma query
`select ... timezone from cron.job` — o `cron.job.timezone` so existe
no pg_cron **1.4+**, e em versoes antigas ela dava
`column "timezone" does not exist`. Como o SQL Editor roda o arquivo
numa transacao so, esse erro no fim **desfazia** a criacao da funcao e
do agendamento. Por isso os arquivos foram separados: o de criacao nao
tem nenhuma query que possa falhar, e o de conferencia e opcional.

O horario agora e **calculado** pelo proprio script (fuso do servidor +
dia da semana):

**A via do Windows (5.34) continua no projeto** como alternativa
(`zerar_semanais_semanal.py` + `agendar_zerar_semanal.cmd`), mas a
tarefa agendada do Windows foi **removida** (a do servidor e melhor:
nao depende da maquina ligada nem de chave).

### 5.36 💍 O nome (e a cor) do Piercing (17/11)

O nome certo do acessorio e **"Piercing do Outro Mundo do Caos"** (estava
"Piercing da Dimensao do Caos").

**Onde cada coisa vem (importante):**

| Coisa | Onde esta | Precisa refazer o .exe? |
|---|---|---|
| o **nome** exibido | no **banco** (`user_acessorios_titulo.piercing`) | **nao** |
| a **cor** do acessorio | no **codigo** (`card_personagem.py`, `REGRAS_ACESSORIOS`) | so se a regra mudar |
| a **lista** do dropdown | no **codigo** (`opcoes.py`) | so se trocar as opcoes |

A cor sai de uma regra que casa por **trecho do nome** (sem acento,
minusculo). Com o nome novo, a regra `"outro mundo do caos"` passa a
casar e o Piercing fica **vermelho** (`#fb7185`) — igual ao
"Brinco do Outro Mundo do Caos" (que e o mesmo item do jogo). Antes
("Dimensao do Caos") **nenhuma** regra casava e ele ficava sem cor.

```
piercing  | Piercing da Dimensao do Caos    -> (sem cor)
piercing  | Piercing do Outro Mundo do Caos  -> #fb7185 (vermelho)
brinco    | Brinco do Outro Mundo do Caos    -> #fb7185 (vermelho)
```

**O que foi feito:**
- a linha da **conta de teste** foi trocada pela API (a RLS so deixa
  mexer nas linhas do usuario logado);
- para as **outras contas**, o script `sql/corrigir_nome_piercing.sql`
  (rode no SQL Editor do Supabase).

**A lista do dropdown tambem foi corrigida** (`opcoes.py`): o nome
antigo saiu, o novo entrou e o typo `"PIercing da Dimensao Raro"` virou
`"Piercing da Dimensao Raro"`. Como isso e **codigo**, o `.exe` foi
refeito (e o `git push` leva a correcao para os PCs da guilda).

```
piercing | Piercing do Outro Mundo do Caos | Piercing da Dimensao Lendario |
          Piercing da Dimensao Epico | Piercing da Dimensao Raro |
          Piercing do Piu Piu
```

### 5.37 🔗 O projeto no GitHub (17/11)

```
https://github.com/guitador123/caminho-da-maestria
```

**O que foi feito**
- Git instalado (winget) + GitHub CLI (`gh`), autorizado na conta
  `guitador123`;
- repositorio criado e **publico** (para os PCs da guilda clonarem sem
  credencial), com 2 commits e **172 arquivos** (27,5 MB);
- `.gitignore` que **nao deixa subir**: `.venv`, `dist/`, `build/`,
  `instalador/` (755 MB), `__pycache__`, `_capturas/`, `login_prefs.json`,
  `service_role.txt`, `*.env`, `*.key`...
- `.gitattributes` (LF no repo, CRLF nos `.bat`/`.cmd`);
- `requirements.txt` (as dependencias), `README.md` (instrucoes),
  **`iniciar.bat`** (prepara o PC) e **`atualizar.bat`** (atualiza e abre).

**Como atualizar o PC da guilda (sem instalador)**

1. uma vez so, no PC da guilda:
   ```bat
   git clone https://github.com/guitador123/caminho-da-maestria.git
   cd caminho-da-maestria
   ```
   e clique em **`iniciar.bat`** (cria o `.venv` e abre o app);
2. para atualizar: **dois cliques no `atualizar.bat`** (ele faz o
   `git pull`, atualiza as dependencias e abre o app).

No PC do dono, para publicar uma versao nova:
```bash
git add . && git commit -m "o que mudou" && git push
```

**Testado:** `git clone` do repositorio (sem credencial) + o app abrindo
a partir do clone — **CLONE OK**.

**Seguranca:** o commit foi auditado (nenhuma `service_role`, nenhum
`sb_secret_`, nenhum JWT, nenhuma chave privada). A unica chave no
codigo e a **publishable key** do Supabase (publica por design). O
e-mail/senha da conta pessoal antiga foram **removidos** do codigo e do
HANDOFF (nos scripts de auditoria eles eram procurados — e isso os
exponha).

> ℹ️ Se quiser o repo **privado**: `gh repo edit
> guitador123/caminho-da-maestria --visibility=private` (os PCs da
> guilda passam a precisar de um token para clonar).

### 5.38 🔄 Atualizacao automatica (17/11)

**Pedido:** "o .exe, sempre que aberto, verifique se existe algum commit
novo e ja atualize automaticamente".

**Modulo novo: `atualizacao.py`** (chamado no `login.abrir_aplicativo()`,
antes da tela de login)

```
REPOSITORIO = "guitador123/caminho-da-maestria"
```

O que ele faz:

1. compara a versao local com a do GitHub;
2. se forem diferentes, atualiza e **reinicia** o programa.

**Duas situacoes (o app se adapta):**

| Onde o app esta | O que ele faz |
|---|---|
| clone do git (tem `.git`) | `git pull --ff-only` + `pip install -r requirements.txt` e reinicia |
| instalado do `.exe`/instalador | baixa a ultima **Release**, troca os arquivos (por um `.cmd` auxiliar, porque o Windows nao deixa trocar um `.exe` em uso) e reinicia |

**A versao local:**
- num clone: e o `git rev-parse HEAD` (o que esta rodando);
- no `.exe`: o commit gravado em **`assets/versao.txt`** na hora do build
  (gerado pelo `gravar_versao.py`, que entra no build pelo `.spec` e e
  **ignorado pelo git**, porque e artefato de build).

**O `git` e achado mesmo fora do PATH** (`caminho_git()` tenta o PATH e
os caminhos padrao de instalacao).

**Publicar uma versao (para o `.exe` se atualizar):**
```bash
python scripts/publicar_release.py
```
(grava a versao, empacota, **audita o pacote** e cria a Release no GitHub)

**Testado:**
- clone atrasado (2 commits) -> detectou, fez `git pull` e ficou igual ao
  remoto: `ATUALIZACAO AUTOMATICA OK`;
- o `.exe` instalado -> detecta a Release nova, baixa, troca e reinicia.

**Nada trava o programa:** rede/GitHub fora do ar, chave invalida ou
qualquer erro -> o app abre normalmente (tudo em `try/except`).

**Detalhes que mudaram durante a implementacao (importantes!):**

| Assunto | Decisao |
|---|---|
| **consulta do GitHub** | usa os **feeds Atom** (`/commits/main.atom` e `/releases.atom`), **nao a API**: a API tem limite de 60/hora por IP e varios PCs da guilda no mesmo IP estourariam |
| **download da release** | URL previsivel: `/releases/latest/download/Caminho-da-Maestria.zip` (o asset **nao pode ter espaco** — o GitHub troca por ponto) |
| **versao da release** | a entrada do feed com o `updated` mais novo (o feed vem em ordem de criacao) |
| **a troca dos arquivos** | o Windows nao deixa trocar um `.exe` em uso: quem troca (e **reabre** o programa) e um `.cmd` auxiliar, **depois** que o app fecha |
| **o app nao se relanca** | se ele abrisse de novo antes da troca, os arquivos ficariam em uso e a copia falharia |
| **a pasta temporaria** | so e apagada no **erro** (no sucesso, quem apaga e o auxiliar, depois de copiar) |
| **o git** | e achado mesmo fora do PATH (`caminho_git()`) |
| **log** | `%LOCALAPPDATA%\\Caminho da Maestria\\log_atualizacao.log` |

**Testado de verdade:**
- clone atrasado (2 commits) -> detectou e fez `git pull`: `ATUALIZACAO
  AUTOMATICA OK`;
- `.exe` instalado (sem `.git`), com a versao falsificada -> baixou a
  release (217 MB), trocou os arquivos e **abriu de novo com a versao
  nova**: `AUTO-UPDATE DO EXE OK (baixou, trocou e reiniciou)`.

### 5.39 📦 O instalador no GitHub (17/11)

O instalador (com a versao mais nova) foi publicado como **asset da
Release** do GitHub:

```
https://github.com/guitador123/caminho-da-maestria/releases/latest/download/Caminho-da-Maestria-Instalador.zip
```

A release tem os dois arquivos:

| Arquivo | Para que serve |
|---|---|
| `Caminho-da-Maestria-Instalador.zip` (218 MB) | o **instalador** (instala sem Python) |
| `Caminho-da-Maestria.zip` (217 MB) | o programa pronto (e o que o `.exe` baixa para se atualizar) |

**O nome do asset nao pode ter espaco** (o GitHub troca por ponto) — por
isso `gerar_instalador.py` e `publicar_release.py` usam
`Caminho-da-Maestria-Instalador.zip` e `Caminho-da-Maestria.zip`.

**O `publicar_release.py` agora sobe os dois** (o programa e o
instalador), entao da proxima vez e so rodar ele.

**Testado de ponta a ponta:** baixou o instalador do GitHub (228 MB em
14s), descompactou, instalou (atalhos + desinstalador), **abriu o
programa** e desinstalou: `INSTALADOR DO GITHUB OK`.

### 5.40 🐞 O filtro de dungeon nao filtrava (18/11)

**Sintoma:** marcar "Torre das Ilusoes" (e "Caminho Abissal") no
filtro "Nao fez estas masmorras semanais" nao escondia ninguem — a
lista continuava com os 25 cards.

**A causa:** as chaves do filtro e as chaves dos dados estavam
escritas de formas diferentes:

| Onde | Antes | Agora |
|---|---|---|
| filtro (`FILTRO_MAZMORRAS`) | `caminho_abissal`, `torre_das_ilusoes` | `caminhoabissal`, `torredasilusoes` |
| dados (`card_personagem.DUNGEONS`) | `caminhoabissal`, `torredasilusoes` | (os mesmos) |

As chaves dos dados sao **normalizadas** (sem acento, sem espaco e sem
underscore). O filtro usava o nome com underscore -> a busca
(`mazmorras.get(chave)`) nunca achava -> a dungeon era tratada como
"sempre nao feita" -> **todo mundo passava no filtro**.

Por isso so as opcoes com o nome "errado" quebravam: `Vazio 1, 2 e 3`
(`void123`) e `Vazio 4` (`void4`) funcionavam; **Torre das Ilusoes** e
**Caminho Abissal** nao.

**A correcao**
1. as chaves de `FILTRO_MAZMORRAS` agora sao as mesmas dos dados;
2. a comparacao no `_filtrar_personagens` tambem ficou tolerante
   (compara as chaves normalizadas), para nao acontecer de novo;
3. o `opcoes.py` ganhou `mesmo_dado()` e `chave_semanal()` (a Torre
   Semanal tem dois nomes: `torre_das_ilusoes` no app e
   `torre_das_ilusoes_semanal` no banco) — com isso a coluna dela e
   achada em qualquer contexto (filtro, card, Missao Rapida e tela de
   edicao).

> ℹ️ A Torre **mensal** (a do "30 / 30", na aba Geral) e outra
> coluna e continua como antes — o alias so vale para a semanal.

**Teste:** `teste_filtro_dungeons.py` marca cada uma das 4 dungeons no
banco (na conta de teste), recarrega o app e confere que o card conta a
dungeon como feita e que o **filtro esconde justamente aquele
personagem** (24 de 25). Resultado: `FILTROS DE DUNGEON OK`.

## 6. Pendências (17/11/2026)
> As pendências **1, 2 e 3 já foram implementadas** (ver 5.6, 5.7 e 5.9).
> As decisões já fechadas estão em 6.1; as tarefas em 6.2.

### 6.1 Decisões fechadas (não são mais pendências)

| Item | Decisão do usuário |
|---|---|
| **Tabela de personagens** | Não existe mais: a lista de personagens será **somente os cards** — *já está feito* (25 cards com retrato, rolagem e tela de edição). O `CTkTabview` da tabela segue desligado (`MOSTRAR_TABELA = False`) e pode ser removido do código quando sobrar tempo. |
| **Idioma** | **Somente Português.** O botão "English" sai do cabeçalho; inglês só vira feature no futuro, se um dia. |
| **"Instalar aplicativo"** | Botão inútil → **descartar** (sai do cabeçalho). |

### 6.2 Tarefas pendentes

| # | Tarefa | Prioridade | Notas / como está hoje |
|---|---|---|---|
| 1 | ~~**Salvar no banco em segundo plano**~~ | ✅ **FEITO (14/11)** | Resolvido: envio em thread de rede + polling na thread da UI + upsert em lote. A UI volta a responder em **0,09s** (antes congelava por ~20s). Ver 5.6. |
| 2 | ~~**Cards atualizando em tempo real**~~ | ✅ **FEITO (14/11)** | A tela de edição propaga cada alteração (checkbox, campo, dropdown) para o dataframe e redesenha o card na hora. Ver 5.7. |
| 3 | ~~**Nível do Chaser no banco**~~ | ✅ **FEITO (14/11)** | Coluna `user_characters.nivel_chaser` (bigint) — **um valor por conta**, inteiro >= 0, editável pelo cartão "NÍVEL DO CHASER" (clique no campo). **SQL já rodado** e persistência validada. Ver 5.9. |
| 4 | ~~**Missão Rápida**~~ | ✅ **FEITO (14/11)** | O botão abre um **painel flutuante** (personagem + as 7 missoes, marcar várias de uma vez, salvar em 1 gravação) **e** liga o **modo rápido nos cards** (clicar no chip marca). Atalhos: `M`, `1`-`7`, `Ctrl+Enter`, `Esc`. Ver 5.16. |
| 5 | ~~**Card inteiro clicável**~~ | ✅ **FEITO (14/11)** | Clicar em **qualquer parte** do card abre a edição daquele personagem (a seta continua funcionando). Cada card tem uma tag exclusiva, então não há mistura. Ver 5.11. |
| 6 | ~~**Arrumar o enquadramento dos cards**~~ | ✅ **FEITO (14/11)** | Layout do card **metrico** (mede as fontes de verdade) + dupla escala de fonte corrigida. A grade se adapta: 3 colunas em 1152, 5 colunas em FullHD (escala 1.06) e 5 em QuadHD (escala 1.41), sempre com o card inteiro visivel. Ver 5.10. |
| 7 | ~~**Tela de perfil**~~ | ✅ **FEITO (15/11)** | O painel vago do hero virou o **perfil**: foto (do computador, guardada no Supabase), **Nick** + **Nivel do Chaser**, icone por nivel (`assets/chaser/cl1.png`, `cl100.png`...) com opacidade reduzida, e a janela "Minha conta" (trocar e-mail, senha e logout). Ver 5.22. |
| 8 | ~~**Gerar um instalador** do aplicativo~~ | ✅ **FEITO (17/11)** | Instalador compactado (218 MB) com todas as dependencias embutidas, atalhos, desinstalador e auditoria de segredos (APROVADO). Ver 5.33. |
| 9 | ~~**Ajustes finos de estética**~~ | ✅ **FEITO (15/11)** | Grade das 25 fotos cabe na tela (janela maior), circulo do filtro alinhado com o texto, paineis sem espaco vazio, "VOID" alinhado no card e build sem o `.venv` de 400 MB. Ver 5.24. |
| 10 | ~~**Limpar a coluna antiga**~~ | ✅ **FEITO (14/11)** | A coluna `fragmentos_facis` **já não existia** no banco (verificado). O que sobrou foi o **código morto** que falava nela (ignorar/descartar a coluna + fallback) — removido, e agora há um teste que vigia o schema. Ver 5.15. |

## 7. Como rodar e validar

### Rodar
```powershell
cd "C:\Users\guilh\Downloads\Controle GrandChase"

python app_grandchase.py      # abre o login -> tela principal
# ou direto o executavel:
.\dist\Controle Grand Chase\Controle Grand Chase.exe
```
O app sempre passa pelo **login** (Supabase Auth). Para testar sem conta nova,
use a conta de teste:
`teste@teste.com` (senha em `GC_TESTE_SENHA` ou no `.env.teste`, fora do git).

### Validar
```powershell
python -m py_compile app_grandchase.py card_personagem.py janela_personagem.py tema_visual.py tema_login.py login.py caminhos.py supabase_db.py opcoes.py
python tests/integracao/teste_fundo.py                              # imagem existe e abre no PIL
python tests/integracao/teste_integracao.py                         # dados/RLS
python tests/integracao/teste_acoes.py                              # acoes da tela (nao destrutivo)
python tests/integracao/teste_edicao.py                             # edicao grava nos dataframes
python tests/integracao/teste_campos_novos.py                       # colunas novas no Supabase
python tests/integracao/teste_edicao_supabase.py                    # edicao -> Supabase -> restaura
python tests/integracao/teste_salvamento_async.py                   # salvamento em 2o plano (nao trava)
python tests/integracao/teste_card_ao_vivo.py                      # edicao ao vivo -> card na hora
python tests/integracao/teste_visual_cores.py "c.png"               # regras de cor dos cards
python tests/integracao/teste_edicao_personagem.py                   # cada card abre a SUA edicao
python tests/integracao/teste_edicao_persistencia.py                 # salvar -> reabrir (Supabase)
python tests/integracao/teste_nivel_chaser.py                       # nivel do chaser (local)
python tests/integracao/teste_nivel_supabase.py                     # nivel do chaser (Supabase)
python tests/integracao/teste_layout_card.py                        # card em qualquer resolucao
python tests/integracao/teste_resolucoes.py                         # capturas FullHD/QuadHD
python tests/integracao/teste_login_exe_resolucao.py "e.png"      # .exe em tela cheia
python tests/integracao/teste_card_clicavel.py                     # card inteiro clicavel
python tests/integracao/teste_dropdowns_liberacao.py               # dropdowns despertar/liberacao
python tests/integracao/teste_perfil.py                           # perfil no hero + conta
python tests/integracao/teste_contador_despertar.py                # contador do despertar
python tests/integracao/teste_contador_libertacao.py               # contador da liberacao
python tests/integracao/teste_schema_limpo.py                      # schema do banco sem sobras
python tests/integracao/teste_missao_rapida.py                    # missao rapida (painel + cards)
python tests/integracao/teste_zerar_dungeons.py                  # zerar dungeons limpa o card
python tests/integracao/teste_filtros.py                        # busca + filtros + ordem
python tests/integracao/teste_login_memo.py                         # memorizar conta
python tests/integracao/teste_visual.py "C:\temp\captura.png"       # screenshot da tela local
python tests/integracao/teste_visual_login.py "C:\temp\captura.png" # screenshot logado
python tests/integracao/teste_visual_login2.py "C:\temp\captura.png" # screenshot da tela de login
python tests/integracao/teste_card.py "C:\temp\captura.png"         # screenshot de 1 card
python tests/integracao/teste_visual_cards.py "a.png" "b.png"        # hero + lista de cards (rolagem)
python tests/integracao/teste_visual_edicao.py "c.png"              # tela de edicao
python tests/integracao/teste_cards_retrato.py "d.png" 830          # cards com os retratos
python tests/integracao/teste_login_exe.py "e.png"                  # E2E do .exe (login -> tela)
pyinstaller "Controle Grand Chase.spec" --noconfirm                    # build
```
Resultados esperados: `PIL abriu OK`, `INTEGRACAO OK`, `ACOES OK`, `EDICAO OK`,
`CAMPOS NOVOS OK`, `EDICAO SUPABASE OK`, `MEMORIZAR CONTA OK`, `LOGIN E2E OK`.

⚠ Se houver um **jogo em tela cheia** no desktop, ele segura o foco e o
`teste_login_exe.py` dá falso negativo (a digitação não chega no app). Feche o
jogo antes de rodar o E2E.

- **16/11** — o **nome do app no Windows** passou a ser so **"Caminho
  da Maestria"** (janela + executavel) e o `.exe` ganhou o **emblema do
  Akkatsuki** como icone. Ver 5.25.
- **16/11** — a grade da tela de perfil passou a mostrar os **25
  icones** (colunas com largura fixa) e o **icone do Sieghart** foi
  refeito a partir do retrato original (estava apagado).
- **16/11** — o **`elesis_icon.png` foi gerado** a partir do
  `ELESIS.png` (com `rembg`, igual ao script do usuario) — agora os 25
  icones de perfil estao completos.
- **15/11** — **pendência #9 resolvida**: a grade das 25 fotos passou a caber
  na tela, o **circulo do filtro** ficou alinhado com o texto, os paineis
  perderam o espaco vazio do rodape e o build parou de levar o `.venv` de
  400 MB. Ver 5.24.
- **15/11** — **perfil v2**: a foto agora e **uma das 25** (pasta
  `assets/perfil/`, `<personagem>_icon.png`), entrou a **barra de EXP**
  (preenche com o nivel do chaser) e o icone do nivel foi para o **tamanho
  do badge** com mais opacidade. Tudo atualiza **em tempo real**. Ver 5.23.
- **15/11** — **perfil ajustado**: o texto virou **"Lv. <nivel> - <nick>"**,
  os **icones do usuario** (`assets/chaser/cl1.png` ... `cl900.png`) foram
  ligados (com cache, sao ~1 MB cada) e o **SQL do perfil** foi executado
  (nick e avatar ja persistem no Supabase). Ver 5.22.
- **15/11** — **pendência #7 resolvida**: o painel vago do hero virou o
  **perfil** (foto do computador guardada no Supabase, **Nick** + **Nivel do
  Chaser**, icone por nivel em `assets/chaser/` com opacidade reduzida) e a
  janela **"Minha conta"** (trocar e-mail, senha e logout). Ver 5.22.
- **15/11** — **a busca por texto e o filtro "Ordenar por Ataque Total" foram
  removidos**: a lista e **sempre** ordenada pelo **Ataque Total** (maior ->
  menor) e o filtro "Ordenar por Void" continua para trocar a ordenacao.
  Tambem: "Poder" -> **"Ataque Total"** na tela de edição e o
  congelamento do filtro caiu para **0,10s**. Ver 5.21.
- **15/11** — **filtros ajustados**: os botões passaram a responder ao
  clique (com **CHECK** no ativo), entrou o filtro **"Ordenar por Ataque
  Total"**, o congelamento caiu de **1,64s para 0,20s** (8,2x) e "Poder"
  virou **"Ataque Total"**. Ver 5.20.
- **14/11** — **feature nova: barra de FILTROS** acima dos cards (busca em
  tempo real, "não fez estas masmorras", "ordenar por Void", "progresso
  incompleto") e a lista sempre do mais forte para o mais fraco, se
  reordenando em tempo real. Ver 5.19.
- **14/11** — **pendência #9 resolvida**: o retrato do card passou a ter
  **área fixa** (o texto ficou igual em todos os cards), corrigido o bug da
  **reticência** que aparecia mesmo sem truncar, refinado o título/eyebrow e
  o **logo da login** (que era cortado na borda). Ver 5.18.
- **14/11** — **bug corrigido**: "Zerar dungeons semanais" zerava os
  cartões do hero mas **nao os cards de personagem** (as missoes seguiam
  marcadas). Agora ele tambem redesenha todos os cards. Ver 5.17.
- **14/11** — **pendência #4 resolvida**: o botão "Missão
  Rápida" agora abre um **painel flutuante** (personagem + 7 missões,
  marcar várias de uma vez, 1 gravação) e liga o **modo rápido
  nos cards** (clicar no chip da missão marca/desmarca). Atalhos `M`,
  `1`-`7`, `Ctrl+Enter`, `Esc`. Ver 5.16.
- **14/11** — **pendência #10 resolvida**: a coluna antiga
  `fragmentos_facis` **já não existia** no banco; o que restava era o
  código morto que falava nela — removido. Agora há um teste que
  vigia o schema (nenhuma coluna fora do que o app conhece). Ver 5.15.
- **14/11** — **contador "LIBERTAÇÃO COMPLETA" corrigido**: agora
  avalia as **3 condições** (estado VERDADEIRO + Núcleos 9/9 +
  Épicos+ 4/4) — antes contava só o estado. Ver 5.14.
- **14/11** — **contador "DESPERTAR COMPLETO" corrigido**: ele contava as
  **pecas de Void** (nada a ver com o despertar) e ainda nao atualizava
  **ao vivo** na tela de edicao. Agora conta quem tem **Nucleos 13/13 e
  Epicos+ 9/9** e sobe 1 na hora. Ver 5.13.
- **14/11** — **dropdowns do Despertar/Libertação**: no Despertar os
  Núcleos agora param em **13/13** (sem o resto da lista) e os Épicos+ vão
  **0/9 ... 9/9**; na Libertação os campos numéricos viraram **dropdown**
  (Núcleos 0/9 ... 9/9 e Épicos+ 0/4 ... 4/4) e continuam gravando
  **numero** no banco. Ver 5.12.
- **14/11** — **pendência #5 resolvida**: agora **clicar em qualquer
  parte do card** abre a edição daquele personagem (antes só a
  seta →). Cada card tem uma tag exclusiva no canvas, então não ha
  mistura entre os 25 cards. Ver 5.11.
- **14/11** — **pendência #6 resolvida**: os cards estavam **ilegiveis em FullHD e QuadHD** (texto por cima de texto). A causa era a fonte ser escalada **duas vezes** no card (2.56x o texto contra 1.6x do layout), larguras misturando px reais com px de design e o layout usando offsets fixos em vez das metricas reais das fontes. Agora o layout e **metrico** e a grade se adapta (3/5/5 colunas). Ver 5.10.
- **14/11** — **pendência #3 resolvida**: o **Nível do Chaser** agora
  vem do banco (coluna `user_characters.nivel_chaser`, bigint) e é
  **editável**: clicar no campo do cartão "NÍVEL DO CHASER" abre a
  janela de edição (inteiro >= 0, erro mostrado dentro da janela). O
  valor é **um por conta** (gravado em todas as linhas). Falta rodar
  `sql/nivel_chaser.sql` no Supabase. Ver 5.9.
- **14/11** — **2 bugs da tela de edição corrigidos**:
  (A) a seta de todos os cards usava a mesma tag `"seta"` no canvas — o
  binding do último card (Zero) respondia a todos os cliques; agora cada
  card tem uma tag exclusiva. (B) a edição lia "arma"/"anel"/"void4"
  numa tabela com "Arma"/"Anel"/"Void 4" — as chaves agora são
  normalizadas (`coluna_banco`), então o salvo volta marcado ao reabrir.
  Ver 5.8.
- **14/11** — **pendência #2 resolvida**: o card **atualiza ao vivo** com a
  tela de edição (cada checkbox/campo/dropdown redesenha o card) e foram
  aplicadas as **regras de cor**: ✓ verde / ✗ vermelho nas peças de Void,
  contorno verde nas missões concluídas e o texto dos acessórios colorido
  (azul/amarelo/roxo/vermelho por regra) **com contorno** para legibilidade.
  Ver 5.7.
- **14/11** — **pendência #1 resolvida**: salvamento no Supabase em **segundo
  plano** (thread de rede + polling na UI + upsert em lote) e **sem nenhuma
  janela de aviso** (só a barra de status). A UI volta a responder em 0,09s
  (antes congelava ~20s). Bônus: deduplicação das linhas filhas no banco
  (Kallia tinha 30 linhas em `user_semanais` → 25) e proteção na leitura.
  Ver 5.6.
## 8. Histórico curto
- **14/11** — **pendências registradas** (nada implementado): tabela de
  personagens = somente os cards (já feito), idioma só em português,
  "Instalar aplicativo" descartado, Missão Rápida (detalhes a venir),
  `nivel_chaser` como variável por conta, **salvar no banco em segundo
  plano** (hoje congela o app), enquadramento/organização dos cards em tela
  cheia, **tela de perfil** no espaço vago (Nick, troca de e-mail/senha,
  logout), **card inteiro clicável**, **cards em tempo real** com a edição e
  **instalador** compactado (sem vazar `service_role key`). Ver seção 6.

- **12/11** — login + Auth + camada Supabase + seed automático de 25 personagens + dropdowns +
  importação de Excel corrigida + correção da 1ª coluna (UUID → Nome) validados
  (`test_novos.py` 9/9, `test_ui.py`, screenshots, E2E autenticado OK).
- **12/11 (noite)** — usuário enviou mockup "Caminho da Maestria" + imagem de fundo;
  `app_grandchase.py` reescrito com a tela nova (cards, import, ações, tabview).
  Fundo implementado de 4 formas diferentes; console confirmava carregamento, mas a imagem
  continuava encoberta.
- **13/11 (manhã)** — fundo resolvido, cards dinâmicos, ações ligadas, botão Salvar,
  colunas amigáveis, Treeview escura, Torre semanal (alias `*_semanal`), testes
  automatizados e `.exe` validado.
- **13/11 (tarde)** — **tela principal refeita em 3 camadas** para bater 1:1 com o
  mockup "Caminho da Maestria": cenário PIL (arte no enquadramento original +
  violeta + painéis de vidro assados) + canvas com todos os textos/ícones +
  widgets sólidos. Emoji assados pelo PIL (Tk não desenha emoji), tabela de
  personagens oculta (`MOSTRAR_TABELA = False`), "Missão Rápida" com destaque
  visual. Novo módulo `tema_visual.py`.
- **13/11 (noite)** — **tela de login refeita**: logo `assets/login.png` como
  fundo (gradiente + glow + cartão de vidro), título "Caminho da Maestria",
  subtítulo "Controle de conta, feita para a Akkatsuki", botão Entrar com
  **gradiente na cor extraída da própria logo** (esmeralda `#35e3ab`), opção
  **Memorizar conta** (salva o e-mail em `login_prefs.json` após o login) e
  caixas de seleção desenhadas no canvas. Novos módulos `tema_login.py` e
  `caminhos.py`; spec com `login.png` no `datas`; `.exe` rebuildado e validado.
- **13/11 (noite)** — **corrigido o crash que impedia a tela principal de
  abrir**: `alloc: invalid block` ao destruir a janela de login com
  `ImageTk.PhotoImage` ainda vivos → agora `_liberar_recursos()` solta as
  imagens antes do `destroy()` (ver 5.5).
- **13/11 (noite)** — **botões ajustados**: ícones agora são imagens
  **quadradas** (o `getbbox` do emoji estourava o botão), conteúdo
  **centralizado** com auto-shrink da fonte, o `↻` foi **redesenhado com PIL**,
  o "Import Excel" saiu do `CTkButton` (o `compound="left"` desalinhava ícone e
  texto) e virou **gradiente roxo desenhado no canvas**, com **hover** em todos
  os botões. Novo teste E2E do `.exe` (`teste_login_exe.py`).
- **13/11 (noite)** — **bloco de importação esvaziado**: título, descrição,
  ESCOLHER ARQUIVO, campo e Import Excel foram removidos da tela; o painel de
  vidro permanece (espaço vago para novas ideias). Código do bloco intacto,
  atrás da flag `MOSTRAR_IMPORTACAO`.
- **13/11 (noite)** — **segmentado da login redesenhado no canvas**: o
  `CTkSegmentedButton` usava a mesma cor de texto nos 3 itens, e o item
  selecionado (verde) ficava ilegível. Agora é desenhado no canvas: pílula
  verde + **texto escuro** no item ativo e texto claro nos demais, com clique
  por item funcionando.
- **13/11 (noite)** — **cards de personagem** (`card_personagem.py`): o card
  desenhado no canvas principal (rola junto), escala adaptativa (1.0 → 1.6 no
  QHD) com grade sempre centralizada, **tela de edição** em Toplevel
  (`janela_personagem.py`) com todos os campos do mockup, **4 colunas novas** no
  banco (SQL rodado pelo usuário) + alias do "Fragmento do Vazio Disperso" (o
  rótulo tinha "do" e a coluna não) e correção do log no `.exe` sem console
  (`sys.stdout` é `None` → o `print` quebrava o `_registrar`).
- **13/11 (noite)** — **os 25 retratos** (`assets/personagens/*.png`) ligados de
  uma vez: recorte automático da borda transparente, encaixe no alto à direita do
  card e badge do título truncado para não invadir a arte. `datas` do spec
  ajustado para levar a pasta `personagens` no build. Cenário com tom violeta
  mais próximo do mockup.

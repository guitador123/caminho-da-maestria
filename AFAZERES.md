# Afazeres — Caminho da Maestria

Lista de melhorias saída da análise de 23/11/2026, em ordem de urgência.
Marque `[x]` ao concluir e anote o commit ao lado.

**Legenda:**
🔴 Crítica: segurança ou risco de perder dados/usuários. Fazer já.
🟠 Alta: bug ou risco real, mas sem dano imediato.
🟡 Média: manutenção que facilita todo o resto.
🟢 Baixa: funcionalidade nova ou melhoria de experiência.

---

## ✅ Concluído

- [x] Auto-update: reabrir o app no modo git depois do `git pull` (`07d0ad8`)
- [x] Auto-update: mostrar o aviso "Nova versão disponível" (`07d0ad8`)
- [x] Auto-update: abrir a versão antiga se a troca de arquivos falhar (`07d0ad8`)
- [x] Remover o `NOME_ASSET` duplicado e o `\r\r\n` do script auxiliar (`07d0ad8`)
- [x] Remover os métodos duplicados da missão rápida em `app_grandchase.py` (`07d0ad8`)
- [x] Publicar a release `v2026.11.23-07d0ad8`

---

## 🔴 Crítica

### 1. Trocar a senha da conta de teste e tirá-la do código ✅
O repositório é público, e a senha de `teste@teste.com` aparece em vários
`teste_*.py`, no `limpar_duplicados.py` e no `HANDOFF.md`.
Qualquer pessoa pode entrar no Supabase com ela.
- [x] Trocar a senha da conta de teste no Supabase e gravar a nova no `.env.teste` (23/11: senha antiga recusada, nova OK)
- [x] Ler e-mail/senha de variáveis de ambiente (`GC_TESTE_EMAIL`, `GC_TESTE_SENHA`) ou do `.env.teste` nos testes (`credenciais_teste.py`)
- [x] Remover a senha do `HANDOFF.md` e do `README.md`
- Obs.: a senha antiga continua no histórico do git; por isso a troca é obrigatória.
- **Pronto quando:** `git grep testeteste` não encontra nada e os testes rodam com as variáveis.

### 2. Versionar o schema e as políticas de RLS ✅
A chave pública está dentro do app, então o RLS é a única coisa que impede
um usuário de ler ou editar os dados de outro. Hoje as tabelas principais
e as policies não estão no repositório.
- [x] Teste `teste_rls.py`: sem login não lê nada; logado só vê e só grava o que é seu (23/11: RLS OK nas 5 tabelas)
- [x] Exportar o schema para `sql/schema.sql` (23/11)
- [x] Revisar: as 6 tabelas têm RLS ligado; insert/update/delete restritos ao dono
- [x] `sql/corrigir_permissoes.sql` aplicado (23/11): a `zerar_semanais()` (SECURITY DEFINER) estava liberada para anon e authenticated, ou seja, qualquer um podia zerar as semanais da guilda; agora só postgres/service_role. A `profiles` antiga deixou de ser legível sem login
- [x] `python teste_zerar_semanais.py --confirmar`: "PROTEGIDA" (anon e usuário comum recebem permissão negada)
- [x] Reexportado (23/11): FKs depois das tabelas, extensão `uuid-ossp` e permissões das funções; dá para recriar o banco só com `sql/schema.sql`
- **Pronto quando:** dá para recriar o banco do zero só com os arquivos de `sql/`.

### 3. Conferir a integridade das atualizações
O auto-update baixa e instala o zip da release sem checar nada. Se a conta
do GitHub for comprometida, todos os PCs da guilda rodam o código do invasor.
- [x] Assinatura Ed25519 em vez de só hash (`assinatura.py`): a chave privada fica em `~/.caminho-da-maestria/chave_release.pem` e a pública vai embutida no app
- [x] `publicar_release.py` assina o zip e sobe o `.sig` (e para antes do build se faltar a chave)
- [x] `atualizacao.py` só instala se a assinatura conferir; senão registra no log e abre a versão atual
- [x] `teste_assinatura.py`: válida instala; zip adulterado, .sig adulterado, sem .sig e chave de invasor são recusados
- [x] **Guardar uma cópia da chave privada** fora do PC (feito em 23/11)
- [x] Publicada a release `v2026.11.23-bc98408` com o `.sig` (a release real baixada do GitHub confere; o módulo está dentro do .exe)
- [ ] Ativar a verificação em duas etapas (2FA) na conta do GitHub (adiado; fazer depois)
- Obs.: o modo git (`atualizar.bat` / `git pull`) não é coberto pela assinatura; ele confia no GitHub. Aí a proteção é o 2FA.
- **Pronto quando:** um zip alterado é recusado e o app abre normalmente na versão atual.

---

## 🟠 Alta

### 4. Fixar as versões das dependências ✅
Com `>=` sem limite em `requirements.txt`, uma versão nova do `customtkinter`
ou do `supabase` pode quebrar os PCs da guilda no próximo `atualizar.bat`.
- [x] `requirements.txt` com `==` (as versões do build testado) + `constraints.txt` travando as 42 dependências, inclusive as indiretas
- [x] Instalação limpa num `.venv` novo = lock idêntico; `pip check` OK; testes de assinatura, RLS, integração e missão rápida passaram nesse `.venv`
- [x] Todas as 42 têm wheel para Python 3.11 no Windows (o mínimo do README)
- Obs.: para atualizar uma biblioteca, troque a versão no `requirements.txt` e no `constraints.txt`, rode os testes e publique uma release. Vale revisar a cada poucos meses (ex.: `certifi`, que traz os certificados).
- **Pronto quando:** `pip install -r requirements.txt` num `.venv` novo instala exatamente as mesmas versões.

### 5. Revisar a planilha `Controle Grand Chase (1).xlsx` no repositório ✅
- [x] Revisada (23/11): só os 25 nomes de personagem do jogo e valores de progresso; sem nick, e-mail, contato ou metadados pessoais. Pode ficar (é o modelo de onde saiu o `opcoes.py`)
- [x] Risco real encontrado: no modo git, "Salvar Excel" gravava POR CIMA dessa planilha versionada (os dados reais iriam para o GitHub num `git add .`). Agora o app sempre pergunta onde salvar quando o destino é a planilha-modelo

### 6. Salvamento atômico e só do que mudou ✅
Cada salvamento envia a conta inteira (25 personagens × todas as tabelas),
sem transação. Se uma tabela falhar no meio, as outras já foram gravadas.
- [x] Enviar só as linhas alteradas (`so_alteradas()` compara com `self.originals` quando vieram do banco; importado do Excel continua mandando tudo)
- [x] Gravar tudo numa função RPC no Postgres (`sql/salvar_conta.sql`, aplicado em 23/11): 1 requisição, 1 transação, `security invoker` (RLS vale), não troca dono nem personagem, recusa `id` de outra conta
- [x] Sem a função no banco, o app salva do jeito antigo e registra no log
- [x] `teste_salvar_atomico.py`: anon recusado; de 25 personagens só 1 enviado; lote com 1 linha inválida não grava nem a boa; id falso recusado; dono e personagem não mudam
- **Pronto quando:** uma falha no meio do salvamento não deixa o banco pela metade.

### 7. Parar de engolir erros (`except Exception: pass`) ✅
São cerca de 70 no projeto. Muitos escondem bugs reais (o aviso do
auto-update ficou quebrado por causa disso).
- [x] `registro.py`: `falha(contexto)` grava tipo, mensagem e traceback em `%LOCALAPPDATA%\Caminho da Maestria\gc_app.log` (uma vez por sessão; roda acima de 1 MB). Antes o log só era gravado no .exe e na pasta do programa
- [x] ~100 `except` revistos em 21 arquivos: widget já fechado (`TclError`) segue em silêncio; qualquer outro erro vai para o log. Casos esperados (coluna opcional ausente no banco, arquivo opcional inexistente) não poluem o log
- [x] Salvar, login, Excel e SQLite registram o erro além de mostrá-lo; atualização que falha mostra "Não foi possível atualizar agora" na janelinha antes de abrir a versão atual
- [x] Varredura de segredos (`gerar_instalador.py` e `auditoria_instalador.py`) não pula mais em silêncio um arquivo que não conseguiu ler: bloqueia. `zerar_semanais_semanal.py` não diz mais "zerou tudo" se não conseguiu conferir
- [x] O `robocopy /MIR` do auto-update apagava os `.log` da pasta do programa a cada atualização (justo quando o log de atualização mais importa); agora eles ficam (`/XF *.log *.log.1`)
- [x] O log já pegou um bug escondido: o `teste_acoes.py` "restaurava" a aba Semanais copiando o `id` da 1ª linha para todas, e o salvamento falhava em silêncio (corrigido)
- Obs.: `teste_edicao_supabase.py` já falhava antes (usa `.delete` num `CTkComboBox` do CustomTkinter 6); fica para o item 8
- **Pronto quando:** nenhum `except` fica sem registro.

---

## 🟡 Média

### 8. Migrar os testes para pytest e rodar no GitHub Actions ✅
Hoje são 42 scripts soltos que precisam de janela e de Supabase.
- [x] `tests/` com 87 testes de lógica pura: `opcoes`, `_limpar`/`_bool`, `so_alteradas` e `salvar_conta` (cliente Supabase falso: só o que mudou, fallback, erro não grava pela metade), `_sha_da_release`, feed de releases, script de troca do auto-update, `limpar_sobras`, assinatura (chave de teste), `registro`, Pix, helpers dos cards e do nível. Os filtros ficam para o item 10 (estão presos dentro da classe da janela)
- [x] `tests/test_integracao.py` roda 17 scripts `teste_*.py` (Supabase/janela) com o marcador `integracao`, fora do padrão: `python -m pytest -m integracao`
- [x] `.github/workflows/testes.yml`: Windows, Python 3.11 e 3.14, só leitura, a cada push e PR
- [x] `teste_edicao_supabase.py` consertado (alguns contadores viraram `CTkComboBox`)
- **Pronto quando:** `pytest` passa localmente e o check aparece verde no GitHub.

### 9. Organizar a raiz do projeto ✅
- [x] `src/` (18 módulos do app), `scripts/` (build, release, instalador, zerar semanal), `tools/` (prévias, esboços, `debug_app`, `limpar_duplicados`), `tests/integracao/` (os 45 `teste_*.py` + `credenciais_teste.py`). Os geradores de ícone/QR continuam em `assets/` (junto do que geram)
- [x] `app_grandchase.py` da raiz virou um **atalho** para `src/` (os `.bat` e o auto-update dos PCs em modo git continuam abrindo o mesmo arquivo; os `.bat` não mudaram)
- [x] `caminhos.app_dir()` e `atualizacao._app_dir()` continuam na raiz no modo fonte (`login_prefs.json`, planilha, `.git`); teste novo garante isso
- [x] `.spec` aponta para `src/`; o `.exe` montado abre normalmente; `publicar_release.py` chama os scripts em `scripts/`
- Para rodar um script de `tools/` ou `tests/integracao/` direto: `python tools/debug_app.py`, `python tests/integracao/teste_perfil.py` (o `_raiz.py` de cada pasta põe o `src/` no caminho)

### 10. Quebrar o `app_grandchase.py` (cerca de 2.700 linhas) ✅
- [x] Extrair filtros, missão rápida, salvamento e importação/exportação de Excel em módulos próprios: `app_filtros.py`, `app_missao.py`, `app_salvamento.py` (Supabase, nível, preferências), `app_arquivos.py` (Excel, SQLite, tabela), `app_cartoes.py` (cartões do topo), `config_app.py` (constantes) e `dados_app.py` (funções puras). O `app_grandchase.py` caiu de 2.759 para ~1.100 linhas (tela, cards, perfil, widgets)
- [x] Os métodos foram movidos sem mudar o código (o `GrandChaseApp` herda das partes; conferido por AST: os mesmos 106 métodos). Única mudança: `MOSTRAR_TABELA` virou `self.mostrar_tabela` (lido na criação)
- [x] `tests/test_dados_app.py`: testes puros das funções de colunas/valores
- [x] Fazer depois do item 8, para ter testes protegendo a refatoração (88 → 107 testes puros + 17 de integração passando)

---

## 🟢 Baixa (funcionalidades novas)

### 11. Botão "Verificar atualização" e versão visível ✅
- [x] Versão no estilo `1.0.0` (`src/versao_app.py`); o botão "Instalar aplicativo" (que só dizia "em breve") virou **"Versão 1.0.0"**
- [x] Clicar procura atualização na hora, em segundo plano (a tela não trava): "já está na mais recente", "sem internet", ou "Versão X disponível — atualizar agora?". Com alteração não salva, avisa e não atualiza
- [x] A release ganha o número no **título** ("Caminho da Maestria 1.1.0"); o nome técnico (`v<data>-<commit>`) não mudou, para os `.exe` antigos continuarem se atualizando. `publicar_release.py` recusa publicar um número repetido
- [x] Testes: `tests/test_atualizacao.py` (título → número, só verificar não instala nada) e `tests/integracao/teste_versao.py` (os 7 cenários do botão, com a instalação simulada)

### 12. Visão da guilda
- [ ] Ranking ou painel com o progresso semanal de todos (leitura entre membros via RLS)
- [ ] Destaque de quem ainda não fez as dungeons da semana

### 13. Histórico de evolução
- [ ] Guardar o poder e o ataque total por semana
- [ ] Gráfico de evolução por personagem

### 14. Funcionar offline
- [ ] Cache local dos dados quando o Supabase estiver fora
- [ ] Sincronizar quando a conexão voltar

---

## Ordem sugerida
1 → 2 → 3 → 4 → 5 → 7 → 6 → 8 → 9 → 10 → 11 → 12 → 13 → 14

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

### 13. Histórico de evolução ✅
- [x] **Banco** (`sql/historico_semanal.sql`): o reset de quarta 03h tira uma "foto" de cada personagem ANTES de zerar (Ataque Total, as 12 peças do Void e os 7 desafios da semana) em `user_historico_semanal`. Só o dono lê (RLS); só a função do reset grava. Se a foto falhar, o reset continua
- [x] `sql/historico_semanal.sql` aplicado (23/11): tabela com RLS (só o dono lê; usuário e anon não gravam nem chamam `registrar_semana`/`zerar_semanais`), coluna `resumo_visto` criada. A 1ª foto sai no reset de quarta, 25/11, 3h
- [x] **Página "Evolução semanal"**: Ataque Total médio da conta por semana (linha), por personagem (ranking com mini-linha e variação), peças do Void separadas em equipamentos (Elmo, Cota, Calça, Luva, Bota, Capa, Arma) e acessórios (Diadema, Máscara, Asas, Facas, Escudo), desafios semanais feitos (total, por semana e por desafio). Números e gráficos, no visual do app
- [x] Acesso pelo 9º cartão da grade ("EVOLUÇÃO SEMANAL", mostra a variação do ataque médio); abre **sozinha no 1º login após o reset** destacando a semana que acabou (uma vez por conta: `user_profiles.resumo_visto`)
- [x] Exportar: "Copiar imagem" (Ctrl+V no Discord) e "Salvar PNG": a página inteira é uma imagem, o que se vê é o que se compartilha
- [x] Testes: `tests/test_historico.py` (cálculos, reset de quarta em UTC×Brasília, abre 1 vez) e `tests/integracao/teste_evolucao.py` (cartão, abrir sozinha, copiar, salvar, sem a tabela)
- [x] No caminho: as legendas "characters complete" (Despertar/Libertação) viraram "personagens concluídos"

### Pendência vista no caminho
- [x] A barra de EXP saía do painel em 900 px: a ALTURA dela passava pela conversão de coordenada (somava o deslocamento vertical da tela). Agora é escalada como tamanho; `teste_perfil.py` confere 820 e 900 px
- [x] Level Chaser vai de 0 a **999** (o máximo do jogo): a janela recusa acima disso e o app trata valores maiores como 999
- [x] A barra mostra o **% até o próximo distintivo** (1-99, 100-199...): nível 5 = 5% (faltam 95 para o 100), 385 = 85%. A partir do 900 (o último distintivo) aparece "Distintivo máximo alcançado" e a barra sobe de 0% (900) a 100% (999, "100% · MÁX"). O % fica **dentro** da barra, em branco com contorno escuro; embaixo, "Próximo distintivo: Lv. 400 · faltam 15"

### 14. Funcionar offline ✅
- [x] **Cópia local** (`src/cache_local.py`): cada carga e cada salvamento gravam a conta em `%LOCALAPPDATA%\Caminho da Maestria\offline\<user_id>.json` (o que está na tela + o que está no banco + perfil + "pendente"). Antes de enviar, o app já guarda no PC: se a internet cair ou o app fechar no meio, nada se perde
- [x] **Entrar sem internet**: só a conta com "Memorizar conta" marcado. Fica um hash PBKDF2 da senha (nunca a senha) e o token da sessão, em `contas.bin` protegido pelo Windows (DPAPI). Desmarcar apaga a conta do arquivo
- [x] **Usar offline**: salvar vira pendência no PC (sair não pergunta "alterações não salvas"); a Evolução mostra só a semana atual
- [x] **Sincronizar quando a conexão voltar**: a cada 20 s tenta reabrir a sessão com o token guardado; se ele expirou, pede a senha uma vez. Vai só o que mudou offline, personagem por personagem (os não mexidos ficam como estão no banco). Uma pendência de uma sessão anterior é enviada antes da carga normal
- [x] Testes: `tests/test_cache_local.py`, `tests/test_login_offline.py` e `tests/integracao/teste_offline.py` (abrir offline, editar, reconectar, pendência antiga, queda no meio do uso)
- Limite: nick e foto do perfil só mudam com internet

---

## 🔧 Pendências que apareceram no caminho

### Filtros dos cards (Ataque Total, Caminho Abissal, Torre) ✅
- [x] **Bug:** depois de editar um personagem, marcar uma dungeon ou zerar as dungeons, os cards eram redesenhados mas a lista NÃO era refeita: mudar o Ataque Total não trocava a ordem, e com o filtro "não fez Caminho Abissal/Torre" ligado o card marcado continuava aparecendo até mexer em algum filtro. Agora `_reordenar_cards()` refaz filtro + ordem na hora (mantendo a rolagem)
- [x] **Bug:** o card mostra o Ataque Total com ponto de milhar ("618.002"), mas o campo de edição lia "618.002" como 618. Agora aceita o ponto de milhar
- [x] A lógica foi para `src/filtros.py` (funções puras) com 20 testes em `tests/test_filtros.py`, incluindo a Torre das Ilusões, que tem o mesmo nome nas duas abas (Geral = andar do mês; Semanais = fez esta semana; o filtro usa a da semana)
- [x] `tests/integracao/teste_filtro_ao_vivo.py` reproduz os dois casos na tela (falha no código antigo, passa no novo)
- [x] **Bug:** clicar no filtro (Caminho Abissal, Torre...) fazia a tela saltar para cima e deixava a arte de fundo deslocada. Causas: a rolagem era guardada como FRAÇÃO da página (que encolhe quando o filtro esconde cards), a página podia ficar menor que a janela, e o cenário "fixo" não era reposicionado. Agora a rolagem é guardada em pixels, a tela fica parada (só sobe o necessário quando sobraria espaço vazio, nunca acima da barra de filtros) e o fundo acompanha. `tests/integracao/teste_filtro_rolagem.py` reproduz (no código antigo: 840 → 200 px e 1560 → 360 px, com o fundo fora do lugar)

### Rolagem da página ✅
- [x] Antes, cada clique da roda andava **40 px secos** (147 a 230 cliques até o último card). Agora (`src/rolagem.py`): o passo é ~1/5 da altura da tela (igual em qualquer resolução), a tela **desliza** até o destino (~250 ms, animação por tempo, não por quadro) e cliques rápidos **aceleram** até 3×. Até o fim: 26–60 cliques devagar, 11–23 girando rápido. A janela da Evolução usa a mesma rolagem
- [x] Testes: `tests/test_rolagem.py` (desaceleração, aceleração, limites) e `tests/integracao/teste_rolagem_suave.py` (4 resoluções, fundo parado em todos os quadros)

### Pix (`monta_payload`) ✅
- [x] O payload gerado pelo código não era um Pix válido: tinha um campo `01` = `26` inexistente e faltava o `0014` (GUI) dentro do campo 26. Agora segue o manual do BR Code e reproduz **caractere por caractere** o exemplo oficial do Banco Central (teste em `tests/test_helpers.py`); a chave vai normalizada e o `gerar_qr.py` confere estrutura e CRC antes de gravar
- [x] `pix_pagamento.campos_do_payload()` lê e valida um payload (recusa CRC errado e campo cortado)
- [x] Chave Pix trocada (24/11): `gerar_qr.py --forcar` gerou o copia e cola e o QR. Agora ele grava os TRÊS arquivos (`pix_payload.txt`, `qr_pix.png` e o `assets/qrcode-pix.png` que o painel mostra) a partir do mesmo payload, com a chave normalizada, a margem branca de 4 módulos e no tamanho exato do painel (245 px, sem esticar). Conferido: as duas imagens decodificam igual ao copia e cola

### Painel de doação ✅
- [x] Uma coluna só (480 px), tudo na mesma margem: valores em 3 colunas iguais, QR centralizado numa moldura branca com "Para: <nome>", copia e cola legível e botão "Copiar código Pix" com o aviso logo abaixo
- [x] Cabe inteiro numa janela de 900 px; em janelas menores o conteúdo rola (a barra some quando tudo cabe). Esc fecha
- [x] Bugs: o aviso de erro quebrava (faltava a cor `erro`); o rodapé citava "Cartão" (não existe); textos sem acento; o "Fechar" duplicava o X
- [x] Copiar usa o `clip.exe` sem abrir janela (o conteúdo fica na área de transferência mesmo depois que o app fecha)

### Limpeza de código ✅
- [x] Imports sem uso removidos (`login.py`, `tema_visual.py`, `janela_doacao.py`, `publicar_release.py`, `previa_cenario.py`); os reexportados pelo `app_grandchase.py` agora estão declarados em `__all__`
- [x] Variáveis nunca usadas, um f-string sem variável e o `_crc16` duplicado do `gerar_qr.py` removidos: o pyflakes fica limpo (só os `import _raiz`, que são de propósito)

## Ordem sugerida
1 → 2 → 3 → 4 → 5 → 7 → 6 → 8 → 9 → 10 → 11 → 12 → 13 → 14

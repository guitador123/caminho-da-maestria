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
- [ ] `publicar_release.py` gera o SHA-256 do zip e publica junto da release
- [ ] `atualizacao.py` confere o hash antes de instalar (e não instala se não bater)
- [ ] Ativar a verificação em duas etapas (2FA) na conta do GitHub, se ainda não estiver
- **Pronto quando:** um zip alterado é recusado e o app abre normalmente na versão atual.

---

## 🟠 Alta

### 4. Fixar as versões das dependências
Com `>=` sem limite em `requirements.txt`, uma versão nova do `customtkinter`
ou do `supabase` pode quebrar os PCs da guilda no próximo `atualizar.bat`.
- [ ] Trocar para `==` com as versões que funcionam hoje (ou gerar um lock file)
- **Pronto quando:** `pip install -r requirements.txt` num `.venv` novo instala exatamente as mesmas versões.

### 5. Revisar a planilha `Controle Grand Chase (1).xlsx` no repositório
- [ ] Ver se tem dados reais da guilda (nicks, progresso)
- [ ] Se tiver: tirar do repositório e pôr no `.gitignore` (e avaliar limpar do histórico)

### 6. Salvamento atômico e só do que mudou
Cada salvamento envia a conta inteira (25 personagens × todas as tabelas),
sem transação. Se uma tabela falhar no meio, as outras já foram gravadas.
- [ ] Enviar só as linhas alteradas (comparando com `self.originals`)
- [ ] Gravar tudo numa função RPC no Postgres (uma transação só)
- **Pronto quando:** uma falha no meio do salvamento não deixa o banco pela metade.

### 7. Parar de engolir erros (`except Exception: pass`)
São cerca de 70 no projeto. Muitos escondem bugs reais (o aviso do
auto-update ficou quebrado por causa disso).
- [ ] Trocar por `_registrar(...)` no log, no mínimo
- [ ] Mostrar ao usuário os erros que importam (salvar, login, atualização)
- **Pronto quando:** nenhum `except` fica sem registro.

---

## 🟡 Média

### 8. Migrar os testes para pytest e rodar no GitHub Actions
Hoje são 42 scripts soltos que precisam de janela e de Supabase.
- [ ] Criar `tests/` com testes de lógica pura (filtros, `opcoes`, `_limpar`, `_sha_da_release`, script do auto-update)
- [ ] Separar os testes que precisam do Supabase ou de janela (marcador `@pytest.mark.integracao`)
- [ ] Workflow do GitHub Actions rodando os testes puros a cada push
- **Pronto quando:** `pytest` passa localmente e o check aparece verde no GitHub.

### 9. Organizar a raiz do projeto
- [ ] `src/` (código do app), `tests/`, `scripts/` (build, release, instalador), `tools/` (prévias, esboços, geradores de ícone)
- [ ] Ajustar o `.spec` do PyInstaller, os `.bat` e o auto-update para os caminhos novos
- **Atenção:** o auto-update dos PCs já instalados chama `app_grandchase.py` na raiz. Manter um atalho ali ou migrar com cuidado.

### 10. Quebrar o `app_grandchase.py` (cerca de 2.700 linhas)
- [ ] Extrair filtros, missão rápida, salvamento e importação/exportação de Excel em módulos próprios
- [ ] Fazer depois do item 8, para ter testes protegendo a refatoração

---

## 🟢 Baixa (funcionalidades novas)

### 11. Botão "Verificar atualização" e versão visível
- [ ] Mostrar "versão X instalada" no app
- [ ] Botão para procurar atualização na hora

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

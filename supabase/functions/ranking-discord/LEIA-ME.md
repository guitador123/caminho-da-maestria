# Ranking da guilda no Discord: passo a passo

Uma mensagem **fixa** num canal do Discord com os 5 pódios e o campeão de cada personagem. A cada 5 minutos o Supabase **edita** essa mesma mensagem (nunca manda uma nova).

Como funciona: o agendador do banco (pg_cron) chama a Edge Function `ranking-discord` a cada 5 minutos. Ela lê o ranking do banco e edita a mensagem pelo webhook do canal. A URL do webhook fica **só** nos segredos do Supabase: nunca vai para o app nem para o repositório.

Arquivos:
- `sql/discord.sql`: a parte do banco (os dados e onde fica o ID da mensagem)
- `supabase/functions/ranking-discord/index.ts`: a Edge Function
- `sql/discord_agendar.sql`: o agendamento a cada 5 minutos

---

## Parte 1: o canal e o webhook (no Discord)

1. Crie um canal só para o ranking (ex.: `#ranking`). Sugestão: em **Editar canal → Permissões**, tire de `@everyone` a permissão **Enviar mensagens**, para a mensagem ficar sozinha no canal.
2. Ainda em **Editar canal**, vá em **Integrações → Webhooks → Novo webhook**.
3. Dê o nome **Caminho da Maestria** e, se quiser, troque a foto pelo ícone do app.
4. Clique em **Copiar URL do webhook**. Guarde-a por enquanto (no Bloco de Notas, por exemplo).

> A URL do webhook é uma **senha**: quem tiver ela posta no canal. Não mande no chat nem em print.

## Parte 2: o banco (SQL)

1. Supabase → **SQL Editor** → cole o arquivo inteiro `sql/discord.sql` → **Run**.
2. A conferência no fim deve mostrar:
   - `ranking_dados`: `false / false / false / true`
   - `ranking_da_guilda`: `false / true / true`

## Parte 3: os 2 segredos

1. Gere um segredo aleatório (no PowerShell; ele já vai para a área de transferência):
   ```powershell
   ([guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")) | Set-Clipboard
   ```
2. Supabase → **Edge Functions → Secrets** (às vezes em "Manage secrets") → adicione:
   - `DISCORD_WEBHOOK_URL` = a URL copiada na Parte 1
   - `SEGREDO_RANKING` = o segredo gerado agora
3. Guarde o segredo no Bloco de Notas também: ele é usado de novo na Parte 5.

## Parte 4: a Edge Function

1. Supabase → **Edge Functions → Deploy a new function → Via Editor**.
2. Nome: **`ranking-discord`** (exatamente assim).
3. Apague o código de exemplo e cole **todo** o conteúdo de `supabase/functions/ranking-discord/index.ts`.
4. Clique em **Deploy**.
5. Nos detalhes da função (aba **Details** ou **Settings**), **desligue** a opção **Verify JWT** / **Enforce JWT verification** e salve. Quem protege a função é o `SEGREDO_RANKING`: sem ele, ela responde "nao autorizado" e não faz nada.

## Parte 5: ligar (e ver a mensagem aparecer)

1. Abra `sql/discord_agendar.sql` e troque as **2** ocorrências de `COLE_O_SEGREDO_AQUI` pelo segredo da Parte 3.
2. Supabase → **SQL Editor** → cole o arquivo (já com o segredo) → **Run**.
3. Ele agenda a atualização a cada 5 minutos **e** já chama uma vez: em alguns segundos a mensagem aparece no canal.
4. A conferência no fim mostra `ranking-discord | */5 * * * * | true`.

## Parte 6: acabamento

1. No Discord, clique na mensagem → **Fixar mensagem**.
2. Pronto: daqui para frente ela se atualiza sozinha.

---

## Se a mensagem não aparecer

Rode no SQL Editor (mostra as últimas respostas da função):

```sql
select created, status_code, left(content::text, 300) as resposta
  from net._http_response order by created desc limit 5;
```

| O que aparece | O que fazer |
|---|---|
| `401` / "nao autorizado" | o segredo do `discord_agendar.sql` não é igual ao `SEGREDO_RANKING` (Parte 3 e 5) |
| `401` com "Invalid JWT" / "Missing authorization" | a verificação de JWT ainda está ligada (Parte 4, item 5) |
| `404` | o nome da função não é exatamente `ranking-discord` |
| `500` com "DISCORD_WEBHOOK_URL" | falta o segredo `DISCORD_WEBHOOK_URL` (Parte 3) |
| `500` com "Discord: 401" ou "Unknown Webhook" | a URL do webhook está errada ou o webhook foi apagado: crie outro (Parte 1) e troque o segredo |
| `500` com "ranking_dados" | rode de novo o `sql/discord.sql` (Parte 2) |

Os erros também aparecem em **Edge Functions → ranking-discord → Logs**.

## Para mudar ou parar

- **Apagaram a mensagem?** Não precisa fazer nada: na próxima atualização a função posta uma nova (e passa a editar essa).
- **Trocar de canal:** crie o webhook no canal novo, troque o segredo `DISCORD_WEBHOOK_URL` e apague a linha guardada (`delete from public.discord_mensagens where chave = 'ranking';`).
- **Parar de atualizar:** `select cron.unschedule('ranking-discord');`

-- ===========================================================================
-- Item 12: AGENDAR o ranking no Discord (a cada 5 minutos)
--
-- Rode SO DEPOIS de criar a Edge Function "ranking-discord" e de ver a
-- mensagem aparecer no canal (ver o tutorial).
--
-- ANTES DE RODAR: troque  COLE_O_SEGREDO_AQUI  (2 vezes, abaixo) pelo
-- mesmo segredo que voce colocou em SEGREDO_RANKING nos segredos das Edge
-- Functions. Ele so fica guardado aqui, no agendador do banco.
--
-- Pode rodar de novo sem duplicar (o agendamento tem nome fixo).
-- ===========================================================================

-- o pg_net faz a chamada HTTP de dentro do banco
create extension if not exists pg_net;

-- (re)cria o agendamento: a cada 5 minutos, chama a Edge Function
select cron.unschedule(jobid) from cron.job where jobname = 'ranking-discord';
select cron.schedule(
  'ranking-discord',
  '*/5 * * * *',
  $$
  select net.http_post(
    url := 'https://rtpwvfrdhrvtulvvctze.supabase.co/functions/v1/ranking-discord',
    headers := '{"Content-Type": "application/json", "x-segredo": "COLE_O_SEGREDO_AQUI"}'::jsonb,
    body := '{}'::jsonb
  );
  $$
);

-- e ja atualiza uma vez agora
select net.http_post(
  url := 'https://rtpwvfrdhrvtulvvctze.supabase.co/functions/v1/ranking-discord',
  headers := '{"Content-Type": "application/json", "x-segredo": "COLE_O_SEGREDO_AQUI"}'::jsonb,
  body := '{}'::jsonb
);

-- conferencia: deve aparecer 1 linha, ranking-discord, */5 * * * *, ativo
select jobname, schedule, active from cron.job where jobname = 'ranking-discord';

-- (para PARAR de atualizar um dia:)
--   select cron.unschedule('ranking-discord');

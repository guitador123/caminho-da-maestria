-- ===========================================================================
-- Item 12 (27/11): o ranking da guilda no Discord (PARTE DO BANCO)
--
-- Uma mensagem FIXA num canal do Discord, editada a cada 5 minutos pela
-- Edge Function "ranking-discord" (supabase/functions/ranking-discord).
--
-- Este arquivo:
--   1) cria a tabela onde fica o ID da mensagem (para editar sempre a
--      mesma). Ninguem do app le nem grava nela (RLS sem politicas); so a
--      Edge Function, com a chave de servico;
--   2) cria ranking_dados(): os mesmos dados da guia Ranking, que SO a
--      Edge Function (service_role) chama;
--   3) refaz ranking_da_guilda() (a da guia Ranking) para usar a mesma
--      funcao (o resultado no app nao muda).
--
-- O AGENDAMENTO (a cada 5 minutos) fica em sql/discord_agendar.sql, que so
-- roda DEPOIS da Edge Function existir (ver o tutorial).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- ===========================================================================

-- 1) onde fica o ID da mensagem do Discord -----------------------------------
create table if not exists public.discord_mensagens (
  chave text primary key,
  message_id text not null,
  atualizado_em timestamp with time zone default now() not null
);
alter table public.discord_mensagens enable row level security;
-- (sem politicas: anon e authenticated nao veem nada; a service_role passa)

-- 2) os dados do ranking (todas as contas), so para a Edge Function ----------
create or replace function public.ranking_dados()
returns jsonb
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
begin
  return jsonb_build_object(
    'contas', coalesce((
      select jsonb_agg(c)
        from (
          select uc.user_id,
                 nullif(trim(max(p.nick)), '') as nick,
                 coalesce(max(uc.nivel_chaser), 0) as nivel_chaser,
                 coalesce(max(uc.colecao_cartas), 0) as colecao_cartas,
                 coalesce(round(avg(uc.poder)), 0) as ataque_medio,
                 case when length(coalesce(max(p.avatar), '')) between 1 and 40
                      then max(p.avatar) end as avatar,
                 coalesce(sum((
                   select count(*)
                     from public.user_semanais us,
                          jsonb_each(to_jsonb(us)) as d(chave, valor)
                    where us.character_id = uc.id
                      and d.chave in ('fornalha_infernal', 'altar_da_runha',
                                      'torre_das_ilusoes_semanal', 'void_123',
                                      'void_4', 'caminho_abissal',
                                      'terra_do_julgamento')
                      and d.valor = 'true'::jsonb)), 0) as dungeons
            from public.user_characters uc
            left join public.user_profiles p on p.id = uc.user_id
           group by uc.user_id
        ) c), '[]'::jsonb),
    'personagens', coalesce((
      select jsonb_agg(jsonb_build_object(
               'user_id', uc.user_id,
               'character_name', uc.character_name,
               'poder', coalesce(uc.poder, 0),
               'ataque', coalesce((to_jsonb(uc) ->> 'ataque')::numeric, 0),
               'ataque_especial',
                 coalesce((to_jsonb(uc) ->> 'ataque_especial')::numeric, 0),
               'critico', coalesce((to_jsonb(uc) ->> 'critico')::numeric, 0),
               'dano_critico',
                 coalesce((to_jsonb(uc) ->> 'dano_critico')::numeric, 0)))
        from public.user_characters uc), '[]'::jsonb)
  );
end;
$$;

revoke execute on function public.ranking_dados() from public, anon, authenticated;
grant execute on function public.ranking_dados() to service_role;

-- 3) a guia Ranking do app usa a mesma funcao (precisa de login) -------------
create or replace function public.ranking_da_guilda()
returns jsonb
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
begin
  if auth.uid() is null then
    raise exception 'ranking_da_guilda: e preciso estar logado'
      using errcode = '42501';
  end if;
  return public.ranking_dados();
end;
$$;

revoke execute on function public.ranking_da_guilda() from public, anon;
grant execute on function public.ranking_da_guilda() to authenticated;

notify pgrst, 'reload schema';

-- conferencia: a 1a linha deve ser false/false/false/true (so a Edge
-- Function chama ranking_dados) e a 2a false/true/true
select 'ranking_dados' as funcao,
       has_function_privilege('anon', 'public.ranking_dados()', 'execute') as anon,
       has_function_privilege('authenticated', 'public.ranking_dados()', 'execute') as logado,
       has_function_privilege('service_role', 'public.ranking_dados()', 'execute') as servico
union all
select 'ranking_da_guilda',
       has_function_privilege('anon', 'public.ranking_da_guilda()', 'execute'),
       has_function_privilege('authenticated', 'public.ranking_da_guilda()', 'execute'),
       has_function_privilege('service_role', 'public.ranking_da_guilda()', 'execute');

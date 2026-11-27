-- ===========================================================================
-- Item 19 (27/11): a guia "Ranking"
--
-- Devolve, de TODAS as contas do app:
--   - contas: nick, avatar, Level Chaser, colecao, Ataque Total medio e as
--     dungeons semanais feitas NA SEMANA ATUAL (soma dos 25 personagens);
--   - personagens: o Ataque Total, o Ataque, o Ataque Especial, o % de
--     critico e o % de dano critico de cada personagem de cada conta.
-- O app monta os campeoes e os 5 podios (src/ranking.py).
--
-- Seguranca (igual a sql/guilda.sql): as tabelas continuam fechadas; esta
-- funcao so LE, precisa de login (anon nao chama) e nao devolve
-- username/e-mail.
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- ===========================================================================

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
  return jsonb_build_object(
    'contas', coalesce((
      select jsonb_agg(c)
        from (
          select uc.user_id,
                 nullif(trim(max(p.nick)), '') as nick,
                 case when length(coalesce(max(p.avatar), '')) between 1 and 40
                      then max(p.avatar) end as avatar,
                 coalesce(max(uc.nivel_chaser), 0) as nivel_chaser,
                 coalesce(max(uc.colecao_cartas), 0) as colecao_cartas,
                 coalesce(round(avg(uc.poder)), 0) as ataque_medio,
                 -- as 7 dungeons da semana ATUAL (o reset de quarta zera)
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

-- so quem esta logado chama (anon nao)
revoke execute on function public.ranking_da_guilda() from public, anon;
grant execute on function public.ranking_da_guilda() to authenticated;

-- PostgREST: recarrega as funcoes para o app enxergar
notify pgrst, 'reload schema';

-- conferencia: deve mostrar anon = false e authenticated = true
select has_function_privilege('anon', 'public.ranking_da_guilda()', 'execute')
         as anon,
       has_function_privilege('authenticated', 'public.ranking_da_guilda()',
                              'execute') as authenticated;

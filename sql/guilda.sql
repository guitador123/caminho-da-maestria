-- ===========================================================================
-- Item 12 (27/11): o HUB da guilda
--
-- Todas as contas do app aparecem no HUB (sem opcao de ficar de fora), em
-- ordem de Level Chaser (desempate: Ataque Total medio). Clicar num perfil
-- mostra a conta da pessoa SO PARA VER.
--
-- Seguranca:
--   - as tabelas NAO sao abertas: o RLS continua "cada um ve e grava so o
--     seu". A leitura entre contas passa por estas 2 funcoes, que devolvem
--     so o necessario e NAO gravam nada;
--   - security definer + "precisa estar logado" (anon nao chama);
--   - o perfil sai so com nick e avatar (o username/e-mail NAO sai).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- ===========================================================================

-- 1) a lista do HUB ---------------------------------------------------------
create or replace function public.perfis_da_guilda()
returns table (
  user_id uuid,
  nick text,
  avatar text,
  nivel_chaser bigint,
  colecao_cartas bigint,
  ataque_medio numeric,
  personagens integer
)
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
#variable_conflict use_column
begin
  if auth.uid() is null then
    raise exception 'perfis_da_guilda: e preciso estar logado'
      using errcode = '42501';
  end if;
  return query
    select uc.user_id,
           nullif(trim(max(p.nick)), ''),
           -- so o nome do personagem da foto (o formato antigo, base64,
           -- e grande demais e fica de fora)
           case when length(coalesce(max(p.avatar), '')) between 1 and 40
                then max(p.avatar) end,
           coalesce(max(uc.nivel_chaser), 0)::bigint,
           coalesce(max(uc.colecao_cartas), 0)::bigint,
           coalesce(round(avg(uc.poder)), 0)::numeric,
           count(*)::integer
      from public.user_characters uc
      left join public.user_profiles p on p.id = uc.user_id
     group by uc.user_id
     order by 4 desc, 6 desc;
end;
$$;

-- 2) a conta de uma pessoa (so para ver) -------------------------------------
create or replace function public.conta_da_guilda(p_user uuid)
returns jsonb
language plpgsql
stable
security definer
set search_path = public, pg_temp
as $$
begin
  if auth.uid() is null then
    raise exception 'conta_da_guilda: e preciso estar logado'
      using errcode = '42501';
  end if;
  return jsonb_build_object(
    'perfil', (
      select jsonb_build_object(
               'nick', nullif(trim(p.nick), ''),
               'avatar', case when length(coalesce(p.avatar, '')) between 1 and 40
                              then p.avatar end)
        from public.user_profiles p where p.id = p_user),
    'personagens', coalesce((
      select jsonb_agg(to_jsonb(uc) - 'user_id' - 'updated_at')
        from public.user_characters uc where uc.user_id = p_user), '[]'::jsonb),
    'pecas_void', coalesce((
      select jsonb_agg(to_jsonb(t) - 'updated_at')
        from public.user_pecas_void t
        join public.user_characters uc on uc.id = t.character_id
       where uc.user_id = p_user), '[]'::jsonb),
    'acessorios_titulo', coalesce((
      select jsonb_agg(to_jsonb(t) - 'updated_at')
        from public.user_acessorios_titulo t
        join public.user_characters uc on uc.id = t.character_id
       where uc.user_id = p_user), '[]'::jsonb),
    'semanais', coalesce((
      select jsonb_agg(to_jsonb(t) - 'updated_at')
        from public.user_semanais t
        join public.user_characters uc on uc.id = t.character_id
       where uc.user_id = p_user), '[]'::jsonb)
  );
end;
$$;

-- so quem esta logado chama (anon nao)
revoke execute on function public.perfis_da_guilda() from public, anon;
grant execute on function public.perfis_da_guilda() to authenticated;
revoke execute on function public.conta_da_guilda(uuid) from public, anon;
grant execute on function public.conta_da_guilda(uuid) to authenticated;

-- PostgREST: recarrega as funcoes para o app enxergar
notify pgrst, 'reload schema';

-- conferencia: deve mostrar anon = false e authenticated = true (2 linhas)
select f, has_function_privilege('anon', f, 'execute') as anon,
       has_function_privilege('authenticated', f, 'execute') as authenticated
  from (values ('public.perfis_da_guilda()'),
               ('public.conta_da_guilda(uuid)')) as v(f);

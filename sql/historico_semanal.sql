-- ============================================================
--  Caminho da Maestria - HISTORICO SEMANAL (pagina "Evolucao")
--
--  Toda quarta as 03h (Brasilia) o pg_cron chama zerar_semanais().
--  Agora, ANTES de zerar as dungeons, ela tira uma "foto" de cada
--  personagem de cada conta e guarda em user_historico_semanal:
--    - Ataque Total (poder)
--    - o Level Chaser da conta (nivel_chaser)
--    - as 12 pecas do Void (equipamentos e acessorios)
--    - os 7 desafios semanais feitos na semana que acabou
--
--  O app le esse historico (cada conta so ve o seu: RLS) e monta a
--  pagina de Evolucao com numeros e graficos.
--
--  Seguranca:
--    - a tabela so pode ser LIDA pelo dono (nao ha policy de insert,
--      update nem delete: ninguem grava por fora);
--    - so registrar_semana() grava (SECURITY DEFINER), e so postgres e
--      service_role podem chamar (nao o anon nem um usuario logado).
--
--  Rodar no SQL Editor do Supabase (pode rodar de novo sem problema).
-- ============================================================

-- 1) a tabela ---------------------------------------------------------------
create table if not exists public.user_historico_semanal (
  id uuid default uuid_generate_v4() not null,
  user_id uuid not null,
  character_id uuid,
  character_name text not null,
  -- a data (Brasilia) do reset que FECHOU a semana (uma quarta-feira)
  semana date not null,
  poder bigint,
  -- o Level Chaser da conta (o mesmo em todas as linhas da semana)
  nivel_chaser bigint,
  -- a colecao de cartas da conta (idem)
  colecao_cartas bigint,
  pecas_void jsonb not null default '{}'::jsonb,
  desafios jsonb not null default '{}'::jsonb,
  criado_em timestamp with time zone default now() not null,
  constraint user_historico_semanal_pkey primary key (id),
  constraint user_historico_semanal_unico
    unique (user_id, character_name, semana),
  constraint user_historico_semanal_user_id_fkey foreign key (user_id)
    references auth.users(id) on delete cascade,
  constraint user_historico_semanal_character_id_fkey foreign key
    (character_id) references public.user_characters(id) on delete set null
);
-- quem rodou a versao anterior deste SQL ganha a coluna aqui
alter table public.user_historico_semanal
  add column if not exists nivel_chaser bigint;
alter table public.user_historico_semanal
  add column if not exists colecao_cartas bigint;
-- a foto le a colecao da conta (sql/colecao_cartas.sql)
alter table public.user_characters
  add column if not exists colecao_cartas bigint default 0;

create index if not exists user_historico_semanal_user_semana
  on public.user_historico_semanal (user_id, semana);

alter table public.user_historico_semanal enable row level security;

drop policy if exists "Users can view own historico"
  on public.user_historico_semanal;
create policy "Users can view own historico" on public.user_historico_semanal
  as permissive for select to authenticated
  using (auth.uid() = user_id);

-- 2) o "ja vi o resumo desta semana" (abre a pagina so 1 vez por reset) ------
alter table public.user_profiles
  add column if not exists resumo_visto date;

-- 3) a foto da semana ------------------------------------------------------
create or replace function public.registrar_semana(
  p_semana date default (now() at time zone 'America/Sao_Paulo')::date)
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  total integer;
begin
  insert into public.user_historico_semanal
    (user_id, character_id, character_name, semana, poder, nivel_chaser,
     colecao_cartas, pecas_void, desafios)
  select uc.user_id, uc.id, uc.character_name, p_semana, uc.poder,
         uc.nivel_chaser, uc.colecao_cartas,
         coalesce((select to_jsonb(pv) - 'id' - 'character_id' - 'updated_at'
                     from public.user_pecas_void pv
                    where pv.character_id = uc.id
                    limit 1), '{}'::jsonb),
         coalesce((select to_jsonb(us) - 'id' - 'character_id' - 'updated_at'
                     from public.user_semanais us
                    where us.character_id = uc.id
                    limit 1), '{}'::jsonb)
    from public.user_characters uc
  on conflict (user_id, character_name, semana) do update
    set character_id = excluded.character_id,
        poder = excluded.poder,
        nivel_chaser = excluded.nivel_chaser,
        colecao_cartas = excluded.colecao_cartas,
        pecas_void = excluded.pecas_void,
        desafios = excluded.desafios,
        criado_em = now();
  get diagnostics total = row_count;
  return total;
end;
$$;

revoke execute on function public.registrar_semana(date)
  from public, anon, authenticated;
grant execute on function public.registrar_semana(date)
  to postgres, service_role;

-- 4) o reset de quarta tira a foto ANTES de zerar --------------------------
-- (o mesmo corpo de antes + a chamada no comeco; se a foto falhar, o
--  reset continua: zerar as dungeons e mais importante que o historico)
create or replace function public.zerar_semanais()
returns integer
language plpgsql
security definer
set search_path to 'public', 'pg_temp'
as $function$
declare
  colunas text[] := array[
    'fornalha_infernal', 'altar_da_runha', 'torre_das_ilusoes_semanal',
    'void_123', 'void_4', 'caminho_abissal', 'terra_do_julgamento',
    'updated_at'
  ];
  col text;
  existe boolean;
  tem_id boolean;
  filtro text;
  condicoes text[] := '{}';
  partes text[] := '{}';
  total integer := 0;
begin
  -- a foto da semana que esta acabando (pagina "Evolucao" do app)
  begin
    perform public.registrar_semana();
  exception when others then
    raise warning 'registrar_semana falhou (o reset continua): %', sqlerrm;
  end;

  -- monta o SET so com as colunas que existem de fato no banco
  foreach col in array colunas loop
    select exists (
      select 1 from information_schema.columns
       where table_schema = 'public'
         and table_name = 'user_semanais'
         and column_name = col
    ) into existe;

    if existe then
      if col = 'updated_at' then
        partes := array_append(partes, 'updated_at = now()');
      else
        partes := array_append(partes, col || ' = false');
        condicoes := array_append(condicoes, col);
      end if;
    end if;
  end loop;

  if coalesce(array_length(partes, 1), 0) = 0 then
    raise exception 'nenhuma coluna de missao semanal encontrada em public.user_semanais';
  end if;

  select exists (
    select 1 from information_schema.columns
     where table_schema = 'public'
       and table_name = 'user_semanais'
       and column_name = 'id'
  ) into tem_id;

  if coalesce(array_length(condicoes, 1), 0) > 0 then
    filtro := 'where (' || array_to_string(condicoes, ' or ') || ')';
    if tem_id then
      filtro := filtro || ' and id is not null';
    end if;
  else
    filtro := case when tem_id then 'where id is not null' else 'where true' end;
  end if;

  execute format('update public.user_semanais set %s %s',
                 array_to_string(partes, ', '), filtro);

  get diagnostics total = row_count;
  return total;
end;
$function$;

-- create or replace mantem as permissoes, mas reforca:
revoke execute on function public.zerar_semanais()
  from public, anon, authenticated;
grant execute on function public.zerar_semanais() to postgres, service_role;

-- PostgREST: recarrega a lista de tabelas/funcoes para o app enxergar
notify pgrst, 'reload schema';

-- conferencia: deve mostrar tudo false, menos o ultimo (true)
select
  has_function_privilege('anon', 'public.registrar_semana(date)', 'execute')
    as anon_registra,
  has_function_privilege('authenticated', 'public.registrar_semana(date)',
                         'execute') as usuario_registra,
  has_table_privilege('authenticated', 'public.user_historico_semanal',
                      'insert') and exists (
    select 1 from pg_policies where tablename = 'user_historico_semanal'
       and cmd in ('INSERT', 'UPDATE', 'DELETE', 'ALL'))
    as usuario_grava,
  (select relrowsecurity from pg_class
    where oid = 'public.user_historico_semanal'::regclass) as rls_ligado;

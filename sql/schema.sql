-- ===========================================================================
-- Caminho da Maestria: schema "public" exportado em 23/11/2026 17:15
-- Gerado por sql/exportar_schema.sql (nao edite a mao: exporte de novo)
-- ===========================================================================

create extension if not exists "uuid-ossp" with schema extensions;

-- ---------------------------------------------------------------- funcoes
CREATE OR REPLACE FUNCTION public.rls_auto_enable()
 RETURNS event_trigger
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE
  cmd record;
  tbl name;
BEGIN
  FOR cmd IN
    SELECT *
    FROM pg_event_trigger_ddl_commands()
    WHERE command_tag IN ('CREATE TABLE', 'CREATE TABLE AS', 'SELECT INTO')
      AND object_type IN ('table','partitioned table')
  LOOP
     IF cmd.schema_name IS NOT NULL AND cmd.schema_name IN ('public') AND cmd.schema_name NOT IN ('pg_catalog','information_schema') AND cmd.schema_name NOT LIKE 'pg_toast%' AND cmd.schema_name NOT LIKE 'pg_temp%' THEN
      BEGIN
        SELECT c.relname INTO tbl FROM pg_catalog.pg_class c WHERE c.oid = cmd.objid;
        EXECUTE format('alter table if exists %I.%I enable row level security', cmd.schema_name, tbl);
        RAISE LOG 'rls_auto_enable: enabled RLS on %', cmd.object_identity;
      EXCEPTION
        WHEN OTHERS THEN
          RAISE LOG 'rls_auto_enable: failed to enable RLS on %', cmd.object_identity;
      END;
     ELSE
        RAISE LOG 'rls_auto_enable: skip % (either system schema or not in enforced list: %.)', cmd.object_identity, cmd.schema_name;
     END IF;
  END LOOP;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.zerar_semanais()
 RETURNS integer
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO 'public', 'pg_temp'
AS $function$
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
  -- monta o SET so com as colunas que existem de fato no banco
  foreach col in array colunas loop
    select exists (
      select 1 from information_schema.columns
       where table_schema = 'public'
         and table_name = 'user_semanais'
         and column_name = col
    ) into existe;

    if existe then
      -- array_append (e NAO o operador ||): com um literal solto o
      -- Postgres tenta converter para text[] e da "malformed array
      -- literal"
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

  -- o UPDATE precisa de um WHERE (o Postgres exige: sem ele da
  -- "UPDATE requires a WHERE clause"). O filtro abaixo pega TODAS as
  -- linhas (e ainda deixa o log com o numero de linhas afetadas).
  select exists (
    select 1 from information_schema.columns
     where table_schema = 'public'
       and table_name = 'user_semanais'
       and column_name = 'id'
  ) into tem_id;

  -- o WHERE e montado para pegar SO as linhas que tem alguma marcacao
  -- (as que ja estao em false nao sao tocadas) e o numero devolvido e
  -- quantas linhas tinham marcacao
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
$function$
;

-- salvamento atomico da conta (ver sql/salvar_conta.sql)
create or replace function public.salvar_conta(dados jsonb)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
  uid       uuid := auth.uid();
  tabelas   text[] := array['user_characters', 'user_pecas_void',
                            'user_acessorios_titulo', 'user_semanais'];
  chaves    text[] := array['personagens', 'pecas_void',
                            'acessorios_titulo', 'semanais'];
  tabela    text;
  linha     jsonb;
  colunas   text;
  inseridas text;
  afetadas  integer;
  total     integer;
  contagem  jsonb := '{}'::jsonb;
begin
  if uid is null then
    raise exception 'salvar_conta: e preciso estar logado'
      using errcode = '42501';
  end if;
  if jsonb_typeof(dados) is distinct from 'object' then
    raise exception 'salvar_conta: "dados" precisa ser um objeto JSON'
      using errcode = '22023';
  end if;

  for i in 1 .. array_length(tabelas, 1) loop
    tabela := tabelas[i];
    total := 0;

    -- colunas que um update pode mexer (as de controle ficam de fora)
    select string_agg(quote_ident(c.column_name), ', '
                      order by c.ordinal_position)
      into colunas
      from information_schema.columns c
     where c.table_schema = 'public' and c.table_name = tabela
       and c.column_name not in ('id', 'user_id', 'character_id',
                                 'updated_at', 'created_at');

    for linha in
      select value from jsonb_array_elements(coalesce(dados -> chaves[i],
                                                      '[]'::jsonb))
    loop
      if jsonb_typeof(linha) is distinct from 'object' then
        raise exception 'salvar_conta: linha invalida em %', chaves[i]
          using errcode = '22023';
      end if;

      if tabela = 'user_characters' then
        linha := linha || jsonb_build_object('user_id', uid);
      elsif not (linha ? 'character_id') or linha ->> 'character_id' = '' then
        -- linha filha sem character_id: acha o personagem pelo nome
        -- (os personagens ja foram gravados acima, na mesma transacao)
        linha := linha || jsonb_build_object('character_id',
          (select uc.id from user_characters uc
            where uc.user_id = uid
              and uc.character_name = linha ->> '_nome'));
        if linha ->> 'character_id' is null then
          raise exception 'salvar_conta: personagem "%" nao encontrado (%)',
            linha ->> '_nome', chaves[i]
            using errcode = '23503';
        end if;
      end if;

      if coalesce(linha ->> 'id', '') <> '' then
        -- UPDATE: as chaves que vieram trocam o valor; o resto continua
        -- igual (jsonb_populate_record parte da propria linha `t`)
        execute format(
          'update public.%1$I t set (%2$s, updated_at) = '
          '(select %2$s, now() from jsonb_populate_record(t, $1) r) '
          'where t.id = ($1 ->> ''id'')::uuid',
          tabela, colunas)
          using linha;
        get diagnostics afetadas = row_count;
        if afetadas = 0 then
          raise exception 'salvar_conta: linha % de % nao encontrada '
                          '(ou e de outra conta)', linha ->> 'id', tabela
            using errcode = '42501';
        end if;
      else
        -- INSERT: so as chaves que vieram e que sao colunas de verdade
        select string_agg(quote_ident(c.column_name), ', ')
          into inseridas
          from information_schema.columns c
         where c.table_schema = 'public' and c.table_name = tabela
           and linha ? c.column_name
           and c.column_name not in ('id', 'updated_at', 'created_at');
        execute format(
          'insert into public.%1$I (%2$s) '
          'select %2$s from jsonb_populate_record(null::public.%1$I, $1)',
          tabela, inseridas)
          using linha;
      end if;
      total := total + 1;
    end loop;

    contagem := contagem || jsonb_build_object(chaves[i], total);
  end loop;

  return contagem;
end;
$$;

-- ---------------------------------------------------------------- tabelas
create table if not exists public.profiles (
  id uuid not null,
  username text not null,
  full_name text,
  avatar_url text,
  role text default 'member'::text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  constraint profiles_username_key UNIQUE (username),
  constraint profiles_pkey PRIMARY KEY (id)
);
alter table public.profiles enable row level security;

create table if not exists public.user_acessorios_titulo (
  id uuid default uuid_generate_v4() not null,
  character_id uuid not null,
  anel text,
  brinco text,
  piercing text,
  tornozeleira text,
  titulo text,
  colar text default '',
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  constraint user_acessorios_titulo_pkey PRIMARY KEY (id)
);
alter table public.user_acessorios_titulo enable row level security;

create table if not exists public.user_characters (
  id uuid default uuid_generate_v4() not null,
  user_id uuid not null,
  character_name text not null,
  poder bigint,
  torre_das_ilusoes text,
  vazio_uni integer,
  vazio_apo integer,
  libertacao text,
  nucleo text,
  nucleos_epicos text,
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  nucleos_dimensionais integer default 0,
  libertacao_nucleos integer default 0,
  libertacao_epicos integer default 0,
  fragmento_vazio_disperso integer default 0,
  nivel_chaser bigint default 0,
  colecao_cartas bigint default 0,
  ataque bigint default 0,
  ataque_especial bigint default 0,
  critico numeric(8, 2) default 0,
  dano_critico numeric(8, 2) default 0,
  dano_costas numeric(8, 2) default 0,
  constraint user_characters_user_id_character_name_key UNIQUE (user_id, character_name),
  constraint user_characters_pkey PRIMARY KEY (id)
);
alter table public.user_characters enable row level security;

create table if not exists public.user_pecas_void (
  id uuid default uuid_generate_v4() not null,
  character_id uuid not null,
  arma boolean default false,
  luvas boolean default false,
  cota boolean default false,
  botas boolean default false,
  capa boolean default false,
  calca boolean default false,
  elmo boolean default false,
  escudos boolean default false,
  asas boolean default false,
  facas boolean default false,
  mascara boolean default false,
  diadema boolean default false,
  cartas_arma text default '',
  cartas_luvas text default '',
  cartas_cota text default '',
  cartas_botas text default '',
  cartas_capa text default '',
  cartas_calca text default '',
  cartas_elmo text default '',
  pedra_arma text default '',
  pedra_luvas text default '',
  pedra_cota text default '',
  pedra_botas text default '',
  pedra_capa text default '',
  pedra_calca text default '',
  pedra_elmo text default '',
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  constraint user_pecas_void_pkey PRIMARY KEY (id)
);
alter table public.user_pecas_void enable row level security;

create table if not exists public.user_profiles (
  id uuid not null,
  username text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  missao_rapida boolean default false,
  missao_rapida_personagem text,
  nick text,
  avatar text,
  constraint user_profiles_username_key UNIQUE (username),
  constraint user_profiles_pkey PRIMARY KEY (id)
);
alter table public.user_profiles enable row level security;

create table if not exists public.user_semanais (
  id uuid default uuid_generate_v4() not null,
  character_id uuid not null,
  fornalha_infernal boolean default false,
  altar_da_runha boolean default false,
  torre_das_ilusoes_semanal boolean default false,
  void_123 boolean default false,
  void_4 boolean default false,
  caminho_abissal boolean default false,
  terra_do_julgamento boolean default false,
  void123_andar text default '',
  void4_andar text default '',
  updated_at timestamp with time zone default timezone('utc'::text, now()) not null,
  constraint user_semanais_pkey PRIMARY KEY (id)
);
alter table public.user_semanais enable row level security;

-- ---------------------------------------------------- chaves estrangeiras
alter table public.profiles
  add constraint profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
alter table public.user_acessorios_titulo
  add constraint user_acessorios_titulo_character_id_fkey FOREIGN KEY (character_id) REFERENCES user_characters(id) ON DELETE CASCADE;
alter table public.user_characters
  add constraint user_characters_user_id_fkey FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE;
alter table public.user_pecas_void
  add constraint user_pecas_void_character_id_fkey FOREIGN KEY (character_id) REFERENCES user_characters(id) ON DELETE CASCADE;
alter table public.user_profiles
  add constraint user_profiles_id_fkey FOREIGN KEY (id) REFERENCES auth.users(id) ON DELETE CASCADE;
alter table public.user_semanais
  add constraint user_semanais_character_id_fkey FOREIGN KEY (character_id) REFERENCES user_characters(id) ON DELETE CASCADE;

-- ---------------------------------------------------------------- indices
-- (nenhum)

-- ------------------------------------------- permissoes das funcoes (RPC)
-- (secao acrescentada a mao em 23/11, conferida com has_function_privilege;
--  a proxima exportacao ja gera esta secao sozinha)
revoke execute on function public.zerar_semanais() from public, anon, authenticated;
grant execute on function public.zerar_semanais() to postgres;
grant execute on function public.zerar_semanais() to service_role;
revoke execute on function public.salvar_conta(jsonb) from public, anon;
grant execute on function public.salvar_conta(jsonb) to authenticated;

-- ------------------------------------------------------- policies (RLS)
create policy "Profiles are viewable by owner" on public.profiles
  as permissive for select to authenticated
  using ((auth.uid() = id));

create policy "Users can insert own profile" on public.profiles
  as permissive for insert to public
  with check ((auth.uid() = id));

create policy "Users can update own profile" on public.profiles
  as permissive for update to public
  using ((auth.uid() = id));

create policy "Users can delete own acessorios_titulo" on public.user_acessorios_titulo
  as permissive for delete to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_acessorios_titulo.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can insert own acessorios_titulo" on public.user_acessorios_titulo
  as permissive for insert to public
  with check ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_acessorios_titulo.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can update own acessorios_titulo" on public.user_acessorios_titulo
  as permissive for update to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_acessorios_titulo.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can view own acessorios_titulo" on public.user_acessorios_titulo
  as permissive for select to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_acessorios_titulo.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can delete own characters" on public.user_characters
  as permissive for delete to public
  using ((auth.uid() = user_id));

create policy "Users can insert own characters" on public.user_characters
  as permissive for insert to public
  with check ((auth.uid() = user_id));

create policy "Users can update own characters" on public.user_characters
  as permissive for update to public
  using ((auth.uid() = user_id));

create policy "Users can view own characters" on public.user_characters
  as permissive for select to public
  using ((auth.uid() = user_id));

create policy "Users can delete own pecas_void" on public.user_pecas_void
  as permissive for delete to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_pecas_void.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can insert own pecas_void" on public.user_pecas_void
  as permissive for insert to public
  with check ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_pecas_void.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can update own pecas_void" on public.user_pecas_void
  as permissive for update to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_pecas_void.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can view own pecas_void" on public.user_pecas_void
  as permissive for select to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_pecas_void.character_id) AND (uc.user_id = auth.uid())))));

create policy "Profiles are viewable by owner" on public.user_profiles
  as permissive for select to public
  using ((auth.uid() = id));

create policy "Users can insert own profile" on public.user_profiles
  as permissive for insert to public
  with check ((auth.uid() = id));

create policy "Users can update own profile" on public.user_profiles
  as permissive for update to public
  using ((auth.uid() = id));

create policy "Users can delete own semanais" on public.user_semanais
  as permissive for delete to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_semanais.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can insert own semanais" on public.user_semanais
  as permissive for insert to public
  with check ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_semanais.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can update own semanais" on public.user_semanais
  as permissive for update to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_semanais.character_id) AND (uc.user_id = auth.uid())))));

create policy "Users can view own semanais" on public.user_semanais
  as permissive for select to public
  using ((EXISTS ( SELECT 1
   FROM user_characters uc
  WHERE ((uc.id = user_semanais.character_id) AND (uc.user_id = auth.uid())))));

-- --------------------------------------------------------------- triggers
-- (nenhum)

-- ============================================================
-- historico semanal (pagina "Evolucao"; ver sql/historico_semanal.sql)
-- redefine a zerar_semanais() para tirar a foto antes de zerar
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

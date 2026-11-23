-- ===========================================================================
-- EXPORTA o schema "public" (tabelas, RLS, policies, funcoes e triggers)
-- como um script SQL, para versionar no git (sql/schema.sql).
--
-- Como usar:
--   1. Supabase > SQL Editor > New query > cole este arquivo > Run
--   2. o resultado e UMA celula (coluna "script"): copie o conteudo
--      inteiro e salve em  sql/schema.sql
--
-- So LE o catalogo do Postgres: nao altera nada no banco.
-- ===========================================================================

with
tabelas as (
  select c.oid, c.relname, c.relrowsecurity, c.relforcerowsecurity
    from pg_class c
    join pg_namespace n on n.oid = c.relnamespace
   where n.nspname = 'public' and c.relkind = 'r'
),
colunas as (
  select t.relname,
         string_agg(
           format('  %I %s%s%s', a.attname,
                  format_type(a.atttypid, a.atttypmod),
                  case when d.adbin is not null
                       then ' default ' || pg_get_expr(d.adbin, d.adrelid) else '' end,
                  case when a.attnotnull then ' not null' else '' end),
           E',\n' order by a.attnum) as cols
    from tabelas t
    join pg_attribute a on a.attrelid = t.oid and a.attnum > 0 and not a.attisdropped
    left join pg_attrdef d on d.adrelid = t.oid and d.adnum = a.attnum
   group by t.relname
),
restricoes as (
  select t.relname,
         string_agg(format('  constraint %I %s', co.conname, pg_get_constraintdef(co.oid)),
                    E',\n' order by co.contype desc, co.conname) as cons
    from tabelas t
    join pg_constraint co on co.conrelid = t.oid and co.contype <> 'f'
   group by t.relname
),
-- as chaves estrangeiras vao DEPOIS de todas as tabelas (assim a ordem
-- alfabetica nao quebra: as filhas referenciam a user_characters)
chaves_estrangeiras as (
  select string_agg(format(E'alter table public.%I\n  add constraint %I %s;',
                           t.relname, co.conname, pg_get_constraintdef(co.oid)),
                    E'\n' order by t.relname, co.conname) as txt
    from tabelas t
    join pg_constraint co on co.conrelid = t.oid and co.contype = 'f'
),
ddl_tabelas as (
  select string_agg(
           format(E'create table if not exists public.%I (\n%s%s\n);\n',
                  t.relname, c.cols,
                  coalesce(E',\n' || r.cons, ''))
           || case when t.relrowsecurity
                   then format(E'alter table public.%I enable row level security;\n', t.relname)
                   else format(E'-- ATENCAO: RLS DESLIGADO em public.%I\n', t.relname) end
           || case when t.relforcerowsecurity
                   then format(E'alter table public.%I force row level security;\n', t.relname)
                   else '' end,
           E'\n' order by t.relname) as txt
    from tabelas t
    join colunas c using (relname)
    left join restricoes r using (relname)
),
indices as (
  select string_agg(i.indexdef || ';', E'\n' order by i.tablename, i.indexname) as txt
    from pg_indexes i
   where i.schemaname = 'public'
     and not exists (select 1 from pg_constraint co
                      where co.conname = i.indexname)
),
politicas as (
  select string_agg(
           format(E'create policy %I on public.%I\n  as %s for %s to %s%s%s;',
                  p.policyname, p.tablename, lower(p.permissive), lower(p.cmd),
                  array_to_string(p.roles, ', '),
                  case when p.qual is not null then E'\n  using (' || p.qual || ')' else '' end,
                  case when p.with_check is not null then E'\n  with check (' || p.with_check || ')' else '' end),
           E'\n\n' order by p.tablename, p.policyname) as txt
    from pg_policies p
   where p.schemaname = 'public'
),
funcoes as (
  select string_agg(pg_get_functiondef(f.oid) || ';', E'\n\n' order by f.proname) as txt
    from pg_proc f
    join pg_namespace n on n.oid = f.pronamespace
   where n.nspname = 'public' and f.prokind = 'f'
     and not exists (select 1 from pg_depend d
                      where d.objid = f.oid and d.deptype = 'e')   -- sem as de extensoes
),
-- quem pode EXECUTAR cada funcao (importante nas SECURITY DEFINER: no
-- Supabase, anon e authenticated ganham EXECUTE por padrao)
permissoes_funcoes as (
  select string_agg(
           format(E'revoke execute on function public.%I(%s) from public, anon, authenticated;\n',
                  f.proname, pg_get_function_identity_arguments(f.oid))
           || coalesce((
                select string_agg(format('grant execute on function public.%I(%s) to %I;',
                                         f.proname, pg_get_function_identity_arguments(f.oid),
                                         r.rolname), E'\n' order by r.rolname)
                  from aclexplode(f.proacl) a
                  join pg_roles r on r.oid = a.grantee
                 where a.privilege_type = 'EXECUTE'), '-- (ninguem alem do dono)'),
           E'\n\n' order by f.proname) as txt
    from pg_proc f
    join pg_namespace n on n.oid = f.pronamespace
   where n.nspname = 'public' and f.prokind = 'f'
     and f.prorettype <> 'event_trigger'::regtype
     and not exists (select 1 from pg_depend d
                      where d.objid = f.oid and d.deptype = 'e')
),
gatilhos as (
  select string_agg(pg_get_triggerdef(tg.oid) || ';', E'\n' order by tg.tgname) as txt
    from pg_trigger tg
    join pg_class c on c.oid = tg.tgrelid
    join pg_namespace n on n.oid = c.relnamespace
   where not tg.tgisinternal
     and (n.nspname = 'public'
          or (n.nspname = 'auth' and c.relname = 'users'))  -- ex.: cria o perfil no cadastro
)
select
  '-- ===========================================================================' || E'\n' ||
  '-- Caminho da Maestria: schema "public" exportado em ' || to_char(now(), 'DD/MM/YYYY HH24:MI') || E'\n' ||
  '-- Gerado por sql/exportar_schema.sql (nao edite a mao: exporte de novo)' || E'\n' ||
  '-- ===========================================================================' || E'\n\n' ||
  E'create extension if not exists "uuid-ossp" with schema extensions;\n\n' ||
  E'-- ---------------------------------------------------------------- funcoes\n' ||
  coalesce((select txt from funcoes), '-- (nenhuma)') || E'\n\n' ||
  E'-- ---------------------------------------------------------------- tabelas\n' ||
  coalesce((select txt from ddl_tabelas), '-- (nenhuma)') || E'\n' ||
  E'-- ---------------------------------------------------- chaves estrangeiras\n' ||
  coalesce((select txt from chaves_estrangeiras), '-- (nenhuma)') || E'\n\n' ||
  E'-- ---------------------------------------------------------------- indices\n' ||
  coalesce((select txt from indices), '-- (nenhum)') || E'\n\n' ||
  E'-- ------------------------------------------- permissoes das funcoes (RPC)\n' ||
  coalesce((select txt from permissoes_funcoes), '-- (nenhuma)') || E'\n\n' ||
  E'-- ------------------------------------------------------- policies (RLS)\n' ||
  coalesce((select txt from politicas), '-- (nenhuma)') || E'\n\n' ||
  E'-- --------------------------------------------------------------- triggers\n' ||
  coalesce((select txt from gatilhos), '-- (nenhum)') || E'\n'
  as script;

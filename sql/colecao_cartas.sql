-- ===========================================================================
-- Item 15.4 (24/11): nivel da colecao de cartas (0 a 2500)
--
-- Um valor POR CONTA, como o Level Chaser: fica em
-- user_characters.colecao_cartas e o app grava o mesmo valor em todas as
-- linhas da conta. Entra na foto semanal (user_historico_semanal) e na
-- pagina "Evolucao semanal".
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem as colunas o app continua funcionando, mas a colecao nao e gravada.
-- ===========================================================================

-- 1) a colecao da conta
alter table public.user_characters
  add column if not exists colecao_cartas bigint default 0;

-- 2) a coluna na foto semanal
alter table public.user_historico_semanal
  add column if not exists colecao_cartas bigint;

-- 3) a foto da semana passa a gravar a colecao (o resto e igual ao
--    sql/historico_semanal.sql)
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

-- PostgREST: recarrega as colunas para o app enxergar as novas
notify pgrst, 'reload schema';

-- conferencia: deve listar as 2 colunas
select table_name, column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and column_name = 'colecao_cartas'
 order by table_name;

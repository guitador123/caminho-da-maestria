-- ===========================================================================
-- ZERAR AS MISSOES SEMANAIS DE TODAS AS CONTAS - toda quarta as 03h
--
-- Usa o pg_cron (o agendador do proprio Postgres, que roda no servidor do
-- Supabase). Nao precisa de maquina ligada nem de chave service_role:
-- a funcao roda com os poderes do dono dela (security definer).
--
-- COMO USAR: abra o SQL Editor do Supabase, cole este arquivo inteiro e
-- clique em "Run". E idempotente: pode rodar de novo sem duplicar nada.
--
-- Este arquivo SÓ CRIA a funcao e o agendamento (nenhuma query de
-- conferencia, para nao dar erro e rollback). As queries de conferencia
-- estao em `sql/zerar_semanais_verificar.sql`.
--
-- O QUE ELE FAZ
--   Marca como "Falso" as 7 colunas de missao semanal da tabela
--   public.user_semanais, para TODOS os usuarios:
--
--     fornalha_infernal | altar_da_runha | torre_das_ilusoes_semanal |
--     void_123 | void_4 | caminho_abissal | terra_do_julgamento
--
--   (a funcao ve sozinha quais colunas existem no banco e mexe so nelas)
--
-- HORARIO
--   Toda quarta-feira as 03h de Brasilia. O Brasil nao usa horario de
--   verao desde 2019, entao sao sempre 03h (UTC-3).
--   O script calcula a hora no fuso do SERVIDOR (no Supabase e UTC, ou
--   seja 03h de Brasilia = 06h UTC) e cria a tarefa ja com esse valor.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- 1) A funcao que zera as missoes
-- ---------------------------------------------------------------------------
create or replace function public.zerar_semanais()
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
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
$$;

comment on function public.zerar_semanais() is
  'Zera as missoes semanais de todas as contas (usado pelo pg_cron).';

-- so o dono do banco (o pg_cron) e o service_role podem chamar.
-- ATENCAO: no Supabase o `from public` NAO basta: o Supabase da EXECUTE
-- direto para anon e authenticated em toda funcao nova do schema public
-- (e a funcao e SECURITY DEFINER: ignoraria o RLS e zeraria a guilda toda).
revoke execute on function public.zerar_semanais() from public, anon, authenticated;
grant  execute on function public.zerar_semanais() to postgres, service_role;


-- ---------------------------------------------------------------------------
-- 2) O agendamento (pg_cron)
-- ---------------------------------------------------------------------------
-- Se o pg_cron ainda nao estiver habilitado neste projeto:
--   create extension if not exists pg_cron with schema extensions;
-- (no Supabase ele ja vem habilitado; se der erro, ative pelo painel:
--  Database > Extensions > pg_cron)

do $$
declare
  fuso_servidor text;
  expressao text;
  hora integer;
  dia integer;   -- 0 = domingo ... 6 = sabado (igual ao cron)
  novo_id bigint;
begin
  -- fuso do servidor (no Supabase e UTC)
  fuso_servidor := current_setting('TimeZone');

  -- 03h de Brasilia (UTC-3, sem horario de verao desde 2019) convertido
  -- para o fuso do servidor. A referencia e uma quarta-feira, entao o dia
  -- da semana tambem sai certo (o servidor pode estar num fuso que muda
  -- o dia).
  select extract(hour from t)::int, extract(dow from t)::int
    into hora, dia
    from (
      select (timestamp '2026-01-07 03:00' at time zone 'America/Sao_Paulo')
               at time zone fuso_servidor as t
    ) as s;

  expressao := '0 ' || lpad(hora::text, 2, '0') || ' * * ' || dia::text;

  -- remove a versao antiga, se existir (se nao existir, segue em frente)
  begin
    perform cron.unschedule('zerar-missoes-semanais');
  exception when others then
    null;   -- ainda nao tinha tarefa com esse nome
  end;

  -- cria a tarefa. O pg_cron antigo (sem a coluna timezone) so tem
  -- cron.schedule(schedule, command); o novo tem o nome da tarefa.
  begin
    perform cron.schedule(
      'zerar-missoes-semanais',
      expressao,
      'select public.zerar_semanais();'
    );
  exception when others then
    perform cron.schedule(expressao, 'select public.zerar_semanais();');
    select max(jobid) into novo_id from cron.job;
    if novo_id is not null then
      update cron.job
         set jobname = 'zerar-missoes-semanais'
       where jobid = novo_id;
    end if;
  end;

  raise notice 'Agendado: zerar-missoes-semanais | cron=% | servidor em % | 03h de Brasilia = %h no servidor',
    expressao, fuso_servidor, hora;
end;
$$;


-- ===========================================================================
-- PRONTO. Para conferir, rode o arquivo `sql/zerar_semanais_verificar.sql`
-- (ou o trecho "Como conferir" do LEIA-ME-zerar-semanal.txt).
-- ===========================================================================

-- ===========================================================================
-- Correcoes de permissao (revisao do schema de 23/11/2026)
--
-- Rode no Supabase > SQL Editor. Rode o bloco 1 primeiro e veja o
-- resultado; depois rode o bloco 2 (a correcao) e o bloco 1 de novo.
-- ===========================================================================


-- ---------------------------------------------------------------------------
-- 1) VERIFICAR (so le): quem pode chamar a zerar_semanais()?
--
-- A funcao e SECURITY DEFINER: ela roda com os poderes do dono e IGNORA o
-- RLS. O `revoke ... from public` do sql/zerar_semanais_pg_cron.sql NAO
-- basta no Supabase, porque o Supabase da EXECUTE direto para os papeis
-- `anon` e `authenticated` em toda funcao nova do schema public.
-- Se aparecer `true` para anon ou authenticated, QUALQUER pessoa com a
-- chave publica (que vai dentro do app) pode zerar as missoes semanais
-- de TODA a guilda pelo endpoint /rest/v1/rpc/zerar_semanais.
-- ---------------------------------------------------------------------------
select papel,
       has_function_privilege(papel, 'public.zerar_semanais()', 'execute')
         as pode_executar
  from unnest(array['anon', 'authenticated', 'service_role', 'postgres'])
         as papel;


-- ---------------------------------------------------------------------------
-- 2) CORRIGIR
-- ---------------------------------------------------------------------------

-- 2a) so o dono (postgres, que e quem o pg_cron usa) e o service_role
--     (o script zerar_semanais_semanal.py) podem chamar a limpeza
revoke execute on function public.zerar_semanais() from public, anon, authenticated;
grant  execute on function public.zerar_semanais() to postgres, service_role;

-- 2b) a tabela antiga `public.profiles` (o app usa a `user_profiles`)
--     tinha select liberado para TODO MUNDO, inclusive sem login.
--     Hoje ela esta vazia; trocamos para "so o dono le".
drop policy if exists "Profiles are viewable by everyone" on public.profiles;
create policy "Profiles are viewable by owner" on public.profiles
  as permissive for select to authenticated
  using (auth.uid() = id);

-- (opcional) se tiver certeza de que nada usa a `profiles`, pode apagar:
--   select count(*) from public.profiles;   -- confira que da 0
--   drop table public.profiles;

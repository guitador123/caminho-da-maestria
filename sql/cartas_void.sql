-- ===========================================================================
-- Item 15.3 (24/11): as 4 cartas de cada equipamento do Void
--
-- Uma coluna de texto por equipamento em user_pecas_void, com os 4 slots
-- separados por "|" (a posicao conta; slot vazio fica vazio):
--   cartas_cota = 'Ataque +555|Ataque +530||Outra'
-- As opcoes e as cores ficam no app (src/dados_app.py, CARTAS_VOID).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem as colunas o app continua funcionando, mas as cartas nao sao gravadas.
-- ===========================================================================

alter table public.user_pecas_void
  add column if not exists cartas_arma  text default '',
  add column if not exists cartas_luvas text default '',
  add column if not exists cartas_cota  text default '',
  add column if not exists cartas_botas text default '',
  add column if not exists cartas_capa  text default '',
  add column if not exists cartas_calca text default '',
  add column if not exists cartas_elmo  text default '';

-- PostgREST: recarrega as colunas para o app enxergar as novas
notify pgrst, 'reload schema';

-- conferencia: deve listar as 7 colunas
select column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and table_name = 'user_pecas_void'
   and column_name like 'cartas_%'
 order by column_name;

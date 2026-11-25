-- ===========================================================================
-- Item 16 (24/11): a pedra de cada equipamento do Void
--
-- Uma coluna de texto por equipamento em user_pecas_void com o nivel
-- (+0 a +18) e o status da pedra, separados por "|":
--   pedra_arma = '18|10% Dano Crítico'      (vazio = pedra nao informada)
-- As opcoes de status ficam no app (src/dados_app.py, PEDRAS_VOID).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem as colunas o app continua funcionando, mas as pedras nao sao gravadas.
-- ===========================================================================

alter table public.user_pecas_void
  add column if not exists pedra_arma  text default '',
  add column if not exists pedra_luvas text default '',
  add column if not exists pedra_cota  text default '',
  add column if not exists pedra_botas text default '',
  add column if not exists pedra_capa  text default '',
  add column if not exists pedra_calca text default '',
  add column if not exists pedra_elmo  text default '';

-- PostgREST: recarrega as colunas para o app enxergar as novas
notify pgrst, 'reload schema';

-- conferencia: deve listar as 7 colunas
select column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and table_name = 'user_pecas_void'
   and column_name like 'pedra_%'
 order by column_name;

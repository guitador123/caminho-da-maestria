-- ===========================================================================
-- Item 15.5 (24/11): o Colar nos acessorios de cada personagem
--
-- Coluna de texto em user_acessorios_titulo, como Anel/Brinco/Tornozeleira.
-- As opcoes e as cores ficam no app (src/opcoes.py e card_personagem.py).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem a coluna o app continua funcionando, mas o colar nao e gravado.
-- ===========================================================================

alter table public.user_acessorios_titulo
  add column if not exists colar text default '';

-- PostgREST: recarrega as colunas para o app enxergar a nova
notify pgrst, 'reload schema';

-- conferencia: deve listar a coluna
select column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and table_name = 'user_acessorios_titulo'
   and column_name = 'colar';

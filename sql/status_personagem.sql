-- ===========================================================================
-- Item 15.1 (24/11): status de cada personagem
--
--   ataque            -> Ataque            (inteiro)
--   ataque_especial   -> Ataque Especial   (inteiro)
--   critico           -> % de acerto critico   (ate 2 casas decimais)
--   dano_critico      -> % de dano critico     (ate 2 casas decimais)
--   dano_costas       -> % de dano nas costas  (ate 2 casas decimais)
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem as colunas o app continua funcionando, mas os status nao sao gravados.
-- A funcao salvar_conta grava qualquer coluna da tabela: nao precisa mudar.
-- ===========================================================================

alter table public.user_characters
  add column if not exists ataque          bigint        default 0,
  add column if not exists ataque_especial bigint        default 0,
  add column if not exists critico         numeric(8, 2) default 0,
  add column if not exists dano_critico    numeric(8, 2) default 0,
  add column if not exists dano_costas     numeric(8, 2) default 0;

-- PostgREST: recarrega as colunas para o app enxergar as novas
notify pgrst, 'reload schema';

-- conferencia: deve listar as 5 colunas
select column_name, data_type, numeric_scale
  from information_schema.columns
 where table_schema = 'public' and table_name = 'user_characters'
   and column_name in ('ataque', 'ataque_especial', 'critico',
                       'dano_critico', 'dano_costas')
 order by column_name;

-- ===========================================================================
-- Item 17 (26/11): o andar do Void marcado pela Missao Rapida
--
-- Marcar "Void (1, 2 e 3)" ou "Void 4" na Missao Rapida pergunta 1F/2F/3F
-- e soma no Void Unificado / Apocalipse do personagem. Para DESMARCAR
-- desfazer a soma, o app guarda o andar junto com a semana:
--   void123_andar = '3F|2026-11-25'   (vazio = nada a desfazer)
-- A marca so vale na semana dela: depois do reset de quarta ela e ignorada
-- (por isso a funcao zerar_semanais NAO precisa mudar).
--
-- Rode no SQL Editor do Supabase (pode rodar de novo sem problema).
-- Sem as colunas o app continua somando, mas desmarcar nao desfaz a soma.
-- ===========================================================================

alter table public.user_semanais
  add column if not exists void123_andar text default '',
  add column if not exists void4_andar   text default '';

-- PostgREST: recarrega as colunas para o app enxergar as novas
notify pgrst, 'reload schema';

-- conferencia: deve listar as 2 colunas
select column_name, data_type
  from information_schema.columns
 where table_schema = 'public' and table_name = 'user_semanais'
   and column_name like 'void%_andar'
 order by column_name;

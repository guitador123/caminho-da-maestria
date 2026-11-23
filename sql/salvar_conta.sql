-- ============================================================
--  Caminho da Maestria - salvamento ATOMICO da conta
--
--  O app chama:  rpc("salvar_conta", {"dados": {...}})
--    dados = {
--      "personagens":       [ {id?, character_name, poder, ...}, ... ],
--      "pecas_void":        [ {id?, character_id? | _nome, arma, ...}, ... ],
--      "acessorios_titulo": [ ... ],
--      "semanais":          [ ... ]
--    }
--  So vem o que MUDOU desde o ultimo salvamento.
--
--  Tudo roda numa transacao so: se qualquer linha falhar, NADA e
--  gravado (antes, uma falha no meio deixava o banco pela metade).
--
--  Seguranca:
--    - SECURITY INVOKER: roda como o proprio usuario, entao o RLS das
--      tabelas continua valendo (ninguem grava na conta de outro).
--    - id, user_id e character_id NUNCA sao alterados num update (nao da
--      para "mover" uma linha para outra conta ou personagem).
--    - personagem novo sempre nasce com user_id = auth.uid().
--    - update que nao acha a linha (inexistente ou de outra conta)
--      cancela tudo, em vez de passar em silencio.
--
--  Rodar no SQL Editor do Supabase (pode rodar de novo sem problema).
-- ============================================================

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

-- so quem esta logado pode chamar (o RLS faz o resto)
revoke execute on function public.salvar_conta(jsonb) from public, anon;
grant execute on function public.salvar_conta(jsonb) to authenticated;

-- PostgREST: recarrega a lista de funcoes para o app enxergar a nova
notify pgrst, 'reload schema';

-- conferencia: deve mostrar anon = false e authenticated = true
select has_function_privilege('anon', 'public.salvar_conta(jsonb)', 'execute')
         as anon,
       has_function_privilege('authenticated', 'public.salvar_conta(jsonb)',
                              'execute') as authenticated;

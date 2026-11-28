// =============================================================================
// Caminho da Maestria - o ranking da guilda no Discord (Edge Function)
//
// Monta o ranking (as mesmas regras da guia Ranking do app) e EDITA sempre
// a mesma mensagem num canal do Discord, via webhook. Na 1a vez (ou se a
// mensagem for apagada) posta uma nova e guarda o ID.
//
// Chamada pelo agendador do banco a cada 5 minutos (sql/discord_agendar.sql)
// com o cabecalho "x-segredo". Sem o segredo certo, nao faz nada.
//
// Segredos (Supabase > Edge Functions > Secrets):
//   DISCORD_WEBHOOK_URL  a URL do webhook do canal (NUNCA vai para o app)
//   SEGREDO_RANKING      um texto aleatorio (o mesmo do discord_agendar.sql)
// SUPABASE_URL e SUPABASE_SERVICE_ROLE_KEY o Supabase ja fornece sozinho.
//
// Regras (iguais as do app, src/ranking.py):
//   - personagem: o maior Ataque Total; empate: a Soma (Ataque + Especial)
//   - podios: empate pelo Ataque Total medio
//   - "mais fortes" = de quantos personagens a conta e a 1a
//   - dungeons: sempre a semana atual
// =============================================================================

export const PERSONAGENS = [
  "Elesis", "Lire", "Arme", "Lass", "Ryan", "Ronan", "Amy", "Jin",
  "Sieghart", "Mari", "Dio", "Zero", "Rey", "Lupus", "Lin", "Azin", "Holy",
  "Edel", "Veigas", "Decane", "Ai", "Kallia", "Uno", "Iris", "Ereb",
];

export const CATEGORIAS = [
  ["fortes", "💪 Mais personagens em 1º"],
  ["level", "⭐ Level Chaser"],
  ["colecao", "🃏 Coleção de cartas"],
  ["dungeons", "⚔️ Dungeons da semana"],
  ["ataque", "⚡ Ataque Total médio"],
];

const MEDALHAS = ["🥇", "🥈", "🥉"];
const ROXO = 0x8b5cf6;
const DOURADO = 0xf5c451;

const num = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? Math.trunc(n) : 0;
};
export const milhar = (v) =>
  String(Math.max(0, num(v))).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
export const somaNoMilhar = (ataque, especial) => {
  const milhares = Math.floor((Math.max(0, num(ataque)) + Math.max(0, num(especial))) / 1000);
  return `${Math.floor(milhares / 10)}.${milhares % 10}`;
};
const normalizar = (t) =>
  String(t ?? "").normalize("NFD").replace(/[̀-ͯ]/g, "")
    .toLowerCase().replace(/[^a-z0-9]/g, "");
export const nomeDaConta = (conta) =>
  String(conta?.nick ?? "").trim() || "Sem nick";
// o Discord trataria *, _, ~, `, | do nick como formatacao
const limpo = (t) => String(t).replace(/([*_~`|\\>])/g, "\\$1");

export function placarDoPersonagem(personagens, nome) {
  const alvo = normalizar(nome);
  return (personagens ?? [])
    .filter((p) => normalizar(p.character_name) === alvo && num(p.poder) > 0)
    .sort((a, b) =>
      num(b.poder) - num(a.poder) ||
      (num(b.ataque) + num(b.ataque_especial)) -
        (num(a.ataque) + num(a.ataque_especial)));
}

export function campeoes(personagens) {
  const saida = {};
  for (const nome of PERSONAGENS) {
    const placar = placarDoPersonagem(personagens, nome);
    if (placar.length) saida[nome] = placar[0];
  }
  return saida;
}

export function podio(contas, categoria, personagens) {
  const titulos = {};
  if (categoria === "fortes") {
    for (const c of Object.values(campeoes(personagens))) {
      titulos[c.user_id] = (titulos[c.user_id] ?? 0) + 1;
    }
  }
  const coluna = { level: "nivel_chaser", colecao: "colecao_cartas",
                   dungeons: "dungeons", ataque: "ataque_medio" }[categoria];
  return (contas ?? [])
    .map((c) => [c, categoria === "fortes" ? (titulos[c.user_id] ?? 0) : num(c[coluna])])
    .sort((a, b) => b[1] - a[1] || num(b[0].ataque_medio) - num(a[0].ataque_medio));
}

export function textoDoValor(categoria, n) {
  n = num(n);
  if (categoria === "fortes") return n === 1 ? "1 campeão" : `${n} campeões`;
  if (categoria === "level") return `Lv. ${n}`;
  if (categoria === "dungeons") return n === 1 ? "1 dungeon" : `${n} dungeons`;
  return milhar(n);
}

/** A mensagem inteira (2 embeds), pronta para o webhook. */
export function montarMensagem(dados, agora = new Date()) {
  const contas = dados?.contas ?? [];
  const personagens = dados?.personagens ?? [];
  const porId = Object.fromEntries(contas.map((c) => [c.user_id, c]));

  const campos = CATEGORIAS.map(([chave, titulo]) => {
    const linhas = podio(contas, chave, personagens).slice(0, 3).map(
      ([conta, n], i) =>
        `${MEDALHAS[i]} **${limpo(nomeDaConta(conta))}** · ${textoDoValor(chave, n)}`);
    return { name: titulo, value: linhas.join("\n") || "—", inline: true };
  });

  const linhas = PERSONAGENS.map((nome) => {
    const c = campeoes(personagens)[nome];
    if (!c) return `**${nome}** · —`;
    const dono = limpo(nomeDaConta(porId[c.user_id]));
    return `**${nome}** · 👑 ${dono} · ⚡ ${milhar(c.poder)} · ${somaNoMilhar(c.ataque, c.ataque_especial)}`;
  });

  const hora = agora.toLocaleString("pt-BR", {
    timeZone: "America/Sao_Paulo", day: "2-digit", month: "2-digit",
    hour: "2-digit", minute: "2-digit",
  });
  return {
    username: "Caminho da Maestria",
    allowed_mentions: { parse: [] },
    embeds: [
      {
        title: "🏆 Ranking da Guilda",
        description: `${contas.length} jogadores · todas as contas do app · ` +
          "dungeons da semana atual",
        color: ROXO,
        fields: campos,
      },
      {
        title: "👑 Campeões por personagem",
        description: linhas.join("\n"),
        color: DOURADO,
        footer: { text: `Atualiza sozinho a cada 5 min · última: ${hora}` },
        timestamp: agora.toISOString(),
      },
    ],
  };
}

// ----------------------------------------------------------- o servidor --
async function rest(caminho, chave, opcoes = {}) {
  const base = Deno.env.get("SUPABASE_URL");
  return await fetch(`${base}/rest/v1/${caminho}`, {
    ...opcoes,
    headers: { apikey: chave, Authorization: `Bearer ${chave}`,
               "Content-Type": "application/json", ...(opcoes.headers ?? {}) },
  });
}

async function atualizar() {
  const chave = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY");
  const webhook = (Deno.env.get("DISCORD_WEBHOOK_URL") ?? "").split("?")[0]
    .replace(/\/+$/, "");
  if (!webhook) throw new Error("falta o segredo DISCORD_WEBHOOK_URL");

  const resp = await rest("rpc/ranking_dados", chave, { method: "POST", body: "{}" });
  if (!resp.ok) throw new Error(`ranking_dados: ${resp.status} ${await resp.text()}`);
  const mensagem = montarMensagem(await resp.json());

  const guardada = await rest("discord_mensagens?chave=eq.ranking&select=message_id", chave);
  let id = (await guardada.json())?.[0]?.message_id ?? null;

  if (id) {
    const editada = await fetch(`${webhook}/messages/${id}`, {
      method: "PATCH", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mensagem),
    });
    if (editada.status === 404) id = null;          // a mensagem foi apagada
    else if (!editada.ok) throw new Error(`Discord: ${editada.status} ${await editada.text()}`);
  }
  if (!id) {
    const postada = await fetch(`${webhook}?wait=true`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(mensagem),
    });
    if (!postada.ok) throw new Error(`Discord: ${postada.status} ${await postada.text()}`);
    id = (await postada.json()).id;
    await rest("discord_mensagens", chave, {
      method: "POST",
      headers: { Prefer: "resolution=merge-duplicates" },
      body: JSON.stringify({ chave: "ranking", message_id: id,
                             atualizado_em: new Date().toISOString() }),
    });
  }
  return id;
}

if (typeof Deno !== "undefined") {
  Deno.serve(async (req) => {
    const segredo = Deno.env.get("SEGREDO_RANKING");
    if (!segredo || req.headers.get("x-segredo") !== segredo) {
      return new Response("nao autorizado", { status: 401 });
    }
    try {
      const id = await atualizar();
      return Response.json({ ok: true, message_id: id });
    } catch (erro) {
      console.error(erro);
      return Response.json({ ok: false, erro: String(erro) }, { status: 500 });
    }
  });
}

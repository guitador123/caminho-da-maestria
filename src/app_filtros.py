# -*- coding: utf-8 -*-
"""
Barra de filtros e a logica de filtrar/ordenar os cards.

Parte da tela principal (`GrandChaseApp` herda de `FiltrosMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import tema_visual as tv
import tkinter as tk
from card_personagem import (
    DUNGEONS as DUNGEONS_CARD,
    LARGURA as CARD_LARGURA,
    _fracao)
from config_app import (
    ABA_GERAL,
    ABA_SEMANAIS,
    FILTRO_MAZMORRAS,
    FILTRO_PROGRESSO,
    FILTRO_VOID)
from dados_app import (
    _coluna_dungeon_semanal,
    _colunas_conhecidas,
    _num,
    _verdadeiro)
from opcoes import normalizar
from registro import falha


class FiltrosMixin:
    # ------------------------------------------------- barra de filtros --
    def _desenhar_filtros(self):
        """Desenha a barra de filtros (acima dos cards)."""
        # --- os 3 paineis -----------------------------------------------
        grupos = [
            ("mazmorras", "funil", "N\u00e3o fez estas masmorras semanais",
             tv.FILTROS_PAINEL1, FILTRO_MAZMORRAS,
             "Selecione uma ou mais op\u00e7\u00f5es para ver quem ainda n\u00e3o "
             "concluiu todas as selecionadas."),
            ("ordem", "ordenar", "Ordenar por Void",
             tv.FILTROS_PAINEL2, FILTRO_VOID,
             "Marque um ou os dois; a lista fica em ordem decrescente "
             "pela quantidade selecionada."),
            ("progresso", "progresso", "Progresso incompleto",
             tv.FILTROS_PAINEL3, FILTRO_PROGRESSO,
             "Marque um ou os dois; ao marcar ambos, aparecem personagens "
             "incompletos nos dois."),
        ]
        for grupo, icone, titulo, caixa, opcoes, ajuda in grupos:
            self._desenhar_painel_filtro(grupo, icone, titulo, caixa,
                                         opcoes, ajuda)

    def _desenhar_painel_filtro(self, grupo, icone, titulo, caixa, opcoes,
                                ajuda, slim=False):
        """Um painel de filtro (vidro + opcoes redondas)."""
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(caixa)
        largura = max(1, int(x2 - x1))
        altura = max(1, int(y2 - y1))

        # fundo de vidro
        self.canvas.create_image(x1, y1, anchor="nw", image=self._foto(
            tv.retangulo_alfa(cor=(28, 24, 48), alfa=205,
                              tamanho=(largura, altura), raio=16)),
            tags=("filtros",))

        # icone + titulo
        self._icone(icone, x1 + lay.f(24), y1 + lay.f(20), lay.f(18),
                    cor=(167, 139, 250, 255), tags=("filtros",))
        self._texto(x1 + lay.f(42), y1 + lay.f(11), titulo, 13,
                    cor=tv.CORES["texto"], peso="bold", tags=("filtros",))

        if slim:
            # tudo numa linha so
            x = x1 + lay.f(300)
            for chave, rotulo in opcoes:
                marcado = chave in self._conjunto_filtro(grupo)
                tag = f"filtro:{grupo}:{chave}"
                self.canvas.create_image(
                    x, y1 + lay.f(26), anchor="w",
                    image=self._foto(tv.circulo_opcao(marcado, lay.f(19))),
                    tags=(tag, "filtros"))
                self._texto(x + lay.f(28), y1 + lay.f(26), rotulo, 12,
                            cor=(tv.CORES["texto"] if marcado
                                 else tv.CORES["suave"]),
                            anchor="w", tags=(tag, "filtros"))
                self.canvas.tag_bind(tag, "<Button-1>",
                                     lambda e, g=grupo, c=chave:
                                     self._alternar_filtro(g, c))
                self.canvas.tag_bind(tag, "<Enter>",
                                     lambda e: self.canvas.configure(cursor="hand2"))
                self.canvas.tag_bind(tag, "<Leave>",
                                     lambda e: self.canvas.configure(cursor=""))
                x += lay.f(160)
            self._texto(x + lay.f(10), y1 + lay.f(20), ajuda, 10,
                        cor=tv.CORES["olho"], tags=("filtros",))
            return

        # opcoes (botoes redondos)
        y = y1 + lay.f(48)
        for chave, rotulo in opcoes:
            marcado = chave in self._conjunto_filtro(grupo)
            lado = lay.f(19)
            tag = f"filtro:{grupo}:{chave}"
            self.canvas.create_image(
                x1 + lay.f(16), y, anchor="w",
                image=self._foto(tv.circulo_opcao(marcado, lado)),
                tags=(tag, "filtros"))
            # o circulo e o texto ficam na MESMA linha (anchor="w" centra
            # o texto na vertical, como o circulo)
            self._texto(x1 + lay.f(44), y, rotulo, 12,
                        cor=(tv.CORES["texto"] if marcado else tv.CORES["suave"]),
                        anchor="w", tags=(tag, "filtros"))
            self.canvas.tag_bind(tag, "<Button-1>",
                                 lambda e, g=grupo, c=chave:
                                 self._alternar_filtro(g, c))
            self.canvas.tag_bind(tag, "<Enter>",
                                 lambda e: self.canvas.configure(cursor="hand2"))
            self.canvas.tag_bind(tag, "<Leave>",
                                 lambda e: self.canvas.configure(cursor=""))
            y += lay.f(31)

        # texto de ajuda (quebrado para caber dentro do painel)
        for linha in self._quebrar(ajuda, 10, largura - lay.f(32)):
            self._texto(x1 + lay.f(16), y + lay.f(6), linha, 10,
                        cor=tv.CORES["olho"], tags=("filtros",))
            y += lay.f(14)

    def _quebrar(self, texto, tamanho, largura_max):
        """Quebra um texto em linhas que cabem em `largura_max` (px reais)."""
        fonte = self._fonte_obj(tamanho)
        palavras = str(texto).split()
        linhas = []
        atual = ""
        for palavra in palavras:
            teste = (atual + " " + palavra).strip()
            if fonte.measure(teste) <= largura_max or not atual:
                atual = teste
            else:
                linhas.append(atual)
                atual = palavra
        if atual:
            linhas.append(atual)
        return linhas or [""]

    def _conjunto_filtro(self, grupo):
        return {"mazmorras": self.filtro_mazmorras,
                "ordem": self.filtro_ordem_void,
                "progresso": self.filtro_progresso}.get(grupo)

    # --------------------------------------------------------- filtros ----
    def _dados_filtro(self, nome):
        """Dados de um personagem usados pelos filtros."""
        df_geral = self.dfs.get(ABA_GERAL)
        df_sem = self.dfs.get(ABA_SEMANAIS)

        def _linha(df):
            if df is None or df.empty or "Nome" not in df.columns:
                return {}
            achada = df[df["Nome"].astype(str) == str(nome)]
            if achada.empty:
                return {}
            return achada.iloc[0].to_dict()

        geral = _linha(df_geral)
        semanal = _linha(df_sem)

        # --- void (forca do personagem) ---
        vazio_uni = _num(geral.get("Vazio Uni.") or geral.get("vazio_uni"))
        vazio_apo = _num(geral.get("Vazio Apo.") or geral.get("vazio_apo"))

        # --- mazmorras semanais ---
        mazmorras = {}
        for chave, _rotulo in DUNGEONS_CARD:
            coluna = _coluna_dungeon_semanal(df_sem, chave)
            mazmorras[chave] = (_verdadeiro(semanal.get(coluna))
                                if coluna else False)

        # --- despertar / liberacao ---
        despertar = False
        nucleo = _fracao(geral.get("Núcleo") or geral.get("nucleo"))
        epicos = _fracao(geral.get("Núcleos Épicos+")
                         or geral.get("nucleos_epicos"))
        if nucleo[0] == 13 and epicos[0] == 9:
            despertar = True
        libertacao = False
        if _verdadeiro(geral.get("Libertação") or geral.get("libertacao")):
            lib_nuc = _num(geral.get("Libertação Núcleos")
                           or geral.get("libertacao_nucleos"))
            lib_epi = _num(geral.get("Libertação Épicos+")
                           or geral.get("libertacao_epicos"))
            libertacao = (lib_nuc == 9 and lib_epi == 4)

        return {"vazio_uni": vazio_uni, "vazio_apo": vazio_apo,
                "ataque": _num(geral.get("Poder") or geral.get("poder")),
                "mazmorras": mazmorras, "despertar": despertar,
                "libertacao": libertacao}

    def _ordenar_personagens(self, nomes, dados):
        """Ordem: sempre do mais forte para o mais fraco.

        Padrao: pelo **Ataque Total** (maior -> menor). Se o filtro "Ordenar
        por Void" estiver marcado, a lista passa a ordenar pela soma dos
        Void selecionados.
        """
        if self.filtro_ordem_void:
            selecionados = self.filtro_ordem_void

            def _forca(nome):
                info = dados.get(nome) or {}
                return sum(info.get(chave, 0) for chave in selecionados)

            return sorted(nomes, key=_forca, reverse=True)
        return sorted(nomes,
                      key=lambda n: (dados.get(n) or {}).get("ataque", 0),
                      reverse=True)

    def _filtrar_personagens(self, nomes):
        """Aplica os filtros e devolve (nomes, dados) ja ordenados."""
        dados = {nome: self._dados_filtro(nome) for nome in nomes}
        selecionados = list(nomes)

        # 1) "nao fez estas masmorras semanais": quem ainda nao concluiu
        #    pelo menos uma das selecionadas
        if self.filtro_mazmorras:
            def _faltam(nome):
                maz = (dados.get(nome) or {}).get("mazmorras") or {}
                for chave in self.filtro_mazmorras:
                    # a chave do filtro e a chave normalizada da dungeon
                    procurada = chave
                    if procurada not in maz:
                        for outra in maz:
                            if normalizar(outra) == normalizar(chave):
                                procurada = outra
                                break
                    if not maz.get(procurada, False):
                        return True      # ainda nao fez esta dungeon
                return False
            selecionados = [n for n in selecionados if _faltam(n)]

        # 2) "progresso incompleto": quem esta incompleto em TODOS os marcados
        if self.filtro_progresso:
            def _incompleto(nome):
                info = dados.get(nome) or {}
                return all(not info.get(chave, False)
                           for chave in self.filtro_progresso)
            selecionados = [n for n in selecionados if _incompleto(n)]

        # 3) ordem (do mais forte para o mais fraco)
        return self._ordenar_personagens(selecionados, dados), dados

    def _nomes_visiveis(self):
        """Os nomes dos personagens que passam pelos filtros (na ordem)."""
        geral = self.dfs.get(ABA_GERAL)
        if geral is None or geral.empty:
            return []
        nomes = [str(n) for n in geral["Nome"].tolist()]
        visiveis, _dados = self._filtrar_personagens(nomes)
        return visiveis

    def _alternar_filtro(self, grupo, chave):
        """Liga/desliga uma opcao do filtro."""
        alvo = self._conjunto_filtro(grupo)
        if alvo is None:
            return
        if chave in alvo:
            alvo.discard(chave)
        else:
            alvo.add(chave)
        self._aplicar_filtros()

    def _aplicar_filtros(self):
        """Aplica os filtros.

        NAO recria os 25 cards (era o que travava a tela): os cards sao
        apenas MOVIDOS ou ESCONDIDOS, e a barra de filtros e redesenhada
        (para aparecer o CHECK da opcao ativa).
        """
        try:
            yview = self.canvas.yview()
        except tk.TclError:
            yview = (0.0, 1.0)
        except Exception:
            falha("ler a rolagem")
            yview = (0.0, 1.0)
        self._reposicionar_cards()
        self._redesenhar_filtros()
        try:
            self.canvas.yview_moveto(yview[0])
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("restaurar a rolagem")

    def _reposicionar_cards(self):
        """Mostra/esconde e move os cards conforme o filtro (rapido)."""
        geral = self.dfs.get(ABA_GERAL)
        if geral is None or geral.empty:
            return
        nomes = [str(n) for n in geral["Nome"].tolist()]
        visiveis, _dados = self._filtrar_personagens(nomes)

        lay = self.lay
        largura_janela = self.winfo_width() or tv.DESIGN_W
        altura_janela = self.winfo_height() or tv.DESIGN_H
        escala = self._escala_dos_cards(largura_janela, altura_janela)
        largura_card = CARD_LARGURA * escala
        gap = 16 * escala
        margem = 20
        colunas = max(1, int((largura_janela - 2 * margem + gap)
                             // (largura_card + gap)))
        largura_total = colunas * largura_card + (colunas - 1) * gap
        x0 = max(margem, (largura_janela - largura_total) / 2)
        y0 = lay.y(tv.FILTROS_FIM)

        # as posicoes de cada card (por linhas)
        alturas = {c.dados.get("nome"): c.altura
                   for c in getattr(self, "cards_personagem", [])}
        posicoes = {}
        y = y0
        for inicio in range(0, len(visiveis), colunas):
            linha = visiveis[inicio:inicio + colunas]
            altura_linha = max((alturas.get(nome, 0) for nome in linha),
                               default=0)
            for coluna, nome in enumerate(linha):
                posicoes[nome] = (x0 + coluna * (largura_card + gap), y)
            y += altura_linha + gap

        for card in getattr(self, "cards_personagem", []):
            nome = card.dados.get("nome")
            if nome in posicoes:
                x, y_card = posicoes[nome]
                card.definir_visivel(True)
                card.mover_para(x, y_card)
            else:
                card.definir_visivel(False)

        # o scrollregion agora e menor (so os cards visiveis)
        try:
            total = y + lay.h(40)
            self.canvas.configure(scrollregion=(0, 0, max(largura_janela,
                                                          largura_total + 2 * margem),
                                                total))
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("reposicionar os cards")

    def _redesenhar_filtros(self):
        """Redesenha a barra de filtros (aparece o CHECK da opcao ativa)."""
        try:
            self.canvas.delete("filtros")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("apagar os filtros")
        self._desenhar_filtros()

    # ----------------------------------------------- filtro / missao rapida
    def _prontos_missao(self):
        """Nomes dos personagens com TODAS as dungeons semanais concluidas."""
        df = self.dfs.get(ABA_SEMANAIS)
        if df is None or df.empty:
            return set()
        colunas = _colunas_conhecidas(df, "semanais")
        if not colunas:
            return set()
        prontos = set()
        for _, linha in df.iterrows():
            if all(_verdadeiro(linha.get(c)) for c in colunas):
                prontos.add(str(linha.get("Nome", "")))
        return prontos

    def _linhas_visiveis(self, df, termo):
        """Linhas do dataframe respeitando a busca e o filtro Missao Rapida."""
        termo = (termo or "").strip().lower()
        linhas = df.iterrows()
        if termo:
            linhas = (r for r in linhas
                      if str(r[1].get("Nome", "")).lower().find(termo) >= 0)
        if self.missao_rapida:
            prontos = self._prontos_missao()
            if prontos:
                linhas = (r for r in linhas
                          if str(r[1].get("Nome", "")) in prontos)
        return list(linhas)

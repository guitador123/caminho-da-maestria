# -*- coding: utf-8 -*-
"""
Barra de filtros e a logica de filtrar/ordenar os cards.

Parte da tela principal (`GrandChaseApp` herda de `FiltrosMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import tkinter as tk

import filtros
import tema_visual as tv
from card_personagem import LARGURA as CARD_LARGURA
from config_app import (ABA_GERAL, ABA_SEMANAIS, FILTRO_MAZMORRAS,
                        FILTRO_PROGRESSO, FILTRO_VOID)
from dados_app import _colunas_conhecidas, _verdadeiro
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
        """Dados de um personagem usados pelos filtros (ver filtros.py)."""
        return filtros.dados_filtro(self.dfs.get(ABA_GERAL),
                                    self.dfs.get(ABA_SEMANAIS), nome)

    def _ordenar_personagens(self, nomes, dados):
        """Do mais forte para o mais fraco (ver filtros.filtrar_e_ordenar)."""
        return filtros.filtrar_e_ordenar(nomes, dados,
                                         ordem_void=self.filtro_ordem_void)

    def _filtrar_personagens(self, nomes):
        """Aplica os filtros e devolve (nomes, dados) ja ordenados."""
        dados = {nome: self._dados_filtro(nome) for nome in nomes}
        visiveis = filtros.filtrar_e_ordenar(
            nomes, dados, mazmorras=self.filtro_mazmorras,
            progresso=self.filtro_progresso,
            ordem_void=self.filtro_ordem_void)
        return visiveis, dados

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

    def _reordenar_cards(self):
        """Refaz a lista (filtro + ordem) depois que um card mudou.

        Sem isso, mudar o Ataque Total nao trocava a ordem e marcar uma
        dungeon (ex.: Caminho Abissal) nao tirava o card do filtro "nao
        fez" ate mexer em algum filtro. Mantem a rolagem onde estava.
        """
        topo = self._topo_da_rolagem()
        if topo is None:
            return                    # janela ja fechada
        self._reposicionar_cards(manter_topo=topo)
        self._restaurar_rolagem(topo)

    # --------------------------------------------------------- rolagem ----
    def _topo_da_rolagem(self):
        """Onde a tela esta, em PIXELS da pagina (None se ja fechou).

        Em pixels, e nao em fracao (yview): quando o filtro esconde cards
        a pagina encolhe, e a mesma fracao caia muito mais acima (a tela
        "pulava")."""
        try:
            return self.canvas.canvasy(0)
        except tk.TclError:
            return None
        except Exception:
            falha("ler a rolagem")
            return None

    def _restaurar_rolagem(self, topo):
        """Volta para o mesmo pixel e segura o cenario de fundo no lugar
        (sem isso a arte ficava deslocada depois do filtro)."""
        rolagem = getattr(self, "_rolagem", None)
        if rolagem is not None:
            rolagem.parar()           # uma animacao da roda nao continua
        try:
            total = float(str(self.canvas.cget("scrollregion")).split()[3])
            visivel = self.canvas.winfo_height()
            topo = max(0.0, min(topo, total - visivel))
            self.canvas.yview_moveto(topo / total if total > 0 else 0.0)
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("restaurar a rolagem")
        self._fixar_cenario()

    def _aplicar_filtros(self):
        """Aplica os filtros.

        NAO recria os 25 cards (era o que travava a tela): os cards sao
        apenas MOVIDOS ou ESCONDIDOS, e a barra de filtros e redesenhada
        (para aparecer o CHECK da opcao ativa).
        """
        topo = self._topo_da_rolagem()
        if topo is None:
            topo = 0.0
        self._reposicionar_cards(manter_topo=topo)
        self._redesenhar_filtros()
        topo = self._topo_sem_vazio(topo)
        self._ajustar_altura(topo)
        self._restaurar_rolagem(topo)

    def _ajustar_altura(self, topo):
        """A pagina vai ate o ultimo card, ou ate o fim da tela (o que for
        maior): sem sobra de espaco vazio para rolar."""
        fim = getattr(self, "_fim_dos_cards", None)
        if fim is None:
            return
        try:
            x1, y1, x2, _y2 = (float(v) for v in
                               str(self.canvas.cget("scrollregion")).split())
            total = max(fim + self.lay.h(40),
                        topo + self.canvas.winfo_height())
            self.canvas.configure(scrollregion=(x1, y1, x2, total))
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("ajustar a altura da pagina")

    def _topo_sem_vazio(self, topo):
        """Rolado la embaixo, com o filtro deixando poucos cards, a tela
        mostraria so espaco vazio: sobe o NECESSARIO para o ultimo card
        encostar no rodape (nunca acima da barra de filtros)."""
        fim = getattr(self, "_fim_dos_cards", None)
        if fim is None:
            return topo
        barra = self.lay.y(tv.FILTROS_BUSCA[1]) - self.lay.h(30)
        alvo = max(barra, fim + self.lay.h(40) - self.canvas.winfo_height())
        return min(topo, alvo)

    def _reposicionar_cards(self, manter_topo=None):
        """Mostra/esconde e move os cards conforme o filtro (rapido).

        `manter_topo` (pixels): a pagina fica alta o bastante para a tela
        continuar exatamente ali (com poucos cards ela ficava menor que a
        janela e o Tk jogava tudo para o topo)."""
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
            self._fim_dos_cards = y          # onde termina o ultimo card
            if manter_topo is not None:
                total = max(total, manter_topo + self.canvas.winfo_height())
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

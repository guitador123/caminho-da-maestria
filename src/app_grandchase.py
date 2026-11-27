"""
Controle Grand Chase - Editor Desktop Moderno
Tela principal: "Caminho da Maestria" (visual fiel ao mockup)

Camadas da tela (ver tema_visual.py):
    1. cenario PIL  - arte do Grand Chase graduada em roxo + paineis de vidro
    2. canvas Tk    - a imagem do cenario + todos os textos e icones
    3. widgets CTk  - campos e botoes de fundo solido

Interface: CustomTkinter + PIL
Dados: Supabase (nuvem) + Excel local (backup) + SQLite local (opcional)
"""

import os
import queue
import tkinter as tk
from tkinter import messagebox
from tkinter import font as tkfont
from PIL import ImageTk

import customtkinter as ctk

from supabase_db import get_supabase
from opcoes import coluna_banco, chave_semanal
import tema_visual as tv
import caminhos
from registro import falha, registrar
from card_personagem import (CardPersonagem, LARGURA as CARD_LARGURA,
                              ESCALA_MAX, ALTURA_CARD_BASE)

# A tela foi dividida em partes (23/11/2026, item 10 do AFAZERES). O
# GrandChaseApp herda os metodos de cada uma:
from app_filtros import FiltrosMixin          # barra de filtros + filtrar
from app_arquivos import ArquivosMixin        # Excel, SQLite, tabela
from app_salvamento import SalvamentoMixin    # Supabase, nivel, preferencias
from app_missao import MissaoMixin            # missao rapida, zerar dungeons
from app_cartoes import CartoesMixin          # cartoes de estatistica
from app_atualizacao import AtualizacaoMixin  # botao da versao (atualizar)
from app_evolucao import EvolucaoMixin        # pagina "Evolucao semanal"
from app_offline import OfflineMixin          # copia local e sincronia
from app_paginas import PaginasMixin          # guias: Maestria/Guilda/Evolucao
from rolagem import RolagemSuave              # roda do mouse suave
from dados_app import STATUS_PERSONAGEM, _decimal

# constantes e helpers (reexportados: outros modulos e os testes importam
# daqui, ex.: `from app_grandchase import FILTRO_VOID, _num`)
from config_app import (  # noqa: F401
    FILTRO_MAZMORRAS, FILTRO_VOID, FILTRO_PROGRESSO, MODO_MISSAO_JANELA,
    MODO_MISSAO_CARD, NIVEL_CHASER_PADRAO, COLUNA_NIVEL, ABA_GERAL,
    ABA_PECAS, ABA_ACESSORIOS, ABA_SEMANAIS, ROTULOS_COLUNAS, BASE_DIR,
    BACKGROUND_PATH, EXCEL_DEFAULT, DB_FILE, COLECAO_CARTAS_MAXIMO)
from dados_app import (  # noqa: F401
    _mesmo_arquivo, _colunas_conhecidas, _rotular_colunas, _verdadeiro,
    _num, _ordenar_colunas, _coluna_dungeon_semanal, _coluna_no_df,
    progresso_exp)
from app_arquivos import ttk_treeview_moderno, _estilizar_ttk  # noqa: F401

# o que outros modulos e os testes importam DAQUI (reexportado)
__all__ = [
    "GrandChaseApp", "MOSTRAR_TABELA", "MOSTRAR_IMPORTACAO",
    "FILTRO_MAZMORRAS", "FILTRO_VOID", "FILTRO_PROGRESSO",
    "MODO_MISSAO_JANELA", "MODO_MISSAO_CARD", "NIVEL_CHASER_PADRAO",
    "COLUNA_NIVEL", "ABA_GERAL", "ABA_PECAS", "ABA_ACESSORIOS",
    "ABA_SEMANAIS", "ROTULOS_COLUNAS", "BASE_DIR", "BACKGROUND_PATH",
    "EXCEL_DEFAULT", "DB_FILE", "_mesmo_arquivo", "_colunas_conhecidas",
    "_rotular_colunas", "_verdadeiro", "_num", "_ordenar_colunas",
    "_coluna_dungeon_semanal", "_coluna_no_df", "ttk_treeview_moderno",
    "_estilizar_ttk",
]

# ---------------------------------------------------------------------------
# Configuracao visual
# ---------------------------------------------------------------------------
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# A tabela de personagens fica oculta por enquanto (foco na estetica)
MOSTRAR_TABELA = False

# Bloco "Import updated workbook": o painel de vidro continua desenhado
# (espaco reservado para outras ideias), mas o conteudo fica oculto.
MOSTRAR_IMPORTACAO = False

# Print + log em arquivo (o .exe roda sem console). Ver registro.py.
_registrar = registrar


class GrandChaseApp(FiltrosMixin, ArquivosMixin, SalvamentoMixin,
                    MissaoMixin, CartoesMixin, AtualizacaoMixin,
                    EvolucaoMixin, OfflineMixin, PaginasMixin, ctk.CTk):
    def __init__(self, user=None, supabase=None, offline=False):
        super().__init__()
        # lido na criacao (os testes ligam app_grandchase.MOSTRAR_TABELA antes)
        self.mostrar_tabela = MOSTRAR_TABELA

        self.title("Caminho da Maestria")
        self._aplicar_icone()
        self.geometry("1152x820")
        self.minsize(960, 680)
        # o X passa pelo quit_app (que libera as imagens do Tk antes de fechar)
        self.protocol("WM_DELETE_WINDOW", self._sair)

        self.user = user
        self.user_id = getattr(user, "id", None) if user is not None else None
        self.email_usuario = str(getattr(user, "email", "") or "")
        self.user_email = (getattr(user, "email", None) or "") if user is not None else ""

        self.excel_path = EXCEL_DEFAULT if os.path.exists(EXCEL_DEFAULT) else None
        self.dfs = {}
        self.originals = {}
        # True quando `originals` e o que esta no banco: ai o salvamento
        # manda so as linhas que mudaram (importado do Excel = manda tudo)
        self._originais_do_banco = False
        self.tree_refs = {}
        self.abas_criadas = []
        self.modified = False
        self.supabase = supabase or get_supabase()
        self.usar_supabase = self.user_id is not None
        self.arquivo_selecionado = None
        self.missao_rapida = False
        self.nivel_chaser = NIVEL_CHASER_PADRAO
        self.colecao_cartas = 0           # 15.4: um valor por conta
        self._aviso_nivel = ""
        self._painel_missao = None
        self.ultimo_personagem_missao = None
        self.missao_modo = MODO_MISSAO_JANELA
        # --- filtros da lista de cards ---
        self.filtro_mazmorras = set()
        self.filtro_ordem_void = set()
        self.filtro_progresso = set()
        # --- perfil do usuario ---
        self.perfil_nick = ""
        self.perfil_avatar = ""      # (legacy) base64 da foto
        self.perfil_personagem = ""   # o personagem da foto (elesis, lire...)
        self.perfil_avatar_temp = None   # arquivo temporario p/ o PIL
        self._janela_perfil = None
        self._painel_doacao = None
        self.lay = tv.Layout(1152, 820)
        self.itens_valores = {}     # chave do card -> item do canvas
        self.itens_botoes = {}      # chave -> item do canvas (hit area)
        self.itens_texto_botao = {}  # chave -> item do texto do botao
        self.itens_destaque = {}    # chave -> item do destaque (botao ligado)
        self.itens_hover = {}       # chave -> item do clareamento (hover)
        self.itens_verde = {}       # chave -> item do fundo VERDE (ativo)
        self.itens_chave_missao = {}  # partes da opcao do modo da missao
        self._tamanho_fundo = (0, 0)
        self._job_fundo = None
        self._tentativas_fundo = 0
        self.status_var = ctk.StringVar(value="Pronto")

        # --- salvamento em segundo plano ---------------------------------
        self._fila_salvamento = queue.Queue()
        self._salvando = False
        self._salvar_pendente = False
        self._versao = 0          # contador de alteracoes nos dados
        self._versao_salva = -1    # versao que estava sendo enviada
        self.after(80, self._verificar_salvamento)
        # --- modo offline (copia local + sincronia) ----------------------
        self._iniciar_offline(offline)

        # === Camada 2: canvas (imagem do cenario + textos) ===============
        self.canvas = tk.Canvas(self, bg="#191334", highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        # as guias do topo (Maestria, Guilda, Evolucao)
        self._iniciar_paginas()

        self._construir_widgets()
        self._montar_tela()

        self.after(120, self._redesenhar)
        self.bind("<Configure>", self._ao_redimensionar)
        # rolagem da pagina (cards abaixo do "Caminho da Maestria"):
        # suave e proporcional a tela (rolagem.py); passo de 1 px para a
        # animacao nao andar aos trancos
        self.canvas.configure(yscrollincrement=1)
        self._rolagem = RolagemSuave(self.canvas, ao_mover=self._fixar_cenario)
        self.canvas.bind("<MouseWheel>", self._rolar)
        self.bind("<KeyPress>", self._atalho_missao)

        # Carrega dados automaticamente
        if self.usar_supabase:
            self.carregar_do_supabase()
            # 1o login depois do reset de quarta: abre a evolucao sozinha
            self.after(1500, self._verificar_resumo_semanal)
        elif self.excel_path:
            self.load_excel(self.excel_path)
        else:
            self.status("Nenhum dado carregado. Use 'Escolher arquivo' ou conecte ao Supabase.")

    # ======================================================= TELA (camadas) ==
    def _ao_redimensionar(self, event):
        """Redesenha a tela quando a janela muda de tamanho."""
        if event.widget is not self:
            return
        largura = self.winfo_width()
        altura = self.winfo_height()
        if largura < 400 or altura < 300:
            return
        if abs(largura - self._tamanho_fundo[0]) < 24 and \
                abs(altura - self._tamanho_fundo[1]) < 24:
            return
        if self._job_fundo is not None:
            try:
                self.after_cancel(self._job_fundo)
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("cancelar o redesenho do fundo")
        self._job_fundo = self.after(140, self._redesenhar)

    def _redesenhar(self):
        """Re-renderiza o cenario e redesenha todos os textos."""
        self._job_fundo = None
        if not self.winfo_ismapped():
            self._tentativas_fundo += 1
            if self._tentativas_fundo <= 20:
                self._job_fundo = self.after(150, self._redesenhar)
            return
        try:
            largura, altura = self._tamanho_alvo()
            if (largura, altura) == self._tamanho_fundo:
                return
            self._tamanho_fundo = (largura, altura)
            self._montar_tela()
            _registrar(f"[Cenario] redesenhado ({largura}x{altura})")
        except Exception as e:
            falha("[Cenario] redesenhar", e)

    def _tamanho_alvo(self):
        """Tamanho a usar para o cenario (real da janela ou o da geometria)."""
        largura = self.winfo_width()
        altura = self.winfo_height()
        if largura >= 400 and altura >= 300:
            return largura, altura
        try:
            geo = self.geometry().split("+")[0]
            l, a = geo.lower().split("x")
            return max(int(l), 400), max(int(a), 300)
        except tk.TclError:
            return tv.DESIGN_W, tv.DESIGN_H
        except Exception:
            falha("ler o tamanho da janela")
            return tv.DESIGN_W, tv.DESIGN_H

    def _montar_tela(self):
        """Monta a tela: cenario (PIL) + textos (canvas) + widgets."""
        largura, altura = self._tamanho_alvo()
        self.lay = tv.Layout(largura, altura)

        # --- camada 1: arte (fundo FIXO) + paineis (rolam com o conteudo) --
        try:
            if os.path.exists(BACKGROUND_PATH):
                arte = tv.render_arte(BACKGROUND_PATH, largura, altura)
                self.cenario_tk = ImageTk.PhotoImage(arte)
                self.paineis_tk = ImageTk.PhotoImage(
                    tv.render_paineis(largura, altura, self.lay))
                self.canvas.delete("all")
                self._item_cenario = self.canvas.create_image(
                    0, 0, anchor="nw", image=self.cenario_tk, tags="cenario")
                self.canvas.create_image(0, 0, anchor="nw", image=self.paineis_tk,
                                         tags="paineis")
        except Exception as e:
            falha("[Cenario] gerar", e)

        self._desenhar_textos()
        self._desenhar_cards()
        self._posicionar_widgets()
        self._atualizar_cards()
        # por ultimo: a barra de guias fica por cima de tudo
        self._desenhar_abas_maestria()

    # ------------------------------------------------------------ rolagem --
    def _rolar(self, evento):
        """Rola a pagina (suave); o cenario (arte) continua fixo."""
        self._rolagem.roda(evento.delta)

    def _fixar_cenario(self):
        """Mantem a arte de fundo parada enquanto o conteudo rola."""
        item = getattr(self, "_item_cenario", None)
        if item:
            try:
                self.canvas.coords(item, 0, self.canvas.canvasy(0))
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("fixar o cenario")
        # a barra de guias tambem fica parada no topo
        self._elevar_abas()

    # ------------------------------------------------------------- cards ---
    def _dados_personagem(self, nome, dfs=None):
        """Monta o dicionario de dados de um personagem (vindo do Supabase).
        `dfs`: outras abas (a conta de outra pessoa, na Guilda); sem ele,
        as da sua conta."""
        dfs = self.dfs if dfs is None else dfs
        geral = dfs.get(ABA_GERAL)
        pecas = dfs.get(ABA_PECAS)
        acess = dfs.get(ABA_ACESSORIOS)
        sem = dfs.get(ABA_SEMANAIS)

        def _linha(df):
            if df is None or df.empty or "Nome" not in df.columns:
                return None
            achada = df[df["Nome"].astype(str) == str(nome)]
            if achada.empty:
                return None
            return achada.iloc[0].to_dict()

        linha_geral = _linha(geral) or {}
        linha_pecas = _linha(pecas) or {}
        linha_acess = _linha(acess) or {}
        linha_sem = _linha(sem) or {}

        # status (15.1): a coluna vem com o rotulo ("Dano nas Costas %")
        # ou com o nome do banco ("dano_costas")
        por_chave = {coluna_banco(k): v for k, v in linha_geral.items()}
        status = {}
        for chave, coluna, _rotulo, tipo in STATUS_PERSONAGEM:
            valor = por_chave.get(coluna_banco(coluna))
            status[chave] = (_decimal(valor) if tipo == "percentual"
                             else _num(valor))

        return {
            "nome": nome,
            **status,
            "poder": _num(linha_geral.get("Poder") or linha_geral.get("poder")),
            "torre": (linha_geral.get("Torre Das Ilusões")
                      or linha_geral.get("torre_das_ilusoes") or "0 / 30"),
            "vazio_uni": _num(linha_geral.get("Vazio Uni.")
                              or linha_geral.get("vazio_uni")),
            "vazio_apo": _num(linha_geral.get("Vazio Apo.")
                              or linha_geral.get("vazio_apo")),
            "nucleos_dimensionais": _num(linha_geral.get("Núcleos Dimensionais")
                                         or linha_geral.get("nucleos_dimensionais")),
            "fragmento_vazio_disperso": _num(
                linha_geral.get("Fragmento do Vazio Disperso")
                or linha_geral.get("fragmento_vazio_disperso")),
            "nucleo": linha_geral.get("Núcleo") or linha_geral.get("nucleo") or "",
            "nucleos_epicos": (linha_geral.get("Núcleos Épicos+")
                               or linha_geral.get("nucleos_epicos") or ""),
            "libertacao": (linha_geral.get("Libertação")
                           or linha_geral.get("libertacao") or ""),
            "libertacao_nucleos": _num(linha_geral.get("Libertação Núcleos")
                                      or linha_geral.get("libertacao_nucleos")),
            "libertacao_epicos": _num(linha_geral.get("Libertação Épicos+")
                                      or linha_geral.get("libertacao_epicos")),
            "titulo": (linha_acess.get("Título")
                       or linha_acess.get("titulo") or ""),
            # as chaves sao NORMALIZADAS (via coluna_banco) para casar com a
            # planilha ("Anel" -> "anel", "Altar da Ruína" -> "altardarunha")
            # e com o banco ("altar_da_runha") ao mesmo tempo.
            "pecas": {coluna_banco(k): v for k, v in linha_pecas.items()
                      if k not in ("Nome", "id", "character_id")},
            "acessorios": {coluna_banco(k): v for k, v in linha_acess.items()
                           if k not in ("Nome", "id", "character_id")},
            # a Torre semanal entra com a chave do app ("torredasilusoes")
            "semanais": {chave_semanal(k): v for k, v in linha_sem.items()
                         if k not in ("Nome", "id", "character_id")},
        }

    def _escala_dos_cards(self, largura, altura):
        """Escala do card para a resolucao atual.

        Regras:
        1. o card precisa CABER na ALTURA da tela (para ver o card inteiro);
        2. o card nunca fica menor que o design aprovado (escala 1.0);
        3. a grade tem que PREENCHER a largura da tela (evita metade vazia).
        """
        base = ALTURA_CARD_BASE
        # 1) limite pela altura da tela
        limite = min(ESCALA_MAX, (altura * 0.97) / base)
        if limite < 1.0:
            return 1.0
        # 2) maior escala que ainda preenche a largura
        margem = 20
        util = max(1.0, largura - 2 * margem)
        for passo in range(0, 80):
            escala = round(limite - passo * 0.02, 3)
            if escala < 1.0:
                break
            gap = 16 * escala
            largura_card = CARD_LARGURA * escala
            colunas = max(1, int((util + gap) // (largura_card + gap)))
            usado = colunas * largura_card + (colunas - 1) * gap
            if usado >= util * 0.9:
                return escala
        return 1.0

    def _desenhar_cards(self):
        """Desenha os 25 cards de personagem abaixo da tela principal.

        O card se adapta a resolucao: a escala e calculada pela ALTURA da
        tela (para o card caber inteiro) e pela LARGURA (para a grade
        preencher a tela) — a grade fica sempre centralizada.
        """
        self.cards_personagem = []
        geral = self.dfs.get(ABA_GERAL)
        if geral is None or geral.empty or "Nome" not in geral.columns:
            return

        nomes = [str(n) for n in geral["Nome"].tolist()]
        # filtros: quem aparece (e em que ordem)
        nomes, _dados_filtro = self._filtrar_personagens(nomes)

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
        y0 = lay.y(tv.FILTROS_FIM)   # abaixo do hero E da barra de filtros

        pasta = os.path.join(caminhos.assets_dir(), "assets", "personagens")
        y = y0
        for inicio in range(0, len(nomes), colunas):
            linha = nomes[inicio:inicio + colunas]
            altura_linha = 0
            for coluna, nome in enumerate(linha):
                card = CardPersonagem(
                    self.canvas, x0 + coluna * (largura_card + gap), y,
                    self._dados_personagem(nome),
                    ao_abrir=self._abrir_personagem,
                    pasta_retratos=pasta, escala=escala,
                    ao_missao=self.alternar_missao_rapida,
                    ao_cartas=self._abrir_cartas)
                self.cards_personagem.append(card)
                altura_linha = max(altura_linha, card.altura)
            y += altura_linha + gap

        # scrollregion: hero + cards
        total = y + lay.h(40)
        self.canvas.configure(scrollregion=(0, 0, max(largura_janela,
                                                      largura_total + 2 * margem),
                                            total))

    def _abrir_personagem(self, dados):
        """Abre a janela de edicao do personagem.

        No modo MISSÃO RÁPIDA (CARD) o card NÃO abre a edição: ele serve só
        para marcar as missões (clicar num chip), sem abrir nada junto.
        """
        if self.missao_rapida and self.missao_modo == MODO_MISSAO_CARD:
            self.status("Missao rapida (CARD) ligada: clique numa missao do "
                        "card para marcar. (Desligue o modo para editar o "
                        "personagem.)")
            return
        try:
            from janela_personagem import JanelaPersonagem
            JanelaPersonagem(self, dados.get("nome"))
        except Exception as e:
            falha("[Personagem] abrir a edicao", e)
            self.status(f"Erro ao abrir a edicao de {dados.get('nome')}: {e}")

    def _abrir_cartas(self, nome, peca):
        """Edicao rapida das cartas de uma peca do Void (15.3)."""
        try:
            from janela_cartas import JanelaCartas
            atual = getattr(self, "_janela_cartas", None)
            if atual is not None and atual.winfo_exists():
                # pedra incompleta: fica na peca atual ate completar
                if atual.pedra_valida():
                    atual.mostrar(nome, peca)
                atual.lift()
                return atual
            self._janela_cartas = JanelaCartas(self, nome, peca)
            return self._janela_cartas
        except Exception as e:
            falha("[Cartas] abrir a edicao", e)
            self.status(f"Erro ao abrir as cartas de {nome}: {e}")
            return None

    def _atualizar_card(self, nome):
        """Redesenha o card de um personagem (edicao ao vivo)."""
        for card in getattr(self, "cards_personagem", []):
            if card.dados.get("nome") == str(nome):
                try:
                    # rebuild os dados a partir dos dataframes (podem ter mudado)
                    card.atualizar(self._dados_personagem(str(nome)))
                    # o Ataque Total ou uma dungeon podem ter mudado: refaz
                    # a ordem e o filtro na hora
                    self._reordenar_cards()
                    # o card redesenhado nasce por cima: a barra volta ao topo
                    self._elevar_abas()
                    return True
                except Exception as e:
                    falha("[Personagem] redesenhar o card", e)
                    return False
        return False

    def _redesenhar_cards(self):
        """Apaga os cards atuais e desenha a grade de novo (com filtros)."""
        for card in getattr(self, "cards_personagem", []):
            for item in getattr(card, "_itens", []):
                try:
                    self.canvas.delete(item)
                except tk.TclError:
                    pass                      # janela ja fechada
                except Exception:
                    falha("apagar os cards")
        self._desenhar_cards()

    def _atualizar_todos_os_cards(self):
        """Redesenha TODOS os cards de personagem (os dados podem ter mudado).

        Necesario quando uma acao mexe em varios personagens de uma vez
        (ex.: zerar as dungeons semanais) - senao os cards ficam com o
        retrato antigo.
        """
        for card in getattr(self, "cards_personagem", []):
            nome = card.dados.get("nome")
            if nome is None:
                continue
            try:
                card.atualizar(self._dados_personagem(str(nome)))
            except Exception as erro:
                falha("[Card] redesenhar o card", erro)
        self._reordenar_cards()

    # ------------------------------------------------------------ textos ----
    def _aplicar_icone(self):
        """Icone da janela (o .ico do app, em todas as abas)."""
        caminhos.aplicar_icone(self)

    def _fonte(self, tamanho, peso="normal", familia="Segoe UI"):
        return (familia, self.lay.f(tamanho), peso)

    def _foto(self, imagem):
        """Cria um PhotoImage GUARDANDO a referencia (senao o GC apaga)."""
        if not hasattr(self, "_fotos_extra"):
            self._fotos_extra = {}
        chave = f"extra_{len(self._fotos_extra)}"
        foto = ImageTk.PhotoImage(imagem)
        self._fotos_extra[chave] = foto
        return foto

    def _fonte_obj(self, tamanho, peso="normal", familia="Segoe UI"):
        """Objeto Font do Tk (para medir textos)."""
        if not hasattr(self, "_fontes"):
            self._fontes = {}
        chave = (familia, self.lay.f(tamanho), peso)
        if chave not in self._fontes:
            self._fontes[chave] = tkfont.Font(family=familia,
                                              size=self.lay.f(tamanho),
                                              weight=peso)
        return self._fontes[chave]

    def _texto(self, x, y, texto, tamanho, cor=None, peso="normal",
               familia="Segoe UI", anchor="nw", **extra):
        return self.canvas.create_text(
            x, y, text=texto, font=self._fonte(tamanho, peso, familia),
            fill=cor or tv.CORES["texto"], anchor=anchor, **extra)

    def _texto_espacado(self, x, y, texto, tamanho, cor=None, espaco=2.2):
        """Texto com espacamento entre letras (o Tk nao tem tracking)."""
        fonte = self._fonte_obj(tamanho, "bold")
        cor = cor or tv.CORES["olho"]
        cursor = x
        for caractere in texto:
            self.canvas.create_text(cursor, y, text=caractere,
                                    font=self._fonte(tamanho, "bold"),
                                    fill=cor, anchor="nw")
            cursor += fonte.measure(caractere) + espaco * self.lay.s

    def _icone(self, nome, cx, cy, tamanho, cor=None, tags=()):
        """Desenha um icone (emoji assado pelo PIL) no canvas."""
        img = tv.icone(nome, tamanho, cor)
        photo = ImageTk.PhotoImage(img)
        self._fotos_icones = getattr(self, "_fotos_icones", {})
        self._fotos_icones[f"{nome}_{tamanho}_{cor}"] = photo
        return self.canvas.create_image(cx, cy, anchor="center", image=photo,
                                       tags=tags)

    def _desenhar_textos(self):
        """Desenha todo o texto da tela (cabecalho, botoes, cartoes)."""
        lay = self.lay
        self.itens_valores.clear()
        self.itens_botoes.clear()
        self.itens_texto_botao.clear()
        self.itens_destaque.clear()
        self.itens_hover.clear()
        self.canvas.delete("texto")
        self.canvas.delete("hit")

        # --- cabecalho ---------------------------------------------------
        x1, y1 = lay.ponto(tv.TITULO_LINHA1)
        self._texto(x1, y1, "Caminho da", 44, peso="bold",
                    familia="Segoe UI Black")

        x1, y1 = lay.ponto(tv.TITULO_LINHA2)
        self._texto(x1, y1, "Maestria", 44, peso="bold",
                    familia="Segoe UI Black")

        sx, sy = lay.ponto(tv.SUBTITULO)
        self._texto(sx, sy, "Seus personagens, equipamentos e progresso semanal",
                    15, cor=tv.CORES["suave"])
        self._texto(sx, sy + lay.h(26), "\u2014 tudo em um s\u00f3 lugar.", 15,
                    cor=tv.CORES["suave"])

        # --- botoes do cabecalho ----------------------------------------
        for chave, (icone, rotulo, caixa) in enumerate(
                tv.BOTOES_LINHA1 + tv.BOTOES_LINHA2):
            self._desenhar_botao(f"topo{len(self.itens_botoes)}", icone, rotulo,
                                 caixa, claro=(chave == 3))

        # --- bloco de importacao ----------------------------------------
        # (vazio por enquanto: o painel de vidro continua desenhado no cenario,
        #  guardando o espaco para outras ideias)
        if MOSTRAR_IMPORTACAO:
            ix, iy = lay.ponto(tv.IMPORT_TITULO)
            self._icone("entrada", ix + lay.f(9), iy + lay.f(9), lay.f(18))
            self._texto(ix + lay.f(25), iy, "Import updated workbook", 15,
                        peso="bold")

            dx, dy = lay.ponto(tv.IMPORT_DESCRICAO)
            self._texto(dx, dy, "Update saved characters from an .xlsx file. "
                        "Blank cells are left unchanged; unknown names are "
                        "skipped.", 11, cor=tv.CORES["suave"])

            # --- botao Import Excel (gradiente roxo, desenhado no canvas) -
            caixa_import = tv.IMPORT_BOTOES["importar"]
            largura_import = lay.w(caixa_import[2] - caixa_import[0])
            altura_import = lay.h(caixa_import[3] - caixa_import[1])
            gradiente = tv.botao_gradiente(tv.CORES["roxo"], largura_import,
                                           altura_import, raio=8)
            self._desenhar_botao("importar", "entrada", "Import Excel",
                                 caixa_import, fundo=gradiente,
                                 comando=self.importar_excel)

        # --- perfil (o painel de vidro vago do hero) ---------------------
        self._desenhar_perfil()

        # --- opcao do modo da Missao Rapida (check) ---------------------
        self._desenhar_chave_missao()

        # --- barra de filtros (acima dos cards) -------------------------
        self._desenhar_filtros()

        # --- cartoes ----------------------------------------------------
        for chave, titulo, subtitulo in tv.CARDS:
            caixa, _linha, _coluna = tv.posicao_do_cartao(chave)
            self._desenhar_cartao(chave, titulo, subtitulo, caixa)

    def _desenhar_botao(self, chave, icone, rotulo, caixa, claro=False,
                        fundo=None, comando=None, cor_texto=None):
        """Botao desenhado no canvas (icone + texto) + area de clique.

        O conteudo (icone + texto) e sempre CENTRALIZADO no botao e nunca
        ultrapassa as bordas: se nao couber, a fonte do texto diminui.
        `fundo` = imagem PIL do fundo do botao (ex.: gradiente roxo).
        """
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(caixa)
        centro_x = (x1 + x2) / 2
        centro_y = (y1 + y2) / 2
        largura_botao = x2 - x1

        tamanho_icone = lay.f(17)
        espaco = lay.f(7)
        margem = lay.f(12)

        # fonte do texto: encolhe ate caber dentro do botao
        tamanho_texto = 13
        largura_texto = 0
        while tamanho_texto >= 9:
            fonte = self._fonte_obj(tamanho_texto, "bold")
            largura_texto = fonte.measure(rotulo)
            if tamanho_icone + espaco + largura_texto <= largura_botao - 2 * margem:
                break
            tamanho_texto -= 1

        total = tamanho_icone + espaco + largura_texto
        inicio = centro_x - total / 2

        # fundo do botao (gradiente) ou destaque (estado ligado)
        if fundo is not None:
            foto = ImageTk.PhotoImage(fundo)
            self._fotos_botao = getattr(self, "_fotos_botao", {})
            self._fotos_botao[f"fundo_{chave}"] = foto
            self.canvas.create_image(x1, y1, anchor="nw", image=foto)

        # fundo VERDE do estado ATIVO (criado ANTES do icone/texto para
        # ficar atras deles)
        tamanho_verde = (max(1, int(x2 - x1)), max(1, int(y2 - y1)))
        verde = ImageTk.PhotoImage(tv.retangulo_alfa(
            cor=(34, 197, 94), alfa=255, tamanho=tamanho_verde, raio=10))
        self._fotos_destaque = getattr(self, "_fotos_destaque", {})
        self._fotos_destaque[f"verde_{chave}"] = verde
        item_verde = self.canvas.create_image(
            x1, y1, anchor="nw", image=verde, state="hidden")
        self.itens_verde[chave] = item_verde

        cor_icone = (28, 21, 51, 255) if claro else (255, 255, 255, 255)
        self._icone(icone, inicio + tamanho_icone / 2, centro_y, tamanho_icone,
                    cor_icone)
        item_texto = self._texto(inicio + tamanho_icone + espaco, centro_y, rotulo,
                                 tamanho_texto,
                                 cor=cor_texto or (tv.CORES["botao_claro_texto"]
                                                   if claro else tv.CORES["texto"]),
                                 anchor="w")

        # destaque (estado "ligado")
        destaque = ImageTk.PhotoImage(tv.retangulo_alfa(
            tamanho=(max(1, int(x2 - x1)), max(1, int(y2 - y1)))))
        self._fotos_destaque = getattr(self, "_fotos_destaque", {})
        self._fotos_destaque[chave] = destaque
        item_destaque = self.canvas.create_image(
            x1, y1, anchor="nw", image=destaque, state="hidden")

        # hover (clareia o botao ao passar o mouse)
        hover = ImageTk.PhotoImage(tv.retangulo_alfa(
            cor=(255, 255, 255), alfa=26,
            tamanho=(max(1, int(x2 - x1)), max(1, int(y2 - y1)))))
        self._fotos_destaque[f"hover_{chave}"] = hover
        item_hover = self.canvas.create_image(
            x1, y1, anchor="nw", image=hover, state="hidden")

        # area de clique (invisivel, fica por cima do texto)
        item = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="",
                                            tags=("hit", f"botao:{chave}"))
        if comando is not None:
            self.canvas.tag_bind(item, "<Button-1>", lambda e, c=comando: c())
        else:
            self.canvas.tag_bind(item, "<Button-1>",
                                 lambda evento, c=chave: self._clic_botao(c))
        self.canvas.tag_bind(item, "<Enter>",
                             lambda e, c=chave: self._hover_botao(c, True))
        self.canvas.tag_bind(item, "<Leave>",
                             lambda e, c=chave: self._hover_botao(c, False))
        self.itens_botoes[chave] = item
        self.itens_texto_botao[chave] = item_texto
        self.itens_destaque[chave] = item_destaque
        self.itens_hover[chave] = item_hover

    # ------------------------------------------------------------ perfil ----
    def _desenhar_perfil(self):
        """Desenha o perfil no painel de vidro vago do hero."""
        # apaga o desenho anterior (senao os itens se acumulam a cada
        # atualizacao e o texto fica sobreposto)
        try:
            self.canvas.delete("perfil")
            self.canvas.delete("perfil_colecao")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("apagar o perfil")
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(tv.PERFIL_PAINEL)
        cx, cy, raio = lay.ponto(tv.PERFIL_AVATAR[:2]) + (lay.f(tv.PERFIL_AVATAR[2]),)
        tx, ty = lay.ponto(tv.PERFIL_TEXTO)
        icx, icy = lay.ponto(tv.PERFIL_ICONE)

        # --- o icone do nivel (a direita, no TAMANHO do badge) ----------
        # os PNGs do usuario tem ~1 MB: o cache evita carregar e
        # redimensionar a imagem a cada redesenho da tela
        caminho_icone = self._icone_do_chaser()
        if caminho_icone:
            try:
                lado = lay.f(tv.PERFIL_ICONE_LADO)
                chave = (caminho_icone, os.path.getmtime(caminho_icone), lado)
                cache = getattr(self, "_cache_icone_chaser", None)
                if cache is None:
                    cache = {}
                    self._cache_icone_chaser = cache
                arte = cache.get(chave)
                if arte is None:
                    arte = tv.icone_chaser(caminho_icone, lado, 0.7)
                    cache.clear()
                    cache[chave] = arte
                self.canvas.create_image(icx, icy, anchor="center",
                                         image=self._foto(arte),
                                         tags=("perfil",))
            except Exception:
                falha("desenhar o icone do chaser")

        # --- a foto (circulo): uma das 25 imagens de perfil ------------
        try:
            caminho_foto = self._foto_do_perfil()
            if caminho_foto:
                arte = tv.avatar_circular(caminho_foto, lay.f(96))
            else:
                arte = tv.avatar_circular(None, lay.f(96))
                from PIL import ImageDraw
                inicial = (self.perfil_nick
                           or (self.email_usuario or "").split("@")[0]
                           or "?")[:1].upper()
                ImageDraw.Draw(arte).text(
                    (lay.f(96) / 2, lay.f(96) / 2), inicial,
                    fill=(210, 200, 240, 255), anchor="mm")
            self.canvas.create_image(cx, cy, anchor="center", image=self._foto(arte),
                                    tags=("perfil",))
        except Exception:
            falha("desenhar o avatar do perfil")

        # --- a barra de EXP: o % ate o proximo distintivo -----------------
        # (1-99, 100-199...: nivel 5 = 5%, faltam 95 para o 100)
        # a ALTURA e um tamanho (lay.h), nao uma coordenada: passar por
        # lay.caixa somava o deslocamento vertical e, em 900 px de altura,
        # a barra crescia para fora do painel
        bx1, by1, bx2, _ = tv.PERFIL_EXP
        ex1, ey1 = lay.x(bx1), lay.y(by1)
        largura_total = max(8, int(lay.w(bx2 - bx1)))
        eh = max(12, int(lay.h(tv.PERFIL_EXP[3])))
        percentual, proximo = progresso_exp(self.nivel_chaser)
        # do 900 ao 999 a barra continua subindo; so no 999 aparece o MAX
        self._texto_exp = (f"{percentual:.0f}%" if percentual < 100
                           else "100%  ·  MÁX")
        self.canvas.create_image(ex1, ey1, anchor="nw", tags=("perfil",),
                                 image=self._foto(tv.barra_exp(
                                     largura_total, eh, percentual,
                                     self._texto_exp)))
        legenda_y = ey1 + eh + lay.h(5)
        self._texto(ex1, legenda_y, "EXP", 11, cor=tv.CORES["texto"],
                    peso="bold", tags=("perfil",))
        if proximo is None:
            dica = "Distintivo máximo alcançado"
        else:
            faltam = proximo - int(self.nivel_chaser or 0)
            dica = (f"Próximo distintivo: Lv. {proximo}  ·  "
                    f"falta{'m' if faltam > 1 else ''} {faltam}")
        self._texto(ex1 + largura_total, legenda_y, dica, 11,
                    cor=tv.CORES["suave"], peso="bold", anchor="ne",
                    tags=("perfil",))

        # --- o texto: "Lv. <nivel> - <nick>" -----------------------------
        nivel = self.nivel_chaser
        nick = self.perfil_nick or (self.email_usuario or "").split("@")[0] or "?"
        fonte_texto = self._fonte_obj(18, "bold")
        self._texto(tx, ty, "Lv.", 18, cor=tv.CORES["texto"], peso="bold",
                    tags=("perfil",))
        cursor = tx + fonte_texto.measure("Lv.") + 8
        self._texto(cursor, ty, str(nivel), 18, cor=tv.CORES["laranja"],
                    peso="bold", tags=("perfil",))
        cursor += fonte_texto.measure(str(nivel)) + 10
        self._texto(cursor, ty, "-", 18, cor=tv.CORES["olho"], peso="bold",
                    tags=("perfil",))
        cursor += fonte_texto.measure("-") + 10
        self._texto(cursor, ty, nick, 18, cor=tv.CORES["texto"], peso="bold",
                    tags=("perfil",))
        self._texto(tx, ty + lay.f(28),
                    "Clique para abrir o perfil e editar", 11,
                    cor=tv.CORES["olho"], tags=("perfil",))

        # --- a area clicavel --------------------------------------------
        self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="",
                                     tags=("perfil",))
        self._desenhar_colecao()
        self.canvas.tag_bind("perfil", "<Button-1>",
                             lambda e: self._abrir_perfil())
        self.canvas.tag_bind("perfil", "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind("perfil", "<Leave>",
                             lambda e: self.canvas.configure(cursor=""))

    def _desenhar_colecao(self):
        """A colecao de cartas (15.4) no painel do perfil: um bloco no vao
        entre a barra de EXP e o distintivo. Clicar abre a edicao (e nao o
        perfil)."""
        lay = self.lay
        tag = "perfil_colecao"
        x1, y1, x2, y2 = lay.caixa(tv.PERFIL_COLECAO)
        largura, altura = int(x2 - x1), int(y2 - y1)
        self.canvas.create_image(
            x1, y1, anchor="nw", tags=(tag,),
            image=self._foto(tv.retangulo_alfa(
                cor=(28, 22, 52), alfa=150, tamanho=(largura, altura),
                raio=lay.f(12))))
        cx = x1 + largura / 2
        self._texto(cx, y1 + lay.h(12), "COLEÇÃO", 10, cor=tv.CORES["suave"],
                    peso="bold", anchor="n", tags=(tag,))
        self._texto(cx, y1 + lay.h(30), "DE CARTAS", 10, cor=tv.CORES["suave"],
                    peso="bold", anchor="n", tags=(tag,))
        valor = f"{int(self.colecao_cartas or 0):,}".replace(",", ".")
        self._texto(cx, y1 + lay.h(47), valor, 20, cor=tv.CORES["texto"],
                    peso="bold", anchor="n", tags=(tag,))
        maximo = f"{COLECAO_CARTAS_MAXIMO:,}".replace(",", ".")
        self._texto(cx, y1 + lay.h(82), f"de {maximo}", 10,
                    cor=tv.CORES["olho"], anchor="n", tags=(tag,))
        self.canvas.tag_raise(tag)
        self.canvas.tag_bind(tag, "<Button-1>", lambda e: self._abrir_colecao())
        self.canvas.tag_bind(tag, "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind(tag, "<Leave>",
                             lambda e: self.canvas.configure(cursor=""))

    def _foto_do_perfil(self):
        """Caminho da foto escolhida (uma das 25 de assets/perfil/)."""
        if not self.perfil_personagem:
            return None
        pasta = os.path.join(caminhos.assets_dir(), "assets", tv.PASTA_PERFIL)
        base = str(self.perfil_personagem).strip()
        for nome in (f"{base.lower()}_icon.png", f"{base}_icon.png"):
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho
        return None

    def _icone_do_chaser(self):
        """Caminho do icone do nivel do chaser (cl1.png, cl100.png, ...)."""
        nivel = max(1, int(self.nivel_chaser or 1))
        # 1-99 -> cl1.png | 100-199 -> cl100.png | 200-299 -> cl200.png ...
        marco = 1 if nivel < 100 else (nivel // 100) * 100
        pasta = os.path.join(caminhos.assets_dir(), "assets", tv.PASTA_CHASER)
        for nome in (f"cl{marco}.png", f"cl{marco}.jpg", f"cl{marco}.webp"):
            caminho = os.path.join(pasta, nome)
            if os.path.exists(caminho):
                return caminho
        return None

    def _abrir_perfil(self):
        """Abre a janela 'Minha conta'."""
        if self._janela_perfil is not None:
            try:
                self._janela_perfil.lift()
                self._janela_perfil.focus_force()
                return self._janela_perfil
            except tk.TclError:
                self._janela_perfil = None
            except Exception:
                falha("trazer a janela de perfil")
                self._janela_perfil = None
        try:
            from janela_perfil import JanelaPerfil
            self._janela_perfil = JanelaPerfil(self)
            return self._janela_perfil
        except Exception as erro:
            falha("[Perfil] abrir", erro)
            self.status(f"Erro ao abrir o perfil: {erro}")
            return None

    def _abrir_doacao(self):
        """Abre (ou fecha) o painel lateral de doacao."""
        if self._painel_doacao is not None:
            try:
                if self._painel_doacao.winfo_exists():
                    self._painel_doacao.fechar()
                    self._painel_doacao = None
                    return None
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("fechar o painel de doacao")
            self._painel_doacao = None
        try:
            from janela_doacao import PainelDoacao
            self._painel_doacao = PainelDoacao(self)
            return self._painel_doacao
        except Exception as erro:
            falha("[Doacao] abrir o painel", erro)
            self.status(f"Erro ao abrir o painel de apoio: {erro}")
            return None

    def _salvar_perfil(self):
        """Grava o nick/avatar no Supabase (se as colunas existirem)."""
        if not self.usar_supabase or not self.user_id:
            return False
        try:
            from supabase_db import salvar_perfil
            return salvar_perfil(self.supabase, self.user_id,
                                 {"nick": self.perfil_nick,
                                  "avatar": (self.perfil_personagem
                                             or self.perfil_avatar or None)})
        except Exception as erro:
            falha("[Perfil] salvar", erro)
            return False

    def _ler_perfil(self):
        """Le o nick/avatar do Supabase."""
        if not self.usar_supabase or not self.user_id:
            return
        try:
            from supabase_db import ler_perfil
            self._aplicar_perfil(ler_perfil(self.supabase, self.user_id))
        except Exception as erro:
            falha("[Perfil] ler", erro)

    def _aplicar_perfil(self, dados):
        """Nick/avatar (do Supabase ou da copia offline)."""
        try:
            if not dados:
                return
            if dados.get("nick"):
                self.perfil_nick = str(dados["nick"])
            if dados.get("avatar"):
                valor = str(dados["avatar"])
                # o novo formato e o NOME do personagem (elesis, lire...);
                # o formato antigo (base64) ainda e aceito
                if len(valor) < 40:
                    self.perfil_personagem = valor
                else:
                    self.perfil_avatar = valor
                    try:
                        from janela_perfil import _de_base64
                        self.perfil_avatar_temp = _de_base64(self.perfil_avatar)
                    except Exception:
                        falha("decodificar o avatar do perfil")
                        self.perfil_avatar_temp = None
        except Exception as erro:
            falha("[Perfil] ler", erro)

    def fazer_logout(self):
        """Sai da conta (volta para a tela de login)."""
        try:
            self.status("Saindo da conta...")
            try:
                self.supabase.auth.sign_out()
            except Exception:
                falha("sair da conta (sign_out)")
            self.destroy()
        except Exception as erro:
            falha("[Perfil] logout", erro)

    def _desenhar_cartao(self, chave, titulo, subtitulo, caixa):
        """Titulo, valor e legenda de um cartao de estatistica."""
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(caixa)

        self._texto(x1 + lay.w(20), y1 + lay.h(14), titulo, 12,
                    cor=tv.CORES["suave"], peso="bold")

        if chave == "nivel":
            # campo + botao de confirmacao (desenhados no canvas para
            # rolarem junto com o conteudo)
            largura = lay.w(250)
            altura = lay.h(40)
            item_campo = self.canvas.create_image(
                x1 + lay.w(18), y1 + lay.h(34), anchor="nw",
                image=self._foto(tv.retangulo_alfa(
                    cor=(185, 166, 232), alfa=255,
                    tamanho=(largura, altura), raio=8)))
            item_valor = self.canvas.create_text(
                x1 + lay.w(18) + largura / 2, y1 + lay.h(34) + altura / 2,
                text=str(self.nivel_chaser), font=self._fonte(20, "bold"),
                fill="#241d3d", anchor="center")
            tamanho = lay.f(40)
            item_check = self.canvas.create_image(
                x2 - lay.w(18) - tamanho, y1 + lay.h(34), anchor="nw",
                image=self._foto(tv.retangulo_alfa(
                    cor=(139, 92, 246), alfa=255,
                    tamanho=(tamanho, tamanho), raio=10)))
            self.canvas.create_text(x2 - lay.w(18) - tamanho / 2,
                                    y1 + lay.h(34) + tamanho / 2, text="\u2713",
                                    font=self._fonte(18, "bold"), fill="#ffffff",
                                    anchor="center")
            # o valor e atualizado em _atualizar_cards
            self.itens_valores[chave] = (item_valor, None,
                                         x1 + lay.w(18), y1 + lay.h(34))
            # clicar no campo (ou no check) abre a edicao do nivel
            for item in (item_campo, item_valor, item_check):
                self.canvas.tag_bind(item, "<Button-1>",
                                     lambda e: self._abrir_nivel())
                self.canvas.tag_bind(item, "<Enter>",
                                     lambda e: self.canvas.configure(cursor="hand2"))
                self.canvas.tag_bind(item, "<Leave>",
                                     lambda e: self.canvas.configure(cursor=""))
            return

        item_valor = self._texto(x1 + lay.w(20), y1 + lay.h(34), "—", 30,
                                 peso="bold")
        item_legenda = None
        y_legenda = y1 + lay.h(50)
        if subtitulo:
            item_legenda = self._texto(x1 + lay.w(20), y_legenda, subtitulo,
                                       12, cor=tv.CORES["suave"], anchor="w")
        self.itens_valores[chave] = (item_valor, item_legenda,
                                     x1 + lay.w(20), y_legenda)

    def _posicionar_legenda(self, chave, valor):
        """Coloca a legenda ao lado do valor (a largura do valor varia)."""
        dados = self.itens_valores.get(chave)
        if not dados:
            return
        item_valor, item_legenda, x_valor, y_legenda = dados
        if item_legenda is None:
            return
        fonte = self._fonte_obj(30, "bold")
        largura = fonte.measure(valor)
        self.canvas.coords(item_legenda, x_valor + largura + self.lay.w(8),
                           y_legenda)

    def _hover_botao(self, chave, ativo):
        """Mostra/oculta o clareamento do botao ao passar o mouse."""
        item = self.itens_hover.get(chave)
        if item is not None:
            self.canvas.itemconfigure(item, state="normal" if ativo else "hidden")

    def _clic_botao(self, chave):
        """Clique nos botoes desenhados no canvas."""
        acoes = {
            "topo0": self._abrir_doacao,
            "topo1": self.procurar_atualizacao,     # botao "Versao X.Y.Z"
            "topo2": self.save_excel,
            "topo3": self.zerar_dungeons,
            "topo4": self.alternar_missao,
        }
        acao = acoes.get(chave)
        if acao:
            acao()

    # ------------------------------------------------------- widgets (cam 3) --
    def _construir_widgets(self):
        """Widgets com fundo SOLIDO (por cima do canvas)."""
        self.btn_escolher = None
        self.lbl_arquivo = None
        if MOSTRAR_IMPORTACAO:
            self.btn_escolher = ctk.CTkButton(
                self,
                text="ESCOLHER ARQUIVO",
                corner_radius=8,
                fg_color=tv.CORES["botao_escuro"],
                hover_color="#3a3358",
                text_color="#ffffff",
                font=ctk.CTkFont(size=12, weight="bold"),
                command=self.escolher_arquivo,
            )
            self.lbl_arquivo = ctk.CTkEntry(
                self,
                placeholder_text="Nenhum arquivo escolhido",
                corner_radius=8,
                fg_color=tv.CORES["entrada"],
                text_color=tv.CORES["entrada_texto"],
                placeholder_text_color="#6b6480",
                border_width=0,
                font=ctk.CTkFont(size=13),
                state="readonly",
            )

        self.entrada_chaser = None
        self.btn_chaser = None

        if self.mostrar_tabela:
            self.notebook = ctk.CTkTabview(self, fg_color="#14181d")
            self.notebook.place(relx=0, rely=0, relwidth=1, relheight=1)

    def _posicionar_widgets(self):
        """Posiciona os widgets solidos sobre o canvas."""
        lay = self.lay
        for widget, chave in ((self.btn_escolher, "escolher"),
                              (self.lbl_arquivo, "entrada")):
            if widget is None:
                continue
            x1, y1, x2, y2 = lay.caixa(tv.IMPORT_BOTOES[chave])
            self._posicionar(widget, x1, y1, x2 - x1, y2 - y1)

    @staticmethod
    def _posicionar(widget, x, y, largura, altura):
        """CTk nao aceita width/height no place(): ajusta no configure."""
        try:
            widget.configure(width=max(1, int(largura)), height=max(1, int(altura)))
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("posicionar widget")
        widget.place(x=int(x), y=int(y))

    # ---------------------------------------------------------- status ------
    def status(self, texto):
        self.status_var.set(str(texto))
        try:
            if hasattr(self, "_item_status"):
                self.canvas.itemconfig(self._item_status, text=str(texto))
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("atualizar a barra de status")

    def _sair(self):
        # offline, a alteracao ja fica guardada no PC (vai depois)
        if self.modified and not self._salvo_neste_pc() and                 not messagebox.askyesno("Sair", "Existem alteracoes nao salvas. Deseja mesmo sair?"):
            return
        self.quit_app()

    def quit_app(self):
        self._liberar_recursos()
        self.destroy()

    def _liberar_recursos(self):
        """Solta as imagens do Tk antes de destruir a janela.

        Sem isso o ImageTk.PhotoImage e finalizado depois do interpretador Tk
        e o processo morre com "alloc: invalid block" ao fechar.
        """
        try:
            self.canvas.delete("all")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("limpar o canvas")
        for atributo in ("cenario_tk",):
            if hasattr(self, atributo):
                try:
                    setattr(self, atributo, None)
                except tk.TclError:
                    pass                      # janela ja fechada
                except Exception:
                    falha("liberar imagens")
        if hasattr(self, "_fotos_icones"):
            self._fotos_icones.clear()
        if hasattr(self, "_fotos_destaque"):
            self._fotos_destaque.clear()


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Treeview moderno


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from login import abrir_aplicativo
    abrir_aplicativo()

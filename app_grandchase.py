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
import sys
import time
import gc
import queue
import threading
import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk
from tkinter import font as tkfont
from PIL import Image, ImageTk, ImageFilter

import customtkinter as ctk
import pandas as pd
import openpyxl

# ---------------------------------------------------------------------------
# Supabase
# ---------------------------------------------------------------------------
from supabase_db import get_supabase, carregar_personagens, upsert_personagem, \
    carregar_pecas_void, upsert_peca_void, carregar_acessorios_titulo, \
    upsert_acessorio, carregar_semanais, upsert_semanal, exportar_para_excel, \
    garantir_estrutura, colunas_salvaveis, salvar_conta, COLUNAS
from opcoes import obter_opcoes, coluna_banco, canonizar_aba, normalizar, chave_semanal
import tema_visual as tv
import caminhos
from card_personagem import (CardPersonagem, LARGURA as CARD_LARGURA,
                              ESCALA_MAX, TORRE_MAX,
                              ALTURA_CARD_BASE, _fracao,
                              DUNGEONS as DUNGEONS_CARD)

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

# ------------------------------------------------------------ filtros ----
# (chave, rotulo) de cada opcao dos filtros
# ⚠ as chaves aqui tem que ser IGUAIS as de card_personagem.DUNGEONS
# (normalizadas: sem acento, sem espaco e sem underscore). Com o
# underscore a opcao nunca era encontrada nos dados e o filtro nao
# filtrava nada.
FILTRO_MAZMORRAS = [
    ("void123", "Vazio 1, 2 e 3"),
    ("void4", "Vazio 4"),
    ("caminhoabissal", "Caminho Abissal"),
    ("torredasilusoes", "Torre das Ilusões"),
]
FILTRO_VOID = [
    ("vazio_uni", "Vazio Unificado"),
    ("vazio_apo", "Vazio Apocalipse"),
]
FILTRO_PROGRESSO = [
    ("despertar", "Não completou o despertar"),
    ("libertacao", "Não completou a libertação"),
]

# Modos da Missao Rapida (apenas UM por vez)
MODO_MISSAO_JANELA = "janela"   # o painel flutuante marca as missoes
MODO_MISSAO_CARD = "card"      # clicar no chip do card marca

# Nivel do Chaser: UM valor por conta (todos os personagens). Antes era uma
# constante; agora vem do banco (coluna user_characters.nivel_chaser) e pode
# ser alterado na tela principal.
NIVEL_CHASER_PADRAO = 385
COLUNA_NIVEL = "Nível do Chaser"

# Abas de dados conhecidas (chaves de self.dfs)
ABA_GERAL = "Geral"
ABA_PECAS = "Peças (Void)"
ABA_ACESSORIOS = "Acessórios Título"
ABA_SEMANAIS = "Semanais"

# Rotulos amigaveis para as colunas do banco (chave normalizada -> rotulo)
ROTULOS_COLUNAS = {
    "charactername": "Nome",
    "poder": "Poder",
    "torredasilusoes": "Torre Das Ilusões",
    "vaziouni": "Vazio Uni.",
    "vazioapo": "Vazio Apo.",
    "libertacao": "Libertação",
    "nucleo": "Núcleo",
    "nucleosepicos": "Núcleos Épicos+",
    "arma": "Arma",
    "asas": "Asas",
    "botas": "Botas",
    "calca": "Calça",
    "capa": "Capa",
    "cota": "Cota",
    "elmo": "Elmo",
    "escudos": "Escudos",
    "facas": "Facas",
    "luvas": "Luvas",
    "mascara": "Máscara",
    "diadema": "Diadema",
    "anel": "Anel",
    "brinco": "Brinco",
    "piercing": "Piercing",
    "tornozeleira": "Tornozeleira",
    "titulo": "Título",
    "fornalhainfernal": "Fornalha Infernal",
    "altardarunha": "Altar da Ruína",
    "void123": "Void ( 1, 2 e 3 )",
    "void4": "Void 4",
    "caminhoabissal": "Caminho Abissal",
    "terradojulgamento": "Terra do Julgamento",
    # campos novos (13/11) — ATENCAO: a chave e o nome normalizado da COLUNA
    # do banco ("fragmento_vazio_disperso" -> "fragmentovaziodisperso")
    "nucleosdimensionais": "Núcleos Dimensionais",
    "fragmentovaziodisperso": "Fragmento do Vazio Disperso",
    "libertacaonucleos": "Libertação Núcleos",
    "libertacaoepicos": "Libertação Épicos+",
    "nivelchaser": "Nível do Chaser",
}

BASE_DIR = caminhos.app_dir()
BACKGROUND_PATH = caminhos.fundo_principal()
EXCEL_DEFAULT = caminhos.planilha_padrao()
DB_FILE = caminhos.banco_sqlite()
LOG_PATH = caminhos.arquivo_log()


def _registrar(mensagem):
    """Print + log em arquivo (o .exe roda sem console).

    ⚠ No executavel SEM console o `sys.stdout` e None → o `print` levanta
    excecao e o log nunca era gravado. Por isso o print vai protegido.
    """
    try:
        print(mensagem)
    except Exception:
        pass
    if getattr(sys, "frozen", False):
        try:
            with open(LOG_PATH, "a", encoding="utf-8") as arquivo:
                arquivo.write(f"{time.strftime('%H:%M:%S')} {mensagem}\n")
        except Exception:
            pass


def _colunas_conhecidas(df, logica):
    """Colunas do dataframe que existem de verdade na tabela do banco."""
    if df is None or df.empty:
        return []
    permitidas = {coluna_banco(c) for c in COLUNAS.get(logica, [])}
    if logica == "semanais":
        permitidas.add(coluna_banco("torre_das_ilusoes"))
    if logica == "personagens":
        permitidas.add(coluna_banco("nivel_chaser"))
    achadas = []
    for coluna in df.columns:
        if coluna in ("Nome", "id", "character_id"):
            continue
        if coluna_banco(coluna) in permitidas:
            achadas.append(coluna)
    return achadas


def _rotular_colunas(df):
    """Troca os nomes do banco (snake_case) pelos rotulos da planilha."""
    if df is None or df.empty:
        return df
    troca = {}
    for coluna in df.columns:
        rotulo = ROTULOS_COLUNAS.get(coluna_banco(coluna))
        if rotulo and coluna != rotulo:
            troca[coluna] = rotulo
    return df.rename(columns=troca) if troca else df


def _verdadeiro(valor) -> bool:
    """'VERDADEIRO' / 'Verdadeiro' / True / 1 -> True."""
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    texto = str(valor).strip().lower()
    return texto in ("verdadeiro", "true", "1", "t", "sim", "x")


class GrandChaseApp(ctk.CTk):
    def __init__(self, user=None, supabase=None):
        super().__init__()

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
        self.tree_refs = {}
        self.abas_criadas = []
        self.modified = False
        self.supabase = supabase or get_supabase()
        self.usar_supabase = self.user_id is not None
        self.arquivo_selecionado = None
        self.missao_rapida = False
        self.nivel_chaser = NIVEL_CHASER_PADRAO
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

        # === Camada 2: canvas (imagem do cenario + textos) ===============
        self.canvas = tk.Canvas(self, bg="#191334", highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._construir_widgets()
        self._montar_tela()

        self.after(120, self._redesenhar)
        self.bind("<Configure>", self._ao_redimensionar)
        # rolagem da pagina (cards abaixo do "Caminho da Maestria")
        self.canvas.bind("<MouseWheel>", self._rolar)
        self.bind("<KeyPress>", self._atalho_missao)
        self.canvas.configure(yscrollincrement=40)

        # Carrega dados automaticamente
        if self.usar_supabase:
            self.carregar_do_supabase()
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
            except Exception:
                pass
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
            _registrar(f"[Cenario] Erro ao redesenhar: {e}")

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
        except Exception:
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
            _registrar(f"[Cenario] Erro ao gerar: {e}")

        self._desenhar_textos()
        self._desenhar_cards()
        self._posicionar_widgets()
        self._atualizar_cards()

    # ------------------------------------------------------------ rolagem --
    def _rolar(self, evento):
        """Rola a pagina; o cenario (arte) continua fixo."""
        passos = -1 if evento.delta > 0 else 1
        self.canvas.yview_scroll(passos, "units")
        self._fixar_cenario()

    def _fixar_cenario(self):
        """Mantem a arte de fundo parada enquanto o conteudo rola."""
        item = getattr(self, "_item_cenario", None)
        if item:
            try:
                self.canvas.coords(item, 0, self.canvas.canvasy(0))
            except Exception:
                pass

    # ------------------------------------------------------------- cards ---
    def _dados_personagem(self, nome):
        """Monta o dicionario de dados de um personagem (vindo do Supabase)."""
        geral = self.dfs.get(ABA_GERAL)
        pecas = self.dfs.get(ABA_PECAS)
        acess = self.dfs.get(ABA_ACESSORIOS)
        sem = self.dfs.get(ABA_SEMANAIS)

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

        return {
            "nome": nome,
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
                    ao_missao=self.alternar_missao_rapida)
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
            _registrar(f"[Personagem] Erro ao abrir a edicao: {e}")
            self.status(f"Erro ao abrir a edicao de {dados.get('nome')}: {e}")

    def _atualizar_card(self, nome):
        """Redesenha o card de um personagem (edicao ao vivo)."""
        for card in getattr(self, "cards_personagem", []):
            if card.dados.get("nome") == str(nome):
                try:
                    # rebuild os dados a partir dos dataframes (podem ter mudado)
                    card.atualizar(self._dados_personagem(str(nome)))
                    return True
                except Exception as e:
                    _registrar(f"[Personagem] Erro ao redesenhar o card: {e}")
                    return False
        return False

    def _redesenhar_cards(self):
        """Apaga os cards atuais e desenha a grade de novo (com filtros)."""
        for card in getattr(self, "cards_personagem", []):
            for item in getattr(card, "_itens", []):
                try:
                    self.canvas.delete(item)
                except Exception:
                    pass
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
                _registrar(f"[Card] Erro ao redesenhar o card: {erro}")

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
        except Exception:
            pass
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
                pass

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
            pass

        # --- a barra de EXP (preenche com o nivel do chaser) -----------
        ex1, ey1, ex2, eh = lay.caixa(tv.PERFIL_EXP)
        largura_total = max(1, ex2 - ex1)
        percentual = min(100.0, max(0.0, float(self.nivel_chaser or 0) / 10.0))
        self.canvas.create_image(ex1, ey1, anchor="nw", image=self._foto(
            tv.retangulo_alfa(cor=(38, 34, 62), alfa=255,
                              tamanho=(largura_total, eh), raio=eh / 2)))
        if percentual > 0:
            largura_preenchida = max(eh, largura_total * percentual / 100.0)
            self.canvas.create_image(ex1, ey1, anchor="nw", image=self._foto(
                tv.botao_gradiente("#a3e635", largura_preenchida, eh,
                                   raio=eh / 2)))
        self._texto(ex1, ey1 + eh + 6, "EXP", 11, cor=tv.CORES["olho"],
                    peso="bold", tags=("perfil",))
        self._texto(ex2, ey1 + eh + 6, f"{percentual:.1f}%", 11,
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
        item = self.canvas.create_rectangle(x1, y1, x2, y2, fill="", outline="",
                                            tags=("perfil",))
        self.canvas.tag_bind("perfil", "<Button-1>",
                             lambda e: self._abrir_perfil())
        self.canvas.tag_bind("perfil", "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind("perfil", "<Leave>",
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
            except Exception:
                self._janela_perfil = None
        try:
            from janela_perfil import JanelaPerfil
            self._janela_perfil = JanelaPerfil(self)
            return self._janela_perfil
        except Exception as erro:
            _registrar(f"[Perfil] Erro ao abrir: {erro}")
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
            except Exception:
                pass
            self._painel_doacao = None
        try:
            from janela_doacao import PainelDoacao
            self._painel_doacao = PainelDoacao(self)
            return self._painel_doacao
        except Exception as erro:
            _registrar(f"[Doacao] Erro ao abrir o painel: {erro}")
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
            _registrar(f"[Perfil] Erro ao salvar: {erro}")
            return False

    def _ler_perfil(self):
        """Le o nick/avatar do Supabase."""
        if not self.usar_supabase or not self.user_id:
            return
        try:
            from supabase_db import ler_perfil
            dados = ler_perfil(self.supabase, self.user_id)
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
                        self.perfil_avatar_temp = None
        except Exception as erro:
            _registrar(f"[Perfil] Erro ao ler: {erro}")

    def fazer_logout(self):
        """Sai da conta (volta para a tela de login)."""
        try:
            self.status("Saindo da conta...")
            try:
                self.supabase.auth.sign_out()
            except Exception:
                pass
            self.destroy()
        except Exception as erro:
            _registrar(f"[Perfil] Erro no logout: {erro}")

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
            "topo1": lambda: self.status("Instalar aplicativo: em breve."),
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

        if MOSTRAR_TABELA:
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
        except Exception:
            pass
        widget.place(x=int(x), y=int(y))

    # ---------------------------------------------------------- status ------
    def status(self, texto):
        self.status_var.set(str(texto))
        try:
            if hasattr(self, "_item_status"):
                self.canvas.itemconfig(self._item_status, text=str(texto))
        except Exception:
            pass

    # --------------------------------------------------- tema / arquivo -----
    def toggle_theme(self):
        modo = ctk.get_appearance_mode()
        novo = "light" if modo == "Dark" else "dark"
        ctk.set_appearance_mode(novo)
        self.status(f"Tema alterado para: {novo.capitalize()}")

    def escolher_arquivo(self):
        path = filedialog.askopenfilename(
            title="Selecionar planilha Excel",
            filetypes=[("Excel", "*.xlsx *.xls *.xlsm"), ("Todos", "*.*")]
        )
        if path:
            self.excel_path = path
            self.arquivo_selecionado = path
            nome = os.path.basename(path)
            if self.lbl_arquivo is not None:
                self.lbl_arquivo.configure(state="normal")
                self.lbl_arquivo.delete(0, "end")
                self.lbl_arquivo.insert(0, nome)
                self.lbl_arquivo.configure(state="readonly")
            self.load_excel(path)

    def importar_excel(self):
        if not self.arquivo_selecionado:
            if self.lbl_arquivo is not None:
                self.lbl_arquivo.configure(
                    placeholder_text="Selecione um arquivo primeiro")
            return
        self.load_excel(self.arquivo_selecionado)

    # ----------------------------------------------------- carregar Excel --
    def load_excel(self, path):
        try:
            xl = pd.ExcelFile(path)
            abas = xl.sheet_names

            self._limpar_abas()

            for aba in list(abas):
                df = xl.parse(aba)
                if "Nome" not in df.columns and len(df) and \
                        "Nome" in [str(v) for v in df.iloc[0].tolist()]:
                    df = xl.parse(aba, header=1)
                df = df.dropna(axis=1, how="all")
                if "Nome" not in df.columns and df.columns[0] != "Nome":
                    df.insert(0, "Nome", [f"Linha {i+1}" for i in range(len(df))])

                aba_can = canonizar_aba(aba)
                if aba_can in self.dfs:
                    continue
                df = _ordenar_colunas(df)
                self.dfs[aba_can] = df
                self.originals[aba_can] = df.copy()
                if MOSTRAR_TABELA:
                    self._criar_aba(aba_can, df)

            self.modified = False
            self._ler_nivel_chaser()
            self._atualizar_cards()
            self.status(f"Carregado: {os.path.basename(path)} | {len(abas)} abas | "
                        f"{sum(len(d) for d in self.dfs.values())} registros")
        except PermissionError:
            messagebox.showerror("Erro", "Feche o arquivo Excel antes de abri-lo.")
        except Exception as e:
            messagebox.showerror("Erro ao carregar Excel", str(e))

    def _limpar_abas(self):
        """Remove as abas do notebook e zera os dataframes."""
        if MOSTRAR_TABELA:
            for aba in list(self.abas_criadas):
                try:
                    self.notebook.delete(aba)
                except Exception:
                    pass
        self.abas_criadas.clear()
        self.dfs.clear()
        self.originals.clear()
        self.tree_refs.clear()

    # --------------------------------------------------- carregar Supabase --
    def carregar_do_supabase(self):
        try:
            self._limpar_abas()

            nota_estrutura = ""
            try:
                criado = garantir_estrutura(self.supabase, self.user_id)
                total = sum(v for k, v in criado.items()
                            if k != "erro" and isinstance(v, int))
                if total:
                    nota_estrutura = f" | estrutura criada: {total} linhas novas"
                elif criado.get("erro"):
                    nota_estrutura = (" | sem permissao para criar a estrutura "
                                      "(rode o SQL do HANDOFF.md)")
            except Exception:
                nota_estrutura = ""

            personagens = carregar_personagens(self.supabase, self.user_id)
            if not personagens:
                self.status("Nenhum personagem encontrado para o seu usuario. "
                            "Use 'Escolher arquivo' para importar dados." + nota_estrutura)
                return

            df_geral = _ordenar_colunas(_rotular_colunas(pd.DataFrame(personagens)))

            pecas = carregar_pecas_void(self.supabase, personagens)
            df_pecas = _ordenar_colunas(_rotular_colunas(pd.DataFrame(pecas))) \
                if pecas else pd.DataFrame()

            acessorios = carregar_acessorios_titulo(self.supabase, personagens)
            df_acess = _ordenar_colunas(_rotular_colunas(pd.DataFrame(acessorios))) \
                if acessorios else pd.DataFrame()

            semanais = carregar_semanais(self.supabase, personagens)
            df_sem = _ordenar_colunas(_rotular_colunas(pd.DataFrame(semanais))) \
                if semanais else pd.DataFrame()

            abas_dados = {
                ABA_GERAL: df_geral,
                ABA_PECAS: df_pecas,
                ABA_ACESSORIOS: df_acess,
                ABA_SEMANAIS: df_sem,
            }

            for nome, df in abas_dados.items():
                if df.empty:
                    continue
                self.dfs[nome] = df
                self.originals[nome] = df.copy()
                if MOSTRAR_TABELA:
                    self._criar_aba(nome, df)

            self.modified = False
            self._versao = 0
            self._ler_nivel_chaser()
            self._atualizar_cards()
            self._ler_preferencia()
            self._ler_ultimo_personagem()
            self._ler_perfil()
            total = sum(len(d) for d in self.dfs.values())
            self.status(f"Carregado do Supabase: {len(personagens)} personagens "
                        f"| {total} registros nas abas" + nota_estrutura)
        except Exception as e:
            messagebox.showerror("Erro Supabase", str(e))
            self.status("Erro ao conectar com Supabase")

    # ------------------------------------------------------ criar aba -------
    def _criar_aba(self, nome_aba, df):
        tab = self.notebook.add(nome_aba)
        self.abas_criadas.append(nome_aba)
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        busca_frame = ctk.CTkFrame(tab, fg_color="transparent")
        busca_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        busca_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(busca_frame, text="Buscar personagem:").pack(side="left", padx=(0, 6))
        var_busca = ctk.StringVar()
        ent_busca = ctk.CTkEntry(busca_frame, textvariable=var_busca,
                                 placeholder_text="digite o nome...")
        ent_busca.pack(side="left", fill="x", expand=True, padx=(0, 6))

        chk_todos = ctk.CTkCheckBox(busca_frame, text="Mostrar todos",
                                    command=lambda: self._refrescar_tabela(nome_aba, ""))
        chk_todos.pack(side="left")

        container = ttk.Frame(tab)
        container.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(0, weight=1)

        tree = ttk_treeview_moderno(container, df.columns)

        for _, row in self._linhas_visiveis(df, ""):
            tree.insert("", "end", values=list(row))

        def on_dbl(event, df_ref=df, aba=nome_aba):
            self._editar_celula(event, tree, df_ref, aba)

        tree.bind("<Double-1>", on_dbl)

        def filtrar(*args, tv_=tree, df_ref=df, sv=var_busca):
            termo = sv.get().lower()
            tv_.delete(*tv_.get_children())
            for _, row in self._linhas_visiveis(df_ref, termo):
                tv_.insert("", "end", values=list(row))

        var_busca.trace_add("write", filtrar)

        self.tree_refs[nome_aba] = {
            "tree": tree,
            "df": df,
            "container": container,
            "busca": var_busca,
        }

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
        except Exception:
            yview = (0.0, 1.0)
        self._reposicionar_cards()
        self._redesenhar_filtros()
        try:
            self.canvas.yview_moveto(yview[0])
        except Exception:
            pass

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
        except Exception:
            pass

    def _redesenhar_filtros(self):
        """Redesenha a barra de filtros (aparece o CHECK da opcao ativa)."""
        try:
            self.canvas.delete("filtros")
        except Exception:
            pass
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

    # ------------------------------------------------------ editar celula ---
    def _editar_celula(self, event, tree, df_ref, aba):
        item = tree.identify_row(event.y)
        col = tree.identify_column(event.x)
        if not item or not col:
            return

        col_idx = int(col.replace("#", "")) - 1
        if col_idx < 0 or col_idx >= len(df_ref.columns):
            return
        col_name = df_ref.columns[col_idx]
        if col_name in ("id", "character_id"):
            return
        valor_atual = tree.set(item, col_name)

        # A tabela pode estar filtrada (busca / Missao Rapida): a posicao do
        # item na arvore NAO e a posicao no dataframe -> traduz via a lista
        # de linhas visiveis.
        ref = self.tree_refs.get(aba) or {}
        var_busca = ref.get("busca")
        termo = var_busca.get() if var_busca is not None else ""
        visiveis = self._linhas_visiveis(df_ref, termo)
        posicao = tree.index(item)
        if posicao < 0 or posicao >= len(visiveis):
            return
        indice_df = visiveis[posicao][0]

        dlg = ctk.CTkToplevel(self)
        dlg.title(f"Editar - {col_name}")
        dlg.geometry("420x220")
        dlg.transient(self)
        dlg.grab_set()
        dlg.resizable(False, False)

        ctk.CTkLabel(dlg, text="Personagem:", font=ctk.CTkFont(weight="bold")).pack(pady=(20, 0))
        ctk.CTkLabel(dlg, text=tree.set(item, "Nome"), text_color="#9dd").pack(pady=(0, 10))

        ctk.CTkLabel(dlg, text=f"Campo: {col_name}", font=ctk.CTkFont(weight="bold")).pack(pady=(0, 5))
        ctk.CTkLabel(dlg, text=f"Valor atual: {valor_atual or '(vazio)'}").pack(pady=(0, 15))

        opcoes = obter_opcoes(aba, col_name)
        if opcoes:
            valores = ["(vazio)"] + list(opcoes)
            if valor_atual and valor_atual not in valores:
                valores.append(valor_atual)
            campo = ttk.Combobox(dlg, values=valores, state="readonly", width=36)
            campo.set(valor_atual)
            campo.pack(pady=5)
            campo.focus()

            def ler_valor():
                v = campo.get()
                return "" if v == "(vazio)" else v
            alvo = campo
        else:
            ent = ctk.CTkEntry(dlg, width=300)
            ent.insert(0, valor_atual)
            ent.pack(pady=5)
            ent.focus()
            ent.select_range(0, "end")

            def ler_valor():
                return ent.get()
            alvo = ent

        btns = ctk.CTkFrame(dlg, fg_color="transparent")
        btns.pack(pady=20)

        def salvar_celula():
            novo = ler_valor()
            tree.set(item, col_name, novo)
            # converte para o tipo da coluna (pandas 3 nao aceita string em int64)
            convertido = novo
            try:
                tipo = df_ref[col_name].dtype
                if getattr(tipo, "kind", "") in "iu" and str(novo).strip():
                    convertido = int(float(novo))
                elif getattr(tipo, "kind", "") == "f" and str(novo).strip():
                    convertido = float(novo)
                else:
                    convertido = tipo.type(novo)
            except Exception:
                convertido = novo
            try:
                df_ref.loc[indice_df, col_name] = convertido
            except Exception:
                df_ref[col_name] = df_ref[col_name].astype(object)
                df_ref.loc[indice_df, col_name] = novo
            self._marcar_modificado()
            self._atualizar_cards()
            self.status(f"Alterado: {col_name} = {novo}")
            dlg.destroy()

        ctk.CTkButton(btns, text="Salvar", fg_color="#2ecc71", hover_color="#27ae60",
                      command=salvar_celula).pack(side="left", padx=8)
        ctk.CTkButton(btns, text="Cancelar", command=dlg.destroy).pack(side="left", padx=8)

        alvo.bind("<Return>", lambda e: salvar_celula())
        alvo.bind("<Escape>", lambda e: dlg.destroy())

    # ------------------------------------------------------ refrescar tabela
    def _refrescar_tabela(self, nome_aba, termo):
        ref = self.tree_refs.get(nome_aba)
        if not ref:
            return
        tv_ = ref["tree"]
        df_ref = ref["df"]
        tv_.delete(*tv_.get_children())
        for _, row in self._linhas_visiveis(df_ref, termo):
            tv_.insert("", "end", values=list(row))

    # ---------------------------------------------------------- cartoes -----
    def _contar_verdadeiros(self, df, chave):
        """Conta as linhas 'Verdadeiro' da coluna (pelo nome logico do banco)."""
        coluna = _coluna_no_df(df, chave)
        if coluna is None:
            return 0
        return int(df[coluna].map(_verdadeiro).sum())

    def _despertar_completo(self):
        """Personagens com o DESPERTAR completo: Núcleos 13/13 e Épicos+ 9/9.

        Compara o VALOR (o numerador da fração), então funciona tanto para
        "9 / 9" (formato do dropdown novo) quanto para "9 / 13" (formato
        antigo da planilha, em que o denominador dos épicos+ estava errado).
        """
        df = self.dfs.get(ABA_GERAL)
        coluna_nucleo = _coluna_no_df(df, "nucleo")
        coluna_epicos = _coluna_no_df(df, "nucleos_epicos")
        if coluna_nucleo is None or coluna_epicos is None:
            return 0
        completos = 0
        for nucleo, epicos in zip(df[coluna_nucleo], df[coluna_epicos]):
            if _fracao(nucleo)[0] == 13 and _fracao(epicos)[0] == 9:
                completos += 1
        return completos

    def _libertacao_completo(self):
        """Personagens com a LIBERTAÇÃO completa (3 condições):

        1. o campo "Libertação" (estado) = VERDADEIRO
        2. Núcleos = 9/9
        3. Épicos+ = 4/4

        Se as colunas de progresso (libertacao_nucleos/libertacao_epicos)
        nao existirem na tabela (ex.: planilha antiga, modo local), conta
        apenas pelo estado — que era a regra antiga.
        """
        df = self.dfs.get(ABA_GERAL)
        col_estado = _coluna_no_df(df, "libertacao")
        col_nucleo = _coluna_no_df(df, "libertacao_nucleos")
        col_epicos = _coluna_no_df(df, "libertacao_epicos")
        if col_estado is None:
            return 0
        if col_nucleo is None or col_epicos is None:
            # sem as colunas de progresso: fica so o estado
            return int(df[col_estado].map(_verdadeiro).sum())
        completos = 0
        for estado, nucleos, epicos in zip(df[col_estado],
                                           df[col_nucleo], df[col_epicos]):
            if not _verdadeiro(estado):
                continue
            if _fracao(nucleos)[0] == 9 and _fracao(epicos)[0] == 4:
                completos += 1
        return completos

    def _poder_medio(self):
        df = self.dfs.get(ABA_GERAL)
        coluna = _coluna_no_df(df, "poder")
        if coluna is None:
            return None
        numeros = pd.to_numeric(df[coluna], errors="coerce").dropna()
        if numeros.empty:
            return None
        return float(numeros.mean())

    def _torre_concluida(self):
        """Personagens com a Torre das Ilusoes concluida."""
        df_sem = self.dfs.get(ABA_SEMANAIS)
        coluna = _coluna_no_df(df_sem, "torre_das_ilusoes")
        if coluna:
            return self._contar_verdadeiros(df_sem, "torre_das_ilusoes")
        df = self.dfs.get(ABA_GERAL)
        coluna = _coluna_no_df(df, "torre_das_ilusoes")
        if coluna is None:
            return 0
        valores = df[coluna].astype(str).str.strip()
        return int(valores.isin(("30 / 30", "30/30")).sum())

    def _atualizar_cards(self):
        """Recalcula os cards de estatistica a partir de self.dfs."""
        if not self.itens_valores:
            return
        df_sem = self.dfs.get(ABA_SEMANAIS)
        df_geral = self.dfs.get(ABA_GERAL)

        caminho = self._contar_verdadeiros(df_sem, "caminho_abissal")
        void123 = self._contar_verdadeiros(df_sem, "void_123")
        void4 = self._contar_verdadeiros(df_sem, "void_4")
        torre = self._torre_concluida()
        despertar = self._despertar_completo()
        libertacao = self._libertacao_completo()
        poder = self._poder_medio()
        nivel = self.nivel_chaser

        valores = {
            "caminho_abissal": str(caminho),
            "poder_medio": ("—" if poder is None else f"{poder:,.0f}".replace(",", ".")),
            "torre": str(torre),
            "void123": str(void123),
            "void4": str(void4),
            "nivel": str(nivel),
            "despertar": str(despertar),
            "libertacao": str(libertacao),
        }
        for chave, valor in valores.items():
            dados = self.itens_valores.get(chave)
            if not dados:
                continue
            item_valor = dados[0]
            self.canvas.itemconfig(item_valor, text=valor)
            self._posicionar_legenda(chave, valor)

    def valores_dos_cards(self):
        """Texto atual de cada card de estatistica (util para testes)."""
        valores = {}
        for chave, dados in self.itens_valores.items():
            try:
                valores[chave] = self.canvas.itemcget(dados[0], "text")
            except Exception:
                valores[chave] = ""
        return valores

    # ----------------------------------------------------- salvar Supabase --
    def salvar(self):
        """Salva os dados: no Supabase (conta logada) ou na planilha (local)."""
        if self.usar_supabase:
            self.salvar_supabase()
        else:
            self.save_excel()

    def _marcar_modificado(self):
        """Marca os dados como alterados (versiona para o salvamento em bg)."""
        self.modified = True
        self._versao += 1

    def _snapshot_dados(self):
        """Copia dos dataframes para enviar (sem depender da UI durante o envio)."""
        dados = {}
        for aba, df in self.dfs.items():
            if df is None or df.empty:
                continue
            limpo = df.astype(object).where(pd.notnull(df), None)
            dados[aba] = limpo.to_dict("records")
        return dados

    # ------------------------------------------------ nivel do chaser ----
    def _coluna_nivel(self, df):
        """Coluna do nivel do chaser no dataframe (None se nao existir)."""
        if df is None or df.empty:
            return None
        for coluna in df.columns:
            if coluna_banco(coluna) == "nivelchaser":
                return coluna
        return None

    def _ler_nivel_chaser(self):
        """Le o nivel do chaser do dataframe (um valor por conta)."""
        df = self.dfs.get(ABA_GERAL)
        if df is None or df.empty:
            self.nivel_chaser = NIVEL_CHASER_PADRAO
            return self.nivel_chaser
        coluna = self._coluna_nivel(df)
        if coluna is None:
            # a coluna ainda nao existe no banco: cria no dataframe (so e
            # gravada se a coluna existir de fato no Supabase)
            df[COLUNA_NIVEL] = NIVEL_CHASER_PADRAO
            self.nivel_chaser = NIVEL_CHASER_PADRAO
            return self.nivel_chaser
        for valor in df[coluna].tolist():
            if valor is None:
                continue
            texto = str(valor).strip()
            if texto in ("", "nan", "None"):
                continue
            try:
                self.nivel_chaser = max(0, int(float(texto.split(".")[0])))
            except (TypeError, ValueError):
                continue
            break
        return self.nivel_chaser

    def _nivel_no_banco(self):
        """A coluna user_characters.nivel_chaser existe de verdade?"""
        if not self.usar_supabase:
            return False
        try:
            from supabase_db import colunas_salvaveis
            return "nivelchaser" in colunas_salvaveis(self.supabase, "personagens")
        except Exception:
            return False

    def definir_nivel_chaser(self, valor):
        """Grava o nivel do chaser (um valor por conta) e salva no banco.

        O valor e um numero INTEIRO >= 0. O salvamento acontece em segundo
        plano (sem travar a tela e sem janela de aviso).
        """
        try:
            numero = int(str(valor).strip())
        except (TypeError, ValueError):
            return False
        if numero < 0:
            return False
        self.nivel_chaser = numero
        df = self.dfs.get(ABA_GERAL)
        if df is not None and not df.empty:
            coluna = self._coluna_nivel(df)
            if coluna is None:
                coluna = COLUNA_NIVEL
                df[coluna] = numero
            else:
                # um valor por conta: grava em todas as linhas
                df[coluna] = numero
        self._atualizar_cards()
        # o perfil do hero mostra o nivel: atualiza em tempo real
        self._desenhar_perfil()
        self._marcar_modificado()
        if self.usar_supabase:
            self._aviso_nivel = ("" if self._nivel_no_banco() else
                                 " | nivel_chaser: rode sql/nivel_chaser.sql "
                                 "no Supabase para gravar")
            self.salvar_supabase()
            return True
        self.status(f"Nivel do chaser: {numero}")
        return True

    def _abrir_nivel(self):
        """Abre a janela de edicao do nivel do chaser."""
        try:
            from janela_nivel import JanelaNivelChaser
            JanelaNivelChaser(self)
        except Exception as erro:
            _registrar(f"[Nivel] Erro ao abrir a edicao: {erro}")
            self.status(f"Erro ao abrir a edicao do nivel: {erro}")

    def salvar_supabase(self):
        """Envia as alteracoes ao Supabase em SEGUNDO PLANO.

        A interface continua utilizavel durante o envio e o resultado aparece
        na barra de status (sem nenhuma janela de aviso).
        """
        if not self.usar_supabase:
            self.status("Supabase nao esta ativado (modo local).")
            return
        if not self.modified:
            self.status("Nenhuma alteracao para salvar.")
            return
        if self._salvando:
            self._salvar_pendente = True
            self.status("Salvando… (o proximo salvamento ja esta na fila)")
            return

        self._salvando = True
        self._salvar_pendente = False
        self._versao_salva = self._versao
        self.status("Salvando no Supabase…")
        dados = self._snapshot_dados()

        # O GC nao pode rodar na thread de rede: ele pode finalizar um
        # tkinter.font.Font e travar o Tcl (GIL x Tcl). Desligamos durante o
        # envio e religamos na thread da UI.
        gc.collect()
        gc.disable()
        threading.Thread(target=self._salvar_em_segundo_plano, args=(dados,),
                         daemon=True).start()

    def _salvar_em_segundo_plano(self, dados):
        """Executa APENAS a parte de rede (nada de Tk nesta thread)."""
        try:
            resultado = salvar_conta(self.supabase, self.user_id, dados)
            self._fila_salvamento.put(("ok", resultado))
        except Exception as erro:
            self._fila_salvamento.put(("erro", erro))

    def _verificar_salvamento(self):
        """Le o resultado do salvamento (na thread da UI) e atualiza a tela."""
        try:
            while True:
                tipo, payload = self._fila_salvamento.get_nowait()
                self._aplicar_resultado_salvamento(tipo, payload)
        except queue.Empty:
            pass
        except Exception as erro:
            self.status(f"Erro ao ler o resultado do salvamento: {erro}")
        self.after(120, self._verificar_salvamento)

    def _aplicar_resultado_salvamento(self, tipo, payload):
        """Aplica o resultado do salvamento (status + cards), sem messagebox."""
        gc.enable()
        try:
            gc.collect()
        except Exception:
            pass

        self._salvando = False

        if tipo == "erro":
            self.status(f"Erro ao salvar no Supabase: {payload}")
            self.modified = True
            self._salvar_pendente = True
        else:
            salvos = payload.get("salvos") or {}
            perdidas = payload.get("perdidas") or []
            total = sum(salvos.values())
            if self._versao == self._versao_salva:
                # nada mudou durante o envio: pode marcar como salvo
                self.modified = False
                self.originals = {k: v.copy() for k, v in self.dfs.items()}
            else:
                # houve alteracao durante o envio -> salva de novo
                self.modified = True
                self._salvar_pendente = True
            self._atualizar_cards()
            if perdidas:
                self.status("Salvo no Supabase! (" + str(total) + " registros) | "
                            "colunas fora do banco: " + ", ".join(perdidas))
            else:
                self.status(f"Salvo no Supabase! ({total} registros)"
                            + self._aviso_nivel)

        if self._salvar_pendente and self.modified:
            self._salvar_pendente = False
            self.salvar_supabase()

    # ----------------------------------------------------- salvar Excel ----
    def save_excel(self):
        if not self.dfs:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
            return

        caminho = self.excel_path
        if not caminho:
            caminho = filedialog.asksaveasfilename(
                title="Salvar planilha Excel",
                defaultextension=".xlsx",
                filetypes=[("Excel", "*.xlsx")],
                initialfile="Caminho da Maestria.xlsx",
            )
            if not caminho:
                return
            self.excel_path = caminho

        try:
            with pd.ExcelWriter(caminho, engine="openpyxl", mode="w") as writer:
                for aba, df in self.dfs.items():
                    df.to_excel(writer, sheet_name=aba, index=False)
            self.originals = {k: v.copy() for k, v in self.dfs.items()}
            self.modified = False
            self.status(f"Exportado: {os.path.basename(caminho)}")
            messagebox.showinfo("Sucesso", f"Dados exportados para:\n{caminho}")
        except PermissionError:
            messagebox.showerror("Erro", "Feche o arquivo Excel antes de salvar.")
        except Exception as e:
            messagebox.showerror("Erro ao salvar", str(e))

    # -------------------------------------------------------- SQLite -------
    def sync_sqlite(self):
        try:
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
            conn = sqlite3.connect(DB_FILE)
            for aba, df in self.dfs.items():
                tabela = "".join(c if c.isalnum() else "_" for c in aba)
                df.to_sql(tabela, conn, if_exists="replace", index=False)
            conn.close()
            self.status(f"Sincronizado com SQLite: {DB_FILE}")
            messagebox.showinfo("Sucesso", f"Dados exportados para {DB_FILE}")
        except Exception as e:
            messagebox.showerror("Erro SQLite", str(e))

    def _sair(self):
        if self.modified and not messagebox.askyesno("Sair", "Existem alteracoes nao salvas. Deseja mesmo sair?"):
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
        except Exception:
            pass
        for atributo in ("cenario_tk",):
            if hasattr(self, atributo):
                try:
                    setattr(self, atributo, None)
                except Exception:
                    pass
        if hasattr(self, "_fotos_icones"):
            self._fotos_icones.clear()
        if hasattr(self, "_fotos_destaque"):
            self._fotos_destaque.clear()

    # ------------------------------ acoes da tela principal -----------------
    def zerar_dungeons(self):
        """Marca todas as colunas da aba Semanais como 'Falso'."""
        df = self.dfs.get(ABA_SEMANAIS)
        if df is None or df.empty:
            messagebox.showinfo("Semanais", "Nao ha dados semanais carregados.")
            return
        colunas = _colunas_conhecidas(df, "semanais")
        if not colunas:
            messagebox.showinfo("Semanais", "A aba Semanais nao tem colunas de dungeon.")
            return
        marcadas = sum(1 for c in colunas if df[c].map(_verdadeiro).any())
        if not messagebox.askyesno(
                "Zerar dungeons semanais",
                f"Marcar todas as {len(colunas)} colunas semanais como 'Falso'?\n\n"
                f"({marcadas} colunas tem marcacoes ativas)"):
            return

        for coluna in colunas:
            df[coluna] = "Falso"
        self._marcar_modificado()
        busca = self.tree_refs.get(ABA_SEMANAIS, {}).get("busca")
        self._refrescar_tabela(ABA_SEMANAIS, busca.get() if busca else "")
        self._atualizar_cards()
        # e os CARDS de personagem (as missoes tem que sumir deles tambem)
        self._atualizar_todos_os_cards()
        if self.usar_supabase:
            self.salvar_supabase()
        else:
            self.status("Dungeons semanais zeradas (use 'Salvar' para gravar).")

    # --------------------------------------------------- missao rapida ----
    def _coluna_missao(self, chave):
        """Coluna da missao semanal no dataframe (pelo nome logico)."""
        df = self.dfs.get(ABA_SEMANAIS)
        return _coluna_dungeon_semanal(df, chave)

    def _missoes_do_personagem(self, nome):
        """Estado atual das 7 missoes de um personagem {chave: bool}."""
        df = self.dfs.get(ABA_SEMANAIS)
        estado = {}
        if df is None or df.empty or "Nome" not in df.columns:
            return estado
        achada = df[df["Nome"].astype(str) == str(nome)]
        if achada.empty:
            return estado
        linha = achada.iloc[0]
        for chave, _rotulo in DUNGEONS_CARD:
            coluna = self._coluna_missao(chave)
            if coluna is None:
                continue
            estado[chave] = _verdadeiro(linha.get(coluna))
        return estado

    def marcar_missoes(self, nome, missoes):
        """Marca/desmarca varias missoes semanais de um personagem.

        Tudo em UMA gravacao (o app ja salva em 2o plano).
        """
        df = self.dfs.get(ABA_SEMANAIS)
        if df is None or df.empty or "Nome" not in df.columns:
            return False
        mask = df["Nome"].astype(str) == str(nome)
        if not mask.any():
            return False
        alteradas = 0
        for chave, feito in missoes.items():
            coluna = self._coluna_missao(chave)
            if coluna is None or coluna not in df.columns:
                continue
            df.loc[mask, coluna] = "Verdadeiro" if feito else "Falso"
            alteradas += 1
        if not alteradas:
            return False
        self._atualizar_card(str(nome))
        self._atualizar_cards()
        self._marcar_modificado()
        if self.usar_supabase:
            self.salvar_supabase()
        return True

    def alternar_missao_rapida(self, chave, nome):
        """Clique no chip de uma missao (no modo missao rapida).

        Fora do modo, o clique no chip abre a edicao do personagem (como
        antes) — o chip tem prioridade de tag no canvas.
        """
        if not (self.missao_rapida and self.missao_modo == MODO_MISSAO_CARD):
            # fora do modo CARD: o clique no chip abre a edicao (como antes)
            self._abrir_personagem({"nome": nome})
            return False
        df = self.dfs.get(ABA_SEMANAIS)
        coluna = self._coluna_missao(chave)
        if df is None or coluna is None:
            return False
        mask = df["Nome"].astype(str) == str(nome)
        if not mask.any():
            return False
        atual = _verdadeiro(df.loc[mask, coluna].iloc[0])
        novo = not atual
        df.loc[mask, coluna] = "Verdadeiro" if novo else "Falso"
        self._atualizar_card(str(nome))
        self._atualizar_cards()
        self._marcar_modificado()
        if self.usar_supabase:
            self.salvar_supabase()
        rotulo = dict(DUNGEONS_CARD).get(chave, chave)
        self.status(f"{nome}: {rotulo} {'MARCADA' if novo else 'desmarcada'}")
        return True

    def alternar_missao(self):
        """Liga/desliga o MODO MISSÃO RÁPIDA (e abre/fecha o painel)."""
        estado = not self.missao_rapida
        self.missao_rapida = estado
        self._marcar_botao("topo4", estado)
        if estado:
            if self.missao_modo == MODO_MISSAO_JANELA:
                self._abrir_painel_missao()
                self.status("Missao rapida (PAINEL): marque as dungeons no "
                            "painel. Esc fecha.")
            else:
                self._fechar_painel_missao()
                self.status("Missao rapida (CARD): clique na missao do card "
                            "para marcar (o card nao abre a edicao).")
        else:
            self._fechar_painel_missao()
            self.status("Missao rapida desligada.")
        # a preferencia antiga (filtro da tabela) nao e mais usada
        self._salvar_preferencia("missao_rapida", estado)

    def _rotulo_modo_missao(self):
        """Texto da opcao (mostra o modo que esta ativo)."""
        if self.missao_modo == MODO_MISSAO_CARD:
            return "Modo: clicar no card"
        return "Modo: painel (janela)"

    def _desenhar_chave_missao(self):
        """Check (abaixo do botao Missao Rapida) que escolhe o MODO."""
        lay = self.lay
        x1, y1, x2, y2 = lay.caixa(tv.MISSAO_MODO)
        tamanho = lay.f(17)
        cy = (y1 + y2) / 2

        self._fotos_extra = getattr(self, "_fotos_extra", {})
        self._fotos_extra["missao_caixa"] = ImageTk.PhotoImage(
            tv.caixa_check("#241d3d", "#6d5fa8", (tamanho, tamanho), raio=5))
        self._fotos_extra["missao_caixa_marcada"] = ImageTk.PhotoImage(
            tv.caixa_check("#22c55e", "#22c55e", (tamanho, tamanho), raio=5))

        item_caixa = self.canvas.create_image(
            x1, cy - tamanho / 2, anchor="nw",
            image=self._fotos_extra["missao_caixa"], tags=("missao_modo",))
        item_v = self.canvas.create_text(
            x1 + tamanho / 2, cy, text="\u2713", font=self._fonte(11, "bold"),
            fill="#08130d", anchor="center", state="hidden", tags=("missao_modo",))
        item_texto = self._texto(x1 + tamanho + lay.w(9), cy,
                                 self._rotulo_modo_missao(), 11,
                                 cor=tv.CORES["suave"], anchor="w")
        self.canvas.itemconfig(item_texto, tags=("missao_modo",))

        self.canvas.tag_bind("missao_modo", "<Button-1>",
                             lambda e: self.alternar_modo_missao())
        self.canvas.tag_bind("missao_modo", "<Enter>",
                             lambda e: self.canvas.configure(cursor="hand2"))
        self.canvas.tag_bind("missao_modo", "<Leave>",
                             lambda e: self.canvas.configure(cursor=""))

        self.itens_chave_missao = {"caixa": item_caixa, "v": item_v,
                                   "texto": item_texto}
        self._atualizar_chave_missao()

    def _atualizar_chave_missao(self):
        """Pinta o check conforme o modo ativo."""
        marcado = self.missao_modo == MODO_MISSAO_CARD
        item_caixa = self.itens_chave_missao.get("caixa")
        if item_caixa is not None:
            self.canvas.itemconfigure(
                item_caixa,
                image=self._fotos_extra.get(
                    "missao_caixa_marcada" if marcado else "missao_caixa"))
        item_v = self.itens_chave_missao.get("v")
        if item_v is not None:
            self.canvas.itemconfigure(item_v,
                                      state="normal" if marcado else "hidden")
        item_texto = self.itens_chave_missao.get("texto")
        if item_texto is not None:
            self.canvas.itemconfigure(item_texto,
                                      text=self._rotulo_modo_missao())

    def alternar_modo_missao(self):
        """Alterna entre o MODO PAINEL e o MODO CARD (so um por vez)."""
        self.missao_modo = (MODO_MISSAO_CARD if self.missao_modo == MODO_MISSAO_JANELA
                            else MODO_MISSAO_JANELA)
        self._atualizar_chave_missao()
        if self.missao_rapida:
            if self.missao_modo == MODO_MISSAO_JANELA:
                self._abrir_painel_missao()
            else:
                self._fechar_painel_missao()
        self.status("Missao rapida: " +
                    ("clicando no CARD (o card nao abre a edicao)."
                     if self.missao_modo == MODO_MISSAO_CARD
                     else "no PAINEL (o card continua abrindo a edicao)."))

    def _abrir_painel_missao(self):
        """Abre (ou foca) o painel flutuante da missao rapida."""
        if getattr(self, "_painel_missao", None) is not None:
            try:
                self._painel_missao.lift()
                self._painel_missao.focus_force()
                return self._painel_missao
            except Exception:
                self._painel_missao = None
        try:
            from janela_missao_rapida import JanelaMissaoRapida
            self._painel_missao = JanelaMissaoRapida(self)
            return self._painel_missao
        except Exception as erro:
            _registrar(f"[Missao] Erro ao abrir o painel: {erro}")
            self.status(f"Erro ao abrir o painel da missao rapida: {erro}")
            return None

    def _fechar_painel_missao(self):
        painel = getattr(self, "_painel_missao", None)
        if painel is not None:
            try:
                painel.destroy()
            except Exception:
                pass
        self._painel_missao = None

    def _atalho_missao(self, evento):
        """Atalho de teclado: 'M' liga/desliga o modo missao rapida."""
        if isinstance(evento.widget, (tk.Entry, tk.Text, ctk.CTkEntry)):
            return
        if str(evento.keysym).lower() != "m":
            return
        self.alternar_missao()

    def _marcar_botao(self, chave, ativo):
        """Estado LIGADO do botao: fundo VERDE + texto escuro.

        (o modo Missao Rapida fica com o botao verde, sinalizando que
        o card esta em modo de marcacao e nao abre a edicao)
        """
        verde = self.itens_verde.get(chave)
        if verde is not None:
            self.canvas.itemconfigure(verde,
                                      state="normal" if ativo else "hidden")
        destaque = self.itens_destaque.get(chave)
        if destaque is not None:
            self.canvas.itemconfigure(destaque, state="hidden")
        texto = self.itens_texto_botao.get(chave)
        if texto is not None:
            self.canvas.itemconfigure(
                texto, fill="#08130d" if ativo else tv.CORES["texto"])

    def marcar_chaser(self):
        """Abre a edicao do nivel do chaser (o card e clicavel)."""
        self._abrir_nivel()

    # ------------------------------------------------------ preferencias ----
    def _ler_preferencia(self):
        """Le a preferencia 'missao_rapida' do user_profiles (se existir)."""
        if not self.usar_supabase or not self.user_id:
            return
        try:
            resp = (self.supabase.table("user_profiles")
                    .select("*").eq("id", self.user_id).limit(1).execute())
            linhas = getattr(resp, "data", None) or []
            if linhas and "missao_rapida" in linhas[0]:
                self.missao_rapida = bool(linhas[0]["missao_rapida"])
        except Exception:
            pass

    def _coluna_perfil_existe(self, coluna):
        """A coluna opcional existe no user_profiles? (sonda, com cache)."""
        cache = getattr(self, "_cache_perfil", None)
        if cache is None:
            cache = {}
            self._cache_perfil = cache
        if coluna not in cache:
            try:
                self.supabase.table("user_profiles").select(coluna) \
                    .limit(1).execute()
                cache[coluna] = True
            except Exception:
                cache[coluna] = False
        return cache[coluna]

    def _ler_ultimo_personagem(self):
        """Le o ultimo personagem usado na missao rapida (se a coluna
        existir no banco; senao, so nesta sessao)."""
        self.ultimo_personagem_missao = None
        if not self.usar_supabase or not self.user_id:
            return
        if not self._coluna_perfil_existe("missao_rapida_personagem"):
            return
        try:
            resp = (self.supabase.table("user_profiles")
                    .select("missao_rapida_personagem")
                    .eq("id", self.user_id).limit(1).execute())
            linhas = getattr(resp, "data", None) or []
            if linhas and linhas[0].get("missao_rapida_personagem"):
                self.ultimo_personagem_missao = \
                    linhas[0]["missao_rapida_personagem"]
        except Exception:
            pass

    def _lembrar_personagem_missao(self, nome):
        """Guarda o ultimo personagem usado (o painel ja abre nele)."""
        self.ultimo_personagem_missao = str(nome)
        if not self.usar_supabase or not self.user_id:
            return False
        if not self._coluna_perfil_existe("missao_rapida_personagem"):
            return False
        try:
            self.supabase.table("user_profiles") \
                .update({"missao_rapida_personagem": str(nome)}) \
                .eq("id", self.user_id).execute()
            return True
        except Exception:
            return False

    def _salvar_preferencia(self, nome, valor):
        """Grava uma preferencia no user_profiles (best effort)."""
        if not self.usar_supabase or not self.user_id:
            return False
        try:
            self.supabase.table("user_profiles").update({nome: bool(valor)}) \
                .eq("id", self.user_id).execute()
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _num(valor, padrao=0):
    """Converte para int (aceita None, '' e texto)."""
    if valor is None or valor == "":
        return padrao
    try:
        return int(float(valor))
    except (TypeError, ValueError):
        return padrao


def _ordenar_colunas(df):
    """Coloca 'Nome' como PRIMEIRA coluna e move 'id'/'character_id' para o FIM."""
    cols = list(df.columns)
    internas = [c for c in ("id", "character_id") if c in cols]
    if "Nome" in cols and cols[0] == "Nome" and not internas:
        return df
    nome = ["Nome"] if "Nome" in cols else []
    meio = [c for c in cols if c not in internas and c != "Nome"]
    return df[nome + meio + internas]


def _coluna_dungeon_semanal(df, chave):
    """Coluna de uma dungeon SEMANAL no dataframe.

    A Torre das Ilusoes semanal esta no banco como
    "torre_das_ilusoes_semanal", mas a chave do app e
    "torredasilusoes" - sem esta equivalencia a Torre nunca era
    encontrada (e por isso o filtro dela nao filtrava nada).
    """
    coluna = _coluna_no_df(df, chave)
    if coluna:
        return coluna
    from opcoes import mesmo_dado
    for coluna_df in (df.columns if df is not None else ()):
        if mesmo_dado(coluna_df, chave):
            return coluna_df
    return None


def _coluna_no_df(df, chave):
    """Descobre a coluna real do dataframe que corresponde a chave do banco.

    Ex.: chave 'caminho_abissal' encontra 'Caminho Abissal' na planilha e
    'caminho_abissal' no Supabase (comparacao normalizada).
    """
    if df is None or df.empty:
        return None
    alvo = coluna_banco(chave)
    for coluna in df.columns:
        if coluna_banco(coluna) == alvo:
            return coluna
    return None


# ---------------------------------------------------------------------------
# Treeview moderno
# ---------------------------------------------------------------------------
def ttk_treeview_moderno(parent, colunas):
    frame = ttk.Frame(parent)
    frame.grid(row=0, column=0, sticky="nsew")
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    cols = list(colunas)
    visiveis = [c for c in cols if c not in ("id", "character_id")]
    if not visiveis:
        visiveis = cols

    tree = ttk.Treeview(frame, columns=cols, show="headings",
                        displaycolumns=visiveis)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    for col in cols:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor="center", stretch=True)

    _estilizar_ttk()
    return tree


def _estilizar_ttk():
    """Visual escuro para os widgets ttk (tabela, scrollbars, combobox)."""
    try:
        estilo = ttk.Style()
        try:
            estilo.theme_use("clam")
        except Exception:
            pass
        estilo.configure("TFrame", background="#14181d")
        estilo.configure("Treeview",
                         background="#171b21",
                         fieldbackground="#171b21",
                         foreground="#dfe6ee",
                         borderwidth=0,
                         rowheight=26)
        estilo.configure("Treeview.Heading",
                         background="#242a32",
                         foreground="#aab4c0",
                         relief="flat",
                         borderwidth=0,
                         padding=(6, 4))
        estilo.map("Treeview",
                   background=[("selected", "#2f80ed")],
                   foreground=[("selected", "#ffffff")])
        estilo.map("Treeview.Heading", background=[("active", "#2e353e")])
        for orientacao in ("Vertical", "Horizontal"):
            estilo.configure(f"{orientacao}.TScrollbar",
                             background="#222831",
                             troughcolor="#171b21",
                             bordercolor="#171b21",
                             arrowcolor="#6b7684",
                             borderwidth=0,
                             arrowsize=12)
        estilo.configure("TCombobox",
                         fieldbackground="#171b21",
                         background="#171b21",
                         foreground="#dfe6ee",
                         arrowcolor="#9aa5b1",
                         bordercolor="#2b323b",
                         selectbackground="#2f80ed",
                         selectforeground="#ffffff")
        estilo.configure("Listbox",
                         background="#171b21",
                         foreground="#dfe6ee",
                         selectbackground="#2f80ed",
                         selectforeground="#ffffff")
    except Exception:
        pass


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from login import abrir_aplicativo
    abrir_aplicativo()

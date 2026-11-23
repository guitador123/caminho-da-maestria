# -*- coding: utf-8 -*-
"""
Janela de edicao de um personagem (Toplevel).

Aberta pelo botao `->` do card. Todos os campos do mockup sao editaveis aqui:

  - Identidade:  Titulo/Origem (dropdown), Poder
  - Progresso:   Torre das Ilusoes (0-30), Void Unificado, Void Apocalipse,
                  Núcleos Dimensionais, Fragmento do Vazio Disperso
  - Despertar:   Núcleos (dropdown), Epicos+ (dropdown)
  - Liberacao:   Núcleos (0-9), Epicos+ (0-4), estado (dropdown)
  - Equipamentos Void (12 checkboxes)
  - Acessorios (4 dropdowns) + Titulo/Origem
  - Dungeons semanais (7 checkboxes)

Ao salvar, os dataframes do app sao atualizados e o `salvar_supabase()` e
chamado (ele grava no Supabase).
"""

import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

import caminhos

from opcoes import obter_opcoes
from dados_app import _num as _num_dados
from registro import falha

ABA_GERAL = "Geral"
ABA_PECAS = "Peças (Void)"
ABA_ACESSORIOS = "Acessórios Título"
ABA_SEMANAIS = "Semanais"

# (coluna na tabela, rotulo, tipo)
CAMPOS_GERAIS = [
    ("Poder", "Ataque Total", "numero"),
    ("Torre Das Ilusões", "Torre das Ilusões (andar)", "torre"),
    ("Vazio Uni.", "Void Unificado", "numero"),
    ("Vazio Apo.", "Void Apocalipse", "numero"),
    ("Núcleos Dimensionais", "Núcleos Dimensionais", "numero"),
    ("Fragmento do Vazio Disperso", "Fragmento do Vazio Disperso", "numero"),
]

PECAS = [
    ("arma", "Arma"), ("luvas", "Luvas"), ("cota", "Cota"), ("botas", "Botas"),
    ("capa", "Capa"), ("calca", "Calça"), ("elmo", "Elmo"),
    ("escudos", "Escudo"), ("asas", "Asas"), ("facas", "Facas"),
    ("mascara", "Máscara"), ("diadema", "Diadema"),
]

ACESSORIOS = [
    ("anel", "Anel"), ("tornozeleira", "Tornozeleira"),
    ("brinco", "Brinco"), ("piercing", "Piercing"),
]

# as mesmas chaves NORMALIZADAS do card (card_personagem.DUNGEONS)
DUNGEONS = [
    ("void4", "Void 4"),
    ("altardarunha", "Altar da Ruína"),
    ("caminhoabissal", "Caminho Abissal"),
    ("fornalhainfernal", "Fornalha Infernal"),
    ("void123", "Void (1, 2 e 3)"),
    ("torredasilusoes", "Torre das Ilusões"),
    ("terradojulgamento", "Terra do Julgamento"),
]

# Opcoes dos dropdowns (regra do usuario, 14/11)
OPCOES_DESPERTAR_NUCLEOS = [f"{i} / 13" for i in range(14)]
OPCOES_DESPERTAR_EPICOS = [f"{i} / 9" for i in range(10)]
OPCOES_LIBERTACAO_NUCLEOS = [f"{i} / 9" for i in range(10)]
OPCOES_LIBERTACAO_EPICOS = [f"{i} / 4" for i in range(5)]

CORES = {
    "fundo": "#141221",
    "painel": "#1e1a30",
    "painel_borda": "#332d4d",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "verde": "#22c55e",
}


def _num(valor, padrao=0):
    """'5 / 9' -> 5; '618.002' (ponto de milhar) -> 618002."""
    if valor is None or valor == "":
        return padrao
    partes = str(valor).replace("/", " ").split()
    if not partes:
        return padrao
    return _num_dados(partes[0], padrao)


def _fracao_texto(valor, maximo):
    """'13/13' ou 13 -> '13 / 13' (formato dos dropdowns).

    Vazio continua vazio (nao inventa '0 / 13' para quem nao tem nada).
    """
    texto = str(valor if valor is not None else "").strip()
    if not texto:
        return ""
    try:
        numero = int(float(texto.split("/")[0]))
    except (TypeError, ValueError):
        return ""
    return f"{numero} / {maximo}"


def _verdadeiro(valor) -> bool:
    if isinstance(valor, bool):
        return valor
    if valor is None:
        return False
    return str(valor).strip().lower() in ("verdadeiro", "true", "1", "t", "sim")


class JanelaPersonagem(ctk.CTkToplevel):
    """Edicao de um personagem."""

    def __init__(self, app, nome):
        super().__init__(app)
        self.app = app
        self.nome = nome
        self.title(f"{nome} — Caminho da Maestria")
        caminhos.aplicar_icone(self)
        self.geometry("620x860")
        self.minsize(560, 700)
        self.configure(fg_color=CORES["fundo"])

        self._linhas = {}
        self._geral = self._linha_da_tabela(ABA_GERAL)
        self._pecas = self._linha_da_tabela(ABA_PECAS)
        self._acess = self._linha_da_tabela(ABA_ACESSORIOS)
        self._sem = self._linha_da_tabela(ABA_SEMANAIS)

        self._montar()
        self.after(60, self._focar)

    # ------------------------------------------------------------ dados ----
    def _coluna_no_df(self, df, chave):
        """Coluna real do dataframe para a chave logica (planilha ou banco)."""
        if df is None or df.empty:
            return None
        from opcoes import coluna_banco
        alvo = coluna_banco(chave)
        for coluna in df.columns:
            if coluna_banco(coluna) == alvo:
                return coluna
        return None

    def _coluna_semanal(self, chave):
        """Coluna da dungeon SEMANAL (a Torre tem outro nome no banco)."""
        df = self.app.dfs.get(ABA_SEMANAIS)
        coluna = self._coluna_no_df(df, chave)
        if coluna:
            return coluna
        from opcoes import mesmo_dado
        for coluna_df in (df.columns if df is not None else ()):
            if mesmo_dado(coluna_df, chave):
                return coluna_df
        return None

    def _valor(self, linha, chave, padrao=None):
        """Valor de um campo da linha do personagem.

        A linha tem as chaves NORMALIZADAS, entao "Arma" (planilha),
        "arma" (banco) e "ARMA" caem no mesmo lugar.
        """
        if not linha:
            return padrao
        from opcoes import coluna_banco
        if chave in linha:
            return linha[chave]
        return linha.get(coluna_banco(chave), padrao)

    def _linha_da_tabela(self, aba):
        """Linha do personagem na aba, com as chaves NORMALIZADAS.

        Sem isso a tela de edicao lia "arma" numa tabela que tem "Arma" e
        voltava vazia -> o que foi salvo nao aparecia marcado ao reabrir.
        """
        df = self.app.dfs.get(aba)
        if df is None or df.empty or "Nome" not in df.columns:
            return {}
        achada = df[df["Nome"].astype(str) == str(self.nome)]
        if achada.empty:
            return {}
        from opcoes import coluna_banco, chave_semanal
        linha = achada.iloc[0].to_dict()
        saida = {}
        for coluna, valor in linha.items():
            chave = coluna_banco(coluna)
            if aba == ABA_SEMANAIS:
                # a Torre semanal entra com a chave do app
                chave = chave_semanal(chave)
            saida[chave] = valor
        return saida

    # ------------------------------------------------------------- UI ------
    def _montar(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=20, pady=(18, 6))
        ctk.CTkLabel(topo, text=self.nome, font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left")
        ctk.CTkLabel(topo, text="Editar personagem", font=ctk.CTkFont(size=14),
                     text_color=CORES["suave"]).pack(side="left", padx=12, pady=(10, 0))

        rolagem = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                         scrollbar_button_color="#3a3358")
        rolagem.pack(fill="both", expand=True, padx=16, pady=(4, 8))

        self._secao(rolagem, "Identidade")
        self._campo_titulo(rolagem)
        self._campo_numero(rolagem, "Poder", "Ataque Total",
                           self._valor(self._geral, "Poder"))

        self._secao(rolagem, "Progresso")
        for coluna, rotulo, tipo in CAMPOS_GERAIS[1:]:
            valor = self._valor(self._geral, coluna)
            if tipo == "torre":
                self._campo_torre(rolagem, coluna, rotulo, valor)
            else:
                self._campo_numero(rolagem, coluna, rotulo, valor)

        self._secao(rolagem, "Despertar")
        self._campo_combo(rolagem, "Núcleo", "Núcleos (Despertar)",
                           _fracao_texto(self._valor(self._geral, "Núcleo"), 13),
                           valores=list(OPCOES_DESPERTAR_NUCLEOS))
        self._campo_combo(rolagem, "Núcleos Épicos+", "Épicos+ (Despertar)",
                           _fracao_texto(self._valor(self._geral, "Núcleos Épicos+"), 9),
                           valores=list(OPCOES_DESPERTAR_EPICOS))

        self._secao(rolagem, "Libertação")
        # a liberacao tambem e dropdown (o banco guarda so o numero)
        self._campo_combo(rolagem, "Libertação Núcleos", "Núcleos (Libertação)",
                           _fracao_texto(self._valor(self._geral, "Libertação Núcleos"), 9),
                           valores=list(OPCOES_LIBERTACAO_NUCLEOS), fracao=True)
        self._campo_combo(rolagem, "Libertação Épicos+", "Épicos+ (Libertação)",
                           _fracao_texto(self._valor(self._geral, "Libertação Épicos+"), 4),
                           valores=list(OPCOES_LIBERTACAO_EPICOS), fracao=True)
        self._campo_combo(rolagem, "Libertação", "Estado da Libertação",
                           self._valor(self._geral, "Libertação"),
                           valores=["FALSO", "VERDADEIRO", "INEXISTENTE"])

        self._secao(rolagem, "Equipamentos Void")
        grade = ctk.CTkFrame(rolagem, fg_color="transparent")
        grade.pack(fill="x", padx=4)
        for indice, (chave, rotulo) in enumerate(PECAS):
            marcado = _verdadeiro(self._valor(self._pecas, chave))
            caixa = ctk.CTkCheckBox(grade, text=rotulo, font=ctk.CTkFont(size=13),
                                     text_color=CORES["suave"],
                                     fg_color=CORES["verde"],
                                     hover_color="#16a34a",
                                     border_color="#5b5378")
            if marcado:
                caixa.select()
            caixa.configure(command=self._propagar)
            caixa.grid(row=indice // 4, column=indice % 4, sticky="w",
                       padx=10, pady=4)
            real = self._coluna_no_df(self.app.dfs.get(ABA_PECAS), chave)
            self._linhas[("peca", real or chave)] = caixa

        self._secao(rolagem, "Acessórios")
        for chave, rotulo in ACESSORIOS:
            self._campo_combo(rolagem, chave, rotulo,
                               self._valor(self._acess, chave),
                               aba=ABA_ACESSORIOS)

        self._secao(rolagem, "Dungeons semanais")
        grade2 = ctk.CTkFrame(rolagem, fg_color="transparent")
        grade2.pack(fill="x", padx=4)
        for indice, (chave, rotulo) in enumerate(DUNGEONS):
            marcado = _verdadeiro(self._valor(self._sem, chave))
            caixa = ctk.CTkCheckBox(grade2, text=rotulo, font=ctk.CTkFont(size=13),
                                     text_color=CORES["suave"],
                                     fg_color=CORES["verde"],
                                     hover_color="#16a34a",
                                     border_color="#5b5378")
            if marcado:
                caixa.select()
            caixa.configure(command=self._propagar)
            caixa.grid(row=indice // 4, column=indice % 4, sticky="w",
                       padx=10, pady=4)
            real = self._coluna_semanal(chave)
            self._linhas[("semanal", real or chave)] = caixa

        # --- botoes ---
        barra = ctk.CTkFrame(self, fg_color="transparent")
        barra.pack(fill="x", padx=20, pady=(4, 18))
        ctk.CTkButton(barra, text="Cancelar", width=140, height=42,
                      corner_radius=10, fg_color="#2a2440", hover_color="#372f52",
                      command=self.destroy).pack(side="right")
        ctk.CTkButton(barra, text="Salvar", width=160, height=42, corner_radius=10,
                      fg_color=CORES["verde"], hover_color="#16a34a",
                      text_color="#08130d",
                      font=ctk.CTkFont(size=15, weight="bold"),
                      command=self._salvar).pack(side="right", padx=(0, 12))

    def _secao(self, pai, titulo):
        ctk.CTkLabel(pai, text=titulo.upper(), font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=6, pady=(16, 6))

    def _linha_campo(self, pai, rotulo):
        linha = ctk.CTkFrame(pai, fg_color="transparent")
        linha.pack(fill="x", padx=6, pady=3)
        ctk.CTkLabel(linha, text=rotulo, width=190, anchor="w",
                     font=ctk.CTkFont(size=13), text_color=CORES["suave"]
                     ).pack(side="left")
        return linha

    def _campo_numero(self, pai, coluna, rotulo, valor, maximo=None):
        linha = self._linha_campo(pai, rotulo)
        entrada = ctk.CTkEntry(linha, width=130, height=34, corner_radius=8,
                                fg_color=CORES["painel"], border_color=CORES["painel_borda"],
                                text_color=CORES["texto"], font=ctk.CTkFont(size=14))
        entrada.insert(0, str(_num(valor)))
        entrada.pack(side="left")
        real = self._coluna_no_df(self.app.dfs.get(ABA_GERAL), coluna)
        self._linhas[("geral", real or coluna)] = (entrada, maximo)
        entrada.bind("<Return>", lambda e: self._propagar())
        entrada.bind("<FocusOut>", lambda e: self._propagar())
        return entrada

    def _campo_torre(self, pai, coluna, rotulo, valor):
        linha = self._linha_campo(pai, rotulo)
        entrada = ctk.CTkEntry(linha, width=90, height=34, corner_radius=8,
                                fg_color=CORES["painel"], border_color=CORES["painel_borda"],
                                text_color=CORES["texto"], font=ctk.CTkFont(size=14),
                                justify="center")
        entrada.insert(0, str(_num(valor)))
        entrada.pack(side="left")
        ctk.CTkLabel(linha, text="/ 30", font=ctk.CTkFont(size=13),
                     text_color=CORES["suave"]).pack(side="left", padx=6)
        real = self._coluna_no_df(self.app.dfs.get(ABA_GERAL), coluna)
        self._linhas[("geral", real or coluna)] = (entrada, 30)
        entrada.bind("<Return>", lambda e: self._propagar())
        entrada.bind("<FocusOut>", lambda e: self._propagar())
        return entrada

    def _campo_combo(self, pai, coluna, rotulo, valor, aba=None, valores=None,
                     fracao=False):
        linha = self._linha_campo(pai, rotulo)
        if valores is None:
            valores = obter_opcoes(aba or ABA_GERAL, coluna) or []
        if not valores:
            valores = [str(valor or "")]
        if valor and valor not in valores:
            valores = [str(valor)] + list(valores)
        combo = ctk.CTkComboBox(linha, width=300, height=34, corner_radius=8,
                                 fg_color=CORES["painel"],
                                 border_color=CORES["painel_borda"],
                                 button_color=CORES["roxo"],
                                 button_hover_color="#a78bfa",
                                 dropdown_fg_color=CORES["painel"],
                                 dropdown_text_color=CORES["texto"],
                                 dropdown_hover_color="#3a3358",
                                 text_color=CORES["texto"],
                                 font=ctk.CTkFont(size=13),
                                 values=list(valores))
        if valor:
            combo.set(str(valor))
        combo.pack(side="left")
        tabela = self.app.dfs.get(aba or ABA_GERAL)
        real = self._coluna_no_df(tabela, coluna)
        if fracao:
            # combo de fracao ("5 / 9"): o banco guarda so o numero
            self._linhas[("geral", real or coluna)] = (combo, "fracao")
        elif aba == ABA_ACESSORIOS:
            self._linhas[("acesso", real or coluna)] = combo
        else:
            self._linhas[("geral", real or coluna)] = combo
        combo.bind("<<ComboboxSelected>>", lambda e: self._propagar())
        return combo

    def _campo_titulo(self, pai):
        """Titulo/Origem (dropdown com os titulos do jogo)."""
        linha = self._linha_campo(pai, "Origem / Título")
        valores = obter_opcoes(ABA_ACESSORIOS, "Título") or []
        combo = ctk.CTkComboBox(linha, width=300, height=34, corner_radius=8,
                                 fg_color=CORES["painel"],
                                 border_color=CORES["painel_borda"],
                                 button_color=CORES["roxo"],
                                 button_hover_color="#a78bfa",
                                 dropdown_fg_color=CORES["painel"],
                                 dropdown_text_color=CORES["texto"],
                                 dropdown_hover_color="#3a3358",
                                 text_color=CORES["texto"],
                                 font=ctk.CTkFont(size=13),
                                 values=list(valores) or [""])
        atual = self._valor(self._acess, "Título") or ""
        if atual and atual not in (valores or []):
            combo.configure(values=[atual] + list(valores or []))
        if atual:
            combo.set(atual)
        combo.pack(side="left")
        real = self._coluna_no_df(self.app.dfs.get(ABA_ACESSORIOS), "Título")
        self._linhas[("acesso", real or "Título")] = combo
        combo.bind("<<ComboboxSelected>>", lambda e: self._propagar())

    # ------------------------------------------------------------ salvar ----
    def _aplicar_ao_df(self):
        """Escreve os valores dos widgets nos dataframes do app."""
        df = self.app.dfs.get(ABA_GERAL)
        if df is not None and not df.empty and "Nome" in df.columns:
            mask = df["Nome"].astype(str) == str(self.nome)
            for coluna, item in self._linhas.items():
                if coluna[0] != "geral":
                    continue
                nome_coluna = coluna[1]
                if nome_coluna not in df.columns:
                    continue
                if isinstance(item, tuple):
                    entrada, maximo = item
                    valor = _num(entrada.get())
                    if maximo == "fracao":
                        # combo de fracao: a coluna e INTEIRA no banco,
                        # entao grava so o numero ("5 / 9" -> 5)
                        pass
                    else:
                        if maximo is not None:
                            valor = max(0, min(maximo, valor))
                        if nome_coluna == "Torre Das Ilusões":
                            valor = f"{valor} / 30"
                    df.loc[mask, nome_coluna] = valor
                else:
                    df.loc[mask, nome_coluna] = item.get()

        df = self.app.dfs.get(ABA_PECAS)
        if df is not None and not df.empty and "Nome" in df.columns:
            mask = df["Nome"].astype(str) == str(self.nome)
            for (tipo, chave), caixa in self._linhas.items():
                if tipo != "peca":
                    continue
                if chave in df.columns:
                    df.loc[mask, chave] = "VERDADEIRO" if caixa.get() else "FALSO"

        df = self.app.dfs.get(ABA_ACESSORIOS)
        if df is not None and not df.empty and "Nome" in df.columns:
            mask = df["Nome"].astype(str) == str(self.nome)
            for (tipo, chave), combo in self._linhas.items():
                if tipo != "acesso":
                    continue
                if chave in df.columns:
                    df.loc[mask, chave] = combo.get()

        df = self.app.dfs.get(ABA_SEMANAIS)
        if df is not None and not df.empty and "Nome" in df.columns:
            mask = df["Nome"].astype(str) == str(self.nome)
            for (tipo, chave), caixa in self._linhas.items():
                if tipo != "semanal":
                    continue
                if chave in df.columns:
                    df.loc[mask, chave] = "Verdadeiro" if caixa.get() else "Falso"

    def _propagar(self):
        """Envia as alteracoes para o app: o card atualiza na hora."""
        try:
            self._aplicar_ao_df()
            self.app._marcar_modificado()
            self.app._atualizar_card(self.nome)
            # os contadores do "Caminho da Maestria" (despertar completo,
            # liberacao completa, torre, etc.) tambem mudam ao vivo
            self.app._atualizar_cards()
            self.app.status(f"{self.nome}: alteracoes aplicadas (clique em Salvar "
                            f"para gravar no Supabase).")
        except Exception as erro:
            self.app.status(f"Erro ao aplicar a alteracao: {erro}")

    def _salvar(self):
        """Grava nos dataframes e pede o salvamento no Supabase."""
        try:
            self._aplicar_ao_df()
            self.app._marcar_modificado()
            self.app._atualizar_cards()
            self.app._atualizar_card(self.nome)
            self.destroy()
            if self.app.usar_supabase:
                self.app.salvar_supabase()
            else:
                self.app.status(f"{self.nome}: alteracoes aplicadas.")
        except Exception as erro:
            messagebox.showerror("Erro ao salvar", str(erro))

    def _focar(self):
        try:
            self.lift()
            self.focus_force()
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("focar a janela do personagem")

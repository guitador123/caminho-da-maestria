# -*- coding: utf-8 -*-
"""
Excel (importar/exportar), SQLite e a tabela (Treeview).

Parte da tela principal (`GrandChaseApp` herda de `ArquivosMixin`).
Separado do app_grandchase.py sem mudar o codigo dos metodos.
"""

import customtkinter as ctk
import os
import pandas as pd
import sqlite3
import tkinter as tk
from config_app import DB_FILE, EXCEL_DEFAULT
from dados_app import _mesmo_arquivo, _ordenar_colunas
from opcoes import canonizar_aba, obter_opcoes
from registro import falha
from tkinter import filedialog, messagebox, ttk


class ArquivosMixin:
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
                if self.mostrar_tabela:
                    self._criar_aba(aba_can, df)

            self.modified = False
            self._ler_nivel_chaser()
            self._ler_colecao_cartas()
            self._atualizar_cards()
            self.status(f"Carregado: {os.path.basename(path)} | {len(abas)} abas | "
                        f"{sum(len(d) for d in self.dfs.values())} registros")
        except PermissionError:
            messagebox.showerror("Erro", "Feche o arquivo Excel antes de abri-lo.")
        except Exception as e:
            falha("[Excel] carregar", e)
            messagebox.showerror("Erro ao carregar Excel", str(e))

    def _limpar_abas(self):
        """Remove as abas do notebook e zera os dataframes."""
        if self.mostrar_tabela:
            for aba in list(self.abas_criadas):
                try:
                    self.notebook.delete(aba)
                except tk.TclError:
                    pass                      # janela ja fechada
                except Exception:
                    falha("limpar as abas")
        self.abas_criadas.clear()
        self.dfs.clear()
        self.originals.clear()
        self._originais_do_banco = False
        self.tree_refs.clear()

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

    # ----------------------------------------------------- salvar Excel ----
    def save_excel(self):
        if not self.dfs:
            messagebox.showwarning("Aviso", "Nenhum dado para exportar.")
            return

        caminho = self.excel_path
        # a planilha-modelo do repositorio NUNCA e sobrescrita: ela e
        # versionada (e publica no GitHub); os dados reais do usuario vao
        # para um arquivo que ele escolhe
        if caminho and _mesmo_arquivo(caminho, EXCEL_DEFAULT):
            caminho = None
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
            falha("[Excel] salvar", e)
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
            falha("[SQLite] salvar", e)
            messagebox.showerror("Erro SQLite", str(e))


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
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("escolher o tema ttk")
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
        falha("estilizar o ttk")

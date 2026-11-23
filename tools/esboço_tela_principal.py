"""
Esboço da tela principal "Caminho da Maestria" em CustomTkinter.

Baseado na imagem de referência (sem idioma, sem "Instalar aplicativo").

Requisitos:
    pip install customtkinter pillow

Observações importantes:
- A imagem de fundo e os ícones NÃO estão incluídos. Você precisa fornecer
  arquivos PNG/JPG e ajustar os caminhos no código (marcados com # TODO).
- Sem a imagem de fundo, a tela fica com cor escura sólida (simulando o tema).
"""

import os
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

import customtkinter as ctk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ---------------------------------------------------------------------------
# Caminhos dos arquivos (ajuste conforme sua estrutura)
# ---------------------------------------------------------------------------
CAMINHO_FUNDO = r"C:\Users\guilh\Downloads\Controle GrandChase\assets\fundo_personagens.png"
CAMINHO_ICONE_EXCEL = r"C:\Users\guilh\Downloads\Controle GrandChase\assets\icone_excel.png"
CAMINHO_ICONE_IMPORT = r"C:\Users\guilh\Downloads\Controle GrandChase\assets\icone_import.png"


def carregar_imagem(caminho, tamanho=None):
    """Carrega uma imagem com PIL e retorna CTkImage, ou None se falhar."""
    try:
        if not os.path.exists(caminho):
            return None
        img = Image.open(caminho)
        if tamanho:
            img = img.resize(tamanho, Image.LANCZOS)
        return ctk.CTkImage(light_image=img, dark_image=img, size=tamanho or img.size)
    except Exception:
        return None


class TelaPrincipal(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Controle Grand Chase - Caminho da Maestria")
        self.geometry("1200x760")
        self.minsize(1000, 650)

        # Estado
        self.arquivo_selecionado = None

        # Layout raiz
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Container principal (simula o fundo escuro da imagem)
        self.container = ctk.CTkFrame(self, corner_radius=0)
        self.container.grid(row=0, column=0, sticky="nsew")
        self.container.grid_columnconfigure(0, weight=1)
        self.container.grid_rowconfigure(1, weight=1)

        # --- Fundo com imagem (se existir) ---
        self._aplicar_fundo()

        # ==================================================================
        # CABEÇALHO
        # ==================================================================
        self.header = ctk.CTkFrame(self.container, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=40, pady=(30, 10))
        self.header.grid_columnconfigure(0, weight=1)

        # Texto pequeno superior esquerdo
        ctk.CTkLabel(
            self.header,
            text="GRAND CHASE · CENTRAL DE PROGRESSO",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#aaaaaa",
        ).grid(row=0, column=0, sticky="w")

        # Título grande
        ctk.CTkLabel(
            self.header,
            text="Caminho da Maestria",
            font=ctk.CTkFont(size=44, weight="bold"),
            text_color="#ffffff",
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))

        # Subtítulo
        ctk.CTkLabel(
            self.header,
            text="Seus personagens, equipamentos e progresso semanal\n— tudo em um só lugar.",
            font=ctk.CTkFont(size=15),
            text_color="#cccccc",
            justify="left",
        ).grid(row=2, column=0, sticky="w", pady=(8, 0))

        # Botões topo direito (somente Exportar Excel mantido)
        self.botoes_topo = ctk.CTkFrame(self.header, fg_color="transparent")
        self.botoes_topo.grid(row=0, column=1, rowspan=3, sticky="e")

        btn_exportar = carregar_imagem(CAMINHO_ICONE_EXCEL, tamanho=(18, 18))
        ctk.CTkButton(
            self.botoes_topo,
            text="Exportar Excel",
            image=btn_exportar,
            compound="left",
            width=140,
            height=36,
            corner_radius=8,
            command=self.exportar_excel,
        ).pack(side="left", padx=(0, 10), pady=5)

        # ==================================================================
        # BLOCO DE IMPORTAÇÃO (Import updated workbook)
        # ==================================================================
        self.bloco_import = ctk.CTkFrame(
            self.container,
            corner_radius=12,
            fg_color=("#2b2b2b", "#1f1f1f"),
            border_width=1,
            border_color=("#444444", "#333333"),
        )
        self.bloco_import.grid(row=1, column=0, sticky="ew", padx=40, pady=(20, 10))
        self.bloco_import.grid_columnconfigure(1, weight=1)

        icone_import = carregar_imagem(CAMINHO_ICONE_IMPORT, tamanho=(20, 20))

        ctk.CTkLabel(
            self.bloco_import,
            text="Import updated workbook",
            image=icone_import,
            compound="left",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#ffffff",
        ).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(18, 5))

        ctk.CTkLabel(
            self.bloco_import,
            text="Update saved characters from an .xlsx file. Blank cells are left unchanged; unknown names are skipped.",
            font=ctk.CTkFont(size=13),
            text_color="#999999",
            justify="left",
        ).grid(row=1, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 15))

        # Linha: botão escolher | campo texto | botão importar
        self.btn_escolher = ctk.CTkButton(
            self.bloco_import,
            text="ESCOLHER ARQUIVO",
            width=180,
            height=40,
            corner_radius=8,
            fg_color="#333333",
            hover_color="#444444",
            command=self.escolher_arquivo,
        )
        self.btn_escolher.grid(row=2, column=0, padx=(20, 10), pady=(0, 20), sticky="w")

        self.lbl_arquivo = ctk.CTkEntry(
            self.bloco_import,
            placeholder_text="Nenhum arquivo escolhido",
            width=320,
            height=40,
            corner_radius=8,
            state="readonly",
        )
        self.lbl_arquivo.grid(row=2, column=1, padx=10, pady=(0, 20), sticky="ew")

        icone_import_btn = carregar_imagem(CAMINHO_ICONE_IMPORT, tamanho=(18, 18))
        ctk.CTkButton(
            self.bloco_import,
            text="Import Excel",
            image=icone_import_btn,
            compound="left",
            width=150,
            height=40,
            corner_radius=8,
            fg_color="#8a2be2",
            hover_color="#7a1fd2",
            command=self.importar_excel,
        ).grid(row=2, column=2, padx=(10, 20), pady=(0, 20), sticky="e")

        # ==================================================================
        # CARDS DE ESTATÍSTICAS (grid 4x2)
        # ==================================================================
        self.container_cards = ctk.CTkFrame(self.container, fg_color="transparent")
        self.container_cards.grid(row=2, column=0, sticky="nsew", padx=40, pady=(0, 30))
        self.container_cards.grid_columnconfigure(0, weight=1)
        self.container_cards.grid_columnconfigure(1, weight=1)
        self.container_cards.grid_columnconfigure(2, weight=1)
        self.container_cards.grid_columnconfigure(3, weight=1)

        cards = [
            ("CAMINHO ABISSAL", "1", "personagens concluídos"),
            ("PODER MÉDIO", "617,134", ""),
            ("TORRE DAS ILUSÕES", "25", "personagens concluídos"),
            ("VOID (1, 2 E 3)", "11", "personagens concluídos"),
            ("VOID 4", "5", "personagens concluídos"),
            ("NÍVEL DO CHASER", "385", ""),
            ("DESPERTAR COMPLETO", "18", "characters complete"),
            ("LIBERTAÇÃO COMPLETA", "0", "characters complete"),
        ]

        for idx, (titulo, valor, subtitulo) in enumerate(cards):
            linha = idx // 4
            coluna = idx % 4
            self._criar_card(
                self.container_cards,
                titulo=titulo,
                valor=valor,
                subtitulo=subtitulo,
                linha=linha,
                coluna=coluna,
            )

        # ==================================================================
        # BOTÕES AÇÕES RÁPIDAS (abaixo do cabeçalho, lado direito)
        # ==================================================================
        self.acoes = ctk.CTkFrame(self.container, fg_color="transparent")
        self.acoes.grid(row=0, column=0, sticky="e", padx=40, pady=(30, 0))
        # Posicionado acima do bloco import via place para ficar flutuante à direita
        # (alternativa simples ao grid complexo)

        icone_dungeon = carregar_imagem(None, tamanho=(18, 18))  # sem ícone real
        self.btn_zerar = ctk.CTkButton(
            self.acoes,
            text="↻ Zerar dungeons semanais",
            width=200,
            height=40,
            corner_radius=10,
            fg_color="#ffffff",
            text_color="#000000",
            hover_color="#dddddd",
            command=self.zerar_dungeons,
        )
        self.btn_zerar.pack(side="left", padx=(0, 12))

        # Missão Rápida: Alternar (switch)
        self.frame_missao = ctk.CTkFrame(self.acoes, fg_color="transparent")
        self.frame_missao.pack(side="left")

        self.switch_missao = ctk.CTkSwitch(
            self.frame_missao,
            text="Missão Rápida: Alternar",
            command=self.alternar_missao,
        )
        self.switch_missao.pack(pady=(8, 0))

    # ------------------------------------------------------------------
    # Métodos visuais / auxiliares
    # ------------------------------------------------------------------
    def _aplicar_fundo(self):
        """Tenta aplicar imagem de fundo; senão, cor escura sólida."""
        img_fundo = carregar_imagem(CAMINHO_FUNDO, tamanho=(1200, 760))
        if img_fundo:
            self.lbl_fundo = ctk.CTkLabel(self.container, image=img_fundo, text="")
            self.lbl_fundo.image = img_fundo  # manter referência
            self.lbl_fundo.place(relx=0.5, rely=0.5, anchor="center")
        else:
            # Sem imagem: cor escura para simular o fundo
            self.container.configure(fg_color=("#1a1a2e", "#121212"))

    def _criar_card(self, parent, titulo, valor, subtitulo, linha, coluna):
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            fg_color=("#333333", "#222222"),
            border_width=1,
            border_color=("#444444", "#333333"),
        )
        card.grid(row=linha, column=coluna, padx=10, pady=10, sticky="nsew")
        parent.grid_rowconfigure(linha, weight=1)
        parent.grid_columnconfigure(coluna, weight=1)

        ctk.CTkLabel(
            card,
            text=titulo,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#bbbbbb",
        ).pack(anchor="w", padx=16, pady=(16, 4))

        ctk.CTkLabel(
            card,
            text=valor,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#ffffff",
        ).pack(anchor="w", padx=16, pady=(0, 2))

        if subtitulo:
            ctk.CTkLabel(
                card,
                text=subtitulo,
                font=ctk.CTkFont(size=12),
                text_color="#888888",
            ).pack(anchor="w", padx=16, pady=(0, 12))

        # Check apenas no card Nível do Chaser
        if titulo == "NÍVEL DO CHASER":
            chk = ctk.CTkCheckBox(card, text="", command=self.marcar_chaser)
            chk.place(relx=0.92, rely=0.88)

    # ------------------------------------------------------------------
    # Ações dos botões
    # ------------------------------------------------------------------
    def escolher_arquivo(self):
        caminho = filedialog.askopenfilename(
            title="Selecionar planilha Excel",
            filetypes=[("Excel", "*.xlsx *.xls"), ("Todos", "*.*")],
        )
        if caminho:
            self.arquivo_selecionado = caminho
            nome = os.path.basename(caminho)
            self.lbl_arquivo.configure(state="normal")
            self.lbl_arquivo.delete(0, "end")
            self.lbl_arquivo.insert(0, nome)
            self.lbl_arquivo.configure(state="readonly")

    def importar_excel(self):
        if not self.arquivo_selecionado:
            # Simples aviso visual (pode ser substituído por CTkMessagebox)
            self.lbl_arquivo.configure(placeholder_text="Selecione um arquivo primeiro")
            return
        print(f"Importando: {self.arquivo_selecionado}")
        # Aqui você chamaria sua lógica de importação existente

    def exportar_excel(self):
        print("Exportar Excel clicado")
        # Integrar com sua função save_excel / exportar_para_excel existente

    def zerar_dungeons(self):
        print("Zerar dungeons semanais clicado")

    def alternar_missao(self):
        estado = "ativada" if self.switch_missao.get() else "desativada"
        print(f"Missão Rápida {estado}")

    def marcar_chaser(self):
        print("Check Nível do Chaser toggled")


if __name__ == "__main__":
    app = TelaPrincipal()
    app.mainloop()

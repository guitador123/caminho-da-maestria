# -*- coding: utf-8 -*-
"""
Janela "MINHA CONTA" (o perfil).

Permite:
  - trocar a **foto** (qualquer imagem do computador) e grava no Supabase;
  - alterar o **Nick**;
  - **trocar o e-mail**;
  - **trocar a senha**;
  - **sair (logout)**.

A foto e guardada em base64 na coluna `user_profiles.avatar` (redimensionada
para 128x128 para nao pesar no banco). Se a coluna nao existir, a foto vale
so nesta sessao (o app avisa).
"""

import base64
import os
import tempfile
import tkinter as tk

import customtkinter as ctk

import caminhos
import supabase_db as db
import tema_visual as tv
from registro import falha

CORES = {
    "fundo": "#141221",
    "painel": "#1e1a30",
    "painel_borda": "#332d4d",
    "texto": "#f2f0fa",
    "suave": "#a49dc4",
    "roxo": "#8b5cf6",
    "verde": "#22c55e",
    "erro": "#fb7185",
    "laranja": "#f5c451",
}

TAMANHO_FOTO = 128


def _para_base64(caminho, lado=TAMANHO_FOTO):
    """Redimensiona a imagem e devolve o base64 (PNG)."""
    from PIL import Image
    with Image.open(caminho) as original:
        foto = original.convert("RGBA")
        m = min(foto.width, foto.height)
        foto = foto.crop(((foto.width - m) // 2, (foto.height - m) // 2,
                          (foto.width - m) // 2 + m, (foto.height - m) // 2 + m))
        foto = foto.resize((lado, lado), Image.LANCZOS)
        temporario = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
        temporario.close()
        try:
            foto.save(temporario.name, format="PNG")
            with open(temporario.name, "rb") as arquivo:
                return base64.b64encode(arquivo.read()).decode("ascii")
        finally:
            try:
                os.unlink(temporario.name)
            except OSError:
                falha("apagar o temporario do avatar")


def _de_base64(dados):
    """Base64 -> arquivo temporario (para o PIL)."""
    if not dados:
        return None
    try:
        bruto = base64.b64decode(dados)
    except Exception:
        falha("decodificar o avatar")
        return None
    temporario = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    temporario.write(bruto)
    temporario.close()
    return temporario.name


class JanelaPerfil(ctk.CTkToplevel):
    """Edicao do perfil do usuario."""

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self.title("Minha conta")
        caminhos.aplicar_icone(self)
        self.geometry("620x900")
        self.resizable(False, False)
        self.configure(fg_color=CORES["fundo"])
        self.transient(app)

        self.status_var = tk.StringVar(value="")
        self.erro_var = tk.StringVar(value="")
        self.nick_var = tk.StringVar(value=getattr(app, "perfil_nick", "") or "")
        self.email_var = tk.StringVar(value="")

        self._montar()
        self.after(80, self._focar)

    # ------------------------------------------------------------- UI ------
    def _montar(self):
        topo = ctk.CTkFrame(self, fg_color="transparent")
        topo.pack(fill="x", padx=22, pady=(18, 4))
        ctk.CTkLabel(topo, text="MINHA CONTA", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=CORES["texto"]).pack(side="left")
        ctk.CTkLabel(topo, text="perfil da conta", font=ctk.CTkFont(size=12),
                     text_color=CORES["suave"]).pack(side="left", padx=10, pady=(8, 0))

        rolagem = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                         scrollbar_button_color="#3a3358")
        rolagem.pack(fill="both", expand=True, padx=18, pady=(6, 4))

        # --- a foto -------------------------------------------------------
        ctk.CTkLabel(rolagem, text="FOTO", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=4, pady=(10, 4))
        self.foto_preview = ctk.CTkLabel(rolagem, text="", width=128, height=128,
                                         corner_radius=64, fg_color=CORES["painel"],
                                         text_color=CORES["suave"],
                                         font=ctk.CTkFont(size=42, weight="bold"))
        self.foto_preview.pack(anchor="w", padx=4)
        ctk.CTkLabel(rolagem, text="Escolha a foto (um dos 25 personagens)",
                     font=ctk.CTkFont(size=11),
                     text_color=CORES["suave"]).pack(anchor="w", padx=4, pady=(2, 4))
        # altura para as 5 linhas de 5: os 25 icones cabem sem rolar
        grade = ctk.CTkScrollableFrame(rolagem, fg_color=CORES["painel"],
                                       corner_radius=10, height=336,
                                       scrollbar_button_color="#3a3358")
        grade.pack(fill="x", padx=4, pady=(2, 4))
        self._grade_fotos = grade
        self._botoes_foto = {}
        # as 5 colunas ficam com o tamanho fixo (sem se espalhar): assim os
        # 25 icones cabem todos, sem cortar a 5a coluna
        for coluna in range(5):
            grade.grid_columnconfigure(coluna, weight=0, minsize=62)
        self._montar_grade_fotos()

        # --- o nick -------------------------------------------------------
        ctk.CTkLabel(rolagem, text="NICK", font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=4, pady=(12, 4))
        linha_nick = ctk.CTkFrame(rolagem, fg_color="transparent")
        linha_nick.pack(fill="x", padx=4)
        self.entrada_nick = ctk.CTkEntry(linha_nick, height=38, corner_radius=8,
                                         fg_color=CORES["painel"],
                                         border_color=CORES["painel_borda"],
                                         text_color=CORES["texto"],
                                         font=ctk.CTkFont(size=15),
                                         textvariable=self.nick_var)
        self.entrada_nick.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(linha_nick, text="Salvar", width=90, height=38,
                      corner_radius=8, fg_color=CORES["verde"],
                      hover_color="#16a34a", text_color="#08130d",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._salvar_nick).pack(side="left", padx=(8, 0))

        # --- e-mail -------------------------------------------------------
        self._secao(rolagem, "E-MAIL")
        linha_email = ctk.CTkFrame(rolagem, fg_color="transparent")
        linha_email.pack(fill="x", padx=4)
        self.entrada_email = ctk.CTkEntry(linha_email, height=38, corner_radius=8,
                                          fg_color=CORES["painel"],
                                          border_color=CORES["painel_borda"],
                                          text_color=CORES["texto"],
                                          font=ctk.CTkFont(size=14),
                                          textvariable=self.email_var)
        self.entrada_email.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(linha_email, text="Trocar", width=100, height=38,
                      corner_radius=8, fg_color="#2a2440", hover_color="#372f52",
                      text_color=CORES["texto"], font=ctk.CTkFont(size=13),
                      command=self._trocar_email).pack(side="left", padx=(8, 0))

        # --- senha --------------------------------------------------------
        self._secao(rolagem, "SENHA")
        linha_senha = ctk.CTkFrame(rolagem, fg_color="transparent")
        linha_senha.pack(fill="x", padx=4)
        self.entrada_senha = ctk.CTkEntry(linha_senha, height=38, corner_radius=8,
                                          fg_color=CORES["painel"],
                                          border_color=CORES["painel_borda"],
                                          text_color=CORES["texto"],
                                          show="*", font=ctk.CTkFont(size=14))
        self.entrada_senha.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(linha_senha, text="Trocar", width=100, height=38,
                      corner_radius=8, fg_color="#2a2440", hover_color="#372f52",
                      text_color=CORES["texto"], font=ctk.CTkFont(size=13),
                      command=self._trocar_senha).pack(side="left", padx=(8, 0))

        # --- sair ---------------------------------------------------------
        ctk.CTkButton(rolagem, text="SAIR DA CONTA (LOGOUT)", height=42,
                      corner_radius=8, fg_color="#4a1028", hover_color="#6b1739",
                      text_color="#ff9ab5", font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._sair).pack(fill="x", padx=4, pady=(20, 8))

        ctk.CTkLabel(rolagem, textvariable=self.erro_var,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CORES["erro"]).pack(anchor="w", padx=4, pady=(4, 8))
        ctk.CTkLabel(rolagem, textvariable=self.status_var,
                     font=ctk.CTkFont(size=12),
                     text_color=CORES["suave"]).pack(anchor="w", padx=4, pady=(2, 12))

        self._atualizar_preview()

    def _secao(self, pai, titulo):
        ctk.CTkLabel(pai, text=titulo, font=ctk.CTkFont(size=11, weight="bold"),
                     text_color=CORES["roxo"]).pack(anchor="w", padx=4, pady=(14, 4))

    def _focar(self):
        try:
            self.focus_set()
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("focar a janela de perfil")

    # --------------------------------------------------------- acoes ------
    def _atualizar_preview(self):
        """Mostra a foto escolhida (ou a inicial do nick)."""
        caminho = getattr(self.app, "perfil_avatar_temp", None)
        if not caminho:
            try:
                caminho = self.app._foto_do_perfil()
            except Exception:
                caminho = None
        if caminho:
            try:
                from PIL import Image, ImageDraw
                foto = tv.recorte_quadrado(Image.open(caminho).convert("RGBA"))
                foto = foto.resize((128, 128), Image.LANCZOS)
                mascara = Image.new("L", (128, 128), 0)
                ImageDraw.Draw(mascara).ellipse((0, 0, 127, 127), fill=255)
                foto.putalpha(mascara)
                # o CTk precisa de CTkImage (para escalar em telas HiDPI)
                self._preview_ctk = ctk.CTkImage(light_image=foto, dark_image=foto,
                                                 size=(128, 128))
                self.foto_preview.configure(image=self._preview_ctk, text="")
                return
            except Exception:
                falha("mostrar a previa da foto")
        inicial = (self.nick_var.get() or "?")[:1].upper()
        self.foto_preview.configure(image=None, text=inicial)

    def _montar_grade_fotos(self):
        """Grade com as 25 fotos de perfil (uma por personagem)."""
        from opcoes import PERSONAGENS
        pasta = os.path.join(caminhos.assets_dir(), "assets", tv.PASTA_PERFIL)
        for botao in self._botoes_foto.values():
            try:
                botao.destroy()
            except tk.TclError:
                pass                      # janela ja fechada
            except Exception:
                falha("limpar a grade de fotos")
        self._botoes_foto = {}
        grade = self._grade_fotos
        colunas = 5
        for indice, nome in enumerate(PERSONAGENS):
            caminho = os.path.join(pasta, f"{nome.lower()}_icon.png")
            if not os.path.exists(caminho):
                caminho = os.path.join(pasta, f"{nome}_icon.png")
            selecionado = (str(self.app.perfil_personagem or "").lower()
                           == nome.lower())
            if os.path.exists(caminho):
                try:
                    from PIL import Image, ImageDraw
                    foto = tv.recorte_quadrado(
                        Image.open(caminho).convert("RGBA"))
                    foto = foto.resize((48, 48), Image.LANCZOS)
                    mascara = Image.new("L", (48, 48), 0)
                    ImageDraw.Draw(mascara).ellipse((0, 0, 47, 47), fill=255)
                    foto.putalpha(mascara)
                    self._fotos_tk = getattr(self, "_fotos_tk", {})
                    self._fotos_tk[nome] = ctk.CTkImage(light_image=foto,
                                                        dark_image=foto,
                                                        size=(48, 48))
                    botao = ctk.CTkButton(
                        grade, text="", width=52, height=52, corner_radius=26,
                        image=self._fotos_tk[nome],
                        fg_color=CORES["roxo"] if selecionado else "transparent",
                        hover_color="#2f2949", border_width=0,
                        command=lambda n=nome: self._escolher_foto(n))
                except Exception:
                    botao = ctk.CTkButton(
                        grade, text=nome[:2].upper(), width=52, height=52,
                        corner_radius=26, fg_color="transparent",
                        hover_color="#2f2949", border_width=1,
                        border_color=CORES["roxo"] if selecionado
                        else CORES["painel_borda"],
                        text_color=CORES["suave"], font=ctk.CTkFont(size=12),
                        command=lambda n=nome: self._escolher_foto(n))
            else:
                # ainda sem a imagem: mostra so o nome
                botao = ctk.CTkButton(
                    grade, text=nome[:2].upper(), width=52, height=52,
                    corner_radius=26, fg_color="transparent",
                    hover_color="#2f2949", border_width=1,
                    border_color=CORES["roxo"] if selecionado
                    else CORES["painel_borda"],
                    text_color=CORES["suave"], font=ctk.CTkFont(size=12),
                    command=lambda n=nome: self._escolher_foto(n))
            botao.grid(row=indice // colunas, column=indice % colunas,
                       padx=4, pady=4)
            self._botoes_foto[nome] = botao

    def _escolher_foto(self, nome):
        """Usa a foto do personagem escolhido (o que existe na pasta)."""
        self.app.perfil_personagem = nome
        self.app.perfil_avatar = ""
        self.app.perfil_avatar_temp = None
        self._montar_grade_fotos()
        self._atualizar_preview()
        # o hero muda na hora
        self.app._desenhar_perfil()
        gravado = self.app._salvar_perfil()
        if gravado:
            self.status_var.set(f"Foto: {nome} (guardada no Supabase).")
        else:
            self.status_var.set(f"Foto: {nome} (so nesta sessao: a coluna "
                                f"avatar do banco ainda nao existe).")

    def _escolher_arquivo(self):
        from tkinter import filedialog
        caminho = filedialog.askopenfilename(
            title="Escolher a foto do perfil",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp *.bmp *.gif"),
                       ("Todos", "*.*")])
        if not caminho:
            return
        try:
            dados = _para_base64(caminho)
        except Exception as erro:
            self.erro_var.set(f"Erro ao ler a imagem: {erro}")
            return
        self.app.perfil_avatar = dados
        self.app.perfil_avatar_temp = _de_base64(dados)
        self._atualizar_preview()
        self.app._desenhar_perfil()
        gravado = self.app._salvar_perfil()
        if gravado:
            self.status_var.set("Foto atualizada e guardada no Supabase.")
        else:
            self.status_var.set("Foto atualizada (so nesta sessao: a coluna "
                                "avatar do banco ainda nao existe).")

    def _salvar_nick(self):
        nick = (self.nick_var.get() or "").strip()
        self.app.perfil_nick = nick
        self.app._desenhar_perfil()
        gravado = self.app._salvar_perfil()
        if gravado:
            self.status_var.set("Nick salvo.")
        else:
            self.status_var.set("Nick alterado (so nesta sessao: a coluna "
                                "nick do banco ainda nao existe).")

    def _trocar_email(self):
        email = (self.email_var.get() or "").strip()
        if "@" not in email:
            self.erro_var.set("Informe um e-mail valido.")
            return
        erro = db.trocar_email(self.app.supabase, email)
        if erro:
            self.erro_var.set(f"Erro ao trocar o e-mail: {erro}")
            return
        self.erro_var.set("")
        self.status_var.set("E-mail alterado. Confirme o novo e-mail.")

    def _trocar_senha(self):
        senha = self.entrada_senha.get()
        if len(senha) < 6:
            self.erro_var.set("A senha precisa ter pelo menos 6 caracteres.")
            return
        erro = db.trocar_senha(self.app.supabase, senha)
        if erro:
            self.erro_var.set(f"Erro ao trocar a senha: {erro}")
            return
        self.entrada_senha.delete(0, "end")
        self.erro_var.set("")
        self.status_var.set("Senha alterada.")

    def _sair(self):
        self.app.fazer_logout()
        self.destroy()

"""
Tela de login / cadastro / recuperacao de senha (Supabase Auth).

Visual: o logo Akkatsuki (assets/login.png) e assado no PIL como fundo,
com um cartao de vidro; os textos vao no canvas do Tk e os campos/botoes
solidos sao widgets CTk. A cor de destaque (botao Entrar) e extraida da
própria imagem do logo.

Gate de entrada do Controle Grand Chase: depois de autenticar, abre o
app_grandchase passando o usuario logado e o cliente Supabase com sessao
(a sessao fica em memoria no Client, por isso ele viaja junto).

Uso:
    python login.py            -> abre a tela e, no sucesso, o app principal
    python app_grandchase.py   -> redireciona para esta mesma tela
"""

import json
import re

import tkinter as tk
from tkinter import font as tkfont

import customtkinter as ctk

import auth
import cache_local
import caminhos
from registro import falha
import tema_login as tl

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

TITULO_APP = "Caminho da Maestria"
SUBTITULO_APP = "Controle de conta, feita para a Akkatsuki"

ROTULOS = {"Entrar": "entrar", "Criar conta": "conta", "Recuperar": "recuperar"}
INVERSO = {v: k for k, v in ROTULOS.items()}

# Mensagens comuns do Supabase Auth traduzidas para portugues
ERROS_PT = [
    ("invalid login credentials", "E-mail ou senha incorretos."),
    ("email not confirmed", "Confirme seu e-mail (caixa de entrada) antes de entrar."),
    ("user already registered", "Este e-mail ja esta cadastrado."),
    ("already registered", "Este e-mail ja esta cadastrado."),
    ("password should be at least", "A senha precisa de pelo menos 6 caracteres."),
    ("unable to validate email address", "E-mail invalido."),
    ("signup is disabled", "Cadastro temporariamente desativado."),
    ("for security purposes", "Muitas tentativas. Aguarde alguns minutos e tente de novo."),
    ("rate limit", "Muitas tentativas. Aguarde alguns minutos e tente de novo."),
    ("email rate limit exceeded", "Muitas tentativas. Aguarde alguns minutos e tente de novo."),
    ("smtp", "Nao foi possivel enviar o e-mail agora. Tente mais tarde."),
    ("database error", "Erro no banco de dados. Tente novamente."),
    ("no row", "Usuario nao encontrado."),
]


def mensagem_erro(erro) -> str:
    """Converte uma excecao do Supabase em mensagem amigavel."""
    bruto = (
        getattr(erro, "msg", None)
        or getattr(erro, "message", None)
        or getattr(erro, "details", None)
        or str(erro)
    )
    bruto = str(bruto)
    for trecho, texto in ERROS_PT:
        if trecho in bruto.lower():
            return texto
    return bruto[:160]


SEM_INTERNET = ("Sem conexão com a internet. Para entrar offline, entre uma "
                "vez com internet com \"Memorizar conta\" marcado.")
SENHA_OFFLINE = ("Sem conexão com a internet, e a senha não confere com a "
                 "última usada neste computador.")


def entrar(email, senha):
    """Login com internet; sem internet, entra com a copia deste PC.

    Devolve (cliente, resposta). Offline, a resposta tem `offline=True` e
    o cliente ainda nao tem sessao (ela volta com a internet).
    """
    try:
        return auth.login(email, senha)
    except Exception as erro:
        if not cache_local.eh_erro_de_rede(erro):
            raise
        falha("[Login] sem internet", erro)
        conta = cache_local.conta_offline(email, senha)
        if conta is None:
            raise RuntimeError(SENHA_OFFLINE
                               if cache_local.conta_memorizada(email)
                               else SEM_INTERNET) from None
        from types import SimpleNamespace
        usuario = SimpleNamespace(id=conta["user_id"], email=conta["email"])
        return auth.get_supabase(), SimpleNamespace(user=usuario,
                                                    session=None,
                                                    offline=True)


def _ler_prefs():
    """Preferencias locais (conta memorizada)."""
    try:
        with open(caminhos.preferencias(), "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except Exception:
        falha("ler login_prefs.json")
        return {}


def _salvar_prefs(dados):
    try:
        with open(caminhos.preferencias(), "w", encoding="utf-8") as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    except Exception:
        falha("gravar login_prefs.json")


class LoginApp(ctk.CTk):
    """Janela de autenticacao (login, cadastro e recuperacao de senha)."""

    def __init__(self, resultado: dict):
        super().__init__()
        self.resultado = resultado          # preenchido no sucesso: user + supabase
        self._ocupado = False
        self.modo = "entrar"
        self.destaque = tl.cor_de_destaque()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title("Caminho da Maestria - Entrar")
        self._aplicar_icone()
        self.geometry(f"{tl.DESIGN_W}x{tl.DESIGN_H}")
        self.resizable(False, False)

        # --- camada 1/2: cenario (PIL) + textos (canvas) ----------------
        self.canvas = tk.Canvas(self, bg="#0b0812", highlightthickness=0, bd=0)
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._criar_widgets()
        self._montar_cenario()
        self.mostrar_modo("Entrar")
        self.protocol("WM_DELETE_WINDOW", self._fechar)

    # ------------------------------------------------------------------ UI --
    def _criar_widgets(self):
        """Widgets solidos (segmentado, campos e caixas de selecao)."""
        self.ent_email = self._campo("seuemail@exemplo.com")
        self.ent_nome = self._campo("como a guilda te chama")
        self.ent_senha = self._campo("sua senha", show="*")
        self.ent_senha2 = self._campo("minimo de 6 caracteres", show="*")
        self.ent_confirma = self._campo("confirme a senha", show="*")
        self.ent_email2 = self._campo("seuemail@exemplo.com")
        self.ent_email3 = self._campo("seuemail@exemplo.com")
        self.ent_senha3 = self._campo("sua senha", show="*")

        # as caixas de selecao ("Mostrar senha" / "Memorizar conta") sao
        # desenhadas no canvas: o CTkCheckBox pintaria um retangulo cinza
        # (fundo transparente resolve para a cor da janela)
        self._checks = {"mostrar": False, "memorizar": False}

    def _campo(self, placeholder, show=None):
        entrada = ctk.CTkEntry(self, placeholder_text=placeholder, height=38,
                               corner_radius=10, fg_color=tl.CORES["campo"],
                               border_color=tl.CORES["campo_borda"],
                               border_width=1,
                               text_color="#ffffff",
                               placeholder_text_color="#6f668f",
                               font=ctk.CTkFont(size=13))
        if show:
            entrada.configure(show=show)
        return entrada

    # ------------------------------------------------------------ cenario ---
    def _montar_cenario(self):
        """Fundo (logo + cartao de vidro) + cabecalho e textos fixos."""
        largura = self.winfo_width() or tl.DESIGN_W
        altura = self.winfo_height() or tl.DESIGN_H
        try:
            img = tl.renderizar_cenario(caminhos.fundo_login(), largura, altura,
                                        self.destaque)
            from PIL import ImageTk
            self.cenario_tk = ImageTk.PhotoImage(img)
            self.canvas.delete("cenario")
            self.canvas.create_image(0, 0, anchor="nw", image=self.cenario_tk,
                                     tags="cenario")
        except Exception as e:
            falha("[Login] gerar o cenario", e)

        self._desenhar_cabecalho()

    def _fonte(self, tamanho, peso="normal", familia="Segoe UI"):
        return (familia, tamanho, peso)

    def _fonte_obj(self, tamanho, peso="normal", familia="Segoe UI"):
        if not hasattr(self, "_fontes"):
            self._fontes = {}
        chave = (familia, tamanho, peso)
        if chave not in self._fontes:
            self._fontes[chave] = tkfont.Font(family=familia, size=tamanho,
                                              weight=peso)
        return self._fontes[chave]

    def _desenhar_cabecalho(self):
        """Titulo, subtitulo e rodape (ficam no canvas)."""
        self.canvas.delete("cabecalho")
        x = tl.COLUNA[0]
        tl.texto_espacado(self.canvas, x, tl.EYEBROW_Y,
                          "GRAND CHASE \u00b7 AKKATSUKI",
                          self._fonte_obj(11, "bold"), tl.CORES["olho"])
        self.canvas.create_text(x, tl.TITULO_Y, text=TITULO_APP,
                                font=self._fonte(28, "bold", "Segoe UI Black"),
                                fill=tl.CORES["texto"], anchor="nw",
                                tags="cabecalho")
        self.canvas.create_text(x, tl.SUBTITULO_Y, text=SUBTITULO_APP,
                                font=self._fonte(13), fill=tl.CORES["suave"],
                                anchor="nw", tags="cabecalho")
        self.canvas.create_text(
            tl.DESIGN_W / 2, tl.DESIGN_H - 34,
            text="Seus dados ficam protegidos: cada membro ve apenas os "
                 "proprios personagens.",
            font=self._fonte(11), fill="#7b7399", anchor="n",
            tags="cabecalho")

    # --------------------------------------------------------- formulario ---
    def _desenhar_segmentos(self):
        """Segmentado (Entrar / Criar conta / Recuperar) desenhado no canvas.

        O CTkSegmentedButton do CTk 6 usa a MESMA cor de texto para o item
        selecionado e os demais -> texto claro sobre o verde ficava ilegivel.
        Aqui o item ativo recebe texto ESCURO sobre a pilula verde.
        """
        from PIL import ImageTk
        x = tl.COLUNA[0]
        largura = tl.COLUNA[1] - tl.COLUNA[0]
        y = tl.SEGMENTO_Y
        altura = tl.SEGMENTO_H
        segmento = largura / 3

        # trilha
        trilha = ImageTk.PhotoImage(tl.retangulo_arredondado(
            tl.CORES["segmento"], largura, altura, raio=10))
        self._fotos = getattr(self, "_fotos", {})
        self._fotos["trilha"] = trilha
        self.canvas.create_image(x, y, anchor="nw", image=trilha)

        # pílula do item selecionado (criada ANTES dos textos: fica atras)
        self._fotos["pills"] = ImageTk.PhotoImage(tl.retangulo_arredondado(
            self.destaque, segmento - 6, altura - 6, raio=8))
        self._item_pilula = self.canvas.create_image(
            x + 3, y + 3, anchor="nw", image=self._fotos["pills"])

        self._itens_segmentos = []
        for indice, rotulo in enumerate(("Entrar", "Criar conta", "Recuperar")):
            centro = x + segmento * indice + segmento / 2
            item = self.canvas.create_text(
                centro, y + altura / 2, text=rotulo,
                font=self._fonte(13, "bold"), fill="#cfc7e6", anchor="center")
            self._itens_segmentos.append(item)
            # area de clique
            area = self.canvas.create_rectangle(
                x + segmento * indice, y, x + segmento * (indice + 1), y + altura,
                fill="", outline="", tags=("hit", f"seg:{indice}"))
            self.canvas.tag_bind(area, "<Button-1>",
                                 lambda e, i=indice: self._clique_segmento(i))

        self._selecionar_segmento()

    def _clique_segmento(self, indice):
        if self._ocupado or getattr(self, "_bloqueado", False):
            return
        self.mostrar_modo(("Entrar", "Criar conta", "Recuperar")[indice])

    def _selecionar_segmento(self):
        """Move a pilula para o item ativo e ajusta as cores do texto."""
        if not getattr(self, "_itens_segmentos", None):
            return
        x = tl.COLUNA[0]
        largura = tl.COLUNA[1] - tl.COLUNA[0]
        segmento = largura / 3
        indice = ("entrar", "conta", "recuperar").index(self.modo)

        if getattr(self, "_item_pilula", None):
            self.canvas.coords(self._item_pilula,
                               x + segmento * indice + 3, tl.SEGMENTO_Y + 3)
        for i, item in enumerate(self._itens_segmentos):
            self.canvas.itemconfigure(
                item,
                fill=tl.tom_texto_sobre(self.destaque) if i == indice else "#cfc7e6")

    def _limpar_formulario(self):
        """Esconde todos os widgets do formulario antes de montar o modo."""
        for widget in (self.ent_email, self.ent_nome, self.ent_senha,
                       self.ent_senha2, self.ent_confirma, self.ent_email2,
                       self.ent_email3, self.ent_senha3):
            widget.place_forget()

    def _posicionar(self, widget, x, y, largura, altura):
        try:
            widget.configure(width=max(1, int(largura)), height=max(1, int(altura)))
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("posicionar widget do login")
        widget.place(x=int(x), y=int(y))

    def _campos_do_modo(self):
        return {
            "entrar": [("E-mail", self.ent_email),
                       ("Senha", self.ent_senha)],
            "conta": [("Nome de usuario", self.ent_nome),
                      ("E-mail", self.ent_email2),
                      ("Senha", self.ent_senha2),
                      ("Confirmar senha", self.ent_confirma)],
            "recuperar": [("E-mail", self.ent_email3)],
        }[self.modo]

    def _montar_formulario(self):
        """Monta campos, botoes e links do modo atual."""
        self._limpar_formulario()
        self.canvas.delete("formulario")

        x = tl.COLUNA[0]
        largura = tl.COLUNA[1] - tl.COLUNA[0]

        # --- segmentado (Entrar / Criar conta / Recuperar) ----------------
        self._desenhar_segmentos()

        campos = self._campos_do_modo()
        tem_checks = self.modo == "entrar"
        texto = None
        if self.modo == "recuperar":
            texto = ("Informe o e-mail da conta. Enviaremos um link para "
                     "redefinir a senha.")

        altura_label = 17
        altura_campo = 38
        gap_campo = 10
        altura_check = 26
        altura_botao = 46
        altura_link = 24

        # altura total do conteudo (para centralizar no cartao)
        total = 0
        if texto:
            total += 56
        total += len(campos) * (altura_label + altura_campo + gap_campo)
        if tem_checks:
            total += altura_check + 12
        total += altura_botao + 16
        total += altura_link

        y = tl.FORM_TOPO + max(0, (tl.FORM_BASE - tl.FORM_TOPO - total) // 2)

        if texto:
            self.canvas.create_text(x, y, text=texto, font=self._fonte(12),
                                    fill=tl.CORES["suave"], anchor="nw",
                                    justify="left", width=largura,
                                    tags="formulario")
            y += 56

        for rotulo, entrada in campos:
            self.canvas.create_text(x, y, text=rotulo.upper(),
                                    font=self._fonte(11, "bold"),
                                    fill=tl.CORES["olho"], anchor="nw",
                                    tags="formulario")
            self._posicionar(entrada, x, y + altura_label, largura, altura_campo)
            y += altura_label + altura_campo + gap_campo

        if tem_checks:
            self._desenhar_check("mostrar", x, y + 4, "Mostrar senha")
            self._desenhar_check("memorizar", x + 165, y + 4, "Memorizar conta")
            y += altura_check + 12

        # --- botao principal (gradiente na cor de destaque) --------------
        from PIL import ImageTk
        grad = ImageTk.PhotoImage(tl.botao_gradiente(self.destaque, largura,
                                                      altura_botao, raio=12))
        self._fotos = getattr(self, "_fotos", {})
        self._fotos["botao"] = grad
        self.canvas.create_image(x, y, anchor="nw", image=grad, tags="formulario")
        rotulo = {"entrar": "Entrar", "conta": "Criar conta",
                  "recuperar": "Enviar link de redefinicao"}[self.modo]
        self.canvas.create_text(x + largura / 2, y + altura_botao / 2, text=rotulo,
                                font=self._fonte(15, "bold"),
                                fill=tl.tom_texto_sobre(self.destaque),
                                anchor="center", tags="formulario")
        item = self.canvas.create_rectangle(x, y, x + largura, y + altura_botao,
                                            fill="", outline="",
                                            tags=("hit", "botao", "formulario"))
        self.canvas.tag_bind(item, "<Button-1>", lambda e: self._acao_principal())
        y += altura_botao + 16

        # --- link --------------------------------------------------------
        texto_link, destino = {
            "entrar": ("Esqueci minha senha", "recuperar"),
            "conta": ("Ja tenho conta", "entrar"),
            "recuperar": ("Voltar ao login", "entrar"),
        }[self.modo]
        item = self.canvas.create_text(x + largura / 2, y + 8, text=texto_link,
                                       font=self._fonte(13, "bold"),
                                       fill=tl._variar(self.destaque, 1.18),
                                       anchor="center",
                                       tags=("hit", "link", "formulario"))
        self.canvas.tag_bind(item, "<Button-1>",
                             lambda e, d=destino: self.mostrar_modo(d))
        y += altura_link

        # --- mensagem de status -------------------------------------------
        self._item_status = self.canvas.create_text(
            x, min(tl.FORM_BASE + 12, y + 6), text="", font=self._fonte(12),
            fill=tl.CORES["erro"], anchor="nw", tags="formulario")

    # ---------------------------------------------------------------- modos --
    def mostrar_modo(self, valor: str):
        chave = ROTULOS.get(valor, valor)
        if chave not in ("entrar", "conta", "recuperar"):
            chave = "entrar"
        self.modo = chave
        self.title(f"Caminho da Maestria - {INVERSO[chave]}")
        self._aplicar_icone()
        self._montar_formulario()
        self._status("")
        foco = {
            "entrar": self.ent_email,
            "conta": self.ent_nome,
            "recuperar": self.ent_email3,
        }[chave]
        foco.focus_set()

    def _cor_status(self, cor):
        try:
            self.canvas.itemconfig(self._item_status, fill=cor)
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("cor do aviso do login")

    def _aviso(self, texto, cor=tl.CORES["erro"]):
        try:
            self.canvas.itemconfig(self._item_status, text=texto)
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("texto do aviso do login")
        self._cor_status(cor)

    def _status(self, texto):
        try:
            self.canvas.itemconfig(self._item_status, text=texto)
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("texto do status do login")

    def _estado_botoes(self, estado):
        # os botoes sao desenhados no canvas: o bloqueio e feito no clique
        self._bloqueado = estado != "normal"

    # ------------------------------------------------------------ senha -----
    def _desenhar_check(self, chave, x, y, texto):
        """Caixa de selecao desenhada no canvas (sem retangulo cinza)."""
        from PIL import ImageTk
        marcado = self._checks.get(chave, False)
        lado = 16
        img = ImageTk.PhotoImage(tl.caixa_marcada(self.destaque, lado, marcado))
        self._fotos = getattr(self, "_fotos", {})
        self._fotos[f"check_{chave}"] = img
        self.canvas.create_image(x, y, anchor="nw", image=img, tags="formulario")
        if marcado:
            self.canvas.create_text(x + lado / 2, y + lado / 2 - 1, text="\u2713",
                                    font=self._fonte(11, "bold"),
                                    fill=tl.tom_texto_sobre(self.destaque),
                                    anchor="center", tags="formulario")
        self.canvas.create_text(x + lado + 8, y + 1, text=texto,
                                font=self._fonte(13), fill=tl.CORES["suave"],
                                anchor="nw", tags="formulario")
        # area de clique
        largura_texto = self._fonte_obj(13).measure(texto)
        item = self.canvas.create_rectangle(x, y, x + lado + 12 + largura_texto,
                                            y + lado + 6, fill="", outline="",
                                            tags=("hit", f"check:{chave}",
                                                  "formulario"))
        self.canvas.tag_bind(item, "<Button-1>",
                             lambda e, c=chave: self._alternar_check(c))

    def _alternar_check(self, chave):
        self._checks[chave] = not self._checks.get(chave, False)
        if chave == "mostrar":
            self._alternar_senha()
        else:
            self._alternar_memorizar()
        self._montar_formulario()

    def _alternar_senha(self):
        mostrar = self._checks.get("mostrar", False)
        for entrada in (self.ent_senha, self.ent_senha2, self.ent_senha3,
                        self.ent_confirma):
            entrada.configure(show="" if mostrar else "*")

    def _alternar_memorizar(self):
        """Desmarcar 'memorizar conta' apaga a conta salva."""
        if not self._checks.get("memorizar", False):
            prefs = _ler_prefs()
            prefs.pop("email", None)
            prefs["lembrar"] = False
            _salvar_prefs(prefs)

    # ------------------------------------------------------- execucao -------
    def _executar(self, trabalho, ao_concluir):
        """Executa uma chamada de rede na propria thread da UI.

        As chamadas sao curtas; rodar na thread do Tk evita o deadlock
        GIL x Tcl que ocorre quando uma thread importa httpx/httpcore de
        forma preguicosa enquanto o mainloop esta ativo.
        """
        if self._ocupado:
            return
        self._ocupado = True
        self._estado_botoes("disabled")
        self._aviso("Aguarde um instante...", "#f1c40f")
        self.update()                      # repinta antes de bloquear
        try:
            resultado = trabalho()
        except Exception as erro:
            self._falhou(erro)
            return
        if not self._viva():               # janela fechada durante a chamada
            return
        self._ocupado = False
        self._estado_botoes("normal")
        ao_concluir(resultado)

    def _viva(self):
        try:
            return bool(self.winfo_exists())
        except tk.TclError:
            return False
        except Exception:
            falha("conferir se o login esta aberto")
            return False

    def _falhou(self, erro):
        falha("[Login] acao da conta", erro)
        if not self._viva():
            return
        self._ocupado = False
        self._estado_botoes("normal")
        self._aviso(mensagem_erro(erro))

    # -------------------------------------------------------- acoes login --
    def _acao_principal(self):
        """Dispara a acao do botao principal conforme o modo."""
        if self.modo == "entrar":
            self._enviar_login()
        elif self.modo == "conta":
            self._enviar_conta()
        else:
            self._enviar_reset()

    def _enviar_login(self):
        if self._ocupado:
            return
        email = self.ent_email.get().strip()
        senha = self.ent_senha.get()
        if not email or not senha:
            return self._aviso("Preencha e-mail e senha.")
        if not EMAIL_RE.match(email):
            return self._aviso("E-mail invalido.")
        self._executar(lambda: entrar(email, senha), self._login_ok)

    def _aplicar_icone(self):
        """Icone da janela (o .ico do app, em todas as abas)."""
        caminhos.aplicar_icone(self)

    def _login_ok(self, resultado):
        sb, resp = resultado
        user = getattr(resp, "user", None)
        if user is None:
            return self._falhou(RuntimeError("Falha ao autenticar."))
        if getattr(resp, "offline", False):
            self.resultado["offline"] = True
            return self._abrir_app(user, sb)
        auth.garantir_perfil(sb, user.id,
                             username=(user.email or "").split("@")[0])
        self._memorizar_conta(user, getattr(resp, "session", None))
        self._abrir_app(user, sb)

    def _memorizar_conta(self, user=None, sessao=None):
        """Guarda (ou apaga) a conta memorizada no computador.

        Memorizada, ela tambem entra sem internet (cache_local): fica um
        hash da senha e o token da sessao, protegidos pelo Windows.
        """
        prefs = _ler_prefs()
        email = self.ent_email.get().strip()
        if self._checks.get("memorizar"):
            prefs["email"] = email
            prefs["lembrar"] = True
            if user is not None:
                cache_local.memorizar_conta(
                    email, user.id, self.ent_senha.get(),
                    getattr(sessao, "refresh_token", None))
        else:
            prefs.pop("email", None)
            prefs["lembrar"] = False
            cache_local.esquecer_conta(email)
        _salvar_prefs(prefs)

    # -------------------------------------------------------- acoes conta --
    def _enviar_conta(self):
        if self._ocupado:
            return
        nome = self.ent_nome.get().strip()
        email = self.ent_email2.get().strip()
        senha = self.ent_senha2.get()
        confirma = self.ent_confirma.get()

        if len(nome) < 2:
            return self._aviso("Informe um nome de usuario (minimo 2 letras).")
        if not EMAIL_RE.match(email):
            return self._aviso("E-mail invalido.")
        if len(senha) < 6:
            return self._aviso("A senha precisa de pelo menos 6 caracteres.")
        if senha != confirma:
            return self._aviso("As senhas nao coincidem.")

        self._executar(lambda: auth.cadastro(email, senha, nome),
                       lambda r: self._conta_ok(r, nome))

    def _conta_ok(self, resultado, nome):
        sb, resp = resultado
        user = getattr(resp, "user", None)
        session = getattr(resp, "session", None)
        if user is None:
            return self._falhou(RuntimeError("Nao foi possivel criar a conta."))
        if session:
            # Sem confirmacao de e-mail: ja entra direto
            auth.garantir_perfil(sb, user.id, username=nome)
            return self._abrir_app(user, sb)
        # Confirmacao de e-mail ativa: volta para a entrada com o aviso
        self.mostrar_modo("Entrar")
        self.ent_email.delete(0, "end")
        self.ent_email.insert(0, self.ent_email2.get().strip())
        self._aviso("Conta criada! Confirme seu e-mail e depois entre "
                    "(caixa de entrada).", cor=tl.CORES["ok"])

    # ------------------------------------------------ acoes recuperar --
    def _enviar_reset(self):
        if self._ocupado:
            return
        email = self.ent_email3.get().strip()
        if not EMAIL_RE.match(email):
            return self._aviso("Informe um e-mail valido.")
        self._executar(lambda: auth.resetar_senha(email), self._reset_ok)

    def _reset_ok(self, _resultado):
        self._aviso("Se o e-mail existir, o link de redefinicao foi enviado "
                    "(confira tambem a caixa de spam).", cor=tl.CORES["ok"])

    # ------------------------------------------------------------ saida ------
    def _liberar_recursos(self):
        """Solta as imagens do Tk ANTES de destruir a janela.

        Sem isso o ImageTk.PhotoImage e finalizado depois do interpretador Tk
        e o processo morre com "alloc: invalid block" ao passar do login
        para a tela principal.
        """
        try:
            self.canvas.delete("all")
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("limpar o canvas do login")
        try:
            self.cenario_tk = None
        except tk.TclError:
            pass                      # janela ja fechada
        except Exception:
            falha("liberar o cenario do login")
        if hasattr(self, "_fotos"):
            self._fotos.clear()

    def _abrir_app(self, user, sb):
        """Entrega o usuario autenticado ao chamador e fecha esta janela."""
        self.resultado["user"] = user
        self.resultado["supabase"] = sb
        self._ocupado = False
        self._liberar_recursos()
        self.destroy()

    def _fechar(self):
        """Fecha a janela (botao X)."""
        self._liberar_recursos()
        self.destroy()

    # ---------------------------------------------------------- memorized ---
    def _aplicar_conta_memorizada(self):
        """Preenche o e-mail salvo (apos o primeiro login)."""
        prefs = _ler_prefs()
        email = prefs.get("email")
        if not email:
            return
        if prefs.get("lembrar", True):
            self.ent_email.insert(0, email)
            self._checks["memorizar"] = True
            self._montar_formulario()


# ---------------------------------------------------------------------------
def abrir_aplicativo():
    """Ponto de entrada: login -> app principal (gate de acesso).

    Antes de tudo, o programa confere no GitHub se tem commit novo e
    atualiza sozinho (se ja estiver na ultima, segue normal).
    """
    try:
        from atualizacao import verificar_e_atualizar
        if verificar_e_atualizar():
            return          # atualizou e ja reiniciou
    except Exception:
        falha("[Atualizacao] verificar no inicio")   # segue na versao atual

    resultado = {}
    janela = LoginApp(resultado)
    janela._aplicar_conta_memorizada()
    janela.mainloop()

    user = resultado.get("user")
    if not user:
        return  # janela fechada sem login: encerra

    from app_grandchase import GrandChaseApp
    app = GrandChaseApp(user=user, supabase=resultado.get("supabase"),
                        offline=bool(resultado.get("offline")))
    app.mainloop()


if __name__ == "__main__":
    abrir_aplicativo()

# -*- coding: utf-8 -*-
"""
Rolagem SUAVE de um tk.Canvas pela roda do mouse.

Antes cada clique da roda andava 40 px de uma vez (seco e lento: ~20
cliques por tela). Agora:

  - o passo e uma FRACAO da altura visivel (o mesmo "peso" em qualquer
    resolucao);
  - a tela DESLIZA ate o destino (desaceleracao exponencial, ~150 ms);
  - cliques seguidos se SOMAM ao destino, e cliques RAPIDOS aceleram (o
    passo cresce ate 3x): girar rapido atravessa a pagina, girar devagar
    continua preciso;
  - a animacao e por TEMPO, nao por quadro: dura o mesmo numa tela leve
    (quadro de 10 ms) ou pesada (quadro de 20 ms);
  - touchpad (delta pequeno e fracionado) rola proporcionalmente.

    rolagem = RolagemSuave(canvas, ao_mover=fixar_cenario)
    canvas.bind("<MouseWheel>", lambda e: rolagem.roda(e.delta))

O canvas precisa de yscrollincrement=1 (senao o Tk arredonda cada
movimento para o passo e a animacao "anda aos trancos").
"""

import math
import time

import tkinter as tk

FRACAO_DA_TELA = 0.22      # quanto cada clique da roda anda
PASSO_MINIMO = 90          # px (janelas muito baixas)
SUAVIDADE = 0.055          # s: constante de tempo da desaceleracao
INTERVALO = 8              # ms entre quadros (o Tk limita ao que conseguir)
JANELA_ACELERACAO = 0.15   # s: cliques mais proximos que isso aceleram
ACELERACAO = 0.35          # quanto cada clique rapido soma ao ritmo
RITMO_MAXIMO = 3.0         # o passo chega a 3x


def limitar(valor, menor, maior):
    return max(menor, min(valor, maior))


def proximo_passo(atual, alvo, segundos, suavidade=SUAVIDADE):
    """Onde a tela fica depois de `segundos` (desaceleracao exponencial).

    Anda uma fracao do que falta, maior quanto mais tempo passou: o
    movimento e o mesmo com quadros rapidos ou lentos. Perto do fim,
    encosta no alvo.
    """
    falta = alvo - atual
    if abs(falta) < 0.75:
        return alvo
    fator = 1.0 - math.exp(-max(0.0, segundos) / suavidade)
    andar = falta * fator
    if abs(andar) < 1.0:                 # nunca "trava" a meio pixel
        andar = math.copysign(min(1.0, abs(falta)), falta)
    return atual + andar


class RolagemSuave:
    def __init__(self, canvas, ao_mover=None, fracao=FRACAO_DA_TELA,
                 minimo=PASSO_MINIMO):
        self.canvas = canvas
        self.ao_mover = ao_mover
        self.fracao = fracao
        self.minimo = minimo
        self.alvo = None
        self._job = None
        self._ultimo = 0.0
        self.ritmo = 1.0                 # multiplicador da aceleracao
        self._ultimo_clique = 0.0
        self._ultimo_delta = 0

    # ------------------------------------------------------------ medidas
    def _limites(self):
        """(maximo do topo, altura visivel) em pixels da pagina."""
        regiao = str(self.canvas.cget("scrollregion")).split()
        total = float(regiao[3]) if len(regiao) == 4 else 0.0
        visivel = max(1, self.canvas.winfo_height())
        return max(0.0, total - visivel), visivel, total

    def topo(self):
        return self.canvas.canvasy(0)

    # -------------------------------------------------------------- roda
    def roda(self, delta):
        """Um evento da roda (delta do Windows: 120 por clique)."""
        try:
            maximo, visivel, _total = self._limites()
        except tk.TclError:
            return
        # aceleracao: cliques seguidos e rapidos aumentam o passo (girar
        # rapido atravessa a pagina; girar devagar continua preciso)
        agora = time.perf_counter()
        rapido = agora - self._ultimo_clique < JANELA_ACELERACAO
        mesmo_sentido = (delta < 0) == (self._ultimo_delta < 0)
        if rapido and mesmo_sentido:
            self.ritmo = min(RITMO_MAXIMO, self.ritmo + ACELERACAO)
        else:
            self.ritmo = 1.0
        self._ultimo_clique, self._ultimo_delta = agora, delta
        passo = max(self.minimo, visivel * self.fracao) * self.ritmo
        base = self.alvo if self.alvo is not None else self.topo()
        self.alvo = limitar(base - (delta / 120.0) * passo, 0.0, maximo)
        if self._job is None:
            # o 1o quadro ja anda como se 1 quadro tivesse passado
            self._ultimo = time.perf_counter() - 0.016
            self._quadro()

    def parar(self):
        """Outra parte do app mexeu na rolagem: esquece o destino."""
        self.alvo = None
        if self._job is not None:
            try:
                self.canvas.after_cancel(self._job)
            except tk.TclError:
                pass
            self._job = None

    def ir_para(self, topo):
        """Posiciona sem animar (pixel do topo)."""
        self.parar()
        self._mover(topo)

    # ------------------------------------------------------------ quadros
    def _mover(self, topo):
        _maximo, _visivel, total = self._limites()
        self.canvas.yview_moveto(topo / total if total > 0 else 0.0)
        if self.ao_mover is not None:
            self.ao_mover()

    def _quadro(self):
        self._job = None
        if self.alvo is None:
            return
        try:
            agora = time.perf_counter()
            segundos, self._ultimo = agora - self._ultimo, agora
            maximo, _visivel, _total = self._limites()
            self.alvo = limitar(self.alvo, 0.0, maximo)
            atual = self.topo()
            novo = proximo_passo(atual, self.alvo, segundos)
            self._mover(novo)
            if novo == self.alvo:
                self.alvo = None
                return
            self._job = self.canvas.after(INTERVALO, self._quadro)
        except tk.TclError:
            self.alvo = None             # janela fechada

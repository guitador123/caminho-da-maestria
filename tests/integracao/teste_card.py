"""
Previa do card de personagem (sem Supabase): renderiza o Uno com os dados
do mockup e salva um PNG.

    python teste_card.py [saida.png]
"""

import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
import sys
import time
import tkinter as tk

from PIL import ImageGrab

import customtkinter as ctk
from card_personagem import CardPersonagem

SAIDA = sys.argv[1] if len(sys.argv) > 1 else "captura_card.png"

DADOS_UNO = {
    "nome": "Uno",
    "poder": 1715342,
    "torre": "30 / 30",
    "vazio_uni": 10,
    "vazio_apo": 34,
    "nucleos_dimensionais": 605,
    "fragmento_vazio_disperso": 161,
    "nucleo": "13 / 13",
    "nucleos_epicos": "9 / 9",
    "libertacao": "INEXISTENTE",
    "libertacao_nucleos": 0,
    "libertacao_epicos": 0,
    "origem": "Origem de Caos",
    "pecas": {"arma": True, "luvas": True, "cota": True, "botas": True,
              "capa": True, "calca": True, "elmo": True, "escudos": True,
              "asas": True, "facas": True, "mascara": True, "diadema": True},
    "acessorios": {"anel": "Anel do Ciclo Infinito",
                   "tornozeleira": "Apocalipse",
                   "brinco": "Brinco do Outro Mundo do Caos",
                   "piercing": "Piercing do Outro Mundo do Caos",
                   "titulo": "Aniquilador do Vazio"},
    # as chaves das dungeons sao NORMALIZADAS (como o app monta)
    "semanais": {"void4": True, "altardarunha": False,
                 "caminhoabissal": True, "fornalhainfernal": True,
                 "void123": True, "torredasilusoes": True,
                 "terradojulgamento": True},
}


def main():
    ctk.set_appearance_mode("dark")
    janela = ctk.CTk()
    janela.geometry("400x1000")
    janela.configure(fg_color="#141221")

    # o card e desenhado num CANVAS (nao e um widget)
    canvas = tk.Canvas(janela, width=400, height=1000, bg="#141221",
                       highlightthickness=0)
    canvas.place(x=0, y=0)

    card = CardPersonagem(canvas, 20, 20, DADOS_UNO,
                          pasta_retratos=os.path.join("assets", "personagens"))
    janela.attributes("-topmost", True)
    janela.lift()
    janela.update()
    time.sleep(1.0)
    janela.update()
    x, y = janela.winfo_rootx(), janela.winfo_rooty()
    w, h = janela.winfo_width(), janela.winfo_height()
    caminho = os.path.abspath(SAIDA)
    ImageGrab.grab(bbox=(x, y, x + w, y + h)).save(caminho)
    print(f"[card] {caminho} ({w}x{h}) | card {card.altura}px")
    janela.destroy()


if __name__ == "__main__":
    main()

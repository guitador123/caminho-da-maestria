"""Previa do cenario (sem Tk): gera a imagem base da tela nova."""
import _raiz  # noqa: F401  (coloca src/ no sys.path)
import sys

from PIL import Image

import tema_visual as tv

saida = sys.argv[1] if len(sys.argv) > 1 else "previa_cenario.png"
largura = int(sys.argv[2]) if len(sys.argv) > 2 else tv.DESIGN_W
altura = int(sys.argv[3]) if len(sys.argv) > 3 else tv.DESIGN_H

lay = tv.Layout(largura, altura)
img = tv.render_cenario(r"assets\background.jpg", largura, altura, lay)
img.save(saida)
print(f"{saida} {img.size} escala={lay.s:.3f}")

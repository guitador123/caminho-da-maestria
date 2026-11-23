import _raiz  # noqa: F401  (coloca src/ no sys.path)
import os
from PIL import Image

caminho = r"C:\Users\guilh\Downloads\Controle GrandChase\assets\background.jpg"

print("1) Arquivo existe?", os.path.exists(caminho))
if os.path.exists(caminho):
    print("   Tamanho:", os.path.getsize(caminho), "bytes")
    try:
        img = Image.open(caminho)
        print("   PIL abriu OK:", img.format, img.size, img.mode)
    except Exception as e:
        print("   ERRO ao abrir com PIL:", e)
else:
    print("   -> Salve a imagem exatamente neste caminho:")
    print("      C:\\Users\\guilh\\Downloads\\Controle GrandChase\\assets\\background.jpg")
    
# -*- coding: utf-8 -*-
"""
Copiar uma IMAGEM para a area de transferencia do Windows (CF_DIB).

Depois e so dar Ctrl+V no Discord (ou no Paint, WhatsApp Web...) que a
imagem aparece. Sem bibliotecas extras: usa a API do Windows (ctypes).
"""

import ctypes
import io
import os

from registro import falha

CF_DIB = 8
GMEM_MOVEABLE = 0x0002


def copiar_imagem(imagem):
    """Copia uma PIL.Image. Devolve True se deu certo."""
    if os.name != "nt":
        return False
    buffer = io.BytesIO()
    imagem.convert("RGB").save(buffer, "BMP")
    dados = buffer.getvalue()[14:]          # DIB = o BMP sem o cabecalho

    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    # tipos explicitos: no Windows 64 bits os ponteiros nao cabem em int
    kernel32.GlobalAlloc.restype = ctypes.c_void_p
    kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
    kernel32.GlobalFree.argtypes = [ctypes.c_void_p]
    user32.SetClipboardData.restype = ctypes.c_void_p
    user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
    user32.OpenClipboard.argtypes = [ctypes.c_void_p]

    if not user32.OpenClipboard(None):
        return False
    try:
        user32.EmptyClipboard()
        memoria = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(dados))
        if not memoria:
            return False
        destino = kernel32.GlobalLock(memoria)
        ctypes.memmove(destino, dados, len(dados))
        kernel32.GlobalUnlock(memoria)
        if not user32.SetClipboardData(CF_DIB, memoria):
            kernel32.GlobalFree(memoria)
            return False
        return True                 # agora a memoria e do Windows
    except Exception:
        falha("copiar a imagem para a area de transferencia")
        return False
    finally:
        user32.CloseClipboard()

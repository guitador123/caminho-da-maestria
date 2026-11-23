# -*- mode: python ; coding: utf-8 -*-

import os

block_cipher = None

a = Analysis(
    ['app_grandchase.py'],
    pathex=[],
    binaries=[],
    datas=[(os.path.join(SPECPATH, 'assets', 'background.jpg'), 'assets'),
           (os.path.join(SPECPATH, 'assets', 'login.png'), 'assets'),
           (os.path.join(SPECPATH, 'assets', 'app.ico'), 'assets'),
           # o QR Code do Pix (imagem pronta do usuario)
           (os.path.join(SPECPATH, 'assets', 'qrcode-pix.png'), 'assets'),
           # a versao (commit) em que este .exe foi feito
           (os.path.join(SPECPATH, 'assets', 'versao.txt'), 'assets'),
           (os.path.join(SPECPATH, 'assets', 'personagens'), 'assets/personagens'),
           (os.path.join(SPECPATH, 'assets', 'chaser'), 'assets/chaser'),
           # so os PNGs (a pasta tem um .venv de 400 MB e varios logs)
           (os.path.join(SPECPATH, 'assets', 'perfil', '*.png'), 'assets/perfil'),
           # a doacao: so os arquivos que o app usa em tempo de execucao
           # (o script gerador e o __pycache__ ficam de fora)
           (os.path.join(SPECPATH, 'assets', 'doacao', 'pix.txt'), 'assets/doacao'),
           (os.path.join(SPECPATH, 'assets', 'doacao', 'nome.txt'), 'assets/doacao'),
           (os.path.join(SPECPATH, 'assets', 'doacao', 'pix_payload.txt'), 'assets/doacao'),
           (os.path.join(SPECPATH, 'assets', 'doacao', 'qr_pix.png'), 'assets/doacao')],
    # a assinatura das releases (atualizacao.py importa dentro da funcao)
    hiddenimports=['assinatura',
                   'cryptography.hazmat.primitives.asymmetric.ed25519'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'PyQt6', 'PySide6', 'PyQt5', 'PySide2',
        'scipy', 'sympy', 'gmpy2', 'matplotlib', 'sklearn',
        'skimage', 'patsy', 'statsmodels', 'xarray', 'altair',
        'plotly', 'bokeh', 'dask', 'distributed', 'numba',
        'llvmlite', 'h5py', 'tables', 'pyarrow', 'fsspec',
        'botocore', 's3fs', 'gcsfs', 'adlfs', 'sqlalchemy',
        'psycopg2', 'MySQLdb', 'pymysql', 'cx_Oracle',
        'ipython', 'jupyter', 'jupyterlab', 'notebook',
        'nbconvert', 'nbformat', 'ipywidgets', 'traitlets',
        'sphinx', 'jinja2', 'pygments', 'docutils',
        'pytest', 'astroid', 'pylint', 'black', 'yapf',
        'isort', 'flake8', 'mypy', 'nbclient', 'nbclassic',
        'qtpy', 'panel', 'pyviz_comms', 'hvplot', 'datashader',
        'geoviews', 'holoviews', 'datashape', 'odo',
        'blaze', 'odo', 'smart_open', 'sshtunnel',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Caminho da Maestria',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(SPECPATH, 'assets', 'app.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Caminho da Maestria',
)

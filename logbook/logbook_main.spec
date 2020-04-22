# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import importlib
from pathlib import Path

added_file = [
    ('views', 'views'),
    ('scripts','scripts'),
    ('themes', 'themes'), 
    ('images', 'images'),
    ('qtmodern_package','qtmodern_package'),
    ('settings.json','.'),
    ('logbook_user_guide.pdf','.')
    ]

a = Analysis(['logbook_main.py'],
             pathex=['\\logbook_main.spec'],
             binaries=[],
             datas=added_file,
             hiddenimports=['openpyxl', 'PyQt5.uic','pyodbc'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)

pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)

exe = EXE(pyz,
          a.scripts,
          exclude_binaries=True,
          name='Logbookv2',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False , 
          icon='images\\icons\\appicon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='Logbook v2')
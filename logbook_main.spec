# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

import importlib
from pathlib import Path

'''package_imports = [['qtmodern', ['resources/frameless.qss', 'resources/style.qss']]]'''

added_file = [('logbook_design.ui','.'),('logbook_dialog.ui','.'), ('themes', 'themes'), ('images', 'images'),('qtmodern_package','qtmodern_package'),('settings.json','.')]

'''for package, files in package_imports:
    proot = Path(importlib.import_module(package).__file__).parent
    added_file.extend((proot / f, package) for f in files)'''

a = Analysis(['logbook_main.py'],
             pathex=['\\logbook_main.spec'],
             binaries=[],
             datas=added_file,
             hiddenimports=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='logbook_main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True , icon='images\\appicon.ico')

coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               upx_exclude=[],
               name='logbook_main')
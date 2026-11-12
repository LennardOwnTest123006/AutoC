# PyInstaller:  pyinstaller autoc.spec   ->  dist/AutoC.exe
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(["autoc/__main__.py"], pathex=["."],
             datas=[("autoc/data", "autoc/data")],
             hiddenimports=collect_submodules("pystray") + ["PIL._tkinter_finder"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, name="AutoC", console=False, upx=False)

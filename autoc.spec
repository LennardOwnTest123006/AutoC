# PyInstaller:  pyinstaller autoc.spec   ->  dist/AutoC/{AutoC.exe, autoc-cli.exe, ...}
from PyInstaller.utils.hooks import collect_submodules

a = Analysis(["run_autoc.py"], pathex=["."],
             datas=[("autoc/data", "autoc/data")],
             hiddenimports=collect_submodules("pystray") + ["tkinter", "PIL._tkinter_finder"])
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, exclude_binaries=True, name="AutoC", console=False)
cli = EXE(pyz, a.scripts, exclude_binaries=True, name="autoc-cli", console=True)
coll = COLLECT(gui, cli, a.binaries, a.datas, name="AutoC")

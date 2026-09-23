# piperread-gui.spec — gèle l'interface graphique en exécutable Windows autonome.
#
# Pourquoi ce fichier existe :
#     Livrer piperread-gui comme actif de la Release GitHub pour Windows.
#     PyInstaller gèle un point d'entrée par
#     exécutable ; le serveur HTTP de Piper (processus séparé, jamais lié
#     dans ce même exécutable — frontière GPL actée dans server.py) a le sien,
#     piper-http-server.spec, livré dans le sous-dossier piper-http-server\.
#
#     Mode dossier (COLLECT), pas fichier unique : un exécutable unique
#     s'extrait dans %TEMP% à chaque lancement, ce qui retardait le démarrage
#     de plusieurs secondes (décision « exécutable Windows : mode dossier,
#     comptes à nom accentué »).
#
# Construit par :
#     .github/workflows/build-windows-gui.yml, sur windows-latest — aucune
#     construction croisée depuis Linux (PyInstaller ne fait pas de
#     cross-compilation ; produire un binaire Windows réel exige un
#     interpréteur et des wheels Windows réels).
#
# Lancer (depuis gui/, sur Windows, environnement déjà préparé par le
# workflow — voir sa section « Installer les dépendances ») :
#     pyinstaller packaging/windows/piperread-gui.spec

import sys
from pathlib import Path

RACINE_GUI = Path(SPECPATH).resolve().parent.parent

a = Analysis(
    [str(RACINE_GUI / "piperread_gui" / "app.py")],
    pathex=[str(RACINE_GUI)],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="piperread-gui",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(RACINE_GUI / "packaging" / "windows" / "piperread.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="piperread-gui",
)

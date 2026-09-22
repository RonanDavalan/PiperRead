# piper-http-server.spec — gèle le serveur HTTP de Piper en exécutable Windows autonome.
#
# Pourquoi ce fichier existe :
#     Compagnon de piperread-gui.exe (piperread-gui.spec), livré à côté de
#     lui dans le même dossier d'installation. server.py l'invoque en
#     sous-processus, jamais en import direct : c'est la frontière GPL déjà
#     actée pour le lien au noyau (CONCEPTION_PIPERREAD.md, fiche « interface
#     graphique »), transposée à Windows où il n'existe ni venv ni paquet
#     noyau séparé pour héberger l'interpréteur.
#
#     Le paquet `piper` embarque des données non-Python nécessaires à
#     l'exécution (`espeak-ng-data/`, `templates/`, `img/`, `hebrew/`,
#     `tashkeel/`) que PyInstaller ne suit pas par la seule analyse des
#     imports : `collect_all("piper")` les inclut explicitement. Même
#     nécessité pour `onnxruntime` (bibliothèques natives).
#
# Construit par :
#     .github/workflows/build-windows-gui.yml, sur windows-latest — voir
#     piperread-gui.spec pour la raison de l'absence de construction croisée.
#
# Lancer (depuis gui/, sur Windows) :
#     pyinstaller packaging/windows/piper-http-server.spec

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

RACINE_GUI = Path(SPECPATH).resolve().parent.parent

datas = []
binaries = []
hiddenimports = []

for paquet in ("piper", "onnxruntime", "flask"):
    d, b, h = collect_all(paquet)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [str(RACINE_GUI / "piperread_gui" / "piper_server_entry.py")],
    pathex=[str(RACINE_GUI)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.datas,
    [],
    name="piper-http-server",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

# piper-http-server.spec — gèle le serveur HTTP de Piper en exécutable Windows autonome.
#
# Pourquoi ce fichier existe :
#     Compagnon de piperread-gui.exe (piperread-gui.spec), livré dans le
#     sous-dossier piper-http-server\ de son dossier, en mode dossier comme
#     lui (chaque exécutable a son propre _internal\). server.py l'invoque en
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

# Page de code UTF-8 pour tout le processus (Windows 10 1903 et suivants) :
# espeak-ng ouvre ses données et énumère ses voix par les API « ANSI » de
# Windows, qui échouent sur un dossier de profil accentué. La locale de la
# bibliothèque C ne suffit pas : l'énumération des voix passe par Win32.
MANIFESTE = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <application xmlns="urn:schemas-microsoft-com:asm.v3">
    <windowsSettings>
      <longPathAware xmlns="http://schemas.microsoft.com/SMI/2016/WindowsSettings">true</longPathAware>
      <activeCodePage xmlns="http://schemas.microsoft.com/SMI/2019/WindowsSettings">UTF-8</activeCodePage>
    </windowsSettings>
  </application>
</assembly>
"""

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
    [],
    exclude_binaries=True,
    name="piper-http-server",
    manifest=MANIFESTE,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="piper-http-server",
)

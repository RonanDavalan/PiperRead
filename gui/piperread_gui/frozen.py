"""
frozen.py — répertoire d'installation réel quand l'interface tourne en exécutable gelé.

Pourquoi ce fichier existe :
    Sous PyInstaller, `Path(__file__)` d'un module résolu depuis l'archive
    embarquée pointe vers le dossier d'extraction temporaire de l'exécutable
    (onefile), jamais vers son dossier d'installation réel : `voices/`,
    `lang/`, l'icône et `piper-http-server.exe`, tous livrés à côté de
    `piperread-gui.exe`, y seraient introuvables. `app.py` et `i18n.py`
    utilisent `installation_dir()` à la place de `Path(__file__)` pour
    calculer leur racine de résolution quand `sys.frozen` est vrai ; `None`
    sinon, pour laisser inchangée la résolution clone/paquet Linux déjà
    établie (`server.py` fait de même pour `piper-http-server.exe`, par sa
    propre résolution, indépendante de celle-ci).

Entrée / sortie :
    Aucune entrée. Sortie : `installation_dir()` rend le dossier réel de
    l'exécutable gelé, ou `None` si l'interface n'est pas gelée.
"""

import sys
from pathlib import Path


def installation_dir() -> Path | None:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return None

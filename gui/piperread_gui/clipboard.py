"""
clipboard.py — capture le contenu du presse-papiers classique.

Pourquoi ce fichier existe :
    Le noyau (read.sh) résout déjà l'ordre Wayland puis X11 pour le
    presse-papiers ; l'interface répète ce même ordre sans le réécrire à sa
    façon, pour ne jamais se comporter différemment du noyau sur la même
    machine. Windows n'a ni `wl-paste` ni `xsel` : l'interface y lit le
    presse-papiers par l'API Qt déjà chargée pour le tray (`QApplication`),
    sans nouvel outil externe ni nouvelle dépendance.

Entrée / sortie :
    Aucune entrée. Sortie : le contenu texte du presse-papiers, chaîne vide
    si aucun outil n'est disponible ou si le presse-papiers ne contient que
    des espaces.

Dépend de :
    Le binaire `wl-paste` (Wayland) puis, à défaut, `xsel` (X11) — les mêmes
    outils externes que `read.sh`. Sur Windows, `PySide6.QtWidgets.QApplication`
    à la place, appelée depuis le fil principal Qt (seul fil autorisé à
    toucher le presse-papiers Qt).
"""

import shutil
import subprocess
import sys

_CLIPBOARD_COMMANDS = (
    ("wl-paste", ["wl-paste", "--no-newline"]),
    ("xsel", ["xsel", "--clipboard", "--output"]),
)


def _read_clipboard_windows() -> str:
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance()
    if application is None:
        return ""
    return application.clipboard().text()


def read_clipboard() -> str:
    if sys.platform == "win32":
        return _read_clipboard_windows()
    for binary, command in _CLIPBOARD_COMMANDS:
        if shutil.which(binary) is None:
            continue
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        if result.stdout.strip():
            return result.stdout
    return ""

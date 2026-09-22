"""
clipboard.py — capture le texte à lire : sélection souris, sinon presse-papiers.

Pourquoi ce fichier existe :
    Le noyau (read.sh, mode `auto`) lit d'abord la sélection souris
    (`primary`), puis le presse-papiers classique si elle est vide, en
    essayant chaque fois Wayland puis X11. L'interface répète exactement cet
    ordre, pour ne jamais se comporter différemment du noyau sur la même
    machine : le geste naturel est « sélectionner puis lire ». Windows n'a ni
    sélection primaire, ni `wl-paste`, ni `xsel` : l'interface y lit le seul
    presse-papiers par l'API Qt déjà chargée pour le tray (`QApplication`),
    sans outil externe ni dépendance supplémentaire.

Entrée / sortie :
    Aucune entrée. Sortie : le texte de la sélection, ou à défaut celui du
    presse-papiers ; chaîne vide si aucun outil n'est disponible ou si les
    deux ne contiennent que des espaces.

Dépend de :
    Le binaire `wl-paste` (Wayland) puis, à défaut, `xsel` (X11) — les mêmes
    outils externes que `read.sh`. Sur Windows, `PySide6.QtWidgets.QApplication`
    à la place, appelée depuis le fil principal Qt (seul fil autorisé à
    toucher le presse-papiers Qt).
"""

import shutil
import subprocess
import sys

_SELECTION_COMMANDS = (
    ("wl-paste", ["wl-paste", "--primary", "--no-newline"]),
    ("xsel", ["xsel", "--primary", "--output"]),
)

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


def _first_non_blank(commands) -> str:
    for binary, command in commands:
        if shutil.which(binary) is None:
            continue
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        if result.stdout.strip():
            return result.stdout
    return ""


def read_clipboard() -> str:
    if sys.platform == "win32":
        return _read_clipboard_windows()
    return _first_non_blank(_SELECTION_COMMANDS) or _first_non_blank(_CLIPBOARD_COMMANDS)

"""
clipboard.py — capture le contenu du presse-papiers classique.

Pourquoi ce fichier existe :
    Le noyau (read.sh) résout déjà l'ordre Wayland puis X11 pour le
    presse-papiers ; l'interface répète ce même ordre sans le réécrire à sa
    façon, pour ne jamais se comporter différemment du noyau sur la même
    machine.

Entrée / sortie :
    Aucune entrée. Sortie : le contenu texte du presse-papiers, chaîne vide
    si aucun outil n'est disponible ou si le presse-papiers ne contient que
    des espaces.

Dépend de :
    Le binaire `wl-paste` (Wayland) puis, à défaut, `xsel` (X11) — les mêmes
    outils externes que `read.sh`.
"""

import shutil
import subprocess

_CLIPBOARD_COMMANDS = (
    ("wl-paste", ["wl-paste", "--no-newline"]),
    ("xsel", ["xsel", "--clipboard", "--output"]),
)


def read_clipboard() -> str:
    for binary, command in _CLIPBOARD_COMMANDS:
        if shutil.which(binary) is None:
            continue
        result = subprocess.run(
            command, capture_output=True, text=True, check=False
        )
        if result.stdout.strip():
            return result.stdout
    return ""

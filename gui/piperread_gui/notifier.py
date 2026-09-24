"""
notifier.py — notification système par `notify-send`, indépendante du tray.

Pourquoi ce fichier existe :
    Un bureau peut exposer les notifications de bureau (protocole D-Bus
    `org.freedesktop.Notifications`) sans exposer de zone de notification
    (« tray ») — c'est le cas de GNOME sans extension. `notify-send` parle
    directement à ce protocole, sans dépendre de `QSystemTrayIcon`, donc
    reste utilisable pour prévenir l'utilisateur même quand le tray est
    absent.

Entrée / sortie :
    Entrée : un titre et un message. Sortie : aucune ; l'échec est ignoré en
    silence (absence de `notify-send`, session sans bus de notification) —
    ce n'est jamais l'échec de cette notification qui doit interrompre la
    lecture.

Dépend de :
    Le binaire `notify-send`, s'il est présent.
"""

import shutil
import subprocess

_DELAI_SECONDES = 2.0


def notifier(titre: str, message: str) -> None:
    if shutil.which("notify-send") is None:
        return
    try:
        subprocess.run(
            ["notify-send", titre, message],
            capture_output=True,
            check=False,
            stdin=subprocess.DEVNULL,
            timeout=_DELAI_SECONDES,
        )
    except subprocess.TimeoutExpired:
        pass

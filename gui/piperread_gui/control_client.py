"""
control_client.py — envoie une commande à une instance de piperread-gui déjà lancée.

Pourquoi ce fichier existe :
    Sépare l'envoi d'une commande (`--pause`, `--stop`…) du serveur qui
    l'écoute (`control_server.py`), pour que `app.py` puisse tester l'un sans
    l'autre. Sous Windows, le jeton lu dans le fichier de connexion précède la
    commande sur la ligne envoyée — même fichier que celui écrit par
    `ControlServer._demarrer_windows`.

Entrée / sortie :
    Entrée : le nom d'une commande (`lire`, `pause`, `reprendre`, `arreter`,
    `phrase_precedente`, `phrase_suivante`, `quitter`). Sortie : la réponse
    texte du serveur.

Dépend de :
    `control_server.chemin_socket` (POSIX) ou `control_server.chemin_connexion_windows`
    (Windows) pour retrouver l'instance en cours ; lève `ErreurAucuneInstance`
    si aucune n'écoute ou si le jeton présenté est refusé.
"""

import socket
import sys

from piperread_gui.control_server import chemin_connexion_windows, chemin_socket

_DELAI_SECONDES = 2.0


class ErreurAucuneInstance(RuntimeError):
    pass


def envoyer_commande(commande: str) -> str:
    if sys.platform == "win32":
        return _envoyer_commande_windows(commande)
    return _envoyer_commande_posix(commande)


def _envoyer_commande_posix(commande: str) -> str:
    chemin = chemin_socket()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as connexion:
            connexion.settimeout(_DELAI_SECONDES)
            connexion.connect(str(chemin))
            connexion.sendall((commande + "\n").encode())
            return connexion.makefile("r").readline().strip()
    except OSError as erreur:
        raise ErreurAucuneInstance(
            "Aucune instance de piperread-gui en cours d'exécution."
        ) from erreur


def _envoyer_commande_windows(commande: str) -> str:
    chemin = chemin_connexion_windows()
    try:
        port, jeton = chemin.read_text(encoding="utf-8").splitlines()[:2]
    except (OSError, ValueError) as erreur:
        raise ErreurAucuneInstance(
            "Aucune instance de piperread-gui en cours d'exécution."
        ) from erreur

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as connexion:
            connexion.settimeout(_DELAI_SECONDES)
            connexion.connect(("127.0.0.1", int(port)))
            connexion.sendall(f"{jeton} {commande}\n".encode())
            reponse = connexion.makefile("r").readline().strip()
    except (OSError, ValueError) as erreur:
        raise ErreurAucuneInstance(
            "Aucune instance de piperread-gui en cours d'exécution."
        ) from erreur

    if reponse != "ok":
        raise ErreurAucuneInstance(
            "Aucune instance de piperread-gui en cours d'exécution."
        )
    return reponse

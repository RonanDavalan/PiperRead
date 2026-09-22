"""
control_client.py — envoie une commande à une instance de piperread-gui déjà lancée.

Pourquoi ce fichier existe :
    Sépare l'envoi d'une commande (`--pause`, `--stop`…) du serveur qui
    l'écoute (`control_server.py`), pour que `app.py` puisse tester l'un sans
    l'autre.

Entrée / sortie :
    Entrée : le nom d'une commande (`lire`, `pause`, `reprendre`, `arreter`,
    `phrase_precedente`, `phrase_suivante`, `quitter`). Sortie : la réponse
    texte du serveur.

Dépend de :
    `control_server.chemin_socket` pour retrouver la socket de l'instance en
    cours ; lève `ErreurAucuneInstance` si aucune n'écoute.
"""

import socket

from piperread_gui.control_server import chemin_socket

_DELAI_SECONDES = 2.0


class ErreurAucuneInstance(RuntimeError):
    pass


def envoyer_commande(commande: str) -> str:
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

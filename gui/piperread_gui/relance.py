"""
relance.py — relance de l'interface par une autre instance de la même commande.

Pourquoi ce fichier existe :
    L'entrée « Relancer » du menu doit remplacer le processus courant par un
    neuf qui relit `piperread.conf` et recharge la voix. Isolé de `app.py`
    pour que la construction de la commande se teste sans lancer de
    processus. `os.execv` n'est pas utilisé : sous Windows il crée un second
    processus au lieu de substituer le courant, et l'appelant s'arrête aussitôt,
    serveur de synthèse et socket de pilotage encore ouverts.

Entrée / sortie :
    Entrée : les options de ligne de commande de l'instance courante
    (`sys.argv[1:]`). Sortie : aucune ; un processus détaché est lancé, que
    l'appelant laisse démarrer avant de quitter. `--play` est retiré : une
    relance ne relit pas le presse-papiers.

Dépend de :
    `frozen.py` pour distinguer l'exécutable gelé du lancement par module.
"""

import subprocess
import sys

from piperread_gui import frozen


def commande_de_relance(options: list[str]) -> list[str]:
    conservees = [option for option in options if option != "--play"]
    if frozen.installation_dir() is not None:
        return [sys.executable, *conservees]
    return [sys.executable, "-m", "piperread_gui.app", *conservees]


def relancer_instance(options: list[str]) -> None:
    commande = commande_de_relance(options)
    if sys.platform == "win32":
        drapeaux = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
        subprocess.Popen(commande, stdin=subprocess.DEVNULL, creationflags=drapeaux)
    else:
        subprocess.Popen(commande, stdin=subprocess.DEVNULL, start_new_session=True)

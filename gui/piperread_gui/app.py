"""
app.py — point d'entrée de l'interface graphique : fenêtre-tray, sans fenêtre visible.

Pourquoi ce fichier existe :
    Assemble ce que les autres fichiers du paquet ne font qu'un par un :
    une `QApplication` (obligatoire avant toute instanciation de
    `QSystemTrayIcon`, sous peine de crash immédiat sur PySide6), le
    `PlaybackController` de la session, le tray qui l'expose et la socket de
    pilotage (`control_server.py`) qui reste la seule surface sur un bureau
    sans zone de notification. L'icône provient de `Ressources/piperread.svg`,
    déjà dessinée pour le paquet
    (`_CADRE/SPECIFICATIONS/PROCEDURES_LLM/instance/TACHE_dessiner-icone-svg.md`) —
    aucune nouvelle icône n'est dessinée pour ce chantier.

Entrée / sortie :
    Entrée : options de ligne de commande, mêmes que `cli.py` (`--model`,
    `--lang`), plus sept options de pilotage d'une instance déjà lancée
    (`--play`, `--pause`, `--resume`, `--stop`, `--next`, `--previous`,
    `--quit`). Sortie : aucune (boucle d'événements Qt, sans fenêtre visible
    tant qu'aucun dialogue de réglages n'existe — session suivante).
"""

import argparse
import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from piperread_gui.control_client import ErreurAucuneInstance, envoyer_commande
from piperread_gui.control_server import ControlServer, ErreurControleIndisponible
from piperread_gui.controller import PlaybackController
from piperread_gui.tray import PiperReadTray, avertir_si_tray_absent

_GUI_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _GUI_DIR.parent
_ICONE = _REPO_ROOT / "Ressources" / "piperread.svg"


def _modele_par_defaut() -> Path | None:
    dossier_voix = _REPO_ROOT / "voices"
    modeles = sorted(dossier_voix.glob("*.onnx"))
    return modeles[0] if modeles else None


def _analyser_arguments(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        prog="piperread-gui",
        description="Interface graphique de PiperRead : icône de tray et menu de lecture.",
    )
    analyseur.add_argument(
        "--model",
        type=Path,
        default=_modele_par_defaut(),
        help="Chemin du modèle de voix .onnx (défaut : la première voix de voices/).",
    )
    analyseur.add_argument(
        "--lang",
        default="fr",
        choices=("en", "fr", "de", "es"),
        help="Langue du découpage en phrases (défaut : fr).",
    )

    groupe_pilotage = analyseur.add_mutually_exclusive_group()
    groupe_pilotage.add_argument(
        "--play", dest="commande", action="store_const", const="lire",
        help="Démarre ou reprend la lecture du presse-papiers sur l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--pause", dest="commande", action="store_const", const="pause",
        help="Met en pause l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--resume", dest="commande", action="store_const", const="reprendre",
        help="Reprend la lecture de l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--stop", dest="commande", action="store_const", const="arreter",
        help="Arrête la lecture de l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--next", dest="commande", action="store_const", const="phrase_suivante",
        help="Passe à la phrase suivante sur l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--previous", dest="commande", action="store_const", const="phrase_precedente",
        help="Revient à la phrase précédente sur l'instance déjà lancée.",
    )
    groupe_pilotage.add_argument(
        "--quit", dest="commande", action="store_const", const="quitter",
        help="Ferme l'instance déjà lancée (tray et socket compris).",
    )

    return analyseur.parse_args(argv)


def _piloter_instance_existante(commande: str) -> int:
    if os.name != "posix":
        print(
            "Le pilotage d'une instance déjà lancée n'est pris en charge que sur Linux/Unix.",
            file=sys.stderr,
        )
        return 1
    try:
        reponse = envoyer_commande(commande)
    except ErreurAucuneInstance as erreur:
        print(str(erreur), file=sys.stderr)
        return 1
    print(reponse)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = _analyser_arguments(sys.argv[1:] if argv is None else argv)

    if arguments.commande is not None:
        return _piloter_instance_existante(arguments.commande)

    if arguments.model is None:
        print(
            "Aucun modèle de voix trouvé ; préciser --model <chemin vers un .onnx>.",
            file=sys.stderr,
        )
        return 1

    application = QApplication(sys.argv[:1])
    application.setQuitOnLastWindowClosed(False)

    avertir_si_tray_absent()

    controller = PlaybackController(arguments.model, arguments.lang)
    tray = PiperReadTray(controller, _ICONE)
    tray.show()

    control_server = None
    if os.name == "posix":
        control_server = ControlServer()
        try:
            control_server.demarrer()
        except ErreurControleIndisponible as erreur:
            print(str(erreur), file=sys.stderr)
            return 1

        repartiteur = {
            "lire": controller.lire,
            "pause": controller.pause,
            "reprendre": controller.reprendre,
            "arreter": controller.arreter,
            "phrase_precedente": controller.phrase_precedente,
            "phrase_suivante": controller.phrase_suivante,
            "quitter": lambda: (controller.arreter(), application.quit()),
        }
        control_server.commande.connect(lambda ligne: repartiteur.get(ligne, lambda: None)())

    code_sortie = application.exec()

    if control_server is not None:
        control_server.arreter()

    return code_sortie


if __name__ == "__main__":
    raise SystemExit(main())

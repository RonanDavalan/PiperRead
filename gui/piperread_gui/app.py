"""
app.py — point d'entrée de l'interface graphique : fenêtre-tray, sans fenêtre visible.

Pourquoi ce fichier existe :
    Assemble ce que les autres fichiers du paquet ne font qu'un par un :
    une `QApplication` (obligatoire avant toute instanciation de
    `QSystemTrayIcon`, sous peine de crash immédiat sur PySide6), le
    `PlaybackController` de la session, et le tray qui l'expose. L'icône
    provient de `Ressources/piperread.svg`, déjà dessinée pour le paquet
    (`_CADRE/SPECIFICATIONS/PROCEDURES_LLM/instance/TACHE_dessiner-icone-svg.md`) —
    aucune nouvelle icône n'est dessinée pour ce chantier.

Entrée / sortie :
    Entrée : options de ligne de commande, mêmes que `cli.py` (`--model`,
    `--lang`). Sortie : aucune (boucle d'événements Qt, sans fenêtre visible
    tant qu'aucun dialogue de réglages n'existe — session suivante).
"""

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

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
    return analyseur.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = _analyser_arguments(sys.argv[1:] if argv is None else argv)

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

    return application.exec()


if __name__ == "__main__":
    raise SystemExit(main())

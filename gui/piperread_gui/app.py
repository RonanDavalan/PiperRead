"""
app.py — point d'entrée de l'interface graphique : fenêtre-tray, sans fenêtre visible.

Pourquoi ce fichier existe :
    Assemble ce que les autres fichiers du paquet ne font qu'un par un :
    une `QApplication` (obligatoire avant toute instanciation de
    `QSystemTrayIcon`, sous peine de crash immédiat sur PySide6), le
    `PlaybackController` de la session, le tray qui l'expose et la socket de
    pilotage (`control_server.py`) qui reste la seule surface sur un bureau
    sans zone de notification. L'icône provient de `Ressources/piperread.svg`
    du clone en priorité, sinon de l'icône du thème installée par le paquet
    noyau (`/usr/share/icons/hicolor/scalable/apps/piperread.svg`, dont
    `piperread-gui` dépend) — déjà dessinée pour le paquet
    (`_CADRE/SPECIFICATIONS/PROCEDURES_LLM/instance/TACHE_dessiner-icone-svg.md`) —
    aucune nouvelle icône n'est dessinée pour ce chantier. Le dossier des voix
    suit la même priorité (`config.default_voices_dir`, clone puis
    `$XDG_DATA_HOME/piperread/voices`, même règle que `BASE_DIR`/`DATA_DIR`
    de `read.sh`). Sur l'exécutable Windows gelé, la racine de résolution est
    le dossier réel de `piperread-gui.exe` (`frozen.installation_dir`), pas
    le dossier d'extraction temporaire que donnerait `Path(__file__)` — même
    principe que `server._trouver_executable_windows`. La résolution de la
    vitesse, de la voix et de la langue
    (`config.resolve_settings`, session 3) suit le même ordre de priorité que
    `read.sh` : option de ligne de commande > variable d'environnement >
    `piperread.conf` > défaut.

Entrée / sortie :
    Entrée : options de ligne de commande, mêmes que `cli.py` (`--model`,
    `--lang`), plus `--speed` (session 3, vitesse de 0.5 à 3.0 — pas de
    `--voice` distinct : `--model` sert déjà ce rôle en désignant directement
    le fichier, choix de session 1 conservé par immuabilité des identifiants),
    plus sept options de pilotage d'une instance déjà lancée (`--play`,
    `--pause`, `--resume`, `--stop`, `--next`, `--previous`, `--quit`).
    Sortie : aucune (boucle d'événements Qt, sans fenêtre visible tant
    qu'aucun réglage n'est ouvert depuis le menu du tray).
"""

import argparse
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from piperread_gui import config, frozen, i18n
from piperread_gui.control_client import ErreurAucuneInstance, envoyer_commande
from piperread_gui.control_server import ControlServer, ErreurControleIndisponible
from piperread_gui.controller import PlaybackController
from piperread_gui.tray import PiperReadTray, avertir_si_tray_absent

_GUI_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = frozen.installation_dir() or _GUI_DIR.parent
_ICONE_INSTALLEE = Path("/usr/share/icons/hicolor/scalable/apps/piperread.svg")
_ICONE_GELEE = "piperread.ico"


def _resoudre_icone(repo_root: Path) -> Path:
    if frozen.installation_dir() is not None:
        return repo_root / _ICONE_GELEE
    candidat = repo_root / "Ressources" / "piperread.svg"
    return candidat if candidat.is_file() else _ICONE_INSTALLEE


_ICONE = _resoudre_icone(_REPO_ROOT)
_VOICES_DIR = config.default_voices_dir(_REPO_ROOT)


def _analyser_arguments(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        prog="piperread-gui",
        description="Interface graphique de PiperRead : icône de tray et menu de lecture.",
    )
    analyseur.add_argument(
        "--model",
        type=Path,
        default=None,
        help="Chemin du modèle de voix .onnx (défaut : résolu depuis piperread.conf, sinon la première voix de voices/).",
    )
    analyseur.add_argument(
        "--lang",
        default=None,
        choices=("en", "fr", "de", "es"),
        help="Langue des messages et du découpage en phrases (défaut : résolue depuis piperread.conf).",
    )
    analyseur.add_argument(
        "--speed",
        default=None,
        help="Vitesse de 0.5 à 3.0, point ou virgule (défaut : résolue depuis piperread.conf, sinon 1.0).",
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
    try:
        reponse = envoyer_commande(commande)
    except ErreurAucuneInstance as erreur:
        print(str(erreur), file=sys.stderr)
        return 1
    print(reponse)
    return 0


def _emettre_avertissements(
    messages: dict[str, str],
    warnings: list[tuple[str, str, str]],
    model_path: Path | None,
) -> None:
    for cle, valeur, source in warnings:
        if cle == "voice" and model_path is not None:
            print(i18n.msg(messages, "voice_fallback", valeur, source, model_path.stem), file=sys.stderr)
        else:
            print(i18n.msg(messages, "setting_invalid", cle, valeur, source), file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    arguments = _analyser_arguments(sys.argv[1:] if argv is None else argv)

    if arguments.commande is not None:
        return _piloter_instance_existante(arguments.commande)

    resolu = config.resolve_settings(
        _VOICES_DIR,
        speed_option=arguments.speed,
        voice_option=None,
        lang_option=arguments.lang,
    )
    messages = i18n.load_messages(resolu.lang)

    if resolu.invalid is not None:
        cle, valeur, source = resolu.invalid
        if cle == "voice" and config.valid_voice_name(valeur):
            print(i18n.msg(messages, "voice_not_found", valeur), file=sys.stderr)
        else:
            print(i18n.msg(messages, "option_invalid", source, valeur), file=sys.stderr)
        return 2

    _emettre_avertissements(messages, resolu.warnings, resolu.model_path)

    model_path = arguments.model if arguments.model is not None else resolu.model_path
    if model_path is None:
        print(
            "Aucun modèle de voix trouvé ; préciser --model <chemin vers un .onnx>.",
            file=sys.stderr,
        )
        return 1

    application = QApplication(sys.argv[:1])
    application.setQuitOnLastWindowClosed(False)

    controller = PlaybackController(model_path, resolu.lang, resolu.speed)
    avertir_si_tray_absent(controller.messages)
    tray = PiperReadTray(controller, _ICONE)
    tray.show()

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

    control_server.arreter()

    return code_sortie


if __name__ == "__main__":
    raise SystemExit(main())

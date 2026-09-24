"""
app.py — point d'entrée de l'interface graphique : fenêtre-tray, sans fenêtre visible.

Pourquoi ce fichier existe :
    Assemble ce que les autres fichiers du paquet ne font qu'un par un :
    une `QApplication` (obligatoire avant toute instanciation de
    `QSystemTrayIcon`, sous peine de crash immédiat sur PySide6), le
    `PlaybackController`, le tray qui l'expose et la socket de
    pilotage (`control_server.py`) qui reste la seule surface sur un bureau
    sans zone de notification. L'icône provient de `Ressources/piperread.svg`
    du clone en priorité, sinon de l'icône du thème installée par le paquet
    noyau (`/usr/share/icons/hicolor/scalable/apps/piperread.svg`, dont
    `piperread-gui` dépend) — déjà dessinée pour le paquet
    (`_CADRE/SPECIFICATIONS/PROCEDURES_LLM/instance/TACHE_dessiner-icone-svg.md`) —
    l'interface n'a pas d'icône propre. Le dossier des voix
    suit la même priorité (`config.default_voices_dir`, clone puis
    `$XDG_DATA_HOME/piperread/voices`, même règle que `BASE_DIR`/`DATA_DIR`
    de `read.sh`). Sur l'exécutable Windows gelé, la racine de résolution est
    le dossier réel de `piperread-gui.exe` (`frozen.installation_dir`), pas
    le dossier d'extraction temporaire que donnerait `Path(__file__)` — même
    principe que `server._trouver_executable_windows`. La résolution de la
    vitesse, de la voix, de la langue et de la télémétrie du moteur
    (`config.resolve_settings`) suit le même ordre de priorité que
    `read.sh` : option de ligne de commande > variable d'environnement >
    `piperread.conf` > défaut (télémétrie exclue, sans option dédiée : voir
    `controller.py`).

Entrée / sortie :
    Entrée : options de ligne de commande, mêmes que `cli.py` (`--model`,
    `--lang`), plus `--speed` (vitesse de 0.5 à 3.0 — pas de `--voice`
    distinct : `--model` sert déjà ce rôle en désignant directement le
    fichier, nom conservé par immuabilité des identifiants),
    plus sept options de pilotage d'une instance déjà lancée (`--play`,
    `--pause`, `--resume`, `--stop`, `--next`, `--previous`, `--quit`).
    `--play` sans instance lancée démarre l'interface puis lit, dès que la
    voix est chargée : c'est la commande du lanceur de menu, qui doit lire au
    premier clic, que l'interface tourne ou non. Au démarrage, la voix est
    chargée en fond et le lancement à l'ouverture de session est posé au
    premier lancement (`autostart.py`).
    Sortie : aucune (boucle d'événements Qt, sans fenêtre visible tant
    qu'aucun réglage n'est ouvert depuis le menu du tray). L'entrée « Relancer »
    du menu ferme proprement cette instance puis en lance une neuve
    (`relance.py`).
"""

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from piperread_gui import autostart, config, frozen, i18n
from piperread_gui.control_client import ErreurAucuneInstance, envoyer_commande
from piperread_gui.control_server import ControlServer, ErreurControleIndisponible
from piperread_gui.controller import PlaybackController
from piperread_gui.relance import relancer_instance
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


def _piloter_instance_existante(commande: str) -> int | None:
    try:
        reponse = envoyer_commande(commande)
    except ErreurAucuneInstance as erreur:
        if commande == "lire":
            return None
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
        code = _piloter_instance_existante(arguments.commande)
        if code is not None:
            return code

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

    control_server = ControlServer()
    try:
        control_server.demarrer()
    except ErreurControleIndisponible as erreur:
        print(str(erreur), file=sys.stderr)
        return 1

    autostart.appliquer_defaut_premier_lancement(_ICONE)

    controller = PlaybackController(model_path, resolu.lang, resolu.speed, resolu.telemetry)
    controller.demarrer_moteur()
    avertir_si_tray_absent(controller.messages)
    tray = PiperReadTray(controller, _ICONE)
    tray.show()

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

    relance = {"demandee": False}

    def demander_relance() -> None:
        relance["demandee"] = True
        controller.arreter()
        application.quit()

    tray.relance_demandee.connect(demander_relance)

    if arguments.commande == "lire":
        QTimer.singleShot(0, controller.lire)

    code_sortie = application.exec()

    control_server.arreter()
    controller.arreter_moteur()
    if relance["demandee"]:
        relancer_instance(sys.argv[1:])

    return code_sortie


if __name__ == "__main__":
    raise SystemExit(main())

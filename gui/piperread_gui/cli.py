"""
cli.py — boucle de test en ligne de commande : presse-papiers jusqu'au son.

Pourquoi ce fichier existe :
    Faire la preuve, avant toute fenêtre, que la chaîne complète tient :
    démarrage du serveur local, découpage en phrases, synthèse phrase par
    phrase, lecture audio, arrêt propre. Le tray et le menu (`app.py`) sont
    branchés sur cette même chaîne.

Entrée / sortie :
    Entrée : options de ligne de commande (voir `--help`). Sortie : le texte
    du presse-papiers est lu à voix haute, phrase par phrase, sur la sortie
    audio par défaut ; messages de progression sur la sortie standard.
"""

import argparse
import sys
from pathlib import Path

from piperread_gui import config
from piperread_gui.clipboard import read_clipboard
from piperread_gui.player import play_wav_bytes
from piperread_gui.sentences import split_sentences
from piperread_gui.server import ErreurServeurPiper, PiperHttpServer
from piperread_gui.synth_client import ErreurSynthese, synthesize

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _modele_par_defaut() -> Path | None:
    dossiers = config.voices_dirs(_REPO_ROOT)
    nom = config.default_voice_name(dossiers)
    return config.find_voice(nom, dossiers) if nom else None


def _analyser_arguments(argv: list[str]) -> argparse.Namespace:
    analyseur = argparse.ArgumentParser(
        prog="piperread-gui-cli",
        description=(
            "Lit le texte du presse-papiers, phrase par phrase, en passant "
            "par le serveur HTTP local de Piper — boucle de test sans fenêtre."
        ),
    )
    analyseur.add_argument(
        "--model",
        type=Path,
        default=_modele_par_defaut(),
        help="Chemin du modèle de voix .onnx (défaut : la première voix des dossiers de voix).",
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

    texte = read_clipboard()
    if not texte.strip():
        print("Presse-papiers vide : rien à lire.")
        return 0

    phrases = split_sentences(texte, arguments.lang)
    if not phrases:
        print("Aucune phrase reconnue dans le texte du presse-papiers.")
        return 0

    try:
        with PiperHttpServer(arguments.model) as serveur:
            print(f"Serveur prêt sur {serveur.base_url} ({len(phrases)} phrase(s)).")
            for numero, phrase in enumerate(phrases, start=1):
                print(f"[{numero}/{len(phrases)}] {phrase}")
                audio = synthesize(serveur.base_url, phrase)
                play_wav_bytes(audio)
    except (ErreurServeurPiper, ErreurSynthese) as erreur:
        print(f"Erreur : {erreur}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("Interrompu.", file=sys.stderr)
        return 130

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""
voice_download.py — télécharge une voix dans le dossier de l'utilisateur, à sa demande seulement.

Pourquoi ce fichier existe :
    Aucune voix n'est livrée ni téléchargée sans demande explicite (décision
    « Voix jamais livrées ni téléchargées sans demande »). Ce fichier n'est
    appelé que par le clic sur « Télécharger » de `voice_dialog.py`. Il suit
    la règle de `download_voice` de `utils/voices.sh` : le module du moteur
    écrit dans le dossier qu'on lui donne et ne rejette qu'un fichier vide, un
    téléchargement coupé y laisserait un modèle tronqué pris ensuite pour une
    voix installée. Le téléchargement se fait donc dans un dossier temporaire
    voisin, et les fichiers ne sont déplacés qu'une fois complets, le
    `.onnx.json` puis le `.onnx`, puisque c'est ce dernier que la recherche
    des voix cherche.

    Comme l'interface ne lie jamais Piper (GPL), le téléchargement est fait
    par le moteur dans son propre processus, par `piper_server_entry.py`
    (argument `download-voices`) : l'interpréteur du moteur sous Linux,
    `piper-http-server.exe` sous Windows.

Entrée / sortie :
    Entrée : le nom d'une voix du catalogue et le dossier des voix de
    l'utilisateur. Sortie : le chemin du `.onnx` posé ; `ErreurTelechargement`
    sinon, sans rien laisser dans le dossier des voix. `annuler` tue le
    processus en cours ; le dossier temporaire disparaît dans tous les cas.

Dépend de :
    `server.py` pour retrouver l'interpréteur ou l'exécutable du moteur.
"""

import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from piperread_gui import server
from piperread_gui.config import valid_voice_name


class ErreurTelechargement(RuntimeError):
    pass


def _commande(dossier: Path, nom: str) -> list[str]:
    if sys.platform == "win32":
        base = [str(server._trouver_executable_windows())]
    else:
        base = [str(server._trouver_interprete()), str(server._POINT_D_ENTREE)]
    return [*base, "download-voices", "--download-dir", str(dossier), nom]


class Telechargement:
    def __init__(self, nom: str, dossier_voix: Path):
        if not valid_voice_name(nom):
            raise ErreurTelechargement(f"Nom de voix invalide : {nom}")
        self._nom = nom
        self._dossier_voix = dossier_voix
        self._processus: subprocess.Popen | None = None
        self._annule = threading.Event()

    def annuler(self) -> None:
        self._annule.set()
        processus = self._processus
        if processus is not None and processus.poll() is None:
            processus.kill()

    def executer(self) -> Path:
        try:
            self._dossier_voix.mkdir(parents=True, exist_ok=True)
            temporaire = Path(tempfile.mkdtemp(prefix=".download.", dir=self._dossier_voix))
        except OSError as erreur:
            raise ErreurTelechargement(str(erreur)) from erreur
        try:
            return self._telecharger_dans(temporaire)
        finally:
            shutil.rmtree(temporaire, ignore_errors=True)

    def _telecharger_dans(self, temporaire: Path) -> Path:
        try:
            self._processus = subprocess.Popen(
                _commande(temporaire, self._nom),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (OSError, server.ErreurServeurPiper) as erreur:
            raise ErreurTelechargement(str(erreur)) from erreur
        if self._annule.is_set():
            self._processus.kill()
        _, erreurs = self._processus.communicate()

        modele = temporaire / f"{self._nom}.onnx"
        description = temporaire / f"{self._nom}.onnx.json"
        if (
            self._annule.is_set()
            or self._processus.returncode != 0
            or not modele.is_file()
            or modele.stat().st_size == 0
            or not description.is_file()
            or description.stat().st_size == 0
        ):
            derniere = (erreurs or "").strip().splitlines()
            raise ErreurTelechargement(derniere[-1] if derniere else self._nom)

        shutil.move(str(description), self._dossier_voix / description.name)
        shutil.move(str(modele), self._dossier_voix / modele.name)
        return self._dossier_voix / modele.name

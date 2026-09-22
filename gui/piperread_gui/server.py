"""
server.py — démarre et arrête le serveur HTTP local que fournit Piper lui-même.

Pourquoi ce fichier existe :
    Le moteur Piper est sous licence GPL-3.0-or-later ; l'interface, sous MIT,
    ne peut pas le lier dans son propre processus sans en hériter les
    obligations. Le piloter comme programme externe, par le serveur HTTP
    qu'il fournit lui-même (`python3 -m piper.http_server`), évite ce lien —
    exactement le principe déjà appliqué au noyau, qui appelle l'exécutable
    `piper` en sous-processus plutôt que de le lier. Décision arbitrée dans
    `CONCEPTION_PIPERREAD.md`, fiche « interface graphique ».

Entrée / sortie :
    Entrée : le chemin du modèle de voix (`.onnx`). Sortie : un objet
    `PiperHttpServer` démarré, dont l'attribut `base_url` pointe vers
    `http://127.0.0.1:<port>`, port choisi automatiquement et jamais exposé
    au-delà de la boucle locale.

Dépend de :
    Un interpréteur Python disposant du paquet `piper-tts[http]` — celui du
    clone (`<racine du dépôt>/piper-env/`) en priorité, sinon celui du paquet
    installé (`/usr/lib/piperread/venv/`), même logique de résolution que
    `read.sh` (`BASE_DIR`/`VENV_PATH`). Sur Windows, il n'existe ni venv ni
    paquet noyau séparé : l'exécutable autonome `piper-http-server.exe`,
    gelé par PyInstaller à côté de `piperread-gui.exe`
    (`gui/packaging/windows/`), en tient lieu et se lance directement, sans
    interpréteur ni option `-m`.
"""

import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

_GUI_DIR = Path(__file__).resolve().parent.parent
_REPO_ROOT = _GUI_DIR.parent
_VENV_PAQUET = Path("/usr/lib/piperread/venv")
_NOM_EXECUTABLE_WINDOWS = "piper-http-server.exe"
_HOTE_LOCAL = "127.0.0.1"
_DELAI_PRET_SECONDES = 20.0
_INTERVALLE_SONDAGE_SECONDES = 0.2


class ErreurServeurPiper(RuntimeError):
    pass


def _trouver_interprete() -> Path:
    venv_clone = _REPO_ROOT / "piper-env"
    venv_dir = venv_clone if venv_clone.is_dir() else _VENV_PAQUET

    interprete = venv_dir / "bin" / "python3"
    if not interprete.is_file():
        raise ErreurServeurPiper(
            f"Interpréteur introuvable : {interprete}. Installer le moteur "
            f"avec son extra HTTP : "
            f"\"{venv_dir}/bin/pip\" install \"piper-tts[http]\""
        )
    return interprete


def _trouver_executable_windows() -> Path:
    repertoire = Path(sys.executable).resolve().parent
    executable = repertoire / _NOM_EXECUTABLE_WINDOWS
    if not executable.is_file():
        raise ErreurServeurPiper(
            f"Exécutable du serveur de synthèse introuvable : {executable}. "
            f"Il doit être installé à côté de piperread-gui.exe."
        )
    return executable


def _commande_serveur(port: int, model_path: Path) -> list[str]:
    if sys.platform == "win32":
        return [
            str(_trouver_executable_windows()),
            "--host", _HOTE_LOCAL,
            "--port", str(port),
            "--model", str(model_path),
        ]
    return [
        str(_trouver_interprete()),
        "-m", "piper.http_server",
        "--host", _HOTE_LOCAL,
        "--port", str(port),
        "--model", str(model_path),
    ]


def _port_libre(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sonde:
        sonde.bind((host, 0))
        return sonde.getsockname()[1]


class PiperHttpServer:
    def __init__(self, model_path: str | Path):
        self._model_path = Path(model_path)
        if not self._model_path.is_file():
            raise ErreurServeurPiper(f"Modèle de voix introuvable : {self._model_path}")
        self._processus: subprocess.Popen | None = None
        self.port: int | None = None

    @property
    def base_url(self) -> str:
        if self.port is None:
            raise ErreurServeurPiper("Le serveur n'est pas démarré.")
        return f"http://{_HOTE_LOCAL}:{self.port}"

    def start(self) -> None:
        if self._processus is not None:
            raise ErreurServeurPiper("Le serveur est déjà démarré.")

        self.port = _port_libre(_HOTE_LOCAL)

        self._processus = subprocess.Popen(
            _commande_serveur(self.port, self._model_path),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self._attendre_disponibilite()

    def _attendre_disponibilite(self) -> None:
        assert self._processus is not None
        limite = time.monotonic() + _DELAI_PRET_SECONDES
        url_info = f"{self.base_url}/info"
        while time.monotonic() < limite:
            code_sortie = self._processus.poll()
            if code_sortie is not None:
                erreur = self._processus.stderr.read() if self._processus.stderr else ""
                raise ErreurServeurPiper(
                    f"Le serveur s'est arrêté avant d'être prêt (code {code_sortie}) : {erreur.strip()}"
                )
            try:
                with urllib.request.urlopen(url_info, timeout=1.0):
                    return
            except (urllib.error.URLError, ConnectionError, TimeoutError):
                time.sleep(_INTERVALLE_SONDAGE_SECONDES)
        self.stop()
        raise ErreurServeurPiper(
            f"Le serveur n'a pas répondu sur {url_info} avant {_DELAI_PRET_SECONDES:.0f} s."
        )

    def stop(self) -> None:
        if self._processus is None:
            return
        self._processus.terminate()
        try:
            self._processus.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            self._processus.kill()
            self._processus.wait(timeout=5.0)
        self._processus = None
        self.port = None

    def __enter__(self) -> "PiperHttpServer":
        self.start()
        return self

    def __exit__(self, *_exc_info) -> None:
        self.stop()

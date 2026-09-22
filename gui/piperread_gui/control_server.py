"""
control_server.py — canal de pilotage local d'une instance déjà lancée, par une socket Unix.

Pourquoi ce fichier existe :
    Sur un bureau sans zone de notification (GNOME sans extension), le menu du
    tray (`tray.py`) reste inaccessible une fois la notification unique
    affichée (`avertir_si_tray_absent`) : aucune autre surface n'existait pour
    piloter la lecture en cours. Ce fichier ouvre ce canal, dans le même
    répertoire d'exécution que `read.sh` (`runtime_dir()`, mêmes contrôles de
    propriétaire et de permissions), sous un nom de fichier distinct de ses
    `lock`/`group` pour ne jamais les confondre.

Entrée / sortie :
    Entrée : une commande texte par ligne, envoyée par `control_client.py`.
    Sortie : un signal Qt `commande` (texte de la commande reçue), que
    `app.py` relie aux méthodes de `PlaybackController`.

Dépend de :
    `socket.AF_UNIX` uniquement — aucune interface réseau, contrairement au
    serveur HTTP de synthèse (`server.py`), qui répond à un besoin distinct.
"""

import os
import socket
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

NOM_SOCKET = "gui.sock"
_DELAI_ACCEPTATION_SECONDES = 0.5


class ErreurControleIndisponible(RuntimeError):
    pass


def repertoire_execution() -> Path:
    runtime = os.environ.get("XDG_RUNTIME_DIR")
    dossier = Path(runtime) / "piperread" if runtime else Path(f"/tmp/piperread-{os.getuid()}")
    if not dossier.exists() and not dossier.is_symlink():
        dossier.mkdir(mode=0o700)
    stat = dossier.lstat()
    if (
        dossier.is_symlink()
        or not dossier.is_dir()
        or stat.st_uid != os.getuid()
        or (stat.st_mode & 0o777) != 0o700
    ):
        raise ErreurControleIndisponible(
            f"Répertoire d'exécution refusé (propriétaire ou permissions inattendus) : {dossier}"
        )
    return dossier


def chemin_socket() -> Path:
    return repertoire_execution() / NOM_SOCKET


def _instance_deja_active(chemin: Path) -> bool:
    if not chemin.exists():
        return False
    sonde = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    try:
        sonde.connect(str(chemin))
        return True
    except OSError:
        return False
    finally:
        sonde.close()


class ControlServer(QObject):
    commande = Signal(str)

    def __init__(self):
        super().__init__()
        self._socket: socket.socket | None = None
        self._fil: threading.Thread | None = None
        self._arret = threading.Event()

    def demarrer(self) -> None:
        chemin = chemin_socket()
        if _instance_deja_active(chemin):
            raise ErreurControleIndisponible(
                "Une instance de piperread-gui écoute déjà sur ce compte."
            )
        chemin.unlink(missing_ok=True)

        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.bind(str(chemin))
        chemin.chmod(0o600)
        self._socket.listen(1)
        self._socket.settimeout(_DELAI_ACCEPTATION_SECONDES)

        self._fil = threading.Thread(target=self._boucle_acceptation, daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=2.0)
            self._fil = None
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        chemin_socket().unlink(missing_ok=True)

    def _boucle_acceptation(self) -> None:
        assert self._socket is not None
        while not self._arret.is_set():
            try:
                connexion, _ = self._socket.accept()
            except OSError:
                continue
            with connexion:
                try:
                    ligne = connexion.makefile("r").readline().strip()
                    if ligne:
                        self.commande.emit(ligne)
                    connexion.sendall(b"ok\n")
                except OSError:
                    continue

"""
control_server.py — canal de pilotage local d'une instance déjà lancée.

Pourquoi ce fichier existe :
    Sur un bureau sans zone de notification (GNOME sans extension), le menu du
    tray (`tray.py`) reste inaccessible une fois la notification unique
    affichée (`avertir_si_tray_absent`) : aucune autre surface n'existait pour
    piloter la lecture en cours. Ce fichier ouvre ce canal, dans le même
    répertoire d'exécution que `read.sh` (`runtime_dir()`, mêmes contrôles de
    propriétaire et de permissions sur POSIX), sous un nom de fichier distinct
    de ses `lock`/`group` pour ne jamais les confondre.

    Sous Windows, `socket.AF_UNIX` n'existe pas de façon fiable : le canal y
    est une socket TCP en boucle locale (`127.0.0.1`, port choisi par l'OS),
    dont les coordonnées sont écrites dans un fichier du même répertoire
    d'exécution, accompagnées d'un jeton aléatoire à usage unique par instance
    que le client doit présenter — un correspondant qui ne connaît pas le
    jeton ne peut pas piloter l'instance, seule protection disponible sur une
    plateforme sans permissions de socket par fichier.

Entrée / sortie :
    Entrée : une commande texte par ligne, envoyée par `control_client.py`
    (précédée du jeton sur Windows). Sortie : un signal Qt `commande` (texte
    de la commande reçue), que `app.py` relie aux méthodes de
    `PlaybackController`.

Dépend de :
    `socket.AF_UNIX` sur POSIX (Linux, macOS) ; `socket.AF_INET` en boucle
    locale sur Windows uniquement — jamais d'interface réseau exposée, sur
    aucune des deux plateformes.
"""

import os
import secrets
import socket
import sys
import threading
from pathlib import Path

from PySide6.QtCore import QObject, Signal

NOM_SOCKET = "gui.sock"
NOM_CONNEXION_WINDOWS = "gui.port"
_DELAI_ACCEPTATION_SECONDES = 0.5


class ErreurControleIndisponible(RuntimeError):
    pass


def repertoire_execution() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or str(Path.home() / "AppData" / "Local")
        dossier = Path(base) / "piperread" / "run"
        dossier.mkdir(parents=True, exist_ok=True)
        if dossier.is_symlink() or not dossier.is_dir():
            raise ErreurControleIndisponible(
                f"Répertoire d'exécution refusé : {dossier}"
            )
        return dossier

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


def chemin_connexion_windows() -> Path:
    return repertoire_execution() / NOM_CONNEXION_WINDOWS


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


def _instance_deja_active_windows(chemin: Path) -> bool:
    if not chemin.exists():
        return False
    try:
        port, _jeton = chemin.read_text(encoding="utf-8").splitlines()[:2]
    except (OSError, ValueError):
        return False
    sonde = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sonde.settimeout(_DELAI_ACCEPTATION_SECONDES)
    try:
        sonde.connect(("127.0.0.1", int(port)))
        return True
    except (OSError, ValueError):
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
        self._jeton: str | None = None

    def demarrer(self) -> None:
        if sys.platform == "win32":
            self._demarrer_windows()
        else:
            self._demarrer_posix()

    def _demarrer_posix(self) -> None:
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

        self._fil = threading.Thread(target=self._boucle_acceptation_posix, daemon=True)
        self._fil.start()

    def _demarrer_windows(self) -> None:
        chemin = chemin_connexion_windows()
        if _instance_deja_active_windows(chemin):
            raise ErreurControleIndisponible(
                "Une instance de piperread-gui écoute déjà sur ce compte."
            )

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(("127.0.0.1", 0))
        port = self._socket.getsockname()[1]
        self._jeton = secrets.token_hex(16)
        chemin.write_text(f"{port}\n{self._jeton}\n", encoding="utf-8")
        self._socket.listen(1)
        self._socket.settimeout(_DELAI_ACCEPTATION_SECONDES)

        self._fil = threading.Thread(target=self._boucle_acceptation_windows, daemon=True)
        self._fil.start()

    def arreter(self) -> None:
        self._arret.set()
        if self._fil is not None:
            self._fil.join(timeout=2.0)
            self._fil = None
        if self._socket is not None:
            self._socket.close()
            self._socket = None
        if sys.platform == "win32":
            chemin_connexion_windows().unlink(missing_ok=True)
        else:
            chemin_socket().unlink(missing_ok=True)
        self._jeton = None

    def _boucle_acceptation_posix(self) -> None:
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

    def _boucle_acceptation_windows(self) -> None:
        assert self._socket is not None
        prefixe = f"{self._jeton} "
        while not self._arret.is_set():
            try:
                connexion, _ = self._socket.accept()
            except OSError:
                continue
            with connexion:
                try:
                    ligne = connexion.makefile("r").readline().strip()
                    if ligne.startswith(prefixe) and ligne[len(prefixe):]:
                        self.commande.emit(ligne[len(prefixe):])
                        connexion.sendall(b"ok\n")
                    else:
                        connexion.sendall(b"erreur\n")
                except OSError:
                    continue

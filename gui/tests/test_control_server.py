import socket
import time

import pytest
from PySide6.QtCore import Qt

from piperread_gui.control_server import (
    ControlServer,
    ErreurControleIndisponible,
    chemin_connexion_windows,
    chemin_socket,
    repertoire_execution,
)


@pytest.fixture(autouse=True)
def _xdg_runtime_isole(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))


def test_repertoire_execution_cree_en_700(tmp_path):
    dossier = repertoire_execution()
    assert dossier == tmp_path / "runtime" / "piperread"
    assert oct(dossier.stat().st_mode & 0o777) == oct(0o700)


def test_repertoire_execution_refuse_permissions_laxistes(tmp_path):
    dossier = tmp_path / "runtime" / "piperread"
    dossier.mkdir(parents=True, mode=0o755)

    with pytest.raises(ErreurControleIndisponible):
        repertoire_execution()


def test_chemin_socket_dans_le_repertoire_execution(tmp_path):
    assert chemin_socket() == tmp_path / "runtime" / "piperread" / "gui.sock"


def test_demarrer_recoit_une_commande_et_repond():
    serveur = ControlServer()
    commandes_recues = []
    serveur.commande.connect(commandes_recues.append, Qt.ConnectionType.DirectConnection)
    serveur.demarrer()
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2.0)
            client.connect(str(chemin_socket()))
            client.sendall(b"pause\n")
            reponse = client.makefile("r").readline().strip()
        assert reponse == "ok"

        limite = 2.0
        import time

        debut = time.monotonic()
        while not commandes_recues and time.monotonic() - debut < limite:
            time.sleep(0.01)
        assert commandes_recues == ["pause"]
    finally:
        serveur.arreter()


def test_survit_a_une_connexion_fermee_sans_lecture():
    serveur = ControlServer()
    commandes_recues = []
    serveur.commande.connect(commandes_recues.append, Qt.ConnectionType.DirectConnection)
    serveur.demarrer()
    try:
        sonde = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sonde.connect(str(chemin_socket()))
        sonde.close()

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(2.0)
            client.connect(str(chemin_socket()))
            client.sendall(b"pause\n")
            reponse = client.makefile("r").readline().strip()
        assert reponse == "ok"

        import time

        debut = time.monotonic()
        while not commandes_recues and time.monotonic() - debut < 2.0:
            time.sleep(0.01)
        assert commandes_recues == ["pause"]
    finally:
        serveur.arreter()


def test_seconde_instance_refusee():
    premier = ControlServer()
    premier.demarrer()
    try:
        second = ControlServer()
        with pytest.raises(ErreurControleIndisponible):
            second.demarrer()
    finally:
        premier.arreter()


def test_socket_perimee_nettoyee_avant_demarrage():
    chemin = chemin_socket()
    chemin.parent.mkdir(parents=True, exist_ok=True)
    orpheline = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    orpheline.bind(str(chemin))
    orpheline.close()

    serveur = ControlServer()
    try:
        serveur.demarrer()
    finally:
        serveur.arreter()


def test_arreter_supprime_le_fichier_de_socket():
    serveur = ControlServer()
    serveur.demarrer()
    assert chemin_socket().exists()

    serveur.arreter()
    assert not chemin_socket().exists()


@pytest.fixture
def _windows_simule(monkeypatch, tmp_path):
    import piperread_gui.control_server as module

    monkeypatch.setattr(module.sys, "platform", "win32")
    local_appdata = tmp_path / "AppData" / "Local"
    local_appdata.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))


def test_windows_demarrer_ecrit_port_et_jeton(_windows_simule):
    serveur = ControlServer()
    serveur.demarrer()
    try:
        contenu = chemin_connexion_windows().read_text(encoding="utf-8").splitlines()
        assert len(contenu) == 2
        port, jeton = contenu
        assert port.isdigit()
        assert len(jeton) == 32
    finally:
        serveur.arreter()


def test_windows_recoit_une_commande_avec_jeton_valide(_windows_simule):
    serveur = ControlServer()
    commandes_recues = []
    serveur.commande.connect(commandes_recues.append, Qt.ConnectionType.DirectConnection)
    serveur.demarrer()
    try:
        port, jeton = chemin_connexion_windows().read_text(encoding="utf-8").splitlines()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(2.0)
            client.connect(("127.0.0.1", int(port)))
            client.sendall(f"{jeton} pause\n".encode())
            reponse = client.makefile("r").readline().strip()
        assert reponse == "ok"

        debut = time.monotonic()
        while not commandes_recues and time.monotonic() - debut < 2.0:
            time.sleep(0.01)
        assert commandes_recues == ["pause"]
    finally:
        serveur.arreter()


def test_windows_refuse_jeton_invalide(_windows_simule):
    serveur = ControlServer()
    commandes_recues = []
    serveur.commande.connect(commandes_recues.append, Qt.ConnectionType.DirectConnection)
    serveur.demarrer()
    try:
        port, _jeton = chemin_connexion_windows().read_text(encoding="utf-8").splitlines()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
            client.settimeout(2.0)
            client.connect(("127.0.0.1", int(port)))
            client.sendall(b"mauvais-jeton pause\n")
            reponse = client.makefile("r").readline().strip()
        assert reponse == "erreur"

        time.sleep(0.1)
        assert commandes_recues == []
    finally:
        serveur.arreter()


def test_windows_seconde_instance_refusee(_windows_simule):
    premier = ControlServer()
    premier.demarrer()
    try:
        second = ControlServer()
        with pytest.raises(ErreurControleIndisponible):
            second.demarrer()
    finally:
        premier.arreter()


def test_windows_arreter_supprime_le_fichier_de_connexion(_windows_simule):
    serveur = ControlServer()
    serveur.demarrer()
    assert chemin_connexion_windows().exists()

    serveur.arreter()
    assert not chemin_connexion_windows().exists()

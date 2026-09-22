import pytest

from piperread_gui.control_client import ErreurAucuneInstance, envoyer_commande
from piperread_gui.control_server import ControlServer


@pytest.fixture(autouse=True)
def _xdg_runtime_isole(tmp_path, monkeypatch):
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))


def test_envoyer_commande_leve_si_aucune_instance():
    with pytest.raises(ErreurAucuneInstance):
        envoyer_commande("pause")


def test_envoyer_commande_atteint_une_instance_lancee():
    serveur = ControlServer()
    serveur.demarrer()
    try:
        reponse = envoyer_commande("arreter")
        assert reponse == "ok"
    finally:
        serveur.arreter()


@pytest.fixture
def _windows_simule(monkeypatch, tmp_path):
    import piperread_gui.control_client as module_client
    import piperread_gui.control_server as module_server

    monkeypatch.setattr(module_server.sys, "platform", "win32")
    monkeypatch.setattr(module_client.sys, "platform", "win32")
    local_appdata = tmp_path / "AppData" / "Local"
    local_appdata.mkdir(parents=True)
    monkeypatch.setenv("LOCALAPPDATA", str(local_appdata))


def test_windows_envoyer_commande_leve_si_aucune_instance(_windows_simule):
    with pytest.raises(ErreurAucuneInstance):
        envoyer_commande("pause")


def test_windows_envoyer_commande_atteint_une_instance_lancee(_windows_simule):
    serveur = ControlServer()
    serveur.demarrer()
    try:
        reponse = envoyer_commande("arreter")
        assert reponse == "ok"
    finally:
        serveur.arreter()

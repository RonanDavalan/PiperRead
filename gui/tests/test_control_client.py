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

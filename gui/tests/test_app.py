import pytest

from piperread_gui import app
from piperread_gui.app import _analyser_arguments


def test_sans_option_de_pilotage():
    arguments = _analyser_arguments(["--lang", "fr"])
    assert arguments.commande is None


@pytest.mark.parametrize(
    "option,commande",
    [
        ("--play", "lire"),
        ("--pause", "pause"),
        ("--resume", "reprendre"),
        ("--stop", "arreter"),
        ("--next", "phrase_suivante"),
        ("--previous", "phrase_precedente"),
        ("--quit", "quitter"),
    ],
)
def test_chaque_option_de_pilotage_produit_sa_commande(option, commande):
    arguments = _analyser_arguments([option])
    assert arguments.commande == commande


def test_options_de_pilotage_mutuellement_exclusives():
    with pytest.raises(SystemExit):
        _analyser_arguments(["--play", "--stop"])


def test_speed_absente_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.speed is None


def test_speed_transmise_telle_quelle():
    arguments = _analyser_arguments(["--speed", "1,5"])
    assert arguments.speed == "1,5"


def test_lang_absente_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.lang is None


def test_model_absent_par_defaut():
    arguments = _analyser_arguments([])
    assert arguments.model is None


# --- _resoudre_icone ---


def test_resoudre_icone_clone_prioritaire(tmp_path):
    ressources = tmp_path / "Ressources"
    ressources.mkdir()
    (ressources / "piperread.svg").touch()
    assert app._resoudre_icone(tmp_path) == ressources / "piperread.svg"


def test_resoudre_icone_repli_installee(tmp_path):
    assert app._resoudre_icone(tmp_path) == app._ICONE_INSTALLEE


def test_resoudre_icone_gelee_ignore_le_clone(monkeypatch, tmp_path):
    ressources = tmp_path / "Ressources"
    ressources.mkdir()
    (ressources / "piperread.svg").touch()
    monkeypatch.setattr(app.frozen, "installation_dir", lambda: tmp_path)

    assert app._resoudre_icone(tmp_path) == tmp_path / app._ICONE_GELEE

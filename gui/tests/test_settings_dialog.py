import pytest
from PySide6.QtWidgets import QApplication

from piperread_gui import config
from piperread_gui.controller import PlaybackController
from piperread_gui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def application():
    return QApplication.instance() or QApplication([])


@pytest.fixture(autouse=True)
def _config_isole(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    for cle in ("PIPERREAD_SPEED", "PIPERREAD_VOICE", "PIPERREAD_LANG"):
        monkeypatch.delenv(cle, raising=False)


def _voix(tmp_path, *noms):
    dossier = tmp_path / "voices"
    dossier.mkdir(exist_ok=True)
    for nom in noms:
        (dossier / f"{nom}.onnx").touch()
    return dossier


def test_dialogue_pre_rempli_avec_les_reglages_actuels(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha", "beta")
    controleur = PlaybackController(voices_dir / "beta.onnx", "fr", speed=1.75)

    dialogue = SettingsDialog(controleur)

    assert dialogue._voix.currentText() == "beta"
    assert dialogue._vitesse.value() == pytest.approx(1.75)
    assert dialogue._langue.currentData() == "fr"


def test_aucune_voix_desactive_le_champ(application, tmp_path):
    voices_dir = _voix(tmp_path, "seule")
    controleur = PlaybackController(voices_dir / "seule.onnx", "fr")
    (voices_dir / "seule.onnx").unlink()

    dialogue = SettingsDialog(controleur)

    assert not dialogue._voix.isEnabled()


def test_enregistrer_ecrit_le_fichier_et_met_a_jour_le_controleur(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha", "beta")
    controleur = PlaybackController(voices_dir / "alpha.onnx", "fr", speed=1.0)

    dialogue = SettingsDialog(controleur)
    dialogue._voix.setCurrentText("beta")
    dialogue._vitesse.setValue(2.0)
    dialogue._langue.setCurrentIndex(dialogue._langue.findData("en"))

    dialogue._enregistrer()

    valeurs, _ = config.load_config_file()
    assert valeurs == {"speed": "2.00", "voice": "beta", "lang": "en"}

    assert controleur.model_path == voices_dir / "beta.onnx"
    assert controleur.lang == "en"
    assert controleur.speed == pytest.approx(2.0)


def test_annuler_ne_modifie_rien(application, tmp_path):
    voices_dir = _voix(tmp_path, "alpha")
    controleur = PlaybackController(voices_dir / "alpha.onnx", "fr", speed=1.0)

    dialogue = SettingsDialog(controleur)
    dialogue._vitesse.setValue(2.5)
    dialogue.reject()

    assert not config.config_file_path().exists()
    assert controleur.speed == 1.0
